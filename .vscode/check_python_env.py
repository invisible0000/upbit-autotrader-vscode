#!/usr/bin/env python3
"""
VS Code Virtual Environment Checker and Fixer
GitHub Copilot 터미널에서 가상환경 문제를 진단하고 해결하는 스크립트
"""

import sys
import os
import subprocess
from pathlib import Path

def check_virtual_env():
    """현재 가상환경 상태 확인"""
    print("🔍 Python Virtual Environment Status Check")
    print("=" * 50)

    # 기본 정보
    print(f"Python Executable: {sys.executable}")
    print(f"Python Version: {sys.version}")
    print(f"Current Working Directory: {os.getcwd()}")

    # 가상환경 확인
    venv_var = os.environ.get('VIRTUAL_ENV')
    if venv_var:
        print(f"✅ VIRTUAL_ENV: {venv_var}")
    else:
        print("❌ VIRTUAL_ENV: Not set")

    # 가상환경 파일 존재 확인
    workspace = Path(__file__).parent.parent
    venv_path = workspace / ".venv"

    print(f"\n📁 Workspace: {workspace}")
    print(f"🐍 Expected .venv path: {venv_path}")

    if venv_path.exists():
        print("✅ .venv directory exists")

        # Windows
        activate_script = venv_path / "Scripts" / "Activate.ps1"
        python_exe = venv_path / "Scripts" / "python.exe"

        if activate_script.exists():
            print(f"✅ Activation script: {activate_script}")
        else:
            print(f"❌ Activation script not found: {activate_script}")

        if python_exe.exists():
            print(f"✅ Python executable: {python_exe}")
        else:
            print(f"❌ Python executable not found: {python_exe}")
    else:
        print("❌ .venv directory not found")

    return venv_var is not None, venv_path

def check_packages():
    """설치된 패키지 확인"""
    print("\n📦 Installed Packages Check")
    print("=" * 30)

    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list"],
                              capture_output=True, text=True)
        packages = result.stdout.split('\n')
        print(f"Total packages: {len(packages) - 3}")  # 헤더 제외

        # 주요 패키지 확인
        important_packages = ['aiohttp', 'pandas', 'numpy', 'pytest']
        for package in important_packages:
            found = any(package.lower() in line.lower() for line in packages)
            status = "✅" if found else "❌"
            print(f"{status} {package}")

    except Exception as e:
        print(f"❌ Failed to check packages: {e}")

def suggest_solutions():
    """해결방안 제시"""
    print("\n🔧 Suggested Solutions")
    print("=" * 25)

    print("1. VS Code에서 새 터미널 열기:")
    print("   - Ctrl+Shift+` (새 터미널)")
    print("   - 터미널 타입을 'PowerShell 7 (Auto venv)' 선택")

    print("\n2. 수동으로 가상환경 활성화:")
    print("   .venv\\Scripts\\Activate.ps1")

    print("\n3. Python 인터프리터 확인:")
    print("   - Ctrl+Shift+P → 'Python: Select Interpreter'")
    print("   - .venv\\Scripts\\python.exe 선택")

    print("\n4. 터미널에서 확인:")
    print("   Get-Command python | Select-Object -ExpandProperty Source")

    print("\n5. GitHub Copilot 터미널 문제 해결:")
    print("   - VS Code 재시작")
    print("   - 또는 터미널에서 수동 실행: .vscode\\activate_venv.bat")

def main():
    """메인 함수"""
    print("🎯 VS Code Virtual Environment Diagnostics")
    print("GitHub Copilot Terminal Environment Checker\n")

    is_venv_active, venv_path = check_virtual_env()
    check_packages()
    suggest_solutions()

    if not is_venv_active:
        print("\n⚠️  가상환경이 활성화되지 않았습니다!")
        print("위의 해결방안을 참고하여 가상환경을 활성화해주세요.")
    else:
        print("\n✅ 가상환경이 올바르게 설정되었습니다!")

if __name__ == "__main__":
    main()
