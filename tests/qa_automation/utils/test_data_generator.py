"""
테스트 데이터 생성기 모듈

이 모듈은 업비트 자동매매 시스템의 GUI 자동화 테스트를 위한 테스트 데이터를 생성합니다.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os


def generate_ohlcv_data(rows=100, save_to_file=True):
    """
    OHLCV 데이터 생성
    
    Args:
        rows (int): 생성할 데이터 행 수
        save_to_file (bool): 파일로 저장할지 여부
    
    Returns:
        pandas.DataFrame: 생성된 OHLCV 데이터
    """
    print(f"OHLCV 데이터 {rows}행 생성 중...")
    
    # 시작 날짜 설정
    start_date = datetime.now() - timedelta(days=rows)
    
    # 날짜 인덱스 생성
    dates = [start_date + timedelta(days=i) for i in range(rows)]
    
    # 시드 설정으로 재현 가능한 랜덤 데이터 생성
    np.random.seed(42)
    
    # 초기 가격 설정
    base_price = 50000.0
    
    # 가격 변동 생성
    changes = np.random.normal(0, 1000, rows)
    
    # OHLCV 데이터 생성
    data = []
    current_price = base_price
    
    for i in range(rows):
        # 당일 변동폭
        daily_change = changes[i]
        daily_volatility = abs(daily_change) * 0.5
        
        # OHLCV 계산
        open_price = current_price
        close_price = current_price + daily_change
        high_price = max(open_price, close_price) + np.random.uniform(0, daily_volatility)
        low_price = min(open_price, close_price) - np.random.uniform(0, daily_volatility)
        volume = np.random.uniform(1000, 10000)
        
        # 데이터 추가
        data.append({
            'timestamp': dates[i],
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
        
        # 다음 봉의 시가는 현재 봉의 종가
        current_price = close_price
    
    # DataFrame 생성
    df = pd.DataFrame(data)
    
    # 파일로 저장
    if save_to_file:
        file_path = os.path.join("sample_QA_Automation", "test_data", "mock_ohlcv_data.csv")
        df.to_csv(file_path, index=False)
        print(f"OHLCV 데이터가 {file_path}에 저장되었습니다.")
    
    return df


def generate_trades_data(count=10, save_to_file=True):
    """
    거래 데이터 생성
    
    Args:
        count (int): 생성할 거래 수
        save_to_file (bool): 파일로 저장할지 여부
    
    Returns:
        pandas.DataFrame: 생성된 거래 데이터
    """
    print(f"거래 데이터 {count}개 생성 중...")
    
    # 시작 날짜 설정
    start_date = datetime.now() - timedelta(days=90)
    
    # 시드 설정으로 재현 가능한 랜덤 데이터 생성
    np.random.seed(42)
    
    # 거래 데이터 생성
    trades = []
    
    for i in range(count):
        # 랜덤 날짜 (최근 90일 내)
        trade_date = start_date + timedelta(days=np.random.randint(0, 90))
        
        # 매수/매도 여부
        trade_type = "buy" if i % 2 == 0 else "sell"
        
        # 가격 및 수량
        price = np.random.uniform(40000, 60000)
        quantity = np.random.uniform(0.1, 1.0)
        
        # 거래 데이터 추가
        trades.append({
            'timestamp': trade_date,
            'type': trade_type,
            'price': price,
            'quantity': quantity,
            'total': price * quantity
        })
    
    # DataFrame 생성
    df = pd.DataFrame(trades)
    
    # 파일로 저장
    if save_to_file:
        file_path = os.path.join("sample_QA_Automation", "test_data", "mock_trades_data.csv")
        df.to_csv(file_path, index=False)
        print(f"거래 데이터가 {file_path}에 저장되었습니다.")
    
    return df


def generate_portfolio_data(save_to_file=True):
    """
    포트폴리오 데이터 생성
    
    Args:
        save_to_file (bool): 파일로 저장할지 여부
    
    Returns:
        dict: 생성된 포트폴리오 데이터
    """
    print("포트폴리오 데이터 생성 중...")
    
    # 시드 설정으로 재현 가능한 랜덤 데이터 생성
    np.random.seed(42)
    
    # 포트폴리오 데이터 생성
    portfolio = {
        'total_value': np.random.uniform(10000000, 20000000),
        'profit_loss': np.random.uniform(-1000000, 2000000),
        'profit_loss_percent': np.random.uniform(-10, 20),
        'assets': []
    }
    
    # 자산 데이터 생성
    coins = ['BTC', 'ETH', 'XRP', 'ADA', 'SOL', 'DOT', 'DOGE', 'AVAX', 'MATIC', 'LINK']
    total_allocation = 0
    
    for coin in coins:
        # 할당 비율 (총합이 100%가 되도록)
        if coin == coins[-1]:
            allocation = 100 - total_allocation
        else:
            allocation = np.random.randint(5, 20)
            total_allocation += allocation
        
        # 수익/손실
        profit_loss = np.random.uniform(-20, 30)
        
        # 자산 추가
        portfolio['assets'].append({
            'coin': coin,
            'allocation': allocation,
            'value': portfolio['total_value'] * allocation / 100,
            'profit_loss': profit_loss,
            'price': np.random.uniform(100, 50000),
            'quantity': np.random.uniform(0.1, 10)
        })
    
    # 파일로 저장
    if save_to_file:
        file_path = os.path.join("sample_QA_Automation", "test_data", "mock_portfolio_data.json")
        import json
        with open(file_path, 'w') as f:
            json.dump(portfolio, f, indent=4)
        print(f"포트폴리오 데이터가 {file_path}에 저장되었습니다.")
    
    return portfolio


def generate_market_data(count=20, save_to_file=True):
    """
    시장 데이터 생성
    
    Args:
        count (int): 생성할 코인 수
        save_to_file (bool): 파일로 저장할지 여부
    
    Returns:
        pandas.DataFrame: 생성된 시장 데이터
    """
    print(f"시장 데이터 {count}개 생성 중...")
    
    # 시드 설정으로 재현 가능한 랜덤 데이터 생성
    np.random.seed(42)
    
    # 코인 목록
    coins = ['BTC', 'ETH', 'XRP', 'ADA', 'SOL', 'DOT', 'DOGE', 'AVAX', 'MATIC', 'LINK',
             'UNI', 'ATOM', 'LTC', 'ALGO', 'XLM', 'FIL', 'VET', 'THETA', 'TRX', 'EOS',
             'AAVE', 'XTZ', 'EGLD', 'XMR', 'CAKE', 'NEO', 'COMP', 'DASH', 'ZEC', 'WAVES']
    
    # 시장 데이터 생성
    market_data = []
    
    for i in range(min(count, len(coins))):
        # 가격
        price = np.random.uniform(100, 50000)
        
        # 24시간 변동
        change_24h = np.random.uniform(-10, 10)
        
        # 거래량
        volume_24h = np.random.uniform(1000000, 100000000)
        
        # 시가총액
        market_cap = np.random.uniform(10000000, 1000000000000)
        
        # 시장 데이터 추가
        market_data.append({
            'coin': coins[i],
            'price': price,
            'change_24h': change_24h,
            'volume_24h': volume_24h,
            'market_cap': market_cap
        })
    
    # DataFrame 생성
    df = pd.DataFrame(market_data)
    
    # 파일로 저장
    if save_to_file:
        file_path = os.path.join("sample_QA_Automation", "test_data", "mock_market_data.csv")
        df.to_csv(file_path, index=False)
        print(f"시장 데이터가 {file_path}에 저장되었습니다.")
    
    return df


def generate_all_test_data():
    """모든 테스트 데이터 생성"""
    generate_ohlcv_data()
    generate_trades_data()
    generate_portfolio_data()
    generate_market_data()
    print("모든 테스트 데이터가 생성되었습니다.")


if __name__ == "__main__":
    generate_all_test_data()