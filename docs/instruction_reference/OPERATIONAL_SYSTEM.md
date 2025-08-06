# 🚀 운영 시스템 및 전략 실행 통합 가이드

> **목적**: 매매 전략 시스템, 로깅 인프라, 기본 7규칙 전략 운영 통합 안내
> **범위**: 전략 시스템, 로깅 시스템, 기여 가이드, LLM 최적화
> **갱신**: 2025-08-06

---

## 📈 매매 전략 시스템 (STRATEGY_SYSTEM)

### 전략 시스템 개요
- **구조**: 1개 진입 전략(필수) + 0~N개 관리 전략(선택)
- **최대 관리 전략**: 5개까지 조합 허용
- **충돌 해결**: priority/conservative/merge 방식 지원
- **검증 기준**: 기본 7규칙 전략으로 모든 전략 시스템 검증
- **아키텍처**: DDD 기반 Domain 엔티티로 구현

### Domain Entity 기반 진입 전략 (6종)

#### 1. 이동평균 교차 전략
```python
class MovingAverageCrossoverStrategy(EntryStrategy):
    """골든크로스/데드크로스 기반 진입"""
    def __init__(self, strategy_id: StrategyId, short_period=20, long_period=50, ma_type='SMA'):
        self.short_period = short_period  # 5~20
        self.long_period = long_period    # 20~60
        self.ma_type = ma_type           # SMA/EMA

    def generate_signal(self, market_data: MarketData) -> TradingSignal:
        # 골든 크로스: 단기선이 장기선 상향 돌파 → 'BUY'
        # 데드 크로스: 단기선이 장기선 하향 돌파 → 'SELL'
        # 기타: 'HOLD'
```

#### 2. RSI 과매수/과매도 전략
```python
class RSIEntryStrategy(EntryStrategy):
    """RSI 기반 진입 전략"""
    def __init__(self, period=14, oversold=30, overbought=70):
        # 과매도 구간에서 상승 반전 → 'BUY'
        # 과매수 구간에서 하락 반전 → 'SELL'
```

#### 3. 볼린저 밴드 전략
- **reversal 모드**: 하단 터치 후 반등 → BUY, 상단 터치 후 하락 → SELL
- **breakout 모드**: 상단 돌파 → BUY, 하단 이탈 → SELL

#### 4. 변동성 돌파 전략 (래리 윌리엄스)
- **돌파 기준**: 당일 시초가 + (전일 고가-저가 범위 × 돌파 비율)
- **신호 생성**: 돌파 기준가 도달 시 매수/매도 신호

#### 5. MACD 전략
- **신호**: MACD가 신호선 상향/하향 돌파 시점
- **파라미터**: fast=12, slow=26, signal=9

#### 6. 스토캐스틱 전략
- **조건**: 과매도/과매수 구간에서 %K가 %D 교차 시점
- **파라미터**: k_period=14, d_period=3, oversold=20, overbought=80

### 관리 전략 (6종)

#### 1. 물타기 전략 (Pyramid Buying)
```python
class PyramidBuyingStrategy(ManagementStrategy):
    """하락 시 추가 매수로 평단가 낮추기"""
    def __init__(self, trigger_drop_rate=0.05, max_additions=5, absolute_stop_loss=0.15):
        # 5% 하락마다 추가 매수, 최대 5회, 15% 손절선

    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> str:
        # 절대 손절선 체크 → 'CLOSE_POSITION'
        # 추가 매수 조건 → 'ADD_BUY'
```

#### 2. 불타기 전략 (Scale-in Buying)
- **목적**: 상승 시 추가 매수로 수익 극대화
- **조건**: 3% 수익마다 추가 매수, 최대 3회, 20% 목표 수익률

#### 3. 트레일링 스탑 전략
- **활성화**: 2% 수익 달성 시
- **후행**: 최고가에서 5% 하락 시 청산

#### 4. 고정 손절/익절 전략
- **손절**: 고정 비율 하락 시 청산
- **익절**: 목표 수익률 달성 시 청산

#### 5. 부분 익절 전략
- **단계별**: 5%, 10%, 20% 수익률별 부분 매도
- **비율**: 30%, 30%, 40% 분할 매도

#### 6. 시간 기반 청산 전략
- **최대 보유**: 기본 168시간 (1주일)
- **강제 청산**: 시간 초과 시 무조건 청산

### 전략 조합 규칙
```python
# 기본 조합 (진입 + 1개 관리)
basic_combination = {
    "entry_strategy": RSIEntryStrategy(period=14),
    "management_strategies": [TrailingStopStrategy(trail_distance=0.05)]
}

# 복합 리스크 관리
complex_combination = {
    "entry_strategy": MovingAverageCrossoverStrategy(),
    "management_strategies": [
        PyramidBuyingStrategy(max_additions=3, priority=3),
        FixedStopLossStrategy(stop_loss_rate=0.10, priority=2),
        PartialTakeProfitStrategy(priority=1)
    ],
    "conflict_resolution": "priority"
}
```

### 충돌 해결 방식
1. **priority**: 우선순위 높은 신호 채택
2. **conservative**: 보수적 신호 채택 (HOLD > CLOSE > ADD)
3. **merge**: 신호들을 병합하여 처리

---

## 🎯 기본 7규칙 전략 검증 기준 (BASIC_7_RULE_STRATEGY_GUIDE)

### 전략 개요
| 번호 | 규칙 이름 (역할) | 간단한 설명 |
|:-----|:----------------|:------------|
| 1 | **RSI 과매도 진입** (ENTRY) | RSI 지표가 20 이하로 떨어지면 최초 진입 |
| 2 | **수익 시 불타기** (SCALE_IN) | 수익률 5% 도달 시마다 3회까지 추가 매수 |
| 3 | **계획된 익절** (EXIT) | 불타기 3회 완료 후, 다음 수익 신호에 전량 매도 |
| 4 | **트레일링 스탑** (EXIT) | 5% 수익 후, 고점 대비 3% 하락 시 전량 매도 |
| 5 | **하락 시 물타기** (SCALE_IN) | 평단가 대비 -5% 하락 시, 2회까지 추가 매수 |
| 6 | **급락 감지** (EXIT/RISK_MGMT) | 1분 내 -5% 폭락 시, 모든 규칙 무시하고 즉시 청산 |
| 7 | **급등 감지** (MANAGEMENT) | 1분 내 +5% 급등 시, 불타기 중단하여 트레일링 스탑으로 더 높은 수익 추구 |

### Step-by-Step 실습 가이드

#### Phase 1: 전략 빌더 시작
```bash
cd ui_prototypes
python atomic_strategy_builder_ui.py
```
- **화면 구성**: 왼쪽 컴포넌트 팔레트 (📊변수, 🎯조건, ⚡액션 탭)
- **전략 캔버스**: 오른쪽 선택된 컴포넌트들, 규칙 카드 영역

#### Phase 2: 규칙 1 - RSI 과매도 진입 (ENTRY)
1. **RSI 지표 설정**: 📊 변수 탭 → "📈 RSI 지표" 클릭 → period: 14
2. **과매도 조건 생성**: 🎯 조건 탭 → "🔧 새 조건 만들기" → RSI < 20
3. **매수 액션 선택**: ⚡ 액션 탭 → "💰 전량 매수" 클릭
4. **진입 규칙 생성**: "🔧 규칙 만들기" → 규칙 역할: "ENTRY"

#### Phase 3-8: 나머지 6개 규칙
- **수익 시 불타기**: 현재 수익률 >= 5% → SCALE_IN
- **계획된 익절**: 5% 수익 달성 → EXIT
- **트레일링 스탑**: 5% 수익 후 3% 하락 → EXIT
- **하락 시 물타기**: -5% 손실 → SCALE_IN
- **급락 감지**: -5% 급락 → EXIT (비상 청산)
- **급등 감지**: +5% 급등 → EXIT (불타기 방지)

#### Phase 9: 전략 검증 및 저장
1. **전략 검증**: "✅ 전략 검증" 클릭 → 진입/청산 규칙 확인
2. **전략 저장**: "💾 전략 저장" → 이름: "기본 7규칙 전략 예제"

### 검증 포인트
- [ ] 7개 규칙이 모두 생성되었는가?
- [ ] 진입 규칙 1개가 있는가?
- [ ] 청산 규칙이 4개 이상 있는가?
- [ ] 각 규칙 카드의 색상이 역할에 맞게 표시되는가?
- [ ] 전략 검증이 통과되는가?
- [ ] 전략이 성공적으로 저장되는가?

---

## 🔍 Infrastructure 스마트 로깅 시스템 v4.0 (INFRASTRUCTURE_SMART_LOGGING_GUIDE)

### v4.0 핵심 혁신
- **자동 LLM 브리핑**: 마크다운 형태의 실시간 시스템 상태 보고서 자동 생성
- **JSON 대시보드**: 구조화된 모니터링 데이터로 실시간 차트/API 연동 지원
- **자동 문제 감지**: DI, UI, DB, Memory 등 8가지 패턴 기반 이슈 자동 분류
- **성능 최적화**: 비동기 처리(1000+ 로그/초), 메모리 자동 최적화, 지능형 캐싱(90%+ 히트율)

### v4.0 시스템 아키텍처
```
upbit_auto_trading/infrastructure/logging/
├── __init__.py                    # 통합 진입점
├── configuration/
│   └── enhanced_config.py         # v4.0 통합 설정 관리
├── briefing/
│   ├── system_status_tracker.py   # 실시간 컴포넌트 상태 추적
│   ├── issue_analyzer.py          # 패턴 기반 문제 감지
│   └── llm_briefing_service.py    # 마크다운 브리핑 생성
├── dashboard/
│   ├── issue_detector.py          # 로그 기반 자동 문제 감지
│   ├── realtime_dashboard.py      # JSON 대시보드 데이터 생성
│   └── dashboard_service.py       # 대시보드 파일 관리
└── performance/
    ├── async_processor.py         # 비동기 로그 처리 (1000+ 로그/초)
    ├── memory_optimizer.py        # 메모리 사용량 최적화
    ├── cache_manager.py           # 지능형 캐싱 시스템 (90%+ 히트율)
    └── performance_monitor.py     # 성능 메트릭 수집
```

### v4.0 기본 사용법
```python
# 새로운 v4.0 로깅 서비스 사용 (권장)
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

### v4.0 환경변수 제어
```powershell
# v4.0 Enhanced 기능 제어
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

### v4.0 출력 파일 시스템
- **LLM 브리핑**: `logs/llm_briefing_YYYYMMDD_HHMMSS.md` (마크다운 보고서)
- **JSON 대시보드**: `logs/dashboard_data.json` (실시간 구조화 데이터)
- **메인 로그**: `logs/upbit_auto_trading.log` (통합 로그)
- **세션 로그**: `logs/upbit_auto_trading_YYYYMMDD_HHMMSS_PID{숫자}.log` (세션별)

### 자동 LLM 브리핑 시스템
```python
# v4.0에서 자동으로 생성되는 마크다운 브리핑
logging_service = get_enhanced_logging_service()
logger = logging_service.get_logger("SystemMonitor")

logger.info("시스템 상태 체크 완료")  # 자동으로 브리핑 파일 업데이트
logger.error("DB 연결 실패")        # 자동 문제 감지 및 해결방안 제안
```

### 구조화된 에러 보고
```python
def report_error_to_llm(error_context):
    """LLM 에이전트에게 구조화된 에러 보고"""
    logger = get_enhanced_logging_service().get_logger("LLMReporter")

    logger.error("🤖 === LLM 에이전트 에러 보고 시작 ===")
    logger.error(f"📍 Component: {error_context.component}")
    logger.error(f"⚠️ Error Type: {error_context.error_type}")
    logger.error(f"📄 Error Message: {error_context.message}")
    logger.error(f"📊 Context Data: {error_context.context}")
    logger.error(f"🔍 Stack Trace: {error_context.stack_trace}")
    logger.error("🤖 === LLM 에이전트 에러 보고 완료 ===")
```

---

## 🤝 기여 가이드 (CONTRIBUTING)

### 빠른 시작
```powershell
# 1. 저장소 포크 후 클론
git clone <your-forked-repository-url>
cd upbit-autotrader-vscode

# 2. 가상환경 설정 (Windows)
python -m venv venv
venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 핵심 검증: 기본 7규칙 전략이 완전히 작동해야 함
python run_desktop_ui.py
```

### 브랜치 전략
- **master**: 안정적인 릴리스 버전
- **feature/***: 새로운 기능 개발
- **bugfix/***: 버그 수정

### 커밋 컨벤션
```
<type>: <subject>

<body>

<footer>
```

#### Type 분류
- **feat**: 새로운 기능 추가
- **fix**: 버그 수정
- **docs**: 문서 변경
- **refactor**: 코드 리팩토링
- **test**: 테스트 코드 추가/수정
- **chore**: 빌드/설정 변경

### 개발 원칙

#### 필수 검증 기준
**모든 변경사항은 기본 7규칙 전략 수행 가능해야 함**
1. RSI 과매도 진입 (ENTRY)
2. 수익 시 불타기 (SCALE_IN)
3. 계획된 익절 (EXIT)
4. 트레일링 스탑 (EXIT)
5. 하락 시 물타기 (SCALE_IN)
6. 급락 감지 (RISK_MGMT)
7. 급등 감지 (MANAGEMENT)

#### 코딩 표준
- **PEP 8 준수**: 79자 제한, 타입 힌트 필수
- **테스트 필수**: 신규 기능은 단위테스트 작성
- **문서화**: 복잡한 로직은 주석 필수

#### 데이터베이스 작업
- **스키마 변경**: `data_info/*.sql` 파일 수정
- **변수 정의**: `data_info/*.yaml` 파일 수정
- **DB 파일**: `data/*.sqlite3` (Git 추적 안함)

### 테스트
```bash
# 모든 테스트 실행
pytest

# 테스트 커버리지 확인
pytest --cov=upbit_auto_trading

# 특정 모듈 테스트
pytest tests/test_trigger_builder.py -v
```

### Pull Request 가이드
```markdown
## 변경 사항
- [ ] RSI 진입 전략 구현
- [ ] 트리거 빌더 UI 업데이트

## 테스트 결과
- [ ] 기본 7규칙 전략 구성 가능
- [ ] 백테스팅 정상 동작
- [ ] UI 응답성 정상

## 스크린샷
(UI 변경 시 첨부)

Closes #42
```

---

## 📝 LLM 문서화 최적화 (LLM_DOCUMENTATION_GUIDELINES)

### LLM 인식률 최적화 원칙

#### 토큰 효율성
- **최적 길이**: 150-200줄 (인식률과 이해도 최고)
- **최소**: 50줄 (컨텍스트 부족 방지)
- **최대**: 250줄 (LLM 컨텍스트 윈도우 고려)
- **초과 시**: 하위 문서로 분리 필수

#### 구조적 명확성
```markdown
# 🎯 [아이콘] 문서 제목
> **목적**: 명확한 한 줄 설명
> **대상**: LLM 에이전트, 개발자
> **갱신**: 2025-08-03

## 📋 필수 구조 요소
1. 개요 (What): 무엇을 다루는가?
2. 목적 (Why): 왜 필요한가?
3. 방법 (How): 어떻게 구현하는가?
4. 예시 (Example): 실제 사용 사례
5. 참조 (Reference): 관련 문서들
```

#### 의미적 마커 활용
- **🚨 필수**: 반드시 지켜야 할 규칙
- **⚠️ 주의**: 실수하기 쉬운 부분
- **💡 팁**: 효율성 향상 방법
- **📝 예시**: 실제 구현 코드

### 문서 유형별 최적화

#### 명세서 (30% 비즈니스 로직, 25% 아키텍처, 25% 제약사항, 20% 참조)
- 핵심 키워드를 **볼드 처리**
- 숫자와 수치는 `백틱`으로 강조
- 목록은 계층 구조로 명확히 정리

#### 가이드 (40% 단계별 워크플로, 30% 코드 예시, 20% 검증 방법, 10% 참조)
- 코드 블록에 언어 타입 명시
- 실행 결과 예시 포함
- 조건문과 반복문 명확히 표시

#### 체크리스트 (50% 우선순위별 분류, 30% 구체적 검증 기준, 20% 도구와 명령어)
- [ ] 체크박스로 진행 상황 시각화
- 기준치는 구체적 숫자로 명시
- 검증 명령어는 코드 블록으로 제공

### LLM 이해도 향상 기법

#### 컨텍스트 압축
- 핵심 키워드를 문서 상단 배치
- 중복 설명 제거, 상호 참조 활용
- 표와 목록으로 정보 구조화

#### 의미적 일관성
- "전략" vs "Strategy": 한국어로 통일
- "컴포넌트" vs "모듈": 컨텍스트별 구분
- "DB" vs "데이터베이스": 줄임말보다 전체 용어

#### 참조 체계 최적화
- 절대 링크: [문서명](파일명.md)
- 상대 링크: [섹션명](#섹션-앵커)
- 계층적 참조 구조 유지, 순환 참조 방지

### 문서 작성 체크리스트

#### 작성 전 (계획 단계)
- [ ] 대상 독자 명확화: LLM 에이전트 vs 개발자 vs 모두
- [ ] 문서 유형 결정: 명세서 / 가이드 / 체크리스트 / 참조
- [ ] 예상 길이 계획: 150-200줄 목표로 범위 설정
- [ ] 참조 관계 설계: 어떤 문서들과 연결할 것인가?

#### 작성 중 (실행 단계)
- [ ] 구조적 마커 사용: 아이콘, 볼드, 코드 블록 적절 활용
- [ ] 코드 예시 포함: 실행 가능한 코드와 예상 결과
- [ ] 용어 일관성 확인: 프로젝트 전체 용어 사전 준수
- [ ] 점진적 상세화: 개요 → 세부사항 → 예시 → 참조 순서

#### 작성 후 (검증 단계)
- [ ] 길이 최적화: 50-250줄 범위 내 유지
- [ ] 읽기 흐름 확인: 논리적 순서와 자연스러운 연결
- [ ] 참조 링크 검증: 모든 링크가 유효하고 정확한가?
- [ ] LLM 테스트: 실제 LLM에게 문서 기반 작업 요청해보기

---

## 💡 운영 시스템 통합 전략

### 전략 시스템 개발 우선순위
1. **Domain Layer**: Strategy, Trigger 엔티티 구현
2. **Application Layer**: StrategyService, TriggerService 구현
3. **Infrastructure Layer**: Repository 패턴, Database 접근
4. **Presentation Layer**: UI 컴포넌트, Presenter 패턴

### 로깅 시스템 활용 전략
1. **개발 초기**: v3.1 호환 모드로 기존 코드 유지
2. **기능 개발**: v4.0 Enhanced 서비스로 새 기능 개발
3. **성능 최적화**: 비동기 처리, 메모리 최적화 적용
4. **운영 모니터링**: JSON 대시보드, LLM 브리핑 활용

### 문서화 워크플로
1. **요구사항 분석**: LLM vs 개발자 대상 구분
2. **구조 설계**: 150-200줄 목표, 의미적 마커 활용
3. **내용 작성**: 코드 예시, 검증 방법 포함
4. **최적화**: 토큰 효율성, 참조 체계 검증

---

**🎯 운영 성공 기준**: 기본 7규칙 전략이 완벽하게 동작하는 시스템
**💡 핵심**: 전략 시스템 견고성, 로깅 투명성, 문서 최적화!
