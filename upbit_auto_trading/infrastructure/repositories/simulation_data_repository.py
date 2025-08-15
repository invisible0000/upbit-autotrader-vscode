"""
시뮬레이션 데이터 Repository
DDD Infrastructure Layer - 실제 마켓 데이터 액세스
"""

import sqlite3
import pandas as pd
import os
from typing import Optional, Dict, Any, List
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("SimulationDataRepository")


class SimulationDataRepository:
    """시뮬레이션용 마켓 데이터 Repository"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Repository 초기화

        Args:
            db_path: DB 경로 (None이면 기본 경로 사용)
        """
        if db_path is None:
            # 내장 시뮬레이션 데이터 경로 (Infrastructure Layer)
            self.db_path = os.path.join(
                os.path.dirname(__file__), "..", "simulation", "data",
                "sampled_market_data.sqlite3"
            )
        else:
            self.db_path = db_path

        self._verify_database()
        logger.info(f"SimulationDataRepository 초기화 완료: {self.db_path}")

    def _verify_database(self) -> bool:
        """데이터베이스 존재 및 구조 확인"""
        try:
            if not os.path.exists(self.db_path):
                logger.error(f"DB 파일이 존재하지 않음: {self.db_path}")
                return False

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # market_data 테이블 존재 확인
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='market_data'
                """)
                if not cursor.fetchone():
                    logger.error("market_data 테이블이 존재하지 않음")
                    return False

                # 데이터 개수 확인
                cursor.execute("SELECT COUNT(*) FROM market_data WHERE symbol = 'KRW-BTC'")
                count = cursor.fetchone()[0]
                logger.info(f"KRW-BTC 데이터 레코드 수: {count}개")

                return count > 0

        except Exception as e:
            logger.error(f"데이터베이스 검증 실패: {e}")
            return False

    def load_market_data(self, symbol: str = "KRW-BTC", timeframe: str = "1d",
                        limit: int = 500) -> Optional[pd.DataFrame]:
        """
        시장 데이터 로드

        Args:
            symbol: 심볼 (기본: KRW-BTC)
            timeframe: 시간틀 (기본: 1d)
            limit: 제한 개수

        Returns:
            DataFrame 또는 None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT
                    timestamp,
                    open,
                    high,
                    low,
                    close,
                    volume
                FROM market_data
                WHERE symbol = ? AND timeframe = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """

                df = pd.read_sql_query(query, conn, params=[symbol, timeframe, limit])

                if df.empty:
                    logger.warning(f"데이터 없음: {symbol}, {timeframe}")
                    return None

                # 데이터 전처리
                df = df.sort_values('timestamp').reset_index(drop=True)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')

                # 숫자형 변환
                numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_cols:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                logger.debug(f"마켓 데이터 로드 완료: {len(df)}개")
                return df

        except Exception as e:
            logger.error(f"마켓 데이터 로드 실패: {e}")
            return None

    def load_scenario_data(self, scenario: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """
        시나리오별 데이터 로드 (Legacy 세그먼테이션 활용)

        Args:
            scenario: 시나리오명
            limit: 제한 개수

        Returns:
            시나리오에 맞는 DataFrame
        """
        # Legacy에서 정의된 시나리오 세그먼트
        scenario_segments = {
            '급등': {
                'date_range': ('2025-04-16', '2025-07-21'),
                'description': '급등 구간 (+31.39%, 121M→160M)'
            },
            '상승추세': {
                'date_range': ('2023-07-16', '2023-10-23'),
                'description': '상승 추세 구간 (+13.47%, 39M→44M)'
            },
            '횡보': {
                'date_range': ('2023-04-27', '2023-08-04'),
                'description': '횡보 구간 (-1.95%, 39M→38M)'
            },
            '하락추세': {
                'date_range': ('2023-07-06', '2023-10-13'),
                'description': '하락 추세 구간 (-7.26%, 40M→37M)'
            },
            '급락': {
                'date_range': ('2018-08-01', '2018-11-08'),
                'description': '급락 구간 (-16.55%, 8.7M→7.3M)'
            }
        }

        if scenario not in scenario_segments:
            logger.warning(f"알 수 없는 시나리오: {scenario}")
            return self.load_market_data(limit=limit)

        try:
            segment_info = scenario_segments[scenario]
            start_date, end_date = segment_info['date_range']

            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT
                    timestamp,
                    open,
                    high,
                    low,
                    close,
                    volume
                FROM market_data
                WHERE symbol = 'KRW-BTC' AND timeframe = '1d'
                AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
                LIMIT ?
                """

                df = pd.read_sql_query(query, conn, params=[start_date, end_date, limit])

                if df.empty:
                    logger.warning(f"시나리오 데이터 없음: {scenario}")
                    return self.load_market_data(limit=limit)

                # 데이터 전처리
                df = df.sort_values('timestamp').reset_index(drop=True)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')

                # 숫자형 변환
                numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_cols:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                logger.info(f"시나리오 데이터 로드: {scenario} ({len(df)}개)")
                return df

        except Exception as e:
            logger.error(f"시나리오 데이터 로드 실패 {scenario}: {e}")
            return self.load_market_data(limit=limit)

    def get_available_scenarios(self) -> List[str]:
        """사용 가능한 시나리오 목록 반환"""
        return ['급등', '상승추세', '횡보', '하락추세', '급락']

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 계산 (Infrastructure Layer 유틸리티)"""
        try:
            if df is None or df.empty:
                return df

            # RSI 계산
            def calculate_rsi(prices, period=14):
                delta = prices.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                return rsi

            # 이동평균 계산
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_60'] = df['close'].rolling(window=60).mean()

            # RSI 계산
            df['rsi'] = calculate_rsi(df['close'])

            # 변동성 계산
            df['volatility_30d'] = df['close'].pct_change().rolling(window=30).std() * 100

            # 수익률 계산
            df['return_7d'] = df['close'].pct_change(7) * 100
            df['return_30d'] = df['close'].pct_change(30) * 100

            logger.debug("기술적 지표 계산 완료")
            return df

        except Exception as e:
            logger.error(f"기술적 지표 계산 실패: {e}")
            return df

    def get_scenario_summary(self, scenario: str) -> Dict[str, Any]:
        """시나리오 요약 정보 반환"""
        try:
            df = self.load_scenario_data(scenario, limit=200)
            if df is None or df.empty:
                return {}

            df = self.calculate_technical_indicators(df)

            return {
                'scenario': scenario,
                'data_points': len(df),
                'date_range': f"{df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}",
                'price_range': {
                    'min': float(df['close'].min()),
                    'max': float(df['close'].max()),
                    'start': float(df['close'].iloc[0]),
                    'end': float(df['close'].iloc[-1])
                },
                'total_return': float((df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100),
                'volatility': float(df['close'].pct_change().std() * 100),
                'indicators': {
                    'rsi_avg': float(df['rsi'].mean()) if 'rsi' in df.columns else None,
                    'volume_avg': float(df['volume'].mean())
                }
            }

        except Exception as e:
            logger.error(f"시나리오 요약 생성 실패: {e}")
            return {}
