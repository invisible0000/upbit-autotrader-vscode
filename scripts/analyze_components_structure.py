#!/usr/bin/env python3
"""
두 components 폴더 비교 분석 스크립트
- 메인 루트의 components/ 폴더
- strategy_management/components/ 폴더
어떤 것이 실제로 사용되고 있는지 역추적
"""

import os
import re
from pathlib import Path
import hashlib

def get_file_hash(file_path):
    """파일 해시 계산"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def analyze_two_components_folders():
    """두 components 폴더 비교 분석"""
    
    print("🔍 두 Components 폴더 비교 분석")
    print("=" * 70)
    
    # 두 폴더 경로
    root_components = Path("components")
    strategy_components = Path("upbit_auto_trading/ui/desktop/screens/strategy_management/components")
    
    # 각 폴더의 파일 목록
    root_files = {}
    strategy_files = {}
    
    if root_components.exists():
        for f in root_components.iterdir():
            if f.suffix == '.py' and f.name != '__init__.py':
                root_files[f.name] = {
                    'path': str(f),
                    'size': f.stat().st_size,
                    'hash': get_file_hash(f)
                }
    
    if strategy_components.exists():
        for f in strategy_components.iterdir():
            if f.suffix == '.py' and f.name != '__init__.py':
                strategy_files[f.name] = {
                    'path': str(f),
                    'size': f.stat().st_size,
                    'hash': get_file_hash(f)
                }
    
    print(f"📁 메인 루트 components/: {len(root_files)}개 파일")
    print(f"📁 strategy_management/components/: {len(strategy_files)}개 파일")
    
    # 파일별 비교
    all_files = set(root_files.keys()) | set(strategy_files.keys())
    
    print(f"\n📊 파일별 비교:")
    for filename in sorted(all_files):
        root_exists = filename in root_files
        strategy_exists = filename in strategy_files
        
        if root_exists and strategy_exists:
            # 두 곳 모두 존재 - 해시 비교
            root_hash = root_files[filename]['hash']
            strategy_hash = strategy_files[filename]['hash']
            
            if root_hash == strategy_hash:
                print(f"   🟢 {filename}: 두 폴더에 동일 파일 존재")
            else:
                print(f"   🟡 {filename}: 두 폴더에 다른 버전 존재")
                print(f"      ├─ 루트: {root_files[filename]['size']} bytes")
                print(f"      └─ 전략: {strategy_files[filename]['size']} bytes")
        elif root_exists:
            print(f"   🔵 {filename}: 루트에만 존재")
        elif strategy_exists:
            print(f"   🟣 {filename}: 전략 폴더에만 존재")
    
    return root_files, strategy_files, all_files

def analyze_import_patterns():
    """import 패턴 분석 - 어떤 components를 사용하는지"""
    
    print(f"\n🔗 Import 패턴 분석:")
    print("=" * 70)
    
    # strategy_management 관련 파일들에서 import 분석
    strategy_management_dir = Path("upbit_auto_trading/ui/desktop/screens/strategy_management")
    
    import_patterns = {
        'root_components': [],  # from components.xxx import
        'strategy_components': [],  # from .components.xxx import or 상대경로
        'other_imports': []
    }
    
    for py_file in strategy_management_dir.rglob("*.py"):
        try:
            content = py_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # 루트 components import
                if re.search(r'from components\.', line):
                    import_patterns['root_components'].append({
                        'file': str(py_file.relative_to(Path('.'))),
                        'line': i + 1,
                        'import': line
                    })
                
                # 로컬 components import  
                elif re.search(r'from \.components\.|from .components import', line):
                    import_patterns['strategy_components'].append({
                        'file': str(py_file.relative_to(Path('.'))),
                        'line': i + 1,
                        'import': line
                    })
                
                # 기타 components 관련 import
                elif 'components' in line and ('import' in line or 'from' in line):
                    import_patterns['other_imports'].append({
                        'file': str(py_file.relative_to(Path('.'))),
                        'line': i + 1,
                        'import': line
                    })
                    
        except Exception as e:
            print(f"   ⚠️ 파일 읽기 실패: {py_file} - {e}")
    
    # 결과 출력
    print(f"🔴 루트 components/ 사용: {len(import_patterns['root_components'])}개")
    for item in import_patterns['root_components']:
        print(f"   📄 {item['file']}:{item['line']} - {item['import']}")
    
    print(f"\n🟢 로컬 components/ 사용: {len(import_patterns['strategy_components'])}개")
    for item in import_patterns['strategy_components']:
        print(f"   📄 {item['file']}:{item['line']} - {item['import']}")
    
    print(f"\n🟡 기타 components 관련: {len(import_patterns['other_imports'])}개")
    for item in import_patterns['other_imports']:
        print(f"   📄 {item['file']}:{item['line']} - {item['import']}")
    
    return import_patterns

def check_git_history():
    """Git 히스토리에서 components 폴더 변경 추적"""
    print(f"\n📜 Git 히스토리 분석:")
    print("=" * 70)
    
    try:
        import subprocess
        
        # components 폴더 관련 최근 커밋 확인
        result = subprocess.run([
            'git', 'log', '--oneline', '-10', '--', 'components/', 
            'upbit_auto_trading/ui/desktop/screens/strategy_management/components/'
        ], capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0 and result.stdout:
            print("📝 최근 components 관련 커밋들:")
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")
        else:
            print("📝 Git 히스토리를 찾을 수 없습니다.")
            
    except Exception as e:
        print(f"⚠️ Git 히스토리 확인 실패: {e}")

def recommend_solution():
    """해결 방안 제안"""
    print(f"\n🎯 분석 결과 및 해결 방안:")
    print("=" * 70)
    
    print("🔍 발견된 문제:")
    print("   • 두 개의 components 폴더가 존재")
    print("   • 루트 components/에서 import하는 코드 존재")
    print("   • strategy_management/components/가 정식 구조")
    
    print(f"\n💡 해결 방안:")
    print("   1. 루트 components/ 사용을 로컬 components/로 변경")
    print("   2. import 경로 수정: from components.xxx → from .components.xxx")
    print("   3. 루트 components/ 폴더 완전 제거")
    print("   4. 누락된 파일이 있다면 strategy_management/components/에 추가")

def main():
    print("🔍 Components 폴더 구조 역추적 분석")
    print("=" * 70)
    
    # 1. 두 폴더 비교
    root_files, strategy_files, all_files = analyze_two_components_folders()
    
    # 2. Import 패턴 분석
    import_patterns = analyze_import_patterns()
    
    # 3. Git 히스토리 확인
    check_git_history()
    
    # 4. 해결 방안 제안
    recommend_solution()
    
    print(f"\n{'='*70}")
    print("📊 종합 분석:")
    print(f"   • 루트 components/: {len(root_files)}개 파일")
    print(f"   • 전략 components/: {len(strategy_files)}개 파일")
    print(f"   • 루트 import 사용: {len(import_patterns['root_components'])}곳")
    print(f"   • 로컬 import 사용: {len(import_patterns['strategy_components'])}곳")

if __name__ == "__main__":
    main()
