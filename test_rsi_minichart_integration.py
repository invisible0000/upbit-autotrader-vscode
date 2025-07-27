#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RSI 미니차트 통합 테스트

새로 만든 미니차트 변수 서비스와 기존 RSI 계산/표시 시스템의 통합을 테스트합니다.
"""

import sys
import os
import logging
from datetime import datetime
import numpy as np

# PyQt6와 호환되는 matplotlib 백엔드 설정
os.environ['QT_API'] = 'PyQt6'

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QLabel, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt

# 프로젝트 경로 추가
project_root = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', '..', '..', '..'
))
sys.path.insert(0, project_root)

# 컴포넌트 import
try:
    from upbit_auto_trading.ui.desktop.screens.strategy_management.\
        trigger_builder.components.trigger_calculator import TriggerCalculator
    from upbit_auto_trading.ui.desktop.screens.strategy_management.\
        trigger_builder.components.shared.minichart_variable_service import \
        get_minichart_variable_service
    print("✅ 모든 컴포넌트 import 성공")
except ImportError as e:
    print(f"❌ Import 실패: {e}")
    sys.exit(1)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class RSIMiniChartTestWidget(QWidget):
    """RSI 미니차트 테스트 위젯"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_data()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("RSI 미니차트 통합 테스트")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # 정보 표시
        self.info_label = QLabel("RSI 계산 및 미니차트 서비스 통합 테스트를 진행합니다...")
        layout.addWidget(self.info_label)
        
        # 버튼들
        button_layout = QHBoxLayout()
        
        self.test_service_btn = QPushButton("1. 미니차트 서비스 테스트")
        self.test_service_btn.clicked.connect(self.test_minichart_service)
        button_layout.addWidget(self.test_service_btn)
        
        self.test_rsi_calc_btn = QPushButton("2. RSI 계산 테스트")
        self.test_rsi_calc_btn.clicked.connect(self.test_rsi_calculation)
        button_layout.addWidget(self.test_rsi_calc_btn)
        
        self.test_integration_btn = QPushButton("3. 통합 차트 테스트")
        self.test_integration_btn.clicked.connect(self.test_integration)
        button_layout.addWidget(self.test_integration_btn)
        
        layout.addLayout(button_layout)
        
        # 차트 영역
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        self.setWindowTitle("RSI 미니차트 통합 테스트")
        self.resize(1000, 700)
        
    def init_data(self):
        """테스트 데이터 초기화"""
        # 샘플 가격 데이터 생성 (비트코인 모의 데이터)
        np.random.seed(42)  # 재현 가능한 결과를 위해
        
        base_price = 50000000  # 5천만원
        returns = np.random.normal(0, 0.02, 100)  # 일일 수익률 2% 변동성
        prices = [base_price]
        
        for return_rate in returns:
            new_price = prices[-1] * (1 + return_rate)
            prices.append(max(new_price, base_price * 0.5))  # 최소 50% 하락 제한
            
        self.price_data = prices[1:]  # 첫 번째 값 제외
        
        # 날짜 데이터
        self.dates = [
            datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            for i in range(len(self.price_data))
        ]
        
        logging.info(f"테스트 데이터 생성: {len(self.price_data)}일간 가격 데이터")
        logging.info(f"가격 범위: {min(self.price_data):,.0f} ~ {max(self.price_data):,.0f}")
        
    def test_minichart_service(self):
        """미니차트 서비스 테스트"""
        try:
            service = get_minichart_variable_service()
            
            # RSI 변수 설정 조회
            rsi_config = service.get_variable_config('RSI')
            if not rsi_config:
                self.info_label.setText("❌ RSI 변수 설정을 찾을 수 없습니다")
                return
                
            # 정보 표시
            info_text = f"""✅ 미니차트 서비스 테스트 성공

RSI 변수 설정:
- 변수 ID: {rsi_config.variable_id}
- 변수명: {rsi_config.variable_name}
- 카테고리: {rsi_config.category}
- 스케일 타입: {rsi_config.scale_type}
- 표시 모드: {rsi_config.display_mode}
- 스케일 범위: {rsi_config.scale_min} ~ {rsi_config.scale_max}
- 자동 스케일: {rsi_config.auto_scale}
- 기본 색상: {rsi_config.primary_color}

스케일 그룹 정보:"""
            
            scale_group = service.get_scale_group(rsi_config.scale_type)
            if scale_group:
                info_text += f"\n- 그룹명: {scale_group['group_name']}"
                info_text += f"\n- 범위: {scale_group['min_value']} ~ {scale_group['max_value']}"
                if 'reference_lines' in scale_group:
                    info_text += "\n- 참조선:"
                    for line in scale_group['reference_lines']:
                        info_text += f"\n  • {line['label']}: {line['value']} ({line['color']})"
            
            # 색상 스키마
            colors = service.get_color_scheme()
            info_text += "\n\n색상 스키마:"
            for element, color in colors.items():
                info_text += f"\n- {element}: {color}"
                
            self.info_label.setText(info_text)
            logging.info("미니차트 서비스 테스트 완료")
            
        except Exception as e:
            error_msg = f"❌ 미니차트 서비스 테스트 실패: {e}"
            self.info_label.setText(error_msg)
            logging.error(error_msg)
    
    def test_rsi_calculation(self):
        """RSI 계산 테스트"""
        try:
            calculator = TriggerCalculator()
            
            # RSI 계산
            rsi_values = calculator.calculate_rsi(self.price_data, period=14)
            
            # 결과 분석
            valid_rsi = [val for val in rsi_values if val is not None]
            if not valid_rsi:
                self.info_label.setText("❌ RSI 계산 결과가 없습니다")
                return
                
            info_text = f"""✅ RSI 계산 테스트 성공

계산 결과:
- 전체 데이터: {len(self.price_data)}개
- 유효한 RSI: {len(valid_rsi)}개
- RSI 범위: {min(valid_rsi):.2f} ~ {max(valid_rsi):.2f}
- 평균 RSI: {np.mean(valid_rsi):.2f}
- 최근 RSI: {valid_rsi[-1]:.2f}

범위 검증:
- 0-100 범위 내: {'✅' if all(0 <= val <= 100 for val in valid_rsi) else '❌'}
- 과매도(30 이하): {len([v for v in valid_rsi if v <= 30])}개
- 과매수(70 이상): {len([v for v in valid_rsi if v >= 70])}개"""
            
            self.info_label.setText(info_text)
            
            # 간단한 차트 그리기
            self.figure.clear()
            ax1 = self.figure.add_subplot(2, 1, 1)
            ax2 = self.figure.add_subplot(2, 1, 2)
            
            # 가격 차트
            ax1.plot(range(len(self.price_data)), self.price_data, 'b-', linewidth=1)
            ax1.set_title('가격 데이터')
            ax1.set_ylabel('가격 (원)')
            ax1.grid(True, alpha=0.3)
            
            # RSI 차트
            ax2.plot(range(len(rsi_values)), rsi_values, 'g-', linewidth=1.5, label='RSI')
            ax2.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='과매수선(70)')
            ax2.axhline(y=30, color='r', linestyle='--', alpha=0.7, label='과매도선(30)')
            ax2.set_title('RSI 지표')
            ax2.set_ylabel('RSI')
            ax2.set_ylim(0, 100)
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            logging.info("RSI 계산 테스트 완료")
            
        except Exception as e:
            error_msg = f"❌ RSI 계산 테스트 실패: {e}"
            self.info_label.setText(error_msg)
            logging.error(error_msg)
    
    def test_integration(self):
        """미니차트 서비스와 RSI 계산 통합 테스트"""
        try:
            # 서비스와 계산기 초기화
            service = get_minichart_variable_service()
            calculator = TriggerCalculator()
            
            # RSI 변수 설정 조회
            rsi_config = service.get_variable_config('RSI')
            if not rsi_config:
                raise ValueError("RSI 변수 설정을 찾을 수 없습니다")
                
            # RSI 계산
            rsi_values = calculator.calculate_rsi(self.price_data, 
                                                period=rsi_config.default_parameters.get('period', 14))
            
            # 레이아웃 정보 생성 (고정값 70과 함께)
            layout_info = service.create_layout_info(
                base_variable_id='RSI',
                fixed_value=70.0,
                trigger_points=[20, 50, 80]  # 예시 트리거 포인트
            )
            
            # 4요소 미니차트 그리기
            self.figure.clear()
            
            # RSI는 서브플롯으로 표시
            gs = self.figure.add_gridspec(2, 1, height_ratios=[0.6, 0.4], hspace=0.3)
            ax_price = self.figure.add_subplot(gs[0])
            ax_rsi = self.figure.add_subplot(gs[1])
            
            # 1. Price 요소
            ax_price.plot(range(len(self.price_data)), self.price_data, 
                         color=layout_info.color_scheme['price'], 
                         linewidth=1.5, label='Price')
            ax_price.set_title('가격 차트 (Price)')
            ax_price.set_ylabel('가격 (원)')
            ax_price.grid(True, alpha=0.3)
            ax_price.legend()
            
            # 2. iVal (RSI) 요소  
            ax_rsi.plot(range(len(rsi_values)), rsi_values,
                       color=layout_info.color_scheme['indicator'],
                       linewidth=2, label='iVal (RSI)')
            
            # 3. fVal (고정값 70) 요소
            for element in layout_info.comparison_elements:
                if element['type'] == 'fixed_value':
                    ax_rsi.axhline(y=element['value'], 
                                  color=element['color'],
                                  linestyle=element.get('linestyle', '-'),
                                  alpha=0.8,
                                  label=element['label'])
            
            # 4. Trg (트리거) 요소
            for element in layout_info.trigger_markers:
                if element['type'] == 'trigger_points':
                    for pos in element['positions']:
                        if pos < len(rsi_values) and rsi_values[pos] is not None:
                            ax_rsi.scatter(pos, rsi_values[pos],
                                         color=element['color'],
                                         marker=element['marker'],
                                         s=element['size'],
                                         alpha=0.8,
                                         label=element['label'] if pos == element['positions'][0] else "")
            
            # 스케일 그룹의 참조선 추가
            scale_group = service.get_scale_group(rsi_config.scale_type)
            if scale_group and 'reference_lines' in scale_group:
                for line in scale_group['reference_lines']:
                    ax_rsi.axhline(y=line['value'], 
                                  color=line['color'], 
                                  linestyle=':', 
                                  alpha=0.6,
                                  label=line['label'])
            
            ax_rsi.set_title('RSI 지표 (4요소 미니차트)')
            ax_rsi.set_ylabel('RSI')
            ax_rsi.set_ylim(0, 100)
            ax_rsi.grid(True, alpha=0.3)
            ax_rsi.legend()
            
            self.canvas.draw()
            
            # 결과 정보
            valid_rsi = [val for val in rsi_values if val is not None]
            info_text = f"""✅ 통합 테스트 성공

4요소 미니차트 구성:
1. Price: 가격 데이터 ({layout_info.color_scheme['price']})
2. iVal: RSI 지표 ({layout_info.color_scheme['indicator']})
3. fVal: 고정값 70 ({layout_info.color_scheme['comparison']})
4. Trg: 트리거 포인트 3개 ({layout_info.color_scheme['trigger']})

RSI 통계:
- 현재값: {valid_rsi[-1]:.2f}
- 범위: {min(valid_rsi):.2f} ~ {max(valid_rsi):.2f}
- 평균: {np.mean(valid_rsi):.2f}

레이아웃 정보:
- 메인 요소: {len(layout_info.main_elements)}개
- 비교 요소: {len(layout_info.comparison_elements)}개  
- 트리거 마커: {len(layout_info.trigger_markers)}개"""
            
            self.info_label.setText(info_text)
            logging.info("통합 테스트 완료")
            
        except Exception as e:
            error_msg = f"❌ 통합 테스트 실패: {e}"
            self.info_label.setText(error_msg)
            logging.error(error_msg, exc_info=True)


class RSIMiniChartTestWindow(QMainWindow):
    """메인 테스트 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("RSI 미니차트 통합 테스트")
        self.setGeometry(100, 100, 1200, 800)
        
        # 중앙 위젯 설정
        central_widget = RSIMiniChartTestWidget()
        self.setCentralWidget(central_widget)


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # 윈도우 생성 및 표시
    window = RSIMiniChartTestWindow()
    window.show()
    
    # 이벤트 루프 시작
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
