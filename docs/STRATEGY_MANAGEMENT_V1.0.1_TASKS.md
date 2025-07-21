# 매매 전략 관리 V1.0.1 개발 태스크 문서

## 📋 개요

**🚨 중요한 구조 변경**: 기존 '전략'을 **진입 전략(Entry Strategy)**과 **관리 전략(Management Strategy)**으로 역할 분리

### 🎯 주요 목표
1. **역할 분리**: 진입 신호 생성 vs 포지션 관리 로직 명확히 구분
2. **조합 시스템**: 1개 진입 전략 + 0~N개 관리 전략 조합
3. **UI 구조 개선**: 역할 기반 탭 분리 (진입/관리/조합)
4. **백테스팅 엔진 개선**: 포지션 상태에 따른 전략 역할 전환
5. **AI 친화적 구조**: LLM 모델이 감당 가능한 수준의 코드 복잡도 유지

## 🔄 전략 역할 분리 명세

### 📈 진입 전략 (Entry Strategy)
**역할**: 포지션이 없는 상태에서 최초 진입 신호를 생성
**조건**: 현재 포지션이 없을 때만 활성화
**출력**: `BUY`, `SELL`, `HOLD` 신호

**진입 전략 예시:**
1. **이동평균 교차**: 골든크로스/데드크로스 신호
2. **RSI**: 과매수/과매도 구간 돌파 신호  
3. **볼린저 밴드**: 밴드 터치 후 반전 신호
4. **변동성 돌파**: 래리 윌리엄스 돌파 신호
5. **MACD**: MACD 라인과 시그널 라인 교차
6. **스토캐스틱**: %K와 %D 라인 교차 및 과매수/과매도

### 🛡️ 관리 전략 (Management Strategy)
**역할**: 이미 진입한 포지션의 리스크 관리 및 수익 극대화
**조건**: 활성 포지션이 존재할 때만 활성화
**출력**: `ADD_BUY`, `ADD_SELL`, `CLOSE_POSITION`, `UPDATE_STOP` 신호

**관리 전략 예시:**
1. **물타기 (Averaging Down)**: 하락 시 추가 매수로 평단가 낮추기
2. **불타기 (Pyramiding)**: 상승 시 추가 매수로 수익 극대화
3. **트레일링 스탑**: 동적 손절가 조정으로 수익 보호
4. **고정 익절/손절**: 진입가 대비 고정 % 도달 시 청산
5. **부분 청산**: 단계별 익절로 리스크 감소
6. **시간 기반 청산**: 최대 보유 기간 도달 시 강제 청산

## 🏗️ 새로운 시스템 구조

### 전략 조합 시스템
```
완성된 매매 시스템 = 진입 전략(1개) + 관리 전략(0~N개)

예시:
- RSI 과매도 진입 + 물타기 + 트레일링 스탑
- 이동평균 교차 진입 + 고정 익절/손절 + 부분 청산
- 변동성 돌파 진입 + 불타기 + 시간 기반 청산
```

### 백테스팅 엔진 상태 전환
```
[진입 대기] → [포지션 진입] → [포지션 관리] → [포지션 종료] → [진입 대기]
     ↓              ↓              ↓              ↓
  진입전략만       진입전략        관리전략만       전략비활성화
   활성화         신호발생         활성화          (청산완료)
```

## 🚀 개발 계획

### Phase 1: 전략 역할 분리 및 UI 재구성 (4-5일)

#### Task 1.1: 전략 클래스 구조 재설계 ✅ **[COMPLETED - 2025-07-21]**
**목표**: 진입 전략과 관리 전략의 명확한 인터페이스 분리

**✅ 완료된 구현:**
```python
# ✅ 기본 전략 인터페이스 완성
class BaseStrategy(ABC):
    @abstractmethod
    def get_strategy_role(self) -> StrategyRole:
        """전략 역할 반환: 'entry' | 'management'"""
        pass

# ✅ 진입 전략 기본 클래스 완성  
class EntryStrategy(BaseStrategy):
    def get_strategy_role(self) -> StrategyRole:
        return StrategyRole.ENTRY
    
    @abstractmethod
    def generate_entry_signal(self, market_data, position_status) -> TradingSignal:
        """진입 신호 생성: 'BUY' | 'SELL' | 'HOLD'"""
        pass

# ✅ 관리 전략 기본 클래스 완성
class ManagementStrategy(BaseStrategy):
    def get_strategy_role(self) -> StrategyRole:
        return StrategyRole.MANAGEMENT
    
    @abstractmethod
    def generate_management_signal(self, market_data, position_info) -> TradingSignal:
        """
        관리 신호 생성: 'ADD_BUY' | 'ADD_SELL' | 'CLOSE_POSITION' | 'UPDATE_STOP' | 'HOLD'
        """
        pass
```

**✅ 검증 결과:**
- **개별 전략 테스트**: 모든 진입/관리 전략 정상 작동 확인
- **신호 생성**: BUY/SELL/HOLD (진입) vs ADD_BUY/CLOSE_POSITION (관리) 신호 분리 완료
- **역할 분리**: 포지션 상태에 따른 전략 활성화 조건 구현 완료
- **파일 위치**: `upbit_auto_trading/business_logic/strategy/role_based_strategy.py`

#### Task 1.2: 진입 전략 구현 (6개) ✅ **[COMPLETED - 2025-07-21]**
**목표**: 현재 4개 + 2개 추가로 총 6개 진입 전략 구현

**✅ 구현 완료된 진입 전략 목록:**
```python
# 1. ✅ MovingAverageCrossEntry - 이동평균 교차 진입 전략
parameters = {
    "short_period": 5,      # 단기 이평선 기간
    "long_period": 20,      # 장기 이평선 기간
    "ma_type": "SMA"        # "SMA" | "EMA"
}

# 2. ✅ RSIEntry - RSI 과매수/과매도 진입 전략  
parameters = {
    "rsi_period": 14,       # RSI 계산 기간
    "oversold": 30,         # 과매도 기준
    "overbought": 70        # 과매수 기준
}

# 3. ✅ BollingerBandsEntry - 볼린저 밴드 진입 전략
parameters = {
    "period": 20,           # 중심선 기간
    "std_multiplier": 2.0,  # 표준편차 승수
    "entry_type": "reversal" # "reversal" | "breakout"
}

# 4. ✅ VolatilityBreakoutEntry - 변동성 돌파 진입 전략
parameters = {
    "lookback_period": 1,   # 변동폭 계산 기간
    "k_value": 0.5,         # 돌파 계수
    "close_on_day_end": True # 당일 종가 청산 여부
}

# 5. ✅ MACDEntry - MACD 진입 전략
parameters = {
    "fast_period": 12,      # 빠른 EMA 기간
    "slow_period": 26,      # 느린 EMA 기간
    "signal_period": 9,     # 시그널 라인 기간
    "histogram_threshold": 0 # 히스토그램 임계값
}

# 6. ✅ StochasticEntry - 스토캐스틱 진입 전략
parameters = {
    "k_period": 14,         # %K 기간
    "d_period": 3,          # %D 기간
    "oversold": 20,         # 과매도 기준
    "overbought": 80        # 과매수 기준
}
```

**✅ 검증 결과:**
- **신호 생성 테스트**: 모든 진입 전략이 BUY/SELL/HOLD 신호 정상 생성
- **파라미터 검증**: 각 전략별 기본값 및 유효성 검사 완료
- **지표 요구사항**: 필요한 기술적 지표 목록 정의 완료
- **실제 사용 시나리오**: 제공된 지표 문서 기반 현실적 매매 로직 구현

#### Task 1.3: 관리 전략 구현 (6개) ✅ **[COMPLETED - 2025-07-21]**
**목표**: 포지션 관리를 위한 6개 관리 전략 구현

**✅ 구현 완료된 관리 전략 목록:**
```python
# 1. ✅ AveragingDownManagement - 물타기 관리 전략
parameters = {
    "trigger_drop_percent": 5.0,          # 추가 매수 트리거 (%)
    "max_additional_buys": 3,             # 최대 추가 매수 횟수
    "additional_quantity_ratio": 1.0,     # 추가 매수 수량 비율
    "stop_loss_percent": -30.0            # 절대 손절선 (%)
}

# 2. ✅ PyramidingManagement - 불타기 관리 전략
parameters = {
    "trigger_rise_percent": 3.0,          # 추가 매수 트리거 (%)
    "max_additional_buys": 2,             # 최대 추가 매수 횟수
    "quantity_decrease_ratio": 0.8,       # 수량 감소 비율
    "profit_protection": True             # 손익분기점 보호
}

# 3. ✅ TrailingStopManagement - 트레일링 스탑 관리 전략
parameters = {
    "trailing_distance": 5.0,            # 추적 거리 (%)
    "activation_profit": 3.0,            # 활성화 최소 수익률 (%)
    "stop_type": "percentage"            # "percentage" | "atr"
}

# 4. ✅ FixedTargetManagement - 고정 익절/손절 관리 전략
parameters = {
    "profit_target": 10.0,               # 익절 목표 (%)
    "stop_loss": 5.0,                    # 손절 기준 (%)
    "partial_profit_enabled": False      # 부분 익절 사용 여부
}

# 5. ✅ PartialExitManagement - 부분 청산 관리 전략
parameters = {
    "profit_levels": [5.0, 10.0, 15.0],  # 익절 단계 (%)
    "exit_ratios": [0.3, 0.3, 0.4],      # 각 단계별 청산 비율
    "trailing_after_partial": True       # 부분 청산 후 트레일링 적용
}

# 6. ✅ TimeBasedExitManagement - 시간 기반 청산 관리 전략
parameters = {
    "max_holding_hours": 24,             # 최대 보유 시간
    "force_exit_on_loss": True,          # 손실 시에도 강제 청산
    "exit_market_close": True            # 장 마감 전 청산
}
```

**✅ 검증 결과:**
- **물타기 테스트**: -10% 하락 시 추가매수 신호(ADD_BUY) 정상 생성 확인
- **신호 타입**: ADD_BUY/ADD_SELL/CLOSE_POSITION/UPDATE_STOP/HOLD 분리 완료
- **포지션 메트릭**: 미실현 손익, 보유시간 등 계산 로직 구현 완료
- **실제 사용 사례**: 제공된 매매 시나리오 기반 현실적 관리 로직 구현

### Phase 2: UI 구조 재설계 (4-5일)

#### Task 2.1: 전략 관리 화면 탭 구조 변경 ✅ **[COMPLETED - 2025-07-21]**
**목표**: 역할 기반 3탭 구조로 변경

**✅ 완료된 구현:**
```python
# ✅ 3탭 구조 완성
class StrategyManagementScreen(QWidget):
    def init_ui(self):
        self.tab_widget = QTabWidget()
        
        # 1) 📈 진입 전략 탭
        entry_tab = self.create_entry_strategy_tab()
        self.tab_widget.addTab(entry_tab, "📈 진입 전략")
        
        # 2) 🛡️ 관리 전략 탭  
        management_tab = self.create_management_strategy_tab()
        self.tab_widget.addTab(management_tab, "🛡️ 관리 전략")
        
        # 3) 🔗 전략 조합 탭
        combination_tab = self.create_strategy_combination_tab()
        self.tab_widget.addTab(combination_tab, "🔗 전략 조합")

# ✅ 전략 조합 탭 3분할 레이아웃 완성
def create_strategy_combination_tab(self):
    # 좌측: 조합 목록 (25%)
    # 중앙: 조합 에디터 (50%) 
    # 우측: 백테스트 결과 (25%)
    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.setSizes([250, 500, 250])
```

**✅ 검증 결과:**
- **UI 테스트**: 3탭 구조 정상 로딩 및 전환 확인
- **데이터 로딩**: 진입 6개, 관리 6개, 조합 3개 정상 표시
- **레이아웃**: 조합 탭 3분할 패널 비율 정상 적용
- **이벤트**: 모든 버튼 클릭 이벤트 정상 작동
- **파일 위치**: `upbit_auto_trading/ui/desktop/strategy_management_screen.py`

#### Task 2.2: 전략 조합 데이터 모델 ✅ **[COMPLETED - 2025-07-21]**
**목표**: 1개 진입 전략 + N개 관리 전략 조합을 위한 데이터 구조

**✅ 완료된 구현:**
```python
# ✅ 전략 조합 데이터 클래스 완성
@dataclass
class StrategyCombination:
    combination_id: str
    name: str
    description: str
    entry_strategy: StrategyConfig              # 필수 1개
    management_strategies: List[StrategyConfig] # 선택 0~5개
    execution_order: ExecutionOrderType
    conflict_resolution: ConflictResolutionType
    risk_limit: RiskLimit

# ✅ 조합 관리 클래스 완성
class CombinationManager:
    def create_combination(self, name, description, entry_strategy, management_strategies)
    def get_combination(self, combination_id)
    def update_combination(self, combination)
    def delete_combination(self, combination_id)
    def save_combinations(self) -> JSON 직렬화
    def load_combinations(self) -> JSON 역직렬화
```

**✅ 검증 결과:**
- **데이터 모델**: StrategyCombination 클래스 정상 작동
- **JSON 직렬화**: 저장/로딩 완벽 지원
- **유효성 검증**: 5개 관리 전략 제한, 우선순위 중복 방지
- **샘플 데이터**: 3개 실제 조합 생성 및 테스트 완료
- **UI 연동**: CombinationManager와 UI 정상 연동
- **파일 위치**: `upbit_auto_trading/business_logic/strategy/strategy_combination.py`

#### Task 2.3: UI-데이터 모델 연동 ✅ **[COMPLETED - 2025-07-21]**
**목표**: UI와 실제 데이터 모델 완전 연동

**✅ 완료된 구현:**
```python
# ✅ 실시간 UI 인터랙션
class StrategyManagementScreen:
    def __init__(self):
        self.combination_manager = CombinationManager("ui_strategy_combinations.json")
    
    # ✅ 체크박스 인터랙션
    def on_entry_selection_clicked(self, row, col):
        # 진입 전략 1개만 선택 제한
        
    def on_mgmt_selection_clicked(self, row, col):
        # 관리 전략 최대 5개 제한
        
    # ✅ 실시간 미리보기
    def preview_combination(self):
        # 선택된 전략 조합 실시간 표시
        
    # ✅ 조합 CRUD 연동
    def save_combination(self):   # 생성
    def delete_combination(self):  # 삭제
    def on_combination_selected(self): # 조회
```

**✅ 검증 결과:**
- **체크박스 제한**: 진입 1개, 관리 최대 5개 정상 제한
- **실시간 미리보기**: 선택 변경 시 즉시 조합 구성 표시
- **조합 관리**: 생성/조회/삭제 정상 작동
- **데이터 영속성**: JSON 파일 자동 저장/로딩
- **이벤트 처리**: 모든 사용자 인터랙션 정상 처리

**새로운 탭 구조:**
```python
class StrategyManagementScreen(QWidget):
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 상단 툴바 (검색/필터)
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # 3탭 구조
        self.tab_widget = QTabWidget()
        
        # 1) 진입 전략 탭
        entry_tab = self.create_entry_strategy_tab()
        self.tab_widget.addTab(entry_tab, "📈 진입 전략")
        
        # 2) 관리 전략 탭  
        management_tab = self.create_management_strategy_tab()
        self.tab_widget.addTab(management_tab, "�️ 관리 전략")
        
        # 3) 전략 조합 탭
        combination_tab = self.create_strategy_combination_tab()
        self.tab_widget.addTab(combination_tab, "🔗 전략 조합")
        
        layout.addWidget(self.tab_widget)
```

#### Task 2.2: 전략 조합 탭 UI 설계
**목표**: 1개 진입 전략 + N개 관리 전략 조합 인터페이스

**전략 조합 탭 구조:**
```
전략 조합 탭 (StrategyCombinationTab)
├── 좌측 패널 (25%) - 조합 목록
│   ├── 저장된 조합 목록
│   ├── 새 조합 생성 버튼
│   └── 조합 삭제 버튼
├── 중앙 패널 (50%) - 조합 에디터
│   ├── 조합 기본 정보
│   │   ├── 조합 이름
│   │   └── 설명
│   ├── 진입 전략 선택 (필수, 1개만)
│   │   ├── 사용 가능한 진입 전략 목록
│   │   └── 선택된 진입 전략 표시
│   ├── 관리 전략 선택 (선택, 0~N개)
│   │   ├── 사용 가능한 관리 전략 목록
│   │   ├── 선택된 관리 전략 목록
│   │   └── 우선순위 설정
│   └── 조합 설정
│       ├── 관리 전략 실행 순서
│       ├── 충돌 해결 방식
│       └── 리스크 한계 설정
└── 우측 패널 (25%) - 백테스트 결과
    ├── 조합 성과 요약
    ├── 개별 전략 기여도
    └── 리스크 지표
```

#### Task 2.3: 전략 조합 데이터 모델
**목표**: 진입 + 관리 전략 조합을 위한 데이터 구조

```python
@dataclass
class StrategyCombination:
    combination_id: str
    name: str
    description: str
    
    # 필수: 진입 전략 (1개만)
    entry_strategy: dict  # {"strategy_id": str, "parameters": dict}
    
    # 선택: 관리 전략 (0~N개)
    management_strategies: List[dict]  # [{"strategy_id": str, "parameters": dict, "priority": int}]
    
    # 조합 설정
    execution_order: str = "parallel"  # "parallel" | "sequential"
    conflict_resolution: str = "priority"  # "priority" | "merge" | "ignore"
    risk_limit: dict = None  # {"max_position_size": float, "max_drawdown": float}
    
    created_at: datetime = None
    updated_at: datetime = None
    
    def validate(self):
        """조합 유효성 검증"""
        if not self.entry_strategy:
            raise ValueError("진입 전략은 필수입니다")
        
        if len(self.management_strategies) > 5:
            raise ValueError("관리 전략은 최대 5개까지 허용됩니다")
```

### Phase 3: 백테스팅 엔진 재설계 (5-6일)

#### Task 3.1: 상태 기반 백테스팅 엔진 구현
**목표**: 포지션 상태에 따른 전략 역할 전환 로직 구현

**새로운 백테스팅 엔진 구조:**
```python
class RoleBasedBacktestEngine:
    def __init__(self, strategy_combination: StrategyCombination):
        self.combination = strategy_combination
        self.entry_strategy = self.load_entry_strategy()
        self.management_strategies = self.load_management_strategies()
        self.position = None  # 현재 포지션 정보
        self.state = "WAITING_ENTRY"  # 엔진 상태
    
    def process_market_data(self, market_data):
        """시장 데이터 처리 및 상태별 로직 실행"""
        
        if self.state == "WAITING_ENTRY":
            # 진입 대기: 진입 전략만 활성화
            signal = self.entry_strategy.generate_entry_signal(
                market_data, position_status=None
            )
            
            if signal in ['BUY', 'SELL']:
                self.enter_position(signal, market_data)
                self.state = "POSITION_MANAGEMENT"
                
        elif self.state == "POSITION_MANAGEMENT":
            # 포지션 관리: 관리 전략들만 활성화
            for management_strategy in self.management_strategies:
                mgmt_signal = management_strategy.generate_management_signal(
                    market_data, self.position
                )
                
                if mgmt_signal['action'] != 'HOLD':
                    self.execute_management_action(mgmt_signal)
                    
                    # 포지션 완전 청산 시 상태 전환
                    if mgmt_signal['action'] == 'CLOSE_POSITION':
                        self.state = "WAITING_ENTRY"
                        self.position = None
                        break
    
    def enter_position(self, signal, market_data):
        """포지션 진입"""
        self.position = {
            'direction': signal,
            'entry_price': market_data['close'],
            'entry_time': market_data['timestamp'],
            'quantity': self.calculate_position_size(),
            'stop_price': None,
            'management_history': []
        }
    
    def execute_management_action(self, mgmt_signal):
        """관리 전략 액션 실행"""
        action = mgmt_signal['action']
        
        if action == 'ADD_BUY':
            # 추가 매수 (물타기/불타기)
            self.position['quantity'] += mgmt_signal['quantity']
            self.update_average_price(mgmt_signal['price'], mgmt_signal['quantity'])
            
        elif action == 'ADD_SELL':
            # 부분 매도
            self.position['quantity'] -= mgmt_signal['quantity']
            
        elif action == 'UPDATE_STOP':
            # 트레일링 스탑 업데이트
            self.position['stop_price'] = mgmt_signal['stop_price']
            
        elif action == 'CLOSE_POSITION':
            # 전체 포지션 청산
            self.close_position(mgmt_signal['price'])
        
        # 관리 이력 기록
        self.position['management_history'].append({
            'action': action,
            'timestamp': mgmt_signal.get('timestamp'),
            'price': mgmt_signal.get('price'),
            'quantity': mgmt_signal.get('quantity')
        })
```

#### Task 3.2: 데이터베이스 스키마 업데이트
**목표**: 새로운 전략 구조를 지원하는 DB 스키마

**새로운 테이블 구조:**
```sql
-- 전략 기본 테이블 (기존 수정)
ALTER TABLE trading_strategies ADD COLUMN strategy_role TEXT NOT NULL 
    CHECK (strategy_role IN ('entry', 'management')) DEFAULT 'entry';

-- 전략 조합 테이블
CREATE TABLE strategy_combinations (
    combination_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    entry_strategy_id TEXT NOT NULL,
    execution_order TEXT DEFAULT 'parallel',
    conflict_resolution TEXT DEFAULT 'priority',
    risk_limit TEXT, -- JSON 형태 저장
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entry_strategy_id) REFERENCES trading_strategies(strategy_id)
);

-- 조합의 관리 전략 테이블
CREATE TABLE combination_management_strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    combination_id TEXT NOT NULL,
    management_strategy_id TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    parameters TEXT, -- JSON 형태로 개별 파라미터 저장
    FOREIGN KEY (combination_id) REFERENCES strategy_combinations(combination_id),
    FOREIGN KEY (management_strategy_id) REFERENCES trading_strategies(strategy_id)
);

-- 백테스트 실행 이력 테이블 (확장)
ALTER TABLE backtest_results ADD COLUMN combination_id TEXT;
ALTER TABLE backtest_results ADD COLUMN position_management_log TEXT; -- JSON 형태
```

#### Task 3.3: 충돌 해결 및 우선순위 시스템
**목표**: 여러 관리 전략이 동시에 신호를 보낼 때 처리 방식

**충돌 해결 방식:**
```python
class ConflictResolver:
    def resolve_management_conflicts(self, signals: List[dict], 
                                   resolution_method: str) -> dict:
        """
        여러 관리 전략 신호 충돌 해결
        
        Args:
            signals: 각 관리 전략의 신호 목록
            resolution_method: "priority" | "merge" | "conservative"
        
        Returns:
            최종 실행할 단일 신호
        """
        
        if resolution_method == "priority":
            # 우선순위가 높은 전략의 신호 채택
            return max(signals, key=lambda x: x.get('priority', 0))
            
        elif resolution_method == "merge":
            # 신호들을 합리적으로 병합
            return self.merge_signals(signals)
            
        elif resolution_method == "conservative":
            # 보수적 접근: CLOSE_POSITION 우선, 그 다음 HOLD
            close_signals = [s for s in signals if s['action'] == 'CLOSE_POSITION']
            if close_signals:
                return close_signals[0]
            
            hold_signals = [s for s in signals if s['action'] == 'HOLD']
            if hold_signals:
                return hold_signals[0]
            
            # 그 외는 우선순위 기준
            return max(signals, key=lambda x: x.get('priority', 0))
    
    def merge_signals(self, signals: List[dict]) -> dict:
        """신호 병합 로직"""
        # 추가 매수/매도 수량 합산
        total_add_buy = sum(s['quantity'] for s in signals 
                           if s['action'] == 'ADD_BUY')
        total_add_sell = sum(s['quantity'] for s in signals 
                            if s['action'] == 'ADD_SELL')
        
        # 트레일링 스탑은 가장 보수적인 값 선택
        stop_prices = [s['stop_price'] for s in signals 
                      if s['action'] == 'UPDATE_STOP' and s.get('stop_price')]
        
        # 병합된 최종 신호 생성
        if total_add_buy > 0:
            return {'action': 'ADD_BUY', 'quantity': total_add_buy}
        elif total_add_sell > 0:
            return {'action': 'ADD_SELL', 'quantity': total_add_sell}
        elif stop_prices:
            return {'action': 'UPDATE_STOP', 'stop_price': min(stop_prices)}
        else:
            return {'action': 'HOLD'}
```

### Phase 4: 백테스팅 통합 (2-3일)

#### Task 4.1: 조합 전략 백테스트 지원
**목표**: 조합 전략도 기본 전략과 동일하게 백테스트 가능 (DB와 기간 선택 기능 포함)

**백테스트 엔진 확장:**
```python
class CompositeStrategyBacktester:
    def run_backtest(self, composite_config: CompositeStrategyConfig,
                    symbol: str, start_date: str, end_date: str,
                    initial_capital: float, 
                    data_source: str = "default") -> dict:
        """
        조합 전략 백테스트 실행
        Args:
            data_source: 백테스팅 대상 DB 선택 ("upbit_1m", "upbit_5m", "upbit_1h" 등)
        """
        # 조합 전략 개수 제한 검증
        if len(composite_config.base_strategies) > 4:
            raise ValueError("조합 전략은 최대 4개까지만 백테스트 가능합니다")
        
        # 1. 구성 전략들의 개별 신호 생성
        individual_signals = {}
        for strategy_id in composite_config.base_strategies:
            strategy = self.load_strategy(strategy_id)
            signals = strategy.generate_signals(market_data, data_source)
            individual_signals[strategy_id] = signals
        
        # 2. 조합 로직으로 최종 신호 생성
        if composite_config.combination_type == "discrete":
            engine = DiscreteCompositionEngine()
            final_signals = engine.generate_signals(
                individual_signals, composite_config.logic_operator
            )
        else:  # weighted
            engine = WeightedCompositionEngine()
            final_signals = engine.generate_signals(
                individual_signals, composite_config.weights,
                composite_config.signal_threshold
            )
        
        # 3. 백테스트 실행
        return self.execute_backtest(final_signals, market_data, initial_capital)
```

**백테스트 UI 개선:**
- DB 선택 콤보박스 추가 (upbit_1m, upbit_5m, upbit_1h, upbit_1d)
- 백테스트 기간 선택 위젯 추가 (시작일/종료일 DatePicker)
- 조합 전략 제한사항 UI 표시

#### Task 4.2: 성과 비교 및 분석
**목표**: 개별 전략 vs 조합 전략 성과 비교 (백테스팅 검증 항목 향후 조사)

**비교 지표 (현재):**
- 개별 전략별 수익률, 샤프 비율, MDD
- 조합 전략 수익률, 샤프 비율, MDD
- 상관관계 분석 (개별 전략 간)
- 리스크 분산 효과 측정

**향후 조사 필요:**
- 백테스팅 검증 결과 상세 출력 항목 연구
- 슬리피지 및 거래 비용 반영 방안
- 드로우다운 분석 및 복구 시간 측정

## 📊 개발 일정표

| Phase | Task | 예상 소요 시간 | 담당 영역 | 비고 |
|-------|------|------------|-----------|------|
| 1.1 | 툴바 중복 제거 및 개선 | 1일 | Frontend | |
| 1.2 | 기본 전략 유형 확장 (4→10개) | 3일 | Backend + Frontend | 디폴트 파라미터 적용 |
| 2.1 | QTabWidget 도입 | 1일 | Frontend | |
| 2.2 | 조합 전략 탭 UI 설계 | 3일 | Frontend | 4개 제한 UI 반영 |
| 3.1 | 조합 전략 DB 스키마 | 1일 | Database | 4개 제한 검증 |
| 3.2 | 조합 신호 생성 엔진 | 4일 | Backend | AI 친화적 구조 |
| 4.1 | 조합 전략 백테스트 지원 | 2일 | Backend | DB/기간 선택 추가 |
| 4.2 | 성과 비교 및 분석 | 1일 | Backend + Frontend | 검증 항목 조사 병행 |

**총 예상 개발 시간: 20일** (기존과 동일, 제약사항으로 복잡도 감소)

## 🔧 기술적 고려사항

### 1. 성능 최적화
- **조합 신호 계산**: 개별 전략 신호를 캐싱하여 중복 계산 방지
- **백테스트 병렬화**: 여러 전략의 백테스트를 병렬로 실행 (최대 4개 제한 활용)
- **메모리 관리**: 대용량 시계열 데이터 처리 시 메모리 효율성

### 2. 확장성 고려
- **플러그인 아키텍처**: 새로운 전략 유형 쉽게 추가 가능 (AI 친화적 구조)
- **설정 파일**: 전략 파라미터를 JSON/YAML로 외부화 (디폴트 값 관리)
- **API 호환성**: 향후 웹 인터페이스와의 연동 고려

### 3. 사용자 경험
- **실시간 미리보기**: 조합 설정 변경 시 즉시 예상 결과 표시
- **드래그&드롭**: 직관적인 전략 조합 인터페이스 (4개 제한 표시)
- **시각적 피드백**: 조합 로직을 그래프로 표현

### 4. AI 친화적 개발 방침
### Phase 4: 통합 테스트 및 검증 (3-4일)

#### Task 4.1: 전략 조합 백테스트 지원
**목표**: 새로운 역할 분리 구조에서 백테스트 실행

**백테스트 실행 예시:**
```python
def run_combination_backtest():
    """전략 조합 백테스트 실행 예시"""
    
    # 1. 전략 조합 설정
    combination = StrategyCombination(
        combination_id="rsi_averaging_trailing",
        name="RSI 진입 + 물타기 + 트레일링 스탑",
        description="RSI 과매도 진입 후 물타기와 트레일링 스탑으로 관리",
        
        # 진입 전략: RSI 과매도
        entry_strategy={
            "strategy_id": "rsi_entry",
            "parameters": {"rsi_period": 14, "oversold": 30}
        },
        
        # 관리 전략: 물타기 + 트레일링 스탑
        management_strategies=[
            {
                "strategy_id": "averaging_down",
                "parameters": {"trigger_drop_percent": 5.0, "max_additional_buys": 2},
                "priority": 1
            },
            {
                "strategy_id": "trailing_stop", 
                "parameters": {"trailing_distance": 3.0, "activation_profit": 2.0},
                "priority": 2
            }
        ],
        
        execution_order="parallel",
        conflict_resolution="conservative"
    )
    
    # 2. 백테스트 엔진 실행
    engine = RoleBasedBacktestEngine(combination)
    results = engine.run_backtest(
        symbol="BTC-KRW",
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=1000000
    )
    
    return results
```

#### Task 4.2: 성과 분석 및 시각화
**목표**: 진입/관리 전략 기여도 분석

**분석 지표:**
```python
class PerformanceAnalyzer:
    def analyze_combination_performance(self, backtest_results):
        """전략 조합 성과 분석"""
        
        analysis = {
            # 전체 성과
            "total_return": self.calculate_total_return(backtest_results),
            "sharpe_ratio": self.calculate_sharpe_ratio(backtest_results),
            "max_drawdown": self.calculate_max_drawdown(backtest_results),
            
            # 진입 전략 기여도
            "entry_strategy_contribution": {
                "successful_entries": self.count_successful_entries(),
                "entry_accuracy": self.calculate_entry_accuracy(),
                "average_entry_timing": self.analyze_entry_timing()
            },
            
            # 관리 전략 기여도
            "management_strategy_contribution": {
                "averaging_down_effect": self.analyze_averaging_effect(),
                "trailing_stop_protection": self.analyze_stop_protection(),
                "partial_exit_optimization": self.analyze_partial_exits()
            },
            
            # 리스크 관리 효과
            "risk_management": {
                "position_size_control": self.analyze_position_sizing(),
                "drawdown_reduction": self.calculate_drawdown_reduction(),
                "volatility_impact": self.analyze_volatility_impact()
            }
        }
        
        return analysis
```

## 📊 개발 일정표 (수정)

| Phase | Task | 예상 소요 시간 | 담당 영역 | 핵심 내용 |
|-------|------|------------|-----------|-----------|
| 1.1 | 전략 클래스 구조 재설계 | 2일 | Backend | 진입/관리 전략 인터페이스 분리 |
| 1.2 | 진입 전략 구현 (6개) | 3일 | Backend | 이평교차, RSI, 볼밴드, 변동성돌파, MACD, 스토캐스틱 |
| 1.3 | 관리 전략 구현 (6개) | 4일 | Backend | 물타기, 불타기, 트레일링, 고정익절, 부분청산, 시간청산 |
| 2.1 | UI 탭 구조 변경 | 2일 | Frontend | 진입/관리/조합 3탭 구조 |
| 2.2 | 전략 조합 UI 설계 | 3일 | Frontend | 1진입+N관리 조합 인터페이스 |
| 2.3 | 조합 데이터 모델 | 1일 | Backend | StrategyCombination 클래스 |
| 3.1 | 백테스팅 엔진 재설계 | 3일 | Backend | 상태 기반 역할 전환 로직 |
| 3.2 | DB 스키마 업데이트 | 1일 | Database | 역할 분리 지원 테이블 |
| 3.3 | 충돌 해결 시스템 | 2일 | Backend | 관리 전략 신호 충돌 처리 |
| 4.1 | 백테스트 통합 테스트 | 2일 | Integration | 전략 조합 백테스트 검증 |
| 4.2 | 성과 분석 시스템 | 2일 | Backend + Frontend | 진입/관리 기여도 분석 |

**총 예상 개발 시간: 25일** (복잡도 증가로 5일 추가)

## 🔧 기술적 고려사항 (업데이트)

### 1. 성능 최적화
- **상태 전환 최적화**: 포지션 상태 변경 시에만 전략 재평가
- **신호 캐싱**: 동일 시점 여러 관리 전략 신호 중복 계산 방지
- **메모리 관리**: 장기간 백테스트 시 포지션 이력 관리

### 2. 확장성 고려
- **플러그인 아키텍처**: 새로운 진입/관리 전략 쉽게 추가
- **역할 기반 설계**: 진입과 관리 로직의 명확한 분리
- **AI 친화적 구조**: 각 전략의 독립적인 책임과 명확한 인터페이스

### 3. 사용자 경험
- **직관적 조합**: 1진입+N관리의 자연스러운 구성
- **시각적 피드백**: 포지션 상태와 활성 전략 실시간 표시
- **성과 분석**: 진입/관리 전략별 기여도 분석

## 📋 우선순위 및 다음 단계 (업데이트)

### 즉시 시작 가능한 작업 (High Priority)
1. **Task 1.1**: 전략 클래스 구조 재설계 (2일) - 핵심 기반 작업
2. **Task 1.2**: 진입 전략 구현 (3일) - 기존 4개 + 신규 2개

### 의존성이 있는 작업 (Medium Priority)
3. **Task 1.3**: 관리 전략 구현 (1.1, 1.2 완료 후)
4. **Task 2.1**: UI 구조 변경 (전략 구조 확정 후)

### 통합 테스트 (Low Priority)
5. **Task 3.1**: 백테스팅 엔진 재설계 (모든 전략 구현 완료 후)

## 🤝 확정된 개발 방침

### 1. 전략 역할 분리 **[확정]**
- **진입 전략**: 포지션 없을 때만 활성화, 최초 진입 신호 생성
- **관리 전략**: 포지션 있을 때만 활성화, 리스크 관리 및 수익 극대화
- **조합 시스템**: 1개 진입 + 0~5개 관리 전략 조합

### 2. 백테스팅 엔진 상태 전환 **[확정]**
- **진입 대기 → 포지션 진입 → 포지션 관리 → 포지션 종료** 순환
- 각 상태별 활성화되는 전략 역할 명확히 구분
- 충돌 해결 시스템으로 관리 전략 신호 조정

### 3. UI 설계 방향 **[확정]**
- **3탭 구조**: 진입 전략 / 관리 전략 / 전략 조합
- **조합 인터페이스**: 필수 1개 진입 + 선택 N개 관리
- **제약사항 표시**: 각 역할별 제한사항 UI에 명시

### 4. 실현 가능한 매매 시나리오 **[목표]**
- "RSI 과매도로 진입 → -5%마다 물타기 2번 → 10% 트레일링 스탑"
- "이평교차로 진입 → 불타기로 추가 매수 → 부분 청산으로 수익 실현"
- "변동성 돌파 진입 → 고정 익절/손절 → 시간 기반 강제 청산"

이 새로운 구조로 사용자가 실제 매매에서 사용하는 직관적이고 현실적인 전략을 구성할 수 있게 됩니다!

## 📝 추가 고려사항

### V1.2 이후 개발 예정
1. **동적 파라미터 조정**: 시장 상황에 따른 관리 전략 파라미터 자동 조정
2. **머신러닝 기반 진입 타이밍**: AI 모델을 이용한 진입 신호 정교화
3. **리스크 패리티**: 포트폴리오 레벨에서 리스크 균형 관리
4. **실시간 알림 시스템**: 전략 조합별 신호 발생 알림

사용자가 제기한 핵심 문제를 해결하는 완전히 새로운 구조로 재설계되었습니다!

## 🎯 결론

기존의 "전략"이라는 모호한 개념을 **진입 전략**과 **관리 전략**으로 명확히 분리함으로써:

1. **직관적인 매매 로직**: 실제 트레이더의 사고 방식과 일치
2. **명확한 책임 분리**: 각 전략의 역할과 실행 조건이 명확
3. **현실적인 백테스팅**: 포지션 상태에 따른 정확한 시뮬레이션
4. **확장 가능한 구조**: 새로운 진입/관리 전략 쉽게 추가 가능

이제 사용자는 "어떻게 들어갈 것인가"와 "들어간 후 어떻게 관리할 것인가"를 분리해서 생각하고 조합할 수 있습니다!
