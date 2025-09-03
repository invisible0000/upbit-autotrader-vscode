# 전역 WebSocket 구독 핵심 시나리오 테스트 가이드 V2

> **실전 검증된 핵심 시나리오들을 체계화한 최종 실용 가이드**

## 🎯 Level 1: 기본 구독 시나리오 (Easy) - 입문자 필수

### 시나리오 1-1: 차트뷰 최초 진입 (황금 시나리오)
- **설정**: Public 연결, Private 비연결, 심플 변환 ON, 압축 통신 ON
- **상황**: 애플리케이션 최초 실행 → 차트뷰 탭 진입
- **변화**:
  1. 마켓 콤보박스 기본값(KRW) → 전체 KRW 티커 구독
  2. 기본 심볼(KRW-BTC) → 호가창 구독
- **목표**: 차트뷰의 기본 동작 패턴 검증 (가장 빈번한 사용 사례)
- **표시**:
  - T:+0.0s 001 REQUEST ticker 전체_KRW_심볼 (코인리스트) → WS_SEND
  - T:+0.2s 002 REQUEST orderbook KRW-BTC (호가창) → MERGE_SEND
  - T:+0.8s 003 SNAPSHOT ticker KRW-BTC PRICE:65000000 → 코인리스트
  - T:+1.0s 004 SNAPSHOT orderbook KRW-BTC ASK1:65001000 → 호가창
  - T:+1.5s 005 REALTIME ticker KRW-BTC PRICE:65002000 → 코인리스트
  - T:+1.8s 006 REALTIME orderbook KRW-BTC ASK1:65002500 → 호가창
- **검증점**: 다중 데이터 타입 동시 구독, 스냅샷→리얼타임 흐름, 통합 메시지 최적화

### 시나리오 1-2: 코인 선택 변경 (연쇄 반응)
- **설정**: Public 연결, Private 비연결, 심플 변환 ON, 압축 통신 ON
- **상황**: 차트뷰에서 KRW-BTC → KRW-ETH 코인 변경
- **변화**: 코인리스트 클릭 → 호가창 심볼 자동 변경
- **목표**: 효율적 구독 관리 (ticker는 유지, orderbook만 변경)
- **표시**:
  - T:+0.0s 007 EVENT coin_selected KRW-ETH → 내부이벤트
  - T:+0.1s 008 REQUEST orderbook KRW-ETH (호가창) → MERGE_SEND
  - T:+0.3s 009 SNAPSHOT orderbook KRW-ETH ASK1:4200000 → 호가창
  - T:+0.8s 010 REALTIME ticker KRW-ETH PRICE:4201000 → 코인리스트 (기존 구독)
  - T:+1.2s 011 REALTIME orderbook KRW-ETH ASK1:4201500 → 호가창
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
  - T:+0.0s 012 CONFLICT ticker KRW-BTC 리얼타임vs스냅샷 → RESOLVE_BOTH
  - T:+0.2s 013 MERGE both 모드로 통합 → UPGRADE_SEND
  - T:+0.5s 014 SNAPSHOT ticker KRW-BTC PRICE:65003000 → 포트폴리오위젯1
  - T:+0.8s 015 REALTIME ticker KRW-BTC PRICE:65003500 → 차트위젯1
  - T:+1.2s 016 REALTIME ticker KRW-BTC PRICE:65004000 → 차트위젯1 (포트폴리오는 무시)
- **검증점**: 충돌 해결 정책, 선택적 데이터 라우팅, 기존 스트림 보호

### 시나리오 2-2: 멀티탭 복합 구독 (실전 복잡도)
- **설정**: Public 연결, Private 비연결, 심플 변환 ON, 압축 통신 ON
- **상황**: 차트뷰 + 거래내역 + 알고리즘 탭 동시 활성
- **변화**:
  1. 차트뷰: ticker:[전체_KRW] + orderbook:[KRW-BTC]
  2. 거래내역: trade:[KRW-BTC]
  3. 알고리즘: ticker:[KRW-BTC](리얼타임 전용)
- **목표**: 다중 데이터 타입 + 스트림 타입 최적화
- **표시**:
  - T:+0.0s 017 BATCH_REQUEST 3개탭 ticker+orderbook+trade → OPTIMIZE_SEND
  - T:+0.3s 018 SNAPSHOT ticker KRW-BTC PRICE:65005000 → 차트뷰
  - T:+0.5s 019 SNAPSHOT orderbook KRW-BTC ASK1:65006000 → 차트뷰
  - T:+0.8s 020 REALTIME ticker KRW-BTC PRICE:65005500 → 차트뷰+알고리즘
  - T:+1.0s 021 REALTIME trade KRW-BTC PRICE:65005300 VOL:0.01 → 거래내역
  - T:+1.5s 022 REALTIME orderbook KRW-BTC ASK1:65006200 → 차트뷰
- **검증점**: 배치 구독 처리, 데이터 타입별 분리, 컴포넌트별 필터링

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
  - T:+0.0s 023 CLEANUP 차트위젯1 ticker KRW-BTC,KRW-ETH → ANALYZE_DEPS
  - T:+0.1s 024 OPTIMIZE KRW-BTC 2개위젯 유지, KRW-ETH 제거 → SELECTIVE_SEND
  - T:+0.3s 025 REALTIME ticker KRW-BTC PRICE:65007000 → 호가위젯1 (계속 수신)
  - T:+0.6s 026 REALTIME orderbook KRW-BTC ASK1:65007500 → 트레이더위젯1 (계속 수신)
  - T:+0.8s 027 REALTIME ticker KRW-XRP PRICE:580 → 호가위젯1 (계속 수신)
  - T:+1.0s --- ticker KRW-ETH 수신 중단 (정상 정리)
- **검증점**: 구독 의존성 분석, 선택적 해제, 사용 중인 구독 보호

### 시나리오 3-2: 대량 컴포넌트 동시 생성/소멸 (성능 테스트)
- **설정**: Public 연결, Private 비연결, 심플 변환 ON, 압축 통신 ON
- **상황**: 안정적인 기본 구독 상태
- **변화**:
  1. 10개 차트위젯 동시 생성 (각각 다른 KRW 심볼)
  2. 5초 후 5개 위젯 동시 소멸
- **목표**: 대량 배치 처리 성능 + 메모리 정리 효율성
- **표시**:
  - T:+0.0s 028 BATCH_CREATE 10개위젯 ticker:[10개_KRW_심볼] → BATCH_OPTIMIZE
  - T:+0.5s 029 SNAPSHOT ticker 10개심볼 일괄 수신 → 각 위젯
  - T:+1.0s 030 REALTIME ticker 10개심볼 실시간 시작 → 각 위젯
  - T:+5.0s 031 BATCH_DESTROY 5개위젯 소멸 → CLEANUP_OPTIMIZE
  - T:+5.2s 032 OPTIMIZE 5개심볼 구독 유지, 5개심볼 정리 → SELECTIVE_SEND
  - T:+5.5s 033 REALTIME ticker 5개심볼만 계속 → 남은 위젯들
- **검증점**: 배치 처리 성능, 메모리 사용량, WeakRef 정리, 상태 일관성

## 🔒 Level 4: Private API 통합 (Expert) - 전문가 기능

### 시나리오 4-1: Public+Private 동시 데이터 활용 (트레이딩 핵심)
- **설정**: Public+Private 연결, API 키 유효, 심플 변환 ON, 압축 통신 ON
- **상황**:
  - Public: ticker:[KRW-BTC] + orderbook:[KRW-BTC]
  - Private: myOrder:(전체) + myAsset:(전체)
- **변화**: 통합 트레이딩 대시보드가 모든 데이터 조합 요청
- **목표**: 양방향 연결 데이터 실시간 통합
- **표시**:
  - T:+0.0s 034 AUTH_SUCCESS Private 연결 + JWT 인증 → PRIVATE_READY
  - T:+0.2s 035 COMBO_REQUEST Public+Private 조합 → DUAL_SEND
  - T:+0.8s 036 REALTIME ticker KRW-BTC PRICE:65008000 → 대시보드 [PUBLIC]
  - T:+1.0s 037 REALTIME orderbook KRW-BTC ASK1:65009000 → 대시보드 [PUBLIC]
  - T:+1.2s 038 REALTIME myOrder FILLED KRW-BTC 0.001 → 대시보드 [PRIVATE]
  - T:+1.5s 039 REALTIME myAsset KRW:1500000 BTC:0.021 → 대시보드 [PRIVATE]
- **검증점**: 이중 연결 관리, 보안 경계 유지, 실시간 데이터 통합

### 시나리오 4-2: Private 연결 오류 처리 (견고성 테스트)
- **설정**: Public 연결, Private 연결 실패, API 키 오류, 심플 변환 ON
- **상황**: Public 구독 정상 동작 중
- **변화**: Private 데이터 요청 시 인증 실패 → 공개 데이터만 제공
- **목표**: 부분 실패 시 degraded 모드 동작
- **표시**:
  - T:+0.0s 040 REQUEST myOrder+myAsset (주문위젯1) → AUTH_REQUIRED
  - T:+1.0s 041 AUTH_FAILED Invalid API key → FALLBACK_MODE
  - T:+1.2s 042 NOTIFY 사용자에게 Private 기능 제한 알림 → UI_WARNING
  - T:+1.5s 043 REALTIME ticker KRW-BTC PRICE:65010000 → 차트위젯1 (Public 계속)
  - T:+2.0s 044 FALLBACK Public 데이터만 제공 → PARTIAL_SERVICE
- **검증점**: 인증 실패 처리, 서비스 degradation, 사용자 알림

## 💥 Level 5: 장애 복구 및 극한 상황 (Expert+) - 시스템 견고성

### 시나리오 5-1: 네트워크 연결 끊김 완전 복구 (최고 중요도)
- **설정**: Public+Private 연결, 다중 컴포넌트 활성 구독 중
- **상황**:
  - 5개 컴포넌트: ticker+orderbook+trade+myOrder 복합 구독
  - 네트워크 장애로 Public 연결 끊김
- **변화**: 30초 후 자동 재연결 → 모든 구독 상태 복원
- **목표**: 완벽한 상태 복원 + 데이터 무결성 보장
- **표시**:
  - T:+0.0s 045 CONNECTION_LOST Public WebSocket (5개 컴포넌트 영향) → DETECT_FAILURE
  - T:+0.1s 046 BACKUP_STATE 현재 구독 상태 백업 → STATE_SNAPSHOT
  - T:+30.0s 047 RECONNECT_START Public WebSocket → CONNECTION_RETRY
  - T:+31.2s 048 RESTORE_SUBSCRIPTIONS 백업 상태 기반 복원 → BULK_SEND
  - T:+32.0s 049 REALTIME ticker KRW-BTC PRICE:65012000 → 모든 구독자 (복원 완료)
  - T:+32.5s 050 REALTIME orderbook KRW-BTC ASK1:65012500 → 호가 구독자 (복원 완료)
  - T:+33.0s 051 VERIFY_INTEGRITY 모든 컴포넌트 데이터 수신 확인 → FULL_RECOVERY
- **검증점**: 연결 상태 감지, 구독 상태 백업/복원, 데이터 무결성, 완전 복구

### 시나리오 5-2: 메모리 압박 상황 대응 (시스템 한계)
- **설정**: Public 연결, 메모리 사용량 90% 임계점 근접
- **상황**: 100개 컴포넌트 + 전체 마켓(350개 심볼) 구독 중
- **변화**: 시스템 메모리 압박 감지 → 자동 최적화 모드
- **목표**: 서비스 중단 없이 메모리 사용량 감소
- **표시**:
  - T:+0.0s 052 MEMORY_WARNING 90% 사용량 임계점 → OPTIMIZE_MODE
  - T:+0.5s 053 ANALYZE_USAGE 컴포넌트별 메모리 사용량 분석 → PRIORITY_SORT
  - T:+1.0s 054 OPTIMIZE_SUBSCRIPTIONS 중복 제거 + 배치 통합 → MEMORY_REDUCE
  - T:+2.0s 055 GC_FORCE 강제 가비지 컬렉션 실행 → MEMORY_RECLAIM
  - T:+3.0s 056 MEMORY_NORMAL 75% 사용량으로 안정화 → NORMAL_MODE
  - T:+3.5s 057 REALTIME 모든 데이터 정상 수신 계속 → SERVICE_MAINTAIN
- **검증점**: 메모리 모니터링, 자동 최적화, 서비스 연속성, 성능 복원

## 📊 실전 검증 메트릭

### 성능 기준값 (Pass/Fail 기준)
```yaml
latency_requirements:
  subscription_request_to_first_data: "<3초"     # 구독 → 첫 데이터
  subscription_merge_processing: "<500ms"       # 구독 통합 처리
  data_routing_per_message: "<100ms"           # 메시지당 라우팅
  component_callback_execution: "<50ms"        # 콜백 실행

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
2. **시나리오 2-1 (스트림 타입 충돌)**: 핵심 기술적 도전
3. **시나리오 3-1 (부분 해제 최적화)**: 성능 최적화 핵심
4. **시나리오 5-1 (네트워크 복구)**: 시스템 견고성 검증
5. **시나리오 4-1 (Public+Private 통합)**: 고급 기능 검증

---

## 🎯 실행 가이드

### Phase 1: 기초 검증 (필수)
- Level 1 시나리오 1-1, 1-2 (Mock 환경)
- 예상 시간: 5분

### Phase 2: 핵심 기능 (필수)
- Level 2 시나리오 2-1, 2-2 (실제 Public API)
- 예상 시간: 10분

### Phase 3: 고급 관리 (권장)
- Level 3 시나리오 3-1, 3-2 (실제 API + 부하 테스트)
- 예상 시간: 15분

### Phase 4: 전문가 기능 (선택)
- Level 4 시나리오 4-1, 4-2 (Private API 필요)
- 예상 시간: 10분

### Phase 5: 극한 테스트 (선택)
- Level 5 시나리오 5-1, 5-2 (통합 환경 + 장애 시뮬레이션)
- 예상 시간: 20분

---

**문서 버전**: v2.0
**작성일**: 2025년 9월 3일
**기반**: 실전 검증된 시나리오 01~03 통합 분석
**호환성**: WebSocket v6.2+ 전역 구독 관리 시스템
