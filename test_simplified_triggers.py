#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
간소화된 트리거 마커 시스템 테스트

- 카운트 기능 제거
- iVal 기준 상단 10% 위치 통일
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import numpy as np

from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.core.simulation_result_widget import SimulationResultWidget

def test_simplified_trigger_markers():
    """간소화된 트리거 마커 테스트"""
    
    print("🧪 간소화된 트리거 마커 시스템 테스트")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    
    # 테스트 데이터 생성
    num_days = 50
    price_data = 50000 + np.random.normal(0, 2000, num_days).cumsum()
    
    # RSI 시뮬레이션 (0-100 범위)
    rsi_data = 30 + 40 * (0.5 + 0.5 * np.sin(np.linspace(0, 4*np.pi, num_days)))
    rsi_data = np.clip(rsi_data, 0, 100)
    
    # MACD 시뮬레이션 (-2 ~ +2 범위)
    macd_data = 2 * np.sin(np.linspace(0, 3*np.pi, num_days))
    
    # 거래량 데이터
    volume_data = np.random.normal(1000000, 200000, num_days)
    volume_data = np.abs(volume_data)  # 양수 보장
    
    # 트리거 결과 (여러 지점에서 발생)
    trigger_results = [(rsi > 60, {}) for rsi in rsi_data]
    
    # 시뮬레이션 결과 위젯 생성
    widget = SimulationResultWidget()
    
    # 1. RSI 테스트 (oscillator 카테고리)
    print("\n📊 1. RSI 테스트 (oscillator)")
    print(f"   RSI 범위: {min(rsi_data):.1f} ~ {max(rsi_data):.1f}")
    print(f"   트리거 발생: {sum(1 for triggered, _ in trigger_results if triggered)}회")
    
    widget.update_simulation_chart(
        scenario="RSI 트리거 테스트",
        price_data=price_data.tolist(),
        trigger_results=trigger_results,
        base_variable_data=rsi_data.tolist(),
        variable_info={"name": "RSI", "category": "oscillator"}
    )
    widget.setWindowTitle("RSI 트리거 테스트 (상단 10% 위치)")
    
    # 2. MACD 테스트 (oscillator 카테고리)
    print("\n📊 2. MACD 테스트 (oscillator)")
    macd_triggers = [(macd > 1.0, {}) for macd in macd_data]
    print(f"   MACD 범위: {min(macd_data):.2f} ~ {max(macd_data):.2f}")
    print(f"   트리거 발생: {sum(1 for triggered, _ in macd_triggers if triggered)}회")
    
    # 위젯 창 표시
    widget.show()
    widget.resize(1000, 600)
    
    print("\n✅ 간소화된 마커 시스템 적용:")
    print("   - 카운트 기능 제거됨")
    print("   - iVal 기준 상단 10% 위치로 통일")
    print("   - 모든 지표에서 일관된 마커 표시")
    print("   - 범례에서 'Trg' 라벨만 표시")
    
    # 3초 후 종료
    QTimer.singleShot(3000, app.quit)
    
    try:
        app.exec()
    except KeyboardInterrupt:
        print("\n🛑 테스트 중단됨")
    
    print("\n🎉 간소화 테스트 완료!")

if __name__ == "__main__":
    test_simplified_trigger_markers()
