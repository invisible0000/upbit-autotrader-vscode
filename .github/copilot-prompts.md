# 업비트 자동매매 시스템 - 자주 쓰는 Copilot 프롬프트

## 🎯 DDD + MVP 아키텍처 패턴

### Factory 패턴 구현

```
Copilot, DDD Factory 패턴으로 ApplicationServiceContainer를 통해 [컴포넌트명] Factory를 구현해 주세요.
- BaseComponentFactory 상속
- _get_service() 메서드 사용
- Golden Rules 준수 (Fail Fast)
- Infrastructure 로깅 적용
```

### MVP 패턴 구현

```
Copilot, MVP 패턴으로 [화면명] Presenter와 View를 분리해서 구현해 주세요.
- Presenter는 presentation/presenters/ 위치
- View는 ui/desktop/screens/ 위치
- 의존성 역전 원칙 준수
```

### Container 접근 패턴

```
Copilot, ApplicationServiceContainer를 통해 올바른 계층별 접근을 구현해 주세요.
- get_application_container() 사용
- app_container.get_xxx_service() 패턴
- ApplicationContext 상태 검증
```

## 🧪 테스트 및 검증 패턴

### 단위 테스트 생성

```
Copilot, pytest를 사용해서 [함수명/클래스명]에 대한 단위 테스트를 작성해 주세요.
- Given-When-Then 패턴
- 비즈니스 로직 검증 중심
- Mock 객체 적절히 활용
```

### UI 통합 테스트

```
Copilot, python run_desktop_ui.py로 검증 가능한 UI 통합 테스트를 구현해 주세요.
- 설정 화면 진입 확인
- 7규칙 전략 동작 검증
- MVP 패턴 연결 상태 확인
```

## ⚡ 빠른 구현 패턴

### 로깅 시스템

```
Copilot, Infrastructure 로깅을 사용해서 [컴포넌트명] 로거를 생성하고 적절한 로그를 출력해 주세요.
- create_component_logger("ComponentName") 사용
- print() 대신 logger 사용
- 에러, 경고, 정보 레벨 구분
```

### 안전한 거래 시뮬레이션

```
Copilot, dry_run=True 기본값으로 안전한 거래 시뮬레이션을 구현해 주세요.
- 실거래는 dry_run=False + 2단계 확인
- 모든 주문은 기본 시뮬레이션
- 결과 로깅 및 검증
```

### PowerShell 명령어

```
Copilot, Windows PowerShell 전용으로 [작업명] 스크립트를 작성해 주세요.
- Unix 명령어 금지 (&&, grep, ls 등)
- 표준 PS 구문 사용
- Here-String 방식 권장
```

## 🔧 프로젝트 특화 표현

### 아키텍처 준수

```
Copilot, DDD + Clean Architecture 계층별 접근 규칙을 100% 준수해서 구현해 주세요.
- Presentation → Application → Infrastructure 방향
- Domain 순수성 유지 (외부 의존성 없음)
- 계층 위반 절대 금지
```

### 데이터베이스 분리

```
Copilot, 3-DB 분리 구조를 준수해서 데이터 접근을 구현해 주세요.
- settings.sqlite3: 설정 데이터
- strategies.sqlite3: 전략 데이터
- market_data.sqlite3: 시장 데이터
```

### 7규칙 전략 통합

```
Copilot, 7규칙 전략이 완벽 동작하도록 [기능명]을 구현해 주세요.
- RSI 과매도 진입, 수익시 불타기, 계획된 익절
- 트레일링 스탑, 하락시 물타기
- 급락 감지, 급등 감지
```

## 📋 태스크 완료 보고

### 완료 보고서 템플릿

```
## 🎉 [태스크명] 완료 보고서

### ✅ 완료된 작업
- [완료 항목들]

### 🎯 성공 기준 달성
- [달성된 기준들]

### 📊 테스트 결과
- [검증 결과들]

**[태스크명] 작업이 성공적으로 완료되었습니다!** 🎉
```
