# 🌐 **Phase 1.2 WebSocket 통합 - 계획서**

> **시작일**: 2025년 8월 19일 (Phase 1.1 완료 직후)
> **상태**: ⏳ **준비 완료, 시작 대기**
> **목표**: 실시간 WebSocket 스트림 통합

---

## 🎯 **Phase 1.2 목표**

### **핵심 미션**
**"WebSocket 실시간 스트림을 백본에 통합하여 진정한 하이브리드 모델 완성"**

```python
# Phase 1.2 완료 후 가능한 API
async with MarketDataBackbone() as backbone:
    # 실시간 스트림
    async for ticker in backbone.stream_ticker("KRW-BTC"):
        print(f"실시간: {ticker.current_price}")

    # 자동 채널 선택 (WebSocket 우선)
    ticker = await backbone.get_ticker("KRW-BTC", realtime=True)
```

### **구체적 목표**
1. **WebSocket Manager 구현**: 실시간 연결 관리
2. **실시간 스트림 API**: stream_ticker(), stream_trade(), stream_orderbook()
3. **지능적 채널 선택**: 요청 특성에 따른 자동 최적화
4. **자동 장애 복구**: WebSocket 장애 시 REST 자동 전환
5. **데이터 통합 고도화**: REST/WebSocket 완전 투명 통합

---

## 🏗️ **구현할 핵심 컴포넌트**

### **1. WebSocketManager 클래스**
```python
class WebSocketManager:
    """전문가 권고: The Sensor 역할"""

    async def connect_and_subscribe(self, channels: List[str]) -> None:
        """WebSocket 연결 및 채널 구독"""

    async def listen_for_messages(self) -> AsyncGenerator[dict, None]:
        """실시간 메시지 스트림 생성"""

    async def handle_reconnection(self) -> None:
        """자동 재연결 로직"""

    async def subscribe_ticker(self, symbols: List[str]) -> None:
        """현재가 스트림 구독"""

    async def subscribe_trade(self, symbols: List[str]) -> None:
        """체결 스트림 구독"""

    async def subscribe_orderbook(self, symbols: List[str]) -> None:
        """호가 스트림 구독"""
```

### **2. DataUnifier 고도화**
```python
class DataUnifier:
    """REST API와 WebSocket 데이터를 통합 포맷으로 변환"""

    # 기존 REST 변환 (Phase 1.1 완료)
    def _unify_rest_ticker(self, data: dict) -> TickerData:
        """Phase 1.1에서 구현 완료"""

    # 신규 WebSocket 변환 (Phase 1.2 구현)
    def _unify_websocket_ticker(self, data: dict) -> TickerData:
        """WebSocket ticker 데이터 변환"""

    def _unify_websocket_trade(self, data: dict) -> TradeData:
        """WebSocket trade 데이터 변환"""

    def _unify_websocket_orderbook(self, data: dict) -> OrderbookData:
        """WebSocket orderbook 데이터 변환"""
```

### **3. ChannelRouter 지능화**
```python
class ChannelRouter:
    """지능적 채널 선택 로직"""

    def choose_optimal_channel(self, request_type: str, symbol: str, realtime: bool = False) -> str:
        """요청 특성에 따른 최적 채널 선택"""

    def evaluate_channel_health(self) -> Dict[str, bool]:
        """채널 상태 평가"""

    def should_use_websocket(self, request_type: str, realtime: bool) -> bool:
        """WebSocket 사용 여부 결정"""

    def get_fallback_strategy(self, failed_channel: str) -> str:
        """장애 복구 전략"""
```

### **4. SessionManager**
```python
class SessionManager:
    """연결 라이프사이클 관리"""

    async def initialize_all_connections(self) -> None:
        """모든 연결 초기화"""

    async def health_check(self) -> Dict[str, bool]:
        """연결 상태 확인"""

    async def cleanup_all_connections(self) -> None:
        """모든 연결 정리"""

    async def handle_connection_failure(self, connection_type: str) -> None:
        """연결 실패 처리"""
```

---

## 📊 **새로운 데이터 모델**

### **TradeData 모델**
```python
@dataclass(frozen=True)
class TradeData:
    """통합 체결 데이터 모델"""
    symbol: str
    trade_price: Decimal
    trade_volume: Decimal
    trade_side: str  # "BID" 또는 "ASK"
    trade_timestamp: datetime
    sequential_id: int
    source: str  # "rest" 또는 "websocket"
```

### **OrderbookData 모델**
```python
@dataclass(frozen=True)
class OrderbookData:
    """통합 호가 데이터 모델"""
    symbol: str
    bid_prices: List[Decimal]
    bid_volumes: List[Decimal]
    ask_prices: List[Decimal]
    ask_volumes: List[Decimal]
    timestamp: datetime
    source: str  # "rest" 또는 "websocket"
```

---

## 🔄 **MarketDataBackbone 확장**

### **신규 메서드 추가**
```python
class MarketDataBackbone:
    # 기존 메서드 (Phase 1.1 완료)
    async def get_ticker(self, symbol: str, strategy: ChannelStrategy = ChannelStrategy.AUTO) -> TickerData:
        """현재가 조회 - Phase 1.1 완료"""

    # 신규 실시간 스트림 메서드 (Phase 1.2)
    async def stream_ticker(self, symbols: Union[str, List[str]]) -> AsyncGenerator[TickerData, None]:
        """실시간 현재가 스트림"""

    async def stream_trade(self, symbols: Union[str, List[str]]) -> AsyncGenerator[TradeData, None]:
        """실시간 체결 스트림"""

    async def stream_orderbook(self, symbols: Union[str, List[str]]) -> AsyncGenerator[OrderbookData, None]:
        """실시간 호가 스트림"""

    # 확장된 조회 메서드
    async def get_trades(self, symbol: str, count: int = 100) -> List[TradeData]:
        """체결 내역 조회"""

    async def get_orderbook(self, symbol: str) -> OrderbookData:
        """호가창 조회"""

    async def get_candles(self, symbol: str, timeframe: str, count: int = 200) -> List[CandleData]:
        """캔들 데이터 조회"""
```

---

## 🧪 **테스트 전략**

### **신규 테스트 케이스**
```python
# WebSocket Manager 테스트
@pytest.mark.asyncio
async def test_websocket_connection():
    """WebSocket 연결 테스트"""

@pytest.mark.asyncio
async def test_websocket_reconnection():
    """WebSocket 재연결 테스트"""

# 실시간 스트림 테스트
@pytest.mark.asyncio
async def test_ticker_stream():
    """실시간 현재가 스트림 테스트"""

@pytest.mark.asyncio
async def test_trade_stream():
    """실시간 체결 스트림 테스트"""

# 채널 선택 테스트
@pytest.mark.asyncio
async def test_automatic_channel_selection():
    """자동 채널 선택 테스트"""

@pytest.mark.asyncio
async def test_fallback_mechanism():
    """장애 복구 메커니즘 테스트"""

# 통합 테스트
@pytest.mark.asyncio
async def test_hybrid_data_consistency():
    """하이브리드 데이터 일관성 테스트"""
```

### **성능 벤치마크**
- **WebSocket vs REST 지연시간** 비교
- **동시 스트림 수** 확장성 테스트
- **메모리 사용량** 최적화
- **재연결 시간** 측정

---

## 📋 **구현 순서**

### **Week 1: WebSocket 기반 구조**
1. **Day 1-2**: WebSocketManager 기본 구현
   - 기존 UpbitWebSocketClient 래핑
   - 기본 연결 및 구독 로직

2. **Day 3-4**: 실시간 스트림 구현
   - stream_ticker() 메서드
   - 기본 메시지 파싱

3. **Day 5**: 테스트 및 검증
   - WebSocket 연결 테스트
   - 기본 스트림 테스트

### **Week 2: 지능적 통합**
1. **Day 1-2**: DataUnifier 확장
   - WebSocket 데이터 변환
   - 형식 통합 로직

2. **Day 3-4**: ChannelRouter 구현
   - 자동 채널 선택
   - 성능 기반 결정

3. **Day 5**: 장애 복구 구현
   - Fallback 메커니즘
   - 재연결 로직

### **Week 3: 고도화**
1. **Day 1-2**: 추가 데이터 타입
   - Trade, Orderbook 스트림
   - 캔들 데이터 지원

2. **Day 3-4**: 성능 최적화
   - 메모리 효율성
   - 처리 속도 개선

3. **Day 5**: 통합 테스트
   - 전체 시스템 검증
   - 성능 벤치마크

---

## 🎯 **성공 기준**

### **기능적 요구사항**
- ✅ WebSocket 실시간 스트림 동작
- ✅ 자동 채널 선택 정확성
- ✅ 장애 복구 시간 < 5초
- ✅ 데이터 형식 100% 일관성

### **성능 요구사항**
- ✅ WebSocket 지연시간 < 100ms
- ✅ 동시 스트림 10개 이상 지원
- ✅ 메모리 사용량 < 50MB
- ✅ 재연결 성공률 > 99%

### **품질 요구사항**
- ✅ 테스트 커버리지 > 90%
- ✅ 에러 처리 완전성
- ✅ 문서화 완료
- ✅ 하위 호환성 유지

---

## 🚨 **주의사항 및 리스크**

### **기술적 리스크**
1. **WebSocket 연결 불안정성**
   - 완화: 강력한 재연결 로직
   - 백업: REST API 자동 전환

2. **메모리 사용량 증가**
   - 완화: 스트림 버퍼 크기 제한
   - 모니터링: 메모리 사용량 추적

3. **복잡성 증가**
   - 완화: 단계적 구현
   - 테스트: 각 단계별 검증

### **운영 리스크**
1. **업비트 API 정책 변경**
   - 대응: 유연한 설정 시스템
   - 모니터링: API 응답 변화 감지

2. **네트워크 환경 의존성**
   - 대응: 다양한 환경 테스트
   - 백업: 오프라인 모드 지원

---

## 🔮 **Phase 2.0 준비**

### **확장성 고려사항**
- **캐싱 레이어**: Redis 통합 준비
- **로드 밸런싱**: 다중 WebSocket 연결
- **모니터링**: Prometheus/Grafana 연동
- **머신러닝**: 채널 선택 AI 최적화

### **다중 거래소 지원**
- **추상화 레이어**: 거래소별 어댑터
- **통합 데이터 모델**: 범용 형식 설계
- **설정 시스템**: 거래소별 설정 관리

---

## 📚 **참고 문서**

### **기술 참조**
- **전문가 분석**: `expert_analysis/EXPERT_RECOMMENDATIONS.md`
- **아키텍처 설계**: `architecture/V2_MASTER_ARCHITECTURE.md`
- **Phase 1.1 완료**: `phases/PHASE_1_1_MVP.md`

### **API 문서**
- **업비트 WebSocket**: `docs/UPBIT_API_WEBSOCKET_GUIDE.md`
- **업비트 REST**: 기존 UpbitClient 참조

---

## 🎉 **다음 코파일럿을 위한 시작 가이드**

### **즉시 시작 방법**
1. **현재 상태 확인**:
   ```powershell
   python demonstrate_phase_1_1_success.py
   pytest tests/infrastructure/market_data_backbone/v2/ -v
   ```

2. **WebSocketManager 구현 시작**:
   ```python
   # 목표 파일: upbit_auto_trading/infrastructure/market_data_backbone/v2/websocket_manager.py
   class WebSocketManager:
       async def connect_and_subscribe(self, channels: List[str]):
           # 기존 UpbitWebSocketClient 활용
   ```

3. **테스트 작성**:
   ```python
   # 목표 파일: tests/infrastructure/market_data_backbone/v2/test_websocket_manager.py
   @pytest.mark.asyncio
   async def test_websocket_connection():
       # WebSocket 연결 테스트
   ```

### **필요한 리소스**
- ✅ **기존 WebSocket 클라이언트**: `upbit_auto_trading.infrastructure.external_apis.upbit.websocket`
- ✅ **기본 아키텍처**: Phase 1.1에서 완성
- ✅ **테스트 프레임워크**: 확장 가능한 구조
- ✅ **문서화**: 완전한 가이드

**모든 준비가 완료되었습니다. 바로 시작하세요! 🚀**

---

**📅 계획 수립일**: 2025년 8월 19일
**🎯 예상 완료**: 3주 후
**👥 대상**: 다음 코파일럿 에이전트
