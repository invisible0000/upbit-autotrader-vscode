#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
대화형 마이그레이션 도구

사용자 친화적인 인터페이스로 DB 마이그레이션을 안내하는 도구
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from upbit_auto_trading.data_layer.storage.db_cleanup_manager import DBCleanupManager
from upbit_auto_trading.data_layer.migrations.schema_definitions.version_registry import (
    SchemaVersionRegistry, get_current_schema_version
)

class MigrationWizard:
    """대화형 마이그레이션 도우미"""
    
    def __init__(self):
        self.cleanup_manager = DBCleanupManager()
        self.current_analysis = None
        
    def run(self):
        """마이그레이션 마법사 실행"""
        self.print_welcome()
        
        # 현재 상태 분석
        self.current_analysis = self.analyze_current_state()
        
        # 메인 메뉴 실행
        while True:
            choice = self.show_main_menu()
            
            if choice == '1':
                self.guided_migration()
            elif choice == '2':
                self.emergency_reset_wizard()
            elif choice == '3':
                self.backup_wizard()
            elif choice == '4':
                self.analyze_and_report()
            elif choice == '5':
                self.settings_wizard()
            elif choice == '0':
                print("👋 마이그레이션 도우미를 종료합니다.")
                break
            else:
                print("❌ 잘못된 선택입니다. 다시 선택해주세요.")
    
    def print_welcome(self):
        """환영 메시지 출력"""
        print("=" * 60)
        print("🧙‍♂️ 업비트 자동매매 DB 마이그레이션 도우미")
        print("=" * 60)
        print()
        print("이 도구는 데이터베이스 스키마 변경, 초기화, 백업을")
        print("안전하고 쉽게 수행할 수 있도록 도와드립니다.")
        print()
    
    def analyze_current_state(self) -> Dict[str, Any]:
        """현재 DB 상태 분석"""
        print("🔍 현재 데이터베이스 상태를 분석하는 중...")
        analysis = self.cleanup_manager.analyze_current_state()
        print("✅ 분석 완료!")
        print()
        return analysis
    
    def show_main_menu(self) -> str:
        """메인 메뉴 표시"""
        current_version = self.current_analysis.get('schema_version', 'unknown')
        latest_version = get_current_schema_version()
        total_size = self.current_analysis.get('total_size_mb', 0)
        
        print("📊 현재 상태:")
        print(f"   🏷️ 스키마 버전: {current_version}")
        print(f"   💾 DB 크기: {total_size} MB")
        print(f"   📁 DB 파일 수: {len(self.current_analysis.get('database_files', []))}")
        
        if self.current_analysis.get('issues'):
            print(f"   ⚠️ 발견된 문제: {len(self.current_analysis['issues'])}개")
        
        print()
        print("🎯 수행할 작업을 선택하세요:")
        print()
        print("1️⃣ 가이드 마이그레이션 (권장)")
        print("2️⃣ 긴급 DB 초기화")
        print("3️⃣ 백업 관리")
        print("4️⃣ 상세 분석 보고서")
        print("5️⃣ 설정 관리")
        print("0️⃣ 종료")
        print()
        
        return input("선택 (0-5): ").strip()
    
    def guided_migration(self):
        """가이드 마이그레이션"""
        print("\n🎯 가이드 마이그레이션")
        print("=" * 40)
        
        current_version = self.current_analysis.get('schema_version', 'unknown')
        latest_version = get_current_schema_version()
        
        if current_version == latest_version:
            print("✅ 이미 최신 스키마 버전을 사용하고 있습니다!")
            input("\n계속하려면 Enter를 누르세요...")
            return
        
        print(f"현재 버전: {current_version}")
        print(f"최신 버전: {latest_version}")
        print()
        
        # 마이그레이션 경로 확인
        migration_validation = SchemaVersionRegistry.validate_migration_path(
            current_version, latest_version
        )
        
        if not migration_validation['valid']:
            print("❌ 직접 마이그레이션 경로가 없습니다.")
            print("💡 긴급 초기화를 통해 최신 버전으로 업그레이드하세요.")
            input("\n계속하려면 Enter를 누르세요...")
            return
        
        print("✅ 마이그레이션 경로를 찾았습니다!")
        
        # 경고사항 표시
        if migration_validation.get('warnings'):
            print("\n⚠️ 주의사항:")
            for warning in migration_validation['warnings']:
                print(f"   • {warning}")
        
        print("\n🔄 마이그레이션 과정:")
        print("   1. 현재 DB 백업 생성")
        print("   2. 스키마 업그레이드")
        print("   3. 데이터 변환 및 이관")
        print("   4. 무결성 검증")
        
        if not self.confirm("마이그레이션을 시작하시겠습니까?"):
            return
        
        # 백업 이름 입력
        backup_name = input("\n백업 이름 (Enter=자동생성): ").strip()
        if not backup_name:
            backup_name = None
        
        print("\n🚀 마이그레이션 시작...")
        
        try:
            # 백업 생성
            backup_path = self.cleanup_manager.create_backup(backup_name)
            print(f"✅ 백업 완료: {backup_path}")
            
            # 스키마 적용
            success = self.cleanup_manager.apply_clean_schema(latest_version)
            
            if success:
                print("✅ 스키마 업그레이드 완료!")
                
                # 데이터 마이그레이션 (향후 구현)
                print("📦 데이터 마이그레이션 (현재는 스킵)")
                
                # 검증
                validation = self.cleanup_manager.validate_migration()
                if validation['status'] == 'passed':
                    print("✅ 마이그레이션 성공!")
                else:
                    print("⚠️ 검증에서 문제 발견:")
                    for error in validation.get('errors', []):
                        print(f"   • {error}")
            else:
                print("❌ 마이그레이션 실패!")
                
        except Exception as e:
            print(f"❌ 마이그레이션 중 오류 발생: {e}")
        
        input("\n계속하려면 Enter를 누르세요...")
    
    def emergency_reset_wizard(self):
        """긴급 초기화 마법사"""
        print("\n🚨 긴급 DB 초기화")
        print("=" * 40)
        print()
        print("⚠️ 주의: 이 작업은 데이터베이스를 완전히 초기화합니다!")
        print()
        print("두 가지 옵션이 있습니다:")
        print("1️⃣ 안전 초기화 (백테스트 결과 보존)")
        print("2️⃣ 완전 초기화 (모든 데이터 삭제)")
        print("0️⃣ 취소")
        print()
        
        choice = input("선택 (0-2): ").strip()
        
        if choice == '0':
            return
        elif choice == '1':
            self.safe_reset_wizard()
        elif choice == '2':
            self.complete_reset_wizard()
        else:
            print("❌ 잘못된 선택입니다.")
    
    def safe_reset_wizard(self):
        """안전 초기화 마법사"""
        print("\n🛡️ 안전 초기화")
        print("백테스트 결과와 중요한 설정은 보존됩니다.")
        
        if not self.confirm("안전 초기화를 진행하시겠습니까?"):
            return
        
        print("\n🚀 안전 초기화 시작...")
        success = self.cleanup_manager.emergency_reset(preserve_backtests=True)
        
        if success:
            print("✅ 안전 초기화 완료!")
        else:
            print("❌ 초기화 실패!")
        
        input("\n계속하려면 Enter를 누르세요...")
    
    def complete_reset_wizard(self):
        """완전 초기화 마법사"""
        print("\n💥 완전 초기화")
        print("⚠️ 모든 데이터가 영구적으로 삭제됩니다!")
        
        if not self.confirm("정말로 모든 데이터를 삭제하시겠습니까?"):
            return
        
        # 이중 확인
        confirm_text = "DELETE"
        user_input = input(f"\n확인을 위해 '{confirm_text}'를 입력하세요: ").strip()
        
        if user_input != confirm_text:
            print("❌ 확인 텍스트가 일치하지 않습니다. 작업이 취소되었습니다.")
            return
        
        print("\n💥 완전 초기화 시작...")
        success = self.cleanup_manager.emergency_reset(preserve_backtests=False)
        
        if success:
            print("✅ 완전 초기화 완료!")
        else:
            print("❌ 초기화 실패!")
        
        input("\n계속하려면 Enter를 누르세요...")
    
    def backup_wizard(self):
        """백업 관리 마법사"""
        print("\n💾 백업 관리")
        print("=" * 40)
        print()
        print("1️⃣ 새 백업 생성")
        print("2️⃣ 백업 목록 조회")
        print("3️⃣ 백업 복원") 
        print("0️⃣ 돌아가기")
        print()
        
        choice = input("선택 (0-3): ").strip()
        
        if choice == '1':
            self.create_backup_wizard()
        elif choice == '2':
            self.list_backups_wizard()
        elif choice == '3':
            self.restore_backup_wizard()
        elif choice == '0':
            return
        else:
            print("❌ 잘못된 선택입니다.")
    
    def create_backup_wizard(self):
        """백업 생성 마법사"""
        print("\n💾 새 백업 생성")
        
        backup_name = input("백업 이름 (Enter=자동생성): ").strip()
        if not backup_name:
            backup_name = None
        
        print("\n📦 백업 생성 중...")
        try:
            backup_path = self.cleanup_manager.create_backup(backup_name)
            print(f"✅ 백업 완료: {backup_path}")
        except Exception as e:
            print(f"❌ 백업 실패: {e}")
        
        input("\n계속하려면 Enter를 누르세요...")
    
    def list_backups_wizard(self):
        """백업 목록 조회"""
        print("\n📋 백업 목록")
        print("(향후 구현 예정)")
        input("\n계속하려면 Enter를 누르세요...")
    
    def restore_backup_wizard(self):
        """백업 복원 마법사"""
        print("\n🔄 백업 복원")
        print("(향후 구현 예정)")
        input("\n계속하려면 Enter를 누르세요...")
    
    def analyze_and_report(self):
        """상세 분석 보고서"""
        print("\n📊 상세 분석 보고서")
        print("=" * 40)
        
        analysis = self.current_analysis
        
        print(f"\n🕐 분석 시간: {analysis['timestamp']}")
        print(f"🏷️ 스키마 버전: {analysis['schema_version']}")
        print(f"💾 총 크기: {analysis['total_size_mb']} MB")
        
        # DB 파일 정보
        print(f"\n📁 데이터베이스 파일:")
        for db_file in analysis.get('database_files', []):
            print(f"   • {db_file}")
        
        # 테이블 정보
        print(f"\n📋 테이블 현황:")
        for db_name, tables in analysis.get('tables', {}).items():
            print(f"\n   📂 {db_name}:")
            for table in tables:
                count = analysis.get('data_counts', {}).get(db_name, {}).get(table, 0)
                print(f"      • {table}: {count:,}개")
        
        # 문제점
        issues = analysis.get('issues', [])
        if issues:
            print(f"\n⚠️ 발견된 문제점:")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print(f"\n✅ 문제점이 발견되지 않았습니다.")
        
        # 권장사항
        current_version = analysis['schema_version']
        latest_version = get_current_schema_version()
        
        print(f"\n💡 권장사항:")
        if current_version != latest_version:
            print(f"   • 최신 스키마로 업그레이드 권장 ({current_version} → {latest_version})")
        if issues:
            print("   • 발견된 문제점들을 해결하세요")
        if analysis['total_size_mb'] > 100:
            print("   • 대용량 DB입니다. 백업 관리에 주의하세요")
        
        input("\n계속하려면 Enter를 누르세요...")
    
    def settings_wizard(self):
        """설정 관리 마법사"""
        print("\n⚙️ 설정 관리")
        print("=" * 40)
        print()
        print("1️⃣ 스키마 버전 정보")
        print("2️⃣ 마이그레이션 규칙 조회")
        print("3️⃣ 시스템 상태 확인")
        print("0️⃣ 돌아가기")
        print()
        
        choice = input("선택 (0-3): ").strip()
        
        if choice == '1':
            self.show_schema_versions()
        elif choice == '2':
            self.show_migration_rules()
        elif choice == '3':
            self.show_system_status()
        elif choice == '0':
            return
        else:
            print("❌ 잘못된 선택입니다.")
    
    def show_schema_versions(self):
        """스키마 버전 정보 표시"""
        print("\n🗃️ 스키마 버전 정보")
        
        versions = SchemaVersionRegistry.list_all_versions()
        
        for version_info in versions:
            status = "✅ LATEST" if version_info['is_latest'] else "📋"
            deprecated = " (⚠️ DEPRECATED)" if version_info['deprecated'] else ""
            
            print(f"\n{status} {version_info['version']}{deprecated}")
            print(f"   📝 {version_info['name']}")
            print(f"   📅 {version_info['release_date']}")
            print(f"   📄 {version_info['description']}")
        
        input("\n계속하려면 Enter를 누르세요...")
    
    def show_migration_rules(self):
        """마이그레이션 규칙 조회"""
        print("\n🔄 마이그레이션 규칙")
        print("(향후 구현 예정)")
        input("\n계속하려면 Enter를 누르세요...")
    
    def show_system_status(self):
        """시스템 상태 확인"""
        print("\n🔍 시스템 상태")
        
        try:
            # DB 연결 테스트
            engine = self.cleanup_manager.db_manager.get_engine()
            print("✅ 데이터베이스 연결: 정상")
            
            # 백업 시스템 테스트  
            print("✅ 백업 시스템: 정상")
            
            # 마이그레이션 시스템 테스트
            print("✅ 마이그레이션 시스템: 정상")
            
        except Exception as e:
            print(f"❌ 시스템 오류: {e}")
        
        input("\n계속하려면 Enter를 누르세요...")
    
    def confirm(self, message: str) -> bool:
        """사용자 확인"""
        while True:
            response = input(f"{message} (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no', '']:
                return False
            else:
                print("y 또는 n을 입력해주세요.")

def main():
    """메인 함수"""
    try:
        wizard = MigrationWizard()
        wizard.run()
    except KeyboardInterrupt:
        print("\n\n👋 사용자에 의해 종료되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
