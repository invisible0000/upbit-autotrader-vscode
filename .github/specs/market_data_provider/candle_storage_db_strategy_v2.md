# 🎯 CandleStorage DB 전략 v2 - 현업 제안 반영

## 📋 **핵심 논의 결과**

### **현업 제안의 핵심**
> "OverlapAnalyzer로 API 최적화 → DB 기본 기능으로 중복 처리"

**논의 맥락**: OverlapAnalyzer는 API 호출 최적화를 위해 **필수**이고, 현업 제안은 OverlapAnalyzer가 최적화된 요청을 한 **후** DB 삽입 단계에서 중복 처리를 어떻게 할 것인가에 대한 것.

---

## 🔑 **선제 조건: 프라이머리 키 변경**

### **현재 스키마 문제점**
```sql
CREATE TABLE candles_KRW_BTC_1m (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- 문제: 비즈니스 의미 없음
    candle_date_time_utc TEXT NOT NULL,     -- 실제 중복 판단 기준
    ...
    UNIQUE(candle_date_time_utc)            -- 중복 제약은 있음
);
```

### **권장 스키마 변경**
```sql
CREATE TABLE candles_KRW_BTC_1m (
    candle_date_time_utc TEXT PRIMARY KEY,  -- 변경: 비즈니스 의미 있는 자연키
    id INTEGER UNIQUE,                      -- 변경: 기존 호환성을 위한 UNIQUE
    market TEXT NOT NULL,
    opening_price DECIMAL NOT NULL,
    high_price DECIMAL NOT NULL,
    low_price DECIMAL NOT NULL,
    trade_price DECIMAL NOT NULL,
    timestamp INTEGER NOT NULL,
    candle_acc_trade_price DECIMAL NOT NULL,
    candle_acc_trade_volume DECIMAL NOT NULL,
    unit INTEGER NOT NULL,
    trade_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 보조 인덱스
    UNIQUE(timestamp),
    INDEX(created_at)
);
```

### **프라이머리 키 선택 근거**

| 항목 | `candle_date_time_utc` | `timestamp` | `id` (현재) |
|------|------------------------|-------------|-------------|
| **비즈니스 의미** | ✅ 명확한 시간 표현 | ✅ 유닉스 타임스탬프 | ❌ 인위적 ID |
| **중복 탐지** | ✅ 완벽 | ✅ 완벽 | ❌ 불가능 |
| **업비트 API 호환** | ✅ 직접 매핑 | ✅ 직접 매핑 | ❌ 관련 없음 |
| **가독성** | ✅ 사람이 읽기 쉬움 | ❌ 숫자만 | ❌ 의미 없음 |
| **정렬** | ✅ 시간순 자연 정렬 | ✅ 시간순 정렬 | ❌ 삽입순 |

**최종 선택**: `candle_date_time_utc` (가독성 + 업비트 API 표준)

---

## 🏗️ **기존 코드 분석 결과**

### **현재 시스템의 DB 삽입 방식**
모든 기존 구현에서 **일관되게 `INSERT OR REPLACE` 사용**:

```python
# SqliteCandleRepository (현재 운영)
insert_sql = f"""
    INSERT OR REPLACE INTO {table_name}
    (market, candle_date_time_utc, candle_date_time_kst, ...)
    VALUES (?, ?, ?, ...)
"""

# BatchDBManager V4
query = """
INSERT OR REPLACE INTO candles (
    symbol, timeframe, timestamp, ...
) VALUES (?, ?, ?, ...)
"""
```

---

## 🎯 **현업 제안: INSERT OR IGNORE 방식**

### **INSERT OR REPLACE vs INSERT OR IGNORE**

| 구분 | INSERT OR REPLACE (기존) | INSERT OR IGNORE (권장) |
|------|--------------------------|-------------------------|
| **중복 발생시** | 기존 행 삭제 → 새로 삽입 | 중복 행 무시하고 건너뜀 |
| **ID 변화** | ❌ AUTO_INCREMENT 변경 | ✅ 기존 ID 보존 |
| **성능** | ❌ DELETE + INSERT 비용 | ✅ 단순 건너뛰기 |
| **트리거** | ❌ 2번 실행 (DELETE+INSERT) | ✅ 1번만 실행 |
| **업비트 데이터 특성** | ❌ 과도한 처리 | ✅ 과거 데이터 불변성 반영 |

### **업비트 데이터 특성에 맞는 이유**
- **과거 데이터 불변**: 업비트 서버의 과거 캔들 데이터는 변경되지 않음
- **중복은 무시**: 같은 시간 캔들이 다시 와도 기존 것 유지가 합리적
- **성능 우선**: UPDATE 불필요, 단순 IGNORE가 효율적

---

## 🚀 **권장 구현 전략**

### **OverlapAnalyzer + INSERT OR IGNORE 조합**
```python
class CandleStorage:
    """현업 제안: OverlapAnalyzer 후 INSERT OR IGNORE"""

    async def save_candles_optimized(self, market: str, timeframe: str,
                                   candles: List[dict]) -> int:
        """INSERT OR IGNORE 방식으로 안전한 삽입"""
        table_name = self._get_table_name(market, timeframe)

        insert_sql = f"""
            INSERT OR IGNORE INTO {table_name}
            (candle_date_time_utc, market, opening_price,
             high_price, low_price, trade_price, timestamp,
             candle_acc_trade_price, candle_acc_trade_volume,
             unit, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """

        candle_tuples = [
            (
                candle['candle_date_time_utc'],  # PK
                candle['market'],
                candle['opening_price'],
                candle['high_price'],
                candle['low_price'],
                candle['trade_price'],
                candle['timestamp'],
                candle['candle_acc_trade_price'],
                candle['candle_acc_trade_volume'],
                candle['unit']
            )
            for candle in candles
        ]

        try:
            with self.db_manager.get_connection("market_data") as conn:
                cursor = conn.executemany(insert_sql, candle_tuples)
                inserted_count = cursor.rowcount

                self.logger.info(f"캔들 저장 완료", extra={
                    "table": table_name,
                    "attempted": len(candles),
                    "inserted": inserted_count,  # 실제 삽입된 개수 (중복 제외)
                    "method": "INSERT_OR_IGNORE"
                })
                return inserted_count

        except Exception as e:
            self.logger.error(f"캔들 저장 실패: {e}")
            raise
```

### **완전한 워크플로우**
```python
async def get_candles_with_optimization(self, market: str, timeframe: str,
                                       count: int) -> List[dict]:
    """OverlapAnalyzer + INSERT OR IGNORE 완전 조합"""

    # 1. DB에서 기존 데이터 확인
    existing = await self._get_from_db(market, timeframe, count)

    if len(existing) >= count:
        return existing[:count]  # 충분한 데이터 있음

    # 2. OverlapAnalyzer로 API 호출 최적화 (50% 절감)
    missing_ranges = self.overlap_analyzer.analyze_gaps(existing, count)
    optimized_requests = self.overlap_analyzer.optimize_api_calls(missing_ranges)

    # 3. 최적화된 API 호출
    for request in optimized_requests:
        api_data = await self.api_client.get_candles(
            market, timeframe, count=request.count, to=request.to
        )

        # 4. INSERT OR IGNORE로 안전한 배치 삽입
        await self.storage.save_candles_optimized(market, timeframe, api_data)

    # 5. 최종 데이터 반환
    return await self._get_from_db(market, timeframe, count)
```

---

## 📊 **예상 효과**

### **성능 개선**
- **API 호출**: OverlapAnalyzer로 50% 절감
- **DB 삽입**: INSERT OR IGNORE로 20-30% 성능 향상
- **메모리**: 기존 데이터 보존으로 추가 처리 불필요

### **안정성 향상**
- **ID 일관성**: AUTO_INCREMENT ID 보존
- **데이터 무결성**: 기존 데이터 덮어쓰기 방지
- **트리거 안정성**: 단일 INSERT 이벤트만 발생

### **개발 효율성**
- **코드 단순화**: 복잡한 UPSERT 로직 불필요
- **디버깅 용이**: INSERT OR IGNORE 동작 예측 가능
- **SQLite 최적화**: DB 엔진 내장 기능 활용

---

## 🎯 **구현 우선순위**

### **Phase 1: 프라이머리 키 변경** (1일)
```sql
-- 스키마 마이그레이션
ALTER TABLE candles_KRW_BTC_1m ...
-- candle_date_time_utc를 PRIMARY KEY로 변경
```

### **Phase 2: INSERT OR IGNORE 적용** (1일)
```python
# 기존 INSERT OR REPLACE → INSERT OR IGNORE 변경
# 모든 관련 Repository 업데이트
```

### **Phase 3: 통합 테스트** (1일)
- OverlapAnalyzer + INSERT OR IGNORE 조합 검증
- 성능 벤치마크 및 안정성 테스트

**총 소요 시간**: 3일 (기존 7일 대비 대폭 단축)

---

## ✅ **최종 권장사항**

### **핵심 결정 사항**
1. **프라이머리 키**: `candle_date_time_utc` 변경 (선제 조건)
2. **중복 처리**: `INSERT OR IGNORE` 방식 채택
3. **API 최적화**: OverlapAnalyzer 유지 (필수)
4. **배치 처리**: executemany() 활용

### **성공 요소**
- ✅ **OverlapAnalyzer**: API 호출 50% 절감 유지
- ✅ **INSERT OR IGNORE**: 중복 자동 무시로 안전성 확보
- ✅ **자연키 PK**: 비즈니스 의미 있는 프라이머리 키
- ✅ **SQLite 최적화**: DB 엔진 내장 기능 최대 활용

### **기존 대비 장점**
- **개발 시간**: 7일 → 3일 (57% 단축)
- **코드 복잡도**: 단순화된 INSERT OR IGNORE
- **성능**: API 최적화 + DB 삽입 최적화
- **안정성**: 기존 데이터 보존 + 예측 가능한 동작

**🎯 결론**: 현업 제안의 "OverlapAnalyzer + INSERT OR IGNORE" 조합이 가장 실용적이고 효율적인 솔루션입니다.
