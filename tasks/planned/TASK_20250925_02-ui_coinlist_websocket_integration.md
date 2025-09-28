# 📋 TASK_20250925_02: 코인리스트 웹소켓 연동

## 🎯 태스크 목표

- **주요 목표**: CoinListService를 WebSocket v6 시스템 기반으로 재구성하여 실시간 코인 데이터 제공
- **완료 기준**: 코인리스트에서 실시간 가격 변동이 확인되고, 마켓별 필터링과 검색 기능이 정상 작동

## 📊 현재 상황 분석

### 문제점

1. **정적 데이터**: 현재 샘플 데이터만 표시, 실시간 업데이트 없음
2. **구 시스템 의존**: SmartDataProvider 기반 구조에서 벗어나지 못함
3. **사용자 경험**: 실제 투자 의사결정에 필요한 실시간 정보 부족

### 사용 가능한 리소스

- **WebSocket v6**: 완전히 구축된 업비트 웹소켓 시스템
- **WebSocketClient**: `subscribe_ticker()` API 완비
- **차트뷰 UI**: 이미 구현된 CoinListWidget과 연동 구조
- **REST API**: 마켓 목록 조회용 업비트 REST API

## 🔄 체계적 작업 절차 (필수 준수)

### 8단계 작업 절차

1. **📋 작업 항목 확인**: WebSocket 기반 CoinListService 구조 설계
2. **🔍 검토 후 세부 작업 항목 생성**: 데이터 흐름과 캐싱 전략 구체화
3. **[-] 작업중 마킹**: 해당 작업 항목을 진행 중 상태로 변경
4. **⚙️ 작업 항목 진행**: WebSocketClient 통합 및 실시간 데이터 처리 구현
5. **✅ 작업 내용 확인**: 실시간 데이터 수신 및 UI 업데이트 검증
6. **📝 상세 작업 내용 업데이트**: 구현 세부사항 및 성능 지표 기록
7. **[x] 작업 완료 마킹**: 해당 작업 항목을 완료 상태로 변경
8. **⏳ 작업 승인 대기**: 다음 태스크(차트뷰 통합) 진행 전 검토

### 작업 상태 마커

- **[ ]**: 미완료 (미시작)
- **[-]**: 진행 중 (현재 작업)
- **[x]**: 완료

## ⚙️ 작업 계획

### Phase 1: WebSocket 기반 데이터 레이어 구축

- [ ] 기존 `UpbitPublicClient.get_markets()` 통합하여 마켓 목록 조회
- [ ] WebSocketClient 통합 및 초기화 로직 구현
- [ ] 마켓별 심볼 필터링 및 배치 구독 메서드 구현
- [ ] 실시간 티커 데이터 수신 콜백 메서드 구현

### Phase 2: 데이터 처리 및 캐싱 시스템

- [ ] 티커 데이터 파싱 및 CoinInfo 변환 로직 구현
- [ ] 메모리 캐싱 전략 구현 (마켓 목록 캐싱, 티커 실시간 업데이트)
- [ ] 데이터 정렬 및 필터링 로직 개선 (거래량, 변화율 기준)
- [ ] UI 업데이트 쓰로틀링 구현 (과도한 업데이트 방지)

### Phase 3: 에러 처리 및 복원력 강화

- [ ] WebSocket 연결 실패시 폴백 메커니즘 구현
- [ ] 재연결 시나리오 처리 및 데이터 복원
- [ ] 성능 모니터링 및 로깅 시스템 구현
- [ ] 메모리 누수 방지 및 리소스 정리 로직

### Phase 4: CoinListWidget 연동 및 테스트

- [ ] CoinListWidget과의 시그널/슬롯 연결 최적화
- [ ] 실시간 UI 업데이트 테스트 및 성능 검증
- [ ] 마켓 변경, 검색, 정렬 기능 통합 테스트
- [ ] 장시간 운영 안정성 테스트

## 🛠️ 개발할 도구

- ✅ **기존 활용**: `UpbitPublicClient.get_markets()` - 마켓 목록 조회 (DDD Infrastructure Layer)
- ✅ **기존 활용**: `WebSocketClient.subscribe_ticker()` - 실시간 티커 구독 (WebSocket v6)
- 🆕 `data_throttler.py`: UI 업데이트 쓰로틀링 유틸리티 (60fps 제한)
- 🆕 CoinListService 내부 WebSocket 통합 로직

## 🎯 성공 기준

- ✅ 코인리스트에서 실시간 가격 변동 확인 (1초 이내 업데이트)
- ✅ KRW/BTC/USDT 마켓 필터링 정상 작동
- ✅ 검색 기능으로 코인 이름/심볼 필터링 가능
- ✅ 거래량/변화율 기준 정렬 기능 정상 작동
- ✅ 연결 끊김 후 자동 재연결 및 데이터 복원
- ✅ 메모리 사용량 안정성 (24시간 운영 시 메모리 누수 없음)

## 💡 작업 시 주의사항

### 성능 최적화

- **배치 구독**: 마켓당 최대 200개 심볼을 한 번에 구독
- **업데이트 쓰로틸링**: UI 업데이트는 16ms(60fps) 간격으로 제한
- **메모리 효율성**: WeakRef 패턴으로 순환 참조 방지

### DDD 아키텍처 준수

- **Application Layer**: CoinListService 인터페이스 변경 없음
- **Infrastructure Layer**: WebSocket 연결은 Infrastructure 계층에서 처리
- **Domain Layer**: CoinInfo DTO 구조 유지

### 안전성 원칙

- **Graceful Degradation**: WebSocket 실패 시 REST API 폴백
- **데이터 검증**: 수신된 티커 데이터 유효성 검사
- **에러 격리**: 하나의 심볼 오류가 전체 서비스에 영향 없도록

## 🚀 즉시 시작할 작업

```powershell
# 1. WebSocket v6 시스템 상태 확인
$env:UPBIT_CONSOLE_OUTPUT = "true"
python -c "
import asyncio
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket import WebSocketClient

async def test_websocket():
    client = WebSocketClient('test_coin_list')

    async def on_ticker(event):
        print(f'✅ 티커 수신: {event.symbol} {event.trade_price:,}원')

    await client.subscribe_ticker(['KRW-BTC'], on_ticker)
    await asyncio.sleep(5)

asyncio.run(test_websocket())
"

# 2. 현재 CoinListService 구조 분석
code upbit_auto_trading\application\chart_viewer\coin_list_service.py
```

---
**다음 에이전트 시작점**: WebSocket v6 시스템 연결 테스트 후 CoinListService 리팩터링 시작

## 📝 작업 진행 기록

### 2025-09-25 계획 수립

- 전제 조건: TASK_20250925_01 완료 (차트뷰 로딩 가능)
- 핵심 목표: 정적 데이터 → 실시간 WebSocket 데이터 전환
- 예상 소요시간: 4-6시간

### 기술 스펙

- **데이터 소스**: 업비트 WebSocket v6 (ticker 채널)
- **마켓 목록**: 업비트 REST API (/v1/market/all)
- **구독 전략**: 마켓별 배치 구독 (예: KRW 마켓 전체)
- **업데이트 주기**: 실시간 (업비트 데이터 수신시마다)
