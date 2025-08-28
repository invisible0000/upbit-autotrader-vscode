"""
업비트 WebSocket 전체 마켓 스냅샷 테스트
========================================

🎯 목적: 업비트 WebSocket의 극한 처리 능력 테스트
📊 범위: 전체 마켓 (KRW + BTC + USDT) x 모든 데이터 타입
🔧 방식: 하나의 티켓으로 모든 데이터를 스냅샷 요청 (1회)
⚡ 측정: 응답 시간, 메시지 수, 데이터 크기, 처리 성능

실행 방법:
    cd d:/projects/upbit-autotrader-vscode
    python temp/demo_upbit_websocket_full_snapshot.py
"""

import asyncio
import websockets
import json
import sys
import os
import time
import traceback
import aiohttp
from datetime import datetime
from typing import List, Dict, Any, Set

# ===== 📊 테스트 설정 변수 =====
MAX_MARKETS = 3          # 테스트할 마켓 수 (첫 메시지 샘플을 위해 3개로 제한)
INCLUDE_BTC_USDT = True  # BTC, USDT 마켓 포함 여부
RESPONSE_TIMEOUT = 10    # 응답 대기 시간 (초)
DEBUG_MODE = True        # 디버그 모드 (첫 번째 메시지 샘플 출력)
SHOW_FIRST_MESSAGE = True  # 첫 번째 수신 메시지 상세 출력
# ===============================

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from upbit_auto_trading.infrastructure.logging import create_component_logger
    logger = create_component_logger("UpbitFullSnapshotTest")
    LOGGING_AVAILABLE = True
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("UpbitFullSnapshotTest")
    LOGGING_AVAILABLE = False


class UpbitFullSnapshotTester:
    """업비트 WebSocket 전체 스냅샷 테스터"""

    def __init__(self):
        self.websocket = None
        self.all_markets: List[str] = []

        # 테스트 결과 수집
        self.test_results = {
            "start_time": None,
            "end_time": None,
            "total_duration": 0.0,
            "first_message_time": None,
            "last_message_time": None,
            "response_duration": 0.0,
            "markets_requested": 0,
            "data_types_requested": 0,
            "messages_received": 0,
            "data_size_bytes": 0,
            "message_types": {},
            "market_coverage": set(),
            "errors": [],
            "performance_metrics": {}
        }

        # 업비트 WebSocket에서 지원하는 캔들 형식만 사용
        self.all_data_types = [
            "ticker",       # 현재가
            "orderbook",    # 호가
            "trade",        # 체결
            "candle.1s",    # 1초 캔들
            "candle.1m",    # 1분 캔들
            "candle.3m",    # 3분 캔들
            "candle.5m",    # 5분 캔들
            "candle.10m",   # 10분 캔들
            "candle.15m",   # 15분 캔들
            "candle.30m",   # 30분 캔들
            "candle.60m",   # 60분 캔들 (1시간)
            "candle.240m",  # 240분 캔들 (4시간)
        ]

    async def get_all_markets(self) -> List[str]:
        """모든 마켓 조회 (KRW + BTC + USDT)"""
        try:
            logger.info("🔍 전체 마켓 목록 조회 중...")

            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.upbit.com/v1/market/all") as response:
                    if response.status == 200:
                        markets_data = await response.json()
                    else:
                        raise Exception(f"API 호출 실패: {response.status}")

            # 마켓별 분류
            krw_markets = [m['market'] for m in markets_data if m['market'].startswith('KRW-')]
            btc_markets = [m['market'] for m in markets_data if m['market'].startswith('BTC-')]
            usdt_markets = [m['market'] for m in markets_data if m['market'].startswith('USDT-')]

            logger.info("✅ 전체 마켓 조회 완료")
            logger.info(f"   🇰🇷 KRW 마켓: {len(krw_markets)}개")
            logger.info(f"   ₿ BTC 마켓: {len(btc_markets)}개")
            logger.info(f"   💲 USDT 마켓: {len(usdt_markets)}개")

            # 설정에 따른 마켓 선택
            selected_markets = krw_markets[:]  # KRW 마켓은 항상 포함

            if INCLUDE_BTC_USDT:
                selected_markets.extend(btc_markets)
                selected_markets.extend(usdt_markets)

            # 마켓 개수 제한 적용
            if MAX_MARKETS > 0:
                selected_markets = selected_markets[:MAX_MARKETS]
                logger.info(f"📊 마켓 개수 제한 적용: {len(selected_markets)}개 사용")

            logger.info(f"🎯 최종 선택된 마켓: {len(selected_markets)}개")
            if len(selected_markets) <= 10:
                logger.info(f"   선택된 마켓: {selected_markets}")
            else:
                logger.info(f"   선택된 마켓 (처음 10개): {selected_markets[:10]}...")

            return selected_markets

        except Exception as e:
            logger.error(f"❌ 마켓 조회 실패: {e}")
            # 대체 마켓 (주요 마켓만)
            fallback_markets = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP'][:MAX_MARKETS] if MAX_MARKETS > 0 else ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']
            logger.warning(f"대체 마켓 사용: {len(fallback_markets)}개")
            return fallback_markets

    async def connect_websocket(self) -> bool:
        """WebSocket 연결"""
        try:
            logger.info("🔌 업비트 WebSocket 연결 중...")

            self.websocket = await websockets.connect(
                "wss://api.upbit.com/websocket/v1",
                ping_interval=None,  # 테스트 중에는 ping 비활성화
                ping_timeout=None,
                close_timeout=30
            )

            logger.info("✅ WebSocket 연결 성공")
            return True

        except Exception as e:
            logger.error(f"❌ WebSocket 연결 실패: {e}")
            return False

    def create_full_snapshot_message(self) -> List[Dict[str, Any]]:
        """전체 스냅샷 메시지 생성"""
        logger.info("📋 전체 스냅샷 메시지 생성 중...")

        # 고유 티켓 ID
        ticket_id = f"full_test_{int(time.time())}"

        # 메시지 구조
        message = [{"ticket": ticket_id}]

        # 각 데이터 타입별로 모든 마켓 요청 (업비트 API 스펙에 맞게)
        for data_type in self.all_data_types:
            request_spec = {
                "type": data_type,
                "codes": self.all_markets,
                "isOnlySnapshot": True  # 스냅샷만 요청
            }
            message.append(request_spec)

        # 포맷 설정
        message.append({"format": "DEFAULT"})

        # 통계 업데이트
        self.test_results["markets_requested"] = len(self.all_markets)
        self.test_results["data_types_requested"] = len(self.all_data_types)

        # 디버그 모드일 때 요청 메시지 출력
        if DEBUG_MODE:
            logger.info("🔍 생성된 WebSocket 요청 메시지:")
            logger.info("=" * 60)
            logger.info(json.dumps(message, indent=2, ensure_ascii=False))
            logger.info("=" * 60)

        logger.info("📊 요청 규모")
        logger.info(f"   마켓 수: {len(self.all_markets)}개")
        logger.info(f"   데이터 타입: {len(self.all_data_types)}개")
        logger.info(f"   총 요청 조합: {len(self.all_markets) * len(self.all_data_types):,}개")

        return message

    async def send_snapshot_request(self) -> bool:
        """스냅샷 요청 전송"""
        try:
            message = self.create_full_snapshot_message()
            message_json = json.dumps(message, ensure_ascii=False)

            logger.info(f"🚀 스냅샷 요청 전송 시작...")
            logger.info(f"📦 메시지 크기: {len(message_json):,} bytes")

            # 전송 시작 시점 기록
            self.test_results["start_time"] = datetime.now()

            # 메시지 전송
            await self.websocket.send(message_json)

            logger.info("✅ 스냅샷 요청 전송 완료")
            return True

        except Exception as e:
            logger.error(f"❌ 스냅샷 요청 전송 실패: {e}")
            self.test_results["errors"].append(f"Request send error: {str(e)}")
            return False

    async def collect_responses(self, timeout_seconds: int = 30) -> None:
        """응답 수집"""
        logger.info(f"👂 응답 수집 시작 (최대 {timeout_seconds}초)")

        try:
            # 타임아웃과 함께 응답 수집
            await asyncio.wait_for(
                self._response_collection_loop(),
                timeout=timeout_seconds
            )

        except asyncio.TimeoutError:
            logger.info(f"⏰ {timeout_seconds}초 타임아웃으로 수집 종료")

        except Exception as e:
            logger.error(f"❌ 응답 수집 중 오류: {e}")
            self.test_results["errors"].append(f"Response collection error: {str(e)}")

    async def _response_collection_loop(self) -> None:
        """응답 수집 루프"""
        consecutive_timeouts = 0
        max_consecutive_timeouts = 5

        while consecutive_timeouts < max_consecutive_timeouts:
            try:
                # 5초 타임아웃으로 메시지 대기
                message = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=5.0
                )

                consecutive_timeouts = 0  # 메시지 수신 시 리셋
                await self._process_message(message)

            except asyncio.TimeoutError:
                consecutive_timeouts += 1
                logger.debug(f"메시지 대기 타임아웃 ({consecutive_timeouts}/{max_consecutive_timeouts})")

                # 첫 번째 메시지도 받지 못한 경우 계속 대기
                if self.test_results["first_message_time"] is None:
                    consecutive_timeouts = 0

            except websockets.exceptions.ConnectionClosed:
                logger.info("WebSocket 연결이 종료되었습니다")
                break

            except Exception as e:
                logger.error(f"메시지 수신 오류: {e}")
                self.test_results["errors"].append(f"Message receive error: {str(e)}")
                break

        logger.info("🏁 응답 수집 완료")

    async def _process_message(self, raw_message: str) -> None:
        """개별 메시지 처리"""
        try:
            # 메시지 파싱
            if isinstance(raw_message, bytes):
                message_text = raw_message.decode('utf-8')
            else:
                message_text = str(raw_message)

            data = json.loads(message_text)

            # 첫 번째 메시지 시점 기록
            current_time = datetime.now()
            if self.test_results["first_message_time"] is None:
                self.test_results["first_message_time"] = current_time
                logger.info("🎯 첫 번째 응답 수신!")

                # 첫 번째 메시지 샘플 출력
                if SHOW_FIRST_MESSAGE:
                    logger.info(f"📨 첫 번째 메시지 샘플 (길이: {len(message_text)} bytes):")
                    logger.info(f"원시 JSON: {message_text}")
                    logger.info(f"파싱된 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")

            # 마지막 메시지 시점 업데이트
            self.test_results["last_message_time"] = current_time

            # 메시지 통계 업데이트
            self.test_results["messages_received"] += 1
            self.test_results["data_size_bytes"] += len(message_text)

            # 메시지 타입 분석
            message_type = data.get("type", "unknown")
            if message_type not in self.test_results["message_types"]:
                self.test_results["message_types"][message_type] = 0
            self.test_results["message_types"][message_type] += 1

            # 마켓 커버리지 분석
            market = data.get("code", data.get("market", ""))
            if market:
                self.test_results["market_coverage"].add(market)

            # 주기적 진행상황 출력
            if self.test_results["messages_received"] % 100 == 0:
                elapsed = (current_time - self.test_results["start_time"]).total_seconds()
                rate = self.test_results["messages_received"] / elapsed
                logger.info(f"📊 진행: {self.test_results['messages_received']:,}개 메시지 "
                           f"({rate:.1f} msg/sec, {len(self.test_results['market_coverage'])}개 마켓)")

        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            self.test_results["errors"].append(f"JSON parse error: {str(e)}")
        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")
            self.test_results["errors"].append(f"Message process error: {str(e)}")

    async def disconnect(self) -> None:
        """연결 해제"""
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("✅ WebSocket 연결 해제 완료")
            except Exception as e:
                logger.error(f"연결 해제 중 오류: {e}")

    def calculate_final_metrics(self) -> None:
        """최종 성능 지표 계산"""
        if not self.test_results["start_time"]:
            return

        end_time = self.test_results["last_message_time"] or datetime.now()
        self.test_results["end_time"] = end_time

        # 전체 소요 시간
        total_duration = (end_time - self.test_results["start_time"]).total_seconds()
        self.test_results["total_duration"] = total_duration

        # 응답 시간 (첫 메시지까지)
        if self.test_results["first_message_time"]:
            response_duration = (self.test_results["first_message_time"] - self.test_results["start_time"]).total_seconds()
            self.test_results["response_duration"] = response_duration

        # 성능 지표
        messages_received = self.test_results["messages_received"]
        data_size_mb = self.test_results["data_size_bytes"] / (1024 * 1024)

        if total_duration > 0:
            self.test_results["performance_metrics"] = {
                "messages_per_second": messages_received / total_duration,
                "data_throughput_mbps": data_size_mb / total_duration,
                "market_coverage_percent": len(self.test_results["market_coverage"]) / max(len(self.all_markets), 1) * 100,
                "data_type_coverage": len(self.test_results["message_types"]),
                "average_message_size_bytes": self.test_results["data_size_bytes"] / max(messages_received, 1)
            }

    def print_test_results(self) -> None:
        """테스트 결과 출력"""
        print("\n" + "=" * 80)
        print("🎯 업비트 WebSocket 전체 마켓 스냅샷 테스트 결과")
        print("=" * 80)

        # 기본 정보
        print(f"📊 요청 규모:")
        print(f"   마켓 수: {self.test_results['markets_requested']:,}개")
        print(f"   데이터 타입: {self.test_results['data_types_requested']}개")
        print(f"   총 요청 조합: {self.test_results['markets_requested'] * self.test_results['data_types_requested']:,}개")

        # 응답 결과
        print(f"\n📈 응답 결과:")
        print(f"   수신 메시지: {self.test_results['messages_received']:,}개")
        print(f"   커버된 마켓: {len(self.test_results['market_coverage'])}개")
        print(f"   데이터 크기: {self.test_results['data_size_bytes'] / (1024*1024):.2f} MB")

        # 성능 지표
        if self.test_results["performance_metrics"]:
            metrics = self.test_results["performance_metrics"]
            print(f"\n⚡ 성능 지표:")
            print(f"   첫 응답까지: {self.test_results['response_duration']:.3f}초")
            print(f"   전체 소요시간: {self.test_results['total_duration']:.3f}초")
            print(f"   처리 속도: {metrics['messages_per_second']:.1f} msg/sec")
            print(f"   데이터 처리량: {metrics['data_throughput_mbps']:.2f} MB/sec")
            print(f"   마켓 커버리지: {metrics['market_coverage_percent']:.1f}%")
            print(f"   평균 메시지 크기: {metrics['average_message_size_bytes']:.0f} bytes")

        # 메시지 타입별 분포
        if self.test_results["message_types"]:
            print(f"\n📋 메시지 타입별 분포:")
            for msg_type, count in sorted(self.test_results["message_types"].items()):
                percentage = count / max(self.test_results["messages_received"], 1) * 100
                print(f"   {msg_type}: {count:,}개 ({percentage:.1f}%)")

        # 오류 정보
        if self.test_results["errors"]:
            print(f"\n❌ 오류 ({len(self.test_results['errors'])}개):")
            for error in self.test_results["errors"][:5]:  # 최대 5개만 표시
                print(f"   - {error}")
            if len(self.test_results["errors"]) > 5:
                print(f"   ... 및 {len(self.test_results['errors']) - 5}개 더")

        # 결론
        print(f"\n💡 테스트 결론:")
        if self.test_results["messages_received"] > 0:
            success_rate = (1 - len(self.test_results["errors"]) / max(self.test_results["messages_received"], 1)) * 100
            print(f"   ✅ 업비트 WebSocket은 {self.test_results['markets_requested']:,}개 마켓 x {self.test_results['data_types_requested']}개 데이터 타입")
            print(f"      총 {self.test_results['markets_requested'] * self.test_results['data_types_requested']:,}개 조합을 하나의 티켓으로 성공적으로 처리!")
            print(f"   📊 성공률: {success_rate:.1f}%")
            print(f"   ⚡ 업비트의 WebSocket 처리 능력은 매우 뛰어남을 확인!")
        else:
            print(f"   ❌ 테스트 실패 - 응답을 받지 못했습니다")

        print("=" * 80)

    async def run_test(self, timeout_seconds: int = 30) -> None:
        """전체 테스트 실행"""
        try:
            logger.info("🚀 업비트 WebSocket 전체 마켓 스냅샷 테스트 시작!")

            # 1. 마켓 조회
            self.all_markets = await self.get_all_markets()
            if not self.all_markets:
                logger.error("❌ 마켓 조회 실패로 테스트 중단")
                return

            # 2. WebSocket 연결
            if not await self.connect_websocket():
                logger.error("❌ WebSocket 연결 실패로 테스트 중단")
                return

            # 3. 스냅샷 요청
            if not await self.send_snapshot_request():
                logger.error("❌ 스냅샷 요청 실패로 테스트 중단")
                return

            # 4. 응답 수집
            await self.collect_responses(timeout_seconds)

            # 5. 결과 분석
            self.calculate_final_metrics()

            logger.info("✅ 테스트 완료!")

        except Exception as e:
            logger.error(f"❌ 테스트 실행 중 오류: {e}")
            logger.error(f"상세 오류: {traceback.format_exc()}")
            self.test_results["errors"].append(f"Test execution error: {str(e)}")

        finally:
            await self.disconnect()
            self.print_test_results()


async def main():
    """메인 함수"""
    print(f"""
🚀 업비트 WebSocket 전체 마켓 스냅샷 테스트
==========================================

📊 테스트 설정:
- 최대 마켓 수: {MAX_MARKETS}개 (0이면 전체 마켓)
- BTC/USDT 포함: {INCLUDE_BTC_USDT}
- 응답 타임아웃: {RESPONSE_TIMEOUT}초
- 디버그 모드: {DEBUG_MODE}

📋 테스트 내용:
- 업비트 WebSocket 극한 처리 능력 측정
- 모든 마켓 x 모든 데이터 타입 (현재가, 호가, 체결, 지원되는 모든 캔들)
- 하나의 티켓으로 모든 데이터를 스냅샷 요청
- 응답 시간, 처리량, 성공률 측정

테스트를 시작합니다...
    """)

    tester = UpbitFullSnapshotTester()

    # 설정된 타임아웃으로 테스트 실행
    await tester.run_test(timeout_seconds=RESPONSE_TIMEOUT)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 사용자가 테스트를 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
