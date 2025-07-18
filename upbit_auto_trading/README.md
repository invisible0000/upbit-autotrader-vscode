# 업비트 자동매매 시스템

한국 업비트 거래소의 KRW 마켓 코인들을 대상으로 하는 자동매매 시스템입니다. 초단타(1시간 이내)부터 스윙(1주일 단위)까지 다양한 거래 주기를 지원하며, 종목 스크리닝, 백테스팅, 실시간 거래 기능을 제공합니다.

## 주요 기능

- 종목 스크리닝: 거래량, 변동성, 가격 추세 등을 기반으로 코인 필터링
- 데이터 관리: 시장 데이터 수집, 저장, 관리
- 매매 전략 관리: 다양한 매매 전략 생성, 수정, 저장
- 포트폴리오 구성: 여러 코인과 전략 조합 관리
- 백테스팅: 과거 데이터를 사용하여 전략 성능 테스트 (구현 완료)
  - 단일 코인 백테스팅
  - 포트폴리오 백테스팅
  - 백테스트 결과 분석 및 시각화
  - 백테스트 결과 저장 및 비교
- 실시간 거래: 검증된 전략을 사용하여 실시간 자동 거래
- 모니터링 및 알림: 시장 상황과 거래 활동 모니터링, 중요 이벤트 알림
  - 알림 센터: 가격 알림, 거래 알림, 시스템 알림 관리 (구현 완료)
  - 알림 필터링: 유형별, 읽음 상태별, 시간 범위별 필터링
  - 알림 설정: 알림 활성화/비활성화, 알림 방법, 알림 빈도 설정
- 사용자 인터페이스: 직관적인 데스크톱 UI로 모든 기능에 쉽게 접근
  - 다크 모드/라이트 모드 지원
  - 화면 간 쉬운 전환을 위한 네비게이션 바
  - 시스템 상태 모니터링을 위한 상태 바
  - 사용자 설정 저장 및 로드 기능
  - 윈도우 크기 및 위치 기억 기능
  - 대시보드 화면 (구현 완료):
    - 포트폴리오 요약 위젯: 보유 자산의 구성을 보여주는 도넛 차트와 목록
    - 활성 거래 목록 위젯: 현재 진입해 있는 모든 포지션의 상세 내역
    - 시장 개요 위젯: 주기적으로 수집된 대표 코인들의 시세 정보
    - 5초 주기 자동 데이터 갱신 기능
  - 차트 뷰 화면 (진행 중):
    - 캔들스틱 차트: 다양한 시간대(1분~1주)의 가격 데이터 시각화
    - 기술적 지표 오버레이: SMA, EMA, 볼린저 밴드, RSI, MACD, 스토캐스틱 등
    - 거래 시점 마커: 백테스트 및 실시간 거래의 매수/매도 시점 표시
    - 차트 확대/축소 및 이동 기능

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

- [문서 목록](docs/README.md)
- [개발 가이드](docs/development_guide.md)
- [API 문서](docs/api_docs.md)
- [대시보드 가이드](docs/dashboard_guide.md)
- [차트 뷰 가이드](docs/chart_view_guide.md)
- [알림 센터 가이드](docs/notification_guide.md)
- [백테스팅 가이드](docs/backtesting_guide.md)
- [레퍼런스 문서 활용 가이드](docs/reference_guide.md)
- [테스트 결과 요약](docs/test_results_summary.md)

### 레퍼런스 문서

시스템 설계 및 구현에 필요한 상세 레퍼런스 문서는 프로젝트 루트의 `reference` 폴더에서 확인할 수 있습니다:

- [시스템 아키텍처 설계서](../reference/01_system_architecture_design.md) - C4 모델 기반 시스템 구조 설명
- [데이터베이스 스키마 명세서](../reference/02_database_schema_specification_erd.md)
- [API 명세서](../reference/03_api_specification.md)
- [배포 및 운영 가이드](../reference/04_deployment_and_operations_guide.md)
- [보안 설계 문서](../reference/05_security_design_document.md)
- [UI 명세서](../reference/ui_spec_01_main_dashboard.md) 등

## 라이선스

MIT License