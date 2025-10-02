# 📋 TASK_20251001_06: DI 패턴 표준화 구현 (안전한 단계별 수정)

## 🎯 태스크 목표

### 주요 목표

**3-Container DI 시스템의 `.provider` 패턴 오류 수정 및 완전한 표준화 구현**

- **기술적 목표**: PresentationContainer의 `.provided.service.provider` → `.service` 패턴 수정
- **품질 목표**: 런타임 에러 완전 해결 및 DI 시스템 안정화
- **아키텍처 목표**: 전체 3-Container 시스템의 완전성 검증

### 완료 기준

- ✅ **핵심 오류 해결**: `'Factory' object has no attribute 'load_api_keys'` 에러 완전 제거
- ✅ **UI 통합 검증**: `python run_desktop_ui.py`에서 API 연결 테스트 성공
- ✅ **코드 정리**: MainWindowPresenter의 방어적 코드 제거
- ✅ **시스템 안정성**: 7규칙 전략 트리거 빌더 정상 동작 확인

---

## 📊 현재 상황 요약

### 🎉 TASK_20251001_05 분석 결과

**💡 핵심 발견**: 이는 완벽한 아키텍처에서 발생한 **단일 패턴 오류**입니다!

1. **구조적 완성도**: 3-Container DI 아키텍처는 DDD 원칙에 완벽 부합
2. **단일 오류**: `.provided.service.provider` → `.service` 수정만으로 완전 해결
3. **확장성 보장**: 현재 구조는 향후 확장에 최적화되어 있음
4. **패턴 표준화**: dependency-injector 공식 베스트 프랙티스 완전 준수

### 🚨 수정 대상 파일

**핵심 수정 파일 (1개)**:

- `upbit_auto_trading/presentation/presentation_container.py`

**정리 대상 파일 (1개)**:

- `upbit_auto_trading/presentation/presenters/main_window_presenter.py`

---

## 🔄 안전한 수정 절차 (필수 준수)

### 7단계 안전 절차

1. **📋 백업 생성**: 수정 대상 파일의 안전한 백업 생성
2. **🔍 현재 상태 확인**: 에러 재현 및 현재 동작 상태 기록
3. **⚙️ 패턴 수정**: `.provider` → 직접 참조 패턴으로 변경
4. **✅ 즉시 검증**: 패턴 수정 후 즉시 동작 확인
5. **🧹 코드 정리**: 방어적 코드 제거 및 최적화
6. **🚀 통합 테스트**: 전체 시스템 검증 및 7규칙 동작 확인
7. **📝 완료 보고**: 수정 내용 문서화 및 최종 검증

---

## 📋 단계별 실행 계획

### Phase 1: 안전 준비 및 현재 상태 확인 (15분)

#### 1.1 백업 및 환경 준비

- [ ] **대상 파일 백업 생성**

  ```powershell
  # PresentationContainer 백업
  Copy-Item "upbit_auto_trading/presentation/presentation_container.py" `
           "upbit_auto_trading/presentation/presentation_container_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').py"

  # MainWindowPresenter 백업
  Copy-Item "upbit_auto_trading/presentation/presenters/main_window_presenter.py" `
           "upbit_auto_trading/presentation/presenters/main_window_presenter_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').py"
  ```

- [ ] **현재 에러 상태 재현 및 기록**

  ```powershell
  # 현재 에러 재현 및 로그 캡처
  python run_desktop_ui.py 2>&1 | Tee-Object -FilePath "logs/error_before_fix_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
  ```

#### 1.2 수정 계획 최종 검토

- [ ] **수정 패턴 확인**
  - 변경 전: `external_container.provided.theme_service.provider`
  - 변경 후: `external_container.theme_service`
  - 영향 범위: PresentationContainer만 (다른 Container 무영향)

### Phase 2: 핵심 패턴 수정 (20분)

#### 2.1 PresentationContainer 수정

- [ ] **`.provider` 패턴 제거**

  ```python
  # Before (❌)
  services=providers.Dict(
      theme_service=external_container.provided.theme_service.provider,
      api_key_service=external_container.provided.api_key_service.provider,
  )

  # After (✅)
  services=providers.Dict(
      theme_service=external_container.theme_service,
      api_key_service=external_container.api_key_service,
  )
  ```

#### 2.2 즉시 동작 검증

- [ ] **수정 후 즉시 테스트**

  ```powershell
  # 수정 후 즉시 검증
  python run_desktop_ui.py
  ```

- [ ] **API 연결 테스트 성공 확인**
  - MainWindow 실행 성공
  - API 키 로드 성공
  - 에러 메시지 제거 확인

### Phase 3: 코드 정리 및 최적화 (15분)

#### 3.1 MainWindowPresenter 정리

- [ ] **방어적 코드 제거**

  ```python
  # Before (❌ 방어적 코드)
  if hasattr(self.api_key_service, 'load_api_keys'):
      api_keys = self.api_key_service.load_api_keys()
  else:
      self.logger.warning(f"타입 불일치: {type(self.api_key_service)}")

  # After (✅ 직접 호출)
  api_keys = self.api_key_service.load_api_keys()
  ```

#### 3.2 코드 품질 확인

- [ ] **타입 힌트 및 로직 검토**
- [ ] **불필요한 주석 정리**
- [ ] **일관성 검토**

### Phase 4: 통합 테스트 및 최종 검증 (20분)

#### 4.1 전체 시스템 검증

- [ ] **UI 통합 테스트**

  ```powershell
  # 전체 시스템 검증
  python run_desktop_ui.py
  ```

- [ ] **7규칙 전략 시스템 동작 확인**
  - 전략 관리 화면 접근
  - 트리거 빌더 실행
  - 7규칙 구성 가능 여부 확인

#### 4.2 DI 시스템 무결성 검증

- [ ] **Container 간 의존성 체인 확인**

  ```powershell
  # DI 시스템 검증 스크립트
  python -c "
  from upbit_auto_trading.infrastructure.dependency_injection.di_lifecycle_manager import DILifecycleManager
  manager = DILifecycleManager()
  manager.initialize()
  presenter = manager.get_main_window_presenter()
  print('✅ DI 시스템 정상 동작')
  manager.shutdown()
  "
  ```

#### 4.3 API 키 서비스 동작 검증

- [ ] **API 키 서비스 직접 테스트**

  ```powershell
  python -c "
  from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import UpbitAuthenticator
  auth = UpbitAuthenticator()
  print(f'🔐 API 키 인증 상태: {auth.is_authenticated()}')
  "
  ```

### Phase 5: 문서화 및 완료 (10분)

#### 5.1 변경 사항 문서화

- [ ] **수정 내용 기록**
  - 변경된 파일 목록
  - 수정된 패턴 설명
  - 검증 결과 요약

- [ ] **성능 및 안정성 개선사항 기록**

#### 5.2 최종 완료 확인

- [ ] **체크리스트 검토**
  - [ ] 런타임 에러 완전 제거
  - [ ] UI 정상 동작
  - [ ] API 연결 성공
  - [ ] 7규칙 전략 동작 확인
  - [ ] 방어적 코드 제거
  - [ ] 백업 파일 안전 보관

---

## 🛠️ 수정 대상 코드 상세 분석

### PresentationContainer 수정 부분

**파일**: `upbit_auto_trading/presentation/presentation_container.py`

**라인**: 대략 88-91행 (main_window_presenter Factory 내부)

```python
# 🔍 현재 문제 패턴 (Provider 객체 반환)
main_window_presenter = providers.Factory(
    MainWindowPresenter,
    services=providers.Dict(
        # ❌ 이 패턴이 Provider 객체를 반환함
        theme_service=external_container.provided.theme_service.provider,
        api_key_service=external_container.provided.api_key_service.provider,

        # ✅ 이 부분들은 이미 올바름
        navigation_bar=navigation_service,
        database_health_service=providers.Factory(...),
        screen_manager_service=screen_manager_service,
        window_state_service=window_state_service,
        menu_service=menu_service
    )
)

# ✅ 수정 후 올바른 패턴 (서비스 인스턴스 반환)
main_window_presenter = providers.Factory(
    MainWindowPresenter,
    services=providers.Dict(
        # ✅ 직접 참조로 인스턴스 주입
        theme_service=external_container.theme_service,
        api_key_service=external_container.api_key_service,

        # ✅ 기존 올바른 부분 유지
        navigation_bar=navigation_service,
        database_health_service=providers.Factory(...),
        screen_manager_service=screen_manager_service,
        window_state_service=window_state_service,
        menu_service=menu_service
    )
)
```

### MainWindowPresenter 정리 부분

**파일**: `upbit_auto_trading/presentation/presenters/main_window_presenter.py`

**라인**: 대략 125-140행 (handle_api_connection_test 메서드 내부)

```python
# 🔍 현재 방어적 코드 (Provider 객체 문제 대응)
def handle_api_connection_test(self) -> None:
    try:
        # ❌ 이 방어 코드를 제거해야 함
        if hasattr(self.api_key_service, 'load_api_keys'):
            api_keys = self.api_key_service.load_api_keys()
        else:
            self.logger.warning(f"⚠️ API Key Service 타입 불일치: {type(self.api_key_service)}")
            self.status_update_requested.emit("api_status", "서비스 오류")
            return
    except Exception as api_error:
        self.logger.error(f"❌ API 키 로드 실패: {api_error}")

# ✅ 정리 후 깔끔한 코드
def handle_api_connection_test(self) -> None:
    try:
        # ✅ 직접 호출 (더 이상 방어 코드 불필요)
        api_keys = self.api_key_service.load_api_keys()

        if api_keys:
            self.logger.info("API 키 파일 발견 - 연결 테스트 중...")
            # ... 기존 연결 테스트 로직 유지
    except Exception as api_error:
        self.logger.error(f"❌ API 키 로드 실패: {api_error}")
```

---

## 🎯 성공 기준 및 검증 체크리스트

### ✅ 필수 성공 기준

1. **런타임 에러 제거**: `'Factory' object has no attribute 'load_api_keys'` 에러 완전 제거
2. **UI 정상 실행**: `python run_desktop_ui.py` 성공적 실행
3. **API 연결 성공**: MainWindow에서 API 키 로드 및 연결 테스트 성공
4. **전체 기능 유지**: 기존의 모든 기능이 정상 동작

### ✅ 품질 검증 체크리스트

- [ ] **코드 품질**: 방어적 코드 제거로 깔끔한 코드
- [ ] **타입 안전성**: 올바른 서비스 인스턴스 주입
- [ ] **성능**: Provider 객체 생성 오버헤드 제거
- [ ] **유지보수성**: 표준 dependency-injector 패턴 준수

### ✅ 시스템 통합 검증

- [ ] **3-Container 무결성**: External → Application → Presentation 체인 정상
- [ ] **MVP 패턴 유지**: MainWindow ↔ Presenter 분리 구조 유지
- [ ] **7규칙 전략**: 트리거 빌더에서 7규칙 전략 구성 가능
- [ ] **향후 확장성**: 새로운 Container/Service 추가 시 호환성

---

## 🚨 주의사항 및 롤백 계획

### 안전 수칙

1. **백업 필수**: 모든 수정 전 반드시 백업 생성
2. **단계별 검증**: 각 수정 후 즉시 동작 확인
3. **점진적 적용**: 한 번에 하나씩 수정하여 문제 지점 명확화
4. **로그 보존**: 수정 전후 상태를 로그로 기록

### 롤백 계획

**문제 발생 시 즉시 실행**:

```powershell
# 1. 백업에서 복원
Copy-Item "upbit_auto_trading/presentation/presentation_container_backup_*.py" `
         "upbit_auto_trading/presentation/presentation_container.py"

Copy-Item "upbit_auto_trading/presentation/presenters/main_window_presenter_backup_*.py" `
         "upbit_auto_trading/presentation/presenters/main_window_presenter.py"

# 2. 즉시 동작 확인
python run_desktop_ui.py

# 3. 문제 분석
# 롤백 후 문제 원인 분석 및 다른 접근법 검토
```

### 예상 위험 요소

- **타입 불일치**: 서비스 인스턴스 vs Provider 객체 혼동
- **Wiring 오류**: 모듈 wiring 설정 문제
- **순환 참조**: Container 간 의존성 순환 (현재는 없음)

---

## 🔗 참고 문서

### 태스크 05 분석 결과

- **DI_Pattern_Analysis_and_Standards_Guide.md**: dependency-injector 표준 패턴 가이드
- **3_Container_DI_Architecture_Deep_Analysis.md**: 아키텍처 심층 분석 및 성숙도 평가
- **TASK_20251001_05 결과**: Phase 1-4 완전한 분석 완료

### dependency-injector 공식 문서

- **Container 간 참조**: 올바른 `.service` vs `.provider` 사용법
- **@inject 패턴**: 표준 데코레이터 사용법
- **Wiring 베스트 프랙티스**: 모듈 wiring 최적화

---

**문서 유형**: DI 패턴 표준화를 위한 안전한 코드 수정 태스크
**우선순위**: 🔥 최고 (런타임 에러 직접 해결)
**예상 소요 시간**: 1-2시간 (안전한 단계별 수정)
**접근 방식**: 백업 → 수정 → 검증 → 정리 → 완료

---

> **💡 핵심 메시지**: "완벽한 아키텍처에서 단일 패턴만 수정하여 완전한 DI 시스템 완성!"
> **🎯 성공 전략**: 안전한 백업 → 점진적 수정 → 즉시 검증 → 완전한 통합!

---

**다음 실행**: Phase 1.1부터 시작하여 안전한 백업 생성 및 현재 상태 확인 작업 진행
