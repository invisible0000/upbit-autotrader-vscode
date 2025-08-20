# 📋 TASK_20250820_01: Smart Routing 완전 추상화 재설계

## 🎯 태스크 목표
- **주요 목표**: URL 기반에서 도메인 모델 기반으로 Smart Router 완전 재설계
- **완료 기준**: 내부 시스템이 업비트 API 구조를 몰라도 되는 완전한 추상화 구현

## 📊 현재 상황 분석
### 문제점
1. **API 종속적 인터페이스**: `get_data("/v1/candles/minutes/15?market=KRW-BTC")` 형태로 호출
2. **추상화 부족**: 내부 시스템이 여전히 업비트 API URL 구조를 알아야 함
3. **도메인 모델 부재**: 비즈니스 개념(심볼, 타임프레임)이 URL에 숨어있음
4. **확장성 제약**: 다른 거래소 추가 시 모든 호출 코드 수정 필요

### 사용 가능한 리소스
- 기존 구현체: `smart_routing_backup/` 폴더 (패턴 분석, 레이트 제한 등 로직 재활용 가능)
- WebSocket 구독 관리: subscription_manager.py 로직
- 필드 매핑: FieldMapper 클래스 로직
- **중요**: 아직 이 기능이 실제 사용되지 않음 → 즉시 마이그레이션 가능
- 교체 대상: market_data_backbone 기존 기능, 차트뷰어 호출 코드

## 🔄 수정된 체계적 작업 절차 (최소화)

### 🎯 핵심 문제점 식별 (수정됨)
1. **실시간 처리 방식 모호**: `subscribe_realtime()` vs `get_candle_data(streaming=True)` 선택 필요
2. **Smart Router 혼란 방지**: 히스토리 분석 없이 명확한 채널 지시 받기
3. **인터페이스 통합**: 단일 API로 일회성/실시간 모두 처리
4. **역할 분리 강화**: 각 레이어의 책임 명확화

### 🎯 명확한 역할 분리 정책 (3-Layer 아키텍처)

#### Layer 1: Smart Routing (가장 하위 - API 추상화)
- **API 추상화**: URL 구조 완전 은닉, 도메인 모델만 노출
- **빈도 기반 채널 선택**: 요청 빈도 분석으로 REST ↔ WebSocket 자동 전환
- **다중 데이터 타입**: get_candle_data(), get_ticker_data(), get_orderbook_data(), get_trade_data()
- **제한 준수**: 업비트 API 제한 내에서만 동작 (캔들 200개, 티커 100개 등)
- **WebSocket 관리**: 구독 생명주기, 재연결, 빈도 저조 시 자동 해제

#### Layer 2: Market Data Coordinator (중간 레이어 - 요청 조율)
- **대용량 처리**: 200개 초과 캔들 요청을 분할하여 Smart Routing 다중 호출
- **다중 데이터 타입**: 각 데이터 타입별 분할 전략 (캔들, 티커, 호가창, 체결)
- **병렬 최적화**: 동시 요청 수 제어, 레이트 제한 관리
- **결과 통합**: 분할된 응답들을 하나로 합성 (데이터 타입별 로직)
- **Simple Interface**: 빈도 조절은 상위에서, 채널 선택은 Smart Router에서

#### Layer 3: Market Data Storage (상위 레이어 - 데이터 관리)
- **DB 관리**: 마켓 데이터 영속성, 스키마 관리 (데이터 타입별 테이블)
- **캐싱 전략**: 메모리/디스크 캐시, 만료 정책 (타입별 최적화)
- **증분 업데이트**: 기존 데이터 활용, 효율적 갱신
- **다중 API 인터페이스**: get_candle_data(), get_ticker_data(), get_orderbook_data(), get_trade_data()
- **빈도 조절**: 사용 사례별 요청 빈도 최적화 (실시간 차트=고빈도, 백테스트=저빈도)

### Phase 1: 핵심 인터페이스 호환성 수정 (긴급)
- [ ] 1.1 기존 IDataRouter 인터페이스 분석 및 호환 구조 설계
- [ ] 1.2 최소 동작 가능한 Provider 구현 (UpbitProvider with REST)
- [ ] 1.3 시간 범위 요청 파라미터 명확화 (start_time, end_time, count 우선순위)
- [ ] 1.4 기본 동작 테스트 (get_candle_data 호출)

### Phase 2: 최소 동작 가능한 구현
- [ ] 2.1 IDataRouter 호환 SmartDataRouter 구현 (기존 인터페이스 유지)
- [ ] 2.2 Request 객체 내부 변환 로직 구현
- [ ] 2.3 기본 업비트 제공자 구현 (REST만)
- [ ] 2.4 채널 선택 최소 로직 (REST 우선, 조건부 WebSocket)

### Phase 3: 확장 기능 (나중에)
- [ ] 3.1 WebSocket 구독 관리 로직 통합
- [ ] 3.2 레이트 제한 로직 통합
- [ ] 3.3 필드 매핑 로직 통합
- [ ] 3.4 패턴 분석 로직 통합

### Phase 4: 최소 테스트 및 검증
- [ ] 4.1 기본 동작 테스트 (캔들 데이터 조회)
- [ ] 4.2 시간 범위 요청 테스트 (start_time, end_time, count)
- [ ] 4.3 기존 호출 코드와의 호환성 테스트

### 확인된 교체 대상
- `unified_market_data_api.py`: 기존 SmartChannelRouter 사용 중
- `test_smart_routing_core.py`: 테스트 코드 교체 필요
- smart_routing 폴더: 완전히 새로 구현

## 🛠️ 개발할 도구 및 파일 구조

### 새로운 폴더 구조
```
smart_routing/
├── __init__.py
├── models/                     # 도메인 모델
│   ├── __init__.py
│   ├── symbols.py             # TradingSymbol 클래스
│   ├── timeframes.py          # Timeframe 열거형
│   ├── market_data_types.py   # 캔들, 티커, 호가창, 체결 모델
│   ├── requests.py            # 각 데이터 타입별 요청 모델
│   └── responses.py           # 각 데이터 타입별 응답 모델
├── interfaces/                 # 추상 인터페이스
│   ├── __init__.py
│   ├── data_router.py         # IDataRouter (다중 데이터 타입)
│   └── data_provider.py       # IDataProvider (업비트 전용)
├── implementations/            # 구현체
│   ├── __init__.py
│   ├── smart_data_router.py   # 빈도 기반 스마트 라우터
│   ├── upbit_rest_provider.py # REST API 제공자
│   └── upbit_ws_provider.py   # WebSocket 제공자
├── strategies/                 # 라우팅 전략
│   ├── __init__.py
│   ├── frequency_analyzer.py  # 요청 빈도 분석
│   ├── channel_selector.py    # 빈도 기반 채널 선택
│   └── websocket_manager.py   # WebSocket 생명주기 관리
└── utils/                      # 유틸리티
    ├── __init__.py
    ├── field_mapper.py         # 필드 매핑 (데이터 타입별)
    ├── rate_limiter.py         # 레이트 제한 (API별)
    └── exceptions.py           # 예외 클래스들
```

### 핵심 도구들
- `models/symbols.py`: 거래소 독립적 심볼 관리
- `models/timeframes.py`: 표준화된 타임프레임 정의
- `models/market_data_types.py`: 캔들, 티커, 호가창, 체결 데이터 모델
- `implementations/smart_data_router.py`: 빈도 기반 채널 선택 라우터
- `strategies/frequency_analyzer.py`: 요청 빈도 분석 및 WebSocket 전환 로직

## 🎯 수정된 성공 기준 (최소화)
- ✅ **호환성 우선**: 기존 `IDataRouter` 인터페이스 그대로 구현하되, 내부에서 스마트 라우팅
- ✅ **시간 파라미터 명확화**: `count`, `start_time`, `end_time` 우선순위와 변환 로직 명확 정의
- ✅ **최소 동작**: 캔들 데이터 조회가 정상 작동 (REST API 우선)
- ✅ **확장 가능한 구조**: 향후 WebSocket, 레이트 제한 등 추가 가능한 아키텍처

## 💡 수정된 작업 시 주의사항
### 최소화 원칙
- **기존 인터페이스 유지**: `IDataRouter` 시그니처 변경 금지
- **내부 추상화**: Request 객체는 내부에서만 사용, 외부는 기존 파라미터 방식
- **점진적 확장**: REST API만으로 최소 동작 먼저, WebSocket은 나중에
- **시간 처리 명확화**: start_time 기준 최대 200개, 초과 시 에러 반환

### 시간 파라미터 처리 정책 (수정됨)
```python
# Smart Routing 시간 처리 정책
def handle_candle_request(start_time, end_time, count, timeframe):
    """
    1. start_time이 주어지면 시작점으로 사용
    2. 업비트 API 최대 200개 제한 준수
    3. 200개 초과 예상 시 에러 반환 → Data Persistence가 분할 처리
    4. 스크리너: 현재 시간부터 역순으로 N개 (최신 데이터 우선)
    5. 백테스트: start_time부터 순서대로 최대 200개
    """
    if start_time and end_time:
        estimated_count = calculate_expected_count(start_time, end_time, timeframe)
        if estimated_count > 200:
            raise DataRangeExceedsLimitException(
                f"요청 범위 초과: 예상 {estimated_count}개 > 최대 200개. "
                f"Data Persistence에서 분할 요청 필요"
            )

    return process_within_api_limits(start_time, end_time, count)
```

### 간소화된 구조
```
smart_routing/
├── models/                     # 내부 도메인 모델만
│   ├── symbols.py             # TradingSymbol
│   ├── timeframes.py          # Timeframe
│   └── requests.py            # 내부 Request 객체들
├── interfaces/                 # 기존 인터페이스 유지
│   ├── data_router.py         # IDataRouter (기존 시그니처)
│   └── data_provider.py       # IDataProvider (간소화)
├── implementations/            # 최소 구현
│   ├── smart_data_router.py   # 기존 인터페이스 구현
│   └── upbit_provider.py      # REST API만
└── utils/                      # 최소 유틸리티
    └── exceptions.py           # 예외 클래스들
```

## 🚀 즉시 시작할 작업 (수정됨)
1. **Phase 1.1 긴급 수정**: 기존 IDataRouter 인터페이스에 누락된 클래스들 정의
2. **시간 파라미터 우선순위 명확화**: start_time → 최대 200개 → 에러 반환
3. **최소 SmartDataRouter 구현**: 기존 시그니처 유지하되 내부에서 Request 객체 변환

```python
# 수정된 첫 번째 구현 목표 (빈도 기반 채널 선택)
class SmartDataRouter(IDataRouter):
    async def get_candle_data(
        self,
        symbol: TradingSymbol,
        timeframe: Timeframe,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[CandleData]:
        # 1. 빈도 분석: 이 심볼/타임프레임 최근 요청 빈도 확인
        request_frequency = self._frequency_analyzer.get_frequency(
            symbol, timeframe, window_minutes=5
        )

        # 2. 채널 선택: 빈도 임계값 기반 자동 결정
        if request_frequency > self._websocket_threshold:
            # 고빈도: WebSocket 구독 활성화
            if not self._websocket_manager.is_subscribed(symbol, timeframe):
                await self._websocket_manager.subscribe(symbol, timeframe)
            return await self._websocket_provider.get_cached_data(
                symbol, timeframe, count, start_time, end_time
            )
        else:
            # 저빈도: REST API 사용
            return await self._rest_provider.fetch_candle_data(
                symbol, timeframe, count, start_time, end_time
            )

    async def get_ticker_data(self, symbols: List[TradingSymbol]) -> List[TickerData]:
        """티커 데이터 - 빈도 기반 채널 선택"""
        pass

    async def get_orderbook_data(self, symbol: TradingSymbol) -> OrderbookData:
        """호가창 데이터 - 빈도 기반 채널 선택"""
        pass

    async def get_trade_data(
        self,
        symbol: TradingSymbol,
        count: Optional[int] = None
    ) -> List[TradeData]:
        """체결 데이터 - 빈도 기반 채널 선택"""
        pass
```

### 🔄 역할 분리 후 리팩터링 계획
1. **smart_routing_backup02 생성**: 현재 구현 백업
2. **Smart Routing 재구현**: 단순하고 명확한 책임만 (Layer 1)
3. **Market Data Coordinator 신규 개발**: 요청 조율 레이어 (Layer 2)
4. **Market Data Storage 분리**: DB 관리 레이어 (Layer 3)
5. **인터페이스 호환성 보장**: 기존 호출 코드 수정 없이 교체

### 📁 3-Layer 폴더 구조 + Backbone API
```
market_data_backbone/
├── __init__.py                 # 통합 API 엔트리포인트
├── market_data_api.py          # 메인 API - 전체 시스템 인터페이스
├── backbone_manager.py         # 3-Layer 조율 및 생명주기 관리
├── config/                     # 설정 관리
│   ├── __init__.py
│   ├── backbone_config.py      # 전체 백본 설정
│   ├── layer_configs.py        # 각 레이어별 설정
│   └── performance_config.py   # 성능 튜닝 설정
├── interfaces/                 # 통합 인터페이스
│   ├── __init__.py
│   ├── market_data_api.py      # IMarketDataAPI - 외부 인터페이스
│   └── backbone_manager.py     # IBackboneManager - 내부 관리
├── smart_routing/              # Layer 1: API 추상화
│   ├── models/
│   ├── interfaces/
│   ├── implementations/
│   └── utils/
├── market_data_coordinator/    # Layer 2: 요청 조율
│   ├── interfaces/
│   ├── implementations/
│   ├── strategies/             # 분할 전략
│   └── optimizers/             # 성능 최적화
├── market_data_storage/        # Layer 3: 데이터 관리
│   ├── interfaces/
│   ├── implementations/
│   ├── cache/                  # 캐싱 전략
│   └── persistence/            # DB 관리
└── utils/                      # 공통 유틸리티
    ├── __init__.py
    ├── health_monitor.py       # 전체 백본 헬스 체크
    ├── performance_tracker.py  # 성능 추적
    └── dependency_injection.py # DI 컨테이너
```

---
**상태**: 완전 재개발 예정 - 모든 단계 미완료로 초기화
**백업 계획**: smart_routing → smart_routing_backup02
**다음 작업**: 3-Layer 아키텍처로 새로운 구조 설계
**연관 태스크**:
- TASK_20250820_02 Market Data Coordinator 개발
- TASK_20250820_03 Market Data Storage 개발
- TASK_20250820_04 Market Data Backbone API 개발 (통합 API)
