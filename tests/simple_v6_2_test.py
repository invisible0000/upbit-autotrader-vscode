#!/usr/bin/env python3
"""
WebSocket v6.2 리얼타임 스트림 시스템 간단 기능 테스트
"""

import asyncio
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.support.subscription_manager import SubscriptionManager
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.core.websocket_types import DataType, WebSocketType

async def test_realtime_streams():
    print("🚀 v6.2 리얼타임 스트림 시스템 테스트 시작")
    print("=" * 50)

    manager = SubscriptionManager()

    # 리얼타임 스트림 추가
    await manager.add_realtime_stream(WebSocketType.PUBLIC, DataType.TICKER, {'KRW-BTC', 'KRW-ETH'}, 'test_component')

    # 스냅샷 요청 추가
    await manager.add_snapshot_request(WebSocketType.PUBLIC, DataType.TICKER, {'KRW-ADA'})

    # 상태 확인
    streams = manager.get_realtime_streams(WebSocketType.PUBLIC)
    snapshots = manager.get_pending_snapshots(WebSocketType.PUBLIC)

    print('🎯 리얼타임 스트림:', streams)
    print('📸 스냅샷 요청:', snapshots)

    # 통합 메시지 생성
    unified = await manager.create_unified_subscription_message(WebSocketType.PUBLIC, DataType.TICKER)
    print('🔗 통합 메시지:', unified)

    # 복잡성 분석
    complexities = manager.analyze_stream_complexity()
    print('📈 복잡성 분석:', complexities)

    summary = manager.get_stream_summary()
    print('📊 최종 상태:', summary)

    print("=" * 50)
    print('✅ v6.2 리얼타임 스트림 시스템 기능 테스트 완료')

if __name__ == "__main__":
    asyncio.run(test_realtime_streams())
