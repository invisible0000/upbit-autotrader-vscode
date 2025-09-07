"""
캔들 데이터 Repository 인터페이스

DDD Domain Layer의 핵심 인터페이스로, 캔들 데이터 영속성을 추상화합니다.
Infrastructure Layer에서 이 인터페이스를 구현해야 합니다.
"""

from abc import ABC, abstractmethod
from datetime import datetime
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

    # === 수집 상태 관리 메서드 (Smart Candle Collector 기능) ===

    @abstractmethod
    async def get_collection_status(
        self,
        symbol: str,
        timeframe: str,
        target_time: datetime
    ) -> Optional[Dict[str, Any]]:
        """특정 시간의 수집 상태 조회

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임
            target_time: 대상 시간

        Returns:
            수집 상태 정보 또는 None
        """
        pass

    @abstractmethod
    async def update_collection_status(
        self,
        symbol: str,
        timeframe: str,
        target_time: datetime,
        status: str,
        api_response_code: Optional[int] = None
    ) -> None:
        """수집 상태 업데이트

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임
            target_time: 대상 시간
            status: 수집 상태 ('COLLECTED', 'EMPTY', 'PENDING', 'FAILED')
            api_response_code: API 응답 코드
        """
        pass

    @abstractmethod
    async def get_missing_candle_times(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[datetime]:
        """미수집 캔들 시간 목록 조회

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임
            start_time: 시작 시간
            end_time: 종료 시간

        Returns:
            미수집 캔들 시간 목록
        """
        pass

    @abstractmethod
    async def get_empty_candle_times(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[datetime]:
        """빈 캔들 시간 목록 조회

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임
            start_time: 시작 시간
            end_time: 종료 시간

        Returns:
            빈 캔들 시간 목록
        """
        pass

    @abstractmethod
    async def get_continuous_candles(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        include_empty: bool = True
    ) -> List[Dict[str, Any]]:
        """연속된 캔들 데이터 조회 (빈 캔들 포함/제외 선택 가능)

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임
            start_time: 시작 시간
            end_time: 종료 시간
            include_empty: 빈 캔들 포함 여부

        Returns:
            연속된 캔들 데이터 (빈 캔들 포함/제외)
        """
        pass
