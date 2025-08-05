# TASK-20250803-17

## Title
Migration & Deployment - 프로덕션 배포 및 데이터 마이그레이션

## Objective (목표)
Clean Architecture로 리팩토링된 시스템을 안전하게 프로덕션 환경에 배포하고, 기존 데이터의 무손실 마이그레이션을 보장합니다. 롤백 계획과 모니터링 시스템을 구축하여 안정적인 운영 환경을 확보합니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "🚨 위험 관리 및 롤백 계획" + "📞 다음 단계 Action Items"

## Pre-requisites (선행 조건)
- `TASK-20250803-16`: 성능 최적화 완료
- 모든 Phase 1-5 태스크 완료 및 검증
- 통합 테스트 모든 항목 통과

## Detailed Steps (상세 실행 절차)

### 1. **[백업]** 기존 데이터 완전 백업
- [ ] `scripts/backup_manager.py` 생성:
```python
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List

class BackupManager:
    """데이터베이스 백업 관리자"""
    
    def __init__(self, backup_root: str = "data/backups"):
        self.backup_root = Path(backup_root)
        self.backup_root.mkdir(exist_ok=True)
        
    def create_migration_backup(self) -> str:
        """마이그레이션 전 완전 백업"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_root / f"migration_backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)
        
        # 3-DB 아키텍처 백업
        db_files = {
            "settings": "data/settings.sqlite3",
            "strategies": "data/strategies.sqlite3", 
            "market_data": "data/market_data.sqlite3"
        }
        
        backup_manifest = {
            "timestamp": timestamp,
            "backup_type": "migration",
            "files": {}
        }
        
        for db_name, db_path in db_files.items():
            if Path(db_path).exists():
                backup_path = backup_dir / f"{db_name}.sqlite3"
                shutil.copy2(db_path, backup_path)
                
                # 백업 무결성 검증
                self._verify_backup_integrity(db_path, backup_path)
                backup_manifest["files"][db_name] = str(backup_path)
        
        # 백업 매니페스트 저장
        manifest_path = backup_dir / "backup_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(backup_manifest, f, indent=2)
        
        return str(backup_dir)
    
    def _verify_backup_integrity(self, original: str, backup: str) -> None:
        """백업 파일 무결성 검증"""
        # 테이블 수 검증
        orig_tables = self._get_table_count(original)
        backup_tables = self._get_table_count(backup)
        
        if orig_tables != backup_tables:
            raise BackupIntegrityError(f"테이블 수 불일치: {orig_tables} vs {backup_tables}")
        
        # 레코드 수 검증
        orig_records = self._get_total_record_count(original)
        backup_records = self._get_total_record_count(backup)
        
        if orig_records != backup_records:
            raise BackupIntegrityError(f"레코드 수 불일치: {orig_records} vs {backup_records}")
```

- [ ] 백업 검증 스크립트:
```bash
#!/bin/bash
# 파일: scripts/verify_backup.sh

echo "🔍 백업 무결성 검증 시작..."

BACKUP_DIR=$1
ORIGINAL_DATA_DIR="data"

# SQLite 파일 무결성 검사
for db_file in settings.sqlite3 strategies.sqlite3 market_data.sqlite3; do
    if [ -f "$BACKUP_DIR/$db_file" ] && [ -f "$ORIGINAL_DATA_DIR/$db_file" ]; then
        echo "📊 $db_file 검증 중..."
        
        # PRAGMA integrity_check
        sqlite3 "$BACKUP_DIR/$db_file" "PRAGMA integrity_check;" | grep -q "ok"
        if [ $? -eq 0 ]; then
            echo "✅ $db_file 백업 무결성 확인"
        else
            echo "❌ $db_file 백업 손상 감지!"
            exit 1
        fi
    fi
done

echo "🎉 모든 백업 파일 검증 완료"
```

### 2. **[마이그레이션]** 스키마 및 데이터 마이그레이션
- [ ] `migration/migration_manager.py` 생성:
```python
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
import logging

class MigrationManager:
    """데이터베이스 마이그레이션 관리자"""
    
    def __init__(self, migration_scripts_dir: str = "migration/scripts"):
        self.migration_dir = Path(migration_scripts_dir)
        self.logger = logging.getLogger(__name__)
    
    def execute_migration(self) -> bool:
        """마이그레이션 실행"""
        try:
            # 1. 스키마 마이그레이션
            self._migrate_schemas()
            
            # 2. 데이터 마이그레이션
            self._migrate_data()
            
            # 3. 인덱스 재구성
            self._rebuild_indexes()
            
            # 4. 마이그레이션 검증
            self._verify_migration()
            
            self.logger.info("✅ 마이그레이션 성공적으로 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 마이그레이션 실패: {e}")
            self._rollback_migration()
            return False
    
    def _migrate_schemas(self) -> None:
        """스키마 마이그레이션"""
        schema_scripts = [
            "001_add_clean_architecture_tables.sql",
            "002_create_domain_entity_tables.sql", 
            "003_add_strategy_version_control.sql"
        ]
        
        for script in schema_scripts:
            script_path = self.migration_dir / script
            if script_path.exists():
                self._execute_sql_script(script_path)
    
    def _migrate_data(self) -> None:
        """기존 데이터를 새 스키마로 마이그레이션"""
        # 기존 strategies 테이블 → 새 domain entities
        self._migrate_strategy_data()
        
        # 기존 conditions 테이블 → 새 trigger system
        self._migrate_trigger_data()
        
        # 설정 데이터 검증 및 정규화
        self._normalize_settings_data()
    
    def _migrate_strategy_data(self) -> None:
        """전략 데이터 마이그레이션"""
        with sqlite3.connect("data/strategies.sqlite3") as conn:
            # 기존 전략 데이터 조회
            old_strategies = conn.execute("""
                SELECT id, name, description, strategy_config 
                FROM legacy_strategies
            """).fetchall()
            
            # 새 스키마로 변환 및 삽입
            for strategy in old_strategies:
                strategy_entity = self._convert_to_domain_entity(strategy)
                self._insert_strategy_entity(conn, strategy_entity)
```

- [ ] 마이그레이션 SQL 스크립트들:
```sql
-- 파일: migration/scripts/001_add_clean_architecture_tables.sql
-- Clean Architecture Domain Entity 테이블 생성

CREATE TABLE IF NOT EXISTS domain_strategies (
    id TEXT PRIMARY KEY,
    aggregate_version INTEGER NOT NULL DEFAULT 1,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS domain_triggers (
    id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL,
    trigger_type TEXT NOT NULL, -- 'ENTRY', 'EXIT', 'MANAGEMENT'
    variable_config TEXT NOT NULL, -- JSON
    evaluation_config TEXT NOT NULL, -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES domain_strategies(id)
);

-- 성능 최적화 인덱스
CREATE INDEX IF NOT EXISTS idx_domain_triggers_strategy_id 
ON domain_triggers(strategy_id);

CREATE INDEX IF NOT EXISTS idx_domain_triggers_type 
ON domain_triggers(trigger_type);
```

### 3. **[검증]** 마이그레이션 검증 시스템
- [ ] 데이터 일관성 검증:
```python
# 파일: migration/validation/migration_validator.py
class MigrationValidator:
    """마이그레이션 결과 검증"""
    
    def validate_complete_migration(self) -> ValidationResult:
        """전체 마이그레이션 검증"""
        results = []
        
        # 1. 데이터 개수 검증
        results.append(self._validate_record_counts())
        
        # 2. 데이터 무결성 검증
        results.append(self._validate_data_integrity())
        
        # 3. 비즈니스 로직 검증
        results.append(self._validate_business_logic())
        
        # 4. 성능 검증
        results.append(self._validate_performance())
        
        return ValidationResult.combine(results)
    
    def _validate_business_logic(self) -> ValidationResult:
        """비즈니스 로직 정상 동작 검증"""
        # 기본 7규칙 전략으로 검증
        try:
            strategy_service = self._container.resolve(StrategyApplicationService)
            
            # 기존 전략 조회 테스트
            strategies = strategy_service.get_all_strategies()
            assert len(strategies) > 0, "마이그레이션 후 전략이 없음"
            
            # 새 전략 생성 테스트
            test_strategy = strategy_service.create_strategy(
                CreateBasic7RuleStrategyCommand()
            )
            assert test_strategy.strategy_id is not None
            
            return ValidationResult.success("비즈니스 로직 검증 통과")
            
        except Exception as e:
            return ValidationResult.failure(f"비즈니스 로직 검증 실패: {e}")
```

### 4. **[배포]** 프로덕션 배포 스크립트
- [ ] `deployment/deploy.py` 생성:
```python
import subprocess
import sys
from pathlib import Path
from typing import List, Dict

class ProductionDeployer:
    """프로덕션 배포 관리자"""
    
    def __init__(self, config_path: str = "deployment/production_config.yaml"):
        self.config = self._load_config(config_path)
        self.deployment_log = []
    
    def deploy_to_production(self) -> bool:
        """프로덕션 배포 실행"""
        try:
            # 1. 배포 전 검증
            self._pre_deployment_checks()
            
            # 2. 종속성 설치
            self._install_dependencies()
            
            # 3. 환경 설정
            self._setup_production_environment()
            
            # 4. 서비스 배포
            self._deploy_services()
            
            # 5. 배포 후 검증
            self._post_deployment_verification()
            
            return True
            
        except Exception as e:
            self._rollback_deployment()
            raise DeploymentError(f"배포 실패: {e}")
    
    def _pre_deployment_checks(self) -> None:
        """배포 전 필수 검증"""
        checks = [
            ("Python 버전", self._check_python_version),
            ("의존성 설치", self._check_dependencies),
            ("데이터베이스", self._check_database_status),
            ("마이그레이션", self._check_migration_status),
            ("테스트 통과", self._check_test_results)
        ]
        
        for check_name, check_func in checks:
            if not check_func():
                raise PreDeploymentError(f"{check_name} 검증 실패")
    
    def _setup_production_environment(self) -> None:
        """프로덕션 환경 설정"""
        # 환경 변수 설정
        env_vars = {
            "UPBIT_ENV": "production",
            "UPBIT_LOG_LEVEL": "INFO",
            "UPBIT_DB_PATH": "/opt/upbit-autotrader/data",
            "UPBIT_LOG_PATH": "/var/log/upbit-autotrader"
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value
        
        # 디렉토리 생성
        for path in ["/opt/upbit-autotrader/data", "/var/log/upbit-autotrader"]:
            Path(path).mkdir(parents=True, exist_ok=True)
```

### 5. **[모니터링]** 운영 모니터링 시스템
- [ ] `monitoring/production_monitor.py` 생성:
```python
import time
import psutil
import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class SystemHealthStatus:
    """시스템 상태 정보"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    database_status: Dict[str, bool]
    application_status: Dict[str, str]
    active_strategies: int
    
class ProductionMonitor:
    """프로덕션 환경 모니터링"""
    
    def __init__(self, alert_thresholds: Dict[str, float] = None):
        self.thresholds = alert_thresholds or {
            "cpu_usage": 80.0,     # 80% 이상
            "memory_usage": 85.0,   # 85% 이상
            "disk_usage": 90.0,     # 90% 이상
            "response_time": 1.0    # 1초 이상
        }
        self.health_history: List[SystemHealthStatus] = []
    
    def collect_system_health(self) -> SystemHealthStatus:
        """시스템 상태 수집"""
        return SystemHealthStatus(
            timestamp=time.time(),
            cpu_usage=psutil.cpu_percent(interval=1),
            memory_usage=psutil.virtual_memory().percent,
            disk_usage=psutil.disk_usage('/').percent,
            database_status=self._check_database_health(),
            application_status=self._check_application_health(),
            active_strategies=self._get_active_strategy_count()
        )
    
    def check_alert_conditions(self, status: SystemHealthStatus) -> List[str]:
        """알림 조건 검사"""
        alerts = []
        
        if status.cpu_usage > self.thresholds["cpu_usage"]:
            alerts.append(f"🚨 CPU 사용률 높음: {status.cpu_usage:.1f}%")
        
        if status.memory_usage > self.thresholds["memory_usage"]:
            alerts.append(f"🚨 메모리 사용률 높음: {status.memory_usage:.1f}%")
        
        if not all(status.database_status.values()):
            failed_dbs = [db for db, status in status.database_status.items() if not status]
            alerts.append(f"🚨 데이터베이스 연결 실패: {failed_dbs}")
        
        return alerts
```

### 6. **[롤백]** 롤백 시스템 구축
- [ ] `scripts/rollback_manager.py` 생성:
```python
class RollbackManager:
    """롤백 관리자"""
    
    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
        self.logger = logging.getLogger(__name__)
    
    def execute_rollback(self, backup_timestamp: str) -> bool:
        """지정된 백업으로 롤백"""
        try:
            # 1. 현재 상태 백업 (롤백 전 스냅샷)
            current_backup = self.backup_manager.create_migration_backup()
            self.logger.info(f"현재 상태 백업 생성: {current_backup}")
            
            # 2. 서비스 중단
            self._stop_services()
            
            # 3. 데이터 복원
            self._restore_from_backup(backup_timestamp)
            
            # 4. 서비스 재시작
            self._start_services()
            
            # 5. 롤백 검증
            self._verify_rollback()
            
            return True
            
        except Exception as e:
            self.logger.error(f"롤백 실패: {e}")
            return False
    
    def _verify_rollback(self) -> None:
        """롤백 후 시스템 정상 동작 검증"""
        # 기본 7규칙 전략으로 시스템 동작 확인
        verification_script = "scripts/verify_system_health.py"
        result = subprocess.run([sys.executable, verification_script], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RollbackVerificationError("롤백 후 시스템 검증 실패")
```

### 7. **[문서화]** 운영 매뉴얼 작성
- [ ] `docs/operations/PRODUCTION_MANUAL.md` 생성:
```markdown
# 📋 업비트 자동매매 시스템 운영 매뉴얼

## 🚀 시스템 시작/중단
```bash
# 시스템 시작
python run_desktop_ui.py --env=production

# 시스템 상태 확인
python scripts/check_system_health.py

# 시스템 중단
python scripts/shutdown_system.py
```

## 📊 모니터링 대시보드
- **CPU/메모리**: 80% 이하 유지
- **응답 시간**: 1초 이하
- **활성 전략 수**: 정상 범위 확인
- **데이터베이스 상태**: 모든 DB 연결 정상

## 🚨 비상 상황 대응
### 시스템 과부하 시
1. 활성 전략 수 감소
2. 메모리 사용량 모니터링
3. 필요시 시스템 재시작

### 데이터베이스 오류 시
1. 백업에서 복원: `python scripts/restore_from_backup.py`
2. 무결성 검증: `python scripts/verify_data_integrity.py`
```

## Verification Criteria (완료 검증 조건)

### **[마이그레이션 성공]**
- [ ] 모든 기존 데이터 무손실 마이그레이션
- [ ] 신규 스키마 정상 동작 확인
- [ ] 기본 7규칙 전략 정상 실행

### **[배포 안정성]**
- [ ] 프로덕션 환경에서 24시간 무중단 운영
- [ ] 모든 핵심 기능 정상 동작
- [ ] 성능 목표 달성 (응답시간 100ms 이하)

### **[롤백 준비]**
- [ ] 백업 무결성 검증 통과
- [ ] 롤백 시나리오 테스트 완료
- [ ] 비상 상황 대응 매뉴얼 준비

## Notes (주의사항)
- 마이그레이션 전 반드시 백업 생성
- 프로덕션 배포는 업무 시간 외 실행
- 롤백 계획을 항상 준비한 상태로 진행
