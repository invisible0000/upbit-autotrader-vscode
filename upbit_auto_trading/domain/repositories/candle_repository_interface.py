"""
캔들 데이터 Repository 인터페이스

DDD Domain Layer의 핵심 인터페이스로, 캔들 데이터 영속성을 추상화합니다.
Infrastructure Layer에서 이 인터페이스를 구현해야 합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any


class CandleRepositoryInterface(ABC):
    """캔들 데이터 Repository 인터페이스"""

    @abstractmethod
    async def ensure_table_exists(self, symbol: str, timeframe: str) -> str:
        """캔들 테이블 존재 확인 및 생성

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m', '1h')

        Returns:
            생성/확인된 테이블명
        """
        pass

    @abstractmethod
    async def ensure_symbol_exists(self, symbol: str) -> bool:
        """심볼이 market_symbols 테이블에 존재하는지 확인하고 없으면 등록

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')

        Returns:
            심볼 등록/확인 성공 여부
        """
        pass

    @abstractmethod
    async def insert_candles(self, symbol: str, timeframe: str, candles: List[Dict]) -> int:
        """캔들 데이터 삽입

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임
            candles: 캔들 데이터 리스트

        Returns:
            실제 삽입된 레코드 수
        """
        pass

    @abstractmethod
    async def get_candles(self,
                          symbol: str,
                          timeframe: str,
                          start_time: Optional[str] = None,
                          end_time: Optional[str] = None,
                          limit: Optional[int] = None) -> List[Dict]:
        """캔들 데이터 조회

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임
            start_time: 시작 시간 (ISO format)
            end_time: 종료 시간 (ISO format)
            limit: 최대 조회 개수

        Returns:
            캔들 데이터 리스트
        """
        pass

    @abstractmethod
    async def get_table_stats(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """특정 캔들 테이블 통계 조회

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임

        Returns:
            테이블 통계 정보 (레코드 수, 시간 범위 등)
        """
        pass

    @abstractmethod
    async def get_all_candle_tables(self) -> List[Dict[str, Any]]:
        """모든 캔들 테이블 목록 조회

        Returns:
            모든 캔들 테이블의 메타정보 리스트
        """
        pass

    @abstractmethod
    async def table_exists(self, symbol: str, timeframe: str) -> bool:
        """캔들 테이블 존재 여부 확인

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임

        Returns:
            테이블 존재 여부
        """
        pass
