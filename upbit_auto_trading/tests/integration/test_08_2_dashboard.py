"""
대시보드 화면 통합 테스트 모듈

이 모듈은 대시보드 화면의 기능을 테스트합니다.
"""
import unittest
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

# 테스트할 클래스 임포트
from upbit_auto_trading.ui.desktop.screens.dashboard.dashboard_screen import DashboardScreen
from upbit_auto_trading.ui.desktop.screens.dashboard.widgets.portfolio_summary_widget import PortfolioSummaryWidget
from upbit_auto_trading.ui.desktop.screens.dashboard.widgets.active_positions_widget import ActivePositionsWidget
from upbit_auto_trading.ui.desktop.screens.dashboard.widgets.market_overview_widget import MarketOverviewWidget


class TestDashboard(unittest.TestCase):
    """대시보드 화면 테스트 클래스"""
    
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
        print("\n=== 테스트 ID 08_2_1: test_dashboard_screen_creation ===")
        self.dashboard_screen = DashboardScreen()
    
    def test_dashboard_screen_creation(self):
        """대시보드 화면 생성 테스트"""
        # 대시보드 화면이 생성되었는지 확인
        self.assertIsNotNone(self.dashboard_screen)
        print("대시보드 화면이 성공적으로 생성되었습니다.")
        
        # 필요한 위젯들이 포함되어 있는지 확인
        self.assertIsNotNone(self.dashboard_screen.portfolio_summary_widget)
        print("포트폴리오 요약 위젯이 존재합니다.")
        
        self.assertIsNotNone(self.dashboard_screen.active_positions_widget)
        print("활성 거래 목록 위젯이 존재합니다.")
        
        self.assertIsNotNone(self.dashboard_screen.market_overview_widget)
        print("시장 개요 위젯이 존재합니다.")
    
    def test_portfolio_summary_widget(self):
        """포트폴리오 요약 위젯 테스트"""
        print("\n=== 테스트 ID 08_2_2: test_portfolio_summary_widget ===")
        
        # 위젯 생성
        widget = PortfolioSummaryWidget()
        
        # 위젯이 생성되었는지 확인
        self.assertIsNotNone(widget)
        print("포트폴리오 요약 위젯이 성공적으로 생성되었습니다.")
        
        # 위젯의 ID가 올바르게 설정되었는지 확인
        self.assertEqual(widget.objectName(), "widget-portfolio-summary")
        print("위젯 ID가 올바르게 설정되었습니다: widget-portfolio-summary")
        
        # 위젯의 기본 데이터가 로드되었는지 확인
        self.assertTrue(hasattr(widget, 'refresh_data'))
        print("위젯에 데이터 새로고침 메서드가 존재합니다.")
    
    def test_active_positions_widget(self):
        """활성 거래 목록 위젯 테스트"""
        print("\n=== 테스트 ID 08_2_3: test_active_positions_widget ===")
        
        # 위젯 생성
        widget = ActivePositionsWidget()
        
        # 위젯이 생성되었는지 확인
        self.assertIsNotNone(widget)
        print("활성 거래 목록 위젯이 성공적으로 생성되었습니다.")
        
        # 위젯의 ID가 올바르게 설정되었는지 확인
        self.assertEqual(widget.objectName(), "widget-active-positions")
        print("위젯 ID가 올바르게 설정되었습니다: widget-active-positions")
        
        # 위젯의 테이블이 존재하는지 확인
        self.assertTrue(hasattr(widget, 'positions_table'))
        print("위젯에 거래 목록 테이블이 존재합니다.")
        
        # 위젯의 기본 데이터가 로드되었는지 확인
        self.assertTrue(hasattr(widget, 'refresh_data'))
        print("위젯에 데이터 새로고침 메서드가 존재합니다.")
    
    def test_market_overview_widget(self):
        """시장 개요 위젯 테스트"""
        print("\n=== 테스트 ID 08_2_4: test_market_overview_widget ===")
        
        # 위젯 생성
        widget = MarketOverviewWidget()
        
        # 위젯이 생성되었는지 확인
        self.assertIsNotNone(widget)
        print("시장 개요 위젯이 성공적으로 생성되었습니다.")
        
        # 위젯의 ID가 올바르게 설정되었는지 확인
        self.assertEqual(widget.objectName(), "widget-market-overview")
        print("위젯 ID가 올바르게 설정되었습니다: widget-market-overview")
        
        # 위젯의 테이블이 존재하는지 확인
        self.assertTrue(hasattr(widget, 'market_table'))
        print("위젯에 시장 개요 테이블이 존재합니다.")
        
        # 위젯의 기본 데이터가 로드되었는지 확인
        self.assertTrue(hasattr(widget, 'refresh_data'))
        print("위젯에 데이터 새로고침 메서드가 존재합니다.")
    
    def test_dashboard_refresh(self):
        """대시보드 새로고침 테스트"""
        print("\n=== 테스트 ID 08_2_5: test_dashboard_refresh ===")
        
        # 대시보드 새로고침 메서드가 존재하는지 확인
        self.assertTrue(hasattr(self.dashboard_screen, 'refresh_all_widgets'))
        print("대시보드에 모든 위젯 새로고침 메서드가 존재합니다.")
        
        # 새로고침 메서드 호출
        try:
            self.dashboard_screen.refresh_all_widgets()
            print("모든 위젯 새로고침이 성공적으로 실행되었습니다.")
        except Exception as e:
            self.fail(f"새로고침 중 예외 발생: {e}")
    
    def tearDown(self):
        """각 테스트 후에 실행"""
        # 메모리 정리
        if hasattr(self, 'dashboard_screen'):
            self.dashboard_screen.deleteLater()


if __name__ == "__main__":
    unittest.main()