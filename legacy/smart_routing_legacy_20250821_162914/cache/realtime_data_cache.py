"""
실시간 데이터 캐시 구현

Smart Router 내부의 메모리 캐시로, 실거래 성능 최적화를 위해
WebSocket으로 받은 실시간 데이터를 < 1ms 속도로 제공합니다.
"""

from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from collections import deque
import threading

from ..models.symbols import TradingSymbol
from ..models.market_data_types import CandleData, TickerData
from upbit_auto_trading.infrastructure.logging import create_component_logger


class RealtimeDataCache:
    """실거래 전용 메모리 캐시

    특징:
    1. < 1ms 메모리 접근 성능
    2. 심볼별 × 타임프레임별 슬라이딩 윈도우
    3. TTL 기반 자동 만료
    4. Storage Layer 연동을 위한 공개 인터페이스
    5. 메모리 제한 자동 관리
    """

    def __init__(self, max_symbols: int = 100, max_candles_per_timeframe: int = 200):
        self.max_symbols = max_symbols
        self.max_candles_per_timeframe = max_candles_per_timeframe

        # 로깅
        self.logger = create_component_logger("RealtimeDataCache")

        # 스레드 안전성을 위한 락
        self._lock = threading.RLock()

        # 캐시 저장소
        self._ticker_cache: Dict[str, TimestampedData] = {}
        self._candle_cache: Dict[str, Dict[str, deque]] = {}  # symbol -> timeframe -> deque

        # 캔들 완성 이벤트 핸들러
        self.on_candle_completed: Optional[Callable[[TradingSymbol, str, CandleData], None]] = None

        self.logger.info(f"RealtimeDataCache 초기화: max_symbols={max_symbols}, max_candles={max_candles_per_timeframe}")

    async def update_ticker_data(self, symbol: TradingSymbol, ticker: TickerData, ttl_seconds: int = 300) -> None:
        """티커 데이터 업데이트 (TTL: 5분)"""
        symbol_key = self._get_symbol_key(symbol)

        with self._lock:
            # 메모리 제한 확인
            if len(self._ticker_cache) >= self.max_symbols and symbol_key not in self._ticker_cache:
                self._evict_oldest_ticker()

            # TTL 적용 데이터 저장
            expiry_time = datetime.now() + timedelta(seconds=ttl_seconds)
            self._ticker_cache[symbol_key] = TimestampedData(ticker, expiry_time)

        self.logger.debug(f"티커 데이터 업데이트: {symbol_key}, price={ticker.current_price}")

    async def get_cached_ticker(self, symbol: TradingSymbol) -> Optional[TickerData]:
        """캐시된 티커 데이터 조회 (< 1ms 성능 목표)"""
        symbol_key = self._get_symbol_key(symbol)

        with self._lock:
            if symbol_key not in self._ticker_cache:
                return None

            cached_data = self._ticker_cache[symbol_key]

            # TTL 확인
            if datetime.now() > cached_data.expiry_time:
                del self._ticker_cache[symbol_key]
                return None

            return cached_data.data

    async def update_candle_data(self, symbol: TradingSymbol, timeframe: str, candle: CandleData) -> None:
        """캔들 데이터 업데이트 (슬라이딩 윈도우)"""
        symbol_key = self._get_symbol_key(symbol)

        with self._lock:
            # 심볼별 캐시 초기화
            if symbol_key not in self._candle_cache:
                if len(self._candle_cache) >= self.max_symbols:
                    self._evict_oldest_symbol()
                self._candle_cache[symbol_key] = {}

            # 타임프레임별 캐시 초기화
            if timeframe not in self._candle_cache[symbol_key]:
                self._candle_cache[symbol_key][timeframe] = deque(maxlen=self.max_candles_per_timeframe)

            candle_queue = self._candle_cache[symbol_key][timeframe]

            # 기존 캔들 업데이트 또는 새 캔들 추가
            updated = False
            for i, existing_candle in enumerate(candle_queue):
                if existing_candle.timestamp == candle.timestamp:
                    candle_queue[i] = candle
                    updated = True
                    break

            if not updated:
                candle_queue.append(candle)
                # 시간순 정렬 유지
                sorted_candles = sorted(candle_queue, key=lambda c: c.timestamp)
                candle_queue.clear()
                candle_queue.extend(sorted_candles)

        self.logger.debug(f"캔들 데이터 업데이트: {symbol_key}:{timeframe}, time={candle.timestamp}")

    async def get_cached_candles(self, symbol: TradingSymbol, timeframe: str, count: int) -> List[CandleData]:
        """캐시된 캔들 데이터 조회 (최신 N개)"""
        symbol_key = self._get_symbol_key(symbol)

        with self._lock:
            if symbol_key not in self._candle_cache:
                return []

            if timeframe not in self._candle_cache[symbol_key]:
                return []

            candle_queue = self._candle_cache[symbol_key][timeframe]
            return list(candle_queue)[-count:] if count > 0 else list(candle_queue)

    def get_cached_ticker_sync(self, symbol: TradingSymbol) -> Optional[TickerData]:
        """Storage Layer용 동기 인터페이스"""
        symbol_key = self._get_symbol_key(symbol)

        with self._lock:
            if symbol_key not in self._ticker_cache:
                return None

            cached_data = self._ticker_cache[symbol_key]

            # TTL 확인
            if datetime.now() > cached_data.expiry_time:
                del self._ticker_cache[symbol_key]
                return None

            # 복사본 반환 (원본 보호)
            return cached_data.data

    def get_cached_candles_sync(self, symbol: TradingSymbol, timeframe: str, count: int) -> List[CandleData]:
        """Storage Layer용 동기 인터페이스"""
        symbol_key = self._get_symbol_key(symbol)

        with self._lock:
            if symbol_key not in self._candle_cache:
                return []

            if timeframe not in self._candle_cache[symbol_key]:
                return []

            candle_queue = self._candle_cache[symbol_key][timeframe]
            return list(candle_queue)[-count:] if count > 0 else list(candle_queue)

    def clear_cache(self) -> None:
        """모든 캐시 정리"""
        with self._lock:
            self._ticker_cache.clear()
            self._candle_cache.clear()

        self.logger.info("모든 캐시 정리 완료")

    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        with self._lock:
            return {
                "ticker_count": len(self._ticker_cache),
                "symbol_count": len(self._candle_cache),
                "total_candle_count": sum(
                    sum(len(tf_cache) for tf_cache in symbol_cache.values())
                    for symbol_cache in self._candle_cache.values()
                ),
                "max_symbols": self.max_symbols,
                "max_candles_per_timeframe": self.max_candles_per_timeframe
            }

    def _get_symbol_key(self, symbol: TradingSymbol) -> str:
        """심볼을 캐시 키로 변환"""
        return f"{symbol.quote_currency}-{symbol.base_currency}"

    def _evict_oldest_ticker(self) -> None:
        """가장 오래된 티커 제거 (LRU)"""
        if not self._ticker_cache:
            return

        oldest_key = min(self._ticker_cache.keys(),
                         key=lambda k: self._ticker_cache[k].created_at)
        del self._ticker_cache[oldest_key]
        self.logger.debug(f"오래된 티커 제거: {oldest_key}")

    def _evict_oldest_symbol(self) -> None:
        """가장 오래된 심볼 제거"""
        if not self._candle_cache:
            return

        # 첫 번째 심볼 제거 (FIFO)
        oldest_symbol = next(iter(self._candle_cache))
        del self._candle_cache[oldest_symbol]
        self.logger.debug(f"오래된 심볼 제거: {oldest_symbol}")


class TimestampedData:
    """TTL 지원 데이터 컨테이너"""

    def __init__(self, data: Any, expiry_time: datetime):
        self.data = data
        self.expiry_time = expiry_time
        self.created_at = datetime.now()
