# upbit-autotrader-vscode 통합 개발 지침 (Copilot 자동 검토용)

이 문서는 GitHub Copilot이 새로운 세션을 시작할 때마다 반드시 검토하는 **통합 개발 지침**입니다.

## 📋 **[핵심 현황 요약 - 2025년 7월 20일 기준]**

### 🎯 **현재 버전**: v0.1.0-alpha
- **목표 릴리즈**: v0.1.0-stable (2025-08-15)
- **전체 진행률**: **62%** (28/45 태스크 완료)
- **핵심 태스크 문서**: `VERSION_0_1_MILESTONE_TASKS.md`

### ✅ **개발 완성도 현황**
- **Phase 1-3 완료**: 기반 구축 ~ UI 통합 (95% 완료)
- **Phase 4 진행중**: 실시간 거래 엔진 (80% 완료)
- **업비트 API 클라이언트**: **95% 완성** - 즉시 활용 가능
- **차트 뷰**: 가짜 데이터 사용 중 → **실제 데이터 연동 우선 필요**

### 🔥 **현재 최우선 과제** (1-3일 내 완료)
1. **TASK-001**: 차트 데이터 로더 통합 (90% 완료)
2. **TASK-002**: 웹소켓 실시간 업데이트 구현
3. **TASK-003**: 과거 데이터 무한 스크롤 구현

### 💡 **중요 발견사항**
- **중복 개발 방지**: 업비트 API 클라이언트 재개발 불필요
- **기존 코드 활용**: `get_historical_candles()` 메서드 완벽 지원
- **즉시 적용 가능**: 1-2일 내 실제 차트 데이터 연동 완성 가능

---

## [자동 검토 대상 문서 목록]
아래의 모든 문서는 Copilot이 세션 시작 시 자동으로 검토합니다. 각 문서의 위치와 역할을 참고하여, 최신 개발 현황과 규칙을 항상 반영합니다.

### 1. 핵심 개발 지침 및 워크플로우
- `.kiro/specs/upbit-auto-trading/requirements.md` : 기능 요구사항
- `.kiro/specs/upbit-auto-trading/design.md` : 시스템 설계, 구조, 데이터 흐름, UI/UX, 보안 등
- `.kiro/specs/upbit-auto-trading/tasks.md` : 태스크별 개발 계획 및 진행 현황 **[최신 업데이트됨]**
- `.kiro/steering/development_workflow.md` : 전체 개발 프로세스 및 워크플로우
- `.kiro/steering/unit_test_guidelines.md` : 단위 테스트 작성 및 관리 지침
- `.kiro/steering/testing_best_practices.md` : 테스트 및 디버깅 모범 사례
- `.kiro/steering/korean-language.md` : 한글 문서화 및 언어 규칙

### 2. 프로젝트 및 서비스 문서
- `README.md` (루트, 각 주요 폴더) : 프로젝트 개요, 설치 및 사용법, 주요 기능
- `CONTRIBUTING.md` : 외부 기여자 및 팀원 개발/기여 지침
- `GEMINI.md` : Gemini 관련 문서

### 3. 시스템/기능/보안/운영/참고 문서
- `reference/*.md` : 시스템 아키텍처, 데이터베이스, API, 배포/운영, 보안, UI/UX, 각종 기능별 상세 명세

### 4. 서비스별 상세 가이드 및 개선 내역
- `upbit_auto_trading/docs/*.md` : UI 가이드, 백테스팅, 실시간 거래, 시스템 모니터링, 알림, 코드 품질 개선, 개발 진행 상황, API 문서 등

### 5. 기타
- `sample_QA_Automation/README.md` : QA 자동화 샘플 및 테스트 가이드

각 문서의 최신 내용과 변경 내역을 반드시 확인하고, 개발/테스트/배포/운영 시 일관성 있게 적용합니다.

---

## 📊 **[기존 코드 활용 가이드]**

### ✅ **완성된 업비트 API 클라이언트 활용법**

**파일 위치**: `upbit_auto_trading/data_layer/collectors/upbit_api.py`

**주요 완성 기능**:
```python
# 1. 과거 데이터 수집 (이미 완성됨!)
api.get_historical_candles(symbol, timeframe, start_date, end_date)

# 2. 실시간 데이터 조회
api.get_candles(symbol, timeframe, count)

# 3. API 제한 준수 (자동 처리)
# - 초당 10회, 분당 600회 제한 준수
# - 재시도 로직, 오류 처리 완성

# 4. 모든 시간대 지원
# - 1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M
```

### 🎯 **차트 뷰 즉시 개선 방법**

**참고 파일**: `upbit_auto_trading/ui/desktop/screens/chart_view/dynamic_chart_data_guide.py`

**구현 단계**:
1. **기존 코드 수정** (30분)
   ```python
   # chart_view_screen.py 수정
   # 기존: self.chart_data = self.generate_sample_data()
   # 변경: self.load_real_chart_data(symbol)
   ```

2. **동적 데이터 매니저 추가** (1시간)
   ```python
   # DynamicChartDataManager 클래스 통합
   # 백그라운드 스레드로 API 호출
   # 실시간 업데이트 (1분마다)
   ```

3. **테스트 및 최적화** (4시간)

---

## 🔧 **[UI 개선 현황 및 해결된 문제들]**

### ✅ **해결된 UI 문제들** (2025/01/19)

**1. 테마 전환 시 글자색 가시성 문제**
- **문제**: 화이트 모드에서 좌측 탭 글자가 흰색으로 보이지 않음
- **해결책**: `main_window.py`의 CSS 스타일링 수정
- **구현 위치**: `apply_theme()` 메서드 내 다크/라이트 모드별 스타일 분리

**2. 차트 뷰 초기 렌더링 문제**
- **문제**: 프로그램 시작 시 차트가 찌그러진 상태로 출력
- **해결책**: `chart_view_screen.py`에 `showEvent()`, `resizeEvent()` 핸들러 추가
- **구현**: 창 크기 변경 시 차트 자동 재조정

**3. 윈도우 크기 초기화**
- **문제**: 이전 세션의 창 크기가 제대로 복원되지 않음
- **해결책**: `main_window.py`에서 기본 창 크기 설정 및 상태 복원 로직 개선

---

## 📊 **[코드베이스 분석 결과 - 중복 개발 방지]**

### ✅ **기존 완성된 핵심 모듈들**

**1. 업비트 API 클라이언트** (`upbit_auto_trading/data_layer/collectors/upbit_api.py`)
- **완성도**: 95% - 즉시 실전 활용 가능
- **주요 기능**: 
  - `get_historical_candles()` - 과거 데이터 수집 완료
  - `get_candles()` - 실시간 데이터 조회 완료
  - 레이트 제한 준수 (초당 10회, 분당 600회)
  - 자동 재시도 및 오류 처리
- **지원 시간대**: 1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M
- **⚠️ 중요**: 새로운 API 클라이언트 개발 절대 금지!

**2. 차트 뷰 시스템** (`upbit_auto_trading/ui/desktop/screens/chart_view/`)
- **현재 상태**: 샘플 데이터 사용 중
- **즉시 개선 가능**: 기존 API 클라이언트와 연동
- **구현 가이드**: `dynamic_chart_data_guide.py` 참조

**3. 데이터베이스 레이어** (`upbit_auto_trading/data_layer/`)
- **완성도**: 90% 완료
- **기능**: SQLite 기반 트레이딩 데이터 저장/조회

---

## 1. 개발 워크플로우 및 핵심 원칙

### 🚫 **중복 개발 방지 체크리스트**
새로운 기능 개발 전 반드시 확인:
1. **기존 코드 조사**: `grep_search`로 유사 기능 검색
2. **API 확인**: `upbit_api.py`에서 필요한 메서드 존재 여부 확인
3. **문서 검토**: 관련 가이드 문서 존재 여부 확인
4. **테스트 코드 분석**: 기존 구현 로직 파악

### 📋 **개발 워크플로우**
- **TDD 원칙**: 기능 개발 전 테스트 케이스 작성
- **태스크 기반**: tasks.md의 번호와 일치하는 테스트 파일명 사용
- **기존 코드 우선**: 95% 완성된 모듈 최대한 활용
- **단계별 진행**: 기능 개발 → 테스트 → 리뷰 → 병합

## 2. 테스트 및 디버깅
- 테스트 파일은 `test_`로 시작, 태스크와 기능명 snake_case로 작성
- 개별 테스트 실행 및 전체 테스트 순차 실행(`run_tests_in_order.py` 활용)
- 테스트 실패 시 즉시 디버깅 및 수정, 원인 분석 후 문서화
- 테스트 커버리지 목표: 비즈니스 로직 80% 이상, 데이터/유틸리티 70% 이상
- Mock 객체 활용, 외부 API/DB 등은 테스트 환경 분리

## 3. 코드 품질 및 문서화
- **중복 코드 제거**: 기존 완성된 모듈 최대한 재사용
- **성능 최적화**: 불필요한 API 호출 방지
- **명확한 네이밍**: 변수/함수명으로 기능 명확히 표현
- **문서 연동**: `.kiro/specs` 및 `docs/` 폴더와 일관성 유지
- **버전 관리**: Git으로 변경 내역 추적
- **언어 일관성**: 한글/영문 혼용 시 규칙 준수

---
**🎯 중요 지침: 본 프로젝트의 사용자는 비개발자 출신의 코딩 초보입니다. 모든 설명, 예시, 가이드, 코드 주석은 반드시 초보자가 이해할 수 있도록 쉽고 상세하게 작성해야 합니다. 어려운 용어는 풀어서 설명하고, 단계별로 따라할 수 있도록 안내합니다.**
---

## 4. 보안 및 신뢰성

### 🔐 **API 키 관리**
- **환경 변수**: `.env` 파일에 UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY 저장
- **암호화**: 중요 정보는 cryptography 패키지로 암호화
- **접근 제한**: API 키는 필요한 모듈에서만 접근

### 🛡️ **에러 처리 및 안정성**
- **자동 재시도**: 네트워크 오류 시 3회까지 재시도
- **레이트 제한**: 업비트 API 제한 준수 (초당 10회, 분당 600회)
- **예외 처리**: 모든 API 호출에 try-catch 적용
- **로깅**: 모든 오류는 `logs/` 폴더에 기록

## 5. 패키지 관리 및 환경설정

### 📦 **[필수 종속성 목록]**
```python
# 핵심 데이터 처리
pandas
numpy

# API 통신
requests
python-dotenv

# 보안 및 인증
cryptography
pyjwt  # ⚠️ 필수! JWT 토큰 처리용

# 설정 관리
pyyaml

# GUI (PyQt6)
PyQt6
pyqtgraph
```

### ⚠️ **중요 주의사항**
- **JWT 패키지**: 반드시 `pyjwt` 설치 필요 (jwt 아님!)
- **ImportError 대응**: 패키지 누락 시 즉시 `pip install` 안내
- **requirements.txt 동기화**: 새로운 패키지 설치 시 반드시 추가

### 🔧 **환경설정 체크리스트**
1. **Python 3.8+** 버전 확인
2. **가상환경** 생성 및 활성화 권장
3. **환경 변수 파일** `.env` 생성
4. **API 키 설정** 업비트에서 발급받은 키 입력
5. **의존성 설치** `pip install -r requirements.txt`

## 6. 테스트 코드 작성 지침

### 📋 **테스트 코드 스타일**
- **독립 함수**: 모든 단위 테스트는 독립 함수로 작성
- **직접 실행 구조**: `if __name__ == "__main__"` 패턴 사용
- **명확한 출력**: 테스트 ID와 결과 상태 표시
  ```python
  def test_api_connection():
      print("[테스트 1/3] API 연결 테스트 시작...")
      try:
          # 테스트 로직
          print("[성공] API 연결 정상")
          return True
      except Exception as e:
          print(f"[실패] API 연결 오류: {e}")
          return False
  ```

### 🎯 **테스트 작성 원칙**
- **환경 변수 확인**: 테스트 시작 전 필수 설정 점검
- **사용자 친화적 메시지**: 오류 발생 시 해결 방법 안내
- **로그 중심**: 실제 동작 결과를 사용자가 확인 가능하도록
- **종료 코드**: 성공/실패에 따른 적절한 exit code 반환

---

## 📚 **[개발 참고 자료]**

### 🔗 **주요 문서 링크**
- **API 가이드**: `upbit_auto_trading/docs/api_documentation.md`
- **UI 개발**: `upbit_auto_trading/docs/ui_development_guide.md`
- **백테스팅**: `upbit_auto_trading/docs/backtesting_guide.md`
- **실시간 거래**: `upbit_auto_trading/docs/live_trading_guide.md`

### 🛠️ **유용한 도구 및 명령어**
```bash
# 전체 테스트 실행
python run_tests_in_order.py

# 개별 테스트 실행
python -m pytest tests/test_specific_module.py

# GUI 애플리케이션 실행
python run_desktop_ui.py

# 코드 품질 검사
python -m flake8 upbit_auto_trading/
```

---

이 문서는 GitHub Copilot이 세션 시작 시 자동으로 검토합니다. 추가/수정 요청 시 언제든 말씀해 주세요.

---

## 📊 **[핵심 아키텍처 및 UI 구조 가이드]**

### 🎯 **메인 대시보드 아키텍처** (`ui_spec_01_main_dashboard.md` 기반)

**핵심 위젯 구성**:
1. **총 자산 위젯** (`widget-total-assets`)
   - **연동**: `UpbitAPI.get_account()` + `PortfolioPerformance.calculate_portfolio_performance()`
   - **위치**: `upbit_auto_trading/data_layer/collectors/upbit_api.py`
   - **상태**: 95% 완성 - 즉시 활용 가능

2. **포트폴리오 요약 위젯** (`widget-portfolio-summary`)
   - **연동**: `PortfolioManager.get_all_portfolios()`
   - **위치**: `business_logic/portfolio/portfolio_manager.py`
   - **기능**: 도넛 차트 + 비중 표시

3. **실시간 거래 현황 위젯** (`widget-active-positions`)
   - **연동**: `TradingEngine.get_active_positions()` (구현 예정)
   - **위치**: `business_logic/trader/` (80% 완료)
   - **요구사항**: 1초 이내 지연시간으로 갱신

4. **최근 알림/로그 위젯** (`widget-notifications`)
   - **연동**: `Notification` 모델 + SQLAlchemy 쿼리
   - **쿼리 예**: `session.query(Notification).order_by(Notification.timestamp.desc()).limit(10).all()`
   - **위치**: `data_layer/models.py`

### 🔗 **UI-백엔드 연동 매핑**

| UI 컴포넌트 | 백엔드 클래스/메서드 | 파일 위치 | 완성도 |
|------------|-------------------|----------|--------|
| 차트 뷰 | `get_historical_candles()` | `data_layer/collectors/upbit_api.py` | ✅ 95% |
| 자산 위젯 | `UpbitAPI.get_account()` | `data_layer/collectors/upbit_api.py` | ✅ 95% |
| 포트폴리오 | `PortfolioManager` | `business_logic/portfolio/` | ✅ 90% |
| 거래 현황 | `TradingEngine` | `business_logic/trader/` | 🟡 80% |
| 알림 시스템 | `Notification` 모델 | `data_layer/models.py` | ✅ 90% |

### ⚡ **성능 요구사항**
- **실시간 업데이트**: 1초 이내 지연시간
- **데이터 수집**: `DataCollector` 를 통한 주기적 수집
- **API 제한 준수**: 초당 10회, 분당 600회 (자동 처리됨)

---

## 🚀 **[즉시 구현 가능한 개선 작업들]**

### 1️⃣ **차트 뷰 최적화된 동적 데이터 로딩** (최우선, 1-2일 소요)

**🎯 핵심 개선 전략** (사용자 제안 반영):

**업비트 API 제한사항**:
- 한 번에 최대 **200개 캔들**만 조회 가능
- **초당 10회, 분당 600회** 요청 제한 (매우 넉넉함)

**최적화 방법**:
1. **점진적 로딩 (Lazy Loading)**: 필요할 때 필요한 만큼만
2. **실시간 업데이트**: 웹소켓으로 API 요청 최소화  
3. **과거 데이터 확장**: 스크롤 시 동적 추가

**구현 단계**:
```python
# 1단계: 초기 데이터 로딩 (여러 번 API 호출)
def fetch_initial_candles(market, interval, total_count=600):
    all_candles = []
    request_count = (total_count + 199) // 200  # 필요한 요청 횟수
    
    for _ in range(request_count):
        candles = upbit_api.get_candles(market, interval, count=200, to=last_time)
        all_candles = candles + all_candles  # 과거→현재 순서
        last_time = candles[0]['candle_date_time_utc']
    
    return all_candles

# 2단계: 실시간 업데이트 (웹소켓)
def setup_websocket_realtime():
    # 체결(trade) 데이터로 현재 캔들 OHLCV 직접 계산
    # 1분 지나면 완성된 캔들을 차트에 추가
    # API 요청 수 전혀 사용 안함!
```

**예상 성능**:
- **초기 로딩**: 600개 캔들, 3회 API 호출, 1-2초 완료
- **실시간 업데이트**: 웹소켓, API 요청 0회
- **과거 확장**: 스크롤 시 200개씩 추가, 0.1초

**파일 위치**: `dynamic_chart_data_guide.py` (이미 업데이트됨)

### 2️⃣ **UI 테마 및 렌더링 문제 해결** (완료됨)

**해결된 문제들**:
- ✅ 화이트 모드 탭 글자 가시성 문제
- ✅ 차트 초기 렌더링 찌그러짐 문제
- ✅ 윈도우 크기 초기화 문제

### 3️⃣ **실시간 거래 엔진 완성** (진행 중, 80% 완료)

**위치**: `business_logic/trader/`
**필요 작업**: `TradingEngine.get_active_positions()` 메서드 구현
**연동**: `widget-active-positions` 위젯과 직접 연결

---

## 🎯 **[개발 우선순위 및 로드맵]**

### 📋 **Phase 4 완료 목표** (현재 80% 완료)
1. **차트 뷰 실데이터 연동** ← **최우선 작업**
2. 실시간 거래 엔진 `get_active_positions()` 구현
3. 웹소켓 실시간 스트리밍 완성
4. 알림 시스템 UI 연동 완성

### 📈 **장기 개선 계획**
1. Plotly 기반 고급 차트 도입
2. 모바일 반응형 UI 개선
3. 성능 최적화 및 캐싱 시스템
4. 고급 백테스팅 기능 확장

---

## 🛠️ **[실용적 개발 가이드]**

### 🔍 **코드 탐색 명령어**
```bash
# API 관련 코드 검색
grep -r "get_historical_candles" upbit_auto_trading/

# UI 위젯 관련 코드 검색  
grep -r "widget-" reference/

# 차트 뷰 관련 파일 찾기
find . -name "*chart*" -type f
```

### 🧪 **테스트 실행 방법**
```bash
# 전체 테스트 순차 실행
python run_tests_in_order.py

# API 연결 테스트
python test_api_key.py

# 차트 뷰 테스트
python test_chart_view.py
```

### 🖥️ **GUI 실행 및 디버깅**
```bash
# 데스크톱 UI 실행
python run_desktop_ui.py

# 에러 로그 확인
type logs\gui_error.log
```

---

## 💡 **[Copilot 세션별 체크리스트]**

### ✅ **새 세션 시작 시 반드시 확인**
1. `tasks.md` 최신 진행 상황 검토
2. `upbit_api.py` 완성도 확인 (중복 개발 방지)
3. `dynamic_chart_data_guide.py` 구현 가이드 참조
4. UI 명세서 (`ui_spec_01_main_dashboard.md`) 확인
5. 사용자 요청이 기존 완성 기능과 중복되는지 검증

### 🚫 **절대 금지 사항**
- 업비트 API 클라이언트 재개발
- 기존 95% 완성된 모듈 무시하고 새로 개발
- UI 명세서 무시하고 임의 구조 생성
- 테스트 없이 기능 구현

### 🎯 **권장 개발 접근법**
1. **기존 코드 최대 활용**: 완성된 모듈 우선 사용
2. **단계별 구현**: 작은 단위로 테스트하며 진행
3. **문서 연동**: UI 명세서와 일치하는 구현
4. **사용자 친화적**: 비개발자도 이해할 수 있는 설명

---

이 통합 개발 가이드는 모든 파편화된 정보를 하나로 모은 Copilot 친화적 문서입니다. 새로운 세션에서 이 문서만 참조하면 전체 프로젝트 상황을 즉시 파악할 수 있습니다.

## [핵심 아키텍처 및 기능 요약]
업비트 자동매매 시스템은 데이터 계층(수집/저장/관리), 비즈니스 로직 계층(스크리닝/전략/백테스팅/거래/포트폴리오), 사용자 인터페이스 계층(GUI/차트/대시보드)으로 구성됩니다.
각 계층별 주요 컴포넌트와 인터페이스는 `.kiro/specs/upbit-auto-trading/design.md`에 상세 명세되어 있습니다.

### 데이터 계층
- 시장 데이터 수집(OHLCV, 호가, 시세), 정제/가공/지표 계산, 데이터 저장/정리/관리
- 데이터 모델: OHLCV, OrderBook, Trade, Strategy, Backtest, Portfolio 등

### 비즈니스 로직 계층
- 종목 스크리닝(거래량/변동성/추세), 전략 생성/수정/저장/관리, 백테스팅, 실시간 거래, 포트폴리오 관리
- 각 기능별 인터페이스 및 반환값 구조 명확화

### 사용자 인터페이스 계층
- 대시보드, 차트 뷰, 설정 화면, 알림 센터 등
- 직관적 UI, 다크/라이트 모드, 1280x720 이상 해상도 지원, 마지막 UI 상태 복원

### 사용자 인터페이스 계층
1. 컴포넌트 분리 및 명세 기반 설계
- 대시보드, 차트 뷰, 종목 스크리너, 전략 관리, 백테스팅, 실시간 거래, 포트폴리오, 모니터링/알림 등 각 화면을 독립 컴포넌트로 분리
- 각 UI 요소는 고유 ID, 기능 설명, 연동 클래스/메서드, 관련 코드 경로를 명세서에서 확인

2. 데이터 흐름 및 백엔드 연동
- 사용자 입력(코인 선택, 전략 설정 등)은 이벤트로 처리
- 데이터 요청/갱신은 백엔드 API(UpbitAPI, DataCollector, StrategyManager 등)와 직접 연동
- 실시간 데이터(가격, 거래내역 등)는 주기적 폴링 또는 웹소켓으로 갱신

3. UX 및 반응성
- 모든 UI는 0.5초 이내 반응, 실시간 데이터는 1초 이내 갱신(성능 요구사항 반영)
- 주요 액션(저장, 실행, 중지 등)은 즉각적 피드백(로딩 스피너, 토스트 메시지 등) 제공
- UI 상태(설정, 마지막 화면 등)는 저장/복원 기능 포함

4. 테스트 및 유지보수
- 각 컴포넌트별 단위/통합 테스트 작성
- UI/비즈니스/데이터 계층 분리로 유지보수 용이
- 명세서와 실제 코드(클래스/메서드/경로) 일치 여부 지속 검증

5. 개발 워크플로우
- 화면 명세서 기반 UI 설계 → 컴포넌트/이벤트/데이터 연동 구현 → 테스트/디버깅 → 문서화
- 주요 변경 시 명세서와 코드 동시 업데이트, PR 리뷰 필수

### 성능/보안/신뢰성/데이터 정책
- 백테스팅 1년치 데이터 5분 이내 처리, 실시간 거래 1초 이내 데이터 갱신, UI 0.5초 이내 반응
- API 키 AES-256 암호화, HTTPS/SSL 통신, 민감정보 로그 저장 금지, API 키 권한 분리
- 99% 이상 가동 시간, 예기치 않은 종료 시 데이터 손실 방지, 네트워크 장애 자동 복구, 거래 원자성 보장
- 분봉 데이터 90일 원본 저장, 이후 요약/삭제, DB 10GB 초과 시 자동 정리

### 오류 처리 및 테스트 전략
- API/데이터/거래/시스템 오류별 재시도·예외·알림·자동 복구
- 단위/통합/백테스팅/UI 테스트, mock 객체 활용, 경계/예외/성능/사용성/반응성 테스트

### 기술 스택
- Python 3.8+, SQLite/PostgreSQL, requests/aiohttp, 병렬/비동기 처리 지원

상세 내용 및 인터페이스/데이터 모델/테스트 전략은 `.kiro/specs/upbit-auto-trading/design.md`와 `requirements.md`, `tasks.md`를 참고하여 구현 및 테스트 시 반드시 반영합니다.
