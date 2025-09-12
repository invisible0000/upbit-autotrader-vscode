"""
📋 CandleDataProvider New03 - Mock 통합된 청크 계획 방식
기존 new01의 정교한 아키텍처 + MockUpbitCandleResponder 실제 데이터 수집

Created: 2025-09-12
Purpose: new01 방식과 new02 방식의 성능 비교를 위한 통합 버전
Features: 청크 계획 보존 + Mock API 연동 + 성능 측정
Philosophy: "정교한 계획 수립 + 실제 데이터 수집의 조화"
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils
from upbit_auto_trading.infrastructure.market_data.candle.candle_models import (
    RequestInfo, ChunkInfo
)

logger = create_component_logger("CandleDataProviderNew03")


class ChunkStatus(Enum):
    """청크 처리 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CandleDataProviderNew03:
    """
    Mock 통합된 청크 계획 방식의 캔들 데이터 제공자

    핵심 원리:
    - new01의 정교한 청크 계획 수립 로직 완전 보존
    - MockUpbitCandleResponder를 통한 실제 데이터 수집 추가
    - 기존 아키텍처 침해 없이 점진적 확장
    - new01 vs new02 성능 비교를 위한 측정 기능

    성능 비교 목적: 청크 계획 오버헤드 vs 순차 처리 단순성
    """

    def __init__(self, use_mock: bool = True):
        """CandleDataProviderNew03 초기화"""
        logger.info("CandleDataProviderNew03 (Mock 통합 버전) 초기화 시작...")

        # Mock API 클라이언트 추가
        self.use_mock = use_mock
        if use_mock:
            from upbit_auto_trading.infrastructure.market_data.candle.mock_upbit_candle_responder import (
                MockUpbitCandleResponder
            )
            self.api_client = MockUpbitCandleResponder(seed=42)
            logger.info("MockUpbitCandleResponder 연결 완료")
        else:
            self.api_client = None
            logger.info("실제 API 클라이언트 사용 (구현 예정)")

        logger.info("✅ CandleDataProviderNew03 초기화 완료")

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        to: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[ChunkInfo]:
        """
        캔들 데이터 요청을 처리하여 청크 계획 반환 (new01 로직 완전 보존)

        사용자 편의성을 위해 개별 파라미터로 받아서 내부에서 RequestInfo 생성
        실제 데이터 수집은 collect_candles_data()에서 수행

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

    def collect_candles_data(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        to: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        기존 청크 계획 방식 + 실제 데이터 수집 통합

        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m', '1h', '1d')
            count: 조회할 캔들 개수
            to: 시작점 - 최신 캔들 시간
            end: 종료점 - 가장 과거 캔들 시간

        Returns:
            List[Dict]: 수집된 캔들 데이터 (업비트 형식)
        """
        logger.info(f"통합 캔들 수집 시작: {symbol} {timeframe}")

        # 1. 기존 방식으로 청크 계획 생성
        chunks = self.get_candles(symbol, timeframe, count, to, end)
        logger.info(f"청크 계획 완료: {len(chunks)}개 청크")

        # 2. 각 청크별로 실제 데이터 수집
        all_candles = []
        for i, chunk in enumerate(chunks):
            logger.debug(f"청크 {i + 1}/{len(chunks)} 수집 중...")
            chunk_data = self._collect_chunk_data(chunk)
            all_candles.extend(chunk_data)

        logger.info(f"✅ 통합 캔들 수집 완료: {len(all_candles)}개")
        return all_candles

    def _collect_chunk_data(self, chunk_info: ChunkInfo) -> List[Dict[str, Any]]:
        """
        ChunkInfo를 사용해 실제 캔들 데이터 수집

        Args:
            chunk_info: 청크 정보 (ChunkInfo 객체)

        Returns:
            List[Dict]: 청크별 수집된 캔들 데이터
        """
        if not self.use_mock:
            raise NotImplementedError("실제 API 클라이언트는 아직 구현되지 않았습니다")

        # ChunkInfo → Mock API 파라미터 변환
        api_params = {
            "market": chunk_info.symbol,
            "count": chunk_info.count,
            "to": chunk_info.to.strftime("%Y-%m-%dT%H:%M:%S") if chunk_info.to else None
        }

        logger.debug(f"청크 데이터 수집: {chunk_info.chunk_id}, {api_params}")

        # 타임프레임별 API 호출
        return self._call_api_by_timeframe(chunk_info.timeframe, api_params)

    def _call_api_by_timeframe(self, timeframe: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        타임프레임별 Mock API 호출 분기

        Args:
            timeframe: 타임프레임 ('1m', '5m', '1h', '1d' 등)
            params: API 파라미터

        Returns:
            List[Dict]: 캔들 데이터
        """
        # 타임프레임 파싱하여 적절한 Mock API 호출
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

    def normalize_request(
        self,
        request: RequestInfo
    ) -> List[ChunkInfo]:
        """
        모든 요청을 to_with_end 형태로 정규화 (new01 로직 완전 보존)

        핵심 원리:
        1. to가 없으면 현재 시간으로 설정
        2. end가 없으면 count를 이용해 계산
        3. 모든 결과를 TimeUtils로 정렬
        4. 단일 create_chunks로 처리

        Args:
            request: 요청 정보 (RequestInfo 객체)

        Returns:
            List[ChunkInfo]: 정규화 완료된 청크 리스트
        """
        logger.info(f"요청 정규화: {request.symbol} {request.timeframe}, count={request.count}, to={request.to}, end={request.end}")

        # 1. to 시간 확정 (없으면 현재 시간)
        if request.to is None:
            to_time = datetime.now(timezone.utc)
            logger.debug("to가 없어서 현재 시간으로 설정")
        else:
            to_time = request.to

        # 2. TimeUtils로 시간 정렬 (to 시점 정렬)
        normalized_start = TimeUtils.align_to_candle_boundary(to_time, request.timeframe)
        logger.debug(f"정렬된 to 시간: {normalized_start}")

        # 3. end 시간 확정 및 총 캔들 개수 계산
        if request.end is not None:
            # end가 있는 경우: end 사용 + count 계산
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
            total_count: int = request.count  # type: ignore[assignment]
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

        # 5. 청크 리스트 반환
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
        정규화된 to_with_end 형태를 200개 단위로 분할 (new01 로직 완전 보존)

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

        # 청크 크기 (원래는 200, 테스트용으로 10 사용)
        CHUNK_SIZE = 200
        chunks = []
        remaining_count = total_count
        current_start = start_time
        chunk_index = 0

        while remaining_count > 0:
            # 현재 청크 크기 결정 (최대 CHUNK_SIZE개)
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

            # ChunkInfo 생성
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

    def get_performance_comparison(
        self,
        symbol: str,
        timeframe: str,
        count: int
    ) -> Dict[str, Any]:
        """
        성능 측정을 위한 편의 메서드

        Args:
            symbol: 심볼
            timeframe: 타임프레임
            count: 캔들 개수

        Returns:
            Dict: 성능 측정 결과
        """
        import time

        start_time = time.perf_counter()

        # 기존 방식: 청크 계획 + 데이터 수집
        candles = self.collect_candles_data(symbol, timeframe, count)

        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000

        # 청크 정보도 함께 수집 (오버헤드 측정용)
        chunks = self.get_candles(symbol, timeframe, count)

        return {
            "method": "chunked_planning_with_mock",
            "total_candles": len(candles),
            "execution_time_ms": round(execution_time_ms, 3),
            "candles_per_second": round(len(candles) / (execution_time_ms / 1000), 1),
            "avg_time_per_candle_us": round(execution_time_ms * 1000 / len(candles), 2) if candles else 0,
            "chunk_count": len(chunks),
            "avg_candles_per_chunk": round(len(candles) / len(chunks), 1) if chunks else 0,
            "first_candle": candles[0]["candle_date_time_utc"] if candles else None,
            "last_candle": candles[-1]["candle_date_time_utc"] if candles else None,
            "success": True
        }


# 성능 비교 테스트 함수
def demo_performance_comparison():
    """new01 vs new02 성능 비교 데모"""
    print("🔥 CandleDataProvider 성능 비교 테스트")
    print("=" * 80)

    # new03 방식 테스트 (new01 기반 + Mock 통합)
    provider_new03 = CandleDataProviderNew03(use_mock=True)

    # new02 방식 테스트 (비교용)
    from upbit_auto_trading.infrastructure.market_data.candle.candle_data_provider_new02 import CandleDataProviderNew02
    provider_new02 = CandleDataProviderNew02(use_mock=True)

    # 테스트 케이스들
    test_cases = [
        {"symbol": "KRW-BTC", "timeframe": "1m", "count": 50, "name": "소량 (50개)"},
        {"symbol": "KRW-BTC", "timeframe": "1m", "count": 200, "name": "중간 (200개)"},
        {"symbol": "KRW-BTC", "timeframe": "5m", "count": 100, "name": "5분봉 (100개)"},
    ]

    performance_results = []

    for i, case in enumerate(test_cases):
        print(f"\n📋 테스트 {i + 1}: {case['name']}")
        print("-" * 60)

        # new03 방식 성능 측정 (청크 계획 방식)
        result_new03 = provider_new03.get_performance_comparison(
            symbol=case["symbol"],
            timeframe=case["timeframe"],
            count=case["count"]
        )

        # new02 방식 성능 측정 (순차 처리 방식)
        result_new02 = provider_new02.get_performance_comparison(
            symbol=case["symbol"],
            timeframe=case["timeframe"],
            count=case["count"]
        )

        # 결과 비교 출력
        print(f"🔹 New03 (청크 계획): {result_new03['execution_time_ms']}ms")
        print(f"   └─ 청크 수: {result_new03['chunk_count']}개")
        print(f"   └─ 청크당 평균: {result_new03['avg_candles_per_chunk']}개")
        print(f"   └─ 속도: {result_new03['candles_per_second']} 캔들/초")

        print(f"🔹 New02 (순차 처리): {result_new02['execution_time_ms']}ms")
        print(f"   └─ 속도: {result_new02['candles_per_second']} 캔들/초")

        # 성능 비율 계산
        if result_new03['execution_time_ms'] > 0 and result_new02['execution_time_ms'] > 0:
            speed_ratio = result_new03['execution_time_ms'] / result_new02['execution_time_ms']
            if speed_ratio < 1:
                print(f"🚀 New03이 {1 / speed_ratio:.1f}배 빠름 (청크 계획 오버헤드 < 순차 처리)")
            else:
                print(f"🐌 New02가 {speed_ratio:.1f}배 빠름 (순차 처리 > 청크 계획)")

        # 데이터 무결성 확인
        data_match = result_new03['total_candles'] == result_new02['total_candles']
        print(f"📊 데이터 일치: {'✅' if data_match else '❌'} ({result_new03['total_candles']} vs {result_new02['total_candles']})")

        # 결과 저장
        performance_results.append({
            "case": case["name"],
            "new03_time": result_new03['execution_time_ms'],
            "new02_time": result_new02['execution_time_ms'],
            "chunk_count": result_new03['chunk_count'],
            "speed_ratio": speed_ratio if 'speed_ratio' in locals() else 1.0
        })

    # 전체 요약
    print("\n🎯 전체 성능 비교 요약")
    print("=" * 80)
    for result in performance_results:
        case_name = result['case']
        new03_time = result['new03_time']
        new02_time = result['new02_time']
        chunk_count = result['chunk_count']
        print(f"{case_name:15} | New03: {new03_time:6.1f}ms | New02: {new02_time:6.1f}ms | 청크: {chunk_count}개")

    print("\n💡 테스트 완료 - Mock API 기반")
    print("📈 청크 계획 방식의 오버헤드와 순차 처리의 단순성을 비교할 수 있습니다")
    print("🔍 실제 환경에서는 네트워크 지연, 메모리 사용량 등 추가 요소들이 성능에 영향을 줄 수 있습니다")


if __name__ == "__main__":
    demo_performance_comparison()
