"""
실제 매매 시나리오에서 완성도 기반 캔들 처리 활용 예시
7규칙 전략에서 안전한 캔들 데이터 활용 방법
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from upbit_auto_trading.infrastructure.market_data_backbone.smart_data_provider.core.realtime_candle_manager import (
    RealtimeCandleManager
)


class SafeTradingSignalGenerator:
    """완성도 검증된 안전한 매매 신호 생성기"""

    def __init__(self):
        self.candle_manager = RealtimeCandleManager()

    async def generate_entry_signal(self, symbol: str, timeframe: str = "1m") -> Optional[Dict]:
        """
        진입 신호 생성 (완성된 캔들만 사용)

        7규칙 중 RSI 과매도 진입 예시
        """
        # 1. 최근 20개 완성된 캔들 필요 (RSI 계산용)
        completed_candles = await self._get_completed_candles(symbol, timeframe, count=20)

        if len(completed_candles) < 20:
            return {
                'signal': 'WAIT',
                'reason': f'완성된 캔들 부족 ({len(completed_candles)}/20)',
                'safe': False
            }

        # 2. RSI 계산 (완성된 데이터만 사용)
        rsi = self._calculate_rsi(completed_candles)

        # 3. 과매도 조건 확인
        if rsi < 30:
            # 4. 마지막 캔들의 완성도 API로 재확인 (중요한 신호이므로)
            latest_candle_time = self._parse_candle_time(completed_candles[0])
            is_api_confirmed = await self.candle_manager.verify_candle_with_api(
                symbol, timeframe, latest_candle_time
            )

            if is_api_confirmed:
                return {
                    'signal': 'BUY',
                    'reason': f'RSI 과매도 ({rsi:.1f}) + API 완성 확인',
                    'rsi': rsi,
                    'candle_time': latest_candle_time,
                    'safe': True,
                    'confidence': 'HIGH'
                }
            else:
                return {
                    'signal': 'WAIT',
                    'reason': f'RSI 과매도 ({rsi:.1f}) 하지만 API 미확인',
                    'safe': False,
                    'confidence': 'LOW'
                }

        return {
            'signal': 'HOLD',
            'reason': f'RSI 정상 범위 ({rsi:.1f})',
            'rsi': rsi,
            'safe': True
        }

    async def check_trailing_stop(self, symbol: str, entry_price: float,
                                current_position: str = "LONG") -> Dict:
        """
        트레일링 스탑 체크 (실시간 + 완성 데이터 조합)

        7규칙 중 트레일링 스탑 예시
        """
        # 1. 실시간 가격 (미완성 캔들 포함)
        latest_realtime = self.candle_manager.get_latest_candle(symbol, "1m")

        # 2. 완성된 캔들로 안전한 고점 확인
        completed_candles = await self._get_completed_candles(symbol, "1m", count=10)

        if not latest_realtime or not completed_candles:
            return {'action': 'HOLD', 'reason': '데이터 부족', 'safe': False}

        current_price = latest_realtime.get('trade_price', 0)

        # 완성된 캔들에서 최근 고점 찾기 (안전한 기준점)
        safe_high = max(candle.get('high_price', 0) for candle in completed_candles)

        # 트레일링 퍼센트 (5%)
        trailing_percent = 0.05
        stop_price = safe_high * (1 - trailing_percent)

        if current_position == "LONG" and current_price <= stop_price:
            # 중요한 청산 신호이므로 API로 재확인
            latest_time = self._parse_candle_time(latest_realtime)
            is_confirmed = await self.candle_manager.verify_candle_with_api(symbol, "1m", latest_time)

            return {
                'action': 'SELL',
                'reason': f'트레일링 스탑 발동: {current_price} <= {stop_price:.0f}',
                'current_price': current_price,
                'stop_price': stop_price,
                'safe_high': safe_high,
                'api_confirmed': is_confirmed,
                'safe': is_confirmed,
                'urgency': 'HIGH' if is_confirmed else 'MEDIUM'
            }

        return {
            'action': 'HOLD',
            'reason': f'트레일링 범위 내: {current_price} > {stop_price:.0f}',
            'current_price': current_price,
            'stop_price': stop_price,
            'margin': ((current_price - stop_price) / stop_price * 100),
            'safe': True
        }

    async def detect_volume_spike(self, symbol: str) -> Dict:
        """
        거래량 급증 감지 (완성된 캔들 기반 안전한 분석)

        7규칙 중 급등/급락 감지 예시
        """
        # 최근 완성된 20개 캔들 (거래량 평균 계산용)
        completed_candles = await self._get_completed_candles(symbol, "1m", count=20)

        if len(completed_candles) < 20:
            return {'signal': 'WAIT', 'reason': '데이터 부족', 'safe': False}

        # 평균 거래량 계산 (완성된 캔들만)
        avg_volume = sum(candle.get('candle_acc_trade_volume', 0)
                        for candle in completed_candles[1:]) / (len(completed_candles) - 1)

        # 최신 완성 캔들의 거래량
        latest_volume = completed_candles[0].get('candle_acc_trade_volume', 0)

        # 거래량 급증 비율
        volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 0

        if volume_ratio > 3.0:  # 3배 이상 급증
            latest_time = self._parse_candle_time(completed_candles[0])

            # API로 재확인 (중요한 신호)
            is_confirmed = await self.candle_manager.verify_candle_with_api(symbol, "1m", latest_time)

            return {
                'signal': 'VOLUME_SPIKE',
                'ratio': volume_ratio,
                'latest_volume': latest_volume,
                'avg_volume': avg_volume,
                'candle_time': latest_time,
                'api_confirmed': is_confirmed,
                'safe': is_confirmed,
                'action': 'MONITOR' if is_confirmed else 'WAIT'
            }

        return {
            'signal': 'NORMAL',
            'ratio': volume_ratio,
            'safe': True
        }

    # ==========================================
    # Private 헬퍼 메서드
    # ==========================================

    async def _get_completed_candles(self, symbol: str, timeframe: str, count: int) -> List[Dict]:
        """완성된 캔들만 가져오기 (DB 또는 API에서)"""
        # 실제 구현 시 Smart Data Provider V3.0과 연계
        # 여기서는 예시 구조만 제공

        # 1. DB에서 완성된 캔들 조회
        # 2. 부족하면 업비트 API로 보완 (완성된 캔들만 제공되므로 안전)
        # 3. 시간순 정렬하여 반환

        return []  # 실제 구현 필요

    def _calculate_rsi(self, candles: List[Dict], period: int = 14) -> float:
        """RSI 계산"""
        if len(candles) < period + 1:
            return 50.0  # 중립값

        # 가격 변화 계산
        price_changes = []
        for i in range(1, len(candles)):
            prev_price = candles[i].get('trade_price', 0)
            curr_price = candles[i-1].get('trade_price', 0)
            price_changes.append(curr_price - prev_price)

        # 상승/하락 분리
        gains = [change for change in price_changes[-period:] if change > 0]
        losses = [-change for change in price_changes[-period:] if change < 0]

        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _parse_candle_time(self, candle: Dict) -> datetime:
        """캔들 시간 파싱"""
        time_str = candle.get('candle_date_time_kst', '')
        if time_str:
            return datetime.fromisoformat(time_str.replace('T', ' '))

        timestamp = candle.get('timestamp', 0)
        if timestamp:
            return datetime.fromtimestamp(timestamp / 1000)

        return datetime.now()


# ==========================================
# 사용 예시
# ==========================================

async def trading_example():
    """실제 매매 시나리오 예시"""
    signal_gen = SafeTradingSignalGenerator()

    # 1. 진입 신호 확인
    entry_signal = await signal_gen.generate_entry_signal('KRW-BTC')
    print(f"진입 신호: {entry_signal}")

    if entry_signal['signal'] == 'BUY' and entry_signal['safe']:
        print("✅ 안전한 진입 신호 - 매수 실행")
        entry_price = 50000000  # 예시 가격

        # 2. 포지션 보유 중 트레일링 스탑 모니터링
        stop_check = await signal_gen.check_trailing_stop('KRW-BTC', entry_price)
        print(f"스탑 체크: {stop_check}")

        if stop_check['action'] == 'SELL' and stop_check['safe']:
            print("✅ 안전한 청산 신호 - 매도 실행")

    # 3. 거래량 급증 모니터링
    volume_check = await signal_gen.detect_volume_spike('KRW-BTC')
    print(f"거래량 체크: {volume_check}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(trading_example())
