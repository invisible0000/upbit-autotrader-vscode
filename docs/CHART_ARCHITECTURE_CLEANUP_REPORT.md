# 차트 아키텍처 정리 보고서

## 📋 개요
트리거 빌더 화면의 차트 기능을 엄밀하게 분석하고 사용되지 않는 코드를 정리했습니다.

## 🔍 분석 결과

### ✅ **진짜 차트**: SimulationResultWidget
**위치**: `upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/components/core/simulation_result_widget.py`

**증거**:
1. **실제 데이터 소스 연동**: 
   - `get_trigger_simulation_service()` 서비스 사용
   - 실제 market data와 trigger calculator 연동

2. **실제 시뮬레이션 결과 처리**:
   ```python
   chart_data = {
       'scenario': result.scenario,
       'price_data': result.price_data,           # 실제 가격 데이터
       'base_variable_data': result.base_variable_data,  # 실제 계산된 변수 데이터  
       'external_variable_data': result.external_variable_data,
       'trigger_points': result.trigger_points,   # 실제 트리거 발동 지점
   }
   ```

3. **UI 연결**:
   - `_process_simulation_result()` → `simulation_result_widget.update_chart_with_simulation_results()`
   - 스크린샷의 우측 하단 "시뮬레이션 결과 미니차트" 박스에 위치

### ❌ **가짜 차트**: MiniChartWidget (제거됨)
**문제점**:
1. **인스턴스화되지 않음**: 어디서도 `MiniChartWidget()` 호출하지 않음
2. **연결되지 않은 메서드**: `update_chart_with_simulation_data()` 호출되지 않음
3. **UI에 추가되지 않음**: 어떤 레이아웃에도 추가되지 않음
4. **죽은 코드**: 203줄의 사용되지 않는 코드

## 🧹 정리 작업

### 제거된 코드
- `MiniChartWidget` 클래스 전체 (203줄)
- 불필요한 matplotlib import (`Figure`, `FigureCanvas`)
- 중복된 import 문

### 유지된 구조
```
TriggerBuilderScreen
├── create_test_result_area()
│   └── SimulationResultWidget()               # 진짜 차트
│       ├── create_mini_chart_widget()
│       └── update_chart_with_simulation_results()
├── run_simulation()                           # 실제 시뮬레이션 실행
└── _process_simulation_result()               # 결과 처리 및 차트 업데이트
```

## 📊 시뮬레이션 데이터 플로우

```
1. 사용자 시뮬레이션 버튼 클릭
   ↓
2. run_simulation() 호출
   ↓
3. get_trigger_simulation_service().run_simulation()
   ↓
4. 실제 market data + trigger calculator 연산
   ↓
5. _process_simulation_result()
   ↓
6. simulation_result_widget.update_chart_with_simulation_results()
   ↓
7. 스크린샷의 우측 하단 차트에 실제 결과 표시
```

## ✅ 검증 완료

1. **UI 구조 일치**: 스크린샷의 단일 미니차트 = SimulationResultWidget 차트
2. **데이터 소스 연동**: 실제 시뮬레이션 서비스와 연결
3. **트리거 계산**: 실제 trigger calculator 사용
4. **코드 정리**: 203줄의 죽은 코드 제거

## 🎯 결론

트리거 빌더의 차트 기능은 이제 명확하고 단순한 구조를 가지게 되었습니다:
- **하나의 진짜 차트**: SimulationResultWidget 내부
- **실제 데이터 연동**: 시뮬레이션 서비스 + 트리거 계산기
- **UI 위치**: 우측 하단 "시뮬레이션 결과 미니차트" 박스

이제 차트 기능의 확장이나 디버깅이 훨씬 명확해졌습니다.
