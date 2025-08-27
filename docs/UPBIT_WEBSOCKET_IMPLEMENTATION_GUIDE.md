# 🔧 업비트 WebSocket 구독 시스템 구현 가이드

> **보완 문서**: UPBIT_WEBSOCKET_SUBSCRIPTION_SYSTEM_ARCHITECTURE.md
> **대상 독자**: 개발자, 아키텍트
> **난이도**: 고급

---

## 🎯 구현 핵심 요약

### 📋 **주요 클래스 및 메서드**

```python
# 1. 구독 관리자 초기화
subscription_manager = UpbitWebSocketSubscriptionManager(
    max_tickets=5,           # 업비트 권장 최대값
    enable_ticket_reuse=True # 티켓 재사용 활성화
)

# 2. 통합 구독 추가
ticket_id = subscription_manager.add_unified_subscription(
    data_type="ticker",      # 구독 타입
    symbols=["KRW-BTC"],     # 심볼 목록
    **kwargs                 # 추가 옵션
)

# 3. 구독 메시지 생성
raw_message = subscription_manager.get_resubscribe_message_by_ticket(ticket_id)
# 결과: [{'ticket': 'unified-xxx'}, {'type': 'ticker', 'codes': ['KRW-BTC']}, {'format': 'DEFAULT'}]

# 4. WebSocket 전송
await websocket.send(json.dumps(raw_message))
```

---

## 🏗️ 클래스별 상세 구현

### 🎫 **1. UnifiedSubscription**

```python
class UnifiedSubscription:
    """단일 티켓으로 여러 구독 타입 관리"""

    def __init__(self, ticket: str):
        self.ticket = ticket
        self.types: Dict[str, Dict] = {}  # 타입별 구독 설정
        self.symbols: Set[str] = set()    # 전체 심볼 집합
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self.message_count = 0

    def add_subscription_type(self, data_type: str, symbols: List[str], **kwargs):
        """새로운 구독 타입 추가"""

        # 캔들 타입 정규화 (중요!)
        if data_type.startswith("candle") or data_type.endswith(("m", "s")):
            data_type = self._normalize_candle_type(data_type, **kwargs)

        # 구독 설정 저장
        self.types[data_type] = {
            "codes": symbols,
            **kwargs
        }

        # 심볼 업데이트
        self.symbols.update(symbols)
        self.last_updated = datetime.now()

    def get_subscription_message(self) -> List[Dict[str, Any]]:
        """업비트 API 호환 메시지 생성"""
        if not self.types:
            return []

        message = [{"ticket": self.ticket}]

        # 모든 타입을 하나의 메시지에 포함
        for data_type, config in self.types.items():
            type_message = {"type": data_type, **config}
            message.append(type_message)

        message.append({"format": "DEFAULT"})
        return message

    def _normalize_candle_type(self, unit: str, **kwargs) -> str:
        """캔들 타입 정규화 (업비트 규격 준수)"""
        VALID_MINUTE_UNITS = [1, 3, 5, 10, 15, 30, 60, 240]
        VALID_SECOND_UNITS = [1]

        # "5m" → "candle.5m", "1s" → "candle.1s" 변환
        if unit.endswith("m") and not unit.startswith("candle."):
            minute_str = unit[:-1]
            if minute_str.isdigit() and int(minute_str) in VALID_MINUTE_UNITS:
                return f"candle.{minute_str}m"

        elif unit.endswith("s") and not unit.startswith("candle."):
            second_str = unit[:-1]
            if second_str.isdigit() and int(second_str) in VALID_SECOND_UNITS:
                return f"candle.{second_str}s"

        return unit
```

### 🎛️ **2. UpbitWebSocketSubscriptionManager**

```python
class UpbitWebSocketSubscriptionManager:
    """전담 구독 관리 시스템"""

    def __init__(self, max_tickets: int = 5, enable_ticket_reuse: bool = True):
        self._unified_subscriptions: Dict[str, UnifiedSubscription] = {}
        self._current_ticket = None
        self._max_tickets = max_tickets
        self.enable_ticket_reuse = enable_ticket_reuse

        # 레거시 호환성
        self._subscription_manager = SubscriptionResult()

        # 통계
        self._metrics = SubscriptionMetrics()

    def add_unified_subscription(self, data_type: str, symbols: List[str], **kwargs) -> str:
        """통합 구독 추가 - 핵심 로직"""

        # 현재 티켓이 없으면 새로 생성
        if not self._current_ticket:
            self._current_ticket = self._generate_ticket_id("unified")
            self._unified_subscriptions[self._current_ticket] = UnifiedSubscription(self._current_ticket)

        # 기존 티켓에 새 타입 추가
        unified_sub = self._unified_subscriptions[self._current_ticket]
        unified_sub.add_subscription_type(data_type, symbols, **kwargs)

        # 레거시 호환성 유지
        self._subscription_manager.add_subscription(data_type, symbols, **kwargs)

        # 통계 업데이트
        self._metrics.total_symbols = len(unified_sub.symbols)
        self._metrics.update()

        return self._current_ticket

    def get_subscriptions(self) -> Dict[str, Any]:
        """구독 정보 조회 - 새로운 구조 + 레거시 호환"""
        tickets_info = {}

        for ticket_id, unified_sub in self._unified_subscriptions.items():
            raw_message = unified_sub.get_subscription_message()

            tickets_info[ticket_id] = {
                'ticket': unified_sub.ticket,
                'raw_message': raw_message,
                'resubscribe_message': raw_message,  # 재구독용
                'subscription_types': list(unified_sub.types.keys()),
                'total_symbols': len(unified_sub.symbols),
                'stream_configs': self._build_stream_configs(unified_sub),
                'created_at': unified_sub.created_at,
                'last_updated': unified_sub.last_updated,
                'message_count': unified_sub.message_count,
                'is_resendable': len(raw_message) > 0,
                'symbols_summary': self._format_symbols_for_log(list(unified_sub.symbols))
            }

        return {
            'tickets': tickets_info,
            'consolidated_view': self.get_consolidated_view(),  # 레거시 호환
            'total_tickets': len(self._unified_subscriptions),
            'current_ticket': self._current_ticket,
            'resubscribe_ready': all(info['is_resendable'] for info in tickets_info.values())
        }

    def _build_stream_configs(self, unified_sub: UnifiedSubscription) -> Dict[str, Dict]:
        """스트림 설정 정보 구성"""
        stream_configs = {}

        for sub_type, type_config in unified_sub.types.items():
            is_snapshot_only = type_config.get('isOnlySnapshot', False)

            stream_configs[sub_type] = {
                'codes': type_config.get('codes', []),
                'raw_config': type_config,
                'is_snapshot_only': is_snapshot_only,
                'is_realtime': not is_snapshot_only,
                'stream_type': 'SNAPSHOT' if is_snapshot_only else 'REALTIME'
            }

        return stream_configs
```

### 🌐 **3. UpbitWebSocketPublicClient 통합**

```python
class UpbitWebSocketPublicClient:
    """WebSocket 클라이언트 - 구독 관리자 통합"""

    def __init__(self):
        # 구독 관리자 초기화
        self.subscription_manager = UpbitWebSocketSubscriptionManager()

        # WebSocket 연결 설정
        self.websocket = None
        self.is_connected = False

        # 메시지 핸들러
        self._message_handlers = {}

    async def subscribe_ticker(self, symbols: List[str], **kwargs) -> bool:
        """현재가 구독 - 구독 관리자 위임 패턴"""

        # 1. 구독 관리자에 등록
        ticket_id = self.subscription_manager.add_unified_subscription(
            WebSocketDataType.TICKER.value, symbols, **kwargs
        )

        # 2. 실제 WebSocket 전송
        result = await self._send_subscription_message(ticket_id)

        return result

    async def _send_subscription_message(self, ticket_id: str) -> bool:
        """WebSocket 메시지 전송 - 핵심 구현"""
        if not self.is_connected or not self.websocket:
            return False

        try:
            # 구독 관리자에서 완성된 메시지 가져오기
            raw_message = self.subscription_manager.get_resubscribe_message_by_ticket(ticket_id)
            if not raw_message:
                return False

            # JSON 직렬화 및 전송
            message_json = json.dumps(raw_message)
            await self.websocket.send(message_json)

            return True

        except Exception as e:
            self.logger.error(f"❌ 구독 메시지 전송 실패: {e}")
            return False

    def get_subscriptions(self) -> Dict[str, Any]:
        """구독 정보 조회 - 구독 관리자 위임"""
        return self.subscription_manager.get_subscriptions()
```

---

## 🔄 핵심 플로우 구현

### 📨 **메시지 생성 플로우**

```python
def subscription_flow_example():
    """구독 메시지 생성 플로우"""

    # 1. 구독 관리자 초기화
    manager = UpbitWebSocketSubscriptionManager()

    # 2. 첫 번째 구독 추가
    ticket1 = manager.add_unified_subscription("ticker", ["KRW-BTC"])
    # 내부적으로 UnifiedSubscription 생성, 티켓 할당

    # 3. 같은 티켓에 두 번째 구독 추가
    ticket2 = manager.add_unified_subscription("orderbook", ["KRW-BTC"])
    # ticket1 == ticket2 (같은 티켓 재사용!)

    # 4. 메시지 생성
    message = manager.get_resubscribe_message_by_ticket(ticket1)
    # 결과: [
    #   {'ticket': 'unified-xxxxx'},
    #   {'type': 'ticker', 'codes': ['KRW-BTC']},
    #   {'type': 'orderbook', 'codes': ['KRW-BTC']},
    #   {'format': 'DEFAULT'}
    # ]

    return message
```

### 🔄 **재구독 플로우**

```python
async def reconnection_flow(client):
    """연결 복원 시 재구독 플로우"""

    # 1. 구독 정보 조회
    subscriptions = client.get_subscriptions()

    # 2. 모든 티켓 재구독
    for ticket_id, ticket_info in subscriptions['tickets'].items():
        if ticket_info['is_resendable']:
            # 3. 원본 메시지로 재구독
            resubscribe_message = ticket_info['resubscribe_message']
            await client.websocket.send(json.dumps(resubscribe_message))

            # 4. 로깅
            types = ticket_info['subscription_types']
            print(f"✅ 티켓 {ticket_id} 재구독: {types}")
```

---

## 🧪 테스트 구현 패턴

### ✅ **단위 테스트 예시**

```python
@pytest.mark.asyncio
async def test_unified_subscription_integration():
    """통합 구독 테스트"""

    # Given: 클라이언트 연결
    client = UpbitWebSocketPublicClient()
    await client.connect()

    # When: 여러 타입 구독
    await client.subscribe_ticker(['KRW-BTC'])
    await client.subscribe_orderbook(['KRW-BTC'])

    # Then: 구독 정보 확인
    subscriptions = client.get_subscriptions()

    # 1. 티켓 개수 확인
    assert subscriptions['total_tickets'] == 1

    # 2. 구독 타입 확인
    ticket_info = list(subscriptions['tickets'].values())[0]
    assert 'ticker' in ticket_info['subscription_types']
    assert 'orderbook' in ticket_info['subscription_types']

    # 3. 재구독 메시지 확인
    resubscribe_msg = ticket_info['resubscribe_message']
    assert len(resubscribe_msg) == 4  # ticket + ticker + orderbook + format
    assert resubscribe_msg[0]['ticket']
    assert resubscribe_msg[-1]['format'] == 'DEFAULT'
```

### 🔍 **통합 테스트 예시**

```python
@pytest.mark.asyncio
async def test_subscription_lifecycle():
    """구독 생명주기 테스트"""

    client = UpbitWebSocketPublicClient()
    await client.connect()

    # 1. 구독 추가
    await client.subscribe_ticker(['KRW-BTC', 'KRW-ETH'])
    initial_subscriptions = client.get_subscriptions()

    # 2. 추가 구독 (같은 티켓에 통합되어야 함)
    await client.subscribe_orderbook(['KRW-BTC'])
    updated_subscriptions = client.get_subscriptions()

    # 3. 티켓 개수 동일 확인
    assert (initial_subscriptions['total_tickets'] ==
            updated_subscriptions['total_tickets'])

    # 4. 구독 타입 증가 확인
    ticket_id = updated_subscriptions['current_ticket']
    ticket_info = updated_subscriptions['tickets'][ticket_id]
    assert len(ticket_info['subscription_types']) == 2

    # 5. 연결 해제 및 재연결
    await client.disconnect()
    await client.connect()

    # 6. 재구독 실행
    for ticket_id, ticket_info in updated_subscriptions['tickets'].items():
        resubscribe_msg = ticket_info['resubscribe_message']
        await client.websocket.send(json.dumps(resubscribe_msg))

    # 7. 재구독 후 상태 확인
    final_subscriptions = client.get_subscriptions()
    assert final_subscriptions['resubscribe_ready'] == True
```

---

## 🚨 주의사항 및 베스트 프랙티스

### ⚠️ **구현 시 주의사항**

1. **티켓 재사용 로직**:
   ```python
   # ❌ 잘못된 방식: 매번 새 티켓 생성
   ticket1 = generate_new_ticket()
   ticket2 = generate_new_ticket()  # 비효율적!

   # ✅ 올바른 방식: 기존 티켓 재사용
   if not self._current_ticket:
       self._current_ticket = self._generate_ticket_id("unified")
   # 같은 티켓에 추가 구독
   ```

2. **메시지 구조 검증**:
   ```python
   # 필수 검증 항목
   assert isinstance(raw_message, list)
   assert raw_message[0].get('ticket')
   assert raw_message[-1].get('format') == 'DEFAULT'
   ```

3. **예외 처리**:
   ```python
   try:
       ticket_id = manager.add_unified_subscription(data_type, symbols)
       result = await self._send_subscription_message(ticket_id)
   except Exception as e:
       self.logger.error(f"구독 실패: {e}")
       return False
   ```

### 🎯 **성능 최적화 팁**

1. **메모리 효율성**:
   ```python
   # Set 사용으로 중복 제거
   self.symbols: Set[str] = set()
   self.symbols.update(new_symbols)
   ```

2. **네트워크 효율성**:
   ```python
   # 배치 구독으로 메시지 수 최소화
   await client.subscribe_unified([
       {'type': 'ticker', 'symbols': ['KRW-BTC', 'KRW-ETH']},
       {'type': 'orderbook', 'symbols': ['KRW-BTC']}
   ])
   ```

3. **상태 관리**:
   ```python
   # 통계 정보 캐싱
   self._metrics.update()  # 변경 시에만 업데이트
   ```

---

## 📊 디버깅 및 모니터링

### 🔍 **로깅 설정**

```python
# 환경 변수로 로깅 제어
import os
os.environ['UPBIT_LOG_SCOPE'] = 'verbose'
os.environ['UPBIT_COMPONENT_FOCUS'] = 'UpbitSubscriptionManager'

# 구독 관리자 로그 예시
logger.info(f"✅ {data_type} 통합 구독 추가: {len(symbols)}개 심볼, 티켓: {ticket_id}")
logger.debug(f"📝 현재 활성 티켓: {self._current_ticket}")
logger.error(f"❌ 구독 실패: {error_message}")
```

### 📈 **상태 모니터링**

```python
def monitor_subscription_health(client):
    """구독 상태 모니터링"""

    subscriptions = client.get_subscriptions()

    # 1. 기본 통계
    print(f"총 티켓: {subscriptions['total_tickets']}")
    print(f"재구독 준비: {subscriptions['resubscribe_ready']}")

    # 2. 티켓별 상세 정보
    for ticket_id, ticket_info in subscriptions['tickets'].items():
        print(f"\n티켓 {ticket_id[:8]}:")
        print(f"  구독 타입: {ticket_info['subscription_types']}")
        print(f"  심볼 수: {ticket_info['total_symbols']}")
        print(f"  재전송 가능: {ticket_info['is_resendable']}")

        # 3. 스트림 설정 확인
        for stream_type, stream_config in ticket_info['stream_configs'].items():
            print(f"  {stream_type}: {stream_config['stream_type']}")
```

---

## 🚀 확장 가능성

### 🔮 **향후 확장 방향**

1. **다중 거래소 지원**:
   ```python
   class UniversalSubscriptionManager:
       def __init__(self):
           self.upbit_manager = UpbitWebSocketSubscriptionManager()
           self.binance_manager = BinanceWebSocketSubscriptionManager()
   ```

2. **AI 기반 최적화**:
   ```python
   class SmartSubscriptionOptimizer:
       def optimize_ticket_allocation(self, subscription_patterns):
           # ML 기반 티켓 할당 최적화
           pass
   ```

3. **실시간 대시보드**:
   ```python
   class SubscriptionDashboard:
       def get_realtime_metrics(self):
           return {
               'active_subscriptions': self.manager.get_active_count(),
               'message_rate': self.manager.get_message_rate(),
               'efficiency_score': self.manager.calculate_efficiency()
           }
   ```

---

**작성일**: 2025년 8월 27일
**문서 버전**: v1.0
**구현 상태**: ✅ **Production Ready**
