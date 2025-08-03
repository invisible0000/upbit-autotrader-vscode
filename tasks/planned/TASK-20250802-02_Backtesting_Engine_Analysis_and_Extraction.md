# TASK-20250802-02: 백테스팅 엔진 분석 및 추출

## 📋 작업 개요
**목표**: shared_simulation/engines의 백테스팅 로직을 순수 비즈니스 로직으로 분석 및 추출
**우선순위**: CRITICAL 
**예상 소요시간**: 4-6시간
**전제조건**: TASK-20250802-01 완료

## 🎯 작업 목표
- [ ] 현재 백테스팅 엔진들의 UI 의존성 정확한 파악
- [ ] 순수 비즈니스 로직과 UI 로직 분리 방안 설계
- [ ] 데이터 처리 로직과 계산 로직 분리
- [ ] 새로운 아키텍처 인터페이스 설계

## 📊 분석 대상 파일

### 주요 엔진 파일들
1. **simulation_engines.py** (274 lines)
   - BaseSimulationEngine, EmbeddedSimulationEngine
   - RealDataSimulationEngine, RobustSimulationEngine
   - UI 독립적 가능성: 80%

2. **robust_simulation_engine.py** (450+ lines)
   - RobustSimulationEngine, EnhancedRealDataSimulationEngine
   - 복잡한 데이터 처리 로직 포함
   - UI 독립적 가능성: 90%

3. **real_data_simulation.py** (430+ lines)
   - 실제 DB 데이터 처리
   - 시나리오별 데이터 추출
   - UI 독립적 가능성: 95%

4. **embedded_simulation_engine.py** (390+ lines)
   - 내장 시뮬레이션 데이터셋
   - 순수 계산 로직
   - UI 독립적 가능성: 98%

## 🔍 세부 분석 작업

### Step 1: UI 의존성 분석
```bash
# PyQt6 및 UI 관련 import 찾기
grep -n "from PyQt6\|import PyQt6\|from.*ui\|import.*ui" \
    upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/engines/*.py

# 외부 모듈 의존성 분석
grep -n "^from\|^import" \
    upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/engines/*.py

# 클래스 및 함수 정의 분석
grep -n "^class\|^def" \
    upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/engines/*.py
```

### Step 2: 비즈니스 로직 분류
각 파일별로 다음과 같이 분류:

#### 순수 비즈니스 로직 (분리 대상)
- 데이터 계산 함수 (`calculate_*`)
- 시뮬레이션 엔진 클래스 (`*Engine`)
- 데이터 변환 로직
- 기술적 지표 계산

#### UI 연결 로직 (분리 후 서비스 계층으로)
- 데이터 포맷팅
- 에러 메시지 처리
- 진행 상황 표시

#### 설정 및 초기화 (공통 로직)
- DB 경로 설정
- 로깅 설정
- 기본값 정의

### Step 3: 새로운 구조 설계
```
business_logic/backtester/
├── engines/
│   ├── __init__.py
│   ├── base_engine.py              # BaseSimulationEngine → BaseBacktestEngine
│   ├── data_engine.py              # 데이터 로딩/변환 로직
│   ├── calculation_engine.py       # 기술적 지표 계산
│   └── scenario_engine.py          # 시나리오 생성 로직
│
├── models/
│   ├── __init__.py
│   ├── market_data.py              # 시장 데이터 모델
│   ├── simulation_result.py        # 시뮬레이션 결과 모델
│   └── backtest_config.py          # 백테스트 설정 모델
│
└── services/
    ├── __init__.py
    ├── backtesting_service.py      # UI와 엔진 연결
    └── data_validation_service.py  # 데이터 검증 서비스
```

## 🛠️ 실행 단계

### Phase 2-1: 파일별 상세 분석
각 엔진 파일에 대해:
1. 함수별 UI 의존성 체크
2. 입력/출력 인터페이스 정의
3. 분리 가능한 함수 목록 작성
4. 분리 불가능한 함수 사유 분석

### Phase 2-2: 인터페이스 설계
```python
# 예상 인터페이스 (추상 클래스)
class BaseBacktestEngine(ABC):
    @abstractmethod
    def load_market_data(self, config: BacktestConfig) -> MarketData:
        pass
    
    @abstractmethod
    def calculate_indicators(self, data: MarketData) -> IndicatorData:
        pass
    
    @abstractmethod
    def run_simulation(self, data: MarketData, strategy: Strategy) -> SimulationResult:
        pass
```

### Phase 2-3: 의존성 매핑
현재 의존성 → 새로운 의존성 매핑:
- `shared_simulation.engines` → `business_logic.backtester.engines`
- UI 직접 호출 → 서비스 계층 경유
- 전역 변수 → 설정 객체

## ✅ 완료 기준
- [ ] 4개 주요 엔진 파일 완전 분석 완료
- [ ] UI 의존성 보고서 작성 완료
- [ ] 새로운 인터페이스 설계 문서 완료
- [ ] 분리 불가능한 로직 명시 및 사유 설명
- [ ] 데이터 플로우 다이어그램 작성

## 📈 성공 지표
- **분석 완료도**: 100% (4개 파일 모두)
- **UI 의존성 식별**: 모든 PyQt6 의존성 파악
- **비즈니스 로직 분류**: 90% 이상 정확한 분류
- **인터페이스 설계**: 명확한 입력/출력 정의

## 🚨 주의사항
1. **기존 기능 보존**: 분석 중 기능 변경 금지
2. **의존성 순환**: 새로운 구조에서 순환 참조 방지
3. **성능 고려**: 로직 분리로 인한 성능 저하 최소화

## 🔗 연관 TASK
- **이전**: TASK-20250802-01 (사전 준비)
- **다음**: TASK-20250802-03 (백테스팅 엔진 구현)

## 📝 분석 결과 산출물
1. `analysis_report_backtesting_engines.md` - 상세 분석 보고서
2. `new_architecture_design.py` - 새로운 아키텍처 설계
3. `dependency_mapping.json` - 의존성 매핑 정보
4. `ui_dependencies_list.txt` - UI 의존성 목록

---
**작업자**: GitHub Copilot  
**생성일**: 2025년 8월 2일
**상태**: 계획됨
