#!/usr/bin/env python3
"""
Strategy Management 레거시 파일 분석 도구
"""

import os
import sys
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple

class LegacyFileAnalyzer:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.strategy_management_path = self.base_path / "upbit_auto_trading/ui/desktop/screens/strategy_management"
        self.trigger_builder_path = self.strategy_management_path / "trigger_builder"
        
        # 현재 활성 사용 파일들 (trigger_builder 기반)
        self.active_files = set()
        self.legacy_candidates = set()
        self.import_graph = {}
        
    def analyze_imports_in_file(self, file_path: Path) -> List[str]:
        """파일의 import 문들을 분석"""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
                
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                        
        except Exception as e:
            print(f"⚠️ 파일 분석 실패: {file_path} - {e}")
        
        return imports
    
    def find_all_python_files(self) -> List[Path]:
        """모든 Python 파일 찾기"""
        python_files = []
        for root, dirs, files in os.walk(self.strategy_management_path):
            # __pycache__ 제외
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    python_files.append(Path(root) / file)
        
        return python_files
    
    def analyze_active_imports(self):
        """현재 활성화된 파일들의 import 관계 분석"""
        print("📊 활성 파일 import 관계 분석 중...")
        
        # trigger_builder_screen.py를 시작점으로 분석
        trigger_builder_screen = self.trigger_builder_path / "trigger_builder_screen.py"
        if trigger_builder_screen.exists():
            self.active_files.add(trigger_builder_screen)
            self._trace_imports_recursively(trigger_builder_screen)
        
        # strategy_management_screen.py도 확인
        strategy_screen = self.strategy_management_path / "strategy_management_screen.py"
        if strategy_screen.exists():
            self.active_files.add(strategy_screen)
            self._trace_imports_recursively(strategy_screen)
            
    def _trace_imports_recursively(self, file_path: Path, visited: Set[Path] = None):
        """재귀적으로 import된 파일들 추적"""
        if visited is None:
            visited = set()
            
        if file_path in visited:
            return
            
        visited.add(file_path)
        imports = self.analyze_imports_in_file(file_path)
        self.import_graph[str(file_path)] = imports
        
        for import_name in imports:
            # 상대 import 처리
            if import_name.startswith('.'):
                # 상대 경로 처리
                relative_path = self._resolve_relative_import(file_path, import_name)
                if relative_path and relative_path.exists():
                    self.active_files.add(relative_path)
                    self._trace_imports_recursively(relative_path, visited)
    
    def _resolve_relative_import(self, current_file: Path, import_name: str) -> Path:
        """상대 import를 절대 경로로 변환"""
        try:
            current_dir = current_file.parent
            import_parts = import_name.split('.')
            
            # . 개수만큼 상위 디렉토리로
            for part in import_parts:
                if part == '':  # '.'의 경우
                    current_dir = current_dir.parent
                else:
                    # 실제 모듈/파일 이름
                    potential_file = current_dir / f"{part}.py"
                    potential_dir = current_dir / part
                    
                    if potential_file.exists():
                        return potential_file
                    elif potential_dir.exists():
                        init_file = potential_dir / "__init__.py"
                        if init_file.exists():
                            return init_file
                        current_dir = potential_dir
                    else:
                        break
                        
            return None
        except Exception:
            return None
    
    def identify_legacy_files(self):
        """레거시 파일들 식별"""
        print("🔍 레거시 파일 식별 중...")
        
        all_files = self.find_all_python_files()
        
        for file_path in all_files:
            if file_path not in self.active_files:
                # 추가 검증: 파일이 실제로 어디서도 사용되지 않는지 확인
                if self._is_truly_unused(file_path):
                    self.legacy_candidates.add(file_path)
    
    def _is_truly_unused(self, file_path: Path) -> bool:
        """파일이 실제로 사용되지 않는지 추가 검증"""
        file_name = file_path.stem
        
        # 전체 프로젝트에서 해당 파일을 import하는지 검색
        for root, dirs, files in os.walk(self.base_path):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                if file.endswith('.py'):
                    try:
                        full_path = Path(root) / file
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # 파일명이 import 문에 포함되어 있는지 확인
                        if file_name in content and 'import' in content:
                            # 더 정확한 검증이 필요하지만 보수적으로 사용중으로 판단
                            return False
                            
                    except Exception:
                        continue
        
        return True
    
    def generate_report(self):
        """분석 보고서 생성"""
        print("\n" + "="*60)
        print("🎯 Strategy Management 레거시 파일 분석 보고서")
        print("="*60)
        
        print(f"\n✅ 활성 사용 중인 파일들 ({len(self.active_files)}개):")
        for file_path in sorted(self.active_files):
            rel_path = file_path.relative_to(self.strategy_management_path)
            print(f"   📄 {rel_path}")
        
        print(f"\n⚠️ 레거시 후보 파일들 ({len(self.legacy_candidates)}개):")
        components_legacy = []
        root_legacy = []
        
        for file_path in sorted(self.legacy_candidates):
            rel_path = file_path.relative_to(self.strategy_management_path)
            if 'components' in str(rel_path):
                components_legacy.append(rel_path)
            else:
                root_legacy.append(rel_path)
        
        print(f"\n   📁 Components 레거시 ({len(components_legacy)}개):")
        for rel_path in components_legacy:
            print(f"      🗃️ {rel_path}")
            
        print(f"\n   📁 Root 레거시 ({len(root_legacy)}개):")
        for rel_path in root_legacy:
            print(f"      🗃️ {rel_path}")
        
        return {
            'active_files': self.active_files,
            'legacy_candidates': self.legacy_candidates,
            'components_legacy': [self.strategy_management_path / p for p in components_legacy],
            'root_legacy': [self.strategy_management_path / p for p in root_legacy]
        }

def main():
    base_path = "."
    analyzer = LegacyFileAnalyzer(base_path)
    
    print("🔍 Strategy Management 디렉토리 레거시 파일 분석 시작...")
    
    # 분석 실행
    analyzer.analyze_active_imports()
    analyzer.identify_legacy_files()
    
    # 보고서 생성
    results = analyzer.generate_report()
    
    print(f"\n📋 분석 완료!")
    print(f"   - 활성 파일: {len(results['active_files'])}개")
    print(f"   - 레거시 후보: {len(results['legacy_candidates'])}개")
    
    return results

if __name__ == "__main__":
    results = main()
