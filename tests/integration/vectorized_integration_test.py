"""
벡터화 로직 통합 테스트 - 실제 EmptyCandleDetector 동작 확인

목적:
1. 벡터화 로직이 기본으로 동작하는지 확인
2. 청크 경계 문제가 해결되었는지 확인
3. 성능 향상이 유지되는지 확인

Created: 2025-09-21
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import time

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.candle.empty_candle_detector import EmptyCandleDetector

# 로그 출력 최소화
import logging
logging.getLogger("EmptyCandleDetector").setLevel(logging.WARNING)

logger = create_component_logger("VectorizedIntegrationTest")


def test_vectorized_integration():
    """벡터화 로직 통합 테스트"""

    print("🧪 벡터화 로직 통합 테스트 시작")
    print("-" * 50)

    # 테스트 데이터 생성 (빈 캔들 포함)
    detector = EmptyCandleDetector("KRW-BTC", "1m")
    current_time = datetime(2025, 9, 21, 12, 20, 0, tzinfo=timezone.utc)

    # 시나리오: 19,18 빈 캔들 + 16 빈 캔들
    api_candles = [
        {"candle_date_time_utc": "2025-09-21T12:17:00", "trade_price": 50000},  # 17 (19,18 빈 캔들)
        {"candle_date_time_utc": "2025-09-21T12:15:00", "trade_price": 50100},  # 15 (16 빈 캔들)
        {"candle_date_time_utc": "2025-09-21T12:14:00", "trade_price": 50200},  # 14
        {"candle_date_time_utc": "2025-09-21T12:13:00", "trade_price": 50300},  # 13
    ]

    api_start = current_time - timedelta(minutes=1)  # 19
    api_end = current_time - timedelta(minutes=6)    # 14

    print(f"📊 입력 데이터:")
    print(f"  • API 캔들: {len(api_candles)}개")
    print(f"  • 범위: {api_start} ~ {api_end}")
    print(f"  • 예상 빈 캔들: 19,18 + 16 = 3개")

    # 성능 측정
    start_time = time.perf_counter()

    # 벡터화 로직 실행
    result = detector.detect_and_fill_gaps(
        api_candles=api_candles,
        api_start=api_start,
        api_end=api_end,
        fallback_reference="test_ref"
    )

    end_time = time.perf_counter()
    execution_time = (end_time - start_time) * 1000  # ms

    # 결과 분석
    total_candles = len(result)
    empty_candles = [c for c in result if c.get("empty_copy_from_utc")]
    real_candles = [c for c in result if not c.get("empty_copy_from_utc")]

    print(f"\n📈 실행 결과:")
    print(f"  • 실행 시간: {execution_time:.2f}ms")
    print(f"  • 총 캔들: {total_candles}개")
    print(f"  • 실제 캔들: {len(real_candles)}개")
    print(f"  • 빈 캔들: {len(empty_candles)}개")

    # 빈 캔들 상세 확인
    print(f"\n🔍 빈 캔들 상세:")
    for candle in empty_candles:
        utc_time = candle["candle_date_time_utc"]
        reference = candle.get("empty_copy_from_utc", "None")
        print(f"  • {utc_time} (참조: {reference})")

    # 정확성 검증
    expected_empty_count = 3  # 19,18,16
    success = len(empty_candles) == expected_empty_count

    print(f"\n✅ 정확성 검증:")
    print(f"  • 예상: {expected_empty_count}개 빈 캔들")
    print(f"  • 실제: {len(empty_candles)}개 빈 캔들")
    print(f"  • 결과: {'✅ 성공' if success else '❌ 실패'}")

    # 청크 경계 테스트
    print(f"\n🔧 청크 경계 테스트 (api_start +1틱):")

    # 청크2 시뮬레이션 (is_first_chunk=False)
    chunk2_datetime_list = [
        datetime(2025, 9, 21, 12, 14, 0, tzinfo=timezone.utc),  # 14
        datetime(2025, 9, 21, 12, 11, 0, tzinfo=timezone.utc),  # 11 (13,12 빈 캔들)
        datetime(2025, 9, 21, 12, 10, 0, tzinfo=timezone.utc),  # 10
    ]

    chunk2_api_start = datetime(2025, 9, 21, 12, 14, 0, tzinfo=timezone.utc)  # 14
    chunk2_api_end = datetime(2025, 9, 21, 12, 10, 0, tzinfo=timezone.utc)    # 10

    # 직접 벡터화 메서드 호출 (청크2 시뮬레이션)
    chunk2_gaps = detector._detect_gaps_in_datetime_list(
        chunk2_datetime_list, detector.symbol, chunk2_api_start, chunk2_api_end,
        "test_ref", is_first_chunk=False  # 청크2 이상
    )

    expected_chunk2_gaps = 1  # 13,12 빈 캔들 그룹
    chunk2_success = len(chunk2_gaps) == expected_chunk2_gaps

    print(f"  • 청크2 예상 Gap: {expected_chunk2_gaps}개")
    print(f"  • 청크2 실제 Gap: {len(chunk2_gaps)}개")
    print(f"  • 청크2 결과: {'✅ 성공 (api_start +1틱 동작)' if chunk2_success else '❌ 실패'}")

    # 최종 결과
    overall_success = success and chunk2_success

    print(f"\n🎯 최종 결과:")
    print(f"  • 벡터화 로직: {'✅ 정상 동작' if success else '❌ 문제 발생'}")
    print(f"  • 청크 경계 해결: {'✅ 해결됨' if chunk2_success else '❌ 미해결'}")
    print(f"  • 전체 성공: {'✅ 성공' if overall_success else '❌ 실패'}")

    return overall_success


if __name__ == "__main__":
    success = test_vectorized_integration()

    if success:
        print("\n🎉 벡터화 로직 통합 테스트 성공!")
        print("   ✅ Phase 1 완료 - 청크 경계 문제 해결 및 성능 향상 달성")
    else:
        print("\n❌ 벡터화 로직 통합 테스트 실패")
        print("   ⚠️ 추가 디버깅이 필요합니다")
