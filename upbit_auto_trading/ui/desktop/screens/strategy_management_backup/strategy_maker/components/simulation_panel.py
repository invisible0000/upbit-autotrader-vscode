"""
StrategyMaker - 시뮬레이션 패널
공통 시뮬레이션 시스템을 활용한 전략 미리보기
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QComboBox, QLabel, QSpinBox, QTextEdit, QGroupBox
)
from PyQt6.QtCore import QThread, pyqtSignal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd

# 공통 시뮬레이션 시스템 import
try:
    from ..shared_simulation import (
        get_simulation_engine,
        create_quick_simulation,
        get_simulation_system_info
    )
    SHARED_SIMULATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 공통 시뮬레이션 시스템 import 실패: {e}")
    SHARED_SIMULATION_AVAILABLE = False

class SimulationWorker(QThread):
    """시뮬레이션 작업 쓰레드"""
    
    simulation_completed = pyqtSignal(dict)
    
    def __init__(self, engine_type: str, scenario: str, limit: int):
        super().__init__()
        self.engine_type = engine_type
        self.scenario = scenario
        self.limit = limit
    
    def run(self):
        """시뮬레이션 실행"""
        if not SHARED_SIMULATION_AVAILABLE:
            self.simulation_completed.emit({
                'error': '공통 시뮬레이션 시스템을 사용할 수 없습니다'
            })
            return
        
        try:
            result = create_quick_simulation(self.scenario, self.limit)
            self.simulation_completed.emit(result)
        except Exception as e:
            self.simulation_completed.emit({
                'error': f'시뮬레이션 실행 실패: {str(e)}'
            })

class StrategySimulationPanel(QWidget):
    """전략 시뮬레이션 패널"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.simulation_worker = None
        self.setup_ui()
        self.setup_chart()
    
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("📊 전략 시뮬레이션 (공통 시스템 활용)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # 컨트롤 패널
        control_group = QGroupBox("시뮬레이션 설정")
        control_layout = QHBoxLayout(control_group)
        
        # 엔진 선택
        control_layout.addWidget(QLabel("엔진:"))
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["robust", "embedded", "realdata"])
        control_layout.addWidget(self.engine_combo)
        
        # 시나리오 선택  
        control_layout.addWidget(QLabel("시나리오:"))
        self.scenario_combo = QComboBox()
        self.scenario_combo.addItems(["normal", "bull", "bear", "volatile"])
        control_layout.addWidget(self.scenario_combo)
        
        # 데이터 개수
        control_layout.addWidget(QLabel("데이터 개수:"))
        self.limit_spin = QSpinBox()
        self.limit_spin.setMinimum(50)
        self.limit_spin.setMaximum(1000)
        self.limit_spin.setValue(100)
        control_layout.addWidget(self.limit_spin)
        
        # 실행 버튼
        self.run_button = QPushButton("🚀 시뮬레이션 실행")
        self.run_button.clicked.connect(self.run_simulation)
        control_layout.addWidget(self.run_button)
        
        layout.addWidget(control_group)
        
        # 차트 영역
        chart_group = QGroupBox("미니차트 미리보기")
        chart_layout = QVBoxLayout(chart_group)
        
        # Matplotlib 차트
        self.figure = Figure(figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        
        layout.addWidget(chart_group)
        
        # 결과 출력 영역
        result_group = QGroupBox("시뮬레이션 결과")
        result_layout = QVBoxLayout(result_group)
        
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(150)
        result_layout.addWidget(self.result_text)
        
        layout.addWidget(result_group)
        
        # 시스템 정보 표시
        if SHARED_SIMULATION_AVAILABLE:
            self.show_system_info()
    
    def setup_chart(self):
        """차트 초기 설정"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, '시뮬레이션을 실행하세요', 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14)
        ax.set_title('전략 미리보기 차트')
        self.canvas.draw()
    
    def show_system_info(self):
        """시스템 정보 표시"""
        try:
            info = get_simulation_system_info()
            info_text = f"""
📋 공통 시뮬레이션 시스템 정보:
• 버전: {info['version']}
• 사용 가능한 엔진: {', '.join(info['available_engines'])}
• 지원 시나리오: {', '.join(info['supported_scenarios'])}

✅ 특징:
{chr(10).join(info['features'])}
            """
            self.result_text.setText(info_text)
        except Exception as e:
            self.result_text.setText(f"시스템 정보 로드 실패: {e}")
    
    def run_simulation(self):
        """시뮬레이션 실행"""
        if not SHARED_SIMULATION_AVAILABLE:
            self.result_text.setText("❌ 공통 시뮬레이션 시스템을 사용할 수 없습니다.")
            return
        
        # UI 비활성화
        self.run_button.setEnabled(False)
        self.run_button.setText("⏳ 실행 중...")
        
        # 설정 값들
        engine_type = self.engine_combo.currentText()
        scenario = self.scenario_combo.currentText()
        limit = self.limit_spin.value()
        
        # 워커 스레드 시작
        self.simulation_worker = SimulationWorker(engine_type, scenario, limit)
        self.simulation_worker.simulation_completed.connect(self.on_simulation_completed)
        self.simulation_worker.start()
    
    def on_simulation_completed(self, result):
        """시뮬레이션 완료 처리"""
        # UI 재활성화
        self.run_button.setEnabled(True)
        self.run_button.setText("🚀 시뮬레이션 실행")
        
        if 'error' in result:
            self.result_text.setText(f"❌ 오류: {result['error']}")
            return
        
        # 결과 표시
        validation = result.get('validation', {})
        result_text = f"""
🎯 시뮬레이션 완료!

📊 데이터 정보:
• 사용된 엔진: {result.get('engine_used', 'Unknown')}
• 시나리오: {result.get('scenario', 'Unknown')} 
• 레코드 수: {result.get('record_count', 0)}
• 데이터 유효성: {'✅ 유효' if validation.get('is_valid', False) else '❌ 무효'}

⚠️ 경고사항: {len(validation.get('warnings', []))}개
❌ 오류: {len(validation.get('errors', []))}개
        """
        
        if validation.get('warnings'):
            result_text += f"\n\n⚠️ 경고:\n" + "\n".join(validation['warnings'])
        
        if validation.get('errors'):
            result_text += f"\n\n❌ 오류:\n" + "\n".join(validation['errors'])
        
        self.result_text.setText(result_text)
        
        # 차트 업데이트
        data = result.get('data')
        if data is not None and not data.empty:
            self.update_chart(data)
    
    def update_chart(self, data: pd.DataFrame):
        """차트 업데이트"""
        try:
            self.figure.clear()
            
            # 2개의 서브플롯 생성
            ax1 = self.figure.add_subplot(211)  # 가격 차트
            ax2 = self.figure.add_subplot(212)  # 거래량 차트
            
            # 가격 차트 (캔들스틱 스타일)
            if all(col in data.columns for col in ['timestamp', 'open', 'high', 'low', 'close']):
                # 단순한 라인 차트로 표시
                ax1.plot(data['timestamp'], data['close'], label='Close', color='blue', linewidth=1.5)
                
                # 기술적 지표가 있으면 표시
                if 'SMA_20' in data.columns:
                    ax1.plot(data['timestamp'], data['SMA_20'], label='SMA(20)', color='red', alpha=0.7)
                if 'SMA_60' in data.columns:
                    ax1.plot(data['timestamp'], data['SMA_60'], label='SMA(60)', color='green', alpha=0.7)
                
                ax1.set_title('📈 가격 차트 (공통 시뮬레이션 시스템)')
                ax1.set_ylabel('가격 (KRW)')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
            
            # 거래량 차트
            if 'volume' in data.columns:
                ax2.bar(data['timestamp'], data['volume'], alpha=0.6, color='gray', width=0.001)
                ax2.set_title('📊 거래량')
                ax2.set_ylabel('거래량')
                ax2.set_xlabel('시간')
                ax2.grid(True, alpha=0.3)
            
            # 차트 레이아웃 조정
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            print(f"❌ 차트 업데이트 실패: {e}")

# 테스트용 메인 함수
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    widget = StrategySimulationPanel()
    widget.show()
    sys.exit(app.exec())
