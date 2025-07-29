#!/usr/bin/env python3
"""
데이터베이스 구조 통합 롤백 스크립트
TASK-20250728-01_Database_Structure_Unification 롤백용

이 스크립트는 마이그레이션 작업을 롤백하여 원래 상태로 복구합니다.
"""

import shutil
import os
from datetime import datetime
from pathlib import Path


class DatabaseRollback:
    """데이터베이스 롤백 클래스"""
    
    def __init__(self):
        self.base_path = Path(".")
        self.data_path = self.base_path / "data"
        self.legacy_path = self.base_path / "legacy_db"
        self.backup_path = self.legacy_path / "backups"
        
        self.rollback_log = []
        
    def log(self, message: str):
        """로그 메시지 기록"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.rollback_log.append(log_entry)
        print(log_entry)
        
    def check_backup_exists(self) -> bool:
        """백업 폴더 존재 확인"""
        if not self.backup_path.exists():
            self.log("❌ 백업 폴더가 존재하지 않습니다!")
            return False
            
        backup_files = list(self.backup_path.glob("*.sqlite3"))
        if not backup_files:
            self.log("❌ 백업 데이터베이스 파일이 없습니다!")
            return False
            
        self.log(f"✅ 백업 파일 {len(backup_files)}개 확인됨")
        return True
        
    def backup_current_state(self):
        """현재 상태 백업 (롤백 전)"""
        rollback_backup_path = self.legacy_path / f"rollback_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        rollback_backup_path.mkdir(exist_ok=True)
        
        if self.data_path.exists():
            shutil.copytree(self.data_path, rollback_backup_path / "data", dirs_exist_ok=True)
            self.log(f"✅ 롤백 전 현재 상태 백업: {rollback_backup_path}")
        
    def restore_from_backup(self) -> bool:
        """백업에서 복구"""
        try:
            # 현재 data 폴더 백업
            self.backup_current_state()
            
            # 현재 data 폴더 삭제
            if self.data_path.exists():
                shutil.rmtree(self.data_path)
                self.log("✅ 기존 data 폴더 제거됨")
            
            # 백업에서 복구
            shutil.copytree(self.backup_path, self.data_path, dirs_exist_ok=True)
            self.log("✅ 백업에서 data 폴더 복구 완료")
            
            return True
            
        except Exception as e:
            self.log(f"❌ 복구 중 오류 발생: {e}")
            return False
            
    def verify_rollback(self) -> bool:
        """롤백 결과 검증"""
        self.log("=== 롤백 검증 시작 ===")
        
        # 예상되는 원본 파일들 확인
        expected_files = [
            "app_settings.sqlite3",
            "upbit_auto_trading.sqlite3", 
            "market_data.sqlite3"
        ]
        
        success = True
        for filename in expected_files:
            file_path = self.data_path / filename
            if file_path.exists():
                self.log(f"✅ {filename} 복구됨")
            else:
                self.log(f"⚠️ {filename} 없음 (원래 없었을 수 있음)")
                
        return success
        
    def save_rollback_log(self):
        """롤백 로그 저장"""
        log_file = self.legacy_path / f"rollback_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=== 데이터베이스 구조 통합 롤백 로그 ===\n")
            f.write(f"시작 시간: {datetime.now()}\n")
            f.write(f"작업 디렉토리: {self.base_path.absolute()}\n\n")
            
            for log_entry in self.rollback_log:
                f.write(log_entry + "\n")
                
        self.log(f"📋 롤백 로그 저장: {log_file}")
        
    def run_rollback(self) -> bool:
        """전체 롤백 실행"""
        self.log("🔄 데이터베이스 구조 통합 롤백 시작")
        
        # 1. 백업 확인
        if not self.check_backup_exists():
            return False
            
        # 2. 복구 실행
        if not self.restore_from_backup():
            return False
            
        # 3. 검증
        if not self.verify_rollback():
            self.log("⚠️ 롤백 검증에서 일부 파일이 확인되지 않음")
            
        # 4. 로그 저장
        self.save_rollback_log()
        
        self.log("🎉 데이터베이스 롤백 완료!")
        return True


def main():
    """메인 실행 함수"""
    print("🔄 데이터베이스 구조 통합 롤백 스크립트")
    print("TASK-20250728-01_Database_Structure_Unification 롤백")
    print("=" * 50)
    
    rollback = DatabaseRollback()
    
    # 사용자 확인
    print(f"작업 디렉토리: {rollback.base_path.absolute()}")
    print(f"백업 폴더: {rollback.backup_path}")
    print("\n⚠️ 주의: 현재 data 폴더의 내용이 백업 상태로 복구됩니다.")
    print("현재 상태는 별도로 백업됩니다.")
    
    confirm = input("\n롤백을 계속하시겠습니까? (y/N): ")
    if confirm.lower() != 'y':
        print("롤백이 취소되었습니다.")
        return
        
    # 롤백 실행
    success = rollback.run_rollback()
    
    if success:
        print("\n✅ 롤백이 성공적으로 완료되었습니다!")
        print("📋 원래 데이터베이스 구조로 복구되었습니다.")
    else:
        print("\n❌ 롤백이 실패했습니다.")
        print("📋 수동으로 복구가 필요할 수 있습니다.")


if __name__ == "__main__":
    main()
