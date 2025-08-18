"""
차트뷰어 리소스 관리자

기존 시스템과 완전히 독립적으로 차트뷰어의 리소스를 관리합니다.
창 상태에 따른 우선순위 조정 및 메모리 제한을 담당합니다.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from upbit_auto_trading.domain.events.chart_viewer_events import ChartViewerPriority
from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class ChartResourceInfo:
    """차트별 리소스 정보"""
    chart_id: str
    window_state: str  # 'active', 'background', 'minimized', 'closed'
    priority_level: int
    memory_limit_mb: int
    last_activity: datetime
    is_active: bool


class ChartViewerResourceManager:
    """
    차트뷰어 리소스 관리자

    기존 시스템과 완전히 독립적으로 동작하며, 차트뷰어만의 리소스를 관리합니다.
    창 상태에 따른 우선순위 자동 조정을 담당합니다.
    """

    def __init__(self):
        self._logger = create_component_logger("ChartViewerResourceManager")
        self._chart_resources: Dict[str, ChartResourceInfo] = {}

        # 리소스 제한 설정 (기존 시스템과 독립적)
        self._resource_limits = {
            'active': {
                'priority': ChartViewerPriority.CHART_HIGH,        # 5
                'memory_mb': 256,
                'max_charts': 4
            },
            'background': {
                'priority': ChartViewerPriority.CHART_BACKGROUND,  # 8
                'memory_mb': 128,
                'max_charts': 8
            },
            'minimized': {
                'priority': ChartViewerPriority.CHART_LOW,         # 10
                'memory_mb': 64,
                'max_charts': 16
            }
        }

        self._logger.info("차트뷰어 리소스 관리자 초기화됨 (기존 시스템과 독립)")

    def register_chart(self, chart_id: str, window_state: str = 'active') -> ChartResourceInfo:
        """차트 등록 및 초기 리소스 할당"""
        try:
            if chart_id in self._chart_resources:
                self._logger.warning(f"이미 등록된 차트: {chart_id}")
                return self._chart_resources[chart_id]

            # 리소스 제한 확인
            self._validate_resource_limits(window_state)

            # 차트 리소스 정보 생성
            limits = self._resource_limits[window_state]
            resource_info = ChartResourceInfo(
                chart_id=chart_id,
                window_state=window_state,
                priority_level=limits['priority'],
                memory_limit_mb=limits['memory_mb'],
                last_activity=datetime.now(),
                is_active=window_state == 'active'
            )

            self._chart_resources[chart_id] = resource_info

            self._logger.info(
                f"차트 등록: {chart_id} "
                f"(상태: {window_state}, 우선순위: {limits['priority']}, "
                f"메모리: {limits['memory_mb']}MB)"
            )

            return resource_info

        except Exception as e:
            self._logger.error(f"차트 등록 실패: {chart_id} - {e}")
            raise

    def update_window_state(self, chart_id: str, new_state: str) -> Optional[ChartResourceInfo]:
        """창 상태 변경 및 리소스 재할당"""
        try:
            if chart_id not in self._chart_resources:
                self._logger.warning(f"등록되지 않은 차트: {chart_id}")
                return None

            resource_info = self._chart_resources[chart_id]
            old_state = resource_info.window_state

            if old_state == new_state:
                self._logger.debug(f"차트 상태 변경 없음: {chart_id} ({new_state})")
                return resource_info

            # 리소스 제한 확인
            self._validate_resource_limits(new_state)

            # 리소스 정보 업데이트
            limits = self._resource_limits[new_state]
            resource_info.window_state = new_state
            resource_info.priority_level = limits['priority']
            resource_info.memory_limit_mb = limits['memory_mb']
            resource_info.last_activity = datetime.now()
            resource_info.is_active = new_state == 'active'

            self._logger.info(
                f"차트 상태 변경: {chart_id} "
                f"({old_state} → {new_state}, "
                f"우선순위: {limits['priority']}, "
                f"메모리: {limits['memory_mb']}MB)"
            )

            # 리소스 조정 로직 호출
            self._adjust_chart_resources(chart_id, old_state, new_state)

            return resource_info

        except Exception as e:
            self._logger.error(f"창 상태 변경 실패: {chart_id} - {e}")
            raise

    def unregister_chart(self, chart_id: str) -> bool:
        """차트 등록 해제 및 리소스 회수"""
        try:
            if chart_id not in self._chart_resources:
                self._logger.warning(f"등록되지 않은 차트: {chart_id}")
                return False

            resource_info = self._chart_resources.pop(chart_id)

            self._logger.info(
                f"차트 등록 해제: {chart_id} "
                f"(메모리 회수: {resource_info.memory_limit_mb}MB)"
            )

            return True

        except Exception as e:
            self._logger.error(f"차트 등록 해제 실패: {chart_id} - {e}")
            return False

    def get_chart_priority(self, chart_id: str) -> int:
        """차트의 현재 우선순위 조회"""
        if chart_id not in self._chart_resources:
            return ChartViewerPriority.CHART_LOW  # 기본값

        return self._chart_resources[chart_id].priority_level

    def get_active_charts(self) -> Dict[str, ChartResourceInfo]:
        """활성 차트 목록 조회"""
        return {
            chart_id: info for chart_id, info in self._chart_resources.items()
            if info.is_active
        }

    def get_chart_by_state(self, window_state: str) -> Dict[str, ChartResourceInfo]:
        """특정 상태의 차트 목록 조회"""
        return {
            chart_id: info for chart_id, info in self._chart_resources.items()
            if info.window_state == window_state
        }

    def get_resource_statistics(self) -> Dict[str, Any]:
        """리소스 사용 통계 조회"""
        stats = {
            'total_charts': len(self._chart_resources),
            'active_charts': len([info for info in self._chart_resources.values() if info.is_active]),
            'by_state': {},
            'total_memory_mb': 0,
            'priority_distribution': {}
        }

        # 상태별 통계
        for state in ['active', 'background', 'minimized']:
            charts_in_state = [info for info in self._chart_resources.values() if info.window_state == state]
            stats['by_state'][state] = {
                'count': len(charts_in_state),
                'memory_mb': sum(info.memory_limit_mb for info in charts_in_state)
            }

        # 총 메모리 사용량
        stats['total_memory_mb'] = sum(info.memory_limit_mb for info in self._chart_resources.values())

        # 우선순위별 분포
        for priority in [ChartViewerPriority.CHART_HIGH, ChartViewerPriority.CHART_BACKGROUND, ChartViewerPriority.CHART_LOW]:
            count = len([info for info in self._chart_resources.values() if info.priority_level == priority])
            stats['priority_distribution'][priority] = count

        return stats

    def _validate_resource_limits(self, window_state: str) -> None:
        """리소스 제한 검증"""
        if window_state not in self._resource_limits:
            raise ValueError(f"지원하지 않는 창 상태: {window_state}")

        # 상태별 최대 차트 수 확인
        current_count = len(self.get_chart_by_state(window_state))
        max_count = self._resource_limits[window_state]['max_charts']

        if current_count >= max_count:
            self._logger.warning(
                f"리소스 제한 도달: {window_state} 상태 차트 "
                f"({current_count}/{max_count})"
            )
            # 경고만 출력하고 계속 진행 (기존 시스템에 영향 없음)

    def _adjust_chart_resources(self, chart_id: str, old_state: str, new_state: str) -> None:
        """차트 리소스 조정 (기존 시스템과 독립)"""
        try:
            # 기존 시스템에 영향을 주지 않는 안전한 리소스 조정
            old_priority = self._resource_limits[old_state]['priority']
            new_priority = self._resource_limits[new_state]['priority']

            if new_priority > old_priority:  # 우선순위 낮아짐
                self._logger.debug(f"차트 리소스 감소: {chart_id} ({old_priority} → {new_priority})")
                # 리소스 사용량 감소 로직 (후속 Phase에서 구현)

            elif new_priority < old_priority:  # 우선순위 높아짐
                self._logger.debug(f"차트 리소스 증가: {chart_id} ({old_priority} → {new_priority})")
                # 리소스 사용량 증가 로직 (후속 Phase에서 구현)

            # 기존 시스템과 격리된 메모리 관리
            old_memory = self._resource_limits[old_state]['memory_mb']
            new_memory = self._resource_limits[new_state]['memory_mb']
            memory_diff = new_memory - old_memory

            if memory_diff != 0:
                self._logger.debug(
                    f"차트 메모리 조정: {chart_id} "
                    f"({old_memory}MB → {new_memory}MB, 변화: {memory_diff:+d}MB)"
                )

        except Exception as e:
            self._logger.error(f"차트 리소스 조정 실패: {chart_id} - {e}")

    def cleanup(self) -> None:
        """리소스 정리"""
        try:
            chart_count = len(self._chart_resources)
            total_memory = sum(info.memory_limit_mb for info in self._chart_resources.values())

            self._chart_resources.clear()

            self._logger.info(
                f"차트뷰어 리소스 관리자 정리 완료 "
                f"(차트: {chart_count}개, 메모리: {total_memory}MB 회수)"
            )

        except Exception as e:
            self._logger.error(f"리소스 관리자 정리 실패: {e}")


# 창 상태별 우선순위 매핑 함수 (기존 시스템과 호환)
def get_priority_for_window_state(window_state: str) -> int:
    """창 상태에 따른 우선순위 반환 (기존 시스템 안전)"""
    return ChartViewerPriority.get_window_priority(window_state)


# 리소스 제한 상수 정의
class ChartViewerResourceLimits:
    """차트뷰어 리소스 제한 상수"""

    # 메모리 제한 (MB)
    MEMORY_ACTIVE = 256
    MEMORY_BACKGROUND = 128
    MEMORY_MINIMIZED = 64

    # 차트 수 제한
    MAX_ACTIVE_CHARTS = 4
    MAX_BACKGROUND_CHARTS = 8
    MAX_MINIMIZED_CHARTS = 16

    # 총 메모리 제한 (기존 시스템 영향 없도록)
    TOTAL_MEMORY_LIMIT_MB = 2048  # 2GB
