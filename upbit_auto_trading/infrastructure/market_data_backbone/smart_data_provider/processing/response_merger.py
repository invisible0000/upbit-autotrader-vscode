"""
분할된 응답 자동 병합 시스템

분할된 요청들의 응답을 올바른 순서로 병합하고
완전한 데이터셋을 구성합니다.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .request_splitter import SplitRequest, SplitStrategy


logger = create_component_logger("ResponseMerger")


@dataclass
class SplitResponse:
    """분할된 응답 정보"""
    split_request: SplitRequest
    data: List[Dict[str, Any]]
    success: bool
    error: Optional[str] = None
    response_time_ms: float = 0.0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class MergedResponse:
    """병합된 최종 응답"""
    original_request_id: str
    data: List[Dict[str, Any]]
    success: bool
    total_splits: int
    successful_splits: int
    failed_splits: int
    total_response_time_ms: float
    merge_strategy: SplitStrategy
    error_details: List[str]
    metadata: Dict[str, Any]


class ResponseMerger:
    """분할된 응답 자동 병합기"""

    def __init__(self):
        self.logger = logger
        self._pending_responses: Dict[str, List[SplitResponse]] = {}

    def add_split_response(self, response: SplitResponse) -> Optional[MergedResponse]:
        """분할된 응답 추가 및 병합 시도"""

        original_id = response.split_request.original_id

        # 대기 중인 응답 목록에 추가
        if original_id not in self._pending_responses:
            self._pending_responses[original_id] = []

        self._pending_responses[original_id].append(response)

        # 모든 분할 응답이 도착했는지 확인
        expected_splits = response.split_request.total_splits
        received_splits = len(self._pending_responses[original_id])

        self.logger.debug(
            f"Split response received: {received_splits}/{expected_splits}",
            extra={
                "original_id": original_id,
                "split_index": response.split_request.split_index
            }
        )

        if received_splits >= expected_splits:
            # 모든 응답이 도착한 경우 병합 수행
            merged = self._merge_responses(original_id)
            # 완료된 응답은 메모리에서 제거
            del self._pending_responses[original_id]
            return merged

        return None

    def _merge_responses(self, original_id: str) -> MergedResponse:
        """응답들을 병합하여 완전한 데이터셋 구성"""

        responses = self._pending_responses[original_id]

        if not responses:
            return MergedResponse(
                original_request_id=original_id,
                data=[],
                success=False,
                total_splits=0,
                successful_splits=0,
                failed_splits=0,
                total_response_time_ms=0.0,
                merge_strategy=SplitStrategy.COUNT_BASED,
                error_details=["No responses to merge"],
                metadata={}
            )

        # 응답 정렬 (split_index 기준)
        responses.sort(key=lambda r: r.split_request.split_index)

        # 전략에 따른 병합 수행
        strategy = responses[0].split_request.strategy

        if strategy == SplitStrategy.TIME_BASED:
            merged_data = self._merge_time_based_responses(responses)
        elif strategy == SplitStrategy.COUNT_BASED:
            merged_data = self._merge_count_based_responses(responses)
        elif strategy == SplitStrategy.SYMBOL_BASED:
            merged_data = self._merge_symbol_based_responses(responses)
        else:
            merged_data = self._merge_simple_responses(responses)

        # 통계 계산
        successful_responses = [r for r in responses if r.success]
        failed_responses = [r for r in responses if not r.success]

        total_response_time = sum(r.response_time_ms for r in responses)

        error_details = [r.error for r in failed_responses if r.error]

        # 메타데이터 구성
        metadata = {
            "merge_timestamp": datetime.now().isoformat(),
            "split_count": len(responses),
            "data_count": len(merged_data),
            "average_response_time_ms": total_response_time / len(responses) if responses else 0,
            "strategy_used": strategy.value
        }

        self.logger.info(
            f"Merged {len(responses)} split responses into {len(merged_data)} records",
            extra={
                "original_id": original_id,
                "strategy": strategy.value,
                "successful_splits": len(successful_responses),
                "failed_splits": len(failed_responses)
            }
        )

        return MergedResponse(
            original_request_id=original_id,
            data=merged_data,
            success=len(successful_responses) > 0,  # 하나라도 성공하면 성공으로 간주
            total_splits=len(responses),
            successful_splits=len(successful_responses),
            failed_splits=len(failed_responses),
            total_response_time_ms=total_response_time,
            merge_strategy=strategy,
            error_details=error_details,
            metadata=metadata
        )

    def _merge_time_based_responses(self, responses: List[SplitResponse]) -> List[Dict[str, Any]]:
        """시간 기반 분할 응답 병합 (캔들 데이터)"""

        merged_data = []

        for response in responses:
            if response.success and response.data:
                # 캔들 데이터는 시간순으로 정렬되어 있어야 함
                sorted_candles = sorted(
                    response.data,
                    key=lambda x: datetime.fromisoformat(x.get('candle_date_time_kst', '1970-01-01T00:00:00'))
                )
                merged_data.extend(sorted_candles)

        # 전체 데이터를 시간순으로 재정렬
        if merged_data:
            merged_data.sort(
                key=lambda x: datetime.fromisoformat(x.get('candle_date_time_kst', '1970-01-01T00:00:00'))
            )

        # 중복 제거 (같은 시간의 캔들이 있을 수 있음)
        if merged_data:
            unique_data = []
            seen_times = set()

            for candle in merged_data:
                candle_time = candle.get('candle_date_time_kst')
                if candle_time not in seen_times:
                    unique_data.append(candle)
                    seen_times.add(candle_time)

            merged_data = unique_data

        self.logger.debug(
            f"Time-based merge completed: {len(merged_data)} unique candles",
            extra={"responses_count": len(responses)}
        )

        return merged_data

    def _merge_count_based_responses(self, responses: List[SplitResponse]) -> List[Dict[str, Any]]:
        """개수 기반 분할 응답 병합"""

        merged_data = []

        # 순서대로 데이터 연결
        for response in responses:
            if response.success and response.data:
                merged_data.extend(response.data)

        self.logger.debug(
            f"Count-based merge completed: {len(merged_data)} total records",
            extra={"responses_count": len(responses)}
        )

        return merged_data

    def _merge_symbol_based_responses(self, responses: List[SplitResponse]) -> List[Dict[str, Any]]:
        """심볼 기반 분할 응답 병합 (티커, 호가 데이터)"""

        merged_data = []

        # 모든 심볼의 데이터를 합침
        for response in responses:
            if response.success and response.data:
                merged_data.extend(response.data)

        # 티커/호가 데이터는 심볼별로 정렬
        if merged_data and merged_data[0].get('market'):
            merged_data.sort(key=lambda x: x.get('market', ''))

        self.logger.debug(
            f"Symbol-based merge completed: {len(merged_data)} total records",
            extra={"responses_count": len(responses)}
        )

        return merged_data

    def _merge_simple_responses(self, responses: List[SplitResponse]) -> List[Dict[str, Any]]:
        """단순 응답 병합 (기본 전략)"""

        merged_data = []

        for response in responses:
            if response.success and response.data:
                merged_data.extend(response.data)

        return merged_data

    def get_pending_count(self) -> int:
        """대기 중인 응답 그룹 수"""
        return len(self._pending_responses)

    def get_pending_details(self) -> Dict[str, Dict[str, Any]]:
        """대기 중인 응답 상세 정보"""

        details = {}

        for original_id, responses in self._pending_responses.items():
            if responses:
                expected_splits = responses[0].split_request.total_splits
                received_splits = len(responses)

                details[original_id] = {
                    "expected_splits": expected_splits,
                    "received_splits": received_splits,
                    "completion_percentage": (received_splits / expected_splits) * 100,
                    "strategy": responses[0].split_request.strategy.value,
                    "oldest_response_time": min(r.timestamp for r in responses),
                    "newest_response_time": max(r.timestamp for r in responses)
                }

        return details

    def cleanup_stale_responses(self, max_age_minutes: int = 30) -> int:
        """오래된 미완성 응답 정리"""

        cutoff_time = datetime.now()
        cutoff_time = cutoff_time.replace(minute=cutoff_time.minute - max_age_minutes)

        stale_ids = []

        for original_id, responses in self._pending_responses.items():
            if responses:
                oldest_response = min(responses, key=lambda r: r.timestamp)
                if oldest_response.timestamp < cutoff_time:
                    stale_ids.append(original_id)

        for stale_id in stale_ids:
            del self._pending_responses[stale_id]
            self.logger.warning(
                f"Cleaned up stale response group: {stale_id}",
                extra={"cleanup_age_minutes": max_age_minutes}
            )

        return len(stale_ids)
