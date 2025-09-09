"""
CandleDataProvider v4.0 - OverlapAnalyzer
API 요청 최적화 분석 엔진

핵심 목적: overlap_optimizer의 효율적 쿼리 패턴을 활용하여
이미 존재하는 데이터는 API 요청하지 않고 DB에서 조회하여 효율성 극대화

설계 원칙:
- Repository 패턴 활용: DDD 계층 분리 준수
- 단순한 인터페이스: analyze_overlap 하나로 모든 정보 제공
- 효율적 쿼리: overlap_optimizer의 검증된 SQL 패턴 활용
"""

from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from enum import Enum

from upbit_auto_trading.domain.repositories.candle_repository_interface import CandleRepositoryInterface
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("OverlapAnalyzer")


class OverlapStatus(Enum):
    """겹침 상태"""
    NO_OVERLAP = "no_overlap"              # 겹침 없음 → 전체 구간 API 요청 필요
    PARTIAL_OVERLAP = "partial_overlap"     # 부분 겹침 → 일부는 DB 조회, 일부는 API 요청
    COMPLETE_OVERLAP = "complete_overlap"   # 완전 겹침 → API 요청 없이 DB에서만 조회


@dataclass(frozen=True)
class OverlapResult:
    """겹침 분석 결과 - API 요청 최적화 정보"""
    status: OverlapStatus
    connected_end: Optional[datetime]  # 연속된 데이터의 끝점 (이 시점까지는 DB 조회 가능)


class OverlapAnalyzer:
    """
    API 요청 최적화 분석 엔진 (overlap_optimizer 효율적 쿼리 기반)

    핵심 목적: 이미 존재하는 데이터는 API 요청하지 않고 DB에서 조회하여 효율성 극대화

    역할:
    - Repository 패턴을 통한 효율적 DB 조회
    - overlap_optimizer의 검증된 쿼리 패턴 활용
    - 단순하고 명확한 겹침 상태 반환
    """

    def __init__(self, repository: CandleRepositoryInterface, time_utils):
        """
        Args:
            repository: 캔들 데이터 저장소 (DDD Repository 패턴)
            time_utils: 시간 유틸리티 (timeframe 계산용)
        """
        self.repository = repository
        self.time_utils = time_utils

        logger.info("OverlapAnalyzer 초기화 완료 - overlap_optimizer 효율적 쿼리 기반")

    async def analyze_overlap(
        self,
        symbol: str,
        timeframe: str,
        target_start: datetime,
        target_count: int
    ) -> OverlapResult:
        """
        효율적 겹침 분석: overlap_optimizer 패턴을 Repository로 활용

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            target_start: 요청 시작 시간
            target_count: 요청 캔들 개수

        Returns:
            OverlapResult: 겹침 상태 + connected_end

        동작 원리 (overlap_optimizer 기반):
        1. has_any_data_in_range: 데이터 존재 여부 확인 (LIMIT 1)
        2. is_range_complete: 완전 겹침 확인 (COUNT vs expected)
        3. find_last_continuous_time: 연속된 끝점 찾기 (MAX 쿼리)
        """
        logger.debug(f"겹침 분석 시작: {symbol} {timeframe} {target_start} ~ {target_count}개")

        # 요청 범위 계산
        timeframe_seconds = self.time_utils.get_timeframe_seconds(timeframe)
        target_end = target_start + timedelta(seconds=timeframe_seconds * (target_count - 1))

        # 1. 단순한 데이터 존재 확인 (overlap_optimizer _check_start_overlap 방식)
        has_data = await self.repository.has_any_data_in_range(
            symbol, timeframe, target_start, target_end
        )

        if not has_data:
            logger.debug("데이터 없음 → NO_OVERLAP")
            return OverlapResult(status=OverlapStatus.NO_OVERLAP, connected_end=None)

        # 2. 완전 겹침 확인 (overlap_optimizer _check_complete_overlap 방식)
        is_complete = await self.repository.is_range_complete(
            symbol, timeframe, target_start, target_end, target_count
        )

        if is_complete:
            logger.debug("완전 겹침 → COMPLETE_OVERLAP")
            return OverlapResult(status=OverlapStatus.COMPLETE_OVERLAP, connected_end=target_end)

        # 3. 부분 겹침 - 연속된 끝점 찾기 (효율적 MAX 쿼리)
        connected_end = await self.repository.find_last_continuous_time(
            symbol, timeframe, target_start
        )

        logger.debug(f"부분 겹침 → PARTIAL_OVERLAP, connected_end={connected_end}")
        return OverlapResult(status=OverlapStatus.PARTIAL_OVERLAP, connected_end=connected_end)

    def get_overlap_summary(self, result: OverlapResult, target_count: int) -> str:
        """
        겹침 분석 결과 요약 (디버깅/로깅용)

        Args:
            result: 겹침 분석 결과
            target_count: 요청한 캔들 개수

        Returns:
            str: 사람이 읽기 쉬운 요약 메시지
        """
        if result.status == OverlapStatus.NO_OVERLAP:
            return f"겹침 없음 → 전체 {target_count}개 API 요청 필요"

        elif result.status == OverlapStatus.COMPLETE_OVERLAP:
            return f"완전 겹침 → API 요청 없이 DB에서 {target_count}개 조회 가능"

        elif result.status == OverlapStatus.PARTIAL_OVERLAP:
            if result.connected_end:
                return "부분 겹침 → connected_end까지 DB 조회, 그 이후 API 요청"
            else:
                return "부분 겹침 → 하지만 연속 데이터 없음, API 요청 필요"

        return "알 수 없는 겹침 상태"
