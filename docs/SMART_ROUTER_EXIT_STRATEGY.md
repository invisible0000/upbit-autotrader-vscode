# 🚨 스마트 라우터 출구 전략 (Exit Strategy)

## 🎯 목적

**실거래 시스템 생존성 확보**: 스마트 라우터 장애 시 즉시 기본 클라이언트로 폴백하여 거래 중단 방지

## ⚡ 긴급 상황 시나리오

### 🔥 레벨 1: 스마트 라우터 부분 장애
- 채널 선택 오류
- 데이터 포맷 통합 실패
- WebSocket 연결 불안정

### 🚨 레벨 2: 스마트 라우터 완전 장애
- 초기화 실패
- 메모리 누수/크래시
- 복구 불가능한 오류

### 💀 레벨 3: 마켓 데이터 백본 전체 장애
- 스마트 라우터 + 백본 시스템 동시 장애
- 실거래 데이터 공급 중단 위기

## 🛡️ 출구 전략 구현

### 1단계: 폴백 감지 시스템

```python
class MarketDataFallbackManager:
    """마켓 데이터 폴백 관리자"""

    def __init__(self):
        self.smart_router_enabled = True
        self.fallback_active = False
        self.failure_count = 0
        self.last_success_time = datetime.now()

        # 기본 클라이언트 (항상 준비)
        self.upbit_public_client = UpbitPublicClient()
        self.upbit_websocket_client = UpbitWebSocketQuotationClient()

    async def health_check(self) -> bool:
        """스마트 라우터 상태 점검"""
        try:
            # 스마트 라우터 기본 기능 테스트
            test_result = await self.smart_router.get_ticker(["KRW-BTC"])
            if test_result.get('success'):
                self.failure_count = 0
                self.last_success_time = datetime.now()
                return True
            else:
                self.failure_count += 1
                return False

        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"스마트 라우터 상태 점검 실패: {e}")
            return False

    async def should_fallback(self) -> bool:
        """폴백 실행 여부 판단"""
        # 연속 실패 3회 또는 5분간 성공 없음
        if self.failure_count >= 3:
            return True
        if (datetime.now() - self.last_success_time).seconds > 300:
            return True
        return False
```

### 2단계: 직접 클라이언트 폴백

```python
class DirectClientFallback:
    """직접 클라이언트 폴백 구현"""

    def __init__(self):
        self.public_client = UpbitPublicClient()
        self.websocket_client = UpbitWebSocketQuotationClient()
        self.logger = create_component_logger("DirectFallback")

    async def get_ticker_fallback(self, symbols: List[str]) -> Dict[str, Any]:
        """티커 데이터 직접 조회 폴백"""
        try:
            # REST API 직접 호출
            markets = ",".join(symbols)
            data = await self.public_client.get_ticker(markets)

            return {
                "success": True,
                "data": data,
                "source": "direct_rest_fallback"
            }
        except Exception as e:
            self.logger.error(f"티커 폴백 실패: {e}")
            return {"success": False, "error": str(e)}

    async def get_candles_fallback(self, symbols: List[str],
                                 interval: str, count: int = 1,
                                 to: Optional[str] = None) -> Dict[str, Any]:
        """캔들 데이터 직접 조회 폴백"""
        try:
            results = []

            for symbol in symbols:
                if interval.endswith('m'):
                    unit = int(interval[:-1])
                    data = await self.public_client.get_candles_minutes(
                        symbol, unit=unit, count=count, to=to
                    )
                elif interval == '1d':
                    data = await self.public_client.get_candles_days(
                        symbol, count=count, to=to
                    )
                else:
                    raise ValueError(f"지원하지 않는 간격: {interval}")

                results.extend(data)

            return {
                "success": True,
                "data": results,
                "source": "direct_rest_fallback"
            }
        except Exception as e:
            self.logger.error(f"캔들 폴백 실패: {e}")
            return {"success": False, "error": str(e)}

    async def get_trades_fallback(self, symbols: List[str],
                                count: int = 1) -> Dict[str, Any]:
        """체결 데이터 직접 조회 폴백"""
        try:
            results = []

            for symbol in symbols:
                data = await self.public_client.get_ticks(symbol, count=count)
                results.extend(data)

            return {
                "success": True,
                "data": results,
                "source": "direct_rest_fallback"
            }
        except Exception as e:
            self.logger.error(f"체결 폴백 실패: {e}")
            return {"success": False, "error": str(e)}
```

### 3단계: 실시간 데이터 폴백

```python
class RealtimeDataFallback:
    """실시간 데이터 폴백 (WebSocket 직접 사용)"""

    def __init__(self):
        self.websocket_client = UpbitWebSocketQuotationClient()
        self.subscription_cache = {}

    async def setup_realtime_fallback(self, symbols: List[str]):
        """실시간 폴백 설정"""
        try:
            await self.websocket_client.connect()

            # 티커 구독
            await self.websocket_client.subscribe_ticker(symbols)

            # 캔들 구독 (1분봉)
            await self.websocket_client.subscribe_candle(symbols, "1m")

            # 체결 구독
            await self.websocket_client.subscribe_trades(symbols)

            self.logger.info(f"실시간 폴백 설정 완료: {symbols}")
            return True

        except Exception as e:
            self.logger.error(f"실시간 폴백 설정 실패: {e}")
            return False

    async def get_cached_data(self, data_type: str, symbol: str) -> Optional[Dict]:
        """캐시된 실시간 데이터 조회"""
        cache_key = f"{data_type}:{symbol}"
        return self.subscription_cache.get(cache_key)
```

## 🔄 통합 폴백 시스템

### 마스터 폴백 매니저

```python
class MasterFallbackSystem:
    """마스터 폴백 시스템 - 모든 출구 전략 통합"""

    def __init__(self):
        self.smart_router = None  # 초기에는 None
        self.fallback_manager = MarketDataFallbackManager()
        self.direct_fallback = DirectClientFallback()
        self.realtime_fallback = RealtimeDataFallback()
        self.fallback_active = False

    async def initialize(self):
        """시스템 초기화 - 스마트 라우터 우선, 실패 시 폴백"""
        try:
            # 1순위: 스마트 라우터 시도
            from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing import SmartRouter
            self.smart_router = SmartRouter()
            await self.smart_router.initialize()
            self.logger.info("✅ 스마트 라우터 초기화 성공")

        except Exception as e:
            self.logger.warning(f"⚠️ 스마트 라우터 초기화 실패, 폴백 모드로 전환: {e}")
            await self._activate_fallback()

    async def get_ticker(self, symbols: List[str]) -> Dict[str, Any]:
        """티커 조회 - 폴백 지원"""
        if not self.fallback_active and self.smart_router:
            try:
                result = await self.smart_router.get_ticker(symbols)
                if result.get('success'):
                    return result
                else:
                    # 스마트 라우터 실패 시 즉시 폴백
                    await self._activate_fallback()
            except Exception:
                await self._activate_fallback()

        # 폴백 모드 실행
        return await self.direct_fallback.get_ticker_fallback(symbols)

    async def get_candles(self, symbols: List[str], interval: str,
                         count: int = 1, to: Optional[str] = None) -> Dict[str, Any]:
        """캔들 조회 - 폴백 지원"""
        if not self.fallback_active and self.smart_router:
            try:
                result = await self.smart_router.get_candles(
                    symbols, interval=interval, count=count, to=to
                )
                if result.get('success'):
                    return result
                else:
                    await self._activate_fallback()
            except Exception:
                await self._activate_fallback()

        # 폴백 모드 실행
        return await self.direct_fallback.get_candles_fallback(
            symbols, interval, count, to
        )

    async def _activate_fallback(self):
        """폴백 모드 활성화"""
        if not self.fallback_active:
            self.fallback_active = True
            self.logger.warning("🚨 폴백 모드 활성화 - 직접 클라이언트 사용")

            # 실시간 데이터 폴백 설정
            await self.realtime_fallback.setup_realtime_fallback(["KRW-BTC"])
```

## 📋 출구 전략 실행 가이드

### Phase 1: 즉시 대응 (0-30초)
```python
# 1. 스마트 라우터 상태 점검
health_ok = await fallback_system.health_check()

# 2. 실패 시 즉시 폴백 활성화
if not health_ok:
    await fallback_system._activate_fallback()

# 3. 핵심 데이터 확보 (거래 지속)
ticker_data = await fallback_system.get_ticker(["KRW-BTC"])
```

### Phase 2: 안정화 (30초-5분)
```python
# 1. 실시간 데이터 폴백 설정
await realtime_fallback.setup_realtime_fallback(trading_symbols)

# 2. 캐시 데이터 확보
for symbol in trading_symbols:
    cached_ticker = await realtime_fallback.get_cached_data("ticker", symbol)

# 3. 모니터링 강화
await start_intensive_monitoring()
```

### Phase 3: 복구 시도 (5분 이후)
```python
# 1. 주기적 스마트 라우터 복구 시도
async def recovery_attempt():
    try:
        await smart_router.initialize()
        test_result = await smart_router.get_ticker(["KRW-BTC"])
        if test_result.get('success'):
            fallback_system.fallback_active = False
            logger.info("✅ 스마트 라우터 복구 완료")
            return True
    except:
        logger.info("⏳ 스마트 라우터 복구 중...")
        return False

# 2. 5분마다 복구 시도
while fallback_active:
    await asyncio.sleep(300)  # 5분 대기
    if await recovery_attempt():
        break
```

## 🚨 긴급 대응 체크리스트

### ✅ 즉시 확인 사항
- [ ] 기본 클라이언트 연결 상태
- [ ] 핵심 심볼 데이터 수신 여부
- [ ] Rate Limit 상태
- [ ] 메모리/CPU 사용량

### ⚡ 즉시 실행 사항
- [ ] 폴백 모드 활성화
- [ ] 실시간 구독 재설정
- [ ] 로그 레벨 상승 (ERROR → DEBUG)
- [ ] 알림 발송 (관리자)

### 🔧 점검 대상
- [ ] 네트워크 연결
- [ ] API 키 유효성
- [ ] 외부 의존성 상태
- [ ] 디스크 공간

## 💡 예방 조치

### 정기 점검
```python
# 매일 자정 스마트 라우터 상태 점검
async def daily_health_check():
    systems = ["smart_router", "rest_client", "websocket_client"]
    for system in systems:
        health = await check_system_health(system)
        if not health:
            await send_alert(f"{system} 상태 이상")
```

### 성능 모니터링
```python
# 실시간 성능 지표 추적
metrics = {
    "api_success_rate": 0.95,  # 95% 이상 유지
    "response_time": 1000,     # 1초 이내
    "error_count": 0           # 에러 최소화
}
```

## 🎯 결론

**출구 전략 핵심 원칙**:

1. **예측 가능성**: 장애 시나리오 사전 정의
2. **자동화**: 수동 개입 없이 자동 폴백
3. **투명성**: 폴백 상태 명확한 로깅
4. **복구 능력**: 자동 복구 시도
5. **최후 수단**: 직접 클라이언트 항상 준비

**실거래에서는 100% 가용성이 생명**입니다. 스마트 라우터는 편의 기능이고, 기본 클라이언트가 진짜 생명줄입니다.
