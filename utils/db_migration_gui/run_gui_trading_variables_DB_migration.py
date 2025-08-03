#!/usr/bin/env python3
"""
🚀 Trading Variables DB Migration GUI 실행 스크립트
GUI 기반 마이그레이션 도구 실행

사용법:
    python run_gui.py

작성일: 2025-07-30
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
sys.path.insert(0, project_root)


def main():
    """메인 함수"""
    try:
        print("🎯 Trading Variables DB Migration GUI 시작 중...")
        
        # GUI 모듈 import
        from trading_variables_DB_migration_main_gui import main as gui_main
        
        # GUI 실행
        gui_main()
        
    except ImportError as e:
        print(f"❌ 모듈 import 오류: {e}")
        print("필요한 패키지가 설치되어 있는지 확인하세요:")
        print("  - tkinter (Python 표준 라이브러리)")
        print("  - sqlite3 (Python 표준 라이브러리)")
        return 1
        
    except Exception as e:
        print(f"❌ GUI 실행 중 오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
