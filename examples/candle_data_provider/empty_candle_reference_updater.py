"""
EmptyCandleReferenceUpdater - 미참조 빈 캔들 참조점 자동 업데이트 처리기

Created: 2025-09-20
Purpose: 오버랩 분석 완료 후 'none_'으로 시작하는 미참조 빈 캔들 그룹을 자동 탐지하여 적절한 참조점으로 업데이트
Features: 6단계 검증 로직, 독립적 후처리, 메인 플로우 보호, Infrastructure 로깅
Architecture: DDD Infrastructure 계층, Repository 패턴, 단일 책임 원칙
"""

from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils
from upbit_auto_trading.infrastructure.market_data.candle.candle_models import OverlapResult
from upbit_auto_trading.domain.repositories.candle_repository_interface import (
    CandleRepositoryInterface
)

logger = create_component_logger("EmptyCandleReferenceUpdater")


@dataclass(frozen=True)
class UpdateResult:
    """참조점 업데이트 결과"""
    success: bool
    group_id: Optional[str] = None
    new_reference: Optional[str] = None
    updated_count: int = 0
    skip_reason: Optional[str] = None
    error_message: Optional[str] = None


class EmptyCandleReferenceUpdater:
    """
    미참조 빈 캔들 참조점 자동 업데이트 처리기

    핵심 기능:
    1. 오버랩 분석 완료 후 후처리로 실행
    2. db_start~db_end 범위에서 'none_' 미참조 빈 캔들 탐지
    3. 해당 시점의 한 틱 미래 레코드 조회하여 참조점 결정
    4. 미참조 그룹 전체를 새 참조점으로 일괄 업데이트

    설계 원칙:
    - Infrastructure 계층: 기술적 세부사항 캡슐화
    - Repository 패턴: DB 접근 로직 분리
    - 단일 책임 원칙: 참조 업데이트만 담당
    - 독립적 처리: 메인 수집 프로세스와 완전 분리
    - 안전성: 에러 발생 시 메인 플로우에 영향 없음
    """

    def __init__(self, repository: CandleRepositoryInterface):
        """
        Args:
            repository: CandleRepositoryInterface 구현체 (의존성 주입)
        """
        self.repository = repository
        logger.info("EmptyCandleReferenceUpdater 초기화 완료 - 미참조 빈 캔들 후처리 지원")

    async def process_unreferenced_empty_candles(
        self,
        overlap_result: OverlapResult,
        symbol: str,
        timeframe: str
    ) -> UpdateResult:
        """
        6단계 조건 검증 및 참조점 업데이트 실행

        비즈니스 로직 플로우:
        1. OverlapResult에 db_start, db_end 존재 확인
        2. find_unreferenced_empty_candle_in_range(db_start, db_end) → 범위 내 미참조 빈 캔들 검색
        3. 미참조 빈 캔들 발견되면:
           ├─ 그룹 ID 추출 (예: 'none_d1dea30f')
           ├─ 해당 시점의 한 틱 미래 레코드 조회 (get_record_by_time)
           └─ 미래 레코드의 empty_copy_from_utc 확인
        4. 참조점 결정:
           ├─ 값 존재 → 해당 값으로 그룹 업데이트
           └─ NULL → candle_date_time_utc로 그룹 업데이트
        5. 발견되지 않으면 처리 건너뛰기

        Args:
            overlap_result: 오버랩 분석 결과 (db_start, db_end 포함)
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m')

        Returns:
            UpdateResult: 업데이트 결과 (성공/실패, 상세 정보)
        """
        try:
            # 1단계: OverlapResult 조건 검증
            if not overlap_result.db_start or not overlap_result.db_end:
                skip_reason = f"DB 범위 부족 (db_start={overlap_result.db_start}, db_end={overlap_result.db_end})"
                logger.debug(f"미참조 빈 캔들 처리 건너뛰기: {symbol} {timeframe} - {skip_reason}")
                return UpdateResult(success=True, skip_reason=skip_reason)

            # 2단계: 범위 내 미참조 빈 캔들 검색
            unreferenced_candle = await self.repository.find_unreferenced_empty_candle_in_range(
                symbol, timeframe, overlap_result.db_start, overlap_result.db_end
            )

            if not unreferenced_candle:
                skip_reason = f"미참조 빈 캔들 없음 ({overlap_result.db_start} ~ {overlap_result.db_end})"
                logger.debug(f"미참조 빈 캔들 처리 건너뛰기: {symbol} {timeframe} - {skip_reason}")
                return UpdateResult(success=True, skip_reason=skip_reason)

            # 3단계: 그룹 ID 추출 및 검증
            group_id = unreferenced_candle['empty_copy_from_utc']
            candle_time_str = unreferenced_candle['candle_date_time_utc']

            if not group_id or not group_id.startswith('none_'):
                error_msg = f"유효하지 않은 그룹 ID: {group_id}"
                logger.warning(f"미참조 빈 캔들 처리 실패: {symbol} {timeframe} - {error_msg}")
                return UpdateResult(success=False, error_message=error_msg)

            logger.info(f"미참조 빈 캔들 발견: {symbol} {timeframe} {candle_time_str} (그룹: {group_id})")

            # 4단계: 해당 시점의 한 틱 미래 레코드 조회
            candle_time_str_clean = candle_time_str.replace('Z', '')
            candle_time = datetime.fromisoformat(candle_time_str_clean)

            # UTC timezone 명시적 설정 (DB 저장 형식과 호환)
            if candle_time.tzinfo is None:
                candle_time = candle_time.replace(tzinfo=timezone.utc)

            future_time = TimeUtils.get_time_by_ticks(candle_time, timeframe, 1)

            future_record = await self.repository.get_record_by_time(
                symbol, timeframe, future_time
            )

            # 5단계: 참조점 결정
            if not future_record:
                # 미래 레코드 없음 → 현재 시점을 참조점으로 사용
                new_reference = candle_time_str
                logger.info(f"미래 레코드 없음, 현재 시점 참조: {candle_time_str}")
            else:
                # 미래 레코드의 empty_copy_from_utc 확인
                future_empty_ref = future_record.get('empty_copy_from_utc')
                if future_empty_ref:
                    # 미래 레코드에 참조 존재 → 해당 값 사용
                    new_reference = future_empty_ref
                    logger.info(f"미래 레코드 참조 발견: {future_empty_ref}")
                else:
                    # 미래 레코드가 실제 캔들 → 해당 시점 사용
                    new_reference = future_record['candle_date_time_utc']
                    logger.info(f"미래 실제 캔들 참조: {new_reference}")

            # 6단계: 그룹 일괄 업데이트 실행
            updated_count = await self.repository.update_empty_copy_reference_by_group(
                symbol, timeframe, group_id, new_reference
            )

            if updated_count > 0:
                logger.info(f"미참조 그룹 참조점 업데이트 완료: {group_id} → {new_reference} ({updated_count}개)")
                return UpdateResult(
                    success=True,
                    group_id=group_id,
                    new_reference=new_reference,
                    updated_count=updated_count
                )
            else:
                error_msg = f"업데이트 대상 없음 (그룹: {group_id})"
                logger.warning(f"미참조 빈 캔들 업데이트 실패: {symbol} {timeframe} - {error_msg}")
                return UpdateResult(success=False, error_message=error_msg)

        except Exception as e:
            error_msg = f"미참조 빈 캔들 처리 중 오류: {type(e).__name__}: {e}"
            logger.warning(f"참조점 업데이트 실패 (무시): {symbol} {timeframe} - {error_msg}")
            return UpdateResult(success=False, error_message=error_msg)

    def _extract_group_id_from_empty_reference(self, empty_copy_from_utc: str) -> Optional[str]:
        """
        empty_copy_from_utc에서 그룹 ID 추출

        Args:
            empty_copy_from_utc: 빈 캔들 참조 필드 값

        Returns:
            그룹 ID 또는 None (유효하지 않은 경우)

        Note:
            - 'none_xxxxxxxx' 형태에서 전체 문자열이 그룹 ID
            - 간단한 검증만 수행 (startswith 체크)
        """
        if not empty_copy_from_utc or not isinstance(empty_copy_from_utc, str):
            return None

        if empty_copy_from_utc.startswith('none_'):
            return empty_copy_from_utc
        else:
            return None

    def get_processing_stats(self) -> dict:
        """
        처리 통계 반환 (향후 모니터링용)

        Returns:
            dict: 처리 통계 정보

        Note:
            - 현재는 기본 정보만 반환
            - 향후 처리 횟수, 성공률 등 추가 가능
        """
        return {
            'component': 'EmptyCandleReferenceUpdater',
            'purpose': '미참조 빈 캔들 참조점 자동 업데이트',
            'trigger': '오버랩 분석 완료 후',
            'safety': '독립적 후처리, 메인 플로우 보호'
        }
