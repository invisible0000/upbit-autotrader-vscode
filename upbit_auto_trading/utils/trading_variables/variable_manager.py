"""
트레이딩 지표 변수 관리 시스템 - 핵심 관리 클래스

SimpleVariableManager: 
- DB 기반 지표 호환성 검증
- SQL JOIN을 통한 효율적인 호환 지표 조회
- 스키마 자동 초기화 기능

사용법:
    vm = SimpleVariableManager('trading.db')
    compatible = vm.get_compatible_variables('SMA')
    result = vm.check_compatibility('SMA', 'EMA')
"""

import sqlite3
import os
from typing import List, Dict, Tuple, Optional
import logging

# 전역 DB 매니저 임포트
try:
    from upbit_auto_trading.utils.global_db_manager import get_db_connection
    USE_GLOBAL_MANAGER = True
except ImportError:
    print("⚠️ 전역 DB 매니저를 사용할 수 없습니다. 기존 방식을 사용합니다.")
    USE_GLOBAL_MANAGER = False

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleVariableManager:
    """트레이딩 지표 변수 관리 클래스"""
    
    def __init__(self, db_path: str = 'trading_variables.db'):
        """
        초기화
        
        Args:
            db_path: SQLite DB 파일 경로 (전역 매니저 사용시 무시됨)
        """
        self.db_path = db_path  # 레거시 호환성
        self.conn = None
        self.use_global_manager = USE_GLOBAL_MANAGER
        
        if not self.use_global_manager:
            self._connect()
        self._init_schema()
    
    def _get_connection(self):
        """DB 연결 반환 - 전역 매니저 또는 기존 방식"""
        if self.use_global_manager:
            return get_db_connection('tv_trading_variables')
        else:
            return self.conn
    
    def _connect(self):
        """DB 연결 (기존 방식용)"""
        if not self.use_global_manager:
            try:
                self.conn = sqlite3.connect(self.db_path)
                self.conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
                logger.info(f"DB 연결 성공: {self.db_path}")
            except Exception as e:
                logger.error(f"DB 연결 실패: {e}")
                raise
    
    def _init_schema(self):
        """스키마 자동 초기화"""
        try:
            # 스키마 파일 경로
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            
            if os.path.exists(schema_path):
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                
                # SQL 문을 세미콜론으로 분할하여 실행
                statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
                
                conn = self._get_connection()
                cursor = conn.cursor()
                
                for statement in statements:
                    try:
                        cursor.execute(statement)
                    except sqlite3.Error as e:
                        logger.warning(f"스키마 실행 중 오류 (무시됨): {e}")
                
                if not self.use_global_manager:
                    conn.commit()  # 전역 매니저 사용시에는 자동 관리됨
                
                for statement in statements:
                    if statement:
                        self.conn.execute(statement)
                
                self.conn.commit()
                logger.info("스키마 초기화 완료")
                
                # 초기화 확인
                cursor = self.conn.execute("SELECT COUNT(*) as count FROM trading_variables WHERE is_active = 1")
                count = cursor.fetchone()['count']
                logger.info(f"활성 지표 수: {count}개")
                
            else:
                logger.warning(f"스키마 파일을 찾을 수 없습니다: {schema_path}")
                
        except Exception as e:
            logger.error(f"스키마 초기화 실패: {e}")
            # 기본 테이블만이라도 생성
            self._create_basic_table()
    
    def _create_basic_table(self):
        """기본 테이블 생성 (스키마 파일 없을 때)"""
        try:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS trading_variables (
                    variable_id TEXT PRIMARY KEY,
                    display_name_ko TEXT NOT NULL,
                    purpose_category TEXT NOT NULL,
                    chart_category TEXT NOT NULL,
                    comparison_group TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
            logger.info("기본 테이블 생성 완료")
        except Exception as e:
            logger.error(f"기본 테이블 생성 실패: {e}")
            raise
    
    def get_compatible_variables(self, base_variable_id: str) -> List[Tuple[str, str]]:
        """
        기본 변수와 호환 가능한 변수들 조회
        
        Args:
            base_variable_id: 기준 변수 ID (예: 'SMA')
            
        Returns:
            [(variable_id, display_name_ko), ...] 형태의 리스트
        """
        try:
            query = """
            SELECT v2.variable_id, v2.display_name_ko 
            FROM trading_variables v1
            JOIN trading_variables v2 ON (
                v1.purpose_category = v2.purpose_category 
                AND v1.comparison_group = v2.comparison_group
                AND v2.is_active = 1
                AND v2.variable_id != v1.variable_id
            )
            WHERE v1.variable_id = ? AND v1.is_active = 1
            ORDER BY v2.display_name_ko
            """
            
            cursor = self.conn.execute(query, (base_variable_id,))
            results = cursor.fetchall()
            
            # sqlite3.Row를 튜플로 변환
            return [(row['variable_id'], row['display_name_ko']) for row in results]
            
        except Exception as e:
            logger.error(f"호환 변수 조회 실패: {e}")
            return []
    
    def check_compatibility(self, var1: str, var2: str) -> Dict[str, any]:
        """
        두 변수의 호환성 검증
        
        Args:
            var1: 첫 번째 변수 ID
            var2: 두 번째 변수 ID
            
        Returns:
            {
                'compatible': bool,
                'reason': str,
                'var1_info': dict,
                'var2_info': dict
            }
        """
        try:
            query = """
            SELECT v1.variable_id as v1_id, v1.display_name_ko as v1_name,
                   v1.purpose_category as v1_purpose, v1.comparison_group as v1_comp,
                   v2.variable_id as v2_id, v2.display_name_ko as v2_name,
                   v2.purpose_category as v2_purpose, v2.comparison_group as v2_comp
            FROM trading_variables v1, trading_variables v2
            WHERE v1.variable_id = ? AND v2.variable_id = ?
              AND v1.is_active = 1 AND v2.is_active = 1
            """
            
            cursor = self.conn.execute(query, (var1, var2))
            result = cursor.fetchone()
            
            if not result:
                return {
                    'compatible': False,
                    'reason': f'변수를 찾을 수 없음 ({var1} 또는 {var2})',
                    'var1_info': None,
                    'var2_info': None
                }
            
            # 결과 파싱
            v1_purpose = result['v1_purpose']
            v1_comp = result['v1_comp']
            v2_purpose = result['v2_purpose'] 
            v2_comp = result['v2_comp']
            
            var1_info = {
                'id': result['v1_id'],
                'name': result['v1_name'],
                'purpose': v1_purpose,
                'comparison': v1_comp
            }
            
            var2_info = {
                'id': result['v2_id'],
                'name': result['v2_name'], 
                'purpose': v2_purpose,
                'comparison': v2_comp
            }
            
            # 호환성 판단
            if v1_purpose == v2_purpose and v1_comp == v2_comp:
                return {
                    'compatible': True,
                    'reason': f'같은 {v1_purpose} 카테고리 ({v1_comp})',
                    'var1_info': var1_info,
                    'var2_info': var2_info
                }
            else:
                return {
                    'compatible': False,
                    'reason': f'다른 카테고리 ({v1_purpose}:{v1_comp} ≠ {v2_purpose}:{v2_comp})',
                    'var1_info': var1_info,
                    'var2_info': var2_info
                }
                
        except Exception as e:
            logger.error(f"호환성 검증 실패: {e}")
            return {
                'compatible': False,
                'reason': f'검증 중 오류 발생: {str(e)}',
                'var1_info': None,
                'var2_info': None
            }
    
    def get_all_variables(self, active_only: bool = True) -> List[Dict[str, any]]:
        """
        모든 변수 조회
        
        Args:
            active_only: True면 활성 변수만, False면 전체
            
        Returns:
            변수 정보 딕셔너리 리스트
        """
        try:
            where_clause = "WHERE is_active = 1" if active_only else ""
            query = f"""
            SELECT variable_id, display_name_ko, display_name_en,
                   purpose_category, chart_category, comparison_group,
                   is_active, description, source
            FROM trading_variables 
            {where_clause}
            ORDER BY purpose_category, display_name_ko
            """
            
            cursor = self.conn.execute(query)
            results = cursor.fetchall()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"전체 변수 조회 실패: {e}")
            return []
    
    def get_variables_by_category(self, purpose_category: str) -> List[Dict[str, any]]:
        """
        카테고리별 변수 조회
        
        Args:
            purpose_category: 용도 카테고리 ('trend', 'momentum', 'volatility', 'volume', 'price')
            
        Returns:
            해당 카테고리의 변수들
        """
        try:
            query = """
            SELECT variable_id, display_name_ko, chart_category, comparison_group
            FROM trading_variables 
            WHERE purpose_category = ? AND is_active = 1
            ORDER BY display_name_ko
            """
            
            cursor = self.conn.execute(query, (purpose_category,))
            results = cursor.fetchall()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"카테고리별 조회 실패: {e}")
            return []
    
    def add_variable(self, variable_id: str, display_name_ko: str, 
                    purpose_category: str, chart_category: str, 
                    comparison_group: str, description: str = '',
                    display_name_en: str = '', source: str = 'custom',
                    is_active: bool = False) -> bool:
        """
        새 변수 추가
        
        Args:
            variable_id: 변수 ID
            display_name_ko: 한국어 표시명
            purpose_category: 용도 카테고리
            chart_category: 차트 카테고리
            comparison_group: 비교 그룹
            description: 설명
            display_name_en: 영어 표시명
            source: 출처
            is_active: 활성화 여부
            
        Returns:
            성공 여부
        """
        try:
            query = """
            INSERT INTO trading_variables 
            (variable_id, display_name_ko, display_name_en, purpose_category, 
             chart_category, comparison_group, description, source, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.conn.execute(query, (
                variable_id, display_name_ko, display_name_en, purpose_category,
                chart_category, comparison_group, description, source, is_active
            ))
            self.conn.commit()
            
            logger.info(f"변수 추가 성공: {variable_id} ({display_name_ko})")
            return True
            
        except sqlite3.IntegrityError as e:
            logger.error(f"변수 추가 실패 - 중복 ID: {variable_id}")
            return False
        except Exception as e:
            logger.error(f"변수 추가 실패: {e}")
            return False
    
    def activate_variable(self, variable_id: str) -> bool:
        """변수 활성화"""
        try:
            cursor = self.conn.execute(
                "UPDATE trading_variables SET is_active = 1 WHERE variable_id = ?",
                (variable_id,)
            )
            self.conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"변수 활성화 성공: {variable_id}")
                return True
            else:
                logger.warning(f"변수를 찾을 수 없음: {variable_id}")
                return False
                
        except Exception as e:
            logger.error(f"변수 활성화 실패: {e}")
            return False
    
    def deactivate_variable(self, variable_id: str) -> bool:
        """변수 비활성화"""
        try:
            cursor = self.conn.execute(
                "UPDATE trading_variables SET is_active = 0 WHERE variable_id = ?",
                (variable_id,)
            )
            self.conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"변수 비활성화 성공: {variable_id}")
                return True
            else:
                logger.warning(f"변수를 찾을 수 없음: {variable_id}")
                return False
                
        except Exception as e:
            logger.error(f"변수 비활성화 실패: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, any]:
        """통계 정보 조회"""
        try:
            stats = {}
            
            # 전체 통계
            cursor = self.conn.execute("SELECT COUNT(*) as total FROM trading_variables")
            stats['total_variables'] = cursor.fetchone()['total']
            
            cursor = self.conn.execute("SELECT COUNT(*) as active FROM trading_variables WHERE is_active = 1")
            stats['active_variables'] = cursor.fetchone()['active']
            
            # 카테고리별 통계
            cursor = self.conn.execute("""
                SELECT purpose_category, COUNT(*) as count 
                FROM trading_variables 
                WHERE is_active = 1 
                GROUP BY purpose_category
            """)
            
            stats['by_category'] = {}
            for row in cursor.fetchall():
                stats['by_category'][row['purpose_category']] = row['count']
            
            # 차트 타입별 통계
            cursor = self.conn.execute("""
                SELECT chart_category, COUNT(*) as count 
                FROM trading_variables 
                WHERE is_active = 1 
                GROUP BY chart_category
            """)
            
            stats['by_chart_type'] = {}
            for row in cursor.fetchall():
                stats['by_chart_type'][row['chart_category']] = row['count']
            
            return stats
            
        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            return {}
    
    def close(self):
        """DB 연결 종료"""
        if self.conn:
            self.conn.close()
            logger.info("DB 연결 종료")
    
    def __enter__(self):
        """Context manager 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.close()


if __name__ == "__main__":
    # 기본 테스트
    print("🧪 SimpleVariableManager 기본 테스트")
    
    with SimpleVariableManager('test_trading_variables.db') as vm:
        # 통계 출력
        stats = vm.get_statistics()
        print(f"📊 총 {stats.get('active_variables', 0)}개의 활성 지표")
        
        # SMA 호환성 테스트
        print("\n🔍 SMA 호환 지표 조회:")
        compatible = vm.get_compatible_variables('SMA')
        for var_id, name in compatible:
            print(f"  ✅ {var_id}: {name}")
        
        # 호환성 검증 테스트
        print("\n🔍 SMA-EMA 호환성 검증:")
        result = vm.check_compatibility('SMA', 'EMA')
        print(f"  호환성: {'✅' if result['compatible'] else '❌'}")
        print(f"  이유: {result['reason']}")
        
        print("\n✅ 테스트 완료!")
