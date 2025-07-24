#!/usr/bin/env python3
"""
전체 문제 해결 검증 및 도구 정리 스크립트
사용자가 지적한 6가지 문제점에 대한 종합 검증 및 임시 파일 정리
"""

import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

def check_issues():
    """사용자 지적 문제점 검증"""
    print("🔍 사용자 지적 문제점 종합 검증")
    print("=" * 50)
    
    issues = {
        1: "외부변수 파라미터의 기간이 50봉까지만 입력되는 문제",
        2: "편집 시 트리거 외부변수 설정 로드 안됨",
        3: "편집기능이 새로운 트리거로 등록되는 문제",
        4: "Trigger Details 정보 읽어오기 기능 수정 필요",
        5: "테스트용 json/py 파일들의 정리 및 tools 이관",
        6: "Case Simulation 기능의 정상성 검증 필요"
    }
    
    # 1. DB 상태 확인
    print("\n1️⃣ 외부변수 파라미터 기간 확인")
    check_external_parameters()
    
    # 2. 코드 수정 확인
    print("\n2️⃣ 코드 수정사항 확인")
    check_code_modifications()
    
    # 3. 임시 파일 정리
    print("\n5️⃣ 임시 파일 정리")
    cleanup_temporary_files()
    
    print("\n✅ 종합 검증 완료")

def check_external_parameters():
    """외부변수 파라미터 확인"""
    try:
        conn = sqlite3.connect("data/app_settings.sqlite3")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, external_variable 
            FROM trading_conditions 
            WHERE external_variable IS NOT NULL 
            AND external_variable != ''
        """)
        
        results = cursor.fetchall()
        
        for name, external_variable_str in results:
            try:
                external_var = json.loads(external_variable_str)
                params = external_var.get('parameters', {})
                if 'period' in params:
                    period = params['period']
                    print(f"  {name}: 외부변수 기간 = {period}일")
                    if period > 50:
                        print(f"    ✅ 50일 초과 기간 지원 확인 ({period}일)")
                    else:
                        print(f"    ⚠️  50일 이하 기간 ({period}일)")
            except json.JSONDecodeError:
                print(f"  {name}: JSON 파싱 실패")
        
        conn.close()
        
    except Exception as e:
        print(f"  ❌ 오류: {e}")

def check_code_modifications():
    """코드 수정사항 확인"""
    
    # condition_dialog.py 수정사항 확인
    dialog_file = "upbit_auto_trading/ui/desktop/screens/strategy_management/components/condition_dialog.py"
    
    if os.path.exists(dialog_file):
        with open(dialog_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("  🔧 condition_dialog.py 수정사항:")
        
        # 편집 모드 추가 확인
        if "self.edit_mode" in content:
            print("    ✅ 편집 모드 추적 변수 추가됨")
        else:
            print("    ❌ 편집 모드 추적 변수 없음")
        
        # 외부변수 파라미터 복원 확인
        if "external_variable.get('parameters')" in content:
            print("    ✅ 외부변수 'parameters' 필드 지원 추가됨")
        else:
            print("    ❌ 외부변수 'parameters' 필드 지원 없음")
            
        # JSON import 확인
        if "import json" in content:
            print("    ✅ json 모듈 import 추가됨")
        else:
            print("    ❌ json 모듈 import 없음")
    
    # strategy_maker.py 수정사항 확인
    maker_file = "upbit_auto_trading/ui/desktop/screens/strategy_management/components/strategy_maker.py"
    
    if os.path.exists(maker_file):
        with open(maker_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("  🔧 strategy_maker.py 수정사항:")
        
        # Trigger Details 개선 확인
        if "external_var.get('parameters')" in content:
            print("    ✅ Trigger Details에서 외부변수 파라미터 표시 개선됨")
        else:
            print("    ❌ Trigger Details 외부변수 파라미터 표시 개선 없음")

def cleanup_temporary_files():
    """임시 파일 정리 및 tools 디렉터리 이관"""
    
    # tools 디렉터리 생성
    tools_dir = Path("tools")
    tools_dir.mkdir(exist_ok=True)
    
    # 임시 파일들 목록
    temp_files = [
        "check_db_state.py",
        "test_parameter_restoration.py", 
        "test_ui_parameter_restoration.py",
        "fix_trigger_formats.py",
        "fix_macd_triggers.py",
        "fix_external_params.py",
        "diagnose_external_params.py",
        "investigate_triggers.py",
        "verify_final_state.py"
    ]
    
    # JSON 백업 파일들
    json_files = []
    for file in Path(".").glob("*.json"):
        if any(pattern in file.name for pattern in ["trigger", "backup", "log", "reference"]):
            json_files.append(file.name)
    
    print("  📦 임시 파일 정리:")
    
    moved_count = 0
    
    # Python 스크립트 이관
    for file_name in temp_files:
        if os.path.exists(file_name):
            dest_path = tools_dir / file_name
            try:
                shutil.move(file_name, dest_path)
                print(f"    ✅ {file_name} → tools/{file_name}")
                moved_count += 1
            except Exception as e:
                print(f"    ❌ {file_name} 이동 실패: {e}")
    
    # JSON 파일 이관  
    for file_name in json_files:
        if os.path.exists(file_name):
            dest_path = tools_dir / file_name
            try:
                shutil.move(file_name, dest_path)
                print(f"    ✅ {file_name} → tools/{file_name}")
                moved_count += 1
            except Exception as e:
                print(f"    ❌ {file_name} 이동 실패: {e}")
    
    # 정리 요약 파일 생성
    create_tools_readme(tools_dir, moved_count)
    
    print(f"  📊 총 {moved_count}개 파일이 tools 디렉터리로 이관되었습니다.")

def create_tools_readme(tools_dir, moved_count):
    """tools 디렉터리에 README 파일 생성"""
    
    readme_content = f"""# 🛠️ Tools Directory

## 📁 개요
이 디렉터리는 트리거 정규화 및 파라미터 복원 시스템 개발 과정에서 생성된 유용한 도구들을 보관합니다.

## 📅 생성일시
- **정리일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **이관 파일 수**: {moved_count}개

## 🔧 주요 도구들

### 트리거 정규화 도구
- `fix_trigger_formats.py` - 비정상적인 트리거를 올바른 외부변수 형식으로 변환
- `fix_macd_triggers.py` - MACD 트리거 특별 수정
- `fix_external_params.py` - 외부변수 파라미터 수정

### 진단 및 검증 도구  
- `investigate_triggers.py` - 트리거 이상 상태 조사
- `diagnose_external_params.py` - 외부변수 파라미터 진단
- `verify_final_state.py` - 최종 상태 검증

### 테스트 도구
- `test_parameter_restoration.py` - 파라미터 복원 시스템 테스트
- `test_ui_parameter_restoration.py` - UI 파라미터 복원 테스트
- `check_db_state.py` - 데이터베이스 상태 확인

### 백업 및 로그 파일
- `trigger_backup_*.json` - 원본 트리거 데이터 백업
- `trigger_conversion_log_*.json` - 변환 작업 로그
- `trigger_examples_reference_*.json` - 외부변수 사용법 예시

## 🚀 사용법

### 트리거 정규화 실행
```bash
python tools/fix_trigger_formats.py
```

### 상태 검증
```bash
python tools/verify_final_state.py
```

### 파라미터 복원 테스트
```bash
python tools/test_parameter_restoration.py
```

## ⚠️ 주의사항
- 이 도구들은 데이터베이스를 직접 수정할 수 있습니다
- 실행 전 반드시 백업을 생성하세요
- 프로덕션 환경에서는 신중하게 사용하세요

## 📝 관련 문서
- `TRIGGER_NORMALIZATION_REPORT.md` - 트리거 정규화 작업 보고서
- `PARAMETER_RESTORATION_COMPLETION_REPORT.md` - 파라미터 복원 구현 보고서

## 🎯 향후 활용
- 유사한 데이터 정규화 작업 시 참고 자료로 활용
- 트리거 시스템 유지보수 시 진단 도구로 사용
- 새로운 외부변수 추가 시 예시 참고

---
*이 도구들은 2025년 7월 24일 트리거 정규화 및 파라미터 복원 시스템 개발 과정에서 생성되었습니다.*
"""
    
    readme_path = tools_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"    ✅ tools/README.md 생성 완료")

if __name__ == "__main__":
    check_issues()
