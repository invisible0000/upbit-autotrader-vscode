# 🚀 프로젝트 핵심 명세서

## 📋 프로젝트 개요

**프로젝트명**: 업비트 자동매매 시스템 (Upbit Auto Trading System)  
**기술스택**: Python 3.8+, PyQt6, SQLite, pandas, ta-lib  
**아키텍처**: DDD 기반 계층형 아키텍처 (Domain-Driven Design)  
**개발방법론**: 도메인 주도 설계 + 스펙 기반 개발

## 🎯 핵심 비즈니스 로직

### 1. 종목 스크리닝 시스템
- **목적**: 거래량 추세와 변동성 기반 코인 필터링
- **기준**: 24시간 거래대금, 7일 변동성, 가격 추세
- **결과**: 수익성 있는 거래 기회 식별

### 2. 매매 전략 관리 (V1.0.1)

#### 🔄 전략 역할 분리 구조
- **진입 전략**: 포지션 없을 때 최초 진입 신호 (`BUY`, `SELL`, `HOLD`)
- **관리 전략**: 활성 포지션의 리스크 관리 (`ADD_BUY`, `CLOSE_POSITION`, `UPDATE_STOP`)
- **조합 시스템**: 1개 진입 전략(필수) + 0~N개 관리 전략(선택)

#### 📈 지원 진입 전략 (6종)
1. **이동평균 교차**: 단기/장기 이평선 크로스오버
2. **RSI**: 과매도/과매수 구간 진입
3. **볼린저 밴드**: 밴드 터치 반전/돌파
4. **변동성 돌파**: 전일 변동폭 기반 돌파
5. **MACD**: 시그널 교차 및 다이버전스
6. **스토캐스틱**: %K, %D 교차 신호

#### 🛡️ 지원 관리 전략 (6종)
1. **물타기**: 하락 시 추가 매수 (최대 5회)
2. **불타기**: 상승 시 피라미드 추가 매수 (최대 3회)
3. **트레일링 스탑**: 수익률 추적 손절
4. **고정 익절/손절**: 목표 수익률 도달 시 청산
5. **부분 청산**: 단계별 수익 실현
6. **시간 기반 청산**: 최대 보유 시간 제한

### 3. 트리거 빌더 시스템

#### 3중 카테고리 호환성 시스템
- **purpose_category**: `trend`, `momentum`, `volatility`, `volume`, `price`
- **chart_category**: `overlay`, `subplot`
- **comparison_group**: `price_comparable`, `percentage_comparable`

#### 조건 생성 워크플로
1. 변수 선택 (SMA, RSI, MACD 등)
2. 파라미터 설정 (기간, 승수 등)
3. 비교 연산자 선택 (`>`, `<`, `~=` 등)
4. 대상값 설정 (고정값/외부변수)

### 4. 백테스팅 엔진
- **데이터 기준**: 1년치 분봉 데이터
- **처리 성능**: 5분 내 완료 목표
- **상태 관리**: 진입 대기 ↔ 포지션 관리 전환
- **성능 지표**: 수익률, MDD, 샤프비율, 승률

### 5. 실시간 거래 시스템
- **모니터링**: 1초 이내 시장 데이터 갱신
- **주문 실행**: 업비트 API 연동, 원자적 거래 처리
- **리스크 관리**: 최대 포지션 크기, 드로우다운 제한

## 🏗️ DDD 기반 시스템 아키텍처

### Presentation Layer (PyQt6)
```
MainWindow
├── 📊 시장 분석 (Market Analysis)
├── ⚙️ 전략 관리 (Strategy Management)
│   ├── Trigger Builder    # 조건 생성
│   ├── Strategy Maker     # 전략 조합
│   └── Backtesting       # 성능 검증
└── 🔧 설정 (Settings)
    ├── API Configuration
    ├── Database Settings
    └── Logging Controls
```

### Domain Layer (핵심 비즈니스 로직)
- **도메인 엔티티**: Strategy, Trigger, Position, Trade
- **값 객체**: StrategyId, TriggerId, TradingSignal
- **도메인 서비스**: CompatibilityChecker, SignalEvaluator
- **도메인 이벤트**: StrategyCreated, PositionOpened, TradeExecuted

### Application Layer (Use Cases)
- **전략 서비스**: StrategyApplicationService, TriggerApplicationService
- **거래 서비스**: TradingApplicationService, BacktestingApplicationService
- **DTO**: StrategyDto, TriggerDto, PositionDto

### Infrastructure Layer (외부 연동)
- **Repository**: SqliteStrategyRepository, SqliteTriggerRepository
- **API 클라이언트**: UpbitApiClient, MarketDataProvider
- **이벤트 버스**: DomainEventBus

### 데이터베이스 구조 (3-DB 아키텍처)
1. **settings.sqlite3**: 구조 정의 (변수, 파라미터, 카테고리)
2. **strategies.sqlite3**: 전략 인스턴스 (사용자 생성 전략)
3. **market_data.sqlite3**: 시장 데이터 (가격, 지표, 거래량)

### 핵심 기술적 제약사항

#### 성능 요구사항
- 백테스팅: 1년 분봉 데이터 5분 내 처리
- UI 응답성: 모든 사용자 입력 100ms 내 반응
- 실시간 데이터: 1초 이내 갱신

#### 보안 요구사항
- API 키: 환경변수 기반 관리, 하드코딩 금지
- 로깅: 민감 정보 자동 마스킹
- 데이터: 개인 정보 Git 추적 방지

#### 사용성 요구사항
- 드래그앤드롭: 직관적 전략 구성
- 실시간 미리보기: 변경사항 즉시 반영
- 오류 처리: 명확한 에러 메시지

## 🔧 개발 환경

### 필수 도구
- **OS**: Windows (PowerShell 5.1+)
- **Python**: 3.8+ (타입 힌트 필수)
- **GUI**: PyQt6
- **DB**: SQLite3
- **테스팅**: pytest

### 코딩 표준
- **PEP 8**: 엄격 준수 (79자 제한)
- **타입 힌트**: 모든 함수/메소드
- **단위 테스트**: 신규 기능 필수
- **문서화**: docstring + 인라인 주석

## 🚀 배포 전략

### 현재 지원
- **개발 모드**: `python run_desktop_ui.py`
- **Git Clone**: 소스코드 기반 설치

### 향후 계획
- **CLI 모드**: 헤드리스 자동 거래
- **포터블**: 단일 실행파일
- **클라우드**: 웹 기반 인터페이스

## 📚 관련 문서

- [아키텍처 개요](ARCHITECTURE_OVERVIEW.md)
- [개발 가이드](DEVELOPMENT_GUIDE.md)
- [전략 명세서](STRATEGY_SPECIFICATIONS.md)
- [DB 스키마](DB_SCHEMA.md)
