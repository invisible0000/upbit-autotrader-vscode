"""
WebSocket 구독 매니저 개선 계획

현재 문제점과 해결 방안을 정리한 문서입니다.
"""

# ================================================================
# WebSocket 구독 매니저 문제점 분석 및 해결 방안
# ================================================================

## 🚨 현재 문제점

### 1. 구조적 문제
- **개별 구독 처리**: 업비트 다중 심볼 일괄 구독 미활용
- **불필요한 재연결**: 구독 변경 시마다 전체 재연결 → 0.5초 지연 × 2회
- **Smart Router 연동 부족**: 매니저를 우회하는 직접 구독 방식 병행

### 2. 성능 문제
- **모니터링 비활성화**: 실시간 성능 감시 기능 완전 정지
- **비효율적 구독 관리**: 5개 제한이 있지만 실제 다중 구독 성능 미활용

### 3. 아키텍처 문제
- **단일 심볼 중심 설계**: 업비트의 배치 구독 API 패턴과 불일치
- **복잡한 우선순위 로직**: 단순한 구독 요청에 과도한 오버헤드

## ✅ 해결 방안

### Phase 1: 구독 매니저 최적화
1. **배치 구독 지원 추가**
   ```python
   async def request_batch_subscription(
       self,
       symbols: List[str],
       subscription_type: SubscriptionType
   ) -> bool:
       # 여러 심볼을 한 번에 구독
   ```

2. **재연결 최소화**
   ```python
   # 기존: 구독 변경 시 재연결
   await disconnect() -> await connect() -> resubscribe_all()

   # 개선: 추가 구독만 수행 (재연결 없음)
   await subscribe_additional([new_symbols])
   ```

3. **Smart Router 통합 강화**
   ```python
   # Smart Router에서 매니저 우선 사용
   if self.websocket_subscription_manager:
       success = await self.websocket_subscription_manager.request_batch_subscription(
           request.symbols, subscription_type
       )
   ```

### Phase 2: 성능 모니터링 재활성화
1. **실시간 메시지 카운터 복원**
2. **성능 임계값 기반 자동 최적화**
3. **구독 효율성 메트릭 추가**

### Phase 3: 설정 시스템 연동
1. **구독 제한을 SmartRouterConfig로 이동**
2. **성능 임계값도 설정으로 관리**

## 🎯 우선순위

1. **즉시 적용 (High)**: 배치 구독 지원 추가
2. **단기 (Medium)**: Smart Router 통합 강화
3. **중기 (Low)**: 성능 모니터링 재활성화

## 📊 예상 성능 개선

### 기존 방식
- 구독 변경: 재연결 1초 + 재구독 시간
- 개별 구독: N번의 개별 API 호출

### 개선 방식
- 구독 추가: 즉시 배치 구독 (재연결 없음)
- 일괄 구독: 1번의 배치 API 호출

**예상 성능 향상: 3-5배**
