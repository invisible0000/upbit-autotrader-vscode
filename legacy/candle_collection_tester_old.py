"""
캔들 수집 테스터 - CandleDataProvider 래퍼
테스트용 통계 수집, 결과 분석, 편의 기능 제공
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.market_data.candle.candle_data_provider import CandleDataProvider
from upbit_auto_trading.infrastructure.market_data.candle.candle_models import CandleDataResponse
from upbit_auto_trading.infrastructure.repositories.sqlite_candle_repository import SqliteCandleRepository
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
from upbit_auto_trading.infrastructure.market_data.candle.overlap_analyzer import OverlapAnalyzer
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils


@dataclass
class CollectionStats:
    """수집 통계 정보"""
    # 요청 정보
    symbol: str
    timeframe: str
    count: Optional[int]
    start_time: Optional[datetime]
    end_time: Optional[datetime]

    # 수집 전 상태
    db_records_before: int
    db_time_range_before: Optional[str]

    # 수집 결과
    success: bool
    collected_count: int
    data_source: str
    response_time_ms: float

    # 수집 후 상태
    db_records_after: int
    db_time_range_after: Optional[str]
    db_records_added: int

    # Provider 통계
    api_requests_made: int
    chunks_processed: int
    cache_hits: int
    mixed_optimizations: int

    # 분석 결과
    expected_count: Optional[int] = None
    count_matches_expected: Optional[bool] = None
    gaps_filled: List[str] = None


class CandleCollectionTester:
    """
    캔들 수집 테스터 - 테스트용 래퍼 클래스

    주요 기능:
    - CandleDataProvider 래핑하여 편리한 테스트 인터페이스 제공
    - 수집 전후 DB 상태 자동 비교
    - 통계 수집 및 분석
    - 예상값 vs 실제값 비교
    """

    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        self.db_path = db_path
        self.provider: Optional[CandleDataProvider] = None

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        # 의존성 주입으로 CandleDataProvider 초기화
        db_paths = {
            'market_data': self.db_path
        }
        db_manager = DatabaseManager(db_paths)
        repository = SqliteCandleRepository(db_manager)
        upbit_client = UpbitPublicClient()
        time_utils = TimeUtils()
        overlap_analyzer = OverlapAnalyzer(repository, time_utils)

        self.provider = CandleDataProvider(
            repository=repository,
            upbit_client=upbit_client,
            overlap_analyzer=overlap_analyzer,
            chunk_size=200
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.provider and hasattr(self.provider, 'close'):
            await self.provider.close()
        # 개별 의존성들도 정리 (필요한 경우)
        if hasattr(self, 'upbit_client') and hasattr(self.upbit_client, 'close'):
            await self.upbit_client.close()

    async def collect_and_analyze(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        expected_count: Optional[int] = None
    ) -> CollectionStats:
        """
        캔들 수집 및 상세 분석

        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m')
            count: 요청 개수
            start_time: 시작 시간
            end_time: 종료 시간
            expected_count: 예상 수집 개수 (검증용)

        Returns:
            CollectionStats: 상세 수집 통계
        """
        if not self.provider:
            raise RuntimeError("Provider가 초기화되지 않았습니다. async with 사용하세요.")

        # 1. 수집 전 상태 스냅샷
        db_before = await self._get_db_snapshot()

        # 2. 캔들 수집 실행
        collection_start = time.perf_counter()
        response = await self.provider.get_candles(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            start_time=start_time,
            end_time=end_time
        )
        collection_time = (time.perf_counter() - collection_start) * 1000

        # 3. 수집 후 상태 스냅샷
        db_after = await self._get_db_snapshot()

        # 4. 통계 생성
        stats = CollectionStats(
            # 요청 정보
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            start_time=start_time,
            end_time=end_time,

            # 수집 전 상태
            db_records_before=db_before['total_records'],
            db_time_range_before=db_before['time_range'],

            # 수집 결과
            success=response.success,
            collected_count=response.total_count,
            data_source=response.data_source,
            response_time_ms=response.response_time_ms,

            # 수집 후 상태
            db_records_after=db_after['total_records'],
            db_time_range_after=db_after['time_range'],
            db_records_added=db_after['total_records'] - db_before['total_records'],

            # Provider 통계 변화 (현재 미지원으로 기본값 설정)
            api_requests_made=1,  # 임시값 - CandleDataProvider에 get_stats 메서드 필요
            chunks_processed=1,   # 임시값
            cache_hits=0,         # 임시값
            mixed_optimizations=0,  # 임시값

            # 분석 결과
            expected_count=expected_count,
        )

        # 5. 예상값 비교 분석
        if expected_count:
            stats.count_matches_expected = (stats.collected_count >= expected_count)

        return stats

    async def _get_db_snapshot(self) -> Dict[str, Any]:
        """DB 현재 상태 스냅샷"""
        import sqlite3
        import os

        if not os.path.exists(self.db_path):
            return {
                'total_records': 0,
                'time_range': None,
                'earliest': None,
                'latest': None
            }

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 레코드 수 확인
            cursor.execute("SELECT COUNT(*) FROM candles_KRW_BTC_1m")
            total_records = cursor.fetchone()[0]

            if total_records == 0:
                return {
                    'total_records': 0,
                    'time_range': None,
                    'earliest': None,
                    'latest': None
                }

            # 시간 범위 확인
            cursor.execute("""
                SELECT
                    MIN(candle_date_time_utc) as earliest,
                    MAX(candle_date_time_utc) as latest
                FROM candles_KRW_BTC_1m
            """)
            earliest, latest = cursor.fetchone()

            time_range = f"{earliest} ~ {latest}" if earliest and latest else None

            return {
                'total_records': total_records,
                'time_range': time_range,
                'earliest': earliest,
                'latest': latest
            }

        finally:
            conn.close()

    def print_stats_summary(self, stats: CollectionStats) -> None:
        """통계 요약 출력"""
        print(f"\n📊 === 수집 통계 요약 ===")
        print(f"🎯 요청: {stats.symbol} {stats.timeframe}")
        if stats.count:
            print(f"   📝 요청 개수: {stats.count}개")
        if stats.start_time:
            print(f"   📅 시작 시간: {stats.start_time}")
        if stats.end_time:
            print(f"   📅 종료 시간: {stats.end_time}")

        print(f"\n✅ 수집 결과:")
        print(f"   🔄 성공 여부: {stats.success}")
        print(f"   📈 수집 개수: {stats.collected_count}개")
        print(f"   📊 데이터 소스: {stats.data_source}")
        print(f"   ⏱️  응답 시간: {stats.response_time_ms:.1f}ms")

        print(f"\n💾 DB 상태 변화:")
        print(f"   📋 레코드: {stats.db_records_before}개 → {stats.db_records_after}개 (+{stats.db_records_added})")
        print(f"   📅 이전 범위: {stats.db_time_range_before}")
        print(f"   📅 이후 범위 (업비트 방향): {stats.db_time_range_after}")

        print(f"\n🔧 Provider 통계:")
        print(f"   🌐 API 요청: {stats.api_requests_made}회")
        print(f"   📦 청크 처리: {stats.chunks_processed}개")
        print(f"   💨 캐시 히트: {stats.cache_hits}회")
        print(f"   🔄 혼합 최적화: {stats.mixed_optimizations}회")

        if stats.expected_count:
            print(f"\n🎯 예상값 비교:")
            print(f"   📝 예상 개수: {stats.expected_count}개")
            print(f"   ✅ 예상 충족: {stats.count_matches_expected}")

    def print_detailed_analysis(self, stats: CollectionStats) -> None:
        """상세 분석 출력"""
        self.print_stats_summary(stats)

        print(f"\n🔍 === 상세 분석 ===")

        # 효율성 분석
        if stats.api_requests_made > 0:
            efficiency = stats.collected_count / stats.api_requests_made
            print(f"📈 API 효율성: {efficiency:.1f}개/요청")

        # DB 증가율 분석
        if stats.db_records_added > 0:
            increase_rate = (stats.db_records_added / stats.collected_count) * 100
            print(f"💾 DB 증가율: {increase_rate:.1f}% ({stats.db_records_added}/{stats.collected_count})")

        # 데이터 소스 분석
        if stats.data_source == "mixed":
            print(f"🔄 혼합 최적화 성공: DB + API 조합 사용")
        elif stats.data_source == "db":
            print(f"💾 완전 DB 최적화: API 요청 없이 DB만 사용")
        elif stats.data_source == "api":
            print(f"🌐 API 중심 수집: 주로 새로운 데이터 수집")

        # 예상값 검증
        if stats.expected_count and not stats.count_matches_expected:
            shortage = stats.expected_count - stats.collected_count
            print(f"⚠️  수집 부족: {shortage}개 부족 (예상 {stats.expected_count}개, 실제 {stats.collected_count}개)")


# 편의 함수들
async def test_basic_collection(
    symbol: str = "KRW-BTC",
    timeframe: str = "1m",
    count: int = 100,
    expected_count: Optional[int] = None
) -> CollectionStats:
    """기본 수집 테스트 (편의 함수)"""
    async with CandleCollectionTester() as tester:
        return await tester.collect_and_analyze(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            expected_count=expected_count or count
        )

async def test_time_range_collection(
    symbol: str = "KRW-BTC",
    timeframe: str = "1m",
    start_time: datetime = None,
    end_time: datetime = None,
    expected_count: Optional[int] = None
) -> CollectionStats:
    """시간 범위 수집 테스트 (편의 함수)"""
    async with CandleCollectionTester() as tester:
        return await tester.collect_and_analyze(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time,
            expected_count=expected_count
        )


if __name__ == "__main__":
    # 예제 실행
    async def example_test():
        print("🧪 캔들 수집 테스터 예제")

        # 100개 수집 테스트
        stats = await test_basic_collection(count=100, expected_count=100)

        # 결과 출력
        async with CandleCollectionTester() as tester:
            tester.print_detailed_analysis(stats)

    asyncio.run(example_test())
