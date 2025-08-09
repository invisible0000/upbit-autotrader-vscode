# ⚡ 자주 사용하는 명령어 모음
*최종 업데이트: 2025년 8월 9일*

## 🔍 시스템 검증 (일일 필수)

### 🖥️ UI 실행 및 기본 검증
```powershell
# 최종 통합 검증 (필수)
python run_desktop_ui.py

# UI 실행 후 확인 사항:
# - 메인 윈도우 정상 로딩
# - 전략 관리 → 트리거 빌더 진입 가능
# - 설정 → 각 탭 정상 표시
```

### 📊 DB 상태 확인
```powershell
# 3-DB 상태 확인
python tools/super_db_table_viewer.py settings
python tools/super_db_table_viewer.py strategies
python tools/super_db_table_viewer.py market_data

# 특정 테이블 참조 분석
python tools/super_db_table_reference_code_analyzer.py --tables tv_trading_variables
```

### 📋 로깅 시스템 활성화
```powershell
# 기본 로깅 (콘솔 출력)
$env:UPBIT_CONSOLE_OUTPUT='true'

# 상세 로깅 (개발 시 사용)
$env:UPBIT_CONSOLE_OUTPUT='true'; $env:UPBIT_LOG_SCOPE='verbose'

# 특정 컴포넌트 집중 로깅
$env:UPBIT_CONSOLE_OUTPUT='true'; $env:UPBIT_COMPONENT_FOCUS='TriggerBuilder'
```

---

## 🧪 테스트 실행

### 🔬 단위 테스트
```powershell
# 전체 테스트 (CI/CD 수준)
pytest tests/ -v

# 계층별 테스트
pytest tests/domain/ -v                    # Domain Layer 검증
pytest tests/application/ -v               # Application Layer 검증
pytest tests/infrastructure/ -v            # Infrastructure Layer 검증

# 특정 테스트 파일
pytest tests/domain/services/test_strategy_compatibility_service.py -v
```

### 🎯 특정 기능 테스트
```powershell
# Infrastructure Repository 테스트
pytest tests/infrastructure/repositories/ -v

# Domain Services 테스트
pytest tests/domain/services/ -v

# Use Cases 테스트
pytest tests/application/use_cases/ -v
```

---

## 🔍 코드 분석 및 검증

### 🚨 계층 위반 검사 (필수)
```powershell
# Domain Layer 순수성 검증 (결과 없어야 정상)
grep -r "import sqlite3" upbit_auto_trading/domain/
grep -r "import requests" upbit_auto_trading/domain/
grep -r "from PyQt6" upbit_auto_trading/domain/

# Presenter 순수성 검증 (결과 없어야 정상)
grep -r "sqlite3" upbit_auto_trading/ui/
grep -r "sqlite3" upbit_auto_trading/presentation/
```

### 📈 구현 현황 분석
```powershell
# Use Case 구현 현황
find upbit_auto_trading/application/use_cases/ -name "*.py" | wc -l

# Domain Services 구현 현황
find upbit_auto_trading/domain/services/ -name "*.py" | wc -l

# Repository 구현 현황
find upbit_auto_trading/infrastructure/repositories/ -name "*.py" | wc -l
```

### 🔧 코드 품질 검사
```powershell
# Python 구문 오류 검사
python -m py_compile upbit_auto_trading/**/*.py

# Import 순서 검사 (선택사항)
isort --check-only upbit_auto_trading/

# 코드 스타일 검사 (선택사항)
flake8 upbit_auto_trading/ --max-line-length=120
```

---

## 🛠️ 개발 환경 설정

### 🐍 Python 환경 관리
```powershell
# Python 환경 설정 (최초 1회)
python setup_vscode_venv.py

# 패키지 설치/업데이트
pip install -r requirements.txt

# 개발 의존성 설치
pip install pytest pytest-cov flake8 isort
```

### 📦 패키지 의존성 관리
```powershell
# 현재 설치된 패키지 목록
pip list

# 특정 패키지 설치
pip install package_name

# requirements.txt 업데이트
pip freeze > requirements.txt
```

---

## 🔄 개발 워크플로우

### 📝 새 기능 개발 시작
```powershell
# 1. 현황 파악
docs/llm_quick_reference/01_SYSTEM_SNAPSHOT.md    # 브라우저에서 열기
docs/llm_quick_reference/02_IMPLEMENTATION_MAP.md # 기존 구현 검색

# 2. 기본 검증
python run_desktop_ui.py                          # 현재 상태 확인
pytest tests/domain/ -v                           # Domain Layer 무결성
```

### 🔧 개발 중 반복 검증
```powershell
# 빠른 구문 검사
python -c "import upbit_auto_trading; print('✅ Import 성공')"

# 특정 모듈 검사
python -c "from upbit_auto_trading.domain.services import StrategyCompatibilityService; print('✅ Service 로드 성공')"

# UI 빠른 확인
python run_desktop_ui.py
```

### ✅ 개발 완료 후 최종 검증
```powershell
# 1. 계층 위반 검사
grep -r "import sqlite3" upbit_auto_trading/domain/

# 2. UI 통합 검증
python run_desktop_ui.py

# 3. 관련 테스트 실행
pytest tests/ -k "new_feature_name" -v

# 4. 문서 업데이트 확인
# docs/llm_quick_reference/02_IMPLEMENTATION_MAP.md 업데이트 여부 확인
```

---

## 📊 디버깅 및 트러블슈팅

### 🔍 일반적인 문제 해결
```powershell
# Import 오류 해결
python -c "import sys; print('\n'.join(sys.path))"  # Python 경로 확인

# DB 연결 문제 해결
python tools/simple_db_check.py                     # DB 파일 상태 확인

# 로깅 문제 해결
$env:UPBIT_CONSOLE_OUTPUT='true'; python run_desktop_ui.py  # 강제 로깅 활성화
```

### 🚨 긴급 문제 진단
```powershell
# 시스템 전체 상태 점검
python -c "
try:
    from upbit_auto_trading.infrastructure import RepositoryContainer
    container = RepositoryContainer()
    print('✅ Infrastructure Layer 정상')

    from upbit_auto_trading.domain.services import StrategyCompatibilityService
    service = StrategyCompatibilityService()
    print('✅ Domain Services 정상')

    print('🎉 핵심 시스템 모두 정상')
except Exception as e:
    print(f'❌ 오류 발견: {e}')
"
```

### 📋 성능 모니터링
```powershell
# DB 성능 체크
python -c "
import time
from upbit_auto_trading.infrastructure import RepositoryContainer

start = time.time()
container = RepositoryContainer()
strategy_repo = container.get_strategy_repository()
strategies = strategy_repo.get_all()
end = time.time()

print(f'전략 조회 시간: {end-start:.3f}초')
print(f'전략 개수: {len(strategies)}개')
"
```

---

## 🎯 빠른 참조

### 📱 자주 쓰는 단축 조합
```powershell
# 개발 시작 (3단계)
python run_desktop_ui.py                                    # 현재 상태
docs/llm_quick_reference/02_IMPLEMENTATION_MAP.md          # 기존 구현 검색
grep -r "import sqlite3" upbit_auto_trading/domain/        # 계층 위반 검사

# 개발 완료 (3단계)
pytest tests/ -v                                           # 전체 테스트
python run_desktop_ui.py                                   # UI 통합 검증
# 02_IMPLEMENTATION_MAP.md 문서 업데이트                    # 수동 작업
```

### 🔧 핵심 환경변수
```powershell
# 로깅 제어
$env:UPBIT_CONSOLE_OUTPUT='true'                  # 콘솔 출력 활성화
$env:UPBIT_LOG_SCOPE='verbose'                    # 상세 로그
$env:UPBIT_COMPONENT_FOCUS='ComponentName'        # 특정 컴포넌트 집중

# 개발 모드
$env:PYTHONPATH="D:\projects\upbit-autotrader-vscode"  # Python 경로 (필요시)
```

### 📂 핵심 경로 (북마크 추천)
```
upbit_auto_trading/domain/services/                # Domain Services
upbit_auto_trading/application/use_cases/          # Use Cases
upbit_auto_trading/infrastructure/repositories/    # Repository 구현체
upbit_auto_trading/presentation/presenters/        # MVP Presenters
docs/llm_quick_reference/                          # 빠른 참조 문서들
```

---

**⚡ 핵심 기억사항:**
- **매일 시작**: `python run_desktop_ui.py`로 현재 상태 확인
- **개발 중**: Domain Layer 계층 위반 수시 검사
- **완료 후**: 테스트 실행 + UI 검증 + 문서 업데이트

**🚀 효율 팁**: 이 명령어들을 PowerShell 히스토리에 저장하여 `↑` 키로 빠르게 재사용!
