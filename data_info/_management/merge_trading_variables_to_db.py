#!/usr/bin/env python3
"""
헬프 카테고리 일괄 수정 및 거래 변수 통합 스크립트

주요 기능:
1. 헬프 카테고리 정규화 (concept, usage, advanced로 통일)
2. 거래 변수별 분산된 YAML 파일들을 데이터베이스로 통합
3. 기존 잘못된 카테고리 데이터 정리

사용법:
    python data_info/_management/merge_trading_variables_to_db.py --fix-help-categories
    python data_info/_management/merge_trading_variables_to_db.py --dry-run --fix-help-categories
    python data_info/_management/merge_trading_variables_to_db.py --variable SMA
"""

import argparse
import sqlite3
import yaml
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class TradingVariableDatabaseMerger:
    """거래 변수 YAML 파일들을 데이터베이스에 통합하는 클래스"""

    def __init__(self, db_path: str = "data/settings.sqlite3"):
        self.db_path = db_path
        self.trading_variables_path = Path("data_info/trading_variables")
        self.registry_path = Path("data_info/_management/trading_variables_registry.yaml")

    def load_registry(self) -> Dict[str, Any]:
        """지표 레지스트리 로드"""
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_trading_variable_categories(self) -> List[str]:
        """거래 변수 카테고리 목록 반환"""
        return [d.name for d in self.trading_variables_path.iterdir() if d.is_dir()]

    def get_trading_variables_in_category(self, category: str) -> List[str]:
        """특정 카테고리의 거래 변수들 반환"""
        category_path = self.trading_variables_path / category
        if not category_path.exists():
            return []
        return [d.name for d in category_path.iterdir() if d.is_dir()]

    def load_trading_variable_files(self, category: str, variable: str) -> Dict[str, Any]:
        """거래 변수의 모든 YAML 파일들 로드"""
        variable_path = self.trading_variables_path / category / variable

        files = {
            'definition': 'definition.yaml',
            'parameters': 'parameters.yaml',
            'help_texts': 'help_texts.yaml',
            'placeholders': 'placeholders.yaml',
            'help_guide': 'help_guide.yaml'
        }

        data = {}
        for key, filename in files.items():
            file_path = variable_path / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data[key] = yaml.safe_load(f)
            else:
                print(f"⚠️  {filename} 파일이 없습니다: {file_path}")
                data[key] = None

        return data

    def merge_trading_variables(self, conn: sqlite3.Connection, data: Dict[str, Any],
                              category: str, variable: str, dry_run: bool = False):
        """tv_trading_variables 테이블에 데이터 병합"""
        definition = data.get('definition')
        if not definition:
            return

        variable_id = definition.get('variable_id', variable.upper())

        # 기존 데이터 확인
        cursor = conn.execute(
            "SELECT COUNT(*) FROM tv_trading_variables WHERE variable_id = ?",
            (variable_id,)
        )
        exists = cursor.fetchone()[0] > 0

        insert_data = {
            'variable_id': variable_id,
            'display_name_ko': definition.get('display_name_ko', ''),
            'display_name_en': definition.get('display_name_en', ''),
            'description': definition.get('description', ''),
            'purpose_category': definition.get('purpose_category', ''),
            'chart_category': definition.get('chart_category', ''),
            'comparison_group': definition.get('comparison_group', ''),
            'is_active': definition.get('is_active', True),
            'parameter_required': definition.get('parameter_required', False),
            'source': 'distributed_yaml',
            'updated_at': datetime.now().isoformat()
        }

        if dry_run:
            action = "UPDATE" if exists else "INSERT"
            print(f"  [DRY-RUN] tv_trading_variables {action}: {variable_id}")
            return

        if exists:
            # 업데이트
            set_clause = ", ".join([f"{k} = ?" for k in insert_data.keys() if k != 'variable_id'])
            values = [v for k, v in insert_data.items() if k != 'variable_id'] + [variable_id]
            conn.execute(
                f"UPDATE tv_trading_variables SET {set_clause} WHERE variable_id = ?",
                values
            )
            print(f"  ✅ tv_trading_variables 업데이트: {variable_id}")
        else:
            # 삽입
            columns = ", ".join(insert_data.keys())
            placeholders = ", ".join(["?" for _ in insert_data])
            conn.execute(
                f"INSERT INTO tv_trading_variables ({columns}) VALUES ({placeholders})",
                list(insert_data.values())
            )
            print(f"  ✅ tv_trading_variables 삽입: {variable_id}")

    def merge_variable_parameters(self, conn: sqlite3.Connection, data: Dict[str, Any],
                                  category: str, variable: str, dry_run: bool = False):
        """tv_variable_parameters 테이블에 데이터 병합"""
        definition = data.get('definition')
        parameters = data.get('parameters')
        if not definition or not parameters:
            return

        variable_id = definition.get('variable_id', variable.upper())

        # 기존 파라미터들 삭제 (교체 방식)
        if not dry_run:
            conn.execute(
                "DELETE FROM tv_variable_parameters WHERE variable_id = ?",
                (variable_id,)
            )

        params_list = parameters.get('parameters', [])
        for param in params_list:
            insert_data = {
                'variable_id': variable_id,
                'parameter_name': param.get('name', ''),
                'parameter_type': param.get('type', 'integer'),
                'default_value': str(param.get('default_value', '')),
                'min_value': str(param.get('min_value', '')) if param.get('min_value') is not None else None,
                'max_value': str(param.get('max_value', '')) if param.get('max_value') is not None else None,
                'enum_values': str(param.get('enum_values', '')) if param.get('enum_values') else None,
                'is_required': param.get('required', True),
                'display_name_ko': param.get('display_name', ''),
                'display_name_en': param.get('display_name', ''),
                'description': param.get('description', ''),
                'display_order': param.get('display_order', 0),
                'created_at': datetime.now().isoformat()
            }

            if dry_run:
                print(f"  [DRY-RUN] tv_variable_parameters INSERT: {variable_id}.{param.get('name', '')}")
            else:
                columns = ", ".join(insert_data.keys())
                placeholders = ", ".join(["?" for _ in insert_data])
                conn.execute(
                    f"INSERT INTO tv_variable_parameters ({columns}) VALUES ({placeholders})",
                    list(insert_data.values())
                )
                print(f"  ✅ tv_variable_parameters 삽입: {variable_id}.{param.get('name', '')}")

    def merge_help_documents(self, conn: sqlite3.Connection, data: Dict[str, Any],
                             category: str, variable: str, dry_run: bool = False):
        """tv_variable_help_documents 테이블에 데이터 병합"""
        definition = data.get('definition')
        help_texts = data.get('help_texts')
        help_guide = data.get('help_guide')
        placeholders = data.get('placeholders')

        if not definition:
            return

        variable_id = definition.get('variable_id', variable.upper())

        # 기존 도움말 문서들 삭제 (교체 방식)
        if not dry_run:
            conn.execute(
                "DELETE FROM tv_variable_help_documents WHERE variable_id = ?",
                (variable_id,)
            )

        # help_texts 처리
        if help_texts and help_texts.get('help_texts'):
            for text_item in help_texts['help_texts']:
                self._insert_help_document(
                    conn, variable_id, 'concept', text_item, dry_run
                )

        # help_guide 처리
        if help_guide and help_guide.get('guides'):
            for guide_item in help_guide['guides']:
                self._insert_help_document(
                    conn, variable_id, 'advanced', guide_item, dry_run
                )

        # placeholders 처리
        if placeholders and placeholders.get('placeholders'):
            for placeholder_item in placeholders['placeholders']:
                self._insert_help_document(
                    conn, variable_id, 'placeholder', placeholder_item, dry_run
                )

    def _insert_help_document(self, conn: sqlite3.Connection, variable_id: str,
                              help_category: str, item: Dict[str, Any], dry_run: bool = False):
        """개별 도움말 문서 삽입"""
        insert_data = {
            'variable_id': variable_id,
            'help_category': help_category,
            'content_type': 'markdown',
            'title_ko': item.get('title', ''),
            'title_en': item.get('title_en', ''),
            'content_ko': item.get('content', ''),
            'content_en': item.get('content_en', ''),
            'display_order': item.get('priority', 5),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        if dry_run:
            print(f"  [DRY-RUN] tv_variable_help_documents INSERT: {variable_id} ({help_category})")
        else:
            columns = ", ".join(insert_data.keys())
            placeholders = ", ".join(["?" for _ in insert_data])
            conn.execute(
                f"INSERT INTO tv_variable_help_documents ({columns}) VALUES ({placeholders})",
                list(insert_data.values())
            )
            print(f"  ✅ tv_variable_help_documents 삽입: {variable_id} ({help_category})")

    def merge_single_variable(self, category: str, variable: str, dry_run: bool = False):
        """단일 변수를 데이터베이스에 병합"""
        print(f"\n📊 변수 병합 시작: {category}/{variable}")

        # 변수 파일들 로드
        data = self.load_trading_variable_files(category, variable)

        # 필수 파일 확인
        if not data.get('definition'):
            print(f"❌ definition.yaml이 없어서 건너뜀: {category}/{variable}")
            return False

        # 데이터베이스 연결
        with sqlite3.connect(self.db_path) as conn:
            # 각 테이블에 데이터 병합
            self.merge_trading_variables(conn, data, category, variable, dry_run)
            self.merge_variable_parameters(conn, data, category, variable, dry_run)
            self.merge_help_documents(conn, data, category, variable, dry_run)

            if not dry_run:
                conn.commit()

        print(f"✅ 변수 병합 완료: {category}/{variable}")
        return True

    def merge_all_variables(self, dry_run: bool = False):
        """모든 변수들을 데이터베이스에 병합"""
        print("🔄 모든 변수 병합 시작...")
        if dry_run:
            print("🔍 DRY-RUN 모드 (실제 데이터베이스 변경 없음)")

        total_count = 0
        success_count = 0

        categories = self.get_trading_variable_categories()
        for category in categories:
            variables = self.get_trading_variables_in_category(category)
            for variable in variables:
                total_count += 1
                if self.merge_single_variable(category, variable, dry_run):
                    success_count += 1

        print(f"\n📈 병합 완료: {success_count}/{total_count} 변수 처리됨")
        if not dry_run:
            print(f"💾 데이터베이스 업데이트: {self.db_path}")


def main():
    parser = argparse.ArgumentParser(description="거래 변수 YAML 파일들을 데이터베이스에 병합")
    parser.add_argument("--dry-run", action="store_true", help="실제 변경 없이 시뮬레이션만 실행")
    parser.add_argument("--variable", help="특정 변수만 병합 (예: trailing_stop)")
    parser.add_argument("--category", help="특정 카테고리의 변수들만 병합 (예: meta)")
    args = parser.parse_args()

    merger = TradingVariableDatabaseMerger()

    if args.variable:
        # 특정 변수만 병합
        found = False
        for category in merger.get_trading_variable_categories():
            if args.variable.lower() in [var.lower() for var in merger.get_trading_variables_in_category(category)]:
                # 정확한 이름 찾기
                variables = merger.get_trading_variables_in_category(category)
                for variable in variables:
                    if variable.lower() == args.variable.lower():
                        merger.merge_single_variable(category, variable, args.dry_run)
                        found = True
                        break
                break

        if not found:
            print(f"❌ 변수를 찾을 수 없습니다: {args.variable}")

    elif args.category:
        # 특정 카테고리만 병합
        if args.category in merger.get_trading_variable_categories():
            variables = merger.get_trading_variables_in_category(args.category)
            for variable in variables:
                merger.merge_single_variable(args.category, variable, args.dry_run)
        else:
            print(f"❌ 카테고리를 찾을 수 없습니다: {args.category}")

    else:
        # 모든 변수 병합
        merger.merge_all_variables(args.dry_run)


if __name__ == "__main__":
    main()
