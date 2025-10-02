# 📋 DI 컨테이너 일관성 개선 제안

## 🎯 현재 문제: 의존성 제공 패턴의 불일치

### 🚨 **발견된 불일치 패턴들**

#### **패턴 A: Service 래핑 방식**

```python
# Infrastructure Services (중간 래핑 레이어)
api_key_service = providers.Factory("ApiKeyService", ...)
theme_service = providers.Factory("ThemeService", ...)
orderbook_data_service = providers.Factory("OrderbookDataService", ...)
```

#### **패턴 B: 직접 Client 방식**

```python
# Direct Client Access (바로 제공)
upbit_public_client = providers.Singleton("UpbitPublicClient")
upbit_private_client = providers.Factory("UpbitPrivateClient")
websocket_client = providers.Singleton("WebSocketClient")
```

### 😵 **문제점들**

1. **일관성 부족**: 같은 API 관련인데 Service vs Client 패턴이 혼재
2. **중복 레이어**: ApiKeyService → UpbitPrivateClient → HTTP (불필요한 중간 단계)
3. **개발자 혼란**: 어떤 패턴을 사용해야 할지 기준 불명확
4. **성능 오버헤드**: 불필요한 래핑으로 인한 함수 호출 체인

---

## 💡 **일관된 규칙 제안**

### **📏 Service vs Client 결정 기준**

#### **✅ Service 래핑이 필요한 경우**

```python
복잡도 체크리스트:
□ 3개 이상의 의존성 조합 필요
□ 복잡한 비즈니스 로직 포함
□ 상태 관리 또는 캐싱 필요
□ 에러 처리/재시도 로직 필요
□ 여러 Client 통합 필요
□ 이벤트 발행/구독 처리
```

**예시:**

```python
# ✅ Service 래핑 정당화됨
orderbook_data_service = providers.Factory(
    "OrderbookDataService",
    websocket_client=websocket_client,      # 의존성 1
    rest_client=upbit_public_client,        # 의존성 2
    event_bus=event_bus,                    # 의존성 3
    cache_service=cache_service             # 의존성 4
    # 🎯 복잡한 WebSocket + REST 통합 + 이벤트 + 캐싱
)
```

#### **✅ 직접 Client 제공이 적절한 경우**

```python
단순함 체크리스트:
□ 단순 API 호출만 담당
□ 상태 없는 순수 함수적 동작
□ 표준 인터페이스 제공
□ 1-2개 의존성만 필요
□ 추가 비즈니스 로직 불필요
```

**예시:**

```python
# ✅ 직접 Client 제공 정당화됨
upbit_public_client = providers.Singleton("UpbitPublicClient")
upbit_private_client = providers.Factory("UpbitPrivateClient",
                                        api_key_service=api_key_service)
websocket_client = providers.Singleton("WebSocketClient")
# 🎯 단순 API 호출만, 복잡한 로직 없음
```

---

## 🔧 **개선된 DI 컨테이너 구조**

### **Infrastructure Layer Container 재구성**

```python
class ExternalDependencyContainer(DeclarativeContainer):
    """외부 의존성 컨테이너 - 일관된 패턴 적용"""

    # =============================================================================
    # 📁 직접 Client 제공 (단순 API 접근)
    # =============================================================================

    # Database Clients (단순 연결)
    database_connection_service = providers.Singleton("DatabaseConnectionService")

    # API Clients (단순 HTTP 요청)
    upbit_public_client = providers.Singleton("UpbitPublicClient")
    upbit_private_client = providers.Factory("UpbitPrivateClient",
                                           access_key=config.upbit.access_key,
                                           secret_key=config.upbit.secret_key)

    # WebSocket Clients (단순 연결)
    websocket_client = providers.Singleton("WebSocketClient")

    # File System Clients (단순 I/O)
    file_system_service = providers.Singleton("FileSystemService")

    # =============================================================================
    # 🏭 Service 래핑 제공 (복잡한 비즈니스 로직)
    # =============================================================================

    # 복잡한 인증/보안 처리
    api_key_service = providers.Factory(
        "ApiKeyService",
        secure_repository=secure_keys_repository,    # 의존성 1
        encryption_service=encryption_service,       # 의존성 2
        upbit_client=upbit_private_client           # 의존성 3
        # 🎯 보안 + 저장 + 검증 + API 테스트 통합
    )

    # 복잡한 데이터 통합
    orderbook_data_service = providers.Factory(
        "OrderbookDataService",
        websocket_client=websocket_client,          # 의존성 1
        rest_client=upbit_public_client,            # 의존성 2
        event_bus=event_bus,                        # 의존성 3
        cache_service=cache_service                 # 의존성 4
        # 🎯 실시간 + REST + 이벤트 + 캐싱 통합
    )

    # 복잡한 설정 관리 (Application Layer로 이동 권장)
    # settings_service → application/services/settings_application_service.py
```

---

## 📊 **기존 서비스들의 재분류**

### **🔄 Service → Client 변경 권장**

| 현재 서비스 | 복잡도 | 권장 조치 | 이유 |
|-------------|--------|-----------|------|
| api_key_service | 중간 | Service 유지 | 보안+저장+검증 통합 |
| theme_service | 낮음 | Application으로 이동 | UI 비즈니스 로직 |
| settings_service | 낮음 | Application으로 이동 | 사용자 워크플로우 |

### **✅ Client 직접 제공으로 단순화**

```python
# 현재 (불필요한 래핑)
some_service = providers.Factory("SomeService", client=some_client)

# 개선 (직접 제공)
some_client = providers.Factory("SomeClient", config=config)
```

---

## 🎯 **개발자 가이드라인**

### **🤔 "Service vs Client" 결정 플로우차트**

```
새로운 의존성이 필요하다면?
    ↓
단순 API 호출만 하나?
    ↓ Yes                    ↓ No
직접 Client 제공         복잡한 로직 있나?
    ↓                        ↓ Yes              ↓ No
providers.Factory(          Service 래핑        Client 재검토
  "SomeClient")               ↓                   ↓
                        providers.Factory(    혹시 잘못 분류?
                          "SomeService",
                          dependencies...)
```

### **📋 체크리스트**

#### **Client 직접 제공 체크리스트**

- [ ] 단순 CRUD 또는 API 호출만 수행
- [ ] 비즈니스 로직 없음
- [ ] 의존성 2개 이하
- [ ] 상태 관리 불필요
- [ ] 표준 인터페이스 제공

#### **Service 래핑 체크리스트**

- [ ] 복잡한 비즈니스 로직 포함
- [ ] 3개 이상 의존성 통합
- [ ] 상태 관리 또는 캐싱 필요
- [ ] 에러 처리/재시도 로직
- [ ] 이벤트 발행/구독 처리

---

## 🚀 **마이그레이션 계획**

### **Phase 1: 명확한 Client들 (즉시 적용)**

```python
# 즉시 직접 제공으로 변경
upbit_public_client = providers.Singleton("UpbitPublicClient")
upbit_private_client = providers.Factory("UpbitPrivateClient")
database_connection_service = providers.Singleton("DatabaseConnectionService")
file_system_service = providers.Singleton("FileSystemService")
```

### **Phase 2: 경계선 Service들 (재검토)**

```python
# 복잡도 재평가 후 결정
api_key_service = ?  # 복잡한 보안 로직 → Service 유지
orderbook_data_service = ?  # 복잡한 통합 → Service 유지
```

### **Phase 3: 부적절한 Service들 (레이어 이동)**

```python
# Application Layer로 이동
settings_service → application/services/settings_application_service.py
theme_service → application/services/ui_theme_service.py
```

---

## 💡 **기대 효과**

1. **일관성**: 명확한 기준으로 Service vs Client 결정
2. **단순성**: 불필요한 래핑 레이어 제거
3. **성능**: 함수 호출 체인 단축
4. **유지보수**: 개발자가 패턴 선택에 고민할 시간 감소
5. **확장성**: 새 컴포넌트 추가시 일관된 기준 적용

---

> **🎯 핵심 원칙**: "단순한 것은 단순하게, 복잡한 것만 Service로!"
