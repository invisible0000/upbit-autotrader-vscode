#!/usr/bin/env python3
"""
🔄 레거시 YAML 마이그레이션 도구
기존 통합 YAML 파일들을 지표별 분산 구조로 변환

작성일: 2025-08-15
목적: 200+ 지표 대응을 위한 확장 가능한 구조 구축
"""

import os
import yaml
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class IndicatorInfo:
    """지표 정보 데이터 클래스"""
    variable_id: str
    category: str
    folder_path: str
    display_name_ko: str
    display_name_en: str


class LegacyMigrator:
    """레거시 YAML 파일을 새 구조로 마이그레이션"""

    def __init__(self):
        self._logger = create_component_logger("LegacyMigrator")
        self._base_path = Path("data_info")
        self._indicators_path = self._base_path / "indicators"
        self._archived_path = self._base_path / "_archived"

        # 지표 레지스트리 로드
        self._registry = self._load_registry()

    def _load_registry(self) -> Dict[str, IndicatorInfo]:
        """지표 레지스트리 로드"""
        registry_path = self._base_path / "_management" / "indicator_registry.yaml"

        if not registry_path.exists():
            self._logger.error("지표 레지스트리가 없습니다")
            return {}

        with open(registry_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        registry = {}
        for var_id, info in data.get('indicators', {}).items():
            registry[var_id] = IndicatorInfo(
                variable_id=var_id,
                category=info['category'],
                folder_path=info['folder_path'],
                display_name_ko=info['display_name_ko'],
                display_name_en=info['display_name_en']
            )

        return registry

    def migrate_all(self):
        """전체 마이그레이션 실행"""
        self._logger.info("레거시 YAML 마이그레이션 시작")

        # 1. 기본 정의 마이그레이션 (tv_trading_variables.yaml)
        self._migrate_trading_variables()

        # 2. 매개변수 마이그레이션 (tv_variable_parameters.yaml)
        self._migrate_variable_parameters()

        # 3. 도움말 텍스트 마이그레이션 (tv_help_texts.yaml)
        self._migrate_help_texts()

        # 4. 플레이스홀더 마이그레이션 (tv_placeholder_texts.yaml)
        self._migrate_placeholder_texts()

        self._logger.info("마이그레이션 완료")

    def _migrate_trading_variables(self):
        """tv_trading_variables.yaml 마이그레이션"""
        legacy_path = self._archived_path / "tv_trading_variables.yaml"

        if not legacy_path.exists():
            self._logger.warning("tv_trading_variables.yaml 백업이 없습니다")
            return

        with open(legacy_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        variables = data.get('trading_variables', {})

        for var_id, var_data in variables.items():
            if var_id not in self._registry:
                self._logger.warning(f"레지스트리에 없는 변수: {var_id}")
                continue

            indicator_info = self._registry[var_id]
            target_folder = self._indicators_path / indicator_info.folder_path
            target_file = target_folder / "definition.yaml"

            # 폴더 생성
            target_folder.mkdir(parents=True, exist_ok=True)

            # 정의 파일 생성 (기존 파일이 없는 경우만)
            if not target_file.exists():
                definition_data = {
                    var_id: {
                        'variable_id': var_id,
                        'display_name_ko': var_data.get('display_name_ko'),
                        'display_name_en': var_data.get('display_name_en'),
                        'description': var_data.get('description'),
                        'purpose_category': var_data.get('purpose_category'),
                        'chart_category': var_data.get('chart_category'),
                        'comparison_group': var_data.get('comparison_group'),
                        'parameter_required': var_data.get('parameter_required'),
                        'is_active': var_data.get('is_active'),
                        'source': var_data.get('source'),
                        'created_at': var_data.get('created_at'),
                        'updated_at': var_data.get('updated_at')
                    }
                }

                with open(target_file, 'w', encoding='utf-8') as f:
                    yaml.dump(definition_data, f, allow_unicode=True,
                             default_flow_style=False, sort_keys=False)

                self._logger.info(f"생성: {target_file}")

    def _migrate_variable_parameters(self):
        """tv_variable_parameters.yaml 마이그레이션"""
        legacy_path = self._archived_path / "tv_variable_parameters.yaml"

        if not legacy_path.exists():
            self._logger.warning("tv_variable_parameters.yaml 백업이 없습니다")
            return

        with open(legacy_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        parameters = data.get('variable_parameters', {})

        # 변수별로 그룹화
        grouped_params = {}
        for param_key, param_data in parameters.items():
            var_id = param_data.get('variable_id')
            if var_id not in grouped_params:
                grouped_params[var_id] = {}

            param_name = param_data.get('parameter_name')
            grouped_params[var_id][param_name] = param_data

        # 각 변수별로 파일 생성
        for var_id, var_params in grouped_params.items():
            if var_id not in self._registry:
                continue

            indicator_info = self._registry[var_id]
            target_folder = self._indicators_path / indicator_info.folder_path
            target_file = target_folder / "parameters.yaml"

            # 폴더 생성
            target_folder.mkdir(parents=True, exist_ok=True)

            # 매개변수 파일 생성 (기존 파일이 없는 경우만)
            if not target_file.exists():
                parameters_data = {
                    'parameters': var_params
                }

                with open(target_file, 'w', encoding='utf-8') as f:
                    yaml.dump(parameters_data, f, allow_unicode=True,
                             default_flow_style=False, sort_keys=False)

                self._logger.info(f"생성: {target_file}")

    def _migrate_help_texts(self):
        """tv_help_texts.yaml 마이그레이션"""
        legacy_path = self._archived_path / "tv_help_texts.yaml"

        if not legacy_path.exists():
            self._logger.warning("tv_help_texts.yaml 백업이 없습니다")
            return

        with open(legacy_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        help_texts = data.get('help_texts', {})

        # 변수별로 그룹화
        grouped_helps = {}
        for help_key, help_data in help_texts.items():
            var_id = help_data.get('variable_id')
            if var_id not in grouped_helps:
                grouped_helps[var_id] = {}

            grouped_helps[var_id][help_key] = help_data

        # 각 변수별로 파일 생성
        for var_id, var_helps in grouped_helps.items():
            if var_id not in self._registry:
                continue

            indicator_info = self._registry[var_id]
            target_folder = self._indicators_path / indicator_info.folder_path
            target_file = target_folder / "help_texts.yaml"

            # 폴더 생성
            target_folder.mkdir(parents=True, exist_ok=True)

            # 도움말 파일 생성 (기존 파일이 없는 경우만)
            if not target_file.exists():
                help_data = {
                    'help_texts': var_helps
                }

                with open(target_file, 'w', encoding='utf-8') as f:
                    yaml.dump(help_data, f, allow_unicode=True,
                             default_flow_style=False, sort_keys=False)

                self._logger.info(f"생성: {target_file}")

    def _migrate_placeholder_texts(self):
        """tv_placeholder_texts.yaml 마이그레이션"""
        legacy_path = self._archived_path / "tv_placeholder_texts.yaml"

        if not legacy_path.exists():
            self._logger.warning("tv_placeholder_texts.yaml 백업이 없습니다")
            return

        with open(legacy_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        placeholders = data.get('placeholder_texts', {})

        # 변수별로 그룹화
        grouped_placeholders = {}
        for placeholder_key, placeholder_data in placeholders.items():
            var_id = placeholder_data.get('variable_id')
            if var_id not in grouped_placeholders:
                grouped_placeholders[var_id] = {}

            grouped_placeholders[var_id][placeholder_key] = placeholder_data

        # 각 변수별로 파일 생성
        for var_id, var_placeholders in grouped_placeholders.items():
            if var_id not in self._registry:
                continue

            indicator_info = self._registry[var_id]
            target_folder = self._indicators_path / indicator_info.folder_path
            target_file = target_folder / "placeholders.yaml"

            # 폴더 생성
            target_folder.mkdir(parents=True, exist_ok=True)

            # 플레이스홀더 파일 생성 (기존 파일이 없는 경우만)
            if not target_file.exists():
                placeholder_data = {
                    'placeholders': var_placeholders
                }

                with open(target_file, 'w', encoding='utf-8') as f:
                    yaml.dump(placeholder_data, f, allow_unicode=True,
                             default_flow_style=False, sort_keys=False)

                self._logger.info(f"생성: {target_file}")

    def generate_missing_indicators(self):
        """누락된 지표들의 기본 구조 생성"""
        self._logger.info("누락된 지표 구조 생성 시작")

        for var_id, indicator_info in self._registry.items():
            target_folder = self._indicators_path / indicator_info.folder_path

            # 폴더 생성
            target_folder.mkdir(parents=True, exist_ok=True)

            # 각 필수 파일들이 없으면 템플릿 생성
            required_files = ['definition.yaml', 'parameters.yaml', 'help_texts.yaml', 'placeholders.yaml']

            for filename in required_files:
                file_path = target_folder / filename
                if not file_path.exists():
                    self._create_template_file(var_id, indicator_info, file_path)

    def _create_template_file(self, var_id: str, indicator_info: IndicatorInfo, file_path: Path):
        """템플릿 파일 생성"""
        filename = file_path.name

        if filename == 'definition.yaml':
            content = {
                var_id: {
                    'variable_id': var_id,
                    'display_name_ko': indicator_info.display_name_ko,
                    'display_name_en': indicator_info.display_name_en,
                    'description': f"{indicator_info.display_name_ko} 지표",
                    'purpose_category': indicator_info.category,
                    'chart_category': 'subplot',
                    'comparison_group': 'percentage_comparable',
                    'parameter_required': True,
                    'is_active': True,
                    'source': 'built-in',
                    'created_at': '2025-08-15 22:45:00',
                    'updated_at': '2025-08-15 22:45:00'
                }
            }
        elif filename == 'parameters.yaml':
            content = {
                'parameters': {
                    'period': {
                        'parameter_name': 'period',
                        'parameter_type': 'integer',
                        'default_value': '14',
                        'is_required': True,
                        'display_name_ko': '기간',
                        'display_name_en': 'Period',
                        'description': '계산 기간',
                        'display_order': 1
                    }
                }
            }
        elif filename == 'help_texts.yaml':
            content = {
                'help_texts': {
                    f'{var_id}_period': {
                        'variable_id': var_id,
                        'parameter_name': 'period',
                        'help_text_ko': f'{indicator_info.display_name_ko} 계산 기간',
                        'help_text_en': f'{indicator_info.display_name_en} calculation period',
                        'tooltip_ko': '일반적으로 14일 사용',
                        'tooltip_en': 'Typically uses 14 days'
                    }
                }
            }
        else:  # placeholders.yaml
            content = {
                'placeholders': {
                    f'{var_id}_period': {
                        'variable_id': var_id,
                        'parameter_name': 'period',
                        'placeholder_text_ko': '예: 14',
                        'placeholder_text_en': 'e.g., 14'
                    }
                }
            }

        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(content, f, allow_unicode=True,
                     default_flow_style=False, sort_keys=False)

        self._logger.info(f"템플릿 생성: {file_path}")

    def validate_structure(self):
        """새 구조 검증"""
        self._logger.info("구조 검증 시작")

        for var_id, indicator_info in self._registry.items():
            target_folder = self._indicators_path / indicator_info.folder_path

            if not target_folder.exists():
                self._logger.error(f"폴더 없음: {target_folder}")
                continue

            required_files = ['definition.yaml', 'parameters.yaml', 'help_texts.yaml', 'placeholders.yaml']
            missing_files = []

            for filename in required_files:
                if not (target_folder / filename).exists():
                    missing_files.append(filename)

            if missing_files:
                self._logger.warning(f"{var_id}: 누락 파일 {missing_files}")
            else:
                self._logger.info(f"{var_id}: 완전 ✅")


def main():
    """메인 실행"""
    print("🔄 레거시 YAML 마이그레이션 도구")
    print()

    migrator = LegacyMigrator()

    # 1. 기존 데이터 마이그레이션
    print("📋 1단계: 기존 데이터 마이그레이션")
    migrator.migrate_all()

    # 2. 누락 지표 템플릿 생성
    print("\n🏗️ 2단계: 누락 지표 템플릿 생성")
    migrator.generate_missing_indicators()

    # 3. 구조 검증
    print("\n✅ 3단계: 구조 검증")
    migrator.validate_structure()

    print("\n🎉 마이그레이션 완료!")
    print("💡 다음 단계: python data_info/_management/merge_indicators_to_db.py")


if __name__ == "__main__":
    main()
