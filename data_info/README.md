# 📊 Data Info - Trading Variables System

> **업비트 자동매매 시스템의 거래 변수 정의 및 관리**
> DDD 아키텍처 기반, 완전 분산형 파일 구조로 설계

---

## 🎯 Overview

이 디렉토리는 **Trading Variables System v3.0**의 핵심 데이터 정의를 관리합니다.
기존 indicators 중심에서 **포괄적인 거래 변수 시스템**으로 완전히 재설계되었습니다.

### 🔥 주요 특징
- **28개 거래 변수** - 8개 카테고리로 체계화
- **분산형 파일 구조** - 각 변수별 독립적 관리
- **완전한 문서화** - 정의, 파라미터, 도움말, 플레이스홀더, 가이드
- **DDD 호환** - Domain-driven Design 원칙 준수
- **트리거 빌더 최적화** - UI 컴포넌트와 완벽 연동

---

## 📁 Directory Structure

```
data_info/
├── 📄 README.md                    # 이 문서
├── 📁 trading_variables/           # 거래 변수 시스템 (메인)
│   ├── 📁 trend/                   # 추세 지표 (7개)
│   │   ├── 📁 sma/                 # 단순이동평균
│   │   ├── 📁 ema/                 # 지수이동평균
│   │   ├── 📁 bollinger_bands/     # 볼린저 밴드
│   │   ├── 📁 parabolic_sar/       # 파라볼릭 SAR
│   │   ├── 📁 ichimoku/            # 일목균형표
│   │   ├── 📁 pivot_points/        # 피벗 포인트
│   │   └── 📁 linear_regression/   # 선형 회귀
│   ├── 📁 momentum/                # 모멘텀 지표 (7개)
│   │   ├── 📁 rsi/                 # 상대강도지수
│   │   ├── 📁 macd/                # MACD
│   │   ├── 📁 stochastic/          # 스토캐스틱
│   │   ├── 📁 cci/                 # 상품채널지수
│   │   ├── 📁 williams_r/          # 윌리엄스 %R
│   │   ├── 📁 roc/                 # 변화율
│   │   └── 📁 tsi/                 # 진정한 강도 지수
│   ├── 📁 volume/                  # 거래량 지표 (4개)
│   │   ├── 📁 volume_sma/          # 거래량 이동평균
│   │   ├── 📁 volume_weighted_price/ # 거래량 가중 평균 가격
│   │   ├── 📁 on_balance_volume/   # 온 밸런스 볼륨
│   │   └── 📁 chaikin_money_flow/  # 차이킨 머니 플로우
│   ├── 📁 volatility/              # 변동성 지표 (4개)
│   │   ├── 📁 atr/                 # 평균 진정한 범위
│   │   ├── 📁 standard_deviation/  # 표준편차
│   │   ├── 📁 bollinger_width/     # 볼린저 밴드 폭
│   │   └── 📁 vix/                 # 변동성 지수
│   ├── 📁 price/                   # 가격 데이터 (2개)
│   │   ├── 📁 current_price/       # 현재가
│   │   └── 📁 price_change_rate/   # 가격 변화율
│   ├── 📁 capital/                 # 자본 관리 (2개)
│   │   ├── 📁 cash_balance/        # 현금 잔고
│   │   └── 📁 position_size/       # 포지션 크기
│   ├── 📁 state/                   # 상태 변수 (1개)
│   │   └── 📁 market_phase/        # 시장 국면
│   └── 📁 meta/                    # 메타 변수 (1개)
│       └── 📁 external_variable/   # 외부 변수
└── 📁 _archived/                   # 아카이브된 파일들
```

---

## 🔧 Variable File Structure

각 거래 변수는 **5개의 YAML 파일**로 완전히 정의됩니다:

```
{variable_name}/
├── 📄 definition.yaml        # 기본 정의 (ID, 이름, 카테고리, 복잡도)
├── 📄 parameters.yaml        # 파라미터 상세 정의
├── 📄 help_texts.yaml        # 간단 도움말 (툴팁용)
├── 📄 placeholders.yaml      # 입력 필드 플레이스홀더
└── 📄 help_guide.yaml        # 상세 가이드 문서
```

### 📋 파일별 역할

| 파일 | 용도 | 예시 |
|------|------|------|
| `definition.yaml` | 변수 기본 정보 | ID, 표시명, 카테고리, 복잡도 |
| `parameters.yaml` | 파라미터 정의 | 타입, 기본값, 범위, 검증 규칙 |
| `help_texts.yaml` | 간단 도움말 | 툴팁, 한줄 설명 |
| `placeholders.yaml` | UI 플레이스홀더 | 입력 필드 안내 문구 |
| `help_guide.yaml` | 상세 가이드 | 사용법, 예시, 주의사항 |

---

## 🎨 Categories & Variables

### 🔄 Trend (추세) - 7개
시장의 방향성과 추세를 분석하는 지표들
- `SMA` - 단순이동평균 (Simple Moving Average)
- `EMA` - 지수이동평균 (Exponential Moving Average)
- `BOLLINGER_BANDS` - 볼린저 밴드
- `PARABOLIC_SAR` - 파라볼릭 SAR
- `ICHIMOKU` - 일목균형표
- `PIVOT_POINTS` - 피벗 포인트
- `LINEAR_REGRESSION` - 선형 회귀

### ⚡ Momentum (모멘텀) - 7개
가격 변화의 속도와 강도를 측정하는 지표들
- `RSI` - 상대강도지수 (Relative Strength Index)
- `MACD` - MACD (Moving Average Convergence Divergence)
- `STOCHASTIC` - 스토캐스틱 오실레이터
- `CCI` - 상품채널지수 (Commodity Channel Index)
- `WILLIAMS_R` - 윌리엄스 %R
- `ROC` - 변화율 (Rate of Change)
- `TSI` - 진정한 강도 지수 (True Strength Index)

### 📊 Volume (거래량) - 4개
거래량 기반 분석 지표들
- `VOLUME_SMA` - 거래량 이동평균
- `VOLUME_WEIGHTED_PRICE` - 거래량 가중 평균 가격
- `ON_BALANCE_VOLUME` - 온 밸런스 볼륨
- `CHAIKIN_MONEY_FLOW` - 차이킨 머니 플로우

### 📈 Volatility (변동성) - 4개
시장 변동성을 측정하는 지표들
- `ATR` - 평균 진정한 범위 (Average True Range)
- `STANDARD_DEVIATION` - 표준편차
- `BOLLINGER_WIDTH` - 볼린저 밴드 폭
- `VIX` - 변동성 지수

### 💰 Price (가격) - 2개
기본 가격 데이터
- `CURRENT_PRICE` - 현재가
- `PRICE_CHANGE_RATE` - 가격 변화율

### 💼 Capital (자본) - 2개
자본 관리 관련 변수들
- `CASH_BALANCE` - 현금 잔고
- `POSITION_SIZE` - 포지션 크기

### 🎯 State (상태) - 1개
시장 상태 관련 변수들
- `MARKET_PHASE` - 시장 국면

### 🔧 Meta (메타) - 1개
시스템 메타 변수들
- `EXTERNAL_VARIABLE` - 외부 변수

---

## 🚀 Usage

### 트리거 빌더에서 사용
```python
# 변수 로딩
from upbit_auto_trading.application.services import TradingVariablesService

service = TradingVariablesService()
variables = service.get_all_variables()  # 28개 변수 로드

# 특정 카테고리 로딩
trend_variables = service.get_variables_by_category("trend")  # 7개
```

### 개별 변수 정의 확인
```python
# RSI 변수 정보
rsi_info = service.get_variable_info("RSI")
rsi_parameters = service.get_variable_parameters("RSI")
rsi_help = service.get_variable_help_text("RSI")
```

---

## 🔄 Migration History

### v3.0.0 (2025-08-15) - **현재 버전**
- ✅ **완전 재설계**: indicators → trading_variables
- ✅ **8개 카테고리**: trend, momentum, volume, volatility, price, capital, state, meta
- ✅ **28개 변수**: 포괄적 거래 변수 시스템
- ✅ **분산형 구조**: 각 변수별 5개 파일로 완전 정의
- ✅ **레거시 정리**: 구 시스템 완전 제거

### v2.x (Legacy)
- ❌ **indicators 중심**: 제한적 지표 시스템
- ❌ **중앙집중형**: 단일 YAML 파일들
- ❌ **확장성 부족**: 새 변수 추가 어려움

---

## 📝 Development Guidelines

### 새 변수 추가시
1. **카테고리 결정** - 8개 카테고리 중 적절한 위치 선택
2. **폴더 생성** - `trading_variables/{category}/{variable_id}/`
3. **5개 파일 작성** - definition, parameters, help_texts, placeholders, help_guide
4. **레지스트리 업데이트** - `trading_variables_registry.yaml` 수정
5. **테스트 추가** - UI 연동 테스트

### 파일 네이밍 규칙
- **폴더명**: snake_case (예: `bollinger_bands`)
- **변수 ID**: UPPER_CASE (예: `BOLLINGER_BANDS`)
- **표시명**: 한글 (예: `볼린저 밴드`)

### 파라미터 타입
- `integer` - 정수 (기간, 개수)
- `float` - 실수 (배율, 비율)
- `decimal` - 고정소수점 (가격, 금액)
- `boolean` - 불린 (활성화/비활성화)
- `enum` - 열거형 (옵션 선택)

---

## 🧪 Testing

```powershell
# 구조 검증
python validate_trading_variables_structure.py

# 트리거 빌더 테스트
python run_desktop_ui.py
# → 매매전략 관리 → 트리거 빌더

# 변수 로딩 테스트
pytest tests/test_trading_variables.py -v
```

---

## 📚 Related Documents

- [Trading Variables Registry](../trading_variables_registry.yaml) - 전체 변수 목록
- [DDD Architecture Guide](../docs/architecture.md) - 아키텍처 가이드
- [Trigger Builder Manual](../docs/trigger_builder.md) - 트리거 빌더 사용법
- [Development Guide](../docs/development.md) - 개발 가이드

---

**📅 Last Updated**: 2025-08-15
**📌 Version**: v3.0.0
**🎯 Status**: Production Ready - 트리거 빌더 완전 지원
