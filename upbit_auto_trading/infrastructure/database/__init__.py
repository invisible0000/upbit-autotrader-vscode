"""
데이터베이스 연결 및 관리

SQLite 데이터베이스와의 연결을 관리하고, 성능 최적화된 쿼리 실행을 담당합니다.
Connection Pooling, 트랜잭션 관리, 동시성 제어 등을 제공합니다.

주요 클래스:
- DatabaseManager: 다중 SQLite 연결 관리 및 쿼리 실행
- DatabaseConnectionProvider: Singleton 패턴의 연결 제공자
"""

__all__ = []
