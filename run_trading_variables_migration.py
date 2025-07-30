#!/usr/bin/env python3
"""
🚀 Trading Variables DB M        # GUI 모듈 import 및 실행
        try:
            from trading_variables_DB_migration_main_gui import main as gui_main
            print("🖥️ GUI 시작...")
            gui_main()
        except Exception as gui_error:
            print(f"❌ GUI 실행 오류: {gui_error}")
            # 원래 디렉토리로 복원
            os.chdir(original_cwd)
            return 1ion Tool - 프로젝트 루트 실행기
========================================================

프로젝트 루트에서 Trading Variables DB Migration GUI를 실행하는 스크립트

사용법:
    python run_trading_variables_migration.py

특징:
- 프로젝트 루트에서 직접 실행 가능
- 자동 경로 탐지 및 설정
- LLM 에이전트 친화적 (경로 찾기 토큰 절약)

작성일: 2025-07-30
"""

import subprocess
import sys
import os

def run_migration_script():
    """
    GUI 트레이딩 변수 DB 마이그레이션 유틸리티를 실행합니다.

    Python의 '-m' 옵션을 사용하여 모듈로 실행하여,
    프로젝트의 어느 위치에서든 안정적으로 경로를 찾을 수 있도록 합니다.
    """
    module_path = "upbit_auto_trading.utils.trading_variables.gui_variables_DB_migration_util.run_gui_trading_variables_DB_migration"
    
    print("="*50)
    print(f"▶️  마이그레이션 스크립트 실행: {module_path}")
    print("="*50)
    
    try:
        # sys.executable은 현재 실행 중인 파이썬 인터프리터를 가리킵니다.
        # 이를 통해 가상환경(venv)이 활성화된 경우에도 정확한 파이썬으로 실행됩니다.
        result = subprocess.run(
            [sys.executable, "-m", module_path],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8' # PowerShell 터미널의 한글 깨짐 방지
        )
        print("✅ 마이그레이션 성공:")
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print("❌ 마이그레이션 실패:")
        print(e.stderr)
        
    except FileNotFoundError:
        print(f"❌ 오류: '{sys.executable}' 파이썬 인터프리터를 찾을 수 없습니다.")

if __name__ == "__main__":
    run_migration_script()