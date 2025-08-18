#!/usr/bin/env python3
"""
Phase 0.4: 기존 시스템 안전성 검증 - 성능 영향 측정
실제 차트뷰어 구현 없이 기존 시스템의 안전성과 성능을 검증
"""

import asyncio
import time
import psutil
from typing import Dict, Any

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.events.bus.in_memory_event_bus import InMemoryEventBus


class SystemSafetyValidator:
    """기존 시스템 안전성 검증"""

    def __init__(self):
        self.logger = create_component_logger("SystemSafetyValidator")

    async def validate_system_safety(self) -> Dict[str, Any]:
        """기존 시스템 안전성 검증"""
        process = psutil.Process()

        # 초기 상태 측정
        initial_memory = process.memory_info().rss / 1024 / 1024
        initial_cpu = psutil.cpu_percent(interval=1)

        self.logger.info("=== Phase 0.4: 기존 시스템 안전성 검증 ===")
        self.logger.info(f"초기 메모리: {initial_memory:.2f}MB")
        self.logger.info(f"초기 CPU: {initial_cpu:.2f}%")

        # 기존 InMemoryEventBus 기본 동작 검증
        await self._test_existing_event_bus(process, initial_memory)

        # 시스템 리소스 안정성 검증
        await self._test_resource_stability(process, initial_memory)

        # 최종 측정
        final_memory = process.memory_info().rss / 1024 / 1024
        final_cpu = psutil.cpu_percent(interval=1)

        memory_increase = final_memory - initial_memory

        self.logger.info("=== 검증 완료 ===")
        self.logger.info(f"최종 메모리: {final_memory:.2f}MB")
        self.logger.info(f"메모리 증가: {memory_increase:.2f}MB")
        self.logger.info(f"최종 CPU: {final_cpu:.2f}%")

        # 안전성 기준 검증
        safety_result = self._validate_safety_criteria(memory_increase, final_cpu)

        return {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": memory_increase,
            "final_cpu_percent": final_cpu,
            "safety_validated": safety_result,
            "phase_0_4_completed": True
        }

    async def _test_existing_event_bus(self, process: psutil.Process, initial_memory: float) -> None:
        """기존 이벤트 버스 기본 동작 검증"""
        self.logger.info("=== 기존 InMemoryEventBus 기본 동작 검증 ===")

        # 기존 이벤트 버스 생성 및 시작
        event_bus = InMemoryEventBus()
        await event_bus.start()

        setup_memory = process.memory_info().rss / 1024 / 1024
        setup_cpu = psutil.cpu_percent(interval=0.5)

        self.logger.info(f"이벤트 버스 설정 후 메모리: {setup_memory:.2f}MB (증가: {setup_memory - initial_memory:.2f}MB)")
        self.logger.info(f"이벤트 버스 설정 후 CPU: {setup_cpu:.2f}%")

        # 기존 통계 조회 기능 검증
        stats = event_bus.get_statistics()
        self.logger.info(f"이벤트 버스 통계: {stats}")

        # 이벤트 버스 정리
        await event_bus.stop()

        cleanup_memory = process.memory_info().rss / 1024 / 1024
        self.logger.info(f"정리 후 메모리: {cleanup_memory:.2f}MB")

        # 메모리 누수 검증
        memory_leak = cleanup_memory - initial_memory
        if memory_leak > 5:  # 5MB 이상 누수시 경고
            self.logger.warning(f"⚠️ 메모리 누수 감지: {memory_leak:.2f}MB")
        else:
            self.logger.info(f"✅ 메모리 누수 없음: {memory_leak:.2f}MB")

    async def _test_resource_stability(self, process: psutil.Process, initial_memory: float) -> None:
        """시스템 리소스 안정성 검증"""
        self.logger.info("=== 시스템 리소스 안정성 검증 (10초) ===")

        max_memory = initial_memory
        max_cpu = 0.0
        measurements = []

        start_time = time.time()
        while time.time() - start_time < 10:
            current_memory = process.memory_info().rss / 1024 / 1024
            current_cpu = psutil.cpu_percent(interval=0.1)

            max_memory = max(max_memory, current_memory)
            max_cpu = max(max_cpu, current_cpu)

            measurements.append({
                "time": time.time() - start_time,
                "memory": current_memory,
                "cpu": current_cpu
            })

            await asyncio.sleep(0.5)  # 0.5초마다 측정

        avg_memory = sum(m["memory"] for m in measurements) / len(measurements)
        avg_cpu = sum(m["cpu"] for m in measurements) / len(measurements)

        self.logger.info(f"10초간 최대 메모리: {max_memory:.2f}MB")
        self.logger.info(f"10초간 평균 메모리: {avg_memory:.2f}MB")
        self.logger.info(f"10초간 최대 CPU: {max_cpu:.2f}%")
        self.logger.info(f"10초간 평균 CPU: {avg_cpu:.2f}%")

        # 안정성 확인
        memory_stability = max_memory - min(m["memory"] for m in measurements)
        cpu_stability = max(m["cpu"] for m in measurements) - min(m["cpu"] for m in measurements)

        self.logger.info(f"메모리 변동폭: {memory_stability:.2f}MB")
        self.logger.info(f"CPU 변동폭: {cpu_stability:.2f}%")

        if memory_stability < 10:  # 10MB 미만 변동
            self.logger.info("✅ 메모리 사용량 안정함")
        else:
            self.logger.warning(f"⚠️ 메모리 사용량 불안정: {memory_stability:.2f}MB 변동")

        if cpu_stability < 20:  # 20% 미만 변동
            self.logger.info("✅ CPU 사용량 안정함")
        else:
            self.logger.warning(f"⚠️ CPU 사용량 불안정: {cpu_stability:.2f}% 변동")

    def _validate_safety_criteria(self, memory_increase: float, cpu_usage: float) -> bool:
        """안전성 기준 검증"""
        self.logger.info("=== 안전성 기준 검증 ===")

        safety_passed = True

        # 메모리 증가량 검증 (20MB 이하로 설정 - 실제 구현 없이 테스트)
        if memory_increase <= 20:
            self.logger.info(f"✅ 메모리 증가량 OK: {memory_increase:.2f}MB <= 20MB")
        else:
            self.logger.error(f"❌ 메모리 증가량 초과: {memory_increase:.2f}MB > 20MB")
            safety_passed = False

        # CPU 사용량 검증 (15% 이하로 설정 - 기본 시스템 부하)
        if cpu_usage <= 15:
            self.logger.info(f"✅ CPU 사용량 OK: {cpu_usage:.2f}% <= 15%")
        else:
            self.logger.error(f"❌ CPU 사용량 초과: {cpu_usage:.2f}% > 15%")
            safety_passed = False

        if safety_passed:
            self.logger.info("🎉 Phase 0.4 안전성 검증 통과!")
        else:
            self.logger.error("❌ Phase 0.4 안전성 검증 실패")

        return safety_passed


async def main():
    """메인 실행 함수"""
    validator = SystemSafetyValidator()

    try:
        result = await validator.validate_system_safety()

        print("\n" + "="*60)
        print("Phase 0.4: 기존 시스템 안전성 검증 결과")
        print("="*60)
        print(f"초기 메모리: {result['initial_memory_mb']:.2f}MB")
        print(f"최종 메모리: {result['final_memory_mb']:.2f}MB")
        print(f"메모리 증가: {result['memory_increase_mb']:.2f}MB")
        print(f"최종 CPU: {result['final_cpu_percent']:.2f}%")
        print(f"안전성 검증: {'통과' if result['safety_validated'] else '실패'}")
        print(f"Phase 0.4 완료: {'✅' if result['phase_0_4_completed'] else '❌'}")
        print("="*60)

        return 0 if result['safety_validated'] else 1

    except Exception as e:
        print(f"검증 실패: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
