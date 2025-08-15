"""
SQLite TradingVariable Repository 구현
- ITradingVariableRepository 인터페이스 구현
- settings.sqlite3의 tv_trading_variables 테이블과 연동
- YAML 파일과 DB 간 동기화 기능
"""
import yaml
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging
from datetime import datetime

from upbit_auto_trading.domain.trigger_builder.entities.trading_variable import TradingVariable
from upbit_auto_trading.domain.trigger_builder.repositories.i_trading_variable_repository import ITradingVariableRepository
from upbit_auto_trading.domain.trigger_builder.enums import VariableCategory, ChartCategory, ComparisonGroup
from upbit_auto_trading.domain.trigger_builder.value_objects.variable_parameter import VariableParameter
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager


class SqliteTradingVariableRepository(ITradingVariableRepository):
    """SQLite 기반 TradingVariable Repository"""

    def __init__(self, db_manager: DatabaseManager):
        self._db_manager = db_manager
        self._logger = logging.getLogger(__name__)
        self._cache: Dict[str, TradingVariable] = {}
        self._cache_loaded = False

    async def get_by_id(self, variable_id: str) -> Optional[TradingVariable]:
        """변수 ID로 조회"""
        try:
            await self._ensure_cache_loaded()
            return self._cache.get(variable_id)
        except Exception as e:
            self._logger.error(f"변수 조회 실패 (ID: {variable_id}): {e}")
            return None

    async def get_all_active(self) -> List[TradingVariable]:
        """활성화된 모든 변수 조회"""
        try:
            await self._ensure_cache_loaded()
            return [var for var in self._cache.values() if var.is_active]
        except Exception as e:
            self._logger.error(f"활성 변수 조회 실패: {e}")
            return []

    async def get_by_category(self, category: VariableCategory) -> List[TradingVariable]:
        """카테고리별 변수 조회"""
        try:
            await self._ensure_cache_loaded()
            return [var for var in self._cache.values()
                    if var.purpose_category == category and var.is_active]
        except Exception as e:
            self._logger.error(f"카테고리별 변수 조회 실패 ({category}): {e}")
            return []

    async def get_by_comparison_group(self, group: ComparisonGroup) -> List[TradingVariable]:
        """비교 그룹별 변수 조회"""
        try:
            await self._ensure_cache_loaded()
            return [var for var in self._cache.values()
                    if var.comparison_group == group and var.is_active]
        except Exception as e:
            self._logger.error(f"비교 그룹별 변수 조회 실패 ({group}): {e}")
            return []

    async def search_by_name(self, search_term: str, language: str = "ko") -> List[TradingVariable]:
        """이름으로 변수 검색"""
        try:
            await self._ensure_cache_loaded()
            search_term = search_term.lower()
            results = []

            for var in self._cache.values():
                if not var.is_active:
                    continue

                if language == "ko":
                    if search_term in var.display_name_ko.lower():
                        results.append(var)
                else:
                    if search_term in var.display_name_en.lower():
                        results.append(var)

            return results
        except Exception as e:
            self._logger.error(f"변수 검색 실패 (검색어: {search_term}): {e}")
            return []

    async def create(self, variable: TradingVariable) -> TradingVariable:
        """변수 생성"""
        try:
            with self._db_manager.get_connection("settings") as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO tv_trading_variables (
                        variable_id, display_name_ko, display_name_en, description,
                        purpose_category, chart_category, comparison_group,
                        parameter_required, is_active, source, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    variable.variable_id, variable.display_name_ko, variable.display_name_en,
                    variable.description, variable.purpose_category.value,
                    variable.chart_category.value, variable.comparison_group.value,
                    variable.parameter_required, variable.is_active, variable.source,
                    variable.created_at.isoformat(), variable.updated_at.isoformat()
                ))

                # 파라미터도 저장
                for param in variable.parameters:
                    await self._save_parameter(cursor, variable.variable_id, param)

            # 캐시 업데이트
            self._cache[variable.variable_id] = variable

            self._logger.info(f"변수 생성 성공: {variable.variable_id}")
            return variable

        except Exception as e:
            self._logger.error(f"변수 생성 실패 ({variable.variable_id}): {e}")
            raise

    async def update(self, variable: TradingVariable) -> TradingVariable:
        """변수 수정"""
        try:
            variable.updated_at = datetime.now()

            with self._db_manager.get_connection("settings") as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE tv_trading_variables SET
                        display_name_ko = ?, display_name_en = ?, description = ?,
                        purpose_category = ?, chart_category = ?, comparison_group = ?,
                        parameter_required = ?, is_active = ?, updated_at = ?
                    WHERE variable_id = ?
                """, (
                    variable.display_name_ko, variable.display_name_en, variable.description,
                    variable.purpose_category.value, variable.chart_category.value,
                    variable.comparison_group.value, variable.parameter_required,
                    variable.is_active, variable.updated_at.isoformat(), variable.variable_id
                ))

                # 기존 파라미터 삭제 후 재생성
                cursor.execute("DELETE FROM tv_variable_parameters WHERE variable_id = ?",
                               (variable.variable_id,))

                for param in variable.parameters:
                    await self._save_parameter(cursor, variable.variable_id, param)

            # 캐시 업데이트
            self._cache[variable.variable_id] = variable

            self._logger.info(f"변수 수정 성공: {variable.variable_id}")
            return variable

        except Exception as e:
            self._logger.error(f"변수 수정 실패 ({variable.variable_id}): {e}")
            raise

    async def delete(self, variable_id: str) -> bool:
        """변수 삭제"""
        try:
            with self._db_manager.get_connection("settings") as conn:
                cursor = conn.cursor()

                # 파라미터 먼저 삭제
                cursor.execute("DELETE FROM tv_variable_parameters WHERE variable_id = ?",
                               (variable_id,))

                # 변수 삭제
                cursor.execute("DELETE FROM tv_trading_variables WHERE variable_id = ?",
                               (variable_id,))

            # 캐시에서 제거
            if variable_id in self._cache:
                del self._cache[variable_id]

            self._logger.info(f"변수 삭제 성공: {variable_id}")
            return True

        except Exception as e:
            self._logger.error(f"변수 삭제 실패 ({variable_id}): {e}")
            return False

    async def get_compatible_variables(self, variable_id: str) -> List[TradingVariable]:
        """호환 가능한 변수들 조회"""
        try:
            target_var = await self.get_by_id(variable_id)
            if not target_var:
                return []

            compatible_groups = self._get_compatible_groups(target_var.comparison_group)

            await self._ensure_cache_loaded()
            return [var for var in self._cache.values()
                    if var.is_active
                    and var.variable_id != variable_id
                    and var.comparison_group in compatible_groups]

        except Exception as e:
            self._logger.error(f"호환 변수 조회 실패 ({variable_id}): {e}")
            return []

    async def bulk_create(self, variables: List[TradingVariable]) -> List[TradingVariable]:
        """변수 일괄 생성"""
        created_variables = []
        try:
            for variable in variables:
                created_var = await self.create(variable)
                created_variables.append(created_var)

            self._logger.info(f"변수 일괄 생성 성공: {len(created_variables)}개")
            return created_variables

        except Exception as e:
            self._logger.error(f"변수 일괄 생성 실패: {e}")
            return created_variables

    async def get_variables_with_parameters(self) -> List[TradingVariable]:
        """파라미터가 있는 변수들 조회"""
        try:
            await self._ensure_cache_loaded()
            return [var for var in self._cache.values()
                    if var.is_active and var.parameter_required and len(var.parameters) > 0]
        except Exception as e:
            self._logger.error(f"파라미터 변수 조회 실패: {e}")
            return []

    async def get_meta_variables(self) -> List[TradingVariable]:
        """메타 변수들 조회 (META_ 접두사)"""
        try:
            await self._ensure_cache_loaded()
            return [var for var in self._cache.values()
                    if var.is_active and var.is_meta_variable()]
        except Exception as e:
            self._logger.error(f"메타 변수 조회 실패: {e}")
            return []

    async def get_dynamic_management_variables(self) -> List[TradingVariable]:
        """동적 관리 변수들 조회"""
        try:
            await self._ensure_cache_loaded()
            return [var for var in self._cache.values()
                    if var.is_active and var.is_dynamic_management_variable()]
        except Exception as e:
            self._logger.error(f"동적 관리 변수 조회 실패: {e}")
            return []

    async def get_change_detection_variables(self) -> List[TradingVariable]:
        """변화 감지 변수들 조회"""
        try:
            await self._ensure_cache_loaded()
            return [var for var in self._cache.values()
                    if var.is_active and var.is_change_detection_variable()]
        except Exception as e:
            self._logger.error(f"변화 감지 변수 조회 실패: {e}")
            return []

    async def get_external_trackable_variables(self) -> List[TradingVariable]:
        """외부 추적 가능한 변수들 조회"""
        try:
            await self._ensure_cache_loaded()
            return [var for var in self._cache.values()
                    if var.is_active
                    and any(param.parameter_type == "external_variable" for param in var.parameters)]
        except Exception as e:
            self._logger.error(f"외부 추적 변수 조회 실패: {e}")
            return []

    async def load_from_yaml_config(self) -> List[TradingVariable]:
        """YAML 설정파일에서 변수들 로드"""
        try:
            yaml_path = Path("data_info/tv_trading_variables.yaml")
            if not yaml_path.exists():
                self._logger.warning(f"YAML 파일을 찾을 수 없습니다: {yaml_path}")
                return []

            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            variables = []
            trading_vars = data.get('trading_variables', {})

            for var_id, var_data in trading_vars.items():
                try:
                    variable = self._create_variable_from_yaml(var_id, var_data)
                    variables.append(variable)
                except Exception as e:
                    self._logger.error(f"YAML 변수 생성 실패 ({var_id}): {e}")

            self._logger.info(f"YAML에서 {len(variables)}개 변수 로드 성공")
            return variables

        except Exception as e:
            self._logger.error(f"YAML 로드 실패: {e}")
            return []

    async def _ensure_cache_loaded(self) -> None:
        """캐시가 로드되지 않았으면 DB에서 로드"""
        if not self._cache_loaded:
            await self._load_cache_from_db()

    async def _load_cache_from_db(self) -> None:
        """DB에서 모든 변수를 캐시로 로드"""
        try:
            with self._db_manager.get_connection("settings") as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT variable_id, display_name_ko, display_name_en, description,
                           purpose_category, chart_category, comparison_group,
                           parameter_required, is_active, source, created_at, updated_at
                    FROM tv_trading_variables
                """)

                for row in cursor.fetchall():
                    variable = self._create_variable_from_db_row(row)
                    # 파라미터 로드
                    await self._load_parameters_for_variable(cursor, variable)
                    self._cache[variable.variable_id] = variable

            self._cache_loaded = True
            self._logger.info(f"DB에서 {len(self._cache)}개 변수 캐시 로드 완료")

        except Exception as e:
            self._logger.error(f"캐시 로드 실패: {e}")

    def _create_variable_from_db_row(self, row) -> TradingVariable:
        """DB 행에서 TradingVariable 생성"""
        return TradingVariable(
            variable_id=row[0],
            display_name_ko=row[1],
            display_name_en=row[2],
            description=row[3],
            purpose_category=VariableCategory(row[4]),
            chart_category=ChartCategory(row[5]),
            comparison_group=ComparisonGroup(row[6]),
            parameter_required=bool(row[7]),
            is_active=bool(row[8]),
            source=row[9],
            created_at=datetime.fromisoformat(row[10]),
            updated_at=datetime.fromisoformat(row[11])
        )

    def _create_variable_from_yaml(self, var_id: str, var_data: Dict[str, Any]) -> TradingVariable:
        """YAML 데이터에서 TradingVariable 생성"""
        return TradingVariable(
            variable_id=var_id,
            display_name_ko=var_data.get('display_name_ko', ''),
            display_name_en=var_data.get('display_name_en', ''),
            description=var_data.get('description', ''),
            purpose_category=VariableCategory(var_data.get('purpose_category', 'trend')),
            chart_category=ChartCategory(var_data.get('chart_category', 'overlay')),
            comparison_group=ComparisonGroup(var_data.get('comparison_group', 'price_comparable')),
            parameter_required=var_data.get('parameter_required', False),
            is_active=var_data.get('is_active', True),
            source=var_data.get('source', 'yaml'),
            created_at=datetime.fromisoformat(var_data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(var_data.get('updated_at', datetime.now().isoformat()))
        )

    async def _load_parameters_for_variable(self, cursor, variable: TradingVariable) -> None:
        """변수의 파라미터들을 DB에서 로드"""
        try:
            cursor.execute("""
                SELECT parameter_name, display_name_ko, display_name_en,
                       parameter_type, default_value, min_value, max_value, description, enum_values
                FROM tv_variable_parameters
                WHERE variable_id = ?
            """, (variable.variable_id,))

            for param_row in cursor.fetchall():
                # 타입별 값 변환
                parameter_type = param_row[3]
                default_value = self._convert_parameter_value(param_row[4], parameter_type)
                min_value = self._convert_parameter_value(param_row[5], parameter_type) if param_row[5] is not None else None
                max_value = self._convert_parameter_value(param_row[6], parameter_type) if param_row[6] is not None else None
                enum_values = param_row[8]  # enum_values 추가

                parameter = VariableParameter(
                    parameter_name=param_row[0],
                    display_name_ko=param_row[1],
                    display_name_en=param_row[2],
                    parameter_type=parameter_type,
                    default_value=default_value,
                    min_value=min_value,
                    max_value=max_value,
                    description=param_row[7],
                    enum_values=enum_values  # enum_values 전달
                )
                variable.add_parameter(parameter)

        except Exception as e:
            self._logger.error(f"파라미터 로드 실패 ({variable.variable_id}): {e}")

    def _convert_parameter_value(self, value: Any, parameter_type: str) -> Any:
        """파라미터 타입에 맞게 값 변환"""
        if value is None:
            return None

        try:
            if parameter_type == "integer":
                return int(value)
            elif parameter_type == "decimal":
                return float(value)
            elif parameter_type == "boolean":
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            elif parameter_type in ("enum", "external_variable"):
                # enum과 external_variable는 문자열로 처리
                return str(value)
            else:  # string and other types
                return str(value)
        except (ValueError, TypeError):
            self._logger.warning(f"타입 변환 실패: {value} -> {parameter_type}")
            return value

    async def _save_parameter(self, cursor, variable_id: str, parameter: VariableParameter) -> None:
        """파라미터를 DB에 저장"""
        cursor.execute("""
            INSERT INTO tv_variable_parameters (
                variable_id, parameter_name, display_name_ko, display_name_en,
                parameter_type, default_value, min_value, max_value, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            variable_id, parameter.parameter_name, parameter.display_name_ko,
            parameter.display_name_en, parameter.parameter_type, parameter.default_value,
            parameter.min_value, parameter.max_value, parameter.description
        ))

    def _get_compatible_groups(self, group: ComparisonGroup) -> set:
        """호환 가능한 비교 그룹들 반환"""
        compatibility_matrix = {
            ComparisonGroup.PRICE_COMPARABLE: {ComparisonGroup.PRICE_COMPARABLE},
            ComparisonGroup.PERCENTAGE_COMPARABLE: {ComparisonGroup.PERCENTAGE_COMPARABLE, ComparisonGroup.ZERO_CENTERED},
            ComparisonGroup.ZERO_CENTERED: {ComparisonGroup.ZERO_CENTERED, ComparisonGroup.PERCENTAGE_COMPARABLE},
            ComparisonGroup.VOLUME_COMPARABLE: {ComparisonGroup.VOLUME_COMPARABLE},
            ComparisonGroup.VOLATILITY_COMPARABLE: {ComparisonGroup.VOLATILITY_COMPARABLE},
            ComparisonGroup.CAPITAL_COMPARABLE: {ComparisonGroup.CAPITAL_COMPARABLE},
            ComparisonGroup.QUANTITY_COMPARABLE: {ComparisonGroup.QUANTITY_COMPARABLE},
            ComparisonGroup.SIGNAL_CONDITIONAL: {ComparisonGroup.SIGNAL_CONDITIONAL}
        }
        return compatibility_matrix.get(group, {group})
