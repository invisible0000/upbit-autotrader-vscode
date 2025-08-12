"""
실시간 로깅 관리 탭 - MVP Presenter
===================================

DDD Application Layer - Use Case 구현
Config 파일 기반 로깅 설정 관리 및 실시간 적용

주요 특징:
- MVP 패턴 Presenter (비즈니스 로직 담당)
- Config 파일 기반 설정 시스템 (환경변수 완전 대체)
- 실시간 설정 적용 및 UI 프리징 방지
- Infrastructure Layer 로깅 시스템 통합
- DDD Domain Layer 의존성 없음
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.logging.config.logging_config_manager import LoggingConfigManager


class LoggingManagementPresenter(QObject):
    """실시간 로깅 관리 MVP Presenter - Config 파일 기반"""

    def __init__(self, view=None):
        super().__init__()
        self.view = view

        # Infrastructure 로깅
        self.logger = create_component_logger("LoggingManagementPresenter")
        self.logger.info("🎛️ 로깅 관리 프레젠터 초기화 시작")

        # Config 관리자 초기화
        self._config_manager = LoggingConfigManager()

        # 실시간 업데이트 타이머 (UI 프리징 방지)
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._apply_delayed_settings)

        # 현재 설정 캐시
        self._current_settings = {}
        self._pending_settings = {}

        self._initialize()

    def _initialize(self):
        """초기화 및 View 연결"""
        if self.view:
            self._connect_view_signals()
            self._load_initial_settings()

        self.logger.info("✅ 로깅 관리 프레젠터 초기화 완료")

    def _connect_view_signals(self):
        """View 시그널 연결 - MVP 패턴"""
        self.view.settings_changed.connect(self._on_settings_changed)
        self.view.apply_settings_requested.connect(self._on_apply_settings)
        self.view.reset_settings_requested.connect(self._on_reset_settings)

        self.logger.debug("🔗 뷰 시그널 연결 완료")

    def _load_initial_settings(self):
        """초기 설정 로드 및 View 업데이트"""
        try:
            settings = self._config_manager.get_current_config()
            self._current_settings = settings.copy()

            # View에 설정 반영
            self.view.update_settings_display(settings)

            self.logger.info("📄 초기 설정 로드 완료")
            self.view.show_status_message("설정 파일에서 초기 설정을 로드했습니다", "info")

        except Exception as e:
            self.logger.error(f"❌ 초기 설정 로드 실패: {e}")
            self.view.show_status_message(f"초기 설정 로드 실패: {e}", "error")

            # 기본 설정으로 폴백
            self._apply_default_settings()

    def _apply_default_settings(self):
        """기본 설정 적용 (폴백용)"""
        default_settings = {
            "log_level": "INFO",
            "console_output": True,
            "log_scope": "normal",
            "component_focus": "",
            "file_logging_enabled": True,
            "file_path": "logs/upbit_auto_trading.log",
            "file_level": "DEBUG"
        }

        self._current_settings = default_settings.copy()
        self.view.update_settings_display(default_settings)

        self.logger.warning("⚠️ 기본 설정으로 폴백")
        self.view.show_status_message("기본 설정을 적용했습니다", "warning")

    def _on_settings_changed(self, changed_setting: Dict[str, Any]):
        """설정 변경 시 실시간 처리 (UI 프리징 방지)"""
        self.logger.debug(f"🔄 설정 변경 감지: {changed_setting}")

        # 변경 사항을 펜딩 큐에 누적
        self._pending_settings.update(changed_setting)

        # 지연 적용 타이머 재시작 (연속 변경 시 마지막만 적용)
        self._update_timer.stop()
        self._update_timer.start(500)  # 500ms 지연

        # 즉시 UI 상태 메시지 업데이트
        setting_name = list(changed_setting.keys())[0]
        setting_value = list(changed_setting.values())[0]
        self.view.show_status_message(f"{setting_name}: {setting_value} (적용 대기중...)", "info")

    def _apply_delayed_settings(self):
        """지연된 설정 일괄 적용 (성능 최적화)"""
        if not self._pending_settings:
            return

        try:
            self.logger.info(f"⚡ 일괄 설정 적용: {self._pending_settings}")

            # 현재 설정에 변경사항 병합
            self._current_settings.update(self._pending_settings)

            # Config 파일에 저장
            self._config_manager.update_config(self._current_settings)

            # 로깅 시스템 즉시 적용
            self._apply_to_logging_system(self._current_settings)

            # UI 상태 업데이트
            change_count = len(self._pending_settings)
            self.view.show_status_message(f"✅ {change_count}개 설정이 적용되었습니다", "info")

            # 펜딩 큐 클리어
            self._pending_settings.clear()

        except Exception as e:
            self.logger.error(f"❌ 설정 적용 실패: {e}")
            self.view.show_status_message(f"설정 적용 실패: {e}", "error")

    def _apply_to_logging_system(self, settings: Dict[str, Any]):
        """Infrastructure Layer 로깅 시스템에 설정 적용"""
        try:
            # 로깅 레벨 적용
            if "log_level" in settings:
                self._config_manager.set_log_level(settings["log_level"])

            # 콘솔 출력 설정
            if "console_output" in settings:
                self._config_manager.set_console_output(settings["console_output"])

            # 파일 로깅 설정
            if any(key in settings for key in ["file_logging_enabled", "file_path", "file_level"]):
                self._config_manager.configure_file_logging(
                    enabled=settings.get("file_logging_enabled", True),
                    file_path=settings.get("file_path", "logs/upbit_auto_trading.log"),
                    level=settings.get("file_level", "DEBUG")
                )

            # 고급 설정
            if "log_scope" in settings:
                self._config_manager.set_log_scope(settings["log_scope"])

            if "component_focus" in settings:
                self._config_manager.set_component_focus(settings["component_focus"])

            self.logger.debug("🔧 로깅 시스템 설정 적용 완료")

        except Exception as e:
            self.logger.error(f"❌ 로깅 시스템 적용 실패: {e}")
            raise

    def _on_apply_settings(self):
        """설정 적용 버튼 클릭 시 처리"""
        try:
            # 현재 View의 모든 설정 가져오기
            current_view_settings = self.view.get_current_settings()

            # 변경사항 비교
            changes = {}
            for key, value in current_view_settings.items():
                if key not in self._current_settings or self._current_settings[key] != value:
                    changes[key] = value

            if not changes:
                self.view.show_status_message("변경된 설정이 없습니다", "info")
                return

            self.logger.info(f"🔄 수동 설정 적용 요청: {changes}")

            # 즉시 적용
            self._current_settings.update(changes)
            self._config_manager.update_config(self._current_settings)
            self._apply_to_logging_system(self._current_settings)

            change_count = len(changes)
            self.view.show_status_message(f"✅ {change_count}개 설정을 수동 적용했습니다", "info")

        except Exception as e:
            self.logger.error(f"❌ 수동 설정 적용 실패: {e}")
            self.view.show_status_message(f"설정 적용 실패: {e}", "error")

    def _on_reset_settings(self):
        """설정 리셋 요청 처리"""
        try:
            # 사용자 확인
            reply = QMessageBox.question(
                self.view,
                "설정 리셋 확인",
                "모든 로깅 설정을 기본값으로 되돌리시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.logger.info("🔄 설정 리셋 실행")

                # Config 파일 리셋
                self._config_manager.reset_to_default()

                # 기본 설정 로드
                default_settings = self._config_manager.get_current_config()
                self._current_settings = default_settings.copy()

                # View 업데이트
                self.view.update_settings_display(default_settings)

                # 로깅 시스템 적용
                self._apply_to_logging_system(default_settings)

                self.view.show_status_message("✅ 모든 설정이 기본값으로 리셋되었습니다", "info")

        except Exception as e:
            self.logger.error(f"❌ 설정 리셋 실패: {e}")
            self.view.show_status_message(f"설정 리셋 실패: {e}", "error")

    # ===== 로그/콘솔 관리 메서드 =====

    def start_log_monitoring(self):
        """로그 파일 모니터링 시작"""
        try:
            log_file_path = self._current_settings.get("file_path", "logs/upbit_auto_trading.log")

            if os.path.exists(log_file_path):
                # 기존 로그 내용 로드
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        self.view.append_log_message(content)

                self.logger.info(f"📄 로그 파일 모니터링 시작: {log_file_path}")
            else:
                self.view.append_log_message("로그 파일이 아직 생성되지 않았습니다.")

        except Exception as e:
            self.logger.error(f"❌ 로그 모니터링 시작 실패: {e}")

    def save_logs_to_file(self):
        """로그를 파일로 저장"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self.view,
                "로그 파일 저장",
                f"upbit_logs_{QTimer().currentDateTime().toString('yyyyMMdd_hhmmss')}.txt",
                "Text Files (*.txt);;All Files (*)"
            )

            if file_path:
                # View에서 현재 로그 내용 가져오기 (이 메서드는 View에 추가 필요)
                log_content = self.view.log_viewer_widget.get_all_content()

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(log_content)

                self.view.show_status_message(f"✅ 로그가 저장되었습니다: {file_path}", "info")
                self.logger.info(f"💾 로그 파일 저장: {file_path}")

        except Exception as e:
            self.logger.error(f"❌ 로그 저장 실패: {e}")
            self.view.show_status_message(f"로그 저장 실패: {e}", "error")

    def clear_all_viewers(self):
        """모든 뷰어 내용 지우기"""
        self.view.clear_log_viewer()
        self.view.clear_console_viewer()
        self.view.show_status_message("✅ 모든 뷰어 내용이 지워졌습니다", "info")
        self.logger.info("🧹 모든 뷰어 내용 지우기 완료")

    # ===== 설정 관리 헬퍼 메서드 =====

    def get_current_config_path(self) -> str:
        """현재 사용 중인 설정 파일 경로 반환"""
        return self._config_manager.get_config_file_path()

    def export_settings(self):
        """설정을 파일로 내보내기"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self.view,
                "로깅 설정 내보내기",
                f"logging_settings_{QTimer().currentDateTime().toString('yyyyMMdd_hhmmss')}.yaml",
                "YAML Files (*.yaml *.yml);;All Files (*)"
            )

            if file_path:
                self._config_manager.export_config(file_path)
                self.view.show_status_message(f"✅ 설정이 내보내졌습니다: {file_path}", "info")
                self.logger.info(f"📤 설정 내보내기: {file_path}")

        except Exception as e:
            self.logger.error(f"❌ 설정 내보내기 실패: {e}")
            self.view.show_status_message(f"설정 내보내기 실패: {e}", "error")

    def import_settings(self):
        """파일에서 설정 가져오기"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self.view,
                "로깅 설정 가져오기",
                "",
                "YAML Files (*.yaml *.yml);;All Files (*)"
            )

            if file_path:
                imported_settings = self._config_manager.import_config(file_path)

                # View 업데이트
                self.view.update_settings_display(imported_settings)
                self._current_settings = imported_settings.copy()

                # 로깅 시스템 적용
                self._apply_to_logging_system(imported_settings)

                self.view.show_status_message(f"✅ 설정을 가져왔습니다: {file_path}", "info")
                self.logger.info(f"📥 설정 가져오기: {file_path}")

        except Exception as e:
            self.logger.error(f"❌ 설정 가져오기 실패: {e}")
            self.view.show_status_message(f"설정 가져오기 실패: {e}", "error")

    # ===== 라이프사이클 관리 =====

    def cleanup(self):
        """리소스 정리"""
        if self._update_timer.isActive():
            self._update_timer.stop()

        self.logger.info("🧹 로깅 관리 프레젠터 정리 완료")

    def __del__(self):
        """소멸자"""
        self.cleanup()
