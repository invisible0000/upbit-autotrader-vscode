"""
차트뷰어 마켓 데이터 수집 서비스

기존 InMemoryEventBus 시스템을 활용하여 차트뷰어 전용 데이터 수집 엔진을 구현합니다.
기존 시스템과 완전 격리되며, 1개월 타임프레임까지 지원합니다.

주요 기능:
- 멀티소스 데이터 수집 (API + WebSocket)
- 타임프레임 변환 (1분 → 1개월)
- 기존 DomainEvent 상속 이벤트 발행
- 기존 시스템과 격리된 우선순위 관리
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio

from upbit_auto_trading.application.services.base_application_service import BaseApplicationService
from upbit_auto_trading.domain.events.chart_viewer_events import (
    CandleDataEvent, ChartViewerPriority, TimeframeSupport,
    ChartSubscriptionEvent
)
from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class MarketDataRequest:
    """마켓 데이터 요청 DTO"""
    symbol: str
    timeframe: str
    count: int = 200
    data_source: str = "websocket"  # "websocket", "api", "hybrid"
    chart_id: str = ""
    priority_level: int = ChartViewerPriority.CHART_HIGH


class ChartMarketDataService(BaseApplicationService):
    """
    차트뷰어 마켓 데이터 수집 서비스

    기존 InMemoryEventBus와 호환되는 차트뷰어 전용 데이터 수집 엔진입니다.
    기존 매매 시스템에 영향을 주지 않으면서 1개월 타임프레임까지 지원합니다.
    """

    def __init__(self, event_bus=None, upbit_api_client=None, websocket_client=None):
        super().__init__()
        self.logger = create_component_logger("ChartMarketDataService")

        # 기존 시스템과 호환 (의존성 주입)
        self._event_bus = event_bus
        self._upbit_api_client = upbit_api_client
        self._websocket_client = websocket_client

        # 차트뷰어 전용 상태 관리
        self._active_subscriptions: Dict[str, MarketDataRequest] = {}
        self._data_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._conversion_cache: Dict[str, List[Dict[str, Any]]] = {}

        # 타임프레임 변환기
        self._timeframe_converter = TimeframeConverter()

        # 데이터 검증기
        self._data_validator = MarketDataValidator()

        # 기존 시스템과 격리된 리소스 관리
        self._is_running = False
        self._collection_tasks: List[asyncio.Task] = []

    async def collect_market_data(self, request: MarketDataRequest) -> None:
        """
        마켓 데이터 수집 시작 (기존 시스템과 격리)

        Args:
            request: 마켓 데이터 요청 정보
        """
        self.logger.info(
            f"마켓 데이터 수집 시작: {request.symbol} {request.timeframe} "
            f"(소스: {request.data_source}, 우선순위: {request.priority_level})"
        )

        try:
            # 타임프레임 지원 확인
            if not TimeframeSupport.is_timeframe_supported(request.timeframe):
                raise ValueError(f"지원하지 않는 타임프레임: {request.timeframe}")

            # 데이터 소스 결정 (1개월 타임프레임 처리)
            optimal_source = TimeframeSupport.get_data_source(request.timeframe)
            if optimal_source == "api" and request.data_source == "websocket":
                self.logger.warning(
                    f"타임프레임 {request.timeframe}은 API 전용입니다. "
                    f"데이터 소스를 {optimal_source}로 변경합니다."
                )
                request.data_source = optimal_source

            # 구독 등록 (기존 시스템과 격리)
            subscription_id = f"{request.chart_id}_{request.symbol}_{request.timeframe}"
            self._active_subscriptions[subscription_id] = request

            # 초기 히스토리 데이터 로딩
            await self._load_initial_data(request)

            # 실시간 데이터 수집 시작
            if request.data_source in ["websocket", "hybrid"]:
                await self._start_realtime_collection(request)

            # 구독 이벤트 발행 (기존 DomainEvent 상속)
            subscription_event = ChartSubscriptionEvent(
                chart_id=request.chart_id,
                symbol=request.symbol,
                timeframe=request.timeframe,
                subscription_type="subscribe",
                subscription_id=subscription_id,
                requested_count=request.count,
                priority_level=request.priority_level
            )

            if self._event_bus:
                await self._event_bus.publish(subscription_event)

            self.logger.info(f"마켓 데이터 수집 구독 완료: {subscription_id}")

        except Exception as e:
            self.logger.error(f"마켓 데이터 수집 실패: {request.symbol} - {e}")
            raise

    async def _load_initial_data(self, request: MarketDataRequest) -> None:
        """초기 히스토리 데이터 로딩"""
        self.logger.info(f"초기 데이터 로딩: {request.symbol} {request.timeframe}")

        try:
            # 캐시 키 생성
            cache_key = f"{request.symbol}_{request.timeframe}"

            # 타임프레임 변환이 필요한 경우
            if TimeframeSupport.is_conversion_required(request.timeframe):
                raw_data = await self._load_raw_data_for_conversion(request)
                converted_data = self._timeframe_converter.convert_timeframe(
                    raw_data, "1m", request.timeframe
                )
                self._data_cache[cache_key] = converted_data
                candle_data = converted_data[-request.count:] if converted_data else []
            else:
                # 직접 로딩
                candle_data = await self._load_direct_data(request)
                self._data_cache[cache_key] = candle_data

            # 데이터 검증
            validated_data = self._data_validator.validate_candle_data(candle_data)

            # 캔들 데이터 이벤트 발행 (기존 DomainEvent 상속)
            for candle in validated_data:
                candle_event = CandleDataEvent(
                    chart_id=request.chart_id,
                    symbol=request.symbol,
                    timeframe=request.timeframe,
                    candle_data=candle,
                    is_realtime=False,
                    data_source=request.data_source,
                    priority_level=request.priority_level
                )

                if self._event_bus:
                    await self._event_bus.publish(candle_event)

            self.logger.info(
                f"초기 데이터 로딩 완료: {len(validated_data)}개 캔들 "
                f"({request.symbol} {request.timeframe})"
            )

        except Exception as e:
            self.logger.error(f"초기 데이터 로딩 실패: {request.symbol} - {e}")
            raise

    async def _load_raw_data_for_conversion(self, request: MarketDataRequest) -> List[Dict[str, Any]]:
        """변환용 원시 데이터 로딩 (1분 데이터)"""
        # 1개월 타임프레임의 경우 충분한 1분 데이터 필요
        if request.timeframe == "1M":
            days_needed = 35  # 1개월 + 여유분
        elif request.timeframe == "1w":
            days_needed = 10  # 1주 + 여유분
        elif request.timeframe == "1d":
            days_needed = 3   # 1일 + 여유분
        else:
            days_needed = 1   # 기본 1일

        required_count = days_needed * 24 * 60  # 1분 단위 개수

        # API에서 1분 데이터 로딩
        if self._upbit_api_client:
            try:
                raw_data = await self._upbit_api_client.get_candles(
                    symbol=request.symbol,
                    timeframe="1m",
                    count=min(required_count, 1440)  # Upbit API 제한
                )
                self.logger.debug(f"변환용 1분 데이터 로딩: {len(raw_data)}개")
                return raw_data
            except Exception as e:
                self.logger.error(f"변환용 데이터 로딩 실패: {e}")
                return []

        return []

    async def _load_direct_data(self, request: MarketDataRequest) -> List[Dict[str, Any]]:
        """직접 데이터 로딩 (타임프레임 변환 불필요)"""
        if self._upbit_api_client:
            try:
                data = await self._upbit_api_client.get_candles(
                    symbol=request.symbol,
                    timeframe=request.timeframe,
                    count=request.count
                )
                self.logger.debug(f"직접 데이터 로딩: {len(data)}개")
                return data
            except Exception as e:
                self.logger.error(f"직접 데이터 로딩 실패: {e}")
                return []

        return []

    async def _start_realtime_collection(self, request: MarketDataRequest) -> None:
        """실시간 데이터 수집 시작"""
        self.logger.info(f"실시간 수집 시작: {request.symbol} {request.timeframe}")

        if not self._websocket_client:
            self.logger.warning("WebSocket 클라이언트가 없어 실시간 수집을 건너뜁니다.")
            return

        try:
            # 실시간 수집 태스크 생성 (기존 시스템과 격리)
            task = asyncio.create_task(
                self._realtime_collection_loop(request)
            )
            self._collection_tasks.append(task)

        except Exception as e:
            self.logger.error(f"실시간 수집 시작 실패: {e}")

    async def _realtime_collection_loop(self, request: MarketDataRequest) -> None:
        """실시간 데이터 수집 루프 (기존 시스템과 격리)"""
        subscription_id = f"{request.chart_id}_{request.symbol}_{request.timeframe}"

        self.logger.debug(f"실시간 수집 루프 시작: {subscription_id}")

        try:
            while subscription_id in self._active_subscriptions:
                # WebSocket에서 실시간 데이터 수신
                # (실제 구현은 WebSocket 클라이언트에 따라 달라집니다)

                # 예시: 1초마다 체크 (실제로는 WebSocket 이벤트 기반)
                await asyncio.sleep(1.0)

                # 실시간 캔들 업데이트 이벤트 발행 (기존 시스템과 격리)
                # 실제 데이터는 WebSocket에서 수신된 데이터를 사용

        except asyncio.CancelledError:
            self.logger.debug(f"실시간 수집 루프 취소: {subscription_id}")
        except Exception as e:
            self.logger.error(f"실시간 수집 루프 오류: {subscription_id} - {e}")

    async def unsubscribe_market_data(self, chart_id: str, symbol: str, timeframe: str) -> None:
        """마켓 데이터 구독 해제 (기존 시스템과 격리)"""
        subscription_id = f"{chart_id}_{symbol}_{timeframe}"

        if subscription_id in self._active_subscriptions:
            # 구독 제거
            del self._active_subscriptions[subscription_id]

            # 캐시 정리
            cache_key = f"{symbol}_{timeframe}"
            if cache_key in self._data_cache:
                del self._data_cache[cache_key]

            # 구독 해제 이벤트 발행
            unsubscribe_event = ChartSubscriptionEvent(
                chart_id=chart_id,
                symbol=symbol,
                timeframe=timeframe,
                subscription_type="unsubscribe",
                subscription_id=subscription_id
            )

            if self._event_bus:
                await self._event_bus.publish(unsubscribe_event)

            self.logger.info(f"마켓 데이터 구독 해제: {subscription_id}")
        else:
            self.logger.warning(f"구독을 찾을 수 없습니다: {subscription_id}")

    def get_subscription_status(self) -> Dict[str, Any]:
        """구독 상태 조회 (기존 시스템과 격리)"""
        return {
            "active_subscriptions": len(self._active_subscriptions),
            "cache_entries": len(self._data_cache),
            "collection_tasks": len(self._collection_tasks),
            "is_running": self._is_running,
            "subscriptions": list(self._active_subscriptions.keys())
        }

    async def cleanup(self) -> None:
        """리소스 정리 (기존 시스템과 격리)"""
        self.logger.info("차트 마켓 데이터 서비스 정리 중...")

        self._is_running = False

        # 모든 수집 태스크 취소
        for task in self._collection_tasks:
            task.cancel()

        if self._collection_tasks:
            await asyncio.gather(*self._collection_tasks, return_exceptions=True)

        # 캐시 정리
        self._active_subscriptions.clear()
        self._data_cache.clear()
        self._conversion_cache.clear()
        self._collection_tasks.clear()

        self.logger.info("차트 마켓 데이터 서비스 정리 완료")


class TimeframeConverter:
    """타임프레임 변환기 (1분 → 1개월)"""

    def __init__(self):
        self.logger = create_component_logger("TimeframeConverter")

    def convert_timeframe(self, minute_data: List[Dict[str, Any]],
                         source_tf: str, target_tf: str) -> List[Dict[str, Any]]:
        """
        타임프레임 변환 (1분 → 목표 타임프레임)

        Args:
            minute_data: 1분 캔들 데이터
            source_tf: 소스 타임프레임 (현재는 "1m"만 지원)
            target_tf: 목표 타임프레임

        Returns:
            변환된 캔들 데이터
        """
        if source_tf != "1m":
            raise ValueError("현재는 1분 데이터에서만 변환이 지원됩니다.")

        if not minute_data:
            return []

        try:
            # 타임프레임별 변환 로직
            if target_tf == "3m":
                return self._convert_to_minutes(minute_data, 3)
            elif target_tf == "5m":
                return self._convert_to_minutes(minute_data, 5)
            elif target_tf == "15m":
                return self._convert_to_minutes(minute_data, 15)
            elif target_tf == "30m":
                return self._convert_to_minutes(minute_data, 30)
            elif target_tf == "1h":
                return self._convert_to_minutes(minute_data, 60)
            elif target_tf == "4h":
                return self._convert_to_minutes(minute_data, 240)
            elif target_tf == "1d":
                return self._convert_to_daily(minute_data)
            elif target_tf == "1w":
                return self._convert_to_weekly(minute_data)
            elif target_tf == "1M":
                return self._convert_to_monthly(minute_data)
            else:
                raise ValueError(f"지원하지 않는 타임프레임 변환: {target_tf}")

        except Exception as e:
            self.logger.error(f"타임프레임 변환 실패: {source_tf} → {target_tf} - {e}")
            return []

    def _convert_to_minutes(self, data: List[Dict[str, Any]], minutes: int) -> List[Dict[str, Any]]:
        """분 단위 타임프레임 변환"""
        if not data:
            return []

        result = []

        # 시간순 정렬 (오래된 것부터)
        sorted_data = sorted(data, key=lambda x: x.get('timestamp', 0))

        # 그룹화하여 변환
        current_group = []
        group_start_time = None

        for candle in sorted_data:
            timestamp = candle.get('timestamp', 0)
            candle_time = datetime.fromtimestamp(timestamp)

            # 그룹 시작 시간 계산 (분 단위로 정렬)
            aligned_minute = (candle_time.minute // minutes) * minutes
            aligned_time = candle_time.replace(minute=aligned_minute, second=0, microsecond=0)

            if group_start_time is None:
                group_start_time = aligned_time

            # 같은 그룹인지 확인
            if aligned_time == group_start_time:
                current_group.append(candle)
            else:
                # 이전 그룹 완료 처리
                if current_group:
                    converted_candle = self._merge_candles(current_group)
                    if converted_candle:
                        result.append(converted_candle)

                # 새 그룹 시작
                current_group = [candle]
                group_start_time = aligned_time

        # 마지막 그룹 처리
        if current_group:
            converted_candle = self._merge_candles(current_group)
            if converted_candle:
                result.append(converted_candle)

        return result

    def _convert_to_daily(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """일봉 변환"""
        if not data:
            return []

        result = []

        # 날짜별로 그룹화
        date_groups = {}
        for candle in data:
            timestamp = candle.get('timestamp', 0)
            date_key = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

            if date_key not in date_groups:
                date_groups[date_key] = []
            date_groups[date_key].append(candle)

        # 각 날짜별로 변환
        for date_key in sorted(date_groups.keys()):
            converted_candle = self._merge_candles(date_groups[date_key])
            if converted_candle:
                result.append(converted_candle)

        return result

    def _convert_to_weekly(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """주봉 변환"""
        if not data:
            return []

        result = []

        # 주별로 그룹화 (월요일 기준)
        week_groups = {}
        for candle in data:
            timestamp = candle.get('timestamp', 0)
            dt = datetime.fromtimestamp(timestamp)

            # 해당 주의 월요일 계산
            days_since_monday = dt.weekday()
            monday = dt - timedelta(days=days_since_monday)
            week_key = monday.strftime('%Y-%m-%d')

            if week_key not in week_groups:
                week_groups[week_key] = []
            week_groups[week_key].append(candle)

        # 각 주별로 변환
        for week_key in sorted(week_groups.keys()):
            converted_candle = self._merge_candles(week_groups[week_key])
            if converted_candle:
                result.append(converted_candle)

        return result

    def _convert_to_monthly(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """월봉 변환 (1개월 타임프레임)"""
        if not data:
            return []

        result = []

        # 월별로 그룹화
        month_groups = {}
        for candle in data:
            timestamp = candle.get('timestamp', 0)
            month_key = datetime.fromtimestamp(timestamp).strftime('%Y-%m')

            if month_key not in month_groups:
                month_groups[month_key] = []
            month_groups[month_key].append(candle)

        # 각 월별로 변환
        for month_key in sorted(month_groups.keys()):
            converted_candle = self._merge_candles(month_groups[month_key])
            if converted_candle:
                result.append(converted_candle)

        return result

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


class MarketDataValidator:
    """마켓 데이터 검증기"""

    def __init__(self):
        self.logger = create_component_logger("MarketDataValidator")

    def validate_candle_data(self, candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """캔들 데이터 검증 및 정리"""
        if not candles:
            return []

        validated = []

        for candle in candles:
            if self._is_valid_candle(candle):
                # 중복 제거를 위한 정규화
                normalized = self._normalize_candle(candle)
                if normalized not in validated:
                    validated.append(normalized)
            else:
                self.logger.warning(f"유효하지 않은 캔들 데이터: {candle}")

        # 시간순 정렬
        validated.sort(key=lambda x: x.get('timestamp', 0))

        self.logger.debug(f"데이터 검증 완료: {len(candles)} → {len(validated)}개")
        return validated

    def _is_valid_candle(self, candle: Dict[str, Any]) -> bool:
        """캔들 데이터 유효성 검사"""
        required_fields = ['open', 'high', 'low', 'close', 'volume', 'timestamp']

        # 필수 필드 확인
        for field in required_fields:
            if field not in candle:
                return False

            value = candle[field]
            if value is None or (isinstance(value, (int, float)) and value < 0):
                return False

        # OHLC 논리 확인
        o, h, l, c = candle['open'], candle['high'], candle['low'], candle['close']
        if not (l <= o <= h and l <= c <= h):
            return False

        return True

    def _normalize_candle(self, candle: Dict[str, Any]) -> Dict[str, Any]:
        """캔들 데이터 정규화"""
        return {
            'timestamp': candle.get('timestamp'),
            'open': float(candle.get('open', 0)),
            'high': float(candle.get('high', 0)),
            'low': float(candle.get('low', 0)),
            'close': float(candle.get('close', 0)),
            'volume': float(candle.get('volume', 0)),
            'datetime': candle.get('datetime', ''),
            'market': candle.get('market', ''),
        }
