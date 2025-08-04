#!/usr/bin/env python3
"""
시장 데이터 Repository 인터페이스
=================================

market_data.sqlite3 데이터베이스의 시장 데이터 접근을 위한 Repository 인터페이스입니다.
OHLCV 캔들 데이터, 기술적 지표, 실시간 시세, 호가 데이터 등 시계열 데이터에 대한 추상화된 접근을 제공합니다.

Design Principles:
- High-Performance Interface: 대용량 시계열 데이터 처리 최적화
- Domain Entity Mapping: MarketData Value Object와 완전 호환
- Timeframe Flexibility: 1m, 5m, 1h, 1d 등 다양한 시간프레임 지원
- Caching Strategy: 기술적 지표 캐시 관리로 계산 효율성 극대화

Mapped Tables:
- market_symbols: 거래 가능한 심볼 정보
- candlestick_data_*: 시간프레임별 OHLCV 데이터 (1m, 5m, 1h, 1d)
- technical_indicators_*: 기술적 지표 계산 결과 (1h, 1d)
- real_time_quotes: 실시간 시세 데이터
- order_book_snapshots: 호가창 스냅샷
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from enum import Enum

# Domain Value Object import
from upbit_auto_trading.domain.services.trigger_evaluation_service import MarketData


class Timeframe(Enum):
    """지원하는 시간프레임"""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    HOUR_1 = "1h"
    DAY_1 = "1d"
    
    def get_table_suffix(self) -> str:
        """테이블 이름 접미사 반환"""
        return self.value
    
    def get_display_name(self) -> str:
        """표시용 한글 이름"""
        display_names = {
            self.MINUTE_1: "1분봉",
            self.MINUTE_5: "5분봉",
            self.HOUR_1: "1시간봉",
            self.DAY_1: "1일봉"
        }
        return display_names[self]


class MarketDataRepository(ABC):
    """
    시장 데이터 접근을 위한 Repository 인터페이스

    market_data.sqlite3의 시계열 데이터와 기술적 지표에 대한
    도메인 중심의 추상화된 접근을 제공합니다.
    
    주요 특징:
    - 고성능 시계열 데이터 처리: 대용량 OHLCV 데이터 효율적 조회
    - 다중 시간프레임: 1m, 5m, 1h, 1d 통합 지원
    - 지표 캐시 관리: 중복 계산 방지 및 성능 최적화
    - 실시간 데이터: 최신 시세와 호가 데이터 접근
    """

    # ===================================
    # 기본 시장 데이터 조회 메서드
    # ===================================

    @abstractmethod
    def get_latest_market_data(self, symbol: str, timeframe: Timeframe = Timeframe.MINUTE_1) -> Optional[MarketData]:
        """
        최신 시장 데이터 조회
        
        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 시간프레임 (기본값: 1분봉)
            
        Returns:
            Optional[MarketData]: 최신 시장 데이터 또는 None
            
        Example:
            latest_btc = market_repo.get_latest_market_data('KRW-BTC', Timeframe.HOUR_1)
            if latest_btc:
                print(f"BTC 현재가: {latest_btc.close_price:,}원")
        """
        pass

    @abstractmethod
    def get_historical_data(self, symbol: str, timeframe: Timeframe, 
                          start_date: datetime, end_date: datetime, 
                          limit: Optional[int] = None) -> List[MarketData]:
        """
        과거 시장 데이터 조회
        
        Args:
            symbol: 심볼
            timeframe: 시간프레임
            start_date: 시작일시
            end_date: 종료일시
            limit: 최대 조회 개수 (None이면 전체)
            
        Returns:
            List[MarketData]: 시간순 정렬된 시장 데이터 목록
            
        Example:
            # 최근 100개 1시간봉 데이터
            history = market_repo.get_historical_data(
                'KRW-BTC', Timeframe.HOUR_1, 
                datetime.now() - timedelta(days=7), datetime.now(),
                limit=100
            )
        """
        pass

    @abstractmethod
    def get_recent_data(self, symbol: str, timeframe: Timeframe, count: int) -> List[MarketData]:
        """
        최근 N개 데이터 조회 (백테스팅용 최적화)
        
        Args:
            symbol: 심볼
            timeframe: 시간프레임
            count: 조회할 데이터 개수
            
        Returns:
            List[MarketData]: 최신순으로 정렬된 데이터 목록
            
        Example:
            # 백테스팅용 최근 200개 일봉 데이터
            recent_data = market_repo.get_recent_data('KRW-BTC', Timeframe.DAY_1, 200)
        """
        pass

    @abstractmethod
    def save_market_data(self, symbol: str, timeframe: Timeframe, market_data: MarketData) -> None:
        """
        시장 데이터 저장
        
        Args:
            symbol: 심볼
            timeframe: 시간프레임
            market_data: 저장할 시장 데이터
            
        Example:
            new_data = MarketData(
                symbol='KRW-BTC', timestamp=datetime.now(),
                open_price=50000000, high_price=51000000,
                low_price=49000000, close_price=50500000, volume=100.5
            )
            market_repo.save_market_data('KRW-BTC', Timeframe.MINUTE_1, new_data)
        """
        pass

    @abstractmethod
    def save_market_data_batch(self, symbol: str, timeframe: Timeframe, 
                             market_data_list: List[MarketData]) -> int:
        """
        시장 데이터 일괄 저장 (성능 최적화)
        
        Args:
            symbol: 심볼
            timeframe: 시간프레임
            market_data_list: 저장할 데이터 목록
            
        Returns:
            int: 저장된 레코드 수
            
        Example:
            # API에서 받은 1000개 1분봉 데이터 일괄 저장
            saved_count = market_repo.save_market_data_batch(
                'KRW-BTC', Timeframe.MINUTE_1, api_data_list
            )
        """
        pass

    # ===================================
    # 기술적 지표 관리 메서드
    # ===================================

    @abstractmethod
    def get_indicator_data(self, symbol: str, indicator_name: str, 
                         timeframe: Timeframe, period: int,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> List[Tuple[datetime, float]]:
        """
        기술적 지표 데이터 조회
        
        Args:
            symbol: 심볼
            indicator_name: 지표 이름 ('RSI', 'SMA', 'MACD' 등)
            timeframe: 시간프레임
            period: 지표 기간 (예: RSI의 14, SMA의 20)
            start_date: 시작일시 (None이면 전체)
            end_date: 종료일시 (None이면 최신까지)
            
        Returns:
            List[Tuple[datetime, float]]: (타임스탬프, 지표값) 튜플 목록
            
        Example:
            # RSI 14 최근 100개 값
            rsi_data = market_repo.get_indicator_data(
                'KRW-BTC', 'RSI', Timeframe.HOUR_1, 14,
                datetime.now() - timedelta(days=7), datetime.now()
            )
        """
        pass

    @abstractmethod
    def get_latest_indicator_value(self, symbol: str, indicator_name: str, 
                                 timeframe: Timeframe, period: int) -> Optional[float]:
        """
        최신 기술적 지표값 조회
        
        Args:
            symbol: 심볼
            indicator_name: 지표 이름
            timeframe: 시간프레임
            period: 지표 기간
            
        Returns:
            Optional[float]: 최신 지표값 또는 None
            
        Example:
            # BTC 현재 RSI 값
            current_rsi = market_repo.get_latest_indicator_value(
                'KRW-BTC', 'RSI', Timeframe.HOUR_1, 14
            )
        """
        pass

    @abstractmethod
    def save_indicator_data(self, symbol: str, indicator_name: str, 
                          timeframe: Timeframe, period: int,
                          values: List[Tuple[datetime, float]]) -> int:
        """
        기술적 지표 데이터 저장 (캐시)
        
        Args:
            symbol: 심볼
            indicator_name: 지표 이름
            timeframe: 시간프레임
            period: 지표 기간
            values: (타임스탬프, 지표값) 튜플 목록
            
        Returns:
            int: 저장된 레코드 수
            
        Example:
            # 계산된 RSI 값들 캐시에 저장
            rsi_values = [(datetime.now(), 65.5), (datetime.now() - timedelta(hours=1), 68.2)]
            saved = market_repo.save_indicator_data(
                'KRW-BTC', 'RSI', Timeframe.HOUR_1, 14, rsi_values
            )
        """
        pass

    @abstractmethod
    def is_indicator_cached(self, symbol: str, indicator_name: str, 
                          timeframe: Timeframe, period: int,
                          timestamp: datetime) -> bool:
        """
        특정 시점의 지표가 캐시되어 있는지 확인
        
        Args:
            symbol: 심볼
            indicator_name: 지표 이름
            timeframe: 시간프레임
            period: 지표 기간
            timestamp: 확인할 시점
            
        Returns:
            bool: 캐시 존재 여부
            
        Example:
            # 1시간 전 RSI가 캐시되어 있는지 확인
            cached = market_repo.is_indicator_cached(
                'KRW-BTC', 'RSI', Timeframe.HOUR_1, 14,
                datetime.now() - timedelta(hours=1)
            )
        """
        pass

    @abstractmethod
    def get_missing_indicator_timestamps(self, symbol: str, indicator_name: str,
                                       timeframe: Timeframe, period: int,
                                       start_date: datetime, end_date: datetime) -> List[datetime]:
        """
        지표 캐시가 누락된 시점들 조회
        
        Args:
            symbol: 심볼
            indicator_name: 지표 이름
            timeframe: 시간프레임
            period: 지표 기간
            start_date: 시작일시
            end_date: 종료일시
            
        Returns:
            List[datetime]: 캐시가 누락된 타임스탬프 목록
            
        Example:
            # 지난 7일간 RSI 캐시 누락 구간 찾기
            missing = market_repo.get_missing_indicator_timestamps(
                'KRW-BTC', 'RSI', Timeframe.HOUR_1, 14,
                datetime.now() - timedelta(days=7), datetime.now()
            )
        """
        pass

    # ===================================
    # 심볼 및 메타데이터 관리 메서드
    # ===================================

    @abstractmethod
    def get_available_symbols(self) -> List[str]:
        """
        거래 가능한 심볼 목록 조회
        
        Returns:
            List[str]: 활성 심볼 목록
            
        Example:
            symbols = market_repo.get_available_symbols()
            # ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', ...]
        """
        pass

    @abstractmethod
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        심볼 상세 정보 조회
        
        Args:
            symbol: 심볼
            
        Returns:
            Optional[Dict[str, Any]]: 심볼 정보 또는 None
            
        Example:
            btc_info = market_repo.get_symbol_info('KRW-BTC')
            # {
            #     'symbol': 'KRW-BTC',
            #     'display_name_ko': '비트코인',
            #     'min_order_amount': 5000,
            #     'price_precision': 0,
            #     'is_active': True
            # }
        """
        pass

    @abstractmethod
    def get_available_timeframes(self) -> List[str]:
        """
        지원하는 시간프레임 목록 조회
        
        Returns:
            List[str]: 시간프레임 목록
            
        Example:
            timeframes = market_repo.get_available_timeframes()
            # ['1m', '5m', '1h', '1d']
        """
        pass

    @abstractmethod
    def is_symbol_active(self, symbol: str) -> bool:
        """
        심볼 활성화 상태 확인
        
        Args:
            symbol: 심볼
            
        Returns:
            bool: 활성화 상태
            
        Example:
            active = market_repo.is_symbol_active('KRW-BTC')
            # True
        """
        pass

    # ===================================
    # 데이터 범위 및 통계 조회 메서드
    # ===================================

    @abstractmethod
    def get_data_range(self, symbol: str, timeframe: Timeframe) -> Optional[Tuple[datetime, datetime]]:
        """
        특정 심볼/시간프레임의 데이터 범위 조회
        
        Args:
            symbol: 심볼
            timeframe: 시간프레임
            
        Returns:
            Optional[Tuple[datetime, datetime]]: (시작일시, 종료일시) 또는 None
            
        Example:
            date_range = market_repo.get_data_range('KRW-BTC', Timeframe.DAY_1)
            if date_range:
                start, end = date_range
                print(f"BTC 일봉 데이터: {start} ~ {end}")
        """
        pass

    @abstractmethod
    def get_data_count(self, symbol: str, timeframe: Timeframe,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> int:
        """
        데이터 개수 조회
        
        Args:
            symbol: 심볼
            timeframe: 시간프레임
            start_date: 시작일시 (None이면 전체)
            end_date: 종료일시 (None이면 전체)
            
        Returns:
            int: 데이터 개수
            
        Example:
            # BTC 1시간봉 총 개수
            count = market_repo.get_data_count('KRW-BTC', Timeframe.HOUR_1)
            print(f"BTC 1시간봉 데이터: {count:,}개")
        """
        pass

    @abstractmethod
    def get_latest_timestamp(self, symbol: str, timeframe: Timeframe) -> Optional[datetime]:
        """
        최신 데이터 타임스탬프 조회
        
        Args:
            symbol: 심볼
            timeframe: 시간프레임
            
        Returns:
            Optional[datetime]: 최신 데이터의 타임스탬프 또는 None
            
        Example:
            latest = market_repo.get_latest_timestamp('KRW-BTC', Timeframe.MINUTE_1)
            if latest:
                print(f"BTC 최신 1분봉: {latest}")
        """
        pass

    # ===================================
    # 실시간 데이터 관리 메서드
    # ===================================

    @abstractmethod
    def get_real_time_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        실시간 시세 조회
        
        Args:
            symbol: 심볼
            
        Returns:
            Optional[Dict[str, Any]]: 실시간 시세 정보 또는 None
            
        Example:
            quote = market_repo.get_real_time_quote('KRW-BTC')
            # {
            #     'current_price': 50000000,
            #     'bid_price': 49999000,
            #     'ask_price': 50001000,
            #     'volume_24h': 1000.5,
            #     'price_change_rate_24h': 2.5
            # }
        """
        pass

    @abstractmethod
    def save_real_time_quote(self, symbol: str, quote_data: Dict[str, Any]) -> None:
        """
        실시간 시세 저장
        
        Args:
            symbol: 심볼
            quote_data: 시세 데이터
            
        Example:
            quote = {
                'current_price': 50000000,
                'bid_price': 49999000,
                'ask_price': 50001000,
                'volume_24h': 1000.5
            }
            market_repo.save_real_time_quote('KRW-BTC', quote)
        """
        pass

    @abstractmethod
    def get_order_book(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        호가창 정보 조회
        
        Args:
            symbol: 심볼
            
        Returns:
            Optional[Dict[str, Any]]: 호가창 정보 또는 None
            
        Example:
            orderbook = market_repo.get_order_book('KRW-BTC')
            # {
            #     'asks': [{'price': 50001000, 'size': 0.1}, ...],
            #     'bids': [{'price': 49999000, 'size': 0.2}, ...]
            # }
        """
        pass

    # ===================================
    # 데이터 정리 및 최적화 메서드
    # ===================================

    @abstractmethod
    def cleanup_old_data(self, timeframe: Timeframe, cutoff_date: datetime,
                        symbols: Optional[List[str]] = None) -> int:
        """
        오래된 데이터 정리
        
        Args:
            timeframe: 시간프레임
            cutoff_date: 삭제 기준일 (이전 데이터 삭제)
            symbols: 대상 심볼 목록 (None이면 전체)
            
        Returns:
            int: 삭제된 레코드 수
            
        Example:
            # 30일 이전 1분봉 데이터 삭제
            deleted = market_repo.cleanup_old_data(
                Timeframe.MINUTE_1,
                datetime.now() - timedelta(days=30)
            )
        """
        pass

    @abstractmethod
    def cleanup_indicator_cache(self, cutoff_date: datetime,
                              indicator_names: Optional[List[str]] = None) -> int:
        """
        오래된 지표 캐시 정리
        
        Args:
            cutoff_date: 삭제 기준일
            indicator_names: 대상 지표 목록 (None이면 전체)
            
        Returns:
            int: 삭제된 레코드 수
            
        Example:
            # 7일 이전 모든 지표 캐시 삭제
            deleted = market_repo.cleanup_indicator_cache(
                datetime.now() - timedelta(days=7)
            )
        """
        pass

    @abstractmethod
    def optimize_tables(self) -> None:
        """
        테이블 최적화 (VACUUM, REINDEX 등)
        
        Example:
            # 주기적 DB 최적화
            market_repo.optimize_tables()
        """
        pass

    @abstractmethod
    def get_storage_statistics(self) -> Dict[str, Any]:
        """
        저장소 통계 정보 조회
        
        Returns:
            Dict[str, Any]: 저장소 통계
            
        Example:
            stats = market_repo.get_storage_statistics()
            # {
            #     'total_records': 1000000,
            #     'size_mb': 250.5,
            #     'oldest_data': datetime(2024, 1, 1),
            #     'newest_data': datetime(2025, 8, 4),
            #     'symbols_count': 50
            # }
        """
        pass

    # ===================================
    # 백테스팅 최적화 메서드
    # ===================================

    @abstractmethod
    def preload_data_for_backtest(self, symbol: str, timeframe: Timeframe,
                                 start_date: datetime, end_date: datetime,
                                 required_indicators: List[Tuple[str, int]]) -> Dict[str, Any]:
        """
        백테스팅용 데이터 사전 로드 (성능 최적화)
        
        Args:
            symbol: 심볼
            timeframe: 시간프레임
            start_date: 시작일시
            end_date: 종료일시
            required_indicators: 필요한 지표 목록 [(지표명, 기간), ...]
            
        Returns:
            Dict[str, Any]: 사전 로드된 데이터 컨테이너
            
        Example:
            # 백테스팅용 데이터 사전 로드
            data_container = market_repo.preload_data_for_backtest(
                'KRW-BTC', Timeframe.HOUR_1,
                datetime(2024, 1, 1), datetime(2025, 1, 1),
                [('RSI', 14), ('SMA', 20), ('MACD', 12)]
            )
        """
        pass

    @abstractmethod
    def get_data_gaps(self, symbol: str, timeframe: Timeframe,
                     start_date: datetime, end_date: datetime) -> List[Tuple[datetime, datetime]]:
        """
        데이터 누락 구간 조회
        
        Args:
            symbol: 심볼
            timeframe: 시간프레임
            start_date: 시작일시
            end_date: 종료일시
            
        Returns:
            List[Tuple[datetime, datetime]]: 누락 구간 목록 [(시작, 끝), ...]
            
        Example:
            # BTC 1시간봉 데이터 누락 구간 찾기
            gaps = market_repo.get_data_gaps(
                'KRW-BTC', Timeframe.HOUR_1,
                datetime(2024, 1, 1), datetime(2025, 1, 1)
            )
        """
        pass
