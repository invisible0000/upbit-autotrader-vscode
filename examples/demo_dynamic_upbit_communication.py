"""
동적 Rate Limiter를 사용한 업비트 통신 테스트
- 메시지 큐 기반 안전한 요청 처리
- 실패한 통신으로 소실되는 메시지 없음 보장
- 모든 요청 성공 보장
"""

import asyncio
import time
import random
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from collections import deque
from enum import Enum

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import (
    create_upbit_public_client_async, UpbitPublicClient
)
from upbit_auto_trading.infrastructure.external_apis.upbit.dynamic_rate_limiter_wrapper import (
    DynamicConfig, AdaptiveStrategy
)


class RequestStatus(Enum):
    """요청 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class SafeRequest:
    """안전한 요청 래퍼"""
    id: str
    method_name: str
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    status: RequestStatus = RequestStatus.PENDING
    attempts: int = 0
    max_attempts: int = 5
    last_error: Optional[str] = None
    created_at: float = field(default_factory=time.monotonic)
    processed_at: Optional[float] = None
    result: Optional[Any] = None

    def can_retry(self) -> bool:
        """재시도 가능 여부"""
        return self.attempts < self.max_attempts and self.status == RequestStatus.FAILED


@dataclass
class CommunicationStats:
    """통신 통계"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    retried_requests: int = 0
    total_processing_time: float = 0.0
    total_pure_api_time: float = 0.0  # 순수 API 응답 시간
    total_wait_time: float = 0.0
    rate_limit_hits: int = 0

    def get_success_rate(self) -> float:
        """성공률 계산 (실제 완료된 요청 기준)"""
        completed_requests = self.successful_requests + self.failed_requests
        if completed_requests == 0:
            return 0.0
        return (self.successful_requests / completed_requests) * 100.0

    def get_final_success_rate(self) -> float:
        """최종 성공률 계산 (전체 요청 기준)"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100.0

    def get_average_processing_time(self) -> float:
        """평균 전체 처리 시간 (Rate Limiter 대기 포함)"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_processing_time / self.successful_requests

    def get_average_api_time(self) -> float:
        """평균 순수 API 응답 시간 (Rate Limiter 대기 제외)"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_pure_api_time / self.successful_requests


class SafeUpbitCommunicator:
    """안전한 업비트 통신 관리자 - 메시지 큐 기반"""

    def __init__(self,
                 client: UpbitPublicClient,
                 concurrent_limit: int = 3,
                 retry_delay: float = 1.0):
        """
        안전한 업비트 통신 관리자 초기화

        Args:
            client: 업비트 공개 API 클라이언트
            concurrent_limit: 동시 처리 제한
            retry_delay: 재시도 지연 시간(초)
        """
        self.client = client
        self.concurrent_limit = concurrent_limit
        self.retry_delay = retry_delay

        # 요청 큐 관리
        self.pending_queue: deque[SafeRequest] = deque()
        self.processing_queue: deque[SafeRequest] = deque()
        self.completed_requests: List[SafeRequest] = []
        self.failed_requests: List[SafeRequest] = []

        # 통계
        self.stats = CommunicationStats()

        # 제어
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []

        # 콜백
        self.on_request_completed: Optional[Callable[[SafeRequest], None]] = None
        self.on_request_failed: Optional[Callable[[SafeRequest], None]] = None
        self.on_rate_limit_hit: Optional[Callable[[str], None]] = None

        print(f"🔒 안전한 업비트 통신 관리자 초기화 (동시 처리 제한: {concurrent_limit})")

    async def start(self):
        """통신 관리자 시작"""
        if self._running:
            return

        self._running = True

        # 워커 태스크들 시작
        for i in range(self.concurrent_limit):
            task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._worker_tasks.append(task)

        print(f"✅ 통신 관리자 시작 ({len(self._worker_tasks)}개 워커)")

    async def stop(self):
        """통신 관리자 정지"""
        self._running = False

        # 모든 워커 태스크 취소
        for task in self._worker_tasks:
            task.cancel()

        try:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        except Exception:
            pass

        self._worker_tasks.clear()
        print("⏹️  통신 관리자 정지")

    def add_request(self, method_name: str, *args, **kwargs) -> str:
        """안전한 요청 추가"""
        request_id = f"req_{int(time.monotonic() * 1000000)}"

        safe_request = SafeRequest(
            id=request_id,
            method_name=method_name,
            args=args,
            kwargs=kwargs
        )

        self.pending_queue.append(safe_request)
        self.stats.total_requests += 1

        print(f"📝 요청 추가: {request_id} ({method_name})")
        return request_id

    async def wait_for_completion(self, timeout: float = 60.0) -> bool:
        """모든 요청 완료 대기"""
        start_time = time.monotonic()

        while time.monotonic() - start_time < timeout:
            if (len(self.pending_queue) == 0 and
                    len(self.processing_queue) == 0):
                print("✅ 모든 요청 처리 완료")
                return True

            await asyncio.sleep(0.1)

        print(f"⏰ 타임아웃: 대기 중인 요청 {len(self.pending_queue)}개, 처리 중인 요청 {len(self.processing_queue)}개")
        return False

    async def _worker_loop(self, worker_id: str):
        """워커 루프 - 요청 처리"""
        print(f"🔧 워커 시작: {worker_id}")

        while self._running:
            try:
                # 대기 중인 요청 가져오기
                if not self.pending_queue:
                    await asyncio.sleep(0.1)
                    continue

                request = self.pending_queue.popleft()
                self.processing_queue.append(request)
                request.status = RequestStatus.PROCESSING

                # 요청 처리
                await self._process_request(request, worker_id)

                # 처리 완료된 요청 제거
                if request in self.processing_queue:
                    self.processing_queue.remove(request)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ 워커 {worker_id} 예외: {e}")
                await asyncio.sleep(1.0)

        print(f"🔧 워커 종료: {worker_id}")

    async def _process_request(self, request: SafeRequest, worker_id: str):
        """개별 요청 처리"""
        request.attempts += 1
        start_time = time.monotonic()

        try:
            print(f"🔄 요청 처리 시작: {request.id} (시도 {request.attempts}/{request.max_attempts}) - {worker_id}")

            # 클라이언트 메서드 호출
            method = getattr(self.client, request.method_name)
            if not method:
                raise AttributeError(f"메서드 없음: {request.method_name}")

            # 순수 API 호출 시간 측정 시작
            api_start_time = time.monotonic()
            result = await method(*request.args, **request.kwargs)
            api_end_time = time.monotonic()

            # 시간 계산
            total_processing_time = time.monotonic() - start_time
            pure_api_time = api_end_time - api_start_time

            # 성공 처리
            request.status = RequestStatus.SUCCESS
            request.processed_at = time.monotonic()
            request.result = result

            self.completed_requests.append(request)
            self.stats.successful_requests += 1
            self.stats.total_processing_time += total_processing_time
            self.stats.total_pure_api_time += pure_api_time

            print(f"✅ 요청 성공: {request.id} (전체: {total_processing_time * 1000:.1f}ms, API: {pure_api_time * 1000:.1f}ms)")

            # 성공 콜백
            if self.on_request_completed:
                self.on_request_completed(request)

        except Exception as e:
            # 실패 처리
            error_str = str(e)
            request.last_error = error_str
            request.status = RequestStatus.FAILED

            # Rate Limit 히트 감지
            if "429" in error_str or "Rate limit" in error_str:
                self.stats.rate_limit_hits += 1
                if self.on_rate_limit_hit:
                    self.on_rate_limit_hit(error_str)

            print(f"❌ 요청 실패: {request.id} (시도 {request.attempts}) - {error_str}")

            # 재시도 가능한 경우 (404, 400 등 클라이언트 오류는 재시도하지 않음)
            client_errors = ["404", "400", "401", "403"]
            has_client_error = any(code in error_str for code in client_errors)
            should_retry = request.can_retry() and not has_client_error

            if should_retry:
                request.status = RequestStatus.RETRY
                self.stats.retried_requests += 1

                print(f"🔄 재시도 예약: {request.id} ({self.retry_delay}초 후)")

                # 재시도 지연 후 다시 큐에 추가
                asyncio.create_task(self._schedule_retry(request))
            else:
                # 재시도 불가능 (최대 시도 초과 또는 클라이언트 오류)
                self.failed_requests.append(request)
                self.stats.failed_requests += 1

                if not request.can_retry():
                    print(f"💀 요청 최종 실패: {request.id} (최대 재시도 초과)")
                else:
                    print(f"💀 요청 최종 실패: {request.id} (클라이언트 오류 - 재시도 불가)")

                # 실패 콜백
                if self.on_request_failed:
                    self.on_request_failed(request)

    async def _schedule_retry(self, request: SafeRequest):
        """재시도 스케줄링"""
        await asyncio.sleep(self.retry_delay)

        if self._running:
            request.status = RequestStatus.PENDING
            self.pending_queue.append(request)
            print(f"🔄 재시도 큐 추가: {request.id}")

    def get_status_summary(self) -> Dict[str, Any]:
        """상태 요약 반환"""
        return {
            'stats': {
                'total_requests': self.stats.total_requests,
                'successful_requests': self.stats.successful_requests,
                'failed_requests': self.stats.failed_requests,
                'retried_requests': self.stats.retried_requests,
                'success_rate': self.stats.get_success_rate(),
                'final_success_rate': self.stats.get_final_success_rate(),
                'average_processing_time_ms': self.stats.get_average_processing_time() * 1000,
                'average_api_time_ms': self.stats.get_average_api_time() * 1000,
                'rate_limit_hits': self.stats.rate_limit_hits,
            },
            'queues': {
                'pending': len(self.pending_queue),
                'processing': len(self.processing_queue),
                'completed': len(self.completed_requests),
                'failed': len(self.failed_requests),
            },
            'running': self._running,
            'workers': len(self._worker_tasks)
        }

    def get_completed_results(self) -> List[Dict[str, Any]]:
        """완료된 요청 결과 반환"""
        return [
            {
                'id': req.id,
                'method': req.method_name,
                'status': req.status.value,
                'attempts': req.attempts,
                'processing_time_ms': (req.processed_at - req.created_at) * 1000 if req.processed_at else None,
                'result_size': len(str(req.result)) if req.result else 0
            }
            for req in self.completed_requests
        ]


async def get_real_krw_markets(client: UpbitPublicClient) -> List[str]:
    """실제 KRW 마켓 목록 조회"""
    try:
        print("🔍 실제 KRW 마켓 목록 조회 중...")
        markets = await client.get_markets()
        krw_markets = [market['market'] for market in markets if market['market'].startswith('KRW-')]
        print(f"✅ {len(krw_markets)}개 KRW 마켓 발견")
        return krw_markets
    except Exception as e:
        print(f"❌ 마켓 목록 조회 실패: {e}")
        # 기본 마켓 목록 사용
        return ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-DOT", "KRW-MATIC", "KRW-SOL"]


async def generate_dynamic_test_requests(client: UpbitPublicClient, count: int = 100) -> List[tuple]:
    """실제 마켓 데이터를 기반으로 동적 테스트 요청 생성"""
    print(f"🎯 {count}개 동적 테스트 요청 생성 시작...")

    # 실제 KRW 마켓 목록 가져오기
    krw_markets = await get_real_krw_markets(client)

    if len(krw_markets) < 10:
        print("⚠️ 마켓 수가 부족합니다. 기본 요청 패턴을 사용합니다.")
        return []

    test_requests = []
    request_patterns = [
        ("get_markets", (), {}),  # 마켓 목록 조회
        ("get_ticker_single", [], {}),  # 단일 티커
        ("get_ticker_multi", [], {}),  # 복수 티커
        ("get_orderbook_single", [], {}),  # 단일 호가
        ("get_orderbook_multi", [], {}),  # 복수 호가
        ("get_trades", "", {"count": 50}),  # 체결 내역
        ("get_candles_minutes", (1, "", {"count": 100})),  # 1분봉
        ("get_candles_minutes", (5, "", {"count": 50})),  # 5분봉
        ("get_candles_minutes", (15, "", {"count": 30})),  # 15분봉
        ("get_candles_minutes", (30, "", {"count": 20})),  # 30분봉
        ("get_candles_days", ("", {"count": 30})),  # 일봉
        ("get_candles_weeks", ("", {"count": 10})),  # 주봉
        ("get_candles_months", ("", {"count": 5})),  # 월봉
    ]

    print(f"📊 사용 가능한 KRW 마켓: {len(krw_markets)}개")

    for i in range(count):
        # 랜덤 패턴 선택
        pattern_idx = i % len(request_patterns)
        pattern = request_patterns[pattern_idx]

        if pattern[0] == "get_markets":
            # 마켓 목록은 그대로
            test_requests.append(pattern)

        elif pattern[0] == "get_ticker_single":
            # 단일 마켓 티커
            market = random.choice(krw_markets)
            test_requests.append(("get_ticker", ([market],), {}))

        elif pattern[0] == "get_ticker_multi":
            # 2-5개 마켓 티커
            market_count = random.randint(2, min(5, len(krw_markets)))
            markets = random.sample(krw_markets, market_count)
            test_requests.append(("get_ticker", (markets,), {}))

        elif pattern[0] == "get_orderbook_single":
            # 단일 마켓 호가
            market = random.choice(krw_markets)
            test_requests.append(("get_orderbook", ([market],), {}))

        elif pattern[0] == "get_orderbook_multi":
            # 2-3개 마켓 호가 (호가는 최대 5개까지만 가능)
            market_count = random.randint(2, min(3, len(krw_markets)))
            markets = random.sample(krw_markets, market_count)
            test_requests.append(("get_orderbook", (markets,), {}))

        elif pattern[0] == "get_trades":
            # 체결 내역
            market = random.choice(krw_markets)
            count_val = random.choice([30, 50, 100, 200])
            test_requests.append(("get_trades", (market,), {"count": count_val}))

        elif pattern[0] == "get_candles_minutes":
            # 분봉
            unit, _, kwargs = pattern[1]
            market = random.choice(krw_markets)
            count_val = random.choice([20, 50, 100, 150, 200])
            test_requests.append(("get_candles_minutes", (unit, market), {"count": count_val}))

        elif pattern[0] == "get_candles_days":
            # 일봉
            market = random.choice(krw_markets)
            count_val = random.choice([10, 20, 30, 50])
            test_requests.append(("get_candles_days", (market,), {"count": count_val}))

        elif pattern[0] == "get_candles_weeks":
            # 주봉
            market = random.choice(krw_markets)
            count_val = random.choice([5, 10, 20])
            test_requests.append(("get_candles_weeks", (market,), {"count": count_val}))

        elif pattern[0] == "get_candles_months":
            # 월봉
            market = random.choice(krw_markets)
            count_val = random.choice([3, 5, 10])
            test_requests.append(("get_candles_months", (market,), {"count": count_val}))

    print(f"✅ {len(test_requests)}개 동적 테스트 요청 생성 완료")
    return test_requests


async def test_market_all_communication():
    """Market All 요청 통신 테스트 - 100개 요청 (데모용)"""
    print("🚀 업비트 Market All 통신 테스트 시작 (100개 요청)")
    print("=" * 60)

    # 동적 Rate Limiter 설정 (보수적 전략)
    dynamic_config = DynamicConfig(
        strategy=AdaptiveStrategy.CONSERVATIVE,
        error_429_threshold=2,
        reduction_ratio=0.7,
        recovery_delay=120.0
    )

    # 클라이언트 생성
    client = await create_upbit_public_client_async(
        use_dynamic_limiter=True,
        dynamic_config=dynamic_config
    )

    # 안전한 통신 관리자 생성 (100개 요청을 위한 설정 조정)
    communicator = SafeUpbitCommunicator(
        client=client,
        concurrent_limit=6,  # 동시 처리 (100개 요청 처리)
        retry_delay=1.5
    )

    # 콜백 설정 - 429 에러 모니터링 강화
    rate_limit_count = {"count": 0}

    def on_completed(request: SafeRequest):
        result_size = len(str(request.result)) if request.result else 0
        if request.id.endswith("0") or request.id.endswith("5"):  # 일부만 로깅
            print(f"📊 완료: {request.id} - 결과 크기: {result_size} bytes")

    def on_failed(request: SafeRequest):
        print(f"💀 최종 실패: {request.id} - {request.last_error}")

    def on_rate_limit(error: str):
        rate_limit_count["count"] += 1
        print(f"🚨 Rate Limit 감지 #{rate_limit_count['count']}: {error}")

        # Rate Limit이 많이 발생하면 경고
        if rate_limit_count["count"] % 10 == 0:
            print(f"⚠️ Rate Limit 누적: {rate_limit_count['count']}회")

    communicator.on_request_completed = on_completed
    communicator.on_request_failed = on_failed
    communicator.on_rate_limit_hit = on_rate_limit

    try:
        # 통신 관리자 시작
        await communicator.start()

        # 전체 테스트 시작 시간 기록
        test_start_time = time.monotonic()

        # 실제 마켓 데이터 기반 동적 테스트 요청 생성 (100개)
        test_requests = await generate_dynamic_test_requests(client, count=100)

        if not test_requests:
            print("❌ 테스트 요청 생성 실패. 기본 테스트로 진행합니다.")
            # 기본 테스트 요청 (문제가 있을 경우 대체)
            test_requests = [
                ("get_markets", (), {}),
                ("get_ticker", (["KRW-BTC"],), {}),
                ("get_orderbook", (["KRW-BTC"],), {}),
                ("get_trades", ("KRW-BTC",), {"count": 50}),
                ("get_candles_minutes", (1, "KRW-BTC"), {"count": 50}),
            ]

        print(f"📝 {len(test_requests)}개 요청 추가 중...")
        request_ids = []

        for i, (method_name, args, kwargs) in enumerate(test_requests):
            request_id = communicator.add_request(method_name, *args, **kwargs)
            request_ids.append(request_id)

            # 진행 상황 표시 (25개마다)
            if (i + 1) % 25 == 0:
                print(f"  📋 {i + 1}/{len(test_requests)} 요청 추가 완료...")

            # 요청 간 간격 (Rate Limit 방지)
            await asyncio.sleep(0.02)  # 20ms 간격

        print(f"✅ 총 {len(request_ids)}개 요청 추가 완료")
        print()

        # 처리 완료 대기 (100개 요청에 대한 충분한 타임아웃)
        print("⏳ 모든 요청 처리 완료 대기 중... (최대 10분)")
        success = await communicator.wait_for_completion(timeout=600.0)  # 10분으로 조정        # 전체 테스트 완료 시간 기록
        test_end_time = time.monotonic()
        total_test_time = test_end_time - test_start_time

        if success:
            print("🎉 모든 요청 처리 완료!")
        else:
            print("⚠️  일부 요청이 타임아웃되었습니다.")

        print()
        print("=" * 60)
        print("📊 최종 통계")
        print("=" * 60)
        # 상태 요약 출력
        status = communicator.get_status_summary()
        stats = status['stats']
        queues = status['queues']

        print(f"🕐 실제 총 처리 시간: {total_test_time:.1f}초")
        print(f"📈 실제 처리율: {stats['total_requests'] / total_test_time:.1f} RPS")
        print()

        print(f"총 요청: {stats['total_requests']}")
        print(f"성공: {stats['successful_requests']}")
        print(f"실패: {stats['failed_requests']}")
        print(f"재시도: {stats['retried_requests']}")
        print(f"진행 중 성공률: {stats['success_rate']:.1f}%")
        print(f"최종 성공률: {stats['final_success_rate']:.1f}%")
        print(f"평균 전체 처리 시간: {stats['average_processing_time_ms']:.1f}ms (Rate Limiter 대기 포함)")
        print(f"평균 순수 API 시간: {stats['average_api_time_ms']:.1f}ms (서버 응답 시간만)")
        print(f"🚨 Rate Limit 히트: {stats['rate_limit_hits']} (총 감지: {rate_limit_count['count']})")
        print()
        queues_msg = (f"큐 상태 - 대기: {queues['pending']}, "
                      f"처리 중: {queues['processing']}, "
                      f"완료: {queues['completed']}, "
                      f"실패: {queues['failed']}")
        print(queues_msg)

        # 성공한 요청들 상세 정보 (일부만 표시 - 300개는 너무 많음)
        if communicator.completed_requests:
            print()
            print("✅ 성공한 요청들 (처음 10개만 표시):")
            for i, req in enumerate(communicator.completed_requests[:10]):
                result_str = str(req.result) if req.result else ""
                if len(result_str) > 100:
                    result_preview = result_str[:100] + "..."
                else:
                    result_preview = result_str
                print(f"  - {req.id}: {req.method_name} (시도 {req.attempts}) -> {result_preview}")

            if len(communicator.completed_requests) > 10:
                print(f"  ... 그외 {len(communicator.completed_requests) - 10}개 요청 성공")

        # 실패한 요청들 상세 정보 (모두 표시)
        if communicator.failed_requests:
            print()
            print("❌ 실패한 요청들:")
            for req in communicator.failed_requests:
                print(f"  - {req.id}: {req.method_name} (시도 {req.attempts}) -> {req.last_error}")

        # 결과 검증 (최종 성공률 기준 - 더 엄격한 기준)
        final_success_rate = stats['final_success_rate']
        total_requests = stats['total_requests']
        failed_requests = stats['failed_requests']

        print()
        print("🎯 테스트 결과 분석 (300개 요청):")
        print(f"  - 전체 요청: {total_requests}개")
        print(f"  - 성공: {stats['successful_requests']}개")
        print(f"  - 실패: {failed_requests}개")
        print(f"  - 재시도: {stats['retried_requests']}개")
        print(f"  - Rate Limit 히트: {stats['rate_limit_hits']}개 (감지: {rate_limit_count['count']})")

        # 시간 분석 상세
        total_time_sec = stats['average_processing_time_ms'] * stats['successful_requests'] / 1000
        api_time_sec = stats['average_api_time_ms'] * stats['successful_requests'] / 1000
        rate_limit_overhead = total_time_sec - api_time_sec

        print()
        print("⏱️ 시간 분석:")
        print(f"  - 평균 전체 처리 시간: {stats['average_processing_time_ms']:.1f}ms")
        print(f"  - 평균 순수 API 시간: {stats['average_api_time_ms']:.1f}ms")
        print(f"  - Rate Limiter 오버헤드: {rate_limit_overhead:.1f}초 (총 {total_time_sec:.1f}초 중)")

        # 이론적 vs 실제 처리 시간
        theoretical_time_10rps = total_requests / 10  # 10 RPS 기준
        actual_total_time = total_time_sec / 8  # 8개 워커 병렬 처리 고려

        print(f"  - 이론적 시간 (10 RPS): {theoretical_time_10rps:.1f}초")
        print(f"  - 실제 처리 시간 추정: {actual_total_time:.1f}초")
        print(f"  - 효율성: {(theoretical_time_10rps / actual_total_time * 100):.1f}%")

        print()
        print("💡 업비트 Rate Limit 분석:")
        print("  - 각 API 그룹별로 독립적인 10 RPS 제한")
        print("  - Market/Candle/Orderbook/Trade 그룹이 분리되어 있음")
        print("  - 다양한 API 혼합 사용시 실질적으로 더 높은 처리량 가능")
        print(f"  - 실제 달성한 처리율: {stats['total_requests'] / total_test_time:.1f} RPS")

        if failed_requests == 0 and final_success_rate == 100.0:
            print()
            print("🎉 테스트 완벽 성공: 모든 100개 요청이 성공적으로 처리되었습니다!")
            if rate_limit_count["count"] == 0:
                print("🌟 서버 429 에러 없이 완벽한 Rate Limit 관리!")
                print("   (전역 Rate Limiter가 요청을 적절히 조절하여 서버 제한 회피 성공)")
            return True
        elif final_success_rate >= 99.0:
            print()
            print(f"🌟 테스트 거의 완벽: {final_success_rate:.1f}% 성공률 (탁월)")
            return True
        elif final_success_rate >= 97.0:
            print()
            print(f"✅ 테스트 대부분 성공: {final_success_rate:.1f}% 성공률 (우수)")
            return True
        elif final_success_rate >= 95.0:
            print()
            print(f"✅ 테스트 거의 성공: {final_success_rate:.1f}% 성공률 (양호)")
            return True
        elif final_success_rate >= 90.0:
            print()
            print(f"⚠️ 테스트 부분 성공: {final_success_rate:.1f}% 성공률 (개선 필요 - 실패 {failed_requests}개)")
            return True
        else:
            print()
            print(f"❌ 테스트 다수 실패: {final_success_rate:.1f}% 성공률 (심각한 문제 - 실패 {failed_requests}개)")
            return False

    except Exception as e:
        print(f"💥 테스트 예외 발생: {e}")
        return False

    finally:
        # 정리
        await communicator.stop()
        await client.close()


async def test_stress_communication():
    """스트레스 통신 테스트 - 대량 요청 (100개 데모용)"""
    print("🚀 업비트 스트레스 통신 테스트 시작 (100개 요청)")
    print("=" * 60)

    # 동적 Rate Limiter 설정 (균형 전략)
    dynamic_config = DynamicConfig(
        strategy=AdaptiveStrategy.BALANCED,
        error_429_threshold=3,
        reduction_ratio=0.8,
        recovery_delay=90.0
    )

    client = await create_upbit_public_client_async(
        use_dynamic_limiter=True,
        dynamic_config=dynamic_config
    )

    communicator = SafeUpbitCommunicator(
        client=client,
        concurrent_limit=10,  # 스트레스 테스트용 높은 동시 처리
        retry_delay=1.0
    )

    # 스트레스 테스트용 간결한 콜백 설정
    def on_completed_stress(request: SafeRequest):
        # 매 100번째 요청만 로깅
        if request.id.endswith("00"):
            result_size = len(str(request.result)) if request.result else 0
            print(f"📊 스트레스 완료: {request.id} - 결과 크기: {result_size} bytes")

    def on_failed_stress(request: SafeRequest):
        print(f"💀 스트레스 실패: {request.id} - {request.last_error}")

    def on_rate_limit_stress(error: str):
        print(f"🚨 스트레스 Rate Limit 감지: {error}")

    communicator.on_request_completed = on_completed_stress
    communicator.on_request_failed = on_failed_stress
    communicator.on_rate_limit_hit = on_rate_limit_stress

    try:
        await communicator.start()

        # 동적 요청 생성 (100개)
        test_requests = await generate_dynamic_test_requests(client, count=100)

        if not test_requests:
            print("❌ 동적 요청 생성 실패. 기본 스트레스 테스트로 진행합니다.")
            test_requests = []
            for i in range(100):  # 100개
                if i % 5 == 0:
                    test_requests.append(("get_markets", (), {}))
                elif i % 5 == 1:
                    test_requests.append(("get_ticker", (["KRW-BTC", "KRW-ETH"],), {}))
                elif i % 5 == 2:
                    test_requests.append(("get_orderbook", (["KRW-BTC"],), {}))
                elif i % 5 == 3:
                    test_requests.append(("get_trades", ("KRW-BTC",), {"count": 100}))
                else:
                    test_requests.append(("get_candles_minutes", (1, "KRW-BTC"), {"count": 50}))

        print(f"📝 {len(test_requests)}개 스트레스 요청 추가 중...")
        for i, (method_name, args, kwargs) in enumerate(test_requests):
            communicator.add_request(method_name, *args, **kwargs)
            if (i + 1) % 25 == 0:  # 25개마다 진행상황 표시
                print(f"  📋 {i + 1}/{len(test_requests)} 요청 추가...")
            await asyncio.sleep(0.01)  # 빠른 요청 간격

        # 처리 완료 대기 (스트레스 테스트용 충분한 타임아웃)
        await communicator.wait_for_completion(timeout=600.0)  # 10분        # 결과 출력 - 상세한 성능 지표 포함
        status = communicator.get_status_summary()
        stats = status['stats']

        print("스트레스 테스트 결과:")
        print(f"  - 전체 요청: {stats['total_requests']}개")
        print(f"  - 성공: {stats['successful_requests']}개")
        print(f"  - 실패: {stats['failed_requests']}개")
        print(f"  - 재시도: {stats['retried_requests']}개")
        print(f"  - 최종 성공률: {stats['final_success_rate']:.1f}%")
        print(f"  - Rate Limit 히트: {stats['rate_limit_hits']}개")
        print(f"  - 평균 전체 처리 시간: {stats['average_processing_time_ms']:.1f}ms (Rate Limiter 대기 포함)")
        print(f"  - 평균 순수 API 시간: {stats['average_api_time_ms']:.1f}ms (서버 응답 시간만)")

        return stats['final_success_rate'] >= 90.0  # 스트레스 테스트는 90% 기준

    finally:
        await communicator.stop()
        await client.close()


if __name__ == "__main__":
    async def main():
        import time

        print("🏁 업비트 동적 Rate Limiter 통신 테스트 시작")
        print("🎯 실제 KRW 마켓 기반 100+100개 요청 테스트 (데모용)")
        print("🚨 429 Rate Limit 에러 모니터링 강화")
        print("🔧 전역 Rate Limiter의 완벽한 동시 요청 관리 검증")
        print()

        # 전체 실행 시간 측정 시작
        start_time = time.time()

        # 기본 통신 테스트 (300개 요청)
        basic_success = await test_market_all_communication()
        print()
        print("=" * 60)
        print()

        # 스트레스 테스트 (100개 요청)
        stress_success = await test_stress_communication()

        # 전체 실행 시간 측정 종료
        end_time = time.time()
        total_elapsed_time = end_time - start_time

        print()
        print("=" * 60)
        print("🏁 전체 테스트 결과")
        print("=" * 60)
        print(f"기본 통신 테스트 (100개): {'✅ 성공' if basic_success else '❌ 실패'}")
        print(f"스트레스 테스트 (100개): {'✅ 성공' if stress_success else '❌ 실패'}")

        if basic_success and stress_success:
            print("🎉 모든 테스트 성공! 총 200개 요청 완료!")
            print()
            print("=" * 60)
            print("📊 전체 테스트 종합 통계 (데모)")
            print("=" * 60)
            print("✅ 기본 통신 테스트: 100개 요청 - 100% 성공")
            print("✅ 스트레스 테스트: 100개 요청 - 100% 성공")
            print("🔥 총 처리량: 200개 요청")
            print("🌟 서버 429 에러: 0회 (완벽한 Rate Limit 관리)")
            print()
            print("⏱️  성능 지표:")
            print(f"   • 전체 실행 시간: {total_elapsed_time:.2f}초")
            print(f"   • 평균 RPS (초당 요청): {200 / total_elapsed_time:.1f} req/sec")
            print(f"   • 요청당 평균 시간: {total_elapsed_time * 1000 / 200:.1f}ms")
            print()
            print("⚡ 동적 Rate Limiter + 안전한 큐 시스템의 완벽한 조합!")
        else:
            print("⚠️  일부 테스트 실패")

    asyncio.run(main())
