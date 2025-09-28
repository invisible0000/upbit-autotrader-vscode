# 📋 MVP 아키텍처 검토 방법론 가이드

> 업비트 자동매매 시스템의 MVP(Model-View-Presenter) 패턴 준수성을 체계적으로 검토하는 방법론

## 🎯 가이드 목적

MVP 패턴과 DDD 아키텍처가 올바르게 적용되었는지 검증하여 시스템의 유지보수성, 테스트 가능성, 확장성을 확보합니다.

## 📊 검토가 필요한 영역

1. **아키텍처 경계 준수**:
   - View에서 비즈니스 로직 완전 제거
   - Presenter의 적절한 역할 분담
   - DDD 계층 간 의존성 방향 준수

2. **MVP 패턴 완전성**:
   - Presenter-View 간 인터페이스 기반 통신
   - View 순수성(Passive View) 달성
   - 비즈니스 로직의 Application/Domain 계층 완전 분리

3. **사용자 상호작용 플로우 무결성**:
   - 전체 플로우에서 아키텍처 원칙 준수
   - 컴포넌트 간 상호작용의 일관성

## 📝 검토 대상 및 우선순위

### 1. API 키 설정 플로우 (최고 우선순위) 🔑

- 전체 시스템 인증의 핵심 기능
- 검토 범위: 설정 화면 → API 키 탭 → 입력/저장/테스트 → 결과 표시

### 2. 데이터베이스 설정 플로우 (고 우선순위) 💾

- 시스템 데이터 관리 핵심, 백업/복원 로직 포함
- 검토 범위: DB 상태 조회 → 경로 변경/백업/복원 → 결과 검증

### 3. UI 설정 플로우 (중간 우선순위) 🎨

- 테마/스타일 관리, 기본적 MVP 패턴 검증

### 4. 로깅 관리 플로우 (중간 우선순위) 📝

- 시스템 모니터링, 실시간 로그 표시

## 🛠️ 5단계 검토 방법론

### Phase 1: 정적 코드 분석

**목표**: Import 구조와 클래스 책임 분석

#### 1.1 MVP 패턴 위반 탐지 기준 정의

**View 순수성 위반 기준**:

- [ ] View 클래스에서 비즈니스 로직 직접 실행
- [ ] View에서 Application/Domain Service 직접 호출
- [ ] View에서 데이터 변환/검증 로직 수행
- [ ] View에서 Infrastructure 레이어 직접 접근

**Presenter 책임 위반 기준**:

- [ ] Presenter에서 UI 위젯 직접 조작 (시그널 우회)
- [ ] Presenter에서 Infrastructure 레이어 직접 접근
- [ ] Presenter에 UI 렌더링 로직 포함
- [ ] Presenter에서 View 구현체 직접 참조 (인터페이스 우회)

#### 1.2 DDD 아키텍처 위반 탐지 기준

**계층 경계 위반 기준**:

- [ ] Domain → Infrastructure 의존성
- [ ] View → Domain 직접 의존성
- [ ] Application → Presentation 의존성
- [ ] 계층 건너뛰기 (View → Domain, Presentation → Infrastructure)

**의존성 방향 위반 기준**:

- [ ] 순환 의존성 존재
- [ ] 상위 계층이 하위 계층 구현체에 직접 의존
- [ ] Interface 없는 직접 의존성

#### 1.3 자동 분석 도구 개발

```python
# mvp_architecture_analyzer.py
class MVPArchitectureAnalyzer:
    """MVP 패턴 및 DDD 아키텍처 준수성 자동 분석"""

    def analyze_view_purity(self, view_path: str) -> List[Violation]:
        """View 순수성 검증"""
        pass

    def analyze_presenter_responsibilities(self, presenter_path: str) -> List[Violation]:
        """Presenter 책임 분리 검증"""
        pass

    def analyze_dependency_flow(self, component_paths: List[str]) -> DependencyGraph:
        """의존성 흐름 분석"""
        pass

    def detect_layer_violations(self) -> List[LayerViolation]:
        """DDD 계층 위반 탐지"""
        pass
```

### Phase 2: 정적 코드 분석

#### 2.1 Import 구조 분석

**분석 대상**:

- 각 클래스의 import 문 분석으로 의존성 방향 검증
- 계층별 파일에서 다른 계층 import 패턴 분석
- 순환 의존성 자동 탐지

**검증 스크립트**:

```python
def analyze_import_structure():
    """
    검토 항목:
    1. View 클래스에서 Domain/Application 직접 import 금지
    2. Presenter에서 Infrastructure 직접 import 금지
    3. Domain에서 Infrastructure import 금지
    4. 순환 import 탐지
    """
    pass
```

#### 2.2 클래스 책임 분석

**분석 기준**:

- 각 클래스의 메서드 분석으로 SRP 위반 탐지
- UI 로직과 비즈니스 로직의 혼재 여부
- Infrastructure 관심사의 다른 계층 유입 여부

### Phase 3: 동적 실행 흐름 추적

#### 3.1 API 키 설정 종합 플로우 추적 (상세 예시)

**시나리오**: "API 키 입력 → 저장 → 테스트 → 결과 표시" 전체 흐름

**추적 단계**:

1. **사용자 상호작용 시작**

   ```
   설정 화면 진입 → API 키 탭 클릭

   검토 포인트:
   - SettingsScreen._on_tab_changed()가 View 로직만 포함하는가?
   - 탭 전환시 비즈니스 로직 없이 UI만 변경하는가?
   - Lazy Loading이 Presenter 없이 View 레벨에서만 처리되는가?
   ```

2. **API 키 입력 및 저장**

   ```
   사용자 입력 → 저장 버튼 클릭

   추적 흐름:
   ApiSettingsView.on_save_clicked()
   ↓ (시그널)
   ApiSettingsPresenter.handle_save_request()
   ↓ (Application Service 호출)
   ApiKeyService.save_api_keys()
   ↓ (Infrastructure)
   암호화 → DB 저장 → 결과 반환
   ↓ (역방향)
   Presenter → View → UI 업데이트

   검토 포인트:
   - View에서 입력값 검증 없이 단순 전달만?
   - Presenter에서 비즈니스 규칙 적용?
   - Service에서 Infrastructure 추상화 사용?
   - UI 업데이트가 시그널을 통해서만?
   ```

3. **API 연결 테스트**

   ```
   테스트 버튼 클릭 → API 호출 → 결과 표시

   추적 흐름:
   ApiSettingsView.on_test_clicked()
   ↓ (시그널)
   ApiSettingsPresenter.handle_test_request()
   ↓ (Service 호출)
   ApiKeyService.test_api_connection()
   ↓ (Infrastructure)
   UpbitApiClient → 외부 API → 응답
   ↓ (결과 처리)
   Presenter → View → 결과 다이얼로그 표시

   검토 포인트:
   - 외부 API 의존성이 Infrastructure에만 격리?
   - 에러 처리가 각 계층별로 적절히 분리?
   - UI 피드백이 View의 인터페이스 메서드 사용?
   ```

#### 3.2 크로스 탭 상호작용 추적

**시나리오**: "API 키 변경 → 다른 탭의 상태 변화"

**검토 포인트**:

- 탭 간 상태 공유가 Service 레이어를 통해서만?
- View 간 직접 통신 없이 Presenter/Service 경유?
- 상태 변경 알림이 이벤트 기반으로 처리?

### Phase 4: 아키텍처 준수성 종합 평가

#### 4.1 발견된 위반 사항 분류

**심각도별 분류**:

- **Critical**: 아키텍처 핵심 원칙 위반 (계층 건너뛰기, 순환 의존성)
- **High**: MVP 패턴 위반 (View에 비즈니스 로직, Presenter의 UI 직접 조작)
- **Medium**: 관심사 분리 미흡 (책임 혼재, 인터페이스 미사용)
- **Low**: 코드 품질 이슈 (네이밍, 주석, 구조화)

**카테고리별 분류**:

- **의존성 위반**: 잘못된 계층 간 호출
- **책임 분리 위반**: 여러 관심사가 한 클래스에 혼재
- **인터페이스 위반**: 구체적 구현에 직접 의존
- **패턴 위반**: MVP/DDD 패턴 원칙 불준수

#### 4.2 우선순위별 개선 방안 제시

**즉시 개선 필요**:

- Critical/High 레벨 위반 사항
- 시스템 안정성에 직접 영향
- 아키텍처 일관성 파괴 요소

**점진적 개선 대상**:

- Medium 레벨 위반 사항
- 코드 품질 및 유지보수성 개선
- 패턴 완성도 향상

### Phase 5: 검증 및 문서화

#### 5.1 검토 결과 검증

**검증 방법**:

- 동료 개발자 리뷰
- 아키텍처 전문가 검토
- 실제 사용 시나리오 테스트

**검증 기준**:

- 탐지된 위반 사항의 정확성
- 개선 방안의 실현 가능성
- 아키텍처 일관성 확보 정도

#### 5.2 검토 체크리스트 템플릿

**API 키 설정 검토 체크리스트**:

```markdown
## API 키 설정 MVP 아키텍처 검토

### View 레이어 검증 (ApiSettingsView)
- [ ] 비즈니스 로직 미포함 (단순 UI 렌더링만)
- [ ] 입력값 검증 없이 Presenter로 전달
- [ ] Infrastructure 레이어 직접 접근 없음
- [ ] 시그널 기반 Presenter 통신
- [ ] UI 상태 변경만 담당

### Presenter 레이어 검증 (ApiSettingsPresenter)
- [ ] View 인터페이스를 통한 조작만
- [ ] 비즈니스 로직을 Application Service에 위임
- [ ] Infrastructure 직접 접근 없음
- [ ] 입력값 검증 및 변환 처리
- [ ] 에러 처리 및 사용자 피드백 관리

### Application 레이어 검증 (ApiKeyService)
- [ ] 비즈니스 규칙 구현 및 실행
- [ ] Infrastructure 추상화 사용
- [ ] Domain 객체 활용
- [ ] 트랜잭션 관리
- [ ] 상태 일관성 보장

### Infrastructure 레이어 검증
- [ ] 외부 시스템과의 실제 연동
- [ ] 기술적 관심사만 처리
- [ ] Domain 규칙 미포함
- [ ] 추상화된 인터페이스 구현
```

## 🛠️ 검토 도구 개발 계획

### 자동 분석 도구

1. **MVP Pattern Analyzer** (`mvp_pattern_analyzer.py`)
   - View 순수성 자동 검증
   - Presenter 책임 분석
   - 시그널-슬롯 연결 검증

2. **DDD Layer Validator** (`ddd_layer_validator.py`)
   - 계층 간 의존성 방향 검증
   - Import 구조 분석
   - 순환 의존성 탐지

3. **Dependency Flow Tracer** (`dependency_flow_tracer.py`)
   - 실행 시 호출 흐름 추적
   - 계층 통과 경로 기록
   - 위반 지점 자동 탐지

### 수동 검토 가이드

1. **설정별 검토 가이드**
   - API 키 설정 상세 검토 가이드
   - 데이터베이스 설정 검토 가이드
   - UI 설정 검토 가이드
   - 로깅 관리 검토 가이드

2. **위반 사항 분류 가이드**
   - 위반 유형별 탐지 방법
   - 심각도 판정 기준
   - 개선 방안 템플릿

## 💡 검토 시 주의사항

### 검토 범위 한계 인식

- **현재 구현체 기준**: 이상적 아키텍처가 아닌 현재 상태 검토
- **점진적 개선 관점**: 완벽함보다는 개선 방향 제시
- **실용성 우선**: 이론적 완벽함보다 실무 적용 가능성

### 검토 객관성 확보

- **다각적 검증**: 정적 + 동적 + 수동 검토 조합
- **기준 명확화**: 주관적 판단보다 객관적 기준 적용
- **동료 검토**: 단일 검토자 판단 의존 최소화

## 🛠️ 검토 도구 활용

### 자동 분석 도구

```powershell
# MVP 패턴 빠른 분석
python docs\architecture_review\tools\mvp_quick_analyzer.py --component settings_screen

# 전체 UI 스캔
python docs\architecture_review\tools\mvp_quick_analyzer.py --scan-all-ui
```

### 수동 검토 체크리스트

**API 키 설정 검토 예시**:

```markdown
### View 레이어 (ApiSettingsView)
- [ ] 비즈니스 로직 미포함
- [ ] 시그널 기반 Presenter 통신
- [ ] Infrastructure 직접 접근 없음

### Presenter 레이어 (ApiSettingsPresenter)
- [ ] View 인터페이스 사용
- [ ] 비즈니스 로직을 Service에 위임
- [ ] 에러 처리 및 사용자 피드백 관리

### Application 레이어 (ApiKeyService)
- [ ] 비즈니스 규칙 구현
- [ ] Infrastructure 추상화 사용
- [ ] 트랜잭션 관리
```

## 📊 검토 결과 관리

### 위반 사항 등록

1. **발견**: `violation_registry/templates/violation_report_template.md` 사용
2. **등록**: `violation_registry/active_violations.md`에 요약 기록
3. **추적**: 해결 진행상황 지속 모니터링
4. **완료**: `violation_registry/resolved_violations.md`로 이관

### 개선 추적

- **로드맵**: `improvement_tracking/improvement_roadmap.md` 참조
- **월간 리포트**: `improvement_tracking/monthly_progress/` 활용
- **사례 학습**: `improvement_tracking/resolved_cases/` 축적

## 🚀 실제 검토 수행

실제 검토를 수행할 때는 다음 단계를 따르세요:

1. **검토 대상 선정**: 우선순위에 따른 컴포넌트 선택
2. **검토 태스크 생성**: 구체적이고 실행 가능한 체크리스트 기반
3. **도구 활용**: 자동 분석 + 수동 검토 조합
4. **결과 문서화**: 표준 템플릿 사용하여 기록
5. **개선 계획 수립**: 우선순위와 일정 명시

---

**연관 문서**:

- [Architecture Review System](README.md) - 전체 시스템 개요
- [MVP Pattern Review Guide](mvp_pattern_review/README.md) - 상세 검토 가이드
- [Improvement Roadmap](improvement_tracking/improvement_roadmap.md) - 개선 계획
