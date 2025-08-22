# 📡 업비트 스마트 라우터 V2.0 기획서

## 🎯 프로젝트 개요

### 목적
업비트 WebSocket과 REST API의 형식 차이와 지원 범위 차이를 해결하여, 사용자가 데이터 요청 시 최적의 통신 채널을 자동으로 선택하는 스마트 라우팅 시스템 구축

### 현재 문제점
- ❌ **형식 불일치**: WebSocket과 REST API 응답 형식이 완전히 다름
- ❌ **지원 범위 차이**: 특정 기능은 한쪽 API에서만 지원
- ❌ **복잡한 선택**: 개발자가 매번 어떤 API를 사용할지 결정해야 함
- ❌ **비효율적 사용**: 상황에 맞지 않는 API 채널 사용으로 성능 저하

---

## 📊 업비트 API 분석

### WebSocket vs REST API 비교표

| 구분 | WebSocket | REST API | 비고 |
|------|-----------|----------|------|
| **연결 방식** | 지속적 연결 | 요청-응답 | WebSocket은 한번 연결 후 지속적 데이터 수신 |
| **실시간성** | 실시간 스트림 | 폴링 방식 | WebSocket이 실시간 데이터에 유리 |
| **Rate Limit** | 5 req/s, 100 req/min | 10 req/s, 600 req/min | REST가 더 많은 요청 허용 |
| **데이터 형식** | 바이너리/JSON 스트림 | JSON 응답 | 완전히 다른 파싱 방식 필요 |
| **연결 안정성** | 불안정 (재연결 필요) | 안정적 | REST가 더 안정적 |

### 지원 기능 매트릭스

| 기능 | WebSocket | REST API | 최적 채널 권장 |
|------|:---------:|:--------:|:-------------:|
| **실시간 티커** | ✅ | ✅ | WebSocket |
| **과거 캔들 데이터** | ❌ | ✅ | REST |
| **실시간 체결** | ✅ | ✅ | WebSocket |
| **호가 정보** | ✅ | ✅ | WebSocket |
| **계정 정보** | ❌ | ✅ | REST |
| **주문 관리** | ❌ | ✅ | REST |
| **입출금 내역** | ❌ | ✅ | REST |
| **1초 캔들** | ✅ (Beta) | ❌ | WebSocket |

### 형식 차이 예시

#### REST API 티커 응답
```json
{
  "market": "KRW-BTC",
  "trade_date": "20241031",
  "trade_time": "010742",
  "trade_date_kst": "20241031",
  "trade_time_kst": "100742",
  "trade_timestamp": 1730336862000,
  "opening_price": 100571000.0,
  "high_price": 100673000.0,
  "low_price": 100380000.0,
  "trade_price": 100473000.0,
  "prev_closing_price": 100571000.0,
  "change": "FALL",
  "change_price": 98000.0,
  "change_rate": -0.0009744058,
  "signed_change_price": -98000.0,
  "signed_change_rate": -0.0009744058,
  "trade_volume": 0.00014208,
  "acc_trade_price": 73891234567.89,
  "acc_trade_price_24h": 147782469135.78,
  "acc_trade_volume": 736.15823456,
  "acc_trade_volume_24h": 1472.31646912,
  "highest_52_week_price": 120000000.0,
  "highest_52_week_date": "2024-03-14",
  "lowest_52_week_price": 45000000.0,
  "lowest_52_week_date": "2024-01-01",
  "timestamp": 1730336862082
}
```

#### WebSocket 티커 응답
```json
{
  "type": "ticker",
  "code": "KRW-BTC",
  "opening_price": 100571000.0,
  "high_price": 100673000.0,
  "low_price": 100380000.0,
  "trade_price": 100473000.0,
  "prev_closing_price": 100571000.0,
  "change": "FALL",
  "change_price": 98000.0,
  "change_rate": -0.0009744058,
  "signed_change_price": -98000.0,
  "signed_change_rate": -0.0009744058,
  "trade_volume": 0.00014208,
  "acc_trade_price": 73891234567.89,
  "acc_trade_price_24h": 147782469135.78,
  "acc_trade_volume": 736.15823456,
  "acc_trade_volume_24h": 1472.31646912,
  "highest_52_week_price": 120000000.0,
  "highest_52_week_date": "2024-03-14",
  "lowest_52_week_price": 45000000.0,
  "lowest_52_week_date": "2024-01-01",
  "timestamp": 1730336862082,
  "stream_type": "REALTIME"
}
```

---

## 🏗️ 3단계 구현 전략

### 1단계: 지원 범위 기반 형식 통일

#### 목표
- 지원 범위가 넓은 통신 채널을 기준으로 데이터 형식 통일
- REST API를 표준 형식으로 선정 (더 넓은 지원 범위)

#### 구현 방안

```python
class DataFormatUnifier:
    """WebSocket과 REST API 응답을 통일된 형식으로 변환"""

    @staticmethod
    def unify_ticker_data(data: Dict, source: str) -> Dict:
        """티커 데이터를 REST API 형식으로 통일"""
        if source == "websocket":
            # WebSocket 형식을 REST 형식으로 변환
            return {
                "market": data["code"],
                "trade_date": datetime.fromtimestamp(data["timestamp"]/1000).strftime("%Y%m%d"),
                "trade_time": datetime.fromtimestamp(data["timestamp"]/1000).strftime("%H%M%S"),
                "opening_price": data["opening_price"],
                "high_price": data["high_price"],
                "low_price": data["low_price"],
                "trade_price": data["trade_price"],
                # ... 나머지 필드 매핑
                "data_source": "websocket_unified"
            }
        else:
            # REST API 형식은 그대로 유지
            data["data_source"] = "rest_api"
            return data
```

#### 형식 통일 규칙

| 데이터 타입 | 표준 형식 | 변환 방식 |
|------------|----------|----------|
| **티커** | REST API 형식 | WebSocket → REST 변환 |
| **호가** | REST API 형식 | WebSocket → REST 변환 |
| **체결** | REST API 형식 | WebSocket → REST 변환 |
| **캔들** | REST API 형식 | 기본 REST 사용 |
| **1초 캔들** | WebSocket 형식 | WebSocket 전용 |

### 2단계: 고정 채널 라우팅 규칙

#### REST API 전용 (고정)
```python
REST_ONLY_ENDPOINTS = {
    "candles": "과거 데이터는 REST가 효율적",
    "accounts": "계정 정보는 REST만 지원",
    "orders": "주문 관리는 REST만 지원",
    "deposits": "입출금 내역은 REST만 지원",
    "withdraws": "출금 내역은 REST만 지원",
    "status": "API 상태는 REST만 지원"
}
```

#### WebSocket 전용 (고정)
```python
WEBSOCKET_ONLY_ENDPOINTS = {
    "candles_1s": "1초 캔들은 WebSocket만 지원 (Beta)",
    "realtime_stream": "연속적 실시간 스트림"
}
```

#### 유연 채널 (상황별 선택)
```python
FLEXIBLE_ENDPOINTS = {
    "ticker": "실시간성 vs 안정성",
    "orderbook": "실시간성 vs 안정성",
    "trades": "실시간성 vs 과거 데이터"
}
```

### 3단계: 스마트 선택 알고리즘

#### 선택 기준 점수표

| 요소 | WebSocket 점수 | REST 점수 | 가중치 |
|------|:-------------:|:---------:|:------:|
| **실시간성 요구** | +10 | +2 | 3x |
| **안정성 요구** | +2 | +10 | 2x |
| **요청 빈도** | +8 (고빈도) | +5 (저빈도) | 2x |
| **데이터 양** | +3 (소량) | +8 (대량) | 1x |
| **연결 상태** | +10 (연결됨) | +10 (항상) | 3x |
| **Rate Limit** | +5 (여유) | +8 (여유) | 2x |

#### 스마트 선택 로직

```python
class SmartChannelSelector:
    def select_channel(self, request: DataRequest) -> str:
        """상황에 맞는 최적 채널 선택"""

        # 1단계: 고정 채널 확인
        if request.endpoint in REST_ONLY_ENDPOINTS:
            return "rest"
        if request.endpoint in WEBSOCKET_ONLY_ENDPOINTS:
            return "websocket"

        # 2단계: 점수 계산
        ws_score = self._calculate_websocket_score(request)
        rest_score = self._calculate_rest_score(request)

        # 3단계: 최종 선택
        if ws_score > rest_score * 1.2:  # 20% 마진
            return "websocket"
        else:
            return "rest"

    def _calculate_websocket_score(self, request: DataRequest) -> float:
        score = 0

        # 실시간성 요구
        if request.realtime_priority == "high":
            score += 10 * 3
        elif request.realtime_priority == "medium":
            score += 6 * 3

        # 요청 빈도
        if request.frequency > 0.5:  # 2초 이하 간격
            score += 8 * 2

        # 연결 상태
        if self.websocket_manager.is_connected():
            score += 10 * 3

        # Rate Limit 상태
        if self.websocket_manager.get_rate_limit_usage() < 0.8:
            score += 5 * 2

        return score
```

---

## 🔧 기술 구현 세부사항

### 아키텍처 설계

```
┌─────────────────────────────────────────────────────────┐
│                 SmartRouter V2.0                       │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐│
│  │ Format Unifier  │  │ Channel Selector│  │ Data Cache  ││
│  │                 │  │                 │  │             ││
│  │ • WS→REST       │  │ • Smart Logic   │  │ • 형식 통일  ││
│  │ • REST→REST     │  │ • Fixed Rules   │  │ • 빠른 응답  ││
│  └─────────────────┘  └─────────────────┘  └─────────────┘│
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────┐                  ┌─────────────────┐│
│  │ WebSocket Mgr   │                  │ REST API Mgr    ││
│  │                 │                  │                 ││
│  │ • 연결 관리      │                  │ • HTTP 요청     ││
│  │ • 스트림 처리    │                  │ • Rate Limit    ││
│  │ • 재연결 로직    │                  │ • 안정성 우선   ││
│  └─────────────────┘                  └─────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### 핵심 컴포넌트

#### 1. DataFormatUnifier (형식 통일기)
```python
class DataFormatUnifier:
    """모든 데이터를 REST API 형식으로 통일"""

    FIELD_MAPPING = {
        "websocket_ticker": {
            "code": "market",
            "timestamp": lambda x: {
                "trade_date": datetime.fromtimestamp(x/1000).strftime("%Y%m%d"),
                "trade_time": datetime.fromtimestamp(x/1000).strftime("%H%M%S"),
                "timestamp": x
            }
        }
    }

    def unify(self, data: Any, source: str, data_type: str) -> Dict:
        """데이터를 통일된 형식으로 변환"""
        key = f"{source}_{data_type}"
        mapping = self.FIELD_MAPPING.get(key, {})

        result = {}
        for ws_field, rest_field in mapping.items():
            if callable(rest_field):
                result.update(rest_field(data[ws_field]))
            else:
                result[rest_field] = data[ws_field]

        result["_source"] = source
        result["_unified_at"] = time.time()
        return result
```

#### 2. ChannelSelector (채널 선택기)
```python
class ChannelSelector:
    """최적 통신 채널 선택"""

    def __init__(self):
        self.usage_history = defaultdict(list)
        self.performance_metrics = {}

    def select(self, request: DataRequest) -> ChannelDecision:
        """요청에 대한 최적 채널 결정"""

        # 고정 규칙 확인
        if fixed_channel := self._get_fixed_channel(request):
            return ChannelDecision(
                channel=fixed_channel,
                reason="fixed_rule",
                confidence=1.0
            )

        # 스마트 선택
        scores = self._calculate_scores(request)
        selected = max(scores, key=scores.get)
        confidence = scores[selected] / sum(scores.values())

        return ChannelDecision(
            channel=selected,
            reason="smart_selection",
            confidence=confidence,
            scores=scores
        )
```

#### 3. RequestPatternAnalyzer (패턴 분석기)
```python
class RequestPatternAnalyzer:
    """요청 패턴 분석 및 예측"""

    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self.request_history = defaultdict(deque)

    def analyze_frequency(self, symbol: str) -> FrequencyAnalysis:
        """요청 빈도 분석"""
        history = self.request_history[symbol]
        if len(history) < 3:
            return FrequencyAnalysis(
                category="unknown",
                avg_interval=0.0,
                trend="stable"
            )

        intervals = [
            history[i] - history[i-1]
            for i in range(1, len(history))
        ]

        avg_interval = sum(intervals) / len(intervals)

        # 추세 분석
        recent_avg = sum(intervals[-3:]) / 3
        older_avg = sum(intervals[:-3]) / (len(intervals) - 3)

        if recent_avg < older_avg * 0.7:
            trend = "accelerating"
        elif recent_avg > older_avg * 1.3:
            trend = "decelerating"
        else:
            trend = "stable"

        # 빈도 카테고리
        if avg_interval < 2.0:
            category = "high_frequency"
        elif avg_interval < 10.0:
            category = "medium_frequency"
        else:
            category = "low_frequency"

        return FrequencyAnalysis(
            category=category,
            avg_interval=avg_interval,
            trend=trend
        )
```

---

## 📋 구현 로드맵

### Phase 1: 기반 구조 (1주차)
- [ ] 현재 smart_routing 폴더 구조 분석
- [ ] DataFormatUnifier 구현
- [ ] 기본 ChannelSelector 구현
- [ ] 단위 테스트 작성

### Phase 2: 고정 규칙 (2주차)
- [ ] REST 전용 엔드포인트 정의
- [ ] WebSocket 전용 엔드포인트 정의
- [ ] 고정 라우팅 로직 구현
- [ ] 통합 테스트

### Phase 3: 스마트 선택 (3주차)
- [ ] RequestPatternAnalyzer 구현
- [ ] 점수 기반 선택 알고리즘
- [ ] 성능 메트릭 수집
- [ ] 피드백 루프 구현

### Phase 4: 최적화 (4주차)
- [ ] 캐시 시스템 구현
- [ ] Rate Limit 관리 고도화
- [ ] 오류 처리 및 복구
- [ ] 모니터링 대시보드

---

## 🎯 성공 기준

### 기능적 요구사항
- ✅ **형식 통일**: 모든 응답이 일관된 형식
- ✅ **자동 선택**: 수동 채널 지정 불필요
- ✅ **고정 규칙**: 특정 요청의 채널 고정
- ✅ **스마트 선택**: 상황별 최적 채널 선택

### 성능 요구사항
- **응답 시간**: < 100ms (캐시 히트 시)
- **정확도**: > 85% (올바른 채널 선택)
- **안정성**: 99.9% uptime
- **메모리**: < 100MB 사용

### 사용성 요구사항
- **API 단순화**: 기존 대비 50% 코드 감소
- **투명성**: 선택 이유 제공
- **디버깅**: 상세한 로그 및 메트릭

---

## 🔍 예상 도전과제 및 해결방안

### 도전과제 1: WebSocket 연결 불안정
**문제**: WebSocket 연결이 자주 끊어져 데이터 손실 발생
**해결**:
- 자동 재연결 로직
- 실패 시 즉시 REST API 폴백
- 연결 상태 실시간 모니터링

### 도전과제 2: Rate Limit 관리 복잡성
**문제**: 두 채널의 서로 다른 Rate Limit 동시 관리
**해결**:
- 채널별 독립적인 Rate Limit 추적
- 80% 사용률에서 경고, 90%에서 제한
- 요청 큐를 통한 스케줄링

### 도전과제 3: 형식 변환 오버헤드
**문제**: 실시간 데이터 변환으로 인한 지연
**해결**:
- 필수 필드만 변환하는 경량 모드
- 백그라운드 변환 처리
- 변환 결과 캐싱

---

## 📈 모니터링 및 개선

### 핵심 메트릭
```python
METRICS_TO_TRACK = {
    "channel_selection_accuracy": "올바른 채널 선택 비율",
    "response_time_p95": "95%ile 응답 시간",
    "websocket_connection_uptime": "WebSocket 연결 안정성",
    "rest_api_success_rate": "REST API 성공률",
    "format_conversion_time": "형식 변환 소요 시간",
    "cache_hit_ratio": "캐시 히트 비율"
}
```

### 지속적 개선
- **주간 리뷰**: 성능 메트릭 분석
- **사용자 피드백**: API 사용 패턴 수집
- **A/B 테스팅**: 새로운 선택 알고리즘 검증
- **자동 튜닝**: ML 기반 파라미터 최적화

---

## 🚀 기대 효과

### 개발자 경험 개선
- **단순한 API**: 하나의 인터페이스로 모든 데이터 접근
- **자동 최적화**: 개발자가 채널 선택 고민 불필요
- **일관된 형식**: 동일한 파싱 로직 재사용 가능

### 시스템 성능 향상
- **최적 채널 사용**: 상황별 최적 성능
- **Rate Limit 효율**: 두 채널의 최대 활용
- **지연 최소화**: 스마트한 캐싱과 라우팅

### 유지보수성 향상
- **중앙 집중**: 하나의 라우터에서 모든 채널 관리
- **투명성**: 선택 이유와 성능 메트릭 제공
- **확장성**: 새로운 채널 추가 용이

---

**🎯 최종 목표**: "개발자는 데이터만 요청하고, 시스템이 알아서 최적화하는 투명한 스마트 라우터"
