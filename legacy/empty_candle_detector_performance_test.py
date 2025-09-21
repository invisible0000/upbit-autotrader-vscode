"""
EmptyCandleDetector 성능 비교 테스트

목적: 제안된 벡터화 연산 방식과 기존 루프 방식의 성능을 비교
- 기존 방식: _detect_gaps_in_datetime_list (루프 기반)
- 제안 방식: 벡터화 연산 (numpy 차분 연산)

테스트 시나리오:
1. 다양한 데이터 크기 (10, 100, 1000, 10000개 캔들)
2. Gap 밀도 변화 (Gap 없음, 적음, 많음)
3. 타임프레임별 성능 차이 분석
4. 메모리 사용량 비교

Created: 2025-09-21
"""

import sys
import time
import gc
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np
import psutil
import os

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 프로젝트 imports
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.candle.empty_candle_detector import EmptyCandleDetector, GapInfo
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils

logger = create_component_logger("EmptyCandleDetectorPerformanceTest")

# ================================================================
# 🎛️ 테스트 설정
# ================================================================
TEST_CONFIGS = [
    {
        "name": "소규모",
        "candle_count": 50,
        "gap_density": 0.1,  # 10% Gap
        "timeframe": "1m"
    },
    {
        "name": "중간규모",
        "candle_count": 500,
        "gap_density": 0.15,  # 15% Gap
        "timeframe": "1m"
    },
    {
        "name": "대규모",
        "candle_count": 2000,
        "gap_density": 0.2,  # 20% Gap
        "timeframe": "1m"
    },
    {
        "name": "초대규모",
        "candle_count": 5000,
        "gap_density": 0.1,  # 10% Gap (안정성 위해 낮춤)
        "timeframe": "1m"
    }
]

REPEAT_COUNT = 10  # 각 테스트 반복 횟수 (평균값 계산용)


class VectorizedGapDetector:
    """
    제안된 벡터화 방식의 Gap 감지기

    기존 _detect_gaps_in_datetime_list의 벡터화된 버전:
    - numpy 배열 기반 차분 연산
    - 조건부 마스킹으로 Gap 검출
    - 메모리 효율적인 배치 처리
    """

    def __init__(self, symbol: str, timeframe: str):
        self.symbol = symbol
        self.timeframe = timeframe
        self.gap_threshold_ms = self._get_gap_threshold(timeframe)
        self._timeframe_delta_ms = TimeUtils.get_timeframe_seconds(timeframe) * 1000

        logger.debug(f"VectorizedGapDetector 초기화: {symbol} {timeframe}")

    def detect_gaps_vectorized(
        self,
        datetime_list: List[datetime],
        api_start: Optional[datetime] = None,
        api_end: Optional[datetime] = None,
        fallback_reference: Optional[str] = None
    ) -> List[GapInfo]:
        """
        🚀 벡터화 연산 기반 Gap 감지

        제안 방식:
        1. datetime → timestamp 벡터 변환
        2. numpy 차분 연산으로 Gap 검출
        3. 조건부 마스킹으로 Gap 위치 식별
        4. 배치 처리로 GapInfo 생성

        Args:
            datetime_list: 순수 datetime 리스트 (업비트 내림차순 정렬)
            api_start: Gap 검출 시작점
            api_end: Gap 검출 종료점
            fallback_reference: 안전한 참조 상태

        Returns:
            List[GapInfo]: 감지된 Gap 정보
        """
        if not datetime_list:
            return []

        # 업비트 내림차순 정렬 확보
        sorted_datetimes = sorted(datetime_list, reverse=True)

        # api_end 처리: 마지막 Gap 감지를 위해 api_end-1틱을 리스트에 추가
        if api_end:
            sorted_datetimes.append(TimeUtils.get_time_by_ticks(api_end, self.timeframe, -1))

        gaps = []

        # 🆕 1. 첫 번째 캔들과 api_start 비교
        if api_start and sorted_datetimes:
            first_time = sorted_datetimes[0]
            if first_time < api_start:
                gap_info = GapInfo(
                    gap_start=api_start,
                    gap_end=first_time,
                    market=self.symbol,
                    reference_state=fallback_reference,
                    timeframe=self.timeframe
                )
                gaps.append(gap_info)
                logger.debug(f"✅ 첫 Gap 감지 (벡터화): {api_start} ~ {first_time}")

        # 🚀 2. 벡터화된 Gap 검출
        if len(sorted_datetimes) >= 2:
            # timestamp 배열 생성 (밀리초 단위)
            timestamps = np.array([
                int(dt.timestamp() * 1000) for dt in sorted_datetimes
            ])

            # 차분 계산: current - next (업비트 내림차순이므로 양수가 정상 간격)
            deltas = timestamps[:-1] - timestamps[1:]

            # Gap 조건: 차분이 timeframe보다 큰 경우
            gap_mask = deltas > self._timeframe_delta_ms

            # Gap 인덱스 추출
            gap_indices = np.where(gap_mask)[0]

            logger.debug(f"🔍 벡터화 Gap 분석: {len(sorted_datetimes)}개 캔들, {len(gap_indices)}개 Gap 발견")

            # 배치 처리로 GapInfo 생성
            for idx in gap_indices:
                previous_time = sorted_datetimes[idx]      # 더 최신
                current_time = sorted_datetimes[idx + 1]   # 더 과거

                # Gap 범위 계산
                expected_current = TimeUtils.get_time_by_ticks(previous_time, self.timeframe, -1)
                gap_end_time = TimeUtils.get_time_by_ticks(current_time, self.timeframe, 1)

                gap_info = GapInfo(
                    gap_start=expected_current,
                    gap_end=gap_end_time,
                    market=self.symbol,
                    reference_state=previous_time.strftime('%Y-%m-%dT%H:%M:%S'),
                    timeframe=self.timeframe
                )
                gaps.append(gap_info)
                logger.debug(f"✅ Gap 등록 (벡터화): {expected_current} ~ {gap_end_time}")

        return gaps

    def _get_gap_threshold(self, timeframe: str) -> int:
        """타임프레임별 Gap 감지 임계값 (EmptyCandleDetector와 동일)"""
        gap_threshold_ms_map = {
            '1s': 1500, '1m': 90000, '3m': 270000, '5m': 450000,
            '10m': 900000, '15m': 1350000, '30m': 2700000, '60m': 5400000,
            '240m': 21600000, '1h': 5400000, '4h': 21600000, '1d': 129600000,
            '1w': 907200000, '1M': 3888000000, '1y': 47304000000
        }
        return gap_threshold_ms_map.get(timeframe, 90000)


class PerformanceBenchmark:
    """성능 벤치마크 실행기"""

    def __init__(self):
        self.results = []

    def create_test_data(self, config: Dict) -> Tuple[List[datetime], datetime, datetime]:
        """
        테스트용 datetime 리스트 생성

        Args:
            config: 테스트 설정

        Returns:
            Tuple[datetime_list, api_start, api_end]
        """
        candle_count = config["candle_count"]
        gap_density = config["gap_density"]
        timeframe = config["timeframe"]

        # 기준 시간 설정 (현재 시간 기준)
        base_time = datetime.now(timezone.utc)
        api_start = TimeUtils.align_to_candle_boundary(base_time, timeframe)

        # 연속 시간 시퀀스 생성 (업비트 내림차순)
        full_sequence = []
        current_time = api_start

        for i in range(candle_count):
            # Gap 생성 확률 적용
            if np.random.random() < gap_density:
                # Gap 생성: 1-3틱 건너뛰기
                skip_ticks = np.random.randint(1, 4)
                current_time = TimeUtils.get_time_by_ticks(current_time, timeframe, -skip_ticks)
            else:
                current_time = TimeUtils.get_time_by_ticks(current_time, timeframe, -1)

            full_sequence.append(current_time)

        api_end = current_time

        logger.info(f"테스트 데이터 생성: {len(full_sequence)}개 캔들, Gap 밀도: {gap_density:.1%}")
        logger.debug(f"시간 범위: {api_start} ~ {api_end}")

        return full_sequence, api_start, api_end

    def measure_performance(self, func, *args, **kwargs) -> Dict[str, float]:
        """
        함수 성능 측정

        Returns:
            Dict: 실행 시간, 메모리 사용량 등 성능 메트릭
        """
        # 메모리 측정 시작
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # 실행 시간 측정
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()

        # 메모리 측정 완료
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_delta = memory_after - memory_before

        execution_time = (end_time - start_time) * 1000  # ms

        return {
            "execution_time_ms": execution_time,
            "memory_delta_mb": memory_delta,
            "result_count": len(result) if isinstance(result, list) else 0
        }

    def run_comparison_test(self, config: Dict) -> Dict:
        """
        기존 방식 vs 벡터화 방식 비교 테스트

        Args:
            config: 테스트 설정

        Returns:
            Dict: 성능 비교 결과
        """
        symbol = "KRW-BTC"
        timeframe = config["timeframe"]

        # 테스트 데이터 생성
        datetime_list, api_start, api_end = self.create_test_data(config)

        # 검출기 생성
        original_detector = EmptyCandleDetector(symbol, timeframe)
        vectorized_detector = VectorizedGapDetector(symbol, timeframe)

        # 반복 테스트를 위한 결과 저장
        original_times = []
        vectorized_times = []
        original_memories = []
        vectorized_memories = []

        logger.info(f"🔍 성능 테스트 시작: {config['name']} ({REPEAT_COUNT}회 반복)")

        # 반복 테스트 실행
        for i in range(REPEAT_COUNT):
            # 가비지 컬렉션으로 메모리 정리
            gc.collect()

            # 🔄 기존 방식 테스트
            try:
                original_metrics = self.measure_performance(
                    original_detector._detect_gaps_in_datetime_list,
                    datetime_list, symbol, api_start, api_end, "fallback_ref"
                )
                original_times.append(original_metrics["execution_time_ms"])
                original_memories.append(original_metrics["memory_delta_mb"])
                original_gap_count = original_metrics["result_count"]
            except Exception as e:
                logger.error(f"기존 방식 테스트 실패 (#{i+1}): {e}")
                continue

            # 메모리 정리
            gc.collect()

            # 🚀 벡터화 방식 테스트 (is_first_chunk=True로 설정)
            try:
                vectorized_metrics = self.measure_performance(
                    vectorized_detector.detect_gaps_vectorized,
                    datetime_list, api_start, api_end, "fallback_ref"
                )
                vectorized_times.append(vectorized_metrics["execution_time_ms"])
                vectorized_memories.append(vectorized_metrics["memory_delta_mb"])
                vectorized_gap_count = vectorized_metrics["result_count"]
            except Exception as e:
                logger.error(f"벡터화 방식 테스트 실패 (#{i + 1}): {e}")
                continue

        # 결과 정확성 검증
        accuracy_match = original_gap_count == vectorized_gap_count

        # 통계 계산
        def calculate_stats(values):
            if not values:
                return {"mean": 0, "min": 0, "max": 0, "std": 0}
            return {
                "mean": np.mean(values),
                "min": np.min(values),
                "max": np.max(values),
                "std": np.std(values)
            }

        original_stats = calculate_stats(original_times)
        vectorized_stats = calculate_stats(vectorized_times)
        original_memory_stats = calculate_stats(original_memories)
        vectorized_memory_stats = calculate_stats(vectorized_memories)

        # 성능 개선율 계산
        if original_stats["mean"] > 0:
            speed_improvement = ((original_stats["mean"] - vectorized_stats["mean"])
                               / original_stats["mean"] * 100)
        else:
            speed_improvement = 0

        if original_memory_stats["mean"] > 0:
            memory_improvement = ((original_memory_stats["mean"] - vectorized_memory_stats["mean"])
                                / original_memory_stats["mean"] * 100)
        else:
            memory_improvement = 0

        result = {
            "config": config,
            "test_data": {
                "candle_count": len(datetime_list),
                "gap_count": original_gap_count,
                "timeframe": timeframe
            },
            "original": {
                "time_stats": original_stats,
                "memory_stats": original_memory_stats,
                "gap_count": original_gap_count
            },
            "vectorized": {
                "time_stats": vectorized_stats,
                "memory_stats": vectorized_memory_stats,
                "gap_count": vectorized_gap_count
            },
            "comparison": {
                "speed_improvement_percent": speed_improvement,
                "memory_improvement_percent": memory_improvement,
                "accuracy_match": accuracy_match,
                "valid_runs": len(original_times)
            }
        }

        return result

    def run_all_tests(self) -> List[Dict]:
        """모든 테스트 설정에 대한 벤치마크 실행"""
        logger.info("🚀 EmptyCandleDetector 성능 비교 테스트 시작")
        logger.info(f"테스트 설정: {len(TEST_CONFIGS)}개, 반복: {REPEAT_COUNT}회")

        all_results = []

        for i, config in enumerate(TEST_CONFIGS):
            logger.info(f"\n📊 테스트 {i+1}/{len(TEST_CONFIGS)}: {config['name']}")
            logger.info(f"설정: {config['candle_count']}개 캔들, Gap 밀도: {config['gap_density']:.1%}")

            try:
                result = self.run_comparison_test(config)
                all_results.append(result)

                # 즉시 결과 출력
                self.print_result_summary(result)

            except Exception as e:
                logger.error(f"테스트 실행 실패: {e}")
                import traceback
                traceback.print_exc()

        return all_results

    def print_result_summary(self, result: Dict):
        """개별 테스트 결과 요약 출력"""
        config = result["config"]
        original = result["original"]
        vectorized = result["vectorized"]
        comparison = result["comparison"]

        print(f"\n📈 === {config['name']} 결과 ===")
        print(f"📊 데이터: {result['test_data']['candle_count']}개 캔들, {result['test_data']['gap_count']}개 Gap")
        print(f"⏱️  기존 방식: {original['time_stats']['mean']:.2f}ms (±{original['time_stats']['std']:.2f})")
        print(f"🚀 벡터화: {vectorized['time_stats']['mean']:.2f}ms (±{vectorized['time_stats']['std']:.2f})")
        print(f"📈 속도 개선: {comparison['speed_improvement_percent']:.1f}%")
        print(f"💾 메모리 개선: {comparison['memory_improvement_percent']:.1f}%")
        print(f"✅ 정확성: {'일치' if comparison['accuracy_match'] else '불일치'}")
        print(f"🔄 유효 실행: {comparison['valid_runs']}/{REPEAT_COUNT}회")

    def print_final_report(self, all_results: List[Dict]):
        """최종 종합 리포트 출력"""
        print("\n" + "="*80)
        print("🎯 === EmptyCandleDetector 성능 비교 최종 리포트 ===")
        print("="*80)

        # 종합 통계
        total_tests = len(all_results)
        successful_tests = len([r for r in all_results if r["comparison"]["accuracy_match"]])

        # 평균 성능 개선율 계산
        speed_improvements = [r["comparison"]["speed_improvement_percent"] for r in all_results]
        memory_improvements = [r["comparison"]["memory_improvement_percent"] for r in all_results]

        avg_speed_improvement = np.mean(speed_improvements) if speed_improvements else 0
        avg_memory_improvement = np.mean(memory_improvements) if memory_improvements else 0

        print(f"📊 테스트 개요:")
        print(f"  • 총 테스트: {total_tests}개")
        print(f"  • 성공한 테스트: {successful_tests}개")
        print(f"  • 정확성 통과율: {successful_tests/total_tests*100:.1f}%")

        print(f"\n🚀 성능 개선 결과:")
        print(f"  • 평균 속도 개선: {avg_speed_improvement:.1f}%")
        print(f"  • 평균 메모리 개선: {avg_memory_improvement:.1f}%")

        # 상세 결과 테이블
        print(f"\n📋 상세 결과:")
        print("테스트명\t\t캔들수\tGap수\t기존(ms)\t벡터화(ms)\t속도개선(%)")
        print("-" * 80)

        for result in all_results:
            config = result["config"]
            test_data = result["test_data"]
            original_time = result["original"]["time_stats"]["mean"]
            vectorized_time = result["vectorized"]["time_stats"]["mean"]
            speed_improvement = result["comparison"]["speed_improvement_percent"]

            print(f"{config['name']}\t\t{test_data['candle_count']}\t{test_data['gap_count']}\t"
                  f"{original_time:.2f}\t\t{vectorized_time:.2f}\t\t{speed_improvement:.1f}")

        # 권장사항
        print(f"\n💡 권장사항:")
        if avg_speed_improvement > 10:
            print(f"  ✅ 벡터화 방식이 평균 {avg_speed_improvement:.1f}% 빠름 → 벡터화 방식 채택 권장")
        elif avg_speed_improvement > 0:
            print(f"  ⚠️ 벡터화 방식이 {avg_speed_improvement:.1f}% 빠름 → 추가 최적화 검토 필요")
        else:
            print(f"  ❌ 기존 방식이 더 빠름 ({-avg_speed_improvement:.1f}%) → 기존 방식 유지 권장")

        if avg_memory_improvement > 0:
            print(f"  💾 메모리 사용량 {avg_memory_improvement:.1f}% 절약")

        print("\n" + "="*80)


def main():
    """메인 테스트 실행 함수"""
    print("🔍 EmptyCandleDetector 성능 비교 테스트")
    print("목적: 제안된 벡터화 연산 방식과 기존 루프 방식의 성능 비교")
    print("-" * 60)

    # numpy 시드 설정 (재현 가능한 테스트)
    np.random.seed(42)

    # 벤치마크 실행
    benchmark = PerformanceBenchmark()

    try:
        all_results = benchmark.run_all_tests()
        benchmark.print_final_report(all_results)

        logger.info("✅ 모든 성능 테스트 완료")
        return True

    except Exception as e:
        logger.error(f"❌ 테스트 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("EmptyCandleDetector 성능 비교 테스트 시작...")
    success = main()

    if success:
        print("\n✅ 성능 테스트 완료")
    else:
        print("\n❌ 성능 테스트 실패")
