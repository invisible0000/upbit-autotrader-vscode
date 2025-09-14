# GCRA Burst 의미론 심화 분석

## 🎯 요약
현재 RPM burst 구현이 표준 GCRA와 다른 방식(Fixed Window)으로 작동함을 확인.
표준 GCRA는 연속적 τ(tolerance) 기반이며, 더 부드럽고 안전한 rate limiting 제공.

## 📚 권위 소스 분석

### 1. Wikipedia GCRA 정의
- **TAT 기반**: `ta > TAT - τ` 조건으로 conforming 판단
- **τ 의미**: "얼마나 일찍 도착할 수 있는지"의 시간적 여유
- **Dual Leaky Bucket**: 여러 rate limit 동시 적용 가능

### 2. aiolimiter 구현 (Python)
```python
limiter = AsyncLimiter(4, 8)  # 8초 동안 4개, 초기 4개 burst
# 초기에 4개 연속 처리 가능, 이후 2초마다 1개씩 refill
```

### 3. RFC 2697 Token Bucket
- **CBS/EBS**: 초기 token bucket이 가득 찬 상태
- **연속적 refill**: CIR times per second로 지속 충전
- **Burst 처리**: 초기 크레딧 소모 후 정상 속도 유지

## 🔍 현재 구현 분석

### RPM Burst 로직 (upbit_rate_limiter_managers.py)
```python
# 문제: Fixed Window with Reset
if now_minute != self.last_rpm_burst_minute:
    self.rpm_burst_used = 0  # 매분 0초에 리셋
    self.last_rpm_burst_minute = now_minute

if self.rpm_burst_used < self.config.requests_per_minute_burst:
    self.rpm_burst_used += 1
    return True  # N개 "무료 패스"
```

**특징**:
- 매분 정각에 burst 카운터 리셋
- 분 초반에 burst 한도만큼 연속 사용 가능
- 나머지 시간은 일반 RPM 제한 적용

## ⚖️ 비교 분석

| 구분 | 현재 방식 (Fixed Window) | 표준 GCRA (τ 기반) |
|------|-------------------------|-------------------|
| **리셋 시점** | 매분 0초 | 연속적 (리셋 없음) |
| **Burst 허용** | 분당 N개 무조건 | τ 시간만큼 앞당겨 사용 |
| **Traffic Pattern** | Spiky (분 초반 집중) | Smooth (평균적 분산) |
| **Abuse 저항성** | 취약 (분 초반 몰아서) | 강함 (평균 속도 유지) |
| **알고리즘 일관성** | RPS와 다른 방식 | RPS와 동일한 GCRA |

## 🚨 실제 Upbit 정책 추정

**"분당 100회" 해석**:
1. **Fixed Window** (현재 구현): 매분 0-59초 구간에서 100회
2. **Sliding Window**: 지난 60초 동안 100회
3. **GCRA**: 평균 1.67req/sec + τ tolerance

**일반적 API 서비스**: Sliding Window 또는 GCRA 사용 (Fixed Window는 abuse 취약)

## 📋 개선 방안

### Option 1: 표준 GCRA 적용 (이론적 최선)

```python
# config에 τ 값 추가
tau_minute = burst_rpm * (60 / rpm)  # burst_size * interval

# 표준 GCRA 로직
def _consume_dual_token_atomic(self, group: str, now: float) -> bool:
    # RPS 체크
    interval_seconds = 1.0 / self.config.requests_per_second
    tau_seconds = self.config.requests_per_second_burst * interval_seconds

    if now > self.group_tats[group].tat - tau_seconds:
        self.group_tats[group].tat = max(now, self.group_tats[group].tat) + interval_seconds
        rps_ok = True

    # RPM 체크 (동일한 GCRA 방식)
    interval_minute = 60.0 / self.config.requests_per_minute
    tau_minute = self.config.requests_per_minute_burst * interval_minute

    if now > self.group_tats_minute[group].tat - tau_minute:
        self.group_tats_minute[group].tat = max(now, self.group_tats_minute[group].tat) + interval_minute
        rpm_ok = True

    return rps_ok and rpm_ok
```

### Option 2: 설정 옵션 제공
```python
class RateLimitConfig:
    burst_mode: Literal["fixed_window", "gcra_tau"] = "fixed_window"
    # 기존 시스템 호환성 유지하면서 선택 가능
```

### Option 3: 점진적 전환
1. 테스트 환경에서 두 방식 모두 구현
2. Upbit 실제 API로 검증 테스트
3. 결과 비교 후 최적 방식 선택

## 🎯 권고사항

**단기 (현재)**:
- 현재 구현 유지 (안정성 우선)
- 이 문서로 차이점 명확히 인식
- 모니터링으로 실제 429 에러 패턴 관찰

**중기 (검증 후)**:
- 테스트 환경에서 표준 GCRA 구현
- 두 방식으로 실제 Upbit API 테스트
- Performance와 429 에러 빈도 비교

**장기 (안정화 후)**:
- 검증된 방식을 기본값으로 설정
- 알고리즘 일관성 확보 (RPS와 RPM 동일 방식)
- 네트워크 표준 준수

## 📈 기대 효과

**표준 GCRA 적용 시**:
- ✅ 더 부드러운 traffic shaping
- ✅ Abuse 저항성 향상
- ✅ 네트워크 표준 준수
- ✅ 알고리즘 일관성 확보
- ⚠️ 기존 동작과 차이 (검증 필요)

## 🔗 참고 자료

- [Wikipedia: Generic Cell Rate Algorithm](https://en.wikipedia.org/wiki/Generic_cell_rate_algorithm)
- [aiolimiter: Python Async Rate Limiter](https://github.com/mjpieters/aiolimiter)
- [RFC 2697: Single Rate Three Color Marker](https://tools.ietf.org/rfc/rfc2697.txt)
- [Upstash Ratelimit: Token Bucket Implementation](https://github.com/upstash/ratelimit-py)

---
**작성일**: 2025-01-28
**분석자**: GitHub Copilot + 권위 소스 종합 분석
**다음 액션**: 테스트 환경에서 두 방식 비교 검증
