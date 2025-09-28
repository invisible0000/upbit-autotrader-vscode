# 📊 현재 활성 위반 사항 목록

> 발견되었지만 아직 해결되지 않은 아키텍처 위반 사항들을 관리합니다.

**최종 업데이트**: 2025-09-28
**총 미해결 위반**: 54건 (자동 분석 + 수동 검증)
**Critical 위반**: 51건
**High 위반**: 3건

## 🚨 Critical 위반 (즉시 해결 필요)

> 시스템 안정성에 직접적인 위험을 초래하는 위반사항

### V20250928_001 - Settings 컴포넌트 Infrastructure 계층 직접 접근

**컴포넌트**: Settings Screen 전체
**파일**: 다중 파일 (47개 위반)
**유형**: DDD_LAYER_VIOLATION
**발견일**: 2025-09-28
**담당자**: TBD
**목표 해결일**: 2025-10-05 (1주일 내)

**문제 요약**: View와 Presenter에서 Infrastructure 계층(`create_component_logger`, `get_path_service` 등)에 직접 접근

**해결 방안**:

- 로깅: Application Service를 통한 로깅 서비스 제공
- 설정: 의존성 주입을 통한 서비스 제공
- 계층 순서 준수: Presentation → Application → Infrastructure

**관련 문서**:

- 상세보고서: `mvp_pattern_review/settings_screen/2025-09-28_automated_analysis_report.md`
- 관련 태스크: `tasks/active/TASK_20250928_02_infrastructure_layer_fix.md`

---

### V20250928_051 - View에서 Presenter 직접 생성 (DI 패턴 위반)

**컴포넌트**: Settings Screen 메인 View
**파일**: `settings_screen.py` (4개 위반)
**유형**: DEPENDENCY_INJECTION_VIOLATION
**발견일**: 2025-09-28 (수동 검증으로 발견)
**담당자**: TBD
**목표 해결일**: 2025-10-05 (1주일 내)

**문제 요약**: View에서 Presenter를 직접 생성하여 DI 컨테이너를 우회하는 Critical 아키텍처 위반

**세부 위반사항**:

- `line 98`: `self.main_presenter = SettingsPresenter(...)`
- `line 185`: `self.api_settings_presenter = ApiSettingsPresenter(...)`
- `line 210`: `self.database_settings_presenter = DatabaseSettingsPresenter(...)`
- `line 248`: `self.logging_management_presenter = LoggingManagementPresenter(...)`

**해결 방안**: MVPContainer를 통한 의존성 주입으로 모든 Presenter 생성을 DI 컨테이너에서 관리

**관련 문서**:

- 검증보고서: `mvp_pattern_review/settings_screen/2025-09-28_automated_tool_validation_report.md`
- **해결 태스크**: `tasks/active/TASK_20250928_04_view_presenter_di_fix.md` ✅ **생성 완료**

---

### V20250928_052 - Factory 패턴 부재 (컴포넌트 생성 책임 분산)

**컴포넌트**: Settings Screen
**파일**: `settings_screen.py` (하위 컴포넌트 생성 로직)
**유형**: DESIGN_PATTERN_VIOLATION
**발견일**: 2025-09-28 (수동 검증으로 발견)
**담당자**: TBD
**목표 해결일**: 2025-10-10 (2주일 내)

**문제 요약**: 하위 컴포넌트 생성 로직이 View에 하드코딩되어 Factory 패턴 부재

**해결 방안**: SettingsViewFactory 도입으로 컴포넌트 생성 책임 분리

**관련 문서**:

- 검증보고서: `mvp_pattern_review/settings_screen/2025-09-28_automated_tool_validation_report.md`
- **해결 태스크**: `tasks/active/TASK_20250928_05_settings_factory_pattern.md` ✅ **생성 완료**

---

## ⚠️ High 위반 (단기 해결 필요)

> MVP/DDD 패턴의 핵심 원칙을 위반하는 사항

### V20250928_002 - Presenter에서 UI 직접 조작

**컴포넌트**: Settings Screen Presenters
**파일**: 다중 파일 (3개 위반)
**유형**: MVP_PATTERN_VIOLATION
**발견일**: 2025-09-28
**담당자**: TBD
**목표 해결일**: 2025-10-02 (4일 내)

**문제 요약**: Presenter에서 `.setText()` 등을 통해 UI 위젯을 직접 조작

**해결 방안**: View 인터페이스 메서드를 통한 간접 조작으로 변경

**관련 문서**:

- 상세보고서: `mvp_pattern_review/settings_screen/2025-09-28_automated_analysis_report.md`
- 관련 태스크: `tasks/active/TASK_20250928_03_presenter_ui_fix.md`

---

## 📋 Medium 위반 (중기 해결 대상)

> 코드 품질과 유지보수성에 영향을 주는 사항

*현재 Medium 위반 사항 없음*

## 📝 Low 위반 (장기 개선 대상)

> 코드 스타일과 일관성 관련 사항

*현재 Low 위반 사항 없음*

---

## 📊 위반 사항 추가 가이드

새로운 위반 사항 발견 시 다음 형식으로 추가하세요:

### Critical/High/Medium/Low 위반 섹션에 추가

```markdown
### V{YYYYMMDD}_{순번} - {위반 제목}

**컴포넌트**: {대상 컴포넌트}
**파일**: `{파일경로}:{라인번호}`
**유형**: {MVP_PATTERN | DDD_LAYER | DEPENDENCY_INJECTION}
**발견일**: {YYYY-MM-DD}
**담당자**: {할당된 개발자 또는 TBD}
**목표 해결일**: {YYYY-MM-DD 또는 TBD}

**문제 요약**: {한 줄로 문제 상황 설명}

**해결 방안**: {간략한 해결 방향}

**관련 문서**:
- 상세보고서: `violation_registry/templates/violation_report_V{ID}.md`
- 관련 태스크: `tasks/active/TASK_{날짜}_{태스크명}.md`

---
```

## 🎯 해결 우선순위 원칙

1. **Critical 우선**: 시스템 안정성 위협하는 위반사항
2. **비즈니스 영향도**: 핵심 기능에 영향주는 정도
3. **수정 복잡도**: 해결에 필요한 리소스와 시간
4. **연쇄 효과**: 다른 컴포넌트에 미치는 영향

## 📈 추적 지표

### 월별 위반 발생/해결 현황

| 월 | 신규 발견 | 해결 완료 | 미해결 누적 | Critical 남은수 |
|----|----------|----------|-------------|-----------------|
| 2025-09 | 0 | 0 | 0 | 0 |
| 2025-10 | - | - | - | - |

### 컴포넌트별 위반 현황

| 컴포넌트 | Critical | High | Medium | Low | 총계 |
|----------|----------|------|--------|-----|------|
| settings_screen | 51 | 3 | 0 | 0 | 54 |
| strategy_manager | 0 | 0 | 0 | 0 | 0 |
| trading_engine | 0 | 0 | 0 | 0 | 0 |
| **총계** | **51** | **3** | **0** | **0** | **54** |

---

**다음 리뷰 일정**: TBD
**책임자**: 아키텍처 리뷰팀
