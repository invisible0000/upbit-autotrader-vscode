# 시스템 모니터링 가이드

## 개요

시스템 모니터링은 업비트 자동매매 시스템의 안정적인 운영을 위한 핵심 기능입니다. 이 모듈은 시스템 리소스 사용량, 오류 발생, 로그 파일 등을 모니터링하고 필요한 경우 사용자에게 알림을 제공합니다. 이 문서는 시스템 모니터링 기능의 구조, 기능, 사용 방법에 대한 가이드를 제공합니다.

## 구조

시스템 모니터링 모듈은 다음과 같은 주요 컴포넌트로 구성됩니다:

1. **시스템 모니터**
   - `SystemMonitor`: 시스템 모니터링 핵심 클래스
   - `AlertManager`: 알림 관리 클래스 (알림 센터와 연동)

2. **모니터링 대상**
   - 시스템 리소스 (CPU, 메모리, 디스크)
   - 오류 및 예외 상황
   - 로그 파일
   - 시스템 상태

## 기능

### 1. 시스템 리소스 모니터링

시스템 모니터는 다음과 같은 리소스를 모니터링합니다:

#### 1.1 CPU 사용량 모니터링

```python
# CPU 사용량 확인
monitor.check_cpu_usage()

# 임계값 설정
monitor.set_cpu_threshold(80)  # 80% 임계값 설정
```

CPU 사용량이 설정된 임계값(기본값: 80%)을 초과하면 알림이 발생합니다.

#### 1.2 메모리 사용량 모니터링

```python
# 메모리 사용량 확인
monitor.check_memory_usage()

# 임계값 설정
monitor.set_memory_threshold(90)  # 90% 임계값 설정
```

메모리 사용량이 설정된 임계값(기본값: 90%)을 초과하면 알림이 발생합니다.

#### 1.3 디스크 사용량 모니터링

```python
# 디스크 사용량 확인
monitor.check_disk_usage()

# 임계값 설정
monitor.set_disk_threshold(95)  # 95% 임계값 설정
```

디스크 사용량이 설정된 임계값(기본값: 95%)을 초과하면 알림이 발생합니다.

### 2. 오류 알림

시스템 모니터는 다음과 같은 오류 알림 기능을 제공합니다:

```python
# 일반 오류 알림
monitor.notify_error("database", "데이터베이스 연결 실패: Connection refused", is_critical=False)

# 심각한 오류 알림
monitor.notify_error("api", "API 키 인증 실패: Invalid API key", is_critical=True)
```

`is_critical` 매개변수를 통해 오류의 심각도를 지정할 수 있습니다. 심각한 오류는 알림 센터에서 강조 표시됩니다.

### 3. 시스템 상태 알림

시스템 모니터는 다음과 같은 시스템 상태 알림 기능을 제공합니다:

```python
# 시스템 상태 알림
monitor.notify_system_status("startup", "시스템이 정상적으로 시작되었습니다.")
monitor.notify_system_status("database", "데이터베이스 백업이 완료되었습니다.")
```

### 4. 로그 파일 모니터링

시스템 모니터는 로그 파일을 모니터링하고 특정 로그 레벨(예: ERROR, CRITICAL)의 메시지가 발생하면 알림을 생성합니다:

```python
# 로그 파일 모니터링 추가
monitor.add_log_file_to_monitor("logs/error.log", ["ERROR", "CRITICAL"])
monitor.add_log_file_to_monitor("logs/app.log", ["CRITICAL"])

# 로그 파일 모니터링 제거
monitor.remove_log_file_from_monitor("logs/app.log")

# 로그 파일 확인
monitor.check_log_files()
```

### 5. 자동 모니터링

시스템 모니터는 백그라운드 스레드를 통해 자동으로 시스템을 모니터링할 수 있습니다:

```python
# 모니터링 시작
monitor.start_monitoring()

# 모니터링 간격 설정 (초 단위)
monitor.set_monitoring_interval(60)  # 60초마다 모니터링

# 모니터링 중지
monitor.stop_monitoring()
```

### 6. 알림 설정 관리

시스템 모니터는 다음과 같은 알림 설정 관리 기능을 제공합니다:

```python
# 오류 알림 활성화/비활성화
monitor.set_error_notification_enabled(True)
monitor.set_error_notification_enabled(False)

# 상태 알림 활성화/비활성화
monitor.set_status_notification_enabled(True)
monitor.set_status_notification_enabled(False)

# 리소스 알림 활성화/비활성화
monitor.set_resource_notification_enabled(True)
monitor.set_resource_notification_enabled(False)

# 설정 저장
monitor.save_settings("config/monitor_settings.json")

# 설정 로드
monitor.load_settings("config/monitor_settings.json")
```

## 사용 방법

### 1. 시스템 모니터 초기화

```python
from upbit_auto_trading.business_logic.monitoring.system_monitor import SystemMonitor
from upbit_auto_trading.business_logic.monitoring.alert_manager import AlertManager

# 알림 관리자 생성
alert_manager = AlertManager()

# 시스템 모니터 생성
system_monitor = SystemMonitor(alert_manager)
```

### 2. 리소스 모니터링 설정

```python
# CPU 사용량 임계값 설정
system_monitor.set_cpu_threshold(80)  # 80%

# 메모리 사용량 임계값 설정
system_monitor.set_memory_threshold(90)  # 90%

# 디스크 사용량 임계값 설정
system_monitor.set_disk_threshold(95)  # 95%
```

### 3. 로그 파일 모니터링 설정

```python
# 로그 파일 모니터링 추가
system_monitor.add_log_file_to_monitor("logs/error.log", ["ERROR", "CRITICAL"])
system_monitor.add_log_file_to_monitor("logs/app.log", ["CRITICAL"])
```

### 4. 자동 모니터링 시작

```python
# 모니터링 간격 설정 (초 단위)
system_monitor.set_monitoring_interval(60)  # 60초마다 모니터링

# 모니터링 시작
system_monitor.start_monitoring()
```

### 5. 수동 모니터링

```python
# CPU 사용량 확인
system_monitor.check_cpu_usage()

# 메모리 사용량 확인
system_monitor.check_memory_usage()

# 디스크 사용량 확인
system_monitor.check_disk_usage()

# 로그 파일 확인
system_monitor.check_log_files()
```

### 6. 알림 생성

```python
# 오류 알림 생성
system_monitor.notify_error("database", "데이터베이스 연결 실패: Connection refused", is_critical=True)

# 시스템 상태 알림 생성
system_monitor.notify_system_status("backup", "데이터베이스 백업이 완료되었습니다.")
```

### 7. 모니터링 중지

```python
# 모니터링 중지
system_monitor.stop_monitoring()
```

## 개발자 가이드

최근 구현된 모니터링 및 알림 시스템에 대한 자세한 개발 내용은 [개발 진행 현황](development_progress.md) 문서에서 확인할 수 있습니다.

### 1. 외부 패키지 의존성 관리

시스템 모니터링 모듈은 `psutil` 패키지를 사용하여 시스템 리소스 사용량을 모니터링합니다. 이 패키지가 설치되어 있지 않은 경우에도 기본 기능이 동작하도록 예외 처리가 되어 있습니다:

```python
# psutil 패키지 임포트 시도
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil package not available. Resource monitoring will be limited.")

def check_cpu_usage(self):
    if not PSUTIL_AVAILABLE:
        # 대체 로직 또는 기능 비활성화
        return
    # 정상 로직 실행
```

`psutil` 패키지를 설치하려면 다음 명령을 사용합니다:

```bash
pip install psutil
```

### 2. 알림 중복 방지

시스템 모니터링 모듈은 알림 이력을 관리하여 중복 알림을 방지합니다:

```python
def notify_error(self, component, message, is_critical=False):
    # 중복 알림 방지
    error_key = f"{component}:{message}"
    if error_key in self.notified_errors:
        return
    
    # 알림 생성 로직...
    
    # 알림 이력에 추가
    self.notified_errors.add(error_key)
```

임계값 변경 시 관련 알림 이력이 초기화됩니다:

```python
def set_cpu_threshold(self, threshold):
    self.cpu_threshold = max(1, min(100, threshold))
    # 임계값 변경 시 알림 이력 초기화
    self.notified_resources = set(r for r in self.notified_resources if not r.startswith("cpu:"))
```

### 3. 멀티스레딩 안전성

시스템 모니터링 모듈은 멀티스레딩 환경에서 안전하게 동작하도록 설계되었습니다:

```python
def start_monitoring(self):
    if self.is_monitoring:
        return
    
    self.is_monitoring = True
    
    def monitoring_task():
        while self.is_monitoring:
            try:
                # 모니터링 로직...
            except Exception as e:
                print(f"시스템 모니터링 중 오류 발생: {e}")
            
            # 대기
            time.sleep(self.monitoring_interval)
    
    # 모니터링 스레드 시작 (데몬 스레드로 설정)
    self.monitoring_thread = threading.Thread(target=monitoring_task, daemon=True)
    self.monitoring_thread.start()
```

모니터링 스레드는 데몬 스레드로 설정되어 메인 프로그램 종료 시 자동으로 종료됩니다.

### 4. 파일 경로 및 권한 관리

시스템 모니터링 모듈은 파일 작업 시 경로 확인 및 예외 처리를 통해 안전하게 동작합니다:

```python
def save_settings(self, file_path):
    try:
        # 디렉토리 경로 확인
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # 설정 저장 로직...
        
    except Exception as e:
        print(f"설정 저장 중 오류 발생: {e}")
        return False
```

## 테스트

시스템 모니터링 모듈은 다음과 같은 테스트가 구현되어 있습니다:

1. **오류 알림 테스트**
   - 오류 알림이 올바르게 생성되는지 확인
   - 중복 알림 방지 기능이 올바르게 작동하는지 확인

2. **시스템 상태 알림 테스트**
   - 시스템 상태 알림이 올바르게 생성되는지 확인

3. **리소스 모니터링 테스트**
   - CPU, 메모리, 디스크 사용량 모니터링이 올바르게 작동하는지 확인
   - 임계값 설정이 올바르게 적용되는지 확인

4. **알림 설정 관리 테스트**
   - 알림 설정이 올바르게 저장되고 로드되는지 확인
   - 알림 활성화/비활성화 기능이 올바르게 작동하는지 확인

5. **로그 모니터링 테스트**
   - 로그 파일 모니터링이 올바르게 작동하는지 확인
   - 로그 레벨 필터링이 올바르게 적용되는지 확인

테스트를 실행하려면 다음 명령을 사용합니다:

```bash
python -m unittest upbit_auto_trading/tests/test_09_3_system_notifications.py
```

## 모범 사례 및 주의사항

### 1. 리소스 모니터링 최적화

- 모니터링 간격을 너무 짧게 설정하면 시스템 부하가 증가할 수 있습니다. 적절한 간격(예: 30초 이상)을 설정하세요.
- 리소스 사용량이 많은 작업(예: 백테스팅)을 실행할 때는 임시로 리소스 알림을 비활성화하는 것이 좋습니다.

### 2. 플랫폼 독립성

- 시스템 리소스 모니터링 기능은 플랫폼별 차이를 고려하여 구현되었습니다.
- Windows, Linux, macOS 등 다양한 환경에서 테스트를 수행하는 것이 좋습니다.
- `psutil` 패키지가 설치되어 있지 않은 경우에도 기본 기능이 동작하도록 설계되었습니다.

### 3. 로그 파일 모니터링

- 로그 파일이 매우 큰 경우 모니터링 성능이 저하될 수 있습니다. 로그 파일을 주기적으로 로테이션하는 것이 좋습니다.
- 로그 레벨 필터링을 적절히 설정하여 중요한 로그 메시지만 알림을 받도록 하세요.

### 4. 알림 관리

- 너무 많은 알림이 발생하면 사용자가 중요한 알림을 놓칠 수 있습니다. 알림 임계값을 적절히 설정하세요.
- 알림 발생 빈도를 제한하는 메커니즘을 구현하는 것이 좋습니다(예: 동일 알림은 1시간에 한 번만 발생).
- 알림 우선순위를 설정하여 중요한 알림이 사용자에게 효과적으로 전달되도록 하세요.

## 향후 개선 사항

1. **알림 발생 빈도 제한**
   - 동일한 알림이 특정 시간 내에 반복해서 발생하지 않도록 제한하는 기능 추가
   - 예: "동일 알림은 1시간에 한 번만 발생"

2. **알림 우선순위 설정**
   - 알림에 우선순위를 부여하여 중요한 알림이 더 눈에 띄게 표시되도록 개선
   - 우선순위별 알림 처리 방식 차별화 (예: 높은 우선순위 알림은 즉시 표시, 낮은 우선순위 알림은 요약으로 표시)

3. **알림 그룹화**
   - 유사한 알림을 하나로 묶어 표시하는 기능 구현
   - 예: "CPU 사용량 임계값 초과 알림 5건"

4. **원격 모니터링**
   - 원격 시스템 모니터링 기능 추가
   - 여러 시스템의 상태를 중앙에서 모니터링하는 기능 구현

5. **모니터링 대시보드**
   - 시스템 리소스 사용량, 알림 발생 현황 등을 시각적으로 표시하는 대시보드 구현
   - 시계열 그래프를 통한 리소스 사용량 추이 분석 기능 추가

6. **사용자 정의 모니터링**
   - 사용자가 직접 모니터링 대상과 조건을 정의할 수 있는 기능 추가
   - 스크립트 기반 모니터링 규칙 설정 기능 구현

## 결론

시스템 모니터링 모듈은 업비트 자동매매 시스템의 안정적인 운영을 위한 핵심 기능입니다. 이 문서에서는 시스템 모니터링 모듈의 구조, 기능, 사용 방법에 대한 가이드를 제공했습니다. 향후 개선 사항을 통해 모니터링 기능과 사용자 경험을 더욱 향상시킬 계획입니다.