# 🏗️ DDD 계층 구조 + 금지사항 가이드
*최종 업데이트: 2025년 8월 10일*

## ⚡ 의존성 방향 (절대 규칙)
```
🎨 Presentation → ⚙️ Application → 💎 Domain ← 🔧 Infrastructure
     ↓              ↓              ↑           ↑
   View/MVP      Use Cases      Business    Repository
                                 Logic       Impl
```

**핵심**: Domain이 중심이며, 다른 계층을 참조하지 않음

---

## 📁 계층별 위치 + 역할 + 금지사항

### 🎨 Presentation Layer
**📂 위치**: `upbit_auto_trading/ui/desktop/`, `upbit_auto_trading/presentation/`
- **✅ 역할**: UI 표시, 사용자 입력 수집, View 업데이트
- **✅ 허용**: Use Case 호출, View Interface 구현, MVP 패턴
- **✅ 적용된 패턴**: Settings MVP 100% 완성 (ApiSettingsView, DatabaseSettingsView, NotificationSettingsView, UISettingsView)
- **❌ 금지**: SQLite 직접 사용, 파일시스템 접근, 비즈니스 로직, print 문 사용
- **🔧 로깅**: Infrastructure logging `create_component_logger()` 필수 사용

### ⚙️ Application Layer
**📂 위치**: `upbit_auto_trading/application/`
- **✅ 역할**: Use Case 조율, DTO 변환, 트랜잭션 관리
- **✅ 허용**: Domain Service + Repository Interface만
- **❌ 금지**: SQLite, HTTP, 구체적 기술 스택, UI 참조, print 문 사용
- **🔧 로깅**: Infrastructure logging `create_component_logger()` 필수 사용

### 💎 Domain Layer
**📂 위치**: `upbit_auto_trading/domain/`
- **✅ 역할**: 순수 비즈니스 로직, Entity, Value Object, Domain Service
- **✅ 허용**: 자체 Entity, Value Object, Service, Repository Interface만
- **❌ 금지**: 다른 계층 import 절대 금지, SQLite, HTTP, UI, print 문 사용
- **🔧 로깅**: Infrastructure logging `create_component_logger()` 필수 사용

### 🔧 Infrastructure Layer
**📂 위치**: `upbit_auto_trading/infrastructure/`
- **✅ 역할**: 외부 시스템 연동, Repository 구현, DB 접근
- **✅ 허용**: SQLite, API, 파일시스템, Domain Entity 변환
- **✅ 완성된 시스템**: 로깅 시스템 (create_component_logger), Repository Container
- **❌ 금지**: Domain 로직 포함, UI 로직, print 문 사용
- **🔧 로깅**: Infrastructure logging `create_component_logger()` 필수 사용

---

## 🚨 자주 위반하는 패턴들 (즉시 차단!)

### ❌ 절대 금지된 코드

#### 1. Presenter에서 SQLite 직접 사용 (계층 위반!)
```python
# ❌ 절대 금지!
class BadPresenter:
    def method(self):
        import sqlite3  # 금지!
        conn = sqlite3.connect("db.sqlite3")
        cursor = conn.execute("SELECT * FROM strategies")

        print("데이터 로드 중...")  # 금지! Infrastructure 로깅 사용 필수
```

#### 2. Domain에서 다른 계층 import (의존성 위반!)
```python
# ❌ 절대 금지!
from upbit_auto_trading.infrastructure.database import SomeRepo  # 금지!
from upbit_auto_trading.ui.desktop import SomeWidget  # 금지!

def domain_method():
    print("처리 중...")  # 금지! Infrastructure 로깅 사용 필수
```

#### 3. Application에서 UI 직접 조작 (책임 위반!)
```python
# ❌ 절대 금지!
class BadUseCase:
    def execute(self):
        widget.setText("완료")  # UI 직접 조작 금지!
        print("작업 완료")  # 금지! Infrastructure 로깅 사용 필수
```

#### 4. 호환성 alias 사용 (투명성 위반!)
```python
# ❌ 절대 금지!
from upbit_auto_trading.ui.desktop.screens.settings import ApiSettingsView as ApiSettings  # alias 금지!
# __init__.py에서 alias 제공도 금지!
```

### ✅ 올바른 코드 패턴

#### 1. Presenter는 Use Case만 호출 + Infrastructure 로깅
```python
# ✅ 올바른 패턴
from upbit_auto_trading.infrastructure.logging import create_component_logger

class GoodPresenter:
    def __init__(self, use_case):
        self.use_case = use_case
        self.logger = create_component_logger("GoodPresenter")

    def method(self):
        self.logger.info("작업 시작")
        result = self.use_case.execute(request_dto)
        self.view.update_display(result)
        self.logger.info("작업 완료")
```

#### 2. Domain은 순수 로직만 + Infrastructure 로깅
```python
# ✅ 올바른 패턴
from upbit_auto_trading.infrastructure.logging import create_component_logger

class GoodDomainService:
    def __init__(self, repo: AbstractRepo):  # 인터페이스만
        self.repo = repo
        self.logger = create_component_logger("GoodDomainService")

    def validate_strategy(self, strategy):
        self.logger.debug("전략 검증 시작")
        # 순수 비즈니스 로직만
        is_valid = strategy.is_valid()
        self.logger.info(f"전략 검증 결과: {is_valid}")
        return is_valid
```

#### 3. Infrastructure는 Domain Interface 구현 + 직접 import
```python
# ✅ 올바른 패턴
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.ui.desktop.screens.settings.api_settings import ApiSettingsView  # 직접 import
from upbit_auto_trading.ui.desktop.screens.settings.database_settings import DatabaseSettingsView

class GoodRepository(IStrategyRepository):  # Interface 구현
    def __init__(self):
        self.logger = create_component_logger("GoodRepository")

    def save(self, strategy: Strategy):
        self.logger.info("전략 저장 시작")
        # Domain Entity → Database 변환
        record = self._to_database_record(strategy)
        # SQLite 저장 (Infrastructure만 허용)
        self.db.save(record)
        self.logger.info("전략 저장 완료")
```

---

## 🔍 계층 위반 즉시 체크 방법

### 🔧 자동 검증 명령어
```powershell
# Domain Layer에 외부 의존성 있는지 확인 (결과 없어야 정상)
grep -r "import sqlite3" upbit_auto_trading/domain/
grep -r "import requests" upbit_auto_trading/domain/
grep -r "from PyQt6" upbit_auto_trading/domain/

# Presenter에 SQLite 직접 사용 있는지 확인 (결과 없어야 정상)
grep -r "import sqlite3" upbit_auto_trading/ui/
grep -r "sqlite3.connect" upbit_auto_trading/presentation/

# print 문 사용 확인 (결과 없어야 정상 - Infrastructure 로깅 사용 필수)
grep -r "print(" upbit_auto_trading/ --exclude-dir=tests --exclude-dir=tools

# 호환성 alias 사용 확인 (결과 없어야 정상)
grep -r "import.*as.*View" upbit_auto_trading/ui/
grep -r "__all__.*alias" upbit_auto_trading/
```

### 📋 파일별 점검 체크리스트
#### Domain Layer 파일 점검
- [ ] `import` 문에 infrastructure, ui, application 없음
- [ ] SQLite, HTTP, 파일시스템 관련 코드 없음
- [ ] 순수 비즈니스 로직만 포함
- [ ] `print` 문 없음 (Infrastructure 로깅 사용)

#### Presenter 파일 점검
- [ ] Use Case 호출만 있음
- [ ] SQLite 직접 접근 없음
- [ ] 복잡한 비즈니스 계산 없음
- [ ] `print` 문 없음 (Infrastructure 로깅 사용)
- [ ] 직접 import 사용 (호환성 alias 금지)

#### Use Case 파일 점검
- [ ] Domain Service + Repository Interface만 의존
- [ ] UI 위젯 직접 조작 없음
- [ ] 구체적 기술 스택 참조 없음
- [ ] `print` 문 없음 (Infrastructure 로깅 사용)

---

## 🛠️ 올바른 개발 순서 (Bottom-Up)

### 1단계: Domain Layer 먼저
```python
# 1. Entity, Value Object 정의
class Strategy(Entity):
    def validate(self) -> bool:
        # 비즈니스 로직

# 2. Repository Interface 정의
class IStrategyRepository(ABC):
    def save(self, strategy: Strategy) -> None:
        pass
```

### 2단계: Infrastructure Layer
```python
# 3. Repository 구현체
class SqliteStrategyRepository(IStrategyRepository):
    def save(self, strategy: Strategy) -> None:
        # SQLite 저장 로직
```

### 3단계: Application Layer
```python
# 4. Use Case 구현
class CreateStrategyUseCase:
    def __init__(self, repo: IStrategyRepository):
        self.repo = repo

    def execute(self, request: CreateStrategyDto) -> ResponseDto:
        # Domain Entity 생성 + Repository 호출
```

### 4단계: Presentation Layer
```python
# 5. Presenter 구현
class StrategyPresenter:
    def __init__(self, use_case: CreateStrategyUseCase):
        self.use_case = use_case

    def create_strategy(self):
        result = self.use_case.execute(dto)
        self.view.show_result(result)
```

---

## 🎯 핵심 원칙 요약

### ✅ 허용되는 의존성
- **Presentation** → Application (Use Case 호출)
- **Application** → Domain (Service, Repository Interface)
- **Infrastructure** → Domain (Entity 변환, Interface 구현)

### ❌ 금지되는 의존성
- **Domain** → 다른 모든 계층 (절대 금지!)
- **Presentation** → Infrastructure (Repository 직접 사용 금지)
- **Application** → Infrastructure (구체 구현 의존 금지)

### 💡 계층 위반 시 해결책
1. **Domain 위반** → 해당 로직을 적절한 계층으로 이동
2. **Presenter 위반** → Use Case 생성 후 위임
3. **Use Case 위반** → Repository Interface로 추상화

---

**🔥 기억할 것**: 의심스러우면 Domain Layer가 다른 계층을 import하고 있는지 먼저 확인!

**⚡ 빠른 검증**: `python run_desktop_ui.py` 실행해서 오류 없으면 계층 구조 정상!
