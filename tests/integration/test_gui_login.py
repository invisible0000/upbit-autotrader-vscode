#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GUI 설정 화면에서 API키 입력 후 로그인 동작 테스트 (통합)
"""
import unittest
from unittest.mock import patch
from upbit_auto_trading.ui.desktop.main import MainWindow

class TestGuiLogin(unittest.TestCase):
    def setUp(self):
        print("GUI 로그인 테스트 시작...")
        self.window = MainWindow()

    @patch('upbit_auto_trading.business_logic.trader.trading_settings.TradingSettings.validate_api_key')
    def test_api_key_login(self, mock_validate):
        """API키 입력 후 로그인 버튼 클릭 시 정상 동작 및 결과 출력"""
        mock_validate.return_value = True
        # API키 입력 시뮬레이션
        # settings_widget이 MainWindow에 없을 경우, 올바른 경로로 접근하거나 생성 필요
        # 예시: 만약 settings_widget이 main_window.centralWidget() 내부에 있다면
        # self.window.centralWidget().api_key_input.setText("test-api-key")
        # 또는 settings_widget을 직접 생성해야 할 수도 있음

        # 현재 코드가 정상 동작하지 않는다면 아래와 같이 수정해보세요:
        # settings_widget이 MainWindow의 속성으로 존재하는지 확인
        if hasattr(self.window, "settings_widget"):
            self.window.settings_widget.api_key_input.setText("test-api-key")
        else:
            # settings_widget이 없다면, centralWidget에서 찾거나 직접 생성
            try:
            settings_widget = self.window.centralWidget()
            settings_widget.api_key_input.setText("test-api-key")
            except AttributeError:
            raise AttributeError("MainWindow에 settings_widget 또는 centralWidget이 없습니다. 올바른 경로를 확인하세요.")
        # 로그인 버튼 클릭 시뮬레이션
        self.window.settings_widget.login_button.click()
        # 로그인 성공 메시지 확인
        result = self.window.settings_widget.status_label.text()
        print(f"로그인 결과: {result}")
        self.assertIn("성공", result)

    def tearDown(self):
        print("GUI 로그인 테스트 종료.")

if __name__ == '__main__':
    unittest.main()
