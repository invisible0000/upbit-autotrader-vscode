"""
로깅 관리 탭 - 간단한 MVP Presenter
==================================

DDD Application Layer - Use Case 구현, Service 계층
무한 루프 방지를 위한 안전한 로깅 관리

주요 책임:
- MVP 패턴 Presenter (비즈니스 로직과 UI 연결)
- 안전한 로깅 시스템 통합
- 환경변수 관리
- 이벤트 처리 및 UI 상태 관리
"""

from PyQt6.QtCore import QTimer
from datetime import datetime
from ..upbit_auto_trading.ui.desktop.screens.settings.logging_management.logging_management_view import LoggingManagementView

# 새로운 간단한 시스템 사용
from upbit_auto_trading.infrastructure.logging.integration.logging_manager import get_logging_manager
from upbit_auto_trading.infrastructure.logging.integration.environment_variable_manager import EnvironmentVariableManager


class LoggingManagementPresenter:
    """로깅 관리 탭 - 안전한 MVP Presenter"""

    def __init__(self, view: LoggingManagementView):
        self.view = view
        self._demo_counter = 0

        # 새로운 간단한 시스템 사용
        self._logging_manager = get_logging_manager()
        self._environment_manager = EnvironmentVariableManager()
        self._is_logging_active = False

        # 임시 설정 저장
        self._pending_settings = {
            'log_level': "",
            'console_output': False,
            'log_scope': "",
            'component_focus': "",
            'log_context': ""  # 🆕 로깅 컨텍스트 추가
        }
        self._has_pending_changes = False

        # 재귀 방지 플래그
        self._refreshing = False
        self._initializing = False

        self._setup_event_handlers()
        self._setup_logging_system()
        self._load_current_environment_variables()  # 🆕 환경 변수 로드

        # 시작 메시지 (직접 UI 호출) - 초기화 확인용
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log("✅ 간단한 MVP Presenter 초기화 완료")
        self.view.append_log(f"🔄 [{timestamp}] 안전한 로깅 시스템 연동 준비")
        self.view.append_console(f"💻 [{timestamp}] Presenter 초기화됨 - 테스트 메시지")

        # 테스트용 콘솔 출력 (stdout으로 출력되어 캡처 테스트)
        print(f"🧪 [{timestamp}] 콘솔 캡처 테스트: Presenter 초기화")
        print(f"📊 [{timestamp}] 시스템 상태: 로깅 관리 활성화")
        print(f"🔗 [{timestamp}] MVP 패턴 연결: View ↔ Presenter")

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

        # 환경변수 변경 감지
        self.view.log_level_combo.currentTextChanged.connect(self._on_log_level_changed)
        self.view.console_output_checkbox.toggled.connect(self._on_console_output_changed)
        self.view.log_scope_combo.currentTextChanged.connect(self._on_log_scope_changed)
        self.view.component_focus_edit.textChanged.connect(self._on_component_focus_changed)
        self.view.log_context_combo.currentTextChanged.connect(self._on_log_context_changed)  # 🆕

    def _setup_logging_system(self) -> None:
        """안전한 로깅 시스템 설정"""
        try:
            # 즉시 상태 표시
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.view.append_log(f"🔧 [{timestamp}] 로깅 시스템 설정 시작...")

            # 로깅 시작 먼저 수행
            start_result = self._logging_manager.start_logging()
            self.view.append_log(f"� [{timestamp}] start_logging() 결과: {start_result}")

            # 핸들러 등록 (로깅 시작 후)
            self._logging_manager.add_log_handler(self._on_log_received)
            self._logging_manager.add_console_handler(self._on_console_received)
            self.view.append_log(f"� [{timestamp}] 핸들러 등록 완료")

            if start_result:
                self._is_logging_active = True
                self.view.append_log("✅ 안전한 로깅 시스템 연동 성공")
                self.view.append_log("📡 실시간 로그 캡처 활성화")
                self.view.append_console("💻 콘솔 출력 캡처 시작")

                # 환경변수 상태 동기화
                self._sync_environment_variables()
            else:
                self.view.append_log("⚠️ 로깅 시스템 연동 실패 - 데모 모드 사용")
                self._setup_demo_system()

        except Exception as e:
            self.view.append_log(f"❌ 로깅 연동 오류: {e}")
            self.view.append_log("🔧 데모 모드로 폴백")
            self._setup_demo_system()

    def _setup_demo_system(self):
        """데모 로그 생성 시스템"""
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
        """설정 적용 버튼 클릭"""
        if not self._has_pending_changes:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.view.append_log(f"[{timestamp}] ℹ️ 변경된 설정이 없습니다")
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] ⚙️ 환경변수 일괄 적용 시작 (영구 저장)...")

        # 환경변수 매니저를 통해 영구 저장으로 실제 적용
        applied_count = 0

        if self._pending_settings['log_level']:
            success = self._environment_manager.set_variable(
                'UPBIT_LOG_LEVEL', self._pending_settings['log_level'], persistent=True
            )
            if success:
                self.view.append_log(f"  ✅ UPBIT_LOG_LEVEL: {self._pending_settings['log_level']} (영구 저장)")
                applied_count += 1

        if self._pending_settings['console_output'] is not None:
            console_value = 'true' if self._pending_settings['console_output'] else 'false'
            success = self._environment_manager.set_variable('UPBIT_CONSOLE_OUTPUT', console_value, persistent=True)
            if success:
                self.view.append_log(f"  ✅ UPBIT_CONSOLE_OUTPUT: {console_value} (영구 저장)")
                applied_count += 1

        if self._pending_settings['log_scope']:
            success = self._environment_manager.set_variable(
                'UPBIT_LOG_SCOPE', self._pending_settings['log_scope'], persistent=True
            )
            if success:
                self.view.append_log(f"  ✅ UPBIT_LOG_SCOPE: {self._pending_settings['log_scope']} (영구 저장)")
                applied_count += 1

        if self._pending_settings['component_focus']:
            success = self._environment_manager.set_variable(
                'UPBIT_COMPONENT_FOCUS', self._pending_settings['component_focus'], persistent=True
            )
            if success:
                self.view.append_log(f"  ✅ UPBIT_COMPONENT_FOCUS: {self._pending_settings['component_focus']} (영구 저장)")
                applied_count += 1

        if self._pending_settings['log_context']:
            success = self._environment_manager.set_variable(
                'UPBIT_LOG_CONTEXT', self._pending_settings['log_context'], persistent=True
            )
            if success:
                self.view.append_log(f"  ✅ UPBIT_LOG_CONTEXT: {self._pending_settings['log_context']} (영구 저장)")
                applied_count += 1

        # 완료 메시지
        self.view.append_log(f"[{timestamp}] 🎯 환경변수 영구 저장 완료: {applied_count}개 설정")
        self.view.append_log(f"[{timestamp}] 🔄 다음 프로그램 시작 시 자동으로 적용됩니다")

        # 대기 중인 설정 초기화
        self._pending_settings = {
            'log_level': "",
            'console_output': False,
            'log_scope': "",
            'component_focus': "",
            'log_context': ""  # 🆕 로깅 컨텍스트 추가
        }
        self._has_pending_changes = False

    def _on_reset_clicked(self):
        """기본값 복원 버튼 클릭"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] 🔄 설정을 기본값으로 복원 중...")

        # UI를 기본값으로 설정
        self.view.set_log_level("INFO")
        self.view.set_console_output_enabled(True)
        self.view.set_log_scope("normal")
        self.view.set_component_focus("")

        # 실제 환경변수도 기본값으로 리셋
        self._reset_environment_variables()

        self.view.append_log("✅ 기본값 복원 완료")

    def _on_clear_clicked(self):
        """로그 지우기 버튼 클릭"""
        self.view.clear_all()
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] 🗑️ 로그가 지워졌습니다")
        self.view.append_log("📋 새로운 로그 세션 시작")
        self.view.append_console(f"[{timestamp}] 💻 콘솔 출력 지워짐")

    def _on_save_clicked(self):
        """로그 저장 버튼 클릭"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] 💾 로그 저장 기능")
        self.view.append_log("📋 향후 파일 저장 기능 구현 예정")

    def _on_auto_scroll_toggled(self, enabled: bool):
        """자동 스크롤 토글"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "활성화" if enabled else "비활성화"
        self.view.append_log(f"[{timestamp}] 📜 자동 스크롤 {status}")

    # ===== 환경변수 변경 감지 =====

    def _on_log_level_changed(self, new_level: str):
        """로그 레벨 변경 감지"""
        if self._initializing:  # 🆕 초기화 중에는 변경 로그 스킵
            return

        self._pending_settings['log_level'] = new_level
        self._has_pending_changes = True

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] 📊 로그 레벨 대기: {new_level} (설정 적용 필요)")

    def _on_console_output_changed(self, enabled: bool):
        """콘솔 출력 변경 감지"""
        if self._initializing:  # 🆕 초기화 중에는 변경 로그 스킵
            return

        self._pending_settings['console_output'] = enabled
        self._has_pending_changes = True

        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "활성화" if enabled else "비활성화"
        self.view.append_log(f"[{timestamp}] 💻 콘솔 출력 대기: {status} (설정 적용 필요)")

    def _on_log_scope_changed(self, new_scope: str):
        """로그 스코프 변경 감지"""
        if self._initializing:  # 🆕 초기화 중에는 변경 로그 스킵
            return

        self._pending_settings['log_scope'] = new_scope
        self._has_pending_changes = True

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] 🔍 로그 스코프 대기: {new_scope} (설정 적용 필요)")

    def _on_component_focus_changed(self, component: str):
        """컴포넌트 집중 변경 감지"""
        if self._initializing:  # 🆕 초기화 중에는 변경 로그 스킵
            return

        self._pending_settings['component_focus'] = component
        self._has_pending_changes = True

        timestamp = datetime.now().strftime("%H:%M:%S")
        display_text = component if component else "(없음)"
        self.view.append_log(f"[{timestamp}] 📝 컴포넌트 집중 대기: {display_text} (설정 적용 필요)")

    def _on_log_context_changed(self, context: str):
        """로깅 컨텍스트 변경 감지"""
        if self._initializing:  # 🆕 초기화 중에는 변경 로그 스킵
            return

        self._pending_settings['log_context'] = context
        self._has_pending_changes = True

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] 🌍 로깅 컨텍스트 대기: {context} (설정 적용 필요)")

    # ===== 로깅 시스템 콜백 =====

    def _on_log_received(self, log_content: str) -> None:
        """로그 파일에서 수신된 로그 처리

        Args:
            log_content: 로그 내용
        """
        if not self._is_logging_active or self._refreshing:
            return

        try:
            # UI에 직접 전달 (무한 루프 방지)
            self.view.append_log(log_content)

        except Exception:
            pass  # 에러 무시

    def _on_console_received(self, console_content: str) -> None:
        """콘솔 출력 수신 처리

        Args:
            console_content: 콘솔 출력 내용
        """
        if not self._is_logging_active or self._refreshing:
            return

        try:
            # 콘솔 출력 영역에 직접 전달
            self.view.append_console(console_content)

        except Exception:
            pass  # 에러 무시

    def _sync_environment_variables(self) -> None:
        """현재 환경변수 상태를 UI와 동기화"""
        try:
            import os

            current_level = os.getenv('UPBIT_LOG_LEVEL', 'INFO')
            current_console = os.getenv('UPBIT_CONSOLE_OUTPUT', 'false').lower() == 'true'
            current_scope = os.getenv('UPBIT_LOG_SCOPE', 'normal')
            current_component = os.getenv('UPBIT_COMPONENT_FOCUS', '')

            self.view.append_log(f"🔄 환경변수: LEVEL={current_level}, CONSOLE={current_console}")
            self.view.append_log(f"🔄 환경변수: SCOPE={current_scope}, FOCUS={current_component}")

        except Exception as e:
            self.view.append_log(f"⚠️ 환경변수 동기화 오류: {e}")

    def _reset_environment_variables(self) -> None:
        """환경변수를 기본값으로 리셋 (영구 저장)"""
        try:
            results = self._environment_manager.reset_all_variables(persistent=True)

            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)

            if success_count == total_count:
                self.view.append_log("✅ 모든 환경변수가 기본값으로 리셋됨 (영구 저장)")
                self.view.append_log("🔄 다음 프로그램 시작 시 기본값으로 적용됩니다")
            else:
                failed_vars = [var for var, success in results.items() if not success]
                self.view.append_log(f"⚠️ 일부 환경변수 리셋 실패: {failed_vars}")

        except Exception as e:
            self.view.append_log(f"❌ 환경변수 리셋 오류: {e}")

    def get_logging_stats(self) -> dict:
        """로깅 시스템 통계 반환

        Returns:
            dict: 로깅 통계 정보
        """
        if self._is_logging_active:
            return self._logging_manager.get_stats()
        else:
            return {
                'is_active': False,
                'mode': 'demo',
                'demo_counter': self._demo_counter
            }

    def refresh(self) -> None:
        """탭 새로고침 처리 - 안전한 갱신"""
        # 재귀 방지
        if self._refreshing:
            return

        try:
            self._refreshing = True
            timestamp = datetime.now().strftime("%H:%M:%S")

            if self._is_logging_active:
                stats = self._logging_manager.get_stats()
                log_count = stats['log_capture']['total_logs']
                console_count = stats['console_capture']['total_captures']

                self.view.append_log(f"📊 [{timestamp}] 실시간 로깅 활성화 - {log_count}개 로그, {console_count}개 콘솔")
                self.view.append_console(f"🔄 [{timestamp}] 탭 새로고침 - 콘솔 캡처 활성화")
            else:
                self.view.append_log(f"🔄 [{timestamp}] 탭 새로고침 - 데모 모드")

        except Exception as e:
            self.view.append_log(f"❌ 새로고침 처리 오류: {e}")
        finally:
            self._refreshing = False

    def _load_current_environment_variables(self) -> None:
        """현재 환경 변수를 읽어서 UI에 표시"""
        try:
            # 환경 변수 읽기
            all_vars = self._environment_manager.get_all_variables()

            timestamp = datetime.now().strftime("%H:%M:%S")
            self.view.append_log(f"[{timestamp}] 🔍 현재 환경 변수 로드 중...")

            # 각 환경 변수를 UI 컨트롤에 설정 (재귀 방지)
            self._initializing = True

            # Log Level 설정
            log_level = all_vars.get('UPBIT_LOG_LEVEL', 'INFO')
            index = self.view.log_level_combo.findText(log_level)
            if index >= 0:
                self.view.log_level_combo.setCurrentIndex(index)
                self.view.append_log(f"  ✅ UPBIT_LOG_LEVEL: {log_level}")

            # Console Output 설정
            console_output = all_vars.get('UPBIT_CONSOLE_OUTPUT', 'false').lower() == 'true'
            self.view.console_output_checkbox.setChecked(console_output)
            self.view.append_log(f"  ✅ UPBIT_CONSOLE_OUTPUT: {console_output}")

            # Log Scope 설정
            log_scope = all_vars.get('UPBIT_LOG_SCOPE', 'normal')
            index = self.view.log_scope_combo.findText(log_scope)
            if index >= 0:
                self.view.log_scope_combo.setCurrentIndex(index)
                self.view.append_log(f"  ✅ UPBIT_LOG_SCOPE: {log_scope}")

            # Component Focus 설정
            component_focus = all_vars.get('UPBIT_COMPONENT_FOCUS', '')
            self.view.component_focus_edit.setText(component_focus)
            if component_focus:
                self.view.append_log(f"  ✅ UPBIT_COMPONENT_FOCUS: {component_focus}")
            else:
                self.view.append_log("  ➖ UPBIT_COMPONENT_FOCUS: (설정되지 않음)")

            # Log Context 설정
            log_context = all_vars.get('UPBIT_LOG_CONTEXT', 'development')
            index = self.view.log_context_combo.findText(log_context)
            if index >= 0:
                self.view.log_context_combo.setCurrentIndex(index)
                self.view.append_log(f"  ✅ UPBIT_LOG_CONTEXT: {log_context}")

            self.view.append_log(f"[{timestamp}] 🎯 환경 변수 로드 완료")

            self._initializing = False

        except Exception as e:
            self.view.append_log(f"❌ 환경 변수 로드 실패: {e}")
            self._initializing = False

    def shutdown(self):
        """Presenter 종료 처리"""
        try:
            if hasattr(self, 'demo_timer') and self.demo_timer:
                self.demo_timer.stop()

            if self._is_logging_active:
                self._logging_manager.stop_logging()
                self._is_logging_active = False

        except Exception:
            pass

    def __del__(self):
        """소멸자: 리소스 정리"""
        try:
            self.shutdown()
        except Exception:
            pass
