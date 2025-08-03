#!/usr/bin/env python3
"""
변수 정의 모듈 - DB 기반 동적 트레이딩 변수 시스템
Version: 2.0 (Database-driven)
"""

import sqlite3
import json
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# 호환성 검증기 import (shared 폴더)
try:
    from ..shared.compatibility_validator import CompatibilityValidator
    COMPATIBILITY_VALIDATOR_AVAILABLE = True
    print("✅ 통합 호환성 검증기 로드 성공 (trigger_builder/components)")
except ImportError as e:
    print(f"⚠️ 통합 호환성 검증기 로드 실패: {e}")
    COMPATIBILITY_VALIDATOR_AVAILABLE = False


class VariableDefinitions:
    """DB 기반 트레이딩 변수 정의 관리 클래스 - # O(1) 캐시 기반 접근"""
    
    # 클래스 레벨 캐시
    _variables_cache: Optional[Dict[str, Any]] = None
    _parameters_cache: Optional[Dict[str, Dict[str, Any]]] = None
    _category_cache: Optional[Dict[str, List[Tuple[str, str]]]] = None
    _placeholder_cache: Optional[Dict[str, Dict[str, str]]] = None
    _help_texts_cache: Optional[Dict[str, Dict[str, str]]] = None
    
    @classmethod
    def _get_db_connection(cls) -> sqlite3.Connection:
        """settings.sqlite3 DB 연결 # O(1) time, O(1) space"""
        try:
            # 여러 경로 시도 (프로젝트 루트에서 실행되는 경우 고려)
            possible_paths = [
                Path("data/settings.sqlite3"),  # 프로젝트 루트에서
                Path("data/settings.sqlite3"),                     # 하위 폴더에서
                Path("../../../data/settings.sqlite3"),           # 컴포넌트 폴더에서
            ]
            
            db_path = None
            for path in possible_paths:
                if path.exists():
                    db_path = path
                    break
            
            if db_path is None:
                raise FileNotFoundError(f"DB 파일을 찾을 수 없습니다. 시도한 경로: {[str(p) for p in possible_paths]}")
            
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row  # Dict-like 접근
            print(f"✅ DB 연결 성공: {db_path}")
            return conn
        except Exception as e:
            print(f"❌ DB 연결 실패: {e}")
            raise
    
    @classmethod
    def _load_variables_from_db(cls) -> Dict[str, Any]:
        """DB에서 모든 변수 정의 로드 및 캐싱 # O(n) time, O(n) space"""
        if cls._variables_cache is not None:
            return cls._variables_cache
        
        try:
            conn = cls._get_db_connection()
            cursor = conn.cursor()
            
            # 활성화된 변수들만 로드 (parameter_required 필드 추가)
            cursor.execute("""
                SELECT variable_id, display_name_ko, display_name_en, description, 
                       purpose_category, chart_category, comparison_group, is_active, parameter_required
                FROM tv_trading_variables 
                WHERE is_active = 1
                ORDER BY variable_id
            """)
            
            variables = {}
            for row in cursor.fetchall():
                variables[row["variable_id"]] = {
                    "id": row["variable_id"],
                    "name_ko": row["display_name_ko"],
                    "name_en": row["display_name_en"],
                    "description": row["description"],
                    "purpose_category": row["purpose_category"],
                    "chart_category": row["chart_category"], 
                    "comparison_group": row["comparison_group"],
                    "is_active": bool(row["is_active"]),
                    "parameter_required": bool(row["parameter_required"])
                }
            
            conn.close()
            cls._variables_cache = variables
            print(f"✅ DB에서 {len(variables)}개 변수 로드 완료")
            return variables
            
        except Exception as e:
            print(f"❌ DB 변수 로딩 실패: {e}")
            # 최소한의 폴백 - 사용자가 문제를 인지할 수 있도록
            return {
                "CURRENT_PRICE": {
                    "id": "CURRENT_PRICE",
                    "name_ko": "현재가 (DB 연결 실패)",
                    "description": "DB 연결 실패로 기본값 사용",
                    "purpose_category": "price",
                    "chart_category": "overlay",
                    "comparison_group": "price_comparable"
                }
            }
    
    @classmethod  
    def _load_parameters_from_db(cls) -> Dict[str, Dict[str, Any]]:
        """DB에서 모든 변수 파라미터 로드 및 캐싱 (플레이스홀더, 도움말 통합) # O(n*m) time, O(n*m) space"""
        if cls._parameters_cache is not None:
            return cls._parameters_cache
        
        try:
            conn = cls._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT vp.variable_id, vp.parameter_name, vp.parameter_type, 
                       vp.display_name_ko as label, vp.default_value, vp.min_value, vp.max_value,
                       vp.enum_values as options_json, vp.description as help_text, vp.is_required
                FROM tv_variable_parameters vp
                JOIN tv_trading_variables tv ON vp.variable_id = tv.variable_id
                WHERE tv.is_active = 1
                ORDER BY vp.variable_id, vp.parameter_name
            """)
            
            parameters = {}
            for row in cursor.fetchall():
                var_id = row["variable_id"]
                param_name = row["parameter_name"]
                
                if var_id not in parameters:
                    parameters[var_id] = {}
                
                # enum_values 파싱 (options_json 대신)
                options = []
                if row["options_json"]:
                    try:
                        options = json.loads(row["options_json"])
                    except json.JSONDecodeError:
                        # 콤마로 구분된 문자열인 경우
                        options = [opt.strip() for opt in row["options_json"].split(",")]
                
                param_type = row["parameter_type"]
                default_value = row["default_value"]
                min_value = row["min_value"]
                max_value = row["max_value"]

                # 타입에 따른 값 변환
                if param_type == 'integer':
                    if default_value is not None:
                        try:
                            default_value = int(default_value)
                        except (ValueError, TypeError):
                            pass
                    if min_value is not None:
                        try:
                            min_value = int(min_value)
                        except (ValueError, TypeError):
                            pass
                    if max_value is not None:
                        try:
                            max_value = int(max_value)
                        except (ValueError, TypeError):
                            pass
                elif param_type == 'float':
                    if default_value is not None:
                        try:
                            default_value = float(default_value)
                        except (ValueError, TypeError):
                            pass
                    if min_value is not None:
                        try:
                            min_value = float(min_value)
                        except (ValueError, TypeError):
                            pass
                    if max_value is not None:
                        try:
                            max_value = float(max_value)
                        except (ValueError, TypeError):
                            pass

                parameters[var_id][param_name] = {
                    "label": row["label"],
                    "type": param_type,
                    "default": default_value,
                    "min": min_value,
                    "max": max_value,
                    "step": None,  # step_value 컬럼이 없음
                    "options": options,
                    "help": row["help_text"],
                    "required": bool(row["is_required"])
                }
            
            conn.close()
            
            # 플레이스홀더와 도움말을 별도 테이블에서 로드하여 통합
            placeholders = cls._load_placeholder_texts_from_db()
            help_texts = cls._load_help_texts_from_db()
            
            # 파라미터 정보에 플레이스홀더와 상세 도움말 추가
            for var_id in parameters:
                for param_name in parameters[var_id]:
                    # 플레이스홀더 추가 (tv_placeholder_texts 테이블에서)
                    if var_id in placeholders and param_name in placeholders[var_id]:
                        parameters[var_id][param_name]["placeholder"] = placeholders[var_id][param_name]
                    else:
                        # 폴백 플레이스홀더
                        default_val = parameters[var_id][param_name].get("default", "")
                        parameters[var_id][param_name]["placeholder"] = f"예: {default_val}" if default_val else ""
                    
                    # 상세 도움말 추가 (tv_help_texts 테이블에서, 기존 help보다 우선)
                    if var_id in help_texts and param_name in help_texts[var_id]:
                        parameters[var_id][param_name]["help"] = help_texts[var_id][param_name]
            
            cls._parameters_cache = parameters
            print(f"✅ DB에서 {len(parameters)}개 변수의 파라미터 로드 완료 (플레이스홀더, 도움말 통합)")
            return parameters
            
        except Exception as e:
            print(f"❌ DB 파라미터 로딩 실패: {e}")
            # 최소한의 폴백
            return {"CURRENT_PRICE": {}}
    
    @classmethod
    def _load_placeholder_texts_from_db(cls) -> Dict[str, Dict[str, str]]:
        """DB에서 플레이스홀더 텍스트 로드 및 캐싱 # O(n) time, O(n) space"""
        if cls._placeholder_cache is not None:
            return cls._placeholder_cache
        
        try:
            conn = cls._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT variable_id, parameter_name, placeholder_text_ko
                FROM tv_placeholder_texts
                ORDER BY variable_id, parameter_name
            """)
            
            placeholders = {}
            for row in cursor.fetchall():
                var_id = row["variable_id"]
                param_name = row["parameter_name"]
                
                if var_id not in placeholders:
                    placeholders[var_id] = {}
                
                placeholders[var_id][param_name] = row["placeholder_text_ko"]
            
            conn.close()
            cls._placeholder_cache = placeholders
            print(f"✅ DB에서 {sum(len(params) for params in placeholders.values())}개 플레이스홀더 로드 완료")
            return placeholders
            
        except Exception as e:
            print(f"❌ DB 플레이스홀더 로딩 실패: {e}")
            return {}
    
    @classmethod
    def _load_help_texts_from_db(cls) -> Dict[str, Dict[str, str]]:
        """DB에서 도움말 텍스트 로드 및 캐싱 # O(n) time, O(n) space"""
        if cls._help_texts_cache is not None:
            return cls._help_texts_cache
        
        try:
            conn = cls._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT variable_id, parameter_name, help_text_ko
                FROM tv_help_texts
                ORDER BY variable_id, parameter_name
            """)
            
            help_texts = {}
            for row in cursor.fetchall():
                var_id = row["variable_id"]
                param_name = row["parameter_name"]
                
                if var_id not in help_texts:
                    help_texts[var_id] = {}
                
                help_texts[var_id][param_name] = row["help_text_ko"]
            
            conn.close()
            cls._help_texts_cache = help_texts
            print(f"✅ DB에서 {sum(len(params) for params in help_texts.values())}개 도움말 로드 완료")
            return help_texts
            
        except Exception as e:
            print(f"❌ DB 도움말 로딩 실패: {e}")
            return {}
    
    @classmethod
    def get_chart_category(cls, variable_id: str) -> str:
        """변수 ID의 차트 카테고리 반환 (overlay or subplot) # O(1) time"""
        variables = cls._load_variables_from_db()
        var_info = variables.get(variable_id, {})
        return var_info.get("chart_category", "subplot")
    
    @classmethod
    def is_overlay_indicator(cls, variable_id: str) -> bool:
        """오버레이 지표인지 확인 # O(1) time"""
        return cls.get_chart_category(variable_id) == "overlay"
    
    @classmethod
    def get_variable_parameters(cls, var_id: str) -> Dict[str, Any]:
        """변수별 파라미터 정의 반환 (DB 기반, 캐시 우선) # O(1) time"""
        parameters = cls._load_parameters_from_db()
        return parameters.get(var_id, {})
    
    @classmethod
    def is_parameter_required(cls, var_id: str) -> bool:
        """변수가 파라미터를 필요로 하는지 확인 # O(1) time"""
        variables = cls._load_variables_from_db()
        var_info = variables.get(var_id, {})
        return var_info.get("parameter_required", False)
    
    @classmethod
    def get_parameter_status_info(cls, var_id: str) -> Dict[str, str]:
        """변수의 파라미터 상태 정보 반환 (UI 표시용) # O(1) time"""
        is_required = cls.is_parameter_required(var_id)
        parameters = cls.get_variable_parameters(var_id)
        
        if not is_required:
            # 파라미터가 필요 없는 변수
            return {
                'message': '✅ 이 변수는 파라미터 설정이 필요하지 않습니다.',
                'color': '#2e7d32',  # 초록색
                'bg_color': '#e8f5e9',
                'border_color': '#4caf50',
                'font_weight': 'normal',
                'status_type': 'no_params_needed'
            }
        elif not parameters:
            # 파라미터가 필요하지만 DB에 정의되지 않은 경우 (오류 상황)
            return {
                'message': '⚠️ 파라미터 정의가 누락되었습니다. 관리자에게 문의하세요.',
                'color': '#d32f2f',  # 빨간색
                'bg_color': '#ffebee',
                'border_color': '#f44336',
                'font_weight': 'bold',
                'status_type': 'error_missing_params'
            }
        else:
            # 파라미터가 정상적으로 정의된 경우 (이 함수가 호출되지 않음)
            return {
                'message': '📋 파라미터가 정상적으로 로드되었습니다.',
                'color': '#1976d2',  # 파란색
                'bg_color': '#e3f2fd',
                'border_color': '#2196f3',
                'font_weight': 'normal',
                'status_type': 'normal'
            }
    
    @staticmethod
    def get_variable_descriptions() -> Dict[str, str]:
        """변수별 설명 반환 (DB 기반) # O(n) time"""
        variables = VariableDefinitions._load_variables_from_db()
        descriptions = {}
        
        for var_id, var_info in variables.items():
            descriptions[var_id] = var_info.get("description", f"{var_info.get('name_ko', var_id)} 설명")
        
        return descriptions
    
    @staticmethod
    def get_variable_placeholders() -> Dict[str, Dict[str, str]]:
        """변수별 플레이스홀더 반환 (기본값 제공) # O(1) time"""
        # 기본적인 플레이스홀더만 제공 (DB 확장 가능)
        return {
            "RSI": {
                "target": "예: 70 (과매수), 30 (과매도), 50 (중립)",
                "name": "예: RSI 과매수 신호",
                "description": "RSI가 70을 넘어 과매수 구간 진입 시 매도 신호"
            },
            "SMA": {
                "target": "예: 현재가 기준 또는 다른 SMA(골든크로스용)",
                "name": "예: 20일선 돌파",
                "description": "가격이 20일 이동평균선 상향 돌파 시 상승 추세 확인"
            },
            "CURRENT_PRICE": {
                "target": "예: 50000 (목표가), 비율: 1.05 (5%상승)",
                "name": "예: 목표가 도달",
                "description": "목표 가격 도달 시 수익 실현"
            }
        }
    
    @staticmethod
    def get_category_variables() -> Dict[str, List[Tuple[str, str]]]:
        """카테고리별 변수 목록 반환 (DB 기반) # O(n) time"""
        if VariableDefinitions._category_cache is not None:
            return VariableDefinitions._category_cache
        
        variables = VariableDefinitions._load_variables_from_db()
        categories = {}
        
        for var_id, var_info in variables.items():
            category = var_info.get("purpose_category", "custom")
            if category not in categories:
                categories[category] = []
            
            categories[category].append((var_id, var_info.get("name_ko", var_id)))
        
        VariableDefinitions._category_cache = categories
        return categories
    
    @staticmethod
    def get_variable_category(variable_id: str) -> str:
        """변수 ID로부터 카테고리 찾기 (DB 기반) # O(1) time"""
        variables = VariableDefinitions._load_variables_from_db()
        var_info = variables.get(variable_id, {})
        return var_info.get("purpose_category", "custom")
    
    @staticmethod
    def check_variable_compatibility(var1_id: str, var2_id: str) -> Tuple[bool, str]:
        """변수 간 호환성 검증 (통합 호환성 검증기 + DB 기반) # O(1) time"""
        try:
            # 통합 호환성 검증기 우선 사용
            if COMPATIBILITY_VALIDATOR_AVAILABLE:
                validator = CompatibilityValidator()
                is_compatible, score, reason = validator.validate_compatibility(var1_id, var2_id)
                reason_str = str(reason) if isinstance(reason, dict) else reason
                print(f"✅ 통합 호환성 검증: {var1_id} ↔ {var2_id} = {is_compatible} ({score}%) - {reason_str}")
                return is_compatible, reason_str
            else:
                # 폴백: DB 기반 comparison_group 검증
                variables = VariableDefinitions._load_variables_from_db()
                var1_info = variables.get(var1_id, {})
                var2_info = variables.get(var2_id, {})
                
                group1 = var1_info.get("comparison_group", "unknown")
                group2 = var2_info.get("comparison_group", "unknown")
                
                if group1 == group2 and group1 != "unknown":
                    return True, f"같은 비교그룹: {group1}"
                else:
                    return False, f"다른 비교그룹: {group1} vs {group2}"
            
        except Exception as e:
            print(f"⚠️ 호환성 검증 실패: {e}")
            # 최종 폴백 - 무조건 비호환으로 처리 (안전)
            return False, f"호환성 검증 오류: {str(e)}"
    
    @staticmethod
    def get_available_indicators() -> Dict[str, Any]:
        """사용 가능한 모든 지표 목록 반환 (DB 기반) # O(n) time"""
        variables = VariableDefinitions._load_variables_from_db()
        
        core_indicators = []
        custom_indicators = []
        
        for var_id, var_info in variables.items():
            if var_info.get("is_active", False):
                # purpose_category가 'custom'이면 사용자 정의로 분류
                if var_info.get("purpose_category") == "custom":
                    custom_indicators.append(var_id)
                else:
                    core_indicators.append(var_id)
        
        return {
            "core": core_indicators,
            "custom": custom_indicators,
            "total_count": len(core_indicators) + len(custom_indicators)
        }
    
    @classmethod
    def clear_cache(cls):
        """캐시 초기화 (테스트 및 새로고침용) # O(1) time"""
        cls._variables_cache = None
        cls._parameters_cache = None  
        cls._category_cache = None
        cls._placeholder_cache = None
        cls._help_texts_cache = None
        print("🔄 VariableDefinitions 캐시 초기화 완료 (플레이스홀더, 도움말 포함)")
    
    @classmethod
    def get_db_status(cls) -> Dict[str, Any]:
        """DB 연결 상태 및 통계 정보 반환 # O(n) time"""
        try:
            variables = cls._load_variables_from_db()
            parameters = cls._load_parameters_from_db()
            
            return {
                "db_connected": True,
                "variables_count": len(variables),
                "parameters_count": sum(len(params) for params in parameters.values()),
                "categories": list(set(var["purpose_category"] for var in variables.values())),
                "cache_status": {
                    "variables_cached": cls._variables_cache is not None,
                    "parameters_cached": cls._parameters_cache is not None,
                    "category_cached": cls._category_cache is not None
                }
            }
        except Exception as e:
            return {
                "db_connected": False,
                "error": str(e),
                "fallback_active": True
            }


# 모듈 로드 시 DB 상태 확인
if __name__ == "__main__":
    # 개발/테스트용 실행 코드
    print("=== DB 기반 VariableDefinitions 테스트 ===")
    
    status = VariableDefinitions.get_db_status()
    print(f"DB 상태: {status}")
    
    if status.get("db_connected"):
        variables = VariableDefinitions.get_category_variables()
        print(f"로드된 카테고리: {list(variables.keys())}")
        
        # RSI 파라미터 테스트
        rsi_params = VariableDefinitions.get_variable_parameters("RSI")
        print(f"RSI 파라미터: {list(rsi_params.keys())}")
    else:
        print("❌ DB 연결 실패 - 폴백 모드 사용")
