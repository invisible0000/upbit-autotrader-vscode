"""
JWT 토큰 자동 갱신 관리자
=====================

Private WebSocket을 위한 JWT 토큰 생명주기 관리
80% 만료 시점 자동 갱신, 실패 시 REST 폴백

🎯 특징:
- 자동 토큰 갱신 (만료 80% 시점)
- 백그라운드 갱신 루프
- 갱신 실패 시 graceful degradation
- 토큰 유효성 검증
"""

import asyncio
import time
import jwt
from typing import Optional, Dict, Any
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger

# 인증 시스템 연동
try:
    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import UpbitAuthenticator
    AUTH_AVAILABLE = True
    AuthenticatorClass = UpbitAuthenticator
except ImportError:
    AUTH_AVAILABLE = False
    AuthenticatorClass = None

from .exceptions import AuthenticationError


# AuthenticationError는 이미 exceptions.py에 정의되어 있음


class JWTManager:
    """JWT 토큰 자동 갱신 관리자"""

    def __init__(self, refresh_threshold: float = 0.8, retry_count: int = 3):
        """
        JWT 매니저 초기화

        Args:
            refresh_threshold: 갱신 임계값 (0.8 = 80% 만료 시점)
            retry_count: 갱신 실패 시 재시도 횟수
        """
        self.logger = create_component_logger("JWTManager")
        self.refresh_threshold = refresh_threshold
        self.retry_count = retry_count

        # 토큰 상태
        self._current_token: Optional[str] = None
        self._token_issued_at: Optional[float] = None
        self._token_expires_at: Optional[float] = None
        self._token_payload: Optional[Dict[str, Any]] = None

        # 갱신 루프
        self._refresh_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._shutdown_requested = False

        # 통계
        self._refresh_count = 0
        self._last_refresh_time: Optional[float] = None
        self._consecutive_failures = 0

        if not AUTH_AVAILABLE:
            self.logger.warning("UpbitAuthenticator를 사용할 수 없습니다. JWT 기능이 제한됩니다.")

    async def get_valid_token(self) -> Optional[str]:
        """
        유효한 JWT 토큰 반환

        Returns:
            Optional[str]: 유효한 JWT 토큰 또는 None
        """
        if not AUTH_AVAILABLE:
            self.logger.error("인증 시스템이 사용할 수 없습니다")
            return None

        try:
            # 현재 토큰이 유효한지 확인
            if self._is_token_valid():
                return self._current_token

            # 토큰이 없거나 만료됨 - 새로 생성
            await self._refresh_token()

            return self._current_token if self._is_token_valid() else None

        except Exception as e:
            self.logger.error(f"토큰 획득 실패: {e}")
            return None

    async def force_refresh(self) -> bool:
        """
        강제 토큰 갱신

        Returns:
            bool: 갱신 성공 여부
        """
        try:
            await self._refresh_token()
            return self._is_token_valid()
        except Exception as e:
            self.logger.error(f"강제 갱신 실패: {e}")
            return False

    def start_auto_refresh(self) -> None:
        """자동 갱신 시작"""
        if self._is_running:
            self.logger.warning("자동 갱신이 이미 실행 중입니다")
            return

        if not AUTH_AVAILABLE:
            self.logger.error("인증 시스템이 없어 자동 갱신을 시작할 수 없습니다")
            return

        self._shutdown_requested = False
        self._refresh_task = asyncio.create_task(self._auto_refresh_loop())
        self._is_running = True

        self.logger.info("JWT 자동 갱신 시작")

    async def stop_auto_refresh(self) -> None:
        """자동 갱신 중지"""
        if not self._is_running:
            return

        self.logger.info("JWT 자동 갱신 중지 요청")
        self._shutdown_requested = True

        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass

        self._is_running = False
        self.logger.info("JWT 자동 갱신 중지 완료")

    def get_token_info(self) -> Dict[str, Any]:
        """
        현재 토큰 정보 반환

        Returns:
            Dict: 토큰 상태 정보
        """
        if not self._current_token:
            return {
                'has_token': False,
                'is_valid': False,
                'refresh_count': self._refresh_count,
                'consecutive_failures': self._consecutive_failures
            }

        now = time.time()
        time_to_expire = (self._token_expires_at or 0) - now

        return {
            'has_token': True,
            'is_valid': self._is_token_valid(),
            'issued_at': datetime.fromtimestamp(self._token_issued_at or 0).isoformat() if self._token_issued_at else None,
            'expires_at': datetime.fromtimestamp(self._token_expires_at or 0).isoformat() if self._token_expires_at else None,
            'time_to_expire_seconds': max(0, time_to_expire),
            'refresh_progress': self._get_refresh_progress(),
            'refresh_count': self._refresh_count,
            'last_refresh': (
                datetime.fromtimestamp(self._last_refresh_time).isoformat()
                if self._last_refresh_time else None
            ),
            'consecutive_failures': self._consecutive_failures,
            'auto_refresh_running': self._is_running
        }

    # =============================================================================
    # 내부 구현 메서드
    # =============================================================================

    async def _auto_refresh_loop(self) -> None:
        """토큰 자동 갱신 루프"""
        self.logger.info(f"자동 갱신 루프 시작 (임계값: {self.refresh_threshold * 100}%)")

        while not self._shutdown_requested:
            try:
                # 초기 토큰이 없으면 생성
                if not self._current_token:
                    await self._refresh_token()

                # 갱신이 필요한지 확인
                if self._should_refresh():
                    self.logger.info("토큰 갱신 필요 - 갱신 시작")
                    await self._refresh_token()

                # 다음 확인까지 대기 (30초)
                await asyncio.sleep(30)

            except asyncio.CancelledError:
                self.logger.info("자동 갱신 루프 취소됨")
                break
            except Exception as e:
                self.logger.error(f"자동 갱신 루프 오류: {e}")
                await asyncio.sleep(60)  # 오류 시 1분 대기

    async def _refresh_token(self) -> None:
        """토큰 갱신 수행"""
        if not AUTH_AVAILABLE:
            raise AuthenticationError("인증 시스템이 사용할 수 없습니다")

        for attempt in range(self.retry_count):
            try:
                self.logger.debug(f"토큰 갱신 시도 {attempt + 1}/{self.retry_count}")

                # UpbitAuthenticator를 통한 JWT 생성
                if not AUTH_AVAILABLE or AuthenticatorClass is None:
                    raise AuthenticationError("인증 시스템을 사용할 수 없습니다")

                authenticator = AuthenticatorClass()
                new_token = authenticator.create_jwt_token(
                    query_params={}
                )

                if not new_token:
                    raise AuthenticationError("JWT 토큰 생성 실패")

                # 토큰 검증 및 파싱
                payload = self._parse_token(new_token)
                if not payload:
                    raise AuthenticationError("생성된 토큰 파싱 실패")

                # 토큰 업데이트
                now = time.time()
                self._current_token = new_token
                self._token_issued_at = payload.get('iat', now)
                self._token_expires_at = payload.get('exp', now + 600)  # 기본 10분
                self._token_payload = payload

                # 통계 업데이트
                self._refresh_count += 1
                self._last_refresh_time = now
                self._consecutive_failures = 0

                expires_in = (self._token_expires_at or now) - now
                self.logger.info(f"토큰 갱신 성공 (유효기간: {expires_in:.0f}초)")
                return

            except Exception as e:
                self._consecutive_failures += 1
                self.logger.warning(f"토큰 갱신 실패 (시도 {attempt + 1}): {e}")

                if attempt < self.retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # 지수 백오프

        # 모든 시도 실패
        self.logger.error(f"토큰 갱신 완전 실패 ({self.retry_count}회 시도)")
        raise AuthenticationError(f"토큰 갱신 실패 - {self._consecutive_failures}회 연속 실패")

    def _is_token_valid(self) -> bool:
        """토큰 유효성 검사"""
        if not self._current_token or not self._token_expires_at:
            return False

        now = time.time()
        return now < self._token_expires_at

    def _should_refresh(self) -> bool:
        """갱신이 필요한지 판단"""
        if not self._current_token or not self._token_expires_at or not self._token_issued_at:
            return True

        now = time.time()
        total_lifetime = self._token_expires_at - self._token_issued_at
        elapsed = now - self._token_issued_at

        # 임계값에 도달했는지 확인
        progress = elapsed / total_lifetime if total_lifetime > 0 else 1.0
        return progress >= self.refresh_threshold

    def _get_refresh_progress(self) -> float:
        """갱신 진행률 계산 (0.0 ~ 1.0)"""
        if not self._token_issued_at or not self._token_expires_at:
            return 1.0

        now = time.time()
        total_lifetime = self._token_expires_at - self._token_issued_at
        elapsed = now - self._token_issued_at

        if total_lifetime <= 0:
            return 1.0

        return min(1.0, max(0.0, elapsed / total_lifetime))

    def _parse_token(self, token: str) -> Optional[Dict[str, Any]]:
        """JWT 토큰 파싱 (검증 없이)"""
        try:
            # JWT 헤더와 페이로드만 파싱 (서명 검증 안함)
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except Exception as e:
            self.logger.error(f"토큰 파싱 실패: {e}")
            return None


# =============================================================================
# 편의 함수들
# =============================================================================

_global_jwt_manager: Optional[JWTManager] = None


async def get_global_jwt_manager() -> JWTManager:
    """
    전역 JWT 매니저 인스턴스 반환 (싱글톤)

    Returns:
        JWTManager: 전역 JWT 매니저
    """
    global _global_jwt_manager

    if _global_jwt_manager is None:
        _global_jwt_manager = JWTManager()
        _global_jwt_manager.start_auto_refresh()

    return _global_jwt_manager


async def get_valid_jwt_token() -> Optional[str]:
    """
    유효한 JWT 토큰 빠른 획득

    Returns:
        Optional[str]: 유효한 JWT 토큰
    """
    manager = await get_global_jwt_manager()
    return await manager.get_valid_token()


async def shutdown_global_jwt_manager() -> None:
    """전역 JWT 매니저 종료"""
    global _global_jwt_manager

    if _global_jwt_manager:
        await _global_jwt_manager.stop_auto_refresh()
        _global_jwt_manager = None


# =============================================================================
# 사용 예시
# =============================================================================

async def example_usage():
    """JWT Manager 사용 예시"""

    # 1. 전역 매니저 사용 (권장)
    jwt_manager = await get_global_jwt_manager()

    # 2. 토큰 획득
    token = await jwt_manager.get_valid_token()
    if token:
        print(f"JWT 토큰 획득: {token[:50]}...")
    else:
        print("JWT 토큰 획득 실패")

    # 3. 토큰 정보 확인
    info = jwt_manager.get_token_info()
    print(f"토큰 정보: {info}")

    # 4. 강제 갱신
    success = await jwt_manager.force_refresh()
    print(f"강제 갱신 결과: {success}")

    # 5. 빠른 토큰 획득
    quick_token = await get_valid_jwt_token()
    print(f"빠른 토큰: {quick_token[:50] if quick_token else 'None'}...")


if __name__ == "__main__":
    asyncio.run(example_usage())
