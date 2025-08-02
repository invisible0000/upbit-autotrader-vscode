# TriggerBuilder Core Components

## 📋 개요

이 폴더는 **트리거 빌더 시스템의 핵심 컴포넌트들**을 포함하고 있습니다. 각 컴포넌트는 특정 책임을 가지며, 상호 연결되어 완전한 트리거 빌더 시스템을 구성합니다.

## 🏗️ 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                    TriggerBuilder Screen                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
    ┌────▼───┐   ┌────▼───┐   ┌────▼───┐
    │ 조건생성 │   │ 트리거  │   │ 트리거  │
    │ (Dialog)│   │ 리스트  │   │ 상세정보 │
    └────────┘   └────────┘   └────────┘
         │            │            │
    ┌────▼──────────▼────────────▼────┐
    │          Core Components         │
    │ ● variable_definitions (DB기반)  │
    │ ● parameter_widgets (UI생성)    │
    │ ● condition_storage (DB저장)    │
    │ ● condition_validator (검증)    │
    │ ● condition_builder (로직생성)  │
    │ ● preview_components (미리보기) │
    └─────────────────────────────────┘
```

## 📁 컴포넌트 구조

### 🎯 **Main UI Components**

#### 1. `condition_dialog.py` - 조건 생성 다이얼로그
- **역할**: 새로운 트리거 조건을 생성/편집하는 메인 UI
- **주요 기능**:
  - 변수 선택 (카테고리별 분류)
  - 파라미터 동적 생성 
  - 비교 연산자 설정
  - 목표값/외부변수 설정
  - 실시간 호환성 검증
- **의존성**: `VariableDefinitions`, `ParameterWidgetFactory`, `ConditionValidator`

#### 2. `trigger_list_widget.py` - 트리거 목록 관리
- **역할**: 저장된 트리거들의 목록 표시 및 관리
- **주요 기능**:
  - 트리거 목록 트리뷰 표시
  - 저장/편집/복사/삭제 버튼 기능
  - 트리거 데이터 로드/저장
  - 검색 및 필터링
- **의존성**: `ConditionStorage`

#### 3. `trigger_detail_widget.py` - 트리거 상세 정보
- **역할**: 선택된 트리거의 상세 정보 표시
- **주요 기능**:
  - 트리거 조건 상세 표시
  - 파라미터 값 표시
  - 실행 코드 미리보기
- **의존성**: `PreviewGenerator`

### 🔧 **Core Logic Components**

#### 4. `variable_definitions.py` - DB 기반 변수 시스템 ⭐⭐⭐
- **역할**: 트레이딩 변수들의 정의 및 파라미터 관리 (DB 기반)
- **주요 기능**:
  - DB에서 변수 정의 동적 로딩
  - 카테고리별 변수 분류
  - 파라미터 타입별 정의
  - 차트 카테고리 매핑
  - 호환성 검증 지원
- **DB 테이블**: `tv_trading_variables`, `tv_variable_parameters`
- **캐싱**: O(1) 접근을 위한 클래스 레벨 캐시

#### 5. `condition_storage.py` - 데이터베이스 저장소
- **역할**: 트리거 조건들의 DB 저장/로드 관리
- **주요 기능**:
  - 조건 저장/수정/삭제
  - JSON 직렬화 처리
  - 스키마 검증
  - 전역 DB 매니저 연동
- **DB 테이블**: `trading_conditions` (strategies.sqlite3)

#### 6. `condition_validator.py` - 조건 검증기
- **역할**: 생성된 조건의 유효성 검증
- **주요 기능**:
  - 필수 필드 검증
  - 데이터 타입 검증
  - 비즈니스 로직 검증
  - 에러 메시지 생성

#### 7. `condition_builder.py` - 조건 빌더
- **역할**: UI 데이터를 완전한 조건 객체로 변환
- **주요 기능**:
  - UI → 조건 객체 변환
  - 실행 코드 생성
  - 파라미터 바인딩
  - 메타데이터 생성

#### 8. `parameter_widgets.py` - 파라미터 위젯 팩토리
- **역할**: 변수별 파라미터 입력 UI 동적 생성
- **주요 기능**:
  - 타입별 위젯 생성 (int, float, enum, bool)
  - 실시간 유효성 검증
  - 범위 제한 적용
  - 기본값 설정

#### 9. `preview_components.py` - 미리보기 생성기
- **역할**: 조건의 실행 코드 및 설명 생성
- **주요 기능**:
  - Python 실행 코드 생성
  - 사용자 친화적 설명 생성
  - 미리보기 포맷팅

## 🔄 컴포넌트 간 상호작용

### 📊 데이터 흐름

```
1. 사용자 조건 생성 요청
   ↓
2. ConditionDialog 열림
   ↓
3. VariableDefinitions에서 변수 목록 로드 (DB)
   ↓
4. 사용자가 변수 선택
   ↓
5. ParameterWidgetFactory가 파라미터 UI 생성
   ↓
6. 사용자가 파라미터 입력
   ↓
7. ConditionValidator가 실시간 검증
   ↓
8. ConditionBuilder가 조건 객체 생성
   ↓
9. ConditionStorage가 DB에 저장
   ↓
10. TriggerListWidget이 목록 새로고침
```

### 🔗 의존성 그래프

```
condition_dialog.py
├── variable_definitions.py (변수 정의)
├── parameter_widgets.py (UI 생성)
├── condition_validator.py (검증)
├── condition_builder.py (객체 생성)
├── condition_storage.py (저장)
└── preview_components.py (미리보기)

trigger_list_widget.py
└── condition_storage.py (데이터 로드)

trigger_detail_widget.py
└── preview_components.py (상세 표시)
```

## 💾 데이터베이스 연동

### 사용하는 테이블들

1. **`tv_trading_variables`** (settings.sqlite3)
   - 트레이딩 변수 정의
   - 카테고리, 차트 타입, 비교 그룹 정보

2. **`tv_variable_parameters`** (settings.sqlite3)
   - 변수별 파라미터 정의
   - 타입, 기본값, 범위, 옵션 정보

3. **`trading_conditions`** (strategies.sqlite3)
   - 사용자가 생성한 트리거 조건들
   - JSON 형태로 완전한 조건 정보 저장

## 🛠️ 사용 방법

### 기본 사용 패턴

```python
# 1. 변수 정의 로드
from .variable_definitions import VariableDefinitions
variables = VariableDefinitions.get_category_variables()

# 2. 조건 다이얼로그 사용
from .condition_dialog import ConditionDialog
dialog = ConditionDialog(parent)
if dialog.exec() == QDialog.DialogCode.Accepted:
    condition = dialog.get_condition_data()

# 3. 조건 저장
from .condition_storage import ConditionStorage
storage = ConditionStorage()
storage.save_condition(condition)

# 4. 트리거 리스트 표시
from .trigger_list_widget import TriggerListWidget
list_widget = TriggerListWidget(parent)
list_widget.load_triggers()
```

## 🔧 확장 가능성

### 새로운 변수 추가
1. `tv_trading_variables` 테이블에 변수 정의 추가
2. `tv_variable_parameters` 테이블에 파라미터 정의 추가
3. 자동으로 UI에 반영됨 (DB 기반 동적 로딩)

### 새로운 파라미터 타입 추가
1. `ParameterWidgetFactory`에 새 위젯 타입 추가
2. `ConditionValidator`에 검증 로직 추가

### 새로운 연산자 추가
1. `condition_dialog.py`의 연산자 목록에 추가
2. `condition_builder.py`의 코드 생성 로직에 추가

## 🚨 주의사항

1. **DB 호환성**: 변수 정의 변경 시 기존 조건들과의 호환성 고려
2. **캐시 관리**: `VariableDefinitions.clear_cache()` 필요시 호출
3. **에러 처리**: 모든 컴포넌트에서 적절한 폴백 메커니즘 구현됨
4. **순환 의존성**: 컴포넌트 간 순환 의존성 방지를 위한 설계

## 📈 성능 특징

- **변수 로딩**: O(1) 캐시 기반 접근
- **파라미터 생성**: 동적 UI 생성으로 메모리 효율성
- **DB 접근**: 연결 풀링 및 재사용
- **검증**: 실시간 검증으로 사용자 경험 향상

---

**이 컴포넌트들은 함께 작동하여 사용자가 복잡한 트레이딩 조건을 쉽게 생성하고 관리할 수 있는 강력한 시스템을 제공합니다.**
