# 업비트 WebSocket 체결(Trade) API 참조 문서

> 업비트 WebSocket 체결 API의 완전한 기술 명세서 - LLM 최적화 버전

## 📋 개요

업비트 WebSocket 체결 API는 **실시간 체결 데이터**를 제공하며, 각 거래소에서 실제로 체결된 거래의 상세 정보를 실시간으로 수신할 수 있습니다.

### 🎯 주요 특징
- **실시간 체결 스트림**: 매수/매도 체결 즉시 수신
- **배치 구독 지원**: 여러 심볼 동시 구독 가능
- **체결 고유번호**: sequential_id로 중복 처리 방지
- **최우선 호가 포함**: 체결과 동시에 호가창 정보 제공

## 🔌 연결 정보

### 엔드포인트
```
wss://api.upbit.com/websocket/v1
```

### 프로토콜
- **WebSocket** (RFC 6455)
- **JSON 메시지** 형식
- **UTF-8** 인코딩

## 📝 Request 메시지 구조

### 기본 형식
```json
[
  {
    "ticket": "UNIQUE_TICKET_ID"
  },
  {
    "type": "trade",
    "codes": ["KRW-BTC", "KRW-ETH"],
    "is_only_snapshot": false,
    "is_only_realtime": false
  },
  {
    "format": "DEFAULT"
  }
]
```

### 📊 Request 필드 명세

| 필드명 | 타입 | 필수여부 | 기본값 | 설명 |
|--------|------|----------|--------|------|
| `type` | String | Required | - | **"trade"** 고정값 |
| `codes` | List:String | Required | - | 수신할 페어 목록 (대문자 필수) |
| `is_only_snapshot` | Boolean | Optional | false | 스냅샷 시세만 제공 |
| `is_only_realtime` | Boolean | Optional | false | 실시간 시세만 제공 |

### 🎯 구독 모드

| 설정 | `is_only_snapshot` | `is_only_realtime` | 동작 |
|------|-------------------|-------------------|------|
| **전체 모드** | false | false | 스냅샷 + 실시간 모두 수신 |
| **스냅샷만** | true | false | 현재 상태만 1회 수신 |
| **실시간만** | false | true | 실시간 체결만 수신 |

## 📥 Response 데이터 구조

### 🎯 체결 데이터 필드 완전 명세

| 필드명 | 단축명 | 타입 | 설명 | 예시 |
|--------|--------|------|------|------|
| `type` | `ty` | String | 데이터 타입 | "trade" |
| `code` | `cd` | String | 페어 코드 | "KRW-BTC" |
| `trade_price` | `tp` | Double | **체결 가격** | 100473000.0 |
| `trade_volume` | `tv` | Double | **체결량** | 0.00014208 |
| `ask_bid` | `ab` | String | **매수/매도 구분** | "ASK", "BID" |
| `prev_closing_price` | `pcp` | Double | 전일 종가 | 100571000.0 |
| `change` | `c` | String | 가격 변동 방향 | "RISE", "EVEN", "FALL" |
| `change_price` | `cp` | Double | 전일 대비 변동액 | 98000.0 |
| `trade_date` | `td` | String | 체결 일자(UTC) | "2024-10-31" |
| `trade_time` | `ttm` | String | 체결 시각(UTC) | "01:07:42" |
| `trade_timestamp` | `ttms` | Long | **체결 타임스탬프(ms)** | 1730336862047 |
| `timestamp` | `tms` | Long | **수신 타임스탬프(ms)** | 1730336862082 |
| `sequential_id` | `sid` | Long | **체결 고유번호** | 17303368620470000 |
| `best_ask_price` | `bap` | Double | 최우선 매도호가 | 100473000 |
| `best_ask_size` | `bas` | Double | 최우선 매도잔량 | 0.43139478 |
| `best_bid_price` | `bbp` | Double | 최우선 매수호가 | 100465000 |
| `best_bid_size` | `bbs` | Double | 최우선 매수잔량 | 0.01990656 |
| `stream_type` | `st` | String | 스트림 타입 | "SNAPSHOT", "REALTIME" |

### 🔍 핵심 필드 상세 설명

#### 1. **체결 식별 정보**
- `sequential_id`: 체결의 고유 식별자 (중복 처리 방지용)
- `trade_timestamp`: 실제 체결 발생 시간
- `timestamp`: WebSocket 메시지 수신 시간

#### 2. **체결 내용**
- `trade_price`: 체결된 가격
- `trade_volume`: 체결된 수량
- `ask_bid`: 체결 유형
  - `"ASK"`: 매도 체결 (시장가 매수가 매도호가에 체결)
  - `"BID"`: 매수 체결 (시장가 매도가 매수호가에 체결)

#### 3. **시장 상황**
- `best_ask_price/size`: 체결 직후 최우선 매도호가/잔량
- `best_bid_price/size`: 체결 직후 최우선 매수호가/잔량
- `prev_closing_price`: 전일 종가 기준 정보

## 📊 실제 응답 예시

### KRW-BTC 체결 데이터
```json
{
  "type": "trade",
  "code": "KRW-BTC",
  "timestamp": 1730336862082,
  "trade_date": "2024-10-31",
  "trade_time": "01:07:42",
  "trade_timestamp": 1730336862047,
  "trade_price": 100473000.00000000,
  "trade_volume": 0.00014208,
  "ask_bid": "BID",
  "prev_closing_price": 100571000.00000000,
  "change": "FALL",
  "change_price": 98000.00000000,
  "sequential_id": 17303368620470000,
  "best_ask_price": 100473000,
  "best_ask_size": 0.43139478,
  "best_bid_price": 100465000,
  "best_bid_size": 0.01990656,
  "stream_type": "SNAPSHOT"
}
```

### KRW-ETH 체결 데이터
```json
{
  "type": "trade",
  "code": "KRW-ETH",
  "timestamp": 1730336862120,
  "trade_date": "2024-10-31",
  "trade_time": "01:07:42",
  "trade_timestamp": 1730336862080,
  "trade_price": 3700000.00000000,
  "trade_volume": 0.02207517,
  "ask_bid": "BID",
  "prev_closing_price": 3695000.00000000,
  "change": "RISE",
  "change_price": 5000.00000000,
  "sequential_id": 17303368620800006,
  "best_ask_price": 3700000,
  "best_ask_size": 0.39101775,
  "best_bid_price": 3699000,
  "best_bid_size": 0.13499454,
  "stream_type": "SNAPSHOT"
}
```

## 🎯 스마트 라우팅 최적화 고려사항

### 📈 성능 특성
- **지연시간**: 체결 발생 후 10-50ms 내 수신
- **처리량**: 심볼당 초당 수백~수천 체결 처리 가능
- **배치 구독**: 최대 189개 KRW 페어 동시 구독 가능

### 🔧 구현 권장사항

#### 1. **중복 처리 방지**
```python
processed_trades = set()

def handle_trade(trade_data):
    sequential_id = trade_data['sequential_id']
    if sequential_id in processed_trades:
        return  # 중복 체결 무시
    processed_trades.add(sequential_id)
    # 체결 처리 로직
```

#### 2. **타임스탬프 활용**
```python
# 실제 체결 시간 vs 수신 시간 비교
def analyze_latency(trade_data):
    trade_time = trade_data['trade_timestamp']
    receive_time = trade_data['timestamp']
    latency = receive_time - trade_time
    return latency  # ms 단위 지연시간
```

#### 3. **체결 방향 분석**
```python
def analyze_market_pressure(trade_data):
    if trade_data['ask_bid'] == 'BID':
        return 'BUY_PRESSURE'  # 매수 압력
    else:
        return 'SELL_PRESSURE'  # 매도 압력
```

## ⚡ 실시간 처리 최적화

### 🎯 배치 구독 활용
```json
{
  "type": "trade",
  "codes": [
    "KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-DOT",
    "KRW-LINK", "KRW-LTC", "KRW-BCH", "KRW-EOS", "KRW-TRX"
  ]
}
```

### 📊 데이터 필터링
- **거래량 임계값**: 소액 체결 필터링
- **가격 범위**: 비정상 체결 감지
- **시간 윈도우**: 특정 시간대만 분석

## 🔒 에러 처리 및 재연결

### 일반적인 에러 상황
1. **연결 끊김**: 네트워크 불안정
2. **메시지 파싱 오류**: 잘못된 JSON
3. **구독 제한**: 과도한 심볼 구독

### 재연결 전략
```python
async def reconnect_with_backoff():
    retry_count = 0
    base_delay = 1.0

    while retry_count < MAX_RETRIES:
        try:
            await connect_websocket()
            return
        except Exception:
            delay = base_delay * (2 ** retry_count)
            await asyncio.sleep(min(delay, 30))
            retry_count += 1
```

## 📊 성능 벤치마크 (참고용)

| 항목 | 측정값 | 비고 |
|------|--------|------|
| **연결 설정 시간** | ~200ms | 초기 handshake |
| **체결 지연시간** | 10-50ms | 거래소 → WebSocket |
| **최대 동시 구독** | 189개 페어 | KRW 마켓 전체 |
| **메시지 처리율** | 1000+ msg/sec | 고빈도 체결 상황 |

## 🎯 Use Case별 활용 가이드

### 1. **실시간 가격 추적**
- `trade_price` 중심 모니터링
- 체결량 가중 평균 계산

### 2. **시장 심리 분석**
- `ask_bid` 비율 분석
- 체결량 분포 패턴 추적

### 3. **유동성 분석**
- `best_ask/bid_size` 모니터링
- 호가창 변화 추적

### 4. **지연 분석**
- `trade_timestamp` vs `timestamp` 비교
- 네트워크 지연 측정

---

## 📚 관련 문서
- [WebSocket 티커 API](./websocket_ticker.md)
- [WebSocket 호가 API](./websocket_orderbook.md)
- [WebSocket 연결 가이드](https://docs.upbit.com/kr/reference/websocket-guide)

---

*이 문서는 업비트 공식 API 문서를 기반으로 LLM 최적화하여 작성되었습니다.*
*최신 정보는 [업비트 개발자 센터](https://docs.upbit.com/kr/reference/websocket-trade)에서 확인하세요.*
