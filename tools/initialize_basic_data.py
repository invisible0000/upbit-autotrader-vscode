"""
기본 마켓 데이터 초기화
"""
import sqlite3
from pathlib import Path

def initialize_basic_data():
    """기본 마켓 심볼과 타임프레임 데이터 초기화"""
    db_path = Path("data/market_data.sqlite3")

    # 기본 KRW 마켓 심볼들
    krw_symbols = [
        ("KRW-BTC", "BTC", "KRW", "비트코인", "Bitcoin"),
        ("KRW-ETH", "ETH", "KRW", "이더리움", "Ethereum"),
        ("KRW-XRP", "XRP", "KRW", "리플", "Ripple"),
        ("KRW-ADA", "ADA", "KRW", "에이다", "Cardano"),
        ("KRW-DOT", "DOT", "KRW", "폴카닷", "Polkadot"),
    ]

    with sqlite3.connect(db_path) as conn:
        print("📋 기본 마켓 심볼 추가 중...")

        # 마켓 심볼 삽입
        for symbol_data in krw_symbols:
            conn.execute("""
                INSERT OR REPLACE INTO market_symbols
                (symbol, base_currency, quote_currency, display_name_ko, display_name_en)
                VALUES (?, ?, ?, ?, ?)
            """, symbol_data)
            print(f"  ✅ {symbol_data[0]} ({symbol_data[3]}) 추가됨")

        print("\n⏰ 타임프레임 데이터 확인 중...")

        # 타임프레임 데이터 확인
        cursor = conn.execute("SELECT timeframe, display_name FROM timeframes ORDER BY sort_order")
        timeframes = cursor.fetchall()

        for tf in timeframes:
            print(f"  ⏱️ {tf[0]} ({tf[1]}) 사용 가능")

        conn.commit()
        print("\n✅ 기본 데이터 초기화 완료!")

if __name__ == "__main__":
    initialize_basic_data()
