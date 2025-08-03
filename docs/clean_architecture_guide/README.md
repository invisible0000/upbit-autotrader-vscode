# 📚 Clean Architecture 개발 가이드 인덱스

> **목적**: Clean Architecture 기반 업비트 자동매매 시스템 개발 가이드  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-03

## 🎯 문서 개요

Clean Architecture 리팩토링으로 인한 시스템 구조 변화에 대응하여, **모든 개발 시나리오**에서 빠르고 정확한 개발이 가능하도록 하는 포괄적 가이드입니다.

## 📋 아키텍처 변화의 핵심

### ✅ 개선점: 수정 부분이 명확해짐
- **단일 책임**: 각 계층이 명확한 역할만 담당
- **의존성 역전**: 상위 계층이 하위 계층을 참조하지 않음
- **변경 격리**: 한 계층 변경이 다른 계층에 영향 최소화
- **테스트 용이**: 각 계층을 독립적으로 테스트 가능

### 📊 복잡도 변화
- **초기 학습**: 아키텍처 이해 필요 (1-2주)
- **개발 속도**: 구조 파악 후 빠른 개발 (기존 대비 2-3배)
- **유지보수**: 변경 영향 범위 예측 가능 (기존 대비 50% 시간 단축)

## 📁 문서 구조 (읽기 순서)

### 1️⃣ 기초 이해 (필수)
- **[시스템 개요](01_SYSTEM_OVERVIEW.md)**: 전체 아키텍처 구조
- **[계층별 책임](02_LAYER_RESPONSIBILITIES.md)**: 각 계층의 역할과 경계
- **[데이터 흐름](03_DATA_FLOW.md)**: 요청부터 응답까지 데이터 이동

### 2️⃣ 개발 실무 (작업 시 참조)
- **[기능 추가 가이드](04_FEATURE_DEVELOPMENT.md)**: 새 기능 개발 워크플로
- **[UI 개발 가이드](05_UI_DEVELOPMENT.md)**: MVP 패턴 기반 UI 구현
- **[데이터베이스 수정](06_DATABASE_MODIFICATION.md)**: DB 스키마 변경 가이드
- **[API 통합](07_API_INTEGRATION.md)**: 외부 API 연동 방법

### 3️⃣ 고급 개발 (특수 상황)
- **[상태 관리](08_STATE_MANAGEMENT.md)**: 복잡한 상태 추적 시스템
- **[이벤트 시스템](09_EVENT_SYSTEM.md)**: Domain Event 및 UI Event
- **[성능 최적화](10_PERFORMANCE_OPTIMIZATION.md)**: 병목점 해결 방법
- **[에러 처리](11_ERROR_HANDLING.md)**: 예외 상황 대응 패턴

### 4️⃣ 특별 시나리오 (실제 사례)
- **[트레일링 스탑 구현](12_TRAILING_STOP_IMPLEMENTATION.md)**: 고급 기능 구현 사례
- **[백테스팅 엔진 확장](13_BACKTESTING_EXTENSION.md)**: 기존 시스템 확장
- **[새로운 전략 추가](14_NEW_STRATEGY_ADDITION.md)**: 전략 시스템 확장

### 5️⃣ 운영 및 유지보수
- **[디버깅 가이드](15_DEBUGGING_GUIDE.md)**: 문제 추적 및 해결
- **[테스팅 전략](16_TESTING_STRATEGY.md)**: 계층별 테스트 방법
- **[배포 및 마이그레이션](17_DEPLOYMENT_MIGRATION.md)**: 안전한 시스템 업데이트

## 🔍 빠른 참조

### 자주 사용하는 패턴
- **새 기능 추가**: 04_FEATURE_DEVELOPMENT.md → Domain → Application → Presentation
- **UI 수정**: 05_UI_DEVELOPMENT.md → MVP 패턴 확인
- **DB 스키마 변경**: 06_DATABASE_MODIFICATION.md → 영향 범위 분석 필수
- **버그 수정**: 15_DEBUGGING_GUIDE.md → 계층별 원인 추적

### 용어 사전
- **MVP**: Model-View-Presenter (UI 패턴)
- **DI**: Dependency Injection (의존성 주입)
- **DTO**: Data Transfer Object (데이터 전송 객체)
- **CQRS**: Command Query Responsibility Segregation (명령-조회 분리)
- **Repository**: 데이터 접근 추상화 패턴
- **Domain Event**: 도메인 계층에서 발생하는 비즈니스 이벤트

## 🚀 시작하기

### 첫 번째 작업 시
1. **[시스템 개요](01_SYSTEM_OVERVIEW.md)** 읽기 (10분)
2. **[계층별 책임](02_LAYER_RESPONSIBILITIES.md)** 숙지 (15분)
3. 작업 유형에 맞는 가이드 참조

### 긴급 디버깅 시
1. **[디버깅 가이드](15_DEBUGGING_GUIDE.md)** → 증상별 원인 추적
2. **[데이터 흐름](03_DATA_FLOW.md)** → 전체 플로우 확인
3. 해당 계층별 문서 참조

## 💡 문서 활용 팁

- **병렬 읽기**: 기능 개발 시 여러 문서 동시 참조
- **단계별 적용**: 이론 → 실습 → 검증 순서 권장
- **실험적 접근**: 테스트 환경에서 먼저 시도
- **피드백 반영**: 실제 경험을 바탕으로 문서 개선

---

**🎯 핵심**: "Clean Architecture는 초기 학습 비용은 있지만, 장기적으로 개발 생산성과 코드 품질을 크게 향상시킵니다!"

**📞 지원**: 각 문서 하단의 관련 문서 링크를 활용하여 필요한 정보를 빠르게 찾으세요.
