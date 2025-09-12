"""
📋 CandleDataProvider v4.1 - 간략화된 normalize_request 구현
모든 요청을 to_with_end 형태로 정규화하는 단순화된 버전

Created: 2025-09-11
Purpose: 과도하게 세분화된 메서드들을 단일 normalize_request로 통합
Features: 4가지 파라미터 조합을 단순한 if-else로 처리
"""

from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils
from upbit_auto_trading.infrastructure.market_data.candle.candle_models import (
    RequestInfo, ChunkInfo
)

logger = create_component_logger("CandleDataProvider")


class ChunkStatus(Enum):
    """청크 처리 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CandleDataProvider:
    """
    캔들 데이터 제공자 v4.1 - 간략화된 버전

    핵심 원리:
    - 모든 요청을 to + end 형태로 정규화 (request_type 구분 불필요)
    - 과도한 메서드 분리 제거 (6개 → 2개 메서드)
    - 단순한 if-else 구조로 4가지 조합 처리
    - 업비트 데이터 순서 준수: [to, ..., end] (최신 → 과거)
    """

    def __init__(self):
        """CandleDataProvider 초기화"""
        logger.info("CandleDataProvider v4.1 (간략화 버전) 초기화 시작...")
        logger.info("✅ CandleDataProvider v4.1 초기화 완료")

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        to: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[ChunkInfo]:
        """
        캔들 데이터 요청을 처리하여 청크 계획 반환

        사용자 편의성을 위해 개별 파라미터로 받아서 내부에서 RequestInfo 생성
        실제 데이터 수집은 별도 컴포넌트에서 ChunkPlan을 사용하여 수행

        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m', '1h', '1d')
            count: 조회할 캔들 개수 (1~7,000,000) - count와 end는 동시 사용 불가
            to: 시작점 - 최신 캔들 시간 (업비트 응답의 첫 번째 캔들)
            end: 종료점 - 가장 과거 캔들 시간 (업비트 응답의 마지막 캔들)

        Returns:
            List[ChunkInfo]: 청크 정보 리스트

        4가지 파라미터 조합:
            - count만: 현재시간에서 count개 과거로
            - count + to: to(시작)에서 count개 과거로
            - to + end: to(시작)에서 end(종료)까지
            - end만: 현재시간에서 end(종료)까지

        Example:
            >>> chunks = provider.get_candles(symbol="KRW-BTC", timeframe="1m", count=100)
            >>> print(f"총 {len(chunks)}개 청크, {sum(chunk.count for chunk in chunks)}개 캔들")
        """
        logger.info(f"캔들 데이터 요청 처리: {symbol} {timeframe}, count={count}, to={to}, end={end}")

        # 동적 비즈니스 검증 (실행 시점의 현재 시간 기준)
        current_time = datetime.now(timezone.utc)
        if to is not None and to > current_time:
            raise ValueError(f"to 시점이 미래입니다: {to}")
        if end is not None and end > current_time:
            raise ValueError(f"end 시점이 미래입니다: {end}")

        # 📊 캔들 개수 제한 검증 (최대 7,000,000개)
        MAX_CANDLES = 7_000_000  # 35,000 요청, 20,000개 당 10초

        # count가 직접 제공된 경우
        if count is not None and count > MAX_CANDLES:
            raise ValueError(f"요청 캔들 개수({count:,})가 최대 허용량({MAX_CANDLES:,})을 초과합니다")

        # 기간(to, end)이 제공된 경우 사전 계산으로 제한 확인
        if count is None and to is not None and end is not None:
            # 시간 정렬 후 예상 캔들 개수 계산
            normalized_to = TimeUtils.align_to_candle_boundary(to, timeframe)
            normalized_end = TimeUtils.align_to_candle_boundary(end, timeframe)

            if normalized_to <= normalized_end:
                raise ValueError(f"to는 end보다 이전 시점이어야 합니다: to={normalized_to}, end={normalized_end}")

            estimated_count = TimeUtils.calculate_expected_count(
                start_time=normalized_to,
                end_time=normalized_end,
                timeframe=timeframe
            )

            if estimated_count > MAX_CANDLES:
                raise ValueError(
                    f"요청 기간의 예상 캔들 개수({estimated_count:,})가 최대 허용량({MAX_CANDLES:,})을 초과합니다. "
                    f"기간을 단축하거나 더 큰 타임프레임을 사용하세요."
                )

            logger.info(f"📊 기간 기반 요청: 예상 캔들 개수 {estimated_count:,}개 (제한: {MAX_CANDLES:,}개)")

        # end만 제공된 경우 사전 계산
        elif count is None and end is not None:
            # 현재 시간에서 end까지의 예상 캔들 개수 계산
            normalized_current = TimeUtils.align_to_candle_boundary(current_time, timeframe)
            normalized_end = TimeUtils.align_to_candle_boundary(end, timeframe)

            if normalized_current <= normalized_end:
                raise ValueError(f"현재 시간은 end보다 이전 시점이어야 합니다: 현재={normalized_current}, end={normalized_end}")

            estimated_count = TimeUtils.calculate_expected_count(
                start_time=normalized_current,
                end_time=normalized_end,
                timeframe=timeframe
            )

            if estimated_count > MAX_CANDLES:
                raise ValueError(
                    f"현재 시간부터 요청 종료점까지의 예상 캔들 개수({estimated_count:,})가 최대 허용량({MAX_CANDLES:,})을 초과합니다. "
                    f"종료점을 최근으로 조정하거나 더 큰 타임프레임을 사용하세요."
                )

            logger.info(f"📊 종료점 기반 요청: 예상 캔들 개수 {estimated_count:,}개 (제한: {MAX_CANDLES:,}개)")

        # 사용자 편의성을 위해 개별 파라미터를 RequestInfo로 변환
        request = RequestInfo(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            to=to,
            end=end
        )

        # 요청을 정규화하여 청크 리스트 생성
        chunks = self.normalize_request(request)

        logger.info(f"✅ 캔들 데이터 요청 처리 완료: {len(chunks)}개 청크")
        return chunks

    def normalize_request(
        self,
        request: RequestInfo
    ) -> List[ChunkInfo]:
        """
        모든 요청을 to_with_end 형태로 정규화

        핵심 원리:
        1. to가 없으면 현재 시간으로 설정
        2. end가 없으면 count를 이용해 계산
        3. 모든 결과를 TimeUtils로 정렬
        4. 단일 create_chunks로 처리

        Args:
            request: 요청 정보 (RequestInfo 객체)
                - symbol: 심볼 (예: 'KRW-BTC')
                - timeframe: 타임프레임 (예: '1m', '5m', '1h', '1d')
                - count: 조회할 캔들 개수 (1~무제한)
                - to: 시작점 - 최신 캔들 시간 (업비트 응답의 첫 번째 캔들)
                - end: 종료점 - 가장 과거 캔들 시간 (업비트 응답의 마지막 캔들)

        Returns:
            List[ChunkInfo]: 정규화 완료된 청크 리스트

        4가지 파라미터 조합:
        - count만: 현재시간에서 count개 과거로
        - count + to: to(시작)에서 count개 과거로
        - to + end: to(시작)에서 end(종료)까지
        - end만: 현재시간에서 end(종료)까지

        업비트 데이터 순서: [to, 4, 3, 2, end] (최신 → 과거)
        """
        logger.info(f"요청 정규화: {request.symbol} {request.timeframe}, count={request.count}, to={request.to}, end={request.end}")

        # 📝 RequestInfo는 이미 생성 시 모든 기본 검증 완료:
        #    - symbol, timeframe 필수 체크
        #    - count와 end 동시 사용 금지
        #    - count 또는 to+end 조합 필수
        #    - count >= 1 검증
        #    - 시간 순서 검증 (to > end)

        # 1. to 시간 확정 (없으면 현재 시간)
        if request.to is None:
            to_time = datetime.now(timezone.utc)
            logger.debug("to가 없어서 현재 시간으로 설정")
        else:
            to_time = request.to
            # 📝 미래 시간 검증은 get_candles에서 이미 완료

        # 2. TimeUtils로 시간 정렬 (to 시점 정렬)
        normalized_start = TimeUtils.align_to_candle_boundary(to_time, request.timeframe)
        logger.debug(f"정렬된 to 시간: {normalized_start}")

        # 3. end 시간 확정 및 총 캔들 개수 계산
        if request.end is not None:
            # end가 있는 경우: end 사용 + count 계산
            # 📝 미래 시간 검증은 get_candles에서 이미 완료
            normalized_end = TimeUtils.align_to_candle_boundary(request.end, request.timeframe)

            # 정규화된 시간으로 순서 재검증 (캔들 경계 정렬 후)
            if normalized_start <= normalized_end:
                raise ValueError(f"정규화된 to는 end보다 이전 시점이어야 합니다: to={normalized_start}, end={normalized_end}")

            total_count = TimeUtils.calculate_expected_count(
                start_time=normalized_start,  # 최신 시점이 start
                end_time=normalized_end,     # 과거 시점이 end
                timeframe=request.timeframe
            )

            # 🚧 개발 중 검증: calculate_expected_count와 request.count 일치성 확인 (차후 제거 예정)
            if request.count is not None and total_count != request.count:
                raise ValueError(
                    f"계산된 캔들 개수({total_count})와 요청 캔들 개수({request.count})가 일치하지 않습니다. "
                    f"start_time={normalized_start}, end_time={normalized_end}, timeframe={request.timeframe}"
                )

            logger.debug(f"end 기반 계산: end={normalized_end}, count={total_count}")
        else:
            # end가 없는 경우: count 사용 + end 계산
            # RequestInfo 검증에서 이미 count는 None이 아님을 보장:
            # "count 또는 to+end 조합 중 하나는 반드시 제공되어야 합니다"
            total_count: int = request.count  # type: ignore[assignment]  # RequestInfo.__post_init__ 검증으로 None 불가능
            normalized_end = TimeUtils.get_aligned_time_by_ticks(
                base_time=normalized_start,
                timeframe=request.timeframe,
                tick_count=-total_count + 1
            )
            logger.debug(f"count 기반 계산: count={total_count}, end={normalized_end}")

        # 4. 청크 생성 (단일 메서드) - 정규화된 값 사용
        chunks = self.create_chunks(
            start_time=normalized_start,
            end_time=normalized_end,
            total_count=total_count,
            timeframe=request.timeframe,
            symbol=request.symbol
        )

        # 5. 청크 리스트 반환 (ChunkPlan 제거로 단순화)
        logger.info(f"✅ 정규화 완료: {len(chunks)}개 청크, 총 {total_count}개 캔들")
        return chunks

    def create_chunks(
        self,
        start_time: datetime,
        end_time: datetime,
        total_count: int,
        timeframe: str,
        symbol: str
    ) -> List[ChunkInfo]:
        """
        정규화된 to_with_end 형태를 200개 단위로 분할

        Args:
            start_time: 정렬된 시작 시간 (최신)
            end_time: 정렬된 종료 시간 (과거)
            total_count: 전체 캔들 개수
            timeframe: 타임프레임
            symbol: 심볼

        Returns:
            List[ChunkInfo]: 청크 정보 리스트
        """
        logger.info(f"청크 생성: {symbol} {timeframe}, {total_count}개 캔들")

        # 청크 크기 (임시로 10으로 축소 - 검증용)
        CHUNK_SIZE = 10
        chunks = []
        remaining_count = total_count
        current_start = start_time
        chunk_index = 0

        while remaining_count > 0:
            # 현재 청크 크기 결정 (최대 200개)
            chunk_count = min(remaining_count, CHUNK_SIZE)

            # 청크 종료 시간 계산 (과거 방향)
            chunk_end = TimeUtils.get_aligned_time_by_ticks(
                base_time=current_start,
                timeframe=timeframe,
                tick_count=-chunk_count + 1
            )

            # 마지막 청크인 경우 원본 end_time 사용
            if remaining_count <= CHUNK_SIZE:
                chunk_end = end_time

            # ChunkInfo 생성 (5자리로 확장 시 99999개 청크까지 지원)
            chunk_id = f"{symbol}_{timeframe}_{chunk_index:05d}"
            chunk_info = ChunkInfo(
                chunk_id=chunk_id,
                chunk_index=chunk_index,
                symbol=symbol,
                timeframe=timeframe,
                count=chunk_count,
                to=current_start,
                end=chunk_end
            )
            chunks.append(chunk_info)

            logger.debug(f"청크 {chunk_index}: {current_start} → {chunk_end} ({chunk_count}개)")

            # 다음 청크 준비 (연속성 보장)
            if remaining_count > CHUNK_SIZE:
                timeframe_delta = TimeUtils.get_timeframe_delta(timeframe)
                current_start = chunk_end - timeframe_delta

            remaining_count -= chunk_count
            chunk_index += 1

        logger.info(f"✅ 청크 분할 완료: {len(chunks)}개 청크")
        return chunks
