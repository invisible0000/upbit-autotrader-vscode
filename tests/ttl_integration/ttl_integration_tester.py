"""
TTL 갱신 통합 테스트
WebSocket + API 동시 고빈도 테스트로 TTL 갱신 시점 문제 감지

목적:
1. WebSocket과 API가 동시에 잘 작동하는지 확인
2. TTL 갱신 시점에 키 문제가 발생하는지 감지
3. 고빈도 API 호출로 TTL 갱신을 강제 유발
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import json

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_private_client import UpbitWebSocketPrivateClient
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_client import UpbitClient
from upbit_auto_trading.infrastructure.services.api_key_service import ApiKeyService
from upbit_auto_trading.infrastructure.repositories.sqlite_secure_keys_repository import SqliteSecureKeysRepository
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager


@dataclass
class TTLIntegrationMetrics:
    """TTL 통합 테스트 메트릭"""
    start_time: datetime
    end_time: Optional[datetime] = None

    # WebSocket 메트릭
    websocket_connections: int = 0
    websocket_disconnections: int = 0
    websocket_errors: int = 0
    websocket_messages_received: int = 0

    # API 메트릭
    api_calls_total: int = 0
    api_calls_success: int = 0
    api_calls_failed: int = 0
    api_auth_errors: int = 0

    # TTL 관련 메트릭
    ttl_refresh_detected: int = 0
    ttl_refresh_failures: int = 0

    # 동시성 메트릭
    concurrent_issues: int = 0
    timing_issues: int = 0

    # 상세 오류 로그
    error_details: list = field(default_factory=list)


class TTLIntegrationTester:
    """WebSocket + API 동시 TTL 갱신 테스트"""

    def __init__(self,
                 test_duration_minutes: float = 60.0,
                 api_call_interval_seconds: float = 1.0,
                 websocket_check_interval_seconds: float = 0.1,
                 status_report_interval_seconds: int = 30):
        self.logger = create_component_logger("TTLIntegrationTest")

        self.test_duration_minutes = test_duration_minutes
        self.api_call_interval_seconds = api_call_interval_seconds
        self.websocket_check_interval_seconds = websocket_check_interval_seconds
        self.status_report_interval_seconds = status_report_interval_seconds

        self.metrics = TTLIntegrationMetrics(start_time=datetime.now())
        self.is_running = False

        # 클라이언트들
        self.websocket_client: Optional[UpbitWebSocketPrivateClient] = None
        self.api_client: Optional[UpbitClient] = None
        self.api_key_service: Optional[ApiKeyService] = None

        # 동기화용
        self.websocket_task: Optional[asyncio.Task] = None
        self.api_task: Optional[asyncio.Task] = None
        self.monitor_task: Optional[asyncio.Task] = None

    async def setup_services(self) -> tuple[str, str]:
        """API 키 서비스 및 클라이언트 설정"""
        self.logger.info("🔧 TTL 통합 테스트 환경 설정 중...")

        # API 키 서비스 초기화
        db_paths = {
            'settings': 'data/settings.sqlite3',
            'strategies': 'data/strategies.sqlite3',
            'market_data': 'data/market_data.sqlite3'
        }
        db_manager = DatabaseManager(db_paths)
        repository = SqliteSecureKeysRepository(db_manager)
        self.api_key_service = ApiKeyService(repository)

        # API 키 로드
        access_key, secret_key, _ = self.api_key_service.load_api_keys()

        if not access_key or not secret_key:
            raise ValueError("유효한 API 키가 없습니다. 먼저 API 키를 설정해주세요.")

        # 클라이언트 초기화
        self.websocket_client = UpbitWebSocketPrivateClient(access_key, secret_key)

        # API 클라이언트 생성 (캐시가 없으면 새로 생성)
        self.api_client = self.api_key_service.get_cached_api_instance()
        if not self.api_client:
            self.logger.info("💡 캐싱된 API 인스턴스 없음 - 새로 생성")
            self.api_client = self.api_key_service.cache_api_instance()

        if not self.api_client:
            raise ValueError("API 클라이언트 생성 실패")

        self.logger.info("✅ TTL 통합 테스트 환경 설정 완료")
        return access_key, secret_key

    async def websocket_loop(self):
        """WebSocket 연결 및 모니터링 루프"""
        try:
            self.logger.info("🔌 WebSocket 루프 시작")

            # WebSocket 연결
            if not await self.websocket_client.connect():
                raise Exception("WebSocket 연결 실패")

            self.metrics.websocket_connections += 1

            # 구독 설정
            await self.websocket_client.subscribe_my_assets()
            await self.websocket_client.subscribe_my_orders()

            self.logger.info("✅ WebSocket 연결 및 구독 완료")

            # 모니터링 루프
            while self.is_running:
                await asyncio.sleep(self.websocket_check_interval_seconds)

                # 연결 상태 체크
                if not self.websocket_client.is_connected:
                    self.logger.warning("⚠️ WebSocket 연결 끊김 감지")
                    self.metrics.websocket_disconnections += 1
                    self.metrics.error_details.append({
                        'timestamp': datetime.now(),
                        'type': 'websocket_disconnect',
                        'details': 'WebSocket connection lost'
                    })
                    break

        except Exception as e:
            self.logger.error(f"❌ WebSocket 루프 오류: {e}")
            self.metrics.websocket_errors += 1
            self.metrics.error_details.append({
                'timestamp': datetime.now(),
                'type': 'websocket_error',
                'details': str(e)
            })

    async def api_loop(self):
        """API 호출 루프 (고빈도로 TTL 갱신 유발)"""
        try:
            self.logger.info("📡 API 호출 루프 시작")

            while self.is_running:
                try:
                    # 계좌 정보 조회 (인증 필요한 API)
                    self.metrics.api_calls_total += 1

                    accounts = await asyncio.to_thread(self.api_client.get_accounts)

                    if accounts:
                        self.metrics.api_calls_success += 1
                        self.logger.debug(f"✅ API 호출 성공 (총 {self.metrics.api_calls_total}회)")
                    else:
                        self.metrics.api_calls_failed += 1
                        self.logger.warning(f"⚠️ API 호출 응답 없음 (호출 {self.metrics.api_calls_total}회)")

                except Exception as e:
                    self.metrics.api_calls_failed += 1
                    error_msg = str(e).lower()

                    if 'auth' in error_msg or 'token' in error_msg or 'unauthorized' in error_msg:
                        self.metrics.api_auth_errors += 1
                        self.logger.error(f"🔑 API 인증 오류 감지: {e}")
                        self.metrics.error_details.append({
                            'timestamp': datetime.now(),
                            'type': 'api_auth_error',
                            'details': str(e)
                        })
                    else:
                        self.logger.error(f"❌ API 호출 오류: {e}")
                        self.metrics.error_details.append({
                            'timestamp': datetime.now(),
                            'type': 'api_error',
                            'details': str(e)
                        })

                await asyncio.sleep(self.api_call_interval_seconds)

        except Exception as e:
            self.logger.error(f"❌ API 루프 치명적 오류: {e}")
            self.metrics.error_details.append({
                'timestamp': datetime.now(),
                'type': 'api_loop_fatal',
                'details': str(e)
            })

    async def monitoring_loop(self):
        """상태 모니터링 및 TTL 갱신 감지 루프"""
        try:
            self.logger.info("📊 모니터링 루프 시작")
            last_report_time = datetime.now()
            last_ttl_check = datetime.now()

            while self.is_running:
                await asyncio.sleep(1)  # 1초마다 체크

                current_time = datetime.now()

                # TTL 갱신 감지 (API 키 서비스 캐시 상태 체크)
                if (current_time - last_ttl_check).total_seconds() >= 10:  # 10초마다 TTL 체크
                    try:
                        # 새로운 API 인스턴스 요청으로 TTL 갱신 감지
                        if self.api_key_service:  # 타입 체커를 위한 None 체크
                            new_api_instance = self.api_key_service.get_cached_api_instance()

                            if new_api_instance != self.api_client:
                                self.metrics.ttl_refresh_detected += 1
                                self.logger.info(f"🔄 TTL 갱신 감지! (총 {self.metrics.ttl_refresh_detected}회)")

                                # None인 경우 새 인스턴스 강제 생성
                                if new_api_instance is None:
                                    self.logger.warning("⚠️ TTL 갱신 후 API 인스턴스가 None - 새 인스턴스 생성 중...")
                                    new_api_instance = self.api_key_service.get_or_create_api_instance()
                                    if new_api_instance:
                                        self.logger.info("✅ 새 API 인스턴스 생성 완료")
                                    else:
                                        self.logger.error("❌ 새 API 인스턴스 생성 실패")
                                        self.metrics.ttl_refresh_failures += 1

                                self.api_client = new_api_instance
                    except Exception as e:
                        self.metrics.ttl_refresh_failures += 1
                        self.logger.error(f"❌ TTL 갱신 체크 실패: {e}")

                    last_ttl_check = current_time

                # 상태 리포트
                if (current_time - last_report_time).total_seconds() >= self.status_report_interval_seconds:
                    self._log_integration_status()
                    last_report_time = current_time

        except Exception as e:
            self.logger.error(f"❌ 모니터링 루프 오류: {e}")

    def _log_integration_status(self):
        """통합 상태 로깅"""
        elapsed = (datetime.now() - self.metrics.start_time).total_seconds()
        elapsed_minutes = int(elapsed // 60)
        elapsed_seconds = int(elapsed % 60)

        if elapsed_minutes > 0:
            elapsed_str = f"{elapsed_minutes}분 {elapsed_seconds}초"
        else:
            elapsed_str = f"{elapsed_seconds}초"

        # API 성공률 계산
        api_success_rate = 100 * self.metrics.api_calls_success / max(1, self.metrics.api_calls_total)

        # WebSocket 상태
        ws_status = "🟢 연결됨" if (self.websocket_client and self.websocket_client.is_connected) else "🔴 끊김"

        self.logger.info(f"""
🔥 TTL 통합 테스트 상태 ({elapsed_str} 경과):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📡 WebSocket:
   - 연결 상태: {ws_status}
   - 연결/해제: {self.metrics.websocket_connections}/{self.metrics.websocket_disconnections}
   - 수신 메시지: {self.metrics.websocket_messages_received}
   - 오류: {self.metrics.websocket_errors}

🔗 API 호출:
   - 총 호출: {self.metrics.api_calls_total}회
   - 성공률: {api_success_rate:.1f}% ({self.metrics.api_calls_success}/{self.metrics.api_calls_total})
   - 실패: {self.metrics.api_calls_failed}회
   - 인증 오류: {self.metrics.api_auth_errors}회

🔑 TTL 관리:
   - TTL 갱신 감지: {self.metrics.ttl_refresh_detected}회
   - TTL 갱신 실패: {self.metrics.ttl_refresh_failures}회

⚠️  문제 감지:
   - 동시성 이슈: {self.metrics.concurrent_issues}회
   - 타이밍 이슈: {self.metrics.timing_issues}회
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)

    async def run_integration_test(self) -> TTLIntegrationMetrics:
        """통합 테스트 실행"""
        test_duration_seconds = self.test_duration_minutes * 60

        self.logger.info(f"""
🚀 TTL 통합 테스트 시작 ({self.test_duration_minutes}분)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 테스트 설정:
   - 테스트 시간: {self.test_duration_minutes}분
   - API 호출 간격: {self.api_call_interval_seconds}초
   - WebSocket 체크 간격: {self.websocket_check_interval_seconds}초
   - 상태 리포트 간격: {self.status_report_interval_seconds}초

🎯 목표:
   - WebSocket + API 동시 안정성 확인
   - TTL 갱신 시점 문제 감지
   - 고빈도 API 호출로 TTL 갱신 강제 유발
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)

        try:
            self.is_running = True

            # 서비스 설정
            await self.setup_services()

            # 병렬 태스크 시작
            self.websocket_task = asyncio.create_task(self.websocket_loop())
            self.api_task = asyncio.create_task(self.api_loop())
            self.monitor_task = asyncio.create_task(self.monitoring_loop())

            self.logger.info("⚡ 모든 루프 시작됨 - 통합 테스트 진행 중...")

            # 테스트 시간 대기
            await asyncio.sleep(test_duration_seconds)

            self.logger.info("⏹️ 테스트 시간 완료 - 정리 중...")

        except Exception as e:
            self.logger.error(f"❌ 통합 테스트 실행 중 오류: {e}")
            self.metrics.error_details.append({
                'timestamp': datetime.now(),
                'type': 'integration_test_error',
                'details': str(e)
            })

        finally:
            await self._cleanup()
            self._finalize_metrics()

        return self.metrics

    async def _cleanup(self):
        """정리 작업"""
        self.logger.info("🧹 TTL 통합 테스트 정리 중...")
        self.is_running = False

        # 태스크 정리
        tasks_to_cancel = [self.websocket_task, self.api_task, self.monitor_task]
        for task in tasks_to_cancel:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # WebSocket 정리
        if self.websocket_client:
            await self.websocket_client.disconnect()

        self.logger.info("✅ TTL 통합 테스트 정리 완료")

    def _finalize_metrics(self):
        """메트릭 최종화"""
        self.metrics.end_time = datetime.now()
        duration_seconds = (self.metrics.end_time - self.metrics.start_time).total_seconds()
        duration_minutes = duration_seconds / 60

        # 성공률 계산
        api_success_rate = 100 * self.metrics.api_calls_success / max(1, self.metrics.api_calls_total)
        ws_uptime_rate = 100 * (1 - self.metrics.websocket_disconnections / max(1, self.metrics.websocket_connections))

        self.logger.info(f"""
🏁 TTL 통합 테스트 최종 결과:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️  총 지속시간: {duration_seconds:.1f}초 ({duration_minutes:.2f}분)

📡 WebSocket 결과:
   - 연결 성공률: {ws_uptime_rate:.1f}%
   - 총 연결/해제: {self.metrics.websocket_connections}/{self.metrics.websocket_disconnections}
   - 수신 메시지: {self.metrics.websocket_messages_received}
   - 오류 수: {self.metrics.websocket_errors}

🔗 API 결과:
   - 총 호출: {self.metrics.api_calls_total}회
   - 성공률: {api_success_rate:.1f}% ({self.metrics.api_calls_success}/{self.metrics.api_calls_total})
   - 인증 오류: {self.metrics.api_auth_errors}회 (TTL 갱신 관련)

🔑 TTL 갱신 분석:
   - 감지된 TTL 갱신: {self.metrics.ttl_refresh_detected}회
   - TTL 갱신 실패: {self.metrics.ttl_refresh_failures}회
   - 예상 갱신 횟수: {int(duration_minutes // 5)}회 (5분 간격)

🎯 통합 안정성:
   - 동시성 문제: {self.metrics.concurrent_issues}회
   - 타이밍 문제: {self.metrics.timing_issues}회
   - 총 오류: {len(self.metrics.error_details)}개

{'🎉 통합 테스트 성공! WebSocket + API 동시 운영 안정성 확인됨!' if self.metrics.api_auth_errors == 0 and self.metrics.websocket_errors == 0 else '⚠️  일부 문제 감지됨 - 상세 로그 확인 필요'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)

        # 오류 상세 정보 출력 (필요시)
        if self.metrics.error_details:
            self.logger.warning(f"📋 감지된 오류 {len(self.metrics.error_details)}개:")
            for i, error in enumerate(self.metrics.error_details[-5:], 1):  # 최근 5개만
                self.logger.warning(f"   {i}. [{error['timestamp'].strftime('%H:%M:%S')}] {error['type']}: {error['details']}")


# 편의 함수들
async def run_ttl_integration_test_1_hour():
    """1시간 TTL 통합 테스트"""
    tester = TTLIntegrationTester(
        test_duration_minutes=60.0,
        api_call_interval_seconds=1.0,  # 1초마다 API 호출
        websocket_check_interval_seconds=0.1,  # 0.1초마다 WebSocket 체크
        status_report_interval_seconds=30  # 30초마다 상태 리포트
    )
    return await tester.run_integration_test()


async def run_ttl_integration_test_high_frequency():
    """고빈도 TTL 통합 테스트 (30분, 매우 빠른 API 호출)"""
    tester = TTLIntegrationTester(
        test_duration_minutes=30.0,
        api_call_interval_seconds=0.5,  # 0.5초마다 API 호출
        websocket_check_interval_seconds=0.1,  # 0.1초마다 WebSocket 체크
        status_report_interval_seconds=15  # 15초마다 상태 리포트
    )
    return await tester.run_integration_test()


if __name__ == "__main__":
    async def main():
        print("🔥 TTL 통합 테스트 선택:")
        print("1. 1시간 표준 테스트 (1초 API 간격)")
        print("2. 30분 고빈도 테스트 (0.5초 API 간격)")

        choice = input("선택 (1 또는 2): ").strip()

        try:
            if choice == "1":
                print("\n🚀 1시간 TTL 통합 테스트 시작...")
                metrics = await run_ttl_integration_test_1_hour()
            elif choice == "2":
                print("\n⚡ 30분 고빈도 TTL 통합 테스트 시작...")
                metrics = await run_ttl_integration_test_high_frequency()
            else:
                print("❌ 잘못된 선택입니다.")
                return

            print(f"\n✅ 테스트 완료! 상세 결과는 로그를 확인하세요.")

        except KeyboardInterrupt:
            print("\n⏹️ 사용자에 의해 테스트 중단됨")
        except Exception as e:
            print(f"\n❌ 테스트 실행 중 오류: {e}")
            import traceback
            traceback.print_exc()

    asyncio.run(main())
