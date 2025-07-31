#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스 분석 도구
settings.sqlite3의 테이블 구조와 데이터를 분석하여 마이그레이션 위험도를 평가합니다.

Usage:
    python db_analysis_tool.py
"""

import sqlite3
import os
import json
from typing import Dict, List, Tuple, Any
from pathlib import Path


class DatabaseAnalyzer:
    """데이터베이스 분석 클래스"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.results = {}
        
    def check_file_exists(self) -> bool:
        """데이터베이스 파일 존재 여부 확인"""
        exists = self.db_path.exists()
        print(f"🔍 데이터베이스 파일: {self.db_path}")
        print(f"📁 파일 존재 여부: {'✅ 존재' if exists else '❌ 없음'}")
        
        if exists:
            size_mb = self.db_path.stat().st_size / (1024 * 1024)
            print(f"📊 파일 크기: {size_mb:.2f} MB")
            
        return exists
    
    def get_table_list(self) -> List[str]:
        """모든 테이블 목록 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [row[0] for row in cursor.fetchall()]
                
                print(f"\n📊 총 테이블 수: {len(tables)}")
                print("\n📋 테이블 목록:")
                for table in tables:
                    print(f"  📦 {table}")
                
                return tables
                
        except Exception as e:
            print(f"❌ 테이블 목록 조회 오류: {e}")
            return []
    
    def analyze_table_data(self, tables: List[str]) -> Dict[str, int]:
        """각 테이블의 데이터 수 분석"""
        table_counts = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                print("\n🔢 테이블별 데이터 수:")
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        table_counts[table] = count
                        
                        # 데이터가 있는 테이블 강조
                        status = "📊" if count > 0 else "🗂️"
                        print(f"  {status} {table}: {count:,}개 레코드")
                        
                    except Exception as e:
                        print(f"  ❌ {table}: 분석 실패 ({e})")
                        table_counts[table] = -1
                
                return table_counts
                
        except Exception as e:
            print(f"❌ 테이블 데이터 분석 오류: {e}")
            return {}
    
    def analyze_table_structure(self, tables: List[str]) -> Dict[str, List[Dict]]:
        """테이블 구조 분석"""
        table_structures = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                print("\n🏗️ 테이블 구조 분석:")
                for table in tables:
                    try:
                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = []
                        for row in cursor.fetchall():
                            column_info = {
                                'cid': row[0],
                                'name': row[1],
                                'type': row[2],
                                'notnull': row[3],
                                'default': row[4],
                                'pk': row[5]
                            }
                            columns.append(column_info)
                        
                        table_structures[table] = columns
                        print(f"  🏗️ {table}: {len(columns)}개 컬럼")
                        
                    except Exception as e:
                        print(f"  ❌ {table}: 구조 분석 실패 ({e})")
                        table_structures[table] = []
                
                return table_structures
                
        except Exception as e:
            print(f"❌ 테이블 구조 분석 오류: {e}")
            return {}
    
    def categorize_risk_level(self, table_name: str, record_count: int) -> str:
        """위험도 레벨 분류"""
        # 핵심 테이블들
        critical_tables = {
            'app_settings', 'system_settings', 'strategies', 
            'strategy_components', 'strategy_conditions', 'strategy_execution'
        }
        
        # 중요 테이블들
        important_tables = {
            'trading_conditions', 'execution_history', 'chart_layout_templates',
            'chart_variables', 'backup_info'
        }
        
        # 시뮬레이션 관련
        simulation_tables = {
            'simulation_sessions', 'simulation_trades', 'simulation_market_data'
        }
        
        # 시스템/로그 테이블
        system_tables = {
            'variable_compatibility_rules', 'variable_usage_logs', 
            'component_strategy', 'sqlite_sequence'
        }
        
        # 트리거 빌더 시스템 테이블 (새로운 스키마에서 유지)
        trigger_builder_tables = {
            'tv_comparison_groups', 'tv_help_texts', 'tv_indicator_categories',
            'tv_indicator_library', 'tv_parameter_types', 'tv_placeholder_texts',
            'tv_schema_version', 'tv_trading_variables', 'tv_variable_parameters',
            'tv_workflow_guides'
        }
        
        if table_name in critical_tables:
            if record_count > 0:
                return "🔴 CRITICAL (데이터 있음)"
            else:
                return "🟠 CRITICAL (데이터 없음)"
        elif table_name in important_tables:
            if record_count > 0:
                return "🟡 IMPORTANT (데이터 있음)"
            else:
                return "🟨 IMPORTANT (데이터 없음)"
        elif table_name in simulation_tables:
            return "🔵 SIMULATION"
        elif table_name in system_tables:
            return "🟢 SYSTEM/LOG"
        elif table_name in trigger_builder_tables:
            if record_count > 0:
                return "🟦 TRIGGER_BUILDER (데이터 있음) - 유지됨"
            else:
                return "🟦 TRIGGER_BUILDER (데이터 없음) - 유지됨"
        else:
            return "⚪ UNKNOWN"
    
    def generate_risk_report(self, table_counts: Dict[str, int]) -> None:
        """위험도 보고서 생성"""
        print("\n" + "="*60)
        print("🚨 마이그레이션 위험도 분석 보고서")
        print("="*60)
        
        # 위험도별 분류
        risk_categories = {
            'critical_with_data': [],
            'critical_no_data': [],
            'important_with_data': [],
            'important_no_data': [],
            'simulation': [],
            'system': [],
            'trigger_builder_with_data': [],
            'trigger_builder_no_data': [],
            'unknown': []
        }
        
        for table, count in table_counts.items():
            if count == -1:  # 분석 실패
                continue
                
            risk_level = self.categorize_risk_level(table, count)
            
            if "CRITICAL" in risk_level and "데이터 있음" in risk_level:
                risk_categories['critical_with_data'].append((table, count))
            elif "CRITICAL" in risk_level and "데이터 없음" in risk_level:
                risk_categories['critical_no_data'].append((table, count))
            elif "IMPORTANT" in risk_level and "데이터 있음" in risk_level:
                risk_categories['important_with_data'].append((table, count))
            elif "IMPORTANT" in risk_level and "데이터 없음" in risk_level:
                risk_categories['important_no_data'].append((table, count))
            elif "SIMULATION" in risk_level:
                risk_categories['simulation'].append((table, count))
            elif "SYSTEM" in risk_level:
                risk_categories['system'].append((table, count))
            elif "TRIGGER_BUILDER" in risk_level and "데이터 있음" in risk_level:
                risk_categories['trigger_builder_with_data'].append((table, count))
            elif "TRIGGER_BUILDER" in risk_level and "데이터 없음" in risk_level:
                risk_categories['trigger_builder_no_data'].append((table, count))
            else:
                risk_categories['unknown'].append((table, count))
        
        # 보고서 출력
        print("\n🔴 **최고 위험** - 핵심 테이블 (데이터 보유):")
        for table, count in risk_categories['critical_with_data']:
            print(f"  ⚠️ {table}: {count:,}개 레코드 ← 삭제 시 프로그램 중단 위험")
        
        print("\n🟠 **고위험** - 핵심 테이블 (데이터 없음):")
        for table, count in risk_categories['critical_no_data']:
            print(f"  ⚠️ {table}: {count}개 레코드 ← 테이블 구조 필요")
        
        print("\n🟡 **중위험** - 중요 테이블 (데이터 보유):")
        for table, count in risk_categories['important_with_data']:
            print(f"  📊 {table}: {count:,}개 레코드 ← 기능 저하 가능")
        
        print("\n🟨 **중위험** - 중요 테이블 (데이터 없음):")
        for table, count in risk_categories['important_no_data']:
            print(f"  📊 {table}: {count}개 레코드")
        
        print("\n🔵 **저위험** - 시뮬레이션 관련:")
        for table, count in risk_categories['simulation']:
            print(f"  🎮 {table}: {count:,}개 레코드")
        
        print("\n🟢 **최소위험** - 시스템/로그:")
        for table, count in risk_categories['system']:
            print(f"  🔧 {table}: {count:,}개 레코드")
        
        print("\n🟦 **유지됨** - 트리거 빌더 시스템 (데이터 있음):")
        for table, count in risk_categories['trigger_builder_with_data']:
            print(f"  🔄 {table}: {count:,}개 레코드 ← 새 스키마에서 유지")
        
        print("\n🟦 **유지됨** - 트리거 빌더 시스템 (데이터 없음):")
        for table, count in risk_categories['trigger_builder_no_data']:
            print(f"  🔄 {table}: {count}개 레코드 ← 새 스키마에서 유지")
        
        if risk_categories['unknown']:
            print("\n⚪ **미분류** - 추가 분석 필요:")
            for table, count in risk_categories['unknown']:
                print(f"  ❓ {table}: {count:,}개 레코드")
        
        # 요약
        total_critical_data = len(risk_categories['critical_with_data'])
        total_important_data = len(risk_categories['important_with_data'])
        total_trigger_builder = len(risk_categories['trigger_builder_with_data']) + len(risk_categories['trigger_builder_no_data'])
        
        print(f"\n📋 **위험도 요약**:")
        print(f"  🔴 데이터 보유 핵심 테이블: {total_critical_data}개")
        print(f"  🟡 데이터 보유 중요 테이블: {total_important_data}개")
        print(f"  🟦 유지되는 트리거 빌더 테이블: {total_trigger_builder}개")
        print(f"  ⚠️ 총 위험 테이블: {total_critical_data + total_important_data}개")
        
        if total_critical_data > 0:
            print(f"\n🚨 **긴급 권고**: {total_critical_data}개의 핵심 테이블에 데이터가 있습니다.")
            print("   현재 상태로 마이그레이션 시 프로그램이 작동하지 않을 수 있습니다!")
            
        print(f"\n💡 **마이그레이션 분석**:")
        print(f"  ✅ 안전하게 유지: {total_trigger_builder}개 (트리거 빌더 시스템)")
        print(f"  ⚠️ 삭제 위험: {total_critical_data + total_important_data}개 (핵심/중요 테이블)")
        
        # 삭제될 테이블 중 데이터가 있는 것들
        total_deletion_risk = 0
        for category in ['critical_with_data', 'important_with_data', 'simulation', 'system']:
            total_deletion_risk += len(risk_categories[category])
        
        if total_deletion_risk > 0:
            print(f"  🚨 데이터 손실 위험: {total_deletion_risk}개 테이블이 삭제될 예정입니다!")
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """전체 분석 실행"""
        print("🔍 settings.sqlite3 데이터베이스 전면 분석 시작...")
        print("="*60)
        
        # 1. 파일 존재 확인
        if not self.check_file_exists():
            return {'error': 'Database file not found'}
        
        # 2. 테이블 목록 조회
        tables = self.get_table_list()
        if not tables:
            return {'error': 'No tables found'}
        
        # 3. 테이블 데이터 수 분석
        table_counts = self.analyze_table_data(tables)
        
        # 4. 테이블 구조 분석
        table_structures = self.analyze_table_structure(tables)
        
        # 5. 위험도 보고서 생성
        self.generate_risk_report(table_counts)
        
        # 결과 정리
        self.results = {
            'db_path': str(self.db_path),
            'total_tables': len(tables),
            'table_list': tables,
            'table_counts': table_counts,
            'table_structures': table_structures,
            'analysis_timestamp': str(Path().cwd())
        }
        
        return self.results
    
    def save_results(self, output_file: str = "db_analysis_results.json") -> None:
        """분석 결과를 JSON 파일로 저장"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 분석 결과 저장: {output_file}")
        except Exception as e:
            print(f"❌ 결과 저장 실패: {e}")


def main():
    """메인 실행 함수"""
    # 데이터베이스 경로 설정
    db_path = r"upbit_auto_trading\data\settings.sqlite3"
    
    # 분석기 생성 및 실행
    analyzer = DatabaseAnalyzer(db_path)
    results = analyzer.run_full_analysis()
    
    if 'error' not in results:
        # 결과 저장
        analyzer.save_results("tools/db_analysis_results.json")
        
        print("\n" + "="*60)
        print("✅ 데이터베이스 분석 완료!")
        print("📋 다음 단계: 위험도가 높은 테이블들의 코드 참조 분석")
        print("="*60)
    else:
        print(f"\n❌ 분석 실패: {results['error']}")


if __name__ == "__main__":
    main()
