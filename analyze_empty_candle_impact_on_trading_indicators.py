"""
빈 캔들 처리가 매매 지표에 미치는 영향 분석
이동평균, RSI, MACD 등 핵심 지표의 정확성 검증
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt

class TradingIndicatorImpactAnalyzer:
    """매매 지표에 대한 빈 캔들 영향 분석기"""

    def __init__(self):
        self.test_scenarios = []

    def create_test_scenarios(self) -> List[Dict]:
        """다양한 빈 캔들 시나리오 생성"""

        # 기본 가격 데이터 (실제 거래가 있는 캔들)
        base_prices = [
            50000, 50500, 51000, 49500, 48000,  # 5개 실제 캔들
            49000, 50200, 51500, 52000, 50800   # 5개 더 실제 캔들
        ]

        scenarios = []

        # 시나리오 1: 빈 캔들 없음 (순수 데이터)
        scenarios.append({
            'name': '빈캔들_없음_순수데이터',
            'data': self._create_pure_candles(base_prices),
            'description': '모든 시간대에 실제 거래가 있는 경우'
        })

        # 시나리오 2: 중간에 2개 빈 캔들 (마지막 가격으로 채움)
        scenarios.append({
            'name': '빈캔들_2개_마지막가격채움',
            'data': self._create_candles_with_gaps(base_prices, gap_positions=[3, 4], fill_method='last_price'),
            'description': '중간 2개 시간대 거래 없음 - 마지막 가격으로 채움'
        })

        # 시나리오 3: 중간에 2개 빈 캔들 (선형 보간)
        scenarios.append({
            'name': '빈캔들_2개_선형보간',
            'data': self._create_candles_with_gaps(base_prices, gap_positions=[3, 4], fill_method='interpolation'),
            'description': '중간 2개 시간대 거래 없음 - 선형 보간'
        })

        # 시나리오 4: 빈 캔들 제거 (시간 압축)
        scenarios.append({
            'name': '빈캔들_제거_시간압축',
            'data': self._create_candles_with_gaps(base_prices, gap_positions=[3, 4], fill_method='remove'),
            'description': '빈 캔들 완전 제거 (시간축 압축)'
        })

        # 시나리오 5: 연속 5개 빈 캔들 (극단적 경우)
        scenarios.append({
            'name': '빈캔들_5개연속_마지막가격',
            'data': self._create_candles_with_gaps(base_prices, gap_positions=[2, 3, 4, 5, 6], fill_method='last_price'),
            'description': '연속 5개 시간대 거래 없음 - 마지막 가격으로 채움'
        })

        return scenarios

    def _create_pure_candles(self, prices: List[float]) -> pd.DataFrame:
        """순수한 캔들 데이터 생성"""
        data = []
        base_time = datetime(2025, 8, 22, 10, 0, 0)

        for i, price in enumerate(prices):
            # 각 캔들마다 약간의 변동성 추가
            high = price * (1 + np.random.uniform(0.001, 0.01))
            low = price * (1 - np.random.uniform(0.001, 0.01))
            close = price + np.random.uniform(-100, 100)
            volume = np.random.uniform(10, 100)

            data.append({
                'timestamp': base_time + timedelta(minutes=i),
                'open': price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume,
                'is_real_trade': True
            })

        return pd.DataFrame(data)

    def _create_candles_with_gaps(self, prices: List[float], gap_positions: List[int],
                                 fill_method: str) -> pd.DataFrame:
        """빈 캔들이 있는 데이터 생성"""
        data = []
        base_time = datetime(2025, 8, 22, 10, 0, 0)
        last_real_price = None

        for i in range(len(prices) + len(gap_positions)):
            timestamp = base_time + timedelta(minutes=i)

            if i in gap_positions:
                # 빈 캔들 처리
                if fill_method == 'last_price' and last_real_price is not None:
                    # 마지막 거래 가격으로 채움
                    data.append({
                        'timestamp': timestamp,
                        'open': last_real_price,
                        'high': last_real_price,
                        'low': last_real_price,
                        'close': last_real_price,
                        'volume': 0,
                        'is_real_trade': False
                    })
                elif fill_method == 'interpolation':
                    # 선형 보간 (단순화)
                    if last_real_price is not None:
                        next_price = prices[min(len(prices)-1, i - len([g for g in gap_positions if g <= i]))]
                        interpolated = (last_real_price + next_price) / 2
                        data.append({
                            'timestamp': timestamp,
                            'open': interpolated,
                            'high': interpolated,
                            'low': interpolated,
                            'close': interpolated,
                            'volume': 0,
                            'is_real_trade': False
                        })
                elif fill_method == 'remove':
                    # 빈 캔들 제거 (데이터에 추가하지 않음)
                    continue
            else:
                # 실제 거래 캔들
                price_idx = i - len([g for g in gap_positions if g <= i])
                if price_idx < len(prices):
                    price = prices[price_idx]
                    high = price * (1 + np.random.uniform(0.001, 0.01))
                    low = price * (1 - np.random.uniform(0.001, 0.01))
                    close = price + np.random.uniform(-100, 100)
                    volume = np.random.uniform(10, 100)

                    data.append({
                        'timestamp': timestamp,
                        'open': price,
                        'high': high,
                        'low': low,
                        'close': close,
                        'volume': volume,
                        'is_real_trade': True
                    })

                    last_real_price = close

        return pd.DataFrame(data)

    def calculate_sma(self, df: pd.DataFrame, period: int = 5) -> pd.Series:
        """단순 이동평균 계산"""
        return df['close'].rolling(window=period, min_periods=1).mean()

    def calculate_ema(self, df: pd.DataFrame, period: int = 5) -> pd.Series:
        """지수 이동평균 계산"""
        return df['close'].ewm(span=period).mean()

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """RSI 계산"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 5, std_dev: int = 2) -> Dict:
        """볼린저 밴드 계산"""
        sma = self.calculate_sma(df, period)
        std = df['close'].rolling(window=period).std()

        return {
            'upper': sma + (std * std_dev),
            'middle': sma,
            'lower': sma - (std * std_dev)
        }

    def analyze_indicator_differences(self, scenarios: List[Dict]) -> Dict:
        """시나리오별 지표 차이 분석"""
        results = {}

        # 기준 시나리오 (빈 캔들 없음)
        base_scenario = scenarios[0]
        base_df = base_scenario['data']

        base_indicators = {
            'sma': self.calculate_sma(base_df),
            'ema': self.calculate_ema(base_df),
            'rsi': self.calculate_rsi(base_df),
            'bb': self.calculate_bollinger_bands(base_df)
        }

        # 다른 시나리오들과 비교
        for scenario in scenarios[1:]:
            df = scenario['data']

            indicators = {
                'sma': self.calculate_sma(df),
                'ema': self.calculate_ema(df),
                'rsi': self.calculate_rsi(df),
                'bb': self.calculate_bollinger_bands(df)
            }

            # 차이 계산
            differences = {}

            # SMA 차이
            if len(indicators['sma']) >= len(base_indicators['sma']):
                sma_diff = np.abs(indicators['sma'][:len(base_indicators['sma'])] - base_indicators['sma'])
            else:
                sma_diff = np.abs(indicators['sma'] - base_indicators['sma'][:len(indicators['sma'])])

            differences['sma_max_diff'] = sma_diff.max()
            differences['sma_mean_diff'] = sma_diff.mean()

            # EMA 차이
            if len(indicators['ema']) >= len(base_indicators['ema']):
                ema_diff = np.abs(indicators['ema'][:len(base_indicators['ema'])] - base_indicators['ema'])
            else:
                ema_diff = np.abs(indicators['ema'] - base_indicators['ema'][:len(indicators['ema'])])

            differences['ema_max_diff'] = ema_diff.max()
            differences['ema_mean_diff'] = ema_diff.mean()

            # RSI 차이 (NaN 제외)
            base_rsi_clean = base_indicators['rsi'].dropna()
            test_rsi_clean = indicators['rsi'].dropna()

            if len(test_rsi_clean) > 0 and len(base_rsi_clean) > 0:
                min_len = min(len(base_rsi_clean), len(test_rsi_clean))
                rsi_diff = np.abs(test_rsi_clean[:min_len].values - base_rsi_clean[:min_len].values)
                differences['rsi_max_diff'] = np.max(rsi_diff)
                differences['rsi_mean_diff'] = np.mean(rsi_diff)
            else:
                differences['rsi_max_diff'] = 0
                differences['rsi_mean_diff'] = 0

            results[scenario['name']] = {
                'differences': differences,
                'description': scenario['description'],
                'data_length': len(df),
                'real_trades_count': len(df[df['is_real_trade'] == True]),
                'fake_candles_count': len(df[df['is_real_trade'] == False])
            }

        return results

    def generate_report(self, analysis_results: Dict) -> str:
        """분석 결과 리포트 생성"""
        report = []
        report.append("=" * 80)
        report.append("📊 빈 캔들 처리가 매매 지표에 미치는 영향 분석 리포트")
        report.append("=" * 80)

        for scenario_name, result in analysis_results.items():
            report.append(f"\n🔍 시나리오: {scenario_name}")
            report.append(f"   설명: {result['description']}")
            report.append(f"   전체 캔들: {result['data_length']}개")
            report.append(f"   실제 거래: {result['real_trades_count']}개")
            report.append(f"   빈 캔들: {result['fake_candles_count']}개")

            diff = result['differences']
            report.append(f"\n   📈 지표별 편차:")
            report.append(f"      SMA - 최대편차: {diff['sma_max_diff']:.2f}, 평균편차: {diff['sma_mean_diff']:.2f}")
            report.append(f"      EMA - 최대편차: {diff['ema_max_diff']:.2f}, 평균편차: {diff['ema_mean_diff']:.2f}")
            report.append(f"      RSI - 최대편차: {diff['rsi_max_diff']:.2f}, 평균편차: {diff['rsi_mean_diff']:.2f}")

            # 위험도 평가
            if diff['sma_max_diff'] > 500 or diff['ema_max_diff'] > 500:
                report.append(f"      ⚠️ 위험: 이동평균 편차가 큼 (매매 신호 왜곡 가능성)")

            if diff['rsi_max_diff'] > 10:
                report.append(f"      ⚠️ 위험: RSI 편차가 큼 (과매수/과매도 신호 왜곡 가능성)")

            if diff['sma_max_diff'] < 100 and diff['ema_max_diff'] < 100 and diff['rsi_max_diff'] < 5:
                report.append(f"      ✅ 안전: 지표 편차가 작음 (매매에 미치는 영향 미미)")

        report.append(f"\n" + "=" * 80)
        report.append("💡 권장사항:")
        report.append("   1. 차트 시각화용과 매매 계산용 데이터 분리 고려")
        report.append("   2. 빈 캔들은 차트에만 사용, 지표 계산에서는 제외")
        report.append("   3. 지표 계산 시 실제 거래 캔들만 사용하는 옵션 제공")
        report.append("=" * 80)

        return "\n".join(report)

def main():
    """분석 실행"""
    print("🔍 빈 캔들이 매매 지표에 미치는 영향 분석 시작...")

    analyzer = TradingIndicatorImpactAnalyzer()

    # 시나리오 생성
    scenarios = analyzer.create_test_scenarios()
    print(f"📋 생성된 시나리오: {len(scenarios)}개")

    # 분석 실행
    analysis_results = analyzer.analyze_indicator_differences(scenarios)

    # 리포트 생성
    report = analyzer.generate_report(analysis_results)
    print(report)

    # 시각화 (선택적)
    create_comparison_charts(scenarios, analyzer)

def create_comparison_charts(scenarios: List[Dict], analyzer: TradingIndicatorImpactAnalyzer):
    """비교 차트 생성"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('빈 캔들 처리 방식별 지표 비교', fontsize=16)

    colors = ['blue', 'red', 'green', 'orange', 'purple']

    for i, scenario in enumerate(scenarios[:3]):  # 처음 3개 시나리오만
        df = scenario['data']
        color = colors[i]
        label = scenario['name']

        # 가격 차트
        axes[0, 0].plot(df.index, df['close'], color=color, label=label, alpha=0.7)
        axes[0, 0].set_title('종가 비교')
        axes[0, 0].legend()

        # SMA 비교
        sma = analyzer.calculate_sma(df)
        axes[0, 1].plot(df.index, sma, color=color, label=label, alpha=0.7)
        axes[0, 1].set_title('SMA(5) 비교')
        axes[0, 1].legend()

        # EMA 비교
        ema = analyzer.calculate_ema(df)
        axes[1, 0].plot(df.index, ema, color=color, label=label, alpha=0.7)
        axes[1, 0].set_title('EMA(5) 비교')
        axes[1, 0].legend()

        # RSI 비교
        rsi = analyzer.calculate_rsi(df)
        axes[1, 1].plot(df.index, rsi, color=color, label=label, alpha=0.7)
        axes[1, 1].set_title('RSI(14) 비교')
        axes[1, 1].axhline(y=70, color='red', linestyle='--', alpha=0.5)
        axes[1, 1].axhline(y=30, color='green', linestyle='--', alpha=0.5)
        axes[1, 1].legend()

    plt.tight_layout()
    plt.savefig('empty_candle_impact_analysis.png', dpi=300, bbox_inches='tight')
    print("📊 비교 차트 저장됨: empty_candle_impact_analysis.png")

if __name__ == "__main__":
    main()
