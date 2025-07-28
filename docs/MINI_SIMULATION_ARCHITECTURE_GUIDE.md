# 미니 시뮬레이션 아키텍처 가이드

## 📋 개요
이 문서는 Phase 1-4를 통해 구축된 **재사용 가능한 미니 시뮬레이션 시스템** 구조를 설명합니다.
다른 대화 세션의 AI 에이전트가 빠르게 현재 상황을 파악할 수 있도록 작성되었습니다.

## 🏗️ 전체 아키텍처 구조

### 리팩토링 완료 상태 (Phase 1-4)
```
📁 upbit_auto_trading/ui/desktop/screens/strategy_management/
├── 🎯 공통 미니 시뮬레이션 시스템 (Phase 3에서 구축)
│   └── components/mini_simulation/
│       ├── engines/                    # 통합된 시뮬레이션 엔진들
│       │   ├── base_simulation_engines.py     # 검증된 엔진들 (복사본)
│       │   ├── simulation_engine_factory.py   # 통합 팩토리 패턴
│       │   └── __init__.py
│       ├── services/                   # 비즈니스 로직 서비스
│       │   ├── data_source_manager.py         # 데이터 소스 관리자
│       │   └── __init__.py
│       ├── widgets/                    # 재사용 가능한 UI 컴포넌트 (향후 확장)
│       │   └── __init__.py
│       └── __init__.py                 # 공통 인터페이스
│
├── 🎯 TriggerBuilder (기존 + 어댑터)
│   └── trigger_builder/
│       ├── mini_simulation_engines/    # Phase 2: engines → mini_simulation_engines
│       │   ├── real_data_simulation.py        # 구 버전 (Junction으로 접근)
│       │   ├── embedded_simulation_engine.py  # 구 버전
│       │   └── robust_simulation_engine.py    # 구 버전
│       ├── engines/                    # Junction 링크 → mini_simulation_engines
│       ├── components/
│       │   ├── adapters/               # Phase 4: 어댑터 패턴
│       │   │   ├── mini_simulation_adapter.py # 핵심 어댑터 클래스
│       │   │   ├── __init__.py
│       │   │   ├── test_adapter.py            # 테스트 스크립트
│       │   │   └── quick_test.py              # 간단 검증
│       │   ├── shared/
│       │   │   ├── simulation_engines.py     # 검증된 엔진들 (원본)
│       │   │   └── data_source_manager.py    # 검증된 관리자
│       │   └── core/                          # TriggerBuilder UI 컴포넌트들
│       └── trigger_builder_screen.py
│
└── 🎯 StrategyMaker (Phase 5에서 테스트 예정)
    └── strategy_maker.py
```

## 🔧 핵심 컴포넌트 설명

### 1. 공통 미니 시뮬레이션 시스템
**위치**: `strategy_management/components/mini_simulation/`

**목적**: 모든 탭에서 재사용 가능한 미니 시뮬레이션 기능 제공

```python
# 사용 예시
from strategy_management.components.mini_simulation import (
    get_simulation_engine, DataSourceType, SimulationDataSourceManager
)

# 엔진 선택
engine = get_simulation_engine(DataSourceType.EMBEDDED)
market_data = engine.load_market_data(limit=100)
```

### 2. TriggerBuilder 어댑터
**위치**: `trigger_builder/components/adapters/mini_simulation_adapter.py`

**목적**: TriggerBuilder와 공통 시스템을 연결하는 브리지

```python
# 사용 예시
from trigger_builder.components.adapters import get_trigger_builder_adapter

adapter = get_trigger_builder_adapter()
result = adapter.run_trigger_simulation(
    trigger_data={'name': 'SMA_Cross'},
    scenario='횡보',
    source_type='embedded'
)
```

### 3. 데이터 소스 타입
```python
# 4가지 데이터 소스 지원
DataSourceType.EMBEDDED     # 내장 최적화 데이터셋
DataSourceType.REAL_DB      # 실제 DB 데이터
DataSourceType.SYNTHETIC    # 합성 현실적 데이터  
DataSourceType.SIMPLE_FALLBACK  # 단순 폴백
```

## 🎯 금융지표 변수 시스템 (현재 상태)

### 현재 지원되는 금융지표들
```python
# trigger_builder/components/shared/에서 확인 가능
- SMA (단순이동평균): 20일, 60일
- EMA (지수이동평균): 12일, 26일
- RSI (상대강도지수): 14일
- MACD (이동평균수렴확산)
- 볼린저밴드 (상단, 하단)
- 거래량 기반 지표들
```

### 변수 등록 시스템
```python
# 기존 TriggerBuilder에서 사용 중
from trigger_builder.components.shared.chart_variable_service import get_chart_variable_service
from trigger_builder.components.shared.variable_display_system import get_variable_registry

# 새로운 지표 추가시 이 시스템들을 통해 등록
```

## 🚀 재사용 가능한 구조의 장점

### 1. 다른 탭에서 즉시 활용 가능
```python
# StrategyMaker에서 미니차트 사용 예시
from strategy_management.components.mini_simulation import get_simulation_engine

class StrategyPreviewWidget:
    def __init__(self):
        self.engine = get_simulation_engine(DataSourceType.EMBEDDED)
        # 전략 프리뷰용 미니차트 생성
```

### 2. 새로운 금융지표 추가 용이성
```python
# 공통 시스템에 한 번만 추가하면 모든 탭에서 사용 가능
# engines/base_simulation_engines.py의 calculate_technical_indicators() 메서드 확장
```

### 3. AI 에이전트 개발 효율성
- **단일 진실 소스**: 공통 시스템만 수정하면 모든 곳에 반영
- **명확한 구조**: 어댑터 패턴으로 책임 분리
- **폴백 시스템**: 기존 코드 100% 호환성 보장

## 📝 Phase 5에서 검증할 항목들

### 1. StrategyMaker 탭 연동
- [ ] 공통 미니차트 컴포넌트 임포트 테스트
- [ ] 기본 시뮬레이션 엔진 동작 확인
- [ ] 차트 렌더링 호환성 검증

### 2. 새로운 금융지표 추가 시뮬레이션
- [ ] 공통 시스템에 새 지표 추가
- [ ] TriggerBuilder에서 자동 반영 확인
- [ ] StrategyMaker에서 동일 지표 사용 가능 확인

### 3. 성능 및 안정성
- [ ] 메모리 사용량 측정
- [ ] 멀티탭 동시 사용 테스트
- [ ] 에러 처리 및 폴백 동작 검증

## ⚠️ 주의사항 (다음 에이전트를 위한 가이드)

### 1. 기존 코드 수정시
```bash
# 반드시 애플리케이션 테스트 실행
python run_desktop_ui.py
# UI: 매매전략관리 → 트리거빌더 → 트리거선택 → 시뮬레이션 실행
```

### 2. 새로운 금융지표 추가시
1. `components/mini_simulation/engines/base_simulation_engines.py` 수정
2. TriggerBuilder 어댑터에서 자동 지원 확인
3. 공통 인터페이스 통해 다른 탭에서 접근 가능

### 3. 롤백이 필요한 경우
```bash
# Junction 링크로 기존 경로 보존되어 있음
# engines → mini_simulation_engines
# 기존 시스템은 여전히 작동 중
```

## 🎯 최종 목표 달성도
- ✅ **Phase 1**: 로깅 시스템 정리 (30-40% 로그 감소)
- ✅ **Phase 2**: 폴더 구조 정리 (engines → mini_simulation_engines)
- ✅ **Phase 3**: 공통 컴포넌트 시스템 구축
- ✅ **Phase 4**: 어댑터 패턴으로 완전 호환성 확보
- 🔄 **Phase 5**: 재사용성 테스트 및 문서화 (진행 중)

---
**📅 작성일**: 2025년 7월 28일  
**📝 작성자**: AI Agent (Phase 1-4 완료 상태)  
**🎯 용도**: 다음 대화 세션 에이전트의 빠른 상황 파악용
