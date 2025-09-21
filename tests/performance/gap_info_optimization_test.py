"""
GapInfo 최적화 테스트
사용자 제안: gap_start/gap_end에 실제 빈 캔들 범위 저장하여 TimeUtils 호출 최소화
"""

import time
from datetime import datetime, timedelta
from upbit_auto_trading.infrastructure.market_data.candle.empty_candle_detector import GapInfo
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils

def test_gap_info_optimization():
    """GapInfo 최적화 효과 측정"""

    print("🚀 GapInfo 최적화 테스트")
    print("="*50)

    # 테스트 데이터 설정
    timeframe = "1m"
    market = "KRW-BTC"

    # 원본 레코드 시간 (Gap 직전/직후)
    record_before = datetime(2024, 1, 1, 16, 20, 0)  # Gap 직전
    record_after = datetime(2024, 1, 1, 16, 15, 0)   # Gap 직후 (5분 Gap)

    print(f"📊 테스트 시나리오:")
    print(f"   Gap 직전 레코드: {record_before}")
    print(f"   Gap 직후 레코드: {record_after}")
    print(f"   Gap 크기: 5분 (5개 빈 캔들)")
    print()

    # 🔧 새로운 방식: GapInfo에 실제 빈 캔들 범위 저장
    gap_start_time = TimeUtils.get_time_by_ticks(record_before, timeframe, -1)  # 첫 빈 캔들
    gap_end_time = TimeUtils.get_time_by_ticks(record_after, timeframe, 1)     # 마지막 빈 캔들

    optimized_gap_info = GapInfo(
        gap_start=gap_start_time,
        gap_end=gap_end_time,
        market=market,
        reference_state=record_after.strftime('%Y-%m-%dT%H:%M:%S'),
        timeframe=timeframe
    )

    print(f"✅ 새로운 방식 (최적화된 GapInfo):")
    print(f"   gap_start: {optimized_gap_info.gap_start} (실제 첫 빈 캔들)")
    print(f"   gap_end: {optimized_gap_info.gap_end} (실제 마지막 빈 캔들)")
    print()

    # 빈 캔들 시간점 생성 시뮬레이션
    def generate_time_points_optimized(gap_info):
        """최적화된 방식: gap_start/gap_end 바로 사용"""
        time_points = []
        current_time = gap_info.gap_start  # TimeUtils 호출 없이 바로 사용!

        while current_time >= gap_info.gap_end:
            time_points.append(current_time)
            current_time = TimeUtils.get_time_by_ticks(current_time, timeframe, -1)

        return time_points

    def generate_time_points_old_way(record_before, record_after, timeframe):
        """기존 방식: 매번 TimeUtils 호출"""
        time_points = []
        # 매번 계산 필요
        start_time = TimeUtils.get_time_by_ticks(record_before, timeframe, -1)
        end_time = TimeUtils.get_time_by_ticks(record_after, timeframe, 1)

        current_time = start_time
        while current_time >= end_time:
            time_points.append(current_time)
            current_time = TimeUtils.get_time_by_ticks(current_time, timeframe, -1)

        return time_points

    # 성능 테스트
    iterations = 1000

    # 새로운 방식 (최적화)
    start_time = time.time()
    for _ in range(iterations):
        optimized_points = generate_time_points_optimized(optimized_gap_info)
    optimized_time = time.time() - start_time

    # 기존 방식
    start_time = time.time()
    for _ in range(iterations):
        old_points = generate_time_points_old_way(record_before, record_after, timeframe)
    old_time = time.time() - start_time

    # 결과 비교
    print(f"⚡ 성능 비교 ({iterations}회 반복):")
    print(f"   기존 방식: {old_time:.4f}초")
    print(f"   최적화 방식: {optimized_time:.4f}초")

    if optimized_time > 0:
        speedup = old_time / optimized_time
        improvement = ((old_time - optimized_time) / old_time) * 100
        print(f"   💨 속도 향상: {speedup:.1f}배")
        print(f"   📈 성능 개선: {improvement:.1f}%")

    print()

    # 결과 검증
    print(f"🔍 결과 검증:")
    print(f"   기존 방식 빈 캔들 개수: {len(old_points)}")
    print(f"   최적화 방식 빈 캔들 개수: {len(optimized_points)}")
    print(f"   결과 동일: {old_points == optimized_points}")

    if old_points == optimized_points:
        print("   ✅ 최적화 성공: 결과 동일, 성능 향상!")
    else:
        print("   ❌ 결과 불일치 발견")

    print()

    # 의미론적 개선 효과
    print(f"🎯 의미론적 개선 효과:")
    print(f"   📋 로그 가독성: gap_start/gap_end가 실제 빈 캔들 시간")
    print(f"   🔧 코드 단순화: TimeUtils 중복 호출 제거")
    print(f"   📖 직관성: 'Gap 범위' → '실제 빈 캔들 범위'")
    print(f"   🐛 디버깅: 로그만 봐도 어떤 빈 캔들이 생성될지 명확")

if __name__ == "__main__":
    test_gap_info_optimization()
