#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
차트 변수 서비스 간단 테스트

plotly 없이 차트 변수 카테고리 시스템의 핵심 기능만 테스트
"""

import sqlite3
import json
import sys
import os

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)


class SimpleChartVariableTest:
    """간단한 차트 변수 서비스 테스트"""

    def __init__(self):
        self.db_path = "data/app_settings.sqlite3"

    def test_database_setup(self):
        """데이터베이스 설정 테스트"""
        print("🔍 데이터베이스 테이블 확인")
        print("-" * 40)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 테이블 목록 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            chart_tables = [
                'chart_variables',
                'variable_compatibility_rules',
                'chart_layout_templates',
                'variable_usage_logs'
            ]
            
            for table in chart_tables:
                if table in tables:
                    print(f"✅ {table} 테이블 존재")
                    
                    # 테이블 데이터 수 확인
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   데이터 수: {count}개")
                else:
                    print(f"❌ {table} 테이블 없음")

    def test_variables(self):
        """등록된 변수 확인"""
        print("\n📊 등록된 변수 목록")
        print("-" * 40)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT variable_id, variable_name, category, display_type, 
                       scale_min, scale_max, unit, default_color
                FROM chart_variables
                WHERE is_active = 1
                ORDER BY category, variable_name
            """)
            
            current_category = None
            for row in cursor.fetchall():
                var_id, name, category, display_type, scale_min, scale_max, unit, color = row
                
                if category != current_category:
                    print(f"\n📂 {category.upper()} 카테고리:")
                    current_category = category
                
                print(f"  - {name} ({var_id})")
                print(f"    표시: {display_type}, 단위: {unit}, 색상: {color}")
                
                if scale_min is not None and scale_max is not None:
                    print(f"    스케일: {scale_min} ~ {scale_max}")

    def test_compatibility_rules(self):
        """호환성 규칙 테스트"""
        print("\n🔗 호환성 규칙 확인")
        print("-" * 40)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT cr.base_variable_id, cv.variable_name, cr.compatible_category, 
                       cr.compatibility_reason
                FROM variable_compatibility_rules cr
                JOIN chart_variables cv ON cr.base_variable_id = cv.variable_id
                ORDER BY cr.base_variable_id, cr.compatible_category
            """)
            
            current_base = None
            for row in cursor.fetchall():
                base_id, base_name, compatible_cat, reason = row
                
                if base_id != current_base:
                    print(f"\n🎯 {base_name} ({base_id}) 호환 카테고리:")
                    current_base = base_id
                
                print(f"  - {compatible_cat}")
                if reason:
                    print(f"    이유: {reason}")

    def test_layout_templates(self):
        """레이아웃 템플릿 테스트"""
        print("\n🎨 레이아웃 템플릿 확인")
        print("-" * 40)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT template_name, description, main_chart_height_ratio, 
                       subplot_configurations, color_palette, is_default
                FROM chart_layout_templates
                ORDER BY is_default DESC, template_name
            """)
            
            for row in cursor.fetchall():
                name, desc, main_ratio, subplot_configs, colors, is_default = row
                
                status = "🌟 기본" if is_default else "📋 일반"
                print(f"\n{status} {name}")
                if desc:
                    print(f"  설명: {desc}")
                print(f"  메인 차트 비율: {main_ratio}")
                
                if subplot_configs:
                    configs = json.loads(subplot_configs)
                    if configs:
                        print(f"  서브플롯 설정:")
                        for var_id, config in configs.items():
                            print(f"    - {var_id}: 높이비율 {config.get('height_ratio', 0.3)}, "
                                  f"위치 {config.get('position', 1)}")
                
                if colors:
                    palette = json.loads(colors)
                    print(f"  색상 팔레트: {len(palette)}개 색상 정의됨")

    def test_chart_layout_logic(self):
        """차트 레이아웃 로직 테스트"""
        print("\n🔧 차트 레이아웃 로직 테스트")
        print("-" * 40)

        # 테스트 케이스들
        test_cases = [
            {
                'name': '메인 차트만',
                'variables': ['current_price', 'moving_average']
            },
            {
                'name': '서브플롯만',
                'variables': ['rsi']
            },
            {
                'name': '혼합',
                'variables': ['current_price', 'moving_average', 'rsi', 'macd']
            },
            {
                'name': '복잡한 조합',
                'variables': ['current_price', 'bollinger_band', 'rsi', 'macd', 'volume']
            }
        ]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for case in test_cases:
                print(f"\n📋 {case['name']}: {', '.join(case['variables'])}")
                
                main_chart_vars = []
                subplots = []
                
                for var_id in case['variables']:
                    cursor.execute("""
                        SELECT variable_name, category, display_type, subplot_height_ratio
                        FROM chart_variables
                        WHERE variable_id = ? AND is_active = 1
                    """, (var_id,))
                    
                    result = cursor.fetchone()
                    if result:
                        name, category, display_type, height_ratio = result
                        
                        if category == 'price_overlay':
                            main_chart_vars.append({'name': name, 'type': display_type})
                        else:
                            subplots.append({
                                'name': name, 
                                'type': display_type, 
                                'height_ratio': height_ratio
                            })
                
                print(f"  메인 차트 변수: {len(main_chart_vars)}개")
                for var in main_chart_vars:
                    print(f"    - {var['name']} ({var['type']})")
                
                print(f"  서브플롯: {len(subplots)}개")
                for subplot in subplots:
                    print(f"    - {subplot['name']} ({subplot['type']}, "
                          f"높이비율: {subplot['height_ratio']})")
                
                # 높이 비율 계산
                if subplots:
                    main_ratio = 0.6
                    remaining = 0.4
                    total_subplot_ratio = sum(s['height_ratio'] for s in subplots)
                    
                    if total_subplot_ratio > 0:
                        ratios = [main_ratio]
                        for subplot in subplots:
                            subplot_ratio = (subplot['height_ratio'] / total_subplot_ratio) * remaining
                            ratios.append(subplot_ratio)
                        
                        print(f"  높이 비율: {[f'{r:.3f}' for r in ratios]}")

    def test_compatibility_check(self):
        """호환성 검사 테스트"""
        print("\n🔍 호환성 검사 테스트")
        print("-" * 40)

        test_pairs = [
            ('rsi', 'stochastic'),  # 같은 오실레이터
            ('current_price', 'moving_average'),  # 같은 가격 오버레이
            ('rsi', 'macd'),  # 다른 카테고리
            ('current_price', 'volume'),  # 완전 다른 카테고리
        ]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for base_var, ext_var in test_pairs:
                # 기본 변수 정보
                cursor.execute("""
                    SELECT variable_name, category, compatible_categories
                    FROM chart_variables
                    WHERE variable_id = ?
                """, (base_var,))
                base_result = cursor.fetchone()
                
                # 외부 변수 정보
                cursor.execute("""
                    SELECT variable_name, category
                    FROM chart_variables
                    WHERE variable_id = ?
                """, (ext_var,))
                ext_result = cursor.fetchone()
                
                if base_result and ext_result:
                    base_name, base_category, compatible_cats_json = base_result
                    ext_name, ext_category = ext_result
                    
                    compatible_cats = json.loads(compatible_cats_json) if compatible_cats_json else []
                    is_compatible = ext_category in compatible_cats
                    
                    status = "✅ 호환" if is_compatible else "❌ 불호환"
                    print(f"{status} {base_name}({base_category}) ↔ {ext_name}({ext_category})")
                    
                    if is_compatible:
                        print(f"    {base_category}는 {ext_category}와 호환됩니다.")
                    else:
                        print(f"    {base_category}는 {ext_category}와 호환되지 않습니다.")

    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 차트 변수 카테고리 시스템 테스트 시작")
        print("=" * 60)

        try:
            self.test_database_setup()
            self.test_variables()
            self.test_compatibility_rules()
            self.test_layout_templates()
            self.test_chart_layout_logic()
            self.test_compatibility_check()
            
            print("\n✅ 모든 테스트 완료!")
            
        except Exception as e:
            print(f"\n❌ 테스트 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()


def main():
    """메인 실행 함수"""
    if not os.path.exists("data/app_settings.sqlite3"):
        print("❌ 데이터베이스 파일을 찾을 수 없습니다.")
        print("먼저 chart_variable_migration.py를 실행해주세요.")
        return
    
    test = SimpleChartVariableTest()
    test.run_all_tests()


if __name__ == "__main__":
    main()
