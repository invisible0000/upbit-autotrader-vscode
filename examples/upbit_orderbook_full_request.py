#!/usr/bin/env python3
"""
업비트 Ticker 전체 마켓 테스트 스크립트

목적:
- 모든 업비트 마켓의 Ticker API 호출 가능성 테스트
- 성능 지표 측정 (응답시간, 데이터 용량, 성공률 등)
- 파이썬 기본 라이브러리만 사용하여 클라이언트 독립적 구현

참고: 호가 API가 현재 인증을 요구하므로 Ticker API로 대체하여 테스트

사용법:
python upbit_orderbook_full_request.py
"""

import json
import time
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from datetime import datetime
import gzip
from typing import List, Dict, Any


class UpbitTickerTester:
    """업비트 Ticker 전체 마켓 테스트 클래스"""

    BASE_URL = "https://api.upbit.com"
    MARKET_ALL_URL = f"{BASE_URL}/v1/market/all"
    TICKER_URL = f"{BASE_URL}/v1/ticker"

    def __init__(self):
        self.results = {
            'start_time': None,
            'end_time': None,
            'total_markets': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time_ms': 0,
            'total_data_size_bytes': 0,
            'markets_data': [],
            'error_details': []
        }

    def get_all_markets(self) -> List[str]:
        """모든 마켓 심볼 조회"""
        print("📊 모든 마켓 심볼 조회 중...")

        try:
            request = Request(self.MARKET_ALL_URL)
            request.add_header('Accept', 'application/json')
            request.add_header('User-Agent', 'UpbitOrderbookTester/1.0')

            start_time = time.time()
            with urlopen(request, timeout=10) as response:
                response_time = (time.time() - start_time) * 1000

                # 응답 데이터 읽기 (gzip 압축 해제 고려)
                data = response.read()
                if response.info().get('Content-Encoding') == 'gzip':
                    data = gzip.decompress(data)

                markets_data = json.loads(data.decode('utf-8'))

            # 마켓 코드만 추출
            market_symbols = [market['market'] for market in markets_data]

            print(f"✅ 마켓 조회 완료: {len(market_symbols)}개")
            print(f"   응답시간: {response_time:.1f}ms")
            print(f"   데이터 크기: {len(data):,} bytes")

            return market_symbols

        except Exception as e:
            print(f"❌ 마켓 조회 실패: {e}")
            return []

    def get_all_tickers_with_gzip(self, markets: List[str]) -> Dict[str, Any]:
        """모든 마켓의 Ticker 정보를 gzip 압축으로 조회"""

        # 업비트 API는 한 번에 여러 마켓 조회 가능 (쉼표로 구분)
        markets_param = ",".join(markets)
        url = f"{self.TICKER_URL}?markets={markets_param}"

        print(f"🗜️ gzip 압축 요청 URL: {url[:100]}..." if len(url) > 100 else f"🗜️ gzip 압축 요청 URL: {url}")
        print(f"📊 요청 마켓 수: {len(markets)}개")
        print(f"📏 URL 길이: {len(url):,} 문자")

        try:
            request = Request(url)
            request.add_header('Accept', 'application/json')
            request.add_header('Accept-Encoding', 'gzip, deflate')  # gzip 압축 요청
            request.add_header('User-Agent', 'UpbitOrderbookTester/1.0')

            start_time = time.time()
            with urlopen(request, timeout=30) as response:  # 타임아웃 증가
                response_time = (time.time() - start_time) * 1000

                # 응답 헤더 확인
                content_encoding = response.info().get('Content-Encoding', '')
                content_length = response.info().get('Content-Length')

                # 응답 데이터 읽기
                compressed_data = response.read()
                compressed_size = len(compressed_data)

                # gzip 압축 해제
                if 'gzip' in content_encoding.lower():
                    data = gzip.decompress(compressed_data)
                    original_size = len(data)
                    compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
                else:
                    data = compressed_data
                    original_size = compressed_size
                    compression_ratio = 0

                ticker_data = json.loads(data.decode('utf-8'))

                return {
                    'success': True,
                    'data': ticker_data,
                    'response_time_ms': response_time,
                    'compressed_size_bytes': compressed_size,
                    'original_size_bytes': original_size,
                    'compression_ratio': compression_ratio,
                    'content_encoding': content_encoding,
                    'markets_count': len(markets),
                    'received_count': len(ticker_data) if isinstance(ticker_data, list) else 1
                }

        except HTTPError as e:
            error_msg = f"HTTP {e.code}: {e.reason}"
            try:
                # 에러 응답 본문 읽기
                error_data = e.read().decode('utf-8')
                if error_data:
                    error_msg += f" - {error_data}"
            except Exception:
                pass

            return {
                'success': False,
                'error': error_msg,
                'response_time_ms': 0,
                'compressed_size_bytes': 0,
                'original_size_bytes': 0,
                'compression_ratio': 0,
                'content_encoding': '',
                'markets_count': len(markets),
                'received_count': 0
            }
        except URLError as e:
            return {
                'success': False,
                'error': f"Network error: {e.reason}",
                'response_time_ms': 0,
                'compressed_size_bytes': 0,
                'original_size_bytes': 0,
                'compression_ratio': 0,
                'content_encoding': '',
                'markets_count': len(markets),
                'received_count': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'response_time_ms': 0,
                'compressed_size_bytes': 0,
                'original_size_bytes': 0,
                'compression_ratio': 0,
                'content_encoding': '',
                'markets_count': len(markets),
                'received_count': 0
            }

    def get_all_tickers(self, markets: List[str]) -> Dict[str, Any]:
        """모든 마켓의 Ticker 정보를 한번에 조회"""

        # 업비트 API는 한 번에 여러 마켓 조회 가능 (쉼표로 구분)
        markets_param = ",".join(markets)
        url = f"{self.TICKER_URL}?markets={markets_param}"

        print(f"🌐 요청 URL: {url[:100]}..." if len(url) > 100 else f"🌐 요청 URL: {url}")
        print(f"📊 요청 마켓 수: {len(markets)}개")
        print(f"📏 URL 길이: {len(url):,} 문자")

        try:
            request = Request(url)
            request.add_header('Accept', 'application/json')
            request.add_header('User-Agent', 'UpbitOrderbookTester/1.0')

            start_time = time.time()
            with urlopen(request, timeout=30) as response:  # 타임아웃 증가
                response_time = (time.time() - start_time) * 1000

                # 응답 데이터 읽기
                data = response.read()
                if response.info().get('Content-Encoding') == 'gzip':
                    data = gzip.decompress(data)

                orderbook_data = json.loads(data.decode('utf-8'))

                return {
                    'success': True,
                    'data': orderbook_data,
                    'response_time_ms': response_time,
                    'data_size_bytes': len(data),
                    'markets_count': len(markets),
                    'received_count': len(orderbook_data) if isinstance(orderbook_data, list) else 1
                }

        except HTTPError as e:
            error_msg = f"HTTP {e.code}: {e.reason}"
            try:
                # 에러 응답 본문 읽기
                error_data = e.read().decode('utf-8')
                if error_data:
                    error_msg += f" - {error_data}"
            except Exception:
                pass

            return {
                'success': False,
                'error': error_msg,
                'response_time_ms': 0,
                'data_size_bytes': 0,
                'markets_count': len(markets),
                'received_count': 0
            }
        except URLError as e:
            return {
                'success': False,
                'error': f"Network error: {e.reason}",
                'response_time_ms': 0,
                'data_size_bytes': 0,
                'markets_count': len(markets),
                'received_count': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'response_time_ms': 0,
                'data_size_bytes': 0,
                'markets_count': len(markets),
                'received_count': 0
            }

    def analyze_ticker_data(self, ticker_data: List[Dict]) -> Dict[str, Any]:
        """Ticker 데이터 분석"""
        if not ticker_data:
            return {'total_markets': 0, 'analysis': 'No data'}

        analysis = {
            'markets_analyzed': len(ticker_data),
            'price_ranges': {
                'krw_markets': [],
                'btc_markets': [],
                'usdt_markets': []
            },
            'volume_stats': [],
            'change_rates': []
        }

        for ticker in ticker_data:
            market = ticker.get('market', '')
            trade_price = float(ticker.get('trade_price', 0))
            change_rate = float(ticker.get('change_rate', 0))
            acc_trade_volume_24h = float(ticker.get('acc_trade_volume_24h', 0))

            # 마켓별 분류
            if market.startswith('KRW-'):
                analysis['price_ranges']['krw_markets'].append(trade_price)
            elif market.startswith('BTC-'):
                analysis['price_ranges']['btc_markets'].append(trade_price)
            elif market.startswith('USDT-'):
                analysis['price_ranges']['usdt_markets'].append(trade_price)

            analysis['volume_stats'].append(acc_trade_volume_24h)
            analysis['change_rates'].append(change_rate * 100)  # 퍼센트로 변환

        # 통계 계산
        analysis['avg_change_rate'] = sum(analysis['change_rates']) / len(analysis['change_rates']) if analysis['change_rates'] else 0
        analysis['avg_volume'] = sum(analysis['volume_stats']) / len(analysis['volume_stats']) if analysis['volume_stats'] else 0

        # 마켓별 평균 가격
        for market_type, prices in analysis['price_ranges'].items():
            if prices:
                analysis[f'avg_price_{market_type}'] = sum(prices) / len(prices)
                analysis[f'count_{market_type}'] = len(prices)
            else:
                analysis[f'avg_price_{market_type}'] = 0
                analysis[f'count_{market_type}'] = 0

        return analysis

    def analyze_orderbook_data(self, orderbook_data: List[Dict]) -> Dict[str, Any]:
        """호가 데이터 분석"""
        if not orderbook_data:
            return {'total_levels': 0, 'avg_spread': 0, 'analysis': 'No data'}

        analysis = {
            'markets_analyzed': len(orderbook_data),
            'total_orderbook_levels': 0,
            'spreads': [],
            'bid_volumes': [],
            'ask_volumes': []
        }

        for orderbook in orderbook_data:
            if 'orderbook_units' in orderbook:
                levels = len(orderbook['orderbook_units'])
                analysis['total_orderbook_levels'] += levels

                # 첫 번째 레벨의 스프레드 계산
                if levels > 0:
                    first_level = orderbook['orderbook_units'][0]
                    bid_price = float(first_level['bid_price'])
                    ask_price = float(first_level['ask_price'])
                    spread = ask_price - bid_price
                    spread_percent = (spread / bid_price) * 100 if bid_price > 0 else 0

                    analysis['spreads'].append(spread_percent)
                    analysis['bid_volumes'].append(float(first_level['bid_size']))
                    analysis['ask_volumes'].append(float(first_level['ask_size']))

        # 평균값 계산
        if analysis['spreads']:
            analysis['avg_spread_percent'] = sum(analysis['spreads']) / len(analysis['spreads'])
            analysis['avg_bid_volume'] = sum(analysis['bid_volumes']) / len(analysis['bid_volumes'])
            analysis['avg_ask_volume'] = sum(analysis['ask_volumes']) / len(analysis['ask_volumes'])
        else:
            analysis['avg_spread_percent'] = 0
            analysis['avg_bid_volume'] = 0
            analysis['avg_ask_volume'] = 0

        return analysis

    def run_gzip_comparison_test(self) -> None:
        """gzip 압축 성능 비교 테스트 실행"""
        print("🚀 업비트 Ticker API gzip 압축 성능 비교 테스트 시작")
        print("=" * 60)

        self.results['start_time'] = datetime.now()

        # 1. 모든 마켓 조회
        markets = self.get_all_markets()
        if not markets:
            print("❌ 마켓 조회 실패로 테스트 중단")
            return

        self.results['total_markets'] = len(markets)

        # 2. 일반 요청 테스트
        print(f"\n📋 1. 일반 요청 테스트 (gzip 압축 없음)")
        print(f"   📊 총 마켓 수: {len(markets)}개")
        normal_result = self.get_all_tickers(markets)

        # 3. gzip 압축 요청 테스트
        print(f"\n📋 2. gzip 압축 요청 테스트")
        print(f"   📊 총 마켓 수: {len(markets)}개")
        gzip_result = self.get_all_tickers_with_gzip(markets)

        # 4. 성능 비교 분석
        self.analyze_performance_comparison(normal_result, gzip_result)

        self.results['end_time'] = datetime.now()

        # 5. 비교 결과 출력
        self.print_comparison_results(normal_result, gzip_result)

    def analyze_performance_comparison(self, normal_result: Dict[str, Any], gzip_result: Dict[str, Any]) -> None:
        """성능 비교 분석"""
        comparison = {
            'normal_request': {
                'success': normal_result['success'],
                'response_time_ms': normal_result['response_time_ms'],
                'data_size_bytes': normal_result.get('data_size_bytes', 0),
                'markets_count': normal_result['received_count'] if normal_result['success'] else 0
            },
            'gzip_request': {
                'success': gzip_result['success'],
                'response_time_ms': gzip_result['response_time_ms'],
                'compressed_size_bytes': gzip_result.get('compressed_size_bytes', 0),
                'original_size_bytes': gzip_result.get('original_size_bytes', 0),
                'compression_ratio': gzip_result.get('compression_ratio', 0),
                'content_encoding': gzip_result.get('content_encoding', ''),
                'markets_count': gzip_result['received_count'] if gzip_result['success'] else 0
            }
        }

        # 성능 개선 계산
        if normal_result['success'] and gzip_result['success']:
            # 응답 시간 비교
            time_improvement = (normal_result['response_time_ms'] - gzip_result['response_time_ms']) / normal_result['response_time_ms'] * 100

            # 데이터 크기 비교 (압축 효과)
            normal_size = normal_result.get('data_size_bytes', 0)
            gzip_compressed_size = gzip_result.get('compressed_size_bytes', 0)
            if normal_size > 0:
                bandwidth_savings = (normal_size - gzip_compressed_size) / normal_size * 100
            else:
                bandwidth_savings = 0

            comparison['performance_metrics'] = {
                'time_improvement_percent': time_improvement,
                'bandwidth_savings_percent': bandwidth_savings,
                'bytes_saved': normal_size - gzip_compressed_size
            }

        self.results['gzip_comparison'] = comparison

    def print_comparison_results(self, normal_result: Dict[str, Any], gzip_result: Dict[str, Any]) -> None:
        """gzip 압축 비교 결과 출력"""
        print("\n" + "=" * 60)
        print("📊 gzip 압축 성능 비교 결과")
        print("=" * 60)

        if not (normal_result['success'] and gzip_result['success']):
            print("❌ 일부 요청이 실패하여 비교할 수 없습니다.")
            if not normal_result['success']:
                print(f"   일반 요청 실패: {normal_result.get('error', 'Unknown error')}")
            if not gzip_result['success']:
                print(f"   gzip 요청 실패: {gzip_result.get('error', 'Unknown error')}")
            return

        print("🎯 **응답 시간 비교**")
        normal_time = normal_result['response_time_ms']
        gzip_time = gzip_result['response_time_ms']
        time_diff = normal_time - gzip_time
        time_improvement = (time_diff / normal_time * 100) if normal_time > 0 else 0

        print(f"   일반 요청:     {normal_time:.1f}ms")
        print(f"   gzip 압축:     {gzip_time:.1f}ms")
        print(f"   시간 차이:     {time_diff:+.1f}ms")
        print(f"   성능 개선:     {time_improvement:+.1f}%")

        print("\n💾 **데이터 크기 비교**")
        normal_size = normal_result.get('data_size_bytes', 0)
        compressed_size = gzip_result.get('compressed_size_bytes', 0)
        original_size = gzip_result.get('original_size_bytes', 0)
        compression_ratio = gzip_result.get('compression_ratio', 0)

        print(f"   일반 요청:     {normal_size:,} bytes ({normal_size/1024:.1f} KB)")
        print(f"   압축된 크기:   {compressed_size:,} bytes ({compressed_size/1024:.1f} KB)")
        print(f"   원본 크기:     {original_size:,} bytes ({original_size/1024:.1f} KB)")
        print(f"   압축 비율:     {compression_ratio:.1f}%")

        if normal_size > 0 and compressed_size > 0:
            bandwidth_savings = (normal_size - compressed_size) / normal_size * 100
            bytes_saved = normal_size - compressed_size
            print(f"   대역폭 절약:   {bandwidth_savings:.1f}% ({bytes_saved:,} bytes)")

        print("\n🌐 **서버 응답 정보**")
        content_encoding = gzip_result.get('content_encoding', '')
        print(f"   Content-Encoding: {content_encoding}")
        print(f"   gzip 지원:     {'✅ 지원됨' if 'gzip' in content_encoding.lower() else '❌ 지원되지 않음'}")

        print("\n📈 **종합 평가**")
        if compression_ratio > 70:
            compression_grade = "🟢 우수"
        elif compression_ratio > 50:
            compression_grade = "🟡 양호"
        elif compression_ratio > 30:
            compression_grade = "🟠 보통"
        else:
            compression_grade = "🔴 낮음"

        print(f"   압축 효율:     {compression_grade} ({compression_ratio:.1f}%)")

        if time_improvement > 10:
            speed_grade = "🟢 빠름"
        elif time_improvement > 0:
            speed_grade = "🟡 약간 빠름"
        elif time_improvement > -10:
            speed_grade = "🟠 비슷함"
        else:
            speed_grade = "🔴 느림"

        print(f"   속도 개선:     {speed_grade} ({time_improvement:+.1f}%)")

        # 권장사항
        if compression_ratio > 50 and time_improvement > -5:
            recommendation = "✅ gzip 압축 사용 권장"
        elif compression_ratio > 30:
            recommendation = "🟡 대용량 데이터 시 gzip 압축 고려"
        else:
            recommendation = "❌ gzip 압축 효과 제한적"

        print(f"   권장사항:     {recommendation}")

    def run_full_test(self) -> None:
        """전체 테스트 실행 - 모든 마켓을 한번에 요청"""
        print("🚀 업비트 호가 전체 마켓 테스트 시작")
        print("=" * 60)

        self.results['start_time'] = datetime.now()

        # 1. 모든 마켓 조회
        markets = self.get_all_markets()
        if not markets:
            print("❌ 마켓 조회 실패로 테스트 중단")
            return

        self.results['total_markets'] = len(markets)

        # 2. 모든 마켓의 Ticker를 한번에 조회 (호가 API는 인증 필요)
        print(f"\n📋 모든 마켓 Ticker 데이터 한번에 조회")
        print(f"   📊 총 마켓 수: {len(markets)}개")
        print(f"   🎯 테스트 목적: API 한계 및 성능 측정")
        print(f"   ⚠️  참고: 호가 API는 인증이 필요하므로 Ticker API로 대체")

        result = self.get_all_tickers(markets)

        # 결과 누적
        if result['success']:
            self.results['successful_requests'] = result['received_count']
            self.results['failed_requests'] = 0
            all_ticker_data = result['data'] if isinstance(result['data'], list) else [result['data']]
            print(f"   ✅ 성공: {result['received_count']}개 마켓 응답 받음")

            # Ticker 데이터 분석
            print("\n🔍 Ticker 데이터 분석 중...")
            analysis = self.analyze_ticker_data(all_ticker_data)
            self.results['ticker_analysis'] = analysis

        else:
            self.results['successful_requests'] = 0
            self.results['failed_requests'] = result['markets_count']
            self.results['error_details'].append({
                'request_type': 'single_bulk_request',
                'markets_count': result['markets_count'],
                'error': result['error']
            })
            print(f"   ❌ 실패: {result['error']}")

        self.results['total_response_time_ms'] = result['response_time_ms']
        self.results['total_data_size_bytes'] = result['data_size_bytes']

        print(f"   ⏱️  응답시간: {result['response_time_ms']:.1f}ms")
        print(f"   💾 데이터 크기: {result['data_size_bytes']:,} bytes")

        self.results['end_time'] = datetime.now()

        # 4. 결과 출력
        self.print_results()

    def print_results(self) -> None:
        """테스트 결과 출력"""
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)

        # 기본 통계
        total_duration = (self.results['end_time'] - self.results['start_time']).total_seconds()
        success_rate = (
            (self.results['successful_requests'] / self.results['total_markets'] * 100)
            if self.results['total_markets'] > 0 else 0
        )

        print("🎯 **기본 통계**")
        print(f"   전체 마켓 수: {self.results['total_markets']:,}개")
        print(f"   성공한 요청: {self.results['successful_requests']:,}개")
        print(f"   실패한 요청: {self.results['failed_requests']:,}개")
        print(f"   성공률: {success_rate:.1f}%")

        print("\n⏱️  **성능 지표**")
        print(f"   총 소요시간: {total_duration:.1f}초")
        print(f"   총 응답시간: {self.results['total_response_time_ms']:,.0f}ms")
        print(f"   단일 요청 응답시간: {self.results['total_response_time_ms']:.1f}ms")
        print(f"   처리율: {self.results['total_markets'] / total_duration:.1f} 마켓/초")

        print("\n💾 **데이터 용량**")
        data_size_mb = self.results['total_data_size_bytes'] / (1024 * 1024)
        data_size_kb = self.results['total_data_size_bytes'] / 1024
        avg_size_per_market = (
            self.results['total_data_size_bytes'] / self.results['successful_requests']
            if self.results['successful_requests'] > 0 else 0
        )

        print(f"   총 데이터 크기: {self.results['total_data_size_bytes']:,} bytes")
        print(f"                  {data_size_kb:.1f} KB")
        print(f"                  {data_size_mb:.2f} MB")
        print(f"   마켓당 평균 크기: {avg_size_per_market:.0f} bytes")

        # Ticker 분석 결과
        if 'ticker_analysis' in self.results:
            analysis = self.results['ticker_analysis']
            print(f"\n📊 **Ticker 분석**")
            print(f"   분석된 마켓: {analysis['markets_analyzed']:,}개")
            print(f"   KRW 마켓: {analysis['count_krw_markets']}개 (평균가: {analysis['avg_price_krw_markets']:,.0f}원)")
            print(f"   BTC 마켓: {analysis['count_btc_markets']}개 (평균가: {analysis['avg_price_btc_markets']:.8f})")
            print(f"   USDT 마켓: {analysis['count_usdt_markets']}개 (평균가: {analysis['avg_price_usdt_markets']:.4f})")
            print(f"   평균 변화율: {analysis['avg_change_rate']:.2f}%")
            print(f"   평균 거래량: {analysis['avg_volume']:.2f}")

        # 호가 분석 결과 (레거시 코드 - 실제로는 사용되지 않음)
        if 'orderbook_analysis' in self.results:
            analysis = self.results['orderbook_analysis']
            print(f"\n📋 **호가 분석**")
            print(f"   분석된 마켓: {analysis['markets_analyzed']:,}개")
            print(f"   총 호가 레벨: {analysis['total_orderbook_levels']:,}개")
            print(f"   평균 스프레드: {analysis['avg_spread_percent']:.3f}%")
            print(f"   평균 매수 물량: {analysis['avg_bid_volume']:.2f}")
            print(f"   평균 매도 물량: {analysis['avg_ask_volume']:.2f}")

        # Rate Limit 분석
        total_requests = 1 if self.results['total_markets'] > 0 else 0  # 단일 요청
        requests_per_second = total_requests / total_duration if total_duration > 0 else 0
        print("\n🚦 **Rate Limit 분석**")
        print(f"   실제 요청 횟수: {total_requests}회 (단일 대용량 요청)")
        print(f"   초당 요청 수: {requests_per_second:.2f}회/초")
        print("   업비트 제한: 10회/초")
        print(f"   제한 준수: {'✅ 준수' if requests_per_second <= 10 else '❌ 초과'}")

        # 에러 상세
        if self.results['error_details']:
            print("\n❌ **에러 상세**")
            for error in self.results['error_details']:
                if 'request_type' in error:  # 단일 요청 에러
                    print(f"   요청 타입: {error['request_type']}")
                    print(f"   마켓 수: {error['markets_count']}개")
                    print(f"   에러: {error['error']}")
                else:  # 기존 청크 에러 (하위 호환성)
                    print(f"   청크 {error['chunk']}: {error['error']}")
                    markets_list = error['markets'][:3]
                    suffix = '...' if len(error['markets']) > 3 else ''
                    print(f"   실패한 마켓: {', '.join(markets_list)}{suffix}")

        print("\n" + "=" * 60)
        print("🎉 테스트 완료!")


def main():
    """메인 함수"""
    print("🚀 업비트 Ticker API gzip 압축 성능 비교 테스트")
    print("=" * 60)
    print("이 스크립트는 업비트의 모든 마켓에 대해 Ticker API gzip 압축 효과를 비교합니다.")
    print("개발 지침용 성능 데이터를 수집하여 최적화 방향을 제시합니다.")
    print("=" * 60)

    try:
        tester = UpbitTickerTester()
        tester.run_gzip_comparison_test()

    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
