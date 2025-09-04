# 🧪 WebSocket v6 기능 검증 체크리스트

## 📋 **기본 기능 검증**

### **✅ 1. 단일 데이터 타입 구독**
```python
# 테스트 코드
client = WebSocketClient("test_single")

# ticker 구독 테스트
await client.subscribe_ticker(['KRW-BTC'], lambda e: print(f"Ticker: {e.trade_price}"))

# orderbook 구독 테스트
await client.subscribe_orderbook(['KRW-BTC'], lambda e: print(f"Orderbook: {len(e.orderbook_units)}"))

# trade 구독 테스트
await client.subscribe_trade(['KRW-BTC'], lambda e: print(f"Trade: {e.trade_volume}"))
```

**검증 항목:**
- [ ] 스냅샷 데이터 즉시 수신
- [ ] 실시간 데이터 지속 수신
- [ ] 콜백 함수 정상 호출
- [ ] 데이터 타입 정확성

### **✅ 2. 복합 구독 (동일 클라이언트)**
```python
# 테스트 코드
client = WebSocketClient("test_composite")

await client.subscribe_ticker(['KRW-BTC'], on_ticker)
await client.subscribe_orderbook(['KRW-BTC'], on_orderbook)
await client.subscribe_trade(['KRW-BTC'], on_trade)
```

**검증 항목:**
- [ ] 모든 데이터 타입 동시 수신
- [ ] 각 콜백 독립적 호출
- [ ] 데이터 누락 없음
- [ ] 메모리 사용량 적정

### **✅ 3. 다중 심볼 구독**
```python
# 테스트 코드
symbols = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA', 'KRW-DOT']
await client.subscribe_ticker(symbols, on_multi_ticker)
```

**검증 항목:**
- [ ] 모든 심볼 데이터 수신
- [ ] 심볼별 구분 정확
- [ ] 처리 성능 적정
- [ ] Rate Limit 준수

---

## 🔄 **구독 관리 검증**

### **✅ 4. 구독 교체 (심볼 변경)**
```python
# 테스트 시나리오
client = WebSocketClient("test_replacement")

# 초기 구독
await client.subscribe_ticker(['KRW-BTC'], callback)
await asyncio.sleep(2)  # 데이터 수신 확인

# 심볼 변경
await client.subscribe_ticker(['KRW-ETH'], callback)
await asyncio.sleep(2)  # 새 데이터 수신 확인
```

**검증 항목:**
- [ ] 기존 구독 자동 해제
- [ ] 새 구독 즉시 활성화
- [ ] 중간 데이터 누락 없음
- [ ] cleanup() 자동 처리

### **✅ 5. 구독 추가 vs 교체**
```python
# 테스트 A: 동일 데이터 타입 추가 (교체)
await client.subscribe_ticker(['KRW-BTC'], callback)
await client.subscribe_ticker(['KRW-ETH'], callback)  # BTC 해제, ETH 구독

# 테스트 B: 다른 데이터 타입 추가 (누적)
await client.subscribe_ticker(['KRW-BTC'], ticker_callback)
await client.subscribe_orderbook(['KRW-BTC'], orderbook_callback)  # 둘 다 유지
```

**검증 항목:**
- [ ] 교체 vs 누적 동작 구분
- [ ] 의도한 구독 상태 달성
- [ ] 불필요한 네트워크 요청 없음

### **✅ 6. 정리 (cleanup) 기능**
```python
# 테스트 코드
client = WebSocketClient("test_cleanup")
await client.subscribe_ticker(['KRW-BTC'], callback)
await client.subscribe_orderbook(['KRW-BTC'], callback)

start_time = time.time()
await client.cleanup()
cleanup_time = time.time() - start_time

print(f"Cleanup 소요시간: {cleanup_time:.3f}초")
```

**검증 항목:**
- [ ] 모든 구독 완전 해제
- [ ] 메모리 정리 완료
- [ ] 성능 허용 범위 (< 2초)
- [ ] 예외 발생 없음

---

## 🚀 **고급 기능 검증**

### **✅ 7. Private 데이터 구독**
```python
# API 키 필요
client = WebSocketClient("test_private")

await client.subscribe_my_order(on_my_order)
await client.subscribe_my_asset(on_my_asset)
```

**검증 항목:**
- [ ] 인증 정상 처리
- [ ] Private 데이터 수신
- [ ] 보안 요구사항 충족
- [ ] Public과 분리 동작

### **✅ 8. 대량 심볼 처리**
```python
# 100개 심볼 테스트
large_symbols = [f"KRW-COIN{i:03d}" for i in range(100)]  # 가상 심볼
await client.subscribe_ticker(large_symbols, callback)
```

**검증 항목:**
- [ ] 메시지 크기 제한 통과
- [ ] 처리 성능 유지
- [ ] 메모리 사용량 안정
- [ ] 모든 심볼 데이터 수신

### **✅ 9. 동시 클라이언트 운영**
```python
# 여러 클라이언트 동시 실행
clients = []
for i in range(10):
    client = WebSocketClient(f"test_concurrent_{i}")
    await client.subscribe_ticker(['KRW-BTC'], callback)
    clients.append(client)
```

**검증 항목:**
- [ ] 클라이언트 간 독립성
- [ ] 리소스 격리
- [ ] 성능 저하 없음
- [ ] 안정적 동시 실행

---

## ⚡ **성능 및 안정성 검증**

### **✅ 10. 연결 안정성**
```python
# 장시간 연결 테스트
client = WebSocketClient("test_stability")
await client.subscribe_ticker(['KRW-BTC'], callback)

# 1시간 동안 데이터 수신 모니터링
start_time = time.time()
message_count = 0

while time.time() - start_time < 3600:  # 1시간
    await asyncio.sleep(1)
    # 메시지 수신 카운트 체크
```

**검증 항목:**
- [ ] 연결 지속성 (1시간+)
- [ ] 자동 재연결 동작
- [ ] 데이터 연속성 보장
- [ ] 메모리 누수 없음

### **✅ 11. Rate Limiter 검증**
```python
# 빠른 연속 요청 테스트
client = WebSocketClient("test_rate_limit")

for i in range(20):
    await client.subscribe_ticker([f'KRW-BTC'], callback)
    await asyncio.sleep(0.05)  # 50ms 간격
```

**검증 항목:**
- [ ] Rate Limit 적용 확인
- [ ] 요청 대기 처리
- [ ] 에러 발생 없음
- [ ] 순서 보장

### **✅ 12. 에러 처리**
```python
# 예외 상황 테스트
try:
    # 잘못된 심볼 구독
    await client.subscribe_ticker(['INVALID-SYMBOL'], callback)
except Exception as e:
    print(f"예상된 에러: {e}")

try:
    # 네트워크 끊김 시뮬레이션
    # (실제로는 네트워크 인터페이스 비활성화)
    pass
except Exception as e:
    print(f"네트워크 에러 처리: {e}")
```

**검증 항목:**
- [ ] 잘못된 입력 처리
- [ ] 네트워크 에러 복구
- [ ] 예외 전파 제어
- [ ] 로그 기록 정확성

---

## 🎯 **실전 시나리오 검증**

### **✅ 13. 차트 애플리케이션 시뮬레이션**
```python
class ChartSimulation:
    async def test_multi_chart(self):
        # 4개 차트 동시 운영
        charts = {}
        symbols = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA']

        for i, symbol in enumerate(symbols):
            client = WebSocketClient(f"chart_{i}")
            await client.subscribe_ticker([symbol], self.on_ticker)
            await client.subscribe_orderbook([symbol], self.on_orderbook)
            charts[i] = {'client': client, 'symbol': symbol}

        # 심볼 변경 테스트
        await charts[0]['client'].subscribe_ticker(['KRW-DOGE'], self.on_ticker)
```

### **✅ 14. 자동매매 봇 시뮬레이션**
```python
class TradingBotSimulation:
    async def test_trading_scenario(self):
        # 시장 모니터링
        market_monitor = WebSocketClient("market_monitor")
        await market_monitor.subscribe_ticker(
            ['KRW-BTC', 'KRW-ETH', 'KRW-XRP'],
            self.on_price_change
        )

        # 주문 관리
        order_manager = WebSocketClient("order_manager")
        await order_manager.subscribe_my_order(self.on_order_update)

        # 시뮬레이션 실행
        await asyncio.sleep(60)  # 1분간 실행
```

---

## 📊 **검증 결과 기록 템플릿**

### **기능별 체크리스트**
```
[ ] 1. 단일 데이터 타입 구독
    - 스냅샷 수신: ⏱️ __초
    - 실시간 데이터: ✅/❌
    - 메모리 사용량: __MB

[ ] 2. 복합 구독
    - 동시 수신: ✅/❌
    - 성능 영향: __% 증가

[ ] 3. 다중 심볼 구독
    - 최대 테스트 심볼 수: __개
    - 처리 지연: ⏱️ __ms

[ ] 4. 구독 교체
    - 교체 완료 시간: ⏱️ __초
    - 데이터 누락: ✅/❌

[ ] 5. cleanup 성능
    - 소요 시간: ⏱️ __초
    - 메모리 정리: ✅/❌
```

### **성능 벤치마크**
```
연결 설정 시간: ⏱️ ___초
첫 데이터 수신: ⏱️ ___초
평균 응답 지연: ⏱️ ___ms
메모리 사용량: ___MB
CPU 사용률: ___%
```

### **안정성 테스트**
```
연속 실행 시간: ⏱️ ___시간
총 메시지 수: ___개
에러 발생 횟수: ___회
재연결 횟수: ___회
```

---

## 🎉 **검증 완료 기준**

### **✅ 기본 통과 조건**
- 모든 기본 기능 (1-6) 정상 동작
- cleanup() 성능 2초 이내
- 메모리 누수 없음
- 30분 이상 안정 실행

### **🚀 고급 통과 조건**
- Private 데이터 연동 성공
- 100개 이상 심볼 처리
- 다중 클라이언트 안정 실행
- 1시간 이상 무중단 운영

### **💎 완벽 통과 조건**
- 모든 실전 시나리오 성공
- Rate Limiter 완벽 대응
- 에러 복구 메커니즘 검증
- 프로덕션 환경 준비 완료

이 체크리스트를 통해 WebSocket v6 시스템의 모든 기능을 체계적으로 검증하고 실전 준비를 완료하실 수 있습니다! 🎯
