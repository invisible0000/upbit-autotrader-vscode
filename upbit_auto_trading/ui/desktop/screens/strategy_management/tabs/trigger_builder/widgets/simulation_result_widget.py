"""
시뮬레이션 결과 위젯 - Legacy UI 기반 MVP 구현
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QHBoxLayout, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("SimulationResultWidget")

# matplotlib 차트 지원 (선택적)
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    CHART_AVAILABLE = True
    logger.debug("matplotlib 차트 라이브러리 로드 성공")
except ImportError:
    CHART_AVAILABLE = False
    FigureCanvas = None
    Figure = None
    logger.warning("matplotlib 차트 라이브러리를 찾을 수 없습니다")


class SimulationResultWidget(QWidget):
    """시뮬레이션 결과 위젯 - MVP 패턴"""

    # 시그널 정의
    result_updated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_scenario = None
        self.current_data_source = "embedded"

        # matplotlib 폰트 설정을 초기화 시 한 번만 수행
        self._setup_matplotlib_font_once()

        self.setup_ui()
        self.initialize_default_state()
        self.setup_use_cases()

    def _setup_matplotlib_font_once(self):
        """matplotlib 폰트를 초기화 시 한 번만 설정"""
        if not CHART_AVAILABLE:
            return

        try:
            import matplotlib
            # matplotlib 폰트 매니저의 디버그 로깅 비활성화
            matplotlib.set_loglevel('WARNING')

            import matplotlib.pyplot as plt
            import matplotlib.font_manager as fm

            # 폰트 캐시 재구성 방지 및 한 번만 설정
            plt.rcParams['font.family'] = 'Malgun Gothic'
            plt.rcParams['axes.unicode_minus'] = False

            # 폰트가 사용 가능한지 확인 (로그 최소화)
            try:
                available_fonts = [f.name for f in fm.fontManager.ttflist]
                if 'Malgun Gothic' not in available_fonts:
                    plt.rcParams['font.family'] = 'DejaVu Sans'
                    logger.warning("Malgun Gothic font not available, using DejaVu Sans")
                else:
                    logger.debug("Malgun Gothic font configured successfully")
            except Exception:
                plt.rcParams['font.family'] = 'DejaVu Sans'

        except Exception as e:
            logger.warning(f"matplotlib font setup failed: {e}")

    def setup_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 상단 제어 버튼들
        self.create_control_buttons(main_layout)

        # 결과 표시 영역
        if CHART_AVAILABLE:
            self.create_chart_area(main_layout)
        else:
            self.create_text_area(main_layout)

        # 하단 로그 영역
        self.create_log_area(main_layout)

    def create_control_buttons(self, parent_layout):
        """제어 버튼 영역"""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        # 결과 초기화 버튼
        clear_btn = QPushButton("🗑️ 초기화")
        clear_btn.setMaximumHeight(25)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        clear_btn.clicked.connect(self.clear_results)
        btn_layout.addWidget(clear_btn)

        # 결과 저장 버튼
        save_btn = QPushButton("💾 저장")
        save_btn.setMaximumHeight(25)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
        """)
        save_btn.clicked.connect(self.save_results)
        btn_layout.addWidget(save_btn)

        btn_layout.addStretch()
        parent_layout.addLayout(btn_layout)

    def create_chart_area(self, parent_layout):
        """차트 영역 생성 (matplotlib 사용)"""
        if not CHART_AVAILABLE or Figure is None or FigureCanvas is None:
            # matplotlib이 없으면 텍스트 영역으로 대체
            self.create_text_area(parent_layout)
            return

        # matplotlib 차트 캔버스 (폰트는 __init__에서 이미 설정됨)
        self.figure = Figure(figsize=(8, 4), dpi=80)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(200)

        # 기본 차트 설정
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Simulation Results")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Return (%)")
        self.ax.grid(True, alpha=0.3)

        parent_layout.addWidget(self.canvas)

    def create_text_area(self, parent_layout):
        """텍스트 기반 결과 영역 (matplotlib 없을 때)"""
        self.result_label = QLabel("Simulation results will be displayed here.")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setMinimumHeight(200)
        self.result_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
                font-family: monospace;
            }
        """)
        parent_layout.addWidget(self.result_label)

    def create_log_area(self, parent_layout):
        """로그 영역 생성"""
        # 로그 제목
        log_label = QLabel("📝 시뮬레이션 로그")
        log_label.setStyleSheet("font-weight: bold; margin: 5px 0;")
        parent_layout.addWidget(log_label)

        # 로그 리스트
        self.log_list = QListWidget()
        self.log_list.setMaximumHeight(100)
        self.log_list.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: monospace;
                font-size: 10px;
            }
            QListWidget::item {
                padding: 2px 5px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
        """)
        parent_layout.addWidget(self.log_list)

    def initialize_default_state(self):
        """기본 상태 초기화"""
        self.add_log("Simulation result widget initialized")

        if CHART_AVAILABLE and hasattr(self, 'ax'):
            # 기본 차트 표시
            self.ax.text(0.5, 0.5, 'Run simulation to see results',
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax.transAxes,
                        fontsize=12,
                        alpha=0.6)
            self.canvas.draw()

    def update_simulation_result(self, scenario_type, result_data=None):
        """시뮬레이션 결과 업데이트"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        if result_data is None:
            # 샘플 데이터로 시뮬레이션
            result_data = self._generate_sample_result(scenario_type)

        self.add_log(f"[{timestamp}] {scenario_type} simulation completed")

        if CHART_AVAILABLE:
            self._update_chart(scenario_type, result_data)
        else:
            self._update_text_result(scenario_type, result_data)

        self.result_updated.emit(result_data)

    def _generate_sample_result(self, scenario_type):
        """샘플 결과 데이터 생성"""
        import random

        # 시나리오별 샘플 데이터
        scenarios = {
            "uptrend": {"return": 15.5, "trades": 8, "win_rate": 75.0},
            "downtrend": {"return": -8.2, "trades": 6, "win_rate": 33.3},
            "surge": {"return": 25.8, "trades": 3, "win_rate": 100.0},
            "crash": {"return": -15.6, "trades": 4, "win_rate": 25.0},
            "sideways": {"return": 2.1, "trades": 12, "win_rate": 58.3},
            "ma_cross": {"return": 8.7, "trades": 5, "win_rate": 60.0},
            "full_test": {"return": 12.3, "trades": 25, "win_rate": 68.0}
        }

        base_data = scenarios.get(scenario_type, {"return": 0, "trades": 0, "win_rate": 50})

        # 약간의 랜덤 변화 추가
        return {
            "scenario": scenario_type,
            "total_return": base_data["return"] + random.uniform(-2, 2),
            "total_trades": base_data["trades"],
            "win_rate": base_data["win_rate"] + random.uniform(-5, 5),
            "max_drawdown": abs(base_data["return"]) * 0.3,
            "timestamp": datetime.now()
        }

    def _update_chart(self, scenario_type, result_data):
        """차트 업데이트"""
        self.ax.clear()
        self.ax.set_title(f"시뮬레이션 결과: {scenario_type}")
        self.ax.set_xlabel("거래 횟수")
        self.ax.set_ylabel("누적 수익률 (%)")

        # 샘플 누적 수익률 데이터 생성
        trades = range(1, int(result_data["total_trades"]) + 1)
        final_return = result_data["total_return"]
        cumulative_returns = [final_return * (i / len(trades)) for i in trades]

        self.ax.plot(trades, cumulative_returns, marker='o', linewidth=2)
        self.ax.grid(True, alpha=0.3)
        self.ax.axhline(y=0, color='r', linestyle='--', alpha=0.5)

        self.canvas.draw()

    def _update_text_result(self, scenario_type, result_data):
        """텍스트 결과 업데이트"""
        result_text = f"""
시뮬레이션 결과: {scenario_type}

📊 수익률: {result_data['total_return']:.2f}%
🎯 거래 횟수: {result_data['total_trades']}회
✅ 승률: {result_data['win_rate']:.1f}%
📉 최대 손실: {result_data['max_drawdown']:.2f}%

실행 시간: {result_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()

        self.result_label.setText(result_text)

    def add_log(self, message):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_item = QListWidgetItem(f"[{timestamp}] {message}")
        self.log_list.addItem(log_item)
        self.log_list.scrollToBottom()

        # 로그 개수 제한 (최대 50개)
        if self.log_list.count() > 50:
            self.log_list.takeItem(0)

    def clear_results(self):
        """결과 초기화"""
        if CHART_AVAILABLE:
            self.ax.clear()
            self.initialize_default_state()
            self.canvas.draw()
        else:
            self.result_label.setText("시뮬레이션 결과가 여기에 표시됩니다.")

        self.log_list.clear()
        self.add_log("결과 초기화 완료")

    def save_results(self):
        """결과 저장 (추후 구현)"""
        self.add_log("결과 저장 기능 (추후 구현 예정)")
        logger.info("시뮬레이션 결과 저장 요청")

    def setup_use_cases(self):
        """UseCase 설정 - DDD 패턴"""
        try:
            from upbit_auto_trading.infrastructure.repositories.simulation_data_repository import SimulationDataRepository
            from upbit_auto_trading.application.use_cases.simulation.load_simulation_data_use_case import LoadSimulationDataUseCase

            # Repository와 UseCase 초기화
            self.repository = SimulationDataRepository()
            self.load_data_use_case = LoadSimulationDataUseCase(self.repository)

            logger.debug("SimulationResultWidget UseCase 설정 완료")
        except Exception as e:
            logger.error(f"UseCase 설정 실패: {e}")
            self.load_data_use_case = None

    def run_simulation(self, scenario_type: str):
        """시뮬레이션 실행 - 실제 데이터 연동"""
        try:
            self.current_scenario = scenario_type
            self.add_log(f"시뮬레이션 시작: {scenario_type}")

            if self.load_data_use_case is None:
                self.add_log("❌ 데이터 로드 기능 초기화 실패")
                return

            # UseCase를 통한 실제 데이터 로드
            scenario_data = self.load_data_use_case.execute(scenario_type, length=100)

            # 차트 업데이트
            if CHART_AVAILABLE and scenario_data.price_data:
                self._update_chart_with_real_data(scenario_data)

            # 텍스트 결과 업데이트
            self._update_text_with_real_data(scenario_data)

            self.add_log(f"✅ 시뮬레이션 완료: {scenario_data.data_source}")

        except Exception as e:
            logger.error(f"시뮬레이션 실행 실패: {e}")
            self.add_log(f"❌ 시뮬레이션 실패: {e}")

    def _update_chart_with_real_data(self, scenario_data):
        """실제 데이터로 차트 업데이트"""
        try:
            self.ax.clear()

            # 실제 가격 데이터 플롯
            x_data = range(len(scenario_data.price_data))
            self.ax.plot(x_data, scenario_data.price_data, 'b-', linewidth=2, alpha=0.8)

            # 차트 설정
            self.ax.set_title(f'{scenario_data.scenario} 시나리오 ({scenario_data.data_source})', fontsize=14, fontweight='bold')
            self.ax.set_xlabel('시간 (데이터 포인트)')
            self.ax.set_ylabel('가격 (KRW)')
            self.ax.grid(True, alpha=0.3)

            # 수익률 표시
            if scenario_data.change_percent != 0:
                color = 'red' if scenario_data.change_percent < 0 else 'green'
                self.ax.text(0.02, 0.98, f'수익률: {scenario_data.change_percent:.2f}%',
                           transform=self.ax.transAxes,
                           fontsize=12,
                           color=color,
                           fontweight='bold',
                           verticalalignment='top')

            # 기간 정보 표시
            self.ax.text(0.02, 0.02, f'기간: {scenario_data.period}',
                        transform=self.ax.transAxes,
                        fontsize=10,
                        alpha=0.7,
                        verticalalignment='bottom')

            self.canvas.draw()

        except Exception as e:
            logger.error(f"차트 업데이트 실패: {e}")

    def _update_text_with_real_data(self, scenario_data):
        """실제 데이터로 텍스트 결과 업데이트"""
        try:
            result_text = f"""
시뮬레이션 결과: {scenario_data.scenario}

📊 수익률: {scenario_data.change_percent:.2f}%
📈 시작가: {scenario_data.base_value:,.0f} KRW
💰 현재가: {scenario_data.current_value:,.0f} KRW
📊 데이터 포인트: {scenario_data.data_points}개
🗓 기간: {scenario_data.period}
🔄 데이터 소스: {scenario_data.data_source}

실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()

            self.result_label.setText(result_text)

        except Exception as e:
            logger.error(f"텍스트 결과 업데이트 실패: {e}")

    def update_data_source(self, source_type: str):
        """데이터 소스 변경"""
        self.current_data_source = source_type
        self.add_log(f"데이터 소스 변경: {source_type}")

        # 현재 시나리오가 있으면 다시 실행
        if self.current_scenario:
            self.run_simulation(self.current_scenario)
