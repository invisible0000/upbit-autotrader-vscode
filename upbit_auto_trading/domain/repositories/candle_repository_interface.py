"""
CandleDataProvider v4.0 - Domain Repository Interface

DDD Domain Layer의 핵심 인터페이스로 캔들 데이터 영속성을 추상화합니다.
Infrastructure Layer에서 이 인터페이스를 구현해야 합니다.

Design Principles:
- Domain Layer 순수성: 외부 의존성 없음 (sqlite3, requests 등 금지)
- Repository 패턴: 데이터 저장소 세부사항 추상화
- 업비트 특화: 심볼별 개별 테이블 구조 지원
- 성능 최적화: DatabaseManager 활용을 위한 인터페이스 설계
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass(frozen=True)
class CandleData:
    """캔들 데이터 도메인 모델"""
    market: str
    candle_date_time_utc: datetime
    candle_date_time_kst: datetime
    opening_price: float
    high_price: float
    low_price: float
    trade_price: float
    timestamp: int
    candle_acc_trade_price: float
    candle_acc_trade_volume: float
    unit: int = 1
    trade_count: int = 0


@dataclass(frozen=True)
class CandleQueryResult:
    """캔들 조회 결과"""
    candles: List[CandleData]
    total_count: int
    query_time_ms: float
    cache_hit: bool = False


class CandleRepositoryInterface(ABC):
    """캔들 데이터 Repository 인터페이스 (DDD Domain Layer)"""

    # === 핵심 CRUD 메서드 ===

    @abstractmethod
    async def save_candles(self, symbol: str, timeframe: str, candles: List[CandleData]) -> int:
        """캔들 데이터 저장 (INSERT OR IGNORE 기반 중복 자동 처리)

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m', '1h')
            candles: 저장할 캔들 데이터 리스트

        Returns:
            실제 삽입된 레코드 수 (중복 제외)

        Note:
            - candle_date_time_utc PRIMARY KEY로 중복 자동 차단
            - 배치 처리로 성능 최적화 (executemany 활용)
        """
        pass

    @abstractmethod
    async def get_candles(self,
                          symbol: str,
                          timeframe: str,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          count: Optional[int] = None,
                          order_desc: bool = True) -> CandleQueryResult:
        """캔들 데이터 조회

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임
            start_time: 시작 시간 (None이면 제한없음)
            end_time: 종료 시간 (None이면 제한없음)
            count: 최대 조회 개수 (None이면 제한없음)
            order_desc: 내림차순 정렬 여부 (최신순)

        Returns:
            CandleQueryResult 객체 (캔들 리스트 + 메타데이터)
        """
        pass

    @abstractmethod
    async def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[CandleData]:
        """최신 캔들 데이터 조회

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임

        Returns:
            최신 캔들 데이터 또는 None (데이터 없음)
        """
        pass

    @abstractmethod
    async def count_candles(self,
                            symbol: str,
                            timeframe: str,
                            start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None) -> int:
        """캔들 데이터 개수 조회

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임
            start_time: 시작 시간 (None이면 제한없음)
            end_time: 종료 시간 (None이면 제한없음)

        Returns:
            조건에 맞는 캔들 데이터 개수
        """
        pass

    # === 테이블 관리 메서드 ===

    @abstractmethod
    async def ensure_table_exists(self, symbol: str, timeframe: str) -> str:
        """캔들 테이블 존재 확인 및 생성

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m', '1h')

        Returns:
            생성/확인된 테이블명 (예: 'candles_KRW_BTC_1m')

        Note:
            - 테이블명 패턴: candles_{SYMBOL}_{TIMEFRAME}
            - 동적 테이블 생성으로 심볼별 성능 최적화
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

    @abstractmethod
    async def get_table_stats(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """특정 캔들 테이블 통계 조회

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임

        Returns:
            테이블 통계 정보 (레코드 수, 시간 범위, 크기 등)
        """
        pass

    @abstractmethod
    async def get_all_candle_tables(self) -> List[Dict[str, Any]]:
        """모든 캔들 테이블 목록 조회

        Returns:
            모든 캔들 테이블의 메타정보 리스트
            - table_name: 테이블명
            - symbol: 심볼
            - timeframe: 타임프레임
            - record_count: 레코드 수
            - size_mb: 테이블 크기 (MB)
            - latest_time: 최신 데이터 시간
        """
        pass

    # === 4단계 최적화 지원 메서드 ===

    @abstractmethod
    async def check_complete_overlap(self,
                                     symbol: str,
                                     timeframe: str,
                                     start_time: datetime,
                                     count: int) -> bool:
        """완전 겹침 확인 (4단계 최적화 - Step 2)

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임
            start_time: 시작 시간
            count: 요청 개수

        Returns:
            완전 겹침 여부 (DB 개수 == 요청 개수)

        Note:
            - COUNT 쿼리로 초고속 겹침 판별
            - API 호출 완전 회피 가능 여부 확인
        """
        pass

    @abstractmethod
    async def check_fragmentation(self,
                                  symbol: str,
                                  timeframe: str,
                                  start_time: datetime,
                                  count: int,
                                  gap_threshold_seconds: int) -> int:
        """파편화 겹침 확인 (4단계 최적화 - Step 3)

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임
            start_time: 시작 시간
            count: 확인 개수
            gap_threshold_seconds: 간격 임계값 (초)

        Returns:
            파편화 개수 (끊어진 구간 수)

        Note:
            - LAG 윈도우 함수로 연속성 확인
            - 2번 이상 끊어지면 전체 재요청이 효율적
        """
        pass

    @abstractmethod
    async def find_connected_end(self,
                                 symbol: str,
                                 timeframe: str,
                                 start_time: datetime,
                                 max_count: int = 200) -> Optional[datetime]:
        """연결된 끝 찾기 (4단계 최적화 - Step 4)

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임
            start_time: 시작 시간
            max_count: 최대 확인 개수 (업비트 200개 제한)

        Returns:
            연속된 데이터의 끝 시간 또는 None

        Note:
            - ROW_NUMBER + datetime 함수로 연속성 확인
            - 연속된 구간의 정확한 끝점 탐지
        """
        pass

    # === 성능 모니터링 메서드 ===

    @abstractmethod
    async def get_performance_metrics(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """성능 지표 조회

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임

        Returns:
            성능 지표 딕셔너리
            - avg_query_time_ms: 평균 쿼리 시간
            - cache_hit_rate: 캐시 히트율
            - table_size_mb: 테이블 크기
            - fragmentation_rate: 파편화 비율
            - last_update_time: 마지막 업데이트 시간
        """
        pass

    # === 데이터 품질 검증 메서드 ===

    @abstractmethod
    async def validate_data_integrity(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """데이터 무결성 검증

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임

        Returns:
            무결성 검증 결과
            - duplicate_count: 중복 데이터 수 (0이어야 함)
            - missing_count: 누락 추정 수
            - time_consistency: 시간 정렬 일관성
            - data_coverage_rate: 데이터 커버리지 비율
        """
        pass
