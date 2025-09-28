# 🔄 Legacy → Modern 패턴 마이그레이션 전략

## 🎯 마이그레이션 원칙

**Zero Downtime**: 기존 기능 100% 유지하며 점진적 전환
**Backward Compatible**: 과도기 동안 Legacy와 Modern 패턴 공존
**Risk Minimization**: 단계별 검증으로 회귀 방지

---

## 📋 마이그레이션 대상 분석

### 🔍 Legacy 패턴 현황

#### 1. 의존성 주입 패턴

```python
# Legacy Pattern 1: 직접 resolve() 호출
container = get_app_context().container
service = container.resolve(IService)

# Legacy Pattern 2: 수동 인스턴스 생성
service = ConcreteService()

# Legacy Pattern 3: 전역 변수 참조
from global_services import trading_service
```

#### 2. UI 이벤트 처리 패턴

```python
# Legacy Pattern: 동기 이벤트 처리
def on_button_clicked(self):
    result = self.service.process()  # UI 블록킹 위험
    self.update_ui(result)
```

#### 3. 스타일 관리 패턴

```python
# Legacy Pattern: 하드코딩된 스타일
widget.setStyleSheet("color: #333; background: #fff;")
```

### ✅ Modern 패턴 목표

#### 1. @inject 의존성 주입

```python
@inject
def __init__(
    self,
    service: IService = Provide["service"]
):
    self._service = service
```

#### 2. @asyncSlot UI 이벤트

```python
@asyncSlot()
async def on_button_clicked(self):
    result = await self._service.process_async()
    self.update_ui(result)
```

#### 3. 전역 스타일 시스템

```python
# ObjectName 기반 스타일링
widget.setObjectName("primary_button")
# CSS는 전역 스타일 파일에서 관리
```

---

## 🛠️ 단계별 마이그레이션 전략

### Phase 1: 의존성 주입 전환 전략

#### 1.1 호환성 유지 접근법

**목표**: Legacy와 Modern 패턴이 동시에 작동하도록 설계

```python
# ApplicationContainer 이중 지원 설계
class ApplicationContainer(containers.DeclarativeContainer):
    # Modern: @inject 패턴용
    strategy_service = providers.Factory(StrategyService)

    # Legacy: resolve() 지원 (임시)
    def resolve(self, service_type):
        logger.warning(f"Legacy resolve() 호출: {service_type}")
        return self._resolve_legacy(service_type)
```

#### 1.2 점진적 전환 순서

**우선순위**: 의존성 트리의 leaf 노드부터 시작

```
1. Infrastructure Services (의존성 없음)
   └── DatabaseManager, LoggingService, PathService

2. Domain Repositories (Infrastructure만 의존)
   └── StrategyRepository, TriggerRepository

3. Application Services (Repository 의존)
   └── TradingService, StrategyApplicationService

4. UI Presenters (Application Service 의존)
   └── MainWindow, WidgetPresenters
```

#### 1.3 전환 체크리스트 (서비스별)

```markdown
## Service: {ServiceName}

### 🔍 사전 점검
- [ ] 현재 의존성 목록 파악
- [ ] 순환 의존성 검증
- [ ] 테스트 코드 존재 여부

### 🔧 전환 작업
- [ ] @inject 데코레이터 추가
- [ ] Provide[] 파라미터 설정
- [ ] Container Provider 등록
- [ ] Wiring 모듈에 추가

### ✅ 전환 검증
- [ ] 단위 테스트 통과
- [ ] Integration 테스트 통과
- [ ] UI 기능 정상 동작
- [ ] 성능 저하 없음
```

### Phase 2: UI 이벤트 처리 전환 전략

#### 2.1 @asyncSlot 도입 가이드라인

**적용 기준**:

```python
# ✅ @asyncSlot 적용 대상
- 외부 API 호출이 포함된 이벤트
- 100ms 이상 소요될 수 있는 작업
- I/O 작업이 포함된 이벤트
- 에러 처리가 복잡한 이벤트

# ❌ 동기 처리 유지 대상
- 단순 UI 상태 변경
- 즉시 완료되는 계산
- 로컬 데이터 조회만
```

#### 2.2 UI 반응성 패턴

```python
# 표준 @asyncSlot 패턴
@asyncSlot()
async def on_action_triggered(self):
    try:
        # 1. UI 비활성화
        self.action_button.setEnabled(False)
        self.show_loading_indicator(True)

        # 2. 비동기 작업 수행
        result = await self._service.process_async()

        # 3. 결과 처리
        self._handle_success(result)

    except Exception as e:
        # 4. 에러 처리
        self._handle_error(e)

    finally:
        # 5. UI 복구
        self.action_button.setEnabled(True)
        self.show_loading_indicator(False)
```

#### 2.3 이벤트 루프 안전성

```python
# LoopGuard 활용 패턴
from upbit_auto_trading.infrastructure.runtime import ensure_main_loop

class ServiceClass:
    async def async_method(self):
        ensure_main_loop(
            where="ServiceClass.async_method",
            component="ServiceClass"
        )
        # 안전한 비동기 작업
```

### Phase 3: 스타일 시스템 전환 전략

#### 3.1 ObjectName 기반 스타일링

```python
# 전환 패턴
class ModernWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._apply_styles()

    def _apply_styles(self):
        # ObjectName 설정 (하드코딩 제거)
        self.primary_button.setObjectName("primary_button")
        self.secondary_button.setObjectName("secondary_button")

        # 전역 스타일 적용은 StyleManager가 처리
```

#### 3.2 테마 시스템 통합

```python
# 테마 변경 이벤트 연결
from upbit_auto_trading.ui.desktop.common.theme_notifier import ThemeNotifier

class ThemedWidget(QWidget):
    def __init__(self):
        super().__init__()
        # 테마 변경시 자동 업데이트
        ThemeNotifier.instance().theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        # 필요시 추가 스타일 적용
        pass
```

---

## 🔒 안전성 보장 메커니즘

### 1. 단계별 롤백 계획

#### Phase 1 롤백 (의존성 주입)

```python
# 긴급 롤백 시나리오
class EmergencyRollback:
    @staticmethod
    def restore_legacy_injection():
        # 1. @inject 데코레이터 비활성화
        # 2. Legacy Container.resolve() 복구
        # 3. 수동 서비스 생성으로 폴백
        pass
```

#### Phase 2 롤백 (UI 이벤트)

```python
# @asyncSlot → 동기 이벤트 폴백
def rollback_to_sync_events(self):
    # 1. @asyncSlot 제거
    # 2. await → 동기 호출 변경
    # 3. UI 블록킹 허용 (임시)
    pass
```

### 2. 실시간 모니터링

#### 성능 지표 추적

```python
class MigrationMonitor:
    def track_injection_performance(self):
        # DI 컨테이너 초기화 시간
        # 서비스 해결 속도
        # 메모리 사용량 변화
        pass

    def track_ui_responsiveness(self):
        # @asyncSlot 이벤트 처리 시간
        # UI 프리징 발생 빈도
        # 에러 발생률
        pass
```

#### 품질 게이트

```python
class QualityGate:
    def check_migration_health(self):
        checks = [
            self.verify_no_legacy_warnings(),
            self.verify_ui_responsiveness(),
            self.verify_functionality_intact(),
            self.verify_performance_maintained()
        ]
        return all(checks)
```

### 3. 자동화된 검증

#### CI/CD 통합 테스트

```powershell
# 마이그레이션 후 자동 검증
pytest tests/integration/
pytest tests/ui/
python run_desktop_ui.py --test-mode
python tools/migration_validator.py
```

#### 회귀 테스트 자동화

```python
class RegressionTester:
    def test_core_functionality(self):
        # 7규칙 전략 생성 테스트
        # 트리거 빌더 동작 테스트
        # 실시간 데이터 수신 테스트
        # API 연동 테스트
        pass
```

---

## 📊 마이그레이션 성공 지표

### 정량적 지표

#### 코드 품질

- Legacy 패턴 사용률: 0%
- @inject 적용률: 100%
- 테스트 커버리지: 80% 이상
- 코드 복잡도: 현재 대비 10% 감소

#### 성능 지표

- 애플리케이션 시작 시간: 현재 수준 유지
- UI 반응성: 100ms 이하 유지
- 메모리 사용량: 현재 대비 5% 이내
- CPU 사용률: 현재 수준 유지

#### 안정성 지표

- 크래시 발생률: 0%
- 기능 회귀: 0건
- 에러 발생률: 현재 대비 감소
- 사용자 불만: 0건

### 정성적 지표

#### 개발자 경험

- 코드 가독성 향상
- 유지보수 편의성 증대
- 새 기능 개발 속도 향상
- 디버깅 용이성 개선

#### 아키텍처 품질

- 계층 간 결합도 감소
- 테스트 가능성 증대
- 확장성 향상
- 재사용성 증대

---

## 📋 마이그레이션 체크리스트

### 사전 준비

- [ ] 현재 상태 백업 (Git branch)
- [ ] Legacy 코드 인벤토리 작성
- [ ] 우선순위 매트릭스 수립
- [ ] 롤백 계획 수립

### Phase 1 (의존성 주입)

- [ ] Infrastructure Services 전환
- [ ] Domain Repositories 전환
- [ ] Application Services 전환
- [ ] UI Presenters 전환
- [ ] Legacy 지원 코드 제거

### Phase 2 (UI 현대화)

- [ ] TriggerBuilder 컴포넌트 전환
- [ ] @asyncSlot 패턴 적용
- [ ] 전역 스타일 시스템 통합
- [ ] MVP 패턴 명확화

### Phase 3 (품질 강화)

- [ ] 로깅 패턴 통일
- [ ] 테스트 코드 작성
- [ ] 성능 모니터링 구축
- [ ] 문서 업데이트

### 완료 검증

- [ ] 모든 테스트 통과
- [ ] 성능 지표 만족
- [ ] 품질 게이트 통과
- [ ] 사용자 승인

---

**🎯 핵심 성공 요인**: 점진적 접근 + 안전성 우선 + 지속적 검증
