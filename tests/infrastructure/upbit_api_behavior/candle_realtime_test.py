"""업비트 API 캔들 데이터 실시간 제공 방식 테스트

이 모듈은 업비트 API가 캔들 데이터를 실시간으로 제공하는지,
아니면 완성된 캔들만 제공하는지를 검증합니다.

테스트 목적:
1. 진행 중인 캔들의 OHLC 값이 실시간으로 업데이트되는지 확인
2. 현재가와 캔들 종가의 일치성 검증
3. multiplier 기능 설계에 필요한 핵심 정보 도출
"""

import asyncio
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from upbit_auto_trading.infrastructure.external_apis.upbit import UpbitClient
from upbit_auto_trading.infrastructure.logging import create_component_logger


class UpbitCandleRealtimeTest:
    """업비트 캔들 데이터 실시간 제공 방식 테스트 클래스"""

    def __init__(self, test_duration_minutes: int = 10, sample_interval_seconds: int = 30):
        self.client: Optional[UpbitClient] = None
        self.logger = create_component_logger("UpbitCandleTest")
        self.test_duration_minutes = test_duration_minutes
        self.sample_interval_seconds = sample_interval_seconds
        self.test_data: List[Dict[str, Any]] = []

        # 결과 저장 경로
        self.test_results_dir = Path("tests/infrastructure/upbit_api_behavior/test_results")
        self.test_results_dir.mkdir(parents=True, exist_ok=True)

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.client = UpbitClient()
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def test_candle_update_pattern(self, symbol: str = "KRW-BTC", timeframe: int = 5) -> Dict[str, Any]:
        """5분봉 실시간 업데이트 패턴 테스트

        Args:
            symbol: 테스트할 심볼 (기본: KRW-BTC)
            timeframe: 캔들 타임프레임 분 단위 (기본: 5분)

        Returns:
            테스트 결과 요약 딕셔너리
        """
        self.logger.info(f"🚀 캔들 실시간 업데이트 패턴 테스트 시작: {symbol}, {timeframe}분봉")
        self.logger.info(f"⏱️ 테스트 시간: {self.test_duration_minutes}분, 샘플링 간격: {self.sample_interval_seconds}초")

        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=self.test_duration_minutes)
        sample_count = (self.test_duration_minutes * 60) // self.sample_interval_seconds

        self.test_data = []

        try:
            for i in range(sample_count):
                current_time = datetime.now()

                if current_time >= end_time:
                    break

                self.logger.info(f"📊 데이터 수집 {i+1}/{sample_count} - {current_time.strftime('%H:%M:%S')}")

                # 병렬로 캔들과 현재가 데이터 수집
                sample_data = await self._collect_sample_data(symbol, timeframe, current_time)
                self.test_data.append(sample_data)

                # Rate limit 고려한 대기
                await asyncio.sleep(self.sample_interval_seconds)

        except Exception as e:
            self.logger.error(f"❌ 테스트 중 오류 발생: {e}")
            raise

        # 테스트 결과 분석 및 저장
        analysis_result = await self._analyze_test_results(symbol, timeframe)
        await self._save_test_results(symbol, timeframe, start_time)

        self.logger.info(f"✅ 테스트 완료: 총 {len(self.test_data)}개 샘플 수집")
        return analysis_result

    async def _collect_sample_data(self, symbol: str, timeframe: int, timestamp: datetime) -> Dict[str, Any]:
        """단일 시점의 샘플 데이터 수집"""
        try:
            # 캔들과 현재가 동시 조회
            candles_task = self.client.get_candles_minutes(symbol, unit=timeframe, count=2)
            tickers_task = self.client.get_tickers([symbol])

            candles, tickers = await asyncio.gather(candles_task, tickers_task)

            current_candle = candles[0] if candles else {}
            previous_candle = candles[1] if len(candles) > 1 else {}
            ticker = tickers[0] if tickers else {}

            return {
                'timestamp': timestamp.isoformat(),
                'current_candle': current_candle,
                'previous_candle': previous_candle,
                'ticker': ticker,
                'candle_time': current_candle.get('candle_date_time_kst'),
                'trade_price': ticker.get('trade_price'),
                'opening_price': current_candle.get('opening_price'),
                'high_price': current_candle.get('high_price'),
                'low_price': current_candle.get('low_price'),
                'trade_price_candle': current_candle.get('trade_price'),  # 캔들의 종가
                'acc_trade_volume': current_candle.get('candle_acc_trade_volume')
            }

        except Exception as e:
            self.logger.error(f"❌ 샘플 데이터 수집 실패: {e}")
            return {
                'timestamp': timestamp.isoformat(),
                'error': str(e)
            }

    async def _analyze_test_results(self, symbol: str, timeframe: int) -> Dict[str, Any]:
        """수집된 테스트 데이터 분석"""
        self.logger.info("🔍 테스트 결과 분석 시작")

        if not self.test_data:
            return {'error': '분석할 데이터가 없습니다'}

        # 에러가 없는 유효한 데이터만 필터링
        valid_data = [d for d in self.test_data if 'error' not in d and d.get('current_candle')]

        if not valid_data:
            return {'error': '유효한 데이터가 없습니다'}

        analysis = {
            'symbol': symbol,
            'timeframe': timeframe,
            'total_samples': len(self.test_data),
            'valid_samples': len(valid_data),
            'test_period': {
                'start': valid_data[0]['timestamp'],
                'end': valid_data[-1]['timestamp']
            }
        }

        # 캔들 시간 분석
        candle_times = [d['candle_time'] for d in valid_data if d.get('candle_time')]
        unique_candle_times = list(set(candle_times))
        analysis['unique_candles_observed'] = len(unique_candle_times)
        analysis['candle_times'] = sorted(unique_candle_times)

        # OHLC 변화 패턴 분석
        analysis['ohlc_analysis'] = self._analyze_ohlc_changes(valid_data)

        # 현재가 vs 캔들 종가 일치성 분석
        analysis['price_consistency'] = self._analyze_price_consistency(valid_data)

        # 실시간 업데이트 여부 판단
        analysis['realtime_update_verdict'] = self._determine_realtime_behavior(analysis)

        self.logger.info(f"📈 분석 완료: {analysis['unique_candles_observed']}개 캔들 관찰")
        return analysis

    def _analyze_ohlc_changes(self, valid_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """OHLC 값들의 변화 패턴 분석"""
        if len(valid_data) < 2:
            return {'error': '분석에 충분한 데이터가 없습니다'}

        # 같은 캔들 시간대의 데이터들을 그룹화
        candle_groups = {}
        for data in valid_data:
            candle_time = data.get('candle_time')
            if candle_time:
                if candle_time not in candle_groups:
                    candle_groups[candle_time] = []
                candle_groups[candle_time].append(data)

        ohlc_changes = {}
        for candle_time, group in candle_groups.items():
            if len(group) > 1:  # 같은 캔들에 대해 여러 샘플이 있는 경우
                changes = {
                    'opening_price_changes': [],
                    'high_price_changes': [],
                    'low_price_changes': [],
                    'closing_price_changes': [],
                    'volume_changes': []
                }

                for i in range(1, len(group)):
                    prev, curr = group[i-1], group[i]

                    # 각 OHLC 값의 변화 기록
                    if prev.get('opening_price') != curr.get('opening_price'):
                        changes['opening_price_changes'].append({
                            'from': prev.get('opening_price'),
                            'to': curr.get('opening_price'),
                            'time': curr['timestamp']
                        })

                    if prev.get('high_price') != curr.get('high_price'):
                        changes['high_price_changes'].append({
                            'from': prev.get('high_price'),
                            'to': curr.get('high_price'),
                            'time': curr['timestamp']
                        })

                    if prev.get('low_price') != curr.get('low_price'):
                        changes['low_price_changes'].append({
                            'from': prev.get('low_price'),
                            'to': curr.get('low_price'),
                            'time': curr['timestamp']
                        })

                    if prev.get('trade_price_candle') != curr.get('trade_price_candle'):
                        changes['closing_price_changes'].append({
                            'from': prev.get('trade_price_candle'),
                            'to': curr.get('trade_price_candle'),
                            'time': curr['timestamp']
                        })

                    if prev.get('acc_trade_volume') != curr.get('acc_trade_volume'):
                        changes['volume_changes'].append({
                            'from': prev.get('acc_trade_volume'),
                            'to': curr.get('acc_trade_volume'),
                            'time': curr['timestamp']
                        })

                ohlc_changes[candle_time] = changes

        return ohlc_changes

    def _analyze_price_consistency(self, valid_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """현재가와 캔들 종가의 일치성 분석"""
        consistency_data = []

        for data in valid_data:
            ticker_price = data.get('trade_price')
            candle_price = data.get('trade_price_candle')

            if ticker_price is not None and candle_price is not None:
                is_consistent = ticker_price == candle_price
                consistency_data.append({
                    'timestamp': data['timestamp'],
                    'ticker_price': ticker_price,
                    'candle_price': candle_price,
                    'is_consistent': is_consistent,
                    'price_diff': abs(ticker_price - candle_price) if ticker_price != candle_price else 0
                })

        if not consistency_data:
            return {'error': '가격 일치성 분석할 데이터가 없습니다'}

        total_samples = len(consistency_data)
        consistent_samples = sum(1 for d in consistency_data if d['is_consistent'])
        consistency_ratio = consistent_samples / total_samples

        return {
            'total_samples': total_samples,
            'consistent_samples': consistent_samples,
            'consistency_ratio': consistency_ratio,
            'consistency_percentage': consistency_ratio * 100,
            'inconsistent_cases': [d for d in consistency_data if not d['is_consistent']]
        }

    def _determine_realtime_behavior(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """실시간 업데이트 여부 최종 판단"""
        verdict = {
            'is_realtime_update': False,
            'confidence_level': 'low',
            'evidence': [],
            'recommendation': ''
        }

        # 증거 수집
        ohlc_analysis = analysis.get('ohlc_analysis', {})
        price_consistency = analysis.get('price_consistency', {})

        # 증거 1: OHLC 값의 실시간 변화
        has_ohlc_changes = any(
            any(changes.values()) for changes in ohlc_analysis.values()
            if isinstance(changes, dict) and 'error' not in changes
        )

        if has_ohlc_changes:
            verdict['evidence'].append("같은 캔들 시간대에서 OHLC 값의 변화 감지")
            verdict['is_realtime_update'] = True
            verdict['confidence_level'] = 'medium'

        # 증거 2: 현재가와 캔들 종가의 일치성
        consistency_ratio = price_consistency.get('consistency_ratio', 0)
        if consistency_ratio > 0.8:  # 80% 이상 일치
            verdict['evidence'].append(f"현재가와 캔들 종가 높은 일치율: {consistency_ratio:.2%}")
            verdict['is_realtime_update'] = True
            verdict['confidence_level'] = 'high'
        elif consistency_ratio < 0.2:  # 20% 미만 일치
            verdict['evidence'].append(f"현재가와 캔들 종가 낮은 일치율: {consistency_ratio:.2%}")
            verdict['is_realtime_update'] = False
            verdict['confidence_level'] = 'high'

        # 추천사항 생성
        if verdict['is_realtime_update']:
            verdict['recommendation'] = (
                "✅ 실시간 캔들 업데이트 지원: multiplier 기능에서 즉시 반영 가능하나 "
                "노이즈 필터링 옵션 필요"
            )
        else:
            verdict['recommendation'] = (
                "⚠️ 완성 캔들만 제공: 가상의 실시간 캔들 관리 시스템 구축 필요. "
                "현재가 기반으로 진행 중 캔들 시뮬레이션 구현 권장"
            )

        return verdict

    async def _save_test_results(self, symbol: str, timeframe: int, start_time: datetime):
        """테스트 결과를 파일로 저장"""
        timestamp_str = start_time.strftime("%Y%m%d_%H%M%S")

        # JSON 형태로 상세 데이터 저장
        json_file = self.test_results_dir / f"candle_test_{symbol}_{timeframe}m_{timestamp_str}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_data, f, ensure_ascii=False, indent=2)

        # CSV 형태로 요약 데이터 저장
        csv_file = self.test_results_dir / f"candle_summary_{symbol}_{timeframe}m_{timestamp_str}.csv"

        if self.test_data:
            valid_data = [d for d in self.test_data if 'error' not in d and d.get('current_candle')]

            if valid_data:
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = [
                        'timestamp', 'candle_time', 'opening_price', 'high_price',
                        'low_price', 'trade_price_candle', 'trade_price_ticker',
                        'acc_trade_volume'
                    ]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for data in valid_data:
                        writer.writerow({
                            'timestamp': data['timestamp'],
                            'candle_time': data.get('candle_time', ''),
                            'opening_price': data.get('opening_price', ''),
                            'high_price': data.get('high_price', ''),
                            'low_price': data.get('low_price', ''),
                            'trade_price_candle': data.get('trade_price_candle', ''),
                            'trade_price_ticker': data.get('trade_price', ''),
                            'acc_trade_volume': data.get('acc_trade_volume', '')
                        })

        self.logger.info(f"💾 테스트 결과 저장 완료:")
        self.logger.info(f"   📄 JSON: {json_file}")
        self.logger.info(f"   📊 CSV: {csv_file}")


async def run_candle_realtime_test():
    """캔들 실시간 테스트 실행 함수"""
    print("🚀 업비트 API 캔들 데이터 실시간 제공 방식 테스트 시작")
    print("=" * 60)

    try:
        async with UpbitCandleRealtimeTest(test_duration_minutes=10, sample_interval_seconds=30) as tester:
            # 5분봉 테스트
            result = await tester.test_candle_update_pattern("KRW-BTC", 5)

            print("\n📊 테스트 결과 요약:")
            print("=" * 60)
            print(f"🎯 심볼: {result.get('symbol', 'N/A')}")
            print(f"⏱️ 타임프레임: {result.get('timeframe', 'N/A')}분봉")
            print(f"📈 총 샘플: {result.get('total_samples', 0)}개")
            print(f"✅ 유효 샘플: {result.get('valid_samples', 0)}개")
            print(f"🕐 관찰된 캔들: {result.get('unique_candles_observed', 0)}개")

            verdict = result.get('realtime_update_verdict', {})
            print(f"\n🎯 실시간 업데이트 여부: {'✅ YES' if verdict.get('is_realtime_update') else '❌ NO'}")
            print(f"🔍 신뢰도: {verdict.get('confidence_level', 'unknown').upper()}")
            print(f"💡 권장사항: {verdict.get('recommendation', 'N/A')}")

            if verdict.get('evidence'):
                print(f"\n📋 근거:")
                for evidence in verdict['evidence']:
                    print(f"   • {evidence}")

    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_candle_realtime_test())
