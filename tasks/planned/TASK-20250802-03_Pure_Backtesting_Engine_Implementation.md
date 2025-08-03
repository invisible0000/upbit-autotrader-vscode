# TASK-20250802-03: 순수 백테스팅 엔진 구현

## 📋 작업 개요  
**목표**: UI 의존성이 제거된 순수 백테스팅 엔진을 business_logic/backtester/에 구현
**우선순위**: CRITICAL
**예상 소요시간**: 6-8시간
**전제조건**: TASK-20250802-02 완료

## 🎯 작업 목표
- [ ] 순수 비즈니스 로직만 포함된 백테스팅 엔진 구현
- [ ] UI 의존성 완전 제거 (PyQt6 import 0개)
- [ ] 명확한 입력/출력 인터페이스 정의
- [ ] 단위 테스트 가능한 구조 구현

## 📁 구현할 파일 구조

```
business_logic/backtester/
├── __init__.py
├── engines/
│   ├── __init__.py
│   ├── base_engine.py              # 추상 백테스트 엔진
│   ├── market_data_engine.py       # 시장 데이터 처리
│   ├── indicator_engine.py         # 기술적 지표 계산  
│   ├── simulation_engine.py        # 시뮬레이션 실행
│   └── scenario_engine.py          # 시나리오 생성
│
├── models/
│   ├── __init__.py
│   ├── market_data.py              # 시장 데이터 모델
│   ├── backtest_config.py          # 백테스트 설정
│   ├── simulation_result.py        # 시뮬레이션 결과
│   └── indicator_data.py           # 지표 데이터 모델
│
└── services/
    ├── __init__.py
    ├── backtesting_service.py      # 메인 백테스팅 서비스
    └── data_validation_service.py  # 데이터 검증 서비스
```

## 🛠️ 세부 구현 단계

### Step 1: 기본 모델 클래스 구현

#### 1.1 MarketData 모델 (models/market_data.py)
```python
@dataclass
class MarketData:
    """시장 데이터 모델 - UI 독립적"""
    timestamps: List[datetime]
    open_prices: List[float]
    high_prices: List[float] 
    low_prices: List[float]
    close_prices: List[float]
    volumes: List[float]
    
    def to_dataframe(self) -> pd.DataFrame:
        """pandas DataFrame으로 변환"""
        
    def validate(self) -> bool:
        """데이터 유효성 검증"""
```

#### 1.2 BacktestConfig 모델 (models/backtest_config.py)
```python
@dataclass
class BacktestConfig:
    """백테스트 설정 - UI 독립적"""
    data_source: str
    scenario: str
    data_length: int
    indicators: List[str]
    parameters: Dict[str, Any]
    
    def validate(self) -> bool:
        """설정 유효성 검증"""
```

### Step 2: 핵심 엔진 구현

#### 2.1 BaseEngine (engines/base_engine.py)
```python
from abc import ABC, abstractmethod

class BaseBacktestEngine(ABC):
    """백테스트 엔진 추상 클래스 - UI 완전 독립"""
    
    @abstractmethod
    def load_data(self, config: BacktestConfig) -> MarketData:
        """데이터 로딩"""
        pass
    
    @abstractmethod
    def calculate_indicators(self, data: MarketData) -> IndicatorData:
        """기술적 지표 계산"""  
        pass
    
    @abstractmethod
    def run_simulation(self, data: MarketData, strategy: Dict) -> SimulationResult:
        """시뮬레이션 실행"""
        pass
```

#### 2.2 MarketDataEngine (engines/market_data_engine.py)  
현재 `RealDataSimulationEngine.load_market_data()` 로직을 UI 의존성 제거하여 이전:
- SQLite3 DB 연결 및 데이터 로딩
- 시나리오별 데이터 필터링
- 폴백 데이터 생성

#### 2.3 IndicatorEngine (engines/indicator_engine.py)
현재 각 엔진의 `calculate_*` 함수들을 통합:
- SMA, EMA, RSI, MACD 계산
- 기술적 지표 공통 인터페이스
- 커스텀 파라미터 지원

### Step 3: 서비스 계층 구현

#### 3.1 BacktestingService (services/backtesting_service.py)
```python
class BacktestingService:
    """백테스팅 메인 서비스 - UI와 비즈니스 로직 연결점"""
    
    def __init__(self):
        self.data_engine = MarketDataEngine()
        self.indicator_engine = IndicatorEngine()
        self.simulation_engine = SimulationEngine()
    
    def run_backtest(self, config: BacktestConfig) -> SimulationResult:
        """백테스트 실행 - UI에서 호출하는 메인 인터페이스"""
        # 1. 데이터 로딩
        market_data = self.data_engine.load_data(config)
        
        # 2. 지표 계산
        indicators = self.indicator_engine.calculate_indicators(market_data)
        
        # 3. 시뮬레이션 실행
        result = self.simulation_engine.run_simulation(market_data, indicators, config)
        
        return result
```

## 🧪 코드 마이그레이션 전략

### 현재 → 새로운 구조 매핑
1. **RobustSimulationEngine** → **MarketDataEngine** + **SimulationEngine**
2. **calculate_technical_indicators()** → **IndicatorEngine.calculate_indicators()**
3. **get_scenario_data()** → **MarketDataEngine.load_scenario_data()**
4. **EmbeddedSimulationDataEngine** → **ScenarioEngine**

### UI 의존성 제거 방법
```python
# 기존 (UI 의존적)
def load_market_data(self, limit: int = 100) -> pd.DataFrame:
    try:
        # UI 로깅, UI 상태 업데이트 등
        logging.info("✅ 데이터 로드 완료")  # UI 로깅
        return data
    except Exception as e:
        QMessageBox.warning(self, "오류", str(e))  # UI 의존성

# 새로운 (UI 독립적)  
def load_market_data(self, config: BacktestConfig) -> MarketData:
    try:
        # 순수 비즈니스 로직만
        return MarketData(...)
    except Exception as e:
        # 예외는 상위로 전파, UI에서 처리
        raise BacktestDataError(f"데이터 로드 실패: {e}")
```

## ✅ 완료 기준
- [ ] 모든 백테스팅 엔진 파일 구현 완료 (7개 파일)
- [ ] PyQt6 import 0개 달성
- [ ] 기존 기능 100% 보존 (기능 회귀 없음)
- [ ] 명확한 입력/출력 인터페이스 정의
- [ ] 에러 처리 및 예외 전파 체계 구축

## 📈 성공 지표
- **UI 독립성**: PyQt6 의존성 0개
- **기능 동등성**: 기존 엔진과 100% 동일한 결과
- **인터페이스 명확성**: 모든 메서드에 명확한 타입 힌트
- **예외 처리**: 적절한 커스텀 예외 정의

## 🚨 주의사항
1. **기능 동등성**: 기존 시뮬레이션 결과와 동일해야 함
2. **성능 유지**: 로직 분리로 인한 성능 저하 최소화
3. **메모리 효율**: 대용량 데이터 처리 시 메모리 사용량 고려
4. **스레드 안전성**: 멀티스레드 환경에서 안전한 구현

## 🔗 연관 TASK
- **이전**: TASK-20250802-02 (분석 및 추출)
- **다음**: TASK-20250802-04 (단위 테스트 작성)

## 📝 산출물
1. **구현된 백테스팅 엔진**: 7개 파일 완전 구현
2. **인터페이스 문서**: API 문서 및 사용 예제
3. **마이그레이션 가이드**: 기존 코드에서 새 코드로 전환 방법
4. **성능 벤치마크**: 기존 대비 성능 비교 결과

---
**작업자**: GitHub Copilot
**생성일**: 2025년 8월 2일  
**상태**: 계획됨
