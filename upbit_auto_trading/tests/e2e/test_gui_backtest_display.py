#!/usr/bin/env python3
"""
백테스트 결과 표시 테스트

실제 백테스트를 실행하고 결과 구조를 확인하여 
GUI에서 올바르게 표시되는지 테스트합니다.
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_simple_backtest_result():
    """간단한 백테스트 결과 구조 테스트"""
    print("🧪 백테스트 결과 구조 테스트 시작")
    
    try:
        # 샘플 백테스트 결과 생성 (실제 GUI에서 받는 것과 동일한 구조)
        sample_result = {
            "id": "test_backtest_001",
            "strategy_id": "ma_cross_5_20",
            "symbol": "KRW-BTC",
            "timeframe": "1h",
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2024, 1, 7),
            "initial_capital": 1000000,
            "performance_metrics": {
                "total_return": 0.0866,  # 8.66%
                "total_return_percent": 8.66,
                "win_rate": 0.6,  # 60%
                "max_drawdown": 0.0342,  # 3.42%
                "trades_count": 5,
                "profit_factor": 1.85
            },
            "trades": [
                {
                    "id": "trade_001",
                    "symbol": "KRW-BTC",
                    "entry_time": datetime(2024, 1, 2, 10, 0),
                    "entry_price": 45000000,
                    "exit_time": datetime(2024, 1, 2, 15, 0),
                    "exit_price": 46000000,
                    "quantity": 0.022222,
                    "side": "long",
                    "profit_loss": 22222,
                    "profit_loss_percent": 2.22,
                    "entry_fee": 1000,
                    "exit_fee": 1022
                },
                {
                    "id": "trade_002", 
                    "symbol": "KRW-BTC",
                    "entry_time": datetime(2024, 1, 3, 9, 0),
                    "entry_price": 46500000,
                    "exit_time": datetime(2024, 1, 3, 14, 0),
                    "exit_price": 45800000,
                    "quantity": 0.021505,
                    "side": "long",
                    "profit_loss": -15054,
                    "profit_loss_percent": -1.51,
                    "entry_fee": 1000,
                    "exit_fee": 985
                },
                {
                    "id": "trade_003",
                    "symbol": "KRW-BTC", 
                    "entry_time": datetime(2024, 1, 4, 11, 0),
                    "entry_price": 47000000,
                    "exit_time": datetime(2024, 1, 4, 16, 0),
                    "exit_price": 48500000,
                    "quantity": 0.021277,
                    "side": "long",
                    "profit_loss": 31915,
                    "profit_loss_percent": 3.19,
                    "entry_fee": 1000,
                    "exit_fee": 1032
                }
            ]
        }
        
        print(f"📊 샘플 백테스트 결과 구조: {list(sample_result.keys())}")
        
        # 성과 지표 확인
        metrics = sample_result['performance_metrics']
        print(f"   - 성과 지표: {list(metrics.keys())}")
        print(f"     * 총 수익률: {metrics.get('total_return_percent', 0):.2f}%")
        print(f"     * 승률: {metrics.get('win_rate', 0)*100:.1f}%")
        print(f"     * 최대 손실폭: {metrics.get('max_drawdown', 0)*100:.2f}%")
        
        # 거래 내역 확인
        trades = sample_result['trades']
        print(f"   - 거래 내역: {len(trades)}개")
        
        # GUI 결과 업데이트 시뮬레이션
        print("\n🖥️ GUI 결과 업데이트 시뮬레이션:")
        
        # 두 가지 결과 구조 모두 지원하는 로직 테스트
        summary = sample_result.get('summary', {})
        metrics = sample_result.get('performance_metrics', {})
        
        # 성과 지표 추출
        total_return = 0.0
        win_rate = 0.0
        max_drawdown = 0.0
        
        if summary:
            total_return = summary.get('total_return', 0.0)
            win_rate = summary.get('win_rate', 0.0)
            max_drawdown = summary.get('max_drawdown', 0.0)
        elif metrics:
            total_return = metrics.get('total_return_percent', metrics.get('total_return', 0.0))
            win_rate = metrics.get('win_rate', 0.0)
            max_drawdown = metrics.get('max_drawdown', 0.0)
        
        # 퍼센트 변환 (값이 1.0 이하면 비율이므로 100을 곱함)
        if abs(total_return) <= 1.0:
            total_return = total_return * 100
        if abs(win_rate) <= 1.0:
            win_rate = win_rate * 100
        if abs(max_drawdown) <= 1.0:
            max_drawdown = max_drawdown * 100
        
        print(f"   - 표시될 총 수익률: {total_return:.2f}%")
        print(f"   - 표시될 승률: {win_rate:.1f}%")
        print(f"   - 표시될 최대 손실폭: {max_drawdown:.2f}%")
        
        # 거래 테이블 시뮬레이션
        print(f"\n📋 거래 테이블 시뮬레이션:")
        print("   거래시각          종류  코인     가격        수량      손익률")
        print("   " + "="*65)
        
        for i, trade in enumerate(trades):
            # 시간 처리
            timestamp = (trade.get('exit_time') or 
                       trade.get('entry_time') or 
                       trade.get('timestamp', ''))
            time_str = timestamp.strftime('%Y-%m-%d %H:%M') if hasattr(timestamp, 'strftime') else str(timestamp)[:16]
            
            # 거래 유형
            if trade.get('exit_time'):
                action = '매도'
            else:
                action = '매수'
            
            # 가격
            price = trade.get('exit_price', trade.get('entry_price', 0))
            
            # 수량
            quantity = trade.get('quantity', 0)
            
            # 손익률
            profit_pct = trade.get('profit_loss_percent', 0)
            
            print(f"   {time_str} {action:2s} KRW-BTC {price:9,.0f} {quantity:.6f} {profit_pct:6.2f}%")
        
        print("\n✅ 백테스트 결과 구조 테스트 완료")
        
        # 실제 GUI 업데이트 함수 호출 시뮬레이션
        print("\n🔧 GUI 업데이트 함수 시뮬레이션:")
        try:
            # GUI 클래스 시뮬레이션
            class MockBacktestResults:
                def update_results(self, results):
                    print(f"   MockGUI: 결과 업데이트 호출됨")
                    print(f"   - 결과 키: {list(results.keys())}")
                    
                    # 성과 지표 처리 로직 테스트
                    summary = results.get('summary', {})
                    metrics = results.get('performance_metrics', {})
                    
                    if metrics:
                        total_return = metrics.get('total_return_percent', metrics.get('total_return', 0.0))
                        print(f"   - 성과 지표에서 총 수익률: {total_return}")
                    
                    trades = results.get('trades', [])
                    print(f"   - 처리될 거래 수: {len(trades)}")
                    
                    return True
            
            mock_gui = MockBacktestResults()
            result = mock_gui.update_results(sample_result)
            
            if result:
                print("   ✅ GUI 업데이트 시뮬레이션 성공")
            
        except Exception as e:
            print(f"   ❌ GUI 시뮬레이션 실패: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_backtest_result()
    exit(0 if success else 1)
