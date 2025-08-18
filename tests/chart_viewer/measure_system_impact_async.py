#!/usr/bin/env python3
"""
차트뷰어 시스템 영향 측정 (비동기 버전)
"""

import asyncio
import time
import random
import psutil
import sys
import os
from typing import List, Dict, Any

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.events.bus.in_memory_event_bus import InMemoryEventBus

# 차트뷰어 컴포넌트 import
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from chart_viewer_events import CandleDataEvent, OrderbookDataEvent
from chart_viewer_event_handler import ChartViewerEventHandler
from chart_viewer_resource_manager import ChartViewerResourceManager


class SystemImpactMeasurement:
    """시스템 영향 측정"""

    def __init__(self):
        self.logger = create_component_logger("SystemImpactMeasurement")
        self.event_bus = InMemoryEventBus()
        self.event_handler = ChartViewerEventHandler(self.event_bus)
        self.resource_manager = ChartViewerResourceManager()

    async def measure_system_impact(self) -> Dict[str, Any]:
        """시스템 영향 측정 실행"""
        process = psutil.Process()

        # 초기 상태 측정
        initial_memory = process.memory_info().rss / 1024 / 1024
        initial_cpu = psutil.cpu_percent(interval=1)

        self.logger.info("=== 초기 상태 ===")
        self.logger.info(f"메모리: {initial_memory:.2f}MB")
        self.logger.info(f"CPU: {initial_cpu:.2f}%")

        # 차트뷰어 시스템 초기화
        await self._initialize_chart_viewer_system()

        setup_memory = process.memory_info().rss / 1024 / 1024
        setup_cpu = psutil.cpu_percent(interval=1)

        self.logger.info("=== 차트뷰어 시스템 초기화 ===")
        self.logger.info(f"메모리: {setup_memory:.2f}MB (증가: {setup_memory - initial_memory:.2f}MB)")
        self.logger.info(f"CPU: {setup_cpu:.2f}%")

        # 부하 테스트
        await self._run_load_test(process, initial_memory)

        # 정리 및 최종 측정
        await self._cleanup_and_final_measurement(process, initial_memory)

        return {
            "initial_memory_mb": initial_memory,
            "setup_memory_mb": setup_memory,
            "memory_increase_mb": setup_memory - initial_memory,
            "test_completed": True
        }

    async def _initialize_chart_viewer_system(self) -> None:
        """차트뷰어 시스템 초기화"""
        # 이벤트 버스 시작
        await self.event_bus.start()

        # 이벤트 핸들러 초기화
        await self.event_handler.initialize()

        # 테스트 차트 윈도우 등록 (5개)
        for i in range(5):
            chart_id = f"chart_window_{i}"
            self.resource_manager.register_chart(
                chart_id=chart_id,
                window_state="active",
                memory_usage_mb=256
            )

    async def _run_load_test(self, process: psutil.Process, initial_memory: float) -> None:
        """부하 테스트 실행"""
        self.logger.info("=== 이벤트 처리 부하 테스트 (30초) ===")

        # 메트릭 수집을 위한 변수
        max_memory = initial_memory
        max_cpu = 0.0
        memory_samples = []
        cpu_samples = []

        # 이벤트 생성 태스크와 모니터링 태스크를 동시 실행
        event_task = asyncio.create_task(self._generate_event_load(30))
        monitor_task = asyncio.create_task(
            self._monitor_resources(process, 30, memory_samples, cpu_samples)
        )

        # 두 태스크 완료 대기
        await asyncio.gather(event_task, monitor_task)

        # 결과 분석
        if memory_samples:
            max_memory = max(memory_samples)
            avg_memory = sum(memory_samples) / len(memory_samples)
        else:
            max_memory = avg_memory = process.memory_info().rss / 1024 / 1024

        if cpu_samples:
            max_cpu = max(cpu_samples)
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
        else:
            max_cpu = avg_cpu = psutil.cpu_percent(interval=1)

        final_memory = process.memory_info().rss / 1024 / 1024
        final_cpu = psutil.cpu_percent(interval=1)

        self.logger.info("=== 부하 테스트 결과 ===")
        self.logger.info(f"최대 메모리: {max_memory:.2f}MB (증가: {max_memory - initial_memory:.2f}MB)")
        self.logger.info(f"평균 메모리: {avg_memory:.2f}MB")
        self.logger.info(f"최종 메모리: {final_memory:.2f}MB")
        self.logger.info(f"최대 CPU: {max_cpu:.2f}%")
        self.logger.info(f"평균 CPU: {avg_cpu:.2f}%")
        self.logger.info(f"최종 CPU: {final_cpu:.2f}%")

        # 성능 기준 검증
        self._validate_performance_criteria(max_memory, initial_memory, max_cpu)

    async def _generate_event_load(self, duration_seconds: int) -> None:
        """이벤트 부하 생성"""
        end_time = time.time() + duration_seconds
        event_count = 0

        while time.time() < end_time:
            # 다양한 이벤트 타입으로 테스트
            event_types = [
                (CandleDataEvent, {
                    "symbol": "KRW-BTC",
                    "timeframe": "1m",
                    "candle_data": {
                        "open": 50000000,
                        "high": 51000000,
                        "low": 49000000,
                        "close": 50500000,
                        "volume": 100
                    }
                }),
                (OrderbookDataEvent, {
                    "symbol": "KRW-BTC",
                    "orderbook_data": {
                        "bids": [{"price": 50000000, "size": 1.0}],
                        "asks": [{"price": 50100000, "size": 1.0}]
                    }
                })
            ]

            event_type, data = random.choice(event_types)
            event = event_type(**data)

            try:
                await self.event_bus.publish(event)
                event_count += 1
            except Exception as e:
                self.logger.warning(f"이벤트 발행 실패: {e}")

            await asyncio.sleep(0.01)  # 100 events/second

        self.logger.info(f"총 {event_count}개 이벤트 발행 완료")

    async def _monitor_resources(self, process: psutil.Process, duration_seconds: int,
                               memory_samples: List[float], cpu_samples: List[float]) -> None:
        """리소스 모니터링"""
        end_time = time.time() + duration_seconds

        while time.time() < end_time:
            current_memory = process.memory_info().rss / 1024 / 1024
            current_cpu = psutil.cpu_percent(interval=0.1)

            memory_samples.append(current_memory)
            cpu_samples.append(current_cpu)

            await asyncio.sleep(1)  # 1초마다 측정

    async def _cleanup_and_final_measurement(self, process: psutil.Process,
                                           initial_memory: float) -> None:
        """정리 및 최종 측정"""
        self.logger.info("=== 리소스 정리 ===")

        # 차트 윈도우 정리
        for i in range(5):
            chart_id = f"chart_window_{i}"
            self.resource_manager.unregister_chart(chart_id)

        # 이벤트 버스 정지
        await self.event_bus.stop()

        # 정리 대기
        await asyncio.sleep(2)

        cleanup_memory = process.memory_info().rss / 1024 / 1024
        cleanup_cpu = psutil.cpu_percent(interval=1)

        self.logger.info(f"정리 후 메모리: {cleanup_memory:.2f}MB")
        self.logger.info(f"메모리 누수: {cleanup_memory - initial_memory:.2f}MB")
        self.logger.info(f"정리 후 CPU: {cleanup_cpu:.2f}%")

        # 메모리 누수 검증
        memory_leak = cleanup_memory - initial_memory
        if memory_leak > 10:  # 10MB 이상 누수시 경고
            self.logger.warning(f"⚠️ 메모리 누수 감지: {memory_leak:.2f}MB")
        else:
            self.logger.info(f"✅ 메모리 누수 없음: {memory_leak:.2f}MB")

    def _validate_performance_criteria(self, max_memory: float, initial_memory: float,
                                     max_cpu: float) -> None:
        """성능 기준 검증"""
        self.logger.info("=== 성능 기준 검증 ===")

        memory_increase = max_memory - initial_memory

        # 메모리 사용량 검증 (100MB 이하)
        if memory_increase <= 100:
            self.logger.info(f"✅ 메모리 사용량 OK: {memory_increase:.2f}MB <= 100MB")
        else:
            self.logger.error(f"❌ 메모리 사용량 초과: {memory_increase:.2f}MB > 100MB")

        # CPU 사용량 검증 (20% 이하)
        if max_cpu <= 20:
            self.logger.info(f"✅ CPU 사용량 OK: {max_cpu:.2f}% <= 20%")
        else:
            self.logger.error(f"❌ CPU 사용량 초과: {max_cpu:.2f}% > 20%")


async def main():
    """메인 실행 함수"""
    measurement = SystemImpactMeasurement()

    try:
        result = await measurement.measure_system_impact()
        print("\n=== 최종 결과 ===")
        print(f"초기 메모리: {result['initial_memory_mb']:.2f}MB")
        print(f"설정 후 메모리: {result['setup_memory_mb']:.2f}MB")
        print(f"메모리 증가: {result['memory_increase_mb']:.2f}MB")
        print(f"테스트 완료: {result['test_completed']}")

    except Exception as e:
        print(f"측정 실패: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
