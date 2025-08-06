# 🏗️ 시스템 아키텍처 및 개발 기준 통합 가이드

> **목적**: DDD 기반 업비트 자동매매 시스템의 아키텍처 구조와 개발 표준 통합 안내
> **범위**: 프로젝트 명세, DDD 아키텍처, 개발 체크리스트, 에러 처리, 데이터베이스
> **갱신**: 2025-08-06

---

## 🎯 프로젝트 핵심 명세 (PROJECT_SPECIFICATIONS)

### 기술 스택 및 아키텍처
- **기술스택**: Python 3.8+, PyQt6, SQLite, pandas, ta-lib
- **아키텍처**: DDD 기반 계층형 아키텍처 (Domain-Driven Design)
- **개발환경**: Windows (PowerShell 5.1+), Python 3.8+ (타입 힌트), PyQt6, SQLite3, pytest

### 핵심 비즈니스 로직
- **종목 스크리닝**: 24시간 거래대금, 7일 변동성, 가격 추세 기반 필터링
- **매매 전략**: 1개 진입 전략(필수) + 0~N개 관리 전략(선택) 조합
- **진입 전략 6종**: 이동평균 교차, RSI, 볼린저 밴드, 변동성 돌파, MACD, 스토캐스틱
- **관리 전략 6종**: 물타기, 불타기, 트레일링 스탑, 고정 익절/손절, 부분 청산, 시간 기반 청산
- **트리거 빌더**: 3중 카테고리 호환성 시스템 (purpose_category, chart_category, comparison_group)

### DDD 계층 구조
- **Presentation Layer**: PyQt6 UI (표시만 담당, Passive View)
- **Application Layer**: Use Case 구현, Service 계층
- **Domain Layer**: 핵심 비즈니스 로직, Entity, Value Object
- **Infrastructure Layer**: 외부 연동, Repository 구현, Database 접근

### 3-Database 아키텍처
- **settings.sqlite3**: 시스템 구조 정의 (변수 정의, 파라미터 스키마)
- **strategies.sqlite3**: 사용자 전략 저장 (전략 인스턴스, 백테스팅 결과)
- **market_data.sqlite3**: 시장 데이터 캐시 (가격 데이터, 기술적 지표)

### 성능 및 보안 요구사항
- **성능**: 백테스팅 5분 내, UI 응답 100ms 내, 실시간 데이터 1초 내 갱신
- **보안**: API 키 환경변수, 로깅 마스킹, 개인정보 Git 추적 방지
- **사용성**: 드래그앤드롭 직관적 구성, 실시간 미리보기, 명확한 에러 메시지

---

## 🏗️ DDD 기반 컴포넌트 아키텍처 (COMPONENT_ARCHITECTURE)

### 계층별 역할 정의
- **Presentation**: main_window, presenters (MVP), views (Passive), components (재사용)
- **Application**: services (Use Case), dto (데이터 전송), commands (Command 패턴)
- **Domain**: entities (도메인 엔티티), value_objects (값 객체), services (도메인 서비스), repositories (추상), events (도메인 이벤트)
- **Infrastructure**: repositories (구체 구현), external_apis (외부 API), database (DB 접근), messaging (이벤트 버스)

### 핵심 컴포넌트 설계
- **트리거 시스템**: TriggerCondition (개별 조건), TriggerRule (조건 조합), TriggerBuilder (메인), CompatibilityValidator (호환성 검증)
- **전략 시스템**: EntryStrategy (진입), ManagementStrategy (관리), StrategyCombiner (조합), 신호 충돌 해결
- **UI 컴포넌트**: BaseWidget (기본), ConditionCard (조건 카드), RuleBuilder (규칙 빌더), setup_ui/style/events 분리

### 데이터 흐름 패턴
- **트리거 생성**: 사용자 입력 → UI 컴포넌트 → 조건 생성 → 호환성 검증 → 규칙 조합 → DB 저장
- **매매 신호**: 시장 데이터 → 지표 계산 → 조건 평가 → 규칙 평가 → 전략 실행 → 매매 신호
- **전략 실행**: 진입 신호 → 포지션 생성 → 관리 전략 활성화 → 리스크 관리 → 포지션 종료

### 의존성 관리
- **의존성 주입**: DIContainer, ApplicationContext 자동 등록
- **인터페이스**: IMarketDataService, IDatabaseService, ILoggingService
- **테스트 가능**: 의존성 주입으로 Mock Service 활용, 계층별 독립 테스트

### Infrastructure 스마트 로깅 v4.0 통합
- **자동 LLM 브리핑**: 마크다운 형태 실시간 상태 보고서 자동 생성
- **JSON 대시보드**: 구조화된 모니터링 데이터로 실시간 차트/API 연동
- **성능 최적화**: 비동기 처리(1000+ 로그/초), 메모리 자동 최적화, 지능형 캐싱
- **완전 역호환**: 기존 v3.0/v3.1 시스템과 동시 사용 가능

---

## ✅ 개발 검증 체크리스트 (DEV_CHECKLIST)

### 🎯 최종 검증 기준: 기본 7규칙 전략
- **RSI 과매도 진입**: 트리거 빌더에서 RSI < 20 조건 생성 가능
- **불타기/물타기**: 수익 시 추가 매수, 손실 시 평단가 낮추기 설정 가능
- **트레일링 스탑**: 수익 보호 후행 손절, 고정 익절/손절 설정 가능
- **전략 조합**: 진입 + 관리 전략 조합하여 완전한 매매 전략 구성
- **백테스팅**: 7규칙 조합 전략의 백테스팅 정상 동작 확인

### DDD 아키텍처 준수
- **Domain Layer**: Business Rule이 Entity 클래스에 포함, Value Object로 ID/Signal 구현, Domain Service로 복잡한 규칙 처리
- **Application Layer**: Use Case가 Application Service로 구현, DTO 사용, Command/Query 분리, 트랜잭션 관리
- **Infrastructure Layer**: 구체적 Repository 구현, 외부 API 격리, 의존성 주입

### 데이터베이스 개발
- **3-DB 구조**: data/*.sqlite3 파일만 사용, data_info/*.sql 스키마, data_info/*.yaml 변수 관리
- **DB 연결**: DatabaseManager() 클래스 사용, DB 연결 실패 시 명확한 에러, 원자적 DB 작업
- **테이블명**: tv_ 접두사 사용 (tv_trading_variables), 폐기 DB 언급 금지

### UI 개발 (PyQt6)
- **컴포넌트**: screens/*/components/ 폴더로 관리, PyQt6 시그널/슬롯, 재사용 가능한 구현
- **스타일링**: QSS 파일 사용 (하드코딩 금지), 다크/라이트 테마 대응, 창 크기 변경 대응
- **테마 시스템**: objectName 기반 스타일링, apply_matplotlib_theme_simple() 차트 적용

### 변수 호환성 시스템
- **3중 카테고리**: purpose_category (trend, momentum, volatility), chart_category (overlay, subplot), comparison_group (price_comparable, percentage_comparable)
- **호환성 검증**: 실시간 UI 검증, 비호환 조합 경고 표시, 호환되지 않는 변수 선택 목록 제외

### 코드 품질
- **기본 원칙**: PEP 8 준수 (79자 제한), 타입 힌트 필수, 단일 책임 (함수 20줄 이하), DRY 원칙, 의미있는 이름
- **로깅**: create_component_logger("ComponentName") 사용, 환경변수 제어, LLM 에이전트 구조화 보고
- **테스트**: pytest 기반 단위테스트, 성공/엣지 케이스, Mock 활용, 7규칙 전체 워크플로 검증

### 커밋 전 최종 검증
- **GUI 실행**: python run_desktop_ui.py 정상 실행
- **7규칙 구성**: 트리거 빌더에서 7규칙 전략 구성 가능
- **백테스팅**: 구성한 전략의 백테스팅 정상 동작
- **기존 기능**: 기존 기능에 영향 주지 않음

---

## 🚨 DDD 기반 에러 처리 정책 (ERROR_HANDLING_POLICY)

### 핵심 철학: "종기의 고름을 뺀다"
- **Domain Layer 에러를 숨기지 말고 명확히 드러내라**
- **Infrastructure 로깅으로 즉시 파악하고 빠른 문제 해결**

### DDD 계층별 에러 처리
- **Domain Layer**: Business Rule 위반 시 명확한 Domain Exception 발생
- **Application Layer**: Use Case 실패 시 구체적인 Application Exception 전파
- **Infrastructure Layer**: 외부 의존성 실패 시 Infrastructure Exception으로 래핑
- **Presentation Layer**: 사용자 친화적 에러 메시지로 변환

### 금지되는 폴백 패턴
- **Domain Service Import 에러 숨김**: try/except ImportError로 더미 클래스 제공 금지
- **Business Logic 폴백**: Domain Rule 위반을 무시하고 추가하는 행위 금지
- **Repository 폴백**: 저장 실패했는데 성공한 것처럼 행동하는 패턴 금지

### 허용되는 최소 예외 처리
- **UI 구조 보존**: UI가 완전히 깨지지 않도록 최소 구조만 제공
- **외부 의존성**: 외부 라이브러리 등 선택적 기능의 graceful degradation
- **네트워크/파일**: 외부 리소스 접근 실패 시 명확한 에러 상태 표시

### Infrastructure 로깅 기반 디버깅
- **실시간 에러 감지**: create_component_logger() 사용, 문제 발생 즉시 LLM 에이전트 인식
- **구조화된 보고**: 🤖 LLM_REPORT: Operation, Status, Details 형식으로 보고
- **환경변수 제어**: UPBIT_LOG_CONTEXT='debugging', UPBIT_LOG_SCOPE='debug_all', UPBIT_CONSOLE_OUTPUT='true'

### 개발 시 확인사항
- **Import 에러**: 잘못된 경로로 import 시 즉시 실패하는지
- **DB 연결 실패**: 데이터베이스 없을 때 명확한 에러 메시지 표시하는지
- **파라미터 오류**: 잘못된 파라미터 전달 시 구체적인 검증 메시지 제공하는지
- **UI 컴포넌트 오류**: 필수 UI 요소 로드 실패 시 즉시 표시되는지

---

## 🗄️ DDD 기반 데이터베이스 스키마 (DB_SCHEMA)

### Infrastructure Layer Repository 구현
- **Domain Entity 매핑**: Aggregate Root를 데이터베이스 테이블로 매핑
- **Repository Pattern**: Domain Layer Repository Interface → Infrastructure 구현
- **Data Mapper**: Entity ↔ 데이터베이스 레코드 변환

### 1. settings.sqlite3 - Domain Configuration
- **tv_trading_variables**: VariableId, DisplayName, PurposeCategory, ChartCategory, ComparisonGroup
- **tv_variable_parameters**: ParameterDefinition, ParameterType, DefaultValue, MinMax, EnumOptions
- **tv_indicator_categories**: CategoryType, CategoryKey, CategoryName, Description, Icon, ColorCode
- **cfg_app_settings**: key-value 앱 전역 설정

### 2. strategies.sqlite3 - Strategy Aggregate
- **strategies**: Strategy Entity (id, strategy_name, description, is_active, created_at)
- **strategy_conditions**: Trigger Entity (id, condition_name, strategy_id, variable_id, operator, target_value)
- **backtest_results**: 백테스팅 결과 (strategy_id, total_return, max_drawdown, sharpe_ratio, win_rate)
- **execution_logs**: 실행 기록 (strategy_id, symbol, action, price, quantity, timestamp)

### 3. market_data.sqlite3 - Market Data Aggregate
- **price_data**: OHLCV 데이터 (symbol, timestamp, timeframe, open/high/low/close, volume)
- **indicator_cache**: 기술적 지표 캐시 (symbol, timestamp, indicator_name, value, additional_data)
- **market_info**: 시장 정보 (symbol, korean_name, tick_size, min_order_amount)

### Domain Entity → DB 매핑
- **Strategy.strategy_id.value** → strategies.id
- **Strategy.name** → strategies.strategy_name
- **Trigger.trigger_name** → strategy_conditions.condition_name
- **TradingVariable.variable_id** → tv_trading_variables.variable_id
- **ParameterDefinition** → tv_variable_parameters.*

### Repository 구현 패턴
- **SqliteStrategyRepository**: Strategy Aggregate 저장소 구현
- **SqliteTriggerRepository**: Trigger Entity 저장소 구현
- **SqliteSettingsRepository**: 설정 저장소 구현
- **Unit of Work**: 트랜잭션 일관성 보장

### 성능 최적화
- **인덱스**: idx_price_data_symbol_time, idx_indicator_cache_lookup
- **정기 정리**: 30일 이상 분봉 데이터 삭제, 7일 이상 지표 캐시 정리
- **백업 전략**: settings 주간, strategies 일일, market_data 백업 제외 (재생성 가능)

---

## 💡 핵심 원칙 요약

### 절대 변경 금지
- **7규칙 전략**: 모든 개발의 최종 검증 기준
- **3-DB 구조**: settings, strategies, market_data 분리 구조
- **에러 투명성**: 문제를 숨기지 말고 즉시 드러내기
- **PowerShell**: 모든 터미널 명령어는 PowerShell 구문 사용

### 아키텍처 가이드라인
- **DDD 4계층**: Presentation → Application → Domain ← Infrastructure
- **컴포넌트 기반**: 재사용 가능한 모듈화된 구조
- **의존성 역전**: 인터페이스 통한 추상화 의존
- **이벤트 기반**: 도메인 이벤트로 느슨한 결합

### 개발 표준
- **코딩**: PEP 8, 타입 힌트, 단일 책임, DRY 원칙
- **테스트**: pytest 기반, Mock 활용, 90% 커버리지
- **로깅**: Infrastructure 스마트 로깅 v4.0, LLM 에이전트 보고
- **테마**: QSS 기반, 다크/라이트 지원, 접근성 고려

---

**🎯 성공 기준**: 새로운 아키텍처에서도 기본 7규칙 전략이 완벽하게 동작해야 함
**💡 핵심**: 의심스러우면 7규칙 전략으로 검증, DDD 원칙 준수, 에러 투명성 유지!
