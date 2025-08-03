# 🔄 데이터 흐름 및 요청 처리

> **목적**: 사용자 요청부터 응답까지 데이터 흐름 이해  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-03

## 📊 전체 데이터 흐름

```
👤 사용자 → 🎨 View → 🎭 Presenter → ⚙️ Service → 💎 Domain → 🔌 Repository → 🗄️ DB
     ↖         ↖        ↖         ↖        ↖        ↖         ↖
      ←---------←--------←---------←--------←--------←---------← 응답
```

**흐름 방향**: 요청은 왼쪽→오른쪽, 응답은 오른쪽→왼쪽

## 🎯 실제 예시: "새 트리거 생성"

### 1단계: 🎨 View (사용자 입력)
```python
class TriggerBuilderView(QWidget):
    def on_create_clicked(self):
        # ✅ 입력 수집
        data = {
            'variable_id': 'RSI',
            'operator': '>',
            'target_value': '70',
            'parameters': {'period': 14}
        }
        
        # ✅ 기본 검증
        if not data['target_value']:
            self.show_error("값을 입력하세요")
            return
            
        # ✅ Presenter 호출
        self.presenter.create_trigger(data)
```

### 2단계: 🎭 Presenter (입력 조율)
```python
class TriggerBuilderPresenter:
    def create_trigger(self, form_data):
        # ✅ Command 객체 생성
        command = CreateTriggerCommand(
            variable_id=form_data['variable_id'],
            operator=form_data['operator'],
            target_value=form_data['target_value']
        )
        
        # ✅ Service 호출
        try:
            result = self.trigger_service.create_trigger(command)
            
            if result.success:
                self.view.show_success("트리거 생성 완료")
                self.view.refresh_trigger_list()
            else:
                self.view.show_error(result.error)
                
        except Exception as e:
            self.view.show_error(f"오류: {e}")
```

### 3단계: ⚙️ Service (Use Case 실행)
```python
class TriggerService:
    def create_trigger(self, command):
        # ✅ 트랜잭션 시작
        with self.unit_of_work:
            
            # ✅ 검증 (Application 레벨)
            if not self._user_can_create_trigger(command.user_id):
                return Result.fail("권한이 없습니다")
            
            # ✅ Domain 객체 생성
            trigger = Trigger.create(
                command.variable_id,
                command.operator,
                command.target_value
            )
            
            # ✅ 저장 (Infrastructure 위임)
            self.trigger_repo.save(trigger)
            
            # ✅ 이벤트 발행
            self.event_publisher.publish(TriggerCreated(trigger.id))
            
            # ✅ 트랜잭션 커밋
            self.unit_of_work.commit()
            
        return Result.success(TriggerDto.from_entity(trigger))
```

### 4단계: 💎 Domain (비즈니스 로직)
```python
class Trigger:
    @classmethod
    def create(cls, variable_id, operator, target_value):
        # ✅ 비즈니스 규칙 검증
        if operator not in cls.VALID_OPERATORS:
            raise InvalidOperatorError(f"지원하지 않는 연산자: {operator}")
            
        if not cls._is_valid_target_value(target_value):
            raise InvalidTargetValueError("잘못된 목표값입니다")
        
        # ✅ 도메인 객체 생성
        trigger = cls(
            id=TriggerId.generate(),
            variable_id=variable_id,
            operator=operator,
            target_value=target_value
        )
        
        # ✅ 도메인 이벤트 추가
        trigger.add_event(TriggerCreated(trigger.id))
        
        return trigger
```

### 5단계: 🔌 Repository (데이터 저장)
```python
class SqliteTriggerRepository:
    def save(self, trigger: Trigger):
        # ✅ Domain 객체 → DB 데이터 변환
        data = {
            'id': trigger.id.value,
            'variable_id': trigger.variable_id,
            'operator': trigger.operator,
            'target_value': str(trigger.target_value),
            'created_at': datetime.utcnow().isoformat()
        }
        
        # ✅ DB 저장
        self.db.execute(
            "INSERT INTO triggers (id, variable_id, operator, target_value, created_at) "
            "VALUES (:id, :variable_id, :operator, :target_value, :created_at)",
            data
        )
```

## 🔄 다른 패턴들

### 조회 흐름 (Query)
```
👤 사용자 → 🎨 View → 🎭 Presenter → 📖 QueryHandler → 🔌 Repository → 🗄️ DB
     ↖         ↖        ↖         ↖           ↖         ↖
      ←---------←--------←---------←-----------←---------← DTO
```

```python
# Query Handler 예시
class GetTriggerListQuery:
    def __init__(self, user_id):
        self.user_id = user_id

class GetTriggerListHandler:
    def handle(self, query: GetTriggerListQuery):
        # ✅ 직접 Repository 호출 (Domain 거치지 않음)
        triggers = self.trigger_repo.find_by_user_id(query.user_id)
        
        # ✅ DTO 변환
        trigger_dtos = [TriggerDto.from_entity(t) for t in triggers]
        
        return Result.success(trigger_dtos)
```

### 이벤트 기반 흐름
```
💎 Domain Event → ⚙️ Event Handler → 🔌 External Service
                →                 → 📧 Notification
                →                 → 📊 Analytics
```

```python
# 이벤트 처리 예시
class TriggerCreatedHandler:
    def handle(self, event: TriggerCreated):
        # ✅ 분석 데이터 업데이트
        self.analytics_service.track_trigger_creation(event.trigger_id)
        
        # ✅ 사용자 알림
        self.notification_service.notify_user(
            event.user_id,
            f"새 트리거가 생성되었습니다: {event.trigger_id}"
        )
```

## 🚨 주요 원칙

### 1. 의존성 방향
```python
# ✅ 올바른 의존성 방향
class TriggerService:
    def __init__(self, trigger_repo: TriggerRepository):  # 인터페이스에 의존
        self.trigger_repo = trigger_repo

# ❌ 잘못된 의존성 방향  
class Trigger:
    def save(self):
        repo = SqliteTriggerRepository()  # 구체 클래스에 의존 (금지!)
```

### 2. 데이터 변환 지점
- **Presenter**: View ↔ DTO
- **Service**: DTO ↔ Domain Entity
- **Repository**: Domain Entity ↔ DB Data

### 3. 에러 처리 흐름
```python
# ✅ 계층별 에러 처리
try:
    # Domain에서 예외 발생
    trigger = Trigger.create(invalid_data)
except DomainException as e:
    # Application에서 포착
    return Result.fail(e.message)
except Exception as e:
    # Presenter에서 포착
    self.view.show_error(f"시스템 오류: {e}")
```

## 📊 성능 고려사항

### 1. 지연 로딩 (Lazy Loading)
```python
class Strategy:
    @property
    def triggers(self):
        if not self._triggers_loaded:
            self._triggers = self._trigger_repo.find_by_strategy_id(self.id)
            self._triggers_loaded = True
        return self._triggers
```

### 2. 캐싱 전략
```python
class CachedTriggerRepository:
    def find_by_id(self, trigger_id):
        # ✅ 캐시 확인
        cached = self.cache.get(trigger_id)
        if cached:
            return cached
            
        # ✅ DB 조회 후 캐시 저장
        trigger = self.db_repo.find_by_id(trigger_id)
        self.cache.set(trigger_id, trigger, ttl=300)
        return trigger
```

### 3. 배치 처리
```python
class TriggerBatchService:
    def create_multiple_triggers(self, commands):
        # ✅ 배치로 처리
        triggers = []
        for command in commands:
            trigger = Trigger.create(command.variable_id, command.operator, command.target_value)
            triggers.append(trigger)
            
        # ✅ 한 번에 저장
        self.trigger_repo.save_batch(triggers)
```

## 📚 관련 문서

- [시스템 개요](01_SYSTEM_OVERVIEW.md): 전체 아키텍처
- [계층별 책임](02_LAYER_RESPONSIBILITIES.md): 각 계층 역할
- [기능 개발](04_FEATURE_DEVELOPMENT.md): 실제 개발 가이드

---
**💡 핵심**: "데이터는 계층을 순차적으로 거치며, 각 계층에서 적절히 변환됩니다!"
