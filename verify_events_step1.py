print('🔍 도메인 이벤트 클래스 구현 검증')
print('=' * 50)

# 모든 이벤트 클래스 import 테스트
try:
    from upbit_auto_trading.domain.events import DomainEvent
    from upbit_auto_trading.domain.events.strategy_events import StrategyCreated, StrategyValidated
    from upbit_auto_trading.domain.events.trigger_events import TriggerCreated, TriggerEvaluationStarted
    from upbit_auto_trading.domain.events.trading_events import OrderPlaced, PositionOpened
    from upbit_auto_trading.domain.events.backtest_events import BacktestStarted, BacktestCompleted
    print('✅ 모든 이벤트 클래스 import 성공')
except Exception as e:
    print(f'❌ 이벤트 클래스 import 실패: {e}')
    exit(1)

# DomainEvent 상속 확인
event_classes = [StrategyCreated, StrategyValidated, TriggerCreated, OrderPlaced, BacktestStarted]
print('\n📋 DomainEvent 상속 확인:')
for cls in event_classes:
    if issubclass(cls, DomainEvent):
        print(f'✅ {cls.__name__} - DomainEvent 상속')
    else:
        print(f'❌ {cls.__name__} - DomainEvent 상속 안함')

# 직렬화 기능 테스트
print('\n📋 직렬화 기능 테스트:')
try:
    # 임시 이벤트 생성 및 직렬화 테스트
    test_event = StrategyCreated(strategy_id="TEST_001", strategy_name="테스트 전략")
    serialized = test_event.to_dict()
    print(f'✅ StrategyCreated 직렬화 성공: {len(serialized)} 필드')

    # 핵심 필드 확인
    required_fields = ['event_id', 'timestamp', 'event_type', 'strategy_id']
    for field in required_fields:
        if field in serialized:
            print(f'✅ 필수 필드 {field} 존재')
        else:
            print(f'❌ 필수 필드 {field} 누락')

except Exception as e:
    print(f'❌ 직렬화 테스트 실패: {e}')

print('\n✅ 1단계: 이벤트 정의 검증 완료')
