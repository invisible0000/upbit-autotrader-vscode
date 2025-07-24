#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Components 및 UI Prototypes 폴더 정리 분석 스크립트
- 현재 사용 중인 컴포넌트 vs 프로토타입 파일 분석
- 메인 프로젝트로 통합된 파일 검출
- 정리 추천안 제시
"""

from pathlib import Path
import re

class ComponentsFolderAnalyzer:
    """Components/UI_Prototypes 폴더 분석기"""
    
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.components_dir = self.project_root / "components"
        self.ui_prototypes_dir = self.project_root / "ui_prototypes"
        self.main_ui_dir = self.project_root / "upbit_auto_trading" / "ui"
        
    def analyze_components_usage(self):
        """Components 폴더 사용성 분석"""
        analysis = {
            'active_components': [],      # 현재 메인 프로젝트에서 사용
            'integrated_components': [],   # 메인 프로젝트로 통합됨
            'prototype_components': [],    # 프로토타입 단계
            'outdated_components': [],     # 더 이상 사용 안함
            'unclear_components': []       # 목적 불명확
        }
        
        # Components 폴더 분석
        if self.components_dir.exists():
            component_files = list(self.components_dir.glob("*.py"))
            
            for file_path in component_files:
                filename = file_path.name
                
                if filename == "__init__.py":
                    continue
                
                # 파일 내용 기반 분석
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 메인 UI 폴더에서 사용되는지 확인
                is_imported = self.check_if_imported_in_main_ui(filename)
                
                if filename == 'condition_storage.py':
                    if is_imported:
                        analysis['active_components'].append({
                            'file': filename,
                            'purpose': '조건 저장/관리 핵심 컴포넌트',
                            'status': '메인 프로젝트에서 활발히 사용',
                            'location': 'components/',
                            'recommendation': '유지'
                        })
                    else:
                        analysis['integrated_components'].append({
                            'file': filename,
                            'purpose': '조건 저장/관리 (통합됨)',
                            'status': '메인 프로젝트로 통합 완료',
                            'location': 'components/',
                            'recommendation': '정리 대상'
                        })
                        
                elif filename == 'condition_dialog.py':
                    analysis['integrated_components'].append({
                        'file': filename,
                        'purpose': '조건 다이얼로그 (구버전)',
                        'status': '메인 UI로 통합됨',
                        'location': 'components/',
                        'recommendation': '정리 대상'
                    })
                
                elif filename == 'variable_definitions.py':
                    analysis['active_components'].append({
                        'file': filename,
                        'purpose': '변수 정의 시스템',
                        'status': '현재 사용 중',
                        'location': 'components/',
                        'recommendation': '유지'
                    })
                
                elif filename in ['condition_builder.py', 'condition_validator.py']:
                    if 'class' in content and len(content) > 1000:
                        analysis['integrated_components'].append({
                            'file': filename,
                            'purpose': f'{filename.replace(".py", "")} 기능',
                            'status': '메인 프로젝트로 통합됨',
                            'location': 'components/',
                            'recommendation': '정리 대상'
                        })
                    else:
                        analysis['prototype_components'].append({
                            'file': filename,
                            'purpose': f'{filename.replace(".py", "")} 프로토타입',
                            'status': '프로토타입/미완성',
                            'location': 'components/',
                            'recommendation': '정리 대상'
                        })
                
                elif filename in ['preview_components.py', 'parameter_widgets.py']:
                    analysis['integrated_components'].append({
                        'file': filename,
                        'purpose': f'{filename.replace(".py", "")} 기능',
                        'status': '메인 UI 컴포넌트로 통합됨',
                        'location': 'components/',
                        'recommendation': '정리 대상'
                    })
                
                else:
                    analysis['unclear_components'].append({
                        'file': filename,
                        'purpose': '목적 불명확',
                        'status': '수동 검토 필요',
                        'location': 'components/',
                        'recommendation': '검토 후 결정'
                    })
        
        return analysis
    
    def analyze_ui_prototypes_usage(self):
        """UI Prototypes 폴더 사용성 분석"""
        analysis = {
            'old_prototypes': [],     # 구버전 프로토타입
            'completed_prototypes': [], # 완료된 프로토타입
            'outdated_docs': [],      # 구버전 문서
            'outdated_dbs': []        # 구버전 DB
        }
        
        if self.ui_prototypes_dir.exists():
            prototype_files = list(self.ui_prototypes_dir.iterdir())
            
            for file_path in prototype_files:
                filename = file_path.name
                
                if filename.endswith('.py'):
                    if 'v3' in filename or 'simple' in filename:
                        analysis['old_prototypes'].append({
                            'file': filename,
                            'purpose': 'UI 프로토타입 (구버전)',
                            'status': '메인 UI로 대체됨',
                            'location': 'ui_prototypes/',
                            'recommendation': '삭제'
                        })
                    else:
                        analysis['completed_prototypes'].append({
                            'file': filename,
                            'purpose': 'UI 프로토타입 (완료)',
                            'status': '개발 완료됨',
                            'location': 'ui_prototypes/',
                            'recommendation': '아카이브'
                        })
                
                elif filename.endswith('.md'):
                    if 'guide' in filename.lower() or 'readme' in filename.lower():
                        analysis['outdated_docs'].append({
                            'file': filename,
                            'purpose': '프로토타입 문서',
                            'status': '구버전 가이드',
                            'location': 'ui_prototypes/',
                            'recommendation': 'docs로 이동 또는 삭제'
                        })
                
                elif filename.endswith('.db'):
                    analysis['outdated_dbs'].append({
                        'file': filename,
                        'purpose': '프로토타입용 DB',
                        'status': '통합 DB 이후 불필요',
                        'location': 'ui_prototypes/',
                        'recommendation': '삭제'
                    })
        
        return analysis
    
    def check_if_imported_in_main_ui(self, filename):
        """메인 UI에서 해당 파일이 import되는지 확인"""
        try:
            if not self.main_ui_dir.exists():
                return False
                
            # 메인 UI 폴더의 모든 .py 파일 검사
            for py_file in self.main_ui_dir.rglob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        module_name = filename.replace('.py', '')
                        if f"from components.{module_name}" in content or f"import components.{module_name}" in content:
                            return True
                except:
                    continue
            return False
        except:
            return False
    
    def generate_cleanup_recommendations(self):
        """정리 추천안 생성"""
        components_analysis = self.analyze_components_usage()
        prototypes_analysis = self.analyze_ui_prototypes_usage()
        
        recommendations = {
            'keep_active': [],        # 유지할 활성 컴포넌트
            'move_to_archive': [],    # 아카이브로 이동
            'move_to_docs': [],       # docs로 이동
            'delete_safe': [],        # 안전하게 삭제
            'manual_review': []       # 수동 검토
        }
        
        # Components 분석 결과 처리
        for item in components_analysis['active_components']:
            recommendations['keep_active'].append(item)
        
        for item in components_analysis['integrated_components']:
            recommendations['move_to_archive'].append(item)
        
        for item in components_analysis['prototype_components']:
            recommendations['delete_safe'].append(item)
        
        for item in components_analysis['outdated_components']:
            recommendations['delete_safe'].append(item)
        
        for item in components_analysis['unclear_components']:
            recommendations['manual_review'].append(item)
        
        # UI Prototypes 분석 결과 처리
        for item in prototypes_analysis['old_prototypes']:
            recommendations['delete_safe'].append(item)
        
        for item in prototypes_analysis['completed_prototypes']:
            recommendations['move_to_archive'].append(item)
        
        for item in prototypes_analysis['outdated_docs']:
            recommendations['move_to_docs'].append(item)
        
        for item in prototypes_analysis['outdated_dbs']:
            recommendations['delete_safe'].append(item)
        
        return recommendations, components_analysis, prototypes_analysis
    
    def print_analysis_report(self):
        """분석 보고서 출력"""
        print("🔍 Components & UI Prototypes 폴더 정리 분석")
        print("=" * 60)
        
        recommendations, components_analysis, prototypes_analysis = self.generate_cleanup_recommendations()
        
        # Components 폴더 분석
        print("📁 Components 폴더 분석:")
        total_components = sum(len(category) for category in components_analysis.values())
        print(f"   총 {total_components}개 파일")
        
        categories = {
            'active_components': '✅ 활성 사용',
            'integrated_components': '🔄 통합 완료', 
            'prototype_components': '⚡ 프로토타입',
            'outdated_components': '📦 구버전',
            'unclear_components': '❓ 불명확'
        }
        
        for category, files in components_analysis.items():
            if files:
                print(f"   {categories[category]}: {len(files)}개")
                for item in files:
                    print(f"     • {item['file']} - {item['purpose']}")
        
        print()
        
        # UI Prototypes 폴더 분석
        print("📁 UI Prototypes 폴더 분석:")
        total_prototypes = sum(len(category) for category in prototypes_analysis.values())
        print(f"   총 {total_prototypes}개 파일")
        
        proto_categories = {
            'old_prototypes': '📦 구버전',
            'completed_prototypes': '✅ 완료됨',
            'outdated_docs': '📄 구문서',
            'outdated_dbs': '💾 구DB'
        }
        
        for category, files in prototypes_analysis.items():
            if files:
                print(f"   {proto_categories[category]}: {len(files)}개")
                for item in files:
                    print(f"     • {item['file']} - {item['purpose']}")
        
        print("\n" + "=" * 60)
        print("💡 정리 추천안")
        print("=" * 60)
        
        rec_categories = {
            'keep_active': '✅ 유지 (활성)',
            'move_to_archive': '📦 아카이브 이동',
            'move_to_docs': '📚 docs 이동',
            'delete_safe': '🗑️ 안전 삭제',
            'manual_review': '🤔 수동 검토'
        }
        
        for category, files in recommendations.items():
            if files:
                print(f"\n{rec_categories[category]} - {len(files)}개")
                for item in files:
                    print(f"  • {item['file']} ({item['location']})")
        
        return recommendations
    
    def execute_cleanup_plan(self, recommendations, dry_run=True):
        """정리 계획 실행"""
        if dry_run:
            print("\n🧪 드라이런 모드 - 실제 파일 이동/삭제 안함")
        else:
            print("\n🚀 실제 정리 작업 실행")
        
        print("=" * 60)
        
        # 아카이브로 이동
        archive_dir = Path("legacy_archive/components_prototypes")
        if not dry_run:
            archive_dir.mkdir(parents=True, exist_ok=True)
        
        for item in recommendations['move_to_archive']:
            if item['location'] == 'components/':
                src_path = self.components_dir / item['file']
            else:
                src_path = self.ui_prototypes_dir / item['file']
            
            dest_path = archive_dir / item['file']
            
            if src_path.exists():
                if not dry_run:
                    import shutil
                    shutil.move(str(src_path), str(dest_path))
                print(f"📦 아카이브: {item['file']} → legacy_archive/components_prototypes/")
        
        # docs로 이동
        docs_dir = Path("docs")
        for item in recommendations['move_to_docs']:
            src_path = self.ui_prototypes_dir / item['file']
            dest_path = docs_dir / item['file']
            
            if src_path.exists():
                if not dry_run:
                    import shutil
                    shutil.move(str(src_path), str(dest_path))
                print(f"📚 docs 이동: {item['file']} → docs/")
        
        # 삭제
        for item in recommendations['delete_safe']:
            if item['location'] == 'components/':
                file_path = self.components_dir / item['file']
            else:
                file_path = self.ui_prototypes_dir / item['file']
            
            if file_path.exists():
                if not dry_run:
                    file_path.unlink()
                print(f"🗑️ 삭제: {item['file']} ({item['purpose']})")
        
        print(f"\n📈 정리 결과:")
        print(f"  • 유지: {len(recommendations['keep_active'])}개")
        print(f"  • 아카이브: {len(recommendations['move_to_archive'])}개")
        print(f"  • docs 이동: {len(recommendations['move_to_docs'])}개")
        print(f"  • 삭제: {len(recommendations['delete_safe'])}개")
        print(f"  • 수동검토: {len(recommendations['manual_review'])}개")

def main():
    """메인 함수"""
    analyzer = ComponentsFolderAnalyzer()
    
    # 분석 보고서 출력
    recommendations = analyzer.print_analysis_report()
    
    # 사용자 확인
    print("\n❓ Components & UI Prototypes 폴더 정리를 진행하시겠습니까?")
    print("   1) y/yes - 실제 정리 실행")
    print("   2) d/dry - 드라이런만 실행")
    print("   3) n/no - 취소")
    
    choice = input("\n선택 (y/d/n): ").lower().strip()
    
    if choice in ['y', 'yes']:
        analyzer.execute_cleanup_plan(recommendations, dry_run=False)
        print("\n✅ Components & UI Prototypes 폴더 정리 완료!")
        
    elif choice in ['d', 'dry']:
        analyzer.execute_cleanup_plan(recommendations, dry_run=True)
        print("\n✅ 드라이런 완료!")
        
    else:
        print("\n❌ 정리 작업 취소됨")

if __name__ == "__main__":
    main()
