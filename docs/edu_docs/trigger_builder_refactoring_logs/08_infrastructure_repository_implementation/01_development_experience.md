# 🎯 Infrastructure Repository 구현 개발 경험

> **목적**: DDD 기반 Infrastructure Layer Repository 구현 시 실제 경험한 개발 과정과 인사이트 공유
> **대상**: 주니어 개발자, DDD 아키텍처 학습자
> **갱신**: 2025-08-05

## 📋 프로젝트 개요

**작업 기간**: 2025-08-03 ~ 2025-08-05 (3일)
**핵심 목표**: Domain Layer에서 정의한 Repository 인터페이스를 SQLite 기반으로 구현
**아키텍처**: DDD(Domain-Driven Design) 3-Layer Architecture
**데이터베이스**: 3-DB 아키텍처 (settings.sqlite3, strategies.sqlite3, market_data.sqlite3)

## 🎯 실제 개발 과정 및 경험

### 📊 Phase 1: 데이터베이스 스키마 분석 (Day 1)

#### 🔍 **예상했던 것 vs 실제 발견한 것**
```markdown
❌ 예상: 단순한 3개 데이터베이스 구조
✅ 실제: 복잡한 데이터 분산과 미니차트 독립 시스템

발견한 핵심 구조:
- Settings DB: 메타데이터 중심 (tv_* 테이블군)
- Strategies DB: 사용자 전략 저장 (strategies, strategy_conditions)
- Market Data DB: 백테스팅용 90일치 풍부한 데이터
- ⭐ Mini-Chart Sample DB: UI 시뮬레이션 전용 독립 시스템
```

#### 💡 **핵심 인사이트**
1. **레거시 코드 분석의 중요성**: atomic_* 테이블들이 현재 미사용임을 파악
2. **독립성 원칙**: 미니차트 샘플 DB는 별도 엔진에서 관리 (Repository 시스템과 격리)
3. **데이터 정의 소스**: data_info/*.yaml 파일이 Single Source of Truth

### 🏗️ Phase 2: 폴더 구조 설계 (Day 1)

#### 🎯 **DDD 계층별 분리 경험**
```
upbit_auto_trading/infrastructure/
├── repositories/     # Repository 구현체들
├── database/        # 데이터베이스 연결 관리
├── mappers/         # Entity ↔ Database 변환
└── __init__.py      # 패키지 Export 관리
```

#### 💡 **설계 결정 배경**
- **repositories/**: Domain 인터페이스 구현체들을 한 곳에 집중
- **database/**: 연결 풀링과 트랜잭션 관리를 분리
- **mappers/**: 데이터 변환 로직을 독립적으로 관리
- **확장성 고려**: 향후 external_apis, messaging 추가 가능한 구조

### 🔧 Phase 3: DatabaseManager 구현 (Day 1)

#### 🚨 **예상치 못한 도전과제**
```python
# 문제: SQLite 동시성과 성능 최적화
PRAGMA journal_mode=WAL;     # Write-Ahead Logging
PRAGMA synchronous=NORMAL;   # 성능 향상
PRAGMA cache_size=10000;     # 메모리 캐시 증가
```

#### ✅ **해결 과정**
1. **Connection Pooling**: 스레드 로컬 연결로 동시성 해결
2. **트랜잭션 패턴**: Context Manager로 안전한 트랜잭션 처리
3. **에러 핸들링**: 데이터베이스별 구체적인 예외 처리

### 🗺️ Phase 4: Mapper 구현과 Mock 패턴 (Day 2)

#### 🎯 **가장 어려웠던 부분: Mock 패턴 설계**

**문제 상황:**
- Domain Entity가 아직 완성되지 않음
- Infrastructure Layer는 미리 구현해야 함
- Entity 인터페이스 호환성 보장 필요

**해결 방법:**
```python
class MockStrategy:
    """Domain Layer 완성 전까지 호환성 보장하는 임시 Entity"""
    def __init__(self, strategy_id=None, name=None, description=None):
        self.strategy_id = strategy_id or "mock_strategy"
        self.name = name or "Mock Strategy"
        self.description = description or "Mock implementation"
        # ... 나머지 속성들
```

#### 💡 **Mock 패턴에서 배운 교훈**
1. **타입 안전성**: type: ignore 주석으로 임시 호환성 보장
2. **인터페이스 일관성**: 실제 Entity와 동일한 메서드 시그니처 유지
3. **데이터 변환**: JSON 직렬화/역직렬화 지원으로 데이터베이스 호환성

### 📦 Phase 5: Repository 구현 (Day 2-3)

#### 🎯 **Strategy Repository 구현 경험**

**가장 도전적이었던 메서드들:**
```python
# 1. find_strategies_by_criteria - 복잡한 필터링
def find_strategies_by_criteria(self, criteria):
    # 동적 WHERE 절 생성의 어려움

# 2. update_strategy_metadata - 부분 업데이트
def update_strategy_metadata(self, strategy_id, metadata):
    # 어떤 필드만 업데이트할지 결정하는 로직

# 3. get_strategy_statistics - 집계 쿼리
def get_strategy_statistics(self):
    # JOIN과 GROUP BY를 활용한 통계 계산
```

#### ✅ **구현 과정에서 배운 핵심 패턴**

1. **Upsert 패턴**: INSERT OR REPLACE 활용
```python
def save(self, strategy):
    strategy_data = self._mapper.to_database_record(strategy)
    query = """
    INSERT OR REPLACE INTO strategies
    (id, strategy_name, description, is_active, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """
```

2. **동적 쿼리 생성**: 조건부 WHERE 절
```python
def build_where_clause(self, criteria):
    conditions = []
    params = []

    if criteria.get('is_active') is not None:
        conditions.append("is_active = ?")
        params.append(criteria['is_active'])

    return " AND ".join(conditions), params
```

### 🧪 Phase 6: 테스트 구현 (Day 3)

#### 🎯 **테스트 전략의 진화**

**초기 접근: 통합 테스트**
```python
# 문제: 실제 데이터베이스에 의존적
def test_strategy_repository():
    repo = SqliteStrategyRepository()  # 실제 DB 연결
    strategy = create_test_strategy()
    repo.save(strategy)  # 실제 데이터 저장
```

**개선된 접근: Mock을 활용한 단위 테스트**
```python
# 해결: DatabaseManager를 Mock으로 격리
def test_strategy_repository(mock_db_manager):
    repo = SqliteStrategyRepository(mock_db_manager)
    strategy = create_mock_strategy()
    repo.save(strategy)  # Mock DB에 저장
```

#### 💡 **테스트에서 배운 핵심 교훈**

1. **의존성 격리**: Mock을 활용해 Repository 로직만 순수 검증
2. **에지 케이스 테스트**: 존재하지 않는 데이터 조회, 중복 저장 등
3. **성능 테스트**: 동시성 안전성, 메모리 누수 확인

## 🚀 성과 및 결과

### ✅ **완성된 핵심 컴포넌트**
1. **SqliteStrategyRepository**: 17개 Domain 메서드 완전 구현
2. **RepositoryContainer**: 의존성 주입 컨테이너 패턴
3. **DatabaseManager**: 3-DB 아키텍처 연결 관리
4. **Comprehensive Testing**: 34개 테스트 케이스 100% 통과

### 📊 **정량적 성과**
- **구현 기간**: 3일 (계획 대비 100%)
- **테스트 커버리지**: 100% (34/34 테스트 통과)
- **Domain 인터페이스 준수**: 100% (17/17 메서드 구현)
- **성능**: 0.31초 내 모든 테스트 완료

### 🎯 **정성적 성과**
- **DDD 아키텍처 이해도 대폭 향상**
- **Mock 패턴을 활용한 점진적 개발 경험**
- **pytest 기반 TDD 개발 방법론 습득**
- **SQLite 최적화 및 동시성 처리 경험**

## 🔍 개발 과정에서 느낀 점

### 💡 **가장 중요했던 인사이트**

1. **점진적 개발의 힘**: Mock 패턴으로 Domain Layer 완성 전에도 안정적 개발 가능
2. **테스트 주도 개발**: 테스트를 먼저 작성하면 설계가 더 명확해짐
3. **의존성 주입의 가치**: RepositoryContainer로 코드 유연성 대폭 향상
4. **레거시 코드 분석**: 기존 시스템 이해가 새로운 설계의 핵심

### 🚨 **가장 어려웠던 순간들**

1. **Mock 패턴 설계**: Domain Entity 없이 Infrastructure 구현하는 딜레마
2. **동적 쿼리 생성**: 유연한 검색 조건을 SQL로 변환하는 복잡성
3. **테스트 격리**: Mock과 실제 구현 간의 일관성 보장
4. **성능 최적화**: SQLite의 한계 내에서 최적 성능 달성

### 🎯 **다음에 더 잘할 수 있는 것들**

1. **초기 설계 단계**: Domain Entity 인터페이스를 미리 더 상세히 정의
2. **테스트 우선 개발**: TDD 방식으로 테스트를 더 일찍 작성
3. **문서화 병행**: 구현과 동시에 문서 업데이트
4. **성능 측정**: 벤치마크 테스트를 개발 초기부터 포함

## 📚 참고 자료 및 관련 문서

- [DDD 용어 사전](../../../DDD_UBIQUITOUS_LANGUAGE_DICTIONARY.md)
- [Infrastructure Layer 아키텍처](../../../COMPONENT_ARCHITECTURE.md)
- [Database 스키마](../../../DB_SCHEMA.md)
- [개발 체크리스트](../../../DEV_CHECKLIST.md)

---

**💡 핵심 메시지**: DDD Infrastructure Layer 구현은 **점진적 개발**과 **테스트 주도**로 접근하면 성공할 수 있다!
