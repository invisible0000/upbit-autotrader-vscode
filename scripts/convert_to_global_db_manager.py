#!/usr/bin/env python3
"""
전역 DB 매니저 마이그레이션 스크립트
모든 sqlite3.connect 호출을 전역 매니저로 변경
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


class GlobalDBMigrator:
    """전역 DB 매니저로 마이그레이션하는 도구"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.target_patterns = [
            r'sqlite3\.connect\([^)]+\)',  # sqlite3.connect() 호출
            r'with sqlite3\.connect\([^)]+\) as',  # with문 패턴
        ]
        
    def find_python_files(self) -> List[Path]:
        """Python 파일들 찾기"""
        python_files = []
        
        # upbit_auto_trading 폴더 내 모든 .py 파일
        upbit_folder = self.project_root / "upbit_auto_trading"
        if upbit_folder.exists():
            for py_file in upbit_folder.rglob("*.py"):
                # __pycache__ 폴더 제외
                if "__pycache__" not in str(py_file):
                    python_files.append(py_file)
                    
        return python_files
    
    def analyze_file(self, file_path: Path) -> List[Tuple[int, str]]:
        """파일에서 sqlite3.connect 호출 찾기"""
        matches = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                for pattern in self.target_patterns:
                    if re.search(pattern, line):
                        matches.append((line_num, line.strip()))
                        
        except Exception as e:
            print(f"⚠️ 파일 읽기 오류: {file_path} - {e}")
            
        return matches
    
    def generate_migration_report(self):
        """마이그레이션 보고서 생성"""
        print("🔍 전역 DB 매니저 마이그레이션 분석")
        print("=" * 60)
        
        python_files = self.find_python_files()
        total_matches = 0
        priority_files = []
        
        for file_path in python_files:
            matches = self.analyze_file(file_path)
            
            if matches:
                total_matches += len(matches)
                relative_path = file_path.relative_to(self.project_root)
                
                # 우선순위 파일 분류
                if any(keyword in str(file_path) for keyword in [
                    'condition_storage', 'variable_manager', 'real_data_simulation',
                    'database_manager', 'trading_variables'
                ]):
                    priority_files.append((relative_path, matches))
                
                print(f"\n📁 {relative_path}")
                print(f"   발견된 DB 호출: {len(matches)}개")
                
                for line_num, line in matches:
                    print(f"   📍 라인 {line_num}: {line}")
        
        print(f"\n📊 총 요약:")
        print(f"   - 분석된 파일: {len(python_files)}개")
        print(f"   - 발견된 DB 호출: {total_matches}개")
        print(f"   - 우선순위 파일: {len(priority_files)}개")
        
        print(f"\n🎯 우선 수정 권장 파일들:")
        for file_path, matches in priority_files:
            print(f"   - {file_path} ({len(matches)}개 호출)")
            
        return priority_files
    
    def generate_migration_template(self, file_path: Path):
        """개별 파일 마이그레이션 템플릿 생성"""
        print(f"\n🔧 {file_path} 마이그레이션 가이드:")
        print("-" * 40)
        
        print("1. 파일 상단에 임포트 추가:")
        print("""
# 전역 DB 매니저 임포트
try:
    from upbit_auto_trading.utils.global_db_manager import get_db_connection
    USE_GLOBAL_MANAGER = True
except ImportError:
    print("⚠️ 전역 DB 매니저를 사용할 수 없습니다. 기존 방식을 사용합니다.")
    USE_GLOBAL_MANAGER = False
""")
        
        print("2. 클래스 초기화에 플래그 추가:")
        print("""
def __init__(self, db_path: str = "..."):
    self.db_path = db_path  # 레거시 호환성
    self.use_global_manager = USE_GLOBAL_MANAGER
""")
        
        print("3. 연결 헬퍼 메소드 추가:")
        print("""
def _get_connection(self):
    '''DB 연결 반환 - 전역 매니저 또는 기존 방식'''
    if self.use_global_manager:
        return get_db_connection('테이블명')  # 적절한 테이블명으로 변경
    else:
        return sqlite3.connect(self.db_path)
""")
        
        print("4. 모든 sqlite3.connect() 호출을 self._get_connection()으로 변경")


def main():
    """메인 실행"""
    migrator = GlobalDBMigrator()
    priority_files = migrator.generate_migration_report()
    
    print(f"\n🚀 마이그레이션 실행 계획:")
    print("=" * 60)
    print("1. 우선순위 파일부터 차례대로 수정")
    print("2. 각 파일마다 테스트 실행")
    print("3. 점진적으로 전체 시스템에 적용")
    print("4. 기존 호환성 유지하며 안전하게 전환")
    
    # 템플릿 예시
    if priority_files:
        sample_file = priority_files[0][0]
        migrator.generate_migration_template(sample_file)
    
    print(f"\n✅ 분석 완료! 우선순위 파일부터 수정을 시작하세요.")


if __name__ == "__main__":
    main()
