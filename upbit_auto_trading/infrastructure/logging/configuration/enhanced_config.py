"""
Infrastructure Layer - Enhanced Logging Configuration
===================================================

LLM 에이전트 로깅 시스템 v4.0을 위한 확장 설정
기존 LoggingConfig 기반으로 새로운 기능들을 지원
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from pathlib import Path

from .logging_config import LoggingConfig


@dataclass
class EnhancedLoggingConfig(LoggingConfig):
    """
    강화된 로깅 설정 - LLM 에이전트 최적화

    기존 LoggingConfig를 확장하여 새로운 기능들을 지원:
    - 실시간 LLM 브리핑 시스템
    - 터미널 출력 캡처 및 통합
    - 자동 진단 대시보드
    - 성능 최적화 레이어
    """

    # === LLM 브리핑 시스템 설정 ===
    briefing_enabled: bool = field(
        default_factory=lambda: os.getenv('UPBIT_LLM_BRIEFING_ENABLED', 'true').lower() == 'true'
    )
    briefing_path: str = field(
        default_factory=lambda: os.getenv('UPBIT_BRIEFING_PATH', 'logs/llm_agent_briefing.md')
    )
    briefing_update_interval: int = field(
        default_factory=lambda: int(os.getenv('UPBIT_BRIEFING_UPDATE_INTERVAL', '5'))
    )
    briefing_max_issues: int = field(
        default_factory=lambda: int(os.getenv('UPBIT_BRIEFING_MAX_ISSUES', '10'))
    )

    # === 터미널 통합 설정 ===
    terminal_capture_enabled: bool = field(
        default_factory=lambda: os.getenv('UPBIT_TERMINAL_CAPTURE', 'true').lower() == 'true'
    )
    terminal_capture_path: str = field(
        default_factory=lambda: os.getenv('UPBIT_TERMINAL_CAPTURE_PATH', 'logs/terminal_capture.log')
    )
    terminal_buffer_size: int = field(
        default_factory=lambda: int(os.getenv('UPBIT_TERMINAL_BUFFER_SIZE', '1000'))
    )
    terminal_sync_interval: int = field(
        default_factory=lambda: int(os.getenv('UPBIT_TERMINAL_SYNC_INTERVAL', '1'))
    )

    # === 자동 진단 대시보드 설정 ===
    dashboard_enabled: bool = field(
        default_factory=lambda: os.getenv('UPBIT_AUTO_DIAGNOSIS', 'true').lower() == 'true'
    )
    dashboard_path: str = field(
        default_factory=lambda: os.getenv('UPBIT_DASHBOARD_PATH', 'logs/llm_agent_dashboard.json')
    )
    dashboard_update_interval: int = field(
        default_factory=lambda: int(os.getenv('UPBIT_DASHBOARD_UPDATE_INTERVAL', '5'))
    )
    auto_recommendations: bool = field(
        default_factory=lambda: os.getenv('UPBIT_AUTO_RECOMMENDATIONS', 'true').lower() == 'true'
    )
    diagnosis_depth: int = field(
        default_factory=lambda: int(os.getenv('UPBIT_DIAGNOSIS_DEPTH', '3'))
    )

    # === 강화된 LLM 보고서 설정 ===
    enhanced_reports_enabled: bool = field(
        default_factory=lambda: os.getenv('UPBIT_ENHANCED_REPORTS', 'true').lower() == 'true'
    )
    enhanced_reports_path: str = field(
        default_factory=lambda: os.getenv('UPBIT_ENHANCED_REPORTS_PATH', 'logs/enhanced_llm_reports.log')
    )

    # === 성능 최적화 설정 ===
    async_processing: bool = field(
        default_factory=lambda: os.getenv('UPBIT_ASYNC_LOGGING', 'true').lower() == 'true'
    )
    batch_size: int = field(
        default_factory=lambda: int(os.getenv('UPBIT_BATCH_SIZE', '50'))
    )
    memory_threshold_mb: int = field(
        default_factory=lambda: int(os.getenv('UPBIT_MEMORY_THRESHOLD', '200'))
    )
    performance_monitoring: bool = field(
        default_factory=lambda: os.getenv('UPBIT_PERFORMANCE_MONITORING', 'true').lower() == 'true'
    )
    performance_metrics_path: str = field(
        default_factory=lambda: os.getenv('UPBIT_PERFORMANCE_METRICS_PATH', 'logs/performance_metrics.json')
    )

    # === 기능 제어 설정 ===
    component_focus: Optional[str] = field(
        default_factory=lambda: os.getenv('UPBIT_COMPONENT_FOCUS')
    )
    feature_development_mode: bool = field(
        default_factory=lambda: os.getenv('UPBIT_FEATURE_DEV_MODE', 'false').lower() == 'true'
    )

    @classmethod
    def from_environment(cls) -> 'EnhancedLoggingConfig':
        """
        환경변수에서 강화된 로깅 설정 로드

        Returns:
            EnhancedLoggingConfig: 환경변수 기반 설정 인스턴스
        """
        # 기존 LoggingConfig의 from_environment() 로직 재사용
        base_config = LoggingConfig.from_environment()

        # EnhancedLoggingConfig 인스턴스 생성 (dataclass는 자동으로 환경변수 읽기)
        enhanced_config = cls()

        # 기존 설정 복사
        for field_name in base_config.__dataclass_fields__:
            if hasattr(enhanced_config, field_name):
                setattr(enhanced_config, field_name, getattr(base_config, field_name))

        return enhanced_config

    def validate_config(self) -> List[str]:
        """
        설정 검증 및 경고 메시지 반환

        Returns:
            List[str]: 검증 경고 메시지 목록
        """
        warnings = []

        # 브리핑 시스템 검증
        if self.briefing_enabled and not self.terminal_capture_enabled:
            warnings.append("⚠️ 브리핑 시스템에는 터미널 캡처가 권장됩니다")

        # 성능 설정 검증
        if self.async_processing and self.batch_size < 10:
            warnings.append("⚠️ 비동기 처리 시 배치 크기는 10 이상 권장됩니다")

        # 메모리 임계값 검증
        if self.memory_threshold_mb < 100:
            warnings.append("⚠️ 메모리 임계값이 너무 낮습니다 (최소 100MB 권장)")

        # 업데이트 간격 검증
        if self.briefing_update_interval < 1:
            warnings.append("⚠️ 브리핑 업데이트 간격은 최소 1초 이상이어야 합니다")

        # 파일 경로 검증
        for path_attr in ['briefing_path', 'dashboard_path', 'terminal_capture_path']:
            path_value = getattr(self, path_attr)
            if path_value:
                try:
                    Path(path_value).parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    warnings.append(f"⚠️ {path_attr} 경로 생성 실패: {e}")

        return warnings

    def get_feature_summary(self) -> Dict[str, bool]:
        """
        활성화된 기능 요약 반환

        Returns:
            Dict[str, bool]: 기능별 활성화 상태
        """
        return {
            "LLM 브리핑 시스템": self.briefing_enabled,
            "터미널 캡처": self.terminal_capture_enabled,
            "자동 진단 대시보드": self.dashboard_enabled,
            "강화된 LLM 보고서": self.enhanced_reports_enabled,
            "비동기 처리": self.async_processing,
            "성능 모니터링": self.performance_monitoring,
            "기능 개발 모드": self.feature_development_mode
        }

    def get_environment_summary(self) -> str:
        """
        현재 환경변수 설정 요약 문자열 생성

        Returns:
            str: 환경변수 설정 요약
        """
        env_vars = [
            f"UPBIT_LLM_BRIEFING_ENABLED={self.briefing_enabled}",
            f"UPBIT_TERMINAL_CAPTURE={self.terminal_capture_enabled}",
            f"UPBIT_AUTO_DIAGNOSIS={self.dashboard_enabled}",
            f"UPBIT_ASYNC_LOGGING={self.async_processing}",
            f"UPBIT_BRIEFING_UPDATE_INTERVAL={self.briefing_update_interval}",
            f"UPBIT_MEMORY_THRESHOLD={self.memory_threshold_mb}"
        ]
        return "\n".join(env_vars)


def validate_enhanced_config(config: EnhancedLoggingConfig) -> List[str]:
    """
    강화된 로깅 설정 검증 및 경고 메시지 반환

    Args:
        config: 검증할 설정 인스턴스

    Returns:
        List[str]: 검증 경고 메시지 목록
    """
    return config.validate_config()


def create_enhanced_logging_config() -> EnhancedLoggingConfig:
    """
    환경변수 기반 강화된 로깅 설정 생성

    Returns:
        EnhancedLoggingConfig: 설정 인스턴스
    """
    config = EnhancedLoggingConfig.from_environment()

    # 설정 검증
    warnings = validate_enhanced_config(config)
    if warnings:
        # 기존 로깅 시스템을 통해 경고 출력
        import logging
        logger = logging.getLogger("EnhancedLoggingConfig")
        for warning in warnings:
            logger.warning(warning)

    return config


# 편의 함수들
def get_enhanced_logging_config() -> EnhancedLoggingConfig:
    """강화된 로깅 설정 인스턴스 반환"""
    return create_enhanced_logging_config()


def is_llm_briefing_enabled() -> bool:
    """LLM 브리핑 시스템 활성화 여부 확인"""
    return os.getenv('UPBIT_LLM_BRIEFING_ENABLED', 'true').lower() == 'true'


def is_terminal_capture_enabled() -> bool:
    """터미널 캡처 시스템 활성화 여부 확인"""
    return os.getenv('UPBIT_TERMINAL_CAPTURE', 'true').lower() == 'true'


def is_auto_diagnosis_enabled() -> bool:
    """자동 진단 시스템 활성화 여부 확인"""
    return os.getenv('UPBIT_AUTO_DIAGNOSIS', 'true').lower() == 'true'
