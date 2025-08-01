#!/usr/bin/env python3
"""
🔄 Super DB Schema Extractor
현재 DB에서 완전한 스키마 추출 도구

🤖 LLM 사용 가이드:
===================
이 도구는 현재 DB 상태를 완전한 스키마 파일로 추출하는 도구입니다.

📋 주요 명령어 (tools 폴더에서 실행):
1. python super_db_schema_extractor.py                    # settings DB 스키마 추출 (기본)
2. python super_db_schema_extractor.py settings          # settings DB 스키마 추출
3. python super_db_schema_extractor.py market_data       # market_data DB 스키마 추출
4. python super_db_schema_extractor.py strategies        # strategies DB 스키마 추출

🎯 언제 사용하면 좋은가:
- GUI 마이그레이션 도구의 스키마 파일 업데이트할 때
- 현재 DB 상태를 백업용 스키마로 저장할 때
- 다른 환경과 DB 구조 동기화할 때
- 스키마 버전 관리가 필요할 때

💡 출력 파일 형식:
- GUI 업데이트용: upbit_autotrading_unified_schema.sql (기존 파일 덮어쓰기)
- 백업용: upbit_autotrading_unified_schema_now_YYYYMMDD_HHMMSS.sql

기능:
1. 모든 테이블 CREATE 문 추출
2. 인덱스 정보 포함
3. 타임스탬프 기반 백업 파일 생성
4. 추출 결과 자동 검증

작성일: 2025-07-31
작성자: Upbit Auto Trading Team
"""

import sqlite3
import os
import re
from datetime import datetime
from typing import List, Optional


class SuperDBSchemaExtractor:
    """
    🔄 현재 DB에서 완전한 스키마 추출 도구
    
    🤖 LLM 사용 패턴:
    extractor = SuperSchemaExtractor()
    extractor.extract_schema()                    # 📊 settings DB 스키마 추출 (기본)
    extractor.extract_schema('market_data')      # 🔍 특정 DB 스키마 추출
    extractor.extract_schema('settings', True)   # 💾 백업 파일로 저장
    
    💡 지원 DB: settings, market_data, strategies
    💡 출력 위치: gui_variables_DB_migration_util/data_info/
    """
    
    def __init__(self):
        self.db_paths = {
            'settings': 'upbit_auto_trading/data/settings.sqlite3',
            'market_data': 'upbit_auto_trading/data/market_data.sqlite3',
            'strategies': 'upbit_auto_trading/data/strategies.sqlite3'
        }
        self.output_dir = 'upbit_auto_trading/utils/trading_variables/gui_variables_DB_migration_util/data_info'
    
    def extract_schema(self, db_name: str = 'settings', create_backup: bool = False) -> Optional[str]:
        """
        🤖 LLM 추천: 메인 스키마 추출 메서드
        현재 DB 상태를 완전한 스키마 파일로 추출
        
        Args:
            db_name: 추출할 DB ('settings', 'market_data', 'strategies')
            create_backup: True면 타임스탬프 백업 파일 생성, False면 기본 파일 덮어쓰기
        
        Returns:
            str: 생성된 스키마 파일 경로 (성공시), None (실패시)
        
        출력 예시:
        🔄 === SETTINGS DB 스키마 추출 ===
        📊 총 27개 테이블 추출 완료
        💾 스키마 파일 생성: upbit_autotrading_unified_schema.sql
        ✅ 검증 완료: 27개 테이블 확인됨
        """
        if db_name not in self.db_paths:
            print(f"❌ 지원하지 않는 DB: {db_name}")
            print(f"📋 지원 DB 목록: {list(self.db_paths.keys())}")
            return None
            
        db_path = self.db_paths[db_name]
        if not os.path.exists(db_path):
            print(f"❌ DB 파일이 존재하지 않습니다: {db_path}")
            return None
        
        print(f"🔄 === {db_name.upper()} DB 스키마 추출 ===")
        
        try:
            # 스키마 추출 실행
            schema_content, table_count = self._extract_schema_content(db_path, db_name)
            
            # 출력 파일 경로 결정
            output_path = self._get_output_path(create_backup)
            
            # 스키마 파일 저장
            self._save_schema_file(output_path, schema_content)
            
            # 결과 검증 및 출력
            verified_count = self._verify_schema_file(output_path)
            
            print(f"📊 총 {table_count}개 테이블 추출 완료")
            print(f"💾 스키마 파일 생성: {os.path.basename(output_path)}")
            print(f"✅ 검증 완료: {verified_count}개 테이블 확인됨")
            
            if table_count != verified_count:
                print(f"⚠️ 경고: 추출({table_count})과 검증({verified_count}) 테이블 수 불일치")
            
            return output_path
            
        except Exception as e:
            print(f"❌ 스키마 추출 중 오류: {e}")
            return None
    
    def _extract_schema_content(self, db_path: str, db_name: str) -> tuple[str, int]:
        """DB에서 스키마 내용 추출"""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 스키마 헤더 생성
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            schema_lines = [
                "-- Upbit Auto Trading Unified Schema",
                f"-- 완전한 통합 스키마 ({db_name} DB에서 추출)",
                f"-- 생성일: {timestamp}",
                f"-- 추출 도구: Super DB Schema Extractor",
                "PRAGMA foreign_keys = ON;",
                ""
            ]
            
            # 모든 테이블 추출 (sqlite_sequence 제외)
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name != 'sqlite_sequence' 
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # 각 테이블의 CREATE 문 추출
            for table_name in tables:
                cursor.execute("""
                    SELECT sql FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table_name,))
                
                create_sql = cursor.fetchone()
                if create_sql and create_sql[0]:
                    schema_lines.append(f"-- Table: {table_name}")
                    schema_lines.append(create_sql[0] + ";")
                    schema_lines.append("")
            
            # 인덱스 추출
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='index' AND sql IS NOT NULL 
                ORDER BY name
            """)
            indexes = cursor.fetchall()
            
            if indexes:
                schema_lines.append("-- Indexes")
                for index in indexes:
                    if index[0]:
                        schema_lines.append(index[0] + ";")
                schema_lines.append("")
            
            return '\n'.join(schema_lines), len(tables)
    
    def _get_output_path(self, create_backup: bool) -> str:
        """출력 파일 경로 생성"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        if create_backup:
            # 타임스탬프 백업 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"upbit_autotrading_unified_schema_now_{timestamp}.sql"
        else:
            # 기본 파일명 (GUI 도구가 사용하는 파일)
            filename = "upbit_autotrading_unified_schema.sql"
        
        return os.path.join(self.output_dir, filename)
    
    def _save_schema_file(self, output_path: str, content: str) -> None:
        """스키마 파일 저장"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _verify_schema_file(self, file_path: str) -> int:
        """생성된 스키마 파일 검증"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # CREATE TABLE 문 개수 확인
        create_patterns = re.findall(
            r'CREATE TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+(\w+)\s*\(',
            content,
            re.IGNORECASE
        )
        
        return len(create_patterns)
    
    def list_available_databases(self) -> None:
        """
        🤖 LLM 추천: 사용 가능한 DB 목록 확인
        현재 시스템에서 스키마 추출 가능한 DB들을 표시
        """
        print("🔍 === 스키마 추출 가능한 DB 목록 ===")
        
        for db_name, db_path in self.db_paths.items():
            if os.path.exists(db_path):
                # 테이블 수 확인
                try:
                    with sqlite3.connect(db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                        table_count = cursor.fetchone()[0]
                    
                    print(f"  ✅ {db_name:<12} ({table_count}개 테이블) - {db_path}")
                except:
                    print(f"  ⚠️ {db_name:<12} (접근 오류) - {db_path}")
            else:
                print(f"  ❌ {db_name:<12} (파일 없음) - {db_path}")


def main():
    """
    🤖 LLM 사용 가이드: 메인 실행 함수
    
    명령행 인수에 따라 다른 동작 수행:
    - 인수 없음: settings DB 스키마 추출 (기본값, GUI 파일 업데이트)
    - 'settings'/'market_data'/'strategies': 특정 DB 스키마 추출
    - 'list': 사용 가능한 DB 목록 표시
    - 'backup': settings DB 스키마를 백업 파일로 추출
    
    🎯 LLM이 자주 사용할 패턴:
    1. python super_schema_extractor.py              # GUI 스키마 파일 업데이트
    2. python super_schema_extractor.py backup       # 현재 상태 백업
    3. python super_schema_extractor.py list         # DB 상태 확인
    """
    import sys
    
    extractor = SuperDBSchemaExtractor()
    
    if len(sys.argv) == 1:
        # 기본값: settings DB 스키마 추출 (GUI 파일 업데이트)
        extractor.extract_schema('settings', create_backup=False)
        
    elif len(sys.argv) == 2:
        cmd = sys.argv[1].lower()
        
        if cmd == 'list':
            extractor.list_available_databases()
        elif cmd == 'backup':
            # 백업 파일로 추출
            extractor.extract_schema('settings', create_backup=True)
        elif cmd in extractor.db_paths:
            # 특정 DB 스키마 추출
            extractor.extract_schema(cmd, create_backup=False)
        else:
            print(f"❌ 알 수 없는 명령어: {cmd}")
            print_usage()
    else:
        print_usage()


def print_usage():
    """
    🤖 LLM을 위한 상세 사용법 가이드
    사용자가 도구 사용법을 물어볼 때 이 내용을 참조하세요
    """
    print("""
🔄 Super DB Schema Extractor 사용법:

🤖 === LLM을 위한 핵심 가이드 ===
가장 많이 사용할 명령어들:

1️⃣ GUI 스키마 파일 업데이트 (가장 기본, 자주 사용):
   python super_db_schema_extractor.py

2️⃣ 현재 상태 백업 생성:
   python super_db_schema_extractor.py backup

3️⃣ 사용 가능한 DB 확인:
   python super_db_schema_extractor.py list

📋 === 전체 명령어 목록 ===
기본 사용:
  python super_db_schema_extractor.py              # settings DB → GUI 스키마 파일 업데이트 ⭐ 가장 유용
  python super_db_schema_extractor.py settings     # settings DB 스키마 추출
  python super_db_schema_extractor.py market_data  # market_data DB 스키마 추출
  python super_db_schema_extractor.py strategies   # strategies DB 스키마 추출

백업 및 관리:
  python super_db_schema_extractor.py backup       # 타임스탬프 백업 파일 생성 ⭐ 중요한 변경 전 필수
  python super_db_schema_extractor.py list         # 사용 가능한 DB 목록 표시

💡 === 출력 파일 설명 ===
• 기본 모드: upbit_autotrading_unified_schema.sql (GUI 도구가 사용하는 파일)
• 백업 모드: upbit_autotrading_unified_schema_now_20250731_143022.sql

🎯 === 활용 시나리오 ===
• GUI 마이그레이션 도구 업데이트: 기본 모드로 스키마 파일 갱신
• 중요한 변경 전 백업: backup 모드로 현재 상태 보존
• 다른 환경과 동기화: 특정 DB 스키마 추출 후 배포
• 스키마 버전 관리: 정기적인 백업으로 변경 이력 관리
""")


if __name__ == "__main__":
    main()
