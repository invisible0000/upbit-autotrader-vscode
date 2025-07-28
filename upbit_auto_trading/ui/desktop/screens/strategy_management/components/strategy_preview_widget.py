"""
StrategyMaker 미니차트 통합 예시

Phase 5에서 공통 미니 시뮬레이션 시스템의 재사용성을 검증하기 위한 예시 코드
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
import traceback

# 공통 미니 시뮬레이션 시스템 import
try:
    from ..mini_simulation import (
        get_simulation_engine,
        SimulationDataSourceManager
    )
    from ..mini_simulation.engines import DataSourceType
    MINI_SIMULATION_AVAILABLE = True
    print("✅ StrategyMaker: 공통 미니 시뮬레이션 시스템 연결 성공")
except ImportError as e:
    MINI_SIMULATION_AVAILABLE = False
    print(f"⚠️ StrategyMaker: 공통 미니 시뮬레이션 시스템 연결 실패: {e}")

# matplotlib for charting
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ StrategyMaker: matplotlib 사용 불가")


class StrategyPreviewWidget(QWidget):
    """전략 프리뷰용 미니차트 위젯 - 공통 시스템 재사용 예시"""
    
    # 시그널
    preview_generated = pyqtSignal(dict)  # 프리뷰 생성 완료
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 전략 프리뷰")
        
        # 공통 시스템 사용 여부
        self.use_common_system = MINI_SIMULATION_AVAILABLE
        self.data_source_manager = None
        self.current_engine = None
        
        # UI 초기화
        self.init_ui()
        
        # 공통 시스템 초기화
        if self.use_common_system:
            self.init_common_system()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 헤더
        header = QLabel("📊 전략 프리뷰 (공통 미니 시뮬레이션 시스템 사용)")
        header.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px;")
        layout.addWidget(header)
        
        # 상태 표시
        self.status_label = QLabel()
        self.update_status()
        layout.addWidget(self.status_label)
        
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 컨트롤 버튼들
        button_layout = QHBoxLayout()
        
        self.test_engine_btn = QPushButton("🔧 엔진 테스트")
        self.test_engine_btn.clicked.connect(self.test_simulation_engine)
        button_layout.addWidget(self.test_engine_btn)
        
        self.test_data_btn = QPushButton("📊 데이터 로드 테스트")
        self.test_data_btn.clicked.connect(self.test_data_loading)
        button_layout.addWidget(self.test_data_btn)
        
        self.preview_chart_btn = QPushButton("📈 미니차트 생성")
        self.preview_chart_btn.clicked.connect(self.generate_preview_chart)
        button_layout.addWidget(self.preview_chart_btn)
        
        layout.addLayout(button_layout)
        
        # 결과 표시 영역
        self.result_text = QLabel("결과가 여기에 표시됩니다...")
        self.result_text.setWordWrap(True)
        self.result_text.setStyleSheet("background-color: #f5f5f5; padding: 10px; border: 1px solid #ddd;")
        self.result_text.setMinimumHeight(200)
        layout.addWidget(self.result_text)
        
        # 차트 영역 (matplotlib가 있는 경우)
        if MATPLOTLIB_AVAILABLE:
            self.setup_chart_area(layout)
    
    def setup_chart_area(self, layout):
        """차트 영역 설정"""
        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
    
    def init_common_system(self):
        """공통 미니 시뮬레이션 시스템 초기화"""
        try:
            self.data_source_manager = SimulationDataSourceManager()
            print("✅ StrategyMaker: 데이터 소스 매니저 초기화 성공")
        except Exception as e:
            print(f"⚠️ StrategyMaker: 데이터 소스 매니저 초기화 실패: {e}")
            self.use_common_system = False
        
        self.update_status()
    
    def update_status(self):
        """상태 업데이트"""
        if self.use_common_system:
            status = "✅ 공통 미니 시뮬레이션 시스템 사용 중"
        else:
            status = "⚠️ 공통 시스템 사용 불가 - 폴백 모드"
        
        self.status_label.setText(status)
        self.status_label.setStyleSheet(
            "color: green; font-weight: bold;" if self.use_common_system 
            else "color: orange; font-weight: bold;"
        )
    
    def test_simulation_engine(self):
        """시뮬레이션 엔진 테스트"""
        try:
            if not self.use_common_system:
                self.result_text.setText("❌ 공통 시스템을 사용할 수 없습니다.")
                return
            
            # 각 데이터 소스 타입별로 엔진 테스트
            results = []
            
            for source_type in [DataSourceType.EMBEDDED, DataSourceType.REAL_DB, 
                              DataSourceType.SYNTHETIC, DataSourceType.SIMPLE_FALLBACK]:
                try:
                    engine = get_simulation_engine(source_type)
                    engine_name = engine.name if hasattr(engine, 'name') else 'Unknown'
                    results.append(f"✅ {source_type.value}: {engine_name}")
                except Exception as e:
                    results.append(f"❌ {source_type.value}: {str(e)}")
            
            result_text = "🔧 시뮬레이션 엔진 테스트 결과:\n\n" + "\n".join(results)
            self.result_text.setText(result_text)
            
        except Exception as e:
            self.result_text.setText(f"❌ 엔진 테스트 실패: {str(e)}\n\n{traceback.format_exc()}")
    
    def test_data_loading(self):
        """데이터 로딩 테스트"""
        try:
            if not self.use_common_system:
                self.result_text.setText("❌ 공통 시스템을 사용할 수 없습니다.")
                return
            
            # 내장 엔진으로 데이터 로드 테스트
            engine = get_simulation_engine(DataSourceType.EMBEDDED)
            market_data = engine.load_market_data(limit=50)
            
            if market_data is not None and not market_data.empty:
                # 데이터 요약 정보
                summary = f"""📊 데이터 로드 성공!

📈 데이터 요약:
- 데이터 포인트: {len(market_data)}개
- 컬럼: {list(market_data.columns)}
- 기간: {market_data.index[0]} ~ {market_data.index[-1]}
- 종가 범위: {market_data['close'].min():,.0f} ~ {market_data['close'].max():,.0f}

✅ 공통 미니 시뮬레이션 시스템에서 데이터를 성공적으로 가져왔습니다!
이는 StrategyMaker에서도 TriggerBuilder와 동일한 데이터를 사용할 수 있음을 의미합니다."""
                
                self.result_text.setText(summary)
                
                # 데이터 저장 (차트 생성용)
                self.current_data = market_data
                
            else:
                self.result_text.setText("❌ 데이터 로드 실패: 빈 데이터")
                
        except Exception as e:
            self.result_text.setText(f"❌ 데이터 로드 실패: {str(e)}\n\n{traceback.format_exc()}")
    
    def generate_preview_chart(self):
        """미니차트 생성 (재사용성 검증)"""
        try:
            if not MATPLOTLIB_AVAILABLE:
                self.result_text.setText("❌ matplotlib이 사용 불가능합니다.")
                return
            
            if not hasattr(self, 'current_data') or self.current_data is None:
                self.result_text.setText("⚠️ 먼저 '📊 데이터 로드 테스트'를 실행해주세요.")
                return
            
            # 차트 그리기
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # 가격 차트
            ax.plot(self.current_data.index, self.current_data['close'], 
                   label='종가', color='blue', linewidth=1.5)
            
            # 이동평균선 (있는 경우)
            if 'sma_20' in self.current_data.columns:
                ax.plot(self.current_data.index, self.current_data['sma_20'], 
                       label='SMA20', color='red', alpha=0.7)
            
            if 'sma_60' in self.current_data.columns:
                ax.plot(self.current_data.index, self.current_data['sma_60'], 
                       label='SMA60', color='green', alpha=0.7)
            
            ax.set_title('📈 StrategyMaker 미니차트 (공통 시스템 사용)')
            ax.set_ylabel('가격 (원)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # 차트 스타일링
            self.figure.tight_layout()
            self.canvas.draw()
            
            # 결과 메시지
            chart_info = f"""📈 미니차트 생성 완료!

🎯 재사용성 검증 결과:
✅ 공통 미니 시뮬레이션 시스템의 데이터를 성공적으로 사용
✅ TriggerBuilder와 동일한 차트 생성 가능
✅ 동일한 금융지표 (SMA20, SMA60) 접근 가능

💡 이제 StrategyMaker에서도 TriggerBuilder와 동일한 품질의 
   미니차트와 시뮬레이션 기능을 사용할 수 있습니다!"""
            
            self.result_text.setText(chart_info)
            
            # 시그널 발송
            self.preview_generated.emit({
                'status': 'success',
                'data_points': len(self.current_data),
                'chart_generated': True
            })
            
        except Exception as e:
            self.result_text.setText(f"❌ 차트 생성 실패: {str(e)}\n\n{traceback.format_exc()}")
    
    def get_system_info(self):
        """시스템 정보 반환"""
        return {
            'using_common_system': self.use_common_system,
            'matplotlib_available': MATPLOTLIB_AVAILABLE,
            'data_source_manager': self.data_source_manager is not None,
            'current_engine': self.current_engine.name if self.current_engine and hasattr(self.current_engine, 'name') else None
        }
