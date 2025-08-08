# Database Configuration Domain

데이터베이스 설정과 관리를 담당하는 도메인 계층입니다.

## 구조

### Entities (엔터티)
- `database_profile.py`: 데이터베이스 프로필 엔터티
- `backup_record.py`: 백업 기록 엔터티

### Value Objects (값 객체)
- `database_path.py`: 데이터베이스 경로 값 객체
- `database_type.py`: 데이터베이스 타입 값 객체

### Aggregates (집합체)
- `database_configuration.py`: 데이터베이스 설정 집합체 루트

### Services (도메인 서비스)
- `database_backup_service.py`: 백업 관련 도메인 서비스

### Repositories (저장소 인터페이스)
- `idatabase_config_repository.py`: 데이터베이스 설정 저장소 인터페이스

## 사용법

```python
from upbit_auto_trading.domain.database_configuration import (
    DatabaseProfile,
    DatabasePath,
    DatabaseType,
    DatabaseConfiguration,
    DatabaseBackupService
)

# 데이터베이스 프로필 생성
profile = DatabaseProfile(
    profile_id="profile_001",
    name="메인 설정 DB",
    database_type="settings",
    file_path=Path("data/settings.sqlite3"),
    created_at=datetime.now()
)

# 설정 집합체 생성
config = DatabaseConfiguration()
config.add_database_profile(profile)
config.activate_database_profile(profile.profile_id)

# 백업 서비스 사용
backup_service = DatabaseBackupService()
backup_record = backup_service.create_backup(profile)
```

## DDD 원칙

이 도메인 계층은 다음 DDD 원칙을 준수합니다:

1. **도메인 순수성**: 외부 의존성 없이 비즈니스 로직만 포함
2. **집합체 일관성**: DatabaseConfiguration이 모든 일관성 규칙 강제
3. **불변성**: 엔터티 상태 변경 시 새 인스턴스 반환
4. **의존성 역전**: Repository 인터페이스로 Infrastructure 계층과 분리
