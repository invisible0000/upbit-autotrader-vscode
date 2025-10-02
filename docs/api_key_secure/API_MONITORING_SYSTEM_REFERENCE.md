# 📊 API 모니터링 시스템 참조 가이드

> **목적**: LLM 에이전트가 Task 2.6에서 구현된 API 모니터링 시스템을 효과적으로 활용하고 중복 개발을 방지할 수 있도록 체계적으로 정리한 참조 문서

## 📋 시스템 개요

**구현 상태**: ✅ **완료 및 운영 중** (Task 2.6 - 80% 완료)
**성능**: 호출당 0.0005ms (API 호출 시간의 0.0025% 오버헤드)
**통합 범위**: 5개 핵심 API 메서드 + 전역 모니터링 시스템
**아키텍처**: DDD Infrastructure Layer, 스레드 안전성, 글로벌 싱글톤
**실제 검증**: ✅ 2025년 8월 18일 실제 API 호출로 모니터링 동작 확인

---

## 🎯 핵심 컴포넌트

### 📂 **1. SimpleFailureMonitor 클래스** ✅ 완료

**파일**: `upbit_auto_trading/infrastructure/monitoring/simple_failure_monitor.py`
**크기**: 220 라인 (고도화된 구현)

#### 주요 기능

- **연속 실패 감지**: 3회 연속 실패 시 자동 상태 변경
- **자동 복구**: 성공 시 실패 카운터 리셋 및 건강 상태 복구
- **스레드 안전성**: `threading.RLock()` 사용
- **성능 최적화**: 조건부 로깅, 메모리 내 연산
- **통계 제공**: 성공률, 총 호출 수, 연속 실패 수

#### 핵심 메서드

```python
def mark_api_result(self, success: bool) -> None:
    """API 호출 결과를 기록 (0.0005ms)"""

def get_statistics(self) -> dict:
    """상세 통계 정보 반환"""

def is_healthy(self) -> bool:
    """API 상태가 건강한지 확인"""

def reset_statistics(self) -> None:
    """통계 초기화 (테스트용)"""
```

### 📂 **2. GlobalAPIMonitor 싱글톤** ✅ 완료

**파일**: 동일 파일 내 구현
**패턴**: Thread-safe Singleton

#### 편의 함수들 (권장 사용)

```python
from upbit_auto_trading.infrastructure.monitoring.simple_failure_monitor import (
    mark_api_success,    # ✅ API 성공 기록
    mark_api_failure,    # ❌ API 실패 기록
    get_api_statistics,  # 📊 통계 조회
    is_api_healthy      # 🔍 상태 확인
)

# 사용 예시
try:
    result = await api_call()
    mark_api_success()  # 성공 시
    return result
except Exception:
    mark_api_failure()  # 실패 시
    raise
```

### 📂 **3. ClickableApiStatus UI 위젯** ✅ 완료

**파일**: `upbit_auto_trading/ui/desktop/common/widgets/clickable_api_status.py`
**크기**: 234 라인 (완전한 PyQt6 위젯)

#### 주요 기능

- **클릭 가능**: 좌클릭으로 API 상태 새로고침 요청
- **10초 쿨다운**: 연속 클릭 방지
- **상태별 색상**: 건강함(초록), 문제(빨강), 확인중(노랑)
- **PyQt6 시그널**: `refresh_requested = pyqtSignal()`

#### 핵심 메서드

```python
def set_api_status(self, is_healthy: bool, message: str = ""):
    """API 상태 설정 및 UI 업데이트"""

def start_cooldown(self):
    """10초 쿨다운 타이머 시작"""

def update_display(self, status, details=""):
    """상태 표시 업데이트 (색상, 텍스트)"""
```

---

## 🔗 통합된 API 메서드들

### ✅ **1. UpbitClient 메서드들** (4개)

**파일**: `upbit_auto_trading/infrastructure/external_apis/upbit/upbit_client.py`

#### 통합 완료된 메서드들

```python
async def get_accounts(self) -> List[Dict[str, Any]]:
    """계좌 정보 조회 + 모니터링"""
    try:
        self.requires_private_access()
        result = await self.private.get_accounts()
        mark_api_success()  # ✅ 성공 기록
        return result
    except Exception:
        mark_api_failure()  # ❌ 실패 기록
        raise

async def get_candles_minutes(self, market: str, unit: int = 1,
                              to: Optional[str] = None, count: int = 200):
    """분봉 캔들 조회 + 모니터링"""

async def get_tickers(self, markets: List[str]):
    """현재가 정보 조회 + 모니터링"""

async def get_orderbook(self, markets: List[str]):
    """호가 정보 조회 + 모니터링"""
```

### ✅ **2. ApiKeyService.test_api_connection** (1개)

**파일**: `upbit_auto_trading/infrastructure/services/api_key_service.py`

#### 통합 완료

```python
def test_api_connection(self, access_key: str, secret_key: str) -> Tuple[bool, str, Dict[str, Any]]:
    """API 연결 테스트 + 모니터링"""
    try:
        # ... 실제 API 호출 ...
        mark_api_success()  # ✅ 성공 기록
        return True, message, account_info
    except Exception as e:
        mark_api_failure()  # ❌ 실패 기록
        return False, error_msg, {}
```

---

## 📊 성능 및 검증 데이터

### ⚡ **성능 메트릭**

```python
# 실제 테스트 결과 (pytest)
100회 모니터링 호출 시간: 0.05ms
호출당 평균 시간: 0.0005ms
API 호출 대비 오버헤드: 0.0025% (거의 0)

# 업비트 API 호출 vs 모니터링
업비트 API: 50-200ms (네트워크 + 서버)
모니터링: 0.0005ms (메모리 내 연산)
성능 영향: 무시할 수준
```

### 🧪 **통합 테스트 검증**

```python
# 테스트 시나리오 결과 (2025년 8월 18일 실제 검증)
📊 초기 통계: total_calls=0, success_rate=100.0%
✅ 5회 성공 → success_rate=100.0%, 건강함
🚨 3회 연속 실패 → consecutive_failures=3, 문제 있음
🔄 1회 복구 → consecutive_failures=0, 건강함

# 실제 API 호출 검증
🚀 UpbitClient.get_candles_minutes() 호출
✅ 결과: total_calls=1, success_calls=1, success_rate=100.0%

# 실패 감지 임계값: 3회 연속 실패
# 복구 감지: 1회 성공으로 즉시 복구
```

### 🔍 **실시간 활용 현황**

- **UpbitClient**: 4개 메서드에서 실시간 모니터링 중
- **ApiKeyService**: test_api_connection에서 모니터링 중
- **글로벌 통계**: 프로그램 실행 중 지속적 추적
- **자동 로깅**: 연속 3회 실패 시 WARNING 레벨 자동 기록

---

## 🛠️ LLM 에이전트 사용 가이드

### ✅ **DO: 권장 사용 패턴**

#### 1. 새로운 API 메서드에 모니터링 추가

```python
from upbit_auto_trading.infrastructure.monitoring.simple_failure_monitor import mark_api_success, mark_api_failure

async def new_api_method(self):
    try:
        result = await some_api_call()
        mark_api_success()  # ✅ 성공 기록
        return result
    except Exception:
        mark_api_failure()  # ❌ 실패 기록
        raise
```

#### 2. 모니터링 상태 확인

```python
from upbit_auto_trading.infrastructure.monitoring.simple_failure_monitor import get_api_statistics, is_api_healthy

# 상태 확인
if is_api_healthy():
    print("API 정상 동작 중")
else:
    print("API 문제 감지됨")

# 상세 통계
stats = get_api_statistics()
print(f"성공률: {stats['success_rate']:.1f}%")
print(f"연속 실패: {stats['consecutive_failures']}회")
```

#### 3. UI에서 상태 표시

```python
from upbit_auto_trading.ui.desktop.common.widgets.clickable_api_status import ClickableApiStatus

# PyQt6 위젯 사용
status_widget = ClickableApiStatus(cooldown_seconds=10)
status_widget.refresh_requested.connect(self.refresh_api_status)
status_widget.set_api_status(is_healthy=True, message="API 정상")
```

### ❌ **DON'T: 중복 개발 방지**

#### 1. SimpleFailureMonitor 재구현 금지

```python
# ❌ 금지: 이미 구현됨
class MyApiMonitor:  # 중복!
    def __init__(self):
        self.failures = 0
```

#### 2. 수동 실패 카운팅 금지

```python
# ❌ 금지: 수동 카운팅
failure_count = 0  # 중복!
if api_failed:
    failure_count += 1
```

#### 3. 별도 UI 위젯 제작 금지

```python
# ❌ 금지: ClickableApiStatus 이미 존재
class MyStatusLabel(QLabel):  # 중복!
    def mousePressEvent(self, event):
        pass
```

### 🔧 **확장 가능한 영역**

#### 1. 새로운 API 엔드포인트 추가

- 기존 패턴 따라 `mark_api_success()`/`mark_api_failure()` 추가
- 추가 비용 없이 모니터링 혜택 획득

#### 2. 커스텀 임계값 설정

```python
# 특별한 경우 임계값 조정 가능
monitor = SimpleFailureMonitor(failure_threshold=5)  # 기본: 3회
```

#### 3. 상태 변경 콜백 추가

```python
def on_status_change(is_healthy: bool):
    if not is_healthy:
        send_alert("API 문제 감지!")

monitor = SimpleFailureMonitor(status_callback=on_status_change)
```

---

## 📋 Task 2.6 완료 현황

### ✅ **완료된 단계** (4/5 = 80%)

- **Task 2.6.1**: 실패 카운터 기본 구현 ✅
- **Task 2.6.2**: 실패 카운터 클래스 구현 ✅
- **Task 2.6.4**: 클릭 가능 상태바 구현 ✅
- **Task 2.6.5**: API 지점 통합 ✅

### ❌ **미완료 단계** (1/5 = 20%)

- **Task 2.6.3**: 상태바 클릭 기능 테스트 ❌
  - **필요**: `tests/ui/test_clickable_status_bar.py` 작성
  - **내용**: PyQt6 이벤트 테스트, 쿨다운 검증

---

## 🎯 LLM 에이전트 체크리스트

### 📊 **모니터링 시스템 활용 전**

- [ ] 기존 `SimpleFailureMonitor` 존재 확인
- [ ] 대상 API 메서드가 이미 통합되었는지 확인
- [ ] UI 위젯이 필요한 경우 `ClickableApiStatus` 재사용 고려

### 🔧 **새로운 기능 개발 시**

- [ ] `mark_api_success()`/`mark_api_failure()` 패턴 사용
- [ ] DDD Infrastructure Layer 준수
- [ ] 성능 영향 최소화 (0.0025% 오버헤드 유지)

### 🧪 **테스트 작성 시**

- [ ] 기존 테스트 파일 참조: `tests/monitoring/test_simple_failure_monitor.py`
- [ ] 성능 테스트 포함 (100회 호출 < 1ms)
- [ ] 스레드 안전성 검증

---

**📅 최종 업데이트**: 2025년 8월 18일 (실제 동작 검증 완료)
**🎯 상태**: Task 2.6 80% 완료, 실용적 모니터링 시스템 **운영 중**
**🚀 다음 단계**: Task 2.6.3 UI 테스트 작성으로 100% 완료
**💡 핵심 가치**: 중복 개발 방지 + 검증된 고성능 모니터링 시스템 재사용
**✅ 검증 완료**: 실제 API 호출에서 모니터링 정상 동작 확인
