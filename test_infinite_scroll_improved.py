#!/usr/bin/env python3
"""
TASK-003 개선된 무한 스크롤 기능 테스트
- 절대적 뷰포트 보존 방식
- 단순화된 로딩 조건 
"""

import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from upbit_auto_trading.ui.desktop.screens.chart_view.chart_view_screen import ChartViewScreen

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def show_test_guide():
    """테스트 가이드 메시지 표시"""
    msg = QMessageBox()
    msg.setWindowTitle("📊 TASK-003 개선된 무한 스크롤 테스트")
    msg.setIcon(QMessageBox.Icon.Information)
    
    guide_text = """
🎯 개선된 무한 스크롤 기능 테스트

✅ 주요 개선사항:
• 사용자 뷰포트 절대 보존 (복잡한 조건 제거)
• 단순화된 로딩 조건 (왼쪽 끝 도달 시에만)
• 실시간 업데이트 시 뷰포트 유지

🧪 테스트 시나리오:

1️⃣ 무한 스크롤 테스트:
   • 왼쪽으로 스크롤하여 과거 데이터 로딩 확인
   • 800개 이상 스크롤 가능한지 확인 (5000개까지)
   • 축소/확대 상태에서도 정상 동작 확인

2️⃣ 뷰포트 보존 테스트:
   • 과거 데이터 탐색 중 실시간 캔들 추가 시
   • 뷰포트가 절대 변경되지 않는지 확인
   • 최신 데이터 보기 중일 때만 자동 스크롤

3️⃣ 메모리 관리 테스트:
   • 장시간 스크롤 시 5000개 제한 동작
   • 메모리 사용량 안정성 확인

⚠️ 주의사항:
• 1분봉으로 테스트하여 실시간 업데이트 확인
• 좌측 끝까지 스크롤하여 800+ 캔들 확인
• 과거 데이터 탐색 중 새 캔들 추가 테스트

준비되면 확인을 눌러 테스트를 시작하세요!
"""
    msg.setText(guide_text)
    msg.exec()

def main():
    """테스트 실행"""
    logger.info("개선된 무한 스크롤 기능 테스트 시작")
    
    app = QApplication(sys.argv)
    
    # 테스트 가이드 표시
    QTimer.singleShot(1000, show_test_guide)
    
    # 차트 뷰 화면 생성 (기본 생성자 사용)
    chart_screen = ChartViewScreen()
    
    # 1분봉으로 시간대 변경 (실시간 테스트용)
    QTimer.singleShot(2000, lambda: chart_screen.on_timeframe_changed("1분"))
    
    chart_screen.show()
    
    logger.info("차트 뷰 화면이 시작되었습니다.")
    logger.info("왼쪽으로 스크롤하여 개선된 무한 스크롤 기능을 테스트하세요!")
    logger.info("800개 이상 스크롤 가능하고, 뷰포트가 절대 보존되는지 확인하세요!")
    
    # 애플리케이션 실행
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
