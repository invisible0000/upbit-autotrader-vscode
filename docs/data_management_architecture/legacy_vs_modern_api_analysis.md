# 📊 Legacy vs Modern API 상세 분석 및 마이그레이션 전략

## 🔍 **API 구현 비교 분석**

### **Legacy UpbitAPI (data_layer/collectors/upbit_api.py)**

#### **구조적 특징**
```python
class UpbitAPI:
    def __init__(self, access_key=None, secret_key=None):
        self.session = requests.Session()  # 동기식 HTTP
        self._setup_retry_strategy()       # 기본 재시도

    def get_candles(self, market, timeframe, count=200):
        # 단순 동기식 호출
        response = self.session.get(url, params=params)
        return response.json()
```

#### **Rate Limiting (기본적)**
- 요청 간 1초 대기 (`time.sleep(1)`)
- 단순한 예외 처리 및 재시도
- 버스트 요청 제어 없음

#### **장점**
- ✅ **단순함**: 동기식 코드로 이해하기 쉬움
- ✅ **검증된 안정성**: 현재 전체 시스템에서 사용중
- ✅ **즉시 사용 가능**: 추가 설정 불필요

#### **단점**
- ❌ **블로킹 I/O**: API 호출 시 UI/로직 블록
- ❌ **제한적 Rate Limiting**: 고부하 환경에서 제한 가능
- ❌ **확장성 부족**: 병렬 처리 어려움
- ❌ **에러 처리 단순**: 복잡한 장애 상황 대응 제한

### **Modern UpbitClient (infrastructure/external_apis/upbit/)**

#### **구조적 특징**
```python
class UpbitClient:
    def __init__(self, access_key=None, secret_key=None):
        self.public = UpbitPublicClient()    # 퍼블릭 API
        self.private = UpbitPrivateClient()  # 프라이빗 API

    async def get_candles_minutes(self, market, unit=1, count=200):
        # 비동기 호출 + 고급 Rate Limiting
        async with self.rate_limiter:
            response = await self.session.get(url)
            return await response.json()
```

#### **고급 Rate Limiting**
```python
rate_config = RateLimitConfig(
    requests_per_second=10,    # 초당 10회
    requests_per_minute=600,   # 분당 600회
    burst_limit=100           # 버스트 허용
)
```

#### **장점**
- ✅ **비동기 처리**: UI 블록 없는 API 호출
- ✅ **정교한 Rate Limiting**: 업비트 제한에 최적화
- ✅ **병렬 처리**: 여러 API 동시 호출 가능
- ✅ **DDD 준수**: 깔끔한 계층 분리
- ✅ **에러 복구**: 고급 재시도 및 백오프 전략
- ✅ **모니터링**: API 성공/실패 추적

#### **단점**
- ❌ **복잡성**: 비동기 프로그래밍 학습 곡선
- ❌ **미사용 상태**: 아직 시스템 통합 안됨
- ❌ **호환성**: 기존 동기식 코드와 직접 호환 불가

## 🎯 **실제 성능 및 안정성 비교**

### **1. 부하 환경에서의 동작**

#### **Legacy API (문제점)**
```python
# 여러 계산기가 동시에 요청할 때
for calculator in calculators:
    data = api.get_candles('KRW-BTC', '1h', 100)  # 블로킹
    # 각 요청마다 1초씩 대기 → 총 N초 소요
```

#### **Modern API (개선점)**
```python
# 병렬 처리로 효율성 향상
tasks = [
    client.get_candles_minutes('KRW-BTC', 60, 100)
    for calculator in calculators
]
results = await asyncio.gather(*tasks)  # 동시 실행
```

### **2. Rate Limit 대응력**

#### **Legacy**: 단순 대기
```python
time.sleep(1)  # 무조건 1초 대기
```

#### **Modern**: 지능적 제어
```python
# 토큰 버킷 알고리즘으로 최적화
async with rate_limiter:  # 필요한 만큼만 대기
    response = await make_request()
```

### **3. 장애 복구 능력**

#### **Legacy**: 기본 재시도
- 3회 재시도 후 포기
- 고정 대기 시간

#### **Modern**: 고급 복구
- 지수 백오프 (1초 → 2초 → 4초...)
- 서킷 브레이커 패턴
- API 상태 모니터링

## 🏗️ **DDD 아키텍처 장점 분석**

### **1. 기능 추가/교체 용이성**

#### **현재 Legacy 구조**
```
계산기 → UpbitAPI (직접 의존) → SQLite DB
```
- API 변경 시 모든 계산기 수정 필요
- 테스트 어려움 (실제 API 의존)

#### **DDD 구조**
```
계산기 → DataService (인터페이스) ← UpbitRepository (구현체)
```
- 인터페이스 통해 느슨한 결합
- Mock 테스트 가능
- 구현체 교체 시 계산기 코드 변경 불필요

### **2. 테스트 용이성**

#### **Legacy**
```python
def test_atr_calculator():
    # 실제 API 호출 필요 → 불안정한 테스트
    calculator = ATRCalculator()
    result = calculator.calculate('KRW-BTC', params)
```

#### **DDD**
```python
def test_atr_calculator():
    # Mock 데이터로 안정적 테스트
    mock_service = MockDataService()
    calculator = ATRCalculator(mock_service)
    result = calculator.calculate(params)
```

### **3. 확장성**

#### **새로운 거래소 추가**
```python
# Legacy: 모든 계산기 수정 필요
class ATRCalculator:
    def __init__(self):
        self.upbit_api = UpbitAPI()      # 하드코딩
        self.binance_api = BinanceAPI()  # 추가 시 모든 곳 수정

# DDD: 인터페이스만 구현
class BinanceDataService(DataServiceInterface):
    async def get_candles(self, market, timeframe, count):
        # Binance API 구현
        pass
```

## 🚀 **마이그레이션 전략**

### **Phase 1: 호환성 래퍼 (즉시 가능)**
```python
class UpbitAPICompatWrapper:
    """기존 코드 호환용 동기식 래퍼"""

    def __init__(self):
        self._async_client = UpbitClient()

    def get_candles(self, market, timeframe, count):
        """기존 인터페이스 유지하면서 Modern API 사용"""
        return asyncio.run(
            self._async_client.get_candles_minutes(market, unit, count)
        )
```

### **Phase 2: 점진적 전환**
```python
# 1. 새로운 계산기는 비동기로 구현
class NewATRCalculator:
    async def calculate_async(self, params):
        async with UpbitClient() as client:
            data = await client.get_candles_minutes(...)

# 2. 기존 계산기는 래퍼 사용
class LegacyATRCalculator:
    def calculate(self, params):
        wrapper = UpbitAPICompatWrapper()
        data = wrapper.get_candles(...)  # 기존 인터페이스
```

### **Phase 3: 완전 전환**
- 모든 계산기를 비동기로 전환
- Legacy API 제거
- DDD 아키텍처 완성

## ✅ **결론 및 권장사항**

### **Modern API가 더 안정적인가?**
**✅ YES** - 다음 이유로:
1. **정교한 Rate Limiting**: 업비트 제한에 최적화
2. **비동기 처리**: UI 블록 없음
3. **병렬 처리**: 여러 계산기 동시 실행 가능
4. **고급 에러 복구**: 장애 상황 대응력 향상
5. **모니터링**: API 상태 추적 가능

### **DDD가 기능 추가/교체를 쉽게 하는가?**
**✅ YES** - 다음 이유로:
1. **느슨한 결합**: 인터페이스 기반 설계
2. **테스트 용이**: Mock 객체 활용 가능
3. **확장성**: 새로운 거래소/데이터소스 추가 용이
4. **유지보수**: 계층별 독립적 수정 가능

### **즉시 실행 계획**

**1. 백업 폴더 이동**
```powershell
# strategy_management_backup을 legacy로 이동
Move-Item "upbit_auto_trading\ui\desktop\screens\strategy_management_backup" "legacy\strategy_management_backup"
```

**2. 호환성 래퍼 구현**
- `infrastructure/adapters/upbit_api_wrapper.py` 생성
- 기존 동기식 인터페이스 유지하면서 Modern API 사용

**3. 점진적 전환**
- ATR 계산기부터 Modern API 적용
- 나머지 계산기들 순차 전환

Modern API + DDD 아키텍처가 **확실히 더 안정적이고 확장 가능**합니다. 마이그레이션을 시작하시겠습니까?
