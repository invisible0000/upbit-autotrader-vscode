#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
프로젝트 자동 정리 스크립트
- 불필요한 테스트/분석 스크립트 정리
- 유용한 스크립트는 scripts/utility로 이동
- 일회성 스크립트는 삭제 또는 archive 폴더로 이동
"""

import os
import shutil
import glob
from pathlib import Path
import json
from datetime import datetime

class ProjectCleaner:
    """프로젝트 정리 클래스"""
    
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.scripts_dir = self.project_root / "scripts"
        self.utility_dir = self.scripts_dir / "utility"
        self.archive_dir = self.scripts_dir / "archive"
        self.cleanup_log = []
        
        # 디렉토리 생성
        self.utility_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cleanup_candidates(self):
        """정리 대상 파일 목록 수집"""
        patterns = [
            "check_*.py",
            "analyze_*.py", 
            "test_*.py",
            "debug_*.py",
            "simple_*.py",
            "migration_*.py",
            "clean_*.py",
            "create_sample_*.py",
            "remove_*.py",
            "extend_*.py",
            "fix_*.py"
        ]
        
        candidates = []
        for pattern in patterns:
            files = list(self.project_root.glob(pattern))
            candidates.extend(files)
        
        return candidates
    
    def categorize_files(self, files):
        """파일을 카테고리별로 분류"""
        categories = {
            'keep_useful': [],      # 유용한 스크립트 - utility로 이동
            'archive': [],          # 보관용 - archive로 이동  
            'delete': [],           # 삭제
            'manual_review': []     # 수동 검토 필요
        }
        
        # 유용한 스크립트 패턴
        useful_patterns = [
            "check_db_structure.py",
            "check_atomic_tables.py", 
            "analyze_db_structure.py",
            "run_tests_in_order.py"
        ]
        
        # 삭제 대상 패턴 (일회성, 오류, 중복)
        delete_patterns = [
            "check_auto_generated_triggers.py",
            "debug_*",
            "simple_check.py",
            "test_ui_*",
            "test_new_*",
            "test_integrated_*",
            "test_condition_*", 
            "test_component_*",
            "test_combination_*",
            "migration_step*.py",
            "clean_all_*.py",
            "remove_*.py"
        ]
        
        for file_path in files:
            file_name = file_path.name
            
            # 유용한 스크립트 확인
            if any(pattern in file_name for pattern in useful_patterns):
                categories['keep_useful'].append(file_path)
            
            # 삭제 대상 확인  
            elif any(self._match_pattern(file_name, pattern) for pattern in delete_patterns):
                categories['delete'].append(file_path)
            
            # 중요한 테스트는 archive
            elif file_name.startswith('test_strategy_management') or 'backtest' in file_name:
                categories['archive'].append(file_path)
                
            # 나머지는 수동 검토
            else:
                categories['manual_review'].append(file_path)
        
        return categories
    
    def _match_pattern(self, filename, pattern):
        """와일드카드 패턴 매칭"""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
    
    def preview_cleanup(self):
        """정리 작업 미리보기"""
        candidates = self.get_cleanup_candidates()
        categories = self.categorize_files(candidates)
        
        print("🔍 프로젝트 정리 미리보기")
        print("=" * 60)
        
        total_files = len(candidates)
        print(f"📊 총 정리 대상: {total_files}개 파일")
        print()
        
        for category, files in categories.items():
            if not files:
                continue
                
            category_names = {
                'keep_useful': '🔧 유용한 스크립트 (scripts/utility로 이동)',
                'archive': '📦 보관용 (scripts/archive로 이동)',
                'delete': '🗑️ 삭제 대상',
                'manual_review': '🤔 수동 검토 필요'
            }
            
            print(f"{category_names[category]} - {len(files)}개")
            for file_path in files:
                print(f"  • {file_path.name}")
            print()
        
        return categories
    
    def execute_cleanup(self, categories, dry_run=True):
        """정리 작업 실행"""
        if dry_run:
            print("🧪 드라이런 모드 - 실제 파일 이동/삭제 안함")
        else:
            print("🚀 실제 정리 작업 실행")
        
        print("=" * 60)
        
        # 유용한 스크립트를 utility로 이동
        for file_path in categories['keep_useful']:
            dest_path = self.utility_dir / file_path.name
            if not dry_run:
                shutil.move(str(file_path), str(dest_path))
            print(f"📦 이동: {file_path.name} → scripts/utility/")
            self.cleanup_log.append(f"MOVED: {file_path.name} → scripts/utility/")
        
        # 보관용을 archive로 이동
        for file_path in categories['archive']:
            dest_path = self.archive_dir / file_path.name
            if not dry_run:
                shutil.move(str(file_path), str(dest_path))
            print(f"📦 보관: {file_path.name} → scripts/archive/")
            self.cleanup_log.append(f"ARCHIVED: {file_path.name} → scripts/archive/")
        
        # 파일 삭제
        for file_path in categories['delete']:
            if not dry_run:
                file_path.unlink()
            print(f"🗑️ 삭제: {file_path.name}")
            self.cleanup_log.append(f"DELETED: {file_path.name}")
        
        # 수동 검토 필요 파일 안내
        if categories['manual_review']:
            print("\n🤔 수동 검토 필요한 파일들:")
            for file_path in categories['manual_review']:
                print(f"  • {file_path.name}")
            print("   → 이 파일들은 직접 확인 후 처리해주세요.")
    
    def save_cleanup_log(self):
        """정리 로그 저장"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'actions': self.cleanup_log,
            'total_processed': len(self.cleanup_log)
        }
        
        log_file = self.scripts_dir / "cleanup_log.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📝 정리 로그 저장: {log_file}")

def main():
    """메인 함수"""
    print("🧹 프로젝트 자동 정리 스크립트")
    print("=" * 60)
    
    cleaner = ProjectCleaner()
    
    # 1. 미리보기
    categories = cleaner.preview_cleanup()
    
    if not any(categories.values()):
        print("✅ 정리할 파일이 없습니다!")
        return
    
    # 2. 사용자 확인
    print("\n❓ 정리 작업을 진행하시겠습니까?")
    print("   1) y/yes - 실제 정리 실행")
    print("   2) d/dry - 드라이런만 실행")
    print("   3) n/no - 취소")
    
    choice = input("\n선택 (y/d/n): ").lower().strip()
    
    if choice in ['y', 'yes']:
        cleaner.execute_cleanup(categories, dry_run=False)
        cleaner.save_cleanup_log()
        print("\n✅ 프로젝트 정리 완료!")
        
    elif choice in ['d', 'dry']:
        cleaner.execute_cleanup(categories, dry_run=True)
        print("\n✅ 드라이런 완료!")
        
    else:
        print("\n❌ 정리 작업 취소됨")

if __name__ == "__main__":
    main()
