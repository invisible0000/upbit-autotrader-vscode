#!/usr/bin/env python3
"""
🎯 Super DB Direct Query
데이터베이스 직접 쿼리 실행 및 결과 확인 도구

🤖 LLM 사용 가이드:
===================
이 도구는 DB에 대해 직접 SQL 쿼리를 실행하고 결과를 확인하는 도구입니다.

📋 주요 명령어 (tools 폴더에서 실행):
1. python super_db_direct_query.py --query "SELECT * FROM tv_trading_variables LIMIT 5;" --database settings
2. python super_db_direct_query.py --query "PRAGMA table_info(tv_trading_variables);" --database settings
3. python super_db_direct_query.py --query "SELECT COUNT(*) FROM trading_conditions;" --database strategies
4. python super_db_direct_query.py --query "SELECT name FROM sqlite_master WHERE type='table';" --database settings

🎯 언제 사용하면 좋은가:
- 특정 테이블의 스키마 구조 확인할 때 (PRAGMA table_info)
- 테이블 데이터 샘플 조회할 때
- 컬럼 존재 여부 확인할 때
- 데이터 개수나 통계 확인할 때
- 복잡한 조건으로 데이터 검색할 때

💡 출력 해석:
- 쿼리 결과를 표 형태로 보기 좋게 출력
- 결과가 많을 경우 자동으로 제한
- 에러 발생 시 상세한 오류 메시지 제공

안전 기능:
1. 읽기 전용 쿼리만 허용 (SELECT, PRAGMA)
2. 위험한 쿼리 자동 차단 (DROP, DELETE, UPDATE)
3. 결과 행 수 제한으로 메모리 보호

작성일: 2025-08-01
작성자: Upbit Auto Trading Team
"""

import sqlite3
import argparse
import logging
import sys
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

# 프로젝트 루트를 파이썬 패스에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SuperDBDirectQuery:
    """
    🎯 Super DB Direct Query - 직접 쿼리 실행 도구
    
    🤖 LLM 사용 패턴:
    query_tool = SuperDBDirectQuery()
    query_tool.execute_query("SELECT * FROM tv_trading_variables LIMIT 5;", "settings")
    query_tool.check_column_exists("tv_trading_variables", "category", "settings")
    query_tool.get_table_schema("tv_trading_variables", "settings")
    
    💡 핵심 기능: 안전한 쿼리 실행 + 결과 포매팅 + 스키마 확인
    """
    
    def __init__(self):
        """초기화 - 경로 및 안전 규칙 설정"""
        self.project_root = PROJECT_ROOT
        self.data_path = self.project_root / "upbit_auto_trading" / "data"
        
        # DB 경로 매핑
        self.db_mapping = {
            "settings": self.data_path / "settings.sqlite3",
            "strategies": self.data_path / "strategies.sqlite3",
            "market_data": self.data_path / "market_data.sqlite3"
        }
        
        # 허용된 쿼리 패턴 (읽기 전용)
        self.allowed_patterns = [
            r'^SELECT\s+',
            r'^PRAGMA\s+',
            r'^EXPLAIN\s+',
            r'^WITH\s+'
        ]
        
        # 금지된 쿼리 패턴 (데이터 변경)
        self.forbidden_patterns = [
            r'\bDROP\b',
            r'\bDELETE\b',
            r'\bUPDATE\b',
            r'\bINSERT\b',
            r'\bALTER\b',
            r'\bCREATE\b',
            r'\bTRUNCATE\b'
        ]
        
        # 결과 행 수 제한
        self.max_rows = 100
        
    def _validate_query_safety(self, query: str) -> Tuple[bool, str]:
        """
        쿼리 안전성 검증
        
        Args:
            query: 실행할 SQL 쿼리
            
        Returns:
            (is_safe, message): 안전 여부와 메시지
        """
        query_upper = query.upper().strip()
        
        # 금지된 패턴 검사
        for pattern in self.forbidden_patterns:
            if re.search(pattern, query_upper, re.IGNORECASE):
                return False, f"위험한 쿼리 패턴 감지: {pattern}"
        
        # 허용된 패턴 검사
        is_allowed = False
        for pattern in self.allowed_patterns:
            if re.match(pattern, query_upper, re.IGNORECASE):
                is_allowed = True
                break
                
        if not is_allowed:
            return False, "허용되지 않은 쿼리 타입입니다. SELECT, PRAGMA, EXPLAIN, WITH만 허용됩니다."
            
        return True, "안전한 쿼리입니다."
    
    def _get_database_path(self, database: str) -> Path:
        """
        데이터베이스 경로 반환
        
        Args:
            database: 데이터베이스 이름 또는 경로
            
        Returns:
            데이터베이스 파일 경로
        """
        if database in self.db_mapping:
            return self.db_mapping[database]
        
        # 직접 경로인 경우
        db_path = Path(database)
        if db_path.exists():
            return db_path
            
        # 상대 경로인 경우
        relative_path = self.project_root / database
        if relative_path.exists():
            return relative_path
            
        raise FileNotFoundError(f"데이터베이스를 찾을 수 없습니다: {database}")
    
    def execute_query(self, query: str, database: str = "settings") -> Dict[str, Any]:
        """
        쿼리 실행 및 결과 반환
        
        Args:
            query: 실행할 SQL 쿼리
            database: 대상 데이터베이스
            
        Returns:
            실행 결과 딕셔너리
        """
        try:
            # 쿼리 안전성 검증
            is_safe, message = self._validate_query_safety(query)
            if not is_safe:
                return {
                    "success": False,
                    "error": message,
                    "query": query,
                    "database": database
                }
            
            # DB 연결
            db_path = self._get_database_path(database)
            
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row  # Dict-like access
                cursor = conn.cursor()
                
                # 쿼리 실행
                cursor.execute(query)
                
                # 결과 가져오기 (제한된 행 수)
                if query.upper().strip().startswith('SELECT') or query.upper().strip().startswith('WITH'):
                    rows = cursor.fetchmany(self.max_rows)
                    columns = [description[0] for description in cursor.description] if cursor.description else []
                    
                    # 더 많은 데이터가 있는지 확인
                    has_more = len(cursor.fetchmany(1)) > 0
                    
                    return {
                        "success": True,
                        "rows": [dict(row) for row in rows],
                        "columns": columns,
                        "row_count": len(rows),
                        "has_more": has_more,
                        "query": query,
                        "database": database,
                        "db_path": str(db_path)
                    }
                else:
                    # PRAGMA 등의 경우
                    rows = cursor.fetchall()
                    columns = [description[0] for description in cursor.description] if cursor.description else []
                    
                    return {
                        "success": True,
                        "rows": [dict(row) for row in rows],
                        "columns": columns,
                        "row_count": len(rows),
                        "has_more": False,
                        "query": query,
                        "database": database,
                        "db_path": str(db_path)
                    }
                    
        except sqlite3.Error as e:
            return {
                "success": False,
                "error": f"SQLite 오류: {str(e)}",
                "query": query,
                "database": database
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"예상치 못한 오류: {str(e)}",
                "query": query,
                "database": database
            }
    
    def check_column_exists(self, table_name: str, column_name: str, database: str = "settings") -> bool:
        """
        특정 테이블에 컬럼이 존재하는지 확인
        
        Args:
            table_name: 테이블 이름
            column_name: 컬럼 이름
            database: 데이터베이스 이름
            
        Returns:
            컬럼 존재 여부
        """
        query = f"PRAGMA table_info({table_name});"
        result = self.execute_query(query, database)
        
        if not result["success"]:
            logger.error(f"테이블 정보 조회 실패: {result['error']}")
            return False
            
        for row in result["rows"]:
            if row.get("name") == column_name:
                return True
                
        return False
    
    def get_table_schema(self, table_name: str, database: str = "settings") -> Optional[List[Dict[str, Any]]]:
        """
        테이블 스키마 정보 반환
        
        Args:
            table_name: 테이블 이름
            database: 데이터베이스 이름
            
        Returns:
            스키마 정보 리스트
        """
        query = f"PRAGMA table_info({table_name});"
        result = self.execute_query(query, database)
        
        if result["success"]:
            return result["rows"]
        else:
            logger.error(f"스키마 조회 실패: {result['error']}")
            return None
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        쿼리 결과를 보기 좋게 포매팅
        
        Args:
            result: execute_query 결과
            
        Returns:
            포매팅된 문자열
        """
        output = []
        output.append("="*80)
        output.append("🎯 Super DB Direct Query 결과")
        output.append("="*80)
        
        if not result["success"]:
            output.append(f"❌ 쿼리 실행 실패")
            output.append(f"🔍 쿼리: {result['query']}")
            output.append(f"🗄️ 데이터베이스: {result['database']}")
            output.append(f"⚠️ 오류: {result['error']}")
            return "\\n".join(output)
        
        output.append(f"✅ 쿼리 실행 성공")
        output.append(f"🔍 쿼리: {result['query']}")
        output.append(f"🗄️ 데이터베이스: {result['database']}")
        output.append(f"📂 DB 경로: {result['db_path']}")
        output.append(f"📊 결과 행 수: {result['row_count']}")
        
        if result['has_more']:
            output.append(f"⚠️ 더 많은 데이터가 있습니다 (최대 {self.max_rows}행만 표시)")
        
        output.append("")
        
        if result['rows']:
            # 테이블 형태로 출력 (기본 라이브러리 사용)
            if result['columns']:
                # 헤더 출력
                output.append(" | ".join(result['columns']))
                output.append("-" * (len(" | ".join(result['columns']))))
                
                # 데이터 출력
                for row in result['rows']:
                    row_data = [str(v) if v is not None else "NULL" for v in row.values()]
                    output.append(" | ".join(row_data))
            else:
                for i, row in enumerate(result['rows'], 1):
                    output.append(f"Row {i}: {dict(row)}")
        else:
            output.append("📋 결과가 없습니다.")
        
        return "\\n".join(output)


def main():
    """메인 함수 - CLI 인터페이스"""
    parser = argparse.ArgumentParser(
        description="🎯 Super DB Direct Query - 데이터베이스 직접 쿼리 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 테이블 스키마 확인
  python super_db_direct_query.py --query "PRAGMA table_info(tv_trading_variables);" --database settings
  
  # 데이터 샘플 조회
  python super_db_direct_query.py --query "SELECT * FROM tv_trading_variables LIMIT 5;" --database settings
  
  # 테이블 목록 조회
  python super_db_direct_query.py --query "SELECT name FROM sqlite_master WHERE type='table';" --database settings
  
  # 데이터 개수 확인
  python super_db_direct_query.py --query "SELECT COUNT(*) as count FROM trading_conditions;" --database strategies
        """
    )
    
    parser.add_argument(
        "--query", "-q",
        required=True,
        help="실행할 SQL 쿼리 (SELECT, PRAGMA, EXPLAIN, WITH만 허용)"
    )
    
    parser.add_argument(
        "--database", "-d",
        default="settings",
        help="대상 데이터베이스 (settings, strategies, market_data 또는 파일 경로)"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["table", "json", "csv"],
        default="table",
        help="출력 형식 (기본값: table)"
    )
    
    args = parser.parse_args()
    
    # 도구 초기화
    query_tool = SuperDBDirectQuery()
    
    print("🚀 Super DB Direct Query v1.0 시작")
    print("=" * 60)
    
    # 쿼리 실행
    result = query_tool.execute_query(args.query, args.database)
    
    # 결과 출력
    if args.format == "table":
        print(query_tool.format_result(result))
    elif args.format == "json":
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    elif args.format == "csv":
        if result["success"] and result["rows"]:
            import csv
            import io
            output = io.StringIO()
            if result["columns"]:
                writer = csv.DictWriter(output, fieldnames=result["columns"])
                writer.writeheader()
                for row in result["rows"]:
                    writer.writerow(row)
            print(output.getvalue())
        else:
            print("CSV 출력을 위한 데이터가 없습니다.")
    
    # 종료 상태
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
