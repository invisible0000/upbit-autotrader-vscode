# 업비트 REST API Private 테스트 방법론 v1.0

## 🎯 핵심 원칙
- **DRY-RUN 우선 = 안전성 최우선** (모든 주문은 기본 dry_run=True)
- **실제 거래 API 검증** (인증, 주문, 취소 안전 테스트)
- **계층별 단계적 검증** (초기화 → 조회 → 주문 → 고급 기능)
- **Given-When-Then 패턴** (일관성 보장)
- **Rate Limiter 동적 조정 검증** (429 오류 대응 테스트)

## 🚨 안전 규칙 (Critical Safety Rules)
- **모든 주문은 현재가 +20% 이상의 안전한 가격**
- **5,000원 이상 주문 금액 보장 (업비트 최소 기준)**
- **체결 방지를 위한 높은 가격 설정**
- **테스트 후 확실한 주문 취소로 안전성 보장**
- **실제 거래 금지: dry_run=False는 명시적 2단계 확인 후에만**

## 📁 파일 구조
```
tests\infrastructure\test_external_apis\upbit\test_upbit_private_client_v2
├── conftest.py                        # pytest 공통 설정 및 안전 픽스처
├── test_01_initialization.py          # 클라이언트 초기화 및 인증 테스트
├── test_02_accounts.py                # 계좌 정보 조회 실제 테스트
├── test_03_orders_basic.py            # 기본 주문 조회 API 실제 테스트
├── test_04_orders_dry_run.py          # DRY-RUN 주문 생성/취소 테스트
├── test_05_orders_real_safe.py        # 실제 주문 안전 테스트 (Phase 1-3 통합)
├── test_06_rate_limiter_dynamic.py    # 동적 Rate Limiter 실제 동작 테스트
├── test_07_advanced_features.py       # 고급 기능 (일괄 취소, 체결 내역)
└── run_all_tests.py                   # 통합 테스트 실행 파일
```

## 🧪 표준 테스트 패턴

### DRY-RUN 우선 테스트 (핵심 안전장치)
```python
class TestUpbitPrivateClientDryRunSafe:
    @pytest.mark.asyncio
    @pytest.mark.dry_run_safe
    async def test_dry_run_order_creation(self, safe_real_client):
        """DRY-RUN: 주문 생성 시뮬레이션"""
        # Given: DRY-RUN 모드 클라이언트
        assert safe_real_client.is_dry_run_enabled()

        # When: 주문 생성 시도
        result = await safe_real_client.place_order(...)

        # Then: DRY-RUN 결과 검증
        assert result['dry_run'] == True

    @pytest.mark.asyncio
    @pytest.mark.dry_run_safe
    async def test_dry_run_order_cancellation(self, safe_real_client):
        """DRY-RUN: 주문 취소 시뮬레이션"""
```

### 실제 API 안전 테스트 (고가격 체결 방지)
```python
class TestUpbitPrivateClientRealSafe:
    @pytest.mark.asyncio
    @pytest.mark.real_api
    @pytest.mark.safe_order
    async def test_real_safe_order_lifecycle(self, safe_real_client, public_client):
        """실제: 안전한 주문 생성-조회-취소 라이프사이클"""
        # Given: 현재가 +25% 안전 가격 계산
        safe_price = await self._calculate_safe_price(public_client, market='KRW-BTC')

        # When: 안전한 주문 생성 (체결 불가능한 가격)
        order_result = await safe_real_client.place_order(
            market='KRW-BTC',
            side='ask',
            ord_type='limit',
            volume=Decimal('0.001'),
            price=safe_price,
            dry_run=False  # 실제 주문이지만 안전함
        )

        # Then: 주문 생성 검증 및 안전 취소
        assert 'uuid' in order_result
        await self._safe_cleanup_order(safe_real_client, order_result['uuid'])

    async def _calculate_safe_price(self, public_client, market='KRW-BTC', premium=0.25):
        """현재가 대비 안전한 가격 계산 (체결 방지)"""

    async def _safe_cleanup_order(self, client, order_uuid):
        """안전한 주문 정리"""
```

### 동적 Rate Limiter 실제 동작 테스트
```python
class TestUpbitPrivateClientRateLimiterDynamic:
    @pytest.mark.asyncio
    @pytest.mark.real_api
    @pytest.mark.rate_limiter
    async def test_dynamic_rate_limiter_adaptation(self, safe_real_client):
        """실제: 동적 Rate Limiter 429 대응 검증"""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    @pytest.mark.rate_limiter
    async def test_rate_limiter_recovery(self, safe_real_client):
        """실제: Rate Limiter 점진적 복구 검증"""
```

### 인증 및 초기화 테스트
```python
class TestUpbitPrivateClientInitialization:
    @pytest.mark.asyncio
    async def test_client_authentication_real(self, real_credentials):
        """실제: 클라이언트 인증 검증"""

    @pytest.mark.asyncio
    async def test_dry_run_mode_default(self):
        """기본: DRY-RUN 모드 기본 활성화 검증"""

    @pytest.mark.asyncio
    async def test_dynamic_limiter_integration(self, safe_real_client):
        """실제: 동적 Rate Limiter 통합 검증"""
```

## 📊 지원 API 카테고리

### 인증 및 초기화 (Initialization)
- **authentication**: 인증 토큰 검증
- **client_setup**: 클라이언트 초기화
- **dry_run_config**: DRY-RUN 모드 설정
- **rate_limiter_setup**: 동적 Rate Limiter 설정

### 계좌 관리 (Account Management)
- **accounts**: 전체 계좌 정보 조회
- **balances**: 잔고 조회 및 검증
- **orders_chance**: 주문 가능 정보 조회

### 주문 관리 (Order Management) - 3단계 안전성
1. **DRY-RUN 테스트**: 모든 주문 시뮬레이션
2. **안전 실제 테스트**: 고가격 체결 방지 주문
3. **조회 기능 테스트**: 주문 상태 조회 검증

### 주문 API 타입
- **place_order**: 주문 생성 (DRY-RUN 우선)
- **get_order**: 특정 주문 조회
- **get_orders**: 주문 목록 조회
- **get_open_orders**: 체결 대기 주문 조회
- **get_closed_orders**: 완료된 주문 조회
- **cancel_order**: 개별 주문 취소
- **cancel_orders_by_ids**: ID별 일괄 취소
- **batch_cancel_orders**: 통화별 일괄 취소

### 거래 내역 (Trading History)
- **get_trades_history**: 거래 체결 내역 조회

### 고급 기능 (Advanced Features)
- **batch_operations**: 일괄 처리 기능
- **error_recovery**: 에러 복구 메커니즘
- **performance_monitoring**: 성능 모니터링

## 🔧 conftest.py 핵심 픽스처

### 안전한 실제 클라이언트 픽스처 (핵심)
```python
@pytest_asyncio.fixture
async def safe_real_client():
    """안전한 실제 클라이언트 (DRY-RUN 기본)"""
    access_key = "your_access_key"      # 실제 API 키로 교체
    secret_key = "your_secret_key"      # 실제 시크릿 키로 교체

    client = UpbitPrivateClient(
        access_key=access_key,
        secret_key=secret_key,
        dry_run=True,  # 기본값: 안전 모드
        use_dynamic_limiter=True
    )
    yield client
    await client.close()

@pytest_asyncio.fixture
async def real_trade_client():
    """실제 거래 클라이언트 (신중한 사용 필요)"""
    access_key = "your_access_key"      # 실제 API 키로 교체
    secret_key = "your_secret_key"      # 실제 시크릿 키로 교체

    client = UpbitPrivateClient(
        access_key=access_key,
        secret_key=secret_key,
        dry_run=False,  # 실제 거래 모드 (주의!)
        use_dynamic_limiter=True
    )
    yield client
    await client.close()

@pytest.fixture
def real_credentials():
    """실제 인증 정보 픽스처"""
    return {
        'access_key': "your_access_key",    # 실제 API 키로 교체
        'secret_key': "your_secret_key"     # 실제 시크릿 키로 교체
    }
```

### 안전성 검증 헬퍼 함수
```python
async def calculate_safe_order_price(public_client, market='KRW-BTC', premium=0.25):
    """체결 방지를 위한 안전한 주문 가격 계산"""
    ticker = await public_client.get_ticker(market)
    current_price = int(ticker[market]['trade_price'])

    # 호가 단위 조회
    instruments = await public_client.get_orderbook_instruments(markets=market)
    tick_size = int(instruments[market]['tick_size'])

    # 안전 가격 계산 (현재가 + 프리미엄)
    safe_price = int(current_price * (1 + premium))
    safe_price = ((safe_price // tick_size) + 1) * tick_size

    return safe_price, current_price, tick_size

async def ensure_safe_order_cleanup(client, order_uuids):
    """테스트 후 안전한 주문 정리"""
    for uuid in order_uuids:
        try:
            await client.cancel_order(uuid=uuid)
            print(f"✅ 안전 정리: {uuid[:8]}...")
        except Exception as e:
            print(f"⚠️ 정리 실패: {uuid[:8]}... - {e}")

def validate_dry_run_response(response):
    """DRY-RUN 응답 검증"""
    assert isinstance(response, dict)
    assert response.get('dry_run') == True
    assert 'simulated_result' in response

def validate_real_order_response(response):
    """실제 주문 응답 검증"""
    assert isinstance(response, dict)
    assert 'uuid' in response
    assert 'state' in response
    assert response.get('dry_run') != True
```

## 📋 안전성 검증 패턴

### DRY-RUN 안전성 검증
```python
@pytest.mark.asyncio
@pytest.mark.dry_run_safe
async def test_dry_run_safety_verification(self, safe_real_client):
    """DRY-RUN: 안전성 검증 패턴"""
    # Given: DRY-RUN 모드 확인
    assert safe_real_client.is_dry_run_enabled()

    # When: 주문 시뮬레이션
    result = await safe_real_client.place_order(
        market='KRW-BTC',
        side='bid',
        ord_type='limit',
        volume=Decimal('0.001'),
        price=Decimal('100000000')  # 높은 가격
    )

    # Then: DRY-RUN 결과 검증
    validate_dry_run_response(result)
    print(f"✅ DRY-RUN 주문 시뮬레이션: {result.get('simulated_result')}")
```

### 실제 주문 안전성 검증
```python
@pytest.mark.asyncio
@pytest.mark.real_api
@pytest.mark.safe_order
async def test_real_order_safety_verification(self, safe_real_client, public_client):
    """실제: 안전한 주문 검증 패턴"""
    # Given: 안전 가격 계산
    safe_price, current_price, tick_size = await calculate_safe_order_price(
        public_client, market='KRW-BTC', premium=0.30  # 30% 프리미엄
    )

    volume = Decimal('5000') / Decimal(str(safe_price))  # 5000원 상당
    volume = volume.quantize(Decimal('0.00000001'))

    print(f"📊 안전 주문 정보:")
    print(f"   현재가: {current_price:,}원")
    print(f"   안전가: {safe_price:,}원 (+{((safe_price/current_price-1)*100):.1f}%)")
    print(f"   수량: {volume} BTC")

    # When: 임시로 실제 주문 모드 전환 (안전한 가격이므로 체결 불가)
    safe_real_client.enable_dry_run(False)

    order_result = await safe_real_client.place_order(
        market='KRW-BTC',
        side='ask',  # 매도 (높은 가격으로 체결 불가)
        ord_type='limit',
        volume=volume,
        price=Decimal(str(safe_price))
    )

    # Then: 주문 생성 검증 및 즉시 취소
    validate_real_order_response(order_result)
    order_uuid = order_result['uuid']

    # 안전 정리
    await ensure_safe_order_cleanup(safe_real_client, [order_uuid])

    # DRY-RUN 모드 복구
    safe_real_client.enable_dry_run(True)

    print(f"✅ 안전한 실제 주문 테스트 완료: {order_uuid[:8]}...")
```

### Rate Limiter 동적 조정 검증
```python
@pytest.mark.asyncio
@pytest.mark.real_api
@pytest.mark.rate_limiter
async def test_dynamic_rate_limiter_real_adaptation(self, safe_real_client):
    """실제: 동적 Rate Limiter 적응 검증"""
    # Given: 동적 Rate Limiter 상태 확인
    initial_status = safe_real_client.get_dynamic_status()

    # When: 연속 요청으로 429 유발 시도
    for i in range(15):  # 제한 임계치 근처까지
        try:
            await safe_real_client.get_accounts()
            await asyncio.sleep(0.05)  # 짧은 간격
        except Exception as e:
            if "429" in str(e):
                print(f"✅ 429 오류 감지: {i+1}번째 요청에서 발생")
                break

    # Then: Rate Limiter 동적 조정 확인
    final_status = safe_real_client.get_dynamic_status()

    # 조정이 발생했는지 확인
    if final_status != initial_status:
        print("✅ 동적 Rate Limiter 조정 감지")
        print(f"   초기 상태: {initial_status}")
        print(f"   조정 후: {final_status}")
    else:
        print("ℹ️ Rate Limiter 조정 없음 (정상 범위 내 요청)")
```

## 🚀 실행 명령어

### 단계별 테스트 실행
```powershell
# 1단계: DRY-RUN 안전 테스트만 실행
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_private_client_v2/ -v -m dry_run_safe

# 2단계: 실제 API 조회 테스트 (주문 제외)
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_private_client_v2/ -v -m "real_api and not safe_order"

# 3단계: 안전한 실제 주문 테스트 (고가격 체결 방지)
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_private_client_v2/ -v -m "real_api and safe_order"

# 4단계: Rate Limiter 동적 조정 테스트
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_private_client_v2/ -v -m rate_limiter

# 전체 테스트 (DRY-RUN 우선)
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_private_client_v2/ -v
```

### API 키 설정
```powershell
# 필수: API 인증 정보
$access_key = "your_access_key"
$secret_key = "your_secret_key"

# 선택: 실제 거래 테스트 허용 (2단계 확인)
$real_trade_enabled = "false"  # 기본값: 실제 거래 금지

# 선택: 로깅 설정
$console_output = "true"
$log_scope = "verbose"
$component_focus = "UpbitPrivateClient"
```

## 📊 실제 API 응답 데이터 형식

### 계좌 정보 실제 응답 (Dict 형태)
```python
# get_accounts() 실제 응답
{
    "KRW": {
        "currency": "KRW",
        "balance": "1000000.0",
        "locked": "0.0",
        "avg_buy_price": "0",
        "avg_buy_price_modified": False,
        "unit_currency": "KRW"
    },
    "BTC": {
        "currency": "BTC",
        "balance": "0.1",
        "locked": "0.0",
        "avg_buy_price": "83000000",
        "avg_buy_price_modified": False,
        "unit_currency": "KRW"
    }
}
```

### 주문 정보 실제 응답
```python
# place_order() 실제 응답
{
    "uuid": "9ca023a5-851b-4fec-9f0a-48cd83c2eaae",
    "side": "ask",
    "ord_type": "limit",
    "price": "100000000.0",
    "state": "wait",
    "market": "KRW-BTC",
    "created_at": "2024-09-01T14:30:00+09:00",
    "volume": "0.001",
    "remaining_volume": "0.001",
    "reserved_fee": "250.0",
    "remaining_fee": "250.0",
    "paid_fee": "0.0",
    "locked": "0.001",
    "executed_volume": "0.0",
    "trades_count": 0
}

# DRY-RUN 응답
{
    "dry_run": True,
    "simulated_result": {
        "uuid": "dry-run-uuid-simulation",
        "market": "KRW-BTC",
        "side": "ask",
        "ord_type": "limit",
        "price": "100000000.0",
        "volume": "0.001",
        "estimated_fee": "250.0",
        "estimated_total": "100000.0"
    },
    "message": "DRY-RUN: 주문이 시뮬레이션되었습니다"
}
```

### 동적 Rate Limiter 상태 응답
```python
# get_dynamic_status() 응답
{
    'config': {
        'strategy': 'balanced',
        'error_threshold': 3,
        'reduction_ratio': 0.8,
        'recovery_delay': 180.0,
    },
    'groups': {
        'rest_private_default': {
            'total_requests': 45,
            'error_429_count': 2,
            'current_rate_ratio': 0.8,
            'recent_429_errors': 1,
            'time_since_last_reduction': 120.5,
            'time_since_last_recovery': None,
        }
    }
}
```

## 🛡️ 에러 처리 및 복구 패턴

### 429 Rate Limit 에러 처리
```python
@pytest.mark.asyncio
async def test_429_error_recovery(self, safe_real_client):
    """429 에러 자동 복구 검증"""
    try:
        # 연속 요청으로 429 유발
        for i in range(20):
            await safe_real_client.get_accounts()
    except Exception as e:
        if "429" in str(e):
            print("✅ 429 에러 감지 - 동적 조정 확인")

            # 복구 대기
            await asyncio.sleep(5)

            # 복구 후 요청 성공 확인
            accounts = await safe_real_client.get_accounts()
            assert len(accounts) > 0
            print("✅ 429 에러 복구 성공")
```

### 인증 에러 처리
```python
@pytest.mark.asyncio
async def test_authentication_error_handling(self):
    """잘못된 인증 정보 에러 처리"""
    # Given: 잘못된 인증 정보
    invalid_client = UpbitPrivateClient(
        access_key="invalid_key",
        secret_key="invalid_secret",
        dry_run=True
    )

    # When/Then: 인증 에러 발생 확인
    with pytest.raises(Exception) as exc_info:
        await invalid_client.get_accounts()

    assert "authentication" in str(exc_info.value).lower()
```

## 🎯 테스트 목표
- **DRY-RUN 모드 안전성 검증** (기본 동작 보장)
- **실제 API 인증 및 조회 기능 검증**
- **안전한 실제 주문 생성/취소 라이프사이클 검증**
- **동적 Rate Limiter 429 대응 및 복구 검증**
- **에러 처리 및 복구 메커니즘 검증**
- **고급 기능 (일괄 처리, 체결 내역) 검증**

## 🔍 성능 및 안전성 기준
```python
PRIVATE_API_SAFETY_CRITERIA = {
    "dry_run_default": True,                    # DRY-RUN 기본 활성화
    "safe_order_premium": 0.20,                # 최소 20% 프리미엄 가격
    "min_order_amount": 5000,                  # 최소 5,000원 주문
    "max_test_orders": 5,                      # 테스트당 최대 5개 주문
    "cleanup_timeout": 30.0,                   # 정리 작업 타임아웃 30초
    "rate_limiter_adaptation": True,           # Rate Limiter 동적 조정 필수
    "authentication_timeout": 10.0,            # 인증 타임아웃 10초
}
```

## ✅ 검증 완료 기준
```
====== Private API 테스트 통과 기준 ======
✅ DRY-RUN 모드 기본 동작: 모든 주문 시뮬레이션 성공
✅ 실제 인증 및 조회: 계좌/주문 정보 조회 성공
✅ 안전한 실제 주문: 고가격 주문 생성/취소 성공
✅ 동적 Rate Limiter: 429 감지 및 자동 조정 성공
✅ 에러 복구: 인증/네트워크 에러 처리 성공
✅ 고급 기능: 일괄 처리 및 체결 내역 조회 성공
✅ 안전성 보장: 모든 테스트 주문 정리 완료
✅ 성능 기준: 응답 시간 및 처리량 기준 만족
```

---
**v1.0: 업비트 Private API 안전 우선 테스트 방법론 - DRY-RUN First & Real Safe (2025-09-01 생성)**
**안전성 원칙: DRY-RUN 기본 + 고가격 체결 방지 + 동적 Rate Limiter + 확실한 정리**
**실제 거래 금지: 모든 실제 주문은 체결 불가능한 안전 가격으로 테스트 후 즉시 취소**
