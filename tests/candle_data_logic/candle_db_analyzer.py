"""
캔들 DB 분석기
DB 상태를 한눈에 파악할 수 있도록 파편화 정보를 명확히 표시
기존 test_db_fragmentation_analysis.py를 기반으로 심플하게 재구성
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class FragmentInfo:
    """파편화 구간 정보"""
    start_utc: str
    end_utc: str
    count: int
    duration_minutes: int


class CandleDBAnalyzer:
    """캔들 DB 분석기"""

    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        """
        Args:
            db_path: DB 파일 경로 (기본: data/market_data.sqlite3)
        """
        self.db_path = os.path.abspath(db_path)
        self.table_name = "candles_KRW_BTC_1m"

    def analyze(self) -> Dict[str, Any]:
        """
        DB 상태 전체 분석

        Returns:
            dict: 분석 결과
        """
        if not os.path.exists(self.db_path):
            return {
                'success': False,
                'error': f'DB 파일이 존재하지 않습니다: {self.db_path}'
            }

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 기본 통계
                basic_stats = self._get_basic_stats(cursor)

                # 파편화 분석
                fragments = self._detect_fragments(cursor)

                # 연속성 분석
                continuity = self._analyze_continuity(cursor)

                return {
                    'success': True,
                    'db_path': self.db_path,
                    'basic_stats': basic_stats,
                    'fragments': fragments,
                    'continuity': continuity,
                    'summary': self._create_summary(basic_stats, fragments)
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _get_basic_stats(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        """기본 통계 정보"""
        cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
        total_count = cursor.fetchone()[0]

        if total_count == 0:
            return {
                'total_count': 0,
                'start_utc': None,
                'end_utc': None,
                'duration_minutes': 0,
                'expected_count': 0,
                'completeness_percent': 0.0
            }

        cursor.execute(f"""
            SELECT
                MIN(candle_date_time_utc) as earliest,
                MAX(candle_date_time_utc) as latest
            FROM {self.table_name}
        """)
        earliest, latest = cursor.fetchone()

        # 기간 계산
        earliest_dt = datetime.fromisoformat(earliest.replace('Z', '+00:00'))
        latest_dt = datetime.fromisoformat(latest.replace('Z', '+00:00'))
        duration = latest_dt - earliest_dt
        duration_minutes = int(duration.total_seconds() / 60)
        expected_count = duration_minutes + 1

        return {
            'total_count': total_count,
            'start_utc': latest,     # 업비트 순서: 최신이 시작
            'end_utc': earliest,     # 업비트 순서: 과거가 끝
            'duration_minutes': duration_minutes,
            'expected_count': expected_count,
            'completeness_percent': (total_count / expected_count) * 100 if expected_count > 0 else 0.0
        }

    def _detect_fragments(self, cursor: sqlite3.Cursor) -> List[FragmentInfo]:
        """파편화 구간 검출"""
        cursor.execute(f"""
            SELECT candle_date_time_utc
            FROM {self.table_name}
            ORDER BY candle_date_time_utc DESC
        """)

        all_times = [row[0] for row in cursor.fetchall()]

        if not all_times:
            return []

        fragments = []
        current_start = all_times[0]
        current_end = all_times[0]

        for i in range(1, len(all_times)):
            current_time = datetime.fromisoformat(all_times[i].replace('Z', '+00:00'))
            prev_time = datetime.fromisoformat(all_times[i-1].replace('Z', '+00:00'))

            # 1분 차이인지 확인
            expected_time = prev_time.replace(second=0, microsecond=0) - timedelta(minutes=1)
            time_diff = abs((current_time - expected_time).total_seconds())

            if time_diff <= 30:  # 연속
                current_end = all_times[i]
            else:  # 연속성 끊김
                # 현재 세그먼트 저장
                fragment = self._create_fragment_info(current_end, current_start, all_times)
                fragments.append(fragment)

                # 새 세그먼트 시작
                current_start = all_times[i]
                current_end = all_times[i]

        # 마지막 세그먼트 추가
        fragment = self._create_fragment_info(current_end, current_start, all_times)
        fragments.append(fragment)

        return fragments

    def _create_fragment_info(self, start_utc: str, end_utc: str, all_times: List[str]) -> FragmentInfo:
        """
        파편화 구간 정보 생성
        업비트 순서에 맞게 최신 → 과거 순서로 조정
        """
        count = len([t for t in all_times if start_utc <= t <= end_utc])

        start_dt = datetime.fromisoformat(start_utc.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_utc.replace('Z', '+00:00'))
        duration_minutes = int((end_dt - start_dt).total_seconds() / 60)

        # 업비트 순서: 최신(max) → 과거(min)
        latest_time = max(start_utc, end_utc)   # 최신
        earliest_time = min(start_utc, end_utc) # 과거

        return FragmentInfo(
            start_utc=latest_time,   # 최신이 시작
            end_utc=earliest_time,   # 과거가 끝
            count=count,
            duration_minutes=duration_minutes
        )

    def _analyze_continuity(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        """연속성 분석 (최신 데이터부터)"""
        cursor.execute(f"""
            WITH RECURSIVE continuous_data AS (
                -- 가장 최신 데이터부터 시작
                SELECT
                    candle_date_time_utc,
                    datetime(candle_date_time_utc, '-1 minute') as expected_prev
                FROM {self.table_name}
                WHERE candle_date_time_utc = (
                    SELECT MAX(candle_date_time_utc) FROM {self.table_name}
                )

                UNION ALL

                -- 1분 간격으로 연속된 데이터만 추적
                SELECT
                    c.candle_date_time_utc,
                    datetime(c.candle_date_time_utc, '-1 minute') as expected_prev
                FROM {self.table_name} c
                INNER JOIN continuous_data cd
                    ON datetime(c.candle_date_time_utc) = cd.expected_prev
            )
            SELECT
                MIN(candle_date_time_utc) as continuous_start,
                MAX(candle_date_time_utc) as continuous_end,
                COUNT(*) as continuous_count
            FROM continuous_data
        """)

        result = cursor.fetchone()
        if result and result[0]:
            # 업비트 순서: 최신 → 과거
            latest_time = result[1]   # MAX(candle_date_time_utc)
            earliest_time = result[0] # MIN(candle_date_time_utc)

            return {
                'has_continuous_data': True,
                'continuous_start': latest_time,   # 최신이 시작
                'continuous_end': earliest_time,   # 과거가 끝
                'continuous_count': result[2]
            }
        else:
            return {
                'has_continuous_data': False,
                'continuous_start': None,
                'continuous_end': None,
                'continuous_count': 0
            }

    def _create_summary(self, basic_stats: Dict[str, Any], fragments: List[FragmentInfo]) -> str:
        """분석 결과 요약"""
        if basic_stats['total_count'] == 0:
            return "빈 테이블 (레코드 없음)"

        summary_parts = []
        summary_parts.append(f"총 {basic_stats['total_count']:,}개 레코드")
        summary_parts.append(f"{len(fragments)}개 파편")

        return " | ".join(summary_parts)

    def print_analysis(self) -> None:
        """분석 결과를 사용자 친화적으로 출력"""
        print("📊 === 캔들 DB 분석 결과 ===")

        result = self.analyze()

        if not result['success']:
            print(f"❌ 분석 실패: {result['error']}")
            return

        basic_stats = result['basic_stats']
        fragments = result['fragments']
        continuity = result['continuity']

        # 기본 정보
        print(f"\n📁 DB 파일: {result['db_path']}")
        print(f"📊 {result['summary']}")

        if basic_stats['total_count'] == 0:
            print("📋 테이블이 비어있습니다.")
            return

        # 전체 범위 (업비트 순서: 최신 → 과거)
        print(f"\n📅 전체 범위 (최신 → 과거):")
        print(f"   최신: {basic_stats['start_utc']}")
        print(f"   과거: {basic_stats['end_utc']}")
        print(f"   기간: {basic_stats['duration_minutes']:,}분")

        # 연속성 정보 (업비트 순서: 최신 → 과거)
        if continuity['has_continuous_data']:
            print("\n🔗 최신 연속 구간 (최신 → 과거):")
            print(f"   {continuity['continuous_start']} → {continuity['continuous_end']}")
            print(f"   연속 캔들: {continuity['continuous_count']:,}개")

        # 파편화 구간들 (업비트 순서: 최신 → 과거)
        print(f"\n📂 파편화 구간 ({len(fragments)}개, 최신 → 과거):")
        for i, fragment in enumerate(fragments, 1):
            print(f"   파편{i}: {fragment.start_utc} → {fragment.end_utc} | {fragment.count:,}개")


def main():
    """CLI 실행용 메인 함수"""
    analyzer = CandleDBAnalyzer()
    analyzer.print_analysis()


if __name__ == "__main__":
    main()
