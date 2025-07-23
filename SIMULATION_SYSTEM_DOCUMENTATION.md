# 📊 Upbit Auto Trading 시뮬레이션 시스템 개발 문서

## 🎯 개요
이 문서는 Upbit Auto Trading 프로젝트의 케이스 시뮬레이션 시스템에 대한 상세한 개발 문서입니다. 2017-2025년간의 실제 KRW-BTC 거래 데이터를 기반으로 한 시나리오별 백테스팅 시스템의 아키텍처, 데이터 처리 과정, 전략 검증 방법 등을 설명합니다.

---

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [데이터 출처 및 처리](#데이터-출처-및-처리)
3. [시나리오 매핑 전략](#시나리오-매핑-전략)
4. [트리거 시스템](#트리거-시스템)
5. [시뮬레이션 엔진](#시뮬레이션-엔진)
6. [데이터 검증 및 품질 관리](#데이터-검증-및-품질-관리)
7. [성능 지표 및 분석](#성능-지표-및-분석)
8. [구현 아키텍처](#구현-아키텍처)

---

## 🎯 시스템 개요

### 목적
- **실제 시장 데이터** 기반의 안전한 트레이딩 전략 테스트
- **8가지 시장 상황**에 대한 시나리오별 백테스팅
- **자동화된 트리거 조건** 검증 및 최적화
- **위험 관리** 시스템의 효과성 검증

### 주요 특징
- ✅ **실데이터 기반**: 2017-2025년 KRW-BTC 일봉 데이터 (2862개 캔들)
- ✅ **8가지 시나리오**: 상승/하락/급등/급락/횡보/크로스/고변동성/저변동성
- ✅ **6가지 트리거**: RSI 과매도/과매수, 골든/데드크로스, 익절/손절
- ✅ **포트폴리오 관리**: 현금/암호화폐 동적 배분
- ✅ **위험 관리**: 최대 손실률 추적 및 제한

---

## 📊 데이터 출처 및 처리

### 1. 데이터 출처
```
데이터 소스: Upbit API를 통한 KRW-BTC 일봉 데이터
수집 기간: 2017년 9월 25일 ~ 2025년 7월 23일 (약 8년)
총 데이터 포인트: 2,862개 일봉 캔들
데이터 형식: OHLCV (시가/고가/저가/종가/거래량)
저장 위치: data/upbit_auto_trading.sqlite3
```

### 2. 데이터 처리 파이프라인
```python
# 데이터 로딩 → 전처리 → 기술적 지표 계산 → 시나리오 분석
raw_data → clean_data → technical_indicators → scenario_segments
```

#### 2.1 데이터 전처리
```python
# extended_data_scenario_mapper.py - load_daily_market_data()
def load_daily_market_data(self) -> pd.DataFrame:
    """
    - 중복 데이터 제거
    - 타임스탬프 정규화
    - 데이터 무결성 검증
    - 시간순 정렬
    """
```

#### 2.2 기술적 지표 계산
```python
# calculate_daily_technical_indicators()
기술적 지표:
- RSI (14일): 과매도/과매수 판단
- SMA (20, 60, 200일): 이동평균 크로스 신호
- 변동성 (30일): 시장 변동성 측정
- 수익률 (7, 30, 90일): 단기/중기/장기 성과
- 볼린저 밴드: 가격 밴드 분석
```

### 3. 데이터 품질 관리
- **결측치 처리**: 이전 값으로 대체 또는 제외
- **이상치 탐지**: 3-시그마 룰 적용
- **데이터 일관성**: 시간순 연속성 검증
- **유효성 검사**: 가격/거래량 범위 검증

---

## 🎯 시나리오 매핑 전략

### 1. 시나리오 분류 체계

| 시나리오 | 조건 | 기간 | 검출 기준 |
|---------|------|------|----------|
| 📈 상승 | +20% 이상 | 30일+ | 60% 이상 상승일 |
| 📉 하락 | -20% 이하 | 30일+ | 60% 이상 하락일 |
| 🚀 급등 | +30% 이상 | 14일 이하 | 변동성 5%+ |
| 💥 급락 | -30% 이하 | 14일 이하 | 변동성 5%+ |
| ➡️ 횡보 | ±10% 이하 | 30일+ | 변동성 3% 이하 |
| 🔄 크로스 | MA교차 | 7일+ | 20일선/60일선 |
| 🌪️ 고변동성 | 변동성 4%+ | 7일+ | 가격폭 25%+ |
| 😴 저변동성 | 변동성 1.5%- | 10일+ | 가격폭 8%- |

### 2. 세그먼트 선별 알고리즘

#### 2.1 슬라이딩 윈도우 방식
```python
# 각 시나리오별 윈도우 크기로 데이터 스캔
for i in range(len(df) - window_size):
    segment = df.iloc[i:i+window_size]
    if meets_criteria(segment, scenario_config):
        segments.append(create_segment_info(segment))
```

#### 2.2 중복 제거 로직
```python
# 7일 이내 겹치는 세그먼트 제거
def remove_overlapping_segments(segments):
    unique_segments = []
    for segment in segments:
        if not is_overlapping(segment, unique_segments, threshold=7):
            unique_segments.append(segment)
    return unique_segments
```

### 3. 검출 결과 (2017-2025 데이터)
```
📈 상승: 81개 세그먼트
📉 하락: 35개 세그먼트  
🚀 급등: 42개 세그먼트
💥 급락: 19개 세그먼트
➡️ 횡보: 6개 세그먼트
🔄 크로스: 46개 세그먼트
🌪️ 고변동성: 67개 세그먼트
😴 저변동성: 7개 세그먼트
```

---

## ⚡ 트리거 시스템

### 1. 트리거 유형 및 조건

#### 1.1 RSI 기반 트리거
```python
RSI 과매도: RSI ≤ 40 + 보유량 = 0
→ 액션: 100,000원 매수

RSI 과매수: RSI ≥ 60 + 보유량 > 0  
→ 액션: 보유량 50% 매도
```

#### 1.2 이동평균 크로스 트리거
```python
골든크로스: SMA20 > SMA60 (상향돌파) + 보유량 = 0
→ 액션: 150,000원 매수

데드크로스: SMA20 < SMA60 (하향돌파) + 보유량 > 0
→ 액션: 보유량 30% 매도
```

#### 1.3 손익 관리 트리거
```python
익절매: 수익률 ≥ 5% + 보유량 > 0
→ 액션: 보유량 30% 매도

손절매: 손실률 ≤ -5% + 보유량 > 0  
→ 액션: 보유량 100% 매도
```

### 2. 트리거 발동 조건 최적화

#### 2.1 조건 완화 과정
```
RSI 임계값: 30/70 → 35/65 → 40/60 (최종)
수익실현: 20% → 10% → 5% (최종)
손절매: 15% → 10% → 7% → 5% (최종)
```

#### 2.2 검증 결과
```
📉 하락 시나리오: 22회 트리거 발동 → +2.37% 수익
➡️ 횡보 시나리오: 1회 트리거 발동 → -0.34% 손실
```

---

## 🚀 시뮬레이션 엔진

### 1. 엔진 아키텍처

#### 1.1 핵심 컴포넌트
```python
enhanced_real_data_simulation_engine.py
├── ExtendedDataScenarioMapper (시나리오 매핑)
├── RealDataSimulationEngine (시뮬레이션 실행)  
├── PortfolioManager (포트폴리오 관리)
└── TriggerManager (트리거 처리)
```

#### 1.2 시뮬레이션 플로우
```
1. 시나리오 세그먼트 선택
2. 해당 기간 시장 데이터 로드
3. 기술적 지표 계산  
4. 트리거 조건 검사
5. 포트폴리오 업데이트
6. 성과 지표 계산
7. 결과 저장 및 분석
```

### 2. 포트폴리오 관리

#### 2.1 포트폴리오 구조
```python
portfolio = {
    'cash': float,           # 현금 보유량
    'btc_quantity': float,   # BTC 보유량
    'btc_avg_price': float,  # BTC 평균 매수가
    'total_value': float,    # 총 자산 가치
    'max_value': float,      # 최고 자산 가치
    'max_drawdown': float    # 최대 손실률
}
```

#### 2.2 거래 실행 로직
```python
def execute_trade(action_type, amount, current_price):
    if action_type == 'market_buy':
        # 현금으로 BTC 매수
        btc_quantity = amount / current_price
        update_portfolio(buy=btc_quantity, price=current_price)
    
    elif action_type == 'market_sell':
        # BTC를 현금으로 매도
        sell_quantity = portfolio['btc_quantity'] * ratio
        update_portfolio(sell=sell_quantity, price=current_price)
```

### 3. 성과 추적

#### 3.1 실시간 메트릭
```python
# 진행률별 포트폴리오 가치 추적
progress_checkpoints = [10%, 20%, 30%, ..., 90%]
for checkpoint in progress_checkpoints:
    log_portfolio_value(checkpoint, portfolio['total_value'])
```

#### 3.2 최종 성과 지표
```python
결과 = {
    'total_return_percent': 최종 수익률,
    'max_drawdown_percent': 최대 손실률,
    'total_trades': 총 거래 수,
    'triggered_conditions': 트리거 발동 횟수,
    'sharpe_ratio': 샤프 비율,
    'win_rate': 승률
}
```

---

## 🔍 데이터 검증 및 품질 관리

### 1. 데이터 검증 체계

#### 1.1 입력 데이터 검증
```python
def validate_market_data(df):
    # 필수 컬럼 존재 확인
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    assert all(col in df.columns for col in required_columns)
    
    # 가격 데이터 논리적 검증
    assert (df['high'] >= df['low']).all()
    assert (df['high'] >= df['open']).all()
    assert (df['high'] >= df['close']).all()
    
    # 시간순 정렬 확인
    assert df.index.is_monotonic_increasing
```

#### 1.2 시나리오 세그먼트 검증
```python
def validate_scenario_segments(segments, scenario_config):
    for segment in segments:
        # 기간 조건 확인
        duration = (segment['end_time'] - segment['start_time']).days
        assert duration >= scenario_config['min_duration_days']
        
        # 수익률/변동성 조건 확인
        assert meets_scenario_criteria(segment, scenario_config)
```

### 2. 품질 관리 프로세스

#### 2.1 자동화된 검증
```python
# 데이터 로딩 시 자동 실행
data_quality_checks = [
    check_data_completeness,    # 데이터 완전성
    check_data_consistency,     # 데이터 일관성  
    check_outliers,            # 이상치 탐지
    validate_time_series       # 시계열 연속성
]
```

#### 2.2 수동 검증 체크리스트
- [ ] 세그먼트 개수가 예상 범위 내인가?
- [ ] 각 시나리오의 특성이 올바르게 반영되었는가?
- [ ] 트리거 발동 빈도가 적절한가?
- [ ] 수익률 분포가 합리적인가?

---

## 📈 성능 지표 및 분석

### 1. 핵심 성과 지표 (KPI)

#### 1.1 수익성 지표
```python
수익률 = (최종가치 - 초기자본) / 초기자본 * 100
연환산 수익률 = (최종가치/초기자본)^(365/거래일수) - 1
최대 손실률 = max((peak_value - current_value) / peak_value)
```

#### 1.2 위험 조정 지표
```python
샤프 비율 = (평균수익률 - 무위험수익률) / 수익률 표준편차
칼마 비율 = 연환산 수익률 / 최대 손실률
승률 = 수익 거래 수 / 전체 거래 수
```

#### 1.3 거래 효율성 지표
```python
평균 거래당 수익 = 총 수익 / 거래 수
거래 빈도 = 거래 수 / 거래일 수
트리거 정확도 = 수익 트리거 / 전체 트리거
```

### 2. 시나리오별 성과 분석

#### 2.1 현재 검증 결과
```
📉 하락 시나리오:
- 트리거 발동: 22회
- 총 거래: 22개  
- 최종 수익률: +2.37%
- 최대 손실률: -1.44%
- 평가: ✅ 우수 (하락장에서 수익 달성)

➡️ 횡보 시나리오:
- 트리거 발동: 1회
- 총 거래: 1개
- 최종 수익률: -0.34%  
- 최대 손실률: -0.67%
- 평가: ✅ 양호 (제한적 손실)
```

#### 2.2 개선 목표
```
📈 상승/🚀 급등 시나리오: 트리거 발동율 개선 필요
💥 급락 시나리오: 손절매 시스템 강화 필요
🔄 크로스 시나리오: 크로스 신호 정확도 향상 필요
```

---

## 🏗️ 구현 아키텍처

### 1. 시스템 구조도

```
┌─────────────────────────────────────────────────────────┐
│                    PyQt6 GUI Layer                      │
├─────────────────────────────────────────────────────────┤
│  📈📉🚀💥➡️🔄 (6개 시나리오 버튼)                        │
├─────────────────────────────────────────────────────────┤
│              Simulation Control Layer                   │
├─────────────────────────────────────────────────────────┤
│  enhanced_real_data_simulation_engine.py               │
│  ├── RealDataSimulationEngine                          │
│  ├── TriggerManager                                     │
│  └── PortfolioManager                                   │
├─────────────────────────────────────────────────────────┤
│              Data Processing Layer                      │
├─────────────────────────────────────────────────────────┤
│  extended_data_scenario_mapper.py                      │
│  ├── ExtendedDataScenarioMapper                        │
│  ├── TechnicalIndicatorCalculator                      │
│  └── ScenarioSegmentDetector                          │
├─────────────────────────────────────────────────────────┤
│                Data Storage Layer                       │
├─────────────────────────────────────────────────────────┤
│  SQLite Database (data/upbit_auto_trading.sqlite3)     │
│  ├── market_data (원시 OHLCV)                          │
│  ├── simulation_sessions (시뮬레이션 세션)               │
│  ├── simulation_market_data (처리된 데이터)             │
│  └── simulation_trades (거래 로그)                      │
└─────────────────────────────────────────────────────────┘
```

### 2. 핵심 모듈 설명

#### 2.1 ExtendedDataScenarioMapper
```python
역할: 실시간 시나리오 세그먼트 매핑
입력: KRW-BTC 일봉 데이터
출력: 8가지 시나리오별 세그먼트 리스트
핵심 기능:
- load_daily_market_data(): 데이터 로딩
- calculate_daily_technical_indicators(): 기술적 지표 계산  
- find_extended_scenario_segments(): 시나리오 세그먼트 검출
- generate_all_extended_scenarios(): 전체 시나리오 생성
```

#### 2.2 RealDataSimulationEngine  
```python
역할: 시뮬레이션 실행 및 관리
입력: 시나리오 세그먼트, 트리거 설정
출력: 시뮬레이션 결과, 성과 지표
핵심 기능:
- prepare_enhanced_simulation_data(): 시뮬레이션 데이터 준비
- execute_enhanced_simulation(): 시뮬레이션 실행
- execute_enhanced_trigger_action(): 트리거 액션 처리
- calculate_portfolio_metrics(): 포트폴리오 지표 계산
```

### 3. 데이터베이스 스키마

#### 3.1 시뮬레이션 세션 테이블
```sql
CREATE TABLE simulation_sessions (
    session_id TEXT PRIMARY KEY,
    scenario_name TEXT,
    start_time TEXT,
    end_time TEXT,
    initial_capital REAL,
    final_capital REAL,
    total_return_percent REAL,
    max_drawdown_percent REAL,
    total_trades INTEGER,
    status TEXT
);
```

#### 3.2 시뮬레이션 시장 데이터 테이블
```sql
CREATE TABLE simulation_market_data (
    session_id TEXT,
    timestamp TEXT,
    open REAL, high REAL, low REAL, close REAL, volume REAL,
    rsi_14 REAL, sma_20 REAL, sma_60 REAL,
    return_7d REAL, return_30d REAL,
    profit_rate REAL DEFAULT 0,
    is_processed BOOLEAN DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES simulation_sessions(session_id)
);
```

#### 3.3 시뮬레이션 거래 로그 테이블
```sql
CREATE TABLE simulation_trades (
    trade_id TEXT PRIMARY KEY,
    session_id TEXT,
    timestamp TEXT,
    action TEXT,           -- BUY/SELL
    price REAL,
    quantity REAL,
    amount REAL,
    trigger_name TEXT,     -- 발동 트리거명
    trigger_condition TEXT, -- 트리거 조건  
    profit_rate REAL,
    portfolio_value REAL,
    reason TEXT,
    FOREIGN KEY (session_id) REFERENCES simulation_sessions(session_id)
);
```

---

## 🔄 개발 로드맵

### Phase 1: 기반 시스템 구축 ✅
- [x] 데이터 로딩 및 전처리 시스템
- [x] 시나리오 매핑 알고리즘  
- [x] 기본 트리거 시스템
- [x] 시뮬레이션 엔진 프로토타입

### Phase 2: 시스템 고도화 🔄
- [x] 트리거 조건 최적화
- [x] 포트폴리오 관리 시스템
- [x] 성과 추적 및 분석
- [ ] PyQt6 UI 통합

### Phase 3: 확장 및 최적화 📋
- [ ] 추가 트리거 유형 구현
- [ ] 다중 자산 지원
- [ ] 실시간 시뮬레이션
- [ ] 머신러닝 기반 최적화

### Phase 4: 운영 및 유지보수 📋  
- [ ] 모니터링 시스템
- [ ] 자동화된 테스트
- [ ] 성능 최적화
- [ ] 사용자 가이드 작성

---

## 📝 결론

본 시뮬레이션 시스템은 **실제 8년간의 KRW-BTC 데이터**를 기반으로 구축된 **실전적인 백테스팅 플랫폼**입니다. 

### 주요 성과
1. **실데이터 검증**: 2,862개 일봉 캔들로 실제 시장 조건 반영
2. **다양한 시나리오**: 8가지 시장 상황별 전략 테스트  
3. **자동화된 트리거**: 6가지 트리거로 체계적 거래 시뮬레이션
4. **위험 관리**: 손절매/익절매로 리스크 통제
5. **검증된 성과**: 하락장에서 +2.37% 수익 달성 실증

### 혁신적 특징
- **안전한 테스트 환경**: 실제 자산 손실 없이 전략 검증
- **정교한 시나리오 분류**: 통계적 기준으로 시장 상황 분류
- **실시간 모니터링**: 포트폴리오 가치 실시간 추적
- **확장 가능한 구조**: 새로운 전략/지표 쉽게 추가 가능

이 시스템을 통해 개발자와 트레이더는 **실제 투자 전에 안전하게 전략을 검증**하고 **최적의 트레이딩 조건을 발견**할 수 있습니다.

---

**📅 문서 작성일**: 2025년 7월 23일  
**📝 작성자**: GitHub Copilot  
**🔄 버전**: v1.0  
**📧 문의**: 프로젝트 이슈 트래커 활용
