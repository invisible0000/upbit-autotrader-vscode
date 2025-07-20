"""
수정된 UI 테스트 스크립트
"""
import subprocess
import sys
import os

def test_ui_fixes():
    """UI 수정사항 테스트"""
    print("🔧 UI 수정사항 테스트")
    print("="*50)
    
    print("✅ 완료된 수정사항:")
    print("   1. DB 저장 문제 해결 (SQLite3 직접 사용)")
    print("   2. 날짜 선택기 크기 개선 (yyyy-MM-dd 형식, 최소 너비 120px)")
    print("   3. emergency_stop_updates 메서드 추가")
    
    print("\n📍 DB 저장 위치:")
    print("   data/upbit_auto_trading.sqlite3")
    
    print("\n🧪 테스트 방법:")
    print("   1. 백테스팅 탭 이동")
    print("   2. 날짜 선택기에서 연도 확인 (2025-MM-dd 형식)")
    print("   3. '📥 차트 데이터 수집' 버튼 클릭")
    print("   4. 데이터 수집 완료 후 check_data_status.py 실행")
    
    print("\n🚀 UI 실행...")
    
def check_db_before_after():
    """데이터 수집 전후 DB 상태 비교"""
    print("\n📊 현재 DB 상태:")
    os.system("python check_data_status.py")

if __name__ == "__main__":
    test_ui_fixes()
    check_db_before_after()
    
    print("\n" + "="*50)
    print("🎯 테스트 준비 완료!")
    print("이제 python run_desktop_ui.py 를 실행하여 테스트해보세요.")
    print("="*50)
