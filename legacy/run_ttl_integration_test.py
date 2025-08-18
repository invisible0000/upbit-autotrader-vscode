"""
TTL 통합 테스트 실행 스크립트
WebSocket + API 동시 고빈도 테스트로 TTL 갱신 시점 문제 감지
"""

import asyncio
from tests.ttl_integration.ttl_integration_tester import run_ttl_integration_test_high_frequency


async def main():
    print('🔥 TTL 통합 테스트 - WebSocket + API 동시 실행')
    print('=' * 70)
    print('📋 테스트 목표:')
    print('   🎯 WebSocket과 API가 동시에 잘 작동하는지 확인')
    print('   🔑 TTL 갱신 시점에 키 문제가 발생하는지 감지')
    print('   ⚡ 0.5초마다 API 호출로 TTL 갱신 강제 유발')
    print('   📡 0.1초마다 WebSocket 상태 체크')
    print()
    print('🕒 예상 동작:')
    print('   - API 호출: 매 0.5초 (계좌 정보 조회)')
    print('   - WebSocket: 0.1초마다 연결 상태 체크')
    print('   - TTL 갱신: 5분마다 (300초 간격)')
    print('   - 상태 리포트: 15초마다')
    print('=' * 70)
    print()

    try:
        print('⚡ 30분 고빈도 TTL 통합 테스트 시작...')
        print('💡 WebSocket과 API가 동시에 실행됩니다')
        print('💡 Ctrl+C로 언제든 중단 가능합니다')
        print()

        metrics = await run_ttl_integration_test_high_frequency()

        print()
        print('🎯 TTL 통합 테스트 최종 요약:')
        print('=' * 70)
        duration_minutes = (metrics.end_time - metrics.start_time).total_seconds() / 60
        api_success_rate = 100 * metrics.api_calls_success / max(1, metrics.api_calls_total)
        ws_uptime_rate = 100 * (1 - metrics.websocket_disconnections / max(1, metrics.websocket_connections))

        print(f'⏱️  테스트 시간: {duration_minutes:.1f}분')
        print(f'📡 WebSocket 가동률: {ws_uptime_rate:.1f}%')
        print(f'🔗 API 성공률: {api_success_rate:.1f}% ({metrics.api_calls_success}/{metrics.api_calls_total})')
        print(f'🔑 TTL 갱신 감지: {metrics.ttl_refresh_detected}회')
        print(f'❌ API 인증 오류: {metrics.api_auth_errors}회')
        print(f'⚠️  총 오류: {len(metrics.error_details)}개')

        print()
        if metrics.api_auth_errors == 0 and metrics.websocket_errors == 0:
            print('🎉 테스트 성공! WebSocket + API 동시 운영이 안정적입니다!')
            if metrics.ttl_refresh_detected > 0:
                print('✅ TTL 갱신도 정상적으로 감지되었습니다!')
            else:
                print('ℹ️  TTL 갱신은 감지되지 않았지만 시스템은 안정적입니다.')
        else:
            print('⚠️  일부 문제가 감지되었습니다:')
            if metrics.api_auth_errors > 0:
                print(f'   🔑 API 인증 오류 {metrics.api_auth_errors}회 - TTL 갱신 관련 문제 가능성')
            if metrics.websocket_errors > 0:
                print(f'   📡 WebSocket 오류 {metrics.websocket_errors}회 - 연결 안정성 문제')

    except KeyboardInterrupt:
        print()
        print('⏹️ 사용자에 의해 테스트 중단됨')
        print('💡 부분 결과도 유효한 분석 데이터입니다')
    except Exception as e:
        print(f'❌ 테스트 중 오류: {e}')
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
