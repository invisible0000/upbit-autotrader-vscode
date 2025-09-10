# 🧪 CandleDataProvider v5.0 - Test Strategy & Validation Plan
> 단위 테스트, 통합 테스트, 성능 테스트 및 메인 프로그램 통합 검증 계획

## 🎯 Testing Overview

### Testing Pyramid
```
┌─────────────────────┐
│   E2E Tests (5%)    │  ← 메인 프로그램 통합 (python run_desktop_ui.py)
├─────────────────────┤
│ Integration (25%)   │  ← 컴포넌트 간 연동 테스트
├─────────────────────┤
│  Unit Tests (70%)   │  ← 개별 메서드 테스트
└─────────────────────┘
```

### Test Categories
1. **Unit Tests**: 개별 메서드 단위 테스트
2. **Integration Tests**: 기반 컴포넌트와의 연동 테스트
3. **Performance Tests**: 응답 시간 및 처리량 검증
4. **E2E Tests**: 메인 프로그램 통합 검증
5. **Error Handling Tests**: 예외 상황 처리 검증

---

## 🔧 Unit Tests (70%)

### Test Structure
```
tests/infrastructure/data_providers/candle/
├── test_candle_data_provider_unit.py       # 메인 단위 테스트
├── test_parameter_validation.py            # 파라미터 검증 테스트
├── test_chunk_processing.py               # 청크 처리 테스트
├── test_cache_operations.py               # 캐시 동작 테스트
└── test_error_handling.py                 # 에러 처리 테스트
```

### 1. Core Method Tests

#### 1.1 get_candles() Parameter Combinations
```python
import pytest
from datetime import datetime, timezone, timedelta
from upbit_auto_trading.infrastructure.market_data.candle.candle_data_provider import CandleDataProvider
from upbit_auto_trading.infrastructure.market_data.candle.candle_models import CandleDataResponse

class TestGetCandlesParameterCombinations:
    """get_candles() 5가지 파라미터 조합 테스트"""

    @pytest.fixture
    async def provider(self):
        """테스트용 CandleDataProvider 인스턴스"""
        # Mock 의존성으로 테스트용 인스턴스 생성
        return CandleDataProvider(mock_db_manager, mock_upbit_client)

    async def test_count_only(self, provider):
        """케이스 1: count만 - 최신 데이터부터 역순"""
        response = await provider.get_candles("KRW-BTC", "5m", count=100)

        assert response.success is True
        assert response.total_count == 100
        assert len(response.candles) == 100
        # 시간순 정렬 확인 (과거 → 최신)
        timestamps = [c.candle_date_time_utc for c in response.candles]
        assert timestamps == sorted(timestamps)

    async def test_start_time_plus_count(self, provider):
        """케이스 2: start_time + count - 특정 시점부터"""
        start_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        response = await provider.get_candles("KRW-BTC", "1d", start_time=start_time, count=30)

        assert response.success is True
        assert response.total_count == 30
        # 첫 번째 캔들이 start_time 이후인지 확인 (inclusive_start=True)
        first_candle_time = datetime.fromisoformat(response.candles[0].candle_date_time_utc.replace('Z', ''))
        assert first_candle_time >= start_time

    async def test_start_time_plus_end_time(self, provider):
        """케이스 3: start_time + end_time - 구간 지정"""
        start_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 31, tzinfo=timezone.utc)
        response = await provider.get_candles("KRW-BTC", "1d", start_time=start_time, end_time=end_time)

        assert response.success is True
        assert response.total_count > 0
        # 모든 캔들이 지정 범위 내인지 확인
        for candle in response.candles:
            candle_time = datetime.fromisoformat(candle.candle_date_time_utc.replace('Z', ''))
            assert start_time <= candle_time <= end_time

    async def test_inclusive_start_false(self, provider):
        """inclusive_start=False - 업비트 API 네이티브 동작"""
        start_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        response = await provider.get_candles(
            "KRW-BTC", "1d", start_time=start_time, count=30, inclusive_start=False
        )

        assert response.success is True
        # 첫 번째 캔들이 start_time 이후인지 확인 (start_time 제외)
        first_candle_time = datetime.fromisoformat(response.candles[0].candle_date_time_utc.replace('Z', ''))
        assert first_candle_time > start_time
```

#### 1.2 Parameter Validation Tests
```python
class TestParameterValidation:
    """파라미터 검증 테스트"""

    async def test_no_parameters_error(self, provider):
        """필수 파라미터 없을 시 ValidationError"""
        with pytest.raises(ValidationError, match="count, start_time\\+count, 또는 start_time\\+end_time 중 하나는 필수"):
            await provider.get_candles("KRW-BTC", "5m")

    async def test_invalid_timeframe(self, provider):
        """지원하지 않는 타임프레임"""
        with pytest.raises(ValidationError, match="지원하지 않는 타임프레임"):
            await provider.get_candles("KRW-BTC", "2m", count=100)

    async def test_count_out_of_range(self, provider):
        """count 범위 초과"""
        with pytest.raises(ValidationError, match="count는 1 이상 10000 이하"):
            await provider.get_candles("KRW-BTC", "5m", count=15000)

    async def test_future_time_request(self, provider):
        """미래 시간 요청 에러"""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        with pytest.raises(ValidationError, match="미래 시간"):
            await provider.get_candles("KRW-BTC", "5m", start_time=future_time, count=100)

    async def test_invalid_time_order(self, provider):
        """start_time >= end_time 에러"""
        start_time = datetime(2024, 1, 31, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        with pytest.raises(ValidationError, match="start_time은 end_time보다 이전"):
            await provider.get_candles("KRW-BTC", "1d", start_time=start_time, end_time=end_time)
```

#### 1.3 Timeframe Support Tests
```python
class TestTimeframeSupport:
    """27개 타임프레임 지원 테스트"""

    @pytest.mark.parametrize("timeframe", [
        '1s', '1m', '3m', '5m', '10m', '15m', '30m', '60m', '240m',
        '1h', '4h', '1d', '1w', '1M', '1y'
    ])
    async def test_all_supported_timeframes(self, provider, timeframe):
        """모든 지원 타임프레임 테스트"""
        response = await provider.get_candles("KRW-BTC", timeframe, count=10)
        assert response.success is True
        assert len(response.candles) <= 10  # 실제 데이터가 없을 수도 있음

    def test_get_supported_timeframes(self, provider):
        """지원 타임프레임 목록 반환 테스트"""
        timeframes = provider.get_supported_timeframes()
        assert len(timeframes) == 15  # 27개에서 중복 제거
        assert '1m' in timeframes
        assert '1d' in timeframes
        assert '1y' in timeframes
```

### 2. Chunk Processing Tests

```python
class TestChunkProcessing:
    """청크 처리 로직 테스트"""

    async def test_auto_chunk_splitting(self, provider):
        """200개 초과시 자동 청크 분할"""
        response = await provider.get_candles("KRW-BTC", "5m", count=500)

        assert response.success is True
        assert response.total_count <= 500
        # 내부적으로 3개 청크(200+200+100)로 분할되었음을 로그로 확인

    async def test_target_end_time_early_termination(self, provider):
        """target_end_time 도달시 조기 중단"""
        start_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 15, tzinfo=timezone.utc)  # 14일 = 약 280개 5분봉

        response = await provider.get_candles("KRW-BTC", "5m", start_time=start_time, end_time=end_time)

        assert response.success is True
        # 모든 캔들이 end_time 이전인지 확인
        for candle in response.candles:
            candle_time = datetime.fromisoformat(candle.candle_date_time_utc.replace('Z', ''))
            assert candle_time <= end_time

    def test_chunk_model_creation(self, provider):
        """CandleChunk 모델 생성 테스트"""
        chunks = provider._split_into_chunks("KRW-BTC", "1m", 350, start_time, end_time)

        assert len(chunks) == 2  # 200 + 150
        assert chunks[0].count == 200
        assert chunks[1].count == 150
        assert chunks[0].chunk_index == 0
        assert chunks[1].chunk_index == 1
```

### 3. Cache Operations Tests

```python
class TestCacheOperations:
    """캐시 동작 테스트"""

    async def test_cache_hit(self, provider):
        """캐시 히트 테스트"""
        # 첫 번째 요청 (캐시 미스)
        response1 = await provider.get_candles("KRW-BTC", "5m", count=100)
        assert response1.data_source in ["api", "db", "mixed"]

        # 두 번째 동일 요청 (캐시 히트)
        response2 = await provider.get_candles("KRW-BTC", "5m", count=100)
        assert response2.data_source == "cache"
        assert response2.response_time_ms < 20  # 캐시는 20ms 이하

    async def test_cache_expiry(self, provider):
        """캐시 만료 테스트"""
        # 첫 번째 요청
        response1 = await provider.get_candles("KRW-BTC", "5m", count=100)

        # 캐시 강제 만료 (테스트용)
        provider.cache.cleanup_expired()

        # 만료 후 요청 (캐시 미스)
        response2 = await provider.get_candles("KRW-BTC", "5m", count=100)
        assert response2.data_source != "cache"

    def test_cache_stats(self, provider):
        """캐시 통계 테스트"""
        stats = provider.get_cache_stats()

        assert 'total_entries' in stats
        assert 'memory_usage_mb' in stats
        assert 'hit_rate' in stats
        assert stats['memory_usage_mb'] >= 0
```

---

## 🔗 Integration Tests (25%)

### Test Structure
```
tests/infrastructure/integration/candle/
├── test_overlap_analyzer_integration.py   # OverlapAnalyzer 통합
├── test_time_utils_integration.py         # TimeUtils 통합
├── test_repository_integration.py         # Repository 통합
├── test_models_integration.py             # Models 통합
└── test_full_component_integration.py     # 전체 통합
```

### 1. OverlapAnalyzer Integration Tests

```python
class TestOverlapAnalyzerIntegration:
    """OverlapAnalyzer v5.0 통합 테스트"""

    @pytest.fixture
    async def provider_with_real_db(self):
        """실제 DB를 사용하는 테스트용 provider"""
        db_manager = DatabaseManager()
        return CandleDataProvider(db_manager, mock_upbit_client)

    async def test_no_overlap_scenario(self, provider_with_real_db):
        """NO_OVERLAP 시나리오 - 전체 API 요청"""
        # DB에 데이터가 없는 새로운 심볼로 테스트
        response = await provider_with_real_db.get_candles("TEST-SYMBOL", "5m", count=100)

        # OverlapAnalyzer가 NO_OVERLAP 판단 → 전체 API 요청
        assert response.data_source == "api"

    async def test_complete_overlap_scenario(self, provider_with_real_db):
        """COMPLETE_OVERLAP 시나리오 - 전체 DB 조회"""
        # 먼저 데이터를 DB에 저장
        await self._prepare_complete_data("KRW-BTC", "5m", 100)

        response = await provider_with_real_db.get_candles("KRW-BTC", "5m", count=100)

        # OverlapAnalyzer가 COMPLETE_OVERLAP 판단 → 전체 DB 조회
        assert response.data_source == "db"
        assert response.total_count == 100

    async def test_partial_start_scenario(self, provider_with_real_db):
        """PARTIAL_START 시나리오 - 시작 부분 혼합"""
        # 부분적으로만 데이터 준비 (최신 50개만)
        await self._prepare_partial_data("KRW-BTC", "5m", recent_count=50, total_request=100)

        response = await provider_with_real_db.get_candles("KRW-BTC", "5m", count=100)

        # OverlapAnalyzer가 PARTIAL_START 판단 → 혼합 처리
        assert response.data_source == "mixed"
        assert response.total_count == 100

    async def test_five_state_classification(self, provider_with_real_db):
        """5가지 상태 분류 모두 테스트"""
        test_scenarios = [
            ("NO_OVERLAP", self._setup_no_overlap),
            ("COMPLETE_OVERLAP", self._setup_complete_overlap),
            ("PARTIAL_START", self._setup_partial_start),
            ("PARTIAL_MIDDLE_FRAGMENT", self._setup_partial_middle_fragment),
            ("PARTIAL_MIDDLE_CONTINUOUS", self._setup_partial_middle_continuous)
        ]

        for expected_status, setup_func in test_scenarios:
            # 각 시나리오별 DB 상태 설정
            symbol = f"TEST-{expected_status}"
            await setup_func(symbol, "5m", 100)

            # CandleDataProvider 호출
            response = await provider_with_real_db.get_candles(symbol, "5m", count=100)

            # 결과 검증 (로그에서 OverlapAnalyzer 상태 확인)
            assert response.success is True
```

### 2. TimeUtils Integration Tests

```python
class TestTimeUtilsIntegration:
    """TimeUtils 통합 테스트"""

    async def test_timeframe_calculation_accuracy(self, provider):
        """타임프레임 계산 정확성 테스트"""
        start_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 2, tzinfo=timezone.utc)  # 24시간 = 1440분

        response = await provider.get_candles("KRW-BTC", "1m", start_time=start_time, end_time=end_time)

        # TimeUtils 계산이 정확한지 확인
        expected_count = 24 * 60  # 1440개
        assert response.total_count <= expected_count  # 실제 데이터는 적을 수 있음

    async def test_chunk_time_sequence_generation(self, provider):
        """청크별 시간 시퀀스 생성 테스트"""
        start_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

        # 350개 요청 → 2개 청크(200+150)
        response = await provider.get_candles("KRW-BTC", "5m", start_time=start_time, count=350)

        # 시간 순서가 정확한지 확인 (TimeUtils.generate_time_sequence 검증)
        timestamps = [datetime.fromisoformat(c.candle_date_time_utc.replace('Z', '')) for c in response.candles]
        assert timestamps == sorted(timestamps)

        # 시간 간격이 정확한지 확인 (5분 = 300초)
        for i in range(1, min(10, len(timestamps))):
            time_diff = (timestamps[i] - timestamps[i-1]).total_seconds()
            assert time_diff == 300  # 5분봉 간격

    @pytest.mark.parametrize("timeframe,expected_seconds", [
        ("1s", 1), ("1m", 60), ("5m", 300), ("1h", 3600), ("1d", 86400)
    ])
    def test_timeframe_seconds_integration(self, provider, timeframe, expected_seconds):
        """타임프레임 초 변환 통합 테스트"""
        # provider 내부에서 TimeUtils.get_timeframe_seconds() 호출
        actual_seconds = provider.time_utils.get_timeframe_seconds(timeframe)
        assert actual_seconds == expected_seconds
```

### 3. Repository Integration Tests

```python
class TestRepositoryIntegration:
    """SqliteCandleRepository 통합 테스트"""

    async def test_save_and_retrieve_cycle(self, provider_with_real_db):
        """저장 → 조회 사이클 테스트"""
        # 1. API로 데이터 수집 (자동 저장)
        response1 = await provider_with_real_db.get_candles("KRW-BTC", "1m", count=50)
        assert response1.success is True
        original_count = response1.total_count

        # 2. 동일 요청으로 DB에서 조회 (캐시 비활성화)
        provider_with_real_db.cache.clear()  # 캐시 비워서 DB 조회 강제
        response2 = await provider_with_real_db.get_candles("KRW-BTC", "1m", count=50)

        assert response2.data_source == "db"
        assert response2.total_count == original_count
        # 데이터 내용이 동일한지 확인
        assert response1.candles[0].trade_price == response2.candles[0].trade_price

    async def test_repository_method_coverage(self, provider_with_real_db):
        """Repository 10개 메서드 활용 확인"""
        symbol, timeframe = "KRW-BTC", "5m"

        # 데이터 준비
        await provider_with_real_db.get_candles(symbol, timeframe, count=100)

        # Repository 메서드들이 실제로 호출되는지 확인 (로그 또는 Mock 활용)
        repo = provider_with_real_db.repository

        # 1. has_any_data_in_range
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        end_time = datetime.now(timezone.utc)
        has_data = await repo.has_any_data_in_range(symbol, timeframe, start_time, end_time)
        assert isinstance(has_data, bool)

        # 2. is_range_complete
        is_complete = await repo.is_range_complete(symbol, timeframe, start_time, end_time, 12)
        assert isinstance(is_complete, bool)

        # 3. find_last_continuous_time
        last_time = await repo.find_last_continuous_time(symbol, timeframe, start_time)
        assert last_time is None or isinstance(last_time, datetime)
```

---

## ⚡ Performance Tests (Performance Validation)

### Test Structure
```
tests/infrastructure/performance/candle/
├── test_response_time_targets.py          # 응답 시간 목표 검증
├── test_cache_performance.py              # 캐시 성능 테스트
├── test_chunk_processing_performance.py   # 청크 처리 성능
└── test_memory_usage.py                   # 메모리 사용량 테스트
```

### 1. Response Time Targets

```python
class TestResponseTimeTargets:
    """응답 시간 목표 검증"""

    @pytest.mark.performance
    async def test_100_candles_response_time(self, provider):
        """100개 캔들: 평균 50ms 이하"""
        response_times = []

        for _ in range(10):  # 10회 측정
            start_time = time.perf_counter()
            response = await provider.get_candles("KRW-BTC", "5m", count=100)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            assert response.success is True
            response_times.append(elapsed_ms)

        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 50, f"평균 응답시간 {avg_response_time:.2f}ms > 50ms"

    @pytest.mark.performance
    async def test_1000_candles_response_time(self, provider):
        """1000개 캔들: 평균 500ms 이하"""
        start_time = time.perf_counter()
        response = await provider.get_candles("KRW-BTC", "5m", count=1000)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert response.success is True
        assert elapsed_ms < 500, f"응답시간 {elapsed_ms:.2f}ms > 500ms"

    @pytest.mark.performance
    async def test_cache_hit_response_time(self, provider):
        """캐시 히트: 평균 10ms 이하"""
        # 첫 번째 요청으로 캐시 생성
        await provider.get_candles("KRW-BTC", "5m", count=100)

        # 캐시 히트 테스트
        cache_response_times = []
        for _ in range(5):
            start_time = time.perf_counter()
            response = await provider.get_candles("KRW-BTC", "5m", count=100)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            assert response.data_source == "cache"
            cache_response_times.append(elapsed_ms)

        avg_cache_time = sum(cache_response_times) / len(cache_response_times)
        assert avg_cache_time < 10, f"캐시 평균 응답시간 {avg_cache_time:.2f}ms > 10ms"
```

### 2. Memory Usage Tests

```python
class TestMemoryUsage:
    """메모리 사용량 테스트"""

    @pytest.mark.performance
    async def test_cache_memory_limit(self, provider):
        """캐시 메모리 100MB 제한 테스트"""
        # 대량 요청으로 캐시 채우기
        for i in range(50):
            symbol = f"TEST-{i:02d}"
            await provider.get_candles(symbol, "1m", count=200)

        cache_stats = provider.get_cache_stats()
        assert cache_stats['memory_usage_mb'] <= 100, "캐시 메모리 한계 초과"

    @pytest.mark.performance
    async def test_chunk_processing_memory(self, provider):
        """청크 처리시 메모리 사용량 제한"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # 대량 요청 (자동 청크 분할)
        response = await provider.get_candles("KRW-BTC", "1m", count=5000)

        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before

        assert response.success is True
        assert memory_increase < 200, f"메모리 증가량 {memory_increase:.2f}MB > 200MB"
```

---

## 🔄 E2E Tests (5%)

### Test Structure
```
tests/e2e/
├── test_main_program_integration.py       # 메인 프로그램 통합
├── test_ui_chart_integration.py           # UI 차트 통합
└── test_7_rules_strategy_integration.py   # 7규칙 전략 통합
```

### 1. Main Program Integration

```python
class TestMainProgramIntegration:
    """메인 프로그램 통합 테스트"""

    @pytest.mark.e2e
    def test_desktop_ui_startup(self):
        """python run_desktop_ui.py 정상 실행 테스트"""
        import subprocess
        import time

        # UI 실행 (백그라운드)
        process = subprocess.Popen(
            ["python", "run_desktop_ui.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # 5초 대기 후 종료
        time.sleep(5)
        process.terminate()

        # 에러 없이 실행되었는지 확인
        stdout, stderr = process.communicate()
        assert process.returncode == 0 or process.returncode == -15, f"UI 실행 실패: {stderr.decode()}"

    @pytest.mark.e2e
    async def test_candle_data_provider_in_main_program(self):
        """메인 프로그램 내에서 CandleDataProvider 사용 테스트"""
        from run_desktop_ui import main_app  # 메인 앱 import

        # 메인 앱에서 CandleDataProvider 인스턴스 가져오기
        app = main_app()
        provider = app.get_candle_data_provider()

        # 정상 동작 확인
        response = await provider.get_candles("KRW-BTC", "5m", count=10)
        assert response.success is True
        assert len(response.candles) > 0
```

### 2. UI Chart Integration

```python
class TestUIChartIntegration:
    """UI 차트 통합 테스트"""

    @pytest.mark.e2e
    async def test_chart_data_loading(self):
        """차트 위젯에서 캔들 데이터 로딩 테스트"""
        from upbit_auto_trading.ui.desktop.components.charts.candle_chart_widget import CandleChartWidget

        # 차트 위젯 생성
        chart_widget = CandleChartWidget()

        # 데이터 로딩 (CandleDataProvider 사용)
        await chart_widget.load_candle_data("KRW-BTC", "5m", count=100)

        # 차트에 데이터가 로드되었는지 확인
        assert chart_widget.has_data() is True
        assert chart_widget.get_candle_count() == 100

    @pytest.mark.e2e
    async def test_realtime_chart_update(self):
        """실시간 차트 업데이트 테스트"""
        from upbit_auto_trading.ui.desktop.components.charts.realtime_chart import RealtimeChart

        chart = RealtimeChart("KRW-BTC", "1m")

        # 실시간 업데이트 시작
        await chart.start_realtime_update()

        # 3초 대기 후 데이터 확인
        await asyncio.sleep(3)

        assert chart.get_latest_price() > 0
        assert chart.get_update_count() >= 1

        await chart.stop_realtime_update()
```

### 3. 7 Rules Strategy Integration

```python
class TestSevenRulesStrategyIntegration:
    """7규칙 전략 통합 테스트"""

    @pytest.mark.e2e
    async def test_strategy_candle_data_access(self):
        """7규칙 전략에서 캔들 데이터 접근 테스트"""
        from upbit_auto_trading.application.trading.strategies.seven_rules_strategy import SevenRulesStrategy

        strategy = SevenRulesStrategy("KRW-BTC")

        # 전략에서 캔들 데이터 요청
        market_data = await strategy.get_market_data()

        assert market_data is not None
        assert len(market_data.candles) > 0
        assert market_data.symbol == "KRW-BTC"

    @pytest.mark.e2e
    async def test_rsi_calculation_with_real_data(self):
        """실제 캔들 데이터로 RSI 계산 테스트"""
        from upbit_auto_trading.infrastructure.market_data.candle.candle_data_provider import create_candle_data_provider

        provider = create_candle_data_provider()
        response = await provider.get_candles("KRW-BTC", "5m", count=100)

        # RSI 계산 (7규칙 전략의 기술적 분석)
        prices = [candle.trade_price for candle in response.candles]
        rsi = calculate_rsi(prices, period=14)

        assert 0 <= rsi <= 100
        assert isinstance(rsi, float)
```

---

## 🚨 Error Handling Tests

### Test Structure
```
tests/infrastructure/error_handling/candle/
├── test_validation_errors.py              # 검증 에러 테스트
├── test_network_errors.py                 # 네트워크 에러 테스트
├── test_rate_limit_handling.py            # Rate Limit 처리 테스트
└── test_graceful_degradation.py           # 점진적 저하 테스트
```

### 1. Error Recovery Tests

```python
class TestErrorRecovery:
    """에러 복구 테스트"""

    @pytest.mark.error_handling
    async def test_api_failure_db_fallback(self, provider_with_mocked_api):
        """API 실패시 DB 폴백 테스트"""
        # API를 실패하도록 Mock 설정
        provider_with_mocked_api.upbit_client.get_candles.side_effect = NetworkError("Connection failed")

        # DB에 데이터가 있는 상황
        await self._prepare_db_data("KRW-BTC", "5m", 100)

        response = await provider_with_mocked_api.get_candles("KRW-BTC", "5m", count=100)

        # DB 폴백으로 성공해야 함
        assert response.success is True
        assert response.data_source == "db"

    @pytest.mark.error_handling
    async def test_rate_limit_exponential_backoff(self, provider_with_mocked_api):
        """Rate Limit 지수 백오프 테스트"""
        # Rate Limit 에러를 3회 발생시킨 후 성공하도록 Mock 설정
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise RateLimitError("Rate limit exceeded")
            return mock_api_response

        provider_with_mocked_api.upbit_client.get_candles.side_effect = side_effect

        start_time = time.perf_counter()
        response = await provider_with_mocked_api.get_candles("KRW-BTC", "5m", count=100)
        elapsed_time = time.perf_counter() - start_time

        # 재시도 성공
        assert response.success is True
        # 지수 백오프로 인한 지연 (1초 + 2초 + 4초 = 7초 이상)
        assert elapsed_time >= 7

    @pytest.mark.error_handling
    async def test_partial_chunk_failure_handling(self, provider_with_mocked_api):
        """일부 청크 실패시 처리 테스트"""
        # 청크 1은 성공, 청크 2는 실패하도록 설정
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # 두 번째 청크만 실패
                raise NetworkError("Network timeout")
            return mock_api_response

        provider_with_mocked_api.upbit_client.get_candles.side_effect = side_effect

        response = await provider_with_mocked_api.get_candles("KRW-BTC", "5m", count=350)  # 2개 청크

        # 부분 성공도 유효한 응답
        assert response.success is True
        assert response.total_count > 0  # 일부 데이터라도 반환
        assert "mixed" in response.data_source or "api" in response.data_source
```

---

## 🎯 Test Execution Strategy

### 1. 개발 단계별 테스트

#### Phase 1: Unit Tests (개발 중)
```powershell
# 개별 메서드 테스트
pytest tests/infrastructure/data_providers/candle/test_candle_data_provider_unit.py -v

# 파라미터 검증 테스트
pytest tests/infrastructure/data_providers/candle/test_parameter_validation.py -v

# 빠른 피드백 루프
pytest tests/infrastructure/data_providers/candle/ -k "not integration and not performance and not e2e"
```

#### Phase 2: Integration Tests (컴포넌트 완성 후)
```powershell
# 기반 컴포넌트 통합 테스트
pytest tests/infrastructure/integration/candle/ -v

# 특정 통합 테스트
pytest tests/infrastructure/integration/candle/test_overlap_analyzer_integration.py -v
```

#### Phase 3: Performance Tests (최적화 후)
```powershell
# 성능 테스트 (시간 소요)
pytest tests/infrastructure/performance/candle/ -v -m performance

# 메모리 사용량 테스트
pytest tests/infrastructure/performance/candle/test_memory_usage.py -v
```

#### Phase 4: E2E Tests (전체 완성 후)
```powershell
# 메인 프로그램 통합 테스트
pytest tests/e2e/ -v -m e2e

# UI 통합 테스트 (GUI 환경 필요)
pytest tests/e2e/test_ui_chart_integration.py -v -s
```

### 2. CI/CD Pipeline Integration

```yaml
# .github/workflows/candle_data_provider_tests.yml
name: CandleDataProvider Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run Unit Tests
        run: pytest tests/infrastructure/data_providers/candle/ -v --tb=short

  integration-tests:
    needs: unit-tests
    runs-on: windows-latest
    steps:
      - name: Run Integration Tests
        run: pytest tests/infrastructure/integration/candle/ -v

  performance-tests:
    needs: integration-tests
    runs-on: windows-latest
    steps:
      - name: Run Performance Tests
        run: pytest tests/infrastructure/performance/candle/ -v -m performance
```

### 3. Coverage Targets

| Test Type | Coverage Target | Critical Methods |
|-----------|----------------|------------------|
| Unit Tests | 95% | get_candles(), _validate_request(), _split_chunks() |
| Integration Tests | 85% | OverlapAnalyzer 연동, Repository 연동 |
| Performance Tests | - | 응답 시간, 메모리 사용량 |
| E2E Tests | - | UI 실행, 7규칙 전략 연동 |

### 4. Acceptance Testing

#### 최종 검증 체크리스트
- [ ] 모든 Unit Tests 통과 (95% 커버리지)
- [ ] 모든 Integration Tests 통과
- [ ] 성능 테스트 목표 달성 (100개: 50ms, 1000개: 500ms)
- [ ] `python run_desktop_ui.py` 정상 실행
- [ ] UI 차트에서 캔들 데이터 정상 표시
- [ ] 7규칙 전략에서 데이터 정상 사용
- [ ] 메모리 사용량 100MB 이하 유지
- [ ] 에러 상황에서 graceful degradation

---

## 📊 Test Data Management

### Test Database Setup
```python
@pytest.fixture(scope="session")
async def test_db_manager():
    """테스트용 DB 매니저"""
    db_manager = DatabaseManager(db_path="data/test_market_data.sqlite3")
    yield db_manager
    # 테스트 후 정리
    os.remove("data/test_market_data.sqlite3")

@pytest.fixture
async def clean_test_data():
    """각 테스트 전/후 데이터 정리"""
    # 테스트 전 정리
    await cleanup_test_tables()
    yield
    # 테스트 후 정리
    await cleanup_test_tables()
```

### Mock Data Generation
```python
def generate_mock_candle_data(symbol: str, timeframe: str, count: int) -> List[CandleData]:
    """테스트용 Mock 캔들 데이터 생성"""
    base_price = 95000000  # 9500만원
    base_time = datetime.now(timezone.utc)

    candles = []
    for i in range(count):
        candle_time = base_time - timedelta(minutes=5 * i)  # 5분봉 역순
        price_variation = random.uniform(0.95, 1.05)

        candle = CandleData(
            market=symbol,
            candle_date_time_utc=candle_time.isoformat().replace('+00:00', 'Z'),
            candle_date_time_kst=(candle_time + timedelta(hours=9)).isoformat(),
            opening_price=base_price * price_variation,
            high_price=base_price * price_variation * 1.01,
            low_price=base_price * price_variation * 0.99,
            trade_price=base_price * price_variation,
            timestamp=int(candle_time.timestamp() * 1000),
            candle_acc_trade_price=random.uniform(1000000000, 5000000000),
            candle_acc_trade_volume=random.uniform(10.0, 100.0),
            symbol=symbol,
            timeframe=timeframe
        )
        candles.append(candle)

    return candles
```

이제 완전한 테스트 전략이 수립되었습니다. 이 계획에 따라 CandleDataProvider v5.0을 개발하고 검증하면 안정적인 메인 프로그램 통합이 가능할 것입니다.
