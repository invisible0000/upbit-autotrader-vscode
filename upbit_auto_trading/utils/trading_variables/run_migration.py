#!/usr/bin/env python3
"""
🔄 Trading Variables DB 마이그레이션 실행 스크립트
사용법: python run_migration.py
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, project_root)


def main():
    """마이그레이션 실행"""
    print("🎯 Trading Variables DB 마이그레이션을 시작합니다.")
    print()
    
    # 동적 import
    from upbit_auto_trading.utils.trading_variables.migrate_db import TradingVariablesDBMigration
    
    # 마이그레이션 객체 생성
    migration = TradingVariablesDBMigration()
    
    # 안전한 마이그레이션 실행 (사용자 확인 포함)
    success = migration.run_migration(force=False)
    
    if success:
        print("\n🎉 마이그레이션이 성공적으로 완료되었습니다!")
        print("이제 프로그램을 다시 시작하면 새로운 DB 스키마가 적용됩니다.")
    else:
        print("\n❌ 마이그레이션 중 오류가 발생했습니다.")
        print("백업 파일에서 복원하거나 로그를 확인해주세요.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
