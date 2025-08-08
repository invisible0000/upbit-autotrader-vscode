#!/usr/bin/env python3
"""
데이터베이스 상태 확인 스크립트
strategies.sqlite3 변경 중 UI 멈춤 문제 분석용
"""

import yaml
import os
import sqlite3
from pathlib import Path

def main():
    print("=== 데이터베이스 상태 진단 시작 ===\n")

    # 1. database_config.yaml 상태 확인
    config_path = "config/database_config.yaml"
    print(f"1️⃣ {config_path} 상태 확인")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        print("✅ 설정 파일 로드 성공")

        # databases 섹션에서 경로 정보 추출
        databases = config.get('databases', {})
        for db_type, conf in databases.items():
            print(f"   {db_type}: {conf.get('path', 'N/A')}")
        print()

    except Exception as e:
        print(f"❌ 설정 파일 로드 실패: {e}")
        return    # 2. 각 데이터베이스 파일 상태 확인
    print("2️⃣ 데이터베이스 파일들 상태 확인")

    for db_type, conf in config.items():
        db_path = conf['path']
        print(f"\n📁 {db_type} 데이터베이스:")
        print(f"   경로: {db_path}")

        # 파일 존재 여부
        if os.path.exists(db_path):
            print(f"   ✅ 파일 존재")
            print(f"   📏 크기: {os.path.getsize(db_path):,} bytes")

            # SQLite 유효성 검증
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                conn.close()
                print(f"   ✅ 유효한 SQLite 파일 (테이블 {len(tables)}개)")

            except Exception as e:
                print(f"   ❌ SQLite 검증 실패: {e}")
        else:
            print(f"   ❌ 파일 없음")

    # 3. DDD 시스템 상태 확인
    print("\n3️⃣ DDD 시스템 상태 확인")

    try:
        from upbit_auto_trading.domain.services.database_path_service import DatabasePathService
        from upbit_auto_trading.infrastructure.repositories.database_config_repository import DatabaseConfigRepository

        # 싱글톤 상태 확인
        service = DatabasePathService()
        print("✅ DatabasePathService 싱글톤 생성 성공")

        # 경로 조회
        paths = service.get_all_database_paths()
        print(f"✅ DDD 서비스에서 조회한 경로: {len(paths)}개")
        for db_type, path in paths.items():
            print(f"   {db_type}: {path}")

    except Exception as e:
        print(f"❌ DDD 시스템 확인 실패: {e}")

    # 4. 잠재적 문제 분석
    print("\n4️⃣ 잠재적 문제 분석")

    # 파일 락 확인
    databases = config.get('databases', {})
    strategies_conf = databases.get('strategies', {})
    strategies_path = strategies_conf.get('path', '')

    if strategies_path and os.path.exists(strategies_path):
        try:
            # 파일 열기 시도
            with open(strategies_path, 'r+b') as f:
                pass
            print(f"✅ {os.path.basename(strategies_path)} 파일 락 없음")
        except Exception as e:
            print(f"⚠️ {os.path.basename(strategies_path)} 파일 락 가능성: {e}")    # 백업 파일들 확인
    data_dir = Path("data")
    backup_files = list(data_dir.glob("*복사본*")) + list(data_dir.glob("*backup*"))
    if backup_files:
        print(f"\n📦 백업 파일들 발견: {len(backup_files)}개")
        for backup in backup_files:
            print(f"   {backup}")

    print("\n=== 진단 완료 ===")

if __name__ == "__main__":
    main()
