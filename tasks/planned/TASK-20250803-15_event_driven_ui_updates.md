# TASK-20250803-14

## Title
Presentation Layer - 이벤트 기반 UI 갱신 시스템 구현

## Objective (목표)
Domain Event와 UI 간의 느슨한 결합을 통해 실시간 UI 갱신 시스템을 구현합니다. 전략 실행, 백테스팅 진행, 호환성 검증 등의 이벤트를 실시간으로 UI에 반영하여 사용자 경험을 향상시킵니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "Phase 4: Presentation Layer 리팩토링 (3주)" > "4.3 이벤트 기반 UI 갱신 (1주)"

## Pre-requisites (선행 조건)
- `TASK-20250803-13`: View 리팩토링 완료
- `TASK-20250803-10`: Event Bus 시스템 구현 완료
- Domain Event 시스템 구현 완료

## Detailed Steps (상세 실행 절차)

### 1. **[분석]** UI 갱신 이벤트 요구사항 식별
- [ ] 실시간 갱신이 필요한 UI 컴포넌트 목록 작성
- [ ] Domain Event와 UI Event 매핑 관계 정의
- [ ] 이벤트 기반 갱신 우선순위 설정

### 2. **[이벤트 정의]** UI 전용 이벤트 클래스
- [ ] `presentation/events/ui_events.py` 생성:
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List

@dataclass
class StrategyListUpdatedEvent:
    """전략 목록 갱신 이벤트"""
    strategies: List[Dict[str, Any]]
    timestamp: datetime

@dataclass
class TriggerCompatibilityCheckedEvent:
    """트리거 호환성 검증 이벤트"""
    is_compatible: bool
    warnings: List[str]
    affected_variables: List[str]
    timestamp: datetime

@dataclass
class BacktestProgressEvent:
    """백테스팅 진행 상황 이벤트"""
    strategy_id: str
    progress_percent: float
    current_date: str
    interim_results: Dict[str, Any]
    timestamp: datetime

@dataclass
class ChartDataUpdatedEvent:
    """차트 데이터 갱신 이벤트"""
    chart_id: str
    chart_data: Dict[str, Any]
    timestamp: datetime
```

### 3. **[구현]** UI 이벤트 핸들러
- [ ] `presentation/event_handlers/ui_event_handlers.py` 생성:
```python
from typing import Dict, List, Callable
from upbit_auto_trading.presentation.events.ui_events import *

class UIEventHandler:
    """UI 이벤트 핸들러"""
    
    def __init__(self):
        self._subscribers: Dict[type, List[Callable]] = {}
    
    def subscribe(self, event_type: type, handler: Callable) -> None:
        """이벤트 핸들러 등록"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def publish(self, event: Any) -> None:
        """UI 이벤트 발행"""
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"UI 이벤트 핸들링 오류: {e}")

class StrategyListEventHandler:
    """전략 목록 이벤트 핸들러"""
    
    def __init__(self, view: IStrategyListView):
        self._view = view
    
    def handle_strategy_list_updated(self, event: StrategyListUpdatedEvent) -> None:
        """전략 목록 갱신 처리"""
        self._view.display_strategies(event.strategies)
    
    def handle_strategy_created(self, event: StrategyCreatedEvent) -> None:
        """새 전략 생성 처리"""
        self._view.show_success(f"전략 '{event.strategy_name}' 생성 완료")
```

### 4. **[구현]** 실시간 호환성 검증 UI
- [ ] TriggerBuilderView에 실시간 이벤트 연동:
```python
class TriggerBuilderView(QWidget, ITriggerBuilderView):
    def __init__(self):
        super().__init__()
        self._ui_event_handler = UIEventHandler()
        self._setup_event_subscriptions()
    
    def _setup_event_subscriptions(self) -> None:
        """이벤트 구독 설정"""
        self._ui_event_handler.subscribe(
            TriggerCompatibilityCheckedEvent,
            self._on_compatibility_checked
        )
    
    def _on_compatibility_checked(self, event: TriggerCompatibilityCheckedEvent) -> None:
        """호환성 검증 결과 UI 반영"""
        self.update_compatibility_status(event.is_compatible)
        if event.warnings:
            self.show_compatibility_warning("\n".join(event.warnings))
        
        # 호환되지 않는 변수들 비활성화
        self._disable_incompatible_variables(event.affected_variables)
```

### 5. **[구현]** 백테스팅 진행률 표시
- [ ] `presentation/components/progress_chart_widget.py` 생성:
```python
from PyQt6.QtWidgets import QWidget, QProgressBar, QLabel, QVBoxLayout
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

class ProgressChartWidget(QWidget):
    """백테스팅 진행률 및 미니 차트 위젯"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self._ui_event_handler = UIEventHandler()
        self._setup_event_subscriptions()
    
    def setup_ui(self) -> None:
        """UI 구성"""
        layout = QVBoxLayout(self)
        
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("대기 중...")
        self.mini_chart = self._create_mini_chart()
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.mini_chart)
    
    def _on_backtest_progress(self, event: BacktestProgressEvent) -> None:
        """백테스팅 진행 상황 업데이트"""
        self.progress_bar.setValue(int(event.progress_percent))
        self.status_label.setText(f"진행 중... {event.current_date}")
        
        # 중간 결과 미니 차트에 반영
        if event.interim_results:
            self._update_mini_chart(event.interim_results)
```

### 6. **[통합]** Presenter와 이벤트 시스템 연동
- [ ] Presenter에서 UI 이벤트 발행:
```python
class StrategyMakerPresenter:
    def __init__(self, view: IStrategyMakerView, 
                 strategy_service: StrategyApplicationService,
                 ui_event_handler: UIEventHandler):
        self._view = view
        self._strategy_service = strategy_service
        self._ui_event_handler = ui_event_handler
    
    def handle_save_strategy(self, strategy_data: Dict[str, Any]) -> None:
        """전략 저장 처리"""
        try:
            result = self._strategy_service.create_strategy(
                CreateStrategyCommand.from_dict(strategy_data)
            )
            
            # UI 이벤트 발행
            self._ui_event_handler.publish(
                StrategyListUpdatedEvent(
                    strategies=self._get_updated_strategy_list(),
                    timestamp=datetime.now()
                )
            )
            
            self._view.show_success("전략 저장 완료")
        except ValidationError as e:
            self._view.display_validation_errors(e.errors)
```

### 7. **[구현]** 차트 실시간 업데이트
- [ ] 차트 컴포넌트에 이벤트 기반 갱신:
```python
class MiniChartComponent(QWidget):
    def __init__(self):
        super().__init__()
        self._ui_event_handler = UIEventHandler()
        self._ui_event_handler.subscribe(
            ChartDataUpdatedEvent,
            self._on_chart_data_updated
        )
    
    def _on_chart_data_updated(self, event: ChartDataUpdatedEvent) -> None:
        """차트 데이터 갱신"""
        if event.chart_id == self.chart_id:
            self._redraw_chart(event.chart_data)
```

### 8. **[최적화]** 이벤트 디바운싱 및 배칭
- [ ] `presentation/utils/event_debouncer.py` 생성:
```python
import asyncio
from typing import Callable, Dict
from datetime import datetime, timedelta

class EventDebouncer:
    """이벤트 디바운싱 유틸리티"""
    
    def __init__(self, delay_ms: int = 300):
        self._delay = timedelta(milliseconds=delay_ms)
        self._pending_calls: Dict[str, datetime] = {}
    
    def debounce(self, key: str, callback: Callable) -> None:
        """디바운싱된 콜백 실행"""
        now = datetime.now()
        self._pending_calls[key] = now
        
        asyncio.create_task(self._execute_delayed(key, callback, now))
    
    async def _execute_delayed(self, key: str, callback: Callable, timestamp: datetime) -> None:
        """지연 실행"""
        await asyncio.sleep(self._delay.total_seconds())
        
        # 더 최근 호출이 있으면 취소
        if self._pending_calls.get(key) != timestamp:
            return
        
        callback()
        del self._pending_calls[key]
```

## Verification Criteria (완료 검증 조건)

### **[실시간 갱신 확인]**
- [ ] 전략 저장 시 목록이 즉시 갱신됨
- [ ] 호환성 검증 결과가 실시간으로 UI에 반영됨
- [ ] 백테스팅 진행률이 실시간으로 표시됨

### **[이벤트 시스템 성능]**
- [ ] UI 이벤트 처리 지연 시간 100ms 이하
- [ ] 이벤트 핸들링 오류 시 UI가 멈추지 않음
- [ ] 메모리 누수 없이 이벤트 구독/해제 동작

### **[사용자 경험 확인]**
- [ ] UI가 즉시 반응하며 사용자 피드백 제공
- [ ] 장시간 작업 시 진행 상황 표시
- [ ] 오류 발생 시 명확한 메시지 표시

## Notes (주의사항)
- UI 스레드 안전성 고려 필수
- 이벤트 핸들러에서 예외 발생 시 다른 핸들러에 영향 없도록 격리
- 메모리 누수 방지를 위한 적절한 구독 해제
