# 📋 TASK_20250928_03: Settings Screen Presenter UI 직접 조작 위반 해결

## 🎯 태스크 목표

- **주요 목표**: Presenter UI 직접 조작 3건 + Factory 패턴 부재 1건 해결
- **완료 기준**: View 인터페이스를 통한 간접 조작 + 컴포넌트 생성 책임 분리
- **우선순위**: High (P1) - 단기 해결 필요 (자동 분석 도구 검증으로 추가 위반 발견)

## 🚨 해결 대상 위반사항

### 주요 위반 내용

#### V20250928_002 - Presenter UI 직접 조작

- **위반 건수**: 3건 (High)
- **위반 패턴**: Presenter에서 `.setText()`, `.setEnabled()` 등 직접 UI 조작
- **영향 파일**:
  1. `database_settings_presenter.py:426` - `msg_box.setText(success_msg)`
  2. `database_settings_presenter.py:650` - `msg_box.setText(success_msg)`
  3. `logging_config_presenter.py:118` - `self.view.component_focus_edit.setText(component_focus)`

#### V20250928_052 - Factory 패턴 부재 (새 발견)

- **위반 건수**: 1건 (High)
- **위반 패턴**: 하위 컴포넌트 생성 로직이 View에 하드코딩
- **영향 범위**: `settings_screen.py`의 lazy initialization 메서드들
- **발견 과정**: 자동 분석 도구 검증 중 수동 발견

### 근본 원인

1. **MVP 패턴 원칙 위반**: Presenter가 View의 캐쉘화를 무시하고 직접 UI 조작
2. **인터페이스 부재**: View 인터페이스가 정의되지 않아 직접 접근 유도
3. **책임 분리 실패**: UI 상태 관리가 Presenter와 View에 분산되어 있음
4. **Factory 패턴 부재**: 컴포넌트 생성 책임이 View에 하드코딩되어 확장성과 재사용성 저하 (자동 분석 도구가 놓친 위반)

## ✅ 해결 체크리스트

### Phase 1: View 인터페이스 정의 (1시간)

- [ ] **DatabaseSettingsView 인터페이스 확장**
  - [ ] `IDatabaseSettingsView` 프로토콜에 메시지 표시 메서드 추가
  - [ ] `show_success_message(self, message: str)` 메서드 정의
  - [ ] `show_error_message(self, message: str)` 메서드 정의

- [ ] **LoggingConfigView 인터페이스 정의**
  - [ ] `ILoggingConfigView` 프로토콜 생성
  - [ ] `set_component_focus(self, component: str)` 메서드 정의
  - [ ] 기존 `component_focus_edit` 직접 접근 대신 인터페이스 제공

### Phase 2: Presenter 수정 - UI 직접 조작 제거 (1.5시간)

- [ ] **DatabaseSettingsPresenter 수정**
  - [ ] `line 426`: `msg_box.setText()` 제거하고 `self.view.show_success_message()` 호출
  - [ ] `line 650`: 동일하게 View 인터페이스 메서드로 변경
  - [ ] QMessageBox 직접 생성 제거, View에서 메시지 표시 위임

- [ ] **LoggingConfigPresenter 수정**
  - [ ] `line 118`: `self.view.component_focus_edit.setText()` 제거
  - [ ] `self.view.set_component_focus(component_focus)` 호출로 변경
  - [ ] View 내부 위젯에 직접 접근하지 않도록 수정

### Phase 3: View 구현체 업데이트 (2시간)

- [ ] **DatabaseSettingsView 메서드 구현**
  - [ ] `show_success_message(message: str)` 구현

    ```python
    def show_success_message(self, message: str):
        QMessageBox.information(self, "성공", message)
    ```

  - [ ] `show_error_message(message: str)` 구현
  - [ ] 기존 코드에서 중복된 메시지 박스 로직 제거

- [ ] **LoggingConfigView 메서드 구현**
  - [ ] `set_component_focus(component: str)` 구현

    ```python
    def set_component_focus(self, component: str):
        self.component_focus_edit.setText(component)
    ```

  - [ ] Presenter가 위젯에 직접 접근할 수 없도록 캡슐화

### Phase 4: 인터페이스 준수성 검증 (30분)

- [ ] **타입 체크 및 인터페이스 준수 확인**
  - [ ] Presenter가 View를 인터페이스 타입으로 받는지 확인
  - [ ] `isinstance(self.view, IDatabaseSettingsView)` 검증
  - [ ] MyPy 또는 IDE 타입 체크로 인터페이스 준수 확인

- [ ] **MVP 패턴 검증**
  - [ ] Presenter에서 View 위젯에 직접 접근하는 코드 완전 제거 확인
  - [ ] View의 공개 메서드만 사용하도록 제한
  - [ ] UI 로직이 View에만 존재하는지 검증

### Phase 5: Factory 패턴 도입 (1시간)

- [ ] **타입 체크 및 인터페이스 준수 확인**
  - [ ] Presenter가 View를 인터페이스 타입으로 받는지 확인
  - [ ] `isinstance(self.view, IDatabaseSettingsView)` 검증
  - [ ] MyPy 또는 IDE 타입 체크로 인터페이스 준수 확인

- [ ] **MVP 패턴 검증**
  - [ ] Presenter에서 View 위젯에 직접 접근하는 코드 완전 제거 확인
  - [ ] View의 공개 메서드만 사용하도록 제한
  - [ ] UI 로직이 View에만 존재하는지 검증

## 🛠️ 구체적 수정 방법론

### 1. 인터페이스 우선 설계

```python
# interfaces/database_settings_view_interface.py
from typing import Protocol

class IDatabaseSettingsView(Protocol):
    def show_success_message(self, message: str) -> None:
        """성공 메시지를 사용자에게 표시"""
        ...

    def show_error_message(self, message: str) -> None:
        """오류 메시지를 사용자에게 표시"""
        ...

    def show_confirmation_dialog(self, message: str) -> bool:
        """확인 대화상자 표시 및 결과 반환"""
        ...
```

### 2. Presenter 리팩터링 패턴

```python
# Before (위반)
class DatabaseSettingsPresenter:
    def handle_backup_complete(self, success_msg: str):
        # ❌ 직접 UI 조작
        msg_box = QMessageBox()
        msg_box.setText(success_msg)
        msg_box.exec()

# After (수정)
class DatabaseSettingsPresenter:
    def handle_backup_complete(self, success_msg: str):
        # ✅ View 인터페이스를 통한 간접 조작
        self.view.show_success_message(success_msg)
```

### 3. View 구현체 패턴

```python
class DatabaseSettingsView(QWidget):
    def show_success_message(self, message: str) -> None:
        """인터페이스 구현 - 성공 메시지 표시"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("작업 완료")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()

    def show_error_message(self, message: str) -> None:
        """인터페이스 구현 - 오류 메시지 표시"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("오류")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.exec()
```

## 🎯 검증 기준

### 자동화된 검증

```powershell
# Presenter에서 UI 직접 조작 패턴 검색 (결과가 0이어야 함)
Get-ChildItem upbit_auto_trading\ui\desktop\screens\settings -Recurse -Include *presenter.py | Select-String -Pattern "\.setText\(|\.setEnabled\(|\.show\("

# MVP 분석 도구 재실행
python docs\architecture_review\tools\mvp_quick_analyzer.py --component settings --violations-only
```

### 수동 검증

- [ ] **기능 테스트**: 각 메시지 표시 기능이 정상 동작하는지 확인
- [ ] **UI 일관성**: 메시지 박스 스타일과 동작이 일관적인지 확인
- [ ] **사용자 경험**: 메시지 표시 타이밍과 내용이 적절한지 확인

## 📊 예상 영향 및 이점

### 즉시 효과

- [ ] **MVP 패턴 준수**: Presenter와 View의 책임이 명확히 분리됨
- [ ] **테스트 용이성**: Presenter 테스트 시 View를 Mock으로 대체 가능
- [ ] **유지보수성**: UI 변경 시 View만 수정하면 됨

### 장기적 이점

- [ ] **확장성**: 새로운 UI 요소 추가 시 인터페이스 확장만으로 처리
- [ ] **재사용성**: 동일한 Presenter를 다른 View 구현체와 사용 가능
- [ ] **아키텍처 일관성**: 전체 시스템의 MVP 패턴 준수도 향상

## 🎯 완료 기준

### 필수 완료 사항

- [ ] **UI 직접 조작 완전 제거**: 3건의 High 위반 모두 해결
- [ ] **View 인터페이스 완전 구현**: 모든 UI 조작이 인터페이스를 통해 수행
- [ ] **기능 무결성 보장**: 기존 메시지 표시 기능이 모두 정상 동작
- [ ] **MVP 패턴 준수**: Presenter가 View의 구현 세부사항에 의존하지 않음

### 성공 지표

- [ ] 자동 분석 도구에서 High 위반 0건 달성
- [ ] Presenter 단위 테스트 작성 가능해짐
- [ ] View 교체 시 Presenter 코드 수정 불필요
- [ ] 코드 리뷰에서 MVP 패턴 위반 지적 사항 없음

## 📋 예상 소요시간 및 리소스

- **총 예상시간**: 6시간 (기존 5시간 + Factory 패턴 도입 1시간)
- **필요 기술**: MVP 패턴, 인터페이스 설계, Factory 패턴, PyQt6
- **전제 조건**: MVP 패턴 개념과 인터페이스 기반 설계 이해 + 자동 분석 도구 검증 결과 반영

## 🚀 시작 방법

```powershell
# 1. 현재 위반 상황 확인
Get-ChildItem upbit_auto_trading\ui\desktop\screens\settings -Recurse -Include *presenter.py | Select-String -Pattern "\.setText\(|\.setEnabled\("

# 2. Git 브랜치 생성 (또는 기존 브랜치 사용)
git checkout -b fix/presenter-ui-violations

# 3. Phase 1부터 순차 진행
# - 인터페이스 정의
# - Presenter 수정
# - View 구현체 업데이트

# 4. 검증
python run_desktop_ui.py  # 기능 테스트
python docs\architecture_review\tools\mvp_quick_analyzer.py --component settings
```

## 📋 관련 문서

- **MVP 패턴 가이드**: `docs/MVP_ARCHITECTURE.md`
- **MVP 실용 가이드**: `docs/MVP_QUICK_GUIDE.md`
- **근본 분석**: `docs/architecture_review/mvp_pattern_review/settings_screen/2025-09-28_mvp_violation_report.md`
- **도구 검증 보고서**: `docs/architecture_review/mvp_pattern_review/settings_screen/2025-09-28_automated_tool_validation_report.md` (Factory 패턴 부재 발견)
- **위반사항 등록**: `docs/architecture_review/violation_registry/active_violations.md` (V20250928_052 추가)

---

**시작일**: 2025-09-28
**목표 완료일**: 2025-10-02
**우선순위**: High (P1)
**담당자**: TBD
