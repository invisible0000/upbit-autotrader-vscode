"""
실시간 캔들 완성도 관리자
미완성 캔들은 메모리만, 완성된 캔들만 DB 저장
"""
from typing import Dict, Optional, List, NamedTuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("RealtimeCandleManager")


class ProcessResult(NamedTuple):
    """처리 결과"""
    action: str  # "SAVE_TO_DB" | "MEMORY_ONLY" | "UPDATE_TEMP"
    candle: 'CandleData'
    is_complete: bool


@dataclass
class CandleCompletionInfo:
    """캔들 완성 정보"""
    start_time: datetime
    end_time: datetime
    is_complete: bool
    last_update: datetime


class RealtimeCandleManager:
    """
    실시간 캔들 완성도 관리자

    핵심 원칙:
    1. 미완성 캔들은 메모리에서만 관리 (DB 저장 X)
    2. 완성된 캔들만 DB에 저장
    3. 트리거/전략에는 항상 최신 데이터 제공 (완성도 무관)
    4. 같은 타임프레임 내 중복 저장 방지
    """

    # 타임프레임별 초 단위 매핑
    TIMEFRAME_SECONDS = {
        '1m': 60,
        '3m': 180,
        '5m': 300,
        '15m': 900,
        '30m': 1800,
        '1h': 3600,
        '4h': 14400,
        '1d': 86400,
        '1w': 604800,
        '1M': 2628000  # 대략 30.4일
    }

    def __init__(self, temp_cache_ttl_minutes: int = 60):
        """
        Args:
            temp_cache_ttl_minutes: 임시 캔들 캐시 유지 시간 (분)
        """
        # 임시 캔들 저장소 (메모리만)
        self.temp_candles: Dict[str, 'CandleData'] = {}

        # 완성 정보 추적
        self.completion_info: Dict[str, CandleCompletionInfo] = {}

        # 설정
        self.temp_cache_ttl = timedelta(minutes=temp_cache_ttl_minutes)

        logger.info("실시간 캔들 관리자 초기화 완료")

    async def verify_candle_with_api(self, symbol: str, timeframe: str, candle_time: datetime) -> bool:
        """
        업비트 REST API로 캔들 완성 여부 직접 확인

        사용 사례:
        - 중요한 매매 신호 확인 시
        - 저거래량 심볼의 완성도 불확실 시
        - 시스템 시작 시 최신 완성 캔들 확인
        """
        try:
            import aiohttp

            # 타임프레임에 따른 API 엔드포인트 결정
            if timeframe == "1m":
                url = "https://api.upbit.com/v1/candles/minutes/1"
            elif timeframe == "5m":
                url = "https://api.upbit.com/v1/candles/minutes/5"
            elif timeframe == "15m":
                url = "https://api.upbit.com/v1/candles/minutes/15"
            elif timeframe == "1h":
                url = "https://api.upbit.com/v1/candles/minutes/60"
            elif timeframe == "1d":
                url = "https://api.upbit.com/v1/candles/days"
            else:
                logger.warning(f"API 검증 미지원 타임프레임: {timeframe}")
                return False

            params = {'market': symbol, 'count': 5}  # 최근 5개 캔들

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        candles = await response.json()

                        # 해당 시간의 캔들이 API에서 완성되어 조회되는지 확인
                        for api_candle in candles:
                            api_time = datetime.fromisoformat(
                                api_candle['candle_date_time_kst'].replace('T', ' ')
                            )
                            if api_time == candle_time:
                                logger.info(f"✅ REST API 완성 확인: {symbol} {timeframe} {candle_time}")
                                return True

                        logger.debug(f"⏳ REST API 미완성: {symbol} {timeframe} {candle_time}")
                        return False
                    else:
                        logger.warning(f"API 응답 오류: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"API 완성 확인 실패: {e}")
            return False

    def process_realtime_update(self, candle_data: Dict) -> ProcessResult:
        """
        실시간 캔들 업데이트 처리

        Returns:
            ProcessResult: 처리 방법과 캔들 데이터
        """
        try:
            # 캔들 시간 정보 추출
            symbol = candle_data.get('market', '')
            timeframe = self._extract_timeframe(candle_data)
            candle_time = self._parse_candle_time(candle_data)

            if not all([symbol, timeframe, candle_time]):
                logger.warning(f"캔들 정보 불완전: symbol={symbol}, timeframe={timeframe}, candle_time={candle_time}")
                return ProcessResult("ERROR", candle_data, False)

            # 타입 안전성 확보 (위에서 검증했지만 명시적 체크)
            assert timeframe is not None
            assert candle_time is not None

            # 캔들 키 생성
            candle_key = self._generate_candle_key(symbol, timeframe, candle_time)

            # 완성도 판단
            is_complete = self._is_candle_complete(candle_time, timeframe)

            # 완성 정보 업데이트
            self._update_completion_info(candle_key, candle_time, timeframe, is_complete)

            if is_complete:
                # 완성된 캔들 → DB 저장 대상
                if candle_key in self.temp_candles:
                    del self.temp_candles[candle_key]  # 임시 캔들 제거
                    logger.debug(f"임시 캔들 제거 후 DB 저장: {candle_key}")

                return ProcessResult("SAVE_TO_DB", candle_data, True)

            else:
                # 미완성 캔들 → 메모리만 업데이트
                self.temp_candles[candle_key] = candle_data
                logger.debug(f"임시 캔들 메모리 업데이트: {candle_key}")

                return ProcessResult("MEMORY_ONLY", candle_data, False)

        except Exception as e:
            logger.error(f"실시간 캔들 처리 오류: {e}")
            return ProcessResult("ERROR", candle_data, False)

    def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """
        최신 캔들 조회 (임시 캔들 우선)

        Returns:
            가장 최신의 캔들 (완성도 무관)
        """
        # 해당 심볼/타임프레임의 모든 임시 캔들 찾기
        matching_temp_candles = []
        for key, candle in self.temp_candles.items():
            if key.startswith(f"{symbol}_{timeframe}_"):
                matching_temp_candles.append(candle)

        if matching_temp_candles:
            # 가장 최근 시간의 임시 캔들 반환 (None 안전 처리)
            def get_candle_time(candle):
                parsed_time = self._parse_candle_time(candle)
                return parsed_time if parsed_time else datetime.min

            latest_temp = max(matching_temp_candles, key=get_candle_time)
            logger.debug(f"최신 임시 캔들 반환: {symbol} {timeframe}")
            return latest_temp

        logger.debug(f"임시 캔들 없음: {symbol} {timeframe}")
        return None

    def cleanup_expired_temp_candles(self) -> int:
        """만료된 임시 캔들 정리"""
        from zoneinfo import ZoneInfo

        current_time = datetime.now(ZoneInfo("Asia/Seoul")).replace(tzinfo=None)
        expired_keys = []

        for key, candle in self.temp_candles.items():
            candle_time = self._parse_candle_time(candle)
            if candle_time and current_time - candle_time > self.temp_cache_ttl:
                expired_keys.append(key)

        for key in expired_keys:
            del self.temp_candles[key]
            if key in self.completion_info:
                del self.completion_info[key]

        if expired_keys:
            logger.info(f"만료된 임시 캔들 {len(expired_keys)}개 정리 완료")

        return len(expired_keys)

    def get_stats(self) -> Dict[str, int]:
        """통계 정보"""
        return {
            'temp_candles_count': len(self.temp_candles),
            'completion_tracking_count': len(self.completion_info),
            'memory_usage_kb': len(str(self.temp_candles)) // 1024
        }

    # ==========================================
    # Private 메서드
    # ==========================================

    def _generate_candle_key(self, symbol: str, timeframe: str, candle_time: datetime) -> str:
        """캔들 키 생성"""
        return f"{symbol}_{timeframe}_{candle_time.strftime('%Y%m%d_%H%M%S')}"

    def _extract_timeframe(self, candle_data: Dict) -> Optional[str]:
        """캔들 데이터에서 타임프레임 추출"""
        # 업비트 API 응답에서 타임프레임 추출 로직
        # 실제 구현 시 API 스펙에 맞게 수정 필요
        return candle_data.get('unit', '1m')  # 기본값 1분

    def _parse_candle_time(self, candle_data: Dict) -> Optional[datetime]:
        """캔들 시간 파싱"""
        try:
            # KST 시간 우선 사용
            time_str = candle_data.get('candle_date_time_kst')
            if time_str:
                return datetime.fromisoformat(time_str.replace('T', ' '))

            # timestamp 사용
            timestamp = candle_data.get('timestamp')
            if timestamp:
                return datetime.fromtimestamp(timestamp / 1000)

            return None
        except Exception as e:
            logger.warning(f"캔들 시간 파싱 실패: {e}")
            return None

    def _is_candle_complete(self, candle_time: datetime, timeframe: str) -> bool:
        """캔들 완성 여부 판단 (업비트 REST API 기반 전략)"""
        from zoneinfo import ZoneInfo

        # KST 시간대로 현재 시간 조정
        current_time = datetime.now(ZoneInfo("Asia/Seoul")).replace(tzinfo=None)

        # 타임프레임별 캔들 지속 시간
        duration_seconds = self.TIMEFRAME_SECONDS.get(timeframe, 60)

        # 캔들 종료 시간 계산
        candle_end_time = candle_time + timedelta(seconds=duration_seconds)

        # 업비트 REST API 특성 기반 완성도 판단
        # 1. 기본 완성 조건: 캔들 종료 시간 경과
        basic_complete = current_time >= candle_end_time

        if not basic_complete:
            logger.debug(f"캔들 미완성 (기본): {candle_time} ~ {candle_end_time} vs {current_time}")
            return False

        # 2. 업비트 API 안전 마진 적용 (실제 검증 결과: 15초 완성 지연)
        # 메인 심볼: 15초 마진, 저거래량 심볼: 더 긴 마진 필요
        safety_margin_seconds = 30  # 안전 마진 30초

        time_since_completion = (current_time - candle_end_time).total_seconds()
        is_safe_complete = time_since_completion >= safety_margin_seconds

        if is_safe_complete:
            logger.debug(f"캔들 완성 확인 (API 안전): {candle_time}, 완성 후 {time_since_completion:.1f}초 경과")
        else:
            logger.debug(f"캔들 대기 중 (API 안전): {candle_time}, 완성 후 {time_since_completion:.1f}초 경과 (30초 대기)")

        return is_safe_complete

    def _update_completion_info(self, candle_key: str, candle_time: datetime,
                                timeframe: str, is_complete: bool) -> None:
        """완성 정보 업데이트"""
        duration_seconds = self.TIMEFRAME_SECONDS.get(timeframe, 60)
        end_time = candle_time + timedelta(seconds=duration_seconds)

        self.completion_info[candle_key] = CandleCompletionInfo(
            start_time=candle_time,
            end_time=end_time,
            is_complete=is_complete,
            last_update=datetime.now()
        )
