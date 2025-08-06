"""
Logging Service - 로깅 서비스
============================

Infrastructure Layer의 표준 로깅 서비스
환경별 지능형 필터링, 간단하고 안정적인 로깅 솔루션

핵심 기능:
- Context-aware Filtering: 환경별 지능형 로그 필터링
- Dual File Logging: 메인 로그 + 세션별 로그 관리
- Environment Variable Control: 실시간 로그 레벨 제어
- Component Focus: 특정 컴포넌트 집중 로깅
"""

import os
import sys
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager

# Infrastructure Layer Interfaces
from upbit_auto_trading.infrastructure.logging.interfaces.logging_interface import (
    ILoggingService, LogContext, LogScope
)


class LoggingService(ILoggingService):
    """
    Infrastructure Layer 표준 로깅 서비스

    환경별 지능형 필터링을 지원하는 안정적인 로깅 솔루션
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """로깅 서비스 초기화"""

        # 기본 속성 초기화
        self._loggers = {}
        self._formatters = {}
        self._handlers = {}
        self._lock = threading.RLock()

        # 로그 파일 이름 설정 (기존과 겹치지 않도록)
        self.main_log_name = "application.log"
        self.session_log_prefix = "session"

        # 현재 컨텍스트 및 스코프 (환경변수에서 읽기)
        self._current_context = self._get_context_from_env()
        self._current_scope = self._get_scope_from_env()
        self._component_focus = os.getenv('UPBIT_COMPONENT_FOCUS')

        # Feature Development 컨텍스트
        self._feature_context_stack = []

        # 핵심 서비스 초기화
        self._initialize_core_service()

    def _get_context_from_env(self) -> LogContext:
        """환경변수에서 로그 컨텍스트 읽기"""
        env_context = os.getenv('UPBIT_LOG_CONTEXT', 'development').lower()
        try:
            return LogContext(env_context)
        except ValueError:
            return LogContext.DEVELOPMENT

    def _get_scope_from_env(self) -> LogScope:
        """환경변수에서 로그 스코프 읽기"""
        env_scope = os.getenv('UPBIT_LOG_SCOPE', 'normal').lower()
        try:
            return LogScope(env_scope)
        except ValueError:
            return LogScope.NORMAL

    def _initialize_core_service(self) -> None:
        """핵심 로깅 서비스 초기화"""
        try:
            # 로그 디렉토리 생성
            self._ensure_log_directory()

            # 이전 세션 병합
            self._merge_previous_sessions()

            # 포매터 초기화
            self._initialize_formatters()

            # 핸들러 초기화
            self._initialize_handlers()

            # 세션 시작 로그
            self._write_session_header()

        except Exception as e:
            print(f"❌ 로깅 서비스 초기화 실패: {e}")
            # 최소한의 콘솔 로깅이라도 유지
            self._initialize_fallback_logging()

    def _merge_previous_sessions(self) -> None:
        """이전 세션 로그들을 메인 로그에 병합"""
        try:
            log_dir = Path("logs")
            main_log_path = log_dir / self.main_log_name

            # 이전 세션 파일들 찾기
            session_pattern = f"{self.session_log_prefix}_*.log"
            session_files = list(log_dir.glob(session_pattern))

            if not session_files:
                # 초기화 완료 로그 (간단히)
                logger = self.get_logger("LoggingService")
                logger.info("이전 세션 없음 - 새 로그 시작")
                return

            # 날짜순 정렬
            session_files.sort(key=lambda x: x.stat().st_mtime)

            # 메인 로그 읽기 (기존 내용 보존)
            existing_content = ""
            if main_log_path.exists():
                with open(main_log_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()

            # 새로운 메인 로그 작성 (단순 병합)
            with open(main_log_path, 'w', encoding='utf-8') as main_file:
                # 이전 세션들 병합 (상단에 삽입)
                for session_file in session_files:
                    try:
                        with open(session_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if content.strip():
                                main_file.write(content)
                                main_file.write("\n")
                    except Exception:
                        continue

                # 기존 내용 추가 (그대로)
                if existing_content.strip():
                    main_file.write(existing_content)

            # 이전 세션 파일들 정리
            for session_file in session_files:
                try:
                    session_file.unlink()
                except Exception:
                    continue

            # 병합 완료 로그 (간단히)
            logger = self.get_logger("LoggingService")
            logger.info(f"이전 세션 {len(session_files)}개 병합 완료")

        except Exception:
            # 병합 실패해도 로깅은 계속 진행
            logger = self.get_logger("LoggingService")
            logger.info("세션 병합 실패 - 새 로그 시작")

    def _write_session_header(self) -> None:
        """세션 로그에 헤더 작성"""
        try:
            session_filename = self._generate_session_filename()
            session_path = Path("logs") / session_filename

            with open(session_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"SESSION START - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"PID: {os.getpid()}\n")
                f.write(f"세션 파일: {session_filename}\n")
                f.write("로깅 시스템 - 세션별 로그 파일\n")
                f.write("=" * 80 + "\n\n")

        except Exception:
            pass  # 헤더 실패해도 로깅은 계속

    def _ensure_log_directory(self) -> None:
        """로그 디렉토리 생성"""
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)

    def _initialize_formatters(self) -> None:
        """로그 포매터 초기화"""
        # 기본 포매터
        self._formatters['default'] = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 콘솔 포매터
        self._formatters['console'] = logging.Formatter(
            '%(levelname)s | %(name)s | %(message)s'
        )

    def _initialize_handlers(self) -> None:
        """로그 핸들러 초기화"""
        try:
            # 메인 로그 파일 핸들러
            main_log_path = Path("logs") / self.main_log_name
            main_handler = logging.FileHandler(main_log_path, mode='a', encoding='utf-8')
            main_handler.setFormatter(self._formatters['default'])
            main_handler.setLevel(logging.DEBUG)
            self._handlers['main'] = main_handler

            # 세션 로그 파일 핸들러
            session_filename = self._generate_session_filename()
            session_log_path = Path("logs") / session_filename
            session_handler = logging.FileHandler(session_log_path, mode='a', encoding='utf-8')
            session_handler.setFormatter(self._formatters['default'])
            session_handler.setLevel(logging.DEBUG)
            self._handlers['session'] = session_handler

            # 콘솔 핸들러 (조건부)
            console_output_enabled = os.getenv('UPBIT_CONSOLE_OUTPUT', 'false').lower() == 'true'
            if console_output_enabled:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(self._formatters['console'])
                console_handler.setLevel(self._get_console_log_level())
                self._handlers['console'] = console_handler

        except Exception as e:
            print(f"❌ 핸들러 초기화 실패: {e}")
            self._initialize_fallback_logging()

    def _generate_session_filename(self) -> str:
        """세션별 로그 파일명 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pid = os.getpid()
        return f"{self.session_log_prefix}_{timestamp}_PID{pid}.log"

    def _get_console_log_level(self) -> int:
        """환경변수 기반 콘솔 로그 레벨 결정"""
        scope_levels = {
            LogScope.SILENT: logging.CRITICAL + 1,  # 아무것도 출력하지 않음
            LogScope.MINIMAL: logging.ERROR,
            LogScope.NORMAL: logging.WARNING,
            LogScope.VERBOSE: logging.INFO,
            LogScope.DEBUG_ALL: logging.DEBUG
        }
        return scope_levels.get(self._current_scope, logging.INFO)

    def _initialize_fallback_logging(self) -> None:
        """폴백 로깅 초기화 (최소한의 기능)"""
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = self._formatters.get('console', logging.Formatter('%(levelname)s - %(message)s'))
        console_handler.setFormatter(formatter)
        self._handlers['console'] = console_handler

    # ==================== ILoggingService 인터페이스 구현 ====================

    def get_logger(self, component_name: str) -> logging.Logger:
        """컴포넌트별 로거 반환"""
        with self._lock:
            if component_name not in self._loggers:
                self._loggers[component_name] = self._create_logger(component_name)
            return self._loggers[component_name]

    def _create_logger(self, component_name: str) -> logging.Logger:
        """새로운 로거 생성"""
        logger = logging.getLogger(f"upbit.{component_name}")
        logger.setLevel(logging.DEBUG)

        # 기존 핸들러 제거 (중복 방지)
        logger.handlers.clear()
        logger.propagate = False

        # 컴포넌트 포커스 필터링
        if self._component_focus and component_name != self._component_focus:
            # 포커스 대상이 아닌 경우 레벨 상승
            logger.setLevel(logging.WARNING)

        # 핸들러 추가
        for handler_name, handler in self._handlers.items():
            if self._should_add_handler(component_name, handler_name):
                logger.addHandler(handler)

        return logger

    def _should_add_handler(self, component_name: str, handler_name: str) -> bool:
        """핸들러 추가 여부 결정"""
        # 컴포넌트 포커스가 설정된 경우 필터링
        if self._component_focus and component_name != self._component_focus:
            # 포커스 대상이 아닌 경우 콘솔 출력 제한
            if handler_name == 'console':
                return False

        # 현재 스코프에 따른 필터링
        if self._current_scope == LogScope.SILENT:
            return handler_name in ['main', 'session']  # 파일에만 저장

        return True

    def set_context(self, context: LogContext) -> None:
        """로깅 컨텍스트 설정"""
        with self._lock:
            self._current_context = context
            self._update_all_loggers()

    def set_scope(self, scope: LogScope) -> None:
        """로깅 스코프 설정"""
        with self._lock:
            self._current_scope = scope
            self._update_console_handler_level()
            self._update_all_loggers()

    def enable_feature_development(self, feature_name: str):
        """특정 기능 개발 모드 활성화"""
        return self.feature_development_context(feature_name)

    def get_current_context(self) -> LogContext:
        """현재 로그 컨텍스트 조회"""
        return self._current_context

    def get_current_scope(self) -> LogScope:
        """현재 로그 스코프 조회"""
        return self._current_scope

    def is_debug_enabled(self, component_name: str) -> bool:
        """특정 컴포넌트의 디버그 로깅 활성화 여부 확인"""
        if self._component_focus and component_name != self._component_focus:
            return False
        return self._current_scope in [LogScope.VERBOSE, LogScope.DEBUG_ALL]

    def configure_file_logging(self,
                               main_log_path: str,
                               session_log_path: Optional[str] = None,
                               enable_dual_logging: bool = True) -> None:
        """파일 로깅 설정"""
        # 현재는 기본 구현만 제공
        pass

    def get_log_statistics(self) -> Dict[str, Any]:
        """로깅 통계 정보 조회"""
        return {
            'active_loggers': len(self._loggers),
            'active_handlers': len(self._handlers),
            'current_context': self._current_context.value,
            'current_scope': self._current_scope.value,
            'component_focus': self._component_focus
        }

    def _update_all_loggers(self) -> None:
        """모든 로거의 설정 업데이트"""
        for component_name, logger in self._loggers.items():
            # 로거 레벨 재설정
            if self._component_focus and component_name != self._component_focus:
                logger.setLevel(logging.WARNING)
            else:
                logger.setLevel(logging.DEBUG)

    def _update_console_handler_level(self) -> None:
        """콘솔 핸들러 레벨 업데이트"""
        if 'console' in self._handlers:
            new_level = self._get_console_log_level()
            self._handlers['console'].setLevel(new_level)

    @contextmanager
    def feature_development_context(self, feature_name: str):
        """특정 기능 개발을 위한 컨텍스트"""
        with self._lock:
            # 이전 설정 백업
            prev_scope = self._current_scope
            prev_focus = self._component_focus

            # Feature Development 설정 적용
            self._feature_context_stack.append((feature_name, prev_scope, prev_focus))
            self._current_scope = LogScope.DEBUG_ALL
            self._component_focus = feature_name

            # 설정 업데이트
            self._update_all_loggers()
            self._update_console_handler_level()

            logger = self.get_logger("FeatureDevelopment")
            logger.info(f"🔧 Feature Development 모드 시작: {feature_name}")

        try:
            yield
        finally:
            with self._lock:
                # 이전 설정 복원
                if self._feature_context_stack:
                    _, prev_scope, prev_focus = self._feature_context_stack.pop()
                    self._current_scope = prev_scope
                    self._component_focus = prev_focus

                    # 설정 복원
                    self._update_all_loggers()
                    self._update_console_handler_level()

                    logger = self.get_logger("FeatureDevelopment")
                    logger.info(f"🔧 Feature Development 모드 종료: {feature_name}")

    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 반환"""
        context_str = (self._current_context.value
                       if hasattr(self._current_context, 'value')
                       else str(self._current_context))
        scope_str = (self._current_scope.value
                     if hasattr(self._current_scope, 'value')
                     else str(self._current_scope))

        return {
            'service_type': 'LoggingService',
            'current_context': context_str,
            'current_scope': scope_str,
            'component_focus': self._component_focus,
            'active_loggers': list(self._loggers.keys()),
            'active_handlers': list(self._handlers.keys()),
            'feature_context_stack': [name for name, _, _ in self._feature_context_stack]
        }

    def shutdown(self) -> None:
        """서비스 종료 및 정리"""
        try:
            # 핸들러 정리
            for handler in self._handlers.values():
                handler.close()

            logger = self.get_logger("LoggingService")
            logger.info("🚀 로깅 서비스 종료 완료")

        except Exception as e:
            print(f"❌ 서비스 종료 중 오류: {e}")


# ==================== 전역 인스턴스 관리 ====================

_global_logging_service: Optional[LoggingService] = None
_service_lock = threading.Lock()


def get_logging_service(config: Optional[Dict[str, Any]] = None) -> LoggingService:
    """전역 로깅 서비스 인스턴스 반환"""
    global _global_logging_service

    with _service_lock:
        if _global_logging_service is None:
            _global_logging_service = LoggingService(config)
        return _global_logging_service


def create_logging_service(config: Optional[Dict[str, Any]] = None) -> LoggingService:
    """새로운 로깅 서비스 인스턴스 생성"""
    return LoggingService(config)


def reset_logging_service() -> None:
    """전역 로깅 서비스 리셋 (테스트용)"""
    global _global_logging_service
    with _service_lock:
        if _global_logging_service:
            _global_logging_service.shutdown()
        _global_logging_service = None


# ==================== 편의 함수 ====================

def create_component_logger(component_name: str) -> logging.Logger:
    """컴포넌트별 로거 생성 (편의 함수)"""
    service = get_logging_service()
    return service.get_logger(component_name)


def set_logging_context(context: LogContext) -> None:
    """로깅 컨텍스트 설정 (편의 함수)"""
    service = get_logging_service()
    service.set_context(context)


def set_logging_scope(scope: LogScope) -> None:
    """로깅 스코프 설정 (편의 함수)"""
    service = get_logging_service()
    service.set_scope(scope)


# ==================== 내보내기 ====================

__all__ = [
    'LoggingService',
    'get_logging_service',
    'create_logging_service',
    'reset_logging_service',
    'create_component_logger',
    'set_logging_context',
    'set_logging_scope'
]

__version__ = '2.0.0'
