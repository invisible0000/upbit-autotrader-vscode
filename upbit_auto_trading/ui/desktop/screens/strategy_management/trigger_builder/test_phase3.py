#!/usr/bin/env python3
"""
Phase 3 검증 테스트 - simulation_engines.py
"""

import sys
import os

# 경로 설정
sys.path.append('components/shared')

try:
    from components.shared.simulation_engines import BaseSimulationEngine
    import pandas as pd
    import numpy as np
    
    print("✅ simulation_engines import 성공")
    
    # BaseSimulationEngine 인스턴스 생성
    engine = BaseSimulationEngine()
    print(f"✅ BaseSimulationEngine 인스턴스 생성 성공")
    print(f"   TriggerCalculator 사용 가능: {engine.trigger_calculator is not None}")
    
    # 테스트 데이터 생성
    test_prices = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107, 109])
    print(f"✅ 테스트 데이터 생성 완료: {len(test_prices)}개 데이터")
    
    # RSI 테스트
    try:
        rsi_result = engine._calculate_rsi(test_prices, period=5)
        print(f"✅ RSI 계산 성공: {type(rsi_result)}, 길이: {len(rsi_result)}")
        print(f"   RSI 값 샘플: {rsi_result.iloc[:3].tolist()}")
    except Exception as e:
        print(f"❌ RSI 테스트 실패: {e}")
    
    # MACD 테스트
    try:
        macd_result = engine._calculate_macd(test_prices)
        print(f"✅ MACD 계산 성공: {type(macd_result)}, 길이: {len(macd_result)}")
        print(f"   MACD 값 샘플: {macd_result.iloc[:3].tolist()}")
    except Exception as e:
        print(f"❌ MACD 테스트 실패: {e}")
    
    print("\n✅ Phase 3 기본 검증 완료")
    
except ImportError as e:
    print(f"❌ Import 오류: {e}")
except Exception as e:
    print(f"❌ 예상치 못한 오류: {e}")
