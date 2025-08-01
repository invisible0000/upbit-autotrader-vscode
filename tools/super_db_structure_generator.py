#!/usr/bin/env python3
"""
🛠️ Super DB Structure Generator - 스키마 구조 자동 생성 도구

DB 마이그레이션용 첫 번째 핵심 도구입니다.
- data_info의 YAML 및 SQL 스키마를 기반으로 DB 구조를 자동 생성
- 구조/인스턴스 분리 원칙에 따른 2-DB 시스템 구축
- 설정은 settings.sqlite3, 사용자 데이터는 strategies.sqlite3

사용법:
  python tools/super_db_structure_generator.py --mode create --target settings
  python tools/super_db_structure_generator.py --mode create --target strategies
  python tools/super_db_structure_generator.py --mode validate --db data/settings.sqlite3
"""

import argparse
import sqlite3
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

# 프로젝트 루트를 파이썬 패스에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/super_db_structure_generator.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class SuperDBStructureGenerator:
    """DB 구조 자동 생성 및 검증 도구"""
    
    def __init__(self):
        """초기화 - 경로 및 설정 준비"""
        self.project_root = PROJECT_ROOT
        self.data_info_path = (
            self.project_root / "upbit_auto_trading" / "utils" /
            "trading_variables" / "gui_variables_DB_migration_util" / "data_info"
        )
        self.db_path = self.project_root / "upbit_auto_trading" / "data"
        
        # 로그 디렉토리 생성
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logger.info("🚀 Super DB Structure Generator 초기화")
        logger.info(f"📂 Data Info Path: {self.data_info_path}")
        logger.info(f"🗄️ DB Path: {self.db_path}")
        
    def load_schema_sql(self) -> str:
        """통합 스키마 SQL 파일 로드"""
        schema_file = self.data_info_path / "upbit_autotrading_unified_schema.sql"
        
        if not schema_file.exists():
            raise FileNotFoundError(f"❌ 스키마 파일을 찾을 수 없습니다: {schema_file}")
            
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
            
        logger.info(f"✅ 스키마 파일 로드 완료: {schema_file.name}")
        return schema_sql
        
    def load_yaml_data(self, yaml_filename: str) -> Dict:
        """YAML 파일 로드"""
        yaml_file = self.data_info_path / yaml_filename
        
        if not yaml_file.exists():
            logger.warning(f"⚠️ YAML 파일이 존재하지 않음: {yaml_filename}")
            return {}
            
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        logger.info(f"✅ YAML 데이터 로드: {yaml_filename}")
        return data or {}
        
    def parse_schema_for_settings_db(self, schema_sql: str) -> List[str]:
        """settings.sqlite3에 들어갈 테이블들 추출"""
        # 구조 정의용 테이블들 (tv_, cfg_, sys_, _structure 접미사)
        settings_prefixes = ['tv_', 'cfg_', 'sys_', 'app_settings', 'backup_info']
        settings_suffixes = ['_structure', '_template', '_category', '_type']
        
        lines = schema_sql.split('\n')
        settings_tables = []
        current_table_sql = []
        is_settings_table = False
        
        for line in lines:
            line = line.strip()
            
            # CREATE TABLE 시작
            if line.startswith('CREATE TABLE'):
                if current_table_sql and is_settings_table:
                    settings_tables.append('\n'.join(current_table_sql))
                
                current_table_sql = [line]
                table_name = line.split()[2].replace('(', '').strip()
                
                # settings DB용 테이블인지 판단
                is_settings_table = (
                    any(table_name.startswith(prefix) for prefix in settings_prefixes) or
                    any(table_name.endswith(suffix) for suffix in settings_suffixes) or
                    'chart_' in table_name or 'template' in table_name
                )
                
                logger.debug(f"테이블 분석: {table_name} → settings DB: {is_settings_table}")
                
            else:
                if current_table_sql:
                    current_table_sql.append(line)
                    
                # 테이블 정의 종료 감지
                if line.endswith(');'):
                    if is_settings_table:
                        settings_tables.append('\n'.join(current_table_sql))
                    current_table_sql = []
                    is_settings_table = False
                    
        logger.info(f"📊 settings.sqlite3용 테이블 {len(settings_tables)}개 추출")
        return settings_tables
        
    def parse_schema_for_strategies_db(self, schema_sql: str) -> List[str]:
        """strategies.sqlite3에 들어갈 테이블들 추출 + 새로운 user_ 테이블 생성"""
        # 사용자 인스턴스용 테이블들
        user_prefixes = ['trading_conditions', 'component_strategy', 'strategies', 'execution_']
        
        lines = schema_sql.split('\n')
        strategies_tables = []
        current_table_sql = []
        is_strategies_table = False
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('CREATE TABLE'):
                if current_table_sql and is_strategies_table:
                    strategies_tables.append('\n'.join(current_table_sql))
                
                current_table_sql = [line]
                table_name = line.split()[2].replace('(', '').strip()
                
                # strategies DB용 테이블인지 판단
                is_strategies_table = any(table_name.startswith(prefix) for prefix in user_prefixes)
                
                logger.debug(f"테이블 분석: {table_name} → strategies DB: {is_strategies_table}")
                
            else:
                if current_table_sql:
                    current_table_sql.append(line)
                    
                if line.endswith(');'):
                    if is_strategies_table:
                        strategies_tables.append('\n'.join(current_table_sql))
                    current_table_sql = []
                    is_strategies_table = False
                    
        # 새로운 user_ 테이블들 추가
        user_tables = self._generate_user_tables()
        strategies_tables.extend(user_tables)
        
        logger.info(f"📊 strategies.sqlite3용 테이블 {len(strategies_tables)}개 추출")
        return strategies_tables
        
    def _generate_user_tables(self) -> List[str]:
        """사용자 인스턴스용 새로운 테이블 정의 생성"""
        user_tables = []
        
        # user_triggers (trading_conditions의 새로운 형태)
        user_triggers_sql = """
CREATE TABLE user_triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_name TEXT NOT NULL,
    description TEXT,
    left_variable_id TEXT NOT NULL,
    left_parameters TEXT,  -- JSON
    operator TEXT NOT NULL,
    right_variable_id TEXT NOT NULL,
    right_parameters TEXT,  -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    user_id TEXT DEFAULT 'default'
);"""
        user_tables.append(user_triggers_sql.strip())
        
        # user_strategies (component_strategy + strategies 통합)
        user_strategies_sql = """
CREATE TABLE user_strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT NOT NULL,
    description TEXT,
    entry_triggers TEXT,  -- JSON array of trigger IDs
    exit_triggers TEXT,   -- JSON array of trigger IDs
    position_size_type TEXT DEFAULT 'fixed',  -- fixed, percentage, dynamic
    position_size_value REAL DEFAULT 100000,
    config_json TEXT,     -- 전략 설정
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    user_id TEXT DEFAULT 'default',
    backtest_results TEXT  -- JSON
);"""
        user_tables.append(user_strategies_sql.strip())
        
        # execution_history (실행 기록)
        execution_history_sql = """
CREATE TABLE execution_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL,
    trigger_id INTEGER,
    action_type TEXT NOT NULL,  -- 'BUY', 'SELL', 'SIGNAL'
    symbol TEXT NOT NULL,
    price REAL,
    quantity REAL,
    executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'PENDING',  -- PENDING, SUCCESS, FAILED
    error_message TEXT,
    order_id TEXT,
    FOREIGN KEY (strategy_id) REFERENCES user_strategies(id)
);"""
        user_tables.append(execution_history_sql.strip())
        
        logger.info("🏗️ 사용자 인스턴스 테이블 3개 생성")
        return user_tables
        
    def create_settings_db(self, force: bool = False) -> bool:
        """settings.sqlite3 생성"""
        db_file = self.db_path / "settings.sqlite3"
        
        if db_file.exists() and not force:
            logger.warning(f"⚠️ DB 파일이 이미 존재: {db_file}")
            return False
            
        try:
            # DB 디렉토리 생성
            self.db_path.mkdir(parents=True, exist_ok=True)
            
            # 기존 파일이 있으면 삭제 (force 모드)
            if db_file.exists() and force:
                db_file.unlink()
                logger.info(f"🗑️ 기존 DB 파일 삭제: {db_file}")
            
            # 스키마 로드 및 파싱
            schema_sql = self.load_schema_sql()
            settings_tables = self.parse_schema_for_settings_db(schema_sql)
            
            # DB 생성 및 테이블 생성
            with sqlite3.connect(db_file) as conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                
                for table_sql in settings_tables:
                    try:
                        conn.execute(table_sql)
                        logger.debug(f"✅ 테이블 생성 완료: {table_sql.split()[2]}")
                    except sqlite3.Error as e:
                        logger.error(f"❌ 테이블 생성 실패: {e}")
                        logger.error(f"SQL: {table_sql[:100]}...")
                        
                conn.commit()
                
            logger.info(f"🎉 settings.sqlite3 생성 완료: {db_file}")
            logger.info(f"📊 생성된 테이블 수: {len(settings_tables)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ settings.sqlite3 생성 실패: {e}")
            return False
            
    def create_strategies_db(self, force: bool = False) -> bool:
        """strategies.sqlite3 생성"""
        db_file = self.db_path / "strategies.sqlite3"
        
        if db_file.exists() and not force:
            logger.warning(f"⚠️ DB 파일이 이미 존재: {db_file}")
            return False
            
        try:
            # DB 디렉토리 생성
            self.db_path.mkdir(parents=True, exist_ok=True)
            
            # 기존 파일이 있으면 삭제 (force 모드)
            if db_file.exists() and force:
                db_file.unlink()
                logger.info(f"🗑️ 기존 DB 파일 삭제: {db_file}")
            
            # 스키마 로드 및 파싱
            schema_sql = self.load_schema_sql()
            strategies_tables = self.parse_schema_for_strategies_db(schema_sql)
            
            # DB 생성 및 테이블 생성
            with sqlite3.connect(db_file) as conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                
                for table_sql in strategies_tables:
                    try:
                        conn.execute(table_sql)
                        table_name = table_sql.split()[2].replace('(', '').strip()
                        logger.debug(f"✅ 테이블 생성 완료: {table_name}")
                    except sqlite3.Error as e:
                        logger.error(f"❌ 테이블 생성 실패: {e}")
                        logger.error(f"SQL: {table_sql[:100]}...")
                        
                conn.commit()
                
            logger.info(f"🎉 strategies.sqlite3 생성 완료: {db_file}")
            logger.info(f"📊 생성된 테이블 수: {len(strategies_tables)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ strategies.sqlite3 생성 실패: {e}")
            return False
            
    def validate_structure_integrity(self, db_name: str) -> Dict[str, any]:
        """생성된 DB 구조의 무결성 검증"""
        db_file = self.db_path / f"{db_name}.sqlite3"
        
        if not db_file.exists():
            return {"status": "error", "message": f"DB 파일이 존재하지 않음: {db_file}"}
            
        try:
            with sqlite3.connect(db_file) as conn:
                # 테이블 목록 조회
                tables = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """).fetchall()
                
                table_names = [table[0] for table in tables]
                
                # Foreign Key 관계 확인
                fk_info = {}
                for table_name in table_names:
                    fks = conn.execute(f"PRAGMA foreign_key_list({table_name})").fetchall()
                    if fks:
                        fk_info[table_name] = fks
                        
                # 인덱스 확인
                indexes = conn.execute("""
                    SELECT name, tbl_name FROM sqlite_master 
                    WHERE type='index' AND name NOT LIKE 'sqlite_%'
                """).fetchall()
                
                validation_result = {
                    "status": "success",
                    "db_name": db_name,
                    "table_count": len(table_names),
                    "tables": table_names,
                    "foreign_keys": fk_info,
                    "indexes": indexes,
                    "validated_at": datetime.now().isoformat()
                }
                
                logger.info(f"✅ {db_name}.sqlite3 구조 검증 완료")
                logger.info(f"📊 테이블 수: {len(table_names)}")
                logger.info(f"🔗 외래키 관계: {len(fk_info)}개 테이블")
                logger.info(f"📇 인덱스: {len(indexes)}개")
                
                return validation_result
                
        except sqlite3.Error as e:
            error_result = {
                "status": "error", 
                "message": f"DB 검증 실패: {e}",
                "db_name": db_name
            }
            logger.error(f"❌ {db_name}.sqlite3 검증 실패: {e}")
            return error_result
            
    def generate_structure_report(self, db_name: str) -> str:
        """DB 구조 보고서 생성"""
        validation_result = self.validate_structure_integrity(db_name)
        
        if validation_result["status"] == "error":
            return f"❌ 보고서 생성 실패: {validation_result['message']}"
            
        report = f"""
# 🗄️ {db_name.upper()}.SQLITE3 구조 보고서

## 📊 기본 정보
- **DB 파일**: {db_name}.sqlite3
- **테이블 수**: {validation_result['table_count']}개
- **검증 일시**: {validation_result['validated_at']}

## 📋 테이블 목록
"""
        
        for i, table in enumerate(validation_result['tables'], 1):
            report += f"{i}. `{table}`\n"
            
        if validation_result['foreign_keys']:
            report += "\n## 🔗 외래키 관계\n"
            for table, fks in validation_result['foreign_keys'].items():
                report += f"- **{table}**: {len(fks)}개 외래키\n"
                
        if validation_result['indexes']:
            report += f"\n## 📇 인덱스\n"
            for index_name, table_name in validation_result['indexes']:
                report += f"- `{index_name}` → `{table_name}`\n"
                
        report += f"\n---\n**생성 도구**: Super DB Structure Generator v1.0\n"
        
        return report


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="🛠️ Super DB Structure Generator - DB 구조 자동 생성 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python tools/super_db_structure_generator.py --mode create --target settings
  python tools/super_db_structure_generator.py --mode create --target strategies --force
  python tools/super_db_structure_generator.py --mode validate --db settings
  python tools/super_db_structure_generator.py --mode report --db settings
        """
    )
    
    parser.add_argument('--mode', required=True, 
                       choices=['create', 'validate', 'report'],
                       help='동작 모드: create(생성), validate(검증), report(보고서)')
    
    parser.add_argument('--target', 
                       choices=['settings', 'strategies'],
                       help='생성할 DB 타입 (create 모드에서 필수)')
    
    parser.add_argument('--db',
                       help='검증할 DB 이름 (validate/report 모드에서 필수)')
    
    parser.add_argument('--force', action='store_true',
                       help='기존 DB 파일 덮어쓰기')
    
    args = parser.parse_args()
    
    generator = SuperDBStructureGenerator()
    
    try:
        if args.mode == 'create':
            if not args.target:
                print("❌ create 모드에서는 --target이 필요합니다")
                return 1
                
            if args.target == 'settings':
                success = generator.create_settings_db(force=args.force)
            else:  # strategies
                success = generator.create_strategies_db(force=args.force)
                
            if success:
                print(f"🎉 {args.target}.sqlite3 생성 완료!")
                return 0
            else:
                print(f"❌ {args.target}.sqlite3 생성 실패")
                return 1
                
        elif args.mode == 'validate':
            if not args.db:
                print("❌ validate 모드에서는 --db가 필요합니다")
                return 1
                
            result = generator.validate_structure_integrity(args.db)
            if result["status"] == "success":
                print(f"✅ {args.db}.sqlite3 검증 성공!")
                print(f"📊 테이블 수: {result['table_count']}")
                return 0
            else:
                print(f"❌ 검증 실패: {result['message']}")
                return 1
                
        elif args.mode == 'report':
            if not args.db:
                print("❌ report 모드에서는 --db가 필요합니다")
                return 1
                
            report = generator.generate_structure_report(args.db)
            print(report)
            
            # 보고서 파일로 저장
            report_file = Path(f"logs/{args.db}_structure_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
            report_file.parent.mkdir(exist_ok=True)
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n📄 보고서 저장: {report_file}")
            return 0
            
    except Exception as e:
        logger.error(f"❌ 실행 중 오류 발생: {e}")
        print(f"❌ 오류: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
