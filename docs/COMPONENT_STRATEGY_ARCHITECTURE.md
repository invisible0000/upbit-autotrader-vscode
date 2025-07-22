# 컴포넌트 기반 전략 시스템 아키텍처 개요

## 🎯 시스템 목표
기존 고정 전략 클래스의 한계를 극복하고, **아토믹 컴포넌트**를 자유롭게 조합하여 무한한 전략 생성이 가능한 시스템 구축

---

## 🔄 아키텍처 전환 (2025-07-22)

### ❌ 기존 시스템의 문제점
- **고정된 전략 클래스**: 새로운 전략마다 클래스 작성 필요
- **확장성 부족**: 기존 전략 수정이 어려움
- **조합의 한계**: 전략 간 조합 로직 복잡
- **유지보수성**: 코드 중복과 의존성 문제

### ✅ 새로운 컴포넌트 시스템
- **아토믹 컴포넌트**: 트리거와 액션의 독립적 구성요소
- **자유로운 조합**: 드래그&드롭으로 전략 구성
- **동적 확장**: 새 컴포넌트 쉽게 추가
- **시각적 관리**: GUI 기반 전략 메이커

---

## 🧩 컴포넌트 아키텍처

### 1️⃣ **트리거 컴포넌트 (Trigger Components)**
시장 상황을 감지하고 전략 실행 조건을 판단하는 구성요소

#### 📊 Price 카테고리 (3개)
- **PriceChangeTrigger**: 가격 변동율 감지
- **PriceBreakoutTrigger**: 가격 범위 돌파 감지  
- **PriceCrossoverTrigger**: 가격 기준선 교차 감지

#### 📈 Indicator 카테고리 (4개)
- **RSITrigger**: RSI 과매수/과매도 감지
- **MACDTrigger**: MACD 시그널 감지
- **BollingerBandTrigger**: 볼린저 밴드 터치 감지
- **MovingAverageCrossTrigger**: 이동평균 교차 감지

#### ⏰ Time 카테고리 (3개)
- **PeriodicTrigger**: 주기적 실행
- **ScheduledTrigger**: 특정 시간 실행
- **DelayTrigger**: 지연 후 실행

#### 📊 Volume 카테고리 (4개)
- **VolumeSurgeTrigger**: 거래량 급증 감지
- **VolumeDropTrigger**: 거래량 급락 감지
- **RelativeVolumeTrigger**: 상대적 거래량 감지
- **VolumeBreakoutTrigger**: 거래량 돌파 감지

### 2️⃣ **액션 컴포넌트 (Action Components)**
트리거 발생 시 실제 거래 행동을 수행하는 구성요소

#### 🛒 거래 액션 (3개)
- **MarketBuyAction**: 시장가 매수
- **MarketSellAction**: 시장가 매도  
- **PositionCloseAction**: 포지션 청산

### 3️⃣ **조건 컴포넌트 (Condition Components)**
트리거와 액션 사이의 추가 검증 로직 (향후 확장)

---

## 🏷️ 태그 기반 포지션 관리

### 포지션 태그 시스템
전략 간 충돌을 방지하고 안전한 거래를 보장하는 핵심 메커니즘

| 태그 | 설명 | 권한 |
|------|------|------|
| **AUTO** | 자동 전략이 생성한 포지션 | 자동 전략만 관리 |
| **MANUAL** | 수동으로 생성한 포지션 | 수동 조작만 가능 |
| **HYBRID** | 혼합 관리 포지션 | 자동+수동 모두 가능 |
| **LOCKED** | 잠금된 포지션 | 어떤 전략도 관리 불가 |

### 충돌 방지 메커니즘
```python
# 예: AUTO 태그 포지션에 대한 수동 매도 시도
if position.tag == "AUTO" and action_source == "MANUAL":
    raise PositionAccessDenied("AUTO 포지션은 수동 조작할 수 없습니다")
```

---

## 🎨 전략 메이커 UI 아키텍처

### 3-Panel 구조
1. **컴포넌트 팔레트**: 사용 가능한 트리거/액션 목록
2. **전략 캔버스**: 드래그&드롭으로 전략 구성
3. **설정 패널**: 선택된 컴포넌트의 상세 설정

### 상호작용 플로우
```
사용자 액션 → 컴포넌트 드래그 → 캔버스 드롭 → 자동 연결 → 설정 패널 활성화
```

---

## 💾 데이터 모델 아키텍처

### 레거시/컴포넌트 분리
```sql
-- 기존 모델 (레거시)
legacy_strategy
legacy_strategy_combination
legacy_combination_management_strategy

-- 새로운 컴포넌트 모델
component_strategy
strategy_execution  
strategy_template
component_configuration
```

### 컴포넌트 전략 구조
```json
{
  "id": "strategy-uuid",
  "name": "RSI 과매도 매수 전략",
  "triggers": [
    {
      "type": "rsi",
      "config": {"threshold": 30, "period": 14}
    }
  ],
  "actions": [
    {
      "type": "market_buy", 
      "config": {"amount_percent": 10}
    }
  ],
  "tags": ["AUTO"],
  "category": "technical",
  "difficulty": "beginner"
}
```

---

## 🔄 실행 엔진 아키텍처

### 이벤트 기반 실행
1. **시장 데이터 수신** → 모든 활성 전략의 트리거 검사
2. **트리거 발생** → 해당 전략의 액션 실행
3. **포지션 태그 검사** → 충돌 방지 확인
4. **거래 실행** → 실제 주문 처리
5. **실행 기록** → StrategyExecution 테이블에 저장

### 확장성 설계
- **플러그인 구조**: 새 컴포넌트 쉽게 추가
- **메타데이터 기반**: 동적 UI 생성
- **템플릿 시스템**: 사전 정의된 전략 패턴

---

## 🚀 향후 확장 계획

### 1단계: 조건 컴포넌트 추가
- **TimeCondition**: 특정 시간대 제한
- **BalanceCondition**: 잔고 조건 확인
- **RiskCondition**: 리스크 한도 검사

### 2단계: 고급 트리거 확장
- **PatternTrigger**: 차트 패턴 인식
- **SentimentTrigger**: 감정 분석 기반
- **NewsEventTrigger**: 뉴스 이벤트 감지

### 3단계: 머신러닝 통합
- **MLPredictionTrigger**: AI 예측 모델 연동
- **AutoOptimizeAction**: 자동 파라미터 최적화
- **RiskMLAction**: ML 기반 리스크 관리

---

## 📊 성능 및 모니터링

### 전략 성능 추적
- **실행 성공률**: 각 컴포넌트별 성공/실패 비율
- **수익성 분석**: 트리거-액션 조합별 성과
- **위험 지표**: 최대 낙폭, 샤프 비율 등

### 시스템 모니터링
- **컴포넌트 로드**: 각 컴포넌트 실행 빈도
- **메모리 사용량**: 전략 인스턴스 관리
- **지연시간**: 트리거 감지부터 액션 실행까지

---

**⚠️ 중요**: 이 아키텍처는 기존 고정 전략 시스템을 완전히 대체하는 차세대 설계입니다.
