#!/usr/bin/env python3
"""
로그 관리 유틸리티 - 로그 파일 정리, 분석, 관리

2025-07-29: Debug Logger가 도입된 이후 로그 파일 관리 필요성 대응
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class LogManager:
    """로그 파일 관리 클래스"""
    
    def __init__(self):
        self.log_dir = project_root / "logs"
        self.current_time = datetime.now()
        
    def analyze_log_files(self):
        """로그 파일들 분석"""
        print("🔍 로그 파일 분석 시작...")
        
        log_files = []
        for log_file in self.log_dir.glob("*.log"):
            stat = log_file.stat()
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            age_days = (self.current_time - last_modified).days
            
            log_files.append({
                'name': log_file.name,
                'path': str(log_file),
                'size': stat.st_size,
                'last_modified': last_modified,
                'age_days': age_days,
                'is_empty': stat.st_size == 0
            })
        
        # Markdown 파일들도 확인
        for md_file in self.log_dir.glob("*.md"):
            stat = md_file.stat()
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            age_days = (self.current_time - last_modified).days
            
            log_files.append({
                'name': md_file.name,
                'path': str(md_file),
                'size': stat.st_size,
                'last_modified': last_modified,
                'age_days': age_days,
                'is_empty': stat.st_size == 0
            })
        
        return sorted(log_files, key=lambda x: x['last_modified'], reverse=True)
    
    def print_analysis(self, log_files):
        """분석 결과 출력"""
        print(f"\n📊 로그 파일 분석 결과 ({len(log_files)}개 파일)")
        print("=" * 80)
        
        for log_file in log_files:
            status_icon = "🟢" if log_file['age_days'] <= 1 else "🟡" if log_file['age_days'] <= 7 else "🔴"
            empty_icon = " ⚠️(빈파일)" if log_file['is_empty'] else ""
            
            print(f"{status_icon} {log_file['name']:<25} | "
                  f"크기: {log_file['size']:>8,}B | "
                  f"수정: {log_file['last_modified'].strftime('%m-%d %H:%M')} | "
                  f"경과: {log_file['age_days']:>2}일{empty_icon}")
    
    def identify_cleanup_candidates(self, log_files, max_age_days=7):
        """정리 대상 파일들 식별"""
        cleanup_candidates = []
        
        for log_file in log_files:
            reasons = []
            
            # 오래된 파일
            if log_file['age_days'] > max_age_days:
                reasons.append(f"{log_file['age_days']}일 경과")
            
            # 빈 파일
            if log_file['is_empty']:
                reasons.append("빈 파일")
            
            # 특정 패턴 (예: gui_error.log가 너무 큰 경우)
            if log_file['name'] == 'gui_error.log' and log_file['size'] > 50000:
                reasons.append("GUI 에러 로그 크기 초과")
            
            if reasons:
                cleanup_candidates.append({
                    'file': log_file,
                    'reasons': reasons
                })
        
        return cleanup_candidates
    
    def suggest_cleanup(self, cleanup_candidates):
        """정리 제안"""
        if not cleanup_candidates:
            print("\n✅ 정리가 필요한 로그 파일이 없습니다.")
            return
        
        print(f"\n🧹 정리 제안 ({len(cleanup_candidates)}개 파일)")
        print("=" * 60)
        
        for candidate in cleanup_candidates:
            file_info = candidate['file']
            reasons = candidate['reasons']
            
            print(f"📁 {file_info['name']}")
            print(f"   경로: {file_info['path']}")
            print(f"   이유: {', '.join(reasons)}")
            print(f"   제안: ", end="")
            
            if file_info['is_empty']:
                print("삭제 권장")
            elif "일 경과" in ' '.join(reasons):
                print("아카이브 후 삭제")
            else:
                print("백업 후 초기화")
            print()
    
    def check_debug_logger_status(self):
        """Debug Logger 상태 확인"""
        print("\n🔍 Debug Logger 상태 확인...")
        
        # Debug Logger 파일 존재 확인
        debug_logger_path = project_root / "upbit_auto_trading" / "utils" / "debug_logger.py"
        
        if not debug_logger_path.exists():
            print("❌ Debug Logger 파일이 존재하지 않습니다.")
            return False
        
        print("✅ Debug Logger 파일 존재")
        
        # 최근 로그 기록 확인
        main_log = self.log_dir / "upbit_auto_trading.log"
        if main_log.exists() and main_log.stat().st_size > 0:
            print("✅ 메인 로그 파일에 기록 있음")
            
            # 최근 기록 확인
            try:
                with open(main_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1].strip()
                        print(f"🔍 마지막 로그: {last_line[:100]}...")
                    else:
                        print("⚠️ 로그 파일은 존재하지만 비어있음")
            except Exception as e:
                print(f"❌ 로그 파일 읽기 실패: {e}")
        else:
            print("⚠️ 메인 로그 파일이 비어있거나 존재하지 않음")
            return False
        
        return True
    
    def create_log_cleanup_script(self):
        """로그 정리 스크립트 생성"""
        script_content = '''@echo off
echo 로그 파일 정리 스크립트
echo ========================

REM 7일 이상 된 빈 로그 파일 삭제
forfiles /p logs /m *.log /d -7 /c "cmd /c if @fsize==0 del @path"

REM GUI 에러 로그가 50KB 이상이면 백업 후 초기화
for %%f in (logs\\gui_error.log) do (
    if %%~zf gtr 51200 (
        echo GUI 에러 로그 크기 초과, 백업 중...
        copy "%%f" "%%f.backup.%date:~0,4%%date:~5,2%%date:~8,2%"
        echo. > "%%f"
    )
)

echo 정리 완료!
pause
'''
        
        script_path = project_root / "cleanup_logs.bat"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"📝 로그 정리 스크립트 생성: {script_path}")

def main():
    """메인 실행 함수"""
    print("🚀 로그 관리 유틸리티 시작")
    print(f"📅 현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    manager = LogManager()
    
    # 1. 로그 파일 분석
    log_files = manager.analyze_log_files()
    manager.print_analysis(log_files)
    
    # 2. 정리 대상 식별
    cleanup_candidates = manager.identify_cleanup_candidates(log_files)
    manager.suggest_cleanup(cleanup_candidates)
    
    # 3. Debug Logger 상태 확인
    debug_status = manager.check_debug_logger_status()
    
    # 4. 정리 스크립트 생성
    manager.create_log_cleanup_script()
    
    # 5. 종합 보고서
    print("\n📋 종합 보고서")
    print("=" * 40)
    print(f"총 로그 파일: {len(log_files)}개")
    print(f"정리 대상: {len(cleanup_candidates)}개")
    print(f"Debug Logger 상태: {'정상' if debug_status else '비정상'}")
    
    if not debug_status:
        print("\n⚠️ Debug Logger가 제대로 작동하지 않는 것 같습니다.")
        print("   - Debug Logger 설정 확인 필요")
        print("   - 로그 레벨 확인 필요")
        print("   - 파일 권한 확인 필요")

if __name__ == "__main__":
    main()
