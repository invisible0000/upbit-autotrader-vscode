#!/usr/bin/env python3
"""잔고와 최근 주문 상태 확인"""

import asyncio
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_private_client import create_upbit_private_client
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient


async def check_status():
    private_client = create_upbit_private_client()
    public_client = UpbitPublicClient()

    try:
        # 현재가와 호가 정보 확인
        print('=== 현재가와 호가 정보 ===')

        # 현재가 조회
        ticker = await public_client.get_ticker('KRW-BTC')
        current_price = ticker['KRW-BTC']['trade_price']
        print(f'현재가: {current_price:,}원')

        # 호가 조회
        orderbook = await public_client.get_orderbook('KRW-BTC')
        btc_orderbook = orderbook['KRW-BTC']

        print('\n=== 매수/매도 호가 비교 ===')
        print('매수 호가 (bid - 사려는 가격):')
        for i, unit in enumerate(btc_orderbook['orderbook_units'][:5]):
            bid_price = int(unit['bid_price'])
            print(f'  {i + 1}위: {bid_price:,}원')

        print('\n매도 호가 (ask - 팔려는 가격):')
        for i, unit in enumerate(btc_orderbook['orderbook_units'][:5]):
            ask_price = int(unit['ask_price'])
            print(f'  {i + 1}위: {ask_price:,}원')        # 30호가 확인 (있다면)
        if len(btc_orderbook['orderbook_units']) >= 30:
            bid_30 = int(btc_orderbook['orderbook_units'][29]['bid_price'])
            ask_30 = int(btc_orderbook['orderbook_units'][29]['ask_price'])
            print(f'\n30호가: 매수 {bid_30:,}원, 매도 {ask_30:,}원')
        else:
            print(f'\n호가 개수: {len(btc_orderbook["orderbook_units"])}개 (30호가 없음)')

        # 계좌 잔고 확인
        print('\n=== 계좌 잔고 ===')
        accounts = await private_client.get_accounts()
        print(f'계좌 정보 타입: {type(accounts)}')
        for currency, info in accounts.items():
            balance = float(info['balance'])
            if balance > 0:
                if currency == 'KRW':
                    print(f'{currency}: {balance:,.2f}원')
                else:
                    avg_price = float(info.get('avg_buy_price', 0))
                    value = balance * current_price if currency == 'BTC' else 0
                    print(f'{currency}: {balance:.8f} (평균단가: {avg_price:,.0f}원, 현재가치: {value:,.0f}원)')

        # 최근 종료 주문 확인 (다양한 방법으로)
        print('\n=== 최근 종료 주문 확인 ===')

        # 방법 1: 모든 종료 주문
        print('1. 모든 종료 주문:')
        all_closed = await private_client.get_closed_orders(limit=5)
        print(f'  타입: {type(all_closed)}, 개수: {len(all_closed)}')

        # 방법 2: KRW-BTC 종료 주문
        print('2. KRW-BTC 종료 주문:')
        btc_closed = await private_client.get_closed_orders(market='KRW-BTC', limit=5)
        print(f'  타입: {type(btc_closed)}, 개수: {len(btc_closed)}')

        # 방법 3: 체결된 주문 (done 상태)
        print('3. 체결된 주문:')
        done_orders = await private_client.get_closed_orders(market='KRW-BTC', state='done', limit=5)
        print(f'  타입: {type(done_orders)}, 개수: {len(done_orders)}')

        # 실제 주문 내용 출력
        if all_closed:
            print('\n=== 최근 주문 상세 ===')
            for i, (order_id, order) in enumerate(list(all_closed.items())[:3]):
                print(f'{i + 1}. UUID: {order_id[:8]}...')
                print(f'   마켓: {order.get("market", "N/A")}')
                print(f'   측: {order.get("side", "N/A")} (bid=매수, ask=매도)')
                print(f'   가격: {order.get("price", "N/A")}원')
                print(f'   수량: {order.get("volume", "N/A")}')
                print(f'   상태: {order.get("state", "N/A")}')
                print(f'   생성시간: {order.get("created_at", "N/A")}')
                print()

    finally:
        await private_client.close()


if __name__ == "__main__":
    asyncio.run(check_status())
