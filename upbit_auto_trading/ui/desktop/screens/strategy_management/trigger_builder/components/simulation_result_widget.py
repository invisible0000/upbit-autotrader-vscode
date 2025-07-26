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
        
        # 마지막 시뮬레이션 결과 저장용 변수들
        self._last_scenario = None
        self._last_price_data = None
        self._last_trigger_results = None
        
        self.setup_ui()
        self.initialize_default_state()
        
        # 테마 변경 신호 연결
        try:
            from upbit_auto_trading.ui.desktop.common.theme_notifier import get_theme_notifier
            theme_notifier = get_theme_notifier()
            theme_notifier.theme_changed.connect(self._on_theme_changed)
        except Exception as e:
            print(f"⚠️ 테마 변경 신호 연결 실패: {e}")
    
    def _on_theme_changed(self, is_dark: bool):
        """테마 변경 시 호출되는 슬롯"""
        # 현재 표시된 차트를 다시 그리기 (로그 메시지 제거)
        if hasattr(self, 'figure') and CHART_AVAILABLE:
            # 마지막 시뮬레이션 결과가 있으면 그것으로 업데이트, 없으면 플레이스홀더
            if (self._last_scenario and self._last_price_data is not None and 
                    self._last_trigger_results is not None):
                self.update_simulation_chart(self._last_scenario, self._last_price_data, 
                                             self._last_trigger_results)
            else:
                self.show_placeholder_chart()
    
    def setup_ui(self):
        """UI 구성 - 원본 create_test_result_area()와 정확히 동일"""
        # 메인 그룹박스 (스타일은 애플리케이션 테마를 따름)
        self.group = QGroupBox("📊 시뮬레이션 결과 & 미니차트")
        # 기본 스타일 적용 (다른 위젯들과 통일)
        # self.group.setStyleSheet(self._get_original_group_style())  # 기본 스타일 제거
        
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
        
        # 작동 기록 리스트 (애플리케이션 테마를 따름)
        self.test_history_list = QListWidget()
        # 4줄 표시되도록 높이 설정 (대략 줄당 30px + 여백)
        self.test_history_list.setMaximumHeight(130)
        self.test_history_list.setMinimumHeight(130)
        # 스크롤바 정책 설정 - 필요시 스크롤바 표시
        from PyQt6.QtCore import Qt
        self.test_history_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.test_history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # 하드코딩된 스타일 제거 - QSS 테마를 따름
        
        layout.addWidget(QLabel("📋 트리거 신호:"))  # 사용자에게 직관적이고 에이전트 기능 색인에 용이
        layout.addWidget(self.test_history_list)
    
    def create_mini_chart_widget(self):
        """미니 차트 위젯 생성 - 테마 적용"""
        chart_widget = QWidget()
        layout = QVBoxLayout(chart_widget)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # 차트 위젯 배경을 테마에 맞게 설정
        chart_widget.setObjectName("chart_widget")  # QSS 선택자용
        
        if CHART_AVAILABLE:
            try:
                # 차트 크기를 더 크게 설정하여 테스트 결과 박스 공간을 최대한 활용
                self.figure = Figure(figsize=(6, 4), dpi=80)
                self.canvas = FigureCanvas(self.figure)
                # 최대 높이를 더 크게 설정
                # 테스트: 고정 크기 제약 제거
                # self.canvas.setMaximumHeight(300)
                # self.canvas.setMinimumHeight(250)
                self.canvas.setMinimumHeight(200)  # 최소 높이만 설정
                
                # Canvas 배경을 테마에 맞게 설정
                self.canvas.setObjectName("chart_canvas")  # QSS 선택자용
                
                layout.addWidget(self.canvas)
                
                # 초기 차트 표시
                self.show_placeholder_chart()
                
            except Exception as e:
                print(f"⚠️ 미니 차트 생성 실패: {e}")
                text_label = QLabel("📈 차트 영역\n시뮬레이션 결과가 표시됩니다.")
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
        """플레이스홀더 차트 표시 - 전역 테마 신호 사용"""
        if not CHART_AVAILABLE or not hasattr(self, 'figure'):
            return
        
        try:
            # 전역 테마 매니저 사용
            from upbit_auto_trading.ui.desktop.common.theme_notifier import apply_matplotlib_theme_simple, get_theme_notifier
            apply_matplotlib_theme_simple()
            
            # 테마에 따른 색상 설정
            theme_notifier = get_theme_notifier()
            is_dark = theme_notifier.is_dark_theme()
            line_color = '#60a5fa' if is_dark else '#3498db'  # 다크: 연한 파랑, 라이트: 진한 파랑
            bg_color = '#2c2c2c' if is_dark else 'white'  # 배경색
            
            # Figure와 Canvas 배경색 명시적 설정
            self.figure.patch.set_facecolor(bg_color)
            if hasattr(self, 'canvas'):
                self.canvas.setStyleSheet(f"background-color: {bg_color};")
            
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # 플레이스홀더 데이터
            x = range(10)
            y = [0] * 10
            
            ax.plot(x, y, line_color, linewidth=1)
            # 차트 제목 제거하여 더 큰 차트 공간 확보
            # ax.set_title('Chart Ready', fontsize=8)
            ax.set_ylabel('Price', fontsize=10)  # Y축 라벨 크기 증가
            
            # Y축 틱 라벨 포맷팅 (3자 이내)
            def format_y_tick(value, pos):
                if value >= 1000000:
                    return f"{value / 1000000:.1f}m"
                elif value >= 1000:
                    return f"{value / 1000:.0f}k"
                elif value >= 1:
                    return f"{value:.0f}"
                else:
                    return f"{value:.1f}"
            
            from matplotlib.ticker import FuncFormatter
            ax.yaxis.set_major_formatter(FuncFormatter(format_y_tick))
            
            ax.tick_params(axis='both', which='major', labelsize=12)  # 6에서 12로 2배 증가
            
            # X축 틱 라벨 포맷팅 (데이터 인덱스 표시)
            ax.set_xticks(range(0, 10, 2))
            ax.set_xticklabels([str(i) for i in range(0, 10, 2)])
            
            ax.grid(True, alpha=0.3)
            
            # subplot 배경색도 설정
            ax.set_facecolor(bg_color)
            
            # tight_layout 제거 - 틱 라벨 크기에 영향을 줄 수 있음 (플레이스홀더)
            # self.figure.tight_layout(pad=0.5)
            self.canvas.draw()
            
        except Exception as e:
            print(f"⚠️ 플레이스홀더 차트 표시 실패: {e}")
    
    def update_simulation_chart(self, scenario, price_data, trigger_results):
        """시뮬레이션 결과로 차트 업데이트 - 전역 테마 신호 사용"""
        if not CHART_AVAILABLE or not hasattr(self, 'figure'):
            return
        
        # 마지막 결과 저장 (테마 변경 시 재사용)
        self._last_scenario = scenario
        self._last_price_data = price_data
        self._last_trigger_results = trigger_results
        
        try:
            # 전역 테마 매니저 사용
            from upbit_auto_trading.ui.desktop.common.theme_notifier import apply_matplotlib_theme_simple, get_theme_notifier
            apply_matplotlib_theme_simple()
            
            # 테마에 따른 색상 설정
            theme_notifier = get_theme_notifier()
            is_dark = theme_notifier.is_dark_theme()
            line_color = '#60a5fa' if is_dark else '#3498db'  # 다크: 연한 파랑, 라이트: 진한 파랑
            trigger_color = '#f87171' if is_dark else '#ef4444'  # 다크: 연한 빨강, 라이트: 진한 빨강
            bg_color = '#2c2c2c' if is_dark else 'white'  # 배경색
            
            # Figure와 Canvas 배경색 명시적 설정
            self.figure.patch.set_facecolor(bg_color)
            if hasattr(self, 'canvas'):
                self.canvas.setStyleSheet(f"background-color: {bg_color};")
            
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            if price_data:
                # 가격 데이터 플롯
                x = range(len(price_data))
                ax.plot(x, price_data, line_color, linewidth=1, label='Price')
                
                # 트리거 포인트 표시 및 작동 기록 추가
                if trigger_results:
                    trigger_count = 0
                    # 기존 작동 기록 클리어 (새 시뮬레이션 시작)
                    self.test_history_list.clear()
                    
                    for i, (triggered, _) in enumerate(trigger_results):
                        if triggered and i < len(price_data):
                            ax.scatter(i, price_data[i], c=trigger_color, s=20, marker='^', zorder=5)
                            trigger_count += 1
                            # 각 트리거 발생 지점을 작동 기록에 추가 (인덱스 번호 사용)
                            self.add_test_history_item(f"[{i:03d}] 트리거 발동 #{trigger_count}: 가격 {price_data[i]:,.0f}", "success")
                    
                    if trigger_count > 0:
                        ax.scatter([], [], c=trigger_color, s=20, marker='^', label=f'Triggers ({trigger_count})', zorder=5)
            
            # 차트 제목 제거하여 더 큰 차트 공간 확보
            # ax.set_title(f'{scenario} Result', fontsize=8)
            ax.set_ylabel('Price', fontsize=10)  # Y축 라벨 크기 증가
            
            # Y축 틱 라벨 포맷팅 (3자 이내)
            def format_y_tick(value, pos):
                if value >= 1000000:
                    return f"{value / 1000000:.1f}m"
                elif value >= 1000:
                    return f"{value / 1000:.0f}k"
                elif value >= 1:
                    return f"{value:.0f}"
                else:
                    return f"{value:.1f}"
            
            from matplotlib.ticker import FuncFormatter
            ax.yaxis.set_major_formatter(FuncFormatter(format_y_tick))
            
            ax.tick_params(axis='both', which='major', labelsize=12)  # 6에서 12로 2배 증가
            
            # X축 틱 라벨 포맷팅 (데이터 인덱스 표시)
            if price_data and len(price_data) > 5:
                x_tick_positions = range(0, len(price_data), max(1, len(price_data) // 5))
                ax.set_xticks(x_tick_positions)
                ax.set_xticklabels([str(i) for i in x_tick_positions])
            
            ax.grid(True, alpha=0.3)
            
            # subplot 배경색도 설정
            ax.set_facecolor(bg_color)
            
            # tight_layout 제거 - 틱 라벨 크기에 영향을 줄 수 있음 (시뮬레이션)
            # self.figure.tight_layout(pad=0.5)
            self.canvas.draw()
            
        except Exception as e:
            print(f"⚠️ 시뮬레이션 차트 업데이트 실패: {e}")
    
    def update_trigger_signals(self, simulation_result_data):
        """트리거 신호들을 작동 기록에 업데이트"""
        try:
            scenario = simulation_result_data.get('scenario', 'Unknown')
            price_data = simulation_result_data.get('price_data', [])
            trigger_points = simulation_result_data.get('trigger_points', [])
            result_text = simulation_result_data.get('result_text', 'UNKNOWN')
            condition_name = simulation_result_data.get('condition_name', 'Unknown')
            
            # 기존 작동 기록 클리어 (새 시뮬레이션 시작)
            self.test_history_list.clear()
            
            # 개별 트리거 신호들을 작동 기록에 추가
            if trigger_points and len(trigger_points) > 0:
                for idx, point_idx in enumerate(trigger_points):
                    if 0 <= point_idx < len(price_data):
                        price_value = price_data[point_idx]
                        signal_detail = f"[{point_idx:03d}] 트리거 발동 #{idx+1}: 가격 {price_value:,.0f}"
                        self.add_test_history_item(signal_detail, "success")
            else:
                # 신호가 없을 때 메시지
                self.add_test_history_item(f"{scenario}: 검출된 신호 없음", "info")
            
            print(f"✅ 트리거 신호 업데이트 완료: {len(trigger_points)}개 신호")
            
        except Exception as e:
            print(f"❌ 트리거 신호 업데이트 실패: {e}")
            self.add_test_history_item(f"신호 업데이트 오류: {e}", "error")
    
    def _get_original_group_style(self):
        """원본 그룹박스 스타일 - 하드코딩된 배경색 제거"""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #fd7e14;
                border-radius: 8px;
                margin-top: 1ex;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #fd7e14;
            }
        """
    
    def initialize_default_state(self):
        """기본 상태 초기화 - 원본과 동일"""
        self.add_test_history_item("시스템 시작", "ready")
    
    def add_test_history_item(self, message: str, status: str = "info"):
        """테스트 기록 추가 - 시간 대신 메시지에 이미 포함된 인덱스 사용"""
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
        # 트리거 발동 메시지의 경우 이미 인덱스가 포함되어 있으므로 시간 제거
        if "트리거 발동" in message and "[" in message:
            item_text = f"{icon} {message}"
        else:
            # 일반 메시지는 시간 포함
            timestamp = datetime.now().strftime("%H:%M:%S")
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
            
            # 이전 결과 모두 지우기 (최근 시뮬레이션 결과만 표시)
            self.test_history_list.clear()
            
            if success:
                # 성공 케이스 - 작동 기록에만 추가
                self.add_test_history_item(f"{scenario} 시뮬레이션 완료: {trigger_name}", "success")
                
            else:
                # 실패 케이스 - 작동 기록에만 추가
                error_msg = result.get('error', 'Unknown error')
                self.add_test_history_item(f"{scenario} 시뮬레이션 실패: {error_msg}", "error")
            
            # 결과 업데이트 시그널 발송
            self.result_updated.emit(result)
            
        except Exception as e:
            self.add_test_history_item(f"결과 업데이트 오류: {e}", "error")
            print(f"❌ 시뮬레이션 결과 업데이트 실패: {e}")

    def export_results(self) -> dict:
        """결과 내보내기"""
        return {
            'history_count': self.test_history_list.count(),
            'export_time': datetime.now().isoformat()
        }
    
    def update_chart_with_simulation_results(self, chart_simulation_data, trigger_results):
        """시뮬레이션 결과로 차트 및 기록 업데이트"""
        try:
            scenario = chart_simulation_data.get('scenario', 'Unknown')
            price_data = chart_simulation_data.get('price_data', [])
            trigger_points = trigger_results.get('trigger_points', [])
            
            # 차트 업데이트
            if price_data:
                # 트리거 결과를 (triggered, value) 튜플 리스트로 변환
                trigger_results_for_chart = []
                for i, value in enumerate(price_data):
                    triggered = i in trigger_points
                    trigger_results_for_chart.append((triggered, value))
                
                self.update_simulation_chart(scenario, price_data, trigger_results_for_chart)
            
            # 트리거 신호들을 작동 기록에 추가
            simulation_result_data = {
                'scenario': scenario,
                'price_data': price_data,
                'trigger_points': trigger_points,
                'result_text': "✅ PASS" if len(trigger_points) > 0 else "❌ FAIL",
                'condition_name': chart_simulation_data.get('condition_name', 'Unknown')
            }
            self.update_trigger_signals(simulation_result_data)
            
            print(f"✅ 차트 및 기록 업데이트 완료: {len(trigger_points)}개 신호")
            
        except Exception as e:
            print(f"❌ 차트 및 기록 업데이트 실패: {e}")
            self.add_test_history_item(f"차트 업데이트 오류: {e}", "error")

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
