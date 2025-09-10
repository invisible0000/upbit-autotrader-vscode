# Tasks: OverlapAnalyzer v5.0

**Input**: Design documents from `/specs/002-overlapanalyzer-v5-for/`
**Prerequisites**: spec.md ✅, plan.md ✅

## Execution Summary
Minimal integration with existing DDD structure. Total: 5 focused tasks.
- Repository interface extension (2 methods)
- SQLite implementation (database layer)
- OverlapAnalyzer main logic (5-state classification)
- Comprehensive testing (TDD approach)
- Integration & validation

**Target Files**: 1 new file + 2 extensions + 1 test file = **4 files total**

---

## Phase 3.1: Repository Foundation

### T001: Extend Repository Interface
**File**: `upbit_auto_trading/domain/repositories/candle_repository_interface.py`
**Action**: Add 2 method signatures for overlap analysis
```python
async def has_data_at_time(self, symbol: str, timeframe: str, target_time: datetime) -> bool:
    """Check if candle data exists at specific timestamp"""

async def find_data_start_in_range(self, symbol: str, timeframe: str,
                                  start_time: datetime, end_time: datetime) -> Optional[datetime]:
    """Find first data timestamp within given range"""
```
**Validation**: Interface compilation check, type hints verified

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

### T002: Create Comprehensive Test Suite
**File**: `tests/infrastructure/market_data/candle/test_overlap_analyzer.py`
**Action**: Write failing tests for all 5 overlap states + edge cases
```python
class TestOverlapAnalyzer:
    # 5 Core State Tests
    async def test_no_overlap_analysis()           # Empty DB case
    async def test_complete_overlap_analysis()     # Full DB coverage
    async def test_partial_start_analysis()        # DB data at beginning
    async def test_partial_middle_fragment_analysis()  # DB data with gaps
    async def test_partial_middle_continuous_analysis() # DB data at end

    # Edge Cases
    async def test_invalid_time_range()            # start > end
    async def test_database_connection_failure()   # DB error handling
    async def test_timestamp_precision_handling()  # Microsecond differences

    # Performance
    async def test_analysis_performance()          # <10ms requirement
```
**Validation**: All tests MUST FAIL initially (no implementation exists)
**Dependencies**: Requires existing test database setup from current test suite

---

## Phase 3.3: Implementation

### T003: Implement Repository Methods
**File**: `upbit_auto_trading/infrastructure/repositories/sqlite_candle_repository.py`
**Action**: Add 2 optimized SQLite methods following existing patterns
```python
async def has_data_at_time(self, symbol: str, timeframe: str, target_time: datetime) -> bool:
    # PRIMARY KEY lookup for maximum performance
    # Reuse existing db_manager connection
    # Follow existing error handling pattern

async def find_data_start_in_range(self, symbol: str, timeframe: str,
                                  start_time: datetime, end_time: datetime) -> Optional[datetime]:
    # MAX() query with BETWEEN for range search
    # Handle Upbit descending order (latest = start)
    # Use existing table_exists() check
```
**Style Requirements**:
- Follow existing method naming conventions
- Use existing `create_component_logger("SQLiteCandleRepository")`
- Maintain existing error handling patterns
- Reuse `self.db_manager.get_connection("market_data")`

**Validation**: T002 repository tests start passing

---

### T004: Create OverlapAnalyzer Core
**File**: `upbit_auto_trading/infrastructure/market_data/candle/overlap_analyzer.py`
**Action**: Single-file implementation with embedded data models
```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime

# Data Models (embedded in same file for simplicity)
class OverlapStatus(Enum):
    NO_OVERLAP = "no_overlap"
    COMPLETE_OVERLAP = "complete_overlap"
    PARTIAL_START = "partial_start"
    PARTIAL_MIDDLE_FRAGMENT = "partial_middle_fragment"
    PARTIAL_MIDDLE_CONTINUOUS = "partial_middle_continuous"

@dataclass(frozen=True)
class OverlapRequest:
    symbol: str
    timeframe: str
    target_start: datetime
    target_end: datetime
    target_count: int

@dataclass(frozen=True)
class OverlapResult:
    status: OverlapStatus
    api_start: Optional[datetime] = None
    api_end: Optional[datetime] = None
    db_start: Optional[datetime] = None
    db_end: Optional[datetime] = None

# Main Implementation
class OverlapAnalyzer:
    def __init__(self, repository, time_utils):
        self.repository = repository
        self.time_utils = time_utils
        self.logger = create_component_logger("OverlapAnalyzer")

    async def analyze_overlap(self, request: OverlapRequest) -> OverlapResult:
        # 5-state classification algorithm
        # Follows algorithm from OVERLAP_ANALYZER_V5_SIMPLIFIED_DESIGN.md
```

**Style Requirements**:
- Follow existing Infrastructure component patterns
- Use `create_component_logger("OverlapAnalyzer")`
- Maintain DDD layer separation (no direct DB access)
- Include docstrings in existing project style

**Algorithm**: Implement exact 5-step decision tree from existing design document
**Validation**: T002 analyzer tests start passing

---

## Phase 3.4: Integration & Validation

### T005: Integration Testing & Performance Validation
**Actions**:
1. **Run full test suite**: Verify all T002 tests pass
2. **Performance validation**: Confirm <10ms analysis time
3. **Integration check**: Test with existing candle data pipeline
4. **Style validation**: Ensure code matches existing project conventions

**Integration Points**:
- Verify compatibility with existing `time_utils` module
- Test with existing `market_data.sqlite3` database
- Confirm logging integrates with existing Infrastructure logging

**Success Criteria**:
- [ ] All 8 test methods pass (5 states + 3 edge cases)
- [ ] Performance test shows <10ms average
- [ ] No breaking changes to existing candle repository
- [ ] Code style matches existing infrastructure components
- [ ] Integration with existing DDD layers verified

---

## Parallel Execution Opportunities

**[P] Parallel Tasks**: None - all tasks have dependencies
**Reason**: Sequential execution required due to:
- T001 → T002 (tests need interface)
- T002 → T003 (TDD: tests before implementation)
- T003 → T004 (analyzer needs repository methods)
- T004 → T005 (integration needs all components)

## Dependency Graph
```
T001 (Interface)
  ↓
T002 (Tests)
  ↓
T003 (Repository Implementation)
  ↓
T004 (Analyzer Implementation)
  ↓
T005 (Integration & Validation)
```

## Validation Checklist
- [ ] All existing tests continue to pass
- [ ] New functionality integrates seamlessly
- [ ] Code style matches project conventions
- [ ] Performance requirements met (<10ms)
- [ ] No new external dependencies added
- [ ] DDD layer separation maintained

---

## Ready for Implementation
✅ **5 focused tasks defined**
✅ **Existing structure preserved**
✅ **TDD workflow enforced**
✅ **Integration validation included**

**Estimated Effort**: 4-6 hours for experienced developer
**Risk Level**: LOW (minimal changes to existing codebase)
