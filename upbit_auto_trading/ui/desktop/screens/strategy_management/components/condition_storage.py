#!/usr/bin/env python3
"""
조건 저장소 - 데이터베이스 조건 저장/관리
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import os

class ConditionStorage:
    """조건을 데이터베이스에 저장/관리하는 클래스"""
    
    def __init__(self, db_path: str = "data/app_settings.sqlite3"):
        self.db_path = db_path
        self._ensure_database_exists()
        self._verify_unified_schema()
    
    def _ensure_database_exists(self):
        """데이터베이스 디렉토리 및 파일 생성"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _verify_unified_schema(self):
        """통합 데이터베이스 스키마 확인"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 필수 테이블 존재 확인
            required_tables = ['trading_conditions', 'strategies', 'system_settings']
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            for table in required_tables:
                if table not in existing_tables:
                    raise Exception(f"통합 데이터베이스에 필수 테이블 '{table}'이 없습니다. 마이그레이션을 먼저 실행하세요.")
            
            # 데이터베이스 버전 확인
            try:
                cursor.execute("SELECT value FROM system_settings WHERE key = 'db_version'")
                db_version = cursor.fetchone()
                if not db_version:
                    print("⚠️ 데이터베이스 버전 정보가 없습니다.")
                else:
                    print(f"✅ 통합 데이터베이스 연결됨 (버전: {db_version[0]})")
            except:
                print("⚠️ 시스템 설정 테이블에 접근할 수 없습니다.")
    
    def _create_tables(self):
        """조건 저장을 위한 테이블 생성"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 조건 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading_conditions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    variable_id TEXT NOT NULL,
                    variable_name TEXT NOT NULL,
                    variable_params TEXT,  -- JSON
                    operator TEXT NOT NULL,
                    comparison_type TEXT DEFAULT 'fixed',
                    target_value TEXT,
                    external_variable TEXT,  -- JSON
                    trend_direction TEXT DEFAULT 'static',
                    is_active BOOLEAN DEFAULT 1,
                    category TEXT DEFAULT 'custom',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0
                )
            """)
            
            # 조건 사용 이력 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS condition_usage_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    condition_id INTEGER,
                    strategy_name TEXT,
                    action_type TEXT,  -- 'buy', 'sell'
                    execution_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    market_data TEXT,  -- JSON
                    result_type TEXT,  -- 'success', 'failure', 'pending'
                    profit_loss REAL,
                    notes TEXT,
                    FOREIGN KEY (condition_id) REFERENCES trading_conditions (id)
                )
            """)
            
            # 조건 태그 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS condition_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    condition_id INTEGER,
                    tag_name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (condition_id) REFERENCES trading_conditions (id)
                )
            """)
            
            conn.commit()
    
    def save_condition(self, condition_data: Dict[str, Any], overwrite: bool = False) -> Tuple[bool, str, Optional[int]]:
        """조건 저장 (덮어쓰기 옵션 포함)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # ID가 있는 경우 (편집 모드)
                if 'id' in condition_data and condition_data['id'] is not None:
                    condition_id = condition_data['id']
                    
                    # ID로 기존 조건 확인
                    cursor.execute(
                        "SELECT id, name FROM trading_conditions WHERE id = ?",
                        (condition_id,)
                    )
                    existing_row = cursor.fetchone()
                    
                    if existing_row:
                        # 기존 조건 업데이트 (ID 기반)
                        cursor.execute("""
                            UPDATE trading_conditions SET
                                name = ?, description = ?, variable_id = ?, variable_name = ?,
                                variable_params = ?, operator = ?, comparison_type = ?,
                                target_value = ?, external_variable = ?, trend_direction = ?, 
                                category = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (
                            condition_data['name'],
                            condition_data.get('description', ''),
                            condition_data['variable_id'],
                            condition_data['variable_name'],
                            json.dumps(condition_data.get('variable_params', {}), ensure_ascii=False),
                            condition_data['operator'],
                            condition_data.get('comparison_type', 'fixed'),
                            condition_data.get('target_value'),
                            json.dumps(condition_data.get('external_variable'), ensure_ascii=False) if condition_data.get('external_variable') else None,
                            condition_data.get('trend_direction', 'static'),
                            condition_data.get('category', 'custom'),
                            condition_id
                        ))
                        
                        conn.commit()
                        return True, f"조건 '{condition_data['name']}'이 업데이트되었습니다. (ID: {condition_id})", condition_id
                    else:
                        return False, f"ID {condition_id}에 해당하는 조건을 찾을 수 없습니다.", None
                
                # ID가 없는 경우 (신규 생성)
                else:
                    # 이름 중복 확인
                    cursor.execute(
                        "SELECT id FROM trading_conditions WHERE name = ?",
                        (condition_data['name'],)
                    )
                    existing_row = cursor.fetchone()
                    
                    if existing_row and not overwrite:
                        return False, f"조건명 '{condition_data['name']}'이 이미 존재합니다.", None
                    
                    if existing_row and overwrite:
                        # 기존 조건 업데이트 (이름 기반)
                        condition_id = existing_row[0]
                        cursor.execute("""
                            UPDATE trading_conditions SET
                                description = ?, variable_id = ?, variable_name = ?,
                                variable_params = ?, operator = ?, comparison_type = ?,
                                target_value = ?, external_variable = ?, trend_direction = ?, 
                                category = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (
                            condition_data.get('description', ''),
                            condition_data['variable_id'],
                            condition_data['variable_name'],
                            json.dumps(condition_data.get('variable_params', {}), ensure_ascii=False),
                            condition_data['operator'],
                            condition_data.get('comparison_type', 'fixed'),
                            condition_data.get('target_value'),
                            json.dumps(condition_data.get('external_variable'), ensure_ascii=False) if condition_data.get('external_variable') else None,
                            condition_data.get('trend_direction', 'static'),
                            condition_data.get('category', 'custom'),
                            condition_id
                        ))
                        
                        conn.commit()
                        return True, f"조건 '{condition_data['name']}'이 업데이트되었습니다.", condition_id
                    
                    else:
                        # 새 조건 저장
                        cursor.execute("""
                            INSERT INTO trading_conditions (
                                name, description, variable_id, variable_name,
                                variable_params, operator, comparison_type,
                                target_value, external_variable, trend_direction, category
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            condition_data['name'],
                            condition_data.get('description', ''),
                            condition_data['variable_id'],
                            condition_data['variable_name'],
                            json.dumps(condition_data.get('variable_params', {}), ensure_ascii=False),
                            condition_data['operator'],
                            condition_data.get('comparison_type', 'fixed'),
                            condition_data.get('target_value'),
                            json.dumps(condition_data.get('external_variable'), ensure_ascii=False) if condition_data.get('external_variable') else None,
                            condition_data.get('trend_direction', 'static'),
                            condition_data.get('category', 'custom')
                        ))
                        
                        condition_id = cursor.lastrowid
                        conn.commit()
                        return True, f"조건 '{condition_data['name']}'이 저장되었습니다.", condition_id
                
        except sqlite3.IntegrityError as e:
            return False, f"데이터 무결성 오류: {str(e)}", None
        except Exception as e:
            return False, f"저장 중 오류 발생: {str(e)}", None
    
    def get_condition_by_id(self, condition_id: int) -> Optional[Dict[str, Any]]:
        """ID로 조건 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT * FROM trading_conditions WHERE id = ?",
                    (condition_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_condition_dict(row)
                return None
                
        except Exception as e:
            print(f"조건 조회 오류: {str(e)}")
            return None
    
    def get_condition_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """이름으로 조건 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT * FROM trading_conditions WHERE name = ?",
                    (name,)
                )
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_condition_dict(row)
                return None
                
        except Exception as e:
            print(f"조건 조회 오류: {str(e)}")
            return None
    
    def get_all_conditions(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """모든 조건 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM trading_conditions"
                if active_only:
                    query += " WHERE is_active = 1"
                query += " ORDER BY created_at DESC"
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                return [self._row_to_condition_dict(row) for row in rows]
                
        except Exception as e:
            print(f"조건 목록 조회 오류: {str(e)}")
            return []
    
    def get_conditions_by_category(self, category: str) -> List[Dict[str, Any]]:
        """카테고리별 조건 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT * FROM trading_conditions WHERE category = ? AND is_active = 1 ORDER BY created_at DESC",
                    (category,)
                )
                rows = cursor.fetchall()
                
                return [self._row_to_condition_dict(row) for row in rows]
                
        except Exception as e:
            print(f"카테고리별 조건 조회 오류: {str(e)}")
            return []
    
    def update_condition(self, condition_id: int, updates: Dict[str, Any]) -> Tuple[bool, str]:
        """조건 업데이트"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 업데이트할 필드들 구성
                set_clauses = []
                values = []
                
                for key, value in updates.items():
                    if key in ['name', 'description', 'operator', 'comparison_type', 
                              'target_value', 'trend_direction', 'category', 'is_active']:
                        set_clauses.append(f"{key} = ?")
                        values.append(value)
                    elif key == 'variable_params':
                        set_clauses.append("variable_params = ?")
                        values.append(json.dumps(value, ensure_ascii=False))
                    elif key == 'external_variable':
                        set_clauses.append("external_variable = ?")
                        values.append(json.dumps(value, ensure_ascii=False) if value else None)
                
                if not set_clauses:
                    return False, "업데이트할 필드가 없습니다."
                
                # updated_at 자동 갱신
                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                values.append(condition_id)
                
                query = f"UPDATE trading_conditions SET {', '.join(set_clauses)} WHERE id = ?"
                cursor.execute(query, values)
                
                if cursor.rowcount == 0:
                    return False, "조건을 찾을 수 없습니다."
                
                conn.commit()
                return True, "조건이 업데이트되었습니다."
                
        except Exception as e:
            return False, f"업데이트 중 오류: {str(e)}"
    
    def delete_condition(self, condition_id: int) -> Tuple[bool, str]:
        """조건 삭제 (소프트 삭제)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "UPDATE trading_conditions SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (condition_id,)
                )
                
                if cursor.rowcount == 0:
                    return False, "조건을 찾을 수 없습니다."
                
                conn.commit()
                return True, "조건이 삭제되었습니다."
                
        except Exception as e:
            return False, f"삭제 중 오류: {str(e)}"
    
    def search_conditions(self, keyword: str) -> List[Dict[str, Any]]:
        """조건 검색"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM trading_conditions 
                    WHERE is_active = 1 AND (
                        name LIKE ? OR 
                        description LIKE ? OR 
                        variable_name LIKE ?
                    )
                    ORDER BY created_at DESC
                """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
                
                rows = cursor.fetchall()
                return [self._row_to_condition_dict(row) for row in rows]
                
        except Exception as e:
            print(f"조건 검색 오류: {str(e)}")
            return []
    
    def get_condition_statistics(self) -> Dict[str, Any]:
        """조건 통계 정보"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 전체 조건 수
                cursor.execute("SELECT COUNT(*) FROM trading_conditions WHERE is_active = 1")
                total_conditions = cursor.fetchone()[0]
                
                # 카테고리별 조건 수
                cursor.execute("""
                    SELECT category, COUNT(*) 
                    FROM trading_conditions 
                    WHERE is_active = 1 
                    GROUP BY category
                """)
                category_stats = dict(cursor.fetchall())
                
                # 변수별 조건 수
                cursor.execute("""
                    SELECT variable_id, COUNT(*) 
                    FROM trading_conditions 
                    WHERE is_active = 1 
                    GROUP BY variable_id
                    ORDER BY COUNT(*) DESC
                """)
                variable_stats = dict(cursor.fetchall())
                
                return {
                    "total_conditions": total_conditions,
                    "category_distribution": category_stats,
                    "variable_distribution": variable_stats,
                    "last_updated": datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"통계 조회 오류: {str(e)}")
            return {"error": str(e)}
    
    def _row_to_condition_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """DB 행을 조건 딕셔너리로 변환"""
        condition = {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "variable_id": row["variable_id"],
            "variable_name": row["variable_name"],
            "operator": row["operator"],
            "comparison_type": row["comparison_type"],
            "target_value": row["target_value"],
            "trend_direction": row["trend_direction"],
            "is_active": bool(row["is_active"]),
            "category": row["category"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "usage_count": row["usage_count"],
            "success_rate": row["success_rate"]
        }
        
        # JSON 필드 파싱
        try:
            if row["variable_params"]:
                condition["variable_params"] = json.loads(row["variable_params"])
            else:
                condition["variable_params"] = {}
        except json.JSONDecodeError:
            condition["variable_params"] = {}
        
        try:
            if row["external_variable"]:
                condition["external_variable"] = json.loads(row["external_variable"])
            else:
                condition["external_variable"] = None
        except json.JSONDecodeError:
            condition["external_variable"] = None
        
        return condition
