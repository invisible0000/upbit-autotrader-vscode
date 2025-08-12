"""
Infrastructure Layer - Logging Configuration
===========================================

로깅 시스템 설정 관리
Environment 기반 자동 설정과 수동 설정 지원
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path
import logging

from ..interfaces.logging_interface import LogContext, LogScope

@dataclass
class LoggingConfig:
    """
    로깅 설정 데이터 클래스

    Infrastructure Layer의 설정과 연계하여 일관된 로깅 환경 제공
    """

    # 기본 설정
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 파일 로깅 설정
    file_enabled: bool = True
    main_log_path: str = "logs/upbit_auto_trading.log"
    session_log_enabled: bool = True
    session_log_path: str = "logs/upbit_auto_trading_session_{timestamp}_{pid}.log"

    # LLM 전용 통합 로그 설정 (듀얼 시스템)
    llm_log_enabled: bool = True
    llm_main_log_path: str = "logs/upbit_auto_trading_LLM.log"  # 통합 LLM 로그
    llm_session_log_path: str = "logs/upbit_auto_trading_LLM_{timestamp}_PID{pid}.log"  # 세션별 LLM 로그

    # 콘솔 로깅 설정
    console_enabled: bool = True
    console_level: str = "WARNING"  # 콘솔은 경고 이상만

    # Smart Logging 설정
    context: LogContext = LogContext.DEVELOPMENT
    scope: LogScope = LogScope.NORMAL

    # 성능 설정
    max_log_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    encoding: str = "utf-8"

    # 필터링 설정
    component_focus: Optional[str] = None  # 특정 컴포넌트만 포커스
    feature_development: Optional[str] = None  # 특정 기능 개발 모드

    # LLM 에이전트 관련 설정
    llm_briefing_enabled: bool = True  # LLM 에이전트 브리핑 활성화
    performance_monitoring: bool = False  # 성능 모니터링 활성화
    briefing_update_interval: int = 5  # 브리핑 업데이트 간격 (초)

    @classmethod
    def from_environment(cls) -> 'LoggingConfig':
        """
        환경변수로부터 설정 생성

        환경변수:
            UPBIT_LOG_LEVEL: 로그 레벨
            UPBIT_LOG_CONTEXT: 로그 컨텍스트
            UPBIT_LOG_SCOPE: 로그 스코프
            UPBIT_COMPONENT_FOCUS: 컴포넌트 포커스
            UPBIT_CONSOLE_OUTPUT: 콘솔 출력 활성화

        Returns:
            LoggingConfig: 환경변수 기반 설정
        """
        config = cls()

        # 로그 레벨
        if level := os.getenv('UPBIT_LOG_LEVEL'):
            config.level = level.upper()

        # 로그 컨텍스트
        if context := os.getenv('UPBIT_LOG_CONTEXT'):
            try:
                config.context = LogContext(context.lower())
            except ValueError:
                pass  # 잘못된 값이면 기본값 유지

        # 로그 스코프
        if scope := os.getenv('UPBIT_LOG_SCOPE'):
            try:
                config.scope = LogScope(scope.lower())
            except ValueError:
                pass

        # 컴포넌트 포커스
        config.component_focus = os.getenv('UPBIT_COMPONENT_FOCUS')

        # 콘솔 출력
        if console_output := os.getenv('UPBIT_CONSOLE_OUTPUT'):
            config.console_enabled = console_output.lower() == 'true'

        # 기능 개발 모드
        config.feature_development = os.getenv('UPBIT_FEATURE_DEVELOPMENT')

        # LLM 브리핑 설정
        if llm_briefing := os.getenv('UPBIT_LLM_BRIEFING_ENABLED'):
            config.llm_briefing_enabled = llm_briefing.lower() == 'true'

        # 성능 모니터링 설정
        if perf_monitoring := os.getenv('UPBIT_PERFORMANCE_MONITORING'):
            config.performance_monitoring = perf_monitoring.lower() == 'true'

        # 브리핑 업데이트 간격
        if briefing_interval := os.getenv('UPBIT_BRIEFING_UPDATE_INTERVAL'):
            try:
                config.briefing_update_interval = int(briefing_interval)
            except ValueError:
                pass  # 잘못된 값이면 기본값 유지

        return config

    @classmethod
    def for_development(cls) -> 'LoggingConfig':
        """개발 환경 최적화 설정"""
        return cls(
            level="DEBUG",
            context=LogContext.DEVELOPMENT,
            scope=LogScope.VERBOSE,
            console_enabled=True,
            console_level="DEBUG"
        )

    @classmethod
    def for_testing(cls) -> 'LoggingConfig':
        """테스트 환경 최적화 설정"""
        return cls(
            level="INFO",
            context=LogContext.TESTING,
            scope=LogScope.NORMAL,
            console_enabled=False  # 테스트 시 콘솔 출력 최소화
        )

    @classmethod
    def for_production(cls) -> 'LoggingConfig':
        """프로덕션 환경 최적화 설정"""
        return cls(
            level="WARNING",
            context=LogContext.PRODUCTION,
            scope=LogScope.MINIMAL,
            console_enabled=False,
            session_log_enabled=False  # 프로덕션에서는 세션 로그 비활성화
        )

    def create_log_directories(self) -> None:
        """로그 디렉토리 생성"""
        for log_path in [self.main_log_path, self.session_log_path,
                         self.llm_main_log_path, self.llm_session_log_path]:
            if log_path:
                Path(log_path).parent.mkdir(parents=True, exist_ok=True)

    def get_effective_level(self) -> int:
        """
        효과적인 로그 레벨 계산

        LogScope와 설정된 레벨을 종합하여 실제 사용할 레벨 결정

        Returns:
            int: logging 모듈의 레벨 상수
        """
        base_level = getattr(logging, self.level.upper(), logging.INFO)

        # LogScope에 따른 레벨 조정
        scope_adjustments = {
            LogScope.SILENT: logging.ERROR,
            LogScope.MINIMAL: max(base_level, logging.WARNING),
            LogScope.NORMAL: base_level,
            LogScope.VERBOSE: min(base_level, logging.DEBUG),
            LogScope.DEBUG_ALL: logging.DEBUG
        }

        return scope_adjustments.get(self.scope, base_level)

    def should_log_component(self, component_name: str) -> bool:
        """
        특정 컴포넌트 로깅 여부 판단

        Args:
            component_name: 컴포넌트 이름

        Returns:
            bool: 로깅 허용 여부
        """
        if not self.component_focus:
            return True

        # 대소문자 무시하고 부분 일치 확인
        return self.component_focus.lower() in component_name.lower()

    def is_feature_development_active(self, feature_name: str) -> bool:
        """
        특정 기능 개발 모드 활성화 여부

        Args:
            feature_name: 기능 이름

        Returns:
            bool: 개발 모드 활성화 여부
        """
        if not self.feature_development:
            return False

        return self.feature_development.lower() == feature_name.lower()

    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환"""
        return {
            'level': self.level,
            'format': self.format,
            'file_enabled': self.file_enabled,
            'main_log_path': self.main_log_path,
            'session_log_enabled': self.session_log_enabled,
            'console_enabled': self.console_enabled,
            'context': self.context.value,
            'scope': self.scope.value,
            'component_focus': self.component_focus,
            'feature_development': self.feature_development,
            'llm_briefing_enabled': self.llm_briefing_enabled,
            'performance_monitoring': self.performance_monitoring,
            'briefing_update_interval': self.briefing_update_interval
        }
