# Domain Layer (도메인 계층)

## 🎯 도메인 계층이란?
**비즈니스 핵심 로직**이 있는 곳입니다. 실제 업무 규칙과 개념들을 코드로 표현합니다.
- "프로파일이 유효한가?", "세션이 활성화되어 있나?" 같은 **비즈니스 규칙**
- **외부 기술에 의존하지 않음** (데이터베이스, UI, 파일 시스템과 독립)

## 📂 폴더 구조

```
domain/
├── entities/           # 엔티티 (핵심 비즈니스 객체)
├── value_objects/      # 값 객체 (불변 데이터)
├── services/          # 도메인 서비스 (복잡한 비즈니스 로직)
├── repositories/      # 저장소 인터페이스 (실제 구현은 Infrastructure에)
└── events/           # 도메인 이벤트
```

## 🏷️ 현재 구현된 기능들

### Entities (엔티티)
- **ProfileEditorSession**: 프로파일 편집 세션 관리
  - 편집 중인 프로파일 정보
  - 임시 파일 경로
  - 세션 상태 (활성/비활성)
  - 저장 가능 여부 검증

- **ProfileMetadata**: 프로파일 메타데이터
  - 프로파일 이름, 설명
  - 생성일시, 생성자
  - 환경변수 목록
  - 프로파일 타입 (기본/커스텀)

### Value Objects (값 객체)
- **ProfileDisplayName**: UI 표시용 프로파일 이름
- **YamlContent**: YAML 내용 검증 및 파싱

### Services (도메인 서비스)
- **ProfileValidationService**: 프로파일 유효성 검증
  - YAML 구문 검사
  - 환경 프로파일 구조 검증
  - 비즈니스 규칙 검증

## 🔍 사용 예시

```python
# 엔티티 생성
session = ProfileEditorSession(
    session_id="edit_001",
    profile_metadata=metadata,
    temp_file_path="/tmp/config.yaml"
)

# 비즈니스 규칙 검증
if session.can_save():
    # 저장 가능
    pass
```

## ⚠️ 중요한 원칙
1. **외부 기술 의존 금지**: 데이터베이스, 파일 시스템 직접 접근 안함
2. **순수한 비즈니스 로직**: "업무 규칙"만 포함
3. **테스트 용이성**: 외부 의존성 없이 단위 테스트 가능
