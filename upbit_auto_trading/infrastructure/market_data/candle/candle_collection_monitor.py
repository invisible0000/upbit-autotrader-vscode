"""
CandleCollectionMonitor - 캔들 수집 모니터링 전용 클래스

Created: 2025-09-22
Purpose: CandleDataProvider에서 모니터링 기능을 분리하여 단일 책임 원칙 준수
Responsibility: CollectionState 기반 모니터링, 성능 지표, 진행률 추적

분리 이유:
- CandleDataProvider의 단일 책임 원칙 준수 (캔들 수집에만 집중)
- 모니터링 로직과 비즈니스 로직 분리
- 코드 가독성 및 유지보수성 향상
- 필요시에만 모니터링 기능 사용 가능

사용법:
    monitor = CandleCollectionMonitor(collection_state)
    performance = monitor.get_performance_metrics()
    progress = monitor.get_detailed_progress()
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, Generator
import time

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.candle.candle_models import CollectionState

logger = create_component_logger("CandleCollectionMonitor")


class CandleCollectionMonitor:
    """
    캔들 수집 모니터링 전용 클래스

    CollectionState를 기반으로 다양한 모니터링 정보를 제공합니다.
    CandleDataProvider에서 분리하여 단일 책임 원칙을 준수합니다.
    """

    def __init__(self, collection_state: CollectionState):
        """
        모니터 초기화

        Args:
            collection_state: 모니터링할 수집 상태
        """
        self.state = collection_state
        logger.debug(f"CandleCollectionMonitor 초기화: {collection_state.request_id}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 지표 및 효율성 정보"""
        # 처리 시간 계산
        elapsed_seconds = (datetime.now(timezone.utc) - self.state.start_time).total_seconds()

        # 처리량 계산
        chunks_per_second = len(self.state.completed_chunks) / elapsed_seconds if elapsed_seconds > 0 else 0
        candles_per_second = self.state.total_collected / elapsed_seconds if elapsed_seconds > 0 else 0

        # 겹침 분석 효율성 계산
        overlap_chunks = sum(1 for chunk in self.state.completed_chunks if chunk.has_overlap_info())
        overlap_hit_rate = overlap_chunks / len(self.state.completed_chunks) if self.state.completed_chunks else 0

        # API 절약률 추정 (겹침이 있는 청크들의 비율)
        complete_overlap_chunks = sum(1 for chunk in self.state.completed_chunks
                                    if chunk.overlap_status and chunk.overlap_status.value == 'complete_overlap')
        api_savings = complete_overlap_chunks / len(self.state.completed_chunks) if self.state.completed_chunks else 0

        return {
            'throughput': {
                'chunks_per_second': round(chunks_per_second, 3),
                'candles_per_second': round(candles_per_second, 1),
                'elapsed_seconds': round(elapsed_seconds, 1)
            },
            'efficiency': {
                'overlap_hit_rate': round(overlap_hit_rate, 3),
                'api_savings': round(api_savings, 3),
                'complete_overlap_count': complete_overlap_chunks
            },
            'timing': {
                'avg_chunk_duration': round(self.state.avg_chunk_duration, 2),
                'estimated_remaining': round(self.state.estimated_remaining_seconds, 1),
                'total_estimated': round(elapsed_seconds + self.state.estimated_remaining_seconds, 1)
            }
        }

    def get_detailed_progress(self) -> Dict[str, Any]:
        """상세 진행률 및 건강 상태 정보"""
        current_time = datetime.now(timezone.utc)

        # 시간 기반 진행률 계산 (CollectionState에 target_end가 없어서 수정 필요)
        time_progress = None
        # TODO: target_end 정보를 어떻게 가져올지 결정 필요

        # 청크 단계 분석
        phase = "initializing"
        if self.state.completed_chunks:
            if self.state.is_completed:
                phase = "completed"
            elif self.state.current_chunk:
                phase = "processing"
            else:
                phase = "collecting"

        # 건강 상태 체크
        errors = 1 if self.state.error_message else 0
        warnings = 0

        # 경고 조건들
        if self.state.avg_chunk_duration > 5.0:  # 5초 이상 걸리는 청크
            warnings += 1

        return {
            'by_time': {
                'start_time': self.state.start_time.strftime('%H:%M:%S'),
                'current_time': current_time.strftime('%H:%M:%S'),
                'elapsed_seconds': (current_time - self.state.start_time).total_seconds(),
                'time_progress': time_progress  # None일 수 있음
            },
            'by_chunks': {
                'phase': phase,
                'current_chunk': len(self.state.completed_chunks) + 1,
                'total_chunks': self.state.estimated_total_chunks,
                'chunk_progress': len(self.state.completed_chunks) / self.state.estimated_total_chunks if self.state.estimated_total_chunks > 0 else 0
            },
            'health': {
                'errors': errors,
                'warnings': warnings,
                'last_error': self.state.error_message,
                'avg_chunk_duration': self.state.avg_chunk_duration
            }
        }

    def get_compact_status(self) -> Dict[str, Any]:
        """압축된 상태 정보 (네트워크 최적화)"""
        # continue_flag를 직접 계산하거나 외부에서 받아야 함
        # TODO: should_continue_collection 로직을 어떻게 처리할지 결정 필요

        # 상태 코드 매핑 (단순화된 버전)
        status_code = "ok"
        if self.state.is_completed:
            status_code = "complete"
        elif self.state.error_message:
            status_code = "error"

        return {
            'id': self.state.request_id[:8],  # 짧은 ID
            'pct': round((self.state.total_collected / self.state.total_requested * 100) if self.state.total_requested > 0 else 0, 1),
            'eta': round(self.state.estimated_remaining_seconds, 0),
            'chunks': len(self.state.completed_chunks),
            'status': status_code,
            'ts': int(datetime.now(timezone.utc).timestamp())  # Unix timestamp
        }

    def get_streaming_updates(self, include_details: bool = False) -> Generator[Dict[str, Any], None, None]:
        """스트리밍 업데이트 제너레이터 (WebSocket용)"""
        last_chunk_count = 0
        last_collected_count = 0

        while True:
            current_chunks = len(self.state.completed_chunks)
            current_collected = self.state.total_collected

            # 변화가 있을 때만 업데이트 전송
            if current_chunks != last_chunk_count or current_collected != last_collected_count:
                update_data = {
                    'type': 'progress',
                    'data': {
                        'pct': round((current_collected / self.state.total_requested * 100) if self.state.total_requested > 0 else 0, 1),
                        'chunks': current_chunks,
                        'collected': current_collected,
                        'eta': round(self.state.estimated_remaining_seconds, 0)
                    },
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

                # 상세 정보 포함 옵션
                if include_details:
                    update_data['data']['details'] = {
                        'current_chunk': self.state.current_chunk.chunk_id if self.state.current_chunk else None,
                        'avg_duration': round(self.state.avg_chunk_duration, 2),
                        'phase': self._get_current_phase()
                    }

                yield update_data

                last_chunk_count = current_chunks
                last_collected_count = current_collected

            # 완료 체크
            if self.state.is_completed:
                yield {
                    'type': 'completed',
                    'data': {'final_count': self.state.total_collected},
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                break

            # 짧은 대기 (실제 사용시 외부에서 제어)
            time.sleep(0.1)

    def _get_current_phase(self) -> str:
        """현재 처리 단계 반환"""
        if self.state.is_completed:
            return "completed"
        elif self.state.current_chunk:
            return "processing"
        elif self.state.completed_chunks:
            return "collecting"
        else:
            return "initializing"

    def get_efficiency_summary(self) -> Dict[str, Any]:
        """효율성 요약 정보"""
        if not self.state.completed_chunks:
            return {'status': 'no_data', 'message': '처리된 청크가 없습니다'}

        total_chunks = len(self.state.completed_chunks)

        # 겹침 분석 활용 통계
        overlap_utilized = sum(1 for chunk in self.state.completed_chunks
                             if chunk.has_overlap_info())

        # API 절약 효과
        complete_overlaps = sum(1 for chunk in self.state.completed_chunks
                              if chunk.overlap_status and
                              chunk.overlap_status.value == 'complete_overlap')

        # 시간 효율성
        elapsed = (datetime.now(timezone.utc) - self.state.start_time).total_seconds()
        efficiency_score = self.state.total_collected / elapsed if elapsed > 0 else 0

        return {
            'overlap_analysis': {
                'utilization_rate': round(overlap_utilized / total_chunks, 3),
                'api_savings_rate': round(complete_overlaps / total_chunks, 3),
                'complete_overlaps': complete_overlaps,
                'total_chunks': total_chunks
            },
            'time_efficiency': {
                'candles_per_second': round(efficiency_score, 2),
                'avg_chunk_duration': round(self.state.avg_chunk_duration, 2),
                'total_elapsed': round(elapsed, 1)
            },
            'overall_score': round((overlap_utilized / total_chunks + efficiency_score / 10) / 2, 3)
        }

    def get_real_time_stats(self) -> Dict[str, Any]:
        """실시간 통계 (대시보드용)"""
        return {
            'progress': {
                'percentage': round((self.state.total_collected / self.state.total_requested * 100) if self.state.total_requested > 0 else 0, 1),
                'collected': self.state.total_collected,
                'requested': self.state.total_requested
            },
            'timing': {
                'eta_seconds': round(self.state.estimated_remaining_seconds, 0),
                'elapsed_seconds': round((datetime.now(timezone.utc) - self.state.start_time).total_seconds(), 1)
            },
            'chunks': {
                'completed': len(self.state.completed_chunks),
                'estimated_total': self.state.estimated_total_chunks,
                'current': self.state.current_chunk.chunk_id if self.state.current_chunk else None
            },
            'status': {
                'is_completed': self.state.is_completed,
                'has_error': bool(self.state.error_message),
                'phase': self._get_current_phase()
            }
        }
