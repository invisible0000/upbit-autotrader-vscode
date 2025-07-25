"""
데이터 소스 선택 UI 위젯
사용자가 시뮬레이션에 사용할 데이터 소스를 선택할 수 있는 UI
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QRadioButton, QButtonGroup, QGroupBox, QFrame)
from PyQt6.QtCore import pyqtSignal
import logging


class DataSourceSelectorWidget(QWidget):
    """데이터 소스 선택 위젯"""
    
    # 데이터 소스 변경 시그널
    source_changed = pyqtSignal(str)  # 선택된 소스 타입
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_source = None
        self.manager = None
        self.init_ui()
        self.load_available_sources()
        
    def init_ui(self):
        """UI 초기화 - 매우 컴팩트한 버전"""
        layout = QVBoxLayout(self)
        layout.setSpacing(3)  # 간격 더 줄이기
        layout.setContentsMargins(2, 2, 2, 2)  # 마진 최소화
        
        # 데이터 소스 선택 그룹 - 제목 간소화
        self.source_group = QGroupBox("데이터 소스")
        self.source_group.setStyleSheet("font-size: 10px; font-weight: bold;")  # 폰트 크기 줄이기
        source_layout = QVBoxLayout(self.source_group)
        source_layout.setSpacing(2)  # 그룹 내부 간격 줄이기
        source_layout.setContentsMargins(4, 8, 4, 4)  # 그룹 내부 마진 줄이기
        
        # 라디오 버튼 그룹
        self.button_group = QButtonGroup()
        self.source_buttons = {}
        
        # 버튼들이 추가될 컨테이너
        self.buttons_container = QWidget()
        self.buttons_layout = QVBoxLayout(self.buttons_container)
        self.buttons_layout.setSpacing(1)  # 버튼 간격 최소화
        source_layout.addWidget(self.buttons_container)
        
        layout.addWidget(self.source_group)
        
    def load_available_sources(self):
        """사용 가능한 데이터 소스 로드"""
        try:
            # 2단계 상위 디렉터리의 data_source_manager 임포트
            from ...data_source_manager import get_data_source_manager
            self.manager = get_data_source_manager()
            
            # 기존 버튼들 제거
            for button in self.source_buttons.values():
                button.deleteLater()
            self.source_buttons.clear()
            
            # 사용 가능한 소스들 가져오기
            available_sources = self.manager.get_available_sources()
            
            if not available_sources:
                no_source_label = QLabel("❌ 사용 가능한 데이터 소스가 없습니다.")
                no_source_label.setStyleSheet("color: red; font-weight: bold;")
                self.buttons_layout.addWidget(no_source_label)
                return
            
            # 각 소스별 라디오 버튼 생성
            for source_key, source_info in available_sources.items():
                self.create_source_button(source_key, source_info)
            
            # 현재 사용자 선호도 표시
            current_preference = self.manager.get_user_preference()
            if current_preference and current_preference in self.source_buttons:
                self.source_buttons[current_preference].setChecked(True)
                self.current_source = current_preference
            elif available_sources:
                # 기본값으로 추천 소스 선택
                recommended = None
                for key, info in available_sources.items():
                    if info.get("recommended", False):
                        recommended = key
                        break
                
                if recommended:
                    self.source_buttons[recommended].setChecked(True)
                    self.current_source = recommended
            
            logging.info(f"데이터 소스 로드 완료: {len(available_sources)}개")
            
        except Exception as e:
            logging.error(f"데이터 소스 로드 실패: {e}")
            error_label = QLabel(f"❌ 데이터 소스 로드 실패: {e}")
            error_label.setStyleSheet("color: red;")
            self.buttons_layout.addWidget(error_label)
    
    def create_source_button(self, source_key: str, source_info: dict):
        """개별 소스용 라디오 버튼 생성 - 매우 컴팩트한 버전"""
        # 매우 간단한 라디오 버튼 컨테이너
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                border: 1px solid #e0e0e0;
                border-radius: 3px;
                margin: 0px;
                padding: 2px;
            }
            QFrame:hover {
                border-color: #4a90e2;
            }
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)  # 매우 작은 패딩
        layout.setSpacing(4)
        
        # 라디오 버튼 (이름만, 폰트 크기 줄이기)
        radio_button = QRadioButton(source_info["name"])
        radio_button.setStyleSheet("font-size: 10px; font-weight: bold;")  # 하드코딩된 텍스트 색상 제거
        
        layout.addWidget(radio_button)
        
        # 추천 표시 (더 작게)
        if source_info.get("recommended", False):
            recommended_label = QLabel("🏆")
            recommended_label.setStyleSheet("font-size: 8px;")
            layout.addWidget(recommended_label)
        
        layout.addStretch()
        
        # 이벤트 연결
        radio_button.toggled.connect(lambda checked, key=source_key: self.on_source_selected(checked, key, source_info))
        
        # 버튼 그룹에 추가
        self.button_group.addButton(radio_button)
        self.source_buttons[source_key] = radio_button
        
        # 레이아웃에 추가
        self.buttons_layout.addWidget(container)
    
    def on_source_selected(self, checked: bool, source_key: str, source_info: dict):
        """데이터 소스 선택시 호출 - 자동 적용"""
        if checked:
            self.current_source = source_key
            
            # 선택하자마자 자동으로 적용
            if self.manager:
                try:
                    success = self.manager.set_user_preference(source_key)
                    if success:
                        self.source_changed.emit(source_key)
                        logging.info(f"데이터 소스 자동 적용: {source_key}")
                    else:
                        logging.error("데이터 소스 자동 적용 실패")
                except Exception as e:
                    logging.error(f"데이터 소스 자동 적용 중 오류: {e}")
    
    def get_current_source(self) -> str:
        """현재 선택된 데이터 소스 반환"""
        return self.current_source or ""
