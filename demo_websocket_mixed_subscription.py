"""
업비트 WebSocket 섞인 일괄 요청 데모

🎯 목적:
- UpbitWebSocketPublicClient와 UpbitWebSocketSubscriptionManager 통합 시연
- 하나의 티켓으로 여러 데이터 타입 동시 구독 (ticker, trade, orderbook, candle)
- 실시간 메시지 처리 및 스트림 타입 분리 (SNAPSHOT/REALTIME)

🚀 핵심 특징:
- 티켓 효율성: 전통적 방식 4개 티켓 → 통합 방식 1개 티켓
- 스트림 타입 분리: SNAPSHOT(완료된 데이터) vs REALTIME(진행 중 업데이트)
- 안전한 연결 관리: 자동 재연결 및 정리
"""
import asyncio
from datetime import datetime
from typing import Optional

# 업비트 WebSocket 클라이언트 import
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_public_client import (
    UpbitWebSocketPublicClient,
    WebSocketDataType,
    StreamType
)
from upbit_auto_trading.infrastructure.logging import create_component_logger

# 로거 설정
logger = create_component_logger("WebSocketMixedDemo")


class WebSocketMixedSubscriptionDemo:
    """업비트 WebSocket 섞인 일괄 구독 데모 클래스"""

    def __init__(self):
        self.client: Optional[UpbitWebSocketPublicClient] = None
        self.message_counts = {
            'ticker': {'snapshot': 0, 'realtime': 0},
            'trade': {'snapshot': 0, 'realtime': 0},
            'orderbook': {'snapshot': 0, 'realtime': 0},
            'candle': {'snapshot': 0, 'realtime': 0}
        }
        self.start_time = datetime.now()

    async def run_demo(self, duration_seconds: int = 30):
        """
        데모 실행

        Args:
            duration_seconds: 실행 시간 (초)
        """
        logger.info("🚀 업비트 WebSocket 섞인 일괄 구독 데모 시작")

        try:
            # 1단계: WebSocket 클라이언트 초기화
            await self._initialize_client()

            # 2단계: 혼합 구독 설정 (하나의 티켓으로 모든 타입)
            await self._setup_mixed_subscriptions()

            # 3단계: 구독 정보 확인
            self._display_subscription_info()

            # 4단계: 메시지 수신 및 처리
            await self._monitor_messages(duration_seconds)

        except Exception as e:
            logger.error(f"❌ 데모 실행 중 오류: {e}")
        finally:
            await self._cleanup()

    async def _initialize_client(self):
        """WebSocket 클라이언트 초기화"""
        logger.info("📡 WebSocket 클라이언트 초기화 중...")

        self.client = UpbitWebSocketPublicClient(
            auto_reconnect=True,
            persistent_connection=False,  # 데모용이므로 지속 연결 비활성화
            auto_start_message_loop=True
        )

        # 메시지 핸들러 등록
        self._register_message_handlers()

        # 연결
        success = await self.client.connect()
        if not success:
            raise ConnectionError("WebSocket 연결 실패")

        logger.info("✅ WebSocket 연결 성공")

    def _register_message_handlers(self):
        """메시지 핸들러 등록"""
        if not self.client:
            return

        # 각 데이터 타입별 핸들러 등록
        self.client.add_message_handler(WebSocketDataType.TICKER, self._handle_ticker_message)
        self.client.add_message_handler(WebSocketDataType.TRADE, self._handle_trade_message)
        self.client.add_message_handler(WebSocketDataType.ORDERBOOK, self._handle_orderbook_message)
        self.client.add_message_handler(WebSocketDataType.CANDLE, self._handle_candle_message)

    async def _setup_mixed_subscriptions(self):
        """혼합 구독 설정 - 진정한 일괄 요청 (하나의 메시지에 모든 타입 포함)"""
        logger.info("📊 섞인 일괄 구독 설정 중...")

        if not self.client:
            raise RuntimeError("WebSocket 클라이언트가 초기화되지 않음")

        # 테스트할 심볼들
        symbols = ["KRW-BTC", "KRW-ETH"]

        # 🎯 진정한 일괄 구독: 하나의 메시지에 모든 타입 포함
        success = await self._send_single_mixed_subscription_message(symbols)

        if success:
            logger.info("✅ 섞인 일괄 구독 설정 완료 (1개 메시지로 4개 타입 동시 구독)")
        else:
            logger.error("❌ 섞인 일괄 구독 설정 실패")

        # 1초 대기 (구독 안정화)
        await asyncio.sleep(1)

    async def _send_single_mixed_subscription_message(self, symbols: list[str]) -> bool:
        """
        하나의 WebSocket 메시지로 모든 타입 동시 구독

        업비트 WebSocket 프로토콜:
        [
            {"ticket": "unique_id"},
            {"type": "ticker", "codes": ["KRW-BTC", "KRW-ETH"]},
            {"type": "trade", "codes": ["KRW-BTC", "KRW-ETH"]},
            {"type": "orderbook", "codes": ["KRW-BTC", "KRW-ETH"]},
            {"type": "candle.5m", "codes": ["KRW-BTC", "KRW-ETH"], "isOnlySnapshot": true},
            {"format": "DEFAULT"}
        ]
        """
        if not self.client or not self.client.websocket or not self.client.is_connected:
            logger.error("❌ WebSocket 연결이 준비되지 않음")
            return False

        try:
            import json
            import uuid

            # 고유 티켓 생성
            ticket_id = f"mixed-demo-{uuid.uuid4().hex[:8]}"

            # � 하나의 메시지에 모든 구독 타입 포함
            mixed_message = [
                # 1. 티켓 정보
                {"ticket": ticket_id},

                # 2. 현재가 구독
                {"type": "ticker", "codes": symbols},

                # 3. 체결 구독
                {"type": "trade", "codes": symbols},

                # 4. 호가 구독
                {"type": "orderbook", "codes": symbols},

                # 5. 캔들 구독 (5분봉, SNAPSHOT만)
                {"type": "candle.5m", "codes": symbols, "isOnlySnapshot": True},

                # 6. 포맷 설정
                {"format": "DEFAULT"}
            ]

            # JSON 직렬화 및 전송
            message_json = json.dumps(mixed_message)
            await self.client.websocket.send(message_json)

            # 구독 관리자에 정보 등록 (테스트 호환성)
            if hasattr(self.client, 'subscription_manager'):
                for data_type in ['ticker', 'trade', 'orderbook', 'candle.5m']:
                    if hasattr(self.client.subscription_manager, '_subscription_manager'):
                        if data_type == 'candle.5m':
                            self.client.subscription_manager._subscription_manager.add_subscription(
                                'candle', symbols, unit="5m", isOnlySnapshot=True
                            )
                        else:
                            self.client.subscription_manager._subscription_manager.add_subscription(
                                data_type, symbols
                            )

            logger.info("📡 일괄 구독 메시지 전송 완료:")
            logger.info(f"   🎫 티켓: {ticket_id}")
            logger.info("   📊 타입: ticker, trade, orderbook, candle.5m")
            logger.info(f"   🏷️ 심볼: {', '.join(symbols)}")
            logger.info(f"   📝 메시지 크기: {len(message_json)} 바이트")

            return True

        except Exception as e:
            logger.error(f"❌ 일괄 구독 메시지 전송 실패: {e}")
            return False

    def _display_subscription_info(self):
        """구독 정보 표시"""
        if not self.client:
            logger.warning("⚠️ 클라이언트가 초기화되지 않음")
            return

        logger.info("📋 구독 정보 요약:")

        # 구독 통계
        subscription_stats = self.client.get_subscription_stats()
        logger.info(f"   🎫 총 티켓 수: {subscription_stats.get('total_tickets', 0)}개")
        logger.info(f"   📊 효율성: {subscription_stats.get('reuse_efficiency', 0):.1f}%")

        # 활성 구독 상세
        active_subs = self.client.get_active_subscriptions()
        for data_type, sub_info in active_subs.items():
            symbols = sub_info.get('symbols', [])
            logger.info(f"   📡 {data_type}: {len(symbols)}개 심볼 ({', '.join(symbols)})")

    async def _monitor_messages(self, duration_seconds: int):
        """메시지 모니터링"""
        logger.info(f"👂 {duration_seconds}초간 메시지 수신 모니터링 시작...")

        # 주기적 통계 출력을 위한 태스크
        stats_task = asyncio.create_task(self._periodic_stats_display())

        try:
            await asyncio.sleep(duration_seconds)
        finally:
            stats_task.cancel()
            try:
                await stats_task
            except asyncio.CancelledError:
                pass

        # 최종 통계 출력
        self._display_final_stats()

    async def _periodic_stats_display(self):
        """주기적 통계 표시 (5초마다)"""
        while True:
            try:
                await asyncio.sleep(5)
                self._display_current_stats()
            except asyncio.CancelledError:
                break

    def _display_current_stats(self):
        """현재 통계 표시"""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        # 전체 메시지 수 계산
        total_messages = sum(
            sum(counts.values()) for counts in self.message_counts.values()
        )

        # 스트림 타입별 총합
        total_snapshot = sum(counts['snapshot'] for counts in self.message_counts.values())
        total_realtime = sum(counts['realtime'] for counts in self.message_counts.values())

        logger.info(f"📊 [{elapsed:.0f}초] 메시지 수신 현황: "
                    f"총 {total_messages}개 (SNAPSHOT: {total_snapshot}, REALTIME: {total_realtime})")

    def _display_final_stats(self):
        """최종 통계 표시"""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        logger.info("📈 최종 메시지 수신 통계:")
        logger.info(f"   ⏱️ 총 실행 시간: {elapsed:.1f}초")

        for data_type, counts in self.message_counts.items():
            total = sum(counts.values())
            snapshot = counts['snapshot']
            realtime = counts['realtime']

            if total > 0:
                logger.info(f"   📡 {data_type.upper()}: {total}개 "
                            f"(SNAPSHOT: {snapshot}, REALTIME: {realtime})")

    # ================================================================
    # 메시지 핸들러들
    # ================================================================

    async def _handle_ticker_message(self, message):
        """Ticker 메시지 처리"""
        stream_type = self._get_stream_type(message)
        self.message_counts['ticker'][stream_type] += 1

        # 첫 번째 메시지만 상세 로그
        if sum(self.message_counts['ticker'].values()) <= 3:
            market = message.market if hasattr(message, 'market') else message.get('market', 'UNKNOWN')
            price = message.data.get('trade_price', 0) if hasattr(message, 'data') else message.get('trade_price', 0)
            logger.info(f"📈 [TICKER-{stream_type}] {market}: {price:,}원")

    async def _handle_trade_message(self, message):
        """Trade 메시지 처리"""
        stream_type = self._get_stream_type(message)
        self.message_counts['trade'][stream_type] += 1

        # 첫 번째 메시지만 상세 로그
        if sum(self.message_counts['trade'].values()) <= 3:
            market = message.market if hasattr(message, 'market') else message.get('market', 'UNKNOWN')
            price = message.data.get('trade_price', 0) if hasattr(message, 'data') else message.get('trade_price', 0)
            volume = message.data.get('trade_volume', 0) if hasattr(message, 'data') else message.get('trade_volume', 0)
            logger.info(f"💱 [TRADE-{stream_type}] {market}: {price:,}원 × {volume}")

    async def _handle_orderbook_message(self, message):
        """Orderbook 메시지 처리"""
        stream_type = self._get_stream_type(message)
        self.message_counts['orderbook'][stream_type] += 1

        # 첫 번째 메시지만 상세 로그
        if sum(self.message_counts['orderbook'].values()) <= 3:
            market = message.market if hasattr(message, 'market') else message.get('market', 'UNKNOWN')
            logger.info(f"📋 [ORDERBOOK-{stream_type}] {market}: 호가 업데이트")

    async def _handle_candle_message(self, message):
        """Candle 메시지 처리"""
        stream_type = self._get_stream_type(message)
        self.message_counts['candle'][stream_type] += 1

        # 모든 캔들 메시지 로그 (빈도가 낮으므로)
        market = message.market if hasattr(message, 'market') else message.get('market', 'UNKNOWN')
        if hasattr(message, 'data'):
            open_price = message.data.get('opening_price', 0)
            close_price = message.data.get('trade_price', 0)
        else:
            open_price = message.get('opening_price', 0)
            close_price = message.get('trade_price', 0)

        logger.info(f"🕯️ [CANDLE-{stream_type}] {market}: "
                    f"시가 {open_price:,}원 → 종가 {close_price:,}원")

    def _get_stream_type(self, message) -> str:
        """메시지에서 스트림 타입 추출"""
        if hasattr(message, 'stream_type'):
            if message.stream_type == StreamType.SNAPSHOT:
                return 'snapshot'
            elif message.stream_type == StreamType.REALTIME:
                return 'realtime'

        # dict 형태의 메시지인 경우
        if isinstance(message, dict):
            stream_type_value = message.get('stream_type', '').upper()
            if stream_type_value == 'SNAPSHOT':
                return 'snapshot'
            elif stream_type_value == 'REALTIME':
                return 'realtime'

        # 기본값 (스트림 타입 정보가 없는 경우)
        return 'realtime'

    async def _cleanup(self):
        """정리 작업"""
        if self.client:
            logger.info("🧹 WebSocket 연결 정리 중...")
            await self.client.disconnect()
            logger.info("✅ 정리 완료")


async def main():
    """메인 함수"""
    print("=" * 60)
    print("🚀 업비트 WebSocket 섞인 일괄 구독 데모")
    print("=" * 60)

    demo = WebSocketMixedSubscriptionDemo()

    try:
        # 30초간 데모 실행
        await demo.run_demo(duration_seconds=30)

    except KeyboardInterrupt:
        logger.info("⏹️ 사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"❌ 데모 실행 중 오류: {e}")

    print("=" * 60)
    print("✅ 데모 완료")
    print("=" * 60)


if __name__ == "__main__":
    # 환경변수 설정 (상세 로깅)
    import os
    os.environ["UPBIT_CONSOLE_OUTPUT"] = "true"
    os.environ["UPBIT_LOG_SCOPE"] = "verbose"

    # 데모 실행
    asyncio.run(main())
