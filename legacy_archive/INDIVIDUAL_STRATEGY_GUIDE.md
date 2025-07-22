# 개별 전략 속성 정의 및 관리 가이드

## 📋 개요

개별 전략은 **단일 매매 아이디어**를 구현하는 최소 단위로, 독립적으로 실행 가능하며 조합 가능한 모듈화된 컴포넌트입니다.

---

## 🏷️ 핵심 속성 (Core Attributes)

### 1. **식별 속성 (Identification)**

| 속성명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| `strategy_id` | string | ✅ | 시스템 내 유일한 식별자 | "strategy_001", "rsi_reversal_v2" |
| `strategy_name` | string | ✅ | 사용자 친화적 이름 | "RSI 과매수/과매도", "이동평균 교차" |
| `strategy_type` | string | ✅ | 전략 분류 코드 | "rsi_reversal", "moving_average_cross" |
| `version` | string | ❌ | 전략 버전 | "1.0.0", "2.1.3" |

### 2. **역할 속성 (Role Classification)**

| 속성명 | 타입 | 필수 | 설명 | 가능한 값 |
|--------|------|------|------|-----------|
| `role` | enum | ✅ | 전략의 역할 분류 | `ENTRY`, `EXIT`, `SCALE_IN`, `SCALE_OUT`, `RISK_FILTER` |
| `signal_type` | enum | ✅ | 생성하는 신호 타입 | `BUY`, `SELL`, `STOP_LOSS`, `TAKE_PROFIT`, `TRAILING` |
| `market_phase` | enum | ❌ | 적합한 시장 상황 | `TRENDING`, `SIDEWAYS`, `VOLATILE`, `ALL` |

### 3. **기술적 속성 (Technical Specifications)**

| 속성명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| `parameters` | dict | ✅ | 전략 파라미터 | `{"period": 14, "threshold": 70}` |
| `indicators_required` | list | ✅ | 필요한 기술적 지표 | `["RSI", "SMA", "VOLUME"]` |
| `timeframe_support` | list | ❌ | 지원하는 시간프레임 | `["1m", "5m", "1h", "1d"]` |
| `min_history_required` | int | ✅ | 최소 필요 히스토리 | `50` (50개 봉) |

### 4. **동작 속성 (Behavioral Attributes)**

| 속성명 | 타입 | 필수 | 설명 | 기본값 |
|--------|------|------|------|--------|
| `is_enabled` | bool | ✅ | 활성화 상태 | `true` |
| `confidence_score` | float | ❌ | 신뢰도 점수 (0.0-1.0) | `0.5` |
| `risk_level` | enum | ❌ | 리스크 수준 | `LOW`, `MEDIUM`, `HIGH` |
| `execution_priority` | int | ❌ | 실행 우선순위 (낮을수록 높음) | `5` |

### 5. **메타데이터 (Metadata)**

| 속성명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| `description` | string | ❌ | 전략 설명 | "RSI 70 이상에서 매도, 30 이하에서 매수" |
| `author` | string | ❌ | 작성자 | "system", "user_123" |
| `created_at` | datetime | ✅ | 생성 일시 | `2024-01-15T10:30:00Z` |
| `updated_at` | datetime | ✅ | 최종 수정 일시 | `2024-01-20T15:45:00Z` |
| `tags` | list | ❌ | 태그 목록 | `["momentum", "mean_reversion", "scalping"]` |

---

## 🎭 역할별 전략 분류 (Role-Based Classification)

### 📈 **진입 전략 (Entry Strategies)**

**공통 특징:**
- `role = "ENTRY"`
- `signal_type = "BUY" | "SELL"`
- 포지션이 없는 상태에서만 활성화

**세부 분류:**

#### 📊 **추세 추종형 (Trend Following)**
```yaml
전략 예시:
  - 이동평균 교차: 골든크로스/데드크로스
  - MACD 교차: MACD와 시그널 라인 교차
  - 변동성 돌파: 전일 변동성 기준 돌파
  
특징:
  - market_phase: TRENDING
  - risk_level: MEDIUM
  - confidence_score: 0.6-0.8
```

#### 🔄 **평균 회귀형 (Mean Reversion)**
```yaml
전략 예시:
  - RSI 과매수/과매도: RSI 30/70 기준
  - 볼린저 밴드: 밴드 터치 후 반전
  - 스토캐스틱: %K, %D 교차
  
특징:
  - market_phase: SIDEWAYS
  - risk_level: HIGH
  - confidence_score: 0.4-0.6
```

### 🛡️ **관리 전략 (Management Strategies)**

**공통 특징:**
- `role = "EXIT" | "SCALE_IN" | "SCALE_OUT"`
- 포지션이 있는 상태에서만 활성화

**세부 분류:**

#### 🚨 **손절 전략 (Stop Loss)**
```yaml
전략 예시:
  - 고정 손절: 진입가 대비 고정 비율
  - 트레일링 스탑: 최고가 추적 손절
  - 변동성 기반 손절: ATR 기준 동적 손절
  
특징:
  - role: EXIT
  - signal_type: STOP_LOSS
  - execution_priority: 1 (최고 우선순위)
```

#### 💰 **익절 전략 (Take Profit)**
```yaml
전략 예시:
  - 목표 익절: 고정 수익률 달성 시
  - 부분 익절: 단계별 부분 매도
  - 지표 기반 익절: RSI/MACD 신호 기준
  
특징:
  - role: EXIT | SCALE_OUT
  - signal_type: TAKE_PROFIT
  - execution_priority: 3-5
```

---

## 📊 파라미터 설계 가이드

### 🔢 **파라미터 타입별 속성**

#### **수치형 파라미터 (Numeric Parameters)**
```python
parameter_schema = {
    "period": {
        "type": "int",
        "default": 14,
        "min": 2,
        "max": 100,
        "description": "계산 기간",
        "validation": "range_check"
    },
    "threshold": {
        "type": "float", 
        "default": 70.0,
        "min": 0.0,
        "max": 100.0,
        "description": "임계값",
        "validation": "range_check"
    }
}
```

#### **선택형 파라미터 (Choice Parameters)**
```python
parameter_schema = {
    "ma_type": {
        "type": "choice",
        "default": "SMA",
        "options": ["SMA", "EMA", "WMA"],
        "description": "이동평균 타입",
        "validation": "choice_check"
    },
    "signal_mode": {
        "type": "choice",
        "default": "cross",
        "options": ["cross", "level", "divergence"],
        "description": "신호 발생 모드",
        "validation": "choice_check"
    }
}
```

#### **불린형 파라미터 (Boolean Parameters)**
```python
parameter_schema = {
    "use_volume_filter": {
        "type": "bool",
        "default": False,
        "description": "거래량 필터 사용 여부",
        "validation": "bool_check"
    }
}
```

---

## 🔍 유효성 검증 (Validation Rules)

### ✅ **필수 검증 항목**

1. **속성 완결성 검증**
   ```python
   required_fields = [
       "strategy_id", "strategy_name", "strategy_type", 
       "role", "signal_type", "parameters", "indicators_required"
   ]
   ```

2. **파라미터 유효성 검증**
   ```python
   def validate_parameters(params, schema):
       for key, value in params.items():
           param_config = schema.get(key)
           if not param_config:
               raise ValidationError(f"Unknown parameter: {key}")
           
           # 타입 검증
           if param_config["type"] == "int" and not isinstance(value, int):
               raise ValidationError(f"Parameter {key} must be integer")
           
           # 범위 검증
           if "min" in param_config and value < param_config["min"]:
               raise ValidationError(f"Parameter {key} below minimum")
   ```

3. **역할 일관성 검증**
   ```python
   role_signal_mapping = {
       "ENTRY": ["BUY", "SELL"],
       "EXIT": ["STOP_LOSS", "TAKE_PROFIT", "TRAILING"],
       "SCALE_IN": ["BUY"],
       "SCALE_OUT": ["SELL", "TAKE_PROFIT"]
   }
   
   def validate_role_consistency(role, signal_type):
       allowed_signals = role_signal_mapping.get(role, [])
       if signal_type not in allowed_signals:
           raise ValidationError(f"Signal type {signal_type} not allowed for role {role}")
   ```

---

## 🏭 팩토리 패턴 구현

### 🏗️ **전략 팩토리 구조**

```python
class StrategyFactory:
    """전략 생성을 담당하는 팩토리 클래스"""
    
    def __init__(self):
        self.strategy_registry = {}
        self.parameter_schemas = {}
    
    def register_strategy(self, strategy_type: str, strategy_class: type, schema: dict):
        """전략 클래스와 파라미터 스키마 등록"""
        self.strategy_registry[strategy_type] = strategy_class
        self.parameter_schemas[strategy_type] = schema
    
    def create_strategy(self, strategy_config: dict) -> StrategyInterface:
        """전략 설정으로부터 전략 인스턴스 생성"""
        strategy_type = strategy_config["strategy_type"]
        
        # 등록된 전략인지 확인
        if strategy_type not in self.strategy_registry:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        # 파라미터 검증
        schema = self.parameter_schemas[strategy_type]
        self.validate_parameters(strategy_config["parameters"], schema)
        
        # 전략 인스턴스 생성
        strategy_class = self.strategy_registry[strategy_type]
        return strategy_class(strategy_config)
```

---

## 🎯 베스트 프랙티스 (Best Practices)

### ✨ **DO's (권장사항)**

1. **명확한 명명 규칙**
   - `strategy_id`: snake_case 사용 (`rsi_reversal_v2`)
   - `strategy_name`: 사용자 친화적 한글명 ("RSI 과매수/과매도")

2. **파라미터 기본값 설정**
   - 모든 파라미터에 안전한 기본값 제공
   - 일반적으로 통용되는 표준값 사용 (RSI: 14, 볼밴: 20)

3. **상세한 설명 작성**
   - 전략의 동작 원리 명시
   - 파라미터별 영향도 설명
   - 적합한 시장 환경 가이드

### ❌ **DON'Ts (금지사항)**

1. **하드코딩 금지**
   - 파라미터는 반드시 설정 가능하게 구현
   - 매직넘버 사용 금지

2. **과도한 복잡성 지양**
   - 하나의 전략은 하나의 아이디어만 구현
   - 여러 로직이 필요하면 별도 전략으로 분리

3. **상태 의존성 최소화**
   - 전략 간 직접적인 상태 공유 금지
   - 필요 시 조합 레벨에서 상호작용 정의

---

## 📈 확장성 고려사항

### 🔮 **미래 확장 포인트**

1. **동적 파라미터 최적화**
   - 머신러닝 기반 파라미터 자동 튜닝
   - 시장 상황별 적응형 파라미터

2. **고급 신호 처리**
   - 신호 강도/신뢰도 스코어링
   - 다차원 신호 벡터 지원

3. **성능 메트릭 내장**
   - 전략별 성과 추적
   - 실시간 성과 모니터링

### 🔧 **기술적 확장성**

1. **플러그인 아키텍처**
   - 런타임 전략 로딩
   - 서드파티 전략 모듈 지원

2. **분산 처리 지원**
   - 병렬 신호 계산
   - 클러스터 환경 대응

---

> **💡 핵심 원칙**: "각 전략은 독립적이고 재사용 가능한 레고 블록처럼 설계되어야 합니다."
