# WebSocket v6 간소화 연결 관리 가이드

## 📌 개요

업비트 자동매매 시스템의 WebSocket v6 간소화 버전에서 **연결 유지 관리**와 **전역 구독 관리**를 위한 핵심 설계 문서입니다.

### 🎯 핵심 목표
- **즉시 응답성**: 1초 이내 정보 제공 (일반 상황)
- **연결 지속성**: 프로그램 시작부터 종료까지 WebSocket 연결 유지
- **자동 복구**: 네트워크 이슈 시 투명한 재연결
- **전역 관리**: Public/Private 연결의 통합 구독 관리

---

## 🔗 연결 유지 관리 시스템

### 1. 연결 생명주기 관리

#### 🚀 시작 시 즉시 연결
```python
# WebSocketManager.start() 시점
async def start(self) -> None:
    """시스템 시작 시 즉시 기본 연결 생성"""

    # 1️⃣ Public 연결 즉시 생성 (필수)
    await self._ensure_connection(WebSocketType.PUBLIC)

    # 2️⃣ Private 연결 조건부 생성 (API 키 존재 시)
    if await self._has_valid_api_key():
        await self._ensure_connection(WebSocketType.PRIVATE)

    # 3️⃣ 연결 지속성 모니터링 시작
    await self._start_connection_monitoring()
```

#### ⏱️ 타임아웃 정책
```yaml
연결_타임아웃:
  일반상황: 1초
  네트워크_불량: 5초 (최대)
  재시도_간격: 1초, 2초, 5초 (지수백오프)

응답_타임아웃:
  메시지_전송: 1초
  구독_변경: 2초
  최대_대기: 5초
```

### 2. 연결 상태 모니터링

#### 🔍 실시간 헬스체크
```python
async def _start_connection_monitoring(self) -> None:
    """연결 지속성 보장 모니터링"""

    while self._state == GlobalManagerState.ACTIVE:
        # 30초마다 연결 상태 확인
        await asyncio.sleep(30.0)

        # Public 연결 헬스체크
        if not await self._is_connection_healthy(WebSocketType.PUBLIC):
            await self._recover_connection(WebSocketType.PUBLIC)

        # Private 연결 헬스체크 (API 키 유효성 포함)
        if await self._should_maintain_private_connection():
            if not await self._is_connection_healthy(WebSocketType.PRIVATE):
                await self._recover_connection(WebSocketType.PRIVATE)
```

#### 💓 연결 건강도 체크
```python
async def _is_connection_healthy(self, connection_type: WebSocketType) -> bool:
    """연결 건강도 확인"""

    connection = self._connections[connection_type]

    # 1️⃣ 연결 객체 존재 확인
    if not connection:
        return False

    # 2️⃣ WebSocket 상태 확인 (state == 1 = OPEN)
    if hasattr(connection, 'state') and connection.state != 1:
        return False

    # 3️⃣ 최근 응답성 확인 (60초 이내 메시지 수신)
    last_activity = self._last_message_times.get(connection_type)
    if last_activity and time.time() - last_activity > 60:
        return False

    return True
```

### 3. 자동 복구 시스템

#### 🔄 투명한 재연결
```python
async def _recover_connection(self, connection_type: WebSocketType) -> None:
    """연결 복구 (사용자 인식 없이)"""

    try:
        # 1️⃣ 기존 연결 정리
        await self._disconnect_websocket(connection_type)

        # 2️⃣ 잠시 대기 (안정성)
        await asyncio.sleep(1.0)

        # 3️⃣ 새 연결 생성
        await self._connect_websocket(connection_type)

        # 4️⃣ 기존 구독 즉시 복원
        await self._restore_subscriptions(connection_type)

        logger.info(f"✅ {connection_type} 연결 복구 완료")

    except Exception as e:
        logger.error(f"❌ {connection_type} 연결 복구 실패: {e}")
        # 재시도 스케줄링
        asyncio.create_task(self._schedule_retry(connection_type))
```

#### 🔂 지수 백오프 재시도
```python
async def _schedule_retry(self, connection_type: WebSocketType) -> None:
    """재시도 스케줄링 (지수 백오프)"""

    retry_delays = [1, 2, 5, 10, 20]  # 초 단위

    for delay in retry_delays:
        await asyncio.sleep(delay)

        try:
            await self._recover_connection(connection_type)
            return  # 성공 시 재시도 중단
        except Exception as e:
            logger.warning(f"재시도 {delay}초 후 실패: {e}")
            continue

    # 모든 재시도 실패 시 알림
    logger.error(f"🚨 {connection_type} 연결 완전 실패")
```

---

## 🌐 전역 구독 관리

### 1. 통합 구독 상태 관리

#### 📊 전역 구독 추적
```python
class GlobalSubscriptionTracker:
    """전역 구독 상태 추적기"""

    def __init__(self):
        # 전역 구독 현황 (데이터타입별)
        self.active_subscriptions = {
            # Public 구독
            DataType.TICKER: set(),      # {"KRW-BTC", "KRW-ETH", ...}
            DataType.ORDERBOOK: set(),   # {"KRW-BTC"}
            DataType.TRADE: set(),       # {"KRW-BTC"}
            DataType.CANDLE_1M: set(),   # {"KRW-BTC"}

            # Private 구독 (심볼 없음)
            DataType.MYORDER: set(),     # {True} or set()
            DataType.MYASSET: set(),     # {True} or set()
        }

        # 컴포넌트별 구독 (추적용)
        self.component_subscriptions = {}  # {component_id: {data_type: symbols}}
```

#### 🔄 구독 변경 감지
```python
async def _on_subscription_change(self, changes: Dict) -> None:
    """구독 변경 시 즉시 WebSocket 반영"""

    # Public 구독 변경사항 적용
    public_changes = self._extract_public_changes(changes)
    if public_changes:
        await self._apply_public_subscriptions()

    # Private 구독 변경사항 적용
    private_changes = self._extract_private_changes(changes)
    if private_changes:
        await self._apply_private_subscriptions()
```

### 2. 스마트 구독 병합

#### 🧠 중복 제거 최적화
```python
async def _apply_public_subscriptions(self) -> None:
    """Public 구독 최적화 적용"""

    # 모든 컴포넌트의 구독을 병합
    merged_subscriptions = self._merge_component_subscriptions()

    # 업비트 메시지 형식으로 변환
    subscription_messages = []

    for data_type, symbols in merged_subscriptions.items():
        if symbols and data_type.is_public():
            message = {
                "ticket": f"ws_{data_type.value}_{int(time.time())}",
                "type": data_type.value,
                "codes": list(symbols)  # 중복 제거된 심볼 목록
            }
            subscription_messages.append(message)

    # 일괄 전송 (업비트 권장 방식)
    if subscription_messages:
        await self._send_subscription_batch(WebSocketType.PUBLIC, subscription_messages)
```

#### 📋 실시간 시나리오 예시

##### 시나리오 1: 차트뷰어 초기 로딩
```yaml
상황: 사용자가 차트뷰어 탭 클릭
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
컴포넌트          요청                   병합된_전역구독
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CoinList         KRW-* ticker          → ticker: [KRW-*]
OrderbookView    KRW-BTC orderbook     → orderbook: [KRW-BTC]
ChartView        KRW-BTC candle.1m     → candle.1m: [KRW-BTC]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

업비트_WebSocket_메시지:
  - ticker: 전체 KRW 마켓
  - orderbook: KRW-BTC
  - candle.1m: KRW-BTC
```

##### 시나리오 2: 코인 변경 (KRW-BTC → KRW-ETH)
```yaml
상황: 코인리스트에서 ETH 클릭
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
변경사항                      최적화된_구독변경
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OrderbookView: BTC→ETH       → orderbook: [KRW-ETH]
ChartView: BTC→ETH          → candle.1m: [KRW-ETH]
CoinList: 변경없음           → ticker: [KRW-*] (유지)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

최적화_결과:
  ✅ KRW-BTC 구독은 자동 정리
  ✅ KRW-ETH 구독은 즉시 활성화
  ⚡ 1초 이내 새 데이터 수신 시작
```

### 3. API 키 관리

#### 🔐 Private 연결 상태 관리
```python
async def _monitor_api_key_status(self) -> None:
    """API 키 상태 모니터링"""

    while self._state == GlobalManagerState.ACTIVE:
        try:
            # API 키 유효성 확인
            if await self._jwt_manager.get_valid_token():
                # API 키 정상 - Private 연결 유지
                if not await self._is_connection_healthy(WebSocketType.PRIVATE):
                    await self._recover_connection(WebSocketType.PRIVATE)
            else:
                # API 키 이상 - Private 연결 해제 및 알림
                if self._connections[WebSocketType.PRIVATE]:
                    await self._disconnect_websocket(WebSocketType.PRIVATE)
                    self._notify_api_key_issue()

        except Exception as e:
            logger.warning(f"API 키 상태 확인 실패: {e}")

        await asyncio.sleep(60.0)  # 1분마다 확인
```

#### 📢 API 키 이슈 알림
```python
def _notify_api_key_issue(self) -> None:
    """API 키 이슈 시스템 알림"""

    issue_info = {
        "type": "api_key_issue",
        "message": "API 키 이상으로 Private 연결 사용 불가",
        "timestamp": time.time(),
        "auto_recovery": True  # API 키 정상화 시 자동 복구
    }

    # 시스템 이벤트로 전파 (UI 알림 등)
    self._broadcast_system_event(issue_info)
```

---

## ⚡ 성능 최적화

### 1. Rate Limiter 통합

#### 🚦 동적 속도 제한
```python
async def _apply_rate_limit(self, action: str = 'websocket_message') -> None:
    """업비트 API 제한 준수"""

    if self._rate_limiter_enabled and self._dynamic_limiter:
        try:
            # 동적 Rate Limiter로 안전한 속도 제어
            await self._dynamic_limiter.acquire(action, 'WS', max_wait=15.0)
        except Exception as e:
            logger.warning(f"Rate Limiter 오류 (계속 진행): {e}")
```

### 2. 메시지 처리 최적화

#### 📨 비동기 메시지 처리
```python
async def _handle_messages(self, connection_type: WebSocketType, connection) -> None:
    """메시지 수신 및 즉시 처리"""

    async for message in connection:
        try:
            # JSON 파싱
            data = json.loads(message)

            # 업비트 에러 메시지 확인
            if self._is_upbit_error(data):
                await self._handle_upbit_error(data, connection_type)
                continue

            # 이벤트 생성 및 라우팅 (비동기)
            asyncio.create_task(self._process_message_async(data, connection_type))

        except Exception as e:
            logger.error(f"메시지 처리 실패: {e}")
```

---

## 🔧 추가 고려사항

### 1. 연결 독립성 강화
- **Public/Private 완전 분리**: 한쪽 연결 이슈가 다른 쪽에 영향 없음
- **개별 복구 메커니즘**: 각 연결별 독립적 재연결 로직
- **독립성 모니터링**: 연결 간 영향도 실시간 추적

### 2. 백프레셔 처리
- **Queue 관리**: 메시지 급증 시 오래된 데이터 자동 제거
- **우선순위 처리**: 실시간성 중요 데이터 우선 처리
- **메모리 보호**: 메시지 큐 크기 제한으로 메모리 누수 방지

### 3. 모니터링 및 디버깅
- **연결 메트릭스**: 응답시간, 처리량, 에러율 실시간 추적
- **헬스체크 API**: 외부에서 WebSocket 상태 조회 가능
- **로그 구조화**: 연결별, 컴포넌트별 세분화된 로깅

### 4. 사용자 경험 개선
- **투명한 재연결**: 사용자가 연결 이슈를 인식하지 못하도록
- **즉시 응답**: 구독 변경 후 1초 이내 데이터 수신
- **상태 피드백**: UI에서 연결 상태 시각적 표시

---

## 🚀 구현 우선순위

### Phase 1: 핵심 연결 관리 (1주)
1. ✅ 시작 시 즉시 연결 생성
2. ✅ 30초 주기 헬스체크
3. ✅ 자동 재연결 메커니즘
4. ✅ API 키 상태 모니터링

### Phase 2: 전역 구독 최적화 (1주)
1. ✅ 구독 병합 및 중복 제거
2. ✅ 실시간 구독 변경 반영
3. ✅ 컴포넌트별 구독 추적
4. ✅ Rate Limiter 통합

### Phase 3: 성능 및 안정성 (1주)
1. 🔄 백프레셔 처리 강화
2. 🔄 연결 독립성 모니터링
3. 🔄 메트릭스 수집 및 분석
4. 🔄 종합 테스트 및 최적화

---

## 📊 성공 지표

### 연결 안정성
- **가동률**: 99.9% 이상 연결 유지
- **복구시간**: 네트워크 이슈 시 5초 이내 자동 복구
- **응답성**: 일반 상황에서 1초 이내 데이터 수신

### 성능 효율성
- **메모리 사용량**: 연결당 50MB 이하
- **CPU 사용률**: 정상 상태에서 5% 이하
- **메시지 처리**: 초당 1000개 이상 메시지 처리 가능

### 사용자 경험
- **투명성**: 재연결 시 사용자 인지 불가
- **즉시성**: 구독 변경 후 즉시 데이터 수신
- **안정성**: 24시간 연속 운영 시 이슈 없음

---

이 가이드는 **WebSocket v6 간소화 시스템**에서 핵심적인 연결 유지와 전역 구독 관리 기능을 구현하기 위한 실무적이고 구체적인 방향을 제시합니다. 기존 v6 백업 버전의 고급 기능들을 참고하되, 간소화된 구조에 맞게 최적화된 설계입니다.
