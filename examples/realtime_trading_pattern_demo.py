"""
실시간 거래를 위한 WebSocket 활용 패턴 데모

🎯 핵심 전략:
1. 연결은 유지하되 스냅샷/실시간 구분 처리
2. 실시간 데이터만으로 거래 결정
3. 스냅샷은 초기 상태 파악용
4. 효율적인        # 주기적 통계 로그 (100개마다)
        if self.message_count % 100 == 0:
            logger.info(f"📊 처리 통계: {self.message_count}개 메시지 수신, "
                        f"관심 심볼 {len(self.target_symbols)}개, "
                        f"활성 심볼 {len(self.initialized_symbols)}개")분리

⚠️ 중요한 사실: WebSocket 지속적 데이터 스트림
- 한번 구독하면 연결 종료까지 지속적 전송
- 우리가 원치 않아도 데이터는 계속 들어옴
- 효율적 필터링이 성능의 핵심
- 메모리/CPU 사용량 관리 필수

🔧 효율성 최적화:
1. 관심 심벌만 선별적 구독
2. 의미있는 변동만 처리 (임계값 설정)
3. 즉시 처리 후 메모리 해제
4. 주기적 통계 모니터링
"""

import asyncio
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_public_client import (
    UpbitWebSocketPublicClient, WebSocketDataType, WebSocketMessage
)
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("RealtimeTradingDemo")


class RealtimeTradingStrategy:
    """실시간 거래 전략 예시 - 효율적 스트림 관리"""

    def __init__(self):
        self.client = UpbitWebSocketPublicClient()
        self.current_prices = {}  # 현재 가격 저장
        self.initialized_symbols = set()  # 스냅샷 받은 심벌들

        # 효율성을 위한 필터링 설정
        self.target_symbols = {"KRW-BTC", "KRW-ETH", "KRW-XRP"}  # 관심 심벌만
        self.min_change_threshold = 0.1  # 0.1% 이상 변동만 처리
        self.message_count = 0  # 메시지 카운터
        self.last_log_time = 0  # 로그 주기 제어

    async def setup_subscriptions(self):
        """구독 설정 - 연결 한 번, 지속적 사용"""
        await self.client.connect()

        # 관심 심벌만 선별적 구독 (효율성 극대화)
        symbols = list(self.target_symbols)

        # 🔧 완전한 해결: 스트림 타입 구분 없이 모든 메시지 처리
        def simple_ticker_handler(message: WebSocketMessage):
            """단순 티커 핸들러 - 모든 메시지를 동일하게 처리"""
            symbol = message.market
            price = message.data.get("trade_price")

            if price is None:
                return

            # 첫 번째 메시지면 초기 가격 설정
            if symbol not in self.current_prices:
                self.current_prices[symbol] = price
                self.initialized_symbols.add(symbol)
                logger.info(f"📸 {symbol} 초기 가격: {price:,}원")
                return

            # 기존 가격과 비교하여 거래 로직 실행
            old_price = self.current_prices[symbol]
            if old_price != price:  # 가격 변동이 있을 때만
                change_rate = ((price - old_price) / old_price) * 100

                # 의미있는 변동만 처리
                if abs(change_rate) >= self.min_change_threshold:
                    self.check_trading_signals(symbol, old_price, price, change_rate)

                # 가격 업데이트
                self.current_prices[symbol] = price

            # 메시지 카운터
            self.message_count += 1
            if self.message_count % 100 == 0:
                logger.info(f"📊 처리된 메시지: {self.message_count}개, 활성 심볼: {len(self.initialized_symbols)}개")

        self.client.add_message_handler(WebSocketDataType.TICKER, simple_ticker_handler)

        # 구독 시작 - 이후 지속적 스트림 개시
        await self.client.subscribe_ticker(symbols)
        logger.info(f"✅ 구독 완료: {symbols}")
        logger.info("🌊 지속적 데이터 스트림 시작 - 연결 종료까지 자동 수신")

    def handle_snapshot_ticker(self, message: WebSocketMessage):
        """스냅샷 처리: 초기 상태만 저장"""
        symbol = message.market
        price = message.data.get("trade_price")

        # 초기 가격 설정
        self.current_prices[symbol] = price
        self.initialized_symbols.add(symbol)

        logger.info(f"📸 {symbol} 초기 가격: {price:,}원")

    def handle_realtime_ticker(self, message: WebSocketMessage):
        """실시간 처리: 효율적 필터링 + 거래 로직"""
        symbol = message.market
        new_price = message.data.get("trade_price")

        # 메시지 카운터 증가
        self.message_count += 1

        # 🎯 1단계: 관심 심벌 필터링 (90% 메시지 걸러냄)
        if symbol not in self.target_symbols:
            return

        # 🎯 2단계: 초기화 확인
        if symbol not in self.initialized_symbols:
            return

        # 🎯 3단계: 데이터 유효성 확인
        if new_price is None:
            return

        old_price = self.current_prices.get(symbol)
        if old_price is None:
            return

        # 🎯 4단계: 변동 임계값 필터링 (작은 변동 무시)
        price_change = new_price - old_price
        change_rate = abs(price_change / old_price) * 100

        if change_rate < self.min_change_threshold:
            return  # 의미있는 변동만 처리

        # 🎯 5단계: 거래 로직 실행
        self.check_trading_signals(symbol, old_price, new_price, price_change / old_price * 100)

        # 현재 가격 업데이트
        self.current_prices[symbol] = new_price

        # 주기적 통계 로그 (1000개마다)
        if self.message_count % 1000 == 0:
            logger.info(f"📊 처리 통계: {self.message_count}개 메시지 수신, "
                        f"관심 심벌 {len(self.target_symbols)}개, "
                        f"활성 심벌 {len(self.initialized_symbols)}개")

    def check_trading_signals(self, symbol: str, old_price: float, new_price: float, change_rate: float):
        """거래 신호 체크"""

        # 예시: 1% 이상 급등 시 매수 신호
        if change_rate > 1.0:
            logger.warning(f"🚀 {symbol} 급등 감지: {old_price:,} → {new_price:,} (+{change_rate:.2f}%)")
            # 여기서 실제 매수 로직 실행

        # 예시: 1% 이상 급락 시 매도 신호
        elif change_rate < -1.0:
            logger.warning(f"📉 {symbol} 급락 감지: {old_price:,} → {new_price:,} ({change_rate:.2f}%)")
            # 여기서 실제 매도 로직 실행

        # 일반적인 가격 변동
        else:
            logger.debug(f"💹 {symbol}: {old_price:,} → {new_price:,} ({change_rate:+.3f}%)")


class WebSocketConnectionManager:
    """WebSocket 연결 관리자"""

    def __init__(self, strategy: RealtimeTradingStrategy):
        self.strategy = strategy
        self.running = False

    async def start_trading(self):
        """거래 시작"""
        try:
            # 구독 설정
            await self.strategy.setup_subscriptions()

            # 거래 루프 시작
            self.running = True
            logger.info("🎯 실시간 거래 시작")
            logger.info("💡 지속적 데이터 스트림: WebSocket 연결 중 자동 수신")

            while self.running:
                # 연결 상태 확인
                if not self.strategy.client.is_connected:
                    logger.error("❌ WebSocket 연결 끊어짐, 재연결 시도...")
                    await self.strategy.client.connect()

                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ 거래 실행 오류: {e}")
        finally:
            await self.cleanup()

    async def stop_trading(self):
        """거래 중지"""
        self.running = False
        logger.info("⏹️ 거래 중지 요청")

    async def cleanup(self):
        """정리 작업"""
        if self.strategy.client.is_connected:
            await self.strategy.client.disconnect()
        logger.info("🧹 정리 완료")


async def demo_realtime_trading():
    """실시간 거래 데모"""
    logger.info("🚀 실시간 거래 패턴 데모 시작")

    # 전략 및 매니저 생성
    strategy = RealtimeTradingStrategy()
    manager = WebSocketConnectionManager(strategy)

    try:
        # 30초간 실시간 거래 시뮬레이션
        trading_task = asyncio.create_task(manager.start_trading())

        # 30초 후 자동 종료
        await asyncio.sleep(30)
        await manager.stop_trading()
        await trading_task

    except KeyboardInterrupt:
        logger.info("⏹️ 사용자 중지")
        await manager.stop_trading()

    logger.info("✅ 데모 완료")


if __name__ == "__main__":
    asyncio.run(demo_realtime_trading())
