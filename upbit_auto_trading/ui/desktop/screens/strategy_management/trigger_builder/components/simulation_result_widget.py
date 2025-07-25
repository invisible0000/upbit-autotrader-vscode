"""
시뮬레이션 결과 위젯
원본: integrated_condition_manager.py의 create_test_result_area() 완전 복제
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, 
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime

# 차트 라이브러리 import
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    CHART_AVAILABLE = True
except ImportError:
    CHART_AVAILABLE = False
    print("⚠️ matplotlib를 찾을 수 없습니다.")


class SimulationResultWidget(QWidget):
    """테스트 결과 차트 & 기록 위젯 - 원본 완전 복제"""
    
    # 시그널 정의
    result_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.initialize_default_state()
    
    def setup_ui(self):
        """UI 구성 - 원본 create_test_result_area()와 정확히 동일"""
        # 메인 그룹박스 (원본과 정확히 동일한 스타일)
        self.group = QGroupBox("테스트 결과 차트")
        self.group.setStyleSheet(self._get_original_group_style())
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.group)
        
        layout = QVBoxLayout(self.group)
        
        # 미니 차트 영역 - matplotlib 차트 또는 대체 라벨 (원본과 동일)
        if CHART_AVAILABLE:
            try:
                self.mini_chart_widget = self.create_mini_chart_widget()
                layout.addWidget(self.mini_chart_widget)
                print("✅ 미니 차트 위젯 생성 완료")
            except Exception as e:
                print(f"❌ 차트 위젯 생성 실패: {e}")
                chart_label = self.create_fallback_chart_label()
                layout.addWidget(chart_label)
        else:
            chart_label = self.create_fallback_chart_label()
            layout.addWidget(chart_label)
        
        # 작동 기록 리스트 (원본과 정확히 동일)
        self.test_history_list = QListWidget()
        self.test_history_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
                max-height: 280px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f0f0f0;
                margin: 2px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
        """)
        
        layout.addWidget(QLabel("🕐 작동 기록:"))
        layout.addWidget(self.test_history_list)
    
    def create_mini_chart_widget(self):
        """미니 차트 위젯 생성 - 원본과 동일"""
        chart_widget = QWidget()
        layout = QVBoxLayout(chart_widget)
        layout.setContentsMargins(2, 2, 2, 2)
        
        if CHART_AVAILABLE:
            try:
                self.figure = Figure(figsize=(4, 2), dpi=80)
                self.canvas = FigureCanvas(self.figure)
                self.canvas.setMaximumHeight(180)
                layout.addWidget(self.canvas)
                
                # 초기 차트 표시
                self.show_placeholder_chart()
                
            except Exception as e:
                print(f"⚠️ 미니 차트 생성 실패: {e}")
                text_label = QLabel("� 차트 영역\n시뮬레이션 결과가 표시됩니다.")
                text_label.setMaximumHeight(180)
                layout.addWidget(text_label)
        else:
            text_label = QLabel("📈 차트 영역\n시뮬레이션 결과가 표시됩니다.")
            text_label.setMaximumHeight(180)
            layout.addWidget(text_label)
        
        return chart_widget
    
    def create_fallback_chart_label(self):
        """차트 라이브러리가 없을 때 대체 라벨 - 원본과 동일"""
        chart_label = QLabel("📊 미니 차트 영역")
        chart_label.setStyleSheet("""
            border: 3px dashed #fd7e14;
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            color: #fd7e14;
            font-weight: bold;
            font-size: 14px;
            background-color: #fff8f0;
            min-height: 180px;
        """)
        chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return chart_label
    
    def show_placeholder_chart(self):
        """플레이스홀더 차트 표시 - 원본과 동일"""
        if not CHART_AVAILABLE or not hasattr(self, 'figure'):
            return
        
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # 플레이스홀더 데이터
            x = range(10)
            y = [0] * 10
            
            ax.plot(x, y, 'b-', linewidth=1)
            ax.set_title('차트 대기 중', fontsize=8)
            ax.set_ylabel('가격', fontsize=7)
            ax.tick_params(axis='both', which='major', labelsize=6)
            ax.grid(True, alpha=0.3)
            
            self.figure.tight_layout(pad=0.5)
            self.canvas.draw()
            
        except Exception as e:
            print(f"⚠️ 플레이스홀더 차트 표시 실패: {e}")
    
    def update_simulation_chart(self, scenario, price_data, trigger_results):
        """시뮬레이션 결과로 차트 업데이트 - 원본과 동일"""
        if not CHART_AVAILABLE or not hasattr(self, 'figure'):
            return
        
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            if price_data:
                # 가격 데이터 플롯
                x = range(len(price_data))
                ax.plot(x, price_data, 'b-', linewidth=1, label='가격')
                
                # 트리거 포인트 표시
                if trigger_results:
                    for i, (triggered, _) in enumerate(trigger_results):
                        if triggered and i < len(price_data):
                            ax.scatter(i, price_data[i], c='red', s=20, marker='^', zorder=5)
            
            ax.set_title(f'{scenario} 결과', fontsize=8)
            ax.set_ylabel('가격', fontsize=7)
            ax.tick_params(axis='both', which='major', labelsize=6)
            ax.grid(True, alpha=0.3)
            
            self.figure.tight_layout(pad=0.5)
            self.canvas.draw()
            
        except Exception as e:
            print(f"⚠️ 시뮬레이션 차트 업데이트 실패: {e}")
    
    def _get_original_group_style(self):
        """원본 그룹박스 스타일"""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #fd7e14;
                border-radius: 8px;
                margin-top: 1ex;
                padding: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #fd7e14;
                background-color: white;
            }
        """
    
    def initialize_default_state(self):
        """기본 상태 초기화 - 원본과 동일"""
        self.add_test_history_item("시스템 시작", "ready")
    
    def add_test_history_item(self, message: str, status: str = "info"):
        """테스트 기록 추가 - 원본과 동일"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 상태별 아이콘 (원본과 동일)
        status_icons = {
            "ready": "✅",
            "running": "🔄", 
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        
        icon = status_icons.get(status, "ℹ️")
        item_text = f"{icon} [{timestamp}] {message}"
        
        item = QListWidgetItem(item_text)
        self.test_history_list.addItem(item)
        
        # 최신 항목으로 스크롤
        self.test_history_list.scrollToBottom()
        
        # 최대 100개 항목 유지
        if self.test_history_list.count() > 100:
            self.test_history_list.takeItem(0)
    
    def add_simulation_log(self, result):
        """시뮬레이션 결과 로그 추가"""
        scenario = result.get('scenario', 'Unknown')
        trigger_count = result.get('trigger_count', 0)
        success_rate = result.get('success_rate', 0.0)
        profit_loss = result.get('profit_loss', 0.0)
        
        message = f"{scenario}: 트리거 {trigger_count}회, 성공률 {success_rate:.1f}%, 수익률 {profit_loss:+.2f}%"
        self.add_test_history_item(message, "success" if profit_loss > 0 else "warning")
        status_icons = {
            "ready": "🟢",
            "running": "🔄", 
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "info": "💡"
        }
        
        icon = status_icons.get(status, "💡")
        full_message = f"{icon} [{timestamp}] {message}"
        
        # 리스트에 추가 (최신이 위로)
        item = QListWidgetItem(full_message)
        self.test_history_list.insertItem(0, item)
        
        # 최대 50개까지만 유지
        if self.test_history_list.count() > 50:
            self.test_history_list.takeItem(self.test_history_list.count() - 1)
    
    def update_chart(self, scenario: str, price_data: list, trigger_results: list = None):
        """차트 업데이트 - 원본 인터페이스"""
        if trigger_results is None:
            trigger_results = []
        if hasattr(self.mini_chart, 'update_simulation_chart'):
            self.mini_chart.update_simulation_chart(scenario, price_data, trigger_results)
    
    def update_simulation_result(self, scenario: str, trigger_data: dict, result: dict):
        """시뮬레이션 결과 업데이트"""
        try:
            trigger_name = trigger_data.get('name', 'Unknown') if trigger_data else 'Unknown'
            success = result.get('success', False)
            
            if success:
                # 성공 케이스
                self.add_test_history_item(f"{scenario} 시뮬레이션 완료: {trigger_name}", "success")
                
                # 상세 결과 텍스트 업데이트
                result_text = self._format_success_result(scenario, trigger_data, result)
                self.test_result_text.setText(result_text)
                
            else:
                # 실패 케이스
                error_msg = result.get('error', 'Unknown error')
                self.add_test_history_item(f"{scenario} 시뮬레이션 실패: {error_msg}", "error")
                
                # 에러 결과 텍스트 업데이트
                error_text = self._format_error_result(scenario, trigger_data, result)
                self.test_result_text.setText(error_text)
            
            # 결과 업데이트 시그널 발송
            self.result_updated.emit(result)
            
        except Exception as e:
            self.add_test_history_item(f"결과 업데이트 오류: {e}", "error")
            print(f"❌ 시뮬레이션 결과 업데이트 실패: {e}")
    
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
    
    def _get_original_history_style(self):
        """원본 작동 기록 리스트 스타일과 정확히 동일"""
        return """
            QListWidget {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
                max-height: 120px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
                margin: 2px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
        """
    
    def _get_original_text_style(self):
        """원본 상세 결과 텍스트 스타일과 정확히 동일"""
        return """
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 8px;
                font-size: 10px;
                background-color: white;
                max-height: 120px;
            }
        """
    
    def update_simulation_result(self, scenario: str, trigger_data: dict, result: dict):
        """시뮬레이션 결과 업데이트"""
        try:
            trigger_name = trigger_data.get('name', 'Unknown') if trigger_data else 'Unknown'
            success = result.get('success', False)
            
            if success:
                # 성공 케이스
                self.add_test_history_item(f"{scenario} 시뮬레이션 완료: {trigger_name}", "success")
                
                # 상세 결과 텍스트 업데이트
                result_text = self._format_success_result(scenario, trigger_data, result)
                self.test_result_text.setText(result_text)
                
            else:
                # 실패 케이스
                error_msg = result.get('error', 'Unknown error')
                self.add_test_history_item(f"{scenario} 시뮬레이션 실패: {error_msg}", "error")
                
                # 에러 결과 텍스트 업데이트
                error_text = self._format_error_result(scenario, trigger_data, result)
                self.test_result_text.setText(error_text)
            
            # 결과 업데이트 시그널 발송
            self.result_updated.emit(result)
            
        except Exception as e:
            self.add_test_history_item(f"결과 업데이트 오류: {e}", "error")
            print(f"❌ 시뮬레이션 결과 업데이트 실패: {e}")
    
    def _format_success_result(self, scenario: str, trigger_data: dict, result: dict) -> str:
        """성공 결과 포맷팅"""
        trigger_name = trigger_data.get('name', 'Unknown') if trigger_data else 'Unknown'
        variable = trigger_data.get('variable', 'Unknown') if trigger_data else 'Unknown'
        operator = trigger_data.get('operator', 'Unknown') if trigger_data else 'Unknown'
        value = trigger_data.get('value', 'Unknown') if trigger_data else 'Unknown'
        
        # 시뮬레이션 데이터 추출
        simulation_data = result.get('simulation_data', {})
        triggered = result.get('triggered', False)
        trigger_points = result.get('trigger_points', [])
        
        result_text = f"""🎯 {scenario} 시뮬레이션 결과
        
📋 트리거 정보:
• 이름: {trigger_name}
• 조건: {variable} {operator} {value}

📊 시뮬레이션 데이터:
• 시나리오: {scenario}
• 데이터 포인트: {len(simulation_data.get('prices', []))}개
• 트리거 발생: {'예' if triggered else '아니오'}
• 발생 횟수: {len(trigger_points)}회

🔥 트리거 발생 지점:
{self._format_trigger_points(trigger_points)}

⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return result_text.strip()
    
    def _format_error_result(self, scenario: str, trigger_data: dict, result: dict) -> str:
        """에러 결과 포맷팅"""
        trigger_name = trigger_data.get('name', 'Unknown') if trigger_data else 'Unknown'
        error_msg = result.get('error', 'Unknown error')
        
        error_text = f"""❌ {scenario} 시뮬레이션 실패
        
📋 트리거 정보:
• 이름: {trigger_name}

🚨 오류 내용:
{error_msg}

⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💡 해결 방법:
1. 트리거 설정을 확인해주세요
2. 변수 파라미터가 올바른지 확인해주세요
3. 시뮬레이션 엔진 상태를 확인해주세요
"""
        
        return error_text.strip()
    
    def export_results(self) -> dict:
        """결과 내보내기"""
        return {
            'history_count': self.test_history_list.count(),
            'current_result': self.test_result_text.toPlainText(),
            'export_time': datetime.now().isoformat()
        }
    
    def get_history_count(self) -> int:
        """기록 개수 반환"""
        return self.test_history_list.count()


if __name__ == "__main__":
    # 테스트용 코드
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    widget = SimulationResultWidget()
    widget.show()
    
    # 테스트 결과 추가
    test_trigger = {
        'name': 'RSI 과매수 테스트',
        'variable': 'rsi',
        'operator': '>',
        'value': '70'
    }
    
    test_result = {
        'success': True,
        'triggered': True,
        'trigger_points': [
            {'timestamp': '10:15:30', 'value': 72.5},
            {'timestamp': '10:20:45', 'value': 75.1}
        ],
        'simulation_data': {
            'prices': [100, 102, 105, 108, 110]
        }
    }
    
    widget.update_simulation_result("📈 상승", test_trigger, test_result)
    
    sys.exit(app.exec())
