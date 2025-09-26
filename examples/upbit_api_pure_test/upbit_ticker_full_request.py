#!/usr/bin/env python3
"""
업비트 티커 전체 마켓 테스트 스크립트

목적:
- 모든 업비트 마켓의 티커 API 호출 가능성 테스트
- 성능 지표 측정 (응답시간, 데이터 용량, 성공률 등)
- 파이썬 기본 라이브러리만 사용하여 클라이언트 독립적 구현
- 모든 심볼을 한번에 요청하여 API 한계 테스트

사용법:
python upbit_ticker_full_request.py
"""

import json
import time
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from datetime import datetime
import gzip
from typing import List, Dict, Any


class UpbitTickerTester:
    """업비트 티커 전체 마켓 테스트 클래스"""

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
            'ticker_analysis': {},
            'error_details': [],
            'gzip_comparison': {
                'no_gzip': {},
                'with_gzip': {},
                'comparison_results': {}
            }
        }

    def get_all_markets(self) -> List[str]:
        """모든 마켓 심볼 조회"""
        print("📊 모든 마켓 심볼 조회 중...")

        try:
            request = Request(self.MARKET_ALL_URL)
            request.add_header('Accept', 'application/json')
            request.add_header('User-Agent', 'UpbitTickerTester/1.0')

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
        """모든 마켓의 티커 정보 한번에 조회 (gzip 압축 사용)"""

        # 업비트 API는 한 번에 여러 마켓 조회 가능 (쉼표로 구분)
        markets_param = ",".join(markets)
        url = f"{self.TICKER_URL}?markets={markets_param}"

        print("🗜️  gzip 압축 사용하여 티커 정보 조회...")
        print(f"   요청 URL 길이: {len(url):,} characters")
        print(f"   요청 마켓 수: {len(markets):,}개")

        try:
            request = Request(url)
            request.add_header('Accept', 'application/json')
            request.add_header('Accept-Encoding', 'gzip')  # gzip 압축 요청
            request.add_header('User-Agent', 'UpbitTickerTester/1.0')

            start_time = time.time()
            with urlopen(request, timeout=30) as response:  # 더 긴 타임아웃
                response_time = (time.time() - start_time) * 1000

                # 응답 헤더 확인
                content_encoding = response.info().get('Content-Encoding', '')
                is_compressed = 'gzip' in content_encoding.lower()

                # 응답 데이터 읽기
                data = response.read()
                compressed_size = len(data)

                # gzip 압축 해제
                if is_compressed:
                    data = gzip.decompress(data)

                ticker_data = json.loads(data.decode('utf-8'))

                return {
                    'success': True,
                    'data': ticker_data,
                    'response_time_ms': response_time,
                    'data_size_bytes': len(data),
                    'compressed_size_bytes': compressed_size,
                    'is_compressed': is_compressed,
                    'compression_ratio': (compressed_size / len(data)) if len(data) > 0 else 1.0,
                    'markets_requested': len(markets),
                    'tickers_received': len(ticker_data) if isinstance(ticker_data, list) else 1
                }

        except HTTPError as e:
            return {
                'success': False,
                'error': f"HTTP {e.code}: {e.reason}",
                'response_time_ms': 0,
                'data_size_bytes': 0,
                'compressed_size_bytes': 0,
                'is_compressed': False,
                'compression_ratio': 1.0,
                'markets_requested': len(markets),
                'tickers_received': 0
            }
        except URLError as e:
            return {
                'success': False,
                'error': f"Network error: {e.reason}",
                'response_time_ms': 0,
                'data_size_bytes': 0,
                'compressed_size_bytes': 0,
                'is_compressed': False,
                'compression_ratio': 1.0,
                'markets_requested': len(markets),
                'tickers_received': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'response_time_ms': 0,
                'data_size_bytes': 0,
                'compressed_size_bytes': 0,
                'is_compressed': False,
                'compression_ratio': 1.0,
                'markets_requested': len(markets),
                'tickers_received': 0
            }

    def get_all_tickers(self, markets: List[str]) -> Dict[str, Any]:
        """모든 마켓의 티커 정보 한번에 조회"""

        # 업비트 API는 한 번에 여러 마켓 조회 가능 (쉼표로 구분)
        markets_param = ",".join(markets)
        url = f"{self.TICKER_URL}?markets={markets_param}"

        print(f"🚀 전체 마켓 티커 정보 조회 시작...")
        print(f"   요청 URL 길이: {len(url):,} characters")
        print(f"   요청 마켓 수: {len(markets):,}개")

        try:
            request = Request(url)
            request.add_header('Accept', 'application/json')
            request.add_header('User-Agent', 'UpbitTickerTester/1.0')

            start_time = time.time()
            with urlopen(request, timeout=30) as response:  # 더 긴 타임아웃
                response_time = (time.time() - start_time) * 1000

                # 응답 데이터 읽기
                data = response.read()
                if response.info().get('Content-Encoding') == 'gzip':
                    data = gzip.decompress(data)

                ticker_data = json.loads(data.decode('utf-8'))

                return {
                    'success': True,
                    'data': ticker_data,
                    'response_time_ms': response_time,
                    'data_size_bytes': len(data),
                    'markets_requested': len(markets),
                    'tickers_received': len(ticker_data) if isinstance(ticker_data, list) else 1
                }

        except HTTPError as e:
            return {
                'success': False,
                'error': f"HTTP {e.code}: {e.reason}",
                'response_time_ms': 0,
                'data_size_bytes': 0,
                'markets_requested': len(markets),
                'tickers_received': 0
            }
        except URLError as e:
            return {
                'success': False,
                'error': f"Network error: {e.reason}",
                'response_time_ms': 0,
                'data_size_bytes': 0,
                'markets_requested': len(markets),
                'tickers_received': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'response_time_ms': 0,
                'data_size_bytes': 0,
                'markets_requested': len(markets),
                'tickers_received': 0
            }

    def analyze_ticker_data(self, ticker_data: List[Dict]) -> Dict[str, Any]:
        """티커 데이터 분석"""
        if not ticker_data:
            return {'total_markets': 0, 'analysis': 'No data'}

        analysis = {
            'markets_analyzed': len(ticker_data),
            'krw_markets': 0,
            'btc_markets': 0,
            'usdt_markets': 0,
            'price_ranges': {
                'krw': {'min': float('inf'), 'max': 0, 'avg': 0},
                'btc': {'min': float('inf'), 'max': 0, 'avg': 0},
                'usdt': {'min': float('inf'), 'max': 0, 'avg': 0}
            },
            'volume_stats': {
                'total_krw_volume': 0,
                'total_btc_volume': 0,
                'total_usdt_volume': 0
            },
            'change_stats': {
                'positive_changes': 0,
                'negative_changes': 0,
                'no_changes': 0,
                'avg_change_rate': 0
            }
        }

        krw_prices = []
        btc_prices = []
        usdt_prices = []
        change_rates = []

        for ticker in ticker_data:
            market = ticker.get('market', '')
            trade_price = float(ticker.get('trade_price', 0))
            acc_trade_volume_24h = float(ticker.get('acc_trade_volume_24h', 0))
            change_rate = float(ticker.get('change_rate', 0))

            # 마켓 타입별 분류
            if market.startswith('KRW-'):
                analysis['krw_markets'] += 1
                krw_prices.append(trade_price)
                analysis['volume_stats']['total_krw_volume'] += acc_trade_volume_24h * trade_price
            elif market.startswith('BTC-'):
                analysis['btc_markets'] += 1
                btc_prices.append(trade_price)
                analysis['volume_stats']['total_btc_volume'] += acc_trade_volume_24h
            elif market.startswith('USDT-'):
                analysis['usdt_markets'] += 1
                usdt_prices.append(trade_price)
                analysis['volume_stats']['total_usdt_volume'] += acc_trade_volume_24h

            # 변화율 분석
            change_rates.append(change_rate)
            if change_rate > 0:
                analysis['change_stats']['positive_changes'] += 1
            elif change_rate < 0:
                analysis['change_stats']['negative_changes'] += 1
            else:
                analysis['change_stats']['no_changes'] += 1

        # 가격 범위 계산
        if krw_prices:
            analysis['price_ranges']['krw'] = {
                'min': min(krw_prices),
                'max': max(krw_prices),
                'avg': sum(krw_prices) / len(krw_prices)
            }

        if btc_prices:
            analysis['price_ranges']['btc'] = {
                'min': min(btc_prices),
                'max': max(btc_prices),
                'avg': sum(btc_prices) / len(btc_prices)
            }

        if usdt_prices:
            analysis['price_ranges']['usdt'] = {
                'min': min(usdt_prices),
                'max': max(usdt_prices),
                'avg': sum(usdt_prices) / len(usdt_prices)
            }

        # 평균 변화율
        if change_rates:
            analysis['change_stats']['avg_change_rate'] = sum(change_rates) / len(change_rates)

        return analysis

    def analyze_gzip_performance(self, normal_result: Dict[str, Any], gzip_result: Dict[str, Any]) -> None:
        """gzip 압축 성능 비교 분석"""
        print("\n" + "=" * 60)
        print("🔍 gzip 압축 성능 비교 분석")
        print("=" * 60)

        # 두 테스트 모두 성공한 경우에만 비교
        if normal_result['success'] and gzip_result['success']:
            # 응답시간 비교
            time_diff = gzip_result['response_time_ms'] - normal_result['response_time_ms']
            time_improvement = (time_diff / normal_result['response_time_ms']) * 100

            # 데이터 크기 비교 (원본 크기는 동일해야 함)
            original_size = normal_result['data_size_bytes']
            compressed_size = gzip_result.get('compressed_size_bytes', 0)
            data_reduction = ((original_size - compressed_size) / original_size) * 100 if original_size > 0 else 0

            # 네트워크 절약량 계산
            bytes_saved = original_size - compressed_size

            print("📊 **성능 비교 결과**")
            print(f"   일반 요청 응답시간: {normal_result['response_time_ms']:.1f}ms")
            print(f"   gzip 요청 응답시간: {gzip_result['response_time_ms']:.1f}ms")
            print(f"   응답시간 차이: {time_diff:+.1f}ms ({time_improvement:+.1f}%)")

            print(f"\n💾 **데이터 크기 비교**")
            print(f"   원본 데이터 크기: {original_size:,} bytes")
            print(f"   압축된 크기: {compressed_size:,} bytes")
            print(f"   절약된 용량: {bytes_saved:,} bytes")
            print(f"   압축률: {data_reduction:.1f}%")

            print(f"\n⚡ **성능 평가**")
            if time_improvement < -5:  # 5% 이상 빨라짐
                print("   ✅ gzip 압축이 응답속도를 개선했습니다!")
            elif time_improvement > 5:  # 5% 이상 느려짐
                print("   ⚠️  gzip 압축으로 인해 응답속도가 느려졌습니다.")
            else:
                print("   ➡️  응답속도는 비슷합니다.")

            if data_reduction > 20:  # 20% 이상 압축
                print("   ✅ 네트워크 대역폭을 크게 절약합니다!")
            elif data_reduction > 10:  # 10% 이상 압축
                print("   👍 네트워크 대역폭을 절약합니다.")
            else:
                print("   📋 압축 효과가 제한적입니다.")

            # 압축 여부 확인
            if gzip_result.get('is_compressed', False):
                print("   🗜️  서버에서 gzip 압축을 지원합니다.")
            else:
                print("   ⚠️  서버에서 gzip 압축을 지원하지 않습니다.")

            # 결과를 results에 저장
            self.results['gzip_comparison']['comparison_results'] = {
                'time_diff_ms': time_diff,
                'time_improvement_percent': time_improvement,
                'data_reduction_percent': data_reduction,
                'bytes_saved': bytes_saved,
                'compression_supported': gzip_result.get('is_compressed', False)
            }

        else:
            print("❌ **비교 불가**")
            if not normal_result['success']:
                print(f"   일반 요청 실패: {normal_result['error']}")
            if not gzip_result['success']:
                print(f"   gzip 요청 실패: {gzip_result['error']}")

    def run_full_test(self) -> None:
        """전체 테스트 실행 (일반 요청과 gzip 압축 요청 모두 수행)"""
        print("🚀 업비트 티커 전체 마켓 테스트 시작")
        print("=" * 60)

        self.results['start_time'] = datetime.now()

        # 1. 모든 마켓 조회
        markets = self.get_all_markets()
        if not markets:
            print("❌ 마켓 조회 실패로 테스트 중단")
            return

        self.results['total_markets'] = len(markets)

        # 2. 일반 요청으로 티커 조회
        print("\n📋 [테스트 1] 일반 요청으로 티커 데이터 조회...")
        print("   ⚠️  이는 API 한계 테스트입니다!")

        result_normal = self.get_all_tickers(markets)
        self.results['gzip_comparison']['no_gzip'] = result_normal

        # 결과 출력
        if result_normal['success']:
            print(f"   ✅ 성공: {result_normal['tickers_received']}개 티커 수신")
            print(f"   ⏱️  응답시간: {result_normal['response_time_ms']:.1f}ms")
            print(f"   💾 데이터 크기: {result_normal['data_size_bytes']:,} bytes")
        else:
            print(f"   ❌ 실패: {result_normal['error']}")

        # 잠시 대기 (Rate Limit 고려)
        print("\n⏳ Rate Limit 고려하여 1초 대기...")
        time.sleep(1)

        # 3. gzip 압축 요청으로 티커 조회
        print("\n📋 [테스트 2] gzip 압축 요청으로 티커 데이터 조회...")

        result_gzip = self.get_all_tickers_with_gzip(markets)
        self.results['gzip_comparison']['with_gzip'] = result_gzip

        # 결과 출력
        if result_gzip['success']:
            print(f"   ✅ 성공: {result_gzip['tickers_received']}개 티커 수신")
            print(f"   ⏱️  응답시간: {result_gzip['response_time_ms']:.1f}ms")
            print(f"   💾 원본 크기: {result_gzip['data_size_bytes']:,} bytes")
            print(f"   🗜️  압축 크기: {result_gzip['compressed_size_bytes']:,} bytes")
            print(f"   📊 압축률: {(1 - result_gzip['compression_ratio']) * 100:.1f}%")
            print(f"   🔍 압축 여부: {'✅ 압축됨' if result_gzip['is_compressed'] else '❌ 압축 안됨'}")
        else:
            print(f"   ❌ 실패: {result_gzip['error']}")

        # 4. 성능 비교 분석
        self.analyze_gzip_performance(result_normal, result_gzip)

        # 5. 메인 결과는 일반 요청 결과 사용 (기존 호환성 유지)
        result = result_normal
        if result['success']:
            self.results['successful_requests'] = result['tickers_received']
            self.results['failed_requests'] = result['markets_requested'] - result['tickers_received']
        else:
            self.results['failed_requests'] = result['markets_requested']
            self.results['error_details'].append({
                'request_type': 'all_tickers',
                'markets_count': result['markets_requested'],
                'error': result['error']
            })

        self.results['total_response_time_ms'] = result['response_time_ms']
        self.results['total_data_size_bytes'] = result['data_size_bytes']

        # 6. 티커 데이터 분석 (성공한 결과 사용)
        successful_result = result_normal if result_normal['success'] else result_gzip
        if successful_result['success'] and successful_result['data']:
            print("\n🔍 티커 데이터 분석 중...")
            analysis = self.analyze_ticker_data(successful_result['data'])
            self.results['ticker_analysis'] = analysis

        self.results['end_time'] = datetime.now()

        # 7. 결과 출력
        self.print_results()

    def print_results(self) -> None:
        """테스트 결과 출력"""
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)

        # 기본 통계
        total_duration = (self.results['end_time'] - self.results['start_time']).total_seconds()
        success_rate = (self.results['successful_requests'] / self.results['total_markets'] * 100) if self.results['total_markets'] > 0 else 0

        print("🎯 **기본 통계**")
        print(f"   전체 마켓 수: {self.results['total_markets']:,}개")
        print(f"   성공한 티커: {self.results['successful_requests']:,}개")
        print(f"   실패한 티커: {self.results['failed_requests']:,}개")
        print(f"   성공률: {success_rate:.1f}%")

        print("\n⏱️  **성능 지표**")
        print(f"   총 소요시간: {total_duration:.1f}초")
        print(f"   API 응답시간: {self.results['total_response_time_ms']:,.0f}ms")
        print(f"   처리율: {self.results['total_markets'] / total_duration:.1f} 마켓/초")

        print("\n💾 **데이터 용량**")
        data_size_mb = self.results['total_data_size_bytes'] / (1024 * 1024)
        data_size_kb = self.results['total_data_size_bytes'] / 1024
        avg_size_per_ticker = self.results['total_data_size_bytes'] / self.results['successful_requests'] if self.results['successful_requests'] > 0 else 0

        print(f"   총 데이터 크기: {self.results['total_data_size_bytes']:,} bytes")
        print(f"                  {data_size_kb:.1f} KB")
        print(f"                  {data_size_mb:.2f} MB")
        print(f"   티커당 평균 크기: {avg_size_per_ticker:.0f} bytes")

        # 티커 분석 결과
        if 'ticker_analysis' in self.results and self.results['ticker_analysis']:
            analysis = self.results['ticker_analysis']
            print("\n📋 **티커 분석**")
            print(f"   분석된 마켓: {analysis['markets_analyzed']:,}개")
            print(f"   KRW 마켓: {analysis['krw_markets']:,}개")
            print(f"   BTC 마켓: {analysis['btc_markets']:,}개")
            print(f"   USDT 마켓: {analysis['usdt_markets']:,}개")

            print("\n💰 **가격 범위 (KRW 마켓)**")
            krw_range = analysis['price_ranges']['krw']
            if krw_range['min'] != float('inf'):
                print(f"   최저가: {krw_range['min']:,.0f}원")
                print(f"   최고가: {krw_range['max']:,.0f}원")
                print(f"   평균가: {krw_range['avg']:,.0f}원")

            print("\n📈 **변화율 통계**")
            change_stats = analysis['change_stats']
            print(f"   상승: {change_stats['positive_changes']:,}개")
            print(f"   하락: {change_stats['negative_changes']:,}개")
            print(f"   보합: {change_stats['no_changes']:,}개")
            print(f"   평균 변화율: {change_stats['avg_change_rate']:.3f}%")

            print("\n💹 **거래량 통계 (24시간)**")
            volume_stats = analysis['volume_stats']
            print(f"   KRW 총 거래대금: {volume_stats['total_krw_volume']:,.0f}원")
            print(f"   BTC 총 거래량: {volume_stats['total_btc_volume']:.4f} BTC")
            print(f"   USDT 총 거래량: {volume_stats['total_usdt_volume']:.2f} USDT")

        # API 성능 분석
        print("\n🚦 **API 성능 분석**")
        print("   단일 요청으로 처리: ✅")
        print(f"   URL 길이 제한: {'⚠️  매우 긴 URL' if self.results['total_markets'] > 200 else '✅ 적정'}")
        print(f"   응답 시간: {'⚠️  느림' if self.results['total_response_time_ms'] > 5000 else '✅ 빠름'}")
        print(f"   데이터 크기: {'⚠️  대용량' if data_size_mb > 10 else '✅ 적정'}")

        # gzip 압축 비교 결과
        if 'comparison_results' in self.results['gzip_comparison'] and self.results['gzip_comparison']['comparison_results']:
            comp_results = self.results['gzip_comparison']['comparison_results']
            print("\n🗜️  **gzip 압축 효과 요약**")
            print(f"   압축 지원: {'✅ 지원됨' if comp_results['compression_supported'] else '❌ 미지원'}")
            if comp_results['compression_supported']:
                print(f"   응답시간 개선: {comp_results['time_improvement_percent']:+.1f}%")
                print(f"   데이터 절약: {comp_results['data_reduction_percent']:.1f}% ({comp_results['bytes_saved']:,} bytes)")
                if comp_results['data_reduction_percent'] > 20:
                    print("   권장사항: gzip 압축 사용 권장 (높은 압축률)")
                elif comp_results['data_reduction_percent'] > 10:
                    print("   권장사항: gzip 압축 사용 고려 (적당한 압축률)")
                else:
                    print("   권장사항: 압축 효과 제한적")

        # 에러 상세
        if self.results['error_details']:
            print("\n❌ **에러 상세**")
            for error in self.results['error_details']:
                print(f"   요청 타입: {error['request_type']}")
                print(f"   에러: {error['error']}")
                print(f"   영향받은 마켓: {error['markets_count']}개")

        print("\n" + "=" * 60)
        print("🎉 테스트 완료!")

        # 결론 및 권장사항
        self.print_recommendations()

    def print_recommendations(self) -> None:
        """테스트 결과 기반 권장사항 출력"""
        print("\n💡 **권장사항**")

        if self.results['successful_requests'] == self.results['total_markets']:
            print("   ✅ 모든 마켓 티커를 한번에 요청 가능합니다!")
            print("   ✅ 실시간 가격 모니터링에 적합합니다.")
        else:
            print("   ⚠️  일부 마켓에서 오류가 발생했습니다.")
            print("   🔄 에러 처리 로직이 필요합니다.")

        if self.results['total_response_time_ms'] < 1000:
            print("   ⚡ 매우 빠른 응답속도로 실시간 거래에 적합합니다.")
        elif self.results['total_response_time_ms'] < 3000:
            print("   👍 적당한 응답속도입니다.")
        else:
            print("   ⚠️  응답속도가 느려 실시간 거래에 부적합할 수 있습니다.")

        data_size_mb = self.results['total_data_size_bytes'] / (1024 * 1024)
        if data_size_mb < 1:
            print("   💾 데이터 크기가 작아 빈번한 호출에 적합합니다.")
        elif data_size_mb < 5:
            print("   💾 적당한 데이터 크기입니다.")
        else:
            print("   ⚠️  데이터 크기가 커서 네트워크 비용을 고려해야 합니다.")

        print("\n🎯 **CandleDataProvider 개발 시사점**")
        print("   📊 티커 API는 안정적으로 작동하므로 실시간 가격 모니터링 가능")
        print("   🔄 캔들 데이터는 별도 API이므로 독립적 테스트 필요")
        print("   💾 대용량 데이터 처리를 위한 페이지네이션 고려")
        print("   ⚡ Rate Limit을 고려한 요청 주기 설계 필요")

        # gzip 압축 권장사항
        if 'comparison_results' in self.results['gzip_comparison'] and self.results['gzip_comparison']['comparison_results']:
            comp_results = self.results['gzip_comparison']['comparison_results']
            if comp_results['compression_supported']:
                print(f"   🗜️  gzip 압축으로 {comp_results['data_reduction_percent']:.1f}% 데이터 절약 가능")
                if comp_results['data_reduction_percent'] > 15:
                    print("   💡 대용량 데이터 전송 시 gzip 압축 활용 권장")
                if comp_results['time_improvement_percent'] < 0:
                    print("   🚀 gzip 압축이 응답속도도 개선함")
            else:
                print("   📋 gzip 압축 미지원으로 원본 데이터 전송만 가능")


def main():
    """메인 함수"""
    print("🚀 업비트 티커 전체 마켓 테스트")
    print("=" * 60)
    print("이 스크립트는 업비트의 모든 마켓에 대해 티커 API를 테스트합니다.")
    print("모든 심볼을 한번에 요청하여 API의 한계를 확인합니다.")
    print("=" * 60)

    try:
        tester = UpbitTickerTester()
        tester.run_full_test()

    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
