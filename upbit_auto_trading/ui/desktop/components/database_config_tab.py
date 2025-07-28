"""
데이터베이스 설정 탭 - 메인 윈도우 설정 화면
동적 데이터베이스 파일 선택 및 교체 기능

Author: Database Structure Unification Task
Created: 2025.07.28
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QFileDialog, QMessageBox, QGroupBox, QFormLayout,
    QCheckBox, QTextEdit, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QIcon

from ...config.database_paths import DatabasePaths, get_current_config
from ...utils.global_db_manager import DatabaseManager


class DatabaseSwitchWorker(QThread):
    """데이터베이스 교체 작업을 백그라운드에서 처리하는 워커"""
    
    progress = pyqtSignal(int, str)  # (progress_percent, status_message)
    finished = pyqtSignal(bool, str)  # (success, message)
    
    def __init__(self, new_config: Dict[str, str]):
        super().__init__()
        self.new_config = new_config
        
    def run(self):
        try:
            self.progress.emit(10, "데이터베이스 연결 종료 중...")
            
            # 1. 기존 연결 모두 종료
            db_manager = DatabaseManager()
            db_manager.close_all_connections()
            
            self.progress.emit(30, "새 데이터베이스 파일 검증 중...")
            
            # 2. 새 DB 파일들 존재 확인
            for db_type, file_path in self.new_config.items():
                if not os.path.exists(file_path):
                    self.finished.emit(False, f"데이터베이스 파일을 찾을 수 없습니다: {file_path}")
                    return
                    
            self.progress.emit(50, "데이터베이스 구조 검증 중...")
            
            # 3. DB 파일 구조 검증 (간단한 연결 테스트)
            temp_manager = DatabaseManager()
            for db_type, file_path in self.new_config.items():
                try:
                    # 임시로 연결해서 구조 확인
                    conn = temp_manager._create_connection(file_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                    conn.close()
                except Exception as e:
                    self.finished.emit(False, f"데이터베이스 파일이 손상되었거나 올바르지 않습니다: {db_type}")
                    return
                    
            self.progress.emit(70, "설정 파일 업데이트 중...")
            
            # 4. 설정 파일 업데이트
            config_path = "config/database_config.yaml"
            import yaml
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            else:
                config = {}
                
            # 사용자 정의 경로로 설정
            config['user_defined'] = {
                'settings_db': self.new_config.get('settings', ''),
                'strategies_db': self.new_config.get('strategies', ''),
                'market_data_db': self.new_config.get('market_data', ''),
                'active': True
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
            self.progress.emit(90, "새 데이터베이스 초기화 중...")
            
            # 5. 새 DB 매니저 초기화
            new_manager = DatabaseManager()
            new_manager.reload_configuration()
            
            self.progress.emit(100, "데이터베이스 교체 완료!")
            self.finished.emit(True, "데이터베이스가 성공적으로 교체되었습니다.")
            
        except Exception as e:
            self.finished.emit(False, f"데이터베이스 교체 중 오류 발생: {str(e)}")


class DatabaseConfigTab(QWidget):
    """데이터베이스 설정 탭 위젯"""
    
    # 프로그램 재시작 요청 시그널
    restart_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_config = get_current_config()
        self.pending_config = {}
        self.init_ui()
        self.load_current_settings()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 제목
        title_label = QLabel("📊 데이터베이스 설정")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 현재 설정 그룹
        self.create_current_config_group(layout)
        
        # 데이터베이스 파일 선택 그룹
        self.create_file_selection_group(layout)
        
        # 고급 옵션 그룹
        self.create_advanced_options_group(layout)
        
        # 버튼들
        self.create_action_buttons(layout)
        
        # 진행 상황 표시
        self.create_progress_section(layout)
        
        layout.addStretch()
        
    def create_current_config_group(self, parent_layout):
        """현재 설정 정보 그룹"""
        group = QGroupBox("📋 현재 데이터베이스 정보")
        layout = QFormLayout(group)
        
        self.current_settings_label = QLabel("설정 DB: ")
        self.current_strategies_label = QLabel("전략 DB: ")
        self.current_market_data_label = QLabel("시장데이터 DB: ")
        
        layout.addRow("⚙️ 설정:", self.current_settings_label)
        layout.addRow("🎯 전략:", self.current_strategies_label)
        layout.addRow("📈 시장데이터:", self.current_market_data_label)
        
        parent_layout.addWidget(group)
        
    def create_file_selection_group(self, parent_layout):
        """파일 선택 그룹"""
        group = QGroupBox("📁 새 데이터베이스 파일 선택")
        layout = QVBoxLayout(group)
        
        # 설정 DB
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("⚙️ 설정 DB:"))
        self.settings_path_edit = QLineEdit()
        self.settings_path_edit.setPlaceholderText("settings.sqlite3 파일을 선택하세요...")
        self.settings_browse_btn = QPushButton("찾아보기")
        self.settings_browse_btn.clicked.connect(lambda: self.browse_database_file('settings'))
        
        settings_layout.addWidget(self.settings_path_edit, 2)
        settings_layout.addWidget(self.settings_browse_btn)
        layout.addLayout(settings_layout)
        
        # 전략 DB
        strategies_layout = QHBoxLayout()
        strategies_layout.addWidget(QLabel("🎯 전략 DB:"))
        self.strategies_path_edit = QLineEdit()
        self.strategies_path_edit.setPlaceholderText("strategies.sqlite3 파일을 선택하세요...")
        self.strategies_browse_btn = QPushButton("찾아보기")
        self.strategies_browse_btn.clicked.connect(lambda: self.browse_database_file('strategies'))
        
        strategies_layout.addWidget(self.strategies_path_edit, 2)
        strategies_layout.addWidget(self.strategies_browse_btn)
        layout.addLayout(strategies_layout)
        
        # 시장데이터 DB
        market_layout = QHBoxLayout()
        market_layout.addWidget(QLabel("📈 시장데이터 DB:"))
        self.market_data_path_edit = QLineEdit()
        self.market_data_path_edit.setPlaceholderText("market_data.sqlite3 파일을 선택하세요...")
        self.market_browse_btn = QPushButton("찾아보기")
        self.market_browse_btn.clicked.connect(lambda: self.browse_database_file('market_data'))
        
        market_layout.addWidget(self.market_data_path_edit, 2)
        market_layout.addWidget(self.market_browse_btn)
        layout.addLayout(market_layout)
        
        parent_layout.addWidget(group)
        
    def create_advanced_options_group(self, parent_layout):
        """고급 옵션 그룹"""
        group = QGroupBox("🔧 고급 옵션")
        layout = QVBoxLayout(group)
        
        self.backup_before_switch = QCheckBox("교체 전 현재 데이터베이스 백업 생성")
        self.backup_before_switch.setChecked(True)
        layout.addWidget(self.backup_before_switch)
        
        self.validate_before_switch = QCheckBox("교체 전 새 데이터베이스 구조 검증")
        self.validate_before_switch.setChecked(True)
        layout.addWidget(self.validate_before_switch)
        
        self.auto_restart = QCheckBox("교체 완료 후 자동으로 프로그램 재시작")
        self.auto_restart.setChecked(False)
        layout.addWidget(self.auto_restart)
        
        parent_layout.addWidget(group)
        
    def create_action_buttons(self, parent_layout):
        """액션 버튼들"""
        button_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("🔍 변경사항 미리보기")
        self.preview_btn.clicked.connect(self.preview_changes)
        
        self.apply_btn = QPushButton("✅ 데이터베이스 교체")
        self.apply_btn.clicked.connect(self.apply_database_change)
        self.apply_btn.setEnabled(False)
        
        self.reset_btn = QPushButton("🔄 기본값으로 되돌리기")
        self.reset_btn.clicked.connect(self.reset_to_default)
        
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        
        parent_layout.addLayout(button_layout)
        
    def create_progress_section(self, parent_layout):
        """진행 상황 섹션"""
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        parent_layout.addWidget(line)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        parent_layout.addWidget(self.progress_bar)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setVisible(False)
        parent_layout.addWidget(self.status_text)
        
    def load_current_settings(self):
        """현재 설정 로드"""
        try:
            config = get_current_config()
            
            self.current_settings_label.setText(config.get('settings_db', 'N/A'))
            self.current_strategies_label.setText(config.get('strategies_db', 'N/A'))
            self.current_market_data_label.setText(config.get('market_data_db', 'N/A'))
            
        except Exception as e:
            self.status_text.setText(f"설정 로드 오류: {str(e)}")
            
    def browse_database_file(self, db_type: str):
        """데이터베이스 파일 선택 대화상자"""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle(f"{db_type} 데이터베이스 파일 선택")
        file_dialog.setNameFilter("SQLite 데이터베이스 (*.sqlite3 *.db *.sqlite)")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                
                if db_type == 'settings':
                    self.settings_path_edit.setText(file_path)
                elif db_type == 'strategies':
                    self.strategies_path_edit.setText(file_path)
                elif db_type == 'market_data':
                    self.market_data_path_edit.setText(file_path)
                    
                self.check_apply_button_state()
                
    def check_apply_button_state(self):
        """적용 버튼 활성화 상태 체크"""
        settings_path = self.settings_path_edit.text().strip()
        strategies_path = self.strategies_path_edit.text().strip()
        market_data_path = self.market_data_path_edit.text().strip()
        
        # 모든 경로가 입력되었고, 최소 하나는 현재 설정과 다른 경우에만 활성화
        all_filled = all([settings_path, strategies_path, market_data_path])
        
        current_config = get_current_config()
        any_changed = (
            settings_path != current_config.get('settings_db', '') or
            strategies_path != current_config.get('strategies_db', '') or
            market_data_path != current_config.get('market_data_db', '')
        )
        
        self.apply_btn.setEnabled(all_filled and any_changed)
        
    def preview_changes(self):
        """변경사항 미리보기"""
        current_config = get_current_config()
        
        preview_text = "📋 데이터베이스 교체 미리보기\n\n"
        
        # 설정 DB
        new_settings = self.settings_path_edit.text().strip()
        if new_settings and new_settings != current_config.get('settings_db', ''):
            preview_text += f"⚙️ 설정 DB 변경:\n"
            preview_text += f"   현재: {current_config.get('settings_db', 'N/A')}\n"
            preview_text += f"   변경: {new_settings}\n\n"
            
        # 전략 DB
        new_strategies = self.strategies_path_edit.text().strip()
        if new_strategies and new_strategies != current_config.get('strategies_db', ''):
            preview_text += f"🎯 전략 DB 변경:\n"
            preview_text += f"   현재: {current_config.get('strategies_db', 'N/A')}\n"
            preview_text += f"   변경: {new_strategies}\n\n"
            
        # 시장데이터 DB
        new_market_data = self.market_data_path_edit.text().strip()
        if new_market_data and new_market_data != current_config.get('market_data_db', ''):
            preview_text += f"📈 시장데이터 DB 변경:\n"
            preview_text += f"   현재: {current_config.get('market_data_db', 'N/A')}\n"
            preview_text += f"   변경: {new_market_data}\n\n"
            
        if preview_text == "📋 데이터베이스 교체 미리보기\n\n":
            preview_text += "변경사항이 없습니다."
            
        preview_text += "\n⚠️ 주의사항:\n"
        preview_text += "- 데이터베이스 교체 시 모든 작업이 중단됩니다\n"
        preview_text += "- 교체 완료 후 프로그램 재시작이 필요합니다\n"
        preview_text += "- 백업 옵션이 선택된 경우 현재 DB가 백업됩니다\n"
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("변경사항 미리보기")
        msg_box.setText(preview_text)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()
        
    def apply_database_change(self):
        """데이터베이스 교체 적용"""
        # 확인 대화상자
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("⚠️ 데이터베이스 교체 확인")
        msg_box.setText(
            "데이터베이스를 교체하시겠습니까?\n\n"
            "⚠️ 경고: DB가 교체되면 모든 작업을 멈추고\n"
            "프로그램을 재시작해야 합니다.\n\n"
            "DB 경로를 바꾸시겠습니까?"
        )
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        if msg_box.exec() != QMessageBox.StandardButton.Yes:
            return
            
        # 새 설정 준비
        new_config = {
            'settings': self.settings_path_edit.text().strip(),
            'strategies': self.strategies_path_edit.text().strip(),
            'market_data': self.market_data_path_edit.text().strip()
        }
        
        # 진행 상황 UI 표시
        self.progress_bar.setVisible(True)
        self.status_text.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 버튼들 비활성화
        self.apply_btn.setEnabled(False)
        self.preview_btn.setEnabled(False)
        
        # 백그라운드 작업 시작
        self.worker = DatabaseSwitchWorker(new_config)
        self.worker.progress.connect(self.on_progress_update)
        self.worker.finished.connect(self.on_switch_finished)
        self.worker.start()
        
    @pyqtSlot(int, str)
    def on_progress_update(self, progress: int, message: str):
        """진행 상황 업데이트"""
        self.progress_bar.setValue(progress)
        self.status_text.append(f"[{progress}%] {message}")
        
    @pyqtSlot(bool, str)
    def on_switch_finished(self, success: bool, message: str):
        """데이터베이스 교체 완료"""
        self.status_text.append(f"\n✅ 완료: {message}")
        
        if success:
            # 성공 메시지
            success_msg = QMessageBox(self)
            success_msg.setWindowTitle("✅ 교체 완료")
            success_msg.setText(
                "데이터베이스가 성공적으로 교체되었습니다!\n\n"
                "변경사항을 적용하려면 프로그램을 재시작해야 합니다."
            )
            success_msg.setIcon(QMessageBox.Icon.Information)
            
            if self.auto_restart.isChecked():
                success_msg.setText(
                    success_msg.text() + "\n\n자동 재시작이 시작됩니다."
                )
                
            success_msg.exec()
            
            # 재시작 요청
            if self.auto_restart.isChecked():
                self.restart_requested.emit()
            else:
                # 수동 재시작 안내
                restart_msg = QMessageBox(self)
                restart_msg.setWindowTitle("🔄 재시작 필요")
                restart_msg.setText(
                    "지금 프로그램을 재시작하시겠습니까?\n\n"
                    "재시작하지 않으면 일부 기능이 정상적으로\n"
                    "작동하지 않을 수 있습니다."
                )
                restart_msg.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if restart_msg.exec() == QMessageBox.StandardButton.Yes:
                    self.restart_requested.emit()
        else:
            # 실패 메시지
            error_msg = QMessageBox(self)
            error_msg.setWindowTitle("❌ 교체 실패")
            error_msg.setText(f"데이터베이스 교체에 실패했습니다:\n\n{message}")
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.exec()
            
        # UI 정리
        self.progress_bar.setVisible(False)
        self.apply_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.load_current_settings()  # 현재 설정 다시 로드
        
    def reset_to_default(self):
        """기본값으로 되돌리기"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("기본값으로 되돌리기")
        msg_box.setText(
            "데이터베이스 설정을 기본값으로 되돌리시겠습니까?\n\n"
            "이 작업은 사용자 정의 데이터베이스 경로를 제거하고\n"
            "시스템 기본 경로를 사용합니다."
        )
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            try:
                # 설정 파일에서 사용자 정의 설정 제거
                config_path = "config/database_config.yaml"
                if os.path.exists(config_path):
                    import yaml
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                        
                    if 'user_defined' in config:
                        config['user_defined']['active'] = False
                        
                    with open(config_path, 'w', encoding='utf-8') as f:
                        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                        
                # UI 초기화
                self.settings_path_edit.clear()
                self.strategies_path_edit.clear()
                self.market_data_path_edit.clear()
                
                self.load_current_settings()
                
                QMessageBox.information(
                    self, "완료", 
                    "기본값으로 되돌렸습니다.\n변경사항을 적용하려면 프로그램을 재시작하세요."
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self, "오류", 
                    f"기본값으로 되돌리는 중 오류가 발생했습니다:\n{str(e)}"
                )
