#!/usr/bin/env python3
"""
DB to YAML TV Tables Generator
DB의 TV 관련 테이블들을 표준 폴더 구조로 YAML 파일 생성

이 도구는 DB를 Single Source of Truth로 하여 관리 가능한 YAML 파일들을 생성합니다.
각 변수별로 적절한 카테고리 폴더와 변수 폴더를 생성하고,
모든 TV 테이블의 데이터를 YAML 파일로 추출합니다.

폴더 구조:
data_info/trading_variables_from_db/
├── trend/
│   ├── sma/
│   │   ├── tv_trading_variables.yaml
│   │   ├── tv_variable_parameters.yaml
│   │   ├── tv_variable_help_documents.yaml
│   │   ├── tv_help_texts.yaml
│   │   └── tv_placeholder_texts.yaml
│   └── ...
├── momentum/
├── volatility/
├── volume/
├── price/
├── state/
└── meta/

Usage:
    python db_to_yaml_tv_tables.py [--output-folder folder_name]

Example:
    python db_to_yaml_tv_tables.py
    python db_to_yaml_tv_tables.py --output-folder trading_variables_clean
"""

import sqlite3
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "settings.sqlite3"

# TV 관련 테이블 목록
TV_TABLES = [
    'tv_trading_variables',
    'tv_variable_parameters',
    'tv_variable_help_documents',
    'tv_help_texts',
    'tv_placeholder_texts'
]

# 카테고리 매핑 (variable_id 패턴으로 추정)
CATEGORY_MAPPING = {
    'SMA': 'trend',
    'EMA': 'trend',
    'BOLLINGER_BAND': 'volatility',
    'RSI': 'momentum',
    'STOCHASTIC': 'momentum',
    'ATR': 'volatility',
    'VOLUME': 'volume',
    'VOLUME_SMA': 'volume',
    'VOLUME_SPIKE': 'volume',
    'OPEN_PRICE': 'price',
    'HIGH_PRICE': 'price',
    'LOW_PRICE': 'price',
    'CLOSE_PRICE': 'price',
    'CURRENT_PRICE': 'price',
    'PROFIT_PERCENT': 'state',
    'PROFIT_AMOUNT': 'state',
    'POSITION_SIZE': 'state',
    'AVG_BUY_PRICE': 'state',
    'CASH_BALANCE': 'state',
    'COIN_BALANCE': 'state',
    'TOTAL_BALANCE': 'state',
    'META_PYRAMID_TARGET': 'meta',
    'META_TRAILING_STOP': 'meta',
    'MACD': 'momentum',
    'PRICE_BREAKOUT': 'momentum',
    'RSI_CHANGE': 'momentum',
}


def get_variable_category(variable_id: str) -> str:
    """변수 ID로부터 카테고리를 추정합니다."""
    for pattern, category in CATEGORY_MAPPING.items():
        if pattern in variable_id.upper():
            return category
    return 'unknown'


def get_all_variable_ids() -> List[str]:
    """모든 변수 ID 목록을 반환합니다."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT variable_id FROM tv_trading_variables ORDER BY variable_id")
        variable_ids = [row[0] for row in cursor.fetchall()]

        conn.close()
        return variable_ids

    except Exception as e:
        print(f"❌ Error getting variable IDs: {e}")
        return []


def fetch_table_data_for_variable(table_name: str, variable_id: str) -> List[Dict[str, Any]]:
    """특정 변수의 테이블 데이터를 가져옵니다."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if table_name == 'tv_trading_variables':
            # tv_trading_variables는 variable_id로 직접 필터
            cursor.execute(f"SELECT * FROM {table_name} WHERE variable_id = ? ORDER BY variable_id", (variable_id,))
        elif 'variable_id' in get_table_columns(table_name):
            # variable_id 컬럼이 있는 테이블들
            if table_name == 'tv_variable_parameters':
                cursor.execute(f"SELECT * FROM {table_name} WHERE variable_id = ? ORDER BY parameter_name", (variable_id,))
            else:
                cursor.execute(f"SELECT * FROM {table_name} WHERE variable_id = ? ORDER BY id", (variable_id,))
        else:
            # variable_id가 없는 테이블은 스킵
            return []

        rows = cursor.fetchall()
        data = [dict(row) for row in rows]

        conn.close()
        return data

    except Exception as e:
        print(f"❌ Error fetching {table_name} for {variable_id}: {e}")
        return []


def get_table_columns(table_name: str) -> List[str]:
    """테이블의 컬럼 목록을 반환합니다."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]

        conn.close()
        return columns

    except Exception as e:
        print(f"❌ Error getting columns for {table_name}: {e}")
        return []


def create_variable_folder(output_base: Path, variable_id: str) -> Path:
    """변수 ID에 맞는 폴더 구조를 생성합니다."""
    category = get_variable_category(variable_id)
    variable_folder = output_base / category / variable_id
    variable_folder.mkdir(parents=True, exist_ok=True)
    return variable_folder


def process_tv_trading_variables_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """tv_trading_variables 데이터를 YAML 구조로 변환합니다."""
    if not data:
        return {}

    # 단일 행이므로 첫 번째 행만 사용
    row = data[0]
    variable_id = row['variable_id']

    # 불필요한 메타데이터 제거
    clean_data = {k: v for k, v in row.items()
                  if k not in ['id', 'created_at', 'updated_at'] and v is not None}

    return {variable_id: clean_data}


def process_tv_variable_parameters_data(data: List[Dict[str, Any]], variable_id: str) -> Dict[str, Any]:
    """tv_variable_parameters 데이터를 YAML 구조로 변환합니다."""
    if not data:
        return {variable_id: []}

    # 파라미터별로 정리
    parameters = []
    for row in data:
        clean_param = {k: v for k, v in row.items()
                       if k not in ['id', 'created_at', 'updated_at'] and v is not None}
        parameters.append(clean_param)

    return {variable_id: parameters}


def process_tv_variable_help_documents_data(data: List[Dict[str, Any]], variable_id: str) -> Dict[str, Any]:
    """tv_variable_help_documents 데이터를 YAML 구조로 변환합니다."""
    if not data:
        return {variable_id: {}}

    # help_category별로 정리
    help_docs = {}
    for row in data:
        help_category = row.get('help_category', 'unknown')
        content_ko = row.get('content_ko', '')
        title_ko = row.get('title_ko', '')

        help_docs[help_category] = {
            'title': title_ko,
            'content': content_ko
        }

    return {variable_id: help_docs}


def process_tv_help_texts_data(data: List[Dict[str, Any]], variable_id: str) -> Dict[str, Any]:
    """tv_help_texts 데이터를 YAML 구조로 변환합니다."""
    if not data:
        return {variable_id: {}}

    # parameter_name별로 정리
    help_texts = {}
    for row in data:
        parameter_name = row.get('parameter_name', 'unknown')
        help_text_ko = row.get('help_text_ko', '')

        help_texts[parameter_name] = help_text_ko

    return {variable_id: help_texts}


def process_tv_placeholder_texts_data(data: List[Dict[str, Any]], variable_id: str) -> Dict[str, Any]:
    """tv_placeholder_texts 데이터를 YAML 구조로 변환합니다."""
    if not data:
        return {variable_id: {}}

    # parameter_name별로 정리
    placeholder_texts = {}
    for row in data:
        parameter_name = row.get('parameter_name', 'unknown')
        placeholder_text_ko = row.get('placeholder_text_ko', '')

        placeholder_texts[parameter_name] = placeholder_text_ko

    return {variable_id: placeholder_texts}


def save_yaml_file(data: Dict[str, Any], file_path: Path) -> bool:
    """YAML 파일을 저장합니다."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False,
                      allow_unicode=True, sort_keys=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Error saving {file_path}: {e}")
        return False


def generate_yaml_files_for_variable(variable_id: str, output_base: Path) -> bool:
    """특정 변수에 대한 모든 YAML 파일을 생성합니다."""
    print(f"🔄 Processing {variable_id}...")

    # 변수 폴더 생성
    variable_folder = create_variable_folder(output_base, variable_id)

    success_count = 0

    for table_name in TV_TABLES:
        # 테이블 데이터 가져오기
        data = fetch_table_data_for_variable(table_name, variable_id)

        if not data:
            print(f"  ⚠️  No data in {table_name} for {variable_id}")
            continue

        # 테이블별 데이터 처리
        if table_name == 'tv_trading_variables':
            yaml_data = process_tv_trading_variables_data(data)
        elif table_name == 'tv_variable_parameters':
            yaml_data = process_tv_variable_parameters_data(data, variable_id)
        elif table_name == 'tv_variable_help_documents':
            yaml_data = process_tv_variable_help_documents_data(data, variable_id)
        elif table_name == 'tv_help_texts':
            yaml_data = process_tv_help_texts_data(data, variable_id)
        elif table_name == 'tv_placeholder_texts':
            yaml_data = process_tv_placeholder_texts_data(data, variable_id)
        else:
            yaml_data = {variable_id: data}

        # YAML 파일 저장
        yaml_file = variable_folder / f"{table_name}.yaml"
        if save_yaml_file(yaml_data, yaml_file):
            print(f"  ✅ Created {table_name}.yaml")
            success_count += 1
        else:
            print(f"  ❌ Failed to create {table_name}.yaml")

    return success_count > 0


def generate_summary_file(output_base: Path, variable_ids: List[str]) -> None:
    """생성 요약 파일을 만듭니다."""
    summary = {
        'generation_info': {
            'generated_at': datetime.now().isoformat(),
            'total_variables': len(variable_ids),
            'source_database': str(DB_PATH),
            'tables_processed': TV_TABLES
        },
        'variables_by_category': {}
    }

    # 카테고리별 변수 분류
    for variable_id in variable_ids:
        category = get_variable_category(variable_id)
        if category not in summary['variables_by_category']:
            summary['variables_by_category'][category] = []
        summary['variables_by_category'][category].append(variable_id)

    summary_file = output_base / 'generation_summary.yaml'
    save_yaml_file(summary, summary_file)
    print(f"📄 Generated summary file: {summary_file}")


def main():
    # 명령행 인수 처리
    output_folder = "trading_variables_from_db"
    if '--output-folder' in sys.argv:
        idx = sys.argv.index('--output-folder')
        if idx + 1 < len(sys.argv):
            output_folder = sys.argv[idx + 1]

    output_base = Path(output_folder)

    print("🏗️  DB to YAML TV Tables Generator")
    print("=" * 60)
    print(f"📁 Output folder: {output_base}")
    print(f"🗄️  Source database: {DB_PATH}")
    print(f"📊 Tables to process: {', '.join(TV_TABLES)}")

    # 모든 변수 ID 가져오기
    print("\n🔍 Getting all variable IDs...")
    variable_ids = get_all_variable_ids()

    if not variable_ids:
        print("❌ No variables found in database!")
        sys.exit(1)

    print(f"📊 Found {len(variable_ids)} variables: {', '.join(variable_ids[:5])}{'...' if len(variable_ids) > 5 else ''}")

    # 사용자 확인
    response = input(f"\nGenerate YAML files for {len(variable_ids)} variables? (y/N): ")
    if response.lower() != 'y':
        print("❌ Operation cancelled by user")
        sys.exit(0)

    # 출력 폴더 정리
    if output_base.exists():
        print("🗑️  Cleaning existing output folder...")
        import shutil
        shutil.rmtree(output_base)

    output_base.mkdir(parents=True, exist_ok=True)

    # 각 변수별로 YAML 파일 생성
    print("\n🔄 Generating YAML files...")
    success_count = 0

    for variable_id in variable_ids:
        if generate_yaml_files_for_variable(variable_id, output_base):
            success_count += 1

    # 요약 파일 생성
    generate_summary_file(output_base, variable_ids)

    print("\n🎉 Generation completed!")
    print(f"✅ Successfully processed: {success_count}/{len(variable_ids)} variables")
    print(f"📁 Output location: {output_base.absolute()}")
    print("💡 Review the generated files and replace the existing trading_variables folder when ready")


if __name__ == "__main__":
    main()
