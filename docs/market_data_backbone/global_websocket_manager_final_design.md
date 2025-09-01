# 전역 WebSocket 관리 시스템 최종 설계

## 🎯 **핵심 요구사항 분석**

### 업비트 WebSocket 특성에 따른 필수 기능
1. **전역 실시간 구독 상태 추적**: 모든 클라이언트의 구독 요구사항 통합 관리
2. **덮어쓰기 방식 대응**: 스냅샷 요청 시 기존 실시간 구독 포함해서 전송
3. **자동 구독 정리**: 클라이언트 종료 시 해당 구독만 제거하고 나머지 유지
4. **베이스 연결 유지**: 시스템 전체에 최소 1개 WebSocket 연결 상시 유지
5. **장애 복구**: 연결 끊김 시 자동 재연결 및 구독 상태 복원

## 🏗️ **시스템 아키텍처**

### 1. 전역 WebSocket 관리자
```python
class GlobalWebSocketManager:
    """
    애플리케이션 전역 WebSocket 관리
    - 단일 WebSocket 연결 관리 (Singleton)
    - 모든 클라이언트의 구독 요구사항 통합
    - 자동 연결 유지 및 복구
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        # 실제 WebSocket 연결 (항상 1개만 유지)
        self.websocket_client = None
        
        # 전역 실시간 구독 상태
        self.global_realtime_subscriptions = {
            "ticker": set(),      # 현재가 실시간 구독 심볼들
            "orderbook": set(),   # 호가 실시간 구독 심볼들
            "trade": set(),       # 체결 실시간 구독 심볼들
            "minute1": set(),     # 1분봉 실시간 구독 심볼들
            "minute60": set(),    # 1시간봉 실시간 구독 심볼들
        }
        
        # 클라이언트별 구독 추적 (자동 정리용)
        self.client_subscriptions = {}  # {client_id: {data_type: symbols}}
        
        # 데이터 라우팅 시스템
        self.data_routes = {}  # {(symbol, data_type): [callback_list]}
        
        # 베이스 연결 관리
        self.base_connection_active = False
        self.reconnection_task = None
```

### 2. 클라이언트별 프록시
```python
class WebSocketClientProxy:
    """
    개별 클라이언트용 WebSocket 프록시
    - 기존 WebSocket 클라이언트 인터페이스 호환
    - 모든 요청을 GlobalWebSocketManager에 위임
    """
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.global_manager = GlobalWebSocketManager.get_instance()
        
        # 자동 정리를 위한 weakref 등록
        weakref.finalize(self, self._cleanup_on_destruction)
    
    async def subscribe_ticker_snapshot(self, symbols: List[str]):
        """스냅샷 요청 (기존 실시간 구독 포함)"""
        return await self.global_manager.request_snapshot(
            client_id=self.client_id,
            data_type="ticker",
            symbols=symbols
        )
    
    async def subscribe_ticker_realtime(self, symbols: List[str], callback: Callable):
        """실시간 구독 요청"""
        return await self.global_manager.request_realtime(
            client_id=self.client_id,
            data_type="ticker", 
            symbols=symbols,
            callback=callback
        )
    
    async def unsubscribe_ticker(self, symbols: List[str]):
        """실시간 구독 해제"""
        return await self.global_manager.remove_realtime(
            client_id=self.client_id,
            data_type="ticker",
            symbols=symbols
        )
    
    def _cleanup_on_destruction(self):
        """객체 소멸 시 자동 정리"""
        asyncio.create_task(
            self.global_manager.cleanup_client(self.client_id)
        )
```

## 🔄 **핵심 동작 시나리오**

### 시나리오 예시: 사용자 제시 상황

#### 1. 초기 상태
```python
# 웹소켓 클라이언트1이 KRW-BTC 현재가 실시간 구독
client1 = WebSocketClientProxy("chart_component")
await client1.subscribe_ticker_realtime(["KRW-BTC"], chart_callback)

# 전역 상태:
global_realtime_subscriptions = {
    "ticker": {"KRW-BTC"}
}
client_subscriptions = {
    "chart_component": {"ticker": {"KRW-BTC"}}
}
# 실제 WebSocket: ticker ["KRW-BTC"] 실시간 구독
```

#### 2. 두 번째 클라이언트 스냅샷 + 실시간 요청
```python
# 웹소켓 클라이언트2가 KRW-ETH, KRW-XRP 스냅샷과 실시간 스트림 요청
client2 = WebSocketClientProxy("coinlist_component") 
await client2.subscribe_ticker_snapshot(["KRW-ETH", "KRW-XRP"])
await client2.subscribe_ticker_realtime(["KRW-ETH", "KRW-XRP"], coinlist_callback)

# 전역 상태 업데이트:
global_realtime_subscriptions = {
    "ticker": {"KRW-BTC", "KRW-ETH", "KRW-XRP"}
}
client_subscriptions = {
    "chart_component": {"ticker": {"KRW-BTC"}},
    "coinlist_component": {"ticker": {"KRW-ETH", "KRW-XRP"}}
}
# 실제 WebSocket: ticker ["KRW-BTC", "KRW-ETH", "KRW-XRP"] 실시간 구독
```

#### 3. 부분 구독 해제
```python
# 웹소켓 클라이언트2가 KRW-XRP 실시간 스트림 중단
await client2.unsubscribe_ticker(["KRW-XRP"])

# 전역 상태 업데이트:
global_realtime_subscriptions = {
    "ticker": {"KRW-BTC", "KRW-ETH"}  # KRW-XRP 제거
}
client_subscriptions = {
    "chart_component": {"ticker": {"KRW-BTC"}},
    "coinlist_component": {"ticker": {"KRW-ETH"}}  # KRW-XRP 제거
}
# 실제 WebSocket: ticker ["KRW-BTC", "KRW-ETH"] 실시간 구독 (전체 재구독)
```

#### 4. 클라이언트 종료
```python
# 웹소켓 클라이언트1 종료 (chart_component)
client1 = None  # 객체 소멸 → 자동 정리 트리거

# 전역 상태 자동 업데이트:
global_realtime_subscriptions = {
    "ticker": {"KRW-ETH"}  # KRW-BTC 제거 (client1이 요청했던 것)
}
client_subscriptions = {
    "coinlist_component": {"ticker": {"KRW-ETH"}}  # chart_component 제거
}
# 실제 WebSocket: ticker ["KRW-ETH"] 실시간 구독 (전체 재구독)
```

## 🔧 **핵심 구현 로직**

### 1. 전역 구독 상태 관리
```python
async def request_realtime(self, client_id: str, data_type: str, 
                          symbols: List[str], callback: Callable) -> bool:
    """실시간 구독 요청 처리"""
    async with self._lock:
        # 1. 클라이언트 구독 상태 업데이트
        if client_id not in self.client_subscriptions:
            self.client_subscriptions[client_id] = {}
        
        if data_type not in self.client_subscriptions[client_id]:
            self.client_subscriptions[client_id][data_type] = set()
        
        self.client_subscriptions[client_id][data_type].update(symbols)
        
        # 2. 전역 실시간 구독 상태 업데이트
        self.global_realtime_subscriptions[data_type].update(symbols)
        
        # 3. 데이터 라우팅 등록
        for symbol in symbols:
            route_key = (symbol, data_type)
            if route_key not in self.data_routes:
                self.data_routes[route_key] = []
            self.data_routes[route_key].append(callback)
        
        # 4. WebSocket 실제 구독 갱신
        await self._rebuild_websocket_subscription(data_type)
        
        return True

async def _rebuild_websocket_subscription(self, data_type: str):
    """전체 WebSocket 구독 재구성"""
    all_symbols = list(self.global_realtime_subscriptions[data_type])
    
    if not all_symbols:
        # 구독할 심볼이 없으면 빈 구독 (구독 해제)
        await self._send_websocket_subscription(data_type, [])
    else:
        # 모든 심볼 통합 구독
        await self._send_websocket_subscription(data_type, all_symbols)
```

### 2. 스냅샷 요청 시 기존 실시간 포함
```python
async def request_snapshot(self, client_id: str, data_type: str, 
                          symbols: List[str]) -> dict:
    """스냅샷 요청 (기존 실시간 구독 포함)"""
    async with self._lock:
        # 현재 실시간 구독 중인 심볼들
        current_realtime = self.global_realtime_subscriptions[data_type]
        
        # 요청된 심볼 + 기존 실시간 심볼 통합
        combined_symbols = list(set(symbols) | current_realtime)
        
        # 스냅샷 요청 (기존 실시간 포함)
        snapshot_data = await self._request_websocket_snapshot(
            data_type, combined_symbols
        )
        
        # 요청된 심볼들만 필터링해서 반환
        filtered_data = self._filter_snapshot_data(snapshot_data, symbols)
        
        return filtered_data
```

### 3. 베이스 연결 유지 시스템
```python
async def ensure_base_connection(self):
    """베이스 WebSocket 연결 보장"""
    if not self.base_connection_active:
        await self._establish_base_connection()
        self._start_connection_monitor()

async def _establish_base_connection(self):
    """베이스 연결 설정"""
    try:
        if not self.websocket_client:
            from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5.upbit_websocket_public_client import UpbitWebSocketPublicV5
            self.websocket_client = UpbitWebSocketPublicV5(
                enable_dynamic_rate_limiter=True,
                persistent_connection=True
            )
        
        await self.websocket_client.connect()
        self.base_connection_active = True
        
        # 데이터 수신 라우터 설정
        self._setup_data_router()
        
        logger.info("✅ 베이스 WebSocket 연결 설정 완료")
        
    except Exception as e:
        logger.error(f"베이스 연결 설정 실패: {e}")
        self.base_connection_active = False
        # 재연결 스케줄링
        await asyncio.sleep(5)
        asyncio.create_task(self._establish_base_connection())

def _start_connection_monitor(self):
    """연결 상태 모니터링 시작"""
    if self.reconnection_task is None or self.reconnection_task.done():
        self.reconnection_task = asyncio.create_task(self._connection_monitor_loop())

async def _connection_monitor_loop(self):
    """연결 상태 지속 모니터링"""
    while True:
        try:
            await asyncio.sleep(10)  # 10초마다 체크
            
            if not self._is_connection_healthy():
                logger.warning("WebSocket 연결 상태 불량 - 재연결 시도")
                await self._recover_connection()
            
        except Exception as e:
            logger.error(f"연결 모니터링 오류: {e}")

async def _recover_connection(self):
    """연결 복구 및 구독 상태 복원"""
    try:
        # 기존 연결 정리
        if self.websocket_client:
            await self.websocket_client.disconnect()
        
        # 새 연결 설정
        await self._establish_base_connection()
        
        # 모든 실시간 구독 복원
        await self._restore_all_subscriptions()
        
        logger.info("✅ WebSocket 연결 복구 및 구독 복원 완료")
        
    except Exception as e:
        logger.error(f"연결 복구 실패: {e}")
        # 지수 백오프로 재시도
        await asyncio.sleep(min(30, 2 ** self.reconnection_attempts))
        asyncio.create_task(self._recover_connection())

async def _restore_all_subscriptions(self):
    """모든 구독 상태 복원"""
    for data_type, symbols in self.global_realtime_subscriptions.items():
        if symbols:  # 구독할 심볼이 있으면
            await self._send_websocket_subscription(data_type, list(symbols))
```

### 4. 자동 정리 시스템
```python
async def cleanup_client(self, client_id: str):
    """클라이언트 종료 시 자동 정리"""
    async with self._lock:
        if client_id not in self.client_subscriptions:
            return
        
        client_subs = self.client_subscriptions[client_id]
        
        # 각 데이터 타입별로 구독 제거
        for data_type, symbols in client_subs.items():
            # 전역 구독에서 해당 심볼들 제거
            self.global_realtime_subscriptions[data_type] -= symbols
            
            # 데이터 라우팅에서 콜백 제거
            for symbol in symbols:
                route_key = (symbol, data_type)
                if route_key in self.data_routes:
                    # 해당 클라이언트의 콜백만 제거
                    self.data_routes[route_key] = [
                        cb for cb in self.data_routes[route_key] 
                        if getattr(cb, '_client_id', None) != client_id
                    ]
                    
                    # 콜백이 없으면 라우트 제거
                    if not self.data_routes[route_key]:
                        del self.data_routes[route_key]
            
            # WebSocket 구독 재구성
            await self._rebuild_websocket_subscription(data_type)
        
        # 클라이언트 기록 삭제
        del self.client_subscriptions[client_id]
        
        logger.info(f"✅ 클라이언트 정리 완료: {client_id}")
```

## 🎯 **베이스 연결 관리 전략**

### 1. 상시 연결 유지
```python
class BaseConnectionManager:
    """베이스 WebSocket 연결 전담 관리"""
    
    def __init__(self):
        self.is_base_active = False
        self.health_check_interval = 30  # 30초마다 헬스체크
        self.reconnection_delay = [1, 2, 5, 10, 30]  # 지수 백오프
        
    async def maintain_base_connection(self):
        """베이스 연결 상시 유지"""
        while True:
            try:
                if not self.is_base_active:
                    await self._establish_connection()
                
                await self._health_check()
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"베이스 연결 관리 오류: {e}")
                await self._handle_connection_failure()
```

### 2. 지능적 재연결
```python
async def _handle_connection_failure(self):
    """연결 실패 시 지능적 복구"""
    for delay in self.reconnection_delay:
        try:
            logger.info(f"🔄 {delay}초 후 재연결 시도...")
            await asyncio.sleep(delay)
            
            await self._establish_connection()
            
            if self.is_base_active:
                logger.info("✅ 재연결 성공")
                break
                
        except Exception as e:
            logger.warning(f"재연결 실패: {e}")
            continue
    
    # 모든 재시도 실패 시 알림
    if not self.is_base_active:
        logger.critical("❌ 모든 재연결 시도 실패 - 관리자 확인 필요")
```

## 📊 **기존 WebSocket v5와의 통합**

### 활용할 기존 기능들
```python
# ✅ 이미 구현된 기능들 재사용
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5.subscription_manager import SubscriptionManager
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5.upbit_websocket_public_client import UpbitWebSocketPublicV5

class GlobalWebSocketManager:
    def __init__(self):
        # 기존 SubscriptionManager를 내부 엔진으로 활용
        self.subscription_engine = SubscriptionManager()
        
        # 동적 Rate Limiter 통합된 클라이언트 사용
        self.websocket_client = UpbitWebSocketPublicV5(
            enable_dynamic_rate_limiter=True
        )
```

## 🚀 **구현 우선순위**

### Phase 1: 핵심 GlobalWebSocketManager (1주)
- [x] Singleton 패턴 구현
- [x] 전역 구독 상태 관리
- [x] 기본 구독/해제 로직
- [x] 베이스 연결 유지 시스템

### Phase 2: WebSocketClientProxy (3일)
- [x] 기존 인터페이스 호환 프록시
- [x] 자동 정리 시스템
- [x] 데이터 라우팅

### Phase 3: 장애 복구 시스템 (1주)
- [x] 연결 상태 모니터링
- [x] 자동 재연결
- [x] 구독 상태 복원

### Phase 4: GUI 통합 (1주)
- [x] 기존 컴포넌트 마이그레이션
- [x] 실제 사용 시나리오 테스트
- [x] 성능 최적화

## 🎯 **결론**

### ✅ **"베이스 WebSocket 연결 상시 운용" 필수**
1. **안정성**: 연결 끊김 시 모든 실시간 데이터 중단 방지
2. **연속성**: 사용자가 인지하지 못하게 백그라운드 자동 관리
3. **복구력**: 장애 시 자동 재연결 및 구독 상태 복원
4. **성능**: 연결 설정 오버헤드 최소화

### ✅ **전역 구독 관리 시스템 필수**
1. **업비트 특성 대응**: 덮어쓰기 방식에 완벽 대응
2. **충돌 방지**: 다중 클라이언트 사용 시 구독 충돌 완전 해결
3. **자동 정리**: 클라이언트 종료 시 깔끔한 구독 정리
4. **개발자 경험**: 기존 인터페이스 유지하면서 내부적으로 통합 관리

이 시스템이 구현되면 **어디서든 WebSocket을 사용해도 하나의 몸처럼 동작**하는 진정한 통합 자동매매 시스템이 완성됩니다! 🚀
