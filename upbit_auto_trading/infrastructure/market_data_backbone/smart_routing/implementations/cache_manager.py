"""
캐시 관리 서비스

스마트 라우팅 시스템의 캐시 전략과 생명주기를 관리하는 서비스입니다.
"""

from typing import Dict, List, Any, Optional
import time

from upbit_auto_trading.infrastructure.logging import create_component_logger
from ..cache import MarketDataCache

logger = create_component_logger("CacheManager")


class CacheManager:
    """캐시 관리 서비스

    HOT_CACHE와 WARM_CACHE Tier를 위한 지능형 캐시 관리를 제공합니다.
    """

    def __init__(self, max_size: int = 10000, cleanup_interval: float = 60.0):
        """캐시 관리자 초기화

        Args:
            max_size: 최대 캐시 엔트리 수
            cleanup_interval: 정리 작업 간격 (초)
        """
        logger.info(f"CacheManager 초기화 - 최대 크기: {max_size}, 정리 간격: {cleanup_interval}초")

        self.cache = MarketDataCache(max_size=max_size, cleanup_interval=cleanup_interval)

        # 데이터 타입별 캐시 정책
        self.cache_policies = {
            'ticker': {
                'ttl_seconds': 30.0,  # 30초 (실시간성 중요)
                'prefetch_threshold': 0.8,  # 80% 만료 시점에 미리 갱신
                'batch_update': True  # 배치 업데이트 허용
            },
            'orderbook': {
                'ttl_seconds': 10.0,  # 10초 (매우 빠른 변화)
                'prefetch_threshold': 0.7,
                'batch_update': False  # 개별 업데이트만
            },
            'trade': {
                'ttl_seconds': 60.0,  # 1분 (체결 내역)
                'prefetch_threshold': 0.9,
                'batch_update': True
            },
            'candle': {
                'ttl_seconds': 300.0,  # 5분 (상대적으로 안정)
                'prefetch_threshold': 0.95,
                'batch_update': True
            }
        }

    async def start(self) -> None:
        """캐시 시스템 시작"""
        await self.cache.start()
        logger.info("CacheManager 시작 완료")

    async def stop(self) -> None:
        """캐시 시스템 정지"""
        await self.cache.stop()
        logger.info("CacheManager 정지 완료")

    def get_ticker_data(self, symbols: List[str]) -> Dict[str, Any]:
        """캐시에서 티커 데이터 조회

        Args:
            symbols: 조회할 심볼 리스트

        Returns:
            캐시된 티커 데이터와 캐시 미스 심볼 정보
        """
        start_time = time.time()
        logger.debug(f"캐시에서 티커 조회: {len(symbols)}개 심볼")

        cached_data = {}
        cache_miss_symbols = []
        cache_hits = 0

        for symbol in symbols:
            cache_key = f"ticker:{symbol}"
            data = self.cache.get(cache_key)

            if data:
                cached_data[symbol] = data
                cache_hits += 1
                logger.debug(f"캐시 히트: {symbol}")
            else:
                cache_miss_symbols.append(symbol)
                logger.debug(f"캐시 미스: {symbol}")

        hit_ratio = cache_hits / len(symbols) if symbols else 0.0
        response_time = (time.time() - start_time) * 1000

        logger.debug(f"캐시 조회 완료: {cache_hits}/{len(symbols)} 히트 ({hit_ratio:.1%}), {response_time:.2f}ms")

        return {
            'cached_data': cached_data,
            'cache_miss_symbols': cache_miss_symbols,
            'hit_ratio': hit_ratio,
            'response_time_ms': response_time,
            'cache_hits': cache_hits,
            'cache_misses': len(cache_miss_symbols)
        }

    def store_ticker_data(self, ticker_data: Dict[str, Any], source: str = 'unknown') -> None:
        """티커 데이터를 캐시에 저장

        Args:
            ticker_data: 저장할 티커 데이터
            source: 데이터 소스 (로깅용)
        """
        policy = self.cache_policies['ticker']
        stored_count = 0

        for symbol, data in ticker_data.items():
            cache_key = f"ticker:{symbol}"

            # 데이터에 캐시 메타데이터 추가
            enhanced_data = {
                **data,
                'cached_at': time.time(),
                'cache_source': source,
                'cache_ttl': policy['ttl_seconds']
            }

            self.cache.set(
                key=cache_key,
                data=enhanced_data,
                ttl=policy['ttl_seconds'],
                data_type='ticker'
            )
            stored_count += 1

        logger.debug(f"캐시 저장 완료: {stored_count}개 심볼 (소스: {source}, TTL: {policy['ttl_seconds']}초)")

    def should_prefetch(self, symbol: str, data_type: str = 'ticker') -> bool:
        """미리 가져오기 여부 판단

        Args:
            symbol: 확인할 심볼
            data_type: 데이터 타입

        Returns:
            미리 가져오기 필요 여부
        """
        cache_key = f"{data_type}:{symbol}"
        entry = self.cache._cache.get(cache_key)

        if not entry:
            return True  # 캐시에 없으면 가져와야 함

        policy = self.cache_policies.get(data_type, self.cache_policies['ticker'])

        # 만료 임계점 계산
        time_elapsed = time.time() - entry.created_at
        time_ratio = time_elapsed / entry.ttl_seconds

        should_prefetch = time_ratio >= policy['prefetch_threshold']

        if should_prefetch:
            logger.debug(f"미리 가져오기 필요: {symbol} ({time_ratio:.1%} 만료됨)")

        return should_prefetch

    def get_cache_statistics(self) -> Dict[str, Any]:
        """캐시 통계 조회

        Returns:
            상세한 캐시 성능 통계
        """
        metrics = self.cache.get_metrics()
        memory_usage = self.cache.get_memory_usage()

        # 데이터 타입별 분석
        type_analysis = {}
        for data_type in self.cache_policies.keys():
            type_keys = self.cache.get_keys(f"{data_type}:")
            type_analysis[data_type] = {
                'count': len(type_keys),
                'policy': self.cache_policies[data_type]
            }

        return {
            'basic_metrics': metrics,
            'memory_usage': memory_usage,
            'type_analysis': type_analysis,
            'performance_grade': self._calculate_performance_grade(metrics),
            'recommendations': self._generate_cache_recommendations(metrics, memory_usage)
        }

    def _calculate_performance_grade(self, metrics: Dict[str, Any]) -> str:
        """캐시 성능 등급 계산"""
        hit_rate = metrics.get('hit_rate', 0.0)
        avg_response_time = metrics.get('avg_response_time_ms', 0.0)

        if hit_rate >= 0.8 and avg_response_time <= 1.0:
            return "EXCELLENT"
        elif hit_rate >= 0.6 and avg_response_time <= 2.0:
            return "GOOD"
        elif hit_rate >= 0.4 and avg_response_time <= 5.0:
            return "FAIR"
        else:
            return "POOR"

    def _generate_cache_recommendations(
        self,
        metrics: Dict[str, Any],
        memory_usage: Dict[str, Any]
    ) -> List[str]:
        """캐시 최적화 권장사항 생성"""
        recommendations = []

        hit_rate = metrics.get('hit_rate', 0.0)
        usage_ratio = memory_usage.get('usage_ratio', 0.0)

        if hit_rate < 0.5:
            recommendations.append("낮은 캐시 히트율: TTL 시간 증가 또는 미리 가져오기 정책 검토 필요")

        if usage_ratio > 0.9:
            recommendations.append("높은 메모리 사용률: 캐시 크기 증가 또는 정리 정책 강화 필요")

        if metrics.get('avg_response_time_ms', 0) > 2.0:
            recommendations.append("느린 캐시 응답: 메모리 최적화 또는 인덱싱 전략 검토 필요")

        if not recommendations:
            recommendations.append("캐시 성능이 양호합니다")

        return recommendations

    def clear_expired_entries(self) -> int:
        """만료된 엔트리 수동 정리

        Returns:
            정리된 엔트리 수
        """
        # 기본 캐시에서 제공하는 정리 기능 활용
        # 실제 구현은 MarketDataCache의 cleanup 메서드를 통해 이루어짐
        logger.info("만료된 캐시 엔트리 수동 정리 실행")

        # 정리 전 크기
        size_before = self.cache.get_size()

        # 비동기 정리 작업은 별도 스케줄링
        # 여기서는 통계만 반환

        return 0  # 실제 정리된 수는 별도 추적 필요

    def update_cache_policy(self, data_type: str, **policy_updates) -> None:
        """캐시 정책 동적 업데이트

        Args:
            data_type: 업데이트할 데이터 타입
            **policy_updates: 업데이트할 정책 항목들
        """
        if data_type not in self.cache_policies:
            logger.warning(f"알 수 없는 데이터 타입: {data_type}")
            return

        old_policy = self.cache_policies[data_type].copy()
        self.cache_policies[data_type].update(policy_updates)

        logger.info(f"캐시 정책 업데이트: {data_type}")
        logger.debug(f"변경 전: {old_policy}")
        logger.debug(f"변경 후: {self.cache_policies[data_type]}")

    def invalidate_symbol_cache(self, symbol: str, data_types: Optional[List[str]] = None) -> int:
        """특정 심볼의 캐시 무효화

        Args:
            symbol: 무효화할 심볼
            data_types: 무효화할 데이터 타입들 (None이면 모든 타입)

        Returns:
            무효화된 엔트리 수
        """
        if data_types is None:
            data_types = list(self.cache_policies.keys())

        invalidated_count = 0

        for data_type in data_types:
            cache_key = f"{data_type}:{symbol}"
            if self.cache.delete(cache_key):
                invalidated_count += 1
                logger.debug(f"캐시 무효화: {cache_key}")

        logger.info(f"심볼 {symbol} 캐시 무효화 완료: {invalidated_count}개 엔트리")
        return invalidated_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회

        Returns:
            캐시 사용 통계
        """
        return {
            'cache_size': getattr(self.cache, 'size', 0),
            'hit_rate': getattr(self.cache, 'hit_rate', 0.0),
            'miss_rate': 1.0 - getattr(self.cache, 'hit_rate', 0.0),
            'total_requests': getattr(self.cache, 'total_requests', 0),
            'performance_stats': getattr(self, 'performance_stats', {}),
            'cache_policy_stats': getattr(self, 'cache_policy_stats', {})
        }

    def reset_cache_stats(self) -> None:
        """캐시 통계 초기화"""
        # 성능 통계 초기화
        self.performance_stats = {
            'total_get_requests': 0,
            'total_store_requests': 0,
            'avg_get_time_ms': 0.0,
            'avg_store_time_ms': 0.0,
            'prefetch_success_count': 0,
            'prefetch_total_count': 0
        }

        # 캐시 정책 통계 초기화
        self.cache_policy_stats = {
            'hot_tier_usage': 0,
            'warm_tier_usage': 0,
            'cold_tier_usage': 0,
            'aggressive_prefetch_count': 0,
            'conservative_prefetch_count': 0
        }

        logger.info("캐시 통계 초기화 완료")

    def set_cache(self, key: str, data: Any, ttl: Optional[float] = None) -> None:
        """캐시에 데이터 저장 (호환성 메서드)

        Args:
            key: 캐시 키
            data: 저장할 데이터
            ttl: TTL (Time To Live) 초 단위
        """
        # 기본 TTL 설정
        if ttl is None:
            ttl = 30.0  # 기본 30초

        # 캐시에 저장
        self.cache.set(
            key=key,
            data=data,
            ttl=ttl
        )

        logger.debug(f"캐시 저장: {key} (TTL: {ttl}초)")

    def get_cache(self, key: str) -> Any:
        """캐시에서 데이터 조회 (호환성 메서드)

        Args:
            key: 캐시 키

        Returns:
            캐시된 데이터 또는 None
        """
        result = self.cache.get(key)
        if result:
            logger.debug(f"캐시 조회 성공: {key}")
            return result
        else:
            logger.debug(f"캐시 조회 실패: {key}")
            return None
