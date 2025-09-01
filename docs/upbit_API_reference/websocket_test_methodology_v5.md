# 업비트 WebSocket API 테스트 방법론 v5.0

## 🎯 핵심 원칙
- **동적 Rate Limiter 통합** (REST API와 공유)
- **1파일 = 1데이터타입 = 7테스트** (관리 단순화)
- **표준 7테스트 템플릿** (일관성 보장)
- **실제 업비트 서버 통신** (완전 검증)
- **캔들 9종 완전 지원** (1s~240m)
- **SubscriptionManager v4.0 기반**

## 🔄 v5.0 주요 개선사항
- **동적 Rate Limiter 통합**: REST API와 WebSocket이 동일한 Rate Limiter 공유
- **Rate Limited 구독**: 모든 구독 요청에 Rate Limiting 적용
- **429 오류 자동 감지**: Rate Limit 초과 시 자동 백오프 및 복구
- **Conservative/Balanced/Aggressive 모드**: 상황에 맞는 동적 설정
- **향상된 성능 모니터링**: Rate Limiter 통계 및 상태 추적

## 📁 파일 구조
```
tests\infrastructure\test_external_apis\upbit
├── test_upbit_websocket_public_client_v2/
│   ├── conftest.py                      # pytest 공통 설정 + Rate Limiter 픽스처
│   ├── test01_ticker.py                 # 현재가 7테스트 (Rate Limited)
│   ├── test02_orderbook.py              # 호가 7테스트 (Rate Limited)
│   ├── test03_trade.py                  # 체결 7테스트 (Rate Limited)
│   ├── test04_candle.py                 # 캔들 7테스트 (9종, Rate Limited)
│   ├── test05_mixed_public.py           # Public 조합 7테스트
│   ├── test06_subscription_mgmt.py      # 구독 관리 7테스트
│   ├── test07_rate_limiter_integration.py # Rate Limiter 통합 테스트
│   └── test08_performance_optimization.py # 성능 최적화 테스트
└── test_upbit_websocket_private_client_v2/
    ├── conftest.py                      # pytest 공통 설정 + JWT 인증
    ├── test01_asset.py                  # 자산 7테스트 (Rate Limited)
    ├── test02_order.py                  # 주문 7테스트 (Rate Limited)
    ├── test03_mixed_private.py          # Private 조합 7테스트
    ├── test04_subscription_mgmt.py      # Private 구독 관리 7테스트
    ├── test05_authentication.py         # JWT 인증 테스트
    ├── test06_rate_limiter_integration.py # Rate Limiter 통합 테스트
    └── test07_security_compliance.py    # 보안 컴플라이언스 테스트
```

## 🧪 표준 7테스트 템플릿 (v5.0 Rate Limited)

### 개별 데이터 타입 (ticker/orderbook/trade/candle/asset/order)
```python
class TestDataTypeRateLimited:
    def test01_single_symbol_snapshot_rate_limited(self):
        """기본: KRW-BTC 스냅샷 요청 (Rate Limited)"""
        # Rate Limiter 상태 확인
        # 스냅샷 요청 실행
        # Rate Limiter 통계 검증

    def test02_multi_symbol_snapshot_rate_limited(self):
        """일괄: 전체 KRW 마켓 스냅샷 요청 (Rate Limited)"""
        # 대량 요청 시 Rate Limiting 동작 확인
        # 429 오류 처리 검증

    def test03_single_symbol_realtime_rate_limited(self):
        """실시간: KRW-BTC 실시간 스트림 (Rate Limited)"""
        # 실시간 구독 Rate Limiting 확인

    def test04_multi_symbol_realtime_rate_limited(self):
        """고부하: 전체 KRW 마켓 실시간 스트림 (Rate Limited)"""
        # 고부하 상황에서 Rate Limiter 성능 검증

    def test05_random_symbol_rotation_with_rate_limiting(self):
        """랜덤순회: 심볼+옵션 4시나리오 + Rate Limiting"""
        # 랜덤 순회 중 Rate Limiting 적용 확인

    def test06_snapshot_realtime_hybrid_rate_limited(self):
        """하이브리드: 스냅샷+실시간 혼합사용 (Rate Limited)"""
        # 혼합 사용 시 Rate Limiter 최적화 확인

    def test07_connection_error_recovery_with_rate_limiting(self):
        """복구: 연결오류 및 자동복구 + Rate Limiter 상태 복구"""
        # 연결 오류 복구 시 Rate Limiter 상태 검증
```

### Rate Limiter 통합 테스트
```python
class TestRateLimiterIntegration:
    def test01_dynamic_config_switching(self):
        """동적 설정: Conservative/Balanced/Aggressive 모드 전환"""

    def test02_rest_websocket_shared_limiter(self):
        """공유 Limiter: REST API와 WebSocket Rate Limiter 공유"""

    def test03_429_error_handling(self):
        """429 처리: Rate Limit 초과 시 자동 백오프"""

    def test04_performance_monitoring(self):
        """성능 모니터링: Rate Limiter 통계 및 상태 추적"""

    def test05_adaptive_strategy_verification(self):
        """적응형 전략: 네트워크 상황에 따른 자동 조정"""

    def test06_rate_limiter_cleanup(self):
        """정리: Rate Limiter 자원 정리 및 메모리 관리"""

    def test07_concurrent_client_isolation(self):
        """격리: 여러 클라이언트 간 Rate Limiter 격리"""
```

## 🔧 conftest.py 설정 (v5.0 Rate Limiter 통합)

### Public WebSocket 테스트용
```python
import pytest
import asyncio
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5.upbit_websocket_public_client import (
    UpbitWebSocketPublicV5
)
from upbit_auto_trading.infrastructure.external_apis.upbit.dynamic_rate_limiter_wrapper import (
    DynamicConfig, AdaptiveStrategy
)

@pytest.fixture
async def websocket_client():
    """기본 WebSocket 클라이언트 (동적 Rate Limiter 활성화)"""
    client = UpbitWebSocketPublicV5(use_dynamic_limiter=True)
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()

@pytest.fixture
async def conservative_client():
    """Conservative 모드 WebSocket 클라이언트"""
    config = DynamicConfig(strategy=AdaptiveStrategy.CONSERVATIVE)
    client = UpbitWebSocketPublicV5(use_dynamic_limiter=True, dynamic_config=config)
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()

@pytest.fixture
async def aggressive_client():
    """Aggressive 모드 WebSocket 클라이언트"""
    config = DynamicConfig(strategy=AdaptiveStrategy.AGGRESSIVE)
    client = UpbitWebSocketPublicV5(use_dynamic_limiter=True, dynamic_config=config)
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()

@pytest.fixture
def rate_limiter_stats():
    """Rate Limiter 통계 수집 픽스처"""
    stats = {"requests": 0, "rate_limited": 0, "errors": 0}
    return stats

@pytest.fixture
def krw_symbols():
    """KRW 마켓 심볼 목록"""
    return ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA', 'KRW-DOT']

@pytest.fixture
def all_krw_symbols():
    """전체 KRW 마켓 심볼 (실제 API에서 로드)"""
    # 실제 마켓 API에서 동적 로드
    return get_all_krw_markets()

@pytest.fixture
def candle_types():
    """지원되는 캔들 타입 목록"""
    return ['1s', '1m', '3m', '5m', '10m', '15m', '30m', '60m', '240m']
```

### Private WebSocket 테스트용
```python
@pytest.fixture
async def private_websocket_client():
    """Private WebSocket 클라이언트 (JWT 인증 + Rate Limiter)"""
    client = UpbitWebSocketPrivateV5(use_dynamic_limiter=True)
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()

@pytest.fixture
def api_credentials():
    """API 인증 정보 (환경변수에서 로드)"""
    import os
    return {
        "access_key": os.getenv("UPBIT_ACCESS_KEY"),
        "secret_key": os.getenv("UPBIT_SECRET_KEY")
    }
```

## 📊 성능 기준 (v5.0 Rate Limiter 포함)
```python
PERFORMANCE_CRITERIA = {
    "connection_time": 2.0,              # 연결 < 2초 (Rate Limiter 초기화 포함)
    "subscription_efficiency": 85,        # 구독효율 > 85%
    "rate_limiter_overhead": 0.1,        # Rate Limiter 오버헤드 < 100ms
    "adaptive_response_time": 1.0,       # 적응형 조정 < 1초
    "memory_usage_mb": 50,               # 메모리 사용량 < 50MB
    "rate_limit_compliance": 100,        # Rate Limit 준수율 100%
}
```

## 🚀 실행 명령어 (v5.0)

### 개별 테스트 (Rate Limiter 통합)
```powershell
# Public WebSocket 테스트
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_websocket_public_client_v2/test01_ticker.py -v
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_websocket_public_client_v2/test07_rate_limiter_integration.py -v

# Private WebSocket 테스트
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_websocket_private_client_v2/test01_asset.py -v
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_websocket_private_client_v2/test06_rate_limiter_integration.py -v

# Rate Limiter 성능 테스트
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_websocket_public_client_v2/test08_performance_optimization.py -v
```

### 통합 테스트
```powershell
# Public WebSocket 전체 (Rate Limiter 포함)
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_websocket_public_client_v2/ -v

# Private WebSocket 전체 (Rate Limiter 포함)
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_websocket_private_client_v2/ -v

# Rate Limiter 통합 테스트만
pytest tests/infrastructure/test_external_apis/upbit/ -k "rate_limiter" -v

# 전체 WebSocket 테스트 (v5.0)
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_websocket_*_v2/ -v
```

## 🔍 검증 패턴 (v5.0 Rate Limiter 검증 포함)

### Rate Limiter 통합 검증
```python
async def test_rate_limiter_integration(self, websocket_client, rate_limiter_stats):
    # Given: Rate Limiter가 활성화된 WebSocket 클라이언트
    assert websocket_client._rate_limiter is not None

    # When: 여러 구독 요청 실행
    subscription_id = await websocket_client.subscribe_ticker(['KRW-BTC'])

    # Then: Rate Limiter 통계 확인
    rate_limiter = await websocket_client._ensure_rate_limiter()
    stats = rate_limiter.get_stats()

    assert stats['total_requests'] > 0
    assert stats['rate_limited_count'] >= 0
    assert subscription_id is not None
```

### 429 오류 처리 검증
```python
async def test_429_error_handling(self, aggressive_client):
    # Given: Aggressive 모드로 높은 요청률 설정

    # When: 연속 요청으로 Rate Limit 도달 시도
    tasks = []
    for i in range(20):
        task = aggressive_client.subscribe_ticker([f'KRW-BTC'])
        tasks.append(task)

    # Then: 429 오류 자동 처리 확인
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Rate Limiter가 자동으로 백오프했는지 확인
    rate_limiter = await aggressive_client._ensure_rate_limiter()
    assert rate_limiter._dynamic_monitoring._backoff_active
```

## 🎯 테스트 목표 (v5.0)
- **WebSocket Rate Limiter 통합 기능 완전 검증**
- **REST API와 WebSocket Rate Limiter 공유 확인**
- **동적 설정 모드별 성능 차이 측정**
- **429 오류 자동 처리 및 복구 메커니즘 검증**
- **캔들 9종 완전 지원 + Rate Limiting 확인**
- **Private WebSocket JWT 인증 + Rate Limiting 조합 검증**
- **대용량 구독 시 Rate Limiter 성능 최적화 확인**

## 🔄 Rate Limiter 테스트 시나리오

### 1. 기본 통합 테스트
- Rate Limiter 초기화 및 설정 확인
- 구독 요청에 Rate Limiting 적용 검증
- REST API와 Rate Limiter 공유 확인

### 2. 성능 최적화 테스트
- Conservative/Balanced/Aggressive 모드 성능 비교
- 적응형 전략 동작 확인
- 네트워크 상황별 자동 조정 검증

### 3. 오류 처리 테스트
- 429 오류 감지 및 자동 백오프
- 연결 오류 시 Rate Limiter 상태 복구
- 메모리 누수 및 자원 정리 확인

### 4. 대용량 테스트
- 다중 심볼 동시 구독 시 Rate Limiting
- 장시간 실행 시 Rate Limiter 안정성
- 메모리 사용량 및 성능 모니터링

---

## 🆕 v5.0 주요 특징 요약

1. **동적 Rate Limiter 완전 통합**
   - REST API와 WebSocket 통합 Rate Limiting
   - Conservative/Balanced/Aggressive 모드 지원

2. **향상된 테스트 커버리지**
   - Rate Limiter 전용 테스트 추가
   - 성능 최적화 테스트 강화

3. **실제 운영 환경 대응**
   - 429 오류 자동 처리
   - 적응형 백오프 전략

4. **보안 및 안정성 강화**
   - JWT 토큰 자동 갱신
   - 메모리 누수 방지

**v5.0: 동적 Rate Limiter 통합 + 운영 환경 최적화**
