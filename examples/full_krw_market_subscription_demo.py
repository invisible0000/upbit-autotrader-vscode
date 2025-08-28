"""
업비트 전체 KRW 마켓 통합 # ===== 설정 변수 =====
# KRW 마켓 심벌 제한 개수 (0이면 전체 마켓 사용)
MAX_KRW_MARKETS = 3  # 최대 189, krw 마켓

# 데모 실행 시간 (초)
DEMO_DURATION_SECONDS = 5  # int로 변경
==========================================

🎯 목적: 모든 KRW 마켓의 현재가, 호가, 체결, 캔들(1초) 데이터 수신
🔧 기술: v3.0 SubscriptionManager + 혼합 구독 시스템
📊 성능: 5개 티켓 풀 + 효율적인 메시지 라우팅

실행 방법:
    cd d:/projects/upbit-autotrader-vscode
    python examples/full_krw_market_subscription_demo.py
"""

import asyncio
import websockets
import sys
import os
import traceback
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime

# ===== 설정 변수 =====
# KRW 마켓 심벌 제한 개수 (0이면 전체 마켓 사용)
MAX_KRW_MARKETS = 3  # 최대 189, krw 마켓

# 데모 실행 시간 (초)
DEMO_DURATION_SECONDS = 5  # int로 변경
# ====================

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # 프로젝트 모듈 import
    from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5.subscription_manager import (
        SubscriptionManager
    )
    from upbit_auto_trading.infrastructure.logging import create_component_logger
    logger = create_component_logger("FullKRWMarketDemo")
    MODULE_AVAILABLE = True
except ImportError as e:
    print(f"모듈 import 실패: {e}")
    print("기본 로깅으로 대체합니다.")
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("FullKRWMarketDemo")
    MODULE_AVAILABLE = False
    # SubscriptionManager 모듈이 없으면 None으로 설정
    SubscriptionManager = None


class FullKRWMarketSubscriptionDemo:
    """전체 KRW 마켓 구독 데모"""

    def __init__(self):
        if not MODULE_AVAILABLE or SubscriptionManager is None:
            logger.error("SubscriptionManager 모듈을 사용할 수 없습니다")
            return

        self.subscription_manager = SubscriptionManager(
            public_pool_size=5,  # 큰 데이터량을 위해 증가
            private_pool_size=2
        )
        self.websocket = None
        self.krw_markets: List[str] = []

        # 메시지 수신 통계
        self.message_stats = {
            "ticker": 0,
            "orderbook": 0,
            "trade": 0,
            "candle_1s": 0,  # 1초 캔들 분리
            "candle_1m": 0,  # 1분 캔들 분리
            "candle": 0,     # 전체 캔들 (호환성)
            "total": 0,
            "start_time": None
        }

        # 콜백 등록
        self._register_callbacks()

    def _register_callbacks(self):
        """메시지 타입별 콜백 등록"""

        async def ticker_callback(data: Dict[str, Any]):
            """현재가 콜백"""
            self.message_stats["ticker"] += 1
            self.message_stats["total"] += 1

            market = data.get("code", "UNKNOWN")
            price = data.get("trade_price", 0)
            change_rate = data.get("signed_change_rate", 0) * 100

            if self.message_stats["total"] % 50 == 0:  # 50개마다 출력
                logger.info(f"📈 현재가 | {market}: {price:,}원 ({change_rate:+.2f}%) [총 {self.message_stats['ticker']}개]")

        async def orderbook_callback(data: Dict[str, Any]):
            """호가 콜백"""
            self.message_stats["orderbook"] += 1
            self.message_stats["total"] += 1

            market = data.get("code", "UNKNOWN")
            orderbook_units = data.get("orderbook_units", [])

            if orderbook_units and self.message_stats["total"] % 100 == 0:  # 100개마다 출력
                best_bid = orderbook_units[0].get("bid_price", 0)
                best_ask = orderbook_units[0].get("ask_price", 0)
                spread_rate = ((best_ask - best_bid) / best_ask * 100) if best_ask > 0 else 0

                logger.info(f"📋 호가 | {market}: 매수 {best_bid:,} / 매도 {best_ask:,} "
                            f"(스프레드 {spread_rate:.3f}%) [총 {self.message_stats['orderbook']}개]")

        async def trade_callback(data: Dict[str, Any]):
            """체결 콜백"""
            self.message_stats["trade"] += 1
            self.message_stats["total"] += 1

            market = data.get("code", "UNKNOWN")
            price = data.get("trade_price", 0)
            volume = data.get("trade_volume", 0)
            ask_bid = data.get("ask_bid", "")

            if self.message_stats["total"] % 30 == 0:  # 30개마다 출력
                direction = "🔴매도" if ask_bid == "ASK" else "🔵매수"
                logger.info(f"💰 체결 | {market}: {direction} {price:,}원 x {volume:.4f} [총 {self.message_stats['trade']}개]")

        async def candle_callback(data: Dict[str, Any]):
            """캔들 콜백 - 타입별 구분 처리"""
            candle_type = data.get("type", "")
            market = data.get("code", "UNKNOWN")
            opening_price = data.get("opening_price", 0)
            high_price = data.get("high_price", 0)
            low_price = data.get("low_price", 0)
            trade_price = data.get("trade_price", 0)

            # 타입별 통계 업데이트
            if candle_type == "candle.1s":
                self.message_stats["candle_1s"] += 1
                candle_emoji = "🕯️1s"
            elif candle_type == "candle.1m":
                self.message_stats["candle_1m"] += 1
                candle_emoji = "📊1m"
            else:
                candle_emoji = "🕯️??"

            self.message_stats["candle"] += 1  # 전체 캔들 통계
            self.message_stats["total"] += 1

            # 각 캔들 타입별로 다른 주기로 출력
            if candle_type == "candle.1s" and self.message_stats["candle_1s"] % 5 == 0:  # 1초 캔들은 5개마다
                logger.info(f"{candle_emoji} 캔들 | {market}: O{opening_price:,} H{high_price:,} "
                            f"L{low_price:,} C{trade_price:,} [1s: {self.message_stats['candle_1s']}개]")
            elif candle_type == "candle.1m" and self.message_stats["candle_1m"] % 2 == 0:  # 1분 캔들은 2개마다
                logger.info(f"{candle_emoji} 캔들 | {market}: O{opening_price:,} H{high_price:,} "
                            f"L{low_price:,} C{trade_price:,} [1m: {self.message_stats['candle_1m']}개]")

        # 콜백 등록 - 각 캔들 타입별로 등록
        self.subscription_manager.register_type_callback("ticker", ticker_callback)
        self.subscription_manager.register_type_callback("orderbook", orderbook_callback)
        self.subscription_manager.register_type_callback("trade", trade_callback)
        self.subscription_manager.register_type_callback("candle.1s", candle_callback)  # 1초 캔들
        self.subscription_manager.register_type_callback("candle.1m", candle_callback)  # 1분 캔들

    async def get_krw_markets(self) -> List[str]:
        """KRW 마켓 목록 조회"""
        try:
            logger.info("🔍 KRW 마켓 목록 조회 중...")

            # 업비트 REST API 직접 호출
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.upbit.com/v1/market/all") as response:
                    if response.status == 200:
                        markets = await response.json()
                    else:
                        raise Exception(f"API 호출 실패: {response.status}")

            krw_markets = [
                market['market'] for market in markets
                if market['market'].startswith('KRW-')
            ]

            # 설정된 개수만큼 제한
            if MAX_KRW_MARKETS > 0:
                krw_markets = krw_markets[:MAX_KRW_MARKETS]
                logger.info(f"✅ KRW 마켓 {len(krw_markets)}개로 제한: {krw_markets}")
            else:
                logger.info(f"✅ 전체 KRW 마켓 {len(krw_markets)}개 발견: {krw_markets[:5]}... (총 {len(krw_markets)}개)")

            return krw_markets

        except Exception as e:
            logger.error(f"❌ KRW 마켓 조회 실패: {e}")
            # 기본 주요 마켓으로 대체 (설정된 개수만큼)
            default_markets = [
                'KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA', 'KRW-DOT',
                'KRW-LINK', 'KRW-LTC', 'KRW-BCH', 'KRW-EOS', 'KRW-TRX'
            ]
            if MAX_KRW_MARKETS > 0:
                return default_markets[:MAX_KRW_MARKETS]
            else:
                return default_markets

    async def connect_websocket(self) -> bool:
        """WebSocket 연결"""
        try:
            logger.info("🔌 업비트 WebSocket 연결 중...")
            self.websocket = await websockets.connect(
                "wss://api.upbit.com/websocket/v1",
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )

            # 구독 매니저에 WebSocket 연결 설정
            self.subscription_manager.set_websocket_connection(self.websocket)

            logger.info("✅ WebSocket 연결 성공")
            return True

        except Exception as e:
            logger.error(f"❌ WebSocket 연결 실패: {e}")
            return False

    async def create_full_market_subscription(self) -> Optional[str]:
        """전체 마켓 통합 구독 생성"""
        try:
            logger.info("🚀 전체 KRW 마켓 통합 구독 생성 중...")

            # 혼합 구독 스펙 정의 (기본 티켓 사용)
            data_specs = {
                "ticker": {
                    "symbols": self.krw_markets,
                    "mode": "snapshot_then_realtime",
                    "options": {}
                },
                "orderbook": {
                    "symbols": self.krw_markets,
                    "mode": "snapshot_then_realtime",
                    "options": {}
                },
                "trade": {
                    "symbols": self.krw_markets,
                    "mode": "snapshot_then_realtime",  # 기본값 사용
                    "options": {}
                },
                "candle.1s": {
                    "symbols": self.krw_markets,
                    "mode": "snapshot_then_realtime",
                    "options": {}  # 1초 캔들은 type에 이미 포함됨
                },
                "candle.1m": {
                    "symbols": self.krw_markets,
                    "mode": "snapshot_then_realtime",
                    "options": {}  # 1분 캔들은 type에 이미 포함됨
                }
            }

            # 통합 구독 실행 (기본 티켓 사용)
            subscription_id = await self.subscription_manager.subscribe_mixed(
                data_specs=data_specs,
                ticket_id=None,  # 기본 티켓 사용
                callback=None  # 타입별 콜백 이미 등록됨
            )

            if subscription_id:
                logger.info(f"✅ 통합 구독 생성 성공: {subscription_id}")
                logger.info(f"📊 구독 내용: {len(self.krw_markets)}개 마켓 x 5개 데이터 타입 (현재가, 호가, 체결, 1초캔들, 1분캔들)")
                return subscription_id
            else:
                logger.error("❌ 통합 구독 생성 실패")
                return None

        except Exception as e:
            logger.error(f"❌ 통합 구독 생성 중 오류: {e}")
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return None

    async def handle_websocket_messages(self):
        """WebSocket 메시지 처리"""
        try:
            logger.info("👂 메시지 수신 대기 중...")
            self.message_stats["start_time"] = datetime.now()

            if self.websocket is None:
                logger.error("WebSocket 연결이 None입니다")
                return

            async for raw_message in self.websocket:
                try:
                    # WebSocket 메시지를 문자열로 변환
                    if isinstance(raw_message, bytes):
                        message_str = raw_message.decode('utf-8')
                    else:
                        message_str = str(raw_message)

                    # 첫 번째 메시지는 디버그 출력
                    if self.message_stats["total"] == 0:
                        logger.info(f"🔍 첫 번째 메시지 수신: {message_str[:200]}...")

                    await self.subscription_manager.process_message(message_str)

                    # 주기적 통계 출력
                    if self.message_stats["total"] % 500 == 0:
                        await self._print_statistics()

                except Exception as e:
                    logger.error(f"메시지 처리 오류: {e}")
                    continue

        except websockets.exceptions.ConnectionClosed:
            logger.warning("⚠️ WebSocket 연결 종료됨")
        except Exception as e:
            logger.error(f"❌ 메시지 처리 중 오류: {e}")

    async def _print_statistics(self):
        """통계 출력"""
        if self.message_stats["start_time"]:
            elapsed = (datetime.now() - self.message_stats["start_time"]).total_seconds()
            rate = self.message_stats["total"] / elapsed if elapsed > 0 else 0

            logger.info("=" * 80)
            logger.info("📊 실시간 통계")
            logger.info(f"   총 메시지: {self.message_stats['total']:,}개")
            logger.info(f"   현재가: {self.message_stats['ticker']:,}개")
            logger.info(f"   호가: {self.message_stats['orderbook']:,}개")
            logger.info(f"   체결: {self.message_stats['trade']:,}개")
            logger.info("   📊 캔들 상세:")
            logger.info(f"     🕯️ 1초 캔들: {self.message_stats['candle_1s']:,}개")
            logger.info(f"     📊 1분 캔들: {self.message_stats['candle_1m']:,}개")
            logger.info(f"     🔗 전체 캔들: {self.message_stats['candle']:,}개")
            logger.info(f"   처리 속도: {rate:.1f} msg/sec")
            logger.info(f"   경과 시간: {elapsed:.1f}초")

            # 구독 매니저 통계
            stats = self.subscription_manager.get_stats()
            logger.info(f"   활성 구독: {stats['subscription_stats']['total_subscriptions']}개")
            logger.info(f"   티켓 사용률: {stats['ticket_stats']['public_pool']['utilization_percent']:.1f}%")
            logger.info("=" * 80)

    async def cleanup(self):
        """정리 작업"""
        try:
            logger.info("🧹 정리 작업 시작...")

            # 모든 구독 해제
            unsubscribed = await self.subscription_manager.unsubscribe_all()
            logger.info(f"✅ {unsubscribed}개 구독 해제 완료")

            # WebSocket 연결 종료
            if self.websocket:
                await self.websocket.close()
                logger.info("✅ WebSocket 연결 종료")

        except Exception as e:
            logger.error(f"❌ 정리 작업 중 오류: {e}")

    async def run(self, duration_seconds: int = 300):
        """메인 실행 함수

        Args:
            duration_seconds: 실행 시간 (초, 기본 5분)
        """
        try:
            logger.info("🎬 전체 KRW 마켓 구독 데모 시작")
            logger.info(f"⏱️ 실행 시간: {duration_seconds}초 ({duration_seconds // 60}분)")

            # 1. KRW 마켓 목록 조회
            self.krw_markets = await self.get_krw_markets()
            if not self.krw_markets:
                logger.error("❌ KRW 마켓을 찾을 수 없습니다")
                return

            # 2. WebSocket 연결
            if not await self.connect_websocket():
                logger.error("❌ WebSocket 연결 실패")
                return

            # 3. 통합 구독 생성
            subscription_id = await self.create_full_market_subscription()
            if not subscription_id:
                logger.error("❌ 구독 생성 실패")
                return

            # 4. 메시지 수신 (제한 시간)
            logger.info(f"🏃‍♂️ {duration_seconds}초 동안 메시지 수신 시작...")

            try:
                await asyncio.wait_for(
                    self.handle_websocket_messages(),
                    timeout=duration_seconds
                )
            except asyncio.TimeoutError:
                logger.info(f"⏰ {duration_seconds}초 실행 완료")

            # 5. 최종 통계 출력
            await self._print_statistics()

        except KeyboardInterrupt:
            logger.info("⚡ 사용자 중단 (Ctrl+C)")
        except Exception as e:
            logger.error(f"❌ 실행 중 오류: {e}")
            logger.error(f"상세 오류: {traceback.format_exc()}")
        finally:
            await self.cleanup()


async def main():
    """메인 함수"""
    demo = FullKRWMarketSubscriptionDemo()

    # 설정된 시간만큼 실행
    await demo.run(duration_seconds=DEMO_DURATION_SECONDS)


if __name__ == "__main__":
    print(f"""
🚀 업비트 전체 KRW 마켓 통합 구독 데모 ({DEMO_DURATION_SECONDS}초 실행)
===============================================

📊 설정:
- KRW 마켓 개수: {MAX_KRW_MARKETS if MAX_KRW_MARKETS > 0 else '전체'}개
- 실행 시간: {DEMO_DURATION_SECONDS}초

이 데모는 다음을 수행합니다:
1. 설정된 개수의 KRW 마켓 목록 조회
2. 현재가, 호가, 체결, 1초 캔들 데이터 통합 구독
3. v3.0 구독 매니저의 혼합 구독 시스템 활용
4. 실시간 메시지 수신 통계 출력
5. 효율적인 5개 티켓 풀 관리

{DEMO_DURATION_SECONDS}초 후 자동 종료됩니다...
    """)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 데모가 종료되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
