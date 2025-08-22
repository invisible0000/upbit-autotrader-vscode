"""
성능 최적화 엔진

실시간 네트워크 사용량 모니터링과 시스템 성능 최적화를 담당합니다.
Test 08-11 검증 기반으로 5,241 symbols/sec 목표 달성을 위한 지능형 최적화를 제공합니다.

핵심 기능:
- 실시간 네트워크 사용량 모니터링
- 동적 구독 조절 및 최적화
- 성능 병목점 자동 감지 및 해결
- Usage Context별 맞춤형 최적화 정책
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import time
import statistics

from upbit_auto_trading.infrastructure.logging import create_component_logger
from ..models import UsageContext, NetworkPolicy

logger = create_component_logger("PerformanceOptimizer")


class OptimizationAction(Enum):
    """최적화 액션 타입"""
    MERGE_GROUPS = "merge_groups"           # 그룹 병합
    SPLIT_GROUP = "split_group"             # 그룹 분할
    ADJUST_BATCH_SIZE = "adjust_batch_size" # 배치 크기 조정
    THROTTLE_REQUESTS = "throttle_requests" # 요청 제한
    INCREASE_CAPACITY = "increase_capacity" # 용량 증가
    PAUSE_LOW_PRIORITY = "pause_low_priority" # 저우선순위 일시중지


@dataclass
class PerformanceThreshold:
    """성능 임계값"""
    max_latency_ms: float
    max_network_usage: float
    min_success_rate: float
    max_error_rate: float
    target_symbols_per_sec: float


@dataclass
class OptimizationRecommendation:
    """최적화 권장사항"""
    action: OptimizationAction
    priority: int  # 1-10 (10이 최고 우선순위)
    description: str
    expected_improvement: str
    estimated_impact: float  # 0.0-1.0
    context_affected: List[UsageContext]

    @property
    def is_critical(self) -> bool:
        return self.priority >= 8


@dataclass
class NetworkUsageMetrics:
    """네트워크 사용량 메트릭"""
    current_usage_percent: float
    peak_usage_percent: float
    avg_usage_percent: float
    bytes_per_second: int
    connections_count: int
    bandwidth_efficiency: float

    @property
    def is_congested(self) -> bool:
        return self.current_usage_percent > 80.0

    @property
    def utilization_grade(self) -> str:
        if self.current_usage_percent < 20:
            return "LOW"
        elif self.current_usage_percent < 50:
            return "OPTIMAL"
        elif self.current_usage_percent < 80:
            return "HIGH"
        else:
            return "CRITICAL"


@dataclass
class SystemPerformanceSnapshot:
    """시스템 성능 스냅샷"""
    timestamp: datetime
    network_metrics: NetworkUsageMetrics
    total_symbols: int
    active_groups: int
    avg_latency_ms: float
    symbols_per_second: float
    success_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float

    @property
    def performance_score(self) -> float:
        """성능 점수 (0.0-1.0)"""
        latency_score = max(0.0, 1.0 - (self.avg_latency_ms / 100.0))  # 100ms 기준
        throughput_score = min(1.0, self.symbols_per_second / 5241.0)  # Test 08-11 기준
        success_score = self.success_rate
        network_score = max(0.0, 1.0 - (self.network_metrics.current_usage_percent / 100.0))

        return (latency_score * 0.3 + throughput_score * 0.4 +
                success_score * 0.2 + network_score * 0.1)


class PerformanceOptimizer:
    """성능 최적화 엔진

    실시간 네트워크 모니터링과 시스템 성능 최적화를 제공합니다.
    """

    def __init__(self):
        """성능 최적화 엔진 초기화"""
        logger.info("PerformanceOptimizer 초기화 시작")

        # Test 08-11 기반 성능 임계값
        self._performance_thresholds = {
            UsageContext.REALTIME_TRADING: PerformanceThreshold(
                max_latency_ms=5.0,
                max_network_usage=0.9,  # 90%
                min_success_rate=0.999,  # 99.9%
                max_error_rate=0.001,
                target_symbols_per_sec=1000.0
            ),
            UsageContext.MARKET_SCANNING: PerformanceThreshold(
                max_latency_ms=20.0,
                max_network_usage=0.8,  # 80%
                min_success_rate=0.98,  # 98%
                max_error_rate=0.02,
                target_symbols_per_sec=5241.0  # Test 08-11 목표
            ),
            UsageContext.PORTFOLIO_MONITORING: PerformanceThreshold(
                max_latency_ms=10.0,
                max_network_usage=0.7,  # 70%
                min_success_rate=0.995,  # 99.5%
                max_error_rate=0.005,
                target_symbols_per_sec=2000.0
            ),
            UsageContext.RESEARCH_ANALYSIS: PerformanceThreshold(
                max_latency_ms=100.0,
                max_network_usage=0.3,  # 30%
                min_success_rate=0.95,  # 95%
                max_error_rate=0.05,
                target_symbols_per_sec=500.0
            )
        }

        # 성능 모니터링
        self._performance_history: List[SystemPerformanceSnapshot] = []
        self._network_usage_history: List[float] = []
        self._optimization_callbacks: List[Callable] = []

        # 최적화 상태
        self._last_optimization_time = datetime.now()
        self._optimization_in_progress = False
        self._current_recommendations: List[OptimizationRecommendation] = []

        # 모니터링 설정
        self.MONITORING_INTERVAL_SEC = 5.0
        self.OPTIMIZATION_INTERVAL_SEC = 30.0
        self.HISTORY_RETENTION_MINUTES = 60

        logger.info("PerformanceOptimizer 초기화 완료")

    async def start_monitoring(self) -> None:
        """성능 모니터링 시작"""
        logger.info("성능 모니터링 시작")

        # 주기적 모니터링 태스크 시작
        asyncio.create_task(self._performance_monitoring_loop())
        asyncio.create_task(self._optimization_loop())

    async def _performance_monitoring_loop(self) -> None:
        """성능 모니터링 루프"""
        while True:
            try:
                await asyncio.sleep(self.MONITORING_INTERVAL_SEC)

                # 현재 성능 스냅샷 수집
                snapshot = await self._collect_performance_snapshot()
                self._performance_history.append(snapshot)

                # 네트워크 사용량 히스토리 업데이트
                self._network_usage_history.append(snapshot.network_metrics.current_usage_percent)

                # 히스토리 정리 (메모리 관리)
                await self._cleanup_old_history()

                # 성능 이슈 감지
                issues = await self._detect_performance_issues(snapshot)
                if issues:
                    logger.warning(f"성능 이슈 감지: {len(issues)}개")
                    for issue in issues:
                        logger.warning(f"  - {issue}")

            except Exception as e:
                logger.error(f"성능 모니터링 오류: {str(e)}")

    async def _optimization_loop(self) -> None:
        """최적화 루프"""
        while True:
            try:
                await asyncio.sleep(self.OPTIMIZATION_INTERVAL_SEC)

                if not self._optimization_in_progress:
                    await self._run_optimization_cycle()

            except Exception as e:
                logger.error(f"최적화 루프 오류: {str(e)}")

    async def _collect_performance_snapshot(self) -> SystemPerformanceSnapshot:
        """현재 성능 스냅샷 수집"""
        # 실제 구현에서는 시스템 메트릭 수집
        # 현재는 시뮬레이션 데이터 생성

        current_time = datetime.now()

        # 네트워크 메트릭 시뮬레이션
        base_usage = 30.0 + (hash(str(current_time)) % 20)  # 30-50% 범위
        network_metrics = NetworkUsageMetrics(
            current_usage_percent=base_usage,
            peak_usage_percent=base_usage + 10,
            avg_usage_percent=base_usage - 5,
            bytes_per_second=int(base_usage * 1024 * 1024),  # MB/s
            connections_count=5,
            bandwidth_efficiency=0.8
        )

        # 시스템 성능 시뮬레이션
        symbols_count = 100 + (hash(str(current_time)) % 50)
        latency = 12.0 + (hash(str(current_time)) % 10)

        return SystemPerformanceSnapshot(
            timestamp=current_time,
            network_metrics=network_metrics,
            total_symbols=symbols_count,
            active_groups=3,
            avg_latency_ms=latency,
            symbols_per_second=symbols_count / (latency / 1000.0),
            success_rate=0.985 + (hash(str(current_time)) % 15) / 1000.0,
            memory_usage_mb=256.0,
            cpu_usage_percent=25.0
        )

    async def _detect_performance_issues(self, snapshot: SystemPerformanceSnapshot) -> List[str]:
        """성능 이슈 감지"""
        issues = []

        # 네트워크 사용량 확인
        if snapshot.network_metrics.is_congested:
            issues.append(f"네트워크 사용량 높음: {snapshot.network_metrics.current_usage_percent:.1f}%")

        # 지연시간 확인
        if snapshot.avg_latency_ms > 50.0:
            issues.append(f"평균 지연시간 높음: {snapshot.avg_latency_ms:.2f}ms")

        # 처리량 확인
        if snapshot.symbols_per_second < 1000.0:
            issues.append(f"처리량 낮음: {snapshot.symbols_per_second:.1f} symbols/sec")

        # 성공률 확인
        if snapshot.success_rate < 0.95:
            issues.append(f"성공률 낮음: {snapshot.success_rate:.2%}")

        return issues

    async def _run_optimization_cycle(self) -> None:
        """최적화 사이클 실행"""
        if not self._performance_history:
            return

        logger.info("최적화 사이클 시작")
        self._optimization_in_progress = True

        try:
            # 최근 성능 데이터 분석
            recent_snapshots = self._performance_history[-10:]  # 최근 10개

            # 최적화 권장사항 생성
            recommendations = await self._generate_optimization_recommendations(recent_snapshots)
            self._current_recommendations = recommendations

            # 고우선순위 권장사항 자동 적용
            critical_recommendations = [r for r in recommendations if r.is_critical]

            if critical_recommendations:
                logger.info(f"긴급 최적화 적용: {len(critical_recommendations)}개")
                for rec in critical_recommendations:
                    await self._apply_optimization_recommendation(rec)

            # 최적화 콜백 실행
            for callback in self._optimization_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(recommendations)
                    else:
                        callback(recommendations)
                except Exception as e:
                    logger.error(f"최적화 콜백 오류: {str(e)}")

            self._last_optimization_time = datetime.now()

        finally:
            self._optimization_in_progress = False
            logger.info("최적화 사이클 완료")

    async def _generate_optimization_recommendations(
        self,
        snapshots: List[SystemPerformanceSnapshot]
    ) -> List[OptimizationRecommendation]:
        """최적화 권장사항 생성"""
        recommendations = []

        if not snapshots:
            return recommendations

        latest = snapshots[-1]

        # 네트워크 사용량 기반 권장사항
        if latest.network_metrics.current_usage_percent > 80:
            recommendations.append(OptimizationRecommendation(
                action=OptimizationAction.MERGE_GROUPS,
                priority=9,
                description="네트워크 사용량 높음 - 그룹 병합 권장",
                expected_improvement="네트워크 효율성 15-20% 향상",
                estimated_impact=0.8,
                context_affected=[UsageContext.MARKET_SCANNING]
            ))

        # 지연시간 기반 권장사항
        avg_latency = statistics.mean([s.avg_latency_ms for s in snapshots])
        if avg_latency > 30.0:
            recommendations.append(OptimizationRecommendation(
                action=OptimizationAction.SPLIT_GROUP,
                priority=7,
                description=f"평균 지연시간 높음 ({avg_latency:.1f}ms) - 그룹 분할 권장",
                expected_improvement="지연시간 20-30% 감소",
                estimated_impact=0.6,
                context_affected=[UsageContext.REALTIME_TRADING, UsageContext.PORTFOLIO_MONITORING]
            ))

        # 처리량 기반 권장사항
        if latest.symbols_per_second < 3000:
            recommendations.append(OptimizationRecommendation(
                action=OptimizationAction.ADJUST_BATCH_SIZE,
                priority=6,
                description=f"처리량 부족 ({latest.symbols_per_second:.0f} symbols/sec) - 배치 크기 조정",
                expected_improvement="처리량 25-40% 향상",
                estimated_impact=0.7,
                context_affected=[UsageContext.MARKET_SCANNING]
            ))

        # 성공률 기반 권장사항
        if latest.success_rate < 0.98:
            recommendations.append(OptimizationRecommendation(
                action=OptimizationAction.THROTTLE_REQUESTS,
                priority=8,
                description=f"성공률 낮음 ({latest.success_rate:.2%}) - 요청 제한 권장",
                expected_improvement="성공률 5-10% 향상",
                estimated_impact=0.5,
                context_affected=[UsageContext.RESEARCH_ANALYSIS]
            ))

        # 우선순위별 정렬
        recommendations.sort(key=lambda x: x.priority, reverse=True)

        return recommendations

    async def _apply_optimization_recommendation(self, recommendation: OptimizationRecommendation) -> bool:
        """최적화 권장사항 적용"""
        logger.info(f"최적화 적용: {recommendation.action.value} - {recommendation.description}")

        try:
            # 실제 구현에서는 각 액션별 구체적인 최적화 로직 실행
            # 현재는 시뮬레이션
            await asyncio.sleep(0.1)  # 최적화 처리 시뮬레이션

            logger.info(f"최적화 완료: {recommendation.expected_improvement}")
            return True

        except Exception as e:
            logger.error(f"최적화 적용 실패: {str(e)}")
            return False

    async def _cleanup_old_history(self) -> None:
        """오래된 히스토리 정리"""
        cutoff_time = datetime.now() - timedelta(minutes=self.HISTORY_RETENTION_MINUTES)

        # 성능 히스토리 정리
        self._performance_history = [
            s for s in self._performance_history
            if s.timestamp > cutoff_time
        ]

        # 네트워크 사용량 히스토리 정리 (최근 100개만 유지)
        if len(self._network_usage_history) > 100:
            self._network_usage_history = self._network_usage_history[-100:]

    def register_optimization_callback(self, callback: Callable) -> None:
        """최적화 콜백 등록"""
        self._optimization_callbacks.append(callback)
        logger.info(f"최적화 콜백 등록 완료 - 총 {len(self._optimization_callbacks)}개")

    async def get_current_network_usage(self) -> NetworkUsageMetrics:
        """현재 네트워크 사용량 조회"""
        if self._performance_history:
            return self._performance_history[-1].network_metrics

        # 기본값 반환
        return NetworkUsageMetrics(
            current_usage_percent=0.0,
            peak_usage_percent=0.0,
            avg_usage_percent=0.0,
            bytes_per_second=0,
            connections_count=0,
            bandwidth_efficiency=0.0
        )

    async def get_performance_report(self) -> Dict[str, Any]:
        """성능 보고서 조회"""
        if not self._performance_history:
            return {"status": "no_data", "message": "성능 데이터 없음"}

        latest = self._performance_history[-1]
        recent_snapshots = self._performance_history[-10:]

        # 평균 계산
        avg_latency = statistics.mean([s.avg_latency_ms for s in recent_snapshots])
        avg_throughput = statistics.mean([s.symbols_per_second for s in recent_snapshots])
        avg_success_rate = statistics.mean([s.success_rate for s in recent_snapshots])
        avg_network_usage = statistics.mean([s.network_metrics.current_usage_percent for s in recent_snapshots])

        return {
            "timestamp": latest.timestamp.isoformat(),
            "current_performance": {
                "latency_ms": latest.avg_latency_ms,
                "symbols_per_second": latest.symbols_per_second,
                "success_rate": latest.success_rate,
                "network_usage_percent": latest.network_metrics.current_usage_percent,
                "performance_score": latest.performance_score,
                "total_symbols": latest.total_symbols,
                "active_groups": latest.active_groups
            },
            "averages_last_10_cycles": {
                "avg_latency_ms": avg_latency,
                "avg_throughput": avg_throughput,
                "avg_success_rate": avg_success_rate,
                "avg_network_usage": avg_network_usage
            },
            "network_status": {
                "utilization_grade": latest.network_metrics.utilization_grade,
                "is_congested": latest.network_metrics.is_congested,
                "bandwidth_efficiency": latest.network_metrics.bandwidth_efficiency
            },
            "optimization_status": {
                "last_optimization": self._last_optimization_time.isoformat(),
                "in_progress": self._optimization_in_progress,
                "current_recommendations": len(self._current_recommendations),
                "critical_issues": len([r for r in self._current_recommendations if r.is_critical])
            },
            "test_08_11_compliance": {
                "target_symbols_per_sec": 5241.0,
                "achievement_rate": min(1.0, latest.symbols_per_second / 5241.0),
                "target_latency_ms": 11.20,
                "latency_compliance": latest.avg_latency_ms <= 20.0  # 여유분 포함
            }
        }

    async def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """현재 최적화 권장사항 조회"""
        return [
            {
                "action": rec.action.value,
                "priority": rec.priority,
                "description": rec.description,
                "expected_improvement": rec.expected_improvement,
                "estimated_impact": rec.estimated_impact,
                "is_critical": rec.is_critical,
                "affected_contexts": [ctx.value for ctx in rec.context_affected]
            }
            for rec in self._current_recommendations
        ]

    async def force_optimization(self) -> Dict[str, Any]:
        """강제 최적화 실행"""
        logger.info("강제 최적화 실행 요청")

        if self._optimization_in_progress:
            return {
                "status": "already_running",
                "message": "최적화가 이미 진행 중입니다"
            }

        await self._run_optimization_cycle()

        return {
            "status": "completed",
            "recommendations_applied": len([r for r in self._current_recommendations if r.is_critical]),
            "total_recommendations": len(self._current_recommendations),
            "timestamp": datetime.now().isoformat()
        }
