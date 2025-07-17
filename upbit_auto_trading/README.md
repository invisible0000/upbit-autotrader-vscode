# 업비트 자동매매 시스템

한국 업비트 거래소의 KRW 마켓 코인들을 대상으로 하는 자동매매 시스템입니다. 초단타(1시간 이내)부터 스윙(1주일 단위)까지 다양한 거래 주기를 지원하며, 종목 스크리닝, 백테스팅, 실시간 거래 기능을 제공합니다.

## 주요 기능

- 종목 스크리닝: 거래량, 변동성, 가격 추세 등을 기반으로 코인 필터링
- 데이터 관리: 시장 데이터 수집, 저장, 관리
- 매매 전략 관리: 다양한 매매 전략 생성, 수정, 저장
- 포트폴리오 구성: 여러 코인과 전략 조합 관리
- 백테스팅: 과거 데이터를 사용하여 전략 성능 테스트
- 실시간 거래: 검증된 전략을 사용하여 실시간 자동 거래
- 모니터링 및 알림: 시장 상황과 거래 활동 모니터링, 중요 이벤트 알림

## 설치 및 설정

### 요구사항

- Python 3.8 이상
- 업비트 API 키

### 설치

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 설정

1. `config/config.yaml` 파일을 열고 필요한 설정을 수정합니다.
2. 업비트 API 키를 설정합니다.

## 사용 방법

```bash
# 애플리케이션 실행
python -m upbit_auto_trading
```

## 개발 가이드

- [개발 가이드](docs/development_guide.md)
- [API 문서](docs/api_docs.md)

## 라이선스

MIT License