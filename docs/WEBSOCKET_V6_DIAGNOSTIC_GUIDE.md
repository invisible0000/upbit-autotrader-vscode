# WebSocket v6 진단 및 테스트 가이드

## 📋 문서 개요

### 목적
WebSocket v6 시스템의 타입 안전성 및 아키텍처 일관성 문제를 진단하고 수정하기 위한 포괄적인 가이드

### 대상 독자
- 차세대 개발자/AI 에이전트
- WebSocket v6 시스템 유지보수자
- 아키텍처 검토자

### 핵심 발견 사항
**WebSocket v6의 치명적인 타입 불일치 버그**를 발견함. 모든 구독 요청이 런타임에서 실패하는 근본 원인.

---

## 🔍 발견된 핵심 문제

### Problem Statement
WebSocket v6 시스템에서 `WebSocketManager`와 `SubscriptionManager` 간의 **타입 계약 위반**으로 인해 모든 구독 기능이 동작하지 않음.

### 문제 위치
```
upbit_auto_trading/infrastructure/external_apis/upbit/websocket/core/websocket_manager.py:598-603
```

### 에러 시그니처
```
ERROR | upbit.WebSocketManager | 'list' object has no attribute 'subscriptions'
```

---

## 🧬 타입 불일치 분석

### 1. Interface Contract 위반

**WebSocketManager.register_component() 메서드**
```python
# 파일: websocket_manager.py:574-579
async def register_component(
    self,
    component_id: str,
    component_ref: Any,
    subscriptions: Optional[List[SubscriptionSpec]] = None  # ← List[SubscriptionSpec] 수신
) -> None:
```

**SubscriptionManager.register_component() 메서드**
```python
# 파일: subscription_manager.py:243-245
async def register_component(
    self,
    component_id: str,
    subscription: ComponentSubscription,  # ← ComponentSubscription 객체 기대
    component_ref: Any
) -> None:
```

### 2. 잘못된 데이터 전달
```python
# 파일: websocket_manager.py:598-603
if subscriptions and self._subscription_manager:
    await self._subscription_manager.register_component(
        component_id,
        subscriptions,  # ❌ List[SubscriptionSpec]를 ComponentSubscription으로 전달
        component_ref
    )
```

### 3. 타입 변환 요구사항
```python
# ComponentSubscription 구조 (websocket_types.py:352-359)
@dataclass
class ComponentSubscription:
    component_id: str
    subscriptions: List[SubscriptionSpec]  # ← 여기에 List[SubscriptionSpec]가 들어가야 함
    callback: Optional[Callable[[BaseWebSocketEvent], None]] = None
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    stream_filter: Optional[str] = None
```

---

## 🔧 수정 방안

### 올바른 ComponentSubscription 생성
```python
# websocket_manager.py:598-603 수정 필요
if subscriptions and self._subscription_manager:
    component_subscription = ComponentSubscription(
        component_id=component_id,
        subscriptions=subscriptions,
        callback=None,  # 또는 적절한 콜백
        stream_filter=None
    )

    await self._subscription_manager.register_component(
        component_id,
        component_subscription,  # ✅ 올바른 타입
        component_ref
    )
```

---

## 📝 코드 검토 체크리스트

### Level 1: 기본 타입 검증
- [ ] **Interface Contract 검사**: 메서드 시그니처의 타입 힌트 일관성
- [ ] **데이터 흐름 추적**: A → B → C로 전달되는 데이터의 타입 변환
- [ ] **런타임 오류 패턴**: `'list' object has no attribute 'X'` 형태의 에러

### Level 2: 아키텍처 일관성
- [ ] **Layer Boundary 검증**: Infrastructure 레이어 간 데이터 계약
- [ ] **Factory Pattern 확인**: 복잡한 객체 생성 로직의 위치
- [ ] **Dependency Direction**: DDD 원칙에 따른 의존성 방향

### Level 3: 시스템 통합성
- [ ] **End-to-End Flow**: 사용자 요청 → 내부 처리 → 응답의 전체 흐름
- [ ] **Error Propagation**: 에러가 적절한 레벨에서 처리되는지 확인
- [ ] **Resource Lifecycle**: 객체 생성/소멸 시점의 적절성

---

## 🧪 포괄적 유닛테스트 전략

### Test Suite 구조
```
tests/
├── unit/
│   ├── websocket_v6/
│   │   ├── core/
│   │   │   ├── test_websocket_manager.py
│   │   │   ├── test_websocket_client.py
│   │   │   └── test_websocket_types.py
│   │   ├── support/
│   │   │   ├── test_subscription_manager.py
│   │   │   └── test_format_utils.py
│   │   └── integration/
│   │       ├── test_manager_subscription_integration.py
│   │       └── test_end_to_end_flow.py
├── contract/
│   ├── test_interface_contracts.py
│   └── test_type_safety.py
└── system/
    ├── test_websocket_v6_system.py
    └── test_performance_benchmarks.py
```

### 1. Type Safety Tests (Contract Tests)

**test_interface_contracts.py**
```python
import pytest
from typing import get_type_hints
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.core.websocket_manager import WebSocketManager
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.support.subscription_manager import SubscriptionManager

class TestInterfaceContracts:
    """Interface Contract 검증"""

    def test_websocket_manager_register_component_signature(self):
        """WebSocketManager.register_component 시그니처 검증"""
        hints = get_type_hints(WebSocketManager.register_component)
        assert 'subscriptions' in hints
        # List[SubscriptionSpec] 타입 확인

    def test_subscription_manager_register_component_signature(self):
        """SubscriptionManager.register_component 시그니처 검증"""
        hints = get_type_hints(SubscriptionManager.register_component)
        assert 'subscription' in hints
        # ComponentSubscription 타입 확인

    def test_type_conversion_requirement(self):
        """타입 변환 요구사항 검증"""
        # List[SubscriptionSpec] → ComponentSubscription 변환 로직 존재 확인
        pass
```

### 2. Manager Integration Tests

**test_manager_subscription_integration.py**
```python
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

class TestManagerSubscriptionIntegration:
    """WebSocketManager ↔ SubscriptionManager 통합 테스트"""

    @pytest.mark.asyncio
    async def test_register_component_with_subscriptions(self):
        """구독 정보가 있는 컴포넌트 등록 테스트"""
        # Given: WebSocketManager와 SubscriptionManager 설정
        manager = await create_test_websocket_manager()
        subscription_specs = create_test_subscription_specs()
        component_ref = MagicMock()

        # When: 컴포넌트 등록
        await manager.register_component(
            component_id="test_component",
            component_ref=component_ref,
            subscriptions=subscription_specs
        )

        # Then: SubscriptionManager에 올바른 타입으로 전달되었는지 확인
        subscription_manager = manager._subscription_manager
        subscription_manager.register_component.assert_called_once()

        # 전달된 인자 검증
        call_args = subscription_manager.register_component.call_args
        assert call_args[0][0] == "test_component"  # component_id
        assert isinstance(call_args[0][1], ComponentSubscription)  # 올바른 타입
        assert call_args[0][1].subscriptions == subscription_specs  # 데이터 보존

    @pytest.mark.asyncio
    async def test_register_component_without_subscriptions(self):
        """구독 정보가 없는 컴포넌트 등록 테스트"""
        # SubscriptionManager.register_component이 호출되지 않아야 함
        pass

    @pytest.mark.asyncio
    async def test_component_subscription_creation(self):
        """ComponentSubscription 객체 생성 검증"""
        # 올바른 필드들이 설정되는지 확인
        pass
```

### 3. End-to-End Flow Tests

**test_end_to_end_flow.py**
```python
class TestWebSocketV6EndToEndFlow:
    """전체 흐름 통합 테스트"""

    @pytest.mark.asyncio
    async def test_websocket_client_subscribe_ticker_flow(self):
        """WebSocketClient.subscribe_ticker의 전체 흐름"""
        # Given: 실제 환경에 가까운 설정
        client = WebSocketClient("test_client")
        symbols = ["KRW-BTC", "KRW-ETH"]
        callback = MagicMock()

        # When: subscribe_ticker 호출
        await client.subscribe_ticker(
            symbols=symbols,
            callback=callback,
            stream_preference="snapshot_only"
        )

        # Then: 전체 체인이 성공적으로 작동
        # 1. SubscriptionSpec 생성 확인
        # 2. WebSocketManager 등록 확인
        # 3. SubscriptionManager에 올바른 타입으로 전달 확인
        # 4. 구독 상태 확인
        pass

    @pytest.mark.asyncio
    async def test_error_propagation_on_type_mismatch(self):
        """타입 불일치 시 에러 전파 테스트"""
        # 의도적으로 잘못된 타입을 전달하여 에러 처리 확인
        pass
```

### 4. Performance and Stress Tests

**test_performance_benchmarks.py**
```python
class TestWebSocketV6Performance:
    """성능 및 스트레스 테스트"""

    @pytest.mark.asyncio
    async def test_multiple_client_registration_performance(self):
        """다중 클라이언트 등록 성능 테스트"""
        # 100개의 클라이언트 동시 등록 시 타입 변환 오버헤드 측정
        pass

    @pytest.mark.asyncio
    async def test_subscription_manager_memory_usage(self):
        """구독 관리자의 메모리 사용량 테스트"""
        # ComponentSubscription 객체 생성/소멸 시 메모리 누수 확인
        pass
```

### 5. Regression Tests

**test_websocket_v6_regression.py**
```python
class TestWebSocketV6Regression:
    """회귀 테스트 (버그 재발 방지)"""

    @pytest.mark.asyncio
    async def test_list_object_has_no_attribute_subscriptions_fix(self):
        """'list' object has no attribute 'subscriptions' 버그 재발 방지"""
        # 구체적인 버그 상황을 재현하여 수정된 코드가 올바르게 작동하는지 확인
        manager = await create_test_websocket_manager()
        subscription_specs = [
            SubscriptionSpec(
                data_type=DataType.TICKER,
                symbols=["KRW-BTC"],
                stream_preference="snapshot_only"
            )
        ]

        # 이 호출이 성공해야 함 (이전에는 실패했음)
        await manager.register_component(
            component_id="regression_test",
            component_ref=MagicMock(),
            subscriptions=subscription_specs
        )

        # 성공 검증
        assert manager._subscription_manager.register_component.called
```

---

## 🚀 빠른 문제 검출 방법

### 1. 타입 검사 자동화
```bash
# mypy를 사용한 정적 타입 검사
mypy upbit_auto_trading/infrastructure/external_apis/upbit/websocket/ --strict
```

### 2. 런타임 타입 검증
```python
# 개발 환경에서 타입 검증 데코레이터 사용
from typing import runtime_checkable

@runtime_checkable
def validate_component_subscription(subscription):
    assert hasattr(subscription, 'subscriptions')
    assert hasattr(subscription, 'component_id')
    return True
```

### 3. 간단한 smoke test
```python
# 5분 내에 실행 가능한 기본 검증
async def websocket_v6_smoke_test():
    """WebSocket v6 기본 동작 검증"""
    client = WebSocketClient("smoke_test")
    try:
        await client.subscribe_ticker(
            symbols=["KRW-BTC"],
            callback=lambda x: None,
            stream_preference="snapshot_only"
        )
        return "✅ PASS"
    except Exception as e:
        return f"❌ FAIL: {e}"
```

---

## 🎯 핵심 검증 포인트

### 즉시 확인해야 할 항목
1. **websocket_manager.py:598-603** - ComponentSubscription 객체 생성 로직 추가
2. **subscription_manager.py:243** - 메서드 시그니처와 실제 호출 일치성
3. **websocket_client.py** - _register_with_manager 메서드의 데이터 전달 방식

### 장기적 개선 사항
1. **Type Safety 강화**: 모든 WebSocket v6 인터페이스에 strict typing 적용
2. **Contract Testing**: 컴포넌트 간 인터페이스 계약 자동 검증
3. **Integration Monitoring**: 운영 환경에서 타입 오류 실시간 감지

---

## 📚 참고 자료

### 관련 파일
- `websocket_manager.py:574-610` - 문제 발생 지점
- `subscription_manager.py:243-253` - 타입 불일치 지점
- `websocket_types.py:352-359` - ComponentSubscription 정의
- `websocket_client.py` - 전체 흐름의 시작점

### 테스트 실행 명령
```bash
# 전체 WebSocket v6 테스트 실행
pytest tests/unit/websocket_v6/ -v

# 계약 테스트만 실행
pytest tests/contract/ -v

# 회귀 테스트 실행
pytest tests/unit/websocket_v6/test_websocket_v6_regression.py -v
```

### 디버깅 로그 활성화
```bash
export UPBIT_LOG_SCOPE=verbose
export UPBIT_COMPONENT_FOCUS=WebSocketManager,SubscriptionManager
```

---

## 🏆 성공 기준

### 단기 목표 (1주 내)
- [ ] `'list' object has no attribute 'subscriptions'` 에러 완전 해결
- [ ] WebSocketClient.subscribe_ticker() 정상 동작 확인
- [ ] 기본 회귀 테스트 통과

### 중기 목표 (1개월 내)
- [ ] 전체 WebSocket v6 테스트 슈트 구축
- [ ] Type safety 100% 달성
- [ ] 성능 벤치마크 기준선 설정

### 장기 목표 (3개월 내)
- [ ] WebSocket v6 시스템 안정성 99.9% 달성
- [ ] 자동화된 contract testing 도입
- [ ] 실시간 아키텍처 검증 시스템 구축

---

**이 문서는 WebSocket v6 시스템의 타입 안전성과 아키텍처 일관성을 보장하기 위한 포괄적인 가이드입니다. 다음 개발자가 이 문제를 빠르게 이해하고 해결할 수 있도록 구체적인 실행 방안을 제시합니다.**
