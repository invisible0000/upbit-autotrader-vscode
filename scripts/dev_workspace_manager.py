#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개발 환경 격리 및 복구 지점 관리 스크립트
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


def create_backup_commit(feature_name):
    """복구 지점 Git 커밋 생성"""
    print(f"🔄 복구 지점 생성: {feature_name}")
    
    try:
        # Git 상태 확인
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            # 변경사항이 있으면 커밋
            subprocess.run(['git', 'add', '-A'], check=True)
            commit_msg = f"feat: 복구 지점 - {feature_name} 개발 시작 전"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            subprocess.run(['git', 'push'], check=True)
            print("✅ 복구 지점 커밋 완료")
        else:
            print("✅ 변경사항 없음 - 이미 깨끗한 상태")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Git 작업 실패: {e}")
        return False
    
    return True


def create_dev_workspace(feature_name, source_files=None):
    """개발용 격리 폴더 생성"""
    print(f"📁 개발 환경 구성: {feature_name}")
    
    # 개발 폴더 경로
    dev_root = Path("dev_workspace")
    feature_dir = dev_root / f"{feature_name}_dev"
    
    # 폴더 생성
    feature_dir.mkdir(parents=True, exist_ok=True)
    
    # README 파일 생성
    readme_content = f"""# {feature_name} 개발 환경

## 📅 생성일시
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📝 개발 메모
- 기능 설명: {feature_name}
- 개발 시작일: {datetime.now().strftime('%Y-%m-%d')}
- 상태: 개발 중

## 🔧 개발 완료 후 할 일
1. 완성된 코드를 원래 위치로 이동
2. 테스트 스크립트 정리
3. 최종 커밋 및 푸시
4. 이 폴더 삭제

## 📁 복사된 파일들
"""
    
    if source_files:
        readme_content += "\n".join(f"- {file}" for file in source_files)
        
        # 소스 파일들 복사
        for source_file in source_files:
            source_path = Path(source_file)
            if source_path.exists():
                dest_path = feature_dir / source_path.name
                shutil.copy2(source_path, dest_path)
                print(f"📄 복사: {source_file} → {dest_path}")
            else:
                print(f"⚠️ 파일 없음: {source_file}")
    
    readme_path = feature_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✅ 개발 환경 생성 완료: {feature_dir}")
    return feature_dir


def complete_development(feature_name, target_location=None):
    """개발 완료 후 통합 및 정리"""
    print(f"🎯 개발 완료 처리: {feature_name}")
    
    dev_root = Path("dev_workspace")
    feature_dir = dev_root / f"{feature_name}_dev"
    
    if not feature_dir.exists():
        print(f"❌ 개발 폴더 없음: {feature_dir}")
        return False
    
    print(f"📁 개발 폴더: {feature_dir}")
    
    # 개발된 파일 목록 확인
    dev_files = list(feature_dir.glob("*.py"))
    if not dev_files:
        print("⚠️ 개발된 Python 파일이 없습니다.")
        return False
    
    print("📄 개발된 파일들:")
    for file_path in dev_files:
        if file_path.name != "README.md":
            print(f"  • {file_path.name}")
    
    # 파일 이동 여부 확인
    if target_location:
        target_dir = Path(target_location)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        choice = input(f"\n❓ 파일들을 {target_location}로 이동하시겠습니까? (y/n): ")
        if choice.lower() == 'y':
            for file_path in dev_files:
                if file_path.name.endswith('.py'):
                    dest_path = target_dir / file_path.name
                    shutil.move(str(file_path), str(dest_path))
                    print(f"📦 이동: {file_path.name} → {dest_path}")
    
    # 개발 폴더 삭제 여부 확인
    choice = input(f"\n❓ 개발 폴더를 삭제하시겠습니까? (y/n): ")
    if choice.lower() == 'y':
        shutil.rmtree(feature_dir)
        print(f"🗑️ 개발 폴더 삭제: {feature_dir}")
    
    # 최종 커밋
    choice = input(f"\n❓ 최종 커밋을 생성하시겠습니까? (y/n): ")
    if choice.lower() == 'y':
        try:
            subprocess.run(['git', 'add', '-A'], check=True)
            commit_msg = f"feat: {feature_name} 완성 및 코드 정리"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            subprocess.run(['git', 'push'], check=True)
            print("✅ 최종 커밋 완료")
        except subprocess.CalledProcessError as e:
            print(f"❌ Git 커밋 실패: {e}")
    
    return True


def list_dev_workspaces():
    """개발 환경 목록 표시"""
    dev_root = Path("dev_workspace")
    
    if not dev_root.exists():
        print("📁 개발 환경 폴더가 없습니다.")
        return
    
    workspaces = list(dev_root.glob("*_dev"))
    
    if not workspaces:
        print("📁 활성 개발 환경이 없습니다.")
        return
    
    print("📁 활성 개발 환경 목록:")
    for workspace in workspaces:
        readme_path = workspace / "README.md"
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "생성일시" in content:
                    # 생성일시 추출
                    for line in content.split('\n'):
                        if "생성일시" in line and ":" in line:
                            date_info = line.split(':', 1)[1].strip()
                            print(f"  • {workspace.name} (생성: {date_info})")
                            break
                else:
                    print(f"  • {workspace.name}")
        else:
            print(f"  • {workspace.name}")


def main():
    """메인 함수"""
    print("🛠️ 개발 환경 격리 관리 도구")
    print("=" * 50)
    
    print("1. 새 기능 개발 시작 (복구지점 + 격리환경)")
    print("2. 개발 완료 처리 (통합 + 정리)")
    print("3. 개발 환경 목록 보기")
    print("4. 종료")
    
    choice = input("\n선택 (1-4): ").strip()
    
    if choice == "1":
        feature_name = input("기능명 입력: ").strip()
        if not feature_name:
            print("❌ 기능명이 필요합니다.")
            return
        
        # 복구 지점 생성
        if create_backup_commit(feature_name):
            # 개발 환경 구성
            source_files_input = input("복사할 파일들 (쉼표로 구분, 엔터면 없음): ").strip()
            source_files = [f.strip() for f in source_files_input.split(',')] if source_files_input else None
            
            create_dev_workspace(feature_name, source_files)
        
    elif choice == "2":
        feature_name = input("완료할 기능명: ").strip()
        if not feature_name:
            print("❌ 기능명이 필요합니다.")
            return
            
        target_location = input("파일 이동 위치 (엔터면 현재 위치): ").strip()
        complete_development(feature_name, target_location if target_location else None)
        
    elif choice == "3":
        list_dev_workspaces()
        
    elif choice == "4":
        print("👋 종료합니다.")
        
    else:
        print("❌ 잘못된 선택입니다.")


if __name__ == "__main__":
    main()
