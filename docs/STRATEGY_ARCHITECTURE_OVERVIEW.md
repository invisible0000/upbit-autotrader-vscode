# 전략 관리 시스템 아키텍처 개요

## 🎯 시스템 목표
**원자적 전략 빌더**를 통해 누구나 쉽게 강력한 매매 전략을 만들고, 즉시 백테스트하여 검증할 수 있는 플랫폼 구축

---

## 🧩 원자적 컴포넌트 아키텍처 (Atomic Component Architecture)

### 🏗️ **핵심 구조: Variable → Condition → Action → Rule → Strategy**

#### 1️⃣ **Variable (변수)**
- **목적**: RSI, 가격, 시간 등 기본 데이터 소스
- **특징**: 실시간 업데이트되는 원자적 데이터 단위
- **예시**: `rsi_14`, `current_price`, `volume_24h`

#### 2️⃣ **Condition (조건)**
- **목적**: Variable에 대한 논리적 판단 기준
- **특징**: True/False 결과를 반환하는 독립적 판단 로직
- **예시**: `rsi_14 < 20`, `price > moving_average_20`

#### 3️⃣ **Action (액션)**
- **목적**: 조건 만족 시 실행할 구체적 행동
- **특징**: 매수/매도/청산 등 실제 거래 명령
- **예시**: `market_buy(5%)`, `market_sell(100%)`, `trailing_stop(3%)`

#### 4️⃣ **Rule (규칙)**
- **목적**: Condition + Action의 조합으로 구성된 단일 매매 규칙
- **특징**: "만약 X 조건이면 Y 행동" 형태의 완전한 로직
- **예시**: "RSI < 20이면 5% 매수", "수익률 > 10%이면 전량 매도"

#### 5️⃣ **Strategy (전략)**
- **목적**: 여러 Rule들의 조합으로 구성된 완전한 매매 전략
- **특징**: 진입부터 청산까지 모든 시나리오 커버
- **예시**: "7규칙 기본 전략" (RSI 진입 + 불타기 + 트레일링 스탑 등)

---

## � **Phase 1 완료: 원자적 전략 빌더 시스템**

## 🎯 **Phase 1 완료: 원자적 전략 빌더 시스템**

### ✅ **구현 완료 (2025-07-23)**

- **핵심 시스템**: `ui_prototypes/atomic_strategy_components.py`
- **UI 구현**: `ui_prototypes/atomic_strategy_builder_ui.py`  
- **검증된 예제**: `ui_prototypes/seven_rule_strategy_example.py`
- **사용자 가이드**: `ui_prototypes/basic_7_rule_strategy_guide.md`

### 🚀 **다음 단계 (Phase 2)**

1. **DB 스키마 설계** - 원자적 전략 영속성
2. **UI-DB 연동** - 저장/로드 기능 구현
3. **기존 시스템 통합** - 레거시 컴포넌트와 연동
4. **백테스트 엔진** - 성과 검증 시스템

---

## 📚 **레거시 시스템 (참고용)**

### 🎭 역할 기반 전략 분류 (Role-Based Strategy Classification)

### 📈 **진입 전략 (Entry Strategies)**

| 전략명 | 역할 | 신호 타입 | 설명 |
|-------|------|-----------|------|
| 이동평균 교차 | ENTRY | BUY/SELL | 골든크로스/데드크로스 신호 |
| RSI 과매수/과매도 | ENTRY | BUY/SELL | RSI 30/70 돌파 신호 |
| 볼린저 밴드 | ENTRY | BUY/SELL | 밴드 터치 후 반전 신호 |
| MACD 교차 | ENTRY | BUY/SELL | MACD 라인과 시그널 라인 교차 |
| 스토캐스틱 | ENTRY | BUY/SELL | 과매수/과매도 구간 신호 |
| 변동성 돌파 | ENTRY | BUY/SELL | 변동성 기반 돌파 신호 |

### � **증액 전략 (Scale-In Strategies)**
| 전략명 | 역할 | 신호 타입 | 설명 |
|-------|------|-----------|------|
| 상승 피라미딩 | SCALE_IN | ADD_BUY | 수익 발생 시 추가 매수 |
| 하락 물타기 | SCALE_IN | ADD_BUY | 손실 발생 시 평단가 낮추기 |

### �🛡️ **관리 전략 (Management Strategies)**
| 전략명 | 역할 | 신호 타입 | 설명 |
|-------|------|-----------|------|
| 고정 손절 | EXIT | STOP_LOSS | 고정 손절률 적용 |
| 트레일링 스탑 | EXIT | TRAILING | 수익 추적 손절 |
| 목표 익절 | EXIT | TAKE_PROFIT | 목표 수익률 달성 시 익절 |
| 부분 익절 | SCALE_OUT | PARTIAL_EXIT | 단계별 부분 매도 |
| 시간 기반 청산 | EXIT | TIME_EXIT | 시간 경과 후 강제 청산 |
| 변동성 기반 관리 | MANAGEMENT | VOLATILITY | 변동성에 따른 포지션 조정 |

---

## 🔗 조합 전략의 핵심 메커니즘

### ⚙️ **상태 관리 규칙 (State Management Rules)**
```python
state_rules = {
    "NO_POSITION": ["ENTRY", "RISK_FILTER"],     # 포지션 없을 때: 진입 신호만 감시
    "IN_POSITION": ["EXIT", "SCALE_IN", "SCALE_OUT"]  # 포지션 있을 때: 관리 신호만 감시
}
```

### ⚡ **충돌 해결 규칙 (Conflict Resolution Rules)**
1. **우선순위 기반 (PRIORITY_BASED)**
   - `EXIT > SCALE_OUT > SCALE_IN > ENTRY` 순서
   - 보수적 접근: 안전한 선택 우선

2. **가중치 합계 (WEIGHTED_SUM)**  
   - 각 전략의 신뢰도 점수 합산
   - 임계값 초과 시에만 신호 채택

3. **다수결 (VOTING)**
   - 동일 역할 전략들의 투표
   - 과반수 이상 동의 시 신호 실행

### 🛡️ **유효성 검증 (Validation Logic)**
```python
required_roles = ["ENTRY", "EXIT"]  # 필수 역할
validation_status = "VALID" | "WARNING" | "INVALID"
```

---

## 📊 데이터 흐름 (Data Flow)

```
개별 전략 → 신호 생성 → 조합 규칙 적용 → 최종 신호 → 포트폴리오 실행
     ↑              ↑               ↑             ↑            ↑
  시장 데이터    역할 분류      충돌 해결      우선순위 적용   리스크 관리
```

---

## 🎨 UI 구조 매핑

### 📱 **3탭 구조**
1. **진입 전략 탭**: 개별 진입 전략 CRUD
2. **관리 전략 탭**: 개별 관리 전략 CRUD  
3. **전략 조합 탭**: 조합 생성 및 관리

### 🔄 **상호작용 패턴**
- **탭 1,2 → 탭 3**: 개별 전략들이 조합의 재료가 됨
- **탭 3 → 실행**: 완성된 조합이 실제 매매에 활용
- **백테스팅**: 모든 계층에서 성능 검증 가능

---

## 🚀 확장성 고려사항

### 📈 **수평적 확장**
- 새로운 개별 전략 추가 용이
- 플러그인 방식의 모듈 아키텍처

### 📊 **수직적 확장**  
- 조합 전략 → 포트폴리오 → 멀티 포트폴리오
- 계층별 독립적 스케일링

### 🔧 **유지보수성**
- 각 계층의 독립적 수정 가능
- 단위 테스트 및 통합 테스트 분리

---

> **💡 핵심 철학**: "복잡함을 단순함의 조합으로, 단순함을 재사용 가능한 블록으로"
