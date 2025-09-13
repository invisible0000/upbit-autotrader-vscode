# Upbit Rate Limiter v2.0

업비트 API 전용 통합 Rate Limiter - Zero-429 보장

## 핵심 기능

- **Zero-429 정책**: 429 에러 완전 차단
- **Lock-Free GCRA**: aiohttp 패턴 기반 고성능
- **동적 조정**: 429 발생 시 자동 rate 감소 + 점진적 복구
- **자가치유**: 백그라운드 태스크 장애 시 자동 재시작
- **타임아웃 보장**: 무한 대기 방지

## 파일 구조

- `upbit_rate_limiter.py` - 메인 클래스 (UnifiedUpbitRateLimiter)
- `upbit_rate_limiter_types.py` - 타입 정의 (Enum, DataClass)
- `upbit_rate_limiter_managers.py` - 보조 매니저들 (Self-Healing, Timeout, Atomic TAT)
- `upbit_rate_limiter_timing.py` - 정밀 타이밍 시스템
- `upbit_rate_limiter_monitoring.py` - 429 모니터링 및 통계
- `__init__.py` - 공개 API 노출

## 기본 사용법

```python
from .rate_limiter import UnifiedUpbitRateLimiter, get_unified_rate_limiter

# 인스턴스 생성
limiter = UnifiedUpbitRateLimiter()

# 전역 공유 인스턴스
global_limiter = await get_unified_rate_limiter()

# API 호출 전 게이트 통과
await limiter.gate(UpbitRateLimitGroup.PUBLIC_REST, "/v1/ticker")
```

## 레거시 호환성

기존 `UpbitGCRARateLimiter`와 완전 호환.
`get_global_rate_limiter()` → `get_unified_rate_limiter()` 자동 매핑.
