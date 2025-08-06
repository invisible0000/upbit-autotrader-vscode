"""
Terminal Output Parser - 터미널 출력 파싱 시스템
==============================================

터미널 출력을 구조화된 데이터로 파싱하는 시스템
LLM 에이전트가 이해하기 쉬운 형태로 변환
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum


class OutputType(Enum):
    """출력 타입 분류"""
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    LLM_REPORT = "llm_report"
    PERFORMANCE = "performance"
    STATUS = "status"
    DEBUG = "debug"
    UNKNOWN = "unknown"


@dataclass
class ParsedOutput:
    """파싱된 터미널 출력 데이터"""
    type: OutputType
    raw_line: str
    parsed_data: Tuple[str, ...]
    timestamp: datetime
    component: Optional[str] = None
    level: Optional[str] = None
    message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TerminalOutputParser:
    """
    터미널 출력 구조화 파싱 시스템

    다양한 로그 패턴을 인식하고 LLM이 이해하기 쉬운 구조로 변환
    """

    # 파싱 패턴 정의
    PATTERNS = {
        OutputType.LLM_REPORT: re.compile(
            r'🤖 LLM_REPORT: Operation=([^,]+), Status=([^,]+), Details=(.+)'
        ),
        OutputType.WARNING: re.compile(
            r'WARNING.*?-\s*([^-]+)\s*-.*?(.+)'
        ),
        OutputType.ERROR: re.compile(
            r'ERROR.*?-\s*([^-]+)\s*-.*?(.+)'
        ),
        OutputType.INFO: re.compile(
            r'INFO.*?-\s*([^-]+)\s*-.*?(.+)'
        ),
        OutputType.DEBUG: re.compile(
            r'DEBUG.*?-\s*([^-]+)\s*-.*?(.+)'
        ),
        OutputType.PERFORMANCE: re.compile(
            r'⏱️.*?(\d+\.?\d*)\s*(초|ms|분)'
        ),
        OutputType.STATUS: re.compile(
            r'(✅|⚠️|❌|🎯|🚀|📊|🔧)\s*(.+)'
        )
    }

    # 컴포넌트 추출 패턴
    COMPONENT_PATTERNS = {
        'main_window': re.compile(r'(MainWindow|main_window)', re.IGNORECASE),
        'di_container': re.compile(r'(DI.?Container|ApplicationContainer)', re.IGNORECASE),
        'mvp_container': re.compile(r'(MVP.?Container|mvp_container)', re.IGNORECASE),
        'theme_service': re.compile(r'(ThemeService|theme_service)', re.IGNORECASE),
        'logging_service': re.compile(r'(LoggingService|logging_service)', re.IGNORECASE),
        'database_manager': re.compile(r'(DatabaseManager|database_manager)', re.IGNORECASE),
        'strategy_management': re.compile(r'(Strategy|전략)', re.IGNORECASE),
        'trigger_builder': re.compile(r'(Trigger|트리거)', re.IGNORECASE)
    }

    def __init__(self):
        """파서 초기화"""
        self.parsing_stats = {
            'total_parsed': 0,
            'by_type': {output_type: 0 for output_type in OutputType},
            'unknown_patterns': []
        }

    def parse_output(self, lines: List[str]) -> List[ParsedOutput]:
        """
        터미널 출력 라인들을 구조화된 데이터로 파싱

        Args:
            lines: 파싱할 터미널 출력 라인들

        Returns:
            List[ParsedOutput]: 파싱된 출력 데이터 목록
        """
        parsed_outputs = []

        for line in lines:
            parsed = self._parse_single_line(line)
            if parsed:
                parsed_outputs.append(parsed)
                self.parsing_stats['total_parsed'] += 1
                self.parsing_stats['by_type'][parsed.type] += 1

        return parsed_outputs

    def _parse_single_line(self, line: str) -> Optional[ParsedOutput]:
        """
        단일 라인 파싱

        Args:
            line: 파싱할 라인

        Returns:
            Optional[ParsedOutput]: 파싱된 데이터 또는 None
        """
        # 타임스탬프 추출
        timestamp = self._extract_timestamp(line)

        # 각 패턴으로 매칭 시도
        for output_type, pattern in self.PATTERNS.items():
            match = pattern.search(line)
            if match:
                parsed_data = match.groups()
                component = self._extract_component(line)

                parsed_output = ParsedOutput(
                    type=output_type,
                    raw_line=line,
                    parsed_data=parsed_data,
                    timestamp=timestamp,
                    component=component
                )

                # 특별한 처리가 필요한 타입들
                if output_type == OutputType.LLM_REPORT:
                    self._enrich_llm_report(parsed_output)
                elif output_type in [OutputType.WARNING, OutputType.ERROR, OutputType.INFO, OutputType.DEBUG]:
                    self._enrich_log_entry(parsed_output)
                elif output_type == OutputType.PERFORMANCE:
                    self._enrich_performance_data(parsed_output)
                elif output_type == OutputType.STATUS:
                    self._enrich_status_data(parsed_output)

                return parsed_output

        # 매칭되지 않은 패턴 기록
        if line.strip() and not line.startswith('['):  # 타임스탬프 라인 제외
            self.parsing_stats['unknown_patterns'].append(line[:100])  # 처음 100자만

        return None

    def _extract_timestamp(self, line: str) -> datetime:
        """라인에서 타임스탬프 추출"""
        # [YYYY-MM-DD HH:MM:SS.mmm] 패턴 찾기
        timestamp_pattern = re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\]')
        match = timestamp_pattern.search(line)

        if match:
            try:
                return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                pass

        # 기본값으로 현재 시간 반환
        return datetime.now()

    def _extract_component(self, line: str) -> Optional[str]:
        """라인에서 컴포넌트 이름 추출"""
        for component_name, pattern in self.COMPONENT_PATTERNS.items():
            if pattern.search(line):
                return component_name
        return None

    def _enrich_llm_report(self, parsed_output: ParsedOutput) -> None:
        """LLM 보고서 데이터 강화"""
        if len(parsed_output.parsed_data) >= 3:
            operation, status, details = parsed_output.parsed_data[:3]
            parsed_output.metadata.update({
                'operation': operation,
                'status': status,
                'details': details,
                'category': self._categorize_operation(operation),
                'priority': self._assess_priority(status)
            })

    def _enrich_log_entry(self, parsed_output: ParsedOutput) -> None:
        """일반 로그 엔트리 데이터 강화"""
        if len(parsed_output.parsed_data) >= 2:
            component, message = parsed_output.parsed_data[:2]
            parsed_output.component = component.strip() if component else parsed_output.component
            parsed_output.message = message.strip() if message else None
            parsed_output.level = parsed_output.type.value.upper()

    def _enrich_performance_data(self, parsed_output: ParsedOutput) -> None:
        """성능 데이터 강화"""
        if len(parsed_output.parsed_data) >= 2:
            value, unit = parsed_output.parsed_data[:2]
            try:
                numeric_value = float(value)
                # 단위를 초로 통일
                if unit == 'ms':
                    numeric_value /= 1000
                elif unit == '분':
                    numeric_value *= 60

                parsed_output.metadata.update({
                    'value': numeric_value,
                    'original_value': value,
                    'unit': unit,
                    'value_in_seconds': numeric_value
                })
            except ValueError:
                parsed_output.metadata.update({
                    'value': value,
                    'unit': unit,
                    'parse_error': True
                })

    def _enrich_status_data(self, parsed_output: ParsedOutput) -> None:
        """상태 데이터 강화"""
        if len(parsed_output.parsed_data) >= 2:
            emoji, message = parsed_output.parsed_data[:2]
            status_map = {
                '✅': 'success',
                '⚠️': 'warning',
                '❌': 'error',
                '🎯': 'target',
                '🚀': 'launch',
                '📊': 'metrics',
                '🔧': 'config'
            }

            parsed_output.metadata.update({
                'emoji': emoji,
                'message': message.strip(),
                'status_type': status_map.get(emoji, 'unknown')
            })

    def _categorize_operation(self, operation: str) -> str:
        """Operation을 카테고리로 분류"""
        operation_lower = operation.lower()

        if any(keyword in operation_lower for keyword in ['초기화', 'init', 'setup']):
            return 'initialization'
        elif any(keyword in operation_lower for keyword in ['di', 'container', 'injection']):
            return 'dependency_injection'
        elif any(keyword in operation_lower for keyword in ['mvp', 'presenter', 'view']):
            return 'mvp_pattern'
        elif any(keyword in operation_lower for keyword in ['theme', 'style', 'ui']):
            return 'ui_theme'
        elif any(keyword in operation_lower for keyword in ['db', 'database', 'sqlite']):
            return 'database'
        elif any(keyword in operation_lower for keyword in ['strategy', '전략']):
            return 'strategy'
        elif any(keyword in operation_lower for keyword in ['logging', 'log']):
            return 'logging'
        else:
            return 'general'

    def _assess_priority(self, status: str) -> str:
        """상태에 따른 우선순위 평가"""
        status_lower = status.lower()

        if any(keyword in status_lower for keyword in ['error', '에러', 'failed', '실패']):
            return 'HIGH'
        elif any(keyword in status_lower for keyword in ['warning', '경고', 'limited', '제한']):
            return 'MEDIUM'
        elif any(keyword in status_lower for keyword in ['success', '성공', 'completed', '완료']):
            return 'LOW'
        else:
            return 'MEDIUM'

    def get_parsing_stats(self) -> Dict[str, Any]:
        """파싱 통계 반환"""
        return {
            'total_parsed': self.parsing_stats['total_parsed'],
            'by_type': {output_type.value: count for output_type, count in self.parsing_stats['by_type'].items()},
            'unknown_patterns_count': len(self.parsing_stats['unknown_patterns']),
            'unknown_patterns_sample': self.parsing_stats['unknown_patterns'][:5]  # 처음 5개만
        }

    def clear_stats(self) -> None:
        """파싱 통계 초기화"""
        self.parsing_stats = {
            'total_parsed': 0,
            'by_type': {output_type: 0 for output_type in OutputType},
            'unknown_patterns': []
        }

    def filter_by_type(self, parsed_outputs: List[ParsedOutput],
                       output_types: List[OutputType]) -> List[ParsedOutput]:
        """타입별 필터링"""
        return [output for output in parsed_outputs if output.type in output_types]

    def filter_by_component(self, parsed_outputs: List[ParsedOutput],
                           component: str) -> List[ParsedOutput]:
        """컴포넌트별 필터링"""
        return [output for output in parsed_outputs if output.component == component]

    def filter_by_priority(self, parsed_outputs: List[ParsedOutput],
                          priority: str) -> List[ParsedOutput]:
        """우선순위별 필터링"""
        return [output for output in parsed_outputs
                if output.metadata and output.metadata.get('priority') == priority]


def create_terminal_output_parser() -> TerminalOutputParser:
    """터미널 출력 파서 인스턴스 생성"""
    return TerminalOutputParser()
