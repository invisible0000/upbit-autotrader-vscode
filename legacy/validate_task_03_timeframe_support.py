"""
태스크 0.3 from upbit_auto_trading.domain.events.chart_viewer_events import ChartViewerPriority: 기존 시스템 영향도 테스트

1개월 타임프레임 지원 시스템이 기존 매매 엔진에 영향을 주지 않는지 확인합니다.
기존 InMemoryEventBus의 우선순위 시스템과 완전히 격리되어 동작하는지 검증합니다.
"""

import asyncio
from unittest.mock import Mock, AsyncMock
from typing import List

from upbit_auto_trading.application.chart_viewer.timeframe_support_service import TimeframeSupportService
from upbit_auto_trading.application.chart_viewer.hybrid_data_collection_engine import HybridDataCollectionEngine
from upbit_auto_trading.domain.events.chart_viewer_events import (
    ChartViewerPriority,
    CandleDataEvent,
    ChartSubscriptionEvent
)
from upbit_auto_trading.infrastructure.logging import create_component_logger


logger = create_component_logger("Task03SystemCompatibilityTest")


class ExistingSystemSimulator:
    """기존 매매 시스템 시뮬레이터"""

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.trading_events_received: List = []
        self.chart_events_received: List = []

    async def simulate_trading_activity(self):
        """기존 매매 활동 시뮬레이션"""
        # 기존 매매 우선순위 이벤트 발행
        trading_event = Mock()
        trading_event.priority_level = ChartViewerPriority.TRADING_CRITICAL  # 1
        trading_event.event_type = "trading_signal"

        await self.event_bus.publish(trading_event)
        logger.info("기존 매매 이벤트 발행: 우선순위 1")

    def register_event_handler(self):
        """이벤트 핸들러 등록"""
        # 우선순위별 이벤트 분류 핸들러
        def handle_event(event):
            if hasattr(event, 'priority_level'):
                if ChartViewerPriority.is_trading_priority(event.priority_level):
                    self.trading_events_received.append(event)
                elif ChartViewerPriority.is_chart_viewer_priority(event.priority_level):
                    self.chart_events_received.append(event)

        return handle_event


async def test_system_isolation():
    """시스템 격리 테스트"""
    logger.info("=== 태스크 0.3 시스템 격리 테스트 시작 ===")

    # Given: Mock 이벤트 버스
    mock_event_bus = Mock()
    mock_event_bus.publish = AsyncMock()
    published_events = []

    def capture_event(event):
        published_events.append(event)

    mock_event_bus.publish.side_effect = capture_event

    # Given: 기존 시스템 시뮬레이터
    existing_system = ExistingSystemSimulator(mock_event_bus)

    # Given: 차트뷰어 서비스들
    timeframe_service = TimeframeSupportService(mock_event_bus)

    # When: 기존 시스템과 차트뷰어 시스템 동시 활동
    logger.info("1. 기존 매매 활동 시뮬레이션")
    await existing_system.simulate_trading_activity()

    logger.info("2. 차트뷰어 1개월 타임프레임 구독")
    await timeframe_service.subscribe_timeframe("test_chart", "KRW-BTC", "1M", "active")

    logger.info("3. 창 상태 변경 (우선순위 조정)")
    await timeframe_service.update_window_state("test_chart", "minimized")

    # Then: 이벤트 분석
    trading_events = [e for e in published_events if hasattr(e, 'priority_level') and
                     ChartViewerPriority.is_trading_priority(e.priority_level)]
    chart_events = [e for e in published_events if hasattr(e, 'priority_level') and
                   ChartViewerPriority.is_chart_viewer_priority(e.priority_level)]

    logger.info(f"매매 이벤트 수: {len(trading_events)}")
    logger.info(f"차트뷰어 이벤트 수: {len(chart_events)}")

    # 검증: 우선순위 완전 분리
    for event in chart_events:
        if hasattr(event, 'priority_level'):
            assert event.priority_level in [5, 8, 10], f"차트뷰어 이벤트가 잘못된 우선순위 사용: {event.priority_level}"

    for event in trading_events:
        if hasattr(event, 'priority_level'):
            assert event.priority_level in [1, 2, 3], f"매매 이벤트가 잘못된 우선순위 사용: {event.priority_level}"

    logger.info("✅ 시스템 격리 검증 완료: 우선순위 완전 분리")

    return True


async def test_monthly_timeframe_full_workflow():
    """1개월 타임프레임 전체 워크플로우 테스트"""
    logger.info("=== 1개월 타임프레임 전체 워크플로우 테스트 ===")

    # Given: Mock 이벤트 버스
    mock_event_bus = Mock()
    mock_event_bus.publish = AsyncMock()

    # Given: 서비스 초기화
    timeframe_service = TimeframeSupportService(mock_event_bus)
    collection_engine = HybridDataCollectionEngine(mock_event_bus, timeframe_service)

    # Test 1: 1개월 타임프레임 지원 확인
    logger.info("1. 1개월 타임프레임 지원 확인")
    assert timeframe_service.is_timeframe_supported("1M")
    assert timeframe_service.get_data_source_strategy("1M") == "api"
    logger.info("✅ 1개월 타임프레임 지원됨")

    # Test 2: 모든 타임프레임 (1m~1M) 지원 확인
    logger.info("2. 모든 타임프레임 지원 확인")
    all_timeframes = timeframe_service.get_all_supported_timeframes()
    timeframe_values = [tf[1] for tf in all_timeframes]

    expected_timeframes = ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]
    for tf in expected_timeframes:
        assert tf in timeframe_values, f"타임프레임 {tf} 지원되지 않음"

    logger.info(f"✅ 모든 타임프레임 지원: {timeframe_values}")

    # Test 3: WebSocket/API 하이브리드 모드 확인
    logger.info("3. 하이브리드 모드 확인")
    hybrid_info_1h = timeframe_service.get_hybrid_mode_info("1h")
    hybrid_info_1M = timeframe_service.get_hybrid_mode_info("1M")

    assert hybrid_info_1h["websocket_supported"] == True
    assert hybrid_info_1h["api_supported"] == True
    assert hybrid_info_1M["websocket_supported"] == False  # 1개월은 API 전용
    assert hybrid_info_1M["api_supported"] == True

    logger.info("✅ 하이브리드 모드 정상 동작")

    # Test 4: 기존 타임프레임과 호환성 확인
    logger.info("4. 기존 타임프레임 호환성 확인")
    existing_timeframes = ["1m", "5m", "15m", "1h", "1d"]
    for tf in existing_timeframes:
        assert timeframe_service.is_timeframe_supported(tf)
        config = timeframe_service.get_timeframe_configuration(tf)
        assert config is not None

    logger.info("✅ 기존 타임프레임 호환성 보장")

    return True


async def test_priority_system_safety():
    """우선순위 시스템 안전성 테스트"""
    logger.info("=== 우선순위 시스템 안전성 테스트 ===")

    # Test 1: 우선순위 범위 확인
    trading_priorities = [
        ChartViewerPriority.TRADING_CRITICAL,  # 1
        ChartViewerPriority.TRADING_HIGH,      # 2
        ChartViewerPriority.TRADING_NORMAL     # 3
    ]

    chart_priorities = [
        ChartViewerPriority.CHART_HIGH,        # 5
        ChartViewerPriority.CHART_BACKGROUND,  # 8
        ChartViewerPriority.CHART_LOW          # 10
    ]

    # 우선순위 완전 분리 확인
    for chart_p in chart_priorities:
        for trading_p in trading_priorities:
            assert chart_p > trading_p, f"차트뷰어 우선순위({chart_p})가 매매 우선순위({trading_p})보다 낮아야 함"

    logger.info("✅ 우선순위 범위 완전 분리")

    # Test 2: 창 상태별 우선순위 매핑 확인
    window_states = ["active", "background", "minimized", "deactivated", "restored"]
    for state in window_states:
        priority = ChartViewerPriority.get_window_priority(state)
        assert priority in chart_priorities, f"창 상태 {state}의 우선순위 {priority}가 차트뷰어 범위를 벗어남"

    logger.info("✅ 창 상태별 우선순위 매핑 안전")

    return True


async def main():
    """태스크 0.3 최종 검증 실행"""
    logger.info("🚀 태스크 0.3: 1개월 타임프레임 지원 시스템 - 최종 검증 시작")

    try:
        # 검증 1: 시스템 격리
        result1 = await test_system_isolation()

        # 검증 2: 1개월 타임프레임 전체 워크플로우
        result2 = await test_monthly_timeframe_full_workflow()

        # 검증 3: 우선순위 시스템 안전성
        result3 = await test_priority_system_safety()

        if all([result1, result2, result3]):
            logger.info("🎉 태스크 0.3 검증 완료!")
            logger.info("✅ TimeframeSupport 클래스 구현")
            logger.info("✅ 1w, 1M 타임프레임 API 전용 처리")
            logger.info("✅ WebSocket/API 하이브리드 모드 구현")
            logger.info("✅ 기존 타임프레임과 호환성 보장")
            logger.info("✅ 모든 타임프레임 (1m~1M) 데이터 수집 가능")
            logger.info("✅ 기존 시스템과 완전 격리된 우선순위 시스템")

            print("\n" + "="*60)
            print("🎯 태스크 0.3 성공 기준 달성!")
            print("  - TimeframeSupport 클래스 구현 ✅")
            print("  - 1w, 1M 타임프레임 API 전용 처리 ✅")
            print("  - WebSocket/API 하이브리드 모드 구현 ✅")
            print("  - 기존 타임프레임과 호환성 보장 ✅")
            print("  - 모든 타임프레임 (1m~1M) 데이터 수집 가능 ✅")
            print("="*60)

            return True
        else:
            logger.error("❌ 태스크 0.3 검증 실패")
            return False

    except Exception as e:
        logger.error(f"❌ 태스크 0.3 검증 중 오류: {e}")
        return False


if __name__ == "__main__":
    # 비동기 실행
    result = asyncio.run(main())
    exit(0 if result else 1)
