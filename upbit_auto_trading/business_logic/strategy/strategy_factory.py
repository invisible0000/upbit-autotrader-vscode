"""
전략 팩토리 모듈

이 모듈은 전략 객체를 생성하고 관리하는 팩토리 클래스를 제공합니다.
"""
from typing import Dict, Any, List, Type, Optional
import importlib
import inspect
import logging

from upbit_auto_trading.business_logic.strategy.strategy_interface import StrategyInterface
from upbit_auto_trading.business_logic.strategy.base_strategy import BaseStrategy


class StrategyFactory:
    """
    전략 팩토리 클래스
    
    전략 클래스를 등록하고 인스턴스를 생성합니다.
    """
    
    def __init__(self):
        """
        전략 팩토리 초기화
        """
        self.logger = logging.getLogger(__name__)
        self.strategy_classes: Dict[str, Type[StrategyInterface]] = {}
    
    def register_strategy(self, strategy_id: str, strategy_class: Type[StrategyInterface]) -> bool:
        """
        전략 클래스 등록
        
        Args:
            strategy_id: 전략 ID
            strategy_class: 전략 클래스
            
        Returns:
            등록 성공 여부
        """
        if not issubclass(strategy_class, StrategyInterface):
            self.logger.error(f"전략 클래스 {strategy_class.__name__}가 StrategyInterface를 구현하지 않았습니다.")
            return False
        
        self.strategy_classes[strategy_id] = strategy_class
        self.logger.info(f"전략 '{strategy_id}' 등록 완료")
        return True
    
    def create_strategy(self, strategy_id: str, parameters: Optional[Dict[str, Any]] = None) -> Optional[StrategyInterface]:
        """
        전략 인스턴스 생성
        
        Args:
            strategy_id: 전략 ID
            parameters: 전략 매개변수 (None인 경우 기본값 사용)
            
        Returns:
            전략 인스턴스 또는 None (실패 시)
        """
        if strategy_id not in self.strategy_classes:
            self.logger.error(f"전략 ID '{strategy_id}'가 등록되지 않았습니다.")
            return None
        
        strategy_class = self.strategy_classes[strategy_id]
        
        try:
            # 매개변수가 제공되지 않은 경우 기본값 사용
            if parameters is None:
                # 정적 메서드를 통해 기본 매개변수 가져오기 시도
                if hasattr(strategy_class, 'get_default_parameters_static') and callable(getattr(strategy_class, 'get_default_parameters_static')):
                    parameters = strategy_class.get_default_parameters_static()
                else:
                    # 임시 인스턴스를 생성하여 기본 매개변수 가져오기
                    # 임시 인스턴스 생성을 위한 빈 매개변수 딕셔너리
                    empty_params = {}
                    temp_instance = strategy_class(empty_params)
                    parameters = temp_instance.get_default_parameters()
            
            # 전략 인스턴스 생성
            strategy = strategy_class(parameters)
            return strategy
        
        except Exception as e:
            self.logger.error(f"전략 '{strategy_id}' 생성 중 오류 발생: {str(e)}")
            return None
    
    def get_available_strategies(self) -> List[Dict[str, Any]]:
        """
        사용 가능한 전략 목록 반환
        
        Returns:
            전략 정보 목록
        """
        strategies = []
        
        for strategy_id, strategy_class in self.strategy_classes.items():
            try:
                # 기본 정보 가져오기
                strategy_info = {
                    "id": strategy_id,
                    "name": getattr(strategy_class, "name", strategy_class.__name__),
                    "description": getattr(strategy_class, "description", ""),
                    "version": getattr(strategy_class, "version", "1.0.0")
                }
                
                # 기본 매개변수 가져오기 시도
                if hasattr(strategy_class, 'get_default_parameters_static') and callable(getattr(strategy_class, 'get_default_parameters_static')):
                    # 정적 메서드가 있으면 사용
                    strategy_info["default_parameters"] = strategy_class.get_default_parameters_static()
                else:
                    try:
                        # 임시 인스턴스를 생성하여 기본 매개변수 가져오기
                        empty_params = {}
                        temp_instance = strategy_class(empty_params)
                        strategy_info["default_parameters"] = temp_instance.get_default_parameters()
                    except Exception:
                        # 기본 매개변수를 가져올 수 없는 경우 생략
                        pass
                
                strategies.append(strategy_info)
            
            except Exception as e:
                self.logger.error(f"전략 '{strategy_id}' 정보 가져오기 중 오류 발생: {str(e)}")
        
        return strategies
    
    def load_strategies_from_module(self, module_name: str) -> int:
        """
        모듈에서 전략 클래스 자동 로드
        
        Args:
            module_name: 모듈 이름
            
        Returns:
            로드된 전략 수
        """
        try:
            module = importlib.import_module(module_name)
            loaded_count = 0
            
            # 모듈 내의 모든 클래스 검사
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # StrategyInterface를 구현하고 BaseStrategy가 아닌 클래스만 등록
                if (issubclass(obj, StrategyInterface) and 
                    obj is not StrategyInterface and 
                    obj is not BaseStrategy):
                    
                    # 클래스 이름을 전략 ID로 사용
                    strategy_id = name.lower()
                    if self.register_strategy(strategy_id, obj):
                        loaded_count += 1
            
            self.logger.info(f"모듈 '{module_name}'에서 {loaded_count}개의 전략을 로드했습니다.")
            return loaded_count
        
        except ImportError as e:
            self.logger.error(f"모듈 '{module_name}' 로드 중 오류 발생: {str(e)}")
            return 0