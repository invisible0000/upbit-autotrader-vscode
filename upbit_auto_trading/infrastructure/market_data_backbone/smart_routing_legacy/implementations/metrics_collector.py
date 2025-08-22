"""
성능 메트릭 수집 서비스

스마트 라우팅 시스템의 성능 메트릭을 수집하고 분석하는 서비스입니다.
"""

import time
from typing import Dict, List, Any
from collections import defaultdict, deque
import statistics

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("MetricsCollector")


class MetricsCollector:
    """성능 메트릭 수집 서비스

    스마트 라우팅 시스템의 전체적인 성능 메트릭을 수집하고 분석합니다.
    """

    def __init__(self, history_size: int = 1000):
        """메트릭 수집기 초기화

        Args:
            history_size: 메트릭 히스토리 최대 크기
        """
        logger.info("MetricsCollector 초기화 시작")

        self.history_size = history_size
        self.start_time = time.time()

        # Tier별 성능 메트릭
        self.tier_metrics = {
            'HOT_CACHE': self._create_tier_metrics(),
            'LIVE_SUBSCRIPTION': self._create_tier_metrics(),
            'BATCH_SNAPSHOT': self._create_tier_metrics(),
            'WARM_CACHE_REST': self._create_tier_metrics(),
            'COLD_REST': self._create_tier_metrics()
        }

        # 전체 시스템 메트릭
        self.system_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'websocket_connections': 0,
            'rest_api_calls': 0,
            'rate_limit_hits': 0,
            'fallback_activations': 0
        }

        # 응답 시간 히스토리 (sliding window)
        self.response_time_history = deque(maxlen=self.history_size)
        self.success_rate_history = deque(maxlen=self.history_size)

        # 실시간 통계
        self.current_session = {
            'session_start': self.start_time,
            'requests_this_minute': 0,
            'last_minute_reset': self.start_time,
            'peak_requests_per_minute': 0,
            'avg_requests_per_minute': 0.0
        }

        logger.info("MetricsCollector 초기화 완료")

    def _create_tier_metrics(self) -> Dict[str, Any]:
        """Tier별 메트릭 구조 생성

        Returns:
            초기화된 Tier 메트릭
        """
        return {
            'request_count': 0,
            'success_count': 0,
            'failure_count': 0,
            'total_response_time_ms': 0.0,
            'min_response_time_ms': float('inf'),
            'max_response_time_ms': 0.0,
            'avg_response_time_ms': 0.0,
            'last_used': 0.0,
            'usage_frequency': 0.0,
            'error_types': defaultdict(int),
            'recent_response_times': deque(maxlen=100)
        }

    def record_request(
        self,
        tier: str,
        response_time_ms: float,
        success: bool,
        symbols_count: int = 1,
        error_type: str = None
    ) -> None:
        """요청 메트릭 기록

        Args:
            tier: 사용된 Tier
            response_time_ms: 응답 시간 (밀리초)
            success: 성공 여부
            symbols_count: 요청한 심볼 수
            error_type: 에러 타입 (실패 시)
        """
        current_time = time.time()

        # 전체 시스템 메트릭 업데이트
        self.system_metrics['total_requests'] += 1
        if success:
            self.system_metrics['successful_requests'] += 1
        else:
            self.system_metrics['failed_requests'] += 1

        # Tier별 메트릭 업데이트
        if tier in self.tier_metrics:
            tier_data = self.tier_metrics[tier]

            tier_data['request_count'] += 1
            tier_data['last_used'] = current_time

            if success:
                tier_data['success_count'] += 1

                # 응답 시간 통계 업데이트
                tier_data['total_response_time_ms'] += response_time_ms
                tier_data['min_response_time_ms'] = min(
                    tier_data['min_response_time_ms'], response_time_ms
                )
                tier_data['max_response_time_ms'] = max(
                    tier_data['max_response_time_ms'], response_time_ms
                )
                tier_data['avg_response_time_ms'] = (
                    tier_data['total_response_time_ms'] / tier_data['success_count']
                )

                # 최근 응답 시간 기록
                tier_data['recent_response_times'].append(response_time_ms)

            else:
                tier_data['failure_count'] += 1
                if error_type:
                    tier_data['error_types'][error_type] += 1

        # 히스토리 업데이트
        self.response_time_history.append({
            'timestamp': current_time,
            'tier': tier,
            'response_time_ms': response_time_ms,
            'success': success,
            'symbols_count': symbols_count
        })

        # 성공률 계산 및 기록
        if len(self.response_time_history) >= 10:  # 최소 10개 샘플
            recent_requests = list(self.response_time_history)[-50:]  # 최근 50개
            success_count = sum(1 for r in recent_requests if r['success'])
            current_success_rate = success_count / len(recent_requests)
            self.success_rate_history.append({
                'timestamp': current_time,
                'success_rate': current_success_rate
            })

        # 분당 요청 수 추적
        self._update_requests_per_minute()

        logger.debug(f"메트릭 기록: {tier} - {response_time_ms:.1f}ms, "
                    f"성공: {success}, 심볼: {symbols_count}")

    def record_cache_hit(self, tier: str) -> None:
        """캐시 히트 기록

        Args:
            tier: 캐시가 사용된 Tier
        """
        self.system_metrics['cache_hits'] += 1
        logger.debug(f"캐시 히트 기록: {tier}")

    def record_cache_miss(self, tier: str) -> None:
        """캐시 미스 기록

        Args:
            tier: 캐시 미스가 발생한 Tier
        """
        self.system_metrics['cache_misses'] += 1
        logger.debug(f"캐시 미스 기록: {tier}")

    def record_websocket_connection(self) -> None:
        """WebSocket 연결 기록"""
        self.system_metrics['websocket_connections'] += 1
        logger.debug("WebSocket 연결 기록")

    def record_rest_api_call(self) -> None:
        """REST API 호출 기록"""
        self.system_metrics['rest_api_calls'] += 1
        logger.debug("REST API 호출 기록")

    def record_rate_limit_hit(self) -> None:
        """Rate Limit 도달 기록"""
        self.system_metrics['rate_limit_hits'] += 1
        logger.debug("Rate Limit 도달 기록")

    def record_fallback_activation(self, from_tier: str, to_tier: str) -> None:
        """Fallback 활성화 기록

        Args:
            from_tier: 원래 Tier
            to_tier: Fallback Tier
        """
        self.system_metrics['fallback_activations'] += 1
        logger.info(f"Fallback 활성화 기록: {from_tier} → {to_tier}")

    def _update_requests_per_minute(self) -> None:
        """분당 요청 수 업데이트"""
        current_time = time.time()

        # 1분이 지났는지 확인
        if current_time - self.current_session['last_minute_reset'] >= 60.0:
            # 이전 분의 요청 수 기록
            requests_last_minute = self.current_session['requests_this_minute']

            # 최고 기록 업데이트
            if requests_last_minute > self.current_session['peak_requests_per_minute']:
                self.current_session['peak_requests_per_minute'] = requests_last_minute

            # 평균 계산 (이동 평균)
            session_duration_minutes = (current_time - self.start_time) / 60.0
            total_requests = self.system_metrics['total_requests']
            self.current_session['avg_requests_per_minute'] = (
                total_requests / session_duration_minutes if session_duration_minutes > 0 else 0.0
            )

            # 새 분 시작
            self.current_session['requests_this_minute'] = 1
            self.current_session['last_minute_reset'] = current_time
        else:
            self.current_session['requests_this_minute'] += 1

    def get_tier_performance_summary(self) -> Dict[str, Any]:
        """Tier별 성능 요약 조회

        Returns:
            Tier별 성능 요약
        """
        summary = {}

        for tier, metrics in self.tier_metrics.items():
            if metrics['request_count'] > 0:
                success_rate = metrics['success_count'] / metrics['request_count']

                # 최근 응답 시간 통계
                recent_times = list(metrics['recent_response_times'])
                if recent_times:
                    recent_avg = statistics.mean(recent_times)
                    recent_median = statistics.median(recent_times)
                    recent_p95 = statistics.quantiles(recent_times, n=20)[18] if len(recent_times) >= 20 else max(recent_times)
                else:
                    recent_avg = recent_median = recent_p95 = 0.0

                summary[tier] = {
                    'request_count': metrics['request_count'],
                    'success_rate': success_rate,
                    'avg_response_time_ms': metrics['avg_response_time_ms'],
                    'min_response_time_ms': metrics['min_response_time_ms'] if metrics['min_response_time_ms'] != float('inf') else 0.0,
                    'max_response_time_ms': metrics['max_response_time_ms'],
                    'recent_avg_response_time_ms': recent_avg,
                    'recent_median_response_time_ms': recent_median,
                    'recent_p95_response_time_ms': recent_p95,
                    'usage_frequency': metrics['request_count'] / self.system_metrics['total_requests'],
                    'last_used_ago_seconds': time.time() - metrics['last_used'] if metrics['last_used'] > 0 else None,
                    'error_types': dict(metrics['error_types'])
                }
            else:
                summary[tier] = {
                    'request_count': 0,
                    'success_rate': 0.0,
                    'avg_response_time_ms': 0.0,
                    'usage_frequency': 0.0,
                    'last_used_ago_seconds': None,
                    'error_types': {}
                }

        return summary

    def get_system_overview(self) -> Dict[str, Any]:
        """시스템 전체 개요 조회

        Returns:
            시스템 전체 성능 개요
        """
        current_time = time.time()
        session_duration_seconds = current_time - self.start_time

        # 전체 성공률
        total_requests = self.system_metrics['total_requests']
        overall_success_rate = (
            self.system_metrics['successful_requests'] / total_requests
            if total_requests > 0 else 0.0
        )

        # 캐시 히트율
        total_cache_requests = self.system_metrics['cache_hits'] + self.system_metrics['cache_misses']
        cache_hit_rate = (
            self.system_metrics['cache_hits'] / total_cache_requests
            if total_cache_requests > 0 else 0.0
        )

        # 최근 성능 트렌드
        recent_performance = self._get_recent_performance_trend()

        return {
            'session_info': {
                'start_time': self.start_time,
                'duration_seconds': session_duration_seconds,
                'duration_formatted': self._format_duration(session_duration_seconds)
            },
            'request_stats': {
                'total_requests': total_requests,
                'successful_requests': self.system_metrics['successful_requests'],
                'failed_requests': self.system_metrics['failed_requests'],
                'success_rate': overall_success_rate,
                'requests_per_minute': self.current_session['avg_requests_per_minute'],
                'peak_requests_per_minute': self.current_session['peak_requests_per_minute']
            },
            'cache_stats': {
                'cache_hits': self.system_metrics['cache_hits'],
                'cache_misses': self.system_metrics['cache_misses'],
                'hit_rate': cache_hit_rate
            },
            'infrastructure_stats': {
                'websocket_connections': self.system_metrics['websocket_connections'],
                'rest_api_calls': self.system_metrics['rest_api_calls'],
                'rate_limit_hits': self.system_metrics['rate_limit_hits'],
                'fallback_activations': self.system_metrics['fallback_activations']
            },
            'performance_trend': recent_performance
        }

    def _get_recent_performance_trend(self) -> Dict[str, Any]:
        """최근 성능 트렌드 분석

        Returns:
            최근 성능 트렌드 정보
        """
        if len(self.response_time_history) < 10:
            return {'status': 'insufficient_data'}

        # 최근 50개 요청 분석
        recent_requests = list(self.response_time_history)[-50:]
        recent_response_times = [r['response_time_ms'] for r in recent_requests if r['success']]

        if not recent_response_times:
            return {'status': 'no_successful_requests'}

        # 통계 계산
        avg_response_time = statistics.mean(recent_response_times)
        median_response_time = statistics.median(recent_response_times)

        # 성공률 트렌드
        recent_success_rate = sum(1 for r in recent_requests if r['success']) / len(recent_requests)

        # 트렌드 판단
        if len(self.success_rate_history) >= 2:
            previous_success_rate = self.success_rate_history[-2]['success_rate']
            success_rate_trend = 'improving' if recent_success_rate > previous_success_rate else 'declining'
        else:
            success_rate_trend = 'stable'

        return {
            'status': 'available',
            'recent_avg_response_time_ms': avg_response_time,
            'recent_median_response_time_ms': median_response_time,
            'recent_success_rate': recent_success_rate,
            'success_rate_trend': success_rate_trend,
            'sample_size': len(recent_requests)
        }

    def _format_duration(self, seconds: float) -> str:
        """지속시간을 읽기 쉬운 형식으로 변환

        Args:
            seconds: 초 단위 지속시간

        Returns:
            포맷된 지속시간 문자열
        """
        if seconds < 60:
            return f"{seconds:.1f}초"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}분"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}시간"

    def export_metrics_report(self) -> Dict[str, Any]:
        """상세 메트릭 보고서 생성

        Returns:
            상세한 메트릭 보고서
        """
        return {
            'report_timestamp': time.time(),
            'report_generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'system_overview': self.get_system_overview(),
            'tier_performance': self.get_tier_performance_summary(),
            'raw_metrics': {
                'system_metrics': self.system_metrics.copy(),
                'tier_metrics': {tier: metrics.copy() for tier, metrics in self.tier_metrics.items()}
            },
            'configuration': {
                'history_size': self.history_size,
                'current_history_length': len(self.response_time_history)
            }
        }

    def reset_metrics(self) -> None:
        """모든 메트릭 초기화"""
        logger.info("메트릭 초기화 시작")

        # Tier 메트릭 초기화
        for tier in self.tier_metrics:
            self.tier_metrics[tier] = self._create_tier_metrics()

        # 시스템 메트릭 초기화
        self.system_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'websocket_connections': 0,
            'rest_api_calls': 0,
            'rate_limit_hits': 0,
            'fallback_activations': 0
        }

        # 히스토리 초기화
        self.response_time_history.clear()
        self.success_rate_history.clear()

        # 세션 정보 재설정
        self.start_time = time.time()
        self.current_session = {
            'session_start': self.start_time,
            'requests_this_minute': 0,
            'last_minute_reset': self.start_time,
            'peak_requests_per_minute': 0,
            'avg_requests_per_minute': 0.0
        }

        logger.info("메트릭 초기화 완료")
