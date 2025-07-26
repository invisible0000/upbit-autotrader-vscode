"""
시뮬레이션 제어 위젯
원본: integrated_condition_manager.py의 create_simulation_area() 완전 복제
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QPushButton, 
                            QLabel, QGridLayout, QFrame)
from PyQt6.QtCore import pyqtSignal, Qt

# DataSourceSelectorWidget import
try:
    from .data_source_selector import DataSourceSelectorWidget
    DATA_SOURCE_AVAILABLE = True
except ImportError:
    DataSourceSelectorWidget = None
    DATA_SOURCE_AVAILABLE = False
    print("⚠️ DataSourceSelectorWidget를 찾을 수 없습니다.")


class SimulationControlWidget(QWidget):
    """케이스 시뮬레이션 제어 위젯 - 원본 완전 복제"""
    
    # 시그널 정의 (원본과 동일)
    simulation_requested = pyqtSignal(str)
    data_source_changed = pyqtSignal(str)  # 원본과 정확히 같은 시그널명
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_source_selector = None
        self.simulation_status = None
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화 - 원본 create_simulation_area() 완전 복제"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 시뮬레이션 영역 생성 (원본과 완전 동일)
        simulation_area = self.create_simulation_area()
        layout.addWidget(simulation_area)
    
    def create_simulation_area(self):
        """영역 3: 케이스 시뮬레이션 버튼들 (우측 상단) - 원본 완전 복제"""
        group = QGroupBox("🎮 시뮬레이션 컨트롤")
        # 하드코딩된 스타일 제거 - 애플리케이션 테마를 따름
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(3)
        
        # 데이터 소스 선택 위젯 추가 (원본과 동일)
        if DATA_SOURCE_AVAILABLE and DataSourceSelectorWidget is not None:
            try:
                self.data_source_selector = DataSourceSelectorWidget()
                self.data_source_selector.source_changed.connect(self.on_data_source_changed)
                layout.addWidget(self.data_source_selector)
                print("✅ DataSourceSelectorWidget 생성 성공")
            except Exception as e:
                print(f"⚠️ 데이터 소스 선택기 초기화 실패: {e}")
                # 대체 라벨
                fallback_label = QLabel("📊 가상 데이터로 시뮬레이션")
                fallback_label.setStyleSheet("""
                    background-color: #e7f3ff;
                    border: 1px solid #007bff;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 11px;
                    color: #007bff;
                    text-align: center;
                    font-weight: bold;
                """)
                fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(fallback_label)
        else:
            print("⚠️ DataSourceSelectorWidget 클래스를 로드할 수 없음")
            # 대체 라벨
            fallback_label = QLabel("📊 가상 데이터로 시뮬레이션")
            fallback_label.setStyleSheet("""
                background-color: #e7f3ff;
                border: 1px solid #007bff;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
                color: #007bff;
                text-align: center;
                font-weight: bold;
            """)
            fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(fallback_label)
        
        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #dee2e6; margin: 5px 0;")
        layout.addWidget(separator)
        
        # 시뮬레이션 버튼들 - 3행 2열 그리드 배치 (원본과 동일)
        simulation_buttons = [
            ("상승 추세", "상승 추세 시나리오", "#28a745"),
            ("하락 추세", "하락 추세 시나리오", "#dc3545"),
            ("급등", "급등 시나리오", "#007bff"),
            ("급락", "급락 시나리오", "#fd7e14"),
            ("횡보", "횡보 시나리오", "#6c757d"),
            ("이동평균 교차", "이동평균 교차", "#17a2b8")
        ]
        
        # 그리드 레이아웃 생성 (3행 2열)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(3)
        
        for i, (icon_text, tooltip, color) in enumerate(simulation_buttons):
            btn = QPushButton(icon_text)
            btn.setToolTip(tooltip)
            btn.setFixedHeight(40)  # 35에서 40으로 증가
            btn.setMinimumWidth(130)  # 120에서 130으로 증가
            
            # 스트레치 속성 강화 - 빈 공간을 채워서 커지도록
            from PyQt6.QtWidgets import QSizePolicy
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # 수평으로만 확장
            
            # 최대 폭 설정 제거로 더 많이 확장 가능
            btn.setMaximumWidth(16777215)  # Qt 최대값 설정
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 10px;
                    font-size: 12px;
                    font-weight: bold;
                    margin: 1px;
                    text-align: center;
                }}
                QPushButton:hover {{
                    background-color: {color}dd;
                }}
                QPushButton:pressed {{
                    background-color: {color}aa;
                }}
            """)
            btn.clicked.connect(lambda checked, scenario=icon_text: self.simulation_requested.emit(scenario))
            
            # 3행 2열로 배치
            row = i // 2
            col = i % 2
            grid_layout.addWidget(btn, row, col)
        
        # 그리드 컬럼에 stretch 적용
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        
        # 그리드 레이아웃을 메인 레이아웃에 추가
        layout.addLayout(grid_layout)
        
        layout.addStretch()
        
        # 시뮬레이션 상태 (애플리케이션 테마를 따름)
        self.simulation_status = QLabel("Status: 트리거를 선택하고 추세 버튼을 누르세요.")
        self.simulation_status.setObjectName("simulationStatus")  # QSS에서 스타일링하도록 objectName 설정
        self.simulation_status.setAlignment(Qt.AlignmentFlag.AlignLeft)  # 왼쪽 정렬
        layout.addWidget(self.simulation_status)
        
        return group
    
    def get_groupbox_style(self, border_color):
        """그룹박스 스타일 - 원본과 동일"""
        return f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 14px;
                border: 2px solid {border_color};
                border-radius: 8px;
                margin-top: 1ex;
                padding: 10px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: {border_color};
                background-color: white;
            }}
        """
    
    def update_status(self, message):
        """시뮬레이션 상태 업데이트"""
        if hasattr(self, 'simulation_status'):
            self.simulation_status.setText(message)
    
    def on_data_source_changed(self, source_type: str):
        """데이터 소스 변경 시 호출 - 원본과 동일"""
        try:
            print(f"📊 데이터 소스 변경: {source_type}")
            
            # 시뮬레이션 상태 업데이트 (원본과 동일)
            if hasattr(self, 'simulation_status'):
                self.simulation_status.setText(
                    f"📊 데이터 소스: {source_type}\n"
                    "시뮬레이션 준비 완료"
                )
            
            # 상위 위젯에 시그널 전달
            self.data_source_changed.emit(source_type)
            
        except Exception as e:
            print(f"❌ 데이터 소스 변경 중 오류: {e}")
            # 오류 시에도 조용히 처리 (원본과 동일)
            if hasattr(self, 'simulation_status'):
                self.simulation_status.setText("📊 데이터 소스: 시뮬레이션 모드\n준비 완료")
