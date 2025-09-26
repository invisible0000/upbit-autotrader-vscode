# 🚨 EVENT LOOP 아키텍처 위기 분석 및 해결 방향

**발견일**: 2025-09-26
**심각도**: CRITICAL
**범위**: 시스템 전체
**분류**: 아키텍처 설계 결함

## 📋 요약 (Executive Summary)

업비트 자동매매 시스템에서 **다중 이벤트 루프 충돌로 인한 Infrastructure Layer 마비** 현상이 발견되었습니다. 이는 단순한 버그가 아닌 **전체 비동기 아키텍처의 근본적 설계 결함**으로 판단됩니다.

### 핵심 문제
- PyQt6/QAsync와 asyncio.new_event_loop() 간의 충돌
- Infrastructure Layer의 공유 리소스(HTTP 세션, Lock)가 서로 다른 이벤트 루프에 바인딩
- 이벤트 기반 시스템과 Infrastructure Layer 간의 아키텍처 불일치

## 🔍 발견된 상황 (Incident Analysis)

### 발생 시나리오
1. **정상 시작**: 호가창 서비스가 QAsync 환경에서 정상 동작
2. **트리거 발생**: 코인리스트 위젯이 격리된 이벤트 루프 생성
3. **시스템 충돌**: 모든 Infrastructure Layer 호출 실패
4. **연쇄 반응**: 전체 API 통신 마비

### 오류 메시지
```
❌ HTTP 요청 중 오류 발생: <asyncio.locks.Lock object> is bound to a different event loop
```

### 영향 범위
- ✅ **호가창**: QAsync 환경에서 정상 (DDD Infrastructure 준수)
- ❌ **코인리스트**: 격리 루프에서 Infrastructure 충돌
- ❌ **향후 모든 기능**: 동일한 패턴 사용 시 같은 문제 발생 예상

## 🏗️ 아키텍처 분석 (Architecture Analysis)

### 현재 시스템 구조
```
┌─────────────────────────────────────────────────────────────┐
│                    PyQt6 Application                        │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │   QAsync Loop   │    │    Isolated Event Loops        │ │
│  │                 │    │  (coin_list_widget 패턴)       │ │
│  │  ┌─────────────┐│    │  ┌─────────────────────────────┐│ │
│  │  │ Orderbook   ││    │  │   CoinList Widget          ││ │
│  │  │ Service     ││    │  │   new_event_loop()          ││ │
│  │  │             ││    │  │   set_event_loop()          ││ │
│  │  └─────────────┘│    │  └─────────────────────────────┘│ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Layer                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │            UpbitPublicClient                            │ │
│  │  • HTTP Session (aiohttp)                              │ │
│  │  • Rate Limiter Locks                                  │ │
│  │  • 공유 리소스들 ← 이벤트 루프 바인딩 충돌!              │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 문제점 식별
1. **이벤트 루프 분리**: 단일 애플리케이션 내 다중 루프 존재
2. **리소스 바인딩**: Infrastructure 리소스가 특정 루프에 고정
3. **격리 패턴의 남용**: `new_event_loop()` 사용으로 격리 시도
4. **아키텍처 불일치**: 이벤트 기반 설계 vs Infrastructure Layer 동기화

## 🎯 근본 원인 분석 (Root Cause Analysis)

### 1. 설계 철학의 충돌
- **이벤트 기반 시스템**: 유연한 컴포넌트 협업 목표
- **Infrastructure Layer**: 공유 리소스 기반 효율성 추구
- **PyQt6/asyncio 혼합**: 서로 다른 비동기 패러다임 공존

### 2. 개발 패턴의 일관성 부족
- **호가창**: QAsync 패턴 (정상 동작)
- **코인리스트**: 격리 루프 패턴 (충돌 발생)
- **향후 컴포넌트**: 패턴 선택의 혼란 예상

### 3. Infrastructure Layer 설계 한계
```python
# 현재 문제 패턴
class UpbitPublicClient:
    def __init__(self):
        self._session = aiohttp.ClientSession()  # 특정 루프에 바인딩됨
        self._rate_limiter = RateLimiter()       # Lock 객체도 루프 종속적
```

## 🚀 해결 방향 제안 (Solution Strategies)

### 전략 A: 통합 이벤트 루프 아키텍처 (권장)
**목표**: 단일 QAsync 루프로 전체 시스템 통합

**장점**:
- 아키텍처 일관성 확보
- Infrastructure Layer 안정성
- 이벤트 기반 시스템과 자연스러운 통합

**단점**:
- 기존 격리 패턴 코드 대규모 수정 필요
- QAsync 학습 곡선

**구현 방향**:
```python
# 통합 패턴 예시
class AsyncComponentBase:
    """모든 UI 컴포넌트의 기본 클래스"""

    @asyncSlot()
    async def load_data(self):
        # QAsync 환경에서 안전한 비동기 호출
        data = await self.service.get_data()
        self.update_ui(data)
```

### 전략 B: Infrastructure Layer 격리 아키텍처
**목표**: 각 이벤트 루프별 독립적인 Infrastructure 인스턴스

**장점**:
- 기존 격리 패턴 유지 가능
- 컴포넌트 독립성 보장

**단점**:
- 리소스 중복 (HTTP 세션, Rate Limiter 등)
- 복잡한 상태 동기화 필요
- 메모리 사용량 증가

**구현 방향**:
```python
# 루프별 격리 패턴
class EventLoopAwareInfrastructure:
    _instances = {}  # 루프별 인스턴스 저장

    @classmethod
    def get_instance(cls):
        loop = asyncio.get_event_loop()
        if loop not in cls._instances:
            cls._instances[loop] = UpbitPublicClient()
        return cls._instances[loop]
```

### 전략 C: 하이브리드 아키텍처
**목표**: 핵심 기능은 통합, 독립적 기능은 격리

**장점**:
- 점진적 마이그레이션 가능
- 기존 코드 최소 변경

**단점**:
- 아키텍처 복잡성 증가
- 패턴 선택 기준 모호

## 📊 영향도 분석 (Impact Assessment)

### 즉시 영향 (High Priority)
- **코인리스트 기능**: 현재 완전 마비
- **호가창 기능**: 격리 루프 생성 후 불안정
- **전체 API 통신**: 연쇄적 실패 가능성

### 중기 영향 (Medium Priority)
- **신규 기능 개발**: 패턴 선택의 혼란
- **시스템 안정성**: 예측 불가능한 충돌
- **성능 저하**: 리소스 중복 사용

### 장기 영향 (Long-term Risk)
- **아키텍처 부채**: 기술 부채 누적
- **유지보수성**: 복잡성 증가로 인한 개발 속도 저하
- **확장성**: 새로운 기능 추가 시 제약

## 🔬 조사 및 검토 계획 (Investigation Plan)

### Phase 1: 현황 파악 (1-2일)
1. **전체 시스템 이벤트 루프 매핑**
   ```bash
   # 검색 대상
   grep -r "new_event_loop\|set_event_loop" upbit_auto_trading/
   grep -r "asyncSlot\|QAsync" upbit_auto_trading/
   grep -r "asyncio.run\|run_until_complete" upbit_auto_trading/
   ```

2. **Infrastructure Layer 의존성 분석**
   - UpbitPublicClient 사용 현황
   - 공유 리소스 식별
   - Rate Limiter 바인딩 상태

3. **이벤트 기반 컴포넌트 목록화**
   - 현재 이벤트 버스 사용 패턴
   - 컴포넌트 간 통신 방식
   - 비동기 처리 패턴 분류

### Phase 2: 아키텍처 결정 (2-3일)
1. **성능 벤치마크**
   - 통합 vs 격리 패턴 성능 비교
   - 메모리 사용량 측정
   - 응답 시간 분석

2. **리스크 평가**
   - 각 전략별 구현 난이도
   - 기존 코드 영향도
   - 마이그레이션 비용

3. **아키텍처 결정 회의**
   - 전략 A/B/C 중 선택
   - 마이그레이션 로드맵 수립
   - 개발 우선순위 설정

### Phase 3: 구현 및 검증 (5-7일)
1. **POC 구현**
   - 선택된 전략의 프로토타입
   - 핵심 기능 검증
   - 성능 및 안정성 테스트

2. **점진적 마이그레이션**
   - 우선순위별 컴포넌트 수정
   - 회귀 테스트 실시
   - 모니터링 시스템 구축

## 💡 권장 결정 사항 (Recommendations)

### 즉시 조치 (24시간 내)
1. **코인리스트 위젯 응급 수정**
   - 격리 루프 제거
   - QAsync 패턴 임시 적용
   - 기본 기능 복구

### 단기 조치 (1주일 내)
1. **아키텍처 결정 및 표준화**
   - 전략 A (통합 아키텍처) 권장
   - 개발 가이드라인 수립
   - 코드 리뷰 체크리스트 작성

### 중기 조치 (1개월 내)
1. **전체 시스템 마이그레이션**
   - 통합 이벤트 루프 아키텍처 적용
   - Infrastructure Layer 재설계
   - 종합 테스트 및 검증

## 🎯 핵심 질문 및 결정 포인트 (Key Decision Points)

### 1. 이벤트 기반 시스템의 미래
**질문**: 현재 이벤트 기반 아키텍처를 유지할 것인가?

**고려사항**:
- 이벤트 기반 시스템의 장점 (유연성, 확장성)
- Infrastructure Layer와의 호환성 문제
- 대안 아키텍처 (Service Layer, Repository Pattern 등)

**권장**: 이벤트 기반 + QAsync 통합 아키텍처

### 2. Infrastructure Layer 설계 철학
**질문**: 공유 리소스 vs 격리된 인스턴스?

**고려사항**:
- Rate Limiter의 글로벌 일관성 필요성
- HTTP 커넥션 풀링 효율성
- 메모리 사용량 vs 안정성

**권장**: 루프 인식 싱글톤 패턴

### 3. 개발 생산성 vs 아키텍처 순수성
**질문**: 완벽한 아키텍처 vs 빠른 기능 구현?

**고려사항**:
- 현재 개발 속도 요구사항
- 기술 부채 허용 수준
- 팀 학습 곡선

**권장**: 점진적 마이그레이션 + 명확한 표준

## 📈 성공 지표 (Success Metrics)

### 기술적 지표
- [ ] 이벤트 루프 충돌 제로화
- [ ] API 호출 성공률 99.9% 이상
- [ ] 메모리 사용량 20% 이하 증가
- [ ] 응답 시간 기존 대비 10% 이내

### 개발 지표
- [ ] 새 컴포넌트 개발 시 패턴 선택 혼란 제거
- [ ] 코드 리뷰 시 아키텍처 이슈 감소
- [ ] 단위 테스트 커버리지 90% 이상 유지

## 🚨 위험 요소 및 대응 방안 (Risk Mitigation)

### 높은 위험
**위험**: 전체 시스템 불안정화
**대응**: 단계별 롤백 계획 수립, 충분한 테스트

**위험**: 개발 일정 지연
**대응**: 핵심 기능 우선 적용, 점진적 확산

### 중간 위험
**위험**: 새로운 버그 도입
**대응**: 엄격한 코드 리뷰, 자동 테스트 강화

**위험**: 팀 학습 곡선
**대응**: 내부 교육, 페어 프로그래밍 활용

## 🔍 추가 조사 항목 (Further Investigation)

1. **다른 PyQt6 + asyncio 프로젝트 사례 조사**
2. **QAsync vs asyncio 성능 벤치마크**
3. **Rate Limiter 아키텍처 최적화 방안**
4. **이벤트 버스 vs 직접 호출 성능 비교**
5. **메모리 누수 가능성 분석**

---

## 🏁 결론 (Conclusion)

이 문제는 **단순한 버그가 아닌 아키텍처 레벨의 근본적 이슈**입니다.

이벤트 기반 시스템 자체는 문제없지만, **PyQt6 환경에서 asyncio와의 통합 방식**에 대한 명확한 표준이 필요합니다.

**통합 QAsync 아키텍처**로의 전환을 권장하며, 이를 통해 시스템의 안정성과 개발 생산성을 동시에 확보할 수 있을 것입니다.

**다음 단계**: Phase 1 조사를 즉시 시작하고, 코인리스트 위젯 응급 수정을 병행하여 시스템 안정성을 우선 확보할 것을 제안합니다.
