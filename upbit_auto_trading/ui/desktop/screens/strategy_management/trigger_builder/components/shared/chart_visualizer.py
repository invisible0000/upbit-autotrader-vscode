"""
Chart Visualizer Component
차트 시각화를 담당하는 컴포넌트 - 변수 카테고리별 고급 표현 지원
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import numpy as np
from typing import Dict, List, Optional, Any

# 변수 표시 시스템 import
try:
    from .variable_display_system import get_variable_registry, VariableCategory, ChartDisplayType
    VARIABLE_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 변수 표시 시스템을 불러올 수 없습니다: {e}")
    VARIABLE_SYSTEM_AVAILABLE = False

# 차트 라이브러리 import
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.font_manager as fm
    
    # 시스템에서 사용 가능한 한글 폰트 찾기
    font_list = fm.findSystemFonts(fontpaths=None, fontext='ttf')
    korean_fonts = []
    
    for font_path in font_list:
        try:
            font_prop = fm.FontProperties(fname=font_path)
            font_name = font_prop.get_name()
            if any(keyword in font_name.lower() for keyword in ['malgun', 'gulim', 'dotum', 'batang', 'nanum', '맑은 고딕', '굴림']):
                korean_fonts.append(font_name)
        except:
            continue
    
    # 우선순위에 따라 폰트 설정
    preferred_fonts = ['Malgun Gothic', 'NanumGothic', 'Gulim', 'Dotum']
    selected_font = None
    
    for pref_font in preferred_fonts:
        if pref_font in korean_fonts:
            selected_font = pref_font
            break
    
    if not selected_font and korean_fonts:
        selected_font = korean_fonts[0]
    
    if selected_font:
        plt.rcParams['font.family'] = selected_font
        plt.rcParams['axes.unicode_minus'] = False
    
    CHART_AVAILABLE = True
    
except ImportError as e:
    print(f"⚠️ Matplotlib 라이브러리를 불러올 수 없습니다: {e}")
    CHART_AVAILABLE = False


class ChartVisualizer:
    """차트 시각화를 담당하는 컴포넌트"""
    
    def __init__(self):
        """초기화"""
        self.chart_figure = None
        self.chart_canvas = None
        self.chart_available = CHART_AVAILABLE
    
    def create_chart_widget(self):
        """차트 위젯 생성"""
        if not self.chart_available:
            return self.create_fallback_chart_label()
        
        try:
            self.chart_figure = Figure(figsize=(8, 4))
            self.chart_canvas = FigureCanvas(self.chart_figure)
            self.chart_canvas.setMaximumHeight(250)
            
            # 초기 샘플 데이터로 차트 설정
            self.update_chart_with_sample_data()
            
            return self.chart_canvas
            
        except Exception as e:
            print(f"❌ 차트 위젯 생성 실패: {e}")
            return self.create_fallback_chart_label()
    
    def create_fallback_chart_label(self):
        """차트를 사용할 수 없을 때 대체 라벨 생성"""
        fallback_label = QLabel("📊 차트 기능을 사용할 수 없습니다")
        fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fallback_label.setFont(QFont("Arial", 12))
        fallback_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 8px;
                color: #6c757d;
                padding: 40px;
                margin: 10px;
            }
        """)
        fallback_label.setMaximumHeight(250)
        return fallback_label
    
    def update_chart_with_sample_data(self):
        """샘플 데이터로 차트 초기화"""
        if not self.chart_available or not hasattr(self, 'chart_figure'):
            return
            
        try:
            self.chart_figure.clear()
            ax = self.chart_figure.add_subplot(111)
            
            # 샘플 데이터 생성
            x = np.arange(30)
            y = 50000 + 5000 * np.sin(x/5) + np.random.normal(0, 1000, 30)
            
            ax.plot(x, y, color='#3498db', linewidth=2, label='샘플 가격')
            ax.axhline(y=50000, color='green', linestyle='--', alpha=0.7, label='목표값')
            
            ax.set_title('📊 차트 준비됨 - 시뮬레이션을 실행하세요', fontsize=10)
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.2)
            ax.set_xticks([])
            ax.set_ylabel('')
            
            # 차트 여백 조정
            self.chart_figure.tight_layout(pad=0.5)
            self.chart_figure.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.1)
            
            if hasattr(self, 'chart_canvas'):
                self.chart_canvas.draw()
            
            print("✅ 차트 초기화 완료")
            
        except Exception as e:
            print(f"❌ 차트 초기화 실패: {e}")
    
    def update_chart_with_simulation_results(self, simulation_data, trigger_results):
        """시뮬레이션 결과로 차트 업데이트 - 데이터 타입별 대응"""
        if not self.chart_available or not hasattr(self, 'chart_figure'):
            return
        
        try:
            # 기존 차트 지우기
            self.chart_figure.clear()
            ax = self.chart_figure.add_subplot(111)
            
            # 시뮬레이션 데이터 시각화
            if 'price_data' in simulation_data:
                data = simulation_data['price_data']
                data_type = simulation_data.get('data_type', 'price')
                x = np.arange(len(data))
                
                # 데이터 타입별 라벨 및 색상 설정
                if data_type == 'rsi':
                    label = 'RSI'
                    color = '#9b59b6'  # 보라색
                    # RSI 기준선 추가
                    ax.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='과매수(70)')
                    ax.axhline(y=30, color='blue', linestyle='--', alpha=0.5, label='과매도(30)')
                elif data_type == 'macd':
                    label = 'MACD'
                    color = '#e67e22'  # 주황색
                    # MACD 기준선 추가
                    ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5, label='기준선(0)')
                else:
                    label = 'Price'
                    color = '#3498db'  # 파란색
                    # 목표값 기준선 추가 (가격인 경우)
                    if 'target_value' in simulation_data:
                        target = simulation_data['target_value']
                        ax.axhline(y=target, color='green', linestyle='--', alpha=0.7, 
                                  label=f'목표값({target:,.0f})')
                
                ax.plot(x, data, color=color, linewidth=2, label=label)
                
                # 트리거 발생 지점 표시
                if trigger_results and 'trigger_points' in trigger_results:
                    trigger_x = trigger_results['trigger_points']
                    if trigger_x:  # 트리거 포인트가 있는 경우에만
                        trigger_y = [data[i] for i in trigger_x if i < len(data)]
                        trigger_x_filtered = [i for i in trigger_x if i < len(data)]
                        
                        if trigger_x_filtered:
                            ax.scatter(trigger_x_filtered, trigger_y, color='#e74c3c', s=60, 
                                      zorder=5, label=f'신호({len(trigger_x_filtered)}개)', marker='o')
                
                # 차트 제목에 신호 개수 포함
                total_signals = len(trigger_results.get('trigger_points', []))
                scenario = simulation_data.get("scenario", "Simulation")
                ax.set_title(f'{scenario} - {total_signals}개 신호', 
                            fontsize=10, fontweight='bold')
                
                ax.legend(fontsize=8, loc='upper left')
                ax.grid(True, alpha=0.2)
                
                # Y축만 표시 (데이터 범위 확인용)
                ax.set_xticks([])
                if data_type == 'rsi':
                    ax.set_ylim(0, 100)
                    ax.set_yticks([0, 30, 50, 70, 100])
                elif data_type == 'macd':
                    ax.set_ylim(-2, 2)
                    ax.set_yticks([-2, -1, 0, 1, 2])
                else:
                    # 가격 데이터는 자동 스케일링
                    pass
                
                ax.set_xlabel('')
                ax.set_ylabel('')
            
            # 차트 여백 조정
            self.chart_figure.tight_layout(pad=0.5)
            self.chart_figure.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.1)
            
            # 차트 업데이트
            if hasattr(self, 'chart_canvas'):
                self.chart_canvas.draw()
            
            print(f"✅ 차트 업데이트 완료 ({data_type} 데이터)")
            
        except Exception as e:
            print(f"❌ 차트 업데이트 실패: {e}")
