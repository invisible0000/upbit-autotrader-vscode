# PRG (PreemptiveRateGuard) + Cloudflare 통합 동작 원리

## 🎯 핵심 개념

**PRG**는 Cloudflare Rate Limiter와 **독립적으로 동작**하여 **429 에러를 선제적으로 방지**하는 시스템입니다.

## 📐 동작 공식

### 1. 기본 공식
```
10 RPS 제한의 경우:
- TIR (Target Interval Rate) = 100ms
- N = 10 (샘플 수)
- 429 임계값 = TIR × 0.98 × N = 980ms
```

### 2. PRG 트리거 조건
```
선제 체크: (기존 9개AIR + 잠정AIR) < 980ms
→ "429 위험" 감지 시 PRG 활성화
```

### 3. PRG 대기시간 계산
```
PRGWait = (N × TIR) - (기존AIR + 잠정AIR)
PRGWait = 1000ms - (기존 9개AIR + 잠정AIR)

예시: 1000ms - (280ms + 31ms) = 689ms
```

## 🔄 실행 흐름

### Phase 1: Cloudflare 대기시간 계산
```python
# Cloudflare Sliding Window 알고리즘
estimated_rate = previous_count × ratio + current_count
if estimated_rate + 1 > limit:
    RLWait = excess_requests × base_interval
```

### Phase 2: PRG 선제 분석
```python
# 잠정AIR 계산 (Cloudflare 대기시간 반영)
provisional_air = basic_interval + rl_wait

# PRG 트리거 체크
if (existing_9_air + provisional_air) < 980ms:
    PRGWait = 1000ms - (existing_9_air + provisional_air)
```

### Phase 3: 통합 대기시간 적용
```
TWait = RLWait + PRGWait
실제 대기: await asyncio.sleep(TWait)
```

## 📊 실제 동작 예시

### 요청 3 (10AIR 부족 상황)
```
기존 2개AIR: [31ms, 27ms] = 58ms
잠정AIR: 31ms
선제 체크: 58ms + 31ms = 89ms < 980ms ✅ 429위험
PRGWait: 1000ms - 89ms = 911ms
결과: TWait = 0ms + 911ms = 911ms
```

### 요청 13 (10AIR 안정화 후)
```
기존 9개AIR: 556.8ms
잠정AIR: 199.5ms (168ms RLWait 포함)
선제 체크: 556.8ms + 199.5ms = 756.3ms < 980ms ✅ 429위험
PRGWait: 1000ms - 756.3ms = 243.7ms
결과: TWait = 168ms + 243.7ms = 411.7ms
```

## ⚡ 핵심 장점

1. **Cloudflare 비간섭**: Cloudflare 윈도우 상태에 영향 없음
2. **선제적 방어**: 429 에러 발생 전 미리 차단
3. **정확한 예측**: RLWait를 포함한 잠정AIR로 정밀 계산
4. **동적 조정**: 샘플이 부족해도 최소 1개부터 동작

## 🔧 주요 파라미터

- **임계값 팩터**: 0.98 (98% 도달 시 위험 감지)
- **샘플 수**: ceil(RPS) (10 RPS = 10샘플)
- **최소 동작**: 1개 샘플부터 PRG 활성화
- **히스토리 크기**: 정확히 N개 유지

## 📈 성능 지표

현재 테스트 결과:
- **10AIR이 계속 증가하는 문제**: 슬라이딩 윈도우 미적용
- **샘플 부족 시 조기 동작**: 정상 동작 (1개부터 가능)
- **PRG 활성화**: 429 위험 구간에서 정확히 트리거됨

> **참고**: 10AIR가 1000ms 근처에서 안정화되어야 정상입니다. 현재 1463ms까지 증가하는 것은 슬라이딩 윈도우 로직이 개선되어야 함을 의미합니다.
