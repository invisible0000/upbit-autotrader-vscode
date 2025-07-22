# 매매전략 관리 탭2: 전략조합 화면 개발 태스크

## 🎯 개발 목표
- **코드화된 조합 전략**: 내부 클래스로 체계적 관리
- **DB 기반 영속성**: SQLite를 통한 조합 저장/로딩
- **백테스트 연동**: 조합 전략의 성능 검증 가능
- **직관적 UI**: 2x2 그리드 기반 조합 설계 환경

---

## 📋 개발 태스크 로드맵

### 🏗️ **Phase 1: 기반 인프라 구축**

#### **Task 1-1: 조합 전략 데이터 모델 설계** 
- [ ] `CombinationStrategy` 기본 클래스 설계
- [ ] 조합 메타데이터 스키마 정의
- [ ] 전략 구성 요소 데이터 구조 설계
- [ ] 검증 규칙 및 제약 조건 정의

**파일 경로**: `upbit_auto_trading/strategies/combinations/base_combination.py`

```python
@dataclass
class CombinationMetadata:
    combination_id: str
    name: str
    description: str
    version: str
    created_at: datetime
    is_active: bool
    risk_level: str  # LOW, MEDIUM, HIGH

@dataclass  
class StrategyComponent:
    strategy_id: str
    strategy_type: str
    role: str  # ENTRY, EXIT, SCALE_IN, SCALE_OUT
    trigger_mode: str  # PRIMARY, CONFIRMATION, GUARDIAN
    weight: float
    parameters: Dict[str, Any]
```

#### **Task 1-2: 데이터베이스 스키마 확장**
- [ ] `strategy_combinations` 테이블 생성
- [ ] `combination_components` 테이블 생성  
- [ ] `combination_backtest_results` 테이블 생성
- [ ] 마이그레이션 스크립트 작성

**SQL 스키마**:
```sql
CREATE TABLE strategy_combinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    combination_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    version VARCHAR(20),
    risk_level VARCHAR(10),
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE combination_components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    combination_id VARCHAR(50) NOT NULL,
    strategy_type VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL,
    trigger_mode VARCHAR(20) NOT NULL,
    weight REAL DEFAULT 1.0,
    parameters TEXT,  -- JSON
    order_index INTEGER,
    FOREIGN KEY (combination_id) REFERENCES strategy_combinations(combination_id)
);
```

#### **Task 1-3: 조합 팩토리 및 레지스트리**
- [ ] `CombinationFactory` 클래스 구현
- [ ] 조합 타입 레지스트리 구축
- [ ] 동적 조합 생성 메커니즘
- [ ] 의존성 해결 로직

**파일 경로**: `upbit_auto_trading/strategies/combination_factory.py`

---

### 🎨 **Phase 2: UI 컴포넌트 개발**

#### **Task 2-1: 2x2 그리드 레이아웃 구성**
- [ ] `StrategyCombinationTab` 메인 위젯 생성
- [ ] 4개 서브 위젯 영역 정의 및 배치
- [ ] 위젯 간 통신 인터페이스 설계
- [ ] 반응형 크기 조정 로직

**파일 경로**: `upbit_auto_trading/gui/strategy_combination_tab.py`

#### **Task 2-2: 영역 1 - 전략 라이브러리 위젯**
- [ ] 개별 전략 목록 표시
- [ ] 전략 카드 UI 컴포넌트 (배지 시스템)
- [ ] 필터링 및 검색 기능
- [ ] 드래그 앤 드롭 지원

**UI 요소**:
```
📈 진입 전략
├ 🔵 RSI 과매도 [E][📈][〰️][🔴]
├ 🔵 이평선 교차 [E][📈][📊][🟡] 
└ 🔵 MACD 골든크로스 [E][📈][📊][🟡]

🛡️ 관리 전략  
├ 🔴 트레일링 스탑 [X][🛑][🔄][🟡]
├ 🔴 고정 손절 [X][🛑][🔄][🟢]
└ 🟡 부분 익절 [S][💰][🔄][🟡]
```

#### **Task 2-3: 영역 2 - 조합 목록 위젯**
- [ ] 저장된 조합 전략 목록 표시
- [ ] 조합 요약 정보 카드
- [ ] 조합 로드/편집/삭제 기능
- [ ] 성능 지표 미리보기

#### **Task 2-4: 영역 3 - 조합 빌더 위젯**
- [ ] 드래그 앤 드롭 대상 영역
- [ ] 진입/관리 전략 구분 영역
- [ ] 조합 규칙 설정 UI (AND/OR/WEIGHTED)
- [ ] 실시간 검증 상태 표시

#### **Task 2-5: 영역 4 - 상세 분석 위젯**
- [ ] 선택된 전략 상세 정보 표시
- [ ] 조합 호환성 검증 결과
- [ ] 퀵 백테스트 실행 버튼
- [ ] 조합 저장/내보내기 기능

---

### ⚙️ **Phase 3: 비즈니스 로직 구현**

#### **Task 3-1: 조합 검증 엔진**
- [ ] 역할 충돌 검증 로직
- [ ] 신호 타입 호환성 검증
- [ ] 파라미터 유효성 검증
- [ ] 리스크 수준 분석

**파일 경로**: `upbit_auto_trading/strategies/combination_validator.py`

#### **Task 3-2: 조합 실행 엔진**
- [ ] 신호 생성 파이프라인
- [ ] 우선순위 기반 신호 해결
- [ ] 상태 머신 구현
- [ ] 컨텍스트 공유 메커니즘

**파일 경로**: `upbit_auto_trading/strategies/combination_engine.py`

#### **Task 3-3: 백테스트 통합**
- [ ] 조합 전략용 백테스트 어댑터
- [ ] 성능 지표 계산 (샤프비율, 승률, 최대손실)
- [ ] 결과 저장 및 시각화
- [ ] 비교 분석 기능

---

### 🔄 **Phase 4: 통합 및 테스트**

#### **Task 4-1: 컴포넌트 통합**
- [ ] UI와 비즈니스 로직 연결
- [ ] 이벤트 핸들링 구현
- [ ] 에러 처리 및 사용자 피드백
- [ ] 성능 최적화

#### **Task 4-2: 테스트 작성**
- [ ] 단위 테스트 (조합 검증, 신호 생성)
- [ ] 통합 테스트 (UI 상호작용)
- [ ] 시나리오 테스트 (실제 조합 생성 플로우)
- [ ] 성능 테스트 (대량 전략 처리)

#### **Task 4-3: 문서화 및 예제**
- [ ] 사용자 가이드 작성
- [ ] API 문서 업데이트
- [ ] 예제 조합 전략 생성
- [ ] 문제 해결 가이드

---

## 📅 개발 일정 (추정)

| Phase | 예상 소요 시간 | 주요 마일스톤 |
|-------|----------------|---------------|
| Phase 1 | 2-3일 | 데이터 모델 완성, DB 스키마 적용 |
| Phase 2 | 3-4일 | 2x2 UI 기본 구조 완성 |
| Phase 3 | 3-4일 | 조합 생성/실행 로직 완성 |
| Phase 4 | 2-3일 | 전체 통합 및 테스트 완료 |
| **총합** | **10-14일** | **완전한 전략 조합 탭 완성** |

---

## 🎯 성공 기준 (Definition of Done)

### ✅ **기능적 요구사항**
- [ ] 개별 전략을 드래그 앤 드롭으로 조합 생성 가능
- [ ] 조합 전략을 DB에 저장/로딩 가능
- [ ] 조합의 유효성 검증 및 충돌 감지 
- [ ] 백테스트를 통한 조합 성능 평가 가능
- [ ] 직관적이고 사용하기 쉬운 UI

### ✅ **기술적 요구사항**
- [ ] 코드 커버리지 80% 이상
- [ ] 메모리 사용량 최적화 (100MB 이하)
- [ ] UI 반응 시간 1초 이내
- [ ] 확장 가능한 아키텍처 설계

### ✅ **품질 요구사항**
- [ ] PEP 8 코딩 스타일 준수
- [ ] 타입 힌팅 100% 적용
- [ ] 에러 처리 및 로깅 완비
- [ ] 사용자 가이드 문서 완성

---

## 🚀 개발 우선순위

### 🔥 **High Priority (즉시 시작)**
1. Task 1-1: 조합 전략 데이터 모델 설계
2. Task 1-2: 데이터베이스 스키마 확장
3. Task 2-1: 2x2 그리드 레이아웃 구성

### 🟡 **Medium Priority (기반 완료 후)**
4. Task 2-2~2-5: UI 컴포넌트 개발
5. Task 3-1: 조합 검증 엔진

### 🟢 **Low Priority (마지막 단계)**
6. Task 3-2, 3-3: 실행 엔진 및 백테스트 통합
7. Task 4-1~4-3: 통합 테스트 및 문서화

---

## 💡 개발 팁 및 주의사항

### ⚡ **성능 최적화**
- 전략 목록이 많을 경우 가상화 스크롤 적용
- 조합 검증은 디바운싱으로 불필요한 계산 방지
- 백테스트는 백그라운드 스레드에서 실행

### 🛡️ **에러 처리**
- 잘못된 조합 생성 시 명확한 에러 메시지 제공
- DB 연결 실패 시 로컬 캐시 활용
- UI 프리징 방지를 위한 비동기 처리

### 🎨 **사용자 경험**
- 드래그 앤 드롭 시각적 피드백 제공
- 조합 완성도를 프로그레스 바로 표시
- 저장/로딩 상태를 스피너로 표시

---

> **🎯 핵심 목표**: "사용자가 직관적으로 전략을 조합하고, 즉시 성능을 확인할 수 있는 완전한 도구 완성"
