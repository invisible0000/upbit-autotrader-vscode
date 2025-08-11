# TASK-20250810-02: UI 설정 탭 저장/복원 버튼 수정

## 📋 작업 개요
**우선순위**: 🟡 높음
**담당자**: GitHub Copilot
**생성일**: 2025-08-10
**예상 소요**: 1-2시간

## 🎯 문제 정의
UI 설정 탭의 "설정 저장", "기본값으로 복원" 버튼이 클릭해도 반응하지 않아 사용자 설정 변경사항이 저장되지 않고 기본값 복원도 불가능한 상태.

## 🔍 현재 상태 분석
- ❌ "설정 저장" 버튼 클릭시 무반응
- ❌ "기본값으로 복원" 버튼 클릭시 무반응
- ✅ 테마 선택 등 개별 설정 변경은 즉시 반영됨
- ❌ 프로그램 재시작시 설정 변경사항 유실 가능성

## 📊 서브 태스크 분할

### **서브태스크 2.1: 버튼 시그널 연결 상태 확인** (난이도: ⭐)
- [ ] **2.1.1**: UISettingsView의 버튼 시그널 emit 확인
- [ ] **2.1.2**: UISettingsPresenter의 슬롯 연결 상태 검증
- [ ] **2.1.3**: 시그널-슬롯 매핑 테이블 작성

**TDD 테스트**:
```python
def test_ui_settings_button_signals():
    """UI 설정 버튼 시그널 연결 테스트"""
    widget = UISettingsView()
    presenter = UISettingsPresenter()

    # 시그널 연결 확인
    assert widget.save_settings_requested.receivers() > 0
    assert widget.restore_defaults_requested.receivers() > 0
```

### **서브태스크 2.2: SettingsService 연동 상태 점검** (난이도: ⭐⭐)
- [ ] **2.2.1**: UISettingsPresenter에서 SettingsService 의존성 주입 확인
- [ ] **2.2.2**: 설정 저장 메서드 호출 체인 추적
- [ ] **2.2.3**: 설정 로드 메서드 정상 동작 검증

**TDD 테스트**:
```python
def test_settings_service_integration():
    """SettingsService 통합 테스트"""
    presenter = UISettingsPresenter()

    # 서비스 주입 확인
    assert presenter._settings_service is not None

    # 설정 저장 테스트
    test_settings = {'theme': 'dark', 'window_width': 1200}
    result = presenter.save_current_settings(test_settings)
    assert result is True

    # 설정 로드 테스트
    loaded_settings = presenter.load_current_settings()
    assert loaded_settings['theme'] == 'dark'
```

### **서브태스크 2.3: 설정 저장 로직 구현/수정** (난이도: ⭐⭐⭐)
- [ ] **2.3.1**: UI 상태 → 설정 객체 변환 로직 구현
- [ ] **2.3.2**: SettingsService를 통한 영구 저장 처리
- [ ] **2.3.3**: 저장 성공/실패 피드백 UI 추가

**TDD 테스트**:
```python
def test_settings_persistence():
    """설정 영구 저장 테스트"""
    presenter = UISettingsPresenter()

    # 설정 변경
    original_theme = presenter.get_current_theme()
    new_theme = 'dark' if original_theme == 'light' else 'light'
    presenter.change_theme(new_theme)

    # 저장 실행
    save_success = presenter.save_all_settings()
    assert save_success is True

    # 새로운 인스턴스로 로드 검증
    new_presenter = UISettingsPresenter()
    loaded_theme = new_presenter.get_current_theme()
    assert loaded_theme == new_theme
```

### **서브태스크 2.4: 기본값 복원 로직 구현** (난이도: ⭐⭐)
- [ ] **2.4.1**: 시스템 기본값 정의 및 관리
- [ ] **2.4.2**: 현재 설정 → 기본값 일괄 복원 로직
- [ ] **2.4.3**: 복원 후 UI 즉시 업데이트 처리

**TDD 테스트**:
```python
def test_restore_defaults():
    """기본값 복원 테스트"""
    presenter = UISettingsPresenter()

    # 설정 변경
    presenter.change_theme('dark')
    presenter.change_window_size(1600, 900)

    # 기본값 복원
    restore_success = presenter.restore_all_defaults()
    assert restore_success is True

    # 기본값 확인
    assert presenter.get_current_theme() == 'light'  # 기본값
    assert presenter.get_window_size() == (1200, 800)  # 기본값
```

## 🧪 통합 테스트 시나리오

### **시나리오 A: 설정 저장 워크플로우**
1. UI에서 테마를 라이트 → 다크로 변경
2. 창 크기를 1200x800 → 1600x1000으로 변경
3. "설정 저장" 버튼 클릭
4. 성공 메시지 확인
5. 프로그램 재시작 후 설정 유지 확인

### **시나리오 B: 기본값 복원 워크플로우**
1. 여러 설정을 기본값이 아닌 값으로 변경
2. "기본값으로 복원" 버튼 클릭
3. 확인 다이얼로그 응답
4. 모든 설정이 즉시 기본값으로 복원되는지 확인
5. UI가 즉시 업데이트되는지 확인

### **시나리오 C: 저장 실패 처리**
1. 권한 없는 경로에 설정 저장 시도 (시뮬레이션)
2. 적절한 오류 메시지 표시 확인
3. 사용자 재시도 옵션 제공 확인

## ✅ 완료 조건
- [ ] "설정 저장" 버튼 클릭시 즉시 반응 및 저장 완료
- [ ] "기본값으로 복원" 버튼 클릭시 즉시 UI 업데이트
- [ ] 프로그램 재시작 후 저장된 설정 유지
- [ ] 모든 TDD 테스트 통과 (커버리지 85% 이상)

## 🎨 UX 개선 요구사항
1. **즉시 피드백**: 버튼 클릭시 0.5초 이내 반응
2. **진행 표시**: 저장 중 스피너 또는 진행률 표시
3. **성공 알림**: 저장 완료시 Toast 메시지 (2초간 표시)
4. **확인 다이얼로그**: 기본값 복원시 "정말 복원하시겠습니까?" 확인

## 🚨 리스크 및 주의사항
1. **데이터 손실**: 기존 사용자 설정 백업 후 작업
2. **호환성**: 기존 설정 파일 형식과 호환성 유지
3. **성능**: 설정 저장 프로세스 3초 이내 완료
4. **동시성**: 여러 설정 변경 동시 발생시 안전 처리

## 📝 검증 체크리스트
- [ ] 각 설정 항목별 저장/복원 정상 동작
- [ ] 프로그램 재시작 후 설정 유지 확인
- [ ] 동시에 여러 설정 변경 후 일괄 저장 정상 동작
- [ ] 저장 실패시 사용자 알림 적절성
- [ ] UI 응답성 요구사항 충족 (0.5초 이내)

## 🔄 다음 태스크 연계
성공시 → **TASK-20250810-03** (환경 프로파일 UI 디자인 복원)
실패시 → 설정 관리 아키텍처 재검토 필요
