"""
통합 조건 관리 화면 - 3x2 그리드 레이아웃
조건 빌더 + 트리거 관리 + 미니 테스트 통합 시스템
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QPushButton, QLabel, QMessageBox, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QSplitter, QFrame, QListWidget, QListWidgetItem,
    QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon

# 우리의 컴포넌트 시스템 import
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))
from components.condition_dialog import ConditionDialog
from components.condition_storage import ConditionStorage
from components.condition_loader import ConditionLoader

class IntegratedConditionManager(QWidget):
    """통합 조건 관리 화면 - 3x2 그리드 레이아웃"""
    
    # 시그널 정의
    condition_tested = pyqtSignal(dict, bool)  # 조건, 테스트 결과
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 통합 조건 관리 시스템")
        self.setMinimumSize(1400, 900)
        
        # 컴포넌트 초기화
        self.storage = ConditionStorage()
        self.loader = ConditionLoader(self.storage)
        self.selected_condition = None
        
        self.init_ui()
        self.load_trigger_list()
    
    def init_ui(self):
        """UI 초기화 - 3x2 그리드 레이아웃"""
        main_layout = QVBoxLayout(self)
        
        # 상단 제목
        self.create_header(main_layout)
        
        # 메인 그리드 레이아웃 (3x2)
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        
        # 1+4: 조건 빌더 (좌측, 세로 합쳐짐)
        self.condition_builder_area = self.create_condition_builder_area()
        grid_layout.addWidget(self.condition_builder_area, 0, 0, 2, 1)  # 2행에 걸쳐 배치
        
        # 2: 등록된 트리거 리스트 (중앙 상단)
        self.trigger_list_area = self.create_trigger_list_area()
        grid_layout.addWidget(self.trigger_list_area, 0, 1, 1, 1)
        
        # 3: 케이스 시뮬레이션 버튼들 (우측 상단)
        self.simulation_area = self.create_simulation_area()
        grid_layout.addWidget(self.simulation_area, 0, 2, 1, 1)
        
        # 5: 선택한 트리거 상세 정보 (중앙 하단)
        self.trigger_detail_area = self.create_trigger_detail_area()
        grid_layout.addWidget(self.trigger_detail_area, 1, 1, 1, 1)
        
        # 6: 작동 마커 차트 + 작동 기록 (우측 하단)
        self.test_result_area = self.create_test_result_area()
        grid_layout.addWidget(self.test_result_area, 1, 2, 1, 1)
        
        # 그리드 비율 설정 (3:2:2)
        grid_layout.setColumnStretch(0, 3)  # 조건 빌더
        grid_layout.setColumnStretch(1, 2)  # 트리거 관리
        grid_layout.setColumnStretch(2, 2)  # 시뮬레이션
        
        # 행 비율 설정 (1:1)
        grid_layout.setRowStretch(0, 1)
        grid_layout.setRowStretch(1, 1)
        
        main_layout.addWidget(grid_widget)
        
        print("✅ 통합 조건 관리 시스템 UI 초기화 완료")
    
    def create_header(self, layout):
        """상단 헤더 생성"""
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                          stop: 0 #667eea, stop: 1 #764ba2);
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        
        # 제목
        title_label = QLabel("🎯 통합 조건 관리 시스템")
        title_label.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: white;
            background: transparent;
        """)
        header_layout.addWidget(title_label)
        
        # 부제목
        subtitle_label = QLabel("조건 생성 → 트리거 관리 → 미니 테스트 통합 워크플로우")
        subtitle_label.setStyleSheet("""
            font-size: 12px; 
            color: #f8f9fa;
            background: transparent;
        """)
        header_layout.addWidget(subtitle_label)
        
        header_layout.addStretch()
        
        # 전체 새로고침 버튼
        refresh_btn = QPushButton("🔄 전체 새로고침")
        refresh_btn.setStyleSheet(self.get_white_button_style())
        refresh_btn.clicked.connect(self.refresh_all)
        header_layout.addWidget(refresh_btn)
        
        layout.addWidget(header_widget)
    
    def create_condition_builder_area(self):
        """영역 1+4: 조건 빌더 (좌측 통합)"""
        group = QGroupBox("🎯 조건 빌더")
        group.setStyleSheet(self.get_groupbox_style("#007bff"))
        layout = QVBoxLayout(group)
        
        try:
            # 우리의 조건 다이얼로그를 위젯으로 임베드
            self.condition_dialog = ConditionDialog()
            self.condition_dialog.setParent(group)
            
            # 다이얼로그를 위젯으로 변환 (창 모드 해제)
            self.condition_dialog.setWindowFlags(Qt.WindowType.Widget)
            
            # 시그널 연결
            self.condition_dialog.condition_saved.connect(self.on_condition_saved)
            
            layout.addWidget(self.condition_dialog)
            
        except Exception as e:
            print(f"❌ 조건 빌더 로딩 실패: {e}")
            
            # 대체 위젯
            error_label = QLabel(f"조건 빌더 로딩 실패: {e}")
            error_label.setStyleSheet("color: red; padding: 20px;")
            layout.addWidget(error_label)
        
        return group
    
    def create_trigger_list_area(self):
        """영역 2: 등록된 트리거 리스트 (중앙 상단)"""
        group = QGroupBox("📋 등록된 트리거 리스트")
        group.setStyleSheet(self.get_groupbox_style("#28a745"))
        layout = QVBoxLayout(group)
        
        # 트리거 검색
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍")
        search_layout.addWidget(search_label)
        
        self.search_input = self.create_search_input()
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # 트리거 트리 위젯
        self.trigger_tree = QTreeWidget()
        self.trigger_tree.setHeaderLabels(["트리거명", "변수", "조건", "카테고리"])
        self.trigger_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QTreeWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QTreeWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
        """)
        
        # 트리거 선택 시그널 연결
        self.trigger_tree.itemClicked.connect(self.on_trigger_selected)
        
        layout.addWidget(self.trigger_tree)
        
        # 하단 버튼들
        button_layout = QHBoxLayout()
        
        edit_btn = QPushButton("✏️ 편집")
        edit_btn.setStyleSheet(self.get_small_button_style("#ffc107"))
        edit_btn.clicked.connect(self.edit_selected_trigger)
        
        delete_btn = QPushButton("🗑️ 삭제")
        delete_btn.setStyleSheet(self.get_small_button_style("#dc3545"))
        delete_btn.clicked.connect(self.delete_selected_trigger)
        
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return group
    
    def create_simulation_area(self):
        """영역 3: 케이스 시뮬레이션 버튼들 (우측 상단)"""
        group = QGroupBox("🎮 케이스 시뮬레이션")
        group.setStyleSheet(self.get_groupbox_style("#6f42c1"))
        layout = QVBoxLayout(group)
        
        # 설명
        desc_label = QLabel("📈 가상 시나리오로 트리거 테스트")
        desc_label.setStyleSheet("color: #6c757d; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # 시뮬레이션 버튼들
        simulation_buttons = [
            ("📈 상승", "상승 추세 시나리오", "#28a745"),
            ("📉 하락", "하락 추세 시나리오", "#dc3545"),
            ("🚀 급등", "급등 시나리오", "#007bff"),
            ("💥 급락", "급락 시나리오", "#fd7e14"),
            ("➡️ 횡보", "횡보 시나리오", "#6c757d"),
            ("🔄 지수크로스", "이동평균 교차", "#17a2b8")
        ]
        
        for i, (icon_text, tooltip, color) in enumerate(simulation_buttons):
            btn = QPushButton(icon_text)
            btn.setToolTip(tooltip)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px;
                    font-size: 14px;
                    font-weight: bold;
                    margin: 2px;
                }}
                QPushButton:hover {{
                    background-color: {color}dd;
                    transform: scale(1.02);
                }}
                QPushButton:pressed {{
                    background-color: {color}aa;
                }}
            """)
            btn.clicked.connect(lambda checked, scenario=icon_text: self.run_simulation(scenario))
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # 시뮬레이션 상태
        self.simulation_status = QLabel("💡 트리거를 선택하고 시나리오를 클릭하세요")
        self.simulation_status.setStyleSheet("""
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 8px;
            font-size: 11px;
            color: #495057;
        """)
        layout.addWidget(self.simulation_status)
        
        return group
    
    def create_trigger_detail_area(self):
        """영역 5: 선택한 트리거 상세 정보 (중앙 하단)"""
        group = QGroupBox("📊 트리거 상세 정보")
        group.setStyleSheet(self.get_groupbox_style("#17a2b8"))
        layout = QVBoxLayout(group)
        
        # 상세 정보 텍스트
        self.trigger_detail_text = QTextEdit()
        self.trigger_detail_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f8f9fa;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)
        self.trigger_detail_text.setReadOnly(True)
        self.trigger_detail_text.setPlainText("트리거를 선택하면 상세 정보가 표시됩니다.")
        layout.addWidget(self.trigger_detail_text)
        
        # 빠른 액션 버튼들
        action_layout = QHBoxLayout()
        
        test_btn = QPushButton("🧪 빠른 테스트")
        test_btn.setStyleSheet(self.get_small_button_style("#007bff"))
        test_btn.clicked.connect(self.quick_test_trigger)
        
        copy_btn = QPushButton("📋 복사")
        copy_btn.setStyleSheet(self.get_small_button_style("#6c757d"))
        copy_btn.clicked.connect(self.copy_trigger_info)
        
        action_layout.addWidget(test_btn)
        action_layout.addWidget(copy_btn)
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
        
        return group
    
    def create_test_result_area(self):
        """영역 6: 작동 마커 차트 + 작동 기록 (우측 하단)"""
        group = QGroupBox("📈 테스트 결과 & 작동 기록")
        group.setStyleSheet(self.get_groupbox_style("#fd7e14"))
        layout = QVBoxLayout(group)
        
        # 미니 차트 영역 (모의)
        chart_label = QLabel("📊 미니 차트 영역")
        chart_label.setStyleSheet("""
            border: 2px dashed #fd7e14;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            color: #fd7e14;
            font-weight: bold;
            background-color: #fff3cd;
        """)
        chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(chart_label)
        
        # 작동 기록 리스트
        self.test_history_list = QListWidget()
        self.test_history_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
                max-height: 150px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #fff3cd;
                color: #856404;
            }
        """)
        
        # 기본 항목들 추가
        self.add_test_history_item("시스템 시작", "ready")
        
        layout.addWidget(QLabel("🕐 작동 기록:"))
        layout.addWidget(self.test_history_list)
        
        return group
    
    def create_search_input(self):
        """검색 입력 생성"""
        from PyQt6.QtWidgets import QLineEdit
        
        search_input = QLineEdit()
        search_input.setPlaceholderText("트리거 검색...")
        search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
        """)
        search_input.textChanged.connect(self.filter_triggers)
        return search_input
    
    def get_groupbox_style(self, color):
        """그룹박스 스타일 생성"""
        return f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {color};
                border-radius: 8px;
                margin: 5px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
                color: {color};
            }}
        """
    
    def get_white_button_style(self):
        """흰색 버튼 스타일"""
        return """
            QPushButton {
                background-color: white;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
            }
        """
    
    def get_small_button_style(self, color):
        """작은 버튼 스타일"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
        """
    
    def load_trigger_list(self):
        """트리거 리스트 로드"""
        try:
            conditions = self.storage.get_all_conditions()
            self.trigger_tree.clear()
            
            # 카테고리별 그룹화
            category_groups = {}
            
            for condition in conditions:
                category = condition.get('category', 'unknown')
                if category not in category_groups:
                    category_groups[category] = []
                category_groups[category].append(condition)
            
            # 트리에 추가
            for category, items in category_groups.items():
                category_item = QTreeWidgetItem([f"📁 {category.upper()}", "", "", ""])
                category_item.setExpanded(True)
                
                for condition in items:
                    name = condition.get('name', 'Unknown')
                    variable = condition.get('variable_name', 'Unknown')
                    operator = condition.get('operator', '?')
                    target = condition.get('target_value', '?')
                    
                    condition_text = f"{operator} {target}"
                    
                    item = QTreeWidgetItem([name, variable, condition_text, category])
                    item.setData(0, Qt.ItemDataRole.UserRole, condition)  # 조건 데이터 저장
                    category_item.addChild(item)
                
                self.trigger_tree.addTopLevelItem(category_item)
            
            print(f"✅ {len(conditions)}개 트리거 로드 완료")
            
        except Exception as e:
            print(f"❌ 트리거 리스트 로드 실패: {e}")
    
    def on_condition_saved(self, condition_data):
        """조건 저장 완료 시 호출"""
        print(f"✅ 새 조건 저장: {condition_data.get('name', 'Unknown')}")
        
        # 트리거 리스트 새로고침
        self.load_trigger_list()
        
        # 상태 업데이트
        self.simulation_status.setText(f"✅ '{condition_data.get('name', 'Unknown')}' 저장 완료!")
        
        # 테스트 기록 추가
        self.add_test_history_item(f"조건 저장: {condition_data.get('name', 'Unknown')}", "save")
    
    def on_trigger_selected(self, item, column):
        """트리거 선택 시 호출"""
        condition_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not condition_data:
            return
        
        self.selected_condition = condition_data
        
        # 상세 정보 표시
        detail_text = f"""
🎯 조건명: {condition_data.get('name', 'Unknown')}
📝 설명: {condition_data.get('description', 'No description')}

📊 변수 정보:
  • 변수: {condition_data.get('variable_name', 'Unknown')}
  • 파라미터: {condition_data.get('variable_params', {})}

⚖️ 비교 설정:
  • 연산자: {condition_data.get('operator', 'Unknown')}
  • 비교 타입: {condition_data.get('comparison_type', 'Unknown')}
  • 대상값: {condition_data.get('target_value', 'Unknown')}

🏷️ 카테고리: {condition_data.get('category', 'Unknown')}
🕐 생성일: {condition_data.get('created_at', 'Unknown')}
        """
        
        self.trigger_detail_text.setPlainText(detail_text.strip())
        
        # 시뮬레이션 상태 업데이트
        self.simulation_status.setText(f"🎯 '{condition_data.get('name', 'Unknown')}' 선택됨 - 시나리오를 클릭하세요")
        
        print(f"📊 트리거 선택: {condition_data.get('name', 'Unknown')}")
    
    def run_simulation(self, scenario):
        """시뮬레이션 실행"""
        if not self.selected_condition:
            QMessageBox.warning(self, "⚠️ 경고", "먼저 트리거를 선택해주세요.")
            return
        
        condition_name = self.selected_condition.get('name', 'Unknown')
        
        # 시뮬레이션 상태 업데이트
        self.simulation_status.setText(f"🔄 {scenario} 시나리오 실행 중...")
        
        # 간단한 시뮬레이션 로직 (실제로는 더 복잡할 것)
        import random
        result = random.choice([True, False])  # 임시 랜덤 결과
        
        # 결과 표시
        if result:
            self.simulation_status.setText(f"✅ {scenario}: 트리거 조건 만족!")
            status_icon = "✅"
        else:
            self.simulation_status.setText(f"❌ {scenario}: 트리거 조건 불만족")
            status_icon = "❌"
        
        # 테스트 기록 추가
        self.add_test_history_item(f"{status_icon} {scenario} - {condition_name}", "test")
        
        # 시그널 발생
        self.condition_tested.emit(self.selected_condition, result)
        
        print(f"🎮 시뮬레이션 실행: {scenario} → {result}")
    
    def add_test_history_item(self, text, item_type):
        """테스트 기록 항목 추가"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        type_icons = {
            "ready": "🟢",
            "save": "💾",
            "test": "🧪",
            "error": "❌"
        }
        
        icon = type_icons.get(item_type, "ℹ️")
        full_text = f"{timestamp} {icon} {text}"
        
        item = QListWidgetItem(full_text)
        self.test_history_list.addItem(item)
        
        # 자동 스크롤
        self.test_history_list.scrollToBottom()
        
        # 최대 100개 항목만 유지
        if self.test_history_list.count() > 100:
            self.test_history_list.takeItem(0)
    
    def filter_triggers(self, text):
        """트리거 필터링"""
        # TODO: 검색 기능 구현
        print(f"🔍 검색: {text}")
    
    def edit_selected_trigger(self):
        """선택한 트리거 편집"""
        if not self.selected_condition:
            QMessageBox.warning(self, "⚠️ 경고", "편집할 트리거를 선택해주세요.")
            return
        
        # TODO: 편집 기능 구현
        QMessageBox.information(self, "🚧 개발 중", "트리거 편집 기능을 구현 예정입니다.")
    
    def delete_selected_trigger(self):
        """선택한 트리거 삭제"""
        if not self.selected_condition:
            QMessageBox.warning(self, "⚠️ 경고", "삭제할 트리거를 선택해주세요.")
            return
        
        # TODO: 삭제 기능 구현
        QMessageBox.information(self, "🚧 개발 중", "트리거 삭제 기능을 구현 예정입니다.")
    
    def quick_test_trigger(self):
        """선택한 트리거 빠른 테스트"""
        if not self.selected_condition:
            QMessageBox.warning(self, "⚠️ 경고", "테스트할 트리거를 선택해주세요.")
            return
        
        # 기본 시나리오로 빠른 테스트
        self.run_simulation("빠른 테스트")
    
    def copy_trigger_info(self):
        """트리거 정보 클립보드 복사"""
        if not self.selected_condition:
            QMessageBox.warning(self, "⚠️ 경고", "복사할 트리거를 선택해주세요.")
            return
        
        # TODO: 클립보드 복사 기능 구현
        QMessageBox.information(self, "📋 복사", "트리거 정보가 클립보드에 복사되었습니다.")
    
    def refresh_all(self):
        """전체 새로고침"""
        try:
            # 트리거 리스트 새로고침
            self.load_trigger_list()
            
            # 조건 빌더 새로고침
            if hasattr(self.condition_dialog, 'refresh_data'):
                self.condition_dialog.refresh_data()
            
            # 상태 초기화
            self.simulation_status.setText("🔄 전체 새로고침 완료!")
            self.add_test_history_item("전체 새로고침 완료", "ready")
            
            print("✅ 전체 새로고침 완료")
            
        except Exception as e:
            print(f"❌ 새로고침 실패: {e}")
            QMessageBox.warning(self, "오류", f"새로고침 중 오류가 발생했습니다:\n{e}")

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    window = IntegratedConditionManager()
    window.show()
    
    sys.exit(app.exec())
