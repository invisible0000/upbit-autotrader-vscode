# TASK-20250810-03: 환경 프로파일 UI 디자인 복원

## 📋 작업 개요
**우선순위**: 🟡 높음
**담당자**: GitHub Copilot
**생성일**: 2025-08-10
**예상 소요**: 2-3시간

## 🎯 문제 정의
기존 사용자 친화적 UI 디자인(기본 프로파일 3개 버튼 + 커스텀 프로파일 드롭다운)을 단일 드롭다운으로 임의 변경하여 UX 사용성이 크게 저하됨.

## 🔍 현재 상태 분석
- ❌ 기존 Development/Production/Testing 개별 버튼 제거됨
- ❌ 모든 프로파일이 단일 드롭다운으로 통합됨
- ❌ 원클릭 기본 프로파일 전환 불가능
- ❌ 사용자가 요구한 설계 무시됨

## 🎨 복원 목표 UI 디자인

```
┌─ 환경 프로파일 관리 ─────────────────────────┐
│                                           │
│ 📋 기본 프로파일 (원클릭 전환)              │
│ ┌─────────────┐ ┌─────────────┐ ┌──────────┐ │
│ │ Development │ │ Production  │ │ Testing  │ │
│ │   (활성)    │ │             │ │          │ │
│ └─────────────┘ └─────────────┘ └──────────┘ │
│                                           │
│ ─────────────────────────────────────────── │
│                                           │
│ 🔧 커스텀 프로파일                         │
│ 프로파일: [드롭다운 ▼] [전환] [저장] [삭제] │
│                                           │
│ 📋 현재 프로파일 정보                      │
│ ┌─────────────────────────────────────────┐ │
│ │ 이름: Development                       │ │
│ │ 설명: 개발 환경, 모의거래, 상세 로깅    │ │
│ │ 로그 레벨: DEBUG                        │ │
│ │ 거래 모드: 모의거래                     │ │
│ └─────────────────────────────────────────┘ │
└───────────────────────────────────────────┘
```

## 📊 서브 태스크 분할

### **서브태스크 3.1: 기존 UI 컴포넌트 백업 및 분석** (난이도: ⭐)
- [ ] **3.1.1**: 현재 `environment_profile_widget.py` 백업 생성
- [ ] **3.1.2**: 기존 버튼 기반 UI 구조 분석 (git history 활용)
- [ ] **3.1.3**: 커스텀 프로파일 드롭다운 컴포넌트 분리 추출

**TDD 테스트**:
```python
def test_ui_component_backup():
    """UI 컴포넌트 백업 테스트"""
    backup_path = Path("environment_profile_widget_backup.py")
    original_path = Path("environment_profile_widget.py")

    assert backup_path.exists()
    assert backup_path.stat().st_size > 0
    assert backup_path.read_text() != original_path.read_text()
```

### **서브태스크 3.2: 기본 프로파일 버튼 UI 복원** (난이도: ⭐⭐)
- [ ] **3.2.1**: Development/Production/Testing 3개 버튼 위젯 생성
- [ ] **3.2.2**: 현재 활성 프로파일 시각적 표시 (버튼 스타일링)
- [ ] **3.2.3**: 원클릭 프로파일 전환 시그널 연결

**TDD 테스트**:
```python
def test_basic_profile_buttons():
    """기본 프로파일 버튼 테스트"""
    widget = EnvironmentProfileWidget()

    # 3개 기본 버튼 존재 확인
    dev_btn = widget.findChild(QPushButton, "development_button")
    prod_btn = widget.findChild(QPushButton, "production_button")
    test_btn = widget.findChild(QPushButton, "testing_button")

    assert dev_btn is not None
    assert prod_btn is not None
    assert test_btn is not None

    # 활성 상태 표시 확인
    assert dev_btn.property("active") == True  # 기본 활성
    assert prod_btn.property("active") == False
```

### **서브태스크 3.3: 커스텀 프로파일 섹션 분리** (난이도: ⭐⭐⭐)
- [ ] **3.3.1**: 커스텀 프로파일 전용 위젯 생성 (별도 영역)
- [ ] **3.3.2**: 기본 프로파일과 독립적인 관리 로직 구현
- [ ] **3.3.3**: 커스텀 프로파일 CRUD 기능 (저장/로드/삭제)

**TDD 테스트**:
```python
def test_custom_profile_section():
    """커스텀 프로파일 섹션 테스트"""
    widget = EnvironmentProfileWidget()
    custom_section = widget.findChild(QWidget, "custom_profile_section")

    assert custom_section is not None

    # 커스텀 프로파일 생성 테스트
    widget.create_custom_profile("test_profile", "테스트용")
    profiles = widget.get_custom_profiles()
    assert "test_profile" in [p.name for p in profiles]

    # 커스텀 프로파일 삭제 테스트
    widget.delete_custom_profile("test_profile")
    profiles = widget.get_custom_profiles()
    assert "test_profile" not in [p.name for p in profiles]
```

### **서브태스크 3.4: 프로파일 정보 미리보기 패널** (난이도: ⭐⭐)
- [ ] **3.4.1**: 현재 선택된 프로파일 정보 표시 영역
- [ ] **3.4.2**: 프로파일별 핵심 설정 요약 (로그레벨, 거래모드 등)
- [ ] **3.4.3**: 프로파일 전환시 실시간 정보 업데이트

**TDD 테스트**:
```python
def test_profile_preview_panel():
    """프로파일 미리보기 패널 테스트"""
    widget = EnvironmentProfileWidget()
    preview = widget.findChild(QWidget, "profile_preview_panel")

    assert preview is not None

    # Development 프로파일 선택시
    widget.select_profile("development")
    profile_info = widget.get_current_profile_info()

    assert profile_info['name'] == 'development'
    assert profile_info['trading_mode'] == '모의거래'
    assert profile_info['log_level'] == 'DEBUG'
```

## 🧪 통합 테스트 시나리오

### **시나리오 A: 기본 프로파일 원클릭 전환**
1. Development 버튼 클릭 → 즉시 전환 확인
2. Production 버튼 클릭 → 전환 + 버튼 스타일 변경 확인
3. Testing 버튼 클릭 → 전환 + 미리보기 정보 업데이트 확인

### **시나리오 B: 커스텀 프로파일 관리**
1. 현재 혼합 설정 상태에서 "사용자정의1" 프로파일 저장
2. 다른 기본 프로파일로 전환
3. 커스텀 드롭다운에서 "사용자정의1" 선택하여 복원
4. 커스텀 프로파일 삭제 기능 테스트

### **시나리오 C: UI 반응성 테스트**
1. 빠른 속도로 여러 프로파일 버튼 연속 클릭
2. 각 전환마다 UI 상태 정확 업데이트 확인
3. 미리보기 패널 정보 동기화 확인

## ✅ 완료 조건
- [ ] 기본 프로파일 3개 버튼 원클릭 전환 가능
- [ ] 커스텀 프로파일 드롭다운 독립 영역 분리
- [ ] 프로파일 정보 미리보기 실시간 업데이트
- [ ] 모든 TDD 테스트 통과 (커버리지 90% 이상)

## 🎨 UX 요구사항 검증
1. **직관성**: 일반 사용자가 3초 내 원하는 프로파일 전환 가능
2. **시각적 피드백**: 현재 활성 프로파일 명확한 시각적 구분
3. **정보 제공**: 프로파일 전환 전 핵심 정보 미리 확인 가능
4. **분리성**: 기본 프로파일과 커스텀 프로파일 영역 명확 분리

**UX 테스트**:
```python
def test_user_experience_requirements():
    """UX 요구사항 테스트"""
    widget = EnvironmentProfileWidget()

    # 직관성: 버튼 텍스트 명확성
    dev_btn = widget.findChild(QPushButton, "development_button")
    assert "Development" in dev_btn.text()
    assert dev_btn.isEnabled()

    # 시각적 피드백: 활성 버튼 스타일
    active_style = dev_btn.styleSheet()
    assert "active" in active_style or "selected" in active_style

    # 정보 제공: 미리보기 패널 가시성
    preview = widget.findChild(QWidget, "profile_preview_panel")
    assert preview.isVisible()
```

## 🚨 리스크 및 주의사항
1. **기능 호환성**: 기존 ConfigProfileService와 100% 호환성 유지
2. **성능**: UI 렌더링 지연 최소화 (100ms 이내)
3. **접근성**: 키보드 내비게이션 지원
4. **테마 호환**: 라이트/다크 테마 모든 상황에서 가독성 확보

## 📝 검증 체크리스트
- [ ] 기본 프로파일 버튼 3개 정상 동작
- [ ] 커스텀 프로파일 드롭다운 독립 작동
- [ ] 프로파일 전환시 즉시 UI 업데이트
- [ ] 미리보기 패널 정보 정확성
- [ ] 키보드 접근성 지원
- [ ] 다크/라이트 테마 모든 상황 호환

## 🔄 다음 태스크 연계
성공시 → **TASK-20250810-04** (로그 뷰어 표시 내용 동기화)
실패시 → 사용자 요구사항 재분석 및 UI/UX 컨설팅 필요
