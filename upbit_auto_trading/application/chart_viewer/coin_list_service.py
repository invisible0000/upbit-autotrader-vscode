"""
코인 리스트 서비스 (Application Layer)

차트뷰어 코인 리스트 위젯을 위한 비즈니스 로직을 담당합니다.
업비트 API를 통해 마켓 데이터를 조회하고 UI에서 사용할 형태로 변환합니다.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit import UpbitPublicClient


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
    코인 리스트 서비스

    기능:
    - 업비트 마켓 데이터 조회 및 캐싱
    - 마켓별 코인 목록 필터링 (KRW/BTC/USDT)
    - 검색 및 즐겨찾기 지원
    - 실시간 가격 정보 포맷팅
    """

    def __init__(self):
        """서비스 초기화"""
        self._logger = create_component_logger("CoinListService")
        self._upbit_client = UpbitPublicClient()

        # 캐시 데이터
        self._markets_cache: List[Dict[str, Any]] = []
        self._tickers_cache: Dict[str, Dict[str, Any]] = {}
        self._last_update: Optional[str] = None

        self._logger.info("🪙 코인 리스트 서비스 초기화 완료")

    async def get_markets_data(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """마켓 데이터 조회 (캐싱)"""
        if force_refresh or not self._markets_cache:
            try:
                self._logger.debug("업비트 마켓 데이터 조회 중...")
                self._markets_cache = await self._upbit_client.get_markets(is_details=True)
                self._logger.info(f"✅ 마켓 데이터 조회 완료: {len(self._markets_cache)}개")
            except Exception as e:
                self._logger.error(f"❌ 마켓 데이터 조회 실패: {e}")
                raise

        return self._markets_cache

    async def get_tickers_data(self, markets: List[str], force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """현재가 데이터 조회 (캐싱)"""
        # 캐시되지 않은 마켓만 조회
        uncached_markets = []
        if force_refresh:
            uncached_markets = markets
            self._tickers_cache.clear()
        else:
            uncached_markets = [m for m in markets if m not in self._tickers_cache]

        if uncached_markets:
            try:
                self._logger.debug(f"업비트 현재가 데이터 조회 중: {len(uncached_markets)}개")

                # 100개씩 분할하여 조회 (API 제한)
                for i in range(0, len(uncached_markets), 100):
                    batch = uncached_markets[i:i + 100]
                    tickers = await self._upbit_client.get_tickers(batch)

                    for ticker in tickers:
                        self._tickers_cache[ticker['market']] = ticker

                self._logger.info(f"✅ 현재가 데이터 조회 완료: {len(self._tickers_cache)}개")
            except Exception as e:
                self._logger.error(f"❌ 현재가 데이터 조회 실패: {e}")
                raise

        return {market: self._tickers_cache[market] for market in markets if market in self._tickers_cache}

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
            # 1. 마켓 데이터 조회
            markets_data = await self.get_markets_data()

            # 2. 해당 마켓 필터링
            filtered_markets = []
            for market_info in markets_data:
                symbol = market_info['market']
                if symbol.startswith(f"{market_type}-"):
                    filtered_markets.append(symbol)

            if not filtered_markets:
                self._logger.warning(f"⚠️  {market_type} 마켓에 코인이 없습니다")
                return []

            # 3. 현재가 정보 조회
            tickers_data = await self.get_tickers_data(filtered_markets)

            # 4. CoinInfo 객체 생성
            coins = []
            for market_info in markets_data:
                symbol = market_info['market']
                if not symbol.startswith(f"{market_type}-"):
                    continue

                # 현재가 정보 확인
                ticker = tickers_data.get(symbol)
                if not ticker:
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

            self._logger.debug(f"✅ {market_type} 마켓 코인 목록 생성: {len(coins)}개")
            return coins

        except Exception as e:
            self._logger.error(f"❌ {market_type} 마켓 코인 목록 조회 실패: {e}")
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
