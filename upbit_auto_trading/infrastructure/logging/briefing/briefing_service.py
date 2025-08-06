"""
LLM 브리핑 서비스 - 실시간 시스템 상태 브리핑 생성
LLM 에이전트를 위한 마크다운 형식 브리핑 및 자동 업데이트
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from ..configuration.enhanced_config import EnhancedLoggingConfig
from .status_tracker import SystemStatusTracker, ComponentStatus
from .issue_analyzer import IssueAnalyzer, SystemIssue


class LLMBriefingService:
    """LLM 에이전트를 위한 실시간 브리핑 서비스"""

    def __init__(self, config: EnhancedLoggingConfig):
        self.config = config
        self.status_tracker = SystemStatusTracker()
        self.issue_analyzer = IssueAnalyzer()
        self.briefing_path = config.briefing_path
        self.last_briefing_time = datetime.now()

        # 브리핑 디렉토리 생성
        os.makedirs(os.path.dirname(self.briefing_path), exist_ok=True)

    def generate_briefing(self) -> str:
        """실시간 브리핑 마크다운 생성"""
        current_time = datetime.now()
        system_health = self.status_tracker.get_system_health()
        issues = self.issue_analyzer.analyze_for_issues(self.status_tracker)

        # 시스템 메트릭 수집
        metrics = self.status_tracker.get_system_metrics()
        performance_metrics = self.status_tracker.get_performance_metrics()

        # 브리핑 템플릿 생성
        briefing = f"""# 🤖 LLM 에이전트 브리핑 (실시간)

**생성 시간**: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
**시스템 가동 시간**: {self._format_uptime(metrics.get('system_uptime_seconds', 0))}

---

## 📊 시스템 상태 요약

### 전체 상태: {self._status_emoji(system_health)} {system_health}

{self.status_tracker.get_status_summary()}

### 🟢 정상 동작 컴포넌트
{self._format_ok_components()}

### ⚠️ 주의 필요 컴포넌트 (우선순위순)
{self._format_problematic_components()}

---

## 🚨 감지된 이슈 ({len(issues)}개)

{self._format_issues(issues)}

---

## 📈 성능 메트릭

{self._format_performance_metrics(performance_metrics)}

---

## 🎯 권장 액션 (우선순위순)

{self._format_recommended_actions(issues)}

---

## ⏱️ 해결 시간 추정

- **총 예상 시간**: {self.issue_analyzer.get_estimated_resolution_time()}분
- **높은 우선순위**: {len([i for i in issues if i.priority == 'HIGH'])}개 이슈
- **즉시 조치 필요**: {len([i for i in issues if i.priority == 'HIGH' and 'DI' in i.category])}개

---

## 📋 시스템 정보

- **총 컴포넌트**: {metrics.get('total_components', 0)}개
- **마지막 업데이트**: {metrics.get('last_update', 'Unknown')}
- **브리핑 생성**: {current_time.isoformat()}

---

*이 브리핑은 {self.config.briefing_update_interval}초마다 자동 업데이트됩니다.*
"""

        self.last_briefing_time = current_time
        return briefing

    def update_briefing_file(self) -> None:
        """브리핑 파일 업데이트"""
        try:
            briefing_content = self.generate_briefing()
            with open(self.briefing_path, 'w', encoding='utf-8') as f:
                f.write(briefing_content)
        except Exception as e:
            # 브리핑 생성 실패 시에도 기본 정보 제공
            fallback_briefing = f"""# 🤖 LLM 에이전트 브리핑 (에러)

**생성 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## ❌ 브리핑 생성 실패

브리핑 시스템에 문제가 발생했습니다:

```
{str(e)}
```

### 💡 임시 조치 방안
1. 로그 파일 직접 확인: `logs/upbit_auto_trading.log`
2. 터미널 출력 모니터링
3. 브리핑 서비스 재시작

---
*브리핑 서비스를 재시작하여 정상 동작 복구를 시도하세요.*
"""
            with open(self.briefing_path, 'w', encoding='utf-8') as f:
                f.write(fallback_briefing)

    def update_component_status(self, component: str, status: str,
                                details: str, **metrics) -> None:
        """컴포넌트 상태 업데이트 및 브리핑 갱신"""
        self.status_tracker.update_component_status(
            component, status, details, **metrics
        )
        # 즉시 브리핑 업데이트
        self.update_briefing_file()

    def add_log_based_analysis(self, log_messages: List[str]) -> None:
        """로그 메시지 기반 이슈 분석 추가"""
        log_issues = self.issue_analyzer.analyze_log_messages(log_messages)

        # 발견된 이슈를 상태 추적기에 반영
        for issue in log_issues:
            for component in issue.affected_components:
                priority_to_status = {
                    'HIGH': 'ERROR',
                    'MEDIUM': 'WARNING',
                    'LOW': 'LIMITED'
                }
                self.status_tracker.update_component_status(
                    component,
                    priority_to_status.get(issue.priority, 'WARNING'),
                    issue.description
                )

    def _status_emoji(self, status: str) -> str:
        """상태별 이모지 반환"""
        return {
            'OK': '🟢',
            'WARNING': '⚠️',
            'ERROR': '🔴',
            'UNKNOWN': '⚪'
        }.get(status, '❓')

    def _format_uptime(self, uptime_seconds: float) -> str:
        """가동 시간 포맷팅"""
        if uptime_seconds < 60:
            return f"{uptime_seconds:.1f}초"
        elif uptime_seconds < 3600:
            return f"{uptime_seconds / 60:.1f}분"
        else:
            return f"{uptime_seconds / 3600 : .1f}시간"

    def _format_ok_components(self) -> str:
        """정상 컴포넌트 목록 포맷팅"""
        healthy_components = self.status_tracker.get_healthy_components()

        if not healthy_components:
            return "❌ 정상 동작 중인 컴포넌트가 없습니다."

        formatted = []
        for component in healthy_components:
            metrics_info = ""
            if component.metrics:
                key_metrics = []
                if 'load_time' in component.metrics:
                    key_metrics.append(f"로딩: {component.metrics['load_time']:.1f}s")
                if 'memory_usage' in component.metrics:
                    key_metrics.append(f"메모리: {component.metrics['memory_usage']}MB")
                if key_metrics:
                    metrics_info = f" ({', '.join(key_metrics)})"

            formatted.append(f"- ✅ **{component.name}**{metrics_info}")

        return "\n".join(formatted)

    def _format_problematic_components(self) -> str:
        """문제 컴포넌트 목록 포맷팅"""
        problematic = self.status_tracker.get_problematic_components()

        if not problematic:
            return "✅ 주의가 필요한 컴포넌트가 없습니다."

        formatted = []
        for component in problematic:
            emoji = self._status_emoji(component.status)
            formatted.append(f"- {emoji} **{component.name}** ({component.status})")
            formatted.append(f"  - 상세: {component.details}")
            formatted.append(f"  - 시간: {component.timestamp.strftime('%H:%M:%S')}")

        return "\n".join(formatted)

    def _format_issues(self, issues: List[SystemIssue]) -> str:
        """이슈 목록 포맷팅"""
        if not issues:
            return "✅ 감지된 이슈가 없습니다. 시스템이 정상 동작 중입니다."

        formatted = []
        for i, issue in enumerate(issues[:5], 1):  # 상위 5개 이슈만 표시
            priority_emoji = {
                'HIGH': '🔴',
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }.get(issue.priority, '⚪')

            formatted.append(f"### {i}. {priority_emoji} {issue.title}")
            formatted.append(f"**카테고리**: {issue.category} | **우선순위**: {issue.priority} | **예상 시간**: {issue.estimated_time}분")
            formatted.append(f"**설명**: {issue.description}")
            formatted.append(f"**영향 컴포넌트**: {', '.join(issue.affected_components)}")
            formatted.append("")

        if len(issues) > 5:
            formatted.append(f"*... 외 {len(issues) - 5}개 이슈 추가 감지됨*")

        return "\n".join(formatted)

    def _format_performance_metrics(self, metrics: Dict[str, Any]) -> str:
        """성능 메트릭 포맷팅"""
        if not metrics:
            return "📊 성능 데이터가 수집되지 않았습니다."

        formatted = []

        # 로딩 시간 메트릭
        load_times = {k: v for k, v in metrics.items() if 'load_time' in k}
        if load_times:
            formatted.append("**🚀 로딩 시간**")
            for metric, value in load_times.items():
                component = metric.replace('_load_time', '')
                status = "⚡" if value < 2.0 else "⚠️" if value < 5.0 else "🐌"
                formatted.append(f"- {status} {component}: {value:.1f}s")

        # 메모리 사용량
        memory_metrics = {k: v for k, v in metrics.items() if 'memory' in k}
        if memory_metrics:
            formatted.append("\n**💾 메모리 사용량**")
            for metric, value in memory_metrics.items():
                component = metric.replace('_memory', '')
                status = "✅" if value < 50 else "⚠️" if value < 100 else "🔴"
                formatted.append(f"- {status} {component}: {value}MB")

        return "\n".join(formatted) if formatted else "📊 성능 메트릭을 수집 중입니다..."

    def _format_recommended_actions(self, issues: List[SystemIssue]) -> str:
        """권장 액션 포맷팅"""
        if not issues:
            return "✅ 현재 권장되는 액션이 없습니다. 시스템이 안정적으로 동작 중입니다."

        # 높은 우선순위 이슈의 액션들을 우선 표시
        high_priority_issues = [i for i in issues if i.priority == 'HIGH']

        formatted = []

        if high_priority_issues:
            formatted.append("### 🚨 즉시 조치 필요")
            for issue in high_priority_issues:
                formatted.append(f"**{issue.title}** ({issue.estimated_time}분)")
                for j, action in enumerate(issue.suggested_actions, 1):
                    formatted.append(f"  {j}. {action}")
                formatted.append("")

        # 나머지 우선순위 이슈들
        other_issues = [i for i in issues if i.priority != 'HIGH'][:3]
        if other_issues:
            formatted.append("### 📋 후속 조치")
            for issue in other_issues:
                formatted.append(f"**{issue.title}** ({issue.priority}, {issue.estimated_time}분)")
                for j, action in enumerate(issue.suggested_actions[:2], 1):  # 상위 2개 액션만
                    formatted.append(f"  {j}. {action}")
                formatted.append("")

        return "\n".join(formatted)

    def get_briefing_summary(self) -> Dict[str, Any]:
        """브리핑 요약 정보 반환 (API용)"""
        system_health = self.status_tracker.get_system_health()
        issues = self.issue_analyzer.analyze_for_issues(self.status_tracker)

        return {
            'timestamp': datetime.now().isoformat(),
            'system_health': system_health,
            'total_components': len(self.status_tracker.components),
            'healthy_components': len(self.status_tracker.get_healthy_components()),
            'total_issues': len(issues),
            'high_priority_issues': len([i for i in issues if i.priority == 'HIGH']),
            'estimated_resolution_time': self.issue_analyzer.get_estimated_resolution_time(),
            'last_briefing_update': self.last_briefing_time.isoformat()
        }
