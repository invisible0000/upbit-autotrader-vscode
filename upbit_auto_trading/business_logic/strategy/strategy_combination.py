"""
전략 조합 데이터 모델

역할 기반 전략 시스템을 위한 데이터 구조:
- StrategyCombination: 1개 진입 전략 + 0~N개 관리 전략 조합
- CombinationManager: 조합 생성, 저장, 로딩, 검증 관리
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import json
import uuid

class ConflictResolutionType(Enum):
    """충돌 해결 방식"""
    PRIORITY = "priority"        # 우선순위 기반
    CONSERVATIVE = "conservative"  # 보수적 접근 (청산 우선)
    MERGE = "merge"             # 신호 병합

class ExecutionOrderType(Enum):
    """실행 순서"""
    PARALLEL = "parallel"       # 병렬 실행
    SEQUENTIAL = "sequential"   # 순차 실행

@dataclass
class StrategyConfig:
    """개별 전략 설정"""
    strategy_id: str
    strategy_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    enabled: bool = True

@dataclass
class RiskLimit:
    """리스크 한계 설정"""
    max_position_size: float = 1.0      # 최대 포지션 크기 (배수)
    max_drawdown: float = 0.15          # 최대 드로우다운 (%)
    max_trades_per_day: int = 10        # 일일 최대 거래 수
    position_timeout_hours: int = 168   # 포지션 최대 보유 시간 (시간)

@dataclass
class StrategyCombination:
    """전략 조합 데이터 클래스"""
    combination_id: str
    name: str
    description: str
    
    # 필수: 진입 전략 (1개만)
    entry_strategy: StrategyConfig
    
    # 선택: 관리 전략 (0~N개)
    management_strategies: List[StrategyConfig] = field(default_factory=list)
    
    # 조합 설정
    execution_order: ExecutionOrderType = ExecutionOrderType.PARALLEL
    conflict_resolution: ConflictResolutionType = ConflictResolutionType.CONSERVATIVE
    risk_limit: RiskLimit = field(default_factory=RiskLimit)
    
    # 메타데이터
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    def __post_init__(self):
        """초기화 후 검증"""
        self.validate()
    
    def validate(self) -> None:
        """조합 유효성 검증"""
        if not self.entry_strategy:
            raise ValueError("진입 전략은 필수입니다")
        
        if len(self.management_strategies) > 5:
            raise ValueError("관리 전략은 최대 5개까지 허용됩니다")
        
        if not self.name.strip():
            raise ValueError("조합명은 필수입니다")
        
        # 관리 전략 우선순위 중복 확인
        priorities = [ms.priority for ms in self.management_strategies]
        if len(priorities) != len(set(priorities)):
            raise ValueError("관리 전략 우선순위는 중복될 수 없습니다")
    
    def get_summary(self) -> str:
        """조합 요약 정보"""
        mgmt_count = len(self.management_strategies)
        mgmt_names = [ms.strategy_name for ms in self.management_strategies]
        
        summary = f"{self.entry_strategy.strategy_name}"
        if mgmt_count > 0:
            summary += f" + {', '.join(mgmt_names)}"
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (JSON 직렬화용)"""
        return {
            "combination_id": self.combination_id,
            "name": self.name,
            "description": self.description,
            "entry_strategy": {
                "strategy_id": self.entry_strategy.strategy_id,
                "strategy_name": self.entry_strategy.strategy_name,
                "parameters": self.entry_strategy.parameters,
                "enabled": self.entry_strategy.enabled
            },
            "management_strategies": [
                {
                    "strategy_id": ms.strategy_id,
                    "strategy_name": ms.strategy_name,
                    "parameters": ms.parameters,
                    "priority": ms.priority,
                    "enabled": ms.enabled
                }
                for ms in self.management_strategies
            ],
            "execution_order": self.execution_order.value,
            "conflict_resolution": self.conflict_resolution.value,
            "risk_limit": {
                "max_position_size": self.risk_limit.max_position_size,
                "max_drawdown": self.risk_limit.max_drawdown,
                "max_trades_per_day": self.risk_limit.max_trades_per_day,
                "position_timeout_hours": self.risk_limit.position_timeout_hours
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyCombination':
        """딕셔너리에서 생성 (JSON 역직렬화용)"""
        # 진입 전략 복원
        entry_data = data["entry_strategy"]
        entry_strategy = StrategyConfig(
            strategy_id=entry_data["strategy_id"],
            strategy_name=entry_data["strategy_name"],
            parameters=entry_data.get("parameters", {}),
            enabled=entry_data.get("enabled", True)
        )
        
        # 관리 전략들 복원
        management_strategies = []
        for ms_data in data.get("management_strategies", []):
            ms = StrategyConfig(
                strategy_id=ms_data["strategy_id"],
                strategy_name=ms_data["strategy_name"],
                parameters=ms_data.get("parameters", {}),
                priority=ms_data.get("priority", 1),
                enabled=ms_data.get("enabled", True)
            )
            management_strategies.append(ms)
        
        # 리스크 한계 복원
        risk_data = data.get("risk_limit", {})
        risk_limit = RiskLimit(
            max_position_size=risk_data.get("max_position_size", 1.0),
            max_drawdown=risk_data.get("max_drawdown", 0.15),
            max_trades_per_day=risk_data.get("max_trades_per_day", 10),
            position_timeout_hours=risk_data.get("position_timeout_hours", 168)
        )
        
        return cls(
            combination_id=data["combination_id"],
            name=data["name"],
            description=data["description"],
            entry_strategy=entry_strategy,
            management_strategies=management_strategies,
            execution_order=ExecutionOrderType(data.get("execution_order", "parallel")),
            conflict_resolution=ConflictResolutionType(data.get("conflict_resolution", "conservative")),
            risk_limit=risk_limit,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            is_active=data.get("is_active", True)
        )

class CombinationManager:
    """전략 조합 관리 클래스"""
    
    def __init__(self, storage_path: str = "strategy_combinations.json"):
        self.storage_path = storage_path
        self.combinations: Dict[str, StrategyCombination] = {}
        self.load_combinations()
    
    def create_combination(self, name: str, description: str,
                          entry_strategy: StrategyConfig,
                          management_strategies: Optional[List[StrategyConfig]] = None) -> StrategyCombination:
        """새 전략 조합 생성"""
        combination_id = str(uuid.uuid4())
        
        combination = StrategyCombination(
            combination_id=combination_id,
            name=name,
            description=description,
            entry_strategy=entry_strategy,
            management_strategies=management_strategies or []
        )
        
        self.combinations[combination_id] = combination
        self.save_combinations()
        
        return combination
    
    def get_combination(self, combination_id: str) -> Optional[StrategyCombination]:
        """조합 조회"""
        return self.combinations.get(combination_id)
    
    def get_all_combinations(self) -> List[StrategyCombination]:
        """모든 조합 조회"""
        return list(self.combinations.values())
    
    def get_active_combinations(self) -> List[StrategyCombination]:
        """활성 조합만 조회"""
        return [combo for combo in self.combinations.values() if combo.is_active]
    
    def update_combination(self, combination: StrategyCombination) -> None:
        """조합 업데이트"""
        combination.updated_at = datetime.now()
        combination.validate()
        
        self.combinations[combination.combination_id] = combination
        self.save_combinations()
    
    def delete_combination(self, combination_id: str) -> bool:
        """조합 삭제"""
        if combination_id in self.combinations:
            del self.combinations[combination_id]
            self.save_combinations()
            return True
        return False
    
    def deactivate_combination(self, combination_id: str) -> bool:
        """조합 비활성화"""
        if combination_id in self.combinations:
            self.combinations[combination_id].is_active = False
            self.combinations[combination_id].updated_at = datetime.now()
            self.save_combinations()
            return True
        return False
    
    def save_combinations(self) -> None:
        """조합 데이터 저장"""
        try:
            data = {
                "version": "1.0",
                "combinations": [combo.to_dict() for combo in self.combinations.values()]
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"❌ 전략 조합 저장 실패: {e}")
    
    def load_combinations(self) -> None:
        """조합 데이터 로딩"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.combinations = {}
            for combo_data in data.get("combinations", []):
                combo = StrategyCombination.from_dict(combo_data)
                self.combinations[combo.combination_id] = combo
                
            print(f"✅ 전략 조합 {len(self.combinations)}개 로딩 완료")
            
        except FileNotFoundError:
            print("💡 전략 조합 파일이 없어 새로 생성합니다")
            self.combinations = {}
            
        except Exception as e:
            print(f"❌ 전략 조합 로딩 실패: {e}")
            self.combinations = {}
    
    def get_sample_combinations(self) -> List[StrategyCombination]:
        """샘플 조합 생성 (테스트/데모용)"""
        # 진입 전략들
        rsi_entry = StrategyConfig("rsi_entry", "RSI 과매수/과매도", {"rsi_period": 14, "oversold": 30, "overbought": 70})
        ma_cross_entry = StrategyConfig("ma_cross_entry", "이동평균 교차", {"short_period": 5, "long_period": 20})
        volatility_entry = StrategyConfig("volatility_entry", "변동성 돌파", {"lookback_period": 1, "k_value": 0.5})
        
        # 관리 전략들
        averaging_down = StrategyConfig("averaging_down", "물타기", {"trigger_drop_percent": 5.0, "max_buys": 2}, priority=1)
        trailing_stop = StrategyConfig("trailing_stop", "트레일링 스탑", {"trailing_distance": 3.0}, priority=2)
        pyramiding = StrategyConfig("pyramiding", "불타기", {"trigger_rise_percent": 3.0, "max_buys": 2}, priority=1)
        fixed_target = StrategyConfig("fixed_target", "고정 익절/손절", {"profit_target": 10.0, "stop_loss": 5.0}, priority=3)
        time_based = StrategyConfig("time_based", "시간 청산", {"max_holding_hours": 24}, priority=2)
        
        sample_combinations = [
            StrategyCombination(
                combination_id="sample_1",
                name="RSI + 물타기 + 트레일링",
                description="RSI 과매도 진입 후 물타기와 트레일링 스탑으로 관리",
                entry_strategy=rsi_entry,
                management_strategies=[averaging_down, trailing_stop]
            ),
            StrategyCombination(
                combination_id="sample_2", 
                name="이평교차 + 불타기 + 고정익절",
                description="이동평균 교차 진입 후 불타기와 고정 익절/손절로 관리",
                entry_strategy=ma_cross_entry,
                management_strategies=[pyramiding, fixed_target]
            ),
            StrategyCombination(
                combination_id="sample_3",
                name="변동성 돌파 + 시간청산",
                description="변동성 돌파 진입 후 시간 기반 강제 청산",
                entry_strategy=volatility_entry,
                management_strategies=[time_based]
            )
        ]
        
        return sample_combinations

# 사용 예시 및 테스트
if __name__ == "__main__":
    # 조합 매니저 생성
    manager = CombinationManager("test_combinations.json")
    
    # 샘플 조합 생성
    samples = manager.get_sample_combinations()
    
    for combo in samples:
        print(f"\n📊 {combo.name}")
        print(f"   설명: {combo.description}")
        print(f"   구성: {combo.get_summary()}")
        print(f"   진입: {combo.entry_strategy.strategy_name}")
        print(f"   관리: {len(combo.management_strategies)}개")
        print(f"   충돌해결: {combo.conflict_resolution.value}")
        
        # 조합 저장 테스트
        manager.combinations[combo.combination_id] = combo
    
    manager.save_combinations()
    print(f"\n✅ {len(samples)}개 샘플 조합 생성 완료")
