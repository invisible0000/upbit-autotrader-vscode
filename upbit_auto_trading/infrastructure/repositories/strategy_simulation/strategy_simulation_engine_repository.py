"""
전략 시뮬레이션 엔진 Repository 구현체
시뮬레이션 엔진 생성 및 관리
"""

from typing import Dict, Any, Optional
import importlib
import sys
import os

from upbit_auto_trading.domain.strategy_simulation.value_objects.data_source_type import DataSourceType
from upbit_auto_trading.domain.strategy_simulation.repositories.i_strategy_simulation_repository import (
    IStrategySimulationEngineRepository
)
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("StrategySimulationEngineRepository")


class StrategySimulationEngineRepository(IStrategySimulationEngineRepository):
    """
    전략 시뮬레이션 엔진 Repository 구현체

    각 데이터 소스 타입에 맞는 시뮬레이션 엔진 생성 및 관리
    전략 관리 전용 미니 시뮬레이션 Infrastructure
    """

    def __init__(self):
        """Repository 초기화"""
        self._engine_cache: Dict[str, Any] = {}
        self._engine_capabilities: Dict[DataSourceType, Dict[str, bool]] = {}

        logger.debug("전략 시뮬레이션 엔진 Repository 초기화")

        # 엔진별 기능 정의
        self._initialize_engine_capabilities()

    def create_simulation_engine(self, source_type: DataSourceType) -> Any:
        """데이터 소스 타입에 맞는 시뮬레이션 엔진 생성"""
        try:
            cache_key = f"engine_{source_type.value}"

            # 캐시된 엔진 확인
            if cache_key in self._engine_cache:
                logger.debug(f"캐시된 엔진 반환: {source_type.value}")
                return self._engine_cache[cache_key]

            # 새 엔진 생성
            engine = self._create_engine_instance(source_type)

            if engine:
                self._engine_cache[cache_key] = engine
                logger.debug(f"새 엔진 생성 및 캐시: {source_type.value}")
                return engine
            else:
                logger.warning(f"엔진 생성 실패: {source_type.value}")
                return None

        except Exception as e:
            logger.error(f"시뮬레이션 엔진 생성 실패: {source_type.value}, {e}")
            return None

    def get_engine_capabilities(self, source_type: DataSourceType) -> Dict[str, bool]:
        """엔진별 지원 기능 조회"""
        return self._engine_capabilities.get(source_type, {})

    def cleanup_engine_resources(self, source_type: DataSourceType) -> None:
        """엔진 리소스 정리"""
        try:
            cache_key = f"engine_{source_type.value}"

            if cache_key in self._engine_cache:
                engine = self._engine_cache[cache_key]

                # 엔진별 정리 메서드 호출
                if hasattr(engine, 'cleanup'):
                    engine.cleanup()
                elif hasattr(engine, 'close'):
                    engine.close()

                del self._engine_cache[cache_key]
                logger.debug(f"엔진 리소스 정리 완료: {source_type.value}")

        except Exception as e:
            logger.error(f"엔진 리소스 정리 실패: {source_type.value}, {e}")

    def _initialize_engine_capabilities(self) -> None:
        """엔진별 기능 초기화"""
        self._engine_capabilities = {
            DataSourceType.EMBEDDED_OPTIMIZED: {
                "scenario_optimization": True,
                "real_time_data": False,
                "historical_data": True,
                "custom_scenarios": True,
                "high_performance": True,
                "data_validation": True
            },

            DataSourceType.REAL_DATABASE: {
                "scenario_optimization": False,
                "real_time_data": False,
                "historical_data": True,
                "custom_scenarios": False,
                "high_performance": True,
                "data_validation": True
            },

            DataSourceType.SYNTHETIC_REALISTIC: {
                "scenario_optimization": True,
                "real_time_data": False,
                "historical_data": False,
                "custom_scenarios": True,
                "high_performance": False,
                "data_validation": False
            },

            DataSourceType.SIMPLE_FALLBACK: {
                "scenario_optimization": False,
                "real_time_data": False,
                "historical_data": False,
                "custom_scenarios": False,
                "high_performance": False,
                "data_validation": False
            }
        }

        logger.debug("엔진 기능 정의 완료")

    def _create_engine_instance(self, source_type: DataSourceType) -> Optional[Any]:
        """실제 엔진 인스턴스 생성"""
        try:
            if source_type == DataSourceType.EMBEDDED_OPTIMIZED:
                return self._create_embedded_engine()
            elif source_type == DataSourceType.REAL_DATABASE:
                return self._create_real_database_engine()
            elif source_type == DataSourceType.SYNTHETIC_REALISTIC:
                return self._create_synthetic_engine()
            else:  # SIMPLE_FALLBACK
                return self._create_fallback_engine()

        except Exception as e:
            logger.error(f"엔진 인스턴스 생성 실패: {source_type.value}, {e}")
            return None

    def _create_embedded_engine(self) -> Any:
        """내장 최적화 엔진 생성"""
        try:
            # 전략 시뮬레이션 전용 내장 엔진
            from upbit_auto_trading.infrastructure.simulation.embedded_strategy_engine import EmbeddedStrategyEngine
            return EmbeddedStrategyEngine()

        except ImportError:
            logger.warning("내장 엔진 모듈을 찾을 수 없습니다. 기본 엔진으로 대체")
            return self._create_basic_engine("embedded")

    def _create_real_database_engine(self) -> Any:
        """실제 DB 엔진 생성"""
        try:
            # 전략 시뮬레이션 전용 DB 엔진
            from upbit_auto_trading.infrastructure.simulation.real_data_strategy_engine import RealDataStrategyEngine
            return RealDataStrategyEngine()

        except ImportError:
            logger.warning("실제 DB 엔진 모듈을 찾을 수 없습니다. 기본 엔진으로 대체")
            return self._create_basic_engine("real_db")

    def _create_synthetic_engine(self) -> Any:
        """합성 엔진 생성"""
        try:
            # 전략 시뮬레이션 전용 합성 엔진
            from upbit_auto_trading.infrastructure.simulation.synthetic_strategy_engine import SyntheticStrategyEngine
            return SyntheticStrategyEngine()

        except ImportError:
            logger.warning("합성 엔진 모듈을 찾을 수 없습니다. 기본 엔진으로 대체")
            return self._create_basic_engine("synthetic")

    def _create_fallback_engine(self) -> Any:
        """폴백 엔진 생성"""
        return self._create_basic_engine("fallback")

    def _create_basic_engine(self, engine_type: str) -> Any:
        """기본 엔진 생성 (폴백용)"""
        class BasicSimulationEngine:
            """기본 시뮬레이션 엔진 (폴백용)"""

            def __init__(self, engine_type: str):
                self.engine_type = engine_type
                self.capabilities = {
                    "scenario_optimization": engine_type == "embedded",
                    "real_time_data": False,
                    "historical_data": engine_type in ["embedded", "real_db"],
                    "custom_scenarios": engine_type in ["embedded", "synthetic"],
                    "high_performance": engine_type in ["embedded", "real_db"],
                    "data_validation": engine_type in ["embedded", "real_db"]
                }

            def get_scenario_data(self, scenario: str, length: int = 100) -> Dict[str, Any]:
                """기본 시나리오 데이터 반환"""
                import numpy as np

                base_value = 50000000
                data = np.random.randn(length) * base_value * 0.02 + base_value

                return {
                    'current_value': float(data[-1]),
                    'price_data': data.tolist(),
                    'scenario': scenario,
                    'data_source': f'basic_{self.engine_type}',
                    'period': 'generated_data',
                    'base_value': base_value,
                    'change_percent': (data[-1] / data[0] - 1) * 100
                }

            def cleanup(self):
                """리소스 정리"""
                pass

        logger.debug(f"기본 엔진 생성: {engine_type}")
        return BasicSimulationEngine(engine_type)

    def get_all_engine_status(self) -> Dict[str, Dict[str, Any]]:
        """모든 엔진의 상태 정보 반환"""
        status = {}

        for source_type in DataSourceType.get_all_types():
            cache_key = f"engine_{source_type.value}"

            status[source_type.value] = {
                "cached": cache_key in self._engine_cache,
                "capabilities": self.get_engine_capabilities(source_type),
                "source_type": source_type.value,
                "display_name": DataSourceType.get_display_name(source_type)
            }

        return status

    def clear_all_engine_cache(self) -> None:
        """모든 엔진 캐시 정리"""
        try:
            for source_type in DataSourceType.get_all_types():
                self.cleanup_engine_resources(source_type)

            self._engine_cache.clear()
            logger.debug("모든 엔진 캐시 정리 완료")

        except Exception as e:
            logger.error(f"엔진 캐시 정리 실패: {e}")

    def validate_engine_availability(self, source_type: DataSourceType) -> bool:
        """엔진 사용 가능성 검증"""
        try:
            # 테스트 엔진 생성 시도
            test_engine = self._create_engine_instance(source_type)

            if test_engine is None:
                return False

            # 기본 기능 테스트
            if hasattr(test_engine, 'get_scenario_data'):
                # 테스트 시나리오 실행
                test_result = test_engine.get_scenario_data("테스트", 10)
                return test_result is not None

            return True

        except Exception as e:
            logger.error(f"엔진 가용성 검증 실패: {source_type.value}, {e}")
            return False
