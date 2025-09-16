# 업비트 Rate Limiter 로직 전체 가이드

> **업비트 자동매매 시스템의 Zero-429 정책을 보장하는 통합 Rate Limiter 구조 및 동작 원리**

## 📋 목차
1. [전체 아키텍처 개요](#전체-아키텍처-개요)
2. [핵심 컴포넌트 구조](#핵심-컴포넌트-구조)
3. [메인 로직 플로우](#메인-로직-플로우)
4. [하이브리드 알고리즘 (타임스탬프 윈도우 + GCRA)](#하이브리드-알고리즘)
5. [동적 조정 메커니즘](#동적-조정-메커니즘)
6. [모니터링 및 자가치유 시스템](#모니터링-및-자가치유-시스템)
7. [파일별 역할 분담](#파일별-역할-분담)

---

## 전체 아키텍처 개요

### 설계 철학
- **Zero-429 정책**: 업비트 서버에서 429 오류를 받지 않도록 사전 방지
- **Lock-Free 설계**: aiohttp 패턴을 사용한 고성능 비동기 처리
- **동적 조정**: 실시간 네트워크 상황에 따른 자동 Rate 조정
- **예방적 스로틀링**: 429 오류 발생 패턴 학습 및 사전 차단
- **지연된 커밋**: API 성공 확인 후에만 실제 사용량 반영

### 주요 특징
```
통합 Rate Limiter v2.0
├── Lock-Free GCRA (Generic Cell Rate Algorithm)
├── 타임스탬프 윈도우 (Fixed Window 보완)
├── 동적 조정 (429 자동 대응)
├── 예방적 스로틀링 (패턴 학습)
└── 자가치유 시스템 (백그라운드 복구)
```

---

## 핵심 컴포넌트 구조

### 1. Rate Limit 그룹 분류
```
UpbitRateLimitGroup:
├── REST_PUBLIC        (10 RPS)   - 공개 API (현재가, 호가, 캔들 등)
├── REST_PRIVATE_DEFAULT (30 RPS) - 개인 API (잔고, 주문 내역 등)
├── REST_PRIVATE_ORDER   (8 RPS)  - 주문 API (매수/매도 주문생성, 취소 후 재주문)
├── WEBSOCKET            (5 RPS)  - 공개/개인 웹소켓 연결
└── REST_PRIVATE_CANCEL_ALL (0.5 RPS) - 전체 주문 취소
```

### 2. 핵심 데이터 구조
```
각 그룹별 상태:
├── GroupStats      - 요청 통계, 429 이력, 성공률
├── TAT (초단위)     - GCRA Theoretical Arrival Time
├── TAT (분단위)     - 웹소켓용 분당 제한 관리
├── 타임스탬프 윈도우  - Fixed Window 방식 보완
└── Waiters Queue   - Lock-Free 대기열 (OrderedDict)
```

---

## 메인 로직 플로우

### A. 기본 요청 처리 흐름

```로직
1. 로직 시작 (acquire 호출)
2. Rate Limit 그룹 판별 (endpoint + method 매핑)
3. 예방적 스로틀링 체크 (최근 429 이력 기반)
4. Lock-Free 토큰 획득 시도
   4a. GCRA TAT 계산 및 지연 시간 산출
   4b. 타임스탬프 윈도우 빈슬롯 확인
   4c. 최종 지연 시간 결정 (MAX(GCRA, 윈도우))
5. 지연 적용 여부 판단
   5a. 지연 없음 → 즉시 진행
   5b. 지연 필요 → Waiter Queue 등록
6. 실제 API 호출 (클라이언트 코드)
7. API 성공 시 commit_timestamp 호출
8. 타임스탬프 윈도우 업데이트 (지연된 커밋)
9. 로직 끝
```

### B. 지연된 커밋 시스템

```로직
API 호출 패턴:
1. await limiter.acquire("/ticker", "GET")     # Rate Limit 체크
2. response = await api_call("/ticker")        # 실제 API 호출
3. if success:
     await limiter.commit_timestamp("/ticker") # 성공 시에만 커밋
4. return response
```

**장점**: 실패한 API 호출은 Rate Limit 사용량에 반영되지 않아 불필요한 제한 방지

---

## 하이브리드 알고리즘

### 타임스탬프 윈도우 + GCRA 결합 방식

```로직
개선된 하이브리드 토큰 소모 로직:
1. 현재 시간 확보 (monotonic)
2. 윈도우 딜레이 계산 (항상 수행)
   - 윈도우 내 요청 수 카운트 및 시차 분석
   - window_delay = 가장 오래된 요청 기준 계산
3. GCRA TAT 기반 지연 계산
   - next_tat = max(현재TAT, 현재시간) + (1/effective_RPS)
   - gcra_delay = max(0, next_tat - 현재시간)
4. 버스트 우선 결정 로직
   - 빈슬롯 있음: 즉시 허용 (final_delay = 0.0)
   - 빈슬롯 없음: MAX(gcra_delay, window_delay) 사용
5. 로깅: 항상 양쪽 딜레이 표시로 알고리즘 비교 분석 가능
6. 지연 시간만큼 대기 후 토큰 소모
```

**🆕 로깅 개선점**:
- **항상 표시**: 윈도우딜레이, GCRA딜레이 모두 계산하여 로그 출력
- **비교 분석**: 어떤 알고리즘이 주도하는지 명확히 표시
- **결정 근거**: 버스트허용/GCRA주도/윈도우주도 등 결정 이유 명시

### 동적 윈도우 크기 조정
- **기본 크기**: RPS와 동일 (예: 10 RPS → 10개 윈도우)
- **429 발생 시**: 윈도우 크기 축소 (보수적 모드)
- **안정화 후**: 점진적 복구 (5분 주기)

---

## 동적 조정 메커니즘

### 1. 429 오류 감지 및 대응

```로직
429 오류 처리:
1. notify_429_error 호출
2. 그룹별 통계에 오류 기록
3. Rate 비율 즉시 조정 (예: 1.0 → 0.7)
4. 예방적 스로틀링 활성화
5. 복구 타이머 시작 (5분 후 점진적 복구)
```

### 2. 적응형 전략

```
AdaptiveStrategy 종류:
├── CONSERVATIVE  - 안정성 우선 (Zero-429 최우선, 기본값)
├── BALANCED     - 균형잡힌 조정 (개발 예정)
└── AGGRESSIVE   - 처리량 우선 (개발 예정)

💡 현재 상태: 모든 그룹이 CONSERVATIVE 전략 사용
- 기본 reduction_ratio: 0.8 (429 발생 시 80%로 감소)
- 최소 비율: 0.5 (50% 이하로는 감소하지 않음)
- 복구 주기: 5분 후 점진적 복구 시작
```

**적용 시점**:
- **기본 적용**: 시스템 시작 시 모든 Rate Limit 그룹에 기본 적용 (평상시에도 적용중)
- **429 발생 시**: 동적 조정 메커니즘이 작동하여 실시간 비율 조정
- **미래 확장**: BALANCED, AGGRESSIVE 전략은 향후 구현 예정 (현재는 CONSERVATIVE만 구현)

### 💡 Rate Ratio 적용 메커니즘 (핵심)

**Rate Ratio가 실제로 적용되는 시점과 방법**:

```로직
Rate Ratio 적용 흐름:
1. 시스템 시작: current_rate_ratio = 1.0 (100%)
2. 429 발생: current_rate_ratio = 1.0 × 0.8 = 0.8 (80%)
3. 모든 요청에서 실시간 적용:
   - Effective RPS = Base RPS × current_rate_ratio
   - 예: 10 RPS × 0.8 = 8 RPS (실제 처리 속도)
4. GCRA 토큰 간격 조정:
   - increment = 1.0 / (config.rps × rate_ratio)
   - 예: 1.0 / (10 × 0.8) = 0.125초 간격 (vs 원래 0.1초)
5. 결과: 자동으로 더 긴 지연 시간 적용
```

**코드 위치**:
- `AtomicTATManager._check_basic_gcra()`: `increment = 1.0 / (config.rps * rate_ratio)`
- `UnifiedUpbitRateLimiter.get_comprehensive_status()`: `effective_rps = config.rps * stats.current_rate_ratio`

**핵심 포인트**:
- ✅ **모든 요청**: Rate ratio는 429 없어도 모든 요청에서 확인됨 (기본값 1.0)
- ✅ **실시간 적용**: GCRA 계산 시 매번 current_rate_ratio 사용
- ✅ **자동 지연**: Rate ratio 감소 → Effective RPS 감소 → 토큰 간격 증가 → 자동 지연 증가
- ❌ **별도 강제 지연 없음**: Rate ratio는 기존 GCRA 메커니즘을 통해 자연스럽게 적용

### 3. 예방적 스로틀링

```로직
예방적 지연 계산:
1. 최근 30초 내 429 오류 수집
2. 시간 경과에 따른 감쇠 적용
   - decay_factor = 1.0 - (경과시간 / 30초)
3. 지연 시간 = 기본지연 × 오류수 × 감쇠율
4. 계산된 지연 시간만큼 추가 대기
```

---

## 모니터링 및 자가치유 시스템

### 1. 실시간 모니터링 (RateLimitMonitor)

```로직
모니터링 수집 항목:
├── 429 이벤트 (시간, 엔드포인트, 응답 헤더)
├── 요청 성공율 (그룹별, 시간별)
├── 평균 응답 시간 추적
├── Rate 조정 이력 기록
└── 일일/시간별 통계 생성
```

### 2. 자가치유 시스템 (SelfHealingTaskManager)

```로직
자가치유 프로세스:
1. 백그라운드 태스크 상태 모니터링
2. 중단된 태스크 자동 감지
3. 복구 로직 실행 (재시작 + 상태 복원)
4. 복구 실패 시 알림 및 안전 모드 전환
```

### 3. 타임아웃 보장 (TimeoutAwareRateLimiter)

```로직
타임아웃 처리:
1. 모든 대기 작업에 최대 타임아웃 적용
2. 타임아웃 초과 시 자동 해제
3. 좀비 Waiter 방지 및 메모리 누수 차단
```

---

## 파일별 역할 분담

### 📁 upbit_rate_limiter.py
- **역할**: 메인 Rate Limiter 클래스 (UnifiedUpbitRateLimiter)
- **핵심 메서드**:
  - `acquire()`: 토큰 획득 요청
  - `commit_timestamp()`: 지연된 커밋 실행
  - `notify_429_error()`: 429 오류 알림
  - `_acquire_token_lock_free()`: Lock-Free 토큰 소모
- **특징**: 전체 로직의 중심 허브 역할

### 📁 upbit_rate_limiter_managers.py
- **역할**: 보조 매니저 클래스들
- **주요 클래스**:
  - `SelfHealingTaskManager`: 백그라운드 태스크 자가치유
  - `TimeoutAwareRateLimiter`: 타임아웃 보장 시스템
  - `AtomicTATManager`: 원자적 TAT 및 윈도우 관리
- **특징**: 안정성 및 신뢰성 보장

### 📁 upbit_rate_limiter_monitoring.py
- **역할**: 모니터링 및 통계 시스템
- **핵심 기능**:
  - `log_429_error()`: 429 이벤트 상세 기록
  - `log_request_success()`: 성공 요청 통계
  - `get_daily_429_report()`: 일일 429 리포트 생성
- **특징**: 성능 분석 및 디버깅 지원

### 📁 upbit_rate_limiter_timing.py
- **역할**: 정밀 시간 관리 시스템
- **핵심 클래스**:
  - `PrecisionTimeManager`: 고정밀 시간 계산
  - `PreciseRateLimitTimer`: 정밀한 대기 시간 제어
- **특징**: 마이크로초 단위 정밀도 보장

### 📁 upbit_rate_limiter_types.py
- **역할**: 타입 정의 및 데이터 구조
- **주요 타입**:
  - `UpbitRateLimitGroup`: Rate Limit 그룹 열거형
  - `UnifiedRateLimiterConfig`: 설정 데이터클래스
  - `GroupStats`, `WaiterInfo`: 상태 추적 구조체
- **특징**: 타입 안전성 및 명확한 인터페이스 제공

---

## 🎯 핵심 동작 원리 요약

### 1. Zero-429 보장 방법
- **사전 예측**: GCRA + 타임스탬프 윈도우로 정확한 지연 계산
- **동적 조정**: 429 발생 시 즉시 Rate 감소 및 점진적 복구
- **예방적 지연**: 과거 429 패턴 학습하여 사전 차단

### 2. 고성능 달성 방법
- **Lock-Free**: asyncio.Future 기반 대기열로 락 경합 제거
- **원자적 연산**: 원자적 TAT 업데이트로 동시성 안전성 보장
- **지연된 커밋**: 실패한 요청은 Rate 사용량에 반영하지 않음

### 3. 안정성 보장 방법
- **자가치유**: 백그라운드 태스크 자동 복구
- **타임아웃 보장**: 모든 대기 작업에 최대 시간 제한
- **상세 모니터링**: 모든 이벤트 추적 및 성능 분석

---

## 🚀 사용자 관점에서의 간단한 사용법

```python
# 1. Rate Limiter 획득
limiter = await get_unified_rate_limiter()

# 2. API 호출 전 Rate Limit 체크
await limiter.acquire("/ticker", "GET")

# 3. 실제 API 호출
try:
    response = await upbit_api_call("/ticker")
    # 4. 성공 시 커밋
    await limiter.commit_timestamp("/ticker", "GET")
    return response
except Exception:
    # 실패 시 자동 롤백 (커밋 안함)
    raise
```

**핵심**: 사용자는 단순히 `acquire()` → `API호출` → `commit_timestamp()` 패턴만 사용하면 되며, 내부의 복잡한 Rate Limit 로직은 모두 자동 처리됩니다.

---

*이 문서는 업비트 자동매매 시스템의 Rate Limiter v2.0 기준으로 작성되었습니다. (2025.09.16)*
