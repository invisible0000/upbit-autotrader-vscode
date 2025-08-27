# 업비트 API 통합 참조 가이드

## 🔗 API 연결 정보

### 업비트 서버 엔드포인트
```
REST API:     https://api.upbit.com
WebSocket:    wss://api.upbit.com/websocket/v1
```

### 인증 방식
- **Public API**: 인증 불필요
- **Private API**: JWT 토큰 (HMAC-SHA256 서명)

## 📡 WebSocket API v5.0 참조

### Public WebSocket 클라이언트
**파일**: `upbit_websocket_public_client.py`
**티켓 제한**: 3개

#### 구독 가능한 데이터
| 데이터 타입 | API 필드명 | 한글명 | 샘플 코드 |
|------------|------------|--------|----------|
| `ticker` | 현재가 정보 | 실시간 시세 | KRW-BTC |
| `trade` | 체결 정보 | 실시간 체결 | KRW-BTC |
| `orderbook` | 호가 정보 | 실시간 호가 | KRW-BTC |
| `candle` | 캔들 정보 | 실시간 캔들 | KRW-BTC |

#### 메서드 사용법
```python
# 클라이언트 생성
client = UpbitWebSocketPublicV5()

# 단일 구독
await client.subscribe_ticker(['KRW-BTC'])

# 다중 구독 (티켓 관리 자동)
await client.subscribe_multiple([
    ('ticker', ['KRW-BTC', 'KRW-ETH']),
    ('orderbook', ['KRW-BTC'])
])

# 구독 해제
await client.unsubscribe_ticker(['KRW-BTC'])

# 연결 관리
await client.connect()
await client.disconnect()
```

### Private WebSocket 클라이언트
**파일**: `upbit_websocket_private_client.py`
**티켓 제한**: 2개

#### 구독 가능한 데이터
| 데이터 타입 | API 필드명 | 한글명 | 인증 필요 |
|------------|------------|--------|----------|
| `myOrder` | 내 주문 정보 | 실시간 주문상태 | ✅ |
| `myAsset` | 내 자산 정보 | 실시간 잔고변화 | ✅ |

#### 메서드 사용법
```python
# 클라이언트 생성 (자동 인증)
client = UpbitWebSocketPrivateV5()

# Private 구독
await client.subscribe_my_orders()
await client.subscribe_my_assets()

# 구독 해제
await client.unsubscribe_my_orders()
await client.unsubscribe_my_assets()
```

### WebSocket 모델 구조
**파일**: `models.py` (Pydantic V2)

#### 공통 응답 필드
```python
class BaseResponse:
    type: str          # 메시지 타입
    code: str          # 마켓 코드 (예: KRW-BTC)
    timestamp: int     # 타임스탬프
```

#### Ticker 응답 모델
```python
class TickerResponse:
    trade_price: float        # 현재가
    change: str              # 전일 대비 ('RISE'|'EVEN'|'FALL')
    change_price: float      # 전일 대비 변화 절댓값
    change_rate: float       # 전일 대비 변화율
    acc_trade_volume_24h: float  # 24시간 누적 거래량
    acc_trade_price_24h: float   # 24시간 누적 거래대금
```

## 🌐 REST API 참조

### Public REST API

#### 1. 마켓 정보
```python
# 전체 마켓 코드 조회
GET /v1/market/all
# 응답: [{"market": "KRW-BTC", "korean_name": "비트코인"}, ...]

# 현재가 정보
GET /v1/ticker?markets=KRW-BTC,KRW-ETH
# 응답: [{"market": "KRW-BTC", "trade_price": 95000000}, ...]
```

#### 2. 캔들 정보
```python
# 분봉 (1, 3, 5, 15, 10, 30, 60, 240분)
GET /v1/candles/minutes/1?market=KRW-BTC&count=200

# 일봉
GET /v1/candles/days?market=KRW-BTC&count=30

# 주봉/월봉
GET /v1/candles/weeks?market=KRW-BTC&count=10
GET /v1/candles/months?market=KRW-BTC&count=10
```

#### 3. 체결/호가 정보
```python
# 체결 내역
GET /v1/trades/ticks?market=KRW-BTC&count=100&cursor=시간기준

# 호가 정보
GET /v1/orderbook?markets=KRW-BTC
```

### Private REST API

#### 1. 자산 관리
```python
# 잔고 조회
GET /v1/accounts
# 응답: [{"currency": "KRW", "balance": "1000000"}, ...]

# 입출금 내역
GET /v1/deposits?currency=KRW&state=done&limit=100
GET /v1/withdraws?currency=KRW&state=done&limit=100
```

#### 2. 주문 관리
```python
# 주문하기
POST /v1/orders
{
    "market": "KRW-BTC",
    "side": "bid",           # bid(매수) | ask(매도)
    "ord_type": "limit",     # limit(지정가) | price(시장가-매수) | market(시장가-매도)
    "price": "95000000",     # 주문 가격
    "volume": "0.001"        # 주문 수량
}

# 주문 조회
GET /v1/order?uuid={주문UUID}
GET /v1/orders?market=KRW-BTC&state=wait&limit=100

# 주문 취소
DELETE /v1/order?uuid={주문UUID}
```

## 🔐 인증 시스템

### JWT 토큰 생성
**파일**: `upbit_auth.py`

```python
from upbit_auto_trading.auth.upbit_auth import UpbitAuthenticator

# 자동 API 키 로드
auth = UpbitAuthenticator()

# JWT 토큰 생성 (Private API용)
token = auth.generate_token(query_params)

# Headers 설정
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}
```

### API 키 설정
```json
// config/local_env_vars.json
{
    "UPBIT_ACCESS_KEY": "your_access_key",
    "UPBIT_SECRET_KEY": "your_secret_key"
}
```

## 📊 Rate Limit 정보

### WebSocket 연결 제한
- **Public**: 동시 연결 5개, 구독 티켓 3개
- **Private**: 동시 연결 1개, 구독 티켓 2개

### REST API 제한
- **Public**: 초당 10회, 분당 600회
- **Private**: 초당 5회, 분당 200회
- **주문 API**: 초당 1회, 분당 20회

### 권장 사용 패턴
```python
# 안전한 요청 간격
import asyncio

async def safe_requests():
    for request in requests:
        await make_request()
        await asyncio.sleep(0.1)  # 100ms 간격
```

## 🔧 공통 유틸리티

### 마켓 코드 변환
```python
# 표준 형식: "KRW-BTC"
def format_market_code(base_currency: str, quote_currency: str) -> str:
    return f"{quote_currency}-{base_currency}"

# 예시
krw_btc = format_market_code("BTC", "KRW")  # "KRW-BTC"
```

### 시간 형식 처리
```python
# 업비트 타임스탬프 (밀리초)
timestamp_ms = 1640995200000

# datetime 변환
from datetime import datetime
dt = datetime.fromtimestamp(timestamp_ms / 1000)
```

### 오류 코드 처리
```python
# HTTP 상태 코드
200: "성공"
400: "잘못된 요청"
401: "인증 실패"
403: "권한 없음"
429: "요청 제한 초과"
500: "서버 오류"

# 업비트 특정 오류
"VALIDATION_ERROR": "입력값 검증 실패"
"INSUFFICIENT_FUNDS": "잔고 부족"
"ORDER_NOT_FOUND": "주문을 찾을 수 없음"
```

## 📁 파일 구조 참조

### WebSocket v5.0 구현
```
upbit_auto_trading/
  websocket_v5/
    upbit_websocket_public_client.py    # Public 클라이언트
    upbit_websocket_private_client.py   # Private 클라이언트
    models.py                           # Pydantic V2 모델
    conftest.py                         # pytest 설정
    test_simple_ticker.py               # 기본 테스트
```

### REST API 구현
```
upbit_auto_trading/
  rest_api/
    public_client.py                    # Public REST 클라이언트
    private_client.py                   # Private REST 클라이언트
    models.py                           # REST 응답 모델
```

### 공통 모듈
```
upbit_auto_trading/
  auth/
    upbit_auth.py                       # JWT 인증
  utils/
    exceptions.py                       # 예외 정의
    config.py                          # 설정 관리
    state.py                           # 상태 관리
```

---

**이 참조 가이드를 통해 업비트 API의 모든 기능을 일관되고 효율적으로 사용할 수 있습니다.**
