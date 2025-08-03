# TASK-20250802-01: 아키텍처 리팩토링 Phase 1 사전 준비

## 📋 작업 개요
**목표**: Phase 1 백테스팅 로직 분리를 위한 사전 준비 및 안전 장치 구축
**우선순위**: CRITICAL
**예상 소요시간**: 2-3시간

## 🎯 작업 목표
- [ ] Git 백업 브랜치 생성 및 안전 지점 확보
- [ ] 현재 아키텍처 상태 정확한 분석 및 문서화
- [ ] business_logic 폴더 구조 생성
- [ ] 리팩토링 영향 범위 사전 파악

## 📊 현재 상황 분석

### 문제점 
- UI 폴더(`shared_simulation`)에 핵심 비즈니스 로직이 포함됨
- 백테스팅 엔진들이 UI 계층에 혼재되어 단위 테스트 불가능
- 비즈니스 로직과 UI 로직의 강한 결합

### 리팩토링 대상
```
현재: upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/engines/
├── simulation_engines.py                 # 통합 엔진 (분리 필요)
├── robust_simulation_engine.py           # 강화 엔진 (분리 필요)
├── real_data_simulation.py               # 실데이터 엔진 (분리 필요)
└── embedded_simulation_engine.py         # 내장 엔진 (분리 필요)

목표: upbit_auto_trading/business_logic/backtester/
├── engines/
│   ├── base_engine.py                    # 순수 비즈니스 로직
│   ├── data_engine.py                    # 데이터 처리 로직
│   └── calculation_engine.py             # 계산 로직
└── services/
    └── backtesting_service.py            # UI-비즈니스 연결점
```

## 🛠️ 세부 작업 단계

### Step 1: 백업 및 안전 지점 생성
```bash
# 1. 현재 상태 백업
git add .
git commit -m "Pre-refactoring checkpoint: Architecture Phase 1 preparation"
git checkout -b refactoring-phase1-backup

# 2. 작업 브랜치 생성
git checkout master
git checkout -b architecture-refactoring-phase1
```

### Step 2: 폴더 구조 생성
```bash
# business_logic 폴더 구조 생성
mkdir -p upbit_auto_trading/business_logic/backtester/engines
mkdir -p upbit_auto_trading/business_logic/backtester/services
mkdir -p upbit_auto_trading/business_logic/strategy
mkdir -p upbit_auto_trading/business_logic/portfolio
mkdir -p upbit_auto_trading/services
mkdir -p upbit_auto_trading/ui/desktop/controllers

# __init__.py 파일 생성
touch upbit_auto_trading/business_logic/__init__.py
touch upbit_auto_trading/business_logic/backtester/__init__.py
touch upbit_auto_trading/business_logic/backtester/engines/__init__.py
touch upbit_auto_trading/business_logic/backtester/services/__init__.py
touch upbit_auto_trading/business_logic/strategy/__init__.py
touch upbit_auto_trading/business_logic/portfolio/__init__.py
touch upbit_auto_trading/services/__init__.py
touch upbit_auto_trading/ui/desktop/controllers/__init__.py
```

### Step 3: 현재 상태 분석
```bash
# UI에 포함된 비즈니스 로직 파일 분석
find upbit_auto_trading/ui/ -name "*.py" -exec grep -l "class.*Engine\|def.*calculate\|def.*analyze" {} \;

# 의존성 관계 분석
grep -r "from.*shared_simulation" upbit_auto_trading/
grep -r "import.*shared_simulation" upbit_auto_trading/

# 테스트 파일 현황
find tests/ -name "*.py" | wc -l
ls -la tests/
```

## ✅ 완료 기준
- [ ] 백업 브랜치 생성 완료 (`refactoring-phase1-backup`)
- [ ] 작업 브랜치 생성 완료 (`architecture-refactoring-phase1`)
- [ ] business_logic 폴더 구조 생성 완료
- [ ] 현재 UI 의존성 분석 보고서 생성
- [ ] 리팩토링 영향 범위 문서화

## 🚨 리스크 및 주의사항
1. **데이터 손실 방지**: 모든 작업 전 Git 커밋 필수
2. **의존성 순환 참조**: 기존 import 구조 면밀히 분석
3. **기능 회귀**: 각 단계별 기능 동작 확인

## 📈 성공 지표
- Git 백업 완료: 100%
- 폴더 구조 생성: 100%
- 의존성 분석 완료: 100%
- 문서화 완료: 100%

## 🔗 연관 TASK
- **다음**: TASK-20250802-02 (백테스팅 엔진 분석 및 추출)
- **관련**: architecture_analysis_and_solution.py, refactoring_execution_plan.py

## 📝 비고
- 이 작업은 모든 후속 리팩토링의 기반이 되므로 신중하게 진행
- 백업 브랜치는 리팩토링 실패 시 안전한 롤백 지점 역할
- 현재 상태 분석 결과는 Phase 2-4 계획에도 활용

---
**작업자**: GitHub Copilot
**생성일**: 2025년 8월 2일
**상태**: 계획됨
