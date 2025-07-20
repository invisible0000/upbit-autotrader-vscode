#!/usr/bin/env python3
"""
지표 통합 테스트 스크립트 - 표준 파라미터 포함
- 상부 액션바의 퀵 지표 추가가 우측 지표 패널과 연동되는지 테스트
- 암호화폐 차트 분석용 표준 지표 파라미터 테스트
"""

import sys
import os

# 프로젝트 루트를 sys.path에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from upbit_auto_trading.ui.desktop.screens.chart_view.chart_view_screen import ChartViewScreen

def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # 차트 뷰 화면 생성
    chart_view = ChartViewScreen()
    chart_view.show()
    
    print("=" * 60)
    print("🚀 지표 통합 테스트 - 표준 파라미터 포함")
    print("=" * 60)
    print()
    print("📈 테스트 시나리오:")
    print()
    print("1️⃣ 상부 액션바 테스트:")
    print("   • '+ 지표' 버튼 클릭")
    print("   • 표준 파라미터가 포함된 지표 목록 확인")
    print("   • MA5, MA20, RSI14, MACD(12,26,9) 등 선택 테스트")
    print()
    print("2️⃣ 우측 지표 패널 테스트:")
    print("   • 추가된 지표가 올바르게 표시되는지 확인")
    print("   • '지표 추가' 버튼으로 상세 설정 테스트")
    print()
    print("3️⃣ 지표 연동 테스트:")
    print("   • 양쪽 방법으로 추가한 지표가 통합 관리되는지 확인")
    print("   • 지표 가시성 토글, 설정 변경, 제거 기능 테스트")
    print()
    print("🎯 추가된 표준 지표:")
    print("   📊 이동평균: MA5, MA10, MA20, MA60, MA120")
    print("   📈 지수이동평균: EMA12, EMA20, EMA26")
    print("   📉 기술지표: RSI14, MACD(12,26,9), 볼린저밴드(20,2), 스토캐스틱(14,3,3)")
    print()
    print("=" * 60)
    print("🎮 테스트를 시작하세요!")
    print("=" * 60)
    
    # 애플리케이션 실행
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
