# 🔧 VS Code 터미널 pytest 환경 문제해결 가이드

> **목적**: 새로운 코파일럿이 VS Code 터미널에서 가상환경/pytest 문제를 신속히 해결  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-04

## 🎯 개요

VS Code 터미널에서 새로운 코파일럿 세션 시작 시 자주 발생하는 **가상환경 미활성화**와 **pytest 실행 오류** 문제의 완전한 해결 방안을 제시합니다.

## 🚨 주요 증상들

### 1. 가상환경 문제
```powershell
# ❌ 증상: 프롬프트에 (venv) 표시 없음
PS d:\projects\upbit-autotrader-vscode>

# ❌ 증상: Python 경로가 전역 Python
PS> python -c "import sys; print(sys.executable)"
C:\Users\User\AppData\Local\Programs\Python\Python313\python.exe
```

### 2. pytest 실행 문제
```powershell
# ❌ 증상: pytest 명령어 인식 안됨
pytest : The term 'pytest' is not recognized...

# ❌ 증상: 모듈 import 실패
ModuleNotFoundError: No module named 'upbit_auto_trading'
```

### 3. VS Code 환경 문제
```powershell
# ❌ 증상: Python 인터프리터 경로 불일치
Current interpreter: C:\Users\User\AppData\Local\Programs\Python\Python313\python.exe
Expected: d:\projects\upbit-autotrader-vscode\venv\Scripts\python.exe
```

## 🔧 완전한 해결 절차

### Step 1: 가상환경 상태 진단
```powershell
# 1️⃣ 현재 Python 경로 확인
python -c "import sys; print(sys.executable)"

# 2️⃣ 가상환경 디렉토리 존재 확인
Test-Path "venv\Scripts\python.exe"

# 3️⃣ 프롬프트에서 (venv) 표시 확인
echo $env:VIRTUAL_ENV
```

**✅ 정상 상태 예시:**
```powershell
(venv) PS d:\projects\upbit-autotrader-vscode> python -c "import sys; print(sys.executable)"
d:\projects\upbit-autotrader-vscode\venv\Scripts\python.exe

(venv) PS d:\projects\upbit-autotrader-vscode> echo $env:VIRTUAL_ENV
d:\projects\upbit-autotrader-vscode\venv
```

### Step 2: 가상환경 강제 활성화
```powershell
# 🚨 필수: 항상 이 순서로 실행

# 1️⃣ 기존 가상환경 비활성화 (있다면)
if ($env:VIRTUAL_ENV) { deactivate }

# 2️⃣ 가상환경 활성화
venv\Scripts\Activate.ps1

# 3️⃣ 활성화 확인
python -c "import sys; print('Python:', sys.executable)"
echo "Virtual Env: $env:VIRTUAL_ENV"
```

### Step 3: VS Code Python 인터프리터 설정
```powershell
# 🎯 VS Code Command Palette (Ctrl+Shift+P)에서 실행:
# "Python: Select Interpreter" 
# → "d:\projects\upbit-autotrader-vscode\venv\Scripts\python.exe" 선택

# 또는 터미널에서 확인:
code --list-extensions | Select-String python
```

### Step 4: 프로젝트 개발 모드 설치
```powershell
# 🚨 가상환경 활성화 후 필수 실행

# 1️⃣ 프로젝트를 개발 모드로 설치
pip install -e .

# 2️⃣ pytest 설치 확인
pip list | Select-String pytest

# 3️⃣ upbit_auto_trading 모듈 확인
python -c "import upbit_auto_trading; print('✅ 모듈 로드 성공')"
```

### Step 5: pytest 환경 검증
```powershell
# 🧪 전체 환경 검증

# 1️⃣ pytest 버전 확인
pytest --version

# 2️⃣ 테스트 발견 확인
pytest --collect-only tests/ | Select-String "test session starts"

# 3️⃣ 간단한 테스트 실행
pytest tests/domain/services/test_normalization_service.py::TestNormalizationService::test_init_default_strategy -v
```

## 🚀 자동화 스크립트

### 원클릭 환경 설정 스크립트
```powershell
# 📁 파일명: setup_dev_env.ps1
# 💾 위치: 프로젝트 루트

param(
    [switch]$Force = $false
)

Write-Host "🔧 개발 환경 설정 시작..." -ForegroundColor Green

# 1. 기존 가상환경 비활성화
if ($env:VIRTUAL_ENV) {
    Write-Host "⚠️ 기존 가상환경 비활성화: $env:VIRTUAL_ENV" -ForegroundColor Yellow
    deactivate
}

# 2. 가상환경 활성화
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "📦 가상환경 활성화..." -ForegroundColor Blue
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "❌ 가상환경이 없습니다. 먼저 'python -m venv venv' 실행하세요." -ForegroundColor Red
    exit 1
}

# 3. 개발 모드 설치
Write-Host "🔨 프로젝트 개발 모드 설치..." -ForegroundColor Blue
pip install -e .

# 4. 환경 검증
Write-Host "✅ 환경 검증..." -ForegroundColor Green
python -c "import upbit_auto_trading; print('✅ 모듈 로드 성공')"
pytest --version
Write-Host "🎉 환경 설정 완료!" -ForegroundColor Green
```

### 빠른 검증 스크립트
```powershell
# 📁 파일명: check_env.ps1
# 🎯 현재 환경 상태 빠른 체크

Write-Host "🔍 환경 상태 검사..." -ForegroundColor Cyan

# Python 경로
$pythonPath = python -c "import sys; print(sys.executable)" 2>$null
Write-Host "🐍 Python: $pythonPath"

# 가상환경 상태
if ($env:VIRTUAL_ENV) {
    Write-Host "📦 Virtual Env: ✅ $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "📦 Virtual Env: ❌ 비활성화" -ForegroundColor Red
}

# pytest 설치 상태
try {
    $pytestVersion = pytest --version 2>$null
    Write-Host "🧪 pytest: ✅ $pytestVersion" -ForegroundColor Green
} catch {
    Write-Host "🧪 pytest: ❌ 미설치" -ForegroundColor Red
}

# upbit_auto_trading 모듈
try {
    python -c "import upbit_auto_trading" 2>$null
    Write-Host "📱 upbit_auto_trading: ✅ 로드 가능" -ForegroundColor Green
} catch {
    Write-Host "📱 upbit_auto_trading: ❌ 로드 실패" -ForegroundColor Red
}
```

## 🔍 고급 문제해결

### 문제 1: 권한 오류
```powershell
# ❌ 증상: execution policy 오류
venv\Scripts\Activate.ps1 : cannot be loaded because running scripts is disabled

# ✅ 해결: PowerShell 실행 정책 변경
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 또는 일시적 우회:
PowerShell -ExecutionPolicy Bypass -File "venv\Scripts\Activate.ps1"
```

### 문제 2: VS Code 터미널 캐시 문제
```powershell
# ❌ 증상: VS Code가 이전 Python 인터프리터 기억

# ✅ 해결 1: VS Code 재시작
# Ctrl+Shift+P → "Developer: Reload Window"

# ✅ 해결 2: 설정 강제 갱신
# Ctrl+Shift+P → "Python: Clear Cache and Reload Window"

# ✅ 해결 3: settings.json 직접 수정
# .vscode/settings.json에서 python.defaultInterpreterPath 확인
```

### 문제 3: 모듈 패스 문제
```powershell
# ❌ 증상: sys.path에 프로젝트 경로 없음

# ✅ 해결: PYTHONPATH 환경변수 설정
$env:PYTHONPATH = "d:\projects\upbit-autotrader-vscode"

# 또는 개발 모드 재설치:
pip uninstall upbit-auto-trading -y; pip install -e .
```

## 📋 빠른 체크리스트

### 새 코파일럿 시작 시 (2분 체크)
- [ ] **가상환경 확인**: 프롬프트에 `(venv)` 표시되는가?
- [ ] **Python 경로**: `venv\Scripts\python.exe` 경로인가?
- [ ] **pytest 설치**: `pytest --version` 명령 동작하는가?
- [ ] **모듈 로드**: `import upbit_auto_trading` 성공하는가?
- [ ] **VS Code 인터프리터**: 올바른 가상환경 선택되었는가?

### 문제 발생 시 (5분 해결)
- [ ] **가상환경 재활성화**: `venv\Scripts\Activate.ps1` 실행
- [ ] **개발 모드 재설치**: `pip install -e .` 실행  
- [ ] **VS Code 재시작**: `Developer: Reload Window` 실행
- [ ] **경로 확인**: Python/pytest/모듈 경로 일치 검증
- [ ] **권한 확인**: PowerShell 실행 정책 문제없는가?

## 🎯 성공 상태 확인

### 완벽한 환경 예시
```powershell
(venv) PS d:\projects\upbit-autotrader-vscode> python -c "import sys; print(sys.executable)"
d:\projects\upbit-autotrader-vscode\venv\Scripts\python.exe

(venv) PS d:\projects\upbit-autotrader-vscode> pytest --version
pytest 8.4.1

(venv) PS d:\projects\upbit-autotrader-vscode> python -c "import upbit_auto_trading; print('✅ Success')"
✅ Success

(venv) PS d:\projects\upbit-autotrader-vscode> pytest tests/domain/services/test_normalization_service.py -v
========================= test session starts =========================
tests/domain/services/test_normalization_service.py::TestNormalizationService::test_init_default_strategy PASSED
========================= 1 passed in 0.05s =========================
```

## 💡 예방 가이드

### VS Code 설정 최적화
```json
// 📁 .vscode/settings.json 권장 설정
{
    "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "terminal.integrated.defaultProfile.windows": "PowerShell"
}
```

### 자동 활성화 스크립트
```powershell
# 📁 .vscode/tasks.json에 추가할 태스크
{
    "label": "Activate Development Environment",
    "type": "shell",
    "command": "venv\\Scripts\\Activate.ps1; pip install -e .",
    "group": "build",
    "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "new"
    }
}
```

## 📚 관련 문서

- [개발 체크리스트](DEV_CHECKLIST.md): 환경 설정 검증 기준
- [프로젝트 명세서](PROJECT_SPECIFICATIONS.md): 개발 환경 요구사항
- [LLM 문서화 가이드](LLM_DOCUMENTATION_GUIDELINES.md): 이 문서의 작성 기준

---

**💡 핵심**: "5분 투자로 2시간 절약! 환경 설정은 한 번 제대로, 계속 편리하게!"

**🚀 원클릭 해결**: `venv\Scripts\Activate.ps1; pip install -e .; pytest --version`
