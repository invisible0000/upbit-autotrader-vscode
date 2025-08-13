"""
자동화된 Path Service 교체 스크립트
모든 legacy path 접근을 Factory 패턴으로 교체
"""

import re
from pathlib import Path

def replace_path_usages_in_file(file_path: str):
    """파일의 모든 path 사용을 Factory 패턴으로 교체"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 교체 패턴들
    replacements = [
        # self.paths.SECURE_DIR -> secure directory 경로
        (r'self\.paths\.SECURE_DIR', 
         r'self.path_service.get_directory_path("config") / "secure"'),
        
        # self.paths.API_CREDENTIALS_FILE -> api credentials 파일
        (r'self\.paths\.API_CREDENTIALS_FILE',
         r'self.path_service.get_directory_path("config") / "secure" / "api_credentials.json"'),
        
        # self.paths.CONFIG_DIR -> config directory
        (r'self\.paths\.CONFIG_DIR',
         r'self.path_service.get_directory_path("config")'),
        
        # self.paths.DATA_DIR -> data directory  
        (r'self\.paths\.DATA_DIR',
         r'self.path_service.get_directory_path("data")'),
        
        # self.paths.LOGS_DIR -> logs directory
        (r'self\.paths\.LOGS_DIR',
         r'self.path_service.get_directory_path("logs")'),
        
        # self.paths.BACKUPS_DIR -> backups directory
        (r'self\.paths\.BACKUPS_DIR',
         r'self.path_service.get_directory_path("backups")'),
        
        # Database paths
        (r'self\.paths\.SETTINGS_DB',
         r'self.path_service.get_database_path("settings")'),
         
        (r'self\.paths\.STRATEGIES_DB',
         r'self.path_service.get_database_path("strategies")'),
         
        (r'self\.paths\.MARKET_DATA_DB',
         r'self.path_service.get_database_path("market_data")'),
    ]
    
    # 교체 실행
    changes_made = 0
    for pattern, replacement in replacements:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            changes_made += 1
            content = new_content
            print(f"✅ 교체 완료: {pattern} -> {replacement}")
    
    # 파일 업데이트
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📝 파일 업데이트 완료: {file_path} ({changes_made} 개 교체)")
        return True
    else:
        print(f"⚪ 변경사항 없음: {file_path}")
        return False

def main():
    """주요 파일들 자동 교체"""
    files_to_update = [
        "upbit_auto_trading/infrastructure/services/api_key_service.py",
        "upbit_auto_trading/infrastructure/services/file_system_service.py",
    ]
    
    total_updated = 0
    for file_path in files_to_update:
        full_path = Path("d:/projects/upbit-autotrader-vscode") / file_path
        if full_path.exists():
            if replace_path_usages_in_file(str(full_path)):
                total_updated += 1
        else:
            print(f"❌ 파일 없음: {full_path}")
    
    print(f"\n🎉 교체 완료: {total_updated}/{len(files_to_update)} 파일")

if __name__ == "__main__":
    main()
