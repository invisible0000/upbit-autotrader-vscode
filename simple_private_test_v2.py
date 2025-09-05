"""
간단한 Private WebSocket 테스트 v2
=================================

정식 WebSocket 애플리케이션 서비스를 사용한 내 자산/주문 구독 테스트
run_desktop_ui.py와 동일한 방식으로 서비스 시작/종료
"""

import asyncio
import json
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.services.websocket_application_service import WebSocketApplicationService
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.core.websocket_client import (
    WebSocketClient
)

logger = create_component_logger("SimplePrivateTestV2")


async def simple_private_test_v2():
    """정식 WebSocket 애플리케이션 서비스를 사용한 Private 구독 테스트"""

    received_events = []
    websocket_service = None
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
        logger.info("🚀 정식 WebSocket 애플리케이션 서비스를 사용한 Private 테스트 시작")

        # 1. WebSocket 애플리케이션 서비스 초기화 및 시작 (run_desktop_ui.py와 동일)
        websocket_service = WebSocketApplicationService()

        # 먼저 초기화
        init_success = await websocket_service.initialize()
        if not init_success:
            logger.error("❌ WebSocket 애플리케이션 서비스 초기화 실패")
            return False
        logger.info("✅ WebSocket 애플리케이션 서비스 초기화 완료")

        # 그다음 시작
        start_success = await websocket_service.start()
        if not start_success:
            logger.error("❌ WebSocket 애플리케이션 서비스 시작 실패")
            return False
        logger.info("✅ WebSocket 애플리케이션 서비스 시작 완료")

        # 2. Private 클라이언트 생성
        client = WebSocketClient("simple_private_test_v2")

        # 3. Private 구독 (내 자산 + 내 주문)
        await client.subscribe_my_asset(callback=private_callback)
        logger.info("✅ 내 자산 구독 등록 완료")

        await client.subscribe_my_order(callback=private_callback)
        logger.info("✅ 내 주문 구독 등록 완료")

        # 4. 잠시 대기하여 구독 처리 완료
        await asyncio.sleep(2.0)
        logger.info("✅ 구독 처리 완료")

        # 5. 구독 상태 확인 (서비스를 통한 조회)
        try:
            service_status = await websocket_service.get_service_status()
            logger.info("📊 WebSocket 서비스 상태:")
            logger.info(f"   ├─ 활성 연결: {service_status.get('active_connections', 'N/A')}")
            logger.info(f"   ├─ 구독 수: {service_status.get('total_subscriptions', 'N/A')}")
            logger.info(f"   └─ 서비스 상태: {service_status.get('status', 'N/A')}")
        except Exception as e:
            logger.warning(f"⚠️ 서비스 상태 조회 실패: {e}")

        # 6. 응답 대기
        logger.info("⏱️  Private 응답 대기 중 (10초)...")
        await asyncio.sleep(10.0)

        # 7. 결과 출력
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

        return len(received_events) > 0

    except Exception as e:
        logger.error(f"💥 테스트 실패: {e}")
        import traceback
        logger.error(f"스택 트레이스:\n{traceback.format_exc()}")
        return False

    finally:
        # 9. 깔끔한 정리 (Event 기반 graceful shutdown)
        logger.info("🧹 깔끔한 서비스 정리 시작...")

        try:
            if client:
                logger.info("🔍 client.cleanup() 호출")
                await client.cleanup()
                logger.info("✅ WebSocket 클라이언트 정리 완료")
        except Exception as e:
            logger.warning(f"⚠️ 클라이언트 정리 중 오류: {e}")

        try:
            if websocket_service:
                logger.info("🔍 websocket_service.stop() 호출")
                await websocket_service.stop()
                logger.info("✅ WebSocket 애플리케이션 서비스 정리 완료")
        except Exception as e:
            logger.error(f"💥 서비스 정리 중 예외 발생: {e}")
            import traceback
            logger.error(f"스택 트레이스:\n{traceback.format_exc()}")

        logger.info("✅ 깔끔한 정리 완료 - 프로세스 종료 준비")
if __name__ == "__main__":
    # 환경변수 설정
    import os
    os.environ['UPBIT_CONSOLE_OUTPUT'] = 'true'
    os.environ['UPBIT_LOG_SCOPE'] = 'verbose'

    # 테스트 실행
    result = asyncio.run(simple_private_test_v2())

    if result:
        print("🎉 Private WebSocket 응답 수신 성공!")
    else:
        print("📭 응답 없음 - 하지만 정상적인 상황일 수 있습니다")
        print("💡 빈 계정이거나 자산/주문 변화가 없을 때는 응답이 없을 수 있습니다")
        print("💡 Private WebSocket은 실시간 변화만 알림 (초기 스냅샷 없음)")
