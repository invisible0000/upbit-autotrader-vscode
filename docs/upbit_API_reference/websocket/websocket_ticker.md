# 업비트 WebSocket 현재가 (Ticker) API

> **출처**: [업비트 공식 문서 - WebSocket Ticker](https://docs.upbit.com/kr/reference/websocket-ticker)
> **문서 작성일**: 2025년 8월 21일
> **API 버전**: 최신 (2025년 기준)

## 개요

현재가(Ticker) 데이터를 WebSocket으로 실시간 수신하기 위한 API입니다. 스냅샷과 실시간 스트림 데이터를 모두 지원합니다.

## Request 메시지 형식

### 기본 구조

현재가 데이터 수신을 요청하기 위해서는 WebSocket 연결 이후 아래 구조의 JSON Object를 Data Type Object로 포함하여 전송해야 합니다.

| 필드명 | 타입 | 설명 | 필수여부 | 기본값 |
|--------|------|------|----------|--------|
| type | String | "ticker" (고정값) | Required | - |
| codes | List:String | 수신하고자 하는 페어 목록 (반드시 대문자) | Required | - |
| is_only_snapshot | Boolean | 스냅샷 시세만 제공 | Optional | false |
| is_only_realtime | Boolean | 실시간 시세만 제공 | Optional | false |

### 요청 예시

#### 기본 포맷 (DEFAULT)
```json
[
  {
    "ticket": "0e66c0ac-7e13-43ef-91fb-2a87c2956c49"
  },
  {
    "type": "ticker",
    "codes": ["KRW-BTC", "KRW-ETH"]
  },
  {
    "format": "DEFAULT"
  }
]
```

#### 간단 포맷 (SIMPLE_LIST)
```json
[
  {
    "ticket": "test-ticker-simple"
  },
  {
    "type": "ticker",
    "codes": ["KRW-BTC", "KRW-ETH"]
  },
  {
    "format": "SIMPLE_LIST"
  }
]
```

## 구독 데이터 명세

### 응답 필드 상세

| 필드명 | 축약형 | 설명 | 타입 | 예시 |
|--------|--------|------|------|------|
| type | ty | 데이터 항목 | String | "ticker" |
| code | cd | 페어 코드 | String | "KRW-BTC" |
| opening_price | op | 시가 | Double | 31883000 |
| high_price | hp | 고가 | Double | 32310000 |
| low_price | lp | 저가 | Double | 31855000 |
| trade_price | tp | 현재가 | Double | 32287000 |
| prev_closing_price | pcp | 전일 종가 | Double | 31883000.00000000 |

### 변동 관련 필드

| 필드명 | 축약형 | 설명 | 타입 | 가능값 |
|--------|--------|------|------|--------|
| change | c | 전일 종가 대비 가격 변동 방향 | String | RISE(상승), EVEN(보합), FALL(하락) |
| change_price | cp | 전일 대비 가격 변동의 절대값 | Double | 404000.00000000 |
| signed_change_price | scp | 전일 대비 가격 변동 값 | Double | 404000.00000000 |
| change_rate | cr | 전일 대비 등락율의 절대값 | Double | 0.0126713295 |
| signed_change_rate | scr | 전일 대비 등락율 | Double | 0.0126713295 |

### 거래량 관련 필드

| 필드명 | 축약형 | 설명 | 타입 | 비고 |
|--------|--------|------|------|------|
| trade_volume | tv | 가장 최근 거래량 | Double | - |
| acc_trade_volume | atv | 누적 거래량(UTC 0시 기준) | Double | - |
| acc_trade_volume_24h | atv24h | 24시간 누적 거래량 | Double | - |
| acc_trade_price | atp | 누적 거래대금(UTC 0시 기준) | Double | - |
| acc_trade_price_24h | atp24h | 24시간 누적 거래대금 | Double | - |

### 매수/매도 관련 필드

| 필드명 | 축약형 | 설명 | 타입 | 가능값 |
|--------|--------|------|------|--------|
| ask_bid | ab | 매수/매도 구분 | String | ASK(매도), BID(매수) |
| acc_ask_volume | aav | 누적 매도량 | Double | - |
| acc_bid_volume | abv | 누적 매수량 | Double | - |

### 시간 관련 필드

| 필드명 | 축약형 | 설명 | 타입 | 형식 |
|--------|--------|------|------|------|
| trade_date | tdt | 최근 거래 일자(UTC) | String | yyyyMMdd |
| trade_time | ttm | 최근 거래 시각(UTC) | String | HHmmss |
| trade_timestamp | ttms | 체결 타임스탬프(ms) | Long | - |
| timestamp | tms | 타임스탬프 (ms) | Long | - |

### 52주 관련 필드

| 필드명 | 축약형 | 설명 | 타입 | 형식 |
|--------|--------|------|------|------|
| highest_52_week_price | h52wp | 52주 최고가 | Double | - |
| highest_52_week_date | h52wdt | 52주 최고가 달성일 | String | yyyy-MM-dd |
| lowest_52_week_price | l52wp | 52주 최저가 | Double | - |
| lowest_52_week_date | l52wdt | 52주 최저가 달성일 | String | yyyy-MM-dd |

### 시장 상태 관련 필드

| 필드명 | 축약형 | 설명 | 타입 | 가능값 |
|--------|--------|------|------|--------|
| market_state | ms | 거래상태 | String | PREVIEW(입금지원), ACTIVE(거래지원가능), DELISTED(거래지원종료) |
| delisting_date | dd | 거래지원 종료일 | Date | - |
| market_warning | mw | 유의 종목 여부 | String | NONE(해당없음), CAUTION(투자유의) |
| stream_type | st | 스트림 타입 | String | SNAPSHOT(스냅샷), REALTIME(실시간) |

### Deprecated 필드 (사용 권장하지 않음)

| 필드명 | 축약형 | 설명 | 비고 |
|--------|--------|------|------|
| trade_status | ts | 거래상태 | 참조 대상에서 제외 권장 |
| market_state_for_ios | msfi | 거래 상태 | 참조 대상에서 제외 권장 |
| is_trading_suspended | its | 거래 정지 여부 | 참조 대상에서 제외 권장 |

## 응답 예시

### DEFAULT 포맷 응답
```json
{
  "type": "ticker",
  "code": "KRW-BTC",
  "opening_price": 31883000,
  "high_price": 32310000,
  "low_price": 31855000,
  "trade_price": 32287000,
  "prev_closing_price": 31883000.00000000,
  "acc_trade_price": 78039261076.51241000,
  "change": "RISE",
  "change_price": 404000.00000000,
  "signed_change_price": 404000.00000000,
  "change_rate": 0.0126713295,
  "signed_change_rate": 0.0126713295,
  "ask_bid": "ASK",
  "trade_volume": 0.03103806,
  "acc_trade_volume": 2429.58834336,
  "trade_date": "20230221",
  "trade_time": "074102",
  "trade_timestamp": 1676965262139,
  "acc_ask_volume": 1146.25573608,
  "acc_bid_volume": 1283.33260728,
  "highest_52_week_price": 57678000.00000000,
  "highest_52_week_date": "2022-03-28",
  "lowest_52_week_price": 20700000.00000000,
  "lowest_52_week_date": "2022-12-30",
  "market_state": "ACTIVE",
  "is_trading_suspended": false,
  "delisting_date": null,
  "market_warning": "NONE",
  "timestamp": 1676965262177,
  "acc_trade_price_24h": 228827082483.70729000,
  "acc_trade_volume_24h": 7158.80283560,
  "stream_type": "REALTIME"
}
```

## 사용시 주의사항

### 1. 페어 코드 형식
- 페어 코드는 **반드시 대문자**로 요청해야 합니다
- 형식: `{인용화폐}-{기준화폐}` (예: `KRW-BTC`, `USDT-ETH`)

### 2. 스트림 타입 옵션
- `is_only_snapshot: true`: 현재 상태의 스냅샷만 한 번 수신
- `is_only_realtime: true`: 변경 발생 시에만 실시간 데이터 수신
- 둘 다 `false` (기본값): 스냅샷 + 실시간 스트림 모두 수신

### 3. Deprecated 필드
다음 필드들은 향후 제거될 예정이므로 사용을 권장하지 않습니다:
- `trade_status` (ts)
- `market_state_for_ios` (msfi)
- `is_trading_suspended` (its)

### 4. 타임스탬프 관리
- `trade_timestamp`: 실제 체결 발생 시각 (밀리초)
- `timestamp`: 데이터 전송 시각 (밀리초)
- 모든 시간은 UTC 기준

## 개발 시 고려사항

### 1. 데이터 처리
```typescript
// 예시: TypeScript 타입 정의
interface TickerData {
  type: 'ticker';
  code: string;
  trade_price: number;
  change: 'RISE' | 'EVEN' | 'FALL';
  change_rate: number;
  acc_trade_volume_24h: number;
  // ... 기타 필드
}
```

### 2. 에러 처리
- WebSocket 연결 끊김 대응
- 잘못된 페어 코드 요청 시 처리
- 네트워크 지연으로 인한 데이터 순서 보장

### 3. 성능 최적화
- 필요한 페어만 구독하여 대역폭 절약
- 적절한 버퍼링으로 UI 업데이트 최적화
- 불필요한 JSON 파싱 최소화

## 관련 문서
- [WebSocket 사용 안내](https://docs.upbit.com/kr/reference/websocket-guide)
- [REST API Ticker](https://docs.upbit.com/kr/reference/list-tickers)
- [요청 수 제한(Rate Limits)](https://docs.upbit.com/kr/reference/rate-limits)
