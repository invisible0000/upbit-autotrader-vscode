#!/usr/bin/env python3
"""
업비트 자산 조회 50번 테스트 - 429 에러 2회 발생 시 정지

🎯 목적:
- 업비트 계좌 자산 정보를 50번 수집
- 429 (Too Many Requests) 에러가 2번 발생하면 테스트 정지
- Private Client의 통합 Rate Limiter 실제 동작 검증

📋 테스트 조건:
- 대상: 계좌 자산 조회 API (/v1/accounts)
- 목표: 50번 성공적 수집
- 중단 조건: 429 에러 2회 발생
- Rate Limit 그룹:                total_currencies = len(accounts)
                active_currencies = len([
                    c for c, info in accounts.items()
                    if (float(info.get('balance', '0')) > 0 or
                        float(info.get('locked', '0')) > 0)
                ])ST_PRIVATE_DEFAULT (30 RPS)
- DRY-RUN: 기본 활성화 (실제 API 키 없어도 테스트 가능)
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

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_private_client import UpbitPrivateClient
from upbit_auto_trading.infrastructure.external_apis.upbit.rate_limiter.upbit_rate_limiter import (
    get_unified_rate_limiter
)
from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class AccountTestResult:
    """자산 조회 테스트 결과"""
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
    account_data: Optional[Dict[str, Any]] = None
    is_dry_run: bool = False


class AccountsTest50:
    """업비트 자산 조회 50번 테스트"""

    def __init__(self, dry_run: bool = True):
        self.logger = create_component_logger("AccountsTest50")
        self.client: Optional[UpbitPrivateClient] = None
        self.results: list[AccountTestResult] = []
        self.error_429_count = 0
        self.max_429_errors = 2
        self.target_requests = 50
        self.success_count = 0
        self.dry_run = dry_run

    async def __aenter__(self):
        # DRY-RUN 모드로 클라이언트 생성 - ApiKeyService에서 실제 키 로드
        self.client = UpbitPrivateClient(
            # access_key와 secret_key를 None으로 설정하여 ApiKeyService 사용
            access_key=None,
            secret_key=None,
            dry_run=self.dry_run
        )
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def make_single_request(self, request_num: int, prev_end_wall: Optional[float]) -> AccountTestResult:
        """단일 자산 조회 요청 실행"""
        start_time = time.time()
        timestamp = datetime.now()

        # 요청 전 429 카운트 확인
        rate_limiter = await get_unified_rate_limiter()
        current_stats = rate_limiter.get_comprehensive_status()
        private_default_stats = current_stats.get('groups', {}).get('rest_private_default', {})
        current_429_count = private_default_stats.get('error_429_count', 0)

        try:
            # 계좌 자산 조회 (DRY-RUN에서는 시뮬레이션 데이터 반환)
            account_data = await self.client.get_accounts()
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000

            # 클라이언트 메타데이터 수집
            meta = self.client.get_last_request_meta() if self.client else None
            total_cycle_ms = meta.get('total_cycle_ms') if meta else None
            acquire_wait_ms = meta.get('acquire_wait_ms') if meta else None
            http_latency_ms = meta.get('http_latency_ms') if meta else None
            had_429 = meta.get('had_429') if meta else False

            # 요청 후 429 카운트 확인
            after_stats = rate_limiter.get_comprehensive_status()
            after_private_stats = after_stats.get('groups', {}).get('rest_private_default', {})
            after_429_count = after_private_stats.get('error_429_count', 0)

            # 429 에러 발생 체크
            if after_429_count > current_429_count:
                self.error_429_count += (after_429_count - current_429_count)
                self.logger.error(
                    f"🚨 요청 {request_num:2d}/50 - 429 에러 감지됨 "
                    f"(Rate Limiter 통계 기반, 누적: {self.error_429_count}/{self.max_429_errors}회)"
                )

                if self.error_429_count >= self.max_429_errors:
                    self.logger.critical(f"💀 429 에러 {self.max_429_errors}회 도달! 테스트 중단")

            if account_data:
                result = AccountTestResult(
                    request_number=request_num,
                    success=True,
                    status_code=200,
                    response_time_ms=response_time_ms,
                    total_cycle_ms=total_cycle_ms,
                    acquire_wait_ms=acquire_wait_ms,
                    http_latency_ms=http_latency_ms,
                    had_429=had_429,
                    timestamp=timestamp,
                    account_data=account_data,
                    is_dry_run=self.dry_run
                )

                self.success_count += 1

                # 성공 로그 (DRY-RUN 여부 표시)
                mode_indicator = "[DRY-RUN]" if self.dry_run else "[LIVE]"
                currencies_count = len(account_data) if isinstance(account_data, dict) else "N/A"
                self.logger.info(
                    f"✅ 요청 {request_num:2d}/50 성공 {mode_indicator} - "
                    f"자산 종류: {currencies_count}개 ({response_time_ms:.1f}ms)"
                )

                return result

        except Exception as e:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000

            # 429 에러 체크
            error_str = str(e).lower()
            is_429_error = '429' in error_str or 'too many requests' in error_str or 'rate limit' in error_str

            if is_429_error:
                self.error_429_count += 1
                self.logger.error(f"🚨 요청 {request_num:2d}/50 - 429 에러 발생 (누적: {self.error_429_count}/{self.max_429_errors}회)")

                if self.error_429_count >= self.max_429_errors:
                    self.logger.critical(f"💀 429 에러 {self.max_429_errors}회 도달! 테스트 중단")
            else:
                mode_indicator = "[DRY-RUN]" if self.dry_run else "[LIVE]"
                self.logger.error(f"❌ 요청 {request_num:2d}/50 실패 {mode_indicator} - {e} ({response_time_ms:.1f}ms)")

            return AccountTestResult(
                request_number=request_num,
                success=False,
                response_time_ms=response_time_ms,
                timestamp=timestamp,
                error_message=str(e),
                is_dry_run=self.dry_run
            )

    async def run_test(self):
        """메인 테스트 실행"""
        mode_name = "DRY-RUN" if self.dry_run else "LIVE"
        self.logger.info(f"🚀 업비트 자산 조회 50번 테스트 시작 [{mode_name} 모드]")
        self.logger.info(f"📋 목표: 50번 성공적 수집, 중단 조건: 429 에러 {self.max_429_errors}회")
        self.logger.info("🎯 Rate Limit 그룹: REST_PRIVATE_DEFAULT (30 RPS)")

        start_time = datetime.now()

        # 50번 요청 (또는 429 에러 2회 발생까지)
        prev_end_wall: Optional[float] = None
        inter_request_intervals: list[float] = []

        for request_num in range(1, self.target_requests + 1):
            # 429 에러 체크
            if self.error_429_count >= self.max_429_errors:
                self.logger.warning("🛑 429 에러 한계 도달로 테스트 중단")
                break

            # 요청 실행
            result = await self.make_single_request(request_num, prev_end_wall)

            # 인터리퀘스트 간격 계산
            end_wall = time.perf_counter()
            if prev_end_wall is not None:
                inter_request_intervals.append((end_wall - prev_end_wall) * 1000.0)
            prev_end_wall = end_wall
            self.results.append(result)

            # 진행률 표시 (10의 배수마다)
            if request_num % 10 == 0:
                success_rate = (self.success_count / len(self.results)) * 100
                self.logger.info(f"📊 진행률: {request_num}/50 (성공률: {success_rate:.1f}%)")

            # 요청 간 간격 (REST_PRIVATE_DEFAULT 30 RPS에 맞춤)
            await asyncio.sleep(0.04)  # 40ms 간격 (약 25 RPS, 30 RPS 제한에 여유)

        end_time = datetime.now()
        duration = end_time - start_time

        # 최종 결과 분석
        self.analyze_results(duration, inter_request_intervals)

    def analyze_results(self, duration, inter_request_intervals: list[float]):
        """결과 분석 및 출력"""
        total_requests = len(self.results)
        successful_requests = len([r for r in self.results if r.success])
        failed_requests = total_requests - successful_requests

        mode_name = "DRY-RUN" if self.dry_run else "LIVE"

        self.logger.info("=" * 80)
        self.logger.info(f"📊 업비트 자산 조회 50번 테스트 결과 [{mode_name} 모드]")
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

        # 순수 HTTP 응답 시간 통계
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

        # 최근 성공한 자산 정보 (DRY-RUN과 실제 구분)
        latest_success = None
        for result in reversed(self.results):
            if result.success and result.account_data:
                latest_success = result
                break

        if latest_success and latest_success.account_data:
            accounts = latest_success.account_data
            self.logger.info("=" * 40)
            if self.dry_run:
                self.logger.info("🏃‍♂️ 최신 자산 정보 (DRY-RUN 시뮬레이션)")
            else:
                self.logger.info("💰 최신 자산 정보 (실제 계좌)")
            self.logger.info("=" * 40)

            if isinstance(accounts, dict):
                for currency, account_info in accounts.items():
                    balance = account_info.get('balance', '0')
                    locked = account_info.get('locked', '0')
                    avg_price = account_info.get('avg_buy_price', '0')

                    if float(balance) > 0 or float(locked) > 0:
                        self.logger.info(f"{currency}: 잔액 {balance}, 사용중 {locked}, 평단가 {avg_price}")

                total_currencies = len(accounts)
                active_currencies = sum(
                    1 for c, info in accounts.items()
                    if (float(info.get('balance', '0')) > 0
                        or float(info.get('locked', '0')) > 0)
                )
                self.logger.info(f"총 {total_currencies}개 통화, 활성 {active_currencies}개")
            else:
                self.logger.info(f"자산 데이터 타입: {type(accounts)}")

        # Rate Limiter 그룹 상태 확인
        self.logger.info("=" * 40)
        self.logger.info("🔧 Rate Limiter 상태")
        self.logger.info("=" * 40)

        # Rate Limiter 상태는 클라이언트를 통해 간접적으로 조회
        try:
            if self.client and hasattr(self.client, '_rate_limiter') and self.client._rate_limiter:
                status = self.client._rate_limiter.get_comprehensive_status()
                private_group = status.get('groups', {}).get('rest_private_default', {})

                if private_group:
                    config = private_group.get('config', {})
                    stats = private_group.get('stats', {})

                    self.logger.info("그룹: REST_PRIVATE_DEFAULT")
                    self.logger.info(f"기본 RPS: {config.get('rps', 'N/A')}")
                    self.logger.info(f"현재 비율: {config.get('current_ratio', 'N/A'):.3f}")
                    self.logger.info(f"총 요청: {stats.get('total_requests', 'N/A')}")
                    self.logger.info(f"429 에러: {stats.get('error_429_count', 'N/A')}")
            else:
                self.logger.info("Rate Limiter 상태 정보 없음")
        except Exception as e:
            self.logger.warning(f"Rate Limiter 상태 조회 실패: {e}")

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
        elif successful_requests >= 50:
            self.logger.info("🎉 테스트 성공: 50번 자산 조회 완료!")
        elif successful_requests >= 40:
            self.logger.info(f"✅ 테스트 양호: {successful_requests}번 자산 조회 완료")
        else:
            self.logger.warning(f"⚠️ 테스트 미흡: {successful_requests}번만 자산 조회 완료")


async def main():
    """메인 함수"""
    print("🧪 업비트 자산 조회 50번 테스트 (429 에러 2회 시 중단)")
    print("📝 Private Client 통합 Rate Limiter 검증")
    print("=" * 80)

    # DRY-RUN 모드로 실행 (기본값)
    # 실제 API 키가 있다면 dry_run=False로 변경 가능
    dry_run_mode = True

    async with AccountsTest50(dry_run=dry_run_mode) as tester:
        await tester.run_test()

    print("\n" + "=" * 80)
    print("✅ 테스트 완료")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
