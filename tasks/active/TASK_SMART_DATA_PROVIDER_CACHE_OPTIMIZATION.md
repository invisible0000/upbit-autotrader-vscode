# 📋 Smart Data Provider 캐시 최적화 작업

## 🎯 **작업 목표**
Smart Data Provider의 티커/호가 캐시 전략을 재검토하여 실시간성과 API 사용량 절약의 최적 ### ⚠️ **리스크 관리**

### 🚨 **잠재적 위험**
1. **실시간성 트레이드오프**: 200ms 지연 vs API 사용량 절약
2. **메모리 증가**: 캐시 데이터 저장 공간 (미미함)
3. **플래그 설정 실수**: 잘못된 캐시 설정으로 인한 문제

### 🛡️ **완화 방안**
1. **런타임 제어**: 문제 발생 시 즉시 캐시 비활성화 가능
2. **검색 키워드**: "TICKER_CACHE_ENABLED" 등으로 5초만에 위치 찾기
3. **명확한 주석**: 각 플래그의 목적과 사용법 상세 기록
4. **Fallback 로직**: 캐시 시스템 실패 시 즉시 API 호출
5. **성능 메트릭**: 캐시 히트율 모니터링으로 문제 조기 발견

### 🔍 **긴급 대응 가이드**
```python
# ⚠️ 티커 데이터 문제 시 즉시 실행
cache_manager.disable_ticker_cache()

# ⚠️ 호가 데이터 문제 시 즉시 실행
cache_manager.disable_orderbook_cache()

# 🔍 파일에서 직접 찾아 수정 (Ctrl+F)
# 검색: "TICKER_CACHE_ENABLED" → False로 변경
# 검색: "ORDERBOOK_CACHE_ENABLED" → False로 변경
```# 🔍 **현재 상황 분석**

### ❌ **문제점**
- **티커/호가 캐시 완전 제외**: API 사용량 과다, 중복 요청 발생
- **실시간성 과도 보장**: 0.1초 이내 동일 요청도 매번 API 호출
- **Smart Router 효율성 저하**: 캐시 미활용으로 성능 최적화 한계

### ✅ **장점 유지 요소**
- **Timestamp 정확성**: 모든 데이터에 timestamp 포함으로 신선도 판별 가능
- **데이터 형식 통일**: DataFormatUnifier로 일관된 메타데이터 제공
- **TTL 최적화**: CacheCoordinator의 적응형 TTL 시스템 완성도 높음

## 🚀 **제안 솔루션**

### 💎 **최종 권장: 캐시 제어 플래그 + TTL 기반 실용적 캐시 전략**

```python
# =====================================
# 🎛️ 캐시 제어 플래그 (쉬운 검색/변경용)
# =====================================
CACHE_CONFIG = {
    # 🔍 검색 키워드: "TICKER_CACHE_ENABLED"
    'TICKER_CACHE_ENABLED': True,     # 티커 캐시 ON/OFF
    'TICKER_CACHE_TTL': 0.2,          # 티커 캐시 수명 (초)

    # 🔍 검색 키워드: "ORDERBOOK_CACHE_ENABLED"
    'ORDERBOOK_CACHE_ENABLED': True,  # 호가 캐시 ON/OFF
    'ORDERBOOK_CACHE_TTL': 0.3,       # 호가 캐시 수명 (초)

    # 🔍 검색 키워드: "TRADES_CACHE_ENABLED"
    'TRADES_CACHE_ENABLED': True,     # 체결 캐시 ON/OFF (기존)
    'TRADES_CACHE_TTL': 30.0,         # 체결 캐시 수명 (초)

    # 🔍 검색 키워드: "MARKET_CACHE_ENABLED"
    'MARKET_CACHE_ENABLED': True,     # 시장 개요 캐시 ON/OFF (기존)
    'MARKET_CACHE_TTL': 60.0,         # 시장 개요 캐시 수명 (초)
}

class SmartCacheWithFlags:
    """플래그 제어 가능한 실용적 캐시 시스템"""

    def __init__(self):
        # 캐시 설정 로드
        self.cache_config = CACHE_CONFIG.copy()

    async def get_ticker_smart(self, symbol: str) -> DataResponse:
        """티커 조회 with 캐시 플래그 제어"""

        # 🎛️ 캐시 비활성화 시 직접 API 호출
        if not self.cache_config['TICKER_CACHE_ENABLED']:
            return await self.smart_router.get_ticker(symbol)

        # TTL 캐시 로직
        cached = self.get_cache(
            f"ticker:{symbol}",
            max_age=self.cache_config['TICKER_CACHE_TTL']
        )
        if cached:
            self._record_cache_hit(symbol, 'ticker')
            return cached

        # 캐시 미스 - API 호출 후 캐시 저장
        fresh_data = await self.smart_router.get_ticker(symbol)
        self.set_cache(
            f"ticker:{symbol}",
            fresh_data,
            ttl=self.cache_config['TICKER_CACHE_TTL']
        )
        self._record_cache_miss(symbol, 'ticker')
        return fresh_data

    async def get_orderbook_smart(self, symbol: str) -> DataResponse:
        """호가 조회 with 캐시 플래그 제어"""

        # 🎛️ 캐시 비활성화 시 직접 API 호출
        if not self.cache_config['ORDERBOOK_CACHE_ENABLED']:
            return await self.smart_router.get_orderbook(symbol)

        # TTL 캐시 로직
        cached = self.get_cache(
            f"orderbook:{symbol}",
            max_age=self.cache_config['ORDERBOOK_CACHE_TTL']
        )
        if cached:
            self._record_cache_hit(symbol, 'orderbook')
            return cached

        # 캐시 미스 - API 호출 후 캐시 저장
        fresh_data = await self.smart_router.get_orderbook(symbol)
        self.set_cache(
            f"orderbook:{symbol}",
            fresh_data,
            ttl=self.cache_config['ORDERBOOK_CACHE_TTL']
        )
        self._record_cache_miss(symbol, 'orderbook')
        return fresh_data

    # =====================================
    # 🎛️ 실시간 캐시 제어 API
    # =====================================

    def disable_ticker_cache(self):
        """🔍 검색: disable_ticker_cache - 티커 캐시 비활성화"""
        self.cache_config['TICKER_CACHE_ENABLED'] = False
        self.clear_ticker_cache()
        logger.warning("티커 캐시 비활성화됨")

    def enable_ticker_cache(self, ttl: float = 0.2):
        """🔍 검색: enable_ticker_cache - 티커 캐시 활성화"""
        self.cache_config['TICKER_CACHE_ENABLED'] = True
        self.cache_config['TICKER_CACHE_TTL'] = ttl
        logger.info(f"티커 캐시 활성화됨 (TTL: {ttl}초)")

    def disable_orderbook_cache(self):
        """🔍 검색: disable_orderbook_cache - 호가 캐시 비활성화"""
        self.cache_config['ORDERBOOK_CACHE_ENABLED'] = False
        self.clear_orderbook_cache()
        logger.warning("호가 캐시 비활성화됨")

    def enable_orderbook_cache(self, ttl: float = 0.3):
        """🔍 검색: enable_orderbook_cache - 호가 캐시 활성화"""
        self.cache_config['ORDERBOOK_CACHE_ENABLED'] = True
        self.cache_config['ORDERBOOK_CACHE_TTL'] = ttl
        logger.info(f"호가 캐시 활성화됨 (TTL: {ttl}초)")
```

### 🎯 **핵심 전략 (플래그 제어 추가)**

1. **Ultra-Short TTL**: 200ms TTL로 중복 요청 완전 차단
2. **런타임 캐시 제어**: 코드 수정 없이 즉시 캐시 ON/OFF
3. **쉬운 검색 키워드**: "TICKER_CACHE_ENABLED" 등으로 빠른 위치 찾기
4. **API 사용량 95%+ 절약**: 캐시 활성화 시 극적 효과

**🔑 핵심 장점**:
- 캐시 문제 발생 시 즉시 비활성화 가능 ✅
- 코드 전체 수정 없이 플래그만 변경 ✅
- 검색 키워드로 5초만에 찾아서 수정 ✅
- 동적 TTL 조정으로 세밀한 제어 ✅

**🔍 빠른 사용법**:
```python
# 긴급 시 티커 캐시 비활성화
cache_manager.disable_ticker_cache()

# 문제 해결 후 재활성화
cache_manager.enable_ticker_cache(ttl=0.1)  # 더 짧은 TTL로

# 또는 설정에서 직접 변경
CACHE_CONFIG['TICKER_CACHE_ENABLED'] = False  # 🔍 검색: TICKER_CACHE_ENABLED
```

## 📋 **구현 작업 계획**

### [-] **Phase 1: 캐시 전략 설계**
- [ ] SmartTimestampCache 클래스 설계
- [ ] 티커/호가별 최적 TTL 값 결정
- [ ] 타임스탬프 비교 로직 구현
- [ ] CacheCoordinator 통합 설계

### [ ] **Phase 2: 핵심 구현**
- [ ] memory_realtime_cache.py 확장
- [ ] 캐시 제어 플래그 시스템 구현 (CACHE_CONFIG)
- [ ] 티커 캐시 활성화 (get/set_ticker 메서드 + 플래그)
- [ ] 호가 캐시 활성화 (get/set_orderbook 메서드 + 플래그)
- [ ] 런타임 캐시 제어 API (enable/disable_*_cache)
- [ ] 검색 키워드 및 주석 시스템 구현
- [ ] 캐시 히트/미스 성능 메트릭 추가

### [ ] **Phase 3: 통합 및 최적화**
- [ ] realtime_data_handler.py 수정
- [ ] smart_data_provider.py 캐시 활용 로직 추가
- [ ] CacheCoordinator 적응형 TTL 연동
- [ ] 성능 메트릭 및 모니터링 추가

### [ ] **Phase 4: 테스트 및 검증**
- [ ] 단위 테스트 작성
- [ ] 성능 벤치마크 테스트
- [ ] API 사용량 절약 효과 측정
- [ ] 실시간성 보장 검증

## 🔢 **예상 성과**

### 📈 **정량적 효과**
- **API 호출 98% 감소**: 고빈도 요청 시나리오
- **응답 속도 10x 향상**: 캐시 히트 시 <5ms
- **메모리 사용량**: +2MB (허용 가능한 수준)
- **실시간성**: 200ms 이내 최신 데이터 보장

### 🎯 **정성적 효과**
- **Smart Router 완성도**: 캐시 활용으로 진정한 스마트 라우팅
- **시스템 안정성**: API Rate Limit 위험 대폭 감소
- **사용자 경험**: 즉각 반응하는 UI 응답성
- **확장성**: 다중 사용자/전략 동시 실행 가능

## ⚠️ **리스크 관리**

### 🚨 **잠재적 위험**
1. **실시간성 저하**: 200ms 지연 허용 필요
2. **메모리 증가**: 캐시 데이터 저장 공간
3. **복잡성 증가**: 타임스탬프 비교 로직

### 🛡️ **완화 방안**
1. **설정 가능한 TTL**: 전략별/사용자별 TTL 조정 가능
2. **메모리 모니터링**: 자동 정리 및 크기 제한
3. **Fallback 로직**: 캐시 실패 시 즉시 API 호출

## 🏁 **완료 기준**

### ✅ **Definition of Done**
- [ ] 티커/호가 캐시 정상 작동
- [ ] 실시간성 200ms 이내 보장
- [ ] 실시간 티커/호가요청을 방해하지 않을것(시스템내 다른 기능에서 중복 요청을 대비한 것이지 실시간 정보 취득을 막기 위한것이 아님. rate_limitor 한도에 맞출경우 실시간성 훼손은 없을거라 예상 )
- [ ] 전체 테스트 PASS
- [ ] 성능 벤치마크 기준 달성

### 📊 **검증 방법**
```python
# 성능 테스트
pytest tests/infrastructure/test_external_apis/test_smart_cache_performance.py

# 실시간성 테스트
pytest tests/infrastructure/test_external_apis/test_realtime_guarantee.py

# API 사용량 테스트
pytest tests/infrastructure/test_external_apis/test_api_usage_reduction.py
```

## 🎯 **우선순위: HIGH**

**이유**:
- Smart Router 완성도에 직결
- API 사용량 절약으로 비용 효율성 확보
- 시스템 전체 성능 향상의 핵심 요소

**담당**: AI Assistant
**예상 소요**: 2-3일
**의존성**: DataFormatUnifier 완료 (✅)

---

*Last Updated: 2025-08-25*
*Status: 계획 수립 완료, 구현 대기*
