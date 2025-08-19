"""
MarketDataBackbone V2 - Phase 1.2 WebSocket 통합

전문가 권고사항 적용:
- 하이브리드 통신 모델(WebSocket + REST) 구조 준비
- 사전적 Rate Limiting 시스템
- JWT 인증 강화 고려
- 상태 보정(Reconciliation) 로직 기반 설계
- Queue 기반 디커플링 아키텍처

핵심 원칙:
- 단순함 우선, 기능 구현에 집중
- 기존 클라이언트 래핑 방식
- TDD 접근법
- 점진적 진화
"""

from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from enum import Enum
import asyncio
import time

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_client import UpbitClient


class ProactiveRateLimiter:
    """
    전문가 권고: 사전적 Rate Limiting 시스템

    429 오류 발생 후 대응하는 것이 아니라,
    Remaining-Req 헤더를 통해 사전에 요청 속도를 조절
    """

    def __init__(self):
        self._logger = create_component_logger("ProactiveRateLimiter")
        self._rate_limits = {
            "default": {"sec": 30, "min": 900},  # 기본 그룹
            "order": {"sec": 8, "min": 200}     # 주문 그룹
        }
        self._last_reset_time = time.time()

    def update_from_response_headers(self, headers: dict) -> None:
        """
        API 응답 헤더에서 남은 요청 수 업데이트
        예: Remaining-Req: group=default; min=899; sec=29
        """
        remaining_req = headers.get("Remaining-Req", "")
        if not remaining_req:
            return

        try:
            # 헤더 파싱 로직
            parts = remaining_req.split(";")
            group = None
            for part in parts:
                key, value = part.strip().split("=", 1)
                if key == "group":
                    group = value
                elif key in ["sec", "min"] and group and group in self._rate_limits:
                    self._rate_limits[group][key] = int(value)

            if group:
                self._logger.debug(f"Rate limit 업데이트: {group} = {self._rate_limits.get(group, {})}")

        except Exception as e:
            self._logger.warning(f"Rate limit 헤더 파싱 실패: {e}")

    async def acquire(self, group: str = "default") -> None:
        """
        요청 전에 호출하여 Rate Limit 확인 및 대기
        전문가 권고: 사전적 제어로 429 오류 원천 방지
        """
        if group not in self._rate_limits:
            return

        limits = self._rate_limits[group]
        if limits["sec"] <= 0:
            wait_time = 1.1  # 다음 초까지 대기
            self._logger.info(f"Rate limit 도달, {wait_time}초 대기 중...")
            await asyncio.sleep(wait_time)
            limits["sec"] = self._rate_limits[group]["sec"]  # 리셋


class ChannelStrategy(Enum):
    """채널 선택 전략"""
    AUTO = "auto"
    REST_ONLY = "rest_only"
    WEBSOCKET_ONLY = "websocket_only"


@dataclass(frozen=True)
class TickerData:
    """통합 현재가 데이터 모델"""
    symbol: str
    current_price: Decimal
    change_rate: Decimal  # 변화율 (%)
    change_amount: Decimal  # 변화액
    volume_24h: Decimal
    high_24h: Decimal
    low_24h: Decimal
    prev_closing_price: Decimal
    timestamp: datetime
    source: str  # "rest" 또는 "websocket"


class MarketDataBackbone:
    """
    통합 마켓 데이터 백본 - MVP 구현 (Phase 1.1)

    현재 기능:
    - get_ticker() 메서드만 구현
    - REST API 우선 사용
    - 기본 에러 처리

    Phase 1.2에서 추가 예정:
    - WebSocket 채널 지원
    - 더 많은 데이터 타입
    - 지능적 채널 선택
    """

    def __init__(self):
        """백본 초기화"""
        self._logger = create_component_logger("MarketDataBackbone")
        self._rest_client: Optional[UpbitClient] = None
        self._rate_limiter = ProactiveRateLimiter()
        self._is_initialized = False

        # Phase 1.2: WebSocket 관리자 추가
        self._websocket_manager = None
        self._data_unifier = None
        self._channel_router = None

    async def initialize(self) -> None:
        """백본 시스템 초기화"""
        if self._is_initialized:
            return

        try:
            self._logger.info("MarketDataBackbone 초기화 시작...")

            # REST API 클라이언트 초기화
            self._rest_client = UpbitClient()

            # 간단한 연결 테스트
            await self._test_connection()

            self._is_initialized = True
            self._logger.info("MarketDataBackbone 초기화 완료")

        except Exception as e:
            self._logger.error(f"MarketDataBackbone 초기화 실패: {e}")
            raise

    async def _test_connection(self) -> None:
        """연결 상태 테스트"""
        if not self._rest_client:
            raise RuntimeError("REST 클라이언트가 초기화되지 않았습니다")

        try:
            # 간단한 마켓 정보 조회로 연결 테스트
            markets = await self._rest_client.get_krw_markets()
            if not markets or "KRW-BTC" not in markets:
                raise RuntimeError("업비트 API 연결 테스트 실패")
            self._logger.debug(f"연결 테스트 성공: {len(markets)}개 KRW 마켓 확인")
        except Exception as e:
            self._logger.error(f"연결 테스트 실패: {e}")
            raise

    async def get_ticker(self, symbol: str, strategy: ChannelStrategy = ChannelStrategy.AUTO) -> TickerData:
        """
        현재가 조회 - MVP 구현

        Args:
            symbol: 마켓 심볼 (예: "KRW-BTC")
            strategy: 채널 선택 전략 (Phase 1.1에서는 REST만 지원)

        Returns:
            TickerData: 통합된 현재가 데이터

        Raises:
            ValueError: 잘못된 심볼
            RuntimeError: API 호출 실패
        """
        if not self._is_initialized:
            await self.initialize()

        # 입력 검증
        if not symbol or not isinstance(symbol, str):
            raise ValueError("symbol은 유효한 문자열이어야 합니다")

        symbol = symbol.upper()
        if not symbol.startswith(("KRW-", "BTC-", "ETH-", "USDT-")):
            raise ValueError(f"지원하지 않는 마켓 형식: {symbol}")

        # Phase 1.1에서는 WebSocket 미지원에서 Phase 1.2로 업데이트
        if strategy == ChannelStrategy.WEBSOCKET_ONLY:
            return await self._get_ticker_websocket(symbol)

        try:
            self._logger.debug(f"현재가 조회 시작: {symbol} (전략: {strategy.value})")

            # Rate Limiting 사전 체크 (전문가 권고)
            await self._rate_limiter.acquire("default")

            # 채널 선택 로직
            if strategy == ChannelStrategy.AUTO:
                # AUTO: REST 우선, WebSocket 대체
                try:
                    return await self._get_ticker_rest(symbol)
                except Exception as e:
                    self._logger.warning(f"REST API 실패, WebSocket으로 대체: {symbol} - {e}")
                    return await self._get_ticker_websocket(symbol)
            elif strategy == ChannelStrategy.REST_ONLY:
                return await self._get_ticker_rest(symbol)
            else:  # WEBSOCKET_ONLY
                return await self._get_ticker_websocket(symbol)
            if not self._rest_client:
                raise RuntimeError("REST 클라이언트가 초기화되지 않았습니다")

            tickers = await self._rest_client.get_tickers([symbol])
            if not tickers:
                raise RuntimeError(f"마켓 {symbol}의 현재가 데이터를 찾을 수 없습니다")

            ticker_raw = tickers[0]

            # 데이터 변환 (Phase 1.1 단순 구현)
            ticker_data = self._convert_rest_ticker(ticker_raw)

            self._logger.debug(f"현재가 조회 완료: {symbol} = {ticker_data.current_price:,.0f}원")
            return ticker_data

        except Exception as e:
            self._logger.error(f"현재가 조회 실패 - {symbol}: {e}")
            raise RuntimeError(f"현재가 조회 실패: {e}") from e

    def _convert_rest_ticker(self, raw_data: dict) -> TickerData:
        """REST API 응답을 TickerData로 변환 (Phase 1.1 단순 구현)"""
        try:
            return TickerData(
                symbol=raw_data["market"],
                current_price=Decimal(str(raw_data["trade_price"])),
                change_rate=Decimal(str(raw_data.get("signed_change_rate", 0))) * 100,  # % 단위로 변환
                change_amount=Decimal(str(raw_data.get("signed_change_price", 0))),
                volume_24h=Decimal(str(raw_data.get("acc_trade_volume_24h", 0))),
                high_24h=Decimal(str(raw_data.get("high_price", 0))),
                low_24h=Decimal(str(raw_data.get("low_price", 0))),
                prev_closing_price=Decimal(str(raw_data.get("prev_closing_price", 0))),
                timestamp=datetime.now(),  # Phase 1.1에서는 현재 시간 사용
                source="rest"
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"REST API 응답 데이터 변환 실패: {e}") from e

    async def get_candles(self, symbol: str, timeframe: str, count: int) -> List:
        """캔들 데이터 조회 - Phase 1.2에서 구현 예정"""
        raise NotImplementedError("캔들 데이터 조회는 Phase 1.2에서 구현 예정")

    async def _get_ticker_rest(self, symbol: str) -> TickerData:
        """REST API로 티커 데이터 조회"""
        if not self._rest_client:
            raise RuntimeError("REST 클라이언트가 초기화되지 않았습니다")

        tickers = await self._rest_client.get_tickers([symbol])
        if not tickers:
            raise RuntimeError(f"마켓 {symbol}의 현재가 데이터를 찾을 수 없습니다")

        ticker_raw = tickers[0]
        return self._convert_rest_ticker(ticker_raw)

    async def _get_ticker_websocket(self, symbol: str) -> TickerData:
        """WebSocket으로 티커 데이터 조회 (한 번만)"""
        # WebSocket Manager 초기화
        if not self._websocket_manager:
            from .websocket_manager import WebSocketManager
            self._websocket_manager = WebSocketManager()

        try:
            # 구독 및 첫 번째 메시지 대기
            queue = await self._websocket_manager.subscribe_ticker([symbol])

            # 첫 번째 메시지 대기 (타임아웃 10초)
            ticker_data = await asyncio.wait_for(queue.get(), timeout=10.0)

            return ticker_data

        except asyncio.TimeoutError:
            raise RuntimeError(f"WebSocket 티커 데이터 수신 타임아웃: {symbol}")
        except Exception as e:
            raise RuntimeError(f"WebSocket 티커 조회 실패: {e}") from e

    async def stream_ticker(self, symbols: List[str]) -> AsyncGenerator[TickerData, None]:
        """
        실시간 티커 스트림 (Phase 1.2 새 기능)

        Args:
            symbols: 구독할 심볼 리스트

        Yields:
            TickerData: 실시간 티커 데이터
        """
        # WebSocket Manager 초기화
        if not self._websocket_manager:
            from .websocket_manager import WebSocketManager
            self._websocket_manager = WebSocketManager()

        try:
            self._logger.info(f"실시간 티커 스트림 시작: {symbols}")

            # 구독 시작
            queue = await self._websocket_manager.subscribe_ticker(symbols)

            while True:
                try:
                    # 메시지 수신 (타임아웃 30초)
                    ticker_data = await asyncio.wait_for(queue.get(), timeout=30.0)

                    # 받은 데이터 검증
                    if hasattr(ticker_data, 'symbol'):
                        # 이미 TickerData 객체
                        yield ticker_data
                    else:
                        # 원시 데이터를 TickerData로 변환
                        converted = self._convert_websocket_ticker(ticker_data)
                        yield converted

                except asyncio.TimeoutError:
                    self._logger.warning(f"WebSocket 메시지 타임아웃 (30초): {symbols}")
                    continue
                except Exception as e:
                    self._logger.error(f"스트림 처리 오류: {e}")
                    break

        except Exception as e:
            self._logger.error(f"실시간 티커 스트림 초기화 실패: {e}")
            raise

    async def stream_orderbook(self, symbols: List[str]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        실시간 호가 스트림 (Phase 1.2 새 기능)

        Args:
            symbols: 구독할 심볼 리스트

        Yields:
            Dict: 실시간 호가 데이터
        """
        # WebSocket Manager 초기화
        if not self._websocket_manager:
            from .websocket_manager import WebSocketManager
            self._websocket_manager = WebSocketManager()

        try:
            self._logger.info(f"실시간 호가 스트림 시작: {symbols}")

            # 구독 시작
            queue = await self._websocket_manager.subscribe_orderbook(symbols)

            while True:
                try:
                    # 메시지 수신 (타임아웃 30초)
                    orderbook_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield orderbook_data

                except asyncio.TimeoutError:
                    self._logger.warning(f"WebSocket 호가 메시지 타임아웃 (30초): {symbols}")
                    continue
                except Exception as e:
                    self._logger.error(f"호가 스트림 처리 오류: {e}")
                    break

        except Exception as e:
            self._logger.error(f"실시간 호가 스트림 초기화 실패: {e}")
            raise

    def _convert_websocket_ticker(self, raw_data: Dict[str, Any]) -> TickerData:
        """WebSocket 원시 데이터를 TickerData로 변환"""
        try:
            return TickerData(
                symbol=raw_data.get('code', raw_data.get('market', '')),
                current_price=Decimal(str(raw_data.get('trade_price', 0))),
                change_rate=Decimal(str(raw_data.get('signed_change_rate', 0))) * 100,  # % 단위
                change_amount=Decimal(str(raw_data.get('signed_change_price', 0))),
                volume_24h=Decimal(str(raw_data.get('acc_trade_volume_24h', 0))),
                high_24h=Decimal(str(raw_data.get('high_price', 0))),
                low_24h=Decimal(str(raw_data.get('low_price', 0))),
                prev_closing_price=Decimal(str(raw_data.get('prev_closing_price', 0))),
                timestamp=(datetime.fromtimestamp(raw_data.get('timestamp', 0) / 1000)
                           if raw_data.get('timestamp') else datetime.now()),
                source="websocket"
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"WebSocket 응답 데이터 변환 실패: {e}") from e

    async def get_orderbook(self, symbol: str) -> dict:
        """호가창 조회 - Phase 1.2에서 구현 예정"""
        raise NotImplementedError("호가창 조회는 Phase 1.2에서 구현 예정")

    async def close(self) -> None:
        """리소스 정리"""
        # WebSocket Manager 정리
        if self._websocket_manager:
            await self._websocket_manager.disconnect()
            self._websocket_manager = None

        # REST 클라이언트 정리
        if self._rest_client:
            await self._rest_client.close()

        self._is_initialized = False
        self._logger.info("MarketDataBackbone 리소스 정리 완료")

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.close()


# Phase 1.1 편의 함수
async def get_ticker_simple(symbol: str) -> TickerData:
    """간단한 현재가 조회 함수 - 테스트용"""
    async with MarketDataBackbone() as backbone:
        return await backbone.get_ticker(symbol)
