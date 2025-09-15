#!/usr/bin/env python3
"""
REST Public 그룹 RPM 제한 적용 여부 확인 스크립트
"""

import asyncio
from upbit_auto_trading.infrastructure.external_apis.upbit.rate_limiter.upbit_rate_limiter import UnifiedUpbitRateLimiter
from upbit_auto_trading.infrastructure.external_apis.upbit.rate_limiter.upbit_rate_limiter_types import UpbitRateLimitGroup


async def test_rest_public_group():
    """REST Public 그룹의 RPM 제한 적용 여부 확인"""
    print("🔍 REST Public 그룹 RPM 제한 적용 확인")
    print("=" * 50)

    limiter = UnifiedUpbitRateLimiter()
    group = UpbitRateLimitGroup.REST_PUBLIC

    # 현재 설정 확인
    config = limiter.group_configs[group]
    print(f"📊 REST Public 그룹 설정:")
    print(f"  - RPS: {config.rps}")
    print(f"  - 버스트: {config.burst_capacity}")
    print(f"  - RPM: {config.rpm}")
    print(f"  - 이중 제한: {config.enable_dual_limit}")
    print()

    # TAT 딕셔너리 상태 확인
    print("🗂️  TAT 딕셔너리 상태:")
    print(f"  - group_tats: {list(limiter.group_tats.keys())}")
    print(f"  - group_tats_minute: {list(limiter.group_tats_minute.keys())}")
    print()

    # REST Public 그룹의 TAT 상태
    print(f"🎯 {group.value} TAT 상태:")
    print(f"  - 초단위 TAT: {limiter.group_tats.get(group, 'NOT_FOUND')}")
    print(f"  - 분단위 TAT: {limiter.group_tats_minute.get(group, 'NOT_FOUND')}")
    print()

    # 상태 보고 확인
    status = limiter.get_comprehensive_status()
    rest_public_status = status['groups'].get('rest_public', {})
    config_info = rest_public_status.get('config', {})

    print("📈 상태 보고:")
    print(f"  - dual_limit_enabled: {config_info.get('dual_limit_enabled', 'NOT_FOUND')}")
    if config_info.get('dual_limit_enabled'):
        print(f"  - tat_second: {config_info.get('tat_second', 'NOT_FOUND')}")
        print(f"  - tat_minute: {config_info.get('tat_minute', 'NOT_FOUND')}")
    else:
        print(f"  - tat: {config_info.get('tat', 'NOT_FOUND')}")

    print("\n✅ REST Public 그룹 분석 완료")


async def test_websocket_group():
    """비교를 위한 웹소켓 그룹 확인"""
    print("\n🔍 Websocket 그룹 RPM 제한 적용 확인 (비교용)")
    print("=" * 50)

    limiter = UnifiedUpbitRateLimiter()
    group = UpbitRateLimitGroup.WEBSOCKET

    # 현재 설정 확인
    config = limiter.group_configs[group]
    print(f"📊 Websocket 그룹 설정:")
    print(f"  - RPS: {config.rps}")
    print(f"  - 버스트: {config.burst_capacity}")
    print(f"  - RPM: {config.rpm}")
    print(f"  - 이중 제한: {config.enable_dual_limit}")
    print()

    # TAT 상태 확인
    print(f"🎯 {group.value} TAT 상태:")
    print(f"  - 초단위 TAT: {limiter.group_tats.get(group, 'NOT_FOUND')}")
    print(f"  - 분단위 TAT: {limiter.group_tats_minute.get(group, 'NOT_FOUND')}")
    print()

    # 상태 보고 확인
    status = limiter.get_comprehensive_status()
    websocket_status = status['groups'].get('websocket', {})
    config_info = websocket_status.get('config', {})

    print("📈 상태 보고:")
    print(f"  - dual_limit_enabled: {config_info.get('dual_limit_enabled', 'NOT_FOUND')}")
    if config_info.get('dual_limit_enabled'):
        print(f"  - tat_second: {config_info.get('tat_second', 'NOT_FOUND')}")
        print(f"  - tat_minute: {config_info.get('tat_minute', 'NOT_FOUND')}")
    else:
        print(f"  - tat: {config_info.get('tat', 'NOT_FOUND')}")

    print("\n✅ Websocket 그룹 분석 완료")


if __name__ == "__main__":
    asyncio.run(test_rest_public_group())
    asyncio.run(test_websocket_group())
