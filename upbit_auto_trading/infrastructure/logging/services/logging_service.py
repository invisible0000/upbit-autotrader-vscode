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
from logging.handlers import RotatingFileHandler

# Infrastructure Layer Interfaces
from upbit_auto_trading.infrastructure.logging.interfaces.logging_interface import (
    ILoggingService, LogContext, LogScope
)

# 새로운 설정 파일 관리자
from upbit_auto_trading.infrastructure.logging.config.logging_config_manager import LoggingConfigManager

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

        # 🆕 설정 파일 관리자 초기화
        self._config_manager = LoggingConfigManager()

        # 변경 핸들러 등록
        self._config_manager.add_change_handler(self._on_config_changed)        # 🆕 설정 파일에서 컨텍스트 및 스코프 읽기 (환경변수 대신)
        logging_config = self._config_manager.get_logging_config()
        self._current_context = self._get_context_from_config(logging_config)
        self._current_scope = self._get_scope_from_config(logging_config)
        self._component_focus = logging_config.get('component_focus', '')

        # Feature Development 컨텍스트
        self._feature_context_stack = []

        # 🆕 환경변수 모니터링 제거 (더 이상 필요 없음)
        # 대신 설정 파일 변경 모니터링 사용

        # 핵심 서비스 초기화
        self._initialize_core_service()

        # Domain Events 로깅 핸들러 등록
        self._setup_domain_log_handler()

        print("🔧 Infrastructure 로깅 시스템 - 설정 파일 기반으로 초기화 완료!")
        self._print_current_config()

    def _get_context_from_config(self, config: Dict[str, Any]) -> LogContext:
        """설정 파일에서 로그 컨텍스트 읽기"""
        context_str = config.get('context', 'development').lower()
        try:
            return LogContext(context_str)
        except ValueError:
            return LogContext.DEVELOPMENT

    def _get_scope_from_config(self, config: Dict[str, Any]) -> LogScope:
        """설정 파일에서 로그 스코프 읽기"""
        scope_str = config.get('scope', 'normal').lower()
        try:
            return LogScope(scope_str)
        except ValueError:
            return LogScope.NORMAL

    def _on_config_changed(self, new_config: Dict[str, Any]) -> None:
        """설정 파일 변경 시 콜백 - 완전한 즉시 반영"""
        try:
            logging_config = new_config.get('logging', {})

            # 이전 설정 백업
            old_context = self._current_context
            old_scope = self._current_scope
            old_focus = self._component_focus

            # 새 설정 적용
            self._current_context = self._get_context_from_config(logging_config)
            self._current_scope = self._get_scope_from_config(logging_config)
            self._component_focus = logging_config.get('component_focus', '')

            # 🆕 실제 로깅 시스템 설정 즉시 반영
            self._apply_immediate_logging_changes(logging_config)

            # 🆕 모든 로거 업데이트 (컴포넌트 포커스 포함)
            self._update_all_loggers()

            # 변경 사항 출력
            changes = []
            if old_context != self._current_context:
                changes.append(f"CONTEXT: '{old_context.value}' → '{self._current_context.value}'")
            if old_scope != self._current_scope:
                changes.append(f"SCOPE: '{old_scope.value}' → '{self._current_scope.value}'")
            if old_focus != self._component_focus:
                changes.append(f"FOCUS: '{old_focus}' → '{self._component_focus}'")

            if changes:
                print("🔧 Infrastructure 로깅 설정 실시간 적용:")
                for change in changes:
                    print(f"  {change}")
                print(f"✅ 로깅 설정 변경 적용 완료: {len(changes)}개 변경사항")

        except Exception as e:
            print(f"❌ 설정 변경 적용 실패: {e}")
            import traceback
            traceback.print_exc()

    def _apply_immediate_logging_changes(self, logging_config: Dict[str, Any]) -> None:
        """로깅 설정을 즉시 반영"""
        try:
            with self._lock:
                # 1. 로그 레벨 즉시 변경
                new_level = logging_config.get('level', 'INFO').upper()
                log_level = getattr(logging, new_level, logging.INFO)

                # 모든 기존 로거의 레벨 업데이트
                for logger_name, logger in self._loggers.items():
                    logger.setLevel(log_level)

                # 2. 콘솔 핸들러 즉시 제어 (오토 모드 지원)
                console_output_setting = logging_config.get('console_output', 'false')
                console_enabled = self._resolve_console_output_auto(console_output_setting)
                self._update_console_handlers(console_enabled)

                # 3. 파일 로깅 설정 즉시 반영
                file_config = logging_config.get('file_logging', {})
                if file_config.get('enabled', True):
                    file_level = file_config.get('level', 'DEBUG').upper()
                    file_log_level = getattr(logging, file_level, logging.DEBUG)
                    self._update_file_handlers(file_log_level)

                print(f"🔧 로깅 레벨 변경: {new_level}")
                console_display = f"{'활성화' if console_enabled else '비활성화'}"
                if console_output_setting == 'auto':
                    current_profile = self._config_manager.get_current_profile()
                    console_display += f" (오토: {current_profile} 프로파일)"
                print(f"🔧 콘솔 출력: {console_display}")
                print(f"🔧 파일 로깅 레벨: {file_config.get('level', 'DEBUG')}")

        except Exception as e:
            print(f"❌ 로깅 설정 즉시 반영 실패: {e}")

    def _resolve_console_output_auto(self, console_setting: Any) -> bool:
        """콘솔 출력 오토 모드 해석

        Args:
            console_setting: 'auto', 'true', 'false', True, False

        Returns:
            bool: 실제 콘솔 출력 활성화 여부
        """
        setting_str = str(console_setting).lower()

        if setting_str == 'auto':
            # 🔧 단순한 오토 모드: 개발환경에서는 활성화 (context 의존성 제거)
            # 향후 프로파일 시스템 완성시 프로파일 기반으로 변경 예정
            current_profile = self._config_manager.get_current_profile()
            if current_profile == 'production':
                return False  # 프로덕션 프로파일: 콘솔 출력 비활성화
            else:
                return True   # 기타 프로파일: 콘솔 출력 활성화
        elif setting_str in ['true', '1', 'on']:
            return True
        else:
            return False

    def _update_console_handlers(self, enabled: bool) -> None:
        """콘솔 핸들러 즉시 업데이트"""
        try:
            with self._lock:
                for logger_name, logger in self._loggers.items():
                    # 기존 콘솔 핸들러 모두 제거
                    handlers_to_remove = [
                        h for h in logger.handlers
                        if isinstance(h, logging.StreamHandler) and h.stream == sys.stdout
                    ]
                    for handler in handlers_to_remove:
                        logger.removeHandler(handler)
                        handler.close()

                    # 새로운 콘솔 핸들러 추가 (활성화된 경우만)
                    if enabled:
                        console_handler = logging.StreamHandler(sys.stdout)
                        console_handler.setFormatter(self._formatters.get('console'))
                        console_handler.setLevel(self._get_console_log_level())
                        logger.addHandler(console_handler)

                # 전역 핸들러 상태도 업데이트
                if enabled and 'console' not in self._handlers:
                    console_handler = logging.StreamHandler(sys.stdout)
                    console_handler.setFormatter(self._formatters.get('console'))
                    console_handler.setLevel(self._get_console_log_level())
                    self._handlers['console'] = console_handler
                elif not enabled and 'console' in self._handlers:
                    self._handlers['console'].close()
                    del self._handlers['console']

        except Exception as e:
            print(f"❌ 콘솔 핸들러 업데이트 실패: {e}")

    def _update_file_handlers(self, file_level: int) -> None:
        """파일 핸들러 레벨 즉시 업데이트"""
        try:
            for logger_name, logger in self._loggers.items():
                for handler in logger.handlers:
                    if isinstance(handler, (logging.FileHandler, RotatingFileHandler)):
                        handler.setLevel(file_level)
        except Exception as e:
            print(f"❌ 파일 핸들러 업데이트 실패: {e}")

    def _print_current_config(self) -> None:
        """현재 설정 상태 출력"""
        try:
            config = self._config_manager.get_all_config()
            logging_config = config.get('logging', {})

            print("============================================================")
            print("🔧 Infrastructure 로깅 시스템 - 현재 설정 파일 상태")
            print("============================================================")

            level = logging_config.get('level', 'INFO')
            console = logging_config.get('console_output', False)
            scope = logging_config.get('scope', 'normal')
            context = logging_config.get('context', 'development')
            focus = logging_config.get('component_focus', '')

            print(f"🔹 LOG_LEVEL: {level}")
            print(f"🔹 CONSOLE_OUTPUT: {console}")
            print(f"🔹 LOG_SCOPE: {scope}")
            print(f"🔹 LOG_CONTEXT: {context}")
            print(f"🔹 COMPONENT_FOCUS: {focus or '(전체)'}")

            # 프로파일 정보
            profile = self._config_manager.get_current_profile()
            print(f"🔹 CURRENT_PROFILE: {profile}")

            print("============================================================")

        except Exception as e:
            print(f"❌ 설정 상태 출력 실패: {e}")

    def _setup_domain_log_handler(self) -> None:
        """Domain Layer 로그 이벤트 핸들러 설정"""
        try:
            from upbit_auto_trading.domain.logging import DomainLogEvent
            from upbit_auto_trading.domain.events import get_domain_event_publisher

            def handle_domain_log_event(event: DomainLogEvent):
                """Domain 로그 이벤트를 Infrastructure 로깅 시스템으로 전달"""
                try:
                    logger = self.get_logger(event.component_name)

                    # LogLevel enum을 logging 레벨로 변환
                    level_mapping = {
                        'DEBUG': 10,    # logging.DEBUG
                        'INFO': 20,     # logging.INFO
                        'WARNING': 30,  # logging.WARNING
                        'ERROR': 40,    # logging.ERROR
                        'CRITICAL': 50  # logging.CRITICAL
                    }

                    level = level_mapping.get(event.log_level.value, 20)
                    logger.log(level, event.message)

                except Exception as e:
                    # 로깅 시스템 오류가 발생해도 Domain 이벤트 처리는 계속 진행
                    print(f"Domain log handler error: {e}")

            # 이벤트 핸들러 등록
            publisher = get_domain_event_publisher()
            publisher.subscribe(DomainLogEvent, handle_domain_log_event)

        except Exception as e:
            # Domain Events 시스템이 없어도 기본 로깅은 계속 동작
            print(f"Domain log handler setup failed: {e}")

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
        """로그 핸들러 초기화 (설정 파일 기반) - RotatingFileHandler 포함"""
        try:
            # 🆕 설정 파일에서 로깅 설정 읽기
            logging_config = self._config_manager.get_logging_config()
            file_config = self._config_manager.get_file_logging_config()

            # 파일 로깅이 활성화된 경우에만 파일 핸들러 생성
            if file_config.get('enabled', True):
                # 🆕 설정 파일에서 경로 읽기 (폴더 경로)
                log_folder = file_config.get('path', 'logs')
                log_dir = Path(log_folder)

                # 디렉토리 생성
                log_dir.mkdir(parents=True, exist_ok=True)

                # 🆕 RotatingFileHandler로 메인 로그 파일 핸들러 생성
                main_log_path = log_dir / "application.log"
                max_size_mb = file_config.get('max_size_mb', 10)
                backup_count = file_config.get('backup_count', 5)
                max_bytes = max_size_mb * 1024 * 1024  # MB를 bytes로 변환

                # RotatingFileHandler 사용 (자동 백업 시스템)
                main_handler = RotatingFileHandler(
                    main_log_path,
                    mode='a',
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                main_handler.setFormatter(self._formatters['default'])

                # 🆕 설정 파일에서 파일 로그 레벨 읽기
                file_level_str = file_config.get('level', 'DEBUG')
                file_level = getattr(logging, file_level_str.upper(), logging.DEBUG)
                main_handler.setLevel(file_level)
                self._handlers['main'] = main_handler

                # 세션 로그 파일 핸들러 (일반 FileHandler - 세션별로 생성)
                session_filename = self._generate_session_filename()
                session_log_path = log_dir / session_filename
                session_handler = logging.FileHandler(session_log_path, mode='a', encoding='utf-8')
                session_handler.setFormatter(self._formatters['default'])
                session_handler.setLevel(file_level)
                self._handlers['session'] = session_handler

                print(f"✅ 파일 로깅 활성화:")
                print(f"   📁 로그 폴더: {log_dir}")
                print(f"   📄 메인 로그: {main_log_path} (최대: {max_size_mb}MB, 백업: {backup_count}개)")
                print(f"   📄 세션 로그: {session_log_path}")
                print(f"   📊 로그 레벨: {file_level_str}")

                # 기존 백업 파일 정리 (프로그램 시작 시)
                self._cleanup_old_backups(log_dir, backup_count)

            # 🆕 설정 파일에서 콘솔 출력 설정 읽기 (오토 모드 지원)
            console_output_setting = logging_config.get('console_output', False)
            console_output_enabled = self._resolve_console_output_auto(console_output_setting)

            if console_output_enabled:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(self._formatters['console'])
                console_handler.setLevel(self._get_console_log_level())
                self._handlers['console'] = console_handler

                auto_info = " (오토모드)" if console_output_setting == 'auto' else ""
                print(f"✅ 콘솔 핸들러 활성화{auto_info} - 레벨: {console_handler.level}")
            else:
                auto_info = " (오토모드)" if console_output_setting == 'auto' else ""
                print(f"ℹ️ 콘솔 출력 비활성화{auto_info} (설정 파일 기준)")

        except Exception as e:
            print(f"❌ 핸들러 초기화 실패: {e}")
            self._initialize_fallback_logging()

    def _cleanup_old_backups(self, log_dir: Path, max_backup_count: int) -> None:
        """오래된 백업 파일 정리

        application.log.1, application.log.2, ... 형태의 백업 파일에서
        max_backup_count를 초과하는 오래된 파일들을 삭제

        Args:
            log_dir: 로그 디렉토리
            max_backup_count: 최대 백업 파일 개수
        """
        try:
            # application.log.* 패턴의 백업 파일 찾기
            backup_files = list(log_dir.glob("application.log.*"))

            if len(backup_files) <= max_backup_count:
                return  # 정리할 필요 없음

            # 백업 번호 기준으로 정렬 (application.log.1, .2, .3, ...)
            def get_backup_number(file_path: Path) -> int:
                try:
                    # application.log.5 -> 5
                    return int(file_path.suffix.lstrip('.'))
                except (ValueError, AttributeError):
                    return 0

            backup_files.sort(key=get_backup_number, reverse=True)

            # max_backup_count를 초과하는 파일들 삭제
            files_to_remove = backup_files[max_backup_count:]

            for old_file in files_to_remove:
                try:
                    old_file.unlink()
                    print(f"🗑️ 오래된 백업 파일 삭제: {old_file.name}")
                except OSError as e:
                    print(f"⚠️ 백업 파일 삭제 실패: {old_file.name} - {e}")

            if files_to_remove:
                print(f"✅ 백업 파일 정리 완료: {len(files_to_remove)}개 파일 삭제")

        except Exception as e:
            print(f"⚠️ 백업 파일 정리 중 오류: {e}")

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
        """모든 로거의 설정 업데이트 - 핸들러 포함"""
        for component_name, logger in self._loggers.items():
            # 기존 핸들러 제거
            logger.handlers.clear()

            # 로거 레벨 재설정
            if self._component_focus and component_name != self._component_focus:
                logger.setLevel(logging.WARNING)
            else:
                logger.setLevel(logging.DEBUG)

            # 핸들러 다시 추가 (필터링 적용)
            for handler_name, handler in self._handlers.items():
                if self._should_add_handler(component_name, handler_name):
                    logger.addHandler(handler)

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

    # === 실시간 환경변수 모니터링 시스템 ===

    def _start_env_monitoring(self) -> None:
        """실시간 환경변수 모니터링 시작"""
        try:
            import threading

            # 초기 환경변수 상태 저장
            self._last_env_state = self._get_relevant_env_vars()

            # **시작 시 현재 환경변수 상태 출력 (투명성 확보)**
            self._log_current_env_state()

            # 5초마다 환경변수 변경 체크 (별도 스레드)
            def monitor_loop():
                import time
                while True:
                    try:
                        time.sleep(5)  # 5초 간격
                        self._check_env_changes()
                    except Exception as e:
                        # 에러는 무시하고 계속 모니터링
                        pass

            monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
            monitor_thread.start()

            logger = self.get_logger("LoggingService")
            logger.info("🔍 Infrastructure 환경변수 모니터링 시작")

            # **로그에도 환경변수 상태 상세 기록**
            logger.info("📋 Infrastructure 로깅 시스템 환경변수 시작 상태:")
            for var_name, value in self._last_env_state.items():
                if value:
                    logger.info(f"   • {var_name}: {value} (설정됨)")
                else:
                    default_values = {
                        'UPBIT_CONSOLE_OUTPUT': 'false',
                        'UPBIT_LOG_SCOPE': 'normal',
                        'UPBIT_COMPONENT_FOCUS': '(전체)',
                        'UPBIT_LOG_LEVEL': 'INFO',
                        'UPBIT_LOG_CONTEXT': 'development',
                    }
                    default_val = default_values.get(var_name, '(기본값 없음)')
                    logger.info(f"   • {var_name}: {default_val} (기본값)")
            logger.info("📋 Infrastructure 환경변수 시작 상태 기록 완료")

        except Exception as e:
            logger = self.get_logger("LoggingService")
            logger.error(f"❌ 환경변수 모니터링 시작 실패: {e}")

    def _log_current_env_state(self) -> None:
        """현재 환경변수 상태를 터미널과 로그에 출력 (투명성)"""
        logger = self.get_logger("LoggingService")

        # 기본값 가져오기
        defaults = self._get_env_defaults()

        # 터미널에 명확하게 출력
        print("=" * 60)
        print("🔧 Infrastructure 로깅 시스템 - 현재 환경변수 상태")
        print("=" * 60)

        for var_name, current_value in self._last_env_state.items():
            default_value = defaults.get(var_name, '(정의되지 않음)')

            # 실제 환경 변수에서 다시 확인
            actual_env_value = os.getenv(var_name)

            if actual_env_value is not None and actual_env_value != default_value:
                # 사용자가 설정한 값
                display_value = f"{actual_env_value} ✓ 설정됨"
                logger.info(f"🔹 {var_name}: {actual_env_value} (사용자 설정)")
            else:
                # 기본값 사용
                display_value = f"{default_value} (기본값)"
                logger.info(f"🔹 {var_name}: {default_value} (기본값)")

            print(f"🔹 {var_name}: {display_value}")

        print("=" * 60)
        logger.info("✅ Infrastructure 로깅 환경변수 상태 출력 완료")

        # 추가로 로그에도 상태 기록
        self._log_env_state_to_logs()

    def _get_relevant_env_vars(self) -> dict:
        """로깅 관련 환경변수 수집 - 실제 값 우선, 없으면 기본값"""
        defaults = self._get_env_defaults()

        relevant_vars = {}
        for var_name, default_value in defaults.items():
            # 실제 환경 변수 값을 우선적으로 읽기
            actual_value = os.getenv(var_name)
            if actual_value is not None:
                relevant_vars[var_name] = actual_value
            else:
                relevant_vars[var_name] = default_value

        return relevant_vars

    def _check_env_changes(self) -> None:
        """환경변수 변경 감지 및 즉시 적용"""
        try:
            current_env = self._get_relevant_env_vars()

            # 변경된 환경변수 감지
            changes = {}
            for key, current_value in current_env.items():
                last_value = self._last_env_state.get(key, '')
                if current_value != last_value:
                    changes[key] = {'old': last_value, 'new': current_value}

            if changes:
                self._apply_env_changes(changes)
                self._last_env_state = current_env

        except Exception as e:
            # 환경변수 모니터링 에러는 무시 (서비스 안정성 우선)
            pass

    def _apply_env_changes(self, changes: dict) -> None:
        """환경변수 변경 사항 즉시 로깅 시스템에 적용"""
        logger = self.get_logger("LoggingService")

        # **로그에 환경변수 변경 전체 상황 기록**
        logger.info("🔧 Infrastructure 환경변수 실시간 변경 시작")

        # **터미널에 명확하게 변경 사항 출력**
        print("🔧 Infrastructure 환경변수 실시간 적용:")

        for var_name, change in changes.items():
            old_val, new_val = change['old'], change['new']

            # 터미널과 로그 모두에 출력
            change_msg = f"  {var_name}: '{old_val}' → '{new_val}'"
            print(change_msg)
            logger.info(f"🔄 환경변수 변경 감지: {var_name} = '{new_val}' (이전: '{old_val}')")

            # 즉시 로깅 시스템에 적용
            if var_name == 'UPBIT_LOG_SCOPE':
                self._apply_scope_change(new_val)
                logger.info(f"✅ 로그 스코프 실시간 적용됨: {new_val}")
            elif var_name == 'UPBIT_COMPONENT_FOCUS':
                self._apply_component_focus_change(new_val)
                logger.info(f"✅ 컴포넌트 포커스 실시간 적용됨: {new_val}")
            elif var_name == 'UPBIT_LOG_CONTEXT':
                self._apply_context_change(new_val)
                logger.info(f"✅ 로그 컨텍스트 실시간 적용됨: {new_val}")
            elif var_name == 'UPBIT_CONSOLE_OUTPUT':
                self._apply_console_output_change(new_val)
                logger.info(f"✅ 콘솔 출력 실시간 적용됨: {new_val}")

        success_msg = f"✅ 환경변수 변경 적용 완료: {list(changes.keys())}"
        print(success_msg)
        logger.info(success_msg)

        # **로그에 현재 적용된 환경변수 상태 기록**
        self._log_applied_env_state_to_log_only()

    def _log_applied_env_state_to_log_only(self) -> None:
        """로그에만 현재 환경변수 상태 기록 (터미널 출력 없음)"""
        logger = self.get_logger("LoggingService")
        current_env = self._get_relevant_env_vars()

        logger.info("📋 현재 Infrastructure 환경변수 적용 상태:")
        for var_name, value in current_env.items():
            display_value = value if value else "(기본값 사용 중)"
            logger.info(f"   • {var_name}: {display_value}")
        logger.info("📋 환경변수 상태 기록 완료")

    def _apply_scope_change(self, new_value: str) -> None:
        """로그 스코프 변경 즉시 적용"""
        try:
            new_scope = LogScope(new_value.lower())
            self.set_scope(new_scope)

            logger = self.get_logger("LoggingService")
            logger.info(f"📈 로그 스코프 즉시 변경됨: {new_scope.value}")
        except ValueError:
            pass  # 잘못된 값은 무시

    def _apply_component_focus_change(self, new_value: str) -> None:
        """컴포넌트 포커스 변경 즉시 적용"""
        self._component_focus = new_value if new_value else None

        logger = self.get_logger("LoggingService")
        if new_value:
            logger.info(f"🎯 컴포넌트 포커스 즉시 설정: {new_value}")
        else:
            logger.info("🌐 전체 컴포넌트 로그 즉시 활성화")

    def _apply_context_change(self, new_value: str) -> None:
        """로그 컨텍스트 변경 즉시 적용"""
        try:
            new_context = LogContext(new_value.lower())
            self.set_context(new_context)

            logger = self.get_logger("LoggingService")
            logger.info(f"🌍 로그 컨텍스트 즉시 변경됨: {new_context.value}")
        except ValueError:
            pass  # 잘못된 값은 무시

    def _apply_console_output_change(self, new_value: str) -> None:
        """콘솔 출력 설정 변경 즉시 적용"""
        logger = self.get_logger("LoggingService")
        if new_value.lower() in ['true', '1', 'on']:
            logger.info("📺 콘솔 출력 즉시 활성화됨")
        else:
            logger.info("📴 콘솔 출력 즉시 비활성화됨")

    def _get_env_defaults(self) -> dict:
        """환경변수 기본값 정의 (레거시 환경변수 제거됨)"""
        return {
            'UPBIT_LOG_LEVEL': 'INFO',
            'UPBIT_LOG_SCOPE': 'normal',
            'UPBIT_LOG_CONTEXT': 'development',
            'UPBIT_CONSOLE_OUTPUT': 'false',
            'UPBIT_COMPONENT_FOCUS': ''
        }

    def _log_env_state_to_logs(self) -> None:
        """환경변수 상태를 로그에 기록"""
        logger = self.get_logger("LoggingService")
        defaults = self._get_env_defaults()
        current_env = self._get_relevant_env_vars()

        logger.info("📊 Infrastructure 로깅 환경변수 상태:")
        for var_name, current_value in current_env.items():
            default_value = defaults.get(var_name, '(정의되지 않음)')
            display_value = current_value if current_value else f"{default_value} (기본값)"
            logger.info(f"  🔹 {var_name}: {display_value}")

    def get_current_session_file_path(self) -> Optional[Path]:
        """현재 세션 로그 파일 경로 반환

        Returns:
            Optional[Path]: 현재 세션 로그 파일 경로, 없으면 None
        """
        try:
            # 현재 세션 파일명 생성
            session_filename = self._generate_session_filename()
            session_path = Path("logs") / session_filename

            # 파일이 실제로 존재하는지 확인
            if session_path.exists():
                return session_path

            # 파일이 없으면 logs 디렉토리에서 최신 세션 파일 찾기
            log_dir = Path("logs")
            if not log_dir.exists():
                return None

            session_pattern = f"{self.session_log_prefix}_*.log"
            session_files = list(log_dir.glob(session_pattern))

            if session_files:
                # 최신 파일 반환 (수정 시간 기준)
                session_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                return session_files[0]

            return None

        except Exception:
            return None

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
