#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""upbit_auto_trading.data_layer.collectors.upbit_websocket_client 모듈.

이 모듈은 Upbit 거래소의 웹소켓 API와 상호작용하여 실시간 시장 데이터를 수신하는 클라이언트를 포함합니다.
"""

import asyncio
import websockets

class UpbitWebsocketClient:
    """Upbit 웹소켓 API와 통신하여 실시간 데이터를 수신하는 클라이언트.

    이 클래스는 웹소켓 연결, 구독 요청 및 데이터 스트림 처리를 관리합니다.
    """
    WEBSOCKET_URI = "wss://api.upbit.com/websocket/v1"

    def __init__(self):
        """UpbitWebsocketClient의 새 인스턴스를 초기화합니다."""
        self.websocket = None
        self.ws = None  # 테스트 호환용 속성 추가
        print("UpbitWebsocketClient initialized.")

    async def connect(self):
        """Upbit 웹소켓 서버에 연결합니다."""
        self.websocket = await websockets.connect(self.WEBSOCKET_URI)
        self.ws = self.websocket  # 테스트에서 사용하는 ws 속성에 할당
        print("Connected to Upbit websocket.")

