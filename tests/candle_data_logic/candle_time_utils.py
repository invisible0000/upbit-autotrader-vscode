"""
캔들 시간 계산 유틸리티
테스트 시나리오에서 사용할 시간 계산 및 테스트 조건 자동 생성 기능 제공
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class FragmentType(Enum):
    """파편화 타입"""
    CONTINUOUS = "continuous"    # 연속 데이터
    GAP = "gap"                 # 공백 구간


@dataclass
class TimeRange:
    """시간 범위"""
    start: datetime
    end: datetime
    count: int

    @property
    def duration_minutes(self) -> int:
        """기간 (분)"""
        return int((self.end - self.start).total_seconds() / 60)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'start_utc': self.start.strftime('%Y-%m-%dT%H:%M:%S'),
            'end_utc': self.end.strftime('%Y-%m-%dT%H:%M:%S'),
            'count': self.count,
            'duration_minutes': self.duration_minutes
        }


@dataclass
class TestFragment:
    """테스트용 파편화 구간"""
    fragment_type: FragmentType
    start_offset_minutes: int    # 기준 시간으로부터 오프셋
    count: int                   # 캔들 개수 (GAP의 경우 공백 기간)
    description: str = ""

    def get_time_range(self, base_time: datetime) -> TimeRange:
        """기준 시간 기반으로 실제 시간 범위 계산"""
        start = base_time + timedelta(minutes=self.start_offset_minutes)
        if self.fragment_type == FragmentType.CONTINUOUS:
            end = start + timedelta(minutes=self.count - 1)
            return TimeRange(start, end, self.count)
        else:  # GAP
            end = start + timedelta(minutes=self.count - 1)
            return TimeRange(start, end, 0)  # 공백이므로 캔들 수는 0


class CandleTimeUtils:
    """캔들 시간 계산 유틸리티"""

    @staticmethod
    def calculate_end_time(start_time: str, count: int) -> str:
        """
        시작 시간과 개수로 종료 시간 계산

        주의: 캔들은 역순으로 배치됨 (최신 → 과거)
        start_time이 최신이고, end_time이 가장 과거

        Args:
            start_time: 시작 시간 (최신, UTC) 예: '2025-09-08T00:00:00'
            count: 캔들 개수

        Returns:
            str: 종료 시간 (가장 과거, UTC)
        """
        start_dt = datetime.fromisoformat(start_time).replace(tzinfo=timezone.utc)
        end_dt = start_dt - timedelta(minutes=count - 1)  # 과거 방향으로 계산
        return end_dt.strftime('%Y-%m-%dT%H:%M:%S')

    @staticmethod
    def calculate_count(start_time: str, end_time: str) -> int:
        """
        시작 시간과 종료 시간으로 캔들 개수 계산

        Args:
            start_time: 시작 시간 (UTC)
            end_time: 종료 시간 (UTC)

        Returns:
            int: 캔들 개수
        """
        start_dt = datetime.fromisoformat(start_time).replace(tzinfo=timezone.utc)
        end_dt = datetime.fromisoformat(end_time).replace(tzinfo=timezone.utc)
        duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
        return duration_minutes + 1

    @staticmethod
    def calculate_start_time(end_time: str, count: int) -> str:
        """
        종료 시간과 개수로 시작 시간 계산 (역산)

        주의: 캔들은 역순으로 배치됨 (최신 → 과거)
        end_time이 가장 과거이고, start_time이 최신

        Args:
            end_time: 종료 시간 (가장 과거, UTC)
            count: 캔들 개수

        Returns:
            str: 시작 시간 (최신, UTC)
        """
        end_dt = datetime.fromisoformat(end_time).replace(tzinfo=timezone.utc)
        start_dt = end_dt + timedelta(minutes=count - 1)  # 미래 방향으로 계산
        return start_dt.strftime('%Y-%m-%dT%H:%M:%S')

    @staticmethod
    def add_minutes(time_str: str, minutes: int) -> str:
        """
        시간에 분 추가

        Args:
            time_str: 기준 시간 (UTC)
            minutes: 추가할 분 (음수 가능)

        Returns:
            str: 계산된 시간 (UTC)
        """
        dt = datetime.fromisoformat(time_str).replace(tzinfo=timezone.utc)
        result_dt = dt + timedelta(minutes=minutes)
        return result_dt.strftime('%Y-%m-%dT%H:%M:%S')

    @staticmethod
    def get_time_info(start_time: str, count: int) -> Dict[str, Any]:
        """
        시작 시간과 개수로 상세 시간 정보 계산

        주의: 캔들은 역순 배치 (최신 → 과거)
        start_time: 최신 캔들 시간
        end_time: 가장 오래된 캔들 시간

        Args:
            start_time: 시작 시간 (최신, UTC)
            count: 캔들 개수

        Returns:
            dict: 상세 시간 정보
        """
        end_time = CandleTimeUtils.calculate_end_time(start_time, count)

        start_dt = datetime.fromisoformat(start_time).replace(tzinfo=timezone.utc)
        end_dt = datetime.fromisoformat(end_time).replace(tzinfo=timezone.utc)
        duration = start_dt - end_dt  # 최신 - 과거 = 양수

        return {
            'start_utc': start_time,        # 최신 캔들
            'end_utc': end_time,           # 가장 과거 캔들
            'count': count,
            'duration_minutes': int(duration.total_seconds() / 60),
            'duration_hours': round(duration.total_seconds() / 3600, 2),
            'start_kst': CandleTimeUtils.utc_to_kst(start_time),
            'end_kst': CandleTimeUtils.utc_to_kst(end_time)
        }

    @staticmethod
    def utc_to_kst(utc_time: str) -> str:
        """UTC를 KST로 변환"""
        utc_dt = datetime.fromisoformat(utc_time).replace(tzinfo=timezone.utc)
        kst_dt = utc_dt + timedelta(hours=9)
        return kst_dt.strftime('%Y-%m-%dT%H:%M:%S')

    @staticmethod
    def create_fragmented_scenario(
        base_time: str,
        fragments: List[TestFragment]
    ) -> Dict[str, Any]:
        """
        파편화 시나리오 생성

        Args:
            base_time: 기준 시간 (UTC)
            fragments: 파편화 구간 정의 리스트

        Returns:
            dict: 생성된 시나리오 정보
        """
        base_dt = datetime.fromisoformat(base_time).replace(tzinfo=timezone.utc)

        scenario_fragments = []
        total_candles = 0

        for fragment in fragments:
            time_range = fragment.get_time_range(base_dt)

            fragment_info = {
                'type': fragment.fragment_type.value,
                'description': fragment.description,
                'start_offset_minutes': fragment.start_offset_minutes,
                **time_range.to_dict()
            }

            scenario_fragments.append(fragment_info)

            if fragment.fragment_type == FragmentType.CONTINUOUS:
                total_candles += fragment.count

        # 전체 시간 범위 계산
        all_times = []
        for fragment in scenario_fragments:
            if fragment['type'] == 'continuous':
                all_times.extend([fragment['start_utc'], fragment['end_utc']])

        overall_start = min(all_times) if all_times else base_time
        overall_end = max(all_times) if all_times else base_time

        return {
            'base_time': base_time,
            'fragments': scenario_fragments,
            'total_candles': total_candles,
            'overall_range': {
                'start_utc': overall_start,
                'end_utc': overall_end,
                'duration_minutes': CandleTimeUtils.calculate_count(overall_start, overall_end) - 1
            },
            'fragment_count': len([f for f in scenario_fragments if f['type'] == 'continuous']),
            'gap_count': len([f for f in scenario_fragments if f['type'] == 'gap'])
        }


class TestScenarioBuilder:
    """테스트 시나리오 자동 생성기"""

    def __init__(self, base_time: str = "2025-09-08T00:00:00"):
        """
        Args:
            base_time: 기준 시간 (UTC)
        """
        self.base_time = base_time
        self.utils = CandleTimeUtils()

    def create_basic_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """베이직 테스트 시나리오들 생성"""
        scenarios = {}

        for count in [100, 200, 300, 1000]:
            time_info = self.utils.get_time_info(self.base_time, count)

            scenarios[f'basic_{count}'] = {
                'description': f'베이직 {count}개 캔들 수집 테스트',
                'test_type': 'basic_collection',
                'clean_start': True,
                'generation': {
                    'start_time': self.base_time,
                    'count': count
                },
                'collection': {
                    'symbol': 'KRW-BTC',
                    'timeframe': '1m',
                    'count': count,
                    'end_time': time_info['end_utc']
                },
                'expected': {
                    'min_records': count,
                    'time_range': {
                        'start': self.base_time,
                        'end': time_info['end_utc']
                    },
                    'api_calls': 1,
                    'data_source': 'api'
                },
                'time_info': time_info
            }

        return scenarios

    def create_fragmented_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """파편화 테스트 시나리오들 생성"""
        scenarios = {}

        # 시나리오 1: 간단한 2개 파편
        fragments_simple = [
            TestFragment(
                FragmentType.CONTINUOUS,
                start_offset_minutes=0,
                count=50,
                description="첫 번째 연속 구간"
            ),
            TestFragment(
                FragmentType.GAP,
                start_offset_minutes=50,
                count=30,
                description="30분 공백"
            ),
            TestFragment(
                FragmentType.CONTINUOUS,
                start_offset_minutes=80,
                count=50,
                description="두 번째 연속 구간"
            )
        ]

        scenario_info = self.utils.create_fragmented_scenario(self.base_time, fragments_simple)

        scenarios['fragmented_simple'] = {
            'description': '간단한 파편화 (2개 구간 + 1개 공백)',
            'test_type': 'fragmented_collection',
            'clean_start': True,
            'scenario_info': scenario_info,
            'expected': {
                'fragment_count': 2,
                'gap_count': 1,
                'total_candles': 100,
                'api_calls': 2  # 공백 구간 때문에 2번 호출 예상
            }
        }

        return scenarios

    def create_overlap_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """겹침 테스트 시나리오들 생성"""
        scenarios = {}

        # 시나리오: DB에 100개 있고 200개 요청 (50% 겹침)
        scenarios['overlap_50_percent'] = {
            'description': 'DB 100개 보유 상태에서 200개 요청 (50% 겹침)',
            'test_type': 'overlap_collection',
            'setup': {
                'clean_start': True,
                'pre_generate': {
                    'start_time': self.base_time,
                    'count': 100
                }
            },
            'collection': {
                'symbol': 'KRW-BTC',
                'timeframe': '1m',
                'count': 200,
                'end_time': self.utils.calculate_end_time(self.base_time, 200)
            },
            'expected': {
                'min_records': 200,
                'overlap_optimization': True,
                'api_calls': 1,  # 겹치지 않는 100개만 API 요청
                'db_utilization': '50%'
            }
        }

        return scenarios

    def get_all_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """모든 시나리오 반환"""
        all_scenarios = {}

        all_scenarios.update(self.create_basic_scenarios())
        all_scenarios.update(self.create_fragmented_scenarios())
        all_scenarios.update(self.create_overlap_scenarios())

        return all_scenarios


def main():
    """CLI 실행용 메인 함수"""
    print("⏰ === 캔들 시간 계산 유틸리티 ===")

    utils = CandleTimeUtils()

    # 기본 시간 계산 예시
    print("\n🔢 기본 계산 예시:")
    start_time = "2025-09-08T00:00:00"
    count = 100

    time_info = utils.get_time_info(start_time, count)
    print(f"   시작: {time_info['start_utc']} ({time_info['start_kst']} KST)")
    print(f"   종료: {time_info['end_utc']} ({time_info['end_kst']} KST)")
    print(f"   개수: {time_info['count']}개")
    print(f"   기간: {time_info['duration_minutes']}분 ({time_info['duration_hours']}시간)")

    # 테스트 시나리오 생성 예시
    print("\n🎯 테스트 시나리오 생성 예시:")
    builder = TestScenarioBuilder()
    scenarios = builder.get_all_scenarios()

    print(f"   총 {len(scenarios)}개 시나리오 생성됨:")
    for name, scenario in scenarios.items():
        print(f"   - {name}: {scenario['description']}")


if __name__ == "__main__":
    main()
