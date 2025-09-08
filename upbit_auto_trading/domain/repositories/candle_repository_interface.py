"""
CandleDataProvider v4.0 - Minimal Domain Repository Interface
OverlapAnalyzer 전용 최소한의 인터페이스

설계 원칙:
- OverlapAnalyzer 요구사항에만 집중
- 필요한 기능을 하나씩 점진적으로 추가
- DDD Domain Layer 순수성 유지
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class DataRange:
    """기존 데이터 범위 (OverlapAnalyzer용)"""
    start_time: datetime
    end_time: datetime
    candle_count: int
    is_continuous: bool


class CandleRepositoryInterface(ABC):
    """캔들 데이터 Repository 인터페이스 - OverlapAnalyzer 전용 최소 구현"""

    @abstractmethod
    async def get_data_ranges(self,
                              symbol: str,
                              timeframe: str,
                              start_time: datetime,
                              end_time: datetime) -> List[DataRange]:
        """지정 구간의 기존 데이터 범위 조회 (OverlapAnalyzer 겹침 분석용)

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            start_time: 조회 시작 시간
            end_time: 조회 종료 시간

        Returns:
            List[DataRange]: 기존 데이터 범위 리스트
            - 데이터가 없으면 빈 리스트
            - 데이터가 있으면 연속된 구간별로 DataRange 객체 반환

        Note:
            - OverlapAnalyzer의 핵심 의존성
            - analyze_overlap() → _get_existing_data_ranges() → 이 메서드 호출
            - 겹침 상태 분석과 connected_end 찾기에 사용
        """
        pass

    @abstractmethod
    async def has_any_data_in_range(self,
                                    symbol: str,
                                    timeframe: str,
                                    start_time: datetime,
                                    end_time: datetime) -> bool:
        """지정 범위에 캔들 데이터 존재 여부 확인

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            start_time: 조회 시작 시간
            end_time: 조회 종료 시간

        Returns:
            bool: 데이터 존재 여부 (1개라도 있으면 True)

        Note:
            - overlap_optimizer의 _check_start_overlap 로직 기반
            - 효율적인 LIMIT 1 쿼리 활용
        """
        pass

    @abstractmethod
    async def is_range_complete(self,
                                symbol: str,
                                timeframe: str,
                                start_time: datetime,
                                end_time: datetime,
                                expected_count: int) -> bool:
        """지정 범위의 데이터 완전성 확인

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            start_time: 조회 시작 시간
            end_time: 조회 종료 시간
            expected_count: 예상 캔들 개수

        Returns:
            bool: 실제 개수 >= 예상 개수 여부

        Note:
            - overlap_optimizer의 _check_complete_overlap 로직 기반
            - 효율적인 COUNT 쿼리 활용
        """
        pass

    @abstractmethod
    async def find_last_continuous_time(self,
                                        symbol: str,
                                        timeframe: str,
                                        start_time: datetime) -> Optional[datetime]:
        """시작점부터 연속된 데이터의 마지막 시점 조회

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            start_time: 시작 시점

        Returns:
            Optional[datetime]: 연속된 데이터의 마지막 시점 (없으면 None)

        Note:
            - overlap_analyzer의 find_connected_end 단순화 버전
            - 효율적인 MAX 쿼리 활용
        """
        pass
