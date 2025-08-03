#!/usr/bin/env python3
"""
DB 데이터 매니저 - 모든 트레이딩 변수 정보의 중앙 관리
================================================

DB 중심 설계의 핵심 컴포넌트:
- 모든 지표, 파라미터, 카테고리 정보를 DB에서 직접 관리
- 통합된 데이터 액세스 인터페이스 제공
- data_info 정보를 DB로 마이그레이션 지원

작성일: 2025-07-30
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class DBDataManager:
    """DB 기반 트레이딩 변수 데이터 관리자"""
    
    def __init__(self, db_path: str):
        """
        초기화
        
        Args:
            db_path: SQLite DB 파일 경로
        """
        self.db_path = db_path
        self._ensure_db_connection()
    
    def _ensure_db_connection(self):
        """DB 연결 확인 및 스키마 검증"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
        except Exception as e:
            raise ConnectionError(f"DB 연결 실패: {e}")
    
    def get_connection(self) -> sqlite3.Connection:
        """DB 연결 반환 (row_factory 설정 포함)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ===== 지표 정보 관리 =====
    
    def get_all_indicators(self, active_only: bool = True) -> Dict[str, Any]:
        """
        모든 지표 정보 조회
        
        Args:
            active_only: 활성 지표만 조회할지 여부
            
        Returns:
            지표 정보 딕셔너리 {indicator_id: {정보}}
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        where_clause = "WHERE is_active = 1" if active_only else ""
        
        cursor.execute(f"""
            SELECT variable_id, display_name_ko, display_name_en, 
                   purpose_category, chart_category, comparison_group, 
                   description, created_at, updated_at
            FROM tv_trading_variables 
            {where_clause}
            ORDER BY variable_id
        """)
        
        indicators = {}
        for row in cursor.fetchall():
            indicator_id = row["variable_id"]
            indicators[indicator_id] = {
                "display_name_ko": row["display_name_ko"] or "",
                "display_name_en": row["display_name_en"] or "",
                "purpose_category": row["purpose_category"] or "momentum",
                "chart_category": row["chart_category"] or "subplot",
                "comparison_group": row["comparison_group"] or "percentage_comparable",
                "description": row["description"] or f"{row['display_name_ko']} 지표",
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "parameters": self.get_indicator_parameters(indicator_id)
            }
        
        conn.close()
        return indicators
    
    def get_indicator_info(self, indicator_id: str) -> Optional[Dict[str, Any]]:
        """특정 지표 정보 조회"""
        indicators = self.get_all_indicators()
        return indicators.get(indicator_id)
    
    def get_indicator_parameters(self, indicator_id: str) -> Dict[str, Any]:
        """
        특정 지표의 모든 파라미터 정보 조회
        
        Args:
            indicator_id: 지표 ID
            
        Returns:
            파라미터 정보 딕셔너리 {param_name: {정보}}
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT parameter_name, parameter_type, default_value,
                   min_value, max_value, enum_values, 
                   display_name_ko, description, display_order
            FROM tv_variable_parameters
            WHERE variable_id = ? 
            ORDER BY display_order, parameter_name
        """, (indicator_id,))
        
        parameters = {}
        for row in cursor.fetchall():
            param_name = row["parameter_name"]
            
            # 기본 파라미터 정보
            param_info = {
                "label": row["display_name_ko"] or param_name,
                "type": self._convert_param_type(row["parameter_type"]),
                "default": self._convert_default_value(row["default_value"], row["parameter_type"]),
                "description": row["description"] or f"{param_name} 설정",
                "display_order": row["display_order"] or 0
            }
            
            # 타입별 추가 정보
            if row["parameter_type"] in ["integer", "float"]:
                if row["min_value"] is not None:
                    param_info["min"] = self._convert_numeric_value(row["min_value"], row["parameter_type"])
                if row["max_value"] is not None:
                    param_info["max"] = self._convert_numeric_value(row["max_value"], row["parameter_type"])
            
            # enum 타입 옵션
            if row["parameter_type"] == "enum" and row["enum_values"]:
                try:
                    param_info["options"] = json.loads(row["enum_values"])
                except (json.JSONDecodeError, TypeError):
                    param_info["options"] = [row["enum_values"]]
            
            parameters[param_name] = param_info
        
        conn.close()
        return parameters
    
    # ===== 카테고리 관리 =====
    
    def get_categories_with_indicators(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        카테고리별 지표 목록 조회
        
        Returns:
            {category: [(indicator_id, display_name), ...]}
        """
        indicators = self.get_all_indicators()
        categories = {}
        
        for indicator_id, info in indicators.items():
            category = info["purpose_category"]
            if category not in categories:
                categories[category] = []
            categories[category].append((indicator_id, info["display_name_ko"]))
        
        # 각 카테고리 내에서 정렬
        for category in categories:
            categories[category].sort(key=lambda x: x[1])  # display_name으로 정렬
        
        return categories
    
    def get_chart_categories(self) -> Dict[str, str]:
        """
        차트 카테고리 매핑 조회
        
        Returns:
            {indicator_id: chart_category}
        """
        indicators = self.get_all_indicators()
        return {
            indicator_id: info["chart_category"] 
            for indicator_id, info in indicators.items()
        }
    
    # ===== 통계 및 메타데이터 =====
    
    def get_database_stats(self) -> Dict[str, Any]:
        """DB 통계 정보 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 지표 수 통계
        cursor.execute("SELECT COUNT(*) as total FROM tv_trading_variables")
        total_indicators = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as active FROM tv_trading_variables WHERE is_active = 1")
        active_indicators = cursor.fetchone()["active"]
        
        # 파라미터 수 통계
        cursor.execute("SELECT COUNT(*) as total FROM tv_variable_parameters")
        total_parameters = cursor.fetchone()["total"]
        
        # 카테고리별 분포
        cursor.execute("""
            SELECT purpose_category, COUNT(*) as count 
            FROM tv_trading_variables 
            WHERE is_active = 1
            GROUP BY purpose_category
            ORDER BY count DESC
        """)
        category_distribution = {row["purpose_category"]: row["count"] for row in cursor.fetchall()}
        
        # 차트 카테고리 분포
        cursor.execute("""
            SELECT chart_category, COUNT(*) as count 
            FROM tv_trading_variables 
            WHERE is_active = 1
            GROUP BY chart_category
            ORDER BY count DESC
        """)
        chart_distribution = {row["chart_category"]: row["count"] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            "total_indicators": total_indicators,
            "active_indicators": active_indicators,
            "total_parameters": total_parameters,
            "category_distribution": category_distribution,
            "chart_distribution": chart_distribution,
            "last_updated": datetime.now().isoformat()
        }
    
    # ===== 검색 및 필터링 =====
    
    def search_indicators(self, keyword: str, category: str = None) -> Dict[str, Any]:
        """
        지표 검색
        
        Args:
            keyword: 검색 키워드 (이름, 설명에서 검색)
            category: 카테고리 필터 (선택사항)
            
        Returns:
            검색된 지표 정보
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        where_conditions = ["is_active = 1"]
        params = []
        
        if keyword:
            where_conditions.append("""
                (display_name_ko LIKE ? OR display_name_en LIKE ? OR 
                 description LIKE ? OR variable_id LIKE ?)
            """)
            keyword_pattern = f"%{keyword}%"
            params.extend([keyword_pattern] * 4)
        
        if category:
            where_conditions.append("purpose_category = ?")
            params.append(category)
        
        where_clause = " AND ".join(where_conditions)
        
        cursor.execute(f"""
            SELECT variable_id, display_name_ko, display_name_en, 
                   purpose_category, chart_category, description
            FROM tv_trading_variables 
            WHERE {where_clause}
            ORDER BY display_name_ko
        """, params)
        
        results = {}
        for row in cursor.fetchall():
            indicator_id = row["variable_id"]
            results[indicator_id] = {
                "display_name_ko": row["display_name_ko"],
                "display_name_en": row["display_name_en"],
                "purpose_category": row["purpose_category"],
                "chart_category": row["chart_category"],
                "description": row["description"]
            }
        
        conn.close()
        return results
    
    # ===== 유틸리티 메서드 =====
    
    def _convert_param_type(self, db_type: str) -> str:
        """DB 파라미터 타입을 표준 타입으로 변환"""
        type_mapping = {
            "integer": "int",
            "float": "float", 
            "string": "str",
            "boolean": "bool",
            "enum": "enum"
        }
        return type_mapping.get(db_type, "str")
    
    def _convert_default_value(self, default_str: str, param_type: str):
        """DB 기본값을 적절한 Python 타입으로 변환"""
        if not default_str:
            return None
        
        try:
            if param_type == "integer":
                return int(default_str)
            elif param_type == "float":
                return float(default_str)
            elif param_type == "boolean":
                return default_str.lower() in ["true", "1", "yes"]
            else:
                return default_str
        except (ValueError, AttributeError):
            return default_str
    
    def _convert_numeric_value(self, value_str: str, param_type: str):
        """숫자형 값 변환"""
        if not value_str:
            return None
        
        try:
            if param_type == "integer":
                return int(value_str)
            elif param_type == "float":
                return float(value_str)
            else:
                return value_str
        except (ValueError, TypeError):
            return value_str
    
    # ===== 호환성 지원 메서드 =====
    
    def get_variable_definitions_data(self) -> Dict[str, Any]:
        """
        variable_definitions.py 생성을 위한 데이터 반환
        (기존 sync_db_to_code와 호환성 유지)
        """
        indicators = self.get_all_indicators()
        categories = self.get_categories_with_indicators()
        chart_categories = self.get_chart_categories()
        stats = self.get_database_stats()
        
        return {
            "indicators": indicators,
            "categories": categories,
            "chart_categories": chart_categories,
            "stats": stats,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "source": "db_data_manager",
                "db_path": self.db_path
            }
        }


# ===== 편의 함수들 =====

def create_db_manager(db_path: str) -> DBDataManager:
    """DB 매니저 생성 편의 함수"""
    return DBDataManager(db_path)

def get_indicator_summary(db_path: str, indicator_id: str) -> Optional[Dict[str, Any]]:
    """특정 지표 요약 정보 조회 편의 함수"""
    manager = create_db_manager(db_path)
    return manager.get_indicator_info(indicator_id)

def search_indicators_simple(db_path: str, keyword: str) -> Dict[str, Any]:
    """간단한 지표 검색 편의 함수"""
    manager = create_db_manager(db_path)
    return manager.search_indicators(keyword)
