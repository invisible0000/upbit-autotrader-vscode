"""
멀티소스 데이터 수집기

기존 시스템과 호환되는 차트뷰어 전용 데이터 수집 엔진입니다.
API + WebSocket 하이브리드 모드를 지원하며, 1개월 타임프레임까지 처리합니다.

주요 기능:
- 멀티소스 수집 (API + WebSocket, 1개월 포함)
- 데이터 검증 및 중복 제거
- 기존 시스템과 격리된 리소스 관리
- 실시간 데이터 동기화
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import time

from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class DataSourceConfig:
    """데이터 소스 설정"""
    source_type: str  # "api", "websocket", "hybrid"
    symbol: str
    timeframe: str
    api_client: Optional[Any] = None
    websocket_client: Optional[Any] = None
    hybrid_ratio: float = 0.8  # WebSocket 80%, API 20%


@dataclass
class CollectionResult:
    """수집 결과"""
    success: bool
    data: List[Dict[str, Any]]
    source: str
    error_message: str = ""
    collection_time_ms: float = 0.0


class MultiSourceDataCollector:
    """
    멀티소스 데이터 수집기

    기존 시스템과 격리된 차트뷰어 전용 데이터 수집 엔진입니다.
    API와 WebSocket을 조합하여 최적의 데이터를 수집합니다.
    """

    def __init__(self):
        self.logger = create_component_logger("MultiSourceDataCollector")

        # 수집 상태 관리 (기존 시스템과 격리)
        self._active_collections: Dict[str, DataSourceConfig] = {}
        self._collection_stats: Dict[str, Dict[str, Any]] = {}
        self._last_collection_times: Dict[str, float] = {}

        # 데이터 검증기
        self._validator = DataValidator()

        # 실행 상태
        self._is_running = False
        self._collection_tasks: List[asyncio.Task] = []

    async def start_collection(self, config: DataSourceConfig,
                               data_callback: Callable[[List[Dict[str, Any]]], None]) -> str:
        """
        데이터 수집 시작

        Args:
            config: 데이터 소스 설정
            data_callback: 수집된 데이터 콜백 함수

        Returns:
            collection_id: 수집 식별자
        """
        collection_id = f"{config.symbol}_{config.timeframe}_{config.source_type}"

        self.logger.info(
            f"데이터 수집 시작: {collection_id} "
            f"(소스: {config.source_type}, 1개월 지원)"
        )

        try:
            # 타임프레임 지원 확인 (1개월 포함)
            if not self._is_timeframe_supported(config.timeframe):
                raise ValueError(f"지원하지 않는 타임프레임: {config.timeframe}")

            # 데이터 소스 유효성 확인
            if not self._validate_data_sources(config):
                raise ValueError("유효하지 않은 데이터 소스 설정")

            # 수집 설정 등록
            self._active_collections[collection_id] = config
            self._collection_stats[collection_id] = {
                'total_collections': 0,
                'successful_collections': 0,
                'failed_collections': 0,
                'last_success_time': None,
                'last_error': None,
                'data_source_distribution': {
                    'api': 0,
                    'websocket': 0,
                    'hybrid': 0
                }
            }

            # 초기 히스토리 데이터 수집
            initial_result = await self._collect_initial_data(config)
            if initial_result.success and initial_result.data:
                data_callback(initial_result.data)
                self._update_collection_stats(collection_id, initial_result)

            # 실시간 수집 시작 (1개월 타임프레임은 API 전용)
            if config.source_type in ["websocket", "hybrid"] and config.timeframe not in ["1w", "1M"]:
                task = asyncio.create_task(
                    self._realtime_collection_loop(config, data_callback)
                )
                self._collection_tasks.append(task)

            self.logger.info(f"데이터 수집 시작 완료: {collection_id}")
            return collection_id

        except Exception as e:
            self.logger.error(f"데이터 수집 시작 실패: {collection_id} - {e}")
            raise

    async def _collect_initial_data(self, config: DataSourceConfig) -> CollectionResult:
        """초기 히스토리 데이터 수집"""
        start_time = time.time()
        collection_source = "api"  # 초기 데이터는 항상 API 사용

        self.logger.debug(f"초기 데이터 수집: {config.symbol} {config.timeframe}")

        try:
            if not config.api_client:
                return CollectionResult(
                    success=False,
                    data=[],
                    source=collection_source,
                    error_message="API 클라이언트가 없습니다"
                )

            # 1개월 타임프레임 처리
            if config.timeframe in ["1w", "1M"]:
                # 1개월의 경우 충분한 일봉 데이터 수집 후 변환
                if config.timeframe == "1M":
                    count = 35  # 1개월 + 여유분
                    source_timeframe = "1d"
                elif config.timeframe == "1w":
                    count = 10  # 1주 + 여유분
                    source_timeframe = "1d"
                else:
                    count = 200
                    source_timeframe = config.timeframe
            else:
                count = 200
                source_timeframe = config.timeframe

            # API에서 데이터 수집
            raw_data = await self._collect_from_api(
                config.api_client, config.symbol, source_timeframe, count
            )

            # 타임프레임 변환 (필요한 경우)
            if config.timeframe in ["1w", "1M"] and source_timeframe != config.timeframe:
                converted_data = self._convert_timeframe_data(
                    raw_data, source_timeframe, config.timeframe
                )
                validated_data = self._validator.validate_and_clean(converted_data)
            else:
                validated_data = self._validator.validate_and_clean(raw_data)

            collection_time = (time.time() - start_time) * 1000

            return CollectionResult(
                success=True,
                data=validated_data,
                source=collection_source,
                collection_time_ms=collection_time
            )

        except Exception as e:
            collection_time = (time.time() - start_time) * 1000
            error_msg = f"초기 데이터 수집 실패: {e}"
            self.logger.error(error_msg)

            return CollectionResult(
                success=False,
                data=[],
                source=collection_source,
                error_message=error_msg,
                collection_time_ms=collection_time
            )

    async def _collect_from_api(self, api_client: Any, symbol: str,
                               timeframe: str, count: int) -> List[Dict[str, Any]]:
        """API에서 데이터 수집"""
        try:
            # API 클라이언트의 get_candles 메서드 호출
            # (실제 구현은 API 클라이언트에 따라 달라집니다)
            data = await api_client.get_candles(
                symbol=symbol,
                timeframe=timeframe,
                count=count
            )

            self.logger.debug(f"API 데이터 수집 성공: {len(data)}개 캔들")
            return data if data else []

        except Exception as e:
            self.logger.error(f"API 데이터 수집 실패: {e}")
            return []

    def _convert_timeframe_data(self, data: List[Dict[str, Any]],
                               source_tf: str, target_tf: str) -> List[Dict[str, Any]]:
        """타임프레임 변환 (일봉 → 주봉/월봉)"""
        if not data:
            return []

        self.logger.debug(f"타임프레임 변환: {source_tf} → {target_tf}")

        try:
            if target_tf == "1w":
                return self._convert_to_weekly(data)
            elif target_tf == "1M":
                return self._convert_to_monthly(data)
            else:
                return data

        except Exception as e:
            self.logger.error(f"타임프레임 변환 실패: {e}")
            return data

    def _convert_to_weekly(self, daily_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """일봉 → 주봉 변환"""
        if not daily_data:
            return []

        weekly_data = []

        # 날짜별로 정렬
        sorted_data = sorted(daily_data, key=lambda x: x.get('timestamp', 0))

        # 주별로 그룹화 (월요일 기준)
        week_groups = {}
        for candle in sorted_data:
            timestamp = candle.get('timestamp', 0)
            dt = datetime.fromtimestamp(timestamp)

            # 해당 주의 월요일 계산
            days_since_monday = dt.weekday()
            monday = dt - timedelta(days=days_since_monday)
            week_key = monday.strftime('%Y-%m-%d')

            if week_key not in week_groups:
                week_groups[week_key] = []
            week_groups[week_key].append(candle)

        # 각 주별로 OHLCV 합성
        for week_key in sorted(week_groups.keys()):
            week_candles = week_groups[week_key]
            merged_candle = self._merge_candles(week_candles)
            if merged_candle:
                weekly_data.append(merged_candle)

        return weekly_data

    def _convert_to_monthly(self, daily_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """일봉 → 월봉 변환 (1개월 타임프레임)"""
        if not daily_data:
            return []

        monthly_data = []

        # 날짜별로 정렬
        sorted_data = sorted(daily_data, key=lambda x: x.get('timestamp', 0))

        # 월별로 그룹화
        month_groups = {}
        for candle in sorted_data:
            timestamp = candle.get('timestamp', 0)
            month_key = datetime.fromtimestamp(timestamp).strftime('%Y-%m')

            if month_key not in month_groups:
                month_groups[month_key] = []
            month_groups[month_key].append(candle)

        # 각 월별로 OHLCV 합성
        for month_key in sorted(month_groups.keys()):
            month_candles = month_groups[month_key]
            merged_candle = self._merge_candles(month_candles)
            if merged_candle:
                monthly_data.append(merged_candle)

        return monthly_data

    def _merge_candles(self, candles: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """캔들 데이터 병합 (OHLCV)"""
        if not candles:
            return None

        try:
            # 시간순 정렬
            sorted_candles = sorted(candles, key=lambda x: x.get('timestamp', 0))

            first_candle = sorted_candles[0]
            last_candle = sorted_candles[-1]

            # OHLCV 계산
            open_price = first_candle.get('open', 0)
            close_price = last_candle.get('close', 0)
            high_price = max(candle.get('high', 0) for candle in sorted_candles)
            low_price = min(candle.get('low', float('inf')) for candle in sorted_candles)
            volume = sum(candle.get('volume', 0) for candle in sorted_candles)

            return {
                'timestamp': first_candle.get('timestamp'),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume,
                'datetime': first_candle.get('datetime', ''),
                'market': first_candle.get('market', ''),
            }

        except Exception as e:
            self.logger.error(f"캔들 병합 실패: {e}")
            return None

    async def _realtime_collection_loop(self, config: DataSourceConfig,
                                      data_callback: Callable[[List[Dict[str, Any]]], None]) -> None:
        """실시간 데이터 수집 루프"""
        collection_id = f"{config.symbol}_{config.timeframe}_{config.source_type}"

        self.logger.debug(f"실시간 수집 루프 시작: {collection_id}")

        try:
            last_hybrid_api_time = 0
            hybrid_interval = 5.0  # 5초마다 API 호출 (하이브리드 모드)

            while collection_id in self._active_collections:
                start_time = time.time()

                try:
                    # 하이브리드 모드 처리
                    if config.source_type == "hybrid":
                        current_time = time.time()
                        use_api = (current_time - last_hybrid_api_time) >= hybrid_interval

                        if use_api:
                            # API에서 최신 데이터 수집
                            result = await self._collect_from_api(
                                config.api_client, config.symbol, config.timeframe, 1
                            )
                            last_hybrid_api_time = current_time
                            source = "api"
                        else:
                            # WebSocket에서 실시간 데이터 수집
                            result = await self._collect_from_websocket(config)
                            source = "websocket"

                    elif config.source_type == "websocket":
                        # WebSocket 전용
                        result = await self._collect_from_websocket(config)
                        source = "websocket"

                    else:
                        # API 전용
                        result = await self._collect_from_api(
                            config.api_client, config.symbol, config.timeframe, 1
                        )
                        source = "api"

                    # 데이터 검증 및 콜백 호출
                    if result:
                        validated_data = self._validator.validate_and_clean(result)
                        if validated_data:
                            data_callback(validated_data)

                            # 통계 업데이트
                            collection_result = CollectionResult(
                                success=True,
                                data=validated_data,
                                source=source,
                                collection_time_ms=(time.time() - start_time) * 1000
                            )
                            self._update_collection_stats(collection_id, collection_result)

                except Exception as e:
                    self.logger.error(f"실시간 수집 오류: {collection_id} - {e}")

                    # 에러 통계 업데이트
                    error_result = CollectionResult(
                        success=False,
                        data=[],
                        source="unknown",
                        error_message=str(e),
                        collection_time_ms=(time.time() - start_time) * 1000
                    )
                    self._update_collection_stats(collection_id, error_result)

                # 수집 간격 (타임프레임에 따라 조정)
                if config.timeframe in ["1m", "3m", "5m"]:
                    await asyncio.sleep(1.0)  # 1초 간격
                else:
                    await asyncio.sleep(5.0)  # 5초 간격

        except asyncio.CancelledError:
            self.logger.debug(f"실시간 수집 루프 취소: {collection_id}")
        except Exception as e:
            self.logger.error(f"실시간 수집 루프 치명적 오류: {collection_id} - {e}")

    async def _collect_from_websocket(self, config: DataSourceConfig) -> List[Dict[str, Any]]:
        """WebSocket에서 실시간 데이터 수집"""
        try:
            if not config.websocket_client:
                return []

            # WebSocket 클라이언트에서 최신 데이터 가져오기
            # (실제 구현은 WebSocket 클라이언트에 따라 달라집니다)
            # 예시: ticker 데이터를 캔들 형태로 변환

            # 임시 구현 (실제로는 WebSocket 이벤트 기반)
            return []

        except Exception as e:
            self.logger.error(f"WebSocket 데이터 수집 실패: {e}")
            return []

    def _is_timeframe_supported(self, timeframe: str) -> bool:
        """타임프레임 지원 여부 확인 (1개월 포함)"""
        supported = ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]
        return timeframe in supported

    def _validate_data_sources(self, config: DataSourceConfig) -> bool:
        """데이터 소스 유효성 확인"""
        if config.source_type == "api":
            return config.api_client is not None
        elif config.source_type == "websocket":
            return config.websocket_client is not None
        elif config.source_type == "hybrid":
            return (config.api_client is not None and
                   config.websocket_client is not None)
        else:
            return False

    def _update_collection_stats(self, collection_id: str, result: CollectionResult) -> None:
        """수집 통계 업데이트"""
        if collection_id not in self._collection_stats:
            return

        stats = self._collection_stats[collection_id]
        stats['total_collections'] += 1

        if result.success:
            stats['successful_collections'] += 1
            stats['last_success_time'] = datetime.now()
        else:
            stats['failed_collections'] += 1
            stats['last_error'] = result.error_message

        # 데이터 소스별 통계
        if result.source in stats['data_source_distribution']:
            stats['data_source_distribution'][result.source] += 1

    async def stop_collection(self, collection_id: str) -> bool:
        """데이터 수집 중지"""
        if collection_id not in self._active_collections:
            self.logger.warning(f"수집을 찾을 수 없습니다: {collection_id}")
            return False

        # 수집 설정 제거
        del self._active_collections[collection_id]

        # 관련 태스크 취소
        remaining_tasks = []
        for task in self._collection_tasks:
            if not task.done():
                task.cancel()
            else:
                remaining_tasks.append(task)
        self._collection_tasks = remaining_tasks

        self.logger.info(f"데이터 수집 중지: {collection_id}")
        return True

    def get_collection_stats(self) -> Dict[str, Any]:
        """수집 통계 조회"""
        return {
            'active_collections': len(self._active_collections),
            'collection_tasks': len(self._collection_tasks),
            'is_running': self._is_running,
            'stats_by_collection': self._collection_stats.copy()
        }

    async def cleanup(self) -> None:
        """리소스 정리"""
        self.logger.info("멀티소스 데이터 수집기 정리 중...")

        self._is_running = False

        # 모든 수집 태스크 취소
        for task in self._collection_tasks:
            task.cancel()

        if self._collection_tasks:
            await asyncio.gather(*self._collection_tasks, return_exceptions=True)

        # 상태 정리
        self._active_collections.clear()
        self._collection_stats.clear()
        self._last_collection_times.clear()
        self._collection_tasks.clear()

        self.logger.info("멀티소스 데이터 수집기 정리 완료")


class DataValidator:
    """데이터 검증 및 정리"""

    def __init__(self):
        self.logger = create_component_logger("DataValidator")

    def validate_and_clean(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """데이터 검증 및 정리"""
        if not data:
            return []

        validated = []
        duplicate_count = 0
        invalid_count = 0

        seen_timestamps = set()

        for item in data:
            # 유효성 검사
            if not self._is_valid_candle(item):
                invalid_count += 1
                continue

            # 중복 제거
            timestamp = item.get('timestamp')
            if timestamp in seen_timestamps:
                duplicate_count += 1
                continue

            seen_timestamps.add(timestamp)
            validated.append(self._normalize_candle(item))

        # 시간순 정렬
        validated.sort(key=lambda x: x.get('timestamp', 0))

        if duplicate_count > 0 or invalid_count > 0:
            self.logger.debug(
                f"데이터 정리 완료: "
                f"원본 {len(data)}개 → 유효 {len(validated)}개 "
                f"(중복 제거: {duplicate_count}, 무효: {invalid_count})"
            )

        return validated

    def _is_valid_candle(self, candle: Dict[str, Any]) -> bool:
        """캔들 데이터 유효성 검사"""
        required_fields = ['open', 'high', 'low', 'close', 'volume', 'timestamp']

        # 필수 필드 확인
        for field in required_fields:
            if field not in candle:
                return False

            value = candle[field]
            if value is None:
                return False

            # 숫자 필드 검증
            if field != 'timestamp':
                try:
                    float_value = float(value)
                    if float_value < 0:
                        return False
                except (ValueError, TypeError):
                    return False

        # OHLC 논리 확인
        try:
            o, h, l, c = (float(candle[f]) for f in ['open', 'high', 'low', 'close'])
            if not (l <= o <= h and l <= c <= h):
                return False
        except (ValueError, TypeError):
            return False

        return True

    def _normalize_candle(self, candle: Dict[str, Any]) -> Dict[str, Any]:
        """캔들 데이터 정규화"""
        try:
            return {
                'timestamp': int(candle.get('timestamp', 0)),
                'open': float(candle.get('open', 0)),
                'high': float(candle.get('high', 0)),
                'low': float(candle.get('low', 0)),
                'close': float(candle.get('close', 0)),
                'volume': float(candle.get('volume', 0)),
                'datetime': str(candle.get('datetime', '')),
                'market': str(candle.get('market', '')),
            }
        except (ValueError, TypeError) as e:
            self.logger.warning(f"캔들 정규화 실패: {e}")
            return candle
