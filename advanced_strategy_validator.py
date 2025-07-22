"""
고급 전략 검증 시스템
Advanced Strategy Validation System

전략의 논리적 완성도, 충돌 감지, 포지션 생명주기 검증
"""

from typing import Dict, List, Any, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import json

class ValidationLevel(Enum):
    """검증 수준"""
    WARNING = "warning"    # 경고 (실행 가능하지만 권장하지 않음)
    ERROR = "error"       # 오류 (실행 불가능)
    CRITICAL = "critical" # 치명적 (시스템 위험)

class ValidationCategory(Enum):
    """검증 카테고리"""
    COMPLETENESS = "completeness"      # 완성도 검증
    LOGICAL_CONFLICT = "logical_conflict"  # 논리적 충돌
    POSITION_LIFECYCLE = "position_lifecycle"  # 포지션 생명주기
    RISK_MANAGEMENT = "risk_management"    # 리스크 관리
    PERFORMANCE = "performance"        # 성능/효율성

@dataclass
class ValidationIssue:
    """검증 이슈"""
    level: ValidationLevel
    category: ValidationCategory
    rule_ids: List[str]
    component_ids: List[str]
    message: str
    suggestion: str
    auto_fixable: bool = False

@dataclass
class ValidationResult:
    """검증 결과"""
    is_valid: bool
    is_complete: bool
    is_executable: bool
    confidence_score: float  # 0-100, 전략 신뢰도
    issues: List[ValidationIssue]
    
    def get_issues_by_level(self, level: ValidationLevel) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.level == level]
    
    def get_critical_issues(self) -> List[ValidationIssue]:
        return self.get_issues_by_level(ValidationLevel.CRITICAL)
    
    def get_error_issues(self) -> List[ValidationIssue]:
        return self.get_issues_by_level(ValidationLevel.ERROR)
    
    def get_warning_issues(self) -> List[ValidationIssue]:
        return self.get_issues_by_level(ValidationLevel.WARNING)

class StrategyValidator:
    """고급 전략 검증기"""
    
    def __init__(self):
        self.component_registry = self._initialize_component_registry()
        self.validation_rules = self._initialize_validation_rules()
    
    def _initialize_component_registry(self) -> Dict[str, Dict[str, Any]]:
        """컴포넌트 레지스트리 초기화"""
        return {
            # 트리거 컴포넌트
            "RSITrigger": {
                "type": "trigger",
                "category": "technical_indicator", 
                "indicators_used": ["RSI"],
                "position_requirements": [],
                "conflicts_with": [],
                "typical_thresholds": {"oversold": 30, "overbought": 70}
            },
            "PriceChangeTrigger": {
                "type": "trigger",
                "category": "price_action",
                "indicators_used": ["PRICE"],
                "position_requirements": ["ACTIVE"],  # 포지션이 있어야 함
                "conflicts_with": []
            },
            "ProfitLossTrigger": {
                "type": "trigger", 
                "category": "pnl",
                "indicators_used": ["PNL"],
                "position_requirements": ["ACTIVE"],
                "conflicts_with": []
            },
            
            # 액션 컴포넌트
            "BuyAction": {
                "type": "action",
                "category": "entry",
                "position_effect": "OPEN_LONG",
                "requires_cash": True,
                "conflicts_with": ["SellAction"]
            },
            "SellAction": {
                "type": "action", 
                "category": "exit",
                "position_effect": "CLOSE_LONG",
                "requires_position": True,
                "conflicts_with": ["BuyAction"]
            },
            "AddPositionAction": {
                "type": "action",
                "category": "scale_in", 
                "position_effect": "ADD_LONG",
                "requires_cash": True,
                "requires_position": True,
                "conflicts_with": []
            },
            
            # 조건 컴포넌트
            "BalanceCondition": {
                "type": "condition",
                "category": "risk_management",
                "checks": ["available_cash"],
                "conflicts_with": []
            },
            "ExecutionCountCondition": {
                "type": "condition",
                "category": "execution_control", 
                "checks": ["execution_history"],
                "conflicts_with": []
            },
            "PositionSizeCondition": {
                "type": "condition",
                "category": "risk_management",
                "checks": ["position_size"],
                "conflicts_with": []
            }
        }
    
    def _initialize_validation_rules(self) -> List[callable]:
        """검증 규칙 초기화"""
        return [
            self._validate_strategy_completeness,
            self._validate_position_lifecycle,
            self._validate_logical_conflicts,
            self._validate_indicator_conflicts,
            self._validate_risk_management,
            self._validate_execution_feasibility
        ]
    
    def validate_strategy(self, strategy_data: Dict[str, Any]) -> ValidationResult:
        """전략 종합 검증"""
        issues = []
        
        # 모든 검증 규칙 실행
        for validation_rule in self.validation_rules:
            rule_issues = validation_rule(strategy_data)
            issues.extend(rule_issues)
        
        # 검증 결과 계산
        critical_count = len([i for i in issues if i.level == ValidationLevel.CRITICAL])
        error_count = len([i for i in issues if i.level == ValidationLevel.ERROR]) 
        warning_count = len([i for i in issues if i.level == ValidationLevel.WARNING])
        
        is_valid = critical_count == 0 and error_count == 0
        is_complete = self._check_completeness(strategy_data, issues)
        is_executable = is_valid and is_complete
        
        # 신뢰도 점수 계산 (0-100)
        confidence_score = max(0, 100 - (critical_count * 50) - (error_count * 20) - (warning_count * 5))
        
        return ValidationResult(
            is_valid=is_valid,
            is_complete=is_complete, 
            is_executable=is_executable,
            confidence_score=confidence_score,
            issues=issues
        )
    
    def _validate_strategy_completeness(self, strategy_data: Dict[str, Any]) -> List[ValidationIssue]:
        """전략 완성도 검증"""
        issues = []
        rules = strategy_data.get("rules", [])
        
        if not rules:
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                category=ValidationCategory.COMPLETENESS,
                rule_ids=[],
                component_ids=[],
                message="전략에 규칙이 없습니다",
                suggestion="최소 1개 이상의 규칙을 추가하세요"
            ))
            return issues
        
        # 진입점 확인
        entry_rules = self._find_rules_by_position_effect(rules, ["OPEN_LONG", "OPEN_SHORT"])
        if not entry_rules:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category=ValidationCategory.COMPLETENESS,
                rule_ids=[],
                component_ids=[],
                message="포지션 진입 규칙이 없습니다",
                suggestion="매수(BuyAction) 규칙을 추가하여 포지션 진입점을 만드세요",
                auto_fixable=True
            ))
        
        # 청산점 확인  
        exit_rules = self._find_rules_by_position_effect(rules, ["CLOSE_LONG", "CLOSE_SHORT"])
        if not exit_rules:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category=ValidationCategory.COMPLETENESS,
                rule_ids=[],
                component_ids=[], 
                message="포지션 청산 규칙이 없습니다",
                suggestion="매도(SellAction) 또는 트레일링 스탑 규칙을 추가하여 수익 실현/손실 제한점을 만드세요",
                auto_fixable=True
            ))
        
        return issues
    
    def _validate_position_lifecycle(self, strategy_data: Dict[str, Any]) -> List[ValidationIssue]:
        """포지션 생명주기 검증"""
        issues = []
        rules = strategy_data.get("rules", [])
        
        # 포지션 상태별 규칙 분류
        ready_rules = [r for r in rules if r.get("activation_state") == "READY"]
        active_rules = [r for r in rules if r.get("activation_state") == "ACTIVE"]
        
        # READY 상태에서 ACTIVE 전환 가능성 확인
        if ready_rules:
            can_transition = any(self._rule_can_open_position(rule) for rule in ready_rules)
            if not can_transition:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category=ValidationCategory.POSITION_LIFECYCLE,
                    rule_ids=[r.get("rule_id", "") for r in ready_rules],
                    component_ids=[],
                    message="READY 상태에서 포지션을 열 수 있는 규칙이 없습니다",
                    suggestion="READY 상태 규칙 중 하나에 매수 액션을 추가하세요"
                ))
        
        # ACTIVE 상태에서 종료 가능성 확인
        if active_rules:
            can_close = any(self._rule_can_close_position(rule) for rule in active_rules)
            if not can_close:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category=ValidationCategory.POSITION_LIFECYCLE,
                    rule_ids=[r.get("rule_id", "") for r in active_rules],
                    component_ids=[],
                    message="ACTIVE 상태에서 포지션을 닫을 수 있는 규칙이 없습니다",
                    suggestion="ACTIVE 상태 규칙 중 하나에 매도 액션을 추가하세요"
                ))
        
        return issues
    
    def _validate_logical_conflicts(self, strategy_data: Dict[str, Any]) -> List[ValidationIssue]:
        """논리적 충돌 검증"""
        issues = []
        rules = strategy_data.get("rules", [])
        
        # 같은 활성화 상태의 규칙들 간 충돌 검사
        for state in ["READY", "ACTIVE"]:
            state_rules = [r for r in rules if r.get("activation_state") == state]
            
            # 동시 실행 가능한 규칙들 간의 액션 충돌
            for i, rule1 in enumerate(state_rules):
                for rule2 in state_rules[i+1:]:
                    conflict = self._check_rule_conflict(rule1, rule2)
                    if conflict:
                        issues.append(ValidationIssue(
                            level=ValidationLevel.WARNING,
                            category=ValidationCategory.LOGICAL_CONFLICT,
                            rule_ids=[rule1.get("rule_id", ""), rule2.get("rule_id", "")],
                            component_ids=[],
                            message=f"규칙 간 논리적 충돌: {conflict}",
                            suggestion="우선순위를 다르게 설정하거나 조건을 조정하세요"
                        ))
        
        return issues
    
    def _validate_indicator_conflicts(self, strategy_data: Dict[str, Any]) -> List[ValidationIssue]:
        """지표 기반 충돌 검증"""
        issues = []
        rules = strategy_data.get("rules", [])
        
        # 같은 지표를 사용하는 규칙들 찾기
        indicator_groups = self._group_rules_by_indicator(rules)
        
        for indicator, rules_using_indicator in indicator_groups.items():
            if len(rules_using_indicator) > 1:
                # 같은 지표의 상반된 조건 검사
                conflicts = self._find_indicator_conflicts(rules_using_indicator, indicator)
                for conflict_info in conflicts:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category=ValidationCategory.LOGICAL_CONFLICT,
                        rule_ids=conflict_info["rule_ids"],
                        component_ids=conflict_info["component_ids"],
                        message=f"{indicator} 지표에서 상반된 조건 감지: {conflict_info['description']}",
                        suggestion=conflict_info["suggestion"]
                    ))
        
        return issues
    
    def _validate_risk_management(self, strategy_data: Dict[str, Any]) -> List[ValidationIssue]:
        """리스크 관리 검증"""
        issues = []
        rules = strategy_data.get("rules", [])
        
        # 급락/급등 대응 규칙 확인
        has_emergency_exit = any(self._is_emergency_rule(rule) for rule in rules)
        if not has_emergency_exit:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category=ValidationCategory.RISK_MANAGEMENT,
                rule_ids=[],
                component_ids=[],
                message="급락/긴급 청산 규칙이 없습니다",
                suggestion="손실 제한을 위한 급락 감지 또는 스탑로스 규칙을 추가하는 것을 권장합니다"
            ))
        
        # 자금 관리 조건 확인
        has_balance_check = any(self._has_balance_condition(rule) for rule in rules)
        if not has_balance_check:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category=ValidationCategory.RISK_MANAGEMENT,
                rule_ids=[],
                component_ids=[],
                message="잔고 확인 조건이 없습니다", 
                suggestion="매수 규칙에 잔고 확인 조건을 추가하여 과도한 투자를 방지하세요"
            ))
        
        return issues
    
    def _validate_execution_feasibility(self, strategy_data: Dict[str, Any]) -> List[ValidationIssue]:
        """실행 가능성 검증"""
        issues = []
        rules = strategy_data.get("rules", [])
        
        # 규칙별 실행 가능성 검사
        for rule in rules:
            rule_id = rule.get("rule_id", "unknown")
            
            # 트리거 실행 가능성
            trigger_issues = self._validate_trigger_feasibility(rule)
            issues.extend(trigger_issues)
            
            # 액션 실행 가능성  
            action_issues = self._validate_action_feasibility(rule)
            issues.extend(action_issues)
            
            # 조건 실행 가능성
            condition_issues = self._validate_conditions_feasibility(rule)
            issues.extend(condition_issues)
        
        return issues
    
    # === 헬퍼 메서드들 ===
    
    def _find_rules_by_position_effect(self, rules: List[Dict], effects: List[str]) -> List[Dict]:
        """특정 포지션 효과를 가진 규칙들 찾기"""
        result = []
        for rule in rules:
            action = rule.get("action", {})
            component_name = action.get("component_name", "")
            if component_name in self.component_registry:
                comp_info = self.component_registry[component_name]
                if comp_info.get("position_effect") in effects:
                    result.append(rule)
        return result
    
    def _rule_can_open_position(self, rule: Dict) -> bool:
        """규칙이 포지션을 열 수 있는지 확인"""
        action = rule.get("action", {})
        component_name = action.get("component_name", "")
        if component_name in self.component_registry:
            comp_info = self.component_registry[component_name]
            return comp_info.get("position_effect") in ["OPEN_LONG", "OPEN_SHORT"]
        return False
    
    def _rule_can_close_position(self, rule: Dict) -> bool:
        """규칙이 포지션을 닫을 수 있는지 확인"""
        action = rule.get("action", {})
        component_name = action.get("component_name", "")
        if component_name in self.component_registry:
            comp_info = self.component_registry[component_name]
            return comp_info.get("position_effect") in ["CLOSE_LONG", "CLOSE_SHORT"]
        return False
    
    def _check_rule_conflict(self, rule1: Dict, rule2: Dict) -> Optional[str]:
        """두 규칙 간 충돌 검사"""
        # 액션 충돌 검사
        action1 = rule1.get("action", {}).get("component_name", "")
        action2 = rule2.get("action", {}).get("component_name", "")
        
        if action1 in self.component_registry and action2 in self.component_registry:
            conflicts1 = self.component_registry[action1].get("conflicts_with", [])
            if action2 in conflicts1:
                return f"{action1}과 {action2}는 동시 실행 불가"
        
        return None
    
    def _group_rules_by_indicator(self, rules: List[Dict]) -> Dict[str, List[Dict]]:
        """지표별로 규칙 그룹화"""
        groups = {}
        for rule in rules:
            trigger = rule.get("trigger", {})
            component_name = trigger.get("component_name", "")
            if component_name in self.component_registry:
                indicators = self.component_registry[component_name].get("indicators_used", [])
                for indicator in indicators:
                    if indicator not in groups:
                        groups[indicator] = []
                    groups[indicator].append(rule)
        return groups
    
    def _find_indicator_conflicts(self, rules: List[Dict], indicator: str) -> List[Dict]:
        """특정 지표에서의 충돌 찾기"""
        conflicts = []
        
        if indicator == "RSI":
            # RSI 임계값 충돌 검사
            rsi_rules = []
            for rule in rules:
                trigger = rule.get("trigger", {})
                config = trigger.get("config", {})
                if "threshold" in config and "direction" in config:
                    rsi_rules.append({
                        "rule": rule,
                        "threshold": config["threshold"],
                        "direction": config["direction"]
                    })
            
            # 같은 방향의 중복 임계값 검사
            for i, rsi1 in enumerate(rsi_rules):
                for rsi2 in rsi_rules[i+1:]:
                    if rsi1["direction"] == rsi2["direction"]:
                        if abs(rsi1["threshold"] - rsi2["threshold"]) < 5:
                            conflicts.append({
                                "rule_ids": [rsi1["rule"].get("rule_id", ""), rsi2["rule"].get("rule_id", "")],
                                "component_ids": [],
                                "description": f"유사한 RSI 임계값 ({rsi1['threshold']}, {rsi2['threshold']})",
                                "suggestion": "임계값 차이를 5 이상으로 조정하거나 규칙을 통합하세요"
                            })
        
        return conflicts
    
    def _is_emergency_rule(self, rule: Dict) -> bool:
        """긴급 규칙 여부 확인"""
        trigger = rule.get("trigger", {})
        component_name = trigger.get("component_name", "")
        return "Crash" in component_name or "Emergency" in component_name or rule.get("priority", 10) == 0
    
    def _has_balance_condition(self, rule: Dict) -> bool:
        """잔고 확인 조건 보유 여부"""
        conditions = rule.get("conditions", [])
        for condition in conditions:
            component_name = condition.get("component_name", "")
            if component_name == "BalanceCondition":
                return True
        return False
    
    def _validate_trigger_feasibility(self, rule: Dict) -> List[ValidationIssue]:
        """트리거 실행 가능성 검증"""
        issues = []
        trigger = rule.get("trigger", {})
        component_name = trigger.get("component_name", "")
        config = trigger.get("config", {})
        rule_id = rule.get("rule_id", "")
        
        if component_name in self.component_registry:
            comp_info = self.component_registry[component_name]
            
            # 포지션 요구사항 검사
            position_reqs = comp_info.get("position_requirements", [])
            activation_state = rule.get("activation_state", "")
            
            if "ACTIVE" in position_reqs and activation_state == "READY":
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category=ValidationCategory.POSITION_LIFECYCLE,
                    rule_ids=[rule_id],
                    component_ids=[component_name],
                    message=f"{component_name}는 활성 포지션이 필요하지만 READY 상태에서 실행됩니다",
                    suggestion="activation_state를 ACTIVE로 변경하거나 다른 트리거를 사용하세요"
                ))
        
        return issues
    
    def _validate_action_feasibility(self, rule: Dict) -> List[ValidationIssue]:
        """액션 실행 가능성 검증"""
        issues = []
        action = rule.get("action", {})
        component_name = action.get("component_name", "")
        config = action.get("config", {})
        rule_id = rule.get("rule_id", "")
        
        if component_name in self.component_registry:
            comp_info = self.component_registry[component_name]
            
            # 현금 요구사항 검사
            if comp_info.get("requires_cash", False):
                # 잔고 확인 조건이 있는지 검사
                if not self._has_balance_condition(rule):
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category=ValidationCategory.RISK_MANAGEMENT,
                        rule_ids=[rule_id],
                        component_ids=[component_name],
                        message=f"{component_name}는 현금이 필요하지만 잔고 확인 조건이 없습니다",
                        suggestion="BalanceCondition을 추가하여 충분한 잔고가 있을 때만 실행되도록 하세요"
                    ))
            
            # 포지션 요구사항 검사
            if comp_info.get("requires_position", False):
                activation_state = rule.get("activation_state", "")
                if activation_state == "READY":
                    issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        category=ValidationCategory.POSITION_LIFECYCLE,
                        rule_ids=[rule_id],
                        component_ids=[component_name],
                        message=f"{component_name}는 기존 포지션이 필요하지만 READY 상태에서 실행됩니다",
                        suggestion="activation_state를 ACTIVE로 변경하세요"
                    ))
        
        return issues
    
    def _validate_conditions_feasibility(self, rule: Dict) -> List[ValidationIssue]:
        """조건 실행 가능성 검증"""
        issues = []
        conditions = rule.get("conditions", [])
        rule_id = rule.get("rule_id", "")
        
        for condition in conditions:
            component_name = condition.get("component_name", "")
            config = condition.get("config", {})
            
            # ExecutionCountCondition 검증
            if component_name == "ExecutionCountCondition":
                target_rule_id = config.get("target_rule_id")
                if not target_rule_id:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        category=ValidationCategory.COMPLETENESS,
                        rule_ids=[rule_id],
                        component_ids=[component_name],
                        message="ExecutionCountCondition에 target_rule_id가 지정되지 않았습니다",
                        suggestion="실행 횟수를 추적할 대상 규칙 ID를 지정하세요"
                    ))
        
        return issues
    
    def _check_completeness(self, strategy_data: Dict[str, Any], issues: List[ValidationIssue]) -> bool:
        """완성도 확인"""
        completeness_issues = [i for i in issues if i.category == ValidationCategory.COMPLETENESS]
        error_completeness_issues = [i for i in completeness_issues if i.level == ValidationLevel.ERROR]
        return len(error_completeness_issues) == 0


# 사용 예시 및 테스트
def test_strategy_validation():
    """전략 검증 테스트"""
    
    # 불완전한 전략 (진입점만 있고 청산점 없음)
    incomplete_strategy = {
        "strategy_id": "test_incomplete",
        "strategy_name": "불완전한 전략",
        "rules": [
            {
                "rule_id": "rsi_entry",
                "activation_state": "READY",
                "priority": 10,
                "trigger": {
                    "component_name": "RSITrigger",
                    "config": {"threshold": 30, "direction": "below", "period": 14}
                },
                "conditions": [],
                "action": {
                    "component_name": "BuyAction", 
                    "config": {"amount_percent": 10}
                }
            }
        ]
    }
    
    # 충돌이 있는 전략 (같은 RSI로 상반된 액션)
    conflicting_strategy = {
        "strategy_id": "test_conflict",
        "strategy_name": "충돌 전략",
        "rules": [
            {
                "rule_id": "rsi_buy",
                "activation_state": "READY",
                "priority": 10,
                "trigger": {
                    "component_name": "RSITrigger",
                    "config": {"threshold": 30, "direction": "below", "period": 14}
                },
                "conditions": [],
                "action": {
                    "component_name": "BuyAction",
                    "config": {"amount_percent": 10}
                }
            },
            {
                "rule_id": "rsi_sell", 
                "activation_state": "ACTIVE",
                "priority": 10,
                "trigger": {
                    "component_name": "RSITrigger",
                    "config": {"threshold": 32, "direction": "below", "period": 14}  # 유사한 임계값
                },
                "conditions": [],
                "action": {
                    "component_name": "SellAction",
                    "config": {}
                }
            }
        ]
    }
    
    validator = StrategyValidator()
    
    print("=== 불완전한 전략 검증 ===")
    result1 = validator.validate_strategy(incomplete_strategy)
    print(f"실행 가능: {result1.is_executable}")
    print(f"신뢰도: {result1.confidence_score}%")
    for issue in result1.issues:
        print(f"[{issue.level.value.upper()}] {issue.message}")
        print(f"  → {issue.suggestion}")
    
    print("\n=== 충돌 전략 검증 ===")
    result2 = validator.validate_strategy(conflicting_strategy)
    print(f"실행 가능: {result2.is_executable}")
    print(f"신뢰도: {result2.confidence_score}%")
    for issue in result2.issues:
        print(f"[{issue.level.value.upper()}] {issue.message}")
        print(f"  → {issue.suggestion}")

if __name__ == "__main__":
    test_strategy_validation()
