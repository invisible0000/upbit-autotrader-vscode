#!/usr/bin/env python3
"""
수상한 폴더들 분석 및 정리 스크립트
- sample_QA_Automation: QA 자동화 테스트 관련
- reference: 설계 문서 및 스펙 문서들
- mail: COPILOT 개발 진행 상황 문서들 (mail이라는 이름이 부적절)
"""

import os
import shutil
from pathlib import Path

def analyze_folder_structure():
    """수상한 폴더들의 구조 분석"""
    base_dir = Path(".")
    
    folders_to_analyze = {
        'sample_QA_Automation': '품질보증 자동화 테스트',
        'reference': '레퍼런스 및 설계 문서',
        'mail': '개발 진행 상황 문서 (잘못된 네이밍)'
    }
    
    print("🔍 수상한 폴더들 분석 시작...")
    print("=" * 60)
    
    analysis_results = {}
    
    for folder_name, description in folders_to_analyze.items():
        folder_path = base_dir / folder_name
        if folder_path.exists():
            print(f"\n📁 {folder_name}/ ({description})")
            files = list(folder_path.rglob('*'))
            file_count = len([f for f in files if f.is_file()])
            dir_count = len([f for f in files if f.is_dir()])
            
            print(f"   • 파일 수: {file_count}")
            print(f"   • 디렉토리 수: {dir_count}")
            
            # 파일 타입 분석
            extensions = {}
            for file_path in files:
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    extensions[ext] = extensions.get(ext, 0) + 1
            
            print(f"   • 파일 타입: {dict(extensions)}")
            
            # 주요 파일들 표시
            main_files = [f.name for f in folder_path.iterdir() if f.is_file()][:5]
            print(f"   • 주요 파일들: {main_files}")
            
            analysis_results[folder_name] = {
                'file_count': file_count,
                'dir_count': dir_count,
                'extensions': extensions,
                'main_files': main_files
            }
        else:
            print(f"❌ {folder_name}/ 폴더가 존재하지 않습니다.")
    
    return analysis_results

def recommend_actions():
    """정리 방안 제안"""
    print("\n" + "=" * 60)
    print("🎯 정리 방안 제안")
    print("=" * 60)
    
    recommendations = {
        'sample_QA_Automation': {
            'action': 'tests/ 폴더로 통합',
            'reason': 'QA 자동화는 일반 테스트와 함께 관리하는 것이 효율적',
            'destination': 'tests/qa_automation/',
            'keep_files': ['README.md', 'run_tests.py', 'requirements.txt']
        },
        'reference': {
            'action': 'docs/ 폴더로 통합', 
            'reason': '설계 문서와 스펙은 일반 문서와 함께 관리',
            'destination': 'docs/reference/',
            'keep_files': '모든 .md 파일들'
        },
        'mail': {
            'action': 'docs/progress/ 로 이름 변경 후 이동',
            'reason': 'mail이라는 이름이 부적절, 개발 진행 문서로 명확히 구분',
            'destination': 'docs/progress/',
            'keep_files': '모든 COPILOT_*.md 파일들'
        }
    }
    
    for folder, rec in recommendations.items():
        print(f"\n📁 {folder}/")
        print(f"   🎯 액션: {rec['action']}")
        print(f"   💡 이유: {rec['reason']}")
        print(f"   📂 목적지: {rec['destination']}")
        print(f"   📄 보관 파일: {rec['keep_files']}")
    
    return recommendations

def execute_reorganization():
    """실제 정리 실행"""
    base_dir = Path(".")
    
    # 필요한 디렉토리 생성
    directories_to_create = [
        'tests/qa_automation',
        'docs/reference', 
        'docs/progress'
    ]
    
    for dir_path in directories_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"📁 생성: {dir_path}/")
    
    print("\n🚀 폴더 재구성 시작...")
    
    # 1. sample_QA_Automation -> tests/qa_automation
    qa_source = base_dir / 'sample_QA_Automation'
    qa_dest = base_dir / 'tests' / 'qa_automation'
    
    if qa_source.exists():
        print(f"\n📦 이동: sample_QA_Automation/ → tests/qa_automation/")
        for item in qa_source.iterdir():
            dest_path = qa_dest / item.name
            if item.is_dir():
                shutil.copytree(item, dest_path, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest_path)
            print(f"   ✅ {item.name}")
    
    # 2. reference -> docs/reference
    ref_source = base_dir / 'reference'  
    ref_dest = base_dir / 'docs' / 'reference'
    
    if ref_source.exists():
        print(f"\n📦 이동: reference/ → docs/reference/")
        for item in ref_source.iterdir():
            dest_path = ref_dest / item.name
            if item.is_dir():
                shutil.copytree(item, dest_path, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest_path)
            print(f"   ✅ {item.name}")
    
    # 3. mail -> docs/progress (이름 변경 의미)
    mail_source = base_dir / 'mail'
    progress_dest = base_dir / 'docs' / 'progress'
    
    if mail_source.exists():
        print(f"\n📦 이동: mail/ → docs/progress/ (이름 명확화)")
        for item in mail_source.iterdir():
            dest_path = progress_dest / item.name
            if item.is_dir():
                shutil.copytree(item, dest_path, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest_path)
            print(f"   ✅ {item.name}")
    
    return True

def cleanup_empty_folders():
    """빈 폴더들 정리"""
    folders_to_remove = ['sample_QA_Automation', 'reference', 'mail']
    
    print("\n🗑️ 원본 폴더 정리...")
    for folder_name in folders_to_remove:
        folder_path = Path(folder_name)
        if folder_path.exists():
            try:
                shutil.rmtree(folder_path)
                print(f"   ✅ 삭제: {folder_name}/")
            except Exception as e:
                print(f"   ❌ 삭제 실패: {folder_name}/ - {e}")

def main():
    print("🔍 수상한 폴더들 분석 및 정리")
    print("=" * 60)
    
    # 1. 분석
    results = analyze_folder_structure()
    
    # 2. 제안
    recommendations = recommend_actions()
    
    # 3. 실행 확인
    print(f"\n{'='*60}")
    response = input("🤔 정리를 실행하시겠습니까? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        print("\n🚀 정리 실행 중...")
        
        # 실행
        if execute_reorganization():
            cleanup_empty_folders()
            
            print(f"\n{'='*60}")
            print("✅ 폴더 정리 완료!")
            print("\n📊 정리 결과:")
            print("   • sample_QA_Automation/ → tests/qa_automation/")
            print("   • reference/ → docs/reference/") 
            print("   • mail/ → docs/progress/ (이름 명확화)")
            print("\n🎯 다음 단계:")
            print("   • tests/qa_automation/ 에서 QA 자동화 테스트 관리")
            print("   • docs/reference/ 에서 설계 문서 참조")
            print("   • docs/progress/ 에서 개발 진행 상황 추적")
    else:
        print("❌ 정리가 취소되었습니다.")

if __name__ == "__main__":
    main()
