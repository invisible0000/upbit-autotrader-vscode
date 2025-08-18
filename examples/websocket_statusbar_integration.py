"""
WebSocket 클라이언트와 상태바 연동 예제

이 예제는 웹소켓 클라이언트가 상태 서비스에 자신의 상태를
보고하는 방법을 보여줍니다.
"""

import asyncio
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
    UpbitWebSocketQuotationClient
)
from upbit_auto_trading.infrastructure.services.websocket_status_service import (
    websocket_status_service
)
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("WebSocketStatusIntegration")


class StatusBarIntegratedWebSocketClient:
    """
    상태바와 연동된 웹소켓 클라이언트

    기존 웹소켓 클라이언트를 래핑하여 상태 변경을
    상태 서비스에 자동으로 보고합니다.
    """

    def __init__(self, client_name: str = "quotation"):
        self.client_name = client_name
        self.client = UpbitWebSocketQuotationClient()
        self.logger = create_component_logger(f"WebSocketClient_{client_name}")

        # 상태 서비스에 등록
        websocket_status_service.register_client(
            client_name=self.client_name,
            status_callback=self._on_status_change
        )

        # 초기 상태를 미연결로 설정
        websocket_status_service.update_client_status(
            self.client_name,
            connected=False,
            error_message="초기화됨"
        )

        self.logger.info(f"상태바 연동 웹소켓 클라이언트 초기화: {client_name}")

    async def connect(self) -> bool:
        """연결 및 상태 업데이트"""
        try:
            success = await self.client.connect()

            if success:
                websocket_status_service.update_client_status(
                    self.client_name,
                    connected=True
                )
                self.logger.info(f"웹소켓 연결 성공: {self.client_name}")
            else:
                websocket_status_service.update_client_status(
                    self.client_name,
                    connected=False,
                    error_message="연결 실패"
                )
                self.logger.warning(f"웹소켓 연결 실패: {self.client_name}")

            return success

        except Exception as e:
            websocket_status_service.update_client_status(
                self.client_name,
                connected=False,
                error_message=str(e)
            )
            self.logger.error(f"웹소켓 연결 오류: {e}")
            return False

    async def disconnect(self) -> None:
        """연결 해제 및 상태 업데이트"""
        try:
            await self.client.disconnect()
            websocket_status_service.update_client_status(
                self.client_name,
                connected=False,
                error_message="정상 해제"
            )
            self.logger.info(f"웹소켓 연결 해제: {self.client_name}")

        except Exception as e:
            websocket_status_service.update_client_status(
                self.client_name,
                connected=False,
                error_message=f"해제 오류: {str(e)}"
            )
            self.logger.error(f"웹소켓 해제 오류: {e}")

    def _on_status_change(self, connected: bool):
        """상태 변경 콜백"""
        status_text = "연결됨" if connected else "연결 끊김"
        self.logger.debug(f"상태 변경 알림: {self.client_name} -> {status_text}")

    # 기존 클라이언트 메서드들을 위임
    async def subscribe_ticker(self, markets):
        """ticker 구독"""
        return await self.client.subscribe_ticker(markets)

    async def subscribe_trade(self, markets):
        """trade 구독"""
        return await self.client.subscribe_trade(markets)

    async def listen(self):
        """메시지 수신"""
        async for message in self.client.listen():
            yield message

    async def __aenter__(self):
        """async context manager 진입"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async context manager 종료"""
        await self.disconnect()


async def demo_statusbar_integration():
    """상태바 연동 데모"""
    logger.info("🚀 웹소켓 상태바 연동 데모 시작")

    # 웹소켓 클라이언트 생성 및 연동
    async with StatusBarIntegratedWebSocketClient("demo_quotation") as ws_client:
        # 잠시 대기하여 상태 변경 확인
        await asyncio.sleep(1)

        # 구독 테스트
        await ws_client.subscribe_ticker(["KRW-BTC"])
        logger.info("📊 BTC ticker 구독 완료")

        # 몇 개 메시지 수신
        message_count = 0
        async for message in ws_client.listen():
            logger.info(f"📨 메시지 수신: {message.market}")
            message_count += 1
            if message_count >= 3:
                break

    logger.info("✅ 웹소켓 상태바 연동 데모 완료")

    # 최종 상태 확인
    overall_status = websocket_status_service.get_overall_status()
    logger.info(f"📡 최종 웹소켓 상태: {'연결됨' if overall_status else '미연결'}")


if __name__ == "__main__":
    asyncio.run(demo_statusbar_integration())
