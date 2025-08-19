# 🚀 **MarketDataBackbone V2 - 다음 작업**

> **Phase 1.2 WebSocket 통합 완료! 🎉**
> **다음 Phase 계획 및 발전 방향**

---

## 🎯 **Phase 1.2 완료 성과**

**📅 완료일**: 2025년 8월 19일
**⏰ 소요 기간**: 1일 (계획 대비 빠른 완료)
**🎯 달성 목표**: 실시간 스트림 API 완전 구현
**✅ 성공 지표**: backbone.stream_ticker(["KRW-BTC"]) 정상 동작

### **🛠️ 완료된 주요 구현**
- ✅ **WebSocketManager**: 완전한 연결 관리 및 구독 시스템
- ✅ **실시간 스트림**: `stream_ticker()`, `stream_orderbook()` API
- ✅ **지능적 채널 선택**: AUTO, REST_ONLY, WEBSOCKET_ONLY 전략
- ✅ **자동 재연결**: 장애 복구 및 구독 복원
- ✅ **테스트 커버리지**: 28/28 통과 (기존 16개 + 신규 12개)

---

## 🚀 **다음 Phase: 1.3 고급 데이터 관리**

**📅 시작 예정**: 즉시 시작 가능
**⏰ 예상 기간**: 2-3일
**🎯 최종 목표**: 고급 데이터 처리 및 캐싱 시스템
**✅ 전제조건**: Phase 1.2 완료 ✅

### **🔥 Phase 1.3 핵심 작업**

#### **1단계: DataUnifier 고도화** (1일)
```python
class DataUnifier:
    """데이터 통합 및 정규화 시스템"""

    async def unify_ticker_data(self, rest_data, ws_data) -> TickerData:
        """REST와 WebSocket 데이터 통합"""

    async def validate_data_consistency(self, data) -> bool:
        """데이터 일관성 검증"""

    async def apply_data_corrections(self, data) -> TickerData:
        """데이터 보정 및 정규화"""
```

#### **2단계: 지능형 캐싱 시스템** (1일)
```python
class IntelligentCache:
    """시간 기반 지능형 캐싱"""

    async def cache_with_ttl(self, key: str, data: Any, ttl: int):
        """TTL 기반 캐싱"""

    async def invalidate_on_update(self, symbol: str):
        """업데이트 시 캐시 무효화"""

    async def warm_cache(self, symbols: List[str]):
        """캐시 예열"""
```

#### **3단계: 고급 에러 처리** (0.5일)
```python
class AdvancedErrorHandler:
    """고급 에러 처리 및 복구"""

    async def handle_rate_limit_exceeded(self):
        """Rate Limit 초과 시 대응"""

    async def handle_data_inconsistency(self, data):
        """데이터 불일치 감지 및 복구"""

    async def circuit_breaker_pattern(self):
        """Circuit Breaker 패턴 구현"""
```

---

## 🔮 **장기 로드맵**

### **Phase 1.4: 백테스팅 데이터 파이프라인** (3-4일)
- 과거 데이터 수집 및 저장
- 백테스팅용 데이터 포맷 표준화
- 데이터 무결성 검증 시스템

### **Phase 2.0: 완전한 자동매매 시스템** (1-2주)
- 7규칙 전략 엔진 통합
- 실시간 주문 실행 시스템
- 리스크 관리 및 모니터링

### **Phase 2.1: 고급 최적화** (1주)
- 성능 최적화 및 메모리 관리
- 분산 처리 시스템
- 고가용성 아키텍처

---

## 📋 **즉시 시작 가능한 작업**

### **1. DataUnifier 구현 시작**
```powershell
# 새 파일 생성
New-Item -Path "upbit_auto_trading\infrastructure\market_data_backbone\v2\data_unifier.py" -ItemType File

# 기본 구조 구현
code "upbit_auto_trading\infrastructure\market_data_backbone\v2\data_unifier.py"
```

### **2. 캐싱 시스템 설계**
```powershell
# 캐시 관리자 생성
New-Item -Path "upbit_auto_trading\infrastructure\market_data_backbone\v2\cache_manager.py" -ItemType File
```

### **3. 고급 테스트 추가**
```powershell
# 통합 테스트 파일 생성
New-Item -Path "tests\infrastructure\market_data_backbone\v2\test_advanced_features.py" -ItemType File
```

---

## 🎯 **Phase 1.3 성공 기준**

### **기능적 성공 기준**
- [ ] DataUnifier 완전 구현 및 테스트
- [ ] 캐싱 시스템 동작 및 성능 개선 확인
- [ ] 고급 에러 처리 시나리오 모두 통과
- [ ] 데이터 일관성 검증 시스템 동작

### **품질적 성공 기준**
- [ ] 새 테스트 모두 통과 (예상 10-15개 추가)
- [ ] 기존 테스트 모두 유지 (28/28)
- [ ] 성능 개선 측정 가능
- [ ] 메모리 사용량 최적화

### **성능적 성공 기준**
- [ ] 캐시 적중률 > 80%
- [ ] 응답 시간 20% 개선
- [ ] 메모리 사용량 < 100MB
- [ ] 에러 복구 시간 < 3초

---

## 💡 **개발 가이드라인**

### **Phase 1.3 핵심 원칙**
1. **데이터 품질 우선**: 정확성과 일관성이 성능보다 중요
2. **점진적 최적화**: 기본 기능 구현 후 성능 튜닝
3. **테스트 주도**: 모든 기능은 테스트와 함께
4. **문서 동기화**: 구현과 함께 문서 업데이트

### **참고할 기존 패턴**
- WebSocketManager의 에러 처리 패턴
- MarketDataBackbone의 초기화 패턴
- Infrastructure 로깅 표준
- DDD 계층 분리 원칙

---

## 🚀 **시작하기**

### **즉시 시작 명령어**
```powershell
# 1. 현재 상태 확인
python demonstrate_phase_1_2_websocket.py

# 2. 새 Phase 디렉토리 준비
mkdir -p "docs\market_data_backbone_v2\phase_1_3"

# 3. DataUnifier 기본 클래스 생성
code "upbit_auto_trading\infrastructure\market_data_backbone\v2\data_unifier.py"
```

### **첫 번째 구현 목표** (오늘)
1. `DataUnifier` 기본 클래스 구조 생성
2. 간단한 데이터 통합 메서드 구현
3. 기본 테스트 작성 및 검증

---

**🎉 Phase 1.2 WebSocket 통합 성공을 축하하며, Phase 1.3으로 진화합니다! 🎉**

---

## 📋 **작업 순서 (우선순위)**

### **🔥 1단계: WebSocketManager 기본 클래스 구현** (1일)
**파일**: `upbit_auto_trading/infrastructure/market_data_backbone/v2/websocket_manager.py`

#### **구현할 클래스 구조**
```python
from typing import AsyncGenerator, Dict, List, Optional, Set
from asyncio import Queue
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import UpbitWebSocketQuotationClient
from .models import TickerData, OrderbookData

class ChannelType(Enum):
    TICKER = "ticker"
    ORDERBOOK = "orderbook"
    TRADE = "trade"

@dataclass
class SubscriptionRequest:
    symbols: List[str]
    channel_type: ChannelType
    callback_queue: Queue

class WebSocketManager:
    """WebSocket 연결 및 구독 관리 클래스"""

    def __init__(self):
        self.logger = create_component_logger("WebSocketManager")
        self._client: Optional[UpbitWebSocketQuotationClient] = None
        self._subscriptions: Dict[str, SubscriptionRequest] = {}
        self._message_queues: Dict[str, Queue] = {}
        self._is_connected = False
        self._reconnect_task: Optional[asyncio.Task] = None

    async def connect(self) -> bool:
        """WebSocket 연결 설정"""
        pass

    async def disconnect(self) -> None:
        """WebSocket 연결 해제"""
        pass

    async def subscribe_ticker(self, symbols: List[str]) -> Queue:
        """티커 데이터 구독"""
        pass

    async def subscribe_orderbook(self, symbols: List[str]) -> Queue:
        """호가 데이터 구독"""
        pass

    async def unsubscribe(self, subscription_id: str) -> None:
        """구독 해제"""
        pass

    async def _handle_message(self, message: Dict) -> None:
        """수신 메시지 처리"""
        pass

    async def _auto_reconnect(self) -> None:
        """자동 재연결 로직"""
        pass
```

#### **구현 체크리스트**
- [ ] `WebSocketManager` 기본 클래스 생성
- [ ] 기존 `UpbitWebSocketQuotationClient` 활용 연동
- [ ] 연결 관리 (`connect`, `disconnect`) 구현
- [ ] 기본 구독 메서드 (`subscribe_ticker`) 구현
- [ ] 메시지 처리 파이프라인 구현
- [ ] 자동 재연결 로직 구현

#### **구현 가이드**
```python
# 핵심 구현 포인트
async def connect(self) -> bool:
    """WebSocket 연결 설정"""
    try:
        self._client = UpbitWebSocketQuotationClient()
        # 여기서 기존 클라이언트 초기화 로직 활용
        await self._client.connect()  # 기존 메서드 확인 필요
        self._is_connected = True
        self.logger.info("WebSocket 연결 성공")
        return True
    except Exception as e:
        self.logger.error(f"WebSocket 연결 실패: {e}")
        return False

async def subscribe_ticker(self, symbols: List[str]) -> Queue:
    """티커 데이터 구독"""
    if not self._is_connected:
        await self.connect()

    # 메시지 큐 생성
    queue = Queue()
    subscription_id = f"ticker_{hash(tuple(symbols))}"

    # 구독 요청 생성
    request = SubscriptionRequest(
        symbols=symbols,
        channel_type=ChannelType.TICKER,
        callback_queue=queue
    )

    self._subscriptions[subscription_id] = request

    # 실제 업비트 WebSocket 구독 (기존 클라이언트 활용)
    await self._client.subscribe_ticker(symbols)  # 기존 메서드 확인 필요

    return queue
```

---

### **🔥 2단계: MarketDataBackbone에 스트림 API 추가** (1일)
**파일**: `upbit_auto_trading/infrastructure/market_data_backbone/v2/market_data_backbone.py`

#### **추가할 메서드들**
```python
# MarketDataBackbone 클래스에 추가
async def stream_ticker(self, symbols: List[str]) -> AsyncGenerator[TickerData, None]:
    """실시간 티커 스트림"""
    if self._websocket_manager is None:
        self._websocket_manager = WebSocketManager()

    queue = await self._websocket_manager.subscribe_ticker(symbols)

    while True:
        try:
            # 큐에서 메시지 수신
            message = await asyncio.wait_for(queue.get(), timeout=30.0)

            # 메시지를 TickerData로 변환
            ticker_data = self._convert_websocket_ticker(message)

            yield ticker_data

        except asyncio.TimeoutError:
            self.logger.warning("WebSocket 메시지 타임아웃")
            continue
        except Exception as e:
            self.logger.error(f"스트림 처리 오류: {e}")
            break

async def stream_orderbook(self, symbols: List[str]) -> AsyncGenerator[OrderbookData, None]:
    """실시간 호가 스트림"""
    # 비슷한 구조로 구현
    pass

def _convert_websocket_ticker(self, raw_data: Dict) -> TickerData:
    """WebSocket 티커 데이터를 TickerData로 변환"""
    # WebSocket 포맷을 REST API 포맷으로 통일
    return TickerData(
        symbol=raw_data.get("code", ""),  # WebSocket: "code" vs REST: "market"
        current_price=float(raw_data.get("trade_price", 0)),
        change_rate=float(raw_data.get("signed_change_rate", 0)),
        change_price=float(raw_data.get("signed_change_price", 0)),
        volume_24h=float(raw_data.get("acc_trade_volume_24h", 0)),
        timestamp=raw_data.get("timestamp", 0),
        source="websocket"  # 데이터 소스 명시
    )
```

#### **구현 체크리스트**
- [ ] `stream_ticker()` 메서드 추가
- [ ] `stream_orderbook()` 메서드 추가
- [ ] WebSocket 데이터 변환 로직 구현
- [ ] 에러 처리 및 재연결 로직
- [ ] AsyncGenerator 패턴 구현

---

### **🔥 3단계: 지능적 채널 선택 로직** (0.5일)
**위치**: `MarketDataBackbone` 클래스 내부

#### **구현할 로직**
```python
class ChannelDecision(Enum):
    REST_ONLY = "rest_only"
    WEBSOCKET_ONLY = "websocket_only"
    AUTO = "auto"

def _choose_channel(self, request_type: str, symbols: List[str], options: Dict) -> ChannelDecision:
    """요청에 최적화된 채널 선택"""

    # 1. 명시적 채널 지정
    if options.get("force_channel"):
        return ChannelDecision(options["force_channel"])

    # 2. 요청 타입별 최적화
    if request_type == "get_ticker":
        # 단건 조회: REST가 더 효율적
        if len(symbols) == 1:
            return ChannelDecision.REST_ONLY
        # 다중 조회: WebSocket이 더 효율적
        else:
            return ChannelDecision.WEBSOCKET_ONLY

    elif request_type == "stream_ticker":
        # 스트림은 항상 WebSocket
        return ChannelDecision.WEBSOCKET_ONLY

    # 3. 기본값
    return ChannelDecision.AUTO

async def get_ticker(self, symbol: str, **options) -> TickerData:
    """채널 선택 로직이 적용된 티커 조회"""

    # 채널 결정
    decision = self._choose_channel("get_ticker", [symbol], options)

    if decision == ChannelDecision.REST_ONLY:
        return await self._get_ticker_rest(symbol)
    elif decision == ChannelDecision.WEBSOCKET_ONLY:
        return await self._get_ticker_websocket(symbol)
    else:
        # AUTO: REST 우선, 실패 시 WebSocket
        try:
            return await self._get_ticker_rest(symbol)
        except Exception:
            self.logger.warning(f"REST API 실패, WebSocket으로 대체: {symbol}")
            return await self._get_ticker_websocket(symbol)
```

#### **구현 체크리스트**
- [ ] `ChannelDecision` 열거형 정의
- [ ] `_choose_channel()` 로직 구현
- [ ] 기존 `get_ticker()` 메서드 업데이트
- [ ] 채널별 구현 메서드 분리
- [ ] 자동 대체 로직 구현

---

### **🔥 4단계: 포괄적 테스트 작성** (0.5일)
**파일**: `tests/infrastructure/market_data_backbone/v2/test_websocket_integration.py`

#### **테스트 시나리오**
```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from upbit_auto_trading.infrastructure.market_data_backbone.v2.market_data_backbone import MarketDataBackbone
from upbit_auto_trading.infrastructure.market_data_backbone.v2.websocket_manager import WebSocketManager

class TestWebSocketIntegration:

    @pytest.fixture
    async def backbone(self):
        """테스트용 MarketDataBackbone 인스턴스"""
        backbone = MarketDataBackbone()
        yield backbone
        await backbone.cleanup()  # 연결 정리

    @pytest.mark.asyncio
    async def test_websocket_manager_connection(self):
        """WebSocket 연결 테스트"""
        manager = WebSocketManager()

        # 연결 성공 테스트
        assert await manager.connect() is True
        assert manager._is_connected is True

        # 연결 해제 테스트
        await manager.disconnect()
        assert manager._is_connected is False

    @pytest.mark.asyncio
    async def test_stream_ticker_basic(self, backbone):
        """기본 티커 스트림 테스트"""
        symbols = ["KRW-BTC"]

        async for ticker in backbone.stream_ticker(symbols):
            # 첫 번째 메시지만 검증
            assert ticker.symbol == "KRW-BTC"
            assert ticker.current_price > 0
            assert ticker.source == "websocket"
            break  # 첫 메시지 후 중단

    @pytest.mark.asyncio
    async def test_channel_selection_logic(self, backbone):
        """채널 선택 로직 테스트"""

        # 단건 조회: REST 선택되어야 함
        ticker_rest = await backbone.get_ticker("KRW-BTC", force_channel="rest_only")
        assert ticker_rest.source == "rest"

        # 스트림: WebSocket 강제
        async for ticker_ws in backbone.stream_ticker(["KRW-BTC"]):
            assert ticker_ws.source == "websocket"
            break

    @pytest.mark.asyncio
    async def test_websocket_reconnection(self, backbone):
        """WebSocket 재연결 테스트"""
        # 연결 끊기 시뮬레이션
        # 자동 재연결 동작 검증
        pass

    @pytest.mark.asyncio
    async def test_multiple_symbol_stream(self, backbone):
        """다중 심볼 스트림 테스트"""
        symbols = ["KRW-BTC", "KRW-ETH"]

        received_symbols = set()
        count = 0

        async for ticker in backbone.stream_ticker(symbols):
            received_symbols.add(ticker.symbol)
            count += 1

            # 양쪽 심볼 모두 수신하거나 10개 메시지 후 중단
            if len(received_symbols) >= 2 or count >= 10:
                break

        assert len(received_symbols) >= 1  # 최소 1개 심볼은 수신
```

#### **테스트 체크리스트**
- [ ] WebSocket 연결/해제 테스트
- [ ] 기본 스트림 기능 테스트
- [ ] 채널 선택 로직 테스트
- [ ] 재연결 시나리오 테스트
- [ ] 다중 심볼 처리 테스트
- [ ] 에러 처리 테스트

---

## 📚 **참고할 기존 코드**

### **활용할 기존 클라이언트**
```python
# 이미 구현된 WebSocket 클라이언트
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import UpbitWebSocketQuotationClient

# 이미 구현된 REST 클라이언트
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_client import UpbitClient
```

### **기존 코드 분석 필요사항**
```powershell
# 기존 WebSocket 클라이언트 구조 파악
Get-Content "upbit_auto_trading/infrastructure/external_apis/upbit/upbit_websocket_quotation_client.py" | Select-String -Pattern "class|def|async def"

# 기존 WebSocket 서비스 레이어 확인
Get-Content "upbit_auto_trading/infrastructure/external_apis/upbit/services/websocket_market_data_service.py" | Select-String -Pattern "class|def|async def"
```

---

## 🧪 **검증 및 테스트 계획**

### **개발 중 지속적 검증**
```powershell
# 1. 개발 중 테스트 실행
pytest tests/infrastructure/market_data_backbone/v2/ -v -k websocket

# 2. 전체 테스트 확인 (기존 기능 무결성)
pytest tests/infrastructure/market_data_backbone/v2/ -v

# 3. 실제 API 연동 테스트
python -c "
import asyncio
from upbit_auto_trading.infrastructure.market_data_backbone.v2.market_data_backbone import MarketDataBackbone

async def test_stream():
    backbone = MarketDataBackbone()
    count = 0
    async for ticker in backbone.stream_ticker(['KRW-BTC']):
        print(f'{count}: {ticker.symbol} = {ticker.current_price:,.0f}원')
        count += 1
        if count >= 3:  # 3개 메시지만 확인
            break

asyncio.run(test_stream())
"
```

### **완성 후 통합 검증**
```powershell
# 시연 스크립트 업데이트 및 실행
python demonstrate_phase_1_2_websocket.py  # 새로 생성할 시연 스크립트
```

---

## 📋 **주의사항 및 고려사항**

### **DDD 아키텍처 준수**
- ✅ Infrastructure 계층에서만 외부 API 호출
- ✅ Domain 계층 순수성 유지 (WebSocket 의존성 없음)
- ✅ 의존성 주입으로 테스트 가능한 설계

### **업비트 API 제약사항**
- **연결 제한**: 최대 5개 동시 WebSocket 연결
- **메시지 빈도**: 초당 5건 제한
- **재연결**: 30초 백오프 정책
- **포맷 차이**: WebSocket과 REST의 필드명 차이 주의

### **성능 및 안정성**
- **메모리 관리**: Queue 크기 제한 설정
- **연결 모니터링**: Ping/Pong 메커니즘
- **장애 복구**: < 5초 내 재연결
- **에러 로깅**: Infrastructure 로깅 표준 준수

### **테스트 전략**
- **모킹**: 실제 WebSocket 연결은 선택적으로만
- **타임아웃**: 무한 대기 방지
- **정리**: 테스트 후 연결 해제 확실히
- **격리**: 테스트 간 상태 공유 방지

---

## 🎯 **성공 기준**

### **기능적 성공 기준**
- [ ] `backbone.stream_ticker(["KRW-BTC"])` 정상 동작
- [ ] 실시간 데이터 수신 (< 1초 지연)
- [ ] WebSocket 재연결 자동 복구
- [ ] 다중 심볼 동시 스트림 처리

### **품질적 성공 기준**
- [ ] 새 테스트 모두 통과 (추가 8-10개 테스트)
- [ ] 기존 테스트 모두 유지 (16/16 통과)
- [ ] 타입 힌트 100% 적용
- [ ] 로깅 표준 준수

### **성능적 성공 기준**
- [ ] 스트림 지연시간 < 1초
- [ ] 메모리 사용량 안정적
- [ ] 재연결 시간 < 5초
- [ ] CPU 사용률 < 5% (idle 시)

---

## 🚀 **시작하기**

### **즉시 시작 명령어**
```powershell
# 1. 작업 디렉토리로 이동
cd "d:\projects\upbit-autotrader-vscode"

# 2. 기존 시스템 상태 확인
python demonstrate_phase_1_1_success.py

# 3. WebSocketManager 클래스 생성 시작
New-Item -Path "upbit_auto_trading\infrastructure\market_data_backbone\v2\websocket_manager.py" -ItemType File

# 4. 에디터에서 websocket_manager.py 열기
code "upbit_auto_trading\infrastructure\market_data_backbone\v2\websocket_manager.py"
```

### **첫 번째 구현 목표** (오늘)
1. `WebSocketManager` 기본 클래스 구조 생성
2. 기존 `UpbitWebSocketQuotationClient` 연동
3. 기본 연결/해제 기능 구현
4. 간단한 테스트 작성 및 검증

### **첫 번째 검증** (오늘 말)
```python
# 목표: 이 코드가 동작해야 함
from upbit_auto_trading.infrastructure.market_data_backbone.v2.websocket_manager import WebSocketManager

async def test_basic():
    manager = WebSocketManager()
    success = await manager.connect()
    print(f"연결 성공: {success}")
    await manager.disconnect()

asyncio.run(test_basic())
```

---

## 💡 **코파일럿을 위한 팁**

### **효율적 개발 방법**
1. **기존 코드 활용**: `UpbitWebSocketQuotationClient` 완전 분석 후 시작
2. **점진적 구현**: 최소 기능부터 단계적 확장
3. **지속적 테스트**: 각 단계마다 검증 코드 실행
4. **문서 동기화**: 구현 완료 시 관련 문서 업데이트

### **막혔을 때 참고사항**
- **WebSocket 이슈**: 기존 클라이언트 구현 참조
- **데이터 포맷**: REST vs WebSocket 필드 매핑 확인
- **비동기 패턴**: 기존 `get_ticker()` 구현 참조
- **테스트 패턴**: 기존 테스트 파일 구조 따르기

**🎯 Phase 1.2 완성 시 MarketDataBackbone V2는 업비트 자동매매 시스템의 핵심 인프라가 됩니다!**

---

**📍 시작점**: WebSocketManager 클래스 구현
**🎯 목표**: 실시간 스트림 API 완성
**⏰ 일정**: 2-3일 집중 개발
**🔄 검증**: 매 단계 테스트 및 문서 업데이트
