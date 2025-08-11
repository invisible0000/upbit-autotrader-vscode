# TASK-20250810-06: 환경변수 시작 설정 UX 개선

## 📋 작업 개요
**우선순위**: 🟢 보통
**담당자**: GitHub Copilot
**생성일**: 2025-08-10
**예상 소요**: 2-3시간

## 🎯 문제 정의
현재 CLI 환경변수 설정 방식(`$env:UPBIT_ENVIRONMENT = "production"`)은 일반 사용자에게 부적합하며, 매번 명령줄에서 환경을 지정해야 하는 불편함이 있음. 직관적이고 사용자 친화적인 시작 환경 설정 방식 필요.

## 🔍 현재 상태 분석
- ❌ CLI 환경변수 설정은 개발자용 접근법
- ❌ 일반 사용자가 매번 PowerShell 명령어 입력 부담
- ❌ 환경 설정 실수로 인한 잘못된 모드 시작 위험
- ✅ 프로그램 내 환경 전환 기능은 정상 동작

## 🎨 개선 목표 UX 디자인

### **접근법 A: 시작 화면 환경 선택**
```
┌─ Upbit Auto Trading 시작 ─────────────────┐
│                                         │
│  🚀 시작 환경을 선택하세요                 │
│                                         │
│  ○ Development (개발/테스트)              │
│     • 모의거래 모드                       │
│     • 상세 디버그 로그                    │
│     • API 키 선택사항                     │
│                                         │
│  ○ Production (실거래)                   │
│     • 실제 거래 모드                      │
│     • 표준 로그                          │
│     • API 키 필수                        │
│                                         │
│  ☑ 이 설정을 기본값으로 저장               │
│                                         │
│  [시작하기]  [고급 설정]                  │
└─────────────────────────────────────────┘
```

### **접근법 B: 설정 메뉴 통합**
- 기존 Environment&Logging 탭에 "시작 환경 설정" 섹션 추가
- 프로그램 재시작시 자동 적용되는 기본 환경 지정

## 📊 서브 태스크 분할

### **서브태스크 6.1: 시작 환경 설정 저장소 구현** (난이도: ⭐⭐)
- [ ] **6.1.1**: 사용자 기본 환경 설정 저장 구조 설계
- [ ] **6.1.2**: `config/user_settings.json`에 시작 환경 저장
- [ ] **6.1.3**: 설정 로드/저장 서비스 구현

**TDD 테스트**:
```python
def test_startup_environment_storage():
    """시작 환경 설정 저장소 테스트"""
    storage = StartupEnvironmentStorage()

    # 기본값 확인
    default_env = storage.get_startup_environment()
    assert default_env == 'development'

    # 설정 저장
    storage.set_startup_environment('production')
    saved_env = storage.get_startup_environment()
    assert saved_env == 'production'

    # 재시작 시뮬레이션 (새 인스턴스)
    new_storage = StartupEnvironmentStorage()
    loaded_env = new_storage.get_startup_environment()
    assert loaded_env == 'production'
```

### **서브태스크 6.2: 시작 환경 선택 다이얼로그** (난이도: ⭐⭐⭐)
- [ ] **6.2.1**: StartupEnvironmentDialog 위젯 생성
- [ ] **6.2.2**: 환경별 설명 및 아이콘 표시
- [ ] **6.2.3**: "기본값으로 저장" 체크박스 기능

**TDD 테스트**:
```python
def test_startup_environment_dialog():
    """시작 환경 선택 다이얼로그 테스트"""
    dialog = StartupEnvironmentDialog()

    # 환경 선택 라디오 버튼 존재 확인
    dev_radio = dialog.findChild(QRadioButton, "development_radio")
    prod_radio = dialog.findChild(QRadioButton, "production_radio")
    test_radio = dialog.findChild(QRadioButton, "testing_radio")

    assert dev_radio is not None
    assert prod_radio is not None
    assert test_radio is not None

    # 기본 선택 확인 (development)
    assert dev_radio.isChecked() == True

    # 환경 변경 및 결과 확인
    prod_radio.click()
    selected_env = dialog.get_selected_environment()
    assert selected_env == 'production'
```

### **서브태스크 6.3: 프로그램 시작 로직 통합** (난이도: ⭐⭐⭐)
- [ ] **6.3.1**: `run_desktop_ui.py`에 시작 환경 선택 로직 추가
- [ ] **6.3.2**: 첫 실행시만 다이얼로그 표시, 이후 저장된 설정 사용
- [ ] **6.3.3**: 고급 사용자를 위한 CLI 환경변수 우선순위 유지

**TDD 테스트**:
```python
def test_startup_logic_integration():
    """프로그램 시작 로직 통합 테스트"""
    # 첫 실행 시뮬레이션 (설정 파일 없음)
    if Path("config/user_settings.json").exists():
        Path("config/user_settings.json").unlink()

    startup_manager = StartupManager()

    # 첫 실행시 다이얼로그 표시 확인
    with patch('StartupEnvironmentDialog.exec') as mock_dialog:
        mock_dialog.return_value = QDialog.Accepted
        env = startup_manager.get_startup_environment()
        mock_dialog.assert_called_once()

    # 두 번째 실행시 저장된 설정 사용
    with patch('StartupEnvironmentDialog.exec') as mock_dialog:
        env = startup_manager.get_startup_environment()
        mock_dialog.assert_not_called()
```

### **서브태스크 6.4: 환경별 안전장치 및 경고** (난이도: ⭐⭐)
- [ ] **6.4.1**: Production 환경 선택시 실거래 경고 표시
- [ ] **6.4.2**: API 키 미설정시 환경별 적절한 안내
- [ ] **6.4.3**: 환경 전환 이력 로그 기록

**TDD 테스트**:
```python
def test_environment_safety_measures():
    """환경별 안전장치 테스트"""
    dialog = StartupEnvironmentDialog()

    # Production 선택시 경고 확인
    with patch('QMessageBox.warning') as mock_warning:
        dialog.select_production_environment()
        mock_warning.assert_called_with(
            dialog,
            "실거래 모드 경고",
            "실제 자금이 사용됩니다. API 키가 설정되어 있는지 확인하세요."
        )

    # API 키 미설정시 안내
    with patch('ApiKeyService.has_api_keys', return_value=False):
        warning_shown = dialog.check_api_key_requirements('production')
        assert warning_shown == True
```

## 🧪 통합 테스트 시나리오

### **시나리오 A: 첫 사용자 경험**
1. 프로그램 최초 실행
2. 시작 환경 선택 다이얼로그 표시
3. Development 환경 선택 후 "기본값으로 저장" 체크
4. 프로그램 정상 시작 및 개발 환경 적용 확인
5. 다음 실행시 다이얼로그 없이 바로 개발 환경으로 시작

### **시나리오 B: 기존 사용자 경험**
1. 이미 설정이 저장된 상태에서 프로그램 실행
2. 다이얼로그 없이 저장된 환경으로 즉시 시작
3. Environment&Logging 탭에서 시작 환경 변경 가능
4. 변경 후 재시작시 새 환경으로 시작 확인

### **시나리오 C: 고급 사용자 (CLI 우선순위)**
1. CLI에서 `$env:UPBIT_ENVIRONMENT = "production"` 설정
2. 프로그램 실행시 CLI 설정이 UI 설정보다 우선 적용
3. CLI 환경변수 제거 후 재실행시 UI 설정 적용

## ✅ 완료 조건
- [ ] 시작 환경 선택 다이얼로그 정상 동작
- [ ] 선택한 환경 설정 영구 저장 및 로드
- [ ] 프로그램 재시작시 저장된 환경 자동 적용
- [ ] CLI 환경변수 우선순위 유지 (고급 사용자용)
- [ ] 모든 TDD 테스트 통과 (커버리지 90% 이상)

## 🎨 UX 요구사항 검증
1. **직관성**: 비개발자도 5초 내 환경 선택 가능
2. **안전성**: 실거래 환경 선택시 명확한 경고 제공
3. **편의성**: 한 번 설정 후 재설정 불필요
4. **유연성**: 고급 사용자의 CLI 방식 여전히 지원

**UX 테스트**:
```python
def test_user_friendliness():
    """사용자 친화성 테스트"""
    dialog = StartupEnvironmentDialog()

    # 환경 설명 명확성
    dev_description = dialog.findChild(QLabel, "development_description")
    assert "모의거래" in dev_description.text()
    assert "안전" in dev_description.text()

    prod_description = dialog.findChild(QLabel, "production_description")
    assert "실거래" in prod_description.text()
    assert "주의" in prod_description.text()

    # 버튼 텍스트 명확성
    start_btn = dialog.findChild(QPushButton, "start_button")
    assert "시작" in start_btn.text()
    assert start_btn.isDefault() == True  # Enter 키로 실행 가능
```

## 🚨 리스크 및 주의사항
1. **호환성**: 기존 CLI 환경변수 방식과 충돌 없음
2. **보안**: 환경 설정 파일 조작 공격 방어
3. **성능**: 프로그램 시작 지연 최소화 (다이얼로그 표시 1초 이내)
4. **데이터**: 설정 파일 손상시 기본값으로 안전 복원

## 📝 검증 체크리스트
- [ ] 시작 환경 다이얼로그 모든 상황 정상 동작
- [ ] 환경 설정 저장/로드 안정성 확인
- [ ] CLI vs UI 우선순위 정확한 처리
- [ ] 실거래 환경 안전장치 모든 경로 검증
- [ ] 프로그램 시작 성능 기준 충족 (3초 이내)
- [ ] 다양한 사용자 시나리오 UX 테스트 통과

## 🔄 완료 후 혜택
- **일반 사용자**: 클릭 한 번으로 원하는 환경 시작
- **개발자**: 기존 CLI 방식 여전히 사용 가능
- **안전성**: 실거래 환경 선택시 명확한 경고
- **편의성**: 환경 설정 영구 저장으로 재설정 불필요

## 🔄 다음 단계
성공시 → 전체 TASK 시리즈 완료, 안정성 테스트 진행
실패시 → 사용자 요구사항 재분석 및 UX 전문가 컨설팅
