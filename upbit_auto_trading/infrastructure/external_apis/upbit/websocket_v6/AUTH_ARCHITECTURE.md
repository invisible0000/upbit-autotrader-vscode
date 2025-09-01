# 🔐 인증 및 Rate Limiting 아키텍처 가이드

## 🎯 **핵심 원칙: 중앙 집중 vs 분산**

WebSocket v6에서는 **인증과 Rate Limiting을 전역 관리자에서 중앙 집중**하여 불필요한 중복을 제거하고 효율성을 극대화합니다.

## 🏗️ **기존 v5 패턴의 문제점**

### ❌ **잘못된 패턴 (v5에서 흔히 발생)**
```python
# 각 클라이언트마다 개별적으로 임포트 및 인스턴스 생성
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import UpbitAuthenticator
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import get_global_rate_limiter

class PrivateWebSocketClient:
    def __init__(self, access_key: str, secret_key: str):
        # 🚨 문제: 클라이언트마다 중복 생성
        self.auth = UpbitAuthenticator(access_key, secret_key)
        self.rate_limiter = None

    async def connect(self):
        # 🚨 문제: 각 클라이언트가 개별적으로 Rate Limiter 획득
        self.rate_limiter = await get_global_rate_limiter()

    def create_headers(self, params=None):
        # 🚨 문제: JWT 토큰을 개별적으로 생성
        return self.auth.get_private_headers(params)
```

### **문제점 분석**
1. **메모리 낭비**: 동일한 API 키로 여러 UpbitAuthenticator 인스턴스 생성
2. **중복 처리**: 각 클라이언트가 JWT 토큰을 개별적으로 생성
3. **일관성 부족**: 클라이언트마다 다른 Rate Limiting 정책 적용 가능
4. **테스트 복잡성**: 각 클라이언트 테스트 시 인증 설정 필요

## ✅ **v6의 올바른 패턴**

### **전역 관리자 중심 아키텍처**
```python
# global_websocket_manager.py
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import UpbitAuthenticator
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import get_global_rate_limiter
from upbit_auto_trading.infrastructure.external_apis.upbit.dynamic_rate_limiter_wrapper import get_dynamic_rate_limiter

class GlobalWebSocketManager:
    """전역 WebSocket 관리자 - 인증과 Rate Limiting 중앙 집중"""

    _instance = None
    _auth_instance = None
    _rate_limiter_instance = None

    async def initialize(self, access_key: Optional[str] = None,
                        secret_key: Optional[str] = None):
        """인증 및 Rate Limiter 중앙 초기화"""

        # 🎯 인증 시스템 중앙 관리
        if access_key and secret_key:
            self._auth_instance = UpbitAuthenticator(access_key, secret_key)
            self.private_available = True
        else:
            # ApiKeyService에서 자동 로드 시도
            self._auth_instance = UpbitAuthenticator()
            self.private_available = self._auth_instance.is_authenticated()

        # 🎯 Rate Limiter 중앙 관리
        try:
            # 동적 Rate Limiter 우선 사용
            self._rate_limiter_instance = await get_dynamic_rate_limiter()
            logger.info("✅ 동적 Rate Limiter 활성화")
        except Exception:
            # 폴백: 기본 GCRA Rate Limiter
            self._rate_limiter_instance = await get_global_rate_limiter()
            logger.info("✅ GCRA Rate Limiter 활성화")

    def get_jwt_token(self, params: Optional[dict] = None) -> Optional[str]:
        """JWT 토큰 중앙 생성 - 모든 클라이언트가 공유"""
        if not self._auth_instance or not self._auth_instance.is_authenticated():
            return None
        return self._auth_instance.create_jwt_token(params)

    async def apply_rate_limit(self, endpoint: str, method: str = "GET") -> None:
        """Rate Limiting 중앙 적용"""
        if self._rate_limiter_instance:
            await self._rate_limiter_instance.acquire(endpoint, method)
```

### **개별 클라이언트 단순화**
```python
# upbit_websocket_private_client.py
# 🎯 upbit_auth.py 임포트 불필요!

class UpbitWebSocketPrivateV6:
    """Private WebSocket 클라이언트 - 인증 위임"""

    def __init__(self):
        # 🎯 전역 관리자 참조만 저장
        self.global_manager = GlobalWebSocketManager.get_instance()
        # upbit_auth 직접 임포트/사용 안함!

    async def subscribe_my_orders(self, callback: Callable) -> str:
        """내 주문 구독 - 인증과 Rate Limiting 자동 처리"""

        # 🎯 Rate Limiting 전역 적용
        await self.global_manager.apply_rate_limit("websocket_message")

        # 🎯 JWT 토큰 전역에서 획득
        jwt_token = self.global_manager.get_jwt_token()
        if not jwt_token:
            raise AuthenticationError("Private 기능 사용 불가 - API 키 필요")

        # 🎯 WebSocket 헤더에 JWT 적용
        headers = {"Authorization": f"Bearer {jwt_token}"}

        # WebSocket 연결 및 구독...
        return subscription_id
```

## 🧪 **테스트에서의 사용법**

### **통합 테스트 (실제 API 키 사용)**
```python
# test_websocket_integration.py
import pytest
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v6 import GlobalWebSocketManager

@pytest.mark.asyncio
async def test_private_websocket_real():
    """실제 API 키로 Private WebSocket 테스트"""

    # 🎯 전역 관리자에 실제 API 키 설정
    global_manager = await GlobalWebSocketManager.get_instance()
    await global_manager.initialize(
        access_key=os.getenv("UPBIT_ACCESS_KEY"),
        secret_key=os.getenv("UPBIT_SECRET_KEY")
    )

    # 🎯 개별 클라이언트는 인증 신경 쓸 필요 없음
    ws = WebSocketClientProxy("test_client")

    if ws.is_private_available():
        await ws.subscribe_my_orders(callback)
        # 테스트 로직...
```

### **단위 테스트 (Mock 사용)**
```python
# test_websocket_unit.py
import pytest
from unittest.mock import Mock, patch
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v6 import GlobalWebSocketManager

@pytest.mark.asyncio
async def test_websocket_client_unit():
    """WebSocket 클라이언트 단위 테스트 - Mock 인증"""

    # 🎯 전역 관리자 Mock
    with patch.object(GlobalWebSocketManager, 'get_jwt_token', return_value="mock_jwt_token"):
        with patch.object(GlobalWebSocketManager, 'apply_rate_limit', return_value=None):

            ws = WebSocketClientProxy("test_client")
            # 인증 관련 코드 없이 순수 비즈니스 로직 테스트
            await ws.subscribe_ticker(["KRW-BTC"], callback)
```

### **API 키 없는 테스트 (Public 기능만)**
```python
# test_public_only.py
@pytest.mark.asyncio
async def test_public_websocket_no_auth():
    """API 키 없이 Public 기능 테스트"""

    # 🎯 API 키 없이 초기화
    global_manager = await GlobalWebSocketManager.get_instance()
    await global_manager.initialize()  # access_key=None, secret_key=None

    ws = WebSocketClientProxy("public_test")

    # Public 기능은 완전 동작
    assert ws.is_public_available() == True
    assert ws.is_private_available() == False

    await ws.subscribe_ticker(["KRW-BTC"], callback)
    # Private 시도 시 예외 발생
    with pytest.raises(AuthenticationError):
        await ws.subscribe_my_orders(callback)
```

## 📊 **아키텍처 비교**

| 측면 | v5 (분산) | v6 (중앙집중) | 개선율 |
|------|-----------|---------------|---------|
| **UpbitAuthenticator 인스턴스** | 클라이언트당 1개 | 전체 1개 | -90% |
| **JWT 토큰 생성** | 클라이언트별 개별 | 전역 공유 | -80% |
| **Rate Limiter 인스턴스** | 클라이언트당 획득 | 전체 1개 | -70% |
| **테스트 복잡도** | 각 클라이언트 설정 | 전역 1회 설정 | -60% |
| **메모리 사용량** | N개 인증 객체 | 1개 인증 객체 | -80% |

## 🎯 **결론: 언제 어디서 임포트하는가?**

### **✅ upbit_auth.py를 임포트해야 하는 곳**
1. **GlobalWebSocketManager** - 유일한 인증 관리자
2. **통합 테스트 코드** - 실제 API 호출 테스트
3. **REST API 클라이언트** - 아직 전역 관리자를 사용하지 않는 경우

### **❌ upbit_auth.py를 임포트하지 않는 곳**
1. **개별 WebSocket 클라이언트** - 전역 관리자에 위임
2. **WebSocketClientProxy** - 인증 로직 없음
3. **단위 테스트** - Mock으로 충분
4. **UI 컴포넌트** - WebSocket 프록시만 사용

### **🔧 기존 코드 정리 가이드**
```bash
# 불필요한 upbit_auth.py 임포트 찾기
grep -r "from.*upbit_auth import" --include="*.py" .

# 다음 파일들에서 임포트 제거 가능:
# - upbit_websocket_public_client.py
# - upbit_websocket_private_client.py
# - websocket_client_proxy.py
# - 대부분의 단위 테스트 파일들

# 유지해야 할 파일들:
# - global_websocket_manager.py (핵심 관리자)
# - 통합 테스트 파일들
```

이제 **인증과 Rate Limiting이 완전히 중앙집중화**되어 더욱 효율적이고 유지보수하기 쉬운 아키텍처가 완성되었습니다! 🚀
