# LLM 에이전트 로깅 시스템 설계 문서

## 개요

기존 스마트 로깅 시스템 v3.1을 기반으로 LLM 에이전트가 실시간으로 애플리케이션 상태를 파악하고 효율적으로 문제를 해결할 수 있는 통합 로깅 시스템을 설계합니다.

## 시스템 아키텍처

### 전체 구조
```
Infrastructure Layer - Enhanced Smart Logging v4.0
├── Real-time LLM Briefing System
├── Terminal Integration Module
├── Structured LLM_REPORT Engine
├── Auto-Diagnosis Dashboard
└── Performance Optimization Layer
```

### 핵심 컴포넌트

#### 1. Real-time LLM Briefing System
**위치**: `upbit_auto_trading/infrastructure/logging/briefing/`

**책임**:
- LLM 에이전트용 실시간 상태 요약 생성
- 우선순위별 문제 목록 관리
- 다음 액션 추천 시스템

**구현 클래스**:
```python
class LLMBriefingService:
    """LLM 에이전트를 위한 실시간 브리핑 시스템"""

    def __init__(self, config: BriefingConfig):
        self.config = config
        self.status_tracker = SystemStatusTracker()
        self.issue_analyzer = IssueAnalyzer()
        self.action_recommender = ActionRecommender()

    def generate_briefing(self) -> LLMBriefing:
        """실시간 브리핑 생성"""
        pass

    def update_status(self, component: str, status: ComponentStatus):
        """컴포넌트 상태 업데이트"""
        pass

    def add_issue(self, issue: SystemIssue):
        """문제 추가 및 우선순위 분석"""
        pass
```

**출력 파일**: `logs/llm_agent_briefing.md`
```markdown
# 🤖 LLM 에이전트 브리핑 (실시간)

## 📊 시스템 상태 (2025-08-06 14:30:15)

### 🟢 정상 동작 컴포넌트
- MainWindow: ✅ 초기화 완료 (2.3초)
- DatabaseManager: ✅ 3-DB 연결 성공
- MVP Container: ✅ Mock 모드 (제한적 기능)

### ⚠️ 주의 필요 (우선순위순)

1. **[HIGH] DI Container 누락**
   - 문제: Application Container를 찾을 수 없음
   - 영향: MVP 패턴 제한적 동작
   - 추천 액션: ApplicationContext 초기화 순서 확인
   - 예상 시간: 15분

2. **[MEDIUM] ThemeService 충돌**
   - 문제: PyQt6 metaclass 충돌
   - 영향: 테마 설정 폴백 모드
   - 추천 액션: DI Container 통합 방식 변경
   - 예상 시간: 30분

### 📈 성능 메트릭
- 실행 시간: 2.3초 (목표: <3초) ✅
- 메모리 사용: 145MB (목표: <200MB) ✅
- 로그 처리: 23ms/entry (목표: <50ms) ✅

### 🎯 다음 권장 액션
1. DI Container 초기화 순서 분석 (우선순위: 높음)
2. ThemeService 호환성 검토 (우선순위: 중간)
3. MVP 패턴 실제 통합 테스트 (우선순위: 낮음)
```

#### 2. Terminal Integration Module
**위치**: `upbit_auto_trading/infrastructure/logging/terminal/`

**책임**:
- 터미널 출력 실시간 캡처
- 로그 레벨별 구조화 파싱
- LLM 로그와 터미널 동기화

**구현 클래스**:
```python
class TerminalIntegrationHandler:
    """터미널과 로그 파일의 통합 관리"""

    def __init__(self, config: TerminalConfig):
        self.config = config
        self.terminal_capturer = TerminalCapturer()
        self.parser = TerminalOutputParser()
        self.synchronizer = LogSynchronizer()

    def setup_terminal_capture(self):
        """터미널 출력 캡처 설정"""
        pass

    def parse_terminal_output(self, output: str) -> ParsedOutput:
        """터미널 출력 구조화 파싱"""
        pass

    def sync_to_llm_log(self, parsed_output: ParsedOutput):
        """LLM 로그 파일에 동기화"""
        pass
```

**파싱 규칙**:
```python
TERMINAL_PARSING_PATTERNS = {
    'warning': r'WARNING.*?(\w+).*?-.*?(.+)',
    'error': r'ERROR.*?(\w+).*?-.*?(.+)',
    'info': r'INFO.*?(\w+).*?-.*?(.+)',
    'llm_report': r'🤖 LLM_REPORT: Operation=(\w+), Status=(\w+), Details=(.+)',
    'performance': r'⏱️.*?(\d+\.?\d*).*?(초|ms)',
    'status': r'(✅|⚠️|❌).*?(.+)'
}
```

#### 3. Enhanced LLM_REPORT Engine
**위치**: `upbit_auto_trading/infrastructure/logging/reporting/`

**책임**:
- 구조화된 LLM_REPORT 생성 강화
- 컴포넌트별 Operation 태그 관리
- JSON/Markdown 형식 동시 지원

**구현 클래스**:
```python
class EnhancedLLMReportEngine:
    """강화된 LLM 보고 시스템"""

    def __init__(self, config: ReportConfig):
        self.config = config
        self.report_formatter = ReportFormatter()
        self.operation_classifier = OperationClassifier()
        self.metadata_enricher = MetadataEnricher()

    def create_report(self, operation: str, status: str, details: str,
                     context: Optional[Dict] = None) -> LLMReport:
        """구조화된 LLM 보고서 생성"""
        pass

    def enrich_with_metadata(self, report: LLMReport) -> EnhancedLLMReport:
        """메타데이터로 보고서 강화"""
        pass
```

**보고서 형식**:
```python
@dataclass
class EnhancedLLMReport:
    """강화된 LLM 보고서"""
    timestamp: datetime
    operation: str
    component: str
    status: str
    details: str
    priority: Priority  # HIGH, MEDIUM, LOW
    category: str  # MVP, DI, UI, DB, PERF
    metadata: Dict[str, Any]
    suggested_actions: List[str]
    estimated_time: int  # 해결 예상 시간(분)
    related_issues: List[str]
```

#### 4. Auto-Diagnosis Dashboard
**위치**: `upbit_auto_trading/infrastructure/logging/dashboard/`

**책임**:
- 실시간 시스템 상태 모니터링
- 자동 문제 진단 및 분석
- LLM 에이전트용 대시보드 생성

**구현 클래스**:
```python
class AutoDiagnosisDashboard:
    """자동 진단 대시보드"""

    def __init__(self, config: DashboardConfig):
        self.config = config
        self.status_monitor = SystemStatusMonitor()
        self.issue_detector = IssueDetector()
        self.dashboard_generator = DashboardGenerator()

    def generate_dashboard(self) -> Dashboard:
        """실시간 대시보드 생성"""
        pass

    def detect_issues(self) -> List[SystemIssue]:
        """자동 문제 감지"""
        pass

    def recommend_actions(self, issues: List[SystemIssue]) -> List[Action]:
        """해결 액션 추천"""
        pass
```

**대시보드 출력**: `logs/llm_agent_dashboard.json`
```json
{
  "timestamp": "2025-08-06T14:30:15Z",
  "system_status": {
    "overall": "WARNING",
    "components": {
      "main_window": {"status": "OK", "load_time": 2.3},
      "mvp_container": {"status": "LIMITED", "mode": "mock"},
      "di_container": {"status": "ERROR", "issue": "not_found"}
    }
  },
  "active_issues": [
    {
      "id": "di_container_missing",
      "priority": "HIGH",
      "title": "DI Container 누락",
      "description": "Application Container를 찾을 수 없어 MVP 패턴이 제한적으로 동작",
      "suggested_actions": [
        "ApplicationContext 초기화 순서 확인",
        "DI Container 등록 로직 검토"
      ],
      "estimated_time": 15
    }
  ],
  "performance_metrics": {
    "startup_time": 2.3,
    "memory_usage": 145,
    "log_processing_time": 23
  },
  "recommendations": [
    {
      "action": "fix_di_container",
      "priority": "HIGH",
      "description": "DI Container 초기화 순서 수정"
    }
  ]
}
```

#### 5. Performance Optimization Layer
**위치**: `upbit_auto_trading/infrastructure/logging/performance/`

**책임**:
- 로깅 성능 최적화
- 비동기 로그 처리
- 메모리 사용량 모니터링

**구현 클래스**:
```python
class PerformanceOptimizer:
    """로깅 성능 최적화"""

    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.async_processor = AsyncLogProcessor()
        self.memory_monitor = MemoryMonitor()
        self.batch_processor = BatchProcessor()

    def optimize_logging(self):
        """로깅 성능 최적화"""
        pass

    def monitor_performance(self) -> PerformanceMetrics:
        """성능 메트릭 모니터링"""
        pass
```

## 데이터 플로우

### 1. 로그 생성 플로우
```
Component Event → Logger → Terminal Integration →
LLM Report Engine → Briefing System → Dashboard Update
```

### 2. 문제 감지 플로우
```
Error/Warning → Auto Diagnosis → Issue Classification →
Priority Assignment → Action Recommendation → Dashboard Update
```

### 3. LLM 에이전트 워크플로우
```
Dashboard Check → Issue Analysis → Action Selection →
Implementation → Verification → Results Update
```

## 파일 구조

### 새로운 로깅 파일들
```
logs/
├── llm_agent_briefing.md          # 실시간 브리핑 (Markdown)
├── llm_agent_dashboard.json       # 구조화된 대시보드 (JSON)
├── terminal_capture.log           # 터미널 출력 캡처
├── enhanced_llm_reports.log       # 강화된 LLM 보고서
├── performance_metrics.json       # 성능 메트릭
└── auto_diagnosis.log             # 자동 진단 로그
```

### Infrastructure 코드 구조
```
upbit_auto_trading/infrastructure/logging/
├── __init__.py                     # 통합 진입점
├── briefing/
│   ├── __init__.py
│   ├── briefing_service.py
│   ├── status_tracker.py
│   └── action_recommender.py
├── terminal/
│   ├── __init__.py
│   ├── terminal_capturer.py
│   ├── output_parser.py
│   └── log_synchronizer.py
├── reporting/
│   ├── __init__.py
│   ├── enhanced_report_engine.py
│   ├── operation_classifier.py
│   └── metadata_enricher.py
├── dashboard/
│   ├── __init__.py
│   ├── dashboard_service.py
│   ├── issue_detector.py
│   └── dashboard_generator.py
├── performance/
│   ├── __init__.py
│   ├── performance_optimizer.py
│   ├── async_processor.py
│   └── memory_monitor.py
└── configuration/
    ├── enhanced_config.py
    └── environment_manager.py
```

## 환경변수 설정

### 새로운 환경변수
```python
# LLM 브리핑 시스템
UPBIT_LLM_BRIEFING_ENABLED=true
UPBIT_BRIEFING_UPDATE_INTERVAL=5  # 초
UPBIT_BRIEFING_MAX_ISSUES=10

# 터미널 통합
UPBIT_TERMINAL_CAPTURE=true
UPBIT_TERMINAL_BUFFER_SIZE=1000
UPBIT_TERMINAL_SYNC_INTERVAL=1

# 자동 진단
UPBIT_AUTO_DIAGNOSIS=true
UPBIT_DIAGNOSIS_DEPTH=3
UPBIT_AUTO_RECOMMENDATIONS=true

# 성능 최적화
UPBIT_ASYNC_LOGGING=true
UPBIT_BATCH_SIZE=50
UPBIT_MEMORY_THRESHOLD=200  # MB
```

## 통합 설정 클래스

```python
@dataclass
class EnhancedLoggingConfig:
    """강화된 로깅 시스템 설정"""

    # 기존 설정
    main_log_path: str = "logs/upbit_auto_trading.log"
    llm_log_path: str = "logs/upbit_auto_trading_LLM.log"

    # 새로운 설정
    briefing_enabled: bool = True
    briefing_path: str = "logs/llm_agent_briefing.md"
    briefing_update_interval: int = 5

    terminal_capture_enabled: bool = True
    terminal_capture_path: str = "logs/terminal_capture.log"

    dashboard_enabled: bool = True
    dashboard_path: str = "logs/llm_agent_dashboard.json"

    auto_diagnosis_enabled: bool = True
    performance_monitoring: bool = True

    # 성능 설정
    async_processing: bool = True
    batch_size: int = 50
    memory_threshold_mb: int = 200

    @classmethod
    def from_environment(cls) -> 'EnhancedLoggingConfig':
        """환경변수에서 설정 로드"""
        pass
```

## 기존 코드와의 통합

### 1. SmartLoggingService 확장
기존 `SmartLoggingService`에 새로운 기능을 추가:

```python
class SmartLoggingService(ILoggingService):
    def __init__(self):
        # 기존 초기화
        super().__init__()

        # 새로운 컴포넌트 초기화
        if self._config.briefing_enabled:
            self.briefing_service = LLMBriefingService(self._config)

        if self._config.terminal_capture_enabled:
            self.terminal_integration = TerminalIntegrationHandler(self._config)

        if self._config.dashboard_enabled:
            self.dashboard = AutoDiagnosisDashboard(self._config)

    def enhanced_report(self, operation: str, status: str, details: str, **kwargs):
        """강화된 LLM 보고서 생성"""
        # 기존 LLM_REPORT 생성
        super().llm_report(operation, status, details)

        # 새로운 강화 기능
        if hasattr(self, 'briefing_service'):
            self.briefing_service.process_report(operation, status, details, **kwargs)

        if hasattr(self, 'dashboard'):
            self.dashboard.update_from_report(operation, status, details, **kwargs)
```

### 2. 기존 로거 사용법 유지
개발자는 기존 방식을 그대로 사용하면서 자동으로 강화된 기능을 활용:

```python
# 기존 사용법 (변경 없음)
from upbit_auto_trading.infrastructure.logging import create_component_logger
logger = create_component_logger("MainWindow")
logger.info("🤖 LLM_REPORT: Operation=초기화, Status=완료, Details=MainWindow 로드 성공")

# 자동으로 다음이 수행됨:
# 1. 터미널에 출력
# 2. LLM 로그에 기록
# 3. 브리핑 시스템에 반영
# 4. 대시보드 업데이트
# 5. 성능 메트릭 수집
```

## 단계적 구현 계획

### Phase 1: 기반 인프라 (Week 1)
1. Enhanced 설정 시스템 구축
2. Terminal Integration Module 구현
3. 기존 시스템과의 호환성 확보

### Phase 2: 브리핑 & 대시보드 (Week 2)
1. LLM Briefing Service 구현
2. Auto-Diagnosis Dashboard 구축
3. 실시간 업데이트 시스템 구현

### Phase 3: 최적화 & 통합 (Week 3)
1. Performance Optimization Layer 구현
2. 전체 시스템 통합 테스트
3. 문서화 및 사용 가이드 작성

## 성공 지표

### 정량적 지표
- LLM 에이전트 문제 해결 시간: 현재 수동 분석 대비 70% 단축
- 로깅 시스템 성능 영향: 애플리케이션 실행 시간 증가 <10%
- 자동 진단 정확도: >85%
- 실시간 업데이트 지연: <1초

### 정성적 지표
- LLM 에이전트가 터미널 복사 없이 자동 분석 가능
- 문제 발생 시 구체적인 해결 방안 자동 제시
- 시스템 상태를 한눈에 파악할 수 있는 대시보드 제공
- 개발자와 LLM 에이전트 간의 효율적인 협업 워크플로우 구축
