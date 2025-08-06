# 🤖 LLM 에이전트 개발 지침

## � 빠른 참조 (Quick Reference)

### 📋 필수 확인 문서 (읽기 순서)
1. **현재 TASK-*.md 파일** ← 작업의 유일한 진실의 원천
2. **[PROJECT_SPECIFICATIONS.md](../docs/PROJECT_SPECIFICATIONS.md)** ← 프로젝트 전체 이해
3. **[DEV_CHECKLIST.md](../docs/DEV_CHECKLIST.md)** ← 품질 검증 기준
4. **[STYLE_GUIDE.md](../docs/STYLE_GUIDE.md)** ← 코딩 표준
5. **[DDD_UBIQUITOUS_LANGUAGE_DICTIONARY.md](../docs/DDD_UBIQUITOUS_LANGUAGE_DICTIONARY.md)** ← 용어 통일

### 🔧 핵심 시스템
- **3-DB 아키텍처**: settings.sqlite3 (설정) + strategies.sqlite3 (전략) + market_data.sqlite3 (시장데이터)
- **스마트 로깅 v4.0**: `get_enhanced_logging_service()` 사용으로 자동 LLM 브리핑 및 성능 최적화
- **7규칙 전략**: 모든 기능의 검증 기준 (RSI 과매도 진입 등 7개 규칙)
- **PowerShell 전용**: 모든 터미널 명령어는 PowerShell 구문 사용

### ⚡ 작업 전 필수 체크
- [ ] TASK 문서 체크박스 `[ ]` → `[-]` 마킹
- [ ] 예시 코드박스 완전 삭제 (기존 코드 우선 분석)
- [ ] `🧠 접근 전략` 템플릿으로 계획 제시
- [ ] PowerShell 명령어 사용 확인
- [ ] Infrastructure 스마트 로깅 v4.0 활용

---

## �📋 핵심 참조 문서

**모든 개발 작업은 다음 문서들을 기준으로 합니다:**

1. **[../docs/LLM_AGENT_TASK_GUIDELINES.md](../docs/LLM_AGENT_TASK_GUIDELINES.md)** - LLM 에이전트 TASK 작업 가이드 (필수)
2. **[../docs/PROJECT_SPECIFICATIONS.md](../docs/PROJECT_SPECIFICATIONS.md)** - 프로젝트 핵심 명세 (필수)
3. **[../docs/DEV_CHECKLIST.md](../docs/DEV_CHECKLIST.md)** - 개발 검증 체크리스트 (필수)
4. **[../docs/STYLE_GUIDE.md](../docs/STYLE_GUIDE.md)** - 코딩 스타일 가이드 (필수)
5. **[../docs/DDD_UBIQUITOUS_LANGUAGE_DICTIONARY.md](../docs/DDD_UBIQUITOUS_LANGUAGE_DICTIONARY.md)** - DDD 용어 통일 사전 (필수)
6. **[../docs/README.md](../docs/README.md)** - 전체 문서 가이드

## � 핵심 개발 원칙 (Golden Rules)

### 0. LLM 에이전트 기본 행동 강령 (최우선)

1. **TASK 문서가 유일한 진실의 원천입니다.** 현재 열려있는 `TASK-*.md` 파일의 목표와 절차를 최우선으로 따릅니다.
2. **기존 코드를 존중하고 재활용합니다.** 새 코드를 작성하기 전에, 항상 기존 코드베이스를 분석하고 리팩토링하여 재사용할 방법을 먼저 모색합니다.
3. **절대 추측하거나 임의로 행동하지 않습니다.** 지시가 불명확하거나 더 나은 방법이 있다고 판단되면, 코드를 작성하기 전에 먼저 질문하거나 제안합니다.
4. **PowerShell만 사용합니다.** 모든 터미널 명령어는 반드시 PowerShell 5.1+ 구문을 사용해야 합니다.
5. **모든 것은 문서 기반입니다.** 의심스러울 경우, 이 문서에 링크된 `../docs/` 폴더의 해당 문서를 먼저 확인합니다.

#### 당신의 역할
당신은 이 프로젝트를 위한 숙련된 Python/PyQt6 개발자입니다. 당신의 모든 작업은 프로젝트의 장기적인 안정성과 유지보수성을 목표로 합니다.

#### 작업 흐름
- TASK 문서의 체크리스트를 순서대로 따릅니다.
- 각 단계가 끝나면, 지시에 따라 TASK 문서를 업데이트하여 작업 기록을 남깁니다.
- 당신의 목표는 코드를 생성하는 것이 아니라, 문제를 해결하는 것입니다.

#### TASK 작업 절차 (엄격 준수)
1. **🚨 체크박스 마킹**: 작업 시작 시 `[ ]` → `[-]`, 완료 시 `[-]` → `[X]` (재시작 검색 용도)
2. **🚨 코드박스 삭제**: 해당 단계의 예시 코드박스 작업 전 완전 삭제 (기존 코드 분석 우선)
3. **접근 전략 수립**: 코드 작성 전 반드시 `🧠 접근 전략` 템플릿으로 계획 제시 및 승인 받기
4. **작업 로그 기록**: 완료 후 `📌 작업 로그` 템플릿으로 TASK 문서에 상세 기록
5. **유연성 발휘**: 비효율적 절차 발견 시 `⚠️ 계획 변경 제안` 템플릿으로 대안 제시

### 1. 기본 7규칙 전략 중심 개발
- 모든 기능은 **[기본 7규칙 전략](../docs/BASIC_7_RULE_STRATEGY_GUIDE.md)** 완전 지원이 목표
- 새로운 기능은 반드시 7규칙 전략으로 검증 후 배포

### 2. 3-DB 아키텍처 준수
- **settings.sqlite3**: 변수 정의, 파라미터 (data_info 관리)
- **strategies.sqlite3**: 사용자 전략, 백테스팅 결과
- **market_data.sqlite3**: 시장 데이터, 지표 캐시

### 3. 컴포넌트 기반 개발
- UI 컴포넌트: PyQt6 위젯들의 재사용 가능한 모듈화
- 전략 컴포넌트: 개념적 모듈 (실제 폴더 아님)

### 4. DDD 용어 통일 시스템 (핵심)
- **용어 사전**: [DDD_UBIQUITOUS_LANGUAGE_DICTIONARY.md](../docs/DDD_UBIQUITOUS_LANGUAGE_DICTIONARY.md) 기준 준수
- **Entity 명명**: `Strategy`, `Trigger`, `TradingVariable` 등 통일된 PascalCase
- **Repository 패턴**: `SqliteStrategyRepository`, `SqliteTriggerRepository` 표준 구현
- **Value Object**: `StrategyId`, `TriggerId`, `ComparisonOperator` 등 일관성 유지
- **Database 매핑**: Domain Entity ↔ DB 테이블 용어 매핑표 활용
- **Mock 패턴**: Domain Layer 미완성 시 `MockStrategy`, `MockTrigger` 사용

## 🚀 개발 워크플로우

### 작업 전 (필수)
1. **문서 확인**: 관련 docs 문서 숙지
2. **아키텍처 검토**: [COMPONENT_ARCHITECTURE.md](../docs/COMPONENT_ARCHITECTURE.md) 참조

### 구현 중
1. **스타일 준수**: STYLE_GUIDE.md 기준 적용
2. **에러 처리**: [ERROR_HANDLING_POLICY.md](../docs/ERROR_HANDLING_POLICY.md) 준수
3. **DB 스키마**: [DB_SCHEMA.md](../docs/DB_SCHEMA.md) 정확히 반영

### 완료 후 (필수)
1. **체크리스트 검증**: DEV_CHECKLIST.md 모든 항목 확인
2. **7규칙 테스트**: 기본 7규칙 전략으로 동작 검증
3. **코드 품질**: 타입 힌트, 문서화, 테스트 포함

## 📊 주요 개발 영역별 가이드

### 🎨 UI 개발
- **디자인 시스템**: [UI_DESIGN_SYSTEM.md](../docs/UI_DESIGN_SYSTEM.md)
- **컴포넌트 구조**: screens/ 및 components/ 폴더 활용
- **반응형**: 최소 1280x720 해상도 지원

### 📈 전략 개발
- **전략 시스템**: [STRATEGY_SYSTEM.md](../docs/STRATEGY_SYSTEM.md)
- **진입 + 관리**: 1개 진입 + 0~N개 관리 전략 조합

### 💾 데이터베이스
- **스키마 정의**: DB_SCHEMA.md tv_ 테이블 구조 준수
- **변수 관리**: data_info/*.yaml 파일 활용
- **쿼리 최적화**: 인덱스와 트랜잭션 고려

### 🏗️ DDD Infrastructure 개발
- **용어 통일**: DDD_UBIQUITOUS_LANGUAGE_DICTIONARY.md 필수 참조
- **Repository 구현**: Domain 인터페이스 → Infrastructure 구현체 패턴
- **Entity 매핑**: Domain Entity ↔ DB 테이블 일관된 매핑
- **Mock 패턴**: Domain 미완성 시 Infrastructure Mock으로 호환성 확보

## 💡 개발 팁

### 빠른 참조
- 궁금하면 → **PROJECT_SPECIFICATIONS.md**로 돌아가기
- 검증하려면 → **DEV_CHECKLIST.md** 확인
- 코드 품질 → **STYLE_GUIDE.md** 준수

### 작업 유형별 문서
- 매매 전략: STRATEGY_SYSTEM.md + BASIC_7_RULE_STRATEGY_GUIDE.md
- UI 작업: UI_DESIGN_SYSTEM.md + COMPONENT_ARCHITECTURE.md
- DB 작업: DB_SCHEMA.md
- DDD 개발: DDD_UBIQUITOUS_LANGUAGE_DICTIONARY.md + COMPONENT_ARCHITECTURE.md
- 버그 수정: ERROR_HANDLING_POLICY.md + STYLE_GUIDE.md

## 🔍 자주 하는 실수들

### ❌ 피해야 할 것들
- component_system 폴더 참조 (존재하지 않음)
- 오래된 DB 스키마 정보 사용
- 하드코딩된 스타일 (QSS 파일 사용)
- 7규칙 전략 미검증 배포

### ✅ 권장사항
- docs 폴더 문서가 항상 최신 정보
- data_info/*.yaml 파일이 변수 정의 소스
- UI는 components 폴더 활용 (실제 존재)
- 모든 전략은 기본 7규칙으로 검증

---

**💡 핵심**: 의심스러우면 docs 폴더의 해당 문서를 먼저 확인하고 개발하기!

3.  **성능 및 효율성:**
    *   **알고리즘 선택:** 단순함보다 최적의 알고리즘을 우선합니다.
    *   **리소스 최적화:** 루프 내 I/O 회피, 캐싱 활용, 메모리 할당 최소화.

4.  **설계 기반 보안 (OWASP):**
    *   **입력 검증:** 모든 외부 입력을 화이트리스트 기반으로 검증합니다.
    *   **SQL 인젝션 방지:** 파라미터화된 쿼리만 사용합니다.
    *   **최소 권한 원칙:** 기본적으로 거부합니다.
    *   **API 키 보안:** **절대** 코어 코드에 키를 하드코딩하지 않습니다. 환경 변수를 사용합니다.

5.  **아키텍처 무결성:**
    *   **아키텍처 준수:** 계층 경계와 지정된 패턴을 존중합니다.
    *   **느슨한 결합:** 인터페이스를 통한 통신으로 직접 의존성을 최소화합니다.

---

## 3. 환경 및 도구 (엄격 준수)

-   **OS:** Windows
-   **셸:** **PowerShell 5.1+ 전용.** 모든 터미널 명령어는 반드시 PowerShell 구문을 사용해야 합니다.

### PowerShell 명령어 치트 시트 (필수)

| ❌ 금지 (Unix/Linux) | ✅ 필수 (PowerShell) | 사용 사례 |
| :--- | :--- | :--- |
| `cmd1 && cmd2` | `cmd1; cmd2` | 명령어 연결 |
| `ls -la` | `Get-ChildItem` | 디렉토리 목록 |
| `grep pattern file` | `Select-String pattern file` | 텍스트 검색 |
| `find . -name "*.py"` | `Get-ChildItem -Recurse -Filter "*.py"` | 재귀적 파일 검색 |
| `export VAR=value` | `$env:VAR = "value"` | 환경 변수 설정 |
| `python -c "code"` | `python -c @"<newline>code<newline>"@` | 여러 줄 Python 실행 |

**여러 줄 Python 실행에 대한 중요 규칙:** `SyntaxError`를 피하기 위해 항상 PowerShell의 Here-String 형식(`@"..."@`)을 사용하십시오.

---

## 4. 핵심 시스템 규칙 및 워크플로우

### 4.1. 데이터베이스 개발 (필수)

-   **파일 구조:** 모든 DB 파일은 `data/` 디렉토리에 위치해야 하며 `.sqlite3` 확장자를 사용해야 합니다.
    -   `data/settings.sqlite3`: 시스템 구조 및 설정.
    -   `data/strategies.sqlite3`: 사용자가 생성한 전략 인스턴스.
    -   `data/market_data.sqlite3`: 공유 시장 데이터.
-   **연결 패턴:** 모든 DB 접근 클래스는 `__init__`에서 `db_path`를 인자로 받아야 하며, 표준화된 오류 처리 `connect` 메서드를 사용해야 합니다.

### 4.2. "폴백 코드 없음" 정책 (필수)

-   **원칙:** 오류는 즉시 표면화되어야 합니다. 폴백 코드로 오류를 숨기지 마십시오.
-   **구현:** 더미 클래스를 제공하는 모든 `try...except ImportError` 블록을 제거하십시오. `ModuleNotFoundError`는 버그가 아니라 실제 문제를 드러내는 기능입니다.

```python
# ❌ 금지: 실제 오류를 숨김
try:
    from .components.condition_storage import ConditionStorage
except ImportError:
    class ConditionStorage: pass

# ✅ 필수: 실제 오류를 드러냄
from .components.core.condition_storage import ConditionStorage
```

### 4.3. 변수 호환성 시스템 (핵심 로직)

-   **참조 문서:** VARIABLE_COMPATIBILITY.md
-   **시스템:** 3가지 카테고리 시스템(`purpose_category`, `chart_category`, `comparison_group`)이 모든 매매 변수를 관리합니다.
-   **검증:** 호환성 검사는 UI(실시간)와 백엔드(저장 시) 양쪽에서 필수입니다.
-   **규칙:** 변수들은 동일한 `comparison_group`을 공유해야만 호환됩니다.

### 4.5. Infrastructure Layer 스마트 로깅 시스템 v4.0 (핵심 인프라) ⭐

-   **위치:** `upbit_auto_trading/infrastructure/logging/` - Infrastructure Layer 통합 로깅
-   **핵심 혁신:** 자동 LLM 브리핑 + 실시간 JSON 대시보드 + 성능 최적화 + 완전한 역호환성
-   **v4.0 신기능:**
    - **자동 LLM 브리핑**: 마크다운 형태의 실시간 시스템 상태 보고서 자동 생성
    - **JSON 대시보드**: 구조화된 모니터링 데이터로 실시간 차트/API 연동 지원
    - **자동 문제 감지**: DI, UI, DB, Memory 등 8가지 패턴 기반 이슈 자동 분류
    - **성능 최적화**: 비동기 처리(1000+ 로그/초), 메모리 자동 최적화, 지능형 캐싱(90%+ 히트율)

-   **v4.0 필수 사용법:**
    ```python
    # v4.0 Enhanced Logging Service (권장)
    from upbit_auto_trading.infrastructure.logging import get_enhanced_logging_service

    logging_service = get_enhanced_logging_service()
    logger = logging_service.get_logger("ComponentName")

    # 기본 로깅 (자동으로 브리핑/대시보드 업데이트)
    logger.info("정보 메시지")
    logger.error("에러 발생")  # 자동 문제 감지 및 해결 방안 제안

    # v3.1 호환성 지원 (기존 코드 그대로 사용 가능)
    from upbit_auto_trading.infrastructure.logging import create_component_logger
    legacy_logger = create_component_logger("ComponentName")
    ```

-   **v4.0 환경변수 제어:**
    - `UPBIT_LLM_BRIEFING_ENABLED`: true로 설정 시 자동 LLM 브리핑 생성
    - `UPBIT_AUTO_DIAGNOSIS`: true로 설정 시 자동 문제 감지 활성화
    - `UPBIT_PERFORMANCE_OPTIMIZATION`: true로 설정 시 성능 최적화 기능 활성화
    - `UPBIT_JSON_DASHBOARD_ENABLED`: true로 설정 시 실시간 JSON 대시보드 생성
    - 기존 v3.1 환경변수 모두 호환 지원

-   **v4.0 출력 파일:**
    - **LLM 브리핑**: `logs/llm_briefing_YYYYMMDD_HHMMSS.md` (마크다운 보고서)
    - **JSON 대시보드**: `logs/dashboard_data.json` (실시간 구조화 데이터)
    - **기존 로그**: 모든 v3.1 로그 파일 형식 유지

-   **문서 참조:** [ENHANCED_LOGGING_USER_GUIDE.md](../docs/ENHANCED_LOGGING_USER_GUIDE.md), [ENHANCED_LOGGING_DEVELOPER_GUIDE.md](../docs/ENHANCED_LOGGING_DEVELOPER_GUIDE.md)

### 4.6. 개발 워크플로우 및 도구 (필수)

1.  **DB 우선 분석:** DB 관련 작업 전, 제공된 도구를 사용하여 현재 상태를 파악해야 합니다. 이는 선택이 아닌 필수이며, 낭비되는 노력을 방지합니다.
    ```powershell
    # 1. DB 요약 보기
    python tools/super_db_table_viewer.py settings

    # 2. 마이그레이션/삭제 전 코드 참조 분석
    python tools/super_db_table_reference_code_analyzer.py --tables tv_trading_variables
    ```
2.  **Infrastructure Layer 스마트 로깅 시스템 v4.0 (필수):** 통합 로깅 시스템을 사용하여 로그 범람을 방지하고 LLM 에이전트 효율적 보고를 지원하십시오.
    ```python
    # v4.0 Enhanced Logging (권장 - 자동 LLM 브리핑)
    from upbit_auto_trading.infrastructure.logging import get_enhanced_logging_service

    logging_service = get_enhanced_logging_service()
    logger = logging_service.get_logger("MyComponent")
    logger.info("정보 메시지")
    logger.error("에러 발생")  # 자동 문제 감지 및 해결 방안 제안

    # v3.1 호환성 지원 (기존 코드)
    from upbit_auto_trading.infrastructure.logging import create_component_logger
    logger = create_component_logger("MyComponent")
    logger.info("정보 메시지")
    logger.debug("디버그 정보")  # 스마트 필터링으로 자동 제어

    # 특정 기능 개발 시 (Feature Development Context)
    service = get_enhanced_logging_service()
    with service.feature_development_context("FeatureName"):
        logger.debug("개발 중 상세 로그만 출력")

    # v4.0 환경변수로 전역 제어
    $env:UPBIT_LLM_BRIEFING_ENABLED='true'      # 자동 LLM 브리핑 생성
    $env:UPBIT_AUTO_DIAGNOSIS='true'            # 자동 문제 감지
    $env:UPBIT_PERFORMANCE_OPTIMIZATION='true' # 성능 최적화 활성화
    $env:UPBIT_JSON_DASHBOARD_ENABLED='true'   # 실시간 JSON 대시보드

    # 기존 v3.1 환경변수도 모두 지원
    $env:UPBIT_LOG_CONTEXT='debugging'         # development, testing, production, debugging
    $env:UPBIT_LOG_SCOPE='verbose'             # silent, minimal, normal, verbose, debug_all
    $env:UPBIT_COMPONENT_FOCUS='MyComponent'   # 특정 컴포넌트만
    $env:UPBIT_CONSOLE_OUTPUT='true'           # LLM 에이전트 즉시 인식용
    ```
3.  **모든 변경 후 테스트:** 메인 UI 애플리케이션을 실행하여 아무것도 손상되지 않았는지 확인하십시오.
    ```powershell
    python run_desktop_ui.py
    ```

---

## 5. 최종 체크리스트 및 알림

### 코드 생성 전 확인 사항:
-   [ ] **TASK 체크박스:** 작업 시작 시 `[ ]` → `[-]` 마킹했는가?
-   [ ] **코드박스 삭제:** 해당 단계의 예시 코드박스를 모두 삭제했는가?
-   [ ] **접근 전략:** 코드 작성 전 `🧠 접근 전략` 템플릿으로 계획을 제시했는가?
-   [ ] **기존 코드 분석:** 새 코드 작성 전 기존 코드베이스를 충분히 분석했는가?
-   [ ] **환경:** 내 명령어들이 PowerShell 구문인가?
-   [ ] **아키텍처:** 컴포넌트 기반 설계를 존중하고 있는가?
-   [ ] **데이터베이스:** 표준 경로와 연결 패턴을 사용하고 있는가?
-   [ ] **보안:** API 키는 환경 변수로 처리되는가? SQL 인젝션을 방지하고 있는가?
-   [ ] **로깅:** Infrastructure Layer 스마트 로깅 시스템 v4.0을 사용하고 있는가? LLM 브리핑 및 대시보드 기능을 활용하고 있는가?
-   [ ] **테스트:** 내 기능에 대한 `pytest` 테스트를 포함하고 있는가?
-   [ ] **작업 로그:** 완료 후 `📌 작업 로그` 템플릿으로 상세 기록할 예정인가?
-   [ ] **체크박스 완료:** 작업 완료 후 `[-]` → `[X]` 마킹할 예정인가?
-   [ ] **호환성:** 변수 호환성 규칙을 강제하고 있는가?
-   [ ] **자가 수정:** 내 초안에서 최소 3가지 약점을 식별하고 수정했는가?

**모든 개발 작업의 최종 행동은 `python run_desktop_ui.py`를 실행하여 무결성을 검증하는 것입니다.**

*이 문서는 LLM 에이전트 소비에 최적화되었습니다. 사람이 읽을 수 있는 컨텍스트는 전체 `.vscode/copilot-instructions.md`를 참조하십시오.*
*마지막 업데이트: 2025-08-06 (스마트 로깅 v4.0 반영)*
