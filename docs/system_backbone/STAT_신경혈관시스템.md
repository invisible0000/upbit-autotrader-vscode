# STAT_신경혈관시스템

**목적**: Infrastructure 외 계층의 신경계/혈관계 구성요소 현황
**분량**: 156줄 / 200줄 (78% 사용)
**성격**: 백본이 아닌 비즈니스 조정자들의 상태 분석

---

## 🎯 **핵심 현황 (1-20줄: 즉시 파악)**

### **신경계/혈관계 정의**
- **신경계**: 비즈니스 로직의 흐름을 제어하는 Domain Services
- **혈관계**: 계층 간 데이터와 명령을 전달하는 Application 조정자들
- **UI 접점**: 사용자와 시스템을 연결하는 Presentation 인터페이스

### **계층별 분포**
- **Domain Layer**: 19개 순수 비즈니스 서비스 (신경계)
- **Application Layer**: 23개 조정/오케스트레이션 (혈관계)
- **UI Layer**: 2개 인터페이스 관리 (접점)

### **Infrastructure와의 차이점**
- Infrastructure: 기술적 백본 (뼈대와 근육)
- 신경/혈관: 비즈니스 흐름 제어 (두뇌와 순환계)

---

## 🧠 **Domain Layer 신경계 (21-50줄: 맥락)**

### **핵심 비즈니스 서비스 (19개)**
```yaml
전략 관리 신경계:
- StrategySimulationService: 전략 시뮬레이션 제어
- StrategyCompatibilityService: 전략 호환성 검증
- NormalizationService: 데이터 정규화 로직

트리거 제어 신경계:
- ChangeDetectionService: 변화 감지 알고리즘
- ConditionPreviewService: 조건 미리보기 로직
- ConditionValidationService: 조건 검증 엔진
- VariableCompatibilityService: 변수 호환성 체크

설정 관리 신경계:
- PathConfigurationService: 경로 설정 로직
- UnifiedConfigService: 통합 설정 관리

알림 제어:
- NotificationManager: 알림 정책 관리
```

### **Repository 인터페이스 (순수 계약)**
```yaml
데이터 접근 계약:
- ITradingVariableRepository: 매매 변수 저장 규칙
- IConditionRepository: 조건 저장 규칙
- IStrategySimulationDataRepository: 시뮬레이션 데이터 규칙
- BacktestRepository: 백테스트 데이터 규칙
- MarketDataRepository: 시장 데이터 규칙

특징: Infrastructure에서 구현, Domain에서 계약만 정의
```

---

## 🩸 **Application Layer 혈관계 (51-100줄: 상세)**

### **Use Case 오케스트레이션 (중추 혈관)**
```yaml
전략 관리 플로우:
- 전략 생성/수정/삭제 Use Case
- 백테스트 실행 Use Case
- 시뮬레이션 관리 Use Case

설정 관리 플로우:
- 프로필 변경 Use Case
- 환경 설정 Use Case
- API 키 관리 Use Case
```

### **Event Handling System (신경 신호 전달)**
```yaml
이벤트 핸들러 (23개):
전략 이벤트:
- StrategyCreatedHandler: 전략 생성 후처리
- StrategyUpdatedHandler: 전략 변경 후처리
- TriggerCreatedHandler: 트리거 생성 후처리

백테스트 이벤트:
- BacktestStartedHandler: 백테스트 시작 처리
- BacktestCompletedHandler: 백테스트 완료 처리
- BacktestFailedHandler: 백테스트 실패 처리
- BacktestProgressUpdatedHandler: 진행상황 처리

캐시 무효화:
- CacheInvalidationHandler: 캐시 갱신 신호
- EventHandlerRegistry: 이벤트 라우팅 중추
```

### **Query System (정보 순환 혈관)**
```yaml
쿼리 처리기:
- DashboardQueryHandler: 대시보드 정보 조회
- StrategyListQueryHandler: 전략 목록 조회
- StrategyDetailQueryHandler: 전략 상세 조회

서비스 컨테이너:
- ApplicationServiceContainer: 서비스 생명주기 관리
- QueryServiceContainer: 쿼리 서비스 조정
- QueryService: 쿼리 라우팅 총괄
```

### **Notification System (알림 혈관)**
```yaml
알림 전달 체계:
- NotificationService: 알림 전달 조정
- 다양한 알림 채널 관리
- 사용자별 알림 설정 반영
```

---

## 🖥️ **UI Layer 접점 시스템 (101-150줄: 실행)**

### **최소한의 UI 인프라 (2개)**
```yaml
스타일 관리:
- StyleManager: 전역 UI 테마 관리
- 다크/라이트 모드 전환
- 일관된 UI 스타일 보장

보안 인터페이스:
- ApiKeyManagerSecure: API 키 보안 인터페이스 (Legacy)
- 사용자 인증 및 키 관리 UI
```

### **특징: Passive View 패턴**
```yaml
UI 철학:
- View는 순수 표시만 담당
- Presenter가 모든 로직 처리
- Application Layer와만 통신
- Infrastructure 직접 접근 금지
```

### **MVP 패턴 준수**
```yaml
계층 분리:
View (PyQt6 위젯) → Presenter → Application Service → Domain
각 계층은 다음 계층과만 통신 (건너뛰기 금지)
```

---

## 🔄 **신경/혈관 상호작용 (151-156줄: 연결)**

### **정보 흐름 패턴**
```
사용자 입력 → UI → Application → Domain 신경계
                ↓
           Event 발생 → Event Handler 혈관계
                ↓
           Infrastructure 백본 → 실제 처리
```

### **관련 문서**
- `STAT_백본15개현황.md` - Infrastructure 백본 현황
- `STAT_현재시스템현황.md` - 전체 시스템 상태

**역할**: Infrastructure 백본을 **제어하고 조정**하는 시스템의 신경계/혈관계 🧠🩸
