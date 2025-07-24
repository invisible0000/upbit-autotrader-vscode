"""
데이터베이스 설정 모듈

이 모듈은 데이터베이스 설정 기능을 구현합니다.
- 데이터베이스 경로 설정
- 데이터베이스 최대 크기 설정
- 데이터베이스 백업 및 복원
"""

import os
import json
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QSpinBox, QFileDialog, QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal


class DatabaseSettings(QWidget):
    """데이터베이스 설정 위젯 클래스"""
    
    # 설정 변경 시그널
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """초기화"""
        super().__init__(parent)
        self.setObjectName("widget-database-settings")
        
        # UI 설정
        self._setup_ui()
        
        # 시그널 연결
        self._connect_signals()
    
    def _setup_ui(self):
        """UI 설정"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 데이터베이스 경로 그룹
        path_group = QGroupBox("데이터베이스 경로")
        path_layout = QVBoxLayout(path_group)
        
        # 경로 입력 레이아웃
        path_input_layout = QHBoxLayout()
        
        # 경로 입력
        self.db_path_input = QLineEdit()
        self.db_path_input.setObjectName("input-db-path")
        self.db_path_input.setPlaceholderText("데이터베이스 파일 경로")
        self.db_path_input.setReadOnly(True)
        path_input_layout.addWidget(self.db_path_input)
        
        # 찾아보기 버튼
        self.browse_button = QPushButton("찾아보기")
        self.browse_button.setObjectName("button-browse-db-path")
        path_input_layout.addWidget(self.browse_button)
        
        # DB 생성 버튼 추가
        self.create_db_button = QPushButton("DB 생성")
        self.create_db_button.setObjectName("button-create-db")
        path_input_layout.addWidget(self.create_db_button)
        
        path_layout.addLayout(path_input_layout)
        
        # 경로 설명 (올바른 기본 경로)
        path_info = QLabel("* 데이터베이스 파일의 경로를 설정합니다.\n* 기본 경로는 'data/app_settings.sqlite3'입니다.")
        path_info.setObjectName("label-path-info")
        path_info.setStyleSheet("color: #666666; font-size: 10px;")
        path_layout.addWidget(path_info)
        
        # 데이터 관리 그룹
        data_group = QGroupBox("데이터 관리")
        data_layout = QVBoxLayout(data_group)
        
        # 폼 레이아웃
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 10, 0, 10)
        form_layout.setSpacing(10)
        
        # 최대 크기 입력
        self.max_size_input = QSpinBox()
        self.max_size_input.setObjectName("input-max-size")
        self.max_size_input.setRange(1, 100)
        self.max_size_input.setValue(10)
        self.max_size_input.setSuffix(" GB")
        form_layout.addRow("최대 크기:", self.max_size_input)
        
        # 현재 크기 표시
        self.current_size_label = QLabel("0 MB")
        self.current_size_label.setObjectName("label-current-size")
        form_layout.addRow("현재 크기:", self.current_size_label)
        
        # 데이터 보존 기간 입력
        self.retention_period_input = QSpinBox()
        self.retention_period_input.setObjectName("input-retention-period")
        self.retention_period_input.setRange(1, 365)
        self.retention_period_input.setValue(90)
        self.retention_period_input.setSuffix(" 일")
        form_layout.addRow("데이터 보존 기간:", self.retention_period_input)
        
        data_layout.addLayout(form_layout)
        
        # 데이터 관리 설명
        data_info = QLabel("* 최대 크기를 초과하면 오래된 데이터부터 자동으로 삭제됩니다.\n* 데이터 보존 기간이 지난 데이터는 자동으로 삭제됩니다.")
        data_info.setObjectName("label-data-info")
        data_info.setStyleSheet("color: #666666; font-size: 10px;")
        data_layout.addWidget(data_info)
        
        # 백업 그룹
        backup_group = QGroupBox("백업 및 복원")
        backup_layout = QVBoxLayout(backup_group)
        
        # 백업 버튼 레이아웃
        backup_button_layout = QHBoxLayout()
        
        # 백업 버튼
        self.backup_button = QPushButton("백업")
        self.backup_button.setObjectName("button-backup")
        backup_button_layout.addWidget(self.backup_button)
        
        # 복원 버튼
        self.restore_button = QPushButton("복원")
        self.restore_button.setObjectName("button-restore")
        backup_button_layout.addWidget(self.restore_button)
        
        backup_layout.addLayout(backup_button_layout)
        
        # 백업 진행 상태 바
        self.backup_progress = QProgressBar()
        self.backup_progress.setObjectName("progress-backup")
        self.backup_progress.setRange(0, 100)
        self.backup_progress.setValue(0)
        self.backup_progress.setVisible(False)
        backup_layout.addWidget(self.backup_progress)
        
        # 백업 설명
        backup_info = QLabel("* 백업 파일은 'backups' 디렉토리에 저장됩니다.\n* 복원 시 현재 데이터베이스가 백업 파일로 대체됩니다.")
        backup_info.setObjectName("label-backup-info")
        backup_info.setStyleSheet("color: #666666; font-size: 10px;")
        backup_layout.addWidget(backup_info)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)
        
        # 저장 버튼
        self.save_button = QPushButton("저장")
        self.save_button.setObjectName("button-save-db-settings")
        button_layout.addWidget(self.save_button)
        
        # 초기화 버튼
        self.reset_button = QPushButton("초기화")
        self.reset_button.setObjectName("button-reset-db-settings")
        button_layout.addWidget(self.reset_button)
        
        # 레이아웃 추가
        main_layout.addWidget(path_group)
        main_layout.addWidget(data_group)
        main_layout.addWidget(backup_group)
        main_layout.addLayout(button_layout)
        main_layout.addStretch(1)
        
        # 현재 데이터베이스 크기 업데이트
        self._update_current_size()
    
    def _connect_signals(self):
        """시그널 연결"""
        # 찾아보기 버튼 클릭 시 파일 대화상자 표시
        self.browse_button.clicked.connect(self._browse_db_path)
        
        # DB 생성 버튼 클릭 시 파일 생성
        self.create_db_button.clicked.connect(self.create_database_file)
        
        # 저장 버튼 클릭 시 설정 저장
        self.save_button.clicked.connect(self.save_settings)
        
        # 초기화 버튼 클릭 시 설정 초기화
        self.reset_button.clicked.connect(self._reset_settings)
        
        # 백업 버튼 클릭 시 데이터베이스 백업
        self.backup_button.clicked.connect(self.backup_database)
        
        # 복원 버튼 클릭 시 데이터베이스 복원
        self.restore_button.clicked.connect(self._restore_database)
    
    def _browse_db_path(self):
        """데이터베이스 경로 찾아보기"""
        # 파일 대화상자 표시, 기존 파일 선택용
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "데이터베이스 파일 선택",
            "data/",
            "SQLite 데이터베이스 (*.sqlite3);;모든 파일 (*.*)"
        )
        
        # 파일이 선택되었으면 경로 설정
        if file_path:
            self.db_path_input.setText(file_path)

    def create_database_file(self):
        """입력된 경로에 DB 파일 생성"""
        db_path = self.db_path_input.text().strip()
        if not db_path:
            QMessageBox.warning(self, "DB 경로 오류", "DB 경로와 파일명을 입력하세요.")
            return
        root, ext = os.path.splitext(db_path)
        if not ext:
            db_path += ".sqlite3"
        try:
            db_dir = os.path.dirname(db_path)
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)
            import sqlite3
            conn = sqlite3.connect(db_path)
            conn.close()
            if os.path.exists(db_path):
                QMessageBox.information(self, "DB 생성 완료", f"DB 파일이 생성되었습니다:\n{db_path}")
            else:
                QMessageBox.warning(self, "DB 생성 오류", f"DB 파일 생성에 실패했습니다. 경로를 확인하세요:\n{db_path}")
        except Exception as e:
            QMessageBox.warning(self, "DB 생성 오류", f"DB 생성 중 오류가 발생했습니다:\n{str(e)}")

    def _update_current_size(self):
        """현재 데이터베이스 크기 업데이트"""
        try:
            db_path = self.db_path_input.text()
            if os.path.exists(db_path):
                size_bytes = os.path.getsize(db_path)
                if size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.2f} KB"
                elif size_bytes < 1024 * 1024 * 1024:
                    size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
                self.current_size_label.setText(size_str)
                # 최대 크기 초과 시 자동 삭제
                max_size_gb = self.max_size_input.value()
                if size_bytes > max_size_gb * 1024 * 1024 * 1024:
                    self._delete_old_data_by_size(db_path, size_bytes, max_size_gb)
            else:
                self.current_size_label.setText("파일 없음")
        except Exception as e:
            self.current_size_label.setText("크기 계산 오류")
            print(f"데이터베이스 크기 계산 오류: {str(e)}")

    def _delete_old_data_by_size(self, db_path, size_bytes, max_size_gb):
        """최대 크기 초과 시 오래된 데이터 삭제"""
        import sqlite3
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # 예시: 거래 테이블에서 오래된 데이터 삭제 (테이블명/컬럼명은 실제 구조에 맞게 수정)
            cursor.execute("DELETE FROM trades WHERE rowid IN (SELECT rowid FROM trades ORDER BY timestamp ASC LIMIT 100)")
            conn.commit()
            conn.close()
            print("최대 크기 초과: 오래된 데이터 일부 삭제됨.")
        except Exception as e:
            print(f"오래된 데이터 삭제 오류: {str(e)}")

    def _delete_old_data_by_retention(self):
        """데이터 보존기간 초과 데이터 삭제"""
        import sqlite3
        from datetime import datetime, timedelta
        db_path = self.db_path_input.text()
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            retention_days = self.retention_period_input.value()
            cutoff = datetime.now() - timedelta(days=retention_days)
            cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M:%S')
            # 예시: 거래 테이블에서 보존기간 초과 데이터 삭제 (테이블명/컬럼명은 실제 구조에 맞게 수정)
            cursor.execute("DELETE FROM trades WHERE timestamp < ?", (cutoff_str,))
            conn.commit()
            conn.close()
            print("보존기간 초과: 오래된 데이터 삭제됨.")
        except Exception as e:
            print(f"보존기간 초과 데이터 삭제 오류: {str(e)}")

    def check_and_cleanup_database(self):
        """최대 크기/보존기간 초과 데이터 정리 트리거"""
        self._update_current_size()
        self._delete_old_data_by_retention()
    
    def _reset_settings(self):
        """설정 초기화"""
        # 기본 설정으로 초기화 (올바른 확장자)
        self.db_path_input.setText("data/app_settings.sqlite3")
        self.max_size_input.setValue(10)
        self.retention_period_input.setValue(90)
        
        # 현재 크기 업데이트
        self._update_current_size()
    
    def load_settings(self):
        """설정 로드"""
        try:
            # 설정 파일 경로
            settings_dir = os.path.join(os.path.expanduser("~"), ".upbit_auto_trading")
            settings_path = os.path.join(settings_dir, "db_settings.json")
            
            # 설정 파일이 없으면 기본 설정 사용
            if not os.path.exists(settings_path):
                self._reset_settings()
                return
            
            # 설정 파일 로드
            with open(settings_path, "r") as f:
                settings = json.load(f)
            
            # 설정 적용
            if "db_path" in settings:
                self.db_path_input.setText(settings["db_path"])
            
            if "max_size" in settings:
                self.max_size_input.setValue(settings["max_size"])
            
            if "retention_period" in settings:
                self.retention_period_input.setValue(settings["retention_period"])
            
            # 현재 크기 업데이트
            self._update_current_size()
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "설정 로드 오류",
                f"데이터베이스 설정을 로드하는 중 오류가 발생했습니다:\n{str(e)}"
            )
            
            # 오류 발생 시 기본 설정 사용
            self._reset_settings()
    
    def save_settings(self):
        """설정 저장"""
        try:
            # 입력값 가져오기
            db_path = self.db_path_input.text().strip()
            max_size = self.max_size_input.value()
            retention_period = self.retention_period_input.value()
            
            # 입력값 검증
            if not db_path:
                QMessageBox.warning(
                    self,
                    "입력 오류",
                    "데이터베이스 경로를 입력해주세요."
                )
                return
            
            # 설정 파일 경로
            settings_dir = os.path.join(os.path.expanduser("~"), ".upbit_auto_trading")
            settings_path = os.path.join(settings_dir, "db_settings.json")
            
            # 디렉토리가 없으면 생성
            if not os.path.exists(settings_dir):
                os.makedirs(settings_dir)
            
            # 설정 저장
            settings = {
                "db_path": db_path,
                "max_size": max_size,
                "retention_period": retention_period
            }
            
            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=4)
            
            QMessageBox.information(
                self,
                "저장 완료",
                "데이터베이스 설정이 저장되었습니다."
            )
            
            # 설정 변경 시그널 발생
            self.settings_changed.emit()
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "저장 오류",
                f"데이터베이스 설정을 저장하는 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def backup_database(self):
        """데이터베이스 백업"""
        try:
            # 데이터베이스 파일 경로
            db_path = self.db_path_input.text().strip()
            
            # 파일이 존재하는지 확인
            if not os.path.exists(db_path):
                QMessageBox.warning(
                    self,
                    "백업 오류",
                    "데이터베이스 파일이 존재하지 않습니다."
                )
                return
            
            # 백업 디렉토리 경로
            backup_dir = "backups"
            
            # 디렉토리가 없으면 생성
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # 백업 파일 이름 (현재 시간 포함)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"upbit_auto_trading_backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # 진행 상태 바 표시
            self.backup_progress.setVisible(True)
            self.backup_progress.setValue(0)
            
            # 백업 진행 (간단한 파일 복사)
            shutil.copy2(db_path, backup_path)
            
            # 진행 상태 바 업데이트
            self.backup_progress.setValue(100)
            
            QMessageBox.information(
                self,
                "백업 완료",
                f"데이터베이스가 성공적으로 백업되었습니다.\n백업 파일: {backup_path}"
            )
            
            # 잠시 후 진행 상태 바 숨기기
            import threading
            import time
            
            def hide_progress_bar():
                time.sleep(3)
                self.backup_progress.setVisible(False)
            
            threading.Thread(target=hide_progress_bar).start()
            
        except Exception as e:
            self.backup_progress.setVisible(False)
            QMessageBox.warning(
                self,
                "백업 오류",
                f"데이터베이스 백업 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def _restore_database(self):
        """데이터베이스 복원"""
        try:
            # 백업 디렉토리 경로
            backup_dir = "backups"
            
            # 디렉토리가 존재하는지 확인
            if not os.path.exists(backup_dir):
                QMessageBox.warning(
                    self,
                    "복원 오류",
                    "백업 디렉토리가 존재하지 않습니다."
                )
                return
            
            # 백업 파일 선택 대화상자 표시
            backup_file, _ = QFileDialog.getOpenFileName(
                self,
                "복원할 백업 파일 선택",
                backup_dir,
                "SQLite 데이터베이스 (*.db);;모든 파일 (*.*)"
            )
            
            # 파일이 선택되지 않았으면 종료
            if not backup_file:
                return
            
            # 현재 데이터베이스 파일 경로
            db_path = self.db_path_input.text().strip()
            
            # 복원 전 확인
            reply = QMessageBox.question(
                self,
                "복원 확인",
                f"현재 데이터베이스를 백업 파일로 대체합니다.\n계속하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
            
            # 진행 상태 바 표시
            self.backup_progress.setVisible(True)
            self.backup_progress.setValue(0)
            
            # 현재 데이터베이스 백업 (복원 실패 시 복구용)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_backup_filename = f"upbit_auto_trading_before_restore_{timestamp}.db"
            temp_backup_path = os.path.join(backup_dir, temp_backup_filename)
            
            # 현재 데이터베이스가 존재하면 백업
            if os.path.exists(db_path):
                shutil.copy2(db_path, temp_backup_path)
            
            self.backup_progress.setValue(50)
            
            # 백업 파일을 현재 데이터베이스로 복사
            shutil.copy2(backup_file, db_path)
            
            self.backup_progress.setValue(100)
            
            QMessageBox.information(
                self,
                "복원 완료",
                f"데이터베이스가 성공적으로 복원되었습니다.\n복원 전 백업: {temp_backup_path}"
            )
            
            # 현재 크기 업데이트
            self._update_current_size()
            
            # 잠시 후 진행 상태 바 숨기기
            import threading
            import time
            
            def hide_progress_bar():
                time.sleep(3)
                self.backup_progress.setVisible(False)
            
            threading.Thread(target=hide_progress_bar).start()
            
        except Exception as e:
            self.backup_progress.setVisible(False)
            QMessageBox.warning(
                self,
                "복원 오류",
                f"데이터베이스 복원 중 오류가 발생했습니다:\n{str(e)}"
            )