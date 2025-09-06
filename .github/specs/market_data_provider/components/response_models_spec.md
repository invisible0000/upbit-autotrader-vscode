# Response Models 기능 명세

## 개요
- **파일 경로**: `smart_data_provider_V4/response_models.py`
- **코드 라인 수**: 177줄
- **목적**: 데이터 응답 모델 및 우선순위 시스템 정의
- **핵심 기능**: 데이터 소스 추적, 실시간성 보장, 우선순위 기반 응답 관리

## 주요 컴포넌트

### 1. DataSourceInfo (데이터 소스 정보)
```python
@dataclass
class DataSourceInfo:
    channel: Literal["websocket", "rest_api", "cache"]
    stream_type: Optional[Literal["snapshot", "realtime"]] = None
    cache_info: Optional[Dict[str, Any]] = None
    reliability: float = 1.0  # 0.0-1.0
    latency_ms: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
```

**핵심 기능**:
- **데이터 소스 추적**: websocket/rest_api/cache 채널 식별
- **실시간성 검증**: `is_realtime()` - WebSocket 실시간 스트림 여부
- **신선도 계산**: `freshness_score()` - TTL 기반 데이터 신선도 (0.0-1.0)
- **소스 요약**: `get_source_summary()` - 채널, 지연시간, 캐시 나이 정보

**검증 로직**:
- WebSocket 채널 시 stream_type 필수
- reliability 범위 0.0-1.0 검증

### 2. DataResponse (통합 데이터 응답)
```python
@dataclass
class DataResponse:
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    data_source: Optional[DataSourceInfo] = None
```

**팩토리 메서드**:
- `create_success(data, data_source, **metadata)` - 성공 응답 생성
- `create_error(error, data_source, **metadata)` - 실패 응답 생성

**데이터 접근 메서드**:
- `get(key)` - 키별 데이터 반환 또는 전체 Dict
- `get_single(symbol)` - 단일 심볼 데이터
- `get_all()` - 전체 Dict 데이터

**데이터 소스 편의 속성**:
- `source_channel` - 데이터 소스 채널
- `is_realtime` - 실시간 데이터 여부
- `is_cached` - 캐시된 데이터 여부
- `freshness_score` - 데이터 신선도 점수
- `reliability` - 데이터 신뢰도
- `get_source_summary()` - 소스 메타데이터 딕셔너리

### 3. Priority (우선순위 시스템)
```python
class Priority(Enum):
    CRITICAL = 1    # 실거래봇 (< 50ms)
    HIGH = 2        # 실시간 모니터링 (< 100ms)
    NORMAL = 3      # 차트뷰어 (< 500ms)
    LOW = 4         # 백테스터 (< 5000ms)
```

**성능 기준**:
- `max_response_time_ms` - 우선순위별 최대 응답시간
- `description` - 우선순위 설명
- `smart_router_priority` - SmartRouter 호환 문자열 매핑

**SmartRouter 호환성**:
- CRITICAL/HIGH → "high"
- NORMAL → "normal"
- LOW → "low"

## 기술적 특징

### 실시간성 보장
- **데이터 소스 추적**: 모든 응답에 출처 정보 포함
- **신선도 점수**: TTL 기반 캐시 데이터 신선도 계산
- **실시간 판별**: WebSocket 실시간 스트림 식별

### 우선순위 기반 성능 관리
- **응답 시간 SLA**: 우선순위별 최대 응답시간 정의
- **SmartRouter 통합**: 기존 라우터와 호환되는 우선순위 매핑
- **용도별 분류**: 실거래봇/모니터링/차트/백테스터 구분

### 데이터 접근 패턴
- **유연한 접근**: 키별, 심볼별, 전체 데이터 접근 지원
- **메타데이터 확장**: 임의 메타데이터 추가 가능
- **에러 처리**: 성공/실패 응답 통합 모델

## 사용 예시

### 성공 응답 생성
```python
source_info = DataSourceInfo(
    channel="websocket",
    stream_type="realtime",
    reliability=1.0,
    latency_ms=15.2
)

response = DataResponse.create_success(
    data={"KRW-BTC": {...}},
    data_source=source_info,
    total_count=1,
    request_id="req_123"
)
```

### 캐시 데이터 신선도 확인
```python
if response.freshness_score > 0.8:
    # 신선한 데이터 사용
    process_data(response.data)
else:
    # 새로운 데이터 요청 필요
    refresh_data()
```

### 우선순위 기반 응답시간 관리
```python
priority = Priority.CRITICAL
max_time = priority.max_response_time_ms  # 50.0ms
router_priority = priority.smart_router_priority  # "high"
```

## 의존성
- **표준 라이브러리**: dataclasses, typing, datetime, enum
- **외부 의존성**: 없음
- **아키텍처 계층**: Infrastructure Layer (DDD)

## 성능 특성
- **메모리 효율성**: @dataclass 사용으로 최적화
- **타입 안전성**: 완전한 타입 힌트 제공
- **확장성**: 메타데이터 및 데이터 소스 정보 확장 가능

## 핵심 가치
1. **실시간성 추적**: 데이터 출처와 신선도 명확한 식별
2. **성능 관리**: 우선순위 기반 응답시간 SLA
3. **호환성**: 기존 SmartRouter와 완전 호환
4. **유연성**: 다양한 데이터 접근 패턴 지원
