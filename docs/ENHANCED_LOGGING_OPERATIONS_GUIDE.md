# LLM 에이전트 로깅 시스템 v4.0 운영 가이드

## 🏃‍♂️ 프로덕션 환경 배포

### 1. 시스템 요구사항

#### 최소 요구사항
- **Python**: 3.8 이상
- **메모리**: 최소 2GB RAM
- **디스크**: 최소 1GB 여유 공간
- **CPU**: 듀얼 코어 이상

#### 권장 사양 (고부하 환경)
- **Python**: 3.11 이상
- **메모리**: 8GB RAM 이상
- **디스크**: SSD 5GB 이상
- **CPU**: 쿼드 코어 이상

#### 의존성 패키지
```bash
# 필수 패키지
pip install psutil
pip install aiofiles
pip install pyyaml

# 선택적 패키지 (성능 향상)
pip install uvloop      # 더 빠른 이벤트 루프 (Linux/macOS)
pip install orjson      # 더 빠른 JSON 처리
```

### 2. 프로덕션 설정

#### config/enhanced_logging.production.yaml
```yaml
core:
  enabled: true
  log_level: "INFO"
  max_log_file_size_mb: 100
  backup_count: 10

briefing:
  enabled: true
  update_interval: 300        # 5분마다 업데이트
  auto_generate: true
  include_performance_metrics: true

dashboard:
  enabled: true
  realtime_updates: true
  update_interval: 60         # 1분마다 업데이트
  max_dashboard_history: 1000

performance:
  async_processing: true
  queue_size: 50000          # 대용량 큐
  worker_count: 6            # CPU 코어 수에 맞춰 조정
  batch_size: 500            # 대용량 배치

  memory_optimization: true
  memory_threshold_mb: 2000   # 2GB 임계값
  gc_threshold_factor: 2.0
  monitoring_interval: 60

  caching_enabled: true
  default_cache_size: 10000
  default_cache_ttl: 3600    # 1시간

  performance_monitoring: true
  metric_collection_interval: 30
  history_retention_hours: 24
```

### 3. 서비스 등록 및 관리

#### systemd 서비스 파일 (Linux)
```ini
# /etc/systemd/system/upbit-logging.service
[Unit]
Description=Upbit Auto Trading Logging Service
After=network.target

[Service]
Type=forking
User=upbit
Group=upbit
WorkingDirectory=/opt/upbit-autotrader
Environment=PYTHONPATH=/opt/upbit-autotrader
ExecStart=/opt/upbit-autotrader/venv/bin/python -m upbit_auto_trading.infrastructure.logging.service
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
Restart=always
RestartSec=5

# 리소스 제한
MemoryLimit=4G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 등록 및 시작
sudo systemctl daemon-reload
sudo systemctl enable upbit-logging
sudo systemctl start upbit-logging

# 상태 확인
sudo systemctl status upbit-logging

# 로그 확인
sudo journalctl -u upbit-logging -f
```

#### Windows 서비스 (NSSM 사용)
```cmd
# NSSM으로 서비스 생성
nssm install "Upbit Logging Service" "C:\Python311\python.exe"
nssm set "Upbit Logging Service" Arguments "-m upbit_auto_trading.infrastructure.logging.service"
nssm set "Upbit Logging Service" AppDirectory "C:\upbit-autotrader"
nssm set "Upbit Logging Service" Start SERVICE_AUTO_START

# 서비스 시작
net start "Upbit Logging Service"
```

### 4. 모니터링 및 알림

#### Prometheus 메트릭 수집
```python
# upbit_auto_trading/infrastructure/logging/monitoring/prometheus_exporter.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

class PrometheusExporter:
    def __init__(self, port=8000):
        self.port = port

        # 메트릭 정의
        self.log_entries_total = Counter('logging_entries_total',
                                       'Total log entries processed',
                                       ['level', 'component'])

        self.log_processing_duration = Histogram('logging_processing_duration_seconds',
                                               'Log processing duration')

        self.system_health_score = Gauge('system_health_score',
                                        'Current system health score (0-100)')

        self.memory_usage_mb = Gauge('memory_usage_mb',
                                   'Current memory usage in MB')

        self.cache_hit_rate = Gauge('cache_hit_rate',
                                  'Cache hit rate percentage',
                                  ['cache_name'])

    def start_server(self):
        start_http_server(self.port)
        print(f"Prometheus metrics server started on port {self.port}")

    def record_log_entry(self, level, component):
        self.log_entries_total.labels(level=level, component=component).inc()

    def record_processing_time(self, duration_seconds):
        self.log_processing_duration.observe(duration_seconds)

    def update_system_health(self, score):
        self.system_health_score.set(score)

    def update_memory_usage(self, memory_mb):
        self.memory_usage_mb.set(memory_mb)

    def update_cache_hit_rate(self, cache_name, hit_rate):
        self.cache_hit_rate.labels(cache_name=cache_name).set(hit_rate)

# 사용 예제
exporter = PrometheusExporter(port=8000)
exporter.start_server()
```

#### Grafana 대시보드 설정
```json
{
  "dashboard": {
    "title": "Upbit Logging System Monitoring",
    "panels": [
      {
        "title": "Log Entries per Second",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(logging_entries_total[5m])",
            "legendFormat": "{{level}} - {{component}}"
          }
        ]
      },
      {
        "title": "System Health Score",
        "type": "singlestat",
        "targets": [
          {
            "expr": "system_health_score",
            "legendFormat": "Health Score"
          }
        ],
        "thresholds": "50,80"
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "memory_usage_mb",
            "legendFormat": "Memory (MB)"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "cache_hit_rate",
            "legendFormat": "{{cache_name}}"
          }
        ]
      }
    ]
  }
}
```

### 5. 백업 및 복구

#### 자동 백업 스크립트
```bash
#!/bin/bash
# backup_logging_data.sh

BACKUP_DIR="/backup/upbit-logging"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/backup_$DATE"

# 백업 디렉토리 생성
mkdir -p "$BACKUP_PATH"

# 설정 파일 백업
cp -r /opt/upbit-autotrader/config "$BACKUP_PATH/"

# 로그 파일 백업
cp -r /opt/upbit-autotrader/logs "$BACKUP_PATH/"

# 데이터베이스 백업
cp -r /opt/upbit-autotrader/data "$BACKUP_PATH/"

# 압축
tar -czf "$BACKUP_PATH.tar.gz" -C "$BACKUP_DIR" "backup_$DATE"
rm -rf "$BACKUP_PATH"

# 오래된 백업 정리 (30일 이상)
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_PATH.tar.gz"
```

#### crontab 설정
```bash
# 매일 새벽 2시에 백업 실행
0 2 * * * /opt/upbit-autotrader/scripts/backup_logging_data.sh

# 매시간 시스템 상태 확인
0 * * * * /opt/upbit-autotrader/scripts/health_check.sh
```

#### 복구 스크립트
```bash
#!/bin/bash
# restore_logging_data.sh

BACKUP_FILE="$1"
RESTORE_DIR="/opt/upbit-autotrader"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

# 서비스 중지
sudo systemctl stop upbit-logging

# 현재 데이터 백업
mv "$RESTORE_DIR/config" "$RESTORE_DIR/config.old"
mv "$RESTORE_DIR/logs" "$RESTORE_DIR/logs.old"
mv "$RESTORE_DIR/data" "$RESTORE_DIR/data.old"

# 백업 파일 복원
tar -xzf "$BACKUP_FILE" -C /tmp/
BACKUP_DIR=$(basename "$BACKUP_FILE" .tar.gz)

cp -r "/tmp/$BACKUP_DIR/config" "$RESTORE_DIR/"
cp -r "/tmp/$BACKUP_DIR/logs" "$RESTORE_DIR/"
cp -r "/tmp/$BACKUP_DIR/data" "$RESTORE_DIR/"

# 권한 설정
chown -R upbit:upbit "$RESTORE_DIR"

# 서비스 시작
sudo systemctl start upbit-logging

echo "Restore completed from $BACKUP_FILE"
```

### 6. 로그 순환 및 정리

#### logrotate 설정
```
# /etc/logrotate.d/upbit-logging
/opt/upbit-autotrader/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 upbit upbit
    postrotate
        /bin/kill -HUP $(cat /var/run/upbit-logging.pid 2>/dev/null) 2>/dev/null || true
    endscript
}
```

#### 자동 정리 스크립트
```python
# cleanup_old_data.py
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

class DataCleanupManager:
    def __init__(self, base_path="/opt/upbit-autotrader"):
        self.base_path = Path(base_path)

    def cleanup_old_logs(self, days_to_keep=30):
        """오래된 로그 파일 정리"""
        logs_dir = self.base_path / "logs"
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        for log_file in logs_dir.glob("*.log.*"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                print(f"Deleted old log: {log_file}")

    def cleanup_dashboard_data(self, hours_to_keep=168):  # 7일
        """오래된 대시보드 데이터 정리"""
        dashboard_dir = self.base_path / "data" / "dashboard"
        cutoff_date = datetime.now() - timedelta(hours=hours_to_keep)

        for data_file in dashboard_dir.glob("dashboard_*.json"):
            if data_file.stat().st_mtime < cutoff_date.timestamp():
                data_file.unlink()
                print(f"Deleted old dashboard data: {data_file}")

    def cleanup_performance_metrics(self, days_to_keep=7):
        """오래된 성능 메트릭 정리"""
        metrics_dir = self.base_path / "data" / "metrics"
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        for metrics_file in metrics_dir.glob("metrics_*.json"):
            if metrics_file.stat().st_mtime < cutoff_date.timestamp():
                metrics_file.unlink()
                print(f"Deleted old metrics: {metrics_file}")

if __name__ == "__main__":
    cleanup_manager = DataCleanupManager()
    cleanup_manager.cleanup_old_logs(30)
    cleanup_manager.cleanup_dashboard_data(168)
    cleanup_manager.cleanup_performance_metrics(7)
```

### 7. 성능 튜닝

#### 고부하 환경 최적화
```python
# 고성능 설정 예제
async_processor_config = {
    "queue_size": 100000,      # 대용량 큐
    "worker_count": 8,         # CPU 코어 수 × 2
    "batch_size": 1000,        # 대용량 배치
    "priority_queue_enabled": True,
    "compression_enabled": True  # 메모리 절약
}

memory_optimizer_config = {
    "memory_threshold_mb": 4000,    # 4GB 임계값
    "gc_threshold_factor": 1.5,     # 적극적 GC
    "monitoring_interval": 30,      # 자주 모니터링
    "aggressive_cleanup": True      # 적극적 정리
}

cache_manager_config = {
    "l1_cache_size": 1000,         # 빠른 L1 캐시
    "l2_cache_size": 50000,        # 대용량 L2 캐시
    "l3_cache_size": 500000,       # 초대용량 L3 캐시
    "intelligent_eviction": True,   # 지능형 제거
    "compression_enabled": True     # 압축 저장
}
```

#### 데이터베이스 최적화
```sql
-- 인덱스 최적화
CREATE INDEX idx_logs_timestamp ON logs(timestamp);
CREATE INDEX idx_logs_level ON logs(level);
CREATE INDEX idx_logs_component ON logs(component);
CREATE UNIQUE INDEX idx_logs_composite ON logs(timestamp, component, level);

-- 파티셔닝 (PostgreSQL 예제)
CREATE TABLE logs_2024_01 PARTITION OF logs
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- 통계 업데이트
ANALYZE logs;
```

### 8. 보안 고려사항

#### 로그 데이터 암호화
```python
from cryptography.fernet import Fernet
import base64

class SecureLoggingService:
    def __init__(self, encryption_key=None):
        if encryption_key is None:
            encryption_key = Fernet.generate_key()
        self.cipher_suite = Fernet(encryption_key)

    def encrypt_sensitive_data(self, data):
        """민감한 데이터 암호화"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher_suite.encrypt(data)

    def decrypt_sensitive_data(self, encrypted_data):
        """민감한 데이터 복호화"""
        return self.cipher_suite.decrypt(encrypted_data).decode()

    def secure_log(self, level, component, message, sensitive_data=None):
        """보안 로그 기록"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "component": component,
            "message": message
        }

        if sensitive_data:
            log_entry["sensitive_data"] = base64.b64encode(
                self.encrypt_sensitive_data(str(sensitive_data))
            ).decode()

        return log_entry
```

#### 접근 제어 및 감사
```python
class AccessControlManager:
    def __init__(self):
        self.authorized_users = set()
        self.access_log = []

    def authorize_user(self, user_id, role):
        """사용자 권한 부여"""
        self.authorized_users.add((user_id, role))
        self._log_access("AUTHORIZE", user_id, role)

    def check_permission(self, user_id, action):
        """권한 확인"""
        user_roles = [role for uid, role in self.authorized_users if uid == user_id]

        permission_map = {
            "READ_LOGS": ["admin", "operator", "viewer"],
            "MODIFY_CONFIG": ["admin"],
            "DELETE_DATA": ["admin"],
            "EXPORT_DATA": ["admin", "operator"]
        }

        allowed_roles = permission_map.get(action, [])
        has_permission = any(role in allowed_roles for role in user_roles)

        self._log_access("CHECK_PERMISSION", user_id, action, has_permission)
        return has_permission

    def _log_access(self, action, user_id, target, result=None):
        """접근 로그 기록"""
        access_record = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "user_id": user_id,
            "target": target,
            "result": result,
            "ip_address": self._get_client_ip()
        }
        self.access_log.append(access_record)
```

### 9. 트러블슈팅 가이드

#### 일반적인 문제 및 해결책

**1. 메모리 부족 오류**
```bash
# 메모리 사용량 확인
free -h
top -p $(pgrep -f upbit)

# 해결책
# 1. memory_threshold_mb 값 낮추기
# 2. GC 설정 조정
# 3. 캐시 크기 줄이기
```

**2. 로그 처리 지연**
```python
# 성능 진단
performance_monitor = PerformanceMonitor()
stats = performance_monitor.get_current_performance_summary()

if stats["queue_size"] > 10000:
    print("큐 크기가 너무 큼 - worker_count 증가 필요")

if stats["processing_time_avg"] > 100:
    print("처리 시간이 너무 김 - 배치 크기 조정 필요")
```

**3. 디스크 공간 부족**
```bash
# 디스크 사용량 확인
df -h

# 오래된 파일 정리
find /opt/upbit-autotrader/logs -name "*.log" -mtime +30 -delete
find /opt/upbit-autotrader/data -name "*.json" -mtime +7 -delete
```

**4. 서비스 시작 실패**
```bash
# 로그 확인
sudo journalctl -u upbit-logging -n 50

# 설정 파일 검증
python -c "
import yaml
with open('/opt/upbit-autotrader/config/enhanced_logging.yaml') as f:
    yaml.safe_load(f)
print('Config file is valid')
"

# 권한 확인
ls -la /opt/upbit-autotrader/
```

### 10. 업그레이드 가이드

#### 버전 업그레이드 절차
```bash
#!/bin/bash
# upgrade_logging_system.sh

VERSION="$1"
if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

# 1. 백업 생성
./backup_logging_data.sh

# 2. 서비스 중지
sudo systemctl stop upbit-logging

# 3. 코드 업데이트
cd /opt/upbit-autotrader
git fetch origin
git checkout "v$VERSION"

# 4. 의존성 업데이트
./venv/bin/pip install -r requirements.txt

# 5. 마이그레이션 실행
./venv/bin/python -m upbit_auto_trading.infrastructure.logging.migration

# 6. 설정 검증
./venv/bin/python -c "
from upbit_auto_trading.infrastructure.logging.config import EnhancedLoggingConfig
config = EnhancedLoggingConfig.from_file('config/enhanced_logging.yaml')
print('Configuration is valid')
"

# 7. 서비스 시작
sudo systemctl start upbit-logging

# 8. 상태 확인
sleep 5
sudo systemctl status upbit-logging

echo "Upgrade to version $VERSION completed"
```

---

이 운영 가이드를 통해 LLM 에이전트 로깅 시스템 v4.0을 안정적으로 프로덕션 환경에서 운영할 수 있습니다.
