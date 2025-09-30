# 📋 TASK_20250925_03: 차트뷰 통합 시스템 완성

## 🎯 태스크 목표

- **주요 목표**: 호가창, 캔들차트까지 모든 차트뷰 컴포넌트를 WebSocket 기반 실시간 시스템으로 통합
- **완료 기준**: 코인 선택 시 코인리스트↔호가창↔캔들차트 간 완벽한 실시간 연동 및 데이터 동기화

## 📊 현재 상황 분석

### 문제점

1. **컴포넌트 간 연동 부족**: 코인 선택해도 호가창/차트가 자동 업데이트되지 않음
2. **정적 차트 데이터**: 캔들스틱 차트가 실시간 데이터와 연결되지 않음
3. **사용자 경험 미완성**: 실제 투자 도구로 사용하기에는 기능 부족

### 사용 가능한 리소스

- **완성된 코인리스트**: WebSocket 기반 실시간 코인 데이터 (TASK 02 완료 후)
- **WebSocket v6 시스템**: orderbook, candle 채널 지원
- **기존 UI 구조**: OrderbookWidget, FinplotCandlestickWidget 구현됨
- **이벤트 시스템**: InMemoryEventBus로 컴포넌트 간 통신 가능

## 🔄 체계적 작업 절차 (필수 준수)

### 8단계 작업 절차

1. **📋 작업 항목 확인**: 호가창, 캔들차트 WebSocket 연동 및 컴포넌트 간 이벤트 연결
2. **🔍 검토 후 세부 작업 항목 생성**: 실시간 데이터 동기화 및 성능 최적화 방안
3. **[-] 작업중 마킹**: 해당 작업 항목을 진행 중 상태로 변경
4. **⚙️ 작업 항목 진행**: 각 컴포넌트 WebSocket 연동 및 이벤트 버스 통합
5. **✅ 작업 내용 확인**: 전체 차트뷰 시스템 통합 테스트 및 성능 검증
6. **📝 상세 작업 내용 업데이트**: 최종 시스템 아키텍처 및 사용법 문서화
7. **[x] 작업 완료 마킹**: 해당 작업 항목을 완료 상태로 변경
8. **⏳ 작업 승인 대기**: 7규칙 전략 시스템과의 연동 준비

### 작업 상태 마커

- **[ ]**: 미완료 (미시작)
- **[-]**: 진행 중 (현재 작업)
- **[x]**: 완료

## ⚙️ 작업 계획

### Phase 1: 호가창 WebSocket 연동

- [ ] OrderbookWidget WebSocket 연결 구현
- [ ] 실시간 호가 데이터 수신 및 UI 업데이트
- [ ] 호가 클릭 시 매매 인터페이스 준비 (Phase 4 대비)
- [ ] 시장 임팩트 분석 및 최적가 제안 기능 구현

### Phase 2: 캔들차트 WebSocket 연동

- [ ] FinplotCandlestickWidget WebSocket 연결 구현
- [ ] 실시간 캔들 데이터 수신 및 차트 업데이트
- [ ] 과거 캔들 데이터 (REST API) + 실시간 캔들 (WebSocket) 통합
- [ ] 타임프레임별 차트 전환 기능 구현 (1m, 5m, 15m, 1h, 1d)

### Phase 3: 컴포넌트 간 이벤트 연동 시스템

- [ ] 중앙 차트뷰 이벤트 버스 구현
- [ ] 코인 선택 이벤트 → 호가창/차트 자동 업데이트
- [ ] 타임프레임 변경 이벤트 → 차트 데이터 재로드
- [ ] 마켓 변경 이벤트 → 모든 컴포넌트 동기화

### Phase 4: 고급 기능 및 사용성 개선

- [ ] 차트 확대/축소, 패닝 기능 구현
- [ ] 호가창에서 가격 클릭 → 주문 인터페이스 연결 준비
- [ ] 차트 위 기술적 분석 도구 추가 (이동평균선, 볼린저밴드 등)
- [ ] 즐겨찾기 코인 리스트 동기화

### Phase 5: 성능 최적화 및 안정성 강화

- [ ] 다중 WebSocket 연결 최적화 (연결 풀링)
- [ ] 메모리 사용량 모니터링 및 최적화
- [ ] 에러 복구 및 재연결 시나리오 테스트
- [ ] 장시간 운영 스트레스 테스트

### Phase 6: 최종 통합 테스트 및 문서화

- [ ] 전체 시나리오 테스트 (코인 검색 → 선택 → 실시간 모니터링)
- [ ] 사용자 가이드 및 기능 설명 문서 작성
- [ ] 개발자 API 문서 및 확장 가이드 작성
- [ ] 7규칙 전략 시스템과의 통합 준비

## 🛠️ 개발할 도구

- `chart_view_event_bus.py`: 차트뷰 전용 이벤트 버스 (컴포넌트 간 통신)
- `realtime_orderbook_service.py`: WebSocket 기반 실시간 호가 서비스
- `realtime_candle_service.py`: WebSocket + REST API 통합 캔들 데이터 서비스
- `chart_view_coordinator.py`: 전체 차트뷰 컴포넌트 조정자
- `performance_monitor.py`: 차트뷰 성능 모니터링 도구

## 🎯 성공 기준

- ✅ **실시간 동기화**: 코인 선택 → 1초 이내 호가창/차트 업데이트
- ✅ **데이터 정확성**: WebSocket 데이터와 업비트 공식 앱 데이터 일치
- ✅ **성능 안정성**: 24시간 연속 운영 시 메모리 누수 없음
- ✅ **사용자 경험**: 부드러운 차트 업데이트 (60fps), 지연시간 최소화
- ✅ **확장성**: 새로운 차트 컴포넌트 쉽게 추가 가능한 구조
- ✅ **에러 처리**: 네트워크 오류 시 자동 복구 및 사용자 알림

## 💡 작업 시 주의사항

### 성능 최적화

- **WebSocket 연결 관리**: 불필요한 중복 연결 방지, 연결 풀링 사용
- **데이터 압축**: 대용량 캔들 데이터 효율적 처리
- **UI 렌더링**: 과도한 차트 업데이트로 인한 CPU 사용량 증가 방지

### 메모리 관리

- **데이터 생명주기**: 과거 캔들 데이터 적절한 시점에 정리
- **이벤트 리스너**: 컴포넌트 제거 시 이벤트 리스너 정리
- **WeakRef 패턴**: 컴포넌트 간 순환 참조 방지

### 사용자 경험

- **로딩 인디케이터**: 데이터 로딩 중 사용자에게 진행 상황 표시
- **에러 메시지**: 연결 오류 시 명확하고 유용한 안내 메시지
- **반응성**: 사용자 액션에 대한 즉각적인 피드백

### DDD 아키텍처 준수

- **계층 분리**: Presentation(UI) ↔ Application(Service) ↔ Infrastructure(WebSocket)
- **도메인 순수성**: 비즈니스 로직에 UI나 WebSocket 의존성 주입 금지
- **인터페이스 계약**: 각 서비스 간 명확한 인터페이스 정의

## 🚀 즉시 시작할 작업

```powershell
# 1. 현재 차트뷰 상태 확인 (TASK 01, 02 완료 후)
python run_desktop_ui.py
# → 차트뷰 접근 → 코인리스트 실시간 데이터 확인

# 2. WebSocket 호가 데이터 테스트
python -c "
import asyncio
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket import WebSocketClient

async def test_orderbook():
    client = WebSocketClient('test_orderbook')

    async def on_orderbook(event):
        print(f'📊 호가: {event.symbol}')
        print(f'  매도: {event.orderbook_units[0].ask_price:,}원 ({event.orderbook_units[0].ask_size})')
        print(f'  매수: {event.orderbook_units[0].bid_price:,}원 ({event.orderbook_units[0].bid_size})')

    await client.subscribe_orderbook(['KRW-BTC'], on_orderbook)
    await asyncio.sleep(10)

asyncio.run(test_orderbook())
"

# 3. 현재 OrderbookWidget 구조 분석
code upbit_auto_trading\ui\desktop\screens\chart_view\widgets\orderbook_widget.py
```

---
**다음 에이전트 시작점**: TASK 01, 02 완료 확인 후 OrderbookWidget WebSocket 연동부터 시작

## 📝 작업 진행 기록

### 2025-09-25 계획 수립

- 전제 조건: TASK_20250925_01, 02 완료 (차트뷰 로딩 + 코인리스트 WebSocket 연동)
- 핵심 목표: 개별 컴포넌트 → 통합된 실시간 차트뷰 시스템
- 예상 소요시간: 8-12시간

### 기술 아키텍처

```
차트뷰 통합 아키텍처:
                    ChartViewScreen
                          │
              ┌───────────┼───────────┐
              │           │           │
        CoinListWidget  Chart Area  OrderbookWidget
              │           │           │
        CoinListService  │     OrderbookService
              │           │           │
              └───────────┼───────────┘
                          │
                  ChartViewEventBus
                          │
                  WebSocket v6 System
                          │
                     업비트 API
```

### 데이터 흐름

1. **코인 선택**: CoinListWidget → ChartViewEventBus → 모든 컴포넌트
2. **실시간 데이터**: WebSocket → 각 Service → Widget 업데이트
3. **사용자 액션**: Widget 이벤트 → EventBus → 관련 컴포넌트 동기화

### 성능 목표

- **응답 시간**: 코인 선택 → 1초 이내 모든 컴포넌트 업데이트
- **메모리 사용량**: 24시간 운영 시 100MB 이하 증가
- **CPU 사용률**: 유휴 시 5% 이하, 활성 업데이트 시 20% 이하
