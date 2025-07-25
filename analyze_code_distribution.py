#!/usr/bin/env python3
"""
케이스 시뮬레이션 관련 코드 위치 및 역할 분석
코드 분산 현황과 통합 방안 제시
"""

import os
from pathlib import Path

def analyze_code_distribution():
    """코드 분산 현황 분석"""
    print("🔍 케이스 시뮬레이션 관련 코드 분산 현황 분석")
    print("="*80)
    
    # 코드 파일 위치 및 역할 매핑
    code_locations = {
        "UI 관련 (upbit_auto_trading)": {
            "upbit_auto_trading/ui/desktop/screens/strategy_management/integrated_condition_manager.py": {
                "role": "메인 UI 케이스 시뮬레이션 화면",
                "functions": ["run_simulation()", "generate_simulation_data()", "generate_price_data_for_chart()"],
                "size": "대형 (1515줄)",
                "status": "활성 사용"
            },
            "upbit_auto_trading/ui/desktop/screens/strategy_management/real_data_simulation.py": {
                "role": "UI용 실제 데이터 시뮬레이션 엔진",
                "functions": ["RealDataSimulationEngine", "get_simulation_engine()"],
                "size": "중형 (249줄)",
                "status": "활성 사용"
            }
        },
        
        "스크립트 유틸리티 (scripts/utility)": {
            "scripts/utility/enhanced_real_data_simulation_engine.py": {
                "role": "고급 실제 데이터 시뮬레이션 엔진",
                "functions": ["EnhancedRealDataSimulationEngine", "포트폴리오 관리", "트리거 로직"],
                "size": "대형 (1000줄+)",
                "status": "분리된 고급 시스템"
            },
            "scripts/utility/extended_data_scenario_mapper.py": {
                "role": "확장 데이터 시나리오 매핑",
                "functions": ["ExtendedDataScenarioMapper", "8가지 시나리오 검출"],
                "size": "대형 (500줄+)",
                "status": "독립적 분석 도구"
            }
        },
        
        "프로젝트 루트 (임시/테스트)": {
            "integrated_condition_manager.py": {
                "role": "루트 레벨 조건 매니저 (구버전?)",
                "functions": ["구 통합 조건 관리"],
                "size": "대형",
                "status": "중복/레거시"
            }
        },
        
        "테스트 파일": {
            "test_updated_simulation.py": {
                "role": "업데이트된 시뮬레이션 테스트",
                "functions": ["통합 테스트"],
                "size": "중형",
                "status": "테스트 용도"
            },
            "analyze_data_flow.py": {
                "role": "데이터 흐름 분석",
                "functions": ["흐름 추적"],
                "size": "중형",
                "status": "분석 용도"
            }
        }
    }
    
    # 분석 결과 출력
    for category, files in code_locations.items():
        print(f"\n📁 {category}")
        print("-" * 60)
        
        for file_path, info in files.items():
            # 파일 존재 여부 확인
            full_path = Path(file_path)
            exists = "✅" if full_path.exists() else "❌"
            
            print(f"{exists} {file_path}")
            print(f"   🎯 역할: {info['role']}")
            print(f"   ⚙️ 주요 기능: {', '.join(info['functions'])}")
            print(f"   📊 크기: {info['size']}")
            print(f"   📋 상태: {info['status']}")

def analyze_code_relationships():
    """코드 간 관계 분석"""
    print(f"\n🔗 코드 간 관계 및 의존성")
    print("="*80)
    
    relationships = [
        {
            "from": "UI integrated_condition_manager.py",
            "to": "UI real_data_simulation.py", 
            "relationship": "직접 import 및 사용",
            "purpose": "실제 데이터 기반 시뮬레이션"
        },
        {
            "from": "UI real_data_simulation.py",
            "to": "data/market_data.sqlite3",
            "relationship": "SQLite 직접 쿼리",
            "purpose": "KRW-BTC 시장 데이터 로드"
        },
        {
            "from": "scripts/utility/enhanced_real_data_simulation_engine.py",
            "to": "data/upbit_auto_trading.sqlite3",
            "relationship": "SQLite 쿼리 (다른 DB)",
            "purpose": "고급 시뮬레이션 (분리됨)"
        },
        {
            "from": "scripts/utility/extended_data_scenario_mapper.py",
            "to": "data/upbit_auto_trading.sqlite3",
            "relationship": "SQLite 쿼리",
            "purpose": "시나리오 매핑 (독립적)"
        },
        {
            "from": "루트 integrated_condition_manager.py",
            "to": "UI integrated_condition_manager.py",
            "relationship": "중복/레거시 관계",
            "purpose": "역할 불분명"
        }
    ]
    
    for rel in relationships:
        print(f"📎 {rel['from']}")
        print(f"   ↓ {rel['relationship']}")
        print(f"   📍 {rel['to']}")
        print(f"   🎯 목적: {rel['purpose']}")
        print()

def recommend_code_organization():
    """코드 구조 개선 권장사항"""
    print(f"💡 코드 구조 개선 권장사항")
    print("="*80)
    
    recommendations = [
        {
            "category": "🎯 핵심 활성 코드 (upbit_auto_trading)",
            "files": [
                "upbit_auto_trading/ui/desktop/screens/strategy_management/integrated_condition_manager.py",
                "upbit_auto_trading/ui/desktop/screens/strategy_management/real_data_simulation.py"
            ],
            "status": "✅ 현재 상태 양호",
            "action": "유지 - UI 케이스 시뮬레이션 정상 동작"
        },
        {
            "category": "🔧 유용한 독립 도구 (scripts/utility)",
            "files": [
                "scripts/utility/enhanced_real_data_simulation_engine.py",
                "scripts/utility/extended_data_scenario_mapper.py"
            ],
            "status": "⚠️ 분리된 고급 시스템",
            "action": "필요시 통합 검토 - 현재는 독립적 분석 도구로 활용"
        },
        {
            "category": "🗑️ 정리 대상",
            "files": [
                "integrated_condition_manager.py (루트)",
                "test_*.py (테스트 파일들)",
                "analyze_*.py (분석 파일들)"
            ],
            "status": "❌ 중복/임시 파일",
            "action": "archive 폴더로 이동 또는 삭제"
        }
    ]
    
    for rec in recommendations:
        print(f"\n{rec['category']}")
        print("-" * 60)
        for file in rec['files']:
            print(f"  📄 {file}")
        print(f"📊 상태: {rec['status']}")
        print(f"🔨 권장사항: {rec['action']}")

def main():
    """메인 분석 실행"""
    print("🚀 케이스 시뮬레이션 코드 분산 현황 종합 분석")
    print("="*100)
    
    # 1. 코드 분산 현황
    analyze_code_distribution()
    
    # 2. 코드 간 관계
    analyze_code_relationships()
    
    # 3. 개선 권장사항
    recommend_code_organization()
    
    # 결론
    print(f"\n" + "="*100)
    print("🎯 결론")
    print("="*100)
    
    print("📊 현재 상황:")
    print("   ✅ UI 케이스 시뮬레이션: upbit_auto_trading 폴더에서 정상 동작")
    print("   ✅ 실제 데이터 연동: market_data.sqlite3 직접 쿼리로 의미있는 결과")
    print("   ⚠️ 코드 분산: 여러 위치에 유사 기능 중복 존재")
    print("   🔧 독립 도구: scripts/utility에 고급 분석 도구들")
    
    print(f"\n📋 권장사항:")
    print("   1️⃣ 핵심 기능 유지: upbit_auto_trading의 UI 시뮬레이션은 현재 상태 유지")
    print("   2️⃣ 중복 제거: 루트 레벨 중복 파일들 정리")
    print("   3️⃣ 독립 도구 활용: scripts/utility 도구들은 필요시 별도 실행")
    print("   4️⃣ 테스트 파일 정리: 임시 테스트/분석 파일들 archive로 이동")

if __name__ == "__main__":
    main()
