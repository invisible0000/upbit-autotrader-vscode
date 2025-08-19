# 업비트 호가창 API 가이드

## 개요
업비트 호가창(Orderbook) API는 실시간 호가 정보를 제공하며, 매수/매도 주문 정보를 통해 시장 깊이와 유동성을 파악할 수 있습니다. 이 문서는 자동매매 시스템에서 호가창 기능을 안전하고 효율적으로 구현하기 위한 종합 가이드입니다.

## 주요 기능

### 1. 웹소켓 호가 스트림
- **실시간 호가 데이터**: 매수/매도 호가와 잔량 정보
- **스냅샷/실시간 모드**: 초기 데이터와 실시간 업데이트 선택 가능
- **호가 단위 조절**: 1, 5, 15, 30개 호가 쌍 선택 (기본 30개)

### 2. 호가 모아보기 (원화 마켓 전용)
- **그룹핑 기능**: 지정한 단위로 호가를 그룹화하여 집계
- **KRW 마켓 한정**: BTC, USDT 마켓은 지원하지 않음
- **지원 단위**: 종목별로 다양한 모아보기 단위 제공

### 3. 호가 정책 조회
- **틱 사이즈**: 각 종목의 최소 가격 단위
- **모아보기 지원 단위**: 종목별 지원되는 그룹핑 레벨

## 웹소켓 API 사용법

### 연결 엔드포인트
- **URL**: `wss://api.upbit.com/websocket/v1`
- **프로토콜**: WebSocket
- **인증**: 공개 데이터는 인증 불필요

### 연결 요청 구조
```json
[
  {
    "ticket": "unique-ticket-id"
  },
  {
    "type": "orderbook",
    "codes": ["KRW-BTC", "KRW-ETH.5"],
    "level": 10000,
    "is_only_snapshot": false,
    "is_only_realtime": false
  },
  {
    "format": "DEFAULT"
  }
]
```

### 주요 파라미터
- **ticket**: 고유 식별자 (연결 추적용)
- **type**: "orderbook" (호가창 타입)
- **codes**: 조회할 페어 목록 (대문자 필수)
- **level**: 호가 모아보기 단위 (선택사항, KRW 마켓만)
- **호가 개수 지정**: `KRW-BTC.15` (15개 호가 쌍)
- **is_only_snapshot**: 스냅샷만 수신 (초기 데이터)
- **is_only_realtime**: 실시간만 수신 (변경사항만)

### 웹소켓 연결 생명주기
1. **연결 초기화**: WebSocket 연결 설정
2. **구독 요청**: JSON 배열로 호가창 구독 정보 전송
3. **데이터 수신**: 실시간 호가 데이터 스트림 수신
4. **연결 유지**: 주기적 핑/퐁으로 연결 상태 확인
5. **재연결 처리**: 연결 끊김 시 자동 재연결

### 응답 데이터 구조
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

### 웹소켓 구현 예시 (Python)
```python
import websocket
import json
import threading

class UpbitOrderbookStream:
    def __init__(self):
        self.ws = None
        self.is_connected = False

    def on_message(self, ws, message):
        """호가 데이터 수신 처리"""
        try:
            data = json.loads(message)
            if data.get("type") == "orderbook":
                self.process_orderbook_data(data)
        except Exception as e:
            print(f"메시지 처리 오류: {e}")

    def on_open(self, ws):
        """연결 성공 시 구독 요청"""
        self.is_connected = True
        subscribe_data = [
            {"ticket": "orderbook-stream"},
            {
                "type": "orderbook",
                "codes": ["KRW-BTC", "KRW-ETH"],
                "is_only_realtime": True
            }
        ]
        ws.send(json.dumps(subscribe_data))
        print("호가창 구독 시작")

    def on_error(self, ws, error):
        """에러 처리 및 재연결"""
        print(f"WebSocket 오류: {error}")
        self.is_connected = False
        self.reconnect()

    def start_stream(self):
        """웹소켓 스트림 시작"""
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            "wss://api.upbit.com/websocket/v1",
            on_message=self.on_message,
            on_error=self.on_error,
            on_open=self.on_open
        )
        self.ws.run_forever()
```

### 고급 웹소켓 기능

#### 1. 다중 종목 구독
```json
{
  "type": "orderbook",
  "codes": ["KRW-BTC", "KRW-ETH", "KRW-ADA", "KRW-DOT"],
  "is_only_realtime": true
}
```

#### 2. 호가 개수 제한
```json
{
  "type": "orderbook",
  "codes": ["KRW-BTC.5", "KRW-ETH.10"],
  "is_only_snapshot": false
}
```

#### 3. 모아보기 레벨 활용
```json
{
  "type": "orderbook",
  "codes": ["KRW-BTC"],
  "level": 100000,
  "is_only_realtime": true
}
```

### 스트림 타입 구분
- **SNAPSHOT**: 초기 전체 호가 데이터
- **REALTIME**: 실시간 변경 데이터만

## 원화 마켓 호가 단위 정책

### 2025년 7월 31일 변경된 호가 단위
| 가격 구간 | 호가 단위 |
|-----------|-----------|
| 2,000,000원 이상 | 1,000원 |
| 1,000,000원 이상~2,000,000원 미만 | 1,000원 |
| 500,000원 이상~1,000,000원 미만 | 500원 |
| 100,000원 이상~500,000원 미만 | 100원 |
| 50,000원 이상~100,000원 미만 | 50원 |
| 10,000원 이상~50,000원 미만 | 10원 |
| 5,000원 이상~10,000원 미만 | 5원 |
| 1,000원 이상~5,000원 미만 | 1원 |
| 100원 이상~1,000원 미만 | 1원 |
| 10원 이상~100원 미만 | 0.1원 |
| 1원 이상~10원 미만 | 0.01원 |
| 0.1원 이상~1원 미만 | 0.001원 |
| 0.01원 이상~0.1원 미만 | 0.0001원 |
| 0.001원 이상~0.01원 미만 | 0.00001원 |
| 0.0001원 이상~0.001원 미만 | 0.000001원 |
| 0.00001원 이상~0.0001원 미만 | 0.0000001원 |
| 0.00001원 미만 | 0.00000001원 |

### USDT/KRW, USDC/KRW 특별 정책
- **1,000원~10,000원 구간**: 0.5원 (특별 적용)
- **최소 주문 금액**: 5,000 KRW

## 호가 정책 조회 API

### 엔드포인트
```
GET https://api.upbit.com/v1/orderbook/instruments
```

### 요청 파라미터
- **markets**: 조회할 페어 목록 (쉼표로 구분)

### 응답 예시
```json
[
  {
    "market": "KRW-BTC",
    "quote_currency": "KRW",
    "tick_size": 1000,
    "supported_levels": [0, 10000, 100000, 1000000, 10000000, 100000000]
  }
]
```

## 자동매매 시스템 적용 고려사항

### 1. 주문 가격 검증
```python
def validate_order_price(price: float, market: str) -> bool:
    """호가 단위에 맞는 가격인지 검증"""
    tick_size = get_tick_size(market, price)
    return price % tick_size == 0
```

### 2. 호가창 깊이 분석
- **유동성 평가**: total_ask_size, total_bid_size 활용
- **스프레드 계산**: ask_price - bid_price
- **시장 임팩트 예측**: 대량 주문 시 호가창 영향도 분석

### 3. 실시간 모니터링
- **연결 안정성**: 웹소켓 재연결 로직 필수
- **지연 감지**: timestamp를 통한 데이터 신선도 확인
- **오류 처리**: 잘못된 호가 단위 주문 시 에러 대응

### 4. 호가 모아보기 활용
- **노이즈 감소**: 세밀한 호가를 그룹화하여 트렌드 파악
- **전략 최적화**: 큰 단위로 시장 구조 분석
- **리스크 관리**: 모아보기 단위별 지지/저항 레벨 식별

## 에러 처리

### 주요 에러 코드
- **invalid_price_bid**: 매수 주문 가격 단위 오류
- **invalid_price_ask**: 매도 주문 가격 단위 오류

### 대응 방안
```python
def adjust_price_to_tick_size(price: float, market: str) -> float:
    """가격을 해당 마켓의 호가 단위에 맞게 조정"""
    tick_size = get_tick_size(market, price)
    return round(price / tick_size) * tick_size
```

## 성능 최적화

### 1. 웹소켓 연결 관리
- **연결 풀링**: 여러 종목을 하나의 연결로 처리
- **선택적 구독**: 필요한 종목만 구독하여 대역폭 절약
- **자동 재연결**: 연결 끊김 시 지수적 백오프로 재연결
- **핑/퐁 관리**: 주기적 하트비트로 연결 상태 유지
- **압축 활용**: 가능한 경우 데이터 압축 옵션 사용

### 2. 웹소켓 에러 처리
```python
def handle_websocket_error(self, error_code, retry_count=0):
    """웹소켓 에러별 처리 전략"""
    max_retries = 5
    base_delay = 1

    if retry_count >= max_retries:
        logger.error("최대 재시도 횟수 초과")
        return False

    # 지수적 백오프 적용
    delay = base_delay * (2 ** retry_count)
    time.sleep(delay)

    try:
        self.reconnect()
        return True
    except Exception as e:
        return self.handle_websocket_error(error_code, retry_count + 1)
```

### 3. 데이터 처리 최적화
- **비동기 처리**: 호가 데이터 수신과 분석을 분리
- **메모리 관리**: 오래된 호가 데이터 정리
- **캐싱**: 호가 정책 정보 로컬 캐시
- **델타 처리**: 변경된 호가만 업데이트
- **배치 처리**: 여러 호가 변경을 묶어서 처리

### 4. 알고리즘 최적화
- **우선순위**: 거래량이 많은 종목 우선 처리
- **샘플링**: 고빈도 업데이트 시 적절한 샘플링 적용
- **큐 관리**: 호가 데이터 처리 큐 크기 제한

### 5. 웹소켓 모니터링
```python
class WebSocketMonitor:
    def __init__(self):
        self.connection_stats = {
            "connected_at": None,
            "messages_received": 0,
            "last_message_time": None,
            "reconnect_count": 0
        }

    def check_connection_health(self):
        """연결 상태 건강성 체크"""
        now = time.time()
        if self.connection_stats["last_message_time"]:
            silence_duration = now - self.connection_stats["last_message_time"]
            if silence_duration > 30:  # 30초 이상 침묵 시
                logger.warning("웹소켓 데이터 수신 중단 감지")
                return False
        return True
```

## 보안 고려사항

### 1. 웹소켓 보안
- **TLS/SSL 연결**: wss:// 프로토콜 필수 사용
- **Origin 검증**: 웹 환경에서 Origin 헤더 적절히 설정
- **연결 제한**: 동시 연결 수 제한으로 리소스 보호
- **타임아웃 설정**: 응답 없는 연결 자동 종료

### 2. API 키 관리 (인증 필요 시)
- **환경변수 사용**: 코드에 API 키 하드코딩 금지
- **권한 최소화**: 호가 조회에 필요한 최소 권한만 부여
- **정기 갱신**: API 키 주기적 교체

### 3. Rate Limiting
- **요청 제한 준수**: 업비트 API 제한 사항 엄격 준수
- **백오프 전략**: 제한 초과 시 지수적 백오프
- **모니터링**: 요청 빈도 지속적 모니터링
- **큐 관리**: 요청 큐 크기 제한으로 메모리 보호

### 4. 데이터 무결성
- **타임스탬프 검증**: 오래된 데이터 필터링
- **이상치 탐지**: 비정상적인 호가 데이터 필터링
- **로깅**: 모든 호가 관련 이벤트 상세 기록
- **체크섬 검증**: 중요한 호가 데이터 무결성 확인

### 5. 웹소켓 취약점 대응
```python
class SecureWebSocketClient:
    def __init__(self):
        self.max_message_size = 1024 * 1024  # 1MB 제한
        self.connection_timeout = 30
        self.allowed_origins = ["api.upbit.com"]

    def validate_message(self, message):
        """수신 메시지 검증"""
        if len(message) > self.max_message_size:
            raise ValueError("메시지 크기 초과")

        try:
            json.loads(message)  # JSON 형식 검증
        except json.JSONDecodeError:
            raise ValueError("잘못된 JSON 형식")
```

## 결론

업비트 호가창 API는 자동매매 시스템의 핵심 구성요소로, 시장 상황을 실시간으로 파악하고 최적의 주문 전략을 수립하는 데 필수적입니다. 특히 원화 마켓의 호가 단위 정책 변경과 호가 모아보기 기능을 적절히 활용하면 더욱 정교한 거래 전략을 구현할 수 있습니다.

실제 구현 시에는 웹소켓 연결 안정성, 에러 처리, 성능 최적화를 충분히 고려하여 안정적이고 효율적인 호가창 기능을 구축해야 합니다.
