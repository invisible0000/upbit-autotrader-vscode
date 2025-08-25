## 🚨 WebSocket 성능 및 안정성 개선 필요사항

### 📊 현재 문제 상황 분석

#### 1. WebSocket 연결 불안정성
- **Event loop is closed** 오류 발생
- **Task attached to different loop** 오류
- **재연결 시도가 과도하게 발생** (1초 내 3회)

#### 2. 성능 지연 문제
- 요청 처리 시간: **2~3초** (목표: 1초 이하)
- WebSocket 타임아웃: **0.5초**로 너무 짧음
- REST 폴백이 과도하게 발생

#### 3. Rate Limit 비효율적 사용
- WebSocket 실패 → REST 폴백으로 인한 Rate Limit 낭비
- 업비트 제한(초당 5 WebSocket, 10 REST)을 제대로 활용하지 못함

---

## 🎯 개선 방안

### Phase 1: WebSocket 안정성 개선
1. **Event Loop 관리 개선**
   - asyncio 이벤트 루프 생명주기 관리
   - Task와 Future의 올바른 루프 연결

2. **재연결 로직 최적화**
   - 재연결 간격 조정 (현재: 즉시 → 개선: 100ms 간격)
   - 최대 재시도 횟수 제한

3. **타임아웃 조정**
   - WebSocket 수신 타임아웃: 0.5초 → 2초
   - 연결 타임아웃: 3초 → 5초

### Phase 2: 성능 최적화
1. **응답 시간 목표: 1초 이하**
   - WebSocket 우선 사용으로 실시간 데이터 활용
   - REST 폴백은 마지막 수단으로만 사용

2. **Rate Limit 최적 활용**
   - WebSocket: 초당 5개 구독 완전 활용
   - REST: 초당 10개 요청 효율적 분산

### Phase 3: 테스트 안정성 확보
1. **기본 테스트에서 WebSocket 실패 방지**
   - 연결 품질 사전 검증
   - 안정적인 구독 관리

2. **성능 기준 강화**
   - 모든 요청 1초 이내 완료
   - WebSocket 성공률 95% 이상

---

## 🔧 즉시 개선 필요 항목

### 우선순위 1: WebSocket Event Loop 수정
- `UpbitWebSocketPublicClient`의 asyncio 관리
- Task 생명주기 개선

### 우선순위 2: 타임아웃 및 재연결 최적화
- 현실적인 타임아웃 값 설정
- 스마트한 재연결 전략

### 우선순위 3: 성능 모니터링 강화
- 1초 이내 응답 보장
- Rate Limit 효율성 측정

---

이러한 개선을 통해 **"간단한 테스트에서 WebSocket이 실패하면 안 된다"**는
기본 원칙을 달성할 수 있습니다.
