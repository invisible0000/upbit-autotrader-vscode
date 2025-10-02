# Dependency Injection 패턴 리뷰 – urgent/settings-complete-architecture-redesign 분기

## 📌 검토 배경

사용자는 invisible0000/upbit-autotrader-vscode 저장소의 urgent/settings-complete-architecture-redesign 브랜치에서 **3‑Container DI 아키텍처**의 구현을 진행 중이다. 이전 분석(TASK\_20251001\_05 문서)에 따르면 Presentation 계층에서 dependency-injector 패턴이 파편화되어 에러가 발생했으며, 본 검토에서 해당 분기 코드의 DI 패턴을 점검하고 개선 방안을 제시한다.

## 🔍 주요 파일별 패턴 분석

### 1. ExternalDependencyContainer (Infrastructure)

* dependency\_injector.containers.DeclarativeContainer를 상속해 외부 시스템(로그, DB, API 클라이언트 등)의 Provider를 선언한다.
* providers.Factory/Singleton/Configuration 등 기본 Provider를 바르게 사용하고 있으며, 각 Provider는 주입할 인스턴스의 생성자를 올바르게 지정한다.
* 예시: api\_key\_service = providers.Factory('…ApiKeyService', secure\_keys\_repository=secure\_keys\_repository) – 서비스 생성 시 필요한 레포지토리를 의존성으로 주입한다.

📌 **의견:** Infrastructure 레이어는 표준 패턴대로 잘 작성되어 있으며, 큰 수정 사항은 없다.

### 2. ApplicationServiceContainer (Application)

* 이 컨테이너는 repository\_container를 받아 내부 딕셔너리 \_services에 Application‑Service 인스턴스를 캐시한다. 각 getter에서 필요한 Repository를 꺼내 인스턴스를 생성한다.
* dependency-injector를 직접 사용하지 않고 수동으로 객체를 생성한다. 이는 Application 레이어가 DI 라이브러리에 직접 의존하지 않게 하려는 설계로 보인다.
* get\_api\_key\_service() 등 일부 메서드는 Infrastructure 컨테이너의 Provider를 직접 호출하여 서비스 인스턴스를 반환한다[[1]](https://github.com/invisible0000/upbit-autotrader-vscode/blob/urgent/settings-complete-architecture-redesign/upbit_auto_trading/infrastructure/dependency_injection/external_dependency_container.py#L103-L110).

📌 **의견:** Application 레이어의 DI 패턴은 일관성이 있으며, Provider 호출 시 external\_container.api\_key\_service()처럼 괄호를 사용해 **인스턴스**를 가져온다. 이는 올바른 사용법이다.

### 3. PresentationContainer (Presentation)

* Presentation 레이어 전용 컨테이너로 external\_container와 application\_container를 providers.Dependency로 선언하고 create\_presentation\_container()에서 override 한다.
* main\_window\_presenter = providers.Factory(MainWindowPresenter, services=providers.Dict(...)) 형태로 Presenter를 생성한다. 문제점은 **services 딕셔너리의 값**이다. 아래 코드처럼 외부 서비스 Provider를 주입할 때 external\_container.provided.theme\_service.provider 형태를 사용하고 있다[[2]](https://github.com/invisible0000/upbit-autotrader-vscode/blob/urgent/settings-complete-architecture-redesign/upbit_auto_trading/presentation/presentation_container.py#L88-L91).

main\_window\_presenter = providers.Factory(
 MainWindowPresenter,
 services=providers.Dict(
 # 잘못된 패턴
 theme\_service=external\_container.provided.theme\_service.provider,
 api\_key\_service=external\_container.provided.api\_key\_service.provider,
 ...
 )
)

\* .provided.<service>는 **제공된 인스턴스의 속성이나 메서드를 주입**할 때 사용하며[[3]](https://python-dependency-injector.ets-labs.org/providers/provided_instance.html#:~:text=To%20use%20the%20feature%20you,any%20combination%20of%20the%20following), .provider는 그 provider 자체를 반환한다. 따라서 위 코드에서 theme\_service와 api\_key\_service에는 **Provider 객체**가 들어가며, MainWindowPresenter 안에서 self.api\_key\_service.load\_api\_keys()를 호출하면 provider 객체에는 해당 메서드가 없어 에러가 발생한다.

📌 **문제 요약:** .provided.service.provider 패턴은 **서비스 인스턴스 대신 provider를 주입**하므로 Presenter가 서비스 메서드를 호출할 수 없다. 이는 사용자가 경험한 Factory 객체에 load\_api\_keys 속성이 없다는 오류의 원인이다.

### 4. MainWindow (UI View)

* dependency\_injector.wiring.inject 데코레이터와 Provide[...]를 이용해 생성자에서 서비스를 주입한다:

@inject
def \_\_init\_\_(self,
 api\_key\_service=Provide["api\_key\_service"],
 settings\_service=Provide["settings\_service"],
 theme\_service=Provide["theme\_service"],
 style\_manager=Provide["style\_manager"]
):

* 이러한 주입 방식은 외부 컨테이너를 **wire**하고 올바르게 Provide 이름을 지정했을 때 권장되는 패턴이다. 실제로 di\_lifecycle\_manager에서 wire\_external\_dependency\_modules()를 호출해 upbit\_auto\_trading.ui.desktop.main\_window 모듈을 wiring하고 있다[[4]](https://github.com/invisible0000/upbit-autotrader-vscode/blob/urgent/settings-complete-architecture-redesign/upbit_auto_trading/infrastructure/dependency_injection/external_dependency_container.py#L231-L262).

📌 **의견:** MainWindow는 표준 패턴을 준수한다. 단, Provide[...] 키의 문자열은 컨테이너 속성명과 일치해야 하며, 정확한 wiring 모듈 목록이 필요하다.

### 5. MainWindowPresenter (Presenter)

* services 딕셔너리를 받아 서비스 인스턴스를 속성에 할당하고, API 연결 테스트 시 self.api\_key\_service.load\_api\_keys()를 호출한다[[5]](https://github.com/invisible0000/upbit-autotrader-vscode/blob/urgent/settings-complete-architecture-redesign/upbit_auto_trading/presentation/presenters/main_window_presenter.py#L125-L140). 만약 services 딕셔너리에 provider가 주입되면 메서드가 존재하지 않아 오류가 발생한다.
* 코드 내부에서 서비스 타입 체크를 수행하여 hasattr(self.api\_key\_service, 'load\_api\_keys')를 통해 잘못된 타입을 감지하고 경고를 로깅하지만, 이는 방어적 코드일 뿐 근본 원인을 해결하지 못한다.

📌 **의견:** Presenter는 실제 서비스 인스턴스를 기대하고 있으므로, PresentationContainer에서 Provider 대신 인스턴스를 주입해야 한다.

## ✅ 개선 방안

### 1. PresentationContainer의 Provider 주입 방식 수정

현재:

main\_window\_presenter = providers.Factory(
 MainWindowPresenter,
 services=providers.Dict(
 theme\_service=external\_container.provided.theme\_service.provider,
 api\_key\_service=external\_container.provided.api\_key\_service.provider,
 navigation\_bar=navigation\_service,
 database\_health\_service=providers.Factory(...),
 screen\_manager\_service=screen\_manager\_service,
 window\_state\_service=window\_state\_service,
 menu\_service=menu\_service
 )
)

**수정 제안:** .provided.<service>.provider를 제거하고 **provider 자체**를 전달하면 providers.Dict가 호출 시 각각의 provider를 실행하여 서비스 인스턴스를 반환한다. 따라서 다음과 같이 변경한다.

# PresentationContainer
main\_window\_presenter = providers.Factory(
 MainWindowPresenter,
 services=providers.Dict(
 # 올바른 패턴: provider를 그대로 전달
 theme\_service=external\_container.theme\_service,
 api\_key\_service=external\_container.api\_key\_service,
 # UI 인프라
 navigation\_bar=navigation\_service,
 database\_health\_service=providers.Factory(
 "upbit\_auto\_trading.application.services.database\_health\_service.DatabaseHealthService"
 ),
 # Application UI 서비스
 screen\_manager\_service=screen\_manager\_service,
 window\_state\_service=window\_state\_service,
 menu\_service=menu\_service
 )
)

\* providers.Dict는 내부 provider들을 호출하여 실제 객체를 생성하므로, MainWindowPresenter는 인스턴스를 받을 수 있다. \* 만약 theme\_service나 api\_key\_service가 싱글턴/팩토리 호출 등 추가 로직이 필요하다면 providers.Callable이나 람다를 사용해 명시적으로 호출할 수도 있다.

### 2. MainWindowPresenter에서 DI 프레임워크 직접 사용

지속적으로 Presenter에 딕셔너리를 전달하는 패턴을 유지할지 여부를 검토해야 한다. dependency\_injector의 @inject 데코레이터를 Presenter에도 적용하면 services 딕셔너리를 제거할 수 있고, IDE 타입검사를 통한 안정성이 증가한다. 예를 들어:

from dependency\_injector.wiring import inject, Provide

class MainWindowPresenter(QObject):
 @inject
 def \_\_init\_\_(self,
 theme\_service = Provide["theme\_service"],
 api\_key\_service = Provide["api\_key\_service"],
 database\_health\_service = Provide["database\_health\_service"],
 screen\_manager\_service = Provide["screen\_manager\_service"],
 window\_state\_service = Provide["window\_state\_service"],
 menu\_service = Provide["menu\_service"]
 ):
 ...

\* 이렇게 하면 PresentationContainer에서 providers.Factory(MainWindowPresenter)만 선언하면 된다. 이는 코드 가독성을 높이고 DI 패턴을 일관되게 한다.

### 3. Wiring 범위 검토

* DI 시스템에서 wire() 호출 시 모듈 목록이 적절한지 재검토한다. 현재 wire\_external\_dependency\_modules()에서 Infrastructure 모듈만 wiring하지만, Presentation 모듈 wiring은 DILifecycleManager.\_wire\_presentation\_modules()에서 수행한다[[6]](https://github.com/invisible0000/upbit-autotrader-vscode/blob/urgent/settings-complete-architecture-redesign/upbit_auto_trading/infrastructure/dependency_injection/di_lifecycle_manager.py#L218-L226). 해당 목록에 누락된 모듈이 없는지 확인하고, 필요 시 upbit\_auto\_trading.presentation.presenters 전체를 포함하여 @inject 주입이 제대로 이루어지도록 한다.

### 4. 방어적 코드 간소화

* MainWindowPresenter.handle\_api\_connection\_test()에서 provider 타입을 확인하는 부분은 PresentationContainer의 잘못된 주입을 방지한 결과이므로, 주입 방식이 수정되면 해당 방어 코드를 간소화할 수 있다. 올바른 주입과 철저한 타입 힌트가 제공된다면 hasattr(self.api\_key\_service, 'load\_api\_keys') 검사가 불필요하다.

## 🤔 추가 질문 (Socratic)

1. **MainWindowPresenter에 대한 의존성 주입 방식**: Presenter에 딕셔너리를 전달하는 방식과 데코레이터를 통한 직접 주입 중 어느 방식이 유지보수 측면에서 더 나은가? 선택한 방식에 따라 컨테이너 정의와 테스트 코드가 달라질 것이다.
2. **싱글턴과 팩토리 사용 구분**: 현재 api\_key\_service는 providers.Factory로 정의되어 매번 새 인스턴스를 생성한다. API 키 로딩은 가벼운 연산이 아니므로 싱글턴으로 변경해야 할까? 서비스의 상태 관리 요구사항을 고려해 결정할 필요가 있다.
3. **Presenter와 View의 연결 위치**: MVP 컨테이너에서 Presenter 생성 후 View를 나중에 연결하는 패턴과, 컨테이너에서 완성된 MVP 패턴을 반환하는 방식을 병행하고 있다. 패턴 일관성을 위해 어느 쪽을 택할지 논의해야 한다.

## 📣 결론

urgent/settings-complete-architecture-redesign 브랜치의 DI 패턴은 크게 개선되었으나, **PresentationContainer에서 Provider를 잘못 주입**하는 부분이 여전히 남아 있다. dependency-injector 공식 문서에서 .provided 속성은 주입된 객체의 **속성이나 메서드**를 사용하기 위한 것이며[[3]](https://python-dependency-injector.ets-labs.org/providers/provided_instance.html#:~:text=To%20use%20the%20feature%20you,any%20combination%20of%20the%20following), .provider를 사용하면 Provider 객체가 그대로 전달된다. 따라서 서비스 인스턴스를 기대하는 Presenter와 충돌한다. 위에서 제시한 수정안을 적용하면 MainWindowPresenter가 올바르게 서비스를 호출할 수 있으며, DI 패턴의 일관성이 높아질 것이다.

[[1]](https://github.com/invisible0000/upbit-autotrader-vscode/blob/urgent/settings-complete-architecture-redesign/upbit_auto_trading/infrastructure/dependency_injection/external_dependency_container.py#L103-L110) [[4]](https://github.com/invisible0000/upbit-autotrader-vscode/blob/urgent/settings-complete-architecture-redesign/upbit_auto_trading/infrastructure/dependency_injection/external_dependency_container.py#L231-L262) external\_dependency\_container.py

<https://github.com/invisible0000/upbit-autotrader-vscode/blob/urgent/settings-complete-architecture-redesign/upbit_auto_trading/infrastructure/dependency_injection/external_dependency_container.py>

[[2]](https://github.com/invisible0000/upbit-autotrader-vscode/blob/urgent/settings-complete-architecture-redesign/upbit_auto_trading/presentation/presentation_container.py#L88-L91) presentation\_container.py

<https://github.com/invisible0000/upbit-autotrader-vscode/blob/urgent/settings-complete-architecture-redesign/upbit_auto_trading/presentation/presentation_container.py>

[[3]](https://python-dependency-injector.ets-labs.org/providers/provided_instance.html#:~:text=To%20use%20the%20feature%20you,any%20combination%20of%20the%20following) Injecting provided object attributes, items, or call its methods — Dependency Injector 4.48.2 documentation

<https://python-dependency-injector.ets-labs.org/providers/provided_instance.html>

[[5]](https://github.com/invisible0000/upbit-autotrader-vscode/blob/urgent/settings-complete-architecture-redesign/upbit_auto_trading/presentation/presenters/main_window_presenter.py#L125-L140) main\_window\_presenter.py

<https://github.com/invisible0000/upbit-autotrader-vscode/blob/urgent/settings-complete-architecture-redesign/upbit_auto_trading/presentation/presenters/main_window_presenter.py>

[[6]](https://github.com/invisible0000/upbit-autotrader-vscode/blob/urgent/settings-complete-architecture-redesign/upbit_auto_trading/infrastructure/dependency_injection/di_lifecycle_manager.py#L218-L226) di\_lifecycle\_manager.py

<https://github.com/invisible0000/upbit-autotrader-vscode/blob/urgent/settings-complete-architecture-redesign/upbit_auto_trading/infrastructure/dependency_injection/di_lifecycle_manager.py>