#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
차트 변수 카테고리 시스템 마이그레이션

기존 데이터베이스에 변수 카테고리 시스템을 위한 테이블들을 추가합니다.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Any


class ChartVariableMigration:
    """차트 변수 카테고리 시스템 마이그레이션 클래스"""

    def __init__(self, db_path: str = "data/app_settings.sqlite3"):
        self.db_path = db_path
        self.migration_version = "1.0.0"

    def run_migration(self):
        """마이그레이션 실행"""
        print("🔄 차트 변수 카테고리 시스템 마이그레이션 시작...")
        
        try:
            self._ensure_database_exists()
            self._create_chart_variable_tables()
            self._insert_default_variables()
            self._update_migration_version()
            print("✅ 마이그레이션 완료!")
            
        except Exception as e:
            print(f"❌ 마이그레이션 실패: {e}")
            raise

    def _ensure_database_exists(self):
        """데이터베이스 파일 존재 확인"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"데이터베이스 파일을 찾을 수 없습니다: {self.db_path}")

    def _create_chart_variable_tables(self):
        """차트 변수 관련 테이블 생성"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 1. chart_variables 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chart_variables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    variable_id TEXT NOT NULL UNIQUE,
                    variable_name TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    display_type TEXT NOT NULL,
                    scale_min REAL,
                    scale_max REAL,
                    unit TEXT DEFAULT '',
                    default_color TEXT DEFAULT '#007bff',
                    subplot_height_ratio REAL DEFAULT 0.3,
                    compatible_categories TEXT,  -- JSON
                    is_active INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 2. variable_compatibility_rules 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS variable_compatibility_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    base_variable_id TEXT NOT NULL,
                    compatible_category TEXT NOT NULL,
                    compatibility_reason TEXT,
                    min_value_constraint REAL,
                    max_value_constraint REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (base_variable_id) REFERENCES chart_variables (variable_id)
                )
            """)

            # 3. chart_layout_templates 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chart_layout_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    main_chart_height_ratio REAL DEFAULT 0.6,
                    subplot_configurations TEXT NOT NULL,  -- JSON
                    color_palette TEXT,  -- JSON
                    is_default INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 4. variable_usage_logs 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS variable_usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    variable_id TEXT NOT NULL,
                    condition_id INTEGER,
                    usage_context TEXT NOT NULL,
                    chart_display_info TEXT,  -- JSON
                    render_time_ms INTEGER,
                    user_feedback TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (variable_id) REFERENCES chart_variables (variable_id)
                )
            """)

            # 인덱스 생성
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_chart_variables_category ON chart_variables (category)",
                "CREATE INDEX IF NOT EXISTS idx_chart_variables_active ON chart_variables (is_active)",
                "CREATE INDEX IF NOT EXISTS idx_compatibility_base_var ON variable_compatibility_rules (base_variable_id)",
                "CREATE INDEX IF NOT EXISTS idx_usage_logs_variable ON variable_usage_logs (variable_id)",
                "CREATE INDEX IF NOT EXISTS idx_usage_logs_context ON variable_usage_logs (usage_context)",
            ]

            for index_sql in indexes:
                cursor.execute(index_sql)

            conn.commit()
            print("📊 차트 변수 테이블 생성 완료")

    def _insert_default_variables(self):
        """기본 변수들 삽입"""
        default_variables = [
            # 시가 차트 오버레이 변수들
            {
                'variable_id': 'current_price',
                'variable_name': '현재가',
                'description': '현재 시장 가격',
                'category': 'price_overlay',
                'display_type': 'main_level',
                'unit': '원',
                'default_color': '#1f77b4',
                'compatible_categories': ['price_overlay', 'currency']
            },
            {
                'variable_id': 'moving_average',
                'variable_name': '이동평균',
                'description': '이동평균선 지표',
                'category': 'price_overlay',
                'display_type': 'main_line',
                'unit': '원',
                'default_color': '#ff7f0e',
                'compatible_categories': ['price_overlay']
            },
            {
                'variable_id': 'bollinger_band',
                'variable_name': '볼린저밴드',
                'description': '볼린저 밴드 지표',
                'category': 'price_overlay',
                'display_type': 'main_band',
                'unit': '원',
                'default_color': '#2ca02c',
                'compatible_categories': ['price_overlay']
            },

            # 오실레이터 변수들
            {
                'variable_id': 'rsi',
                'variable_name': 'RSI',
                'description': 'Relative Strength Index',
                'category': 'oscillator',
                'display_type': 'subplot_line',
                'scale_min': 0,
                'scale_max': 100,
                'unit': '%',
                'default_color': '#d62728',
                'subplot_height_ratio': 0.25,
                'compatible_categories': ['oscillator', 'percentage']
            },
            {
                'variable_id': 'stochastic',
                'variable_name': '스토캐스틱',
                'description': 'Stochastic Oscillator',
                'category': 'oscillator',
                'display_type': 'subplot_line',
                'scale_min': 0,
                'scale_max': 100,
                'unit': '%',
                'default_color': '#ff69b4',
                'subplot_height_ratio': 0.25,
                'compatible_categories': ['oscillator', 'percentage']
            },

            # 모멘텀 지표들
            {
                'variable_id': 'macd',
                'variable_name': 'MACD',
                'description': 'Moving Average Convergence Divergence',
                'category': 'momentum',
                'display_type': 'subplot_line',
                'unit': '',
                'default_color': '#9467bd',
                'subplot_height_ratio': 0.3,
                'compatible_categories': ['momentum']
            },

            # 거래량 지표들
            {
                'variable_id': 'volume',
                'variable_name': '거래량',
                'description': '거래량 지표',
                'category': 'volume',
                'display_type': 'subplot_histogram',
                'unit': '',
                'default_color': '#8c564b',
                'subplot_height_ratio': 0.2,
                'compatible_categories': ['volume']
            }
        ]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for var_data in default_variables:
                # 호환 카테고리를 JSON으로 변환
                compatible_json = json.dumps(var_data.pop('compatible_categories', []))
                var_data['compatible_categories'] = compatible_json

                # 변수 삽입 (중복 시 무시)
                cursor.execute("""
                    INSERT OR IGNORE INTO chart_variables 
                    (variable_id, variable_name, description, category, display_type, 
                     scale_min, scale_max, unit, default_color, subplot_height_ratio, 
                     compatible_categories, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    var_data['variable_id'],
                    var_data['variable_name'],
                    var_data.get('description'),
                    var_data['category'],
                    var_data['display_type'],
                    var_data.get('scale_min'),
                    var_data.get('scale_max'),
                    var_data.get('unit', ''),
                    var_data.get('default_color', '#007bff'),
                    var_data.get('subplot_height_ratio', 0.3),
                    var_data['compatible_categories']
                ))

            conn.commit()
            print("📝 기본 변수 데이터 삽입 완료")

    def _insert_compatibility_rules(self):
        """호환성 규칙 삽입"""
        compatibility_rules = [
            # RSI 호환성 규칙
            {
                'base_variable_id': 'rsi',
                'compatible_category': 'oscillator',
                'compatibility_reason': '같은 오실레이터 계열로 0-100 스케일 공유',
                'min_value_constraint': 0,
                'max_value_constraint': 100
            },
            {
                'base_variable_id': 'rsi',
                'compatible_category': 'percentage',
                'compatibility_reason': '퍼센트 단위로 0-100 범위 호환',
                'min_value_constraint': 0,
                'max_value_constraint': 100
            },

            # 현재가 호환성 규칙
            {
                'base_variable_id': 'current_price',
                'compatible_category': 'price_overlay',
                'compatibility_reason': '같은 가격 스케일 사용',
            },
            {
                'base_variable_id': 'current_price',
                'compatible_category': 'currency',
                'compatibility_reason': '통화 단위 호환',
            },

            # MACD 호환성 규칙
            {
                'base_variable_id': 'macd',
                'compatible_category': 'momentum',
                'compatibility_reason': '모멘텀 지표 계열로 비슷한 스케일 사용',
            }
        ]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for rule in compatibility_rules:
                cursor.execute("""
                    INSERT OR IGNORE INTO variable_compatibility_rules
                    (base_variable_id, compatible_category, compatibility_reason,
                     min_value_constraint, max_value_constraint)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    rule['base_variable_id'],
                    rule['compatible_category'],
                    rule['compatibility_reason'],
                    rule.get('min_value_constraint'),
                    rule.get('max_value_constraint')
                ))

            conn.commit()
            print("🔗 호환성 규칙 삽입 완료")

    def _insert_default_layout_templates(self):
        """기본 레이아웃 템플릿 삽입"""
        templates = [
            {
                'template_name': 'standard_trading',
                'description': '표준 트레이딩 차트 레이아웃',
                'main_chart_height_ratio': 0.6,
                'subplot_configurations': {
                    'rsi': {'height_ratio': 0.15, 'position': 1},
                    'macd': {'height_ratio': 0.15, 'position': 2},
                    'volume': {'height_ratio': 0.1, 'position': 3}
                },
                'color_palette': {
                    'primary': '#1f77b4',
                    'secondary': '#ff7f0e',
                    'success': '#2ca02c',
                    'warning': '#ff8c00',
                    'danger': '#d62728'
                },
                'is_default': 1
            },
            {
                'template_name': 'minimal',
                'description': '최소 차트 레이아웃 (메인 차트만)',
                'main_chart_height_ratio': 1.0,
                'subplot_configurations': {},
                'color_palette': {
                    'primary': '#007bff',
                    'secondary': '#6c757d'
                },
                'is_default': 0
            }
        ]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for template in templates:
                cursor.execute("""
                    INSERT OR IGNORE INTO chart_layout_templates
                    (template_name, description, main_chart_height_ratio,
                     subplot_configurations, color_palette, is_default)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    template['template_name'],
                    template['description'],
                    template['main_chart_height_ratio'],
                    json.dumps(template['subplot_configurations']),
                    json.dumps(template['color_palette']),
                    template['is_default']
                ))

            conn.commit()
            print("🎨 기본 레이아웃 템플릿 삽입 완료")

    def _update_migration_version(self):
        """마이그레이션 버전 업데이트"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # system_settings 테이블에 마이그레이션 정보 기록
            cursor.execute("""
                INSERT OR REPLACE INTO system_settings (key, value, description, updated_at)
                VALUES (?, ?, ?, ?)
            """, (
                'chart_variable_migration_version',
                self.migration_version,
                '차트 변수 카테고리 시스템 마이그레이션 버전',
                datetime.now().isoformat()
            ))

            conn.commit()
            print(f"📋 마이그레이션 버전 {self.migration_version} 기록 완료")

    def verify_migration(self):
        """마이그레이션 검증"""
        print("🔍 마이그레이션 검증 중...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 테이블 존재 확인
            tables_to_check = [
                'chart_variables',
                'variable_compatibility_rules', 
                'chart_layout_templates',
                'variable_usage_logs'
            ]

            for table in tables_to_check:
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,)
                )
                if cursor.fetchone():
                    print(f"✅ {table} 테이블 존재")
                else:
                    print(f"❌ {table} 테이블 없음")

            # 기본 데이터 확인
            cursor.execute("SELECT COUNT(*) FROM chart_variables")
            var_count = cursor.fetchone()[0]
            print(f"📊 등록된 변수 수: {var_count}")

            cursor.execute("SELECT COUNT(*) FROM chart_layout_templates WHERE is_default=1")
            default_template_count = cursor.fetchone()[0]
            print(f"🎨 기본 템플릿 수: {default_template_count}")

        print("✅ 마이그레이션 검증 완료")


def main():
    """메인 실행 함수"""
    migration = ChartVariableMigration()
    
    try:
        migration.run_migration()
        migration._insert_compatibility_rules()
        migration._insert_default_layout_templates()
        migration.verify_migration()
        
    except Exception as e:
        print(f"❌ 실행 중 오류 발생: {e}")
        return False
    
    return True


if __name__ == "__main__":
    main()
