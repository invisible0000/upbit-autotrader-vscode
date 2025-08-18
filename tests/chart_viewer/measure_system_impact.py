#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Phase 0.4: 실제 시스템 영향 측정 스크립트

기존 매매 시스템과 차트뷰어 확장의 리소스 사용량을 측정합니다.
"""

import time
import psutil
from concurrent.futures import ThreadPoolExecutor
from upbit_auto_trading.infrastructure.events.bus.in_memory_event_bus import InMemoryEventBus
from upbit_auto_trading.domain.events.chart_viewer_events import CandleDataEvent, OrderbookDataEvent
from upbit_auto_trading.application.chart_viewer.chart_viewer_event_handler import ChartViewerEventHandler
from upbit_auto_trading.application.chart_viewer.chart_viewer_resource_manager import ChartViewerResourceManager
from upbit_auto_trading.infrastructure.logging import create_component_logger


def measure_system_impact():
    """시스템 영향 측정"""
    logger = create_component_logger("SystemImpactMeasurement")

    # 초기 상태 측정
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    initial_cpu = psutil.cpu_percent(interval=1)

    logger.info(f"=== 초기 상태 ===")
    logger.info(f"메모리: {initial_memory:.2f}MB")
    logger.info(f"CPU: {initial_cpu:.2f}%")

    # 차트뷰어 시스템 초기화
    logger.info(f"=== 차트뷰어 시스템 초기화 ===")
    event_bus = InMemoryEventBus()
    chart_handler = ChartViewerEventHandler(event_bus)
    resource_manager = ChartViewerResourceManager()

    # 차트 등록 (여러 차트 윈도우 시뮬레이션)
    chart_ids = []
    for i in range(5):  # 5개 차트 윈도우
        chart_id = f"chart_window_{i}"
        resource_manager.register_chart(chart_id, "active")
        chart_ids.append(chart_id)

    after_init_memory = process.memory_info().rss / 1024 / 1024  # MB
    after_init_cpu = psutil.cpu_percent(interval=1)

    logger.info(f"메모리: {after_init_memory:.2f}MB (증가: {after_init_memory - initial_memory:.2f}MB)")
    logger.info(f"CPU: {after_init_cpu:.2f}%")

    # 이벤트 처리 부하 테스트
    logger.info(f"=== 이벤트 처리 부하 테스트 (30초) ===")

    def generate_chart_events():
        """차트 이벤트 생성 (백그라운드)"""
        for i in range(1000):  # 1000개 이벤트
            # 캔들 데이터 이벤트
            candle_event = CandleDataEvent(
                symbol="KRW-BTC",
                timeframe="1m",
                data_type="candle",
                candle_data={
                    "open": 45000000 + i * 100,
                    "high": 45100000 + i * 100,
                    "low": 44900000 + i * 100,
                    "close": 45050000 + i * 100,
                    "volume": 1000000,
                    "timestamp": time.time()
                }
            )

            # 호가 데이터 이벤트
            orderbook_event = OrderbookDataEvent(
                symbol="KRW-BTC",
                data_type="orderbook",
                orderbook_data={
                    "asks": [{"price": 45100000 + i * 100, "size": 1.0}],
                    "bids": [{"price": 45000000 + i * 100, "size": 1.0}],
                    "timestamp": time.time()
                }
            )

            # 이벤트 발행 (블로킹 방식으로 실제 처리)
            try:
                event_bus.publish_sync(candle_event)
                event_bus.publish_sync(orderbook_event)
            except Exception as e:
                logger.warning(f"이벤트 발행 실패: {e}")

            time.sleep(0.03)  # 30ms 간격 (실제 실시간 환경 시뮬레이션)

    # 백그라운드에서 이벤트 생성
    with ThreadPoolExecutor(max_workers=2) as executor:
        future = executor.submit(generate_chart_events)

        # 30초 동안 리소스 모니터링
        max_memory = initial_memory
        max_cpu = initial_cpu
        memory_samples = []
        cpu_samples = []

        start_time = time.time()
        while time.time() - start_time < 30:
            current_memory = process.memory_info().rss / 1024 / 1024
            current_cpu = psutil.cpu_percent(interval=0.1)

            max_memory = max(max_memory, current_memory)
            max_cpu = max(max_cpu, current_cpu)

            memory_samples.append(current_memory)
            cpu_samples.append(current_cpu)

            time.sleep(1)  # 1초마다 측정

        # 이벤트 생성 완료 대기
        future.result(timeout=60)

    # 최종 측정
    final_memory = process.memory_info().rss / 1024 / 1024
    final_cpu = psutil.cpu_percent(interval=1)

    avg_memory = sum(memory_samples) / len(memory_samples) if memory_samples else final_memory
    avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else final_cpu

    logger.info(f"=== 부하 테스트 결과 ===")
    logger.info(f"최대 메모리: {max_memory:.2f}MB (증가: {max_memory - initial_memory:.2f}MB)")
    logger.info(f"평균 메모리: {avg_memory:.2f}MB")
    logger.info(f"최종 메모리: {final_memory:.2f}MB")
    logger.info(f"최대 CPU: {max_cpu:.2f}%")
    logger.info(f"평균 CPU: {avg_cpu:.2f}%")
    logger.info(f"최종 CPU: {final_cpu:.2f}%")

    # 리소스 정리
    logger.info(f"=== 리소스 정리 ===")
    for chart_id in chart_ids:
        resource_manager.unregister_chart(chart_id)

    # 정리 후 메모리 측정
    time.sleep(2)  # 정리 대기
    cleanup_memory = process.memory_info().rss / 1024 / 1024

    logger.info(f"정리 후 메모리: {cleanup_memory:.2f}MB")
    logger.info(f"메모리 누수: {cleanup_memory - initial_memory:.2f}MB")

    # 결과 요약
    logger.info(f"=== 결과 요약 ===")
    memory_impact = max_memory - initial_memory
    cpu_impact = max_cpu - initial_cpu
    memory_leak = cleanup_memory - initial_memory

    logger.info(f"✅ 메모리 영향: {memory_impact:.2f}MB {'(허용 범위)' if memory_impact < 100 else '(과도함)'}")
    logger.info(f"✅ CPU 영향: {cpu_impact:.2f}% {'(허용 범위)' if abs(cpu_impact) < 20 else '(과도함)'}")
    logger.info(f"✅ 메모리 누수: {memory_leak:.2f}MB {'(양호)' if memory_leak < 10 else '(주의 필요)'}")

    # 성공 기준 검증
    success = True
    if memory_impact >= 100:
        logger.error("❌ 메모리 영향이 100MB를 초과했습니다")
        success = False
    if abs(cpu_impact) >= 20:
        logger.error("❌ CPU 영향이 20%를 초과했습니다")
        success = False
    if memory_leak >= 10:
        logger.error("❌ 메모리 누수가 10MB를 초과했습니다")
        success = False

    if success:
        logger.info("🎉 모든 성능 기준을 통과했습니다!")
    else:
        logger.error("⚠️ 일부 성능 기준을 초과했습니다")

    return success


if __name__ == "__main__":
    success = measure_system_impact()
    exit(0 if success else 1)
