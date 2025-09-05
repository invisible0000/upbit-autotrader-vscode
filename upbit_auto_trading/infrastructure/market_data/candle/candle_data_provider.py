"""
캔들 데이터 제공자 - 메인 인터페이스

업비트 API 특성에 최적화된 캔들 데이터 제공 서비스
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.shared.overlap_analyzer import (
    OverlapAnalyzer,
    CacheStrategy,
    ContinuityType,
    TimeRange,
    create_time_range_from_candles,
    format_analysis_summary
)

logger = create_component_logger("CandleDataProvider")


class CandleDataProvider:
    """
    캔들 데이터 제공자

    🎯 업비트 API 최적화:
    - OverlapAnalyzer 활용하여 API 호출 최소화
    - 200개 단위 요청 최적화
    - Rate Limit 고려한 지능형 캐시 전략
    """

    def __init__(self):
        # 핵심 컴포넌트들
        self._overlap_analyzer = OverlapAnalyzer()
        # self._client = CandleClient()        # TODO: 구현 예정
        # self._repository = CandleRepository()  # TODO: 구현 예정
        # self._cache = CandleCache()          # TODO: 구현 예정

        logger.info("캔들 데이터 제공자 초기화 완료")

    def get_candles(self,
                   symbol: str,
                   interval: str,
                   count: int = 200) -> Dict[str, Any]:
        """
        캔들 데이터 조회 (지능형 최적화)

        Args:
            symbol: 거래 심볼 (예: KRW-BTC)
            interval: 캔들 간격 (예: 1m, 5m, 1h)
            count: 요청할 캔들 개수 (기본 200개)

        Returns:
            Dict: 캔들 데이터 응답
        """
        logger.info(f"캔들 데이터 요청: {symbol} {interval} {count}개")

        # 1. 요청 범위 생성
        end_time = datetime.now()
        # TODO: interval을 기반으로 start_time 계산
        start_time = end_time  # 임시
        request_range = TimeRange(start_time, end_time, count)

        # 2. 캐시에서 기존 데이터 조회
        cached_candles = self._get_cached_candles(symbol, interval)

        if cached_candles:
            # 3. OverlapAnalyzer로 겹침 분석 🎯
            cache_range = create_time_range_from_candles(cached_candles)
            if cache_range:
                analysis_result = self._overlap_analyzer.analyze_overlap(
                    cache_range=cache_range,
                    request_range=request_range,
                    symbol=symbol,
                    timeframe=interval
                )

                logger.info(f"겹침 분석 결과: {format_analysis_summary(analysis_result)}")

                # 4. 분석 결과에 따른 전략 실행
                return self._execute_strategy(analysis_result, symbol, interval, cached_candles)

        # 5. 캐시가 없는 경우 전체 새로 요청
        logger.info(f"캐시 없음 - 전체 요청: {symbol} {interval}")
        return self._fetch_and_cache_candles(symbol, interval, count)

    def _execute_strategy(self,
                         analysis_result,
                         symbol: str,
                         interval: str,
                         cached_candles: List[Dict]) -> Dict[str, Any]:
        """분석 결과에 따른 전략 실행"""

        strategy = analysis_result.recommended_strategy
        confidence = analysis_result.strategy_confidence

        logger.info(f"전략 실행: {strategy.value} (확신도: {confidence:.1%})")

        if strategy == CacheStrategy.USE_CACHE_DIRECT:
            # 캐시 직접 사용 (API 호출 0회) 🎯
            logger.info("캐시 직접 사용 - API 호출 없음")
            return self._format_cache_response(cached_candles, "cache_direct")

        elif strategy == CacheStrategy.EXTEND_CACHE:
            # 캐시 확장 (API 호출 1회) 🎯
            logger.info("캐시 확장 - 최소 API 호출")
            return self._extend_cache_data(analysis_result, symbol, interval, cached_candles)

        elif strategy == CacheStrategy.PARTIAL_FILL:
            # 부분 채움 (누락 구간만 요청) 🎯
            logger.info(f"부분 채움 - {analysis_result.api_call_count_estimate}회 API 호출")
            return self._partial_fill_data(analysis_result, symbol, interval, cached_candles)

        else:  # FULL_REFRESH
            # 전체 갱신 (기존 캐시 포기) 🎯
            logger.info("전체 갱신 - 캐시 효율성 낮음")
            count = analysis_result.request_range.count
            return self._fetch_and_cache_candles(symbol, interval, count)

    def _extend_cache_data(self,
                          analysis_result,
                          symbol: str,
                          interval: str,
                          cached_candles: List[Dict]) -> Dict[str, Any]:
        """캐시 확장 전략 실행"""

        continuity_type = analysis_result.continuity_type
        missing_ranges = analysis_result.missing_ranges

        if continuity_type == ContinuityType.FORWARD_EXTEND:
            # 순방향 확장: 최신 데이터 추가 요청
            logger.info("순방향 확장 - 최신 캔들 추가")
            # TODO: 최신 캔들만 API 요청하여 캐시에 추가

        elif continuity_type == ContinuityType.BACKWARD_EXTEND:
            # 역방향 확장: 과거 데이터 추가 요청
            logger.info("역방향 확장 - 과거 캔들 추가")
            # TODO: 과거 캔들만 API 요청하여 캐시에 추가

        # 임시 응답
        return self._format_cache_response(cached_candles, "cache_extended")

    def _partial_fill_data(self,
                          analysis_result,
                          symbol: str,
                          interval: str,
                          cached_candles: List[Dict]) -> Dict[str, Any]:
        """부분 채움 전략 실행"""

        missing_ranges = analysis_result.missing_ranges
        logger.info(f"누락 구간 {len(missing_ranges)}개 - 개별 요청")

        # TODO: 각 누락 구간별로 API 요청하여 데이터 병합
        for i, missing_range in enumerate(missing_ranges):
            logger.info(f"누락 구간 {i+1}: {missing_range}")
            # API 요청 로직

        # 임시 응답
        return self._format_cache_response(cached_candles, "partial_filled")

    def _get_cached_candles(self, symbol: str, interval: str) -> Optional[List[Dict]]:
        """캐시에서 캔들 데이터 조회"""
        # TODO: 실제 캐시 구현
        logger.debug(f"캐시 조회: {symbol} {interval}")
        return None  # 임시

    def _fetch_and_cache_candles(self, symbol: str, interval: str, count: int) -> Dict[str, Any]:
        """API에서 캔들 데이터 조회 후 캐시 저장"""
        # TODO: 실제 API 클라이언트 구현
        logger.info(f"API 요청: {symbol} {interval} {count}개")

        # 임시 응답
        return {
            "data": [],
            "source": "api_fresh",
            "symbol": symbol,
            "interval": interval,
            "count": count,
            "timestamp": datetime.now().isoformat()
        }

    def _format_cache_response(self, candles: List[Dict], source: str) -> Dict[str, Any]:
        """캐시 응답 포맷팅"""
        return {
            "data": candles,
            "source": source,
            "count": len(candles),
            "timestamp": datetime.now().isoformat(),
            "from_cache": True
        }

    def get_overlap_analyzer_stats(self) -> Dict[str, Any]:
        """OverlapAnalyzer 성능 통계"""
        return self._overlap_analyzer.get_performance_stats()


# 사용 예시
if __name__ == "__main__":
    provider = CandleDataProvider()

    # 캔들 데이터 요청
    result = provider.get_candles("KRW-BTC", "1m", 200)
    print(f"응답: {result}")

    # 분석기 통계 확인
    stats = provider.get_overlap_analyzer_stats()
    print(f"분석기 통계: {stats}")
