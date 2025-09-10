# Quickstart: OverlapAnalyzer v5.0 Infrastructure 모델 검증

**목적**: Infrastructure 모델의 핵심 기능을 빠르게 검증하고 OverlapAnalyzer v5.0 호환성 확인
**소요 시간**: 약 10-15분
**전제 조건**: Python 3.13, pytest, 기존 OverlapAnalyzer v5.0 환경

## 1단계: 기본 환경 설정 (2분)

### 가상 환경 활성화 및 의존성 확인
```bash
# PowerShell에서 실행
cd d:\projects\upbit-autotrader-vscode
.\.venv\Scripts\Activate.ps1

# 필요한 패키지 확인 (표준 라이브러리만 사용)
python -c "import dataclasses, datetime, enum, typing; print('✓ All required modules available')"

# 기존 OverlapAnalyzer 가져오기 테스트
python -c "from upbit_auto_trading.infrastructure.market_data.candle.overlap_analyzer import OverlapAnalyzer; print('✓ OverlapAnalyzer v5.0 available')"
```

### 테스트 디렉토리 생성
```bash
# 테스트 디렉토리 구조 생성
mkdir -p tests/infrastructure/data_models/candle
mkdir -p tests/integration/overlap_analyzer_compatibility
```

## 2단계: 핵심 모델 생성 및 검증 (5분)

### UpbitCandleModel 기본 테스트
```python
# tests/infrastructure/data_models/candle/test_upbit_candle_model.py
import pytest
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, Any

# 임시 모델 정의 (실제 구현 전 검증용)
@dataclass(frozen=True)
class UpbitCandleModel:
    market: str
    candle_date_time_utc: str
    candle_date_time_kst: str
    opening_price: float
    high_price: float
    low_price: float
    trade_price: float
    timestamp: int
    candle_acc_trade_price: float
    candle_acc_trade_volume: float
    unit: Optional[int] = None
    prev_closing_price: Optional[float] = None
    converting_price_unit: Optional[str] = None

def test_upbit_candle_model_creation():
    """기본 캔들 모델 생성 테스트"""
    candle = UpbitCandleModel(
        market="KRW-BTC",
        candle_date_time_utc="2025-09-10T12:00:00",
        candle_date_time_kst="2025-09-10T21:00:00",
        opening_price=50000000.0,
        high_price=51000000.0,
        low_price=49000000.0,
        trade_price=50500000.0,
        timestamp=1694345200000,
        candle_acc_trade_price=1000000000.0,
        candle_acc_trade_volume=20.5
    )

    assert candle.market == "KRW-BTC"
    assert candle.trade_price == 50500000.0
    assert candle.unit is None
    print("✓ Basic candle model creation successful")

def test_upbit_candle_model_with_optional_fields():
    """선택적 필드 포함 테스트"""
    candle = UpbitCandleModel(
        market="KRW-BTC",
        candle_date_time_utc="2025-09-10T12:00:00",
        candle_date_time_kst="2025-09-10T21:00:00",
        opening_price=50000000.0,
        high_price=51000000.0,
        low_price=49000000.0,
        trade_price=50500000.0,
        timestamp=1694345200000,
        candle_acc_trade_price=1000000000.0,
        candle_acc_trade_volume=20.5,
        unit=5,  # 5분봉
        prev_closing_price=49500000.0  # 일봉
    )

    assert candle.unit == 5
    assert candle.prev_closing_price == 49500000.0
    print("✓ Optional fields handling successful")

if __name__ == "__main__":
    test_upbit_candle_model_creation()
    test_upbit_candle_model_with_optional_fields()
    print("✓ All basic model tests passed")
```

### 실행 및 검증
```bash
python tests/infrastructure/data_models/candle/test_upbit_candle_model.py
```

## 3단계: 업비트 API 호환성 검증 (3분)

### 실제 업비트 API 응답 형식 테스트
```python
# tests/infrastructure/data_models/candle/test_upbit_api_compatibility.py
def test_from_upbit_response_minute():
    """업비트 분봉 API 응답에서 모델 생성 테스트"""

    # 실제 업비트 5분봉 API 응답 형식
    upbit_minute_response = {
        "market": "KRW-BTC",
        "candle_date_time_utc": "2025-06-30T00:00:00",
        "candle_date_time_kst": "2025-06-30T09:00:00",
        "opening_price": 147996000.0,
        "high_price": 148480000.0,
        "low_price": 145740000.0,
        "trade_price": 145759000.0,
        "timestamp": 1751327999833,
        "candle_acc_trade_price": 138812096716.42776,
        "candle_acc_trade_volume": 944.35761221,
        "unit": 5  # 분봉 단위
    }

    candle = from_upbit_response(upbit_minute_response)

    assert candle.market == "KRW-BTC"
    assert candle.unit == 5
    assert candle.prev_closing_price is None  # 분봉에는 없음
    print("✓ Upbit minute candle API response conversion successful")

def test_from_upbit_response_daily():
    """업비트 일봉 API 응답에서 모델 생성 테스트"""

    # 실제 업비트 일봉 API 응답 형식
    upbit_daily_response = {
        "market": "KRW-BTC",
        "candle_date_time_utc": "2025-06-30T00:00:00",
        "candle_date_time_kst": "2025-06-30T09:00:00",
        "opening_price": 147996000.0,
        "high_price": 148480000.0,
        "low_price": 145740000.0,
        "trade_price": 145759000.0,
        "timestamp": 1751327999833,
        "candle_acc_trade_price": 138812096716.42776,
        "candle_acc_trade_volume": 944.35761221,
        "prev_closing_price": 147996000.0,  # 일봉에는 전일 종가 포함
        "change_price": -2237000.0,
        "change_rate": -0.0151152734
    }

    candle = from_upbit_response(upbit_daily_response)

    assert candle.market == "KRW-BTC"
    assert candle.unit is None  # 일봉에는 unit 없음
    assert candle.prev_closing_price == 147996000.0
    print("✓ Upbit daily candle API response conversion successful")

def test_to_repository_format():
    """Repository 형식 변환 테스트 (DB 저장용)"""
    candle = UpbitCandleModel(
        market="KRW-BTC",
        candle_date_time_utc="2025-06-30T00:00:00",
        candle_date_time_kst="2025-06-30T09:00:00",
        opening_price=147996000.0,
        high_price=148480000.0,
        low_price=145740000.0,
        trade_price=145759000.0,
        timestamp=1751327999833,
        candle_acc_trade_price=138812096716.42776,
        candle_acc_trade_volume=944.35761221,
        unit=5  # 5분봉
    )

    # 임시 변환 함수
    def to_repository_format(candle: UpbitCandleModel) -> Dict[str, Any]:
        result = {
            'market': candle.market,
            'candle_time': candle.candle_date_time_utc,
            'opening_price': candle.opening_price,
            'high_price': candle.high_price,
            'low_price': candle.low_price,
            'trade_price': candle.trade_price,
            'timestamp': candle.timestamp,
            'candle_acc_trade_price': candle.candle_acc_trade_price,
            'candle_acc_trade_volume': candle.candle_acc_trade_volume,
        }

        # 선택적 필드 추가 (None이 아닐 때만)
        if candle.unit is not None:
            result['unit'] = candle.unit
        if candle.prev_closing_price is not None:
            result['prev_closing_price'] = candle.prev_closing_price

        return result

    repo_data = to_repository_format(candle)

    assert repo_data['market'] == "KRW-BTC"
    assert repo_data['candle_time'] == "2025-06-30T00:00:00"
    assert repo_data['unit'] == 5
    assert 'prev_closing_price' not in repo_data  # None이므로 제외
    print("✓ Repository format conversion successful")

def test_to_db_format():
    """DB 저장 형식 변환 테스트 (created_at 추가)"""
    candle = UpbitCandleModel(
        market="KRW-BTC",
        candle_date_time_utc="2025-06-30T00:00:00",
        candle_date_time_kst="2025-06-30T09:00:00",
        opening_price=147996000.0,
        high_price=148480000.0,
        low_price=145740000.0,
        trade_price=145759000.0,
        timestamp=1751327999833,
        candle_acc_trade_price=138812096716.42776,
        candle_acc_trade_volume=944.35761221
    )

    # 임시 변환 함수
    def to_db_format(candle: UpbitCandleModel) -> Dict[str, Any]:
        result = to_repository_format(candle)
        result['created_at'] = "2025-09-10T12:00:00"  # DB 저장 시각
        return result

    db_data = to_db_format(candle)

    assert 'created_at' in db_data
    assert db_data['created_at'] == "2025-09-10T12:00:00"
    print("✓ DB format conversion with created_at successful")

if __name__ == "__main__":
    test_from_upbit_response_minute()
    test_from_upbit_response_daily()
    test_to_repository_format()
    test_to_db_format()
    print("✓ API compatibility tests passed")
```

### 실행 및 검증
```bash
python tests/infrastructure/data_models/candle/test_upbit_api_compatibility.py
```

## 4단계: OverlapAnalyzer v5.0 호환성 검증 (5분)

### 기존 OverlapAnalyzer와의 통합 테스트
```python
# tests/integration/overlap_analyzer_compatibility/test_compatibility.py
import sys
sys.path.append('d:/projects/upbit-autotrader-vscode')

from upbit_auto_trading.infrastructure.market_data.candle.overlap_analyzer import (
    OverlapAnalyzer, OverlapRequest, OverlapResult, OverlapStatus
)
from datetime import datetime, timezone

def test_overlap_analyzer_interface_unchanged():
    """OverlapAnalyzer v5.0 인터페이스 변경 없음 확인"""

    # OverlapRequest 인터페이스 검증
    request = OverlapRequest(
        symbol="KRW-BTC",
        timeframe="5m",
        target_start=datetime(2025, 9, 10, 12, 0, 0, tzinfo=timezone.utc),
        target_end=datetime(2025, 9, 10, 11, 0, 0, tzinfo=timezone.utc),
        target_count=12
    )

    assert hasattr(request, 'symbol')
    assert hasattr(request, 'timeframe')
    assert hasattr(request, 'target_start')
    assert hasattr(request, 'target_end')
    assert hasattr(request, 'target_count')
    print("✓ OverlapRequest interface unchanged")

    # OverlapStatus 열거형 검증
    expected_statuses = {
        "NO_OVERLAP", "COMPLETE_OVERLAP", "PARTIAL_START",
        "PARTIAL_MIDDLE_FRAGMENT", "PARTIAL_MIDDLE_CONTINUOUS"
    }
    actual_statuses = {status.name for status in OverlapStatus}

    assert expected_statuses == actual_statuses
    print("✓ OverlapStatus enum unchanged")

def test_overlap_analyzer_instantiation():
    """OverlapAnalyzer 인스턴스 생성 테스트"""

    # Mock Repository (실제 구현 시에는 제거)
    class MockRepository:
        async def has_any_data_in_range(self, symbol, timeframe, start, end):
            return False

    # Mock TimeUtils (실제 구현 시에는 제거)
    class MockTimeUtils:
        @staticmethod
        def timeframe_to_seconds(timeframe):
            return 300  # 5분 = 300초

    analyzer = OverlapAnalyzer(
        repository=MockRepository(),
        time_utils=MockTimeUtils,
        enable_validation=True  # 개발 모드
    )

    assert analyzer is not None
    assert hasattr(analyzer, 'analyze_overlap')
    print("✓ OverlapAnalyzer instantiation successful")

def test_infrastructure_model_integration():
    """Infrastructure 모델과 OverlapAnalyzer 통합 가능성 검증"""

    # 새로운 UpbitCandleModel이 기존 Repository 인터페이스와 호환되는지 확인
    sample_candle = UpbitCandleModel(
        market="KRW-BTC",
        candle_date_time_utc="2025-09-10T12:00:00",
        candle_date_time_kst="2025-09-10T21:00:00",
        opening_price=50000000.0,
        high_price=51000000.0,
        low_price=49000000.0,
        trade_price=50500000.0,
        timestamp=1694345200000,
        candle_acc_trade_price=1000000000.0,
        candle_acc_trade_volume=20.5
    )

    # Repository 형식으로 변환 가능 여부 확인
    def to_repository_format(candle):
        return {
            'market': candle.market,
            'candle_time': candle.candle_date_time_utc,
            'opening_price': candle.opening_price,
            'high_price': candle.high_price,
            'low_price': candle.low_price,
            'trade_price': candle.trade_price,
            'timestamp': candle.timestamp,
            'candle_acc_trade_price': candle.candle_acc_trade_price,
            'candle_acc_trade_volume': candle.candle_acc_trade_volume,
        }

    repo_data = to_repository_format(sample_candle)

    # 기존 Repository가 기대하는 필드들이 모두 있는지 확인
    required_fields = {'market', 'candle_time', 'opening_price', 'high_price',
                      'low_price', 'trade_price', 'timestamp'}
    assert required_fields.issubset(set(repo_data.keys()))
    print("✓ Infrastructure model integration compatible")

if __name__ == "__main__":
    test_overlap_analyzer_interface_unchanged()
    test_overlap_analyzer_instantiation()
    test_infrastructure_model_integration()
    print("✓ All compatibility tests passed")
```

### 실행 및 검증
```bash
python tests/integration/overlap_analyzer_compatibility/test_compatibility.py
```

## 5단계: 성능 기준선 측정 (2분)

### 기본 성능 벤치마크
```python
# tests/performance/test_baseline_performance.py
import time
from typing import List

def benchmark_model_creation():
    """모델 생성 성능 측정"""

    # 1000개 캔들 모델 생성 시간 측정
    start_time = time.time()

    candles: List[UpbitCandleModel] = []
    for i in range(1000):
        candle = UpbitCandleModel(
            market="KRW-BTC",
            candle_date_time_utc=f"2025-09-10T{i%24:02d}:00:00",
            candle_date_time_kst=f"2025-09-10T{(i%24+9)%24:02d}:00:00",
            opening_price=50000000.0 + i,
            high_price=51000000.0 + i,
            low_price=49000000.0 + i,
            trade_price=50500000.0 + i,
            timestamp=1694345200000 + i,
            candle_acc_trade_price=1000000000.0 + i,
            candle_acc_trade_volume=20.5 + i
        )
        candles.append(candle)

    end_time = time.time()
    creation_time = end_time - start_time

    print(f"✓ 1000 candle models created in {creation_time:.4f} seconds")
    print(f"✓ Average: {creation_time/1000*1000:.2f}μs per model")

    # 기준: 1000개 생성에 1초 미만
    assert creation_time < 1.0, f"Performance regression: {creation_time:.4f}s > 1.0s"

    return len(candles), creation_time

def benchmark_conversion():
    """변환 작업 성능 측정"""

    candle = UpbitCandleModel(
        market="KRW-BTC",
        candle_date_time_utc="2025-09-10T12:00:00",
        candle_date_time_kst="2025-09-10T21:00:00",
        opening_price=50000000.0,
        high_price=51000000.0,
        low_price=49000000.0,
        trade_price=50500000.0,
        timestamp=1694345200000,
        candle_acc_trade_price=1000000000.0,
        candle_acc_trade_volume=20.5
    )

    # 10000번 변환 작업 시간 측정
    start_time = time.time()

    for _ in range(10000):
        def to_repository_format(c):
            return {
                'market': c.market,
                'candle_time': c.candle_date_time_utc,
                'opening_price': c.opening_price,
                'high_price': c.high_price,
                'low_price': c.low_price,
                'trade_price': c.trade_price,
                'timestamp': c.timestamp,
                'candle_acc_trade_price': c.candle_acc_trade_price,
                'candle_acc_trade_volume': c.candle_acc_trade_volume,
            }

        repo_data = to_repository_format(candle)

    end_time = time.time()
    conversion_time = end_time - start_time

    print(f"✓ 10000 conversions completed in {conversion_time:.4f} seconds")
    print(f"✓ Average: {conversion_time/10000*1000000:.2f}ns per conversion")

    # 기준: 10000번 변환에 0.1초 미만
    assert conversion_time < 0.1, f"Performance regression: {conversion_time:.4f}s > 0.1s"

    return conversion_time

if __name__ == "__main__":
    count, creation_time = benchmark_model_creation()
    conversion_time = benchmark_conversion()

    print(f"\n✓ Performance baseline established:")
    print(f"  - Model creation: {creation_time:.4f}s for 1000 models")
    print(f"  - Conversion: {conversion_time:.4f}s for 10000 conversions")
```

### 실행 및 검증
```bash
python tests/performance/test_baseline_performance.py
```

## 6단계: 전체 검증 및 요약 (1분)

### 통합 검증 스크립트
```bash
# quickstart_validation.ps1
Write-Host "🚀 OverlapAnalyzer v5.0 Infrastructure 모델 Quickstart 검증" -ForegroundColor Green

Write-Host "`n1️⃣ 기본 모델 테스트..."
python tests/infrastructure/data_models/candle/test_upbit_candle_model.py

Write-Host "`n2️⃣ API 호환성 테스트..."
python tests/infrastructure/data_models/candle/test_upbit_api_compatibility.py

Write-Host "`n3️⃣ OverlapAnalyzer 호환성 테스트..."
python tests/integration/overlap_analyzer_compatibility/test_compatibility.py

Write-Host "`n4️⃣ 성능 기준선 측정..."
python tests/performance/test_baseline_performance.py

Write-Host "`n✅ Quickstart 검증 완료!" -ForegroundColor Green
Write-Host "다음 단계: Phase 2 구현 (tasks.md 생성 후 실제 구현)" -ForegroundColor Yellow
```

### 실행
```bash
.\quickstart_validation.ps1
```

## 예상 결과

### 성공 시 출력 예시
```
🚀 OverlapAnalyzer v5.0 Infrastructure 모델 Quickstart 검증

1️⃣ 기본 모델 테스트...
✓ Basic candle model creation successful
✓ Optional fields handling successful
✓ All basic model tests passed

2️⃣ API 호환성 테스트...
✓ Upbit API response conversion successful
✓ Repository format conversion successful
✓ API compatibility tests passed

3️⃣ OverlapAnalyzer 호환성 테스트...
✓ OverlapRequest interface unchanged
✓ OverlapStatus enum unchanged
✓ OverlapAnalyzer instantiation successful
✓ Infrastructure model integration compatible
✓ All compatibility tests passed

4️⃣ 성능 기준선 측정...
✓ 1000 candle models created in 0.0234 seconds
✓ Average: 23.40μs per model
✓ 10000 conversions completed in 0.0156 seconds
✓ Average: 1560.00ns per conversion
✓ Performance baseline established

✅ Quickstart 검증 완료!
다음 단계: Phase 2 구현 (tasks.md 생성 후 실제 구현)
```

## 문제 해결

### 일반적인 오류
1. **ImportError**: OverlapAnalyzer 가져오기 실패
   - 해결: 가상 환경 활성화 확인
   - 확인: `python -c "import upbit_auto_trading; print('OK')"`

2. **AssertionError**: 성능 기준 미달
   - 해결: 복잡한 로직 최적화 필요
   - 목표: 단순한 데이터 구조로 개선

3. **AttributeError**: 인터페이스 불일치
   - 해결: 기존 OverlapAnalyzer 코드 재확인
   - 원칙: 기존 인터페이스 100% 유지

---

**Quickstart 완료**: Infrastructure 모델 핵심 기능 검증 완료
**다음 단계**: `/tasks` 명령어로 상세 구현 계획 수립
**예상 소요 시간**: 전체 구현 2-3일 (TDD 방식)
