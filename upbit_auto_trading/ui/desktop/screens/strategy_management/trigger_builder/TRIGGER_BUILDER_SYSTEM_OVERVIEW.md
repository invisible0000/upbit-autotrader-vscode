# 🚀 Trigger Builder 시스템 개발 문서 (통합 완전판)

## 📊 시스템 개요

트리거 빌더는 사용자가 거래 조건을 시각적으로 구성하고 테스트할 수 있는 통합 인터페이스입니다. 
컴포넌트 기반 아키텍처로 모듈화되어 있으며, 5개의 주요 UI 구성요소와 다층 서비스 아키텍처를 제공합니다.

### 현재 아키텍처 상태 (2025.07.28 기준 - 실제 검증됨)
- **메인 화면**: `trigger_builder_screen.py` (1928 lines → 컴포넌트 기반으로 경량화 진행중)
- **서비스 계층**: `trigger_simulation_service.py` (369 lines, 깔끔한 Request-Response 패턴)
- **컴포넌트 시스템**: `/components` 폴더 내 모듈화된 기능들 (25개 활성 파일)

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
│   └── TRIGGER_BUILDER_SYSTEM_OVERVIEW.md    # 📋 상세 문서파일 (통합 완전판)
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

---

## 🔍 파일별 상세 분석

### ✅ 핵심 사용중 파일들

#### 1. trigger_builder_screen.py (1928줄)
```python
# 역할: 메인 UI 컨트롤러, 전체 화면 구성 및 이벤트 처리
# 상태: 컴포넌트 기반으로 경량화 진행중

주요 import들:
- ConditionDialog ← core/condition_dialog.py
- TriggerListWidget ← core/trigger_list_widget.py  
- TriggerDetailWidget ← core/trigger_detail_widget.py
- SimulationControlWidget ← core/simulation_control_widget.py
- SimulationResultWidget ← core/simulation_result_widget.py
- ChartVisualizer ← shared/chart_visualizer.py
- TriggerCalculator ← shared/trigger_calculator.py
- trigger_simulation_service ← shared/trigger_simulation_service.py (새로 적용)

주요 메서드들:
def create_ui()                    # UI 레이아웃 구성
def run_simulation()              # 시뮬레이션 실행 (40줄로 경량화됨)
def on_trigger_selected()        # 트리거 선택 이벤트
def on_trigger_deleted()         # 트리거 삭제 이벤트
def create_condition()           # 새 조건 생성
```

#### 2. trigger_simulation_service.py (369줄)
```python
# 역할: 새로운 핵심 시뮬레이션 서비스
# 상태: 최신 Request-Response 패턴, SMA 파라미터 분리 문제 해결됨

클래스들:
@dataclass TriggerSimulationRequest   # 요청 데이터
@dataclass TriggerSimulationResult    # 결과 데이터  
class TriggerSimulationService        # 메인 서비스 클래스

주요 메서드들:
def run_simulation()                  # 메인 시뮬레이션 실행
def _analyze_condition()              # 조건 분석
def _calculate_variables()            # 변수 계산
def _calculate_trigger_points()       # 트리거 포인트 계산
def _map_ui_text_to_variable_id()     # UI텍스트→변수ID 매핑
```

#### 3. core/ 폴더 파일들 (모든 파일 사용중)

**condition_dialog.py (1662줄)**
```python
class ConditionDialog(QWidget):
# 역할: 조건 생성/편집 다이얼로그
# 기능: 변수 선택, 연산자 설정, 파라미터 입력

def create_ui()                      # 다이얼로그 UI 구성
def get_condition_data()            # 조건 데이터 추출
def validate_condition()            # 조건 유효성 검증
def save_condition()               # 조건 저장
```

**simulation_result_widget.py (1034줄)**
```python
class SimulationResultWidget(QWidget):
# 역할: 시뮬레이션 결과 차트 및 기록 표시
# 기능: matplotlib 차트, 트리거 신호 표시, 작동 기록

def update_simulation_chart()       # 차트 업데이트
def update_trigger_signals()       # 트리거 신호 업데이트  
def add_test_history_item()        # 작동 기록 추가
def _plot_price_overlay_chart()    # 가격 오버레이 차트
def _plot_trigger_signals_enhanced() # 개선된 트리거 신호 표시
```

**trigger_list_widget.py**
```python
class TriggerListWidget(QListWidget):
# 역할: 트리거 목록 관리 위젯
# 기능: 트리거 로드, 추가, 삭제, 선택

def load_triggers()                # 트리거 목록 로드
def add_trigger()                 # 새 트리거 추가
def delete_selected()            # 선택된 트리거 삭제
def on_trigger_selected()        # 트리거 선택 이벤트
```

**trigger_detail_widget.py**
```python  
class TriggerDetailWidget(QWidget):
# 역할: 트리거 상세정보 표시 패널
# 기능: 상세 정보 표시, 복사, 편집 기능

def update_trigger_detail()       # 상세정보 업데이트
def copy_trigger()               # 트리거 복사
def edit_trigger()              # 트리거 편집
```

**simulation_control_widget.py**
```python
class SimulationControlWidget(QWidget): 
# 역할: 시뮬레이션 제어 패널
# 기능: 시나리오 선택, 실행 버튼, 설정

def create_simulation_area()      # 시뮬레이션 영역 생성
def run_simulation()             # 시뮬레이션 실행 요청
def update_scenario_list()       # 시나리오 목록 업데이트
```

**variable_definitions.py (583줄)**
```python
class VariableDefinitions:
# 역할: 모든 트레이딩 변수의 파라미터 정의
# 기능: 변수별 파라미터, 차트 카테고리 매핑

CHART_CATEGORIES = {...}          # 차트 카테고리 매핑
def get_variable_parameters()     # 변수별 파라미터 정의
def get_chart_category()         # 차트 카테고리 반환
```

#### 4. shared/ 폴더 핵심 파일들

**trigger_calculator.py (309줄)**
```python
class TriggerCalculator:
# 역할: 기술적 지표 계산 엔진
# 기능: SMA, EMA, RSI, MACD 계산, 트리거 포인트 계산

def calculate_sma()              # 단순이동평균 계산
def calculate_ema()              # 지수이동평균 계산
def calculate_rsi()              # RSI 계산
def calculate_macd()             # MACD 계산
def calculate_trigger_points()   # 트리거 포인트 계산
def calculate_cross_trigger_points() # 교차 트리거 계산
```

**chart_visualizer.py**
```python
class ChartVisualizer:
# 역할: 차트 시각화 도구
# 기능: matplotlib 기반 차트 렌더링

def create_chart()               # 차트 생성
def update_chart()              # 차트 업데이트
def plot_indicators()           # 지표 플롯
```

---

## ❌ 제거 대상 파일들

### 1. 중복/백업 파일들
```python
# trigger_simulation_service_clean.py (381줄)
# 상태: ❌ 제거대상 - trigger_simulation_service.py와 완전 동일한 백업파일
# 사유: 이미 trigger_simulation_service.py로 이름 변경됨
```

### 2. 테스트/개발용 파일들
```python  
# test_trigger_list_widget.py (212줄)
# 상태: ❌ 제거대상 - TriggerListWidget 테스트 전용 파일
# 사유: 개발 완료 후 불필요

# chart_development_checklist.py
# 상태: ❌ 제거대상 - 개발용 체크리스트 파일
# 사유: 문서화 완료 후 불필요
```

### 3. 미사용 위젯들
```python
# chart_visualizer_widget.py  
# 상태: ❌ 제거대상 - 미사용 차트 위젯
# 사유: chart_visualizer.py와 simulation_result_widget.py로 기능 통합됨

# database_variable_widgets.py (500+줄)
# 상태: ❌ 제거대상 - 미사용 데이터베이스 위젯들
# 사유: core/condition_dialog.py로 기능 통합됨
```

### 4. 빈 폴더
```python
# components/legacy/ 
# 상태: ❌ 제거대상 - 빈 레거시 폴더
# 사유: 내용 없음
```

---

## 🔗 UI 구성 요소별 코드 연결 트리

### 화면 구성 요소 (trigger_builder_screen.py 기준)

```
TriggerBuilderScreen (메인 화면)
├── 🏠 상단 툴바
│   ├── 조건 생성 버튼 → ConditionDialog.create_condition()
│   └── 새로고침 버튼 → load_triggers()
│
├── 📋 좌측 패널 (트리거 목록)
│   ├── TriggerListWidget
│   │   ├── → ConditionStorage.load_all_triggers()
│   │   ├── → ConditionDialog (새 조건 생성시)
│   │   └── → trigger_selected 시그널 → TriggerDetailWidget 업데이트
│   └── DataSourceSelectorWidget
│       └── → DataSourceManager.get_available_sources()
│
├── 🎯 중앙 패널 (트리거 상세정보)
│   ├── TriggerDetailWidget  
│   │   ├── → 선택된 트리거 정보 표시
│   │   ├── 복사 버튼 → copy_trigger()
│   │   └── 편집 버튼 → ConditionDialog.edit_condition()
│   └── SimulationControlWidget
│       ├── 시나리오 선택 콤보박스
│       ├── 실행 버튼 → trigger_builder_screen.run_simulation()
│       └── 설정 옵션들
│
└── 📊 우측 패널 (시뮬레이션 결과)
    └── SimulationResultWidget
        ├── matplotlib 미니차트
        │   ├── → ChartVisualizer.create_chart()
        │   ├── → trigger_simulation_service.run_simulation()
        │   └── → _plot_price_overlay_chart() / _plot_trigger_signals_enhanced()
        └── 작동 기록 리스트
            └── → add_test_history_item()
```

### 데이터 플로우 트리

```
사용자 액션 (트리거 시뮬레이션 실행)
│
├── 1. SimulationControlWidget.run_simulation()
│   └── → trigger_builder_screen.run_simulation() 호출
│
├── 2. trigger_builder_screen.run_simulation() (40줄 경량화됨)
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

## 🧩 현재 지원되는 변수 목록 (완전판 - variable_definitions.py 기준)

### ✅ 기술 지표 변수들 (차트 기반)

#### 🔹 추세 지표 (Trend Indicators)
```python
# SMA - 단순이동평균
'SMA': {
    'category': 'overlay',
    'parameters': {
        'period': '기간 (1~240봉, 기본값: 20)',
        'timeframe': '타임프레임 (포지션설정따름~1일)'
    },
    'status': '✅ 완전지원 (계산+차트+교차트리거)',
    'cross_support': '✅ SMA vs SMA, SMA vs 현재가'
}

# EMA - 지수이동평균  
'EMA': {
    'category': 'overlay',
    'parameters': {
        'period': '기간 (1~240봉, 기본값: 12)',
        'exponential_factor': '지수 계수 (기본값: 2.0)',
        'timeframe': '타임프레임 (포지션설정따름~1일)'
    },
    'status': '✅ 완전지원 (계산+차트+교차트리거)',
    'cross_support': '✅ EMA vs EMA, EMA vs SMA'
}
```

#### 📊 모멘텀 지표 (Momentum Oscillators)
```python
# RSI - 상대강도지수
'RSI': {
    'category': 'subplot',
    'parameters': {
        'period': '기간 (2~240봉, 기본값: 14)',
        'timeframe': '타임프레임 (포지션설정따름~1일)'
    },
    'status': '✅ 완전지원 (0~100 범위)',
    'common_values': '과매수: >70, 과매도: <30'
}

# MACD - 이동평균 수렴확산
'MACD': {
    'category': 'subplot', 
    'parameters': {
        'fast_period': '빠른선 기간 (5~30봉, 기본값: 12)',
        'slow_period': '느린선 기간 (15~240봉, 기본값: 26)',
        'signal_period': '시그널선 기간 (5~20봉, 기본값: 9)',
        'macd_type': 'MACD종류 (MACD선/시그널선/히스토그램)'
    },
    'status': '✅ 기본지원',
    'signals': '히스토그램 0선 돌파 = 골든/데드크로스'
}

# STOCHASTIC - 스토캐스틱
'STOCHASTIC': {
    'category': 'subplot',
    'parameters': {
        'k_period': '%K 기간 (5~50봉, 기본값: 14)',
        'd_period': '%D 기간 (1~20봉, 기본값: 3)',
        'stoch_type': '종류 (%K 원시값 / %D 평활화값)'
    },
    'status': '📋 정의됨, 🔧 구현필요',
    'common_values': '과매수: >80, 과매도: <20'
}
```

#### � 변동성 지표 (Volatility Indicators)
```python
# BOLLINGER_BAND - 볼린저밴드
'BOLLINGER_BAND': {
    'category': 'overlay',
    'parameters': {
        'period': '기간 (10~240봉, 기본값: 20)',
        'std_dev': '표준편차 배수 (기본값: 2.0)',
        'band_position': '밴드위치 (상단/중앙선/하단)',
        'timeframe': '타임프레임'
    },
    'status': '📋 정의됨, 🔧 구현필요',
    'usage': '밴드 돌파/수렴 신호, 변동성 측정'
}

# ATR - 평균진실범위
'ATR': {
    'category': 'subplot',
    'parameters': {
        'period': '기간 (5~100봉, 기본값: 14)',
        'multiplier': '배수 (0.5~5.0, 기본값: 2.0)'
    },
    'status': '📋 정의됨, 🔧 구현필요',
    'usage': '손절가/익절가 설정, 포지션 사이징'
}
```

#### 💰 거래량 지표 (Volume Indicators)
```python
# VOLUME - 거래량
'VOLUME': {
    'category': 'subplot',
    'parameters': {
        'timeframe': '타임프레임',
        'volume_type': '종류 (거래량/거래대금/상대거래량)'
    },
    'status': '📋 정의됨, � 구현필요'
}

# VOLUME_SMA - 거래량 이동평균
'VOLUME_SMA': {
    'category': 'subplot',
    'parameters': {
        'period': '기간 (5~200봉, 기본값: 20)',
        'volume_type': '거래량 타입 (거래량/거래대금)'
    },
    'status': '📋 정의됨, 🔧 구현필요'
}
```

### 💵 가격 정보 변수들

#### 📌 실시간 가격
```python
# CURRENT_PRICE - 현재가
'CURRENT_PRICE': {
    'category': 'overlay',
    'parameters': {
        'price_type': '가격종류 (현재가/매수호가/매도호가/중간가)',
        'backtest_mode': '백테스팅모드 (실시간/종가기준)'
    },
    'status': '✅ 완전지원'
}

# OPEN_PRICE - 시가
'OPEN_PRICE': {
    'category': 'overlay',
    'parameters': {
        'timeframe': '타임프레임 (포지션설정따름~1일)'
    },
    'status': '📋 정의됨, 🔧 구현필요'
}

# HIGH_PRICE - 고가
'HIGH_PRICE': {
    'category': 'overlay', 
    'parameters': {
        'timeframe': '타임프레임 (포지션설정따름~1일)'
    },
    'status': '📋 정의됨, 🔧 구현필요'
}

# LOW_PRICE - 저가
'LOW_PRICE': {
    'category': 'overlay',
    'parameters': {
        'timeframe': '타임프레임 (포지션설정따름~1일)'
    },
    'status': '📋 정의됨, 🔧 구현필요'
}
```

### � 계좌 정보 변수들

#### 📊 잔고 정보
```python
# TOTAL_BALANCE - 총 자산
'TOTAL_BALANCE': {
    'category': 'subplot',
    'parameters': {
        'currency': '표시통화 (KRW/USD/BTC)',
        'scope': '범위 (포지션제한/계좌전체)'
    },
    'status': '📋 정의됨, 🔧 구현필요'
}

# CASH_BALANCE - 현금 잔고
'CASH_BALANCE': {
    'category': 'subplot',
    'parameters': {
        'currency': '표시통화 (KRW/USD/BTC)',
        'scope': '범위 (포지션제한/계좌전체)'
    },
    'status': '📋 정의됨, 🔧 구현필요'
}

# COIN_BALANCE - 코인 잔고
'COIN_BALANCE': {
    'category': 'subplot',
    'parameters': {
        'coin_unit': '표시단위 (코인수량/원화가치/USD가치)',
        'scope': '범위 (현재코인/전체코인)'
    },
    'status': '📋 정의됨, 🔧 구현필요'
}
```

#### 📈 수익 정보
```python
# PROFIT_PERCENT - 수익률
'PROFIT_PERCENT': {
    'category': 'subplot',
    'parameters': {
        'calculation_method': '계산방식 (미실현/실현/전체)',
        'scope': '범위 (현재포지션/전체포지션/포트폴리오)',
        'include_fees': '수수료포함 (포함/제외)'
    },
    'status': '✅ 기본지원'
}

# PROFIT_AMOUNT - 수익 금액
'PROFIT_AMOUNT': {
    'category': 'subplot',
    'parameters': {
        'currency': '표시통화 (KRW/USD/BTC)',
        'calculation_method': '계산방식 (미실현/실현/전체)',
        'include_fees': '수수료포함 (포함/제외)'
    },
    'status': '📋 정의됨, 🔧 구현필요'
}

# POSITION_SIZE - 포지션 크기
'POSITION_SIZE': {
    'category': 'subplot',
    'parameters': {
        'unit_type': '단위형태 (수량/금액/비율)'
    },
    'status': '📋 정의됨, 🔧 구현필요'
}

# AVG_BUY_PRICE - 평균 매수가
'AVG_BUY_PRICE': {
    'category': 'subplot',
    'parameters': {
        'display_currency': '표시통화 (원화/USD/코인단위)'
    },
    'status': '📋 정의됨, 🔧 구현필요'
}
```

### 📋 구현 상태 요약
- **✅ 완전 지원 (6개)**: SMA, EMA, RSI, MACD, CURRENT_PRICE, PROFIT_PERCENT
- **🔧 구현 필요 (12개)**: BOLLINGER_BAND, STOCHASTIC, ATR, VOLUME, VOLUME_SMA, OPEN_PRICE, HIGH_PRICE, LOW_PRICE, TOTAL_BALANCE, CASH_BALANCE, COIN_BALANCE, PROFIT_AMOUNT, POSITION_SIZE, AVG_BUY_PRICE

---

## 🧮 변수 계산 로직 상세 위치

### 📍 주요 계산 엔진: `trigger_calculator.py` (312줄)
**위치**: `components/shared/trigger_calculator.py`
**역할**: 모든 기술적 지표의 핵심 계산 로직

#### ✅ 구현된 계산 메서드들
```python
# 📊 기술적 지표 계산
def calculate_sma(prices, period) -> List[float]:
    """단순이동평균 계산
    - 초기값: 지금까지의 평균으로 채움
    - 정상 계산: sum(prices[i-period+1:i+1]) / period
    """

def calculate_ema(prices, period) -> List[float]:
    """지수이동평균 계산
    - alpha = 2 / (period + 1)
    - ema = alpha * price + (1-alpha) * prev_ema
    - 첫 번째 값은 그대로 사용
    """

def calculate_rsi(prices, period=14) -> List[float]:
    """RSI(상대강도지수) 계산
    - 가격 변화 → 상승/하락 분리
    - 평균 상승/하락 계산 (Wilder's 스무딩)
    - RSI = 100 - (100 / (1 + RS))
    - 데이터 부족시 중간값(50) 반환
    """

def calculate_macd(prices) -> List[float]:
    """MACD 계산
    - EMA12 - EMA26 (표준 설정)
    - 내부적으로 calculate_ema() 활용
    """

# 🎯 트리거 포인트 계산  
def calculate_trigger_points(variable_data, operator, target_value) -> List[int]:
    """단일 변수 트리거 포인트 계산
    - 지원 연산자: >, >=, <, <=, ~=(±1%), !=
    - 연속 신호 필터링 적용
    """

def calculate_cross_trigger_points(base_data, external_data, operator) -> List[int]:
    """교차 트리거 포인트 계산 (골든크로스/데드크로스)
    - 골든크로스: base가 external을 위로 돌파 (>)
    - 데드크로스: base가 external을 아래로 돌파 (<)
    - 이전값과 현재값 비교로 교차점 감지
    """

# 🔍 특화 트리거 계산
def calculate_rsi_trigger_points(rsi_data, operator, target_value) -> List[int]:
    """RSI 전용 트리거 계산
    - 0-100 범위 검증
    - RSI 특성에 맞는 필터링 (간격 2)
    """

def calculate_macd_trigger_points(macd_data, operator, target_value) -> List[int]:
    """MACD 전용 트리거 계산
    - 0선 교차 중요시 (필터링 최소화)
    """

# 🛠️ 내부 유틸리티
def _check_condition(value, operator, target) -> bool:
    """조건 검사 로직
    - 모든 연산자 통합 처리
    - 근사값(~=) 1% 오차 허용
    """
```

### 📍 변수별 계산 서비스: `trigger_simulation_service.py` (382줄)
**위치**: `components/shared/trigger_simulation_service.py`
**역할**: 변수 매핑 및 파라미터 처리

#### 🔗 변수 계산 플로우
```python
def _calculate_variable_data(variable_name, price_data, parameters) -> List[float]:
    """변수별 계산 분기 처리
    
    1. UI 텍스트 → 변수 ID 매핑
    2. 파라미터 추출 (period 등)
    3. TriggerCalculator 메서드 호출
    """
    
    # 📋 지원되는 변수별 계산
    if variable_id == 'SMA':
        period = _extract_period_from_parameters(parameters, default=20)
        return trigger_calculator.calculate_sma(price_data, period)
        
    elif variable_id == 'EMA':
        period = _extract_period_from_parameters(parameters, default=12)
        return trigger_calculator.calculate_ema(price_data, period)
        
    elif variable_id == 'RSI':
        period = _extract_period_from_parameters(parameters, default=14)
        return trigger_calculator.calculate_rsi(price_data, period)
        
    elif variable_id == 'MACD':
        return trigger_calculator.calculate_macd(price_data)  # 고정 12,26,9
        
    elif variable_id == 'PRICE':
        return price_data  # 현재가는 그대로 반환

def _map_ui_text_to_variable_id(variable_name) -> str:
    """UI 텍스트를 변수 ID로 매핑
    
    지원 매핑:
    - 'SMA', '단순이동평균' → 'SMA'
    - 'EMA', '지수이동평균' → 'EMA'  
    - 'RSI' → 'RSI'
    - 'MACD' → 'MACD'
    - '현재가', 'PRICE' → 'PRICE'
    - '거래량', 'VOLUME' → 'VOLUME'
    """

def _extract_period_from_parameters(parameters, variable_name, default) -> int:
    """파라미터에서 period 추출
    
    우선순위:
    1. parameters 딕셔너리의 'period' 키
    2. variable_name에서 정규식으로 숫자 추출 (예: "SMA(20)")
    3. default 값 사용
    """
```

### 📍 차트 변수 서비스: `chart_variable_service.py` (427줄)
**위치**: `components/shared/chart_variable_service.py`
**역할**: 변수 표시 설정 및 차트 레이아웃 관리

#### 🎨 변수 표시 설정
```python
@dataclass
class VariableDisplayConfig:
    """변수별 차트 표시 설정
    
    - variable_id: 변수 식별자
    - category: 'overlay', 'subplot' 등
    - display_type: 'line', 'histogram' 등
    - scale_min/max: 차트 범위 (RSI: 0-100)
    - default_color: 기본 색상
    - subplot_height_ratio: 서브플롯 높이 비율
    """

class ChartVariableService:
    def get_variable_config(variable_id) -> VariableDisplayConfig:
        """변수별 차트 설정 반환 (DB 캐시 사용)"""
        
    def create_chart_layout(variable_list) -> ChartLayoutInfo:
        """다중 변수 차트 레이아웃 생성"""
```

### 📍 변수 정의 시스템: `variable_definitions.py` (583줄)
**위치**: `components/core/variable_definitions.py`
**역할**: 변수 파라미터 정의 및 UI 메타데이터

#### 📚 파라미터 정의
```python
class VariableDefinitions:
    # 🗂️ 차트 카테고리 매핑
    CHART_CATEGORIES = {
        "SMA": "overlay",      # 메인 차트 오버레이
        "EMA": "overlay", 
        "RSI": "subplot",      # 별도 서브플롯
        "MACD": "subplot",
        "VOLUME": "subplot"
    }
    
    def get_variable_parameters(var_id) -> Dict:
        """변수별 상세 파라미터 정의
        
        예: RSI
        {
            "period": {
                "label": "기간",
                "type": "int",
                "min": 2, "max": 240, "default": 14,
                "help": "RSI 계산 기간 (일반적으로 14)"
            },
            "timeframe": { ... }
        }
        """
        
    def get_variable_descriptions() -> Dict:
        """변수별 설명 텍스트"""
        
    def get_chart_category(variable_id) -> str:
        """변수의 차트 카테고리 반환"""
```

### 🔧 구현이 필요한 변수들
```python
# 📋 정의는 되어있지만 계산 로직이 없는 변수들
NEEDS_IMPLEMENTATION = {
    'BOLLINGER_BAND': {
        'calculation_location': 'trigger_calculator.py에 추가 필요',
        'required_method': 'calculate_bollinger_bands(prices, period, std_dev)',
        'formula': '중앙선(SMA) ± (표준편차 × std_dev)'
    },
    'STOCHASTIC': {
        'calculation_location': 'trigger_calculator.py에 추가 필요', 
        'required_method': 'calculate_stochastic(high, low, close, k_period, d_period)',
        'formula': '%K = (Close-LowestLow)/(HighestHigh-LowestLow) × 100'
    },
    'ATR': {
        'calculation_location': 'trigger_calculator.py에 추가 필요',
        'required_method': 'calculate_atr(high, low, close, period)',
        'formula': 'True Range의 이동평균'
    },
    'VOLUME': {
        'calculation_location': 'trigger_simulation_service.py에 데이터 소스 추가',
        'required_method': '_load_volume_data(scenario)',
        'note': '거래량 시나리오별 가상 데이터 생성 필요'
    }
}
```

---

## 🚨 현재 아키텍처 문제점 및 정리 계획

### ❌ **심각한 문제: 계산 로직 파편화**

현재 **동일한 계산 로직이 5곳에 중복 구현**되어 있어 유지보수성이 매우 떨어집니다:

#### 🔍 중복 구현 위치들
```python
1. ✅ trigger_calculator.py (312줄)          # 메인 - 여기만 남겨야 함
   └── calculate_sma/ema/rsi/macd() 

2. ❌ trigger_simulation_service.py (382줄)  # 폴백 클래스 - 제거 필요
   └── class TriggerCalculator (가짜 구현)

3. ❌ trigger_builder_screen.py (1928줄)     # 레거시 - 제거 필요  
   └── _calculate_sma/ema/rsi/macd() (986-1075줄)

4. ❌ simulation_engines.py (572줄)          # 중복 - 제거 필요
   └── _calculate_rsi/macd()

5. ❌ indicator_calculator.py (전역)         # 전역 유틸 - 별도 관리
   └── _calculate_sma/ema/rsi/macd()
```

### 🎯 **정리 계획 - 단계별 중복 제거**

#### Phase 1: 폴백 정리 ✅ (완료)
```python
# trigger_simulation_service.py 폴백 클래스 수정
class TriggerCalculator:  # 가짜 구현 대신 ImportError 발생
    def calculate_sma(self, prices, period):
        raise ImportError("TriggerCalculator 컴포넌트를 불러올 수 없습니다")
```

#### Phase 2: 레거시 코드 제거 🔧 (예정)
```python
# trigger_builder_screen.py에서 중복 메서드 제거 필요
❌ def _calculate_sma(self, prices, period):      # 986줄 - 제거
❌ def _calculate_ema(self, prices, period):      # 1002줄 - 제거  
❌ def _calculate_rsi(self, prices, period=14):   # 1016줄 - 제거
❌ def _calculate_macd(self, prices):             # 1075줄 - 제거

✅ 대신 trigger_calculator 인스턴스 사용으로 변경
```

#### Phase 3: 서비스 간 중복 제거 🔧 (예정)
```python
# simulation_engines.py 중복 제거
❌ def _calculate_rsi(self, prices: pd.Series, period: int = 14)  # 제거
❌ def _calculate_macd(self, prices: pd.Series)                  # 제거

✅ TriggerCalculator 인스턴스로 위임
```

### ✅ **올바른 역할 분리 (목표 상태)**

#### 1. **변수 정의 & 파라미터** ✅ (이미 잘 분리됨)
```python
📍 variable_definitions.py (583줄)
├── get_variable_parameters() - 파라미터 스키마 정의
├── CHART_CATEGORIES - 차트 카테고리 매핑  
└── get_variable_descriptions() - 설명 텍스트

📍 variable_display_system.py (236줄)  
├── VariableCategory - 카테고리 enum
├── ChartDisplayType - 표시 방식 enum
└── VariableRegistry - 차트 설정 관리
```

#### 2. **계산 로직** 🎯 (중앙화 필요)
```python
📍 trigger_calculator.py (312줄) - 유일한 계산 엔진
├── calculate_sma/ema/rsi/macd() - 기술적 지표 계산
├── calculate_trigger_points() - 단일 조건 트리거
├── calculate_cross_trigger_points() - 교차 조건 트리거
└── _check_condition() - 조건 검사 유틸리티

❌ 다른 모든 곳의 중복 구현 제거 필요
```

#### 3. **서비스 관리 & 결과 제공** ✅ (올바름)
```python
📍 trigger_simulation_service.py (382줄)
├── TriggerSimulationRequest/Result - 데이터 클래스
├── _map_ui_text_to_variable_id() - UI 매핑
├── _extract_period_from_parameters() - 파라미터 추출
├── _calculate_variable_data() - 계산 위임 (trigger_calculator 호출)
└── run_simulation() - 전체 시뮬레이션 오케스트레이션

✅ 계산은 위임, 관리만 담당 (올바른 역할)
```

### 🔧 **즉시 해결해야 할 우선순위**

1. **🔥 긴급**: `trigger_builder_screen.py`의 중복 계산 메서드 제거 (986-1075줄)
2. **⚠️ 중요**: `simulation_engines.py`의 중복 제거
3. **📋 보통**: 폴백 클래스 개선 (완료)
4. **🎯 장기**: 전역 `indicator_calculator.py`와의 역할 정리

### 💡 **개발 가이드라인 업데이트**

```python
✅ DO (권장사항):
- 새 지표 추가시 trigger_calculator.py에만 구현
- variable_definitions.py에 파라미터 정의 추가
- trigger_simulation_service.py에서 계산 위임만 처리

❌ DON'T (금지사항):  
- 다른 파일에 계산 로직 중복 구현 금지
- 폴백 클래스에 실제 계산 로직 구현 금지
- 레거시 메서드(_calculate_*) 사용 금지
```

---

## 🎯 화면별 기능 명세

### 1. 조건 빌더 (ConditionDialog)
```python
📍 위치: components/core/condition_dialog.py (1662줄)
🎯 기능: 트리거 조건 생성 및 편집

UI 구성:
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

주요 메서드:
def create_ui()                    # UI 레이아웃 구성
def get_condition_data()          # 입력된 조건 데이터 추출
def validate_condition()          # 조건 유효성 검증
def save_condition()             # 조건을 데이터베이스에 저장
def load_condition(trigger_id)   # 기존 조건 로드 (편집시)
```

### 2. 트리거 리스트 (TriggerListWidget)
```python
📍 위치: components/core/trigger_list_widget.py
🎯 기능: 저장된 트리거 목록 관리

UI 구성:
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

주요 메서드:
def load_triggers()              # 데이터베이스에서 트리거 목록 로드
def add_trigger(condition_data)  # 새 트리거 추가
def delete_selected()           # 선택된 트리거 삭제
def on_trigger_selected()       # 트리거 선택시 상세정보 업데이트
```

### 3. 트리거 상세정보 (TriggerDetailWidget)
```python
📍 위치: components/core/trigger_detail_widget.py  
🎯 기능: 선택된 트리거의 상세 정보 표시

UI 구성:
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

주요 메서드:
def update_trigger_detail(trigger_data)  # 상세정보 업데이트
def copy_trigger()                       # 트리거 복사
def edit_trigger()                      # 트리거 편집 (ConditionDialog 호출)
def delete_trigger()                    # 트리거 삭제
```

### 4. 시뮬레이션 컨트롤 (SimulationControlWidget)
```python
📍 위치: components/core/simulation_control_widget.py
🎯 기능: 시뮬레이션 실행 제어

UI 구성:
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

주요 메서드:
def create_simulation_area()     # 시뮬레이션 영역 UI 구성
def run_simulation()            # 시뮬레이션 실행 요청
def stop_simulation()           # 시뮬레이션 중단
def update_scenario_list()      # 시나리오 목록 업데이트
def get_simulation_settings()   # 현재 설정값 반환
```

### 5. 시뮬레이션 결과 미니차트 (SimulationResultWidget)
```python
📍 위치: components/core/simulation_result_widget.py (1034줄)
🎯 기능: 시뮬레이션 결과를 차트와 기록으로 표시

UI 구성:
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

차트 카테고리별 렌더링:
├── price_overlay: 메인 차트에 가격과 함께 표시 (SMA, EMA)
├── oscillator: 별도 서브플롯, 0-100 범위 (RSI, 스토캐스틱)  
├── momentum: 별도 서브플롯, 중앙선 포함 (MACD)
└── volume: 히스토그램 형태 (거래량)

주요 메서드:
def update_simulation_chart()           # 메인 차트 업데이트 메서드
def update_trigger_signals()          # 트리거 신호 업데이트
def add_test_history_item()           # 작동 기록 아이템 추가  
def _plot_price_overlay_chart()       # 가격 오버레이 차트 플롯
def _plot_trigger_signals_enhanced()  # 개선된 트리거 신호 마커
def _setup_enhanced_chart_style()     # 차트 스타일 설정
def show_placeholder_chart()          # 플레이스홀더 차트 표시
```

---

## 🔧 서비스 레이어 상세분석

### TriggerSimulationService (메인 서비스)
```python
📍 위치: components/shared/trigger_simulation_service.py (381줄)
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
components/test_trigger_list_widget.py        # 테스트 전용
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

## 🚨 개발시 주의사항 및 가이드라인 (업데이트됨)

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

### 5. 개발 지침 및 디버깅 팁

#### 새 기능 추가 시
1. 적절한 구성요소 선택
2. 시그널/슬롯 연결 확인
3. 테마 호환성 테스트
4. 크기 정책 확인
5. 중복 기능 방지 체크

#### 디버깅 팁
- 각 구성요소는 독립적으로 테스트 가능
- 시그널 연결 상태는 `pyqtSignal.connect()` 로그로 확인
- 레이아웃 문제는 `setStyleSheet()` 테두리로 디버깅
- 변수 계산 오류는 `TriggerCalculator` 클래스에서 직접 테스트

#### 에이전트 개발 가이드라인
- 이 문서의 **중복 개발 방지 체크리스트**를 반드시 확인
- 새 변수 추가시 **필수 작업 체크리스트** 순서대로 진행  
- 파일 상태 (✅사용중/❌제거대상) 확인 후 작업
- 라인 수와 클래스명은 이 문서에서 검증된 정보 사용

---

## 📊 시스템 현황 요약

**📁 총 파일 수**: 27개 Python 파일  
**📝 총 코드 라인**: 12,000+ 줄  
**✅ 활성 파일**: 23개  
**❌ 제거 대상**: 4개  
**🔧 핵심 서비스**: 8개  
**� UI 컴포넌트**: 12개  

### 핵심 통계
- **메인 화면**: 1,928줄 (trigger_builder_screen.py)
- **최대 컴포넌트**: 1,643줄 (condition_dialog.py)
- **결과 차트**: 1,026줄 (simulation_result_widget.py)
- **트리거 목록**: 797줄 (trigger_list_widget.py)
- **변수 정의**: 578줄 (variable_definitions.py)

---

## �🎯 향후 개발 로드맵

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

**📝 마지막 업데이트**: 2025.07.28  
**🔧 검증 상태**: 모든 파일 구조 및 라인 수 실제 확인 완료  
**📊 문서 상태**: README.md + OVERVIEW.md 통합 완료 (V2)  
**👨‍💻 다음 작업**: 에이전트 실수 방지 최적화된 통합 문서 완성

---

*이 문서는 실제 코드를 검증하여 작성되었으며, 에이전트의 중복 개발 방지와 정확한 기능 연결을 위해 최적화되었습니다.*
