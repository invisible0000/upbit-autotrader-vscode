# TASK-20250810-05: 프로파일 전환시 API 키 유지

## 📋 작업 개요
**우선순위**: 🔴 긴급
**담당자**: GitHub Copilot
**생성일**: 2025-08-10
**예상 소요**: 1-2시간

## 🎯 문제 정의
환경 프로파일 전환시 API 키가 초기화되어 사용자가 매번 재입력해야 하는 문제. 이는 사용자 피로도 증가와 API 키 노출 위험성을 높이는 보안/UX 문제임.

## 🔍 현재 상태 분석
- ❌ development ↔ production 프로파일 전환시 API 키 재입력 요구
- ❌ ConfigProfileService가 보안 데이터까지 덮어쓰는 문제
- ❌ 프로파일 전환 = 전체 환경변수 초기화로 인한 부작용
- ✅ API 키는 별도 보안 저장소(`config/secure/`)에 관리됨

## 🔒 보안 요구사항
1. **격리 원칙**: API 키는 환경 프로파일과 독립적으로 관리
2. **지속성**: 프로파일 전환과 무관하게 API 키 유지
3. **선택적 적용**: 환경변수 중 보안 관련 항목 제외 처리
4. **감사 로깅**: API 키 관련 작업 모든 로그 기록

## 📊 서브 태스크 분할

### **서브태스크 5.1: 환경변수 분류 체계 수립** (난이도: ⭐⭐)
- [ ] **5.1.1**: 보안 환경변수 vs 일반 환경변수 구분 정의
- [ ] **5.1.2**: ConfigProfileService에서 보안 변수 제외 로직 추가
- [ ] **5.1.3**: 화이트리스트 방식으로 안전한 환경변수만 관리

**TDD 테스트**:
```python
def test_environment_variable_classification():
    """환경변수 분류 테스트"""
    service = ConfigProfileService()

    # 일반 환경변수 (프로파일 관리 대상)
    general_vars = service.get_general_environment_variables()
    expected_general = [
        'UPBIT_LOG_LEVEL', 'UPBIT_LOG_CONTEXT', 'UPBIT_LOG_SCOPE',
        'UPBIT_CONSOLE_OUTPUT', 'UPBIT_COMPONENT_FOCUS'
    ]
    for var in expected_general:
        assert var in general_vars

    # 보안 환경변수 (프로파일 관리 제외)
    secure_vars = service.get_secure_environment_variables()
    expected_secure = ['UPBIT_ACCESS_KEY', 'UPBIT_SECRET_KEY']
    for var in expected_secure:
        assert var not in general_vars
        assert var in secure_vars
```

### **서브태스크 5.2: 선택적 환경변수 적용 로직** (난이도: ⭐⭐⭐)
- [ ] **5.2.1**: `_apply_env_vars_bulk()` 메서드 수정 - 보안 변수 스킵
- [ ] **5.2.2**: 프로파일 전환시 API 키 보존 로직 추가
- [ ] **5.2.3**: 환경변수 백업/복원 메커니즘 구현

**TDD 테스트**:
```python
def test_selective_environment_application():
    """선택적 환경변수 적용 테스트"""
    service = ConfigProfileService()

    # API 키 설정
    os.environ['UPBIT_ACCESS_KEY'] = 'test_access_key'
    os.environ['UPBIT_SECRET_KEY'] = 'test_secret_key'
    original_access_key = os.environ['UPBIT_ACCESS_KEY']
    original_secret_key = os.environ['UPBIT_SECRET_KEY']

    # 프로파일 전환
    service.switch_profile('production')

    # API 키 유지 확인
    assert os.environ['UPBIT_ACCESS_KEY'] == original_access_key
    assert os.environ['UPBIT_SECRET_KEY'] == original_secret_key

    # 일반 환경변수는 변경됨 확인
    assert os.environ['UPBIT_LOG_LEVEL'] == 'INFO'  # production 설정
```

### **서브태스크 5.3: API 키 상태 모니터링** (난이도: ⭐⭐)
- [ ] **5.3.1**: 프로파일 전환 전후 API 키 상태 검증
- [ ] **5.3.2**: API 키 손실 감지 및 경고 시스템
- [ ] **5.3.3**: 자동 복구 메커니즘 (백업에서 복원)

**TDD 테스트**:
```python
def test_api_key_state_monitoring():
    """API 키 상태 모니터링 테스트"""
    service = ConfigProfileService()
    monitor = ApiKeyStateMonitor()

    # 초기 상태 기록
    initial_state = monitor.capture_api_key_state()
    assert initial_state['has_access_key'] == True
    assert initial_state['has_secret_key'] == True

    # 프로파일 전환 후 상태 비교
    service.switch_profile('testing')
    after_state = monitor.capture_api_key_state()

    # API 키 유지 확인
    assert after_state['has_access_key'] == initial_state['has_access_key']
    assert after_state['has_secret_key'] == initial_state['has_secret_key']
```

### **서브태스크 5.4: 사용자 경험 개선** (난이도: ⭐)
- [ ] **5.4.1**: 프로파일 전환시 "API 키 유지됨" 알림 표시
- [ ] **5.4.2**: API 키 상태 실시간 표시기 개선
- [ ] **5.4.3**: 보안 상태 요약 정보 제공

**UX 테스트**:
```python
def test_user_experience_improvements():
    """사용자 경험 개선 테스트"""
    widget = EnvironmentProfileWidget()

    # 프로파일 전환시 알림 확인
    with patch('QMessageBox.information') as mock_info:
        widget.switch_profile('production')
        mock_info.assert_called_with(
            widget,
            "프로파일 전환 완료",
            "API 키가 안전하게 유지되었습니다."
        )

    # API 키 상태 표시기 확인
    status_indicator = widget.findChild(QLabel, "api_key_status")
    assert "🔐 API 키: 설정됨" in status_indicator.text()
```

## 🧪 통합 테스트 시나리오

### **시나리오 A: 개발 → 프로덕션 전환**
1. development 환경에서 API 키 설정
2. Upbit API 연결 확인 (성공)
3. production 프로파일로 전환
4. API 키 유지 확인 + 프로덕션 환경변수 적용 확인
5. 실거래 API 연결 테스트 (성공)

### **시나리오 B: 다중 프로파일 순환 전환**
1. development → testing → production → development
2. 각 전환 단계마다 API 키 유지 확인
3. 로그 레벨 등 일반 환경변수는 정상 변경 확인
4. 최종적으로 API 연결 상태 정상 유지

### **시나리오 C: API 키 손실 복구**
1. 의도적으로 API 키 환경변수 삭제 (시뮬레이션)
2. 프로파일 전환시 손실 감지 확인
3. 백업에서 자동 복구 또는 사용자 알림 확인

## ✅ 완료 조건
- [ ] 모든 프로파일 전환시 API 키 100% 유지
- [ ] 보안 환경변수와 일반 환경변수 명확한 분리 처리
- [ ] API 키 손실 감지 및 복구 메커니즘 동작
- [ ] 사용자에게 적절한 상태 피드백 제공
- [ ] 모든 TDD 테스트 통과 (커버리지 95% 이상)

## 🔒 보안 검증 체크리스트
- [ ] API 키가 로그에 평문으로 노출되지 않음
- [ ] 프로파일 YAML 파일에 API 키 저장되지 않음
- [ ] 메모리 덤프시 API 키 보호 (가능한 범위 내)
- [ ] 환경변수 백업/복원시 암호화 적용
- [ ] 감사 로그에 API 키 관련 모든 작업 기록

## 🚨 리스크 및 주의사항
1. **데이터 손실**: API 키 백업 메커니즘 필수
2. **보안 취약점**: 환경변수 조작 공격 방어
3. **성능**: 프로파일 전환 지연 최소화 (1초 이내)
4. **호환성**: 기존 API 키 저장 방식과 100% 호환

## 📝 최종 검증 시나리오
```python
def test_complete_profile_switching_with_api_keys():
    """완전한 프로파일 전환 + API 키 유지 테스트"""
    # 1. 초기 설정
    service = ConfigProfileService()
    api_service = ApiKeyService()

    # API 키 설정
    api_service.save_api_keys("test_access", "test_secret")
    initial_connection = api_service.test_connection()
    assert initial_connection == True

    # 2. 프로파일 전환 시퀀스
    profiles = ['development', 'production', 'testing', 'development']
    for profile in profiles:
        service.switch_profile(profile)

        # API 키 유지 확인
        connection_status = api_service.test_connection()
        assert connection_status == True

        # 환경변수 적용 확인
        assert os.environ['UPBIT_LOG_CONTEXT'] == profile

    # 3. 최종 상태 검증
    final_keys = api_service.load_api_keys()
    assert final_keys['access_key'] == "test_access"
    assert final_keys['secret_key'] == "test_secret"
```

## 🔄 다음 태스크 연계
성공시 → **TASK-20250810-02** (UI 설정 탭 저장/복원 버튼 수정)
실패시 → API 키 관리 아키텍처 전면 재설계 필요
