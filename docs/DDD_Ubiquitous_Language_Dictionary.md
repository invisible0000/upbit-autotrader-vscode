
# 🎯 DDD 용어 사전 (Ubiquitous Language Dictionary)

> **목적**: Infrastructure Layer Repository 구현 시 일관된 용어 사용을 위한 Domain 용어 통일
> **대상**: LLM 에이전트, 개발자, 설계자
> **갱신**: 2025-08-10
> **적용범위**: Domain Layer, Infrastructure Layer, Application Layer

## 📋 목차

- [1. 핵심 Domain Entity 용어](#1-핵심-domain-entity-용어)
- [2. Value Object 용어](#2-value-object-용어)
- [3. Repository 관련 용어](#3-repository-관련-용어)
- [4. 데이터베이스 매핑 용어](#4-데이터베이스-매핑-용어)
- [5. 엔티티별 속성 매핑](#5-엔티티별-속성-매핑)
- [6. 네이밍 컨벤션](#6-네이밍-컨벤션)
- [7. Domain Events 및 예외 처리](#7-domain-events-및-예외-처리)
- [8. Infrastructure Layer 매핑](#8-infrastructure-layer-매핑)

---

## 1. 핵심 Domain Entity 용어

### 📈 Strategy (전략)

| **도메인 용어** | **코드명** | **DB 테이블** | **설명** |
|:-------------|:----------|:------------|:--------|
| Strategy | `Strategy` | `strategies` | 매매 전략의 기본 단위 (Aggregate Root) |
| Strategy ID | `StrategyId` | `strategies.id` | 전략의 고유 식별자 (Value Object, 3-50자, 영문시작) |
| Strategy Name | `name` | `strategies.strategy_name` | 사용자 정의 전략명 |
| Strategy Config | `StrategyConfig` | - | 진입/관리 전략 설정 (Value Object) |
| Conflict Resolution | `ConflictResolution` | - | 신호 충돌 해결 방식 (Value Object) |
| Strategy Role | `StrategyRole` | - | 전략 역할 분류 (Value Object) |
| Strategy Status | `is_active` | `strategies.is_active` | 전략 활성화 상태 (Boolean) |

### 🎯 Trigger (트리거/조건)

| **도메인 용어** | **코드명** | **DB 테이블** | **설명** |
|:-------------|:----------|:------------|:--------|
| Trigger | `Trigger` | `strategy_conditions` | 매매 조건/트리거 (Entity) |
| Trigger ID | `TriggerId` | `strategy_conditions.id` | 트리거 고유 식별자 (Value Object) |
| Trigger Name | `trigger_name` | `strategy_conditions.condition_name` | 트리거/조건명 |
| Trigger Type | `TriggerType` | `strategy_conditions.component_type` | 트리거 유형 (ENTRY, MANAGEMENT, EXIT) |
| Comparison Operator | `ComparisonOperator` | `strategy_conditions.operator` | 비교 연산자 (>, <, >=, <=, ~=, !=) |
| Target Value | `target_value` | `strategy_conditions.target_value` | 비교 대상값 |
| Variable Parameters | `variable_params` | `strategy_conditions.variable_params` | 트레이딩 변수 파라미터 (JSON) |

### 📊 Trading Variable (매매 변수)

| **도메인 용어** | **코드명** | **DB 테이블** | **설명** |
|:-------------|:----------|:------------|:--------|
| Trading Variable | `TradingVariable` | `tv_trading_variables` | 기술적 지표/매매 변수 (Value Object) |
| Variable ID | `variable_id` | `tv_trading_variables.variable_id` | 변수 고유 식별자 ('SMA', 'RSI') |
| Variable Name | `display_name_ko` | `tv_trading_variables.display_name_ko` | 한글 표시명 |
| Variable Parameters | `parameters` | `tv_variable_parameters` | 변수별 파라미터 (JSON) |
| Purpose Category | `purpose_category` | `tv_trading_variables.purpose_category` | 목적별 분류 (trend, momentum, volatility) |
| Chart Category | `chart_category` | `tv_trading_variables.chart_category` | 차트 표시 분류 (overlay, subplot) |
| Comparison Group | `comparison_group` | `tv_trading_variables.comparison_group` | 호환성 그룹 (price_comparable, percentage_comparable) |

### ⚙️ Settings (설정)

| **도메인 용어** | **코드명** | **UI 컴포넌트** | **설명** |
|:-------------|:----------|:------------|:--------|
| API Settings | `ApiSettings` | `ApiSettingsView` | API 키 및 연결 설정 |
| Database Settings | `DatabaseSettings` | `DatabaseSettingsView` | 데이터베이스 경로 및 관리 설정 |
| Notification Settings | `NotificationSettings` | `NotificationSettingsView` | 알림 및 메시지 설정 |
| UI Settings | `UISettings` | `UISettingsView` | 사용자 인터페이스 설정 |
| Environment Settings | `EnvironmentSettings` | `EnvironmentSettingsView` | 환경변수 및 로깅 설정 (구현 완료) |

### 🔧 Environment & Logging Configuration

| **도메인 용어** | **환경변수** | **config YAML 키** | **설명** |
|:-------------|:----------|:------------|:--------|
| Console Output | `UPBIT_CONSOLE_OUTPUT` | `console_enabled` | 콘솔 로그 출력 여부 |
| Log Level | `UPBIT_LOG_LEVEL` | `level` | 로그 레벨 (DEBUG, INFO, WARNING, ERROR) |
| Log Context | `UPBIT_LOG_CONTEXT` | `context` | 로그 컨텍스트 (development, production, testing) |
| Log Scope | `UPBIT_LOG_SCOPE` | `scope` | 로그 범위 (normal, verbose, debug) |
| Component Focus | `UPBIT_COMPONENT_FOCUS` | `component_focus` | 특정 컴포넌트 집중 모니터링 |
| LLM Briefing | `UPBIT_LLM_BRIEFING_ENABLED` | `llm_briefing_enabled` | LLM 에이전트 브리핑 활성화 |
| Feature Development | `UPBIT_FEATURE_DEVELOPMENT` | `feature_development` | 기능 개발 컨텍스트 |
| Performance Monitoring | `UPBIT_PERFORMANCE_MONITORING` | `performance_monitoring` | 성능 모니터링 활성화 |
| Briefing Update Interval | `UPBIT_BRIEFING_UPDATE_INTERVAL` | `briefing_update_interval` | 브리핑 업데이트 간격 (초) |

### 📁 Configuration Profile Management

| **도메인 용어** | **클래스명** | **파일 패턴** | **설명** |
|:-------------|:----------|:------------|:--------|
| Config Profile | `ConfigProfile` | `config.{profile}.yaml` | 환경별 설정 프로파일 |
| Profile Loader | `ConfigProfileLoader` | - | YAML 프로파일 로더 |
| Profile Switcher | `ProfileSwitcher` | - | 프로파일 기반 환경변수 적용 |
| Profile Service | `ConfigProfileService` | - | 프로파일 관리 통합 서비스 |
| Profile Switch Result | `ProfileSwitchResult` | - | 프로파일 전환 결과 (성공/실패, 오류 메시지) |

---

## 2. Value Object 용어

### 🔑 Identifier Objects

| **도메인 용어** | **클래스명** | **타입** | **예시값** | **비즈니스 규칙** |
|:-------------|:----------|:--------|:-----------|:-------------|
| Strategy ID | `StrategyId` | `str` | `"basic_7_rule_strategy"` | 3-50자, 영문시작, 영숫자_- 허용 |
| Trigger ID | `TriggerId` | `Union[str, int]` | `"rsi_oversold_entry"` | 고유 식별자 |
| Variable ID | `VariableId` | `str` | `"SMA"`, `"RSI"`, `"MACD"` | 대문자 기술적 지표명 |

### 📏 Parameter Objects

| **도메인 용어** | **클래스명** | **타입** | **설명** |
|:-------------|:----------|:--------|:----------|
| Strategy Config | `StrategyConfig` | `dataclass` | 진입/관리 전략 설정 조합 |
| Conflict Resolution | `ConflictResolution` | `Enum` | priority, conservative, merge |
| Comparison Operator | `ComparisonOperator` | `Enum` | `>`, `<`, `>=`, `<=`, `~=`, `!=` |
| Signal Type | `SignalType` | `Enum` | BUY, SELL, HOLD, ADD_BUY, CLOSE_POSITION |
| Variable Parameters | `VariableParameters` | `Dict[str, Any]` | 변수별 파라미터 (기간, 승수 등) |
| Target Value | `target_value` | `Union[str, int, float]` | 비교 대상값 |
| Compatibility Rules | `CompatibilityRules` | `dataclass` | 변수 호환성 검증 규칙 |

---

## 3. Repository 관련 용어

### 🏗️ Repository Pattern

| **도메인 용어** | **클래스명** | **역할** | **구현체** |
|:-------------|:----------|:--------|:----------|
| Strategy Repository | `StrategyRepository` | Strategy 저장소 인터페이스 | `SqliteStrategyRepository` |
| Trigger Repository | `TriggerRepository` | Trigger 저장소 인터페이스 | `SqliteTriggerRepository` |
| Settings Repository | `SettingsRepository` | 설정 저장소 인터페이스 | `SqliteSettingsRepository` |
| Market Data Repository | `MarketDataRepository` | 시장 데이터 저장소 인터페이스 | `SqliteMarketDataRepository` |
| Base Repository | `BaseRepository[T, ID]` | Repository 기본 인터페이스 | 제네릭 기본 클래스 |
| Repository Factory | `RepositoryFactory` | Repository 생성 팩토리 | Repository 인스턴스 생성 |

### 🗃️ Database Management

| **도메인 용어** | **클래스명** | **역할** | **설명** |
|:-------------|:----------|:--------|:----------|
| Database Manager | `DatabaseManager` | 멀티 DB 연결 관리 | 3-DB 아키텍처 연결 풀링 |
| Repository Container | `RepositoryContainer` | DI 컨테이너 | Repository 의존성 주입 |

### ⚡ Domain Services

| **도메인 용어** | **클래스명** | **역할** | **설명** |
|:-------------|:----------|:--------|:----------|
| Strategy Compatibility Service | `StrategyCompatibilityService` | 전략 호환성 검증 | 전략 조합 유효성 검사 |
| Trigger Evaluation Service | `TriggerEvaluationService` | 트리거 평가 서비스 | 시장 데이터 기반 조건 평가 |
| Normalization Service | `NormalizationService` | 데이터 정규화 서비스 | 지표값 정규화 처리 |
| Business Logic Adapter | `BusinessLogicAdapter` | 비즈니스 로직 어댑터 | 기존 로직과 Domain 연결 |

### 🏗️ Infrastructure Services

| **도메인 용어** | **클래스명** | **역할** | **설명** |
|:-------------|:----------|:--------|:----------|
| Component Logger | `create_component_logger()` | 로깅 시스템 | Infrastructure 표준 로깅 (print 문 대체) |
| Theme Service | `ThemeService` | 테마 관리 서비스 | UI 테마 및 스타일 관리 |
| Application Context | `ApplicationContext` | DI 컨테이너 | 서비스 등록 및 의존성 주입 |

---

## 4. 데이터베이스 매핑 용어

### 🎯 Core Tables (strategies.sqlite3)

| **도메인 개념** | **테이블명** | **주요 컬럼** | **설명** |
|:-------------|:----------|:------------|:--------|
| Strategy | `strategies` | `id`, `strategy_name`, `description` | 전략 메인 테이블 |
| Trigger/Condition | `strategy_conditions` | `id`, `condition_name`, `strategy_id` | 전략별 조건 테이블 |
| Strategy Component | `strategy_components` | `id`, `component_type`, `component_config` | 전략 구성요소 |
| Execution History | `execution_history` | `id`, `strategy_id`, `executed_at` | 실행 기록 |

### 📊 Settings Tables (settings.sqlite3)

| **도메인 개념** | **테이블명** | **주요 컬럼** | **설명** |
|:-------------|:----------|:------------|:--------|
| Trading Variable | `tv_trading_variables` | `variable_id`, `display_name_ko` | 매매 변수 정의 |
| Variable Parameter | `tv_variable_parameters` | `variable_id`, `parameter_name` | 변수별 파라미터 |
| Indicator Category | `tv_indicator_categories` | `category_key`, `category_name_ko` | 지표 분류 체계 |
| App Settings | `cfg_app_settings` | `key`, `value` | 앱 전역 설정 |

### 💹 Market Data Tables (market_data.sqlite3)

| **도메인 개념** | **테이블명** | **주요 컬럼** | **설명** |
|:-------------|:----------|:------------|:--------|
| OHLCV Data | `ohlcv_data` | `symbol`, `timestamp`, `open`, `high`, `low`, `close`, `volume` | 기본 시장 데이터 |
| Portfolio | `portfolios` | `id`, `name`, `total_value` | 포트폴리오 관리 |
| Position | `positions` | `id`, `symbol`, `quantity`, `avg_price` | 포지션 정보 |
| Backtest Result | `backtest_results` | `id`, `strategy_id`, `total_return` | 백테스팅 결과 |

---

## 5. 엔티티별 속성 매핑

### 📈 Strategy Entity 매핑

| **Domain Property** | **DB Column** | **타입** | **제약조건** |
|:------------------|:-------------|:--------|:----------|
| `strategy_id.value` | `strategies.id` | `INTEGER PRIMARY KEY` | NOT NULL |
| `name` | `strategies.strategy_name` | `TEXT` | NOT NULL |
| `description` | `strategies.description` | `TEXT` | NULL |
| `status` | `strategies.is_active` | `BOOLEAN` | DEFAULT 0 |
| `strategy_type` | `strategies.strategy_type` | `TEXT` | DEFAULT 'manual' |
| `tags` | `strategies.tags` | `TEXT` | JSON 배열 형태 |
| `created_at` | `strategies.created_at` | `TIMESTAMP` | DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | `strategies.updated_at` | `TIMESTAMP` | DEFAULT CURRENT_TIMESTAMP |

### 🎯 Trigger Entity 매핑

| **Domain Property** | **DB Column** | **타입** | **제약조건** |
|:------------------|:-------------|:--------|:----------|
| `trigger_id.value` | `strategy_conditions.id` | `INTEGER PRIMARY KEY` | NOT NULL |
| `trigger_name` | `strategy_conditions.condition_name` | `TEXT` | NOT NULL |
| `strategy_id.value` | `strategy_conditions.strategy_id` | `INTEGER` | FOREIGN KEY |
| `variable.variable_id` | `strategy_conditions.variable_id` | `TEXT` | NOT NULL |
| `variable.parameters` | `strategy_conditions.variable_params` | `TEXT` | JSON 형태 |
| `operator` | `strategy_conditions.operator` | `TEXT` | NOT NULL |
| `target_value` | `strategy_conditions.target_value` | `TEXT` | NOT NULL |
| `trigger_type` | `strategy_conditions.component_type` | `TEXT` | 'entry', 'exit', 'management' |
| `is_active` | `strategy_conditions.is_enabled` | `BOOLEAN` | DEFAULT 1 |
| `weight` | `strategy_conditions.execution_order` | `INTEGER` | DEFAULT 1 |

### 📊 Trading Variable Entity 매핑

| **Domain Property** | **DB Column** | **타입** | **제약조건** |
|:------------------|:-------------|:--------|:----------|
| `variable_id` | `tv_trading_variables.variable_id` | `TEXT PRIMARY KEY` | NOT NULL |
| `display_name_ko` | `tv_trading_variables.display_name_ko` | `TEXT` | NOT NULL |
| `display_name_en` | `tv_trading_variables.display_name_en` | `TEXT` | NULL |
| `purpose_category` | `tv_trading_variables.purpose_category` | `TEXT` | NOT NULL |
| `chart_category` | `tv_trading_variables.chart_category` | `TEXT` | NOT NULL |
| `comparison_group` | `tv_trading_variables.comparison_group` | `TEXT` | NOT NULL |
| `parameters` | `tv_variable_parameters.*` | 별도 테이블 | 1:N 관계 |

---

## 6. 네이밍 컨벤션

### 🏷️ 클래스 및 파일명

| **유형** | **패턴** | **예시** | **설명** |
|:-------|:---------|:--------|:--------|
| Domain Entity | `PascalCase` | `Strategy`, `Trigger` | 도메인 엔티티 |
| Value Object | `PascalCase` | `StrategyId`, `TriggerId`, `ComparisonOperator` | 값 객체 |
| Domain Service | `PascalCase + Service` | `StrategyCompatibilityService` | 도메인 서비스 |
| Repository Interface | `PascalCase + Repository` | `StrategyRepository` | 저장소 인터페이스 |
| Repository Implementation | `Sqlite + PascalCase + Repository` | `SqliteStrategyRepository` | SQLite 구현체 |
| Mapper | `PascalCase + Mapper` | `StrategyMapper`, `TriggerMapper` | 엔티티-DB 매퍼 |
| Domain Event | `PascalCase + Event` | `StrategyCreated`, `TriggerEvaluated` | 도메인 이벤트 |
| Domain Exception | `PascalCase + Error` | `InvalidStrategyConfigurationError` | 도메인 예외 |
| Mock 클래스 | `Mock + PascalCase` | `MockStrategy`, `MockTrigger` | 테스트/개발용 Mock |

### 🗂️ 메서드명 및 변수명

| **유형** | **패턴** | **예시** | **설명** |
|:-------|:---------|:--------|:--------|
| Entity Method | `snake_case` | `get_all_triggers()`, `add_trigger()` | 엔티티 메서드 |
| Repository Method | `snake_case` | `find_by_id()`, `save()`, `find_all_active()` | 저장소 메서드 |
| Mapper Method | `snake_case` | `to_entity()`, `to_database_record()` | 매퍼 메서드 |
| Private Method | `_snake_case` | `_load_triggers()`, `_insert_strategy()` | 내부 메서드 |
| Property | `snake_case` | `strategy_id`, `trigger_name`, `created_at` | 속성명 |

### 📊 데이터베이스 컨벤션

| **유형** | **패턴** | **예시** | **설명** |
|:-------|:---------|:--------|:--------|
| 테이블명 | `snake_case` | `strategies`, `strategy_conditions` | 테이블명 (복수형) |
| 컬럼명 | `snake_case` | `strategy_id`, `created_at`, `is_active` | 컬럼명 |
| Foreign Key | `[table]_id` | `strategy_id`, `trigger_id` | 외래키 명명 |
| Boolean 컬럼 | `is_[state]` | `is_active`, `is_enabled` | Boolean 플래그 |
| Timestamp 컬럼 | `[action]_at` | `created_at`, `updated_at`, `executed_at` | 시간 기록 |

---

## 7. Domain Events 및 예외 처리

### ⚡ Domain Events

| **이벤트명** | **클래스명** | **발생 시점** | **설명** |
|:-----------|:----------|:-----------|:--------|
| Strategy Created | `StrategyCreated` | 전략 생성 완료 | 새 전략이 성공적으로 생성됨 |
| Strategy Updated | `StrategyUpdated` | 전략 업데이트 완료 | 기존 전략이 수정됨 |
| Strategy Activated | `StrategyActivated` | 전략 활성화 | 전략이 활성 상태로 변경됨 |
| Strategy Deactivated | `StrategyDeactivated` | 전략 비활성화 | 전략이 비활성 상태로 변경됨 |
| Strategy Deleted | `StrategyDeleted` | 전략 삭제 | 전략이 삭제됨 |
| Trigger Evaluated | `TriggerEvaluated` | 트리거 평가 완료 | 트리거 조건 평가가 완료됨 |

### 🚨 Domain Exceptions

| **예외명** | **클래스명** | **발생 조건** | **설명** |
|:---------|:----------|:-----------|:--------|
| Invalid Strategy ID | `InvalidStrategyIdError` | 전략 ID 규칙 위반 | 3-50자, 영문시작 규칙 위반 |
| Invalid Strategy Configuration | `InvalidStrategyConfigurationError` | 전략 설정 오류 | 진입전략 누락, 호환성 오류 등 |
| Incompatible Trigger | `IncompatibleTriggerError` | 트리거 호환성 오류 | 호환되지 않는 변수 조합 |
| Incompatible Strategy | `IncompatibleStrategyError` | 전략 호환성 오류 | 조합 불가능한 전략 구성 |
| Domain Exception | `DomainException` | 도메인 규칙 위반 | 모든 도메인 예외의 기본 클래스 |

---

## 8. Infrastructure Layer 매핑

### 🗄️ Database Mapper 패턴

| **매퍼 클래스** | **매핑 대상** | **주요 메서드** | **설명** |
|:-------------|:-----------|:-------------|:--------|
| StrategyMapper | Strategy ↔ strategies 테이블 | `to_entity()`, `to_database_record()` | 전략 엔티티 매핑 |
| TriggerMapper | Trigger ↔ strategy_conditions 테이블 | `to_entity()`, `to_database_record()` | 트리거 엔티티 매핑 |
| TradingVariableMapper | TradingVariable ↔ tv_trading_variables | `to_entity()`, `load_parameters()` | 매매 변수 매핑 |
| MockStrategy | Strategy Mock 구현 | `get_all_triggers()` | Domain Layer 구현 전 임시 Mock |
| MockTrigger | Trigger Mock 구현 | 속성 접근 | Domain Layer 구현 전 임시 Mock |

### 🔧 Infrastructure Services

| **서비스명** | **클래스명** | **역할** | **설명** |
|:-----------|:----------|:--------|:--------|
| Connection Pool | `DatabaseManager` | 멀티 DB 연결 관리 | SQLite WAL 모드, 트랜잭션 관리 |
| Query Executor | `DatabaseManager.execute_query()` | 쿼리 실행 | 안전한 파라미터화 쿼리 |
| Transaction Manager | `DatabaseManager.transaction()` | 트랜잭션 관리 | Context Manager 패턴 |

### 🎭 Presentation Layer (MVP Pattern)

| **용어** | **클래스명** | **역할** | **설명** |
|:--------|:----------|:--------|:--------|
| Settings MVP | `*SettingsView` | MVP 패턴 View | Settings 화면 MVP 적용 (완성) |
| API Settings View | `ApiSettingsView` | API 설정 화면 | API 키 관리 UI |
| Database Settings View | `DatabaseSettingsView` | DB 설정 화면 | DB 경로, 백업 관리 UI |
| Notification Settings View | `NotificationSettingsView` | 알림 설정 화면 | 알림 관리 UI |
| UI Settings View | `UISettingsView` | UI 설정 화면 | 테마, 레이아웃 설정 UI |
| Settings Presenter | `*SettingsPresenter` | MVP 패턴 Presenter | View-Service 중재 |
| Direct Import | 직접 import | 호환성 alias 금지 | 모든 Settings 컴포넌트 직접 import 필수 |

---

## 🔄 용어 변환 매핑표

### Database ↔ Domain 매핑

| **DB 테이블** | **DB 컬럼** | **Domain Entity** | **Domain Property** |
|:------------|:-----------|:----------------|:------------------|
| `strategies` | `id` | `Strategy` | `strategy_id.value` |
| `strategies` | `strategy_name` | `Strategy` | `name` |
| `strategies` | `is_active` | `Strategy` | `is_active` (Boolean) |
| `strategies` | `created_at` | `Strategy` | `created_at` |
| `strategy_conditions` | `id` | `Trigger` | `trigger_id.value` |
| `strategy_conditions` | `condition_name` | `Trigger` | `trigger_name` |
| `strategy_conditions` | `component_type` | `Trigger` | `trigger_type` (TriggerType Enum) |
| `strategy_conditions` | `operator` | `Trigger` | `operator` (ComparisonOperator) |
| `strategy_conditions` | `target_value` | `Trigger` | `target_value` |
| `strategy_conditions` | `variable_params` | `Trigger` | `variable.parameters` (JSON) |
| `tv_trading_variables` | `variable_id` | `TradingVariable` | `variable_id` |
| `tv_trading_variables` | `display_name_ko` | `TradingVariable` | `display_name` |
| `tv_trading_variables` | `purpose_category` | `TradingVariable` | `purpose_category` |
| `tv_trading_variables` | `comparison_group` | `TradingVariable` | `comparison_group` |

### UI ↔ Domain 매핑

| **UI 용어** | **Domain 용어** | **설명** | **비고** |
|:----------|:-------------|:--------|:--------|
| "전략" | `Strategy` | 매매 전략 | Aggregate Root |
| "조건" | `Trigger` | 매매 조건/트리거 | Entity |
| "변수" | `TradingVariable` | 기술적 지표 | Value Object |
| "진입 조건" | `TriggerType.ENTRY` | 진입 트리거 | Enum 값 |
| "청산 조건" | `TriggerType.EXIT` | 청산 트리거 | Enum 값 |
| "관리 조건" | `TriggerType.MANAGEMENT` | 관리 트리거 | Enum 값 |
| "신호 충돌 해결" | `ConflictResolution` | 신호 충돌 해결 방식 | Value Object |
| "우선순위" | `ConflictResolution.PRIORITY` | 우선순위 기반 해결 | Enum 값 |
| "보수적" | `ConflictResolution.CONSERVATIVE` | 보수적 신호 채택 | Enum 값 |
| "병합" | `ConflictResolution.MERGE` | 신호 병합 처리 | Enum 값 |

---

## 🎯 사용 지침

### ✅ DO (권장사항)

- **일관된 용어 사용**: 같은 개념은 항상 같은 용어로 표현
- **명확한 구분**: Entity, Value Object, Service 구분 명확히
- **표준 네이밍**: 팀 컨벤션 준수 (PascalCase Entity, snake_case method)
- **문서 업데이트**: 새로운 용어 추가 시 이 문서 갱신
- **Domain Events 활용**: 상태 변경 시 적절한 도메인 이벤트 발행
- **Mock 패턴**: Domain 구현 전 Infrastructure 호환성을 위한 Mock 사용
- **Infrastructure 로깅 사용**: `create_component_logger()` 필수 사용
- **MVP 패턴 적용**: Settings 시스템처럼 View와 Presenter 분리
- **직접 import**: 호환성 alias 금지, 명시적 import 사용

### ❌ DON'T (금지사항)

- **혼용 금지**: `Strategy` ↔ `전략` ↔ `strategy` 혼용
- **축약 금지**: `Stg`, `Trig` 등 축약어 사용
- **중복 정의**: 같은 개념에 다른 클래스명 부여
- **레거시 용어**: 사용하지 않는 테이블/컬럼 참조
- **하드코딩 Entity**: Mock 대신 실제 Entity 하드코딩 (Domain 미완성 시)
- **도메인 규칙 우회**: Repository에서 도메인 로직 처리
- **print 문 사용**: Infrastructure 로깅 시스템 대신 print 문 사용 금지
- **호환성 alias 사용**: 투명성 저해, 직접 import 필수

---

## 📚 관련 문서

- [DB 스키마](DB_SCHEMA.md): 데이터베이스 구조 상세
- [아키텍처 개요](ARCHITECTURE_OVERVIEW.md): DDD 구조 이해
- [개발 체크리스트](DEV_CHECKLIST.md): 용어 사용 검증
- [스타일 가이드](STYLE_GUIDE.md): 코딩 표준

---

**💡 핵심**: "한 번 정의된 용어는 모든 Layer에서 일관되게 사용한다!"

**⚡ 업데이트 규칙**: 새로운 Entity나 Value Object 추가 시 반드시 이 문서에 용어 정의 추가
