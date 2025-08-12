"""
실시간 로깅 관리 탭 - MVP Presenter
=========================================
DDD Application Layer - Use Case 구현, Service 계층
Infrastructure Layer와 Presentation Layer 연결

주요 책임:
- MVP 패턴 Presenter (비즈니스 로직과 UI 연결)
- Infrastructure 로깅 시스템과 통합 (Phase 2)
- 환경변수 관리 및 동기화 (Phase 2)
- 이벤트 처리 및 UI 상태 관리

Phase 1: 기본 MVP + 데모 로그 생성
Phase 2: Infrastructure 통합 + 실시간 로깅
Phase 3: 성능 최적화 + LLM 제거
"""

from PyQt6.QtCore import QTimer
from datetime import datetime
from ..logging_management_view import LoggingManagementView

# Phase 2: Infrastructure Integration
from upbit_auto_trading.infrastructure.logging.integration.log_stream_capture import LogStreamCapture
from upbit_auto_trading.infrastructure.logging.integration.environment_variable_manager import EnvironmentVariableManager
from ..widgets.batched_log_updater import BatchedLogUpdater


class LoggingManagementPresenter:
    """실시간 로깅 관리 탭 - MVP Presenter

    Phase 2: Infrastructure 통합 완료
    - 실제 Infrastructure 로깅 시스템과 연동
    - 실시간 로그 스트림 캡처 및 UI 표시
    - 환경변수 실시간 관리
    """

    def __init__(self, view: LoggingManagementView):
        self.view = view
        self._demo_counter = 0

        # Phase 2: Infrastructure 로깅 시스템과 통합
        self._log_stream_capture = LogStreamCapture(max_buffer_size=1000)
        self._environment_manager = EnvironmentVariableManager()
        self._batch_updater = BatchedLogUpdater(self._batch_log_callback, parent=view)
        self._is_real_logging_active = False

        self._setup_event_handlers()
        self._setup_infrastructure_logging()  # Phase 2: 실제 로깅 시스템

        # 시작 메시지
        self.view.append_log("✅ MVP Presenter 초기화 완료 (Phase 2)")
        self.view.append_log("🔄 Infrastructure 로깅 시스템 연동 준비")

    def _setup_event_handlers(self):
        """이벤트 핸들러 연결 - MVP 패턴"""
        # 환경변수 제어 버튼
        self.view.apply_btn.clicked.connect(self._on_apply_clicked)
        self.view.reset_btn.clicked.connect(self._on_reset_clicked)

        # 로그 뷰어 제어 버튼
        self.view.clear_btn.clicked.connect(self._on_clear_clicked)
        self.view.save_btn.clicked.connect(self._on_save_clicked)

        # 자동 스크롤 토글
        self.view.auto_scroll_checkbox.toggled.connect(self._on_auto_scroll_toggled)

        # 환경변수 변경 감지 (Phase 2에서 실제 연동)
        self.view.log_level_combo.currentTextChanged.connect(self._on_log_level_changed)
        self.view.console_output_checkbox.toggled.connect(self._on_console_output_changed)
        self.view.log_scope_combo.currentTextChanged.connect(self._on_log_scope_changed)
        self.view.component_focus_edit.textChanged.connect(self._on_component_focus_changed)

    def _setup_demo_system(self):
        """Phase 1용 데모 로그 생성 시스템"""
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self._add_demo_log)
        self.demo_timer.start(3000)  # 3초마다 데모 로그 생성

        self.view.append_log("🎯 데모 로그 시스템 활성화 (3초 간격)")

    def _add_demo_log(self):
        """데모용 로그 추가"""
        self._demo_counter += 1
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 다양한 로그 레벨 시뮬레이션
        log_levels = ["INFO", "DEBUG", "WARNING", "ERROR"]
        level = log_levels[self._demo_counter % len(log_levels)]

        # 컴포넌트명 시뮬레이션
        components = ["StrategyService", "UIManager", "DataProvider", "TradingEngine"]
        component = components[self._demo_counter % len(components)]

        demo_log = f"[{timestamp}] [{level:>7}] {component}: Demo log entry #{self._demo_counter:03d}"
        self.view.append_log(demo_log)

        # 10개마다 특별 메시지
        if self._demo_counter % 10 == 0:
            self.view.append_log(f"📊 Demo milestone: {self._demo_counter} logs generated")

    # ===== 이벤트 핸들러 (MVP 패턴) =====

    def _on_apply_clicked(self):
        """설정 적용 버튼 클릭 - Phase 1 기본 처리"""
        # 현재 UI 값들 수집
        log_level = self.view.get_log_level()
        console_enabled = self.view.get_console_output_enabled()
        log_scope = self.view.get_log_scope()
        component_focus = self.view.get_component_focus()

        # Phase 1에서는 로그로만 표시
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] ⚙️ 설정 적용됨:")
        self.view.append_log(f"  └─ UPBIT_LOG_LEVEL: {log_level}")
        self.view.append_log(f"  └─ UPBIT_CONSOLE_OUTPUT: {'true' if console_enabled else 'false'}")
        self.view.append_log(f"  └─ UPBIT_LOG_SCOPE: {log_scope}")
        self.view.append_log(f"  └─ UPBIT_COMPONENT_FOCUS: '{component_focus}'")

        # Phase 2: 실제 환경변수 설정 구현
        self._apply_environment_variables(log_level, console_enabled, log_scope, component_focus)

    def _on_reset_clicked(self):
        """기본값 복원 버튼 클릭"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] 🔄 설정을 기본값으로 복원 중...")

        # UI를 기본값으로 설정
        self.view.set_log_level("INFO")
        self.view.set_console_output_enabled(True)
        self.view.set_log_scope("normal")
        self.view.set_component_focus("")

        # Phase 2: 실제 환경변수도 기본값으로 리셋
        self._reset_environment_variables()

        self.view.append_log("✅ 기본값 복원 완료")

    def _on_clear_clicked(self):
        """로그 지우기 버튼 클릭"""
        self.view.clear_logs()
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] 🗑️ 로그가 지워졌습니다")
        self.view.append_log("📋 새로운 로그 세션 시작")

    def _on_save_clicked(self):
        """로그 저장 버튼 클릭"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] 💾 로그 저장 기능")
        self.view.append_log("📋 Phase 2에서 파일 저장 기능 구현 예정")

        # Phase 2에서 QFileDialog를 사용한 파일 저장 구현

    def _on_auto_scroll_toggled(self, enabled: bool):
        """자동 스크롤 토글"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "활성화" if enabled else "비활성화"
        self.view.append_log(f"[{timestamp}] 📜 자동 스크롤 {status}")

        # Phase 3에서 실제 자동 스크롤 로직 구현

    # ===== 환경변수 변경 감지 =====

    def _on_log_level_changed(self, new_level: str):
        """로그 레벨 변경 감지"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] 🔧 로그 레벨 변경: {new_level}")

        # Phase 2에서 실제 환경변수 동기화 구현

    def _on_console_output_changed(self, enabled: bool):
        """콘솔 출력 변경 감지"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "활성화" if enabled else "비활성화"
        self.view.append_log(f"[{timestamp}] 🖥️ 콘솔 출력 {status}")

        # Phase 2에서 실제 환경변수 동기화 구현

    def _on_log_scope_changed(self, new_scope: str):
        """로그 스코프 변경 감지"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] 📊 로그 스코프 변경: {new_scope}")

        # Phase 2에서 실제 환경변수 동기화 구현

    def _on_component_focus_changed(self, component: str):
        """컴포넌트 집중 변경 감지"""
        if component.strip():
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.view.append_log(f"[{timestamp}] 🎯 컴포넌트 집중: '{component.strip()}'")

        # Phase 2에서 실제 환경변수 동기화 구현

    # ===== 생명주기 관리 =====

    def shutdown(self):
        """Presenter 종료 처리"""
        if hasattr(self, 'demo_timer') and self.demo_timer:
            self.demo_timer.stop()
            self.view.append_log("🛑 데모 로그 시스템 종료")

        # Phase 2에서 Infrastructure 연결 해제 구현

    def get_current_settings(self) -> dict:
        """현재 설정 상태 반환 (디버깅/테스트용)"""
        return {
            'log_level': self.view.get_log_level(),
            'console_output': self.view.get_console_output_enabled(),
            'log_scope': self.view.get_log_scope(),
            'component_focus': self.view.get_component_focus(),
            'demo_counter': self._demo_counter
        }

    # ===== Phase 2: Infrastructure 로깅 통합 =====

    def _setup_infrastructure_logging(self) -> None:
        """Infrastructure 로깅 시스템 설정 및 연동"""
        try:
            # LogStreamCapture 핸들러 등록
            self._log_stream_capture.add_handler(self._on_real_log_received)

            # 실시간 로그 캡처 시작
            if self._log_stream_capture.start_capture():
                self._is_real_logging_active = True
                self.view.append_log("✅ Infrastructure 로깅 시스템 연동 성공")
                self.view.append_log("📡 실시간 로그 스트림 캡처 활성화")

                # 환경변수 상태 동기화
                self._sync_environment_variables()
            else:
                self.view.append_log("⚠️ Infrastructure 로깅 시스템 연동 실패 - 데모 모드 사용")
                self._setup_demo_system()  # 폴백

        except Exception as e:
            self.view.append_log(f"❌ Infrastructure 로깅 연동 오류: {e}")
            self.view.append_log("🔧 데모 모드로 폴백")
            self._setup_demo_system()  # 폴백

    def _on_real_log_received(self, log_messages: str) -> None:
        """실제 Infrastructure 로그 수신 처리

        Args:
            log_messages: 배치로 전달된 로그 메시지들
        """
        if not self._is_real_logging_active:
            return

        try:
            # 여러 로그 메시지를 줄 단위로 분할하여 처리
            log_lines = log_messages.strip().split('\n')

            if hasattr(self, '_batch_updater'):
                # 배치 업데이터를 통해 처리 (성능 최적화)
                self._batch_updater.add_multiple_log_entries(log_lines)
            else:
                # 배치 업데이터가 없는 경우 직접 처리
                for log_line in log_lines:
                    if log_line.strip():
                        self.view.append_log(log_line.strip())

            # 로그 통계 업데이트 (50개마다)
            stats = self._log_stream_capture.get_capture_stats()
            if stats['total_logs'] % 50 == 0:
                stats_message = f"📊 캡처 통계: {stats['total_logs']}개 로그, {stats['duration_seconds']:.1f}초"
                if hasattr(self, '_batch_updater'):
                    self._batch_updater.add_log_entry(stats_message)
                else:
                    self.view.append_log(stats_message)

        except Exception as e:
            print(f"⚠️ 실시간 로그 표시 오류: {e}")

    def _sync_environment_variables(self) -> None:
        """현재 환경변수 상태를 UI와 동기화"""
        import os

        try:
            # 현재 환경변수 읽기
            current_level = os.getenv('UPBIT_LOG_LEVEL', 'INFO')
            current_console = os.getenv('UPBIT_CONSOLE_OUTPUT', 'false').lower() == 'true'
            current_scope = os.getenv('UPBIT_LOG_SCOPE', 'normal')
            current_component = os.getenv('UPBIT_COMPONENT_FOCUS', '')

            # UI 상태 업데이트
            # self.view.update_log_level_display(current_level)  # Phase 2에서 구현 예정
            # self.view.set_console_output_enabled(current_console)  # Phase 2에서 구현 예정
            # self.view.update_environment_variable('UPBIT_LOG_SCOPE', current_scope)  # Phase 2에서 구현 예정
            # self.view.update_environment_variable('UPBIT_COMPONENT_FOCUS', current_component)  # Phase 2에서 구현 예정

            self.view.append_log(f"🔄 환경변수 상태: LEVEL={current_level}, CONSOLE={current_console}")
            self.view.append_log(f"🔄 환경변수 상태: SCOPE={current_scope}, FOCUS={current_component}")

        except Exception as e:
            self.view.append_log(f"⚠️ 환경변수 동기화 오류: {e}")

    def start_real_logging(self) -> bool:
        """실시간 로깅 시작

        Returns:
            bool: 시작 성공 여부
        """
        if self._is_real_logging_active:
            return True

        try:
            self._setup_infrastructure_logging()
            return self._is_real_logging_active
        except Exception as e:
            self.view.append_log(f"❌ 실시간 로깅 시작 실패: {e}")
            return False

    def stop_real_logging(self) -> None:
        """실시간 로깅 중단"""
        if not self._is_real_logging_active:
            return

        try:
            self._log_stream_capture.stop_capture()
            self._is_real_logging_active = False
            self.view.append_log("🛑 실시간 로깅 중단됨")

            # 데모 시스템으로 전환
            self._setup_demo_system()

        except Exception as e:
            self.view.append_log(f"⚠️ 실시간 로깅 중단 오류: {e}")

    def get_logging_stats(self) -> dict:
        """로깅 시스템 통계 반환

        Returns:
            dict: 로깅 통계 정보
        """
        if self._is_real_logging_active:
            return self._log_stream_capture.get_capture_stats()
        else:
            return {
                'is_capturing': False,
                'mode': 'demo',
                'demo_counter': self._demo_counter
            }

    # ===== Phase 2: 실시간 환경변수 제어 =====

    def _apply_environment_variables(
        self, log_level: str, console_enabled: bool, log_scope: str, component_focus: str
    ) -> None:
        """UI 설정을 실제 환경변수에 적용

        Args:
            log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_enabled: 콘솔 출력 활성화 여부
            log_scope: 로그 스코프 (silent, minimal, normal, verbose, debug_all)
            component_focus: 집중할 컴포넌트 이름
        """
        try:
            # 환경변수 설정
            variables_to_set = {
                'UPBIT_LOG_LEVEL': log_level,
                'UPBIT_CONSOLE_OUTPUT': 'true' if console_enabled else 'false',
                'UPBIT_LOG_SCOPE': log_scope,
                'UPBIT_COMPONENT_FOCUS': component_focus
            }

            # 일괄 적용
            results = self._environment_manager.set_multiple_variables(variables_to_set)

            # 결과 확인 및 로깅
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)

            if success_count == total_count:
                self.view.append_log("✅ 모든 환경변수 적용 성공")
                self.view.append_log("🔄 Infrastructure 로깅 시스템에 즉시 반영됨")
            else:
                failed_vars = [var for var, success in results.items() if not success]
                self.view.append_log(f"⚠️ 일부 환경변수 적용 실패: {failed_vars}")

        except Exception as e:
            self.view.append_log(f"❌ 환경변수 적용 오류: {e}")

    def _reset_environment_variables(self) -> None:
        """환경변수를 기본값으로 리셋"""
        try:
            # 기본값으로 리셋
            results = self._environment_manager.reset_all_variables()

            # 결과 확인
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)

            if success_count == total_count:
                self.view.append_log("✅ 모든 환경변수가 기본값으로 리셋됨")
            else:
                failed_vars = [var for var, success in results.items() if not success]
                self.view.append_log(f"⚠️ 일부 환경변수 리셋 실패: {failed_vars}")

        except Exception as e:
            self.view.append_log(f"❌ 환경변수 리셋 오류: {e}")

    def get_current_environment_variables(self) -> dict:
        """현재 환경변수 상태 조회

        Returns:
            dict: 현재 환경변수 값들
        """
        try:
            return self._environment_manager.get_all_variables()
        except Exception as e:
            self.view.append_log(f"❌ 환경변수 조회 오류: {e}")
            return {}

    def update_environment_variable(self, var_name: str, value: str) -> bool:
        """개별 환경변수 업데이트

        Args:
            var_name: 환경변수 이름
            value: 새 값

        Returns:
            bool: 설정 성공 여부
        """
        try:
            success = self._environment_manager.set_variable(var_name, value)
            if success:
                self.view.append_log(f"✅ {var_name}={value} 설정 완료")
            else:
                self.view.append_log(f"❌ {var_name}={value} 설정 실패")
            return success
        except Exception as e:
            self.view.append_log(f"❌ {var_name} 설정 오류: {e}")
            return False

    def get_environment_variable_info(self, var_name: str) -> dict:
        """환경변수 상세 정보 조회

        Args:
            var_name: 환경변수 이름

        Returns:
            dict: 환경변수 정보 (타입, 가능한 값, 현재 값 등)
        """
        try:
            return self._environment_manager.get_variable_info(var_name)
        except Exception as e:
            self.view.append_log(f"❌ {var_name} 정보 조회 오류: {e}")
            return {}

    def rollback_environment_variables(self) -> None:
        """환경변수를 원래 상태로 롤백"""
        try:
            results = self._environment_manager.rollback_to_original()

            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)

            if success_count == total_count:
                self.view.append_log("✅ 환경변수 원상복구 완료")
            else:
                failed_vars = [var for var, success in results.items() if not success]
                self.view.append_log(f"⚠️ 일부 환경변수 롤백 실패: {failed_vars}")

        except Exception as e:
            self.view.append_log(f"❌ 환경변수 롤백 오류: {e}")

    def get_environment_change_history(self, limit: int = 10) -> list:
        """환경변수 변경 이력 조회

        Args:
            limit: 조회할 최대 이력 수

        Returns:
            list: 변경 이력 리스트
        """
        try:
            return self._environment_manager.get_change_history(limit)
        except Exception as e:
            self.view.append_log(f"❌ 변경 이력 조회 오류: {e}")
            return []

    # === 실시간 로그 콜백 메서드들 ===

    def _on_log_received(self, log_record: dict) -> None:
        """개별 로그 메시지 수신 콜백 (배치 처리를 위해 BatchedLogUpdater로 전달)

        Args:
            log_record: 로그 레코드 정보
        """
        try:
            if hasattr(self, '_batch_updater'):
                # 로그 레코드를 포맷팅한 후 배치 업데이터에 추가
                formatted_log = self._format_log_record(log_record)
                self._batch_updater.add_log_entry(formatted_log)
            else:
                # 배치 업데이터가 없는 경우 직접 처리
                formatted_log = self._format_log_record(log_record)
                self.view.append_log(formatted_log)
        except Exception as e:
            print(f"❌ 로그 수신 콜백 오류: {e}")

    def _batch_log_callback(self, log_batch: list) -> None:
        """배치 로그 처리 콜백 (BatchedLogUpdater에서 호출)

        Args:
            log_batch: 배치로 처리할 포맷팅된 로그 메시지 리스트
        """
        try:
            # BatchedLogUpdater에서 이미 포맷팅된 문자열들이 전달됨
            if log_batch:
                self.view.append_log_batch(log_batch)

        except Exception as e:
            print(f"❌ 배치 로그 콜백 오류: {e}")

    def _format_log_record(self, log_record: dict) -> str:
        """로그 레코드를 UI 표시 형식으로 포맷팅

        Args:
            log_record: 로그 레코드 정보

        Returns:
            str: 포맷팅된 로그 메시지
        """
        try:
            timestamp = log_record.get('timestamp', '')
            level = log_record.get('level', 'INFO')
            component = log_record.get('component', 'Unknown')
            message = log_record.get('message', '')

            # 레벨별 이모지 매핑
            level_emoji = {
                'DEBUG': '🔍',
                'INFO': 'ℹ️',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'CRITICAL': '🚨'
            }

            emoji = level_emoji.get(level, 'ℹ️')

            # 포맷팅
            if timestamp:
                formatted = f"{emoji} [{timestamp}] {level:<8} | {component:<15} | {message}"
            else:
                formatted = f"{emoji} {level:<8} | {component:<15} | {message}"

            return formatted

        except Exception as e:
            return f"❌ 로그 포맷팅 오류: {e}"

    def __del__(self):
        """소멸자: 리소스 정리"""
        try:
            if hasattr(self, '_is_real_logging_active') and self._is_real_logging_active:
                self.stop_real_logging()
        except Exception:
            pass
