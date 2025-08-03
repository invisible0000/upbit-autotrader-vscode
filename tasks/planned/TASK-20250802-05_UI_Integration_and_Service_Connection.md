# TASK-20250802-05: UI 연결 및 서비스 통합

## 📋 작업 개요
**목표**: 새로운 백테스팅 서비스를 기존 UI 시스템에 통합 및 연결
**우선순위**: HIGH
**예상 소요시간**: 4-5시간
**전제조건**: TASK-20250802-04 완료

## 🎯 작업 목표
- [ ] shared_simulation UI 컴포넌트를 새로운 서비스와 연결
- [ ] 기존 UI 인터페이스 100% 호환성 유지
- [ ] UI 컴포넌트를 순수 View로 변환 (비즈니스 로직 제거)
- [ ] 에러 처리 및 사용자 피드백 개선

## 🔄 통합 전략

### Phase 5-1: 서비스 어댑터 구현
기존 UI가 새로운 서비스를 호출할 수 있도록 어댑터 패턴 적용

```
ui/desktop/screens/strategy_management/shared_simulation/
├── adapters/                              # 새로 추가
│   ├── __init__.py
│   ├── backtesting_adapter.py            # 구 UI → 신 서비스 연결
│   └── result_formatter.py               # 결과 데이터 포맷팅
│
└── charts/                               # 기존 유지, 로직 정리
    ├── simulation_control_widget.py      # View만 남김
    └── simulation_result_widget.py       # View만 남김
```

### Phase 5-2: UI 컴포넌트 리팩토링
기존 UI에서 비즈니스 로직 제거하고 View 역할만 수행

## 🛠️ 세부 구현 단계

### Step 1: 백테스팅 어댑터 구현

#### 1.1 BacktestingAdapter (adapters/backtesting_adapter.py)
```python
class BacktestingAdapter:
    """기존 UI와 새로운 백테스팅 서비스를 연결하는 어댑터"""
    
    def __init__(self):
        from business_logic.backtester.services.backtesting_service import BacktestingService
        self._service = BacktestingService()
        self._result_formatter = ResultFormatter()
    
    def run_simulation(self, scenario: str, data_length: int = 100, 
                      indicators: List[str] = None) -> Dict[str, Any]:
        """기존 UI 인터페이스와 호환되는 시뮬레이션 실행"""
        try:
            # UI 파라미터 → 백테스트 설정 변환
            config = self._convert_ui_params_to_config(scenario, data_length, indicators)
            
            # 백테스팅 실행
            result = self._service.run_backtest(config)
            
            # 결과를 기존 UI 형식으로 변환
            return self._result_formatter.format_for_ui(result)
            
        except Exception as e:
            # 에러를 UI 친화적 형태로 변환
            return self._handle_error(e)
    
    def get_available_scenarios(self) -> List[str]:
        """사용 가능한 시나리오 목록 (기존 UI 인터페이스)"""
        return ["상승 추세", "하락 추세", "횡보", "급등", "급락", "이동평균 교차"]
    
    def _convert_ui_params_to_config(self, scenario: str, data_length: int, 
                                   indicators: List[str]) -> BacktestConfig:
        """UI 파라미터를 백테스트 설정으로 변환"""
        from business_logic.backtester.models.backtest_config import BacktestConfig
        
        return BacktestConfig(
            data_source="embedded",  # UI에서는 주로 내장 데이터 사용
            scenario=scenario,
            data_length=data_length,
            indicators=indicators or ["SMA", "RSI"],
            parameters=self._get_default_parameters()
        )
    
    def _handle_error(self, error: Exception) -> Dict[str, Any]:
        """에러를 UI에서 처리 가능한 형태로 변환"""
        return {
            'success': False,
            'error': str(error),
            'error_type': type(error).__name__,
            'fallback_data': self._generate_fallback_response()
        }
```

#### 1.2 ResultFormatter (adapters/result_formatter.py)
```python
class ResultFormatter:
    """백테스팅 결과를 UI 형식으로 변환"""
    
    def format_for_ui(self, result: SimulationResult) -> Dict[str, Any]:
        """SimulationResult → UI 호환 딕셔너리 변환"""
        return {
            # 기존 UI가 기대하는 키 구조 유지
            'current_value': result.market_data.close_prices[-1],
            'price_data': result.market_data.close_prices,
            'scenario': result.simulation_metadata.get('scenario', ''),
            'data_source': result.simulation_metadata.get('data_source', ''),
            'period': 'generated_data',
            'base_value': result.market_data.close_prices[0],
            'change_percent': self._calculate_change_percent(result.market_data.close_prices),
            
            # 지표 데이터 추가
            'indicators': self._format_indicators(result.indicators),
            
            # 메타데이터
            'metadata': result.simulation_metadata
        }
    
    def _calculate_change_percent(self, prices: List[float]) -> float:
        """변화율 계산"""
        if len(prices) < 2:
            return 0.0
        return (prices[-1] / prices[0] - 1) * 100
    
    def _format_indicators(self, indicators: IndicatorData) -> Dict[str, List[float]]:
        """지표 데이터를 UI 형식으로 변환"""
        formatted = {}
        
        if hasattr(indicators, 'sma') and indicators.sma:
            formatted['SMA'] = indicators.sma
        if hasattr(indicators, 'rsi') and indicators.rsi:
            formatted['RSI'] = indicators.rsi
        if hasattr(indicators, 'macd') and indicators.macd:
            formatted['MACD'] = indicators.macd
            
        return formatted
```

### Step 2: UI 컴포넌트 리팩토링

#### 2.1 SimulationControlWidget 순수 View 변환
```python
# charts/simulation_control_widget.py (기존 파일 수정)
class SimulationControlWidget(QWidget):
    """시뮬레이션 컨트롤 UI - 순수 View (비즈니스 로직 제거)"""
    
    # 시그널 정의 (UI 이벤트 전달용)
    simulation_requested = pyqtSignal(str, int, list)  # scenario, length, indicators
    scenario_selection_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 어댑터 초기화 (비즈니스 로직 연결점)
        from ..adapters.backtesting_adapter import BacktestingAdapter
        self._adapter = BacktestingAdapter()
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """UI 요소 초기화 (기존 코드 유지)"""
        # 기존 UI 코드...
        pass
    
    def _connect_signals(self):
        """시그널 연결 (UI 이벤트 → 비즈니스 로직)"""
        self.run_button.clicked.connect(self._on_run_simulation)
        self.scenario_combo.currentTextChanged.connect(self.scenario_selection_changed)
    
    def _on_run_simulation(self):
        """시뮬레이션 실행 버튼 클릭 (View 역할만)"""
        scenario = self.scenario_combo.currentText()
        data_length = self.length_spinbox.value()
        indicators = self._get_selected_indicators()
        
        # 비즈니스 로직은 어댑터에 위임
        self.simulation_requested.emit(scenario, data_length, indicators)
    
    def update_results(self, results: Dict[str, Any]):
        """결과 업데이트 (View 업데이트만)"""
        if results.get('success', True):
            self._display_success_results(results)
        else:
            self._display_error_message(results.get('error', '알 수 없는 오류'))
    
    def _get_selected_indicators(self) -> List[str]:
        """선택된 지표 목록 반환 (UI 상태 읽기만)"""
        indicators = []
        if self.sma_checkbox.isChecked():
            indicators.append("SMA")
        if self.rsi_checkbox.isChecked():
            indicators.append("RSI")
        if self.macd_checkbox.isChecked():
            indicators.append("MACD")
        return indicators
```

#### 2.2 SimulationResultWidget 순수 View 변환
```python
# charts/simulation_result_widget.py (기존 파일 수정)  
class SimulationResultWidget(QWidget):
    """시뮬레이션 결과 표시 UI - 순수 View"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def display_results(self, results: Dict[str, Any]):
        """결과 표시 (데이터 렌더링만)"""
        try:
            # 가격 데이터 차트 업데이트
            self._update_price_chart(results.get('price_data', []))
            
            # 지표 차트 업데이트 
            indicators = results.get('indicators', {})
            self._update_indicator_charts(indicators)
            
            # 메타데이터 표시
            self._update_metadata_display(results)
            
        except Exception as e:
            self._display_error(f"결과 표시 중 오류: {e}")
    
    def _update_price_chart(self, price_data: List[float]):
        """가격 차트 업데이트 (순수 UI 로직)"""
        # 차트 그리기 로직...
        pass
    
    def _update_indicator_charts(self, indicators: Dict[str, List[float]]):
        """지표 차트 업데이트 (순수 UI 로직)"""
        # 지표별 차트 그리기...
        pass
    
    def _update_metadata_display(self, results: Dict[str, Any]):
        """메타데이터 표시 (순수 UI 로직)"""
        scenario = results.get('scenario', '')
        change_percent = results.get('change_percent', 0)
        
        self.scenario_label.setText(f"시나리오: {scenario}")
        self.change_label.setText(f"변화율: {change_percent:.2f}%")
```

### Step 3: 통합 컨트롤러 구현

#### 3.1 SimulationController 생성
```python
# controllers/simulation_controller.py (새로 생성)
class SimulationController:
    """시뮬레이션 UI와 서비스 사이의 컨트롤러"""
    
    def __init__(self, control_widget: SimulationControlWidget, 
                 result_widget: SimulationResultWidget):
        self.control_widget = control_widget
        self.result_widget = result_widget
        self.adapter = BacktestingAdapter()
        
        # UI 이벤트 연결
        self.control_widget.simulation_requested.connect(self._handle_simulation_request)
    
    def _handle_simulation_request(self, scenario: str, data_length: int, indicators: List[str]):
        """시뮬레이션 요청 처리 (컨트롤러 로직)"""
        try:
            # 진행 상황 표시
            self.control_widget.set_running_state(True)
            
            # 백테스팅 실행
            results = self.adapter.run_simulation(scenario, data_length, indicators)
            
            # 결과 표시
            self.result_widget.display_results(results)
            self.control_widget.update_results(results)
            
        except Exception as e:
            # 에러 처리
            error_results = {'success': False, 'error': str(e)}
            self.control_widget.update_results(error_results)
            
        finally:
            # UI 상태 복원
            self.control_widget.set_running_state(False)
```

## ✅ 완료 기준
- [ ] 어댑터 클래스 구현 완료 (BacktestingAdapter, ResultFormatter)
- [ ] UI 컴포넌트 순수 View 변환 완료
- [ ] 기존 UI 인터페이스 100% 호환성 유지
- [ ] 에러 처리 및 사용자 피드백 개선
- [ ] 통합 테스트 통과

## 📈 성공 지표
- **호환성**: 기존 UI 동작 100% 동일
- **응답성**: UI 응답 속도 기존 수준 유지
- **안정성**: 에러 발생 시 적절한 사용자 피드백
- **분리도**: UI 코드에서 비즈니스 로직 100% 제거

## 🧪 통합 테스트
```python
def test_ui_service_integration():
    """UI-서비스 통합 테스트"""
    # UI 컴포넌트 생성
    control_widget = SimulationControlWidget()
    result_widget = SimulationResultWidget()
    controller = SimulationController(control_widget, result_widget)
    
    # 시뮬레이션 실행
    control_widget.simulation_requested.emit("상승 추세", 100, ["SMA", "RSI"])
    
    # 결과 확인
    assert result_widget.isVisible()
    assert len(result_widget.price_data) > 0
```

## 🚨 주의사항
1. **호환성 유지**: 기존 UI 인터페이스 변경 금지
2. **성능**: UI 응답성 저하 방지
3. **에러 처리**: 모든 예외 상황 적절히 처리
4. **메모리**: UI 업데이트 시 메모리 누수 방지

## 🔗 연관 TASK
- **이전**: TASK-20250802-04 (단위 테스트 작성)
- **다음**: TASK-20250802-06 (통합 테스트 및 검증)

## 📝 산출물
1. **어댑터 클래스**: BacktestingAdapter, ResultFormatter 구현
2. **리팩토링된 UI**: 순수 View로 변환된 UI 컴포넌트
3. **컨트롤러**: UI-서비스 연결 컨트롤러
4. **통합 가이드**: UI 통합 과정 및 사용법 문서

---
**작업자**: GitHub Copilot
**생성일**: 2025년 8월 2일
**상태**: 계획됨
