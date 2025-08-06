"""
Enhanced Logging Service - 강화된 로깅 서비스
==============================================

기존 SmartLoggingService를 확장하여 LLM 에이전트 지원 기능 추가
완전한 백워드 호환성을 유지하면서 점진적 기능 확장
"""

import threading
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

# 기존 Infrastructure Layer import
from upbit_auto_trading.infrastructure.logging.interfaces.logging_interface import ILoggingService
from upbit_auto_trading.infrastructure.logging.services.smart_logging_service import SmartLoggingService as BaseSmartLoggingService
from upbit_auto_trading.infrastructure.logging.configuration.enhanced_config import EnhancedLoggingConfig

# 새로운 Terminal Integration import
from ..terminal import (
    TerminalCapturer, get_terminal_capturer,
    TerminalOutputParser, create_terminal_output_parser,
    LogSynchronizer, create_log_synchronizer, SyncConfig
)


class EnhancedLoggingService(BaseSmartLoggingService):
    """
    강화된 로깅 서비스

    기존 SmartLoggingService의 모든 기능을 유지하면서
    LLM 에이전트 지원 기능을 추가
    """

    def __init__(self, config: Optional[EnhancedLoggingConfig] = None):
        """Enhanced 로깅 서비스 초기화"""

        # Enhanced Config가 아닌 경우 변환
        if config is None:
            config = EnhancedLoggingConfig.from_environment()
        elif not isinstance(config, EnhancedLoggingConfig):
            # 기존 LoggingConfig를 EnhancedLoggingConfig로 확장
            enhanced_config = EnhancedLoggingConfig.from_environment()
            # 기존 설정 값들 복사
            for field_name, field_value in config.__dict__.items():
                if hasattr(enhanced_config, field_name):
                    setattr(enhanced_config, field_name, field_value)
            config = enhanced_config

        # 기존 SmartLoggingService 초기화
        super().__init__(config)

        self.enhanced_config = config
        self.llm_features_initialized = False

        # LLM 기능 컴포넌트들
        self.terminal_capturer: Optional[TerminalCapturer] = None
        self.output_parser: Optional[TerminalOutputParser] = None
        self.log_synchronizer: Optional[LogSynchronizer] = None

        # 초기화 상태 추적
        self.initialization_status = {
            'base_service': False,
            'terminal_capture': False,
            'output_parser': False,
            'log_synchronizer': False,
            'briefing_service': False
        }

        # 조건부 LLM 기능 초기화
        self._initialize_llm_features()

    def _initialize_llm_features(self) -> None:
        """LLM 지원 기능들을 조건부로 초기화"""
        try:
            self.initialization_status['base_service'] = True

            # 터미널 캡처 기능 초기화
            if self.enhanced_config.terminal_capture_enabled:
                self._initialize_terminal_capture()

            # 브리핑 기능 초기화
            if self.enhanced_config.briefing_enabled:
                self._initialize_briefing_service()

            self.llm_features_initialized = True

            # 초기화 완료 로그
            logger = self.get_logger("EnhancedLoggingService")
            logger.info("🤖 LLM_REPORT: Operation=Enhanced_로깅_초기화, Status=완료, Details=모든 기능 활성화됨")

        except Exception as e:
            logger = self.get_logger("EnhancedLoggingService")
            logger.error(f"❌ LLM 기능 초기화 실패: {e}")
            # 기존 기능은 정상 동작하도록 유지

    def _initialize_terminal_capture(self) -> None:
        """터미널 캡처 시스템 초기화"""
        try:
            # Terminal Capturer 초기화
            self.terminal_capturer = get_terminal_capturer()
            self.initialization_status['terminal_capture'] = True

            # Output Parser 초기화
            self.output_parser = create_terminal_output_parser()
            self.initialization_status['output_parser'] = True

            # Log Synchronizer 초기화
            sync_config = SyncConfig(
                sync_interval=1.0,
                batch_size=50,
                enable_file_output=True,
                llm_log_file=self.enhanced_config.terminal_capture_path,
                auto_cleanup=True
            )

            self.log_synchronizer = create_log_synchronizer(sync_config)
            self.initialization_status['log_synchronizer'] = True

            # 로그 동기화 시작
            if self.log_synchronizer.start():
                logger = self.get_logger("TerminalIntegration")
                logger.info("🤖 LLM_REPORT: Operation=터미널_통합, Status=시작, Details=실시간 캡처 및 동기화 활성화")

        except Exception as e:
            logger = self.get_logger("TerminalIntegration")
            logger.warning(f"⚠️ 터미널 캡처 초기화 실패: {e}")

    def _initialize_briefing_service(self) -> None:
        """브리핑 서비스 초기화 (Phase 2에서 구현 예정)"""
        try:
            # Phase 2에서 구현될 LLMBriefingService 초기화
            # 현재는 준비 상태만 표시
            self.initialization_status['briefing_service'] = True

            logger = self.get_logger("BriefingService")
            logger.info("🤖 LLM_REPORT: Operation=브리핑_서비스, Status=준비, Details=Phase 2에서 구현 예정")

        except Exception as e:
            logger = self.get_logger("BriefingService")
            logger.warning(f"⚠️ 브리핑 서비스 준비 실패: {e}")

    # ==================== 기존 인터페이스 유지 ====================

    def get_logger(self, component_name: str):
        """기존 get_logger 메서드 완전 호환"""
        return super().get_logger(component_name)

    def set_context(self, context):
        """기존 set_context 메서드 완전 호환"""
        return super().set_context(context)

    def feature_development_context(self, feature_name: str):
        """기존 feature_development_context 메서드 완전 호환"""
        return super().feature_development_context(feature_name)

    # ==================== 새로운 LLM 지원 메서드들 ====================

    def get_terminal_output(self, lines: int = 50) -> List[str]:
        """최근 터미널 출력 반환"""
        if self.terminal_capturer:
            return self.terminal_capturer.get_recent_output(lines)
        return []

    def get_parsed_output(self, lines: int = 50) -> List[Any]:
        """파싱된 터미널 출력 반환"""
        if self.output_parser and self.terminal_capturer:
            raw_output = self.terminal_capturer.get_recent_output(lines)
            return self.output_parser.parse_output(raw_output)
        return []

    def get_llm_features_status(self) -> Dict[str, Any]:
        """LLM 기능 상태 반환"""
        return {
            'enhanced_config': {
                'briefing_enabled': self.enhanced_config.briefing_enabled,
                'terminal_capture_enabled': self.enhanced_config.terminal_capture_enabled,
                'briefing_update_interval': self.enhanced_config.briefing_update_interval
            },
            'initialization_status': self.initialization_status,
            'features_initialized': self.llm_features_initialized,
            'components': {
                'terminal_capturer': self.terminal_capturer is not None,
                'output_parser': self.output_parser is not None,
                'log_synchronizer': self.log_synchronizer is not None and self.log_synchronizer.get_sync_state().is_running
            }
        }

    def force_sync_logs(self) -> bool:
        """로그 강제 동기화"""
        if self.log_synchronizer:
            return self.log_synchronizer.force_sync()
        return False

    def get_system_health_summary(self) -> Dict[str, Any]:
        """시스템 상태 요약 (Phase 2에서 확장 예정)"""
        status = self.get_llm_features_status()

        # 기본 상태 분석
        all_initialized = all(status['initialization_status'].values())
        health = "OK" if all_initialized else "LIMITED"

        if not status['enhanced_config']['terminal_capture_enabled']:
            health = "BASIC"

        return {
            'overall_health': health,
            'base_logging': 'OK',
            'llm_features': 'OK' if status['features_initialized'] else 'LIMITED',
            'terminal_integration': 'OK' if status['components']['log_synchronizer'] else 'DISABLED',
            'component_count': len([k for k, v in status['initialization_status'].items() if v]),
            'ready_for_phase2': status['features_initialized']
        }

    def shutdown(self) -> None:
        """서비스 종료 및 정리"""
        try:
            # Log Synchronizer 정리
            if self.log_synchronizer:
                self.log_synchronizer.stop()

            # Terminal Capturer 정리
            if self.terminal_capturer:
                self.terminal_capturer.stop_capture()

            logger = self.get_logger("EnhancedLoggingService")
            logger.info("🤖 LLM_REPORT: Operation=Enhanced_로깅_종료, Status=완료, Details=모든 리소스 정리됨")

        except Exception as e:
            logger = self.get_logger("EnhancedLoggingService")
            logger.error(f"❌ 서비스 종료 중 오류: {e}")
        finally:
            # 기존 서비스 종료
            super().shutdown() if hasattr(super(), 'shutdown') else None


# 전역 인스턴스 관리 (기존 패턴 유지)
_global_enhanced_service: Optional[EnhancedLoggingService] = None
_service_lock = threading.Lock()


def get_enhanced_logging_service(config: Optional[EnhancedLoggingConfig] = None) -> EnhancedLoggingService:
    """전역 Enhanced 로깅 서비스 인스턴스 반환"""
    global _global_enhanced_service

    with _service_lock:
        if _global_enhanced_service is None:
            _global_enhanced_service = EnhancedLoggingService(config)
        return _global_enhanced_service


def create_enhanced_logging_service(config: Optional[EnhancedLoggingConfig] = None) -> EnhancedLoggingService:
    """새로운 Enhanced 로깅 서비스 인스턴스 생성"""
    return EnhancedLoggingService(config)


# 기존 호환성을 위한 alias
def get_logging_service(config=None) -> ILoggingService:
    """기존 get_logging_service 호환성 유지"""
    if config is None or isinstance(config, EnhancedLoggingConfig):
        return get_enhanced_logging_service(config)
    else:
        # 기존 LoggingConfig 전달 시 Enhanced로 변환
        enhanced_config = EnhancedLoggingConfig.from_environment()
        # 기존 설정 복사
        for field_name, field_value in config.__dict__.items():
            if hasattr(enhanced_config, field_name):
                setattr(enhanced_config, field_name, field_value)
        return get_enhanced_logging_service(enhanced_config)
