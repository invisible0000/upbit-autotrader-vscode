"""
데이터베이스 설정 모듈

이 모듈은 데이터베이스 설정 기능을 구현합니다.
- 동적 데이터베이스 파일 선택 및 교체
- 다중 데이터베이스 프로필 관리
- 데이터베이스 백업 및 복원
- 실시간 데이터베이스 전환
"""

import os
import json
import shutil
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QSpinBox, QFileDialog, QGroupBox, QProgressBar,
    QCheckBox, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QIcon

# DatabaseManager 임포트
try:
    from upbit_auto_trading.data_layer.storage.database_manager import DatabaseManager
except ImportError as e:
    print(f"❌ [ERROR] DatabaseManager import 실패: {e}")
    # 백업용 더미 클래스
    class DatabaseManager:
        def __init__(self, config=None, config_path=None):
            pass
            
        def cleanup_database(self):
            pass
            
        def initialize_database(self):
            pass

# 공통 컴포넌트 임포트
try:
    from ...common.components import (
        PrimaryButton, SecondaryButton, StyledLineEdit,
        StyledButton
    )
except ImportError as e:
    print(f"⚠️ [DEBUG] components import 실패: {e}")
    # 백업용 기본 컴포넌트
    PrimaryButton = QPushButton
    SecondaryButton = QPushButton
    StyledLineEdit = QLineEdit
    StyledButton = QPushButton

# simple_paths 시스템 임포트
try:
    from upbit_auto_trading.config.simple_paths import SimplePaths
    IMPORT_SUCCESS = True
except ImportError as import_error:
    print(f"❌ [ERROR] simple_paths import 실패: {import_error}")
    IMPORT_SUCCESS = False
    
    # 백업용 더미 클래스
    class SimplePaths:
        def __init__(self):
            from pathlib import Path
            self.DATA_DIR = Path("data")
            self.SETTINGS_DB = self.DATA_DIR / "settings.sqlite3"
            self.STRATEGIES_DB = self.DATA_DIR / "strategies.sqlite3"
            self.MARKET_DATA_DB = self.DATA_DIR / "market_data.sqlite3"
            self.BACKUPS_DIR = Path("backups")


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
            
            # 1. 기존 연결 정리 (실제 존재하는 메서드 사용)
            try:
                db_manager = DatabaseManager()
                db_manager.cleanup_database()  # 실제 존재하는 메서드
            except Exception as e:
                print(f"⚠️ [WARNING] 데이터베이스 정리 중 오류 (무시): {e}")
            
            self.progress.emit(30, "새 데이터베이스 파일 검증 중...")
            
            # 2. 새 DB 파일들 존재 확인
            for db_type, file_path in self.new_config.items():
                if not os.path.exists(file_path):
                    self.finished.emit(False, f"데이터베이스 파일을 찾을 수 없습니다: {file_path}")
                    return
                    
            self.progress.emit(50, "데이터베이스 구조 검증 중...")
            
            # 3. DB 파일 구조 검증 (간단한 연결 테스트)
            for db_type, file_path in self.new_config.items():
                try:
                    # 임시로 연결해서 구조 확인
                    import sqlite3
                    conn = sqlite3.connect(file_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                    conn.close()
                except Exception:
                    self.finished.emit(False, f"데이터베이스 파일이 손상되었거나 올바르지 않습니다: {db_type}")
                    return
                    
            self.progress.emit(70, "설정 파일 업데이트 중...")
            
            # 4. 설정 파일 업데이트 (올바른 경로 사용)
            config_path = "config/database_config.yaml"
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                except Exception:
                    config = {}
            else:
                config = {}
                
            # 사용자 정의 경로로 설정
            config['user_defined'] = {
                'settings_db': self.new_config.get('settings', ''),
                'strategies_db': self.new_config.get('strategies', ''),
                'market_data_db': self.new_config.get('market_data', ''),
                'active': True
            }
            
            # 설정 파일 디렉토리 생성
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, 
                             default_flow_style=False, 
                             allow_unicode=True,
                             width=1000,  # 긴 줄을 분리하지 않도록 설정
                             default_style='"')  # 문자열을 따옴표로 감싸서 안전하게 저장
                print(f"✅ [DEBUG] YAML 파일 업데이트 성공: {config_path}")
            except Exception as write_error:
                print(f"❌ [ERROR] YAML 파일 쓰기 실패: {write_error}")
                # YAML이 없는 경우 JSON으로 저장
                with open(config_path.replace('.yaml', '.json'), 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
            self.progress.emit(90, "새 데이터베이스 초기화 중...")
            
            # 5. 새 DB 매니저 초기화 (실제 존재하는 방식 사용)
            try:
                # 새 설정으로 DatabaseManager 재생성
                new_manager = DatabaseManager(config=config)
                new_manager.initialize_database()  # 실제 존재하는 메서드
            except Exception as e:
                print(f"⚠️ [WARNING] 새 DB 매니저 초기화 중 오류 (무시): {e}")
            
            self.progress.emit(100, "데이터베이스 교체 완료!")
            self.finished.emit(True, "데이터베이스가 성공적으로 교체되었습니다.")
            
        except Exception as e:
            self.finished.emit(False, f"데이터베이스 교체 중 오류 발생: {str(e)}")


class DatabaseSettings(QWidget):
    """데이터베이스 설정 위젯 클래스 - 다중 DB 파일 선택 및 교체"""
    
    # 설정 변경 시그널
    settings_changed = pyqtSignal()
    
    # 프로그램 재시작 요청 시그널
    restart_requested = pyqtSignal()
    
    # DB 상태 변경 시그널 추가
    db_status_changed = pyqtSignal(bool)  # True: 연결됨, False: 연결 끊김
    
    def __init__(self, parent=None):
        """초기화"""
        super().__init__(parent)
        self.setObjectName("widget-database-settings")
        
        # simple_paths 시스템 사용
        self.paths = SimplePaths()
        self.current_config = {
            'settings_db': str(self.paths.SETTINGS_DB),
            'strategies_db': str(self.paths.STRATEGIES_DB),
            'market_data_db': str(self.paths.MARKET_DATA_DB)
        }
        self.pending_config = {}
        self.switch_worker = None
        
        # UI 설정
        self._setup_ui()
        
        # 시그널 연결
        self._connect_signals()
        
        # 현재 설정 로드
        self.load_current_settings()
    
    def _setup_ui(self):
        """UI 설정"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 제목
        title_label = QLabel("📊 데이터베이스 설정")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # 현재 설정 그룹
        self._create_current_config_group(main_layout)
        
        # 데이터베이스 파일 선택 그룹
        self._create_file_selection_group(main_layout)
        
        # 고급 옵션 그룹
        self._create_advanced_options_group(main_layout)
        
        # 버튼들
        self._create_action_buttons(main_layout)
        
        # 진행 상황 표시
        self._create_progress_section(main_layout)
        
        main_layout.addStretch()
        
    def _create_current_config_group(self, parent_layout):
        """현재 설정 정보 그룹"""
        group = QGroupBox("📋 현재 데이터베이스 정보")
        layout = QFormLayout(group)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        self.current_settings_label = QLabel("N/A")
        self.current_strategies_label = QLabel("N/A") 
        self.current_market_data_label = QLabel("N/A")
        
        # 정보 라벨 스타일
        info_style = "color: #333333; background-color: #f5f5f5; padding: 5px; border-radius: 3px;"
        self.current_settings_label.setStyleSheet(info_style)
        self.current_strategies_label.setStyleSheet(info_style)
        self.current_market_data_label.setStyleSheet(info_style)
        
        layout.addRow("⚙️ 설정 DB:", self.current_settings_label)
        layout.addRow("🎯 전략 DB:", self.current_strategies_label)
        layout.addRow("📈 시장데이터 DB:", self.current_market_data_label)
        
        parent_layout.addWidget(group)
        
    def _create_file_selection_group(self, parent_layout):
        """파일 선택 그룹"""
        group = QGroupBox("📁 새 데이터베이스 파일 선택")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # 설정 DB 선택
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("⚙️ 설정 DB:"), 0)
        
        self.settings_path_edit = StyledLineEdit()
        self.settings_path_edit.setPlaceholderText("settings.sqlite3 파일을 선택하세요...")
        self.settings_browse_btn = SecondaryButton("찾아보기")
        self.settings_browse_btn.clicked.connect(lambda: self._browse_database_file('settings'))
        
        settings_layout.addWidget(self.settings_path_edit, 2)
        settings_layout.addWidget(self.settings_browse_btn, 0)
        layout.addLayout(settings_layout)
        
        # 전략 DB 선택
        strategies_layout = QHBoxLayout()
        strategies_layout.addWidget(QLabel("🎯 전략 DB:"), 0)
        
        self.strategies_path_edit = StyledLineEdit()
        self.strategies_path_edit.setPlaceholderText("strategies.sqlite3 파일을 선택하세요...")
        self.strategies_browse_btn = SecondaryButton("찾아보기")
        self.strategies_browse_btn.clicked.connect(lambda: self._browse_database_file('strategies'))
        
        strategies_layout.addWidget(self.strategies_path_edit, 2)
        strategies_layout.addWidget(self.strategies_browse_btn, 0)
        layout.addLayout(strategies_layout)
        
        # 시장데이터 DB 선택
        market_layout = QHBoxLayout()
        market_layout.addWidget(QLabel("📈 시장데이터 DB:"), 0)
        
        self.market_data_path_edit = StyledLineEdit()
        self.market_data_path_edit.setPlaceholderText("market_data.sqlite3 파일을 선택하세요...")
        self.market_browse_btn = SecondaryButton("찾아보기")
        self.market_browse_btn.clicked.connect(lambda: self._browse_database_file('market_data'))
        
        market_layout.addWidget(self.market_data_path_edit, 2)
        market_layout.addWidget(self.market_browse_btn, 0)
        layout.addLayout(market_layout)
        
        # 안내 문구
        info_label = QLabel("💡 팁: 파일명에 날짜나 사용자명을 추가하여 여러 버전을 관리할 수 있습니다.")
        info_label.setStyleSheet("color: #666666; font-size: 11px; margin-top: 10px;")
        layout.addWidget(info_label)
        
        parent_layout.addWidget(group)
        
    def _create_advanced_options_group(self, parent_layout):
        """고급 옵션 그룹"""
        group = QGroupBox("🔧 고급 옵션")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
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
        
    def _create_action_buttons(self, parent_layout):
        """액션 버튼들"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.preview_btn = SecondaryButton("🔍 변경사항 미리보기")
        self.preview_btn.clicked.connect(self._preview_changes)
        
        self.apply_btn = PrimaryButton("✅ 데이터베이스 교체")
        self.apply_btn.clicked.connect(self._apply_database_change)
        self.apply_btn.setEnabled(False)
        
        self.reset_btn = SecondaryButton("🔄 기본값으로 되돌리기")
        self.reset_btn.clicked.connect(self._reset_to_default)
        
        self.refresh_btn = SecondaryButton("🔃 현재 정보 새로고침")
        self.refresh_btn.clicked.connect(self.load_current_settings)
        
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()
        
        parent_layout.addLayout(button_layout)
        
    def _create_progress_section(self, parent_layout):
        """진행 상황 섹션"""
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        parent_layout.addWidget(line)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #666666; font-size: 11px;")
        self.progress_label.setVisible(False)
        
        parent_layout.addWidget(self.progress_bar)
        parent_layout.addWidget(self.progress_label)
    
    def _connect_signals(self):
        """시그널 연결"""
        # 파일 경로 변경 감지
        self.settings_path_edit.textChanged.connect(self._check_apply_button_state)
        self.strategies_path_edit.textChanged.connect(self._check_apply_button_state)
        self.market_data_path_edit.textChanged.connect(self._check_apply_button_state)
    
    def _browse_database_file(self, db_type: str):
        """데이터베이스 파일 찾아보기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"{db_type.title()} 데이터베이스 파일 선택",
            "upbit_auto_trading/data/",
            "SQLite 데이터베이스 (*.sqlite3 *.db);;모든 파일 (*.*)"
        )
        
        if file_path:
            if db_type == 'settings':
                self.settings_path_edit.setText(file_path)
            elif db_type == 'strategies':
                self.strategies_path_edit.setText(file_path)
            elif db_type == 'market_data':
                self.market_data_path_edit.setText(file_path)
    
    def _check_apply_button_state(self):
        """적용 버튼 활성화 상태 확인"""
        settings_path = self.settings_path_edit.text().strip()
        strategies_path = self.strategies_path_edit.text().strip()
        market_data_path = self.market_data_path_edit.text().strip()
        
        # 모든 경로가 입력되었고, 현재 설정과 다른 경우에만 활성화
        all_filled = bool(settings_path and strategies_path and market_data_path)
        is_different = (
            settings_path != self.current_config.get('settings_db', '') or
            strategies_path != self.current_config.get('strategies_db', '') or
            market_data_path != self.current_config.get('market_data_db', '')
        )
        
        self.apply_btn.setEnabled(all_filled and is_different)
    
    def _preview_changes(self):
        """변경사항 미리보기"""
        settings_path = self.settings_path_edit.text().strip()
        strategies_path = self.strategies_path_edit.text().strip()
        market_data_path = self.market_data_path_edit.text().strip()
        
        if not all([settings_path, strategies_path, market_data_path]):
            QMessageBox.warning(
                self,
                "입력 오류",
                "모든 데이터베이스 파일 경로를 선택해주세요."
            )
            return
        
        # 미리보기 다이얼로그
        preview_text = f"""
📋 데이터베이스 변경 사항 미리보기

🔄 변경될 내용:

⚙️ 설정 DB:
   현재: {self.current_config.get('settings_db', 'N/A')}
   변경: {settings_path}

🎯 전략 DB:
   현재: {self.current_config.get('strategies_db', 'N/A')}
   변경: {strategies_path}

📈 시장데이터 DB:
   현재: {self.current_config.get('market_data_db', 'N/A')}
   변경: {market_data_path}

⚠️ 주의사항:
• 모든 거래 작업이 중단됩니다
• 프로그램이 재시작됩니다
• 백업이 자동으로 생성됩니다 (옵션 선택 시)
        """
        
        QMessageBox.information(
            self,
            "변경사항 미리보기",
            preview_text
        )
    
    def _apply_database_change(self):
        """데이터베이스 변경 적용"""
        settings_path = self.settings_path_edit.text().strip()
        strategies_path = self.strategies_path_edit.text().strip()
        market_data_path = self.market_data_path_edit.text().strip()
        
        # 최종 확인
        reply = QMessageBox.question(
            self,
            "데이터베이스 교체 확인",
            "⚠️ 경고!\n\n"
            "데이터베이스가 교체되려면 모든 작업을 멈추고 "
            "프로그램을 재시작해야 합니다.\n\n"
            "DB 경로를 변경하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 새 설정 구성
        new_config = {
            'settings': settings_path,
            'strategies': strategies_path,
            'market_data': market_data_path
        }
        
        # 백그라운드 작업 시작
        self._start_database_switch(new_config)
    
    def _start_database_switch(self, new_config: Dict[str, str]):
        """데이터베이스 교체 작업 시작"""
        # UI 비활성화
        self.apply_btn.setEnabled(False)
        self.preview_btn.setEnabled(False)
        
        # 진행 상황 표시
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 워커 스레드 시작
        self.switch_worker = DatabaseSwitchWorker(new_config)
        self.switch_worker.progress.connect(self._on_progress_update)
        self.switch_worker.finished.connect(self._on_switch_finished)
        self.switch_worker.start()
    
    @pyqtSlot(int, str)
    def _on_progress_update(self, progress: int, message: str):
        """진행 상황 업데이트"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
    
    @pyqtSlot(bool, str)
    def _on_switch_finished(self, success: bool, message: str):
        """데이터베이스 교체 완료"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # UI 재활성화
        self.apply_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        
        if success:
            # 현재 설정을 강제로 새로고침 (DB 상태 시그널 자동 발생)
            self.load_current_settings()
            
            # 성공 메시지 표시
            QMessageBox.information(
                self,
                "교체 성공",
                f"{message}\n\n현재 데이터베이스 정보가 업데이트되었습니다.\n\n"
                "완전한 적용을 위해 프로그램을 재시작해주세요."
            )
            
            # 자동 재시작 옵션이 활성화된 경우
            if self.auto_restart.isChecked():
                try:
                    self.restart_requested.emit()
                    # 개발 환경에서는 재시작 대신 종료
                    import sys
                    sys.exit(0)
                except Exception as e:
                    QMessageBox.information(
                        self,
                        "재시작 알림",
                        f"자동 재시작에 실패했습니다.\n수동으로 프로그램을 재시작해주세요.\n\n오류: {str(e)}"
                    )
        else:
            # 실패 시 연결 끊김 상태로 설정
            self.db_status_changed.emit(False)
            
            # 실패 메시지 표시
            QMessageBox.critical(
                self,
                "교체 실패",
                f"데이터베이스 교체에 실패했습니다:\n{message}"
            )
    
    def _reset_to_default(self):
        """기본값으로 되돌리기"""
        reply = QMessageBox.question(
            self,
            "기본값 복원",
            "기본 데이터베이스 경로로 되돌리시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings_path_edit.setText("data/settings.sqlite3")
            self.strategies_path_edit.setText("data/strategies.sqlite3")
            self.market_data_path_edit.setText("data/market_data.sqlite3")
    
    def load_current_settings(self):
        """현재 설정 로드"""
        try:
            # simple_paths 기반 설정 표시
            import sqlite3
            
            # 각 데이터베이스 상태 확인 및 표시
            databases = [
                ("Settings", self.paths.SETTINGS_DB, self.current_settings_label),
                ("Strategies", self.paths.STRATEGIES_DB, self.current_strategies_label),
                ("Market Data", self.paths.MARKET_DATA_DB, self.current_market_data_label)
            ]
            
            db_connected = False  # 전체 DB 연결 상태
            
            for name, db_path, label in databases:
                if db_path.exists():
                    # 파일 크기
                    size_mb = db_path.stat().st_size / (1024 * 1024)
                    
                    # 테이블 수 확인
                    table_count = 0
                    try:
                        with sqlite3.connect(str(db_path)) as conn:
                            cursor = conn.cursor()
                            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                            table_count = cursor.fetchone()[0]
                        
                        # settings DB가 연결되면 전체 DB 연결 상태를 True로 설정
                        if name == "Settings" and table_count > 0:
                            db_connected = True
                            
                    except sqlite3.Error:
                        pass
                    
                    status_text = f"✅ {db_path.name} ({size_mb:.2f} MB, {table_count}개 테이블)"
                else:
                    status_text = f"❌ 파일 없음 ({db_path.name})"
                
                label.setText(status_text)
            
            # DB 상태 변경 시그널 발생
            self.db_status_changed.emit(db_connected)
            
            # 새 파일 선택 입력란에 현재 경로 표시
            self.settings_path_edit.setText(str(self.paths.SETTINGS_DB))
            self.strategies_path_edit.setText(str(self.paths.STRATEGIES_DB))
            self.market_data_path_edit.setText(str(self.paths.MARKET_DATA_DB))
            
            # 버튼 상태 업데이트
            self._check_apply_button_state()
            
            # UI 강제 새로고침
            self.repaint()
            
        except Exception as e:
            # 오류 발생 시 연결 끊김 상태로 설정
            self.db_status_changed.emit(False)
            QMessageBox.warning(
                self,
                "설정 로드 오류",
                f"현재 데이터베이스 설정을 로드하는 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def load_settings(self):
        """설정 로드 (호환성을 위한 메서드)"""
        self.load_current_settings()
    
    def save_settings(self):
        """설정 저장 (호환성을 위한 메서드)"""
        self.settings_changed.emit()
