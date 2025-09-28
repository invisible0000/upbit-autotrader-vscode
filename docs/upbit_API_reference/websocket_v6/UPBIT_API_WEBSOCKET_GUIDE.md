# 📡 업비트(Upbit) API 및 웹소켓 완전 가이드

## 🎯 개요
업비트는 REST API와 WebSocket 두 가지 방식으로 데이터와 거래 기능을 제공합니다. 각각의 특성과 제한사항을 이해하여 효율적인 자동매매 시스템을 구축할 수 있습니다.

---

## 🔗 REST API 상세 분석

### 📊 API 분류 및 기능
업비트 REST API는 크게 **Quotation API**(시세 조회)와 **Exchange API**(거래 관련)로 구분됩니다.

#### **1. Quotation API (시세 조회)**
- **기능**: 시세 데이터 조회 (공개 API, 인증 불필요)
- **주요 엔드포인트**:
  - `/v1/market/all`: 마켓 코드 조회
  - `/v1/candles/minutes/{unit}`: 분봉 캔들 (1, 3, 5, 15, 30, 60, 240분)
  - `/v1/candles/days`: 일봉 캔들
  - `/v1/candles/weeks`: 주봉 캔들
  - `/v1/candles/months`: 월봉 캔들
  - `/v1/ticker`: 현재가 정보
  - `/v1/trades/ticks`: 최근 체결 내역
  - `/v1/orderbook`: 호가 정보

#### **2. Exchange API (거래 관련)**
- **기능**: 잔고, 주문, 입출금 관리 (인증 필요)
- **주요 엔드포인트**:
  - `/v1/accounts`: 전체 계좌 조회
  - `/v1/orders`: 주문 리스트 조회
  - `/v1/orders/chance`: 주문 가능 정보
  - `/v1/orders`: 주문하기 (POST)
  - `/v1/orders/{uuid}`: 주문 취소 (DELETE)
  - `/v1/withdraws`: 출금 관련
  - `/v1/deposits`: 입금 관련

### ⚡ Rate Limit (요청 수 제한)
업비트 API는 서비스 안정성을 위해 엄격한 요청 수 제한을 적용합니다.

#### **Exchange API (주문, 출금, 잔고 조회)**
- **주문 관련 API**:
  - 초당 **8회**
  - 분당 **480회**
- **주문 외 API**:
  - 초당 **30회**
  - 분당 **1,800회**

#### **Quotation API (시세 조회)**
- **REST API**:
  - 초당 **10회**
  - 분당 **600회**

#### **Rate Limit 적용 원칙**
- API Key별로 개별 계산
- 제한 초과 시 일시적 사용 제한
- 429 HTTP 상태 코드 반환

---

## 🌐 WebSocket 실시간 스트리밍

### 🎯 WebSocket의 핵심 장점
1. **실시간 데이터**: REST API의 폴링 방식 대신 실시간 푸시
2. **효율적 대역폭**: 한 번 연결로 지속적 데이터 수신
3. **Rate Limit 우회**: 연결 후에는 요청 수 제한 없음
4. **저지연**: 밀리초 단위 실시간 업데이트

### 📡 WebSocket 엔드포인트
```
시세 데이터 (공개):    wss://api.upbit.com/websocket/v1
자산/주문 (프라이빗):   wss://api.upbit.com/websocket/v1/private
```

### 🔐 인증 방식
**프라이빗 WebSocket 사용 시 필수**:
```
Authorization: Bearer [JWT_TOKEN]
```

### 📊 지원 데이터 타입

#### **Quotation (시세 데이터)**
| 데이터 타입 | 설명 | 스냅샷 | 실시간 |
|------------|------|:-----:|:-----:|
| `ticker` | 현재가 정보 | ✅ | ✅ |
| `trade` | 체결 정보 | ✅ | ✅ |
| `orderbook` | 호가 정보 | ✅ | ✅ |
| `candle.{unit}` | 캔들 데이터 | ✅ | ✅ |

#### **Exchange (프라이빗 데이터)**
| 데이터 타입 | 설명 | 스냅샷 | 실시간 |
|------------|------|:-----:|:-----:|
| `myAsset` | 내 자산 정보 | ❌ | ✅ |
| `myOrder` | 내 주문 정보 | ❌ | ✅ |

### 🎛️ 요청 메시지 구조
WebSocket은 JSON Array 형식으로 메시지를 전송합니다:

```json
[
  {"ticket": "unique-id"},
  {"type": "ticker", "codes": ["KRW-BTC", "KRW-ETH"]},
  {"format": "DEFAULT"}
]
```

#### **Ticket Object**
- `ticket`: 고유 식별자 (UUID 권장)

#### **Data Type Object**
- `type`: 데이터 타입 (`ticker`, `trade`, `orderbook`, `candle.1`, etc.)
- `codes`: 조회할 마켓 코드 배열
- `is_only_snapshot`: 스냅샷만 요청 (선택)
- `is_only_realtime`: 실시간 스트림만 요청 (선택)

#### **Format Object**
- `format`: 응답 포맷
  - `DEFAULT`: 기본 포맷
  - `SIMPLE`: 축약 포맷 (필드명 단축)
  - `JSON_LIST`: 리스트 포맷
  - `SIMPLE_LIST`: 축약 리스트 포맷

### 🔄 연결 관리
- **Idle Timeout**: 120초 (무통신 시 자동 종료)
- **Keep-Alive**: PING Frame 또는 "PING" 메시지 전송
- **상태 메시지**: 10초마다 `{"status":"UP"}` 수신
- **압축 지원**: Per-message deflate 압축 가능

### ⚠️ WebSocket Rate Limit
- **연결 요청**: 초당 **5회**, 분당 **100회**
- **연결 후 메시지**: 제한 없음

---

## 🔄 캔들 데이터 실시간 업데이트 분석

### 🕐 캔들 데이터 제공 방식 비교

#### **REST API 캔들 특성**
- **업데이트 방식**: 완성된 캔들 + 진행 중 캔들 혼재 (테스트 필요)
- **지연 시간**: 1-2초
- **데이터 일관성**: 높음
- **Rate Limit**: 초당 10회 제한

#### **WebSocket 캔들 특성**
- **업데이트 방식**: 실시간 스트림
- **지연 시간**: 100-500ms
- **데이터 일관성**: 매우 높음
- **Rate Limit**: 연결 후 무제한

### 💡 실시간 매매를 위한 권장 아키텍처

#### **시나리오 1: WebSocket 우선 (권장)**
```
WebSocket (실시간) → 메인 데이터 소스
REST API (백업)    → 연결 끊김/초기화 시 사용
```

**장점**:
- 실시간 반응 가능
- Rate Limit 걱정 없음
- 네트워크 효율성

**단점**:
- 연결 관리 복잡성
- 재연결 로직 필요

#### **시나리오 2: 하이브리드 접근**
```
WebSocket → 현재가, 체결, 호가 (고빈도 데이터)
REST API → 캔들, 계좌 조회 (저빈도 데이터)
```

### 🛠️ 가상 실시간 캔들 관리 시스템

만약 업비트 API가 완성된 캔들만 제공한다면, 다음과 같은 시스템이 필요합니다:

#### **핵심 컴포넌트**
1. **실시간 가격 수집기** (WebSocket ticker)
2. **캔들 시뮬레이터** (진행 중 캔들 생성)
3. **타임프레임 관리자** (1분, 5분, 15분 등)
4. **데이터 동기화기** (완성 캔들과 실시간 캔들 병합)

#### **구현 예시**
```python
class VirtualCandleManager:
    def __init__(self):
        self.current_candles = {}  # 진행 중 캔들
        self.completed_candles = {}  # 완성된 캔들

    def on_ticker_update(self, ticker_data):
        """WebSocket ticker 업데이트 처리"""
        # 진행 중 캔들의 high, low, close 업데이트

    def on_candle_complete(self, timeframe):
        """캔들 완성 시 처리"""
        # 진행 중 캔들을 완성 캔들로 이동
        # 새로운 진행 중 캔들 시작
```

---

## 📈 자동매매 시스템 설계 권장사항

### 🎯 데이터 수집 전략
1. **WebSocket 기반 실시간 모니터링**
   - `ticker`: 가격 변화 감지
   - `trade`: 체결량 분석
   - `orderbook`: 지지/저항 수준 파악

2. **REST API 보완적 활용**
   - 초기 데이터 로드
   - 연결 장애 시 백업
   - 과거 데이터 분석

### ⚡ 성능 최적화
1. **Connection Pooling**: HTTP 연결 재사용
2. **WebSocket Reconnection**: 자동 재연결 로직
3. **Data Caching**: 중복 요청 방지
4. **Rate Limit 관리**: 요청 큐잉 시스템

### 🛡️ 안정성 확보
1. **Fallback 시스템**: WebSocket → REST API
2. **Circuit Breaker**: 연속 실패 시 임시 중단
3. **Health Check**: 연결 상태 모니터링
4. **Error Handling**: 세분화된 예외 처리

---

## 🚀 multiplier 기능과의 연계

### 📊 실시간 데이터 활용 방안
1. **HIGH_PRICE/LOW_PRICE multiplier**:
   - WebSocket ticker로 실시간 고가/저가 추적
   - 즉시 multiplier 적용하여 신호 생성

2. **RSI multiplier**:
   - 실시간 가격으로 RSI 계산
   - 과매도/과매수 민감도 실시간 조절

3. **VOLUME multiplier**:
   - WebSocket trade로 실시간 거래량 추적
   - 거래량 급증 감지 즉시 반응

### ⚠️ 주의사항
- **노이즈 필터링**: 과도한 신호 방지
- **지연 보상**: 네트워크 지연 고려
- **백테스팅 일관성**: 실시간과 백테스트 환경 차이 최소화

---

## 📚 참고 링크
- [업비트 개발자 센터](https://docs.upbit.com/kr)
- [WebSocket 가이드](https://docs.upbit.com/kr/docs/upbit-quotation-websocket)
- [Rate Limit 안내](https://docs.upbit.com/kr/changelog/안내-업비트-open-api-요청-수-제한-조건-안내)
- [API Key 관리](https://upbit.com/mypage/open_api_management)

---

## 💡 핵심 결론

### ✅ 권장 사항
1. **WebSocket 우선 활용**: 실시간성이 중요한 자동매매에 필수
2. **하이브리드 아키텍처**: WebSocket + REST API 조합
3. **가상 캔들 시스템**: 진행 중 캔들 실시간 관리
4. **Rate Limit 준수**: 안정적 서비스 이용

### 🎯 다음 단계
1. ✅ **캔들 실시간 제공 방식 테스트** 완료 후
2. 🔄 **WebSocket 클라이언트 구현** 계획
3. 📈 **가상 실시간 캔들 시스템** 설계
4. ⚡ **multiplier 기능과 통합** 개발
