# 📋 TASK-20250802-11: 트리거 빌더 아키텍처 분석 및 설계

## 🎯 **작업 개요**
trigger_builder_screen.py(1642줄)의 비즈니스 로직을 체계적으로 분석하고, business_logic 계층 분리를 위한 상세 설계를 수립합니다.

## 📊 **현재 상황 분석**

### **핵심 파일 현황**
```
🎯 분석 대상 파일들:
├── trigger_builder_screen.py (1642줄) - 메인 UI + 비즈니스 로직 혼재
├── components/shared/trigger_calculator.py (312줄) - 순수 계산 로직
├── components/shared/trigger_simulation_service.py (374줄) - 시뮬레이션 서비스
├── components/core/condition_builder.py (342줄) - 조건 생성 로직
└── shared_simulation/charts/ - 미니차트 시스템 (3개 파일)
```

### **비즈니스 로직 분포 현황**
```
📊 trigger_builder_screen.py 내 계산 메서드:
├── _calculate_variable_data() → 지표 계산 핵심 (라인 867)
├── _calculate_sma() → SMA 계산 (라인 937)
├── _calculate_ema() → EMA 계산 (라인 941) 
├── _calculate_rsi() → RSI 계산 (라인 945)
├── _calculate_macd() → MACD 계산 (라인 949)
├── _calculate_cross_trigger_points() → 크로스 신호 (라인 959)
└── calculate_trigger_points() → 트리거 포인트 (라인 1146)
```

## 🏗️ **새로운 아키텍처 설계**

### **Phase 1: business_logic 폴더 구조**
```
upbit_auto_trading/business_logic/
├── triggers/
│   ├── __init__.py
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── technical_indicator_calculator.py   # SMA, EMA, RSI, MACD 계산
│   │   ├── trigger_point_detector.py           # 트리거 포인트 감지
│   │   └── cross_signal_analyzer.py            # 크로스 신호 분석
│   ├── models/
│   │   ├── __init__.py
│   │   ├── trigger_condition_model.py          # 트리거 조건 모델
│   │   ├── variable_data_model.py              # 변수 데이터 모델
│   │   └── trigger_result_model.py             # 트리거 결과 모델
│   └── services/
│       ├── __init__.py
│       ├── trigger_orchestration_service.py    # 메인 트리거 서비스
│       └── condition_management_service.py     # 조건 관리 서비스
├── conditions/
│   ├── __init__.py
│   ├── builders/
│   │   ├── __init__.py
│   │   ├── condition_factory.py                # 조건 객체 팩토리
│   │   └── execution_code_generator.py         # 실행 코드 생성
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── compatibility_checker.py            # 호환성 검증
│   │   └── parameter_validator.py              # 파라미터 검증
│   └── services/
│       ├── __init__.py
│       ├── condition_crud_service.py           # 조건 CRUD 서비스
│       └── variable_definition_service.py      # 변수 정의 서비스
└── visualization/
    ├── __init__.py
    ├── engines/
    │   ├── __init__.py
    │   ├── chart_data_engine.py                # 차트 데이터 생성
    │   └── indicator_rendering_engine.py       # 지표 렌더링
    ├── models/
    │   ├── __init__.py
    │   ├── chart_configuration_model.py        # 차트 설정 모델
    │   └── chart_data_model.py                 # 차트 데이터 모델
    └── services/
        ├── __init__.py
        ├── minichart_orchestration_service.py  # 미니차트 메인 서비스
        └── chart_theme_service.py              # 차트 테마 관리
```

### **Phase 2: UI 어댑터 구조**
```
upbit_auto_trading/ui/desktop/adapters/
├── __init__.py
├── trigger_builder_adapter.py                  # 트리거 빌더 UI 어댑터
├── minichart_ui_adapter.py                     # 미니차트 UI 어댑터
└── condition_management_adapter.py             # 조건 관리 UI 어댑터
```

## 🔄 **마이그레이션 맵핑**

### **기존 → 새로운 구조 맵핑**
```
📁 기존 파일 → 새로운 위치

trigger_builder_screen.py:
├── _calculate_variable_data() → technical_indicator_calculator.py
├── _calculate_sma() → technical_indicator_calculator.py
├── _calculate_ema() → technical_indicator_calculator.py  
├── _calculate_rsi() → technical_indicator_calculator.py
├── _calculate_macd() → technical_indicator_calculator.py
├── calculate_trigger_points() → trigger_point_detector.py
└── _calculate_cross_trigger_points() → cross_signal_analyzer.py

components/shared/trigger_calculator.py → 
└── technical_indicator_calculator.py (통합)

components/shared/trigger_simulation_service.py → 
└── trigger_orchestration_service.py (개선)

components/core/condition_builder.py → 
├── condition_factory.py
└── execution_code_generator.py

shared_simulation/charts/ → 
└── business_logic/visualization/ (서비스 분리)
```

### **인터페이스 호환성 보장**
```python
# trigger_builder_screen.py 변경 전략
class TriggerBuilderScreen(QWidget):
    def __init__(self):
        super().__init__()
        
        # ✅ 기존 UI 유지하면서 서비스 계층 도입
        from upbit_auto_trading.ui.desktop.adapters.trigger_builder_adapter import TriggerBuilderAdapter
        self._adapter = TriggerBuilderAdapter()
    
    def _calculate_variable_data(self, variable_name, price_data, custom_parameters=None):
        """기존 메서드 시그니처 유지 - 어댑터로 위임"""
        return self._adapter.calculate_variable_data(
            variable_name, price_data, custom_parameters
        )
```

## 📋 **상세 작업 내용**

### **1. 아키텍처 분석 (3시간)**
- [ ] trigger_builder_screen.py 메서드별 의존성 분석
- [ ] 기존 components 폴더 구조 분석
- [ ] 외부 라이브러리 의존성 맵핑 (numpy, pandas, matplotlib)
- [ ] PyQt6 UI 의존성 식별

### **2. 비즈니스 로직 분류 (2시간)**
- [ ] 계산 로직 vs UI 로직 분리
- [ ] 재사용 가능한 컴포넌트 식별
- [ ] 공통 인터페이스 설계

### **3. 새로운 폴더 구조 생성 (1시간)**
```powershell
# business_logic 폴더 구조 생성
New-Item -ItemType Directory -Path "upbit_auto_trading\business_logic\triggers\engines" -Force
New-Item -ItemType Directory -Path "upbit_auto_trading\business_logic\triggers\models" -Force
New-Item -ItemType Directory -Path "upbit_auto_trading\business_logic\triggers\services" -Force
New-Item -ItemType Directory -Path "upbit_auto_trading\business_logic\conditions\builders" -Force
New-Item -ItemType Directory -Path "upbit_auto_trading\business_logic\conditions\validators" -Force
New-Item -ItemType Directory -Path "upbit_auto_trading\business_logic\conditions\services" -Force
New-Item -ItemType Directory -Path "upbit_auto_trading\business_logic\visualization\engines" -Force
New-Item -ItemType Directory -Path "upbit_auto_trading\business_logic\visualization\models" -Force
New-Item -ItemType Directory -Path "upbit_auto_trading\business_logic\visualization\services" -Force
New-Item -ItemType Directory -Path "upbit_auto_trading\ui\desktop\adapters" -Force
```

### **4. 기본 __init__.py 파일 생성 (1시간)**
- [ ] 모든 새로운 패키지에 __init__.py 생성
- [ ] 기본 import 구조 설정
- [ ] 순환 참조 방지 설계

### **5. 인터페이스 설계 문서 작성 (2시간)**
- [ ] 각 서비스 클래스의 public 메서드 정의
- [ ] 모델 클래스의 속성 및 메서드 정의
- [ ] 어댑터 클래스의 변환 로직 설계

## ✅ **완료 기준**

### **산출물**
- [ ] 상세 아키텍처 설계 문서
- [ ] 마이그레이션 맵핑 테이블
- [ ] business_logic 폴더 구조 생성 완료
- [ ] 인터페이스 설계 문서

### **검증 기준**
- [ ] 기존 기능 100% 호환성 보장 설계
- [ ] UI 의존성 완전 분리 설계
- [ ] 테스트 가능한 구조 설계
- [ ] 순환 참조 없는 깔끔한 의존성 구조

## 🔗 **다음 단계**
- **TASK-20250802-12**: 기술 지표 계산 엔진 구현
- **관련 문서**: TRIGGER_BUILDER_MASTER_REFACTORING_PLAN.md

## 📊 **예상 소요 시간**
- **총 소요 시간**: 9시간
- **우선순위**: CRITICAL
- **복잡도**: MEDIUM
- **리스크**: LOW (분석 및 설계 단계)

---
**작성일**: 2025년 8월 2일  
**담당자**: GitHub Copilot  
**문서 타입**: 아키텍처 분석 및 설계
