# 🏗️ Market Data Backbone System

## 🎯 **시스템 개요**

Market Data Backbone은 **업비트 자동매매 시스템의 핵심 데이터 인프라**로, 모든 마켓 데이터 요청을 효율적이고 안정적으로 처리하는 3-Layer 아키텍처입니다.

### 🌟 **핵심 가치**
- **완전한 추상화**: 비즈니스 로직이 거래소 API 구조를 몰라도 됨
- **실거래 성능**: 메모리 캐시 우선으로 밀리초 응답 보장
- **무제한 확장**: 3-Layer 구조로 각 레이어 독립적 확장
- **자율적 최적화**: 시스템이 스스로 최적 경로 선택

## 🏗️ **3-Layer 아키텍처**

```
📱 클라이언트 애플리케이션들
├── 🎯 실거래봇 (우선순위: CRITICAL)
├── 📊 차트뷰어 (우선순위: NORMAL)
├── 🔍 스크리너 (우선순위: HIGH)
└── 📈 백테스터 (우선순위: LOW)
    ↓
🌐 **Layer 3: Market Data Storage**
├── 📊 영속성 관리 (캔들 데이터만 DB 저장)
├── 🚀 캐싱 시스템 (메모리 + 디스크)
├── 🔧 DB 최적화 (파편화 관리, 인덱스)
└── 📈 비즈니스 서비스 인터페이스
    ↓
⚡ **Layer 2: Market Data Coordinator**
├── 🔄 대용량 요청 분할 (200개 → 여러 요청)
├── 🚀 병렬 처리 최적화
├── 🔗 결과 통합 및 검증
└── 📊 성능 모니터링
    ↓
🧠 **Layer 1: Smart Routing**
├── 🎯 API 완전 추상화 (URL 구조 은닉)
├── 🔄 자율적 채널 선택 (REST ↔ WebSocket)
├── ⚡ 실시간 데이터 캐시
└── 📏 API 제한 준수 (200개 이내)
    ↓
🔌 **업비트 API**
├── 🌐 REST API (안정성)
└── ⚡ WebSocket (실시간성)
```

## 📊 **Layer별 상세 역할**

### 🧠 **Layer 1: Smart Routing** ⭐ 핵심
- **완전한 API 추상화**: 내부 시스템이 업비트 URL 구조를 몰라도 됨
- **자율적 채널 선택**: 요청 패턴 분석으로 REST ↔ WebSocket 자동 전환
- **실시간 데이터 캐시**: WebSocket → 메모리 → 매매변수 계산 (< 1ms)
- **API 제한 준수**: 업비트 200개 제한 내에서만 동작, 초과 시 에러

### ⚡ **Layer 2: Market Data Coordinator**
- **대용량 요청 분할**: 1000개 요청 → 5번의 200개 요청으로 자동 분할
- **병렬 처리 최적화**: 동시 요청으로 3-5배 성능 향상
- **결과 통합**: 분할된 응답을 하나의 완전한 데이터셋으로 합성
- **에러 복구**: 일부 요청 실패 시 자동 재시도 및 복구

### 🌐 **Layer 3: Market Data Storage**
- **선택적 영속성**: 캔들 데이터만 DB 저장, 실시간 데이터는 메모리만
- **지능적 캐싱**: 계층적 캐시 (메모리 → 디스크 → DB)
- **DB 최적화**: 자동 VACUUM, 인덱스 관리, 파편화 모니터링
- **비즈니스 인터페이스**: 클라이언트가 필요한 데이터를 직접 요청

## 🎯 **실거래 데이터 아키텍처**

### 🔄 **하이브리드 데이터 흐름**
```
실거래 시나리오:
🌐 WebSocket 수신 (0.5초~5초 갱신)
    ↓
💾 RealtimeDataCache (메모리) ← 매매변수 계산기 (즉시 접근)
    ↓
📊 캔들 완성 시 → CandleDB (비동기 저장)

매매변수 계산 요청:
1. 💾 메모리 캐시 확인 (최신 미완성 캔들)
2. 📊 CandleDB 조회 (과거 완성된 캔들)
3. 🔗 통합하여 계산에 사용
```

### 📊 **테이블 구조 (심볼별×타임프레임별 개별)**
```sql
-- 개별 테이블로 완전 분리
candles_KRW_BTC_1m   (timestamp, open, high, low, close, volume)
candles_KRW_BTC_5m   (timestamp, open, high, low, close, volume)
candles_KRW_ETH_1m   (timestamp, open, high, low, close, volume)
candles_KRW_ETH_1d   (timestamp, open, high, low, close, volume)

-- 장점:
-- ✅ 독립적 파편화 관리
-- ✅ 개별 최적화 가능
-- ✅ 인덱스 단순화 (timestamp만)
-- ✅ 타입별 요구사항 대응
```

## 🚀 **성능 최적화**

### ⚡ **실거래 성능 목표**
- **실시간 데이터 접근**: < 1ms (메모리 캐시)
- **캔들 데이터 조회**: < 10ms (하이브리드)
- **대용량 처리**: 3-5배 성능 향상 (병렬화)
- **WebSocket 처리**: < 5ms (비동기)

### 🎯 **우선순위 기반 처리**
```python
Priority.CRITICAL  # 실거래봇 → 직접 액세스, 최고 성능
Priority.HIGH      # 실시간 모니터링 → 빠른 처리
Priority.NORMAL    # 차트뷰어 → 표준 처리
Priority.LOW       # 백테스터 → 시스템 보호, 제한적 처리
```

## 🛠️ **사용법 가이드**

### 📱 **클라이언트별 사용 패턴**

#### 🎯 **실거래봇** (최고 우선순위)
```python
# 실시간 포지션 계산
router = SmartDataRouter()

# 1분봉 400개 + 실시간값 (메모리 캐시에서 즉시)
historical = await router.get_candle_data(symbol, Timeframe.M1, count=400)
realtime = await router.get_ticker_data(symbol)

# 매매 신호 계산 (< 10ms)
signal = calculate_trading_signal(historical, realtime)
```

#### 📊 **차트뷰어** (표준 처리)
```python
# 대용량 데이터 → Coordinator가 자동 분할
coordinator = MarketDataCoordinator()

# 1200개 캔들 → 6번의 200개 요청으로 자동 분할
candles = await coordinator.get_candle_data(symbol, timeframe, count=1200)

# 실시간 업데이트
ticker = await router.get_ticker_data(symbol)
```

#### 🔍 **스크리너** (고빈도 처리)
```python
# 189개 심볼 병렬 처리
symbols = get_krw_market_symbols()  # 189개
tasks = [router.get_ticker_data(symbol) for symbol in symbols]
tickers = await asyncio.gather(*tasks)

# 조건 필터링 후 알림
filtered = screen_by_conditions(tickers)
```

#### 📈 **백테스터** (낮은 우선순위)
```python
# 대용량 백테스트 데이터 (시스템 보호 하에)
storage = MarketDataStorage()

# 3개월 데이터 → 청크별 처리
candles = await storage.get_candle_data(
    symbol, timeframe,
    start_time=three_months_ago,
    end_time=now,
    priority=Priority.LOW  # 낮은 우선순위
)
```

## 📚 **각 Layer 상세 문서**

### 🧠 **Smart Routing (Layer 1)**
- [📖 Smart Routing 완전 가이드](smart_routing/README.md)
- [🔌 API 참조 문서](smart_routing/API_REFERENCE.md)
- [⚡ 실시간 데이터 아키텍처](../REALTIME_DATA_ARCHITECTURE_PLAN.md)

### ⚡ **Market Data Coordinator (Layer 2)**
- [📖 Coordinator 개발 가이드](coordinator/README.md)
- [🔄 분할 전략 문서](coordinator/SPLITTING_STRATEGIES.md)
- [🚀 병렬 처리 최적화](coordinator/PARALLEL_OPTIMIZATION.md)

### 🌐 **Market Data Storage (Layer 3)**
- [📖 Storage 시스템 가이드](storage/README.md)
- [💾 DB 최적화 전략](storage/DATABASE_OPTIMIZATION.md)
- [🚀 캐싱 시스템](storage/CACHING_SYSTEM.md)

## 🔄 **개발 프로세스**

### 📋 **현재 진행 상황**
- **Smart Routing**: 🟢 기본 구현 완료, 실시간 아키텍처 통합 중
- **Coordinator**: 🟡 설계 완료, 구현 예정
- **Storage**: 🟡 설계 완료, 구현 예정
- **통합 테스트**: 🔴 Layer별 완료 후 진행

### 📝 **관련 태스크**
- [TASK_20250820_01: Smart Routing 점진적 개선](../../tasks/active/TASK_20250820_01-smart_routing_abstraction_redesign.md)
- [TASK_20250820_02: Market Data Coordinator 개발](../../tasks/active/TASK_20250820_02-market_data_coordinator_development.md)
- [TASK_20250820_03: Market Data Storage 개발](../../tasks/active/TASK_20250820_03-market_data_storage_development.md)
- [TASK_20250820_04: Backbone API 통합](../../tasks/active/TASK_20250820_04-market_data_backbone_api_development.md)

## 🎯 **설계 철학**

### ✅ **핵심 원칙**
1. **완전한 추상화**: 비즈니스 로직과 API 구조 완전 분리
2. **실거래 우선**: 매매 성능을 최우선으로 하는 아키텍처
3. **자율적 최적화**: 시스템이 스스로 최적 경로 선택
4. **계층별 독립성**: 각 Layer의 책임과 역할 명확히 분리
5. **점진적 개선**: 기존 코드 재사용하며 단계적 발전

### ❌ **금지 사항**
- Layer 간 역할 침범 (예: Layer 1에서 대용량 처리)
- URL 구조 노출 (완전한 추상화 위배)
- 실거래 성능 저하 (메모리 캐시 우회)
- 동기 DB 액세스 (실시간 성능 저하)

## 🚀 **미래 확장성**

### 🔮 **확장 가능 영역**
- **다중 거래소**: 바이낸스, 코인베이스 등 추가
- **ML 최적화**: 머신러닝 기반 채널 선택
- **분산 처리**: 마이크로서비스 아키텍처 전환
- **실시간 스트리밍**: 더 복잡한 실시간 데이터 처리

### 🎯 **장기 비전**
Market Data Backbone이 **업비트 자동매매의 핵심 인프라**로 자리잡아, 모든 데이터 요구사항을 **투명하고 효율적으로** 처리하는 것을 목표로 합니다.

---

## 📞 **문의 및 지원**
- 📧 기술 문의: [이슈 트래커](../../issues)
- 📚 추가 문서: [docs/](../)
- 🔧 개발 가이드: [CONTRIBUTING.md](../../CONTRIBUTING.md)
