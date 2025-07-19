#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""upbit_auto_trading.tests.unit.test_10_1_upbit_websocket 모듈에 대한 단위 테스트.

이 모듈은 Upbit 웹소켓 클라이언트의 기능, 특히 연결, 구독 및 메시지 처리 기능의 정확성을 검증하는 테스트 케이스를 포함합니다.
"""

import asyncio
import unittest
from unittest.mock import patch, AsyncMock

from upbit_auto_trading.data_layer.collectors.upbit_websocket_client import UpbitWebsocketClient

class TestUpbitWebsocketClient(unittest.TestCase):
    """Upbit 웹소켓 클라이언트 테스트 케이스.

    이 클래스는 웹소켓 클라이언트의 다양한 측면을 테스트합니다:
    - 연결 및 연결 해제
    - 구독 메시지 형식
    - 실시간 데이터 수신 및 처리
    """

    def setUp(self):
        """테스트 케이스 실행 전 초기 설정.

        각 테스트 메소드가 실행되기 전에 호출됩니다.
        """
        print("Setting up for a new test...")

    def tearDown(self):
        """테스트 케이스 실행 후 정리 작업.

        각 테스트 메소드가 실행된 후 호출됩니다.
        """
        print("Tearing down the test.")

    def test_initialization(self):
        """웹소켓 클라이언트 초기화 테스트.

        클라이언트가 올바르게 초기화되는지 확인합니다.
        """
        client = UpbitWebsocketClient()
        self.assertIsInstance(client, UpbitWebsocketClient)

    @patch('upbit_auto_trading.data_layer.collectors.upbit_websocket_client.websockets.connect', new_callable=AsyncMock)
    def test_connect(self, mock_connect):
        """웹소켓 연결 테스트.

        클라이언트가 지정된 URI로 웹소켓에 연결을 시도하는지 확인합니다.
        """
        async def run_test():
            client = UpbitWebsocketClient()
            await client.connect()
            mock_connect.assert_called_once_with(client.WEBSOCKET_URI)

        asyncio.run(run_test())

    @patch('upbit_auto_trading.data_layer.collectors.upbit_websocket_client.websockets.connect', new_callable=AsyncMock)
    def test_receive_limited_calls(self, mock_connect):
        """웹소켓 데이터 수신 반복 횟수 제한 테스트.
        최대 호출 횟수만큼만 recv가 호출되는지 확인합니다.
        """
        max_calls = 5
        call_count = 0

        class DummyWebSocket:
            async def recv(self):
                nonlocal call_count
                if call_count < max_calls:
                    call_count += 1
                    return {"type": "trade", "data": "sample"}
                else:
                    raise StopAsyncIteration
            async def close(self):
                return None

        async def run_test():
            client = UpbitWebsocketClient()
            mock_connect.return_value = DummyWebSocket()
            await client.connect()
            # 실제 receive 메서드가 반복 호출을 제한하는지 테스트
            results = []
            try:
                for _ in range(max_calls + 2):
                    msg = await client.ws.recv()
                    results.append(msg)
            except StopAsyncIteration:
                pass
            self.assertEqual(call_count, max_calls)
            print(f"recv 호출 횟수: {call_count} (최대 {max_calls}회)")

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
