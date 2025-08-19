# 🏗️ **MarketDataBackbone V2 - 현실적 페이즈 계획**

> **핵심**: 단순한 통신 채널 통합이 아닌, 효율적인 마켓 데이터 관리 및 전체 시스템 공급 백본
> **목표**: 7규칙 자동매매 전략이 완벽하게 동작하는 고성능 데이터 인프라

---

## 📋 **문서 정보**
- **작성일**: 2025년 8월 19일
- **현재 진행률**: Phase 2.1 완료 (81/81 테스트 통과)
- **대상 독자**: LLM Agent (GitHub Copilot), 개발자
- **업데이트 주기**: 각 페이즈 완료 시

---

## 🎯 **시스템 비전 및 핵심 가치**

### **시스템 목표**
```python
# 최종 목표: 투명한 고성능 데이터 백본
backbone = MarketDataBackbone()

# 차트뷰어에서 요청
chart_data = await backbone.get_candles("KRW-BTC", "1m", 200)  # < 50ms

# 7규칙 전략에서 실시간 지표 계산
rsi = await backbone.get_indicator("KRW-BTC", "RSI", period=14)  # < 10ms (캐시)

# 실시간 스트림 (WebSocket)
async for ticker in backbone.stream_ticker("KRW-BTC"):
    strategy.evaluate_rules(ticker)  # 즉시 전략 평가
```

### **핵심 가치**
1. **성능**: 차트뷰 < 50ms, 캐시된 지표 < 10ms, 실시간 < 20ms
2. **효율성**: 지능형 캐싱, 중복 계산 방지, 메모리 최적화
3. **신뢰성**: 99.9% 가용성, 자동 장애 복구, 데이터 일관성
4. **확장성**: 다중 심볼, 타임프레임, 지표 동시 처리

---

## 📊 **현재 상태 요약 (2025-08-19)**

### ✅ **완료된 기반 시스템**
- **Phase 1.1-1.3**: MarketDataBackbone V2 (62/62 테스트)
- **Phase 2.1**: UnifiedMarketDataAPI (19/19 테스트)
- **총 81개 테스트** 모두 통과 ✅

### 🔥 **핵심 성과**
- **캐싱 성능**: 2.3배 향상 (0.503ms → 0.220ms)
- **데이터 통합**: REST ↔ WebSocket 필드명 통일
- **지능형 라우팅**: 빈도 기반 채널 자동 선택
- **DB 구조**: 인덱스 최적화, 타임프레임별 분리

### ❌ **현재 한계점**
- **모의 데이터**: 실제 API 연동 없음
- **WebSocket 미구현**: REST 폴백만 사용
- **7규칙 분리**: 전략 시스템과 데이터 백본 미연결

---

## 🚀 **Phase 2.2: 실제 API 연동 (우선순위 1)**

**예상 기간**: 3-5일
**목표**: 모의 데이터 → 실제 업비트 API 완전 연동

### **구체적 작업 계획**

#### **Step 1: REST 클라이언트 연동 (1일)**
```python
# 현재 (모의)
mock_rest_data = self._create_mock_rest_data(symbol)

# 목표 (실제)
from upbit_auto_trading.infrastructure.external_api import UpbitPublicClient
rest_data = await self._upbit_client.get_ticker(symbol)
```

**작업 세부사항**:
- [ ] UpbitPublicClient 인스턴스 주입
- [ ] 실제 API 응답 파싱 로직
- [ ] 에러 처리 (HTTP 429, 네트워크 오류)
- [ ] Rate limit 준수 (초당 10회 제한)

#### **Step 2: WebSocket 클라이언트 구현 (2일)**
```python
# 목표: 실제 WebSocket 연결
class UpbitWebSocketClient:
    async def subscribe_ticker(self, symbols: List[str]) -> None:
        """실시간 티커 구독"""

    async def subscribe_orderbook(self, symbols: List[str]) -> None:
        """실시간 호가 구독"""
```

**작업 세부사항**:
- [ ] WebSocket 연결 관리 (자동 재연결)
- [ ] 구독/해제 메시지 처리
- [ ] 실시간 데이터 파싱 및 정규화
- [ ] 연결 상태 모니터링

#### **Step 3: 통합 테스트 (1일)**
- [ ] 실제 API 응답 데이터 검증
- [ ] WebSocket 연결 안정성 테스트
- [ ] SmartChannelRouter 실제 라우팅 검증
- [ ] 성능 벤치마크 (응답시간 측정)

### **성공 기준**
- [ ] 실제 BTC 현재가 정확 조회 (< 100ms)
- [ ] WebSocket 실시간 스트림 연결 안정성
- [ ] SmartChannelRouter 자동 채널 선택 정확성 > 95%
- [ ] 모든 기존 테스트 통과 (81/81)

---

## 🎯 **Phase 2.3: 7규칙 전략 시스템 통합 (우선순위 2)**

**예상 기간**: 5-7일
**목표**: MarketDataBackbone ↔ 7규칙 전략 시스템 완전 연동

### **구체적 작업 계획**

#### **Step 1: 데이터 공급 인터페이스 구현 (2일)**
```python
class StrategyDataProvider:
    """전략 시스템용 데이터 공급자"""

    async def get_current_price(self, symbol: str) -> Decimal:
        """현재가 조회 (캐시 우선)"""

    async def get_rsi(self, symbol: str, period: int = 14) -> Decimal:
        """RSI 지표 (지능형 캐싱)"""

    async def get_price_change_rate(self, symbol: str) -> Decimal:
        """수익률 계산 (실시간)"""
```

**작업 세부사항**:
- [ ] 지표 캐시 시스템 (indicator_cache 테이블 활용)
- [ ] 실시간 가격 변화 감지
- [ ] 백그라운드 지표 업데이트
- [ ] 데이터 일관성 보장

#### **Step 2: 트리거 시스템 연동 (2일)**
```python
# 목표: 실시간 트리거 평가
async def evaluate_triggers(symbol: str) -> List[TriggerResult]:
    """7규칙 실시간 평가"""
    current_data = await data_provider.get_market_snapshot(symbol)

    results = []
    for rule in seven_rules:
        if rule.should_trigger(current_data):
            results.append(rule.create_trigger_result())

    return results
```

**작업 세부사항**:
- [ ] 실시간 데이터 → 트리거 조건 평가
- [ ] 7규칙 조건 체크 (RSI, 수익률, 급락/급등 감지)
- [ ] 트리거 결과 이벤트 발행
- [ ] 백테스팅 데이터 준비

#### **Step 3: UI 통합 검증 (2일)**
- [ ] 트리거 빌더에서 7규칙 구성 가능
- [ ] 실시간 데이터 반영 확인
- [ ] 차트뷰에서 데이터 요청 성능 측정
- [ ] 전체 시스템 통합 테스트

### **성공 기준**
- [ ] `python run_desktop_ui.py` → 전략 관리 → 7규칙 구성 완료
- [ ] 실시간 RSI 계산 < 10ms (캐시된 경우)
- [ ] 트리거 평가 전체 처리시간 < 50ms
- [ ] Dry-run 모드에서 안전한 매매 신호 생성

---

## 📈 **Phase 2.4: 성능 최적화 & 안정성 (우선순위 3)**

**예상 기간**: 3-4일
**목표**: 프로덕션 레벨 성능 및 안정성 달성

### **구체적 작업 계획**

#### **Step 1: 캐싱 고도화 (1-2일)**
```python
class AdvancedCacheManager:
    """Redis 연동 분산 캐시"""

    async def get_with_fallback(self, key: str) -> Any:
        """Redis → 메모리 → DB 순차 조회"""

    async def warm_up_cache(self, symbols: List[str]) -> None:
        """사전 캐시 워밍업"""
```

**작업 세부사항**:
- [ ] Redis 연동 (로컬 개발용)
- [ ] 캐시 워밍업 전략
- [ ] 캐시 무효화 정책
- [ ] 메모리 사용량 모니터링

#### **Step 2: 연결 풀 & 배치 처리 (1-2일)**
- [ ] HTTP 연결 풀 관리
- [ ] WebSocket 연결 재사용
- [ ] 다중 심볼 배치 요청
- [ ] 백그라운드 데이터 동기화

#### **Step 3: 모니터링 & 메트릭 (1일)**
- [ ] 성능 메트릭 수집 (응답시간, 처리량)
- [ ] 에러율 모니터링
- [ ] 자동 알림 시스템
- [ ] 데이터 품질 지표

### **성능 목표**
- **응답시간**: 차트뷰 < 50ms, 지표 < 10ms
- **처리량**: 동시 100 요청/초 처리
- **가용성**: 99.9% 업타임
- **메모리**: 안정적 메모리 사용 (< 1GB)

---

## 🔮 **Phase 3.0+: 장기 로드맵 (2025년 10월 이후)**

### **Phase 3.1: AI 기반 최적화 (10월)**
- **예측적 캐싱**: 사용 패턴 학습
- **지능형 라우팅**: ML 기반 채널 선택
- **이상 탐지**: 데이터 품질 자동 검증

### **Phase 3.2: 다중 거래소 지원 (11월)**
- **바이낸스 어댑터**: 크로스 거래소 데이터
- **통합 데이터 모델**: 거래소별 차이 추상화
- **차익거래 지표**: 실시간 프리미엄 추적

### **Phase 3.3: 엔터프라이즈 기능 (12월)**
- **마이크로서비스**: 독립 배포 가능
- **분산 처리**: Kubernetes 스케일링
- **보안 강화**: API 키 관리, 감사 로그

---

## 📋 **개발 우선순위 및 일정**

### **즉시 시작 (이번 주)**
1. **Phase 2.2**: 실제 API 연동 (3-5일)
2. **Phase 2.3**: 7규칙 전략 통합 (5-7일)

### **단기 목표 (9월)**
3. **Phase 2.4**: 성능 최적화 (3-4일)
4. **통합 테스트**: 전체 시스템 검증 (2-3일)

### **중기 목표 (10월 이후)**
5. **Phase 3.0+**: AI 최적화, 다중 거래소

---

## ⚠️ **리스크 관리**

### **기술적 리스크**
- **업비트 API 변경**: 어댑터 패턴으로 완화
- **WebSocket 불안정**: 자동 재연결 + REST 폴백
- **성능 저하**: 지속적 모니터링 + 최적화

### **일정 리스크**
- **복잡성 증가**: 단계별 점진적 개발
- **테스트 부족**: TDD 방법론 엄격 적용
- **통합 오류**: 매일 통합 테스트 실행

---

## 🎯 **다음 코파일럿을 위한 액션 아이템**

### **즉시 착수 가능한 작업**
1. **UpbitPublicClient 주입**: unified_market_data_api.py 수정
2. **실제 API 응답 파싱**: _get_ticker_rest() 메서드 구현
3. **WebSocket 클라이언트**: _get_ticker_websocket() 실제 구현
4. **통합 테스트**: 실제 데이터로 검증

### **코드 위치**
- **주요 파일**: `upbit_auto_trading/infrastructure/market_data_backbone/v2/unified_market_data_api.py`
- **테스트**: `tests/infrastructure/market_data_backbone/v2/test_unified_market_data_api.py`
- **전략 연동**: `upbit_auto_trading/application/use_cases/trigger_builder/`

### **검증 명령어**
```powershell
# 현재 시스템 확인
python demonstrate_phase_2_1_unified_api.py

# 실제 API 연동 후 테스트
pytest tests/infrastructure/market_data_backbone/v2/ -v

# 7규칙 시스템 검증
python run_desktop_ui.py  # → 전략 관리 → 트리거 빌더
```

---

**📅 작성일**: 2025년 8월 19일
**🔄 다음 업데이트**: Phase 2.2 완료 시
**👥 대상**: LLM Agent + 개발팀
