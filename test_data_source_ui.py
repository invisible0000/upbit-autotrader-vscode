"""
데이터 소스 선택 UI 통합 테스트
"""

import sys
import os
import sqlite3
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_data_source_ui():
    """데이터 소스 선택 UI 테스트"""
    try:
        # PyQt6 애플리케이션 생성
        from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
        
        app = QApplication(sys.argv)
        
        # 메인 윈도우 생성
        main_window = QMainWindow()
        main_window.setWindowTitle("데이터 소스 선택 UI 테스트")
        main_window.setGeometry(100, 100, 1200, 800)
        
        # 중앙 위젯
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # 통합 조건 관리 시스템 추가
        from upbit_auto_trading.ui.desktop.screens.strategy_management.integrated_condition_manager import IntegratedConditionManager
        condition_manager = IntegratedConditionManager()
        layout.addWidget(condition_manager)
        
        main_window.setCentralWidget(central_widget)
        
        # 윈도우 표시
        main_window.show()
        
        print("✅ 데이터 소스 선택 UI 테스트 시작")
        print("📊 데이터 소스 선택 위젯이 우측 상단에 표시됨")
        print("🔄 다양한 데이터 소스를 선택하여 성능 차이를 확인해보세요")
        
        # 이벤트 루프 실행
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ UI 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

def check_data_source_availability():
    """데이터 소스 가용성 확인"""
    print("📊 데이터 소스 가용성 확인 중...")
    
    try:
        from upbit_auto_trading.ui.desktop.screens.strategy_management.data_source_manager import get_data_source_manager
        
        manager = get_data_source_manager()
        sources = manager.get_available_sources()
        
        print(f"✅ 사용 가능한 데이터 소스: {len(sources)}개")
        
        for source_key, source_info in sources.items():
            print(f"  🔹 {source_key}: {source_info['name']}")
            print(f"     성능: {source_info['performance']}")
            print(f"     품질: {source_info['quality']}")
            print(f"     추천: {'예' if source_info.get('recommended', False) else '아니오'}")
        
        # 현재 사용자 선호도 확인
        preference = manager.get_user_preference()
        print(f"📍 현재 사용자 선호도: {preference}")
        
    except Exception as e:
        print(f"❌ 데이터 소스 확인 실패: {e}")

def check_db_existence():
    """데이터베이스 존재 여부 확인"""
    db_path = "data/market_data.sqlite3"
    
    if os.path.exists(db_path):
        print(f"✅ 데이터베이스 존재: {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 테이블 존재 확인
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='krw_btc_daily'
            """)
            
            if cursor.fetchone():
                # 레코드 수 확인
                cursor.execute("SELECT COUNT(*) FROM krw_btc_daily")
                count = cursor.fetchone()[0]
                print(f"📊 KRW-BTC 일간 데이터: {count:,}개 레코드")
            else:
                print("⚠️ krw_btc_daily 테이블이 없음")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ DB 확인 실패: {e}")
    else:
        print(f"⚠️ 데이터베이스 없음: {db_path}")

if __name__ == "__main__":
    print("🚀 데이터 소스 선택 UI 통합 테스트")
    print("=" * 50)
    
    # 1. 데이터베이스 확인
    check_db_existence()
    print()
    
    # 2. 데이터 소스 가용성 확인
    check_data_source_availability()
    print()
    
    # 3. UI 테스트 실행
    test_data_source_ui()
