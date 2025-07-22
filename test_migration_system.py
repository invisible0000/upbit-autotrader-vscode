#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DB 마이그레이션 시스템 테스트

새로 구축한 DB 정리 및 마이그레이션 시스템을 테스트합니다.
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_import_modules():
    """모듈 임포트 테스트"""
    print("🧪 모듈 임포트 테스트...")
    
    try:
        from upbit_auto_trading.data_layer.storage.db_cleanup_manager import DBCleanupManager
        print("✅ DBCleanupManager 임포트 성공")
        
        from upbit_auto_trading.data_layer.migrations.schema_definitions.version_registry import (
            SchemaVersionRegistry, get_current_schema_version
        )
        print("✅ SchemaVersionRegistry 임포트 성공")
        
        print(f"📋 현재 권장 스키마 버전: {get_current_schema_version()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 모듈 임포트 실패: {e}")
        return False

def test_schema_registry():
    """스키마 레지스트리 테스트"""
    print("\n🧪 스키마 레지스트리 테스트...")
    
    try:
        from upbit_auto_trading.data_layer.migrations.schema_definitions.version_registry import SchemaVersionRegistry
        
        # 전체 버전 목록 조회
        versions = SchemaVersionRegistry.list_all_versions()
        print(f"✅ 등록된 스키마 버전: {len(versions)}개")
        
        for version in versions:
            print(f"   📋 {version['version']}: {version['name']}")
        
        # 최신 버전 조회
        latest = SchemaVersionRegistry.get_latest_version()
        print(f"✅ 최신 버전: {latest}")
        
        # 마이그레이션 경로 테스트
        migration_path = SchemaVersionRegistry.validate_migration_path("v1.0-legacy", "v2.0-strategy-combination")
        print(f"✅ 마이그레이션 경로 검증: {'가능' if migration_path['valid'] else '불가능'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 스키마 레지스트리 테스트 실패: {e}")
        return False

def test_cleanup_manager():
    """DB 정리 관리자 테스트"""
    print("\n🧪 DB 정리 관리자 테스트...")
    
    try:
        from upbit_auto_trading.data_layer.storage.db_cleanup_manager import DBCleanupManager
        
        # 인스턴스 생성
        manager = DBCleanupManager()
        print("✅ DBCleanupManager 인스턴스 생성 성공")
        
        # 현재 상태 분석 (실제 DB 파일이 없어도 오류가 나지 않도록)
        analysis = manager.analyze_current_state()
        print("✅ DB 상태 분석 완료")
        print(f"   📁 DB 파일 수: {len(analysis['database_files'])}")
        print(f"   🏷️ 스키마 버전: {analysis['schema_version']}")
        print(f"   💾 총 크기: {analysis['total_size_mb']} MB")
        
        if analysis.get('issues'):
            print(f"   ⚠️ 발견된 문제: {len(analysis['issues'])}개")
        
        return True
        
    except Exception as e:
        print(f"❌ DB 정리 관리자 테스트 실패: {e}")
        return False

def test_cli_tools():
    """CLI 도구 테스트"""
    print("\n🧪 CLI 도구 테스트...")
    
    try:
        # db_cleanup_tool.py 구문 검사
        with open(project_root / "tools" / "db_cleanup_tool.py", 'r', encoding='utf-8') as f:
            cli_code = f.read()
        
        compile(cli_code, "db_cleanup_tool.py", "exec")
        print("✅ db_cleanup_tool.py 구문 검사 통과")
        
        # migration_wizard.py 구문 검사
        with open(project_root / "tools" / "migration_wizard.py", 'r', encoding='utf-8') as f:
            wizard_code = f.read()
            
        compile(wizard_code, "migration_wizard.py", "exec")
        print("✅ migration_wizard.py 구문 검사 통과")
        
        return True
        
    except Exception as e:
        print(f"❌ CLI 도구 테스트 실패: {e}")
        return False

def test_file_structure():
    """파일 구조 테스트"""
    print("\n🧪 파일 구조 테스트...")
    
    required_files = [
        "upbit_auto_trading/data_layer/storage/db_cleanup_manager.py",
        "upbit_auto_trading/data_layer/migrations/schema_definitions/version_registry.py",
        "tools/db_cleanup_tool.py",
        "tools/migration_wizard.py",
        "docs/DB_MIGRATION_AND_CLEANUP_PLAN.md",
        "docs/DB_MIGRATION_USAGE_GUIDE.md"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (누락)")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️ 누락된 파일: {len(missing_files)}개")
        return False
    else:
        print("\n✅ 모든 필수 파일이 존재합니다")
        return True

def test_convenience_functions():
    """편의 함수 테스트"""
    print("\n🧪 편의 함수 테스트...")
    
    try:
        from upbit_auto_trading.data_layer.storage.db_cleanup_manager import analyze_db
        from upbit_auto_trading.data_layer.migrations.schema_definitions.version_registry import (
            get_current_schema_version, is_migration_required
        )
        
        # 분석 함수 테스트
        analysis = analyze_db()
        print("✅ analyze_db() 함수 동작 확인")
        
        # 버전 관련 함수 테스트
        current_version = get_current_schema_version()
        print(f"✅ get_current_schema_version(): {current_version}")
        
        # 마이그레이션 필요 여부 (가상의 버전으로 테스트)
        migration_needed = is_migration_required("v1.0-legacy")
        print(f"✅ is_migration_required(): {migration_needed}")
        
        return True
        
    except Exception as e:
        print(f"❌ 편의 함수 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 DB 마이그레이션 시스템 테스트 시작")
    print("=" * 50)
    
    tests = [
        ("파일 구조", test_file_structure),
        ("모듈 임포트", test_import_modules),
        ("스키마 레지스트리", test_schema_registry),
        ("DB 정리 관리자", test_cleanup_manager),
        ("CLI 도구", test_cli_tools),
        ("편의 함수", test_convenience_functions)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 테스트 통과")
            else:
                print(f"❌ {test_name} 테스트 실패")
        except Exception as e:
            print(f"❌ {test_name} 테스트 오류: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 테스트를 통과했습니다!")
        print("\n💡 다음 단계:")
        print("   1. python tools/db_cleanup_tool.py --analyze 로 현재 DB 상태 확인")
        print("   2. python tools/migration_wizard.py 로 대화형 도구 체험")
        print("   3. 실제 프로젝트에서 필요한 기능 추가 개발")
    else:
        print(f"⚠️ {total - passed}개 테스트가 실패했습니다. 문제를 해결하세요.")
        sys.exit(1)

if __name__ == "__main__":
    main()
