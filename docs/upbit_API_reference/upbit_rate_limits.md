# 업비트 API Rate Limits 정리

> **업비트 공식 문서 기준**: https://docs.upbit.com/kr/reference/rate-limits
> **마지막 업데이트**: 2025년 8월 30일

## 📋 요약

- **제한 단위**: 초(Second) 단위 적용
- **제한 범위**: IP 단위 (시세조회) / 계정 단위 (거래/자산)
- **초과 시**: `429 Too Many Requests` → 지속 시 `418 IP/계정 차단`

---

## 🚀 REST API Rate Limits

### **📊 Quotation API (시세 조회) - IP 단위**
| 그룹 | RPS | 엔드포인트 | 설명 |
|------|-----|------------|------|
| **market** | **10** | `/market/all` | 페어 목록 조회 |
| **candle** | **10** | `/candles/minutes/{unit}` | 분 캔들 조회 |
| | | `/candles/days` | 일 캔들 조회 |
| | | `/candles/weeks` | 주 캔들 조회 |
| | | `/candles/months` | 월 캔들 조회 |
| | | `/candles/seconds` | 초 캔들 조회 |
| **trade** | **10** | `/trades/ticks` | 페어 체결 이력 조회 |
| **ticker** | **10** | `/ticker` | 페어 현재가 조회 |
| | | `/tickers` | 마켓 현재가 조회 |
| **orderbook** | **10** | `/orderbook` | 호가 정보 조회 |

### **🔐 Exchange API (거래/자산) - 계정 단위**
| 그룹 | RPS | 엔드포인트 | 설명 |
|------|-----|------------|------|
| **default** | **30** | `/accounts` | 계정 잔고 조회 |
| | | `/orders/chance` | 주문 가능정보 조회 |
| | | `/orders` (GET) | 개별/목록 주문 조회 |
| | | `/orders/open` | 체결 대기 주문 조회 |
| | | `/orders/closed` | 종료 주문 조회 |
| | | `/orders/{uuid}` (DELETE) | 개별 주문 취소 |
| | | `/orders` (DELETE) | 지정 주문 목록 취소 |
| | | `/withdraws` | 출금 관련 API |
| | | `/deposits` | 입금 관련 API |
| **order** | **8** | `/orders` (POST) | 주문 생성 |
| | | `/orders/cancel_and_new` | 취소 후 재주문 |
| **order-cancel-all** | **0.5** | `/orders/cancel_all` | 주문 일괄 취소 |
| | | | **(2초당 1회)** |

---

## 🌐 WebSocket Rate Limits

| 그룹 | RPS | RPM | 설명 |
|------|-----|-----|------|
| **websocket-connect** | **5** | - | WebSocket 연결 요청 |
| **websocket-message** | **5** | **100** | 데이터 요청 메시지 전송 |

### **WebSocket 제한 단위**
- **인증 없음**: IP 단위 (시세 정보만 구독)
- **인증 포함**: 계정 단위 (내 주문/자산 포함)

---

## ⚠️ 특별 제한 사항

### **Origin 헤더 포함 요청**
- **제한**: `10초당 1회`
- **대상**: 시세 조회 REST API + WebSocket 요청
- **적용**: Origin 헤더가 포함된 모든 요청

---

## 📊 잔여 요청 수 확인

### **Remaining-Req 헤더**
```
Remaining-Req: group=default; min=1800; sec=29
```

- **group**: Rate Limit 그룹명
- **min**: ⚠️ **Deprecated** (고정값, 무시)
- **sec**: **현재 잔여 요청 수** (중요!)

---

## 🛡️ 에러 처리

### **429 Too Many Requests**
- **원인**: 초당 최대 허용 요청 수 초과
- **대응**: 잠시 대기 후 재시도

### **418 IP/계정 차단**
- **원인**: 429 에러 후 지속적인 요청
- **대응**: 응답에 포함된 차단 시간만큼 대기
- **특징**: 정책 위반 반복 시 차단 시간 점진적 증가

---

## 💡 구현 권장사항

### **1. 시간 간격 제어**
```python
# 각 그룹별 최소 간격
min_intervals = {
    'quotation': 100,    # 100ms (10 RPS)
    'default': 33,       # 33ms (30 RPS)
    'order': 125,        # 125ms (8 RPS)
    'cancel_all': 2000,  # 2000ms (0.5 RPS)
    'websocket': 200     # 200ms (5 RPS)
}
```

### **2. Remaining-Req 모니터링**
```python
# 응답 헤더 확인
remaining = response.headers.get('Remaining-Req')
if remaining:
    # "group=default; min=1800; sec=29" 파싱
    sec_value = parse_remaining_sec(remaining)
    if sec_value <= 5:  # 잔여 5개 이하시 대기
        await asyncio.sleep(0.5)
```

### **3. 점진적 백오프**
```python
# 429 에러 발생 시
if response.status == 429:
    backoff_time = min(2 ** retry_count, 10)  # 최대 10초
    await asyncio.sleep(backoff_time)
```

### **4. 글로벌 제한 관리**
```python
# 여러 클라이언트가 동일 IP/계정 사용 시
# 전역 Rate Limiter 인스턴스 공유 필수
shared_limiter = UpbitRateLimiter.get_shared_instance()
```

---

## 🎯 핵심 수치 요약

| API 종류 | 최고 RPS | 최저 RPS | 특이사항 |
|----------|----------|----------|----------|
| 시세 조회 | 10 | 10 | IP 단위, 모든 그룹 동일 |
| 계좌/자산 | 30 | 30 | 계정 단위 |
| 주문 생성 | 8 | 8 | 계정 단위 |
| 일괄 취소 | 0.5 | 0.5 | **2초당 1회!** |
| WebSocket | 5 | 5 | 연결+메시지 각각 |

---

## 🔗 관련 링크

- [업비트 공식 Rate Limits 문서](https://docs.upbit.com/kr/reference/rate-limits)
- [업비트 API 개요](https://docs.upbit.com/kr/reference/api-overview)
- [REST API 가이드](https://docs.upbit.com/kr/reference/rest-api-guide)
- [WebSocket 가이드](https://docs.upbit.com/kr/reference/websocket-guide)
