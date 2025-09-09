"""
CandleDataProvider v4.0 - Enhanced Domain Repository Interface
OverlapAnalyzer 지원 + 새로운 CandleData 모델 지원

설계 원칙:
- OverlapAnalyzer 기존 메서드 완전 호환 유지
- 새로운 CandleData 모델 지원 메서드 추가
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
    """캔들 데이터 Repository 인터페이스 - OverlapAnalyzer + CandleDataProvider v4.0 지원"""

    # === OverlapAnalyzer 전용 메서드들 (기존 호환성 보장) ===

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
            - 효율적인 LEAD 윈도우 함수 활용 (309x 최적화)
        """
        pass

    @abstractmethod
    async def has_data_at_time(self, symbol: str, timeframe: str, target_time: datetime) -> bool:
        """특정 시점에 캔들 데이터 존재 여부 확인

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            target_time: 확인할 특정 시점

        Returns:
            bool: 해당 시점에 데이터 존재 여부

        Note:
            - OverlapAnalyzer v5.0의 has_data_in_start용
            - PRIMARY KEY 점검색으로 최고 성능
        """
        pass

    @abstractmethod
    async def find_data_start_in_range(self, symbol: str, timeframe: str,
                                       start_time: datetime, end_time: datetime) -> Optional[datetime]:
        """범위 내 데이터 시작점 찾기

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.')
            start_time: 조회 시작 시간
            end_time: 조회 종료 시간

        Returns:
            Optional[datetime]: 범위 내 가장 최신 데이터 시점 (없으면 None)

        Note:
            - OverlapAnalyzer v5.0의 중간 겹침 분석용
            - 업비트 서버 내림차순 특성: MAX가 '시작점'
            - PRIMARY KEY 인덱스 활용으로 빠른 성능
        """
        pass

    # === CandleDataProvider v4.0 새로운 메서드들 ===

    @abstractmethod
    async def ensure_table_exists(self, symbol: str, timeframe: str) -> str:
        """캔들 테이블 생성 (새로운 스키마 적용)

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)

        Returns:
            str: 생성된 테이블명

        Note:
            - 업비트 API 호환 스키마 적용
            - PRIMARY KEY (candle_date_time_utc) 사용
            - timeframe_specific_data JSON 컬럼 포함
        """
        pass

    @abstractmethod
    async def save_candle_chunk(self, symbol: str, timeframe: str, candles) -> int:
        """캔들 데이터 청크 저장

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            candles: CandleData 객체 리스트

        Returns:
            int: 저장된 캔들 개수

        Note:
            - 새로운 CandleData 모델 지원
            - INSERT OR IGNORE 방식으로 중복 처리 (중복시 삽입 무시)
            - UTC 시간 PRIMARY KEY + 업비트 데이터 불변성 활용
            - 배치 삽입으로 성능 최적화
        """
        pass

    @abstractmethod
    async def get_candles_by_range(self, symbol: str, timeframe: str, start_time: datetime, end_time: datetime) -> List:
        """지정 범위의 캔들 데이터 조회 (새로운 CandleData 모델 반환)

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            start_time: 조회 시작 시간
            end_time: 조회 종료 시간

        Returns:
            List[CandleData]: 새로운 CandleData 모델 리스트

        Note:
            - PRIMARY KEY 범위 스캔 활용
            - JSON 필드 파싱 포함
            - 시간순 정렬 보장
        """
        pass
