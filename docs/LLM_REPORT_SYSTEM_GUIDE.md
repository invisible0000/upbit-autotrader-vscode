# 🤖 LLM_REPORT 시스템 완전 가이드

> **목적**: LLM 에이전트가 시스템 상태를 실시간으로 모니터링하고 분석할 수 있는 구조화된 로깅 시스템
> **대상**: LLM 에이전트, 개발자, 시스템 관리자
> **갱신**: 2025-08-06

## 🎯 시스템 개요

**LLM_REPORT**는 기존 로그와 달리 **LLM 에이전트가 시스템을 이해하기 위한 전용 보고 시스템**입니다.

### 📊 기본 구조
```python
🤖 LLM_REPORT: Operation={작업명}, Status={상태}, Details={상세정보}
```

### 🔍 일반 로그와의 차이점
| 구분 | 일반 로그 | LLM_REPORT |
|------|-----------|------------|
| **목적** | 디버깅, 감사 | LLM 이해 및 분석 |
| **형식** | 자유형식 | 고정 3-파라미터 구조 |
| **정보밀도** | 중간 | 높음 (정량적 데이터 포함) |
| **자동분석** | 어려움 | 쉬움 |

## 🚀 구현된 컴포넌트들

### 1. **MainWindow** (기존 완성)
```python
🤖 LLM_REPORT: Operation=NavigationBar_DI, Status=SUCCESS, Details=DI Container 기반 주입 완료
🤖 LLM_REPORT: Operation=화면_전환_요청, Status=strategy, Details=
🤖 LLM_REPORT: Operation=위젯_업데이트, Status=성공, Details=
```

### 2. **StrategyManagementScreen** (신규 추가)
```python
🤖 LLM_REPORT: Operation=StrategyScreen_초기화, Status=시작, Details=전략 관리 화면 생성
🤖 LLM_REPORT: Operation=TriggerBuilder_탭_생성, Status=성공, Details=컴포넌트 로드 완료
🤖 LLM_REPORT: Operation=StrategyMaker_탭_생성, Status=성공, Details=전략 메이커 UI 초기화 완료
```

### 3. **TriggerBuilderScreen** (신규 추가)
```python
🤖 LLM_REPORT: Operation=TriggerBuilder_초기화, Status=시작, Details=컴포넌트 기반 트리거 빌더 생성
🤖 LLM_REPORT: Operation=시뮬레이션_엔진, Status=초기화_완료, Details=embedded 엔진 로드 성공
🤖 LLM_REPORT: Operation=트리거_목록_로드, Status=성공, Details=TriggerListWidget 위임 완료
🤖 LLM_REPORT: Operation=시뮬레이션_실행, Status=시작, Details=시나리오: BTC_RSI_Strategy
```

## 💡 활용 시나리오

### **시나리오 1: 성능 문제 진단**
```log
🤖 LLM_REPORT: Operation=차트_렌더링, Status=SLOW, Details=렌더링 시간 5.2초 (임계값 2초 초과)
🤖 LLM_REPORT: Operation=데이터_쿼리, Status=SUCCESS, Details=1000개 데이터 조회, 0.1초
```
→ **LLM 결론**: 차트 렌더링 로직 최적화 필요, 데이터 조회는 정상

### **시나리오 2: 사용자 행동 패턴 분석**
```log
🤖 LLM_REPORT: Operation=사용자_행동, Status=PATTERN, Details=RSI 조건을 5번 연속 수정
🤖 LLM_REPORT: Operation=UI_개선_제안, Status=INSIGHT, Details=RSI 프리셋 기능 필요
```
→ **LLM 결론**: RSI 조건 설정 UI를 개선하여 프리셋 기능 추가 권장

### **시나리오 3: 시스템 장애 추적**
```log
🤖 LLM_REPORT: Operation=조건_검증, Status=FAILURE, Details=RSI 파라미터 누락
🤖 LLM_REPORT: Operation=백테스팅_시작, Status=BLOCKED, Details=조건 검증 실패로 중단
```
→ **LLM 결론**: RSI 파라미터 검증 로직 강화 필요

## 🛠️ 구현 가이드

### **기본 패턴**
```python
class YourScreen(QWidget):
    def __init__(self):
        self.logger = get_integrated_logger("YourComponent")
        self._log_llm_report("초기화", "시작", "컴포넌트 생성")

    def _log_llm_report(self, operation: str, status: str, details: str = "") -> None:
        """LLM 에이전트 구조화된 보고"""
        if self.logger:
            self.logger.info(f"🤖 LLM_REPORT: Operation={operation}, Status={status}, Details={details}")
        else:
            print(f"🤖 LLM_REPORT: Operation={operation}, Status={status}, Details={details}")
```

### **Operation 명명 규칙**
- **컴포넌트_작업**: `TriggerBuilder_초기화`, `Chart_렌더링`
- **작업_세부사항**: `시뮬레이션_실행`, `데이터_로드`
- **사용자_행동**: `사용자_클릭`, `조건_수정`

### **Status 표준값**
- **성공**: `SUCCESS`, `완료`, `성공`
- **진행**: `IN_PROGRESS`, `진행중`, `시작`
- **실패**: `FAILURE`, `ERROR`, `실패`, `오류`
- **경고**: `WARNING`, `SLOW`, `경고`
- **분석**: `PATTERN`, `INSIGHT`, `ALERT`

### **Details 작성 가이드**
```python
# ✅ 좋은 예시
Details="RSI=75.2, 매도신호 발생, 수익률=+3.5%"
Details="렌더링 시간 2.1초, 데이터 포인트 1000개"
Details="사용자가 RSI 임계값을 70→80으로 변경"

# ❌ 나쁜 예시
Details="작업 완료"
Details="에러 발생"
Details="처리중"
```

## 📈 확장 계획

### **Phase 1: 완료** ✅
- MainWindow, StrategyManagementScreen, TriggerBuilderScreen

### **Phase 2: 계획** 🔄
- MonitoringAlertsScreen (실시간 데이터 추적)
- BacktestingScreen (성능 메트릭 모니터링)
- DashboardScreen (전체 시스템 상태)

### **Phase 3: 고도화** 🚀
- 자동 성능 분석 리포트
- 사용자 패턴 기반 UI 최적화 제안
- 실시간 시스템 건강도 모니터링

## 🔍 LLM 에이전트 활용법

### **실시간 모니터링**
```bash
# 환경변수로 LLM_REPORT만 필터링
export UPBIT_CONSOLE_OUTPUT=true
export UPBIT_COMPONENT_FOCUS="LLM_REPORT"
```

### **특정 기능 집중 분석**
```python
with logging_service.feature_development_context("STRATEGY_BUILDING"):
    # 전략 생성 과정 상세 추적
    self._log_llm_report("전략_생성", "시작", "RSI 기반 전략")
```

### **성능 임계값 모니터링**
```python
def monitor_performance(self, operation_time, threshold=2.0):
    status = "SLOW" if operation_time > threshold else "SUCCESS"
    self._log_llm_report("성능_모니터링", status, f"소요시간 {operation_time:.1f}초")
```

## 📚 관련 문서

- [Infrastructure Layer 스마트 로깅](../docs/INFRASTRUCTURE_LOGGING.md): 기반 로깅 시스템
- [MainWindow 구현](../upbit_auto_trading/ui/desktop/main_window.py): 기존 LLM_REPORT 구현 예시
- [개발 체크리스트](DEV_CHECKLIST.md): LLM_REPORT 구현 검증 기준

---

**💡 핵심**: LLM_REPORT는 단순한 로그가 아닌 **LLM 에이전트의 눈과 귀** 역할을 하는 지능형 모니터링 시스템입니다!
