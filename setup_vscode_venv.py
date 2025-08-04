"""
VS Code 터미널 자동 가상환경 활성화 설정 가이드

이 스크립트는 VS Code에서 터미널이 열릴 때 자동으로 가상환경이 활성화되도록 
설정하는 방법들을 제공합니다.
"""

import json
import os
from pathlib import Path

def setup_vscode_python_environment():
    """VS Code Python 환경 설정"""
    print("🔧 VS Code Python 환경 설정 방법")
    print("=" * 60)
    
    # 1. Python 인터프리터 설정
    print("1️⃣ Python 인터프리터 설정")
    print("   - Ctrl+Shift+P → 'Python: Select Interpreter'")
    print("   - 가상환경의 python.exe 선택 (예: venv/Scripts/python.exe)")
    print("   - 이렇게 하면 새 터미널이 자동으로 가상환경 활성화됨")
    
    # 2. .vscode/settings.json 설정
    print("\n2️⃣ .vscode/settings.json 설정")
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)
    
    settings_file = vscode_dir / "settings.json"
    
    # 현재 설정 읽기 (있다면)
    current_settings = {}
    if settings_file.exists():
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                current_settings = json.load(f)
        except:
            current_settings = {}
    
    # Python 관련 설정 추가
    python_settings = {
        "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
        "python.terminal.activateEnvironment": True,
        "python.terminal.activateEnvInCurrentTerminal": True,
        "terminal.integrated.env.windows": {
            "PYTHONPATH": "${workspaceFolder}"
        },
        "terminal.integrated.shellArgs.windows": [
            "-Command",
            "if (Test-Path '.\\venv\\Scripts\\Activate.ps1') { .\\venv\\Scripts\\Activate.ps1 }"
        ]
    }
    
    # 기존 설정과 병합
    current_settings.update(python_settings)
    
    # 설정 파일 저장
    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(current_settings, f, indent=4, ensure_ascii=False)
    
    print(f"   ✅ {settings_file} 설정 완료")
    
    # 3. 가상환경 생성/확인
    print("\n3️⃣ 가상환경 확인")
    venv_path = Path("venv")
    if venv_path.exists():
        print(f"   ✅ 가상환경 존재: {venv_path.absolute()}")
        
        # Python 실행파일 확인
        python_exe = venv_path / "Scripts" / "python.exe"
        if python_exe.exists():
            print(f"   ✅ Python 실행파일: {python_exe.absolute()}")
        else:
            print(f"   ❌ Python 실행파일 없음: {python_exe.absolute()}")
    else:
        print(f"   ❌ 가상환경 없음: {venv_path.absolute()}")
        print("   💡 가상환경 생성: python -m venv venv")
    
    return current_settings

def create_activation_scripts():
    """터미널 자동 활성화 스크립트 생성"""
    print("\n🔧 터미널 자동 활성화 스크립트 생성")
    print("=" * 60)
    
    # PowerShell 프로파일 설정
    powershell_script = '''
# VS Code 터미널에서 자동 가상환경 활성화
if ($env:TERM_PROGRAM -eq "vscode" -and (Test-Path ".\\venv\\Scripts\\Activate.ps1")) {
    Write-Host "🐍 가상환경 자동 활성화 중..." -ForegroundColor Green
    .\\venv\\Scripts\\Activate.ps1
    Write-Host "✅ 가상환경 활성화 완료: $(Split-Path $env:VIRTUAL_ENV -Leaf)" -ForegroundColor Green
}
'''
    
    # .vscode/terminal_setup.ps1 생성
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)
    
    terminal_script = vscode_dir / "terminal_setup.ps1"
    with open(terminal_script, 'w', encoding='utf-8') as f:
        f.write(powershell_script)
    
    print(f"   ✅ {terminal_script} 스크립트 생성")
    
    # .vscode/launch.json에 터미널 설정 추가
    launch_file = vscode_dir / "launch.json"
    launch_config = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Current File (with venv)",
                "type": "python",
                "request": "launch",
                "program": "${file}",
                "console": "integratedTerminal",
                "python": "${workspaceFolder}/venv/Scripts/python.exe",
                "cwd": "${workspaceFolder}",
                "env": {
                    "PYTHONPATH": "${workspaceFolder}"
                }
            }
        ]
    }
    
    with open(launch_file, 'w', encoding='utf-8') as f:
        json.dump(launch_config, f, indent=4)
    
    print(f"   ✅ {launch_file} 디버그 설정 생성")

def check_pytest_installation():
    """pytest 설치 상태 확인 및 해결책 제시"""
    print("\n🧪 pytest 설치 문제 해결")
    print("=" * 60)
    
    # 현재 Python 환경 확인
    import sys
    print(f"📍 현재 Python: {sys.executable}")
    print(f"📍 현재 Python 버전: {sys.version}")
    
    # 가상환경 확인
    venv_python = Path("venv/Scripts/python.exe")
    if venv_python.exists():
        print(f"📍 가상환경 Python: {venv_python.absolute()}")
        
        # 가상환경에서 pytest 설치 상태 확인
        print("\n🔍 가상환경에서 pytest 확인 중...")
        
        # subprocess로 가상환경의 pip list 실행
        import subprocess
        try:
            result = subprocess.run([
                str(venv_python), "-m", "pip", "list"
            ], capture_output=True, text=True, timeout=30)
            
            if "pytest" in result.stdout:
                print("   ✅ 가상환경에 pytest 설치됨")
            else:
                print("   ❌ 가상환경에 pytest 없음")
                print("   💡 해결책: venv\\Scripts\\python.exe -m pip install pytest pytest-cov")
                
        except Exception as e:
            print(f"   ❌ 가상환경 확인 실패: {e}")
    else:
        print("   ❌ 가상환경 없음")
        print("   💡 먼저 가상환경 생성: python -m venv venv")
    
    # pytest 설치 명령어 제시
    print("\n💡 pytest 설치 권장 명령어:")
    print("   1. 가상환경 활성화: .\\venv\\Scripts\\Activate.ps1")
    print("   2. pytest 설치: pip install pytest pytest-cov pytest-mock")
    print("   3. 설치 확인: python -m pytest --version")

def verify_copilot_terminal_integration():
    """Copilot 터미널 통합 확인"""
    print("\n🤖 GitHub Copilot 터미널 통합 확인")
    print("=" * 60)
    
    # VS Code 설정에서 터미널 관련 확인사항
    print("1️⃣ VS Code 설정 확인사항:")
    print("   - python.terminal.activateEnvironment: true")
    print("   - python.terminal.activateEnvInCurrentTerminal: true")
    print("   - terminal.integrated.defaultProfile.windows: PowerShell")
    
    print("\n2️⃣ Copilot이 여는 터미널에서 가상환경 활성화 확인:")
    print("   - 터미널 프롬프트에 (venv) 표시 여부")
    print("   - python --version 실행하여 가상환경 Python 사용 여부")
    print("   - pip list로 가상환경 패키지 목록 확인")
    
    print("\n3️⃣ 문제 해결:")
    print("   - 터미널 재시작: Ctrl+Shift+`")
    print("   - VS Code 재시작 후 Python 인터프리터 재선택")
    print("   - PowerShell 실행 정책 확인: Get-ExecutionPolicy")

def main():
    """메인 설정 실행"""
    print("🚀 VS Code Copilot 터미널 가상환경 자동 활성화 설정")
    print("=" * 80)
    
    try:
        # 1. VS Code Python 환경 설정
        settings = setup_vscode_python_environment()
        
        # 2. 터미널 활성화 스크립트 생성
        create_activation_scripts()
        
        # 3. pytest 설치 상태 확인
        check_pytest_installation()
        
        # 4. Copilot 터미널 통합 확인
        verify_copilot_terminal_integration()
        
        print("\n" + "=" * 80)
        print("✅ 설정 완료!")
        print("\n📋 다음 단계:")
        print("1. VS Code 재시작")
        print("2. Ctrl+Shift+P → 'Python: Select Interpreter' → venv/Scripts/python.exe 선택")
        print("3. 새 터미널 열기 (Ctrl+Shift+`) → (venv) 표시 확인")
        print("4. python -m pytest --version으로 pytest 설치 확인")
        
    except Exception as e:
        print(f"❌ 설정 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
