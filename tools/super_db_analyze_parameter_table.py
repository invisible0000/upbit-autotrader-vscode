#!/usr/bin/env python3
"""
🔍 Super DB Analyze Parameter Table
변수 파라미터 테이블 상세 분석 도구

🤖 LLM 사용 가이드:
===================
이 도구는 트레이딩 변수 파라미터 시스템을 분석하기 위한 전문 도구입니다.

📋 주요 명령어 (tools 폴더에서 실행):
1. python super_db_analyze_parameter_table.py              # 기본 파라미터 분석
2. python super_db_analyze_parameter_table.py --detailed   # 상세 분석 (구조 포함)  
3. python super_db_analyze_parameter_table.py --export     # YAML 형태로 내보내기
4. python super_db_analyze_parameter_table.py --validate   # 파라미터 무결성 검증

🎯 언제 사용하면 좋은가:
- 파라미터가 있는/없는 변수 구분이 필요할 때
- 새로운 변수 추가 시 파라미터 정의 참고할 때  
- UI에서 파라미터 관련 오류 발생 시 원인 분석할 때
- 파라미터 데이터 구조를 이해해야 할 때
- YAML ↔ DB 마이그레이션 전후 상태 확인할 때

💡 출력 해석:
- 📋 변수별 파라미터: 각 변수가 가진 파라미터 목록과 설정값
- ❌ 파라미터 없는 변수: 시장 데이터나 계산값 변수들 (정상)
- 📊 통계 요약: 전체 변수/파라미터 개수 및 분포
- 🔍 구조 분석: 테이블 스키마 및 컬럼 정보 (--detailed 옵션)
- ✅ 무결성 검증: 데이터 일관성 및 필수값 체크 (--validate 옵션)

기능:
1. 변수별 파라미터 목록 및 설정값 분석
2. 파라미터 없는 변수 식별 및 분류
3. 테이블 구조 및 스키마 정보 조회
4. 파라미터 데이터 무결성 검증
5. YAML 형태 내보내기 지원

작성일: 2025-08-02
작성자: Upbit Auto Trading Team
"""

import sqlite3
import yaml
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime


class SuperDBAnalyzeParameterTable:
    """
    🔍 변수 파라미터 테이블 전문 분석 도구
    
    Features:
    - 변수별 파라미터 상세 분석
    - 파라미터 없는 변수 식별
    - 테이블 구조 분석
    - 데이터 무결성 검증
    - YAML 내보내기
    """
    
    def __init__(self):
        """초기화"""
        self.project_root = Path(__file__).parent.parent
        self.db_path = self.project_root / "upbit_auto_trading" / "data" / "settings.sqlite3"
        
        # 변수 분류 정의
        self.variable_categories = {
            'technical_indicators': [
                'ATR', 'BOLLINGER_BAND', 'EMA', 'MACD', 'RSI', 'SMA', 'STOCHASTIC', 'VOLUME_SMA'
            ],
            'market_data': [
                'CURRENT_PRICE', 'HIGH_PRICE', 'LOW_PRICE', 'OPEN_PRICE', 'VOLUME'
            ],
            'portfolio_data': [
                'AVG_BUY_PRICE', 'POSITION_SIZE', 'PROFIT_AMOUNT', 'PROFIT_PERCENT'
            ],
            'balance_data': [
                'CASH_BALANCE', 'COIN_BALANCE', 'TOTAL_BALANCE'
            ]
        }
    
    def get_db_connection(self) -> sqlite3.Connection:
        """DB 연결 생성"""
        if not self.db_path.exists():
            raise FileNotFoundError(f"❌ DB 파일이 존재하지 않습니다: {self.db_path}")
        
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def analyze_table_structure(self) -> Dict[str, Any]:
        """테이블 구조 분석"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 테이블 구조 정보
                cursor.execute("PRAGMA table_info(tv_variable_parameters)")
                columns = cursor.fetchall()
                
                # 인덱스 정보
                cursor.execute("PRAGMA index_list(tv_variable_parameters)")
                indexes = cursor.fetchall()
                
                # 외래키 정보
                cursor.execute("PRAGMA foreign_key_list(tv_variable_parameters)")
                foreign_keys = cursor.fetchall()
                
                return {
                    'columns': [dict(col) for col in columns],
                    'indexes': [dict(idx) for idx in indexes],
                    'foreign_keys': [dict(fk) for fk in foreign_keys],
                    'total_records': self._get_record_count()
                }
                
        except Exception as e:
            print(f"❌ 테이블 구조 분석 실패: {e}")
            return {}
    
    def _get_record_count(self) -> int:
        """레코드 수 조회"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM tv_variable_parameters")
                return cursor.fetchone()[0]
        except:
            return 0
    
    def analyze_parameters_by_variable(self) -> Tuple[Dict[str, List[Dict]], List[Tuple[str, str]]]:
        """변수별 파라미터 분석"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 모든 파라미터 데이터 조회
                cursor.execute("""
                    SELECT * FROM tv_variable_parameters 
                    ORDER BY variable_id, display_order, parameter_name
                """)
                all_params = cursor.fetchall()
                
                # 변수별 그룹화
                by_variable = {}
                for param in all_params:
                    var_id = param['variable_id']
                    if var_id not in by_variable:
                        by_variable[var_id] = []
                    
                    param_data = {
                        'parameter_name': param['parameter_name'],
                        'parameter_type': param['parameter_type'],
                        'default_value': param['default_value'],
                        'min_value': param['min_value'],
                        'max_value': param['max_value'],
                        'enum_values': param['enum_values'],
                        'is_required': bool(param['is_required']),
                        'display_name_ko': param['display_name_ko'],
                        'display_name_en': param['display_name_en'],
                        'description': param['description'],
                        'display_order': param['display_order']
                    }
                    by_variable[var_id].append(param_data)
                
                # 파라미터가 없는 변수 찾기
                cursor.execute("SELECT variable_id, display_name_ko FROM tv_trading_variables ORDER BY variable_id")
                all_vars = cursor.fetchall()
                
                vars_with_params = set(by_variable.keys())
                vars_without_params = []
                
                for var in all_vars:
                    if var['variable_id'] not in vars_with_params:
                        vars_without_params.append((var['variable_id'], var['display_name_ko']))
                
                return by_variable, vars_without_params
                
        except Exception as e:
            print(f"❌ 파라미터 분석 실패: {e}")
            return {}, []
    
    def categorize_variables(self, vars_without_params: List[Tuple[str, str]]) -> Dict[str, List[Tuple[str, str]]]:
        """파라미터 없는 변수 분류"""
        categorized = {
            'market_data': [],
            'portfolio_data': [],
            'balance_data': [],
            'unknown': []
        }
        
        for var_id, name_ko in vars_without_params:
            categorized_flag = False
            for category, var_list in self.variable_categories.items():
                if var_id in var_list:
                    if category == 'technical_indicators':
                        # 기술 지표인데 파라미터가 없으면 문제
                        categorized['unknown'].append((var_id, f"{name_ko} (⚠️ 기술지표인데 파라미터 없음)"))
                    else:
                        category_key = category if category != 'technical_indicators' else 'unknown'
                        categorized[category_key].append((var_id, name_ko))
                    categorized_flag = True
                    break
            
            if not categorized_flag:
                categorized['unknown'].append((var_id, name_ko))
        
        return categorized
    
    def validate_parameter_integrity(self, params_by_var: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """파라미터 데이터 무결성 검증"""
        issues = []
        statistics = {
            'total_variables_with_params': len(params_by_var),
            'total_parameters': sum(len(params) for params in params_by_var.values()),
            'parameter_types': {},
            'required_params': 0,
            'optional_params': 0
        }
        
        for var_id, params in params_by_var.items():
            for param in params:
                # 파라미터 타입 통계
                param_type = param['parameter_type']
                statistics['parameter_types'][param_type] = statistics['parameter_types'].get(param_type, 0) + 1
                
                # 필수/선택 통계
                if param['is_required']:
                    statistics['required_params'] += 1
                else:
                    statistics['optional_params'] += 1
                
                # 무결성 검증
                if not param['parameter_name']:
                    issues.append(f"❌ {var_id}: 파라미터명이 비어있음")
                
                if not param['parameter_type']:
                    issues.append(f"❌ {var_id}.{param['parameter_name']}: 파라미터 타입이 비어있음")
                
                if param['parameter_type'] == 'integer':
                    if param['min_value'] and param['max_value']:
                        try:
                            min_val = int(param['min_value'])
                            max_val = int(param['max_value'])
                            if min_val >= max_val:
                                issues.append(f"⚠️ {var_id}.{param['parameter_name']}: min_value >= max_value")
                        except:
                            issues.append(f"⚠️ {var_id}.{param['parameter_name']}: integer 타입인데 min/max가 숫자가 아님")
                
                if param['parameter_type'] == 'enum':
                    if not param['enum_values']:
                        issues.append(f"❌ {var_id}.{param['parameter_name']}: enum 타입인데 선택지가 없음")
                    else:
                        try:
                            if isinstance(param['enum_values'], str):
                                enum_list = json.loads(param['enum_values'])
                            else:
                                enum_list = param['enum_values']
                            if not isinstance(enum_list, list) or len(enum_list) == 0:
                                issues.append(f"❌ {var_id}.{param['parameter_name']}: enum 선택지가 비어있음")
                        except:
                            issues.append(f"❌ {var_id}.{param['parameter_name']}: enum_values 파싱 실패")
        
        return {
            'issues': issues,
            'statistics': statistics,
            'integrity_score': max(0, 100 - len(issues) * 5)  # 이슈 하나당 5점 감점
        }
    
    def export_to_yaml(self, params_by_var: Dict[str, List[Dict]], output_file: Optional[str] = None) -> bool:
        """YAML 형태로 내보내기"""
        try:
            # 메타데이터 추가
            export_data = {
                'metadata': {
                    'export_time': datetime.now().isoformat(),
                    'source': 'tv_variable_parameters table',
                    'tool': 'super_db_analyze_parameter_table.py',
                    'total_variables': len(params_by_var),
                    'total_parameters': sum(len(params) for params in params_by_var.values())
                },
                'variable_parameters': {}
            }
            
            # 변수별 파라미터 데이터
            for var_id, params in params_by_var.items():
                export_data['variable_parameters'][var_id] = params
            
            # 파일명 결정
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"parameter_analysis_export_{timestamp}.yaml"
            
            output_path = Path(output_file)
            
            # YAML 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(export_data, f, allow_unicode=True, default_flow_style=False, indent=2)
            
            print(f"✅ YAML 내보내기 완료: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ YAML 내보내기 실패: {e}")
            return False
    
    def run_basic_analysis(self) -> None:
        """기본 분석 실행"""
        print("🔍 === 변수 파라미터 테이블 분석 ===")
        print(f"📂 DB 경로: {self.db_path}")
        
        try:
            # 파라미터 분석
            params_by_var, vars_without_params = self.analyze_parameters_by_variable()
            
            if not params_by_var and not vars_without_params:
                print("❌ 분석할 데이터가 없습니다.")
                return
            
            # 파라미터가 있는 변수 출력
            print(f"\n=== 파라미터가 있는 변수 ({len(params_by_var)}개) ===")
            for var_id, params in params_by_var.items():
                print(f"\n📋 {var_id} ({len(params)}개 파라미터):")
                for param in params:
                    param_type = param['parameter_type']
                    default_val = param['default_value'] or 'N/A'
                    required = "🔴 필수" if param['is_required'] else "🔵 선택"
                    print(f"  • {param['parameter_name']} ({param_type}) = {default_val} [{required}]")
            
            # 파라미터가 없는 변수 분류 및 출력
            categorized = self.categorize_variables(vars_without_params)
            
            print(f"\n=== 파라미터가 없는 변수 ({len(vars_without_params)}개) ===")
            
            for category, var_list in categorized.items():
                if not var_list:
                    continue
                    
                category_names = {
                    'market_data': '📈 시장 데이터',
                    'portfolio_data': '💼 포트폴리오 데이터', 
                    'balance_data': '💰 잔고 데이터',
                    'unknown': '❓ 분류 미정'
                }
                
                print(f"\n{category_names.get(category, category)} ({len(var_list)}개):")
                for var_id, name_ko in var_list:
                    print(f"  ❌ {var_id} ({name_ko})")
            
            # 요약 통계
            total_params = sum(len(params) for params in params_by_var.values())
            print(f"\n📊 요약:")
            print(f"  • 파라미터 있는 변수: {len(params_by_var)}개")
            print(f"  • 파라미터 없는 변수: {len(vars_without_params)}개")
            print(f"  • 총 파라미터 레코드: {total_params}개")
            
            # 분류별 요약
            print(f"\n📋 파라미터 없는 변수 분류:")
            for category, var_list in categorized.items():
                if var_list:
                    category_names = {
                        'market_data': '시장 데이터',
                        'portfolio_data': '포트폴리오 데이터',
                        'balance_data': '잔고 데이터', 
                        'unknown': '분류 미정'
                    }
                    print(f"  • {category_names.get(category, category)}: {len(var_list)}개")
            
        except Exception as e:
            print(f"❌ 분석 실패: {e}")
    
    def run_detailed_analysis(self) -> None:
        """상세 분석 실행 (구조 포함)"""
        self.run_basic_analysis()
        
        print("\n" + "="*80)
        print("🔍 === 상세 구조 분석 ===")
        
        # 테이블 구조 분석
        structure = self.analyze_table_structure()
        
        if structure:
            print(f"\n📋 tv_variable_parameters 테이블 구조:")
            print(f"  • 총 레코드 수: {structure['total_records']}개")
            print(f"  • 컬럼 수: {len(structure['columns'])}개")
            print(f"  • 인덱스 수: {len(structure['indexes'])}개")
            print(f"  • 외래키 수: {len(structure['foreign_keys'])}개")
            
            print(f"\n📊 컬럼 상세 정보:")
            for col in structure['columns']:
                nullable = "NULL 허용" if not col['notnull'] else "NOT NULL"
                default = f", 기본값: {col['dflt_value']}" if col['dflt_value'] else ""
                print(f"  • {col['name']} ({col['type']}) - {nullable}{default}")
    
    def run_validation(self) -> None:
        """무결성 검증 실행"""
        print("🔍 === 파라미터 무결성 검증 ===")
        
        try:
            params_by_var, _ = self.analyze_parameters_by_variable()
            validation_result = self.validate_parameter_integrity(params_by_var)
            
            statistics = validation_result['statistics']
            issues = validation_result['issues']
            integrity_score = validation_result['integrity_score']
            
            # 통계 출력
            print(f"\n📊 파라미터 통계:")
            print(f"  • 파라미터가 있는 변수: {statistics['total_variables_with_params']}개")
            print(f"  • 총 파라미터: {statistics['total_parameters']}개")
            print(f"  • 필수 파라미터: {statistics['required_params']}개")
            print(f"  • 선택 파라미터: {statistics['optional_params']}개")
            
            print(f"\n📋 파라미터 타입 분포:")
            for param_type, count in statistics['parameter_types'].items():
                print(f"  • {param_type}: {count}개")
            
            # 무결성 검증 결과
            print(f"\n🔍 무결성 검증 결과:")
            print(f"  • 무결성 점수: {integrity_score}/100점")
            
            if issues:
                print(f"  • 발견된 이슈: {len(issues)}개")
                print(f"\n⚠️ 상세 이슈 목록:")
                for issue in issues:
                    print(f"    {issue}")
            else:
                print(f"  • ✅ 발견된 이슈 없음 - 모든 파라미터가 정상입니다!")
            
        except Exception as e:
            print(f"❌ 검증 실패: {e}")


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="🔍 Super DB Analyze Parameter Table - 변수 파라미터 테이블 전문 분석 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 기본 파라미터 분석
  python tools/super_db_analyze_parameter_table.py
  
  # 상세 분석 (구조 포함)
  python tools/super_db_analyze_parameter_table.py --detailed
  
  # 무결성 검증
  python tools/super_db_analyze_parameter_table.py --validate
  
  # YAML 내보내기
  python tools/super_db_analyze_parameter_table.py --export
  
  # 모든 옵션 동시 실행
  python tools/super_db_analyze_parameter_table.py --detailed --validate --export
        """
    )
    
    parser.add_argument('--detailed', action='store_true',
                       help='상세 분석 모드 (테이블 구조 포함)')
    
    parser.add_argument('--validate', action='store_true',
                       help='파라미터 무결성 검증 실행')
    
    parser.add_argument('--export', action='store_true',
                       help='YAML 형태로 결과 내보내기')
    
    parser.add_argument('--export-file',
                       help='내보낼 YAML 파일명 (기본값: 자동 생성)')
    
    args = parser.parse_args()
    
    analyzer = SuperDBAnalyzeParameterTable()
    
    try:
        # 기본 분석 또는 상세 분석
        if args.detailed:
            analyzer.run_detailed_analysis()
        else:
            analyzer.run_basic_analysis()
        
        # 무결성 검증
        if args.validate:
            print("\n" + "="*80)
            analyzer.run_validation()
        
        # YAML 내보내기
        if args.export:
            print("\n" + "="*80)
            print("📤 === YAML 내보내기 ===")
            params_by_var, _ = analyzer.analyze_parameters_by_variable()
            analyzer.export_to_yaml(params_by_var, args.export_file)
        
        return 0
        
    except Exception as e:
        print(f"❌ 실행 중 오류 발생: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
