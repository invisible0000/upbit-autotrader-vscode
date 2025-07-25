"""
간단한 데이터 소스 선택 UI 테스트
버튼 크기 조정 후 확인
"""

import sys
import os

def test_ui_display():
    """UI 표시 테스트"""
    try:
        # PyQt6 애플리케이션 생성
        from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
        
        app = QApplication(sys.argv)
        
        # 메인 윈도우 생성
        main_window = QMainWindow()
        main_window.setWindowTitle("UI 크기 조정 테스트")
        main_window.setGeometry(100, 100, 1200, 700)  # 화면 크기 조정
        
        # 중앙 위젯
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # 상태 정보 라벨
        status_label = QLabel("📊 데이터 소스 선택 UI 크기 조정 테스트\n버튼 크기와 폰트를 줄여서 화면에 맞게 조정했습니다.")
        status_label.setStyleSheet("""
            background-color: #e3f2fd;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            color: #0277bd;
            margin-bottom: 10px;
        """)
        layout.addWidget(status_label)
        
        try:
            # 통합 조건 관리 시스템 추가
            from upbit_auto_trading.ui.desktop.screens.strategy_management.integrated_condition_manager import IntegratedConditionManager
            condition_manager = IntegratedConditionManager()
            layout.addWidget(condition_manager)
            
            print("✅ 통합 조건 관리 시스템 로드 성공")
            
        except Exception as e:
            print(f"❌ 통합 조건 관리 시스템 로드 실패: {e}")
            
            # 에러 표시 라벨
            error_label = QLabel(f"❌ 로드 실패: {e}")
            error_label.setStyleSheet("""
                background-color: #ffebee;
                padding: 20px;
                border-radius: 5px;
                font-size: 12px;
                color: #c62828;
            """)
            layout.addWidget(error_label)
        
        main_window.setCentralWidget(central_widget)
        
        # 윈도우 표시
        main_window.show()
        
        print("🚀 UI 테스트 시작")
        print("📏 버튼 크기와 폰트가 조정되어 화면에 잘 맞는지 확인하세요")
        print("📊 데이터 소스 선택 위젯이 우측 상단에 표시됩니다")
        print("⚠️ 데이터 소스 목록이 비어있을 수 있지만 UI 레이아웃은 확인 가능합니다")
        
        # 이벤트 루프 실행
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ UI 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🎯 데이터 소스 선택 UI 크기 조정 테스트")
    print("=" * 50)
    
    test_ui_display()
