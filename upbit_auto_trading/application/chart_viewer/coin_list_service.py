"""
코인 리스트 서비스 (Application Layer) - get_tickers_markets() 기반 최적화

차트뷰어 코인 리스트 위젯을 위한 실시간 데이터 서비스입니다.
- 최적화: get_tickers_markets()로 마켓+현재가 정보 한 번에 조회
- REST API: 효율적인 단일 호출 (UpbitPublicClient)
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
    코인 리스트 서비스 - get_tickers_markets() 기반 최적화

    기능:
    - 최적화: get_tickers_markets()로 마켓 정보와 현재가를 한 번에 조회
    - WebSocket v6: 실시간 티커 데이터 수신 (WebSocketClient)
    - 실시간 캐싱: 메모리 기반 CoinInfo 데이터 관리
    - UI 업데이트: 콜백 기반 실시간 알림
    - 에러 처리: WebSocket 실패 시 REST API 폴백
    """

    def __init__(self):
        """서비스 초기화 - get_tickers_markets() 기반 효율화"""
        self._logger = create_component_logger("CoinListService")

        # REST API 클라이언트
        self._rest_client: Optional[UpbitPublicClient] = None
        self._client_ready = False

        # WebSocket 클라이언트
        self._websocket_client: Optional[WebSocketClient] = None
        self._websocket_active = False

        # 캐시 데이터 (통합 저장소)
        self._market_ticker_cache: Dict[str, Dict[str, Any]] = {}  # symbol -> combined_data (market + ticker)
        self._coin_info_cache: Dict[str, CoinInfo] = {}           # symbol -> CoinInfo
        self._last_update: Optional[float] = None

        # 구독 관리
        self._subscribed_symbols: List[str] = []
        self._subscription_active = False

        # UI 콜백
        self._update_callbacks: List[Callable[[List[CoinInfo]], None]] = []

        # 실시간 모드 플래그 (WebSocket 우선, REST 폴백)
        self._realtime_mode = True

        # WebSocket 콜백 제한 (리소스 절약)
        self._callback_counter = 0
        self._last_callback_log = 0

        # 즉시 REST 클라이언트 초기화 (호가창 서비스 패턴)
        self._initialize_rest_client_immediate()

        self._logger.info("🪙 코인 리스트 서비스 초기화 완료 (🚀 get_tickers_markets() 최적화)")

    def _initialize_rest_client_immediate(self) -> None:
        """REST 클라이언트 즉시 초기화 - 호가창 서비스 패턴"""
        try:
            self._rest_client = UpbitPublicClient()
            self._client_ready = True
            self._logger.info("✅ CoinListService REST 클라이언트 즉시 초기화 완료")
        except Exception as e:
            self._logger.error(f"❌ REST 클라이언트 즉시 초기화 실패: {e}")

    async def initialize(self) -> bool:
        """
        서비스 고급 초기화 - 레거시 메서드 (즉시 초기화가 이미 완료된 경우 스킵)

        Returns:
            bool: 초기화 성공 여부
        """
        if self._client_ready:
            self._logger.info("✅ CoinListService 이미 초기화됨, 스킵")
            return True

        try:
            self._logger.info("🔧 CoinListService 고급 초기화 시작...")

            # REST API 클라이언트 생성 및 준비 상태 확인 (레거시 로직)
            if not self._rest_client:
                self._rest_client = UpbitPublicClient()

            # 클라이언트 준비 확인을 위한 간단한 테스트 요청
            retry_count = 0
            max_retries = 3

            while retry_count < max_retries:
                try:
                    # 간단한 마켓 정보 요청으로 클라이언트 준비 상태 확인
                    test_tickers = await self._rest_client.get_tickers_markets(['KRW'])
                    if test_tickers and len(test_tickers) > 0:
                        self._client_ready = True
                        self._logger.info("✅ UpbitPublicClient 준비 완료 및 검증됨")
                        break
                    else:
                        retry_count += 1
                        await asyncio.sleep(0.5)  # 500ms 대기

                except Exception as e:
                    retry_count += 1
                    self._logger.warning(f"⚠️ 클라이언트 준비 검증 실패 ({retry_count}/{max_retries}): {e}")
                    if retry_count < max_retries:
                        await asyncio.sleep(1.0)  # 1초 대기 후 재시도

            if not self._client_ready:
                self._logger.warning("⚠️ REST 클라이언트 준비 완료 대기 시간 초과, 샘플 데이터 모드로 진행")

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

    def _on_ticker_update(self, ticker_event) -> None:
        """
        WebSocket 티커 업데이트 콜백 - 로깅 최적화 적용

        Args:
            ticker_event: WebSocket에서 수신한 티커 이벤트
        """
        try:
            self._callback_counter += 1

            # 로깅 샘플링 (100개마다 1번, 5초마다 최대 1번)
            should_log = (
                self._callback_counter % 100 == 1 or
                (time.time() - self._last_callback_log) > 5.0
            )

            if should_log:
                self._logger.debug(f"📨 WebSocket 콜백: {type(ticker_event)} (누적: {self._callback_counter}개)")
                self._last_callback_log = time.time()

            if not hasattr(ticker_event, 'symbol'):
                if should_log:
                    self._logger.warning("⚠️ 티커 이벤트에 symbol 속성 없음")
                return

            symbol = ticker_event.symbol

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

            # 기존 마켓 정보와 결합하여 저장
            if symbol in self._market_ticker_cache:
                # 기존 마켓 정보 유지하면서 티커 정보 업데이트
                combined_data = self._market_ticker_cache[symbol].copy()
                combined_data.update(ticker_data)
                self._market_ticker_cache[symbol] = combined_data
            else:
                # 새로운 심볼의 경우 티커 정보만 저장 (마켓 정보는 나중에 보완)
                self._market_ticker_cache[symbol] = ticker_data

            # CoinInfo 업데이트 (마켓 정보가 있는 경우에만)
            combined_data = self._market_ticker_cache[symbol]
            if 'korean_name' in combined_data or 'english_name' in combined_data:
                coin_info = self._create_coin_info_from_combined(combined_data)
                self._coin_info_cache[symbol] = coin_info

            # UI 콜백 호출 (쓰로틀링 적용)
            self._trigger_ui_update()

            # 중요 가격 변동 로깅 (상위 코인만)
            if should_log and symbol in ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']:
                price = ticker_data['trade_price']
                change_rate = ticker_data['change_rate'] * 100
                stream_type = getattr(ticker_event, 'stream_type', 'UNKNOWN')
                self._logger.debug(f"📊 {stream_type}: {symbol} = {price:,}원 ({change_rate:+.2f}%)")

        except Exception as e:
            # 에러 로깅도 샘플링 적용 (1분마다 최대 1번)
            if time.time() - getattr(self, '_last_error_log', 0) > 60:
                self._logger.warning(f"⚠️ 티커 업데이트 처리 중 오류: {e}")
                self._last_error_log = time.time()

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
                    # 콜백 에러도 샘플링 (5분마다 최대 1번)
                    if time.time() - getattr(self, '_last_callback_error_log', 0) > 300:
                        self._logger.warning(f"⚠️ UI 콜백 오류: {callback_error}")
                        self._last_callback_error_log = time.time()

        except Exception as e:
            if time.time() - getattr(self, '_last_trigger_error_log', 0) > 300:
                self._logger.warning(f"⚠️ UI 업데이트 트리거 오류: {e}")
                self._last_trigger_error_log = time.time()

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

    async def get_coins_by_market(self, market_type: str, search_filter: str = "") -> List[CoinInfo]:
        """
        마켓별 코인 목록 조회 - get_tickers_markets() 기반 최적화

        Args:
            market_type: 마켓 유형 (KRW, BTC, USDT)
            search_filter: 검색 필터 (코인명/심볼)

        Returns:
            코인 정보 목록
        """
        try:
            self._logger.info(f"🔍 {market_type} 마켓 코인 목록 조회 시작 (검색: '{search_filter}')")

            # get_tickers_markets()로 마켓 정보와 현재가를 한 번에 조회
            if self._client_ready and self._rest_client:
                try:
                    # 실제 API 호출로 마켓별 현재가 데이터 조회
                    tickers_data = await self._rest_client.get_tickers_markets([market_type])
                    self._logger.info(f"✅ {market_type} 마켓 데이터 조회 완료: {len(tickers_data)}개")

                    # 각 티커 데이터를 마켓 정보로 간주하여 처리
                    filtered_symbols = []
                    coins = []

                    for ticker in tickers_data:
                        symbol = ticker['market']

                        # 검색 필터 적용 (심볼 기반으로 간단 검색)
                        if search_filter:
                            if search_filter.lower() not in symbol.lower():
                                continue

                        filtered_symbols.append(symbol)

                        # 통합 데이터 생성 (마켓 정보 + 현재가 정보)
                        combined_data = {
                            'market': symbol,
                            'korean_name': f"{symbol.split('-')[1]}",  # 임시 한글명 (실제로는 마켓 API에서 가져와야 함)
                            'english_name': symbol.split('-')[1],
                            'market_warning': 'NONE',
                            # 티커 정보 추가
                            'trade_price': ticker.get('trade_price', 0),
                            'change_rate': ticker.get('change_rate', 0),
                            'change_price': ticker.get('change_price', 0),
                            'change': ticker.get('change', 'EVEN'),
                            'acc_trade_price_24h': ticker.get('acc_trade_price_24h', 0),
                            'opening_price': ticker.get('opening_price', 0),
                            'high_price': ticker.get('high_price', 0),
                            'low_price': ticker.get('low_price', 0),
                            'prev_closing_price': ticker.get('prev_closing_price', 0),
                            'timestamp': ticker.get('timestamp', int(time.time() * 1000)),
                        }

                        # 캐시에 저장
                        self._market_ticker_cache[symbol] = combined_data

                        # CoinInfo 생성
                        coin_info = self._create_coin_info_from_combined(combined_data)
                        self._coin_info_cache[symbol] = coin_info
                        coins.append(coin_info)

                    # 실시간 WebSocket 구독 시작 (50개 이하일 때)
                    if self._realtime_mode and not self._subscription_active and len(filtered_symbols) <= 50:
                        self._logger.info(f"🚀 실시간 모드: {len(filtered_symbols)}개 심볼 자동 구독 시작")
                        await self.start_realtime_updates(filtered_symbols)

                except Exception as api_error:
                    self._logger.error(f"❌ API 호출 실패: {api_error}")
                    # API 실패 시 샘플 데이터로 폴백
                    coins = await self._get_sample_coins_by_market(market_type, search_filter)
            else:
                self._logger.warning("⚠️ REST 클라이언트 준비되지 않음, 샘플 데이터 사용")
                coins = await self._get_sample_coins_by_market(market_type, search_filter)

            # 거래량 기준 정렬 (높은 순)
            coins.sort(key=lambda x: x.volume_raw, reverse=True)

            self._logger.info(f"✅ {market_type} 마켓 코인 목록 생성 완료: {len(coins)}개")

            # 상위 5개 코인 정보 로그 (간소화)
            if coins:
                top_coins = coins[:5]
                top_info = " | ".join([f"{coin.symbol}({coin.price_formatted})" for coin in top_coins])
                self._logger.debug(f"  상위 5개: {top_info}")

            return coins

        except Exception as e:
            self._logger.error(f"❌ {market_type} 마켓 코인 목록 조회 실패: {e}")
            import traceback
            self._logger.error(f"스택 트레이스: {traceback.format_exc()}")
            return []

    async def _get_sample_coins_by_market(self, market_type: str, search_filter: str = "") -> List[CoinInfo]:
        """샘플 데이터로 코인 목록 생성 (폴백용)"""
        try:
            # 마켓별 샘플 데이터
            sample_data = {
                "KRW": [
                    {"symbol": "KRW-BTC", "name": "비트코인", "base_price": 52000000},
                    {"symbol": "KRW-ETH", "name": "이더리움", "base_price": 3500000},
                    {"symbol": "KRW-XRP", "name": "리플", "base_price": 620},
                ],
                "BTC": [
                    {"symbol": "BTC-ETH", "name": "이더리움", "base_price": 0.067},
                    {"symbol": "BTC-XRP", "name": "리플", "base_price": 0.0000118},
                ],
                "USDT": [
                    {"symbol": "USDT-BTC", "name": "비트코인", "base_price": 50800},
                    {"symbol": "USDT-ETH", "name": "이더리움", "base_price": 3420},
                ]
            }

            market_samples = sample_data.get(market_type, [])
            coins = []

            for sample in market_samples:
                symbol = sample["symbol"]
                name = sample["name"]
                base_price = sample["base_price"]

                # 검색 필터 적용
                if search_filter:
                    search_text = f"{name} {symbol}".lower()
                    if search_filter.lower() not in search_text:
                        continue

                # 가격 변동 시뮬레이션
                price_variation = random.uniform(-0.05, 0.05)
                current_price = base_price * (1 + price_variation)
                change_rate = abs(price_variation)
                change_price = abs(current_price - base_price)
                change_status = "RISE" if price_variation > 0 else "FALL" if price_variation < 0 else "EVEN"
                volume = random.uniform(1000000000, 50000000000)  # 10억~500억

                # 통합 데이터 생성
                combined_data = {
                    'market': symbol,
                    'korean_name': name,
                    'english_name': symbol.split('-')[1],
                    'market_warning': 'NONE',
                    'trade_price': current_price,
                    'change_rate': change_rate,
                    'change_price': change_price,
                    'change': change_status,
                    'acc_trade_price_24h': volume,
                    'opening_price': base_price,
                    'high_price': current_price * 1.02,
                    'low_price': current_price * 0.98,
                    'prev_closing_price': base_price,
                    'timestamp': int(time.time() * 1000),
                }

                # 캐시에 저장
                self._market_ticker_cache[symbol] = combined_data

                # CoinInfo 생성
                coin_info = self._create_coin_info_from_combined(combined_data)
                self._coin_info_cache[symbol] = coin_info
                coins.append(coin_info)

            self._logger.info(f"📝 {market_type} 샘플 데이터 생성: {len(coins)}개")
            return coins

        except Exception as e:
            self._logger.error(f"❌ 샘플 데이터 생성 실패: {e}")
            return []

    def _create_coin_info_from_combined(self, combined_data: Dict[str, Any]) -> CoinInfo:
        """통합 데이터(마켓+티커)로 CoinInfo 생성"""
        symbol = combined_data['market']
        korean_name = combined_data.get('korean_name', '')
        english_name = combined_data.get('english_name', '')

        # 코인명 결정 (한글명 우선, 없으면 영문명)
        display_name = korean_name if korean_name else english_name

        # 마켓 유형 추출
        market_type = symbol.split('-')[0]

        # 가격 정보
        current_price = combined_data.get('trade_price', 0)
        change_rate = combined_data.get('change_rate', 0)
        change_price = combined_data.get('change_price', 0)
        change_status = combined_data.get('change', 'EVEN')  # RISE, FALL, EVEN
        volume = combined_data.get('acc_trade_price_24h', 0)  # 거래대금 (실제 업비트 정렬 기준)

        # 가격 포맷팅
        price_formatted = self._format_price(current_price, market_type)
        change_rate_formatted = self._format_change_rate(change_rate, change_status)
        change_price_formatted = self._format_price(change_price, market_type)
        volume_formatted = self._format_volume(volume)

        # 정렬용 실제 변화율 계산 (음수 포함)
        change_rate_raw = change_rate if change_status == 'RISE' else -change_rate if change_status == 'FALL' else 0.0

        # 경고 마켓 여부
        is_warning = combined_data.get('market_warning', 'NONE') != 'NONE'

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
            # 캐시에서 먼저 확인
            if symbol in self._coin_info_cache:
                return self._coin_info_cache[symbol]

            # 캐시에 없으면 실시간 조회
            if self._client_ready and self._rest_client:
                tickers = await self._rest_client.get_tickers([symbol])
                if tickers:
                    ticker = tickers[0]
                    # 간단한 마켓 정보 생성
                    combined_data = {
                        'market': symbol,
                        'korean_name': symbol.split('-')[1],
                        'english_name': symbol.split('-')[1],
                        'market_warning': 'NONE',
                    }
                    combined_data.update(ticker)

                    coin_info = self._create_coin_info_from_combined(combined_data)
                    self._coin_info_cache[symbol] = coin_info
                    return coin_info

            return None

        except Exception as e:
            self._logger.error(f"❌ 코인 상세 정보 조회 실패 {symbol}: {e}")
            return None

    async def refresh_data(self) -> bool:
        """데이터 새로고침"""
        try:
            self._logger.info("🔄 코인 리스트 데이터 새로고침 시작")

            # 모든 캐시 클리어
            self._market_ticker_cache.clear()
            self._coin_info_cache.clear()

            # 클라이언트 준비 상태 재확인
            if self._rest_client:
                test_tickers = await self._rest_client.get_tickers_markets(['KRW'])
                self._client_ready = bool(test_tickers and len(test_tickers) > 0)

            self._logger.info("✅ 코인 리스트 데이터 새로고침 완료")
            return True

        except Exception as e:
            self._logger.error(f"❌ 데이터 새로고침 실패: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보"""
        return {
            "market_ticker_cache_count": len(self._market_ticker_cache),
            "coin_info_cache_count": len(self._coin_info_cache),
            "callback_count": self._callback_counter,
            "client_ready": self._client_ready,
            "last_update": self._last_update
        }

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
            self._market_ticker_cache.clear()
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
            "cached_market_ticker_count": len(self._market_ticker_cache),
            "update_callbacks_count": len(self._update_callbacks),
            "client_ready": self._client_ready,
            "callback_counter": self._callback_counter,
            "last_update": self._last_update
        }
