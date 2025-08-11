# Infrastructure Layer (인프라스트럭처 계층)

## 🎯 인프라스트럭처 계층이란?
**외부 시스템과의 연결**을 담당합니다. 파일, 데이터베이스, 네트워크 등 **기술적인 구현**이 있는 곳입니다.
- **Domain에서 정의한 인터페이스를 실제로 구현**
- 파일 저장, 데이터베이스 연결, API 호출 등
- **Domain과 Application은 이 계층에 의존하면 안됨** (의존성 역전)

## 📂 폴더 구조

```
infrastructure/
├── config/                 # 설정 관리
├── database/              # 데이터베이스 연결
├── logging/               # 로깅 시스템
├── profile_storage/       # 프로파일 저장소
├── yaml_processing/       # YAML 처리
├── repositories/          # 저장소 구현체
└── services/             # 인프라 서비스
```

## 🛠️ 현재 구현된 기능들

### Profile Storage (프로파일 저장소)
- **TempFileManager**: 임시 파일 관리
  ```python
  def create_temp_file(profile_name, content)     # 임시 파일 생성
  def save_temp_to_original(temp_path, original)  # 원본에 저장
  def cleanup_temp_file(temp_path)                # 임시 파일 정리
  def generate_temp_filename(profile_name)        # 파일명 생성
  ```

- **ProfileMetadataRepository**: 메타데이터 저장소
  ```python
  def save_metadata(metadata)                     # 메타데이터 저장
  def load_metadata(profile_name)                 # 메타데이터 로드
  def delete_metadata(profile_name)               # 메타데이터 삭제
  def list_all_metadata()                         # 전체 목록
  ```

### YAML Processing (YAML 처리)
- **YamlParser**: YAML 파싱 및 검증
  ```python
  def parse_yaml_content(content)                 # YAML 파싱
  def validate_yaml_syntax(content)               # 구문 검증
  def format_yaml_content(content)                # 포맷팅
  ```

### Logging (로깅 시스템)
- **create_component_logger**: 컴포넌트별 로거 생성
  ```python
  logger = create_component_logger("ComponentName")
  logger.info("정보 메시지")
  logger.error("오류 메시지")
  ```

### Database (데이터베이스)
- **DatabaseManager**: 데이터베이스 연결 관리
- **DatabaseHealthService**: DB 상태 모니터링

### Configuration (설정 관리)
- **ConfigurationService**: 설정 파일 관리
- **DatabaseConfigRepository**: DB 설정 저장소

## 🔌 사용 방법

### Application Layer에서 Infrastructure 사용
```python
# Application Service에서 Infrastructure 서비스 주입
class ProfileMetadataService:
    def __init__(self):
        # Infrastructure 서비스들 주입
        self.metadata_repo = ProfileMetadataRepository()
        self.yaml_parser = YamlParser()
        self.temp_manager = TempFileManager()
        self.logger = create_component_logger("ProfileMetadata")
```

### Presenter에서 Infrastructure 직접 사용 금지
```python
# ❌ 잘못된 방법 - Presenter에서 Infrastructure 직접 사용
class EnvironmentProfilePresenter:
    def __init__(self):
        self.yaml_parser = YamlParser()  # 잘못됨!

# ✅ 올바른 방법 - Application Service를 통해 사용
class EnvironmentProfilePresenter:
    def __init__(self):
        self.metadata_service = ProfileMetadataService()  # 올바름!
```

## 🌍 Environment Profile 시스템에서 활용 가능한 서비스들

### 1. 프로파일 목록 로드에 활용
```python
# ProfileMetadataRepository 활용
repo = ProfileMetadataRepository()
all_metadata = repo.list_all_metadata()
```

### 2. YAML 파일 처리에 활용
```python
# YamlParser 활용
parser = YamlParser()
content = parser.parse_yaml_content(yaml_string)
validation = parser.validate_yaml_syntax(yaml_string)
```

### 3. 임시 파일 관리에 활용
```python
# TempFileManager 활용
temp_manager = TempFileManager()
temp_path = temp_manager.create_temp_file("profile_name", content)
```

### 4. 로깅에 활용
```python
# 컴포넌트별 로깅
logger = create_component_logger("EnvironmentProfile")
logger.info("프로파일 로드 시작")
```

## 🔧 현재 Environment Profile에서 누락된 Infrastructure 연동

### 문제점
1. **ProfileMetadataService가 Infrastructure 제대로 활용 안함**
2. **콤보박스 목록 로드가 구현되지 않음**
3. **YAML 파싱에 Infrastructure YamlParser 미사용**

### 해결 방안
```python
# ProfileMetadataService에 Infrastructure 서비스 주입 필요
class ProfileMetadataService:
    def __init__(self):
        self.metadata_repo = ProfileMetadataRepository()  # 추가 필요
        self.yaml_parser = YamlParser()                   # 추가 필요
        self.logger = create_component_logger("ProfileMetadata")
```

## 💡 Infrastructure 활용 팁

1. **의존성 주입**: 생성자에서 Infrastructure 서비스들 주입
2. **인터페이스 사용**: 직접 구현체 의존보다는 인터페이스 의존
3. **에러 처리**: Infrastructure에서 발생한 예외를 Domain 예외로 변환
4. **로깅 활용**: 모든 Infrastructure 작업에 로깅 적용
