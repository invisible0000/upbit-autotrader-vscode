#!/usr/bin/env python3
"""
컴포넌트 기반 조건 생성기 v4 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from components import ConditionDialog, ConditionStorage, ConditionLoader

def main():
    print("🚀 컴포넌트 기반 조건 생성기 v4 테스트 시작!")
    
    app = QApplication(sys.argv)
    
    try:
        # 조건 다이얼로그 생성
        print("📊 조건 다이얼로그 생성 중...")
        dialog = ConditionDialog()
        
        print("🎯 다이얼로그 표시!")
        result = dialog.exec()
        
        if result == dialog.DialogCode.Accepted:
            condition_data = dialog.get_condition_data()
            if condition_data:
                print("✅ 생성된 조건:")
                print(f"  - ID: {condition_data.get('id', 'N/A')}")
                print(f"  - 이름: {condition_data.get('name', 'N/A')}")
                print(f"  - 변수: {condition_data.get('variable_name', 'N/A')}")
                print(f"  - 연산자: {condition_data.get('operator', 'N/A')}")
                print(f"  - 비교값: {condition_data.get('target_value', 'N/A')}")
                
                # 저장된 조건 확인
                if condition_data.get('id'):
                    print("\n📊 데이터베이스 확인 중...")
                    storage = ConditionStorage()
                    stats = storage.get_condition_statistics()
                    print(f"  - 총 조건 수: {stats.get('total_conditions', 0)}")
                    print(f"  - 카테고리별 분포: {stats.get('category_distribution', {})}")
            else:
                print("❌ 조건 데이터를 가져올 수 없습니다.")
                
        else:
            print("❌ 조건 생성이 취소되었습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("🔚 테스트 완료!")

if __name__ == "__main__":
    main()
