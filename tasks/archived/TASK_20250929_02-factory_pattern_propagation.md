# 📋 TASK_20250929_02: Factory 패턴 전파 - 전체 설정 화면 MVP 통합

## 🎯 태스크 목표

- **주요 목표**: TASK_20250929_01에서 검증된 Factory + MVP 패턴을 모든 설정 화면에 전파하여 일관된 아키텍처 구축
- **완료 기준**: 6개 설정 화면 모두 Factory 패턴 기반 MVP 구조로 통합되어 완벽 동작

## 📊 현재 상황 분석

### ✅ 성공 기반 (TASK_20250929_01)

- **API 키 설정**: Factory + MVP 패턴 완벽 구현 완료
- **검증된 패턴**: DI 충돌 해결, MVP 완전 조립, 개발 모드 에러 처리
- **문서화**: `FACTORY_MVP_SUCCESS_PATTERN.md` 완성
- **재사용 가능**: BaseComponentFactory 표준화로 즉시 적용 가능

### 🎯 전파 대상

1. **DatabaseSettingsComponentFactory**: 데이터베이스 설정 MVP 조립
2. **UISettingsComponentFactory**: UI 설정 MVP 조립 (부분 완성)
3. **LoggingSettingsComponentFactory**: 로깅 관리 MVP 조립
4. **NotificationSettingsComponentFactory**: 알림 설정 MVP 조립
5. **EnvironmentProfileComponentFactory**: 환경 프로필 MVP 조립

### 🔍 현재 상태 분석

- **UI 설정**: 이미 View는 존재하지만 Factory에서 MVP 조립 미완성
- **나머지 4개**: 기본 View만 생성하는 단순 Factory 구조
- **공통 패턴**: BaseComponentFactory 상속으로 일관된 확장 가능

## 🔄 체계적 작업 절차

### 작업 상태 마커

- **[ ]**: 미완료 (미시작)
- **[-]**: 진행 중 (현재 작업)
- **[x]**: 완료

## 🛠️ 작업 계획

### Phase 1: UI 설정 Factory MVP 완성 (45분)

#### 1.1 UISettingsView 현재 상태 분석

- [ ] 기존 UI 설정 View 구조 및 기능 파악
- [ ] Presenter 존재 여부 확인 및 DI 상태 분석
- [ ] Factory 현재 구현 상태 확인

#### 1.2 UISettingsPresenter 구현 (필요 시)

- [ ] UISettingsPresenter 클래스 생성 또는 DI 충돌 해결
- [ ] API 설정 패턴 적용: 명시적 의존성 주입 구조
- [ ] MVP 연결 메서드 구현

#### 1.3 UISettingsComponentFactory MVP 조립

- [ ] API 설정 성공 패턴 적용: 서비스 로드 → View 생성 → Presenter 생성 → MVP 연결
- [ ] 초기 데이터 로드 및 UI 상태 설정
- [ ] 개발 모드 에러 처리 적용

### Phase 2: Database 설정 Factory MVP 구현 (1시간)

#### 2.1 DatabaseSettings 컴포넌트 분석 및 설계

- [ ] 데이터베이스 설정 요구사항 파악 (DB 경로, 연결 설정 등)
- [ ] 필요한 Infrastructure 서비스 식별
- [ ] MVP 구조 설계

#### 2.2 DatabaseSettingsPresenter 구현

- [ ] 데이터베이스 관련 비즈니스 로직 구현
- [ ] Factory 호환 생성자 (명시적 의존성 주입)
- [ ] DB 연결 테스트 및 상태 관리 기능

#### 2.3 DatabaseSettingsComponentFactory 완성

- [ ] API 설정 성공 패턴 복사 및 적용
- [ ] Database 서비스 의존성 처리
- [ ] MVP 완전 조립 및 초기화

### Phase 3: Logging 관리 Factory MVP 구현 (1시간)

#### 3.1 LoggingManagement 컴포넌트 분석 및 설계

- [ ] 로깅 관리 요구사항 파악 (로그 레벨, 출력 설정 등)
- [ ] ApplicationLoggingService 연동 방식 설계
- [ ] MVP 구조 설계

#### 3.2 LoggingManagementPresenter 구현

- [ ] 로깅 설정 관련 비즈니스 로직 구현
- [ ] Factory 호환 생성자 구현
- [ ] 로그 레벨 변경 및 실시간 적용 기능

#### 3.3 LoggingSettingsComponentFactory 완성

- [ ] API 설정 성공 패턴 적용
- [ ] LoggingService 의존성 처리
- [ ] MVP 완전 조립 및 초기화

### Phase 4: Notification 설정 Factory MVP 구현 (45분)

#### 4.1 NotificationSettings 컴포넌트 구현

- [ ] 알림 설정 요구사항 파악
- [ ] NotificationService 연동 (필요 시 생성)
- [ ] MVP 구조 및 Presenter 구현

#### 4.2 NotificationSettingsComponentFactory 완성

- [ ] API 설정 성공 패턴 적용
- [ ] 알림 관련 서비스 의존성 처리
- [ ] MVP 완전 조립 및 초기화

### Phase 5: Environment Profile Factory MVP 구현 (45분)

#### 5.1 EnvironmentProfile 컴포넌트 구현

- [ ] 환경 프로필 요구사항 파악
- [ ] 프로필 관리 서비스 연동
- [ ] MVP 구조 및 Presenter 구현

#### 5.2 EnvironmentProfileComponentFactory 완성

- [ ] API 설정 성공 패턴 적용
- [ ] 환경 설정 관련 서비스 의존성 처리
- [ ] MVP 완전 조립 및 초기화

### Phase 6: 통합 테스트 및 검증 (1시간)

#### 6.1 전체 설정 화면 통합 테스트

- [ ] 6개 모든 설정 탭 Factory 생성 확인
- [ ] 각 설정별 MVP 패턴 동작 확인
- [ ] 탭 간 전환 시 lazy loading 정상 동작 확인

#### 6.2 아키텍처 일관성 검증

- [ ] Factory 패턴 일관성 확인 (BaseComponentFactory 표준 준수)
- [ ] DI 흐름 전체 검증
- [ ] 에러 처리 일관성 확인

#### 6.3 성능 및 안정성 검증

- [ ] 메모리 사용량 및 생성 속도 확인
- [ ] 레거시 WARNING 메시지 모두 해결 확인
- [ ] 예외 상황 처리 검증

## 🔧 개발 전략

### 📋 표준 적용 패턴

**각 ComponentFactory 구현 시 다음 패턴 적용:**

```python
class [Name]SettingsComponentFactory(BaseComponentFactory):
    def create_component_instance(self, parent: Optional[QWidget], **kwargs) -> QWidget:
        # 1. 서비스 로드 (생성자 우선 → 전역 Fallback → 실패 시 RuntimeError)
        # 2. View 생성 (실패 시 즉시 RuntimeError)
        # 3. Presenter 생성 및 연결 (실패 시 즉시 RuntimeError)
        # 4. 초기 데이터 로드 (실패해도 View 반환, 에러 로그)
        return view
```

### 🛡️ 안전 장치

- **백업**: 각 Phase 시작 전 관련 파일 백업
- **단계별 검증**: 각 ComponentFactory 완성 후 개별 테스트
- **롤백 준비**: 문제 발생 시 즉시 이전 상태로 복원

### 📊 의존성 서비스 매핑

| 설정 화면 | 주요 의존성 서비스 | 비즈니스 로직 |
|-----------|-------------------|---------------|
| UI Settings | ThemeService, WindowService | 테마 변경, 창 설정 |
| Database | DatabaseService, ConfigService | DB 연결, 경로 설정 |
| Logging | ApplicationLoggingService | 로그 레벨, 출력 설정 |
| Notification | NotificationService | 알림 채널, 규칙 설정 |
| Environment | ProfileService, ConfigService | 프로필 전환, 환경 변수 |

## 🎯 성공 기준

### 📋 완료 체크리스트

- ✅ 6개 모든 설정 화면이 Factory 패턴 기반으로 구현됨
- ✅ 각 설정별 MVP 패턴 완전 조립 및 동작 확인
- ✅ `python run_desktop_ui.py` → 모든 설정 탭 정상 동작
- ✅ 레거시 WARNING 메시지 모두 해결
- ✅ Factory 패턴 일관성 100% 달성
- ✅ 개발 모드 에러 처리 일관된 적용

### 🏆 품질 지표

- **아키텍처 일관성**: 100% (모든 Factory가 동일한 패턴)
- **MVP 완전성**: 100% (View ↔ Presenter 양방향 연결)
- **에러 처리 명확성**: 100% (실패 시 명확한 RuntimeError)
- **재사용성**: 95% (표준 패턴 적용)

## 💡 작업 시 주의사항

### 🔍 각 설정별 특수 고려사항

1. **UI Settings**: 기존 ThemeService와의 연동 유지
2. **Database**: DB 연결 테스트 기능 필수 구현
3. **Logging**: 실시간 로그 레벨 변경 반영
4. **Notification**: 알림 테스트 기능 구현
5. **Environment**: 프로필 전환 시 시스템 재시작 처리

### ⚠️ 레거시 코드 대응

- **기존 시그널 연결**: Factory 생성 후 자동 연결 되도록 수정
- **Lazy Loading 패턴**: 검증 로직을 생성 시점으로 변경
- **DI 의존성**: 모든 Presenter에서 `@inject` 완전 제거

## 🚀 즉시 시작할 작업

**사전 준비**:

1. **성공 패턴 검토**

   ```powershell
   # API 설정 성공 사례 분석
   Get-Content docs\architecture_patterns\factory_pattern\FACTORY_MVP_SUCCESS_PATTERN.md
   ```

2. **현재 상태 파악**

   ```powershell
   # 각 설정 Factory 현재 구현 확인
   Get-Content upbit_auto_trading\application\factories\settings_view_factory.py | Select-String "class.*ComponentFactory" -A 10
   ```

**Phase 1 시작**: UI 설정 Factory MVP 완성부터 진행

---

## 📈 예상 효과

### 즉시 효과

- 모든 설정 화면 아키텍처 일관성 확보
- 개발 효율성 극대화 (표준 패턴 적용)
- 유지보수성 대폭 향상

### 중장기 효과

- 새로운 설정 추가 시 10분 내 구현 가능
- 버그 발생률 80% 감소 (일관된 구조)
- 팀 개발 효율성 5배 향상

## 📋 연관 문서

- **기반 태스크**: `TASK_20250929_01-api_key_factory_pattern_implementation.md`
- **성공 패턴**: `docs/architecture_patterns/factory_pattern/FACTORY_MVP_SUCCESS_PATTERN.md`
- **아키텍처 가이드**: `docs/SETTINGS_ARCHITECTURE_VISUAL_GUIDE.md`

---

**🚀 태스크 시작 준비 완료: 검증된 패턴의 체계적 전파 시작!**
