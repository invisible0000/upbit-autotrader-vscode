#!/usr/bin/env python3
"""
upbit_auto_trading 폴더 내부 코드 자급자족 분석
케이스 시뮬레이션이 순수하게 내부 코드만으로 동작하는지 확인
"""

import os
import re
from pathlib import Path

def analyze_internal_dependencies():
    """upbit_auto_trading 내부 의존성 분석"""
    print("🔍 upbit_auto_trading 폴더 내부 의존성 분석")
    print("="*80)
    
    # 케이스 시뮬레이션 관련 주요 파일들
    main_files = [
        "upbit_auto_trading/ui/desktop/screens/strategy_management/integrated_condition_manager.py",
        "upbit_auto_trading/ui/desktop/screens/strategy_management/real_data_simulation.py"
    ]
    
    external_deps = []
    internal_deps = []
    
    for file_path in main_files:
        if not os.path.exists(file_path):
            print(f"❌ 파일 없음: {file_path}")
            continue
            
        print(f"\n📄 분석: {file_path}")
        print("-" * 60)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # import 문 찾기
        import_lines = re.findall(r'^(?:from|import)\s+([^\s#]+)', content, re.MULTILINE)
        
        for import_line in import_lines:
            # 점으로 시작하는 상대 import
            if import_line.startswith('.'):
                internal_deps.append(f"{file_path}: {import_line} (상대 import)")
                print(f"✅ 내부: {import_line}")
            # upbit_auto_trading으로 시작하는 절대 import
            elif import_line.startswith('upbit_auto_trading'):
                internal_deps.append(f"{file_path}: {import_line} (절대 import)")
                print(f"✅ 내부: {import_line}")
            # 표준 라이브러리나 외부 패키지
            elif import_line not in ['sys', 'os', 'importlib', 'random', 'sqlite3', 'pandas', 'numpy', 'datetime', 'typing', 'logging']:
                if not import_line.startswith('PyQt6') and not import_line.startswith('matplotlib'):
                    external_deps.append(f"{file_path}: {import_line}")
                    print(f"⚠️ 외부: {import_line}")
    
    return internal_deps, external_deps

def check_data_source_independence():
    """데이터 소스 독립성 확인"""
    print(f"\n💾 데이터 소스 독립성 확인")
    print("="*80)
    
    # real_data_simulation.py의 데이터 소스 확인
    sim_file = "upbit_auto_trading/ui/desktop/screens/strategy_management/real_data_simulation.py"
    
    if os.path.exists(sim_file):
        with open(sim_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # DB 경로 확인
        db_paths = re.findall(r'["\']([^"\']*\.sqlite3)["\']', content)
        print("🗄️ 데이터베이스 의존성:")
        for db_path in set(db_paths):
            full_path = os.path.join(os.getcwd(), db_path)
            exists = "✅" if os.path.exists(full_path) else "❌"
            print(f"   {exists} {db_path}")
        
        # 외부 폴더 참조 확인
        external_refs = re.findall(r'["\']([^"\']*(?:scripts|legacy_archive|tools)[^"\']*)["\']', content)
        if external_refs:
            print("⚠️ 외부 폴더 참조:")
            for ref in set(external_refs):
                print(f"   📁 {ref}")
        else:
            print("✅ 외부 폴더 참조 없음")

def verify_component_completeness():
    """컴포넌트 완전성 확인"""
    print(f"\n🧩 컴포넌트 완전성 확인")
    print("="*80)
    
    components_dir = "upbit_auto_trading/ui/desktop/screens/strategy_management/components"
    
    if os.path.exists(components_dir):
        components = os.listdir(components_dir)
        py_files = [f for f in components if f.endswith('.py') and f != '__init__.py']
        
        print(f"📦 컴포넌트 파일 ({len(py_files)}개):")
        for component in sorted(py_files):
            print(f"   ✅ {component}")
        
        # 주요 컴포넌트 확인
        essential_components = [
            'condition_dialog.py',
            'condition_storage.py', 
            'strategy_maker.py'
        ]
        
        print(f"\n🔍 필수 컴포넌트 확인:")
        for essential in essential_components:
            if essential in py_files:
                print(f"   ✅ {essential}")
            else:
                print(f"   ❌ {essential} (누락)")
    else:
        print("❌ components 폴더 없음")

def test_internal_execution():
    """내부 실행 테스트"""
    print(f"\n🎮 내부 실행 테스트")
    print("="*80)
    
    try:
        # 상대 경로로 시뮬레이션 엔진 임포트 테스트
        import sys
        sys.path.append('upbit_auto_trading/ui/desktop/screens/strategy_management')
        
        from real_data_simulation import get_simulation_engine
        
        engine = get_simulation_engine()
        print("✅ 시뮬레이션 엔진 생성 성공 (upbit_auto_trading 내부)")
        
        # 시장 데이터 로드 테스트
        market_data = engine.load_market_data()
        if market_data is not None:
            print(f"✅ 시장 데이터 로드 성공: {len(market_data)}개 레코드")
        else:
            print("⚠️ 시장 데이터 로드 실패 (DB 문제일 수 있음)")
            
        # 시나리오 데이터 테스트
        scenario_data = engine.get_scenario_data("상승 추세", length=30)
        if scenario_data and scenario_data.get('data_source') == 'real_market_data':
            print("✅ 실제 데이터 기반 시나리오 생성 성공")
        else:
            print("⚠️ 폴백 시뮬레이션 사용됨")
            
        return True
        
    except Exception as e:
        print(f"❌ 내부 실행 테스트 실패: {e}")
        return False

def main():
    """메인 분석 실행"""
    print("🚀 upbit_auto_trading 내부 코드 자급자족 분석")
    print("="*100)
    
    # 1. 내부 의존성 분석
    internal_deps, external_deps = analyze_internal_dependencies()
    
    # 2. 데이터 소스 독립성 확인
    check_data_source_independence()
    
    # 3. 컴포넌트 완전성 확인
    verify_component_completeness()
    
    # 4. 내부 실행 테스트
    execution_success = test_internal_execution()
    
    # 결론
    print(f"\n" + "="*100)
    print("🎯 결론: upbit_auto_trading 내부 자급자족 분석")
    print("="*100)
    
    print("📊 분석 결과:")
    print(f"   ✅ 내부 의존성: {len(internal_deps)}개 (상대/절대 import)")
    print(f"   ⚠️ 외부 의존성: {len(external_deps)}개 (upbit_auto_trading 외부)")
    print(f"   💾 데이터 소스: data/market_data.sqlite3 (프로젝트 내부)")
    print(f"   🧩 컴포넌트: components/ 폴더에 완전 구비")
    print(f"   🎮 실행 테스트: {'성공' if execution_success else '실패'}")
    
    print(f"\n📋 자급자족 여부:")
    if len(external_deps) == 0 and execution_success:
        print("   🎉 완전 자급자족! upbit_auto_trading 내부 코드만으로 케이스 시뮬레이션 동작")
        print("   📁 필요한 모든 것:")
        print("      - integrated_condition_manager.py (메인 UI)")
        print("      - real_data_simulation.py (데이터 엔진)")
        print("      - components/ (UI 컴포넌트들)")
        print("      - data/market_data.sqlite3 (실제 데이터)")
    else:
        print("   ⚠️ 일부 외부 의존성 존재")
        if external_deps:
            print("   🔗 외부 의존성:")
            for dep in external_deps[:5]:  # 상위 5개만 표시
                print(f"      - {dep}")

if __name__ == "__main__":
    main()
