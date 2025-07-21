"""
백테스트 결과 표시 위젯
- 핵심 성과 지표 표시
- 자산 변화 차트
- 상세 거래 내역
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QFrame,
    QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.font_manager as fm
    
    # 한글 폰트 설정 (여러 옵션 시도)
    try:
        # Windows에서 사용 가능한 한글 폰트들
        korean_fonts = ['Malgun Gothic', 'Arial Unicode MS', 'Gulim', 'Dotum', 'Batang']
        available_fonts = [f.name for f in fm.fontManager.ttflist]
        
        for font in korean_fonts:
            if font in available_fonts:
                plt.rcParams['font.family'] = [font, 'DejaVu Sans']
                break
        else:
            # 한글 폰트가 없으면 기본 설정
            plt.rcParams['font.family'] = ['DejaVu Sans']
        
        plt.rcParams['axes.unicode_minus'] = False
    except Exception:
        # 폰트 설정 실패 시 기본값 사용
        pass
    
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    # 폴백을 위한 더미 클래스
    class FigureCanvas(QWidget):
        def __init__(self, *args, **kwargs):
            super().__init__()
            self.setMinimumHeight(200)
        
        def draw(self):
            pass  # 더미 메서드

class BacktestResultsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_results = None  # 현재 백테스트 결과 저장
        self.highlight_line = None   # 차트의 하이라이트 선 객체
        self.init_ui()
    
    def resizeEvent(self, a0):
        """윈도우 크기 변경 시 차트를 자동으로 조정"""
        super().resizeEvent(a0)
        
        # 차트가 있고 matplotlib이 사용 가능한 경우에만 실행
        if MATPLOTLIB_AVAILABLE and hasattr(self, 'figure') and hasattr(self, 'canvas'):
            # 약간의 지연을 두고 tight_layout 적용 (리사이즈 이벤트가 여러 번 발생할 수 있으므로)
            if hasattr(self, '_resize_timer'):
                self._resize_timer.stop()
            
            from PyQt6.QtCore import QTimer
            self._resize_timer = QTimer()
            self._resize_timer.timeout.connect(self._apply_tight_layout)
            self._resize_timer.setSingleShot(True)
            self._resize_timer.start(100)  # 100ms 후에 적용
    
    def _apply_tight_layout(self):
        """차트에 tight_layout 적용"""
        try:
            if MATPLOTLIB_AVAILABLE and hasattr(self, 'figure') and self.figure:
                # 차트에 데이터가 있는 경우에만 적용
                if self.figure.get_axes():
                    self.figure.tight_layout(pad=1.5)  # 약간의 여백 추가
                    if hasattr(self.canvas, 'draw'):
                        self.canvas.draw()
        except Exception as e:
            # tight_layout 적용 실패는 로그만 남기고 무시
            print(f"🔧 차트 레이아웃 자동 조정 실패: {e}")
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 1. 핵심 성과 지표 (5개로 확장)
        metrics_frame = QFrame()
        metrics_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        metrics_layout = QHBoxLayout(metrics_frame)
        
        # 총수익률
        profit_layout = QVBoxLayout()
        profit_layout.addWidget(QLabel("총수익률"))
        self.profit_label = QLabel("0.0%")
        self.profit_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        profit_layout.addWidget(self.profit_label)
        metrics_layout.addLayout(profit_layout)
        
        # 승률
        winrate_layout = QVBoxLayout()
        winrate_layout.addWidget(QLabel("승률"))
        self.winrate_label = QLabel("0.0%")
        self.winrate_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        winrate_layout.addWidget(self.winrate_label)
        metrics_layout.addLayout(winrate_layout)
        
        # 최대 손실폭 (MDD - Maximum Drawdown)
        drawdown_layout = QVBoxLayout()
        drawdown_layout.addWidget(QLabel("최대 손실폭(MDD)"))
        self.drawdown_label = QLabel("0.0%")
        self.drawdown_label.setStyleSheet("font-size: 20px; font-weight: bold; color: red;")
        drawdown_layout.addWidget(self.drawdown_label)
        metrics_layout.addLayout(drawdown_layout)
        
        # 샤프 비율 (Sharp Ratio) - 위험 대비 수익률
        sharpe_layout = QVBoxLayout()
        sharpe_layout.addWidget(QLabel("샤프 비율"))
        self.sharpe_label = QLabel("0.00")
        self.sharpe_label.setStyleSheet("font-size: 20px; font-weight: bold; color: blue;")
        sharpe_layout.addWidget(self.sharpe_label)
        metrics_layout.addLayout(sharpe_layout)
        
        # 총 거래 수
        trades_layout = QVBoxLayout()
        trades_layout.addWidget(QLabel("총 거래"))
        self.trades_label = QLabel("0회")
        self.trades_label.setStyleSheet("font-size: 20px; font-weight: bold; color: purple;")
        trades_layout.addWidget(self.trades_label)
        metrics_layout.addLayout(trades_layout)
        
        layout.addWidget(metrics_frame)
        
        # 2. 차트 영역 (크기 조정 가능하도록 개선)
        chart_frame = QFrame()
        chart_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        chart_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(5, 5, 5, 5)
        
        if MATPLOTLIB_AVAILABLE:
            from matplotlib.figure import Figure  # 조건부 임포트
            try:
                from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
            except ImportError:
                try:
                    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
                except ImportError:
                    NavigationToolbar = None  # 도구바 없이 진행
            
            # Figure 크기를 동적으로 설정하고 DPI 조정
            self.figure = Figure(figsize=(10, 6), dpi=80)
            self.canvas = FigureCanvas(self.figure)
            
            # 차트 크기 정책 설정 (윈도우 크기에 따라 확장)
            self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            # 초기 레이아웃 설정
            try:
                # 서브플롯 간격 조정으로 더 나은 초기 레이아웃 제공
                self.figure.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9, wspace=0.2, hspace=0.2)
            except Exception as e:
                print(f"🔧 초기 차트 레이아웃 설정 실패: {e}")
            
            # matplotlib 내장 탐색 도구바 추가 (확대/축소, 팬, 홈 등)
            if NavigationToolbar:
                self.toolbar = NavigationToolbar(self.canvas, self)
                self.toolbar.setStyleSheet("""
                    QToolBar {
                        background-color: #f0f0f0;
                        border: 1px solid #cccccc;
                        spacing: 2px;
                        padding: 2px;
                    }
                    QToolBar::separator {
                        width: 1px;
                        background-color: #cccccc;
                    }
                """)
                chart_layout.addWidget(self.toolbar)  # 도구바 먼저 추가
            
            chart_layout.addWidget(self.canvas)   # 캔버스 추가
            
        else:
            self.chart_label = QLabel("자산 변화 차트 (matplotlib 설치 필요)")
            self.chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chart_layout.addWidget(self.chart_label)
        
        # 차트 프레임에 더 큰 비중 할당 (stretch=3)
        layout.addWidget(chart_frame, stretch=3)
        
        # 3. 거래 내역 테이블 (비중 조정)
        self.trade_table = QTableWidget(0, 8)  # 컬럼 수 증가 (8개)
        self.trade_table.setHorizontalHeaderLabels([
            "거래 시각", "종류", "코인", "가격", "수량", "거래금액", "잔고", "수익률"
        ])
        # 테이블도 크기에 맞춰 확장되도록 설정
        self.trade_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.trade_table.setMinimumHeight(200)
        
        # 거래 테이블 클릭 이벤트 연결
        self.trade_table.itemClicked.connect(self.on_trade_selected)
        
        # 테이블 스타일 설정 (선택 효과 강화)
        self.trade_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
            }
            QTableWidget::item:selected {
                background-color: #3daee9;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #e6f3ff;
            }
        """)
        
        layout.addWidget(self.trade_table, stretch=2)  # 비중 할당
        
        # 4. 로딩 바
        self.loading_bar = QProgressBar()
        self.loading_bar.setVisible(False)
        layout.addWidget(self.loading_bar)
    
    def clear_results(self):
        """결과 초기화"""
        self.profit_label.setText("0.0%")
        self.winrate_label.setText("0.0%")
        self.drawdown_label.setText("0.0%")
        self.sharpe_label.setText("0.00")
        self.trades_label.setText("0회")
        self.trade_table.setRowCount(0)
        
        # 하이라이트 선과 결과 데이터 초기화
        self.current_results = None
        if self.highlight_line:
            try:
                self.highlight_line.remove()
            except:
                pass
            self.highlight_line = None
            
        # 차트 초기화
        if MATPLOTLIB_AVAILABLE and hasattr(self, 'figure'):
            self.figure.clear()
            if hasattr(self.canvas, 'draw'):
                self.canvas.draw()
    
    def show_loading(self, show: bool):
        """로딩 표시/숨김"""
        self.loading_bar.setVisible(show)
        if show:
            self.loading_bar.setRange(0, 0)  # 불확정 진행바
        else:
            self.loading_bar.setRange(0, 100)
    
    def update_results(self, results: dict):
        """백테스트 결과 업데이트
        
        Args:
            results (dict): 백테스트 엔진에서 반환하는 결과 딕셔너리
        """
        try:
            # 결과 저장 (차트 하이라이트용)
            self.current_results = results
            
            print(f"📊 백테스트 결과 데이터 구조: {list(results.keys())}")
            
            # 두 가지 결과 구조 모두 지원
            # 1) summary 키가 있는 경우 (기존 구조)
            # 2) performance_metrics 키가 있는 경우 (새 구조)
            
            summary = results.get('summary', {})
            metrics = results.get('performance_metrics', {})
            
            # 1. 성과 지표 업데이트 - 수정된 계산 로직
            total_return = 0.0
            win_rate = 0.0
            max_drawdown = 0.0
            sharpe_ratio = 0.0
            total_trades = 0
            
            # 초기 자본과 최종 자산 값 가져오기
            initial_capital = results.get('initial_capital', 1000000)
            final_portfolio_value = results.get('final_portfolio_value', initial_capital)
            trades = results.get('trades', [])
            total_trades = len(trades)
            
            print(f"💰 자본 정보: 초기={initial_capital:,.0f}, 최종={final_portfolio_value:,.0f}")
            print(f"🔍 전체 결과 키들: {list(results.keys())}")
            
            # 수익률 계산 - 단순하고 정확한 방법
            total_return = 0.0
            
            # 마지막 거래의 잔고를 확인 (거래 테이블의 마지막 잔고)
            last_balance = final_portfolio_value
            if trades:
                # 거래 기록에서 마지막 잔고 찾기
                last_trade = trades[-1]  # 마지막 거래
                # 매도가 완료된 경우 잔고 계산
                if last_trade.get('exit_time'):  # 매도 완료
                    exit_amount = last_trade.get('net_exit_amount', 0)
                    # 현재까지의 모든 거래 손익 합산
                    total_profit_loss = sum(trade.get('profit_loss', 0) for trade in trades)
                    last_balance = initial_capital + total_profit_loss
                    print(f"📊 거래 기록 기준 최종 잔고: {last_balance:,.0f}")
            
            # 0으로 나누기 방지 및 수익률 계산
            if initial_capital > 0:
                if abs(last_balance - initial_capital) < 0.01:  # 거의 같은 경우 (소수점 오차 고려)
                    total_return = 0.0
                    print(f"📈 초기자본과 최종잔고가 거의 같음: 0.00%")
                else:
                    total_return = ((last_balance - initial_capital) / initial_capital) * 100
                    print(f"📈 수익률 계산: ({last_balance:,.0f} - {initial_capital:,.0f}) / {initial_capital:,.0f} * 100 = {total_return:.2f}%")
            else:
                print(f"❌ 초기 자본이 0 또는 음수: {initial_capital}")
                total_return = 0.0
            
            print(f"🎯 최종 수익률: {total_return:.2f}%")
            
            # 기존 결과에서 다른 지표들 가져오기
            if summary:
                win_rate = summary.get('win_rate', 0.0)
                max_drawdown = summary.get('max_drawdown', 0.0)
                sharpe_ratio = summary.get('sharpe_ratio', 0.0)
            elif metrics:
                win_rate = metrics.get('win_rate', 0.0)
                max_drawdown = metrics.get('max_drawdown', 0.0)
                sharpe_ratio = metrics.get('sharpe_ratio', 0.0)
            
            # 승률과 MDD는 비율인 경우 퍼센트로 변환
            if abs(win_rate) <= 1.0:
                win_rate = win_rate * 100
            if abs(max_drawdown) <= 1.0:
                max_drawdown = max_drawdown * 100
            
            # 샤프 비율이 없으면 간단히 계산 (수익률 / 변동성 근사치)
            if sharpe_ratio == 0.0 and total_trades > 1:
                # 거래별 수익률의 변동성을 이용한 근사 계산
                trade_returns = []
                for trade in trades:
                    profit_pct = trade.get('profit_loss_percent', 0)
                    if profit_pct != 0:
                        trade_returns.append(profit_pct)
                
                if len(trade_returns) > 1:
                    import numpy as np
                    try:
                        returns_std = np.std(trade_returns)
                        if returns_std > 0:
                            sharpe_ratio = (total_return / 100) / (returns_std / 100)
                    except:
                        sharpe_ratio = 0.0
            
            # UI 업데이트
            print(f"🔄 UI 업데이트 시작 - 수익률: {total_return:.2f}%")
            self.profit_label.setText(f"{total_return:.2f}%")
            print(f"✅ profit_label 텍스트 설정 완료: {self.profit_label.text()}")
            
            self.winrate_label.setText(f"{win_rate:.1f}%")
            self.drawdown_label.setText(f"{max_drawdown:.2f}%")
            self.sharpe_label.setText(f"{sharpe_ratio:.2f}")
            self.trades_label.setText(f"{total_trades}회")
            
            # 성과에 따른 색상 설정
            profit_color = "green" if total_return > 0 else "red" if total_return < 0 else "gray"
            self.profit_label.setStyleSheet(
                f"font-size: 20px; font-weight: bold; color: {profit_color};"
            )
            print(f"🎨 profit_label 스타일 설정 완료: {profit_color}")
            
            # 샤프 비율 색상 (1.0 이상이면 우수)
            sharpe_color = "green" if sharpe_ratio >= 1.0 else "blue" if sharpe_ratio >= 0.5 else "orange"
            self.sharpe_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {sharpe_color};")
            
            print(f"✅ 지표 업데이트 완료: 수익률={total_return:.2f}%, 승률={win_rate:.1f}%, MDD={max_drawdown:.2f}%, 샤프={sharpe_ratio:.2f}, 거래={total_trades}회")
            
            # 2. 거래 내역 테이블 업데이트
            self.trade_table.setRowCount(0)
            current_balance = initial_capital  # 현재 잔고 추적
            
            if trades:
                print(f"🔍 거래 데이터 샘플: {trades[0] if trades else 'None'}")
            
            # 매수/매도 거래를 분리해서 표시
            for i, trade in enumerate(trades):
                # 매수 거래 행 추가
                buy_row = self.trade_table.rowCount()
                self.trade_table.insertRow(buy_row)
                
                # 매수 시간
                entry_time = trade.get('entry_time', '')
                if hasattr(entry_time, 'strftime'):
                    entry_time_str = entry_time.strftime('%Y-%m-%d %H:%M')
                else:
                    entry_time_str = str(entry_time)[:16]
                self.trade_table.setItem(buy_row, 0, QTableWidgetItem(entry_time_str))
                
                # 매수 표시
                self.trade_table.setItem(buy_row, 1, QTableWidgetItem('매수'))
                
                # 코인
                symbol = trade.get('symbol', results.get('symbol', 'Unknown'))
                self.trade_table.setItem(buy_row, 2, QTableWidgetItem(symbol))
                
                # 매수가
                entry_price = trade.get('entry_price', 0)
                self.trade_table.setItem(buy_row, 3, QTableWidgetItem(f"{entry_price:,.0f}"))
                
                # 수량
                quantity = trade.get('quantity', 0)
                self.trade_table.setItem(buy_row, 4, QTableWidgetItem(f"{quantity:.6f}"))
                
                # 매수 금액
                entry_amount = trade.get('entry_amount', entry_price * quantity)
                self.trade_table.setItem(buy_row, 5, QTableWidgetItem(f"{entry_amount:,.0f}"))
                
                # 매수 후 잔고 (현금이 줄어듦)
                current_balance = current_balance - entry_amount
                self.trade_table.setItem(buy_row, 6, QTableWidgetItem(f"{current_balance:,.0f}"))
                
                # 매수는 수익률 없음
                self.trade_table.setItem(buy_row, 7, QTableWidgetItem("-"))
                
                # 매도 거래 행 추가 (완료된 거래만)
                if trade.get('exit_time'):
                    sell_row = self.trade_table.rowCount()
                    self.trade_table.insertRow(sell_row)
                    
                    # 매도 시간
                    exit_time = trade.get('exit_time', '')
                    if hasattr(exit_time, 'strftime'):
                        exit_time_str = exit_time.strftime('%Y-%m-%d %H:%M')
                    else:
                        exit_time_str = str(exit_time)[:16]
                    self.trade_table.setItem(sell_row, 0, QTableWidgetItem(exit_time_str))
                    
                    # 매도 표시
                    self.trade_table.setItem(sell_row, 1, QTableWidgetItem('매도'))
                    
                    # 코인
                    self.trade_table.setItem(sell_row, 2, QTableWidgetItem(symbol))
                    
                    # 매도가
                    exit_price = trade.get('exit_price', 0)
                    self.trade_table.setItem(sell_row, 3, QTableWidgetItem(f"{exit_price:,.0f}"))
                    
                    # 수량
                    self.trade_table.setItem(sell_row, 4, QTableWidgetItem(f"{quantity:.6f}"))
                    
                    # 매도 금액
                    net_exit_amount = trade.get('net_exit_amount', exit_price * quantity)
                    self.trade_table.setItem(sell_row, 5, QTableWidgetItem(f"{net_exit_amount:,.0f}"))
                    
                    # 매도 후 잔고 (현금이 늘어남)
                    current_balance = current_balance + net_exit_amount
                    self.trade_table.setItem(sell_row, 6, QTableWidgetItem(f"{current_balance:,.0f}"))
                    
                    # 손익률
                    profit_pct = trade.get('profit_loss_percent', 0)
                    profit_item = QTableWidgetItem(f"{profit_pct:.2f}%")
                    if profit_pct > 0:
                        profit_item.setForeground(Qt.GlobalColor.green)
                    elif profit_pct < 0:
                        profit_item.setForeground(Qt.GlobalColor.red)
                    self.trade_table.setItem(sell_row, 7, profit_item)
            
            # 3. 자산 변화 차트 업데이트
            if MATPLOTLIB_AVAILABLE and hasattr(self, 'canvas'):
                self.update_chart(results)
            
            print(f"✅ 백테스트 결과 업데이트 완료:")
            print(f"   - 총 수익률: {total_return:.2f}%")
            print(f"   - 승률: {win_rate:.1f}%") 
            print(f"   - 최대 손실폭: {max_drawdown:.2f}%")
            print(f"   - 샤프 비율: {sharpe_ratio:.2f}")
            print(f"   - 총 거래: {total_trades}회")
            
        except Exception as e:
            print(f"❌ 백테스트 결과 업데이트 실패: {e}")
            import traceback
            traceback.print_exc()
    
    def update_chart(self, results: dict):
        """백테스트 차트 업데이트 (단일 차트: 가격 + 신호 + 자산변화)"""
        try:
            if not MATPLOTLIB_AVAILABLE or not hasattr(self, 'figure'):
                return
            
            # 차트 초기화
            self.figure.clear()
            
            # 단일 차트 생성 (가시성 개선을 위해)
            ax = self.figure.add_subplot(1, 1, 1)
            
            # 백테스트 데이터 가져오기
            equity_curve = results.get('equity_curve', None)
            
            if equity_curve is not None and hasattr(equity_curve, 'index'):
                # 자산 가치를 메인으로 표시 (파란색 실선)
                ax.plot(equity_curve.index, equity_curve['equity'], 
                       label='포트폴리오 자산 가치', color='blue', linewidth=2.5)
                
                # 코인 가격을 두 번째 y축에 표시
                ax2 = ax.twinx()
                if 'close' in equity_curve.columns:
                    ax2.plot(equity_curve.index, equity_curve['close'], 
                           label='코인 가격', color='gray', linewidth=1, alpha=0.7)
                    ax2.set_ylabel('코인 가격 (KRW)', color='gray')
                    ax2.tick_params(axis='y', labelcolor='gray')
                
                # 거래 신호 마킹
                trades = results.get('trades', [])
                buy_times = []
                buy_values = []  # 해당 시점의 자산 가치
                sell_times = []
                sell_values = []
                
                for trade in trades:
                    entry_time = trade.get('entry_time')
                    exit_time = trade.get('exit_time')
                    
                    if entry_time and entry_time in equity_curve.index:
                        buy_times.append(entry_time)
                        buy_values.append(equity_curve.loc[entry_time, 'equity'])
                    
                    if exit_time and exit_time in equity_curve.index:
                        sell_times.append(exit_time)
                        sell_values.append(equity_curve.loc[exit_time, 'equity'])
                
                # 매수/매도 신호 표시 (자산 가치 차트 위에)
                if buy_times and buy_values:
                    ax.scatter(buy_times, buy_values, color='green', marker='^', 
                              s=120, label='매수 신호', zorder=10, edgecolors='white')
                
                if sell_times and sell_values:
                    ax.scatter(sell_times, sell_values, color='red', marker='v', 
                              s=120, label='매도 신호', zorder=10, edgecolors='white')
                
                # 초기 자산 기준선 표시
                initial_capital = results.get('initial_capital', equity_curve['equity'].iloc[0])
                ax.axhline(y=initial_capital, color='orange', linestyle='--', alpha=0.7, 
                          label=f'초기 자산 ({initial_capital:,.0f}원)')
                
                # 수익 구간 색칠
                ax.fill_between(equity_curve.index, initial_capital, equity_curve['equity'], 
                              where=(equity_curve['equity'] >= initial_capital),
                              color='green', alpha=0.2, interpolate=True, label='수익 구간')
                ax.fill_between(equity_curve.index, initial_capital, equity_curve['equity'], 
                              where=(equity_curve['equity'] < initial_capital),
                              color='red', alpha=0.2, interpolate=True, label='손실 구간')
                
                # 차트 설정
                ax.set_title('백테스트 결과: 포트폴리오 자산 변화 및 매매 신호', fontsize=14, fontweight='bold')
                ax.set_xlabel('시간')
                ax.set_ylabel('자산 가치 (KRW)', color='blue')
                ax.tick_params(axis='y', labelcolor='blue')
                ax.legend(loc='upper left')
                ax.grid(True, alpha=0.3)
                
                # 천 단위 콤마 포맷
                try:
                    from matplotlib.ticker import FuncFormatter
                    formatter = FuncFormatter(lambda x, p: format(int(x), ','))
                    ax.yaxis.set_major_formatter(formatter)
                    ax2.yaxis.set_major_formatter(formatter)
                except ImportError:
                    pass
                
            else:
                # 데이터가 없는 경우
                ax.text(0.5, 0.5, '차트 데이터가 없습니다\n백테스트를 먼저 실행해주세요', 
                       transform=ax.transAxes, ha='center', va='center', 
                       fontsize=12, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
            
            # 레이아웃 조정 (윈도우 크기에 맞게 자동 조정)
            try:
                self.figure.tight_layout(pad=1.5)  # 여백을 조금 더 여유롭게
            except Exception as e:
                print(f"🔧 차트 레이아웃 조정 실패: {e}")
                # 실패해도 계속 진행
            
            # 차트 새로고침
            if hasattr(self.canvas, 'draw'):
                self.canvas.draw()
            
        except Exception as e:
            print(f"❌ 차트 업데이트 실패: {e}")
            import traceback
            traceback.print_exc()
    
    def on_trade_selected(self, item):
        """거래 테이블에서 행이 선택되었을 때 차트에 하이라이트 표시"""
        try:
            if not self.current_results or not MATPLOTLIB_AVAILABLE:
                return
                
            # 선택된 행 번호
            row = item.row()
            
            # 거래 시각 가져오기 (첫 번째 컬럼)
            time_item = self.trade_table.item(row, 0)
            if not time_item:
                return
                
            trade_time_str = time_item.text()
            print(f"🎯 선택된 거래 시각: {trade_time_str}")
            
            # 거래 시각을 datetime으로 변환
            try:
                from datetime import datetime
                # 여러 날짜 형식 시도
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M',
                    '%Y-%m-%d',
                    '%m/%d %H:%M',
                    '%m-%d %H:%M'
                ]
                
                trade_time = None
                for fmt in formats:
                    try:
                        trade_time = datetime.strptime(trade_time_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if not trade_time:
                    print(f"❌ 날짜 형식을 파싱할 수 없습니다: {trade_time_str}")
                    return
                    
            except Exception as e:
                print(f"❌ 날짜 파싱 오류: {e}")
                return
            
            # 차트에 수직선 표시
            self.highlight_trade_on_chart(trade_time)
            
        except Exception as e:
            print(f"❌ 거래 선택 처리 실패: {e}")
            import traceback
            traceback.print_exc()
    
    def highlight_trade_on_chart(self, trade_time):
        """차트에 거래 시점을 수직선으로 하이라이트"""
        try:
            if not hasattr(self, 'figure') or not self.figure:
                return
                
            # 기존 하이라이트 선 제거
            if self.highlight_line:
                try:
                    self.highlight_line.remove()
                except:
                    pass
                self.highlight_line = None
            
            # 차트에서 축 찾기
            axes = self.figure.get_axes()
            if not axes:
                return
                
            ax = axes[0]  # 첫 번째 축 사용
            
            # 수직 하이라이트 선 추가
            self.highlight_line = ax.axvline(
                x=trade_time, 
                color='red', 
                linestyle='--', 
                linewidth=2, 
                alpha=0.8,
                label='선택된 거래',
                zorder=15  # 다른 요소들보다 위에 표시
            )
            
            # 범례 업데이트 (하이라이트 선 포함)
            handles, labels = ax.get_legend_handles_labels()
            # 중복된 라벨 제거
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys(), loc='upper left')
            
            # 차트 새로고침
            if hasattr(self.canvas, 'draw'):
                self.canvas.draw()
                
            print(f"✅ 차트에 거래 시점 하이라이트 완료: {trade_time}")
            
        except Exception as e:
            print(f"❌ 차트 하이라이트 실패: {e}")
            import traceback
            traceback.print_exc()
