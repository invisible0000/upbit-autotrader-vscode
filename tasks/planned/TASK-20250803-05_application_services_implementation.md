# TASK-20250803-05

## Title
Application Layer 서비스 구현 (Use Case 중심 비즈니스 로직)

## Objective (목표)
Clean Architecture의 Application Layer를 구현하여 UI에 분산된 비즈니스 Use Case들을 중앙 집중화합니다. 전략 생성, 트리거 관리, 백테스팅 등의 핵심 Use Case를 Service 클래스로 구현하여 UI-비즈니스 로직 분리를 완성합니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "Phase 2: Application Layer 구축 (2주)" > "2.1 Application Service 설계 (1주)"

## Pre-requisites (선행 조건)
- `TASK-20250803-01`: 도메인 엔티티 설계 및 구현 완료
- `TASK-20250803-02`: 도메인 서비스 구현 완료
- `TASK-20250803-03`: Repository 인터페이스 정의 완료
- `TASK-20250803-04`: 도메인 이벤트 시스템 완료

## Detailed Steps (상세 실행 절차)

### 1. **[분석]** 현재 UI 레이어의 Use Case 추출
- [ ] `upbit_auto_trading/ui/desktop/screens/strategy_management/` 폴더 분석
- [ ] 전략 CRUD, 트리거 생성, 백테스팅 등 주요 Use Case 식별
- [ ] 각 Use Case의 입력/출력 데이터 구조 분석

### 2. **[폴더 구조 생성]** Application Layer 기본 구조
- [ ] `upbit_auto_trading/application/` 폴더 생성
- [ ] `upbit_auto_trading/application/services/` 폴더 생성
- [ ] `upbit_auto_trading/application/dto/` 폴더 생성
- [ ] `upbit_auto_trading/application/commands/` 폴더 생성
- [ ] `upbit_auto_trading/application/__init__.py` 파일 생성

### 3. **[새 코드 작성]** 기본 Application Service 추상 클래스
- [ ] `upbit_auto_trading/application/services/base_application_service.py` 생성:
```python
from abc import ABC
from typing import TypeVar, Generic

from upbit_auto_trading.domain.events.domain_event_publisher import get_domain_event_publisher

T = TypeVar('T')

class BaseApplicationService(ABC, Generic[T]):
    """모든 Application Service의 기본 클래스"""
    
    def __init__(self):
        self._event_publisher = get_domain_event_publisher()
    
    def _publish_domain_events(self, entity) -> None:
        """엔티티의 도메인 이벤트들을 발행"""
        if hasattr(entity, 'get_domain_events'):
            events = entity.get_domain_events()
            for event in events:
                self._event_publisher.publish(event)
            entity.clear_domain_events()
```

### 4. **[새 코드 작성]** DTO (Data Transfer Object) 정의
- [ ] `upbit_auto_trading/application/dto/strategy_dto.py` 생성:
```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class CreateStrategyDto:
    """전략 생성 요청 DTO"""
    name: str
    description: Optional[str] = None
    tags: List[str] = None
    created_by: str = "system"

@dataclass
class StrategyDto:
    """전략 응답 DTO"""
    strategy_id: str
    name: str
    description: Optional[str]
    tags: List[str]
    status: str
    entry_triggers_count: int
    exit_triggers_count: int
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_entity(cls, strategy) -> 'StrategyDto':
        """도메인 엔티티에서 DTO 생성"""
        return cls(
            strategy_id=strategy.strategy_id.value,
            name=strategy.name,
            description=strategy.description,
            tags=strategy.tags or [],
            status=strategy.status.value,
            entry_triggers_count=len(strategy.entry_triggers),
            exit_triggers_count=len(strategy.exit_triggers),
            created_at=strategy.created_at,
            updated_at=strategy.updated_at
        )

@dataclass
class UpdateStrategyDto:
    """전략 수정 요청 DTO"""
    strategy_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    updated_by: str = "system"
```

- [ ] `upbit_auto_trading/application/dto/trigger_dto.py` 생성:
```python
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class CreateTriggerDto:
    """트리거 생성 요청 DTO"""
    strategy_id: str
    variable_id: str
    variable_params: Dict[str, Any]
    operator: str
    target_value: Any
    trigger_type: str  # ENTRY, EXIT
    trigger_name: Optional[str] = None

@dataclass
class TriggerDto:
    """트리거 응답 DTO"""
    trigger_id: str
    strategy_id: str
    trigger_name: str
    variable_id: str
    variable_params: Dict[str, Any]
    operator: str
    target_value: Any
    trigger_type: str
    is_active: bool
    created_at: datetime
    
    @classmethod
    def from_entity(cls, trigger) -> 'TriggerDto':
        """도메인 엔티티에서 DTO 생성"""
        return cls(
            trigger_id=trigger.trigger_id.value,
            strategy_id=trigger.strategy_id.value if trigger.strategy_id else "",
            trigger_name=trigger.trigger_name or "",
            variable_id=trigger.variable.variable_id,
            variable_params=trigger.variable.parameters,
            operator=trigger.operator.value,
            target_value=trigger.target_value,
            trigger_type=trigger.trigger_type.value,
            is_active=trigger.is_active,
            created_at=trigger.created_at
        )
```

### 5. **[새 코드 작성]** Command 패턴 구현
- [ ] `upbit_auto_trading/application/commands/strategy_commands.py` 생성:
```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class CreateStrategyCommand:
    """전략 생성 명령"""
    name: str
    description: Optional[str] = None
    tags: List[str] = None
    created_by: str = "system"
    
    def validate(self) -> List[str]:
        """명령 유효성 검증"""
        errors = []
        if not self.name or len(self.name.strip()) == 0:
            errors.append("전략 이름은 필수입니다")
        if len(self.name) > 100:
            errors.append("전략 이름은 100자를 초과할 수 없습니다")
        return errors

@dataclass
class UpdateStrategyCommand:
    """전략 수정 명령"""
    strategy_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    updated_by: str = "system"
    
    def validate(self) -> List[str]:
        """명령 유효성 검증"""
        errors = []
        if not self.strategy_id:
            errors.append("전략 ID는 필수입니다")
        if self.name is not None and len(self.name) > 100:
            errors.append("전략 이름은 100자를 초과할 수 없습니다")
        return errors

@dataclass
class DeleteStrategyCommand:
    """전략 삭제 명령"""
    strategy_id: str
    soft_delete: bool = True
    deleted_by: str = "system"
    
    def validate(self) -> List[str]:
        """명령 유효성 검증"""
        errors = []
        if not self.strategy_id:
            errors.append("전략 ID는 필수입니다")
        return errors
```

### 6. **[새 코드 작성]** 전략 관리 Application Service
- [ ] `upbit_auto_trading/application/services/strategy_application_service.py` 생성:
```python
from typing import List, Optional
import logging

from upbit_auto_trading.application.services.base_application_service import BaseApplicationService
from upbit_auto_trading.application.dto.strategy_dto import StrategyDto, CreateStrategyDto, UpdateStrategyDto
from upbit_auto_trading.application.commands.strategy_commands import (
    CreateStrategyCommand, UpdateStrategyCommand, DeleteStrategyCommand
)
from upbit_auto_trading.domain.entities.strategy import Strategy
from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
from upbit_auto_trading.domain.services.strategy_compatibility_service import StrategyCompatibilityService

class StrategyApplicationService(BaseApplicationService[Strategy]):
    """전략 관리 Application Service"""
    
    def __init__(self, strategy_repository: StrategyRepository, 
                 compatibility_service: StrategyCompatibilityService):
        super().__init__()
        self._strategy_repository = strategy_repository
        self._compatibility_service = compatibility_service
        self._logger = logging.getLogger(__name__)
    
    def create_strategy(self, command: CreateStrategyCommand) -> StrategyDto:
        """새 전략 생성"""
        # 1. 명령 유효성 검증
        validation_errors = command.validate()
        if validation_errors:
            raise ValueError(f"전략 생성 실패: {', '.join(validation_errors)}")
        
        # 2. 중복 이름 검증
        existing_strategy = self._strategy_repository.find_by_name(command.name)
        if existing_strategy:
            raise ValueError(f"이미 존재하는 전략 이름입니다: {command.name}")
        
        # 3. 도메인 엔티티 생성
        strategy_id = StrategyId.generate()
        strategy = Strategy.create_new(strategy_id, command.name)
        
        if command.description:
            strategy.update_description(command.description)
        if command.tags:
            strategy.update_tags(command.tags)
        
        # 4. 저장 및 이벤트 발행
        self._strategy_repository.save(strategy)
        self._publish_domain_events(strategy)
        
        self._logger.info(f"전략 생성 완료: {strategy.name} (ID: {strategy.strategy_id.value})")
        
        return StrategyDto.from_entity(strategy)
    
    def get_strategy(self, strategy_id: str) -> Optional[StrategyDto]:
        """전략 조회"""
        strategy = self._strategy_repository.find_by_id(StrategyId(strategy_id))
        return StrategyDto.from_entity(strategy) if strategy else None
    
    def get_all_strategies(self) -> List[StrategyDto]:
        """모든 전략 조회"""
        strategies = self._strategy_repository.find_all()
        return [StrategyDto.from_entity(strategy) for strategy in strategies]
    
    def update_strategy(self, command: UpdateStrategyCommand) -> StrategyDto:
        """전략 수정"""
        # 1. 명령 유효성 검증
        validation_errors = command.validate()
        if validation_errors:
            raise ValueError(f"전략 수정 실패: {', '.join(validation_errors)}")
        
        # 2. 기존 전략 조회
        strategy = self._strategy_repository.find_by_id(StrategyId(command.strategy_id))
        if not strategy:
            raise ValueError(f"존재하지 않는 전략입니다: {command.strategy_id}")
        
        # 3. 수정 사항 적용
        if command.name and command.name != strategy.name:
            # 중복 이름 검증
            existing_strategy = self._strategy_repository.find_by_name(command.name)
            if existing_strategy and existing_strategy.strategy_id != strategy.strategy_id:
                raise ValueError(f"이미 존재하는 전략 이름입니다: {command.name}")
            strategy.update_name(command.name)
        
        if command.description is not None:
            strategy.update_description(command.description)
        
        if command.tags is not None:
            strategy.update_tags(command.tags)
        
        # 4. 저장 및 이벤트 발행
        self._strategy_repository.save(strategy)
        self._publish_domain_events(strategy)
        
        self._logger.info(f"전략 수정 완료: {strategy.name} (ID: {strategy.strategy_id.value})")
        
        return StrategyDto.from_entity(strategy)
    
    def delete_strategy(self, command: DeleteStrategyCommand) -> bool:
        """전략 삭제"""
        # 1. 명령 유효성 검증
        validation_errors = command.validate()
        if validation_errors:
            raise ValueError(f"전략 삭제 실패: {', '.join(validation_errors)}")
        
        # 2. 기존 전략 조회
        strategy = self._strategy_repository.find_by_id(StrategyId(command.strategy_id))
        if not strategy:
            raise ValueError(f"존재하지 않는 전략입니다: {command.strategy_id}")
        
        # 3. 삭제 처리
        if command.soft_delete:
            strategy.soft_delete()
            self._strategy_repository.save(strategy)
        else:
            self._strategy_repository.delete(strategy.strategy_id)
        
        # 4. 이벤트 발행
        self._publish_domain_events(strategy)
        
        self._logger.info(f"전략 삭제 완료: {strategy.name} (ID: {strategy.strategy_id.value})")
        
        return True
    
    def activate_strategy(self, strategy_id: str) -> StrategyDto:
        """전략 활성화"""
        strategy = self._strategy_repository.find_by_id(StrategyId(strategy_id))
        if not strategy:
            raise ValueError(f"존재하지 않는 전략입니다: {strategy_id}")
        
        strategy.activate()
        self._strategy_repository.save(strategy)
        self._publish_domain_events(strategy)
        
        return StrategyDto.from_entity(strategy)
    
    def deactivate_strategy(self, strategy_id: str, reason: str = "user_requested") -> StrategyDto:
        """전략 비활성화"""
        strategy = self._strategy_repository.find_by_id(StrategyId(strategy_id))
        if not strategy:
            raise ValueError(f"존재하지 않는 전략입니다: {strategy_id}")
        
        strategy.deactivate(reason)
        self._strategy_repository.save(strategy)
        self._publish_domain_events(strategy)
        
        return StrategyDto.from_entity(strategy)
```

### 7. **[새 코드 작성]** 트리거 관리 Application Service
- [ ] `upbit_auto_trading/application/services/trigger_application_service.py` 생성:
```python
from typing import List, Optional
import logging

from upbit_auto_trading.application.services.base_application_service import BaseApplicationService
from upbit_auto_trading.application.dto.trigger_dto import TriggerDto, CreateTriggerDto
from upbit_auto_trading.domain.entities.trigger import Trigger, TradingVariable
from upbit_auto_trading.domain.value_objects.trigger_id import TriggerId
from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
from upbit_auto_trading.domain.repositories.trigger_repository import TriggerRepository
from upbit_auto_trading.domain.repositories.settings_repository import SettingsRepository
from upbit_auto_trading.domain.services.strategy_compatibility_service import StrategyCompatibilityService

class TriggerApplicationService(BaseApplicationService[Trigger]):
    """트리거 관리 Application Service"""
    
    def __init__(self, trigger_repository: TriggerRepository,
                 strategy_repository: StrategyRepository,
                 settings_repository: SettingsRepository,
                 compatibility_service: StrategyCompatibilityService):
        super().__init__()
        self._trigger_repository = trigger_repository
        self._strategy_repository = strategy_repository
        self._settings_repository = settings_repository
        self._compatibility_service = compatibility_service
        self._logger = logging.getLogger(__name__)
    
    def create_trigger(self, dto: CreateTriggerDto) -> TriggerDto:
        """새 트리거 생성"""
        # 1. 전략 존재 여부 확인
        strategy = self._strategy_repository.find_by_id(StrategyId(dto.strategy_id))
        if not strategy:
            raise ValueError(f"존재하지 않는 전략입니다: {dto.strategy_id}")
        
        # 2. 트레이딩 변수 조회
        variable_def = self._settings_repository.get_trading_variable(dto.variable_id)
        if not variable_def:
            raise ValueError(f"존재하지 않는 트레이딩 변수입니다: {dto.variable_id}")
        
        # 3. 트레이딩 변수 생성
        trading_variable = TradingVariable(
            variable_id=variable_def["variable_id"],
            display_name=variable_def["display_name_ko"],
            purpose_category=variable_def["purpose_category"],
            chart_category=variable_def["chart_category"],
            comparison_group=variable_def["comparison_group"],
            parameters=dto.variable_params
        )
        
        # 4. 트리거 엔티티 생성
        trigger_id = TriggerId.generate()
        trigger = Trigger.create_new(
            trigger_id=trigger_id,
            variable=trading_variable,
            operator=dto.operator,
            target_value=dto.target_value,
            trigger_type=dto.trigger_type
        )
        
        if dto.trigger_name:
            trigger.update_name(dto.trigger_name)
        
        # 5. 호환성 검증
        if not self._compatibility_service.can_add_trigger_to_strategy(strategy, trigger):
            raise ValueError(f"트리거가 전략과 호환되지 않습니다")
        
        # 6. 전략에 트리거 추가
        strategy.add_trigger(trigger)
        
        # 7. 저장 및 이벤트 발행
        self._trigger_repository.save(trigger)
        self._strategy_repository.save(strategy)
        self._publish_domain_events(trigger)
        self._publish_domain_events(strategy)
        
        self._logger.info(f"트리거 생성 완료: {trigger.trigger_name} (ID: {trigger.trigger_id.value})")
        
        return TriggerDto.from_entity(trigger)
    
    def get_triggers_by_strategy(self, strategy_id: str) -> List[TriggerDto]:
        """전략별 트리거 조회"""
        triggers = self._trigger_repository.find_by_strategy_id(StrategyId(strategy_id))
        return [TriggerDto.from_entity(trigger) for trigger in triggers]
    
    def delete_trigger(self, trigger_id: str) -> bool:
        """트리거 삭제"""
        # 1. 트리거 조회
        trigger = self._trigger_repository.find_by_id(TriggerId(trigger_id))
        if not trigger:
            raise ValueError(f"존재하지 않는 트리거입니다: {trigger_id}")
        
        # 2. 전략에서 트리거 제거
        if trigger.strategy_id:
            strategy = self._strategy_repository.find_by_id(trigger.strategy_id)
            if strategy:
                strategy.remove_trigger(trigger.trigger_id)
                self._strategy_repository.save(strategy)
                self._publish_domain_events(strategy)
        
        # 3. 트리거 삭제
        self._trigger_repository.delete(trigger.trigger_id)
        
        self._logger.info(f"트리거 삭제 완료: {trigger.trigger_name} (ID: {trigger.trigger_id.value})")
        
        return True
    
    def validate_trigger_compatibility(self, strategy_id: str, trigger_data: dict) -> dict:
        """트리거 호환성 검증"""
        strategy = self._strategy_repository.find_by_id(StrategyId(strategy_id))
        if not strategy:
            return {"compatible": False, "reason": "존재하지 않는 전략입니다"}
        
        # 임시 트리거 생성하여 호환성 검증
        variable_def = self._settings_repository.get_trading_variable(trigger_data["variable_id"])
        if not variable_def:
            return {"compatible": False, "reason": "존재하지 않는 트레이딩 변수입니다"}
        
        trading_variable = TradingVariable(
            variable_id=variable_def["variable_id"],
            display_name=variable_def["display_name_ko"],
            purpose_category=variable_def["purpose_category"],
            chart_category=variable_def["chart_category"],
            comparison_group=variable_def["comparison_group"],
            parameters=trigger_data.get("variable_params", {})
        )
        
        temp_trigger = Trigger.create_new(
            trigger_id=TriggerId.generate(),
            variable=trading_variable,
            operator=trigger_data["operator"],
            target_value=trigger_data["target_value"],
            trigger_type=trigger_data["trigger_type"]
        )
        
        compatible = self._compatibility_service.can_add_trigger_to_strategy(strategy, temp_trigger)
        reason = "" if compatible else self._compatibility_service.get_incompatibility_reason(strategy, temp_trigger)
        
        return {
            "compatible": compatible,
            "reason": reason,
            "suggestions": self._compatibility_service.get_compatibility_suggestions(strategy, temp_trigger)
        }
```

### 8. **[새 코드 작성]** 백테스팅 Application Service
- [ ] `upbit_auto_trading/application/services/backtest_application_service.py` 생성:
```python
from typing import Dict, Any
import logging
from datetime import datetime

from upbit_auto_trading.application.services.base_application_service import BaseApplicationService
from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
from upbit_auto_trading.domain.repositories.backtest_repository import BacktestRepository
from upbit_auto_trading.domain.repositories.market_data_repository import MarketDataRepository

class BacktestApplicationService(BaseApplicationService):
    """백테스팅 Application Service"""
    
    def __init__(self, strategy_repository: StrategyRepository,
                 backtest_repository: BacktestRepository,
                 market_data_repository: MarketDataRepository):
        super().__init__()
        self._strategy_repository = strategy_repository
        self._backtest_repository = backtest_repository
        self._market_data_repository = market_data_repository
        self._logger = logging.getLogger(__name__)
    
    def start_backtest(self, strategy_id: str, symbol: str, 
                      start_date: datetime, end_date: datetime,
                      initial_capital: float, settings: Dict[str, Any]) -> str:
        """백테스팅 시작"""
        # 1. 전략 존재 여부 확인
        strategy = self._strategy_repository.find_by_id(StrategyId(strategy_id))
        if not strategy:
            raise ValueError(f"존재하지 않는 전략입니다: {strategy_id}")
        
        # 2. 백테스트 ID 생성
        backtest_id = f"BT_{strategy_id}_{int(datetime.now().timestamp())}"
        
        # 3. 백테스트 시작 이벤트 발행
        from upbit_auto_trading.domain.events.backtest_events import BacktestStarted
        start_event = BacktestStarted(
            backtest_id=backtest_id,
            strategy_id=StrategyId(strategy_id),
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            settings=settings
        )
        self._event_publisher.publish(start_event)
        
        # 4. 백테스트 작업을 별도 스레드에서 실행
        # (실제 구현은 Infrastructure Layer에서)
        
        self._logger.info(f"백테스팅 시작: {backtest_id}")
        return backtest_id
    
    def get_backtest_result(self, backtest_id: str) -> Dict[str, Any]:
        """백테스팅 결과 조회"""
        result = self._backtest_repository.find_by_id(backtest_id)
        if not result:
            raise ValueError(f"존재하지 않는 백테스트입니다: {backtest_id}")
        
        return result
    
    def get_backtest_progress(self, backtest_id: str) -> Dict[str, Any]:
        """백테스팅 진행률 조회"""
        progress = self._backtest_repository.get_progress(backtest_id)
        return progress or {"progress": 0, "status": "not_found"}
```

### 9. **[테스트 코드 작성]** Application Service 테스트
- [ ] `tests/application/` 폴더 생성
- [ ] `tests/application/services/test_strategy_application_service.py` 생성:
```python
import pytest
from unittest.mock import Mock

from upbit_auto_trading.application.services.strategy_application_service import StrategyApplicationService
from upbit_auto_trading.application.commands.strategy_commands import CreateStrategyCommand
from upbit_auto_trading.domain.entities.strategy import Strategy
from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId

class TestStrategyApplicationService:
    def setup_method(self):
        self.strategy_repository = Mock()
        self.compatibility_service = Mock()
        self.service = StrategyApplicationService(
            self.strategy_repository, 
            self.compatibility_service
        )
    
    def test_create_strategy_success(self):
        # Given
        command = CreateStrategyCommand(name="테스트 전략", description="테스트용")
        self.strategy_repository.find_by_name.return_value = None
        
        # When
        result = self.service.create_strategy(command)
        
        # Then
        assert result.name == "테스트 전략"
        self.strategy_repository.save.assert_called_once()
    
    def test_create_strategy_duplicate_name_fails(self):
        # Given
        command = CreateStrategyCommand(name="중복 전략")
        existing_strategy = Mock()
        self.strategy_repository.find_by_name.return_value = existing_strategy
        
        # When & Then
        with pytest.raises(ValueError, match="이미 존재하는 전략 이름입니다"):
            self.service.create_strategy(command)
```

### 10. **[통합]** Dependency Injection Container 구성
- [ ] `upbit_auto_trading/application/container.py` 생성:
```python
from upbit_auto_trading.application.services.strategy_application_service import StrategyApplicationService
from upbit_auto_trading.application.services.trigger_application_service import TriggerApplicationService
from upbit_auto_trading.application.services.backtest_application_service import BacktestApplicationService

class ApplicationServiceContainer:
    """Application Service들의 의존성 주입 컨테이너"""
    
    def __init__(self, repository_container):
        self._repo_container = repository_container
        self._services = {}
    
    def get_strategy_service(self) -> StrategyApplicationService:
        if "strategy" not in self._services:
            self._services["strategy"] = StrategyApplicationService(
                self._repo_container.get_strategy_repository(),
                self._repo_container.get_compatibility_service()
            )
        return self._services["strategy"]
    
    def get_trigger_service(self) -> TriggerApplicationService:
        if "trigger" not in self._services:
            self._services["trigger"] = TriggerApplicationService(
                self._repo_container.get_trigger_repository(),
                self._repo_container.get_strategy_repository(),
                self._repo_container.get_settings_repository(),
                self._repo_container.get_compatibility_service()
            )
        return self._services["trigger"]
    
    def get_backtest_service(self) -> BacktestApplicationService:
        if "backtest" not in self._services:
            self._services["backtest"] = BacktestApplicationService(
                self._repo_container.get_strategy_repository(),
                self._repo_container.get_backtest_repository(),
                self._repo_container.get_market_data_repository()
            )
        return self._services["backtest"]
```

## Verification Criteria (완료 검증 조건)

### **[서비스 구현 검증]** 모든 Application Service 구현 확인
- [ ] `pytest tests/application/ -v` 실행하여 모든 테스트 통과
- [ ] 각 서비스의 주요 Use Case 메서드가 올바르게 구현되었는지 확인

### **[DTO 변환 검증]** Entity ↔ DTO 변환 동작 확인
- [ ] Python REPL에서 DTO 변환 테스트:
```python
from upbit_auto_trading.domain.entities.strategy import Strategy
from upbit_auto_trading.application.dto.strategy_dto import StrategyDto

strategy = Strategy.create_new(StrategyId("TEST"), "테스트")
dto = StrategyDto.from_entity(strategy)
assert dto.name == "테스트"
print("✅ DTO 변환 검증 완료")
```

### **[Use Case 실행 검증]** 전체 Use Case 플로우 확인
- [ ] 전략 생성 → 트리거 추가 → 백테스팅 전체 플로우 테스트
- [ ] 도메인 이벤트가 적절히 발행되는지 확인

### **[의존성 주입 검증]** Container를 통한 서비스 생성 확인
- [ ] ApplicationServiceContainer가 올바르게 동작하는지 확인

## Notes (주의사항)
- Application Service는 트랜잭션 경계를 담당하며, 하나의 Use Case 당 하나의 서비스 메서드로 구현
- DTO는 계층 간 데이터 전송에만 사용하며, 비즈니스 로직을 포함하지 않음
- Command 패턴을 통해 입력 검증을 명시적으로 처리
- 모든 도메인 이벤트는 Application Service에서 발행하여 일관성 보장
