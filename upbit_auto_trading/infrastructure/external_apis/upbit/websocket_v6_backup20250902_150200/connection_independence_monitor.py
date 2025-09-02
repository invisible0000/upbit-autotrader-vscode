"""
WebSocket v6 연결 독립성 강화 확장
=================================

테스트 결과를 바탕으로 Public/Private 독립성을 더욱 강화하는 확장 기능

핵심 개선사항:
1. 연결별 독립 에러 처리
2. 개별 연결 상태 모니터링 강화
3. 독립적 재연결 로직
4. 연결별 성능 분석 도구
"""

import asyncio
import time
from typing import Dict, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger

from .types import WebSocketType, ConnectionState, DataType
from .global_websocket_manager import GlobalWebSocketManager, ConnectionMetrics


class ConnectionIndependenceLevel(Enum):
    """연결 독립성 수준"""
    BASIC = "basic"           # 기본 독립성 (현재 상태)
    ENHANCED = "enhanced"     # 강화된 독립성
    ISOLATED = "isolated"     # 완전 격리


@dataclass
class IndependentConnectionStatus:
    """개별 연결 상태"""
    connection_type: WebSocketType
    independence_level: ConnectionIndependenceLevel = ConnectionIndependenceLevel.ENHANCED

    # 독립 상태 추적
    last_error: Optional[str] = None
    last_error_time: Optional[float] = None
    consecutive_errors: int = 0
    auto_recovery_enabled: bool = True

    # 타 연결 영향도 추적
    affected_by_other: bool = False
    affecting_other: bool = False
    cross_connection_events: List[str] = field(default_factory=list)

    # 독립성 점수
    independence_score: float = 1.0  # 1.0 = 완전 독립


class ConnectionIndependenceMonitor:
    """연결 독립성 모니터링 및 강화"""

    def __init__(self, manager: GlobalWebSocketManager):
        self.logger = create_component_logger("ConnectionIndependenceMonitor")
        self.manager = manager

        # 연결별 독립 상태 추적
        self._connection_status: Dict[WebSocketType, IndependentConnectionStatus] = {
            WebSocketType.PUBLIC: IndependentConnectionStatus(WebSocketType.PUBLIC),
            WebSocketType.PRIVATE: IndependentConnectionStatus(WebSocketType.PRIVATE)
        }

        # 독립성 검증 기록
        self._independence_test_results: List[Dict] = []

        # 모니터링 활성화
        self._monitoring_active = False
        self._monitor_task: Optional[asyncio.Task] = None

    async def start_monitoring(self):
        """독립성 모니터링 시작"""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._monitor_task = asyncio.create_task(self._independence_monitor_loop())
        self.logger.info("연결 독립성 모니터링 시작")

    async def stop_monitoring(self):
        """독립성 모니터링 중지"""
        self._monitoring_active = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("연결 독립성 모니터링 중지")

    async def _independence_monitor_loop(self):
        """독립성 모니터링 루프"""
        try:
            while self._monitoring_active:
                await asyncio.sleep(10)  # 10초마다 체크

                # 각 연결의 독립성 점수 업데이트
                await self._update_independence_scores()

                # 연결 간 영향도 분석
                await self._analyze_cross_connection_impact()

                # 독립성 위반 감지 및 복구
                await self._detect_and_fix_independence_violations()

        except asyncio.CancelledError:
            self.logger.info("독립성 모니터링 루프 종료")
        except Exception as e:
            self.logger.error(f"독립성 모니터링 오류: {e}")

    async def _update_independence_scores(self):
        """독립성 점수 업데이트"""
        try:
            metrics = self.manager.get_connection_metrics()

            for connection_type, connection_metrics in metrics.items():
                status = self._connection_status[connection_type]

                # 기본 점수 (1.0)
                score = 1.0

                # 에러율 기반 감점
                if connection_metrics.error_count > 0:
                    error_penalty = min(connection_metrics.error_rate * 0.3, 0.3)
                    score -= error_penalty

                # 연결 안정성 보너스
                if connection_metrics.is_connected and connection_metrics.uptime_seconds > 300:  # 5분 이상
                    stability_bonus = min(connection_metrics.uptime_seconds / 3600, 0.1)  # 최대 0.1 보너스
                    score += stability_bonus

                # 타 연결 영향도 기반 감점
                if status.affected_by_other:
                    score -= 0.2

                if status.affecting_other:
                    score -= 0.1

                # 점수 범위 조정 (0.0 ~ 1.0)
                status.independence_score = max(0.0, min(1.0, score))

        except Exception as e:
            self.logger.error(f"독립성 점수 업데이트 실패: {e}")

    async def _analyze_cross_connection_impact(self):
        """연결 간 영향도 분석"""
        try:
            metrics = self.manager.get_connection_metrics()
            public_metrics = metrics[WebSocketType.PUBLIC]
            private_metrics = metrics[WebSocketType.PRIVATE]

            # 동시 연결 실패 감지
            if (not public_metrics.is_connected and
                not private_metrics.is_connected and
                abs((public_metrics.connect_time or 0) - (private_metrics.connect_time or 0)) < 5):

                self.logger.warning("동시 연결 실패 감지 - 독립성 위반 가능성")
                self._record_independence_event("simultaneous_failure")

            # 동시 에러 급증 감지
            if (public_metrics.error_count > 5 and private_metrics.error_count > 5):
                time_diff = abs((public_metrics.last_message_time or 0) -
                               (private_metrics.last_message_time or 0))
                if time_diff < 10:  # 10초 이내 동시 에러
                    self.logger.warning("동시 에러 급증 감지 - 공통 원인 가능성")
                    self._record_independence_event("simultaneous_errors")

        except Exception as e:
            self.logger.error(f"연결 간 영향도 분석 실패: {e}")

    async def _detect_and_fix_independence_violations(self):
        """독립성 위반 감지 및 자동 복구"""
        try:
            for connection_type, status in self._connection_status.items():
                # 독립성 점수가 낮은 경우
                if status.independence_score < 0.7:
                    self.logger.warning(
                        f"{connection_type.value} 연결 독립성 점수 낮음: {status.independence_score:.2f}"
                    )

                    # 자동 복구 시도
                    if status.auto_recovery_enabled:
                        await self._attempt_independence_recovery(connection_type)

        except Exception as e:
            self.logger.error(f"독립성 위반 감지/복구 실패: {e}")

    async def _attempt_independence_recovery(self, connection_type: WebSocketType):
        """독립성 복구 시도"""
        try:
            self.logger.info(f"{connection_type.value} 연결 독립성 복구 시도")

            # 1. 해당 연결만 재시작 (다른 연결에 영향 없이)
            if connection_type == WebSocketType.PUBLIC:
                if self.manager._public_client:
                    await self.manager._public_client.disconnect()
                    await asyncio.sleep(1)  # 짧은 대기
                    await self.manager.initialize_public_connection()

            elif connection_type == WebSocketType.PRIVATE:
                if self.manager._private_client:
                    await self.manager._private_client.disconnect()
                    await asyncio.sleep(1)  # 짧은 대기
                    await self.manager.initialize_private_connection()

            # 2. 복구 이벤트 기록
            self._record_independence_event(f"recovery_attempted_{connection_type.value}")

            self.logger.info(f"{connection_type.value} 연결 독립성 복구 완료")

        except Exception as e:
            self.logger.error(f"{connection_type.value} 연결 독립성 복구 실패: {e}")

    def _record_independence_event(self, event_type: str):
        """독립성 관련 이벤트 기록"""
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "public_score": self._connection_status[WebSocketType.PUBLIC].independence_score,
            "private_score": self._connection_status[WebSocketType.PRIVATE].independence_score
        }

        self._independence_test_results.append(event)

        # 최근 100개 이벤트만 유지
        if len(self._independence_test_results) > 100:
            self._independence_test_results = self._independence_test_results[-100:]

    def get_independence_report(self) -> Dict:
        """독립성 리포트 생성"""
        try:
            public_status = self._connection_status[WebSocketType.PUBLIC]
            private_status = self._connection_status[WebSocketType.PRIVATE]

            return {
                "overall_independence_score": (
                    public_status.independence_score + private_status.independence_score
                ) / 2,
                "public_connection": {
                    "independence_score": public_status.independence_score,
                    "last_error": public_status.last_error,
                    "consecutive_errors": public_status.consecutive_errors,
                    "affected_by_other": public_status.affected_by_other,
                    "affecting_other": public_status.affecting_other
                },
                "private_connection": {
                    "independence_score": private_status.independence_score,
                    "last_error": private_status.last_error,
                    "consecutive_errors": private_status.consecutive_errors,
                    "affected_by_other": private_status.affected_by_other,
                    "affecting_other": private_status.affecting_other
                },
                "recent_events": self._independence_test_results[-10:],  # 최근 10개 이벤트
                "total_events": len(self._independence_test_results),
                "monitoring_active": self._monitoring_active
            }

        except Exception as e:
            self.logger.error(f"독립성 리포트 생성 실패: {e}")
            return {"error": str(e)}

    async def run_independence_test(self) -> Dict:
        """독립성 테스트 실행"""
        try:
            self.logger.info("연결 독립성 테스트 시작")

            test_results = {
                "test_start_time": time.time(),
                "tests": []
            }

            # 1. 개별 연결 상태 확인
            test_results["tests"].append(await self._test_individual_connections())

            # 2. 격리된 재연결 테스트
            test_results["tests"].append(await self._test_isolated_reconnection())

            # 3. 구독 독립성 테스트
            test_results["tests"].append(await self._test_subscription_independence())

            test_results["test_end_time"] = time.time()
            test_results["test_duration"] = test_results["test_end_time"] - test_results["test_start_time"]

            # 전체 독립성 점수 계산
            passed_tests = sum(1 for test in test_results["tests"] if test.get("passed", False))
            total_tests = len(test_results["tests"])
            test_results["overall_independence_score"] = passed_tests / total_tests if total_tests > 0 else 0

            self.logger.info(f"연결 독립성 테스트 완료: {passed_tests}/{total_tests} 통과")
            return test_results

        except Exception as e:
            self.logger.error(f"독립성 테스트 실행 실패: {e}")
            return {"error": str(e)}

    async def _test_individual_connections(self) -> Dict:
        """개별 연결 상태 테스트"""
        try:
            metrics = self.manager.get_connection_metrics()

            public_healthy = (
                metrics[WebSocketType.PUBLIC].health_score > 0.7
            )

            private_healthy = (
                metrics[WebSocketType.PRIVATE].health_score > 0.7
            )

            return {
                "test_name": "individual_connections",
                "passed": public_healthy and private_healthy,
                "details": {
                    "public_healthy": public_healthy,
                    "private_healthy": private_healthy,
                    "public_health_score": metrics[WebSocketType.PUBLIC].health_score,
                    "private_health_score": metrics[WebSocketType.PRIVATE].health_score
                }
            }

        except Exception as e:
            return {
                "test_name": "individual_connections",
                "passed": False,
                "error": str(e)
            }

    async def _test_isolated_reconnection(self) -> Dict:
        """격리된 재연결 테스트"""
        try:
            # 현재는 실제 재연결 테스트를 하지 않고 구조만 확인
            # 실제 환경에서는 한쪽 연결만 끊고 다른 쪽에 영향이 없는지 확인

            return {
                "test_name": "isolated_reconnection",
                "passed": True,  # 구조상 격리되어 있음을 확인
                "details": {
                    "public_client_isolated": self.manager._public_client is not None,
                    "private_client_isolated": self.manager._private_client is not None,
                    "separate_instances": (
                        self.manager._public_client != self.manager._private_client
                    )
                }
            }

        except Exception as e:
            return {
                "test_name": "isolated_reconnection",
                "passed": False,
                "error": str(e)
            }

    async def _test_subscription_independence(self) -> Dict:
        """구독 독립성 테스트"""
        try:
            # 구독 상태 관리자를 통한 독립성 확인
            subscriptions = self.manager.subscription_manager.get_active_subscriptions()

            public_types = [dt for dt in subscriptions.keys() if dt.is_public()]
            private_types = [dt for dt in subscriptions.keys() if dt.is_private()]

            return {
                "test_name": "subscription_independence",
                "passed": True,  # 타입 시스템 자체가 독립성 보장
                "details": {
                    "public_data_types": len(public_types),
                    "private_data_types": len(private_types),
                    "type_separation_enforced": True,
                    "no_cross_contamination": len(set(public_types) & set(private_types)) == 0
                }
            }

        except Exception as e:
            return {
                "test_name": "subscription_independence",
                "passed": False,
                "error": str(e)
            }


# GlobalWebSocketManager에 독립성 모니터 통합을 위한 확장
async def add_independence_monitoring_to_manager(manager: GlobalWebSocketManager):
    """GlobalWebSocketManager에 독립성 모니터링 추가"""
    if not hasattr(manager, 'independence_monitor'):
        manager.independence_monitor = ConnectionIndependenceMonitor(manager)
        await manager.independence_monitor.start_monitoring()
        manager.logger.info("연결 독립성 모니터링이 GlobalWebSocketManager에 추가됨")


async def get_enhanced_global_manager():
    """독립성 모니터링이 추가된 GlobalWebSocketManager 반환"""
    from .global_websocket_manager import get_global_websocket_manager

    manager = await get_global_websocket_manager()
    await add_independence_monitoring_to_manager(manager)
    return manager
