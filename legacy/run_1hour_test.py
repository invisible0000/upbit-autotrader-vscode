"""
1시간 Private WebSocket TTL 테스트 실행 스크립트
"""

import asyncio
from test_websocket_stable import run_1_hour_test

async def main():
    print('🚀 1시간 Private WebSocket TTL 테스트 시작')
    print('=' * 50)
    print('📋 테스트 목표:')
    print('   - API 키 TTL 만료/갱신 동작 검증')
    print('   - 장기간 연결 안정성 확인')
    print('   - 토큰 자동 갱신 메커니즘 테스트')
    print('   - 2분마다 상세 상태 리포트')
    print('=' * 50)
    print()

    try:
        metrics = await run_1_hour_test()

        print()
        print('🎯 1시간 테스트 최종 결과:')
        print('=' * 50)
        success_rate = 100 * metrics.successful_connections / max(1, metrics.connection_attempts)
        print(f'⏱️  총 지속시간: {metrics.connection_duration_seconds/60:.1f}분')
        print(f'🔌 연결 성공률: {success_rate:.1f}%')
        print(f'🔄 재연결 횟수: {metrics.reconnection_attempts}')
        print(f'🔑 토큰 갱신 횟수: {metrics.token_refresh_count}')
        print(f'📨 수신 메시지: {metrics.messages_received}')
        print(f'❌ 오류 수: {metrics.error_count}')

        if metrics.token_refresh_count > 0:
            print()
            print('✅ API 키 TTL 갱신이 정상 작동했습니다!')
        else:
            print()
            print('ℹ️  TTL 갱신이 필요하지 않았거나 아직 갱신 시점이 아닙니다.')

    except KeyboardInterrupt:
        print()
        print('⏹️ 사용자에 의해 테스트 중단됨')
    except Exception as e:
        print(f'❌ 테스트 중 오류: {e}')

if __name__ == "__main__":
    asyncio.run(main())
