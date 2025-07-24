#!/usr/bin/env python3
"""
Components 폴더 의존성 분석 스크립트
정리 과정에서 실제 사용 중인 파일들을 실수로 아카이브한 문제를 분석
"""

import os
import re
from pathlib import Path

def analyze_component_dependencies():
    """components 폴더와 관련 의존성 분석"""
    
    print("🔍 Components 폴더 의존성 분석")
    print("=" * 60)
    
    # 현재 components 폴더 파일들
    components_dir = Path("components")
    current_files = []
    if components_dir.exists():
        current_files = [f.name for f in components_dir.iterdir() if f.suffix == '.py' and f.name != '__init__.py']
    
    # 아카이브된 파일들
    archive_dir = Path("legacy_archive/components_prototypes")
    archived_files = []
    if archive_dir.exists():
        archived_files = [f.name for f in archive_dir.iterdir() if f.suffix == '.py']
    
    print(f"📁 현재 components/ 파일들: {current_files}")
    print(f"📦 아카이브된 파일들: {archived_files}")
    
    # upbit_auto_trading에서 components import 찾기
    print(f"\n🔗 Components import 사용 현황:")
    
    upbit_dir = Path("upbit_auto_trading")
    import_usage = {}
    
    for py_file in upbit_dir.rglob("*.py"):
        try:
            content = py_file.read_text(encoding='utf-8')
            
            # components import 패턴 찾기
            component_imports = re.findall(r'from components\.(\w+) import|import components\.(\w+)', content)
            
            for match in component_imports:
                module_name = match[0] or match[1]
                if module_name:
                    if module_name not in import_usage:
                        import_usage[module_name] = []
                    import_usage[module_name].append(str(py_file))
                    
        except Exception as e:
            print(f"   ⚠️ 파일 읽기 실패: {py_file} - {e}")
    
    for module, files in import_usage.items():
        status = "✅ 존재" if f"{module}.py" in current_files else "❌ 없음"
        if f"{module}.py" in archived_files:
            status += " (아카이브됨)"
        
        print(f"   {status} {module}.py:")
        for file_path in files:
            print(f"      └─ {file_path}")
    
    return import_usage, current_files, archived_files

def check_internal_dependencies(archived_files):
    """아카이브된 파일들 간의 내부 의존성 확인"""
    print(f"\n🔗 아카이브 파일들의 내부 의존성:")
    
    archive_dir = Path("legacy_archive/components_prototypes")
    
    for file_name in archived_files:
        file_path = archive_dir / file_name
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # 같은 components 폴더 내 import 찾기
            internal_imports = re.findall(r'from \.(\w+) import|from components\.(\w+) import', content)
            
            if internal_imports:
                print(f"   📄 {file_name}:")
                for match in internal_imports:
                    dep_module = match[0] or match[1]
                    if dep_module:
                        dep_file = f"{dep_module}.py"
                        if dep_file in archived_files:
                            print(f"      └─ 의존: {dep_file} (아카이브됨)")
                        else:
                            print(f"      └─ 의존: {dep_file} (현재 존재)")
                            
        except Exception as e:
            print(f"   ⚠️ {file_name} 분석 실패: {e}")

def recommend_recovery():
    """복구 권장사항 제시"""
    print(f"\n🎯 복구 권장사항:")
    print("=" * 60)
    
    # 필수 복구 파일들
    essential_files = [
        'condition_dialog.py',
        'condition_loader.py', 
        'parameter_widgets.py'
    ]
    
    print("📥 필수 복구 파일들:")
    for file_name in essential_files:
        print(f"   ✅ {file_name} - 매매전략 관리 화면에서 직접 사용")
    
    print(f"\n💡 복구 명령어:")
    for file_name in essential_files:
        print(f"   Copy-Item \"legacy_archive\\components_prototypes\\{file_name}\" \"components\\\"")
    
    print(f"\n🔄 의존성 체인:")
    print("   integrated_condition_manager.py")
    print("   ├─ condition_dialog.py")
    print("   │  └─ parameter_widgets.py")
    print("   ├─ condition_storage.py ✅")
    print("   └─ condition_loader.py")

def main():
    import_usage, current_files, archived_files = analyze_component_dependencies()
    check_internal_dependencies(archived_files)
    recommend_recovery()
    
    print(f"\n{'='*60}")
    print("📊 분석 요약:")
    print(f"   • 현재 components/ 에 {len(current_files)}개 파일")
    print(f"   • 아카이브에 {len(archived_files)}개 파일") 
    print(f"   • upbit_auto_trading에서 {len(import_usage)}개 모듈 사용 중")
    print("   • 일부 필수 파일들이 실수로 아카이브됨")

if __name__ == "__main__":
    main()
