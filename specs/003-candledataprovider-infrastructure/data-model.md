# Data Model Design: OverlapAnalyzer v5.0 Infrastructure 레이어 모델

**설계 목표**: 업비트 AP            unit=int(data['unit']) if 'unit' in data else None,  # 분봉만
            prev_closing_price=float(data['prev_closing_price']) if 'prev_closing_price' in data else None,  # 일봉만
            first_day_of_period=str(data['first_day_of_period']) if 'first_day_of_period' in data else None  # 주/월/연봉만완전 호환 + OverlapAnalyzer v5.0 100% 호환성
**아키텍처**: DDD Infrastructure Layer, frozen dataclass 불변성

## 핵심 엔티티 모델

### 1. UpbitCandleModel - 업비트 API 완전 호환 모델

```python
@dataclass(frozen=True)
class UpbitCandleModel:
    """업비트 REST API 캔들 응답과 1:1 매핑되는 불변 모델

    모든 타임프레임 지원:
    - 초봉 (1s): 공통 필드만
    - 분봉 (1m, 3m, 5m, 15m, 30m, 60m, 240m): unit 필드 추가
    - 일봉 (1d): prev_closing_price 필드 추가
    - 주봉/월봉/연봉 (1w, 1M, 1y): first_day_of_period 필드 추가

    DB 저장 필드 (공통 9개 + created_at만):
    - 공통 필드 9개는 모든 타임프레임에서 DB 저장
    - unit, prev_closing_price, first_day_of_period는 DB 저장하지 않음 (API 응답에서만 사용)
    - created_at은 DB 저장 시 자동 추가
    """

    # === 공통 필드 (모든 타임프레임) ===
    market: str                    # "KRW-BTC"
    candle_date_time_utc: str     # "2025-06-30T00:00:00"
    candle_date_time_kst: str     # "2025-06-30T09:00:00"
    opening_price: float          # 시가 (double)
    high_price: float             # 고가 (double)
    low_price: float              # 저가 (double)
    trade_price: float            # 종가/현재가 (double)
    timestamp: int                # 마지막 틱 타임스탬프 (int64, ms)
    candle_acc_trade_price: float # 누적 거래금액 (double)
    candle_acc_trade_volume: float # 누적 거래량 (double)

    # === 타임프레임별 선택적 필드 ===
    unit: Optional[int] = None            # 분봉 단위 (1, 3, 5, 15, 30, 60, 240)
    prev_closing_price: Optional[float] = None  # 전일 종가 (일봉만)
    first_day_of_period: Optional[str] = None   # 집계 시작일 (주/월/연봉만)

    def __post_init__(self):
        """생성 시 데이터 무결성 검증"""
        # OHLC 관계 검증
        if not (self.low_price <= min(self.opening_price, self.trade_price) and
                self.high_price >= max(self.opening_price, self.trade_price)):
            raise ValueError(f"Invalid OHLC relationship: O{self.opening_price} H{self.high_price} L{self.low_price} C{self.trade_price}")

        # 가격 양수 검증
        prices = [self.opening_price, self.high_price, self.low_price, self.trade_price]
        if any(p <= 0 for p in prices):
            raise ValueError(f"All prices must be positive: {prices}")

        # 거래량/거래금액 비음수 검증
        if self.candle_acc_trade_volume < 0 or self.candle_acc_trade_price < 0:
            raise ValueError(f"Trade volume/price must be non-negative: {self.candle_acc_trade_volume}, {self.candle_acc_trade_price}")

    @classmethod
    def from_upbit_response(cls, data: Dict[str, Any]) -> 'UpbitCandleModel':
        """업비트 API 응답에서 모델 생성

        Args:
            data: 업비트 API JSON 응답 (dict)

        Returns:
            UpbitCandleModel: 타입 안전한 캔들 모델

        Raises:
            ValueError: 필수 필드 누락 또는 타입 변환 실패
        """
        try:
            return cls(
                market=str(data['market']),
                candle_date_time_utc=str(data['candle_date_time_utc']),
                candle_date_time_kst=str(data['candle_date_time_kst']),
                opening_price=float(data['opening_price']),
                high_price=float(data['high_price']),
                low_price=float(data['low_price']),
                trade_price=float(data['trade_price']),
                timestamp=int(data['timestamp']),
                candle_acc_trade_price=float(data['candle_acc_trade_price']),
                candle_acc_trade_volume=float(data['candle_acc_trade_volume']),
                unit=int(data['unit']) if 'unit' in data else None,  # 분봉만 (DB 저장 안 함)
                prev_closing_price=float(data['prev_closing_price']) if 'prev_closing_price' in data else None,  # 일봉만 (DB 저장 안 함)
                first_day_of_period=str(data['first_day_of_period']) if 'first_day_of_period' in data else None  # 주/월/연봉만 (DB 저장 안 함)
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Failed to create UpbitCandleModel from API response: {e}")

    def to_repository_format(self) -> Dict[str, Any]:
        """SqliteCandleRepository 호환 형식으로 변환 (OverlapAnalyzer v5.0 호환성)

        Note: 공통 필드 9개만 반환 (타임프레임별 선택적 필드는 DB 저장하지 않음)

        Returns:
            Dict: 기존 Repository 인터페이스와 호환되는 형식 (공통 필드만)
        """
        return {
            'market': self.market,
            'candle_time': self.candle_date_time_utc,
            'opening_price': self.opening_price,
            'high_price': self.high_price,
            'low_price': self.low_price,
            'trade_price': self.trade_price,
            'timestamp': self.timestamp,
            'candle_acc_trade_price': self.candle_acc_trade_price,
            'candle_acc_trade_volume': self.candle_acc_trade_volume
        }

    def to_db_format(self) -> Dict[str, Any]:
        """DB 저장용 형식으로 변환 (공통 필드 9개 + created_at만 저장)

        Notes:
            - 타임프레임별 선택적 필드(unit, prev_closing_price, first_day_of_period)는 DB에 저장하지 않음
            - 오직 모든 타임프레임에 공통으로 존재하는 9개 필드만 저장

        Returns:
            Dict: DB 테이블 스키마와 매칭되는 형식 (공통 필드 + created_at)
        """
        result = self.to_repository_format()
        result['created_at'] = datetime.utcnow().isoformat()  # DB 저장 시각 추가
        return result

    @property
    def change_price(self) -> Optional[float]:
        """가격 변화량 계산 (trade_price - prev_closing_price) - 일봉만 해당"""
        if self.prev_closing_price is None:
            return None
        return self.trade_price - self.prev_closing_price

    @property
    def change_rate(self) -> Optional[float]:
        """가격 변화율 계산 ((trade_price - prev_closing_price) / prev_closing_price) - 일봉만 해당"""
        if self.prev_closing_price is None or self.prev_closing_price == 0:
            return None
        return (self.trade_price - self.prev_closing_price) / self.prev_closing_price
```

```python
@dataclass(frozen=True)
class TimeChunk:
    start_time: datetime     # 청크 시작 시간
    end_time: datetime       # 청크 종료 시간
    expected_count: int      # 예상 캔들 개수
    chunk_index: int         # 청크 순서 (0부터)
```

**검증 규칙**:
- start_time < end_time
- expected_count > 0, <= 200
- chunk_index >= 0

### 3. CandleDataResponse (응답 모델)
**목적**: 서브시스템 응답 표준화

**필드 구조**:
```python
@dataclass(frozen=True)
class CandleDataResponse:
    success: bool
    candles: List[CandleData]
    total_count: int
    data_source: str              # "cache", "db", "api", "mixed"
    response_time_ms: float
    error_message: Optional[str] = None
```

**검증 규칙**:
- success=True → candles 존재, error_message=None
- success=False → error_message 존재
- total_count == len(candles)

### 4. OverlapStatus (상태 열거형)
**목적**: 겹침 분석 결과 상태 (OverlapAnalyzer v5.0 정확한 5개 분류)

**값**:
- NO_OVERLAP: 겹침 없음 → 전체 API 요청 필요
- COMPLETE_OVERLAP: 완전 겹침 → DB만 사용
- PARTIAL_START: 시작 부분 겹침 → 일부 DB + 일부 API
- PARTIAL_MIDDLE_FRAGMENT: 중간 겹침 (파편) → 복잡한 분할 처리
- PARTIAL_MIDDLE_CONTINUOUS: 중간 겹침 (말단) → 연속 데이터 활용

### 5. DataRange (기존 데이터 범위)
**목적**: OverlapAnalyzer 연동용 데이터 범위 정보

**필드 구조**:
```python
@dataclass(frozen=True)
class DataRange:
    start_time: datetime
    end_time: datetime
    candle_count: int
    is_continuous: bool
```

### 6. CacheKey/CacheEntry (캐시 모델)
**목적**: 메모리 캐시 시스템 지원

**CacheKey**:
```python
@dataclass(frozen=True)
class CacheKey:
    symbol: str
    timeframe: str
    start_time: datetime
    count: int
```

**CacheEntry**:
```python
@dataclass(frozen=True)
class CacheEntry:
    key: CacheKey
    candles: List[CandleData]
    created_at: datetime
    ttl_seconds: int
    data_size_bytes: int
```

## 데이터 흐름

### 1. API 응답 → CandleData 변환
```
업비트 API JSON → CandleData.from_upbit_api() → CandleData 객체
```

### 2. DB 저장/조회
```
CandleData → to_db_dict() → SQLite 저장
SQLite 조회 → from_db_row() → CandleData 객체
```

### 3. 청크 처리
```
대량 요청 → TimeUtils.calculate_chunk_boundaries() → List[TimeChunk]
각 TimeChunk → CandleData 수집 → CollectionResult
```

### 4. 응답 생성
```
List[CandleData] → CandleDataResponse → 상위 레이어 반환
```

## 성능 고려사항

### 메모리 최적화
- `@dataclass(frozen=True)`: 불변성 + 해시 가능
- `__slots__` 고려: 메모리 사용량 20% 절약
- Optional 필드: 사용하지 않는 타임프레임에서 메모리 절약

### 처리 속도 최적화
- 팩토리 메서드: 객체 생성 최적화
- 지연 평가: 필요시에만 복잡한 계산 수행
- 배치 처리: 200개 단위 효율적 처리

## 확장성 설계

### 새로운 타임프레임 지원
- 기존 공통 필드 유지
- 새로운 Optional 필드 추가
- 기존 코드 영향 없음

### 새로운 거래소 지원
- CandleData 기본 구조 유지
- 거래소별 어댑터 패턴 적용
- 공통 인터페이스 보장

### 캐시 확장
- CacheKey 기반 유연한 캐시 전략
- TTL, 크기 제한 등 정책 분리
- 메모리/디스크 캐시 선택 가능
