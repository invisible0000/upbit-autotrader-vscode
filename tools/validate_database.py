#!/usr/bin/env python3
"""
데이터베이스 검증 스크립트
TASK-20250728-01_Database_Structure_Unification 검증용

이 스크립트는 마이그레이션 전후의 데이터 무결성을 검증합니다.
"""

import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path


class DatabaseValidator:
    """데이터베이스 검증 클래스"""
    
    def __init__(self):
        self.base_path = Path(".")
        self.data_path = self.base_path / "data"
        self.legacy_path = self.base_path / "legacy_db"
        
        self.validation_log = []
        
    def log(self, message: str):
        """로그 메시지 기록"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.validation_log.append(log_entry)
        print(log_entry)
        
    def get_db_info(self, db_path: Path) -> dict:
        """데이터베이스 정보 추출"""
        if not db_path.exists():
            return {"exists": False}
            
        try:
            with sqlite3.connect(db_path) as conn:
                # 테이블 목록
                tables = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
                
                table_info = {}
                total_records = 0
                
                for table_name, in tables:
                    # 레코드 수
                    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    total_records += count
                    
                    # 스키마 정보
                    schema = conn.execute(
                        f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'"
                    ).fetchone()
                    
                    table_info[table_name] = {
                        "records": count,
                        "schema_hash": hashlib.md5(schema[0].encode()).hexdigest() if schema else None
                    }
                
                return {
                    "exists": True,
                    "tables": table_info,
                    "total_tables": len(tables),
                    "total_records": total_records,
                    "file_size": db_path.stat().st_size
                }
                
        except Exception as e:
            return {"exists": True, "error": str(e)}
            
    def validate_migration_integrity(self) -> bool:
        """마이그레이션 무결성 검증"""
        self.log("=== 마이그레이션 무결성 검증 시작 ===")
        
        # 1. 원본 파일들 정보 수집
        original_files = {
            "app_settings": self.legacy_path / "backups" / "app_settings.sqlite3",
            "upbit_auto_trading": self.legacy_path / "backups" / "upbit_auto_trading.sqlite3",
            "market_data": self.legacy_path / "backups" / "market_data.sqlite3"
        }
        
        # 2. 통합된 파일들 정보 수집
        target_files = {
            "settings": self.data_path / "settings.sqlite3",
            "strategies": self.data_path / "strategies.sqlite3", 
            "market_data": self.data_path / "market_data.sqlite3"
        }
        
        # 3. 원본 데이터 분석
        original_info = {}
        total_original_records = 0
        
        for name, path in original_files.items():
            info = self.get_db_info(path)
            original_info[name] = info
            
            if info.get("exists") and "total_records" in info:
                total_original_records += info["total_records"]
                self.log(f"📊 원본 {name}: {info['total_tables']}개 테이블, {info['total_records']}개 레코드")
            else:
                self.log(f"⚠️ 원본 {name}: 파일 없음 또는 오류")
                
        # 4. 통합 데이터 분석
        target_info = {}
        total_target_records = 0
        
        for name, path in target_files.items():
            info = self.get_db_info(path)
            target_info[name] = info
            
            if info.get("exists") and "total_records" in info:
                total_target_records += info["total_records"]
                self.log(f"📊 통합 {name}: {info['total_tables']}개 테이블, {info['total_records']}개 레코드")
            else:
                self.log(f"❌ 통합 {name}: 파일 없음 또는 오류")
                
        # 5. 데이터 무결성 확인
        self.log("=== 데이터 무결성 분석 ===")
        
        # market_data는 변경 없이 복사되어야 함
        if original_info.get("market_data", {}).get("exists"):
            original_md = original_info["market_data"]
            target_md = target_info.get("market_data", {})
            
            if target_md.get("total_records") == original_md.get("total_records"):
                self.log("✅ market_data.sqlite3 레코드 수 일치")
            else:
                self.log(f"⚠️ market_data.sqlite3 레코드 수 불일치: {original_md.get('total_records')} → {target_md.get('total_records')}")
                
        # 전체 레코드 수 비교 (대략적)
        self.log(f"📊 전체 레코드 수 비교: 원본 {total_original_records} → 통합 {total_target_records}")
        
        if total_target_records >= total_original_records * 0.9:  # 90% 이상 유지
            self.log("✅ 전체 데이터 양 적절히 유지됨")
            return True
        else:
            self.log("⚠️ 데이터 손실 가능성 있음")
            return False
            
    def validate_database_functionality(self) -> bool:
        """데이터베이스 기능성 검증"""
        self.log("=== 데이터베이스 기능성 검증 시작 ===")
        
        target_files = [
            self.data_path / "settings.sqlite3",
            self.data_path / "strategies.sqlite3",
            self.data_path / "market_data.sqlite3"
        ]
        
        success = True
        
        for db_path in target_files:
            if not db_path.exists():
                self.log(f"❌ {db_path.name} 파일이 존재하지 않음")
                success = False
                continue
                
            try:
                with sqlite3.connect(db_path) as conn:
                    # 기본 쿼리 테스트
                    conn.execute("SELECT 1").fetchone()
                    
                    # 테이블 목록 조회
                    tables = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                    
                    # 각 테이블에 대한 간단한 쿼리
                    for table_name, in tables:
                        if not table_name.startswith('sqlite_'):
                            try:
                                conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
                            except Exception as e:
                                self.log(f"⚠️ {db_path.name}.{table_name} 테이블 쿼리 오류: {e}")
                    
                    self.log(f"✅ {db_path.name} 기능성 검증 통과")
                    
            except Exception as e:
                self.log(f"❌ {db_path.name} 기능성 검증 실패: {e}")
                success = False
                
        return success
        
    def generate_validation_report(self) -> str:
        """검증 보고서 생성"""
        report_path = self.legacy_path / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=== 데이터베이스 구조 통합 검증 보고서 ===\n")
            f.write(f"검증 시간: {datetime.now()}\n")
            f.write(f"작업 디렉토리: {self.base_path.absolute()}\n\n")
            
            # 상세 데이터베이스 정보
            f.write("=== 데이터베이스 상세 정보 ===\n")
            
            # 통합된 파일들 정보
            target_files = {
                "settings": self.data_path / "settings.sqlite3",
                "strategies": self.data_path / "strategies.sqlite3",
                "market_data": self.data_path / "market_data.sqlite3"
            }
            
            for name, path in target_files.items():
                f.write(f"\n📊 {name}.sqlite3:\n")
                info = self.get_db_info(path)
                
                if info.get("exists"):
                    if "error" in info:
                        f.write(f"  ❌ 오류: {info['error']}\n")
                    else:
                        f.write(f"  - 파일 크기: {info.get('file_size', 0):,} bytes\n")
                        f.write(f"  - 테이블 수: {info.get('total_tables', 0)}\n")
                        f.write(f"  - 총 레코드 수: {info.get('total_records', 0)}\n")
                        
                        for table_name, table_info in info.get("tables", {}).items():
                            f.write(f"    • {table_name}: {table_info['records']} 레코드\n")
                else:
                    f.write("  ❌ 파일이 존재하지 않음\n")
            
            f.write("\n=== 검증 로그 ===\n")
            for log_entry in self.validation_log:
                f.write(log_entry + "\n")
        
        self.log(f"📋 검증 보고서 저장: {report_path}")
        return str(report_path)
        
    def run_validation(self) -> bool:
        """전체 검증 실행"""
        self.log("🔍 데이터베이스 구조 통합 검증 시작")
        
        # 1. 마이그레이션 무결성 검증
        integrity_ok = self.validate_migration_integrity()
        
        # 2. 기능성 검증
        functionality_ok = self.validate_database_functionality()
        
        # 3. 보고서 생성
        report_path = self.generate_validation_report()
        
        # 4. 최종 결과
        overall_success = integrity_ok and functionality_ok
        
        if overall_success:
            self.log("🎉 모든 검증이 성공적으로 완료되었습니다!")
        else:
            self.log("⚠️ 일부 검증에서 문제가 발견되었습니다.")
            
        self.log(f"📋 상세 보고서: {report_path}")
        
        return overall_success


def main():
    """메인 실행 함수"""
    print("🔍 데이터베이스 구조 통합 검증 스크립트")
    print("TASK-20250728-01_Database_Structure_Unification 검증")
    print("=" * 50)
    
    validator = DatabaseValidator()
    
    # 검증 실행
    success = validator.run_validation()
    
    if success:
        print("\n✅ 검증이 성공적으로 완료되었습니다!")
    else:
        print("\n⚠️ 검증에서 문제가 발견되었습니다.")
        print("📋 상세 내용은 검증 보고서를 확인하세요.")


if __name__ == "__main__":
    main()
