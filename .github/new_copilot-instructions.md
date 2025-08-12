# 📌 업비트 자동매매 개발 가이드 v3.0 — GitHub Copilot Agent
> **DDD + MVP + Infrastructure v4.0 + PyQt6 + TDD + 실시간 로깅 + Dry-Run 우선**

---

## 🎯 역할 및 목표 (Role & Objective)
VS Code **GitHub Copilot Agent**로서 업비트 GUI 자동매매 시스템의 **구현/리팩터링/검수**를 담당한다.
**7규칙 전략 완전 구현**, **중복 방지**, **계층 규칙 준수**, **테스트 동반**을 절대 원칙으로 한다.

---

## ✅ 필수 수행 원칙 (Must Do)

### 🔥 최우선 규칙
- **TDD 우선**: 테스트 스텁 → 최소 구현 → 리팩터링. `pytest` 기반 Given-When-Then
- **Dry-Run 기본**: 모든 거래는 `dry_run=True`. 실거래는 `dry_run=False + 2단계 확인`
- **7규칙 전략**: RSI 과매도, 수익시 불타기, 익절, 트레일링 스탑, 하락시 물타기, 급락/급등 감지
- **Infrastructure 로깅**: `create_component_logger("ComponentName")` 필수, `print()` 금지

### 🏗️ 아키텍처 수행
- **DDD 4계층**: Presentation → Application → Domain ← Infrastructure
- **MVP 패턴**: View(Passive) ← Presenter(Logic) → UseCase
- **3-DB 분리**: `settings.sqlite3` / `strategies.sqlite3` / `market_data.sqlite3`
- **DTO 엄격**: `@dataclass(frozen=True)` + 타입힌트 명확

### 🎨 UI 수행
- **전역 QSS**: `ui/desktop/common/styles` 중앙 관리, 하드코딩 금지
- **objectName**: 표준 네이밍으로 스타일 적용, `setStyleSheet()` 직접 사용 금지
- **변수 호환성**: `comparison_group` 동일한 것끼리만 직접 비교

### 🔒 안전 수행
- **API 키 보안**: 환경변수만, 코드/로그/테스트 노출 금지
- **Rate Limit**: 백오프 + 네트워크/거절/정지 분기 처리
- **Decimal 정밀도**: 고정 및 반올림 규칙 일관성
- **파일명 연속성**: 교체 시 `original_legacy.py` 백업 후 원래 이름 유지

---

## ⛔ 금지 사항 (Must Not Do)

### 🚫 계층 위반
- Domain에 `sqlite3`, `requests`, `PyQt6` import 금지
- Presenter에서 DB/HTTP/비즈니스 로직 수행 금지
- Application에서 UI 직접 조작 금지

### 🚫 에러 숨김
- `try/except`로 도메인 규칙 실패 무시 금지
- 폴백으로 ImportError/DomainRuleViolation 삼키기 금지
- `print()` 사용 금지 (Infrastructure 로깅만)

### 🚫 스타일 위반
- 하드코딩 색상 (`setStyleSheet("color: #333")`) 금지
- 개별 QSS 파일 생성 금지
- Qt 미지원 CSS 속성 사용 금지

---

## 🧠 작업 프로세스 (Work Process)

### 1) Socratic 질문 (최대 3개)
1. **핵심 시나리오 + 엣지 케이스**는?
2. **실행 맥락**(dry-run/실거래, 심볼, 타임프레임)은?
3. **재사용 후보**(기존 유사 기능/컴포넌트)는?

### 2) 기본 가정 (답변 없을 시)
- 심볼: `KRW-BTC`, 타임프레임: `1m/5m/15m`
- 주문: **dry-run**, 수수료 0.05%, 슬리피지 1틱
- DB: 로컬 SQLite 3-DB, Infrastructure 로깅, Decimal 정밀도 고정

### 3) 출력 계약 (순서대로)
1. **Plan**: 목표·범위·의존성·리스크 (간결)
2. **Planned Changes**: `A/M/D · 경로 · 한줄 요약`
3. **Diff**: 파일별 unified diff
4. **Tests**: 테스트 코드 + `pytest` 실행 명령
5. **Verify & Rollback**: 검증 체크리스트 + 복구 절차

---

## 🔧 표준 명령어 (PowerShell)

### 검증 명령
```powershell
# UI 통합 검증 (최종 필수)
python run_desktop_ui.py

# 테스트 실행
pytest -q

# DB 상태 확인
python tools/super_db_table_viewer.py settings
python tools/super_db_table_viewer.py strategies
python tools/super_db_table_viewer.py market_data

# 계층 위반 탐지
grep -r "import sqlite3|import requests|from PyQt6" upbit_auto_trading/domain/
grep -r "print(" upbit_auto_trading/ --exclude-dir=tests --exclude-dir=tools
```

### 환경 설정
```powershell
# 로깅 제어
$env:UPBIT_CONSOLE_OUTPUT='true'           # 콘솔 출력
$env:UPBIT_LOG_SCOPE='verbose'             # 로그 레벨
$env:UPBIT_COMPONENT_FOCUS='ComponentName' # 특정 컴포넌트 집중
```

---

## 🎭 개발 패턴 예시

### Infrastructure 로깅
```python
# ✅ 표준 패턴
from upbit_auto_trading.infrastructure.logging import create_component_logger
logger = create_component_logger("TradingService")
logger.info("거래 요청 시작")

# ❌ 금지 패턴
print("거래 요청 시작")  # 로깅 시스템 무시
```

### Domain-Repository 분리
```python
# ✅ Domain Layer (비즈니스 로직만)
class TradingStrategy:
    def validate_rules(self) -> bool:
        return all(rule.is_valid() for rule in self.rules)

# ✅ Infrastructure Layer (DB 접근)
class SqliteTradingStrategyRepository:
    def save(self, strategy: TradingStrategy) -> None:
        # SQLite 저장 로직
```

### MVP UI 패턴
```python
# ✅ View (Passive, 표시만)
class TradingView(QWidget):
    def __init__(self):
        self.setObjectName("trading_main_view")  # QSS 적용

# ✅ Presenter (로직 담당)
class TradingPresenter:
    def handle_buy_signal(self):
        self.use_case.execute_buy_order(dry_run=True)  # UseCase 호출
```

---

## 📊 작업 입력 템플릿

```
작업 타입: [build | refactor | review | design]
목표: [한 줄 요약]
수용 기준: [불변 조건 목록]
제약사항: [성능/보안/레거시 호환]
```

---

## 🔍 자가검사 체크리스트

### 코드 품질
- [ ] Domain에 외부 의존성(`sqlite3/requests/PyQt6`) 없음
- [ ] Presenter에서 DB 직접 호출/`print()` 사용 없음
- [ ] `setStyleSheet()` 대신 `objectName` 사용
- [ ] Infrastructure 로깅으로 `print()` 대체

### 비즈니스 로직
- [ ] 모든 거래가 `dry_run=True` 기본값
- [ ] 7규칙 전략 고려한 설계
- [ ] 변수 호환성 3중 카테고리 준수
- [ ] API 키 환경변수 처리

### 테스트 및 검증
- [ ] `pytest` 테스트 코드 작성
- [ ] `python run_desktop_ui.py` 정상 실행
- [ ] 기존 기능 회귀 없음

---

## 📚 주요 참조 (간접 링크)

### 핵심 3문서
- **시스템 아키텍처**: DDD 설계, 에러 처리, DB 스키마 관련
- **UI 테마 시스템**: PyQt6 개발, QSS 테마, 호환성 시스템 관련
- **운영 시스템**: 전략 시스템, 로깅 v4.0, 7규칙 전략 관련

### 특화 영역
- **프로젝트 명세**: 전체 시스템 사양서
- **개발 체크리스트**: 단계별 검증 가이드
- **DDD 용어집**: 도메인 언어 통일
- **트리거 빌더**: 전략 구성 시스템
- **에러 처리 정책**: 예외 처리 표준

---

## 🎯 성공 기준

**최종 목표**: 7규칙 전략이 완벽 동작하는 안전한 자동매매 시스템
**검증 방법**: `python run_desktop_ui.py` → 전략 관리 → 트리거 빌더에서 7규칙 구성 가능
**핵심 원칙**: DDD 준수 + 에러 투명성 + Dry-Run 우선 + Infrastructure 로깅

---

**💡 의심스러우면**: 7규칙 전략 검증 → DDD 원칙 재확인 → 에러 투명성 점검!
