#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
웹소켓 실시간 차트 업데이트 테스트 스크립트
"""

import sys
import os
import logging

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from upbit_auto_trading.ui.desktop.screens.chart_view.chart_view_screen import ChartViewScreen

# 디버깅을 위한 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('websocket_chart_test.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """웹소켓 차트 테스트 실행"""
    try:
        logger.info("웹소켓 실시간 차트 테스트 시작")
        
        # Qt 애플리케이션 생성
        app = QApplication(sys.argv)
        
        # 차트 뷰 화면 생성
        chart_view = ChartViewScreen()
        chart_view.setWindowTitle("업비트 자동매매 - 웹소켓 실시간 차트 테스트 (1분)")
        chart_view.resize(1400, 900)
        chart_view.show()
        
        # 1분 차트로 자동 변경 (실시간 캔들 변화 확인용)
        from PyQt6.QtCore import QTimer
        
        def change_to_1min():
            try:
                # 1분 차트로 변경
                chart_view.on_timeframe_changed("1분")
                
                # UI 버튼 상태 변경
                for tf, btn in chart_view.timeframe_buttons.items():
                    btn.setChecked(tf == "1분")
                    
                logger.info("1분 차트로 자동 변경됨 - 실시간 캔들 변화를 확인하세요!")
                
            except Exception as e:
                logger.error(f"1분 차트 변경 중 오류: {e}")
        
        # 2초 후에 1분 차트로 변경
        QTimer.singleShot(2000, change_to_1min)
        
        logger.info("차트 뷰 화면이 시작되었습니다.")
        logger.info("2초 후 1분 차트로 자동 변경되어 실시간 캔들 변화를 확인할 수 있습니다.")
        
        # 애플리케이션 실행
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"테스트 실행 중 오류: {e}")
        raise

if __name__ == "__main__":
    main()
