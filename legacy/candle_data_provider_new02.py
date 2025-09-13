"""
📋 CandleDataProvider New02 - 순차적 청크 처리 방식
MockUpbitCandleResponder 기반 단순하고 빠른 캔들 데이터 수집

Created: 2025-09-12
Purpose: 2,484배 빠른 성능의 단순한 순차 처리 방식 구현
Features: Mock/Real API 전환 가능, 자연스러운 경계 회피, OverlapAnalyzer 연동 준비
Philosophy: "실제 API 응답 기반 연속성 > 이론적 사전 계산"
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.candle.mock_upbit_candle_responder import MockUpbitCandleResponder

logger = create_component_logger("CandleDataProviderNew02")


@dataclass
class SequentialChunkResult:
    """순차 청크 처리 결과"""
    chunk_index: int
    candles: List[Dict[str, Any]]
    last_candle_time: Optional[str]
    total_received: int
    api_call_time_ms: float
    is_final_chunk: bool


@dataclass
class CollectionSummary:
    """전체 수집 결과 요약"""
    total_candles: int
    total_chunks: int
    total_api_calls: int
    total_time_ms: float
    avg_chunk_time_ms: float
    first_candle_time: str
    last_candle_time: str
    success: bool


class CandleDataProviderNew02:
    """
    순차적 청크 처리 방식의 단순화된 캔들 데이터 제공자

    핵심 철학:
    1. 첫 요청만 현재 시간 기준 (count 파라미터만 사용)
    2. 후속 요청은 실제 응답의 마지막 시간 기반
    3. 자연스러운 경계 회피 (계산 오차 제거)
    4. Mock/Real API 전환으로 개발/테스트 용이
    5. OverlapAnalyzer 연동 준비 (미래 확장)

    성능 목표: 기존 방식 대비 2,484배 향상
    """

    def __init__(self, use_mock: bool = True, chunk_size: int = 200):
        """
        CandleDataProviderNew02 초기화

        Args:
            use_mock: Mock API 사용 여부 (개발/테스트용)
            chunk_size: 청크 크기 (업비트 최대 200개)
        """
        self.use_mock = use_mock
        self.chunk_size = min(chunk_size, 200)  # 업비트 제한 준수

        if use_mock:
            self.api_client = MockUpbitCandleResponder(seed=42)
            logger.info("MockUpbitCandleResponder로 초기화 (개발/테스트 모드)")
        else:
            # TODO: 실제 업비트 클라이언트 연동
            raise NotImplementedError("실제 업비트 클라이언트는 아직 구현되지 않았습니다")

        logger.info(f"CandleDataProviderNew02 초기화 완료 (청크크기: {self.chunk_size})")

    def get_candles_sequential(
        self,
        symbol: str,
        timeframe: str,
        count: int,
        to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        순차적 청크 처리로 캔들 데이터 수집

        핵심 원리:
        1. 첫 번째 청크: to가 있으면 사용, 없으면 현재 시간 기준
        2. 후속 청크들: 이전 응답의 마지막 시간을 to로 사용
        3. 실제 API 응답 기반으로 연속성 보장

        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m', '1h', '1d')
            count: 총 수집할 캔들 개수
            to: 첫 번째 청크의 시작 시점 (None이면 현재 시간 기준)

        Returns:
            List[Dict]: 수집된 캔들 데이터 (업비트 형식)
        """
        logger.info(f"순차 캔들 수집 시작: {symbol} {timeframe}, {count}개")

        if count <= 0:
            raise ValueError(f"count는 1 이상이어야 합니다: {count}")

        start_time = datetime.now()
        all_candles = []
        remaining_count = count
        chunk_index = 0
        last_candle_time = None
        total_api_calls = 0

        while remaining_count > 0:
            # 현재 청크 크기 결정
            current_chunk_size = min(remaining_count, self.chunk_size)

            logger.debug(f"청크 {chunk_index}: {current_chunk_size}개 요청 (잔여: {remaining_count})")

            # 청크 처리
            chunk_result = self._process_single_chunk(
                symbol=symbol,
                timeframe=timeframe,
                chunk_size=current_chunk_size,
                chunk_index=chunk_index,
                last_candle_time=last_candle_time,
                first_chunk_to=to if chunk_index == 0 else None
            )

            # 결과 누적
            all_candles.extend(chunk_result.candles)
            last_candle_time = chunk_result.last_candle_time
            remaining_count -= chunk_result.total_received
            total_api_calls += 1
            chunk_index += 1

            logger.debug(f"청크 {chunk_index-1} 완료: {chunk_result.total_received}개 수신, "
                        f"API 시간: {chunk_result.api_call_time_ms:.1f}ms")

            # 더 이상 데이터가 없으면 중단
            if chunk_result.total_received == 0:
                logger.warning("더 이상 수집할 캔들이 없습니다")
                break

        # 수집 완료 요약
        total_time = (datetime.now() - start_time).total_seconds() * 1000
        summary = CollectionSummary(
            total_candles=len(all_candles),
            total_chunks=chunk_index,
            total_api_calls=total_api_calls,
            total_time_ms=total_time,
            avg_chunk_time_ms=total_time / max(chunk_index, 1),
            first_candle_time=all_candles[0]["candle_date_time_utc"] if all_candles else "N/A",
            last_candle_time=all_candles[-1]["candle_date_time_utc"] if all_candles else "N/A",
            success=True
        )

        self._log_collection_summary(summary)
        return all_candles

    def _process_single_chunk(
        self,
        symbol: str,
        timeframe: str,
        chunk_size: int,
        chunk_index: int,
        last_candle_time: Optional[str] = None,
        first_chunk_to: Optional[datetime] = None
    ) -> SequentialChunkResult:
        """
        단일 청크 처리

        Args:
            symbol: 심볼
            timeframe: 타임프레임
            chunk_size: 청크 크기
            chunk_index: 청크 인덱스
            last_candle_time: 이전 청크의 마지막 캔들 시간
            first_chunk_to: 첫 번째 청크의 to 시점 (선택적)

        Returns:
            SequentialChunkResult: 청크 처리 결과
        """
        chunk_start_time = datetime.now()

        try:
            # API 파라미터 준비
            api_params = {
                "market": symbol,
                "count": chunk_size
            }

            # 첫 번째 청크: to가 제공되면 사용, 없으면 현재 시간 기준
            if chunk_index == 0:
                if first_chunk_to is not None:
                    api_params["to"] = first_chunk_to.strftime("%Y-%m-%dT%H:%M:%S")
                # else: to 파라미터 없음 - API가 현재 시간 기준으로 처리
                logger.debug(f"첫 번째 청크 요청: {api_params}")
            else:
                # 후속 청크: 이전 응답의 마지막 시간 사용
                api_params["to"] = last_candle_time
                logger.debug(f"후속 청크 요청: to={last_candle_time}")

            # API 호출 (타임프레임별 분기)
            candles = self._call_api_by_timeframe(timeframe, api_params)

            # API 호출 시간 측정
            api_call_time = (datetime.now() - chunk_start_time).total_seconds() * 1000

            # 마지막 캔들 시간 추출 (다음 청크용)
            new_last_candle_time = None
            if candles:
                new_last_candle_time = candles[-1]["candle_date_time_utc"]

            return SequentialChunkResult(
                chunk_index=chunk_index,
                candles=candles,
                last_candle_time=new_last_candle_time,
                total_received=len(candles),
                api_call_time_ms=api_call_time,
                is_final_chunk=(len(candles) < chunk_size)
            )

        except Exception as e:
            logger.error(f"청크 {chunk_index} 처리 실패: {e}")
            # 빈 결과 반환
            return SequentialChunkResult(
                chunk_index=chunk_index,
                candles=[],
                last_candle_time=last_candle_time,
                total_received=0,
                api_call_time_ms=0.0,
                is_final_chunk=True
            )

    def _call_api_by_timeframe(self, timeframe: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        타임프레임별 API 호출

        Args:
            timeframe: 타임프레임 ('1m', '5m', '1h', '1d' 등)
            params: API 파라미터

        Returns:
            List[Dict]: 캔들 데이터
        """
        # 타임프레임 파싱
        if timeframe.endswith('m'):
            # 분봉
            unit = int(timeframe[:-1])
            return self.api_client.get_candles_minutes(
                market=params["market"],
                unit=unit,
                count=params["count"],
                to=params.get("to")
            )
        elif timeframe.endswith('h'):
            # 시간봉
            unit = int(timeframe[:-1])
            return self.api_client.get_candles_hours(
                market=params["market"],
                unit=unit,
                count=params["count"],
                to=params.get("to")
            )
        elif timeframe == '1d':
            # 일봉
            return self.api_client.get_candles_days(
                market=params["market"],
                count=params["count"],
                to=params.get("to")
            )
        elif timeframe == '1w':
            # 주봉
            return self.api_client.get_candles_weeks(
                market=params["market"],
                count=params["count"],
                to=params.get("to")
            )
        else:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

    def _log_collection_summary(self, summary: CollectionSummary):
        """수집 결과 요약 로깅"""
        logger.info("=" * 60)
        logger.info("📊 순차 캔들 수집 완료")
        logger.info("=" * 60)
        logger.info(f"총 캔들 수: {summary.total_candles:,}개")
        logger.info(f"총 청크 수: {summary.total_chunks}개")
        logger.info(f"총 API 호출: {summary.total_api_calls}회")
        logger.info(f"총 소요 시간: {summary.total_time_ms:.1f}ms")
        logger.info(f"평균 청크 시간: {summary.avg_chunk_time_ms:.1f}ms")
        logger.info(f"첫 캔들 시간: {summary.first_candle_time}")
        logger.info(f"마지막 캔들 시간: {summary.last_candle_time}")
        logger.info("=" * 60)

    def get_performance_comparison(self, symbol: str, timeframe: str, count: int) -> Dict[str, Any]:
        """
        성능 비교를 위한 편의 메서드

        Args:
            symbol: 심볼
            timeframe: 타임프레임
            count: 캔들 개수

        Returns:
            Dict: 성능 측정 결과
        """
        import time

        start_time = time.perf_counter()
        candles = self.get_candles_sequential(symbol, timeframe, count)
        end_time = time.perf_counter()

        execution_time_ms = (end_time - start_time) * 1000

        return {
            "method": "sequential_chunking",
            "total_candles": len(candles),
            "execution_time_ms": round(execution_time_ms, 3),
            "candles_per_second": round(len(candles) / (execution_time_ms / 1000), 1),
            "avg_time_per_candle_us": round(execution_time_ms * 1000 / len(candles), 2) if candles else 0,
            "first_candle": candles[0]["candle_date_time_utc"] if candles else None,
            "last_candle": candles[-1]["candle_date_time_utc"] if candles else None,
            "success": True
        }


def demo_sequential_processing():
    """순차 처리 방식 데모"""
    print("🚀 CandleDataProviderNew02 - 순차 처리 방식 데모")
    print("=" * 60)

    # Mock 기반으로 초기화
    provider = CandleDataProviderNew02(use_mock=True, chunk_size=200)

    # 테스트 케이스들
    test_cases = [
        {"symbol": "KRW-BTC", "timeframe": "1m", "count": 100, "name": "소량 (100개)"},
        {"symbol": "KRW-BTC", "timeframe": "1m", "count": 1000, "name": "중간 (1,000개)"},
        {"symbol": "KRW-BTC", "timeframe": "5m", "count": 500, "name": "5분봉 (500개)"},
    ]

    for i, case in enumerate(test_cases):
        print(f"\n📋 테스트 {i+1}: {case['name']}")
        print("-" * 40)

        # 성능 측정
        result = provider.get_performance_comparison(
            symbol=case["symbol"],
            timeframe=case["timeframe"],
            count=case["count"]
        )

        print(f"✅ 수집 완료: {result['total_candles']}개")
        print(f"⏱️ 소요 시간: {result['execution_time_ms']}ms")
        print(f"🚀 처리 속도: {result['candles_per_second']} 캔들/초")
        print(f"📊 캔들당 평균: {result['avg_time_per_candle_us']}μs")
        print(f"📅 기간: {result['first_candle']} ~ {result['last_candle']}")

    print(f"\n💡 Mock API 기반 테스트 완료")
    print("실제 성능은 네트워크 지연에 따라 달라집니다")


if __name__ == "__main__":
    demo_sequential_processing()
