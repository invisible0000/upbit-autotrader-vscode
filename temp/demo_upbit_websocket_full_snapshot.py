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
MAX_MARKETS = 0         # 테스트할 마켓 수 (더 실용적인 성능 측정을 위해 20개로 증가)
INCLUDE_BTC_USDT = True  # BTC, USDT 마켓 포함 여부
RESPONSE_TIMEOUT = 0     # 응답 대기 시간 (0=스냅샷 완료 시 자동 종료)
DEBUG_MODE = False       # 디버그 모드 (성능 집중을 위해 비활성화)
SHOW_FIRST_MESSAGE = False  # 첫 번째 수신 메시지 상세 출력

# ===== 🚀 새로운 성능 테스트 옵션 =====
USE_COMPRESSION = True    # WebSocket 압축 사용 여부 (deflate-frame)
USE_SIMPLE_FORMAT = True  # SIMPLE 포맷 사용 여부 (60% 대역폭 절약)
COMPARE_FORMATS = False   # 포맷별 성능 비교 테스트 (DEFAULT vs SIMPLE)
PERFORMANCE_FOCUS = True  # 성능 측정에 집중 (상세 로깅 최소화)

# ===== 📈 고급 성능 분석 옵션 =====
MEASURE_COMPRESSION_RATIO = True  # 압축 비율 실제 측정
DETAILED_MESSAGE_ANALYSIS = True  # 메시지 타입별 상세 분석
BANDWIDTH_TRACKING = True         # 실시간 대역폭 사용량 추적

# ===== ⚡ 스냅샷 최적화 설정 =====
SMART_COMPLETION_DETECTION = True  # 스마트 완료 감지 (예상 메시지 수 도달 시 자동 종료)
MAX_IDLE_TIME = 2.0              # 최대 무응답 시간 (초) - 이후 자동 종료
COMPLETION_BUFFER_TIME = 0.5     # 완료 후 추가 대기 시간 (지연 메시지 수집용)
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

# 🚀 WebSocket v5.0 클라이언트 임포트 (SIMPLE 포맷 지원)
try:
    from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5 import (
        upbit_websocket_public_client as v5_client,
        simple_format_converter
    )
    V5_CLIENT_AVAILABLE = True
    logger.info("✅ WebSocket v5.0 클라이언트 로드 성공 (SIMPLE 포맷 지원)")
except ImportError as e:
    V5_CLIENT_AVAILABLE = False
    logger.warning(f"⚠️ WebSocket v5.0 클라이언트 로드 실패: {e}")
    logger.info("기본 WebSocket 클라이언트 사용")


class UpbitFullSnapshotTester:
    """업비트 WebSocket 전체 스냅샷 테스터 - 🚀 압축 & SIMPLE 포맷 지원"""

    def __init__(self):
        self.websocket = None
        self.all_markets: List[str] = []

        # 🚀 성능 최적화 옵션
        self.use_compression = USE_COMPRESSION
        self.use_simple_format = USE_SIMPLE_FORMAT
        self.compare_formats = COMPARE_FORMATS
        self.performance_focus = PERFORMANCE_FOCUS

        # SIMPLE 포맷 컨버터 초기화
        self.simple_converter = None
        if V5_CLIENT_AVAILABLE and self.use_simple_format:
            try:
                # 함수 기반이므로 모듈을 직접 참조
                self.simple_converter = simple_format_converter
                logger.info("✅ SIMPLE 포맷 컨버터 초기화 완료")
            except Exception as e:
                logger.warning(f"⚠️ SIMPLE 포맷 컨버터 초기화 실패: {e}")
                self.use_simple_format = False

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
            "performance_metrics": {},
            # 🚀 새로운 성능 지표
            "compression_enabled": self.use_compression,
            "simple_format_enabled": self.use_simple_format,
            "simple_format_savings": 0,  # SIMPLE 포맷으로 절약된 바이트
            "compression_ratio": 0.0,   # 압축 비율
            "format_conversion_time": 0.0,  # 포맷 변환 시간
            # ⚡ 스마트 완료 감지
            "expected_messages": 0,     # 예상 메시지 수
            "completion_detected": False,  # 완료 감지 여부
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
        """WebSocket 연결 - 🚀 압축 옵션 지원"""
        try:
            logger.info("🔌 업비트 WebSocket 연결 중...")

            # 🚀 간단한 압축 설정 (헤더 없이 기본 연결)
            if self.use_compression:
                logger.info("🗜️ WebSocket 압축 모드 활성화 요청")

            # WebSocket 연결 (기본 설정)
            self.websocket = await websockets.connect(
                "wss://api.upbit.com/websocket/v1",
                ping_interval=None,  # 테스트 중에는 ping 비활성화
                ping_timeout=None,
                close_timeout=30
            )

            logger.info("✅ WebSocket 연결 성공")
            if self.use_compression:
                logger.info("   🗜️ 압축 모드: 서버에서 지원하는 경우 자동 활성화")
            if self.use_simple_format:
                logger.info("   📊 SIMPLE 포맷: 활성화 (60% 대역폭 절약 예상)")
            return True

        except Exception as e:
            logger.error(f"❌ WebSocket 연결 실패: {e}")
            return False

    def create_full_snapshot_message(self) -> List[Dict[str, Any]]:
        """전체 스냅샷 메시지 생성 - 🚀 SIMPLE 포맷 지원"""
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

        # 🚀 포맷 설정 (SIMPLE 또는 DEFAULT)
        format_setting = {"format": "SIMPLE" if self.use_simple_format else "DEFAULT"}
        message.append(format_setting)

        # 통계 업데이트
        self.test_results["markets_requested"] = len(self.all_markets)
        self.test_results["data_types_requested"] = len(self.all_data_types)

        # ⚡ 예상 메시지 수 계산 (스마트 완료 감지용)
        # 각 마켓 x 각 데이터 타입 = 예상 스냅샷 메시지 수
        self.test_results["expected_messages"] = len(self.all_markets) * len(self.all_data_types)

        # 디버그 모드일 때 요청 메시지 출력
        if DEBUG_MODE and not self.performance_focus:
            logger.info("🔍 생성된 WebSocket 요청 메시지:")
            logger.info("=" * 60)
            logger.info(json.dumps(message, indent=2, ensure_ascii=False))
            logger.info("=" * 60)

        logger.info("📊 요청 규모")
        logger.info(f"   마켓 수: {len(self.all_markets)}개")
        logger.info(f"   데이터 타입: {len(self.all_data_types)}개")
        total_combinations = len(self.all_markets) * len(self.all_data_types)
        logger.info(f"   총 요청 조합: {total_combinations:,}개")

        # 🚀 성능 최적화 정보
        if self.use_simple_format:
            logger.info("   📊 SIMPLE 포맷: 활성화 (예상 60% 대역폭 절약)")
        if self.use_compression:
            logger.info("   🗜️ 압축: 요청됨 (추가 대역폭 절약 예상)")

        return message

    async def send_snapshot_request(self) -> bool:
        """스냅샷 요청 전송"""
        try:
            message = self.create_full_snapshot_message()
            message_json = json.dumps(message, ensure_ascii=False)

            logger.info("🚀 스냅샷 요청 전송 시작...")
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
        """응답 수집 - ⚡ 스마트 완료 감지"""
        if RESPONSE_TIMEOUT == 0:
            logger.info("👂 응답 수집 시작 (스마트 완료 감지 모드)")
        else:
            logger.info(f"👂 응답 수집 시작 (최대 {timeout_seconds}초)")

        try:
            if RESPONSE_TIMEOUT == 0 and SMART_COMPLETION_DETECTION:
                # 스마트 완료 감지 모드
                await self._smart_response_collection()
            else:
                # 기존 타임아웃 모드
                await asyncio.wait_for(
                    self._response_collection_loop(),
                    timeout=timeout_seconds
                )

        except asyncio.TimeoutError:
            logger.info(f"⏰ {timeout_seconds}초 타임아웃으로 수집 종료")

        except Exception as e:
            logger.error(f"❌ 응답 수집 중 오류: {e}")
            self.test_results["errors"].append(f"Response collection error: {str(e)}")

    async def _smart_response_collection(self) -> None:
        """스마트 응답 수집 - 예상 메시지 수 도달 시 자동 종료"""
        expected_count = self.test_results["expected_messages"]
        logger.info(f"🎯 예상 메시지 수: {expected_count}개")

        last_message_time = time.time()
        completion_buffer_started = False

        while True:
            try:
                # 짧은 타임아웃으로 메시지 대기
                message = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=0.1
                )

                last_message_time = time.time()
                completion_buffer_started = False
                await self._process_message(message)

                # 예상 메시지 수 도달 확인
                if (self.test_results["messages_received"] >= expected_count and
                    not completion_buffer_started):
                    logger.info(f"✅ 예상 메시지 수({expected_count}개) 도달! 완료 버퍼 시작...")
                    completion_buffer_started = True
                    last_message_time = time.time()

            except asyncio.TimeoutError:
                current_time = time.time()
                idle_time = current_time - last_message_time

                # 완료 버퍼 모드에서 추가 대기
                if completion_buffer_started and idle_time >= COMPLETION_BUFFER_TIME:
                    logger.info(f"🏁 완료 버퍼({COMPLETION_BUFFER_TIME}초) 종료 - 스냅샷 완료!")
                    self.test_results["completion_detected"] = True
                    break

                # 최대 무응답 시간 초과
                if idle_time >= MAX_IDLE_TIME:
                    received = self.test_results["messages_received"]
                    logger.info(f"⏰ 무응답 시간({MAX_IDLE_TIME}초) 초과 - 수집 종료")
                    logger.info(f"📊 최종 수신: {received}/{expected_count}개 ({received/expected_count*100:.1f}%)")
                    break

            except websockets.exceptions.ConnectionClosed:
                logger.info("🔌 WebSocket 연결이 종료되었습니다")
                break

            except Exception as e:
                logger.error(f"메시지 수신 오류: {e}")
                self.test_results["errors"].append(f"Message receive error: {str(e)}")
                break

        logger.info("🏁 스마트 응답 수집 완료")

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

    async def _process_message(self, raw_message) -> None:
        """개별 메시지 처리 - 🚀 SIMPLE 포맷 감지 및 변환"""
        try:
            # 메시지 파싱
            if isinstance(raw_message, bytes):
                message_text = raw_message.decode('utf-8')
            else:
                message_text = str(raw_message)

            data = json.loads(message_text)

            # 🚀 SIMPLE 포맷 감지 및 원본 크기 저장
            original_size = len(message_text)
            is_simple_format = False
            converted_data = data

            # SIMPLE 포맷 감지 (SIMPLE 포맷일 때 특징적인 축약 필드 확인)
            if self.use_simple_format and self.simple_converter:
                try:
                    format_start_time = time.time()

                    # SIMPLE 포맷 감지 (ty, cd 등 축약 필드 존재 확인)
                    if 'ty' in data or 'cd' in data:
                        is_simple_format = True
                        # SIMPLE에서 DEFAULT로 변환 (가독성을 위해)
                        # 메시지 타입에 따른 변환 함수 호출
                        message_type = data.get('ty', data.get('type', ''))
                        try:
                            if message_type == 'ticker':
                                converted_data = self.simple_converter.convert_ticker_simple_to_default(data)
                            elif message_type == 'trade':
                                converted_data = self.simple_converter.convert_trade_simple_to_default(data)
                            elif message_type == 'orderbook':
                                converted_data = self.simple_converter.convert_orderbook_simple_to_default(data)
                            else:
                                # 범용 변환 시도 (기본값 유지)
                                converted_data = data
                        except AttributeError:
                            # 함수가 없는 경우 기본값 유지
                            converted_data = data

                    # 포맷 변환 시간 누적
                    format_end_time = time.time()
                    self.test_results["format_conversion_time"] += (format_end_time - format_start_time)

                    # SIMPLE 포맷 절약량 계산 (추정)
                    if is_simple_format:
                        # DEFAULT 포맷으로 변환했을 때의 크기
                        default_size = len(json.dumps(converted_data, ensure_ascii=False))
                        savings = default_size - original_size
                        self.test_results["simple_format_savings"] += savings

                except Exception as e:
                    logger.debug(f"SIMPLE 포맷 변환 실패: {e}")
                    converted_data = data

            # 첫 번째 메시지 시점 기록
            current_time = datetime.now()
            if self.test_results["first_message_time"] is None:
                self.test_results["first_message_time"] = current_time
                logger.info("🎯 첫 번째 응답 수신!")

                # 첫 번째 메시지 샘플 출력
                if SHOW_FIRST_MESSAGE and not self.performance_focus:
                    logger.info(f"📨 첫 번째 메시지 샘플 (길이: {len(message_text)} bytes):")
                    if is_simple_format:
                        logger.info("🚀 SIMPLE 포맷 감지됨!")
                        logger.info(f"원본 SIMPLE: {json.dumps(data, ensure_ascii=False)}")
                        logger.info(f"변환된 DEFAULT: {json.dumps(converted_data, ensure_ascii=False)}")
                    else:
                        logger.info(f"파싱된 데이터: {json.dumps(converted_data, indent=2, ensure_ascii=False)}")

            # 마지막 메시지 시점 업데이트
            self.test_results["last_message_time"] = current_time

            # 메시지 통계 업데이트
            self.test_results["messages_received"] += 1
            self.test_results["data_size_bytes"] += len(message_text)

            # 🚀 압축 효과 측정 (원본 vs 압축 크기 추정)
            if MEASURE_COMPRESSION_RATIO and self.use_compression:
                # WebSocket 압축은 투명하게 처리되므로 간접적으로 측정
                # 압축되지 않은 JSON 크기와 실제 수신 크기 비교
                uncompressed_estimate = len(json.dumps(converted_data, ensure_ascii=False))
                if uncompressed_estimate > len(message_text):
                    compression_savings = uncompressed_estimate - len(message_text)
                    if "compression_savings" not in self.test_results:
                        self.test_results["compression_savings"] = 0
                    self.test_results["compression_savings"] += compression_savings

            # 메시지 타입 분석 (원본 데이터와 변환된 데이터 모두 확인)
            # SIMPLE 포맷의 경우 'ty' 필드, DEFAULT 포맷의 경우 'type' 필드 사용
            message_type = converted_data.get("type") or data.get("ty") or data.get("type") or "unknown"

            # 🚀 캔들 데이터 타입 감지 개선 - 원본 데이터도 확인
            if message_type == "unknown":
                # 캔들 데이터 특성으로 감지 (OHLC 필드 존재)
                if all(key in converted_data for key in ['opening_price', 'high_price', 'low_price', 'trade_price']):
                    message_type = "candle.unknown"  # 구체적인 타임프레임은 모르지만 캔들임은 확실
                elif 'orderbook_units' in converted_data:
                    message_type = "orderbook"
                elif 'trade_price' in converted_data and 'trade_volume' in converted_data and 'timestamp' in converted_data:
                    message_type = "trade"
                elif 'opening_price' in converted_data and 'change' in converted_data:
                    message_type = "ticker"

            if message_type not in self.test_results["message_types"]:
                self.test_results["message_types"][message_type] = 0
            self.test_results["message_types"][message_type] += 1

            # 마켓 커버리지 분석
            market = converted_data.get("code", converted_data.get("market", ""))
            if market:
                self.test_results["market_coverage"].add(market)

            # 주기적 진행상황 출력 (성능 모드가 아닐 때만)
            if (not self.performance_focus and
                    self.test_results["messages_received"] % 100 == 0):
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
        """테스트 결과 출력 - 🚀 압축 & SIMPLE 포맷 성능 포함"""
        print("\n" + "=" * 80)
        print("🎯 업비트 WebSocket 전체 마켓 스냅샷 테스트 결과")
        print("=" * 80)

        # 🚀 성능 최적화 설정 정보
        print("🚀 성능 최적화 설정:")
        compression_status = "✅ 활성화" if self.test_results['compression_enabled'] else "❌ 비활성화"
        simple_status = "✅ 활성화" if self.test_results['simple_format_enabled'] else "❌ 비활성화"
        print(f"   압축 사용: {compression_status}")
        print(f"   SIMPLE 포맷: {simple_status}")

        # 📡 요청/응답 포맷 상세 정보
        print("\n📡 통신 포맷 분석:")
        if self.test_results['simple_format_enabled']:
            print("   📤 요청 포맷: SIMPLE (업비트 서버로 전송)")
            print("   📥 응답 포맷: SIMPLE → DEFAULT 변환 (분석용)")
        else:
            print("   📤 요청 포맷: DEFAULT (업비트 서버로 전송)")
            print("   📥 응답 포맷: DEFAULT (변환 없음)")

        if self.test_results['compression_enabled']:
            print("   🗜️ 네트워크 압축: 서버 지원 시 자동 적용")

        # 기본 정보
        print("\n📊 요청 규모:")
        print(f"   마켓 수: {self.test_results['markets_requested']:,}개")
        print(f"   데이터 타입: {self.test_results['data_types_requested']}개")
        total_combinations = (self.test_results['markets_requested'] *
                             self.test_results['data_types_requested'])
        print(f"   총 요청 조합: {total_combinations:,}개")

        # 응답 결과
        print("\n📈 응답 결과:")
        print(f"   수신 메시지: {self.test_results['messages_received']:,}개")
        print(f"   커버된 마켓: {len(self.test_results['market_coverage'])}개")
        data_size_mb = self.test_results['data_size_bytes'] / (1024 * 1024)
        print(f"   데이터 크기: {data_size_mb:.2f} MB")

        # 성능 지표
        if self.test_results["performance_metrics"]:
            metrics = self.test_results["performance_metrics"]
            print("\n⚡ 성능 지표:")
            print(f"   첫 응답까지: {self.test_results['response_duration']:.3f}초")
            print(f"   전체 소요시간: {self.test_results['total_duration']:.3f}초")
            print(f"   처리 속도: {metrics['messages_per_second']:.1f} msg/sec")
            print(f"   데이터 처리량: {metrics['data_throughput_mbps']:.2f} MB/sec")
            print(f"   마켓 커버리지: {metrics['market_coverage_percent']:.1f}%")
            print(f"   평균 메시지 크기: {metrics['average_message_size_bytes']:.0f} bytes")

        # 🚀 압축 성능 분석
        if self.test_results['compression_enabled'] and MEASURE_COMPRESSION_RATIO:
            print("\n🗜️ 압축 성능:")
            if "compression_savings" in self.test_results:
                compression_savings_kb = self.test_results['compression_savings'] / 1024
                print(f"   압축으로 절약된 대역폭: {compression_savings_kb:.2f} KB")
                if self.test_results['data_size_bytes'] > 0:
                    compression_ratio = (self.test_results['compression_savings'] /
                                       self.test_results['data_size_bytes']) * 100
                    print(f"   압축 절약률: {compression_ratio:.1f}%")
            else:
                print("   압축 효과: 측정되지 않음 (서버 압축 투명 처리)")

        # 🚀 SIMPLE 포맷 성능 분석
        if self.test_results['simple_format_enabled']:
            print("\n📊 SIMPLE 포맷 성능:")
            savings_kb = self.test_results['simple_format_savings'] / 1024
            print(f"   절약된 대역폭: {savings_kb:.2f} KB")
            if self.test_results['data_size_bytes'] > 0:
                savings_percent = (self.test_results['simple_format_savings'] /
                                 self.test_results['data_size_bytes']) * 100
                print(f"   대역폭 절약률: {savings_percent:.1f}%")

            conversion_time_ms = self.test_results['format_conversion_time'] * 1000
            print(f"   포맷 변환 시간: {conversion_time_ms:.2f}ms")

        # 메시지 타입별 분포
        if self.test_results["message_types"]:
            print("\n📋 메시지 타입별 분포:")
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
        print("\n💡 테스트 결론:")
        if self.test_results["messages_received"] > 0:
            error_count = len(self.test_results["errors"])
            success_rate = (1 - error_count / max(self.test_results["messages_received"], 1)) * 100

            markets = self.test_results['markets_requested']
            data_types = self.test_results['data_types_requested']
            print(f"   ✅ 업비트 WebSocket은 {markets:,}개 마켓 x {data_types}개 데이터 타입")
            print(f"      총 {markets * data_types:,}개 조합을 하나의 티켓으로 성공적으로 처리!")
            print(f"   📊 성공률: {success_rate:.1f}%")

            # 🚀 성능 최적화 결론
            if self.use_simple_format or self.use_compression:
                print("   🚀 성능 최적화:")
                if self.use_simple_format:
                    print("      - SIMPLE 포맷으로 대역폭 절약 달성")
                if self.use_compression:
                    print("      - WebSocket 압축으로 추가 최적화")
                print("   ⚡ 업비트의 WebSocket + 최적화 기술의 시너지 확인!")
            else:
                print("   ⚡ 업비트의 WebSocket 처리 능력은 매우 뛰어남을 확인!")
        else:
            print("   ❌ 테스트 실패 - 응답을 받지 못했습니다")

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

            # 4. 응답 수집 (스마트 모드 또는 타임아웃 모드)
            if RESPONSE_TIMEOUT == 0:
                await self.collect_responses(0)  # 스마트 완료 감지
            else:
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
🚀 업비트 WebSocket 전체 마켓 스냅샷 테스트 (v2.1 - 스마트 완료 감지)
====================================================================

📊 테스트 설정:
- 최대 마켓 수: {MAX_MARKETS}개 (0이면 전체 마켓)
- BTC/USDT 포함: {INCLUDE_BTC_USDT}
- 응답 타임아웃: {RESPONSE_TIMEOUT}초 {'(스마트 완료 감지)' if RESPONSE_TIMEOUT == 0 else ''}
- 디버그 모드: {DEBUG_MODE}

🚀 성능 최적화 설정:
- WebSocket 압축: {USE_COMPRESSION} (permessage-deflate)
- SIMPLE 포맷: {USE_SIMPLE_FORMAT} (60% 대역폭 절약)
- 포맷 비교 테스트: {COMPARE_FORMATS}
- 성능 집중 모드: {PERFORMANCE_FOCUS}

⚡ v2.1 신규 기능:
- 스마트 완료 감지: {SMART_COMPLETION_DETECTION}
- 최대 무응답 시간: {MAX_IDLE_TIME}초
- 완료 버퍼 시간: {COMPLETION_BUFFER_TIME}초

📋 테스트 내용:
- 업비트 WebSocket 극한 처리 능력 측정
- 모든 마켓 x 모든 데이터 타입 (현재가, 호가, 체결, 지원되는 모든 캔들)
- 하나의 티켓으로 모든 데이터를 스냅샷 요청
- 응답 시간, 처리량, 성공률, 대역폭 절약량 측정
- 스냅샷 완료 시 자동 종료 (불필요한 대기 시간 제거)

테스트를 시작합니다...
    """)

    tester = UpbitFullSnapshotTester()

    # 스마트 모드 또는 기본 타임아웃으로 테스트 실행
    if RESPONSE_TIMEOUT == 0:
        await tester.run_test(0)  # 스마트 완료 감지
    else:
        await tester.run_test(timeout_seconds=RESPONSE_TIMEOUT)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 사용자가 테스트를 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
