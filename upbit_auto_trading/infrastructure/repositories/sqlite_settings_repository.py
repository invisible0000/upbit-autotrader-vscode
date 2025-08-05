#!/usr/bin/env python3
"""
SQLite 기반 설정 Repository 구현 (읽기 전용)
=============================================

settings.sqlite3 데이터베이스를 위한 읽기 전용 Repository 구현입니다.
매매 변수 정의, 파라미터, 호환성 규칙 등에 대한 Domain Repository 인터페이스를 구현합니다.

Features:
- 읽기 전용: settings.sqlite3의 불변성 보장
- 캐싱 지원: 자주 조회되는 데이터의 성능 최적화
- DDD 매핑: Domain Entity/Value Object로 변환
- Mock 호환: Domain Layer 완성 전까지 호환성 보장

Tables Mapped:
- tv_trading_variables: 매매 변수 정의
- tv_variable_parameters: 변수별 파라미터
- tv_indicator_categories: 카테고리 정보
- cfg_app_settings: 앱 설정
"""

import json
import logging
from typing import List, Dict, Any, Optional

from upbit_auto_trading.domain.repositories.settings_repository import SettingsRepository
from upbit_auto_trading.domain.entities.trigger import TradingVariable
from upbit_auto_trading.domain.value_objects.compatibility_rules import ComparisonGroupRules
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager


class SqliteSettingsRepository(SettingsRepository):
    """SQLite 기반 Settings Repository 구현 (읽기 전용)"""

    def __init__(self, db_manager: DatabaseManager):
        self._db = db_manager
        self._logger = logging.getLogger(__name__)
        self._cache: Dict[str, Any] = {}  # 성능을 위한 캐시

    def get_trading_variables(self) -> List[TradingVariable]:
        """매매 변수 정의 목록 조회"""
        if 'trading_variables' in self._cache:
            self._logger.debug("📋 캐시에서 매매 변수 목록 반환")
            return self._cache['trading_variables']

        query = """
        SELECT
            tv.variable_id,
            tv.display_name_ko,
            tv.display_name_en,
            tv.purpose_category,
            tv.chart_category,
            tv.comparison_group,
            tv.description,
            tv.source,
            tv.parameter_required,
            tv.is_active
        FROM tv_trading_variables tv
        WHERE tv.is_active = 1
        ORDER BY tv.variable_id
        """

        try:
            rows = self._db.execute_query('settings', query)
            variables = []

            for row in rows:
                row_dict = dict(row)

                # TradingVariable 생성
                variable = TradingVariable(
                    variable_id=row_dict['variable_id'],
                    display_name=row_dict.get('display_name_ko', row_dict['variable_id']),
                    purpose_category=row_dict['purpose_category'],
                    chart_category=row_dict['chart_category'],
                    comparison_group=row_dict['comparison_group']
                )
                variables.append(variable)

            # 캐시 저장
            self._cache['trading_variables'] = variables

            self._logger.info(f"✅ 매매 변수 {len(variables)}개 로드 완료")
            return variables

        except Exception as e:
            self._logger.error(f"❌ 매매 변수 조회 실패: {e}")
            raise

    def find_trading_variable_by_id(self, variable_id: str) -> Optional[TradingVariable]:
        """변수 ID로 매매 변수 조회"""
        variables = self.get_trading_variables()

        for variable in variables:
            if variable.variable_id == variable_id:
                return variable

        self._logger.debug(f"🔍 변수 ID '{variable_id}' 조회 결과: None")
        return None

    def get_trading_variables_by_category(self, purpose_category: str) -> List[TradingVariable]:
        """목적 카테고리별 매매 변수 조회"""
        variables = self.get_trading_variables()

        filtered_variables = [
            var for var in variables
            if var.purpose_category == purpose_category
        ]

        self._logger.debug(f"📊 목적 카테고리 '{purpose_category}': {len(filtered_variables)}개 변수")
        return filtered_variables

    def get_trading_variables_by_chart_category(self, chart_category: str) -> List[TradingVariable]:
        """차트 카테고리별 매매 변수 조회"""
        variables = self.get_trading_variables()

        filtered_variables = [
            var for var in variables
            if var.chart_category == chart_category
        ]

        self._logger.debug(f"📈 차트 카테고리 '{chart_category}': {len(filtered_variables)}개 변수")
        return filtered_variables

    def get_trading_variables_by_comparison_group(self, comparison_group: str) -> List[TradingVariable]:
        """비교 그룹별 매매 변수 조회"""
        variables = self.get_trading_variables()

        filtered_variables = [
            var for var in variables
            if var.comparison_group == comparison_group
        ]

        self._logger.debug(f"🔗 비교 그룹 '{comparison_group}': {len(filtered_variables)}개 변수")
        return filtered_variables

    def get_compatible_variables(self, variable_id: str) -> List[TradingVariable]:
        """특정 변수와 호환 가능한 모든 변수 조회"""
        base_variable = self.find_trading_variable_by_id(variable_id)
        if not base_variable:
            self._logger.warning(f"⚠️ 기준 변수 '{variable_id}' 조회 실패")
            return []

        # 같은 comparison_group의 모든 변수 조회
        compatible_variables = self.get_trading_variables_by_comparison_group(
            base_variable.comparison_group
        )

        # 자기 자신 제외
        compatible_variables = [
            var for var in compatible_variables
            if var.variable_id != variable_id
        ]

        self._logger.debug(f"🤝 '{variable_id}'와 호환 가능한 변수: {len(compatible_variables)}개")
        return compatible_variables

    def get_variable_parameters(self, variable_id: str) -> List[Dict[str, Any]]:
        """특정 변수의 파라미터 정의 조회"""
        cache_key = f"parameters_{variable_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        query = """
        SELECT
            parameter_name,
            parameter_type,
            default_value,
            min_value,
            max_value,
            enum_values,
            is_required,
            display_name_ko,
            display_name_en,
            description,
            display_order
        FROM tv_variable_parameters
        WHERE variable_id = ?
        ORDER BY display_order
        """

        try:
            rows = self._db.execute_query('settings', query, (variable_id,))
            parameters = []

            for row in rows:
                param = dict(row)

                # enum_values JSON 파싱
                if param.get('enum_values'):
                    try:
                        param['enum_values'] = json.loads(param['enum_values'])
                    except json.JSONDecodeError:
                        # JSON 형식이 아닌 경우 파이프(|)로 분할
                        param['enum_values'] = param['enum_values'].split('|')

                # 타입 변환
                if param.get('min_value'):
                    try:
                        param['min_value'] = float(param['min_value'])
                    except (ValueError, TypeError):
                        param['min_value'] = None

                if param.get('max_value'):
                    try:
                        param['max_value'] = float(param['max_value'])
                    except (ValueError, TypeError):
                        param['max_value'] = None

                parameters.append(param)

            # 캐시 저장
            self._cache[cache_key] = parameters

            self._logger.debug(f"📋 변수 '{variable_id}' 파라미터 {len(parameters)}개 로드")
            return parameters

        except Exception as e:
            self._logger.error(f"❌ 변수 파라미터 조회 실패: {variable_id} - {e}")
            raise

    def get_comparison_group_rules(self) -> ComparisonGroupRules:
        """비교 그룹별 호환성 규칙 조회"""
        if 'comparison_group_rules' in self._cache:
            return self._cache['comparison_group_rules']

        # 카테고리 정보 조회
        category_query = """
        SELECT
            category_type,
            category_key,
            category_name_ko,
            description
        FROM tv_indicator_categories
        WHERE is_active = 1
        ORDER BY category_type, display_order
        """

        try:
            rows = self._db.execute_query('settings', category_query)

            purpose_categories = {}
            chart_categories = {}
            comparison_groups = {}

            for row in rows:
                row_dict = dict(row)
                category_type = row_dict['category_type']
                category_key = row_dict['category_key']
                category_info = {
                    'name': row_dict['category_name_ko'],
                    'description': row_dict.get('description', '')
                }

                if category_type == 'purpose':
                    purpose_categories[category_key] = category_info
                elif category_type == 'chart':
                    chart_categories[category_key] = category_info
                elif category_type == 'comparison':
                    comparison_groups[category_key] = category_info

            # 호환성 매트릭스 구성 (기본 규칙)
            compatibility_matrix = {
                'price_comparable': ['price_comparable'],
                'percentage_comparable': ['percentage_comparable'],
                'zero_centered': ['zero_centered'],
                'volume_comparable': ['volume_comparable']
            }

            # ComparisonGroupRules 생성 (Mock 방식으로 간단히 구현)
            # 실제 Domain Value Object가 완성되면 교체
            rules = {
                'purpose_categories': purpose_categories,
                'chart_categories': chart_categories,
                'comparison_groups': comparison_groups,
                'compatibility_matrix': compatibility_matrix
            }

            # 캐시 저장
            self._cache['comparison_group_rules'] = rules

            self._logger.info("✅ 호환성 규칙 로드 완료")
            return rules

        except Exception as e:
            self._logger.error(f"❌ 호환성 규칙 조회 실패: {e}")
            raise

    def get_indicator_categories(self) -> Dict[str, Dict[str, Any]]:
        """지표 카테고리 정보 조회"""
        if 'indicator_categories' in self._cache:
            return self._cache['indicator_categories']

        query = """
        SELECT
            category_type,
            category_key,
            category_name_ko,
            category_name_en,
            description,
            icon,
            color_code,
            display_order
        FROM tv_indicator_categories
        WHERE is_active = 1
        ORDER BY category_type, display_order
        """

        try:
            rows = self._db.execute_query('settings', query)
            categories = {}

            for row in rows:
                row_dict = dict(row)
                category_type = row_dict['category_type']

                if category_type not in categories:
                    categories[category_type] = {}

                categories[category_type][row_dict['category_key']] = {
                    'name_ko': row_dict['category_name_ko'],
                    'name_en': row_dict.get('category_name_en'),
                    'description': row_dict.get('description'),
                    'icon': row_dict.get('icon'),
                    'color_code': row_dict.get('color_code'),
                    'display_order': row_dict.get('display_order', 0)
                }

            # 캐시 저장
            self._cache['indicator_categories'] = categories

            self._logger.info(f"✅ 지표 카테고리 로드 완료: {len(categories)}개 타입")
            return categories

        except Exception as e:
            self._logger.error(f"❌ 지표 카테고리 조회 실패: {e}")
            raise

    def get_app_setting(self, key: str, default_value: Any = None) -> Any:
        """애플리케이션 설정값 조회"""
        query = """
        SELECT value FROM cfg_app_settings
        WHERE key = ?
        """

        try:
            rows = self._db.execute_query('settings', query, (key,))

            if rows:
                value = rows[0]['value']

                # JSON 형태인 경우 파싱 시도
                if value and isinstance(value, str):
                    if value.startswith('{') or value.startswith('['):
                        try:
                            return json.loads(value)
                        except json.JSONDecodeError:
                            pass

                return value
            else:
                self._logger.debug(f"🔍 앱 설정 '{key}' 조회 결과: 기본값 사용")
                return default_value

        except Exception as e:
            self._logger.error(f"❌ 앱 설정 조회 실패: {key} - {e}")
            return default_value

    def clear_cache(self) -> None:
        """캐시 초기화"""
        cache_size = len(self._cache)
        self._cache.clear()
        self._logger.info(f"🧹 설정 캐시 초기화 완료 (이전 캐시: {cache_size}개 항목)")

    def get_cache_info(self) -> Dict[str, Any]:
        """캐시 정보 조회 (디버깅/모니터링용)"""
        return {
            'cache_size': len(self._cache),
            'cached_keys': list(self._cache.keys()),
            'memory_usage_estimate': sum(
                len(str(value)) for value in self._cache.values()
            )
        }
