#!/usr/bin/env python3
"""
KRW-BTC Ticker 100번 수집 테스트 - 429 에러 2회 발생 시 정지

🎯 목적:
- KRW-BTC 마켓의 현재가 정보를 100번 수집
- 429 (Too Many Requests) 에러가 2번 발생하면 테스트 정지
- Rate Limiter의 실제 동작 검증

📋 테스트 조건:
- 대상: KRW-BTC 현재가 API (/v1/ticker)
- 목표: 100번 성공적 수집
- 중단 조건: 429 에러 2회 발생
- 로깅: 요청/응답 상세 기록
"""

import asyncio
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

# 프로젝트 루트를 Python Path에 추가 (최상단에 배치해 import 검사 경고 방지)
PROJECT_ROOT = os.getcwd()
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
from upbit_auto_trading.infrastructure.external_apis.upbit.rate_limiter.upbit_rate_limiter import (
    get_unified_rate_limiter
)
from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class TestResult:
    """테스트 결과"""
    request_number: int
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    total_cycle_ms: Optional[float] = None  # acquire 대기 + HTTP + 재시도 포함 총 사이클
    acquire_wait_ms: Optional[float] = None
    http_latency_ms: Optional[float] = None
    had_429: Optional[bool] = None
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None
    ticker_data: Optional[Dict[str, Any]] = None


class KRWBTCTicker100Test:
    """KRW-BTC Ticker 100번 수집 테스트"""

    def __init__(self):
        self.logger = create_component_logger("KRWBTCTest")
        self.client: Optional[UpbitPublicClient] = None
        self.results: list[TestResult] = []
        self.error_429_count = 0
        self.max_429_errors = 2
        self.target_requests = 100
        self.success_count = 0
        self.last_429_count = 0  # Rate Limiter의 이전 429 카운트

    async def __aenter__(self):
        self.client = UpbitPublicClient()
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def make_single_request(self, request_num: int, prev_end_wall: Optional[float]) -> TestResult:
        """단일 요청 실행"""
    # wall_start (전체 사이클) 는 현재 메타에서 total_cycle_ms 제공되므로 별도 사용 안 함
        start_time = time.time()
        timestamp = datetime.now()

        # 요청 전 429 카운트 확인
        rate_limiter = await get_unified_rate_limiter()
        current_stats = rate_limiter.get_comprehensive_status()
        rest_public_stats = current_stats.get('groups', {}).get('rest_public', {})
        current_429_count = rest_public_stats.get('error_429_count', 0)

        try:
            # KRW-BTC 현재가 조회
            ticker_data = await self.client.get_tickers(['KRW-BTC'])
            # end_wall 사용 대신 run_test 루프에서 wall clock 기반 간격 계산
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000  # 기존 (순수 HTTP 기반 기존 측정)

            # 클라이언트 메타데이터 (전체 사이클/대기 등)
            meta = self.client.get_last_request_meta() if self.client else None
            total_cycle_ms = meta.get('total_cycle_ms') if meta else None
            acquire_wait_ms = meta.get('acquire_wait_ms') if meta else None
            http_latency_ms = meta.get('http_latency_ms') if meta else None
            had_429 = meta.get('had_429') if meta else False

            # 요청 후 429 카운트 확인
            after_stats = rate_limiter.get_comprehensive_status()
            after_rest_public_stats = after_stats.get('groups', {}).get('rest_public', {})
            after_429_count = after_rest_public_stats.get('error_429_count', 0)

            # 429 에러 발생 체크
            if after_429_count > current_429_count:
                self.error_429_count += (after_429_count - current_429_count)
                self.logger.error(
                    f"🚨 요청 {request_num:3d}/100 - 429 에러 감지됨 "
                    f"(Rate Limiter 통계 기반, 누적: {self.error_429_count}/{self.max_429_errors}회)"
                )

                if self.error_429_count >= self.max_429_errors:
                    self.logger.critical(f"💀 429 에러 {self.max_429_errors}회 도달! 테스트 중단")

            if ticker_data and len(ticker_data) > 0:
                result = TestResult(
                    request_number=request_num,
                    success=True,
                    status_code=200,
                    response_time_ms=response_time_ms,
                    total_cycle_ms=total_cycle_ms,
                    acquire_wait_ms=acquire_wait_ms,
                    http_latency_ms=http_latency_ms,
                    had_429=had_429,
                    timestamp=timestamp,
                    ticker_data=ticker_data[0]
                )

                self.success_count += 1

                # 간단한 성공 로그
                price = ticker_data[0].get('trade_price', 'N/A')
                self.logger.info(f"✅ 요청 {request_num:3d}/100 성공 - 현재가: {price:,}원 ({response_time_ms:.1f}ms)")

                return result

        except Exception as e:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000

            # 429 에러 체크
            error_str = str(e).lower()
            is_429_error = '429' in error_str or 'too many requests' in error_str or 'rate limit' in error_str

            if is_429_error:
                self.error_429_count += 1
                self.logger.error(f"🚨 요청 {request_num:3d}/100 - 429 에러 발생 (누적: {self.error_429_count}/{self.max_429_errors}회)")

                if self.error_429_count >= self.max_429_errors:
                    self.logger.critical(f"💀 429 에러 {self.max_429_errors}회 도달! 테스트 중단")
            else:
                self.logger.error(f"❌ 요청 {request_num:3d}/100 실패 - {e} ({response_time_ms:.1f}ms)")

            return TestResult(
                request_number=request_num,
                success=False,
                response_time_ms=response_time_ms,
                timestamp=timestamp,
                error_message=str(e)
            )

    async def run_test(self):
        """메인 테스트 실행"""
        self.logger.info("🚀 KRW-BTC Ticker 100번 수집 테스트 시작")
        self.logger.info(f"📋 목표: 100번 성공적 수집, 중단 조건: 429 에러 {self.max_429_errors}회")

        start_time = datetime.now()

        # 100번 요청 (또는 429 에러 2회 발생까지)
        prev_end_wall: Optional[float] = None
        inter_request_intervals: list[float] = []
        for request_num in range(1, self.target_requests + 1):
            # 429 에러 체크
            if self.error_429_count >= self.max_429_errors:
                self.logger.warning("🛑 429 에러 한계 도달로 테스트 중단")
                break

            # 요청 실행
            result = await self.make_single_request(request_num, prev_end_wall)
            # 인터리퀘스트 간격 계산 (직전 성공/실패 종료벽 시각과 비교)
            # 클라이언트 메타는 여기서 직접 사용하지 않음 (수집만 되어 있음)
            # wall clock 기반 종료 시각 저장
            end_wall = time.perf_counter()
            if prev_end_wall is not None:
                inter_request_intervals.append((end_wall - prev_end_wall) * 1000.0)
            prev_end_wall = end_wall
            self.results.append(result)

            # 진행률 표시 (10의 배수마다)
            if request_num % 10 == 0:
                success_rate = (self.success_count / len(self.results)) * 100
                self.logger.info(f"📊 진행률: {request_num}/100 (성공률: {success_rate:.1f}%)")

            # 요청 간 간격 (Rate Limiter에 맞춤)
            await asyncio.sleep(0.05)  # 50ms 간격 (약 20 RPS, 7 RPS 제한에 여유)

        end_time = datetime.now()
        duration = end_time - start_time

        # 최종 결과 분석
        self.analyze_results(duration, inter_request_intervals)

    def analyze_results(self, duration, inter_request_intervals: list[float]):
        """결과 분석 및 출력"""
        total_requests = len(self.results)
        successful_requests = len([r for r in self.results if r.success])
        failed_requests = total_requests - successful_requests

        self.logger.info("=" * 80)
        self.logger.info("📊 KRW-BTC Ticker 100번 수집 테스트 결과")
        self.logger.info("=" * 80)

        # 기본 통계
        self.logger.info(f"⏱️  총 소요 시간: {duration}")
        self.logger.info(f"📈 총 요청 수: {total_requests}")
        self.logger.info(f"✅ 성공 요청: {successful_requests}")
        self.logger.info(f"❌ 실패 요청: {failed_requests}")
        self.logger.info(f"🚨 429 에러 횟수: {self.error_429_count}")

        if total_requests > 0:
            success_rate = (successful_requests / total_requests) * 100
            self.logger.info(f"📊 성공률: {success_rate:.2f}%")

        # 순수 HTTP 응답 시간 통계 (기존)
        successful_results = [r for r in self.results if r.success and r.response_time_ms is not None]
        if successful_results:
            http_times = [
                r.http_latency_ms if r.http_latency_ms is not None else r.response_time_ms
                for r in successful_results
            ]
            avg_http = sum(http_times) / len(http_times)
            self.logger.info(f"⚡ 평균 HTTP 레이턴시: {avg_http:.1f}ms")

        # 전체 사이클 시간 통계 (Rate Limiter 대기 포함)
        cycle_times = [r.total_cycle_ms for r in self.results if r.total_cycle_ms is not None]
        if cycle_times:
            avg_cycle = sum(cycle_times) / len(cycle_times)
            self.logger.info(f"🕒 평균 전체 사이클 (acquire+HTTP): {avg_cycle:.1f}ms")
            self.logger.info(f"🕒 최단 전체 사이클: {min(cycle_times):.1f}ms / 최장: {max(cycle_times):.1f}ms")

        # Acquire 대기 시간 통계
        acquire_waits = [r.acquire_wait_ms for r in self.results if r.acquire_wait_ms is not None]
        if acquire_waits:
            avg_acquire = sum(acquire_waits) / len(acquire_waits)
            self.logger.info(f"⏳ 평균 RateLimiter 대기시간: {avg_acquire:.1f}ms (max {max(acquire_waits):.1f}ms)")

        # 인터리퀘스트 간격
        if inter_request_intervals:
            avg_interval = sum(inter_request_intervals) / len(inter_request_intervals)
            self.logger.info(f"🔁 평균 인터리퀘스트 간격 (wall): {avg_interval:.1f}ms (n={len(inter_request_intervals)})")

        # 429 경험 여부 (메타 기반)
        had_429_any = any(r.had_429 for r in self.results if r.had_429 is not None)
        self.logger.info(f"🚫 메타 기반 429 경험 여부: {'YES' if had_429_any else 'NO'}")

        # 최근 성공한 현재가 정보
        latest_success = None
        for result in reversed(self.results):
            if result.success and result.ticker_data:
                latest_success = result
                break

        if latest_success and latest_success.ticker_data:
            ticker = latest_success.ticker_data
            self.logger.info("=" * 40)
            self.logger.info("💰 최신 KRW-BTC 현재가 정보")
            self.logger.info("=" * 40)
            self.logger.info(f"현재가: {ticker.get('trade_price', 'N/A'):,}원")
            self.logger.info(f"전일 대비: {ticker.get('signed_change_price', 'N/A'):,}원")
            self.logger.info(f"전일 대비율: {ticker.get('signed_change_rate', 'N/A'):.2%}")
            self.logger.info(f"거래량: {ticker.get('acc_trade_volume_24h', 'N/A'):,.4f} BTC")
            self.logger.info(f"거래대금: {ticker.get('acc_trade_price_24h', 'N/A'):,}원")

        # 에러 요약
        if failed_requests > 0:
            self.logger.info("=" * 40)
            self.logger.info("❌ 에러 요약")
            self.logger.info("=" * 40)

            error_summary = {}
            for result in self.results:
                if not result.success and result.error_message:
                    error_msg = result.error_message
                    if error_msg not in error_summary:
                        error_summary[error_msg] = 0
                    error_summary[error_msg] += 1

            for error_msg, count in error_summary.items():
                self.logger.info(f"  • {error_msg}: {count}회")

        # 최종 판정
        self.logger.info("=" * 80)
        if self.error_429_count >= self.max_429_errors:
            self.logger.error(f"💀 테스트 중단: 429 에러 {self.max_429_errors}회 도달")
        elif successful_requests >= 100:
            self.logger.info("🎉 테스트 성공: 100번 수집 완료!")
        elif successful_requests >= 80:
            self.logger.info(f"✅ 테스트 양호: {successful_requests}번 수집 완료")
        else:
            self.logger.warning(f"⚠️ 테스트 미흡: {successful_requests}번만 수집 완료")


async def main():
    """메인 함수"""
    print("🧪 KRW-BTC Ticker 100번 수집 테스트 (429 에러 2회 시 중단)")
    print("=" * 80)

    async with KRWBTCTicker100Test() as tester:
        await tester.run_test()

    print("\n" + "=" * 80)
    print("✅ 테스트 완료")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
