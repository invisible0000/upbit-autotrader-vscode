# 🧬 **MarketDataBackbone V2 - Project DNA**

> **코파일럿 연속성 보장을 위한 프로젝트 DNA**
> **어떤 상황의 코파일럿이 임무를 이어받아도 완벽하게 수행 가능**

## 📋 **프로젝트 정체성**

### 🎯 **핵심 미션**
**"업비트 REST API와 WebSocket을 개발자에게 단일 인터페이스로 제공하는 통합 백본 시스템"**

```python
# 목표 API - 개발자는 이것만 알면 됨
backbone = MarketDataBackbone()
ticker = await backbone.get_ticker("KRW-BTC", realtime=True)  # 시스템이 알아서 최적화
```

### 🏗️ **아키텍처 원칙 (전문가 검증 완료)**
1. **하이브리드 통신 모델**: WebSocket(감각) + REST(실행)
2. **3-Component 구조**: DataUnifier + ChannelRouter + SessionManager
3. **사전적 Rate Limiting**: 429 오류 원천 방지
4. **큐 기반 디커플링**: 구조적 방화벽 역할
5. **관심사의 분리**: Domain 순수성 유지

### 📊 **현재 상태 (2025-08-19)**
- ✅ **Phase 1.1 MVP 완료**: REST API 기반 기본 기능
- ✅ **16개 테스트 통과**: 100% 커버리지
- ✅ **실제 연동 검증**: BTC 160,617,000원 정확 조회
- ⏳ **Phase 1.2 예정**: WebSocket 통합

---

## 🚀 **Phase별 진화 계획**

### **Phase 1.1 ✅ 완료 (MVP)**
- 기본 MarketDataBackbone 클래스
- REST API 기반 get_ticker() 메서드
- ProactiveRateLimiter 구현
- 완전한 테스트 커버리지

### **Phase 1.2 ⏳ 진행 예정**
- WebSocket Manager 구현
- 실시간 스트림 기능
- 지능적 채널 선택
- 자동 장애 복구

### **Phase 2.0+ 🔮 미래**
- 캐싱 레이어
- 머신러닝 최적화
- 다중 거래소 지원
- 고급 모니터링

---

## 📚 **문서 네비게이션 맵**

### **🏗️ Architecture (아키텍처)**
- `V2_MASTER_ARCHITECTURE.md` - 전체 시스템 설계
- `EXPERT_RECOMMENDATIONS.md` - 전문가 분석 기반 설계
- `COMPONENT_SPECIFICATIONS.md` - 컴포넌트별 상세 명세

### **🔄 Development (개발)**
- `EVOLUTIONARY_GUIDE.md` - 점진적 개발 방법론
- `CURRENT_STATUS.md` - 실시간 진행 상황
- `NEXT_ACTIONS.md` - 다음 코파일럿을 위한 액션

### **📈 Phases (단계별)**
- `PHASE_1_1_MVP.md` - MVP 완료 상세 기록
- `PHASE_1_2_WEBSOCKET.md` - WebSocket 통합 계획
- `PHASE_ROADMAP.md` - 전체 로드맵

### **👨‍💼 Expert Analysis (전문가 분석)**
- `HYBRID_MODEL_ANALYSIS.md` - 하이브리드 모델 분석
- `UPBIT_API_CHANNEL_STUDY.md` - 업비트 API 채널 연구

---

## 🎯 **코파일럿 인수인계 체크리스트**

### **✅ 필수 읽기 문서 (순서대로)**
1. **이 문서 (PROJECT_DNA.md)** - 프로젝트 전체 이해
2. **CURRENT_STATUS.md** - 현재 상태 파악
3. **NEXT_ACTIONS.md** - 즉시 수행할 작업
4. **V2_MASTER_ARCHITECTURE.md** - 기술적 구조 이해

### **🧪 검증 절차**
```powershell
# 1. 기본 동작 확인
python demonstrate_phase_1_1_success.py

# 2. 테스트 실행
pytest tests/infrastructure/market_data_backbone/v2/ -v

# 3. 실제 API 연동 확인
python -c "
import asyncio
from upbit_auto_trading.infrastructure.market_data_backbone.v2.market_data_backbone import get_ticker_simple

async def test():
    ticker = await get_ticker_simple('KRW-BTC')
    print(f'현재가: {ticker.current_price:,.0f}원')

asyncio.run(test())
"
```

### **🔧 개발 환경 설정**
```powershell
# 프로젝트 루트에서
cd d:\projects\upbit-autotrader-vscode
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 🏛️ **아키텍처 핵심 코드 구조**

### **파일 위치 맵**
```
upbit_auto_trading/infrastructure/market_data_backbone/v2/
├── __init__.py                 # 모듈 익스포트
├── market_data_backbone.py     # 메인 백본 클래스
├── data_unifier.py            # 데이터 통합 변환
├── channel_router.py          # 채널 선택 로직
└── session_manager.py         # 연결 관리 (Phase 1.2)

tests/infrastructure/market_data_backbone/v2/
├── test_market_data_backbone.py   # 메인 테스트
├── test_data_unifier.py           # 데이터 통합 테스트
└── test_channel_router.py         # 채널 라우팅 테스트
```

### **핵심 클래스 관계**
```python
MarketDataBackbone
├── _rest_client: UpbitClient
├── _rate_limiter: ProactiveRateLimiter
├── _data_unifier: DataUnifier (Phase 1.2)
├── _channel_router: ChannelRouter (Phase 1.2)
└── _websocket_manager: WebSocketManager (Phase 1.2)
```

---

## 🔥 **즉시 시작 가능한 작업**

### **Phase 1.2 WebSocket 통합 (우선순위 1)**
```python
# 목표: 이 코드가 동작하도록 만들기
async with MarketDataBackbone() as backbone:
    # 실시간 스트림
    async for ticker in backbone.stream_ticker("KRW-BTC"):
        print(f"실시간: {ticker.current_price}")

    # 자동 채널 선택
    ticker = await backbone.get_ticker("KRW-BTC", realtime=True)
```

### **필요한 신규 구현**
1. **WebSocketManager** 클래스
2. **stream_ticker()** 메서드
3. **지능적 채널 선택** 로직
4. **자동 장애 복구** 시스템

---

## 🧠 **프로젝트 지식 베이스**

### **핵심 인사이트**
- **업비트 API 한계**: 모든 통신을 WebSocket 단일화 불가능
- **하이브리드 모델 필수**: 전문가 검증 완료된 유일한 해법
- **사전적 제어**: Rate Limiting을 429 오류 후가 아닌 사전에 제어
- **Queue의 힘**: 컴포넌트 간 디커플링으로 안정성 극대화

### **기술적 결정사항**
- **asyncio 기반**: 비동기 처리 표준
- **Decimal 사용**: 금융 데이터 정밀도 보장
- **DDD 아키텍처**: Infrastructure 레이어 순수 유지
- **TDD 접근**: 테스트 우선 개발

### **성능 기준**
- **응답시간**: < 200ms 목표 (현재 평균 14.48ms)
- **동시 요청**: 5개 72.39ms로 검증 완료
- **테스트 통과**: 16개 모두 6.26초 내 완료

---

## 🎉 **성공 지표**

### **Phase 1.1 달성 ✅**
- ✅ 기본 get_ticker() 동작
- ✅ 16개 테스트 100% 통과
- ✅ 실제 API 연동 성공
- ✅ 전문가 권고사항 100% 반영

### **Phase 1.2 목표 🎯**
- 🎯 WebSocket 실시간 스트림
- 🎯 자동 채널 선택
- 🎯 장애 복구 시스템
- 🎯 성능 최적화

---

## 🚨 **중요 주의사항**

### **절대 지켜야 할 것**
- **DDD 계층 위반 금지**: Domain에 외부 의존성 넣지 말 것
- **기존 시스템 영향 최소화**: 별도 v2 패키지로 격리
- **테스트 우선**: 모든 기능은 테스트와 함께 구현
- **Infrastructure 로깅**: print() 대신 create_component_logger 사용

### **성능 고려사항**
- **Rate Limiting 준수**: 업비트 정책 엄격 준수
- **메모리 효율성**: 대용량 스트림 처리 고려
- **연결 관리**: WebSocket 재연결 로직 필수

---

## 🔄 **문서 진화 규칙**

### **문서 생명주기**
1. **생성**: 새로운 단계 시작 시
2. **수정**: 진행 상황 반영
3. **삭제**: 불필요해진 임시 문서
4. **아카이브**: 완료된 단계 문서 보관

### **업데이트 주기**
- **실시간**: CURRENT_STATUS.md, NEXT_ACTIONS.md
- **주간**: 아키텍처 및 설계 문서
- **단계별**: Phase 완료 시 종합 문서

---

## 🎯 **다음 코파일럿을 위한 메시지**

**환영합니다! 이 프로젝트는 탄탄한 기반 위에 서 있습니다.**

1. **먼저 `CURRENT_STATUS.md`를 읽어주세요** - 현재 상황 파악
2. **`NEXT_ACTIONS.md`를 확인하세요** - 즉시 할 일 확인
3. **테스트를 실행해보세요** - 시스템 동작 확인
4. **Phase 1.2부터 시작하세요** - WebSocket 통합이 다음 목표

**당신이 성공할 수 있도록 모든 준비가 되어 있습니다! 🚀**

---

**📅 최종 업데이트**: 2025년 8월 19일
**🎯 프로젝트 상태**: Phase 1.1 완료, Phase 1.2 준비 완료
**👥 대상**: 모든 코파일럿 에이전트
