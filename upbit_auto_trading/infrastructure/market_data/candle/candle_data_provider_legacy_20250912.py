"""
📋 CandleDataProvider v4.0 - TASK_02 Implementation
요청 정규화 및 청크 생성 로직 구현

Created: 2025-09-11
Purpose: normalize_request와 create_chunks 메서드 구현
Features: 4가지 파라미터 조합 지원, 설정 가능한 청크 분할
"""

from datetime import datetime
from typing import Optional, Tuple
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils
from upbit_auto_trading.infrastructure.market_data.candle.candle_models import (
    RequestInfo, ChunkPlan, ChunkInfo
)

logger = create_component_logger("CandleDataProvider")

# ============================================================================
# 🧪 테스트 및 설정 변수 - 청크 사이즈 조정 가능
# ============================================================================

# 📋 청크 사이즈 설정 (업비트 API 최대 제한: 200개)
# 테스트 시 작은 값(5, 10)으로 변경하여 청크 분할 동작 확인 가능
# 운영 시에는 200으로 설정하여 API 효율성 극대화
CHUNK_SIZE = 200

# 📋 기본 캔들 개수 설정
# count가 지정되지 않았을 때 사용하는 기본값
DEFAULT_CANDLE_COUNT = CHUNK_SIZE

# ============================================================================


class RequestType(Enum):
    """요청 타입 분류"""
    COUNT_ONLY = "count_only"                    # count만 지정
    COUNT_WITH_TO = "count_with_to"              # count + to 지정
    TO_WITH_END = "to_with_end"                  # to + end 지정
    END_ONLY = "end_only"                        # end만 지정


class ChunkStatus(Enum):
    """청크 처리 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CandleDataProvider:
    """
    캔들 데이터 제공자 v4.0 - TASK_02 구현

    주요 기능:
    - normalize_request: 4가지 파라미터 조합을 표준 형태로 변환
    - create_chunks: 대량 요청을 설정 가능한 단위로 분할
    """

    def __init__(self):
        """CandleDataProvider 초기화"""
        logger.info("CandleDataProvider v4.0 (TASK_02) 초기화 시작...")
        logger.info("✅ CandleDataProvider v4.0 초기화 완료")

    def normalize_request(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        to: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> RequestInfo:
        """
        요청 파라미터를 표준 형태로 정규화

        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m', '1h', '1d')
            count: 조회할 캔들 개수 (1~CHUNK_SIZE)
            to: 시작 시간 (이 시점부터 과거로)
            end: 종료 시간 (이 시점까지)

        Returns:
            RequestInfo: 정규화된 요청 정보

        Raises:
            ValueError: 잘못된 파라미터 조합 또는 범위
        """
        logger.info(f"요청 정규화: {symbol} {timeframe}, count={count}, to={to}, end={end}")

        # 1. 기본 검증
        if not symbol or not timeframe:
            raise ValueError("symbol과 timeframe은 필수입니다")

        # 2. 파라미터 조합 분석 및 요청 타입 결정
        request_type = self._determine_request_type(count, to, end)
        logger.debug(f"요청 타입 결정: {request_type.value}")

        # 3. 각 타입별 검증 및 정규화 (None 체크 포함)
        if request_type == RequestType.COUNT_ONLY:
            return self._normalize_count_only(symbol, timeframe, count)
        elif request_type == RequestType.COUNT_WITH_TO:
            if count is None or to is None:
                raise ValueError("COUNT_WITH_TO 타입에는 count와 to가 필요합니다")
            return self._normalize_count_with_to(symbol, timeframe, count, to)
        elif request_type == RequestType.TO_WITH_END:
            if to is None or end is None:
                raise ValueError("TO_WITH_END 타입에는 to와 end가 필요합니다")
            return self._normalize_to_with_end(symbol, timeframe, to, end)
        elif request_type == RequestType.END_ONLY:
            if end is None:
                raise ValueError("END_ONLY 타입에는 end가 필요합니다")
            return self._normalize_end_only(symbol, timeframe, end)
        else:
            raise ValueError(f"지원하지 않는 요청 타입: {request_type}")

    def _determine_request_type(
        self,
        count: Optional[int],
        to: Optional[datetime],
        end: Optional[datetime]
    ) -> RequestType:
        """파라미터 조합을 분석하여 요청 타입 결정"""
        has_count = count is not None
        has_to = to is not None
        has_end = end is not None

        if has_count and has_to and has_end:
            raise ValueError("count, to, end는 동시에 사용할 수 없습니다")
        elif has_count and has_to and not has_end:
            return RequestType.COUNT_WITH_TO
        elif not has_count and has_to and has_end:
            return RequestType.TO_WITH_END
        elif not has_count and not has_to and has_end:
            return RequestType.END_ONLY
        elif has_count and not has_to and not has_end:
            return RequestType.COUNT_ONLY
        else:
            # 기본값: count=DEFAULT_CANDLE_COUNT
            return RequestType.COUNT_ONLY

    def _normalize_count_only(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int]
    ) -> RequestInfo:
        """count만 지정된 경우 처리"""
        final_count = count or DEFAULT_CANDLE_COUNT

        # count 최소값 검증 (최대값은 청크 분할로 처리)
        if final_count < 1:
            raise ValueError(f"count는 1 이상이어야 합니다: {final_count}")

        return RequestInfo(
            symbol=symbol,
            timeframe=timeframe,
            request_type=RequestType.COUNT_ONLY.value,
            count=final_count,
            to=None,
            end=None
        )

    def _normalize_count_with_to(
        self,
        symbol: str,
        timeframe: str,
        count: int,
        to: datetime
    ) -> RequestInfo:
        """count + to 지정된 경우 처리"""
        if count < 1:
            raise ValueError(f"count는 1 이상이어야 합니다: {count}")

        # to 시점 검증 (미래 시간 금지)
        if to > datetime.now():
            raise ValueError(f"to 시점이 미래입니다: {to}")

        return RequestInfo(
            symbol=symbol,
            timeframe=timeframe,
            request_type=RequestType.COUNT_WITH_TO.value,
            count=count,
            to=to,
            end=None
        )

    def _normalize_to_with_end(
        self,
        symbol: str,
        timeframe: str,
        to: datetime,
        end: datetime
    ) -> RequestInfo:
        """to + end 지정된 경우 처리"""
        # 시간 순서 검증
        if to <= end:
            raise ValueError(f"to는 end보다 이후 시점이어야 합니다: to={to}, end={end}")

        # RequestInfo에는 count=None으로 설정 (모델 검증 규칙)
        return RequestInfo(
            symbol=symbol,
            timeframe=timeframe,
            request_type=RequestType.TO_WITH_END.value,
            count=None,  # to_with_end 타입에서는 count 사용 안함
            to=to,
            end=end
        )

    def _normalize_end_only(
        self,
        symbol: str,
        timeframe: str,
        end: datetime
    ) -> RequestInfo:
        """end만 지정된 경우 처리 (현재 시점부터 end까지)"""
        # end 시점 검증 (과거 시점만 허용)
        if end > datetime.now():
            raise ValueError(f"end 시점이 미래입니다: {end}")

        # end_only는 내부적으로 to_with_end 타입으로 처리
        # 현재 시간을 to로, 사용자 지정 시간을 end로 설정
        current_time = datetime.now()

        return RequestInfo(
            symbol=symbol,
            timeframe=timeframe,
            request_type=RequestType.TO_WITH_END.value,  # 내부적으로 to_with_end로 변환
            count=None,
            to=current_time,  # 현재 시간
            end=end          # 사용자 지정 과거 시간
        )

    def create_chunks(self, request: RequestInfo) -> ChunkPlan:
        """
        정규화된 요청을 설정 가능한 단위로 청크 분할

        Args:
            request: 정규화된 요청 정보

        Returns:
            ChunkPlan: 청크 분할 계획
        """
        logger.info(f"청크 생성: {request.symbol} {request.timeframe}, count={request.count}")

        # 설정된 청크 크기 사용
        chunk_size = CHUNK_SIZE

        # 총 청크 개수 계산
        if request.count is not None:
            total_count = request.count
        elif request.request_type == RequestType.TO_WITH_END.value and request.to and request.end:
            # to_with_end 타입: 시간 범위에서 예상 캔들 개수 계산
            total_count = TimeUtils.calculate_expected_count(
                start_time=request.end,
                end_time=request.to,
                timeframe=request.timeframe
            )
        elif request.request_type == RequestType.END_ONLY.value:
            # end_only 타입: 현재 시점부터 end까지의 캔들 개수 계산
            current_time = datetime.now()
            if request.end:
                total_count = TimeUtils.calculate_expected_count(
                    start_time=current_time,
                    end_time=request.end,
                    timeframe=request.timeframe
                )
            else:
                total_count = DEFAULT_CANDLE_COUNT
        else:
            total_count = DEFAULT_CANDLE_COUNT  # 기본값
        total_chunks = (total_count + chunk_size - 1) // chunk_size  # 올림 계산

        logger.debug(f"청크 분할: 총 {total_count}개 캔들 → {total_chunks}개 청크")

        # 청크 리스트 생성
        chunks = []

        for chunk_index in range(total_chunks):
            # 현재 청크의 시작 위치와 개수 계산
            start_position = chunk_index * chunk_size
            remaining_count = total_count - start_position
            current_chunk_count = min(chunk_size, remaining_count)

            # 청크별 시간 범위 계산
            chunk_to, chunk_end = self._calculate_chunk_time_range(
                request, chunk_index, current_chunk_count
            )

            # ChunkInfo 생성
            chunk_id = f"{request.symbol}_{request.timeframe}_{chunk_index:05d}"
            chunk_info = ChunkInfo(
                chunk_id=chunk_id,
                chunk_index=chunk_index,
                symbol=request.symbol,
                timeframe=request.timeframe,
                count=current_chunk_count,
                to=chunk_to,
                end=chunk_end,
                status=ChunkStatus.PENDING.value,
                expected_candles=current_chunk_count,
                previous_chunk_id=chunks[chunk_index - 1].chunk_id if chunk_index > 0 else None,
                next_chunk_id=None  # 다음 청크에서 설정
            )

            # 이전 청크의 next_chunk_id 설정
            if chunks:
                chunks[-1].next_chunk_id = chunk_id

            chunks.append(chunk_info)

        plan = ChunkPlan(
            original_request=request,
            total_chunks=total_chunks,
            total_expected_candles=total_count,
            chunks=chunks,
            plan_created_at=datetime.now()
        )

        logger.info(f"✅ 청크 계획 완성: {total_chunks}개 청크")
        return plan

    def _calculate_chunk_time_range(
        self,
        request: RequestInfo,
        chunk_index: int,
        chunk_count: int
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        개별 청크의 시간 범위를 계산

        Args:
            request: 원본 요청 정보
            chunk_index: 청크 인덱스 (0부터 시작)
            chunk_count: 현재 청크의 캔들 개수

        Returns:
            tuple: (chunk_to, chunk_end) 시간 범위
        """
        # 요청 타입별로 다른 계산 로직
        if request.request_type == RequestType.COUNT_ONLY.value:
            # count만 지정: to=None, end=None (최신 데이터부터)
            return None, None

        elif request.request_type == RequestType.COUNT_WITH_TO.value:
            # count + to 지정: to 시점부터 과거로 청크 분할
            if request.to is None:
                return None, None

            # 청크별 시작 시점 계산 (청크 인덱스 * 청크사이즈개씩 과거로)
            chunk_offset = chunk_index * CHUNK_SIZE
            chunk_to = TimeUtils.get_aligned_time_by_ticks(
                base_time=request.to,
                timeframe=request.timeframe,
                tick_count=-chunk_offset
            )
            return chunk_to, None

        elif request.request_type == RequestType.TO_WITH_END.value:
            # to + end 지정: 시간 범위를 청크로 분할
            if request.to is None or request.end is None:
                return None, None

            # 전체 시간 범위를 균등 분할
            chunk_offset = chunk_index * CHUNK_SIZE
            chunk_to = TimeUtils.get_aligned_time_by_ticks(
                base_time=request.to,
                timeframe=request.timeframe,
                tick_count=-chunk_offset
            )

            # chunk_end는 다음 청크의 시작점 (마지막 청크는 원본 end 사용)
            # 단순화: 각 청크는 독립적으로 처리
            chunk_end = TimeUtils.get_aligned_time_by_ticks(
                base_time=request.to,
                timeframe=request.timeframe,
                tick_count=-(chunk_offset + chunk_count)
            )
            return chunk_to, chunk_end

        elif request.request_type == RequestType.END_ONLY.value:
            # end만 지정: 현재 시점부터 end까지 청크 분할
            if request.end is None:
                return None, None

            current_time = datetime.now()

            # 현재 시점부터 청크별로 시간 범위 계산
            chunk_offset = chunk_index * CHUNK_SIZE
            chunk_to = TimeUtils.get_aligned_time_by_ticks(
                base_time=current_time,
                timeframe=request.timeframe,
                tick_count=chunk_offset
            )

            # 마지막 청크는 end 시점으로, 그 외는 다음 청크 시작점으로
            if chunk_index * CHUNK_SIZE + chunk_count >= TimeUtils.calculate_expected_count(
                start_time=current_time,
                end_time=request.end,
                timeframe=request.timeframe
            ):
                chunk_end = request.end
            else:
                chunk_end = TimeUtils.get_aligned_time_by_ticks(
                    base_time=current_time,
                    timeframe=request.timeframe,
                    tick_count=chunk_offset + chunk_count
                )

            return chunk_to, chunk_end

        else:
            # 알 수 없는 타입: 기본값 반환
            return None, None
