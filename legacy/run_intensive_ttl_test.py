"""
집중 TTL 갱신 테스트 - 10초마다 상태 체크
TTL 갱신 시점에서 통신 장애 발생 여부 감지
"""

import asyncio
from test_websocket_stable import run_intensive_ttl_test

async def main():
    print('🔥 집중 TTL 갱신 테스트 시작 (1시간)')
    print('=' * 60)
    print('📋 테스트 목표:')
    print('   🎯 TTL 갱신 시점 통신 장애 감지 (API 키 TTL: 5분)')
    print('   📊 10초마다 연결 상태 체크 (고빈도 모니터링)')
    print('   🔍 토큰 갱신 전후 연결 끊김 여부 확인')
    print('   ⚡ 즉각적인 문제 감지 및 리포트')
    print()
    print('🕒 예상 TTL 갱신 시점: 5분, 10분, 15분... (300초 간격)')
    print('📈 상태 체크 빈도: 매 10초 (갱신 시점 놓치지 않음)')
    print('=' * 60)
    print()

    try:
        print('⏰ 테스트 시작... (Ctrl+C로 중단 가능)')
        print()

        metrics = await run_intensive_ttl_test()

        print()
        print('🎯 집중 TTL 테스트 최종 결과:')
        print('=' * 60)
        success_rate = 100 * metrics.successful_connections / max(1, metrics.connection_attempts)
        duration_minutes = metrics.connection_duration_seconds / 60

        print(f'⏱️  총 지속시간: {duration_minutes:.1f}분')
        print(f'🔌 연결 성공률: {success_rate:.1f}% ({metrics.successful_connections}/{metrics.connection_attempts})')
        print(f'🔄 재연결 횟수: {metrics.reconnection_attempts}')
        print(f'🔑 토큰 갱신 횟수: {metrics.token_refresh_count}')
        print(f'📨 수신 메시지: {metrics.messages_received}')
        print(f'❌ 오류 수: {metrics.error_count}')

        print()
        print('🔍 TTL 갱신 분석:')
        expected_refreshes = int(duration_minutes // 5)  # 5분마다 갱신 예상

        if metrics.token_refresh_count > 0:
            print(f'✅ TTL 갱신 감지됨: {metrics.token_refresh_count}회')
            print(f'📊 예상 갱신 횟수: {expected_refreshes}회 (5분 간격)')

            if metrics.error_count == 0:
                print('🎉 TTL 갱신 시 통신 장애 없음 - 시스템 안정!')
            else:
                print('⚠️  TTL 갱신 시 일부 오류 발생 - 로그 확인 필요')

        else:
            if duration_minutes < 5:
                print('ℹ️  테스트 시간이 짧아 TTL 갱신이 발생하지 않음')
            else:
                print('⚠️  예상된 TTL 갱신이 감지되지 않음 - 확인 필요')

        print()
        if metrics.reconnection_attempts > 0:
            print(f'🔄 재연결 발생: {metrics.reconnection_attempts}회 - 네트워크 불안정 또는 TTL 갱신 영향')
        else:
            print('🟢 재연결 없음 - 연결 안정성 우수')

    except KeyboardInterrupt:
        print()
        print('⏹️ 사용자에 의해 테스트 중단됨')
        print('💡 부분 결과도 유효한 데이터입니다')
    except Exception as e:
        print(f'❌ 테스트 중 오류: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
