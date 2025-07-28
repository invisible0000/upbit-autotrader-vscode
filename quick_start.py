#!/usr/bin/env python3
"""
Upbit Autotrader - 빠른 시작 스크립트
GitHub 클론 후 바로 실행 가능한 진입점
"""

import sys
import os
from pathlib import Path

def setup_python_path():
    """프로젝트 루트를 Python 경로에 추가"""
    project_root = Path(__file__).parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # 환경 변수 설정
    os.environ['PYTHONPATH'] = str(project_root)
    return project_root

def check_dependencies():
    """필수 의존성 패키지 확인"""
    required_packages = [
        'PyQt6', 'pandas', 'requests', 'python-dotenv', 
        'cryptography', 'pyyaml', 'pyjwt'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.lower().replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 필수 패키지가 설치되지 않았습니다:")
        print(f"   {', '.join(missing_packages)}")
        print("\n✅ 다음 명령어로 설치하세요:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ 모든 필수 패키지가 설치되어 있습니다.")
    return True

def initialize_app():
    """애플리케이션 초기화"""
    project_root = setup_python_path()
    
    print("🚀 Upbit Autotrader 시작")
    print("=" * 50)
    print(f"📁 프로젝트 루트: {project_root}")
    
    # 의존성 확인
    if not check_dependencies():
        return False
    
    # 설정 파일 확인
    config_dir = project_root / "config"
    if not config_dir.exists():
        print("⚠️ config 디렉토리가 없습니다. 생성합니다...")
        config_dir.mkdir(exist_ok=True)
    
    # 데이터 디렉토리 확인
    data_dir = project_root / "data"
    if not data_dir.exists():
        print("⚠️ data 디렉토리가 없습니다. 생성합니다...")
        data_dir.mkdir(exist_ok=True)
    
    return True

def main():
    """메인 진입점"""
    if not initialize_app():
        sys.exit(1)
    
    print("\n🎯 실행 옵션:")
    print("1. Desktop UI 실행: python run_desktop_ui.py")
    print("2. 콘솔 모드 실행: python run.py")
    print("3. 테스트 실행: python -m pytest tests/")
    print("4. 데이터베이스 초기화: python initialize_databases.py")
    
    # 기본적으로 Desktop UI 실행
    try:
        print("\n🖥️ Desktop UI를 실행합니다...")
        from run_desktop_ui import main as run_desktop
        run_desktop()
    except KeyboardInterrupt:
        print("\n👋 애플리케이션을 종료합니다.")
    except Exception as e:
        print(f"\n❌ 실행 중 오류 발생: {e}")
        print("\n💡 문제 해결:")
        print("1. requirements.txt 재설치: pip install -r requirements.txt")
        print("2. Python 버전 확인: python --version (>=3.8 필요)")
        print("3. 이슈 리포트: https://github.com/invisible0000/upbit-autotrader-vscode/issues")

if __name__ == "__main__":
    main()
