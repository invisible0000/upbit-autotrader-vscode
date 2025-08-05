# 📚 Infrastructure Repository 구현 교육 문서

> **목적**: DDD 기반 Infrastructure Layer Repository 구현을 위한 완전한 교육 자료
> **대상**: 주니어 개발자, Infrastructure Layer 학습자
> **갱신**: 2025-08-05

## 📋 문서 구성

### 🎯 **01_development_experience.md** - 개발 경험 공유
**실제 3일간의 Infrastructure Repository 구현 과정을 통해 얻은 생생한 경험과 인사이트**

- **Phase별 개발 과정**: 데이터베이스 분석 → 구조 설계 → 구현 → 테스트
- **예상 vs 실제**: 계획했던 것과 실제 구현에서 발견한 차이점들
- **핵심 도전과제**: Mock 패턴 설계, SQLite 최적화, 동적 쿼리 생성
- **정량적 성과**: 34개 테스트 100% 통과, 17개 Domain 메서드 완전 구현
- **배운 교훈**: 점진적 개발의 힘, 테스트 주도 개발의 가치

### 🛠️ **02_implementation_guide.md** - 단계별 구현 가이드
**처음부터 끝까지 Infrastructure Repository를 구현하는 상세한 실행 가이드**

- **Step 1-2**: 프로젝트 구조 설정, DatabaseManager 구현
- **Step 3-4**: Entity-Database 매퍼, Repository 구현
- **Step 5-6**: Repository Container, 테스트 작성
- **핵심 패턴들**: Upsert 패턴, 동적 쿼리 생성, Mock 패턴
- **성능 최적화**: SQLite WAL 모드, Connection Pooling, 캐싱
- **검증 방법**: 체크리스트, 테스트 실행, 성능 벤치마크

### 🔧 **03_problem_solving.md** - 문제해결 가이드
**실제 구현 과정에서 마주칠 수 있는 주요 문제들과 구체적인 해결 방법**

- **Problem 1**: Domain Entity 없이 Infrastructure 구현 → Mock 패턴 활용
- **Problem 2**: SQLite 동시성 및 성능 → WAL 모드, Thread-Local 연결
- **Problem 3**: Mock-Entity 인터페이스 불일치 → Protocol 기반 호환성
- **Problem 4**: 복잡한 동적 쿼리 → QueryBuilder 클래스 활용
- **Problem 5**: 테스트 DB 의존성 → Mock을 통한 완전 격리
- **디버깅 도구**: 로깅 시스템, SQL 디버깅, 성능 모니터링

## 🎯 학습 순서 (권장)

### 📚 **초급자 (DDD 아키텍처 처음 접하는 경우)**
1. **개발 경험 문서** 읽기 → 전체적인 흐름과 과정 이해
2. **구현 가이드** Step 1-3 → 기본 구조와 패턴 학습
3. **문제해결 가이드** Problem 1-2 → 핵심 문제 해결 방법 숙지

### 🔧 **중급자 (기본 Repository 패턴 이해하는 경우)**
1. **구현 가이드** 전체 → 실제 구현 진행
2. **문제해결 가이드** 전체 → 고급 문제 해결 기법 학습
3. **개발 경험 문서** Phase 5-6 → 고급 구현 팁과 최적화 방법

### ⚡ **고급자 (DDD Infrastructure 경험 있는 경우)**
1. **문제해결 가이드** → 복잡한 상황 대응 방법
2. **구현 가이드** 성능 최적화 부분 → 최신 패턴 학습
3. **개발 경험 문서** 인사이트 부분 → 경험 공유 및 비교

## 🛠️ 실습 환경 준비

### ✅ **필수 준비사항**
```bash
# 1. Python 환경 (3.8+)
python --version

# 2. 필요한 라이브러리 설치
pip install pytest sqlite3 typing dataclasses

# 3. 프로젝트 구조 생성
mkdir -p upbit_auto_trading/infrastructure/{repositories,database,mappers}
mkdir -p tests/infrastructure/repositories
```

### 📁 **참고 폴더 구조**
```
upbit_auto_trading/
├── domain/
│   ├── entities/
│   └── repositories/
├── infrastructure/
│   ├── repositories/
│   ├── database/
│   └── mappers/
└── tests/
    └── infrastructure/
        └── repositories/
```

## 🎯 실습 목표

### 🏆 **완료 시 달성할 수 있는 것들**
1. **DDD Infrastructure Layer 완전 이해**: Repository 패턴, 의존성 주입
2. **Mock 패턴 숙련도**: Domain Entity 없이도 Infrastructure 구현 가능
3. **SQLite 최적화 전문성**: 동시성, 성능, 트랜잭션 관리
4. **pytest TDD 경험**: Mock을 활용한 완전 격리 테스트
5. **문제해결 능력**: 복잡한 Infrastructure 문제 독립적 해결

### 📊 **검증 기준**
- [ ] DatabaseManager 클래스 완전 구현
- [ ] 3개 이상 Repository 구현 (Strategy, Trigger, Settings)
- [ ] RepositoryContainer 의존성 주입 패턴 구현
- [ ] 20개 이상 단위 테스트 작성 및 100% 통과
- [ ] Mock 패턴으로 Domain 호환성 보장
- [ ] SQLite 동시성 문제 해결
- [ ] 복잡한 동적 쿼리 안전 구현

## 📚 관련 자료

### 🔗 **프로젝트 내 참고 문서**
- [DDD 아키텍처 개요](../../../COMPONENT_ARCHITECTURE.md)
- [DDD 용어 사전](../../../DDD_UBIQUITOUS_LANGUAGE_DICTIONARY.md)
- [데이터베이스 스키마](../../../DB_SCHEMA.md)
- [개발 체크리스트](../../../DEV_CHECKLIST.md)

### 🌐 **외부 참고 자료**
- [Domain-Driven Design 개요](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Repository 패턴 가이드](https://martinfowler.com/eaaCatalog/repository.html)
- [SQLite 성능 최적화](https://www.sqlite.org/optoverview.html)
- [pytest 공식 문서](https://docs.pytest.org/)

---

**💡 핵심 메시지**: Infrastructure Repository 구현은 **실습**을 통해서만 완전히 이해할 수 있다!

**🎯 학습 목표**: 이론보다는 **실제 코드 작성**과 **문제 해결 경험**을 통한 실무 역량 향상
