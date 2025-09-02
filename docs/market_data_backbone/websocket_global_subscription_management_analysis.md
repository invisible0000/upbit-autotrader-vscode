# WebSocket 전역 구독 관리 시스템 분석 및 설계

## 📋 문제 상황 분석

### 🎯 핵심 문제
1. **업비트 WebSocket 특성**: 티켓별 분리 관리가 아닌 단일 연결의 통합 구독 관리
2. **GUI 다중 컴포넌트**: 차트뷰어의 코인리스트, 호가창, 차트가 각각 독립적으로 WebSocket 요청
3. **동적 구독 변경**: 사용자 상호작용에 따른 실시간 구독 목록 변경 필요
4. **구독 정리 문제**: 컴포넌트 종료 시 해당 구독의 자동 정리 필요

### 🔄 실제 사용 시나리오

#### 시나리오 1: 차트뷰 탭 클릭 (초기 상태)
```
기본값: KRW-BTC, 1시간봉
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
컴포넌트         요청                실시간 스트림 목록
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
코인리스트       KRW 마켓 모든 코인 현재가   → KRW 마켓 현재가 (ticker)
호가창           KRW-BTC 호가             → KRW-BTC 호가 (orderbook)
차트             KRW-BTC 1시간봉 캔들       → KRW-BTC 1시간봉 (minute60)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 통합 구독 상태:
   - ticker: [KRW-*] (전체 KRW 마켓)
   - orderbook: [KRW-BTC]
   - minute60: [KRW-BTC]
```

#### 시나리오 2: 코인리스트에서 KRW-ETH 클릭
```
변경: 호가창과 차트가 ETH로 전환
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
컴포넌트         변경사항                실시간 스트림 목록
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
코인리스트       변경없음 (KRW 마켓 유지)   → KRW 마켓 현재가 (ticker)
호가창           KRW-ETH로 변경            → KRW-ETH 호가 (orderbook)
차트             KRW-ETH 1시간봉으로 변경   → KRW-ETH 1시간봉 (minute60)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 통합 구독 상태:
   - ticker: [KRW-*] (전체 KRW 마켓)
   - orderbook: [KRW-ETH] (KRW-BTC → KRW-ETH)
   - minute60: [KRW-ETH] (KRW-BTC → KRW-ETH)

⚠️ 중요: KRW-BTC 관련 캔들과 호가는 자동 정리되어야 함(코인 리스트 클릭에 대응)
```

#### 시나리오 3: 마켓을 BTC로 변경
```
변경: 코인리스트 마켓 변경 (코인 미클릭)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
컴포넌트         변경사항                실시간 스트림 목록
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
코인리스트       BTC 마켓 전체 코인        → BTC 마켓 현재가 (ticker)
호가창           변경없음 (KRW-ETH 유지)   → KRW-ETH 호가 (orderbook)
차트             변경없음 (KRW-ETH 유지)   → KRW-ETH 1시간봉 (minute60)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 통합 구독 상태:
   - ticker: [BTC-*] (KRW-* → BTC-*)
   - orderbook: [KRW-ETH] (유지)
   - minute60: [KRW-ETH] (유지)

⚠️ 중요: KRW 마켓 ticker 구독은 자동 정리되어야 함(코인 리스트 기능, 콤보박스 변경에 대응)
```

### 🚨 핵심 기술적 도전과제

#### 1. **업비트 WebSocket 제약사항**
```yaml
업비트_WebSocket_특성:
  - 티켓별_분리관리: false  # 티켓은 단순 식별자, 구독 분리 안됨
  - 통합_구독관리: true     # 하나의 연결에서 모든 구독 통합 관리
  - 덮어쓰기_원리: true     # 새 구독 시 기존 구독 대체
  - 다중_데이터타입: true   # ticker, orderbook, candle 동시 구독 가능

제약사항:
  - 각_요청마다_전체_구독목록_재전송_필요
  - 부분_구독해제_불가능 (전체 재구독 필요)
  - 연결_안정성_의존성_높음
```

#### 2. **다중 클라이언트 사용 시 구독 충돌**
```python
# 문제 상황 예시
websocket_client_1.subscribe_ticker(["KRW-BTC"])     # 구독 1
websocket_client_2.subscribe_ticker(["KRW-ETH"])     # 구독 2 (구독 1 덮어쓰기됨!)

# 결과: KRW-BTC 구독이 사라지고 KRW-ETH만 구독됨
# 이는 업비트 WebSocket의 덮어쓰기 특성 때문임
```

#### 3. **Market Data Backbone과의 복잡한 상호작용**
```yaml
현재_아키텍처:
  SmartDataProvider:
    - 역할: 통합 데이터 제공 인터페이스
    - 의존성: SmartRouter (실제 API 통신)

  SmartRouter:
    - 역할: 최적 채널 선택 (REST vs WebSocket)
    - 의존성: REST/WebSocket 클라이언트들

  문제점:
    - WebSocket_구독_상태가_SmartRouter에_분산
    - 실시간_구독과_일회성_요청의_경계_모호
    - 구독_정리_시점_판단_어려움
```

## 🏗️ 해결 방안 설계

### 📐 설계 옵션 분석

#### 옵션 1: Market Data Backbone 순수 REST 전용
```yaml
장점:
  - 구현_복잡도_최소화
  - WebSocket_구독_충돌_문제_없음
  - 각_컴포넌트_독립적_API_사용

단점:
  - 실시간성_부족 (특히 현재가, 호가)
  - API_Rate_Limit_부담_증가
  - 네트워크_트래픽_증가
  - 사용자_경험_저하

적용_범위:
  - MarketDataBackbone: 캔들 데이터만 관리
  - UI_컴포넌트: 각자 WebSocket 클라이언트 사용
  - 구독_관리: 전역 GlobalSubscriptionManager 필요
```

#### 옵션 2: 통합 WebSocket 관리 (권장)
```yaml
장점:
  - 최고의_실시간성_보장
  - WebSocket_구독_효율성_극대화
  - 통합된_구독_관리
  - API_Rate_Limit_최적화

단점:
  - 구현_복잡도_증가
  - GlobalSubscriptionManager_개발_필요
  - 컴포넌트간_의존성_증가

핵심_구성요소:
  - GlobalWebSocketSubscriptionManager (전역 구독 관리)
  - ComponentSubscriptionTracker (컴포넌트별 구독 추적)
  - AutoCleanupService (자동 정리 서비스)
```

### 🎯 권장 아키텍처: 통합 WebSocket 관리

#### 핵심 컴포넌트 설계

##### 1. GlobalWebSocketSubscriptionManager
```python
class GlobalWebSocketSubscriptionManager:
    """전역 WebSocket 구독 관리자

    🎯 핵심 책임:
    - 프로그램 전체의 WebSocket 구독 통합 관리
    - 컴포넌트별 구독 요청 병합
    - 자동 구독 정리
    - 구독 충돌 방지
    """

    def __init__(self):
        # 전역 구독 상태 (데이터타입별)
        self.global_subscriptions = {
            "ticker": set(),      # 현재가 구독 심볼들
            "orderbook": set(),   # 호가 구독 심볼들
            "trade": set(),       # 체결 구독 심볼들
            "minute1": set(),     # 1분봉 구독 심볼들
            "minute60": set(),    # 1시간봉 구독 심볼들
        }

        # 컴포넌트별 구독 추적
        self.component_subscriptions = {}  # {component_id: {data_type: symbols}}

        # 실제 WebSocket 클라이언트 (단일 인스턴스)
        self.websocket_client = None

    async def subscribe(self, component_id: str, data_type: str, symbols: List[str]):
        """컴포넌트의 구독 요청 처리"""

    async def unsubscribe(self, component_id: str, data_type: str, symbols: List[str]):
        """컴포넌트의 구독 해제 요청 처리"""

    async def cleanup_component(self, component_id: str):
        """컴포넌트 종료 시 관련 구독 모두 정리"""

    async def _rebuild_websocket_subscriptions(self):
        """전역 구독 상태를 WebSocket에 반영 (전체 재구독)"""
```

##### 2. ComponentSubscriptionTracker
```python
class ComponentSubscriptionTracker:
    """컴포넌트별 구독 추적기

    🎯 핵심 책임:
    - 각 UI 컴포넌트의 구독 상태 추적
    - 컴포넌트 생명주기와 연동
    - 자동 정리 트리거
    """

    def register_component(self, component_id: str, component_type: str):
        """컴포넌트 등록 (생성 시)"""

    def unregister_component(self, component_id: str):
        """컴포넌트 해제 (종료 시)"""

    def update_component_subscriptions(self, component_id: str, subscriptions: Dict):
        """컴포넌트 구독 상태 업데이트"""
```

##### 3. SmartDataProvider Integration
```python
class SmartDataProvider:
    """기존 SmartDataProvider 확장

    🎯 확장 사항:
    - GlobalWebSocketSubscriptionManager 통합
    - 실시간 vs 일회성 요청 명확한 분리
    - 구독 생명주기 자동 관리
    """

    def __init__(self):
        # 기존 초기화...
        self.global_ws_manager = GlobalWebSocketSubscriptionManager()

    async def subscribe_realtime(self, component_id: str, data_type: str, symbols: List[str]):
        """실시간 구독 요청 (컴포넌트별 추적 포함)"""
        return await self.global_ws_manager.subscribe(component_id, data_type, symbols)

    async def get_snapshot(self, data_type: str, symbols: List[str]):
        """일회성 스냅샷 요청 (구독 없음)"""
        return await self.smart_router.get_data(...)

    async def cleanup_component_subscriptions(self, component_id: str):
        """컴포넌트 종료 시 구독 정리"""
        return await self.global_ws_manager.cleanup_component(component_id)
```

## 🔬 기술적 구현 가능성 분석

### ✅ 현재 WebSocket v5 시스템의 지원 능력

#### 1. **SubscriptionManager v4.0 활용**
```python
# 현재 SubscriptionManager의 핵심 기능
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5.subscription_manager import SubscriptionManager

# 🎯 활용 가능한 기능들:
subscription_manager = SubscriptionManager()

# 실시간 구독 (컴포넌트별 추적 가능)
await subscription_manager.request_realtime_data(
    symbols=["KRW-BTC", "KRW-ETH"],
    data_type="ticker",
    callback=callback_function,
    client_id="chart_viewer_coinlist",  # 👈 컴포넌트 ID로 활용 가능
    connection_type="public"
)

# 구독 중단 (컴포넌트별)
await subscription_manager.stop_realtime_data(
    symbols=["KRW-BTC"],
    data_type="ticker",
    client_id="chart_viewer_coinlist"
)

# 전체 구독 해제 (컴포넌트 종료 시)
await subscription_manager.unsubscribe_all(connection_type="public")
```

#### 2. **WebSocket v5 클라이언트의 Rate Limiter 통합**
```python
# 이미 구현된 동적 Rate Limiter 활용
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5.upbit_websocket_public_client import UpbitWebSocketPublicV5

# 🚀 Rate Limiter가 통합된 WebSocket 클라이언트
ws_client = UpbitWebSocketPublicV5(enable_dynamic_rate_limiter=True)

# GlobalSubscriptionManager에서 활용 가능
global_manager = GlobalWebSocketSubscriptionManager(websocket_client=ws_client)
```

### 🚧 필요한 추가 개발 사항

#### 1. **GlobalWebSocketSubscriptionManager 구현**
```yaml
개발_필요도: HIGH
복잡도: MEDIUM
예상_개발시간: 3-5일

핵심_기능:
  - 전역 구독 상태 통합 관리
  - 컴포넌트별 구독 추적
  - 자동 구독 병합/정리
  - WebSocket v5 클라이언트 연동
```

#### 2. **ComponentLifecycleManager 구현**
```yaml
개발_필요도: MEDIUM
복잡도: LOW
예상_개발시간: 1-2일

핵심_기능:
  - UI 컴포넌트 생명주기 추적
  - 컴포넌트 종료 시 자동 정리
  - 메모리 누수 방지
```

#### 3. **SmartDataProvider 인터페이스 확장**
```yaml
개발_필요도: HIGH
복잡도: MEDIUM
예상_개발시간: 2-3일

핵심_기능:
  - subscribe_realtime() 메서드 추가
  - get_snapshot() 메서드 명확화
  - component_id 기반 구독 관리
  - 기존 API 호환성 유지
```

## 📊 최종 권장사항

### 🎯 권장 구현 방안: **옵션 2 (통합 WebSocket 관리)**

#### 핵심 이유:
1. **실시간성 보장**: 차트뷰어의 핵심 요구사항 충족
2. **기존 인프라 활용**: WebSocket v5와 SubscriptionManager v4.0 최대 활용
3. **확장성**: 향후 더 많은 실시간 기능 지원 가능
4. **성능 최적화**: Rate Limiter 통합으로 API 효율성 극대화

#### 구현 단계:
```yaml
Phase_1: GlobalWebSocketSubscriptionManager 핵심 구현 (1주)
  - 전역 구독 상태 관리
  - 기본 구독/해제 기능
  - WebSocket v5 클라이언트 연동

Phase_2: Component 생명주기 관리 (3일)
  - ComponentLifecycleManager 구현
  - 자동 정리 메커니즘
  - 메모리 누수 방지

Phase_3: SmartDataProvider 통합 (1주)
  - 실시간/스냅샷 API 분리
  - 기존 API 호환성 유지
  - 전체 시스템 통합 테스트

Phase_4: UI 컴포넌트 연동 (1주)
  - 차트뷰어 컴포넌트 연동
  - 사용 시나리오 검증
  - 성능 최적화
```

### 🎁 예상 효과:
1. **개발자 경험 개선**: 간단한 API로 복잡한 WebSocket 구독 관리
2. **성능 향상**: 전역 구독 최적화로 불필요한 중복 구독 제거
3. **안정성 향상**: 자동 정리로 메모리 누수 및 좀비 구독 방지
4. **유지보수성**: 중앙집중식 관리로 디버깅 및 모니터링 용이

### ⚠️ 주의사항:
1. **복잡도 증가**: 초기 구현 복잡도 높음 (하지만 장기적 이득)
2. **의존성 관리**: 컴포넌트간 의존성 신중한 설계 필요
3. **테스트 전략**: 다양한 시나리오에 대한 철저한 테스트 필요

## 🚀 결론

**현재 Market Data Backbone의 기반 구조는 훌륭하며, GlobalWebSocketSubscriptionManager 추가 구현을 통해 완전한 통합 관리가 가능합니다.**

이는 기존 SmartRouter와 SubscriptionManager v4.0의 강력한 기능을 활용하면서도, 실제 GUI 애플리케이션의 복잡한 구독 관리 요구사항을 완벽하게 해결할 수 있는 실현 가능한 방안입니다.
