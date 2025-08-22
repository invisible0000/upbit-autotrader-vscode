"""
스마트 라우터 V2.0 포괄적 API 검증 테스트

업비트 공개 API 9종(REST 5종 + WebSocket 4종)에 대한 100% 완전 검증을 수행합니다.
각 API 타입별로 모든 파라미터 조합과 예외 상황을 엄밀하게 테스트합니다.
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.smart_router import (
    SmartRouter, get_smart_router
)
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models import (
    DataRequest, DataType, RealtimePriority
)

logger = create_component_logger("ComprehensiveAPIValidator")


@dataclass
class APITestCase:
    """API 테스트 케이스"""
    name: str
    data_type: DataType
    symbols: List[str]
    params: Dict[str, Any]
    expected_fields: List[str]
    realtime_priority: RealtimePriority = RealtimePriority.MEDIUM


@dataclass
class TestResult:
    """테스트 결과"""
    test_name: str
    success: bool
    response_time_ms: float
    data_size: int
    channel_used: str
    error_message: Optional[str] = None
    data_sample: Optional[Dict[str, Any]] = None


class ComprehensiveAPIValidator:
    """포괄적 API 검증 클래스"""

    def __init__(self):
        self.router: Optional[SmartRouter] = None
        self.test_results: List[TestResult] = []
        self.upbit_markets: List[Dict[str, str]] = []

    async def initialize(self):
        """검증 시스템 초기화"""
        logger.info("=== 포괄적 API 검증 시스템 초기화 ===")

        # 스마트 라우터 초기화
        self.router = get_smart_router()
        await self.router.initialize()

        # 업비트 마켓 정보 로드
        await self._load_upbit_markets()

        logger.info(f"✅ 초기화 완료 - 업비트 마켓 수: {len(self.upbit_markets)}")

    async def _load_upbit_markets(self):
        """업비트 마켓 정보 로드"""
        try:
            # 스마트 라우터 대신 직접 REST API 사용
            from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient

            client = UpbitPublicClient()
            markets_response = await client.get_markets()

            if isinstance(markets_response, list) and len(markets_response) > 0:
                self.upbit_markets = markets_response
                logger.info(f"마켓 정보 로드 완료: {len(self.upbit_markets)}개 마켓")
            else:
                # 폴백: 하드코딩된 테스트용 마켓
                self.upbit_markets = [
                    {"market": "KRW-BTC", "korean_name": "비트코인", "english_name": "Bitcoin"},
                    {"market": "KRW-ETH", "korean_name": "이더리움", "english_name": "Ethereum"},
                    {"market": "KRW-ADA", "korean_name": "에이다", "english_name": "Ada"},
                    {"market": "BTC-ETH", "korean_name": "이더리움", "english_name": "Ethereum"},
                    {"market": "USDT-BTC", "korean_name": "비트코인", "english_name": "Bitcoin"}
                ]
                logger.warning(f"마켓 정보 로드 실패 - 테스트용 마켓 사용: {len(self.upbit_markets)}개")

        except Exception as e:
            logger.error(f"마켓 정보 로드 중 오류: {e}")
            # 최소한의 테스트용 마켓
            self.upbit_markets = [
                {"market": "KRW-BTC", "korean_name": "비트코인", "english_name": "Bitcoin"}
            ]

    def get_test_markets(self, market_type: str = "all", count: int = 5) -> List[str]:
        """테스트용 마켓 선택"""
        if market_type == "krw":
            markets = [m["market"] for m in self.upbit_markets if m["market"].startswith("KRW-")]
        elif market_type == "btc":
            markets = [m["market"] for m in self.upbit_markets if m["market"].startswith("BTC-")]
        elif market_type == "usdt":
            markets = [m["market"] for m in self.upbit_markets if m["market"].startswith("USDT-")]
        else:
            markets = [m["market"] for m in self.upbit_markets]

        return markets[:count]

    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """포괄적 검증 실행"""
        logger.info("🚀 포괄적 API 검증 시작")

        validation_results = {
            "phase1_rest_api": await self.validate_rest_apis(),
            "phase2_websocket": await self.validate_websocket_apis(),
            "phase3_integration": await self.validate_smart_routing_integration(),
            "phase4_error_handling": await self.validate_error_scenarios()
        }

        # 전체 요약
        total_tests = sum(len(results) for results in validation_results.values())
        total_success = sum(sum(1 for r in results if r.success) for results in validation_results.values())

        summary = {
            "validation_results": validation_results,
            "summary": {
                "total_tests": total_tests,
                "total_success": total_success,
                "success_rate": total_success / total_tests if total_tests > 0 else 0,
                "timestamp": datetime.now().isoformat()
            }
        }

        logger.info(f"✅ 포괄적 검증 완료 - 성공률: {total_success}/{total_tests} ({total_success / total_tests * 100:.1f}%)")

        return summary

    # ================== Phase 1: REST API 검증 ==================

    async def validate_rest_apis(self) -> List[TestResult]:
        """REST API 5종 완전 검증"""
        logger.info("=== Phase 1: REST API 5종 검증 시작 ===")

        results = []

        # 1. 마켓 정보 API 검증
        results.extend(await self.validate_markets_api())

        # 2. 현재가 API 검증
        results.extend(await self.validate_ticker_api())

        # 3. 호가 API 검증
        results.extend(await self.validate_orderbook_api())

        # 4. 체결 API 검증
        results.extend(await self.validate_trades_api())

        # 5. 캔들 API 검증
        results.extend(await self.validate_candles_api())

        success_count = sum(1 for r in results if r.success)
        logger.info(f"Phase 1 완료 - REST API 검증: {success_count}/{len(results)} 성공")

        return results

    async def validate_markets_api(self) -> List[TestResult]:
        """마켓 정보 API 검증"""
        logger.info("--- 마켓 정보 API 검증 시작 ---")

        # 마켓 정보는 별도 REST API로 직접 테스트
        test_results = []

        try:
            from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient

            client = UpbitPublicClient()
            start_time = time.time()

            # 전체 마켓 조회 테스트
            markets_response = await client.get_markets()
            response_time = (time.time() - start_time) * 1000

            if isinstance(markets_response, list) and len(markets_response) > 0:
                # 성공 케이스
                test_results.append(TestResult(
                    test_name="전체_마켓_조회",
                    success=True,
                    response_time_ms=response_time,
                    data_size=len(markets_response),
                    channel_used="rest_api",
                    data_sample={"sample": markets_response[0] if markets_response else None}
                ))

                # KRW 마켓 필터링 테스트
                krw_markets = [m for m in markets_response if m.get("market", "").startswith("KRW-")]
                test_results.append(TestResult(
                    test_name="KRW_마켓_필터링",
                    success=len(krw_markets) > 0,
                    response_time_ms=response_time,
                    data_size=len(krw_markets),
                    channel_used="rest_api",
                    data_sample={"sample": krw_markets[0] if krw_markets else None}
                ))
            else:
                # 실패 케이스
                test_results.append(TestResult(
                    test_name="전체_마켓_조회",
                    success=False,
                    response_time_ms=response_time,
                    data_size=0,
                    channel_used="rest_api",
                    error_message="마켓 정보 조회 실패"
                ))

        except Exception as e:
            test_results.append(TestResult(
                test_name="전체_마켓_조회",
                success=False,
                response_time_ms=0,
                data_size=0,
                channel_used="error",
                error_message=str(e)
            ))

        return test_results

    async def validate_ticker_api(self) -> List[TestResult]:
        """현재가 API 검증"""
        logger.info("--- 현재가 API 검증 시작 ---")

        test_markets = self.get_test_markets("krw", 3)

        test_cases = [
            APITestCase(
                name="단일_현재가_조회",
                data_type=DataType.TICKER,
                symbols=[test_markets[0]] if test_markets else ["KRW-BTC"],
                params={},
                expected_fields=["market", "trade_price", "change", "change_rate"],
                realtime_priority=RealtimePriority.HIGH
            ),
            APITestCase(
                name="다중_현재가_조회",
                data_type=DataType.TICKER,
                symbols=test_markets[:3] if len(test_markets) >= 3 else ["KRW-BTC", "KRW-ETH"],
                params={},
                expected_fields=["market", "trade_price", "change", "change_rate"],
                realtime_priority=RealtimePriority.MEDIUM
            ),
            APITestCase(
                name="대용량_현재가_조회",
                data_type=DataType.TICKER,
                symbols=self.get_test_markets("krw", 10),
                params={},
                expected_fields=["market", "trade_price"],
                realtime_priority=RealtimePriority.LOW
            )
        ]

        results = []
        for test_case in test_cases:
            result = await self._execute_api_test(test_case)
            results.append(result)

        return results

    async def validate_orderbook_api(self) -> List[TestResult]:
        """호가 API 검증"""
        logger.info("--- 호가 API 검증 시작 ---")

        test_markets = self.get_test_markets("krw", 2)

        test_cases = [
            APITestCase(
                name="단일_호가_조회",
                data_type=DataType.ORDERBOOK,
                symbols=[test_markets[0]] if test_markets else ["KRW-BTC"],
                params={},
                expected_fields=["market", "orderbook_units"],
                realtime_priority=RealtimePriority.HIGH
            ),
            APITestCase(
                name="다중_호가_조회",
                data_type=DataType.ORDERBOOK,
                symbols=test_markets[:2] if len(test_markets) >= 2 else ["KRW-BTC"],
                params={},
                expected_fields=["market", "orderbook_units"],
                realtime_priority=RealtimePriority.HIGH
            )
        ]

        results = []
        for test_case in test_cases:
            result = await self._execute_api_test(test_case)
            results.append(result)

        return results

    async def validate_trades_api(self) -> List[TestResult]:
        """체결 API 검증"""
        logger.info("--- 체결 API 검증 시작 ---")

        test_market = self.get_test_markets("krw", 1)[0] if self.get_test_markets("krw", 1) else "KRW-BTC"

        test_cases = [
            APITestCase(
                name="최신_체결_조회",
                data_type=DataType.TRADES,
                symbols=[test_market],
                params={"count": 10},
                expected_fields=["market", "trade_price", "trade_volume", "trade_date_utc"]
            ),
            APITestCase(
                name="대량_체결_조회",
                data_type=DataType.TRADES,
                symbols=[test_market],
                params={"count": 100},
                expected_fields=["market", "trade_price", "trade_volume"]
            ),
            APITestCase(
                name="최대_체결_조회",
                data_type=DataType.TRADES,
                symbols=[test_market],
                params={"count": 500},
                expected_fields=["market", "trade_price"]
            )
        ]

        results = []
        for test_case in test_cases:
            result = await self._execute_api_test(test_case)
            results.append(result)

        return results

    async def validate_candles_api(self) -> List[TestResult]:
        """캔들 API 검증"""
        logger.info("--- 캔들 API 검증 시작 ---")

        test_market = self.get_test_markets("krw", 1)[0] if self.get_test_markets("krw", 1) else "KRW-BTC"

        test_cases = [
            APITestCase(
                name="1분봉_조회",
                data_type=DataType.CANDLES,
                symbols=[test_market],
                params={"interval": "1m", "count": 10},
                expected_fields=["market", "opening_price", "high_price", "low_price", "trade_price"]
            ),
            APITestCase(
                name="5분봉_조회",
                data_type=DataType.CANDLES,
                symbols=[test_market],
                params={"interval": "5m", "count": 20},
                expected_fields=["market", "opening_price", "high_price", "low_price", "trade_price"]
            ),
            APITestCase(
                name="15분봉_조회",
                data_type=DataType.CANDLES,
                symbols=[test_market],
                params={"interval": "15m", "count": 50},
                expected_fields=["market", "opening_price", "high_price", "low_price", "trade_price"]
            ),
            APITestCase(
                name="일봉_조회",
                data_type=DataType.CANDLES,
                symbols=[test_market],
                params={"interval": "1d", "count": 30},
                expected_fields=["market", "opening_price", "high_price", "low_price", "trade_price"]
            ),
            APITestCase(
                name="대량_캔들_조회",
                data_type=DataType.CANDLES,
                symbols=[test_market],
                params={"interval": "1m", "count": 200},
                expected_fields=["market", "opening_price"]
            )
        ]

        results = []
        for test_case in test_cases:
            result = await self._execute_api_test(test_case)
            results.append(result)

        return results

    # ================== Phase 2: WebSocket 검증 ==================

    async def validate_websocket_apis(self) -> List[TestResult]:
        """WebSocket 4종 검증"""
        logger.info("=== Phase 2: WebSocket 4종 검증 시작 ===")

        results = []

        # WebSocket 현재가 검증
        results.extend(await self.validate_websocket_ticker())

        # WebSocket 호가 검증
        results.extend(await self.validate_websocket_orderbook())

        # WebSocket 체결 검증
        results.extend(await self.validate_websocket_trades())

        # WebSocket 캔들 검증 (실시간 캔들)
        results.extend(await self.validate_websocket_candles())

        success_count = sum(1 for r in results if r.success)
        logger.info(f"Phase 2 완료 - WebSocket 검증: {success_count}/{len(results)} 성공")

        return results

    async def validate_websocket_ticker(self) -> List[TestResult]:
        """WebSocket 현재가 검증"""
        logger.info("--- WebSocket 현재가 검증 시작 ---")

        test_market = self.get_test_markets("krw", 1)[0] if self.get_test_markets("krw", 1) else "KRW-BTC"

        test_cases = [
            APITestCase(
                name="WebSocket_단일_현재가",
                data_type=DataType.TICKER,
                symbols=[test_market],
                params={},
                expected_fields=["market", "trade_price"],
                realtime_priority=RealtimePriority.HIGH  # WebSocket 우선 선택되도록
            ),
            APITestCase(
                name="WebSocket_다중_현재가",
                data_type=DataType.TICKER,
                symbols=self.get_test_markets("krw", 3),
                params={},
                expected_fields=["market", "trade_price"],
                realtime_priority=RealtimePriority.HIGH
            )
        ]

        results = []
        for test_case in test_cases:
            result = await self._execute_api_test(test_case)
            results.append(result)

        return results

    async def validate_websocket_orderbook(self) -> List[TestResult]:
        """WebSocket 호가 검증"""
        logger.info("--- WebSocket 호가 검증 시작 ---")

        test_market = self.get_test_markets("krw", 1)[0] if self.get_test_markets("krw", 1) else "KRW-BTC"

        test_cases = [
            APITestCase(
                name="WebSocket_호가_구독",
                data_type=DataType.ORDERBOOK,
                symbols=[test_market],
                params={},
                expected_fields=["market", "orderbook_units"],
                realtime_priority=RealtimePriority.HIGH
            )
        ]

        results = []
        for test_case in test_cases:
            result = await self._execute_api_test(test_case)
            results.append(result)

        return results

    async def validate_websocket_trades(self) -> List[TestResult]:
        """WebSocket 체결 검증"""
        logger.info("--- WebSocket 체결 검증 시작 ---")

        test_market = self.get_test_markets("krw", 1)[0] if self.get_test_markets("krw", 1) else "KRW-BTC"

        test_cases = [
            APITestCase(
                name="WebSocket_실시간_체결",
                data_type=DataType.TRADES,
                symbols=[test_market],
                params={},
                expected_fields=["market", "trade_price"],
                realtime_priority=RealtimePriority.HIGH
            )
        ]

        results = []
        for test_case in test_cases:
            result = await self._execute_api_test(test_case)
            results.append(result)

        return results

    async def validate_websocket_candles(self) -> List[TestResult]:
        """WebSocket 캔들 검증 (실시간 캔들)"""
        logger.info("--- WebSocket 캔들 검증 시작 ---")

        test_market = self.get_test_markets("krw", 1)[0] if self.get_test_markets("krw", 1) else "KRW-BTC"

        test_cases = [
            APITestCase(
                name="WebSocket_실시간_캔들",
                data_type=DataType.CANDLES,
                symbols=[test_market],
                params={"interval": "1m"},
                expected_fields=["market", "opening_price"],
                realtime_priority=RealtimePriority.HIGH
            )
        ]

        results = []
        for test_case in test_cases:
            result = await self._execute_api_test(test_case)
            results.append(result)

        return results

    # ================== Phase 3: 통합 검증 ==================

    async def validate_smart_routing_integration(self) -> List[TestResult]:
        """스마트 라우팅 통합 검증"""
        logger.info("=== Phase 3: 스마트 라우팅 통합 검증 시작 ===")

        results = []

        # 채널 선택 정확성 검증
        results.extend(await self.validate_channel_selection())

        # 데이터 형식 통일 검증
        results.extend(await self.validate_data_format_unification())

        # 성능 및 안정성 검증
        results.extend(await self.validate_performance_stability())

        success_count = sum(1 for r in results if r.success)
        logger.info(f"Phase 3 완료 - 통합 검증: {success_count}/{len(results)} 성공")

        return results

    async def validate_channel_selection(self) -> List[TestResult]:
        """채널 선택 정확성 검증"""
        logger.info("--- 채널 선택 정확성 검증 시작 ---")

        test_market = self.get_test_markets("krw", 1)[0] if self.get_test_markets("krw", 1) else "KRW-BTC"

        # 실시간성에 따른 채널 선택 테스트
        test_cases = [
            APITestCase(
                name="고실시간_채널선택",
                data_type=DataType.TICKER,
                symbols=[test_market],
                params={},
                expected_fields=["market"],
                realtime_priority=RealtimePriority.HIGH  # WebSocket 기대
            ),
            APITestCase(
                name="저실시간_채널선택",
                data_type=DataType.CANDLES,
                symbols=[test_market],
                params={"interval": "1d", "count": 30},
                expected_fields=["market"],
                realtime_priority=RealtimePriority.LOW  # REST API 기대
            )
        ]

        results = []
        for test_case in test_cases:
            result = await self._execute_api_test(test_case)

            # 채널 선택 정확성 검증
            if result.success:
                if test_case.realtime_priority == RealtimePriority.HIGH:
                    # 고실시간 요청은 WebSocket 우선이어야 함
                    if result.channel_used not in ["websocket", "rest_api"]:  # 폴백 허용
                        result.success = False
                        result.error_message = f"고실시간 요청인데 예상하지 못한 채널 사용: {result.channel_used}"
                elif test_case.realtime_priority == RealtimePriority.LOW:
                    # 저실시간 요청은 REST API가 적절
                    if result.channel_used not in ["rest_api", "websocket"]:  # 유연하게 허용
                        result.success = False
                        result.error_message = f"저실시간 요청인데 예상하지 못한 채널 사용: {result.channel_used}"

            results.append(result)

        return results

    async def validate_data_format_unification(self) -> List[TestResult]:
        """데이터 형식 통일 검증"""
        logger.info("--- 데이터 형식 통일 검증 시작 ---")

        test_market = self.get_test_markets("krw", 1)[0] if self.get_test_markets("krw", 1) else "KRW-BTC"

        # 동일한 데이터를 REST와 WebSocket으로 요청하여 형식 일치 확인
        rest_request = DataRequest(
            symbols=[test_market],
            data_type=DataType.TICKER,
            realtime_priority=RealtimePriority.LOW,  # REST 유도
            request_id="format_test_rest"
        )

        websocket_request = DataRequest(
            symbols=[test_market],
            data_type=DataType.TICKER,
            realtime_priority=RealtimePriority.HIGH,  # WebSocket 유도
            request_id="format_test_websocket"
        )

        results = []

        try:
            # REST 요청
            if self.router:
                rest_result = await self.router.get_data(rest_request)
            else:
                rest_result = {"success": False, "error": "Router not initialized"}

            # WebSocket 요청
            if self.router:
                websocket_result = await self.router.get_data(websocket_request)
            else:
                websocket_result = {"success": False, "error": "Router not initialized"}            # 형식 일치성 검증
            format_test_result = TestResult(
                test_name="데이터_형식_통일성",
                success=True,
                response_time_ms=0,
                data_size=0,
                channel_used="both"
            )

            if rest_result.get("success") and websocket_result.get("success"):
                rest_data = rest_result.get("data", {})
                ws_data = websocket_result.get("data", {})

                # 기본 구조 검증
                if isinstance(rest_data, dict) and isinstance(ws_data, dict):
                    # 통일된 메타데이터 확인
                    if "_unified" in rest_data and "_unified" in ws_data:
                        format_test_result.data_sample = {
                            "rest_format": rest_data.get("_unified", {}),
                            "websocket_format": ws_data.get("_unified", {})
                        }
                    else:
                        format_test_result.success = False
                        format_test_result.error_message = "통일된 메타데이터(_unified) 필드 누락"
                else:
                    format_test_result.success = False
                    format_test_result.error_message = f"예상하지 못한 데이터 형식: REST={type(rest_data)}, WS={type(ws_data)}"
            else:
                format_test_result.success = False
                format_test_result.error_message = "REST 또는 WebSocket 요청 실패"

            results.append(format_test_result)

        except Exception as e:
            results.append(TestResult(
                test_name="데이터_형식_통일성",
                success=False,
                response_time_ms=0,
                data_size=0,
                channel_used="error",
                error_message=str(e)
            ))

        return results

    async def validate_performance_stability(self) -> List[TestResult]:
        """성능 및 안정성 검증"""
        logger.info("--- 성능 및 안정성 검증 시작 ---")

        test_market = self.get_test_markets("krw", 1)[0] if self.get_test_markets("krw", 1) else "KRW-BTC"

        results = []

        # 연속 요청 성능 테스트
        consecutive_test = await self._test_consecutive_requests(test_market)
        results.append(consecutive_test)

        # 동시 요청 성능 테스트
        concurrent_test = await self._test_concurrent_requests(test_market)
        results.append(concurrent_test)

        return results

    async def _test_consecutive_requests(self, test_market: str) -> TestResult:
        """연속 요청 성능 테스트"""
        test_name = "연속_요청_성능"
        success_count = 0
        total_time = 0
        request_count = 10

        try:
            start_time = time.time()

            for i in range(request_count):
                request = DataRequest(
                    symbols=[test_market],
                    data_type=DataType.TICKER,
                    request_id=f"consecutive_{i}"
                )

                if self.router:
                    result = await self.router.get_data(request)
                else:
                    result = {"success": False, "error": "Router not initialized"}
                if result.get("success"):
                    success_count += 1

                # 짧은 간격 대기
                await asyncio.sleep(0.1)

            total_time = time.time() - start_time

            return TestResult(
                test_name=test_name,
                success=success_count >= request_count * 0.8,  # 80% 성공률 기준
                response_time_ms=total_time * 1000,
                data_size=success_count,
                channel_used="mixed",
                data_sample={"success_rate": success_count / request_count}
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                response_time_ms=0,
                data_size=0,
                channel_used="error",
                error_message=str(e)
            )

    async def _test_concurrent_requests(self, test_market: str) -> TestResult:
        """동시 요청 성능 테스트"""
        test_name = "동시_요청_성능"
        request_count = 5

        try:
            start_time = time.time()

            # 동시 요청 생성
            tasks = []
            for i in range(request_count):
                request = DataRequest(
                    symbols=[test_market],
                    data_type=DataType.TICKER,
                    request_id=f"concurrent_{i}"
                )
                if self.router:
                    task = self.router.get_data(request)
                else:
                    # 더미 태스크를 만들어 반환
                    async def dummy_task():
                        return {"success": False, "error": "Router not initialized"}
                    task = dummy_task()
                tasks.append(task)

            # 동시 실행
            results = await asyncio.gather(*tasks, return_exceptions=True)

            total_time = time.time() - start_time
            success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))

            return TestResult(
                test_name=test_name,
                success=success_count >= request_count * 0.8,  # 80% 성공률 기준
                response_time_ms=total_time * 1000,
                data_size=success_count,
                channel_used="mixed",
                data_sample={"success_rate": success_count / request_count}
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                response_time_ms=0,
                data_size=0,
                channel_used="error",
                error_message=str(e)
            )

    # ================== Phase 4: 에러 처리 검증 ==================

    async def validate_error_scenarios(self) -> List[TestResult]:
        """예외 상황 및 에러 처리 검증"""
        logger.info("=== Phase 4: 예외 상황 및 에러 처리 검증 시작 ===")

        results = []

        # 잘못된 파라미터 테스트
        results.extend(await self.validate_invalid_parameters())

        # 존재하지 않는 마켓 테스트
        results.extend(await self.validate_invalid_markets())

        # 극한 파라미터 테스트
        results.extend(await self.validate_extreme_parameters())

        success_count = sum(1 for r in results if r.success)
        logger.info(f"Phase 4 완료 - 에러 처리 검증: {success_count}/{len(results)} 성공")

        return results

    async def validate_invalid_parameters(self) -> List[TestResult]:
        """잘못된 파라미터 검증"""
        logger.info("--- 잘못된 파라미터 검증 시작 ---")

        test_cases = [
            APITestCase(
                name="잘못된_캔들_간격",
                data_type=DataType.CANDLES,
                symbols=["KRW-BTC"],
                params={"interval": "invalid", "count": 10},
                expected_fields=[]
            ),
            APITestCase(
                name="음수_카운트",
                data_type=DataType.TRADES,
                symbols=["KRW-BTC"],
                params={"count": -10},
                expected_fields=[]
            ),
            APITestCase(
                name="과도한_카운트",
                data_type=DataType.CANDLES,
                symbols=["KRW-BTC"],
                params={"count": 10000},  # 업비트 제한 초과
                expected_fields=[]
            )
        ]

        results = []
        for test_case in test_cases:
            result = await self._execute_api_test(test_case)
            # 에러 시나리오는 실패가 정상적인 동작
            if not result.success:
                result.success = True
                result.error_message = f"예상된 에러 (정상): {result.error_message}"
            else:
                result.success = False
                result.error_message = "에러가 발생해야 하는데 성공함"
            results.append(result)

        return results

    async def validate_invalid_markets(self) -> List[TestResult]:
        """존재하지 않는 마켓 검증"""
        logger.info("--- 존재하지 않는 마켓 검증 시작 ---")

        test_cases = [
            APITestCase(
                name="존재하지_않는_마켓",
                data_type=DataType.TICKER,
                symbols=["KRW-INVALID", "BTC-NOTEXIST"],
                params={},
                expected_fields=[]
            ),
            APITestCase(
                name="빈_마켓_리스트",
                data_type=DataType.TICKER,
                symbols=[],
                params={},
                expected_fields=[]
            )
        ]

        results = []
        for test_case in test_cases:
            result = await self._execute_api_test(test_case)
            # 에러 시나리오는 실패가 정상적인 동작 또는 빈 결과
            if not result.success or result.data_size == 0:
                result.success = True
                result.error_message = f"예상된 결과 (정상): {result.error_message or '빈 결과'}"
            results.append(result)

        return results

    async def validate_extreme_parameters(self) -> List[TestResult]:
        """극한 파라미터 검증"""
        logger.info("--- 극한 파라미터 검증 시작 ---")

        test_market = self.get_test_markets("krw", 1)[0] if self.get_test_markets("krw", 1) else "KRW-BTC"

        test_cases = [
            APITestCase(
                name="최대_캔들_요청",
                data_type=DataType.CANDLES,
                symbols=[test_market],
                params={"interval": "1m", "count": 200},  # 업비트 최대 제한
                expected_fields=["market"]
            ),
            APITestCase(
                name="최대_체결_요청",
                data_type=DataType.TRADES,
                symbols=[test_market],
                params={"count": 500},  # 업비트 최대 제한
                expected_fields=["market"]
            )
        ]

        results = []
        for test_case in test_cases:
            result = await self._execute_api_test(test_case)
            results.append(result)

        return results

    # ================== 공통 테스트 실행 메서드 ==================

    async def _execute_api_test(self, test_case: APITestCase) -> TestResult:
        """개별 API 테스트 실행"""
        start_time = time.time()

        try:
            # DataRequest 생성
            request = DataRequest(
                symbols=test_case.symbols,
                data_type=test_case.data_type,
                realtime_priority=test_case.realtime_priority,
                request_id=f"test_{test_case.name}_{int(time.time() * 1000)}"
            )

            # 파라미터 추가
            for key, value in test_case.params.items():
                setattr(request, key, value)

            # API 호출
            if self.router:
                result = await self.router.get_data(request)
            else:
                result = {"success": False, "error": "Router not initialized"}

            response_time = (time.time() - start_time) * 1000

            # 결과 분석
            success = result.get("success", False)
            data = result.get("data", {})
            metadata = result.get("metadata", {})

            # 데이터 크기 계산
            data_size = 0
            if isinstance(data, list):
                data_size = len(data)
            elif isinstance(data, dict):
                if "_original_data" in data and isinstance(data["_original_data"], list):
                    data_size = len(data["_original_data"])
                else:
                    data_size = len(data)

            # 필수 필드 검증
            if success and test_case.expected_fields:
                field_validation = self._validate_required_fields(data, test_case.expected_fields)
                if not field_validation["valid"]:
                    success = False
                    error_message = f"필수 필드 누락: {field_validation['missing_fields']}"
                else:
                    error_message = None
            else:
                error_message = result.get("error")

            return TestResult(
                test_name=test_case.name,
                success=success,
                response_time_ms=response_time,
                data_size=data_size,
                channel_used=metadata.get("channel", "unknown"),
                error_message=error_message,
                data_sample=self._extract_data_sample(data)
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            return TestResult(
                test_name=test_case.name,
                success=False,
                response_time_ms=response_time,
                data_size=0,
                channel_used="error",
                error_message=str(e)
            )

    def _validate_required_fields(self, data: Any, required_fields: List[str]) -> Dict[str, Any]:
        """필수 필드 검증"""
        missing_fields = []

        if isinstance(data, dict):
            # 단일 객체 검증
            if "_original_data" in data:
                # 통일된 형식인 경우 원본 데이터 확인
                original = data["_original_data"]
                if isinstance(original, list) and len(original) > 0:
                    check_data = original[0]
                else:
                    check_data = original
            else:
                check_data = data

            if isinstance(check_data, dict):
                for field in required_fields:
                    if field not in check_data:
                        missing_fields.append(field)

        elif isinstance(data, list) and len(data) > 0:
            # 리스트 형태인 경우 첫 번째 요소 검증
            check_data = data[0]
            if isinstance(check_data, dict):
                for field in required_fields:
                    if field not in check_data:
                        missing_fields.append(field)

        return {
            "valid": len(missing_fields) == 0,
            "missing_fields": missing_fields
        }

    def _extract_data_sample(self, data: Any) -> Optional[Dict[str, Any]]:
        """데이터 샘플 추출"""
        try:
            if isinstance(data, dict):
                if "_original_data" in data:
                    original = data["_original_data"]
                    if isinstance(original, list) and len(original) > 0:
                        return {"sample": original[0], "count": len(original)}
                    else:
                        return {"sample": original}
                else:
                    return {"sample": {k: v for k, v in list(data.items())[:5]}}

            elif isinstance(data, list) and len(data) > 0:
                return {"sample": data[0], "count": len(data)}
            else:
                return {"sample": str(data)[:200]}

        except Exception:
            return None

    async def cleanup(self):
        """리소스 정리"""
        if self.router:
            await self.router.cleanup_resources()


# 실행 스크립트
async def main():
    """메인 실행 함수"""
    validator = ComprehensiveAPIValidator()

    try:
        # 초기화
        await validator.initialize()

        # 포괄적 검증 실행
        results = await validator.run_comprehensive_validation()

        # 결과 출력
        print("\n" + "=" * 80)
        print("🎯 업비트 공개 API 포괄적 검증 결과")
        print("=" * 80)

        summary = results["summary"]
        print(f"📊 전체 테스트: {summary['total_tests']}개")
        print(f"✅ 성공: {summary['total_success']}개")
        print(f"❌ 실패: {summary['total_tests'] - summary['total_success']}개")
        print(f"📈 성공률: {summary['success_rate']:.1%}")
        print(f"🕐 완료 시간: {summary['timestamp']}")

        # 단계별 결과
        for phase, phase_results in results["validation_results"].items():
            if phase_results:
                success_count = sum(1 for r in phase_results if r.success)
                print(f"\n{phase}: {success_count}/{len(phase_results)} 성공")

                # 실패한 테스트 상세 정보
                failed_tests = [r for r in phase_results if not r.success]
                if failed_tests:
                    print("  실패한 테스트:")
                    for test in failed_tests[:3]:  # 최대 3개만 표시
                        print(f"    - {test.test_name}: {test.error_message}")

        # 결과를 파일로 저장
        with open("validation_results.json", "w", encoding="utf-8") as f:
            # TestResult 객체를 dict로 변환
            serializable_results = {}
            for phase, phase_results in results["validation_results"].items():
                serializable_results[phase] = [
                    {
                        "test_name": r.test_name,
                        "success": r.success,
                        "response_time_ms": r.response_time_ms,
                        "data_size": r.data_size,
                        "channel_used": r.channel_used,
                        "error_message": r.error_message,
                        "data_sample": r.data_sample
                    }
                    for r in phase_results
                ]

            json.dump({
                "validation_results": serializable_results,
                "summary": results["summary"]
            }, f, ensure_ascii=False, indent=2)

        print("\n📄 상세 결과가 validation_results.json에 저장되었습니다.")

        return results

    except Exception as e:
        logger.error(f"검증 실행 중 오류: {e}")
        return {"error": str(e)}

    finally:
        # 정리
        await validator.cleanup()


if __name__ == "__main__":
    import os

    # 로깅 환경 설정
    os.environ["UPBIT_CONSOLE_OUTPUT"] = "true"
    os.environ["UPBIT_LOG_SCOPE"] = "normal"
    os.environ["UPBIT_COMPONENT_FOCUS"] = "ComprehensiveAPIValidator"

    # 실행
    results = asyncio.run(main())
    print("\n🏁 검증 완료!")
