# 트리거 빌더 아키텍처 리팩토링 계획서

## 📅 작성일: 2025년 7월 28일

## 🎯 문제 정의

### 현재 상황
- `engines` 폴더: 미니 시뮬레이션 결과를 미니차트에 플롯하는 기능
- 코드가 `trigger_builder` 전용으로 흩어져 있어 다른 탭에서 재사용 불가
- 에이전트가 매번 상황 파악에 채팅 세션을 다 소모하는 문제

### 제안된 변경사항
- `engines` → `mini_simulation_engines` 폴더명 변경
- 재사용 가능한 컴포넌트들을 `components`로 이동

---

## 🔍 현재 아키텍처 분석

### 현재 폴더 구조
```
trigger_builder/
├── engines/                          # 미니 시뮬레이션 엔진들
│   ├── data/
│   │   └── sampled_market_data.sqlite3
│   ├── embedded_simulation_engine.py
│   ├── real_data_simulation.py
│   ├── robust_simulation_engine.py
│   └── __init__.py
├── components/
│   ├── core/                         # TriggerBuilder 전용
│   │   ├── simulation_control_widget.py
│   │   ├── simulation_result_widget.py
│   │   └── ...
│   ├── shared/                       # 공유 컴포넌트
│   │   ├── simulation_engines.py     # engines와 중복!
│   │   ├── trigger_calculator.py
│   │   ├── chart_visualizer.py
│   │   ├── minichart_variable_service.py
│   │   └── ...
│   ├── data_source_manager.py       # engines/data 관리
│   └── data_source_selector.py
└── trigger_builder_screen.py
```

### 🔥 중요한 발견: 중복 구조
1. **engines/ vs components/shared/simulation_engines.py**
   - `engines/` 폴더의 시뮬레이션 엔진들
   - `components/shared/simulation_engines.py`에도 동일한 엔진들 존재
   - 코드 중복과 혼란 발생!

2. **미니차트 관련 컴포넌트들**
   - `components/shared/minichart_variable_service.py`
   - `components/core/simulation_result_widget.py` (미니차트 위젯 포함)
   - `trigger_builder_screen.py`의 `MiniChartWidget` 클래스

---

## 🎯 리팩토링 목표

### 1. 명확한 책임 분리
- **데이터 엔진**: 순수한 데이터 처리 로직
- **UI 컴포넌트**: 재사용 가능한 위젯들
- **통합 서비스**: 엔진과 UI를 연결하는 서비스 계층

### 2. 재사용성 극대화
- 다른 탭에서도 미니차트 시뮬레이션 활용 가능
- 컴포넌트 기반 아키텍처로 확장성 확보

### 3. 코드 중복 제거
- engines/와 components/shared/ 중복 해결
- 단일 진실의 원천(Single Source of Truth) 구현

---

## 🏗️ 제안하는 새로운 아키텍처

### A. 공통 미니차트 시스템 (strategy_management/components)
```
strategy_management/
├── components/
│   ├── mini_simulation/              # 새로운 공통 폴더
│   │   ├── engines/                  # 데이터 엔진들
│   │   │   ├── data/
│   │   │   │   └── sampled_market_data.sqlite3
│   │   │   ├── embedded_simulation_engine.py
│   │   │   ├── real_data_simulation.py
│   │   │   ├── robust_simulation_engine.py
│   │   │   ├── data_source_manager.py
│   │   │   └── __init__.py
│   │   ├── widgets/                  # UI 컴포넌트들
│   │   │   ├── mini_chart_widget.py
│   │   │   ├── simulation_control_widget.py
│   │   │   ├── simulation_result_widget.py
│   │   │   ├── data_source_selector.py
│   │   │   └── __init__.py
│   │   ├── services/                 # 통합 서비스들
│   │   │   ├── mini_simulation_service.py
│   │   │   ├── minichart_variable_service.py
│   │   │   ├── trigger_simulation_service.py
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── shared/                       # 기존 공유 컴포넌트들
│   │   ├── trigger_calculator.py
│   │   ├── chart_visualizer.py
│   │   └── ...
│   └── __init__.py
```

### B. TriggerBuilder 전용 컴포넌트들 (trigger_builder/components)
```
trigger_builder/
├── components/
│   ├── core/                         # TriggerBuilder 전용
│   │   ├── condition_dialog.py
│   │   ├── trigger_list_widget.py
│   │   ├── trigger_detail_widget.py
│   │   └── ...
│   ├── adapters/                     # 공통 컴포넌트 어댑터들
│   │   ├── mini_simulation_adapter.py
│   │   └── __init__.py
│   └── __init__.py
└── trigger_builder_screen.py
```

---

## 📋 상세 리팩토링 계획

### Phase 1: 공통 미니차트 시스템 구축
1. **새로운 폴더 구조 생성**
   ```
   strategy_management/components/mini_simulation/
   ├── engines/
   ├── widgets/  
   ├── services/
   └── __init__.py
   ```

2. **데이터 엔진 이동 및 통합**
   - `trigger_builder/engines/` → `mini_simulation/engines/`
   - `components/shared/simulation_engines.py` 제거 (중복 해결)
   - `data_source_manager.py`, `data_source_selector.py` → `engines/`

3. **UI 컴포넌트 추출 및 일반화**
   - `simulation_control_widget.py` → `widgets/`
   - `simulation_result_widget.py` → `widgets/`
   - `MiniChartWidget` 클래스 → `widgets/mini_chart_widget.py`

4. **서비스 레이어 구축**
   - `trigger_simulation_service.py` → `services/`
   - `minichart_variable_service.py` → `services/`
   - 새로운 `mini_simulation_service.py` 생성

### Phase 2: TriggerBuilder 어댑터 구현
1. **어댑터 패턴 적용**
   ```python
   # trigger_builder/components/adapters/mini_simulation_adapter.py
   class TriggerBuilderMiniSimulationAdapter:
       def __init__(self):
           from strategy_management.components.mini_simulation import (
               MiniSimulationService, MiniChartWidget
           )
           self.simulation_service = MiniSimulationService()
           self.chart_widget = MiniChartWidget()
       
       def run_trigger_simulation(self, trigger_data, scenario):
           # TriggerBuilder 특화 로직
           pass
   ```

2. **TriggerBuilder 특화 로직 유지**
   - 트리거 계산 로직은 TriggerBuilder에 유지
   - 미니차트 시뮬레이션만 공통 컴포넌트 활용

### Phase 3: 다른 탭에서의 재사용 구현
1. **StrategyMaker 탭 연동**
   ```python
   # strategy_maker/components/simulation_preview.py
   from strategy_management.components.mini_simulation import (
       MiniSimulationService, MiniChartWidget
   )
   
   class StrategySimulationPreview:
       def __init__(self):
           self.simulation_service = MiniSimulationService()
           self.chart_widget = MiniChartWidget()
   ```

2. **Backtest 탭 연동**
   - 백테스트 결과를 미니차트로 시각화
   - 동일한 데이터 엔진과 차트 컴포넌트 활용

---

## 🔧 구현 상세 사항

### 1. MiniSimulationService (핵심 서비스)
```python
# strategy_management/components/mini_simulation/services/mini_simulation_service.py
class MiniSimulationService:
    def __init__(self):
        self.data_source_manager = DataSourceManager()
        self.simulation_engines = {
            'embedded': EmbeddedSimulationEngine(),
            'real_db': RealDataSimulationEngine(),
            'synthetic': RobustSimulationEngine()
        }
    
    def run_simulation(self, scenario: str, data_source: str = 'auto'):
        """시나리오 시뮬레이션 실행"""
        engine = self._get_engine(data_source)
        data = engine.get_scenario_data(scenario)
        return self._format_chart_data(data)
    
    def get_available_scenarios(self):
        """사용 가능한 시나리오 목록"""
        return ['bull_market', 'bear_market', 'surge', 'crash', 'sideways']
    
    def get_data_sources(self):
        """사용 가능한 데이터 소스 목록"""
        return list(self.simulation_engines.keys())
```

### 2. MiniChartWidget (재사용 가능한 차트 위젯)
```python
# strategy_management/components/mini_simulation/widgets/mini_chart_widget.py
class MiniChartWidget(QWidget):
    # 시그널
    chart_updated = pyqtSignal(dict)
    simulation_completed = pyqtSignal(str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.simulation_service = MiniSimulationService()
        self.setup_ui()
    
    def update_chart(self, scenario: str, data_source: str = 'auto'):
        """차트 업데이트"""
        result = self.simulation_service.run_simulation(scenario, data_source)
        self._render_chart(result)
        self.chart_updated.emit(result)
    
    def set_trigger_points(self, trigger_points: List[Dict]):
        """트리거 포인트 표시 (TriggerBuilder 전용 기능)"""
        # 옵셔널 기능으로 구현
        pass
```

### 3. TriggerBuilder 어댑터
```python
# trigger_builder/components/adapters/mini_simulation_adapter.py
class TriggerBuilderMiniSimulationAdapter:
    def __init__(self):
        from strategy_management.components.mini_simulation import (
            MiniSimulationService, MiniChartWidget
        )
        self.simulation_service = MiniSimulationService()
        self.chart_widget = MiniChartWidget()
        self.trigger_calculator = TriggerCalculator()
    
    def run_trigger_simulation(self, trigger_data: Dict, scenario: str):
        """트리거 기반 시뮬레이션"""
        # 1. 기본 시뮬레이션 데이터 생성
        sim_result = self.simulation_service.run_simulation(scenario)
        
        # 2. 트리거 계산 (TriggerBuilder 전용)
        trigger_points = self.trigger_calculator.calculate(
            trigger_data, sim_result['price_data']
        )
        
        # 3. 차트에 트리거 포인트 표시
        self.chart_widget.set_trigger_points(trigger_points)
        
        return {
            'simulation_data': sim_result,
            'trigger_points': trigger_points,
            'triggered': len(trigger_points) > 0
        }
```

---

## 📊 재사용성 분석

### 현재 재사용 가능한 컴포넌트들
| 컴포넌트 | 현재 위치 | 제안 위치 | 재사용 범위 |
|---------|----------|----------|------------|
| 시뮬레이션 엔진들 | `engines/` | `mini_simulation/engines/` | 전체 앱 |
| 데이터 소스 관리 | `components/` | `mini_simulation/engines/` | 전체 앱 |
| 미니차트 위젯 | `trigger_builder_screen.py` | `mini_simulation/widgets/` | 전체 앱 |
| 시뮬레이션 결과 위젯 | `components/core/` | `mini_simulation/widgets/` | 전체 앱 |
| 트리거 계산기 | `components/shared/` | `trigger_builder/components/` | TriggerBuilder 전용 |

### 예상 재사용 시나리오
1. **StrategyMaker 탭**: 전략 프리뷰에서 미니차트 시뮬레이션
2. **Backtest 탭**: 백테스트 결과 시각화
3. **Analysis 탭**: 시장 상황 분석 차트
4. **새로운 탭들**: 향후 추가되는 탭에서 미니차트 활용

---

## ⚖️ 장단점 분석

### 장점
1. **코드 재사용성 극대화**
   - 미니차트 시스템을 다른 탭에서 즉시 활용 가능
   - 개발 속도 향상 및 코드 중복 제거

2. **유지보수성 향상**
   - 단일 책임 원칙 적용
   - 버그 수정 시 한 곳만 수정하면 모든 탭에 적용

3. **확장성 확보**
   - 새로운 시뮬레이션 엔진 추가 용이
   - 새로운 차트 기능 추가 시 모든 탭에서 자동 활용

4. **에이전트 효율성**
   - 명확한 구조로 상황 파악 시간 단축
   - 컴포넌트별 독립적 개발 가능

### 단점
1. **초기 리팩토링 비용**
   - 기존 코드 이동 및 재구성 필요
   - 테스트 및 검증 작업 필요

2. **의존성 복잡도 증가**
   - 여러 탭에서 공통 컴포넌트 의존
   - 버전 호환성 관리 필요

3. **TriggerBuilder 특화 기능 추상화**
   - 트리거 관련 기능을 일반화해야 함
   - 일부 최적화된 기능 손실 가능성

---

## 🚀 마이그레이션 로드맵

### Step 1: 준비 단계 (1-2일)
- [ ] 현재 코드 의존성 분석
- [ ] 공통 컴포넌트 인터페이스 설계
- [ ] 새로운 폴더 구조 생성

### Step 2: 데이터 레이어 마이그레이션 (2-3일)
- [ ] `engines/` → `mini_simulation/engines/` 이동
- [ ] 중복 시뮬레이션 엔진 코드 제거
- [ ] 데이터 소스 관리 시스템 통합

### Step 3: UI 레이어 마이그레이션 (3-4일)
- [ ] 미니차트 위젯 추출 및 일반화
- [ ] 시뮬레이션 컨트롤 위젯 이동
- [ ] 결과 표시 위젯 일반화

### Step 4: 서비스 레이어 구축 (2-3일)
- [ ] `MiniSimulationService` 구현
- [ ] 기존 서비스들 통합 및 정리
- [ ] API 인터페이스 표준화

### Step 5: TriggerBuilder 어댑터 구현 (2-3일)
- [ ] 어댑터 패턴 구현
- [ ] TriggerBuilder 특화 로직 유지
- [ ] 기존 기능 100% 호환성 확보

### Step 6: 테스트 및 검증 (2-3일)
- [ ] 모든 기능 동작 확인
- [ ] 성능 테스트
- [ ] 다른 탭에서 재사용 테스트

### 총 예상 기간: **12-18일**

---

## 🎯 즉시 실행 가능한 1단계 작업

### 우선순위 1: 폴더 구조 정리
```bash
# 1. 새로운 공통 폴더 생성
mkdir strategy_management/components/mini_simulation
mkdir strategy_management/components/mini_simulation/engines
mkdir strategy_management/components/mini_simulation/widgets  
mkdir strategy_management/components/mini_simulation/services

# 2. engines 폴더 이름 변경
mv trigger_builder/engines trigger_builder/mini_simulation_engines

# 3. 심볼릭 링크로 임시 호환성 유지
ln -s ../mini_simulation_engines trigger_builder/engines
```

### 우선순위 2: 중복 코드 제거
1. `components/shared/simulation_engines.py` 분석
2. `engines/` 폴더와 중복되는 부분 식별
3. 단일 소스로 통합

### 우선순위 3: 공통 인터페이스 정의
```python
# strategy_management/components/mini_simulation/__init__.py
from .services.mini_simulation_service import MiniSimulationService
from .widgets.mini_chart_widget import MiniChartWidget
from .engines.data_source_manager import DataSourceManager

__all__ = [
    'MiniSimulationService',
    'MiniChartWidget', 
    'DataSourceManager'
]
```

---

## 💡 결론 및 권장사항

### 핵심 결론
1. **현재 구조의 문제점 명확**: engines/와 components/shared/ 중복, TriggerBuilder 전용 코드 분산
2. **리팩토링 필요성 높음**: 재사용성, 유지보수성, 에이전트 효율성 모두 개선 가능
3. **실현 가능성 높음**: 기존 기능 100% 호환성 유지하면서 점진적 마이그레이션 가능

### 즉시 권장 조치
1. **engines 폴더명 변경**: `engines` → `mini_simulation_engines`
2. **중복 코드 정리**: `components/shared/simulation_engines.py` 제거
3. **공통 컴포넌트 폴더 생성**: `strategy_management/components/mini_simulation/`

### 장기적 비전
- **컴포넌트 기반 아키텍처**: 각 탭이 필요한 컴포넌트만 조합하여 사용
- **플러그인 시스템**: 새로운 시뮬레이션 엔진이나 차트 기능을 쉽게 추가
- **에이전트 친화적**: 명확한 구조로 AI 에이전트의 코드 이해도 향상

이 리팩토링을 통해 **코드 재사용성 극대화**, **유지보수성 향상**, **개발 효율성 증진**을 모두 달성할 수 있습니다.
