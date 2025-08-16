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
import json
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

        variable_name = definition.get('variable_name', indicator.upper())

        # 기존 데이터 확인
        cursor = conn.execute(
            "SELECT COUNT(*) FROM tv_trading_variables WHERE variable_name = ?",
            (variable_name,)
        )
        exists = cursor.fetchone()[0] > 0

        insert_data = {
            'variable_name': variable_name,
            'display_name': definition.get('display_name', ''),
            'description': definition.get('description', ''),
            'category': category,
            'purpose_category': definition.get('purpose_category', ''),
            'chart_category': definition.get('chart_category', ''),
            'comparison_group': definition.get('comparison_group', ''),
            'ui_component_type': definition.get('ui_component_type', ''),
            'is_customizable': definition.get('is_customizable', True),
            'is_active': definition.get('is_active', True),
            'sort_order': definition.get('sort_order', 999),
            'tooltip': definition.get('tooltip', ''),
            'source_type': 'distributed_yaml',
            'last_updated': datetime.now().isoformat()
        }

        if dry_run:
            action = "UPDATE" if exists else "INSERT"
            print(f"  [DRY-RUN] tv_trading_variables {action}: {variable_name}")
            return

        if exists:
            # 업데이트
            set_clause = ", ".join([f"{k} = ?" for k in insert_data.keys() if k != 'variable_name'])
            values = [v for k, v in insert_data.items() if k != 'variable_name'] + [variable_name]
            conn.execute(
                f"UPDATE tv_trading_variables SET {set_clause} WHERE variable_name = ?",
                values
            )
            print(f"  ✅ tv_trading_variables 업데이트: {variable_name}")
        else:
            # 삽입
            columns = ", ".join(insert_data.keys())
            placeholders = ", ".join(["?" for _ in insert_data])
            conn.execute(
                f"INSERT INTO tv_trading_variables ({columns}) VALUES ({placeholders})",
                list(insert_data.values())
            )
            print(f"  ✅ tv_trading_variables 삽입: {variable_name}")

    def merge_variable_parameters(self, conn: sqlite3.Connection, data: Dict[str, Any],
                                  category: str, indicator: str, dry_run: bool = False):
        """tv_variable_parameters 테이블에 데이터 병합"""
        definition = data.get('definition')
        parameters = data.get('parameters')
        if not definition or not parameters:
            return

        variable_name = definition.get('variable_name', indicator.upper())

        # 기존 파라미터들 삭제 (교체 방식)
        if not dry_run:
            conn.execute(
                "DELETE FROM tv_variable_parameters WHERE variable_name = ?",
                (variable_name,)
            )

        params_list = parameters.get('parameters', [])
        for param in params_list:
            insert_data = {
                'variable_name': variable_name,
                'parameter_name': param.get('name', ''),
                'display_name': param.get('display_name', ''),
                'parameter_type': param.get('type', 'int'),
                'default_value': param.get('default_value'),
                'min_value': param.get('min_value'),
                'max_value': param.get('max_value'),
                'step_value': param.get('step_value'),
                'description': param.get('description', ''),
                'tooltip': param.get('tooltip', ''),
                'is_required': param.get('required', True),
                'validation_rule': json.dumps(param.get('validation', {})) if param.get('validation') else None,
                'ui_hint': param.get('ui_hint', ''),
                'sort_order': param.get('sort_order', 999),
                'last_updated': datetime.now().isoformat()
            }

            if dry_run:
                print(f"  [DRY-RUN] tv_variable_parameters INSERT: {variable_name}.{param.get('name', '')}")
            else:
                columns = ", ".join(insert_data.keys())
                placeholders = ", ".join(["?" for _ in insert_data])
                conn.execute(
                    f"INSERT INTO tv_variable_parameters ({columns}) VALUES ({placeholders})",
                    list(insert_data.values())
                )
                print(f"  ✅ tv_variable_parameters 삽입: {variable_name}.{param.get('name', '')}")

    def merge_help_documents(self, conn: sqlite3.Connection, data: Dict[str, Any],
                             category: str, indicator: str, dry_run: bool = False):
        """tv_variable_help_documents 테이블에 데이터 병합"""
        definition = data.get('definition')
        help_texts = data.get('help_texts')
        help_guide = data.get('help_guide')
        placeholders = data.get('placeholders')

        if not definition:
            return

        variable_name = definition.get('variable_name', indicator.upper())

        # 기존 도움말 문서들 삭제 (교체 방식)
        if not dry_run:
            conn.execute(
                "DELETE FROM tv_variable_help_documents WHERE variable_name = ?",
                (variable_name,)
            )

        # help_texts 처리
        if help_texts and help_texts.get('help_texts'):
            for text_item in help_texts['help_texts']:
                self._insert_help_document(
                    conn, variable_name, 'text', text_item, dry_run
                )

        # help_guide 처리
        if help_guide and help_guide.get('guides'):
            for guide_item in help_guide['guides']:
                self._insert_help_document(
                    conn, variable_name, 'guide', guide_item, dry_run
                )

        # placeholders 처리
        if placeholders and placeholders.get('placeholders'):
            for placeholder_item in placeholders['placeholders']:
                self._insert_help_document(
                    conn, variable_name, 'placeholder', placeholder_item, dry_run
                )

    def _insert_help_document(self, conn: sqlite3.Connection, variable_name: str,
                              doc_type: str, item: Dict[str, Any], dry_run: bool = False):
        """개별 도움말 문서 삽입"""
        insert_data = {
            'variable_name': variable_name,
            'document_type': doc_type,
            'title': item.get('title', ''),
            'content': item.get('content', ''),
            'target_audience': item.get('target_audience', 'general'),
            'priority': item.get('priority', 5),
            'context_tags': json.dumps(item.get('tags', [])) if item.get('tags') else None,
            'last_updated': datetime.now().isoformat()
        }

        if dry_run:
            print(f"  [DRY-RUN] tv_variable_help_documents INSERT: {variable_name} ({doc_type})")
        else:
            columns = ", ".join(insert_data.keys())
            placeholders = ", ".join(["?" for _ in insert_data])
            conn.execute(
                f"INSERT INTO tv_variable_help_documents ({columns}) VALUES ({placeholders})",
                list(insert_data.values())
            )
            print(f"  ✅ tv_variable_help_documents 삽입: {variable_name} ({doc_type})")

    def merge_single_indicator(self, category: str, indicator: str, dry_run: bool = False):
        """단일 지표를 데이터베이스에 병합"""
        print(f"\n📊 지표 병합 시작: {category}/{indicator}")

        # 지표 파일들 로드
        data = self.load_indicator_files(category, indicator)

        # 필수 파일 확인
        if not data.get('definition'):
            print(f"❌ definition.yaml이 없어서 건너뜀: {category}/{indicator}")
            return False

        # 데이터베이스 연결
        with sqlite3.connect(self.db_path) as conn:
            # 각 테이블에 데이터 병합
            self.merge_trading_variables(conn, data, category, indicator, dry_run)
            self.merge_variable_parameters(conn, data, category, indicator, dry_run)
            self.merge_help_documents(conn, data, category, indicator, dry_run)

            if not dry_run:
                conn.commit()

        print(f"✅ 지표 병합 완료: {category}/{indicator}")
        return True

    def merge_all_indicators(self, dry_run: bool = False):
        """모든 지표들을 데이터베이스에 병합"""
        print("🔄 모든 지표 병합 시작...")
        if dry_run:
            print("🔍 DRY-RUN 모드 (실제 데이터베이스 변경 없음)")

        total_count = 0
        success_count = 0

        categories = self.get_indicator_categories()
        for category in categories:
            indicators = self.get_indicators_in_category(category)
            for indicator in indicators:
                total_count += 1
                if self.merge_single_indicator(category, indicator, dry_run):
                    success_count += 1

        print(f"\n📈 병합 완료: {success_count}/{total_count} 지표 처리됨")
        if not dry_run:
            print(f"💾 데이터베이스 업데이트: {self.db_path}")


def main():
    parser = argparse.ArgumentParser(description="지표 YAML 파일들을 데이터베이스에 병합")
    parser.add_argument("--dry-run", action="store_true", help="실제 변경 없이 시뮬레이션만 실행")
    parser.add_argument("--indicator", help="특정 지표만 병합 (예: SMA)")
    parser.add_argument("--category", help="특정 카테고리의 지표들만 병합 (예: trend)")
    args = parser.parse_args()

    merger = IndicatorDatabaseMerger()

    if args.indicator:
        # 특정 지표만 병합
        found = False
        for category in merger.get_indicator_categories():
            if args.indicator.lower() in [ind.lower() for ind in merger.get_indicators_in_category(category)]:
                # 정확한 이름 찾기
                indicators = merger.get_indicators_in_category(category)
                for indicator in indicators:
                    if indicator.lower() == args.indicator.lower():
                        merger.merge_single_indicator(category, indicator, args.dry_run)
                        found = True
                        break
                break

        if not found:
            print(f"❌ 지표를 찾을 수 없습니다: {args.indicator}")

    elif args.category:
        # 특정 카테고리만 병합
        if args.category in merger.get_indicator_categories():
            indicators = merger.get_indicators_in_category(args.category)
            for indicator in indicators:
                merger.merge_single_indicator(args.category, indicator, args.dry_run)
        else:
            print(f"❌ 카테고리를 찾을 수 없습니다: {args.category}")

    else:
        # 모든 지표 병합
        merger.merge_all_indicators(args.dry_run)


if __name__ == "__main__":
    main()
