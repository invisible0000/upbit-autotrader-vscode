"""
적응형 TTL 관리자 (Adaptive TTL Manager)

시장 상황, 접근 패턴, 변동성을 종합 분석하여 동적으로 TTL을 조정합니다.

핵심 기능:
- 시장 상황별 TTL 조정 (개장/폐장, 변동성)
- 접근 빈도 기반 TTL 최적화
- 심볼별 개별 TTL 관리
- 캐시 적중률 피드백 반영
"""
from typing import Dict, Optional, Any, List
from datetime import datetime, time as dt_time
from dataclasses import dataclass, field
from enum import Enum
import statistics
import math

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("AdaptiveTTLManager")


class MarketCondition(Enum):
    """시장 상황"""
    ACTIVE = "ACTIVE"           # 활발한 거래 (높은 변동성)
    NORMAL = "NORMAL"           # 정상 거래
    QUIET = "QUIET"             # 조용한 거래 (낮은 변동성)
    CLOSED = "CLOSED"           # 시장 휴무
    UNKNOWN = "UNKNOWN"         # 상황 불명


class TimeZoneActivity(Enum):
    """시간대별 활동성"""
    ASIA_PRIME = "ASIA_PRIME"       # 아시아 주 거래시간 (09:00-18:00 KST)
    EUROPE_PRIME = "EUROPE_PRIME"   # 유럽 주 거래시간 (15:00-24:00 KST)
    US_PRIME = "US_PRIME"           # 미국 주 거래시간 (22:00-07:00 KST)
    OFF_HOURS = "OFF_HOURS"         # 비활성 시간대


@dataclass
class AccessPattern:
    """접근 패턴 분석"""
    symbol: str
    timeframe: str = ""

    # 접근 통계
    total_accesses: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    # 시간 통계
    access_intervals: List[float] = field(default_factory=list)
    last_access: Optional[datetime] = None

    # 성능 통계
    avg_response_time: float = 0.0
    volatility_score: float = 0.0

    @property
    def hit_rate(self) -> float:
        """캐시 적중률"""
        if self.total_accesses == 0:
            return 0.0
        return self.cache_hits / self.total_accesses

    @property
    def avg_interval(self) -> float:
        """평균 접근 간격 (초)"""
        if len(self.access_intervals) < 2:
            return 3600.0  # 기본값: 1시간
        return statistics.mean(self.access_intervals)

    @property
    def access_frequency(self) -> float:
        """접근 빈도 (회/시간)"""
        if self.avg_interval <= 0:
            return 0.0
        return 3600.0 / self.avg_interval

    def update_access(self, cache_hit: bool, response_time: float = 0.0) -> None:
        """접근 정보 업데이트"""
        now = datetime.now()

        # 접근 간격 계산
        if self.last_access:
            interval = (now - self.last_access).total_seconds()
            self.access_intervals.append(interval)

            # 최근 50회 접근만 유지
            if len(self.access_intervals) > 50:
                self.access_intervals.pop(0)

        # 통계 업데이트
        self.total_accesses += 1
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

        # 응답 시간 업데이트 (지수 평활)
        if response_time > 0:
            alpha = 0.1  # 평활 계수
            self.avg_response_time = (
                self.avg_response_time * (1 - alpha) + response_time * alpha
            )

        self.last_access = now


@dataclass
class TTLConfig:
    """TTL 설정"""
    base_ttl: float                    # 기본 TTL (초)
    min_ttl: float = 1.0              # 최소 TTL
    max_ttl: float = 3600.0           # 최대 TTL

    # 조정 계수
    frequency_factor: float = 1.0      # 접근 빈도 계수
    volatility_factor: float = 1.0     # 변동성 계수
    hit_rate_factor: float = 1.0       # 적중률 계수
    market_factor: float = 1.0         # 시장 상황 계수
    timezone_factor: float = 1.0       # 시간대 계수

    @property
    def calculated_ttl(self) -> float:
        """계산된 TTL"""
        ttl = (self.base_ttl *
               self.frequency_factor *
               self.volatility_factor *
               self.hit_rate_factor *
               self.market_factor *
               self.timezone_factor)

        return max(self.min_ttl, min(self.max_ttl, ttl))


class AdaptiveTTLManager:
    """
    적응형 TTL 관리자

    다양한 요소를 종합하여 동적으로 TTL을 조정합니다.
    """

    def __init__(self):
        # 기본 TTL 설정 (타입별)
        self.BASE_TTL_CONFIG = {
            "ticker": TTLConfig(base_ttl=3.0, min_ttl=1.0, max_ttl=30.0),
            "orderbook": TTLConfig(base_ttl=10.0, min_ttl=2.0, max_ttl=60.0),
            "trades": TTLConfig(base_ttl=60.0, min_ttl=10.0, max_ttl=300.0),
            "candles": TTLConfig(base_ttl=300.0, min_ttl=60.0, max_ttl=3600.0),
            "market": TTLConfig(base_ttl=300.0, min_ttl=30.0, max_ttl=1800.0)
        }

        # 심볼별 접근 패턴 추적
        self.access_patterns: Dict[str, AccessPattern] = {}

        # 시장 상황 캐시
        self._market_condition_cache: Dict[str, MarketCondition] = {}
        self._market_condition_timestamp = datetime.now()

        # 통계
        self._ttl_calculations = 0
        self._avg_calculation_time = 0.0

        logger.info("적응형 TTL 관리자 초기화 완료")

    def calculate_optimal_ttl(self,
                             data_type: str,
                             symbol: str = "",
                             timeframe: str = "",
                             current_volatility: Optional[float] = None) -> float:
        """
        최적 TTL 계산

        Args:
            data_type: 데이터 타입 (ticker, orderbook, trades, candles)
            symbol: 심볼
            timeframe: 타임프레임 (캔들인 경우)
            current_volatility: 현재 변동성 (0.0 ~ 1.0)

        Returns:
            최적화된 TTL (초)
        """
        start_time = datetime.now()

        try:
            # 기본 TTL 설정 가져오기
            base_config = self.BASE_TTL_CONFIG.get(data_type)
            if not base_config:
                logger.warning(f"알 수 없는 데이터 타입: {data_type}")
                return 60.0  # 기본값

            # 설정 복사
            config = TTLConfig(
                base_ttl=base_config.base_ttl,
                min_ttl=base_config.min_ttl,
                max_ttl=base_config.max_ttl
            )

            # 심볼별 접근 패턴 분석
            pattern_key = f"{symbol}:{timeframe}" if timeframe else symbol
            if pattern_key in self.access_patterns:
                pattern = self.access_patterns[pattern_key]

                # 1. 접근 빈도 계수 계산
                config.frequency_factor = self._calculate_frequency_factor(pattern)

                # 2. 적중률 계수 계산
                config.hit_rate_factor = self._calculate_hit_rate_factor(pattern)

            # 3. 변동성 계수 계산
            if current_volatility is not None:
                config.volatility_factor = self._calculate_volatility_factor(current_volatility)
            else:
                # 패턴에서 변동성 추정
                if pattern_key in self.access_patterns:
                    pattern = self.access_patterns[pattern_key]
                    config.volatility_factor = self._calculate_volatility_factor(pattern.volatility_score)

            # 4. 시장 상황 계수 계산
            market_condition = self._get_market_condition(symbol)
            config.market_factor = self._calculate_market_factor(market_condition)

            # 5. 시간대 계수 계산
            timezone_activity = self._get_timezone_activity()
            config.timezone_factor = self._calculate_timezone_factor(timezone_activity)

            # 최종 TTL 계산
            optimal_ttl = config.calculated_ttl

            # 통계 업데이트
            self._ttl_calculations += 1
            calculation_time = (datetime.now() - start_time).total_seconds() * 1000
            alpha = 0.1
            self._avg_calculation_time = (
                self._avg_calculation_time * (1 - alpha) + calculation_time * alpha
            )

            logger.debug(f"TTL 계산: {data_type} {symbol} = {optimal_ttl:.1f}s "
                        f"(freq={config.frequency_factor:.2f}, "
                        f"hit={config.hit_rate_factor:.2f}, "
                        f"vol={config.volatility_factor:.2f}, "
                        f"mkt={config.market_factor:.2f}, "
                        f"tz={config.timezone_factor:.2f})")

            return optimal_ttl

        except Exception as e:
            logger.error(f"TTL 계산 실패: {data_type} {symbol}, {e}")
            # 안전한 fallback
            return self.BASE_TTL_CONFIG.get(data_type, TTLConfig(base_ttl=60.0)).base_ttl

    def record_access(self,
                     data_type: str,
                     symbol: str,
                     cache_hit: bool,
                     response_time: float = 0.0,
                     timeframe: str = "",
                     volatility: Optional[float] = None) -> None:
        """접근 기록"""
        pattern_key = f"{symbol}:{timeframe}" if timeframe else symbol

        if pattern_key not in self.access_patterns:
            self.access_patterns[pattern_key] = AccessPattern(
                symbol=symbol,
                timeframe=timeframe
            )

        pattern = self.access_patterns[pattern_key]
        pattern.update_access(cache_hit, response_time)

        # 변동성 업데이트
        if volatility is not None:
            pattern.volatility_score = volatility

        logger.debug(f"접근 기록: {data_type} {symbol}, hit={cache_hit}, "
                    f"rt={response_time:.1f}ms")

    def _calculate_frequency_factor(self, pattern: AccessPattern) -> float:
        """접근 빈도 계수 계산"""
        frequency = pattern.access_frequency

        if frequency <= 0:
            return 1.0

        # 접근 빈도가 높을수록 TTL 단축 (더 자주 갱신)
        # 1회/시간 = 1.0, 60회/시간 = 0.5, 3600회/시간 = 0.1
        factor = max(0.1, 1.0 / (1.0 + math.log10(frequency)))

        return factor

    def _calculate_hit_rate_factor(self, pattern: AccessPattern) -> float:
        """적중률 계수 계산"""
        hit_rate = pattern.hit_rate

        # 적중률이 높을수록 TTL 연장
        # 0% = 0.5배, 50% = 1.0배, 90% = 1.5배, 100% = 2.0배
        factor = 0.5 + 1.5 * hit_rate

        return factor

    def _calculate_volatility_factor(self, volatility: float) -> float:
        """변동성 계수 계산"""
        if volatility <= 0:
            return 1.0

        # 변동성이 높을수록 TTL 단축
        # 0% = 1.5배, 50% = 1.0배, 100% = 0.3배
        factor = max(0.3, 1.5 - volatility)

        return factor

    def _calculate_market_factor(self, condition: MarketCondition) -> float:
        """시장 상황 계수 계산"""
        factor_map = {
            MarketCondition.ACTIVE: 0.5,    # 활발한 시장: TTL 단축
            MarketCondition.NORMAL: 1.0,    # 정상 시장: 기본 TTL
            MarketCondition.QUIET: 1.5,     # 조용한 시장: TTL 연장
            MarketCondition.CLOSED: 2.0,    # 시장 휴무: TTL 연장
            MarketCondition.UNKNOWN: 1.0    # 불명: 기본 TTL
        }

        return factor_map.get(condition, 1.0)

    def _calculate_timezone_factor(self, activity: TimeZoneActivity) -> float:
        """시간대 계수 계산"""
        factor_map = {
            TimeZoneActivity.ASIA_PRIME: 0.8,     # 아시아 주시간: TTL 단축
            TimeZoneActivity.EUROPE_PRIME: 0.9,   # 유럽 주시간: 약간 단축
            TimeZoneActivity.US_PRIME: 0.7,       # 미국 주시간: TTL 단축
            TimeZoneActivity.OFF_HOURS: 1.3       # 비활성 시간: TTL 연장
        }

        return factor_map.get(activity, 1.0)

    def _get_market_condition(self, symbol: str) -> MarketCondition:
        """시장 상황 분석"""
        # 캐시 확인 (5분간 유지)
        cache_age = (datetime.now() - self._market_condition_timestamp).total_seconds()
        if cache_age < 300 and symbol in self._market_condition_cache:
            return self._market_condition_cache[symbol]

        try:
            # 실제 구현에서는 시장 데이터 분석
            # 현재는 시간 기반 간단한 추정
            now = datetime.now()
            current_hour = now.hour

            # 암호화폐는 24시간 거래이므로 단순화된 로직
            if 6 <= current_hour <= 22:
                condition = MarketCondition.NORMAL
            else:
                condition = MarketCondition.QUIET

            # 캐시 업데이트
            self._market_condition_cache[symbol] = condition
            if cache_age >= 300:
                self._market_condition_timestamp = now

            return condition

        except Exception as e:
            logger.warning(f"시장 상황 분석 실패: {symbol}, {e}")
            return MarketCondition.UNKNOWN

    def _get_timezone_activity(self) -> TimeZoneActivity:
        """현재 시간대 활동성 분석"""
        now = datetime.now()
        current_time = now.time()

        # KST 기준 시간대별 활동성
        if dt_time(9, 0) <= current_time <= dt_time(18, 0):
            return TimeZoneActivity.ASIA_PRIME
        elif dt_time(15, 0) <= current_time <= dt_time(23, 59):
            return TimeZoneActivity.EUROPE_PRIME
        elif current_time >= dt_time(22, 0) or current_time <= dt_time(7, 0):
            return TimeZoneActivity.US_PRIME
        else:
            return TimeZoneActivity.OFF_HOURS

    # =====================================
    # 관리 및 통계
    # =====================================

    def get_symbol_ttl_insights(self, symbol: str) -> Optional[Dict[str, Any]]:
        """특정 심볼의 TTL 인사이트"""
        if symbol not in self.access_patterns:
            return None

        pattern = self.access_patterns[symbol]

        # 각 데이터 타입별 권장 TTL 계산
        recommended_ttls = {}
        for data_type in self.BASE_TTL_CONFIG.keys():
            ttl = self.calculate_optimal_ttl(data_type, symbol)
            recommended_ttls[data_type] = ttl

        return {
            "symbol": symbol,
            "access_pattern": {
                "total_accesses": pattern.total_accesses,
                "hit_rate": f"{pattern.hit_rate * 100:.1f}%",
                "avg_interval": f"{pattern.avg_interval:.1f}s",
                "access_frequency": f"{pattern.access_frequency:.1f}/hour",
                "avg_response_time": f"{pattern.avg_response_time:.1f}ms",
                "volatility_score": f"{pattern.volatility_score:.2f}"
            },
            "recommended_ttls": recommended_ttls,
            "market_condition": self._get_market_condition(symbol).value,
            "timezone_activity": self._get_timezone_activity().value
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계"""
        total_patterns = len(self.access_patterns)

        if total_patterns > 0:
            avg_hit_rate = statistics.mean(
                pattern.hit_rate for pattern in self.access_patterns.values()
            )
            avg_frequency = statistics.mean(
                pattern.access_frequency for pattern in self.access_patterns.values()
            )
        else:
            avg_hit_rate = 0.0
            avg_frequency = 0.0

        return {
            "ttl_calculations": self._ttl_calculations,
            "avg_calculation_time_ms": self._avg_calculation_time,
            "tracked_patterns": total_patterns,
            "average_hit_rate": f"{avg_hit_rate * 100:.1f}%",
            "average_frequency": f"{avg_frequency:.1f}/hour",
            "base_ttl_configs": {
                data_type: {
                    "base_ttl": config.base_ttl,
                    "min_ttl": config.min_ttl,
                    "max_ttl": config.max_ttl
                }
                for data_type, config in self.BASE_TTL_CONFIG.items()
            }
        }

    def cleanup_old_patterns(self, max_age_hours: float = 24.0) -> int:
        """오래된 패턴 정리"""
        cutoff_time = datetime.now()
        cutoff_time = cutoff_time.replace(
            hour=cutoff_time.hour - int(max_age_hours),
            minute=cutoff_time.minute - int((max_age_hours % 1) * 60)
        )

        old_patterns = []
        for key, pattern in self.access_patterns.items():
            if pattern.last_access and pattern.last_access < cutoff_time:
                old_patterns.append(key)

        for key in old_patterns:
            del self.access_patterns[key]

        if old_patterns:
            logger.info(f"오래된 접근 패턴 {len(old_patterns)}개 정리 완료")

        return len(old_patterns)

    def reset_stats(self) -> None:
        """통계 초기화"""
        self.access_patterns.clear()
        self._market_condition_cache.clear()
        self._ttl_calculations = 0
        self._avg_calculation_time = 0.0
        logger.info("적응형 TTL 관리자 통계 초기화 완료")

    def __str__(self) -> str:
        return (f"AdaptiveTTLManager("
                f"patterns={len(self.access_patterns)}, "
                f"calculations={self._ttl_calculations}, "
                f"avg_time={self._avg_calculation_time:.1f}ms)")
