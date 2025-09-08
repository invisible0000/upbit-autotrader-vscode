"""
📋 CandleDataProvider v4.0 - Infrastructure Service 메인 구현
DDD Infrastructure Layer에서 서브시스템에 캔들 데이터 제공하는 단일 진입점

Created: 2025-01-08
Purpose: 5가지 파라미터 조합 지원, 200개 청크 분할, DB/API 혼합 최적화
Features: inclusive_start 시간 처리, 캐시 활용, 겹침 분석 기반 API 요청 최적화
"""

import time
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager
from upbit_auto_trading.infrastructure.repositories.sqlite_candle_repository import SqliteCandleRepository
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils
from upbit_auto_trading.infrastructure.market_data.candle.models import (
    CandleData, CandleDataResponse, CandleChunk, CollectionResult,
    create_success_response, create_error_response
)

logger = create_component_logger("CandleDataProvider")


class CandleDataProvider:
    """
    캔들 데이터 Infrastructure Service - 서브시스템들의 단일 진입점

    주요 기능:
    - 5가지 파라미터 조합 지원 (count, start_time, end_time)
    - inclusive_start 업비트 API 시간 처리
    - 200개 청크 자동 분할 및 순차 수집
    - DB/API 혼합 최적화 (OverlapAnalyzer 연동)
    - 캐시 활용 (60초 TTL)
    - 대량 요청시 target_end_time 도달 시 자동 중단

    DDD 원칙:
    - Infrastructure Service로 서브시스템들이 직접 import하여 사용
    - 복잡한 청크 처리와 최적화를 서브시스템에서 감춤
    - Domain 로직은 포함하지 않고 순수 데이터 제공만 담당
    """

    def __init__(self,
                 db_manager: Optional[DatabaseManager] = None,
                 upbit_client: Optional[UpbitPublicClient] = None):
        """
        CandleDataProvider 초기화

        Args:
            db_manager: 데이터베이스 매니저 (None이면 기본 인스턴스 생성)
            upbit_client: 업비트 API 클라이언트 (None이면 기본 인스턴스 생성)
        """
        # Infrastructure 로깅 초기화
        logger.info("CandleDataProvider v4.0 초기화 시작...")

        # 데이터베이스 연결 설정
        self.db_manager = db_manager
        if self.db_manager is None:
            logger.debug("기본 DatabaseManager 생성 중...")
            # 기본 DatabaseManager는 추후 의존성 주입으로 개선 예정
            from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager
            from upbit_auto_trading.infrastructure.configuration import get_path_service

            # 전역 경로 서비스에서 표준 DB 경로 가져오기
            path_service = get_path_service()
            db_paths = {
                'settings': str(path_service.get_database_path('settings')),
                'strategies': str(path_service.get_database_path('strategies')),
                'market_data': str(path_service.get_database_path('market_data'))
            }
            self.db_manager = DatabaseManager(db_paths)        # Repository 초기화
        self.repository = SqliteCandleRepository(self.db_manager)

        # 업비트 API 클라이언트 설정
        self.upbit_client = upbit_client
        self._client_owned = upbit_client is None  # 클라이언트 소유권 추적

        # 캐시 (추후 구현 예정)
        self.cache = None

        # 겹침 분석기 (추후 구현 예정)
        self.overlap_analyzer = None

        # 성능 통계
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'api_requests': 0,
            'db_queries': 0,
            'chunks_processed': 0,
            'average_response_time_ms': 0.0
        }

        logger.info("✅ CandleDataProvider v4.0 초기화 완료")

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self._ensure_upbit_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.close()

    async def _ensure_upbit_client(self):
        """업비트 클라이언트 확보"""
        if self.upbit_client is None:
            logger.debug("기본 UpbitPublicClient 생성 중...")
            from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import (
                create_upbit_public_client_async
            )
            self.upbit_client = await create_upbit_public_client_async()
            self._client_owned = True

    async def close(self):
        """리소스 정리"""
        if self._client_owned and self.upbit_client:
            await self.upbit_client.close()
            self.upbit_client = None
            logger.debug("업비트 클라이언트 리소스 정리 완료")

    # ================================================================
    # 서브시스템 진입점 - 메인 API
    # ================================================================

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        inclusive_start: bool = True
    ) -> CandleDataResponse:
        """
        캔들 데이터 조회 - 5가지 파라미터 조합 지원

        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m', '1h', '1d')
            count: 조회할 캔들 개수 (최대 제한 없음, 자동 청크 분할)
            start_time: 시작 시간 (사용자 제공시 inclusive_start 적용)
            end_time: 종료 시간 (항상 포함, 조정 불필요)
            inclusive_start: 사용자 제공 start_time 포함 처리 여부
                           True: start_time 포함하도록 조정 (기본, 직관적)
                           False: API 네이티브 배제 방식 (고급 사용자용)

        Returns:
            CandleDataResponse: 캔들 데이터 응답
                - success: 성공 여부
                - candles: 캔들 데이터 리스트 (시간순 정렬)
                - total_count: 총 개수
                - data_source: 데이터 소스 ("cache", "db", "api", "mixed")
                - response_time_ms: 응답 시간

        Raises:
            ValueError: 잘못된 파라미터 조합 또는 미래 시간 요청
            Exception: API 오류 또는 시스템 오류

        Examples:
            # 1. count만 지정 (최근 200개)
            response = await provider.get_candles("KRW-BTC", "1m", count=200)

            # 2. start_time + count (포함 모드)
            response = await provider.get_candles(
                "KRW-BTC", "1m",
                start_time=datetime.now() - timedelta(hours=10),
                count=600,
                inclusive_start=True  # 10시간 전부터 포함
            )

            # 3. start_time + end_time (시간 범위)
            response = await provider.get_candles(
                "KRW-BTC", "1m",
                start_time=datetime.now() - timedelta(hours=5),
                end_time=datetime.now() - timedelta(hours=1),
                inclusive_start=True  # 5시간 전부터 포함
            )

            # 4. end_time만 지정
            response = await provider.get_candles(
                "KRW-BTC", "1m",
                end_time=datetime.now() - timedelta(hours=2)
            )

            # 5. 기본값 (최근 200개)
            response = await provider.get_candles("KRW-BTC", "1m")
        """
        request_start_time = time.perf_counter()
        self.stats['total_requests'] += 1

        try:
            logger.info(f"🚀 캔들 데이터 요청: {symbol} {timeframe}, "
                        f"count={count}, start_time={start_time}, end_time={end_time}, "
                        f"inclusive_start={inclusive_start}")

            # 1. 요청 검증 및 표준화
            validated_params = await self._validate_and_standardize_request(
                symbol, timeframe, count, start_time, end_time, inclusive_start
            )
            final_start_time, final_end_time, final_count = validated_params

            logger.debug(f"📋 표준화된 요청: start={final_start_time}, end={final_end_time}, count={final_count}")

            # 2. 캐시 우선 확인 (추후 구현)
            # cache_result = await self._check_cache_complete_range(symbol, timeframe, final_start_time, final_count)
            # if cache_result:
            #     return self._create_cache_response(cache_result, time.perf_counter() - request_start_time)

            # 3. 대량 요청시 200개 청크로 분할
            chunks = self._split_into_chunks(symbol, timeframe, final_count, final_start_time, final_end_time)
            logger.debug(f"📦 청크 분할: {len(chunks)}개 청크 (200개씩)")

            # 4. 청크들을 순차 수집 (target_end_time 도달시 중단)
            collected_candles = await self._collect_chunks_sequentially(chunks, final_end_time)

            # 5. 최종 응답 조합
            response = await self._assemble_response(
                collected_candles,
                request_start_time,
                len(chunks)
            )

            logger.info(f"✅ 캔들 데이터 요청 완료: {symbol} {timeframe}, "
                        f"{response.total_count}개 수집, {response.response_time_ms:.1f}ms")

            return response

        except Exception as e:
            error_time = (time.perf_counter() - request_start_time) * 1000
            logger.error(f"❌ 캔들 데이터 요청 실패: {symbol} {timeframe}, {e}")
            return create_error_response(str(e), error_time)

    # ================================================================
    # 요청 검증 및 표준화
    # ================================================================

    async def _validate_and_standardize_request(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        inclusive_start: bool
    ) -> Tuple[datetime, datetime, int]:
        """
        요청 파라미터 검증 및 표준화

        Returns:
            Tuple[datetime, datetime, int]: (final_start_time, final_end_time, final_count)
        """
        # 기본 검증
        if not symbol or not timeframe:
            raise ValueError("symbol과 timeframe은 필수입니다")

        # count + end_time 동시 사용 금지
        if count is not None and end_time is not None:
            raise ValueError("count와 end_time은 동시에 사용할 수 없습니다")

        # TimeUtils로 최종 시간 범위 계산
        final_start_time, final_end_time, final_count = TimeUtils.determine_target_end_time(
            count=count,
            start_time=start_time,
            end_time=end_time,
            timeframe=timeframe
        )

        # 미래 시간 검증
        now = datetime.now(timezone.utc)
        if final_start_time > now:
            raise ValueError(f"시작 시간이 미래입니다: {final_start_time}")
        if final_end_time > now:
            raise ValueError(f"종료 시간이 미래입니다: {final_end_time}")

        # 사용자 제공 start_time에 대한 inclusive_start 처리
        user_provided_start = start_time is not None and (count is not None or end_time is not None)
        adjusted_start_time = self._adjust_start_time_for_api(
            final_start_time, timeframe, inclusive_start, user_provided_start
        )

        return adjusted_start_time, final_end_time, final_count

    def _adjust_start_time_for_api(
        self,
        start_time: datetime,
        timeframe: str,
        inclusive_start: bool,
        user_provided_start: bool
    ) -> datetime:
        """
        업비트 API 시간 처리 - 사용자 제공 start_time에만 조정 적용

        Args:
            start_time: 시작 시간
            timeframe: 타임프레임
            inclusive_start: 포함 모드 여부
            user_provided_start: 사용자가 직접 제공한 start_time 여부

        Returns:
            datetime: 조정된 시작 시간
        """
        if not user_provided_start or not inclusive_start:
            # 조정 불필요 케이스:
            # 1. 시스템 자동 생성 start_time (케이스 1,4,5)
            # 2. 사용자가 배제 모드 선택 (inclusive_start=False)
            return start_time

        # 사용자 제공 start_time + inclusive_start=True: 포함하도록 조정
        # 업비트 API는 start_time을 배제하므로, 시간상 과거로 조정하여 포함 보장
        adjusted_start = TimeUtils.get_before_candle_time(start_time, timeframe)
        logger.debug(f"🎯 사용자 start_time 포함 조정: {start_time} → {adjusted_start} (timeframe: {timeframe})")
        return adjusted_start

    # ================================================================
    # 청크 분할 및 순차 수집
    # ================================================================

    def _split_into_chunks(
        self,
        symbol: str,
        timeframe: str,
        count: int,
        start_time: datetime,
        end_time: datetime
    ) -> List[CandleChunk]:
        """
        전체 요청을 200개 청크로 분할

        Args:
            symbol: 심볼
            timeframe: 타임프레임
            count: 총 캔들 개수
            start_time: 시작 시간
            end_time: 종료 시간

        Returns:
            List[CandleChunk]: 청크 리스트
        """
        chunks = []
        chunk_size = 200
        current_start = start_time
        remaining_count = count
        chunk_index = 0

        while remaining_count > 0:
            # 현재 청크의 캔들 개수 결정
            current_chunk_count = min(chunk_size, remaining_count)

            # 청크 생성
            chunk = CandleChunk(
                symbol=symbol,
                timeframe=timeframe,
                start_time=current_start,
                count=current_chunk_count,
                chunk_index=chunk_index
            )
            chunks.append(chunk)

            # 다음 청크 시작점 계산
            if remaining_count > chunk_size:
                # TimeUtils로 다음 시작점 계산
                chunk_time_span = TimeUtils.get_timeframe_seconds(timeframe) * current_chunk_count
                current_start = current_start + timedelta(seconds=chunk_time_span)

                # end_time 도달 검사
                if current_start >= end_time:
                    logger.debug(f"📍 end_time 도달로 청크 분할 중단: {current_start} >= {end_time}")
                    break

            remaining_count -= current_chunk_count
            chunk_index += 1

        logger.debug(f"📦 청크 분할 완료: {len(chunks)}개 청크, 예상 총 {sum(c.count for c in chunks)}개 캔들")
        return chunks

    async def _collect_chunks_sequentially(
        self,
        chunks: List[CandleChunk],
        target_end_time: datetime
    ) -> List[CandleData]:
        """
        청크들을 순서대로 하나씩 수집

        Args:
            chunks: 청크 리스트
            target_end_time: 목표 종료 시간 (이 시점 도달시 수집 중단)

        Returns:
            List[CandleData]: 수집된 모든 캔들 데이터
        """
        all_collected_candles = []
        connected_end = None  # 연속된 데이터의 끝점 추적

        for chunk_idx, chunk in enumerate(chunks):
            try:
                logger.debug(f"📦 청크 {chunk_idx + 1}/{len(chunks)} 수집 시작: "
                             f"{chunk.symbol} {chunk.timeframe}, {chunk.count}개")

                # 단일 청크 수집
                collection_result = await self._collect_single_chunk(chunk, connected_end)

                if collection_result.collected_candles:
                    all_collected_candles.extend(collection_result.collected_candles)

                    # 수집된 캔들의 마지막 시간으로 connected_end 업데이트
                    last_candle = collection_result.collected_candles[-1]
                    logger.debug(f"🔍 last_candle.candle_date_time_utc 원본: '{last_candle.candle_date_time_utc}'")

                    # UTC 시간대 정보를 명시적으로 추가
                    # API에서 오는 시간이 'Z' 없이 UTC이므로 직접 timezone 설정
                    if 'Z' in last_candle.candle_date_time_utc:
                        # Z가 있는 경우: Z를 +00:00으로 변환
                        utc_time_str = last_candle.candle_date_time_utc.replace('Z', '+00:00')
                        connected_end = datetime.fromisoformat(utc_time_str)
                    else:
                        # Z가 없는 경우: UTC 시간대를 직접 설정
                        naive_time = datetime.fromisoformat(last_candle.candle_date_time_utc)
                        connected_end = naive_time.replace(tzinfo=timezone.utc)

                    logger.debug(f"🔍 최종 connected_end: {connected_end} (tzinfo: {connected_end.tzinfo})")

                    logger.debug(f"✅ 청크 {chunk_idx + 1} 수집 완료: {len(collection_result.collected_candles)}개, "
                                 f"소스={collection_result.data_source}, connected_end={connected_end}")
                else:
                    logger.warning(f"⚠️ 청크 {chunk_idx + 1} 수집 결과 없음")

                # target_end_time 도달 검사 (시간대 정보 맞춤)
                if connected_end and target_end_time:
                    # target_end_time이 시간대 정보가 없으면 UTC로 간주
                    if target_end_time.tzinfo is None:
                        target_end_time_utc = target_end_time.replace(tzinfo=timezone.utc)
                    else:
                        target_end_time_utc = target_end_time

                    if self._is_collection_complete(connected_end, target_end_time_utc):
                        logger.info(f"🎯 target_end_time 도달로 수집 완료: {connected_end} >= {target_end_time_utc}")
                        break

                self.stats['chunks_processed'] += 1

            except Exception as e:
                logger.error(f"❌ 청크 {chunk_idx + 1} 수집 실패: {e}")
                # 청크 실패시에도 계속 진행 (부분 성공 허용)
                continue

        logger.info(f"📊 전체 청크 수집 완료: {len(all_collected_candles)}개 캔들")
        return all_collected_candles

    async def _collect_single_chunk(
        self,
        chunk: CandleChunk,
        connected_end: Optional[datetime]
    ) -> CollectionResult:
        """
        단일 청크 수집 로직

        Args:
            chunk: 수집할 청크
            connected_end: 이전 청크에서 연속된 데이터의 끝점

        Returns:
            CollectionResult: 청크 수집 결과
        """
        collection_start_time = time.perf_counter()

        try:
            # 현재는 단순히 API에서만 수집 (추후 OverlapAnalyzer 연동)
            # TODO: OverlapAnalyzer를 통한 겹침 분석 및 DB/API 혼합 수집
            collected_candles = await self._collect_from_api_only(chunk)

            # Repository에 저장
            if collected_candles:
                await self.repository.save_candle_chunk(chunk.symbol, chunk.timeframe, collected_candles)
                self.stats['db_queries'] += 1

            collection_time_ms = (time.perf_counter() - collection_start_time) * 1000

            return CollectionResult(
                chunk=chunk,
                collected_candles=collected_candles,
                data_source="api",  # 현재는 API만 사용
                api_requests_made=1,
                collection_time_ms=collection_time_ms
            )

        except Exception as e:
            logger.error(f"❌ 청크 수집 중 오류: {chunk.symbol} {chunk.timeframe}, {e}")
            raise

    async def _collect_from_api_only(self, chunk: CandleChunk) -> List[CandleData]:
        """
        API에서만 캔들 데이터 수집 (현재 구현)

        Args:
            chunk: 수집할 청크

        Returns:
            List[CandleData]: 수집된 캔들 데이터
        """
        await self._ensure_upbit_client()

        # 타임프레임별 API 엔드포인트 매핑
        api_response = await self._call_upbit_api(chunk)

        if not api_response:
            logger.warning(f"⚠️ API 응답 없음: {chunk.symbol} {chunk.timeframe}")
            return []

        # API 응답을 CandleData 모델로 변환
        candles = []
        for api_candle in api_response:
            try:
                candle = CandleData.from_upbit_api(api_candle, chunk.timeframe)
                candles.append(candle)
            except Exception as e:
                logger.warning(f"⚠️ 캔들 데이터 변환 실패: {e}")
                continue

        self.stats['api_requests'] += 1
        logger.debug(f"📡 API 수집 완료: {chunk.symbol} {chunk.timeframe}, {len(candles)}개")

        return candles

    async def _call_upbit_api(self, chunk: CandleChunk) -> List[dict]:
        """
        업비트 API 호출 (타임프레임별 엔드포인트 매핑)

        Args:
            chunk: 청크 정보

        Returns:
            List[dict]: 업비트 API 응답 데이터
        """
        symbol = chunk.symbol
        count = chunk.count

        # 업비트 API: to 파라미터 없이 호출하면 최신 데이터부터 count개 반환
        # 현재는 단순 구현으로 to 파라미터 제외 (추후 정확한 시간 범위 처리 개선)
        to_time = None  # 임시로 None 사용하여 최신 데이터 조회

        logger.debug(f"📡 API 호출: {symbol} {chunk.timeframe}, count={count}, to={to_time}")

        try:
            if chunk.timeframe == '1s':
                if to_time:
                    return await self.upbit_client.get_candles_seconds(symbol, count=count, to=to_time)
                else:
                    return await self.upbit_client.get_candles_seconds(symbol, count=count)
            elif chunk.timeframe.endswith('m'):
                # 분봉: 1m, 3m, 5m, 15m, 30m, 60m, 240m
                unit = int(chunk.timeframe[:-1])
                if to_time:
                    return await self.upbit_client.get_candles_minutes(unit, symbol, count=count, to=to_time)
                else:
                    return await self.upbit_client.get_candles_minutes(unit, symbol, count=count)
            elif chunk.timeframe.endswith('h'):
                # 시간봉을 분봉으로 변환: 1h=60m, 4h=240m
                if chunk.timeframe == '1h':
                    unit = 60
                elif chunk.timeframe == '4h':
                    unit = 240
                else:
                    raise ValueError(f"지원하지 않는 시간봉: {chunk.timeframe}")
                if to_time:
                    return await self.upbit_client.get_candles_minutes(unit, symbol, count=count, to=to_time)
                else:
                    return await self.upbit_client.get_candles_minutes(unit, symbol, count=count)
            elif chunk.timeframe == '1d':
                if to_time:
                    return await self.upbit_client.get_candles_days(symbol, count=count, to=to_time)
                else:
                    return await self.upbit_client.get_candles_days(symbol, count=count)
            elif chunk.timeframe == '1w':
                if to_time:
                    return await self.upbit_client.get_candles_weeks(symbol, count=count, to=to_time)
                else:
                    return await self.upbit_client.get_candles_weeks(symbol, count=count)
            elif chunk.timeframe == '1M':
                if to_time:
                    return await self.upbit_client.get_candles_months(symbol, count=count, to=to_time)
                else:
                    return await self.upbit_client.get_candles_months(symbol, count=count)
            elif chunk.timeframe == '1y':
                if to_time:
                    return await self.upbit_client.get_candles_years(symbol, count=count, to=to_time)
                else:
                    return await self.upbit_client.get_candles_years(symbol, count=count)
            else:
                raise ValueError(f"지원하지 않는 타임프레임: {chunk.timeframe}")

        except Exception as e:
            logger.error(f"❌ 업비트 API 호출 실패: {symbol} {chunk.timeframe}, {e}")
            raise

    def _is_collection_complete(self, current_end: datetime, target_end: datetime) -> bool:
        """
        현재 수집이 목표 종료 시간에 도달했는지 확인

        Args:
            current_end: 현재 수집된 데이터의 끝 시간
            target_end: 목표 종료 시간

        Returns:
            bool: 수집 완료 여부
        """
        return current_end >= target_end

    # ================================================================
    # 응답 조합 및 통계
    # ================================================================

    async def _assemble_response(
        self,
        collected_candles: List[CandleData],
        request_start_time: float,
        chunks_count: int
    ) -> CandleDataResponse:
        """
        수집된 모든 청크를 하나의 응답으로 조합

        Args:
            collected_candles: 수집된 모든 캔들 데이터
            request_start_time: 요청 시작 시간
            chunks_count: 처리된 청크 개수

        Returns:
            CandleDataResponse: 최종 응답
        """
        # 중복 제거 (UTC 시간 기준)
        unique_candles = {}
        for candle in collected_candles:
            key = f"{candle.symbol}_{candle.timeframe}_{candle.candle_date_time_utc}"
            if key not in unique_candles:
                unique_candles[key] = candle

        # 시간순 정렬 (과거 → 최신)
        sorted_candles = sorted(
            unique_candles.values(),
            key=lambda c: c.candle_date_time_utc
        )

        # 응답 시간 계산
        response_time_ms = (time.perf_counter() - request_start_time) * 1000

        # 평균 응답 시간 업데이트
        if self.stats['average_response_time_ms'] == 0.0:
            self.stats['average_response_time_ms'] = response_time_ms
        else:
            # 지수 이동 평균 (α=0.1)
            self.stats['average_response_time_ms'] = (
                0.9 * self.stats['average_response_time_ms'] + 0.1 * response_time_ms
            )

        # 데이터 소스 결정 (현재는 API만)
        data_source = "api"  # 추후 "mixed", "db", "cache" 추가

        return create_success_response(
            candles=sorted_candles,
            data_source=data_source,
            response_time_ms=response_time_ms
        )

    # ================================================================
    # 통계 및 상태 조회
    # ================================================================

    def get_stats(self) -> dict:
        """서비스 통계 정보 조회"""
        stats = self.stats.copy()

        # 업비트 클라이언트 통계 추가
        if self.upbit_client:
            stats['upbit_client'] = self.upbit_client.get_stats()

        return stats

    def get_supported_timeframes(self) -> List[str]:
        """지원하는 타임프레임 목록"""
        return ['1s', '1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M', '1y']

    # ================================================================
    # 편의 메서드들
    # ================================================================

    async def get_latest_candles(self, symbol: str, timeframe: str, count: int = 200) -> CandleDataResponse:
        """최신 캔들 조회 (편의 메서드)"""
        return await self.get_candles(symbol, timeframe, count=count)

    async def get_candles_since(
        self,
        symbol: str,
        timeframe: str,
        since: datetime,
        inclusive: bool = True
    ) -> CandleDataResponse:
        """특정 시점 이후 캔들 조회 (편의 메서드)"""
        return await self.get_candles(
            symbol, timeframe,
            start_time=since,
            inclusive_start=inclusive
        )

    async def get_candles_range(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        inclusive_start: bool = True
    ) -> CandleDataResponse:
        """시간 범위 캔들 조회 (편의 메서드)"""
        return await self.get_candles(
            symbol, timeframe,
            start_time=start,
            end_time=end,
            inclusive_start=inclusive_start
        )


# ================================================================
# 편의 팩토리 함수
# ================================================================

def create_candle_data_provider(
    db_manager: Optional[DatabaseManager] = None,
    upbit_client: Optional[UpbitPublicClient] = None
) -> CandleDataProvider:
    """
    CandleDataProvider 인스턴스 생성 (편의 함수)

    Args:
        db_manager: 데이터베이스 매니저 (None이면 기본 생성)
        upbit_client: 업비트 클라이언트 (None이면 기본 생성)

    Returns:
        CandleDataProvider: 설정된 프로바이더 인스턴스

    Examples:
        # 기본 설정으로 생성
        provider = create_candle_data_provider()

        # 커스텀 클라이언트로 생성
        custom_client = create_upbit_public_client()
        provider = create_candle_data_provider(upbit_client=custom_client)
    """
    return CandleDataProvider(db_manager=db_manager, upbit_client=upbit_client)


async def create_candle_data_provider_async(
    db_manager: Optional[DatabaseManager] = None,
    upbit_client: Optional[UpbitPublicClient] = None
) -> CandleDataProvider:
    """
    CandleDataProvider 비동기 생성 및 초기화 (편의 함수)

    Args:
        db_manager: 데이터베이스 매니저 (None이면 기본 생성)
        upbit_client: 업비트 클라이언트 (None이면 기본 생성)

    Returns:
        CandleDataProvider: 초기화된 프로바이더 인스턴스

    Note:
        업비트 클라이언트를 미리 초기화하여 첫 번째 요청 시 지연을 줄입니다.
    """
    provider = CandleDataProvider(db_manager=db_manager, upbit_client=upbit_client)
    await provider._ensure_upbit_client()
    return provider
