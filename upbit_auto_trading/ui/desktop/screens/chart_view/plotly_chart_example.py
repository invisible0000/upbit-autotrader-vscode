"""
Plotly 기반 차트 구현 예시
- 향후 PyQtGraph 대체용 참고 코드
"""

import plotly.graph_objects as go
import plotly.offline as offline
import pandas as pd
import tempfile
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl


class PlotlyChartWidget(QWidget):
    """Plotly 기반 차트 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 웹 엔진 뷰 생성
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        
    def plot_candlestick(self, df):
        """캔들스틱 차트 플롯"""
        try:
            # Plotly 차트 생성
            fig = go.Figure()
            
            # 캔들스틱 추가
            fig.add_trace(go.Candlestick(
                x=df['timestamp'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='가격',
                increasing_line_color='#26A69A',  # 상승 캔들 색상
                decreasing_line_color='#EF5350'   # 하락 캔들 색상
            ))
            
            # 거래량 차트 추가 (서브플롯)
            from plotly.subplots import make_subplots
            fig_with_volume = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
                subplot_titles=('가격', '거래량')
            )
            
            # 가격 차트
            fig_with_volume.add_trace(
                go.Candlestick(
                    x=df['timestamp'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name='가격',
                    increasing_line_color='#26A69A',
                    decreasing_line_color='#EF5350'
                ), 
                row=1, col=1
            )
            
            # 거래량 차트
            if 'volume' in df.columns:
                fig_with_volume.add_trace(
                    go.Bar(
                        x=df['timestamp'],
                        y=df['volume'],
                        name='거래량',
                        marker_color='rgba(158,158,158,0.8)'
                    ),
                    row=2, col=1
                )
            
            # 레이아웃 설정
            fig_with_volume.update_layout(
                title='BTC/KRW 차트',
                xaxis_rangeslider_visible=False,
                template='plotly_dark',  # 다크 테마
                showlegend=False,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            
            # HTML로 저장하고 웹뷰에 로드
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.html', 
                delete=False, 
                mode='w', 
                encoding='utf-8'
            )
            
            fig_with_volume.write_html(
                temp_file.name,
                config={
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['pan2d', 'lasso2d']
                }
            )
            
            # 웹뷰에 로드
            self.web_view.setUrl(QUrl.fromLocalFile(temp_file.name))
            
            # 임시 파일 정리 (나중에)
            self.temp_file = temp_file.name
            
        except Exception as e:
            print(f"Plotly 차트 생성 오류: {e}")
    
    def add_moving_average(self, df, period=20):
        """이동평균선 추가"""
        # 현재 차트에 이동평균선 오버레이 로직
        pass


# 사용 예시
def create_sample_data():
    """샘플 데이터 생성"""
    dates = pd.date_range(start='2025-01-01', periods=100, freq='1H')
    np.random.seed(42)
    
    # 가격 데이터 생성
    price = 50000
    data = []
    
    for date in dates:
        change = np.random.randn() * 1000
        price += change
        
        high = price + abs(np.random.randn() * 500)
        low = price - abs(np.random.randn() * 500)
        close = price + np.random.randn() * 200
        volume = abs(np.random.randn() * 1000000)
        
        data.append({
            'timestamp': date,
            'open': price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
        
        price = close
    
    return pd.DataFrame(data)


# 테스트용 함수
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 샘플 데이터 생성
    sample_df = create_sample_data()
    
    # Plotly 차트 위젯 생성
    chart_widget = PlotlyChartWidget()
    chart_widget.plot_candlestick(sample_df)
    chart_widget.show()
    
    sys.exit(app.exec())
