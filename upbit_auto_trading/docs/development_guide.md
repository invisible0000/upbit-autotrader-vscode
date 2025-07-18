# 개발 가이드

## 개발 환경 설정

### 필수 요구사항
- Python 3.8 이상
- Git

### 개발 환경 설정 방법

1. 저장소 클론
```bash
git clone <repository-url>
cd upbit-auto-trading
```

2. 가상환경 생성 및 활성화
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 개발용 의존성 설치 (선택사항)
```bash
pip install -r requirements-dev.txt
```

### 패키지 설치 환경 관리

개발 과정에서 패키지 설치 환경 문제가 자주 발생할 수 있습니다. 이러한 문제를 방지하고 해결하기 위한 지침입니다.

#### 일반적인 문제
- **패키지 설치 경로 불일치**: 시스템에 여러 Python 환경이 있을 경우, 패키지가 현재 사용 중인 Python 환경이 아닌 다른 환경에 설치될 수 있습니다.
- **패키지 버전 충돌**: 다른 프로젝트에서 사용하는 패키지 버전과 충돌이 발생할 수 있습니다.
- **패키지 설치 실패**: 의존성 문제로 인해 패키지 설치가 실패할 수 있습니다.

#### 해결 방법

1. **현재 Python 환경 확인**
   ```bash
   # 현재 사용 중인 Python 실행 파일 경로 확인
   python -c "import sys; print(sys.executable)"
   
   # 설치된 패키지 목록 확인
   pip list
   ```

2. **특정 Python 환경에 패키지 설치**
   ```bash
   # 특정 Python 실행 파일을 사용하여 패키지 설치
   /path/to/python -m pip install <package-name>
   
   # Windows 예시
   C:\Users\username\AppData\Local\Programs\Python\Python38\python.exe -m pip install PyQt6
   ```

3. **가상환경 사용 확인**
   - 가상환경이 활성화되어 있는지 확인하세요. 명령 프롬프트 또는 터미널 앞에 `(venv)` 표시가 있어야 합니다.
   - 가상환경이 활성화되어 있지 않다면, 위의 가상환경 활성화 명령을 실행하세요.

4. **패키지 설치 확인**
   ```bash
   # 특정 패키지가 설치되어 있는지 확인
   python -c "import package_name; print(package_name.__version__)"
   
   # 예시: PyQt6 설치 확인
   python -c "import PyQt6; print(PyQt6.__version__)"
   ```

5. **의존성 파일 업데이트**
   - 새로운 패키지를 설치한 후에는 항상 `requirements.txt` 파일을 업데이트하세요.
   ```bash
   pip freeze > requirements.txt
   ```

#### UI 개발 시 특별 고려사항
- PyQt6와 같은 GUI 라이브러리는 추가 의존성이 필요할 수 있습니다.
- 데스크톱 UI를 실행하기 전에 다음 명령으로 필요한 패키지가 모두 설치되어 있는지 확인하세요:
  ```bash
  pip install PyQt6 pyqtgraph matplotlib
  ```
- UI 실행 시 오류가 발생하면 패키지가 올바른 Python 환경에 설치되어 있는지 확인하세요.

## 프로젝트 구조

```
upbit_auto_trading/
├── business_logic/       # 비즈니스 로직 계층
│   ├── backtester/       # 백테스팅 기능
│   ├── portfolio/        # 포트폴리오 관리 기능
│   ├── screener/         # 종목 스크리닝 기능
│   ├── strategy/         # 매매 전략 관리 기능
│   └── trader/           # 거래 실행 기능
├── config/               # 설정 파일
├── data_layer/           # 데이터 계층
│   ├── collectors/       # 데이터 수집 기능
│   ├── processors/       # 데이터 처리 기능
│   └── storage/          # 데이터 저장 기능
├── docs/                 # 문서
├── tests/                # 테스트
│   ├── integration/      # 통합 테스트
│   └── unit/             # 단위 테스트
├── ui/                   # 사용자 인터페이스 계층
│   ├── cli/              # 명령줄 인터페이스
│   ├── web/              # 웹 인터페이스
│   └── desktop/          # 데스크톱 인터페이스
│       ├── common/       # 공통 컴포넌트
│       │   ├── styles/   # 스타일 및 테마
│       │   └── widgets/  # 공통 위젯
│       ├── models/       # UI 모델
│       ├── screens/      # 화면 컴포넌트
│       └── utils/        # UI 유틸리티
├── __init__.py           # 패키지 초기화 파일
└── requirements.txt      # 의존성 목록
```

## 코딩 스타일

이 프로젝트는 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 스타일 가이드를 따릅니다.

### 코드 포맷팅
- 들여쓰기: 4칸 공백
- 최대 줄 길이: 100자
- 문자열: 작은따옴표(`'`) 대신 큰따옴표(`"`) 사용
- 주석: 함수, 클래스, 메서드에 독스트링(docstring) 사용

### 네이밍 컨벤션
- 클래스: `CamelCase`
- 함수 및 변수: `snake_case`
- 상수: `UPPER_CASE_WITH_UNDERSCORES`
- 비공개 메서드/속성: `_leading_underscore`

## 개발 워크플로우

프로젝트는 다음과 같은 개발 워크플로우를 따릅니다:

1. **요구사항 분석**: `requirements.md` 문서 검토
2. **설계 검토**: `design.md` 문서 참조
3. **레퍼런스 문서 검토**: `reference` 폴더의 관련 문서 검토
4. **태스크 확인**: `tasks.md` 문서에서 구현할 태스크 확인
5. **테스트 작성**: 테스트 주도 개발(TDD) 방식으로 테스트 먼저 작성
6. **기능 구현**: 테스트를 통과하도록 기능 구현
7. **테스트 실행 및 디버깅**: 모든 테스트가 통과할 때까지 반복
8. **코드 리뷰 및 리팩토링**: 코드 품질 개선
9. **태스크 완료 표시**: `tasks.md` 문서에서 태스크를 완료로 표시
10. **문서 업데이트**: README.md, 설계 문서, API 문서 등 업데이트
11. **GitHub 커밋 및 푸시**: 구현 코드와 문서를 함께 커밋하고 푸시

각 태스크를 완료할 때마다 다음 문서들을 검토하고 필요한 경우 업데이트해야 합니다:
- `README.md`: 개발 현황 및 작업 로그 섹션
- `.kiro/specs/upbit-auto-trading/design.md`: 설계 문서
- `upbit_auto_trading/docs/`: API 문서 및 사용 가이드

자세한 개발 워크플로우 지침은 `.kiro/steering/development_workflow.md` 문서를 참조하세요.

### 레퍼런스 문서 활용

`reference` 폴더에는 시스템 아키텍처, 데이터베이스 스키마, API 명세, 화면 설계 등에 대한 상세 문서가 포함되어 있습니다. 이러한 레퍼런스 문서는 구현 시 중요한 참조 자료로 활용해야 합니다.

특히 UI 구현 시에는 `reference` 폴더의 화면 명세서를 적극 활용하여 일관된 사용자 경험을 제공해야 합니다. 화면 명세서에는 각 화면의 UI 요소, 기능, 백엔드 연결 정보, 사용자 경험 설계 등이 상세히 정의되어 있습니다.

레퍼런스 문서 활용에 대한 자세한 지침은 `upbit_auto_trading/docs/reference_guide.md` 문서를 참조하세요.

## 테스트

### 테스트 파일 명명 규칙
테스트 파일은 다음 형식을 따릅니다:
```
test_[태스크번호]_[기능명].py
```

예시:
- `test_02_1_upbit_api.py`: 태스크 2.1 업비트 REST API 기본 클라이언트 구현에 대한 테스트
- `test_03_2_data_collector.py`: 태스크 3.2 데이터 수집기 구현에 대한 테스트

### 테스트 ID
모든 테스트 메서드는 고유한 테스트 ID를 가져야 합니다. 테스트 ID는 다음 형식으로 출력합니다:
```python
print("\n=== 테스트 id [태스크번호]_[일련번호]: [테스트메서드명] ===")
```

예시:
```python
def test_save_screening_result(self):
    """스크리닝 결과 저장 테스트"""
    print("\n=== 테스트 id 4_2_1: test_save_screening_result ===")
    # 테스트 코드...
```

### 테스트 실행

#### 개별 테스트 파일 실행
```bash
python -m unittest upbit_auto_trading/tests/unit/test_05_2_basic_trading_strategies.py
```

#### 모든 단위 테스트 실행
```bash
pytest upbit_auto_trading/tests/unit
```

#### 통합 테스트 실행
```bash
pytest upbit_auto_trading/tests/integration
```

#### 테스트 커버리지 확인
```bash
pytest --cov=upbit_auto_trading
```

### 테스트 결과 요약
테스트 결과를 요약하여 마크다운 파일로 저장하려면 다음 명령을 실행합니다:
```bash
python run_tests_in_order.py
```

이 명령은 `test_results_summary.md` 파일을 생성하며, 다음 정보가 포함됩니다:
- 테스트 파일별 요약 (실행, 오류, 실패, 건너뜀, 상태)
- 테스트 ID별 상세 결과 (테스트 이름, 파일, 개발 단계, 테스트 내용, 상태)
- 개발 단계별 테스트 현황 (총 테스트 수, 성공, 실패, 성공률)

테스트 결과 요약을 통해 프로젝트의 테스트 상태를 쉽게 파악하고, 개발 단계별 진행 상황을 모니터링할 수 있습니다.

## Git 워크플로우

### 브랜치 전략
- `main`: 안정적인 릴리스 버전
- `develop`: 개발 중인 코드
- `feature/*`: 새로운 기능 개발
- `bugfix/*`: 버그 수정
- `release/*`: 릴리스 준비

### 커밋 컨벤션
커밋 메시지는 다음 형식을 따릅니다:
```
<type>: <subject>

<body>

<footer>
```

- `type`: feat, fix, docs, style, refactor, test, chore 중 하나
- `subject`: 변경 사항에 대한 간결한 설명
- `body`: 변경 사항에 대한 자세한 설명 (선택사항)
- `footer`: 이슈 참조 등 (선택사항)

예시:
```
feat: 이동 평균 교차 전략 구현

- 단순 이동 평균(SMA) 기반 매매 전략 구현
- 매수/매도 신호 생성 로직 추가
- 전략 매개변수 설정 기능 추가

Closes #42
```

## 릴리스 프로세스

1. `develop` 브랜치에서 `release/vX.Y.Z` 브랜치 생성
2. 버전 번호 업데이트 및 최종 테스트
3. `main` 브랜치로 병합 및 태그 생성
4. `develop` 브랜치로 병합

## 문제 해결

개발 중 문제가 발생하면 다음 단계를 따르세요:

1. 로그 확인: `logs/upbit_auto_trading.log` 및 `logs/error.log` 파일 확인
2. 이슈 트래커 검색: 유사한 문제가 이미 보고되었는지 확인
3. 이슈 생성: 새로운 문제인 경우 이슈 트래커에 상세히 보고