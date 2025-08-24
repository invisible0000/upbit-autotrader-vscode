#!/usr/bin/env python3
"""잔고와 최근 주문 상태 확인"""

import asyncio
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_private_client import create_upbit_private_client

async def check_status():
    client = create_upbit_private_client()

    try:
        # 계좌 잔고 확인
        print('=== 계좌 잔고 ===')
        accounts = await client.get_accounts()
        print(f'계좌 정보 타입: {type(accounts)}')
        print(f'계좌 정보: {accounts}')

        # 최근 종료 주문 확인
        print('\n=== 최근 종료 주문 (최근 5개) ===')
        closed_orders = await client.get_closed_orders(market='KRW-BTC', limit=5)
        print(f'종료 주문 타입: {type(closed_orders)}')
        print(f'종료 주문: {closed_orders}')

    finally:
        await client.close()if __name__ == "__main__":
    asyncio.run(check_status())
