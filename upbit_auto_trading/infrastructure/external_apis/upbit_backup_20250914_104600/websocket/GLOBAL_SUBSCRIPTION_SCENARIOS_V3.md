# 전역 WebSocket 구독 핵심 시나리오 테스트 가이드 V3

> **개선된 메시지 시스템과 구독 병합 최적화를 중심으로 한 실용 가이드**

## 🎯 Level 1: 기본 구독 시나리오 (Easy) - 입문자 필수

### 시나리오 1-1: 차트뷰 최초 진입 (황금 시나리오)
- **설정**: Public 연결, Private 비연결, 심플 변환 ON, 압축 통신 ON
- **상황**: 애플리케이션 최초 실행 → 차트뷰 탭 진입
- **변화**:
  1. 마켓 콤보박스 기본값(KRW) → 전체 KRW 티커 구독
  2. 기본 심볼(KRW-BTC) → 호가창 구독
- **목표**: 차트뷰의 기본 동작 패턴 검증 (가장 빈번한 사용 사례)
- **표시**:
  - T:+0.00s(Δ0.00s) REQUEST ticker 전체_KRW_심볼 (코인리스트) → WS_SEND
  - T:+0.20s(Δ0.20s) REQUEST orderbook KRW-BTC (호가창) → MERGE_SEND
  - T:+0.85s(Δ0.65s) 📨001 SNAPSHOT ticker KRW-BTC PRICE:65000000 → 코인리스트
  - T:+1.05s(Δ0.20s) 📨002 SNAPSHOT orderbook KRW-BTC ASK1:65001000 → 호가창
  - T:+1.52s(Δ0.47s) 📨003 REALTIME ticker KRW-BTC PRICE:65002000 → 코인리스트
  - T:+1.83s(Δ0.31s) 📨004 REALTIME orderbook KRW-BTC ASK1:65002500 → 호가창
- **검증점**: 다중 데이터 타입 동시 구독, 스냅샷→리얼타임 흐름, 통합 메시지 최적화

### 시나리오 1-2: 코인 선택 변경 (연쇄 반응)
- **설정**: Public 연결, Private 비연결, 심플 변환 ON, 압축 통신 ON
- **상황**: 차트뷰에서 KRW-BTC → KRW-ETH 코인 변경
- **변화**: 코인리스트 클릭 → 호가창 심볼 자동 변경
- **목표**: 효율적 구독 관리 (ticker는 유지, orderbook만 변경)
- **표시**:
  - T:+0.00s(Δ0.00s) EVENT coin_selected KRW-ETH → 내부이벤트
  - T:+0.12s(Δ0.12s) REQUEST orderbook KRW-ETH (호가창) → MERGE_SEND
  - T:+0.35s(Δ0.23s) 📨005 SNAPSHOT orderbook KRW-ETH ASK1:4200000 → 호가창
  - T:+0.81s(Δ0.46s) 📨006 REALTIME ticker KRW-ETH PRICE:4201000 → 코인리스트 (기존 구독)
  - T:+1.24s(Δ0.43s) 📨007 REALTIME orderbook KRW-ETH ASK1:4201500 → 호가창
- **검증점**: 선택적 구독 변경, 기존 구독 유지, 이벤트 기반 연동

## 🔥 Level 2: 스냅샷+리얼타임 혼합 (Medium) - 핵심 기능

### 시나리오 2-1: 스트림 타입 충돌 해결 (최고 빈도 시나리오)
- **설정**: Public 연결, Private 비연결, 심플 변환 ON, 압축 통신 ON
- **상황**:
  - 차트위젯1: ticker:[KRW-BTC](리얼타임) 활성 구독 중
  - 포트폴리오위젯1: ticker:[KRW-BTC](스냅샷) 신규 요청
- **변화**: 동일 심볼에 다른 스트림 타입 요구 → 충돌 해결
- **목표**: 리얼타임 스트림 보호하며 스냅샷 요구 충족
- **표시**:
  - T:+0.00s(Δ0.00s) CONFLICT ticker KRW-BTC 리얼타임vs스냅샷 → RESOLVE_BOTH
  - T:+0.18s(Δ0.18s) MERGE both 모드로 통합 → UPGRADE_SEND
  - T:+0.52s(Δ0.34s) 📨008 SNAPSHOT ticker KRW-BTC PRICE:65003000 → 포트폴리오위젯1
  - T:+0.84s(Δ0.32s) 📨009 REALTIME ticker KRW-BTC PRICE:65003500 → 차트위젯1
  - T:+1.25s(Δ0.41s) 📨010 REALTIME ticker KRW-BTC PRICE:65004000 → 차트위젯1 (포트폴리오는 무시)
- **검증점**: 충돌 해결 정책, 선택적 데이터 라우팅, 기존 스트림 보호

### 시나리오 2-2: 구독 병합 최적화 (신규 핵심 케이스)
- **설정**: Public 연결, Private 비연결, Rate Limit: 5req/sec, 심플 변환 ON
- **상황**: 0.1초 간격으로 5개 컴포넌트가 연속 구독 요청
- **변화**: Rate Limiter 감지 → 펜딩 큐 → 지능형 병합
- **목표**: 5개 개별 요청을 1개 통합 요청으로 최적화
- **표시**:
  - T:+0.00s(Δ0.00s) REQUEST ticker KRW-BTC (위젯1) → QUEUE_ACCEPT
  - T:+0.10s(Δ0.10s) REQUEST ticker KRW-ETH (위젯2) → QUEUE_ACCEPT
  - T:+0.20s(Δ0.10s) REQUEST ticker KRW-XRP (위젯3) → RATE_LIMIT
  - T:+0.30s(Δ0.10s) REQUEST orderbook KRW-BTC (위젯4) → PENDING
  - T:+0.40s(Δ0.10s) REQUEST trade KRW-BTC (위젯5) → PENDING
  - T:+0.65s(Δ0.25s) MERGE 5개 요청 → ticker:[BTC,ETH,XRP] + orderbook:[BTC] + trade:[BTC] → BATCH_SEND
  - T:+1.42s(Δ0.77s) 📨011 SNAPSHOT ticker 3개심볼 일괄 수신 → 위젯1,2,3
  - T:+1.68s(Δ0.26s) 📨012 SNAPSHOT orderbook KRW-BTC → 위젯4
  - T:+1.95s(Δ0.27s) 📨013 REALTIME trade KRW-BTC → 위젯5
- **검증점**: Rate Limiter 감지, 펜딩 큐 관리, 지능형 병합, 5→1 최적화 효과

## ⚡ Level 3: 구독 해제 및 최적화 (Hard) - 고급 관리

### 시나리오 3-1: 지능형 부분 해제 최적화 (핵심 효율성)
- **설정**: Public 연결, Private 비연결, 심플 변환 ON, 압축 통신 ON
- **상황**:
  - 차트위젯1: ticker:[KRW-BTC,KRW-ETH](리얼타임)
  - 호가위젯1: ticker:[KRW-BTC,KRW-XRP](리얼타임)
  - 트레이더위젯1: orderbook:[KRW-BTC](리얼타임)
- **변화**: 차트위젯1 종료 → 부분 구독 해제
- **목표**: KRW-BTC 유지(다른 위젯 사용), KRW-ETH만 제거
- **표시**:
  - T:+0.00s(Δ0.00s) CLEANUP 차트위젯1 ticker KRW-BTC,KRW-ETH → ANALYZE_DEPS
  - T:+0.12s(Δ0.12s) OPTIMIZE KRW-BTC 2개위젯 유지, KRW-ETH 제거 → SELECTIVE_SEND
  - T:+0.34s(Δ0.22s) 📨014 REALTIME ticker KRW-BTC PRICE:65007000 → 호가위젯1 (계속 수신)
  - T:+0.63s(Δ0.29s) 📨015 REALTIME orderbook KRW-BTC ASK1:65007500 → 트레이더위젯1 (계속 수신)
  - T:+0.85s(Δ0.22s) 📨016 REALTIME ticker KRW-XRP PRICE:580 → 호가위젯1 (계속 수신)
  - T:+1.02s(Δ0.17s) --- ticker KRW-ETH 수신 중단 (정상 정리)
- **검증점**: 구독 의존성 분석, 선택적 해제, 사용 중인 구독 보호

### 시나리오 3-2: 복잡한 구독 중첩 해결 (신규 고급 케이스)
- **설정**: Public 연결, Private 비연결, 복잡한 중첩 구독 환경
- **상황**:
  - 위젯A: ticker:[KRW-BTC,KRW-ETH] + orderbook:[KRW-BTC]
  - 위젯B: ticker:[KRW-BTC,KRW-XRP] + trade:[KRW-BTC]
  - 위젯C: ticker:[KRW-ETH,KRW-ADA] + orderbook:[KRW-ETH]
- **변화**: 위젯B 제거 → 복잡한 중첩 구독 재계산
- **목표**: KRW-BTC ticker 유지(위젯A), KRW-XRP 제거, trade 제거
- **표시**:
  - T:+0.00s(Δ0.00s) CLEANUP 위젯B 전체 구독 해제 → COMPLEX_ANALYZE
  - T:+0.08s(Δ0.08s) CALCULATE ticker:[BTC(A),ETH(A,C),ADA(C)] orderbook:[BTC(A),ETH(C)] → MERGE_RESULT
  - T:+0.15s(Δ0.07s) OPTIMIZE XRP 제거, trade 제거, 나머지 유지 → SELECTIVE_SEND
  - T:+0.42s(Δ0.27s) 📨017 REALTIME ticker KRW-BTC → 위젯A (유지)
  - T:+0.67s(Δ0.25s) 📨018 REALTIME ticker KRW-ETH → 위젯A,C (유지)
  - T:+0.91s(Δ0.24s) 📨019 REALTIME orderbook KRW-BTC → 위젯A (유지)
  - T:+1.18s(Δ0.27s) --- ticker KRW-XRP, trade KRW-BTC 수신 중단 (정상 정리)
- **검증점**: 복잡한 중첩 분석, 정확한 재계산, 최적화된 구독 유지

## 🔒 Level 4: Private API 통합 (Expert) - 전문가 기능

### 시나리오 4-1: Public+Private 동시 데이터 활용 (트레이딩 핵심)
- **설정**: Public+Private 연결, API 키 유효, 심플 변환 ON, 압축 통신 ON
- **상황**:
  - Public: ticker:[KRW-BTC] + orderbook:[KRW-BTC]
  - Private: myOrder:(전체) + myAsset:(전체)
- **변화**: 통합 트레이딩 대시보드가 모든 데이터 조합 요청
- **목표**: 양방향 연결 데이터 실시간 통합
- **표시**:
  - T:+0.00s(Δ0.00s) AUTH_SUCCESS Private 연결 + JWT 인증 → PRIVATE_READY
  - T:+0.23s(Δ0.23s) COMBO_REQUEST Public+Private 조합 → DUAL_SEND
  - T:+0.84s(Δ0.61s) 📨020 REALTIME ticker KRW-BTC PRICE:65008000 → 대시보드 [PUBLIC]
  - T:+1.07s(Δ0.23s) 📨021 REALTIME orderbook KRW-BTC ASK1:65009000 → 대시보드 [PUBLIC]
  - T:+1.25s(Δ0.18s) 📨022 REALTIME myOrder FILLED KRW-BTC 0.001 → 대시보드 [PRIVATE]
  - T:+1.56s(Δ0.31s) 📨023 REALTIME myAsset KRW:1500000 BTC:0.021 → 대시보드 [PRIVATE]
- **검증점**: 이중 연결 관리, 보안 경계 유지, 실시간 데이터 통합

### 시나리오 4-2: 혼합 구독 충돌 해결 (신규 Expert 케이스)
- **설정**: Public+Private 연결, 복잡한 구독 충돌 상황
- **상황**:
  - Public: ticker:[KRW-BTC](리얼타임) 활성
  - Private: myOrder 활성
- **변화**: 새 위젯이 Public ticker:[KRW-BTC](스냅샷) + Private myAsset 동시 요청
- **목표**: Public 충돌 해결 + Private 병합 + 양쪽 연결 최적화
- **표시**:
  - T:+0.00s(Δ0.00s) CONFLICT Public ticker KRW-BTC 리얼타임vs스냅샷 → RESOLVE_PUBLIC
  - T:+0.05s(Δ0.05s) MERGE Private myOrder + myAsset → PRIVATE_BATCH
  - T:+0.18s(Δ0.13s) DUAL_SEND Public 업그레이드 + Private 병합 → OPTIMIZE_BOTH
  - T:+0.52s(Δ0.34s) 📨024 SNAPSHOT ticker KRW-BTC → 신규위젯 [PUBLIC]
  - T:+0.74s(Δ0.22s) 📨025 REALTIME ticker KRW-BTC → 기존위젯 [PUBLIC]
  - T:+0.96s(Δ0.22s) 📨026 REALTIME myOrder → 기존위젯 [PRIVATE]
  - T:+1.19s(Δ0.23s) 📨027 REALTIME myAsset → 신규위젯 [PRIVATE]
- **검증점**: Public/Private 독립 충돌 해결, 이중 연결 최적화, 데이터 타입별 라우팅

## 💥 Level 5: 장애 복구 및 극한 상황 (Expert+) - 시스템 견고성

### 시나리오 5-1: 네트워크 연결 끊김 완전 복구 (최고 중요도)
- **설정**: Public+Private 연결, 다중 컴포넌트 활성 구독 중
- **상황**:
  - 5개 컴포넌트: ticker+orderbook+trade+myOrder 복합 구독
  - 네트워크 장애로 Public 연결 끊김
- **변화**: 30초 후 자동 재연결 → 모든 구독 상태 복원
- **목표**: 완벽한 상태 복원 + 데이터 무결성 보장
- **표시**:
  - T:+0.00s(Δ0.00s) CONNECTION_LOST Public WebSocket (5개 컴포넌트 영향) → DETECT_FAILURE
  - T:+0.12s(Δ0.12s) BACKUP_STATE 현재 구독 상태 백업 → STATE_SNAPSHOT
  - T:+30.0s(Δ29.88s) RECONNECT_START Public WebSocket → CONNECTION_RETRY
  - T:+31.2s(Δ1.20s) RESTORE_SUBSCRIPTIONS 백업 상태 기반 복원 → BULK_SEND
  - T:+32.1s(Δ0.90s) 📨028 REALTIME ticker KRW-BTC PRICE:65012000 → 모든 구독자 (복원 완료)
  - T:+32.6s(Δ0.50s) 📨029 REALTIME orderbook KRW-BTC ASK1:65012500 → 호가 구독자 (복원 완료)
  - T:+33.1s(Δ0.50s) VERIFY_INTEGRITY 모든 컴포넌트 데이터 수신 확인 → FULL_RECOVERY
- **검증점**: 연결 상태 감지, 구독 상태 백업/복원, 데이터 무결성, 완전 복구

### 시나리오 5-2: 구독 폭증 상황 대응 (신규 극한 케이스)
- **설정**: Public 연결, 갑작스런 대량 구독 요청 상황
- **상황**: 정상 운영 중 (10개 컴포넌트, 20개 심볼)
- **변화**: 1초 내 100개 위젯 동시 생성 → 1000개 심볼 구독 요청
- **목표**: 시스템 안정성 유지 + 효율적 배치 처리
- **표시**:
  - T:+0.00s(Δ0.00s) BURST_DETECT 100개 위젯 동시 생성 → EMERGENCY_MODE
  - T:+0.15s(Δ0.15s) RATE_PROTECT 요청 속도 제한 강화 → THROTTLE_ENABLE
  - T:+0.28s(Δ0.13s) BATCH_QUEUE 1000개 심볼 요청 대기열 → SMART_MERGE
  - T:+0.95s(Δ0.67s) OPTIMIZE_BATCH 중복 제거 → 350개 유니크 심볼로 축소
  - T:+1.20s(Δ0.25s) GRADUAL_SEND 배치별 순차 전송 시작 → LOAD_BALANCE
  - T:+3.50s(Δ2.30s) 📨030 SNAPSHOT ticker 350개심볼 1차 배치 → 해당 위젯들
  - T:+4.20s(Δ0.70s) 📨031 REALTIME ticker 350개심볼 실시간 시작 → 모든 위젯
  - T:+4.45s(Δ0.25s) NORMAL_MODE 정상 운영 모드 복귀 → LOAD_STABLE
- **검증점**: 폭증 감지, 응급 모드 전환, 배치 최적화, 점진적 처리, 안정성 유지

## 📊 실전 검증 메트릭

### 성능 기준값 (Pass/Fail 기준)
```yaml
latency_requirements:
  subscription_request_to_first_data: "<3초"     # 구독 → 첫 데이터
  subscription_merge_processing: "<500ms"       # 구독 통합 처리
  data_routing_per_message: "<100ms"           # 메시지당 라우팅
  component_callback_execution: "<50ms"        # 콜백 실행

merge_efficiency:
  batch_optimization_rate: ">=80%"             # 배치 최적화율 (5→1 등)
  merge_processing_time: "<200ms"              # 병합 처리 시간
  conflict_resolution_time: "<100ms"           # 충돌 해결 시간
  dependency_analysis_time: "<50ms"            # 의존성 분석 시간

throughput_requirements:
  concurrent_components: ">=50개"               # 동시 컴포넌트
  symbols_per_subscription: ">=200개"          # 구독당 심볼 수
  messages_per_second: ">=1000개"              # 초당 메시지 처리
  subscription_changes_per_second: ">=10회"    # 초당 구독 변경

reliability_requirements:
  message_loss_rate: "0%"                      # 메시지 손실률
  routing_accuracy: "100%"                     # 라우팅 정확도
  recovery_success_rate: ">=99%"               # 복구 성공률
  memory_leak_rate: "0MB/hour"                 # 메모리 누수
```

### 핵심 검증 시나리오 우선순위
1. **시나리오 1-1 (차트뷰 최초 진입)**: 가장 빈번한 사용 사례
2. **시나리오 2-2 (구독 병합 최적화)**: 핵심 성능 최적화
3. **시나리오 2-1 (스트림 타입 충돌)**: 핵심 기술적 도전
4. **시나리오 3-2 (복잡한 구독 중첩)**: 고급 구독 관리
5. **시나리오 5-1 (네트워크 복구)**: 시스템 견고성 검증

---

## 🎯 실행 가이드

### Phase 1: 기초 검증 (필수)
- Level 1 시나리오 1-1, 1-2 (Mock 환경)
- 예상 시간: 5분

### Phase 2: 핵심 기능 (필수)
- Level 2 시나리오 2-1, 2-2 (실제 Public API)
- 예상 시간: 12분

### Phase 3: 고급 관리 (권장)
- Level 3 시나리오 3-1, 3-2 (실제 API + 복잡 시나리오)
- 예상 시간: 18분

### Phase 4: 전문가 기능 (선택)
- Level 4 시나리오 4-1, 4-2 (Private API 필요)
- 예상 시간: 15분

### Phase 5: 극한 테스트 (선택)
- Level 5 시나리오 5-1, 5-2 (통합 환경 + 장애 시뮬레이션)
- 예상 시간: 25분

---

**문서 버전**: v3.0
**작성일**: 2025년 9월 3일
**주요 개선**: 정밀 타이밍 시스템, 구독 병합 최적화 케이스 추가, 메시지 번호 시스템
**호환성**: WebSocket v6.2+ 전역 구독 관리 시스템
