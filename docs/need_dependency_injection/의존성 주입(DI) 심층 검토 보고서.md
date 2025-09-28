# 의존성 주입(DI) 심층 검토 보고서

본 문서는 **업비트 자동매매 시스템** 프로젝트의 현재 코드베이스를 분석하여 의존성 주입(DI, *Dependency Injection*)의 필요성, 적용 가능한 패턴, 적용 대상 모듈 선정, 비개발자를 위한 설정 가이드를 정리한 것입니다. 분석 과정에서 여러 국내‧외 자료를 참고하였으며, 일부 핵심 내용을 인용하여 이론적 근거를 제시합니다.

## 1. 필요성 검토

### 1.1 왜 DI가 필요한가?

1. **제어의 역전(IoC)의 구현** – DI 패턴은 클래스와 의존성 간 제어권을 외부 컨테이너에 위임하여 제어의 역전(Inversion of Control)을 달성한다[1](https://bramilch.github.io/posts/kr-python-design-patterns/#:~:text=%EC%9D%98%EC%A1%B4%EC%84%B1%20%EC%A3%BC%EC%9E%85%20%ED%8C%A8%ED%84%B4%20DI%20,Pattern). 클래스 내부에서 의존성을 생성하지 않고 외부에서 제공받기 때문에 클래스 간 결합도가 낮아진다.
2. **느슨한 결합과 모듈화** – 의존성을 외부에서 주입하면 코드가 특정 구현에 묶이지 않으므로 모듈 간 교체가 용이하다. 벨로그 글은 DI의 장점으로 “코드의 재사용성, 유연성이 높아지고 유지보수가 쉬워진다”고 강조한다[2](https://velog.io/%40sana/DI-%EC%9D%98%EC%A1%B4%EC%84%B1-%EC%A3%BC%EC%9E%85Dependency-Injection-%EC%9D%98-%EA%B0%9C%EB%85%90%EA%B3%BC-%EB%B0%A9%EB%B2%95#:~:text=%EC%9D%98%EC%A1%B4%EC%84%B1%20%EC%A3%BC%EC%9E%85%EC%9D%98%20%EC%9E%A5%EC%A0%90).
3. **테스트 용이성** – 의존성을 모킹(Mock), 스텁(Stub) 등 테스트 더블로 교체할 수 있어 단위 테스트가 쉬워진다[3](https://bramilch.github.io/posts/kr-python-design-patterns/#:~:text=,%EC%9E%88%EC%A7%80%20%EC%95%8A%EC%9C%BC%EB%AF%80%EB%A1%9C%20%EC%8B%9C%EC%8A%A4%ED%85%9C%EC%9D%B4%20%EB%8D%94%20%EB%AA%A8%EB%93%88%ED%99%94%EB%90%A8). 현재 코드에서는 전역 싱글턴 객체(예: `database_connection_service`)가 많아 테스트 격리가 어렵다.
4. **대규모 프로젝트의 확장성** – 프로젝트 로드맵에 따르면 REST/웹소켓 클라이언트, 트리거/전략 관리, 백테스트 등 다양한 모듈을 통합할 예정이다. 복잡한 구조에서 **주입기(Injector)**가 없으면 인스턴스 생성과 교체가 어려워지고, 로직이 메인 영역에 집중된다.
5. **비개발자/AI 코파일럿 환경** – GitHub Copilot과 같이 AI 기반 도구로 코딩 시 명시적인 DI 패턴을 따르면 서비스의 경계와 의존성이 코드 구조로 드러나 프로젝트 이해가 쉬워진다.

### 1.2 지금도 DI가 없는가?

현재 코드베이스에는 생성자에서 레포지터리와 서비스를 주입하는 **수동 DI**가 부분적으로 적용되어 있다. 예를 들어 `TriggerApplicationService`는 `TriggerRepository`, `StrategyRepository` 등을 생성자 매개변수로 받는다. 그러나 다음 문제점이 있다:

* **글로벌 싱글턴 사용** – `database_connection_service`나 `get_domain_event_publisher()`는 전역으로 생성되어 어디서든 임포트하여 사용한다. 이는 서비스 로케이터(Service Locator) 패턴에 가깝고, 의존성이 숨겨진다.
* **팩토리/캐시 패턴의 혼재** – `PathServiceFactory`와 같이 인스턴스를 캐싱하는 팩토리가 여러 곳에 흩어져 있다. 이러한 구현은 각 객체가 언제 생성되고 파괴되는지 추적하기 어렵게 만든다.

### 1.3 적용하지 않을 경우의 고려

Socratic question: *“이 프로젝트가 소규모이고 유지보수가 필요 없다면 DI가 필요할까?”*

* 벨로그 글은 간단한 프로그램에서는 DI가 오히려 번거롭고 불필요할 수 있다고 지적한다[4](https://velog.io/%40sana/DI-%EC%9D%98%EC%A1%B4%EC%84%B1-%EC%A3%BC%EC%9E%85Dependency-Injection-%EC%9D%98-%EA%B0%9C%EB%85%90%EA%B3%BC-%EB%B0%A9%EB%B2%95#:~:text=%EC%9D%98%EC%A1%B4%EC%84%B1%20%EC%A3%BC%EC%9E%85%EC%9D%80%20%EA%BC%AD%20%ED%95%84%EC%9A%94%ED%95%9C%EA%B0%80%3F).
* 그러나 본 프로젝트는 데이터베이스, 전략 관리, 백테스트, UI 등 많은 모듈을 통합하는 상용 애플리케이션으로 확장될 예정이다. 개발자 역시 여러 번의 ‘삽질’ 경험을 통해 구조 개선을 진행 중이며, 긴 기간 동안 유지보수를 계획하고 있다.
* 따라서 **초기 비용이 있더라도 DI를 도입하는 것이 장기적으로 생산성 향상에 도움이 될 것**이다.

## 2. DI 패턴 검토 및 선정

의존성을 주입하는 대표적인 방법은 다음과 같다. 각 패턴에 대한 장단점을 검토하고 프로젝트에 적합한 방식과 도구를 제안한다.

### 2.1 생성자 주입(Constructor Injection)

* **개념** – 클래스 생성자에서 의존성을 주입받는 방식이다. 생성자 호출 시 필요한 모든 의존성을 외부에서 전달하므로 객체 상태가 불완전할 위험이 적고, 초기화 시점에 의존성이 주입되지 않으면 컴파일/런타임 오류가 발생한다.
* **장점** – 객체의 불변성이 높아지고, 주입되지 않은 상태로 사용될 위험이 없다. 벨로그 글에서 생성자 주입은 테스트와 교체가 용이하고 OCP를 지킨다고 설명한다[5](https://velog.io/%40tco0427/DIDependency-Injection%EC%99%80-%EC%84%9C%EB%B9%84%EC%8A%A4-%EB%A1%9C%EC%BC%80%EC%9D%B4%ED%84%B0#:~:text=).
* **단점** – 의존성이 많아지면 생성자 시그니처가 길어져 가독성이 떨어질 수 있다.
* **적용 대상** – 도메인 서비스(`PathConfigurationService`, `StrategyCompatibilityService`), 레포지터리(`StrategyCompatibilityService`)와 애플리케이션 서비스(`TriggerApplicationService`, `ChartDataService` 등)에 적합하다. 각 서비스가 의존하는 레포지터리 및 도메인 서비스는 생성자 인자로 전달한다.

### 2.2 세터 주입(Setter Injection)

* **개념** – 공개된 세터 메서드를 통해 의존성을 주입하는 방식이다.
* **장점** – 필수 의존성이 아닌 선택적 의존성을 나중에 설정할 수 있다.
* **단점** – 객체 생성 후 세터를 호출하지 않으면 `NoneType` 에러가 발생할 수 있고, 객체의 불변성이 깨진다. 벨로그 글은 Setter 주입이 NullPointerException을 유발하고 불변성을 해친다고 비판한다[6](https://velog.io/%40tco0427/DIDependency-Injection%EC%99%80-%EC%84%9C%EB%B9%84%EC%8A%A4-%EB%A1%9C%EC%BC%80%EC%9D%B4%ED%84%B0#:~:text=%EB%91%90%EB%B2%88%EC%A7%B8%EB%A1%9C%EB%8A%94%20,%EC%82%AC%EC%9A%A9%ED%95%98%EC%A7%80%20%EC%95%8A%EB%8A%94%20%EC%A3%BC%EC%9E%85%20%EB%B0%A9%EC%8B%9D%EC%9D%B4%EB%8B%A4).
* **프로젝트 의견** – 현재 프로젝트에서는 필수 의존성이 대부분이므로 세터 주입은 지양한다.

### 2.3 인터페이스 주입(Interface Injection)

* **개념** – 의존성을 전달하기 위한 별도의 인터페이스를 구현하여 주입하는 방식이다.
* **장점** – 특정 언어에서 컴파일 타임 검사를 강화할 수 있다.
* **단점** – 파이썬에서는 인터페이스 개념이 약하고 사용 사례가 거의 없다[7](https://bramilch.github.io/posts/kr-python-design-patterns/#:~:text=,%ED%81%B4%EB%9E%98%EC%8A%A4%20%EC%83%9D%EC%84%B1%EC%9E%90%EB%A5%BC%20%ED%86%B5%ED%95%B4%20%EC%9D%98%EC%A1%B4%EC%84%B1%EC%9D%84%20%EC%A0%9C%EA%B3%B5).
* **프로젝트 의견** – 명시적인 인터페이스 주입 대신 추상 클래스나 프로토콜을 정의하고 생성자 주입을 사용한다.

### 2.4 서비스 로케이터(Service Locator) 패턴

* **개념** – 필요한 서비스를 전역 로케이터에서 가져오는 방식이다. 현재 `get_path_service()`나 `database_connection_service` 싱글턴이 이에 해당한다.
* **장점** – 객체 생성 코드가 간단해지고, 특정 상황(순환 의존성 해결 등)에서 유용할 수 있다.
* **단점** – 의존성이 숨겨져 있어 코드가 어떤 서비스를 사용하는지 파악하기 어렵고, 인터페이스 분리 원칙(ISP)을 위반한다. Velog 글은 서비스 로케이터의 단점으로 “동일 타입의 객체가 다수 필요한 경우 중복 메소드가 필요하고, 다른 의존 객체 변경의 영향을 받을 수 있다”고 지적한다[8](https://velog.io/%40tco0427/DIDependency-Injection%EC%99%80-%EC%84%9C%EB%B9%84%EC%8A%A4-%EB%A1%9C%EC%BC%80%EC%9D%B4%ED%84%B0#:~:text=%EC%84%9C%EB%B9%84%EC%8A%A4%20%EB%A1%9C%EC%BC%80%EC%9D%B4%ED%84%B0%EC%9D%98%20%EB%8B%A8%EC%A0%90).
* **프로젝트 의견** – 범용 로케이터는 지양하고, DI 컨테이너 내부에서 제한적으로 사용한다. 순환 의존성이 발생하는 경우에는 Lazy provider를 사용하거나 이벤트 발행 기반으로 분리한다.

### 2.5 DI 컨테이너 (Container)

* **개념** – 객체 생성과 의존성 조립을 담당하는 중앙 컨테이너를 정의하고, 애플리케이션은 컨테이너에서 필요한 인스턴스를 주입받는다.
* **도구** – 파이썬에서는 `dependency-injector` 라이브러리가 성숙되고 생산 준비가 된 프레임워크로 평가된다. 공식 문서에 따르면 컨테이너는 Factory/Singleton/Configuration 등 다양한 provider를 지원하며, provider overriding을 통해 테스트 시 스텁 교체가 용이하다[9](https://python-dependency-injector.ets-labs.org/#:~:text=,injection%20framework%20for%20Python). 또한 설정을 `yaml`, `ini`, `json` 파일이나 환경 변수에서 로딩할 수 있다[10](https://python-dependency-injector.ets-labs.org/#:~:text=,See%20Configuration%20provider).
* **예시** – 다음과 같이 컨테이너를 정의할 수 있다:

```python
from dependency_injector import containers, providers
from upbit_auto_trading.infrastructure.services.database_connection_service import DatabaseConnectionService
from upbit_auto_trading.infrastructure.configuration.path_service_factory import get_path_service
from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
# … 기타 레포지터리 import

class Container(containers.DeclarativeContainer):
    config = providers.Configuration() # 환경 변수/파일을 로딩
    # 인프라 서비스
    path_service = providers.Singleton(get_path_service) # 기존 싱글턴을 provider로 래핑
    db_service = providers.Singleton(DatabaseConnectionService)
    # 레포지터리
    strategy_repo = providers.Singleton(StrategyRepository, db_service=db_service)
    trigger_repo = providers.Singleton(TriggerRepository, db_service=db_service)
    settings_repo = providers.Singleton(SettingsRepository, db_service=db_service)
    # 도메인 서비스
    compatibility_service = providers.Singleton(StrategyCompatibilityService)
    # 애플리케이션 서비스
    trigger_app_service = providers.Factory(
        TriggerApplicationService,
        trigger_repository=trigger_repo,
        strategy_repository=strategy_repo,
        settings_repository=settings_repo,
        compatibility_service=compatibility_service,
    )
```

이 컨테이너를 초기화한 뒤 `container.trigger_app_service()`를 호출하면 주입된 인스턴스가 반환되고, 테스트 시에는 `container.strategy_repo.override(MockStrategyRepository())`처럼 오버라이딩할 수 있다[11](https://python-dependency-injector.ets-labs.org/#:~:text=%40inject%20def%20main,None%3A).

* **프로젝트 의견** – **dependency-injector**를 공식적인 DI 컨테이너로 선정한다. 학습 곡선은 있지만, 설정 파일과 환경 변수 로딩 기능을 통해 비개발자도 설정을 관리하기 쉬우며, 코드베이스에서 중복된 팩토리/싱글턴 패턴을 제거할 수 있다.

## 3. DI 대상 기능 및 파일 선정 가이드

### 3.1 DI 필요 여부 판별 기준

1. **외부 리소스 사용** – 데이터베이스, API 클라이언트, 파일 시스템 등 외부 자원을 사용하면 주입 대상이다.
2. **다른 계층의 객체 호출** – 애플리케이션 서비스가 도메인 서비스나 레포지터리를 호출할 경우 의존성을 주입한다.
3. **테스트 격리가 필요한 경우** – 동작을 모킹/스텁 처리하여 테스트해야 하는 경우 주입한다.
4. **구현 교체 가능성이 있는 경우** – 예를 들어 `StrategyRepository`를 SQLite에서 PostgreSQL로 교체할 수 있도록 인터페이스를 정의하고 주입한다.

### 3.2 주요 모듈별 가이드

| 계층 | 파일/모듈 예시 | 현재 상태 | DI 적용 가이드 |
| --- | --- | --- | --- |
| **Domain** | `PathConfigurationService`, `StrategyCompatibilityService`, `NormalizationService`, `TriggerEvaluationService` 등 | 대부분 생성자에 레포지터리 주입이 있으나, 전역 싱글턴을 가져오는 경우도 있음 | 인터페이스(`ABC` 또는 `Protocol`)를 정의하고 의존 레포지터리를 생성자 주입한다. 전역 함수로 가져오는 이벤트 퍼블리셔는 컨테이너의 provider로 래핑한다. |
| **Domain Repositories** | `StrategyRepository`, `TriggerRepository`, `SettingsRepository`, `PathConfigurationRepository` | 구체 구현이 인프라스트럭처 계층에 있음 | 레포지터리 인터페이스를 정의하여 도메인 계층에서 의존하도록 하고, 구현체는 인프라 계층에서 제공한다. DI 컨테이너에서 인터페이스→구현체 매핑을 정의한다. |
| **Application** | `TriggerApplicationService`, `MenuService`, `ChartDataService`, `WebsocketApplicationService` 등 | 대부분 생성자에서 레포지터리와 서비스 인스턴스를 주입받음 | 컨테이너에서 Factory provider를 사용하여 애플리케이션 서비스를 생성한다. UI나 CLI에서 컨테이너를 통해 인스턴스를 얻도록 변경한다. |
| **Infrastructure** | `PathServiceFactory`, `DatabaseConnectionService`, `WebSocketStatusService`, `FileSystemService` 등 | 팩토리/싱글턴 패턴, 전역 변수 사용 | 컨테이너 내에서 Singleton provider로 관리한다. 예: `path_service = providers.Singleton(PathConfigurationService, path_repository=path_repo)`; 전역 함수를 제거하거나 Deprecated로 표시한다. |
| **Events** | `domain_event_publisher.py` | 전역 싱글턴 | DI 컨테이너에서 이벤트 퍼블리셔 provider를 정의하고, 필요 시 외부 서비스(예: 로깅, 메시지 큐)로 연결할 수 있게 한다. |
| **User Interface** | PyQt 화면, Chart Viewer 등 | UI 코드에서 직접 DB나 서비스에 접근하는 패턴이 일부 보임 | UI 컨트롤러는 DI 컨테이너에서 서비스 인스턴스를 받아 사용한다. 예: `chart_viewer = ChartViewer(trigger_service=container.trigger_app_service())`. |

### 3.3 추가 권장 사항

* **설정 파일 분리** – 현재 로컬 경로, API 키 등이 코드에 하드코딩되어 있다면 `config.yaml` 또는 `.env` 파일로 분리한다. `dependency-injector`의 `Configuration` provider를 이용하면 환경별 설정을 쉽게 로딩할 수 있다[12](https://python-dependency-injector.ets-labs.org/#:~:text=,See%20Configuration%20provider).
* **순환 의존성 해소** – 컨테이너 사용 시 순환 의존성이 발생하면 Lazy provider(`providers.Delegated` 또는 `Callable`)를 사용하거나 이벤트 발행/콜백 구조로 분리한다.
* **테스트 격리** – 테스트 모듈에서 `container.override()`를 사용하여 가짜 레포지터리나 서비스 구현을 주입하고, 테스트 종료 후 `container.reset_override()`로 복원한다.

## 4. 비개발자를 위한 설정 문서

GitHub Copilot을 이용해 **바이브 코딩**을 하시는 분을 위해, DI 컨테이너를 도입한 설정 절차를 단계별로 제시합니다.

1. **라이브러리 설치**

```bash
pip install dependency-injector
```

1. **프로젝트 구조 이해** – 현재 저장소는 **DDD(Domain-Driven Design)** 기반으로 `domain`, `application`, `infrastructure`, `ui` 등으로 나뉘어 있습니다. Roadmap 문서에 명시된 대로 각 모듈은 특정 책임을 가지며, 서로 느슨하게 결합됩니다.
2. **DI 컨테이너 정의** – `di_container.py`와 같은 파일을 생성하고 위의 예시처럼 `Container` 클래스를 정의합니다. 여기서 레포지터리와 서비스의 구체 구현을 싱글턴 provider로 등록합니다.
3. **설정 로딩** – `Container.config`를 통해 `config.yaml` 또는 `.env` 파일을 로딩합니다. API 키, 데이터베이스 경로, 로깅 레벨 등을 환경 변수로 정의하면 코드 변경 없이 설정을 관리할 수 있습니다.
4. **애플리케이션 진입점 수정** – 기존 `main.py` 또는 UI 실행 코드에서 직접 인스턴스를 생성하는 부분을 제거하고, DI 컨테이너를 초기화한 뒤 필요한 서비스를 주입합니다.

```python
from di_container import Container

def main():
    container = Container()
    container.config.from\yaml('config.yaml')
    container.init_resources() # 필요한 경우 리소스 provider 초기화
    container.wire(modules=[__name__])

    trigger_service = container.trigger_app_service()

    # 서비스 사용 코드 …

if __name__ == '__main__':
    main()
```

1. **UI에서 서비스 사용** – PyQt 등 UI 클래스는 DI 컨테이너를 통해 필요한 서비스를 주입받아 사용합니다.

```python
class TriggerBuilderDialog(QDialog):
 def __init__(self, trigger_service: TriggerApplicationService, parent=None):
 super().__init__(parent)
 self.trigger_service = trigger_service

# UI 구성…
```

UI를 생성할 때 `dialog = TriggerBuilderDialog(container.trigger_app_service())`처럼 주입합니다.

1. **테스트 작성** – 컨테이너를 테스트 모드로 구성하여 실제 DB 대신 메모리 DB나 목 객체를 주입할 수 있습니다. 예를 들어 `container.strategy_repo.override(FakeStrategyRepository())`로 오버라이딩 후 테스트를 수행합니다.
2. **GitHub Copilot 활용** – Copilot은 주석과 함수 시그니처를 기반으로 코드를 제안합니다. DI 컨테이너 사용 시 서비스 인터페이스와 생성자 시그니처가 명확하므로 Copilot이 제안하는 코드도 일관성을 유지할 수 있습니다. 예시 코드를 주석으로 충분히 설명하여 Copilot이 의도를 파악하도록 돕습니다.

### 참고 및 권장 자료

* DI 개념과 장단점: 의존성 주입은 외부에서 객체를 전달하여 느슨한 결합을 달성하는 설계 패턴이다[13](https://velog.io/%40sana/DI-%EC%9D%98%EC%A1%B4%EC%84%B1-%EC%A3%BC%EC%9E%85Dependency-Injection-%EC%9D%98-%EA%B0%9C%EB%85%90%EA%B3%BC-%EB%B0%A9%EB%B2%95#:~:text=%EC%9D%98%EC%A1%B4%EC%84%B1%20%EC%A3%BC%EC%9E%85%EC%9D%B4%EB%9E%80%3F). 생성자 주입을 통해 특정 구현에 의존하지 않고 다양한 객체를 전달받을 수 있으며, 코드 재사용성 및 테스트 용이성이 높아진다[2](https://velog.io/%40sana/DI-%EC%9D%98%EC%A1%B4%EC%84%B1-%EC%A3%BC%EC%9E%85Dependency-Injection-%EC%9D%98-%EA%B0%9C%EB%85%90%EA%B3%BC-%EB%B0%A9%EB%B2%95#:~:text=%EC%9D%98%EC%A1%B4%EC%84%B1%20%EC%A3%BC%EC%9E%85%EC%9D%98%20%EC%9E%A5%EC%A0%90).
* DI 유형: 생성자 주입, 세터 주입, 인터페이스 주입 중 파이썬에서는 생성자 주입을 우선 고려하고 세터 주입은 지양한다[14](https://bramilch.github.io/posts/kr-python-design-patterns/#:~:text=%EC%9D%98%EC%A1%B4%EC%84%B1%20%EC%A3%BC%EC%9E%85%20%EC%9C%A0%ED%98%95).
* DI 컨테이너: dependency-injector는 Factory, Singleton, Configuration provider 등 다양한 provider를 제공하며, 환경 변수와 설정 파일을 읽어들일 수 있다[15](https://python-dependency-injector.ets-labs.org/#:~:text=,injection%20framework%20for%20Python).
* 서비스 로케이터 경고: Service Locator 패턴은 의존성이 숨겨져 변경과 테스트가 어려워지며, 동일 타입의 객체가 여러 개일 때 메소드가 중복될 수 있다[8](https://velog.io/%40tco0427/DIDependency-Injection%EC%99%80-%EC%84%9C%EB%B9%84%EC%8A%A4-%EB%A1%9C%EC%BC%80%EC%9D%B4%ED%84%B0#:~:text=%EC%84%9C%EB%B9%84%EC%8A%A4%20%EB%A1%9C%EC%BC%80%EC%9D%B4%ED%84%B0%EC%9D%98%20%EB%8B%A8%EC%A0%90).

## 결론

프로젝트는 이미 DDD 구조를 따르면서 수동 DI를 부분적으로 적용하고 있다. 그러나 전역 싱글턴과 팩토리 함수가 혼재하여 객체 간 경계를 파악하기 어렵다. DI 컨테이너를 도입하면 생성, 구성, 주입의 책임을 명확히 분리할 수 있으며, 비개발자도 설정 파일을 통해 서비스 구성을 관리할 수 있다. 특히 백테스트, 실시간 거래, UI 등 다양한 모듈이 확장될 예정임을 고려할 때 **dependency-injector**를 통한 표준화된 DI 패턴 도입이 필요하다.

DI의 도입으로 클래스간 결합도를 줄이고 테스트 가능한 구조를 마련함으로써 장기적으로 유지보수 비용을 절감할 수 있다. 지금 당장은 추가 학습과 리팩토링 비용이 발생할 수 있지만, 프로젝트 로드맵의 목표를 성공적으로 달성하기 위해서는 **체계적인 의존성 관리**가 필수적이다.

## Closing

**Improved Prompt**

• *한국어로 작성: 의존성 주입(DI) 도입의 장단점을 논하고, Python 프로젝트에서 적합한 DI 패턴과 컨테이너를 선택하는 방법을 설명해 주세요. 기존 코드에 수동 DI와 서비스 로케이터가 혼재되어 있을 때의 문제점을 지적하고, DI 컨테이너를 사용한 개선안을 단계별로 제안해 주세요.*

**Model Recommendation:**

• *GPT-4 이상의 언어모델은 긴 코드 구조 분석과 한국어 문서 작성에 능하며, dependency-injector와 같은 라이브러리 예제 코드를 이해하고 설명하는 데 적합합니다. 만약 실제 코드 수정과 테스트 자동화를 진행하려면 GitHub Copilot이나 GPT-4 Code Interpreter 기능을 함께 사용하는 것을 추천합니다.*

**CSL:** 🟢 L1 (약 15.0 %) → *현재 컨텍스트 여유가 충분하므로 추가 질문이나 코드 분석을 수행해도 안전합니다.*

[1](https://bramilch.github.io/posts/kr-python-design-patterns/#:~:text=%EC%9D%98%EC%A1%B4%EC%84%B1%20%EC%A3%BC%EC%9E%85%20%ED%8C%A8%ED%84%B4%20DI%20,Pattern) [3](https://bramilch.github.io/posts/kr-python-design-patterns/#:~:text=,%EC%9E%88%EC%A7%80%20%EC%95%8A%EC%9C%BC%EB%AF%80%EB%A1%9C%20%EC%8B%9C%EC%8A%A4%ED%85%9C%EC%9D%B4%20%EB%8D%94%20%EB%AA%A8%EB%93%88%ED%99%94%EB%90%A8) [7](https://bramilch.github.io/posts/kr-python-design-patterns/#:~:text=,%ED%81%B4%EB%9E%98%EC%8A%A4%20%EC%83%9D%EC%84%B1%EC%9E%90%EB%A5%BC%20%ED%86%B5%ED%95%B4%20%EC%9D%98%EC%A1%B4%EC%84%B1%EC%9D%84%20%EC%A0%9C%EA%B3%B5) [14](https://bramilch.github.io/posts/kr-python-design-patterns/#:~:text=%EC%9D%98%EC%A1%B4%EC%84%B1%20%EC%A3%BC%EC%9E%85%20%EC%9C%A0%ED%98%95) 파이썬 디자인 패턴과 디펜던시 인젝션 패턴 Dependency Injection Pattern | bramilch

<https://bramilch.github.io/posts/kr-python-design-patterns/>

[2](https://velog.io/%40sana/DI-%EC%9D%98%EC%A1%B4%EC%84%B1-%EC%A3%BC%EC%9E%85Dependency-Injection-%EC%9D%98-%EA%B0%9C%EB%85%90%EA%B3%BC-%EB%B0%A9%EB%B2%95#:~:text=%EC%9D%98%EC%A1%B4%EC%84%B1%20%EC%A3%BC%EC%9E%85%EC%9D%98%20%EC%9E%A5%EC%A0%90) [4](https://velog.io/%40sana/DI-%EC%9D%98%EC%A1%B4%EC%84%B1-%EC%A3%BC%EC%9E%85Dependency-Injection-%EC%9D%98-%EA%B0%9C%EB%85%90%EA%B3%BC-%EB%B0%A9%EB%B2%95#:~:text=%EC%9D%98%EC%A1%B4%EC%84%B1%20%EC%A3%BC%EC%9E%85%EC%9D%80%20%EA%BC%AD%20%ED%95%84%EC%9A%94%ED%95%9C%EA%B0%80%3F) [13](https://velog.io/%40sana/DI-%EC%9D%98%EC%A1%B4%EC%84%B1-%EC%A3%BC%EC%9E%85Dependency-Injection-%EC%9D%98-%EA%B0%9C%EB%85%90%EA%B3%BC-%EB%B0%A9%EB%B2%95#:~:text=%EC%9D%98%EC%A1%B4%EC%84%B1%20%EC%A3%BC%EC%9E%85%EC%9D%B4%EB%9E%80%3F) [DI] 의존성 주입(Dependency Injection) 의 개념과 방법 및 장단점

[https://velog.io/@sana/DI-%EC%9D%98%EC%A1%B4%EC%84%B1-%EC%A3%BC%EC%9E%85Dependency-Injection-%EC%9D%98-%EA%B0%9C%EB%85%90%EA%B3%BC-%EB%B0%A9%EB%B2%95](https://velog.io/%40sana/DI-%EC%9D%98%EC%A1%B4%EC%84%B1-%EC%A3%BC%EC%9E%85Dependency-Injection-%EC%9D%98-%EA%B0%9C%EB%85%90%EA%B3%BC-%EB%B0%A9%EB%B2%95)

[5](https://velog.io/%40tco0427/DIDependency-Injection%EC%99%80-%EC%84%9C%EB%B9%84%EC%8A%A4-%EB%A1%9C%EC%BC%80%EC%9D%B4%ED%84%B0#:~:text=) [6](https://velog.io/%40tco0427/DIDependency-Injection%EC%99%80-%EC%84%9C%EB%B9%84%EC%8A%A4-%EB%A1%9C%EC%BC%80%EC%9D%B4%ED%84%B0#:~:text=%EB%91%90%EB%B2%88%EC%A7%B8%EB%A1%9C%EB%8A%94%20,%EC%82%AC%EC%9A%A9%ED%95%98%EC%A7%80%20%EC%95%8A%EB%8A%94%20%EC%A3%BC%EC%9E%85%20%EB%B0%A9%EC%8B%9D%EC%9D%B4%EB%8B%A4) [8](https://velog.io/%40tco0427/DIDependency-Injection%EC%99%80-%EC%84%9C%EB%B9%84%EC%8A%A4-%EB%A1%9C%EC%BC%80%EC%9D%B4%ED%84%B0#:~:text=%EC%84%9C%EB%B9%84%EC%8A%A4%20%EB%A1%9C%EC%BC%80%EC%9D%B4%ED%84%B0%EC%9D%98%20%EB%8B%A8%EC%A0%90) DI(Dependency Injection)와 서비스 로케이터

[https://velog.io/@tco0427/DIDependency-Injection%EC%99%80-%EC%84%9C%EB%B9%84%EC%8A%A4-%EB%A1%9C%EC%BC%80%EC%9D%B4%ED%84%B0](https://velog.io/%40tco0427/DIDependency-Injection%EC%99%80-%EC%84%9C%EB%B9%84%EC%8A%A4-%EB%A1%9C%EC%BC%80%EC%9D%B4%ED%84%B0)

[9](https://python-dependency-injector.ets-labs.org/#:~:text=,injection%20framework%20for%20Python) [10](https://python-dependency-injector.ets-labs.org/#:~:text=,See%20Configuration%20provider) [11](https://python-dependency-injector.ets-labs.org/#:~:text=%40inject%20def%20main,None%3A) [12](https://python-dependency-injector.ets-labs.org/#:~:text=,See%20Configuration%20provider) [15](https://python-dependency-injector.ets-labs.org/#:~:text=,injection%20framework%20for%20Python) Dependency Injector — Dependency injection framework for Python — Dependency Injector 4.48.2 documentation

<https://python-dependency-injector.ets-labs.org/>
