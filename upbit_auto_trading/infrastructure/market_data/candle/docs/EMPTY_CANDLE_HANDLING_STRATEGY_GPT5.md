# 빈 캔들(Empty Candle) 처리 전략 제안서(GPT-5)

본 문서는 거래가 없어 발생한 “빈 캔들”을 DB에 최소 정보로 기록하면서(중복 API 방지), 지표/차트/전략에 공급할 때는 신뢰할 수 있는 등간격(dense) 시계열로 제공하기 위한 일관된 정책을 제안합니다.

## 1) 배경과 목표
- 현재 수집기는 거래가 없는 시간 슬롯을 DB에 NULL 값과 참조 시간(`empty_copy_from_utc`)으로 저장해 “이미 확인한 시간대”를 표식하여 중복 API 요청을 막습니다.
- 그러나 소비 계층(지표/차트/전략)에서 빈 캔들을 포함할지 제외할지, 채움(fill) 정책을 어떻게 둘지에 따라 결과가 크게 달라집니다.
- 목표: 저장(중복 방지)과 제공(분석 안정성)을 분리하여, 저장은 가볍게/제공은 안전하게를 원칙으로 합니다.

## 2) 핵심 원칙(요약)
- DB 저장: 필수 시간 슬롯만 기록. 값은 NULL, 참조 시간 `empty_copy_from_utc`로 “빈 캔들”임을 명확히 표기.
- 제공 기본: “Dense + Fill-Forward + is_empty 플래그” 형태로 전달. 즉 모든 시간 슬롯을 포함하고, 값은 전진 채움, `is_empty=true`로 표시.
- 제공 옵션화: 사용처 요구에 따라 아래 3가지 모드 제공.
  - raw_sparse: 빈 캔들 제거(희소). 연구/특수 케이스 전용.
  - dense_filled [기본]: 모든 슬롯 포함 + 전진 채움 + `is_empty` 유지.
  - dense_null_strict: NULL 유지, 소비자가 직접 채움. 특수 분석용.

## 3) 저장 계층(수집/DB) 정책
- 저장 목적: “이 시간대는 확인됐다”는 사실과 경계(시간격)를 남겨 중복 API를 줄임.
- 레코드 예시(개념):
  - open/high/low/close/volume/trade_count = NULL
  - empty_copy_from_utc = 직전(또는 지정) 기준 캔들의 UTC 시간
  - is_empty 컬럼은 선택 사항. 저장 스키마를 바꾸지 않는다면 제공 시점에 파생 계산해도 무방
- 수집 완료 판단: “시간 슬롯 기준”으로 계산. 즉 빈 캔들도 슬롯 수에 포함(등간격 보장). 이는 수집기의 `effective_candle_count`/`should_complete_collection` 일관성을 높임.

## 4) 제공 계층(Provider) 정책
### 4.1 데이터 접근 인터페이스
- `candle_data_provider.py` 조회 API에 `empty_policy` 인자를 추가:
  - `FILL_FORWARD` [기본]: dense + 전진 채움 + `is_empty` 유지
  - `STRICT_NULL`: dense + 값은 NULL 유지, `is_empty` 유지
  - `DROP_EMPTY`: raw_sparse. 빈 캔들 제거(시간축 압축)

### 4.2 전진 채움(FILL_FORWARD) 규칙
- 가격: open/high/low/close = “직전 실거래 close”
- 거래량/건수: volume=0, trade_count=0
- 플래그: `is_empty=true`
- 시계열 시작부(선행 빈 캔들): 기본적으로 드랍하거나, 첫 실거래 close로 1회 초기화(프로바이더 옵션)
- 상위 프레임(일/주/월): 동일 정책. 경계 전환에서도 이전 close로 채움
- 부작용: ATR 같은 변동성 지표는 빈 구간의 고저가가 close와 같아 변동성 기여가 0 → 합리적. 전략 로직에서 `is_empty`를 이용해 “거래 기반 이벤트”는 건너뛰는 것을 권장

### 4.3 STRICT_NULL 규칙
- 모든 슬롯 포함, 값은 NULL 유지, `is_empty`=true
- 소비자가 직접 채움/보간을 하려는 특수 분석용

### 4.4 DROP_EMPTY 규칙
- 실거래 캔들만 반환(빈 캔들 제거). 시간축이 압축되어 연구용 외에는 비권장

## 5) 차트/지표 관점의 권장안
- 기본은 dense_filled. 이유:
  - 대부분의 지표는 등간격 시계열을 전제로 함(시간축 압축은 왜곡 유발)
  - 차트 축 일관성 유지(시간 경과=캔들 개수)
  - 멀티자산 비교/백테스트에도 동일 길이/간격이 유리
- 시각 표기: `is_empty=true`를 연한 색/점선 등으로 구분, volume=0
- 전략 로직: `is_empty`를 활용해 “거래 발생” 조건과 “시간 경과” 조건을 분리

## 6) 수집 로직과의 합의(Chunk/Overlap)
- 빈 캔들도 “슬롯 수”로 카운팅하여 수집 완료를 판단 → Overlap/Partial 케이스에서도 종료 조건이 명확
- API 호출 최적화: 중첩 분석 결과가 COMPLETE_OVERLAP라면 API 생략, count=0 가드 처리(이미 반영됨)
- 빈 캔들 DB 표식은 Overlap 재분석 시 불필요한 호출을 줄이는 근거 데이터로 활용

## 7) 구현 지침(요약)
- Provider 레벨에 정책 스위치 추가:
  - `get_candles(..., empty_policy: Literal['FILL_FORWARD','STRICT_NULL','DROP_EMPTY']='FILL_FORWARD')`
- 반환 모델에 `is_empty: bool` 추가 또는 파생 계산:
  - 저장 스키마 변경이 어렵다면, 열 값이 NULL이거나 volume=0 & empty_copy_from_utc 존재 시 `is_empty=true`로 판단
- 전진 채움 구현:
  - `empty_copy_from_utc` 또는 “직전 실거래 close”를 참조하여 가격 채움
  - 시작부 처리: 옵션(`drop_leading_empty=True` 등)으로 제어

## 8) 테스트 체크리스트
- 길이/간격: 요청한 기간의 슬롯 수와 반환 배열의 길이가 정확히 일치(dense 모드)
- 지표 안정성: EMA/RSI/ATR 등 결과가 시간축 일관성 하에서 재현 가능
- 차트 일관성: 시간축이 경계(일/주/월)에서도 깨지지 않음
- 시작부 정책: 선행 빈 캔들 처리(드랍/초기화)가 명세대로 동작
- `is_empty`·volume=0: 빈 슬롯 표기가 정확, 전략 분기 로직 검증

## 9) 예시(개념)
```
UTC                 open  high  low   close  volume  is_empty  note
2025-01-01 00:00    100   101   99    100    10      false     실거래
2025-01-01 00:01    100   100   100   100    0       true      빈 슬롯(FILL_FORWARD)
2025-01-01 00:02    100   100   100   100    0       true      빈 슬롯(FILL_FORWARD)
2025-01-01 00:03    101   102   100   101    7       false     실거래
```
STRICT_NULL 모드에서는 빈 슬롯의 open/high/low/close/volume이 NULL로 유지되며, DROP_EMPTY 모드에서는 00:01/00:02 레코드가 제거되어 시간축이 압축됩니다(권장 아님).

## 10) 마이그레이션 메모
- 저장 스키마를 바꾸지 않고도 적용 가능(제공 시점에서 `is_empty` 파생)
- 저장 정책은 그대로 유지(중복 방지 표식 역할에 최적), 소비 정책만 안전한 기본값으로 정렬

---
문의/보완 필요 시 `candle_data_provider.py` 설계에 맞춰 `empty_policy` 인터페이스 상세와 테스트 케이스(지표 결과/차트 렌더링/리샘플링 조합)를 추가로 제시하겠습니다.
