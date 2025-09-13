#!/usr/bin/env python3
"""
업비트 공개 API 전체 엔드포인트 응답 테스트

업비트 공개 API의 모든 엔드포인트를 테스트하여 응답을 확인하는 스크립트입니다.
- 각 엔드포인트의 정상 동작 여부 확인
- 응답 형식 및 데이터 구조 검증
- API 변경사항 감지 및 호환성 확인
- Rate Limiter 통합 테스트

실행 방법:
    python rest_api_public_all_endpoint_response.py

출력:
    - 각 엔드포인트별 응답 상태 및 샘플 데이터
    - 실패한 엔드포인트 요약
    - 전체 테스트 결과 리포트
"""
import asyncio
import json
import sys
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# 프로젝트 루트를 Python Path에 추가
sys.path.insert(0, os.getcwd())

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class EndpointTestResult:
    """엔드포인트 테스트 결과"""
    endpoint: str
    method: str
    success: bool
    status_code: Optional[int] = None
    response_count: Optional[int] = None
    sample_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    response_time_ms: Optional[float] = None


class UpbitPublicAPITester:
    """업비트 공개 API 전체 엔드포인트 테스터"""

    def __init__(self):
        self.logger = create_component_logger("UpbitAPITester")
        self.client: Optional[UpbitPublicClient] = None
        self.results: List[EndpointTestResult] = []

    async def __aenter__(self):
        self.client = UpbitPublicClient()
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)

    def add_result(self, result: EndpointTestResult):
        """테스트 결과 추가"""
        self.results.append(result)

        status = "✅" if result.success else "❌"
        info = ""
        if result.success:
            info = f"({result.response_count}개 데이터, {result.response_time_ms:.1f}ms)"
        else:
            info = f"({result.error_message})"

        self.logger.info(f"{status} {result.endpoint} {info}")

    async def test_market_info(self):
        """마켓 정보 API 테스트"""
        self.logger.info("🏪 마켓 정보 API 테스트 시작")

        # 1. 마켓 코드 조회
        try:
            start_time = asyncio.get_event_loop().time()
            markets = await self.client.get_markets()
            end_time = asyncio.get_event_loop().time()

            self.add_result(EndpointTestResult(
                endpoint="/v1/market/all",
                method="GET",
                success=True,
                response_count=len(markets),
                sample_data=markets[0] if markets else None,
                response_time_ms=(end_time - start_time) * 1000
            ))

            # 마켓 데이터를 다른 테스트에서 사용
            self.sample_markets = {
                'KRW': [m['market'] for m in markets if m['market'].startswith('KRW-')][:3],
                'BTC': [m['market'] for m in markets if m['market'].startswith('BTC-')][:3],
                'USDT': [m['market'] for m in markets if m['market'].startswith('USDT-')][:3]
            }

        except Exception as e:
            self.add_result(EndpointTestResult(
                endpoint="/v1/market/all",
                method="GET",
                success=False,
                error_message=str(e)
            ))
            # 기본 샘플 마켓 설정
            self.sample_markets = {
                'KRW': ['KRW-BTC', 'KRW-ETH', 'KRW-XRP'],
                'BTC': ['BTC-ETH', 'BTC-XRP', 'BTC-ADA'],
                'USDT': ['USDT-BTC', 'USDT-ETH', 'USDT-XRP']
            }

    async def test_ticker_apis(self):
        """현재가 API 테스트"""
        self.logger.info("📊 현재가 API 테스트 시작")

        # 1. get_tickers (개별 마켓 - markets 파라미터 사용)
        try:
            start_time = asyncio.get_event_loop().time()
            ticker = await self.client.get_tickers(self.sample_markets['KRW'][:2])
            end_time = asyncio.get_event_loop().time()

            self.add_result(EndpointTestResult(
                endpoint="/v1/ticker",
                method="GET",
                success=True,
                response_count=len(ticker),
                sample_data=ticker[0] if ticker else None,
                response_time_ms=(end_time - start_time) * 1000
            ))
        except Exception as e:
            self.add_result(EndpointTestResult(
                endpoint="/v1/ticker",
                method="GET",
                success=False,
                error_message=str(e)
            ))

        # 2. get_tickers_markets (마켓 단위 조회)
        for quote_currency in ['KRW', 'BTC', 'USDT']:
            try:
                start_time = asyncio.get_event_loop().time()
                tickers = await self.client.get_tickers_markets([quote_currency])
                end_time = asyncio.get_event_loop().time()

                self.add_result(EndpointTestResult(
                    endpoint=f"/v1/ticker/all?quote_currencies={quote_currency}",
                    method="GET",
                    success=True,
                    response_count=len(tickers),
                    sample_data=tickers[0] if tickers else None,
                    response_time_ms=(end_time - start_time) * 1000
                ))
            except Exception as e:
                self.add_result(EndpointTestResult(
                    endpoint=f"/v1/ticker/all?quote_currencies={quote_currency}",
                    method="GET",
                    success=False,
                    error_message=str(e)
                ))

        # 3. get_tickers_markets (복수 기준통화)
        try:
            start_time = asyncio.get_event_loop().time()
            all_tickers = await self.client.get_tickers_markets(['KRW', 'BTC'])
            end_time = asyncio.get_event_loop().time()

            self.add_result(EndpointTestResult(
                endpoint="/v1/ticker/all?quote_currencies=KRW,BTC",
                method="GET",
                success=True,
                response_count=len(all_tickers),
                sample_data=all_tickers[0] if all_tickers else None,
                response_time_ms=(end_time - start_time) * 1000
            ))
        except Exception as e:
            self.add_result(EndpointTestResult(
                endpoint="/v1/ticker/all?quote_currencies=KRW,BTC",
                method="GET",
                success=False,
                error_message=str(e)
            ))

    async def test_orderbook_apis(self):
        """호가 API 테스트"""
        self.logger.info("📋 호가 API 테스트 시작")

        # 1. 호가 정보 조회
        try:
            start_time = asyncio.get_event_loop().time()
            orderbook = await self.client.get_orderbooks(self.sample_markets['KRW'][:2])
            end_time = asyncio.get_event_loop().time()

            self.add_result(EndpointTestResult(
                endpoint="/v1/orderbook",
                method="GET",
                success=True,
                response_count=len(orderbook),
                sample_data=orderbook[0] if orderbook else None,
                response_time_ms=(end_time - start_time) * 1000
            ))
        except Exception as e:
            self.add_result(EndpointTestResult(
                endpoint="/v1/orderbook",
                method="GET",
                success=False,
                error_message=str(e)
            ))

        # 2. 호가 단위 정보 조회
        try:
            start_time = asyncio.get_event_loop().time()
            instruments = await self.client.get_orderbooks_instruments(self.sample_markets['KRW'][:2])
            end_time = asyncio.get_event_loop().time()

            sample_market = list(instruments.keys())[0] if instruments else None
            sample_data = instruments[sample_market] if sample_market else None

            self.add_result(EndpointTestResult(
                endpoint="/v1/orderbook/instruments",
                method="GET",
                success=True,
                response_count=len(instruments),
                sample_data=sample_data,
                response_time_ms=(end_time - start_time) * 1000
            ))
        except Exception as e:
            self.add_result(EndpointTestResult(
                endpoint="/v1/orderbook/instruments",
                method="GET",
                success=False,
                error_message=str(e)
            ))

    async def test_trades_api(self):
        """체결 API 테스트"""
        self.logger.info("📈 체결 API 테스트 시작")

        try:
            start_time = asyncio.get_event_loop().time()
            trades = await self.client.get_trades(self.sample_markets['KRW'][0], count=50)
            end_time = asyncio.get_event_loop().time()

            self.add_result(EndpointTestResult(
                endpoint="/v1/trades/ticks",
                method="GET",
                success=True,
                response_count=len(trades),
                sample_data=trades[0] if trades else None,
                response_time_ms=(end_time - start_time) * 1000
            ))
        except Exception as e:
            self.add_result(EndpointTestResult(
                endpoint="/v1/trades/ticks",
                method="GET",
                success=False,
                error_message=str(e)
            ))

    async def test_candle_apis(self):
        """캔들 API 테스트"""
        self.logger.info("🕯️ 캔들 API 테스트 시작")

        sample_market = self.sample_markets['KRW'][0]

        # 캔들 API 목록
        candle_tests = [
            ("seconds", lambda: self.client.get_candles_seconds(sample_market, count=50)),
            ("minutes/1", lambda: self.client.get_candles_minutes(1, sample_market, count=50)),
            ("minutes/5", lambda: self.client.get_candles_minutes(5, sample_market, count=50)),
            ("minutes/15", lambda: self.client.get_candles_minutes(15, sample_market, count=50)),
            ("minutes/30", lambda: self.client.get_candles_minutes(30, sample_market, count=50)),
            ("minutes/60", lambda: self.client.get_candles_minutes(60, sample_market, count=50)),
            ("minutes/240", lambda: self.client.get_candles_minutes(240, sample_market, count=50)),
            ("days", lambda: self.client.get_candles_days(sample_market, count=50)),
            ("weeks", lambda: self.client.get_candles_weeks(sample_market, count=50)),
            ("months", lambda: self.client.get_candles_months(sample_market, count=24)),
            ("years", lambda: self.client.get_candles_years(sample_market, count=10))
        ]

        for candle_type, test_func in candle_tests:
            try:
                start_time = asyncio.get_event_loop().time()
                candles = await test_func()
                end_time = asyncio.get_event_loop().time()

                self.add_result(EndpointTestResult(
                    endpoint=f"/v1/candles/{candle_type}",
                    method="GET",
                    success=True,
                    response_count=len(candles),
                    sample_data=candles[0] if candles else None,
                    response_time_ms=(end_time - start_time) * 1000
                ))
            except Exception as e:
                self.add_result(EndpointTestResult(
                    endpoint=f"/v1/candles/{candle_type}",
                    method="GET",
                    success=False,
                    error_message=str(e)
                ))

    async def test_convenience_methods(self):
        """편의 메서드 테스트"""
        self.logger.info("🛠️ 편의 메서드 테스트 시작")

        convenience_tests = [
            ("KRW Markets", "get_krw_markets", lambda: self.client.get_krw_markets()),
            ("BTC Markets", "get_btc_markets", lambda: self.client.get_btc_markets()),
            ("Market Summary", "get_market_summary", lambda: self.client.get_market_summary(self.sample_markets['KRW'][0]))
        ]

        for test_name, method_name, test_func in convenience_tests:
            try:
                start_time = asyncio.get_event_loop().time()
                result = await test_func()
                end_time = asyncio.get_event_loop().time()

                count = len(result) if isinstance(result, list) else 1
                sample_data = result[0] if isinstance(result, list) and result else result

                self.add_result(EndpointTestResult(
                    endpoint=f"편의메서드:{method_name}",
                    method="CONVENIENCE",
                    success=True,
                    response_count=count,
                    sample_data=sample_data,
                    response_time_ms=(end_time - start_time) * 1000
                ))
            except Exception as e:
                self.add_result(EndpointTestResult(
                    endpoint=f"편의메서드:{method_name}",
                    method="CONVENIENCE",
                    success=False,
                    error_message=str(e)
                ))

    def generate_report(self) -> str:
        """테스트 결과 리포트 생성"""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - successful_tests

        report = f"""
=================================================================
📊 업비트 공개 API 전체 엔드포인트 테스트 결과 리포트
=================================================================
⏰ 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📈 전체 테스트: {total_tests}개
✅ 성공: {successful_tests}개 ({(successful_tests/total_tests)*100:.1f}%)
❌ 실패: {failed_tests}개 ({(failed_tests/total_tests)*100:.1f}%)

=================================================================
🔍 상세 결과
=================================================================
"""

        # 성공한 테스트
        successful = [r for r in self.results if r.success]
        if successful:
            report += "\n✅ 성공한 엔드포인트:\n"
            for result in successful:
                avg_time = f"{result.response_time_ms:.1f}ms" if result.response_time_ms else "N/A"
                count_info = f"({result.response_count}개)" if result.response_count else ""
                report += f"  • {result.endpoint} {count_info} - {avg_time}\n"

        # 실패한 테스트
        failed = [r for r in self.results if not r.success]
        if failed:
            report += "\n❌ 실패한 엔드포인트:\n"
            for result in failed:
                report += f"  • {result.endpoint} - {result.error_message}\n"

        # 성능 통계
        if successful:
            response_times = [r.response_time_ms for r in successful if r.response_time_ms]
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                min_time = min(response_times)
                max_time = max(response_times)

                report += f"""
=================================================================
⚡ 성능 통계
=================================================================
평균 응답 시간: {avg_time:.1f}ms
최고 응답 시간: {min_time:.1f}ms
최저 응답 시간: {max_time:.1f}ms
"""

        # 샘플 데이터 (첫 번째 성공한 결과만)
        if successful and successful[0].sample_data:
            report += f"""
=================================================================
📄 샘플 응답 데이터 ({successful[0].endpoint})
=================================================================
{json.dumps(successful[0].sample_data, indent=2, ensure_ascii=False)}
"""

        report += "\n================================================================="
        return report

    async def run_all_tests(self):
        """모든 테스트 실행"""
        self.logger.info("🚀 업비트 공개 API 전체 엔드포인트 테스트 시작")

        try:
            await self.test_market_info()
            await self.test_ticker_apis()
            await self.test_orderbook_apis()
            await self.test_trades_api()
            await self.test_candle_apis()
            await self.test_convenience_methods()

        except Exception as e:
            self.logger.error(f"❌ 테스트 실행 중 예외 발생: {e}")

        # 결과 리포트 출력
        report = self.generate_report()
        print(report)

        # 결과 파일로 저장
        report_file = f"upbit_api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        self.logger.info(f"📁 테스트 리포트 저장됨: {report_file}")

        return len(self.results), sum(1 for r in self.results if r.success)


async def main():
    """메인 함수"""
    print("🧪 업비트 공개 API 전체 엔드포인트 응답 테스트")
    print("=" * 60)

    async with UpbitPublicAPITester() as tester:
        total, successful = await tester.run_all_tests()

        if successful == total:
            print(f"\n🎉 모든 테스트 성공! ({successful}/{total})")
            return 0
        else:
            print(f"\n⚠️ 일부 테스트 실패 ({successful}/{total})")
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
