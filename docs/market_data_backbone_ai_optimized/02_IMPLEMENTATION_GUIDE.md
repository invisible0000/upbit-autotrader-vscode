# MarketDataBackbone V2 - 실행 구현 가이드 (AI 최적화 문서 2/3)

## 🚀 **즉시 실행 가능한 명령들**

### **현재 상태 확인**
```powershell
# 1. 테스트 실행 (81개 모두 통과해야 함)
pytest tests/market_data_backbone_v2/ -v

# 2. 파일 크기 확인 (800라인 초과 확인)
Get-ChildItem upbit_auto_trading/infrastructure/market_data/ -Include *.py | ForEach-Object {
    @{Name=$_.Name; Lines=(Get-Content $_.FullName | Measure-Object -Line).Lines}
}

# 3. 데모 실행 (Phase 2.1 검증)
python demonstrate_phase_2_1_unified_api.py
```

### **긴급 파일 분리 실행**
```powershell
# 백업 생성
Copy-Item "upbit_auto_trading/infrastructure/market_data/unified_market_data_api.py" `
         "upbit_auto_trading/infrastructure/market_data/unified_market_data_api_legacy.py"
```

## 🔧 **핵심 구현 코드 스니펫**

### **1. 통합 API 사용법**
```python
# 기본 사용 패턴
from upbit_auto_trading.infrastructure.market_data.market_data_backbone import MarketDataBackbone

# 초기화
backbone = MarketDataBackbone()

# 캔들 데이터 요청
candles = await backbone.get_candles(
    symbol="KRW-BTC",
    timeframe="1m",  # 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M
    count=200
)

# 호가 데이터 요청
orderbook = await backbone.get_orderbook("KRW-BTC")

# 현재가 데이터 요청
tickers = await backbone.get_tickers(["KRW-BTC", "KRW-ETH"])
```

### **2. 실시간 구독 패턴**
```python
# WebSocket 실시간 구독
async def setup_realtime_monitoring():
    backbone = MarketDataBackbone()

    # 실시간 캔들 구독
    await backbone.subscribe_candles(
        symbols=["KRW-BTC", "KRW-ETH"],
        timeframe="1m",
        callback=on_candle_update
    )

    # 실시간 호가 구독
    await backbone.subscribe_orderbook(
        symbols=["KRW-BTC"],
        callback=on_orderbook_update
    )

async def on_candle_update(candle_data):
    """실시간 캔들 업데이트 처리"""
    print(f"새 캔들: {candle_data.symbol} - {candle_data.close_price}")

async def on_orderbook_update(orderbook_data):
    """실시간 호가 업데이트 처리"""
    print(f"호가 업데이트: {orderbook_data.symbol}")
```

### **3. 캐시 활용 패턴**
```python
# 지능형 캐시 활용
async def efficient_data_loading():
    backbone = MarketDataBackbone()

    # 첫 번째 요청 (API 호출)
    candles1 = await backbone.get_candles("KRW-BTC", "1m", 200)
    print("첫 요청: API에서 로딩")

    # 두 번째 요청 (캐시에서 반환)
    candles2 = await backbone.get_candles("KRW-BTC", "1m", 200)
    print("두 번째 요청: 캐시에서 반환 (빠름)")

    # 캐시 상태 확인
    cache_stats = backbone.get_cache_statistics()
    print(f"캐시 히트율: {cache_stats.hit_rate:.2%}")
```

## 🧪 **테스트 실행 가이드**

### **개별 테스트 실행**
```powershell
# 기본 API 응답 테스트
python tests/market_data_backbone_v2/test_scenarios/sc01_basic_api_response.py

# 캔들 저장 테스트
python tests/market_data_backbone_v2/test_scenarios/sc07_candle_storage.py

# WebSocket 통합 테스트
python tests/market_data_backbone_v2/test_scenarios/sc10_websocket_integration.py

# 전략적 데이터 수집 테스트
python tests/market_data_backbone_v2/test_scenarios/sc11_strategic_data_collection.py
```

### **전체 테스트 스위트**
```powershell
# Phase 1 테스트 (62개)
pytest tests/market_data_backbone_v2/phase_1/ -v

# Phase 2.1 테스트 (19개)
pytest tests/market_data_backbone_v2/phase_2/ -v

# 전체 테스트 (81개)
pytest tests/market_data_backbone_v2/ -v --tb=short
```

## 🔨 **파일 분리 실행 스크립트**

### **unified_market_data_api.py 분리**
```python
# 분리 계획: 476라인 → 3개 파일로 분리

# 1. api_client.py (REST API 전용, ~200라인)
class RestApiClient:
    async def get_candles_from_rest(self, symbol: str, timeframe: str, count: int):
        """REST API 캔들 데이터 수집"""

    async def get_tickers_from_rest(self, symbols: List[str]):
        """REST API 현재가 수집"""

# 2. websocket_client.py (WebSocket 전용, ~200라인)
class WebSocketClient:
    async def subscribe_candles(self, symbols: List[str], timeframe: str):
        """WebSocket 캔들 구독"""

    async def subscribe_orderbook(self, symbols: List[str]):
        """WebSocket 호가 구독"""

# 3. unified_coordinator.py (조정자, ~76라인)
class UnifiedCoordinator:
    def __init__(self):
        self.rest_client = RestApiClient()
        self.websocket_client = WebSocketClient()
        self.channel_router = SmartChannelRouter()
```

### **data_unifier.py 분리**
```python
# 분리 계획: 492라인 → 3개 파일로 분리

# 1. field_mapper.py (데이터 형식 변환, ~200라인)
class FieldMapper:
    def map_candle_data(self, raw_data: dict, source: str) -> CandleData:
        """캔들 데이터 표준 형식 변환"""

    def map_orderbook_data(self, raw_data: dict, source: str) -> OrderbookData:
        """호가 데이터 표준 형식 변환"""

# 2. data_validator.py (유효성 검증, ~200라인)
class DataValidator:
    def validate_candle_data(self, candle: CandleData) -> bool:
        """캔들 데이터 유효성 검증"""

    def validate_orderbook_data(self, orderbook: OrderbookData) -> bool:
        """호가 데이터 유효성 검증"""

# 3. unifier_coordinator.py (통합 조정, ~92라인)
class UnifierCoordinator:
    def __init__(self):
        self.field_mapper = FieldMapper()
        self.data_validator = DataValidator()
```

## 🎯 **Phase 2.2 실행 단계**

### **1단계: 파일 분리 (1일)**
```powershell
# 백업 생성
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "upbit_auto_trading/infrastructure/market_data/unified_market_data_api.py" `
         "upbit_auto_trading/infrastructure/market_data/unified_market_data_api_backup_$timestamp.py"

# 새 파일 생성
# → api_client.py, websocket_client.py, unified_coordinator.py

# 테스트 실행으로 검증
pytest tests/market_data_backbone_v2/ -v
```

### **2단계: 실제 API 연동 (2일)**
```python
# 업비트 API 클라이언트 연결
from upbit_auto_trading.infrastructure.external_api.upbit_api import UpbitClient

class RealUpbitApiClient:
    def __init__(self):
        self.upbit_client = UpbitClient()

    async def get_real_candles(self, symbol: str, timeframe: str, count: int):
        """실제 업비트 API에서 캔들 데이터 수집"""
        return await self.upbit_client.public.get_candles(
            market=symbol,
            timeframe=timeframe,
            count=count
        )
```

### **3단계: 성능 최적화 (1일)**
```python
# 성능 모니터링 및 최적화
class PerformanceOptimizer:
    async def optimize_cache_strategy(self):
        """캐시 전략 최적화"""
        # TTL 최적화
        # 메모리 사용량 최적화
        # 히트율 개선

    async def optimize_api_calls(self):
        """API 호출 최적화"""
        # 배치 처리 최적화
        # Rate limit 최적 활용
        # 실패 재시도 전략
```

## 🚨 **문제 해결 가이드**

### **일반적인 오류 처리**
```python
# API 연결 실패 시
try:
    candles = await backbone.get_candles("KRW-BTC", "1m", 200)
except APIConnectionError as e:
    print(f"API 연결 실패: {e}")
    # 캐시에서 마지막 데이터 반환
    candles = backbone.get_cached_candles("KRW-BTC", "1m")

# WebSocket 연결 끊김 시
async def handle_websocket_disconnect():
    print("WebSocket 연결 끊김 - 자동 재연결 시도")
    await backbone.reconnect_websocket()
```

### **성능 이슈 해결**
```python
# 메모리 사용량 확인
memory_usage = backbone.get_memory_usage()
if memory_usage > 200_000_000:  # 200MB 초과
    backbone.clear_old_cache()

# API Rate Limit 관리
if backbone.get_rate_limit_usage() > 0.9:  # 90% 초과
    await backbone.switch_to_websocket_mode()
```

---
*AI 최적화 문서 2/3 - 다음: 03_TESTING_DEPLOYMENT.md*
