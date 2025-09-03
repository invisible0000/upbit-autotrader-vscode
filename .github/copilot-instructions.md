# 📌 업비트 자동매매 시스템 GitHub Copilot Agent 지침 — Master v3.1
> DDD + MVP + Infrastructure v4.0 + PyQt6 + TDD + 실시간 로깅 + Dry-Run 우선 (W### 정보 검증 원칙
- 여러 소스에서 정보 교차 검증
- 공식 문서를 최우선으로 하되, 커뮤니티 사례도 참고
- 수집한 정보는 프로젝트 컨텍스트에 맞게 적절히 가공 후 적용

---

## 🔧 Pylance MCP 도구 활용 가이드
### AI 코드 품질 검증 파트너

Pylance MCP로 AI 생성 코드를 검증하고 프로젝트 통합 시 오류를 사전 방지하세요.

#### 핵심 활용법
- **환경 진단**: "Python 환경과 Pylance 설정을 분석해 주세요"
- **DDD 검증**: "Domain 레이어의 외부 의존성 위반을 체크해 주세요"
- **Import 정리**: "미사용 import와 순환 참조를 찾아 정리해 주세요"
- **타입 검증**: "DTO 클래스의 타입 힌트와 Decimal 정밀도를 확인해 주세요"
- **자동 리팩터링**: "코드 스타일 표준화와 구조 최적화를 실행해 주세요"

#### 워크플로우
AI 코드 생성 → Pylance 검증 → 통합 최적화 (타입 안전성, 아키텍처 준수 자동 확인)

---

## 📋 태스크 관리 & 진행 마커 규칙owerShell 전용)

---

## 🎯 목적과 성공 기준
- 최종 목표: 7규칙 전략이 완벽 동작하는 안전한 자동매매 시스템
- 검증: python run_desktop_ui.py → 전략 관리 → 트리거 빌더에서 7규칙 구성 가능해야 함
- 7규칙: RSI 과매도 진입, 수익시 불타기, 계획된 익절, 트레일링 스탑, 하락시 물타기, 급락 감지, 급등 감지

---

## 🔒 Golden Rules (항상 준수)
- DDD 4계층: Presentation → Application → Domain ← Infrastructure (Domain은 외부 의존 없음)
- 3-DB 분리: data/settings.sqlite3 · data/strategies.sqlite3 · data/market_data.sqlite3
- Windows PowerShell 전용: Unix 명령어 금지, 표준 PS 구문 사용
- Infrastructure 로깅 필수: create_component_logger("ComponentName"), print() 금지
- 파일명 연속성: 교체 시 {name}_legacy.py 백업 후, 새 구현은 원래 파일명 사용

---

## ✅ Must Do
- TDD 우선: 테스트 스텁 → 최소 구현 → 리팩터링 (pytest, Given-When-Then)
- Dry-Run 기본: 모든 주문은 기본 dry_run=True, 실거래는 dry_run=False + 2단계 확인
- DTO 엄격: @dataclass(frozen=True) + 명확한 타입힌트
- 보안: API 키는 환경변수, 코드/로그/테스트에 노출 금지; Decimal 정밀도 고정; Rate limit 백오프

---

## ⛔ Must Not Do
- 계층 위반: Domain에 sqlite3/requests/PyQt6 import 금지, Presenter에서 DB/HTTP/비즈니스 로직 금지
- 에러 숨김/폴백 금지: 도메인 규칙 실패를 try/except로 삼키지 말 것
- UI 스타일 하드코딩 금지: setStyleSheet("color: #333") 등 금지, 개별 QSS 파일 생성 금지
- Unix 명령어 사용 금지: &&, grep, ls 등 금지 (PowerShell만)

---

## 🏗️ DDD + MVP 적용
- Presentation(PyQt6 View: Passive View) → Application(UseCase/Service) → Domain(Entity/VO/Rule) ← Infrastructure(DB/API)
- 의존성 역전 유지: 외부 연동/저장은 Infrastructure로 격리, Domain 순수성 보장

---

## 🎨 UI 전역 스타일 시스템
- 경로: upbit_auto_trading/ui/desktop/common/styles/
- 사용: View는 기본 위젯 스타일 활용 + 필요한 경우 objectName 지정만; Presenter는 스타일 관여 금지
- QSS 테마: 개별 setStyleSheet 하드코딩 금지, 전역 StyleManager/테마 노티파이어 사용
- matplotlib 테마: from upbit_auto_trading.ui.desktop.common.theme_notifier import apply_matplotlib_theme_simple; 차트 전 호출

---

## 📊 변수 호환성 규칙
- purpose_category: trend, momentum, volatility, volume, price
- chart_category: overlay, subplot
- comparison_group: price_comparable, percentage_comparable, zero_centered
- 규칙: 동일 comparison_group만 직접 비교 가능 (강제 검증 필요)

---

## 🔁 작업 프로세스 (전문가 가이드라인) + Ryan-Style 3-Step Vibe Coding

### 작업 분류 & 프로세스 결정 매트릭스
**GitHub Copilot은 요청을 받으면 먼저 아래 분류에 따라 적절한 프로세스를 제안합니다:**

#### 🚀 Ryan-Style 3-Step 트리거 조건
- **새 기능 또는 아키텍처 변경**: "이 작업에는 체계적인 계획이 필요합니다. Ryan-Style 3-Step Vibe Coding 프로세스를 진행할까요?"
- **복잡한 시스템 통합**: "다중 컴포넌트 영향 분석이 필요합니다. 3-Step 프로세스로 진행하시겠습니까?"
- **불확실한 요구사항**: "요구사항 명확화를 위해 PRD부터 시작하는 것이 좋겠습니다. 3-Step으로 진행할까요?"

#### ⚡ 즉시 실행 조건
- **간단한 버그 수정/UI 개선**: 기존 "테스트·품질 게이트" 규칙에 따라 최소 수정 후 검증
- **설정 변경/단순 리팩터링**: 짧은 설명 후 바로 구현

### Ryan-Style 3-Step Vibe Coding 프로세스

#### Step 1: PRD 작성 (제품 요구서)
새 기능이나 아키텍처 변경 시 다음 구조로 PRD 작성:
- **Problem & Users**: 문제/사용자/가치
- **Goals & Non-goals**: 목표/비목표
- **Scope & UX flows**: 범위/주요 흐름
- **Constraints**: API Rate-limit/Security/Performance 제약
- **Dependencies**: 의존성 분석
- **Acceptance Criteria**: 테스트 가능한 수용 기준
- **Observability**: 로그/메트릭/리커버리 계획
- **Risks & Rollback**: 위험 요소/롤백 전략

**프로세스**: PRD 작성 → 최대 3개 명확화 질문 → 승인 대기

#### Step 2: Task 분해
PRD 승인 후 계층적 태스크 리스트 생성:
- **번호 체계**: 1, 1.1, 1.2, 2, 2.1...
- **각 태스크 포함사항**:
  - Description (무엇을/왜)
  - Acceptance Criteria (검증 기준)
  - Test Plan (테스트 단계/샘플)
  - Risk & Rollback (위험/되돌리기)
  - Effort (난이도/예상시간)
  - Touch Points (수정 파일/모듈 예상)
- **tasks/active/*.md 문서 생성/업데이트** ([ ]/[-]/[x] 마커 사용)

#### Step 3: 순차 실행 (한 번에 하나씩)
각 태스크별 루프:
1. **Plan**: 정확한 변경사항과 영향 범위 요약
2. **Implement**: 패치/diff 제안, 생성/수정 파일 리스트
3. **Self-test**: 테스트 실행 또는 설명, 결과/로그 표시
4. **Verify**: 결과를 Acceptance Criteria에 매핑, 잔여 위험 기록
5. **Ask**: "승인/수정/중단?" 대기
   - 승인 시: 태스크 완료 마킹 후 다음 태스크 제안
   - 수정 시: 요청사항만 적용, 새 diff/결과 표시
   - 차단/정보 부족 시: 정확한 질문 (최대 3개)

### 🛡️ 3-Step 프로세스 가드레일
- **한 번에 하나의 태스크만**: 절대 여러 태스크 동시 처리 금지
- **비밀 정보 보호**: API 키 등은 환경변수/플레이스홀더로 요청
- **아키텍처 준수**: DDD 계층, 3-DB 분리, Dry-Run 기본값 유지
- **기술적 제약 존중**: Rate-limit, Security, Performance 제약 준수

### 🔗 Ryan-Style과 기존 룰의 통합
- **모든 구현은 기존 Golden Rules와 Must Do/Must Not Do 준수**
- **Infrastructure 로깅**: create_component_logger 사용 필수
- **테스트**: 비즈니스 로직, 도메인 규칙, 데이터 변환에 pytest 적용
- **최종 검증**: `python run_desktop_ui.py`로 7규칙 전략 무결성 확인

### 📋 작업 시작 가이드
사용자가 요청하면 Copilot은 다음과 같이 판단하고 제안:

```
"이 요청을 분석해보니 [새 기능/아키텍처 변경/복잡한 통합] 작업입니다.
체계적인 접근을 위해 Ryan-Style 3-Step Vibe Coding 프로세스를 진행하시겠습니까?

Step 1: PRD 작성 → Step 2: 태스크 분해 → Step 3: 순차 실행

아니면 바로 구현하시겠습니까?"
```

**참고 파일**: `.github/vibe_coding_3-step.md`

### 기존 프로세스 (Ryan-Style 미적용 시)
1) **즉시 실행 우선**: 짧은 설명 후 바로 구현. 명확하지 않은 부분만 질문 (최대 3개)
2) **합리적 기본값**: 심볼 KRW-BTC, TF 1m/5m/15m, 수수료 0.05%, 슬리피지 1틱, 로컬 3-DB, dry-run
3) **상황별 적응형 출력** (전문가 판단으로 필요한 것만):
   - **복잡한 변경**: Plan → Planned Changes → Implementation → Verification
   - **간단한 수정**: 바로 구현 후 간단한 검증
   - **새 기능**: Tests 포함 (비즈니스 로직, 도메인 규칙, 데이터 변환)
   - **버그 수정/UI 개선**: 실제 동작 검증으로 충분
   - **아키텍처 변경**: 상세한 계획과 리스크 분석 필수

---

## 🧪 테스트·품질 게이트 (전문가 판단)
- **테스트 범위**: 비즈니스 로직, 도메인 규칙, 데이터 변환에만 pytest 적용
- **UI/버그 수정**: 실제 동작 검증 (`python run_desktop_ui.py`) 우선
- **품질 확인**: Build/Lint 오류 해결, 변경 영향 최소화
- **최종 검증**: 핵심 기능 무결성 확인 (7규칙 전략 동작)

---

## 🧰 표준 명령 (PowerShell 전용)
```powershell
# UI 통합 검증
python run_desktop_ui.py

# 테스트 실행
pytest -q

# DB 상태 확인
python tools/super_db_table_viewer.py settings
python tools/super_db_table_viewer.py strategies
python tools/super_db_table_viewer.py market_data

# 계층 위반 탐지 (PowerShell)
Get-ChildItem upbit_auto_trading/domain -Recurse -Include *.py | Select-String -Pattern "import sqlite3|import requests|from PyQt6"
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String -Pattern "print\("

# 로깅 환경변수
$env:UPBIT_CONSOLE_OUTPUT = "true"
$env:UPBIT_LOG_SCOPE = "verbose"
$env:UPBIT_COMPONENT_FOCUS = "ComponentName"

# PowerShell Here-String 방식 (권장)
$pythonScript = @"
import sqlite3
conn = sqlite3.connect('data/settings.sqlite3')
cursor = conn.cursor()
results = cursor.fetchall()
conn.close()
"@

python -c $pythonScript

---

## 🎯 정보 수집 & 검색 활용 방침
### 인터넷 검색 적극 활용
- 최신 API 문서, 기술 스펙, 라이브러리 정보 수집 시 적극 활용
- 업비트 공식 문서, GitHub 리포지토리, 기술 블로그 등 신뢰할 만한 소스 우선
- 검색 결과를 바탕으로 코드 구현 전 충분한 사전 조사 수행

### Context7 MCP 도구 활용
- Python 라이브러리, 프레임워크 관련 정보 수집 시 적극 활용
- 특히 PyQt6, matplotlib, pandas, numpy 등 핵심 라이브러리 문서 참조
- 최신 베스트 프랙티스와 권장 패턴 확인 후 적용

### 정보 검증 원칙
- 여러 소스에서 정보 교차 검증
- 공식 문서를 최우선으로 하되, 커뮤니티 사례도 참고
- 수집한 정보는 프로젝트 컨텍스트에 맞게 적절히 가공 후 적용

---

## 📋 태스크 관리 & 진행 마커 규칙
### 태스크 진행 마커 표준
- **[ ]**: 미완료 (미시작 상태)
- **[-]**: 진행 중 (현재 작업 중)
- **[x]**: 완료 (작업 완료)

### 태스크 문서 관리 원칙
- 모든 태스크 문서에서 위 마커 규칙을 일관성 있게 적용
- 진행 상황을 명확히 표시하여 프로젝트 추적 용이성 확보
- tasks/active/ 폴더의 모든 마크다운 파일에 적용

---

## 🧱 에러 처리 모범사례
```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
logger = create_component_logger("ComponentName")

def load_config(config: dict) -> None:
    if not config.get("entry_strategy"):
        logger.error("진입 전략 누락")
        raise ValidationError("진입 전략이 설정되지 않았습니다")
```

---

## ✅ 최종 체크리스트
- [ ] dry_run=True 기본, 실거래는 2단계 확인
- [ ] DDD 계층 규칙 위반 없음, Domain 순수성 유지
- [ ] UI 전역 스타일 시스템 준수, setStyleSheet 하드코딩 없음
- [ ] 3-DB 경로/스키마 사용, 외부 의존은 Infrastructure 격리
- [ ] Infrastructure 로깅 사용, print() 미사용
- [ ] 필요한 경우 테스트 포함, UI 런 통해 7규칙 검증
- [ ] 복잡한 시스템 테스트: `docs/COMPLEX_SYSTEM_TESTING_GUIDE.md` 참조

---

본 문서는 .github/new_copilot-instructions.md 및 .github/optimized_copilot-instructions.md의 내용을 통합한 Canonical 가이드입니다.
