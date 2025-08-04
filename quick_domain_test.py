#!/usr/bin/env python3
"""
도메인 이벤트 시스템 빠른 검증 스크립트
"""

print('🔍 도메인 이벤트 클래스 상속 및 인스턴스 생성 검증...')
print()

try:
    from upbit_auto_trading.domain.events.strategy_events import StrategyCreated, StrategyUpdated
    from upbit_auto_trading.domain.events.base_domain_event import DomainEvent

    # 1. 상속 관계 검증
    print('1️⃣ DomainEvent 상속 관계 검증:')
    print(f'   StrategyCreated가 DomainEvent 상속: {issubclass(StrategyCreated, DomainEvent)}')
    print(f'   StrategyUpdated가 DomainEvent 상속: {issubclass(StrategyUpdated, DomainEvent)}')
    print()

    # 2. 인스턴스 생성 테스트
    print('2️⃣ 이벤트 인스턴스 생성 테스트:')
    created_event = StrategyCreated(
        strategy_id='TEST_STRATEGY_001',
        strategy_name='테스트 전략'
    )
    print(f'   ✅ StrategyCreated 인스턴스 생성 성공')
    print(f'   - event_type: {created_event.event_type}')
    print(f'   - aggregate_id: {created_event.aggregate_id}')
    print(f'   - strategy_name: {created_event.strategy_name}')
    print()

    # 3. 직렬화 테스트
    print('3️⃣ 이벤트 직렬화 테스트:')
    event_dict = created_event.to_dict()
    print(f'   ✅ to_dict() 직렬화 성공')
    print(f'   - 포함된 키: {list(event_dict.keys())}')
    print()

    print('✅ 모든 검증 완료! 🎉')

except Exception as e:
    print(f'❌ 검증 실패: {e}')
    import traceback
    print(traceback.format_exc())
