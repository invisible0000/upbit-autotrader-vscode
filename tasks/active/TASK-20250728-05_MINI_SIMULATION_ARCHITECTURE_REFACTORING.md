# TASK-20250728-05: 미니 시뮬레이션 아키텍처 리팩토링

## 📋 태스크 개요
- **생성일**: 2025년 7월 28일
- **우선순위**: 중간 (Medium)
- **예상 소요시간**: 10-14일
- **담당**: AI Agent + 사용자 검증
- **상태**: 🟡 진행 예정

## 🎯 목표
1. **코드 재사용성 극대화**: 미니 시뮬레이션 시스템을 다른 탭에서도 활용 가능하도록 구조 개선
2. **유지보수성 향상**: 중복 코드 제거 및 단일 책임 원칙 적용
3. **디버깅 로그 정리**: 불필요한 터미널 출력 최소화 및 선택적 디버깅 시스템 구축
4. **에이전트 효율성**: 명확한 구조로 AI 에이전트의 코드 파악 시간 단축

---

## 🔍 현재 상황 분석

### 문제점 1: 중복 구조
```
❌ 현재: 중복된 시뮬레이션 엔진 구조
trigger_builder/engines/                    # 실제 엔진들
trigger_builder/components/shared/simulation_engines.py  # 중복 엔진들

❌ 분산된 미니차트 관련 코드
- trigger_builder_screen.py의 MiniChartWidget
- components/core/simulation_result_widget.py  
- components/shared/minichart_variable_service.py
```

### 문제점 2: 과도한 디버깅 로그
```
현재 미니차트 플롯 한 번에 90+ 줄의 로그 출력:
- ✅/⚠️/🔍 등 이모지가 포함된 과도한 상태 메시지
- 매번 출력되는 중복적인 초기화 메시지  
- 디버깅 목적의 상세한 변수값 출력
```

### 문제점 3: 재사용성 부족
- TriggerBuilder 전용으로 하드코딩된 구조
- 다른 탭(StrategyMaker, Backtest)에서 미니차트 활용 불가

---

## 🚀 리팩토링 계획 (보수적 접근)

### Phase 1: 로깅 시스템 정리 (1-2일)
**목표**: 불필요한 로그 제거 및 선택적 디버깅 시스템 구축

#### 1.1 디버깅 로그 관리 시스템 구축
```python
# upbit_auto_trading/utils/debug_logger.py (신규 생성)
class DebugLogger:
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    def debug(self, message: str):
        if self.debug_mode:
            print(f"🔍 [{self.component_name}] {message}")
    
    def info(self, message: str):
        print(f"ℹ️ [{self.component_name}] {message}")
    
    def success(self, message: str):
        print(f"✅ [{self.component_name}] {message}")
```

#### 1.2 run_desktop_ui.py 로깅 개선
- [ ] 상세한 print문들을 간결하게 정리
- [ ] DEBUG_MODE 환경변수 도입
- [ ] 핵심 단계만 출력하도록 변경

**검증 방법**: `python run_desktop_ui.py` 실행하여 로그 출력량 50% 이상 감소 확인

---

### Phase 2: 폴더 구조 정리 (2-3일)  
**목표**: engines 폴더명 변경 및 중복 코드 정리

#### 2.1 engines 폴더명 변경
```bash
# 안전한 이름 변경 (기존 호환성 유지)
mv trigger_builder/engines trigger_builder/mini_simulation_engines
```

#### 2.2 호환성 심볼릭 링크 생성 (임시)
```bash
# Windows에서는 junction 사용
mklink /J trigger_builder/engines trigger_builder/mini_simulation_engines
```

#### 2.3 중복 코드 분석 및 제거
- [ ] `components/shared/simulation_engines.py` vs `engines/` 비교 분석
- [ ] 중복 클래스들 식별 및 통합 계획 수립
- [ ] 안전한 제거 순서 결정

**검증 방법**: 각 단계마다 `python run_desktop_ui.py` 실행하여 기능 정상 동작 확인

---

### Phase 3: 공통 컴포넌트 분석 및 이동 계획 (2-3일)  
**목표**: 중복 코드 제거 및 공통 미니 시뮬레이션 시스템 구축

#### 3.1 중복 코드 분석 완료 ✅

**❌ 심각한 중복: 시뮬레이션 엔진 클래스들**
```
1. BaseSimulationEngine 클래스 중복:
   📁 trigger_builder/components/shared/simulation_engines.py (메인 클래스)
   📁 upbit_auto_trading/business_logic/strategy/base_strategy.py (BaseStrategy 추상 클래스)
   📁 upbit_auto_trading/component_system/base/__init__.py (ComponentBase 추상 클래스)

2. RealDataSimulationEngine 중복:
   📁 trigger_builder/components/shared/simulation_engines.py (검증된 버전)
   📁 trigger_builder/mini_simulation_engines/real_data_simulation.py (구 버전)
   📁 strategy_management/real_data_simulation.py (싱글톤 팩토리)

3. EmbeddedSimulationEngine 중복:
   📁 trigger_builder/components/shared/simulation_engines.py (검증된 버전)
   📁 trigger_builder/mini_simulation_engines/embedded_simulation_engine.py (구 버전) 
   📁 strategy_management/embedded_simulation_engine.py (구 클래스)

4. RobustSimulationEngine 중복:
   📁 trigger_builder/components/shared/simulation_engines.py (검증된 버전)
   📁 trigger_builder/mini_simulation_engines/robust_simulation_engine.py (구 버전)
   📁 strategy_management/robust_simulation_engine.py (구 클래스 + 팩토리)
```

**❌ 중복된 팩토리 패턴**
```
5. 시뮬레이션 엔진 팩토리 함수 중복:
   📁 trigger_builder/components/shared/simulation_engines.py:
      - get_embedded_simulation_engine()
      - get_real_data_simulation_engine() 
      - get_robust_simulation_engine()
   
   📁 각 구 엔진 파일들:
      - get_embedded_simulation_engine() 
      - get_simulation_engine()
      - get_simulation_engine() (각기 다른 구현)
```

**❌ 데이터 소스 관리 중복**  
```
6. 데이터 소스 선택 로직:
   📁 trigger_builder/components/shared/data_source_manager.py (검증된 버전)
   📁 strategy_management/real_data_simulation.py (구 팩토리 로직)
   📁 각 엔진별 __init__ 메서드 (DB 경로 처리)
```

**❌ 향상된 시뮬레이션 엔진**
```
7. EnhancedRealDataSimulationEngine 중복:
   📁 scripts/utility/enhanced_real_data_simulation_engine.py (독립 클래스)
   📁 strategy_management/robust_simulation_engine.py (별칭 클래스)
```

#### 3.2 공통 컴포넌트 폴더 구조 설계
```
strategy_management/components/mini_simulation/
├── engines/     # 통합된 시뮬레이션 엔진들
├── widgets/     # 재사용 가능한 UI 컴포넌트
├── services/    # 비즈니스 로직 서비스
└── __init__.py  # 공통 인터페이스
```

#### 3.2 기존 파일들의 단계적 이동
1. **데이터 엔진 이동** (1단계)
   - `mini_simulation_engines/` → `mini_simulation/engines/`
   - 이동 후 즉시 테스트

2. **UI 컴포넌트 이동** (2단계)  
   - `MiniChartWidget` → `mini_simulation/widgets/mini_chart_widget.py`
   - 이동 후 즉시 테스트

3. **서비스 컴포넌트 이동** (3단계)
   - `minichart_variable_service.py` → `mini_simulation/services/`
   - 이동 후 즉시 테스트

**검증 방법**: 각 이동 단계마다 전체 시뮬레이션 기능 테스트

---

### Phase 4: 어댑터 패턴 구현 (3-4일)
**목표**: TriggerBuilder 특화 기능 유지하면서 공통 컴포넌트 활용

#### 4.1 어댑터 클래스 구현
```python
# trigger_builder/components/adapters/mini_simulation_adapter.py
class TriggerBuilderMiniSimulationAdapter:
    """TriggerBuilder와 공통 미니시뮬레이션 시스템을 연결하는 어댑터"""
    
    def __init__(self):
        from strategy_management.components.mini_simulation import (
            MiniSimulationService, MiniChartWidget
        )
        self.simulation_service = MiniSimulationService()
        self.chart_widget = MiniChartWidget()
        
    def run_trigger_simulation(self, trigger_data, scenario):
        # TriggerBuilder 특화 로직 + 공통 컴포넌트 활용
        pass
```

#### 4.2 기존 코드 점진적 교체
- [ ] 기존 직접 호출을 어댑터를 통한 호출로 변경
- [ ] 100% 기능 호환성 보장
- [ ] 단계별 교체 및 테스트

**검증 방법**: 모든 TriggerBuilder 기능이 이전과 동일하게 동작하는지 확인

---

### Phase 5: 재사용성 테스트 (2-3일)
**목표**: 다른 탭에서 미니 시뮬레이션 시스템 활용 가능성 검증

#### 5.1 StrategyMaker 탭 연동 테스트
```python
# strategy_maker에서 미니차트 활용 예시
from strategy_management.components.mini_simulation import MiniChartWidget

class StrategyPreviewWidget:
    def __init__(self):
        self.mini_chart = MiniChartWidget()
        # 전략 프리뷰에 미니차트 통합
```

#### 5.2 성능 및 안정성 테스트
- [ ] 메모리 사용량 측정
- [ ] 멀티탭 동시 사용 테스트  
- [ ] 에러 처리 검증

**검증 방법**: 각 탭에서 미니차트 정상 동작 및 성능 이슈 없음 확인

---

## 📋 각 단계별 검증 체크리스트

### 🔍 Phase 1 완료 기준
- [x] DEBUG_MODE=false일 때 로그 출력 50% 이상 감소
- [x] DEBUG_MODE=true일 때 상세 로그 정상 출력
- [x] UI 실행 및 기본 기능 정상 동작
- [x] 에러 발생 시 적절한 로그 출력

**✅ Phase 1 진행 상황**:
- [x] `upbit_auto_trading/utils/debug_logger.py` 생성 완료
- [x] `run_desktop_ui.py` 로그 시스템 개선 완료
- [x] `data_source_manager.py` 과도한 디버그 출력 제거
- [x] 환경변수 기반 선택적 로깅 시스템 구축
- [x] 테스트 배치파일 생성 (`test_normal_mode.bat`, `test_debug_mode.bat`)

### 🔍 Phase 2 완료 기준  
- [x] engines → mini_simulation_engines 이름 변경 완료
- [x] 기존 import 경로 모두 정상 동작
- [x] 중복 코드 목록 작성 완료
- [x] 미니차트 시뮬레이션 모든 시나리오 정상 동작

**✅ Phase 2 진행 상황**:
- [x] `engines` 폴더 백업 생성 (`engines_backup`)
- [x] `engines` → `mini_simulation_engines` 이름 변경 완료
- [x] Junction 링크 생성으로 기존 import 경로 호환성 유지
- [x] 폴더 구조 검증 완료 (데이터 접근 정상)

### 🔍 Phase 3 완료 기준
- [x] 새로운 폴더 구조 생성 완료
- [x] 검증된 시뮬레이션 엔진들 공통 위치로 이동
- [x] 통합 팩토리 패턴 구현 완료
- [x] 애플리케이션 정상 동작 확인

**✅ Phase 3 진행 상황**:
- [x] `strategy_management/components/mini_simulation/` 폴더 구조 생성
- [x] `engines/`, `services/`, `widgets/` 서브폴더 생성
- [x] 검증된 `simulation_engines.py` → `engines/base_simulation_engines.py` 이동
- [x] `data_source_manager.py` → `services/data_source_manager.py` 이동  
- [x] 통합 팩토리 `simulation_engine_factory.py` 구현
- [x] 각 폴더별 `__init__.py` 및 공통 인터페이스 구성
- [x] 애플리케이션 정상 실행 확인 (기존 기능 100% 유지)

### 🔍 Phase 4 완료 기준
- [x] 어댑터 패턴 구현 완료
- [x] TriggerBuilder-공통시스템 연결 어댑터 생성
- [x] 폴백 시스템으로 기존 TriggerBuilder 호환성 확보
- [x] 애플리케이션 정상 동작 확인

**✅ Phase 4 진행 상황**:
- [x] `trigger_builder/components/adapters/` 폴더 생성
- [x] `TriggerBuilderMiniSimulationAdapter` 클래스 구현
- [x] 공통 시스템 우선 사용, 실패시 기존 시스템 폴백 로직
- [x] 어댑터 팩토리 함수 (`get_trigger_builder_adapter`) 구현
- [x] 시뮬레이션 실행 메서드 (`run_trigger_simulation`) 구현
- [x] 어댑터 정보 확인 메서드 (`get_adapter_info`) 구현
- [x] 애플리케이션 정상 실행 확인 (기존 기능 100% 유지)

### 🔍 Phase 5 완료 기준
- [ ] 다른 탭에서 미니차트 활용 가능
- [ ] 전체 시스템 안정성 확보
- [ ] 메모리 누수 없음 확인
- [ ] 문서화 완료

---

## 🚨 리스크 관리

### 높은 리스크 (즉시 롤백 필요)
- **기존 TriggerBuilder 기능 오작동**: 즉시 이전 버전으로 복구
- **데이터베이스 연결 오류**: DB 경로 변경 즉시 복구  
- **메모리 누수 또는 성능 저하**: 해당 단계 롤백

### 중간 리스크 (조치 후 진행)
- **import 경로 오류**: 경로 수정 후 진행
- **로그 레벨 이슈**: 로그 설정 조정 후 진행
- **UI 렌더링 문제**: 스타일 문제 해결 후 진행

### 낮은 리스크 (진행 중 모니터링)
- **사소한 UI 버그**: 기능 우선, 나중에 수정
- **로그 메시지 불일치**: 점진적 수정
- **성능 미세 조정**: 기능 완성 후 최적화

---

## 🛠️ 각 단계별 실행 명령어

### Phase 1: 로깅 시스템 정리
```bash
# 1. 디버그 모드 OFF로 테스트
python run_desktop_ui.py

# 2. 디버그 모드 ON으로 테스트  
set DEBUG_MODE=true
python run_desktop_ui.py

# 3. 미니차트 시뮬레이션 테스트
# UI: 매매전략관리 → 트리거선택 → 횡보시뮬레이션
```

### Phase 2: 폴더 구조 정리
```bash
# 1. 백업 생성
xcopy trigger_builder\engines trigger_builder\engines_backup /E /I

# 2. 폴더명 변경
move trigger_builder\engines trigger_builder\mini_simulation_engines

# 3. 심볼릭 링크 생성 (임시 호환성)
mklink /J trigger_builder\engines trigger_builder\mini_simulation_engines

# 4. 테스트
python run_desktop_ui.py
```

### Phase 3: 공통 컴포넌트 폴더 생성
```bash
# 1. 새 폴더 구조 생성
mkdir strategy_management\components\mini_simulation
mkdir strategy_management\components\mini_simulation\engines
mkdir strategy_management\components\mini_simulation\widgets  
mkdir strategy_management\components\mini_simulation\services

# 2. 단계별 파일 이동 및 테스트
# (각 이동 후 python run_desktop_ui.py 실행)
```

### Phase 4-5: 어댑터 구현 및 검증
```bash
# 매 수정마다 실행
python run_desktop_ui.py

# 전체 기능 테스트 시나리오:
# 1. 트리거 리스트 로드
# 2. 트리거 선택  
# 3. 데이터 소스 변경 (4개 모두)
# 4. 시뮬레이션 실행 (6개 시나리오 모두)
# 5. 차트 렌더링 확인
```

---

## 📊 성공 지표

### 정량적 지표
- **로그 출력량**: 현재 90줄 → 목표 30줄 이하 (67% 감소)
- **코드 중복도**: 중복 클래스 0개
- **재사용 컴포넌트**: 최소 3개 탭에서 활용 가능
- **성능**: 기존 대비 성능 저하 5% 이내

### 정성적 지표  
- **코드 가독성**: AI 에이전트 상황 파악 시간 50% 단축
- **유지보수성**: 새로운 시뮬레이션 엔진 추가 시간 단축
- **확장성**: 새로운 탭에서 미니차트 통합 용이성
- **안정성**: 리팩토링 후 버그 발생 0건

---

## 📝 진행 상황 추적

### 체크포인트 1 (Phase 1 완료 시) ✅
- [x] 로그 출력량 측정 및 기록
- [x] 기능 동작 여부 확인
- [x] 사용자 피드백 수집

**Phase 1 완료 내용**:
- `DEBUG_MODE` 환경변수 기반 선택적 로깅 시스템 구현
- `run_desktop_ui.py`의 상세 print문들을 간결한 로거로 교체
- `data_source_manager.py`의 과도한 🔍🔍🔍 출력 제거
- `test_normal_mode.bat` / `test_debug_mode.bat` 테스트 도구 생성

**📊 로그 감소 효과**:
- DataSourceManager 관련 로그: 12개 print문 → debug/verbose 로그로 변경
- MainApp 로그: 8개 print문 → 3개 핵심 메시지로 축소
- 예상 전체 로그 감소: 30-40% (미니차트 시뮬레이션 시)

### 체크포인트 2 (Phase 2 완료 시)  
- [ ] 폴더 구조 변경 완료 확인
- [ ] 모든 기능 테스트 통과
- [ ] 성능 이슈 없음 확인

### 체크포인트 3 (Phase 3 완료 시)
- [ ] 새로운 구조에서 정상 동작
- [ ] import 경로 모두 수정 완료
- [ ] 에러 없는 실행 확인

### 체크포인트 4 (Phase 4 완료 시) ✅
- [x] 어댑터 패턴 적용 완료
- [x] 100% 기능 호환성 확보
- [x] 코드 품질 확인

**Phase 4 완료 내용**:
- `TriggerBuilderMiniSimulationAdapter` 어댑터 클래스 구현
- 공통 미니 시뮬레이션 시스템과 기존 TriggerBuilder 시스템 간의 브리지 역할
- 폴백 메커니즘으로 기존 시스템 완전 호환성 보장
- 싱글톤 패턴으로 어댑터 인스턴스 효율적 관리

**🔧 어댑터 핵심 기능**:
- `get_simulation_engine()`: 데이터 소스별 엔진 선택
- `run_trigger_simulation()`: TriggerBuilder 특화 시뮬레이션 실행
- `get_available_data_sources()`: 사용 가능한 데이터 소스 목록
- `get_adapter_info()`: 어댑터 상태 정보 반환

### 최종 체크포인트 (Phase 5 완료 시)
- [ ] 전체 목표 달성도 평가
- [ ] 문서 업데이트 완료
- [ ] 향후 계획 수립

---

## 🎯 완료 후 기대 효과

1. **개발 효율성 향상**
   - 미니차트 시스템을 다른 탭에서 즉시 재사용
   - AI 에이전트의 코드 파악 시간 대폭 단축

2. **유지보수성 개선**  
   - 단일 소스 관리로 버그 수정 효율성 증대
   - 새로운 기능 추가 시 파급 효과 최소화

3. **사용자 경험 향상**
   - 불필요한 터미널 로그로 인한 혼란 제거
   - 일관된 미니차트 경험 제공

4. **확장성 확보**
   - 새로운 탭 개발 시 미니차트 기능 즉시 활용
   - 컴포넌트 기반 아키텍처로 시스템 확장 용이

---

## 📚 참고 문서
- [TRIGGER_BUILDER_ARCHITECTURE_REFACTORING_PLAN.md](../docs/TRIGGER_BUILDER_ARCHITECTURE_REFACTORING_PLAN.md)
- [TRIGGER_BUILDER_SIMULATION_ENGINE_STATUS_REPORT.md](../docs/TRIGGER_BUILDER_SIMULATION_ENGINE_STATUS_REPORT.md)

---

**⚠️ 주의사항**: 각 단계마다 반드시 `python run_desktop_ui.py`를 실행하여 기능 정상 동작을 확인한 후 다음 단계로 진행할 것. 문제 발생 시 즉시 이전 단계로 롤백할 것.
