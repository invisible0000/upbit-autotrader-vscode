#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
무한 스크롤 기능 테스트 스크립트
"""

import sys
import os
import logging

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer
from upbit_auto_trading.ui.desktop.screens.chart_view.chart_view_screen import ChartViewScreen

# 디버깅을 위한 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('infinite_scroll_test.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """무한 스크롤 테스트 실행"""
    try:
        logger.info("무한 스크롤 기능 테스트 시작")
        
        # Qt 애플리케이션 생성
        app = QApplication(sys.argv)
        
        # 차트 뷰 화면 생성
        chart_view = ChartViewScreen()
        chart_view.setWindowTitle("업비트 자동매매 - 무한 스크롤 테스트")
        chart_view.resize(1400, 900)
        chart_view.show()
        
        # 테스트 가이드 메시지 표시
        def show_guide():
            QMessageBox.information(
                chart_view,
                "무한 스크롤 테스트 가이드 (개선된 버전)",
                "📊 무한 스크롤 개선사항:\n\n"
                "✅ 스마트 로딩: 축소 시 불필요한 데이터 로딩 방지\n"
                "✅ 뷰포트 보존: 데이터 로드 시 화면 위치 유지\n"
                "✅ 메모리 관리: 최대 5000개 캔들로 제한\n"
                "✅ 버퍼 체크: 100개 캔들 버퍼 유지\n\n"
                "🔧 테스트 방법:\n"
                "1. 차트를 확대한 후 왼쪽으로 스크롤 → 데이터 로드\n"
                "2. 차트를 축소한 후 스크롤 → 로딩 안 함 (최적화)\n"
                "3. 로그에서 메모리 사용량 확인\n\n"
                "💡 1분 차트로 변경하면 더 빠른 테스트 가능!"
            )
        
        # 2초 후에 가이드 메시지 표시
        QTimer.singleShot(2000, show_guide)
        
        logger.info("차트 뷰 화면이 시작되었습니다.")
        logger.info("왼쪽으로 스크롤하여 무한 스크롤 기능을 테스트하세요!")
        
        # 애플리케이션 실행
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"테스트 실행 중 오류: {e}")
        raise

if __name__ == "__main__":
    main()
