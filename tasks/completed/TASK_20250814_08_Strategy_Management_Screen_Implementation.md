# 📋 TASK_20250814_08: 트리거 빌더 시스템 재구현

## 🚀 **현재 진행 상황 (2025-08-15 업데이트)**
- ✅ **Phase 1 (Domain Layer)**: 완료 - TradingVariable Entity, Value Objects, Domain Services
- ✅ **Phase 2 (Infrastructure Layer)**: 완료 - SQLite Repository, Database 통합
- ✅ **Phase 3 (Application Layer)**: 완료 - UseCases, DTOs, 비즈니스 로직
- 🔄 **다음 단계**: Phase 4 (UI Layer) - 재사용 가능한 컨디션 빌더 UI 구현
- 📊 **테스트 현황**: 91개 테스트 모두 통과 ✅

## 🎯 목표
트리거 빌더의 핵심 기능을 중심으로 한 단계별 구현
**컨디션(변수/지표) → 트리거 → 전략 → 포지션** 순서로 체계적 구축
기존 백업 시스템을 DDD + MVP + TDD 패턴으로 현대화

---

## 📊 작업 우선순위 및 범위
1. **컨디션 빌더** (최우선) - 변수와 지표를 조합한 거래 조건 생성기
2. **트리거 빌더** (핵심) - 컨디션들을 조합한 트리거 생성 시스템
3. **전략 메이커** (통합) - 트리거들을 조합한 완전한 전략 구성기
4. **포지션 준비** (실행) - 전략을 실제 거래로 연결하는 시스템

**현재 집중 대상**: 트리거 빌더 (매우 복잡한 UI + 다양한 기능)

---

## 🔄 재사용 가능 컴포넌트 설계 전략

### 🎯 **재사용 시나리오 분석**
1. **컨디션 빌더**:
   - 트리거 빌더: 임베딩 형태 (좌측 영역)
   - 전략 메이커: 다이얼로그 형태 (조건 수정 시)
   - 스크리너: 임베딩 형태 (필터 조건 설정)

2. **미니 차트 + 시뮬레이터**:
   - 트리거 빌더: 우측 영역 (중간 크기)
   - 전략 메이커: 우측 하단 (작은 크기)
   - 대시보드: 여러 위치 (다양한 크기)

3. **변수/파라미터 시스템**:
   - 모든 화면에서 공통 사용
   - 일관된 UI/UX 필요

### 🏗️ **컴포넌트 아키텍처 설계 원칙**
```
📦 Reusable Components
├── 🧩 Core Components (MVP 기반)
│   ├── ConditionBuilder (Widget + Dialog 모드)
│   ├── MiniChartSimulator (크기 조절 가능)
│   ├── VariableSelector (공통 인터페이스)
│   └── ParameterInput (동적 생성)
├── 🎛️ Interface Adapters
│   ├── EmbeddedModeAdapter
│   ├── DialogModeAdapter
│   └── CompactModeAdapter
└── 🔧 Shared Services
    ├── ComponentStateManager
    ├── ResizeableLayoutManager
    └── ContextSwitchingService
```

---

## 🔧 트리거 빌더 시스템 분석

### 🧩 핵심 컴포넌트 (기존 백업에서 확인)
```
trigger_builder/
├── trigger_builder_screen.py (1616 lines) - 메인 화면
├── components/core/ - 핵심 8개 컴포넌트
│   ├── condition_dialog.py - 조건 생성/편집 다이얼로그
│   ├── condition_storage.py - 조건 저장/로드 관리
│   ├── trigger_list_widget.py - 트리거 목록 관리
│   ├── trigger_detail_widget.py - 트리거 상세 정보
│   ├── simulation_control_widget.py - 시뮬레이션 제어
│   ├── simulation_result_widget.py - 시뮬레이션 결과
│   ├── parameter_widgets.py - 파라미터 입력 위젯
│   └── variable_definitions.py - 변수 정의 (DB 연동)
├── components/shared/ - 공유 8개 컴포넌트
│   ├── compatibility_validator.py - 호환성 검증
│   ├── trigger_calculator.py - 트리거 계산 엔진
│   ├── chart_visualizer.py - 차트 시각화
│   └── 기타 서비스들...
└── shared_simulation/ - 시뮬레이션 엔진들
```

### 🎨 UI 레이아웃 (2x3 그리드)
```
┌──────────────────┬──────────────────┬──────────────────┐
│ [1] 컨디션 빌더   │ [2] 트리거 리스트 │ [3] 시뮬레이션    │
│ - 변수 선택      │ - 저장된 트리거   │   컨트롤          │
│ - 지표 조합      │ - 생성/편집/삭제  │ - 데이터 소스     │
│ - 조건 생성      │ - 목록 관리       │ - 실행 제어       │
├──────────────────┼──────────────────┼──────────────────┤
│ [4] 컨디션 확장   │ [5] 트리거 상세   │ [6] 시뮬레이션    │
│ - 미리보기       │ - 상세 정보       │   결과 차트       │
│ - 호환성 검증    │ - 실행 코드       │ - 백테스팅       │
│ - 파라미터 설정  │ - 성능 지표       │ - 신호 분석       │
└──────────────────┴──────────────────┴──────────────────┘
```

### 🔗 데이터 플로우
1. **컨디션 생성**: 변수/지표 선택 → 파라미터 설정 → 조건 빌드
2. **트리거 조합**: 컨디션들 → 논리 연산자 → 트리거 완성
3. **시뮬레이션**: 트리거 + 마켓데이터 → 백테스팅 → 결과 분석

---

## 🏗️ Phase 1: 컨디션 빌더 Domain Layer 구축 ✅ **완료**

### [x] 1.1 변수/지표 도메인 모델링 ✅ **완료**
- [x] `TradingVariable` Entity (SMA, EMA, RSI, 등) - **완전 구현됨**
- [x] `VariableParameter` Value Object (기간, 상수값 등) - **완전 구현됨**
- [x] `UnifiedParameter` Value Object (통합 파라미터 관리) - **완전 구현됨**
- [x] `VariableCategory` Enum (trend, momentum, volatility, volume, price) - **완전 구현됨**
- [x] `ChartCategory` Enum (overlay, subplot) - **완전 구현됨**
- [x] `ComparisonGroup` Enum (price_comparable, percentage_comparable, zero_centered) - **완전 구현됨**

### [x] 1.2 컨디션 도메인 모델링 ✅ **완료**
- [x] `Condition` Entity (변수 + 연산자 + 임계값) - **완전 구현됨**
- [x] `ConditionOperator` Enum (>, <, >=, <=, ==, crossover, crossunder) - **완전 구현됨**
- [x] `ConditionValue` Value Object (비교값, 다른 변수, 상수) - **완전 구현됨**
- [x] `ConditionStatus` Enum (유효, 무효, 대기) - **완전 구현됨**

### [x] 1.3 Repository Interface 정의 ✅ **완료**
- [x] `ITradingVariableRepository` - 변수 정의 CRUD - **완전 구현됨**
- [x] `IConditionRepository` - 조건 CRUD - **완전 구현됨**
- [x] `IConditionValidationRepository` - 호환성 검증 데이터 - **완전 구현됨**

### [x] 1.4 Domain Services 구현 ✅ **완료**
- [x] `VariableCompatibilityService` - 변수 간 호환성 검증 - **완전 구현됨**
- [x] `ConditionValidationService` - 조건 유효성 검증 - **완전 구현됨**
- [x] `ConditionPreviewService` - 조건 미리보기 생성 - **완전 구현됨**

---

## 🔧 Phase 2: 컨디션 빌더 Infrastructure Layer ✅ **완료**

### [x] 2.1 Database Repository 구현 ✅ **완료**
- [x] `TradingVariableRepository` - tv_trading_variables 테이블 연동 - **SQLite 구현 완료**
- [x] `ConditionRepository` - 조건 저장/로드 (strategies.sqlite3) - **SQLite 구현 완료**
- [x] `VariableParameterRepository` - tv_variable_parameters 테이블 연동 - **SQLite 구현 완료**
- [x] SQLite 연결 및 트랜잭션 관리 - **DatabaseManager 완료**

### [x] 2.2 External Services Integration ✅ **완료**
- [x] Market Data 연동 (market_data.sqlite3) - **완료**
- [x] 실시간 가격 데이터 서비스 - **완료**
- [x] 히스토리컬 데이터 서비스 - **완료**

### [x] 2.3 DTO 계층 구현 ✅ **완료**
- [x] `ConditionCreateDTO` - 조건 생성 요청 - **완료**
- [x] `ConditionUpdateDTO` - 조건 수정 요청 - **완료**
- [x] `ConditionViewDTO` - 조건 조회 응답 - **완료**
- [x] `VariableListDTO` - 변수 목록 응답 - **완료**

---

## 🎮 Phase 3: 컨디션 빌더 Application Layer ✅ **완료**

### [x] 3.1 UseCase 서비스 구현 ✅ **완료**
- [x] `CreateConditionUseCase` - 조건 생성 - **완료**
- [x] `ValidateConditionUseCase` - 조건 유효성 검증 - **완료**
- [x] `PreviewConditionUseCase` - 조건 미리보기 - **완료**
- [x] `ListTradingVariablesUseCase` - 변수 목록 조회 - **완료**
- [x] `GetVariableParametersUseCase` - 변수 파라미터 조회 - **완료**
- [x] `SearchTradingVariablesUseCase` - 변수 검색 - **완료**
- [x] `GetCompatibleVariablesUseCase` - 호환 변수 조회 - **완료**

### [x] 3.2 Application Services ✅ **완료**
- [x] `ConditionBuilderService` - 조건 빌더 통합 서비스 - **완료**
- [x] `CompatibilityValidationService` - 호환성 검증 서비스 - **완료**
- [x] `ConditionSimulationService` - 조건 시뮬레이션 서비스 - **완료**

### [x] 3.3 DTO 시스템 완성 ✅ **완료**
- [x] `TradingVariableListDTO` - 변수 목록 응답 - **완료**
- [x] `TradingVariableDetailDTO` - 변수 상세 정보 - **완료**
- [x] `VariableSearchRequestDTO` - 검색 요청 - **완료**
- [x] `VariableCompatibilityDTO` - 호환성 정보 - **완료**

---

## 🎨 Phase 4: 기존 UI 기반 트리거 빌더 스크린 재구현 ➡️ **별도 태스크로 분리**

**📋 전용 태스크**: `TASK_20250814_09_Phase4_Trigger_Builder_UI_Legacy_Migration.md`

### ✅ **분리 완료 - Phase 4 전략 변경**
- ✅ **Legacy UI 완전 복사**: 기존 UI를 100% 그대로 따라하여 재구현
- ✅ **폴더 구조 체계화**: legacy 파일 보존 + 새 DDD 구조 병행
- ✅ **단계별 마이그레이션**: 위젯별 개별 마이그레이션 + 스크린샷 비교 검증
- ✅ **롤백 대응 준비**: 실패 시 legacy 직접 수정으로 전환하는 안전 장치

### 🎯 **Phase 4 핵심 전략 (별도 태스크에서 진행)**
- **완전 동일 UI**: 기존 스크린샷과 픽셀 단위 동일성 확보
- **자동 크기 대응**: 윈도우 크기 변경 시 상위 레이아웃에만 영향 받도록 제어
- **DDD 패턴 통합**: MVP + UseCase + Repository 완전 적용하되 UI는 변경 없음
- **Legacy 안전 보존**: 모든 기존 파일을 _legacy로 보존하여 롤백 가능

### 🔄 **향후 재사용성 확장 계획 (Phase 4 완료 후)**
- **멀티 모드 지원**: EmbeddedMode/DialogMode/CompactMode 확장
- **크기 조절 시스템**: ResizeableComponentBase 도입
- **컴포넌트 상태 관리**: ComponentContextManager 구현
- **다른 화면 연동**: 전략 메이커, 스크리너 등에서 재사용

---

## 🏗️ Phase 5: 트리거 빌더 Domain Layer 확장 (Phase 4 완료 후 진행)

### [ ] 5.1 트리거 도메인 모델링
- [ ] `Trigger` Entity (조건들의 조합)
- [ ] `TriggerCondition` Value Object (조건 + 논리연산자)
- [ ] `LogicalOperator` Enum (AND, OR, NOT)
- [ ] `TriggerType` Enum (진입, 청산, 위험관리)
- [ ] `TriggerStatus` Enum (활성, 비활성, 오류)

### [ ] 5.2 트리거 Repository Interface
- [ ] `ITriggerRepository` - 트리거 CRUD
- [ ] `ITriggerTemplateRepository` - 템플릿 관리
- [ ] `ITriggerHistoryRepository` - 실행 이력

### [ ] 5.3 트리거 Domain Services
- [ ] `TriggerValidationService` - 트리거 유효성 검증
- [ ] `TriggerOptimizationService` - 트리거 최적화
- [ ] `TriggerBacktestService` - 백테스팅 서비스

---

## 🎮 Phase 6: 트리거 빌더 Application & UI

### [ ] 6.1 트리거 UseCase 구현
- [ ] `CreateTriggerUseCase` - 트리거 생성
- [ ] `CombineConditionsUseCase` - 조건 조합
- [ ] `ValidateTriggerUseCase` - 트리거 검증
- [ ] `BacktestTriggerUseCase` - 백테스팅 실행

### [ ] 6.2 트리거 빌더 UI (매우 복잡)
- [ ] **TriggerBuilderMainWidget** - 2x3 그리드 레이아웃
  - 좌측: 컨디션 빌더 영역
  - 중앙: 트리거 목록 & 상세
  - 우측: 시뮬레이션 영역

- [ ] **TriggerComposerWidget** - 트리거 조합기
  - 드래그 앤 드롭 조건 조합
  - 논리 연산자 시각적 설정
  - 트리거 플로우 다이어그램
  - 실시간 유효성 검증

- [ ] **TriggerListWidget** - 트리거 목록 관리
  - 계층적 트리 구조
  - 검색/필터링/정렬
  - 즐겨찾기 및 태그
  - 복사/붙여넣기 지원

### [ ] 6.3 시뮬레이션 시스템 통합 (재사용 컴포넌트 활용)
- [ ] **SimulationControlWidget** - 재사용 가능 설계
  - 데이터 소스 선택기 (4개 소스)
  - 기간 설정 위젯
  - 실행 옵션 설정
  - 실시간 진행 상황
  - **크기별 기능 조정**:
    - Full: 모든 옵션 표시
    - Medium: 핵심 옵션만
    - Compact: 원클릭 실행

- [ ] **SimulationResultWidget** - 멀티 모드 결과 분석
  - **Large Mode**: 트리거 빌더용
    - 풀사이즈 차트 (matplotlib)
    - 상세 성능 지표 테이블
    - 트리거 신호 상세 분석
  - **Medium Mode**: 전략 메이커용
    - 미니 차트 + 요약 지표
    - 핵심 신호만 표시
  - **Compact Mode**: 대시보드용
    - 썸네일 차트
    - 요약 수치만

### [ ] 6.4 재사용 컴포넌트 통합 테스트
- [ ] **멀티 모드 컴포넌트 검증**
  - 동일 컴포넌트의 다중 인스턴스 동작
  - 모드 전환 시 상태 유지
  - 메모리 사용량 최적화

- [ ] **크기 조절 반응성 테스트**
  - 부모 컨테이너 크기 변경 대응
  - 자동 레이아웃 조정 검증
  - 최소/최대 크기 제한 동작

---

## 🧪 Phase 7: TDD 테스트 구현

### [ ] 7.1 Domain Layer Tests
- [ ] TradingVariable Entity 테스트
- [ ] Condition Entity 테스트
- [ ] Trigger Entity 테스트
- [ ] Value Objects 테스트
- [ ] Domain Services 테스트 (호환성, 검증, 시뮬레이션)

### [ ] 7.2 Application Layer Tests
- [ ] UseCase 테스트 (조건 생성, 트리거 조합)
- [ ] Application Services 테스트
- [ ] DTO 변환 테스트

### [ ] 7.3 UI Presenter Tests
- [ ] ConditionBuilderPresenter 테스트
- [ ] TriggerBuilderPresenter 테스트
- [ ] 사용자 상호작용 시나리오 테스트

### [ ] 7.4 Integration Tests
- [ ] Database Repository 테스트
- [ ] 시뮬레이션 엔진 테스트
- [ ] 전체 워크플로 테스트

---

## 🎯 Phase 8: 통합 및 최적화

### [ ] 8.1 성능 최적화
- [ ] 변수 정의 캐싱 시스템
- [ ] 호환성 검증 캐싱
- [ ] UI 렌더링 최적화
- [ ] 메모리 사용량 최적화

### [ ] 8.2 사용자 경험 향상 및 재사용성 최적화
- [ ] **컴포넌트 상태 관리 시스템**
  - 사용자별 선호 설정 저장
  - 컨텍스트별 상태 복원
  - 다중 인스턴스 동기화

- [ ] **스마트 레이아웃 시스템**
  - 화면 크기별 자동 최적화
  - 사용자 사용 패턴 학습
  - 컴포넌트 배치 제안

- [ ] **컴포넌트 재사용 편의 기능**
  - 키보드 단축키 지원
  - 드래그 앤 드롭 기능
  - 자동 저장 기능
  - 실행 취소/다시 실행

### [ ] 8.3 재사용 컴포넌트 테마 시스템
- [ ] **통합 테마 시스템 지원**
  - 모든 재사용 컴포넌트 테마 연동
  - 크기별 일관된 스타일링
  - 모드별 맞춤형 스타일

- [ ] **차트 테마 통합**
  - matplotlib 차트 테마 연동
  - 크기별 차트 스타일 최적화
  - 다크/라이트 모드 완벽 지원

---

## 🔄 Phase 9: 재사용 컴포넌트 검증 및 문서화

### [ ] 9.1 재사용성 검증 테스트
- [ ] **컨디션 빌더 재사용 테스트**
  - 트리거 빌더 임베딩 모드 검증
  - 전략 메이커 다이얼로그 모드 검증
  - 스크리너 컴팩트 모드 검증

- [ ] **미니 차트 시뮬레이터 재사용 테스트**
  - 트리거 빌더 Large 모드 검증
  - 전략 메이커 Medium 모드 검증
  - 대시보드 Compact 모드 검증

- [ ] **크로스 플랫폼 호환성 검증**
  - 다양한 화면 해상도 대응
  - 다양한 컨테이너 크기 대응
  - 성능 영향 최소화 검증

### [ ] 9.2 재사용 컴포넌트 문서화
- [ ] **컴포넌트 사용법 가이드**
  - 각 모드별 사용 예제
  - 커스터마이징 가이드
  - 트러블슈팅 가이드

- [ ] **API 문서화**
  - 컴포넌트 인터페이스 명세
  - 이벤트/시그널 목록
  - 설정 옵션 상세

### [ ] 9.3 다음 화면 연동 준비
- [ ] **전략 메이커 연동 인터페이스**
  - 컨디션 빌더 다이얼로그 통합
  - 미니 시뮬레이터 임베딩 준비
  - 데이터 교환 프로토콜 정의

- [ ] **컴포넌트 라이브러리 패키징**
  - 재사용 가능한 컴포넌트 모듈 분리
  - Import 경로 최적화
  - 의존성 최소화

---

## 📋 체크리스트

### 🏗️ 아키텍처 검증
- [ ] DDD 4계층 구조 완벽 준수
- [ ] MVP 패턴 완전 적용 (View는 Passive)
- [ ] DTO로 계층 간 완전 분리
- [ ] Domain Layer 외부 의존성 Zero

### 🎨 UI/UX 검증
- [ ] 트리거 빌더 2x3 그리드 레이아웃 완성
- [ ] 컨디션 빌더 직관적 UI 완성
- [ ] 실시간 호환성 검증 동작
- [ ] 시뮬레이션 결과 시각화 완성

### 🔧 기능 검증
- [ ] 7규칙 전략 구성 가능 (RSI 과매도, 불타기, 익절, 스탑, 물타기, 급락/급등)
- [ ] 백테스팅 시뮬레이션 정상 동작
- [ ] 조건/트리거 저장/로드 정상
- [ ] 호환성 검증 시스템 정확도 95% 이상

### 🔄 재사용성 검증
- [ ] 컨디션 빌더 멀티 모드 동작 (Embedded/Dialog/Compact)
- [ ] 미니 차트 시뮬레이터 크기별 기능 조정
- [ ] 컴포넌트 상태 관리 시스템 정상 동작
- [ ] 다중 인스턴스 동시 실행 안정성

### 🧪 품질 검증 ✅ **Phase 1-3 완료**
- [x] TDD 테스트 커버리지 91개 테스트 모두 통과 ✅
- [x] Infrastructure 로깅 완전 적용 ✅
- [x] 에러 처리 완전 구현 (폴백 제거 정책) ✅
- [x] 3-DB 분리 원칙 준수 ✅
- [ ] 재사용 컴포넌트 메모리 누수 없음 (Phase 4에서 검증 예정)

---

## 🎪 성공 기준

### 🔥 최종 검증 기준
1. **기능적 성공**: `python run_desktop_ui.py` 실행 → 전략 관리 → 트리거 빌더에서 7규칙 구성 가능
2. **아키텍처 성공**: DDD + MVP + DTO + TDD 패턴 완전 적용, 계층 위반 Zero
3. **UI/UX 성공**: 복잡한 트리거 빌더 UI 직관적 동작, 테마 시스템 완벽 통합
4. **성능 성공**: 실시간 호환성 검증 < 100ms, 시뮬레이션 실행 < 5초
5. **재사용성 성공**: 컨디션 빌더 3가지 모드 완벽 동작, 미니 차트 크기별 자동 조정

### 🔄 재사용 컴포넌트 검증 시나리오
```
컨디션 빌더 재사용:
1. 트리거 빌더 → 임베딩 모드 (400x300, 실시간 미리보기)
2. 전략 메이커 → 다이얼로그 모드 (600x500, 수정/저장)
3. 스크리너 → 컴팩트 모드 (300x200, 간단 필터)

미니 차트 시뮬레이터 재사용:
1. 트리거 빌더 → Large 모드 (600x400, 상세 차트)
2. 전략 메이커 → Medium 모드 (400x250, 요약 차트)
3. 대시보드 → Compact 모드 (250x150, 썸네일)
```

### 🎯 7규칙 전략 구성 시나리오
```
1. RSI 과매도 진입: RSI < 30 조건 생성
2. 수익시 불타기: 수익률 > 5% AND 상승 추세
3. 계획된 익절: 수익률 > 10% OR 저항선 접근
4. 트레일링 스탑: 고점 대비 -3% 하락
5. 하락시 물타기: 손실률 > -10% AND RSI < 25
6. 급락 감지: 5분내 -5% 하락
7. 급등 감지: 5분내 +8% 상승
```

---

## 📅 예상 일정

### 🚀 Sprint 별 계획 (재사용성 반영)
- **Sprint 1 (3일)**: Phase 1-2 컨디션 빌더 기반 구축
- **Sprint 2 (5일)**: Phase 4 재사용 가능한 컨디션 빌더 UI (복잡도 증가)
- **Sprint 3 (2일)**: Phase 3 컨디션 빌더 Application Layer
- **Sprint 4 (3일)**: Phase 5 트리거 빌더 Domain Layer
- **Sprint 5 (5일)**: Phase 6 트리거 빌더 Application & UI (재사용 컴포넌트 활용)
- **Sprint 6 (4일)**: Phase 7-8 테스트 & 통합 & 최적화
- **Sprint 7 (3일)**: Phase 9 재사용 컴포넌트 검증 & 문서화
- **총 예상**: 25일 (재사용성 설계 복잡도 반영)---

## 🔗 관련 파일 및 참고자료

### 📁 기존 백업 시스템
- **메인**: `upbit_auto_trading/ui/desktop/screens/strategy_management_backup/trigger_builder/`
- **가이드**: `trigger_builder/TRIGGER_BUILDER_SYSTEM_GUIDE.md`
- **컴포넌트**: `trigger_builder/components/core/` (8개 핵심 컴포넌트)

### 📊 데이터베이스 스키마
- **변수**: `data_info/tv_trading_variables.yaml` (SMA, EMA, RSI 등)
- **파라미터**: `data_info/tv_variable_parameters.yaml`
- **전략**: `data_info/upbit_autotrading_schema_strategies.sql`

### 🛠️ 개발 가이드
- **DDD 가이드**: `.github/copilot-instructions.md`
- **UI 가이드**: `docs/UI_GUIDE.md`
- **아키텍처**: `docs/DDD_아키텍처_패턴_가이드.md`

---

**📌 핵심 포인트**: 재사용 가능한 컴포넌트 설계가 성공의 열쇠! 컨디션 빌더와 미니 차트 시뮬레이터를 여러 모드(Embedded/Dialog/Compact)로 설계하여 트리거 빌더, 전략 메이커, 스크리너 등에서 완벽 재사용 가능하도록 구축

## 🎯 재사용성을 위한 핵심 준비사항 요약

### 🏗️ **아키텍처 준비**
1. **컴포넌트 모드 인터페이스**: EmbeddedMode, DialogMode, CompactMode
2. **크기 조절 시스템**: ResizeableComponentBase + LayoutResponsiveManager
3. **상태 관리 시스템**: ComponentContextManager + 다중 인스턴스 동기화

### 🎨 **UI 준비**
1. **멀티 모드 UI**: 동일 컴포넌트, 다양한 크기와 기능
2. **스마트 레이아웃**: 부모 컨테이너에 따른 자동 조정
3. **일관된 테마**: 모든 모드에서 동일한 Look & Feel

### 🔧 **기술적 준비**
1. **어댑터 패턴**: 각 사용 컨텍스트별 특화 기능
2. **MVP 분리**: Presenter는 모드 독립적, View만 모드별 구현
3. **이벤트 시스템**: 일관된 시그널/슬롯 인터페이스

이렇게 설계하면 향후 전략 메이커, 스크리너, 대시보드 등에서 개발 시간을 대폭 단축하면서도 일관된 사용자 경험을 제공할 수 있습니다! 🚀
