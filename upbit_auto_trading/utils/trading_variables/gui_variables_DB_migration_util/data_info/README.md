# 📊 Data Info - 사용자↔에이전트 협업 공간

이 폴더는 **사용자와 AI 에이전트가 함께 DB 스키마를 관리하는 협업 공간**입니다.

## 🎯 설계 철학

- **Single Source of Truth**: DB가 모든 변수 정의의 단일 진실 소스
- **YAML Collaboration Space**: 이 폴더는 사용자↔에이전트 소통 및 편집 공간
- **Zero Hardcoding**: `variable_definitions.py`는 100% DB 기반 자동 생성
- **Direct Mapping**: YAML 파일명 = 테이블명 (완벽 매핑)

## 📋 파일 구조

### 🏗️ 스키마 파일
- `upbit_autotrading_unified_schema.sql` - **기준 통합 스키마** (모든 테이블 포함)
- `schema_extended_v3.sql` - 이전 확장 스키마 (참고용)
- `schema_new02.sql` - 기존 기본 스키마 (호환성 유지)

### 📝 YAML 데이터 파일들 (테이블명과 직접 매핑)

| YAML 파일 | 대응 테이블 | 용도 |
|-----------|-------------|------|
| `tv_help_texts.yaml` | `tv_help_texts` | 📝 도움말 텍스트 관리 |
| `tv_placeholder_texts.yaml` | `tv_placeholder_texts` | 🎯 플레이스홀더 및 사용 예시 |
| `tv_indicator_categories.yaml` | `tv_indicator_categories` | 📂 지표 카테고리 체계 |
| `tv_parameter_types.yaml` | `tv_parameter_types` | 🔧 파라미터 타입 정의 |
| `tv_indicator_library.yaml` | `tv_indicator_library` | 📚 지표 라이브러리 상세 정보 |
| `tv_workflow_guides.yaml` | `tv_workflow_guides` | 📋 워크플로우 가이드 |

### 🔄 마이그레이션 워크플로우

1. **사용자/에이전트**: YAML 파일에서 내용 편집
2. **시스템**: YAML → DB 자동 마이그레이션 
3. **시스템**: DB → `variable_definitions.py` 자동 생성
4. **결과**: 하드코딩 없는 완전 DB 기반 시스템

## � 사용 방법

### 새로운 지표 추가 시:
1. `tv_indicator_categories.yaml`에서 카테고리 확인/추가
2. `tv_help_texts.yaml`에 도움말 추가
3. `tv_placeholder_texts.yaml`에 플레이스홀더 추가
4. `tv_indicator_library.yaml`에 상세 정보 추가
5. Advanced Migration Tool로 DB 동기화

### 기존 지표 수정 시:
1. 해당 YAML 파일에서 내용 수정
2. Advanced Migration Tool로 DB 동기화
3. 자동으로 `variable_definitions.py` 재생성

## ⚠️ 중요 사항

- **절대 `variable_definitions.py`를 직접 수정하지 마세요** - DB에서 자동 생성됩니다
- **YAML 파일 변경 후 반드시 DB 마이그레이션을 실행하세요**
- **스키마 변경 시 백업을 만들고 테스트하세요**

## 🛠️ 도구들

- `upbit_auto_trading\utils\trading_variables\gui_variables_DB_migration_util\` - DB 마이그레이션 도구
- Advanced Migration Tab - YAML ↔ DB 동기화 GUI

---
*작성일: 2025-07-30*  
*업데이트: 테이블명 직접 매핑 체계로 개선*
3. 테스트 환경에서 먼저 검증
4. 단계별로 진행하며 각 단계 확인

## 📊 효과 및 장점

### 토큰 효율성
- **기존**: 전체 코드 파일을 읽고 분석 (수천 토큰)
- **개선**: 구조화된 YAML 파일만 읽기 (수백 토큰)
- **절약률**: 약 70-80% 토큰 사용량 감소

### 협업 효율성
- **명확한 역할 분담**: LLM은 데이터 편집, 사용자는 GUI 조작
- **단계별 검증**: 각 단계마다 확인 포인트 존재
- **자동화된 반영**: 편집 → DB → 코드로 자동 동기화

### 품질 개선
- **일관성**: 표준화된 패턴과 규칙
- **완전성**: 누락 없는 정보 관리
- **추적성**: 변경 이력 관리 가능

## 🚀 확장 가능성

### 추가 가능한 파일들
- `validation_rules.yaml`: 파라미터 검증 규칙
- `ui_layouts.yaml`: GUI 레이아웃 정의
- `test_scenarios.yaml`: 테스트 시나리오
- `performance_metrics.yaml`: 성능 지표 정의

### 다른 시스템 적용
이 패턴은 다른 복잡한 설정 관리 시스템에도 적용 가능:
- 전략 설정 관리
- UI 컴포넌트 정의
- API 스키마 관리
- 설정 파일 생성

## ⚠️ 주의사항

### YAML 편집 시
- 들여쓰기는 반드시 공백(space) 사용
- 콜론(:) 뒤에는 공백 필요
- 특수문자는 따옴표로 감싸기
- 리스트 항목은 하이픈(-) 사용

### 데이터 일관성
- 여러 파일 간 참조 관계 확인
- 카테고리명, 지표명 일치 확인
- 파라미터 타입 정의 일치 확인

### 백업 및 복구
- 중요한 변경 전 반드시 백업
- 문제 발생 시 즉시 이전 버전으로 복구
- 변경 로그 유지 권장

## 📞 문제 해결

### 일반적인 오류
1. **YAML 파싱 오류**: 문법 검사 도구 사용
2. **마이그레이션 실패**: 스키마 호환성 확인
3. **동기화 문제**: DB 연결 및 권한 확인

### 도움이 필요한 경우
1. `workflow_guide.yaml`의 troubleshooting 섹션 참조
2. GUI 도구의 로그 메시지 확인
3. 백업에서 복구 후 단계별 재시도

---

💡 **이 시스템을 통해 LLM 에이전트와 사용자가 효율적으로 협업하여 복잡한 트레이딩 시스템을 쉽게 관리할 수 있습니다!**
