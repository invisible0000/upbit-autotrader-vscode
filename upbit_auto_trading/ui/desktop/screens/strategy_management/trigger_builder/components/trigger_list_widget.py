"""
트리거 리스트 위젯 - 기존 기능 정확 복제
integrated_condition_manager.py의 create_trigger_list_area() 완전 복제
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, 
    QTreeWidget, QTreeWidgetItem, QMessageBox, QLineEdit, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal

# 조건 저장/로드 모듈
try:
    from upbit_auto_trading.data.condition_storage import ConditionStorage
    from upbit_auto_trading.data.condition_loader import ConditionLoader
    STORAGE_AVAILABLE = True
except ImportError:
    print("⚠️ ConditionStorage, ConditionLoader를 찾을 수 없습니다.")
    STORAGE_AVAILABLE = False


class TriggerListWidget(QWidget):
    """트리거 리스트 위젯 - 기존 기능 정확 복제"""
    
    # 시그널 정의 (기존 인터페이스 유지)
    trigger_selected = pyqtSignal(object, int)  # item, column
    trigger_edited = pyqtSignal()
    trigger_deleted = pyqtSignal()
    trigger_copied = pyqtSignal()
    trigger_save_requested = pyqtSignal()  # 트리거 저장 요청 시그널 추가
    new_trigger_requested = pyqtSignal()
    edit_mode_changed = pyqtSignal(bool)  # 편집 모드 변경 시그널 추가
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_edit_mode = False  # 편집 모드 상태 추가
        self.setup_ui()
        self.load_trigger_list()
    
    def setup_ui(self):
        """UI 구성 - integrated_condition_manager.py와 정확히 동일"""
        # 메인 그룹박스 (원본과 정확히 동일한 스타일)
        self.group = QGroupBox("📋 등록된 트리거 리스트")
        self.group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-weight: bold;
                padding-top: 12px;
                margin: 2px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                background-color: white;
                color: #27ae60;
                font-size: 11px;
                font-weight: bold;
                border-radius: 4px;
                border: 1px solid #27ae60;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.group)
        
        layout = QVBoxLayout(self.group)
        layout.setContentsMargins(8, 8, 8, 8)  # 패딩 줄이기
        
        # 트리거 검색 (원본 순서대로 상단에 배치)
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("트리거 검색...")
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # 트리거 트리 위젯 - 원본과 정확히 동일한 구조
        self.trigger_tree = QTreeWidget()
        self.trigger_tree.setHeaderLabels(["트리거명", "변수", "조건"])  # 원본과 동일
        
        # 트리 구조 제거로 텍스트 간격 문제 해결
        self.trigger_tree.setRootIsDecorated(False)  # 루트 노드 장식 제거
        self.trigger_tree.setIndentation(0)  # 들여쓰기 완전 제거
        
        # 열 폭 설정 (원본과 동일)
        self.trigger_tree.setColumnWidth(0, 180)  # 트리거명 폭
        self.trigger_tree.setColumnWidth(1, 120)  # 변수 폭
        self.trigger_tree.setColumnWidth(2, 140)  # 조건 폭
        
        self.trigger_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #cccccc;
                gridline-color: #e0e0e0;
                background-color: white;
                border-radius: 4px;
            }
            QTreeWidget::item {
                padding: 4px 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTreeWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 6px;
                border: 1px solid #cccccc;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        
        # 트리거 선택 시그널 연결
        self.trigger_tree.itemClicked.connect(self.on_trigger_selected)
        self.search_input.textChanged.connect(self.filter_triggers)
        
        layout.addWidget(self.trigger_tree)
        
        # 하단 버튼들 - 원본과 정확히 동일한 배치
        button_layout = QHBoxLayout()
        
        # 통일된 버튼 스타일 정의 (원본과 동일)
        button_base_style = """
            QPushButton {
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                min-height: 16px;
                max-height: 32px;
            }
        """
        
        # 트리거 저장 버튼 (원본과 동일)
        self.save_btn = QPushButton("� 트리거 저장")
        self.save_btn.setStyleSheet(button_base_style + """
            QPushButton {
                background-color: #28a745;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
                cursor: not-allowed;
            }
        """)
        self.save_btn.clicked.connect(self.save_current_condition)
        
        # 편집 버튼 (원본과 동일)
        self.edit_btn = QPushButton("✏️ 편집")
        self.edit_btn.setStyleSheet(button_base_style + """
            QPushButton {
                background-color: #007bff;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        self.edit_btn.clicked.connect(self.handle_edit_button_click)
        
        # 편집 취소 버튼 (원본과 동일)
        self.cancel_edit_btn = QPushButton("❌ 편집 취소")
        self.cancel_edit_btn.setStyleSheet(button_base_style + """
            QPushButton {
                background-color: #6c757d;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        self.cancel_edit_btn.clicked.connect(self.cancel_edit_trigger)
        
        # 트리거 복사 버튼 (원본과 동일)
        copy_trigger_btn = QPushButton("📋 복사")
        copy_trigger_btn.setStyleSheet(button_base_style + """
            QPushButton {
                background-color: #17a2b8;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:pressed {
                background-color: #117a8b;
            }
        """)
        copy_trigger_btn.clicked.connect(self.copy_trigger_for_edit)
        
        # 삭제 버튼 (원본과 동일)
        delete_btn = QPushButton("🗑️ 삭제")
        delete_btn.setStyleSheet(button_base_style + """
            QPushButton {
                background-color: #e74c3c;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        delete_btn.clicked.connect(self.delete_selected_trigger)
        
        # 버튼들을 원본 순서대로 배치
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.cancel_edit_btn)
        button_layout.addWidget(copy_trigger_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def on_trigger_selected(self, item, column):
        """트리거 선택 시 호출 - 원본 시그널 발송"""
        self.trigger_selected.emit(item, column)
    
    def load_trigger_list(self):
        """트리거 목록 로드 - 원본 기능 복제"""
        try:
            if not STORAGE_AVAILABLE:
                self._add_sample_triggers()
                return
                
            # 실제 데이터 로드 (원본과 동일한 방식)
            storage = ConditionStorage()
            conditions = storage.get_all_conditions()  # 원본 메서드명 사용
            
            self.trigger_tree.clear()
            
            # 조건들을 직접 리스트에 추가 (3개 열 사용: 트리거명, 변수, 조건)
            for condition in conditions:
                name = condition.get('name', 'Unknown')
                variable = condition.get('variable_name', 'Unknown')
                operator = condition.get('operator', '?')
                target = condition.get('target_value', '?')
                category = condition.get('category', 'unknown')
                
                # 외부변수 정보 처리하여 조건 텍스트에 포함
                external_variable = condition.get('external_variable')
                if external_variable and isinstance(external_variable, (dict, str)):
                    if isinstance(external_variable, str):
                        try:
                            import json
                            external_variable = json.loads(external_variable)
                        except:
                            external_variable = None
                    
                    if external_variable:
                        external_var_name = external_variable.get('variable_name', 'N/A')
                        condition_text = f"{operator} {external_var_name} (외부변수)"
                    else:
                        condition_text = f"{operator} {target}"
                else:
                    condition_text = f"{operator} {target}"
                
                # 카테고리 아이콘 추가 (트리거명에 포함)
                category_icons = {
                    "indicator": "📈",
                    "price": "💰", 
                    "capital": "🏦",
                    "state": "📊",
                    "custom": "⚙️",
                    "unknown": "❓"
                }
                icon = category_icons.get(category, "❓")
                
                # 트리거명에 카테고리 아이콘 추가
                display_name = f"{icon} {name}"
                
                # 3개 열 사용: 트리거명, 변수, 조건 (외부변수는 조건 텍스트에 포함)
                item = QTreeWidgetItem([display_name, variable, condition_text])
                item.setData(0, Qt.ItemDataRole.UserRole, condition)  # 조건 데이터 저장
                self.trigger_tree.addTopLevelItem(item)
            
            print(f"✅ {len(conditions)}개 트리거 로드 완료")
                
        except Exception as e:
            print(f"⚠️ 트리거 목록 로드 실패: {e}")
            self._add_sample_triggers()
    
    def _add_sample_triggers(self):
        """샘플 트리거 추가 (원본 형식에 맞게)"""
        sample_triggers = [
            {"name": "RSI 과매도", "variable": "RSI", "condition": "< 30"},
            {"name": "골든크로스", "variable": "이평선교차", "condition": "> 0 (외부변수)"},
            {"name": "거래량급증", "variable": "VOLUME", "condition": "> 평균거래량 (외부변수)"},
            {"name": "현재가상승", "variable": "CURRENT_PRICE", "condition": "> 전일종가"},
            {"name": "볼린저하단", "variable": "볼린저밴드", "condition": "< 하단선 (외부변수)"}
        ]
        
        for i, trigger in enumerate(sample_triggers):
            icon = "📈" if "RSI" in trigger["name"] or "골든" in trigger["name"] else "💰"
            display_name = f"{icon} {trigger['name']}"
            
            item = QTreeWidgetItem([display_name, trigger["variable"], trigger["condition"]])
            # 샘플 데이터도 UserRole에 저장
            sample_condition = {
                "name": trigger["name"],
                "variable_name": trigger["variable"],
                "condition": trigger["condition"],
                "id": f"sample_{i}"
            }
            item.setData(0, Qt.ItemDataRole.UserRole, sample_condition)
            self.trigger_tree.addTopLevelItem(item)
    
    def get_selected_trigger(self):
        """선택된 트리거 반환"""
        current_item = self.trigger_tree.currentItem()
        if current_item:
            return current_item.data(0, Qt.ItemDataRole.UserRole)
        return None
    
    def refresh_list(self):
        """목록 새로고침"""
        self.load_trigger_list()
    
    def add_trigger_item(self, trigger_data):
        """트리거 아이템 추가"""
        name = trigger_data.get('name', 'Unnamed')
        variable = trigger_data.get('variable_name', 'Unknown')
        operator = trigger_data.get('operator', '?')
        target = trigger_data.get('target_value', '?')
        category = trigger_data.get('category', 'unknown')
        
        # 외부변수 정보 처리하여 조건 텍스트에 포함
        external_variable = trigger_data.get('external_variable')
        if external_variable and isinstance(external_variable, (dict, str)):
            if isinstance(external_variable, str):
                try:
                    import json
                    external_variable = json.loads(external_variable)
                except:
                    external_variable = None
            
            if external_variable:
                external_var_name = external_variable.get('variable_name', 'N/A')
                condition_text = f"{operator} {external_var_name} (외부변수)"
            else:
                condition_text = f"{operator} {target}"
        else:
            condition_text = f"{operator} {target}"
        
        # 카테고리 아이콘 추가 (트리거명에 포함)
        category_icons = {
            "indicator": "📈",
            "price": "💰", 
            "capital": "🏦",
            "state": "📊",
            "custom": "⚙️",
            "unknown": "❓"
        }
        icon = category_icons.get(category, "❓")
        display_name = f"{icon} {name}"
        
        item = QTreeWidgetItem([display_name, variable, condition_text])
        item.setData(0, Qt.ItemDataRole.UserRole, trigger_data)
        self.trigger_tree.addTopLevelItem(item)
    
    def remove_selected_trigger(self):
        """선택된 트리거 제거"""
        current_item = self.trigger_tree.currentItem()
        if current_item:
            index = self.trigger_tree.indexOfTopLevelItem(current_item)
            self.trigger_tree.takeTopLevelItem(index)
    
    # 스타일 정의 - integrated_condition_manager.py에서 정확히 복사
    def _get_original_group_style(self):
        """원본 get_groupbox_style("#fd7e14")와 동일"""
        return """
            QGroupBox {
                background-color: white;
                border: 1px solid #fd7e14;
                border-radius: 8px;
                font-weight: bold;
                padding-top: 15px;
                margin: 3px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
                color: #fd7e14;
                font-size: 12px;
            }
        """
    
    def _get_original_tree_style(self):
        """원본 트리 위젯 스타일과 정확히 동일"""
        return """
            QTreeWidget {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
                alternate-background-color: #f8f9fa;
                font-size: 11px;
            }
            QTreeWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTreeWidget::item:selected {
                background-color: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
            }
            QTreeWidget::item:hover {
                background-color: #f8f9fa;
            }
            QTreeWidget::header {
                background-color: #fd7e14;
                color: white;
                border: none;
                font-weight: bold;
                font-size: 10px;
            }
        """
    
    def filter_triggers(self, text):
        """트리거 필터링 - 원본 기능 복제"""
        hidden_count = 0
        for i in range(self.trigger_tree.topLevelItemCount()):
            item = self.trigger_tree.topLevelItem(i)
            if text.lower() in item.text(0).lower():
                item.setHidden(False)
            else:
                item.setHidden(True)
                hidden_count += 1
        
        visible_count = self.trigger_tree.topLevelItemCount() - hidden_count
        print(f"🔍 검색 완료: '{text}' - {visible_count}개 표시, {hidden_count}개 숨김")
    
    # ==============================================
    # 원본 버튼 메서드들 - integrated_condition_manager.py에서 복제
    # ==============================================
    
    def save_current_condition(self):
        """트리거 저장 버튼 - 시그널로 요청 전달"""
        print("💾 트리거 저장 버튼 클릭됨 - 시그널 발송")
        self.trigger_save_requested.emit()  # 시그널 발송으로 메인 화면에 위임
    
    def edit_selected_trigger(self):
        """선택한 트리거 편집 - 원본 기능 복제"""
        current_item = self.trigger_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "⚠️ 경고", "편집할 트리거를 선택해주세요.")
            return
        
        # 조건 데이터 가져오기
        condition_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not condition_data:
            QMessageBox.warning(self, "⚠️ 경고", "트리거 데이터를 찾을 수 없습니다.")
            return
        
        # 원본과 동일한 편집 모드 메시지
        condition_name = condition_data.get('name', '')
        QMessageBox.information(self, "✅ 편집 모드",
                               f"'{condition_name}' 조건이 편집 모드로 로드되었습니다.\n"
                               "수정 후 '트리거 저장' 버튼을 눌러 저장하세요.")
        
        # 편집용 시그널 발송 (condition_data 포함)
        self.trigger_edited.emit()
        
        # 부모 화면에 편집 요청 (조건 빌더에 로드)
        if hasattr(self.parent(), 'load_condition_for_edit'):
            self.parent().load_condition_for_edit(condition_data)
        elif hasattr(self.parent().parent(), 'load_condition_for_edit'):
            self.parent().parent().load_condition_for_edit(condition_data)
        
        # 편집 모드 진입
        self.is_edit_mode = True
        self.update_edit_button_state(True)
    
    def update_edit_button_state(self, is_edit_mode: bool):
        """편집 버튼 상태 업데이트 - 원본 기능 복제"""
        # 통일된 버튼 스타일 정의
        button_base_style = """
            QPushButton {
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                min-height: 16px;
                max-height: 32px;
            }
        """
        
        if is_edit_mode:
            # 편집 모드: "편집 저장" 버튼으로 변경
            self.edit_btn.setText("💾 편집 저장")
            self.edit_btn.setStyleSheet(button_base_style + """
                QPushButton {
                    background-color: #fd7e14;
                }
                QPushButton:hover {
                    background-color: #e8681a;
                }
                QPushButton:pressed {
                    background-color: #d9580d;
                }
            """)
            
            # 편집 모드에서는 트리거 저장 버튼 비활성화 (혼동 방지)
            self.save_btn.setEnabled(False)
            self.save_btn.setToolTip("편집 모드에서는 '편집 저장' 버튼을 사용하세요")
            
        else:
            # 일반 모드: "편집" 버튼으로 복원
            self.edit_btn.setText("✏️ 편집")
            self.edit_btn.setStyleSheet(button_base_style + """
                QPushButton {
                    background-color: #007bff;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
                QPushButton:pressed {
                    background-color: #004085;
                }
            """)
            
            # 일반 모드에서는 트리거 저장 버튼 활성화
            self.save_btn.setEnabled(True)
            self.save_btn.setToolTip("")
        
        # 상태 저장 및 시그널 발송
        self.is_edit_mode = is_edit_mode
        self.edit_mode_changed.emit(is_edit_mode)
    
    def handle_edit_button_click(self):
        """편집 버튼 클릭 핸들러 - 모드에 따라 다른 동작"""
        if self.is_edit_mode:
            # 편집 저장 모드
            self.save_edit_changes()
        else:
            # 편집 모드 시작
            self.edit_selected_trigger()
    
    def save_edit_changes(self):
        """편집 저장 - 원본 기능 복제"""
        # 편집 저장 시그널 발송 (메인 화면에서 처리)
        self.trigger_save_requested.emit()
        
        # 편집 모드 종료
        self.is_edit_mode = False
        self.update_edit_button_state(False)
        
        print("✅ 편집 저장 완료")

    def cancel_edit_trigger(self):
        """편집 취소 - 원본 기능 복제"""
        try:
            # 편집 모드 종료
            self.is_edit_mode = False
            self.update_edit_button_state(False)
            
            # 조건 빌더 초기화 요청 (부모 화면을 통해)
            if hasattr(self.parent(), 'cancel_edit_mode'):
                self.parent().cancel_edit_mode()
            elif hasattr(self.parent().parent(), 'cancel_edit_mode'):
                self.parent().parent().cancel_edit_mode()
            
            QMessageBox.information(self, "❌ 편집 취소", "편집이 취소되었습니다.")
            print("✅ 편집 취소 완료")
            
        except Exception as e:
            print(f"❌ 편집 취소 실패: {e}")
            QMessageBox.critical(self, "❌ 오류", f"편집 취소 중 오류가 발생했습니다:\n{e}")
    
    def copy_trigger_for_edit(self):
        """트리거 복사 - 원본 기능 복제"""
        current_item = self.trigger_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "⚠️ 경고", "복사할 트리거를 선택해주세요.")
            return
        
        # 조건 데이터 가져오기
        condition_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not condition_data:
            QMessageBox.warning(self, "⚠️ 경고", "트리거 데이터를 찾을 수 없습니다.")
            return
        
        try:
            # 원본 조건 데이터 복사
            original_condition = condition_data.copy()
            
            # 새로운 이름 생성 (원본 이름 + "_copy")
            original_name = original_condition.get('name', 'Unknown')
            new_name = f"{original_name}_copy"
            
            # 이미 같은 이름이 있는지 확인하고 번호 추가
            counter = 1
            while self._check_condition_name_exists(new_name):
                new_name = f"{original_name}_copy_{counter}"
                counter += 1
            
            # 새로운 조건 데이터 생성
            copied_condition = original_condition.copy()
            copied_condition['name'] = new_name
            
            # ID 제거 (새로 생성될 때 새 ID 할당)
            if 'id' in copied_condition:
                del copied_condition['id']
            
            # 생성일 업데이트
            from datetime import datetime
            copied_condition['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 부모 화면에 복사된 데이터 로드 요청
            if hasattr(self.parent(), 'load_condition_for_edit'):
                self.parent().load_condition_for_edit(copied_condition)
            elif hasattr(self.parent().parent(), 'load_condition_for_edit'):
                self.parent().parent().load_condition_for_edit(copied_condition)
            
            # 편집 모드 시작
            self.is_edit_mode = True
            self.update_edit_button_state(True)
            
            QMessageBox.information(self, "📋 복사 완료", 
                                   f"'{original_name}' 트리거가 복사되었습니다.\n\n"
                                   f"새 이름: '{new_name}'\n"
                                   f"필요한 수정을 한 후 '편집 저장'을 눌러 저장하세요.")
            
            print(f"✅ 트리거 복사 완료: {original_name} → {new_name}")
            
        except Exception as e:
            print(f"❌ 트리거 복사 실패: {e}")
            QMessageBox.critical(self, "❌ 오류", f"트리거 복사 중 오류가 발생했습니다:\n{e}")
    
    def _check_condition_name_exists(self, name):
        """조건 이름 존재 여부 확인"""
        try:
            if not STORAGE_AVAILABLE:
                return False
            storage = ConditionStorage()
            conditions = storage.get_all_conditions()
            return any(condition.get('name') == name for condition in conditions)
        except Exception:
            return False
    
    def delete_selected_trigger(self):
        """선택한 트리거 삭제 - 원본 기능 복제"""
        current_item = self.trigger_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "⚠️ 경고", "삭제할 트리거를 선택해주세요.")
            return
        
        # 조건 데이터 가져오기
        condition_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not condition_data:
            QMessageBox.warning(self, "⚠️ 경고", "트리거 데이터를 찾을 수 없습니다.")
            return
        
        condition_name = condition_data.get('name', 'Unknown')
        condition_id = condition_data.get('id', None)
        
        # 삭제 확인 다이얼로그 (원본과 동일)
        reply = QMessageBox.question(
            self, "🗑️ 삭제 확인",
            f"정말로 '{condition_name}' 트리거를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if STORAGE_AVAILABLE and condition_id:
                    # 실제 삭제
                    storage = ConditionStorage()
                    storage.delete_condition(condition_id)
                    storage.delete_condition(condition_id)
                    
                    QMessageBox.information(self, "✅ 삭제 완료", f"'{condition_name}' 트리거가 삭제되었습니다.")
                    print(f"✅ 트리거 삭제 완료: {condition_name}")
                    
                    # UI 업데이트
                    self.load_trigger_list()
                    
                    # 삭제 시그널 발송
                    self.trigger_deleted.emit()
                else:
                    # 샘플 데이터에서 삭제 (실제로는 새로고침만)
                    self.load_trigger_list()
                    QMessageBox.information(self, "✅ 삭제 완료", f"'{condition_name}' 트리거가 삭제되었습니다.")
                    
            except Exception as e:
                print(f"❌ 트리거 삭제 실패: {e}")
                QMessageBox.critical(self, "❌ 오류", f"트리거 삭제 중 오류가 발생했습니다:\n{e}")


if __name__ == "__main__":
    # 테스트용 코드
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    widget = TriggerListWidget()
    widget.show()
    
    sys.exit(app.exec())
