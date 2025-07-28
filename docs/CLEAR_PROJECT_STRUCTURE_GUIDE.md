# 🎯 에이전트를 위한 명확한 프로젝트 구조 가이드

## 📋 문제 해결됨!

기존의 복잡하고 Junction 링크에 의존하는 구조를 **명확하고 Git-호환되는 구조**로 리팩토링했습니다.

## 🏗️ 새로운 구조 (2025년 7월 28일)

```
📁 strategy_management/
├── 📊 shared_simulation/              # 🎯 모든 시뮬레이션 기능이 여기에!
│   ├── engines/
│   │   └── simulation_engines.py      # 모든 엔진 통합 (Junction 링크 불필요)
│   ├── data_sources/
│   │   └── market_data_manager.py     # 데이터 로드/검증
│   ├── charts/                        # (향후 차트 컴포넌트)
│   └── __init__.py                    # 통합 인터페이스
│
├── 📈 trigger_builder/                # TriggerBuilder (기존 유지)
│   ├── components/
│   ├── engines/                       # ⚠️ Junction 링크 (레거시)
│   ├── mini_simulation_engines/       # 기존 파일들
│   └── engines_wrapper.py             # Git 호환 래퍼
│
├── 📊 strategy_maker/                 # StrategyMaker (새로 정리)
│   ├── components/
│   │   └── simulation_panel.py        # 공통 시스템 활용 예제
│   └── __init__.py
│
└── 📋 components/                     # 기존 공통 컴포넌트들
    └── mini_simulation/               # ⚠️ 구버전 (곧 제거 예정)
```

## 🎯 다음 에이전트를 위한 명확한 지침

### 1️⃣ 시뮬레이션 관련 작업 시

**✅ 사용해야 할 곳:**
```python
# 새로운 명확한 구조 사용
from strategy_management.shared_simulation import (
    get_simulation_engine,
    create_quick_simulation,
    MarketDataLoader
)

# 빠른 시뮬레이션 생성
result = create_quick_simulation(scenario="bull", limit=100)
```

**❌ 사용하지 말 것:**
- `components/mini_simulation/` (구버전)
- `trigger_builder/engines/` (Junction 링크)
- 복잡한 어댑터 패턴들

### 2️⃣ 데이터 문제 해결 시

**문제**: "미니차트에 시장가 추세가 올바르게 플롯되지 않음"

**해결 방법:**
1. `shared_simulation/data_sources/market_data_manager.py` 확인
2. `SampleDataGenerator.generate_realistic_btc_data()` 메서드 검토
3. 시나리오별 데이터 생성 로직 수정

```python
# 데이터 검증
from strategy_management.shared_simulation import DataValidator

validator = DataValidator()
result = validator.validate_market_data(data)
print("검증 결과:", result)
```

### 3️⃣ StrategyMaker 화면 구현 시

**✅ 재사용 가능한 컴포넌트:**
```python
# 이미 구현된 시뮬레이션 패널 사용
from strategy_management.strategy_maker.components.simulation_panel import StrategySimulationPanel

# 메인 화면에 추가
simulation_panel = StrategySimulationPanel()
layout.addWidget(simulation_panel)
```

### 4️⃣ Git Clone 호환성

**✅ 이제 완전히 호환됨:**
- Junction 링크 대신 실제 파일 사용
- 모든 경로가 상대 import로 구성
- `shared_simulation/` 모듈이 모든 기능 제공

## 🐛 문제 해결 가이드

### 문제 1: "import 오류"
```python
# 해결: 새로운 경로 사용
from strategy_management.shared_simulation import get_simulation_engine
```

### 문제 2: "데이터가 이상함"
```python
# 해결: 데이터 검증 도구 사용
from strategy_management.shared_simulation import DataValidator
validation = DataValidator.validate_market_data(data)
```

### 문제 3: "차트가 안 그려짐"
```python
# 해결: StrategyMaker 예제 참고
# strategy_maker/components/simulation_panel.py 의 update_chart() 메서드 참고
```

## 🚀 즉시 실행 가능한 테스트

```python
# 새로운 구조 테스트
python -c "
from upbit_auto_trading.ui.desktop.screens.strategy_management.shared_simulation import create_quick_simulation
result = create_quick_simulation('bull', 50)
print('✅ 새로운 구조 정상 동작:', result['record_count'], '개 레코드')
"
```

## 📝 요약

1. **✅ 해결됨**: Junction 링크 제거, Git Clone 호환
2. **✅ 명확함**: `shared_simulation/`에 모든 기능 통합
3. **✅ 재사용**: StrategyMaker에서 바로 사용 가능한 컴포넌트
4. **✅ 문서화**: 에이전트가 헤매지 않을 명확한 구조

**다음 에이전트는 이제 `shared_simulation/` 폴더만 보면 모든 것을 이해할 수 있습니다!**
