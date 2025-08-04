"""
Repository 인터페이스 테스트 패키지

이 패키지는 Domain Layer의 Repository 인터페이스들에 대한 Mock 기반 테스트를 포함합니다.
실제 데이터베이스 의존성 없이 인터페이스 계약과 타입 안전성을 검증합니다.

테스트 대상:
- StrategyRepository 인터페이스
- TriggerRepository 인터페이스
- SettingsRepository 인터페이스
- MarketDataRepository 인터페이스
- BacktestRepository 인터페이스
- RepositoryFactory 인터페이스

모든 테스트는 unittest.mock.Mock(spec=Repository) 패턴을 사용하여
인터페이스 명세 준수 여부를 검증합니다.
"""

__all__ = [
    # 테스트 클래스들은 pytest discovery를 통해 자동으로 발견됩니다
]
