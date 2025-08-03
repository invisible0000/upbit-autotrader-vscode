# 🛠️ 테스트 환경 설정 및 도구 가이드

> **대상**: 주니어 개발자 (개발 환경 설정)  
> **목적**: 효율적인 테스트 환경 구축과 도구 활용법  
> **전제**: Python 개발 환경 기본 지식

## 📋 목차
- [1. 개발 환경 설정](#1-개발-환경-설정)
- [2. pytest 완전 활용법](#2-pytest-완전-활용법)
- [3. VS Code 테스트 통합](#3-vs-code-테스트-통합)
- [4. CI/CD 파이프라인 구축](#4-cicd-파이프라인-구축)
- [5. 테스트 도구 생태계](#5-테스트-도구-생태계)

---

## 1. 개발 환경 설정

### 🐍 Python 테스트 환경 구축

#### requirements-test.txt 작성
```txt
# 기본 테스트 프레임워크
pytest>=7.0.0
pytest-cov>=4.0.0          # 커버리지 측정
pytest-html>=3.1.0         # HTML 리포트
pytest-xdist>=3.0.0        # 병렬 실행

# Mock과 픽스처
pytest-mock>=3.8.0         # Mock 기능 확장
factory-boy>=3.2.0         # 테스트 데이터 팩토리
freezegun>=1.2.0           # 시간 조작

# 성능 및 분석
pytest-benchmark>=4.0.0    # 성능 벤치마크
pytest-profiling>=1.7.0    # 프로파일링
pytest-memray>=1.0.0       # 메모리 사용량 분석

# 코드 품질
pytest-flake8>=1.1.0      # 코드 스타일 검사
pytest-mypy>=0.10.0       # 타입 체크
pytest-black>=0.3.0       # 코드 포매팅

# 개발 편의성
pytest-sugar>=0.9.0       # 예쁜 출력
pytest-clarity>=1.0.0     # 명확한 diff 표시
pytest-watch>=4.2.0       # 파일 변경 감지
```

#### 설치 및 설정
```powershell
# 테스트 의존성 설치
pip install -r requirements-test.txt

# 개발용 pytest 설정 확인
pytest --version
pytest --help
```

### ⚙️ pytest.ini 설정 파일
```ini
[tool:pytest]
# 테스트 파일 경로
testpaths = tests

# 테스트 파일 패턴
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

# 기본 옵션
addopts = 
    --verbose                    # 상세 출력
    --tb=short                   # 간단한 traceback
    --strict-markers             # 정의되지 않은 마커 금지
    --strict-config              # 잘못된 설정 금지
    --cov=upbit_auto_trading     # 커버리지 측정 대상
    --cov-report=term-missing    # 터미널에 누락 라인 표시
    --cov-report=html:htmlcov    # HTML 리포트 생성
    --cov-fail-under=80          # 80% 미만 시 실패
    --maxfail=3                  # 3번 실패 시 중단
    --durations=10               # 느린 테스트 10개 표시

# 마커 정의
markers =
    unit: 유닛 테스트
    integration: 통합 테스트
    slow: 느린 테스트 (5초 이상)
    api: 외부 API 테스트
    ui: UI 테스트
    performance: 성능 테스트

# 경고 필터
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
    ignore::UserWarning:matplotlib.*

# 최소 Python 버전
minversion = 6.0
```

### 📁 테스트 폴더 구조 설정
```powershell
# 테스트 디렉토리 생성
New-Item -ItemType Directory -Path "tests"
New-Item -ItemType Directory -Path "tests\unit"
New-Item -ItemType Directory -Path "tests\integration"
New-Item -ItemType Directory -Path "tests\e2e"
New-Item -ItemType Directory -Path "tests\fixtures"
New-Item -ItemType Directory -Path "tests\utils"

# __init__.py 파일 생성
New-Item -ItemType File -Path "tests\__init__.py"
New-Item -ItemType File -Path "tests\unit\__init__.py"
New-Item -ItemType File -Path "tests\integration\__init__.py"
New-Item -ItemType File -Path "tests\e2e\__init__.py"
```

### 🔧 conftest.py 글로벌 설정
```python
# tests/conftest.py

import pytest
import sys
import os
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock

# 프로젝트 루트를 Python 경로에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 글로벌 테스트 설정
pytest.register_assert_rewrite("tests.utils.assertions")

@pytest.fixture(scope="session")
def test_data_dir():
    """테스트 데이터 디렉토리"""
    return Path(__file__).parent / "fixtures"

@pytest.fixture(scope="session")
def temp_dir():
    """임시 디렉토리 (세션 종료 시 자동 삭제)"""
    temp_path = tempfile.mkdtemp(prefix="upbit_test_")
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def mock_upbit_api():
    """업비트 API Mock"""
    mock_api = Mock()
    mock_api.get_current_price.return_value = {
        'market': 'KRW-BTC',
        'trade_price': 50000000,
        'change': 'RISE',
        'change_rate': 0.02
    }
    mock_api.get_candle_data.return_value = [
        {
            'timestamp': '2023-01-01T00:00:00',
            'opening_price': 49000000,
            'high_price': 51000000,
            'low_price': 48000000,
            'trade_price': 50000000,
            'candle_acc_trade_volume': 100.5
        }
    ]
    return mock_api

@pytest.fixture
def sample_ohlcv_dataframe():
    """샘플 OHLCV DataFrame"""
    import pandas as pd
    import numpy as np
    
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    np.random.seed(42)  # 재현 가능한 데이터
    
    base_price = 50000
    prices = []
    for i in range(100):
        change = np.random.normal(0.001, 0.02)
        base_price *= (1 + change)
        prices.append(base_price)
    
    return pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p * 1.02 for p in prices],
        'low': [p * 0.98 for p in prices],
        'close': prices,
        'volume': np.random.randint(1000, 10000, 100)
    })

# 테스트 환경 변수 설정
def pytest_configure(config):
    """pytest 시작 시 실행"""
    os.environ['TESTING'] = 'true'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    os.environ['DATABASE_URL'] = ':memory:'  # 인메모리 DB 사용

def pytest_unconfigure(config):
    """pytest 종료 시 실행"""
    # 환경 변수 정리
    for key in ['TESTING', 'LOG_LEVEL', 'DATABASE_URL']:
        os.environ.pop(key, None)

# 커스텀 마커 자동 적용
def pytest_collection_modifyitems(config, items):
    """테스트 수집 후 마커 자동 적용"""
    for item in items:
        # 느린 테스트 자동 마킹
        if "slow" in item.keywords or "performance" in item.keywords:
            item.add_marker(pytest.mark.slow)
        
        # API 테스트 자동 마킹
        if "api" in item.name.lower() or "upbit" in item.name.lower():
            item.add_marker(pytest.mark.api)
        
        # UI 테스트 자동 마킹
        if "ui" in item.name.lower() or "widget" in item.name.lower():
            item.add_marker(pytest.mark.ui)
```

---

## 2. pytest 완전 활용법

### 🚀 기본 실행 명령어
```powershell
# 모든 테스트 실행
pytest

# 특정 파일 테스트
pytest tests/unit/test_strategy.py

# 특정 클래스 테스트
pytest tests/unit/test_strategy.py::TestStrategy

# 특정 함수 테스트
pytest tests/unit/test_strategy.py::TestStrategy::test_create_strategy

# 패턴으로 테스트 선택
pytest -k "test_rsi"                    # 이름에 "test_rsi" 포함
pytest -k "not slow"                    # "slow" 마커 제외
pytest -k "rsi and not performance"     # 복합 조건
```

### 🏷️ 마커 활용법
```powershell
# 마커별 테스트 실행
pytest -m unit                         # 유닛 테스트만
pytest -m "not slow"                   # 빠른 테스트만
pytest -m "unit and not api"           # 유닛 테스트 중 API 제외
pytest -m "integration or e2e"         # 통합 테스트 또는 E2E

# 마커 조합 활용
pytest -m "unit" --maxfail=1           # 유닛 테스트에서 첫 실패 시 중단
pytest -m "slow" --tb=long             # 느린 테스트 상세 출력
```

### 📊 커버리지 측정
```powershell
# 기본 커버리지
pytest --cov=upbit_auto_trading

# 누락된 라인 표시
pytest --cov=upbit_auto_trading --cov-report=term-missing

# HTML 리포트 생성
pytest --cov=upbit_auto_trading --cov-report=html

# 커버리지 임계치 설정
pytest --cov=upbit_auto_trading --cov-fail-under=80

# 브랜치 커버리지 포함
pytest --cov=upbit_auto_trading --cov-branch --cov-report=html
```

### ⚡ 성능 최적화
```powershell
# 병렬 실행 (CPU 코어 수만큼)
pytest -n auto

# 병렬 실행 (특정 개수)
pytest -n 4

# 느린 테스트 식별
pytest --durations=10                  # 상위 10개
pytest --durations=0                   # 모든 테스트 시간

# 실패한 테스트만 재실행
pytest --lf                           # last failed
pytest --ff                           # failed first
```

### 🔍 디버깅 모드
```powershell
# 상세 출력
pytest -v                             # verbose
pytest -vv                            # extra verbose
pytest -s                             # 출력 캡처 비활성화

# pdb 디버거 진입
pytest --pdb                          # 실패 시 pdb 진입
pytest --pdb-trace                    # 시작 시 pdb 진입

# 첫 번째 실패에서 중단
pytest -x                             # stop on first failure
pytest --maxfail=3                    # stop after 3 failures
```

---

## 3. VS Code 테스트 통합

### 🔧 VS Code 설정 (.vscode/settings.json)
```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests",
        "--tb=short",
        "--cov=upbit_auto_trading",
        "--cov-report=html"
    ],
    "python.testing.autoTestDiscoverOnSaveEnabled": true,
    "python.testing.cwd": "${workspaceFolder}",
    
    // 테스트 파일 자동 감지
    "python.testing.pytestPath": "pytest",
    
    // 테스트 결과 설정
    "python.testing.promptToConfigure": false,
    
    // 커버리지 표시
    "coverage-gutters.coverageFileNames": [
        "coverage.xml",
        "coverage.lcov",
        "htmlcov/index.html"
    ],
    
    // 테스트 파일 제외 (검색 시)
    "search.exclude": {
        "**/htmlcov/**": true,
        "**/.coverage": true,
        "**/.pytest_cache/**": true
    }
}
```

### 🔧 tasks.json 설정 (테스트 작업)
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "pytest: 모든 테스트",
            "type": "shell",
            "command": "pytest",
            "group": "test",
            "options": {
                "cwd": "${workspaceFolder}"
            },
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            },
            "problemMatcher": "$pytest"
        },
        {
            "label": "pytest: 빠른 테스트",
            "type": "shell",
            "command": "pytest",
            "args": ["-m", "not slow", "--tb=short"],
            "group": "test",
            "options": {
                "cwd": "${workspaceFolder}"
            }
        },
        {
            "label": "pytest: 커버리지 리포트",
            "type": "shell",
            "command": "pytest",
            "args": [
                "--cov=upbit_auto_trading",
                "--cov-report=html",
                "--cov-report=term"
            ],
            "group": "test",
            "options": {
                "cwd": "${workspaceFolder}"
            }
        },
        {
            "label": "pytest: 현재 파일",
            "type": "shell",
            "command": "pytest",
            "args": ["${file}", "-v"],
            "group": "test",
            "options": {
                "cwd": "${workspaceFolder}"
            }
        }
    ]
}
```

### 🎯 VS Code 단축키 설정 (keybindings.json)
```json
[
    {
        "key": "ctrl+shift+t",
        "command": "python.runAllTests",
        "when": "editorTextFocus"
    },
    {
        "key": "ctrl+shift+r",
        "command": "python.runCurrentTestFile",
        "when": "editorTextFocus"
    },
    {
        "key": "ctrl+shift+d",
        "command": "python.debugCurrentTestFile",
        "when": "editorTextFocus"
    },
    {
        "key": "f5",
        "command": "python.debugTests",
        "when": "editorTextFocus && resourceExtname == '.py'"
    }
]
```

### 📊 Test Explorer 활용
```json
// VS Code Test Explorer 설정
{
    "testExplorer.useNativeTesting": true,
    "python.testing.pytestEnabled": true,
    
    // 테스트 자동 발견
    "python.testing.autoTestDiscoverOnSaveEnabled": true,
    
    // 테스트 결과 유지
    "python.testing.debugPort": 3000
}
```

---

## 4. CI/CD 파이프라인 구축

### 🚀 GitHub Actions 워크플로
```yaml
# .github/workflows/test.yml
name: 테스트 및 품질 검사

on:
  push:
    branches: [ master, develop ]
  pull_request:
    branches: [ master ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]
    
    steps:
    - name: 코드 체크아웃
      uses: actions/checkout@v4
    
    - name: Python 설정
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: 의존성 캐시
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: 의존성 설치
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: 코드 스타일 검사
      run: |
        black --check .
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: 타입 체크
      run: mypy upbit_auto_trading
    
    - name: 빠른 테스트 실행
      run: |
        pytest tests/unit -m "not slow" --tb=short
    
    - name: 전체 테스트 실행 (커버리지 포함)
      run: |
        pytest --cov=upbit_auto_trading --cov-report=xml --cov-report=term
    
    - name: 커버리지 업로드
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
    
    - name: 테스트 리포트 생성
      if: always()
      run: |
        pytest --html=reports/pytest_report.html --self-contained-html || true
    
    - name: 테스트 리포트 업로드
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-reports-${{ matrix.python-version }}
        path: reports/

  integration-test:
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Python 설정
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: 의존성 설치
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: 통합 테스트 실행
      run: |
        pytest tests/integration -v --tb=short
      env:
        TEST_DATABASE_URL: sqlite:///test_integration.db
    
    - name: E2E 테스트 실행
      run: |
        pytest tests/e2e -v --tb=short
      env:
        TEST_ENV: ci

  performance-test:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/master'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Python 설정
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: 의존성 설치
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: 성능 테스트 실행
      run: |
        pytest tests/performance -v --benchmark-only --benchmark-json=benchmark.json
    
    - name: 성능 결과 저장
      uses: actions/upload-artifact@v3
      with:
        name: performance-results
        path: benchmark.json
```

### 🔄 Pre-commit Hook 설정
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings, flake8-import-order]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]

  - repo: local
    hooks:
      - id: pytest-quick
        name: pytest-quick
        entry: pytest
        language: system
        args: ["-m", "not slow", "--tb=short"]
        pass_filenames: false
        always_run: false
        stages: [commit]
```

```powershell
# pre-commit 설치 및 설정
pip install pre-commit
pre-commit install

# 모든 파일에 대해 실행
pre-commit run --all-files
```

---

## 5. 테스트 도구 생태계

### 📊 커버리지 도구들
```powershell
# coverage.py (기본)
pip install coverage
coverage run -m pytest
coverage report
coverage html

# pytest-cov (pytest 통합)
pip install pytest-cov
pytest --cov=upbit_auto_trading --cov-report=html

# diff-cover (변경사항만 커버리지)
pip install diff-cover
diff-cover coverage.xml --compare-branch=origin/master
```

### 🎭 Mock 도구들
```python
# unittest.mock (기본)
from unittest.mock import Mock, patch, MagicMock

# pytest-mock (pytest 통합)
def test_function(mocker):
    mock_api = mocker.patch('module.api_call')
    mock_api.return_value = 'test'

# responses (HTTP 모킹)
import responses

@responses.activate
def test_api_call():
    responses.add(responses.GET, 'http://api.example.com', 
                 json={'status': 'ok'}, status=200)

# factory-boy (테스트 데이터 생성)
import factory

class StrategyFactory(factory.Factory):
    class Meta:
        model = Strategy
    
    name = factory.Sequence(lambda n: f"전략 {n}")
    entry_rules = factory.LazyFunction(lambda: [])
```

### ⚡ 성능 테스트 도구
```python
# pytest-benchmark
def test_rsi_performance(benchmark):
    data = list(range(1000))
    result = benchmark(calculate_rsi, data, 14)
    assert result is not None

# pytest-memray (메모리 프로파일링)
@pytest.mark.memray
def test_memory_usage():
    # 메모리 사용량이 측정됨
    large_data = [i for i in range(100000)]
    process_data(large_data)

# line_profiler (라인별 프로파일링)
@profile
def slow_function():
    # 각 라인의 실행 시간 측정
    pass
```

### 🔍 코드 품질 도구
```powershell
# flake8 (스타일 검사)
pip install flake8
flake8 upbit_auto_trading

# black (코드 포매팅)
pip install black
black upbit_auto_trading

# mypy (타입 체크)
pip install mypy
mypy upbit_auto_trading

# bandit (보안 검사)
pip install bandit
bandit -r upbit_auto_trading

# pylint (종합 분석)
pip install pylint
pylint upbit_auto_trading
```

### 📈 리포팅 도구
```python
# pytest-html (HTML 리포트)
pytest --html=report.html --self-contained-html

# allure (상세 리포트)
pip install allure-pytest
pytest --alluredir=allure-results
allure serve allure-results

# pytest-json-report (JSON 리포트)
pytest --json-report --json-report-file=report.json
```

---

## 🎯 실무 워크플로 예시

### 📝 일일 개발 워크플로
```powershell
# 1. 개발 시작 전 빠른 테스트
pytest -m "not slow" --tb=short

# 2. 개발 중 (특정 파일)
pytest tests/unit/test_strategy.py -v

# 3. 커밋 전 체크
pre-commit run --all-files
pytest --cov=upbit_auto_trading --cov-fail-under=80

# 4. 푸시 전 최종 검증
pytest tests/ -x --tb=short
```

### 🔄 주간 품질 검증
```powershell
# 1. 전체 테스트 + 상세 커버리지
pytest --cov=upbit_auto_trading --cov-report=html --cov-branch

# 2. 성능 벤치마크
pytest tests/performance --benchmark-only

# 3. 메모리 사용량 체크
pytest --memray

# 4. 코드 품질 종합 분석
flake8 upbit_auto_trading
mypy upbit_auto_trading
bandit -r upbit_auto_trading
```

### 🚀 배포 전 검증
```powershell
# 1. 모든 환경에서 테스트
tox

# 2. 통합 테스트
pytest tests/integration -v

# 3. E2E 테스트
pytest tests/e2e -v

# 4. 성능 회귀 테스트
pytest tests/performance --benchmark-compare=baseline.json
```

---

## 🛠️ 트러블슈팅 가이드

### 🚨 자주 발생하는 문제들

#### 1. Import 오류
```powershell
# 문제: ModuleNotFoundError
# 해결: PYTHONPATH 설정
$env:PYTHONPATH = "."
pytest

# 또는 conftest.py에서 경로 추가
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
```

#### 2. 병렬 실행 충돌
```python
# 문제: 데이터베이스 충돌
# 해결: 각 워커별 독립 DB
@pytest.fixture
def worker_db(worker_id):
    if worker_id == "master":
        return ":memory:"
    return f":memory:_{worker_id}"
```

#### 3. 플랫폼별 차이
```python
# 문제: Windows/Linux 경로 차이
# 해결: pathlib 사용
from pathlib import Path

def test_file_path():
    file_path = Path("data") / "test.db"
    assert file_path.exists()
```

### 💡 성능 최적화 팁
```python
# 1. 픽스처 스코프 최적화
@pytest.fixture(scope="session")  # 세션당 1회
def expensive_setup():
    pass

@pytest.fixture(scope="function")  # 테스트당 1회
def simple_setup():
    pass

# 2. parametrize 활용
@pytest.mark.parametrize("input,expected", [
    (1, 2), (2, 3), (3, 4)
])
def test_increment(input, expected):
    assert increment(input) == expected

# 3. 조건부 테스트 스킵
@pytest.mark.skipif(sys.platform == "win32", 
                   reason="Unix 전용 테스트")
def test_unix_feature():
    pass
```

---

**💡 다음 단계**: 이 가이드를 참고하여 프로젝트에 맞는 테스트 환경을 구축하고, 실제 테스트를 작성해보세요! 🚀
