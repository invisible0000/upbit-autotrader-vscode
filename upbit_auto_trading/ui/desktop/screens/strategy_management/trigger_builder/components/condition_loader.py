#!/usr/bin/env python3
"""
조건 로더 - 저장된 조건을 불러와서 UI에 적용
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from .core.condition_storage import ConditionStorage
from .core.variable_definitions import VariableDefinitions

class ConditionLoader:
    """저장된 조건을 불러와서 사용하는 클래스"""
    
    def __init__(self, storage: Optional[ConditionStorage] = None):
        self.storage = storage or ConditionStorage()
        self.variable_definitions = VariableDefinitions()
    
    def load_condition_for_editing(self, condition_id: int) -> Optional[Dict[str, Any]]:
        """편집을 위해 조건 불러오기"""
        condition = self.storage.get_condition_by_id(condition_id)
        if not condition:
            return None
        
        # UI에서 사용할 형태로 변환
        ui_condition = {
            "id": condition["id"],
            "name": condition["name"],
            "description": condition["description"],
            "variable_id": condition["variable_id"],
            "variable_name": condition["variable_name"],
            "variable_params": condition["variable_params"],
            "operator": condition["operator"],
            "comparison_type": condition["comparison_type"],
            "target_value": condition["target_value"],
            "external_variable": condition["external_variable"],
            "trend_direction": condition["trend_direction"],
            "category": condition["category"]
        }
        
        return ui_condition
    
    def load_conditions_for_selection(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """선택을 위한 조건 목록 불러오기"""
        if category:
            conditions = self.storage.get_conditions_by_category(category)
        else:
            conditions = self.storage.get_all_conditions()
        
        # 선택 리스트에 표시할 정보만 추출
        selection_list = []
        for condition in conditions:
            selection_item = {
                "id": condition["id"],
                "name": condition["name"],
                "description": condition["description"],
                "variable_name": condition["variable_name"],
                "operator_display": self._get_operator_display(condition["operator"]),
                "target_display": self._get_target_display(condition),
                "category": condition["category"],
                "created_at": condition["created_at"],
                "usage_count": condition["usage_count"],
                "success_rate": condition["success_rate"]
            }
            selection_list.append(selection_item)
        
        return selection_list
    
    def load_condition_for_execution(self, condition_id: int) -> Optional[Dict[str, Any]]:
        """실행을 위해 조건 불러오기 (검증 포함)"""
        condition = self.storage.get_condition_by_id(condition_id)
        if not condition:
            return None
        
        # 조건 유효성 검사
        validation_result = self._validate_condition_for_execution(condition)
        if not validation_result["valid"]:
            return {
                "error": True,
                "message": validation_result["message"],
                "condition": condition
            }
        
        # 실행용 조건 데이터 구성
        execution_condition = {
            "id": condition["id"],
            "name": condition["name"],
            "variable_config": {
                "id": condition["variable_id"],
                "name": condition["variable_name"],
                "parameters": condition["variable_params"]
            },
            "comparison": {
                "operator": condition["operator"],
                "type": condition["comparison_type"],
                "target_value": condition["target_value"],
                "external_variable": condition["external_variable"]
            },
            "trend_direction": condition["trend_direction"],
            "metadata": {
                "category": condition["category"],
                "usage_count": condition["usage_count"],
                "success_rate": condition["success_rate"]
            }
        }
        
        return execution_condition
    
    def get_popular_conditions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """인기 조건 목록 (사용 빈도순)"""
        all_conditions = self.storage.get_all_conditions()
        
        # 사용 빈도순 정렬
        popular_conditions = sorted(
            all_conditions, 
            key=lambda x: (x["usage_count"], x["success_rate"]), 
            reverse=True
        )[:limit]
        
        return self.load_conditions_for_selection()[0:limit] if popular_conditions else []
    
    def get_recommended_conditions(self, variable_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """추천 조건 목록"""
        conditions = self.storage.get_all_conditions()
        
        # 변수별 필터링
        if variable_id:
            conditions = [c for c in conditions if c["variable_id"] == variable_id]
        
        # 성공률과 사용빈도 기반 추천
        recommended = []
        for condition in conditions:
            score = self._calculate_recommendation_score(condition)
            if score > 0.5:  # 임계값 이상만 추천
                condition["recommendation_score"] = score
                recommended.append(condition)
        
        # 추천 점수순 정렬
        recommended.sort(key=lambda x: x["recommendation_score"], reverse=True)
        
        return self.load_conditions_for_selection()[:len(recommended)]
    
    def clone_condition(self, condition_id: int, new_name: str) -> tuple[bool, str, Optional[int]]:
        """조건 복제"""
        original = self.storage.get_condition_by_id(condition_id)
        if not original:
            return False, "원본 조건을 찾을 수 없습니다.", None
        
        # 복제용 데이터 구성
        clone_data = {
            "name": new_name,
            "description": f"{original['description']} (복제본)",
            "variable_id": original["variable_id"],
            "variable_name": original["variable_name"],
            "variable_params": original["variable_params"],
            "operator": original["operator"],
            "comparison_type": original["comparison_type"],
            "target_value": original["target_value"],
            "external_variable": original["external_variable"],
            "trend_direction": original["trend_direction"],
            "category": original["category"]
        }
        
        return self.storage.save_condition(clone_data)
    
    def export_conditions(self, condition_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """조건 내보내기 (백업/공유용)"""
        if condition_ids:
            conditions = [self.storage.get_condition_by_id(cid) for cid in condition_ids]
            conditions = [c for c in conditions if c is not None]
        else:
            conditions = self.storage.get_all_conditions()
        
        export_data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "condition_count": len(conditions)
            },
            "conditions": conditions
        }
        
        return export_data
    
    def import_conditions(self, import_data: Dict[str, Any], 
                         overwrite: bool = False) -> Dict[str, Any]:
        """조건 가져오기"""
        results = {
            "success_count": 0,
            "error_count": 0,
            "skipped_count": 0,
            "errors": []
        }
        
        conditions = import_data.get("conditions", [])
        
        for condition in conditions:
            try:
                # 기존 조건 확인
                existing = self.storage.get_condition_by_name(condition["name"])
                
                if existing and not overwrite:
                    results["skipped_count"] += 1
                    continue
                
                # 필요한 필드만 추출
                import_condition = {
                    "name": condition["name"],
                    "description": condition.get("description", ""),
                    "variable_id": condition["variable_id"],
                    "variable_name": condition["variable_name"],
                    "variable_params": condition.get("variable_params", {}),
                    "operator": condition["operator"],
                    "comparison_type": condition.get("comparison_type", "fixed"),
                    "target_value": condition.get("target_value"),
                    "external_variable": condition.get("external_variable"),
                    "trend_direction": condition.get("trend_direction", "static"),
                    "category": condition.get("category", "imported")
                }
                
                if existing and overwrite:
                    success, message = self.storage.update_condition(
                        existing["id"], import_condition
                    )
                else:
                    success, message, _ = self.storage.save_condition(import_condition)
                
                if success:
                    results["success_count"] += 1
                else:
                    results["error_count"] += 1
                    results["errors"].append(f"{condition['name']}: {message}")
                    
            except Exception as e:
                results["error_count"] += 1
                results["errors"].append(f"{condition.get('name', 'Unknown')}: {str(e)}")
        
        return results
    
    def _get_operator_display(self, operator: str) -> str:
        """연산자 표시용 텍스트"""
        displays = {
            ">": "초과",
            ">=": "이상",
            "<": "미만",
            "<=": "이하",
            "~=": "근사값",
            "!=": "다름"
        }
        return displays.get(operator, operator)
    
    def _get_target_display(self, condition: Dict[str, Any]) -> str:
        """비교 대상 표시용 텍스트"""
        if condition["comparison_type"] == "external":
            external_var = condition["external_variable"]
            if external_var:
                return f"외부변수: {external_var.get('variable_name', 'Unknown')}"
            return "외부변수"
        else:
            return str(condition["target_value"] or "값")
    
    def _validate_condition_for_execution(self, condition: Dict[str, Any]) -> Dict[str, Any]:
        """실행용 조건 유효성 검사"""
        # 기본 필드 검사
        if not condition.get("variable_id"):
            return {"valid": False, "message": "변수 ID가 없습니다."}
        
        if not condition.get("operator"):
            return {"valid": False, "message": "연산자가 없습니다."}
        
        # 비교값 검사
        if condition["comparison_type"] == "fixed":
            if not condition.get("target_value"):
                return {"valid": False, "message": "비교값이 없습니다."}
        elif condition["comparison_type"] == "external":
            if not condition.get("external_variable"):
                return {"valid": False, "message": "외부 변수 정보가 없습니다."}
        
        # 파라미터 검사
        variable_params = self.variable_definitions.get_variable_parameters(
            condition["variable_id"]
        )
        condition_params = condition.get("variable_params", {})
        
        for param_name, param_config in variable_params.items():
            if param_name not in condition_params:
                return {
                    "valid": False, 
                    "message": f"필수 파라미터 '{param_name}'이 없습니다."
                }
        
        return {"valid": True, "message": "유효한 조건입니다."}
    
    def _calculate_recommendation_score(self, condition: Dict[str, Any]) -> float:
        """추천 점수 계산"""
        success_rate = condition.get("success_rate", 0.0)
        usage_count = condition.get("usage_count", 0)
        
        # 성공률 가중치: 70%
        success_score = success_rate * 0.7
        
        # 사용빈도 가중치: 30% (정규화된 값)
        usage_score = min(usage_count / 100.0, 1.0) * 0.3
        
        return success_score + usage_score
