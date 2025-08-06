# LLM 에이전트 로깅 시스템 v4.0 사용 가이드

## 📋 개요

LLM 에이전트 로깅 시스템 v4.0은 기존의 수동적인 터미널 출력 복사 방식을 자동화하여, 실시간으로 시스템 상태를 분석하고 문제점을 감지하는 지능형 로깅 시스템입니다.

### 🎯 주요 기능

- **실시간 LLM 브리핑**: 마크다운 형태의 자동 생성된 상태 보고서
- **JSON 대시보드**: 구조화된 실시간 시스템 모니터링 데이터
- **자동 문제 감지**: 패턴 기반 이슈 탐지 및 해결 방안 제안
- **성능 최적화**: 비동기 처리, 메모리 관리, 지능형 캐싱
- **완전 역호환**: 기존 v3.0/v3.1 시스템과 동시 사용 가능

## 🚀 빠른 시작

### 1. 환경 설정

시스템을 활성화하려면 다음 환경변수를 설정하세요:

```powershell
# PowerShell에서
$env:UPBIT_LLM_BRIEFING_ENABLED='true'
$env:UPBIT_AUTO_DIAGNOSIS='true'
$env:UPBIT_PERFORMANCE_OPTIMIZATION='true'
```

```bash
# Bash에서
export UPBIT_LLM_BRIEFING_ENABLED=true
export UPBIT_AUTO_DIAGNOSIS=true
export UPBIT_PERFORMANCE_OPTIMIZATION=true
```

### 2. 기본 사용법

```python
from upbit_auto_trading.infrastructure.logging import get_enhanced_logging_service

# 로깅 서비스 초기화
logging_service = get_enhanced_logging_service()

# 일반 로그 사용 (기존과 동일)
logger = logging_service.get_logger("MyComponent")
logger.info("시스템 시작됨")
logger.warning("설정 파일 누락")
logger.error("데이터베이스 연결 실패")

# LLM 브리핑 및 대시보드가 자동으로 업데이트됩니다
```

### 3. 생성되는 파일들

시스템이 자동으로 생성하는 파일들:

- `logs/llm_agent_briefing.md`: LLM 에이전트용 실시간 브리핑
- `logs/llm_agent_dashboard.json`: 구조화된 시스템 상태 데이터
- `logs/upbit_auto_trading_YYYYMMDD_HHMMSS_PIDXXXXX.log`: 기존 로그 파일

## 📊 LLM 브리핑 시스템

### 브리핑 파일 구조

생성되는 `llm_agent_briefing.md` 파일은 다음과 같은 구조를 가집니다:

```markdown
# 🤖 LLM 에이전트 시스템 브리핑

## 📊 시스템 상태 요약
- **전체 상태**: OK/WARNING/ERROR/CRITICAL
- **마지막 업데이트**: 2025-08-06 12:30:00
- **가동 시간**: 2시간 15분

## 🔍 컴포넌트 상태
### ✅ 정상 작동 (3개)
- MainWindow: 정상 작동
- DatabaseManager: DB 연결 성공
- ThemeService: 테마 적용 완료

### ⚠️ 주의 필요 (2개)
- ConfigManager: 설정 파일 일부 누락
- CacheService: 메모리 사용량 증가

## 🚨 주요 문제점
### 높은 우선순위 (1개)
- **DI_Container**: Application Container를 찾을 수 없음
  - 예상 해결 시간: 15분
  - 권장 액션: ApplicationContext 초기화 순서 확인

## 💡 권장 액션
1. DI Container 초기화 순서 확인
2. 설정 파일 유효성 검사
3. 메모리 사용량 모니터링
```

### 브리핑 업데이트 방식

- **자동 업데이트**: 시스템 상태 변경 시 자동으로 업데이트
- **수동 업데이트**: 필요시 강제 업데이트 가능
- **업데이트 간격**: 기본 30초 (설정 가능)

## 📈 JSON 대시보드 시스템

### 대시보드 데이터 구조

`llm_agent_dashboard.json` 파일의 구조:

```json
{
  "timestamp": "2025-08-06T12:30:00",
  "system_health": "WARNING",
  "components_summary": {
    "OK": 5,
    "WARNING": 2,
    "ERROR": 1,
    "LIMITED": 0,
    "UNKNOWN": 0
  },
  "active_issues": [
    {
      "id": "di_container_missing_1234567890",
      "type": "di_container_missing",
      "severity": "HIGH",
      "message": "Application Container를 찾을 수 없음",
      "detected_at": "2025-08-06T12:29:45",
      "component": "DI_Container",
      "suggested_actions": [
        "ApplicationContext 초기화 순서 확인",
        "DI Container 등록 로직 검토"
      ],
      "estimated_fix_time": 15
    }
  ],
  "performance_metrics": {
    "total_issues": 3,
    "urgent_issues": 1,
    "estimated_fix_time_minutes": 45,
    "issue_rate": 33.33,
    "system_uptime_status": "DEGRADED"
  },
  "recommendations": [
    "🚨 긴급: 1개의 HIGH 우선순위 문제를 먼저 해결하세요",
    "🔧 DI_Container 컴포넌트에 문제가 집중되어 있습니다"
  ],
  "quick_actions": [
    {
      "label": "Fix: DI_Container",
      "action": "ApplicationContext 초기화 순서 확인",
      "severity": "HIGH"
    }
  ]
}
```

## 🔧 고급 설정

### 설정 파일 커스터마이징

`config/enhanced_logging_config.yaml` 파일을 통해 상세 설정 가능:

```yaml
# LLM 브리핑 설정
briefing:
  enabled: true
  update_interval: 30  # 초 단위
  file_path: "logs/llm_agent_briefing.md"
  max_issues_display: 10

# 대시보드 설정
dashboard:
  enabled: true
  file_path: "logs/llm_agent_dashboard.json"
  auto_refresh: true

# 성능 최적화 설정
performance:
  async_processing: true
  memory_threshold_mb: 500
  cache_size: 1000
  monitoring_interval: 10  # 초 단위

# 자동 진단 설정
auto_diagnosis:
  enabled: true
  detection_patterns:
    - name: "di_container_missing"
      pattern: "Application Container.*찾을 수 없음"
      severity: "HIGH"
      category: "DI"
```

### 프로그래밍 API

#### 수동 브리핑 업데이트

```python
from upbit_auto_trading.infrastructure.logging.briefing import LLMBriefingService

briefing_service = LLMBriefingService(config)

# 컴포넌트 상태 수동 업데이트
briefing_service.status_tracker.update_component_status(
    "MyComponent", "ERROR", "특정 오류 발생"
)

# 브리핑 파일 강제 업데이트
briefing_service.update_briefing_file()
```

#### 대시보드 시나리오 시뮬레이션

```python
from upbit_auto_trading.infrastructure.logging.dashboard import DashboardService

dashboard_service = DashboardService()

# 테스트 시나리오 실행
dashboard_data = dashboard_service.simulate_issue_scenario("critical_system")
print(f"시스템 상태: {dashboard_data.system_health}")
```

#### 성능 모니터링

```python
from upbit_auto_trading.infrastructure.logging.performance import PerformanceMonitor

monitor = PerformanceMonitor()
monitor.start_monitoring()

# 커스텀 메트릭 기록
monitor.record_metric("api_response_time", 125.5, "performance")

# 성능 리포트 생성
report = monitor.generate_performance_report(duration_hours=1.0)
```

## 🛠️ 문제 해결

### 일반적인 문제들

#### 1. 브리핑 파일이 생성되지 않음

**원인**: 환경변수가 설정되지 않았거나 권한 문제

**해결방법**:
```powershell
# 환경변수 확인
echo $env:UPBIT_LLM_BRIEFING_ENABLED

# 로그 디렉토리 권한 확인
mkdir logs -Force
```

#### 2. 대시보드 JSON이 업데이트되지 않음

**원인**: 자동 업데이트 시스템이 비활성화됨

**해결방법**:
```python
# 수동 업데이트
dashboard_service = DashboardService()
dashboard_service.update_dashboard()
```

#### 3. 성능 저하 발생

**원인**: 메모리 사용량 증가 또는 캐시 오버플로우

**해결방법**:
```python
# 메모리 최적화 실행
from upbit_auto_trading.infrastructure.logging.performance import MemoryOptimizer

optimizer = MemoryOptimizer()
optimizer.force_garbage_collection()
optimizer.clear_caches()
```

### 로그 레벨별 동작

| 로그 레벨 | 브리핑 업데이트 | 대시보드 업데이트 | 우선순위 처리 |
|-----------|-----------------|-------------------|---------------|
| DEBUG     | ❌              | ❌                | ❌            |
| INFO      | ✅              | ✅                | 낮음          |
| WARNING   | ✅              | ✅                | 중간          |
| ERROR     | ✅              | ✅                | 높음          |
| CRITICAL  | ✅              | ✅                | 최고          |

## 🔄 이전 버전과의 호환성

### v3.0/v3.1과의 동시 사용

v4.0 시스템은 기존 v3.0 및 v3.1 로깅 시스템과 완전히 호환됩니다:

```python
# 기존 방식 (계속 작동)
from upbit_auto_trading.logging import get_smart_log_manager
smart_logger = get_smart_log_manager()

# 새로운 방식 (추가 기능)
from upbit_auto_trading.logging import get_enhanced_logging_service
enhanced_service = get_enhanced_logging_service()
```

### 마이그레이션 가이드

기존 시스템에서 v4.0으로 점진적 마이그레이션:

1. **Phase 1**: 환경변수 설정으로 새 시스템 활성화
2. **Phase 2**: 기존 로깅 코드는 그대로 유지
3. **Phase 3**: 필요에 따라 새로운 API 점진적 도입

## 📚 추가 리소스

### 관련 문서

- `docs/COMPONENT_ARCHITECTURE.md`: 시스템 아키텍처 상세 설명
- `docs/ERROR_HANDLING_POLICY.md`: 오류 처리 정책
- `docs/INFRASTRUCTURE_SMART_LOGGING_GUIDE.md`: 기존 로깅 시스템 가이드

### 예제 코드

전체 예제는 다음 테스트 파일들을 참조하세요:

- `test_task_2_1_briefing_system.py`: 브리핑 시스템 예제
- `test_task_2_2_dashboard_system.py`: 대시보드 시스템 예제
- `test_task_3_1_performance_optimization.py`: 성능 최적화 예제
- `test_task_3_2_integration_test.py`: 통합 시스템 예제

### 지원 및 문의

시스템 관련 문의나 문제 발생 시:

1. 먼저 생성된 브리핑 파일(`logs/llm_agent_briefing.md`) 확인
2. 대시보드 데이터(`logs/llm_agent_dashboard.json`)에서 권장 액션 검토
3. 이 가이드의 문제 해결 섹션 참조

---

**LLM 에이전트 로깅 시스템 v4.0**
자동화된 지능형 로깅으로 더 나은 시스템 모니터링을 경험하세요! 🚀
