#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
차트 변수 카테고리 서비스

변수 카테고리 시스템을 관리하고 차트 표현 방식을 결정하는 서비스 클래스
"""

import sqlite3
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import sys
from pathlib import Path

# 새로운 통합 DB 경로 시스템 import
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent.parent.parent.parent))
try:
    from database_paths import APP_SETTINGS_DB_PATH
    USE_NEW_DB_PATHS = True
except ImportError:
    # 백업: 새 경로 시스템을 찾을 수 없으면 기존 방식 사용
    USE_NEW_DB_PATHS = False
    APP_SETTINGS_DB_PATH = "data/app_settings.sqlite3"


@dataclass
class VariableDisplayConfig:
    """변수 표시 설정"""
    variable_id: str
    variable_name: str
    description: Optional[str]
    category: str
    display_type: str
    scale_min: Optional[float] = None
    scale_max: Optional[float] = None
    unit: str = ""
    default_color: str = "#007bff"
    subplot_height_ratio: float = 0.3
    compatible_categories: List[str] = None
    is_active: bool = True

    def __post_init__(self):
        if self.compatible_categories is None:
            self.compatible_categories = []


@dataclass
class ChartLayoutInfo:
    """차트 레이아웃 정보"""
    main_chart_variables: List[Dict[str, Any]]
    subplots: List[Dict[str, Any]]
    height_ratios: List[float]
    color_assignments: Dict[str, str]


class ChartVariableService:
    """차트 변수 카테고리 서비스"""

    def __init__(self, db_path: str = None):
        # 새로운 통합 DB 경로 시스템 사용 (하위 호환성 유지)
        if db_path is None:
            if USE_NEW_DB_PATHS:
                self.db_path = APP_SETTINGS_DB_PATH  # settings.sqlite3로 매핑됨
                print(f"🔗 ChartVariableService: 새로운 통합 DB 사용 - {self.db_path}")
            else:
                self.db_path = "data/app_settings.sqlite3"  # 레거시 경로
                print(f"⚠️ ChartVariableService: 레거시 DB 경로 사용 - {self.db_path}")
        else:
            self.db_path = db_path  # 사용자 지정 경로
            print(f"📂 ChartVariableService: 사용자 지정 DB 경로 - {self.db_path}")
            
        self._variable_cache: Dict[str, VariableDisplayConfig] = {}
        self._cache_timestamp = None
        self._refresh_cache()

    def _refresh_cache(self):
        """변수 캐시 갱신"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT variable_id, variable_name, description, category, display_type,
                       scale_min, scale_max, unit, default_color, subplot_height_ratio,
                       compatible_categories, is_active
                FROM chart_variables
                WHERE is_active = 1
            """)
            
            self._variable_cache.clear()
            for row in cursor.fetchall():
                compatible_cats = json.loads(row[10]) if row[10] else []
                
                config = VariableDisplayConfig(
                    variable_id=row[0],
                    variable_name=row[1],
                    description=row[2],
                    category=row[3],
                    display_type=row[4],
                    scale_min=row[5],
                    scale_max=row[6],
                    unit=row[7],
                    default_color=row[8],
                    subplot_height_ratio=row[9],
                    compatible_categories=compatible_cats,
                    is_active=bool(row[11])
                )
                
                self._variable_cache[row[0]] = config
            
            self._cache_timestamp = datetime.now()

    def get_variable_config(self, variable_id: str) -> Optional[VariableDisplayConfig]:
        """변수 설정 조회"""
        # 캐시가 오래된 경우 갱신 (5분)
        if (self._cache_timestamp and 
            (datetime.now() - self._cache_timestamp).seconds > 300):
            self._refresh_cache()
        
        return self._variable_cache.get(variable_id)

    def get_variable_by_name(self, variable_name: str) -> Optional[VariableDisplayConfig]:
        """변수명으로 설정 조회"""
        for config in self._variable_cache.values():
            if config.variable_name == variable_name:
                return config
        return None

    def is_compatible_external_variable(self, base_variable_name: str, 
                                      external_variable_name: str) -> Tuple[bool, str]:
        """외부변수 호환성 검사 (변수명 기반)"""
        try:
            # 변수명으로 데이터베이스에서 변수 정보 조회
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 기본 변수 정보 조회
                cursor.execute("""
                    SELECT id, variable_name, category 
                    FROM chart_variables 
                    WHERE variable_name = ?
                """, (base_variable_name,))
                base_result = cursor.fetchone()
                
                if not base_result:
                    return False, f"기본 변수 '{base_variable_name}'를 찾을 수 없습니다."
                
                base_id, base_name, base_category = base_result
                
                # 외부 변수 정보 조회
                cursor.execute("""
                    SELECT id, variable_name, category 
                    FROM chart_variables 
                    WHERE variable_name = ?
                """, (external_variable_name,))
                external_result = cursor.fetchone()
                
                if not external_result:
                    return False, f"외부 변수 '{external_variable_name}'를 찾을 수 없습니다."
                
                external_id, external_name, external_category = external_result
                
                # 먼저 변수 ID를 통한 직접 호환성 규칙 확인
                cursor.execute("""
                    SELECT compatibility_reason, min_value_constraint, max_value_constraint
                    FROM variable_compatibility_rules
                    WHERE base_variable_id = ? AND compatible_category = ?
                """, (base_id, external_category))
                
                compatibility_rule = cursor.fetchone()
                
                if compatibility_rule:
                    reason, min_val, max_val = compatibility_rule
                    constraint_info = ""
                    if min_val is not None or max_val is not None:
                        constraint_info = f" (값 범위: {min_val}-{max_val})"
                    return True, f"호환 가능: {reason}{constraint_info}"
                
                # 변수 ID 기반 규칙이 없으면 카테고리 기반 기본 호환성 확인
                # 같은 카테고리끼리는 기본적으로 호환 가능
                if base_category == external_category:
                    if base_category == "price_overlay":
                        return True, "호환 가능: 같은 가격 스케일을 사용하는 변수들입니다."
                    elif base_category == "oscillator":
                        return True, "호환 가능: 같은 오실레이터 계열 지표들입니다 (0-100 범위)."
                    elif base_category == "momentum":
                        return True, "호환 가능: 같은 모멘텀 지표 계열입니다."
                    elif base_category == "volume":
                        return True, "호환 가능: 같은 거래량 계열 지표들입니다."
                    else:
                        return True, f"호환 가능: 같은 카테고리({base_category}) 변수들입니다."
                
                # 서로 다른 카테고리인 경우 비호환
                return False, (f"호환되지 않음: '{base_name}' ({base_category})는 "
                              f"'{external_name}' ({external_category})와 호환되지 않습니다. "
                              f"차트에서 의미 있는 비교가 어려운 변수 조합입니다.")
                    
        except Exception as e:
            return False, f"호환성 검증 중 오류 발생: {str(e)}"

    def _get_compatibility_constraints(self, base_variable_id: str, 
                                     category: str) -> Optional[Tuple[Optional[float], Optional[float]]]:
        """호환성 제약 조건 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT min_value_constraint, max_value_constraint
                FROM variable_compatibility_rules
                WHERE base_variable_id = ? AND compatible_category = ?
            """, (base_variable_id, category))
            
            result = cursor.fetchone()
            return (result[0], result[1]) if result else None

    def get_chart_layout_info(self, variable_ids: List[str], 
                            template_name: str = 'standard_trading') -> ChartLayoutInfo:
        """차트 레이아웃 정보 생성"""
        main_chart_vars = []
        subplots = []
        
        # 템플릿 정보 조회
        template = self._get_layout_template(template_name)
        color_palette = template.get('color_palette', {}) if template else {}
        
        color_index = 0
        default_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                         '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        for var_id in variable_ids:
            config = self.get_variable_config(var_id)
            if not config:
                continue
            
            # 색상 할당
            color = config.default_color
            if color_index < len(default_colors):
                color = default_colors[color_index]
            color_index += 1
            
            var_info = {
                "variable_id": var_id,
                "name": config.variable_name,
                "config": config,
                "color": color
            }
            
            if config.category == 'price_overlay':
                main_chart_vars.append(var_info)
            else:
                var_info["subplot_config"] = self._get_subplot_config(config, template)
                subplots.append(var_info)
        
        # 높이 비율 계산
        height_ratios = self._calculate_height_ratios(subplots, template)
        
        # 색상 할당 맵
        color_assignments = {var["variable_id"]: var["color"] 
                           for var in main_chart_vars + subplots}
        
        return ChartLayoutInfo(
            main_chart_variables=main_chart_vars,
            subplots=subplots,
            height_ratios=height_ratios,
            color_assignments=color_assignments
        )

    def _get_layout_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """레이아웃 템플릿 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT main_chart_height_ratio, subplot_configurations, color_palette
                FROM chart_layout_templates
                WHERE template_name = ?
            """, (template_name,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'main_chart_height_ratio': result[0],
                    'subplot_configurations': json.loads(result[1]),
                    'color_palette': json.loads(result[2]) if result[2] else {}
                }
            return None

    def _get_subplot_config(self, variable_config: VariableDisplayConfig, 
                          template: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """서브플롯 설정 생성"""
        subplot_config = {
            'height_ratio': variable_config.subplot_height_ratio,
            'scale_min': variable_config.scale_min,
            'scale_max': variable_config.scale_max,
            'unit': variable_config.unit,
            'display_type': variable_config.display_type
        }
        
        # 템플릿에서 특정 설정 오버라이드
        if template and 'subplot_configurations' in template:
            template_subplot_configs = template['subplot_configurations']
            if variable_config.variable_id in template_subplot_configs:
                template_config = template_subplot_configs[variable_config.variable_id]
                subplot_config.update(template_config)
        
        return subplot_config

    def _calculate_height_ratios(self, subplots: List[Dict], 
                               template: Optional[Dict[str, Any]]) -> List[float]:
        """차트 높이 비율 계산"""
        if not subplots:
            return [1.0]  # 메인 차트만
        
        # 템플릿에서 메인 차트 비율 가져오기
        main_ratio = template.get('main_chart_height_ratio', 0.6) if template else 0.6
        remaining = 1.0 - main_ratio
        
        # 서브플롯들의 총 높이 비율 계산
        total_subplot_ratio = sum(
            subplot.get("subplot_config", {}).get("height_ratio", 0.3) 
            for subplot in subplots
        )
        
        if total_subplot_ratio == 0:
            return [1.0]
        
        ratios = [main_ratio]
        for subplot in subplots:
            subplot_config = subplot.get("subplot_config", {})
            subplot_ratio = subplot_config.get("height_ratio", 0.3)
            normalized_ratio = (subplot_ratio / total_subplot_ratio) * remaining
            ratios.append(normalized_ratio)
        
        return ratios

    def register_variable_usage(self, variable_id: str, condition_id: Optional[int] = None,
                              usage_context: str = 'trigger_builder',
                              chart_display_info: Optional[Dict[str, Any]] = None,
                              render_time_ms: Optional[int] = None):
        """변수 사용 로그 등록"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO variable_usage_logs
                (variable_id, condition_id, usage_context, chart_display_info, render_time_ms)
                VALUES (?, ?, ?, ?, ?)
            """, (
                variable_id,
                condition_id,
                usage_context,
                json.dumps(chart_display_info) if chart_display_info else None,
                render_time_ms
            ))
            
            conn.commit()

    def get_usage_statistics(self, variable_id: str, 
                           days: int = 30) -> Dict[str, Any]:
        """변수 사용 통계 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 기본 사용 횟수
            cursor.execute("""
                SELECT COUNT(*) 
                FROM variable_usage_logs 
                WHERE variable_id = ? 
                AND created_at >= datetime('now', '-{} days')
            """.format(days), (variable_id,))
            
            usage_count = cursor.fetchone()[0]
            
            # 컨텍스트별 사용 분포
            cursor.execute("""
                SELECT usage_context, COUNT(*) 
                FROM variable_usage_logs 
                WHERE variable_id = ? 
                AND created_at >= datetime('now', '-{} days')
                GROUP BY usage_context
            """.format(days), (variable_id,))
            
            context_distribution = dict(cursor.fetchall())
            
            # 평균 렌더링 시간
            cursor.execute("""
                SELECT AVG(render_time_ms) 
                FROM variable_usage_logs 
                WHERE variable_id = ? 
                AND render_time_ms IS NOT NULL
                AND created_at >= datetime('now', '-{} days')
            """.format(days), (variable_id,))
            
            avg_render_time = cursor.fetchone()[0]
            
            return {
                'usage_count': usage_count,
                'context_distribution': context_distribution,
                'avg_render_time_ms': avg_render_time,
                'period_days': days
            }

    def get_available_variables_by_category(self, category: str = None) -> List[VariableDisplayConfig]:
        """카테고리별 사용 가능한 변수 목록 조회"""
        variables = list(self._variable_cache.values())
        
        if category:
            variables = [var for var in variables if var.category == category]
        
        return sorted(variables, key=lambda x: x.variable_name)

    def validate_variable_combination(self, variable_ids: List[str]) -> Tuple[bool, List[str]]:
        """변수 조합 유효성 검사"""
        warnings = []
        
        # 같은 카테고리 변수들이 너무 많은지 확인
        category_counts = {}
        for var_id in variable_ids:
            config = self.get_variable_config(var_id)
            if config:
                category_counts[config.category] = category_counts.get(config.category, 0) + 1
        
        # 서브플롯이 너무 많은 경우 경고
        subplot_categories = ['oscillator', 'momentum', 'volume']
        subplot_count = sum(category_counts.get(cat, 0) for cat in subplot_categories)
        
        if subplot_count > 4:
            warnings.append(f"서브플롯이 {subplot_count}개로 너무 많습니다. 차트가 복잡해질 수 있습니다.")
        
        # 같은 카테고리 변수가 너무 많은 경우 경고
        for category, count in category_counts.items():
            if count > 3:
                warnings.append(f"{category} 카테고리 변수가 {count}개로 너무 많습니다.")
        
        return len(warnings) == 0, warnings


# 전역 서비스 인스턴스
_chart_variable_service = None


def get_chart_variable_service() -> ChartVariableService:
    """차트 변수 서비스 싱글톤 반환"""
    global _chart_variable_service
    if _chart_variable_service is None:
        _chart_variable_service = ChartVariableService()
    return _chart_variable_service
