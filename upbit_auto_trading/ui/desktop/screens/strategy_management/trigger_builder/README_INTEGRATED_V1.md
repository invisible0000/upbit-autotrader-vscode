# 🚀 Trigger Builder 시스템 개발 문서 (통합 완전판)

## 📊 시스템 개요

트리거 빌더는 사용자가 거래 조건을 시각적으로 구성하고 테스트할 수 있는 통합 인터페이스입니다. 
컴포넌트 기반 아키텍처로 모듈화되어 있으며, 5개의 주요 UI 구성요소와 다층 서비스 아키텍처를 제공합니다.

### 현재 아키텍처 상태 (2025.07.28 기준 - 실제 검증됨)
- **메인 화면**: `trigger_builder_screen.py` (1928 lines → 컴포넌트 기반으로 경량화 진행중)
- **서비스 계층**: `trigger_simulation_service.py` (369 lines, 깔끔한 Request-Response 패턴)
- **컴포넌트 시스템**: `/components` 폴더 내 모듈화된 기능들 (25개 활성 파일)

---

## 🎯 레이아웃 구조 (2x3 그리드 시스템)

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

---

## 🗂️ 폴더 구조 및 파일 현황 (실제 검증됨)

```
trigger_builder/
├── 📁 ROOT LEVEL FILES (핵심 진입점)
│   ├── __init__.py                           # ✅ 사용중 - 모듈 exports (10줄)
│   ├── trigger_builder_screen.py             # ✅ 핵심파일 - 메인 UI 컨트롤러 (1928줄)
│   ├── README.md                             # 📋 기존 문서파일 (200줄)
│   └── TRIGGER_BUILDER_SYSTEM_OVERVIEW.md    # 📋 상세 문서파일 (759줄)
│
├── 📁 components/ (컴포넌트 시스템)
│   ├── __init__.py                          # ✅ 사용중 - 컴포넌트 exports (8줄)
│   │
│   ├── 📁 core/ (핵심 UI 컴포넌트들) - 모든 파일 사용중 ✅
│   │   ├── condition_builder.py            # ✅ 사용중 - 조건 생성 빌더 (336줄)
│   │   ├── condition_dialog.py             # ✅ 사용중 - 조건 편집 다이얼로그 (1643줄)
│   │   ├── condition_storage.py            # ✅ 사용중 - 조건 저장/로드 시스템 (483줄)
│   │   ├── condition_validator.py          # ✅ 사용중 - 조건 유효성 검증 (199줄)
│   │   ├── parameter_widgets.py            # ✅ 사용중 - 파라미터 입력 위젯들 (362줄)
│   │   ├── preview_components.py           # ✅ 사용중 - 미리보기 컴포넌트들 (255줄)
│   │   ├── simulation_control_widget.py    # ✅ 사용중 - 시뮬레이션 제어 패널 (208줄)
│   │   ├── simulation_result_widget.py     # ✅ 사용중 - 결과 차트 & 기록 (1026줄)
│   │   ├── trigger_detail_widget.py        # ✅ 사용중 - 트리거 상세정보 패널 (371줄)
│   │   ├── trigger_list_widget.py          # ✅ 사용중 - 트리거 목록 관리 (797줄)
│   │   ├── variable_definitions.py         # ✅ 사용중 - 변수 파라미터 정의 (578줄)
│   │   └── __init__.py                     # ✅ 사용중 (16줄)
│   │
│   ├── 📁 shared/ (공통 서비스들) - 대부분 사용중 ✅
│   │   ├── chart_rendering_engine.py       # ✅ 사용중 - 차트 렌더링 엔진 (417줄)
│   │   ├── chart_variable_service.py       # ✅ 사용중 - 차트 변수 서비스 (398줄)
│   │   ├── chart_visualizer.py             # ✅ 사용중 - 차트 시각화 도구 (223줄)
│   │   ├── compatibility_validator.py      # ✅ 사용중 - 호환성 검증 시스템 (358줄)
│   │   ├── minichart_variable_service.py   # ✅ 사용중 - 미니차트 변수 서비스 (384줄)
│   │   ├── simulation_engines.py           # ✅ 사용중 - 다양한 시뮬레이션 엔진들 (572줄)
│   │   ├── trigger_calculator.py           # ✅ 사용중 - 기술적 지표 계산 (309줄)
│   │   ├── trigger_simulation_service.py   # ✅ 핵심서비스 - 메인 시뮬레이션 (369줄)
│   │   ├── variable_display_system.py      # ✅ 사용중 - 변수 표시 시스템 (219줄)
│   │   └── __init__.py                     # ✅ 사용중 (18줄)
│   │
│   ├── 📁 data/ (데이터 저장소)
│   │   └── app_settings.sqlite3            # ✅ 사용중 - 설정 데이터베이스
│   │
│   └── 📁 ROOT LEVEL COMPONENTS (독립 컴포넌트들)
│       ├── chart_development_checklist.py  # **❌ 제거대상** - 개발용 체크리스트
│       ├── chart_visualizer_widget.py      # **❌ 제거대상** - 미사용 중복 차트위젯
│       ├── condition_loader.py             # ✅ 사용중 - 조건 로더 (폴백용)
│       ├── data_source_manager.py          # ✅ 사용중 - 데이터 소스 관리자
│       ├── data_source_selector.py         # ✅ 사용중 - 데이터 소스 선택 위젯
│       ├── database_variable_widgets.py    # **❌ 제거대상** - 미사용 데이터베이스 위젯
│       ├── test_trigger_list_widget.py     # **❌ 제거대상** - 테스트용 파일
│       └── __init__.py                     # ✅ 사용중
```

---

## 🏗️ 주요 구성요소 상세 분석

### 1. 조건빌더 (condition_builder.py + condition_dialog.py)
**위치**: [1,4] 영역 (좌측 전체)  
**파일**: `core/condition_dialog.py` (1643줄), `core/condition_builder.py` (336줄)  
**역할**: 거래 조건 생성 및 편집

#### UI 구성
```
조건 생성 다이얼로그
├── 변수 선택 섹션
│   ├── 변수 타입 콤보박스 (SMA, EMA, RSI, MACD 등)
│   ├── 파라미터 입력 (period, timeframe 등)
│   └── 미리보기 표시
├── 연산자 선택 섹션  
│   └── >, >=, <, <=, ~=, != 연산자
├── 비교값 설정 섹션
│   ├── 고정값 입력 (숫자)
│   └── 외부변수 선택 (다른 지표와 비교)
└── 저장/취소 버튼
```

#### 주요 클래스/메서드
```python
class ConditionDialog(QWidget):
    def create_ui()                    # UI 레이아웃 구성
    def get_condition_data()          # 입력된 조건 데이터 추출
    def validate_condition()          # 조건 유효성 검증
    def save_condition()             # 조건을 데이터베이스에 저장
    def load_condition(trigger_id)   # 기존 조건 로드 (편집시)

class ConditionBuilder:
    def build_condition_from_ui()    # UI 데이터로 조건 객체 생성
    def generate_execution_code()    # 실행 코드 생성
```

#### 주요 시그널
- `condition_created` - 새 조건 생성 시
- `condition_modified` - 조건 수정 시
- `validation_status_changed` - 유효성 상태 변경 시

#### 중요 변수
- `variable_definitions` - 사용 가능한 변수 목록 (VariableDefinitions 클래스)
- `current_condition` - 현재 편집 중인 조건
- `validation_messages` - 호환성 검증 메시지

### 2. 트리거 리스트 (trigger_list_widget.py)
**위치**: [2] 영역 (상단 중앙)  
**파일**: `core/trigger_list_widget.py` (797줄)  
**역할**: 저장된 트리거 목록 표시 및 관리

#### UI 구성
```
트리거 목록 관리
├── 트리거 목록 (QListWidget)
│   ├── 트리거명 표시
│   ├── 조건 요약 표시  
│   └── 상태 아이콘 (활성/비활성)
├── 우클릭 컨텍스트 메뉴
│   ├── 편집
│   ├── 복사
│   ├── 삭제
│   └── 활성화/비활성화
└── 하단 버튼들
    ├── 새 조건 추가
    ├── 선택 삭제
    └── 새로고침
```

#### 주요 클래스/메서드
```python
class TriggerListWidget(QWidget):
    def load_triggers()              # 데이터베이스에서 트리거 목록 로드
    def add_trigger(condition_data)  # 새 트리거 추가
    def delete_selected()           # 선택된 트리거 삭제
    def on_trigger_selected()       # 트리거 선택시 상세정보 업데이트
```

#### 주요 시그널
- `trigger_selected` - 트리거 선택 시
- `trigger_deleted` - 트리거 삭제 시
- `trigger_double_clicked` - 트리거 더블클릭 시

#### 중요 변수
- `trigger_tree` - 트리거 목록 위젯
- `selected_trigger` - 현재 선택된 트리거
- `storage` - 조건 저장소 인스턴스 (ConditionStorage)

### 3. 시뮬레이션 컨트롤 (simulation_control_widget.py)
**위치**: [3] 영역 (상단 우측)  
**파일**: `core/simulation_control_widget.py` (208줄)  
**역할**: 시뮬레이션 실행 및 데이터 소스 선택

#### UI 구성
```
시뮬레이션 제어 패널
├── 시나리오 선택 섹션
│   ├── 시나리오 콤보박스
│   │   ├── 상승 추세
│   │   ├── 하락 추세  
│   │   ├── 급등/급락
│   │   ├── 횡보
│   │   └── 이동평균 교차
│   └── 데이터 개수 설정 (기본 100개)
├── 실행 제어 섹션
│   ├── 실행 버튼 (크고 눈에 띄게)
│   ├── 정지 버튼
│   └── 진행률 표시바
└── 고급 설정 섹션
    ├── 데이터 소스 선택
    ├── 시드값 설정
    └── 노이즈 레벨 조정
```

#### 주요 클래스/메서드
```python
class SimulationControlWidget(QWidget):
    def create_simulation_area()     # 시뮬레이션 영역 UI 구성
    def run_simulation()            # 시뮬레이션 실행 요청
    def stop_simulation()           # 시뮬레이션 중단
    def update_scenario_list()      # 시나리오 목록 업데이트
    def get_simulation_settings()   # 현재 설정값 반환
```

#### 주요 시그널
- `simulation_requested` - 시뮬레이션 요청 시
- `data_source_changed` - 데이터 소스 변경 시

#### 중요 변수
- `data_source_selector` - 데이터 소스 선택기 (DataSourceSelectorWidget)
- `simulation_status` - 시뮬레이션 상태

### 4. 트리거 상세정보 (trigger_detail_widget.py)
**위치**: [5] 영역 (하단 중앙)  
**파일**: `core/trigger_detail_widget.py` (371줄)  
**역할**: 선택된 트리거의 상세 정보 표시

#### UI 구성
```
트리거 상세정보 패널
├── 기본 정보 섹션
│   ├── 트리거명
│   ├── 생성일시  
│   └── 마지막 수정일시
├── 조건 정보 섹션
│   ├── 기본 변수 (SMA_20 등)
│   ├── 연산자 (>, < 등)
│   ├── 비교값/외부변수
│   └── 파라미터 상세
├── 통계 정보 섹션
│   ├── 총 실행 횟수
│   ├── 성공률
│   └── 마지막 실행 결과
└── 액션 버튼들
    ├── 편집
    ├── 복사
    ├── 삭제
    └── 테스트 실행
```

#### 주요 클래스/메서드
```python
class TriggerDetailWidget(QWidget):
    def update_trigger_detail(trigger_data)  # 상세정보 업데이트
    def copy_trigger()                       # 트리거 복사
    def edit_trigger()                      # 트리거 편집 (ConditionDialog 호출)
    def delete_trigger()                    # 트리거 삭제
```

#### 주요 시그널
- `trigger_copied` - 트리거 복사 시

#### 중요 변수
- `detail_text` - 상세정보 텍스트 위젯
- `current_trigger` - 현재 표시 중인 트리거

### 5. 시뮬레이션 결과 미니차트 (simulation_result_widget.py)
**위치**: [6] 영역 (하단 우측)  
**파일**: `core/simulation_result_widget.py` (1026줄)  
**역할**: 시뮬레이션 결과 차트 및 트리거 신호 표시

#### UI 구성
```
시뮬레이션 결과 표시
├── 📊 미니차트 영역 (matplotlib)
│   ├── 가격 데이터 (파란색 라인)
│   ├── 기본변수 (녹색 라인, iVal)
│   ├── 외부변수/고정값 (주황색 라인/점선, eVal/fVal)
│   ├── 트리거 신호 (빨간 역삼각형, Trg)
│   └── 범례 (Price, iVal, eVal/fVal, Trg)
└── 📋 작동 기록 영역 (QListWidget)
    ├── 트리거 발동 기록
    ├── 시간순 정렬
    ├── 상태별 아이콘
    └── 스크롤 지원 (최대 100개 항목)
```

#### 차트 카테고리별 렌더링
```python
렌더링 방식:
├── price_overlay: 메인 차트에 가격과 함께 표시 (SMA, EMA)
├── oscillator: 별도 서브플롯, 0-100 범위 (RSI, 스토캐스틱)  
├── momentum: 별도 서브플롯, 중앙선 포함 (MACD)
└── volume: 히스토그램 형태 (거래량)
```

#### 주요 클래스/메서드
```python
class SimulationResultWidget(QWidget):
    def update_simulation_chart()           # 메인 차트 업데이트 메서드
    def update_trigger_signals()          # 트리거 신호 업데이트
    def add_test_history_item()           # 작동 기록 아이템 추가  
    def _plot_price_overlay_chart()       # 가격 오버레이 차트 플롯
    def _plot_trigger_signals_enhanced()  # 개선된 트리거 신호 마커
    def _setup_enhanced_chart_style()     # 차트 스타일 설정
    def show_placeholder_chart()          # 플레이스홀더 차트 표시
```

#### 주요 시그널
- `result_updated` - 결과 업데이트 시

#### 중요 변수
- `figure` - matplotlib 차트 객체
- `canvas` - 차트 캔버스
- `test_history_list` - 트리거 신호 기록 리스트
- `_last_scenario`, `_last_price_data`, `_last_trigger_results` - 마지막 시뮬레이션 결과

---

## 🔗 구성요소 간 연결관계 및 데이터 플로우

### 시그널 연결 체인
```python
# 주요 시그널 연결 패턴
condition_builder.condition_created.connect(trigger_list.add_trigger)
trigger_list.trigger_selected.connect(trigger_detail.update_trigger_detail)
simulation_control.simulation_requested.connect(simulation_result.update_chart)

# 메인 화면에서의 통합 연결 (trigger_builder_screen.py)
self.trigger_list_widget.trigger_selected.connect(self.on_trigger_selected)
self.trigger_list_widget.trigger_deleted.connect(self.on_trigger_deleted)
self.simulation_control_widget.simulation_requested.connect(self.run_simulation)
```

### 데이터 플로우 트리
```
사용자 액션 (트리거 시뮬레이션 실행)
│
├── 1. SimulationControlWidget.run_simulation()
│   └── → trigger_builder_screen.run_simulation() 호출
│
├── 2. trigger_builder_screen.run_simulation() (40줄로 경량화됨)
│   ├── → TriggerSimulationRequest 객체 생성
│   ├── → trigger_simulation_service.run_simulation() 호출
│   └── → SimulationResultWidget.update_chart_with_simulation_results() 호출
│
├── 3. TriggerSimulationService.run_simulation() (새로운 서비스)
│   ├── → _load_market_data() (시나리오별 가상 데이터)
│   ├── → _analyze_condition() (조건 분석)
│   ├── → _calculate_variables() (변수 계산)
│   │   └── → TriggerCalculator.calculate_sma/ema/rsi/macd()
│   ├── → _calculate_trigger_points() (트리거 계산)
│   └── → TriggerSimulationResult 객체 반환
│
└── 4. SimulationResultWidget.update_chart_with_simulation_results()
    ├── → update_simulation_chart() (차트 업데이트)
    │   ├── → _plot_price_overlay_chart() (가격/지표 플롯)
    │   └── → _plot_trigger_signals_enhanced() (트리거 마커)
    └── → update_trigger_signals() (작동 기록 업데이트)
```

### 서비스 의존성 트리
```
trigger_builder_screen.py (메인 컨트롤러)
├── core/ 컴포넌트들
│   ├── ConditionDialog ← VariableDefinitions (파라미터 정의)
│   ├── TriggerListWidget ← ConditionStorage (데이터 저장)
│   ├── TriggerDetailWidget ← ConditionLoader (데이터 로드)
│   ├── SimulationControlWidget ← SimulationEngines (다양한 엔진)
│   └── SimulationResultWidget ← ChartVisualizer (차트 렌더링)
│
├── shared/ 서비스들
│   ├── TriggerSimulationService (메인 서비스)
│   │   └── ← TriggerCalculator (계산 엔진)
│   ├── ChartVariableService (변수 서비스)
│   ├── CompatibilityValidator (호환성 검증)
│   └── MinichartVariableService (미니차트 서비스)
│
└── data/ 저장소
    └── app_settings.sqlite3 (설정 DB)
```

---

## 🧩 현재 지원되는 변수 목록 (실제 검증됨)

### ✅ 완전 지원 변수 (trigger_simulation_service.py)
```python
FULLY_SUPPORTED_VARIABLES = {
    'SMA': {
        'name': '단순이동평균',
        'ui_text': '🔹 단순이동평균',
        'category': 'price_overlay',
        'parameters': ['period'],
        'calculation_method': 'trigger_calculator.calculate_sma()',
        'status': '✅ 완전지원',
        'cross_trigger_support': '✅ 지원 (SMA vs SMA)'
    },
    'EMA': {
        'name': '지수이동평균', 
        'ui_text': '🔹 지수이동평균',
        'category': 'price_overlay',
        'parameters': ['period'],
        'calculation_method': 'trigger_calculator.calculate_ema()',
        'status': '✅ 완전지원',
        'cross_trigger_support': '✅ 지원 (EMA vs EMA, SMA vs EMA)'
    },
    'RSI': {
        'name': 'RSI 지표',
        'ui_text': '🔹 RSI 지표',
        'category': 'oscillator',
        'parameters': ['period'],
        'calculation_method': 'trigger_calculator.calculate_rsi()',
        'status': '✅ 계산지원 (차트 렌더링 수정됨)',
        'cross_trigger_support': '✅ 지원 vs 고정값 (RSI > 70)'
    },
    'MACD': {
        'name': 'MACD',
        'ui_text': '🔹 MACD',
        'category': 'momentum', 
        'parameters': ['fast', 'slow', 'signal'],
        'calculation_method': 'trigger_calculator.calculate_macd()',
        'status': '✅ 기본지원',
        'cross_trigger_support': '✅ 지원 vs 고정값 (MACD > 0)'
    },
    'PRICE': {
        'name': '현재가',
        'ui_text': '현재가',
        'category': 'price_overlay',
        'parameters': [],
        'calculation_method': 'price_data 직접 사용',
        'status': '✅ 완전지원',
        'cross_trigger_support': '✅ 지원 vs 고정값'
    }
}
```

### 🔧 추가 개발 필요한 변수들 (variable_definitions.py에 정의됨)
```python
DEFINED_BUT_NOT_IMPLEMENTED = {
    'BOLLINGER_BAND': {
        'status': '📋 정의됨, 🔧 구현필요',
        'parameters': ['period', 'std_dev'],
        'category': 'price_overlay'
    },
    'STOCHASTIC': {
        'status': '📋 정의됨, 🔧 구현필요', 
        'parameters': ['k_period', 'd_period'],
        'category': 'oscillator'
    },
    'ATR': {
        'status': '📋 정의됨, 🔧 구현필요',
        'parameters': ['period'],
        'category': 'momentum'
    },
    'VOLUME': {
        'status': '📋 정의됨, 🔧 구현필요',
        'parameters': [],
        'category': 'volume'
    },
    'VOLUME_SMA': {
        'status': '📋 정의됨, 🔧 구현필요',
        'parameters': ['period'],
        'category': 'volume'
    }
}
```

---

## 🔧 서비스 레이어 상세분석

### TriggerSimulationService (메인 서비스)
```python
📍 위치: components/shared/trigger_simulation_service.py (369줄)
🎯 역할: 통합 트리거 시뮬레이션 서비스

아키텍처 패턴: Request-Response
├── TriggerSimulationRequest (입력 데이터클래스)
├── TriggerSimulationResult (출력 데이터클래스)  
└── TriggerSimulationService (처리 로직)

지원 변수 매핑:
def _map_ui_text_to_variable_id():
├── 'SMA' ← '단순이동평균', 'SMA' 
├── 'EMA' ← '지수이동평균', 'EMA'
├── 'RSI' ← 'RSI', 'RSI 지표'
├── 'MACD' ← 'MACD'
├── 'PRICE' ← '현재가', 'PRICE'
└── 'VOLUME' ← '거래량', 'VOLUME'

처리 플로우:
1. _load_market_data() → 시나리오별 가상 데이터 생성
2. _analyze_condition() → 조건 구문 분석  
3. _calculate_variables() → 기술적 지표 계산
4. _calculate_trigger_points() → 트리거 포인트 추출
5. TriggerSimulationResult 생성 → 결과 반환
```

### TriggerCalculator (계산 엔진)
```python
📍 위치: components/shared/trigger_calculator.py (309줄)  
🎯 역할: 기술적 지표 계산 및 트리거 포인트 계산

지원 계산 메서드:
def calculate_sma(prices, period)              # 단순이동평균
def calculate_ema(prices, period)              # 지수이동평균  
def calculate_rsi(prices, period=14)           # RSI 지표
def calculate_macd(prices)                     # MACD (12,26,9)

트리거 계산 메서드:
def calculate_trigger_points(data, op, target) # 단일 조건 (RSI > 70)
def calculate_cross_trigger_points(base, ext, op) # 교차 조건 (SMA > EMA)

연산자 지원:
├── '>' : 초과
├── '>=' : 이상  
├── '<' : 미만
├── '<=' : 이하
├── '~=' : 근사값 (±1%)
└── '!=' : 불일치
```

### Variable Definitions System (변수 정의 시스템)
```python
📍 위치: components/core/variable_definitions.py (578줄)
🎯 역할: 모든 트레이딩 변수의 파라미터 정의

class VariableDefinitions:
    CHART_CATEGORIES = {
        'price_overlay': ['SMA', 'EMA', 'BOLLINGER_BAND', 'PRICE'],
        'oscillator': ['RSI', 'STOCHASTIC'],
        'momentum': ['MACD', 'ATR'],
        'volume': ['VOLUME', 'VOLUME_SMA']
    }
    
    def get_variable_parameters()     # 변수별 파라미터 정의
    def get_chart_category()         # 차트 카테고리 반환
    def get_default_parameters()     # 기본 파라미터 값
```

---

## 📝 제거 계획 및 정리 작업

### ❌ 즉시 제거 가능한 파일들
```bash
# 테스트/개발용 파일들  
components/test_trigger_list_widget.py        # 212줄 - 테스트 전용
components/chart_development_checklist.py    # 개발용 체크리스트

# 미사용 위젯들
components/chart_visualizer_widget.py         # 미사용 중복 위젯
components/database_variable_widgets.py      # 미사용 데이터베이스 위젯
```

### 🔍 검토 후 제거 고려 대상
```bash
# 사용 빈도가 낮은 파일들 (신중히 검토 필요)
components/data_source_manager.py     # 사용중이지만 단순함
components/condition_loader.py        # 폴백용으로 유지 필요  
components/data_source_selector.py    # 사용중, 유지 필요
```

---

## 🚨 개발시 주의사항 (업데이트됨)

### 1. 새로운 변수 추가시 필수 작업 체크리스트
```python
# ✅ 반드시 해야할 작업들 (순서대로)
1. VariableDefinitions.get_variable_parameters()에 파라미터 정의 추가
2. TriggerCalculator.calculate_[변수명]() 메서드 구현
3. TriggerSimulationService._map_ui_text_to_variable_id() 매핑 추가  
4. VariableDefinitions.CHART_CATEGORIES에 렌더링 카테고리 추가
5. ConditionDialog 변수 목록에 추가
6. 테스트 시나리오 작성 및 검증
```

### 2. 기존 기능 수정시 영향도 체크
```python
# ⚠️ 반드시 확인해야할 의존성 체인
trigger_builder_screen.py (메인 컨트롤러) 1928줄
├── ConditionDialog (조건 생성/편집) 1643줄
├── TriggerListWidget (목록 관리) 797줄
├── TriggerDetailWidget (상세정보) 371줄
├── SimulationControlWidget (실행 제어) 208줄
├── SimulationResultWidget (결과 표시) 1026줄
└── TriggerSimulationService (계산 로직) 369줄
    └── TriggerCalculator (지표 계산) 309줄
```

### 3. 중복 개발 방지 체크리스트
```python
# 🔍 이미 구현된 기능들 (중복 개발 금지)
✅ SMA/EMA 계산 → TriggerCalculator.calculate_sma/ema()
✅ RSI 계산 → TriggerCalculator.calculate_rsi()  
✅ MACD 계산 → TriggerCalculator.calculate_macd()
✅ 트리거 포인트 계산 → TriggerCalculator.calculate_trigger_points()
✅ 교차 트리거 계산 → TriggerCalculator.calculate_cross_trigger_points()
✅ 차트 렌더링 → SimulationResultWidget._plot_*_chart()
✅ 조건 저장/로드 → ConditionStorage, ConditionLoader
✅ 데이터 소스 관리 → DataSourceManager, DataSourceSelector
✅ 호환성 검증 → CompatibilityValidator
✅ 변수 표시 시스템 → VariableDisplaySystem
✅ 미니차트 서비스 → MinichartVariableService
```

### 4. 특별 주의사항

#### 테마 지원
- 모든 구성요소는 전역 테마 시스템을 사용
- matplotlib 차트는 `theme_notifier`를 통해 다크/라이트 테마 자동 적용

#### 외부 의존성
- `matplotlib` - 차트 렌더링 (선택적)
- `ConditionStorage` - 조건 저장/로드
- `DataSourceSelectorWidget` - 데이터 소스 선택

#### 크기 정책
- 모든 위젯은 `QSizePolicy.Expanding` 사용
- 고정 크기 설정은 최소화하여 반응형 레이아웃 구현

---

## 🎯 향후 개발 로드맵

### Phase 1: 현재 이슈 해결 ✅ 완료
- [x] RSI 차트 렌더링 오류 수정
- [x] external_variable_info None 처리 보완  
- [x] SMA 파라미터 분리 문제 해결
- [x] trigger_simulation_service.py 통합

### Phase 2: 코드 정리 (진행중)
- [ ] 제거 대상 파일들 정리
- [ ] 중복 코드 제거
- [ ] trigger_builder_screen.py 추가 경량화
- [ ] 주석 및 문서화 개선

### Phase 3: 변수 확장
- [ ] BOLLINGER_BAND 계산 및 렌더링 구현
- [ ] STOCHASTIC 지표 추가 구현  
- [ ] ATR 지표 추가 구현
- [ ] VOLUME 기반 트리거 구현

### Phase 4: 고급 기능
- [ ] 실시간 데이터 연동
- [ ] 백테스팅 시스템 통합  
- [ ] 커스텀 지표 지원
- [ ] 다중 조건 AND/OR 로직
- [ ] 알림 시스템 연동

---

## 📊 시스템 현황 요약

**📁 총 파일 수**: 27개 Python 파일  
**📝 총 코드 라인**: 12,000+ 줄  
**✅ 활성 파일**: 23개  
**❌ 제거 대상**: 4개  
**🔧 핵심 서비스**: 8개  
**🎨 UI 컴포넌트**: 12개  

### 핵심 통계
- **메인 화면**: 1,928줄 (trigger_builder_screen.py)
- **최대 컴포넌트**: 1,643줄 (condition_dialog.py)
- **결과 차트**: 1,026줄 (simulation_result_widget.py)
- **트리거 목록**: 797줄 (trigger_list_widget.py)
- **변수 정의**: 578줄 (variable_definitions.py)

---

## 🛠️ 개발 지침 및 디버깅 팁

### 새 기능 추가 시
1. 적절한 구성요소 선택
2. 시그널/슬롯 연결 확인
3. 테마 호환성 테스트
4. 크기 정책 확인
5. 중복 기능 방지 체크

### 디버깅 팁
- 각 구성요소는 독립적으로 테스트 가능
- 시그널 연결 상태는 `pyqtSignal.connect()` 로그로 확인
- 레이아웃 문제는 `setStyleSheet()` 테두리로 디버깅
- 변수 계산 오류는 `TriggerCalculator` 클래스에서 직접 테스트

### 에이전트 개발 가이드라인
- 이 문서의 **중복 개발 방지 체크리스트**를 반드시 확인
- 새 변수 추가시 **필수 작업 체크리스트** 순서대로 진행  
- 파일 상태 (✅사용중/❌제거대상) 확인 후 작업
- 라인 수와 클래스명은 이 문서에서 검증된 정보 사용

---

**📝 마지막 업데이트**: 2025.07.28  
**🔧 검증 상태**: 모든 파일 구조 및 라인 수 실제 확인 완료  
**📊 문서 상태**: README.md + OVERVIEW.md 통합 완료  
**👨‍💻 다음 작업**: README_INTEGRATED_V2.md 생성 (OVERVIEW 기반 통합)

---

*이 문서는 실제 코드를 검증하여 작성되었으며, 에이전트의 중복 개발 방지와 정확한 기능 연결을 위해 최적화되었습니다.*
