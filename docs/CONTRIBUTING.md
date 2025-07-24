# 기여 가이드

업비트 자동매매 시스템 프로젝트에 기여해 주셔서 감사합니다. 이 문서는 프로젝트에 기여하는 방법에 대한 가이드라인을 제공합니다.

## 개발 환경 설정

1. 저장소 포크 및 클론
```bash
git clone <your-forked-repository-url>
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
pip install -r requirements-dev.txt
```

## 브랜치 전략

프로젝트는 다음과 같은 브랜치 전략을 사용합니다:

- `main`: 안정적인 릴리스 버전
- `develop`: 개발 중인 코드
- `feature/*`: 새로운 기능 개발
- `bugfix/*`: 버그 수정
- `release/*`: 릴리스 준비

기여할 때는 다음 단계를 따라주세요:

1. `develop` 브랜치에서 새 브랜치 생성
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

2. 변경 사항 구현 및 커밋
```bash
git add .
git commit -m "feat: 기능 구현 설명"
```

3. 원격 저장소에 푸시
```bash
git push origin feature/your-feature-name
```

4. Pull Request 생성
   - 베이스 브랜치: `develop`
   - 비교 브랜치: `feature/your-feature-name`

## 커밋 컨벤션

커밋 메시지는 다음 형식을 따릅니다:
```
<type>: <subject>

<body>

<footer>
```

- `type`: 다음 중 하나
  - `feat`: 새로운 기능 추가
  - `fix`: 버그 수정
  - `docs`: 문서 변경
  - `style`: 코드 포맷팅, 세미콜론 누락 등 (코드 변경 없음)
  - `refactor`: 코드 리팩토링
  - `test`: 테스트 코드 추가 또는 수정
  - `chore`: 빌드 프로세스, 패키지 매니저 설정 등 변경
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

## 코드 스타일

이 프로젝트는 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 스타일 가이드를 따릅니다.

- 들여쓰기: 4칸 공백
- 최대 줄 길이: 100자
- 문자열: 작은따옴표(`'`) 대신 큰따옴표(`"`) 사용
- 주석: 함수, 클래스, 메서드에 독스트링(docstring) 사용

코드 스타일 검사:
```bash
flake8 upbit_auto_trading
```

코드 포맷팅:
```bash
black upbit_auto_trading
```

## 테스트

변경 사항을 제출하기 전에 모든 테스트가 통과하는지 확인해주세요:

```bash
# 모든 테스트 실행
pytest

# 단위 테스트만 실행
pytest upbit_auto_trading/tests/unit

# 통합 테스트만 실행
pytest upbit_auto_trading/tests/integration

# 테스트 커버리지 확인
pytest --cov=upbit_auto_trading
```

## Pull Request 가이드라인

Pull Request를 생성할 때 다음 사항을 포함해주세요:

1. PR의 목적과 해결하는 문제 설명
2. 구현 방법에 대한 간략한 설명
3. 관련 이슈 링크
4. 테스트 결과 또는 스크린샷 (해당하는 경우)

## 라이선스

이 프로젝트에 기여함으로써, 귀하는 귀하의 기여가 프로젝트의 라이선스(MIT)에 따라 배포됨에 동의합니다.