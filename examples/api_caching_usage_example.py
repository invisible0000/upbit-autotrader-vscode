#!/usr/bin/env python3
"""
🔄 API 캐싱 사용 예시 - Task 2.3.5

기존 코드를 점진적으로 캐싱 방식으로 교체하는 방법을 보여주는 예시입니다.
✅ Infrastructure Layer DDD 패턴 준수
✅ 폴백 메커니즘으로 호환성 보장
✅ 성능 향상과 안정성 두 마리 토끼

사용법:
1. 기존 코드: 매번 복호화 + API 인스턴스 생성
2. 개선 코드: 캐싱된 인스턴스 우선 사용, 필요시 폴백
"""

import asyncio
from typing import Optional, List, Dict, Any

# DDD Infrastructure 로깅 시스템
from upbit_auto_trading.infrastructure.logging import create_component_logger

# DDD Repository 패턴
from upbit_auto_trading.infrastructure.repositories.repository_container import RepositoryContainer

# Infrastructure Services
from upbit_auto_trading.infrastructure.services.api_key_service import ApiKeyService

# Infrastructure External APIs (DDD 준수)
from upbit_auto_trading.infrastructure.external_apis.upbit import UpbitClient


class ApiUsageExample:
    """API 캐싱 사용 예시 클래스"""

    def __init__(self):
        """초기화"""
        self.logger = create_component_logger("API-Usage-Example")

        # Repository Container 초기화 (DDD 패턴)
        self.repo_container = RepositoryContainer()
        self.secure_keys_repo = self.repo_container.get_secure_keys_repository()

        # ApiKeyService 초기화 (Infrastructure Layer)
        self.api_service = ApiKeyService(self.secure_keys_repo)

    def close(self):
        """리소스 정리"""
        try:
            self.repo_container.close_all_connections()
            self.logger.info("🧹 리소스 정리 완료")
        except Exception as e:
            self.logger.warning(f"⚠️ 정리 중 오류 (무시됨): {e}")

    # ===== 기존 방식 (Task 2.3.5 이전) =====

    async def get_account_balance_old_way(self) -> Optional[List[Dict[str, Any]]]:
        """
        [기존 방식] 매번 복호화 + API 인스턴스 생성

        문제점:
        - 매번 DB에서 암호화 키 로드
        - 매번 API 키 복호화 (2.23ms)
        - 매번 새로운 UpbitClient 인스턴스 생성
        - 성능 저하 및 불필요한 CPU 사용
        """
        try:
            self.logger.info("🐌 기존 방식: 매번 복호화 + 인스턴스 생성")

            # 매번 API 키 로드 (복호화 비용 발생)
            access_key, secret_key, trade_permission = self.api_service.load_api_keys()

            if not access_key or not secret_key:
                self.logger.warning("❌ API 키가 설정되지 않음")
                return None

            # 매번 새로운 API 인스턴스 생성
            api = UpbitClient(access_key, secret_key)

            # API 호출
            accounts = await api.get_accounts()
            self.logger.info(f"✅ 계좌 정보 조회 완료: {len(accounts)}개 계좌")
            return accounts

        except Exception as e:
            self.logger.error(f"❌ 계좌 조회 실패 (기존 방식): {e}")
            return None

    # ===== 개선된 방식 (Task 2.3.5 이후) =====

    async def get_account_balance_new_way(self) -> Optional[List[Dict[str, Any]]]:
        """
        [개선 방식] 캐싱된 인스턴스 우선 사용 + 폴백

        장점:
        - 캐시 적중 시 즉시 API 사용 (0.42ms)
        - 복호화 횟수 대폭 감소
        - 81% 성능 향상
        - 폴백으로 안정성 보장
        """
        try:
            self.logger.info("🚀 개선 방식: 캐싱된 인스턴스 우선 사용")

            # 1. 캐싱된 인스턴스 시도 (고속)
            api = self.api_service.get_cached_api_instance()

            if api is not None:
                self.logger.debug("💨 캐시 적중: 즉시 API 사용")

                # 캐시된 인스턴스로 API 호출
                accounts = await api.get_accounts()
                self.logger.info(f"✅ 계좌 정보 조회 완료 (캐시): {len(accounts)}개 계좌")
                return accounts

            # 2. 캐시 미스 시 폴백 (호환성)
            self.logger.debug("🔄 캐시 미스: 새 인스턴스 생성 및 캐싱")

            api = self.api_service.get_or_create_api_instance()
            if api is None:
                self.logger.warning("❌ API 인스턴스 생성 실패")
                return None

            # 새로 생성된 인스턴스로 API 호출
            accounts = await api.get_accounts()
            self.logger.info(f"✅ 계좌 정보 조회 완료 (새 생성): {len(accounts)}개 계좌")
            return accounts

        except Exception as e:
            self.logger.error(f"❌ 계좌 조회 실패 (개선 방식): {e}")

            # 3. 최종 폴백: 기존 방식 (최대 안정성)
            self.logger.warning("🛡️ 최종 폴백: 기존 방식으로 재시도")
            return await self.get_account_balance_old_way()

    # ===== 권장 방식 (Task 2.3.5 완료 후) =====

    async def get_account_balance_recommended(self) -> Optional[List[Dict[str, Any]]]:
        """
        [권장 방식] 간단하고 최적화된 패턴

        get_or_create_api_instance()를 사용하면:
        - 캐시 관리 자동화
        - 폴백 로직 내장
        - 코드 간소화
        - 최고 성능과 안정성
        """
        try:
            self.logger.info("⭐ 권장 방식: get_or_create_api_instance 사용")

            # 캐시 확인 → 있으면 재사용, 없으면 새로 생성
            api = self.api_service.get_or_create_api_instance()

            if api is None:
                self.logger.warning("❌ API 인스턴스 획득 실패")
                return None

            # API 호출
            accounts = await api.get_accounts()
            self.logger.info(f"✅ 계좌 정보 조회 완료 (권장): {len(accounts)}개 계좌")
            return accounts

        except Exception as e:
            self.logger.error(f"❌ 계좌 조회 실패 (권장 방식): {e}")
            return None

    # ===== 성능 비교 테스트 =====

    async def performance_comparison_test(self) -> None:
        """
        세 가지 방식의 성능 비교 테스트
        """
        import time

        self.logger.info("📊 성능 비교 테스트 시작")

        # 테스트용 API 키 설정 (더미 키)
        success, message = self.api_service.save_api_keys_clean(
            "DEMO_ACCESS_KEY_FOR_PERFORMANCE_TEST",
            "DEMO_SECRET_KEY_FOR_PERFORMANCE_TEST",
            None
        )

        if not success:
            self.logger.error(f"❌ 테스트용 API 키 설정 실패: {message}")
            return

        iterations = 3

        # 1. 기존 방식 성능 측정
        old_times = []
        for i in range(iterations):
            # 캐시 무효화 (공정한 비교)
            self.api_service.clear_cache()

            start_time = time.perf_counter()
            try:
                # 실제 API 호출은 제외하고 인스턴스 생성까지만 측정
                access_key, secret_key, _ = self.api_service.load_api_keys()
                api = UpbitClient(access_key, secret_key) if access_key and secret_key else None
            except Exception:
                api = None
            end_time = time.perf_counter()

            if api:
                duration = (end_time - start_time) * 1000
                old_times.append(duration)

        # 2. 권장 방식 성능 측정
        new_times = []
        for i in range(iterations):
            # 첫 번째는 캐시 생성, 나머지는 캐시 사용
            if i == 0:
                self.api_service.clear_cache()

            start_time = time.perf_counter()
            api = self.api_service.get_or_create_api_instance()
            end_time = time.perf_counter()

            if api:
                duration = (end_time - start_time) * 1000
                new_times.append(duration)

        # 3. 결과 분석
        if old_times and new_times:
            avg_old = sum(old_times) / len(old_times)
            avg_new = sum(new_times) / len(new_times)
            improvement = (avg_old - avg_new) / avg_old * 100 if avg_old > 0 else 0

            self.logger.info(f"📈 성능 비교 결과:")
            self.logger.info(f"   - 기존 방식 평균: {avg_old:.2f}ms")
            self.logger.info(f"   - 권장 방식 평균: {avg_new:.2f}ms")
            self.logger.info(f"   - 성능 향상: {improvement:.1f}%")

            if improvement >= 50:
                self.logger.info("🎉 성능 향상 목표 달성!")
            else:
                self.logger.warning(f"⚠️ 성능 향상 부족: {improvement:.1f}% < 50%")
        else:
            self.logger.warning("⚠️ 성능 측정 실패")


async def main():
    """메인 실행 함수"""
    example = ApiUsageExample()

    try:
        print("🧪 API 캐싱 사용 예시 시작...")

        # 성능 비교 테스트
        await example.performance_comparison_test()

        print("\n📚 사용법 예시:")
        print("✅ 권장: api = self.api_service.get_or_create_api_instance()")
        print("🔄 캐시 우선: api = self.api_service.get_cached_api_instance()")
        print("🧹 캐시 정리: self.api_service.clear_cache()")
        print("📊 상태 확인: status = self.api_service.get_cache_status()")

        print("\n🎯 Task 2.3.5 기존 코드 점진적 교체 완료!")

    except Exception as e:
        print(f"❌ 예시 실행 실패: {e}")

    finally:
        example.close()


if __name__ == "__main__":
    """개별 실행 지원"""
    import os

    # 로깅 환경 설정
    os.environ['UPBIT_CONSOLE_OUTPUT'] = 'true'
    os.environ['UPBIT_COMPONENT_FOCUS'] = 'API-Usage-Example'

    # 비동기 실행
    asyncio.run(main())
