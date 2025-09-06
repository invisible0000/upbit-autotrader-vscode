# 📋 FastCache 기능 명세서 - 기존 코드 분석

## 🔍 **분석 대상 파일**
- **파일**: `upbit_auto_trading/infrastructure/market_data_backbone/smart_data_provider_V4/fast_cache.py`
- **크기**: 97줄
- **목적**: 단순하고 빠른 메모리 캐시 시스템 (200ms TTL 고정)

---

## 📊 **현재 구현된 기능**

### **1. 핵심 클래스: FastCache**
```python
class FastCache:
    """
    고속 메모리 캐시
    - 200ms 고정 TTL
    - 단순한 메모리 구조
    - 자동 만료 정리
    """
```

### **2. 초기화 및 설정**
```python
def __init__(self, default_ttl: float = 0.2):
    self._cache: Dict[str, Dict[str, Any]] = {}      # 데이터 저장소
    self._timestamps: Dict[str, float] = {}          # 타임스탬프 추적
    self._default_ttl = default_ttl                  # TTL 설정 (기본 200ms)
    self._hits = 0                                   # 캐시 히트 카운트
    self._misses = 0                                 # 캐시 미스 카운트
```

**특징:**
- ✅ **고정 TTL**: 200ms (0.2초) 기본값
- ✅ **단순 구조**: Dictionary 기반 메모리 저장
- ✅ **통계 추적**: 히트율 계산을 위한 카운터

---

## 🚀 **핵심 메서드 분석**

### **3. 데이터 조회: get()**
```python
def get(self, key: str) -> Optional[Dict[str, Any]]:
    """캐시에서 데이터 조회"""
    current_time = time.time()

    # 1. 키 존재 확인
    if key not in self._cache:
        self._misses += 1
        return None

    # 2. TTL 만료 확인
    if current_time - self._timestamps[key] > self._default_ttl:
        del self._cache[key]
        del self._timestamps[key]
        self._misses += 1
        return None

    # 3. 히트 성공
    self._hits += 1
    return self._cache[key]
```

**동작 방식:**
- ✅ **즉시 TTL 검증**: 조회 시점에서 만료 여부 확인
- ✅ **자동 정리**: 만료된 데이터는 즉시 삭제
- ✅ **통계 업데이트**: 히트/미스 카운터 자동 증가

### **4. 데이터 저장: set()**
```python
def set(self, key: str, data: Dict[str, Any]) -> None:
    """캐시에 데이터 저장"""
    self._cache[key] = data
    self._timestamps[key] = time.time()
```

**특징:**
- ✅ **단순 저장**: 복잡한 검증 없이 즉시 저장
- ✅ **타임스탬프 기록**: time.time() 기반 정확한 시간 추적
- ✅ **덮어쓰기**: 기존 키가 있으면 자동 갱신

### **5. 전체 정리: clear()**
```python
def clear(self) -> None:
    """캐시 전체 삭제"""
    self._cache.clear()
    self._timestamps.clear()
    logger.info("FastCache 전체 삭제")
```

### **6. 만료 데이터 정리: cleanup_expired()**
```python
def cleanup_expired(self) -> int:
    """만료된 데이터 정리"""
    current_time = time.time()
    expired_keys = []

    # 1. 만료된 키 수집
    for key, timestamp in self._timestamps.items():
        if current_time - timestamp > self._default_ttl:
            expired_keys.append(key)

    # 2. 일괄 삭제
    for key in expired_keys:
        del self._cache[key]
        del self._timestamps[key]

    return len(expired_keys)  # 정리된 개수 반환
```

**활용:**
- ✅ **배치 정리**: 수동 호출로 만료 데이터 일괄 정리
- ✅ **메모리 최적화**: 메모리 사용량 관리 목적
- ✅ **정리 통계**: 정리된 항목 수 반환

### **7. 통계 조회: get_stats()**
```python
def get_stats(self) -> Dict[str, Any]:
    """캐시 통계 반환"""
    total_requests = self._hits + self._misses
    hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

    return {
        'total_keys': len(self._cache),      # 현재 캐시된 키 개수
        'hits': self._hits,                  # 총 히트 수
        'misses': self._misses,              # 총 미스 수
        'hit_rate': round(hit_rate, 2),      # 히트율 (%)
        'ttl': self._default_ttl             # 설정된 TTL
    }
```

---

## 📈 **성능 특성**

### **장점**
- ✅ **극고속**: Dictionary 기반 O(1) 조회
- ✅ **메모리 효율**: 단순 구조로 오버헤드 최소
- ✅ **즉시 만료**: get() 시점에서 TTL 확인으로 즉시 정리
- ✅ **스레드 안전성**: 단순 구조로 경합 상황 최소화

### **제한사항**
- ❌ **고정 TTL**: 동적 TTL 변경 불가 (200ms 고정)
- ❌ **크기 제한 없음**: 메모리 무제한 증가 가능성
- ❌ **LRU 없음**: 오래된 데이터 자동 제거 없음
- ❌ **백그라운드 정리 없음**: 수동 cleanup_expired() 호출 필요

---

## 🎯 **사용 패턴**

### **전형적인 사용 시나리오**
```python
# 1. 캐시 초기화
cache = FastCache(default_ttl=0.2)  # 200ms TTL

# 2. 데이터 저장
cache.set("KRW-BTC-1m", candle_data)

# 3. 데이터 조회 (TTL 자동 확인)
cached_data = cache.get("KRW-BTC-1m")
if cached_data is None:
    # 캐시 미스 또는 만료
    fresh_data = api_call()
    cache.set("KRW-BTC-1m", fresh_data)

# 4. 주기적 정리 (선택사항)
cleaned_count = cache.cleanup_expired()

# 5. 통계 확인
stats = cache.get_stats()
print(f"히트율: {stats['hit_rate']}%")
```

---

## ⚙️ **설계 철학**

### **V4.0의 단순성 우선 접근**
- **복잡한 캐시 관리 제거**: LRU, 동적 TTL 등 고급 기능 배제
- **200ms 고정 TTL**: 중복 요청 차단에 최적화된 초단기 캐시
- **성능 최우선**: 복잡도보다 응답 속도 중시
- **예측 가능성**: 단순한 동작으로 디버깅 용이

### **적용 영역**
- **API 중복 요청 방지**: 동일 요청 200ms 내 재호출 차단
- **고빈도 조회 최적화**: 짧은 시간 내 반복 조회 성능 향상
- **메모리 기반 임시 저장**: 영구 저장이 불필요한 데이터

---

## 🔧 **기존 코드의 장점**

1. **검증된 안정성**: V4.0에서 실제 운영 중인 코드
2. **명확한 책임**: 캐시 기능만 담당하는 단일 책임
3. **Infrastructure 로깅**: create_component_logger 표준 준수
4. **타입 힌트**: 완전한 타입 안정성 확보
5. **통계 지원**: 성능 모니터링을 위한 히트율 추적

**🎯 결론**: 이 FastCache 구현은 단순함과 성능을 완벽히 균형 맞춘 실용적인 캐시 시스템입니다. 200ms TTL로 API 중복 요청을 효과적으로 차단하면서도 복잡도를 최소화했습니다.
