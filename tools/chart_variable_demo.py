#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
차트 변수 카테고리 시스템 데모

새로운 차트 변수 카테고리 시스템의 기능을 테스트하는 데모 스크립트
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

try:
    from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.chart_variable_service import (
        get_chart_variable_service
    )
    from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.chart_rendering_engine import (
        get_chart_rendering_engine
    )
except ImportError as e:
    print(f"❌ 모듈 임포트 실패: {e}")
    print("프로젝트 루트에서 실행해주세요.")
    sys.exit(1)


class ChartVariableDemo:
    """차트 변수 카테고리 시스템 데모 클래스"""

    def __init__(self):
        self.service = get_chart_variable_service()
        self.renderer = get_chart_rendering_engine()

    def run_demo(self):
        """데모 실행"""
        print("🚀 차트 변수 카테고리 시스템 데모 시작")
        print("=" * 60)

        # 1. 등록된 변수 목록 확인
        self.demo_variable_registry()

        # 2. 변수 호환성 테스트
        self.demo_compatibility_check()

        # 3. 차트 레이아웃 생성 테스트
        self.demo_chart_layout()

        # 4. 실제 차트 렌더링 테스트
        self.demo_chart_rendering()

        # 5. 사용 통계 확인
        self.demo_usage_statistics()

        print("✅ 데모 완료!")

    def demo_variable_registry(self):
        """변수 레지스트리 데모"""
        print("\n📊 1. 등록된 변수 목록")
        print("-" * 40)

        # 모든 변수 조회
        all_variables = self.service.get_available_variables_by_category()
        
        categories = {}
        for var in all_variables:
            if var.category not in categories:
                categories[var.category] = []
            categories[var.category].append(var)

        for category, vars_in_cat in categories.items():
            print(f"\n📂 {category.upper()} 카테고리:")
            for var in vars_in_cat:
                print(f"  - {var.variable_name} ({var.variable_id})")
                print(f"    표시방식: {var.display_type}, 단위: {var.unit}")
                if var.scale_min is not None and var.scale_max is not None:
                    print(f"    스케일: {var.scale_min} ~ {var.scale_max}")

    def demo_compatibility_check(self):
        """호환성 검사 데모"""
        print("\n🔗 2. 변수 호환성 검사")
        print("-" * 40)

        test_cases = [
            ('rsi', 'stochastic'),  # 같은 오실레이터 계열
            ('current_price', 'moving_average'),  # 같은 가격 오버레이
            ('rsi', 'macd'),  # 다른 카테고리 (호환 불가)
            ('current_price', 'volume'),  # 완전 다른 카테고리
        ]

        for base_var, external_var in test_cases:
            is_compatible, reason = self.service.is_compatible_external_variable(
                base_var, external_var
            )
            
            status = "✅ 호환" if is_compatible else "❌ 불호환"
            print(f"{status} {base_var} ↔ {external_var}")
            print(f"    이유: {reason}")

    def demo_chart_layout(self):
        """차트 레이아웃 생성 데모"""
        print("\n🎨 3. 차트 레이아웃 생성")
        print("-" * 40)

        # 다양한 변수 조합으로 레이아웃 테스트
        test_combinations = [
            ['current_price', 'moving_average'],  # 메인 차트만
            ['rsi'],  # 서브플롯만
            ['current_price', 'moving_average', 'rsi', 'macd'],  # 복합
            ['current_price', 'rsi', 'macd', 'volume', 'stochastic'],  # 복잡한 조합
        ]

        for i, variables in enumerate(test_combinations, 1):
            print(f"\n📋 조합 {i}: {', '.join(variables)}")
            
            layout_info = self.service.get_chart_layout_info(variables)
            
            print(f"  메인 차트 변수: {len(layout_info.main_chart_variables)}개")
            for var in layout_info.main_chart_variables:
                print(f"    - {var['name']} ({var['config'].display_type})")
            
            print(f"  서브플롯: {len(layout_info.subplots)}개")
            for subplot in layout_info.subplots:
                print(f"    - {subplot['name']} ({subplot['config'].display_type})")
            
            print(f"  높이 비율: {[f'{r:.2f}' for r in layout_info.height_ratios]}")
            
            # 조합 유효성 검사
            is_valid, warnings = self.service.validate_variable_combination(variables)
            if not is_valid:
                print(f"  ⚠️ 경고:")
                for warning in warnings:
                    print(f"    - {warning}")

    def demo_chart_rendering(self):
        """차트 렌더링 데모"""
        print("\n📈 4. 차트 렌더링 테스트")
        print("-" * 40)

        # 샘플 데이터 생성
        sample_data = self._generate_sample_data()
        print(f"샘플 데이터 생성: {len(sample_data)} 행")

        # 변수 설정
        variable_configs = [
            {
                'variable_id': 'current_price',
                'name': '현재가',
                'target_value': '50000',  # 5만원 레벨
                'parameters': {}
            },
            {
                'variable_id': 'moving_average',
                'name': '이동평균',
                'parameters': {'period': 20}
            },
            {
                'variable_id': 'rsi',
                'name': 'RSI',
                'parameters': {'period': 14}
            },
            {
                'variable_id': 'macd',
                'name': 'MACD',
                'parameters': {'fast': 12, 'slow': 26, 'signal': 9}
            }
        ]

        try:
            # 차트 렌더링
            fig = self.renderer.render_chart(
                data=sample_data,
                variable_configs=variable_configs,
                template_name='standard_trading'
            )
            
            print("✅ 차트 렌더링 성공")
            print(f"  - 트레이스 수: {len(fig.data)}")
            print(f"  - 서브플롯 수: {len(fig._get_subplot_rows())}")
            
            # HTML 파일로 저장 (선택적)
            output_file = "demo_chart.html"
            fig.write_html(output_file)
            print(f"  - 차트 저장: {output_file}")
            
        except Exception as e:
            print(f"❌ 차트 렌더링 실패: {e}")

    def demo_usage_statistics(self):
        """사용 통계 데모"""
        print("\n📊 5. 사용 통계")
        print("-" * 40)

        # 각 변수별 사용 통계 조회
        test_variables = ['rsi', 'macd', 'current_price', 'moving_average']
        
        for var_id in test_variables:
            stats = self.service.get_usage_statistics(var_id, days=30)
            print(f"\n📈 {var_id} 사용 통계 (최근 30일):")
            print(f"  - 총 사용 횟수: {stats['usage_count']}")
            print(f"  - 평균 렌더링 시간: {stats['avg_render_time_ms']}ms")
            
            if stats['context_distribution']:
                print(f"  - 컨텍스트별 사용:")
                for context, count in stats['context_distribution'].items():
                    print(f"    * {context}: {count}회")

    def _generate_sample_data(self, days: int = 100) -> pd.DataFrame:
        """샘플 시계열 데이터 생성"""
        # 시간 인덱스 생성
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        timestamps = pd.date_range(start=start_date, end=end_date, freq='1H')
        
        # 가격 데이터 생성 (랜덤워크)
        np.random.seed(42)  # 재현 가능한 결과를 위해
        
        initial_price = 45000
        price_changes = np.random.normal(0, 500, len(timestamps))  # 평균 0, 표준편차 500
        prices = initial_price + np.cumsum(price_changes)
        
        # OHLC 데이터 생성
        data = []
        for i, (timestamp, close) in enumerate(zip(timestamps, prices)):
            # 간단한 OHLC 로직
            volatility = np.random.uniform(0.005, 0.02)  # 0.5% ~ 2% 변동성
            
            high = close * (1 + volatility * np.random.uniform(0, 1))
            low = close * (1 - volatility * np.random.uniform(0, 1))
            
            if i == 0:
                open_price = close
            else:
                open_price = prices[i-1]
            
            volume = np.random.uniform(1000000, 5000000)  # 백만~오백만 거래량
            
            data.append({
                'timestamp': timestamp,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        return pd.DataFrame(data)


def main():
    """메인 실행 함수"""
    try:
        demo = ChartVariableDemo()
        demo.run_demo()
        
    except Exception as e:
        print(f"❌ 데모 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    main()
