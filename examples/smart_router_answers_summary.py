"""
🎯 Smart Router 질문 답변 요약

사용자 질문에 대한 핵심 답변만 정리
"""

# ====================================================================
# 답변 1: 호가는 어떻게 요청하나요?
# ====================================================================

"""
✅ 호가 요청 방법:

from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.upbit_data_provider import UpbitDataProvider

# 방법 1: 단일 심볼
provider = UpbitDataProvider()
await provider.start()
result = await provider.get_orderbook_data(['KRW-BTC'])
orderbook = result['data']['KRW-BTC']

# 방법 2: 다중 심볼
symbols = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']
result = await provider.get_orderbook_data(symbols)
for symbol, orderbook in result['data'].items():
    print(f"{symbol} 호가: {len(orderbook['orderbook_units'])}단계")
"""

# ====================================================================
# 답변 2: 차트용 2000개 캔들 데이터는 어떻게?
# ====================================================================

"""
✅ 대용량 차트 데이터 (2000개) 수집 방법:

async def get_chart_data_2000(router, symbol, interval='5m'):
    all_candles = []
    batch_size = 200  # 업비트 API 제한
    total_batches = 2000 // batch_size  # 10배치

    for batch in range(total_batches):
        candles = await router.get_candles(symbol, interval, batch_size)
        all_candles.extend(candles)
        await asyncio.sleep(0.1)  # Rate limit 준수

    return all_candles

# 사용법
router = SimpleSmartRouter()
await router.start()
chart_data = await get_chart_data_2000(router, 'KRW-BTC', '5m')
print(f"차트 데이터: {len(chart_data)}개 캔들")
"""

# ====================================================================
# 답변 3: KRW 티커 여러값들을 동시에 불러오기
# ====================================================================

"""
✅ KRW 티커 다중 심볼 동시 조회:

import asyncio

# KRW 마켓 주요 심볼들
krw_symbols = [
    'KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA',
    'KRW-DOT', 'KRW-SOL', 'KRW-AVAX', 'KRW-MATIC'
]

# 병렬 비동기 처리
async def get_multiple_krw_tickers(router, symbols):
    tasks = [router.get_ticker(symbol) for symbol in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    tickers = {}
    success_count = 0
    for symbol, result in zip(symbols, results):
        if not isinstance(result, Exception) and result:
            tickers[symbol] = result
            success_count += 1

    return tickers, success_count

# 사용법
tickers, count = await get_multiple_krw_tickers(router, krw_symbols)
print(f"조회 성공: {count}/{len(krw_symbols)}")

for symbol, data in tickers.items():
    price = data.get('trade_price', 0)
    change = data.get('signed_change_rate', 0)
    print(f"{symbol}: ₩{price:,} ({change:+.2%})")
"""

# ====================================================================
# 답변 4: 모든게 동시에 이루어지면 어떻게 사용?
# ====================================================================

"""
✅ 통합 트레이딩 시스템 구조:

async def integrated_trading_system():
    router = SimpleSmartRouter()
    provider = UpbitDataProvider()
    await router.start()
    await provider.start()

    try:
        # 1단계: 초기 데이터 수집 (병렬)
        tasks = {
            'tickers': get_multiple_krw_tickers(router, krw_symbols),
            'orderbooks': provider.get_orderbook_data(symbols[:5]),
            'charts': get_chart_data_2000(router, 'KRW-BTC', '5m')
        }

        results = await asyncio.gather(*tasks.values())
        print("초기 데이터 수집 완료")

        # 2단계: 실시간 모니터링 루프
        while True:
            # 빠른 업데이트 (티커만)
            tickers, count = await get_multiple_krw_tickers(router, core_symbols)

            # 분석 및 표시
            analyze_and_display(tickers)

            # 주기적으로 호가 업데이트 (5초마다)
            if cycle % 5 == 0:
                orderbooks = await provider.get_orderbook_data(core_symbols)

            await asyncio.sleep(1.0)

    finally:
        await router.stop()
        await provider.stop()

# 핵심 구조:
# - 초기 수집: 대용량 데이터는 한번만
# - 실시간: 티커는 1초마다, 호가는 5초마다
# - 병렬 처리: asyncio.gather() 활용
# - 에러 처리: Exception 체크
"""

# ====================================================================
# 🔥 실전 사용 템플릿
# ====================================================================

import asyncio
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.simple_smart_router import SimpleSmartRouter
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.upbit_data_provider import UpbitDataProvider

async def trading_system_template():
    """실전 사용 템플릿"""

    # 시스템 초기화
    router = SimpleSmartRouter()
    provider = UpbitDataProvider()
    await router.start()
    await provider.start()

    # 모니터링할 심볼들
    symbols = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA', 'KRW-DOT']

    try:
        # 1. 차트 데이터 수집 (한번만)
        print("📊 차트 데이터 수집 중...")
        chart_data = []
        for i in range(10):  # 2000개 → 10배치 * 200개
            candles = await router.get_candles('KRW-BTC', '5m', 200)
            chart_data.extend(candles)
            await asyncio.sleep(0.1)
        print(f"차트 데이터: {len(chart_data)}개 수집")

        # 2. 실시간 모니터링
        print("📡 실시간 모니터링 시작...")
        for cycle in range(10):  # 10초간 테스트

            # 티커 조회 (병렬)
            tasks = [router.get_ticker(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            success = 0
            for symbol, result in zip(symbols, results):
                if not isinstance(result, Exception) and result:
                    success += 1
                    if success <= 3:  # 상위 3개만 출력
                        price = result.get('trade_price', 0)
                        change = result.get('signed_change_rate', 0)
                        print(f"💰 {symbol}: ₩{price:,} ({change:+.2%})")

            # 주기적 호가 업데이트
            if cycle % 5 == 0:
                orderbooks = await provider.get_orderbook_data(symbols[:3])
                if orderbooks:
                    print(f"📈 호가 업데이트: {len(orderbooks)}개")

            await asyncio.sleep(1.0)

    finally:
        await router.stop()
        await provider.stop()

if __name__ == "__main__":
    print("🚀 실전 트레이딩 시스템 템플릿")
    asyncio.run(trading_system_template())
