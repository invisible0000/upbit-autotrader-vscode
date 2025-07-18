"""
대시보드 테스트 모듈

이 모듈은 업비트 자동매매 시스템의 대시보드 화면 기능을 테스트합니다.
"""

import unittest
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

# 테스트 환경 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 테스트할 클래스 임포트
from upbit_auto_trading.ui.desktop.screens.dashboard.dashboard_screen import DashboardScreen
from upbit_auto_trading.ui.desktop.screens.dashboard.widgets.portfolio_summary_widget import PortfolioSummaryWidget
from upbit_auto_trading.ui.desktop.screens.dashboard.widgets.active_positions_widget import ActivePositionsWidget
from upbit_auto_trading.ui.desktop.screens.dashboard.widgets.market_overview_widget import MarketOverviewWidget


class TestDashboard(unittest.TestCase):
    """대시보드 테스트 클래스"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        # QApplication 인스턴스가 없으면 생성
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """각 테스트 전에 실행"""
        # 대시보드 화면 생성
        self.dashboard_screen = DashboardScreen()
    
    def test_dashboard_screen_creation(self):
        """대시보드 화면 생성 테스트"""
        print("\n=== 테스트: 대시보드 화면 생성 ===")
        
        # 대시보드 화면이 생성되었는지 확인
        self.assertIsNotNone(self.dashboard_screen)
        print("대시보드 화면이 생성되었습니다.")
        
        # 필요한 위젯들이 포함되어 있는지 확인
        self.assertIsNotNone(self.dashboard_screen.portfolio_summary_widget)
        print("포트폴리오 요약 위젯이 존재합니다.")
        
        self.assertIsNotNone(self.dashboard_screen.active_positions_widget)
        print("활성 거래 목록 위젯이 존재합니다.")
        
        self.assertIsNotNone(self.dashboard_screen.market_overview_widget)
        print("시장 개요 위젯이 존재합니다.")
    
    def test_portfolio_summary_widget(self):
        """포트폴리오 요약 위젯 테스트"""
        print("\n=== 테스트: 포트폴리오 요약 위젯 ===")
        
        # 위젯 생성
        widget = PortfolioSummaryWidget()
        
        # 위젯이 생성되었는지 확인
        self.assertIsNotNone(widget)
        print("포트폴리오 요약 위젯이 생성되었습니다.")
        
        # 위젯의 ID가 올바르게 설정되었는지 확인
        self.assertEqual(widget.objectName(), "widget-portfolio-summary")
        print("위젯 ID가 올바르게 설정되었습니다: widget-portfolio-summary")
        
        # 위젯의 기본 데이터가 로드되었는지 확인
        self.assertTrue(hasattr(widget, 'refresh_data'))
        print("위젯에 데이터 새로고침 메서드가 존재합니다.")
        
        # 새로고침 메서드 테스트
        try:
            widget.refresh_data()
            print("데이터 새로고침 메서드가 오류 없이 실행됩니다.")
        except Exception as e:
            self.fail(f"새로고침 중 예외 발생: {e}")
    
    def test_active_positions_widget(self):
        """활성 거래 목록 위젯 테스트"""
        print("\n=== 테스트: 활성 거래 목록 위젯 ===")
        
        # 위젯 생성
        widget = ActivePositionsWidget()
        
        # 위젯이 생성되었는지 확인
        self.assertIsNotNone(widget)
        print("활성 거래 목록 위젯이 생성되었습니다.")
        
        # 위젯의 ID가 올바르게 설정되었는지 확인
        self.assertEqual(widget.objectName(), "widget-active-positions")
        print("위젯 ID가 올바르게 설정되었습니다: widget-active-positions")
        
        # 위젯의 테이블이 존재하는지 확인
        self.assertTrue(hasattr(widget, 'positions_table'))
        print("위젯에 거래 목록 테이블이 존재합니다.")
        
        # 위젯의 기본 데이터가 로드되었는지 확인
        self.assertTrue(hasattr(widget, 'refresh_data'))
        print("위젯에 데이터 새로고침 메서드가 존재합니다.")
        
        # 새로고침 메서드 테스트
        try:
            widget.refresh_data()
            print("데이터 새로고침 메서드가 오류 없이 실행됩니다.")
        except Exception as e:
            self.fail(f"새로고침 중 예외 발생: {e}")
    
    def test_market_overview_widget(self):
        """시장 개요 위젯 테스트"""
        print("\n=== 테스트: 시장 개요 위젯 ===")
        
        # 위젯 생성
        widget = MarketOverviewWidget()
        
        # 위젯이 생성되었는지 확인
        self.assertIsNotNone(widget)
        print("시장 개요 위젯이 생성되었습니다.")
        
        # 위젯의 ID가 올바르게 설정되었는지 확인
        self.assertEqual(widget.objectName(), "widget-market-overview")
        print("위젯 ID가 올바르게 설정되었습니다: widget-market-overview")
        
        # 위젯의 테이블이 존재하는지 확인
        self.assertTrue(hasattr(widget, 'market_table'))
        print("위젯에 시장 개요 테이블이 존재합니다.")
        
        # 위젯의 기본 데이터가 로드되었는지 확인
        self.assertTrue(hasattr(widget, 'refresh_data'))
        print("위젯에 데이터 새로고침 메서드가 존재합니다.")
        
        # 새로고침 메서드 테스트
        try:
            widget.refresh_data()
            print("데이터 새로고침 메서드가 오류 없이 실행됩니다.")
        except Exception as e:
            self.fail(f"새로고침 중 예외 발생: {e}")
    
    def test_dashboard_refresh(self):
        """대시보드 새로고침 테스트"""
        print("\n=== 테스트: 대시보드 새로고침 ===")
        
        # 대시보드 새로고침 메서드가 존재하는지 확인
        self.assertTrue(hasattr(self.dashboard_screen, 'refresh_all_widgets'))
        print("대시보드에 모든 위젯 새로고침 메서드가 존재합니다.")
        
        # 새로고침 메서드 호출
        try:
            self.dashboard_screen.refresh_all_widgets()
            print("모든 위젯 새로고침이 오류 없이 실행됩니다.")
        except Exception as e:
            self.fail(f"새로고침 중 예외 발생: {e}")
    
    def test_dashboard_layout(self):
        """대시보드 레이아웃 테스트"""
        print("\n=== 테스트: 대시보드 레이아웃 ===")
        
        # 레이아웃이 존재하는지 확인
        self.assertIsNotNone(self.dashboard_screen.layout())
        print("대시보드 레이아웃이 존재합니다.")
        
        # 위젯들이 레이아웃에 추가되었는지 확인
        layout = self.dashboard_screen.layout()
        self.assertGreater(layout.count(), 0)
        print(f"레이아웃에 {layout.count()}개의 아이템이 추가되었습니다.")
    
    def test_dashboard_responsiveness(self):
        """대시보드 반응성 테스트"""
        print("\n=== 테스트: 대시보드 반응성 ===")
        
        # 초기 크기 저장
        initial_size = self.dashboard_screen.size()
        print(f"초기 크기: {initial_size.width()}x{initial_size.height()}")
        
        # 크기 변경
        new_width = initial_size.width() + 100
        new_height = initial_size.height() + 100
        self.dashboard_screen.resize(new_width, new_height)
        
        # 변경된 크기 확인
        new_size = self.dashboard_screen.size()
        self.assertEqual(new_size.width(), new_width)
        self.assertEqual(new_size.height(), new_height)
        print(f"변경된 크기: {new_size.width()}x{new_size.height()}")
        
        # 레이아웃이 올바르게 조정되었는지 확인
        # (실제로는 시각적으로 확인해야 하지만, 자동화 테스트에서는 오류가 없는지만 확인)
        try:
            self.dashboard_screen.update()
            print("레이아웃이 새 크기에 맞게 조정되었습니다.")
        except Exception as e:
            self.fail(f"레이아웃 조정 중 예외 발생: {e}")
    
    def tearDown(self):
        """각 테스트 후에 실행"""
        # 메모리 정리
        self.dashboard_screen.close()
        self.dashboard_screen.deleteLater()


if __name__ == "__main__":
    unittest.main()