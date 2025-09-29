"""
데이터베이스 설정 화면 - MVP 패턴 적용

기본에 충실하면서도 MVP 패턴을 적용한 데이터베이스 설정 화면입니다.
View와 Presenter를 분리하여 비즈니스 로직과 UI를 깔끔하게 분리했습니다.
"""

from typing import Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QGroupBox,
    QFrame, QGridLayout
)
from PyQt6.QtCore import pyqtSignal

# Application Layer - Infrastructure 의존성 격리
from ..widgets.database_status_widget import DatabaseStatusWidget
from ..widgets.database_backup_widget import DatabaseBackupWidget
from ..widgets.database_path_selector import DatabasePathSelector
from ..widgets.database_task_progress_widget import DatabaseTaskProgressWidget


class DatabaseSettingsView(QWidget):
    """
    데이터베이스 설정 화면 - MVP 패턴 적용

    기본에 충실하면서도 MVP 패턴을 적용한 데이터베이스 설정 화면입니다.
    View 역할만 담당하고, 비즈니스 로직은 Presenter에서 처리합니다.
    """

    # 시그널 정의
    settings_changed = pyqtSignal()
    db_status_changed = pyqtSignal(bool)  # 연결 상태 변화

    def __init__(self, parent=None, logging_service=None):
        super().__init__(parent)
        self.setObjectName("widget-database-settings")

        # 로깅 초기화 - DI 패턴
        if logging_service:
            self.logger = logging_service.get_component_logger("DatabaseSettingsView")
        else:
            raise ValueError("DatabaseSettingsView에 logging_service가 주입되지 않았습니다")

        self.logger.info("📊 데이터베이스 설정 화면 (MVP) 초기화 시작")

        # UI 설정
        self._setup_ui()

        # Presenter는 Factory에서 설정됨
        self.presenter = None

        self.logger.info("✅ 데이터베이스 설정 화면 (MVP) 초기화 완료")

    def set_presenter(self, presenter):
        """Presenter 설정 및 연결

        Args:
            presenter: Database 설정 Presenter 인스턴스
        """
        self.presenter = presenter
        self.logger.info("🔗 Presenter 연결됨")

        # 시그널 연결
        self._connect_signals()

        # 초기 데이터 로드 (Presenter를 통해)
        if self.presenter:
            self.presenter.load_database_info()

        # 백업 목록도 초기 로드
        self._on_refresh_backups()

    def _setup_ui(self):
        """UI 구성 - 2x2 그리드 레이아웃 (좌3:1우 비율)"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # 2x2 그리드 레이아웃 생성
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)

        # 열 비율 설정: 좌측 3, 우측 1
        grid_layout.setColumnStretch(0, 3)  # 좌측 열 (데이터베이스 경로 관리, 데이터베이스 관리)
        grid_layout.setColumnStretch(1, 1)  # 우측 열 (상태, 진행상황)

        # 행 비율 설정: 상단과 하단 모두 동일하게
        grid_layout.setRowStretch(0, 1)  # 상단 행
        grid_layout.setRowStretch(1, 1)  # 하단 행

        # 4개 구성요소 배치
        # [0,0] 데이터베이스 경로 관리 (좌측 상단)
        self._create_path_selector_group_grid(grid_layout, 0, 0)

        # [0,1] 데이터베이스 상태 (우측 상단)
        self._create_status_group_grid(grid_layout, 0, 1)

        # [1,0] 데이터베이스 관리 (좌측 하단)
        self._create_management_group_grid(grid_layout, 1, 0)

        # [1,1] 작업 진행 상황 (우측 하단)
        self._create_progress_section_grid(grid_layout, 1, 1)

        main_layout.addLayout(grid_layout)

    def _create_path_selector_group_grid(self, grid_layout, row, col):
        """데이터베이스 경로 관리 (좌측 상단) - 중복 라벨 제거"""
        group = QGroupBox("📂 데이터베이스 경로 관리")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # 경로 선택 위젯들 - 컴팩트하게 배치
        self.settings_path_selector = DatabasePathSelector(
            "settings", "⚙️ 설정 데이터베이스", self
        )
        self.strategies_path_selector = DatabasePathSelector(
            "strategies", "🎯 전략 데이터베이스", self
        )
        self.market_data_path_selector = DatabasePathSelector(
            "market_data", "📈 시장데이터 데이터베이스", self
        )

        layout.addWidget(self.settings_path_selector)
        layout.addWidget(self.strategies_path_selector)
        layout.addWidget(self.market_data_path_selector)

        grid_layout.addWidget(group, row, col)

    def _create_status_group_grid(self, grid_layout, row, col):
        """데이터베이스 상태 (우측 상단) - 내부 중복 라벨 제거"""
        group = QGroupBox("📊 데이터베이스 상태")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)

        # 상태 위젯 - 내부 라벨 중복 제거됨
        self.status_widget = DatabaseStatusWidget(self)
        self.status_widget.status_clicked.connect(self._on_status_clicked)
        layout.addWidget(self.status_widget)

        grid_layout.addWidget(group, row, col)

    def _create_management_group_grid(self, grid_layout, row, col):
        """데이터베이스 백업 관리 (좌측 하단) - 내부 중복 라벨 제거"""
        group = QGroupBox("🔧 데이터베이스 백업 관리")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # 백업 관리 위젯 - 내부 라벨 중복 제거됨
        self.backup_widget = DatabaseBackupWidget(self)
        self.backup_widget.create_backup_requested.connect(self._on_backup_requested)
        self.backup_widget.restore_backup_requested.connect(self._on_restore_requested)
        self.backup_widget.delete_backup_requested.connect(self._on_delete_backup_requested)
        self.backup_widget.refresh_backups_requested.connect(self._on_refresh_backups)
        self.backup_widget.description_updated.connect(self._on_description_updated)
        layout.addWidget(self.backup_widget)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # 관리 버튼들
        button_layout = QHBoxLayout()
        self.validate_btn = QPushButton("✅ 검증")
        self.open_folder_btn = QPushButton("📂 폴더")

        button_layout.addWidget(self.validate_btn)
        button_layout.addWidget(self.open_folder_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        grid_layout.addWidget(group, row, col)

    def _create_progress_section_grid(self, grid_layout, row, col):
        """작업 진행 상황 (우측 하단) - 새로운 전용 위젯 사용"""
        # 새로운 작업 진행 상황 위젯 생성
        self.progress_widget = DatabaseTaskProgressWidget()

        # 그리드에 추가
        grid_layout.addWidget(self.progress_widget, row, col)

    def _connect_signals(self):
        """시그널 연결 - Presenter와 연결"""
        # 상태 위젯의 새로고침 시그널 연결
        self.status_widget.refresh_requested.connect(self.presenter.refresh_status)

        # 상태 위젯에서 새로고침 버튼 가져오기 (레거시 호환)
        refresh_btn = getattr(self.status_widget, 'refresh_btn', None)
        if refresh_btn:
            refresh_btn.clicked.connect(self.presenter.refresh_status)

        # 경로 선택 위젯들의 시그널 연결
        self.settings_path_selector.path_changed.connect(self._on_path_changed)
        self.settings_path_selector.path_validation_requested.connect(self._on_path_validation_requested)

        self.strategies_path_selector.path_changed.connect(self._on_path_changed)
        self.strategies_path_selector.path_validation_requested.connect(self._on_path_validation_requested)

        self.market_data_path_selector.path_changed.connect(self._on_path_changed)
        self.market_data_path_selector.path_validation_requested.connect(self._on_path_validation_requested)

        self.validate_btn.clicked.connect(self.presenter.validate_databases)
        self.open_folder_btn.clicked.connect(self.presenter.open_data_folder)

    def _on_status_clicked(self, database_type: str):
        """상태 카드 클릭 시 상세 정보 표시"""
        self.logger.info(f"📊 상태 카드 클릭: {database_type}")
        # 향후 상세 정보 창 구현 예정

    def _on_backup_requested(self, database_type: str):
        """백업 생성 요청 - 실제 백업 진행"""
        self.logger.info(f"💾 백업 생성 요청: {database_type}")

        # 진행상황 표시
        self.show_progress(f"{database_type} 백업 생성 중...", 0)

        # Presenter를 통해 실제 백업 수행
        if hasattr(self, 'presenter'):
            try:
                # 백업 진행 중 표시
                self.show_progress(f"{database_type} 백업 생성 중...", 50)

                # 실제 백업 로직 - Presenter를 통해 백업 수행
                backup_result = self.presenter.create_database_backup(database_type)

                if backup_result:
                    self.logger.info(f"✅ {database_type} 백업 완료")
                    self.show_progress(f"{database_type} 백업 완료!", 100)
                    # 작업 완료 처리
                    if hasattr(self, 'progress_widget'):
                        self.progress_widget.complete_task(True, f"{database_type} 백업이 성공적으로 생성되었습니다.")
                    self.show_info_message("백업 완료", f"{database_type} 백업이 성공적으로 생성되었습니다.")
                else:
                    self.logger.error(f"❌ {database_type} 백업 실패")
                    # 작업 실패 처리
                    if hasattr(self, 'progress_widget'):
                        self.progress_widget.complete_task(False, f"{database_type} 백업 생성에 실패했습니다.")
                    self.show_error_message("백업 실패", f"{database_type} 백업 생성에 실패했습니다.")

                # 백업 목록 자동 새로고침
                self._on_refresh_backups()

            except Exception as e:
                self.logger.error(f"❌ 백업 실패: {e}")
                # 작업 실패 처리
                if hasattr(self, 'progress_widget'):
                    self.progress_widget.complete_task(False, f"백업 중 오류 발생: {str(e)}")
                self.show_error_message("백업 실패", f"{database_type} 백업 중 오류가 발생했습니다: {str(e)}")
        else:
            self.logger.error("❌ Presenter가 연결되지 않았습니다")
            self.hide_progress()
            self.show_error_message("백업 실패", "Presenter가 연결되지 않았습니다.")

    def _on_restore_requested(self, backup_id: str):
        """백업 복원 요청 - Presenter에게 위임"""
        self.logger.info(f"🔄 백업 복원 요청: {backup_id}")

        # 진행 상황 표시 시작
        self.show_progress("백업 복원 진행 중...")
        self.progress_widget.start_task(f"백업 복원: {backup_id}")

        # Presenter의 메서드를 호출 (아직 구현 안됨 - 다음 단계에서 추가)
        try:
            if hasattr(self.presenter, 'restore_database_backup'):
                self.progress_widget.update_progress(50, "백업 파일 복원 중...")
                success = self.presenter.restore_database_backup(backup_id)

                if success:
                    self.logger.info(f"✅ 백업 복원 성공: {backup_id}")
                    self.progress_widget.complete_task(True, "백업이 성공적으로 복원되었습니다")
                    # 상태 새로고침
                    if hasattr(self.presenter, 'refresh_status'):
                        self.presenter.refresh_status()
                else:
                    self.logger.error(f"❌ 백업 복원 실패: {backup_id}")
                    self.progress_widget.complete_task(False, "백업 복원 중 오류가 발생했습니다")
            else:
                self.logger.warning("⚠️ Presenter에 restore_database_backup 메서드가 없음")
                self.progress_widget.complete_task(False, "복원 기능이 아직 구현되지 않았습니다")
        except Exception as e:
            self.logger.error(f"❌ 백업 복원 예외 발생: {e}")
            self.progress_widget.complete_task(False, f"복원 중 오류 발생: {str(e)}")

    def _on_delete_backup_requested(self, backup_id: str):
        """백업 삭제 요청 - Presenter에게 위임"""
        self.logger.info(f"🗑️ 백업 삭제 요청: {backup_id}")

        # Presenter의 메서드를 호출 (아직 구현 안됨 - 다음 단계에서 추가)
        if hasattr(self.presenter, 'delete_database_backup'):
            success = self.presenter.delete_database_backup(backup_id)
            if success:
                self.logger.info(f"✅ 백업 삭제 성공: {backup_id}")
            else:
                self.logger.error(f"❌ 백업 삭제 실패: {backup_id}")
        else:
            self.logger.warning("⚠️ Presenter에 delete_database_backup 메서드가 없음")

    def _on_refresh_backups(self):
        """백업 목록 새로고침 - 실제 새로고침"""
        self.logger.info("🔃 백업 목록 새로고침")

        # 진행상황 표시
        self.show_progress("백업 목록 새로고침 중...", 50)

        # Presenter를 통해 백업 목록 로드
        if hasattr(self, 'presenter') and hasattr(self, 'backup_widget'):
            try:
                backup_list = self.presenter.get_backup_list()
                self.backup_widget.update_backup_list(backup_list)
                self.logger.info(f"✅ 백업 목록 새로고침 완료: {len(backup_list)}개")

                # 작업 완료 처리
                if hasattr(self, 'progress_widget'):
                    self.progress_widget.complete_task(True, f"백업 목록 새로고침 완료: {len(backup_list)}개")

            except Exception as e:
                self.logger.error(f"❌ 백업 목록 새로고침 실패: {e}")
                # 작업 실패 처리
                if hasattr(self, 'progress_widget'):
                    self.progress_widget.complete_task(False, f"백업 목록 새로고침 실패: {str(e)}")
                self.show_error_message("새로고침 실패", f"백업 목록 새로고침 중 오류가 발생했습니다: {str(e)}")
        else:
            self.logger.warning("⚠️ Presenter 또는 backup_widget 없음")
            # 작업 실패 처리
            if hasattr(self, 'progress_widget'):
                self.progress_widget.complete_task(False, "시스템 오류: Presenter 없음")

    def _on_description_updated(self, backup_id: str, new_description: str):
        """백업 설명 업데이트 처리"""
        self.logger.info(f"📝 백업 설명 업데이트: {backup_id} -> {new_description}")

        if hasattr(self.presenter, 'update_backup_description'):
            try:
                self.presenter.update_backup_description(backup_id, new_description)
                self.logger.info("✅ 백업 설명 업데이트 완료")
            except Exception as e:
                self.logger.error(f"❌ 백업 설명 업데이트 실패: {e}")
                self.show_error_message("설명 업데이트 실패", f"설명 업데이트 중 오류가 발생했습니다: {str(e)}")
        else:
            self.logger.warning("⚠️ Presenter에 update_backup_description 메서드가 없음")

    def _on_path_changed(self, database_type: str, new_path: str):
        """데이터베이스 경로 변경 이벤트 - 실제 경로 변경 처리"""
        self.logger.info(f"📂 경로 변경 요청: {database_type} → {new_path}")

        if not new_path.strip():
            self.logger.debug("🔄 경로가 빈 문자열이므로 처리하지 않음")
            return

        # 사용자 확인 (중요한 작업이므로)
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "데이터베이스 경로 변경",
            f"{database_type} 데이터베이스의 경로를 변경하시겠습니까?\n\n"
            f"새 경로: {new_path}\n\n"
            f"⚠️ 이 작업은 전체 시스템에 영향을 줄 수 있습니다.\n"
            f"계속하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            self.logger.info("👤 사용자가 경로 변경을 취소했습니다")
            return

        # Presenter를 통해 실제 경로 변경 수행
        if hasattr(self, 'presenter'):
            try:
                self.logger.info(f"🔄 Presenter를 통한 실제 경로 변경 시작: {database_type}")

                # 진행상황 표시
                self.show_progress(f"{database_type} 데이터베이스 경로 변경 중...", 0)

                # 경로 변경 적용
                success = self.presenter.change_database_path(database_type, new_path)

                if success:
                    self.logger.info(f"✅ {database_type} 경로 변경 완료")
                    self.show_progress(f"{database_type} 경로 변경 완료!", 100)
                    # 작업 완료 처리
                    if hasattr(self, 'progress_widget'):
                        self.progress_widget.complete_task(True, f"{database_type} 경로가 성공적으로 변경되었습니다.")

                    # 상태 새로고침
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(1000, self.presenter.load_database_info)
                else:
                    self.logger.error(f"❌ {database_type} 경로 변경 실패")
                    # 작업 실패 처리
                    if hasattr(self, 'progress_widget'):
                        self.progress_widget.complete_task(False, f"{database_type} 경로 변경에 실패했습니다.")

                    # 🚨 사용자에게 명확한 경고 메시지 표시
                    self.show_error_message(
                        "데이터베이스 등록 실패",
                        f"⚠️ {database_type} 데이터베이스를 등록할 수 없습니다.\n\n"
                        f"선택한 파일이 손상되었거나 올바른 SQLite 데이터베이스가 아닙니다.\n\n"
                        f"📁 파일: {new_path}\n\n"
                        f"💡 해결 방법:\n"
                        f"• 올바른 SQLite 파일을 선택하세요\n"
                        f"• 파일이 손상된 경우 백업에서 복원하세요\n"
                        f"• 새로운 데이터베이스 파일을 생성하세요"
                    )

                    # 🔧 DDD 원칙: 실패 시 DB에서 실제 정보를 다시 로드하여 UI에 반영
                    self.logger.info("🔄 DB에서 실제 경로 정보를 다시 로드하여 UI 동기화")
                    self.presenter.load_database_info()

            except Exception as e:
                self.logger.error(f"❌ 경로 변경 중 오류: {e}")
                self.hide_progress()
                self.show_error_message("경로 변경 오류", f"경로 변경 중 오류가 발생했습니다: {str(e)}")
        else:
            self.logger.error("❌ Presenter가 연결되지 않았습니다")
            self.show_error_message("시스템 오류", "Presenter가 연결되지 않았습니다.")

    def _on_path_validation_requested(self, database_type: str, path: str):
        """경로 검증 요청 이벤트"""
        self.logger.info(f"🔍 경로 검증 요청: {database_type} → {path}")
        # 로그만 남기고 알림 박스는 표시하지 않음

    # ISimpleDatabaseView 인터페이스 구현
    def display_database_info(self, info: Dict[str, str]) -> None:
        """데이터베이스 정보 표시 - PathSelector 위젯들에 경로 설정"""
        if hasattr(self, 'settings_path_selector'):
            self.settings_path_selector.set_path(info['settings_db'])
        if hasattr(self, 'strategies_path_selector'):
            self.strategies_path_selector.set_path(info['strategies_db'])
        if hasattr(self, 'market_data_path_selector'):
            self.market_data_path_selector.set_path(info['market_data_db'])

    def display_status(self, status: Dict) -> None:
        """상태 정보 표시 - DatabaseStatusWidget에 전달"""
        if hasattr(self, 'status_widget'):
            self.status_widget.update_status(status)

    def show_progress(self, message: str, value: int = 0) -> None:
        """진행상황 표시 - 새로운 위젯 방식"""
        if hasattr(self, 'progress_widget'):
            if value == 0:
                # 작업 시작
                self.progress_widget.start_task(message)
            else:
                # 진행 상황 업데이트
                self.progress_widget.update_progress(value, message)

    def hide_progress(self) -> None:
        """진행상황 숨김 - 새로운 위젯 방식"""
        if hasattr(self, 'progress_widget'):
            self.progress_widget.reset_progress()

    def show_validation_result(self, results: list) -> None:
        """검증 결과 표시"""
        result_text = "📋 데이터베이스 검증 결과:\n\n" + "\n".join(results)
        QMessageBox.information(self, "검증 완료", result_text)

    def show_error_message(self, title: str, message: str) -> None:
        """오류 메시지 표시"""
        QMessageBox.critical(self, title, message)

    def show_success_message(self, title: str, message: str) -> None:
        """성공 메시지 표시"""
        QMessageBox.information(self, title, message)

    def show_info_message(self, title: str, message: str) -> None:
        """정보 메시지 표시"""
        QMessageBox.information(self, title, message)

    # 공개 메서드들 (MVP 패턴으로 간소화)
    def refresh_display(self):
        """화면 새로고침"""
        self.presenter.load_database_info()
