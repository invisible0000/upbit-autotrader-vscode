"""
로깅 설정 파일 관리 Presenter
============================

환경변수 대신 설정 파일을 기반으로 하는 안전한 로깅 관리 시스템

주요 기능:
- config/logging_config.yaml 기반 설정 관리
- 실행 중 안전한 설정 변경 (프리징 없음)
- 환경 프로파일 연동
- 즉시 적용 및 영구 저장
"""

from PyQt6.QtCore import QTimer
from datetime import datetime
from typing import Dict, Any
from ..logging_management_view import LoggingManagementView

# 새로운 설정 파일 관리자 사용
# Application Layer - Infrastructure 의존성 격리 (Phase 3 수정)


class LoggingConfigPresenter:
    """로깅 설정 파일 관리 Presenter

    환경변수 방식을 대체하는 안전하고 유연한 설정 시스템
    """

    def __init__(self, view: LoggingManagementView):
        self.view = view
        self._demo_counter = 0

        # 🆕 설정 파일 관리자 사용 (환경변수 매니저 대신)
        self._config_manager = LoggingConfigManager()
        self._config_manager.add_change_handler(self._on_config_changed)

        # 임시 설정 저장
        self._pending_settings = {
            'level': "",
            'console_output': False,
            'scope': "",
            'component_focus': "",
            'context': ""
        }
        self._has_pending_changes = False

        # 재귀 방지 플래그
        self._refreshing = False
        self._initializing = False

        self._setup_event_handlers()
        self._load_current_config()

        # 시작 메시지
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log("✅ 설정 파일 기반 로깅 관리자 초기화 완료")
        self.view.append_log(f"🔄 [{timestamp}] config/logging_config.yaml 기반 시스템 활성화")
        self.view.append_console(f"💻 [{timestamp}] 안전한 설정 변경 시스템 준비 완료")

    def _setup_event_handlers(self):
        """이벤트 핸들러 연결"""
        # 설정 제어 버튼
        self.view.apply_btn.clicked.connect(self._on_apply_clicked)
        self.view.reset_btn.clicked.connect(self._on_reset_clicked)

        # 로그 뷰어 제어 버튼
        self.view.clear_btn.clicked.connect(self._on_clear_clicked)
        self.view.save_btn.clicked.connect(self._on_save_clicked)

        # 자동 스크롤 토글
        self.view.auto_scroll_checkbox.toggled.connect(self._on_auto_scroll_toggled)

        # 설정 변경 감지
        self.view.log_level_combo.currentTextChanged.connect(self._on_log_level_changed)
        self.view.console_output_checkbox.toggled.connect(self._on_console_output_changed)
        self.view.log_scope_combo.currentTextChanged.connect(self._on_log_scope_changed)
        self.view.component_focus_edit.textChanged.connect(self._on_component_focus_changed)
        self.view.log_context_combo.currentTextChanged.connect(self._on_log_context_changed)

        # 🆕 파일 로깅 설정 변경 감지
        self.view.file_logging_checkbox.toggled.connect(self._on_file_logging_changed)
        self.view.file_path_edit.textChanged.connect(self._on_file_path_changed)
        self.view.file_level_combo.currentTextChanged.connect(self._on_file_level_changed)

    def _load_current_config(self) -> None:
        """현재 설정 파일에서 설정 로드"""
        try:
            # 설정 파일에서 읽기
            logging_config = self._config_manager.get_logging_config()

            timestamp = datetime.now().strftime("%H:%M:%S")
            self.view.append_log(f"[{timestamp}] 🔍 설정 파일에서 현재 설정 로드 중...")

            # UI 컨트롤에 설정 (재귀 방지)
            self._initializing = True

            # Log Level 설정
            log_level = logging_config.get('level', 'INFO')
            index = self.view.log_level_combo.findText(log_level)
            if index >= 0:
                self.view.log_level_combo.setCurrentIndex(index)
                self.view.append_log(f"  ✅ LOG_LEVEL: {log_level}")

            # Console Output 설정
            console_output = logging_config.get('console_output', False)
            self.view.console_output_checkbox.setChecked(console_output)
            self.view.append_log(f"  ✅ CONSOLE_OUTPUT: {console_output}")

            # Log Scope 설정
            log_scope = logging_config.get('scope', 'normal')
            index = self.view.log_scope_combo.findText(log_scope)
            if index >= 0:
                self.view.log_scope_combo.setCurrentIndex(index)
                self.view.append_log(f"  ✅ LOG_SCOPE: {log_scope}")

            # Component Focus 설정
            component_focus = logging_config.get('component_focus', '')
            self.view.component_focus_edit.setText(component_focus)
            if component_focus:
                self.view.append_log(f"  ✅ COMPONENT_FOCUS: {component_focus}")
            else:
                self.view.append_log("  ➖ COMPONENT_FOCUS: (전체)")

            # Log Context 설정
            log_context = logging_config.get('context', 'development')
            index = self.view.log_context_combo.findText(log_context)
            if index >= 0:
                self.view.log_context_combo.setCurrentIndex(index)
                self.view.append_log(f"  ✅ LOG_CONTEXT: {log_context}")

            # 프로파일 정보 - ⚠️ 프로파일 기능 정지됨
            # profile = self._config_manager.get_current_profile()
            # self.view.append_log(f"  🌍 CURRENT_PROFILE: {profile}")
            self.view.append_log("  🚫 PROFILE_FEATURE: 기능 정지됨 (config/ 기반으로 재구현 예정)")

            self.view.append_log(f"[{timestamp}] 🎯 설정 파일 로드 완료")

            self._initializing = False

        except Exception as e:
            self.view.append_log(f"❌ 설정 파일 로드 실패: {e}")
            self._initializing = False

    def _on_config_changed(self, new_config: Dict[str, Any]) -> None:
        """설정 파일 변경 시 콜백"""
        if self._initializing or self._refreshing:
            return

        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.view.append_log(f"[{timestamp}] 🔄 설정 파일 변경 감지됨")

            # UI를 새 설정으로 업데이트
            self._load_current_config()

            self.view.append_log(f"[{timestamp}] ✅ 설정 파일 변경 사항 UI에 반영 완료")

        except Exception as e:
            self.view.append_log(f"❌ 설정 변경 처리 실패: {e}")

    # ===== 이벤트 핸들러 =====

    def _on_apply_clicked(self):
        """설정 적용 버튼 클릭"""
        if not self._has_pending_changes:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.view.append_log(f"[{timestamp}] ℹ️ 변경된 설정이 없습니다")
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] ⚙️ 설정 파일 업데이트 시작...")

        try:
            # 변경된 설정 준비
            updates = {}
            applied_count = 0

            if self._pending_settings['level']:
                updates['level'] = self._pending_settings['level']
                applied_count += 1

            if self._pending_settings['console_output'] is not None:
                updates['console_output'] = self._pending_settings['console_output']
                applied_count += 1

            if self._pending_settings['scope']:
                updates['scope'] = self._pending_settings['scope']
                applied_count += 1

            if self._pending_settings['component_focus'] is not None:
                updates['component_focus'] = self._pending_settings['component_focus']
                applied_count += 1

            if self._pending_settings['context']:
                updates['context'] = self._pending_settings['context']
                applied_count += 1

            # 🆕 설정 파일에 안전하게 저장 (프리징 없음)
            success = self._config_manager.update_logging_config(updates, save_to_file=True)

            if success:
                self.view.append_log(f"[{timestamp}] 🎯 설정 파일 업데이트 완료: {applied_count}개 설정")
                self.view.append_log(f"[{timestamp}] 💾 config/logging_config.yaml에 저장됨")
                self.view.append_log(f"[{timestamp}] ⚡ 즉시 적용 완료 (재시작 불필요)")

                # 대기 중인 설정 초기화
                self._pending_settings = {
                    'level': "",
                    'console_output': False,
                    'scope': "",
                    'component_focus': "",
                    'context': ""
                }
                self._has_pending_changes = False
            else:
                self.view.append_log(f"[{timestamp}] ❌ 설정 파일 업데이트 실패")

        except Exception as e:
            self.view.append_log(f"[{timestamp}] ❌ 설정 적용 중 오류: {e}")

    def _on_reset_clicked(self):
        """기본값 복원 버튼 클릭"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] 🔄 설정을 기본값으로 복원 중...")

        try:
            # 🆕 설정 파일을 기본값으로 리셋
            success = self._config_manager.reset_to_defaults(save_to_file=True)

            if success:
                self.view.append_log(f"[{timestamp}] ✅ 설정 파일 기본값 복원 완료")
                self.view.append_log(f"[{timestamp}] 🔄 UI가 자동으로 업데이트됩니다")

                # UI는 설정 변경 콜백으로 자동 업데이트됨
            else:
                self.view.append_log(f"[{timestamp}] ❌ 기본값 복원 실패")

        except Exception as e:
            self.view.append_log(f"[{timestamp}] ❌ 기본값 복원 중 오류: {e}")

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

    # ===== 설정 변경 감지 =====

    def _on_log_level_changed(self, new_level: str):
        """로그 레벨 변경 감지"""
        if self._initializing:
            return

        self._pending_settings['level'] = new_level
        self._has_pending_changes = True

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] 📊 로그 레벨 대기: {new_level} (적용 버튼 클릭 필요)")

    def _on_console_output_changed(self, enabled: bool):
        """콘솔 출력 변경 감지"""
        if self._initializing:
            return

        self._pending_settings['console_output'] = enabled
        self._has_pending_changes = True

        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "활성화" if enabled else "비활성화"
        self.view.append_log(f"[{timestamp}] 💻 콘솔 출력 대기: {status} (적용 버튼 클릭 필요)")

    def _on_log_scope_changed(self, new_scope: str):
        """로그 스코프 변경 감지"""
        if self._initializing:
            return

        self._pending_settings['scope'] = new_scope
        self._has_pending_changes = True

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] 🔍 로그 스코프 대기: {new_scope} (적용 버튼 클릭 필요)")

    def _on_component_focus_changed(self, component: str):
        """컴포넌트 집중 변경 감지"""
        if self._initializing:
            return

        self._pending_settings['component_focus'] = component
        self._has_pending_changes = True

        timestamp = datetime.now().strftime("%H:%M:%S")
        display_text = component if component else "(전체)"
        self.view.append_log(f"[{timestamp}] 📝 컴포넌트 집중 대기: {display_text} (적용 버튼 클릭 필요)")

    def _on_log_context_changed(self, context: str):
        """로깅 컨텍스트 변경 감지"""
        if self._initializing:
            return

        self._pending_settings['context'] = context
        self._has_pending_changes = True

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.append_log(f"[{timestamp}] 🌍 로깅 컨텍스트 대기: {context} (적용 버튼 클릭 필요)")

    def refresh(self) -> None:
        """탭 새로고침 처리"""
        if self._refreshing:
            return

        try:
            self._refreshing = True
            timestamp = datetime.now().strftime("%H:%M:%S")

            self.view.append_log(f"📊 [{timestamp}] 설정 파일 기반 로깅 관리 탭 새로고침")

            # 현재 설정 다시 로드
            self._load_current_config()

        except Exception as e:
            self.view.append_log(f"❌ 새로고침 처리 오류: {e}")
        finally:
            self._refreshing = False

    def get_status_summary(self) -> Dict[str, Any]:
        """상태 요약 조회"""
        return self._config_manager.get_status_summary()

    def shutdown(self):
        """Presenter 종료 처리"""
        try:
            # 설정 변경 핸들러 제거
            self._config_manager.remove_change_handler(self._on_config_changed)
        except Exception:
            pass

    def __del__(self):
        """소멸자: 리소스 정리"""
        try:
            self.shutdown()
        except Exception:
            pass
