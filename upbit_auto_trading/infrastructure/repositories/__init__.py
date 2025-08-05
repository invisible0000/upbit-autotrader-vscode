"""
Repository 구현체들

Domain Layer에서 정의된 Repository 인터페이스들을 SQLite 기반으로 구현합니다.
모든 Repository는 의존성 주입 패턴을 통해 DatabaseManager를 주입받아 사용합니다.

구현된 Repository들:
- SqliteStrategyRepository: 매매 전략 데이터 관리
- SqliteTriggerRepository: 트리거 조건 데이터 관리
- SqliteSettingsRepository: 시스템 설정 및 변수 정의 (읽기 전용)
- SqliteMarketDataRepository: 시장 데이터 관리 (향후 구현)
- SqliteBacktestRepository: 백테스팅 결과 관리 (향후 구현)
"""

__all__ = []
