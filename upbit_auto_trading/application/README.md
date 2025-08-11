# Application Layer (애플리케이션 계층)

## 🎯 애플리케이션 계층이란?
**사용자의 요청을 처리**하는 곳입니다. UI에서 "저장 버튼"을 누르면 여기서 처리합니다.
- 사용자 요청을 받아서 **Domain과 Infrastructure를 조율**
- **트랜잭션 관리**, **보안**, **권한 검사** 등
- "프로파일 저장해줘", "환경 전환해줘" 같은 **사용자 의도** 구현

## 📂 폴더 구조

```
application/
├── use_cases/         # 유즈케이스 (사용자 시나리오)
├── services/          # 애플리케이션 서비스 (복합 작업)
├── dto/              # 데이터 전송 객체
└── interfaces/       # 인터페이스 정의
```

## 🎬 Use Cases vs Services 차이점

### Use Cases (유즈케이스) - "사용자 시나리오"
- **한 번의 사용자 액션**을 처리
- 예: "프로파일 편집 시작", "프로파일 저장", "편집 취소"

### Services (애플리케이션 서비스) - "복합 작업"
- **여러 유즈케이스를 조합**한 복잡한 작업
- 예: "프로파일 전체 관리", "메타데이터 통합 관리"

## 🚀 현재 구현된 기능들

### Use Cases (유즈케이스)
- **ProfileEditorUseCase**: 프로파일 편집 시나리오
  ```python
  def start_edit_session(profile_name, is_new)    # 편집 시작
  def save_edit_session(session, content)         # 편집 저장
  def cancel_edit_session(session)                # 편집 취소
  def validate_profile_content(content)           # 내용 검증
  ```

- **TempFileManagementUseCase**: 임시 파일 관리
  ```python
  def create_temp_file(profile_name, content)     # 임시 파일 생성
  def apply_temp_to_original(profile_name, temp)  # 원본에 적용
  def cleanup_expired_temp_files()                # 만료된 파일 정리
  ```

- **ProfileMetadataUseCase**: 메타데이터 관리
  ```python
  def create_metadata(name, description)          # 메타데이터 생성
  def update_metadata(name, metadata)             # 메타데이터 수정
  def get_display_name(profile_name)              # 표시명 조회
  def list_profiles_with_metadata()               # 전체 목록
  ```

### Services (애플리케이션 서비스)
- **ProfileMetadataService**: 메타데이터 통합 관리
  ```python
  def create_profile_metadata(name, desc, type)   # 메타데이터 생성
  def get_profile_display_name(name)              # 표시명 가져오기
  def list_all_profiles()                         # 전체 프로파일 목록
  ```

- **ProfileEditSessionService**: 편집 세션 통합 관리
  ```python
  def create_edit_session(metadata, content)      # 편집 세션 생성
  def end_session(session_id)                     # 세션 종료
  def get_active_sessions()                       # 활성 세션 목록
  ```

- **ProfileValidationService**: 검증 통합 관리
  ```python
  def validate_yaml_content(content)              # YAML 검증
  def validate_profile_structure(profile)         # 구조 검증
  def get_validation_errors(content)              # 오류 목록
  ```

- **ConfigProfileService**: 설정 프로파일 관리 (기존 호환)
  ```python
  def get_current_environment()                   # 현재 환경 조회
  def switch_environment(env_name)                # 환경 전환
  def get_available_environments()                # 사용 가능한 환경
  def load_environment_config(env_name)           # 환경 설정 로드
  ```

## 🔄 호출 흐름 예시

```
UI에서 "프로파일 저장" 버튼 클릭
    ↓
EnvironmentProfilePresenter (UI Layer)
    ↓
ProfileEditSessionService.save_session() (Application Service)
    ↓
ProfileEditorUseCase.save_edit_session() (Use Case)
    ↓
ProfileMetadata.validate() (Domain Entity)
    ↓
TempFileManager.save_temp_to_original() (Infrastructure)
```

## 🎯 언제 어느 것을 사용해야 할까?

### Use Cases를 직접 호출하는 경우
- **단순한 단일 작업**
- UI에서 바로 한 가지 작업만 수행

### Services를 호출하는 경우
- **복잡한 조합 작업**
- 여러 단계가 필요한 작업
- **현재 환경 프로파일 시스템은 Services 사용 권장**

## 📋 현재 환경 프로파일 시스템에서 사용법

```python
# Presenter에서 이렇게 사용하세요
from upbit_auto_trading.application.services.profile_metadata_service import ProfileMetadataService
from upbit_auto_trading.application.services.profile_edit_session_service import ProfileEditSessionService

# 프로파일 목록 가져오기
profiles = metadata_service.list_all_profiles()

# 편집 세션 시작
session = edit_service.create_edit_session(metadata, content)
```
