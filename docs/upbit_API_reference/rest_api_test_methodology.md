# 업비트 REST API 테스트 방법론

## 🎯 REST API 테스트 개요

업비트 REST API의 모든 엔드포인트를 체계적으로 검증하기 위한 표준화된 테스트 프레임워크

### 기본 원칙
- **CRUD 패턴 기반** 테스트 설계
- **Rate Limit 준수** 및 최적화
- **Public/Private 분리** 보안 관리
- **페이지네이션** 및 **필터링** 완전 검증

## 📊 REST API 구조

### Public API (인증 불필요)
#### 1. 시세 정보 (Quotation)
- **페어 목록**: `/v1/market/all`
- **현재가**: `/v1/ticker`
- **호가**: `/v1/orderbook`
- **체결**: `/v1/trades/ticks`

#### 2. 캔들 정보 (OHLCV)
- **분봉**: `/v1/candles/minutes/{unit}`
- **일봉**: `/v1/candles/days`
- **주봉**: `/v1/candles/weeks`
- **월봉**: `/v1/candles/months`

### Private API (인증 필요)
#### 1. 자산 관리 (Asset)
- **잔고 조회**: `/v1/accounts`
- **입출금 내역**: `/v1/deposits` `/v1/withdraws`

#### 2. 주문 관리 (Order)
- **주문 생성**: `POST /v1/orders`
- **주문 조회**: `GET /v1/order`
- **주문 목록**: `GET /v1/orders`
- **주문 취소**: `DELETE /v1/order`

## 🧪 7가지 표준 REST 테스트 케이스

### 1. single_endpoint_basic_request
**목적**: 기본 엔드포인트 동작 검증
- **방식**: 단일 엔드포인트 기본 파라미터
- **검증**: HTTP 상태코드, 응답 구조, 필수 필드

### 2. single_endpoint_param_validation
**목적**: 파라미터 유효성 검증
- **방식**: 다양한 파라미터 조합 테스트
- **검증**: 입력 검증, 오류 처리, 기본값 동작

### 3. single_endpoint_pagination
**목적**: 페이지네이션 완전 검증
- **방식**: limit, cursor 파라미터 조합
- **검증**: 대용량 데이터 처리, 페이지 경계 조건

### 4. single_endpoint_rate_limit
**목적**: Rate Limit 처리 검증
- **방식**: 제한 도달까지 연속 요청
- **검증**: 429 응답 처리, 백오프 알고리즘

### 5. multi_endpoint_parallel_request
**목적**: 병렬 처리 성능 검증
- **방식**: 여러 엔드포인트 동시 호출
- **검증**: 동시성 처리, 리소스 효율성

### 6. multi_endpoint_sequential_workflow
**목적**: 실제 사용 워크플로우 검증
- **방식**: 논리적 순서로 엔드포인트 연계 호출
- **검증**: 데이터 일관성, 상태 전이

### 7. error_handling_recovery
**목적**: 오류 상황 처리 검증
- **방식**: 의도적 오류 생성 및 복구
- **검증**: 오류 코드 정확성, 재시도 로직

## 📋 Public API 테스트 매트릭스

| 엔드포인트 | 기본 | 파라미터 | 페이징 | Rate Limit | 병렬 | 워크플로우 | 오류처리 |
|-----------|------|----------|--------|------------|------|-----------|----------|
| `/market/all` | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `/ticker` | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `/orderbook` | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `/trades/ticks` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/candles/minutes/1` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/candles/days` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## 📋 Private API 테스트 매트릭스

| 엔드포인트 | 기본 | 파라미터 | 페이징 | Rate Limit | 병렬 | 워크플로우 | 오류처리 |
|-----------|------|----------|--------|------------|------|-----------|----------|
| `GET /accounts` | ✅ | ✅ | ❌ | ✅ | ⚠️ | ✅ | ✅ |
| `POST /orders` | ✅ | ✅ | ❌ | ✅ | ⚠️ | ✅ | ✅ |
| `GET /orders` | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| `DELETE /order` | ✅ | ✅ | ❌ | ✅ | ⚠️ | ✅ | ✅ |

⚠️ = 신중한 테스트 필요 (실제 거래 영향)

## 🔄 Mixed API 테스트 시나리오

### 1. market_data_aggregation
- **조합**: 페어목록 → 현재가 → 호가 → 체결내역
- **목적**: 완전한 시장 정보 수집 검증

### 2. trading_simulation_workflow
- **조합**: 잔고조회 → 주문생성 → 주문조회 → 주문취소
- **목적**: 실제 거래 시뮬레이션 (테스트넷)

### 3. historical_data_analysis
- **조합**: 일봉 → 시간봉 → 분봉 → 체결내역
- **목적**: 차트 분석용 데이터 완전성 검증

### 4. portfolio_monitoring
- **조합**: 잔고 → 주문목록 → 현재가 → 손익계산
- **목적**: 포트폴리오 추적 시스템 검증

## 🎯 성능 및 안정성 기준

### Response Time 기준
- **Public API**: < 500ms (P95)
- **Private API**: < 1000ms (P95)
- **대용량 요청**: < 2000ms (P95)

### Rate Limit 기준
- **Public**: 초당 10회, 분당 600회
- **Private**: 초당 5회, 분당 200회
- **주문 API**: 초당 1회, 분당 20회

### 데이터 무결성 기준
- **필수 필드**: 100% 존재
- **타입 일치**: 100% 정확
- **범위 검증**: 100% 유효

## 🚀 테스트 실행 예시

```bash
# Public API 테스트
pytest test_rest_public_market.py       # 시장 정보
pytest test_rest_public_quotation.py    # 시세 정보
pytest test_rest_public_candles.py      # 캔들 정보

# Private API 테스트 (테스트넷)
pytest test_rest_private_accounts.py    # 자산 관리
pytest test_rest_private_orders.py      # 주문 관리

# Mixed 워크플로우 테스트
pytest test_rest_mixed_workflows.py     # 통합 시나리오
```

## 🔧 테스트 환경 설정

### 환경변수 설정
```bash
# 운영 API (조회만)
UPBIT_ACCESS_KEY=your_access_key
UPBIT_SECRET_KEY=your_secret_key

# 테스트 환경
UPBIT_TEST_MODE=true
UPBIT_RATE_LIMIT_SAFE=true
UPBIT_MAX_RETRIES=3
```

### 안전 장치
- **실제 주문 방지**: 테스트 모드 강제
- **최소 수량**: 최소 주문 단위 사용
- **즉시 취소**: 주문 후 즉시 취소
- **알림 시스템**: 실제 거래 시 알림

---

**이 테스트 방법론을 통해 업비트 REST API의 모든 기능이 안전하고 효율적으로 검증됩니다.**
