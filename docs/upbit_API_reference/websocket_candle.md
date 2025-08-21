# WebSocket 캔들 (Candle) API 명세

## 📋 개요

업비트 WebSocket 캔들 API는 실시간 OHLCV(시가, 고가, 저가, 종가, 거래량) 데이터를 제공합니다. 다양한 시간 단위의 캔들 데이터를 실시간으로 수신하여 차트 분석과 기술적 분석에 활용할 수 있습니다.

**엔드포인트**: `wss://api.upbit.com/websocket/v1`

## 🎯 주요 특징

### 지원 캔들 타입
업비트는 다음 9가지 캔들 타입을 지원합니다:
- **초봉**: 1초봉 (candle.1s)
- **분봉**: 1분, 3분, 5분, 10분, 15분, 30분, 60분봉 (candle.1m ~ candle.60m)
- **4시간봉**: 240분봉 (candle.240m)

### 실시간 전송 방식
- **전송 주기**: 1초 간격
- **데이터 생성 조건**: 체결 발생시에만 캔들 데이터 생성
- **중복 전송**: 동일 시간대 캔들이 여러 번 전송될 수 있음 (최신 데이터가 우선)

## 📤 요청 메시지 형식

### 기본 구조
```json
[
  {
    "ticket": "unique-ticket-id"
  },
  {
    "type": "candle.5m",
    "codes": ["KRW-BTC", "KRW-ETH"]
  },
  {
    "format": "DEFAULT"
  }
]
```

### 요청 파라미터

| 필드 | 타입 | 설명 | 필수 여부 | 기본값 |
|------|------|------|-----------|--------|
| `type` | String | 캔들 형식 | Required | - |
| `codes` | List\<String\> | 수신할 페어 목록 (대문자) | Required | - |
| `is_only_snapshot` | Boolean | 스냅샷만 제공 | Optional | false |
| `is_only_realtime` | Boolean | 실시간만 제공 | Optional | false |

### 캔들 타입 상세

| 타입 | 설명 | 용도 | 주요 특징 |
|------|------|------|-----------|
| `candle.1s` | 1초봉 | 스캘핑, 초단타 매매 | 고빈도 거래, 틱 분석 |
| `candle.1m` | 1분봉 | 단타 매매, 즉시 반응 | 단기 패턴 분석 |
| `candle.3m` | 3분봉 | 단기 추세 분석 | 빠른 추세 전환 감지 |
| `candle.5m` | 5분봉 | 데이 트레이딩 | 일반적인 단타 분석 |
| `candle.10m` | 10분봉 | 중단기 분석 | 노이즈 제거된 추세 |
| `candle.15m` | 15분봉 | 스윙 트레이딩 | 중기 패턴 분석 |
| `candle.30m` | 30분봉 | 중기 추세 분석 | 일중 추세 파악 |
| `candle.60m` | 60분봉 | 장기 추세 분석 | 주요 지지저항 |
| `candle.240m` | 240분봉 (4시간) | 장기 투자 분석 | 장기 추세, 포지션 분석 |

### 요청 예시

#### 다양한 시간대 캔들 구독
```json
[
  {
    "ticket": "multi-timeframe"
  },
  {
    "type": "candle.1s",
    "codes": ["KRW-BTC"]
  },
  {
    "type": "candle.1m",
    "codes": ["KRW-BTC"]
  },
  {
    "type": "candle.5m",
    "codes": ["KRW-BTC"]
  },
  {
    "type": "candle.60m",
    "codes": ["KRW-BTC"]
  }
]
```

#### 스냅샷 전용 요청
```json
[
  {
    "ticket": "snapshot-only"
  },
  {
    "type": "candle.15m",
    "codes": ["KRW-BTC", "KRW-ETH"],
    "is_only_snapshot": true
  }
]
```

## 📥 응답 데이터 명세

### 응답 구조
```json
{
  "type": "candle.1s",
  "code": "KRW-BTC",
  "candle_date_time_utc": "2025-01-02T04:28:05",
  "candle_date_time_kst": "2025-01-02T13:28:05",
  "opening_price": 142009000.00000000,
  "high_price": 142009000.00000000,
  "low_price": 142009000.00000000,
  "trade_price": 142009000.00000000,
  "candle_acc_trade_volume": 0.00606119,
  "candle_acc_trade_price": 860743.5307100000000000,
  "timestamp": 1735792085824,
  "stream_type": "REALTIME"
}
```

### 필드 상세 설명

| 필드 | 약칭 | 설명 | 타입 | 예시 |
|------|------|------|------|------|
| `type` | `ty` | 캔들 타입 | String | candle.1s, candle.1m, candle.3m, candle.5m, candle.10m, candle.15m, candle.30m, candle.60m, candle.240m |
| `code` | `cd` | 마켓 코드 | String | KRW-BTC |
| `candle_date_time_utc` | `cdttmu` | 캔들 기준시각 (UTC) | String | 2025-01-02T04:28:05 |
| `candle_date_time_kst` | `cdttmk` | 캔들 기준시각 (KST) | String | 2025-01-02T13:28:05 |
| `opening_price` | `op` | 시가 | Double | 142009000.0 |
| `high_price` | `hp` | 고가 | Double | 142009000.0 |
| `low_price` | `lp` | 저가 | Double | 142009000.0 |
| `trade_price` | `tp` | 종가 | Double | 142009000.0 |
| `candle_acc_trade_volume` | `catv` | 누적 거래량 | Double | 0.00606119 |
| `candle_acc_trade_price` | `catp` | 누적 거래금액 | Double | 860743.53 |
| `timestamp` | `tms` | 타임스탬프 (ms) | Long | 1735792085824 |
| `stream_type` | `st` | 스트림 타입 | String | SNAPSHOT/REALTIME |

## 🕐 캔들 데이터 생성 원리

### 데이터 생성 조건
1. **체결 발생시만 생성**: 체결이 없으면 캔들 데이터 미생성
2. **변화 감지**: 직전 캔들 대비 데이터 변경시에만 전송
3. **지연 생성**: 요청 시점에 해당 시간 캔들이 없으면 이전 시간 캔들 전송

### 생성 예시 (3분봉 기준)
```
12:00:00 ~ 12:03:00: 3분봉 존재
12:03:00 ~ 12:04:00: 체결 없음
12:04:00: 요청 시 → 12:00:00 3분봉 반환 (스냅샷)
12:04:05: 첫 체결 발생 → 12:03:00 3분봉 생성
12:04:06: 12:03:00 3분봉 전송 (실시간)
```

### 중복 전송 처리
- **동일 시간대**: 같은 `candle_date_time` 캔들이 여러 번 전송 가능
- **최신 우선**: 가장 마지막 수신 데이터가 최신
- **업데이트 방식**: `candle_date_time` 필드로 캔들 식별 후 덮어쓰기

## 💡 활용 예시

### 1. 기본 캔들 데이터 수신
```python
import asyncio
import websockets
import json

async def monitor_candles():
    uri = "wss://api.upbit.com/websocket/v1"

    async with websockets.connect(uri) as websocket:
        subscribe_message = [
            {"ticket": "candle-monitor"},
            {
                "type": "candle.5m",
                "codes": ["KRW-BTC", "KRW-ETH"]
            }
        ]

        await websocket.send(json.dumps(subscribe_message))

        candle_data = {}  # 캔들 데이터 저장

        while True:
            data = await websocket.recv()
            candle = json.loads(data)

            # 캔들 데이터 업데이트
            key = f"{candle['code']}_{candle['candle_date_time_kst']}"
            candle_data[key] = candle

            print(f"[{candle['code']}] {candle['candle_date_time_kst']} "
                  f"O:{candle['opening_price']:,} H:{candle['high_price']:,} "
                  f"L:{candle['low_price']:,} C:{candle['trade_price']:,}")
```

### 2. 멀티 타임프레임 분석
```python
class MultiTimeframeAnalyzer:
    def __init__(self):
        self.candles = {
            '1m': {},
            '5m': {},
            '15m': {},
            '60m': {}
        }

    def update_candle(self, candle_data):
        """캔들 데이터 업데이트"""
        timeframe = candle_data['type'].split('.')[1]
        code = candle_data['code']
        timestamp = candle_data['candle_date_time_kst']

        if code not in self.candles[timeframe]:
            self.candles[timeframe][code] = {}

        self.candles[timeframe][code][timestamp] = candle_data

    def get_trend_alignment(self, code):
        """멀티 타임프레임 추세 정렬 분석"""
        trends = {}

        for tf in ['1m', '5m', '15m', '60m']:
            if code in self.candles[tf]:
                latest_candles = list(self.candles[tf][code].values())[-3:]
                if len(latest_candles) >= 3:
                    # 간단한 추세 분석 (3개 캔들의 종가 비교)
                    prices = [c['trade_price'] for c in latest_candles]
                    if prices[2] > prices[1] > prices[0]:
                        trends[tf] = 'UP'
                    elif prices[2] < prices[1] < prices[0]:
                        trends[tf] = 'DOWN'
                    else:
                        trends[tf] = 'SIDEWAYS'

        return trends
```

### 3. 실시간 기술적 분석
```python
def calculate_sma(candles, period=20):
    """단순이동평균 계산"""
    if len(candles) < period:
        return None

    recent_candles = candles[-period:]
    prices = [c['trade_price'] for c in recent_candles]
    return sum(prices) / len(prices)

def calculate_rsi(candles, period=14):
    """RSI 계산"""
    if len(candles) < period + 1:
        return None

    prices = [c['trade_price'] for c in candles[-(period+1):]]
    gains = []
    losses = []

    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

async def technical_analysis_monitor():
    """실시간 기술적 분석"""
    candle_history = {}

    async def process_candle(candle_data):
        code = candle_data['code']

        if code not in candle_history:
            candle_history[code] = []

        # 캔들 히스토리 업데이트 (최대 100개 유지)
        candle_history[code].append(candle_data)
        if len(candle_history[code]) > 100:
            candle_history[code] = candle_history[code][-100:]

        # 기술적 분석 계산
        sma20 = calculate_sma(candle_history[code], 20)
        rsi = calculate_rsi(candle_history[code], 14)

        current_price = candle_data['trade_price']

        if sma20 and rsi:
            trend = "상승" if current_price > sma20 else "하락"
            rsi_signal = "과매수" if rsi > 70 else "과매도" if rsi < 30 else "중립"

            print(f"[{code}] 현재가: {current_price:,} | "
                  f"SMA20: {sma20:,.0f} | 추세: {trend} | "
                  f"RSI: {rsi:.1f} ({rsi_signal})")
```

## ⚠️ 주의사항

### 데이터 특성
- **비동기 전송**: 1초 주기이지만 체결 발생시에만 전송
- **지연 가능성**: 체결 타이밍에 따라 데이터 전송이 지연될 수 있음
- **중복 처리**: 동일 시간대 캔들의 중복 전송 대비 필요

### 성능 고려사항
- **메모리 관리**: 캔들 히스토리 누적시 메모리 사용량 증가
- **네트워크 부하**: 다수 시간대 + 다수 코인 구독시 높은 대역폭 사용
- **처리 속도**: 1초 주기 전송으로 빠른 데이터 처리 능력 필요

### 데이터 정합성
- **시간대 동기화**: UTC와 KST 시간 정보 동시 제공
- **소수점 정밀도**: 가격과 거래량의 높은 정밀도 유지
- **타임스탬프**: 밀리초 단위 정확한 시간 정보

## 🔗 관련 API

- [WebSocket 체결 (Trade)](./websocket_trade.md)
- [WebSocket 현재가 (Ticker)](./websocket_ticker.md)
- [REST 캔들 조회](https://docs.upbit.com/kr/reference/list-candles-seconds)

## 📚 추가 자료

- [업비트 WebSocket 사용 안내](https://docs.upbit.com/kr/reference/websocket-guide)
- [캔들 차트 분석 가이드](https://docs.upbit.com/kr/docs/candlestick-analysis)
- [기술적 분석 활용법](https://docs.upbit.com/kr/docs/technical-analysis)

---

**마지막 업데이트**: 2025년 1월
**API 버전**: v1
**문서 버전**: 1.0
