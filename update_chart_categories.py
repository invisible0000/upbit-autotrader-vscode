#!/usr/bin/env python3
"""기존 조건들의 차트 카테고리 자동 업데이트"""

import sys
import os
import sqlite3
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent))

# trigger_builder 컴포넌트 경로 추가
trigger_builder_path = r"d:\projects\upbit-autotrader-vscode\upbit_auto_trading\ui\desktop\screens\strategy_management\trigger_builder\components"
if trigger_builder_path not in sys.path:
    sys.path.insert(0, trigger_builder_path)

from variable_definitions import VariableDefinitions

def update_chart_categories():
    """기존 조건들의 차트 카테고리 자동 업데이트"""
    print("🔧 기존 조건들의 차트 카테고리 자동 업데이트")
    print("=" * 50)
    
    db_path = "data/app_settings.sqlite3"
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 1. 모든 조건 조회
            cursor.execute("SELECT id, name, variable_id FROM trading_conditions")
            conditions = cursor.fetchall()
            
            print(f"📊 총 {len(conditions)}개 조건 발견")
            
            updated_count = 0
            for condition_id, name, variable_id in conditions:
                # 차트 카테고리 결정
                chart_category = VariableDefinitions.get_chart_category(variable_id)
                
                # 업데이트
                cursor.execute("""
                    UPDATE trading_conditions 
                    SET chart_category = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (chart_category, condition_id))
                
                updated_count += 1
                indicator_type = "🔗" if chart_category == "overlay" else "📊"
                print(f"   {indicator_type} '{name}' ({variable_id}) → {chart_category}")
            
            conn.commit()
            print(f"\n✅ {updated_count}개 조건의 차트 카테고리 업데이트 완료")
            
            # 2. 결과 확인
            cursor.execute("""
                SELECT chart_category, COUNT(*) as count 
                FROM trading_conditions 
                GROUP BY chart_category
            """)
            category_stats = cursor.fetchall()
            
            print("\n📊 차트 카테고리 분포:")
            for category, count in category_stats:
                emoji = "🔗" if category == "overlay" else "📊"
                print(f"   {emoji} {category}: {count}개")
                
    except Exception as e:
        print(f"❌ 업데이트 실패: {e}")

if __name__ == "__main__":
    update_chart_categories()
