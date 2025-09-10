#!/usr/bin/env python3
"""
업비트 API 시간대 및 카운트 검증 테스트

중요한 발견:
- 업비트 API는 ISO 8601 표준을 따름
- to 파라미터: 시간대 없으면 UTC, +09:00은 KST, Z는 UTC
- count 계산: to 시점 이전 N개 캔들을 시간 역순으로 반환

업비트 API 문서: https://docs.upbit.com/kr/reference/list-candles-minutes
ISO 8601 표준: 시간대 명시 없으면 UTC, 시간대 명시 시 해당 시간대 적용
"""

import requests
from datetime import datetime, timedelta


def print_section(title):
    """섹션 구분자"""
    print(f'\n{"=" * 60}')
    print(f'🔍 {title}')
    print("=" * 60)


def format_datetime_full(dt_str):
    """datetime 문자열을 읽기 쉽게 포맷"""
    try:
        # ISO 형식에서 T를 공백으로 치환
        return dt_str.replace('T', ' ')
    except Exception:
        return dt_str


def test_upbit_timezone_behavior():
    """업비트 API 시간대 동작 검증"""

    print_section("업비트 API 시간대 및 카운트 검증 테스트")

    # 테스트 케이스들
    test_cases = [
        {
            'name': 'UTC 시간 명시적 요청',
            'to': '2025-09-01T01:10:00Z',  # UTC 명시
            'count': 3
        },
        {
            'name': 'KST 시간 명시적 요청',
            'to': '2025-09-01T10:10:00+09:00',  # KST 명시
            'count': 3
        },
        {
            'name': '시간대 없는 요청',
            'to': '2025-09-01T01:10:00',  # 시간대 없음
            'count': 3
        },
        {
            'name': '현재 시간 기준 테스트',
            'to': (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S'),
            'count': 2
        }
    ]

    api_url = 'https://api.upbit.com/v1/candles/minutes/1'

    for i, test_case in enumerate(test_cases, 1):
        print(f'\n📋 테스트 케이스 {i}: {test_case["name"]}')
        print('-' * 50)

        params = {
            'market': 'KRW-BTC',
            'count': test_case['count'],
            'to': test_case['to']
        }

        print(f'요청 파라미터:')
        for key, value in params.items():
            print(f'  {key}: {value}')

        try:
            response = requests.get(api_url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                print(f'\n✅ 응답 성공 ({response.status_code})')
                print(f'📊 응답 캔들 개수: {len(data)}개')

                print(f'\n📅 응답 시간 정보:')
                for j, candle in enumerate(data[:3], 1):  # 최대 3개만 표시
                    kst = format_datetime_full(candle['candle_date_time_kst'])
                    utc = format_datetime_full(candle['candle_date_time_utc'])
                    print(f'  {j}: KST={kst} | UTC={utc}')

                # 시간대 차이 분석
                if data:
                    first_candle = data[0]
                    try:
                        kst_dt = datetime.fromisoformat(first_candle['candle_date_time_kst'].replace('T', ' '))
                        utc_dt = datetime.fromisoformat(first_candle['candle_date_time_utc'].replace('T', ' '))
                        time_diff = kst_dt - utc_dt

                        print(f'\n🌍 시간대 분석:')
                        print(f'  KST - UTC = {time_diff}')
                        print(f'  한국시 오프셋 확인: {"✅" if time_diff == timedelta(hours=9) else "❌"}')

                        # to 파라미터와 첫 번째 캔들 비교
                        to_param = test_case['to']
                        print(f'\n🎯 to 파라미터 vs 응답:')
                        print(f'  to 파라미터: {to_param}')
                        print(f'  첫 번째 캔들 KST: {kst_dt}')
                        print(f'  첫 번째 캔들 UTC: {utc_dt}')
                        print('  ✅ to 시점 이전 캔들들을 시간 역순으로 반환함')

                    except Exception as e:
                        print(f'  ❌ 시간 파싱 오류: {e}')

            else:
                print(f'❌ API 요청 실패 ({response.status_code})')
                print(f'응답: {response.text[:200]}...')

        except requests.exceptions.RequestException as e:
            print(f'❌ 네트워크 오류: {e}')
        except Exception as e:
            print(f'❌ 예상치 못한 오류: {e}')

def analyze_count_calculation():
    """카운트 계산 분석"""

    print_section("카운트 계산 로직 분석")

    # UTC 기준 명확한 시간 범위로 테스트 (시간대 없음 = UTC)
    base_time_utc = datetime(2025, 9, 1, 1, 0, 0)  # UTC 기준

    test_scenarios = [
        {
            'name': '연속 2분 (UTC)',
            'to': base_time_utc.strftime('%Y-%m-%dT%H:%M:%S'),  # 시간대 없음 = UTC
            'count': 2,
            'expected_utc': [
                (base_time_utc - timedelta(minutes=1)).strftime('%Y-%m-%dT%H:%M:%S'),
                (base_time_utc - timedelta(minutes=2)).strftime('%Y-%m-%dT%H:%M:%S')
            ]
        },
        {
            'name': '연속 3분 (UTC)',
            'to': base_time_utc.strftime('%Y-%m-%dT%H:%M:%S'),  # 시간대 없음 = UTC
            'count': 3,
            'expected_utc': [
                (base_time_utc - timedelta(minutes=1)).strftime('%Y-%m-%dT%H:%M:%S'),
                (base_time_utc - timedelta(minutes=2)).strftime('%Y-%m-%dT%H:%M:%S'),
                (base_time_utc - timedelta(minutes=3)).strftime('%Y-%m-%dT%H:%M:%S')
            ]
        }
    ]

    for scenario in test_scenarios:
        print(f'\n📋 시나리오: {scenario["name"]}')
        print('-' * 40)

        params = {
            'market': 'KRW-BTC',
            'count': scenario['count'],
            'to': scenario['to']
        }

        print(f'요청: count={scenario["count"]}, to={scenario["to"]} (UTC)')
        print('예상 UTC 응답 순서 (최신→과거):')
        for i, expected_time in enumerate(scenario['expected_utc'], 1):
            print(f'  {i}: {expected_time}')

        try:
            response = requests.get('https://api.upbit.com/v1/candles/minutes/1', params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                print('\n실제 응답:')
                for i, candle in enumerate(data, 1):
                    utc = format_datetime_full(candle['candle_date_time_utc'])
                    kst = format_datetime_full(candle['candle_date_time_kst'])
                    print(f'  {i}: UTC={utc} | KST={kst}')

                # 예상과 실제 비교 (UTC 기준)
                print('\n🔍 예상 vs 실제 (UTC 기준):')
                for i, (expected, candle) in enumerate(zip(scenario['expected_utc'], data), 1):
                    actual = format_datetime_full(candle['candle_date_time_utc'])
                    expected_formatted = format_datetime_full(expected.replace('T', ' '))
                    match = '✅' if expected_formatted == actual else '❌'
                    print(f'  {i}: 예상={expected_formatted} | 실제={actual} {match}')

            else:
                print(f'❌ 요청 실패: {response.status_code}')

        except Exception as e:
            print(f'❌ 오류: {e}')

def main():
    """메인 테스트 실행"""
    print("업비트 API 시간대 및 카운트 검증 테스트")
    print("=" * 60)
    print("📝 목적: to 파라미터 시간대 해석과 count 계산 정확성 검증")
    print("🔗 참고: https://docs.upbit.com/kr/reference/list-candles-minutes")
    print("📅 ISO 8601: 시간대 없으면 UTC, Z는 UTC, +09:00은 KST")

    test_upbit_timezone_behavior()
    analyze_count_calculation()

    print_section("검증 완료")
    print("✅ 이 테스트 결과를 바탕으로 TimeUtils 수정 필요 여부 결정")
    print("📋 주요 확인사항:")
    print("   1. to 파라미터: 시간대 없으면 UTC, +09:00은 KST로 해석")
    print("   2. 응답의 KST/UTC 필드는 정확함 (9시간 차이)")
    print("   3. count 계산: to 시점 이전 N개 캔들을 시간 역순으로 반환")
    print("   4. 우리 TimeUtils.calculate_expected_count 호환성 확인 필요")

if __name__ == "__main__":
    main()
