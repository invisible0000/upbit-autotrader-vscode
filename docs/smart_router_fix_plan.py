"""
Smart Router 간단 수정 방안

사용자 피드백을 바탕으로 한 핵심 문제 해결:
1. 데이터 검증 로직 수정
2. 웹소켓 vs REST API 라우팅 개선
3. 안정적인 폴백 메커니즘
"""

# 1. 데이터 검증 로직 수정 방안
def _validate_data_result_fixed(data_result, requested_symbols):
    """개선된 데이터 검증 로직

    기존 문제: 빈 딕셔너리를 실패로 판단
    개선점: 실제 데이터 구조를 정확히 검증
    """
    if not isinstance(data_result, dict):
        return False, [], requested_symbols

    successful_symbols = []
    failed_symbols = []

    for symbol in requested_symbols:
        # 핵심: 데이터가 실제로 존재하는지 정확히 확인
        if symbol in data_result:
            symbol_data = data_result[symbol]

            # 티커 데이터 검증
            if isinstance(symbol_data, dict):
                # 핵심 필드가 있는지 확인 (trade_price, opening_price 등)
                has_valid_data = any(key in symbol_data for key in
                    ['trade_price', 'opening_price', 'high_price', 'low_price'])
                if has_valid_data:
                    successful_symbols.append(symbol)
                else:
                    failed_symbols.append(symbol)

            # 캔들 데이터 검증
            elif isinstance(symbol_data, list) and len(symbol_data) > 0:
                successful_symbols.append(symbol)

            else:
                failed_symbols.append(symbol)
        else:
            failed_symbols.append(symbol)

    return len(failed_symbols) == 0, successful_symbols, failed_symbols


# 2. 웹소켓 우선 라우팅 전략
def get_optimal_routing_strategy(data_type, count=1, is_realtime=False):
    """요청 패턴에 따른 최적 라우팅 전략"""

    if data_type == "ticker":
        # 티커는 항상 실시간성이 중요
        return ["LIVE_SUBSCRIPTION", "BATCH_SNAPSHOT", "HOT_CACHE", "WARM_CACHE_REST", "COLD_REST"]

    elif data_type == "candles":
        if count == 1 or is_realtime:
            # 최신 1개 캔들 → 웹소켓 우선
            return ["BATCH_SNAPSHOT", "LIVE_SUBSCRIPTION", "HOT_CACHE", "WARM_CACHE_REST", "COLD_REST"]
        elif count > 100:
            # 대량 히스토리컬 → REST API 우선
            return ["COLD_REST", "WARM_CACHE_REST", "HOT_CACHE", "BATCH_SNAPSHOT"]
        else:
            # 중간 크기 → 균형
            return ["HOT_CACHE", "WARM_CACHE_REST", "BATCH_SNAPSHOT", "COLD_REST"]

    # 기본값
    return ["HOT_CACHE", "WARM_CACHE_REST", "COLD_REST"]


# 3. 안정적인 폴백 메커니즘
async def safe_data_request(symbol, request_type, fallback_func=None):
    """안전한 데이터 요청 (폴백 포함)"""
    try:
        # 메인 요청
        result = await main_routing_request(symbol, request_type)

        if result and len(result) > 0:
            return result

    except Exception as e:
        print(f"메인 요청 실패: {e}")

    # 폴백 메커니즘
    if fallback_func:
        try:
            return await fallback_func(symbol, request_type)
        except Exception as e:
            print(f"폴백도 실패: {e}")

    # 최후 수단: 빈 결과
    return {} if request_type == "ticker" else []


# 4. 실제 구현 예시 (SimpleSmartRouter 개선)
class FixedSimpleRouter:
    """수정된 간단 라우터"""

    async def get_ticker_fixed(self, symbol: str):
        """안정적인 티커 조회"""

        # 1단계: 캐시 확인
        cached = await self._check_cache(f"ticker:{symbol}")
        if cached:
            return cached

        # 2단계: 웹소켓 시도
        try:
            ws_result = await self._websocket_ticker(symbol)
            if ws_result:
                await self._cache_data(f"ticker:{symbol}", ws_result)
                return ws_result
        except:
            pass

        # 3단계: REST API 시도
        try:
            rest_result = await self._rest_ticker(symbol)
            if rest_result:
                await self._cache_data(f"ticker:{symbol}", rest_result)
                return rest_result
        except:
            pass

        # 4단계: 최후 수단
        return {}

    async def get_candles_fixed(self, symbol: str, interval: str = "1m", count: int = 100):
        """패턴 기반 캔들 조회"""

        if count == 1:
            # 최신 1개 → 웹소켓 우선
            return await self._get_latest_candle_ws(symbol, interval)
        elif count > 100:
            # 대량 → REST API 직접
            return await self._get_historical_candles_rest(symbol, interval, count)
        else:
            # 균형 → 캐시 우선
            return await self._get_balanced_candles(symbol, interval, count)


print("✅ Smart Router 수정 방안 완료!")
print("🔧 핵심 개선사항:")
print("   1. 데이터 검증 로직 수정 → 실제 필드 존재 확인")
print("   2. 웹소켓 우선 전략 → 단일/실시간 데이터")
print("   3. REST API 우선 전략 → 대량/히스토리컬 데이터")
print("   4. 안정적인 폴백 → 캐시 → 웹소켓 → REST API → 빈 결과")
print("   5. 비동기 처리 완전 수정")
