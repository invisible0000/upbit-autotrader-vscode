"""
전략 시뮬레이션 데이터 Repository 구현체
SQLite 기반 실제 마켓 데이터 및 내장 데이터 관리
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from upbit_auto_trading.domain.strategy_simulation.entities.data_source import DataSource
from upbit_auto_trading.domain.strategy_simulation.value_objects.data_source_type import DataSourceType
from upbit_auto_trading.domain.strategy_simulation.value_objects.simulation_scenario import SimulationScenario
from upbit_auto_trading.domain.strategy_simulation.repositories.i_strategy_simulation_repository import (
    IStrategySimulationDataRepository
)
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("StrategySimulationDataRepository")


class StrategySimulationDataRepository(IStrategySimulationDataRepository):
    """
    전략 시뮬레이션 데이터 Repository 구현체

    전략 관리 전용 미니 시뮬레이션 데이터 관리
    실제 백테스팅과는 별개의 Infrastructure
    """

    def __init__(self, market_data_db_path: str = "data/market_data.sqlite3"):
        """
        Repository 초기화

        Args:
            market_data_db_path: 마켓 데이터 SQLite DB 경로
        """
        self.market_data_db_path = market_data_db_path
        self._sampled_data_cache: Dict[str, pd.DataFrame] = {}
        self._embedded_datasets: Dict[str, Dict[str, Any]] = {}

        logger.debug(f"전략 시뮬레이션 데이터 Repository 초기화: {market_data_db_path}")

        # 내장 데이터셋 생성
        self._initialize_embedded_datasets()

    def get_available_data_sources(self) -> List[DataSource]:
        """사용 가능한 데이터 소스 목록 반환"""
        sources = []

        # 1. 내장 최적화 데이터셋 (항상 사용 가능)
        sources.append(DataSource(
            source_type=DataSourceType.EMBEDDED_OPTIMIZED,
            name=DataSourceType.get_display_name(DataSourceType.EMBEDDED_OPTIMIZED),
            description=DataSourceType.get_description(DataSourceType.EMBEDDED_OPTIMIZED),
            is_available=True,
            metadata={"quality": "high", "scenarios": 6, "optimized": True}
        ))

        # 2. 실제 DB 데이터 확인
        real_db_available = self._check_real_database_availability()
        sources.append(DataSource(
            source_type=DataSourceType.REAL_DATABASE,
            name=DataSourceType.get_display_name(DataSourceType.REAL_DATABASE),
            description=DataSourceType.get_description(DataSourceType.REAL_DATABASE),
            is_available=real_db_available,
            metadata={"quality": "high" if real_db_available else "unavailable", "source": "upbit"}
        ))

        # 3. 합성 현실적 데이터 (항상 사용 가능)
        sources.append(DataSource(
            source_type=DataSourceType.SYNTHETIC_REALISTIC,
            name=DataSourceType.get_display_name(DataSourceType.SYNTHETIC_REALISTIC),
            description=DataSourceType.get_description(DataSourceType.SYNTHETIC_REALISTIC),
            is_available=True,
            metadata={"quality": "medium", "synthetic": True}
        ))

        # 4. 단순 폴백 (항상 사용 가능)
        sources.append(DataSource(
            source_type=DataSourceType.SIMPLE_FALLBACK,
            name=DataSourceType.get_display_name(DataSourceType.SIMPLE_FALLBACK),
            description=DataSourceType.get_description(DataSourceType.SIMPLE_FALLBACK),
            is_available=True,
            metadata={"quality": "low", "fallback": True}
        ))

        logger.debug(f"사용 가능한 데이터 소스: {len(sources)}개")
        return sources

    def get_data_source_by_type(self, source_type: DataSourceType) -> Optional[DataSource]:
        """타입별 데이터 소스 조회"""
        sources = self.get_available_data_sources()
        for source in sources:
            if source.source_type == source_type:
                return source
        return None

    def check_data_source_availability(self, source_type: DataSourceType) -> bool:
        """데이터 소스 사용 가능 여부 확인"""
        if source_type == DataSourceType.REAL_DATABASE:
            return self._check_real_database_availability()
        else:
            # 다른 소스들은 항상 사용 가능
            return True

    def load_scenario_data(
        self,
        scenario: SimulationScenario,
        source_type: DataSourceType,
        data_length: int = 100
    ) -> Optional[pd.DataFrame]:
        """시나리오별 시뮬레이션 데이터 로드"""
        try:
            if source_type == DataSourceType.EMBEDDED_OPTIMIZED:
                return self._load_embedded_scenario_data(scenario, data_length)
            elif source_type == DataSourceType.REAL_DATABASE:
                return self._load_real_database_scenario_data(scenario, data_length)
            elif source_type == DataSourceType.SYNTHETIC_REALISTIC:
                return self._load_synthetic_scenario_data(scenario, data_length)
            else:  # SIMPLE_FALLBACK
                return self._load_fallback_scenario_data(scenario, data_length)

        except Exception as e:
            logger.error(f"시나리오 데이터 로드 실패: {scenario.value}, {source_type.value}, {e}")
            return None

    def get_scenario_metadata(
        self,
        scenario: SimulationScenario,
        source_type: DataSourceType
    ) -> Dict[str, Any]:
        """시나리오 메타데이터 조회"""
        base_metadata = {
            "scenario": scenario.value,
            "source_type": source_type.value,
            "risk_level": scenario.get_risk_level(),
            "scenario_color": SimulationScenario.get_scenario_color(scenario),
            "description": SimulationScenario.get_scenario_description(scenario)
        }

        # 소스별 추가 메타데이터
        if source_type == DataSourceType.EMBEDDED_OPTIMIZED:
            base_metadata.update({
                "quality": "high",
                "optimized_for_scenario": True,
                "data_source": "embedded_optimized"
            })
        elif source_type == DataSourceType.REAL_DATABASE:
            base_metadata.update({
                "quality": "high",
                "real_market_data": True,
                "data_source": "upbit_historical"
            })

        return base_metadata

    def validate_data_integrity(self, source_type: DataSourceType) -> bool:
        """데이터 무결성 검증"""
        try:
            # 각 소스별 검증 로직
            if source_type == DataSourceType.REAL_DATABASE:
                return self._validate_real_database_integrity()
            elif source_type == DataSourceType.EMBEDDED_OPTIMIZED:
                return self._validate_embedded_data_integrity()
            else:
                # 합성/폴백 데이터는 생성 시점 검증
                return True

        except Exception as e:
            logger.error(f"데이터 무결성 검증 실패: {source_type.value}, {e}")
            return False

    def _check_real_database_availability(self) -> bool:
        """실제 DB 사용 가능 여부 확인"""
        try:
            if not os.path.exists(self.market_data_db_path):
                logger.warning(f"마켓 데이터 DB 파일 없음: {self.market_data_db_path}")
                return False

            # DB 연결 테스트
            with sqlite3.connect(self.market_data_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

                if not tables:
                    logger.warning("마켓 데이터 DB에 테이블이 없습니다")
                    return False

                logger.debug(f"실제 DB 사용 가능: {len(tables)}개 테이블")
                return True

        except Exception as e:
            logger.error(f"실제 DB 가용성 확인 실패: {e}")
            return False

    def _initialize_embedded_datasets(self) -> None:
        """내장 데이터셋 초기화"""
        np.random.seed(42)  # 일관된 결과
        base_price = 50000000  # 5천만원 기준

        # 시나리오별 최적화된 데이터셋 생성
        for scenario in SimulationScenario.get_all_scenarios():
            self._embedded_datasets[scenario.value] = self._create_optimized_dataset(
                scenario, base_price, 180
            )

        logger.debug(f"내장 데이터셋 초기화 완료: {len(self._embedded_datasets)}개 시나리오")

    def _create_optimized_dataset(
        self,
        scenario: SimulationScenario,
        base_price: float,
        length: int
    ) -> Dict[str, Any]:
        """시나리오별 최적화된 데이터셋 생성"""
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=length),
            periods=length,
            freq='D'
        )

        if scenario == SimulationScenario.UPTREND:
            # 점진적 상승 + 노이즈
            trend = np.linspace(0, base_price * 0.3, length)
            noise = np.random.randn(length) * base_price * 0.02
            prices = base_price + trend + noise

        elif scenario == SimulationScenario.DOWNTREND:
            # 점진적 하락 + 노이즈
            trend = np.linspace(0, -base_price * 0.2, length)
            noise = np.random.randn(length) * base_price * 0.015
            prices = base_price + trend + noise

        elif scenario == SimulationScenario.SIDEWAYS:
            # 범위 내 횡보
            center = base_price
            range_size = base_price * 0.1
            noise = np.random.randn(length) * range_size * 0.3
            sine_wave = np.sin(np.linspace(0, 4*np.pi, length)) * range_size * 0.5
            prices = center + sine_wave + noise

        elif scenario == SimulationScenario.HIGH_VOLATILITY:
            # 높은 변동성
            noise = np.random.randn(length) * base_price * 0.05
            volatility_spikes = np.random.choice([-1, 1], length) * np.random.exponential(0.02, length) * base_price
            prices = base_price + noise + volatility_spikes

        elif scenario == SimulationScenario.SURGE:
            # 급등 패턴
            surge_point = length // 3
            trend = np.concatenate([
                np.zeros(surge_point),
                np.linspace(0, base_price * 0.4, surge_point),
                np.full(length - 2*surge_point, base_price * 0.4)
            ])
            noise = np.random.randn(length) * base_price * 0.015
            prices = base_price + trend + noise

        else:  # CRASH
            # 급락 패턴
            crash_point = length // 2
            trend = np.concatenate([
                np.zeros(crash_point),
                np.linspace(0, -base_price * 0.3, length - crash_point)
            ])
            noise = np.random.randn(length) * base_price * 0.02
            prices = base_price + trend + noise

        # 가격이 0 이하로 떨어지지 않도록
        prices = np.maximum(prices, base_price * 0.1)

        # DataFrame 생성
        df = pd.DataFrame({
            'datetime': dates,
            'open': prices * (1 + np.random.randn(length) * 0.001),
            'high': prices * (1 + abs(np.random.randn(length)) * 0.002),
            'low': prices * (1 - abs(np.random.randn(length)) * 0.002),
            'close': prices,
            'volume': np.random.lognormal(15, 0.5, length)
        })

        df.set_index('datetime', inplace=True)

        return {
            'dataframe': df,
            'scenario': scenario.value,
            'base_price': base_price,
            'optimization': 'scenario_specific',
            'quality_score': 0.95
        }

    def _load_embedded_scenario_data(self, scenario: SimulationScenario, data_length: int) -> Optional[pd.DataFrame]:
        """내장 시나리오 데이터 로드"""
        dataset = self._embedded_datasets.get(scenario.value)
        if not dataset:
            logger.warning(f"내장 데이터셋 없음: {scenario.value}")
            return None

        df = dataset['dataframe'].copy()

        # 요청된 길이에 맞게 조정
        if len(df) > data_length:
            df = df.tail(data_length)

        logger.debug(f"내장 시나리오 데이터 로드: {scenario.value}, {len(df)}개 포인트")
        return df

    def _load_real_database_scenario_data(self, scenario: SimulationScenario, data_length: int) -> Optional[pd.DataFrame]:
        """실제 DB 시나리오 데이터 로드"""
        if not self._check_real_database_availability():
            return None

        try:
            with sqlite3.connect(self.market_data_db_path) as conn:
                # 기본 쿼리 (KRW-BTC 일봉 데이터)
                query = """
                SELECT datetime, open, high, low, close, volume
                FROM daily_candles
                WHERE symbol = 'KRW-BTC'
                ORDER BY datetime DESC
                LIMIT ?
                """

                df = pd.read_sql_query(query, conn, params=[data_length * 2])

                if df.empty:
                    logger.warning("실제 DB에서 데이터를 찾을 수 없습니다")
                    return None

                df['datetime'] = pd.to_datetime(df['datetime'])
                df.set_index('datetime', inplace=True)
                df = df.sort_index()

                # 시나리오에 맞는 데이터 세그멘테이션
                df = self._apply_scenario_segmentation(df, scenario, data_length)

                logger.debug(f"실제 DB 시나리오 데이터 로드: {scenario.value}, {len(df)}개 포인트")
                return df

        except Exception as e:
            logger.error(f"실제 DB 데이터 로드 실패: {e}")
            return None

    def _apply_scenario_segmentation(self, df: pd.DataFrame, scenario: SimulationScenario, target_length: int) -> pd.DataFrame:
        """시나리오에 맞는 데이터 세그멘테이션"""
        if len(df) <= target_length:
            return df

        close_prices = df['close']

        if scenario == SimulationScenario.UPTREND:
            # 상승 구간 찾기
            rolling_returns = close_prices.pct_change(20).rolling(20).mean()
            uptrend_mask = rolling_returns > 0.02  # 2% 이상 상승

        elif scenario == SimulationScenario.DOWNTREND:
            # 하락 구간 찾기
            rolling_returns = close_prices.pct_change(20).rolling(20).mean()
            uptrend_mask = rolling_returns < -0.02  # 2% 이상 하락

        elif scenario == SimulationScenario.HIGH_VOLATILITY:
            # 높은 변동성 구간 찾기
            volatility = close_prices.pct_change().rolling(20).std()
            uptrend_mask = volatility > volatility.quantile(0.8)

        else:
            # 기타 시나리오는 무작위 구간
            start_idx = np.random.randint(0, max(1, len(df) - target_length))
            return df.iloc[start_idx:start_idx + target_length]

        # 조건에 맞는 구간 선택
        valid_indices = df.index[uptrend_mask]
        if len(valid_indices) >= target_length:
            start_idx = np.random.choice(len(valid_indices) - target_length + 1)
            selected_indices = valid_indices[start_idx:start_idx + target_length]
            return df.loc[selected_indices]
        else:
            # 조건 만족 구간이 부족하면 끝에서부터
            return df.tail(target_length)

    def _load_synthetic_scenario_data(self, scenario: SimulationScenario, data_length: int) -> Optional[pd.DataFrame]:
        """합성 시나리오 데이터 로드"""
        # 내장 데이터를 기반으로 노이즈 추가
        embedded_data = self._load_embedded_scenario_data(scenario, data_length)
        if embedded_data is None:
            return None

        # 합성 노이즈 추가
        synthetic_df = embedded_data.copy()
        noise_factor = 0.01  # 1% 노이즈

        for col in ['open', 'high', 'low', 'close']:
            noise = np.random.randn(len(synthetic_df)) * noise_factor
            synthetic_df[col] = synthetic_df[col] * (1 + noise)

        # 볼륨 재생성
        synthetic_df['volume'] = np.random.lognormal(15, 0.3, len(synthetic_df))

        logger.debug(f"합성 시나리오 데이터 생성: {scenario.value}, {len(synthetic_df)}개 포인트")
        return synthetic_df

    def _load_fallback_scenario_data(self, scenario: SimulationScenario, data_length: int) -> Optional[pd.DataFrame]:
        """폴백 시나리오 데이터 로드"""
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=data_length),
            periods=data_length,
            freq='D'
        )

        base_price = 50000000

        # 단순한 시나리오 패턴
        if scenario == SimulationScenario.UPTREND:
            trend = np.linspace(base_price, base_price * 1.1, data_length)
        elif scenario == SimulationScenario.DOWNTREND:
            trend = np.linspace(base_price, base_price * 0.9, data_length)
        else:
            trend = np.full(data_length, base_price)

        # 기본 노이즈
        noise = np.random.randn(data_length) * base_price * 0.01
        prices = trend + noise
        prices = np.maximum(prices, base_price * 0.1)

        df = pd.DataFrame({
            'datetime': dates,
            'open': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': np.random.lognormal(14, 0.2, data_length)
        })

        df.set_index('datetime', inplace=True)

        logger.debug(f"폴백 시나리오 데이터 생성: {scenario.value}, {len(df)}개 포인트")
        return df

    def _validate_real_database_integrity(self) -> bool:
        """실제 DB 무결성 검증"""
        try:
            with sqlite3.connect(self.market_data_db_path) as conn:
                cursor = conn.cursor()

                # 기본 테이블 존재 확인
                cursor.execute("SELECT COUNT(*) FROM daily_candles WHERE symbol = 'KRW-BTC'")
                count = cursor.fetchone()[0]

                if count < 100:  # 최소 100개 레코드 필요
                    logger.warning(f"실제 DB 데이터 부족: {count}개 레코드")
                    return False

                # 데이터 품질 확인
                cursor.execute("""
                    SELECT COUNT(*) FROM daily_candles
                    WHERE symbol = 'KRW-BTC'
                    AND (close IS NULL OR close <= 0 OR high < low)
                """)
                invalid_count = cursor.fetchone()[0]

                if invalid_count > count * 0.05:  # 5% 이상 무효 데이터
                    logger.warning(f"실제 DB 품질 문제: {invalid_count}개 무효 레코드")
                    return False

                return True

        except Exception as e:
            logger.error(f"실제 DB 무결성 검증 실패: {e}")
            return False

    def _validate_embedded_data_integrity(self) -> bool:
        """내장 데이터 무결성 검증"""
        required_scenarios = len(SimulationScenario.get_all_scenarios())
        available_scenarios = len(self._embedded_datasets)

        if available_scenarios != required_scenarios:
            logger.warning(f"내장 데이터셋 불완전: {available_scenarios}/{required_scenarios}")
            return False

        # 각 데이터셋 품질 확인
        for scenario_name, dataset in self._embedded_datasets.items():
            df = dataset.get('dataframe')
            if df is None or df.empty:
                logger.warning(f"내장 데이터셋 비어있음: {scenario_name}")
                return False

            # 필수 컬럼 확인
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"내장 데이터셋 컬럼 누락: {scenario_name}")
                return False

        return True
