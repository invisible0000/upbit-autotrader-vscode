# 📋 TASK_20250820_01: Smart Routing 완전 추상화 재설계

###### Layer 3: Market Data Storage (상위 레이어 - 데이터 관리)
- **DB 관리**: 마켓 데이터 영속성, 스키마 관리 (데이터 타입별 테이블)
- **통합 캐싱 전략**: 메모리/디스크 캐시, 만료 정책 (타입별 최적화)
- **스마트 라우터 메모리 활용**: Storage가 Smart Router 메모리 캐시 확인 후 활용 ✅ **확정**
- **증분 업데이트**: 기존 데이터 활용, 효율적 갱신
- **다중 API 인터페이스**: get_candle_data(), get_ticker_data(), get_orderbook_data(), get_trade_data()
- **사용 패턴 최적화**: 사용 사례별 요청 빈도 최적화 (실시간 차트=고빈도, 백테스트=저빈도)크 목표
- **주요 목표**: 기존 Smart Router 코드를 **점진적 개선**하여 실거래 데이터 아키텍처 완성
- **완료 기준**: 실시간 데이터 캐시 + 자율적 최적화 + 3-Layer 통합으로 실거래 성능 보장

## 📊 현재 상황 분석 (재평가)
### ✅ **이미 완성된 부분 (재사용)**
1. **도메인 모델**: TradingSymbol, Timeframe 등 훌륭하게 설계됨
2. **인터페이스**: IDataRouter, IDataProvider 완전 추상화 달성
3. **기본 구현체**: SmartDataRouter 550라인, 상당한 완성도
4. **유틸리티**: FieldMapper, RateLimiter, 예외 처리 체계

### ⚠️ **개선 필요한 부분 (집중 개발)**
1. **실시간 데이터 통합**: WebSocket → RealtimeDataCache → 매매변수 계산
2. **자율적 최적화 완성**: FrequencyAnalyzer, ChannelSelector 완료
3. **WebSocket 장애 복구**: 다층 Fallback 전략 구현 (즉시 대응 → 배치 모사 → 시스템 모드 전환)
4. **3-Layer 통합**: Coordinator, Storage와의 연결 구현
5. **실거래 우선순위**: Critical Path 성능 보장

### 📊 **재사용 가능한 리소스**
- **현재 구현체**: `smart_routing/` 폴더 (Phase 1-2 완료 상태)
- **레거시 백업**: `smart_routing_backup/` 폴더 (참고용 로직)
- **WebSocket 시스템**: BatchWebSocketManager, UIAwareManager 활용
- **테이블 설계**: 심볼별×타임프레임별 개별 테이블 확정

## 🔄 체계적 작업 절차

### 🎯 핵심 문제점 식별
1. **실시간 처리 방식 모호**: `subscribe_realtime()` vs `get_candle_data(streaming=True)` 선택 필요
2. **Smart Router 자율성 강화**: 내부 빈도 분석으로 최적 채널 자동 선택
3. **WebSocket 장애 복구**: `realtime_only/snapshot_only` 요청 시 WebSocket 장애 대응 전략
4. **인터페이스 통합**: 단일 API로 일회성/실시간 모두 처리
5. **역할 분리 강화**: 각 레이어의 책임 명확화

### 🎯 명확한 역할 분리 정책 (3-Layer 아키텍처)

#### Layer 1: Smart Routing (가장 하위 - API 추상화)
- **API 추상화**: URL 구조 완전 은닉, 도메인 모델만 노출
- **자율적 채널 선택**: 내부 빈도 분석으로 REST ↔ WebSocket 자동 전환
- **WebSocket 장애 복구**: 3단계 Fallback (즉시 대응 → 배치 모사 → 시스템 모드 전환)
- **다중 데이터 타입**: get_candle_data(), get_ticker_data(), get_orderbook_data(), get_trade_data()
- **제한 준수**: 업비트 API 제한 내에서만 동작 (캔들 200개, 티커 100개 등)
- **WebSocket 관리**: 구독 생명주기, 재연결, 빈도 저조 시 자동 해제
- **순수 데이터 제공**: DB 저장 없이 데이터만 상위 레이어에 전달 ✅ **확정**

#### Layer 2: Market Data Coordinator (중간 레이어 - 요청 조율)
- **대용량 처리**: 200개 초과 캔들 요청을 분할하여 Smart Routing 다중 호출
- **다중 데이터 타입**: 각 데이터 타입별 분할 전략 (캔들, 티커, 호가창, 체결)
- **병렬 최적화**: 동시 요청 수 제어, 레이트 제한 관리
- **결과 통합**: 분할된 응답들을 하나로 합성 (데이터 타입별 로직)
- **Smart Router 연동**: 독립적인 Smart Router와 효율적 협력

#### Layer 3: Market Data Storage (상위 레이어 - 데이터 관리)
- **DB 관리**: 마켓 데이터 영속성, 스키마 관리 (데이터 타입별 테이블)
- **캐싱 전략**: 메모리/디스크 캐시, 만료 정책 (타입별 최적화)
- **증분 업데이트**: 기존 데이터 활용, 효율적 갱신
- **다중 API 인터페이스**: get_candle_data(), get_ticker_data(), get_orderbook_data(), get_trade_data()
- **사용 패턴 최적화**: 사용 사례별 요청 빈도 최적화 (실시간 차트=고빈도, 백테스트=저빈도)

### Phase 1: 기존 코드 검증 및 정리 🔄 **새로운 접근**
- [x] 1.1 현재 smart_routing/ 폴더 코드 품질 검증 ✅ **완료 (양호한 코드 품질 확인)**
- [x] 1.2 기존 도메인 모델과 실거래 데이터 요구사항 매핑 ✅ **완료 (스냅샷/실시간 구분 추가)**
- [x] 1.3 WebSocket 통합 지점 설계 (BatchWebSocketManager 연동) ✅ **완료 (Fallback 시스템 통합)**
- [x] 1.4 **아키텍처 결정**: Smart Router = 순수 데이터 제공자 (DB 저장 제외) ✅ **확정**

### Phase 2: 실시간 데이터 아키텍처 통합 🎯 **핵심** ✅ **완료**
- [x] 2.1 RealtimeDataCache 통합 (WebSocket → 메모리 → 상위 레이어 전달) ✅ **완료**
- [x] 2.2 캔들 완성 감지 및 이벤트 발생 (DB 저장은 Storage Layer 담당) ✅ **완료**
- [x] 2.3 하이브리드 데이터 제공 (메모리 우선, API 보조) ✅ **완료**
- [x] 2.4 실거래 성능 최적화 (< 1ms 메모리 접근) ✅ **완료**

### Phase 3: 자율적 최적화 완성 🚧 **기존 미완성 완료** ⏳ **진행 중**
- [x] 3.1 FrequencyAnalyzer 구현 (요청 패턴 분석) ❌ **계산 로직 오류 발견**
  - ❌ **계산 로직 문제**: 고정된 5분 윈도우로 나누어 잘못된 분당 요청수 계산
    - 시나리오: 30초 동안 6번 요청 = 실제 12 requests/minute
    - 현재 계산: `6 / 5 = 1.2 requests/minute` (잘못됨)
    - 원인: 실제 데이터 시간 범위 무시, 고정 윈도우(`time_window_minutes=5`) 사용
  - ❌ **수정 필요**: `analyze_request_pattern()` 메서드의 동적 시간 윈도우 계산
    1. 실제 요청 데이터의 시간 범위 계산 (최신 - 최오래된 요청)
    2. 최소/최대 윈도우 제한 적용 (30초~10분)
    3. 실제 시간 범위로 나누어 올바른 분당 요청수 계산
  - ✅ **고급 기능**: 피크 빈도 계산, 트렌드 분석, 시간대별 분포 등은 양호
- [-] 3.2 ChannelSelector 완성 (REST ↔ WebSocket 자동 전환) ⏳ **검증 중**
- [ ] 3.3 WebSocket 장애 복구 시스템 (3단계 Fallback 전략)
- [ ] 3.4 실거래 우선순위 처리 (Critical/High/Normal/Low)
- [ ] 3.5 시스템 부하 기반 적응적 라우팅

### Phase 4: 3-Layer 통합 및 검증 🔗 **통합**
- [ ] 4.1 Coordinator와의 연동 인터페이스 구현
- [ ] 4.2 Storage Layer 데이터 제공 인터페이스
- [ ] 4.3 실거래 시나리오 통합 테스트
- [ ] 4.4 테이블 구조 검증 (심볼별×타임프레임별 개별 저장)

### 확인된 교체 대상
- `unified_market_data_api.py`: 기존 SmartChannelRouter 사용 중
- `test_smart_routing_core.py`: 테스트 코드 교체 필요
- smart_routing 폴더: 완전히 새로 구현

## 🛠️ 폴더 구조 및 파일 설계

### 최종 폴더 구조 (Layer 1: Smart Routing)
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
│   ├── smart_data_router.py   # 자율적 스마트 라우터
│   ├── upbit_rest_provider.py # REST API 제공자
│   └── upbit_ws_provider.py   # WebSocket 제공자
├── strategies/                 # 라우팅 전략
│   ├── __init__.py
│   ├── frequency_analyzer.py  # 자율적 요청 패턴 분석
│   ├── channel_selector.py    # 자율적 채널 선택 로직
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
- `implementations/smart_data_router.py`: 자율적 채널 선택 라우터
- `strategies/frequency_analyzer.py`: 자율적 요청 패턴 분석 및 WebSocket 전환 로직

## 🎯 성공 기준
- ✅ **호환성 우선**: 기존 `IDataRouter` 인터페이스 그대로 구현하되, 내부에서 스마트 라우팅
- ✅ **완전한 추상화**: URL 구조 완전 은닉, 도메인 모델만 노출
- ✅ **자율적 최적화**: 내부 빈도 분석으로 REST ↔ WebSocket 자동 전환
- ✅ **WebSocket 장애 복구**: 3단계 Fallback으로 서비스 중단 없는 투명한 복구
- ✅ **스냅샷/실시간 구분**: `realtime_only/snapshot_only` 옵션으로 명확한 데이터 타입 요청
- ✅ **API 제한 준수**: 업비트 API 제한 내에서만 동작 (200개 초과 시 에러)

## 💡 작업 시 주의사항
### 설계 원칙
- **기존 인터페이스 유지**: `IDataRouter` 시그니처 변경 금지
- **내부 추상화**: Request 객체는 내부에서만 사용, 외부는 기존 파라미터 방식
- **점진적 확장**: REST API만으로 최소 동작 먼저, WebSocket은 나중에
- **자율적 동작**: 외부 간섭 없이 내부 분석으로 최적 채널 선택

### API 제한 처리 정책
```python
# Smart Routing API 제한 처리
def handle_candle_request(start_time, end_time, count, timeframe):
    """
    1. start_time이 주어지면 시작점으로 사용
    2. 업비트 API 최대 200개 제한 준수
    3. 200개 초과 예상 시 에러 반환 → Coordinator가 분할 처리
    4. 스크리너: 현재 시간부터 역순으로 N개 (최신 데이터 우선)
    5. 백테스트: start_time부터 순서대로 최대 200개
    """
    if start_time and end_time:
        estimated_count = calculate_expected_count(start_time, end_time, timeframe)
        if estimated_count > 200:
            raise DataRangeExceedsLimitException(
                f"요청 범위 초과: 예상 {estimated_count}개 > 최대 200개. "
                f"Coordinator에서 분할 요청 필요"
            )

    return process_within_api_limits(start_time, end_time, count)
```

## 🚀 개발 계획 (점진적 개선)

### 코드 재사용 전략
1. **기존 코드 보존**: smart_routing/ 폴더 그대로 활용
2. **점진적 개선**: 실거래 데이터 아키텍처만 추가/개선
3. **하위 호환성**: 기존 인터페이스 완전 보장

### 구현 목표 (개선된)
```python
# 기존 SmartDataRouter 확장
class SmartDataRouter(IDataRouter):
    def __init__(self):
        # 기존 코드 유지
        self.rest_provider = rest_provider

        # 새로 추가: 실시간 데이터 아키텍처
        self.realtime_cache = RealtimeDataCache()
        self.batch_websocket = BatchWebSocketManager()

    async def get_candle_data(self, symbol, timeframe, count=None, start_time=None, end_time=None):
        # 기존 로직 + 실시간 캐시 우선 조회
        # 하이브리드: 메모리 → DB → API 순서
        pass
```

### 테이블 구조 확정
```sql
-- 심볼별 × 타임프레임별 개별 테이블
candles_KRW_BTC_1m   (timestamp, ohlcv)
candles_KRW_BTC_5m   (timestamp, ohlcv)
candles_KRW_ETH_1m   (timestamp, ohlcv)
candles_KRW_ETH_1d   (timestamp, ohlcv)

-- 장점: 독립적 파편화 관리, 개별 최적화
-- 인덱스: (timestamp) 단일 인덱스로 충분
```

### 3-Layer 아키텍처 통합 구조
```
market_data_backbone/
├── __init__.py                 # 통합 API 엔트리포인트
├── market_data_api.py          # 메인 API - 전체 시스템 인터페이스
├── backbone_manager.py         # 3-Layer 조율 및 생명주기 관리
├── smart_routing/              # Layer 1: API 추상화
├── market_data_coordinator/    # Layer 2: 요청 조율
├── market_data_storage/        # Layer 3: 데이터 관리
└── utils/                      # 공통 유틸리티
```

---
**전략**: 점진적 개선 - 기존 코드 재사용 + 실거래 아키텍처 통합
**백업 불필요**: 현재 코드 상당한 품질, 그대로 활용
**다음 작업**: Phase 1 - 기존 코드 검증 및 실시간 데이터 통합 설계
**연관 태스크**:
- TASK_20250820_02 Market Data Coordinator 개발 (Layer 2)
- TASK_20250820_03 Market Data Storage 개발 (Layer 3)
- TASK_20250820_04 Market Data Backbone API 개발 (통합 API)
- 실시간 데이터 아키텍처 계획 (REALTIME_DATA_ARCHITECTURE_PLAN.md)
