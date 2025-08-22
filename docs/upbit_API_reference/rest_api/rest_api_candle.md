# 📊 업비트 REST API 캔들 데이터 완전 가이드

## 📋 문서 정보

- **API 유형**: REST API 캔들 데이터 조회
- **문서 분량**: 350줄 / 600줄 (58% 사용) 🟡
- **마지막 업데이트**: 2025년 8월 22일
- **핵심 키워드**: REST API, 캔들, OHLCV, 시간대별 조회, 업비트

---

## 🎯 개요

업비트 REST API를 통해 다양한 시간 단위의 캔들(OHLCV) 데이터를 조회할 수 있습니다. 초단위부터 연단위까지 6가지 시간대를 지원하며, 각각 최대 200개의 캔들을 한 번에 조회할 수 있습니다.

### 💡 핵심 특징
- **6가지 시간대**: 초/분/일/주/월/연 단위 캔들 지원
- **최대 조회량**: 한 번에 최대 200개 캔들
- **Rate Limit**: 초당 최대 10회 (캔들 그룹 내 공유)
- **체결 기반**: 체결이 발생한 시간대에만 캔들 생성

---

## 📊 지원하는 캔들 유형

| 캔들 유형 | 엔드포인트 | 특별 제한 | 주요 용도 |
|----------|------------|-----------|-----------|
| **초 캔들** | `/v1/candles/seconds` | 최대 3개월 | 스캘핑, 실시간 분석 |
| **분 캔들** | `/v1/candles/minutes/{unit}` | 단위: 1,3,5,10,15,30,60,240 | 일반 트레이딩 |
| **일 캔들** | `/v1/candles/days` | 환산 통화 지원 | 중장기 분석 |
| **주 캔들** | `/v1/candles/weeks` | - | 주간 패턴 분석 |
| **월 캔들** | `/v1/candles/months` | - | 월간 추세 분석 |
| **연 캔들** | `/v1/candles/years` | - | 장기 투자 분석 |

---

## 🔧 공통 요청 구조

### 📤 기본 파라미터

```http
GET /v1/candles/{type} HTTP/1.1
Host: api.upbit.com
Accept: application/json
```

#### 필수 파라미터
- **market**: 조회하고자 하는 페어(거래쌍)
  - 형식: `KRW-BTC`, `BTC-ETH` 등

#### 선택 파라미터
| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `to` | string | 현재 시각 | 조회 종료 시각 (ISO 8601) |
| `count` | integer | 1 | 조회할 캔들 개수 (최대 200) |

### 📅 시간 형식 (ISO 8601)
```
2025-06-24T04:56:53Z          # UTC
2025-06-24 04:56:53           # 공백 포함
2025-06-24T13:56:53+09:00     # 타임존 포함
```

---

## 📋 응답 데이터 구조

### 🔍 공통 필드

| 필드명 | 타입 | 설명 | 예시값 |
|--------|------|------|--------|
| `market` | string | 페어 코드 | "KRW-BTC" |
| `candle_date_time_utc` | string | 캔들 시작 시각 (UTC) | "2025-07-01T12:00:00" |
| `candle_date_time_kst` | string | 캔들 시작 시각 (KST) | "2025-07-01T21:00:00" |
| `opening_price` | double | 시가 | 145831000 |
| `high_price` | double | 고가 | 145831000 |
| `low_price` | double | 저가 | 145752000 |
| `trade_price` | double | 종가 | 145759000 |
| `timestamp` | int64 | 마지막 틱 타임스탬프 (ms) | 1751327999833 |
| `candle_acc_trade_price` | double | 누적 거래금액 | 4022470467.03403 |
| `candle_acc_trade_volume` | double | 누적 거래량 | 27.58904602 |

### 📊 응답 예시
```json
[
  {
    "market": "KRW-BTC",
    "candle_date_time_utc": "2025-07-01T12:00:00",
    "candle_date_time_kst": "2025-07-01T21:00:00",
    "opening_price": 145831000,
    "high_price": 145831000,
    "low_price": 145752000,
    "trade_price": 145759000,
    "timestamp": 1751327999833,
    "candle_acc_trade_price": 4022470467.03403,
    "candle_acc_trade_volume": 27.58904602
  }
]
```

---

## 🕐 세부 캔들 유형별 가이드

### 1. 📊 초(Second) 캔들

```http
GET /v1/candles/seconds?market=KRW-BTC&count=200
```

#### 🚨 특별 제한사항
- **조회 기간**: 최대 3개월 (요청 시점 기준)
- **3개월 초과 요청 시**: 빈 배열 반환 또는 부분 데이터

#### 💡 사용 사례
- 스캘핑 전략
- 실시간 체결 분석
- 단기 변동성 측정

### 2. ⏰ 분(Minute) 캔들

```http
GET /v1/candles/minutes/{unit}?market=KRW-BTC&count=200
```

#### 📏 지원 단위 (unit)
| Unit | 설명 | 주요 용도 |
|------|------|-----------|
| `1` | 1분봉 | 단기 매매 |
| `3` | 3분봉 | 스윙 트레이딩 |
| `5` | 5분봉 | 일반적 트레이딩 |
| `10` | 10분봉 | 중기 패턴 |
| `15` | 15분봉 | 중기 분석 |
| `30` | 30분봉 | 중장기 분석 |
| `60` | 1시간봉 | 일간 패턴 |
| `240` | 4시간봉 | 장기 추세 |

#### 🔗 요청 예시
```bash
# 5분봉 200개 조회
curl -X GET "https://api.upbit.com/v1/candles/minutes/5?market=KRW-BTC&count=200"

# 특정 시점 이전 1시간봉 50개
curl -X GET "https://api.upbit.com/v1/candles/minutes/60?market=KRW-BTC&count=50&to=2025-08-22T10:00:00"
```

### 3. 📅 일(Day) 캔들

```http
GET /v1/candles/days?market=KRW-BTC&count=100
```

#### 🔄 종가 환산 통화 지원
```http
GET /v1/candles/days?market=BTC-ETH&converting_price_unit=KRW
```

#### 📊 추가 응답 필드
| 필드명 | 설명 | 조건 |
|--------|------|------|
| `prev_closing_price` | 전일 종가 | 항상 포함 |
| `change_price` | 전일 대비 변화량 | 항상 포함 |
| `change_rate` | 전일 대비 변화율 | 항상 포함 |
| `converted_trade_price` | 환산된 종가 | converting_price_unit 사용 시 |

### 4. 📊 주/월/연 캔들

```http
# 주 캔들
GET /v1/candles/weeks?market=KRW-BTC&count=52

# 월 캔들
GET /v1/candles/months?market=KRW-BTC&count=12

# 연 캔들
GET /v1/candles/years?market=KRW-BTC&count=5
```

#### 📊 추가 응답 필드
- **first_day_of_period**: 캔들 집계 시작일자 (yyyy-MM-dd)

---

## ⚡ Rate Limit 및 최적화

### 📊 제한 정보
| 제한 사항 | 값 | 비고 |
|----------|---|------|
| **초당 요청** | 최대 10회 | IP 단위 측정 |
| **공유 그룹** | 캔들 그룹 | 모든 캔들 API가 공유 |
| **최대 개수** | 200개 | 단일 요청당 |

### 🚀 최적화 전략
1. **배치 처리**: 200개씩 묶어서 요청
2. **시간 간격**: 100ms 이상 간격 유지
3. **캐싱 활용**: 동일 데이터 중복 요청 방지
4. **점진적 로딩**: 필요한 만큼만 요청

---

## 🎯 실제 사용 예시

### 📈 기술적 분석 데이터 수집
```python
import requests

def get_candles(market, interval, count=200, to=None):
    """캔들 데이터 조회"""
    base_url = "https://api.upbit.com/v1/candles"

    # 시간 단위별 엔드포인트 매핑
    endpoints = {
        "1m": f"{base_url}/minutes/1",
        "5m": f"{base_url}/minutes/5",
        "1h": f"{base_url}/minutes/60",
        "1d": f"{base_url}/days"
    }

    params = {"market": market, "count": count}
    if to:
        params["to"] = to

    response = requests.get(endpoints[interval], params=params)
    return response.json()

# 사용 예시
btc_5m = get_candles("KRW-BTC", "5m", 200)
btc_daily = get_candles("KRW-BTC", "1d", 100)
```

### 📊 대용량 히스토리 수집
```python
from datetime import datetime, timedelta
import time

def get_historical_data(market, interval, days=30):
    """대용량 히스토리 데이터 수집"""
    all_candles = []
    current_time = datetime.now()

    while days > 0:
        # 200개씩 배치 처리
        candles = get_candles(
            market, interval, 200,
            current_time.isoformat()
        )

        if not candles:
            break

        all_candles.extend(candles)

        # 마지막 캔들 시간으로 이동
        last_time = datetime.fromisoformat(
            candles[-1]["candle_date_time_utc"]
        )
        current_time = last_time - timedelta(seconds=1)

        # Rate limit 준수
        time.sleep(0.1)
        days -= 1

    return all_candles
```

---

## ⚠️ 중요 고려사항

### 🕐 캔들 생성 원칙
- **체결 기반**: 체결이 발생한 시간대에만 캔들 생성
- **빈 캔들 없음**: 거래가 없으면 응답에 포함되지 않음
- **연속성**: 시간 간격이 불규칙할 수 있음

### 🔄 데이터 무결성
- **최신 우선**: `to` 파라미터 시점 이전 데이터만 조회
- **타임존 주의**: UTC와 KST 시간 모두 제공
- **정밀도**: 밀리초 단위 타임스탬프 제공

### 💰 원화 환산
- **일 캔들 전용**: converting_price_unit=KRW 지원
- **BTC 마켓**: BTC-ETH 등을 원화로 환산 가능
- **추가 필드**: converted_trade_price 필드 제공

---

## 🔗 관련 문서

### 📚 API 기본 가이드
- [업비트 API 개요](../api_overview.md)
- [Rate Limits 가이드](../rate_limits.md)
- [인증 방법](../authentication.md)

### 🌐 실시간 데이터
- [WebSocket 캔들 API](../websocket/websocket_candle.md)
- [WebSocket vs REST 비교](../websocket_vs_rest.md)

### 🛠️ 구현 가이드
- [스마트 라우터 설계](../../MARKET_DATA_BACKBONE_REFACTOR_PLAN.md)
- [대용량 데이터 처리](../../MARKET_DATA_PERFORMANCE_OPTIMIZATION_ANALYSIS.md)

---

**문서 유형**: REST API 참조 가이드
**대상 독자**: 개발자, GitHub Copilot Agent
**분량**: 350줄 / 600줄 (58% 사용) 🟡
**마지막 업데이트**: 2025년 8월 22일

## 🎯 빠른 참조

### 📋 체크리스트
- [ ] market 파라미터 필수 확인
- [ ] count는 최대 200개로 제한
- [ ] Rate limit (초당 10회) 준수
- [ ] 시간 형식은 ISO 8601 사용
- [ ] 초 캔들은 3개월 제한 고려

### 🚀 다음 단계
1. **기본 조회**: 단일 캔들 API 테스트
2. **배치 처리**: 200개씩 대용량 조회
3. **실시간 연동**: WebSocket과 조합 사용
4. **최적화**: 캐싱 및 스마트 라우터 적용

**"REST API는 과거 데이터 조회의 핵심, WebSocket은 실시간 데이터의 핵심"**
