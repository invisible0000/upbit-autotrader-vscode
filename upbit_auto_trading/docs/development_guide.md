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
│   └── web/              # 웹 인터페이스
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

## 테스트

### 단위 테스트
```bash
pytest upbit_auto_trading/tests/unit
```

### 통합 테스트
```bash
pytest upbit_auto_trading/tests/integration
```

### 테스트 커버리지 확인
```bash
pytest --cov=upbit_auto_trading
```

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