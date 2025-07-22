#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DB 정리 도구 (CLI)

데이터베이스 초기화, 분석, 마이그레이션을 위한 명령줄 도구
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from upbit_auto_trading.data_layer.storage.db_cleanup_manager import DBCleanupManager
from upbit_auto_trading.data_layer.migrations.schema_definitions.version_registry import (
    SchemaVersionRegistry, get_current_schema_version, is_migration_required
)

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="🗃️ 업비트 자동매매 DB 정리 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 현재 DB 상태 분석
  python tools/db_cleanup_tool.py --analyze
  
  # 백업과 함께 완전 초기화
  python tools/db_cleanup_tool.py --reset-to-latest --backup-name "before_new_feature"
  
  # 백테스트 결과 보존하며 초기화  
  python tools/db_cleanup_tool.py --safe-reset
  
  # 특정 스키마 버전으로 초기화
  python tools/db_cleanup_tool.py --apply-schema v2.0-strategy-combination
  
  # 스키마 버전 목록 조회
  python tools/db_cleanup_tool.py --list-versions
        """
    )
    
    # 분석 관련 옵션
    analysis_group = parser.add_argument_group('분석 옵션')
    analysis_group.add_argument(
        '--analyze', 
        action='store_true',
        help='현재 DB 상태를 분석합니다'
    )
    analysis_group.add_argument(
        '--report-format',
        choices=['json', 'yaml', 'table'],
        default='table',
        help='분석 결과 출력 형식 (기본값: table)'
    )
    
    # 초기화 관련 옵션
    reset_group = parser.add_argument_group('초기화 옵션')
    reset_group.add_argument(
        '--reset-to-latest',
        action='store_true', 
        help='최신 스키마로 완전 초기화 (백업 권장)'
    )
    reset_group.add_argument(
        '--safe-reset',
        action='store_true',
        help='백테스트 결과를 보존하며 초기화'
    )
    reset_group.add_argument(
        '--quick-reset',
        action='store_true',
        help='모든 데이터를 삭제하고 빠른 초기화'
    )
    
    # 스키마 관련 옵션
    schema_group = parser.add_argument_group('스키마 옵션')
    schema_group.add_argument(
        '--apply-schema',
        help='특정 스키마 버전을 적용합니다'
    )
    schema_group.add_argument(
        '--list-versions',
        action='store_true',
        help='사용 가능한 스키마 버전 목록을 표시합니다'
    )
    
    # 백업 관련 옵션
    backup_group = parser.add_argument_group('백업 옵션')
    backup_group.add_argument(
        '--backup-name',
        help='백업 이름 (미지정시 자동 생성)'
    )
    backup_group.add_argument(
        '--skip-backup',
        action='store_true',
        help='백업 생성을 건너뜁니다 (위험!)'
    )
    
    # 기타 옵션
    misc_group = parser.add_argument_group('기타 옵션')
    misc_group.add_argument(
        '--dry-run',
        action='store_true',
        help='실제 실행하지 않고 수행할 작업만 표시'
    )
    misc_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='상세한 출력'
    )
    misc_group.add_argument(
        '--force',
        action='store_true',
        help='확인 없이 강제 실행'
    )
    
    args = parser.parse_args()
    
    # 최소 하나의 옵션은 선택되어야 함
    if not any([
        args.analyze, args.reset_to_latest, args.safe_reset, 
        args.quick_reset, args.apply_schema, args.list_versions
    ]):
        parser.print_help()
        return
    
    try:
        # DB 정리 관리자 초기화
        cleanup_manager = DBCleanupManager()
        
        # 각 명령 실행
        if args.list_versions:
            list_schema_versions()
            
        elif args.analyze:
            analyze_database(cleanup_manager, args.report_format)
            
        elif args.reset_to_latest:
            reset_to_latest(cleanup_manager, args)
            
        elif args.safe_reset:
            safe_reset_database(cleanup_manager, args)
            
        elif args.quick_reset:
            quick_reset_database(cleanup_manager, args)
            
        elif args.apply_schema:
            apply_specific_schema(cleanup_manager, args.apply_schema, args)
            
    except KeyboardInterrupt:
        print("\n❌ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def list_schema_versions():
    """스키마 버전 목록 출력"""
    print("🗃️ 사용 가능한 스키마 버전:")
    print()
    
    versions = SchemaVersionRegistry.list_all_versions()
    
    for version_info in versions:
        status_icon = "✅" if version_info["is_latest"] else "📋"
        deprecated_mark = " (⚠️ DEPRECATED)" if version_info["deprecated"] else ""
        
        print(f"{status_icon} {version_info['version']}{deprecated_mark}")
        print(f"   📝 {version_info['name']}")
        print(f"   📅 {version_info['release_date']}")
        print(f"   📄 {version_info['description']}")
        print()

def analyze_database(cleanup_manager: DBCleanupManager, report_format: str):
    """데이터베이스 분석"""
    print("🔍 데이터베이스 상태 분석 중...")
    
    analysis = cleanup_manager.analyze_current_state()
    
    if report_format == 'json':
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        
    elif report_format == 'yaml':
        try:
            import yaml
            print(yaml.dump(analysis, default_flow_style=False, allow_unicode=True))
        except ImportError:
            print("❌ PyYAML이 설치되지 않았습니다. JSON 형식으로 출력합니다:")
            print(json.dumps(analysis, indent=2, ensure_ascii=False))
            
    else:  # table format
        print_analysis_table(analysis)

def print_analysis_table(analysis):
    """분석 결과를 테이블 형식으로 출력"""
    print("\n📊 DB 분석 결과")
    print("=" * 50)
    
    # 기본 정보
    print(f"🕐 분석 시간: {analysis['timestamp']}")
    print(f"📁 DB 파일 수: {len(analysis['database_files'])}")
    print(f"💾 총 크기: {analysis['total_size_mb']} MB")
    print(f"🏷️ 스키마 버전: {analysis['schema_version']}")
    
    # DB 파일 목록
    if analysis['database_files']:
        print(f"\n📂 DB 파일 목록:")
        for db_file in analysis['database_files']:
            print(f"   • {db_file}")
    
    # 테이블 정보
    if analysis['tables']:
        print(f"\n📋 테이블 현황:")
        for db_name, tables in analysis['tables'].items():
            print(f"   📁 {db_name}: {len(tables)}개 테이블")
            for table in tables[:5]:  # 최대 5개만 표시
                count = analysis['data_counts'].get(db_name, {}).get(table, 0)
                print(f"      • {table} ({count:,}개 레코드)")
            if len(tables) > 5:
                print(f"      ... 외 {len(tables)-5}개")
    
    # 문제점
    if analysis['issues']:
        print(f"\n⚠️ 발견된 문제점:")
        for issue in analysis['issues']:
            print(f"   • {issue}")
    else:
        print(f"\n✅ 문제점이 발견되지 않았습니다.")
    
    # 권장사항
    current_version = analysis['schema_version']
    latest_version = get_current_schema_version()
    
    if is_migration_required(current_version):
        print(f"\n💡 권장사항:")
        print(f"   현재 버전: {current_version}")
        print(f"   최신 버전: {latest_version}")
        print(f"   마이그레이션을 권장합니다.")

def reset_to_latest(cleanup_manager: DBCleanupManager, args):
    """최신 스키마로 초기화"""
    latest_version = get_current_schema_version()
    
    print(f"🧹 최신 스키마로 DB 초기화: {latest_version}")
    
    if not args.force:
        if not confirm_action("모든 데이터가 삭제됩니다. 계속하시겠습니까?"):
            print("❌ 작업이 취소되었습니다.")
            return
    
    if args.dry_run:
        print("🧪 DRY RUN 모드: 실제로는 다음 작업들이 수행됩니다:")
        print("   1. 현재 DB 백업 생성")
        print("   2. 기존 DB 파일 삭제") 
        print("   3. 최신 스키마 적용")
        print("   4. 마이그레이션 검증")
        return
    
    # 백업 생성
    if not args.skip_backup:
        backup_path = cleanup_manager.create_backup(args.backup_name)
        print(f"💾 백업 생성 완료: {backup_path}")
    
    # 스키마 적용
    success = cleanup_manager.apply_clean_schema("latest")
    
    if success:
        print("✅ 최신 스키마 적용 완료!")
        
        # 검증
        validation = cleanup_manager.validate_migration()
        if validation["status"] == "passed":
            print("✅ 검증 통과!")
        else:
            print("⚠️ 검증에서 문제가 발견되었습니다:")
            for error in validation.get("errors", []):
                print(f"   • {error}")
    else:
        print("❌ 스키마 적용 실패!")

def safe_reset_database(cleanup_manager: DBCleanupManager, args):
    """안전한 DB 초기화 (백테스트 보존)"""
    print("🛡️ 안전한 DB 초기화 (백테스트 결과 보존)")
    
    if not args.force:
        if not confirm_action("백테스트 결과를 제외한 모든 데이터가 삭제됩니다. 계속하시겠습니까?"):
            print("❌ 작업이 취소되었습니다.")
            return
    
    if args.dry_run:
        print("🧪 DRY RUN 모드: 실제로는 다음 작업들이 수행됩니다:")
        print("   1. 현재 DB 백업 생성")
        print("   2. 백테스트 데이터 추출")
        print("   3. 새 스키마 적용")
        print("   4. 백테스트 데이터 복원")
        return
    
    success = cleanup_manager.emergency_reset(preserve_backtests=True)
    
    if success:
        print("✅ 안전한 DB 초기화 완료!")
    else:
        print("❌ DB 초기화 실패!")

def quick_reset_database(cleanup_manager: DBCleanupManager, args):
    """빠른 DB 초기화"""
    print("⚡ 빠른 DB 초기화 (모든 데이터 삭제)")
    
    if not args.force:
        if not confirm_action("모든 데이터가 완전히 삭제됩니다. 정말 계속하시겠습니까?"):
            print("❌ 작업이 취소되었습니다.")
            return
    
    if args.dry_run:
        print("🧪 DRY RUN 모드: 실제로는 다음 작업들이 수행됩니다:")
        print("   1. 모든 DB 파일 삭제")
        print("   2. 최신 스키마 적용")
        return
    
    success = cleanup_manager.emergency_reset(preserve_backtests=False)
    
    if success:
        print("✅ 빠른 DB 초기화 완료!")
    else:
        print("❌ DB 초기화 실패!")

def apply_specific_schema(cleanup_manager: DBCleanupManager, schema_version: str, args):
    """특정 스키마 버전 적용"""
    print(f"🎯 특정 스키마 적용: {schema_version}")
    
    # 스키마 버전 유효성 확인
    version_info = SchemaVersionRegistry.get_version_info(schema_version)
    if not version_info:
        print(f"❌ 알 수 없는 스키마 버전: {schema_version}")
        return
    
    if version_info.get('deprecated'):
        print(f"⚠️ 경고: {schema_version}는 더 이상 사용되지 않는 버전입니다.")
        if not args.force:
            if not confirm_action("계속하시겠습니까?"):
                print("❌ 작업이 취소되었습니다.")
                return
    
    if args.dry_run:
        print("🧪 DRY RUN 모드: 실제로는 다음 작업들이 수행됩니다:")
        print(f"   1. {schema_version} 스키마 적용")
        print("   2. 마이그레이션 검증")
        return
    
    success = cleanup_manager.apply_clean_schema(schema_version)
    
    if success:
        print(f"✅ 스키마 {schema_version} 적용 완료!")
    else:
        print(f"❌ 스키마 {schema_version} 적용 실패!")

def confirm_action(message: str) -> bool:
    """사용자 확인 받기"""
    while True:
        response = input(f"{message} (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no', '']:
            return False
        else:
            print("y 또는 n을 입력해주세요.")

if __name__ == "__main__":
    main()
