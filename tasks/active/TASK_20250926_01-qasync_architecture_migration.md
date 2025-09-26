# 📋 TASK_20250926_01: QAsync 통합 이벤트 루프 아키텍처 마이그레이션

## 🎯 태스크 목표

- **주요 목표**: 다중 이벤트 루프 충돌 문제를 근본적으로 해결하여 시스템 안정성 확보
- **완료 기준**: `python run_desktop_ui.py` 실행 시 코인리스트+호가창 동시 동작하며 이벤트 루프 충돌 제로화

## 📊 현재 상황 분석

### 문제점

1. **Critical 이슈**: 코인리스트 위젯이 격리 루프 사용으로 Infrastructure Layer 마비
2. **아키텍처 결함**: PyQt6/QAsync와 asyncio.new_event_loop() 간 충돌
3. **회귀 위험**: 임시 수정 후 다시 같은 패턴으로 되돌아갈 가능성

### 사용 가능한 리소스

- `docs/big_issues/issue_01_20250926/QAsync_REFACTORING_WORK_GUIDE.md` (상세 작업 가이드)
- `docs/big_issues/issue_01_20250926/QAsync_EVENT_LOOP_CRISIS_COMPREHENSIVE_REPORT.md` (종합 진단 보고서)
- 아키텍처 불변식 + LoopGuard + AppKernel 설계안

## 🔄 체계적 작업 절차 (필수 준수)

### 8단계 작업 절차

1. **📋 작업 항목 확인**: 태스크 문서에서 구체적 작업 내용 파악
2. **🔍 검토 후 세부 작업 항목 생성**: 작업을 더 작은 단위로 분해
3. **⏳ 작업중 마킹**: 해당 작업 항목을 `[-]` 상태로 변경
4. **⚙️ 작업 항목 진행**: 실제 작업 수행
5. **✅ 작업 내용 확인**: 결과물 검증 및 품질 확인
6. **📝 상세 작업 내용 업데이트**: 태스크 문서에 진행사항 기록
7. **[x] 작업 완료 마킹**: 해당 작업 항목을 완료 상태로 변경
8. **⏳ 작업 승인 대기**: 다음 단계 진행 전 검토 및 승인

### 작업 상태 마커

- **[ ]**: 미완료 (미시작)
- **[-]**: 진행 중 (현재 작업)
- **[x]**: 완료

## ⚙️ 작업 계획

### Step 0: 가드레일 선배치 (회귀 방지 인프라)

- [ ] **CI/CD 정적 검사 도입**: pre-commit hook으로 금지 패턴 차단
- [ ] **pytest 고정장치 구축**: qasync 환경 강제하는 conftest.py 생성
- [ ] **LoopGuard 런타임 가드 구현**: infrastructure/runtime/loop_guard.py 생성

### Step 1: 진입점/런타임 커널(AppKernel) 도입

- [ ] **AppKernel 클래스 구현**: runtime/app_kernel.py 생성
- [ ] **run_desktop_ui.py 수정**: 단일 진입점으로 정리
- [ ] **통합 테스트**: 기본 앱 시작 동작 검증

### Step 2: Infrastructure 우선 고정

- [ ] **UpbitPublicClient 루프 인식**: 지연 초기화 + LoopGuard 적용
- [ ] **UpbitPrivateClient 동일 패턴**: 루프 바인딩 안전성 확보
- [ ] **DomainEventPublisher 혼용 제거**: 동기/비동기 분기 로직 단순화

### Step 3: UI 전면 QAsync화

- [ ] **코인리스트 위젯 수정**: 격리 루프 제거, @asyncSlot 패턴 적용
- [ ] **로깅 UI 시스템 통합**: event_driven_log_viewer_widget.py QAsync 전환
- [ ] **전략 관리 탭 수정**: trigger_builder_tab.py 비동기 패턴 정리

### Step 4: 종료 시퀀스/관측성

- [ ] **AppKernel.shutdown() 표준화**: 안전한 태스크/세션 정리 시퀀스
- [ ] **TaskManager 시스템 통합**: 모든 create_task를 중앙 관리
- [ ] **최종 검증**: 7규칙 전략 무결성 확인

## 🛠️ 개발할 도구

- `infrastructure/runtime/loop_guard.py`: 이벤트 루프 위반 감지 및 예외 발생
- `runtime/app_kernel.py`: 중앙집중식 런타임 리소스 관리자
- `tests/conftest.py`: qasync 환경 강제 pytest 픽스쳐
- `.github/workflows/qasync-check.yml`: CI에서 금지 패턴 정적 검사

## 🎯 성공 기준

- ✅ **이벤트 루프 충돌 제로화**: `bound to a different event loop` 오류 발생하지 않음
- ✅ **핵심 기능 정상화**: 코인리스트+호가창 동시 동작, 로깅 시스템 안정
- ✅ **CI 검증 통과**: 금지 패턴 정적 검사에서 위반 없음
- ✅ **회귀 방지 확인**: LoopGuard에서 루프 위반 감지 시 즉시 예외 발생
- ✅ **7규칙 전략 검증**: `python run_desktop_ui.py` → 전략 관리 → 트리거 빌더에서 7규칙 구성 가능

## 💡 작업 시 주의사항

### 안전성 원칙 (전문가 조언 반영)

- **가드레일 우선**: Step 0을 완료하지 않고는 절대 Step 1-4로 넘어가지 않음
- **아키텍처 불변식 준수**: 6가지 핵심 규칙을 절대 위반하지 않음
- **단계별 검증**: 각 Step 완료 시마다 `python run_desktop_ui.py` 실행하여 동작 확인
- **백업 필수**: 주요 파일 수정 전 `{filename}_legacy.py`로 백업

### 금지/허용 패턴 엄수

| 분류 | 금지(Disallow) | 허용(Allow) |
|------|----------------|-------------|
| 루프 제어 | `asyncio.new_event_loop()`, `asyncio.run()`, `loop.run_until_complete()` | **없음** |
| UI 브리지 | 직접 스레드+루프 생성 | `@qasync.asyncSlot` + `await` |
| 태스크 | fire-and-forget (참조 미보관) | `TaskManager.create(...)` 등록 |

## 🚀 즉시 시작할 작업

```bash
# 1. 현재 금지 패턴 검사 (베이스라인)
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String -Pattern "new_event_loop|run_until_complete|asyncio\.run\("

# 2. 첫 번째 수정 대상 확인
Write-Host "Step 0 시작: 가드레일 선배치" -ForegroundColor Yellow
```

---

## 📋 상세 진행 기록

### 2025-09-26 생성

- 전문가 조언을 반영한 태스크 문서 생성
- Step 0-4 순서로 회귀 방지 우선 적용
- 아키텍처 불변식과 금지/허용 패턴 명시

---

**다음 에이전트 시작점**: Step 0 > CI/CD 정적 검사 도입부터 시작. `.github/workflows/qasync-check.yml` 생성으로 즉시 실행 가능.
