# 📋 현재 중요 방침 및 가이드라인 종합

## 📊 분석 개요

본 문서는 현재 `docs` 폴더의 핵심 방침과 가이드라인을 종합하여 리팩토링 시 반드시 준수해야 할 원칙들을 정리합니다.

**분석 범위**: docs 폴더 내 19개 핵심 문서  
**목표**: 리팩토링 중 기존 우수 방침 유지  
**중요도**: 모든 리팩토링 결정의 기준

## 🎯 핵심 개발 원칙 (절대 변경 금지)

### 1. 기본 7규칙 전략 중심 개발
**출처**: `BASIC_7_RULE_STRATEGY_GUIDE.md`, `DEV_CHECKLIST.md`

```python
# 모든 개발의 최종 검증 기준
BASIC_7_RULE_STRATEGY = {
    "진입": "RSI 과매도 진입 (RSI < 30)",
    "관리1": "수익 시 불타기 (5% 도달 시마다 3회까지)",
    "관리2": "하락 시 물타기 (평단가 대비 -5% 하락 시 2회까지)",
    "청산1": "계획된 익절 (불타기 3회 완료 후)",
    "청산2": "트레일링 스탑 (5% 수익 후, 고점 대비 3% 하락)",
    "청산3": "급락 감지 (1분 내 -5% 폭락 시 즉시 청산)",
    "제어": "급등 감지 (1분 내 +5% 급등 시 불타기 중단)"
}
```

**리팩토링 적용**:
- 모든 새로운 아키텍처는 7규칙 전략 구현 가능해야 함
- 리팩토링 각 단계별로 7규칙 전략으로 검증 필수
- UI, Service, Domain 모든 계층에서 7규칙 지원

### 2. 3-DB 아키텍처 (고정 구조)
**출처**: `DB_SCHEMA.md`, `ARCHITECTURE_OVERVIEW.md`

```yaml
데이터베이스 구조:
  settings.sqlite3:    # 구조 정의 (변수, 파라미터, 카테고리)
    - 읽기 전용, 업데이트 시에만 변경
    - tv_ 접두사 테이블 (tv_trading_variables)
    - data_info/*.yaml 파일과 연동

  strategies.sqlite3:  # 사용자 전략 (전략, 조건, 백테스팅 결과)
    - 읽기/쓰기, 사용자별 개인화
    - 실행 기록 저장

  market_data.sqlite3: # 시장 데이터 (가격, 지표, 거래량)
    - 대용량, 자동 정리, 공유 가능
    - 성능 최적화 우선
```

**리팩토링 적용**:
- Repository 패턴 적용 시에도 3-DB 구조 유지
- 각 DB별 Repository 분리 (SettingsRepository, StrategyRepository, MarketDataRepository)
- DB 경로는 `config/` 폴더에서 중앙 관리

### 3. 에러 투명성 정책 (폴백 코드 금지)
**출처**: `ERROR_HANDLING_POLICY.md`

```python
# ❌ 절대 금지: 문제를 숨기는 폴백 코드
try:
    from .some_module import SomeClass
except ImportError:
    class SomeClass:  # 더미 클래스
        pass

# ✅ 필수: 명확한 에러 발생
from .some_module import SomeClass  # 실패 시 즉시 ModuleNotFoundError
```

**리팩토링 적용**:
- 새로운 계층 구조에서도 폴백 코드 금지
- 의존성 주입 실패 시 명확한 에러 메시지
- Service Layer에서도 try-catch로 문제 숨기기 금지

## 🏗️ 아키텍처 가이드라인

### 1. 컴포넌트 기반 설계
**출처**: `COMPONENT_ARCHITECTURE.md`, `PROJECT_SPECIFICATIONS.md`

```python
# 설계 원칙
- 단일 책임: 각 컴포넌트는 하나의 명확한 역할
- 느슨한 결합: 인터페이스를 통한 상호작용
- 높은 응집도: 관련 기능을 하나의 모듈로 그룹화
- 의존성 주입: 테스트 가능한 설계
```

**리팩토링 적용**:
- 새로운 Service, Repository도 컴포넌트 기반 설계
- 인터페이스 우선 설계 (Abstract Base Class 활용)
- 각 계층별 명확한 책임 분리

### 2. 3중 카테고리 호환성 시스템
**출처**: `VARIABLE_COMPATIBILITY.md`, `TRIGGER_BUILDER_GUIDE.md`

```python
COMPATIBILITY_SYSTEM = {
    "purpose_category": ["trend", "momentum", "volatility", "volume", "price"],
    "chart_category": ["overlay", "subplot"],
    "comparison_group": ["price_comparable", "percentage_comparable", "zero_centered"]
}

# 호환성 규칙
- 같은 comparison_group = 직접 비교 가능
- 다른 comparison_group = 비교 불가 (UI에서 차단)
- price vs percentage = 정규화 후 비교 (경고 표시)
```

**리팩토링 적용**:
- Domain Layer에 호환성 검증 로직 이동
- CompatibilityDomainService 구현
- UI는 Domain 규칙만 확인하고 표시

### 3. UI 스타일링 표준
**출처**: `STYLE_GUIDE.md`, `UI_DESIGN_SYSTEM.md`

```python
# UI 개발 원칙
- QSS 파일 사용 (하드코딩 금지)
- 다크/라이트 테마 지원
- objectName 기반 스타일링
- 반응형 디자인 (최소 1280x720)

# 테마 시스템
from upbit_auto_trading.ui.desktop.common.theme_notifier import get_theme_notifier
theme_notifier = get_theme_notifier()
theme_notifier.theme_changed.connect(self._on_theme_changed)
```

**리팩토링 적용**:
- Presenter 패턴 적용 시에도 스타일 가이드 유지
- View는 스타일링만 담당, 테마 변경 이벤트만 처리
- Service Layer는 UI 스타일과 완전 분리

## 💻 개발 표준 및 품질 기준

### 1. 코딩 표준
**출처**: `STYLE_GUIDE.md`, `DEV_CHECKLIST.md`

```python
# 필수 준수 사항
- PEP 8 엄격 준수 (79자 제한)
- 타입 힌트 모든 함수/메소드 필수
- docstring 모든 public 메소드
- 단위 테스트 신규 기능 필수

# 함수 설계 원칙
- 함수는 20줄 이하, 하나의 명확한 목적
- DRY 원칙: 중복 로직 추상화
- 의미있는 이름: 축약어 없이 명확한 변수/함수명
```

**리팩토링 적용**:
- 모든 새로운 Service, Repository 클래스도 동일 기준 적용
- Domain 모델도 타입 힌트 및 docstring 필수
- Clean Architecture 계층별로도 코딩 표준 동일 적용

### 2. 테스트 전략
**출처**: `DEV_CHECKLIST.md`

```python
# 테스트 범위
- 단위 테스트: 모든 비즈니스 로직
- 통합 테스트: 계층 간 연동
- 7규칙 전략: 전체 워크플로 검증

# 테스트 패턴
def test_strategy_creation():
    # Given
    strategy_data = create_test_strategy_data()
    
    # When
    result = strategy_service.create_strategy(strategy_data)
    
    # Then
    assert result.is_success
    assert_7_rule_strategy_supported(result.strategy)
```

**리팩토링 적용**:
- 각 계층별 독립적 테스트 가능해야 함
- Domain Layer 테스트: 순수 비즈니스 로직만
- Service Layer 테스트: Use Case 시나리오
- Repository 테스트: Mock을 통한 격리

### 3. 로깅 시스템 v3.0
**출처**: `copilot-instructions.md`

```python
# 스마트 로깅 사용법
from upbit_auto_trading.logging import get_integrated_logger
logger = get_integrated_logger("ComponentName")

# 환경변수 제어
$env:UPBIT_LOG_CONTEXT='debugging'    # development, testing, production
$env:UPBIT_LOG_SCOPE='verbose'        # silent, minimal, normal, verbose
$env:UPBIT_COMPONENT_FOCUS='MyComponent'  # 특정 컴포넌트만
```

**리팩토링 적용**:
- 모든 새로운 Service, Repository에서 통합 로거 사용
- Domain Layer는 로깅 최소화 (비즈니스 로직에 집중)
- Application Layer에서 Use Case 실행 로그
- Infrastructure Layer에서 외부 연동 로그

## 🔧 개발 워크플로우

### 1. 필수 검증 절차
**출처**: `DEV_CHECKLIST.md`

```python
# 개발 전 (필수)
1. 관련 docs 문서 숙지
2. VARIABLE_COMPATIBILITY.md 확인
3. COMPONENT_ARCHITECTURE.md 참조

# 구현 중
1. STYLE_GUIDE.md 기준 적용
2. ERROR_HANDLING_POLICY.md 준수
3. DB_SCHEMA.md 정확히 반영

# 완료 후 (필수)
1. DEV_CHECKLIST.md 모든 항목 확인
2. 7규칙 전략으로 동작 검증
3. 코드 품질: 타입 힌트, 문서화, 테스트 포함
```

**리팩토링 적용**:
- 각 리팩토링 단계별로 동일한 검증 절차 적용
- 새로운 계층 구현 시에도 체크리스트 준수
- 기존 기능 퇴화 방지를 위한 회귀 테스트

### 2. 도구 및 유틸리티 활용
**출처**: `copilot-instructions.md`

```powershell
# DB 분석 도구 (필수 활용)
python tools/super_db_table_viewer.py settings
python tools/super_db_table_reference_code_analyzer.py --tables tv_trading_variables

# 최종 검증
python run_desktop_ui.py  # 모든 개발 작업 후 실행
```

**리팩토링 적용**:
- Repository 구현 시 DB 분석 도구 활용
- 마이그레이션 전후 데이터 무결성 검증
- 각 단계별 메인 UI 실행으로 통합 테스트

## 📊 성능 및 보안 기준

### 1. 성능 요구사항
**출처**: `PROJECT_SPECIFICATIONS.md`

```yaml
성능 기준:
  백테스팅: 1년 분봉 데이터 5분 내 처리
  UI 응답성: 모든 사용자 입력 100ms 내 반응
  실시간 데이터: 1초 이내 갱신
```

**리팩토링 적용**:
- Service Layer 구현 시 성능 벤치마크 유지
- Repository 패턴으로 DB 접근 최적화
- Clean Architecture가 성능에 미치는 영향 모니터링

### 2. 보안 요구사항
**출처**: `PROJECT_SPECIFICATIONS.md`

```yaml
보안 원칙:
  API 키: 환경변수 기반 관리, 하드코딩 금지
  로깅: 민감 정보 자동 마스킹
  데이터: 개인 정보 Git 추적 방지
```

**리팩토링 적용**:
- Infrastructure Layer에서 API 키 관리 집중화
- Domain Layer에는 민감 정보 노출 금지
- Service Layer에서 보안 검증 로직 구현

## 🎯 리팩토링 시 준수 사항

### 1. 기존 우수 원칙 유지 (변경 금지)
- ✅ 기본 7규칙 전략 중심 개발
- ✅ 3-DB 아키텍처 구조
- ✅ 에러 투명성 정책
- ✅ 3중 카테고리 호환성 시스템
- ✅ 스마트 로깅 시스템 v3.0

### 2. 점진적 개선 (단계별 적용)
- 🔄 UI에서 비즈니스 로직 분리
- 🔄 Repository 패턴 완전 구현
- 🔄 Service Layer 구축
- 🔄 Clean Architecture 적용

### 3. 품질 기준 강화 (기존보다 향상)
- 📈 테스트 커버리지: 30% → 80%+
- 📈 코드 복잡도: 평균 15 → 8 이하
- 📈 UI 비즈니스 로직: 60% → 5% 이하
- 📈 순환 의존성: 8개 → 0개

## 💡 리팩토링 가이드라인

### 1. 문서 기반 개발
- 모든 아키텍처 결정은 문서에 기록
- 기존 우수 방침은 새로운 구조에도 적용
- 변경사항은 관련 문서 동시 업데이트

### 2. 점진적 적용
- Big Bang 리팩토링 금지
- 기존 기능 동작 보장
- 단계별 롤백 시나리오 준비

### 3. 지속적 검증
- 각 단계별 7규칙 전략 검증
- 성능 벤치마크 유지
- 코드 품질 지표 모니터링

---

**완료**: 리팩토링 계획 수립을 위한 4개 핵심 문서 작성 완료  
**다음 단계**: 이 4개 문서를 기반으로 한 구체적 리팩토링 계획 수립
