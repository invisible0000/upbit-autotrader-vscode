#!/usr/bin/env python
"""
도메인 서비스 모듈 구조 분석 및 pytest 문제 진단 스크립트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
# __file__은 tests/domain/services/diagnose_test_issues.py이므로 3번 parent로 프로젝트 루트 찾기
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def analyze_module_structure():
    """모듈 구조 분석"""
    print("🔍 모듈 구조 분석 시작...")
    print("=" * 60)
    
    # 1. 프로젝트 루트 확인
    print(f"📁 프로젝트 루트: {project_root}")
    print(f"📂 현재 작업 디렉토리: {os.getcwd()}")
    
    # 2. upbit_auto_trading 폴더 구조 확인
    upbit_trading_path = project_root / "upbit_auto_trading"
    if upbit_trading_path.exists():
        print(f"✅ upbit_auto_trading 폴더 존재: {upbit_trading_path}")
    else:
        print(f"❌ upbit_auto_trading 폴더 없음: {upbit_trading_path}")
        return False
    
    # 3. domain 폴더 구조 확인
    domain_path = upbit_trading_path / "domain"
    if domain_path.exists():
        print(f"✅ domain 폴더 존재: {domain_path}")
        
        # domain 하위 폴더들 확인
        for subfolder in ["entities", "services", "value_objects"]:
            subfolder_path = domain_path / subfolder
            if subfolder_path.exists():
                print(f"  ✅ {subfolder} 폴더 존재")
                
                # 각 폴더의 파일들 나열
                files = list(subfolder_path.glob("*.py"))
                print(f"    📄 {subfolder} 파일들: {[f.name for f in files]}")
            else:
                print(f"  ❌ {subfolder} 폴더 없음")
    else:
        print(f"❌ domain 폴더 없음: {domain_path}")
        return False
    
    # 4. 특정 문제가 된 파일 확인
    entities_path = domain_path / "entities"
    target_files = ["trading_variable.py", "trigger.py", "__init__.py"]
    
    print("\n🎯 문제 파일들 확인:")
    for filename in target_files:
        file_path = entities_path / filename
        if file_path.exists():
            print(f"  ✅ {filename} 존재")
        else:
            print(f"  ❌ {filename} 없음")
    
    return True


def analyze_import_errors():
    """import 오류 분석"""
    print("\n🔍 Import 오류 분석...")
    print("=" * 60)
    
    try:
        # 1. 기본 upbit_auto_trading 모듈 import 테스트
        print("1️⃣ upbit_auto_trading 모듈 import 테스트")
        import upbit_auto_trading
        print(f"  ✅ upbit_auto_trading 모듈 로드 성공: {upbit_auto_trading.__file__}")
        
        # 2. domain 모듈 import 테스트
        print("2️⃣ domain 모듈 import 테스트")
        from upbit_auto_trading import domain
        print(f"  ✅ domain 모듈 로드 성공")
        
        # 3. entities 모듈 import 테스트
        print("3️⃣ entities 모듈 import 테스트")
        try:
            from upbit_auto_trading.domain import entities
            print(f"  ✅ entities 모듈 로드 성공")
            
            # entities 하위 모듈들 확인
            entities_dir = Path(entities.__file__).parent
            py_files = list(entities_dir.glob("*.py"))
            print(f"  📄 entities 모듈 파일들: {[f.stem for f in py_files if f.stem != '__init__']}")
            
        except ImportError as e:
            print(f"  ❌ entities 모듈 로드 실패: {e}")
        
        # 4. 구체적인 trading_variable 모듈 테스트
        print("4️⃣ trading_variable 모듈 import 테스트")
        try:
            from upbit_auto_trading.domain.entities.trading_variable import TradingVariable
            print(f"  ✅ TradingVariable 클래스 import 성공")
        except ImportError as e:
            print(f"  ❌ TradingVariable import 실패: {e}")
            
            # 대안 경로 확인
            try:
                from upbit_auto_trading.domain.entities.trigger import TradingVariable
                print(f"  ✅ TradingVariable을 trigger 모듈에서 발견")
            except ImportError as e2:
                print(f"  ❌ trigger 모듈에서도 TradingVariable 없음: {e2}")
        
        # 5. services 모듈 import 테스트
        print("5️⃣ services 모듈 import 테스트")
        try:
            from upbit_auto_trading.domain import services
            print(f"  ✅ services 모듈 로드 성공")
        except ImportError as e:
            print(f"  ❌ services 모듈 로드 실패: {e}")
            
    except ImportError as e:
        print(f"❌ 기본 모듈 로드 실패: {e}")
        return False
    
    return True


def analyze_pytest_issues():
    """pytest 문제 분석"""
    print("\n🔍 pytest 문제 분석...")
    print("=" * 60)
    
    # 1. Python 실행 환경 확인
    print(f"🐍 Python 실행 파일: {sys.executable}")
    print(f"🐍 Python 버전: {sys.version}")
    print(f"📦 Python 경로: {sys.path[:3]}...")  # 처음 3개만 출력
    
    # 2. pytest 설치 상태 확인
    print("\n2️⃣ pytest 설치 상태 확인")
    try:
        import pytest
        print(f"  ✅ pytest 모듈 발견: {pytest.__version__}")
        print(f"  📍 pytest 위치: {pytest.__file__}")
    except ImportError:
        print("  ❌ pytest 모듈 없음")
        
        # 다른 가능한 Python 환경에서 pytest 확인
        print("  🔍 다른 Python 환경 확인...")
        
        import subprocess
        import shutil
        
        # pip list로 설치된 패키지 확인
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                                  capture_output=True, text=True, timeout=10)
            if "pytest" in result.stdout:
                print("  ⚠️ pip list에는 pytest가 있지만 import 안됨")
                print(f"  📋 pip list 결과 (pytest 관련):")
                for line in result.stdout.split('\n'):
                    if 'pytest' in line.lower():
                        print(f"    {line}")
            else:
                print("  ❌ pip list에도 pytest 없음")
        except Exception as e:
            print(f"  ❌ pip list 실행 실패: {e}")
    
    # 3. 가상환경 확인
    print("\n3️⃣ 가상환경 확인")
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        print(f"  ✅ 가상환경 활성화됨: {venv_path}")
    else:
        print("  ⚠️ 가상환경 비활성화 상태")
    
    # 4. PYTHONPATH 확인
    print("\n4️⃣ PYTHONPATH 확인")
    pythonpath = os.environ.get('PYTHONPATH')
    if pythonpath:
        print(f"  📍 PYTHONPATH: {pythonpath}")
    else:
        print("  ⚠️ PYTHONPATH 설정 없음")
    
    return True


def fix_import_issues():
    """import 문제 해결 시도"""
    print("\n🔧 Import 문제 해결 시도...")
    print("=" * 60)
    
    # 1. TradingVariable 실제 위치 찾기
    print("1️⃣ TradingVariable 실제 위치 찾기")
    
    domain_entities_path = project_root / "upbit_auto_trading" / "domain" / "entities"
    if domain_entities_path.exists():
        py_files = list(domain_entities_path.glob("*.py"))
        
        for py_file in py_files:
            if py_file.name == "__init__.py":
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "class TradingVariable" in content:
                        print(f"  ✅ TradingVariable 발견: {py_file.name}")
                        
                        # trigger.py에 있다면 strategy_compatibility_service.py 수정 필요
                        if py_file.name == "trigger.py":
                            print(f"  🔧 TradingVariable이 trigger.py에 있음 - import 경로 수정 필요")
                            return fix_strategy_compatibility_import()
                            
            except Exception as e:
                print(f"  ❌ {py_file.name} 읽기 실패: {e}")
    
    return False


def fix_strategy_compatibility_import():
    """strategy_compatibility_service.py의 import 경로 수정"""
    print("2️⃣ strategy_compatibility_service.py import 경로 수정")
    
    service_file = project_root / "upbit_auto_trading" / "domain" / "services" / "strategy_compatibility_service.py"
    
    if not service_file.exists():
        print(f"  ❌ 파일 없음: {service_file}")
        return False
    
    try:
        # 파일 읽기
        with open(service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # import 경로 수정
        old_import = "from upbit_auto_trading.domain.entities.trading_variable import TradingVariable"
        new_import = "from upbit_auto_trading.domain.entities.trigger import TradingVariable"
        
        if old_import in content:
            content = content.replace(old_import, new_import)
            
            # 파일 쓰기
            with open(service_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"  ✅ import 경로 수정 완료")
            return True
        else:
            print(f"  ⚠️ 수정할 import 문 찾지 못함")
            return False
            
    except Exception as e:
        print(f"  ❌ 파일 수정 실패: {e}")
        return False


def test_basic_functionality():
    """기본 기능 테스트"""
    print("\n🧪 기본 기능 테스트...")
    print("=" * 60)
    
    try:
        # 1. NormalizationService 테스트
        print("1️⃣ NormalizationService 테스트")
        from upbit_auto_trading.domain.services.normalization_service import NormalizationService
        
        service = NormalizationService()
        result = service.normalize_for_comparison(
            75.0, "percentage_comparable",
            80.0, "percentage_comparable"
        )
        
        print(f"  ✅ 정규화 결과: {result.normalized_value1}, {result.normalized_value2}")
        
        # 2. StrategyCompatibilityService 테스트
        print("2️⃣ StrategyCompatibilityService 테스트")
        from upbit_auto_trading.domain.services.strategy_compatibility_service import StrategyCompatibilityService
        from upbit_auto_trading.domain.entities.trigger import TradingVariable
        
        compat_service = StrategyCompatibilityService()
        
        var1 = TradingVariable(
            variable_id="Close",
            display_name="종가",
            purpose_category="price",
            chart_category="overlay",
            comparison_group="price_comparable"
        )
        
        var2 = TradingVariable(
            variable_id="RSI_14",
            display_name="RSI",
            purpose_category="momentum",
            chart_category="subplot",
            comparison_group="percentage_comparable"
        )
        
        result = compat_service.check_variable_compatibility(var1, var2)
        print(f"  ✅ 호환성 결과: {result.level.value}, 호환={result.is_compatible}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 기능 테스트 실패: {e}")
        return False


def recommend_pytest_solution():
    """pytest 해결책 제안"""
    print("\n💡 pytest 해결책 제안...")
    print("=" * 60)
    
    print("📋 권장 해결책:")
    print("1️⃣ 가상환경 생성 및 활성화:")
    print("   python -m venv venv")
    print("   venv\\Scripts\\activate  # Windows")
    print()
    print("2️⃣ pytest 재설치:")
    print("   pip install pytest pytest-cov pytest-mock")
    print()
    print("3️⃣ 프로젝트 의존성 설치:")
    print("   pip install -r requirements.txt")
    print()
    print("4️⃣ 개발 모드로 프로젝트 설치:")
    print("   pip install -e .")
    print()
    print("5️⃣ 대안: unittest 사용")
    print("   python -m unittest discover tests/domain/services/")


def main():
    """메인 실행"""
    print("🚀 도메인 서비스 문제 진단 및 해결")
    print("=" * 80)
    
    # 1. 모듈 구조 분석
    if not analyze_module_structure():
        print("❌ 모듈 구조에 문제가 있습니다.")
        return False
    
    # 2. Import 오류 분석
    analyze_import_errors()
    
    # 3. pytest 문제 분석
    analyze_pytest_issues()
    
    # 4. 문제 해결 시도
    if fix_import_issues():
        print("✅ Import 문제 해결 완료")
        
        # 5. 기본 기능 테스트
        if test_basic_functionality():
            print("🎉 모든 기본 기능이 정상 동작합니다!")
        else:
            print("⚠️ 일부 기능에 문제가 있습니다.")
    else:
        print("⚠️ Import 문제 해결 실패")
    
    # 6. 해결책 제안
    recommend_pytest_solution()
    
    return True


if __name__ == "__main__":
    main()
