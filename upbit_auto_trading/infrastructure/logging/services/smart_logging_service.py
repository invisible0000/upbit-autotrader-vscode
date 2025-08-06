"""
Infrastructure Layer - Smart Logging Service
===========================================

기존 upbit_auto_trading/logging의 핵심 개념을 Infrastructure Layer로 통합한 구현체
Clean Architecture 기반 로깅 서비스의 완전한 구현
"""

import logging
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, ContextManager
from contextlib import contextmanager

from ..interfaces.logging_interface import ILoggingService, LogContext, LogScope, IContextManager
from ..configuration.logging_config import LoggingConfig


class FeatureDevelopmentContext(IContextManager):
    """기능별 개발 모드 컨텍스트 매니저"""

    def __init__(self, feature_name: str, logging_service: 'SmartLoggingService'):
        self.feature_name = feature_name
        self.logging_service = logging_service
        self.original_feature = None

    def __enter__(self):
        """기능 개발 모드 진입"""
        self.original_feature = self.logging_service._config.feature_development
        self.logging_service._config.feature_development = self.feature_name

        # 해당 기능 관련 컴포넌트들의 로그 레벨을 DEBUG로 임시 설정
        for logger_name, logger in self.logging_service._loggers.items():
            if self.feature_name.lower() in logger_name.lower():
                logger.setLevel(logging.DEBUG)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """기능 개발 모드 종료"""
        self.logging_service._config.feature_development = self.original_feature

        # 로그 레벨 원복
        effective_level = self.logging_service._config.get_effective_level()
        for logger in self.logging_service._loggers.values():
            logger.setLevel(effective_level)


class SmartLoggingService(ILoggingService):
    """
    스마트 로깅 서비스 구현체

    기존 upbit_auto_trading/logging의 핵심 기능들:
    - Context-aware filtering
    - Dual file logging
    - Environment variable control
    - Component-based loggers
    """

    def __init__(self, config: Optional[LoggingConfig] = None):
        """
        Args:
            config: 로깅 설정 (None이면 환경변수에서 자동 생성)
        """
        self._config = config or LoggingConfig.from_environment()
        self._loggers: Dict[str, logging.Logger] = {}
        self._handlers_configured = False
        self._lock = threading.RLock()

        # 로깅 시스템 초기화
        self._setup_logging_system()

        # 시작 시 이전 세션 로그 정리
        self._cleanup_previous_sessions()

    def _setup_logging_system(self) -> None:
        """로깅 시스템 전체 설정"""
        with self._lock:
            if self._handlers_configured:
                return

            # 로그 디렉토리 생성
            self._config.create_log_directories()

            # 루트 로거 설정
            root_logger = logging.getLogger()
            root_logger.setLevel(self._config.get_effective_level())

            # 기존 핸들러 제거 (중복 방지)
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            # 파일 핸들러 설정
            if self._config.file_enabled:
                self._setup_file_handlers()

            # 콘솔 핸들러 설정
            if self._config.console_enabled:
                self._setup_console_handler()

            self._handlers_configured = True

    def _setup_file_handlers(self) -> None:
        """파일 핸들러 설정 (듀얼 로깅)"""
        root_logger = logging.getLogger()
        formatter = logging.Formatter(self._config.format)

        # 메인 로그 파일 핸들러 (사람용 - LLM_REPORT 제외)
        main_handler = logging.FileHandler(
            self._config.main_log_path,
            encoding=self._config.encoding
        )
        main_handler.setFormatter(formatter)
        main_handler.setLevel(self._config.get_effective_level())

        # 메인 로그에서는 LLM_REPORT 제외
        main_handler.addFilter(self._create_non_llm_filter())
        root_logger.addHandler(main_handler)

        # LLM 전용 듀얼 로깅 시스템
        if self._config.llm_log_enabled:
            llm_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

            # 1. LLM 통합 로그 핸들러 (upbit_auto_trading_LLM.log)
            llm_main_handler = logging.FileHandler(
                self._config.llm_main_log_path,
                encoding=self._config.encoding
            )
            llm_main_handler.setFormatter(llm_formatter)
            llm_main_handler.setLevel(logging.INFO)
            llm_main_handler.addFilter(self._create_llm_filter())
            root_logger.addHandler(llm_main_handler)

            # 2. LLM 세션별 로그 핸들러 (upbit_auto_trading_LLM_YYYYMMDD_HHMMSS_PIDxxxxx.log)
            llm_session_path = self._get_llm_session_log_path()

            # LLM 세션 로그 파일에 헤더 추가
            self._write_session_log_header(llm_session_path, "LLM")

            llm_session_handler = logging.FileHandler(
                llm_session_path,
                encoding=self._config.encoding
            )
            llm_session_handler.setFormatter(llm_formatter)
            llm_session_handler.setLevel(logging.INFO)
            llm_session_handler.addFilter(self._create_llm_filter())
            root_logger.addHandler(llm_session_handler)

        # 세션별 로그 파일 핸들러
        if self._config.session_log_enabled:
            session_path = self._get_session_log_path()

            # 세션 로그 파일에 헤더 추가
            self._write_session_log_header(session_path, "SESSION")

            session_handler = logging.FileHandler(
                session_path,
                encoding=self._config.encoding
            )
            session_handler.setFormatter(formatter)
            session_handler.setLevel(logging.DEBUG)  # 세션 로그는 항상 상세하게
            root_logger.addHandler(session_handler)

    def _setup_console_handler(self) -> None:
        """콘솔 핸들러 설정"""
        root_logger = logging.getLogger()

        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            "%(levelname)s - %(name)s - %(message)s"  # 콘솔용 간소 포맷
        )
        console_handler.setFormatter(console_formatter)

        # 콘솔 레벨 설정
        console_level = getattr(logging, self._config.console_level.upper(), logging.WARNING)
        console_handler.setLevel(console_level)

        root_logger.addHandler(console_handler)

    def _get_session_log_path(self) -> str:
        """세션별 로그 파일 경로 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pid = os.getpid()

        template = self._config.session_log_path
        return template.format(timestamp=timestamp, pid=pid)

    def _get_llm_log_path(self) -> str:
        """LLM 전용 로그 파일 경로 생성 (세션별) - 호환성을 위한 레거시 메서드"""
        return self._get_llm_session_log_path()

    def _get_llm_session_log_path(self) -> str:
        """LLM 세션별 로그 파일 경로 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pid = os.getpid()

        template = self._config.llm_session_log_path
        return template.format(timestamp=timestamp, pid=pid)

    def _write_session_log_header(self, log_path: str, log_type: str) -> None:
        """세션 로그 파일에 헤더 정보 작성"""
        try:
            # 파일이 존재하지 않을 때만 헤더 작성
            if not os.path.exists(log_path):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                pid = os.getpid()

                # 파일명에서 세션 정보 추출
                filename = os.path.basename(log_path)

                header = f"""================================================================================
SESSION START - {timestamp}
PID: {pid}
세션 파일: {filename}
스마트 로깅 시스템 v3.1 - {log_type} 로그
시스템: UPBIT AUTO TRADING v1.0.0
================================================================================

"""

                # 헤더 작성
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write(header)

        except Exception as e:
            # 헤더 작성 실패해도 로깅 시스템은 계속 동작해야 함
            print(f"⚠️ 세션 로그 헤더 작성 실패 ({log_type}): {e}")

    def _create_llm_filter(self):
        """LLM_REPORT 전용 필터 생성"""
        class LLMReportFilter(logging.Filter):
            def filter(self, record):
                # LLM_REPORT 키워드가 포함된 메시지만 통과
                return '🤖 LLM_REPORT:' in record.getMessage()

        return LLMReportFilter()

    def _create_non_llm_filter(self):
        """LLM_REPORT 제외 필터 생성"""
        class NonLLMReportFilter(logging.Filter):
            def filter(self, record):
                # LLM_REPORT 키워드가 포함되지 않은 메시지만 통과
                return '🤖 LLM_REPORT:' not in record.getMessage()

        return NonLLMReportFilter()

    def _cleanup_previous_sessions(self) -> None:
        """프로그램 시작 시 이전 세션 로그들을 정리"""
        try:
            # 일반 세션 로그 정리
            self._integrate_session_logs()

            # LLM 세션 로그 정리
            self._integrate_llm_session_logs()

            # 오래된 로그 정리 (6개월 이상)
            self._cleanup_old_logs()

            # 대용량 로그 백업 (10MB 이상)
            self._backup_large_logs()

        except Exception as e:
            # 정리 실패해도 로깅 시스템은 동작해야 함
            print(f"⚠️ 로그 정리 중 오류 발생: {e}")

    def _integrate_session_logs(self) -> None:
        """이전 세션 로그들을 메인 로그에 통합"""
        logs_dir = Path("logs")
        if not logs_dir.exists():
            return

        # 세션 로그 파일들 찾기
        session_files = list(logs_dir.glob("upbit_auto_trading_session_*.log"))
        if not session_files:
            return

        main_log_path = Path(self._config.main_log_path)

        # 세션 로그들을 메인 로그 상단에 통합
        for session_file in sorted(session_files, reverse=True):  # 최신 순
            try:
                self._integrate_log_file(session_file, main_log_path, "일반")
                session_file.unlink()  # 통합 후 세션 파일 삭제
            except Exception as e:
                print(f"⚠️ 세션 로그 통합 실패 {session_file.name}: {e}")

    def _integrate_llm_session_logs(self) -> None:
        """이전 LLM 세션 로그들을 LLM 메인 로그에 통합"""
        logs_dir = Path("logs")
        if not logs_dir.exists():
            return

        # LLM 세션 로그 파일들 찾기
        llm_session_files = list(logs_dir.glob("upbit_auto_trading_LLM_*_PID*.log"))
        if not llm_session_files:
            return

        llm_main_log_path = Path(self._config.llm_main_log_path)

        # LLM 세션 로그들을 LLM 메인 로그 상단에 통합
        for llm_session_file in sorted(llm_session_files, reverse=True):  # 최신 순
            try:
                self._integrate_log_file(llm_session_file, llm_main_log_path, "LLM")
                llm_session_file.unlink()  # 통합 후 세션 파일 삭제
            except Exception as e:
                print(f"⚠️ LLM 세션 로그 통합 실패 {llm_session_file.name}: {e}")

    def _integrate_log_file(self, session_file: Path, main_log_path: Path, log_type: str) -> None:
        """세션 로그를 메인 로그에 통합"""
        # 세션 로그 내용 읽기
        with open(session_file, 'r', encoding='utf-8') as f:
            session_content = f.read()

        # 기존 메인 로그 내용 읽기 (있다면)
        existing_content = ""
        if main_log_path.exists():
            with open(main_log_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()

        # 통합된 내용으로 메인 로그 재작성 (세션 로그를 상단에 추가)
        with open(main_log_path, 'w', encoding='utf-8') as f:
            # 헤더 추가
            f.write(f"### UPBIT AUTO TRADING {log_type.upper()} LOG ###\n")
            f.write("UPBIT AUTO TRADING v1.0.0 | 스마트 로깅 시스템 v3.1\n")
            f.write(f"최신 통합: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("듀얼 파일 로깅 + 스마트 필터링 활성화\n\n")

            # 세션 로그 내용 (최신)
            f.write(session_content)
            f.write("\n")

            # 기존 로그 내용 (이전)
            if existing_content:
                f.write(existing_content)

        print(f"✅ {log_type} 로그 통합 완료: {session_file.name} → {main_log_path.name}")

    def _cleanup_old_logs(self) -> None:
        """6개월 이상 된 로그 파일들 삭제"""
        logs_dir = Path("logs")
        if not logs_dir.exists():
            return

        six_months_ago = datetime.now().timestamp() - (6 * 30 * 24 * 3600)  # 6개월

        for log_file in logs_dir.glob("*.log"):
            try:
                if log_file.stat().st_mtime < six_months_ago:
                    log_file.unlink()
                    print(f"🗑️ 오래된 로그 삭제: {log_file.name}")
            except Exception as e:
                print(f"⚠️ 로그 삭제 실패 {log_file.name}: {e}")

    def _backup_large_logs(self) -> None:
        """10MB 이상 로그 파일들을 백업하고 새로 시작"""
        logs_dir = Path("logs")
        if not logs_dir.exists():
            return

        max_size = self._config.max_log_file_size

        for log_file in [Path(self._config.main_log_path), Path(self._config.llm_main_log_path)]:
            if log_file.exists() and log_file.stat().st_size > max_size:
                try:
                    # 백업 파일명 생성
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"{log_file.stem}_backup_{timestamp}{log_file.suffix}"
                    backup_path = log_file.parent / backup_name

                    # 백업 후 원본 파일 새로 시작
                    log_file.rename(backup_path)
                    print(f"💾 대용량 로그 백업: {log_file.name} → {backup_name}")
                except Exception as e:
                    print(f"⚠️ 로그 백업 실패 {log_file.name}: {e}")

    def get_logger(self, component_name: str) -> logging.Logger:
        """컴포넌트별 로거 조회"""
        with self._lock:
            if component_name not in self._loggers:
                logger = logging.getLogger(f"upbit.{component_name}")

                # 컴포넌트 포커스 확인
                if not self._config.should_log_component(component_name):
                    # 포커스 대상이 아니면 높은 레벨로 설정 (로그 출력 최소화)
                    logger.setLevel(logging.ERROR)
                else:
                    logger.setLevel(self._config.get_effective_level())

                self._loggers[component_name] = logger

            return self._loggers[component_name]

    def set_context(self, context: LogContext) -> None:
        """로그 컨텍스트 설정"""
        with self._lock:
            self._config.context = context

            # 환경변수도 업데이트 (다른 컴포넌트와의 호환성)
            os.environ['UPBIT_LOG_CONTEXT'] = context.value

            # 컨텍스트 변경에 따른 레벨 재조정
            self._update_all_logger_levels()

    def set_scope(self, scope: LogScope) -> None:
        """로그 스코프 설정"""
        with self._lock:
            self._config.scope = scope

            # 환경변수도 업데이트
            os.environ['UPBIT_LOG_SCOPE'] = scope.value

            # 스코프 변경에 따른 레벨 재조정
            self._update_all_logger_levels()

    def _update_all_logger_levels(self) -> None:
        """모든 로거의 레벨 재조정"""
        effective_level = self._config.get_effective_level()

        for component_name, logger in self._loggers.items():
            if self._config.should_log_component(component_name):
                logger.setLevel(effective_level)
            else:
                logger.setLevel(logging.ERROR)

    def enable_feature_development(self, feature_name: str) -> ContextManager:
        """특정 기능 개발 모드 활성화"""
        return FeatureDevelopmentContext(feature_name, self)

    def get_current_context(self) -> LogContext:
        """현재 로그 컨텍스트 조회"""
        return self._config.context

    def get_current_scope(self) -> LogScope:
        """현재 로그 스코프 조회"""
        return self._config.scope

    def is_debug_enabled(self, component_name: str) -> bool:
        """특정 컴포넌트의 디버그 로깅 활성화 여부 확인"""
        if component_name not in self._loggers:
            return False

        logger = self._loggers[component_name]
        return logger.isEnabledFor(logging.DEBUG)

    def configure_file_logging(self,
                               main_log_path: str,
                               session_log_path: Optional[str] = None,
                               enable_dual_logging: bool = True) -> None:
        """파일 로깅 설정"""
        with self._lock:
            self._config.main_log_path = main_log_path

            if session_log_path:
                self._config.session_log_path = session_log_path

            self._config.session_log_enabled = enable_dual_logging

            # 핸들러 재설정
            self._handlers_configured = False
            self._setup_logging_system()

    def get_log_statistics(self) -> dict:
        """로깅 통계 정보 조회"""
        stats = {
            'active_loggers': len(self._loggers),
            'current_context': self._config.context.value,
            'current_scope': self._config.scope.value,
            'effective_level': self._config.get_effective_level(),
            'component_focus': self._config.component_focus,
            'feature_development': self._config.feature_development,
            'handlers_configured': self._handlers_configured
        }

        # 파일 크기 정보
        if self._config.file_enabled and Path(self._config.main_log_path).exists():
            stats['main_log_size'] = Path(self._config.main_log_path).stat().st_size

        if self._config.llm_log_enabled:
            # LLM 통합 로그 크기
            if Path(self._config.llm_main_log_path).exists():
                stats['llm_main_log_size'] = Path(self._config.llm_main_log_path).stat().st_size

            # LLM 세션 로그 크기
            llm_session_path = self._get_llm_session_log_path()
            if Path(llm_session_path).exists():
                stats['llm_session_log_size'] = Path(llm_session_path).stat().st_size

        return stats
