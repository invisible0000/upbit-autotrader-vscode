# OverlapAnalyzer v5.0 호환성 계약

**목적**: OverlapAnalyzer v5.0과 Infrastructure 모델 간의 완전 호환성 보장
**중요도**: CRITICAL - 기존 코드 변경 없이 100% 호환되어야 함

## 인터페이스 계약

### 1. OverlapRequest 호환성
```python
# 기존 OverlapRequest 인터페이스 (변경 금지)
@dataclass(frozen=True)
class OverlapRequest:
    symbol: str                    # 거래 심볼 (예: 'KRW-BTC')
    timeframe: str                 # 타임프레임 ('1m', '5m', '15m', etc.)
    target_start: datetime         # 요청 시작 시간
    target_end: datetime           # 요청 종료 시간
    target_count: int              # 요청 캔들 개수 (1~200)
```

**CONTRACT**: Infrastructure 모델은 이 인터페이스를 있는 그대로 수용해야 함

### 2. OverlapResult 호환성
```python
# 기존 OverlapResult 인터페이스 (변경 금지)
@dataclass(frozen=True)
class OverlapResult:
    status: OverlapStatus          # 겹침 상태 (5가지)
    api_start: Optional[datetime] = None  # API 요청 시작점
    partial_start: Optional[datetime] = None  # 데이터 시작점 (중간 겹침용)
```

**CONTRACT**: Infrastructure 모델의 응답은 이 형식으로 변환 가능해야 함

### 3. OverlapStatus 열거형 (변경 금지)
```python
class OverlapStatus(Enum):
    NO_OVERLAP = "no_overlap"                        # 1. 겹침 없음
    COMPLETE_OVERLAP = "complete_overlap"            # 2.1. 완전 겹침
    PARTIAL_START = "partial_start"                  # 2.2.1. 시작 겹침
    PARTIAL_MIDDLE_FRAGMENT = "partial_middle_fragment"    # 2.2.2.1. 중간 겹침 (파편)
    PARTIAL_MIDDLE_CONTINUOUS = "partial_middle_continuous"  # 2.2.2.2. 중간 겹침 (말단)
```

**CONTRACT**: 5가지 상태 분류 로직은 OverlapAnalyzer에 그대로 유지됨

## Repository 인터페이스 계약

### 4. CandleRepositoryInterface 메서드 호환성
```python
# 기존 메서드들 (시그니처 변경 금지)
async def has_any_data_in_range(self, symbol: str, timeframe: str,
                               start_time: datetime, end_time: datetime) -> bool

async def is_range_complete(self, symbol: str, timeframe: str,
                           start_time: datetime, end_time: datetime,
                           expected_count: int) -> bool

async def find_last_continuous_time(self, symbol: str, timeframe: str,
                                   target_start: datetime, target_end: datetime) -> Optional[datetime]

async def get_data_ranges(self, symbol: str, timeframe: str,
                         start_time: datetime, end_time: datetime) -> List[DataRange]

async def count_candles_in_range(self, symbol: str, timeframe: str,
                                start_time: datetime, end_time: datetime) -> int

async def has_data_at_time(self, symbol: str, timeframe: str,
                          target_time: datetime) -> bool

async def find_data_start_in_range(self, symbol: str, timeframe: str,
                                  start_time: datetime, end_time: datetime) -> Optional[datetime]

async def save_candle_chunk(self, symbol: str, timeframe: str, candles) -> int

async def get_candles_by_range(self, symbol: str, timeframe: str,
                              start_time: datetime, end_time: datetime) -> List
```

**CONTRACT**:
- 모든 메서드 시그니처 변경 금지
- 반환 타입 호환성 유지
- Infrastructure 모델은 이 인터페이스를 통해서만 접근

## 데이터 변환 계약

### 5. UpbitCandleModel → Repository 형식 변환
```python
def to_repository_format(self) -> Dict[str, Any]:
    """SqliteCandleRepository 호환 형식으로 변환

    CONTRACT:
    - 기존 Repository가 기대하는 키/값 구조 유지
    - 타입 변환 보장 (str → str, float → float, int → int)
    - 선택적 필드 처리 (None 값 제외)
    """
    return {
        'market': self.market,
        'candle_time': self.candle_date_time_utc,  # UTC 시간으로 통일
        'opening_price': self.opening_price,
        'high_price': self.high_price,
        'low_price': self.low_price,
        'trade_price': self.trade_price,
        'timestamp': self.timestamp,
        'candle_acc_trade_price': self.candle_acc_trade_price,
        'candle_acc_trade_volume': self.candle_acc_trade_volume,
        # 타임프레임별 선택적 필드들
        **({k: v for k, v in [
            ('unit', self.unit),
            ('prev_closing_price', self.prev_closing_price),
            ('converting_price_unit', self.converting_price_unit)
        ] if v is not None})
    }
```

### 6. Repository 형식 → UpbitCandleModel 변환
```python
@classmethod
def from_repository_format(cls, data: Dict[str, Any]) -> 'UpbitCandleModel':
    """Repository 데이터에서 모델 생성

    CONTRACT:
    - 기존 Repository 저장 형식 완전 지원
    - 누락 필드에 대한 기본값 처리
    - 시간 형식 변환 (_from_utc_iso 호환)
    """
    return cls(
        market=data['market'],
        candle_date_time_utc=data['candle_time'],
        candle_date_time_kst=data.get('candle_time_kst', ''),  # 없으면 빈 문자열
        opening_price=float(data['opening_price']),
        high_price=float(data['high_price']),
        low_price=float(data['low_price']),
        trade_price=float(data['trade_price']),
        timestamp=int(data.get('timestamp', 0)),
        candle_acc_trade_price=float(data.get('candle_acc_trade_price', 0)),
        candle_acc_trade_volume=float(data.get('candle_acc_trade_volume', 0)),
        unit=data.get('unit'),
        prev_closing_price=data.get('prev_closing_price'),
        converting_price_unit=data.get('converting_price_unit')
    )
```

## 성능 계약

### 7. 메모리 사용량 계약
```python
# CONTRACT: 기존 대비 메모리 사용량 증가 없음
# - frozen dataclass: 최소 메모리 오버헤드
# - Optional 필드: None 값으로 메모리 절약
# - 불필요한 중간 객체 생성 금지
```

### 8. 처리 시간 계약
```python
# CONTRACT: 기존 OverlapAnalyzer 성능 유지 또는 개선
# - 객체 생성 시간: 기존과 동일 또는 개선
# - 변환 작업 시간: 최소화 (직접 매핑)
# - 검증 로직: 필요시에만 실행 (개발 모드)
```

## 테스트 계약

### 9. 호환성 테스트 의무
```python
def test_overlap_analyzer_compatibility():
    """OverlapAnalyzer v5.0과의 완전 호환성 검증

    CONTRACT:
    - 기존 모든 테스트 케이스 통과
    - 동일한 입력에 대해 동일한 출력
    - 성능 회귀 없음
    """
    pass

def test_repository_interface_compatibility():
    """SqliteCandleRepository 인터페이스 호환성 검증

    CONTRACT:
    - 기존 모든 메서드 정상 동작
    - 데이터 무결성 보장
    - 트랜잭션 안전성 유지
    """
    pass
```

### 10. 회귀 테스트 의무
```python
def test_no_regression():
    """기존 기능에 대한 회귀 없음 보장

    CONTRACT:
    - 실제 업비트 API 데이터로 검증
    - 다양한 타임프레임 테스트
    - 예외 상황 처리 검증
    """
    pass
```

---

**호환성 보장 약속**: 이 계약을 위반하는 변경은 허용되지 않음
**검증 방법**: 기존 OverlapAnalyzer v5.0 테스트 스위트 100% 통과
**성능 기준**: 기존 성능 유지 또는 개선
