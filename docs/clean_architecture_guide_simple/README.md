# 📚 Clean Architecture 간소화 가이드

> **목적**: LLM 최적화된 Clean Architecture 문서 모음  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-03  
> **최적화**: 150-200줄, 실용적 예시, 의미적 마커

## 🎯 문서 구성

이 폴더는 기존 `docs/clean_architecture_guide`의 장문 문서들을 **LLM 처리 최적화**하여 재작성한 버전입니다.

### 📋 문서 목록 (총 16개)

#### 🏗️ 기본 아키텍처 (01-06)
- **[01_SYSTEM_OVERVIEW.md](01_SYSTEM_OVERVIEW.md)**: 전체 시스템 아키텍처 개요
- **[02_LAYER_RESPONSIBILITIES.md](02_LAYER_RESPONSIBILITIES.md)**: 각 계층의 역할과 책임
- **[03_DATA_FLOW.md](03_DATA_FLOW.md)**: 데이터 흐름과 의존성 방향
- **[04_FEATURE_DEVELOPMENT.md](04_FEATURE_DEVELOPMENT.md)**: 새 기능 개발 워크플로
- **[05_UI_DEVELOPMENT.md](05_UI_DEVELOPMENT.md)**: MVP 패턴 기반 UI 개발
- **[06_TROUBLESHOOTING.md](06_TROUBLESHOOTING.md)**: 일반적인 문제 해결 가이드

#### ⚙️ 고급 개념 (07-11)  
- **[07_STATE_MANAGEMENT.md](07_STATE_MANAGEMENT.md)**: 상태 관리 패턴과 추적
- **[08_EVENT_SYSTEM.md](08_EVENT_SYSTEM.md)**: 도메인/애플리케이션 이벤트 시스템
- **[09_PERFORMANCE_OPTIMIZATION.md](09_PERFORMANCE_OPTIMIZATION.md)**: 계층별 성능 최적화
- **[10_ERROR_HANDLING.md](10_ERROR_HANDLING.md)**: 체계적 오류 처리 전략
- **[11_TESTING_STRATEGY.md](11_TESTING_STRATEGY.md)**: 계층별 테스팅 방법론

#### 🛠️ 실무 구현 (12-16)
- **[12_DEBUGGING_GUIDE.md](12_DEBUGGING_GUIDE.md)**: 계층별 디버깅 도구와 기법
- **[13_DATABASE_MANAGEMENT.md](13_DATABASE_MANAGEMENT.md)**: DB 마이그레이션과 성능 관리
- **[14_TRAILING_STOP_IMPLEMENTATION.md](14_TRAILING_STOP_IMPLEMENTATION.md)**: 트레일링 스탑 전체 구현
- **[15_BACKTESTING_EXTENSION.md](15_BACKTESTING_EXTENSION.md)**: 백테스팅 시스템 확장
- **[16_NEW_STRATEGY_ADDITION.md](16_NEW_STRATEGY_ADDITION.md)**: 새 전략 체계적 추가

## 🔧 LLM 최적화 특징

### ✅ 구조적 개선
- **길이 제한**: 150-200줄로 최적화 (기존 300-1100줄 → 압축)
- **의미적 마커**: 🎯, ✅, ❌, 💡 등으로 즉시 식별 가능
- **실행 가능 코드**: 바로 사용할 수 있는 Python 예시
- **계층적 구조**: 명확한 섹션 구분과 목차

### ✅ 내용 개선
- **핵심 집중**: 가장 중요한 개념과 패턴만 선별
- **실용성**: 이론보다 실제 구현 중심
- **검증 가능**: 코드 예시로 바로 확인 가능
- **상호 참조**: 관련 문서들과 명확한 연결

### ✅ 접근성 개선
- **빠른 스캔**: 마커와 코드블록으로 핵심만 빠르게 파악
- **컨텍스트**: 각 문서가 독립적으로 완전한 정보 제공
- **검색성**: 명확한 키워드와 패턴으로 쉬운 검색

## 🚀 활용 방법

### 👤 개발자용
```markdown
1. 전체 이해: 01-03번 문서로 기본 개념 파악
2. 실무 적용: 04-06번 문서로 개발 프로세스 학습  
3. 고급 기능: 07-11번 문서로 전문 지식 습득
4. 구체적 구현: 12-16번 문서로 실제 기능 구현
```

### 🤖 LLM 에이전트용
```markdown
1. 빠른 컨텍스트: 문서당 150-200줄로 토큰 효율성 극대화
2. 의미적 파싱: 🎯, ✅, ❌ 마커로 중요도 즉시 파악
3. 실행 가능: 코드 예시를 바로 활용하여 구현 제안
4. 검증 기반: 실제 작동하는 패턴으로 정확한 조언
```

## 📊 문서별 세부 특징

### 기본 문서 (01-06): 핵심 개념
- **시스템 이해**: Clean Architecture 5계층 구조
- **개발 워크플로**: 단계별 기능 개발 프로세스
- **문제 해결**: 일반적 이슈와 해결책

### 고급 문서 (07-11): 전문 지식
- **상태 관리**: Single Source of Truth 패턴
- **이벤트 시스템**: Domain Event 기반 디커플링
- **성능 최적화**: 계층별 최적화 전략
- **오류 처리**: Result 패턴과 예외 전략
- **테스팅**: 70% 단위, 25% 통합, 5% E2E

### 실무 문서 (12-16): 구체적 구현
- **디버깅**: 계층별 문제 추적 도구
- **DB 관리**: 마이그레이션과 성능 최적화
- **기능 구현**: 트레일링 스탑, 백테스팅, 새 전략

## 💡 기존 문서와의 차이점

### Before (기존 문서)
- **길이**: 300-1100줄의 장문
- **구조**: 상세한 설명 위주
- **예시**: 개념적 설명 중심
- **접근성**: 전체 읽기 필요

### After (최적화 문서)  
- **길이**: 150-200줄로 압축
- **구조**: 실행 가능 코드 중심
- **예시**: 바로 사용 가능한 패턴
- **접근성**: 마커로 빠른 스캔

## 🔗 상호 참조 체계

각 문서는 다른 관련 문서들과 명확히 연결되어 있습니다:

```
시스템 개요 ← → 레이어 책임 ← → 데이터 흐름
     ↓              ↓              ↓
기능 개발 ← → UI 개발 ← → 문제 해결
     ↓              ↓              ↓
상태 관리 ← → 이벤트 ← → 성능 최적화
     ↓              ↓              ↓
오류 처리 ← → 테스팅 ← → 디버깅
     ↓              ↓              ↓
DB 관리 ← → 구체적 구현들
```

## 📚 추가 자료

### 원본 문서
- **docs/clean_architecture_guide/**: 상세한 원본 문서 (참고용)
- **docs/**: 프로젝트 전체 문서 (PROJECT_SPECIFICATIONS.md 등)

### 관련 가이드
- **docs/DEV_CHECKLIST.md**: 개발 검증 체크리스트
- **docs/STYLE_GUIDE.md**: 코딩 표준
- **docs/BASIC_7_RULE_STRATEGY_GUIDE.md**: 기본 검증 전략

---

**💡 핵심**: "빠르게 이해하고, 바로 적용하고, 확실히 검증하는 문서!"

**🎯 목표**: "LLM과 개발자 모두가 효율적으로 활용할 수 있는 Clean Architecture 가이드"
- 경계 위반 예시와 해결법
- 실제 코드 예시로 이해

### 3️⃣ [데이터 흐름](03_DATA_FLOW.md) ⏱️ 6분
**요청이 어떻게 각 계층을 통과하는가**
- 5단계 데이터 흐름 상세
- 트리거 생성 실제 예시
- 이벤트 처리와 성능 최적화

### 4️⃣ [기능 개발](04_FEATURE_DEVELOPMENT.md) ⏱️ 5분
**새 기능 추가 시 단계별 워크플로**
- Domain First 개발 방법론
- TrailingStop 기능 구현 예시
- 테스트 작성과 검증 방법

### 5️⃣ [UI 개발](05_UI_DEVELOPMENT.md) ⏱️ 7분
**MVP 패턴으로 PyQt6 UI 개발**
- View-Presenter 분리 원칙
- 이벤트 처리와 상태 관리
- 실제 트리거 빌더 구현 예시

### 6️⃣ [문제 해결](06_TROUBLESHOOTING.md) ⏱️ 6분
**자주 발생하는 문제와 해결법**
- 계층 경계 위반 문제
- 순환 의존성 해결
- 성능 문제와 디버깅 전략

**총 소요 시간**: 약 39분으로 Clean Architecture 완전 마스터

## 🏗️ 5계층 아키텍처 요약

```
🎨 Presentation  ← UI만 담당 (사용자 입출력)
⚙️ Application   ← Use Case 조율 (비즈니스 흐름)
💎 Domain        ← 비즈니스 규칙 (핵심, 중심)
🔌 Infrastructure ← 외부 연동 (DB, API)
🛠️ Shared        ← 공통 유틸리티
```

**핵심 원칙**: Domain이 중심이며, 모든 계층이 Domain을 참조 (Domain은 다른 계층 참조 금지)

## 🎯 주요 패턴 요약

### MVP (Model-View-Presenter)
```python
View → Presenter → Service → Domain → Repository
 ↖        ↖         ↖        ↖        ↖
  ←--------←---------←--------←--------← 응답
```

### Repository Pattern
```python
# 인터페이스 (Domain)
class StrategyRepository(ABC):
    def save(self, strategy): pass

# 구현 (Infrastructure)  
class SqliteStrategyRepository(StrategyRepository):
    def save(self, strategy): pass
```

### Domain Events
```python
# Domain에서 이벤트 발생
strategy.add_event(StrategyCreated(strategy.id))

# Application에서 이벤트 처리
event_publisher.publish(strategy.get_events())
```

## 🚀 빠른 시작 가이드

### 새 기능 개발 시 순서
1. **[시스템 개요](01_SYSTEM_OVERVIEW.md)** 읽기 → 전체 구조 파악
2. **[계층별 책임](02_LAYER_RESPONSIBILITIES.md)** 읽기 → 어느 계층에서 작업할지 결정
3. **[기능 개발](04_FEATURE_DEVELOPMENT.md)** 읽기 → 구체적 구현 방법 학습
4. **Domain부터 구현** → Application → Infrastructure → Presentation 순서

### 기존 코드 수정 시
1. **[계층별 책임](02_LAYER_RESPONSIBILITIES.md)** 확인 → 올바른 계층에서 수정하는지 검증
2. **[데이터 흐름](03_DATA_FLOW.md)** 확인 → 수정이 다른 계층에 미치는 영향 파악
3. 해당 계층의 단위 테스트 실행
4. 전체 통합 테스트 실행

### 문제 해결 시
1. **[문제 해결](06_TROUBLESHOOTING.md)** 먼저 확인 → 일반적인 문제 패턴 검색
2. **[데이터 흐름](03_DATA_FLOW.md)** 따라가며 디버깅
3. 각 계층별로 입출력 데이터 확인
4. Domain Layer의 비즈니스 로직 검증
5. Repository Layer의 데이터 저장/조회 확인

## 💡 핵심 개념 치트시트

### 계층별 핵심 역할
- **🎨 Presentation**: 표시만 (비즈니스 로직 금지)
- **⚙️ Application**: Use Case 조율 (트랜잭션, 이벤트)
- **💎 Domain**: 비즈니스 규칙 (외부 의존성 금지)
- **🔌 Infrastructure**: 외부 연동 (DB, API)

### 의존성 방향 (중요!)
```
Presentation → Application → Domain ← Infrastructure
```
- Domain은 다른 계층을 참조하지 않음
- 모든 계층이 Domain을 참조
- Infrastructure는 Domain 인터페이스를 구현

### 데이터 변환 지점
- **View ↔ Presenter**: UI 데이터 ↔ DTO
- **Presenter ↔ Service**: DTO ↔ Command/Query
- **Service ↔ Repository**: Domain Entity ↔ DB Data

## 🔗 관련 자료

### 원본 상세 문서
- `docs/clean_architecture_guide/`: 상세한 설명과 예시
- `docs/refactoring_plan/`: 리팩토링 계획서
- `docs/refactoring_design/`: 리팩토링 설계서

### 프로젝트 핵심 문서
- [프로젝트 명세서](../PROJECT_SPECIFICATIONS.md): 전체 시스템 개요
- [개발 체크리스트](../DEV_CHECKLIST.md): 개발 검증 기준
- [아키텍처 개요](../ARCHITECTURE_OVERVIEW.md): 현재 아키텍처

---

**💡 핵심 메시지**: "Clean Architecture는 복잡하지 않습니다. Domain을 중심으로 계층을 분리하는 것이 전부입니다!"

**🎯 성공 기준**: 이 가이드를 읽고 나면 새로운 기능을 어느 계층에서 어떻게 구현해야 할지 명확히 알 수 있어야 합니다.
