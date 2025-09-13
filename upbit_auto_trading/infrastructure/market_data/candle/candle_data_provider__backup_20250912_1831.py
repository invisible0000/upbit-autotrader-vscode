"""
📋 CandleDataProvider v4.0 - TASK_02 구현 완료
요청 정규화 및 청크 생성 로직 구현 + 하이브리드 순차 처리

Created: 2025-09-11 (Updated: 2025-09-12)
Purpose: normalize_request와 create_chunks 메서드 구현 + 순차 청크 관리
Features: 4가지 파라미터 조합 지원, 설정 가능한 청크 분할, 실시간 상태 관리
Architecture: 기존 TASK_02 요구사항 + New04 하이브리드 방식 결합
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils
from upbit_auto_trading.infrastructure.market_data.candle.candle_models import (
    ChunkInfo, CandleData
)
from upbit_auto_trading.domain.repositories.candle_repository_interface import (
    CandleRepositoryInterface
)
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import (
    UpbitPublicClient
)
from upbit_auto_trading.infrastructure.market_data.candle.overlap_analyzer import (
    OverlapAnalyzer
)

logger = create_component_logger("CandleDataProvider")


class ChunkStatus(Enum):
    """청크 처리 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CollectionState:
    """캔들 수집 상태 관리"""
    request_id: str
    symbol: str
    timeframe: str
    total_requested: int
    total_collected: int = 0
    completed_chunks: List[ChunkInfo] = field(default_factory=list)
    current_chunk: Optional[ChunkInfo] = None
    last_candle_time: Optional[str] = None  # 마지막 수집된 캔들 시간 (연속성용)
    estimated_total_chunks: int = 0
    estimated_completion_time: Optional[datetime] = None
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_completed: bool = False
    error_message: Optional[str] = None
    target_end: Optional[datetime] = None  # end 파라미터 목표 시점 (Phase 1 추가)

    # 남은 시간 추적 필드들
    last_update_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    avg_chunk_duration: float = 0.0  # 평균 청크 처리 시간 (초)
    remaining_chunks: int = 0  # 남은 청크 수
    estimated_remaining_seconds: float = 0.0  # 실시간 계산된 남은 시간


@dataclass
class CollectionPlan:
    """수집 계획 (최소 정보만)"""
    total_count: int
    estimated_chunks: int
    estimated_duration_seconds: float
    first_chunk_params: Dict[str, Any]  # 첫 번째 청크 요청 파라미터


class CandleDataProvider:
    """
    캔들 데이터 제공자 v4.0 - TASK_02 구현 완료

    핵심 원리:
    1. 최소한의 사전 계획 (청크 수와 예상 시간만)
    2. 실시간 순차 청크 생성 (이전 응답 기반)
    3. 상태 추적으로 중단/재시작 지원
    4. 10 RPS 기반 예상 완료 시간 제공

    장점:
    - new01의 안정성: 상태 관리, 검증, 중단/재시작
    - new02의 효율성: 순차 처리, 응답 기반 연속성
    - 최소 오버헤드: 사전 계획 최소화
    - 실시간 확장: 필요할 때만 청크 생성
    """

    def __init__(
        self,
        repository: CandleRepositoryInterface,
        upbit_client: UpbitPublicClient,
        overlap_analyzer: OverlapAnalyzer,
        chunk_size: int = 200
    ):
        """
        CandleDataProvider v4.0 초기화 - DI 패턴 적용

        Args:
            repository: CandleRepositoryInterface 구현체 (DB 접근)
            upbit_client: UpbitPublicClient (API 호출)
            overlap_analyzer: OverlapAnalyzer v5.0 (겹침 분석)
            chunk_size: 청크 크기 (기본값 200, 최대 200)
        """
        # 의존성 주입
        self.repository = repository
        self.upbit_client = upbit_client
        self.overlap_analyzer = overlap_analyzer

        # 기존 설정
        self.chunk_size = min(chunk_size, 200)  # 업비트 제한 준수
        self.active_collections: Dict[str, CollectionState] = {}
        self.api_rate_limit_rps = 10  # 10 RPS 기준

        logger.info("CandleDataProvider v4.0 (DI 패턴 + 하이브리드 순차 처리) 초기화 완료")
        logger.info(f"청크 크기: {self.chunk_size}, API Rate Limit: {self.api_rate_limit_rps} RPS")
        logger.info(f"의존성: Repository={type(repository).__name__}, Client={type(upbit_client).__name__}")
        logger.info(f"의존성: OverlapAnalyzer={type(overlap_analyzer).__name__}")

    def plan_collection(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        to: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> CollectionPlan:
        """
        수집 계획 수립 (최소한의 정보만)

        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m', '1h', '1d')
            count: 조회할 캔들 개수
            to: 시작점 (첫 번째 청크용)
            end: 종료점

        Returns:
            CollectionPlan: 최소 계획 정보
        """
        logger.info(f"수집 계획 수립: {symbol} {timeframe}, count={count}, to={to}, end={end}")

        # 동적 비즈니스 검증
        current_time = datetime.now(timezone.utc)
        if to is not None and to > current_time:
            raise ValueError(f"to 시점이 미래입니다: {to}")
        if end is not None and end > current_time:
            raise ValueError(f"end 시점이 미래입니다: {end}")

        # 총 캔들 개수 계산 (최소한의 정규화)
        total_count = self._calculate_total_count(
            count=count,
            to=to,
            end=end,
            timeframe=timeframe,
            current_time=current_time
        )

        # 예상 청크 수 계산
        estimated_chunks = (total_count + self.chunk_size - 1) // self.chunk_size

        # 예상 완료 시간 계산 (10 RPS 기준)
        estimated_duration_seconds = estimated_chunks / self.api_rate_limit_rps

        # 첫 번째 청크 파라미터 생성
        first_chunk_params = self._create_first_chunk_params(
            symbol=symbol,
            count=count,
            to=to,
            end=end,
            current_time=current_time
        )

        plan = CollectionPlan(
            total_count=total_count,
            estimated_chunks=estimated_chunks,
            estimated_duration_seconds=estimated_duration_seconds,
            first_chunk_params=first_chunk_params
        )

        logger.info(f"✅ 계획 수립 완료: {total_count:,}개 캔들, {estimated_chunks}청크, "
                    f"예상 소요시간: {estimated_duration_seconds:.1f}초")
        return plan

    def start_collection(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        to: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> str:
        """
        캔들 수집 시작 (상태 추적 시작)

        Args:
            symbol: 심볼
            timeframe: 타임프레임
            count: 조회할 캔들 개수
            to: 시작점
            end: 종료점

        Returns:
            str: 수집 요청 ID (상태 추적용)
        """
        logger.info(f"캔들 수집 시작: {symbol} {timeframe}")

        # 계획 수립
        plan = self.plan_collection(symbol, timeframe, count, to, end)

        # 요청 ID 생성 (타임스탬프 기반)
        request_id = f"{symbol}_{timeframe}_{int(datetime.now().timestamp())}"

        # 수집 상태 초기화
        estimated_completion = datetime.now(timezone.utc) + timedelta(
            seconds=plan.estimated_duration_seconds
        )

        collection_state = CollectionState(
            request_id=request_id,
            symbol=symbol,
            timeframe=timeframe,
            total_requested=plan.total_count,
            estimated_total_chunks=plan.estimated_chunks,
            estimated_completion_time=estimated_completion,
            remaining_chunks=plan.estimated_chunks,
            estimated_remaining_seconds=plan.estimated_duration_seconds,
            target_end=end  # Phase 1: end 파라미터 보관
        )

        # 첫 번째 청크 생성
        first_chunk = self._create_next_chunk(
            collection_state=collection_state,
            chunk_params=plan.first_chunk_params,
            chunk_index=0
        )
        collection_state.current_chunk = first_chunk

        # 상태 등록
        self.active_collections[request_id] = collection_state

        logger.info(f"✅ 수집 시작: 요청 ID {request_id}, 예상 완료: {estimated_completion}")
        return request_id

    def get_next_chunk(self, request_id: str) -> Optional[ChunkInfo]:
        """
        다음 처리할 청크 정보 반환

        Args:
            request_id: 수집 요청 ID

        Returns:
            ChunkInfo: 다음 청크 정보 (완료된 경우 None)
        """
        if request_id not in self.active_collections:
            raise ValueError(f"알 수 없는 요청 ID: {request_id}")

        state = self.active_collections[request_id]

        if state.is_completed:
            logger.info(f"수집 완료됨: {request_id}")
            return None

        if state.current_chunk is None:
            logger.warning(f"처리할 청크가 없습니다: {request_id}")
            return None

        logger.debug(f"다음 청크 반환: {state.current_chunk.chunk_id}")
        return state.current_chunk

    async def _fetch_chunk_from_api(self, chunk_info: ChunkInfo) -> List[Dict[str, Any]]:
        """
        실제 API 호출을 통한 청크 데이터 수집

        Args:
            chunk_info: 청크 정보 (symbol, timeframe, count, to 등)

        Returns:
            List[Dict[str, Any]]: 업비트 API 응답 캔들 데이터

        Raises:
            ValueError: 지원하지 않는 타임프레임
            Exception: API 호출 실패
        """
        logger.debug(f"API 청크 요청 시작: {chunk_info.chunk_id}")

        try:
            # 타임프레임별 API 메서드 선택
            if chunk_info.timeframe.endswith('m'):
                # 분봉 (1m, 3m, 5m, 10m, 15m, 30m, 60m, 240m)
                unit = int(chunk_info.timeframe[:-1])
                if unit not in [1, 3, 5, 10, 15, 30, 60, 240]:
                    raise ValueError(f"지원하지 않는 분봉 단위: {unit}")

                to_param = chunk_info.to.strftime("%Y-%m-%dT%H:%M:%S") if chunk_info.to else None
                candles = await self.upbit_client.get_candles_minutes(
                    unit=unit,
                    market=chunk_info.symbol,
                    count=chunk_info.count,
                    to=to_param
                )

            elif chunk_info.timeframe == '1d':
                # 일봉
                to_param = chunk_info.to.strftime("%Y-%m-%d") if chunk_info.to else None
                candles = await self.upbit_client.get_candles_days(
                    market=chunk_info.symbol,
                    count=chunk_info.count,
                    to=to_param
                )

            elif chunk_info.timeframe == '1w':
                # 주봉
                to_param = chunk_info.to.strftime("%Y-%m-%d") if chunk_info.to else None
                candles = await self.upbit_client.get_candles_weeks(
                    market=chunk_info.symbol,
                    count=chunk_info.count,
                    to=to_param
                )

            elif chunk_info.timeframe == '1M':
                # 월봉
                to_param = chunk_info.to.strftime("%Y-%m") if chunk_info.to else None
                candles = await self.upbit_client.get_candles_months(
                    market=chunk_info.symbol,
                    count=chunk_info.count,
                    to=to_param
                )

            else:
                raise ValueError(f"지원하지 않는 타임프레임: {chunk_info.timeframe}")

            logger.info(f"✅ API 청크 완료: {chunk_info.chunk_id}, 수집: {len(candles)}개")
            return candles

        except Exception as e:
            logger.error(f"❌ API 청크 실패: {chunk_info.chunk_id}, 오류: {e}")
            raise

    def _convert_upbit_response_to_candles(
        self,
        api_response: List[Dict[str, Any]],
        timeframe: str
    ) -> List[CandleData]:
        """
        업비트 API 응답을 CandleData 객체로 변환

        Args:
            api_response: 업비트 API 응답 데이터
            timeframe: 타임프레임 (예: '1m', '5m', '1d')

        Returns:
            List[CandleData]: 변환된 CandleData 객체들

        Note:
            - 업비트 API는 최신순(내림차순) 정렬로 응답
            - CandleData.from_upbit_api()를 사용하여 안전한 변환 수행
        """
        logger.debug(f"API 응답 변환 시작: {len(api_response)}개 캔들, 타임프레임: {timeframe}")

        try:
            converted_candles = []
            for candle_dict in api_response:
                candle_data = CandleData.from_upbit_api(candle_dict, timeframe)
                converted_candles.append(candle_data)

            logger.debug(f"✅ API 응답 변환 완료: {len(converted_candles)}개")
            return converted_candles

        except Exception as e:
            logger.error(f"❌ API 응답 변환 실패: {e}")
            logger.error(f"문제된 데이터 샘플: {api_response[:1] if api_response else 'Empty'}")
            raise

    async def _save_candles_to_repository(
        self,
        symbol: str,
        timeframe: str,
        candles: List[CandleData]
    ) -> int:
        """
        Repository를 통한 캔들 데이터 DB 저장

        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m')
            candles: 저장할 CandleData 객체들

        Returns:
            int: 실제 저장된 캔들 개수

        Note:
            - Repository의 save_candle_chunk() 메서드 활용
            - INSERT OR IGNORE 방식으로 중복 자동 처리
            - 트랜잭션 기반 안전한 일괄 저장
        """
        if not candles:
            logger.warning("저장할 캔들 데이터가 없습니다")
            return 0

        logger.debug(f"DB 저장 시작: {symbol} {timeframe}, {len(candles)}개")

        try:
            saved_count = await self.repository.save_candle_chunk(symbol, timeframe, candles)
            logger.debug(f"✅ DB 저장 완료: {saved_count}/{len(candles)}개 저장됨")
            return saved_count

        except Exception as e:
            logger.error(f"❌ DB 저장 실패: {symbol} {timeframe}, {len(candles)}개, 오류: {e}")
            raise

    async def _analyze_chunk_overlap(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ):
        """
        OverlapAnalyzer를 활용한 청크 겹침 분석 (성능 최적화 용도)

        Args:
            symbol: 심볼
            timeframe: 타임프레임
            start_time: 요청 시작 시간
            end_time: 요청 종료 시간

        Returns:
            OverlapResult: 5가지 상태별 겹침 분석 결과

        Note:
            - 현재 버전에서는 단순히 API 호출 우선 정책
            - 추후 성능 최적화 시 DB/API 혼합 처리 활용 예정
        """
        logger.debug(f"겹침 분석: {symbol} {timeframe}, {start_time} ~ {end_time}")

        try:
            # OverlapAnalyzer v5.0 활용
            from upbit_auto_trading.infrastructure.market_data.candle.candle_models import OverlapRequest

            # Timezone 안전 처리: 모든 datetime을 UTC로 통일
            safe_start_time = self._ensure_utc_timezone(start_time)
            safe_end_time = self._ensure_utc_timezone(end_time)

            # 예상 캔들 개수 계산
            expected_count = self._calculate_api_count(safe_start_time, safe_end_time, timeframe)

            overlap_request = OverlapRequest(
                symbol=symbol,
                timeframe=timeframe,
                target_start=safe_start_time,
                target_end=safe_end_time,
                target_count=expected_count
            )

            overlap_result = await self.overlap_analyzer.analyze_overlap(overlap_request)
            logger.debug(f"겹침 분석 결과: {overlap_result.status.value} (예상 개수: {expected_count})")

            return overlap_result

        except Exception as e:
            logger.warning(f"겹침 분석 실패: {e}, API 호출로 진행")
            return None

    async def mark_chunk_completed(
        self,
        request_id: str
    ) -> bool:
        """
        실제 API 호출을 통한 청크 완료 처리 및 다음 청크 생성

        Args:
            request_id: 수집 요청 ID

        Returns:
            bool: 전체 수집 완료 여부

        Note:
            - 실제 API 호출: _fetch_chunk_from_api()
            - 데이터 변환: _convert_upbit_response_to_candles()
            - DB 저장: _save_candles_to_repository()
            - 연속성 보장: 이전 청크 기반 다음 청크 생성
        """
        if request_id not in self.active_collections:
            raise ValueError(f"알 수 없는 요청 ID: {request_id}")

        state = self.active_collections[request_id]

        if state.current_chunk is None:
            raise ValueError("처리 중인 청크가 없습니다")

        logger.info(f"🚀 청크 처리 시작: {state.current_chunk.chunk_id}")

        try:
            # 1. OverlapAnalyzer로 겹침 분석 (성능 최적화)
            chunk_start = state.current_chunk.to  # API 요청의 시작점
            chunk_end = self._calculate_chunk_end_time(state.current_chunk)  # 예상 종료점

            overlap_result = await self._analyze_chunk_overlap(
                state.symbol,
                state.timeframe,
                chunk_start,
                chunk_end
            )

            # 2. 겹침 분석 결과에 따른 데이터 수집 전략
            if overlap_result and hasattr(overlap_result, 'status'):
                candle_data_list, api_calls_made = await self._collect_data_by_overlap_strategy(
                    state.current_chunk, overlap_result
                )
                logger.info(f"🔍 겹침 분석 적용: {overlap_result.status.value}, API 호출: {'예' if api_calls_made else '아니오'}")
            else:
                # 겹침 분석 실패 시 폴백: 기존 API 호출 방식
                logger.warning("겹침 분석 실패 → API 호출 폴백")
                api_response = await self._fetch_chunk_from_api(state.current_chunk)
                candle_data_list = self._convert_upbit_response_to_candles(
                    api_response,
                    state.timeframe
                )
                api_calls_made = True

            # 3. Repository를 통한 DB 저장 (필요한 경우에만)
            if candle_data_list:
                saved_count = await self._save_candles_to_repository(
                    state.symbol,
                    state.timeframe,
                    candle_data_list
                )
            else:
                saved_count = 0
                logger.debug("저장할 새로운 데이터가 없습니다 (완전 겹침)")

            # 4. 현재 청크 완료 처리
            completed_chunk = state.current_chunk
            completed_chunk.status = "completed"
            state.completed_chunks.append(completed_chunk)
            state.total_collected += len(candle_data_list)

            # 5. 마지막 캔들 시간 업데이트 (다음 청크 연속성용)
            if candle_data_list:
                # CandleData 객체 또는 dict에서 마지막 캔들 시간 추출
                last_candle = candle_data_list[-1]
                if hasattr(last_candle, 'candle_date_time_utc'):
                    state.last_candle_time = last_candle.candle_date_time_utc
                elif isinstance(last_candle, dict) and 'candle_date_time_utc' in last_candle:
                    state.last_candle_time = last_candle['candle_date_time_utc']
                else:
                    logger.warning("마지막 캔들에서 시간 정보를 추출할 수 없습니다")

            # 6. 남은 시간 정보 업데이트
            self._update_remaining_time_estimates(state)

            logger.info(f"✅ 청크 완료: {completed_chunk.chunk_id}, "
                        f"수집: {len(candle_data_list)}개, 저장: {saved_count}개, "
                        f"누적: {state.total_collected}/{state.total_requested}, "
                        f"남은시간: {state.estimated_remaining_seconds:.1f}초")

            # 7. 수집 완료 확인 (개수 + 시간 조건)
            count_reached = state.total_collected >= state.total_requested

            # end 시점 도달 확인
            end_time_reached = False
            if state.target_end and candle_data_list:
                try:
                    # 마지막 수집 캔들의 시간을 datetime으로 변환
                    last_candle = candle_data_list[-1]
                    last_candle_time_str = None

                    if hasattr(last_candle, 'candle_date_time_utc'):
                        last_candle_time_str = last_candle.candle_date_time_utc
                    elif isinstance(last_candle, dict) and 'candle_date_time_utc' in last_candle:
                        last_candle_time_str = last_candle['candle_date_time_utc']

                    if last_candle_time_str:
                        # ISO format 처리 (Z suffix 제거)
                        if last_candle_time_str.endswith('Z'):
                            last_candle_time_str = last_candle_time_str[:-1] + '+00:00'
                        last_candle_time = datetime.fromisoformat(last_candle_time_str)

                        # 마지막 캔들 시간이 target_end보다 과거면 정지
                        end_time_reached = last_candle_time <= state.target_end

                        logger.debug(
                            f"시간 조건 확인: 마지막캔들={last_candle_time}, "
                            f"목표종료={state.target_end}, 도달={end_time_reached}"
                        )
                except Exception as e:
                    logger.warning(f"시간 파싱 실패: {e}")

            if count_reached or end_time_reached:
                completion_reason = "개수 달성" if count_reached else "end 시점 도달"
                state.is_completed = True
                state.current_chunk = None
                logger.info(f"🎉 전체 수집 완료 ({completion_reason}): {request_id}, {state.total_collected}개")
                return True

            # 8. 다음 청크 생성
            next_chunk_index = len(state.completed_chunks)
            remaining_count = state.total_requested - state.total_collected
            next_chunk_size = min(remaining_count, self.chunk_size)

            # 다음 청크 파라미터 (업비트 API의 자연스러운 연속성 활용)
            next_chunk_params = {
                "market": state.symbol,
                "count": next_chunk_size,
                "to": state.last_candle_time  # 마지막 캔들 시간을 그대로 사용 (업비트 API가 자동으로 이전 캔들 반환)
            }            # 다음 청크 생성
            next_chunk = self._create_next_chunk(
                collection_state=state,
                chunk_params=next_chunk_params,
                chunk_index=next_chunk_index
            )
            state.current_chunk = next_chunk

            logger.debug(f"➡️ 다음 청크 생성: {next_chunk.chunk_id}, 잔여: {remaining_count}개")
            return False

        except Exception as e:
            # 청크 실패 처리
            if state.current_chunk:
                state.current_chunk.status = "failed"
                state.error_message = str(e)

            logger.error(f"❌ 청크 처리 실패: {state.current_chunk.chunk_id if state.current_chunk else 'Unknown'}, 오류: {e}")
            raise

    def get_collection_status(self, request_id: str) -> Dict[str, Any]:
        """
        수집 상태 조회

        Args:
            request_id: 수집 요청 ID

        Returns:
            Dict: 상세 상태 정보
        """
        if request_id not in self.active_collections:
            raise ValueError(f"알 수 없는 요청 ID: {request_id}")

        state = self.active_collections[request_id]

        progress_percentage = (state.total_collected / state.total_requested) * 100
        elapsed_time = datetime.now(timezone.utc) - state.start_time
        completed_chunks = len(state.completed_chunks)

        return {
            "request_id": request_id,
            "symbol": state.symbol,
            "timeframe": state.timeframe,
            "progress": {
                "collected": state.total_collected,
                "requested": state.total_requested,
                "percentage": round(progress_percentage, 1)
            },
            "chunks": {
                "completed": completed_chunks,
                "estimated_total": state.estimated_total_chunks,
                "current": state.current_chunk.chunk_id if state.current_chunk else None
            },
            "timing": {
                "elapsed_seconds": elapsed_time.total_seconds(),
                "estimated_total_seconds": (
                    state.estimated_completion_time - state.start_time
                    if state.estimated_completion_time else None
                ),
                "estimated_remaining_seconds": state.estimated_remaining_seconds,
                "avg_chunk_duration": state.avg_chunk_duration,
                "remaining_chunks": state.remaining_chunks
            },
            "is_completed": state.is_completed,
            "error": state.error_message
        }

    def resume_collection(self, request_id: str) -> Optional[ChunkInfo]:
        """
        중단된 수집 재개

        Args:
            request_id: 수집 요청 ID

        Returns:
            ChunkInfo: 재개할 청크 정보
        """
        if request_id not in self.active_collections:
            raise ValueError(f"알 수 없는 요청 ID: {request_id}")

        state = self.active_collections[request_id]

        if state.is_completed:
            logger.info(f"이미 완료된 수집: {request_id}")
            return None

        if state.current_chunk is not None:
            logger.info(f"수집 재개: {request_id}, 현재 청크: {state.current_chunk.chunk_id}")
            return state.current_chunk

        # 현재 청크가 없으면 새로 생성 (마지막 상태 기준)
        next_chunk_index = len(state.completed_chunks)
        remaining_count = state.total_requested - state.total_collected

        if remaining_count <= 0:
            state.is_completed = True
            return None

        next_chunk_size = min(remaining_count, self.chunk_size)
        next_chunk_params = {
            "market": state.symbol,
            "count": next_chunk_size,
            "to": state.last_candle_time
        }

        next_chunk = self._create_next_chunk(
            collection_state=state,
            chunk_params=next_chunk_params,
            chunk_index=next_chunk_index
        )
        state.current_chunk = next_chunk

        logger.info(f"수집 재개: 새 청크 생성 {next_chunk.chunk_id}")
        return next_chunk

    def _calculate_total_count(
        self,
        count: Optional[int],
        to: Optional[datetime],
        end: Optional[datetime],
        timeframe: str,
        current_time: datetime
    ) -> int:
        """총 캔들 개수 계산 (최소 정규화)"""

        # count가 직접 제공된 경우
        if count is not None:
            return count

        # end가 제공된 경우: 기간 계산
        if end is not None:
            start_time = to if to is not None else current_time
            normalized_start = TimeUtils.align_to_candle_boundary(start_time, timeframe)
            normalized_end = TimeUtils.align_to_candle_boundary(end, timeframe)

            if normalized_start <= normalized_end:
                raise ValueError("시작 시점이 종료 시점보다 이전입니다")

            return TimeUtils.calculate_expected_count(
                start_time=normalized_start,
                end_time=normalized_end,
                timeframe=timeframe
            )

        raise ValueError("count 또는 end 중 하나는 반드시 제공되어야 합니다")

    def _create_first_chunk_params(
        self,
        symbol: str,
        count: Optional[int],
        to: Optional[datetime],
        end: Optional[datetime],
        current_time: datetime
    ) -> Dict[str, Any]:
        """첫 번째 청크 파라미터 생성"""

        params = {"market": symbol}

        # count 기반 요청 (가장 단순)
        if count is not None:
            chunk_size = min(count, self.chunk_size)
            params["count"] = chunk_size

            # to가 있으면 시작점 지정
            if to is not None:
                params["to"] = to.strftime("%Y-%m-%dT%H:%M:%S")
            # to가 없으면 현재 시간 기준 (count only)

        # end 기반 요청
        elif end is not None:
            params["count"] = self.chunk_size

            # to가 있으면 시작점 지정
            if to is not None:
                params["to"] = to.strftime("%Y-%m-%dT%H:%M:%S")
            # to가 없으면 현재 시간 기준 (end only)

        return params

    def _create_next_chunk(
        self,
        collection_state: CollectionState,
        chunk_params: Dict[str, Any],
        chunk_index: int
    ) -> ChunkInfo:
        """다음 청크 정보 생성"""

        chunk_id = f"{collection_state.symbol}_{collection_state.timeframe}_{chunk_index:05d}"

        # chunk_params에서 실제 'to' 값 추출 (문자열 → datetime 변환)
        current_time = datetime.now(timezone.utc)

        # 'to' 파라미터가 있으면 datetime으로 변환, 없으면 현재 시간 사용
        if "to" in chunk_params and chunk_params["to"]:
            try:
                # ISO 형식 문자열을 datetime으로 변환
                to_str = chunk_params["to"]
                if isinstance(to_str, str):
                    # ISO format 처리 (업비트 API는 'YYYY-MM-DDTHH:MM:SS' 형식)
                    to_datetime = datetime.fromisoformat(to_str.replace('Z', '+00:00'))
                else:
                    to_datetime = current_time
            except (ValueError, TypeError):
                logger.warning(f"'to' 파라미터 파싱 실패: {chunk_params.get('to')}, 현재 시간 사용")
                to_datetime = current_time
        else:
            to_datetime = current_time

        chunk_info = ChunkInfo(
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            symbol=collection_state.symbol,
            timeframe=collection_state.timeframe,
            count=chunk_params["count"],
            to=to_datetime,  # 실제 chunk_params의 'to' 값 사용
            end=current_time,  # end는 추후 API 응답 후 업데이트
            status="pending"
        )

        return chunk_info

    def _update_remaining_time_estimates(self, state: CollectionState):
        """
        실시간 남은 시간 추정 업데이트

        Args:
            state: 수집 상태 객체
        """
        current_time = datetime.now(timezone.utc)

        # 완료된 청크 수
        completed_chunks_count = len(state.completed_chunks)

        if completed_chunks_count == 0:
            # 아직 완료된 청크가 없으면 초기 추정값 사용
            return

        # 평균 청크 처리 시간 계산
        total_elapsed = (current_time - state.start_time).total_seconds()
        state.avg_chunk_duration = total_elapsed / completed_chunks_count

        # 남은 청크 수 계산
        state.remaining_chunks = state.estimated_total_chunks - completed_chunks_count

        # 실시간 남은 시간 추정
        if state.remaining_chunks > 0:
            state.estimated_remaining_seconds = state.remaining_chunks * state.avg_chunk_duration
        else:
            state.estimated_remaining_seconds = 0.0

        # 예상 완료 시간 업데이트
        if state.estimated_remaining_seconds > 0:
            state.estimated_completion_time = current_time + timedelta(
                seconds=state.estimated_remaining_seconds
            )

        # 업데이트 시간 기록
        state.last_update_time = current_time

        logger.debug(f"남은 시간 업데이트: 평균 청크 시간 {state.avg_chunk_duration:.2f}초, "
                     f"남은 청크 {state.remaining_chunks}개, 예상 남은 시간 {state.estimated_remaining_seconds:.1f}초")

    def get_realtime_remaining_time(self, request_id: str) -> Dict[str, Any]:
        """
        실시간 남은 시간 정보 조회

        Args:
            request_id: 수집 요청 ID

        Returns:
            Dict: 실시간 남은 시간 정보
        """
        if request_id not in self.active_collections:
            raise ValueError(f"알 수 없는 요청 ID: {request_id}")

        state = self.active_collections[request_id]
        current_time = datetime.now(timezone.utc)

        # 실시간 남은 시간 재계산 (최신 정보 반영)
        if len(state.completed_chunks) > 0:
            self._update_remaining_time_estimates(state)

        return {
            "request_id": request_id,
            "current_time": current_time.isoformat(),
            "avg_chunk_duration": state.avg_chunk_duration,
            "remaining_chunks": state.remaining_chunks,
            "estimated_remaining_seconds": state.estimated_remaining_seconds,
            "estimated_completion_time": (
                state.estimated_completion_time.isoformat()
                if state.estimated_completion_time else None
            ),
            "progress_percentage": round(
                (state.total_collected / state.total_requested) * 100, 1
            ),
            "is_on_track": self._is_collection_on_track(state),
            "performance_info": self._get_performance_info(state)
        }

    def _is_collection_on_track(self, state: CollectionState) -> bool:
        """
        수집이 예정대로 진행되고 있는지 확인

        Args:
            state: 수집 상태 객체

        Returns:
            bool: 예정대로 진행 중이면 True
        """
        if len(state.completed_chunks) == 0:
            return True  # 아직 시작 단계

        # 초기 예상 시간과 현재 평균 시간 비교
        initial_expected_duration = state.estimated_total_chunks / self.api_rate_limit_rps

        # 현재 평균이 초기 예상의 120% 이내면 정상
        return state.avg_chunk_duration <= initial_expected_duration * 1.2

    def _get_performance_info(self, state: CollectionState) -> Dict[str, Any]:
        """
        수집 성능 정보 제공

        Args:
            state: 수집 상태 객체

        Returns:
            Dict: 성능 정보
        """
        if len(state.completed_chunks) == 0:
            return {"status": "초기 단계"}

        initial_expected_rps = self.api_rate_limit_rps
        current_rps = 1.0 / state.avg_chunk_duration if state.avg_chunk_duration > 0 else 0

        return {
            "expected_rps": initial_expected_rps,
            "current_rps": round(current_rps, 2),
            "efficiency_percentage": round((current_rps / initial_expected_rps) * 100, 1),
            "avg_chunk_duration": state.avg_chunk_duration,
            "total_chunks_completed": len(state.completed_chunks)
        }

    def cleanup_completed_collections(self, max_age_hours: int = 24):
        """완료된 수집 상태 정리"""

        current_time = datetime.now(timezone.utc)
        cutoff_time = current_time - timedelta(hours=max_age_hours)

        completed_ids = []
        for request_id, state in self.active_collections.items():
            if state.is_completed and state.start_time < cutoff_time:
                completed_ids.append(request_id)

        for request_id in completed_ids:
            del self.active_collections[request_id]
            logger.debug(f"완료된 수집 상태 정리: {request_id}")

        if completed_ids:
            logger.info(f"수집 상태 정리 완료: {len(completed_ids)}개")

    def _calculate_chunk_end_time(self, chunk_info: ChunkInfo) -> datetime:
        """
        청크 요청의 예상 종료 시점 계산

        Args:
            chunk_info: 청크 정보

        Returns:
            datetime: 예상 종료 시점 (업비트 API 내림차순 기준)
        """
        # 업비트 API는 내림차순이므로 to 시점에서 count만큼 이전으로 계산
        timeframe_seconds = TimeUtils.get_timeframe_delta(chunk_info.timeframe).total_seconds()
        end_time = chunk_info.to - timedelta(seconds=(chunk_info.count - 1) * timeframe_seconds)

        logger.debug(f"청크 종료 시간 계산: {chunk_info.to} → {end_time} (내림차순 {chunk_info.count}개)")
        return end_time

    async def _collect_data_by_overlap_strategy(
        self,
        chunk_info: ChunkInfo,
        overlap_result
    ) -> tuple[list, bool]:
        """
        겹침 분석 결과에 따른 최적화된 데이터 수집

        Args:
            chunk_info: 청크 정보
            overlap_result: OverlapAnalyzer 분석 결과

        Returns:
            tuple[list, bool]: (수집된 캔들 데이터 리스트, API 호출 여부)
        """
        from upbit_auto_trading.infrastructure.market_data.candle.candle_models import OverlapStatus

        status = overlap_result.status

        if status == OverlapStatus.COMPLETE_OVERLAP:
            # 완전 겹침: DB에서만 데이터 가져오기
            logger.debug("완전 겹침 감지 → DB에서 데이터 조회")
            db_candles = await self.repository.get_candles_by_range(
                chunk_info.symbol,
                chunk_info.timeframe,
                overlap_result.db_start,
                overlap_result.db_end
            )
            return db_candles, False  # API 호출 없음

        elif status == OverlapStatus.NO_OVERLAP:
            # 겹침 없음: API에서만 데이터 가져오기
            logger.debug("겹침 없음 → 전체 API 요청")
            api_response = await self._fetch_chunk_from_api(chunk_info)
            candle_data_list = self._convert_upbit_response_to_candles(
                api_response, chunk_info.timeframe
            )
            return candle_data_list, True

        elif status in [OverlapStatus.PARTIAL_START, OverlapStatus.PARTIAL_MIDDLE_CONTINUOUS]:
            # 부분 겹침: DB + API 혼합 처리
            logger.debug(f"부분 겹침 ({status.value}) → DB + API 혼합 처리")

            # DB 데이터 수집
            db_candles = []
            if overlap_result.db_start and overlap_result.db_end:
                db_candles = await self.repository.get_candles_by_range(
                    chunk_info.symbol,
                    chunk_info.timeframe,
                    overlap_result.db_start,
                    overlap_result.db_end
                )

            # API 데이터 수집
            api_candles = []
            if overlap_result.api_start and overlap_result.api_end:
                # 임시 청크 정보로 API 호출
                api_chunk = ChunkInfo(
                    chunk_id=f"{chunk_info.chunk_id}_api_partial",
                    chunk_index=chunk_info.chunk_index,
                    symbol=chunk_info.symbol,
                    timeframe=chunk_info.timeframe,
                    count=self._calculate_api_count(overlap_result.api_start, overlap_result.api_end, chunk_info.timeframe),
                    to=overlap_result.api_start,
                    end=overlap_result.api_end,
                    status="pending"
                )

                api_response = await self._fetch_chunk_from_api(api_chunk)
                api_candles = self._convert_upbit_response_to_candles(
                    api_response, chunk_info.timeframe
                )

            # 시간순으로 병합 (업비트 내림차순 기준)
            combined_candles = self._merge_candles_by_time(db_candles, api_candles)
            return combined_candles, True

        else:
            # PARTIAL_MIDDLE_FRAGMENT 또는 기타: 안전한 폴백 → 전체 API 요청
            logger.warning(f"복잡한 겹침 상태 ({status.value}) → API 폴백")
            api_response = await self._fetch_chunk_from_api(chunk_info)
            candle_data_list = self._convert_upbit_response_to_candles(
                api_response, chunk_info.timeframe
            )
            return candle_data_list, True

    def _ensure_utc_timezone(self, dt: datetime) -> datetime:
        """DateTime이 timezone을 가지지 않으면 UTC로 설정"""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    def _calculate_api_count(self, start_time: datetime, end_time: datetime, timeframe: str) -> int:
        """API 요청에 필요한 캔들 개수 계산 (업비트 내림차순 기준)"""
        timeframe_seconds = TimeUtils.get_timeframe_delta(timeframe).total_seconds()
        time_diff = (start_time - end_time).total_seconds()  # 내림차순이므로 start > end
        return max(1, int(time_diff / timeframe_seconds) + 1)

    def _merge_candles_by_time(self, db_candles: list, api_candles: list) -> list:
        """
        시간 기준으로 캔들 데이터 병합 (업비트 내림차순 정렬 유지)

        Args:
            db_candles: DB에서 가져온 캔들 데이터
            api_candles: API에서 가져온 캔들 데이터

        Returns:
            list: 시간순으로 정렬된 병합 캔들 데이터
        """
        # 모든 캔들을 합치고 중복 제거 후 시간순 정렬
        all_candles = db_candles + api_candles

        # candle_date_time_utc 기준으로 중복 제거 (딕셔너리 활용)
        unique_candles = {}
        for candle in all_candles:
            if hasattr(candle, 'candle_date_time_utc'):
                key = candle.candle_date_time_utc
            elif isinstance(candle, dict):
                key = candle.get('candle_date_time_utc')
            else:
                continue

            if key not in unique_candles:
                unique_candles[key] = candle

        # 업비트 내림차순 정렬 (최신 → 과거)
        sorted_candles = sorted(
            unique_candles.values(),
            key=lambda x: (
                x.candle_date_time_utc if hasattr(x, 'candle_date_time_utc')
                else x.get('candle_date_time_utc', '')
            ),
            reverse=True  # 내림차순
        )

        logger.debug(f"캔들 병합 완료: DB {len(db_candles)}개 + API {len(api_candles)}개 → 병합 {len(sorted_candles)}개")
        return sorted_candles
