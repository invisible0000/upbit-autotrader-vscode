"""
시뮬레이션 결과 위젯
원본: integrated_condition_manager.py의 create_test_result_area() 완전 복제
미니차트 변수 서비스 통합 버전
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime
import traceback

# 차트 라이브러리 import
try:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    CHART_AVAILABLE = True
except ImportError:
    CHART_AVAILABLE = False
    print("⚠️ matplotlib를 찾을 수 없습니다.")

# 미니차트 변수 서비스 import
try:
    from ..data_sources.minichart_variable_service import get_minichart_variable_service
    MINICHART_SERVICE_AVAILABLE = True
    print("✅ 미니차트 변수 서비스 로드 성공")
except ImportError as e:
    MINICHART_SERVICE_AVAILABLE = False
    print(f"⚠️ 미니차트 변수 서비스 로드 실패: {e}")


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
        layout.setContentsMargins(6, 6, 6, 6)  # 표준 마진
        layout.setSpacing(4)  # 표준 간격 추가

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

    def _setup_common_chart_style(self, ax, bg_color):
        """공통 차트 스타일 설정 - 두 플롯 함수에서 공유"""
        # Y축 라벨 설정
        ax.set_ylabel('Price', fontsize=10)

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

        # 틱 라벨 크기 설정 (일관성 유지)
        ax.tick_params(axis='both', which='major', labelsize=12)

        # 그리드 및 배경색 설정
        ax.grid(True, alpha=0.3)
        ax.set_facecolor(bg_color)

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

            # 공통 차트 스타일 적용
            self._setup_common_chart_style(ax, bg_color)

            # X축 틱 라벨 포맷팅 (데이터 인덱스 표시) - 플레이스홀더용
            ax.set_xticks(range(0, 10, 2))
            ax.set_xticklabels([str(i) for i in range(0, 10, 2)])

            # tight_layout 제거 - 틱 라벨 크기에 영향을 줄 수 있음 (플레이스홀더)
            # self.figure.tight_layout(pad=0.5)
            self.canvas.draw()

        except Exception as e:
            print(f"⚠️ 플레이스홀더 차트 표시 실패: {e}")

    def update_simulation_chart(self, scenario, price_data, trigger_results, base_variable_data=None, external_variable_data=None, variable_info=None, comparison_value=None):
        """시뮬레이션 결과로 차트 업데이트 - 차트 카테고리 시스템 기반 플롯팅"""
        if not CHART_AVAILABLE or not hasattr(self, 'figure'):
            return

        # 마지막 결과 저장 (테마 변경 시 재사용)
        self._last_scenario = scenario
        self._last_price_data = price_data
        self._last_trigger_results = trigger_results

        # 고정값 비교 정보 저장 (RSI > 70 등)
        self._comparison_value = comparison_value

        try:
            # 전역 테마 매니저 사용
            from upbit_auto_trading.ui.desktop.common.theme_notifier import apply_matplotlib_theme_simple, get_theme_notifier
            apply_matplotlib_theme_simple()

            # 테마에 따른 색상 설정
            theme_notifier = get_theme_notifier()
            is_dark = theme_notifier.is_dark_theme()

            # 색상 팔레트 (더 다양하게)
            colors = {
                'primary': '#60a5fa' if is_dark else '#3498db',      # 기본 데이터 (파랑)
                'base_var': '#10b981' if is_dark else '#059669',     # 기본 변수 (녹색)
                'external_var': '#f59e0b' if is_dark else '#d97706', # 외부 변수 (주황)
                'trigger': '#f87171' if is_dark else '#ef4444',      # 트리거 (빨강)
                'reference': '#8b5cf6' if is_dark else '#7c3aed',    # 기준선 (보라)
                'background': '#2c2c2c' if is_dark else 'white'
            }

            # Figure와 Canvas 배경색 설정
            self.figure.patch.set_facecolor(colors['background'])
            if hasattr(self, 'canvas'):
                self.canvas.setStyleSheet(f"background-color: {colors['background']};")

            self.figure.clear()
            ax = self.figure.add_subplot(111)

            if price_data:
                x = range(len(price_data))

                # 📊 단순화된 차트 분류: price_overlay 또는 volume만 사용
                chart_category = self._get_chart_category(variable_info)

                print(f"📊 단순화된 차트 플롯팅: 카테고리={chart_category}")

                if chart_category in ['volume', 'volume_category']:
                    # 볼륨 차트는 히스토그램으로 표시 (subplot)
                    self._plot_volume_chart(ax, x, price_data, base_variable_data,
                                           external_variable_data, variable_info, colors)
                else:
                    # 나머지는 모두 price_overlay로 통일 (price, oscillator, momentum 등)
                    self._plot_price_overlay_chart(ax, x, price_data, base_variable_data,
                                                  external_variable_data, variable_info, colors)

                # 트리거 신호 표시
                if trigger_results:
                    self._plot_trigger_signals_enhanced(ax, trigger_results, price_data,
                                                      base_variable_data, external_variable_data,
                                                      chart_category, colors['trigger'])

            # 공통 차트 스타일 적용
            self._setup_enhanced_chart_style(ax, colors['background'], variable_info)

            # X축 틱 라벨 포맷팅
            if price_data and len(price_data) > 5:
                x_tick_positions = range(0, len(price_data), max(1, len(price_data) // 5))
                ax.set_xticks(x_tick_positions)
                ax.set_xticklabels([str(i) for i in x_tick_positions])

            # 범례가 잘리지 않도록 레이아웃 조정
            try:
                self.figure.tight_layout(pad=2.0)  # 여백 증가
            except Exception as e:
                print(f"⚠️ tight_layout 실패: {e}")

            self.canvas.draw()

        except Exception as e:
            print(f"⚠️ 시뮬레이션 차트 업데이트 실패: {e}")
            import traceback
            traceback.print_exc()

    def _get_chart_category(self, variable_info):
        """변수 정보에서 차트 카테고리 추출"""
        if not variable_info:
            return 'price_overlay'
        return variable_info.get('category', 'price_overlay')

    def _get_display_type(self, variable_info):
        """변수 정보에서 표시 타입 추출"""
        if not variable_info:
            return 'line'
        return variable_info.get('display_type', 'line')

    def _get_english_label(self, variable_name):
        """한글 변수명을 영문 약어로 변환 - 단순화된 4요소 버전"""
        if not variable_name:
            return 'iVal'

        # 이모지 제거
        clean_name = variable_name.replace('🔹 ', '').replace('🔸 ', '').replace('🔺 ', '').strip()

        # 단순화된 4가지 요소만 사용
        if '기본변수' in clean_name or 'SMA' in clean_name.upper() or 'RSI' in clean_name.upper() or 'MACD' in clean_name.upper():
            return 'iVal'
        elif '외부변수' in clean_name or 'EMA' in clean_name.upper():
            return 'eVal'
        elif '고정값' in clean_name:
            return 'fVal'
        elif 'Volume' in clean_name or '거래량' in clean_name:
            return 'Volume'
        else:
            return 'iVal'  # 기본값

    def _plot_price_overlay_chart(self, ax, x, price_data, base_data, external_data, variable_info, colors):
        """단순화된 가격 오버레이 차트 - 4가지 요소 통일 (Price/iVal + fVal/eVal + Trg)"""
        print("🎨 단순화된 price_overlay 차트 플롯 시작")

        # 차트 카테고리 확인 (oscillator인지 price_overlay인지)
        chart_category = variable_info.get('category', 'price_overlay') if variable_info else 'price_overlay'

        if chart_category == 'oscillator':
            # 1. oscillator 데이터 (RSI 등) - base_data 사용 (계산된 RSI 값)
            if base_data and len(base_data) > 0:
                ax.plot(x, base_data, colors['base_var'], linewidth=1.8, label='iVal', alpha=0.9)
                print(f"   🟢 iVal(오실레이터) 데이터: {len(base_data)}개 포인트")

            # 2. 고정값 비교를 위한 fVal 라인 추가 (외부 데이터가 없을 때)
            if not external_data and hasattr(self, '_comparison_value'):
                fixed_value = self._comparison_value
                ax.axhline(y=fixed_value, color=colors['external_var'], linewidth=1.5,
                           linestyle='--', label='fVal', alpha=0.8)
                print(f"   🟡 fVal(고정값): {fixed_value}")

        else:
            # 1. Price 데이터 (파란색) - 일반적인 price_overlay
            ax.plot(x, price_data, colors['primary'], linewidth=1.5, label='Price', alpha=0.8)
            print(f"   📈 Price 데이터: {len(price_data)}개 포인트")

            # 2. iVal - 기본변수 (녹색 라인)
            if base_data and len(base_data) > 0:
                ax.plot(x, base_data, colors['base_var'], linewidth=1.8,
                       label='iVal', alpha=0.9)
                print(f"   🟢 iVal 데이터: {len(base_data)}개 포인트")

        # 3. fVal/eVal - 비교값/외부변수 (주황색)
        if external_data and len(external_data) > 0:
            # 고정값인지 확인
            is_fixed = len(set(external_data)) == 1

            if is_fixed:
                fixed_value = external_data[0]
                ax.axhline(y=fixed_value, color=colors['external_var'], linewidth=1.5,
                           linestyle='--', label='fVal', alpha=0.8)
                print(f"   🟡 fVal(고정값): {fixed_value}")
            else:
                ax.plot(x, external_data, colors['external_var'], linewidth=1.8,
                        label='eVal', alpha=0.9)
                print(f"   🟡 eVal 데이터: {len(external_data)}개 포인트")

        # 4. Trg - 트리거 마커는 _plot_trigger_signals_enhanced()에서 처리

        # 5. 범례 추가
        legend_handles, legend_labels = ax.get_legend_handles_labels()
        print(f"   📋 범례 요소: {len(legend_handles)}개, 라벨: {legend_labels}")

        if legend_handles:
            ax.legend(loc='upper right', fontsize=8, framealpha=0.9,
                     bbox_to_anchor=(1.0, 1.0), ncol=1)
            print("   ✅ 범례 표시 완료")
        else:
            print("   ⚠️ 표시할 범례 요소가 없음")

        print("✅ price_overlay 차트 플롯 완료")

    def _plot_oscillator_chart(self, ax, x, price_data, base_data, external_data, variable_info, colors):
        """오실레이터 차트 플롯 (RSI, 스토캐스틱 등)"""
        # 오실레이터 데이터 (price_data가 실제로는 오실레이터 값)
        variable_name = variable_info.get('variable_name', '오실레이터') if variable_info else '오실레이터'
        ax.plot(x, price_data, colors['primary'], linewidth=1.5, label=variable_name, alpha=0.8)

        # 기준선 추가 (RSI의 경우 30, 70)
        scale_min = variable_info.get('scale_min', 0) if variable_info else 0
        scale_max = variable_info.get('scale_max', 100) if variable_info else 100

        # 오버바이/오버셀 라인
        if scale_min == 0 and scale_max == 100:
            ax.axhline(y=70, color=colors['reference'], linewidth=1, linestyle='--',
                      label='OB(70)', alpha=0.6)
            ax.axhline(y=30, color=colors['reference'], linewidth=1, linestyle='--',
                      label='OS(30)', alpha=0.6)

        # 중앙선
        mid_value = (scale_min + scale_max) / 2
        ax.axhline(y=mid_value, color=colors['reference'], linewidth=0.8, linestyle='-',
                  alpha=0.4)

        # 기본/외부 변수 처리
        self._plot_variable_data(ax, x, base_data, external_data, colors)

        # Y축 범위 설정
        ax.set_ylim(scale_min - 5, scale_max + 5)

        # 범례 추가
        ax.legend(loc='upper right', fontsize=8, framealpha=0.9,
                 bbox_to_anchor=(1.0, 1.0), ncol=1)

    def _plot_momentum_chart(self, ax, x, price_data, base_data, external_data, variable_info, colors):
        """모멘텀 차트 플롯 (MACD 등)"""
        # 모멘텀 데이터
        variable_name = variable_info.get('variable_name', '모멘텀') if variable_info else '모멘텀'
        ax.plot(x, price_data, colors['primary'], linewidth=1.5, label=variable_name, alpha=0.8)

        # 중앙선 (0선)
        ax.axhline(y=0, color=colors['reference'], linewidth=1, linestyle='-',
                  label='Zero Line', alpha=0.6)

        # 기본/외부 변수 처리
        self._plot_variable_data(ax, x, base_data, external_data, colors)

        # 범례 추가
        ax.legend(loc='upper right', fontsize=8, framealpha=0.9,
                 bbox_to_anchor=(1.0, 1.0), ncol=1)

    def _plot_volume_chart(self, ax, x, price_data, base_data, external_data, variable_info, colors):
        """단순화된 볼륨 차트 - 4가지 요소 통일 (Volume + iVal + fVal/eVal + Trg)"""
        print("🎨 단순화된 volume 차트 플롯 시작")

        # 1. Volume 데이터 (파란색 히스토그램)
        ax.bar(x, price_data, color=colors['primary'], alpha=0.6, label='Volume', width=0.8)
        print(f"   📊 Volume 데이터: {len(price_data)}개 포인트")

        # 2. iVal - 기본변수 (녹색 라인)
        if base_data and len(base_data) > 0:
            ax.plot(x, base_data, colors['base_var'], linewidth=1.8,
                   label='iVal', alpha=0.9)
            print(f"   🟢 iVal 데이터: {len(base_data)}개 포인트")

        # 3. fVal/eVal - 비교값/외부변수 (주황색)
        if external_data and len(external_data) > 0:
            # 고정값인지 확인
            is_fixed = len(set(external_data)) == 1

            if is_fixed:
                fixed_value = external_data[0]
                ax.axhline(y=fixed_value, color=colors['external_var'], linewidth=1.5,
                           linestyle='--', label='fVal', alpha=0.8)
                print(f"   🟡 fVal(고정값): {fixed_value}")
            else:
                ax.plot(x, external_data, colors['external_var'], linewidth=1.8,
                        label='eVal', alpha=0.9)
                print(f"   🟡 eVal 데이터: {len(external_data)}개 포인트")

        # 4. Trg - 트리거 마커는 _plot_trigger_signals_enhanced()에서 처리

        # 5. 범례 추가
        legend_handles, legend_labels = ax.get_legend_handles_labels()
        print(f"   📋 범례 요소: {len(legend_handles)}개, 라벨: {legend_labels}")

        if legend_handles:
            ax.legend(loc='upper right', fontsize=8, framealpha=0.9,
                     bbox_to_anchor=(1.0, 1.0), ncol=1)
            print("   ✅ 범례 표시 완료")
        else:
            print("   ⚠️ 표시할 범례 요소가 없음")

        print("✅ volume 차트 플롯 완료")

    def _plot_variable_data(self, ax, x, base_data, external_data, colors):
        """기본/외부 변수 데이터 플롯 (공통 로직)"""
        if base_data:
            if self._is_fixed_value(base_data):
                fixed_value = base_data[0] if base_data else 0
                ax.axhline(y=fixed_value, color=colors['base_var'], linewidth=1.2,
                         linestyle='--', label=f'기본변수: {fixed_value:.1f}', alpha=0.7)
            else:
                ax.plot(x, base_data, colors['base_var'], linewidth=1.2,
                       label='기본변수', alpha=0.8)

        if external_data:
            if self._is_fixed_value(external_data):
                fixed_value = external_data[0] if external_data else 0
                ax.axhline(y=fixed_value, color=colors['external_var'], linewidth=1.2,
                         linestyle=':', label=f'외부변수: {fixed_value:.1f}', alpha=0.7)
            else:
                ax.plot(x, external_data, colors['external_var'], linewidth=1.2,
                       label='외부변수', alpha=0.8)

    def _setup_enhanced_chart_style(self, ax, bg_color, variable_info):
        """향상된 차트 스타일 설정"""
        # Y축 라벨 설정 (변수 정보 기반)
        if variable_info:
            unit = variable_info.get('unit', '')
            y_label = f"Value{' (' + unit + ')' if unit else ''}"
        else:
            y_label = 'Value'

        ax.set_ylabel(y_label, fontsize=10)

        # Y축 틱 라벨 포맷팅 (카테고리별 최적화)
        chart_category = self._get_chart_category(variable_info)

        if chart_category == 'volume':
            # 거래량: 간략 표기 (1M, 1K 등)
            def format_volume_tick(value, pos):
                if value >= 1000000:
                    return f"{value / 1000000:.1f}M"
                elif value >= 1000:
                    return f"{value / 1000:.0f}K"
                else:
                    return f"{value:.0f}"

            from matplotlib.ticker import FuncFormatter
            ax.yaxis.set_major_formatter(FuncFormatter(format_volume_tick))

        elif chart_category in ['oscillator', 'momentum']:
            # 오실레이터/모멘텀: 소수점 1자리
            def format_indicator_tick(value, pos):
                return f"{value:.1f}"

            from matplotlib.ticker import FuncFormatter
            ax.yaxis.set_major_formatter(FuncFormatter(format_indicator_tick))

        else:
            # 가격: 기존 로직
            def format_price_tick(value, pos):
                if value >= 1000000:
                    return f"{value / 1000000:.1f}m"
                elif value >= 1000:
                    return f"{value / 1000:.0f}k"
                elif value >= 1:
                    return f"{value:.0f}"
                else:
                    return f"{value:.1f}"

            from matplotlib.ticker import FuncFormatter
            ax.yaxis.set_major_formatter(FuncFormatter(format_price_tick))

        # 틱 라벨 크기 설정
        ax.tick_params(axis='both', which='major', labelsize=10)

        # 그리드 및 배경색 설정
        ax.grid(True, alpha=0.3)
        ax.set_facecolor(bg_color)

        # 범례 설정 (최대 4개만 표시)
        legend = ax.legend(loc='upper left', fontsize=8, ncol=1)
        if legend and len(legend.get_texts()) > 4:
            # 범례가 너무 많으면 숨김
            legend.set_visible(False)

    def _plot_trigger_signals_enhanced(self, ax, trigger_results, price_data, base_data,
                                     external_data, chart_category, trigger_color):
        """간소화된 트리거 신호 표시 - iVal 기준 상단 10% 위치 통일"""
        if not trigger_results:
            return

        # 미니차트 변수 서비스 활용
        if MINICHART_SERVICE_AVAILABLE:
            try:
                minichart_service = get_minichart_variable_service()
                color_scheme = minichart_service.get_color_scheme()
                trigger_color = color_scheme.get('trigger', trigger_color)
            except Exception:
                pass

        self.test_history_list.clear()
        trigger_positions = []

        for i, (triggered, _) in enumerate(trigger_results):
            if triggered and i < len(price_data):
                # iVal(base_data) 기준 상단 10% 위치에 마커 배치 (모든 지표 통일)
                if base_data and i < len(base_data) and base_data[i] is not None:
                    # 전체 base_data 범위의 10% 오프셋 적용
                    valid_base = [val for val in base_data if val is not None]
                    if valid_base:
                        base_range = max(valid_base) - min(valid_base)
                        offset = base_range * 0.1  # 10% 오프셋으로 증가
                        y_value = base_data[i] + offset
                    else:
                        y_value = base_data[i] + 5.0  # 기본 오프셋
                else:
                    # base_data가 없으면 price_data 기준 (fallback)
                    y_value = price_data[i] * 1.05

                # 통일된 마커 스타일: 빨간 역삼각형
                ax.scatter(i, y_value, c=trigger_color, s=40, marker='v',
                           zorder=5, edgecolors='white', linewidth=1.0, alpha=0.9)

                trigger_positions.append(i)

                # 작동 기록 추가 (iVal 값 기준)
                base_value = base_data[i] if base_data and i < len(base_data) else price_data[i]
                if isinstance(base_value, (int, float)):
                    if base_value >= 1000:
                        value_str = f"{base_value:,.0f}"
                    else:
                        value_str = f"{base_value:.2f}"
                else:
                    value_str = str(base_value)

                self.add_test_history_item(
                    f"[{i:03d}] Trigger: {value_str}",
                    "success"
                )

        # 범례에 간단한 트리거 라벨만 표시 (카운트 제거)
        if trigger_positions:
            ax.scatter([], [], c=trigger_color, s=40, marker='v',
                       label='Trg', zorder=5, edgecolors='white',
                       linewidth=1.0, alpha=0.9)

    def _is_fixed_value(self, data):
        """데이터가 고정값인지 확인 (모든 값이 동일한 경우)"""
        if not data or len(data) <= 1:
            return True
        return all(abs(x - data[0]) < 0.0001 for x in data)

    def _get_base_indicator_data(self, variable_info, data_length):
        """서브플롯용 베이스 지표 데이터 생성 (예: 거래량, RSI 기본 범위)"""
        if not variable_info:
            return None

        variable_id = variable_info.get('variable_id', '')

        # 거래량 지표의 경우 가상 거래량 데이터 생성
        if 'VOLUME' in variable_id:
            import random
            return [random.randint(1000000, 5000000) for _ in range(data_length)]

        # RSI 계열의 경우 0-100 범위의 가상 데이터
        elif variable_id in ['RSI', 'STOCHASTIC']:
            import random
            return [random.uniform(20, 80) for _ in range(data_length)]

        # ATR 같은 변동성 지표의 경우
        elif variable_id == 'ATR':
            import random
            return [random.uniform(1000, 5000) for _ in range(data_length)]

        # MACD의 경우
        elif variable_id == 'MACD':
            import random
            return [random.uniform(-100, 100) for _ in range(data_length)]

        return None

    def _get_base_indicator_name(self, variable_info):
        """베이스 지표 이름 반환"""
        if not variable_info:
            return "베이스 지표"

        variable_id = variable_info.get('variable_id', '')

        name_mapping = {
            'VOLUME': '거래량',
            'VOLUME_SMA': '거래량',
            'RSI': 'RSI 기준선',
            'STOCHASTIC': '스토캐스틱 기준선',
            'ATR': 'ATR 기준선',
            'MACD': 'MACD 기준선'
        }

        return name_mapping.get(variable_id, '베이스 지표')

    def update_trigger_signals(self, simulation_result_data):
        """트리거 신호들을 작동 기록에 업데이트"""
        try:
            scenario = simulation_result_data.get('scenario', 'Unknown')
            price_data = simulation_result_data.get('price_data', [])
            trigger_points = simulation_result_data.get('trigger_points', [])

            # 기존 작동 기록 클리어 (새 시뮬레이션 시작)
            self.test_history_list.clear()

            # 개별 트리거 신호들을 작동 기록에 추가
            if trigger_points and len(trigger_points) > 0:
                for idx, point_idx in enumerate(trigger_points):
                    if 0 <= point_idx < len(price_data):
                        price_value = price_data[point_idx]
                        signal_detail = f"[{point_idx:03d}] 트리거 발동 #{idx + 1}: 가격 {price_value:,.0f}"
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
        """시뮬레이션 결과로 차트 및 기록 업데이트 - 변수 정보 포함"""
        try:
            scenario = chart_simulation_data.get('scenario', 'Unknown')
            price_data = chart_simulation_data.get('price_data', [])
            trigger_points = trigger_results.get('trigger_points', [])

            # 변수 정보 및 실제 계산된 데이터 추출
            variable_info = chart_simulation_data.get('variable_info', {})
            external_variable_info = chart_simulation_data.get('external_variable_info', {})

            # 외부 변수 정보를 인스턴스 변수로 저장 (차트 플롯팅에서 사용)
            self._external_variable_info = external_variable_info

            # 실제 계산된 변수 데이터 우선 사용
            base_variable_data = chart_simulation_data.get('base_variable_data', None)
            external_variable_data = chart_simulation_data.get('external_variable_data', None)

            print(f"📊 차트 업데이트 - 변수정보: {variable_info.get('variable_name', 'Unknown')}, "
                  f"카테고리: {variable_info.get('category', 'Unknown')}")
            if external_variable_info:
                print(f"📊 외부변수정보: {external_variable_info.get('variable_name', 'Unknown')}")
            else:
                print("📊 외부변수정보: 없음 (단일 변수 조건)")
            print(f"🔍 실제 계산된 base_variable_data: {base_variable_data is not None and len(base_variable_data) if base_variable_data else 'None'}")
            print(f"🔍 실제 계산된 external_variable_data: {external_variable_data is not None and len(external_variable_data) if external_variable_data else 'None'}")

            # 차트 업데이트 (변수 정보 포함)
            if price_data:
                # 트리거 결과를 (triggered, value) 튜플 리스트로 변환
                trigger_results_for_chart = []
                for i, value in enumerate(price_data):
                    triggered = i in trigger_points
                    trigger_results_for_chart.append((triggered, value))

                # 실제 계산된 데이터가 없는 경우에만 폴백 생성
                if base_variable_data is None and variable_info:
                    print("⚠️ 실제 계산된 기본 변수 데이터가 없음, 폴백 데이터 생성")
                    base_variable_data = self._generate_variable_simulation_data(
                        variable_info, len(price_data), chart_simulation_data.get('target_value')
                    )

                if external_variable_data is None and external_variable_info:
                    print("⚠️ 실제 계산된 외부 변수 데이터가 없음, 폴백 데이터 생성")
                    external_variable_data = self._generate_variable_simulation_data(
                        external_variable_info, len(price_data), chart_simulation_data.get('target_value')
                    )

                # 차트 업데이트 (새로운 파라미터 포함)
                # 고정값 비교 정보 추출 (target_value 사용)
                comparison_value = chart_simulation_data.get('target_value')

                self.update_simulation_chart(
                    scenario,
                    price_data,
                    trigger_results_for_chart,
                    base_variable_data=base_variable_data,
                    external_variable_data=external_variable_data,
                    variable_info=variable_info,
                    comparison_value=comparison_value
                )

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
            import traceback
            traceback.print_exc()

    def _generate_variable_simulation_data(self, variable_info, data_length, target_value=None):
        """변수 시뮬레이션 데이터 생성"""
        if not variable_info:
            return None

        try:
            category = variable_info.get('category', 'price_overlay')
            scale_min = variable_info.get('scale_min')
            scale_max = variable_info.get('scale_max')

            # 고정값인 경우
            if target_value is not None:
                return [target_value] * data_length

            # 카테고리별 시뮬레이션 데이터 생성
            import random

            if category == 'oscillator' and scale_min is not None and scale_max is not None:
                # 오실레이터: 스케일 범위 내 랜덤
                return [random.uniform(scale_min, scale_max) for _ in range(data_length)]

            elif category == 'momentum':
                # 모멘텀: -10 ~ 10 범위
                min_val = scale_min if scale_min is not None else -10
                max_val = scale_max if scale_max is not None else 10
                return [random.uniform(min_val, max_val) for _ in range(data_length)]

            elif category == 'volume':
                # 거래량: 큰 숫자
                return [random.randint(1000000, 5000000) for _ in range(data_length)]

            else:
                # 가격 계열: 큰 숫자
                base_price = 50000000
                return [base_price + random.uniform(-5000000, 5000000) for _ in range(data_length)]

        except Exception as e:
            print(f"⚠️ 변수 시뮬레이션 데이터 생성 실패: {e}")
            return None

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
