#!/usr/bin/env python3
"""
Super DB Data Migrator v1.0 - 데이터베이스 간 데이터 마이그레이션 도구
================================================================================
🎯 목적: DB 간 테이블 데이터 복사, 스키마 매핑, 데이터 변환
🔧 기능: 
- 테이블 간 데이터 복사
- 컬럼명 매핑 (소스 → 타겟)
- 데이터 변환 (JSON, 타입 변환 등)
- 안전한 트랜잭션 처리
- 중복 데이터 처리 옵션
================================================================================
"""

import sqlite3
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import os

class SuperDBDataMigrator:
    """데이터베이스 간 데이터 마이그레이션 도구"""
    
    def __init__(self):
        self.version = "1.0"
        self.session_log = []
    
    def migrate_data(self, 
                    source_db: str, 
                    target_db: str, 
                    source_table: str, 
                    target_table: str,
                    column_mapping: Optional[Dict[str, str]] = None,
                    where_condition: Optional[str] = None,
                    skip_duplicates: bool = True,
                    dry_run: bool = False) -> Tuple[bool, str, int]:
        """
        데이터 마이그레이션 실행
        
        Args:
            source_db: 소스 데이터베이스 경로
            target_db: 타겟 데이터베이스 경로
            source_table: 소스 테이블명
            target_table: 타겟 테이블명 (기본값: source_table과 동일)
            column_mapping: 컬럼 매핑 (소스컬럼 -> 타겟컬럼)
            where_condition: WHERE 조건 (예: "id > 0")
            skip_duplicates: 중복 데이터 건너뛰기
            dry_run: 실제 실행하지 않고 미리보기만
        
        Returns:
            (성공여부, 메시지, 처리된_행수)
        """
        try:
            print(f"🚀 Super DB Data Migrator v{self.version} 시작")
            print("=" * 60)
            
            # 데이터베이스 경로 검증
            if not os.path.exists(source_db):
                return False, f"소스 DB를 찾을 수 없습니다: {source_db}", 0
            
            # 타겟 테이블명 기본값 설정
            if not target_table:
                target_table = source_table
            
            # 소스 데이터 조회
            source_data = self._fetch_source_data(source_db, source_table, where_condition)
            if not source_data:
                return False, "소스 데이터가 없습니다.", 0
            
            print(f"📊 소스 데이터: {len(source_data)}개 행 발견")
            
            # 타겟 스키마 확인
            target_schema = self._get_table_schema(target_db, target_table)
            if not target_schema:
                return False, f"타겟 테이블 '{target_table}'을 찾을 수 없습니다.", 0
            
            print(f"🎯 타겟 스키마: {len(target_schema)}개 컬럼")
            
            # 컬럼 매핑 처리
            if not column_mapping:
                column_mapping = self._auto_generate_mapping(source_data[0], target_schema)
            
            print(f"🔗 컬럼 매핑: {len(column_mapping)}개 매핑")
            for src, tgt in column_mapping.items():
                print(f"   {src} → {tgt}")
            
            # 데이터 변환
            transformed_data = self._transform_data(source_data, column_mapping, target_schema)
            print(f"🔄 데이터 변환: {len(transformed_data)}개 행 처리됨")
            
            if dry_run:
                print("🔍 DRY RUN 모드 - 실제 데이터는 변경되지 않습니다")
                self._preview_data(transformed_data[:3])  # 처음 3개 행만 미리보기
                return True, f"DRY RUN 완료: {len(transformed_data)}개 행 처리 예정", len(transformed_data)
            
            # 실제 데이터 삽입
            inserted_count = self._insert_data(target_db, target_table, transformed_data, skip_duplicates)
            
            print(f"✅ 마이그레이션 완료: {inserted_count}개 행 삽입됨")
            return True, f"성공적으로 {inserted_count}개 행을 마이그레이션했습니다.", inserted_count
            
        except Exception as e:
            error_msg = f"마이그레이션 실패: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg, 0
    
    def _fetch_source_data(self, db_path: str, table_name: str, where_condition: Optional[str] = None) -> List[Dict[str, Any]]:
        """소스 데이터 조회"""
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = f"SELECT * FROM {table_name}"
            if where_condition:
                query += f" WHERE {where_condition}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            print(f"❌ 소스 데이터 조회 실패: {e}")
            return []
    
    def _get_table_schema(self, db_path: str, table_name: str) -> List[Dict[str, Any]]:
        """테이블 스키마 조회"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            schema = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'name': row[1],
                    'type': row[2],
                    'notnull': row[3],
                    'default': row[4],
                    'pk': row[5]
                }
                for row in schema
            ]
            
        except Exception as e:
            print(f"❌ 스키마 조회 실패: {e}")
            return []
    
    def _auto_generate_mapping(self, sample_row: Dict[str, Any], target_schema: List[Dict[str, Any]]) -> Dict[str, str]:
        """자동 컬럼 매핑 생성"""
        source_columns = set(sample_row.keys())
        target_columns = {col['name'] for col in target_schema}
        
        mapping = {}
        
        # 정확히 일치하는 컬럼들
        for col in source_columns.intersection(target_columns):
            mapping[col] = col
        
        # 유사한 컬럼명 매핑 (기본 규칙들)
        similarity_rules = {
            'condition_name': 'name',  # settings → strategies 매핑
            'description': 'description',
            'created_at': 'created_at',
            'updated_at': 'updated_at',
            'is_active': 'is_active'
        }
        
        for src, tgt in similarity_rules.items():
            if src in source_columns and tgt in target_columns and src not in mapping:
                mapping[src] = tgt
        
        return mapping
    
    def _transform_data(self, source_data: List[Dict[str, Any]], 
                       column_mapping: Dict[str, str], 
                       target_schema: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """데이터 변환"""
        transformed = []
        target_columns = {col['name']: col for col in target_schema}
        
        for row in source_data:
            new_row = {}
            
            # 매핑된 컬럼들 처리
            for src_col, tgt_col in column_mapping.items():
                if src_col in row and tgt_col in target_columns:
                    value = row[src_col]
                    
                    # 타입 변환 처리
                    target_type = target_columns[tgt_col]['type']
                    new_row[tgt_col] = self._convert_value(value, target_type)
            
            # variable_mappings 데이터 특별 처리
            if 'variable_mappings' in row:
                self._parse_variable_mappings(row['variable_mappings'], new_row)
            
            # 필수 컬럼 기본값 설정
            for col_info in target_schema:
                col_name = col_info['name']
                if col_name not in new_row:
                    if col_info['notnull'] and col_info['default'] is None:
                        # NOT NULL 컬럼에 기본값 설정
                        new_row[col_name] = self._get_default_value(col_info['type'])
                    elif col_info['default'] is not None:
                        new_row[col_name] = col_info['default']
            
            transformed.append(new_row)
        
        return transformed
    
    def _parse_variable_mappings(self, json_data: str, target_row: Dict[str, Any]) -> None:
        """variable_mappings JSON을 strategies 테이블 컬럼들로 분리"""
        try:
            if not json_data:
                return
            
            # JSON 파싱
            mapping_data = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            # strategies 테이블 컬럼들로 매핑
            if 'variable_id' in mapping_data:
                target_row['variable_id'] = mapping_data['variable_id']
            if 'variable_name' in mapping_data:
                target_row['variable_name'] = mapping_data['variable_name']
            if 'variable_params' in mapping_data:
                target_row['variable_params'] = json.dumps(mapping_data['variable_params'], ensure_ascii=False)
            if 'operator' in mapping_data:
                target_row['operator'] = mapping_data['operator']
            if 'comparison_type' in mapping_data:
                target_row['comparison_type'] = mapping_data['comparison_type']
            if 'target_value' in mapping_data:
                target_row['target_value'] = mapping_data['target_value']
            if 'external_variable' in mapping_data:
                ext_var = mapping_data['external_variable']
                target_row['external_variable'] = json.dumps(ext_var, ensure_ascii=False) if ext_var else None
            if 'trend_direction' in mapping_data:
                target_row['trend_direction'] = mapping_data['trend_direction']
            if 'chart_category' in mapping_data:
                target_row['chart_category'] = mapping_data['chart_category']
                
        except (json.JSONDecodeError, TypeError) as e:
            print(f"⚠️ JSON 파싱 실패: {e}")
            # 파싱 실패 시 기본값 설정
            target_row['variable_id'] = ''
            target_row['variable_name'] = ''
            target_row['operator'] = ''
    
    def _convert_value(self, value: Any, target_type: str) -> Any:
        """값 타입 변환"""
        if value is None:
            return None
        
        target_type = target_type.upper()
        
        try:
            if target_type in ['INTEGER', 'INT']:
                return int(value) if value != '' else None
            elif target_type in ['REAL', 'FLOAT', 'DOUBLE']:
                return float(value) if value != '' else None
            elif target_type in ['TEXT', 'VARCHAR', 'CHAR']:
                return str(value)
            elif target_type == 'BOOLEAN':
                if isinstance(value, bool):
                    return value
                if isinstance(value, (int, str)):
                    return bool(int(value))
            elif target_type in ['DATETIME', 'TIMESTAMP']:
                if isinstance(value, str):
                    return value
                return str(value)
            else:
                return value
        except (ValueError, TypeError):
            return None
    
    def _get_default_value(self, column_type: str) -> Any:
        """컬럼 타입별 기본값 반환"""
        column_type = column_type.upper()
        
        if column_type in ['INTEGER', 'INT']:
            return 0
        elif column_type in ['REAL', 'FLOAT', 'DOUBLE']:
            return 0.0
        elif column_type in ['TEXT', 'VARCHAR', 'CHAR']:
            return ''
        elif column_type == 'BOOLEAN':
            return False
        elif column_type in ['DATETIME', 'TIMESTAMP']:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            return None
    
    def _insert_data(self, db_path: str, table_name: str, data: List[Dict[str, Any]], skip_duplicates: bool) -> int:
        """데이터 삽입"""
        if not data:
            return 0
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        inserted_count = 0
        
        try:
            # 컬럼 목록 구성
            columns = list(data[0].keys())
            placeholders = ', '.join(['?' for _ in columns])
            columns_str = ', '.join(columns)
            
            if skip_duplicates:
                query = f"INSERT OR IGNORE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            else:
                query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            for row in data:
                values = [row.get(col) for col in columns]
                cursor.execute(query, values)
                if cursor.rowcount > 0:
                    inserted_count += 1
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 데이터 삽입 실패: {e}")
            raise
        finally:
            conn.close()
        
        return inserted_count
    
    def _preview_data(self, sample_data: List[Dict[str, Any]]):
        """데이터 미리보기"""
        print("\n🔍 데이터 미리보기 (처음 3개 행):")
        print("-" * 80)
        
        for i, row in enumerate(sample_data, 1):
            print(f"행 {i}:")
            for key, value in row.items():
                print(f"  {key}: {value}")
            print("-" * 40)


def main():
    parser = argparse.ArgumentParser(description='Super DB Data Migrator - 데이터베이스 간 데이터 마이그레이션')
    
    parser.add_argument('--source-db', required=True, help='소스 데이터베이스 경로')
    parser.add_argument('--target-db', required=True, help='타겟 데이터베이스 경로')
    parser.add_argument('--source-table', required=True, help='소스 테이블명')
    parser.add_argument('--target-table', help='타겟 테이블명 (기본값: source-table과 동일)')
    parser.add_argument('--where', help='WHERE 조건 (예: "id > 0")')
    parser.add_argument('--mapping', help='컬럼 매핑 JSON (예: {"old_name":"new_name"})')
    parser.add_argument('--allow-duplicates', action='store_true', help='중복 데이터 허용')
    parser.add_argument('--dry-run', action='store_true', help='실제 실행하지 않고 미리보기만')
    
    args = parser.parse_args()
    
    # 컬럼 매핑 파싱
    column_mapping = None
    if args.mapping:
        try:
            column_mapping = json.loads(args.mapping)
        except json.JSONDecodeError:
            print("❌ 잘못된 매핑 JSON 형식입니다.")
            return
    
    # 마이그레이션 실행
    migrator = SuperDBDataMigrator()
    success, message, count = migrator.migrate_data(
        source_db=args.source_db,
        target_db=args.target_db,
        source_table=args.source_table,
        target_table=args.target_table,
        column_mapping=column_mapping,
        where_condition=args.where,
        skip_duplicates=not args.allow_duplicates,
        dry_run=args.dry_run
    )
    
    if success:
        print(f"\n✅ {message}")
    else:
        print(f"\n❌ {message}")
        exit(1)


if __name__ == "__main__":
    main()
