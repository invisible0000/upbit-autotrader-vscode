# 🚨 위반 사항 보고서 템플릿

> 이 템플릿을 사용하여 발견된 아키텍처 위반 사항을 체계적으로 기록하세요.

## 📋 기본 정보

**위반 ID**: V{YYYY}{MM}{DD}_{순번} (예: V20250928_001)
**발견일**: {YYYY-MM-DD}
**검토자**: {검토자명}
**컴포넌트**: {대상 컴포넌트명}
**검토 유형**: {initial_review | followup_review | hotfix_review}

## 🎯 위반 사항 개요

**위반 유형**: {MVP_PATTERN | DDD_LAYER | DEPENDENCY_INJECTION | OTHER}
**패턴 분류**: {VIEW_PURITY | PRESENTER_RESPONSIBILITY | LAYER_BOUNDARY | CIRCULAR_DEPENDENCY}
**심각도**: {CRITICAL | HIGH | MEDIUM | LOW}

## 📍 위치 정보

**파일 경로**: `{상대경로}/경로/파일명.py`
**라인 번호**: {시작라인}-{종료라인} (단일라인인 경우 {라인번호})
**메서드/클래스**: `{클래스명}.{메서드명}()` 또는 `{클래스명}`

## 🔍 상세 내용

### 문제가 되는 코드

```python
# 현재 위반 코드 (실제 코드 복사)
class ExampleView(QWidget):
    def on_save_clicked(self):
        # 문제: View에서 직접 비즈니스 로직 수행
        if self.validate_data():  # 위반!
            self.save_to_database()  # 위반!
```

### 위반 사유

**MVP 패턴 관점에서 문제점**:

- [ ] View가 데이터 검증 로직 포함 (순수성 위반)
- [ ] View에서 Infrastructure 레이어 직접 접근
- [ ] Presenter 우회하여 비즈니스 로직 실행
- [ ] {기타 구체적인 위반 사유}

**DDD 아키텍처 관점에서 문제점**:

- [ ] 계층 경계 위반 (Presentation → Infrastructure 직접 호출)
- [ ] 의존성 방향 위반 (상위 → 하위가 아닌 역방향)
- [ ] Domain 순수성 파괴 (외부 기술 의존성 포함)
- [ ] {기타 구체적인 위반 사유}

## 💡 해결 방안

### 권장 수정 방향

```python
# 수정 후 올바른 코드 예시
class ExampleView(QWidget):
    def on_save_clicked(self):
        # View는 단순히 사용자 입력을 Presenter에 전달만
        input_data = self.get_form_data()
        self.save_requested.emit(input_data)  # 시그널로 전달

class ExamplePresenter:
    def handle_save_request(self, input_data: Dict):
        # Presenter가 비즈니스 로직을 Service에 위임
        try:
            validated_data = self.validation_service.validate(input_data)
            self.application_service.save_data(validated_data)
            self.view.show_success_message("저장 완료")
        except ValidationError as e:
            self.view.show_error_message(f"검증 실패: {e.message}")
```

### 단계별 수정 계획

1. **1단계** (즉시): {긴급히 해결해야 할 부분}
2. **2단계** (1주 내): {주요 구조 변경}
3. **3단계** (1개월 내): {완전한 패턴 준수}

### 연관 수정 필요 사항

- [ ] **테스트 코드 수정**: {관련 테스트 파일과 수정 내용}
- [ ] **인터페이스 추가**: {새로 정의해야 할 인터페이스}
- [ ] **의존성 주입 설정**: {DI 컨테이너 설정 변경}
- [ ] **기타**: {추가로 고려해야 할 사항}

## 📊 영향도 분석

### 시스템 영향도

**기능적 영향**:

- [ ] **None**: 현재 기능에 영향 없음
- [ ] **Low**: 일부 기능의 동작에 미미한 영향
- [ ] **Medium**: 주요 기능의 안정성에 영향
- [ ] **High**: 시스템 전체 안정성에 심각한 영향

**기술적 영향**:

- [ ] **테스트 가능성 저하**: 단위 테스트 작성 어려움
- [ ] **유지보수성 저하**: 코드 이해와 수정이 어려움
- [ ] **확장성 제약**: 새 기능 추가 시 제약 발생
- [ ] **성능 문제**: 비효율적인 아키텍처로 인한 성능 저하

### 수정 영향 범위

**직접 영향 파일**:

- `{파일1.py}`: {수정 내용 요약}
- `{파일2.py}`: {수정 내용 요약}

**간접 영향 파일**:

- `{테스트파일1.py}`: {테스트 수정 필요}
- `{설정파일1.yaml}`: {설정 변경 필요}

## 🎯 우선순위 및 일정

**해결 우선순위**: {1-5점, 5점이 최고 우선순위}
**예상 작업시간**: {시간 단위로 예상 소요 시간}
**담당 개발자**: {할당된 개발자명 또는 TBD}
**목표 완료일**: {YYYY-MM-DD 또는 TBD}

**우선순위 선정 근거**:

- {심각도와 영향 범위를 고려한 구체적 근거}
- {비즈니스 우선순위와의 연관성}
- {수정 복잡도와 리소스 가용성}

## 📋 추적 정보

**등록 위치**: `violation_registry/{active|critical}_violations.md`
**관련 이슈**: #{GitHub Issue 번호} (생성된 경우)
**관련 태스크**: `tasks/active/TASK_{날짜}_{태스크명}.md`

### 진행 상황

- [ ] **위반 사항 확인**: 추가 검토 및 검증 완료
- [ ] **해결 계획 승인**: 팀 리뷰 및 계획 승인 완료
- [ ] **구현 시작**: 실제 코드 수정 작업 시작
- [ ] **테스트 완료**: 수정 사항에 대한 테스트 완료
- [ ] **검증 완료**: 위반 사항 해결 검증 완료
- [ ] **문서화 완료**: resolved_violations.md로 이관 완료

### 이력

| 날짜 | 상태 변경 | 담당자 | 비고 |
|------|----------|--------|------|
| {YYYY-MM-DD} | 위반 발견 | {검토자} | 초기 발견 및 등록 |
| {YYYY-MM-DD} | 계획 수립 | {담당자} | 해결 계획 수립 완료 |
| {YYYY-MM-DD} | 진행 중 | {담당자} | 구현 작업 시작 |
| {YYYY-MM-DD} | 해결 완료 | {담당자} | 검증 완료 및 종료 |

## 💭 추가 고려사항

**학습 포인트**:

- {이 위반에서 배울 수 있는 아키텍처 원칙}
- {향후 유사한 실수를 방지하기 위한 가이드라인}

**재발 방지책**:

- [ ] **개발 가이드 업데이트**: {관련 가이드라인 추가}
- [ ] **코드 리뷰 체크리스트 추가**: {리뷰 시 확인사항 추가}
- [ ] **자동화 도구 개선**: {정적 분석 도구 규칙 추가}
- [ ] **교육 및 공유**: {팀 내 아키텍처 패턴 교육}

---

**템플릿 작성일**: {YYYY-MM-DD}
**템플릿 버전**: v1.0
**다음 검토 예정일**: {YYYY-MM-DD}
