#!/usr/bin/env python3
"""
🔄 Super DB Extraction DB to YAML
DB → YAML 전용 추출 도구

📋 **주요 기능**:
- 3-Database에서 YAML 파일로 데이터 역추출
- 백업용 YAML 생성 및 편집용 추출
- 타임스탬프 기반 버전 관리
- 데이터 무결성 검증

🎯 **사용법 가이드**:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 1. **전체 DB → YAML 추출**:
   python tools/super_db_extraction_db_to_yaml.py
   python tools/super_db_extraction_db_to_yaml.py --source settings

📖 2. **특정 테이블만 추출**:
   python tools/super_db_extraction_db_to_yaml.py --tables tv_trading_variables tv_variable_parameters
   python tools/super_db_extraction_db_to_yaml.py --source strategies --tables user_strategies

📖 3. **백업용 추출 (타임스탬프 포함)**:
   python tools/super_db_extraction_db_to_yaml.py --backup
   python tools/super_db_extraction_db_to_yaml.py --source settings --backup --output-dir "backup_20250801"

📖 4. **다른 DB 추출**:
   python tools/super_db_extraction_db_to_yaml.py --source market_data
   python tools/super_db_extraction_db_to_yaml.py --source strategies

📖 5. **완전한 예시**:
   python tools/super_db_extraction_db_to_yaml.py \
     --source settings \
     --tables tv_trading_variables tv_variable_parameters tv_help_texts \
     --backup \
     --output-dir "manual_edit_backup"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 **추출 모드 설명**:
- **편집용**: 기존 YAML 파일 덮어쓰기 (--backup 없음)
- **백업용**: 타임스탬프 추가된 새 YAML 파일 생성 (--backup)
- **특정 테이블**: 지정된 테이블만 선택적 추출 (--tables)

📊 **출력 파일 설명**:
- **편집용**: tv_trading_variables.yaml (기존 파일 덮어쓰기)
- **백업용**: tv_trading_variables_backup_20250801_143052.yaml

🎯 **Super 에이전트 활용법**:
1. DB 변경 전: 현재 상태를 YAML로 백업
2. 수동 편집: YAML 편집 후 다시 DB로 마이그레이션
3. 버전 관리: 중요 변경사항을 타임스탬프 백업으로 보존
4. 데이터 분석: YAML 형태로 데이터 구조 분석

💡 **팁**:
- 중요한 변경 전에는 반드시 --backup 옵션 사용
- 특정 테이블만 작업할 때는 --tables로 범위 제한
- 출력 디렉토리를 지정하여 체계적 백업 관리

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sys
import sqlite3
import yaml
import json
import logging
import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# 프로젝트 루트를 파이썬 패스에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/super_db_extraction_db_to_yaml.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class ExtractionMetadata:
    """추출 메타데이터 관리 클래스"""
    
    def __init__(self, source_db_path: str, source_table: str, target_file: str, 
                 record_count: int, extraction_mode: str, extraction_options: Dict[str, Any] = None):
        self.source_db_path = Path(source_db_path).resolve()
        self.source_table = source_table
        self.target_file = target_file
        self.record_count = record_count
        self.extraction_time = datetime.now()
        self.extraction_mode = extraction_mode
        self.extraction_options = extraction_options or {}
        self.tool_version = "super_db_extraction_db_to_yaml.py v1.1"
    
    def generate_header_comment(self) -> str:
        """상세한 메타데이터 주석 생성"""
        options_str = ""
        if self.extraction_options:
            options_list = [f"{k}: {v}" for k, v in self.extraction_options.items()]
            options_str = f"\n# 추출 옵션: {', '.join(options_list)}"
        
        return f"""# ════════════════════════════════════════════════════════════════
# 🔄 Super DB Extraction - Metadata
# ════════════════════════════════════════════════════════════════
# 추출 소스: {self.source_db_path}
# 소스 테이블: {self.source_table} ({self.record_count}개 레코드)
# 추출 시점: {self.extraction_time.strftime('%Y-%m-%d %H:%M:%S')}
# 추출 모드: {self.extraction_mode}{options_str}
# 대상 파일: {self.target_file}
# 추출 도구: {self.tool_version}
# ────────────────────────────────────────────────────────────────
# 📝 편집 안내:
# - 이 파일은 DB에서 추출된 실제 데이터입니다
# - 편집 후 super_yaml_editor_workflow.py로 DB 반영 가능
# - 변경 전 반드시 백업을 확인하세요
# ════════════════════════════════════════════════════════════════

"""


class SuperDBExtractionDBToYAML:
    """DB → YAML 전용 추출 도구 (Super 에이전트 지원)"""
    
    def __init__(self):
        """초기화 - 경로 및 설정 준비"""
        self.project_root = PROJECT_ROOT
        data_info_base = self.project_root / "upbit_auto_trading" / "utils"
        self.data_info_path = (
            data_info_base / "trading_variables" /
            "gui_variables_DB_migration_util" / "data_info"
        )
        self.db_path = self.project_root / "upbit_auto_trading" / "data"
        
        # 로그 디렉토리 생성
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 테이블 → YAML 매핑 (역매핑)
        self.table_yaml_mapping = {
            'tv_trading_variables': 'tv_trading_variables.yaml',
            'tv_variable_parameters': 'tv_variable_parameters.yaml',
            'tv_help_texts': 'tv_help_texts.yaml',
            'tv_placeholder_texts': 'tv_placeholder_texts.yaml',
            'tv_indicator_categories': 'tv_indicator_categories.yaml',
            'tv_parameter_types': 'tv_parameter_types.yaml',
            'tv_indicator_library': 'tv_indicator_library.yaml',
            'tv_comparison_groups': 'tv_comparison_groups.yaml',
            'cfg_app_settings': 'cfg_app_settings.yaml',
            'cfg_system_settings': 'cfg_system_settings.yaml'
        }
        
        logger.info("🔄 Super DB Extraction DB to YAML 초기화")
        logger.info(f"📂 Data Info Path: {self.data_info_path}")
        logger.info(f"🗄️ DB Path: {self.db_path}")
        logger.info(f"🔄 테이블-YAML 매핑: {len(self.table_yaml_mapping)}개")
        
        # 추출 세션 메타데이터 저장소
        self.extraction_metadata = {}
        
    def get_db_connection(self, db_name: str) -> sqlite3.Connection:
        """DB 연결 생성"""
        db_file = self.db_path / f"{db_name}.sqlite3"
        
        if not db_file.exists():
            raise FileNotFoundError(f"DB 파일이 존재하지 않습니다: {db_file}")
            
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row  # Dict-like access
        return conn
        
    def get_available_tables(self, db_name: str) -> List[str]:
        """DB에서 추출 가능한 테이블 목록 조회"""
        try:
            with self.get_db_connection(db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT IN ('sqlite_sequence', 'tv_schema_version')
                    ORDER BY name
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                # 매핑에 있는 테이블만 필터링
                available_tables = [table for table in tables if table in self.table_yaml_mapping]
                
                logger.info(f"📊 {db_name} DB에서 추출 가능한 테이블: {len(available_tables)}개")
                return available_tables
                
        except Exception as e:
            logger.error(f"❌ 테이블 목록 조회 실패 ({db_name}): {e}")
            return []
    
    def extract_db_to_yaml(self, source_db: str = 'settings',
                           target_tables: Optional[List[str]] = None,
                           backup_mode: bool = False,
                           output_dir: Optional[str] = None) -> bool:
        """DB → YAML 메인 추출 함수"""
        try:
            logger.info(f"🔄 === {source_db.upper()} DB → YAML 추출 시작 ===")
            
            # 출력 디렉토리 설정
            if output_dir:
                output_path = self.project_root / output_dir
                output_path.mkdir(exist_ok=True)
            else:
                output_path = self.data_info_path
            
            # 추출할 테이블 결정
            available_tables = self.get_available_tables(source_db)
            if target_tables:
                tables_to_extract = [table for table in target_tables if table in available_tables]
                if not tables_to_extract:
                    logger.warning(f"⚠️ 지정된 테이블이 DB에 없음: {target_tables}")
                    return False
            else:
                tables_to_extract = available_tables
            
            if not tables_to_extract:
                logger.warning("⚠️ 추출할 테이블이 없습니다")
                return False
            
            logger.info(f"📋 추출 대상: {len(tables_to_extract)}개 테이블")
            for table in tables_to_extract:
                logger.info(f"   • {table} → {self.table_yaml_mapping[table]}")
            
            # 추출 실행
            with self.get_db_connection(source_db) as conn:
                success_count = 0
                total_records = 0
                
                for table_name in tables_to_extract:
                    yaml_filename = self.table_yaml_mapping[table_name]
                    
                    # 백업 모드인 경우 파일명 수정
                    if backup_mode:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        yaml_filename = yaml_filename.replace('.yaml', f'_backup_{timestamp}.yaml')
                    
                    # 테이블 데이터 추출
                    yaml_data, record_count = self._extract_table_to_yaml(conn, table_name)
                    
                    if yaml_data is not None:
                        # 메타데이터 생성
                        extraction_mode = "백업 모드" if backup_mode else "편집 모드"
                        if target_tables:
                            extraction_mode += " (특정 테이블)"
                        
                        metadata = ExtractionMetadata(
                            source_db_path=str(self.db_path / f"{source_db}.sqlite3"),
                            source_table=table_name,
                            target_file=yaml_filename,
                            record_count=record_count,
                            extraction_mode=extraction_mode,
                            extraction_options={
                                "backup_mode": backup_mode,
                                "specific_tables": target_tables is not None,
                                "output_directory": str(output_path) if output_dir else "default"
                            }
                        )
                        
                        # YAML 파일 저장 (메타데이터 포함)
                        output_file = output_path / yaml_filename
                        if self._save_yaml_file(output_file, yaml_data, metadata):
                            success_count += 1
                            total_records += record_count
                            logger.info(f"✅ {table_name} → {yaml_filename}: {record_count}개 레코드")
                        else:
                            logger.error(f"❌ {table_name} → {yaml_filename}: 저장 실패")
                    else:
                        logger.error(f"❌ {table_name}: 추출 실패")
                
                logger.info("🎉 DB → YAML 추출 완료")
                logger.info(f"📊 처리된 테이블: {success_count}/{len(tables_to_extract)}")
                logger.info(f"📊 총 추출 레코드: {total_records}개")
                logger.info(f"📂 출력 위치: {output_path}")
                
                return success_count > 0
                
        except Exception as e:
            logger.error(f"❌ DB → YAML 추출 실패: {e}")
            return False
    
    def _extract_table_to_yaml(self, conn: sqlite3.Connection, table_name: str) -> Tuple[Optional[Dict[str, Any]], int]:
        """특정 테이블을 YAML 형태로 추출"""
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            if not rows:
                logger.warning(f"⚠️ {table_name}: 데이터가 없음")
                return {}, 0
            
            # 테이블별 특수 처리
            if table_name == 'tv_trading_variables':
                yaml_data = self._extract_trading_variables_to_yaml(rows)
            elif table_name == 'tv_variable_parameters':
                yaml_data = self._extract_variable_parameters_to_yaml(rows)
            elif table_name == 'tv_help_texts':
                yaml_data = self._extract_help_texts_to_yaml(rows)
            elif table_name == 'tv_placeholder_texts':
                yaml_data = self._extract_placeholder_texts_to_yaml(rows)
            elif table_name == 'tv_indicator_categories':
                yaml_data = self._extract_indicator_categories_to_yaml(rows)
            elif table_name == 'tv_parameter_types':
                yaml_data = self._extract_parameter_types_to_yaml(rows)
            elif table_name == 'tv_comparison_groups':
                yaml_data = self._extract_comparison_groups_to_yaml(rows)
            elif table_name == 'tv_indicator_library':
                yaml_data = self._extract_indicator_library_to_yaml(rows)
            elif table_name.startswith('cfg_'):
                yaml_data = self._extract_config_table_to_yaml(rows, table_name)
            else:
                # 일반 테이블 처리
                yaml_data = self._extract_generic_table_to_yaml(rows, table_name)
            
            return yaml_data, len(rows)
            
        except Exception as e:
            logger.error(f"❌ 테이블 추출 실패 ({table_name}): {e}")
            return None, 0
    
    def _extract_trading_variables_to_yaml(self, rows: List[sqlite3.Row]) -> Dict[str, Any]:
        """tv_trading_variables → YAML 변환"""
        trading_variables = {}
        
        for row in rows:
            variable_id = row['variable_id']
            trading_variables[variable_id] = {
                'display_name_ko': row['display_name_ko'],
                'display_name_en': row['display_name_en'],
                'description': row['description'] if 'description' in row.keys() else None,
                'purpose_category': row['purpose_category'],
                'chart_category': row['chart_category'],
                'comparison_group': row['comparison_group'],
                'is_active': bool(row['is_active']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'source': row['source'] if 'source' in row.keys() else 'built-in'
            }
        
        return {'trading_variables': trading_variables}
    
    def _extract_variable_parameters_to_yaml(self, rows: List[sqlite3.Row]) -> Dict[str, Any]:
        """tv_variable_parameters → YAML 변환"""
        variable_parameters = {}
        
        for row in rows:
            # 파라미터 키 생성 (variable_id + parameter_name)
            param_key = f"{row['variable_id']}_{row['parameter_name']}"
            
            param_data = {
                'variable_id': row['variable_id'],
                'parameter_name': row['parameter_name'],
                'parameter_type': row['parameter_type'],
                'default_value': row['default_value'],
                'min_value': row['min_value'],
                'max_value': row['max_value'],
                'is_required': bool(row['is_required']) if row['is_required'] is not None else True,
                'display_name_ko': row['display_name_ko'],
                'display_name_en': row['display_name_en'],
                'description': row['description'],
                'display_order': row['display_order']
            }
            
            # enum_values 처리 (JSON 문자열인 경우)
            if row['enum_values']:
                try:
                    if isinstance(row['enum_values'], str):
                        param_data['enum_values'] = json.loads(row['enum_values'])
                    else:
                        param_data['enum_values'] = row['enum_values']
                except:
                    param_data['enum_values'] = row['enum_values']
            else:
                param_data['enum_values'] = None
            
            variable_parameters[param_key] = param_data
        
        return {'variable_parameters': variable_parameters}
    
    def _extract_help_texts_to_yaml(self, rows: List[sqlite3.Row]) -> Dict[str, Any]:
        """tv_help_texts → YAML 변환"""
        help_texts = {}
        
        for row in rows:
            variable_id = row['variable_id']
            parameter_name = row['parameter_name']
            
            if variable_id not in help_texts:
                help_texts[variable_id] = {}
            
            help_texts[variable_id][parameter_name] = {
                'tooltip': row['tooltip'],
                'description': row['description'],
                'example': row['example'],
                'warning': row['warning'],
                'link': row['link'],
                'category': row['category'],
                'priority': row['priority'],
                'last_updated': row['last_updated']
            }
        
        return {'help_texts': help_texts}
    
    def _extract_placeholder_texts_to_yaml(self, rows: List[sqlite3.Row]) -> Dict[str, Any]:
        """tv_placeholder_texts → YAML 변환"""
        placeholder_texts = {}
        
        for row in rows:
            variable_id = row['variable_id']
            parameter_name = row['parameter_name']
            
            if variable_id not in placeholder_texts:
                placeholder_texts[variable_id] = {}
            
            placeholder_texts[variable_id][parameter_name] = {
                'placeholder': row['placeholder'],
                'example_value': row['example_value'],
                'input_format': row['input_format'],
                'validation_pattern': row['validation_pattern'],
                'error_message': row['error_message'],
                'context': row['context'],
                'priority': row['priority'],
                'last_updated': row['last_updated']
            }
        
        return {'placeholder_texts': placeholder_texts}
    
    def _extract_indicator_categories_to_yaml(self, rows: List[sqlite3.Row]) -> Dict[str, Any]:
        """tv_indicator_categories → YAML 변환"""
        indicator_categories = {}
        
        for row in rows:
            category_id = row['id']
            indicator_categories[category_id] = {
                'category_name': row['category_name'],
                'display_name_ko': row['display_name_ko'],
                'display_name_en': row['display_name_en'] if 'display_name_en' in row.keys() else None,
                'description': row['description'] if 'description' in row.keys() else None,
                'chart_position': row['chart_position'] if 'chart_position' in row.keys() else 'subplot',
                'color_scheme': row['color_scheme'] if 'color_scheme' in row.keys() else 'default',
                'color_theme': row['color_theme'] if 'color_theme' in row.keys() else None,
                'display_order': row['display_order'] if 'display_order' in row.keys() else 0,
                'is_active': bool(row['is_active']),
                'created_at': row['created_at']
            }
        
        return {'indicator_categories': indicator_categories}
    
    def _extract_parameter_types_to_yaml(self, rows: List[sqlite3.Row]) -> Dict[str, Any]:
        """tv_parameter_types → YAML 변환"""
        parameter_types = {}
        
        for row in rows:
            type_id = row['id']
            parameter_types[type_id] = {
                'type_name': row['type_name'],
                'description': row['description'],
                'validation_pattern': row['validation_pattern'],
                'default_widget': row['default_widget'],
                'is_active': bool(row['is_active'])
            }
        
        return {'parameter_types': parameter_types}
    
    def _extract_comparison_groups_to_yaml(self, rows: List[sqlite3.Row]) -> Dict[str, Any]:
        """tv_comparison_groups → YAML 변환"""
        comparison_groups = {}
        
        for row in rows:
            group_id = row['id']
            comparison_groups[group_id] = {
                'group_name': row['group_name'],
                'display_name_ko': row['display_name_ko'],
                'display_name_en': row['display_name_en'],
                'description': row['description'],
                'unit_type': row['unit_type'],
                'is_active': bool(row['is_active'])
            }
        
        return {'comparison_groups': comparison_groups}
    
    def _extract_indicator_library_to_yaml(self, rows: List[sqlite3.Row]) -> Dict[str, Any]:
        """tv_indicator_library → YAML 변환"""
        indicator_library = {}
        
        for row in rows:
            indicator_id = row['indicator_id']
            indicator_library[indicator_id] = {
                'display_name_ko': row['display_name_ko'],
                'display_name_en': row['display_name_en'],
                'category': row['category'],
                'description': row['description'],
                'calculation_method': row['calculation_method'],
                'parameters': row['parameters'],
                'usage_example': row['usage_example'],
                'is_active': bool(row['is_active'])
            }
        
        return {'indicator_library': indicator_library}
    
    def _extract_config_table_to_yaml(self, rows: List[sqlite3.Row], table_name: str) -> Dict[str, Any]:
        """cfg_ 테이블들 → YAML 변환"""
        config_data = {}
        
        for row in rows:
            if 'key' in row.keys() and 'value' in row.keys():
                # cfg_app_settings 형태
                config_data[row['key']] = {
                    'value': row['value'],
                    'description': row.get('description', ''),
                    'last_modified': row.get('last_modified', '')
                }
            elif 'setting_name' in row.keys() and 'setting_value' in row.keys():
                # cfg_system_settings 형태
                config_data[row['setting_name']] = {
                    'setting_value': row['setting_value'],
                    'description': row.get('description', '')
                }
            else:
                # 일반적인 형태
                config_data[row['id']] = dict(row)
        
        return {table_name.replace('cfg_', ''): config_data}
    
    def _extract_generic_table_to_yaml(self, rows: List[sqlite3.Row], table_name: str) -> Dict[str, Any]:
        """일반 테이블 → YAML 변환"""
        table_data = []
        
        for row in rows:
            row_data = dict(row)
            table_data.append(row_data)
        
        return {table_name: table_data}
    
    def _save_yaml_file(self, output_file: Path, data: Dict[str, Any], 
                       metadata: Optional[ExtractionMetadata] = None) -> bool:
        """YAML 파일 저장 (메타데이터 주석 포함)"""
        try:
            # 기존 파일 백업 (편집용 모드인 경우)
            if output_file.exists() and 'backup' not in output_file.name:
                backup_file = output_file.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.yaml')
                shutil.copy2(output_file, backup_file)
                logger.info(f"📦 기존 파일 백업: {backup_file.name}")
            
            # YAML 내용 생성
            yaml_content = yaml.dump(data, allow_unicode=True, indent=2, sort_keys=False)
            
            # 메타데이터 주석과 함께 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                if metadata:
                    f.write(metadata.generate_header_comment())
                f.write(yaml_content)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ YAML 파일 저장 실패 ({output_file}): {e}")
            return False
    
    def verify_extraction_integrity(self, source_db: str, yaml_files: List[str]) -> Dict[str, Any]:
        """추출 무결성 검증"""
        verification_results = {
            'source_db': source_db,
            'yaml_files': yaml_files,
            'db_record_counts': {},
            'yaml_record_counts': {},
            'integrity_status': 'unknown',
            'mismatches': []
        }
        
        try:
            # DB 레코드 수 확인
            with self.get_db_connection(source_db) as conn:
                for yaml_file in yaml_files:
                    # YAML 파일명에서 테이블명 찾기
                    table_name = None
                    for table, yaml_name in self.table_yaml_mapping.items():
                        if yaml_file.endswith(yaml_name) or yaml_name in yaml_file:
                            table_name = table
                            break
                    
                    if table_name:
                        cursor = conn.cursor()
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        db_count = cursor.fetchone()[0]
                        verification_results['db_record_counts'][table_name] = db_count
                        
                        # YAML 파일 레코드 수 확인
                        yaml_path = self.data_info_path / yaml_file
                        if yaml_path.exists():
                            try:
                                with open(yaml_path, 'r', encoding='utf-8') as f:
                                    yaml_data = yaml.safe_load(f)
                                
                                yaml_count = 0
                                if yaml_data:
                                    for key, value in yaml_data.items():
                                        if isinstance(value, dict):
                                            yaml_count = len(value)
                                        elif isinstance(value, list):
                                            yaml_count = len(value)
                                        break
                                
                                verification_results['yaml_record_counts'][yaml_file] = yaml_count
                                
                                # 불일치 확인
                                if db_count != yaml_count:
                                    verification_results['mismatches'].append({
                                        'table': table_name,
                                        'yaml_file': yaml_file,
                                        'db_count': db_count,
                                        'yaml_count': yaml_count
                                    })
                                    
                            except Exception as e:
                                logger.error(f"❌ YAML 파일 검증 실패 ({yaml_file}): {e}")
            
            # 전체 무결성 상태 결정
            if not verification_results['mismatches']:
                verification_results['integrity_status'] = 'perfect'
            elif len(verification_results['mismatches']) <= len(yaml_files) * 0.1:  # 10% 이하 불일치
                verification_results['integrity_status'] = 'acceptable'
            else:
                verification_results['integrity_status'] = 'problematic'
            
            logger.info(f"🔍 추출 무결성 검증 완료: {verification_results['integrity_status']}")
            
        except Exception as e:
            logger.error(f"❌ 무결성 검증 실패: {e}")
            verification_results['integrity_status'] = 'error'
        
        return verification_results


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="🔄 Super DB Extraction DB to YAML - DB → YAML 전용 추출 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 전체 DB → YAML 추출
  python tools/super_db_extraction_db_to_yaml.py
  python tools/super_db_extraction_db_to_yaml.py --source settings
  
  # 특정 테이블만 추출
  python tools/super_db_extraction_db_to_yaml.py --tables tv_trading_variables tv_variable_parameters
  
  # 백업용 추출 (타임스탬프 포함)
  python tools/super_db_extraction_db_to_yaml.py --backup
  python tools/super_db_extraction_db_to_yaml.py --source settings --backup --output-dir "backup_20250801"
  
  # 다른 DB 추출
  python tools/super_db_extraction_db_to_yaml.py --source market_data
  python tools/super_db_extraction_db_to_yaml.py --source strategies
        """
    )
    
    parser.add_argument('--source', default='settings',
                       choices=['settings', 'strategies', 'market_data'],
                       help='소스 DB 이름 (기본값: settings)')
    
    parser.add_argument('--tables', nargs='*',
                       help='추출할 특정 테이블 목록 (선택적)')
    
    parser.add_argument('--backup', action='store_true',
                       help='백업 모드 (타임스탬프 포함 파일명)')
    
    parser.add_argument('--output-dir',
                       help='출력 디렉토리 (기본값: data_info)')
    
    parser.add_argument('--verify', action='store_true',
                       help='추출 후 무결성 검증 실행')
    
    parser.add_argument('--list-tables', action='store_true',
                       help='추출 가능한 테이블 목록만 표시')
    
    args = parser.parse_args()
    
    extractor = SuperDBExtractionDBToYAML()
    
    try:
        if args.list_tables:
            # 테이블 목록만 표시
            tables = extractor.get_available_tables(args.source)
            print(f"\n🔍 === {args.source.upper()} DB 추출 가능한 테이블 ===")
            for i, table in enumerate(tables, 1):
                yaml_file = extractor.table_yaml_mapping.get(table, 'unknown.yaml')
                print(f"  {i:2d}. {table:<25} → {yaml_file}")
            print(f"\n📊 총 {len(tables)}개 테이블 추출 가능")
            return 0
        
        # 추출 실행
        success = extractor.extract_db_to_yaml(
            source_db=args.source,
            target_tables=args.tables,
            backup_mode=args.backup,
            output_dir=args.output_dir
        )
        
        if success:
            logger.info("🎉 Super DB → YAML 추출 성공!")
            
            # 무결성 검증 (요청 시)
            if args.verify:
                yaml_files = []
                if args.tables:
                    for table in args.tables:
                        if table in extractor.table_yaml_mapping:
                            yaml_files.append(extractor.table_yaml_mapping[table])
                else:
                    yaml_files = list(extractor.table_yaml_mapping.values())
                
                verification = extractor.verify_extraction_integrity(args.source, yaml_files)
                logger.info(f"🔍 무결성 검증 결과: {verification['integrity_status']}")
                
                if verification['mismatches']:
                    logger.warning("⚠️ 발견된 불일치:")
                    for mismatch in verification['mismatches']:
                        logger.warning(f"   • {mismatch['table']}: DB {mismatch['db_count']} vs YAML {mismatch['yaml_count']}")
            
            return 0
        else:
            logger.error("❌ Super DB → YAML 추출 실패!")
            return 1
            
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
