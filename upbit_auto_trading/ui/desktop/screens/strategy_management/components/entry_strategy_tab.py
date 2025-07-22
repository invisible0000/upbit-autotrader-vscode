"""
진입 전략 관리 탭 컴포넌트
"""
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QTableWidgetItem, 
    QLabel, QMessageBox, QInputDialog, QDialog, QPushButton, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from upbit_auto_trading.ui.desktop.common.components import StyledTableWidget, PrimaryButton, SecondaryButton, DangerButton
from upbit_auto_trading.business_logic.strategy.trading_strategies import (
    StrategyManager, StrategyConfig as TradingStrategyConfig, 
    initialize_default_strategies
)
from .parameter_editor_dialog import ParameterEditorDialog
from datetime import datetime
from typing import Dict, Any
import uuid

class EntryStrategyTab(QWidget):
    """진입 전략 관리 탭"""
    
    # 시그널 정의
    strategy_created = pyqtSignal(str)  # 전략 생성됨
    strategy_updated = pyqtSignal(str)  # 전략 수정됨
    strategy_deleted = pyqtSignal(str)  # 전략 삭제됨
    backtest_requested = pyqtSignal(str)  # 백테스트 요청
    
    def __init__(self, strategy_manager: StrategyManager, parent=None):
        super().__init__(parent)
        self.strategy_manager = strategy_manager
        self.init_ui()
        self.load_strategies()
        self.connect_events()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 진입 전략 설명
        description = QLabel("📈 진입 전략: 포지션이 없는 상태에서 최초 진입 신호를 생성합니다")
        description.setStyleSheet("font-weight: bold; color: #2196F3; padding: 10px; background: #E3F2FD; border-radius: 5px;")
        layout.addWidget(description)
        
        # 진입 전략 테이블 (6개 컬럼)
        self.strategy_table = StyledTableWidget(rows=6, columns=6)
        self.strategy_table.setHorizontalHeaderLabels(["순서", "작성일", "전략명", "상태", "신호유형", "설명"])
        
        # 컬럼 폭 설정
        self.strategy_table.setColumnWidth(0, 70)   # 순서 (90→70, -20)  
        self.strategy_table.setColumnWidth(1, 84)   # 작성일 (120→84, -30% 감소)
        self.strategy_table.setColumnWidth(2, 200)  # 전략명 (2배)
        self.strategy_table.setColumnWidth(3, 70)   # 상태
        self.strategy_table.setColumnWidth(4, 88)   # 신호유형 (80→88, +10% 증가)
        self.strategy_table.setColumnWidth(5, 300)  # 설명 (가장 넓게)
        
        # 행 높이 설정 (버튼이 잘리지 않도록)
        self.strategy_table.verticalHeader().setDefaultSectionSize(30)
        
        # 테이블 설정 (기본 선택 모드)
        self.strategy_table.setSortingEnabled(True)  # 정렬 활성화
        self.strategy_table.setSelectionBehavior(self.strategy_table.SelectionBehavior.SelectRows)  # 행 단위 선택
        self.strategy_table.setSelectionMode(self.strategy_table.SelectionMode.ExtendedSelection)  # 확장 선택 (Ctrl/Shift 지원)
        layout.addWidget(self.strategy_table)
        
        # 버튼 그룹
        button_layout = QHBoxLayout()
        self.create_button = PrimaryButton("📈 진입 전략 생성")
        self.edit_button = SecondaryButton("✏️ 수정")
        self.delete_button = DangerButton("🗑️ 삭제")
        self.delete_selected_button = DangerButton("�️ 선택 항목 삭제")
        
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.delete_selected_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def connect_events(self):
        """이벤트 연결"""
        self.create_button.clicked.connect(self.create_strategy)
        self.edit_button.clicked.connect(self.edit_strategy)
        self.delete_button.clicked.connect(self.delete_strategy)
        self.delete_selected_button.clicked.connect(self.delete_selected_strategies)
        
        # 설명 편집을 위한 더블 클릭 이벤트
        self.strategy_table.cellDoubleClicked.connect(self._on_cell_double_clicked)
    
    def load_strategies(self):
        """전략 데이터 로딩"""
        try:
            print("🔍 진입 전략 데이터를 로딩합니다...")
            
            # 먼저 실제 DB에서 전략 가져오기 시도
            all_strategies = self.strategy_manager.get_strategy_list()
            
            # 진입 전략만 필터링 (관리 전략 제외)
            entry_strategies = []
            for strategy in all_strategies:
                strategy_type = strategy.get("strategy_type", "")
                
                # 관리 전략 타입들 제외 (stop_loss, trailing_stop, take_profit 등)
                management_types = [
                    "stop_loss", "trailing_stop", "take_profit", 
                    "fixed_stop_loss", "trailing_stop_loss",
                    "position_management", "risk_management"
                ]
                
                # 진입 전략만 포함 (관리 전략이 아닌 것들)
                if strategy_type not in management_types and not any(mgmt in strategy_type.lower() for mgmt in ["stop", "management", "trail"]):
                    entry_strategies.append({
                        "id": strategy.get("id", strategy.get("strategy_id", "")),
                        "name": strategy.get("name", ""),
                        "desc": strategy.get("description", ""),
                        "signal": "BUY/SELL",  # 진입 전략은 모두 BUY/SELL
                        "status": "활성"
                    })
            
            print(f"✅ DB에서 진입 전략 {len(entry_strategies)}개 로딩 완료")
            
            # DB에서 로딩한 전략만 표시 (폴백 제거)
            self._populate_strategy_table(entry_strategies)
                
        except Exception as e:
            print(f"❌ 진입 전략 로딩 실패: {e}")
            # 오류 시에도 빈 목록 표시
            self._populate_strategy_table([])
    
    def _populate_strategy_table(self, strategies):
        """전략 목록을 테이블에 표시"""
        self.strategy_table.setRowCount(len(strategies))
        for i, strategy in enumerate(strategies):
            # 순서 컬럼에 이동 버튼 위젯 추가
            move_widget = QWidget()
            move_layout = QHBoxLayout(move_widget)
            move_layout.setContentsMargins(2, 2, 2, 2)
            move_layout.setSpacing(2)
            
            up_button = QPushButton("▲")
            down_button = QPushButton("▼")
            up_button.setFixedSize(26, 14)
            down_button.setFixedSize(26, 14)
            
            # 스타일 적용
            button_style = """
                QPushButton {
                    background-color: #ffffff;
                    border: 1px solid #999;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 12px;
                    color: #333;
                }
                QPushButton:hover {
                    background-color: #e6f3ff;
                    border-color: #4da6ff;
                }
                QPushButton:pressed {
                    background-color: #cce6ff;
                }
            """
            up_button.setStyleSheet(button_style)
            down_button.setStyleSheet(button_style)
            
            # 툴팁 추가
            up_button.setToolTip("위로 이동")
            down_button.setToolTip("아래로 이동")
            
            # 버튼 이벤트 연결
            up_button.setProperty("row", i)
            down_button.setProperty("row", i)
            up_button.clicked.connect(self._on_move_up_clicked)
            down_button.clicked.connect(self._on_move_down_clicked)
            
            move_layout.addWidget(up_button)
            move_layout.addWidget(down_button)
            move_layout.addStretch()
            
            self.strategy_table.setCellWidget(i, 0, move_widget)
            
            # 작성일 컬럼 (체크박스 아님)
            date_item = QTableWidgetItem("25/07/22")  # 현재 날짜
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.strategy_table.setItem(i, 1, date_item)
            
            # 전략명 컬럼
            name_item = QTableWidgetItem(strategy["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, strategy.get("id", ""))  # 전략 ID 저장
            self.strategy_table.setItem(i, 2, name_item)
            
            # 상태 컬럼
            status_item = QTableWidgetItem(strategy.get("status", "활성"))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.strategy_table.setItem(i, 3, status_item)
            
            # 신호유형 컬럼
            signal_item = QTableWidgetItem(strategy.get("signal", "BUY/SELL"))
            signal_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.strategy_table.setItem(i, 4, signal_item)
            
            # 설명 컬럼
            desc_item = QTableWidgetItem(strategy.get("desc", ""))
            self.strategy_table.setItem(i, 5, desc_item)
    
    def create_strategy(self):
        """진입 전략 생성"""
        print("[UI] 📈 진입 전략 생성 다이얼로그 열기")
        
        # 전략 타입 선택 다이얼로그
        strategy_types = [
            "이동평균 교차", "RSI 과매수/과매도", "볼린저 밴드", 
            "변동성 돌파", "MACD 교차", "스토캐스틱"
        ]
        strategy_type, ok = QInputDialog.getItem(
            self, 
            "전략 타입 선택", 
            "생성할 전략 타입을 선택하세요:", 
            strategy_types, 
            0, 
            False
        )
        
        if not ok:
            return
        
        # 전략 이름 입력
        strategy_name, ok = QInputDialog.getText(
            self, 
            "전략 이름", 
            "전략 이름을 입력하세요:",
            text=f"새 {strategy_type} 전략"
        )
        
        if not ok or not strategy_name.strip():
            return
        
        # 중복 이름 체크 및 자동 넘버링
        original_name = strategy_name.strip()
        final_name = self._get_unique_strategy_name(original_name)
        
        if final_name != original_name:
            reply = QMessageBox.question(
                self,
                "이름 중복",
                f"'{original_name}' 이름이 이미 존재합니다.\n'{final_name}'로 변경하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # 기본 파라미터 설정
        default_params = self._get_default_parameters(strategy_type)
        
        # UI 전략 타입을 실제 전략 타입으로 매핑
        strategy_type_mapping = {
            "이동평균 교차": "moving_average_cross",
            "RSI 과매수/과매도": "rsi_reversal", 
            "볼린저 밴드": "bollinger_band_mean_reversion",
            "변동성 돌파": "volatility_breakout",
            "MACD 교차": "macd_cross",
            "스토캐스틱": "stochastic"
        }
        
        actual_strategy_type = strategy_type_mapping.get(strategy_type, strategy_type.lower().replace(" ", "_"))
        
        # 전략 생성
        strategy_config = TradingStrategyConfig(
            strategy_id=str(uuid.uuid4()),
            name=final_name,
            strategy_type=actual_strategy_type,
            parameters=default_params,
            description=f"사용자 생성 {strategy_type} 전략",
            created_at=datetime.now()
        )
        
        # DB에 저장
        try:
            print(f"[DEBUG] 전략 저장 시도: {strategy_config.name}")
            
            # 개별 매개변수 방식으로 저장 (strategy_manager.py의 StrategyManager 사용)
            success = self.strategy_manager.save_strategy(
                strategy_id=strategy_config.strategy_id,
                strategy_type=strategy_config.strategy_type,
                name=strategy_config.name,
                description=strategy_config.description,
                parameters=strategy_config.parameters
            )
            print(f"[DEBUG] 전략 저장 결과: {success}")
                
        except Exception as e:
            print(f"[UI] ❌ 전략 저장 중 오류: {e}")
            success = False
        if success:
            print(f"[UI] ✅ 전략 생성 완료: {final_name}")
            self.load_strategies()  # UI 새로고침
            self.strategy_created.emit(final_name)
            QMessageBox.information(self, "성공", f"전략 '{final_name}'이 생성되었습니다.")
        else:
            print(f"[UI] ❌ 전략 생성 실패: {final_name}")
            QMessageBox.critical(self, "오류", "전략 생성에 실패했습니다.")
    
    def edit_strategy(self):
        """진입 전략 수정"""
        current_row = self.strategy_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "경고", "수정할 전략을 선택해주세요.")
            return
        
        # 선택된 행에 데이터가 있는지 확인
        strategy_name_item = self.strategy_table.item(current_row, 2)  # 전략명 컬럼
        if not strategy_name_item or not strategy_name_item.text().strip():
            QMessageBox.warning(self, "경고", "유효한 전략을 선택해주세요.")
            return
            
        strategy_name = strategy_name_item.text()
        strategy_id = strategy_name_item.data(Qt.ItemDataRole.UserRole)
        
        if not strategy_id:
            QMessageBox.warning(self, "경고", "전략 정보를 찾을 수 없습니다.")
            return
        
        # 전략 설정 로드
        config = self.strategy_manager.load_strategy(strategy_id)
        if not config:
            QMessageBox.critical(self, "오류", "전략 정보를 불러올 수 없습니다.")
            return
        
        print(f"[UI] ✏️ 진입 전략 수정: {strategy_name}")
        
        # 전략 타입 추론 또는 기본값 사용
        if hasattr(config, 'strategy_type'):
            strategy_type = config.strategy_type
        elif hasattr(config, '__class__'):
            # 클래스명에서 전략 타입 추론
            class_name = config.__class__.__name__
            if "MovingAverage" in class_name:
                strategy_type = "moving_average_cross"
            elif "RSI" in class_name:
                strategy_type = "rsi_reversal"
            elif "Bollinger" in class_name:
                strategy_type = "bollinger_band_mean_reversion"
            else:
                strategy_type = "moving_average_cross"  # 기본값
        else:
            strategy_type = "moving_average_cross"  # 기본값
        
        # 파라미터가 객체에서 추출되는 경우 처리
        if hasattr(config, 'parameters') and isinstance(config.parameters, dict):
            parameters = config.parameters
        elif hasattr(config, 'get_parameters'):
            parameters = config.get_parameters()
        else:
            parameters = {}  # 기본 빈 파라미터
        
        # 파라미터 수정 다이얼로그
        dialog = ParameterEditorDialog(strategy_type, parameters, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                # 새 파라미터 가져오기
                new_params = dialog.get_parameters()
                config.parameters = new_params
                config.updated_at = datetime.now()
                
                # DB 업데이트
                success = self.strategy_manager.save_strategy(config)
                if success:
                    print(f"[UI] ✅ 전략 파라미터 수정 완료: {config.name}")
                    self.load_strategies()
                    self.strategy_updated.emit(strategy_name)
                    QMessageBox.information(self, "성공", f"전략 '{config.name}' 파라미터가 수정되었습니다.")
                else:
                    QMessageBox.critical(self, "오류", "전략 저장에 실패했습니다.")
                    
            except Exception as e:
                print(f"[UI] ❌ 전략 파라미터 수정 중 오류: {e}")
                QMessageBox.critical(self, "오류", f"파라미터 수정 중 오류가 발생했습니다:\n{str(e)}")
    
    def delete_strategy(self):
        """진입 전략 삭제"""
        current_row = self.strategy_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "경고", "삭제할 전략을 선택해주세요.")
            return
        
        # 선택된 행에 데이터가 있는지 확인
        strategy_name_item = self.strategy_table.item(current_row, 2)  # 전략명 컬럼
        if not strategy_name_item or not strategy_name_item.text().strip():
            QMessageBox.warning(self, "경고", "유효한 전략을 선택해주세요.")
            return
            
        strategy_name = strategy_name_item.text()
        strategy_id = strategy_name_item.data(Qt.ItemDataRole.UserRole)
        
        if not strategy_id:
            QMessageBox.warning(self, "경고", "전략 정보를 찾을 수 없습니다.")
            return
        
        # 삭제 확인
        reply = QMessageBox.question(
            self, 
            "전략 삭제", 
            f"전략 '{strategy_name}'을 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.strategy_manager.delete_strategy(strategy_id)
                
                if success:
                    print(f"[UI] ✅ 전략 완전 삭제: {strategy_name}")
                    self.load_strategies()
                    self.strategy_deleted.emit(strategy_name)
                    QMessageBox.information(self, "완료", f"전략 '{strategy_name}'이 완전히 삭제되었습니다.")
                else:
                    QMessageBox.critical(self, "오류", "전략 삭제에 실패했습니다.")
            except Exception as e:
                print(f"[UI] ❌ 전략 삭제 중 오류: {e}")
                QMessageBox.critical(self, "오류", f"전략 삭제 중 오류가 발생했습니다:\n{str(e)}")
    
    def delete_selected_strategies(self):
        """선택된 여러 전략 삭제"""
        # 선택된 행들의 인덱스 수집
        selected_rows = []
        selection_model = self.strategy_table.selectionModel()
        if selection_model:
            # 현재 선택된 모든 행 수집
            for i in range(self.strategy_table.rowCount()):
                if selection_model.isRowSelected(i, self.strategy_table.rootIndex()):
                    selected_rows.append(i)
        
        # 선택된 행이 없으면 현재 행을 대상으로
        if not selected_rows:
            current_row = self.strategy_table.currentRow()
            if current_row >= 0:
                selected_rows = [current_row]
        
        if not selected_rows:
            QMessageBox.warning(self, "경고", "삭제할 전략을 선택해주세요.\n\n💡 팁: Ctrl+클릭으로 여러 전략을 선택할 수 있습니다.")
            return
        
        # 선택된 전략들의 정보 수집
        strategies_to_delete = []
        for row in selected_rows:
            strategy_name_item = self.strategy_table.item(row, 2)  # 전략명 컬럼
            if strategy_name_item and strategy_name_item.text().strip():
                strategy_id = strategy_name_item.data(Qt.ItemDataRole.UserRole)
                if strategy_id:
                    strategies_to_delete.append({
                        'row': row,
                        'name': strategy_name_item.text(),
                        'id': strategy_id
                    })
        
        if not strategies_to_delete:
            QMessageBox.warning(self, "경고", "유효한 전략을 선택해주세요.")
            return
        
        # 삭제 확인
        strategy_names = [s['name'] for s in strategies_to_delete]
        names_text = '\n'.join([f"• {name}" for name in strategy_names])
        
        reply = QMessageBox.question(
            self,
            "전략 일괄 삭제",
            f"다음 {len(strategies_to_delete)}개 전략을 삭제하시겠습니까?\n\n{names_text}\n\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                deleted_count = 0
                failed_strategies = []
                
                for strategy_info in strategies_to_delete:
                    success = self.strategy_manager.delete_strategy(strategy_info['id'])
                    if success:
                        deleted_count += 1
                        print(f"[UI] ✅ 전략 삭제: {strategy_info['name']}")
                        self.strategy_deleted.emit(strategy_info['name'])
                    else:
                        failed_strategies.append(strategy_info['name'])
                
                # UI 새로고침
                self.load_strategies()
                
                # 결과 메시지
                if failed_strategies:
                    failed_names = ', '.join(failed_strategies)
                    QMessageBox.warning(
                        self, 
                        "일부 삭제 실패", 
                        f"{deleted_count}개 전략이 삭제되었습니다.\n\n실패한 전략: {failed_names}"
                    )
                else:
                    QMessageBox.information(
                        self, 
                        "삭제 완료", 
                        f"{deleted_count}개 전략이 모두 삭제되었습니다."
                    )
                    
            except Exception as e:
                print(f"[UI] ❌ 전략 일괄 삭제 중 오류: {e}")
                QMessageBox.critical(self, "오류", f"전략 삭제 중 오류가 발생했습니다:\n{str(e)}")
    
    def _get_default_parameters(self, strategy_type: str) -> Dict[str, Any]:
        """전략 타입별 기본 파라미터 반환 - 실제 Strategy 클래스 구조에 맞게 수정"""
        defaults = {
            "이동평균 교차": {
                "name": f"새 이동평균 교차 전략",
                "strategy_type": "moving_average_cross",
                "short_period": 5,
                "long_period": 20,
                "ma_type": "SMA",
                "enabled": True
            },
            "RSI 과매수/과매도": {
                "name": f"새 RSI 과매수/과매도 전략",
                "strategy_type": "rsi_reversal",
                "period": 14,
                "oversold_threshold": 30.0,
                "overbought_threshold": 70.0,
                "enabled": True
            },
            "볼린저 밴드": {
                "name": f"새 볼린저 밴드 전략",
                "strategy_type": "bollinger_band_mean_reversion",
                "period": 20,
                "std_dev": 2.0,
                "enabled": True
            },
            "변동성 돌파": {
                "name": f"새 변동성 돌파 전략",
                "strategy_type": "volatility_breakout",
                "period": 20,
                "k_value": 0.5,
                "enabled": True
            },
            "MACD 교차": {
                "name": f"새 MACD 교차 전략",
                "strategy_type": "macd_cross",
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9,
                "enabled": True
            },
            "스토캐스틱": {
                "name": f"새 스토캐스틱 전략",
                "strategy_type": "stochastic",
                "k_period": 14,
                "d_period": 3,
                "oversold": 20.0,
                "overbought": 80.0,
                "enabled": True
            }
        }
        
        return defaults.get(strategy_type, {"name": f"새 {strategy_type} 전략", "strategy_type": strategy_type.lower().replace(" ", "_"), "enabled": True})
    
    def _get_unique_strategy_name(self, base_name: str) -> str:
        """중복되지 않는 전략 이름 생성"""
        # 현재 등록된 모든 전략 이름 수집
        existing_names = set()
        try:
            strategies = self.strategy_manager.get_all_strategies()
            for strategy in strategies:
                existing_names.add(strategy.name)
        except:
            # DB 오류 시 UI에서 수집
            for i in range(self.strategy_table.rowCount()):
                name_item = self.strategy_table.item(i, 2)  # 전략명 컬럼
                if name_item and name_item.text().strip():
                    existing_names.add(name_item.text())
        
        # 기본 이름이 중복되지 않으면 그대로 반환
        if base_name not in existing_names:
            return base_name
        
        # 중복되면 번호를 붙여서 고유한 이름 생성
        counter = 2
        while True:
            new_name = f"{base_name} {counter:02d}"
            if new_name not in existing_names:
                return new_name
            counter += 1
            if counter > 99:  # 무한 루프 방지
                return f"{base_name} {uuid.uuid4().hex[:8]}"
    
    def _on_cell_double_clicked(self, row: int, col: int):
        """셀 더블 클릭 이벤트 - 설명 편집"""
        if col == 5:  # 설명 컬럼
            self._edit_strategy_description(row)
    
    def _edit_strategy_description(self, row: int):
        """전략 설명 편집"""
        try:
            # 전략 정보 가져오기
            strategy_name_item = self.strategy_table.item(row, 2)  # 전략명 컬럼
            if not strategy_name_item:
                return
                
            strategy_id = strategy_name_item.data(Qt.ItemDataRole.UserRole)
            if not strategy_id:
                return
            
            # DB에서 전략 로드
            config = self.strategy_manager.load_strategy(strategy_id)
            if not config:
                QMessageBox.critical(self, "오류", "전략 정보를 불러올 수 없습니다.")
                return
            
            # 현재 설명 가져오기
            current_description = config.description or ""
            
            # 설명 편집 다이얼로그
            new_description, ok = QInputDialog.getMultiLineText(
                self,
                f"설명 편집: {config.name}",
                "전략 설명을 편집하세요:",
                current_description
            )
            
            if ok and new_description != current_description:
                # 설명 업데이트
                config.description = new_description
                config.updated_at = datetime.now()
                
                # DB 저장
                success = self.strategy_manager.save_strategy(config)
                if success:
                    # UI 업데이트
                    desc_item = self.strategy_table.item(row, 5)
                    if desc_item:
                        desc_item.setText(new_description)
                    
                    print(f"[UI] ✅ 전략 설명 수정 완료: {config.name}")
                    QMessageBox.information(self, "성공", "전략 설명이 수정되었습니다.")
                else:
                    QMessageBox.critical(self, "오류", "설명 저장에 실패했습니다.")
                    
        except Exception as e:
            print(f"[UI] ❌ 설명 편집 중 오류: {e}")
            QMessageBox.critical(self, "오류", f"설명 편집 중 오류가 발생했습니다:\n{str(e)}")
    
    def _on_move_up_clicked(self):
        """위로 이동 버튼 클릭 핸들러"""
        try:
            button = self.sender()
            if button:
                row = button.property("row")
                if row is not None:
                    self.move_strategy_up(row)
        except Exception as e:
            print(f"위로 이동 중 오류: {e}")
    
    def _on_move_down_clicked(self):
        """아래로 이동 버튼 클릭 핸들러"""
        try:
            button = self.sender()
            if button:
                row = button.property("row")
                if row is not None:
                    self.move_strategy_down(row)
        except Exception as e:
            print(f"아래로 이동 중 오류: {e}")
    
    def move_strategy_up(self, row: int):
        """전략을 위로 이동"""
        if row <= 0:
            QMessageBox.information(self, "알림", "이미 맨 위에 있습니다.")
            return
        
        try:
            print(f"[UI] 전략 위로 이동: row {row} -> {row-1}")
            self._swap_table_rows(row, row - 1)
            
            # 이동 후 선택 유지
            self.strategy_table.selectRow(row - 1)
            
        except Exception as e:
            print(f"위로 이동 중 오류: {e}")
            QMessageBox.critical(self, "오류", f"위로 이동 중 오류가 발생했습니다: {str(e)}")
        
    def move_strategy_down(self, row: int):
        """전략을 아래로 이동"""
        if row >= self.strategy_table.rowCount() - 1:
            QMessageBox.information(self, "알림", "이미 맨 아래에 있습니다.")
            return
        
        try:
            print(f"[UI] 전략 아래로 이동: row {row} -> {row+1}")
            self._swap_table_rows(row, row + 1)
            
            # 이동 후 선택 유지
            self.strategy_table.selectRow(row + 1)
            
        except Exception as e:
            print(f"아래로 이동 중 오류: {e}")
            QMessageBox.critical(self, "오류", f"아래로 이동 중 오류가 발생했습니다: {str(e)}")
    
    def _swap_table_rows(self, row1: int, row2: int):
        """두 테이블 행의 데이터를 교환"""
        try:
            # 각 컬럼의 데이터 교환 (순서 컬럼 제외, 1~5번 컬럼만)
            for col in range(1, 6):  # 작성일, 전략명, 상태, 신호유형, 설명
                item1 = self.strategy_table.item(row1, col)
                item2 = self.strategy_table.item(row2, col)
                
                if item1 and item2:
                    # 텍스트 교환
                    text1 = item1.text()
                    text2 = item2.text()
                    item1.setText(text2)
                    item2.setText(text1)
                    
                    # UserRole 데이터도 교환 (전략 ID 등)
                    if col == 2:  # 전략명 컬럼의 경우 ID 정보도 교환
                        data1 = item1.data(Qt.ItemDataRole.UserRole)
                        data2 = item2.data(Qt.ItemDataRole.UserRole)
                        item1.setData(Qt.ItemDataRole.UserRole, data2)
                        item2.setData(Qt.ItemDataRole.UserRole, data1)
            
            # 순서 컬럼의 버튼 위젯들도 row 정보 업데이트
            self._update_move_buttons_row_property(row1, row1)
            self._update_move_buttons_row_property(row2, row2)
            
            print(f"✅ 행 교환 완료: {row1} ↔ {row2}")
            
        except Exception as e:
            print(f"❌ 행 교환 중 오류: {e}")
            raise e
    
    def _update_move_buttons_row_property(self, table_row: int, new_row_value: int):
        """순서 컬럼의 버튼들의 row property 업데이트"""
        try:
            move_widget = self.strategy_table.cellWidget(table_row, 0)
            if move_widget:
                # 위젯 내의 모든 QPushButton 찾아서 row property 업데이트
                buttons = move_widget.findChildren(QPushButton)
                for button in buttons:
                    button.setProperty("row", new_row_value)
        except Exception as e:
            print(f"버튼 row property 업데이트 오류: {e}")
    
    def get_strategies_for_combination(self):
        """전략 조합용 전략 목록 반환"""
        strategies = []
        for i in range(self.strategy_table.rowCount()):
            name_item = self.strategy_table.item(i, 2)  # 전략명 컬럼
            desc_item = self.strategy_table.item(i, 5)  # 설명 컬럼
            if name_item and desc_item:
                strategy_id = name_item.data(Qt.ItemDataRole.UserRole)
                strategies.append({
                    "id": strategy_id,
                    "name": name_item.text(),
                    "description": desc_item.text()
                })
        return strategies
