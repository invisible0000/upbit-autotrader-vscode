"""
초고빈도 TTL 갱신 테스트 - 0.1초마다 상태 체크
TTL 갱신 시점의 미세한 통신 장애도 감지
"""

import asyncio
from test_websocket_stable import run_ultra_high_frequency_test


async def main():
    print('⚡ 초고빈도 TTL 갱신 테스트 시작 (1시간)')
    print('=' * 70)
    print('📋 테스트 목표:')
    print('   🎯 TTL 갱신 시점 미세한 통신 장애 감지 (API 키 TTL: 5분)')
    print('   📊 0.1초마다 연결 상태 체크 (초고빈도 모니터링)')
    print('   🔍 토큰 갱신 전후 순간적 연결 끊김도 감지')
    print('   ⚡ 실시간 문제 감지 및 즉각 리포트')
    print()
    print('🕒 예상 TTL 갱신 시점: 5분, 10분, 15분... (300초 간격)')
    print('📈 상태 체크 빈도: 매 0.1초 (1시간 = 36,000회 체크)')
    print('⚠️  주의: 고빈도 체크로 인한 로그량 증가 예상')
    print('=' * 70)
    print()

    try:
        print('⏰ 초고빈도 테스트 시작... (Ctrl+C로 중단 가능)')
        print('💡 로그가 빠르게 스크롤될 수 있습니다')
        print()

        metrics = await run_ultra_high_frequency_test()

        print()
        print('🎯 초고빈도 TTL 테스트 최종 결과:')
        print('=' * 70)
        success_rate = 100 * metrics.successful_connections / max(1, metrics.connection_attempts)
        duration_minutes = metrics.connection_duration_seconds / 60
        total_checks = int(duration_minutes * 60 / 0.1)  # 0.1초마다 체크

        print(f'⏱️  총 지속시간: {duration_minutes:.1f}분')
        print(f'📊 총 상태 체크 횟수: {total_checks:,}회 (0.1초 간격)')
        print(f'🔌 연결 성공률: {success_rate:.1f}% ({metrics.successful_connections}/{metrics.connection_attempts})')
        print(f'🔄 재연결 횟수: {metrics.reconnection_attempts}')
        print(f'🔑 토큰 갱신 횟수: {metrics.token_refresh_count}')
        print(f'📨 수신 메시지: {metrics.messages_received}')
        print(f'❌ 오류 수: {metrics.error_count}')

        print()
        print('🔍 초고빈도 TTL 갱신 분석:')
        expected_refreshes = int(duration_minutes // 5)  # 5분마다 갱신 예상

        if metrics.token_refresh_count > 0:
            print(f'✅ TTL 갱신 감지됨: {metrics.token_refresh_count}회')
            print(f'📊 예상 갱신 횟수: {expected_refreshes}회 (5분 간격)')

            # 0.1초 단위 분석
            avg_checks_per_refresh = total_checks / max(1, metrics.token_refresh_count)
            print(f'📈 갱신당 평균 체크 횟수: {avg_checks_per_refresh:,.0f}회')

            if metrics.error_count == 0:
                print('🎉 TTL 갱신 시 통신 장애 없음 - 0.1초 단위에서도 완벽!')
            else:
                print('⚠️  TTL 갱신 시 일부 오류 발생 - 초고빈도에서 문제 감지됨')
                error_rate = (metrics.error_count / total_checks) * 100
                print(f'📊 오류율: {error_rate:.6f}% ({metrics.error_count}/{total_checks:,})')

        else:
            if duration_minutes < 5:
                print('ℹ️  테스트 시간이 짧아 TTL 갱신이 발생하지 않음')
            else:
                print('⚠️  예상된 TTL 갱신이 감지되지 않음 - 확인 필요')

        print()
        if metrics.reconnection_attempts > 0:
            print(f'🔄 재연결 발생: {metrics.reconnection_attempts}회')
            reconnection_rate = (metrics.reconnection_attempts / total_checks) * 100
            print(f'📊 재연결율: {reconnection_rate:.6f}% (초고빈도 기준)')
        else:
            print('🟢 재연결 없음 - 0.1초 단위에서도 연결 안정성 완벽!')

        print()
        print('📊 성능 통계:')
        print(f'⚡ 평균 체크 간격: 0.1초 (설정값)')
        print(f'📈 초당 체크 횟수: 10회')
        print(f'🔄 분당 체크 횟수: 600회')

    except KeyboardInterrupt:
        print()
        print('⏹️ 사용자에 의해 테스트 중단됨')
        print('💡 초고빈도 테스트 부분 결과도 유효한 데이터입니다')
    except Exception as e:
        print(f'❌ 테스트 중 오류: {e}')
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
