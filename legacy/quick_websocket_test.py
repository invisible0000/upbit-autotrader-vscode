"""
간단한 WebSocket ping 테스트
"""
import asyncio
import websockets
import json

async def quick_test():
    print("빠른 WebSocket 테스트...")

    try:
        websocket = await websockets.connect("wss://api.upbit.com/websocket/v1")
        print("연결 완료!")

        # PING 전송 테스트
        await websocket.send("PING")
        print("PING 전송 완료")

        # 3초 동안 메시지 수신
        try:
            for i in range(3):
                message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"메시지 {i+1}: {message}")
        except asyncio.TimeoutError:
            print("타임아웃")

        await websocket.close()
        print("연결 종료")

    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())
