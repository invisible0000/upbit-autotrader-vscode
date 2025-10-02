# Repository 패턴 구현 가이드

## 개요

Repository 패턴은 데이터 접근 로직을 캡슐화하여 Domain 계층이 Infrastructure에 직접 의존하지 않도록 하는 DDD 핵심 패턴입니다.

## 구현 구조

### 1. Domain 계층 - Repository 인터페이스

```python
# upbit_auto_trading/domain/database_configuration/repositories/database_verification_repository.py

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

class IDatabaseVerificationRepository(ABC):
    """데이터베이스 검증을 위한 Repository 인터페이스"""

    @abstractmethod
    def verify_sqlite_integrity(self, file_path: Path) -> bool:
        """SQLite 파일의 무결성을 검증합니다."""
        pass

    @abstractmethod
    def check_database_accessibility(self, file_path: Path) -> bool:
        """데이터베이스 파일에 접근 가능한지 확인합니다."""
        pass

    @abstractmethod
    def get_database_info(self, file_path: Path) -> Optional[dict]:
        """데이터베이스 기본 정보를 조회합니다."""
        pass

    @abstractmethod
    def test_connection(self, file_path: Path) -> Tuple[bool, str]:
        """데이터베이스 연결을 테스트합니다."""
        pass
```

### 2. Infrastructure 계층 - Repository 구현

```python
# upbit_auto_trading/infrastructure/persistence/sqlite_database_verification_repository.py

import sqlite3
from pathlib import Path
from typing import Optional, Tuple
from upbit_auto_trading.domain.database_configuration.repositories.database_verification_repository import IDatabaseVerificationRepository

class SqliteDatabaseVerificationRepository(IDatabaseVerificationRepository):
    """SQLite 데이터베이스 검증 Repository 구현체"""

    def verify_sqlite_integrity(self, file_path: Path) -> bool:
        """SQLite 파일의 무결성을 검증합니다."""
        try:
            with sqlite3.connect(file_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check(1)")
                result = cursor.fetchone()
                return result and result[0] == 'ok'
        except Exception:
            return False

    def get_database_info(self, file_path: Path) -> Optional[dict]:
        """데이터베이스 기본 정보를 조회합니다."""
        try:
            with sqlite3.connect(file_path) as conn:
                cursor = conn.cursor()

                # 테이블 수
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]

                return {
                    'file_size': file_path.stat().st_size,
                    'table_count': table_count,
                    'file_path': str(file_path)
                }
        except Exception:
            return None

    # ... 기타 메서드 구현
```

### 3. Domain Service - Repository 사용

```python
# upbit_auto_trading/domain/database_configuration/services/database_backup_service.py

class DatabaseBackupService:
    def __init__(self, verification_repository: IDatabaseVerificationRepository):
        self._verification_repository = verification_repository
        self._logger = create_domain_logger("DatabaseBackupService")

    def _verify_sqlite_structure(self, file_path: Path) -> bool:
        """SQLite 파일 구조 기본 검증"""
        try:
            # Infrastructure 의존성 없이 Repository 사용
            is_valid = self._verification_repository.verify_sqlite_integrity(file_path)

            if is_valid:
                self._logger.debug(f"SQLite 구조 검증 성공: {file_path}")
                return True
            else:
                self._logger.warning(f"SQLite 무결성 검사 실패: {file_path}")
                return False
        except Exception as e:
            self._logger.error(f"SQLite 구조 검증 중 오류 발생: {e}")
            return False
```

## 의존성 주입 (DI)

### Application 계층에서 Repository 주입

```python
# upbit_auto_trading/application/services/database_application_service.py

from upbit_auto_trading.domain.database_configuration.services.database_backup_service import DatabaseBackupService
from upbit_auto_trading.infrastructure.persistence.sqlite_database_verification_repository import SqliteDatabaseVerificationRepository

class DatabaseApplicationService:
    def __init__(self):
        # Infrastructure 구현체를 Domain Service에 주입
        verification_repository = SqliteDatabaseVerificationRepository()
        self._backup_service = DatabaseBackupService(verification_repository)
```

## 주요 이점

### 1. DDD 순수성 확보

- Domain 계층이 Infrastructure에 직접 의존하지 않음
- 비즈니스 로직이 기술적 구현 세부사항과 분리됨

### 2. 테스트 용이성

```python
# 테스트에서 Mock Repository 사용 가능
class MockDatabaseVerificationRepository(IDatabaseVerificationRepository):
    def verify_sqlite_integrity(self, file_path: Path) -> bool:
        return True  # 테스트용 고정값
```

### 3. 유연한 구현 교체

- SQLite에서 PostgreSQL로 변경 시 Repository 구현체만 교체
- Domain 비즈니스 로직은 변경 불필요

## 적용 결과

### Before: 직접 DB 접근 (DDD 위반)

```python
# ❌ Domain에서 직접 sqlite3 사용
import sqlite3

def check_database(self, file_path):
    with sqlite3.connect(file_path) as conn:  # Infrastructure 의존성
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        return cursor.fetchone()[0] == 'ok'
```

### After: Repository 패턴 (DDD 준수)

```python
# ✅ Repository 인터페이스를 통한 추상화
def check_database(self, file_path):
    return self._verification_repository.verify_sqlite_integrity(file_path)
```

## 성과 지표

- **CRITICAL 위반 제거**: 11개 → 0개 (100% 해결)
- **Domain 순수성 확보**: sqlite3 직접 사용 완전 제거
- **테스트 가능성 향상**: Mock Repository 도입 가능
- **유지보수성 개선**: 구현 변경 시 Domain 로직 보호

## 다음 단계

- Phase 1: Domain Events 패턴으로 로깅 의존성 제거 (243개 위반)
- Phase 2: 외부 라이브러리 의존성 DI 적용 (yaml 등)
- Phase 3: 전체 아키텍처 순수성 검증 및 문서화
