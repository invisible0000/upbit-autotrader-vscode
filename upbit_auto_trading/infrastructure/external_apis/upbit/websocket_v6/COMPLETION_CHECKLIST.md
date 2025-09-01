# 🔧 WebSocket v6 개발 체크리스트

## 📋 즉시 시작 가능한 작업 목록

### 🚨 **우선순위 1: types.py 필드 보완** (30분 작업)

**현재 문제**: types.py 이벤트 클래스에 models.py 대비 필드 누락

**해결 방법**:
```python
# 📁 types.py에 추가 필요한 필드들
@dataclass
class TickerEvent(BaseWebSocketEvent):
    # 현재 있는 필드들 유지 +
    opening_price: Decimal = field(default_factory=lambda: Decimal('0'))
    signed_change_price: Decimal = field(default_factory=lambda: Decimal('0'))
    signed_change_rate: Decimal = field(default_factory=lambda: Decimal('0'))
    acc_trade_volume_24h: Decimal = field(default_factory=lambda: Decimal('0'))
    acc_trade_price_24h: Decimal = field(default_factory=lambda: Decimal('0'))
    highest_52_week_price: Decimal = field(default_factory=lambda: Decimal('0'))
    lowest_52_week_price: Decimal = field(default_factory=lambda: Decimal('0'))
    market_state: str = 'ACTIVE'
    # ... models.py의 모든 필드 참조하여 추가
```

**검증**: models.py의 `convert_dict_to_v6_event()` 함수와 호환 확인

---

### 🚨 **우선순위 2: WebSocketClientProxy 구현** (2-3시간 작업)

**새 파일**: `websocket_client_proxy.py`

```python
"""
WebSocket 클라이언트 프록시
========================

컴포넌트가 사용할 간단한 인터페이스 제공
Zero Configuration으로 즉시 사용 가능
"""

import asyncio
import weakref
from typing import List, Callable, Optional, Dict, Any
from dataclasses import dataclass

from .global_websocket_manager import get_global_websocket_manager_sync
from .types import TickerEvent, OrderbookEvent, TradeEvent

class WebSocketClientProxy:
    """컴포넌트별 WebSocket 프록시"""

    def __init__(self, component_id: str):
        self.component_id = component_id
        self._manager = None
        self._subscriptions = {}

    async def subscribe_ticker(
        self,
        symbols: List[str],
        callback: Callable[[TickerEvent], None]
    ):
        """현재가 구독"""
        manager = await self._get_manager()
        # TODO: 글로벌 매니저에 구독 요청 위임

    async def get_ticker_snapshot(self, symbols: List[str]):
        """현재가 스냅샷"""
        # TODO: REST API를 통한 스냅샷 요청

    async def cleanup(self):
        """리소스 정리"""
        # TODO: 모든 구독 해제 및 정리

    async def _get_manager(self):
        """매니저 인스턴스 획득"""
        if self._manager is None:
            self._manager = get_global_websocket_manager_sync()
        return self._manager
```

---

### 🔧 **우선순위 3: JWT Manager 구현** (1-2시간 작업)

**새 파일**: `jwt_manager.py`

```python
"""
JWT 토큰 자동 갱신 관리자
=====================

Private WebSocket을 위한 JWT 토큰 생명주기 관리
80% 만료 시점 자동 갱신, 실패 시 REST 폴백
"""

import asyncio
import time
from typing import Optional
from datetime import datetime, timedelta

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import UpbitAuthenticator
from upbit_auto_trading.infrastructure.logging import create_component_logger

class JWTManager:
    """JWT 토큰 자동 갱신 관리자"""

    def __init__(self):
        self.logger = create_component_logger("JWTManager")
        self._current_token = None
        self._token_expiry = None
        self._refresh_task = None

    async def get_valid_token(self) -> Optional[str]:
        """유효한 JWT 토큰 반환"""
        # TODO: 토큰 유효성 체크 및 필요시 갱신

    async def _auto_refresh_loop(self):
        """토큰 자동 갱신 루프"""
        # TODO: 80% 만료 시점에 자동 갱신

    def start_auto_refresh(self):
        """자동 갱신 시작"""
        # TODO: 백그라운드 태스크 시작
```

---

### 📊 **우선순위 4: 통합 테스트** (1시간 작업)

**새 파일**: `test_complete_integration.py`

```python
"""
v6 WebSocket 완전 통합 테스트
===========================

전체 시스템의 end-to-end 동작 검증
"""

import asyncio
import pytest
from decimal import Decimal

from .websocket_client_proxy import WebSocketClientProxy
from .global_websocket_manager import get_global_websocket_manager_sync

async def test_complete_workflow():
    """완전한 워크플로우 테스트"""

    # 1. 프록시 생성
    proxy = WebSocketClientProxy("test_component")

    # 2. 구독 요청
    received_events = []

    def on_ticker(event):
        received_events.append(event)

    await proxy.subscribe_ticker(["KRW-BTC"], on_ticker)

    # 3. 데이터 수신 대기 (3초)
    await asyncio.sleep(3)

    # 4. 검증
    assert len(received_events) > 0
    assert received_events[0].symbol == "KRW-BTC"
    assert received_events[0].trade_price > Decimal('0')

    # 5. 정리
    await proxy.cleanup()

    print("✅ 완전 통합 테스트 성공!")

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
```

---

## 🎯 완성 후 기대 효과

### **개발자 사용 경험**
```python
# 🎉 완성된 v6 시스템 사용법 (매우 간단!)

from websocket_v6 import WebSocketClientProxy

async def my_chart_component():
    # 1줄로 프록시 생성
    ws = WebSocketClientProxy("chart_btc")

    # 1줄로 구독 시작 (전역 관리됨)
    await ws.subscribe_ticker(
        ["KRW-BTC"],
        lambda event: update_chart(event.trade_price)
    )

    # 스냅샷도 간단히
    snapshot = await ws.get_ticker_snapshot(["KRW-BTC"])

    # 자동 정리 (WeakRef + cleanup)
    await ws.cleanup()
```

### **시스템 성능**
- ✅ **60% 대역폭 절약** (SIMPLE + 압축)
- ✅ **구독 충돌 0건** (중앙 관리)
- ✅ **메모리 누수 0건** (자동 정리)
- ✅ **99.9% 연결 안정성** (자동 재연결)

---

## ⚡ 빠른 완성 팁

### **types.py 보완 시**
1. `models.py`의 각 클래스 필드를 복사
2. `field(default_factory=lambda: Decimal('0'))` 패턴 사용
3. Optional 필드는 `Optional[str] = None` 사용

### **proxy 구현 시**
1. `global_websocket_manager`에 구독 요청 위임
2. 콜백 등록은 `component_id` 기준으로 관리
3. `WeakRef` 사용해서 자동 정리 구현

### **테스트 시**
1. Mock 데이터로 먼저 검증
2. 실제 업비트 연결로 최종 확인
3. 자동 정리 동작 반드시 확인

---

## 🏁 완성 확인 방법

```python
# 최종 완성 검증 스크립트
async def verify_v6_complete():
    """v6 시스템 완성 검증"""

    # 1. 프록시 생성 테스트
    proxy = WebSocketClientProxy("verification")

    # 2. 구독 + 데이터 수신 테스트
    received = []
    await proxy.subscribe_ticker(["KRW-BTC"], received.append)
    await asyncio.sleep(5)

    # 3. 검증
    assert len(received) > 0  # 데이터 수신됨
    assert received[0].symbol == "KRW-BTC"  # 올바른 심볼
    assert hasattr(received[0], 'signed_change_rate')  # 새 필드 존재

    # 4. 정리 테스트
    await proxy.cleanup()

    print("🎉 v6 WebSocket 시스템 100% 완성!")

# 실행: asyncio.run(verify_v6_complete())
```

---

**💡 완성 후**: 이 시스템은 업비트 WebSocket의 모든 문제를 해결하고, 개발자 경험을 극대화한 완벽한 솔루션이 됩니다! 🚀
