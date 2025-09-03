# 전역 WebSocket 구독 실사용 시나리오 테스트 가이드

> **실제 겪게 될 핵심 시나리오들을 난이도별로 정리한 범용 지침서**

## 🎯 Level 1: 기본 구독 시나리오 (Easy)

### 시나리오 1-1: 단일 컴포넌트 기본 구독
- **설정**: Public 연결, Private 비연결, 심플 변환 ON, 압축 통신 ON
- **상황**: 초기 상태 (구독 없음)
- **변화**: 차트위젯1이 ticker:[KRW-BTC](리얼타임) 요청
- **목표**: 전역 관리자가 첫 구독 생성 → Public WebSocket 전송 → 데이터 수신 시작
- **표시**:
  - T:+0.0s 001 REQUEST ticker KRW-BTC (차트위젯1) → WS_SEND
  - T:+0.8s 002 REALTIME ticker KRW-BTC PRICE:65000000 → 차트위젯1
  - T:+1.2s 003 REALTIME ticker KRW-BTC PRICE:65001000 → 차트위젯1
- **검증점**: 구독 상태 추적, 데이터 라우팅, 콜백 실행 정확성

### 시나리오 1-2: 동일 타입 심볼 추가
- **설정**: Public 연결, Private 비연결, 심플 변환 ON, 압축 통신 ON
- **상황**: ticker:[KRW-BTC](리얼타임) 활성 구독 중
- **변화**: 호가위젯1이 ticker:[KRW-ETH](리얼타임) 요청
- **목표**: 기존 구독에 심볼 추가 → 통합 메시지 재전송 → 두 심볼 모두 수신
- **표시**:
  - T:+0.0s 004 REQUEST ticker KRW-ETH (호가위젯1) → MERGE_SEND
  - T:+0.5s 005 REALTIME ticker KRW-BTC PRICE:65002000 → 차트위젯1
  - T:+0.7s 006 REALTIME ticker KRW-ETH PRICE:4200000 → 호가위젯1
- **검증점**: 구독 통합 로직, 기존 구독 유지, 신규 심볼 추가 정확성

## 🔥 Level 2: 스냅샷+리얼타임 혼합 (Medium)

### 시나리오 2-1: 리얼타임 구독 중 스냅샷 요청 (핵심)
- **설정**: Public 연결, Private 비연결, 심플 변환 ON, 압축 통신 ON
- **상황**:
  - 차트위젯1: ticker:[KRW-BTC,KRW-ETH,KRW-XRP](리얼타임)
  - 호가위젯1: orderbook:[KRW-BTC](리얼타임)
- **변화**: 포트폴리오위젯1이 ticker:[KRW-BTC](스냅샷) 요청
- **목표**:
  1. 전역 관리자가 리얼타임+스냅샷 통합 메시지 작성
  2. Public WebSocket 재전송 (기존 리얼타임 유지)
  3. 스냅샷 응답을 포트폴리오위젯1에게만 전달
  4. 리얼타임 데이터는 기존 구독자들에게 계속 전달
- **표시**:
  - T:+0.0s 007 REQUEST ticker KRW-BTC SNAPSHOT (포트폴리오위젯1) → MERGE_SEND
  - T:+0.3s 008 SNAPSHOT ticker KRW-BTC PRICE:65003000 VOL:0.12 → 포트폴리오위젯1
  - T:+0.8s 009 REALTIME ticker KRW-BTC PRICE:65003500 → 차트위젯1
  - T:+1.1s 010 REALTIME ticker KRW-ETH PRICE:4201000 → 차트위젯1
- **검증점**: 스냅샷/리얼타임 구분, 데이터 타입별 라우팅, 구독 상태 정확성

### 시나리오 2-2: 다중 데이터 타입 동시 요청
- **설정**: Public 연결, Private 비연결, 심플 변환 ON, 압축 통신 ON
- **상황**: ticker:[KRW-BTC](리얼타임) 활성 구독 중
- **변화**: 트레이딩위젯1이 orderbook:[KRW-BTC](리얼타임) + trade:[KRW-BTC](리얼타임) 동시 요청
- **목표**: 여러 데이터 타입을 한 번의 WebSocket 메시지로 통합 전송
- **표시**:
  - T:+0.0s 011 REQUEST orderbook+trade KRW-BTC (트레이딩위젯1) → BATCH_SEND
  - T:+0.4s 012 REALTIME ticker KRW-BTC PRICE:65004000 → 차트위젯1
  - T:+0.6s 013 REALTIME orderbook KRW-BTC ASK1:65005000 → 트레이딩위젯1
  - T:+0.9s 014 REALTIME trade KRW-BTC PRICE:65004500 VOL:0.01 → 트레이딩위젯1
- **검증점**: 배치 구독 처리, 데이터 타입별 분리 라우팅, 성능 최적화

## ⚡ Level 3: 구독 해제 및 충돌 해결 (Hard)

### 시나리오 3-1: 부분 구독 해제 최적화
- **설정**: Public 연결, Private 비연결, 심플 변환 ON, 압축 통신 ON
- **상황**:
  - 차트위젯1: ticker:[KRW-BTC,KRW-ETH](리얼타임)
  - 호가위젯1: ticker:[KRW-BTC,KRW-XRP](리얼타임)
- **변화**: 차트위젯1 종료 (ticker:[KRW-BTC,KRW-ETH] 해제 요청)
- **목표**: KRW-BTC는 호가위젯1 때문에 유지, KRW-ETH만 제거된 통합 구독 재전송
- **표시**:
  - T:+0.0s 015 CLEANUP 차트위젯1 ticker KRW-BTC,KRW-ETH → OPTIMIZE_SEND
  - T:+0.3s 016 REALTIME ticker KRW-BTC PRICE:65005000 → 호가위젯1 (유지됨)
  - T:+0.8s 017 REALTIME ticker KRW-XRP PRICE:580 → 호가위젯1 (유지됨)
  - T:+1.0s --- ticker KRW-ETH 데이터 수신 중단 (정상)
- **검증점**: 구독 중복 분석, 필요한 구독만 유지, 불필요한 구독 제거 정확성

### 시나리오 3-2: 스트림 선호도 충돌 해결
- **설정**: Public 연결, Private 비연결, 심플 변환 ON, 압축 통신 ON
- **상황**: 차트위젯1이 ticker:[KRW-BTC](리얼타임 전용) 구독 중
- **변화**: 포트폴리오위젯1이 ticker:[KRW-BTC](스냅샷 전용) 요청
- **목표**: 리얼타임 우선 정책에 따라 both 모드로 통합, 각자 필요한 데이터만 라우팅
- **표시**:
  - T:+0.0s 018 CONFLICT ticker KRW-BTC 리얼타임vs스냅샷 → RESOLVE_BOTH
  - T:+0.2s 019 SNAPSHOT ticker KRW-BTC PRICE:65006000 → 포트폴리오위젯1 (초기 데이터)
  - T:+0.8s 020 REALTIME ticker KRW-BTC PRICE:65006500 → 차트위젯1 (실시간 계속)
  - T:+1.2s 021 REALTIME ticker KRW-BTC PRICE:65007000 → 차트위젯1 (포트폴리오위젯1은 무시)
- **검증점**: 충돌 해결 정책, 선택적 데이터 라우팅, 컴포넌트별 요구사항 충족

## 🔒 Level 4: Private API 연동 (Expert)

### 시나리오 4-1: Private 연결 추가 시나리오
- **설정**: Public 연결, Private 연결 성공, API 키 유효, 심플 변환 ON, 압축 통신 ON
- **상황**: Public ticker:[KRW-BTC](리얼타임) 구독 중
- **변화**: 주문위젯1이 myOrder:(전체)(리얼타임) + myAsset:(전체)(리얼타임) 요청
- **목표**: Private WebSocket 별도 연결로 인증 후 Private 데이터 구독 시작
- **표시**:
  - T:+0.0s 022 AUTH_REQUEST Private 연결 + JWT 토큰 → PRIVATE_CONNECT
  - T:+1.2s 023 REQUEST myOrder+myAsset (주문위젯1) → PRIVATE_SEND
  - T:+1.8s 024 REALTIME myOrder ORDER_PLACED KRW-BTC → 주문위젯1
  - T:+2.1s 025 REALTIME myAsset KRW:1500000 BTC:0.02 → 주문위젯1
- **검증점**: Private 인증 처리, 이중 연결 관리, Private 데이터 보안 라우팅

### 시나리오 4-2: Public+Private 동시 데이터 활용
- **설정**: Public+Private 양쪽 연결, API 키 유효, 심플 변환 ON, 압축 통신 ON
- **상황**:
  - Public: ticker:[KRW-BTC](리얼타임), orderbook:[KRW-BTC](리얼타임)
  - Private: myOrder:(전체)(리얼타임)
- **변화**: 트레이딩뷰위젯1이 Public+Private 데이터 조합으로 매매 분석 요청
- **목표**: 양쪽 연결에서 오는 데이터를 실시간으로 조합하여 단일 컴포넌트에 전달
- **표시**:
  - T:+0.0s 026 COMBO_REQUEST Public ticker+orderbook + Private myOrder (트레이딩뷰위젯1)
  - T:+0.3s 027 REALTIME ticker KRW-BTC PRICE:65008000 → 트레이딩뷰위젯1 [PUBLIC]
  - T:+0.6s 028 REALTIME orderbook KRW-BTC ASK1:65009000 → 트레이딩뷰위젯1 [PUBLIC]
  - T:+0.9s 029 REALTIME myOrder FILLED KRW-BTC 0.001 → 트레이딩뷰위젯1 [PRIVATE]
- **검증점**: 다중 연결 데이터 통합, 보안 경계 유지, 실시간 데이터 동기화

## 💥 Level 5: 장애 복구 및 극한 상황 (Expert+)

### 시나리오 5-1: 네트워크 연결 끊김 복구
- **설정**: Public+Private 연결, 다중 컴포넌트 활성 구독 중
- **상황**: 5개 컴포넌트가 ticker+orderbook+trade+myOrder 복합 구독 중
- **변화**: 네트워크 장애로 Public 연결 끊김 → 30초 후 자동 재연결
- **목표**: 연결 복구 시 모든 구독 상태를 정확히 복원하고 데이터 수신 재개
- **표시**:
  - T:+0.0s 030 CONNECTION_LOST Public WebSocket (5개 컴포넌트 영향)
  - T:+30.0s 031 RECONNECT_START Public WebSocket → 구독 상태 복원 시작
  - T:+31.2s 032 RESTORE ticker:[KRW-BTC,KRW-ETH] orderbook:[KRW-BTC] → WS_SEND
  - T:+32.0s 033 REALTIME ticker KRW-BTC PRICE:65010000 → 모든 구독자 (복원 완료)
- **검증점**: 연결 상태 감지, 구독 상태 백업/복원, 데이터 무결성 보장

### 시나리오 5-2: 대량 컴포넌트 동시 생성/소멸
- **설정**: Public 연결, Private 비연결, 심플 변환 ON, 압축 통신 ON
- **상황**: 안정적인 기본 구독 상태
- **변화**: 10개 차트 위젯이 동시에 생성되어 각각 다른 심볼 구독 요청 → 5초 후 절반이 동시에 소멸
- **목표**: 대량 요청을 효율적으로 배치 처리하고, 소멸 시 정확한 구독 정리
- **표시**:
  - T:+0.0s 034 BATCH_CREATE 10개 위젯 ticker:[10개 심볼] → BATCH_OPTIMIZE
  - T:+0.8s 035 REALTIME ticker 10개 심볼 데이터 동시 수신 시작 → 각 위젯
  - T:+5.0s 036 BATCH_DESTROY 5개 위젯 소멸 → CLEANUP_OPTIMIZE
  - T:+5.3s 037 REALTIME ticker 5개 심볼만 수신 계속 → 남은 위젯들
- **검증점**: 배치 처리 성능, 메모리 사용량, WeakRef 정리 정확성

## 📈 성능 및 안정성 검증 포인트

### 핵심 메트릭
- **구독 지연시간**: 요청 → 첫 데이터 수신 < 3초
- **데이터 라우팅 성능**: 10개 컴포넌트 동시 처리 < 100ms
- **메모리 사용량**: 장시간 구독 시 메모리 누수 없음
- **연결 복구 시간**: 네트워크 복구 → 데이터 수신 재개 < 5초

### 스트레스 테스트 시나리오
- **대량 심볼**: 50개 심볼 동시 구독 시 안정성
- **빈번한 변경**: 1초당 10회 구독 변경 요청 처리 능력
- **장기간 운영**: 24시간 연속 구독 유지 시 안정성
- **동시 접근**: 여러 스레드에서 동시 구독 요청 시 데이터 무결성

---

## 🎯 사용 가이드

### 테스트 실행 순서
1. **Level 1-2**: 기본 기능 검증 (Mock/기본 테스트 활용)
2. **Level 3-4**: 실제 API 연동 테스트 (네트워크 필요)
3. **Level 5**: 장애 시뮬레이션 테스트 (통합 환경)

### 실제 테스트 적용 방법
각 시나리오를 `test_*_real.py` 파일에서 실제 WebSocket 연결로 검증하되,
핵심 로직은 `test_01_mock.py`에서 Mock으로 빠른 검증 병행

### 시나리오 확장 원칙
- **실사용성**: 실제 사용자가 겪을 가능성이 높은 상황
- **범용성**: 시스템 개선 후에도 여전히 유효한 시나리오
- **검증가능성**: 명확한 입력과 예상 출력으로 자동 검증 가능
- **복잡도 분리**: 단순한 것부터 복잡한 것까지 단계별 구성

---

**문서 버전**: v1.0
**작성일**: 2025년 9월 3일
**호환성**: WebSocket v6.2+ 전역 구독 관리 시스템
