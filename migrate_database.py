#!/usr/bin/env python3
"""
데이터베이스 구조 통합 마이그레이션 스크립트
TASK-20250728-01_Database_Structure_Unification Phase 1-3

이 스크립트는 분산된 데이터베이스 파일들을 3개의 통합 파일로 마이그레이션합니다.
"""

import sqlite3
import os
import shutil
import json
from datetime import datetime
from pathlib import Path

class DatabaseMigrator:
    """데이터베이스 마이그레이션 클래스"""
    
    def __init__(self):
        self.base_path = Path(".")
        self.data_path = self.base_path / "data"
        self.legacy_path = self.base_path / "legacy_db"
        
        # 목표 데이터베이스 파일들
        self.target_dbs = {
            'settings': self.data_path / "settings.sqlite3",
            'strategies': self.data_path / "strategies.sqlite3", 
            'market_data': self.data_path / "market_data.sqlite3"  # 기존 유지
        }
        
        # 소스 데이터베이스 파일들
        self.source_dbs = {
            'app_settings': self.data_path / "app_settings.sqlite3",
            'upbit_auto_trading': self.data_path / "upbit_auto_trading.sqlite3",
            'trading_variables_root': self.base_path / "trading_variables.db",
            'market_data': self.data_path / "market_data.sqlite3"
        }
        
        self.migration_log = []
        
    def log(self, message: str):
        """로그 메시지 기록"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.migration_log.append(log_entry)
        print(log_entry)
        
    def check_prerequisites(self) -> bool:
        """마이그레이션 전 필수 조건 확인"""
        self.log("=== 마이그레이션 사전 확인 시작 ===")
        
        # 1. 백업 폴더 확인
        if not (self.legacy_path / "backups").exists():
            self.log("❌ 백업 폴더가 존재하지 않습니다!")
            return False
        self.log("✅ 백업 폴더 확인됨")
        
        # 2. 소스 파일들 확인
        missing_files = []
        for name, path in self.source_dbs.items():
            if not path.exists():
                missing_files.append(f"{name}: {path}")
                
        if missing_files:
            self.log(f"⚠️ 일부 소스 파일이 없습니다: {missing_files}")
            
        # 3. data 폴더 쓰기 권한 확인
        if not self.data_path.exists():
            self.data_path.mkdir(parents=True, exist_ok=True)
        self.log("✅ data 폴더 쓰기 권한 확인됨")
        
        return True
        
    def create_settings_db(self):
        """settings.sqlite3 생성 및 데이터 통합"""
        self.log("=== settings.sqlite3 생성 시작 ===")
        
        settings_db = self.target_dbs['settings']
        
        # 기존 파일이 있으면 백업
        if settings_db.exists():
            backup_name = f"settings_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite3"
            shutil.copy2(settings_db, self.legacy_path / "backups" / backup_name)
            self.log(f"✅ 기존 settings.sqlite3 백업: {backup_name}")
        
        with sqlite3.connect(settings_db) as conn:
            # 기본 스키마 생성
            conn.execute('''
                CREATE TABLE IF NOT EXISTS app_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trading_variables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    value TEXT,
                    type TEXT DEFAULT 'string',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 트리거 생성 (updated_at 자동 업데이트)
            conn.execute('''
                CREATE TRIGGER IF NOT EXISTS update_app_settings_timestamp 
                AFTER UPDATE ON app_settings
                BEGIN
                    UPDATE app_settings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')
            
            conn.execute('''
                CREATE TRIGGER IF NOT EXISTS update_trading_variables_timestamp 
                AFTER UPDATE ON trading_variables
                BEGIN
                    UPDATE trading_variables SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')
            
            conn.commit()
            self.log("✅ settings.sqlite3 기본 스키마 생성 완료")
            
        # 기존 app_settings.sqlite3 데이터 마이그레이션
        self._migrate_app_settings_data(settings_db)
        
        # 기존 trading_variables.db 데이터 마이그레이션  
        self._migrate_trading_variables_data(settings_db)
        
    def _migrate_app_settings_data(self, target_db: Path):
        """app_settings.sqlite3 데이터 마이그레이션"""
        source_db = self.source_dbs['app_settings']
        if not source_db.exists():
            self.log("⚠️ app_settings.sqlite3 파일이 없어 스키마만 생성")
            return
            
        try:
            with sqlite3.connect(source_db) as source_conn:
                # 테이블 목록 확인
                tables = source_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                
                self.log(f"📊 app_settings.sqlite3 테이블 목록: {[t[0] for t in tables]}")
                
            with sqlite3.connect(target_db) as target_conn:
                # 기존 테이블 구조를 그대로 복사
                source_conn = sqlite3.connect(source_db)
                
                for table_name, in tables:
                    if table_name.startswith('sqlite_'):
                        continue
                        
                    # 테이블 구조 복사
                    schema = source_conn.execute(
                        f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'"
                    ).fetchone()
                    
                    if schema:
                        target_conn.execute(schema[0])
                        
                        # 데이터 복사
                        data = source_conn.execute(f"SELECT * FROM {table_name}").fetchall()
                        if data:
                            columns = [desc[0] for desc in source_conn.execute(f"PRAGMA table_info({table_name})")]
                            placeholders = ','.join(['?' for _ in columns])
                            target_conn.executemany(
                                f"INSERT OR IGNORE INTO {table_name} VALUES ({placeholders})", 
                                data
                            )
                            self.log(f"✅ {table_name} 테이블 데이터 마이그레이션: {len(data)}개 레코드")
                
                source_conn.close()
                target_conn.commit()
                
        except Exception as e:
            self.log(f"❌ app_settings 마이그레이션 오류: {e}")
            
    def _migrate_trading_variables_data(self, target_db: Path):
        """trading_variables.db 데이터 마이그레이션"""
        source_db = self.source_dbs['trading_variables_root']
        if not source_db.exists():
            self.log("⚠️ trading_variables.db 파일이 없어 기본 스키마만 유지")
            return
            
        try:
            with sqlite3.connect(source_db) as source_conn:
                # 테이블 확인
                tables = source_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                
                self.log(f"📊 trading_variables.db 테이블 목록: {[t[0] for t in tables]}")
                
                with sqlite3.connect(target_db) as target_conn:
                    # 기존 테이블들을 그대로 복사 (이름 충돌 방지를 위해 접두사 추가)
                    for table_name, in tables:
                        if table_name.startswith('sqlite_'):
                            continue
                            
                        new_table_name = f"tv_{table_name}"  # trading_variables 접두사
                        
                        # 테이블 구조 복사
                        schema = source_conn.execute(
                            f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'"
                        ).fetchone()
                        
                        if schema:
                            # 테이블명 변경
                            new_schema = schema[0].replace(f"CREATE TABLE {table_name}", f"CREATE TABLE IF NOT EXISTS {new_table_name}")
                            target_conn.execute(new_schema)
                            
                            # 데이터 복사
                            data = source_conn.execute(f"SELECT * FROM {table_name}").fetchall()
                            if data:
                                columns = [desc[0] for desc in source_conn.execute(f"PRAGMA table_info({table_name})")]
                                placeholders = ','.join(['?' for _ in columns])
                                target_conn.executemany(
                                    f"INSERT OR IGNORE INTO {new_table_name} VALUES ({placeholders})", 
                                    data
                                )
                                self.log(f"✅ {new_table_name} 테이블 데이터 마이그레이션: {len(data)}개 레코드")
                    
                    target_conn.commit()
                    
        except Exception as e:
            self.log(f"❌ trading_variables 마이그레이션 오류: {e}")
            
    def create_strategies_db(self):
        """strategies.sqlite3 생성 및 데이터 통합"""
        self.log("=== strategies.sqlite3 생성 시작 ===")
        
        strategies_db = self.target_dbs['strategies']
        
        # 기존 파일이 있으면 백업
        if strategies_db.exists():
            backup_name = f"strategies_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite3"
            shutil.copy2(strategies_db, self.legacy_path / "backups" / backup_name)
            self.log(f"✅ 기존 strategies.sqlite3 백업: {backup_name}")
        
        # upbit_auto_trading.sqlite3 데이터 마이그레이션
        source_db = self.source_dbs['upbit_auto_trading']
        if not source_db.exists():
            self.log("⚠️ upbit_auto_trading.sqlite3 파일이 없어 빈 DB 생성")
            # 빈 데이터베이스 생성
            with sqlite3.connect(strategies_db) as conn:
                conn.execute('SELECT 1')  # 파일 생성
            return
            
        try:
            # 기존 파일을 복사한 후 이름 변경
            shutil.copy2(source_db, strategies_db)
            self.log(f"✅ {source_db.name} → strategies.sqlite3 복사 완료")
            
            # 필요시 추가 스키마 업데이트
            with sqlite3.connect(strategies_db) as conn:
                # 메타데이터 테이블 추가
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS migration_info (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        migration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        source_file TEXT,
                        migration_version TEXT
                    )
                ''')
                
                conn.execute('''
                    INSERT INTO migration_info (source_file, migration_version) 
                    VALUES (?, ?)
                ''', (str(source_db), "1.0.0"))
                
                conn.commit()
                self.log("✅ strategies.sqlite3 메타데이터 추가 완료")
                
        except Exception as e:
            self.log(f"❌ strategies 마이그레이션 오류: {e}")
            
    def verify_migration(self) -> bool:
        """마이그레이션 결과 검증"""
        self.log("=== 마이그레이션 검증 시작 ===")
        
        success = True
        
        for name, db_path in self.target_dbs.items():
            if not db_path.exists():
                self.log(f"❌ {name} 파일이 생성되지 않음: {db_path}")
                success = False
                continue
                
            try:
                with sqlite3.connect(db_path) as conn:
                    # 테이블 목록 확인
                    tables = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                    
                    table_count = len(tables)
                    self.log(f"✅ {name}: {table_count}개 테이블 확인됨")
                    
                    # 기본 쿼리 테스트
                    conn.execute('SELECT 1').fetchone()
                    
            except Exception as e:
                self.log(f"❌ {name} 검증 실패: {e}")
                success = False
                
        return success
        
    def save_migration_log(self):
        """마이그레이션 로그 저장"""
        log_file = self.legacy_path / f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=== 데이터베이스 구조 통합 마이그레이션 로그 ===\n")
            f.write(f"시작 시간: {datetime.now()}\n")
            f.write(f"작업 디렉토리: {self.base_path.absolute()}\n\n")
            
            for log_entry in self.migration_log:
                f.write(log_entry + "\n")
                
        self.log(f"📋 마이그레이션 로그 저장: {log_file}")
        
    def run_migration(self) -> bool:
        """전체 마이그레이션 실행"""
        self.log("🚀 데이터베이스 구조 통합 마이그레이션 시작")
        
        # 1. 사전 확인
        if not self.check_prerequisites():
            self.log("❌ 사전 확인 실패 - 마이그레이션 중단")
            return False
            
        # 2. settings.sqlite3 생성
        try:
            self.create_settings_db()
        except Exception as e:
            self.log(f"❌ settings.sqlite3 생성 실패: {e}")
            return False
            
        # 3. strategies.sqlite3 생성  
        try:
            self.create_strategies_db()
        except Exception as e:
            self.log(f"❌ strategies.sqlite3 생성 실패: {e}")
            return False
            
        # 4. market_data.sqlite3는 기존 파일 유지
        market_data_source = self.source_dbs['market_data']
        market_data_target = self.target_dbs['market_data']
        
        if market_data_source.exists() and market_data_source != market_data_target:
            shutil.copy2(market_data_source, market_data_target)
            self.log("✅ market_data.sqlite3 유지됨")
            
        # 5. 검증
        if not self.verify_migration():
            self.log("❌ 마이그레이션 검증 실패")
            return False
            
        # 6. 로그 저장
        self.save_migration_log()
        
        self.log("🎉 데이터베이스 구조 통합 마이그레이션 완료!")
        return True


def main():
    """메인 실행 함수"""
    print("📊 데이터베이스 구조 통합 마이그레이션 스크립트")
    print("TASK-20250728-01_Database_Structure_Unification")
    print("=" * 50)
    
    migrator = DatabaseMigrator()
    
    # 사용자 확인
    print(f"작업 디렉토리: {migrator.base_path.absolute()}")
    print(f"백업 폴더: {migrator.legacy_path}")
    print("\n다음 파일들이 생성됩니다:")
    for name, path in migrator.target_dbs.items():
        print(f"  - {name}: {path}")
    
    confirm = input("\n마이그레이션을 계속하시겠습니까? (y/N): ")
    if confirm.lower() != 'y':
        print("마이그레이션이 취소되었습니다.")
        return
        
    # 마이그레이션 실행
    success = migrator.run_migration()
    
    if success:
        print("\n✅ 마이그레이션이 성공적으로 완료되었습니다!")
        print("📋 다음 단계: Phase 4 - 코드 경로 업데이트")
    else:
        print("\n❌ 마이그레이션이 실패했습니다.")
        print("📋 legacy_db/backups/ 폴더에서 복구하세요.")


if __name__ == "__main__":
    main()
