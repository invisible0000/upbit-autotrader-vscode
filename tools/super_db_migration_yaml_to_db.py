#!/usr/bin/env python3
"""
🔄 Super DB Migration: YAML → DB
===============================
Super 도구 시스템 - YAML 데이터를 3-Database 아키텍처로 마이그레이션

📋 기능:
- YAML 파일들을 정확한 DB로 분배 마이그레이션
- 3-Database 아키텍처 지원 (settings/strategies/market_data)
- 데이터 무결성 검증 및 상세 로깅

🎯 용도:
- 개발 과정에서 YAML 변경사항을 DB에 실시간 반영
- TV 시스템 변수 및 설정을 settings.sqlite3에 마이그레이션
- 통일된 ID 기반 딕셔너리 구조 처리

🚀 사용법:
python tools/super_db_migration_yaml_to_db.py

📂 Super 도구 명명 규칙: super_[domain]_[function].py
"""

import sys
import sqlite3
import yaml
import argparse
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/yaml_to_db_migration.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class YamlToDbMigrationTool:
    """YAML → DB 전문 마이그레이션 도구"""
    
    def __init__(self, data_info_path: str = None, db_path: str = None):
        """
        초기화
        
        Args:
            data_info_path: YAML 파일들이 있는 경로
            db_path: 데이터베이스 파일들이 있는 경로
        """
        # 기본 경로 설정
        project_root = Path(__file__).parent.parent
        self.data_info_path = Path(data_info_path) if data_info_path else project_root / "upbit_auto_trading" / "utils" / "trading_variables" / "gui_variables_DB_migration_util" / "data_info"
        self.db_path = Path(db_path) if db_path else project_root / "upbit_auto_trading" / "data"
        
        # YAML-테이블 매핑 (3개 DB 분리 구조)
        self.yaml_table_mapping = {
            # Settings DB: 프로그램 기본 기능 동작용
            "tv_trading_variables.yaml": ("settings.sqlite3", "tv_trading_variables"),
            "tv_variable_parameters.yaml": ("settings.sqlite3", "tv_variable_parameters"),
            "tv_help_texts.yaml": ("settings.sqlite3", "tv_help_texts"),
            "tv_placeholder_texts.yaml": ("settings.sqlite3", "tv_placeholder_texts"),
            "tv_indicator_categories.yaml": ("settings.sqlite3", "tv_indicator_categories"),
            "tv_parameter_types.yaml": ("settings.sqlite3", "tv_parameter_types"),
            "tv_comparison_groups.yaml": ("settings.sqlite3", "tv_comparison_groups"),
            "tv_indicator_library.yaml": ("settings.sqlite3", "tv_indicator_library"),
            # 향후 확장: strategies.sqlite3와 market_data.sqlite3용 YAML 파일들
        }
        
        logger.info("🚀 YAML→DB 마이그레이션 도구 초기화")
        logger.info(f"📂 Data Info Path: {self.data_info_path}")
        logger.info(f"🗄️ DB Path: {self.db_path}")
        logger.info(f"🔄 YAML-테이블 매핑: {len(self.yaml_table_mapping)}개")

    def load_yaml_data(self, yaml_file: str) -> Dict[str, Any]:
        """YAML 파일을 로드하고 통일된 형식으로 파싱"""
        yaml_path = self.data_info_path / yaml_file
        
        if not yaml_path.exists():
            raise FileNotFoundError(f"❌ YAML 파일이 존재하지 않음: {yaml_path}")
        
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            logger.info(f"✅ YAML 로드 성공: {yaml_file}")
            return data
            
        except yaml.YAMLError as e:
            logger.error(f"❌ YAML 파싱 오류 in {yaml_file}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ YAML 로드 실패 {yaml_file}: {e}")
            raise

    def get_db_connection(self, db_name: str) -> sqlite3.Connection:
        """데이터베이스 연결 생성"""
        db_file_path = self.db_path / db_name
        
        if not db_file_path.exists():
            raise FileNotFoundError(f"❌ DB 파일이 존재하지 않음: {db_file_path}")
        
        try:
            conn = sqlite3.connect(str(db_file_path))
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"❌ DB 연결 실패: {e}")
            raise

    def migrate_yaml_to_table(self, yaml_file: str, target_table: str, conn: sqlite3.Connection) -> int:
        """개별 YAML 파일을 테이블로 마이그레이션"""
        
        # YAML 데이터 로드
        yaml_data = self.load_yaml_data(yaml_file)
        
        # 테이블 초기화
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {target_table}")
        logger.info(f"🧹 테이블 초기화: {target_table}")
        
        # 데이터 삽입
        inserted_count = 0
        
        # 통일된 구조에서 실제 데이터 추출
        root_key = list(yaml_data.keys())[0]  # 첫 번째 루트 키 (예: trading_variables, parameter_types 등)
        actual_data = yaml_data[root_key]
        
        if not isinstance(actual_data, dict):
            raise ValueError(f"❌ {yaml_file}의 데이터가 예상된 딕셔너리 형식이 아닙니다")
        
        for item_id, item_data in actual_data.items():
            try:
                # 테이블별 특화 처리
                if target_table == "tv_trading_variables":
                    self._insert_trading_variable(cursor, item_id, item_data)
                elif target_table == "tv_variable_parameters":
                    self._insert_variable_parameter(cursor, item_id, item_data)
                elif target_table == "tv_help_texts":
                    self._insert_help_text(cursor, item_id, item_data)
                elif target_table == "tv_placeholder_texts":
                    self._insert_placeholder_text(cursor, item_id, item_data)
                elif target_table == "tv_indicator_categories":
                    self._insert_indicator_category(cursor, item_id, item_data)
                elif target_table == "tv_parameter_types":
                    self._insert_parameter_type(cursor, item_id, item_data)
                elif target_table == "tv_comparison_groups":
                    self._insert_comparison_group(cursor, item_id, item_data)
                elif target_table == "tv_indicator_library":
                    self._insert_indicator_library(cursor, item_id, item_data)
                else:
                    logger.warning(f"⚠️ 알 수 없는 테이블: {target_table}")
                    continue
                
                inserted_count += 1
                
            except Exception as e:
                logger.error(f"❌ 데이터 삽입 실패 ({item_id}): {e}")
                continue
        
        conn.commit()
        logger.info(f"✅ {yaml_file} → {target_table}: {inserted_count}개 레코드 마이그레이션 완료")
        return inserted_count

    def _insert_trading_variable(self, cursor: sqlite3.Cursor, variable_id: str, data: Dict):
        """tv_trading_variables 테이블에 데이터 삽입"""
        cursor.execute("""
            INSERT INTO tv_trading_variables (
                variable_id, display_name_ko, display_name_en,
                purpose_category, chart_category, comparison_group,
                parameter_required, description, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            variable_id,
            data.get('display_name_ko', ''),
            data.get('display_name_en', ''),
            data.get('purpose_category', ''),
            data.get('chart_category', ''),
            data.get('comparison_group', ''),
            bool(data.get('parameter_required', False)),
            data.get('description', ''),
            data.get('source', 'built-in')
        ))

    def _insert_variable_parameter(self, cursor: sqlite3.Cursor, param_id: str, data: Dict):
        """tv_variable_parameters 테이블에 데이터 삽입 - 유연한 형식 지원"""
        
        # enum_values 처리 - 다양한 형식 지원
        enum_values = data.get('enum_values')
        if isinstance(enum_values, list):
            enum_values_json = json.dumps(enum_values)
        elif isinstance(enum_values, str) and enum_values.strip():
            try:
                # 이미 JSON 문자열인지 확인
                json.loads(enum_values)
                enum_values_json = enum_values
            except json.JSONDecodeError:
                enum_values_json = None
        else:
            enum_values_json = None
        
        # 문자열에서 따옴표 제거 (값 정규화)
        def clean_value(value):
            if isinstance(value, str):
                return value.strip('"\'')
            return value
        
        cursor.execute("""
            INSERT INTO tv_variable_parameters (
                variable_id, parameter_name, parameter_type,
                default_value, min_value, max_value, enum_values,
                is_required, display_name_ko, display_name_en, description, display_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            clean_value(data.get('variable_id', '')),
            clean_value(data.get('parameter_name', '')),
            clean_value(data.get('parameter_type', 'integer')),
            clean_value(data.get('default_value', '')),
            clean_value(data.get('min_value')) if data.get('min_value') else None,
            clean_value(data.get('max_value')) if data.get('max_value') else None,
            enum_values_json,
            bool(data.get('is_required', True)),
            clean_value(data.get('display_name_ko', data.get('parameter_name', ''))),
            clean_value(data.get('display_name_en', data.get('parameter_name', ''))),
            clean_value(data.get('description', '')),
            int(data.get('display_order', 1))
        ))

    def _insert_help_text(self, cursor: sqlite3.Cursor, help_id: str, data: Dict):
        """tv_help_texts 테이블에 데이터 삽입"""
        cursor.execute("""
            INSERT INTO tv_help_texts (
                variable_id, parameter_name, help_text_ko, help_text_en,
                tooltip_ko, tooltip_en
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get('variable_id', ''),
            data.get('parameter_name', ''),
            data.get('help_text_ko', ''),
            data.get('help_text_en', ''),
            data.get('tooltip_ko', ''),
            data.get('tooltip_en', '')
        ))

    def _insert_placeholder_text(self, cursor: sqlite3.Cursor, placeholder_id: str, data: Dict):
        """tv_placeholder_texts 테이블에 데이터 삽입"""
        cursor.execute("""
            INSERT INTO tv_placeholder_texts (
                variable_id, parameter_name, placeholder_text_ko, placeholder_text_en,
                example_value, validation_pattern
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get('variable_id', ''),
            data.get('parameter_name', ''),
            data.get('placeholder_text_ko', ''),
            data.get('placeholder_text_en', ''),
            data.get('example_value', ''),
            data.get('validation_pattern', '')
        ))

    def _insert_indicator_category(self, cursor: sqlite3.Cursor, category_id: str, data: Dict):
        """tv_indicator_categories 테이블에 데이터 삽입"""
        cursor.execute("""
            INSERT INTO tv_indicator_categories (
                category_name, display_name_ko, display_name_en, description,
                chart_position, color_scheme, color_theme, display_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('category_id', category_id),
            data.get('display_name_ko', category_id),
            data.get('display_name_en', category_id),
            data.get('description', ''),
            data.get('chart_position', 'subplot'),
            data.get('color_scheme', 'default'),
            data.get('color_theme', '#007bff'),
            data.get('display_order', 0)
        ))

    def _insert_parameter_type(self, cursor: sqlite3.Cursor, type_id: str, data: Dict):
        """tv_parameter_types 테이블에 데이터 삽입"""
        cursor.execute("""
            INSERT INTO tv_parameter_types (
                type_name, description, validation_pattern, validation_example,
                ui_component, default_constraints
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get('type_id', type_id),
            data.get('description', ''),
            data.get('validation_pattern', ''),
            data.get('validation_example', ''),
            data.get('ui_component', 'input'),
            data.get('default_constraints', '')
        ))

    def _insert_comparison_group(self, cursor: sqlite3.Cursor, group_id: str, data: Dict):
        """tv_comparison_groups 테이블에 데이터 삽입"""
        cursor.execute("""
            INSERT INTO tv_comparison_groups (
                group_name, display_name_ko, display_name_en, description,
                compatibility_rules
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            data.get('group_id', group_id),
            data.get('group_name_ko', data.get('display_name_ko', group_id)),
            data.get('group_name_en', data.get('display_name_en', group_id)),
            data.get('description', ''),
            str(data.get('compatibility_rules', {}))
        ))

    def _insert_indicator_library(self, cursor: sqlite3.Cursor, indicator_id: str, data: Dict):
        """tv_indicator_library 테이블에 데이터 삽입"""
        cursor.execute("""
            INSERT INTO tv_indicator_library (
                indicator_id, display_name_ko, display_name_en, category,
                calculation_method, calculation_note, description, usage_examples
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('indicator_id', indicator_id),
            data.get('display_name_ko', indicator_id),
            data.get('display_name_en', indicator_id),
            data.get('category', ''),
            data.get('calculation_method', ''),
            data.get('calculation_note', ''),
            data.get('description', ''),
            str(data.get('usage_examples', {}))
        ))

    def migrate_all_files(self, yaml_files: List[str] = None) -> Dict[str, int]:
        """모든 YAML 파일을 DB로 마이그레이션"""
        
        if yaml_files is None:
            yaml_files = list(self.yaml_table_mapping.keys())
        
        results = {}
        total_migrated = 0
        
        logger.info(f"🚀 전체 마이그레이션 시작: {len(yaml_files)}개 파일")
        
        for yaml_file in yaml_files:
            if yaml_file not in self.yaml_table_mapping:
                logger.warning(f"⚠️ 매핑되지 않은 파일: {yaml_file}")
                continue
            
            try:
                db_name, table_name = self.yaml_table_mapping[yaml_file]
                
                with self.get_db_connection(db_name) as conn:
                    count = self.migrate_yaml_to_table(yaml_file, table_name, conn)
                    results[yaml_file] = count
                    total_migrated += count
                    
            except Exception as e:
                logger.error(f"❌ {yaml_file} 마이그레이션 실패: {e}")
                results[yaml_file] = 0
        
        logger.info(f"🎉 전체 마이그레이션 완료: {total_migrated}개 레코드 처리")
        return results


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="YAML to DB Migration Tool")
    parser.add_argument("--yaml-files", nargs="*", help="마이그레이션할 YAML 파일들 (기본값: 전체)")
    parser.add_argument("--data-info-path", help="YAML 파일 경로")
    parser.add_argument("--db-path", help="DB 파일 경로")
    parser.add_argument("--dry-run", action="store_true", help="실제 실행 없이 계획만 표시")
    
    args = parser.parse_args()
    
    try:
        # 도구 초기화
        tool = YamlToDbMigrationTool(args.data_info_path, args.db_path)
        
        if args.dry_run:
            print("🔍 Dry Run Mode: 다음 파일들이 마이그레이션될 예정입니다:")
            files = args.yaml_files or list(tool.yaml_table_mapping.keys())
            for yaml_file in files:
                if yaml_file in tool.yaml_table_mapping:
                    db_name, table_name = tool.yaml_table_mapping[yaml_file]
                    print(f"  📄 {yaml_file} → {db_name}.{table_name}")
            return
        
        # 마이그레이션 실행
        results = tool.migrate_all_files(args.yaml_files)
        
        # 결과 출력
        print("✅ YAML → DB 마이그레이션 완료!")
        print("📊 마이그레이션 결과:")
        for yaml_file, count in results.items():
            print(f"  📄 {yaml_file}: {count}개 레코드")
        
        total_count = sum(results.values())
        print(f"🎯 총 {total_count}개 레코드 마이그레이션 완료")
        
    except Exception as e:
        logger.error(f"❌ 마이그레이션 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
