# Trading Variables Schema 개선 완료 보고서

## 📋 변경 사항 요약

### 1. 🔧 `variable_id` 명명 규칙 통일
**문제점**: 기존 스키마에서 약어(`SMA`, `RSI`), 축약형(`STOCH`), 풀네임(`BOLLINGER_BANDS`) 등이 혼용됨

**개선 사항**:
- `STOCH` → `STOCHASTIC_OSCILLATOR` (업계 표준 전체 이름 사용)
- `STOCH_RSI` → `STOCHASTIC_RSI` (일관성 유지)
- `BOLLINGER_WIDTH` → `BOLLINGER_BANDS_WIDTH` (명확성 향상)
- 나머지 지표들은 이미 적절한 명명 규칙을 따름 (`RSI`, `MACD`, `SMA`, `EMA` 등)

### 2. 📊 파라미터 표준화 - `source` 필드 추가
**문제점**: 가격 기반 지표 중 일부만 `source` 파라미터를 가지고 있음

**추가된 `source` 파라미터**:
- `WMA` (가중이동평균)
- `ROC` (가격변동률)
- `WILLIAMS_R` (윌리엄스 %R)
- `BOLLINGER_BANDS` (기존 유지, 확인용)
- `BOLLINGER_BANDS_WIDTH` (새로 추가)
- `STANDARD_DEVIATION` (표준편차)
- `CCI` (상품채널지수 - hlc3 기본값 사용)
- `MACD` (새로 추가)

**표준 `source` 옵션**: `["open", "high", "low", "close", "hl2", "hlc3", "ohlc4"]`

### 3. 🛡️ 데이터 무결성 강화 주석 추가
**추가된 주석**:
```sql
-- ⚠️ 중요: 애플리케이션 레벨에서 파라미터 값의 숫자/타입 검증이 반드시 필요함
-- variable_parameters 테이블의 min_value, max_value, default_value는 TEXT 타입으로 저장되므로
-- Python 애플리케이션에서 parameter_type에 따른 적절한 타입 변환 및 범위 검증을 수행해야 함
```

### 4. 🎨 UI 텍스트 DB 관리 원칙 명시
**추가된 주석**:
```sql
-- UI 표시 텍스트(display_name_ko, description 등)를 DB에서 관리하여
-- 향후 지표 추가/수정 시 UI 코드 변경 없이 데이터만으로 확장 가능하도록 함.
```

### 5. 📈 추가 파라미터 정의 확장
**새로 추가된 지표별 파라미터**:

- **STOCHASTIC_RSI**: RSI 기간, 스토캐스틱 기간, %K 기간, %D 기간
- **WILLIAMS_R**: 기간, 데이터 소스 (hlc3 기본값)
- **PARABOLIC_SAR**: 시작 가속도, 증가값, 최대값
- **ICHIMOKU**: 전환선 기간, 기준선 기간, 선행스팬B 기간, 후행스팬 이동
- **VWAP**: 세션 타입 (daily, weekly, monthly, custom)
- **OBV**: 스무딩 적용 여부, 스무딩 기간 (선택적)
- **SUPERTREND**: ATR 기간, ATR 배수
- **SQUEEZE_MOMENTUM**: 볼린저 밴드 기간/배수, 켈트너 채널 기간/배수
- **PIVOT_POINTS**: 계산 방식, 시간틀

### 6. 🔄 스키마 버전 업데이트
- 버전: `1.1.0` → `1.2.0`
- 설명: "표준화 및 일관성 개선 - variable_id 명명 규칙 통일, source 파라미터 추가"

## 🎯 주요 개선 효과

1. **일관성**: 모든 지표의 `variable_id`가 통일된 명명 규칙을 따름
2. **유연성**: 가격 기반 지표들이 다양한 데이터 소스를 지원
3. **확장성**: 새로운 지표 추가 시 일관된 구조로 파라미터 정의 가능
4. **안정성**: 타입 검증에 대한 명확한 가이드라인 제시
5. **유지보수성**: UI 텍스트의 중앙 집중식 관리

## 📄 결과 파일
- **개선된 스키마**: `schema_improved.sql`
- **원본 스키마**: `schema.sql` (보존됨)

## 🔍 검증 권장사항
1. 기존 애플리케이션 코드에서 변경된 `variable_id` 참조 업데이트 필요
2. 새로 추가된 `source` 파라미터 처리 로직 구현
3. 파라미터 타입 검증 로직 강화
4. 지표 계산 엔진에서 확장된 파라미터 지원 확인
