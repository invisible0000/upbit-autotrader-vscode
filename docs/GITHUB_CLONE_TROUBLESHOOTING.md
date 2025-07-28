# GitHub Clone 사용자를 위한 문제 해결 가이드

## ⚠️ 중요: Junction 링크 문제 해결

GitHub에서 클론한 프로젝트에서 다음과 같은 오류가 발생할 수 있습니다:

```
ModuleNotFoundError: No module named 'trigger_builder.engines'
```

이는 Windows Junction 링크가 Git으로 전송되지 않기 때문입니다.

### 🛠️ 해결 방법

#### 방법 1: 심볼릭 링크 수동 생성 (Windows)
```powershell
# 관리자 권한으로 PowerShell 실행 후
cd upbit_auto_trading\ui\desktop\screens\strategy_management\trigger_builder
mklink /J engines mini_simulation_engines
```

#### 방법 2: 실제 디렉토리 복사 (안전한 방법)
```powershell
# trigger_builder 디렉토리에서
Copy-Item mini_simulation_engines engines -Recurse -Force
```

#### 방법 3: 공통 시스템 사용 (권장)
프로그램이 자동으로 fallback 메커니즘을 사용하여 공통 시스템으로 연결됩니다.
별도 작업 없이 그대로 실행 가능합니다.

### 🧪 동작 확인
```bash
python quick_start.py
# 또는
python run_desktop_ui.py
```

프로그램이 정상 실행되면 성공입니다.

## 🎯 데이터 세트 및 시나리오 문제 해결

### 현재 상황
- **문제**: 미니차트에서 시장가 추세가 시나리오에 맞지 않게 플롯됨
- **원인**: 샘플 DB에서 랜덤 데이터 추출이 시나리오별로 최적화되지 않음

### 문제 추적 경로
1. **데이터 소스**: `trigger_builder/mini_simulation_engines/data/sampled_market_data.sqlite3`
2. **데이터 로딩**: `embedded_simulation_engine.py` → `load_market_data()` 메서드
3. **시나리오 필터링**: `base_simulation_engines.py` → `filter_by_scenario()` 메서드
4. **차트 렌더링**: `trigger_detail_widget.py` → 미니차트 컴포넌트

### 🔍 다음 세션 에이전트를 위한 디버깅 가이드

#### 1단계: 데이터 추출 검증
```python
# 다음 코드로 현재 데이터 상태 확인
from upbit_auto_trading.ui.desktop.screens.strategy_management.components.mini_simulation import get_simulation_engine
from upbit_auto_trading.ui.desktop.screens.strategy_management.components.mini_simulation import DataSourceType

engine = get_simulation_engine(DataSourceType.EMBEDDED)
data = engine.load_market_data(limit=100)
print("데이터 샘플:")
print(data.head())
print(f"가격 범위: {data['close'].min()} ~ {data['close'].max()}")
```

#### 2단계: 시나리오별 데이터 검증
```python
# 시나리오별 데이터 필터링 확인
scenarios = ['상승 추세', '하락 추세', '급등', '급락', '횡보', 'MA 크로스']
for scenario in scenarios:
    filtered_data = engine.filter_by_scenario(data, scenario)
    print(f"{scenario}: {len(filtered_data)}개 데이터 포인트")
```

#### 3단계: 차트 데이터 최종 확인
```python
# 실제 차트에 전달되는 데이터 검증
from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.adapters import get_trigger_builder_adapter

adapter = get_trigger_builder_adapter()
result = adapter.run_trigger_simulation(
    trigger_data={'name': 'Test'}, 
    scenario='상승 추세',
    source_type='embedded'
)
print("차트 데이터:", result.get('chart_data', {}))
```

### 💡 예상 문제점들

1. **시나리오 필터링 로직 부정확**
   - `filter_by_scenario()` 메서드의 조건문 검토 필요
   - 기술적 지표 계산 오류 가능성

2. **랜덤 샘플링 편향**
   - 전체 데이터에서 무작위 추출이 시나리오 특성을 반영하지 못함
   - 시나리오별 사전 분류된 데이터셋 필요

3. **차트 렌더링 시점 문제**
   - 데이터 로딩과 차트 업데이트 간 타이밍 이슈
   - 비동기 처리 중 데이터 손실 가능성

### 🎯 해결 우선순위
1. **고급**: 시나리오별 사전 분류된 데이터셋 구축
2. **중급**: 필터링 로직 개선
3. **기본**: 데이터 검증 로그 추가

## 📱 StrategyMaker 재사용성 구현

### 현재 폴더 구조 문제
**문제**: `strategy_maker` 폴더가 복잡한 경로에 위치
**해결**: 공통 컴포넌트를 통한 간편한 접근

### 구현 예제
```python
# strategy_maker/strategy_maker_screen.py 예시
from ..components.mini_simulation import (
    get_simulation_engine, 
    DataSourceType,
    SimulationDataSourceManager
)
from ..components.strategy_preview_widget import StrategyPreviewWidget

class StrategyMakerScreen:
    def __init__(self):
        # 공통 미니 시뮬레이션 엔진 사용
        self.simulation_engine = get_simulation_engine(DataSourceType.EMBEDDED)
        
        # 미리 구현된 프리뷰 위젯 재사용
        self.preview_widget = StrategyPreviewWidget()
        
    def create_strategy_preview(self, strategy_config):
        """전략 미리보기 생성"""
        return self.preview_widget.generate_preview_chart(
            strategy_config=strategy_config,
            simulation_engine=self.simulation_engine
        )
```

### 재사용 가능한 컴포넌트들
- ✅ **미니 시뮬레이션 엔진**: 공통 시스템에서 바로 import
- ✅ **데이터 소스 관리자**: 모든 탭에서 동일한 인터페이스
- ✅ **차트 위젯**: `StrategyPreviewWidget` 기반 확장
- ✅ **기술적 지표**: 자동으로 모든 금융지표 사용 가능

---
**📅 업데이트**: 2025년 7월 28일
**🎯 대상**: GitHub 사용자 및 다음 세션 에이전트
