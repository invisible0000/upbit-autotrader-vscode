# 📊 매매 변수 파라미터 강화 및 고급 변수 추가 프로젝트

## 🎯 프로젝트 개요

도움말에서 제시된 고급 매매 전략들을 실제 구현 가능한 형태로 체계화하고,
기존 변수의 파라미터 확장 vs 새로운 고급 변수 분리를 통해 사용성과 기능성의 균형을 맞춘다.

## 📅 프로젝트 정보

- **생성일**: 2025년 8월 17일
- **우선순위**: 높음 (매매 시스템 핵심 기능)
- **예상 기간**: 2-3주
- **담당**: 시스템 아키텍트 + 퀀트 분석가

## 🔍 1단계: 현재 변수별 도움말 분석 및 파라미터 검토

### 📊 분석 대상 (22개 변수)

**[ ] Volatility Category (2개)**
- [ ] ATR - 변동성 레짐 감지, 정규화 ATR, 동적 손절
- [ ] BOLLINGER_BAND - 적응형 밴드, 압축/확장 감지

**[ ] Momentum Category (3개)**
- [ ] RSI - 확률적 RSI, 다이버전스 감지
- [ ] MACD - 히스토그램 분석, 다중 시간대
- [ ] STOCHASTIC - %K/%D 최적화, 과매수/과매도 구간

**[ ] Trend Category (2개)**
- [ ] SMA - 적응형 기간, 기울기 분석
- [ ] EMA - 동적 승수, 반응성 조절

**[ ] Price Category (4개)**
- [ ] CURRENT_PRICE - 실시간 변화율, 백분위 위치
- [ ] HIGH_PRICE - 브레이크아웃 감지, 저항선 분석
- [ ] LOW_PRICE - 지지선 분석, 바닥 패턴 인식
- [ ] OPEN_PRICE - 갭 분석, 장 시작 모멘텀

**[ ] Volume Category (2개)**
- [ ] VOLUME - 거래량 스파이크, 정규화 거래량
- [ ] VOLUME_SMA - 상대 거래량, 추세 분석

**[ ] Capital Category (3개)**
- [ ] CASH_BALANCE - 현금 비율 분석
- [ ] COIN_BALANCE - 보유량 기반 전략
- [ ] TOTAL_BALANCE - 포트폴리오 변화 추적

**[ ] State Category (4개)**
- [ ] AVG_BUY_PRICE - 평단가 기반 손익분기
- [ ] POSITION_SIZE - 동적 사이징, 리스크 조절
- [ ] PROFIT_AMOUNT - 절대 수익 추적
- [ ] PROFIT_PERCENT - 상대 수익률 분석

**[ ] Meta Category (2개)**
- [ ] META_PYRAMID_TARGET - 물타기 최적화
- [ ] META_TRAILING_STOP - 동적 손절 시스템

## 🏗️ 2단계: 변수별 개선 방안 분류

### 📈 **Type A: 파라미터 확장으로 해결**
간단한 설정 추가만으로 기능 확장 가능한 경우

**예시: RSI**
```yaml
기존: period=14, timeframe=1h
추가:
  - smoothing_method: [sma, ema, wma]
  - divergence_period: 20
  - overbought_level: 70
  - oversold_level: 30
```

### 🚀 **Type B: 새로운 고급 변수 필요**
복잡한 계산이나 다중 변수 조합이 필요한 경우

**예시: ATR → ATR_REGIME (변동성 레짐 감지)**
```yaml
새 변수: ATR_VOLATILITY_REGIME
purpose_category: volatility
parameters:
  - base_atr_period: 14
  - regime_detection_period: 50
  - threshold_multiplier: 2.0
output: [low_vol, normal_vol, high_vol, extreme_vol]
```

### 🔄 **Type C: 메타 변수 (다중 입력)**
여러 기존 변수를 조합한 복합 지표

**예시: MARKET_REGIME (시장 상태 종합 판단)**
```yaml
새 변수: MARKET_REGIME_DETECTOR
입력: ATR, RSI, VOLUME_SMA, MACD
출력: [trending_up, trending_down, sideways, volatile]
```

## 📋 3단계: 각 변수별 상세 분석 템플릿

```markdown
### [변수명] 분석

**현재 파라미터:**
- 기존: [current_params]

**도움말에서 발견된 고급 기능:**
1. [기능1]: [설명]
2. [기능2]: [설명]

**개선 방안:**
- [ ] Type A: 파라미터 확장
  - 추가 파라미터: [param_list]
  - 복잡도: 낮음/중간/높음

- [ ] Type B: 새 변수 필요
  - 새 변수명: [NEW_VARIABLE_NAME]
  - 이유: [complexity_reason]

**구현 우선순위:** 1-5점
**사용자 복잡도:** 낮음/중간/높음
**개발 난이도:** 낮음/중간/높음
```

## 🛠️ 4단계: 구현 아키텍처 설계

### 📁 **파일 구조 제안**
```
upbit_auto_trading/
├── domain/
│   └── trading_variables/
│       ├── calculators/           # 변수별 계산 로직
│       │   ├── basic/             # 기본 변수들
│       │   │   ├── atr_calculator.py
│       │   │   ├── rsi_calculator.py
│       │   │   └── ...
│       │   ├── advanced/          # 고급 변수들
│       │   │   ├── atr_regime_calculator.py
│       │   │   ├── market_regime_calculator.py
│       │   │   └── ...
│       │   └── meta/              # 메타 변수들
│       │       ├── pyramid_calculator.py
│       │       └── trailing_stop_calculator.py
│       └── parameter_definitions/  # 파라미터 정의
│           ├── basic_params.yaml
│           ├── advanced_params.yaml
│           └── meta_params.yaml
```

### 🔧 **계산기 클래스 구조**
```python
class AdvancedATRCalculator:
    def __init__(self, params: ATRParams):
        self.period = params.period
        self.timeframe = params.timeframe
        self.regime_period = params.regime_period
        self.threshold_multiplier = params.threshold_multiplier

    def calculate_basic_atr(self, data) -> float:
        """기본 ATR 계산"""

    def calculate_volatility_regime(self, data) -> str:
        """변동성 레짐 감지"""

    def calculate_normalized_atr(self, data) -> float:
        """정규화 ATR"""
```

## 📅 5단계: 구현 로드맵

### **Phase 1: 분석 및 설계 (1주)**
- [ ] 22개 변수 도움말 전수 분석
- [ ] Type A/B/C 분류 완료
- [ ] 우선순위 변수 5개 선정

### **Phase 2: 핵심 변수 구현 (1주)**
- [ ] ATR 고급 기능 구현
- [ ] RSI 확장 기능 구현
- [ ] MACD 히스토그램 분석
- [ ] 계산기 클래스 프레임워크 구축

### **Phase 3: 전체 적용 (1주)**
- [ ] 나머지 변수들 순차 적용
- [ ] 메타 변수 구현
- [ ] 통합 테스트 및 검증

## 🎯 성공 기준

### **기능적 요구사항**
- [ ] 모든 도움말의 고급 기능이 실제 구현됨
- [ ] 사용자 복잡도 최소화 (파라미터 3개 이하 유지)
- [ ] 백테스팅에서 정상 동작 확인

### **비기능적 요구사항**
- [ ] 계산 성능 저하 없음 (기존 대비 10% 이내)
- [ ] 메모리 사용량 증가 최소화
- [ ] 확장성 있는 아키텍처 구축

## ⚠️ 리스크 및 고려사항

### **기술적 리스크**
- 복잡한 계산으로 인한 성능 저하
- 파라미터 과다로 인한 사용자 혼란
- 기존 전략과의 호환성 문제

### **비즈니스 리스크**
- 고급 기능의 실제 매매 효과 불확실
- 개발 리소스 과투입 가능성
- 테스트 기간 부족으로 인한 버그

## 📝 다음 액션 아이템

1. **[ ] 즉시**: 첫 5개 변수 분석 시작 (ATR, RSI, MACD, SMA, VOLUME)
2. **[ ] 3일 내**: Type A/B/C 분류 기준 확정
3. **[ ] 1주 내**: 계산기 프레임워크 프로토타입 구현
4. **[ ] 2주 내**: 핵심 변수 5개 구현 완료

---

**프로젝트 상태**: 📋 계획 수립 완료, 분석 단계 진입 준비
**다음 마일스톤**: 변수별 상세 분석 완료 (1주 후)
