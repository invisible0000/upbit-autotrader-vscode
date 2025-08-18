# GUIDE_신규백본개발

**목적**: 신규 Infrastructure 백본 컴포넌트 개발 표준
**분량**: 179줄 / 200줄 (90% 사용) 🟡
**적용**: 모든 Infrastructure Layer 신규 개발

---

## 🎯 **핵심 원칙 (1-20줄: 즉시 파악)**

### **DDD 4계층 준수**
```
Presentation(PyQt6) → Application(UseCase) → Domain(순수) ← Infrastructure(외부)
```

### **백본 황금 규칙**
- ✅ Domain 순수성: sqlite3/requests/PyQt6 import 금지
- ✅ 의존성 역전: Domain → Infrastructure Interface만 의존
- ✅ 단일 책임: 컴포넌트당 1개 핵심 기능
- ✅ Infrastructure 로깅: create_component_logger() 필수

### **개발 우선순위**
1. **TDD**: 테스트 스텁 → 최소 구현 → 리팩터링
2. **Dry-Run**: 기본 시뮬레이션, 실거래는 2단계 확인
3. **보안**: API키 환경변수, 로깅 민감정보 제외

---

## 🏗️ **표준 아키텍처 (21-50줄: 맥락)**

### **백본 컴포넌트 구조**
```python
upbit_auto_trading/infrastructure/
├── {component_name}/
│   ├── __init__.py           # 공개 인터페이스
│   ├── config.py            # 설정 관리
│   ├── {component_name}.py   # 핵심 구현
│   ├── models.py            # DTO/VO
│   └── exceptions.py        # 전용 예외
```

### **Domain Interface 정의**
```python
# domain/ports/{component_name}_port.py
from abc import ABC, abstractmethod
from typing import Protocol

class {ComponentName}Port(Protocol):
    async def primary_action(self, request: RequestDTO) -> ResponseDTO:
        """핵심 기능 명세"""
        pass
```

### **Infrastructure 구현체**
```python
# infrastructure/{component_name}/{component_name}.py
from upbit_auto_trading.domain.ports import {ComponentName}Port
from upbit_auto_trading.infrastructure.logging import create_component_logger

class {ComponentName}Service({ComponentName}Port):
    def __init__(self):
        self.logger = create_component_logger("{ComponentName}")

    async def primary_action(self, request: RequestDTO) -> ResponseDTO:
        self.logger.info(f"실행: {request}")
        # 구현 로직
        return response
```

---

## 📋 **필수 구현 체크리스트 (51-100줄: 상세)**

### **1. Domain Interface 설계**
```python
✅ 추상 메서드로 핵심 기능 정의
✅ DTO/VO 타입힌트 명시
✅ 비즈니스 예외 정의
✅ 외부 의존성 제거

# 예시: 캐시 포트
class MarketDataCachePort(Protocol):
    async def get_candles(self, symbol: str, timeframe: str, count: int) -> List[CandleDTO]:
        pass

    async def cache_candles(self, symbol: str, timeframe: str, candles: List[CandleDTO]) -> None:
        pass
```

### **2. DTO 설계 표준**
```python
✅ @dataclass(frozen=True) 불변성
✅ 명확한 타입힌트
✅ 검증 로직 포함
✅ 직렬화 지원

@dataclass(frozen=True)
class CandleDTO:
    symbol: str
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal

    def __post_init__(self):
        if self.open_price <= 0:
            raise ValueError("가격은 0보다 커야 합니다")
```

### **3. 설정 관리**
```python
✅ 환경변수 우선
✅ YAML 설정 지원
✅ 기본값 제공
✅ 검증 로직

class {ComponentName}Config:
    def __init__(self):
        self.api_timeout = int(os.getenv('UPBIT_API_TIMEOUT', '30'))
        self.cache_size = int(os.getenv('CACHE_SIZE', '1000'))
        self.retry_count = int(os.getenv('RETRY_COUNT', '3'))
```

### **4. 예외 처리**
```python
✅ 컴포넌트별 예외 정의
✅ 명확한 에러 메시지
✅ 에러 코드 포함
✅ 로깅 연동

class {ComponentName}Error(Exception):
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code

class CacheNotFoundError({ComponentName}Error):
    pass
```

---

## 🧪 **테스트 전략 (101-150줄: 실행)**

### **TDD 개발 순서**
```python
# 1. 테스트 스텁 작성
def test_cache_hit():
    # Given
    cache_service = MarketDataCacheService()
    symbol, timeframe = "KRW-BTC", "1m"

    # When
    result = await cache_service.get_candles(symbol, timeframe, 20)

    # Then
    assert len(result) == 20
    assert result[0].symbol == symbol

# 2. 최소 구현
async def get_candles(self, symbol: str, timeframe: str, count: int) -> List[CandleDTO]:
    return []  # 최소 구현

# 3. 점진적 개선
async def get_candles(self, symbol: str, timeframe: str, count: int) -> List[CandleDTO]:
    # 실제 구현 로직
    pass
```

### **테스트 범위**
```yaml
Unit Tests:
  - Domain 로직 검증
  - DTO 검증 로직
  - 예외 처리

Integration Tests:
  - Infrastructure 연동
  - DB 상호작용
  - API 호출

E2E Tests:
  - 전체 플로우
  - 성능 검증
```

### **Mock 전략**
```python
@pytest.fixture
def mock_api_client():
    with patch('upbit_auto_trading.infrastructure.api.UpbitAPIClient') as mock:
        mock.return_value.get_candles.return_value = sample_candles()
        yield mock

def test_with_mock(mock_api_client):
    service = MarketDataCacheService()
    result = await service.get_candles("KRW-BTC", "1m", 10)
    mock_api_client.return_value.get_candles.assert_called_once()
```

---

## 🚀 **실제 구현 예시 (151-179줄: 연결)**

### **완전한 백본 컴포넌트**
```python
# infrastructure/market_data_cache/market_data_cache.py
from upbit_auto_trading.domain.ports import MarketDataCachePort
from upbit_auto_trading.infrastructure.logging import create_component_logger

class MarketDataCacheService(MarketDataCachePort):
    def __init__(self):
        self.logger = create_component_logger("MarketDataCache")
        self.memory_cache = {}

    async def get_candles(self, symbol: str, timeframe: str, count: int) -> List[CandleDTO]:
        cache_key = f"{symbol}_{timeframe}"

        if cache_key in self.memory_cache:
            self.logger.debug(f"캐시 히트: {cache_key}")
            cached_data = self.memory_cache[cache_key]
            return cached_data[-count:] if len(cached_data) >= count else cached_data

        self.logger.info(f"캐시 미스: {cache_key}, API 호출")
        # API 호출 로직
        return []
```

### **관련 문서 연결**
- `NOW_백본15개현황.md` - 현재 백본 상태
- `PLAN_캐시v1구현.md` - 캐시 구현 계획
- `STAT_성능기준선.md` - 성능 기준

**목표**: 견고하고 확장 가능한 Infrastructure 백본 구축 🏗️
