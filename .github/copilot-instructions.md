# 📌 업비트 자동매매 시스템 GitHub Copilot Agent 지침 — Master v3.1
> DDD + MVP + Infrastructure v4.0 + PyQt6 + TDD + 실시간 로깅 + Dry-Run 우선 (Windows PowerShell 전용)

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

## 🔁 작업 프로세스 (전문가 가이드라인)
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

# API 키 설정 (예시)
$env:UPBIT_ACCESS_KEY = "your_access_key"
$env:UPBIT_SECRET_KEY = "your_secret_key"

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

---

본 문서는 .github/new_copilot-instructions.md 및 .github/optimized_copilot-instructions.md의 내용을 통합한 Canonical 가이드입니다.
