#!/usr/bin/env python3
"""
간단한 무한 스크롤 테스트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simple_import():
    """간단한 import 테스트"""
    try:
        from upbit_auto_trading.ui.desktop.screens.chart_view.candlestick_chart import CandlestickChart
        logger.info("CandlestickChart import 성공")
        
        # QApplication이 필요한 테스트는 여기서 하지 않고 메서드만 확인
        import inspect
        sig = inspect.signature(CandlestickChart.update_data)
        logger.info(f"update_data 메서드 시그니처: {sig}")
        
        return True
        
    except Exception as e:
        logger.error(f"Import 실패: {e}")
        return False

def test_chart_creation():
    """차트 생성 테스트"""
    try:
        from upbit_auto_trading.ui.desktop.screens.chart_view.chart_view_screen import ChartViewScreen
        from upbit_auto_trading.ui.desktop.screens.chart_view.candlestick_chart import CandlestickChart
        logger.info("ChartViewScreen import 성공")
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # CandlestickChart 생성 테스트
        chart = CandlestickChart()
        logger.info("CandlestickChart 생성 성공")
        
        # 메서드 시그니처 실제 확인
        import inspect
        sig = inspect.signature(chart.update_data)
        logger.info(f"update_data 메서드 실제 시그니처: {sig}")
        
        # 간단한 ChartViewScreen 생성 테스트
        chart_screen = ChartViewScreen()
        logger.info("ChartViewScreen 생성 성공")
        
        # 5초 후 종료
        QTimer.singleShot(5000, app.quit)
        
        return True
        
    except Exception as e:
        logger.error(f"차트 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 함수"""
    logger.info("간단한 테스트 시작")
    
    # 1. import 테스트
    if not test_simple_import():
        logger.error("Import 테스트 실패")
        return False
    
    # 2. 차트 생성 테스트
    if not test_chart_creation():
        logger.error("차트 생성 테스트 실패")
        return False
    
    logger.info("모든 테스트 성공")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
