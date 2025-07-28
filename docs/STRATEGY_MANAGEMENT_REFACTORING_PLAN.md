# 전략 관리 시스템 리팩토링 계획

## 🎯 목표: 에이전트가 쉽게 이해할 수 있는 명확한 구조

### 🚫 현재 문제점
1. **복잡한 경로**: trigger_builder/components/adapters/mini_simulation_adapter.py
2. **Junction 링크**: Git Clone 시 작동 안함
3. **분산된 로직**: 비슷한 기능이 여러 곳에 흩어짐
4. **혼란스러운 명명**: mini_simulation vs engines vs adapters

### ✅ 새로운 구조 (리팩토링 목표)

```
📁 strategy_management/
├── 📊 shared_simulation/              # 공통 시뮬레이션 (명확한 이름)
│   ├── engines/                       # 시뮬레이션 엔진들
│   │   ├── embedded_engine.py         # 내장 데이터 엔진
│   │   ├── realdata_engine.py         # 실제 DB 데이터 엔진
│   │   ├── robust_engine.py           # 견고한 엔진
│   │   └── engine_factory.py          # 팩토리 패턴
│   ├── data_sources/                  # 데이터 소스 관리
│   │   ├── market_data_loader.py      # 시장 데이터 로더
│   │   ├── sample_data_generator.py   # 샘플 데이터 생성기
│   │   └── data_validator.py          # 데이터 검증
│   ├── charts/                        # 차트 컴포넌트
│   │   ├── mini_chart_widget.py       # 미니차트 위젯
│   │   └── plot_utils.py              # 플롯 유틸리티
│   └── __init__.py                    # 통합 인터페이스
│
├── 📈 trigger_builder/                # 트리거 빌더 (단순화)
│   ├── screens/
│   │   └── trigger_builder_screen.py # 메인 화면
│   ├── components/
│   │   ├── trigger_list.py            # 트리거 목록
│   │   ├── trigger_editor.py          # 트리거 편집기
│   │   └── simulation_panel.py        # 시뮬레이션 패널
│   └── __init__.py
│
├── 📊 strategy_maker/                 # 전략 메이커 (통합)
│   ├── screens/
│   │   └── strategy_maker_screen.py  # 메인 화면
│   ├── components/
│   │   ├── strategy_editor.py         # 전략 편집기
│   │   ├── backtest_panel.py          # 백테스트 패널
│   │   └── preview_chart.py           # 미리보기 차트
│   └── __init__.py
│
└── 📋 components/                     # 전역 공통 컴포넌트
    ├── condition_builder.py           # 조건 빌더
    ├── variable_selector.py           # 변수 선택기
    └── data_source_selector.py        # 데이터 소스 선택기
```

### 🔄 리팩토링 단계

#### Phase A: 공통 시뮬레이션 통합
1. `shared_simulation/` 디렉토리 생성
2. 모든 엔진을 한 곳에 통합 (Junction 링크 제거)
3. 명확한 팩토리 패턴 구현

#### Phase B: 각 모듈 단순화
1. TriggerBuilder를 `trigger_builder/`에 깔끔하게 정리
2. StrategyMaker를 `strategy_maker/`에 완전 구현
3. 중복 코드 제거

#### Phase C: Git 호환성 확보
1. Junction 링크 완전 제거
2. 상대 import 경로 정리
3. 테스트 및 검증

### 💡 에이전트를 위한 명확한 지침

다음 대화 세션에서 에이전트에게 이렇게 요청하면 됩니다:

```
"strategy_management 폴더를 보면:
1. shared_simulation/: 모든 시뮬레이션 로직이 여기 있음
2. trigger_builder/: 트리거 관련 UI와 로직
3. strategy_maker/: 전략 관련 UI와 로직
4. components/: 공통 UI 컴포넌트

문제가 있으면 shared_simulation/engines/를 먼저 확인하고,
각 모듈의 __init__.py에서 import 경로를 확인하세요."
```

### 🚀 즉시 실행 가능한 작업

1. **shared_simulation 디렉토리 생성**
2. **기존 엔진들을 한 곳에 복사**
3. **새로운 import 경로로 테스트**
4. **성공하면 기존 복잡한 구조 제거**
