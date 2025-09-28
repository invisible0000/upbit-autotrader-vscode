# 프로파일 기능 정지 안내

> **⚠️ 중요 공지**: 2025년 8월 13일부로 환경 프로파일 기능이 정지되었습니다.

## 🚫 정지된 기능들

### 환경 프로파일 관련
- ❌ 프로파일 로드/저장/스위칭
- ❌ 커스텀 프로파일 생성
- ❌ 프로파일 메타데이터 편집
- ❌ YAML 편집기를 통한 설정 변경
- ❌ "현재 설정으로 저장" 기능

### 영향을 받는 UI
- 설정 > 프로파일 탭 (UI는 보존되나 기능 비활성화)
- 퀵 환경 버튼
- 프로파일 선택 콤보박스
- YAML 편집기

## ✅ 대안 사용법

### 로깅 설정
```yaml
# config/logging_config.yaml 직접 편집
logging:
  level: "INFO"
  console_output: "auto"
  file_logging:
    enabled: true
```

### API 설정
- API 키는 기존 방식대로 API 설정 탭에서 관리
- **중요**: API 키 손실 문제가 해결됨

### 데이터베이스 설정
- 데이터베이스 설정 탭에서 직접 관리

## 🔄 향후 계획

### Phase 2: 통합 설정 시스템
- `config/` 폴더 기반 설정 관리
- 실시간 파일 감시 및 자동 적용
- 타입 안전성과 검증 기능

### Phase 3: DB 통합
- 모든 설정의 SQLite 통합 관리
- 프로파일별 설정 오버라이드
- 설정 변경 이력 관리

## 📞 문의사항

이 변경으로 인한 문제가 있거나 질문이 있으시면:
1. `docs/UNIFIED_CONFIGURATION_MANAGEMENT_GUIDE.md` 참조
2. 개발팀에 문의

---

**참조**: [통합 설정 관리 시스템 가이드](./UNIFIED_CONFIGURATION_MANAGEMENT_GUIDE.md)
