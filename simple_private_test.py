"""
간단한 Private WebSocket 테스트
===========================

정식 WebSocket 애플리케이션 서비스를 사용한 내 자산/주문 구독 테스트
"""

import asyncio
import json
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.services.websocket_application_service import WebSocketApplicationService
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.core.websocket_client import (
    WebSocketClient
)

logger = create_component_logger("SimplePrivateTest")


async def simple_private_test():
    """간단한 Private 구독 테스트"""

    received_events = []
    manager = None
    client = None

    def private_callback(event):
        """Private 이벤트 수신 콜백"""
        event_type = event.get('type', 'unknown')
        stream_type = event.get('stream_type', 'UNKNOWN')

        received_events.append(event)

        logger.info("🎉 Private 이벤트 수신!")
        logger.info(f"   ├─ 타입: {event_type}")
        logger.info(f"   ├─ 스트림: {stream_type}")
        logger.info(f"   └─ 내용: {json.dumps(event, ensure_ascii=False)[:200]}...")

    try:
        logger.info("🚀 간단한 Private WebSocket 테스트 시작")

        # 1. WebSocket 매니저 초기화
        manager = await get_websocket_manager()
        await manager.start()
        logger.info("✅ WebSocket 매니저 시작 완료")

        # 2. Private 클라이언트 생성
        client = WebSocketClient("simple_private_test")

        # 3. Private 구독 (내 자산 + 내 주문)
        await client.subscribe_my_asset(callback=private_callback)
        logger.info("✅ 내 자산 구독 등록 완료")

        await client.subscribe_my_order(callback=private_callback)
        logger.info("✅ 내 주문 구독 등록 완료")

        # 4. 구독 메시지 강제 전송
        await manager._send_latest_subscriptions()
        logger.info("✅ 구독 메시지 전송 완료")

        # 5. 구독 상태 확인
        if manager._subscription_manager:
            private_streams = manager._subscription_manager.get_realtime_streams(WebSocketType.PRIVATE)
            logger.info("📊 현재 Private 구독 상태:")
            for data_type, symbols in private_streams.items():
                logger.info(f"   ├─ {data_type.value}: {len(symbols)}개 심볼")
        else:
            logger.warning("⚠️  구독 매니저 없음")

        # 6. 연결 상태 확인
        connection_state = manager._connection_states.get(WebSocketType.PRIVATE)
        logger.info(f"🔗 Private 연결 상태: {connection_state}")

        # 7. 응답 대기
        logger.info("⏱️  Private 응답 대기 중 (10초)...")
        await asyncio.sleep(10.0)

        # 8. 결과 출력
        logger.info("📊 테스트 결과:")
        logger.info(f"   ├─ 수신된 이벤트: {len(received_events)}개")

        if received_events:
            logger.info("🎉 Private WebSocket 응답 수신 성공!")
            for i, event in enumerate(received_events):
                logger.info(f"   이벤트 {i + 1}: {event.get('type', 'unknown')}")
        else:
            logger.info("📭 Private WebSocket 응답 없음")
            logger.info("💡 가능한 원인:")
            logger.info("   ├─ 계정에 자산이 없음")
            logger.info("   ├─ 계정에 주문이 없음")
            logger.info("   ├─ 테스트 계정이라 거래 내역 없음")
            logger.info("   ├─ 자산/주문 변화가 없어서 REALTIME 이벤트 없음")
            logger.info("   └─ 이는 정상적인 상황일 수 있습니다")

        # 9. 강력한 정리 (모든 백그라운드 태스크 종료)
        logger.info("🧹 강력한 정리 시작...")

        try:
            # 클라이언트 정리
            await client.cleanup()
            logger.info("✅ 클라이언트 정리 완료")

            # WebSocket 매니저 정리
            await manager.stop()
            logger.info("✅ WebSocket 매니저 정리 완료")

            # 추가: 모든 asyncio 태스크 강제 종료
            current_task = asyncio.current_task()
            all_tasks = [task for task in asyncio.all_tasks() if task != current_task]

            if all_tasks:
                logger.info(f"🔄 {len(all_tasks)}개 백그라운드 태스크 강제 종료 중...")
                for task in all_tasks:
                    if not task.done():
                        task.cancel()

                # 최대 3초 대기
                try:
                    await asyncio.wait_for(asyncio.gather(*all_tasks, return_exceptions=True), timeout=3.0)
                    logger.info("✅ 모든 백그라운드 태스크 정리 완료")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ 일부 태스크 정리 타임아웃 (3초)")

        except Exception as cleanup_error:
            logger.error(f"⚠️ 정리 중 오류: {cleanup_error}")

        logger.info("✅ 강력한 정리 완료")

        return len(received_events) > 0

    except Exception as e:
        logger.error(f"💥 테스트 실패: {e}")
        import traceback
        logger.error(f"스택 트레이스:\n{traceback.format_exc()}")

        # 실패 시에도 정리 시도
        try:
            if client is not None:
                await client.cleanup()
            if manager is not None:
                await manager.stop()
            logger.info("✅ 예외 상황 정리 완료")
        except Exception as cleanup_error:
            logger.warning(f"⚠️ 예외 상황 정리 실패: {cleanup_error}")

        return False

if __name__ == "__main__":
    # 환경변수 설정
    import os
    os.environ['UPBIT_CONSOLE_OUTPUT'] = 'true'
    os.environ['UPBIT_LOG_SCOPE'] = 'verbose'

    # 테스트 실행
    result = asyncio.run(simple_private_test())

    if result:
        print("🎉 Private WebSocket 응답 수신 성공!")
    else:
        print("📭 응답 없음 - 하지만 정상적인 상황일 수 있습니다")
        print("💡 빈 계정이거나 자산/주문 변화가 없을 때는 응답이 없을 수 있습니다")
        print("💡 Private WebSocket은 실시간 변화만 알림 (초기 스냅샷 없음)")
