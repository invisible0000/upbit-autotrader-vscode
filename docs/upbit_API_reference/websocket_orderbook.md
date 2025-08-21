# WebSocket 호가 (Orderbook) API 명세

## 📋 개요

업비트 WebSocket 호가 API는 실시간 매수/매도 호가 정보를 제공합니다. 지정가 주문의 현재 대기 상황과 시장 깊이(Market Depth)를 실시간으로 모니터링할 수 있습니다.

**엔드포인트**: `wss://api.upbit.com/websocket/v1`

## 🎯 주요 특징

### 호가 모아보기 (Level Grouping)
- **지원 마켓**: KRW 마켓 전용
- **기능**: 지정한 가격 단위로 호가를 그룹핑하여 조회
- **예시**: KRW-BTC에서 level=100000 설정 시 10만원 단위로 호가 집계
- **제한사항**: 지원하지 않는 단위 설정 시 데이터 수신 불가

### 호가 조회 단위 지정
- **지원 단위**: 1, 5, 15, 30개
- **기본값**: 30개 호가 쌍 (매수/매도)
- **설정 방법**: 페어 코드 뒤에 `.{unit}` 형식으로 지정
- **예시**: `KRW-BTC.15` (15개 호가 쌍)

## 📤 요청 메시지 형식

### 기본 구조
```json
[
  {
    "ticket": "unique-ticket-id"
  },
  {
    "type": "orderbook",
    "codes": ["KRW-BTC", "KRW-ETH"],
    "level": 10000
  },
  {
    "format": "DEFAULT"
  }
]
```

### 요청 파라미터

| 필드 | 타입 | 설명 | 필수 여부 | 기본값 |
|------|------|------|-----------|--------|
| `type` | String | `orderbook` 고정값 | Required | - |
| `codes` | List\<String\> | 수신할 페어 목록 (대문자) | Required | - |
| `level` | Double | 모아보기 단위 (KRW 마켓만) | Optional | 0 |
| `is_only_snapshot` | Boolean | 스냅샷만 제공 | Optional | false |
| `is_only_realtime` | Boolean | 실시간만 제공 | Optional | false |

### 고급 요청 예시

#### 페어별 다른 모아보기 단위
```json
[
  {
    "ticket": "orderbook-test"
  },
  {
    "type": "orderbook",
    "codes": ["KRW-BTC"],
    "level": 10000
  },
  {
    "type": "orderbook",
    "codes": ["KRW-ETH"],
    "level": 5000
  },
  {
    "format": "DEFAULT"
  }
]
```

#### 호가 개수 지정
```json
[
  {
    "ticket": "orderbook-depth"
  },
  {
    "type": "orderbook",
    "codes": ["KRW-BTC.15", "KRW-ETH.5"],
    "level": 0
  }
]
```

## 📥 응답 데이터 명세

### 응답 구조
```json
{
  "type": "orderbook",
  "code": "KRW-BTC",
  "timestamp": 1746601573804,
  "total_ask_size": 4.79158413,
  "total_bid_size": 2.65609625,
  "orderbook_units": [
    {
      "ask_price": 137002000,
      "bid_price": 137001000,
      "ask_size": 0.10623869,
      "bid_size": 0.03656812
    }
  ],
  "stream_type": "SNAPSHOT",
  "level": 0
}
```

### 필드 상세 설명

| 필드 | 약칭 | 설명 | 타입 | 예시 |
|------|------|------|------|------|
| `type` | `ty` | 데이터 타입 | String | orderbook |
| `code` | `cd` | 마켓 코드 | String | KRW-BTC |
| `total_ask_size` | `tas` | 호가 매도 총 잔량 | Double | 4.79158413 |
| `total_bid_size` | `tbs` | 호가 매수 총 잔량 | Double | 2.65609625 |
| `orderbook_units` | `obu` | 호가 목록 | List of Objects | - |
| `orderbook_units.ask_price` | `obu.ap` | 매도 호가 | Double | 137002000 |
| `orderbook_units.bid_price` | `obu.bp` | 매수 호가 | Double | 137001000 |
| `orderbook_units.ask_size` | `obu.as` | 매도 잔량 | Double | 0.10623869 |
| `orderbook_units.bid_size` | `obu.bs` | 매수 잔량 | Double | 0.03656812 |
| `timestamp` | `tms` | 타임스탬프 (ms) | Long | 1746601573804 |
| `level` | `lv` | 호가 모아보기 단위 | Double | 0 |
| `stream_type` | `st` | 스트림 타입 | String | SNAPSHOT/REALTIME |

## 💡 활용 예시

### 1. 기본 호가 모니터링
```python
import asyncio
import websockets
import json

async def monitor_orderbook():
    uri = "wss://api.upbit.com/websocket/v1"

    async with websockets.connect(uri) as websocket:
        subscribe_message = [
            {"ticket": "orderbook-monitor"},
            {
                "type": "orderbook",
                "codes": ["KRW-BTC", "KRW-ETH"],
                "level": 0
            }
        ]

        await websocket.send(json.dumps(subscribe_message))

        while True:
            data = await websocket.recv()
            orderbook = json.loads(data)

            print(f"[{orderbook['code']}] 스프레드: {orderbook['orderbook_units'][0]['ask_price'] - orderbook['orderbook_units'][0]['bid_price']:,}원")
```

### 2. 시장 깊이 분석
```python
def analyze_market_depth(orderbook_data):
    """호가 데이터로 시장 깊이 분석"""
    total_ask = orderbook_data['total_ask_size']
    total_bid = orderbook_data['total_bid_size']

    # 매수/매도 비율
    total_volume = total_ask + total_bid
    ask_ratio = (total_ask / total_volume) * 100
    bid_ratio = (total_bid / total_volume) * 100

    # 스프레드 계산
    best_ask = orderbook_data['orderbook_units'][0]['ask_price']
    best_bid = orderbook_data['orderbook_units'][0]['bid_price']
    spread = best_ask - best_bid
    spread_pct = (spread / best_bid) * 100

    return {
        'ask_ratio': ask_ratio,
        'bid_ratio': bid_ratio,
        'spread': spread,
        'spread_percentage': spread_pct
    }
```

### 3. 호가 모아보기 활용
```python
async def monitor_aggregated_orderbook():
    """10만원 단위로 호가 모아보기"""
    subscribe_message = [
        {"ticket": "aggregated-orderbook"},
        {
            "type": "orderbook",
            "codes": ["KRW-BTC"],
            "level": 100000  # 10만원 단위
        }
    ]

    # WebSocket 연결 및 데이터 수신
    # ...
```

## ⚠️ 주의사항

### 호가 모아보기 제한
- **KRW 마켓 전용**: BTC, USDT 마켓에서는 level=0만 지원
- **지원 단위 확인 필수**: [호가 정책 조회 API](https://docs.upbit.com/kr/reference/list-orderbook-instruments) 또는 [마켓별 주문 정책](https://docs.upbit.com/kr/docs/faq-market-policy) 참조
- **미지원 단위 설정 시**: 데이터 수신 불가

### 데이터 처리
- **호가 순서**: ask_price 오름차순, bid_price 내림차순
- **실시간 업데이트**: 호가 변동시마다 전체 호가창 데이터 전송
- **타임스탬프**: 밀리초 단위 Unix timestamp

### 성능 고려사항
- **대용량 데이터**: 30개 호가 쌍 기준 상당한 데이터량
- **주기적 전송**: 호가 변동이 빈번한 코인은 높은 전송 빈도
- **네트워크 대역폭**: 다수 코인 구독시 대역폭 사용량 증가

## 🔗 관련 API

- [호가 정책 조회](https://docs.upbit.com/kr/reference/list-orderbook-instruments)
- [마켓별 주문 정책](https://docs.upbit.com/kr/docs/faq-market-policy)
- [WebSocket 현재가 (Ticker)](./websocket_ticker.md)
- [WebSocket 체결 (Trade)](./websocket_trade.md)

## 📚 추가 자료

- [업비트 WebSocket 사용 안내](https://docs.upbit.com/kr/reference/websocket-guide)
- [업비트 API 개요](https://docs.upbit.com/kr/reference/api-overview)
- [요청 수 제한 정책](https://docs.upbit.com/kr/reference/rate-limits)

---

**마지막 업데이트**: 2025년 1월
**API 버전**: v1
**문서 버전**: 1.0
