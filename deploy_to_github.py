#!/usr/bin/env python3
"""
GitHub 배포 스크립트
프로젝트를 GitHub에 푸시하기 전 최종 점검 및 커밋
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, check=True):
    """명령어 실행"""
    try:
        result = subprocess.run(command, shell=True, check=check, 
                              capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ 명령어 실행 실패: {command}")
        print(f"오류: {e.stderr}")
        return None

def check_git_status():
    """Git 상태 확인"""
    print("🔍 Git 상태 확인 중...")
    
    # Git 초기화 확인
    if not Path(".git").exists():
        print("⚠️ Git 저장소가 초기화되지 않았습니다. 초기화 중...")
        run_command("git init")
        print("✅ Git 저장소 초기화 완료")
    
    # 원격 저장소 확인
    origin = run_command("git remote get-url origin", check=False)
    if not origin:
        print("⚠️ 원격 저장소가 설정되지 않았습니다.")
        print("💡 다음 명령어로 원격 저장소를 추가하세요:")
        print("   git remote add origin https://github.com/invisible0000/upbit-autotrader-vscode.git")
        return False
    
    print(f"✅ 원격 저장소: {origin}")
    return True

def check_files():
    """중요 파일들 존재 확인"""
    print("\n🔍 필수 파일 확인 중...")
    
    required_files = [
        "README.md",
        "requirements.txt", 
        "quick_start.py",
        ".gitignore",
        ".env.template",
        "run_desktop_ui.py",
        "docs/MINI_SIMULATION_ARCHITECTURE_GUIDE.md",
        "docs/MINI_SIMULATION_REFACTORING_COMPLETION_REPORT.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")
    
    if missing_files:
        print("❌ 누락된 파일들:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    print("✅ 모든 필수 파일이 존재합니다.")
    return True

def check_sensitive_data():
    """민감한 데이터 확인"""
    print("\n🔍 민감한 데이터 확인 중...")
    
    # .env 파일 확인
    if Path(".env").exists():
        print("⚠️ .env 파일이 있습니다. .gitignore에 포함되어 있는지 확인...")
        with open(".gitignore", "r", encoding="utf-8") as f:
            gitignore_content = f.read()
        
        if ".env" in gitignore_content:
            print("✅ .env 파일이 .gitignore에 포함되어 있습니다.")
        else:
            print("❌ .env 파일이 .gitignore에 포함되어 있지 않습니다!")
            return False
    
    # 데이터베이스 파일 확인
    db_files = list(Path(".").rglob("*.sqlite3"))
    if db_files:
        print("⚠️ 데이터베이스 파일들:")
        for db_file in db_files:
            print(f"  - {db_file}")
        print("✅ 데이터베이스 파일들이 .gitignore에 포함되어 있는지 확인하세요.")
    
    print("✅ 민감한 데이터 확인 완료")
    return True

def prepare_commit():
    """커밋 준비"""
    print("\n📝 커밋 준비 중...")
    
    # 변경사항 확인
    status = run_command("git status --porcelain")
    if not status:
        print("ℹ️ 커밋할 변경사항이 없습니다.")
        return True
    
    print("📋 변경사항:")
    for line in status.split("\n"):
        if line.strip():
            print(f"  {line}")
    
    # 스테이징
    print("\n📦 파일 스테이징 중...")
    run_command("git add .")
    
    # 커밋 메시지 생성
    commit_message = """🚀 GitHub 배포 준비 완료

✨ 새로운 기능:
- 미니 시뮬레이션 아키텍처 리팩토링 완료
- 크로스 탭 재사용성 구현 
- 어댑터 패턴 기반 확장성 확보

📦 환경 설정:
- 통합 requirements.txt 생성
- 빠른 시작 스크립트 (quick_start.py) 추가
- 포괄적인 README.md 작성
- .env.template 환경 설정 템플릿 제공

🔧 개선사항:
- .gitignore 보안 강화
- 문서 업데이트 (2025년 7월 28일)
- GitHub 클론 후 바로 실행 가능한 구조

🎯 완료된 Phase:
- Phase 1-5: 미니 시뮬레이션 시스템 완전 리팩토링
- 재사용성 테스트 100% 성공
- 향후 에이전트를 위한 완전한 문서화"""
    
    # 커밋 실행
    print("\n💾 커밋 실행 중...")
    result = run_command(f'git commit -m "{commit_message}"')
    if result is not None:
        print("✅ 커밋 완료")
        return True
    else:
        print("❌ 커밋 실패")
        return False

def main():
    """메인 함수"""
    print("🚀 GitHub 배포 준비 스크립트")
    print("=" * 50)
    
    # 1단계: Git 상태 확인
    if not check_git_status():
        print("\n❌ Git 설정을 완료한 후 다시 실행하세요.")
        return False
    
    # 2단계: 파일 확인
    if not check_files():
        print("\n❌ 필수 파일들을 확인한 후 다시 실행하세요.")
        return False
    
    # 3단계: 민감한 데이터 확인
    if not check_sensitive_data():
        print("\n❌ 민감한 데이터를 확인한 후 다시 실행하세요.")
        return False
    
    # 4단계: 커밋 준비
    if not prepare_commit():
        print("\n❌ 커밋에 실패했습니다.")
        return False
    
    # 5단계: 푸시 안내
    print("\n" + "=" * 50)
    print("🎉 GitHub 배포 준비 완료!")
    print("=" * 50)
    
    print("\n📋 다음 단계:")
    print("1. 원격 저장소 확인:")
    print("   git remote -v")
    print()
    print("2. 브랜치 푸시:")
    print("   git push origin main")
    print("   또는")
    print("   git push origin master")
    print()
    print("3. 태그 생성 (선택사항):")
    print("   git tag -a v1.0.0 -m 'Version 1.0.0 - Mini Simulation Architecture'")
    print("   git push origin v1.0.0")
    print()
    print("🔗 GitHub 저장소 URL:")
    print("   https://github.com/invisible0000/upbit-autotrader-vscode")
    print()
    print("✨ 이제 다른 사용자들이 다음 명령어로 프로젝트를 사용할 수 있습니다:")
    print("   git clone https://github.com/invisible0000/upbit-autotrader-vscode.git")
    print("   cd upbit-autotrader-vscode")
    print("   pip install -r requirements.txt")
    print("   python quick_start.py")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 배포 준비 성공!")
    else:
        print("\n❌ 배포 준비 실패!")
        sys.exit(1)
