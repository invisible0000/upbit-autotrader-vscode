# 🚀 **통합 마켓 데이터 백본 시스템 - 점진적 진화형 개발 가이드**

## 📋 **LLM 승계 및 영속성 개발 전략**

> **핵심 철학**: 무한한 테스트 능력을 활용하여 점진적으로 진화하는 개발 사이클로 완벽한 시스템을 구축

---

## 🎯 **개발 전략 개요**

### **핵심 원칙**
1. **점진적 진화**: 1차 구현 → 테스트 → 피드백 → 개선의 반복
2. **무한 테스트**: 각 단계마다 철저한 검증
3. **승계 가능성**: 다른 LLM 에이전트가 언제든 이어받을 수 있는 구조
4. **영속성 확보**: 모든 결정과 진화 과정을 문서화

### **개발 사이클 패턴**
```
Phase N: 구현 → 테스트 → 검증 → 문서화 → 다음 Phase 설계
         ↑                                           ↓
         ← ← ← ← ← 피드백 기반 개선 ← ← ← ← ← ← ← ← ← ←
```

---

## 📚 **LLM 문서 가이드라인 준수**

### **문서 구조 표준**
- **상황 요약**: 현재 위치와 목표
- **기술적 맥락**: 아키텍처와 설계 결정
- **구현 현황**: 완료/진행/예정 상태
- **테스트 결과**: 검증된 사실들
- **다음 단계**: 명확한 액션 아이템
- **승계 정보**: 새로운 에이전트를 위한 진입점

### **코드 진화 추적**
- **버전 태깅**: 각 진화 단계마다 명확한 버전
- **변경 이유**: 왜 이런 결정을 했는지 기록
- **테스트 케이스**: 검증한 시나리오들
- **성능 메트릭**: 측정 가능한 개선 지표

---

## 🔄 **진화형 개발 로드맵**

### **Phase 1: MVP 백본 구축 (현재 단계)**
**목표**: 기본적인 통합 API가 동작하는 최소 기능 제품

#### **Phase 1.1: 기본 인프라**
- [ ] `MarketDataBackbone` 기본 클래스 구현
- [ ] 간단한 REST API 래퍼
- [ ] 기본 WebSocket 연결 관리
- [ ] 단일 데이터 타입 지원 (ticker만)

**검증 목표**:
```python
backbone = MarketDataBackbone()
ticker = await backbone.get_ticker("KRW-BTC")
assert ticker.current_price > 0
```

#### **Phase 1.2: 기본 데이터 통합**
- [ ] REST vs WebSocket 응답 포맷 차이 분석
- [ ] 기본 Data Unifier 구현
- [ ] 간단한 채널 선택 로직
- [ ] 에러 처리 기본 구조

**검증 목표**:
```python
# REST와 WebSocket에서 같은 포맷으로 응답
rest_ticker = await backbone.get_ticker("KRW-BTC", strategy="rest_only")
ws_ticker = await backbone.get_ticker("KRW-BTC", strategy="websocket_only")
assert rest_ticker.current_price == ws_ticker.current_price  # 같은 시점
```

#### **Phase 1.3: 기본 테스트 스위트**
- [ ] 단위 테스트 (각 컴포넌트)
- [ ] 통합 테스트 (전체 플로우)
- [ ] 실제 업비트 API 연동 테스트
- [ ] 성능 기준선 측정

### **Phase 2: 지능적 최적화 (다음 단계)**
**목표**: 상황에 맞는 최적 채널 선택과 성능 향상

#### **Phase 2.1: 성능 기반 라우팅**
- [ ] 응답 시간 측정 시스템
- [ ] 성공률 추적
- [ ] 동적 채널 선택 알고리즘
- [ ] A/B 테스트 프레임워크

#### **Phase 2.2: 캐싱 및 최적화**
- [ ] 지능적 캐싱 시스템
- [ ] 중복 요청 제거
- [ ] 배치 요청 최적화
- [ ] 메모리 사용량 최적화

### **Phase 3: 고급 기능 (이후 단계)**
**목표**: 프로덕션급 안정성과 고급 기능

#### **Phase 3.1: 장애 복구**
- [ ] Circuit Breaker 패턴
- [ ] 자동 재시도 로직
- [ ] 헬스 체크 시스템
- [ ] 알림 및 모니터링

#### **Phase 3.2: 전체 API 지원**
- [ ] 모든 데이터 타입 지원
- [ ] 실시간 구독 관리
- [ ] 배치 데이터 처리
- [ ] 커스텀 확장 포인트

---

## 🧪 **테스트 전략**

### **테스트 레벨**
1. **단위 테스트**: 각 컴포넌트 독립 검증
2. **통합 테스트**: 컴포넌트 간 상호작용
3. **시스템 테스트**: 전체 시나리오 검증
4. **성능 테스트**: 응답시간, 처리량, 메모리
5. **스트레스 테스트**: 극한 상황 대응
6. **장애 테스트**: 네트워크/서버 장애 상황

### **테스트 시나리오 템플릿**
```python
class BackboneTestScenario:
    """표준 테스트 시나리오 템플릿"""

    def setup_scenario(self):
        """테스트 환경 설정"""
        pass

    def test_normal_operation(self):
        """정상 동작 검증"""
        pass

    def test_error_handling(self):
        """에러 상황 처리"""
        pass

    def test_performance(self):
        """성능 요구사항 검증"""
        pass

    def verify_data_consistency(self):
        """데이터 일관성 검증"""
        pass
```

### **성능 기준선**
- **응답 시간**: < 100ms (90%ile)
- **처리량**: > 100 req/sec
- **메모리**: < 100MB
- **가용성**: > 99.9%

---

## 📊 **진화 추적 시스템**

### **진화 메트릭**
```yaml
phase_1_1:
  completion_date: "2025-08-20"
  test_coverage: 85%
  performance_baseline:
    rest_latency: 150ms
    websocket_latency: 50ms
    memory_usage: 45MB
  issues_found: 3
  issues_resolved: 3

phase_1_2:
  completion_date: "TBD"
  target_improvements:
    - unified_data_format: 100%
    - channel_selection_accuracy: 90%
    - error_recovery_rate: 95%
```

### **결정 로그**
```markdown
# 결정 001: REST API 우선 전략
- **날짜**: 2025-08-19
- **이유**: WebSocket은 연결 관리가 복잡하므로 안정성을 위해 REST 우선
- **트레이드오프**: 실시간성 vs 안정성
- **검증 방법**: 응답시간 비교 테스트
- **결과**: 90% 시나리오에서 안정적 동작 확인
```

---

## 🔄 **승계 가이드라인**

### **새로운 에이전트 온보딩**
1. **현재 상황 파악**: `docs/CURRENT_STATUS.md` 읽기
2. **아키텍처 이해**: `docs/UNIFIED_MARKET_DATA_BACKBONE_V2_ARCHITECTURE.md` 검토
3. **진행 상황 확인**: `docs/DEVELOPMENT_PROGRESS.md` 확인
4. **테스트 실행**: `pytest` 로 현재 상태 검증
5. **다음 단계 확인**: `docs/NEXT_ACTIONS.md` 검토

### **작업 인수인계 템플릿**
```markdown
## 🚀 작업 인수인계 (Phase X.Y)

### 현재 상황
- **완료된 작업**: [구체적 목록]
- **진행 중인 작업**: [현재 상태]
- **블로커**: [해결해야 할 이슈들]

### 기술적 컨텍스트
- **아키텍처 결정**: [핵심 설계 결정들]
- **구현 방식**: [채택한 패턴들]
- **성능 현황**: [측정된 메트릭들]

### 다음 에이전트를 위한 액션
1. [ ] [구체적 작업 1]
2. [ ] [구체적 작업 2]
3. [ ] [검증 방법]

### 유의사항
- [특별히 주의해야 할 점들]
- [알려진 이슈들]
- [성능 고려사항]
```

---

## 📁 **문서 구조**

```
docs/
├── UNIFIED_MARKET_DATA_BACKBONE_V2_ARCHITECTURE.md  # 전체 아키텍처
├── EVOLUTIONARY_DEVELOPMENT_GUIDE.md                # 본 문서
├── CURRENT_STATUS.md                                # 현재 진행 상황
├── DEVELOPMENT_PROGRESS.md                          # 상세 진행 로그
├── NEXT_ACTIONS.md                                  # 다음 단계 액션
├── TEST_RESULTS.md                                  # 테스트 결과 누적
├── PERFORMANCE_METRICS.md                           # 성능 측정 결과
├── DECISION_LOG.md                                  # 설계 결정 기록
└── phases/
    ├── phase_1/
    │   ├── objectives.md                            # Phase 1 목표
    │   ├── implementation_guide.md                  # 구현 가이드
    │   ├── test_scenarios.md                        # 테스트 시나리오
    │   └── completion_report.md                     # 완료 보고서
    ├── phase_2/
    └── phase_3/
```

---

## 🎯 **즉시 시작할 액션**

### **1. 현재 상황 문서화**
- [ ] `CURRENT_STATUS.md` 생성
- [ ] 기존 구현체 분석 결과 정리
- [ ] Phase 1.1 목표 구체화

### **2. Phase 1.1 킥오프**
- [ ] MVP 백본 클래스 설계
- [ ] 기본 테스트 케이스 작성
- [ ] 첫 번째 구현 시작

### **3. 개발 환경 설정**
- [ ] 테스트 자동화 설정
- [ ] 성능 측정 도구 준비
- [ ] CI/CD 파이프라인 구성

---

## ✅ **성공 지표**

### **단기 (Phase 1)**
- [ ] 기본 API 호출 성공률 > 95%
- [ ] REST/WebSocket 데이터 일관성 100%
- [ ] 테스트 커버리지 > 80%

### **중기 (Phase 2)**
- [ ] 응답시간 50% 개선
- [ ] 자동 채널 선택 정확도 > 90%
- [ ] 시스템 안정성 > 99%

### **장기 (Phase 3)**
- [ ] 프로덕션 배포 준비 완료
- [ ] 전체 업비트 API 지원
- [ ] 커뮤니티 피드백 반영

---

**다음 에이전트에게**: 이 문서를 기준으로 `CURRENT_STATUS.md`를 먼저 생성하고, Phase 1.1부터 시작하세요. 모든 변경사항은 반드시 테스트와 함께 문서화하세요.
