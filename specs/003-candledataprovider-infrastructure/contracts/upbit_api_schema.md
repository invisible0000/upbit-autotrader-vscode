# 업비트 API 호환성 계약

**목적**: 업비트 REST API 캔들 응답과 Infrastructure 모델 간의 완전 호환성
**중요도**: CRITICAL - 업비트 API 스키마 변경에도 대응 가능해야 함

## API 응답 스키마 계약

### 1. 공통 필드 (모든 타임프레임 필수)
```json
{
  "market": "KRW-BTC",                    // string: 페어 코드
  "candle_date_time_utc": "2025-06-30T00:00:00",  // string: UTC 시간
  "candle_date_time_kst": "2025-06-30T09:00:00",  // string: KST 시간
  "opening_price": 147996000.0,           // double: 시가
  "high_price": 148480000.0,              // double: 고가
  "low_price": 145740000.0,               // double: 저가
  "trade_price": 145759000.0,             // double: 종가
  "timestamp": 1751327999833,             // int64: 마지막 틱 타임스탬프 (ms)
  "candle_acc_trade_price": 138812096716.42776,  // double: 누적 거래금액
  "candle_acc_trade_volume": 944.35761221 // double: 누적 거래량
}
```

**CONTRACT**: UpbitCandleModel은 모든 공통 필드를 필수로 지원해야 함

### 2. 분봉 전용 필드
```json
{
  // ... 공통 필드 ...
  "unit": 5                               // integer: 분봉 단위 (1,3,5,10,15,30,60,240)
}
```

**CONTRACT**: unit 필드는 분봉 타임프레임에서만 존재, Optional[int]로 처리

### 3. 일봉 전용 필드
```json
{
  // ... 공통 필드 ...
  "prev_closing_price": 147996000.0,      // double: 전일 종가
  "change_price": -2237000.0,             // double: 가격 변화 (trade_price - prev_closing_price)
  "change_rate": -0.0151152734             // double: 변화율 ((trade_price - prev_closing_price) / prev_closing_price)
}
```

**CONTRACT**:
- prev_closing_price는 일봉에서만 존재, Optional[float]로 처리
- change_price, change_rate는 DB 저장하지 않음 (계산 가능)
- 필요 시 UpbitCandleModel에서 계산된 프로퍼티로 제공

### 4. 주봉/월봉/연봉 전용 필드
```json
{
  // ... 공통 필드 ...
  "first_day_of_period": "2025-06-30"     // string: 캔들 집계 시작일 (yyyy-MM-dd)
}
```

**CONTRACT**:
- first_day_of_period는 주봉/월봉/연봉에서만 존재
- DB 저장 고려사항: 집계 기간 정보로 활용 가능

### 5. 환산 통화 지원 (선택적 - 일봉만)
```json
{
  // ... 기본 필드 ...
  "converted_trade_price": 49500.123      // double: 환산된 종가 (converting_price_unit="KRW"일 때만)
}
```

**CONTRACT**:
- converting_price_unit 파라미터 요청 시에만 converted_trade_price 필드 존재
- 현재 KRW 환산만 지원, 추후 확장 가능
- DB 저장하지 않음 (API 요청 시마다 계산됨)## 데이터 타입 변환 계약

### 6. Python 타입 매핑
```python
# JSON → Python 타입 변환 규칙 (업비트 API 공식 스펙 기준)
TYPE_MAPPING = {
    "string": str,      # market, candle_date_time_utc, candle_date_time_kst, first_day_of_period
    "double": float,    # 모든 가격/거래량 필드 (opening_price, high_price, low_price, trade_price,
                        # candle_acc_trade_price, candle_acc_trade_volume, prev_closing_price,
                        # change_price, change_rate, converted_trade_price)
    "int64": int,       # timestamp (milliseconds)
    "integer": int,     # unit (분봉 단위)
}

# CONTRACT: 모든 변환은 안전해야 하며, 실패 시 명확한 에러 메시지
def safe_convert(value: Any, target_type: type, field_name: str):
    try:
        if target_type == float:
            return float(value)
        elif target_type == int:
            return int(value)
        elif target_type == str:
            return str(value)
        else:
            raise ValueError(f"Unsupported type: {target_type}")
    except (ValueError, TypeError) as e:
        raise ValueError(f"Failed to convert {field_name}={value} to {target_type}: {e}")
```### 6. 시간 형식 처리 계약
```python
# CONTRACT: 업비트 시간 형식 완전 지원
SUPPORTED_TIME_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",           # 표준: 2025-07-01T12:00:00
    "%Y-%m-%dT%H:%M:%S.%f",        # 마이크로초: 2025-07-01T12:00:00.123456
    "%Y-%m-%dT%H:%M:%SZ",          # UTC 표시: 2025-07-01T12:00:00Z
    "%Y-%m-%dT%H:%M:%S.%fZ",       # UTC + 마이크로초: 2025-07-01T12:00:00.123456Z
]

def parse_upbit_datetime(datetime_str: str) -> datetime:
    """업비트 시간 문자열을 datetime으로 변환

    CONTRACT: 모든 업비트 시간 형식 지원, 파싱 실패 시 명확한 에러
    """
    for fmt in SUPPORTED_TIME_FORMATS:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unsupported datetime format: {datetime_str}")
```

## 필드 검증 계약

### 7. 필수 필드 검증
```python
REQUIRED_FIELDS = {
    'market', 'candle_date_time_utc', 'candle_date_time_kst',
    'opening_price', 'high_price', 'low_price', 'trade_price',
    'timestamp', 'candle_acc_trade_price', 'candle_acc_trade_volume'
}

def validate_required_fields(data: Dict[str, Any]) -> List[str]:
    """필수 필드 존재 검증

    CONTRACT: 필수 필드 누락 시 구체적인 에러 메시지 제공
    """
    missing = REQUIRED_FIELDS - set(data.keys())
    return [f"Missing required field: {field}" for field in missing]
```

### 8. 데이터 무결성 검증
```python
def validate_price_consistency(candle: UpbitCandleModel) -> List[str]:
    """가격 일관성 검증

    CONTRACT: OHLC 관계, 가격 범위, 거래량 검증
    """
    errors = []

    # OHLC 관계 검증
    if not (candle.low_price <= min(candle.opening_price, candle.trade_price) and
            candle.high_price >= max(candle.opening_price, candle.trade_price)):
        errors.append(f"Invalid OHLC relationship: O{candle.opening_price} H{candle.high_price} L{candle.low_price} C{candle.trade_price}")

    # 가격 양수 검증
    prices = [candle.opening_price, candle.high_price, candle.low_price, candle.trade_price]
    if any(p <= 0 for p in prices):
        errors.append(f"All prices must be positive: {prices}")

    # 거래량/거래금액 비음수 검증
    if candle.candle_acc_trade_volume < 0:
        errors.append(f"Trade volume must be non-negative: {candle.candle_acc_trade_volume}")
    if candle.candle_acc_trade_price < 0:
        errors.append(f"Trade price must be non-negative: {candle.candle_acc_trade_price}")

    return errors
```

## API 버전 호환성 계약

### 9. 하위 호환성 보장
```python
# CONTRACT: 새로운 필드 추가에 대한 대응
def handle_unknown_fields(data: Dict[str, Any], known_fields: Set[str]) -> Dict[str, Any]:
    """알려지지 않은 필드 처리

    CONTRACT:
    - 새로운 필드는 무시하고 로그 기록
    - 기존 필드 제거는 에러 발생
    - 버전 정보 메타데이터에 기록
    """
    unknown = set(data.keys()) - known_fields
    if unknown:
        logger.warning(f"Unknown fields detected (possible API update): {unknown}")
        # 메타데이터에 기록하여 추후 분석 가능
        data['_metadata'] = {'unknown_fields': list(unknown)}

    return data
```

### 10. 스키마 버전 추적
```python
@dataclass(frozen=True)
class UpbitApiSchema:
    """업비트 API 스키마 버전 정보"""
    version: str                    # "v1.0", "v1.1" 등
    supported_fields: Set[str]      # 지원되는 필드 목록
    deprecated_fields: Set[str]     # 지원 중단된 필드 목록
    last_updated: datetime          # 마지막 업데이트 시각

    def is_field_supported(self, field: str) -> bool:
        """필드 지원 여부 확인"""
        return field in self.supported_fields and field not in self.deprecated_fields

# CONTRACT: 스키마 변경 시 버전 업데이트와 함께 호환성 검증
CURRENT_SCHEMA = UpbitApiSchema(
    version="2025.09",
    supported_fields=REQUIRED_FIELDS | {'unit', 'prev_closing_price', 'first_day_of_period'},
    deprecated_fields=set(),
    last_updated=datetime(2025, 9, 10)
)
```

## 에러 처리 계약

### 11. 예외 분류 및 처리
```python
class UpbitApiCompatibilityError(Exception):
    """업비트 API 호환성 관련 에러"""
    pass

class FieldMissingError(UpbitApiCompatibilityError):
    """필수 필드 누락"""
    def __init__(self, missing_fields: List[str]):
        self.missing_fields = missing_fields
        super().__init__(f"Missing required fields: {missing_fields}")

class DataValidationError(UpbitApiCompatibilityError):
    """데이터 검증 실패"""
    def __init__(self, validation_errors: List[str]):
        self.validation_errors = validation_errors
        super().__init__(f"Data validation failed: {validation_errors}")

class TypeConversionError(UpbitApiCompatibilityError):
    """타입 변환 실패"""
    def __init__(self, field: str, value: Any, target_type: type, original_error: Exception):
        self.field = field
        self.value = value
        self.target_type = target_type
        self.original_error = original_error
        super().__init__(f"Failed to convert {field}={value} to {target_type}: {original_error}")

# CONTRACT: 모든 에러는 복구 가능한 정보와 함께 제공되어야 함
```

### 12. 복구 및 대체 로직
```python
def create_fallback_candle(raw_data: Dict[str, Any], error: Exception) -> Optional[UpbitCandleModel]:
    """에러 발생 시 대체 캔들 생성

    CONTRACT:
    - 최소한의 필수 정보로 부분 캔들 생성
    - 복구 불가능한 경우 None 반환
    - 복구 과정 로그 기록
    """
    try:
        # 최소 필수 필드만으로 생성 시도
        return UpbitCandleModel(
            market=raw_data.get('market', 'UNKNOWN'),
            candle_date_time_utc=raw_data.get('candle_date_time_utc', '1970-01-01T00:00:00'),
            candle_date_time_kst=raw_data.get('candle_date_time_kst', '1970-01-01T09:00:00'),
            opening_price=float(raw_data.get('opening_price', 0)),
            high_price=float(raw_data.get('high_price', 0)),
            low_price=float(raw_data.get('low_price', 0)),
            trade_price=float(raw_data.get('trade_price', 0)),
            timestamp=int(raw_data.get('timestamp', 0)),
            candle_acc_trade_price=float(raw_data.get('candle_acc_trade_price', 0)),
            candle_acc_trade_volume=float(raw_data.get('candle_acc_trade_volume', 0))
        )
    except Exception as fallback_error:
        logger.error(f"Fallback creation failed: {fallback_error}")
        return None
```

---

**API 호환성 약속**: 업비트 API 스키마 변경에 능동적 대응
**검증 방법**: 실제 업비트 API 응답 데이터로 호환성 테스트
**업데이트 정책**: 새 필드는 Optional로 추가, 기존 필드는 하위 호환성 유지
