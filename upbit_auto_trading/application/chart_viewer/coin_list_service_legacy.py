"""
코인 리스트 서비스 (Application Layer) - WebSocket v6 + REST API 통합

차트뷰어 코인 리스트 위젯을 위한 실시간 데이터 서비스입니다.
- REST API: 마켓 목록 조회 (UpbitPublicClient)
- WebSocket v6: 실시간 가격 데이터 (WebSocketClient)
- 캐싱: 메모리 기반 실시간 데이터 관리
- UI 업데이트: 쓰로틀링 기반 최적화
"""

import asyncio
import time
import random
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.core.websocket_client import WebSocketClient


@dataclass(frozen=True)
class CoinInfo:
    """코인 정보 DTO"""
    symbol: str
    name: str
    market: str
    price: str
    price_formatted: str
    change_rate: str
    change_price: str
    volume: str
    volume_raw: float  # 정렬용 원본 거래량
    change_rate_raw: float  # 정렬용 원본 변화율 (음수 포함)
    is_warning: bool = False


class CoinListService:
    """
    코인 리스트 서비스 - WebSocket v6 + REST API 통합

    기능:
    - REST API: 마켓 목록 조회 및 캐싱 (UpbitPublicClient)
    - WebSocket v6: 실시간 티커 데이터 수신 (WebSocketClient)
    - 실시간 캐싱: 메모리 기반 CoinInfo 데이터 관리
    - UI 업데이트: 콜백 기반 실시간 알림
    - 에러 처리: WebSocket 실패 시 REST API 폴백
    """

    def __init__(self):
        """서비스 초기화 - WebSocket v6 기반 실시간 모드"""
        self._logger = create_component_logger("CoinListService")

        # REST API 클라이언트
        self._rest_client: Optional[UpbitPublicClient] = None

        # WebSocket 클라이언트
        self._websocket_client: Optional[WebSocketClient] = None
        self._websocket_active = False

        # 캐시 데이터
        self._markets_cache: List[Dict[str, Any]] = []
        self._tickers_cache: Dict[str, Dict[str, Any]] = {}  # symbol -> ticker_data
        self._coin_info_cache: Dict[str, CoinInfo] = {}     # symbol -> CoinInfo
        self._last_update: Optional[float] = None

        # 구독 관리
        self._subscribed_symbols: List[str] = []
        self._subscription_active = False

        # UI 콜백
        self._update_callbacks: List[Callable[[List[CoinInfo]], None]] = []

        # 실시간 모드 플래그 (WebSocket 우선, REST 폴백)
        self._realtime_mode = True

        self._logger.info("🪙 코인 리스트 서비스 초기화 완료 (🚀 WebSocket v6 + REST API 실시간 모드)")

    async def initialize(self) -> bool:
        """
        서비스 초기화 - REST API 클라이언트 생성

        Returns:
            bool: 초기화 성공 여부
        """
        try:
            self._logger.info("🔧 CoinListService 초기화 시작...")

            # REST API 클라이언트 생성
            self._rest_client = UpbitPublicClient()
            self._logger.info("✅ UpbitPublicClient 초기화 완료")

            # 마켓 목록 사전 로드
            await self._load_markets_cache()

            self._logger.info("🚀 CoinListService 초기화 완료")
            return True

        except Exception as e:
            self._logger.error(f"❌ 서비스 초기화 실패: {e}")
            return False

    async def start_realtime_updates(self, symbols: List[str]) -> bool:
        """
        실시간 업데이트 시작 - WebSocket v6 구독

        Args:
            symbols: 구독할 심볼 목록 (예: ['KRW-BTC', 'KRW-ETH'])

        Returns:
            bool: 구독 시작 성공 여부
        """
        try:
            self._logger.info(f"📡 실시간 업데이트 시작: {len(symbols)}개 심볼")

            # 기존 WebSocket 정리
            await self._cleanup_websocket()

            # 새 WebSocket 클라이언트 생성
            self._websocket_client = WebSocketClient(f"coin_list_service_{int(time.time() * 1000)}")

            # 티커 구독 (검증된 패턴 활용)
            success = await self._websocket_client.subscribe_ticker(
                symbols=symbols,
                callback=self._on_ticker_update
            )

            if success:
                self._subscribed_symbols = symbols.copy()
                self._subscription_active = True
                self._websocket_active = True
                self._last_update = time.time()

                self._logger.info(f"✅ 실시간 구독 성공: {len(symbols)}개 심볼")
                return True
            else:
                self._logger.error("❌ WebSocket 구독 실패")
                return False

        except Exception as e:
            self._logger.error(f"❌ 실시간 업데이트 시작 실패: {e}")
            await self._cleanup_websocket()
            return False

    async def _load_markets_cache(self) -> None:
        """마켓 목록 캐시 로드 - REST API 활용"""
        try:
            self._logger.debug("📊 업비트 마켓 목록 조회 중...")

            if not self._rest_client:
                raise RuntimeError("REST 클라이언트가 초기화되지 않았습니다")

            # 실제 업비트 마켓 목록 조회
            markets_data = await self._rest_client.get_markets()
            self._markets_cache = markets_data

            # 마켓별 통계
            krw_count = len([m for m in markets_data if m['market'].startswith('KRW-')])
            btc_count = len([m for m in markets_data if m['market'].startswith('BTC-')])
            usdt_count = len([m for m in markets_data if m['market'].startswith('USDT-')])

            self._logger.info(
                f"✅ 실제 마켓 목록 로드 완료: 총 {len(markets_data)}개 "
                f"(KRW: {krw_count}, BTC: {btc_count}, USDT: {usdt_count})"
            )

        except Exception as e:
            self._logger.error(f"❌ 마켓 목록 로드 실패: {e}")
            # 실패 시 샘플 데이터로 폴백
            self._markets_cache = self._create_sample_markets_data()
            self._logger.warning("⚠️ 샘플 데이터로 폴백")

    def _on_ticker_update(self, ticker_event) -> None:
        """
        WebSocket 티커 업데이트 콜백 - 검증된 패턴 활용

        Args:
            ticker_event: WebSocket에서 수신한 티커 이벤트
        """
        try:
            # 디버깅: 콜백 호출 확인
            self._logger.debug(f"📨 WebSocket 콜백 호출됨: {type(ticker_event)}")

            if not hasattr(ticker_event, 'symbol'):
                self._logger.warning("⚠️ 티커 이벤트에 symbol 속성 없음")
                return

            symbol = ticker_event.symbol
            self._logger.debug(f"📊 티커 업데이트 수신: {symbol}")

            # 티커 데이터 캐시 업데이트
            ticker_data = {
                'market': symbol,
                'trade_price': getattr(ticker_event, 'trade_price', 0),
                'change_rate': getattr(ticker_event, 'change_rate', 0),
                'change_price': getattr(ticker_event, 'change_price', 0),
                'change': getattr(ticker_event, 'change', 'EVEN'),
                'acc_trade_price_24h': getattr(ticker_event, 'acc_trade_price_24h', 0),
                'opening_price': getattr(ticker_event, 'opening_price', 0),
                'high_price': getattr(ticker_event, 'high_price', 0),
                'low_price': getattr(ticker_event, 'low_price', 0),
                'prev_closing_price': getattr(ticker_event, 'prev_closing_price', 0),
                'timestamp': getattr(ticker_event, 'timestamp', int(time.time() * 1000)),
            }

            self._tickers_cache[symbol] = ticker_data

            # CoinInfo 업데이트
            market_info = next((m for m in self._markets_cache if m['market'] == symbol), None)
            if market_info:
                coin_info = self._create_coin_info(market_info, ticker_data)
                self._coin_info_cache[symbol] = coin_info

            # UI 콜백 호출 (쓰로틀링 적용)
            self._trigger_ui_update()

            # 디버그 로깅 (5개마다)
            stream_type = getattr(ticker_event, 'stream_type', 'UNKNOWN')
            if len(self._tickers_cache) % 5 == 1:
                price = ticker_data['trade_price']
                self._logger.debug(f"📊 {stream_type} 업데이트: {symbol} = {price:,}원")

        except Exception as e:
            self._logger.warning(f"⚠️ 티커 업데이트 처리 중 오류: {symbol} - {e}")

    def _trigger_ui_update(self) -> None:
        """UI 업데이트 트리거 (쓰로틀링 적용)"""
        try:
            # 현재 캐시된 CoinInfo 목록 생성
            coin_infos = list(self._coin_info_cache.values())

            # 거래량 기준 정렬
            coin_infos.sort(key=lambda x: x.volume_raw, reverse=True)

            # 등록된 콜백 호출
            for callback in self._update_callbacks:
                try:
                    callback(coin_infos)
                except Exception as callback_error:
                    self._logger.warning(f"⚠️ UI 콜백 오류: {callback_error}")

        except Exception as e:
            self._logger.warning(f"⚠️ UI 업데이트 트리거 오류: {e}")

    def register_update_callback(self, callback: Callable[[List[CoinInfo]], None]) -> None:
        """
        UI 업데이트 콜백 등록

        Args:
            callback: CoinInfo 목록을 받는 콜백 함수
        """
        if callback not in self._update_callbacks:
            self._update_callbacks.append(callback)
            self._logger.debug(f"✅ UI 콜백 등록: {len(self._update_callbacks)}개 활성")

    def unregister_update_callback(self, callback: Callable[[List[CoinInfo]], None]) -> None:
        """UI 업데이트 콜백 해제"""
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)
            self._logger.debug(f"🗑️ UI 콜백 해제: {len(self._update_callbacks)}개 활성")

    async def _cleanup_websocket(self) -> None:
        """WebSocket 정리"""
        if self._websocket_client:
            try:
                await self._websocket_client.cleanup()
                self._logger.debug("✅ WebSocket 클라이언트 정리 완료")
            except Exception as e:
                self._logger.warning(f"⚠️ WebSocket 정리 중 오류: {e}")
            finally:
                self._websocket_client = None
                self._websocket_active = False
                self._subscription_active = False

    async def get_markets_data(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        마켓 데이터 조회 - REST API 기반

        Args:
            force_refresh: 강제 새로고침 여부

        Returns:
            List[Dict[str, Any]]: 마켓 정보 목록
        """
        if force_refresh or not self._markets_cache:
            await self._load_markets_cache()

        return self._markets_cache

    async def get_tickers_data(self, markets: List[str], force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        현재가 데이터 조회 - WebSocket 우선, REST API 폴백

        Args:
            markets: 조회할 마켓 목록
            force_refresh: 강제 새로고침 여부

        Returns:
            Dict[str, Dict[str, Any]]: 심볼별 티커 데이터
        """
        try:
            # 1. WebSocket 캐시에서 조회 (실시간 모드)
            if self._realtime_mode and self._websocket_active:
                cached_data = {}
                missing_markets = []

                for market in markets:
                    if market in self._tickers_cache:
                        cached_data[market] = self._tickers_cache[market]
                    else:
                        missing_markets.append(market)

                # WebSocket 구독에 없는 마켓이 있으면 REST API로 보완
                if missing_markets and self._rest_client:
                    self._logger.debug(f"� REST API로 보완 조회: {len(missing_markets)}개")

                    try:
                        rest_tickers = await self._rest_client.get_tickers(missing_markets)
                        for ticker in rest_tickers:
                            market = ticker['market']
                            self._tickers_cache[market] = ticker
                            cached_data[market] = ticker
                    except Exception as rest_error:
                        self._logger.warning(f"⚠️ REST API 보완 조회 실패: {rest_error}")

                if cached_data:
                    return cached_data

            # 2. REST API 전체 조회 (폴백 모드)
            if self._rest_client:
                self._logger.debug(f"📊 REST API 전체 조회: {len(markets)}개")

                rest_tickers = await self._rest_client.get_tickers(markets)
                result = {}

                for ticker in rest_tickers:
                    market = ticker['market']
                    self._tickers_cache[market] = ticker
                    result[market] = ticker

                return result

            # 3. 최후 수단: 샘플 데이터
            self._logger.warning("⚠️ REST API 클라이언트 없음, 샘플 데이터 사용")

            result = {}
            for market in markets:
                if market not in self._tickers_cache:
                    self._tickers_cache[market] = self._create_sample_ticker_data(market)
                result[market] = self._tickers_cache[market]

            return result

        except Exception as e:
            self._logger.error(f"❌ 현재가 데이터 조회 실패: {e}")
            # 에러 시 샘플 데이터로 폴백
            result = {}
            for market in markets:
                result[market] = self._create_sample_ticker_data(market)
            return result

    async def get_coins_by_market(self, market_type: str, search_filter: str = "") -> List[CoinInfo]:
        """
        마켓별 코인 목록 조회

        Args:
            market_type: 마켓 유형 (KRW, BTC, USDT)
            search_filter: 검색 필터 (코인명/심벌)

        Returns:
            코인 정보 목록
        """
        try:
            self._logger.info(f"🔍 {market_type} 마켓 코인 목록 조회 시작 (검색: '{search_filter}')")

            # 1. 마켓 데이터 조회
            markets_data = await self.get_markets_data()
            self._logger.debug(f"📊 전체 마켓 데이터: {len(markets_data)}개")

            # 2. 해당 마켓 필터링
            filtered_markets = []
            for market_info in markets_data:
                symbol = market_info['market']
                if symbol.startswith(f"{market_type}-"):
                    filtered_markets.append(symbol)

            self._logger.info(f"📈 {market_type} 마켓 필터링 결과: {len(filtered_markets)}개")

            if not filtered_markets:
                self._logger.warning(f"⚠️  {market_type} 마켓에 코인이 없습니다")
                return []

            # 3. 실시간 WebSocket 구독 시작 (자동)
            if self._realtime_mode and not self._subscription_active and len(filtered_markets) <= 50:
                self._logger.info(f"🚀 실시간 모드: {len(filtered_markets)}개 심볼 자동 구독 시작")
                await self.start_realtime_updates(filtered_markets)

            # 4. 현재가 정보 조회
            self._logger.debug(f"💰 현재가 정보 조회 시작: {len(filtered_markets)}개")
            tickers_data = await self.get_tickers_data(filtered_markets)
            self._logger.info(f"✅ 현재가 정보 조회 완료: {len(tickers_data)}개")

            # 5. CoinInfo 객체 생성 및 캐싱
            coins = []
            for market_info in markets_data:
                symbol = market_info['market']
                if not symbol.startswith(f"{market_type}-"):
                    continue

                # 현재가 정보 확인
                ticker = tickers_data.get(symbol)
                if not ticker:
                    self._logger.debug(f"⚠️ {symbol}: 현재가 정보 없음")
                    continue

                # 검색 필터 적용
                korean_name = market_info.get('korean_name', '')
                english_name = market_info.get('english_name', '')
                if search_filter:
                    search_text = f"{korean_name} {english_name} {symbol}".lower()
                    if search_filter.lower() not in search_text:
                        continue

                # 코인 정보 생성
                coin = self._create_coin_info(market_info, ticker)
                coins.append(coin)

            # 5. 거래량 기준 정렬 (높은 순) - 원본 값 사용
            coins.sort(key=lambda x: x.volume_raw, reverse=True)

            self._logger.info(f"✅ {market_type} 마켓 코인 목록 생성 완료: {len(coins)}개")

            # 상위 10개 코인 정보 로그
            if coins:
                top_coins = coins[:10]
                for i, coin in enumerate(top_coins, 1):
                    self._logger.debug(f"  {i}. {coin.symbol} - {coin.name} | {coin.price_formatted} ({coin.change_rate})")

            return coins

        except Exception as e:
            self._logger.error(f"❌ {market_type} 마켓 코인 목록 조회 실패: {e}")
            import traceback
            self._logger.error(f"스택 트레이스: {traceback.format_exc()}")
            return []

    def _create_coin_info(self, market_info: Dict[str, Any], ticker: Dict[str, Any]) -> CoinInfo:
        """마켓 정보와 현재가 정보로 CoinInfo 생성"""
        symbol = market_info['market']
        korean_name = market_info.get('korean_name', '')
        english_name = market_info.get('english_name', '')

        # 코인명 결정 (한글명 우선, 없으면 영문명)
        display_name = korean_name if korean_name else english_name

        # 마켓 유형 추출
        market_type = symbol.split('-')[0]

        # 가격 정보
        current_price = ticker.get('trade_price', 0)
        change_rate = ticker.get('change_rate', 0)
        change_price = ticker.get('change_price', 0)
        change_status = ticker.get('change', 'EVEN')  # RISE, FALL, EVEN
        volume = ticker.get('acc_trade_price_24h', 0)  # 거래대금 (실제 업비트 정렬 기준)

        # 가격 포맷팅
        price_formatted = self._format_price(current_price, market_type)
        change_rate_formatted = self._format_change_rate(change_rate, change_status)
        change_price_formatted = self._format_price(change_price, market_type)
        volume_formatted = self._format_volume(volume)

        # 정렬용 실제 변화율 계산 (음수 포함)
        change_rate_raw = change_rate if change_status == 'RISE' else -change_rate if change_status == 'FALL' else 0.0

        # 경고 마켓 여부
        is_warning = market_info.get('market_warning', 'NONE') != 'NONE'

        return CoinInfo(
            symbol=symbol,
            name=display_name,
            market=market_type,
            price=str(current_price),
            price_formatted=price_formatted,
            change_rate=change_rate_formatted,
            change_price=change_price_formatted,
            volume=volume_formatted,
            volume_raw=volume,  # 원본 거래량
            change_rate_raw=change_rate_raw,  # 원본 변화율 (음수 포함)
            is_warning=is_warning
        )

    def _format_price(self, price: float, market_type: str) -> str:
        """가격 포맷팅"""
        if price == 0:
            return "0"

        try:
            if market_type == "KRW":
                # KRW 마켓: 천 단위 구분
                if price >= 1000:
                    return f"{price:,.0f}"
                elif price >= 100:
                    return f"{price:.0f}"
                elif price >= 1:
                    return f"{price:.1f}"
                else:
                    return f"{price:.2f}"
            else:
                # BTC/USDT 마켓: 소수점 표시
                if price >= 1:
                    return f"{price:.3f}"
                elif price >= 0.001:
                    return f"{price:.6f}"
                else:
                    return f"{price:.8f}"
        except Exception:
            return str(price)

    def _format_change_rate(self, change_rate: float, change_status: str) -> str:
        """변화율 포맷팅 (change 상태 고려)"""
        try:
            rate_percent = change_rate * 100

            if change_status == 'RISE':
                return f"+{rate_percent:.2f}%"
            elif change_status == 'FALL':
                return f"-{rate_percent:.2f}%"
            else:  # EVEN
                return "0.00%"
        except Exception:
            return "0.00%"

    def _format_volume(self, volume: float) -> str:
        """거래량 포맷팅"""
        try:
            if volume >= 1_000_000:
                return f"{volume / 1_000_000:.1f}M"
            elif volume >= 1_000:
                return f"{volume / 1_000:.1f}K"
            else:
                return f"{volume:.2f}"
        except Exception:
            return "0"

    async def search_coins(self, query: str, market_type: str = "KRW", limit: int = 50) -> List[CoinInfo]:
        """
        코인 검색

        Args:
            query: 검색어
            market_type: 마켓 유형 제한
            limit: 결과 개수 제한

        Returns:
            검색된 코인 목록
        """
        if not query.strip():
            return []

        try:
            coins = await self.get_coins_by_market(market_type, query.strip())
            return coins[:limit]
        except Exception as e:
            self._logger.error(f"❌ 코인 검색 실패: {e}")
            return []

    async def get_coin_detail(self, symbol: str) -> Optional[CoinInfo]:
        """특정 코인의 상세 정보 조회"""
        try:
            # 마켓 정보 조회
            markets_data = await self.get_markets_data()
            market_info = next((m for m in markets_data if m['market'] == symbol), None)
            if not market_info:
                return None

            # 현재가 정보 조회
            tickers_data = await self.get_tickers_data([symbol])
            ticker = tickers_data.get(symbol)
            if not ticker:
                return None

            return self._create_coin_info(market_info, ticker)

        except Exception as e:
            self._logger.error(f"❌ 코인 상세 정보 조회 실패 {symbol}: {e}")
            return None

    async def refresh_data(self) -> bool:
        """데이터 새로고침"""
        try:
            self._logger.info("🔄 코인 리스트 데이터 새로고침 시작")

            # 모든 캐시 클리어
            self._markets_cache.clear()
            self._tickers_cache.clear()

            # 마켓 데이터 다시 로드
            await self.get_markets_data(force_refresh=True)

            self._logger.info("✅ 코인 리스트 데이터 새로고침 완료")
            return True

        except Exception as e:
            self._logger.error(f"❌ 데이터 새로고침 실패: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보"""
        return {
            "markets_count": len(self._markets_cache),
            "tickers_count": len(self._tickers_cache),
            "last_update": self._last_update
        }

    def _create_sample_markets_data(self) -> List[Dict[str, Any]]:
        """샘플 마켓 데이터 생성 - 주요 코인들"""
        sample_markets = [
            # KRW 마켓 주요 코인들
            {"market": "KRW-BTC", "korean_name": "비트코인", "english_name": "Bitcoin", "market_warning": "NONE"},
            {"market": "KRW-ETH", "korean_name": "이더리움", "english_name": "Ethereum", "market_warning": "NONE"},
            {"market": "KRW-XRP", "korean_name": "리플", "english_name": "XRP", "market_warning": "NONE"},
            {"market": "KRW-ADA", "korean_name": "에이다", "english_name": "Cardano", "market_warning": "NONE"},
            {"market": "KRW-AVAX", "korean_name": "아발란체", "english_name": "Avalanche", "market_warning": "NONE"},
            {"market": "KRW-DOT", "korean_name": "폴카닷", "english_name": "Polkadot", "market_warning": "NONE"},
            {"market": "KRW-MATIC", "korean_name": "폴리곤", "english_name": "Polygon", "market_warning": "NONE"},
            {"market": "KRW-SOL", "korean_name": "솔라나", "english_name": "Solana", "market_warning": "NONE"},
            # BTC 마켓 주요 코인들
            {"market": "BTC-ETH", "korean_name": "이더리움", "english_name": "Ethereum", "market_warning": "NONE"},
            {"market": "BTC-XRP", "korean_name": "리플", "english_name": "XRP", "market_warning": "NONE"},
            {"market": "BTC-ADA", "korean_name": "에이다", "english_name": "Cardano", "market_warning": "NONE"},
            # USDT 마켓 주요 코인들
            {"market": "USDT-BTC", "korean_name": "비트코인", "english_name": "Bitcoin", "market_warning": "NONE"},
            {"market": "USDT-ETH", "korean_name": "이더리움", "english_name": "Ethereum", "market_warning": "NONE"},
        ]

        self._logger.debug(f"📝 샘플 마켓 데이터 생성: {len(sample_markets)}개")
        return sample_markets

    def _create_sample_ticker_data(self, market: str) -> Dict[str, Any]:
        """샘플 티커 데이터 생성 - 마켓별 가격 정보"""
        # 마켓 유형별 기본 가격 설정
        base_prices = {
            "KRW-BTC": 52000000,    # 5200만원
            "KRW-ETH": 3500000,     # 350만원
            "KRW-XRP": 620,        # 620원
            "KRW-ADA": 450,        # 450원
            "KRW-AVAX": 32000,     # 3.2만원
            "KRW-DOT": 8500,       # 8500원
            "KRW-MATIC": 750,      # 750원
            "KRW-SOL": 145000,     # 14.5만원
            "BTC-ETH": 0.067,      # BTC 대비 ETH 비율
            "BTC-XRP": 0.0000118,  # BTC 대비 XRP 비율
            "BTC-ADA": 0.0000086,  # BTC 대비 ADA 비율
            "USDT-BTC": 50800,     # USDT 대비 BTC 가격
            "USDT-ETH": 3420,      # USDT 대비 ETH 가격
        }

        # 기본 가격 설정 (없으면 1000 기본값)
        base_price = base_prices.get(market, 1000)

        # 무작위 변동 적용 (-5% ~ +5%)
        price_variation = random.uniform(-0.05, 0.05)
        current_price = base_price * (1 + price_variation)

        # 변화율 및 변화금액 계산
        change_rate = abs(price_variation)
        change_price = abs(current_price - base_price)
        change_status = "RISE" if price_variation > 0 else "FALL" if price_variation < 0 else "EVEN"

        # 거래대금 (무작위)
        volume_base = {
            "KRW-BTC": 50000000000,  # 500억
            "KRW-ETH": 30000000000,  # 300억
            "KRW-XRP": 20000000000,  # 200억
        }
        acc_trade_price = volume_base.get(market, 1000000000) * random.uniform(0.5, 2.0)

        ticker_data = {
            "market": market,
            "trade_price": current_price,
            "change_rate": change_rate,
            "change_price": change_price,
            "change": change_status,
            "acc_trade_price_24h": acc_trade_price,
            "opening_price": base_price,
            "high_price": current_price * 1.02,
            "low_price": current_price * 0.98,
            "prev_closing_price": base_price,
            "timestamp": 1695000000000,  # 샘플 타임스탬프
        }

        return ticker_data

    async def cleanup(self) -> None:
        """서비스 정리"""
        try:
            self._logger.info("🧹 CoinListService 정리 시작...")

            # WebSocket 정리
            await self._cleanup_websocket()

            # REST 클라이언트 정리
            if self._rest_client:
                await self._rest_client.close()
                self._rest_client = None

            # 캐시 정리
            self._markets_cache.clear()
            self._tickers_cache.clear()
            self._coin_info_cache.clear()
            self._update_callbacks.clear()

            self._logger.info("✅ CoinListService 정리 완료")

        except Exception as e:
            self._logger.error(f"❌ 서비스 정리 중 오류: {e}")

    def is_realtime_active(self) -> bool:
        """실시간 모드 활성화 여부 확인"""
        return self._realtime_mode and self._websocket_active and self._subscription_active

    def get_subscription_info(self) -> Dict[str, Any]:
        """구독 정보 조회"""
        return {
            "realtime_mode": self._realtime_mode,
            "websocket_active": self._websocket_active,
            "subscription_active": self._subscription_active,
            "subscribed_symbols_count": len(self._subscribed_symbols),
            "cached_coins_count": len(self._coin_info_cache),
            "cached_tickers_count": len(self._tickers_cache),
            "update_callbacks_count": len(self._update_callbacks),
            "last_update": self._last_update
        }
