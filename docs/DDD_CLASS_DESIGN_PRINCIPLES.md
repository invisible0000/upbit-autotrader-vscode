# 🏗️ DDD 기반 클래스 설계 원칙 가이드

## 📋 클래스 설계 결정 기준

### 🔹 데이터클래스 (`@dataclass`) 사용

#### ✅ 필수 사용 대상
1. **값 객체 (Value Objects)**
   ```python
   @dataclass(frozen=True)
   class StrategyId:
       value: str
   ```
   - `frozen=True` 필수 (불변성)
   - 비즈니스 규칙 검증
   - 동등성 기반 비교

2. **데이터 전송 객체 (DTOs)**
   ```python
   @dataclass(frozen=True)
   class StrategyDto:
       strategy_id: str
       name: str
   ```

3. **순수 데이터 컨테이너**
   - 행위(메서드)가 최소한
   - 데이터 저장/접근만 담당

#### ⚠️ 제약사항
- **기본값 필드는 항상 뒤에** 배치
- 상속 시 자식에서 필수 필드 추가 불가

### 🔹 일반 클래스 (`class`) 사용

#### ✅ 필수 사용 대상
1. **도메인 엔티티** (dataclass + 비즈니스 로직)
   ```python
   @dataclass  # frozen=False
   class Strategy:
       strategy_id: StrategyId
       name: str
       is_active: bool = True  # 기본값 필드는 뒤로
       
       def add_rule(self, rule):  # 비즈니스 행위
           pass
   ```

2. **상속 기본 클래스**
   ```python
   class DomainEvent(ABC):  # 일반 클래스
       def __init__(self):
           self._event_id = str(uuid.uuid4())
   ```
   - 자식에서 필수 필드 자유롭게 정의 가능

3. **도메인 서비스/Repository**
   ```python
   class StrategyService:  # 일반 클래스
       def validate_strategy(self, strategy):
           pass
   ```

## 🎯 도메인 이벤트 설계 패턴

### 기본 클래스: 일반 클래스
```python
class DomainEvent(ABC):
    def __init__(self):
        self._event_id = str(uuid.uuid4())
        self._occurred_at = datetime.now()
```

### 구체적 이벤트: 일반 클래스
```python
class StrategyCreated(DomainEvent):
    def __init__(self, strategy_id: str, strategy_name: str, 
                 created_by: str = "system"):
        super().__init__()
        self.strategy_id = strategy_id      # 필수
        self.strategy_name = strategy_name  # 필수
        self.created_by = created_by        # 기본값
```

## 🚨 엄격 준수 규칙

1. **값 객체**: 반드시 `@dataclass(frozen=True)`
2. **도메인 이벤트**: 반드시 일반 클래스
3. **엔티티**: `@dataclass` + 비즈니스 메서드
4. **필드 순서**: 기본값 없는 필드 → 기본값 있는 필드
5. **상속 클래스**: 자식에서 필수 필드 추가 시 일반 클래스 사용

## 💡 LLM 에이전트 개발 가이드

### 새 클래스 생성 시 체크리스트
- [ ] 값 객체인가? → `@dataclass(frozen=True)`
- [ ] 도메인 이벤트인가? → 일반 클래스
- [ ] 상속하는 클래스인가? → 필드 순서 확인
- [ ] 엔티티인가? → `@dataclass` + 비즈니스 메서드

### 필드 순서 규칙
```python
# ✅ 올바른 순서
@dataclass
class Example:
    required_field: str           # 필수 필드 먼저
    optional_field: str = "default"  # 기본값 필드 나중

# ❌ 잘못된 순서
@dataclass  
class Example:
    optional_field: str = "default"  # 기본값 필드 먼저 (오류!)
    required_field: str               # 필수 필드 나중
```

---
**원칙**: 느리게 가는 것이 빠른 것. 기본 규칙을 철저히 지켜서 품질 높은 코드 작성.
