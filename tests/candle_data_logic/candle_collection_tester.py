"""
CandleCollectionTester v2.0 - CandleDataProvider v4.1 전용 성능 측정 도구

CandleDataProvider의 실제 API(plan_collection, start_collection, get_next_chunk 등)에 맞춰
성능 측정과 통계 수집에 특화된 테스터

주요 기능:
- 실제 CandleDataProvider API 사용
- 청크 단위 진행률 추적
- API 호출 성능 측정
- DB 상태 변화 추적
- 상세 성능 통계 제공
"""

import sqlite3
import os
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("CandleCollectionTester")

from upbit_auto_trading.infrastructure.market_data.candle.candle_data_provider import CandleDataProvider
from upbit_auto_trading.infrastructure.repositories.sqlite_candle_repository import SqliteCandleRepository
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
from upbit_auto_trading.infrastructure.market_data.candle.overlap_analyzer import OverlapAnalyzer
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils


@dataclass
class PerformanceStats:
    """성능 통계 정보"""
    # 요청 정보
    symbol: str
    timeframe: str
    count: Optional[int]
    to: Optional[datetime]
    end: Optional[datetime]

    # 계획 정보
    total_count: int
    estimated_chunks: int
    estimated_duration_seconds: float

    # 실행 통계
    actual_chunks: int
    actual_duration_ms: float
    chunks_per_second: float
    candles_per_second: float

    # DB 통계
    db_records_before: int
    db_records_after: int
    db_records_added: int

    # 청크별 상세 통계
    chunk_times_ms: List[float]
    total_api_calls: int
    avg_chunk_time_ms: float
    min_chunk_time_ms: float
    max_chunk_time_ms: float

    # 완료 상태
    success: bool
    error_message: Optional[str] = None


class CandleCollectionTesterV2:
    """
    CandleDataProvider v4.1 전용 성능 측정 도구

    실제 API를 사용하여 청크 단위로 진행 추적하며 상세한 성능 통계 제공
    """

    def __init__(self, db_path: str = "data/market_data.sqlite3", chunk_size: int = 200):
        self.db_path = db_path
        self.chunk_size = min(chunk_size, 200)  # 업비트 제한 준수 (최대 200)
        self.provider: Optional[CandleDataProvider] = None
        self.table_name = "candles_KRW_BTC_1m"

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        # CandleDataProvider 초기화 (의존성 주입)
        db_paths = {'market_data': self.db_path}
        db_manager = DatabaseManager(db_paths)
        repository = SqliteCandleRepository(db_manager)

        # Zero-429 정책: 통합 Rate Limiter 사용 (자동으로 Zero-429 정책 적용됨)
        upbit_client = UpbitPublicClient()
        time_utils = TimeUtils()
        overlap_analyzer = OverlapAnalyzer(repository, time_utils)

        self.provider = CandleDataProvider(
            repository=repository,
            upbit_client=upbit_client,
            overlap_analyzer=overlap_analyzer,
            chunk_size=self.chunk_size
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        try:
            # CandleDataProvider HTTP 클라이언트 정리
            if hasattr(self.provider, 'upbit_client') and self.provider.upbit_client:
                if hasattr(self.provider.upbit_client, 'close'):
                    await self.provider.upbit_client.close()
                    logger.debug("✅ HTTP 클라이언트 정리 완료")
        except Exception as e:
            logger.warning(f"HTTP 클라이언트 정리 중 오류: {e}")

        try:
            # SqliteCandleRepository의 DatabaseManager 정리
            if hasattr(self.provider, 'repository') and self.provider.repository:
                if hasattr(self.provider.repository, 'db_manager'):
                    self.provider.repository.db_manager.close_all()
                    logger.debug("✅ Repository DB 매니저 정리 완료")
        except Exception as e:
            logger.warning(f"Repository DB 연결 정리 중 오류: {e}")

        try:
            # 테스터 자체의 DB 매니저 정리 (올바른 메서드명 사용)
            if hasattr(self, 'db_manager') and self.db_manager:
                self.db_manager.close_all()
                logger.debug("✅ 테스터 DB 연결 정리 완료")
        except Exception as e:
            logger.warning(f"테스터 DB 연결 정리 중 오류: {e}")

        try:
            # 전역 DatabaseConnectionProvider 정리
            from upbit_auto_trading.infrastructure.database.database_manager import DatabaseConnectionProvider
            provider_instance = DatabaseConnectionProvider()
            if hasattr(provider_instance, '_db_manager') and provider_instance._db_manager:
                provider_instance._db_manager.close_all()
                logger.debug("✅ 전역 DB 연결 제공자 정리 완료")
        except Exception as e:
            logger.warning(f"전역 DB 연결 제공자 정리 중 오류: {e}")

    async def test_collection_performance(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        to: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> PerformanceStats:
        """
        캔들 수집 성능 테스트

        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m')
            count: 요청 개수
            to: 시작 시간
            end: 종료 시간

        Returns:
            PerformanceStats: 상세 성능 통계
        """
        if not self.provider:
            raise RuntimeError("Provider가 초기화되지 않았습니다. async with 사용하세요.")

        print(f"🚀 성능 테스트 시작: {symbol} {timeframe}")
        if count:
            print(f"   📊 요청: {count}개")
        if to:
            print(f"   📅 시작 시간: {to}")
        if end:
            print(f"   📅 종료 시간: {end}")

        # 1. 수집 전 DB 상태
        db_before = self._get_db_record_count()

        try:
            # 2. 계획 수립
            plan_start = time.perf_counter()
            plan = self.provider.plan_collection(symbol, timeframe, count, to, end)
            plan_time_ms = (time.perf_counter() - plan_start) * 1000

            print(f"📋 계획 수립 완료: {plan_time_ms:.1f}ms")
            print(f"   📊 예상: {plan.total_count}개 캔들, {plan.estimated_chunks}청크")
            print(f"   ⏱️ 예상 소요시간: {plan.estimated_duration_seconds:.1f}초")

            # 3. 수집 시작
            collection_start = time.perf_counter()
            request_id = self.provider.start_collection(symbol, timeframe, count, to, end)

            print(f"🎯 수집 시작: ID={request_id}")

            # 4. 청크별 수집 실행
            chunk_times = []
            chunk_count = 0

            while True:
                # 다음 청크 가져오기
                chunk_info = self.provider.get_next_chunk(request_id)
                if chunk_info is None:
                    break

                chunk_count += 1
                chunk_start = time.perf_counter()

                print(f"📦 청크 {chunk_count}/{plan.estimated_chunks} 처리 중...")
                print(f"   🆔 청크 ID: {chunk_info.chunk_id}")
                print(f"   📊 개수: {chunk_info.count}")
                if chunk_info.to:
                    print(f"   📅 to: {chunk_info.to}")
                if chunk_info.end:
                    print(f"   📅 end: {chunk_info.end}")

                # 청크 완료 처리
                await self.provider.mark_chunk_completed(request_id)

                chunk_time_ms = (time.perf_counter() - chunk_start) * 1000
                chunk_times.append(chunk_time_ms)

                print(f"   ✅ 완료: {chunk_time_ms:.1f}ms")

            # 5. 수집 완료
            total_duration_ms = (time.perf_counter() - collection_start) * 1000

            # 6. 수집 후 DB 상태
            db_after = self._get_db_record_count()

            # 7. 통계 계산
            chunk_times_ms = chunk_times if chunk_times else [0.0]

            stats = PerformanceStats(
                # 요청 정보
                symbol=symbol,
                timeframe=timeframe,
                count=count,
                to=to,
                end=end,

                # 계획 정보
                total_count=plan.total_count,
                estimated_chunks=plan.estimated_chunks,
                estimated_duration_seconds=plan.estimated_duration_seconds,

                # 실행 통계
                actual_chunks=chunk_count,
                actual_duration_ms=total_duration_ms,
                chunks_per_second=chunk_count / (total_duration_ms / 1000) if total_duration_ms > 0 else 0,
                candles_per_second=plan.total_count / (total_duration_ms / 1000) if total_duration_ms > 0 else 0,

                # DB 통계
                db_records_before=db_before,
                db_records_after=db_after,
                db_records_added=db_after - db_before,

                # 청크별 상세 통계
                chunk_times_ms=chunk_times_ms,
                total_api_calls=chunk_count,  # 청크 수 = API 호출 수
                avg_chunk_time_ms=sum(chunk_times_ms) / len(chunk_times_ms),
                min_chunk_time_ms=min(chunk_times_ms),
                max_chunk_time_ms=max(chunk_times_ms),

                # 완료 상태
                success=True
            )

            print(f"✅ 수집 완료: {total_duration_ms:.1f}ms")
            return stats

        except Exception as e:
            error_stats = PerformanceStats(
                symbol=symbol, timeframe=timeframe, count=count, to=to, end=end,
                total_count=0, estimated_chunks=0, estimated_duration_seconds=0,
                actual_chunks=0, actual_duration_ms=0, chunks_per_second=0, candles_per_second=0,
                db_records_before=db_before, db_records_after=self._get_db_record_count(), db_records_added=0,
                chunk_times_ms=[], total_api_calls=0, avg_chunk_time_ms=0, min_chunk_time_ms=0, max_chunk_time_ms=0,
                success=False, error_message=str(e)
            )
            return error_stats

    def _get_db_record_count(self) -> int:
        """DB 레코드 수 조회"""
        if not os.path.exists(self.db_path):
            return 0

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
                return cursor.fetchone()[0]
        except sqlite3.OperationalError:
            # 테이블이 존재하지 않는 경우
            return 0
        except Exception:
            return 0

    def print_performance_summary(self, stats: PerformanceStats) -> None:
        """성능 통계 요약 출력"""
        print("\n📊 === 성능 테스트 결과 ===")

        if not stats.success:
            print(f"❌ 테스트 실패: {stats.error_message}")
            return

        print(f"🎯 요청: {stats.symbol} {stats.timeframe}")
        if stats.count:
            print(f"   📝 개수: {stats.count}개")
        if stats.to:
            print(f"   📅 시작: {stats.to}")
        if stats.end:
            print(f"   📅 종료: {stats.end}")

        print(f"\n📋 계획 vs 실제:")
        print(f"   📊 캔들: 예상 {stats.total_count}개")
        print(f"   📦 청크: 예상 {stats.estimated_chunks}개 → 실제 {stats.actual_chunks}개")
        print(f"   ⏱️ 소요시간: 예상 {stats.estimated_duration_seconds:.1f}초 → 실제 {stats.actual_duration_ms / 1000:.1f}초")

        print("\n🚀 성능 지표:")
        print(f"   📦 청크/초: {stats.chunks_per_second:.2f}")
        print(f"   📊 캔들/초: {stats.candles_per_second:.1f}")
        print(f"   🌐 API 호출: {stats.total_api_calls}회")

        print("\n💾 DB 상태:")
        print(f"   📋 이전: {stats.db_records_before:,}개")
        print(f"   📋 이후: {stats.db_records_after:,}개")
        print(f"   📈 증가: +{stats.db_records_added:,}개")

        print("\n⏱️ 청크 처리 시간:")
        print(f"   평균: {stats.avg_chunk_time_ms:.1f}ms")
        print(f"   최소: {stats.min_chunk_time_ms:.1f}ms")
        print(f"   최대: {stats.max_chunk_time_ms:.1f}ms")

    def print_detailed_analysis(self, stats: PerformanceStats) -> None:
        """상세 성능 분석 출력"""
        self.print_performance_summary(stats)

        if not stats.success:
            return

        print("\n🔍 === 상세 분석 ===")

        # 효율성 분석
        if stats.actual_duration_ms > 0 and stats.estimated_duration_seconds > 0:
            speed_ratio = (stats.estimated_duration_seconds * 1000) / stats.actual_duration_ms
            if speed_ratio > 1.1:
                print(f"🚀 예상보다 빠름: {speed_ratio:.1f}배 빠른 수집")
            elif speed_ratio < 0.9:
                print(f"🐌 예상보다 느림: {1 / speed_ratio:.1f}배 느린 수집")
            else:
                print(f"🎯 예상과 유사한 성능: {speed_ratio:.1f}배")

        # 청크 처리 균일성 분석
        if len(stats.chunk_times_ms) > 1:
            import statistics
            std_dev = statistics.stdev(stats.chunk_times_ms)
            cv = std_dev / stats.avg_chunk_time_ms if stats.avg_chunk_time_ms > 0 else 0

            if cv < 0.2:
                print(f"📊 안정적인 청크 처리: 변동계수 {cv:.2f}")
            elif cv < 0.5:
                print(f"📊 보통 청크 처리: 변동계수 {cv:.2f}")
            else:
                print(f"📊 불균등한 청크 처리: 변동계수 {cv:.2f}")

        # DB 저장 효율성
        if stats.db_records_added > 0 and stats.total_count > 0:
            save_ratio = stats.db_records_added / stats.total_count
            if save_ratio >= 0.95:
                print(f"💾 우수한 DB 저장: {save_ratio * 100:.1f}% 저장됨")
            elif save_ratio >= 0.8:
                print(f"💾 양호한 DB 저장: {save_ratio * 100:.1f}% 저장됨")
            else:
                print(f"💾 저조한 DB 저장: {save_ratio * 100:.1f}% 저장됨 (중복 또는 오류?)")

        # 청크별 시간 분포
        if len(stats.chunk_times_ms) > 3:
            print("\n📈 청크별 처리 시간 (처음 3개):")
            for i, chunk_time in enumerate(stats.chunk_times_ms[:3]):
                print(f"   청크 {i + 1}: {chunk_time:.1f}ms")


# 편의 함수들
async def test_count_collection(
    symbol: str = "KRW-BTC",
    timeframe: str = "1m",
    count: int = 100
) -> PerformanceStats:
    """개수 지정 수집 테스트 (편의 함수)"""
    async with CandleCollectionTesterV2() as tester:
        return await tester.test_collection_performance(
            symbol=symbol,
            timeframe=timeframe,
            count=count
        )


async def test_time_range_collection(
    symbol: str = "KRW-BTC",
    timeframe: str = "1m",
    to: Optional[datetime] = None,
    end: Optional[datetime] = None
) -> PerformanceStats:
    """시간 범위 수집 테스트 (편의 함수)"""
    async with CandleCollectionTesterV2() as tester:
        return await tester.test_collection_performance(
            symbol=symbol,
            timeframe=timeframe,
            to=to,
            end=end
        )


if __name__ == "__main__":
    # 예제 실행
    import asyncio

    async def example_test():
        print("🧪 CandleDataProvider v4.1 성능 테스터")

        # 100개 수집 테스트
        stats = await test_count_collection(count=100)

        # 결과 출력
        async with CandleCollectionTesterV2() as tester:
            tester.print_detailed_analysis(stats)

    asyncio.run(example_test())
