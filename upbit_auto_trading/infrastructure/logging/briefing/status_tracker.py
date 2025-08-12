"""
시스템 상태 추적기 - LLM 에이전트 브리핑 시스템
실시간 컴포넌트 상태 모니터링 및 시스템 헬스 체크
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List
import json

@dataclass
class ComponentStatus:
    """개별 컴포넌트 상태 정보"""
    name: str
    status: str  # 'OK', 'WARNING', 'ERROR', 'LIMITED'
    details: str
    timestamp: datetime
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환 (JSON 직렬화용)"""
        return {
            'name': self.name,
            'status': self.status,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'metrics': self.metrics
        }

    def is_healthy(self) -> bool:
        """컴포넌트가 정상 상태인지 확인"""
        return self.status == 'OK'

    def needs_attention(self) -> bool:
        """주의가 필요한 상태인지 확인"""
        return self.status in ['WARNING', 'ERROR', 'LIMITED']

class SystemStatusTracker:
    """시스템 전체 상태 추적 및 관리"""

    def __init__(self):
        self.components: Dict[str, ComponentStatus] = {}
        self.system_start_time = datetime.now()
        self.last_update_time = datetime.now()

    def update_component_status(self,
                              component: str,
                              status: str,
                              details: str,
                              **metrics) -> None:
        """컴포넌트 상태 업데이트"""
        self.components[component] = ComponentStatus(
            name=component,
            status=status,
            details=details,
            timestamp=datetime.now(),
            metrics=metrics
        )
        self.last_update_time = datetime.now()

    def get_component_status(self, component: str) -> ComponentStatus:
        """특정 컴포넌트 상태 조회"""
        return self.components.get(component)

    def get_system_health(self) -> str:
        """전체 시스템 상태 요약"""
        if not self.components:
            return 'UNKNOWN'

        error_count = sum(1 for c in self.components.values() if c.status == 'ERROR')
        warning_count = sum(1 for c in self.components.values() if c.status in ['WARNING', 'LIMITED'])

        if error_count > 0:
            return 'ERROR'
        elif warning_count > 0:
            return 'WARNING'
        else:
            return 'OK'

    def get_healthy_components(self) -> List[ComponentStatus]:
        """정상 동작 중인 컴포넌트 목록"""
        return [c for c in self.components.values() if c.is_healthy()]

    def get_problematic_components(self) -> List[ComponentStatus]:
        """문제가 있는 컴포넌트 목록 (우선순위순)"""
        problematic = [c for c in self.components.values() if c.needs_attention()]

        # 상태별 우선순위 정렬: ERROR > WARNING > LIMITED
        priority_order = {'ERROR': 0, 'WARNING': 1, 'LIMITED': 2}
        return sorted(problematic, key=lambda x: priority_order.get(x.status, 3))

    def get_system_metrics(self) -> Dict[str, Any]:
        """전체 시스템 메트릭 수집"""
        uptime = datetime.now() - self.system_start_time

        return {
            'total_components': len(self.components),
            'healthy_components': len(self.get_healthy_components()),
            'problematic_components': len(self.get_problematic_components()),
            'system_uptime_seconds': uptime.total_seconds(),
            'last_update': self.last_update_time.isoformat(),
            'system_health': self.get_system_health()
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 관련 메트릭 추출"""
        performance_data = {}

        for component_name, status in self.components.items():
            if 'load_time' in status.metrics:
                performance_data[f'{component_name}_load_time'] = status.metrics['load_time']
            if 'memory_usage' in status.metrics:
                performance_data[f'{component_name}_memory'] = status.metrics['memory_usage']
            if 'response_time' in status.metrics:
                performance_data[f'{component_name}_response'] = status.metrics['response_time']

        return performance_data

    def clear_old_components(self, max_age_hours: int = 24) -> int:
        """오래된 컴포넌트 상태 정리"""
        cutoff_time = datetime.now()
        cutoff_time = cutoff_time.replace(hour=cutoff_time.hour - max_age_hours)

        old_components = [
            name for name, status in self.components.items()
            if status.timestamp < cutoff_time
        ]

        for component_name in old_components:
            del self.components[component_name]

        return len(old_components)

    def to_dict(self) -> Dict[str, Any]:
        """전체 상태를 딕셔너리로 변환"""
        return {
            'system_metrics': self.get_system_metrics(),
            'performance_metrics': self.get_performance_metrics(),
            'components': {
                name: status.to_dict()
                for name, status in self.components.items()
            },
            'healthy_components': [c.name for c in self.get_healthy_components()],
            'problematic_components': [
                {'name': c.name, 'status': c.status, 'details': c.details}
                for c in self.get_problematic_components()
            ]
        }

    def export_to_json(self, filepath: str) -> None:
        """JSON 파일로 상태 내보내기"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def get_status_summary(self) -> str:
        """상태 요약 문자열 생성 (브리핑용)"""
        health = self.get_system_health()
        total = len(self.components)
        healthy = len(self.get_healthy_components())
        problematic = len(self.get_problematic_components())

        health_emoji = {
            'OK': '🟢',
            'WARNING': '⚠️',
            'ERROR': '🔴',
            'UNKNOWN': '⚪'
        }.get(health, '❓')

        return f"{health_emoji} {health} ({healthy}/{total} 정상, {problematic}개 주의 필요)"
