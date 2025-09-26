"""
업비트 프라이빗 API 클라이언트 - 동적 GCRA Rate Limiter + DRY-RUN 지원

DDD Infrastructure 계층 컴포넌트
- 업비트 전용 최적화 구현
- 동적 조정 GCRA Rate Limiter 통합
- DRY-RUN 모드 기본 지원
- 429 오류 자동 처리 및 재시도
- Infrastructure 로깅 시스템 준수

## 지원 엔드포인트 매핑

### 계정 정보
- get_accounts()           → GET /accounts
- get_orders_chance()      → GET /orders/chance

### 주문 관리
- place_order()            → POST /orders
- get_order()              → GET /order
- get_orders()             → GET /orders
- get_open_orders()        → GET /orders/open
- get_closed_orders()      → GET /orders/closed

### 주문 취소
- cancel_order()           → DELETE /order
- cancel_orders_by_ids()   → DELETE /orders/uuids
- batch_cancel_orders()    → DELETE /orders/open

### 거래 내역
- get_trades_history()     → GET /orders/closed (체결된 주문 조회)

### Rate Limit 그룹
- 계정 조회: REST_PRIVATE_DEFAULT 그룹 (초당 30회)
- 주문 생성/취소: REST_PRIVATE_ORDER 그룹 (초당 8회)
- 전체 주문 취소: REST_PRIVATE_CANCEL_ALL 그룹 (초당 0.5회)

### 특이사항
- 모든 메서드는 API 키 인증 필수
- DRY-RUN 모드 기본 활성화 (실거래 시 dry_run=False 명시 필요)
- 주문 관련 메서드는 is_order_request=True로 별도 Rate Limit 적용
- GCRA 기반 동적 조정으로 429 오류 최소화
"""
import asyncio
import aiohttp
import time
import random
from typing import List, Dict, Any, Optional, Literal
from decimal import Decimal

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.runtime import (
    LoopGuard,
    get_loop_guard
)
from .upbit_auth import UpbitAuthenticator
from .rate_limiter import (
    UnifiedUpbitRateLimiter,
    get_unified_rate_limiter,
    log_429_error,
    log_request_success,
    UpbitRateLimitGroup
)


def _get_rate_limit_group_for_endpoint(endpoint: str, method: str) -> UpbitRateLimitGroup:
    """
    엔드포인트별 Rate Limit 그룹 결정

    Args:
        endpoint: API 엔드포인트
        method: HTTP 메서드

    Returns:
        UpbitRateLimitGroup: 해당 엔드포인트의 Rate Limit 그룹
    """
    # 주문 생성/취소 (8 RPS)
    if endpoint == '/orders' and method == 'POST':
        return UpbitRateLimitGroup.REST_PRIVATE_ORDER
    elif endpoint in ['/order', '/orders'] and method == 'DELETE':
        return UpbitRateLimitGroup.REST_PRIVATE_ORDER
    elif endpoint == '/orders/uuids' and method == 'DELETE':
        return UpbitRateLimitGroup.REST_PRIVATE_ORDER

    # 전체 주문 취소 (0.5 RPS)
    elif endpoint == '/orders/open' and method == 'DELETE':
        return UpbitRateLimitGroup.REST_PRIVATE_CANCEL_ALL

    # 기본: 계좌 조회, 주문 가능 정보 등 (30 RPS)
    else:
        return UpbitRateLimitGroup.REST_PRIVATE_DEFAULT


class DryRunConfig:
    """DRY-RUN 모드 설정"""

    def __init__(self, enabled: bool = True, log_prefix: str = "[DRY-RUN]"):
        self.enabled = enabled
        self.log_prefix = log_prefix


class UpbitPrivateClient:
    """
    업비트 프라이빗 API 클라이언트 - 동적 GCRA + DRY-RUN 지원

    주요 특징:
    - 동적 조정 GCRA Rate Limiter 기본 사용
    - DRY-RUN 모드 기본 활성화 (안전성 우선)
    - 429 오류 자동 감지 및 Rate Limit 조정
    - Infrastructure 로깅 시스템 준수
    - 전역 공유 Rate Limiter 지원
    - 상세한 응답 시간 추적
    - 배치 작업 최적화

    DDD 원칙:
    - Infrastructure 계층 컴포넌트
    - 외부 API 통신 책임
    - 도메인 로직 포함 금지
    """

    BASE_URL = "https://api.upbit.com/v1"

    def __init__(self,
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 dry_run: bool = True,
                 rate_limiter: Optional[UnifiedUpbitRateLimiter] = None,
                 loop: Optional[asyncio.AbstractEventLoop] = None,
                 loop_guard: Optional[LoopGuard] = None):
        """
        업비트 프라이빗 API 클라이언트 초기화

        Args:
            access_key: Upbit API Access Key (None이면 환경변수/ApiKeyService에서 로드)
            secret_key: Upbit API Secret Key (None이면 환경변수/ApiKeyService에서 로드)
            dry_run: DRY-RUN 모드 활성화 (기본값: True, 안전성 우선)
            rate_limiter: 사용자 정의 Rate Limiter (기본값: 전역 공유 인스턴스)

        Raises:
            ValueError: 인증 정보가 없고 인증이 필요한 작업 시도 시

        Note:
            DRY-RUN 모드에서는 실제 주문이 전송되지 않고 로그만 출력됩니다.
            실제 거래를 위해서는 명시적으로 dry_run=False로 설정해야 합니다.
        """
        # Infrastructure 로깅 초기화
        self._logger = create_component_logger("UpbitPrivateClient")

        # 루프 인식 및 LoopGuard 설정
        self._loop = loop  # 명시적 루프 저장 (None은 나중에 추론)
        self._loop_guard = loop_guard or get_loop_guard()
        self._initialized = False

        # 인증 관리자 초기화
        self._auth = UpbitAuthenticator(access_key, secret_key)
        if not self._auth.is_authenticated():
            self._logger.warning("⚠️ API 키가 설정되지 않았습니다. 인증이 필요한 API는 사용할 수 없습니다.")

        # DRY-RUN 설정
        self._dry_run_config = DryRunConfig(enabled=dry_run)
        if dry_run:
            self._logger.info("🔒 DRY-RUN 모드 활성화: 실제 주문이 전송되지 않습니다")

        # Rate Limiter 설정 - 새로운 통합 Rate Limiter 사용
        self._rate_limiter = rate_limiter  # None이면 나중에 전역 인스턴스 사용

        # HTTP 세션 관리
        self._session: Optional[aiohttp.ClientSession] = None

        # 성능 통계 추적
        self._stats = {
            'total_requests': 0,
            'dry_run_requests': 0,
            'real_requests': 0,
            'total_429_retries': 0,
            'last_request_429_retries': 0,
            'average_response_time_ms': 0.0,
            'last_http_response_time_ms': 0.0
        }

        # 마지막 요청 메타데이터 (Rate Limiter 대기/HTTP/총 소요시간 포함)
        self._last_request_meta: Optional[dict] = None

        self._logger.info(f"✅ UpbitPrivateClient 초기화 완료 (DRY-RUN: {dry_run})")

    def __repr__(self):
        return (f"UpbitPrivateClient("
                f"authenticated={self._auth.is_authenticated()}, "
                f"dry_run={self._dry_run_config.enabled})")

    async def __aenter__(self):
        await self._ensure_initialized()  # 루프 인식 및 LoopGuard 검증
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # ================================================================
    # 세션 및 리소스 관리
    # ================================================================

    async def _ensure_initialized(self) -> None:
        """지연 초기화로 루프 바인딩 문제 해결"""
        if not self._initialized:
            # LoopGuard 검증
            if self._loop_guard:
                self._loop_guard.ensure_main_loop(where="UpbitPrivateClient._ensure_initialized")

            # 루프 확정
            if self._loop is None:
                self._loop = asyncio.get_running_loop()
                self._logger.debug(f"🔄 이벤트 루프 인식: {type(self._loop).__name__}@{id(self._loop)}")

            self._initialized = True

    async def _ensure_session(self) -> None:
        """HTTP 세션 확보 - 연결 풀링 및 타임아웃 최적화"""
        await self._ensure_initialized()  # 루프 인식 우선 수행

        if not self._session or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,           # 전체 연결 제한
                limit_per_host=30,   # 호스트당 연결 제한
                keepalive_timeout=30,  # Keep-alive 타임아웃
                enable_cleanup_closed=True
            )
            timeout = aiohttp.ClientTimeout(
                total=30,      # 전체 요청 타임아웃
                connect=10,    # 연결 타임아웃
                sock_read=20   # 소켓 읽기 타임아웃
            )
            # 루프 확정 후 리소스 생성 (QAsync 환경에서 안전)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'upbit-autotrader-vscode/1.0'
                },
                loop=self._loop  # 명시적 루프 바인딩
            )
            self._logger.debug("🌐 HTTP 세션 초기화 완료")

    async def _ensure_rate_limiter(self) -> UnifiedUpbitRateLimiter:
        """Rate Limiter 확보 - 통합 Rate Limiter 사용"""
        if self._rate_limiter is None:
            self._rate_limiter = await get_unified_rate_limiter()
            self._logger.debug("🔄 통합 Rate Limiter 초기화 완료")
        return self._rate_limiter

    async def close(self) -> None:
        """리소스 정리"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            self._logger.debug("🗑️ HTTP 세션 정리 완료")

        # Rate Limiter 리소스 정리는 필요시 여기에 추가

    # ================================================================
    # 상태 조회 및 설정
    # ================================================================

    def is_authenticated(self) -> bool:
        """인증 상태 확인"""
        return self._auth.is_authenticated()

    def is_dry_run_enabled(self) -> bool:
        """DRY-RUN 모드 활성화 여부 확인"""
        return self._dry_run_config.enabled

    def enable_dry_run(self, enabled: bool = True) -> None:
        """DRY-RUN 모드 활성화/비활성화"""
        old_state = self._dry_run_config.enabled
        self._dry_run_config.enabled = enabled

        if old_state != enabled:
            if enabled:
                self._logger.warning("🔒 DRY-RUN 모드 활성화: 실제 주문이 전송되지 않습니다")
            else:
                self._logger.warning("🔓 DRY-RUN 모드 비활성화: 실제 주문이 전송됩니다!")

    def get_stats(self) -> Dict[str, Any]:
        """클라이언트 통계 정보 조회"""
        stats = self._stats.copy()

        # 동적 Rate Limiter 통계 추가
        if self._dynamic_limiter:
            stats['dynamic_limiter'] = self._dynamic_limiter.get_dynamic_status()

        return stats

    def get_dynamic_status(self) -> Dict[str, Any]:
        """동적 Rate Limiter 상태 정보 조회"""
        if self._dynamic_limiter:
            return self._dynamic_limiter.get_dynamic_status()
        else:
            # 동적 limiter가 아직 초기화되지 않았거나 비활성화된 경우
            return {
                'config': {
                    'strategy': self._dynamic_config.strategy.value if self._dynamic_config else 'none',
                    'error_threshold': self._dynamic_config.error_429_threshold if self._dynamic_config else 0,
                    'reduction_ratio': self._dynamic_config.reduction_ratio if self._dynamic_config else 1.0,
                    'recovery_delay': self._dynamic_config.recovery_delay if self._dynamic_config else 0
                },
                'groups': {}
            }

    async def ensure_dynamic_limiter_initialized(self) -> None:
        """동적 Rate Limiter 초기화 보장"""
        if self._use_dynamic_limiter and self._dynamic_limiter is None:
            await self._ensure_rate_limiter()

    def get_last_http_response_time(self) -> float:
        """마지막 HTTP 요청의 순수 서버 응답 시간 조회 (Rate Limiter 대기 시간 제외)"""
        return self._stats['last_http_response_time_ms']

    # ================================================================
    # 요청 메타데이터 조회 (테스트/모니터링 용)
    # ================================================================
    def get_last_request_meta(self) -> Optional[Dict[str, Any]]:
        """직전 요청의 상세 타이밍/재시도 메타데이터 반환"""
        return self._last_request_meta.copy() if self._last_request_meta else None

    # ================================================================
    # 핵심 HTTP 요청 처리
    # ================================================================

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        is_order_request: bool = False
    ) -> Any:
        """
        인증된 HTTP 요청 수행 - 통합 Rate Limiter + 429 자동 처리 및 재시도

        Args:
            method: HTTP 메서드
            endpoint: API 엔드포인트
            params: 쿼리 파라미터
            data: 요청 바디 데이터
            is_order_request: 주문 관련 요청 여부 (DRY-RUN 적용 대상)

        Returns:
            Any: API 응답 데이터

        Raises:
            ValueError: 인증되지 않은 상태에서 인증 필요 요청 시
            Exception: API 오류 또는 네트워크 오류
        """
        # 인증 확인
        if not self._auth.is_authenticated():
            raise ValueError("API 키가 설정되지 않았습니다. 인증이 필요한 API는 사용할 수 없습니다.")

        # DRY-RUN 모드 처리 (주문 요청만)
        if is_order_request and self._dry_run_config.enabled:
            return await self._handle_dry_run_request(method, endpoint, params, data)

        await self._ensure_initialized()  # 루프 인식 및 LoopGuard 검증
        await self._ensure_session()

        if not self._session:
            raise RuntimeError("HTTP 세션이 초기화되지 않았습니다")

        url = f"{self.BASE_URL}{endpoint}"
        max_retries = 3

        # 요청별 429 재시도 카운터 초기화
        self._stats['last_request_429_retries'] = 0
        self._stats['total_requests'] += 1

        # 메타데이터 수집용 변수들 (public_client와 동일)
        attempts = 0
        total_429_retries = 0
        had_429 = False
        acquire_wait_ms: float = 0.0
        http_latency_ms: float = 0.0
        total_cycle_start = time.perf_counter()  # 전체 사이클 시작 (성능 모니터링용)

        for attempt in range(max_retries):
            try:
                attempts += 1

                # 🚀 통합 Rate Limiter 적용 - 지연된 커밋 방식
                rate_limiter = await self._ensure_rate_limiter()
                _acquire_start = time.perf_counter()
                await rate_limiter.acquire(endpoint, method)
                _acquire_end = time.perf_counter()
                acquire_wait_ms += (_acquire_end - _acquire_start) * 1000.0

                # 🔍 디버깅: 실제 업비트 서버에 보내는 파라미터 로깅
                self._logger.debug(f"🌐 업비트 프라이빗 API 요청: {method} {endpoint}")
                if params:
                    self._logger.debug(f"📝 요청 파라미터: {params}")
                if data:
                    self._logger.debug(f"📦 요청 데이터: {data}")

                # 🎲 Micro-jitter: 동시 요청 분산 (5~20ms 랜덤 지연)
                await asyncio.sleep(random.uniform(0.005, 0.020))

                # 인증 헤더 생성
                headers = self._auth.get_private_headers(query_params=params, request_body=data)
                headers.update({
                    'Content-Type': 'application/json',
                    'User-Agent': 'upbit-autotrader-vscode/1.0'
                })

                # 순수 HTTP 요청 시간 측정 시작
                http_start_time = time.perf_counter()

                async with self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=headers
                ) as response:
                    http_end_time = time.perf_counter()

                    # 순수 HTTP 응답 시간 저장 (Rate Limiter 대기 시간 제외)
                    response_time_ms = (http_end_time - http_start_time) * 1000
                    self._stats['last_http_response_time_ms'] = response_time_ms
                    http_latency_ms += response_time_ms

                    # 평균 응답 시간 업데이트
                    if self._stats['average_response_time_ms'] == 0.0:
                        self._stats['average_response_time_ms'] = response_time_ms
                    else:
                        # 지수 이동 평균 (α=0.1)
                        self._stats['average_response_time_ms'] = (
                            0.9 * self._stats['average_response_time_ms']
                            + 0.1 * response_time_ms
                        )

                    if response.status in [200, 201]:  # 200: OK, 201: Created
                        self._stats['real_requests'] += 1
                        response_data = await response.json()
                        self._logger.debug(f"✅ 프라이빗 API 요청 성공: {method} {endpoint} ({response_time_ms:.1f}ms)")

                        # 📊 성공 요청 통계 기록
                        await log_request_success(endpoint, response_time_ms)

                        # 🚀 지연된 커밋: API 성공 후 타임스탬프 윈도우에 커밋
                        # DRY-RUN 모드가 아닌 경우에만 커밋 수행
                        if not (is_order_request and self._dry_run_config.enabled):
                            self._logger.debug(f"🔥 API 성공! 지연된 커밋 실행: {method} {endpoint}")
                            await rate_limiter.commit_timestamp(endpoint, method)
                            self._logger.debug(f"✅ 지연된 커밋 완료: {method} {endpoint}")
                        else:
                            self._logger.debug(f"🏃‍♂️ DRY-RUN 모드: 커밋 건너뛰기 {method} {endpoint}")

                        return response_data

                    elif response.status == 429:
                        # 429 응답 처리 - 업비트 프라이빗 API 분석
                        retry_after = response.headers.get('Retry-After')
                        retry_after_float = float(retry_after) if retry_after else None

                        # 🔍 실제 서버 429 응답 상세 정보 로깅
                        error_body = await response.text()
                        self._logger.info("🚨 실제 프라이빗 서버 429 응답 수신!")
                        self._logger.info(f"📡 응답 헤더: {dict(response.headers)}")
                        self._logger.info(f"📄 응답 본문: {error_body[:200]}{'...' if len(error_body) > 200 else ''}")

                        # 🎯 통합 Rate Limiter에 429 에러 알림
                        await rate_limiter.notify_429_error(endpoint, method)

                        # Rate Limiter 상태 조회 (429 처리 후)
                        rate_limiter_status = rate_limiter.get_comprehensive_status()
                        groups_status = rate_limiter_status.get('groups', {})

                        # 현재 엔드포인트의 Rate Limit 그룹 결정
                        current_group = _get_rate_limit_group_for_endpoint(endpoint, method)
                        group_status = groups_status.get(current_group.value, {})
                        current_rate_ratio = group_status.get('config', {}).get('current_ratio')

                        # 상세 429 모니터링 이벤트 기록
                        await log_429_error(
                            endpoint=endpoint,
                            method=method,
                            retry_after=retry_after_float,
                            attempt_number=attempt + 1,
                            rate_limiter_type="unified",
                            current_rate_ratio=current_rate_ratio,
                            response_headers=dict(response.headers),
                            response_body=error_body,
                            # 추가 컨텍스트 - 프라이빗 API 정보 포함
                            total_429_retries=self._stats['total_429_retries'],
                            session_stats=dict(self._stats),
                            rate_limit_group=current_group.value,
                            url=url,
                            params=params,
                            data=data
                        )

                        # 429 재시도 카운터 업데이트
                        self._stats['last_request_429_retries'] += 1
                        self._stats['total_429_retries'] += 1
                        total_429_retries += 1
                        had_429 = True

                        self._logger.warning(f"⚠️ Rate Limit 초과 (429): {endpoint}, 재시도 {attempt + 1}/{max_retries}")

                        # 429 오류 시 RPS 기반 동적 지수 백오프
                        if attempt < max_retries - 1:
                            # 현재 그룹의 효과적 RPS 계산
                            current_rate_ratio = current_rate_ratio or 1.0

                            # 그룹별 기본 RPS
                            base_rps = {
                                UpbitRateLimitGroup.REST_PRIVATE_DEFAULT: 30.0,
                                UpbitRateLimitGroup.REST_PRIVATE_ORDER: 8.0,
                                UpbitRateLimitGroup.REST_PRIVATE_CANCEL_ALL: 0.5
                            }.get(current_group, 30.0)

                            effective_rps = base_rps * current_rate_ratio

                            # RPS 기반 백오프 베이스 시간 (RPS의 2~4배 간격)
                            base_wait = (2.0 / effective_rps) if effective_rps > 0 else 0.5

                            # 지수 백오프 적용 (베이스 * 2^attempt)
                            wait_time = base_wait * (2 ** attempt)

                            self._logger.info(f"⏳ 429 동적 지수 백오프 대기: {wait_time:.3f}초 "
                                              f"(그룹: {current_group.value}, RPS: {effective_rps:.1f}, 베이스: {base_wait:.3f}초)")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            error_text = await response.text()
                            raise Exception(f"429 Rate Limit 오류로 {max_retries}회 재시도 후에도 실패: {error_text}")

                    else:
                        error_text = await response.text()
                        self._logger.error(f"❌ API 오류 (상태: {response.status}): {error_text}")
                        raise Exception(f"API 오류 (상태: {response.status}): {error_text}")

            except asyncio.TimeoutError:
                self._logger.warning(f"⏰ 타임아웃 발생: {endpoint}, 재시도 {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 0.3  # 타임아웃 재시도
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"타임아웃으로 {max_retries}회 재시도 후에도 실패")

            except Exception as e:
                self._logger.error(f"❌ HTTP 요청 중 오류 발생: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5)
                    continue
                else:
                    raise e

        raise Exception("모든 재시도 실패")

    async def _handle_dry_run_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        DRY-RUN 모드에서 주문 요청 시뮬레이션

        Args:
            method: HTTP 메서드
            endpoint: API 엔드포인트
            params: 쿼리 파라미터
            data: 요청 바디 데이터

        Returns:
            Dict: 시뮬레이션된 응답 데이터
        """
        self._stats['dry_run_requests'] += 1

        # 시뮬레이션 지연 (실제 네트워크 지연 모사)
        await asyncio.sleep(0.1)

        # 요청 정보 로깅
        log_msg = f"{self._dry_run_config.log_prefix} {method} {endpoint}"
        if data:
            log_msg += f" | 데이터: {data}"
        if params:
            log_msg += f" | 파라미터: {params}"

        self._logger.info(log_msg)

        # 시뮬레이션된 응답 생성
        if endpoint == '/orders' and method == 'POST':
            # 주문 생성 시뮬레이션
            return {
                'uuid': f'dry-run-order-{int(time.time() * 1000)}',
                'side': data.get('side', 'unknown') if data else 'unknown',
                'ord_type': data.get('ord_type', 'unknown') if data else 'unknown',
                'price': data.get('price', '0') if data else '0',
                'volume': data.get('volume', '0') if data else '0',
                'market': data.get('market', 'unknown') if data else 'unknown',
                'state': 'wait',
                'created_at': '2023-01-01T00:00:00+09:00',
                'dry_run': True
            }
        elif endpoint in ['/order', '/orders'] and method == 'DELETE':
            # 주문 취소 시뮬레이션
            return {
                'uuid': params.get('uuid', 'dry-run-cancel') if params else 'dry-run-cancel',
                'state': 'cancel',
                'cancelled_at': '2023-01-01T00:00:00+09:00',
                'dry_run': True
            }
        else:
            # 기본 시뮬레이션 응답
            return {
                'success': True,
                'message': 'DRY-RUN 모드: 실제 요청이 전송되지 않았습니다',
                'dry_run': True,
                'endpoint': endpoint,
                'method': method
            }

    # ================================================================
    # 자산(Asset) API - 계좌 및 자산 관리
    # ================================================================

    async def get_accounts(self) -> Dict[str, Dict[str, Any]]:
        """
        계좌 정보 조회

        내가 보유한 자산 리스트를 통화별로 인덱싱하여 반환합니다.

        Returns:
            Dict[str, Dict]: 통화별 계좌 정보
                {
                    'KRW': {
                        'currency': 'KRW',
                        'balance': '20000.0',
                        'locked': '0.0',
                        'avg_buy_price': '0',
                        'avg_buy_price_modified': False,
                        'unit_currency': 'KRW'
                    },
                    'BTC': {
                        'currency': 'BTC',
                        'balance': '0.00005',
                        'locked': '0.0',
                        'avg_buy_price': '50000000',
                        'avg_buy_price_modified': False,
                        'unit_currency': 'KRW'
                    }
                }

        Note:
            기존 List 형식이 필요한 경우:
            accounts_list = list(accounts.values())

        Raises:
            ValueError: 인증되지 않은 상태
            Exception: API 오류
        """
        response = await self._make_request('GET', '/accounts')

        # List 응답을 Dict로 변환
        accounts_dict = {}
        if isinstance(response, list):
            for account in response:
                if isinstance(account, dict):
                    currency = account.get('currency')
                    if currency:
                        accounts_dict[currency] = account

        self._logger.debug(f"📊 계좌 정보 조회 완료: {len(accounts_dict)}개 통화")
        return accounts_dict

    # ================================================================
    # 주문(Order) API - 주문 생성, 조회, 취소
    # ================================================================

    async def get_orders_chance(self, market: str) -> Dict[str, Any]:
        """
        주문 가능 정보 조회

        마켓별 주문 가능 정보를 확인합니다.

        Args:
            market: 마켓 코드 (예: KRW-BTC)

        Returns:
            Dict[str, Any]: 주문 가능 정보
                {
                    'bid_fee': '0.0005',           # 매수 수수료율
                    'ask_fee': '0.0005',           # 매도 수수료율
                    'market': {
                        'id': 'KRW-BTC',
                        'name': '비트코인',
                        'order_types': ['limit', 'price', 'market'],
                        'order_sides': ['ask', 'bid'],
                        'bid': {
                            'currency': 'KRW',
                            'price_unit': None,
                            'min_total': '5000'    # 최소 주문 금액
                        },
                        'ask': {
                            'currency': 'BTC',
                            'price_unit': None,
                            'min_total': '5000'
                        },
                        'max_total': '1000000000',     # 최대 주문 금액
                        'state': 'active'
                    },
                    'bid_account': {...},               # 매수 가능 계좌 정보
                    'ask_account': {...}                # 매도 가능 계좌 정보
                }

        Raises:
            ValueError: 인증되지 않은 상태 또는 잘못된 마켓 코드
            Exception: API 오류
        """
        if not market:
            raise ValueError("마켓 코드는 필수입니다")

        params = {'market': market}
        response = await self._make_request('GET', '/orders/chance', params=params)

        self._logger.debug(f"💰 주문 가능 정보 조회 완료: {market}")
        return response

    async def place_order(
        self,
        market: str,
        side: Literal['bid', 'ask'],
        ord_type: Literal['limit', 'price', 'market'],
        volume: Optional[Decimal] = None,
        price: Optional[Decimal] = None,
        identifier: Optional[str] = None,
        dry_run: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        주문 생성

        Args:
            market: 마켓 코드 (예: KRW-BTC)
            side: 주문 종류
                - 'bid': 매수
                - 'ask': 매도
            ord_type: 주문 타입
                - 'limit': 지정가 주문 (volume, price 필수)
                - 'price': 시장가 매수 (price 필수)
                - 'market': 시장가 매도 (volume 필수)
            volume: 주문 수량 (지정가, 시장가 매도 시 필수)
            price: 주문 가격 (지정가, 시장가 매수 시 필수)
            identifier: 조회용 사용자 지정값 (최대 40자)
            dry_run: 이 요청에 대한 DRY-RUN 모드 override (None이면 클라이언트 설정 따름)

        Returns:
            Dict[str, Any]: 생성된 주문 정보
                {
                    'uuid': 'order-uuid-string',
                    'side': 'bid',
                    'ord_type': 'limit',
                    'price': '50000000.0',
                    'volume': '0.001',
                    'market': 'KRW-BTC',
                    'state': 'wait',
                    'created_at': '2023-01-01T12:00:00+09:00',
                    'trades_count': 0,
                    'executed_volume': '0.0',
                    'remaining_volume': '0.001',
                    'paid_fee': '0.0',
                    'locked': '50000.0',
                    'identifier': 'my-order-001'
                }

        Examples:
            # 지정가 매수 (0.001 BTC를 50,000,000원에)
            order = await client.place_order(
                market='KRW-BTC',
                side='bid',
                ord_type='limit',
                volume=Decimal('0.001'),
                price=Decimal('50000000')
            )

            # 시장가 매수 (5만원어치)
            order = await client.place_order(
                market='KRW-BTC',
                side='bid',
                ord_type='price',
                price=Decimal('50000')
            )

            # 시장가 매도 (0.001 BTC)
            order = await client.place_order(
                market='KRW-BTC',
                side='ask',
                ord_type='market',
                volume=Decimal('0.001')
            )

        Raises:
            ValueError: 잘못된 파라미터 조합
            Exception: API 오류
        """
        # 파라미터 검증
        if not market:
            raise ValueError("마켓 코드는 필수입니다")

        if ord_type == 'limit' and (volume is None or price is None):
            raise ValueError("지정가 주문에는 volume과 price가 모두 필요합니다")
        elif ord_type == 'price' and price is None:
            raise ValueError("시장가 매수에는 price가 필요합니다")
        elif ord_type == 'market' and volume is None:
            raise ValueError("시장가 매도에는 volume이 필요합니다")

        if identifier and len(identifier) > 40:
            raise ValueError("identifier는 최대 40자까지 가능합니다")

        # 주문 데이터 구성
        data = {
            'market': market,
            'side': side,
            'ord_type': ord_type
        }

        if volume is not None:
            data['volume'] = str(volume)
        if price is not None:
            data['price'] = str(price)
        if identifier is not None:
            data['identifier'] = identifier

        # DRY-RUN 모드 결정 (요청별 override 또는 클라이언트 설정)
        effective_dry_run = dry_run if dry_run is not None else self._dry_run_config.enabled

        # 임시로 DRY-RUN 설정 변경
        original_dry_run = self._dry_run_config.enabled
        if dry_run is not None:
            self._dry_run_config.enabled = dry_run

        try:
            response = await self._make_request('POST', '/orders', data=data, is_order_request=True)

            order_info = f"{side} {ord_type}"
            if volume:
                order_info += f" volume={volume}"
            if price:
                order_info += f" price={price}"

            if effective_dry_run:
                self._logger.info(f"🔒 [DRY-RUN] 주문 생성: {market} {order_info}")
            else:
                self._logger.info(f"📝 주문 생성 완료: {market} {order_info}")

            return response

        finally:
            # DRY-RUN 설정 복원
            if dry_run is not None:
                self._dry_run_config.enabled = original_dry_run

    async def get_order(self, uuid: Optional[str] = None, identifier: Optional[str] = None) -> Dict[str, Any]:
        """
        개별 주문 조회

        Args:
            uuid: 주문 UUID (uuid 또는 identifier 중 하나 필수)
            identifier: 조회용 사용자 지정값

        Returns:
            Dict[str, Any]: 주문 상세 정보
                {
                    'uuid': 'order-uuid-string',
                    'side': 'bid',
                    'ord_type': 'limit',
                    'price': '50000000.0',
                    'volume': '0.001',
                    'market': 'KRW-BTC',
                    'state': 'wait',
                    'created_at': '2023-01-01T12:00:00+09:00',
                    'trades': [...],              # 체결 내역
                    'trades_count': 0,
                    'executed_volume': '0.0',
                    'remaining_volume': '0.001',
                    'paid_fee': '0.0',
                    'locked': '50000.0'
                }

        Raises:
            ValueError: uuid와 identifier가 모두 없음
            Exception: API 오류
        """
        params = {}
        if uuid:
            params['uuid'] = uuid
        elif identifier:
            params['identifier'] = identifier
        else:
            raise ValueError("uuid 또는 identifier 중 하나는 필수입니다")

        response = await self._make_request('GET', '/order', params=params)

        self._logger.debug(f"🔍 주문 조회 완료: {uuid or identifier}")
        return response

    async def get_orders(
        self,
        market: Optional[str] = None,
        uuids: Optional[List[str]] = None,
        identifiers: Optional[List[str]] = None,
        state: Optional[Literal['wait', 'watch', 'done', 'cancel']] = None,
        states: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 100,
        order_by: Literal['asc', 'desc'] = 'desc'
    ) -> Dict[str, Dict[str, Any]]:
        """
        주문 목록 조회

        Args:
            market: 마켓 코드 (예: KRW-BTC)
            uuids: 주문 UUID 목록
            identifiers: 사용자 지정 식별자 목록
            state: 주문 상태
                - 'wait': 체결대기
                - 'watch': 예약주문
                - 'done': 체결완료
                - 'cancel': 취소
            states: 주문 상태 목록 (state와 중복 사용 불가)
            page: 페이지 번호 (1부터 시작)
            limit: 페이지당 항목 수 (최대 100)
            order_by: 정렬 순서 ('asc': 오름차순, 'desc': 내림차순)

        Returns:
            Dict[str, Dict[str, Any]]: UUID를 키로 하는 주문 정보 딕셔너리
                {
                    'order-uuid-1': {
                        'uuid': 'order-uuid-1',
                        'side': 'bid',
                        'ord_type': 'limit',
                        'price': '50000000.0',
                        'volume': '0.001',
                        'market': 'KRW-BTC',
                        'state': 'wait',
                        'created_at': '2023-01-01T12:00:00+09:00',
                        ...
                    },
                    'order-uuid-2': {...}
                }

        Note:
            기존 List 형식이 필요한 경우:
            orders_list = list(orders.values())

        Raises:
            ValueError: 잘못된 파라미터 조합
            Exception: API 오류
        """
        params = {
            'page': page,
            'limit': min(limit, 100),
            'order_by': order_by
        }

        if market:
            params['market'] = market
        if uuids:
            if len(uuids) > 100:
                raise ValueError("UUID 목록은 최대 100개까지 가능합니다")
            params['uuids'] = ','.join(uuids)
        if identifiers:
            if len(identifiers) > 100:
                raise ValueError("identifier 목록은 최대 100개까지 가능합니다")
            params['identifiers'] = ','.join(identifiers)
        if state:
            params['state'] = state
        if states:
            params['states'] = ','.join(states) if isinstance(states, list) else states

        response = await self._make_request('GET', '/orders', params=params)

        # List 응답을 Dict로 변환
        orders_dict = {}
        if isinstance(response, list):
            for order in response:
                if isinstance(order, dict):
                    order_id = order.get('uuid') or order.get('identifier')
                    if order_id:
                        orders_dict[order_id] = order

        self._logger.debug(f"📋 주문 목록 조회 완료: {len(orders_dict)}개 주문")
        return orders_dict

    async def get_open_orders(
        self,
        market: Optional[str] = None,
        state: Optional[Literal['wait', 'watch']] = None,
        page: int = 1,
        limit: int = 100,
        order_by: Literal['asc', 'desc'] = 'desc'
    ) -> Dict[str, Dict[str, Any]]:
        """
        체결 대기 주문 목록 조회

        현재 체결 대기 중인 주문들을 조회합니다.

        Args:
            market: 마켓 코드 (예: KRW-BTC)
            state: 주문 상태 (기본값: 'wait')
                - 'wait': 체결대기
                - 'watch': 예약주문
            page: 페이지 번호 (1부터 시작)
            limit: 페이지당 항목 수 (최대 100)
            order_by: 정렬 순서

        Returns:
            Dict[str, Dict[str, Any]]: 체결 대기 주문들

        Raises:
            Exception: API 오류
        """
        params = {
            'page': page,
            'limit': min(limit, 100),
            'order_by': order_by,
            'state': state or 'wait'
        }

        if market:
            params['market'] = market

        response = await self._make_request('GET', '/orders/open', params=params)

        # List 응답을 Dict로 변환
        orders_dict = {}
        if isinstance(response, list):
            for order in response:
                if isinstance(order, dict):
                    order_id = order.get('uuid') or order.get('identifier')
                    if order_id:
                        orders_dict[order_id] = order

        self._logger.debug(f"⏳ 체결 대기 주문 조회 완료: {len(orders_dict)}개 주문")
        return orders_dict

    async def get_closed_orders(
        self,
        market: Optional[str] = None,
        state: Optional[Literal['done', 'cancel']] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
        order_by: Literal['asc', 'desc'] = 'desc'
    ) -> Dict[str, Dict[str, Any]]:
        """
        종료 주문 목록 조회

        체결 완료되거나 취소된 주문들을 조회합니다.
        조회 기간은 최대 7일입니다.

        Args:
            market: 마켓 코드 (예: KRW-BTC)
            state: 주문 상태 (기본값: 모든 상태)
                - 'done': 체결완료
                - 'cancel': 취소
            start_time: 조회 시작 시간 (ISO 8601 형식, 예: '2023-01-01T00:00:00+09:00')
            end_time: 조회 종료 시간 (ISO 8601 형식)
            limit: 페이지당 항목 수 (최대 1000)
            order_by: 정렬 순서

        Returns:
            Dict[str, Dict[str, Any]]: 종료된 주문들

        Note:
            조회 기간이 지정되지 않으면 최근 7일간의 주문을 조회합니다.

        Raises:
            ValueError: 조회 기간이 7일을 초과하는 경우
            Exception: API 오류
        """
        # 업비트 공식 /orders/closed 엔드포인트 사용
        params = {
            'limit': min(limit, 1000),
            'order_by': order_by
        }

        # 상태 필터링 - 우선 단일 상태로 테스트
        if state == 'done':
            params['state'] = 'done'
        elif state == 'cancel':
            params['state'] = 'cancel'
        else:
            # 기본값: done 상태만 (테스트용)
            params['state'] = 'done'

        if market:
            params['market'] = market
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time

        response = await self._make_request('GET', '/orders/closed', params=params)

        # List 응답을 Dict로 변환
        orders_dict = {}
        if isinstance(response, list):
            for order in response:
                if isinstance(order, dict):
                    order_id = order.get('uuid') or order.get('identifier')
                    if order_id:
                        orders_dict[order_id] = order

        self._logger.debug(f"✅ 종료 주문 조회 완료: {len(orders_dict)}개 주문")
        return orders_dict

    async def cancel_order(
        self,
        uuid: Optional[str] = None,
        identifier: Optional[str] = None,
        dry_run: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        주문 취소

        Args:
            uuid: 주문 UUID (uuid 또는 identifier 중 하나 필수)
            identifier: 조회용 사용자 지정값
            dry_run: 이 요청에 대한 DRY-RUN 모드 override

        Returns:
            Dict[str, Any]: 취소된 주문 정보
                {
                    'uuid': 'order-uuid-string',
                    'side': 'bid',
                    'ord_type': 'limit',
                    'price': '50000000.0',
                    'volume': '0.001',
                    'market': 'KRW-BTC',
                    'state': 'cancel',
                    'cancelled_at': '2023-01-01T12:00:00+09:00',
                    ...
                }

        Raises:
            ValueError: uuid와 identifier가 모두 없음
            Exception: API 오류
        """
        data = {}
        if uuid:
            data['uuid'] = uuid
        elif identifier:
            data['identifier'] = identifier
        else:
            raise ValueError("uuid 또는 identifier 중 하나는 필수입니다")

        # DRY-RUN 모드 결정
        effective_dry_run = dry_run if dry_run is not None else self._dry_run_config.enabled

        # 임시로 DRY-RUN 설정 변경
        original_dry_run = self._dry_run_config.enabled
        if dry_run is not None:
            self._dry_run_config.enabled = dry_run

        try:
            response = await self._make_request('DELETE', '/order', data=data, is_order_request=True)

            if effective_dry_run:
                self._logger.info(f"🔒 [DRY-RUN] 주문 취소: {uuid or identifier}")
            else:
                self._logger.info(f"❌ 주문 취소 완료: {uuid or identifier}")

            return response

        finally:
            # DRY-RUN 설정 복원
            if dry_run is not None:
                self._dry_run_config.enabled = original_dry_run

    # ================================================================
    # 고급 주문 기능 - 대량 처리 및 특수 주문
    # ================================================================

    async def cancel_orders_by_ids(
        self,
        uuids: Optional[List[str]] = None,
        identifiers: Optional[List[str]] = None,
        dry_run: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        ID로 주문 목록 취소

        최대 20개의 주문을 한 번에 취소할 수 있습니다.

        Args:
            uuids: 취소할 주문 UUID 목록 (최대 20개)
            identifiers: 취소할 주문 식별자 목록 (최대 20개)
            dry_run: 이 요청에 대한 DRY-RUN 모드 override

        Returns:
            Dict[str, Any]: 취소 결과 (성공/실패 주문 목록)
                {
                    'cancelled': [...],    # 성공적으로 취소된 주문들
                    'failed': [...]        # 취소 실패한 주문들
                }

        Raises:
            ValueError: 잘못된 파라미터
            Exception: API 오류
        """
        if not uuids and not identifiers:
            raise ValueError("uuids 또는 identifiers 중 하나는 필수입니다")
        if uuids and identifiers:
            raise ValueError("uuids와 identifiers는 동시에 사용할 수 없습니다")
        if uuids and len(uuids) > 20:
            raise ValueError("취소 가능한 최대 UUID 개수는 20개입니다")
        if identifiers and len(identifiers) > 20:
            raise ValueError("취소 가능한 최대 identifier 개수는 20개입니다")

        params = {}
        if uuids:
            # 업비트 API는 배열 형식을 요구: uuids[]=uuid1&uuids[]=uuid2
            params['uuids[]'] = uuids
        if identifiers:
            # 업비트 API는 배열 형식을 요구: identifiers[]=id1&identifiers[]=id2
            params['identifiers[]'] = identifiers

        # DRY-RUN 모드 결정
        effective_dry_run = dry_run if dry_run is not None else self._dry_run_config.enabled

        # 임시로 DRY-RUN 설정 변경
        original_dry_run = self._dry_run_config.enabled
        if dry_run is not None:
            self._dry_run_config.enabled = dry_run

        try:
            response = await self._make_request('DELETE', '/orders/uuids', params=params, is_order_request=True)

            count = len(uuids) if uuids else len(identifiers or [])
            if effective_dry_run:
                self._logger.info(f"🔒 [DRY-RUN] 일괄 주문 취소: {count}개 주문")
            else:
                self._logger.info(f"❌ 일괄 주문 취소 완료: {count}개 주문")

            return response

        finally:
            # DRY-RUN 설정 복원
            if dry_run is not None:
                self._dry_run_config.enabled = original_dry_run

    async def batch_cancel_orders(
        self,
        quote_currencies: Optional[List[str]] = None,
        cancel_side: Literal['all', 'ask', 'bid'] = 'all',
        count: int = 20,
        order_by: Literal['asc', 'desc'] = 'desc',
        dry_run: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        주문 일괄 취소

        조건을 만족하는 최대 300개의 주문을 일괄 취소합니다.

        Args:
            quote_currencies: 기준 통화 목록 (예: ['KRW', 'BTC', 'USDT'])
            cancel_side: 취소할 주문 방향
                - 'all': 전체
                - 'ask': 매도만
                - 'bid': 매수만
            count: 취소할 최대 주문 수 (최대 300)
            order_by: 정렬 순서
            dry_run: 이 요청에 대한 DRY-RUN 모드 override

        Returns:
            Dict[str, Any]: 취소 결과

        Note:
            Rate Limit: 최대 2초당 1회 호출 가능 (REST_PRIVATE_CANCEL_ALL 그룹)

        Raises:
            ValueError: count가 300을 초과하는 경우
            Exception: API 오류
        """
        if count > 300:
            raise ValueError("취소 가능한 최대 주문 수는 300개입니다")

        params = {
            'cancel_side': cancel_side,
            'count': min(count, 300),
            'order_by': order_by
        }

        if quote_currencies:
            params['quote_currencies'] = ','.join(quote_currencies)

        # DRY-RUN 모드 결정
        effective_dry_run = dry_run if dry_run is not None else self._dry_run_config.enabled

        # 임시로 DRY-RUN 설정 변경
        original_dry_run = self._dry_run_config.enabled
        if dry_run is not None:
            self._dry_run_config.enabled = dry_run

        try:
            response = await self._make_request('DELETE', '/orders/open', params=params, is_order_request=True)

            if effective_dry_run:
                self._logger.warning(f"🔒 [DRY-RUN] 대량 주문 취소: {cancel_side} 방향, 최대 {count}개")
            else:
                self._logger.warning(f"❌ 대량 주문 취소 완료: {cancel_side} 방향, 최대 {count}개")

            return response

        finally:
            # DRY-RUN 설정 복원
            if dry_run is not None:
                self._dry_run_config.enabled = original_dry_run

    # ================================================================
    # 체결 내역 조회
    # ================================================================

    async def get_trades_history(
        self,
        market: Optional[str] = None,
        limit: int = 100,
        order_by: Literal['asc', 'desc'] = 'desc'
    ) -> Dict[str, Dict[str, Any]]:
        """
        종료 주문 목록 조회 (체결 완료/취소된 주문)

        Args:
            market: 마켓 코드 (예: KRW-BTC)
            limit: 조회 개수 (최대 500)
            order_by: 정렬 순서

        Returns:
            Dict[str, Dict[str, Any]]: 체결 내역 딕셔너리
                {
                    'trade-uuid-1': {
                        'uuid': 'trade-uuid-1',
                        'side': 'bid',
                        'price': '50000000.0',
                        'volume': '0.001',
                        'market': 'KRW-BTC',
                        'created_at': '2023-01-01T12:00:00+09:00',
                        'order_uuid': 'order-uuid',
                        'fee': '25.0',
                        'fee_currency': 'KRW'
                    },
                    'trade-uuid-2': {...}
                }

        Raises:
            ValueError: limit이 500을 초과하는 경우
            Exception: API 오류
        """
        if limit > 500:
            raise ValueError("조회 개수는 최대 500개까지 가능합니다")

        params = {
            'limit': min(limit, 500),
            'order_by': order_by
        }
        if market:
            params['market'] = market

        response = await self._make_request('GET', '/orders/closed', params=params)

        # List 응답을 Dict로 변환
        trades_dict = {}
        if isinstance(response, list):
            for i, trade in enumerate(response):
                if isinstance(trade, dict):
                    trade_id = trade.get('uuid', f'trade_{i}')
                    trades_dict[trade_id] = trade

        self._logger.debug(f"📈 종료 주문 목록 조회 완료: {len(trades_dict)}개 주문")
        return trades_dict


# ================================================================
# 편의 팩토리 함수
# ================================================================

def create_upbit_private_client(
    access_key: str,
    secret_key: str,
    dry_run: bool = True,
    use_dynamic_limiter: bool = True
) -> UpbitPrivateClient:
    """
    업비트 프라이빗 API 클라이언트 생성 (편의 함수)

    Args:
        access_key: Upbit API Access Key
        secret_key: Upbit API Secret Key
        dry_run: DRY-RUN 모드 활성화 (기본값: True, 안전성 우선)
        use_dynamic_limiter: 동적 Rate Limiter 사용 여부

    Returns:
        UpbitPrivateClient: 설정된 클라이언트 인스턴스

    Note:
        DRY-RUN 모드가 기본으로 활성화되어 있습니다.
        실제 거래를 위해서는 명시적으로 dry_run=False로 설정해야 합니다.
    """
    return UpbitPrivateClient(
        access_key=access_key,
        secret_key=secret_key,
        dry_run=dry_run,
        use_dynamic_limiter=use_dynamic_limiter
    )


async def create_upbit_private_client_async(
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    dry_run: bool = True,
    rate_limiter: Optional[UnifiedUpbitRateLimiter] = None
) -> UpbitPrivateClient:
    """
    업비트 프라이빗 API 클라이언트 비동기 생성 (편의 함수)

    Args:
        access_key: Upbit API Access Key (None이면 ApiKeyService에서 로드)
        secret_key: Upbit API Secret Key (None이면 ApiKeyService에서 로드)
        dry_run: DRY-RUN 모드 활성화 (기본값: True)
        rate_limiter: 사용자 정의 Rate Limiter (기본값: 전역 공유 인스턴스)

    Returns:
        UpbitPrivateClient: 초기화된 클라이언트 인스턴스
    """
    client = UpbitPrivateClient(
        access_key=access_key,
        secret_key=secret_key,
        dry_run=dry_run,
        rate_limiter=rate_limiter
    )

    # 세션 미리 초기화
    await client._ensure_session()

    return client
