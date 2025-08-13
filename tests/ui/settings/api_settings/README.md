# API 키 설정 기능 테스트

이 디렉토리는 업비트 자동매매 시스템의 API 키 설정 탭 기능에 대한 유닛 테스트를 포함합니다.

## 테스트 구조

```
tests/
├── conftest.py                                # 테스트 공용 픽스처 및 설정
├── infrastructure/
│   └── services/
│       └── test_api_key_service.py           # API 키 서비스 테스트
└── ui/
    └── settings/
        └── api_settings/
            ├── test_api_settings_presenter.py         # 프레젠터 테스트
            ├── test_api_settings_view_simplified.py   # 뷰 테스트 (간소화)
            └── test_api_key_workflow_integration.py   # 통합 테스트
```

## 테스트 범위

### 1. Infrastructure Layer 테스트 (`test_api_key_service.py`)
- ✅ API 키 저장/로드/삭제 기능
- ✅ 암호화/복호화 동작
- ✅ 스마트 삭제 로직
- ✅ 깔끔한 재생성 기능
- ✅ TTL 기반 캐싱 시스템
- ✅ 에러 처리 및 유효성 검증

### 2. Presenter Layer 테스트 (`test_api_settings_presenter.py`)
- ✅ MVP 패턴 준수 검증
- ✅ API 키 설정 로드/저장 로직
- ✅ API 연결 테스트 기능
- ✅ 입력 변경 처리
- ✅ 버튼 상태 관리
- ✅ 계좌 정보 파싱 (다양한 API 응답 형식)

### 3. View Layer 테스트 (`test_api_settings_view_simplified.py`)
- ✅ UI 컴포넌트 초기화
- ✅ Presenter 연결
- ✅ 사용자 이벤트 처리
- ✅ 메시지 박스 표시
- ✅ UI 상태 업데이트

### 4. 통합 테스트 (`test_api_key_workflow_integration.py`)
- ✅ 전체 API 키 워크플로우
- ✅ 버튼 상태 변화 시나리오
- ✅ 입력 처리 흐름
- ✅ 에러 상황 처리
- ✅ 다양한 API 응답 파싱

## 테스트 실행 방법

### 모든 API 키 설정 테스트 실행
```powershell
pytest tests/ui/settings/api_settings/ -v
```

### 특정 테스트 파일만 실행
```powershell
# Infrastructure 테스트
pytest tests/infrastructure/services/test_api_key_service.py -v

# Presenter 테스트
pytest tests/ui/settings/api_settings/test_api_settings_presenter.py -v

# 통합 테스트
pytest tests/ui/settings/api_settings/test_api_key_workflow_integration.py -v
```

### 특정 테스트 케이스만 실행
```powershell
# API 키 저장 테스트만
pytest tests/infrastructure/services/test_api_key_service.py::TestApiKeyServiceSaving -v

# 워크플로우 통합 테스트만
pytest tests/ui/settings/api_settings/test_api_key_workflow_integration.py::TestApiKeyWorkflow::test_complete_api_key_workflow -v
```

### 커버리지와 함께 실행
```powershell
pytest tests/ui/settings/api_settings/ --cov=upbit_auto_trading.ui.desktop.screens.settings.api_settings --cov=upbit_auto_trading.infrastructure.services.api_key_service --cov-report=html
```

## 테스트 결과 예시

성공적인 테스트 실행 시 다음과 같은 출력을 확인할 수 있습니다:

```
============================ test session starts ============================
platform win32 -- Python 3.13.0, pytest-8.4.1, pluggy-1.5.0 -- pytest
collected 45 items

tests/infrastructure/services/test_api_key_service.py::TestApiKeyServiceInterface::test_implements_interface PASSED
tests/infrastructure/services/test_api_key_service.py::TestApiKeyServiceSaving::test_save_api_keys_with_valid_data PASSED
tests/ui/settings/api_settings/test_api_settings_presenter.py::TestApiSettingsLoading::test_load_api_settings_with_saved_keys PASSED
tests/ui/settings/api_settings/test_api_key_workflow_integration.py::TestApiKeyWorkflow::test_complete_api_key_workflow PASSED

========================= 45 passed in 2.34s =========================
```

## 테스트 원칙

### Given-When-Then 패턴
모든 테스트는 명확한 Given-When-Then 구조를 따릅니다:

```python
def test_save_api_keys_with_valid_data(self, mock_service, sample_credentials):
    """Given: 유효한 API 키 데이터가 주어졌을 때
    When: save_api_keys를 호출하면
    Then: 암호화되어 저장되어야 함"""
    # Given
    service = ApiKeyService(mock_repository)

    # When
    result = service.save_api_keys(access_key, secret_key, trade_permission)

    # Then
    assert result is True
```

### DDD 아키텍처 준수
- Domain Layer: 외부 의존성 없는 순수 비즈니스 로직
- Infrastructure Layer: 외부 시스템과의 연동 (DB, API, 파일)
- Presentation Layer: UI와 사용자 상호작용
- Application Layer: 유스케이스 조합

### Mock을 통한 의존성 격리
- PyQt6 위젯들은 Mock으로 대체
- 외부 API 호출은 Mock으로 격리
- 파일 시스템 작업은 임시 디렉토리 사용

## 추가할 테스트

향후 추가할 수 있는 테스트들:

1. **성능 테스트**: TTL 캐싱 성능 검증
2. **보안 테스트**: 암호화/복호화 강도 검증
3. **UI 통합 테스트**: 실제 PyQt6 위젯과의 통합
4. **네트워크 테스트**: 실제 업비트 API와의 연동 (선택적)

## 문제 해결

### 테스트 실행 오류
```powershell
# 의존성 설치
pip install pytest pytest-cov

# 모듈 경로 설정
$env:PYTHONPATH = "d:\projects\upbit-autotrader-vscode"
```

### Import 오류
프로젝트 루트에서 실행하고 PYTHONPATH가 올바르게 설정되었는지 확인하세요.

### Mock 관련 오류
conftest.py의 픽스처들이 올바르게 로드되는지 확인하세요.
