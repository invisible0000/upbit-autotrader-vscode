#!/usr/bin/env python3
"""
🔧 Super DB Debug Path Mapping Tool v1.0
DB 경로 및 매핑 문제 진단 및 해결을 위한 종합 도구

Purpose:
- 3-Database 아키텍처 경로 설정 검증
- 테이블 매핑 정확성 확인
- DB 연결 상태 및 스키마 검증
- Global DB Manager 상태 진단
- 실제 데이터 로딩 테스트

Usage:
    python tools/super_db_debug_path_mapping.py
    python tools/super_db_debug_path_mapping.py --full-test
    python tools/super_db_debug_path_mapping.py --table-mapping-check
    python tools/super_db_debug_path_mapping.py --connection-test

Author: Upbit Auto Trading Team
Created: 2025-08-01
Updated: 2025-08-01 - Initial Super Tool Release
"""

import os
import sys
import sqlite3
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 프로젝트 루트 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from upbit_auto_trading.config.database_paths import (
        TableMappings, 
        SETTINGS_DB_PATH, STRATEGIES_DB_PATH, MARKET_DATA_DB_PATH
    )
    from upbit_auto_trading.components.core.global_db_manager import GlobalDBManager
    from upbit_auto_trading.components.core.condition_storage import ConditionStorage
    from upbit_auto_trading.utils.debug_logger import get_logger
except ImportError as e:
    print(f"❌ 모듈 임포트 실패: {e}")
    print("🔍 대체 방법으로 기본 테스트를 실행합니다...")
    
    # 기본 임포트만 사용
    from upbit_auto_trading.config.database_paths import (
        TableMappings, 
        SETTINGS_DB_PATH, STRATEGIES_DB_PATH, MARKET_DATA_DB_PATH
    )
    GlobalDBManager = None
    ConditionStorage = None
    get_logger = lambda name: type('Logger', (), {'info': print, 'error': print, 'warning': print})()

logger = get_logger("SuperDBDebugPathMapping")


class SuperDBDebugPathMapping:
    """DB 경로 및 매핑 진단 도구"""
    
    def __init__(self):
        """초기화"""
        self.db_paths = {
            'settings': SETTINGS_DB_PATH,
            'strategies': STRATEGIES_DB_PATH,
            'market_data': MARKET_DATA_DB_PATH
        }
        self.results = {
            'path_check': {},
            'mapping_check': {},
            'connection_check': {},
            'data_check': {},
            'global_manager_check': {}
        }
    
    def run_full_diagnosis(self) -> Dict:
        """전체 진단 실행"""
        print("🔧 Super DB Debug Path Mapping Tool v1.0")
        print("=" * 60)
        
        self.check_database_paths()
        self.check_table_mappings()
        self.check_database_connections()
        self.check_global_db_manager()
        self.check_condition_storage()
        self.test_actual_data_loading()
        
        return self.generate_summary_report()
    
    def check_database_paths(self) -> None:
        """데이터베이스 경로 검증"""
        print("\n📂 Phase 1: 데이터베이스 경로 검증")
        print("-" * 40)
        
        for db_name, db_path in self.db_paths.items():
            exists = os.path.exists(db_path)
            size = os.path.getsize(db_path) if exists else 0
            
            status = "✅" if exists else "❌"
            print(f"{status} {db_name}: {db_path}")
            if exists:
                print(f"   📊 파일 크기: {size:,} bytes")
            
            self.results['path_check'][db_name] = {
                'path': db_path,
                'exists': exists,
                'size': size
            }
    
    def check_table_mappings(self) -> None:
        """테이블 매핑 검증"""
        print("\n🗂️ Phase 2: 테이블 매핑 검증")
        print("-" * 40)
        
        # 각 카테고리별 테이블 수 확인
        settings_tables = len(TableMappings.SETTINGS_TABLES)
        strategies_tables = len(TableMappings.STRATEGIES_TABLES)
        market_data_tables = len(TableMappings.MARKET_DATA_TABLES)
        total_tables = settings_tables + strategies_tables + market_data_tables
        
        print(f"📊 설정 테이블: {settings_tables}개")
        print(f"📊 전략 테이블: {strategies_tables}개")
        print(f"📊 시장 데이터 테이블: {market_data_tables}개")
        print(f"📊 총 테이블 매핑: {total_tables}개")
        
        # 중요 테이블 매핑 확인
        critical_tables = [
            'trading_conditions', 'strategies', 'tv_trading_variables',
            'market_data', 'cfg_app_settings'
        ]
        
        print("\n🎯 중요 테이블 매핑 확인:")
        for table in critical_tables:
            db_path = TableMappings.get_db_for_table(table)
            print(f"   {table} → {os.path.basename(db_path)}")
            
            self.results['mapping_check'][table] = {
                'mapped_db': db_path,
                'db_name': os.path.basename(db_path)
            }
    
    def check_database_connections(self) -> None:
        """데이터베이스 연결 테스트"""
        print("\n🔌 Phase 3: 데이터베이스 연결 테스트")
        print("-" * 40)
        
        for db_name, db_path in self.db_paths.items():
            if not os.path.exists(db_path):
                print(f"❌ {db_name}: 파일 없음")
                self.results['connection_check'][db_name] = {
                    'connectable': False,
                    'error': 'File not exists'
                }
                continue
            
            try:
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    table_count = len(tables)
                    
                    print(f"✅ {db_name}: 연결 성공, {table_count}개 테이블")
                    
                    self.results['connection_check'][db_name] = {
                        'connectable': True,
                        'table_count': table_count,
                        'tables': tables[:5]  # 처음 5개만 저장
                    }
                    
            except Exception as e:
                print(f"❌ {db_name}: 연결 실패 - {e}")
                self.results['connection_check'][db_name] = {
                    'connectable': False,
                    'error': str(e)
                }
    
    def check_global_db_manager(self) -> None:
        """Global DB Manager 상태 확인"""
        print("\n🌐 Phase 4: Global DB Manager 상태 확인")
        print("-" * 40)
        
        if GlobalDBManager is None:
            print("⚠️ Global DB Manager 모듈을 찾을 수 없음 - 스킵")
            self.results['global_manager_check']['status'] = 'module_not_found'
            return
        
        try:
            db_manager = GlobalDBManager()
            
            # 각 DB 연결 테스트
            for db_name in ['settings', 'strategies', 'market_data']:
                try:
                    conn_method = getattr(db_manager, f'get_{db_name}_connection')
                    conn = conn_method()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT 1")
                        result = cursor.fetchone()
                        conn.close()
                        
                        print(f"✅ Global Manager - {db_name}: 연결 성공")
                        self.results['global_manager_check'][db_name] = {
                            'status': 'success',
                            'method': f'get_{db_name}_connection'
                        }
                    else:
                        print(f"❌ Global Manager - {db_name}: 연결 객체 None")
                        self.results['global_manager_check'][db_name] = {
                            'status': 'failed_null_connection',
                            'method': f'get_{db_name}_connection'
                        }
                        
                except Exception as e:
                    print(f"❌ Global Manager - {db_name}: {e}")
                    self.results['global_manager_check'][db_name] = {
                        'status': 'error',
                        'error': str(e),
                        'method': f'get_{db_name}_connection'
                    }
                    
        except Exception as e:
            print(f"❌ Global DB Manager 초기화 실패: {e}")
            self.results['global_manager_check']['initialization'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def check_condition_storage(self) -> None:
        """ConditionStorage 연결 및 동작 확인"""
        print("\n💾 Phase 5: ConditionStorage 테스트")
        print("-" * 40)
        
        if ConditionStorage is None:
            print("⚠️ ConditionStorage 모듈을 찾을 수 없음 - 스킵")
            self.results['data_check']['condition_storage'] = {
                'status': 'module_not_found'
            }
            return
        
        try:
            condition_storage = ConditionStorage()
            
            # 조건 개수 확인
            conditions = condition_storage.load_all_conditions()
            condition_count = len(conditions)
            
            print("✅ 조건 저장소 초기화 완료")
            print(f"📊 저장된 조건 개수: {condition_count}")
            
            if condition_count > 0:
                print("🔍 첫 번째 조건 정보:")
                first_condition = conditions[0]
                print(f"   ID: {first_condition.get('id', 'N/A')}")
                print(f"   이름: {first_condition.get('name', 'N/A')}")
                print(f"   생성일: {first_condition.get('created_at', 'N/A')}")
            
            self.results['data_check']['condition_storage'] = {
                'status': 'success',
                'condition_count': condition_count,
                'has_data': condition_count > 0
            }
            
        except Exception as e:
            print(f"❌ ConditionStorage 오류: {e}")
            self.results['data_check']['condition_storage'] = {
                'status': 'error',
                'error': str(e)
            }
    
    def test_actual_data_loading(self) -> None:
        """실제 데이터 로딩 테스트"""
        print("\n🧪 Phase 6: 실제 데이터 로딩 테스트")
        print("-" * 40)
        
        # TV Trading Variables 테스트
        try:
            tv_db_path = TableMappings.get_db_for_table('tv_trading_variables')
            with sqlite3.connect(tv_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM tv_trading_variables")
                tv_count = cursor.fetchone()[0]
                
                print(f"✅ TV Trading Variables: {tv_count}개 변수")
                self.results['data_check']['tv_variables'] = {
                    'status': 'success',
                    'count': tv_count
                }
                
        except Exception as e:
            print(f"❌ TV Variables 로딩 실패: {e}")
            self.results['data_check']['tv_variables'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Strategies 테이블 테스트
        try:
            strategies_db_path = TableMappings.get_db_for_table('strategies')
            with sqlite3.connect(strategies_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='strategies'")
                if cursor.fetchone():
                    cursor.execute("SELECT COUNT(*) FROM strategies")
                    strategy_count = cursor.fetchone()[0]
                    print(f"✅ Strategies: {strategy_count}개 전략")
                    self.results['data_check']['strategies'] = {
                        'status': 'success',
                        'count': strategy_count
                    }
                else:
                    print("⚠️ Strategies 테이블 없음")
                    self.results['data_check']['strategies'] = {
                        'status': 'table_not_found'
                    }
                    
        except Exception as e:
            print(f"❌ Strategies 로딩 실패: {e}")
            self.results['data_check']['strategies'] = {
                'status': 'error',
                'error': str(e)
            }
    
    def generate_summary_report(self) -> Dict:
        """종합 진단 리포트 생성"""
        print("\n📋 Phase 7: 종합 진단 리포트")
        print("=" * 60)
        
        # 성공/실패 카운트
        success_count = 0
        total_checks = 0
        
        # 경로 체크
        for db_check in self.results['path_check'].values():
            total_checks += 1
            if db_check['exists']:
                success_count += 1
        
        # 연결 체크
        for conn_check in self.results['connection_check'].values():
            total_checks += 1
            if conn_check['connectable']:
                success_count += 1
        
        # 글로벌 매니저 체크
        for gm_check in self.results['global_manager_check'].values():
            total_checks += 1
            if isinstance(gm_check, dict) and gm_check.get('status') == 'success':
                success_count += 1
        
        # 데이터 체크
        for data_check in self.results['data_check'].values():
            total_checks += 1
            if isinstance(data_check, dict) and data_check.get('status') == 'success':
                success_count += 1
        
        success_rate = (success_count / total_checks * 100) if total_checks > 0 else 0
        
        print(f"📊 전체 성공률: {success_rate:.1f}% ({success_count}/{total_checks})")
        
        # 문제점 요약
        issues = []
        
        # 경로 문제
        for db_name, check in self.results['path_check'].items():
            if not check['exists']:
                issues.append(f"DB 파일 없음: {db_name}")
        
        # 연결 문제
        for db_name, check in self.results['connection_check'].items():
            if not check['connectable']:
                issues.append(f"DB 연결 실패: {db_name}")
        
        # 글로벌 매니저 문제
        for db_name, check in self.results['global_manager_check'].items():
            if isinstance(check, dict) and check.get('status') != 'success':
                issues.append(f"Global Manager 오류: {db_name}")
            elif isinstance(check, str) and check != 'success':
                issues.append(f"Global Manager 문제: {db_name} - {check}")
        
        if issues:
            print("\n⚠️ 발견된 문제점:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        else:
            print("\n✅ 모든 검사 통과!")
        
        # 권장사항
        recommendations = []
        
        if success_rate < 100:
            recommendations.append("DB 파일 경로 및 권한 확인")
            recommendations.append("Global DB Manager 설정 검토")
        
        # 데이터 체크에서 오류가 있는지 확인
        data_check_errors = False
        for check in self.results['data_check'].values():
            if isinstance(check, dict) and check.get('status') == 'error':
                data_check_errors = True
                break
        
        if data_check_errors:
            recommendations.append("테이블 스키마 및 데이터 무결성 검증")
        
        if recommendations:
            print("\n💡 권장사항:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        return {
            'success_rate': success_rate,
            'total_checks': total_checks,
            'success_count': success_count,
            'issues': issues,
            'recommendations': recommendations,
            'detailed_results': self.results
        }
    
    def run_table_mapping_check(self) -> None:
        """테이블 매핑 전용 검사"""
        print("🗂️ Table Mapping Check Mode")
        print("=" * 40)
        
        self.check_table_mappings()
        
        # 매핑 충돌 검사
        all_tables = {}
        all_tables.update(TableMappings.SETTINGS_TABLES)
        all_tables.update(TableMappings.STRATEGIES_TABLES)
        all_tables.update(TableMappings.MARKET_DATA_TABLES)
        
        # 중복 테이블명 검사
        table_names = list(all_tables.keys())
        duplicates = [name for name in table_names if table_names.count(name) > 1]
        
        if duplicates:
            print(f"\n⚠️ 중복 테이블명 발견: {duplicates}")
        else:
            print("\n✅ 테이블명 중복 없음")
    
    def run_connection_test(self) -> None:
        """연결 테스트 전용"""
        print("🔌 Connection Test Mode")
        print("=" * 40)
        
        self.check_database_paths()
        self.check_database_connections()
        self.check_global_db_manager()


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Super DB Debug Path Mapping Tool')
    parser.add_argument('--full-test', action='store_true', 
                       help='전체 진단 실행')
    parser.add_argument('--table-mapping-check', action='store_true',
                       help='테이블 매핑 검사만 실행')
    parser.add_argument('--connection-test', action='store_true',
                       help='연결 테스트만 실행')
    
    args = parser.parse_args()
    
    tool = SuperDBDebugPathMapping()
    
    if args.table_mapping_check:
        tool.run_table_mapping_check()
    elif args.connection_test:
        tool.run_connection_test()
    else:
        # 기본값 또는 --full-test
        report = tool.run_full_diagnosis()
        
        # JSON 결과 저장 (선택적)
        if args.full_test:
            import json
            report_path = PROJECT_ROOT / "logs" / "db_debug_report.json"
            report_path.parent.mkdir(exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"\n📄 상세 리포트 저장: {report_path}")


if __name__ == "__main__":
    main()
