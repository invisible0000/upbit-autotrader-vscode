# 업비트 WebSocket 전역 구독 관리 시스템 설계

## 📋 문제 정의

### 🔍 핵심 문제
업비트 WebSocket API의 특성상 **티켓별 독립 구독이 불가능**하며, **새로운 구독 요청 시 기존 스트림이 대체**되는 구조입니다. 이로 인해 GUI 애플리케이션에서 여러 컴포넌트가 동시에 WebSocket을 사용할 때 구독 충돌과 데이터 손실이 발생할 수 있습니다.

### 🎯 업비트 WebSocket 특성
1. **티켓 재사용 권장**: 각 구독마다 새 티켓을 만들 필요 없음
2. **구독 덮어쓰기**: 새 구독 요청 시 이전 구독이 완전히 대체됨
3. **전역 상태 관리 필요**: 모든 컴포넌트의 구독 요구사항을 통합 관리해야 함
4. **실시간 스트림 중단 위험**: 개별 컴포넌트의 구독 변경이 다른 컴포넌트에 영향

## 🎬 사용자 시나리오 분석

### 시나리오 1: 차트뷰 탭 최초 진입
```
사용자 액션: 차트뷰 탭 클릭 (기본값: KRW-BTC)

컴포넌트별 요구사항:
┌─────────────────┬──────────────────┬─────────────────────────┐
│ 컴포넌트        │ 구독 타입        │ 구독 심볼               │
├─────────────────┼──────────────────┼─────────────────────────┤
│ 코인 리스트     │ ticker           │ KRW 마켓 전체 (200+개)  │
│ 호가창          │ orderbook        │ KRW-BTC                 │
│ 차트            │ minute60         │ KRW-BTC                 │
└─────────────────┴──────────────────┴─────────────────────────┘

통합 WebSocket 구독:
- 티켓: "unified_public_main_001"
- 실시간 스트림: [KRW마켓 ticker, KRW-BTC orderbook, KRW-BTC minute60]
```

### 시나리오 2: 코인 변경 (KRW-ETH 선택)
```
사용자 액션: 코인 리스트에서 KRW-ETH 클릭

컴포넌트별 요구사항 변경:
┌─────────────────┬──────────────────┬─────────────────────────┐
│ 컴포넌트        │ 구독 타입        │ 구독 심볼               │
├─────────────────┼──────────────────┼─────────────────────────┤
│ 코인 리스트     │ ticker           │ KRW 마켓 전체 (유지)    │
│ 호가창          │ orderbook        │ KRW-ETH (변경)          │
│ 차트            │ minute60         │ KRW-ETH (변경)          │
└─────────────────┴──────────────────┴─────────────────────────┘

통합 WebSocket 구독 갱신:
- 이전 구독 완전 대체
- 새 실시간 스트림: [KRW마켓 ticker, KRW-ETH orderbook, KRW-ETH minute60]
- ⚠️ 기존 KRW-BTC 호가/차트 스트림 중단됨
```

### 시나리오 3: 마켓 변경 (BTC 마켓 선택)
```
사용자 액션: 코인 리스트 마켓 콤보박스를 BTC로 변경

컴포넌트별 요구사항 변경:
┌─────────────────┬──────────────────┬─────────────────────────┐
│ 컴포넌트        │ 구독 타입        │ 구독 심볼               │
├─────────────────┼──────────────────┼─────────────────────────┤
│ 코인 리스트     │ ticker           │ BTC 마켓 전체 (변경)    │
│ 호가창          │ orderbook        │ KRW-ETH (유지)          │
│ 차트            │ minute60         │ KRW-ETH (유지)          │
└─────────────────┴──────────────────┴─────────────────────────┘

통합 WebSocket 구독 갱신:
- 실시간 스트림: [BTC마켓 ticker, KRW-ETH orderbook, KRW-ETH minute60]
- ⚠️ 크로스 마켓 구독: BTC 마켓 + KRW 심볼 동시 구독
```

### 시나리오 4: 복합 변경 상황
```
사용자 액션: 차트 타임프레임을 5분봉으로 변경 + 새 코인 BTC-ETH 선택

컴포넌트별 요구사항:
┌─────────────────┬──────────────────┬─────────────────────────┐
│ 컴포넌트        │ 구독 타입        │ 구독 심볼               │
├─────────────────┼──────────────────┼─────────────────────────┤
│ 코인 리스트     │ ticker           │ BTC 마켓 전체           │
│ 호가창          │ orderbook        │ BTC-ETH                 │
│ 차트            │ minute5          │ BTC-ETH                 │
└─────────────────┴──────────────────┴─────────────────────────┘

최종 통합 구독:
- 실시간 스트림: [BTC마켓 ticker, BTC-ETH orderbook, BTC-ETH minute5]
```

## 🚨 현재 시스템의 한계점

### 1. 분산된 구독 관리
```python
# 문제 상황: 각 컴포넌트가 독립적으로 WebSocket 클라이언트 생성
class CoinListWidget:
    def __init__(self):
        self.ws_client = UpbitWebSocketPublicV5()  # 독립 클라이언트 1

class OrderBookWidget:
    def __init__(self):
        self.ws_client = UpbitWebSocketPublicV5()  # 독립 클라이언트 2

class ChartWidget:
    def __init__(self):
        self.ws_client = UpbitWebSocketPublicV5()  # 독립 클라이언트 3
```

### 2. 구독 충돌 문제
```python
# 시나리오: 차트에서 KRW-BTC 구독 중 → 호가창에서 KRW-ETH 구독 요청
# 결과: KRW-BTC 차트 스트림이 중단됨

chart_client.subscribe_candle(["KRW-BTC"], "minute60")  # 구독 A
# ... 시간 경과 ...
orderbook_client.subscribe_orderbook(["KRW-ETH"])      # 구독 B (구독 A 덮어씀)
# 결과: KRW-BTC 차트 데이터 중단, KRW-ETH 호가만 수신
```

### 3. 상태 동기화 부재
```python
# 각 컴포넌트가 서로의 구독 상태를 모름
coin_list.current_subscriptions     # 알 수 없음
orderbook.current_subscriptions     # 알 수 없음
chart.current_subscriptions         # 알 수 없음
```

## 💡 해결 방안: 전역 구독 관리 시스템

### 아키텍처 개요
```
┌─────────────────────────────────────────────────────────────┐
│                  전역 구독 관리자                            │
│  ┌─────────────────┬─────────────────┬──────────────────┐  │
│  │  구독 통합기    │  상태 추적기    │   충돌 해결기    │  │
│  └─────────────────┴─────────────────┴──────────────────┘  │
└─────────────────────┬───────────────────┬─────────────────┘
                      │                   │
              ┌───────▼────────┐  ┌───────▼────────┐
              │ Public WebSocket│  │Private WebSocket│
              │    (단일 연결)   │  │   (단일 연결)   │
              └─────────────────┘  └─────────────────┘
                      ▲                   ▲
          ┌───────────┼───────────────────┼──────────────┐
          │           │                   │              │
    ┌─────▼────┐ ┌───▼────┐ ┌────────▼────┐ ┌──────▼─────┐
    │코인리스트│ │ 호가창 │ │   차트뷰    │ │ 기타 위젯  │
    │(ticker)  │ │(order) │ │  (candle)   │ │            │
    └──────────┘ └────────┘ └─────────────┘ └────────────┘
```

### 1. 전역 구독 관리자 (GlobalSubscriptionManager)
```python
class GlobalSubscriptionManager:
    """
    애플리케이션 전역 WebSocket 구독 통합 관리
    - 단일 WebSocket 연결 관리
    - 모든 컴포넌트의 구독 요구사항 통합
    - 실시간 구독 변경 및 충돌 해결
    """

    def __init__(self):
        # 단일 WebSocket 연결들
        self.public_client = UpbitWebSocketPublicV5()
        self.private_client = UpbitWebSocketPrivateV5()

        # 컴포넌트별 구독 요구사항 추적
        self.component_subscriptions = {}

        # 현재 활성 통합 구독
        self.active_public_subscription = set()
        self.active_private_subscription = set()

        # 데이터 라우팅 (심볼+타입 → 콜백 리스트)
        self.data_routes = defaultdict(list)
```

### 2. 컴포넌트 구독 인터페이스
```python
class ComponentSubscriptionInterface:
    """컴포넌트에서 사용할 구독 인터페이스"""

    def register_subscription(self,
                            component_id: str,
                            subscription_spec: SubscriptionSpec) -> None:
        """
        컴포넌트의 구독 요구사항 등록

        Args:
            component_id: 컴포넌트 고유 ID (예: "coin_list", "orderbook_krw_btc")
            subscription_spec: 구독 명세 (심볼, 타입, 콜백)
        """

    def update_subscription(self,
                          component_id: str,
                          subscription_spec: SubscriptionSpec) -> None:
        """구독 요구사항 변경"""

    def unregister_subscription(self, component_id: str) -> None:
        """구독 해제"""
```

### 3. 구독 명세 표준화
```python
@dataclass
class SubscriptionSpec:
    """표준화된 구독 명세"""
    symbols: Set[str]           # 구독 심볼들
    data_type: DataType         # 데이터 타입
    callback: Callable          # 데이터 수신 콜백
    priority: int = 0           # 우선순위 (충돌 시 해결용)
    description: str = ""       # 구독 목적 설명

@dataclass
class ComponentSubscription:
    """컴포넌트별 구독 추적"""
    component_id: str
    spec: SubscriptionSpec
    timestamp: float
    is_active: bool = True
```

## 🔧 구현 계획

### Phase 1: 전역 관리자 구현
1. **GlobalSubscriptionManager 클래스 생성**
   - 단일 WebSocket 연결 관리
   - 컴포넌트 구독 추적 시스템
   - 통합 구독 생성 및 갱신 로직

2. **구독 통합 알고리즘**
   - 모든 컴포넌트 요구사항 수집
   - 중복 제거 및 최적화
   - 우선순위 기반 충돌 해결

3. **데이터 라우팅 시스템**
   - 수신 데이터를 적절한 컴포넌트로 전달
   - 심볼+타입 기반 라우팅 테이블
   - 성능 최적화된 디스패처

### Phase 2: 컴포넌트 통합
1. **기존 위젯 개선**
   - 독립 WebSocket 클라이언트 제거
   - 전역 관리자 인터페이스 사용
   - 구독 생명주기 관리

2. **상태 동기화**
   - 컴포넌트 간 구독 상태 공유
   - 실시간 상태 변경 알림
   - 일관성 보장 메커니즘

### Phase 3: 고급 기능
1. **지능적 구독 최적화**
   - 유사 구독 통합 (예: KRW-BTC 1분봉 + 5분봉 → 1분봉만 구독 후 가공)
   - 사용량 기반 자동 해제
   - 대역폭 최적화

2. **장애 복구**
   - WebSocket 연결 끊김 시 자동 재구독
   - 구독 상태 백업 및 복원
   - 점진적 재연결 전략

## 🧪 검증 계획

### 1. 단위 테스트
```python
def test_subscription_consolidation():
    """여러 컴포넌트 구독이 올바르게 통합되는지 테스트"""
    manager = GlobalSubscriptionManager()

    # 3개 컴포넌트가 서로 다른 구독 요청
    manager.register_subscription("coin_list",
        SubscriptionSpec({"KRW-BTC", "KRW-ETH"}, DataType.TICKER, callback1))
    manager.register_subscription("orderbook",
        SubscriptionSpec({"KRW-BTC"}, DataType.ORDERBOOK, callback2))
    manager.register_subscription("chart",
        SubscriptionSpec({"KRW-BTC"}, DataType.MINUTE60, callback3))

    # 통합 구독 검증
    consolidated = manager.get_consolidated_subscription()
    assert "KRW-BTC" in consolidated[DataType.TICKER]
    assert "KRW-ETH" in consolidated[DataType.TICKER]
    assert "KRW-BTC" in consolidated[DataType.ORDERBOOK]
    assert "KRW-BTC" in consolidated[DataType.MINUTE60]
```

### 2. 통합 테스트
```python
def test_gui_scenario_simulation():
    """실제 GUI 사용 시나리오 시뮬레이션"""
    # 시나리오 1: 차트뷰 진입
    # 시나리오 2: 코인 변경
    # 시나리오 3: 마켓 변경
    # 각 단계에서 구독 상태 검증
```

### 3. 성능 테스트
```python
def test_high_frequency_subscription_changes():
    """빈번한 구독 변경 시 성능 검증"""
    # 1초마다 구독 변경 100회
    # 메모리 누수 검사
    # 응답 지연 측정
```

## 📊 현재 WebSocket v5 기능 분석

### ✅ 지원 가능한 기능들
1. **SubscriptionManager v4.0**
   - 이미 통합 구독 최적화 로직 보유
   - 연결별 단일 활성 구독 관리
   - 실시간/스냅샷 지능적 조화

2. **Rate Limiter 통합**
   - 동적 Rate Limiter 적용 완료
   - REST API와 동일한 성능 최적화
   - 전역 Rate Limiting 공유

3. **상태 관리 시스템**
   - WebSocketStateMachine으로 연결 상태 추적
   - 자동 재연결 및 복구 메커니즘
   - 실시간 모니터링 및 디버깅

### ⚠️ 보완 필요한 부분들
1. **컴포넌트 간 구독 조정**
   - 현재는 단일 클라이언트 내에서만 최적화
   - 다중 클라이언트 인스턴스 간 조정 부재
   - 전역 상태 공유 메커니즘 필요

2. **데이터 라우팅 시스템**
   - 수신 데이터를 여러 컴포넌트로 배분하는 로직 부재
   - 콜백 관리 및 라우팅 테이블 필요

3. **생명주기 통합 관리**
   - GUI 컴포넌트 생성/소멸 시 구독 자동 관리
   - 메모리 누수 방지 메커니즘

## 🎯 결론 및 권장사항

### 타당성 검토 결과: ✅ **매우 타당함**
1. **기술적 필요성**: 업비트 WebSocket 특성상 필수적
2. **사용자 경험**: GUI 애플리케이션의 핵심 요구사항
3. **시스템 안정성**: 구독 충돌 방지로 안정성 향상
4. **성능 최적화**: 중복 구독 제거로 대역폭 절약

### 현재 v5 기능으로 구현 가능성: ✅ **충분히 가능**
- **기반 시설**: SubscriptionManager v4.0이 핵심 로직 보유
- **확장 지점**: 전역 관리자 래퍼 클래스로 기능 확장 가능
- **호환성**: 기존 구조 유지하면서 점진적 개선 가능

### 구현 우선순위
1. **🔥 1순위**: GlobalSubscriptionManager 핵심 클래스 구현
2. **⚡ 2순위**: 기존 GUI 컴포넌트와의 통합 인터페이스
3. **🎯 3순위**: 지능적 최적화 및 고급 기능

이 시스템이 구현되면 **REST API + WebSocket 통합 아키텍처**가 완성되어 진정한 의미의 통합 자동매매 시스템이 될 것입니다.
