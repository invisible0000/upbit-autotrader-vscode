#!/usr/bin/env python3
"""
YAML → DB 마이그레이션 스크립트
확장 테이블들(tv_help_texts, tv_parameter_types 등) 생성 및 데이터 이식
"""

import os
import sys
import sqlite3
import yaml
from pathlib import Path
from typing import Dict, List, Any
import shutil
from datetime import datetime

# 프로젝트 루트 경로 추가
project_root = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(project_root))

try:
    from upbit_auto_trading.utils.global_db_manager import get_database_path
except ImportError:
    print("⚠️ global_db_manager import 실패, 직접 경로 사용")
    def get_database_path(db_name):
        return project_root / "upbit_auto_trading" / "data" / f"{db_name}.sqlite3"

def backup_database():
    """데이터베이스 백업 생성"""
    db_path = get_database_path("settings")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"settings_migration_backup_{timestamp}.sqlite3"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ DB 백업 생성: {backup_path.name}")
        return backup_path
    except Exception as e:
        print(f"❌ 백업 생성 실패: {e}")
        return None

def load_yaml_file(yaml_path: Path) -> Dict[str, Any]:
    """YAML 파일 로드"""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ YAML 로드 실패 {yaml_path.name}: {e}")
        return {}

def create_extension_tables(cursor: sqlite3.Cursor):
    """확장 테이블들 생성"""
    
    # 1. tv_help_texts 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tv_help_texts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variable_id TEXT NOT NULL,
            parameter_name TEXT,
            help_text TEXT NOT NULL,
            help_type TEXT DEFAULT 'tooltip',
            language TEXT DEFAULT 'ko',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (variable_id) REFERENCES tv_trading_variables(variable_id)
        )
    ''')
    
    # 2. tv_placeholder_texts 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tv_placeholder_texts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variable_id TEXT NOT NULL,
            parameter_name TEXT,
            placeholder_text TEXT NOT NULL,
            input_type TEXT DEFAULT 'text',
            language TEXT DEFAULT 'ko',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (variable_id) REFERENCES tv_trading_variables(variable_id)
        )
    ''')
    
    # 3. tv_indicator_categories 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tv_indicator_categories (
            category_id TEXT PRIMARY KEY,
            category_name TEXT NOT NULL,
            description TEXT,
            display_order INTEGER DEFAULT 0,
            icon_name TEXT,
            color_code TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 4. tv_parameter_types 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tv_parameter_types (
            type_id TEXT PRIMARY KEY,
            type_name TEXT NOT NULL,
            description TEXT,
            validation_rule TEXT,
            default_widget TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 5. tv_workflow_guides 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tv_workflow_guides (
            guide_id TEXT PRIMARY KEY,
            guide_title TEXT NOT NULL,
            guide_content TEXT NOT NULL,
            step_order INTEGER DEFAULT 0,
            target_audience TEXT DEFAULT 'general',
            difficulty_level TEXT DEFAULT 'basic',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 6. tv_indicator_library 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tv_indicator_library (
            library_id TEXT PRIMARY KEY,
            variable_id TEXT NOT NULL,
            formula_expression TEXT,
            calculation_method TEXT,
            usage_examples TEXT,
            performance_notes TEXT,
            related_indicators TEXT,
            technical_notes TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (variable_id) REFERENCES tv_trading_variables(variable_id)
        )
    ''')
    
    print("✅ 확장 테이블 6개 생성 완료")

def migrate_help_texts(cursor: sqlite3.Cursor, data: Dict):
    """tv_help_texts 데이터 이식"""
    help_texts = data.get('help_texts', {})
    count = 0
    
    for variable_id, texts in help_texts.items():
        if isinstance(texts, dict):
            # 지표 레벨 도움말
            if 'indicator' in texts:
                cursor.execute('''
                    INSERT OR REPLACE INTO tv_help_texts 
                    (variable_id, parameter_name, help_text, help_type) 
                    VALUES (?, ?, ?, ?)
                ''', (variable_id, None, texts['indicator'], 'indicator'))
                count += 1
            
            # 파라미터 레벨 도움말
            if 'parameters' in texts:
                for param_name, param_help in texts['parameters'].items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO tv_help_texts 
                        (variable_id, parameter_name, help_text, help_type) 
                        VALUES (?, ?, ?, ?)
                    ''', (variable_id, param_name, param_help, 'parameter'))
                    count += 1
    
    print(f"✅ help_texts: {count}개 레코드 이식")

def migrate_placeholder_texts(cursor: sqlite3.Cursor, data: Dict):
    """tv_placeholder_texts 데이터 이식"""
    placeholder_texts = data.get('placeholder_texts', {})
    count = 0
    
    for variable_id, placeholders in placeholder_texts.items():
        if isinstance(placeholders, dict):
            for param_name, placeholder_text in placeholders.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO tv_placeholder_texts 
                    (variable_id, parameter_name, placeholder_text) 
                    VALUES (?, ?, ?)
                ''', (variable_id, param_name, placeholder_text))
                count += 1
    
    print(f"✅ placeholder_texts: {count}개 레코드 이식")

def migrate_indicator_categories(cursor: sqlite3.Cursor, data: Dict):
    """tv_indicator_categories 데이터 이식"""
    categories = data.get('categories', {})
    count = 0
    
    for category_id, category_info in categories.items():
        if isinstance(category_info, dict):
            cursor.execute('''
                INSERT OR REPLACE INTO tv_indicator_categories 
                (category_id, category_name, description, display_order, icon_name, color_code) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                category_id,
                category_info.get('name', category_id),
                category_info.get('description', ''),
                category_info.get('display_order', 0),
                category_info.get('icon', ''),
                category_info.get('color', '')
            ))
            count += 1
    
    print(f"✅ indicator_categories: {count}개 레코드 이식")

def migrate_parameter_types(cursor: sqlite3.Cursor, data: Dict):
    """tv_parameter_types 데이터 이식"""
    parameter_types = data.get('parameter_types', {})
    count = 0
    
    for type_id, type_info in parameter_types.items():
        if isinstance(type_info, dict):
            cursor.execute('''
                INSERT OR REPLACE INTO tv_parameter_types 
                (type_id, type_name, description, validation_rule, default_widget) 
                VALUES (?, ?, ?, ?, ?)
            ''', (
                type_id,
                type_info.get('name', type_id),
                type_info.get('description', ''),
                type_info.get('validation', ''),
                type_info.get('widget', 'text')
            ))
            count += 1
    
    print(f"✅ parameter_types: {count}개 레코드 이식")

def migrate_workflow_guides(cursor: sqlite3.Cursor, data: Dict):
    """tv_workflow_guides 데이터 이식"""
    workflow_guides = data.get('workflow_guides', {})
    count = 0
    
    for guide_id, guide_info in workflow_guides.items():
        if isinstance(guide_info, dict):
            cursor.execute('''
                INSERT OR REPLACE INTO tv_workflow_guides 
                (guide_id, guide_title, guide_content, step_order, target_audience, difficulty_level) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                guide_id,
                guide_info.get('title', guide_id),
                guide_info.get('content', ''),
                guide_info.get('order', 0),
                guide_info.get('audience', 'general'),
                guide_info.get('difficulty', 'basic')
            ))
            count += 1
    
    print(f"✅ workflow_guides: {count}개 레코드 이식")

def migrate_indicator_library(cursor: sqlite3.Cursor, data: Dict):
    """tv_indicator_library 데이터 이식"""
    indicator_library = data.get('indicator_library', {})
    count = 0
    
    for library_id, library_info in indicator_library.items():
        if isinstance(library_info, dict):
            cursor.execute('''
                INSERT OR REPLACE INTO tv_indicator_library 
                (library_id, variable_id, formula_expression, calculation_method, 
                 usage_examples, performance_notes, related_indicators, technical_notes) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                library_id,
                library_info.get('variable_id', library_id),
                library_info.get('formula', ''),
                library_info.get('calculation', ''),
                library_info.get('examples', ''),
                library_info.get('performance', ''),
                library_info.get('related', ''),
                library_info.get('notes', '')
            ))
            count += 1
    
    print(f"✅ indicator_library: {count}개 레코드 이식")

def verify_migration(cursor: sqlite3.Cursor):
    """마이그레이션 검증"""
    print("\n🔍 마이그레이션 결과 검증")
    print("=" * 40)
    
    tables = [
        'tv_help_texts',
        'tv_placeholder_texts', 
        'tv_indicator_categories',
        'tv_parameter_types',
        'tv_workflow_guides',
        'tv_indicator_library'
    ]
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"📋 {table}: {count}개 레코드")

def main():
    """메인 실행 함수"""
    print("🚀 YAML → DB 마이그레이션 시작")
    print("=" * 50)
    
    # 현재 디렉토리 설정
    current_dir = Path(__file__).parent
    
    # 백업 생성
    backup_path = backup_database()
    if not backup_path:
        print("❌ 백업 실패로 인한 마이그레이션 중단")
        return
    
    # DB 연결
    db_path = get_database_path("settings")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 1. 확장 테이블 생성
            print("\n📋 확장 테이블 생성")
            create_extension_tables(cursor)
            
            # 2. YAML 파일들 마이그레이션
            yaml_files = [
                ('tv_help_texts.yaml', migrate_help_texts),
                ('tv_placeholder_texts.yaml', migrate_placeholder_texts),
                ('tv_indicator_categories.yaml', migrate_indicator_categories),
                ('tv_parameter_types.yaml', migrate_parameter_types),
                ('tv_workflow_guides.yaml', migrate_workflow_guides),
                ('tv_indicator_library.yaml', migrate_indicator_library)
            ]
            
            print("\n📂 YAML 데이터 이식")
            for yaml_file, migrate_func in yaml_files:
                yaml_path = current_dir / yaml_file
                if yaml_path.exists():
                    print(f"\n📄 {yaml_file} 처리 중...")
                    data = load_yaml_file(yaml_path)
                    if data:
                        migrate_func(cursor, data)
                    else:
                        print(f"⚠️ {yaml_file}: 데이터 없음")
                else:
                    print(f"❌ {yaml_file}: 파일 없음")
            
            # 3. 커밋 및 검증
            conn.commit()
            verify_migration(cursor)
            
            print(f"\n✅ 마이그레이션 완료!")
            print(f"📁 백업 파일: {backup_path.name}")
            
    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 YAML → DB 마이그레이션 성공!")
    else:
        print("\n💥 마이그레이션 실패!")
