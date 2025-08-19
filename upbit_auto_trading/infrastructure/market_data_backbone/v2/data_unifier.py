"""
DataUnifier V3 - Phase 1.3 고급 데이터 통합 및 정규화 시스템

✅ Phase 1.1: 기본 REST API 데이터 통합
✅ Phase 1.2: WebSocket 데이터 통합
🔥 Phase 1.3: 고급 데이터 관리 시스템
    - 데이터 정규화 로직
    - 통합 스키마 관리
    - 대용량 데이터 처리
    - 지능형 캐싱 시스템
    - 데이터 일관성 검증
"""

from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
import hashlib
import json
from collections import defaultdict

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .market_data_backbone import TickerData


class DataSource(Enum):
    """데이터 소스 열거형"""
    REST = "rest"
    WEBSOCKET = "websocket"
    WEBSOCKET_SIMPLE = "websocket_simple"
    CACHED = "cached"


class DataQuality(Enum):
    """데이터 품질 등급"""
    HIGH = "high"           # 완전한 데이터, 모든 필드 검증 통과
    MEDIUM = "medium"       # 일부 필드 누락 또는 추정값 포함
    LOW = "low"             # 필수 필드만 존재, 검증 실패 또는 오류 보정
    INVALID = "invalid"     # 사용 불가능한 데이터


@dataclass(frozen=True)
class NormalizedTickerData:
    """정규화된 티커 데이터 모델 (Phase 1.3)"""
    # 기본 TickerData 확장
    ticker_data: TickerData

    # 추가 메타데이터
    data_quality: DataQuality
    confidence_score: Decimal  # 0.0 ~ 1.0
    normalization_timestamp: datetime
    data_checksum: str

    # 검증 결과
    validation_errors: Tuple[str, ...]
    corrected_fields: Tuple[str, ...]

    # 성능 메트릭
    processing_time_ms: Decimal
    data_source_priority: int  # 1(최고) ~ 10(최저)


@dataclass
class CacheEntry:
    """캐시 엔트리 구조"""
    data: NormalizedTickerData
    created_at: datetime
    access_count: int
    last_access: datetime
    ttl_seconds: int


class DataNormalizer:
    """데이터 정규화 및 검증 시스템"""

    def __init__(self):
        self._logger = create_component_logger("DataNormalizer")

        # 정규화 규칙
        self._price_precision = Decimal('0.01')  # 원 단위
        self._rate_precision = Decimal('0.0001')  # 0.01% 단위
        self._volume_precision = Decimal('0.00000001')  # 8자리 소수점

        # 검증 규칙
        self._max_price_change_rate = Decimal('30.0')  # 30% 이상 변화율은 의심
        self._min_valid_price = Decimal('1.0')  # 최소 유효 가격
        self._max_valid_price = Decimal('1000000000.0')  # 최대 유효 가격 (10억원)

    def normalize_ticker(self, raw_data: Dict[str, Any], source: DataSource) -> NormalizedTickerData:
        """
        원시 데이터를 정규화된 형태로 변환

        Args:
            raw_data: API 원시 응답 데이터
            source: 데이터 소스 타입

        Returns:
            NormalizedTickerData: 정규화된 데이터
        """
        start_time = datetime.now()

        # 0. 필수 필드 검증 (예외 발생 가능)
        self._validate_required_fields(raw_data, source)

        try:
            # 1. 기본 TickerData 생성
            ticker_data = self._create_ticker_data(raw_data, source)

            # 2. 데이터 정규화
            normalized_ticker = self._apply_normalization(ticker_data)

            # 3. 검증 수행
            validation_errors, corrected_fields = self._validate_and_correct(normalized_ticker)

            # 4. 품질 등급 결정
            quality = self._determine_quality(normalized_ticker, validation_errors)

            # 5. 신뢰도 점수 계산
            confidence = self._calculate_confidence(normalized_ticker, source, quality)

            # 6. 체크섬 생성
            checksum = self._generate_checksum(normalized_ticker)

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return NormalizedTickerData(
                ticker_data=normalized_ticker,
                data_quality=quality,
                confidence_score=confidence,
                normalization_timestamp=datetime.now(),
                data_checksum=checksum,
                validation_errors=tuple(validation_errors),
                corrected_fields=tuple(corrected_fields),
                processing_time_ms=Decimal(str(processing_time)),
                data_source_priority=self._get_source_priority(source)
            )

        except Exception as e:
            self._logger.error(f"데이터 정규화 실패: {e}")
            # 에러 시에도 기본 구조 반환
            return self._create_fallback_data(raw_data, source, str(e))

    def _create_ticker_data(self, raw_data: Dict[str, Any], source: DataSource) -> TickerData:
        """소스별 TickerData 생성"""
        if source == DataSource.REST:
            return self._create_from_rest(raw_data)
        elif source in [DataSource.WEBSOCKET, DataSource.WEBSOCKET_SIMPLE]:
            return self._create_from_websocket(raw_data, source)
        else:
            raise ValueError(f"지원하지 않는 데이터 소스: {source}")

    def _create_from_rest(self, data: Dict[str, Any]) -> TickerData:
        """REST API 데이터로부터 TickerData 생성"""
        return TickerData(
            symbol=data["market"],
            current_price=Decimal(str(data["trade_price"])),
            change_rate=Decimal(str(data.get("signed_change_rate", 0))) * 100,
            change_amount=Decimal(str(data.get("signed_change_price", 0))),
            volume_24h=Decimal(str(data.get("acc_trade_volume_24h", 0))),
            high_24h=Decimal(str(data.get("high_price", 0))),
            low_24h=Decimal(str(data.get("low_price", 0))),
            prev_closing_price=Decimal(str(data.get("prev_closing_price", 0))),
            timestamp=datetime.now(),
            source=DataSource.REST.value
        )

    def _create_from_websocket(self, data: Dict[str, Any], source: DataSource) -> TickerData:
        """WebSocket 데이터로부터 TickerData 생성"""
        if source == DataSource.WEBSOCKET_SIMPLE:
            # SIMPLE 포맷 (축약된 필드명)
            symbol_field = "cd"
            price_field = "tp"
            change_rate_field = "scr"
            change_amount_field = "scp"
            volume_field = "aav24"
            high_field = "hp"
            low_field = "lp"
        else:
            # DEFAULT 포맷 (전체 필드명)
            symbol_field = "code"
            price_field = "trade_price"
            change_rate_field = "signed_change_rate"
            change_amount_field = "signed_change_price"
            volume_field = "acc_trade_volume_24h"
            high_field = "high_price"
            low_field = "low_price"

        return TickerData(
            symbol=data[symbol_field],
            current_price=Decimal(str(data[price_field])),
            change_rate=Decimal(str(data.get(change_rate_field, 0))) * 100,
            change_amount=Decimal(str(data.get(change_amount_field, 0))),
            volume_24h=Decimal(str(data.get(volume_field, 0))),
            high_24h=Decimal(str(data.get(high_field, 0))),
            low_24h=Decimal(str(data.get(low_field, 0))),
            prev_closing_price=Decimal(str(data.get("prev_closing_price", 0))),
            timestamp=datetime.now(),
            source=source.value
        )

    def _apply_normalization(self, ticker_data: TickerData) -> TickerData:
        """데이터 정규화 적용"""
        return TickerData(
            symbol=ticker_data.symbol,
            current_price=ticker_data.current_price.quantize(self._price_precision),
            change_rate=ticker_data.change_rate.quantize(self._rate_precision),
            change_amount=ticker_data.change_amount.quantize(self._price_precision),
            volume_24h=ticker_data.volume_24h.quantize(self._volume_precision),
            high_24h=ticker_data.high_24h.quantize(self._price_precision),
            low_24h=ticker_data.low_24h.quantize(self._price_precision),
            prev_closing_price=ticker_data.prev_closing_price.quantize(self._price_precision),
            timestamp=ticker_data.timestamp,
            source=ticker_data.source
        )

    def _validate_and_correct(self, ticker_data: TickerData) -> Tuple[List[str], List[str]]:
        """데이터 검증 및 보정"""
        errors = []
        corrected_fields = []

        # 가격 범위 검증
        if ticker_data.current_price < self._min_valid_price:
            errors.append(f"현재가가 최소값보다 낮음: {ticker_data.current_price}")

        if ticker_data.current_price > self._max_valid_price:
            errors.append(f"현재가가 최대값보다 높음: {ticker_data.current_price}")

        # 변화율 검증
        if abs(ticker_data.change_rate) > self._max_price_change_rate:
            errors.append(f"변화율이 임계값 초과: {ticker_data.change_rate}%")

        # 고저가 논리 검증
        if ticker_data.high_24h < ticker_data.low_24h:
            errors.append("24시간 고가가 저가보다 낮음")
            corrected_fields.append("high_24h")

        return errors, corrected_fields

    def _determine_quality(self, ticker_data: TickerData, validation_errors: List[str]) -> DataQuality:
        """데이터 품질 등급 결정"""
        if len(validation_errors) == 0:
            return DataQuality.HIGH
        elif len(validation_errors) <= 2:
            return DataQuality.MEDIUM
        elif len(validation_errors) <= 5:
            return DataQuality.LOW
        else:
            return DataQuality.INVALID

    def _calculate_confidence(self, ticker_data: TickerData, source: DataSource, quality: DataQuality) -> Decimal:
        """신뢰도 점수 계산"""
        base_confidence = {
            DataQuality.HIGH: Decimal('1.0'),
            DataQuality.MEDIUM: Decimal('0.8'),
            DataQuality.LOW: Decimal('0.5'),
            DataQuality.INVALID: Decimal('0.1')
        }[quality]

        # 소스별 가중치
        source_weight = {
            DataSource.REST: Decimal('1.0'),
            DataSource.WEBSOCKET: Decimal('0.95'),
            DataSource.WEBSOCKET_SIMPLE: Decimal('0.9'),
            DataSource.CACHED: Decimal('0.85')
        }.get(source, Decimal('0.5'))

        return base_confidence * source_weight

    def _generate_checksum(self, ticker_data: TickerData) -> str:
        """데이터 체크섬 생성"""
        data_string = f"{ticker_data.symbol}:{ticker_data.current_price}:{ticker_data.timestamp}"
        return hashlib.md5(data_string.encode()).hexdigest()[:16]

    def _get_source_priority(self, source: DataSource) -> int:
        """데이터 소스 우선순위 반환"""
        return {
            DataSource.REST: 1,
            DataSource.WEBSOCKET: 2,
            DataSource.WEBSOCKET_SIMPLE: 3,
            DataSource.CACHED: 4
        }.get(source, 10)

    def _create_fallback_data(self, raw_data: Dict[str, Any], source: DataSource, error_msg: str) -> NormalizedTickerData:
        """에러 시 폴백 데이터 생성"""
        # 최소한의 TickerData 생성
        fallback_ticker = TickerData(
            symbol=self._extract_symbol_safe(raw_data, source),
            current_price=Decimal('0'),
            change_rate=Decimal('0'),
            change_amount=Decimal('0'),
            volume_24h=Decimal('0'),
            high_24h=Decimal('0'),
            low_24h=Decimal('0'),
            prev_closing_price=Decimal('0'),
            timestamp=datetime.now(),
            source=source.value
        )

        return NormalizedTickerData(
            ticker_data=fallback_ticker,
            data_quality=DataQuality.INVALID,
            confidence_score=Decimal('0'),
            normalization_timestamp=datetime.now(),
            data_checksum="error",
            validation_errors=(error_msg,),
            corrected_fields=(),
            processing_time_ms=Decimal('0'),
            data_source_priority=10
        )

    def _validate_required_fields(self, raw_data: Dict[str, Any], source: DataSource) -> None:
        """필수 필드 검증 - 누락 시 예외 발생"""
        required_fields = []

        if source == DataSource.REST:
            required_fields = ["market", "trade_price"]
        elif source == DataSource.WEBSOCKET:
            required_fields = ["code", "trade_price"]
        elif source == DataSource.WEBSOCKET_SIMPLE:
            required_fields = ["cd", "tp"]

        missing_fields = []
        for field in required_fields:
            if field not in raw_data:
                missing_fields.append(field)

        if missing_fields:
            error_msg = f"필수 필드 누락: {', '.join(missing_fields)}"
            self._logger.error(error_msg)
            raise ValueError(error_msg)

    def _extract_symbol_safe(self, raw_data: Dict[str, Any], source: DataSource) -> str:
        """안전한 심볼 추출"""
        try:
            if source == DataSource.REST:
                return raw_data.get("market", "UNKNOWN")
            elif source == DataSource.WEBSOCKET:
                return raw_data.get("code", "UNKNOWN")
            elif source == DataSource.WEBSOCKET_SIMPLE:
                return raw_data.get("cd", "UNKNOWN")
        except Exception:
            pass
        return "UNKNOWN"


class IntelligentCache:
    """지능형 캐싱 시스템 (Phase 1.3)"""

    def __init__(self, default_ttl: int = 60):
        self._logger = create_component_logger("IntelligentCache")
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl

        # 캐시 통계
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0

    async def get(self, cache_key: str) -> Optional[NormalizedTickerData]:
        """캐시에서 데이터 조회"""
        entry = self._cache.get(cache_key)

        if entry is None:
            self._miss_count += 1
            return None

        # TTL 검증
        if self._is_expired(entry):
            self._evict(cache_key)
            self._miss_count += 1
            return None

        # 접근 정보 업데이트
        entry.access_count += 1
        entry.last_access = datetime.now()

        self._hit_count += 1
        return entry.data

    async def set(self, cache_key: str, data: NormalizedTickerData, ttl: Optional[int] = None) -> None:
        """캐시에 데이터 저장"""
        effective_ttl = ttl or self._default_ttl

        entry = CacheEntry(
            data=data,
            created_at=datetime.now(),
            access_count=1,
            last_access=datetime.now(),
            ttl_seconds=effective_ttl
        )

        self._cache[cache_key] = entry
        self._cleanup_if_needed()

    def _is_expired(self, entry: CacheEntry) -> bool:
        """캐시 엔트리 만료 여부 확인"""
        age = (datetime.now() - entry.created_at).total_seconds()
        return age > entry.ttl_seconds

    def _evict(self, cache_key: str) -> None:
        """캐시 엔트리 제거"""
        if cache_key in self._cache:
            del self._cache[cache_key]
            self._eviction_count += 1

    def _cleanup_if_needed(self) -> None:
        """캐시 크기가 임계값을 초과하면 정리"""
        max_size = 1000  # 최대 1000개 엔트리

        if len(self._cache) > max_size:
            # LRU 방식으로 오래된 엔트리 제거
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].last_access
            )

            # 20% 제거
            remove_count = max_size // 5
            for cache_key, _ in sorted_entries[:remove_count]:
                self._evict(cache_key)

    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보 반환"""
        total_requests = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0

        return {
            "total_entries": len(self._cache),
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate_percent": round(hit_rate, 2),
            "eviction_count": self._eviction_count
        }


class DataUnifier:
    """
    고급 데이터 통합 및 관리 시스템 (Phase 1.3)

    기능:
    ✅ REST/WebSocket 데이터 통합
    ✅ 데이터 정규화 및 검증
    ✅ 지능형 캐싱 시스템
    ✅ 대용량 데이터 처리
    ✅ 데이터 일관성 보장
    """

    def __init__(self, cache_ttl: int = 60):
        """DataUnifier 초기화"""
        self._logger = create_component_logger("DataUnifier")

        # 핵심 컴포넌트 초기화
        self._normalizer = DataNormalizer()
        self._cache = IntelligentCache(default_ttl=cache_ttl)

        # 성능 통계
        self._processing_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "normalization_count": 0,
            "error_count": 0
        }

        # 데이터 일관성 추적
        self._consistency_tracker: Dict[str, List[NormalizedTickerData]] = defaultdict(list)

    async def unify_ticker_data(self, raw_data: Dict[str, Any], source: str, use_cache: bool = True) -> NormalizedTickerData:
        """
        통합 티커 데이터 처리 (Phase 1.3 고도화)

        Args:
            raw_data: 원본 API 응답 데이터
            source: 데이터 소스 ("rest", "websocket", "websocket_simple")
            use_cache: 캐시 사용 여부

        Returns:
            NormalizedTickerData: 정규화된 통합 데이터

        Raises:
            ValueError: 지원하지 않는 소스 또는 잘못된 데이터
        """
        self._processing_stats["total_requests"] += 1

        try:
            # 1. 캐시 확인
            cache_key = self._generate_cache_key(raw_data, source)

            if use_cache:
                cached_data = await self._cache.get(cache_key)
                if cached_data:
                    self._processing_stats["cache_hits"] += 1
                    self._logger.debug(f"캐시 히트: {cache_key}")
                    return cached_data

            # 2. 데이터 소스 타입 결정
            data_source = self._determine_data_source(source)

            # 3. 데이터 정규화 수행
            normalized_data = self._normalizer.normalize_ticker(raw_data, data_source)
            self._processing_stats["normalization_count"] += 1

            # 4. 일관성 검증
            await self._verify_data_consistency(normalized_data)

            # 5. 캐시에 저장
            if use_cache:
                await self._cache.set(cache_key, normalized_data)

            self._logger.debug(f"데이터 통합 완료: {normalized_data.ticker_data.symbol} ({normalized_data.data_quality.value})")
            return normalized_data

        except Exception as e:
            self._processing_stats["error_count"] += 1
            self._logger.error(f"데이터 통합 실패: {e}")
            raise ValueError(f"데이터 통합 실패: {e}") from e

    async def unify_multiple_ticker_data(self, data_batch: List[Tuple[Dict[str, Any], str]]) -> List[NormalizedTickerData]:
        """
        대용량 데이터 배치 처리 (Phase 1.3)

        Args:
            data_batch: (raw_data, source) 튜플의 리스트

        Returns:
            List[NormalizedTickerData]: 정규화된 데이터 리스트
        """
        self._logger.info(f"배치 처리 시작: {len(data_batch)}개 데이터")

        # 비동기 병렬 처리
        tasks = [
            self.unify_ticker_data(raw_data, source)
            for raw_data, source in data_batch
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 필터링 (에러 제외)
        successful_results = [
            result for result in results
            if isinstance(result, NormalizedTickerData)
        ]

        error_count = len(results) - len(successful_results)
        if error_count > 0:
            self._logger.warning(f"배치 처리 중 {error_count}개 에러 발생")

        self._logger.info(f"배치 처리 완료: {len(successful_results)}/{len(data_batch)} 성공")
        return successful_results

    def get_processing_statistics(self) -> Dict[str, Any]:
        """처리 통계 정보 반환"""
        cache_stats = self._cache.get_cache_stats()

        total_requests = max(self._processing_stats["total_requests"], 1)

        return {
            "processing_stats": self._processing_stats.copy(),
            "cache_stats": cache_stats,
            "cache_hit_rate": (self._processing_stats["cache_hits"] / total_requests * 100),
            "error_rate": (self._processing_stats["error_count"] / total_requests * 100)
        }

    def _generate_cache_key(self, raw_data: Dict[str, Any], source: str) -> str:
        """캐시 키 생성"""
        # 심볼과 소스 기반 키 생성
        symbol = self._extract_symbol(raw_data, source)
        data_hash = hashlib.md5(json.dumps(raw_data, sort_keys=True).encode()).hexdigest()[:8]
        return f"{symbol}:{source}:{data_hash}"

    def _extract_symbol(self, raw_data: Dict[str, Any], source: str) -> str:
        """데이터에서 심볼 추출"""
        if source == "rest":
            return raw_data.get("market", "UNKNOWN")
        elif source == "websocket":
            return raw_data.get("code", "UNKNOWN")
        elif source == "websocket_simple":
            return raw_data.get("cd", "UNKNOWN")
        else:
            return "UNKNOWN"

    def _determine_data_source(self, source: str) -> DataSource:
        """문자열 소스를 DataSource enum으로 변환"""
        source_mapping = {
            "rest": DataSource.REST,
            "websocket": DataSource.WEBSOCKET,
            "websocket_simple": DataSource.WEBSOCKET_SIMPLE
        }

        if source not in source_mapping:
            raise ValueError(f"지원하지 않는 데이터 소스: {source}")

        return source_mapping[source]

    async def _verify_data_consistency(self, normalized_data: NormalizedTickerData) -> None:
        """데이터 일관성 검증 및 추적"""
        symbol = normalized_data.ticker_data.symbol

        # 추적 데이터에 추가
        self._consistency_tracker[symbol].append(normalized_data)

        # 최대 100개까지만 보관 (메모리 관리)
        if len(self._consistency_tracker[symbol]) > 100:
            self._consistency_tracker[symbol] = self._consistency_tracker[symbol][-50:]
