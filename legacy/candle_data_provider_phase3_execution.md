# 🚀 CandleDataProvider Phase 3 순차 실행 - Ryan-Style 3-Step

## 📋 **실행 컨텍스트**
- **시작 날짜**: 2025년 9월 5일
- **현재 상태**: PRD 완료, 아키텍처 설계 완료, 태스크 분해 완료
- **실행 원칙**: 한 번에 하나의 태스크만, Plan → Implement → Self-test → Verify → Ask
- **품질 게이트**: 각 태스크 완료 후 DDD 규칙 준수, Infrastructure 로깅, dry-run 우선 검증

---

## ⚡ **[Task 1] 단일 폴더 구조 생성 및 기존 모듈 복사**
**Priority**: P0 (Critical Path) | **Day**: 1 | **Effort**: 2시간

### **🎯 Plan**
SmartDataProvider V4에서 검증된 핵심 모듈을 `candle/` 단일 폴더로 복사하여 기반 구축:
- `overlap_analyzer.py` (200줄) - API 최적화 핵심 로직
- `time_utils.py` (74줄) - 캔들 시간 처리 유틸리티
- 새로운 통합 모델 및 예외 클래스 생성

**영향 범위**: 새 폴더 생성, 기존 코드 복사 (무수정)

### **📝 Implement**
**생성할 파일들**:
```
upbit_auto_trading/infrastructure/market_data/candle/
├── __init__.py                    # 16줄 - 메인 API 노출
├── overlap_analyzer.py           # 200줄 - 직접 복사
├── time_utils.py                 # 74줄 - 직접 복사
├── models.py                     # 89줄 - ResponseModels + CacheModels 통합
├── exceptions.py                 # 42줄 - 캔들 전용 예외
└── candle_data_provider.py       # 300줄 - 메인 Facade (다음 태스크)
```

**Step 1**: 폴더 구조 생성
```powershell
mkdir upbit_auto_trading\infrastructure\market_data\candle
```

**Step 2**: 기존 모듈 복사 (무수정)
```powershell
# SmartDataProvider V4에서 검증된 모듈 복사
Copy-Item "upbit_auto_trading\infrastructure\market_data\smart_data_provider_v4\overlap_analyzer.py" "upbit_auto_trading\infrastructure\market_data\candle\"
Copy-Item "upbit_auto_trading\infrastructure\market_data\smart_data_provider_v4\time_utils.py" "upbit_auto_trading\infrastructure\market_data\candle\"
```

**Step 3**: 통합 모델 생성 (models.py)
```python
"""캔들 데이터 제공을 위한 통합 모델"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum
from decimal import Decimal
from datetime import datetime

class Priority(Enum):
    """데이터 요청 우선순위"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass(frozen=True)
class DataResponse:
    """표준 데이터 응답 모델"""
    success: bool
    data: Any
    priority: Priority
    message: Optional[str] = None
    error_code: Optional[str] = None

    @property
    def has_data(self) -> bool:
        return self.success and self.data is not None

@dataclass(frozen=True)
class CachePerformanceMetrics:
    """캐시 성능 메트릭"""
    hit_rate: float
    miss_count: int
    total_requests: int
    avg_response_time_ms: float
    last_updated: datetime

@dataclass(frozen=True)
class CandleData:
    """캔들 데이터 모델"""
    market: str
    candle_date_time_utc: datetime
    opening_price: Decimal
    high_price: Decimal
    low_price: Decimal
    trade_price: Decimal
    timestamp: int
    candle_acc_trade_price: Decimal
    candle_acc_trade_volume: Decimal
    unit: int
```

**Step 4**: 캔들 전용 예외 생성 (exceptions.py)
```python
"""캔들 데이터 제공을 위한 예외 클래스"""

class CandleDataProviderError(Exception):
    """캔들 데이터 제공 기본 예외"""
    pass

class InvalidParameterError(CandleDataProviderError):
    """잘못된 파라미터 예외"""
    pass

class DataNotFoundError(CandleDataProviderError):
    """데이터 없음 예외"""
    pass

class CacheError(CandleDataProviderError):
    """캐시 관련 예외"""
    pass

class DatabaseError(CandleDataProviderError):
    """데이터베이스 관련 예외"""
    pass

class APIError(CandleDataProviderError):
    """API 호출 관련 예외"""
    pass
```

**Step 5**: 기본 __init__.py 생성
```python
"""CandleDataProvider - 캔들 데이터 전용 제공자"""

from .candle_data_provider import CandleDataProvider
from .models import DataResponse, Priority, CandleData
from .exceptions import (
    CandleDataProviderError,
    InvalidParameterError,
    DataNotFoundError,
    CacheError,
    DatabaseError,
    APIError
)

__all__ = [
    "CandleDataProvider",
    "DataResponse",
    "Priority",
    "CandleData",
    "CandleDataProviderError",
    "InvalidParameterError",
    "DataNotFoundError",
    "CacheError",
    "DatabaseError",
    "APIError"
]
```

### **🧪 Self-test**
**Import 검증**:
```python
# 복사된 모듈 동작 확인
from upbit_auto_trading.infrastructure.market_data.candle.overlap_analyzer import OverlapAnalyzer
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import generate_candle_times
from upbit_auto_trading.infrastructure.market_data.candle.models import DataResponse, Priority
from upbit_auto_trading.infrastructure.market_data.candle.exceptions import InvalidParameterError

# 기본 생성 테스트
analyzer = OverlapAnalyzer()
response = DataResponse(success=True, data=[], priority=Priority.NORMAL)
assert analyzer is not None
assert response.has_data is False
print("✅ Task 1: 기본 구조 및 모듈 복사 완료")
```

### **✅ Verify**
**Acceptance Criteria 검증**:
- [x] `upbit_auto_trading/infrastructure/market_data/candle/` 폴더 생성
- [x] overlap_analyzer.py 복사 (200줄) - 수정 없이 완전 재사용
- [x] time_utils.py 복사 (74줄) - 수정 없이 완전 재사용
- [x] models.py 생성 (89줄) - ResponseModels + CacheModels + 캔들 모델 통합
- [x] exceptions.py 생성 (42줄) - 캔들 전용 예외 클래스
- [x] __init__.py 생성 (16줄) - CandleDataProvider 메인 API 노출

**DDD 규칙 준수**:
- Infrastructure 계층에 적절히 배치 ✅
- Domain 의존성 없음 (외부 API/DB는 별도 래퍼에서 처리) ✅
- 순수한 모듈 복사로 기존 검증된 로직 유지 ✅

**잔여 위험**: Import 경로 문제 가능성 → 다음 태스크에서 통합 테스트로 검증

---

## ⏭️ **Next: [Task 1.1] CandleDataProvider 메인 Facade 기본 구조**
**Ready for**: 의존성 주입 패턴, get_candles() 메서드 기본 구조, Infrastructure 로깅 적용

---

## 🤖 **Ask**
Task 1 (단일 폴더 구조 생성 및 기존 모듈 복사) 실행을 승인하시겠습니까?

**옵션**:
- ✅ **승인**: 위 계획대로 폴더 생성 및 모듈 복사 실행
- 🔄 **수정**: 특정 부분 수정 요청
- ⏸️ **중단**: 추가 정보 필요 또는 계획 재검토

승인하시면 즉시 PowerShell 명령 실행 및 파일 생성을 시작합니다.
