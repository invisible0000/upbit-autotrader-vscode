#!/usr/bin/env python3
"""
🚀 Trading Variables DB Migration Tool - 프로젝트 루트 실행기 v2
============================================================

프로젝트 루트에서 Trading Variables DB Migration GUI를 실행하는 스크립트

사용법:
    python run_trading_variables_migration_v2.py

특징:
- 프로젝트 루트에서 직접 실행 가능
- subprocess를 통한 안전한 실행
- 자동 경로 탐지 및 설정
- LLM 에이전트 친화적 (경로 찾기 토큰 절약)

작성일: 2025-07-30
"""

import sys
import os
import subprocess


def main():
    """메인 함수 - 프로젝트 루트에서 GUI 실행"""
    try:
        print("🎯 Trading Variables DB Migration Tool v2 시작...")
        print("📁 프로젝트 루트에서 실행 중...")
        
        # 현재 디렉토리가 프로젝트 루트인지 확인
        current_dir = os.path.dirname(os.path.abspath(__file__))
        expected_gui_path = os.path.join(
            current_dir,
            "upbit_auto_trading",
            "utils",
            "trading_variables",
            "gui_variables_DB_migration_util"
        )
        
        if not os.path.exists(expected_gui_path):
            print("❌ 오류: upbit_auto_trading 폴더를 찾을 수 없습니다.")
            print(f"현재 위치: {current_dir}")
            print("이 스크립트는 프로젝트 루트에서 실행해야 합니다.")
            return 1
        
        # 직접 해당 디렉토리에서 파이썬 스크립트 실행
        script_path = os.path.join(expected_gui_path, "trading_variables_DB_migration_main_gui.py")
        
        if not os.path.exists(script_path):
            print(f"❌ 오류: {script_path} 파일을 찾을 수 없습니다.")
            return 1
        
        print(f"📂 GUI 스크립트 실행: {script_path}")
        print(f"📍 작업 디렉토리: {expected_gui_path}")
        
        # subprocess로 직접 실행
        result = subprocess.run([
            sys.executable, script_path
        ], cwd=expected_gui_path, capture_output=False)
        
        if result.returncode != 0:
            print(f"❌ GUI 실행 실패 (exit code: {result.returncode})")
            return result.returncode
        
        print("✅ GUI 정상 종료")
        
    except Exception as e:
        print(f"❌ 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    print("=" * 60)
    print("🎯 Trading Variables DB Migration Tool v2")
    print("📍 프로젝트 루트 실행기 (subprocess 방식)")
    print("=" * 60)
    
    sys.exit(main())
