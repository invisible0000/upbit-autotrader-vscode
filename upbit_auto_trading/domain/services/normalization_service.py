"""
Domain Service for Value Normalization

서로 다른 comparison_group 간 정규화를 담당하는 도메인 서비스
호환성 검증에서 WARNING 수준으로 분류된 조합들의 정규화 처리
Domain Event 발행을 통한 정규화 결과 알림 지원
"""

from typing import Dict, Optional
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

from upbit_auto_trading.domain.entities.trigger import TradingVariable

# Domain Event 관련 import 추가
from upbit_auto_trading.domain.events.trigger_events import (
    TradingSignalGenerated  # 정규화 결과를 거래 신호로 취급
)
from upbit_auto_trading.domain.events.domain_event_publisher import get_domain_event_publisher

class NormalizationMethod(Enum):
    """정규화 방법"""
    MINMAX = "minmax"          # 최소-최대 정규화 (0-1 스케일)
    ZSCORE = "zscore"          # Z-스코어 정규화 (평균 0, 표준편차 1)
    PERCENTAGE = "percentage"   # 백분율 기반 정규화
    ROBUST = "robust"          # 로버스트 정규화 (중앙값, IQR 기반)

@dataclass(frozen=True)
class NormalizationParameters:
    """
    정규화 파라미터 Value Object

    실제 정규화에 필요한 통계치들을 저장
    Infrastructure 계층에서 과거 데이터 기반으로 계산됨
    """
    group: str
    method: NormalizationMethod

    # MinMax 정규화용
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    # Z-Score 정규화용
    mean: Optional[float] = None
    std: Optional[float] = None

    # Robust 정규화용
    median: Optional[float] = None
    iqr: Optional[float] = None

    # 추가 메타데이터
    sample_size: int = 0
    confidence_level: float = 0.95
    last_updated: Optional[str] = None

@dataclass(frozen=True)
class NormalizationResult:
    """
    정규화 결과 Value Object

    정규화된 값과 메타데이터를 포함
    """
    original_value1: float
    original_value2: float
    normalized_value1: float
    normalized_value2: float

    group1: str
    group2: str
    method: NormalizationMethod

    # 정규화 품질 지표
    confidence_score: float = 1.0  # 0.0 ~ 1.0
    is_reliable: bool = True
    warning_message: Optional[str] = None

    # 역정규화를 위한 파라미터 보존
    normalization_params1: Optional[NormalizationParameters] = None
    normalization_params2: Optional[NormalizationParameters] = None

class NormalizationStrategy(ABC):
    """정규화 전략 인터페이스"""

    @abstractmethod
    def normalize(self, value: float, params: NormalizationParameters) -> float:
        """값을 정규화"""
        pass

    @abstractmethod
    def denormalize(self, normalized_value: float, params: NormalizationParameters) -> float:
        """정규화된 값을 원래 스케일로 복원"""
        pass

class MinMaxNormalizationStrategy(NormalizationStrategy):
    """최소-최대 정규화 전략"""

    def normalize(self, value: float, params: NormalizationParameters) -> float:
        if params.min_value is None or params.max_value is None:
            raise ValueError("MinMax 정규화에는 min_value, max_value가 필요합니다")

        if params.max_value == params.min_value:
            return 0.5  # 상수값인 경우 중간값 반환

        normalized = (value - params.min_value) / (params.max_value - params.min_value)
        return max(0.0, min(1.0, normalized))  # 0-1 범위로 클램핑

    def denormalize(self, normalized_value: float, params: NormalizationParameters) -> float:
        if params.min_value is None or params.max_value is None:
            raise ValueError("MinMax 역정규화에는 min_value, max_value가 필요합니다")

        return params.min_value + normalized_value * (params.max_value - params.min_value)

class ZScoreNormalizationStrategy(NormalizationStrategy):
    """Z-스코어 정규화 전략"""

    def normalize(self, value: float, params: NormalizationParameters) -> float:
        if params.mean is None or params.std is None:
            raise ValueError("Z-Score 정규화에는 mean, std가 필요합니다")

        if params.std == 0:
            return 0.0  # 표준편차가 0인 경우

        return (value - params.mean) / params.std

    def denormalize(self, normalized_value: float, params: NormalizationParameters) -> float:
        if params.mean is None or params.std is None:
            raise ValueError("Z-Score 역정규화에는 mean, std가 필요합니다")

        return normalized_value * params.std + params.mean

class RobustNormalizationStrategy(NormalizationStrategy):
    """로버스트 정규화 전략"""

    def normalize(self, value: float, params: NormalizationParameters) -> float:
        if params.median is None or params.iqr is None:
            raise ValueError("Robust 정규화에는 median, iqr이 필요합니다")

        if params.iqr == 0:
            return 0.0  # IQR이 0인 경우

        return (value - params.median) / params.iqr

    def denormalize(self, normalized_value: float, params: NormalizationParameters) -> float:
        if params.median is None or params.iqr is None:
            raise ValueError("Robust 역정규화에는 median, iqr이 필요합니다")

        return normalized_value * params.iqr + params.median

class NormalizationService:
    """
    Domain Service: 값 정규화

    책임:
    - 서로 다른 comparison_group 간 값 정규화
    - 다양한 정규화 방법 지원 (MinMax, Z-Score, Robust)
    - 정규화 품질 평가 및 신뢰성 검증
    - StrategyCompatibilityService의 WARNING 처리 지원
    """

    def __init__(self):
        self._strategies: Dict[NormalizationMethod, NormalizationStrategy] = {
            NormalizationMethod.MINMAX: MinMaxNormalizationStrategy(),
            NormalizationMethod.ZSCORE: ZScoreNormalizationStrategy(),
            NormalizationMethod.ROBUST: RobustNormalizationStrategy(),
        }

        # 임시 정규화 파라미터 (추후 Infrastructure에서 실제 데이터 기반으로 계산)
        self._default_params = self._init_default_parameters()

    def normalize_for_comparison(self, value1: float, group1: str,
                                value2: float, group2: str,
                                method: NormalizationMethod = NormalizationMethod.MINMAX,
                                custom_params: Optional[Dict[str, NormalizationParameters]] = None) -> NormalizationResult:
        """
        두 값을 같은 스케일로 정규화하여 비교 가능하게 만듦

        Args:
            value1: 첫 번째 값
            group1: 첫 번째 값의 comparison_group
            value2: 두 번째 값
            group2: 두 번째 값의 comparison_group
            method: 정규화 방법
            custom_params: 사용자 정의 정규화 파라미터

        Returns:
            NormalizationResult: 정규화된 값들과 메타데이터
        """
        # 같은 그룹이면 정규화 불필요
        if group1 == group2:
            return NormalizationResult(
                original_value1=value1,
                original_value2=value2,
                normalized_value1=value1,
                normalized_value2=value2,
                group1=group1,
                group2=group2,
                method=method,
                confidence_score=1.0,
                is_reliable=True,
                warning_message="같은 그룹이므로 정규화 불필요"
            )

        # 지원되는 그룹 조합 확인
        supported_combinations = {
            frozenset(["price_comparable", "percentage_comparable"]),
            frozenset(["volume_comparable", "percentage_comparable"]),
            frozenset(["zero_centered", "percentage_comparable"])
        }

        if frozenset([group1, group2]) not in supported_combinations:
            raise ValueError(
                f"지원하지 않는 그룹 조합: {group1} vs {group2}. "
                f"지원되는 조합: {supported_combinations}"
            )

        # 정규화 파라미터 가져오기
        params1 = self._get_normalization_params(group1, method, custom_params)
        params2 = self._get_normalization_params(group2, method, custom_params)

        # 정규화 전략 가져오기
        strategy = self._strategies[method]

        # 정규화 수행
        try:
            normalized_value1 = strategy.normalize(value1, params1)
            normalized_value2 = strategy.normalize(value2, params2)

            # 정규화 품질 평가
            confidence_score = self._calculate_confidence_score(params1, params2)
            is_reliable = confidence_score >= 0.7
            warning_message = self._generate_warning_message(params1, params2, confidence_score)

            return NormalizationResult(
                original_value1=value1,
                original_value2=value2,
                normalized_value1=normalized_value1,
                normalized_value2=normalized_value2,
                group1=group1,
                group2=group2,
                method=method,
                confidence_score=confidence_score,
                is_reliable=is_reliable,
                warning_message=warning_message,
                normalization_params1=params1,
                normalization_params2=params2
            )

        except Exception as e:
            # 정규화 실패 시 원본값 반환하되 경고 표시
            return NormalizationResult(
                original_value1=value1,
                original_value2=value2,
                normalized_value1=value1,
                normalized_value2=value2,
                group1=group1,
                group2=group2,
                method=method,
                confidence_score=0.0,
                is_reliable=False,
                warning_message=f"정규화 실패: {str(e)}"
            )

    def normalize_variable_values(self, variables: list[TradingVariable],
                                 values: list[float],
                                 method: NormalizationMethod = NormalizationMethod.MINMAX) -> Dict[str, float]:
        """
        복수 변수의 값들을 일괄 정규화

        트리거 빌더에서 여러 변수를 동시에 비교할 때 사용
        """
        if len(variables) != len(values):
            raise ValueError("변수 개수와 값 개수가 일치하지 않습니다")

        if len(variables) < 2:
            # 단일 변수는 정규화 불필요
            return {variables[0].variable_id: values[0]} if variables else {}

        # 첫 번째 변수를 기준으로 나머지 변수들을 정규화
        base_variable = variables[0]
        base_value = values[0]

        normalized_values = {base_variable.variable_id: base_value}

        for i in range(1, len(variables)):
            variable = variables[i]
            value = values[i]

            try:
                result = self.normalize_for_comparison(
                    base_value, base_variable.comparison_group,
                    value, variable.comparison_group,
                    method
                )

                # 두 번째 값(비교 대상)의 정규화된 값을 저장
                normalized_values[variable.variable_id] = result.normalized_value2

            except ValueError:
                # 정규화 불가능한 조합은 원본값 유지
                normalized_values[variable.variable_id] = value

        return normalized_values

    def denormalize_value(self, normalized_value: float,
                         target_group: str,
                         method: NormalizationMethod,
                         normalization_params: Optional[NormalizationParameters] = None) -> float:
        """정규화된 값을 원래 스케일로 복원"""
        if normalization_params is None:
            normalization_params = self._get_normalization_params(target_group, method)

        strategy = self._strategies[method]
        return strategy.denormalize(normalized_value, normalization_params)

    def _get_normalization_params(self, group: str, method: NormalizationMethod,
                                 custom_params: Optional[Dict[str, NormalizationParameters]] = None) -> NormalizationParameters:
        """그룹별 정규화 파라미터 조회"""
        if custom_params and group in custom_params:
            return custom_params[group]

        return self._default_params.get(f"{group}_{method.value}",
                                      self._create_fallback_params(group, method))

    def _calculate_confidence_score(self, params1: NormalizationParameters,
                                   params2: NormalizationParameters) -> float:
        """정규화 신뢰도 점수 계산"""
        # 샘플 크기 기반 신뢰도
        min_sample_size = min(params1.sample_size, params2.sample_size)
        sample_confidence = min(1.0, min_sample_size / 1000)  # 1000개 샘플을 기준으로 100% 신뢰도

        # 파라미터 완전성 기반 신뢰도
        param_confidence = 1.0

        # params1 파라미터 검증
        if params1.method == NormalizationMethod.MINMAX:
            if params1.min_value is None or params1.max_value is None:
                param_confidence *= 0.5
        elif params1.method == NormalizationMethod.ZSCORE:
            if params1.mean is None or params1.std is None:
                param_confidence *= 0.5

        # params2 파라미터 검증
        if params2.method == NormalizationMethod.MINMAX:
            if params2.min_value is None or params2.max_value is None:
                param_confidence *= 0.5
        elif params2.method == NormalizationMethod.ZSCORE:
            if params2.mean is None or params2.std is None:
                param_confidence *= 0.5

        return sample_confidence * param_confidence

    def _generate_warning_message(self, params1: NormalizationParameters,
                                 params2: NormalizationParameters,
                                 confidence_score: float) -> Optional[str]:
        """경고 메시지 생성"""
        warnings = []

        if confidence_score < 0.7:
            warnings.append("정규화 신뢰도가 낮습니다")

        if params1.sample_size < 100 or params2.sample_size < 100:
            warnings.append("통계 샘플 크기가 부족합니다")

        if params1.method != params2.method:
            warnings.append("서로 다른 정규화 방법이 사용되었습니다")

        return "; ".join(warnings) if warnings else None

    def _create_fallback_params(self, group: str, method: NormalizationMethod) -> NormalizationParameters:
        """기본 정규화 파라미터 생성 (임시 구현)"""
        # 실제로는 Infrastructure 계층에서 과거 데이터 기반으로 계산해야 함

        if group == "price_comparable":
            if method == NormalizationMethod.MINMAX:
                return NormalizationParameters(
                    group=group, method=method,
                    min_value=10000.0, max_value=100000000.0,  # 1만원 ~ 1억원
                    sample_size=1500  # 충분한 샘플 크기
                )
            elif method == NormalizationMethod.ZSCORE:
                return NormalizationParameters(
                    group=group, method=method,
                    mean=50000000.0, std=20000000.0,  # 평균 5천만원, 표준편차 2천만원
                    sample_size=1500
                )

        elif group == "percentage_comparable":
            if method == NormalizationMethod.MINMAX:
                return NormalizationParameters(
                    group=group, method=method,
                    min_value=0.0, max_value=100.0,  # 0% ~ 100%
                    sample_size=1500  # 충분한 샘플 크기
                )
            elif method == NormalizationMethod.ZSCORE:
                return NormalizationParameters(
                    group=group, method=method,
                    mean=50.0, std=28.87,  # 평균 50%, 표준편차 28.87% (0-100 균등분포)
                    sample_size=1500
                )

        elif group == "zero_centered":
            if method == NormalizationMethod.MINMAX:
                return NormalizationParameters(
                    group=group, method=method,
                    min_value=-1.0, max_value=1.0,  # -1 ~ 1
                    sample_size=1500
                )
            elif method == NormalizationMethod.ZSCORE:
                return NormalizationParameters(
                    group=group, method=method,
                    mean=0.0, std=0.5,  # 평균 0, 표준편차 0.5
                    sample_size=1500
                )

        # 기본값
        return NormalizationParameters(
            group=group, method=method,
            min_value=0.0, max_value=1.0,
            mean=0.0, std=1.0,
            sample_size=1500  # 충분한 신뢰도
        )

    def _init_default_parameters(self) -> Dict[str, NormalizationParameters]:
        """기본 정규화 파라미터 초기화"""
        params = {}

        groups = ["price_comparable", "percentage_comparable", "zero_centered", "volume_comparable"]
        methods = [NormalizationMethod.MINMAX, NormalizationMethod.ZSCORE, NormalizationMethod.ROBUST]

        for group in groups:
            for method in methods:
                key = f"{group}_{method.value}"
                params[key] = self._create_fallback_params(group, method)

        return params
