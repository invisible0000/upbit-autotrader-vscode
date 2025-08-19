# 🔥 **Phase 2.2 실행 계획서 - 실제 API 연동**

> **현재 상황**: 모의 데이터 기반 UnifiedMarketDataAPI (81/81 테스트 통과)
> **목표**: 실제 업비트 API 완전 연동으로 프로덕션 레디 달성

---

## 📋 **문서 정보**
- **Phase**: 2.2 (실제 API 연동)
- **우선순위**: 최고 (다음 단계 차단 요인)
- **예상 기간**: 3-5일
- **시작일**: 2025년 8월 19일

---

## 🎯 **Phase 2.2 목표 및 성공 기준**

### **핵심 목표**
```python
# 현재 (모의 데이터)
mock_data = self._create_mock_rest_data(symbol)

# 목표 (실제 API)
real_data = await self._upbit_client.get_ticker("KRW-BTC")
websocket_data = await self._websocket_client.get_realtime_ticker("KRW-BTC")
```

### **성공 기준 (측정 가능)**
- [ ] 실제 BTC 현재가 정확 조회 (편차 < 0.1%)
- [ ] REST API 응답시간 < 100ms (평균)
- [ ] WebSocket 실시간 연결 안정성 > 99%
- [ ] 기존 81개 테스트 모두 통과 유지
- [ ] 데이터 품질 검증 통과율 > 95%

---

## 🏗️ **Step-by-Step 실행 계획**

### **Step 1: REST 클라이언트 실제 연동 (Day 1)**

#### **현재 문제점 분석**
```python
# 현재 코드 (unified_market_data_api.py:511)
async def _get_ticker_rest(self, symbol: str) -> UnifiedTickerData:
    mock_rest_data = self._create_mock_rest_data(symbol)  # ← 모의 데이터
    normalized = await self._data_unifier.unify_ticker_data(
        mock_rest_data, "rest", use_cache=True
    )
```

#### **구현 계획**
**1.1. UpbitPublicClient 의존성 주입**
```python
class UnifiedMarketDataAPI:
    def __init__(self, use_websocket: bool = True, cache_ttl: int = 60):
        # 추가할 부분
        from upbit_auto_trading.infrastructure.external_api import UpbitPublicClient
        self._upbit_client = UpbitPublicClient()
```

**1.2. 실제 API 호출 구현**
```python
async def _get_ticker_rest(self, symbol: str) -> UnifiedTickerData:
    try:
        # 실제 API 호출
        api_response = await self._upbit_client.get_ticker(symbol)

        # 응답 검증
        if not self._validate_api_response(api_response):
            raise DataValidationException("API 응답 검증 실패")

        # 정규화 처리
        normalized = await self._data_unifier.unify_ticker_data(
            api_response, "rest", use_cache=True
        )

        return UnifiedTickerData.from_normalized_data(normalized)

    except Exception as e:
        # 에러 처리 및 폴백
        self._logger.error(f"REST API 호출 실패: {e}")
        raise ErrorUnifier.unify_error(e, "rest", "get_ticker")
```

**1.3. 에러 처리 강화**
- HTTP 429 (Rate Limit) → 자동 재시도
- 네트워크 타임아웃 → 폴백 메커니즘
- 잘못된 응답 → 데이터 검증 실패 처리

#### **Day 1 검증 기준**
- [ ] 실제 BTC 현재가 조회 성공
- [ ] API 응답 파싱 정확성 확인
- [ ] 에러 케이스 처리 검증

---

### **Step 2: WebSocket 클라이언트 구현 (Day 2-3)**

#### **현재 문제점**
```python
# 현재 코드 (unified_market_data_api.py:532)
async def _get_ticker_websocket(self, symbol: str) -> UnifiedTickerData:
    self._logger.warning("WebSocket 미구현으로 REST 폴백")  # ← 항상 폴백
    return await self._get_ticker_rest(symbol)
```

#### **구현 계획**
**2.1. WebSocket 클라이언트 통합**
```python
class UnifiedMarketDataAPI:
    def __init__(self, use_websocket: bool = True, cache_ttl: int = 60):
        # 추가할 부분
        if use_websocket:
            from upbit_auto_trading.infrastructure.websocket import UpbitWebSocketClient
            self._websocket_client = UpbitWebSocketClient()
            self._websocket_available = True
        else:
            self._websocket_client = None
            self._websocket_available = False
```

**2.2. 실시간 데이터 처리**
```python
async def _get_ticker_websocket(self, symbol: str) -> UnifiedTickerData:
    if not self._websocket_available:
        self._logger.info("WebSocket 비활성화, REST 사용")
        return await self._get_ticker_rest(symbol)

    try:
        # WebSocket 연결 확인
        if not await self._websocket_client.is_connected():
            await self._websocket_client.connect()

        # 실시간 데이터 요청
        ws_data = await self._websocket_client.get_ticker(symbol, timeout=5.0)

        # 데이터 정규화
        normalized = await self._data_unifier.unify_ticker_data(
            ws_data, "websocket", use_cache=True
        )

        # 채널 상태 업데이트
        self._channel_router.update_channel_health("websocket", True)

        return UnifiedTickerData.from_normalized_data(normalized)

    except asyncio.TimeoutError:
        self._logger.warning("WebSocket 타임아웃, REST 폴백")
        return await self._get_ticker_rest(symbol)
    except Exception as e:
        self._channel_router.update_channel_health("websocket", False, e)
        self._logger.error(f"WebSocket 오류: {e}, REST 폴백")
        return await self._get_ticker_rest(symbol)
```

**2.3. 연결 관리 및 재연결**
- 자동 재연결 메커니즘
- 연결 상태 모니터링
- 구독 관리 (심볼별)

#### **Day 2-3 검증 기준**
- [ ] WebSocket 연결 성공
- [ ] 실시간 데이터 수신 확인
- [ ] 자동 폴백 동작 검증
- [ ] 연결 안정성 테스트 (10분간)

---

### **Step 3: SmartChannelRouter 실제 라우팅 (Day 4)**

#### **현재 상태**
- 빈도 기반 라우팅 로직 완성
- 채널 상태 추적 시스템 완성
- 실제 채널 연결 필요

#### **구현 계획**
**3.1. 실제 채널 가용성 체크**
```python
def _is_websocket_available(self) -> bool:
    """실제 WebSocket 연결 상태 확인"""
    if not self._websocket_client:
        return False

    # 실제 연결 상태 확인
    return self._websocket_client.is_connected() and \
           self._channel_health["websocket"]["available"]
```

**3.2. 지능형 라우팅 최적화**
- 실제 응답시간 기반 채널 선택
- 데이터 신선도 (freshness) 고려
- 에러율 기반 자동 조정

#### **Day 4 검증 기준**
- [ ] 고빈도 요청 → WebSocket 자동 선택
- [ ] 저빈도 요청 → REST 사용
- [ ] 채널 장애 시 자동 폴백
- [ ] 라우팅 정확도 > 95%

---

### **Step 4: 통합 테스트 및 성능 검증 (Day 5)**

#### **성능 벤치마크**
```python
async def benchmark_unified_api():
    api = UnifiedMarketDataAPI(use_websocket=True)

    # REST 성능 테스트
    rest_times = []
    for _ in range(100):
        start = time.time()
        await api.get_ticker("KRW-BTC", source_hint="rest")
        rest_times.append((time.time() - start) * 1000)

    # WebSocket 성능 테스트
    ws_times = []
    for _ in range(100):
        start = time.time()
        await api.get_ticker("KRW-BTC", source_hint="websocket")
        ws_times.append((time.time() - start) * 1000)

    print(f"REST 평균: {np.mean(rest_times):.2f}ms")
    print(f"WebSocket 평균: {np.mean(ws_times):.2f}ms")
```

#### **데이터 정확성 검증**
```python
async def validate_data_accuracy():
    api = UnifiedMarketDataAPI()

    # 동시 요청으로 일관성 확인
    rest_data = await api.get_ticker("KRW-BTC", source_hint="rest")
    ws_data = await api.get_ticker("KRW-BTC", source_hint="websocket")

    # 가격 차이 확인 (< 0.1% 허용)
    price_diff = abs(rest_data.current_price - ws_data.current_price)
    assert price_diff / rest_data.current_price < 0.001
```

#### **Day 5 검증 기준**
- [ ] 성능 목표 달성 (REST < 100ms, WebSocket < 50ms)
- [ ] 데이터 일관성 검증 통과
- [ ] 81개 기존 테스트 모두 통과
- [ ] 실제 운영 환경 시뮬레이션 성공

---

## 🔧 **구현 상세 사항**

### **파일 수정 목록**
1. **`unified_market_data_api.py`**:
   - `__init__()`: 실제 클라이언트 주입
   - `_get_ticker_rest()`: 실제 API 호출
   - `_get_ticker_websocket()`: WebSocket 구현

2. **`test_unified_market_data_api.py`**:
   - 실제 API 응답 테스트 추가
   - 모킹 전략 업데이트
   - 성능 벤치마크 테스트

### **새로운 의존성**
```python
# 필요한 import 추가
from upbit_auto_trading.infrastructure.external_api import UpbitPublicClient
from upbit_auto_trading.infrastructure.websocket import UpbitWebSocketClient
```

### **설정 관리**
```python
# config/development.yaml 추가
market_data_backbone:
  use_websocket: true
  rest_timeout: 10.0
  websocket_timeout: 5.0
  max_retries: 3
```

---

## 🧪 **테스트 전략**

### **단위 테스트**
- [ ] 실제 API 응답 파싱 테스트
- [ ] 에러 케이스 처리 테스트
- [ ] 캐싱 동작 검증

### **통합 테스트**
- [ ] 실제 업비트 API 연동 테스트
- [ ] WebSocket 연결 안정성 테스트
- [ ] SmartChannelRouter 라우팅 테스트

### **성능 테스트**
- [ ] 응답시간 벤치마크
- [ ] 동시 요청 처리 능력
- [ ] 메모리 사용량 모니터링

---

## ⚠️ **리스크 및 대응**

### **기술적 리스크**
- **업비트 API 응답 변경**: 데이터 검증 로직 강화
- **WebSocket 연결 불안정**: 자동 재연결 + REST 폴백
- **Rate Limit 초과**: 요청 간격 조정, 캐싱 활용

### **일정 리스크**
- **복잡성 과소평가**: 각 단계별 중간 점검
- **기존 기능 회귀**: 매일 전체 테스트 실행
- **성능 목표 미달성**: 최적화 작업 추가 시간 확보

---

## 📊 **진행 상황 추적**

### **Daily Checkpoint**
- **Day 1**: REST 연동 ✅/❌
- **Day 2**: WebSocket 기본 연결 ✅/❌
- **Day 3**: WebSocket 데이터 처리 ✅/❌
- **Day 4**: SmartChannelRouter 완성 ✅/❌
- **Day 5**: 통합 검증 ✅/❌

### **최종 검증 명령어**
```powershell
# 1. 실제 API 연동 확인
python demonstrate_phase_2_2_real_api.py

# 2. 전체 테스트 실행
pytest tests/infrastructure/market_data_backbone/v2/ -v

# 3. 성능 벤치마크
python benchmark_unified_api.py

# 4. 통합 시스템 확인
python run_desktop_ui.py
```

---

## 🎯 **Phase 2.2 완료 후 상태**

### **달성될 상태**
- 실제 업비트 API 완전 연동
- WebSocket 실시간 데이터 스트림
- SmartChannelRouter 지능형 라우팅
- 프로덕션 레디 데이터 백본

### **다음 단계 준비**
- Phase 2.3: 7규칙 전략 시스템 연동 준비 완료
- 실제 데이터 기반 전략 테스트 가능
- 차트뷰어 실시간 데이터 공급 준비

---

**📅 작성일**: 2025년 8월 19일
**⏰ 예상 완료**: 2025년 8월 24일
**🎯 다음 페이즈**: Phase 2.3 (7규칙 전략 통합)
