# TASK-20250803-12

## Title
Presentation Layer - MVP 패턴 적용 및 Passive View 구현

## Objective (목표)
Clean Architecture의 Presentation Layer에서 MVP(Model-View-Presenter) 패턴을 적용하여 UI와 비즈니스 로직을 완전히 분리합니다. 현재 UI에 혼재된 비즈니스 로직을 Application Layer로 이동하고, UI는 순수한 표시 기능만 담당하도록 리팩토링합니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "Phase 4: Presentation Layer 리팩토링 (3주)" > "4.1 MVP 패턴 Presenter 구현 (1주)"

## Pre-requisites (선행 조건)
- Phase 3 Infrastructure Layer 완료 (TASK-08~11)
- Application Layer Service 구현 완료
- UI에서 분리할 비즈니스 로직 식별 완료

## Detailed Steps (상세 실행 절차)

### 1. **[분석]** 현재 UI 비즈니스 로직 분석
- [ ] `ui/desktop/screens/strategy_management/` 폴더 분석
- [ ] 각 Screen에서 비즈니스 로직 추출 목록 작성
- [ ] Presenter-View 분리 대상 컴포넌트 식별
- [ ] Application Service와의 연동 지점 설계

### 2. **[구조 생성]** MVP 패턴 폴더 구조
- [ ] `upbit_auto_trading/presentation/presenters/` 폴더 생성
- [ ] `upbit_auto_trading/presentation/views/` 폴더 생성
- [ ] `upbit_auto_trading/presentation/view_models/` 폴더 생성
- [ ] `upbit_auto_trading/presentation/interfaces/` 폴더 생성

### 3. **[인터페이스 정의]** View 인터페이스
- [ ] `upbit_auto_trading/presentation/interfaces/view_interfaces.py` 생성:
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class IStrategyMakerView(ABC):
    """전략 메이커 View 인터페이스"""
    
    @abstractmethod
    def display_strategy_list(self, strategies: List[Dict[str, Any]]) -> None:
        """전략 목록 표시"""
        pass
    
    @abstractmethod
    def display_validation_errors(self, errors: List[str]) -> None:
        """검증 오류 표시"""
        pass
    
    @abstractmethod
    def display_success_message(self, message: str) -> None:
        """성공 메시지 표시"""
        pass
    
    @abstractmethod
    def clear_form(self) -> None:
        """폼 초기화"""
        pass

class ITriggerBuilderView(ABC):
    """트리거 빌더 View 인터페이스"""
    
    @abstractmethod
    def display_variables(self, variables: List[Dict[str, Any]]) -> None:
        """변수 목록 표시"""
        pass
    
    @abstractmethod
    def display_compatibility_warning(self, message: str) -> None:
        """호환성 경고 표시"""
        pass
    
    @abstractmethod
    def update_condition_preview(self, preview: str) -> None:
        """조건 미리보기 업데이트"""
        pass
```

### 4. **[Presenter 구현]** 핵심 Presenter 클래스들
- [ ] `upbit_auto_trading/presentation/presenters/strategy_maker_presenter.py` 생성:
```python
from typing import Dict, Any, List
from upbit_auto_trading.presentation.interfaces.view_interfaces import IStrategyMakerView
from upbit_auto_trading.application.services.strategy_application_service import StrategyApplicationService

class StrategyMakerPresenter:
    """전략 메이커 Presenter"""
    
    def __init__(self, view: IStrategyMakerView, strategy_service: StrategyApplicationService):
        self.view = view
        self.strategy_service = strategy_service
    
    def load_strategies(self) -> None:
        """전략 목록 로드"""
        try:
            strategies = self.strategy_service.get_all_strategies()
            strategy_dtos = [strategy.to_dict() for strategy in strategies]
            self.view.display_strategy_list(strategy_dtos)
        except Exception as e:
            self.view.display_validation_errors([f"전략 로드 실패: {str(e)}"])
    
    def save_strategy(self, strategy_data: Dict[str, Any]) -> None:
        """전략 저장"""
        try:
            # 입력 데이터 검증
            validation_errors = self._validate_strategy_data(strategy_data)
            if validation_errors:
                self.view.display_validation_errors(validation_errors)
                return
            
            # Application Service 호출
            result = self.strategy_service.create_strategy(strategy_data)
            
            # 성공 처리
            self.view.display_success_message("전략이 성공적으로 저장되었습니다")
            self.view.clear_form()
            self.load_strategies()  # 목록 새로고침
            
        except ValidationError as e:
            self.view.display_validation_errors(e.errors)
        except Exception as e:
            self.view.display_validation_errors([f"전략 저장 실패: {str(e)}"])
    
    def _validate_strategy_data(self, data: Dict[str, Any]) -> List[str]:
        """클라이언트 사이드 검증"""
        errors = []
        
        if not data.get('name', '').strip():
            errors.append("전략 이름을 입력해주세요")
        
        if not data.get('entry_triggers'):
            errors.append("진입 조건을 최소 하나 설정해주세요")
        
        return errors
```

### 5. **[View 리팩토링]** Strategy Maker View 리팩토링
- [ ] 기존 `strategy_maker.py`를 Passive View로 변경:
```python
# 기존 코드에서 비즈니스 로직 제거
class StrategyMakerView(QWidget, IStrategyMakerView):
    def __init__(self, presenter: StrategyMakerPresenter):
        super().__init__()
        self.presenter = presenter
        self.setup_ui()
        self.connect_signals()
    
    def on_save_clicked(self):
        """저장 버튼 클릭 - 비즈니스 로직 없이 Presenter에 위임"""
        strategy_data = self.collect_form_data()
        self.presenter.save_strategy(strategy_data)
    
    def display_strategy_list(self, strategies: List[Dict[str, Any]]) -> None:
        """전략 목록 표시 - 순수 UI 로직만"""
        self.strategy_list_widget.clear()
        for strategy in strategies:
            item = QListWidgetItem(strategy['name'])
            self.strategy_list_widget.addItem(item)
```

### 6. **[통합]** Application Context와 연동
- [ ] DI 컨테이너에 Presenter 등록
- [ ] 기존 Screen 클래스들의 초기화 로직 수정
- [ ] MainWindow에서 MVP 패턴 적용

### 7. **[테스트]** MVP 패턴 동작 검증
- [ ] Presenter 단위 테스트 작성
- [ ] View-Presenter 통합 테스트
- [ ] 기존 기능 회귀 테스트

## Verification Criteria (완료 검증 조건)

### **[비즈니스 로직 분리 확인]**
- [ ] UI 클래스에서 모든 비즈니스 로직 제거 확인
- [ ] Presenter가 Application Service만 호출하는지 확인
- [ ] View가 표시 기능만 담당하는지 확인

### **[MVP 패턴 동작 확인]**
- [ ] View → Presenter → Application Service 호출 흐름 검증
- [ ] Presenter가 View 인터페이스만 참조하는지 확인
- [ ] 의존성 주입이 정상 동작하는지 확인

## Notes (주의사항)
- UI 스레드 안전성 고려
- 기존 기능 호환성 유지
- 점진적 리팩토링으로 위험 최소화
