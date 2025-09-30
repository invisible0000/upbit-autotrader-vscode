# 📋 TASK_20250930_01: 필수 기반 서비스 구조 연구 및 설계 개선

## 🎯 태스크 목표

### 주요 목표

**시스템 전반에 영향을 미치는 기초 서비스들의 구조적 문제 분석 및 설계 개선안 도출**

- 기반 서비스들의 인스턴스 생성 패턴 및 생명주기 관리 문제 해결
- Container DI와 직접 생성 패턴 혼재로 인한 동시성 및 일관성 문제 분석
- Singleton 패턴 적용 및 의존성 주입 아키텍처 통합 방안 수립

### 완료 기준

- ✅ 기반 서비스들의 현재 인스턴스 생성 패턴 완전 분석
- ✅ 동시성 문제 및 데이터 불일치 원인 규명
- ✅ 통합된 서비스 아키텍처 설계안 제시
- ✅ 우선순위별 개선 로드맵 수립

---

## 📊 현재 상황 분석

### 🚨 발견된 핵심 문제들

**1. ApiKeyService 다중 인스턴스 문제 (로그 분석 결과)**

```
저장: 44bytes → 로드: 34bytes (키 크기 불일치)
✅ 암호화 키 DB 저장 완료 (Repository) ← 성공 로그
❌ 저장 후 재로드 검증 실패: 키 불일치 ← 실제 문제
```

**2. 인스턴스 생성 패턴 혼재**

- **Container DI 방식**: UI/Application 계층에서 사용
- **직접 생성 방식**: UpbitAuthenticator 등에서 사용
- **결과**: 서로 다른 DB 연결 및 상태 불일치

**3. 동시성 제어 부족**

- 여러 인스턴스가 동시에 DB 접근
- 트랜잭션 격리 수준 문제
- Race Condition 발생 가능성

### 영향 받는 기반 서비스들

#### **1. ApiKeyService** (최우선 문제)

- **역할**: API 키 암호화 저장/로드, JWT 토큰 생성
- **사용처**: UI, WebSocket, Auth, 외부 API 호출
- **문제**: 다중 인스턴스로 인한 데이터 불일치

#### **2. DatabaseManager**

- **역할**: SQLite 연결 관리, 트랜잭션 처리
- **사용처**: 모든 Repository 계층
- **문제**: 인스턴스별 다른 연결 풀 사용 가능성

#### **3. 업비트 REST API 서비스**

- **역할**: 업비트 API 호출, 응답 캐싱, 오류 처리
- **사용처**: 시장 데이터 수집, 주문 실행, 계좌 조회
- **문제**: 요청 경합 및 Rate Limit 위반 가능성

#### **4. WebSocket 서비스**

- **역할**: 실시간 시장 데이터 스트리밍
- **사용처**: 실시간 차트, 호가 데이터, 체결 데이터
- **문제**: 연결 관리 및 메시지 처리 경합

#### **5. Rate Limiter 서비스**

- **역할**: API 호출 빈도 제어, 백오프 전략 실행
- **사용처**: 모든 외부 API 호출 전 검증
- **문제**: 분산 인스턴스로 인한 제한 정책 불일치

#### **6. ApplicationLoggingService**

- **역할**: 전역 로깅 시스템
- **사용처**: 모든 계층 (Infrastructure, Application, Presentation)
- **문제**: 인스턴스 분산으로 인한 로그 일관성 문제

#### **7. PathConfigurationService**

- **역할**: 프로젝트 경로 관리
- **사용처**: 파일 I/O, 설정 로드
- **문제**: 경로 불일치 가능성

### 사용 가능한 리소스

#### 핵심 분석 대상 파일

- **DI Container**: `upbit_auto_trading/infrastructure/dependency_injection/container.py`
- **Application Container**: `upbit_auto_trading/application/container.py`
- **App Context**: `upbit_auto_trading/infrastructure/dependency_injection/app_context.py`
- **ApiKeyService**: `upbit_auto_trading/infrastructure/services/api_key_service.py`
- **DatabaseManager**: `upbit_auto_trading/infrastructure/database/database_manager.py`

#### 문제 발생 지점들

- **UpbitAuthenticator**: `upbit_auto_trading/infrastructure/external_apis/upbit/upbit_auth.py`
- **SettingsViewFactory**: `upbit_auto_trading/application/factories/settings_view_factory.py`
- **MainApp 초기화**: `run_desktop_ui.py`

---

## 🔄 체계적 작업 절차 (8단계 필수 준수)

### Phase 1: 현재 서비스 아키텍처 전면 분석

#### 1.1 기반 서비스 인스턴스 생성 패턴 분석

- [ ] ApiKeyService 인스턴스 생성 지점 전체 추적
- [ ] DatabaseManager 인스턴스 생성 패턴 분석
- [ ] 업비트 REST API 서비스 인스턴스 분산 현황
- [ ] WebSocket 서비스 연결 관리 패턴 조사
- [ ] Rate Limiter 서비스 인스턴스화 방식 분석
- [ ] ApplicationLoggingService 인스턴스 분산 현황 파악
- [ ] PathConfigurationService 사용 패턴 조사

#### 1.2 의존성 주입 vs 직접 생성 혼재 분석

- [ ] Container DI를 통한 인스턴스 생성 경로 추적
- [ ] 직접 생성 (new) 패턴 사용 지점 식별
- [ ] 각 생성 방식의 생명주기 및 스코프 분석
- [ ] 인스턴스 간 상태 공유 및 격리 현황 파악

#### 1.3 이벤트 루프 기반 통합 서비스 풀 현황 분석

- [ ] 현재 이벤트 루프 (asyncio/QAsync) 사용 패턴 조사
- [ ] 서비스별 비동기 처리 방식 및 큐 관리 분석
- [ ] 이벤트 기반 통신 vs 직접 호출 패턴 구분
- [ ] 서비스 간 메시지 패싱 및 이벤트 전파 경로 추적

#### 1.4 동시성 및 Thread Safety 분석

- [ ] 멀티스레딩 환경에서 서비스 접근 패턴 조사
- [ ] 공유 리소스 (DB, API, WebSocket) 접근 시 락 메커니즘 분석
- [ ] Race Condition 발생 가능 지점 식별
- [ ] 트랜잭션 격리 수준 및 일관성 보장 방식 검토
- [ ] 이벤트 루프 내에서 서비스 요청 경합 분석

### Phase 2: 문제점 상세 분석 및 영향도 평가

#### 2.1 ApiKeyService 다중 인스턴스 문제 심화 분석

- [ ] UI Container vs Direct Creation 인스턴스 추적
- [ ] 키 저장/로드 시 사용되는 실제 인스턴스 확인
- [ ] 44bytes vs 34bytes 키 크기 불일치 근본 원인 규명
- [ ] 각 인스턴스별 DB 연결 및 Repository 상태 비교

#### 2.2 필수 서비스별 경합 상황 및 영향도 분석

- [ ] **DB 접근 경합**: 동시 트랜잭션 충돌 및 락 대기 시간 분석
- [ ] **API키 서비스 경합**: 암호화/복호화 프로세스 동시 접근 문제
- [ ] **업비트 REST API 경합**: Rate Limit 위반 및 429 에러 발생 빈도
- [ ] **WebSocket 경합**: 메시지 처리 지연 및 연결 불안정성 분석
- [ ] **Rate Limiter 경합**: 제한 정책 불일치로 인한 API 차단 사례
- [ ] 서비스 간 의존성 체인에서 병목 지점 식별

#### 2.3 시스템 전반 영향도 매핑

- [ ] 기반 서비스 장애 시 영향받는 상위 서비스 식별
- [ ] 데이터 일관성 문제가 전파되는 경로 분석
- [ ] 사용자 체감 영향도 평가 (UI, API 연결, 로그 등)
- [ ] 시스템 안정성 위험 요소 도출
- [ ] 이벤트 루프 블로킹으로 인한 전체 시스템 정지 시나리오 분석

#### 2.4 현재 아키텍처의 구조적 한계 분석

- [ ] DDD + Clean Architecture 위반 사례 식별
- [ ] Singleton 패턴 미적용으로 인한 문제점 정리
- [ ] 의존성 역전 원칙 위반 지점 분석
- [ ] 계층간 결합도 및 응집도 문제 평가
- [ ] 이벤트 기반 아키텍처 부재로 인한 직접 결합 문제

### Phase 3: 개선된 서비스 아키텍처 설계

#### 3.1 통합 이벤트 루프 기반 서비스 풀 설계

- [ ] **중앙화된 서비스 풀 아키텍처**: 단일 이벤트 루프 내에서 모든 필수 서비스 관리
- [ ] **서비스 큐잉 시스템**: DB, API키, REST API, WebSocket, Rate Limiter 요청 순서화
- [ ] **우선순위 기반 스케줄링**: 긴급 요청(익절/손절) vs 일반 요청 구분 처리
- [ ] **서비스 간 메시지 패싱**: 직접 호출 대신 이벤트 기반 통신 체계 구축
- [ ] **백프레셔 제어**: 서비스 과부하 시 요청 제한 및 대기 전략

#### 3.2 통합 서비스 아키텍처 설계

- [ ] 핵심 기반 서비스들의 Singleton 패턴 적용 방안
- [ ] 전역 ServiceLocator vs Container DI 통합 전략
- [ ] 서비스 생명주기 관리 체계 설계
- [ ] 의존성 주입 일관성 보장 방안

#### 3.3 경합 없는 리소스 접근 보장

- [ ] **DB 접근 직렬화**: 트랜잭션 큐잉 및 배치 처리 방식 설계
- [ ] **API키 서비스 원자성**: 암호화/복호화 작업의 Lock-free 구조 설계
- [ ] **업비트 API Rate Limiting**: 통합된 요청 스로틀링 및 백오프 전략
- [ ] **WebSocket 메시지 처리**: 논블로킹 메시지 큐 및 이벤트 디스패처 설계
- [ ] **글로벌 Rate Limiter**: 모든 외부 API 호출 통합 제어 시스템

#### 3.4 동시성 제어 및 Thread Safety 보장

- [ ] 서비스별 동시성 제어 메커니즘 설계
- [ ] 공유 리소스 접근 시 락 전략 수립
- [ ] 트랜잭션 경계 및 격리 수준 최적화
- [ ] 비동기 처리 및 이벤트 기반 아키텍처 고려

#### 3.5 서비스 초기화 및 부트스트랩 설계

- [ ] 애플리케이션 시작 시 서비스 초기화 순서 정의
- [ ] 의존성 해결 및 순환 참조 방지 방안
- [ ] 실패 시 복구 및 Fallback 메커니즘
- [ ] 개발/테스트/프로덕션 환경별 설정 관리
- [ ] 이벤트 루프 기반 서비스 풀 부트스트랩 프로세스

### Phase 4: 점진적 개선 로드맵 수립

#### 4.1 우선순위 기반 개선 계획

- [ ] Critical Path 서비스 (ApiKeyService 등) 우선 개선
- [ ] 단계별 마이그레이션 전략 수립
- [ ] 기존 코드 호환성 보장 방안
- [ ] 리스크 최소화 접근법 정의

#### 4.2 구현 가이드라인 및 표준 정의

- [ ] 새로운 서비스 생성 시 표준 패턴 정의
- [ ] Container 등록 및 DI 사용 가이드라인
- [ ] 테스트 전략 및 Mock 객체 활용 방안
- [ ] 코드 리뷰 체크리스트 및 품질 기준

---

## 🛠️ 분석할 도구 및 방법론

### 📊 **코드 분석 도구**

- `instance_tracker.py`: 인스턴스 생성 지점 및 생명주기 추적
- `dependency_mapper.py`: 의존성 그래프 시각화 도구
- `concurrency_detector.py`: 동시 접근 및 Race Condition 감지
- `service_health_checker.py`: 서비스 상태 및 일관성 검증
- `event_loop_analyzer.py`: 이벤트 루프 내 서비스 요청 흐름 분석
- `service_contention_monitor.py`: 서비스별 경합 및 대기 시간 측정
- `rate_limit_compliance_checker.py`: Rate Limiter 정책 준수 및 위반 감지

### 🔍 **분석 방법론**

- **정적 분석**: 코드 구조 및 패턴 분석
- **동적 분석**: 런타임 인스턴스 추적 및 로깅
- **아키텍처 리뷰**: DDD/Clean Architecture 관점 평가
- **성능 분석**: 메모리 사용량 및 응답 시간 측정
- **이벤트 루프 분석**: 비동기 작업 큐 상태 및 처리 순서 추적
- **경합 상황 시뮬레이션**: 고부하 상황에서 서비스 안정성 테스트

---

## 🎯 성공 기준

### 기술적 검증

- ✅ **인스턴스 통합**: 각 기반 서비스당 단일 인스턴스 보장
- ✅ **데이터 일관성**: 44bytes 저장 → 44bytes 로드 (일치성 보장)
- ✅ **동시성 안전**: Race Condition 및 트랜잭션 충돌 제거
- ✅ **의존성 일관성**: 모든 서비스가 Container DI를 통해 주입

### 아키텍처 품질

- ✅ **DDD 준수**: 계층별 의존성 방향 올바름
- ✅ **SOLID 원칙**: 단일 책임, 의존성 역전 등 준수
- ✅ **확장성**: 새로운 서비스 추가 시 표준 패턴 적용 가능
- ✅ **테스트 용이성**: Mock 및 테스트 더블 적용 가능

### 운영 안정성

- ✅ **시스템 안정성**: 서비스 장애 시 격리 및 복구 가능
- ✅ **성능 최적화**: 불필요한 인스턴스 생성 제거
- ✅ **메모리 효율성**: 리소스 누수 및 중복 방지
- ✅ **모니터링**: 서비스 상태 실시간 추적 가능

---

## 💡 작업 시 주의사항

### 안전성 원칙

- **점진적 개선**: 한 번에 하나의 서비스만 변경
- **호환성 보장**: 기존 API 및 인터페이스 유지
- **롤백 준비**: 각 단계별 롤백 계획 수립
- **테스트 우선**: 변경 전후 동작 검증 필수

### 품질 확보

- **아키텍처 일관성**: DDD + Clean Architecture 원칙 준수
- **코드 품질**: SOLID 원칙 및 디자인 패턴 적용
- **문서화**: 설계 결정사항 및 변경 이유 명확히 기록
- **팀 공유**: 아키텍처 변경사항 팀 리뷰 및 승인

### 성능 고려

- **메모리 최적화**: Singleton 패턴으로 메모리 사용량 최적화
- **초기화 시간**: 애플리케이션 시작 시간 단축
- **런타임 효율성**: 서비스 조회 및 호출 성능 최적화
- **리소스 관리**: DB 연결, 파일 핸들 등 리소스 효율적 관리

---

## 🚀 즉시 시작할 작업

### 1단계: 현재 상황 긴급 진단

```powershell
# 필수 서비스 인스턴스 생성 지점 전면 추적
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String "ApiKeyService\(" -n
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String "DatabaseManager\(" -n
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String "UpbitRestApi\|UpbitClient" -n
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String "WebSocketManager\|WebSocket" -n
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String "RateLimiter\|rate_limiter" -n

# 이벤트 루프 및 비동기 처리 패턴 분석
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String "asyncio\|QAsync\|async def" -n

# 동시 접근 가능 지점 식별
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String "save_key\|load_key\|execute_order\|connect\|send_message" -n
```

### 2단계: 이벤트 루프 기반 서비스 통합 현황 조사

```python
# event_loop_service_analyzer.py 개발
# - 현재 이벤트 루프 사용 패턴 분석
# - 서비스별 요청 큐잉 메커니즘 조사
# - 경합 발생 지점 및 빈도 측정

# service_contention_monitor.py 개발
# - DB 트랜잭션 대기 시간 측정
# - API Rate Limit 위반 모니터링
# - WebSocket 메시지 처리 지연 추적
```

### 3단계: 통합 서비스 풀 요구사항 도출

- **이벤트 루프 기반 서비스 풀**: 단일 스레드 내 모든 필수 서비스 관리
- **큐 기반 요청 처리**: FIFO/우선순위 큐를 통한 경합 제거
- **백프레셔 제어**: 과부하 시 요청 제한 및 대기 전략
- **서비스 간 메시지 패싱**: 직접 호출 대신 이벤트 기반 통신
- **통합된 Rate Limiting**: 모든 외부 API 호출 중앙 제어

---

## 🔗 연관 태스크

### 선행 태스크

- **TASK_20250929_01**: 올바른 Container 사용법 적용 (완료)
- **현재 Container 접근 패턴 분석**: 이미 수행된 분석 결과 활용

### 후속 태스크 (예정)

- **TASK_20250930_02**: 통합 이벤트 루프 기반 서비스 풀 구현
- **TASK_20250930_03**: ApiKeyService 통합 및 Singleton 적용
- **TASK_20250930_04**: DatabaseManager 트랜잭션 큐잉 시스템 구축
- **TASK_20250930_05**: 업비트 REST API 통합 Rate Limiter 적용
- **TASK_20250930_06**: WebSocket 메시지 처리 최적화
- **TASK_20250930_07**: 전역 서비스 아키텍처 마이그레이션
- **TASK_20250930_08**: 동시성 제어 및 Thread Safety 강화

### 종속성

- **높음**: 모든 후속 기능 개발이 이 태스크 결과에 의존
- **영향**: 시스템 전반 안정성, 데이터 일관성, 성능 최적화
- **우선순위**: 🔥 최우선 (시스템 기반 안정성 및 확장성 확보)
- **핵심 가치**: 이벤트 루프 기반 통합으로 요청 경합 원천 차단

---

**다음 에이전트 시작점**:

1. **이벤트 루프 기반 통합 진단**: 현재 비동기 처리 및 서비스 큐잉 메커니즘 전면 분석
2. **필수 서비스 경합 현황 조사**: DB, API키, REST API, WebSocket, Rate Limiter 동시 접근 패턴
3. **통합 서비스 풀 요구사항 도출**: 단일 이벤트 루프 내 경합 없는 서비스 제공 아키텍처
4. **ApiKeyService 다중 인스턴스 문제**: 44bytes vs 34bytes 키 크기 불일치 근본 원인 규명
5. **Container DI vs 직접 생성** 패턴 혼재 현황 정확한 매핑 및 통합 방안
6. **성능 최적화 로드맵**: 요청 경합 제거를 통한 시스템 전반 성능 향상 계획

---

**문서 유형**: 🏗️ 시스템 기반 아키텍처 연구
**우선순위**: 🔥 최우선 (시스템 안정성 핵심)
**예상 소요 시간**: 2-3일 (분석 2일 + 설계안 1일)
**성공 기준**: 통합된 서비스 아키텍처 설계안 및 개선 로드맵 완성
