"""
MarketDataBackbone V2 - 데이터 정규화 및 검증 시스템 (간소화)

데이터 검증, 품질 평가, 정규화를 담당합니다.
"""

from typing import Dict, Any, List, Tuple
from decimal import Decimal
from datetime import datetime
import hashlib

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .market_data_backbone import TickerData
from .data_models import DataSource, DataQuality, NormalizedTickerData
from .data_creator import TickerDataCreator


class DataNormalizer:
    """데이터 정규화 및 검증 시스템"""

    def __init__(self):
        self._logger = create_component_logger("DataNormalizer")
        self._data_creator = TickerDataCreator()

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
        self._data_creator.validate_required_fields(raw_data, source)

        try:
            # 1. 기본 TickerData 생성
            ticker_data = self._data_creator.create_ticker_data(raw_data, source)

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
            symbol=self._data_creator.extract_symbol_safe(raw_data, source),
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
