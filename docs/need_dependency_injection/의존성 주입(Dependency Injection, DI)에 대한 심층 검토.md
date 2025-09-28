# **의존성 주입(Dependency Injection, DI)에 대한 심층 검토**

---

## **의존성 주입(DI) 도입 필요성 검토**

### **1. 의존성 주입(DI)이란 무엇인가? (비유를 통한 이해)**

의존성 주입을 이해하기 위해 '요리사'와 '주방'의 비유를 들어보겠습니다.

* **DI가 없는 경우 (나쁜 예):** 요리사(객체)가 특정 요리(기능)를 할 때마다 직접 농장(외부 API), 정육점(DB), 가게(설정 파일)에 가서 필요한 모든 재료(의존성)를 구해옵니다. 만약 정육점이 문을 닫거나 농장의 위치가 바뀌면, 요리사는 직접 새로운 곳을 찾아 헤매야 합니다. 이는 매우 비효율적이고 변경에 취약합니다.
* **DI가 있는 경우 (좋은 예):** 주방장(DI 컨테이너)이 존재합니다. 요리사는 "스테이크를 만들려니 소고기와 소금이 필요합니다"라고 주방장에게 요청만 하면 됩니다. 그러면 주방장은 가장 신선한 소고기를 공급하는 정육점과 최고급 소금을 가진 가게를 이미 알고 있어, 해당 재료들을 요리사에게 즉시 가져다줍니다. 요리사는 재료를 어디서 구해야 할지 신경 쓸 필요 없이 오직 요리에만 집중할 수 있습니다.

이처럼, **의존성 주입(DI)은 객체가 필요로 하는 다른 객체(의존성)를 직접 만들거나 찾지 않고, 외부(DI 컨테이너)에서 전달받는 프로그래밍 기법**입니다. 이를 통해 객체들은 서로에게 느슨하게 연결(Loosely Coupled)되어 유연하고 확장 가능한 구조를 만들 수 있습니다.

### **2. 현재 프로젝트 코드의 문제점 진단**

현재 `upbit-autotrader-vscode` 프로젝트는 빠른 기능 구현과 프로토타이핑을 거치며 규모가 상당히 커졌습니다. 이 과정에서 몇 가지 구조적인 문제점이 발생했으며, 이는 향후 유지보수와 기능 확장을 어렵게 만들 수 있습니다.

#### **문제점 1: 강한 결합(Tight Coupling)으로 인한 경직된 구조**

많은 클래스들이 자신이 필요로 하는 다른 클래스의 인스턴스를 직접 생성하고 있습니다.

**예시 코드 (가상):**

```python
# upbit_auto_trading/ui/desktop/screens/chart_view/chart_view_screen.py (나쁜 예시)

from upbit_auto_trading.application.services.chart_data_service import ChartDataService

class ChartViewScreen:
    def __init__(self):
        # ChartDataService 인스턴스를 직접 생성하여 강한 결합 발생
        self.chart_data_service = ChartDataService()

    def load_chart_data(self, market):
        data = self.chart_data_service.get_data(market)
        # ... 데이터로 차트 그리기 ...
```

위 코드에서 `ChartViewScreen`은 `ChartDataService`가 어떻게 생성되는지 구체적인 내용을 알아야 합니다. 만약 `ChartDataService`의 생성자가 변경되거나 (예: 설정 객체가 필요해짐) 다른 종류의 `ChartDataService`로 교체해야 할 경우, `ChartViewScreen` 클래스의 코드를 직접 수정해야만 합니다. 프로젝트 전반에 이런 코드가 흩어져 있다면, 작은 변경 하나가 연쇄적인 코드 수정을 유발하는 '지옥'이 펼쳐질 수 있습니다.

#### **문제점 2: 테스트의 어려움**

단위 테스트(Unit Test)의 핵심은 특정 기능(단위)을 다른 부분과 격리하여 독립적으로 테스트하는 것입니다. 하지만 위와 같이 의존성을 직접 생성하는 구조에서는 `ChartDataService`를 가짜(Mock) 객체로 대체하기가 매우 어렵습니다.

결과적으로 `ChartViewScreen`을 테스트할 때마다 실제 데이터베이스나 외부 API와 통신하는 `ChartDataService`가 함께 동작하게 됩니다. 이는 다음과 같은 문제를 야기합니다.

* **느린 테스트 속도:** 실제 네트워크나 DB I/O는 테스트 속도를 현저히 저하시킵니다.
* **외부 환경 의존성:** API 서버가 불안정하거나 DB 연결이 끊기면 테스트가 실패합니다.
* **예측 불가능성:** 외부 데이터는 계속 변하므로 일관된 테스트 결과를 얻기 어렵습니다.

#### **문제점 3: 중앙 관리의 부재와 코드의 복잡성 증가**

프로젝트가 커지면서 어떤 객체들이 존재하고, 이들이 서로 어떻게 연결되어 있는지 파악하기가 점점 어려워집니다. 각 파일에서 개별적으로 객체를 생성하고 관리하기 때문에 전체적인 시스템의 구조를 한눈에 파악할 수 없습니다.

* **설정 변경의 어려움:** 데이터베이스 연결 정보나 API 클라이언트의 타임아웃 설정 등을 변경하려면, 해당 설정을 사용하는 모든 클래스를 일일이 찾아 수정해야 할 수 있습니다.
* **객체 생명주기 관리의 어려움:** 애플리케이션 전체에서 단 하나만 존재해야 하는 객체(싱글턴, Singleton)를 보장하기 어렵고, 불필요한 객체가 계속 생성되어 메모리 낭비를 유발할 수 있습니다.

### **3. 결론: 왜 의존성 주입이 시급한가?**

`ROADMAP.md` 문서에 언급된 바와 같이, DI 시스템 도입은 '긴급 심층 검토'가 필요한 과제입니다. 그 이유는 현재 겪고 있는 구조적 문제들이 프로젝트의 성장을 저해하는 심각한 기술 부채(Technical Debt)로 작용하기 때문입니다.

의존성 주입 시스템을 전면적으로 도입하면 다음과 같은 효과를 기대할 수 있습니다.

1. **유연성 및 확장성 확보:** 객체 간의 결합도를 낮춰 새로운 기능을 추가하거나 기존 기능을 변경할 때 다른 코드에 미치는 영향을 최소화할 수 있습니다.
2. **테스트 가능한 코드:** 의존성을 쉽게 교체할 수 있게 되어, 빠르고 안정적인 단위 테스트 작성이 가능해집니다. 이는 코드 품질을 높이고 버그를 사전에 방지하는 데 결정적인 역할을 합니다.
3. **중앙화된 관리:** 모든 객체의 생성과 연결(의존성 관계)이 DI 컨테이너 한 곳에서 관리되므로, 시스템의 전체 구조를 이해하기 쉽고 설정을 변경하기도 용이해집니다.
4. **개발 생산성 향상:** 개발자는 자신이 개발하는 기능의 핵심 로직에만 집중할 수 있습니다. 필요한 의존성은 DI 컨테이너에 요청하기만 하면 되므로, 반복적인 객체 생성 코드를 작성할 필요가 없습니다.

따라서, 지금 시점에서 의존성 주입 원칙을 프로젝트 전반에 체계적으로 적용하는 것은 더 건강하고 지속 가능한 프로젝트로 나아가기 위한 필수적인 선택입니다

---

## **의존성 주입 패턴 검토 및 프로젝트 적용 방안**

### **1. 대표적인 의존성 주입(DI) 패턴**

의존성을 주입하는 방식에는 크게 세 가지 패턴이 있습니다. 각 패턴의 특징을 이해하고 우리 프로젝트에 가장 적합한 방식을 선택하는 것이 중요합니다.

#### **1) 생성자 주입 (Constructor Injection)**

* **방식:** 클래스의 생성자(`__init__`)를 통해 의존성을 주입받습니다. 객체가 생성되는 시점에 필요한 모든 의존성이 전달됩니다.
* **장점:**
  * **명확성:** 객체를 생성하기 위해 무엇이 필요한지 생성자 시그니처만 봐도 명확하게 알 수 있습니다.
  * **의존성 불변성 보장:** 객체가 한번 생성된 후에는 의존성이 변경될 가능성이 없어, 예측 가능하고 안정적인 상태를 유지할 수 있습니다.
  * **필수 의존성 누락 방지:** 객체 생성 시점에 필요한 의존성이 없으면 인스턴스화 자체가 불가능하므로, 런타임 오류를 조기에 방지할 수 있습니다.
* **단점:**
  * 의존성이 너무 많아지면 생성자 코드가 길어질 수 있습니다. (하지만 이는 해당 클래스가 너무 많은 책임을 지고 있다는 '코드 스멜(Code Smell)'일 수 있습니다.)

**예시 코드:**

```python
class ChartViewPresenter:
    def __init__(self, chart_data_service: IChartDataService, notification_service: INotificationService):
        self._chart_data_service = chart_data_service
        self._notification_service = notification_service
```

#### **2) 세터 주입 (Setter Injection) / 속성 주입 (Property Injection)**

* **방식:** 객체가 생성된 후, 세터(setter) 메서드나 공개 속성(property)을 통해 의존성을 주입합니다.
* **장점:**
  * **선택적 의존성:** 필수가 아닌 선택적인 의존성을 주입할 때 유용합니다.
  * **의존성 변경 가능:** 런타임에 의존성을 다른 구현체로 교체해야 하는 경우 사용할 수 있습니다.
* **단점:**
  * **객체의 불완전한 상태:** 객체가 생성된 후 의존성이 주입되기 전까지는 불완전한 상태일 수 있습니다.
  * **의존성 누락 가능성:** 개발자가 세터를 호출하는 것을 잊으면 `NullPointerException`(Python에서는 `AttributeError`)이 발생할 수 있습니다.
  * **숨겨진 의존성:** 클래스 내부 코드를 보지 않으면 어떤 의존성이 필요한지 파악하기 어렵습니다.

**예시 코드:**

```python
class ChartViewPresenter:
    def __init__(self):
        self._chart_data_service = None
        self._notification_service = None

    def set_chart_data_service(self, service: IChartDataService):
        self._chart_data_service = service

    @property
    def notification_service(self) -> INotificationService:
        return self._notification_service

    @notification_service.setter
    def notification_service(self, service: INotificationService):
        self._notification_service = service
```

#### **3) 메서드 주입 (Method Injection)**

* **방식:** 의존성이 필요한 특정 메서드를 호출할 때 파라미터로 직접 전달받습니다.
* **장점:**
  * **일시적인 의존성:** 클래스 전체가 아닌 특정 메서드에서만 일시적으로 필요한 의존성을 처리하기에 적합합니다.
* **단점:**
  * 동일한 의존성을 여러 메서드에서 필요로 할 경우, 반복적으로 파라미터를 전달해야 해서 코드가 번거로워집니다.

**예시 코드:**

```python
class ReportGenerator:
    def generate_daily_report(self, data_exporter: IDataExporter):
        # ... 리포트 데이터 생성 ...
        data_exporter.export(report_data)
```

### **2. 프로젝트 현황 분석 및 최적 패턴 선정**

#### **현재 프로젝트의 DI 라이브러리: `dependency-injector`**

이미 프로젝트 내 `upbit_auto_trading/infrastructure/dependency_injection/container.py` 파일에서 `dependency-injector` 라이브러리를 사용하고 있습니다. 이 라이브러리는 파이썬에서 의존성 주입을 매우 효율적으로 관리할 수 있도록 도와주는 강력한 도구입니다. 따라서 새로운 패턴을 발명하기보다는, 이 라이브러리의 기능을 최대한 활용하여 **생성자 주입(Constructor Injection) 패턴**을 프로젝트의 표준으로 채택하는 것을 권장합니다.

#### **왜 생성자 주입 패턴인가?**

1. **안정성과 예측 가능성:** `upbit-autotrader-vscode`는 금융 데이터를 다루는 프로그램이므로, 시스템의 안정성과 예측 가능성이 매우 중요합니다. 생성자 주입은 객체가 생성될 때 모든 의존성이 완벽하게 준비되도록 보장하여, '의존성이 아직 설정되지 않은' 불안정한 상태를 원천적으로 차단합니다.
2. **명시적인 의존성 관리:** 클래스의 `__init__` 메서드만 보면 이 클래스가 어떤 다른 구성 요소들과 협력하는지 명확하게 드러납니다. 이는 코드의 가독성을 높이고, 비개발자 출신이라도 Copilot의 도움을 받아 클래스의 역할을 파악하는 데 큰 도움이 됩니다.
3. **dependency-injector와의 최적의 조합:** `dependency-injector` 라이브러리는 생성자 주입 패턴을 매우 간결하고 강력하게 지원합니다. `@inject` 데코레이터를 사용하면 컨테이너에 정의된 의존성을 자동으로 생성자에 주입해 주어, 보일러플레이트 코드를 획기적으로 줄일 수 있습니다.

#### **`dependency-injector`를 활용한 생성자 주입 표준안**

**1. 컨테이너 정의 (container.py):**

* 모든 서비스, 리포지토리, 클라이언트 등은 `Container` 클래스 내에 `providers`를 사용하여 정의합니다.
* **`providers.Singleton`**: 애플리케이션 전체에서 유일한 인스턴스를 유지해야 하는 경우 사용합니다. (예: `DatabaseManager`, `UpbitPublicClient`)
* **`providers.Factory`**: 호출할 때마다 새로운 인스턴스를 생성해야 하는 경우 사용합니다. (예: 특정 데이터를 담는 `Presenter`)

```python

# upbit_auto_trading/infrastructure/dependency_injection/container.py (예시)

from dependency_injector import containers, providers
from upbit_auto_trading.application.services import ChartDataService
from upbit_auto_trading.infrastructure.repositories import SqliteCandleRepository

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Infrastructure Layer
    candle_repository = providers.Singleton(
        SqliteCandleRepository,
        db_path=config.database.market_data_path
    )

    # Application Layer
    chart_data_service = providers.Factory(
        ChartDataService,
        candle_repository=candle_repository
    )
```

**2. 의존성 주입 대상 클래스 (`@inject` 사용):**

* 의존성이 필요한 클래스의 `__init__` 메서드 위에`@inject` 데코레이터를 붙여줍니다.
* 타입 힌팅을 사용하여 어떤 의존성이 필요한지 명시합니다.

```python
# upbit_auto_trading/ui/desktop/screens/chart_view/chart_view_screen.py (개선된 예시)

from dependency_injector.wiring import inject, Provide
from ...application.services.chart_data_service import ChartDataService
from ...infrastructure.dependency_injection.container import Container

class ChartViewScreen:
    @inject
    def __init__(self, chart_data_service: ChartDataService = Provide[Container.chart_data_service]):
        self.chart_data_service = chart_data_service
        # ... UI 초기화 ...

    def load_chart_data(self, market):
        data = self.chart_data_service.get_data(market)
        # ...
```

**3. 애플리케이션 진입점 (`run_desktop_ui.py`) 에서의 설정:**

* 애플리케이션 시작 시 컨테이너를 생성하고, 설정 파일을 로드하며, 의존성을 주입할 모듈들을 지정(wire)합니다.

```python
# run_desktop_ui.py (예시)

from upbit_auto_trading.infrastructure.dependency_injection.container import Container
from upbit_auto_trading.ui.desktop import main_window, screens

def main():
    container = Container()
    container.config.from_yaml('config/config.yaml')
    # 의존성 주입이 필요한 모듈들을 지정
    container.wire(modules=[__name__, main_window, screens])

    app = QApplication(sys.argv)
    # 컨테이너를 통해 MainWindow 인스턴스 생성
    main_win = container.main_window()
    main_win.show()
    sys.exit(app.exec())
```

### **3. 결론**

프로젝트의 안정성, 확장성, 테스트 용이성을 극대화하기 위해, **`dependency-injector` 라이브러리를 활용한 생성자 주입(Constructor Injection) 패턴**을 프로젝트의 공식적인 의존성 주입 표준으로 선정합니다.

이는 이미 도입된 기술을 효과적으로 활용하는 방안이며, 코드의 품질을 한 단계 높이는 중요한 결정이 될 것입니다. 다음 문서에서는 이 패턴을 어떤 파일과 기능에 구체적으로 적용할지에 대한 가이드를 제공합니다

---

## **의존성 주입(DI) 적용 가이드**

이 문서는 `upbit-autotrader-vscode` 프로젝트 내에서 의존성 주입을 일관되게 적용하기 위한 구체적인 지침을 제공합니다.

### **1. DI 적용의 핵심 원칙**

1. **"스스로 만들지 말고, 외부에서 받아라 (Don't create, ask for it)"**
   * 클래스 내부에서 `MyService()`와 같이 다른 클래스의 인스턴스를 직접 생성하지 않습니다.
   * 필요한 객체는 생성자(`__init__`)의 파라미터로 받도록 설계합니다.
2. **"구체적인 것 대신 추상적인 것에 의존하라 (Depend on abstractions, not concretions)"**
   * (이상적으로) 구체적인 클래스(`SqliteCandleRepository`)보다는 추상 베이스 클래스(ABC)나 프로토콜(`ICandleRepository`)에 의존하는 것이 좋습니다. 이는 의존성을 다른 구현체로 쉽게 교체할 수 있게 해줍니다.
   * *현실적인 적용:* 현재 프로젝트에서는 인터페이스(`ABC`)가 많지 않으므로, 우선은 구체 클래스를 주입받되, 향후 리팩토링 시 추상화를 도입하는 것을 목표로 합니다.
3. **"DI 컨테이너는 조립 설명서다 (The DI Container is the assembly manual)"**
   * 객체를 생성하고 서로 연결하는 모든 로직은 `dependency-injector` 컨테이너(`container.py`)에 집중시킵니다.
   * 애플리케이션의 다른 부분에서는 컨테이너에서 최상위 객체를 가져와 사용하기만 하면 됩니다.

### **2. DI 적용 대상 선정 가이드**

모든 클래스에 DI를 적용할 필요는 없습니다. 아래 가이드에 따라 DI가 필요한 대상을 식별합니다.

#### **반드시 DI를 적용해야 하는 대상 (Inject These)**

* **서비스 (Services):** `upbit_auto_trading/application/services/`
  * **이유:** 비즈니스 로직을 수행하며, 주로 리포지토리나 다른 서비스, API 클라이언트 등 여러 의존성을 조합하여 사용합니다.
  * **예시:** `StrategyApplicationService`는 `IStrategyRepository`, `ITriggerRepository` 등을 주입받아야 합니다.
* **리포지토리 (Repositories):** `upbit_auto_trading/infrastructure/repositories/`, `upbit_auto_trading/infrastructure/persistence/`
  * **이유:** 데이터 영속성(저장/조회)을 담당하며, `DatabaseManager`나 설정(DB 경로 등)과 같은 인프라스트럭처 구성 요소에 의존합니다.
  * **예시:** `SqliteStrategyRepository`는 `DatabaseManager`를 주입받아 데이터베이스와 상호작용합니다.
* **외부 API 클라이언트 (External API Clients):** `upbit_auto_trading/infrastructure/external_apis/`
  * **이유:** 외부 시스템과 통신하며, API 키, 요청 제한기(`RateLimiter`), 설정(URL, 타임아웃) 등에 의존합니다.
  * **예시:** `UpbitPrivateClient`는 `ApiKeyService`와 `UpbitRateLimiter`를 주입받아야 합니다.
* **프레젠터 및 UI 이벤트 핸들러 (Presenters & UI Event Handlers):** `upbit_auto_trading/presentation/presenters/`, `upbit_auto_trading/ui/desktop/screens/`
  * **이유:** 사용자 인터페이스의 이벤트를 받아 처리하고, 비즈니스 로직을 수행하기 위해 애플리케이션 서비스에 의존합니다.
  * **예시:** `MainWindowPresenter`는 `ScreenManagerService`, `WindowStateService` 등을 주입받아야 합니다.

#### **DI 적용이 필요 없는 대상 (Don't Inject These)**

* **데이터 전송 객체 (DTOs):** `upbit_auto_trading/application/dto/`
  * **이유:** 계층 간 데이터를 전달하기 위한 단순한 데이터 구조체입니다. 로직을 거의 갖지 않으며, 의존성이 없습니다. 필요할 때마다 직접 생성하여 사용합니다.
* **도메인 엔티티 및 값 객체 (Domain Entities & Value Objects):** `upbit_auto_trading/domain/entities/`, `upbit_auto_trading/domain/value_objects/`
  * **이유:** 도메인의 핵심 개념과 규칙을 표현하는 객체입니다. 서비스나 리포지토리에 의해 생성되고 관리되며, 직접 주입받는 대상이 아닙니다.
  * **예시:** `Strategy` 객체는 `StrategyRepository`가 DB에서 데이터를 읽어 생성하거나, 사용자가 입력한 값으로 `StrategyFactory`가 생성합니다.
* **유틸리티 클래스 (Utility Classes):** `upbit_auto_trading/infrastructure/utilities/`
  * **이유:** 대부분 상태 없이 정적 메서드(또는 클래스 메서드)만으로 구성된 경우가 많습니다.
  * **예시:** `TimeUtils`는 의존성 없이 시간 관련 유틸리티 함수만 제공하므로 주입할 필요가 없습니다.

### **3. 단계별 DI 적용 방법 (Step-by-Step)**

`ChartDataService`를 `ChartViewScreen`에 주입하는 과정을 예시로 설명합니다.

**1단계: 의존성 식별 및 생성자 변경 (Identify & Modify Constructor)**

* **Before:** `ChartViewScreen`이 `ChartDataService`를 직접 생성합니다.

```python
  # upbit_auto_trading/ui/desktop/screens/chart_view/chart_view_screen.py

  class ChartViewScreen(QWidget):
      def **init**(self, parent=None):
          super().**init**(parent)
          self.chart_data_service = ChartDataService() # <- 문제점!
```

* **After:** 생성자를 통해 `ChartDataService`를 받도록 변경하고, `@inject` 데코레이터를 추가합니다.

```python
  # upbit_auto_trading/ui/desktop/screens/chart_view/chart_view_screen.py

  from dependency_injector.wiring import inject, Provide
  from ...application.services.chart_data_service import ChartDataService
  from ...infrastructure.dependency_injection.container import Container

  class ChartViewScreen(QWidget):
      @inject
      def **init**(
          self,
          chart_data_service: ChartDataService = Provide[Container.chart_data_service],
          parent=None
      ):
          super().**init**(parent)
          self.chart_data_service = chart_data_service # <- 주입 받음!
          # ...
```

**2단계: 컨테이너에 의존성 등록 (Register Dependencies in Container)**

* `upbit_auto_trading/infrastructure/dependency_injection/container.py` 파일에 `ChartDataService`와 그것이 필요로 하는 `SqliteCandleRepository`를 등록합니다.

```python
  # upbit_auto_trading/infrastructure/dependency_injection/container.py

  from dependency_injector import containers, providers

  # ... 다른 import

  from ..repositories.sqlite_candle_repository import SqliteCandleRepository
  from ...application.services.chart_data_service import ChartDataService

  class Container(containers.DeclarativeContainer):
      config = providers.Configuration()

      # Repository 등록
      candle_repository = providers.Singleton(
          SqliteCandleRepository,
          db_path=config.database.market_data_db.path # 설정값에서 DB 경로 주입
      )

      # Service 등록 (candle_repository를 주입)
      chart_data_service = providers.Factory(
          ChartDataService,
          candle_repository=candle_repository
      )
      # ...
```

**3단계: 컨테이너에 UI 모듈 연결 (Wire Modules)**

* 애플리케이션 진입점(`run_desktop_ui.py`)에서 `@inject`를 사용할 모듈을 `container.wire()`에 추가합니다. `screens` 패키지 전체를 지정할 수 있습니다.

```python
  # run_desktop_ui.py

  from upbit_auto_trading.infrastructure.dependency_injection.container import Container
  from upbit_auto_trading.ui.desktop import screens # screens 모듈 import

  def main():
      container = Container()
      # ... 설정 로드 ...

      # screens 모듈에 의존성 주입을 활성화
      container.wire(modules=[screens])

      # ... 애플리케이션 실행 ...
```

**4단계: 객체 생성 (Object Creation)**

* 이제 `ChartViewScreen` 객체를 생성할 때, DI 컨테이너가 자동으로 `ChartDataService` 인스턴스를 생성하고 그 의존성인 `SqliteCandleRepository`까지 생성하여 주입해 줍니다. 개발자는 더 이상 객체 생성 순서나 의존성 관계를 신경 쓸 필요가 없습니다.

이 가이드를 따라 프로젝트 전반에 걸쳐 DI를 일관되게 적용하면, 코드의 구조가 훨씬 명확해지고 유연해질 것입니다

---

## **비개발자 및 Copilot 사용자를 위한 의존성 주입(DI) 현황 및 가이드**

안녕하세요! 이 문서는 개발 경험이 많지 않으시거나, GitHub Copilot과 같은 AI 도우미와 함께 '바이브 코딩'을 하시는 분들을 위해 작성되었습니다. 어려운 기술 용어 대신, 최대한 쉽고 직관적으로 우리 프로젝트의 **의존성 주입(DI)** 시스템에 대해 설명해 드립니다.

### **1. DI, 우리 프로젝트의 '스마트 만능 부품 상자'**

"의존성 주입"이라는 말이 조금 어렵게 들릴 수 있습니다. 간단하게 **'부품 조립 시스템'** 이라고 생각해 보세요.

우리가 만드는 자동매매 프로그램은 자동차와 같습니다. 자동차에는 엔진, 바퀴, 핸들, 네비게이션 등 수많은 부품(코드 조각, 클래스)이 필요하죠.

* **예전 방식 (DI가 없었을 때):**
  * '핸들' 부품을 만들 때, 핸들 제작자가 직접 '바퀴 공장'에 가서 바퀴를 만들어와야 합니다.
  * '네비게이션' 부품을 만들 때도, 제작자가 직접 '지도 회사'와 'GPS 위성'에 연결해야 합니다.
  * **문제점:** 모든 부품이 다른 부품을 만드는 방법까지 알아야 해서 너무 복잡하고, '바퀴 공장'이 이사가면 핸들 제작자가 직접 새 주소를 찾아 코드를 고쳐야 했습니다.
* **새로운 방식 (DI 도입 후):**
  * 우리에겐 **'만능 부품 상자(DI 컨테이너)'** 가 생겼습니다. 이 상자는 모든 부품을 만들고 관리하는 방법을 알고 있습니다.
  * 이제 '핸들' 제작자는 "바퀴가 필요해!"라고 외치기만 하면, 부품 상자가 알아서 최신형 바퀴를 가져다줍니다.
  * '네비게이션' 제작자도 "지도랑 GPS 신호 줘!"라고 요청만 하면 됩니다.
  * **장점:** 각 부품 제작자(개발자)는 자신의 전문 분야(핸들, 네비게이션)에만 집중할 수 있습니다. 부품 조립은 '만능 부품 상자'가 전부 알아서 해주니까요!

**핵심:** 의존성 주입(DI)은 **필요한 부품(코드)을 직접 만들지 않고, '만능 부품 상자'에게 달라고 요청하는 방식**입니다.

### **2. 우리 프로젝트의 '만능 부품 상자'는 어디에 있나요?**

우리 프로젝트의 '만능 부품 상자' 역할을 하는 파일은 바로 이것입니다.

* **upbit_auto_trading/infrastructure/dependency_injection/container.py**

이 파일이 바로 우리 프로그램의 모든 핵심 부품(서비스, 데이터베이스 연결, API 통신 등)을 어떻게 만들고 서로 연결할지에 대한 '설계도'이자 '조립 설명서'입니다.

### **3. 현재 상황은 어떤가요?**

* **좋은 소식:** 우리는 이미 dependency-injector라는 아주 좋은 '부품 상자' 라이브러리를 사용하기 시작했습니다.
* **개선할 점:** 아직 모든 부품이 이 '부품 상자'를 사용하고 있지는 않습니다. 어떤 부품은 여전히 예전 방식대로 직접 다른 부품을 만들고 있어, 코드가 뒤섞여 있습니다.
* 우리의 목표 (TASK_20250927_01-di_system_completion.md):
  프로젝트의 모든 중요한 부품들이 이 '만능 부품 상자'를 통해서만 조립되도록 규칙을 통일하는 것입니다. 이렇게 하면 코드가 훨씬 깨끗해지고, 나중에 새로운 기능을 추가하거나 수정하기가 매우 쉬워집니다.

### **4. Copilot과 함께 '바이브 코딩'할 때 이것만 기억하세요!**

새로운 기능을 추가하거나 기존 코드를 수정할 때, 아래의 간단한 규칙을 따르면 됩니다.

**"새로운 클래스(부품)를 만들 때, 그 안에서 다른 클래스를 직접 부르지 마세요."**

**예를 들어,** '실시간 알림' 기능을 만드는 NotificationService 클래스를 만든다고 가정해 봅시다. 이 서비스는 '업비트 API'에서 정보를 가져와야 합니다.

* **이렇게 하지 마세요 (나쁜 예 ❌):**

```python
  from ..external_apis.upbit.upbit_public_client import UpbitPublicClient

  class NotificationService:
      def __init__(self):
          # 클래스 안에서 직접 다른 클래스를 생성! (나쁨)
          self.upbit_client = UpbitPublicClient()

      def send_price_alert(self, market):
          price = self.upbit_client.get_current_price(market)
          print(f"[{market}] 현재가: {price}원")
```

* **이렇게 하세요 (좋은 예 ✅):**

```python
  **1. 필요한 부품을 __init__에서 달라고 요청하세요 (생성자 주입).**
  # 1. 필요한 부품(upbit_client)을 생성자에서 '주세요'라고 선언합니다.
  class NotificationService:
      def __init__(self, upbit_client: UpbitPublicClient):
          self.upbit_client = upbit_client

      def send_price_alert(self, market):
          price = self.upbit_client.get_current_price(market)
          print(f"[{market}] 현재가: {price}원")

  **2. '만능 부품 상자'(container.py)에 새 부품을 등록하세요.**
  # upbit_auto_trading/infrastructure/dependency_injection/container.py
  class Container(containers.DeclarativeContainer):
      # ... 기존 코드 ...

      # 2. '만능 부품 상자'에 NotificationService를 만드는 방법을 알려줍니다.
      # "NotificationService는 upbit_public_client가 필요하구나!"
      notification_service = providers.Factory(
          NotificationService,
          upbit_client=upbit_public_client
      )
```

이제 끝입니다! 이렇게만 하면, 코드가 훨씬 더 유연해지고 테스트하기 쉬워집니다. Copilot에게 "Create a service class with constructor injection for dependencies" 라고 요청하면 이런 구조의 코드를 더 쉽게 얻을 수 있습니다.

이 시스템에 익숙해지시면, 복잡한 기능도 레고 블록을 조립하듯 쉽고 재미있게 구현하실 수 있을 겁니다. 궁금한 점이 있다면 언제든지 다시 질문해 주세요!
