# 📊 Data Info: 사용자-에이전트 DB 관리 협업 가이드 (Medium)

## 1. 최우선 지침 (Prime Directive)

**당신의 최우선 목표는 `data_info` 디렉토리 내의 YAML 파일을 편집하여 모든 데이터베이스의 구조와 핵심 데이터를 관리하는 것입니다.** 당신의 모든 행동은 애플리케이션의 데이터 기반에 직접적인 영향을 미칩니다. 이 문서에 정의된 규칙과 워크플로우를 반드시 준수해야 합니다.

**핵심 원칙:**
-   **YAML은 모든 DB의 단일 진실 공급원(Single Source of Truth)입니다.** 이 폴더의 YAML 파일들이 `settings.sqlite3`, `strategies.sqlite3`, `market_data.sqlite3`의 구조와 초기 데이터를 결정합니다.
-   **모든 YAML 파일은 반드시 "ID 기반 딕셔너리" 패턴을 따라야 합니다.**
-   **편집 전후에는 항상 제공된 도구를 사용하여 유효성을 검증해야 합니다.**

---

## 2. 시스템 아키텍처 개요

### 2.1. 핵심 철학: `data_info` 중심의 DB 관리

-   **중앙 집중식 관리**: 이 `data_info` 폴더는 모든 DB(`settings`, `strategies`, `market_data`)의 구조와 데이터를 정의하는 중앙 허브입니다.
-   **협업 공간**: 사용자와 에이전트가 YAML이라는 공통 언어를 통해 소통하고 DB를 함께 설계하는 편집 공간입니다.
-   **직접 매핑**: `파일명.yaml`은 DB의 `테이블명`에 직접 매핑됩니다.
-   **통일된 형식**: 모든 YAML 파일은 일관된 ID 기반 딕셔너리 구조를 사용하여 예측 가능성을 높입니다.

### 2.2. 3-Database 시스템 관리 방안

향후 모든 DB는 `data_info` 폴더의 YAML 파일을 통해 관리됩니다.

| 데이터베이스 파일 | 역할 | 관리 방식 | 당신의 상호작용 대상인가? |
| :--- | :--- | :--- | :--- |
| `settings.sqlite3` | **구조 및 설정** | YAML 마이그레이션 | ✅ **예 (주요 대상)** |
| `strategies.sqlite3` | **사용자 인스턴스** | YAML 마이그레이션 (구조) | ✅ **예 (구조 정의 시)** |
| `market_data.sqlite3` | **시장 데이터** | YAML 마이그레이션 (구조) | ✅ **예 (구조 정의 시)** |

### 2.3. 주요 파일 매핑 (`settings.sqlite3` 기준)

| YAML 파일 | 매핑 테이블 | 목적 |
| :--- | :--- | :--- |
| `tv_trading_variables.yaml` | `tv_trading_variables` | 핵심 변수 정의 |
| `tv_variable_parameters.yaml` | `tv_variable_parameters` | 변수 파라미터 |
| `tv_help_texts.yaml` | `tv_help_texts` | UI 도움말 텍스트 |
| `tv_placeholder_texts.yaml` | `tv_placeholder_texts` | UI 플레이스홀더 예시 |
| `tv_indicator_categories.yaml` | `tv_indicator_categories` | 지표 카테고리 시스템 |
| `tv_parameter_types.yaml` | `tv_parameter_types` | 파라미터 타입 정의 |
| `tv_comparison_groups.yaml` | `tv_comparison_groups` | 호환성 그룹 정의 |

---

## 3. 핵심 워크플로우: YAML → DB

### 1단계: 분석 및 준비 (필수 선행 작업)

**목표**: 변경을 수행하기 전에 현재 상태를 이해합니다.

```powershell
# 1. 현재 DB 상태 보기
python tools/super_db_table_viewer.py settings

# 2. 비교를 위해 현재 DB 데이터를 YAML로 추출
python tools/super_db_extraction_db_to_yaml.py --tables tv_trading_variables
```

### 2단계: YAML 편집 (당신의 핵심 임무)

**목표**: 형식 규칙을 엄격히 준수하며 사용자 요청에 따라 YAML 파일을 수정합니다.

**편집 전 체크리스트:**
-   [ ] 새 변수에 파라미터가 필요한가? (`parameter_required: true/false`)
-   [ ] 어떤 `purpose_category`, `chart_category`, `comparison_group`에 속하는가?
-   [ ] 모든 필수 필드가 존재하는가? (섹션 4.2 참조)
-   [ ] ID가 고유하며 `UPPERCASE_SNAKE_CASE` 형식인가?

### 3단계: 마이그레이션 및 검증 (사용자/시스템 작업)

**목표**: YAML 변경사항을 데이터베이스에 적용하고 결과를 검증합니다.

```powershell
# 1. 사용자가 마이그레이션 실행
python tools/super_db_migration_yaml_to_db.py --yaml-files tv_trading_variables.yaml

# 2. DB 상태를 다시 확인하여 마이그레이션 검증
python tools/super_db_table_viewer.py settings

# 3. (중요) 다시 YAML로 추출하여 비교 검증
python tools/super_db_extraction_db_to_yaml.py --tables tv_trading_variables
# 이제 새로 추출된 파일과 당신이 편집한 파일이 동일해야 합니다.
```

---

## 4. YAML 데이터 구조 규칙 (엄격)

### 4.1. 보편적 형식: ID 기반 딕셔너리

**이 패턴은 이 디렉토리의 모든 `.yaml` 파일에 대해 필수입니다.**

```yaml
# ✅ 올바른 형식: ID 기반 딕셔너리
UNIQUE_ID_KEY:
  {type}_id: "UNIQUE_ID_KEY"
  display_name_ko: "한글 이름"
  display_name_en: "English Name"
  description: "명확한 설명."
  # ... 기타 필드
```

### 4.2. 필수 필드 (모든 파일)

모든 YAML 파일의 모든 항목은 다음 필드를 포함해야 합니다:
-   `{type}_id`: `string`, `UPPERCASE_SNAKE_CASE`, 최상위 키와 일치해야 함.
-   `display_name_ko`: `string`, 사용자 대상 한국어 이름.
-   `display_name_en`: `string`, 사용자 대상 영어 이름.
-   `description`: `string`, 항목에 대한 상세 설명.

---

## 5. 도구 참조 (실제 구현된 `super_*` 도구)

### 5.1. 분석 및 검증 도구

-   **DB 상태 보기**: `python tools/super_db_table_viewer.py [settings|strategies|market_data]`
-   **DB 스키마 검증**: `python tools/super_db_schema_validator.py`
-   **코드 참조 분석**: `python tools/super_db_table_reference_code_analyzer.py --tables [테이블명]`
-   **파라미터 테이블 분석**: `python tools/super_db_analyze_parameter_table.py`
-   **시스템 상태 모니터링**: `python tools/super_db_health_monitor.py`

### 5.2. 데이터 추출 및 마이그레이션 도구

-   **YAML을 DB로 마이그레이션**: `python tools/super_db_migration_yaml_to_db.py --yaml-files [파일명]`
-   **DB를 YAML로 추출**: `python tools/super_db_extraction_db_to_yaml.py --tables [테이블명]`
-   **데이터 마이그레이터**: `python tools/super_db_data_migrator.py`
-   **DB 스키마 추출**: `python tools/super_db_schema_extractor.py`
-   **DB 구조 생성**: `python tools/super_db_structure_generator.py`

### 5.3. YAML 편집 및 관리 워크플로우 도구

-   **YAML 편집 워크플로우**: `python tools/super_db_yaml_editor_workflow.py`
-   **YAML 파일 병합**: `python tools/super_db_yaml_merger.py`
-   **YAML 간단 비교**: `python tools/super_db_yaml_simple_diff.py`

### 5.4. 디버깅 및 운영 도구

-   **DB 직접 쿼리**: `python tools/super_db_direct_query.py`
-   **롤백 관리자**: `python tools/super_db_rollback_manager.py`
-   **경로 매핑 디버깅**: `python tools/super_db_debug_path_mapping.py`

---

## 6. 품질 보증 프로토콜

당신의 편집은 아래의 검증 체인을 통과할 수 있어야 합니다.

-   **1단계: 구문 검증**: 올바른 YAML 구문 (들여쓰기, 따옴표 등).
-   **2단계: 구조 검증**: ID 기반 딕셔너리 패턴 준수 및 필수 필드 존재.
-   **3단계: 데이터 무결성 검증**: 중복 ID 없음, 모든 파일 간 참조 유효, 논리적 모순 없음.
-   **4단계: 시스템 통합 검증**: 성공적인 DB 마이그레이션 및 애플리케이션(`run_desktop_ui.py`)의 정상 동작 확인.

---
*이 문서는 LLM 에이전트와 사용자가 `data_info` 폴더를 중심으로 협업하여 DB를 관리하기 위한 핵심 지침입니다.*
*마지막 업데이트: 2025-08-02*
