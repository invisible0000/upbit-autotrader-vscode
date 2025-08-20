# 📋 TASK_20250820_02: Market Data Coordinator 개발

## 🎯 태스크 목표
- **주요 목표**: Smart Routing을 조율하여 대용량 마켓 데이터 요청을 효율적으로 처리
- **완료 기준**: 200개 초과 요청을 분할하여 병렬 처리하고 결과를 통합하는 시스템 구현

## 📊 현재 상황 분석
### Coordinator의 역할 정의
- **Layer 2 포지션**: Smart Routing(Layer 1)과 Market Data Storage(Layer 3) 중간
- **대용량 요청 분할**: 200개 초과 요청을 Smart Routing이 처리할 수 있는 크기로 분할
- **다중 데이터 타입 처리**: 캔들, 티커, 호가창, 체결 각각의 분할 전략
- **저장 정책 구분**: 캔들(DB 저장) vs 티커/호가창/체결(메모리 캐시만)
- **병렬 최적화**: 동시 요청 수 제어, 성능 최적화
- **결과 통합**: 분할된 응답들을 하나의 완전한 데이터셋으로 합성

### 핵심 사용 사례
1. **대용량 캔들 데이터**: 1000개 캔들 데이터 → 5번의 200개 요청으로 분할 → **DB 저장**
2. **장기간 데이터**: 3개월간 1분봉 데이터 → 수십 번의 시간 범위별 요청 → **DB 저장**
3. **다중 심볼 티커**: 100개 심볼의 티커 데이터 → 여러 번의 100개씩 분할 요청 → **메모리 캐시만**
4. **대량 호가창**: 여러 코인의 호가창 동시 수집 → 5개씩 분할 처리 → **메모리 캐시만**

## 💾 데이터 저장 정책 (중요)

### ✅ **DB 저장 대상 (Market Data DB)**
- **캔들 데이터 (OHLCV)**: 백테스트, 차트 표시, 기술적 분석에 필수
  - Open, High, Low, Close, Volume
  - 타임스탬프, 심볼, 타임프레임
  - **이유**: 과거 데이터 조회 필요, 영속성 중요, 용량 관리 가능

### ❌ **DB 저장 제외 (메모리 캐시만)**
- **티커 데이터**: 현재가, 24시간 변동률 등
  - **이유**: 실시간 최신 정보만 필요, 과거 데이터 무의미
- **호가창 데이터**: 매수/매도 호가 리스트
  - **이유**: 극도로 빠른 변동, 과거 데이터 무의미, 대용량
- **체결 내역**: 개별 거래 기록
  - **이유**: 대용량, 일시적, 캔들로 집계되므로 개별 저장 불필요

### 🗂️ **별도 DB 대상**
- **전략 실행 데이터**: 포지션, 주문, 손익 → `strategies.sqlite3`
- **설정 데이터**: 사용자 설정, 환경 변수 → `settings.sqlite3`

## 🔄 체계적 작업 절차

### Phase 1: 핵심 인터페이스 설계
- [ ] 1.1 IMarketDataCoordinator 인터페이스 정의 (다중 데이터 타입)
- [ ] 1.2 요청/응답 모델 설계 (캔들, 티커, 호가창, 체결별)
- [ ] 1.3 분할 전략 인터페이스 설계 (데이터 타입별)
- [ ] 1.4 저장 정책 인터페이스 설계 (캔들=DB, 티커/호가창/체결=메모리)
- [ ] 1.5 예외 처리 체계 설계

### Phase 2: 데이터 타입별 분할 전략 구현
- [ ] 2.1 캔들 데이터 분할 전략 (CandleSplitter - 시간 기반)
- [ ] 2.2 티커 데이터 분할 전략 (TickerSplitter - 심볼 기반)
- [ ] 2.3 호가창 데이터 분할 전략 (OrderbookSplitter - 심볼 기반)
- [ ] 2.4 체결 데이터 분할 전략 (TradeSplitter - 시간/카운트 기반)

### Phase 3: 병렬 처리 및 최적화
- [ ] 3.1 비동기 병렬 요청 처리기 구현
- [ ] 3.2 레이트 제한 준수 로직 (업비트 API 제한)
- [ ] 3.3 오류 복구 및 재시도 로직
- [ ] 3.4 요청 우선순위 관리### Phase 4: 결과 통합 및 검증
- [ ] 4.1 데이터 통합기 구현 (DataAggregator - 타입별)
- [ ] 4.2 데이터 정합성 검증 로직 (타입별 검증 규칙)
- [ ] 4.3 중복 제거 및 정렬 로직 (타입별 정렬 기준)
- [ ] 4.4 메타데이터 관리 (요청 통계, 성능 지표)

### Phase 5: 사용 사례별 최적화
- [ ] 5.1 스크리닝 최적화기 (ScreeningOptimizer - 최신 데이터 우선)
- [ ] 5.2 백테스트 최적화기 (BacktestOptimizer - 과거 데이터 청크)
- [ ] 5.3 차트 뷰어 최적화기 (ChartOptimizer - 증분 업데이트)
- [ ] 5.4 다중 심볼 배치 처리기 (MultisymbolBatchProcessor)

## 🛠️ 폴더 구조 및 파일 설계

### 폴더 구조
```
market_data_coordinator/
├── __init__.py
├── interfaces/                    # 추상 인터페이스
│   ├── __init__.py
│   ├── coordinator.py            # IMarketDataCoordinator
│   ├── splitter.py               # ISplitStrategy
│   ├── aggregator.py             # IDataAggregator
│   └── optimizer.py              # IOptimizer
├── implementations/               # 핵심 구현체
│   ├── __init__.py
│   ├── market_data_coordinator.py # 메인 조율자
│   ├── request_splitter.py       # 요청 분할기
│   ├── data_aggregator.py        # 결과 통합기
│   └── performance_monitor.py    # 성능 모니터링
├── strategies/                    # 분할 전략
│   ├── __init__.py
│   ├── candle_splitter.py        # 캔들 데이터 시간 기반 분할
│   ├── ticker_splitter.py        # 티커 데이터 심볼 기반 분할
│   ├── orderbook_splitter.py     # 호가창 데이터 심볼 기반 분할
│   ├── trade_splitter.py         # 체결 데이터 시간/카운트 기반 분할
│   └── strategy_factory.py       # 데이터 타입별 전략 팩토리
├── optimizers/                    # 사용 사례별 최적화
│   ├── __init__.py
│   ├── screening_optimizer.py    # 스크리닝 최적화
│   ├── backtest_optimizer.py     # 백테스트 최적화
│   ├── realtime_optimizer.py     # 실시간 최적화
│   └── multisymbol_processor.py  # 다중 심볼 처리
├── models/                        # 데이터 모델
│   ├── __init__.py
│   ├── requests.py               # 대용량 요청 모델
│   ├── responses.py              # 통합 응답 모델
│   ├── split_plan.py             # 분할 계획 모델
│   └── aggregation_result.py     # 통합 결과 모델
└── utils/                         # 유틸리티
    ├── __init__.py
    ├── time_calculator.py         # 시간 계산 유틸
    ├── rate_limiter.py            # 레이트 제한 관리
    ├── retry_handler.py           # 재시도 로직
    └── validators.py              # 데이터 검증
```

## 🎯 핵심 구현 목표

### 1. 지능적 분할 전략
```python
# 예시: 1000개 캔들 요청을 5번의 200개 요청으로 분할 → DB 저장
class CandleSplitter:
    def split_request(self, request: LargeCandleRequest) -> List[SmallCandleRequest]:
        """
        대용량 캔들 요청을 Smart Routing이 처리할 수 있는 크기로 분할
        - 시간 범위 기반 분할
        - 최대 200개 제한 준수
        - 겹치지 않는 시간 구간 생성
        - 결과는 DB에 저장됨
        """

# 예시: 100개 티커 요청을 여러 번으로 분할 → 메모리 캐시만
class TickerSplitter:
    def split_request(self, request: LargeTickerRequest) -> List[SmallTickerRequest]:
        """
        다중 심볼 티커 요청을 분할
        - 심볼 기반 분할 (100개씩)
        - 결과는 메모리 캐시에만 저장
        - DB 저장 없음 (실시간 데이터)
        """
```

### 2. 병렬 처리 최적화
```python
# 예시: 5개 요청을 동시에 처리하되 레이트 제한 준수
class ParallelRequestProcessor:
    async def process_requests(
        self,
        split_requests: List[SmallDataRequest]
    ) -> List[SmallDataResponse]:
        """
        - 동시 요청 수 제어 (예: 3개씩)
        - 업비트 API 레이트 제한 준수
        - 실패한 요청 재시도
        - 진행률 추적
        """
```

### 3. 데이터 통합 및 검증
```python
# 예시: 분할된 응답들을 하나의 완전한 데이터셋으로 통합
class DataAggregator:
    def aggregate_candle_responses(
        self,
        responses: List[SmallCandleResponse]
    ) -> LargeCandleResponse:
        """
        캔들 데이터 통합 (DB 저장 대상)
        - 시간순 정렬
        - 중복 데이터 제거
        - 데이터 연속성 검증
        - 메타데이터 생성 (총 개수, 시간 범위 등)
        """

    def aggregate_ticker_responses(
        self,
        responses: List[SmallTickerResponse]
    ) -> LargeTickerResponse:
        """
        티커 데이터 통합 (메모리 캐시만)
        - 심볼별 최신 데이터만 유지
        - DB 저장 없음
        - 메모리 효율성 우선
        """
```

## 🔗 다른 레이어와의 협력

### Smart Routing (Layer 1) 협력
- **의존성**: Smart Router의 다중 API 인터페이스 사용 (get_candle_data, get_ticker_data 등)
- **호출 방식**: 분할된 소규모 요청들을 순차/병렬 호출 (데이터 타입별)
- **에러 처리**: Smart Routing 에러를 상위로 전파하거나 재시도
- **빈도 조절**: Smart Router의 빈도 분석을 위해 적절한 간격으로 요청

### Market Data Storage (Layer 3) 협력
- **캔들 데이터**: 통합된 대용량 캔들 데이터를 Storage DB에 저장
- **실시간 데이터**: 티커/호가창/체결은 Storage의 메모리 캐시에만 저장
- **캐시 활용**: Storage의 기존 캔들 데이터 활용하여 증분 요청만 수행
- **메타데이터**: 요청 통계, 성능 지표를 Storage에 저장

## 💡 성능 최적화 전략

### 1. 스크리닝 최적화
- **최신 우선**: 현재 시간부터 역순으로 데이터 수집
- **조기 종료**: 필요한 데이터만 수집 후 중단
- **캐시 활용**: 최근 데이터는 캐시에서 우선 조회

### 2. 백테스트 최적화
- **청크 단위**: 월/주 단위로 데이터 분할 수집
- **병렬 처리**: 여러 시간 구간을 동시에 수집
- **진행률 추적**: 대용량 백테스트 진행 상황 모니터링

### 3. 실시간 업데이트
- **증분 수집**: 마지막 업데이트 이후 데이터만 요청
- **효율적 통합**: 기존 데이터에 새 데이터 병합
- **중복 방지**: 타임스탬프 기반 중복 검사

## 🎯 성공 기준
- ✅ **다중 타입 분할 처리**: 캔들 1000개+, 티커 100개+, 호가창 다중 심볼 등을 자동 분할
- ✅ **병렬 최적화**: 동시 요청으로 처리 시간 단축 (3-5배)
- ✅ **데이터 정합성**: 분할/통합 과정에서 데이터 손실 없음 (타입별 검증)
- ✅ **에러 복구**: 일부 요청 실패 시 재시도 및 복구
- ✅ **레이트 제한 준수**: 업비트 API 제한 내에서 안정적 동작 (타입별 제한)

## 🚀 개발 우선순위
1. **Phase 1**: 핵심 인터페이스 (IMarketDataCoordinator)
2. **Phase 2**: 기본 분할 전략 (TimeBasedSplitter)
3. **Phase 3**: 병렬 처리 (ParallelRequestProcessor)
4. **Phase 4**: 데이터 통합 (DataAggregator)
5. **Phase 5**: 사용 사례별 최적화

---
**의존성**: TASK_20250820_01 Smart Routing 완료 후 시작
**연관 태스크**: TASK_20250820_03 Market Data Storage 개발
**예상 소요시간**: 2-3일 (Smart Routing 완료 후)
**핵심 가치**: 대용량 데이터 처리의 복잡성을 완전히 추상화
