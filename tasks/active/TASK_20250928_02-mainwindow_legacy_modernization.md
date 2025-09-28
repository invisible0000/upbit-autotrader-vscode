# 📋 TASK_20250928_02: MainWindow Legacy 코드 현대화

## 🎯 태스크 목표

- **주요 목표**: 메인 윈도우의 Legacy 코드 정리 및 현대적 패턴 완전 적용
- **완료 기준**: @inject 패턴 100% 적용, MVP 패턴 통합, 에러 처리 개선, QAsync 일관성 확보

## 📊 현재 상황 분석

### 🔍 발견된 문제점

1. **Legacy DI 패턴 혼재**:
   - `di_container=None` 같은 Legacy 파라미터 존재
   - 생성자에서 @inject와 Legacy 방식 혼용
   - MVP Container 초기화 불완전

2. **에러 처리 패턴 문제**:
   - try-catch로 에러를 숨기는 Silent Failure 패턴
   - `print()` 폴백 사용으로 로깅 일관성 부족
   - 실패시 조용히 넘어가서 원인 파악 어려움

3. **MVP 패턴 불완전**:
   - MainWindowPresenter 연결이 불완전
   - View-Presenter 간 시그널-슬롯 연결 미흡
   - 비즈니스 로직이 View에 혼재

4. **QAsync 패턴 일관성 부족**:
   - WebSocket 초기화에서 QTimer.singleShot 사용
   - 직접적인 asyncio.create_task 호출
   - 백그라운드 태스크 관리 불완전

### 📁 사용 가능한 리소스

- `upbit_auto_trading/ui/desktop/main_window.py`: 메인 윈도우 구현체
- `upbit_auto_trading/ui/desktop/presenters/main_window_presenter.py`: Presenter 구현체
- `docs/DEPENDENCY_INJECTION_QUICK_GUIDE.md`: DI 적용 가이드
- `docs/QASYNC_EVENT_QUICK_GUIDE.md`: QAsync 패턴 가이드
- 로그 분석: WebSocket 초기화 과정 참고

## 🔄 체계적 작업 절차 (필수 준수)

### 8단계 작업 절차

1. **📋 작업 항목 확인**: 태스크 문서에서 구체적 작업 내용 파악
2. **🔍 검토 후 세부 작업 항목 생성**: 작업을 더 작은 단위로 분해
3. **🔄 작업중 마킹**: 해당 작업 항목을 `[-]` 상태로 변경
4. **⚙️ 작업 항목 진행**: 실제 작업 수행
5. **✅ 작업 내용 확인**: 결과물 검증 및 품질 확인
6. **📝 상세 작업 내용 업데이트**: 태스크 문서에 진행사항 기록
7. **[x] 작업 완료 마킹**: 해당 작업 항목을 완료 상태로 변경
8. **⏳ 작업 승인 대기**: 다음 단계 진행 전 검토 및 승인

### 작업 상태 마커

- **[ ]**: 미완료 (미시작)
- **[-]**: 진행 중 (현재 작업)
- **[x]**: 완료

## 🛠️ 작업 계획

### Phase 1: Legacy DI 패턴 완전 제거

- [ ] **Legacy 파라미터 제거**: `di_container=None` 같은 불필요한 파라미터 제거
- [ ] **@inject 패턴 완전 적용**: 생성자에서 모든 의존성을 @inject로 주입받도록 변경
- [ ] **MVP Container 통합**: 올바른 MVP Container 초기화 및 연결
- [ ] **Provider 등록 확인**: MainWindow 관련 모든 서비스가 DI Container에 등록되었는지 확인

### Phase 2: 에러 처리 패턴 개선

- [ ] **Silent Failure 제거**: try-catch로 에러를 숨기는 패턴 제거
- [ ] **Fail-Fast 패턴 적용**: 중요한 의존성 실패시 명확한 에러 발생
- [ ] **로깅 일관성 확보**: `print()` 폴백 제거, Infrastructure 로깅만 사용
- [ ] **구체적 에러 메시지**: 실패 원인을 명확히 알 수 있는 에러 메시지 추가

### Phase 3: MVP 패턴 완전 통합

- [ ] **Presenter 역할 명확화**: View의 비즈니스 로직을 Presenter로 이동
- [ ] **시그널-슬롯 연결 완성**: View와 Presenter 간 완전한 시그널-슬롯 연결
- [ ] **View 순수성 확보**: View는 UI 표시만 담당, 비즈니스 로직 완전 분리
- [ ] **Presenter 단위 테스트**: Presenter 로직에 대한 단위 테스트 작성

### Phase 4: QAsync 패턴 일관성 확보

- [ ] **AppKernel TaskManager 활용**: 직접 asyncio.create_task 대신 TaskManager 사용
- [ ] **@asyncSlot 패턴 적용**: UI 이벤트 처리에 @asyncSlot 패턴 적용
- [ ] **백그라운드 태스크 관리**: WebSocket 초기화 등을 TaskManager로 관리
- [ ] **LoopGuard 적용**: ensure_main_loop로 이벤트 루프 안전성 확보

### Phase 5: 통합 검증 및 최적화

- [ ] **전체 기능 테스트**: MainWindow의 모든 기능이 정상 작동하는지 확인
- [ ] **성능 최적화**: 불필요한 초기화 로직 제거 및 최적화
- [ ] **메모리 누수 방지**: 리소스 정리 로직 강화
- [ ] **코드 품질 검증**: 아키텍처 가이드라인 100% 준수 확인

## 🔧 개발할 도구

- `main_window_analyzer.py`: MainWindow 구조 및 의존성 분석 도구
- `mvp_pattern_verifier.py`: MVP 패턴 적용 상태 검증 도구
- `qasync_pattern_checker.py`: QAsync 패턴 일관성 검사 도구

## 🎯 성공 기준

- ✅ Legacy DI 패턴 100% 제거 (di_container 파라미터 등)
- ✅ @inject 패턴 완전 적용
- ✅ Silent Failure 패턴 완전 제거
- ✅ print() 폴백 제거, Infrastructure 로깅만 사용
- ✅ MVP 패턴 완전 통합 (View-Presenter 분리)
- ✅ QAsync 패턴 일관성 100% 확보
- ✅ TaskManager를 통한 백그라운드 작업 관리
- ✅ `python run_desktop_ui.py` 에러 없이 실행
- ✅ WebSocket 초기화 안정성 확보

## 💡 작업 시 주의사항

### 안전성 원칙

- **백업 필수**: `main_window_legacy.py` 형태로 원본 백업
- **점진적 변경**: 한 번에 모든 것을 바꾸지 말고 단계별로 진행
- **실행 테스트**: 각 Phase 완료후 반드시 UI 실행 테스트

### 아키텍처 준수

- **DDD 계층 분리**: Presentation Layer 역할만 담당
- **MVP 패턴**: View는 순수 UI, Presenter는 비즈니스 로직
- **QAsync 통합**: 단일 이벤트 루프 원칙 준수

### 성능 고려사항

- **지연 로딩**: 필요하지 않은 서비스는 지연 초기화
- **리소스 관리**: 메모리 누수 방지를 위한 적절한 정리
- **UI 반응성**: 메인 스레드 블로킹 방지

## 🚀 즉시 시작할 작업

```powershell
# 1. MainWindow 구조 분석
python -c "
import inspect
from upbit_auto_trading.ui.desktop.main_window import MainWindow
print('📊 MainWindow 구조 분석:')
print(f'생성자 시그니처: {inspect.signature(MainWindow.__init__)}')
print(f'메서드 수: {len([m for m in dir(MainWindow) if not m.startswith(\"_\")})}')
"

# 2. Legacy 패턴 탐지
Get-ChildItem upbit_auto_trading\ui\desktop -Recurse -Include *.py | Select-String -Pattern "di_container.*=.*None|print\("

# 3. Silent Failure 패턴 찾기
Get-ChildItem upbit_auto_trading\ui\desktop\main_window.py | Select-String -Pattern "try:|except.*:" -Context 2
```

---
**다음 에이전트 시작점**: Phase 1의 "Legacy 파라미터 제거"부터 시작하여 MainWindow를 현대적 패턴으로 완전히 전환하세요.
