# 📋 서비스 의존성 주입 패턴 가이드
>
> API Settings Factory에서 검증된 ApplicationServiceContainer 기반 DI 패턴

## 🎯 의존성 주입 아키텍처

### 계층별 의존성 방향

```
Presentation → Application → Infrastructure
     ↓              ↓             ↓
   Factory    → Container   →  Repository
```

## 🔧 ApplicationServiceContainer 활용 패턴

### 1. Factory에서 Container 접근

```python
class ComponentFactory(BaseComponentFactory):
    def create_component_instance(self, parent, **kwargs):
        # ✅ 표준 Container 접근 패턴
        app_container = self._get_application_container()

        # ✅ 서비스 주입 with 오류 처리
        service = self._get_service(
            app_container.get_service_name, "ServiceName"
        )
```

### 2. 사용 가능한 서비스들

#### Infrastructure 서비스 (Repository 기반)

- `get_api_key_service()`: API 키 관리 (SecureKeysRepository)
- `get_database_service()`: DB 연결 관리 (DatabaseConnectionService)
- `get_settings_service()`: 설정 관리 (SettingsService)

#### Application 서비스 (비즈니스 로직)

- `get_logging_service()`: 애플리케이션 로깅 (ApplicationLoggingService)
- `get_component_lifecycle_service()`: 컴포넌트 생명주기 관리
- `get_settings_validation_service()`: 설정 유효성 검증

#### Domain 서비스 (도메인 로직)

- `get_notification_service()`: 알림 관리
- `get_strategy_service()`: 전략 관리
- `get_trigger_service()`: 트리거 관리

### 3. 서비스 주입 검증 패턴

```python
# ✅ 안전한 서비스 주입
def _get_service(self, service_getter, service_name: str):
    service = service_getter()
    if service is None:
        raise RuntimeError(f"{service_name} 서비스 로드 실패 - 시스템 중단")
    return service

# 사용 예시
api_key_service = self._get_service(
    app_container.get_api_key_service, "ApiKey"
)
```

## 🏗️ MVP에서의 의존성 흐름

### Factory → Presenter (생성 시점)

```python
presenter = ComponentPresenter(
    view=view,                    # View 의존성
    service=injected_service,     # Model(Service) 의존성
    logging_service=logger        # Infrastructure 의존성
)
```

### Presenter → Service (런타임)

```python
def save_data(self, data):
    # Presenter에서 Service 호출
    result = self.service.save(data)

    # 결과에 따른 View 업데이트
    if result:
        self.view.show_success("저장 완료")
    else:
        self.view.show_error("저장 실패")
```

### Service → Repository (데이터 영속화)

```python
def save(self, data):
    # Service에서 Repository 호출
    success = self.repository.save(data)

    # Repository에서 명시적 커밋 (중요!)
    # conn.commit() 필수

    return success
```

## 🚨 중요한 주의사항

### 1. Repository 트랜잭션 관리

```python
# ❌ 잘못된 패턴 (커밋 누락)
with self.db.get_connection() as conn:
    cursor.execute("INSERT ...")
    return True  # 실제로는 저장 안됨

# ✅ 올바른 패턴 (명시적 커밋)
with self.db.get_connection() as conn:
    cursor.execute("INSERT ...")
    conn.commit()  # 필수!
    return True
```

### 2. 서비스 초기화 검증

```python
# ✅ 서비스 None 체크
if self.service is None:
    self.logger.warning("⚠️ Service가 None으로 전달됨")
    return default_behavior()
```

### 3. Infrastructure 로깅

```python
# ✅ 컴포넌트별 로거 사용
self.logger = logging_service.get_component_logger("ComponentName")
self.logger.info("✅ 초기화 완료")

# ❌ print() 사용 금지
print("초기화 완료")  # Golden Rules 위반
```

## 📊 성공 지표

### API Settings Factory 검증 결과

- ✅ **실제 API 연동**: 업비트 서버 연결 성공 (37,443원 KRW)
- ✅ **데이터 무결성**: DB 트랜잭션 커밋 완전 동작
- ✅ **MVP 패턴**: Factory → View → Presenter → Model 완전 플로우
- ✅ **DI 컨테이너**: ApplicationServiceContainer 기반 완벽 주입

### 재사용 가능성

이 패턴을 적용하면:

- 🔧 Database Settings Factory
- 🎨 UI Settings Factory
- 📢 Notification Settings Factory
- 🌍 Environment Profile Factory

모든 Factory에서 동일한 품질의 MVP 구현이 보장됩니다.

---

**TASK_20250929_02에서 검증 완료된 실전 패턴입니다.**
