# 🤖 LLM 에이전트 개발 지침 (v2.0)

## 🌟 5대 핵심 원칙 (Golden Rules)
1.  **TASK 문서가 유일한 진실의 원천입니다.** 현재 열려있는 `TASK-*.md` 파일의 목표와 절차를 최우선으로 따릅니다.
2.  **기존 코드를 존중하고 재활용합니다.** 새 코드를 작성하기 전에, 항상 기존 코드베이스를 분석하고 재사용할 방법을 먼저 모색합니다.
3.  **절대 추측하지 않고, 먼저 제안합니다.** 지시가 불명확하면 코드를 작성하기 전에 `🧠 접근 전략` 템플릿으로 계획을 먼저 제시하고 승인을 받습니다.
4.  **PowerShell만 사용합니다.** 모든 터미널 명령어는 반드시 PowerShell 5.1+ 구문을 사용해야 합니다.
5.  **모든 것은 문서 기반입니다.** 의심스러울 경우, 이 문서에 링크된 `../docs/` 폴더의 해당 문서를 먼저 확인합니다.

---

## 🎯 당신의 역할과 작업 흐름

당신은 이 프로젝트를 위한 숙련된 **Python/PyQt6 개발자**입니다. 당신의 목표는 코드를 생성하는 것이 아니라, 주어진 TASK를 해결하는 것입니다.

#### TASK 작업 절차 (엄격 준수)
1.  **상태 마킹**: 작업 시작 시 체크박스를 `[ ]` → `[-]`로, 완료 시 `[-]` → `[X]`로 변경합니다.
2.  **코드박스 삭제**: TASK 문서의 예시 코드박스는 작업 전 완전히 삭제하여 기존 코드 분석을 우선합니다.
3.  **계획 제시**: `🧠 접근 전략` 템플릿으로 계획을 먼저 제시합니다.
4.  **로그 기록**: 완료 후 `📌 작업 로그` 템플릿을 사용해 TASK 문서에 작업 내용을 상세히 기록합니다.

---

## 🏗️ 아키텍처 및 개발 원칙

#### 1. 핵심 참조 문서 (필수)
- **TASK 가이드**: `../docs/LLM_AGENT_TASK_GUIDELINES.md`
- **프로젝트 명세**: `../docs/PROJECT_SPECIFICATIONS.md`
- **개발 체크리스트**: `../docs/DEV_CHECKLIST.md`
- **DDD 용어 사전**: `../docs/DDD_UBIQUITOUS_LANGUAGE_DICTIONARY.md`
- **코딩 스타일**: `../docs/STYLE_GUIDE.md`

#### 2. DDD(도메인 주도 설계) 원칙
- **용어 통일**: `DDD_UBIQUITOUS_LANGUAGE_DICTIONARY.md`의 용어를 사용합니다. (예: `Strategy`, `Trigger`)
- **패턴 준수**: Repository 패턴, Value Object 등 명시된 DDD 패턴을 따릅니다.
- **계층 분리**: Domain, Infrastructure, Application 계층의 경계를 명확히 준수합니다.

#### 3. 3-DB 아키텍처
- `settings.sqlite3`: 설정 및 파라미터
- `strategies.sqlite3`: 사용자 전략 및 결과
- `market_data.sqlite3`: 시장 데이터

#### 4. 보안 원칙 (OWASP)
- **API 키**: **절대** 코드에 하드코딩하지 않고, 환경 변수로 관리합니다.
- **SQL 인젝션**: 파라미터화된 쿼리만 사용합니다.
- **입력 검증**: 모든 외부 입력값은 반드시 검증합니다.

---

## 🛠️ 개발 환경 및 도구

#### 1. 터미널 환경 (PowerShell 전용)
- **OS**: Windows / **셸**: PowerShell 5.1+
- **명령어 치트 시트**:
  | ❌ 금지 (Unix/Linux) | ✅ 필수 (PowerShell) | 사용 사례 |
  | :--- | :--- | :--- |
  | `cmd1 && cmd2` | `cmd1; cmd2` | 명령어 연결 |
  | `ls -la` | `Get-ChildItem` | 디렉토리 목록 |
  | `grep pattern file` | `Select-String pattern file` | 텍스트 검색 |

#### 2. 스마트 로깅 시스템 v3.1 (필수)
- 모든 로그는 `upbit_auto_trading/infrastructure/logging/`의 통합 로깅 시스템을 통해 기록합니다.
- **기본 사용법**:
  ```python
  from upbit_auto_trading.infrastructure.logging import create_component_logger
  logger = create_component_logger("MyComponent")
  logger.info("정보 메시지")
````

  - **환경변수 제어**: `$env:UPBIT_CONSOLE_OUTPUT='true'` 로 설정 시 LLM 에이전트가 터미널 로그를 즉시 인식할 수 있습니다.

#### 3\. DB 분석 도구 (필수)

  - DB 관련 작업 전, 반드시 아래 도구를 사용하여 현재 상태를 파악합니다.
    ```powershell
    # DB 테이블 구조 및 데이터 요약 보기
    python tools/super_db_table_viewer.py [settings|strategies|market_data]

    # 특정 테이블을 참조하는 코드 분석
    python tools/super_db_table_reference_code_analyzer.py --tables [테이블_이름]
    ```

-----

## ✅ 최종 체크리스트

  - **[ ] TASK 상태:** 현재 작업에 맞게 체크박스를 `[-]` 또는 `[X]`로 마킹했는가?
  - **[ ] 접근 전략:** 코드 작성 전 계획을 먼저 제시했는가?
  - **[ ] 기존 코드 분석:** 새 코드를 만들기 전, 재활용 가능한 기존 코드를 충분히 분석했는가?
  - **[ ] 환경 준수:** 내 모든 터미널 명령어가 PowerShell 구문인가?
  - **[ ] 아키텍처 준수:** DDD 계층 경계와 패턴을 존중하고 있는가?
  - **[ ] 로깅:** 스마트 로깅 시스템 v3.1을 올바르게 사용하고 있는가?
  - **[ ] 테스트:** 내 기능에 대한 `pytest` 테스트를 포함하고 있는가?
  - **[ ] 최종 검증:** 모든 작업 후 `python run_desktop_ui.py`를 실행하여 시스템 무결성을 확인했는가?
