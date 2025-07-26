# 트리거 빌더 (Trigger Builder) 구성요소 가이드

## 개요
트리거 빌더는 사용자가 거래 조건을 시각적으로 구성하고 테스트할 수 있는 통합 인터페이스입니다. 
리팩토링을 통해 5개의 주요 구성요소로 모듈화되었습니다.

## 레이아웃 구조 (2x3 그리드)
```
┌─────────────────┬─────────────────┬─────────────────┐
│ [1] 조건빌더    │ [2] 트리거리스트 │ [3] 시뮬레이션  │
│ (condition_     │ (trigger_list_  │ 컨트롤          │
│  builder)       │  widget)        │ (simulation_    │
│                 │                 │  control)       │
├─────────────────┼─────────────────┼─────────────────┤
│ [4] 조건빌더    │ [5] 트리거상세  │ [6] 시뮬레이션  │
│ (확장영역)      │ 정보            │ 결과미니차트    │
│                 │ (trigger_detail)│ (simulation_    │
│                 │                 │  result)        │
└─────────────────┴─────────────────┴─────────────────┘
```

## 주요 구성요소

### 1. 조건빌더 (condition_builder.py)
**위치**: [1,4] 영역 (좌측 전체)
**역할**: 거래 조건 생성 및 편집

#### 주요 클래스/메서드
- `ConditionBuilder.build_condition_from_ui()` - UI 데이터로 조건 객체 생성
- `ConditionBuilder.generate_execution_code()` - 실행 코드 생성
- `VariableDefinitions` - 변수 정의 관리
- `ConditionValidator` - 조건 유효성 검증

#### 주요 시그널
- `condition_created` - 새 조건 생성 시
- `condition_modified` - 조건 수정 시
- `validation_status_changed` - 유효성 상태 변경 시

#### 중요 변수
- `variable_definitions` - 사용 가능한 변수 목록
- `current_condition` - 현재 편집 중인 조건
- `validation_messages` - 호환성 검증 메시지

### 2. 트리거 리스트 (trigger_list_widget.py)
**위치**: [2] 영역 (상단 중앙)
**역할**: 저장된 트리거 목록 표시 및 관리

#### 주요 클래스/메서드
- `TriggerListWidget.load_triggers()` - 트리거 목록 로드
- `TriggerListWidget.add_trigger()` - 새 트리거 추가
- `TriggerListWidget.delete_selected()` - 선택된 트리거 삭제
- `ConditionStorage` - 조건 저장/로드 관리

#### 주요 시그널
- `trigger_selected` - 트리거 선택 시
- `trigger_deleted` - 트리거 삭제 시
- `trigger_double_clicked` - 트리거 더블클릭 시

#### 중요 변수
- `trigger_tree` - 트리거 목록 위젯
- `selected_trigger` - 현재 선택된 트리거
- `storage` - 조건 저장소 인스턴스

### 3. 시뮬레이션 컨트롤 (simulation_control_widget.py)
**위치**: [3] 영역 (상단 우측)
**역할**: 시뮬레이션 실행 및 데이터 소스 선택

#### 주요 클래스/메서드
- `SimulationControlWidget.create_simulation_area()` - 시뮬레이션 영역 생성
- `DataSourceSelectorWidget` - 데이터 소스 선택 위젯

#### 주요 시그널
- `simulation_requested` - 시뮬레이션 요청 시
- `data_source_changed` - 데이터 소스 변경 시

#### 중요 변수
- `data_source_selector` - 데이터 소스 선택기
- `simulation_status` - 시뮬레이션 상태

### 4. 트리거 상세정보 (trigger_detail_widget.py)
**위치**: [5] 영역 (하단 중앙)
**역할**: 선택된 트리거의 상세 정보 표시

#### 주요 클래스/메서드
- `TriggerDetailWidget.update_trigger_detail()` - 트리거 상세정보 업데이트
- `TriggerDetailWidget.copy_trigger()` - 트리거 복사

#### 주요 시그널
- `trigger_copied` - 트리거 복사 시

#### 중요 변수
- `detail_text` - 상세정보 텍스트 위젯
- `current_trigger` - 현재 표시 중인 트리거

### 5. 시뮬레이션 결과 미니차트 (simulation_result_widget.py)
**위치**: [6] 영역 (하단 우측)
**역할**: 시뮬레이션 결과 차트 및 트리거 신호 표시

#### 주요 클래스/메서드
- `SimulationResultWidget.update_simulation_chart()` - 차트 업데이트
- `SimulationResultWidget.update_trigger_signals()` - 트리거 신호 업데이트
- `SimulationResultWidget.add_test_history_item()` - 작동 기록 추가

#### 주요 시그널
- `result_updated` - 결과 업데이트 시

#### 중요 변수
- `figure` - matplotlib 차트 객체
- `canvas` - 차트 캔버스
- `test_history_list` - 트리거 신호 기록 리스트
- `_last_scenario`, `_last_price_data`, `_last_trigger_results` - 마지막 시뮬레이션 결과

## 구성요소 간 연결관계

### 데이터 플로우
1. **조건 생성**: 조건빌더 → 트리거 리스트
2. **트리거 선택**: 트리거 리스트 → 트리거 상세정보
3. **시뮬레이션 실행**: 시뮬레이션 컨트롤 → 시뮬레이션 결과
4. **결과 표시**: 시뮬레이션 결과 → 미니차트 & 트리거 신호

### 시그널 연결
```python
# 주요 시그널 연결 패턴
condition_builder.condition_created.connect(trigger_list.add_trigger)
trigger_list.trigger_selected.connect(trigger_detail.update_trigger_detail)
simulation_control.simulation_requested.connect(simulation_result.update_chart)
```

## 특별 주의사항

### 테마 지원
- 모든 구성요소는 전역 테마 시스템을 사용
- matplotlib 차트는 `theme_notifier`를 통해 다크/라이트 테마 자동 적용

### 외부 의존성
- `matplotlib` - 차트 렌더링 (선택적)
- `ConditionStorage` - 조건 저장/로드
- `DataSourceSelectorWidget` - 데이터 소스 선택

### 크기 정책
- 모든 위젯은 `QSizePolicy.Expanding` 사용
- 고정 크기 설정은 최소화하여 반응형 레이아웃 구현

## 개발 지침

### 새 기능 추가 시
1. 적절한 구성요소 선택
2. 시그널/슬롯 연결 확인
3. 테마 호환성 테스트
4. 크기 정책 확인

### 디버깅 팁
- 각 구성요소는 독립적으로 테스트 가능
- 시그널 연결 상태는 `pyqtSignal.connect()` 로그로 확인
- 레이아웃 문제는 `setStyleSheet()` 테두리로 디버깅

---
*마지막 업데이트: 2025년 7월 26일*
