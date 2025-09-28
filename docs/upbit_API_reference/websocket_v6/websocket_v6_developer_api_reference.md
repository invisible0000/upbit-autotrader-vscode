# 🔧 WebSocket v6 시스템 개발자 API 레퍼런스

## 📚 **클래스 및 메서드**

### **WebSocketClient**
| 메서드 | 용도 | 반환 타입 |
|--------|------|-----------|
| `__init__(component_id)` | 클라이언트 생성 | - |
| `subscribe_ticker(symbols, callback)` | 티커 데이터 구독 | `None` |
| `subscribe_orderbook(symbols, callback)` | 호가 데이터 구독 | `None` |
| `subscribe_trade(symbols, callback)` | 체결 데이터 구독 | `None` |
| `subscribe_candle(symbols, unit, callback)` | 캔들 데이터 구독 | `None` |
| `cleanup()` | 모든 구독 해제 | `None` |
| `get_active_symbols()` | 구독 중인 심볼 목록 | `List[str]` |

### **WebSocketManager**
| 메서드 | 용도 | 반환 타입 |
|--------|------|-----------|
| `start()` | 매니저 시작 | `None` |
| `stop()` | 매니저 정지 | `None` |
| `register_component(id, ref, subscriptions)` | 컴포넌트 등록 | `None` |
| `unregister_component(id)` | 컴포넌트 해제 | `None` |
| `get_rate_limiter_status()` | Rate Limiter 상태 | `Dict` |

### **SubscriptionManager**
| 메서드 | 용도 | 반환 타입 |
|--------|------|-----------|
| `register_component(id, subscriptions)` | 구독 등록 | `None` |
| `unregister_component(id)` | 구독 해제 | `None` |
| `unsubscribe_symbols(symbols, type)` | 개별 심볼 해제 | `bool` |
| `get_realtime_streams(ws_type)` | 활성 스트림 목록 | `Dict` |

---

## 📊 **데이터 타입**

### **이벤트 클래스**
| 클래스 | 주요 속성 | 용도 |
|--------|-----------|------|
| `TickerEvent` | `symbol, trade_price, change_rate` | 실시간 가격 정보 |
| `OrderbookEvent` | `symbol, orderbook_units, timestamp` | 실시간 호가 정보 |
| `TradeEvent` | `symbol, trade_price, trade_volume` | 실시간 체결 정보 |
| `CandleEvent` | `symbol, opening_price, high_price` | 캔들 데이터 |

### **구독 스펙**
| 클래스 | 주요 속성 | 용도 |
|--------|-----------|------|
| `SubscriptionSpec` | `data_type, symbols, unit` | 구독 요구사항 정의 |
| `DataType` | `TICKER, ORDERBOOK, TRADE` | 데이터 타입 열거형 |
| `WebSocketType` | `PUBLIC, PRIVATE` | WebSocket 연결 타입 |

---

## ⚙️ **설정 및 상수**

### **환경 변수**
| 변수명 | 기본값 | 용도 |
|--------|--------|------|
| `WEBSOCKET_TIMEOUT` | `3.0` | 연결 타임아웃 (초) |
| `RATE_LIMIT_STRATEGY` | `balanced` | Rate Limiter 전략 |
| `MAX_RECONNECT_ATTEMPTS` | `5` | 최대 재연결 시도 |

### **Rate Limiter 상수**
| 상수 | 값 | 용도 |
|------|----|----|
| `PUBLIC_BURST` | `5` | Public API 버스트 제한 |
| `PRIVATE_BURST` | `3` | Private API 버스트 제한 |
| `DEBOUNCE_DELAY` | `0.1` | 디바운스 지연 (초) |

---

## 🔌 **콜백 함수**

### **콜백 시그니처**
```python
# 동기 콜백
def ticker_callback(event: TickerEvent) -> None:
    pass

# 비동기 콜백
async def async_ticker_callback(event: TickerEvent) -> None:
    pass
```

### **이벤트 필터링**
| 속성 | 타입 | 설명 |
|------|------|------|
| `stream_preference` | `str` | `"snapshot_only"`, `"realtime_only"`, `"both"` |
| `symbols` | `Set[str]` | 구독할 심볼 목록 |
| `unit` | `str` | 캔들 단위 (`"1m"`, `"5m"`, `"1h"`, `"1d"`) |

---

## 🛠️ **유틸리티 함수**

### **헬퍼 함수**
| 함수 | 용도 | 반환 타입 |
|------|------|-----------|
| `generate_subscription_key()` | 구독 키 생성 | `str` |
| `parse_upbit_message()` | 업비트 메시지 파싱 | `BaseWebSocketEvent` |
| `format_symbol()` | 심볼 포맷 정규화 | `str` |

### **검증 함수**
| 함수 | 용도 | 반환 타입 |
|------|------|-----------|
| `validate_symbols()` | 심볼 형식 검증 | `bool` |
| `validate_callback()` | 콜백 함수 검증 | `bool` |
| `is_websocket_connected()` | 연결 상태 확인 | `bool` |

---

## 📈 **모니터링 변수**

### **메트릭 수집**
| 변수 | 타입 | 용도 |
|------|------|------|
| `message_count` | `int` | 수신 메시지 수 |
| `connection_uptime` | `float` | 연결 지속 시간 |
| `subscription_count` | `int` | 활성 구독 수 |
| `rate_limit_hits` | `int` | Rate Limit 도달 횟수 |

### **상태 플래그**
| 변수 | 타입 | 용도 |
|------|------|------|
| `is_connected` | `bool` | 연결 상태 |
| `is_authenticated` | `bool` | 인증 상태 |
| `pending_subscriptions` | `int` | 대기 중인 구독 수 |

---

## 🚨 **예외 처리**

### **예외 클래스**
| 예외 | 발생 상황 | 처리 방법 |
|------|-----------|-----------|
| `WebSocketConnectionError` | 연결 실패 | 재연결 시도 |
| `SubscriptionError` | 구독 실패 | 구독 재시도 |
| `RateLimitExceededError` | Rate Limit 초과 | 대기 후 재시도 |
| `AuthenticationError` | 인증 실패 | API 키 확인 |

### **에러 코드**
| 코드 | 의미 | 처리 방안 |
|------|------|-----------|
| `1000` | 정상 종료 | - |
| `1001` | 서버 재시작 | 재연결 |
| `1002` | 프로토콜 오류 | 연결 재설정 |
| `4001` | 인증 실패 | API 키 재확인 |

---

## 🔧 **디버깅 도구**

### **로깅 레벨**
| 레벨 | 용도 | 예시 |
|------|------|------|
| `DEBUG` | 상세 디버깅 | 메시지 전송/수신 |
| `INFO` | 일반 정보 | 구독 성공/실패 |
| `WARNING` | 경고 상황 | Rate Limit 근접 |
| `ERROR` | 오류 상황 | 연결 실패 |

### **성능 측정**
| 메서드 | 용도 | 단위 |
|--------|------|------|
| `measure_latency()` | 응답 지연 측정 | 밀리초 |
| `track_throughput()` | 처리량 측정 | 메시지/초 |
| `monitor_memory()` | 메모리 사용량 | MB |
