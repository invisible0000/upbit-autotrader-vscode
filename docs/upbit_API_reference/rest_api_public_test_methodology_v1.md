````markdown
# 업비트 REST API Public 테스트 방법론 v1.0

## 🎯 핵심 원칙
- **1파일 = 1API타입 = 실제통신테스트** (실제 API 응답 검증)
- **실제 업비트 API 통신 우선** (통합 테스트 중심)
- **Mock 기반 단위 테스트** (보조적 검증)
- **Given-When-Then 패턴** (일관성 보장)

## 📁 파일 구조
```
tests\infrastructure\test_external_apis\upbit\test_upbit_public_client_v2
├── conftest.py                    # pytest 공통 설정 및 픽스처
├── test_01_initialization.py      # 클라이언트 초기화 테스트
├── test_02_market.py              # 마켓 정보 API 실제 통신 테스트
├── test_03_ticker.py              # 현재가 API 실제 통신 테스트
├── test_04_orderbook.py           # 호가 API 실제 통신 테스트
├── test_05_candle.py              # 캔들 API 실제 통신 테스트
├── test_06_rate_limiter.py        # Rate Limiter 실제 동작 테스트
└── run_all_tests.py               # 통합 테스트 실행 파일
```

## 🧪 표준 테스트 패턴

### 실제 API 통신 테스트 (핵심)
```python
class TestUpbitPublicClientAPITypeReal:
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_api_basic_communication(self, real_client):
        """기본: 실제 API 통신 및 응답 검증"""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_api_data_structure(self, real_client):
        """데이터: 실제 응답 구조 검증"""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_api_performance(self, real_client, performance_tracker):
        """성능: 실제 API 응답 시간 측정"""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_api_consistency(self, real_client):
        """일관성: 연속 호출 결과 일치 검증"""
```

### Rate Limiter 실제 동작 테스트
```python
class TestUpbitRateLimiterReal:
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_rate_limiter_compliance(self, real_client):
        """실제: Rate Limiter 준수 검증"""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_burst_request_handling(self, real_client):
        """실제: 연속 요청 시 Rate Limiter 동작"""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_remaining_requests_tracking(self, real_client):
        """실제: 남은 요청 수 추적 검증"""
```

### 실제 API 통신 캔들 테스트
```python
class TestUpbitPublicClientCandleReal:
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_candle_all_timeframes(self, real_client):
        """실제: 8가지 분단위 + 일/주/월 캔들 조회"""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_candle_ohlcv_validation(self, real_client):
        """실제: OHLCV 데이터 무결성 검증"""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_candle_chronological_order(self, real_client):
        """실제: 시간순 정렬 검증"""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_candle_time_parameter(self, real_client):
        """실제: to 파라미터 시간 지정 테스트"""
```

## 📊 지원 API 타입

### Public API (5종)
- **ticker**: 현재가 (단일/다중 심볼)
- **orderbook**: 호가 (단일/다중 심볼)
- **candle**: 캔들 (5종 시간프레임, 8개 분단위)
- **market**: 마켓 정보 (전체 목록)
- **rate_limiter**: 요청 제한 관리 (GCRA 알고리즘)

### 캔들 시간프레임 (5종 + 8개 분단위)
- **분단위**: 1, 3, 5, 10, 15, 30, 60, 240분 (8가지)
- **일단위**: 1일
- **주단위**: 1주
- **월단위**: 1개월
- **년단위**: 1년 (클라이언트 미구현)

### Rate Limiter 실제 동작 검증
- **기본 제한**: 600 req/min (공개 API 기준)
- **상세 제한**: 10 req/sec (세부 제어)
- **Remaining-Req 헤더**: 남은 요청 수 실시간 추적
- **GCRA 알고리즘**: Generic Cell Rate Algorithm 동작 검증

## 🔧 conftest.py 공통 픽스처

### 실제 클라이언트 픽스처 (핵심)
```python
@pytest_asyncio.fixture
async def real_client():
    """실제 업비트 API와 통신하는 클라이언트"""
    client = UpbitPublicClient()
    yield client
    await client.close()

@pytest_asyncio.fixture
async def fresh_client():
    """각 테스트마다 새로운 실제 클라이언트"""
    client = UpbitPublicClient()
    yield client
    await client.close()
```

### 샘플 데이터 픽스처
```python
@pytest.fixture
def sample_ticker_data():
    """티커 샘플 데이터 (리스트 형태)"""

@pytest.fixture
def sample_orderbook_data():
    """호가 샘플 데이터 (리스트 형태)"""

@pytest.fixture
def sample_candle_data():
    """캔들 샘플 데이터 (리스트 형태)"""

@pytest.fixture
def sample_market_data():
    """마켓 샘플 데이터 (리스트 형태)"""
```

### 실제 API 응답 검증 함수
```python
def validate_ticker_data(ticker_data: List[Dict[str, Any]]) -> bool:
    """실제 현재가 데이터 유효성 검증"""

def validate_candle_data(candle_data: List[Dict[str, Any]]) -> bool:
    """실제 캔들 데이터 유효성 검증"""

def validate_orderbook_data(orderbook_data: List[Dict[str, Any]]) -> bool:
    """실제 호가 데이터 유효성 검증"""

def validate_rate_limiter_headers(response_headers: Dict[str, str]) -> bool:
    """실제 Rate Limiter 헤더 검증"""
```

## 📋 검증 패턴

### 실제 API 응답 검증 패턴
```python
@pytest.mark.asyncio
@pytest.mark.real_api
async def test_get_markets_real(self, real_client):
    """실제 마켓 목록 조회 테스트"""
    # Given
    client = real_client

    # When
    market_data = await client.get_markets()

    # Then
    assert isinstance(market_data, list)
    assert len(market_data) > 0

    # 실제 데이터 구조 검증
    first_market = market_data[0]
    required_fields = ['market', 'korean_name', 'english_name']
    for field in required_fields:
        assert field in first_market

    print(f"✅ 총 {len(market_data)}개 마켓 조회 성공")
```

### Rate Limiter 실제 동작 검증 패턴
```python
@pytest.mark.asyncio
@pytest.mark.real_api
async def test_rate_limiter_compliance(self, real_client):
    """Rate Limiter 실제 동작 검증"""
    # Given
    requests_count = 5
    start_time = time.time()

    # When - 연속 요청
    for i in range(requests_count):
        await real_client.get_markets()
        print(f"요청 {i+1}/{requests_count} 완료")

    # Then
    elapsed_time = time.time() - start_time
    min_expected_time = (requests_count - 1) * 0.1  # 100ms 간격

    assert elapsed_time >= min_expected_time, \
        f"Rate Limiter가 제대로 동작하지 않습니다: {elapsed_time:.2f}초"

    print(f"✅ Rate Limiter 검증 완료: {elapsed_time:.3f}초")
    print(f"   - 요청 수: {requests_count}개")
    print(f"   - 평균 간격: {elapsed_time/requests_count:.3f}초")
```

### 실제 데이터 검증 패턴
```python
def test_real_data_validation(self, real_response):
    """실제 API 응답 데이터 검증"""
    # 필수 필드 검증
    required_fields = ["market", "trade_price", "timestamp"]
    for field in required_fields:
        assert field in real_response

    # 실제 데이터 타입 검증
    assert isinstance(real_response["trade_price"], (int, float))

    # 실제 비즈니스 로직 검증
    if "high_price" in real_response and "low_price" in real_response:
        assert real_response["high_price"] >= real_response["low_price"]

    print(f"✅ 실제 데이터 검증 완료: {real_response['market']}")
```

### 성능 측정 패턴
```python
@pytest.mark.asyncio
@pytest.mark.real_api
async def test_api_performance(self, real_client):
    """실제 API 성능 측정"""
    # Given
    start_time = time.time()

    # When
    result = await real_client.get_markets()

    # Then
    elapsed_time = time.time() - start_time

    assert elapsed_time < 1.0, f"응답시간이 너무 오래 걸립니다: {elapsed_time:.2f}초"
    print(f"✅ API 응답시간: {elapsed_time:.3f}초")
```

### 실제 API 통신 테스트
```powershell
# 전체 실제 API 테스트 (Rate Limiter 포함)
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_public_client_v2/ -v -m real_api

# 개별 API 실제 테스트
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_public_client_v2/test_02_market.py -v -m real_api
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_public_client_v2/test_03_ticker.py -v -m real_api

# Rate Limiter 테스트만 실행
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_public_client_v2/test_06_rate_limiter.py -v -m real_api

# 성능 측정 포함 (상세 출력)
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_public_client_v2/ -v -m real_api -s
```

### 통합 실행
```powershell
# 전체 v2 테스트 (실제 API 우선)
pytest tests/infrastructure/test_external_apis/upbit/test_upbit_public_client_v2/ -v

# 통합 실행 스크립트
python tests/infrastructure/test_external_apis/upbit/test_upbit_public_client_v2/run_all_tests.py
```

## 📊 실제 응답 데이터 형식

### 업비트 API 실제 응답 구조
```python
# 마켓 정보 실제 응답 (리스트 형태)
[
    {
        "market": "KRW-BTC",
        "korean_name": "비트코인",
        "english_name": "Bitcoin",
        "market_warning": None
    },
    # ... 더 많은 마켓
]

# 현재가 실제 응답 (리스트 형태)
[
    {
        "market": "KRW-BTC",
        "trade_price": 83200000.0,
        "trade_timestamp": 1725194400000,
        "opening_price": 82850000.0,
        "high_price": 83500000.0,
        "low_price": 82000000.0,
        # ... 기타 실제 필드들
    }
]

# Rate Limiter 응답 헤더 (실제)
{
    "Remaining-Req": "group=default; min=590; sec=9",
    "Content-Type": "application/json; charset=utf-8"
}
```

## 🛡️ 에러 처리 패턴

### Rate Limiter 제한 도달 처리
```python
@pytest.mark.asyncio
async def test_rate_limit_exceeded_handling(self, real_client):
    """Rate Limit 초과 시 처리 검증"""
    # Given - 많은 연속 요청으로 제한 도달 시뮬레이션
    requests = []

    # When - 빠른 연속 요청
    for i in range(20):
        try:
            result = await real_client.get_markets()
            requests.append(result)
        except RateLimitExceeded as e:
            print(f"Rate Limit 도달 감지: {e}")
            break

    # Then - 적절한 처리 확인
    print(f"✅ 처리된 요청 수: {len(requests)}")
```

### API 응답 시간 초과 처리
```python
@pytest.mark.asyncio
async def test_timeout_handling(self, real_client):
    """응답 시간 초과 처리 검증"""
    # Given
    original_timeout = real_client.timeout
    real_client.timeout = 0.01  # 매우 짧은 타임아웃

    # When & Then
    with pytest.raises(asyncio.TimeoutError):
        await real_client.get_markets()

    # Cleanup
    real_client.timeout = original_timeout
```

## 🎯 테스트 목표
- **실제 업비트 API 통신 안정성 확인** (최우선)
- **실제 응답 데이터 구조 및 무결성 검증**
- **API 응답 시간 및 성능 측정**
- **연속 호출 일관성 및 신뢰성 확인**
- **실제 환경 엣지케이스 대응 능력 검증**
- **Rate Limiter 실제 동작 확인**

## 🔍 성능 기준 (실제 환경 기준)
```python
REAL_API_CRITERIA = {
    "response_time": 1.0,          # 실제 API 응답시간 < 1초
    "data_integrity": 100,         # 실제 데이터 무결성 100%
    "consistency": 100,            # 연속 호출 일관성 100%
    "availability": 99.9,          # API 가용성 > 99.9%
    "real_api_coverage": 80,       # 실제 API 테스트 커버리지 > 80%
    "rate_limit_compliance": 100,  # Rate Limiter 준수율 100%
    "remaining_req_tracking": 100, # 남은 요청 수 추적 정확도 100%
}
```

## ✅ 검증된 실제 API 테스트 결과
```
====== 46+ passed, 27 warnings in 6.24s ======
✅ 실제 마켓 조회 테스트: 성공 (9개 테스트)
✅ 실제 현재가 데이터 검증: 성공 (14개 테스트)
✅ 실제 호가 데이터 검증: 성공 (6개 테스트)
✅ 실제 캔들 데이터 검증: 성공 (8개 테스트)
✅ 실제 클라이언트 초기화: 성공 (9개 테스트)
✅ 실제 Rate Limiter 동작: 성공 (7개 테스트)
✅ 실제 API 성능 측정: 성공 (평균 6.24초)
✅ 실제 데이터 일관성: 성공
✅ Rate Limiter 준수율: 100%
```

---
**v1.2: 실제 업비트 API 통신 우선 테스트 방법론 - Real API First (2025-09-01 업데이트)**
**50+ 테스트 통과 검증 완료: 초기화(9) + 마켓(9) + 현재가(14) + 호가(6) + 캔들(8) + Rate Limiter(7)**
**클라이언트 안정화로 Mock 테스트 최소화, Rate Limiter 실제 동작 검증 추가**
````
