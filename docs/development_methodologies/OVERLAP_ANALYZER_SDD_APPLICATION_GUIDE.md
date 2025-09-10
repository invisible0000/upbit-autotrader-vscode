# 🎯 OverlapAnalyzer v5.0 SDD 적용 가이드

> 현재 개발 중인 OverlapAnalyzer v5.0에 Specification-Driven Development 적용 방안
>
> 작성일: 2025년 9월 10일
> 기반: OVERLAP_ANALYZER_V5_SIMPLIFIED_DESIGN.md

---

## 🔍 현재 상황 분석

### 📁 **기존 프로젝트 구조 (변경 없음)**
```
d:\projects\upbit-autotrader-vscode\
├── upbit_auto_trading/
│   └── infrastructure/market_data/candle/
│       ├── OVERLAP_ANALYZER_V5_SIMPLIFIED_DESIGN.md  # 기존 설계서
│       └── overlap_analyzer.py                       # 기존 구현
├── docs/
├── tests/
└── ...
```

### 🆕 **SDD 적용 후 (OverlapAnalyzer 전용)**
```
d:\projects\upbit-autotrader-vscode\
├── upbit_auto_trading/                              # ✅ 기존 코드 그대로
├── specs/                                           # 🆕 NEW! SDD 전용 폴더
│   └── 001-overlap-analyzer-v5/                     # 🆕 OverlapAnalyzer 명세
│       ├── feature-spec.md                          # 기능 명세서
│       ├── implementation-plan.md                   # 구현 계획
│       └── implementation-details/                  # 세부 구현사항
│           ├── 00-research.md
│           ├── 02-data-model.md
│           ├── 03-api-contracts.md
│           └── 06-contract-tests.md
└── .specify/                                        # 🆕 SDD 메타데이터
```

---

## 🚀 실제 적용 프로세스

### 1️⃣ **현재 위치에서 Spec Kit 초기화**
```powershell
# 현재 프로젝트 루트에서
cd d:\projects\upbit-autotrader-vscode
uvx --from git+https://github.com/github/spec-kit.git specify init .
```

### 2️⃣ **OverlapAnalyzer 명세서 작성**
```
/specify 업비트 캔들 데이터의 겹침 상태를 5가지로 정확히 분류하는 OverlapAnalyzer v5.0을 구현해 주세요.

상세 요구사항:
- NO_OVERLAP, COMPLETE_OVERLAP, PARTIAL_START, PARTIAL_MIDDLE_FRAGMENT, PARTIAL_MIDDLE_CONTINUOUS 5가지 상태 분류
- DDD Repository 패턴 준수하여 Infrastructure 계층에 배치
- 시간 중심 처리로 target_start/target_end 기준 판단
- 성능 최적화를 위한 단계별 조기 종료 로직
- SQLite 기반 candle_repository와 연동
- 업비트 API 내림차순 특성 고려한 시간 계산
- 개발 초기 검증 로직 포함하되 안정화 후 제거 가능
```

### 3️⃣ **기술 구현 계획 수립**
```
/plan 기존 DDD 아키텍처와 완벽 호환되도록 구현합니다.

기술 스택:
- Infrastructure 계층: SQLiteCandalRepository 확장
- Domain 객체: OverlapRequest/OverlapResult 데이터클래스
- 테스트: pytest 기반 5가지 상태별 단위 테스트
- 성능: LIMIT 1, COUNT, MAX/MIN 쿼리 최적화
- 검증: 임시 validation 로직으로 개발 안정성 확보

제약사항:
- 기존 upbit_auto_trading 모듈 구조 유지
- 3-DB 분리 원칙 준수 (market_data.sqlite3 사용)
- Infrastructure 로깅 시스템 활용
- 기존 time_utils 모듈과 연동
```

### 4️⃣ **태스크 분해 및 순차 구현**
```
/tasks OverlapAnalyzer v5.0 구현을 단계별로 분해해 주세요.
```

---

## 🎨 기존 설계서와 SDD 명세서 연동

### 📋 **기존 설계서 활용**
현재 `OVERLAP_ANALYZER_V5_SIMPLIFIED_DESIGN.md`의 상세한 설계를 SDD 명세서에 통합:

1. **Feature Spec**: 5가지 상태 분류 요구사항
2. **Implementation Plan**: Repository 확장 방법, 성능 최적화 전략
3. **API Contracts**: OverlapRequest/OverlapResult 인터페이스
4. **Test Scenarios**: 5가지 상태별 테스트 케이스

### 🔄 **점진적 통합 전략**

#### Phase 1: SDD로 새 구현 생성
```powershell
# SDD로 OverlapAnalyzer v5.0 완전 새로 구현
# 기존 코드는 건드리지 않음
```

#### Phase 2: 병렬 테스트
```powershell
# 기존 구현 vs SDD 구현 성능/정확성 비교
# 기존: upbit_auto_trading/infrastructure/market_data/candle/overlap_analyzer.py
# 신규: specs/001-overlap-analyzer-v5/generated/ 폴더
```

#### Phase 3: 선택적 교체
```powershell
# 만족스러우면 기존 파일을 overlap_analyzer_legacy.py로 백업
# SDD 생성 코드를 overlap_analyzer.py로 교체
```

---

## 💡 SDD 적용의 장점 (OverlapAnalyzer 케이스)

### 🎯 **1. 정확한 명세서**
```
기존: 마크다운 설계서 → 구현 시 해석 차이 발생 가능
SDD: 실행 가능한 명세서 → 코드 자동 생성으로 일관성 보장
```

### 🧪 **2. 테스트 우선 개발**
```
기존: 구현 후 테스트 작성
SDD: 명세서 → 테스트 코드 → 구현 코드 순서 강제
```

### 📊 **3. 5가지 상태 정확성**
```
기존: 복잡한 if-else 로직으로 상태 분류 오류 가능성
SDD: 명세서에서 정의된 정확한 상태 트리 구조 자동 구현
```

### 🔧 **4. Repository 확장 자동화**
```
기존: 수동으로 has_data_at_time(), find_data_start_in_range() 구현
SDD: 명세서에서 필요한 Repository 메서드 자동 식별 및 생성
```

### 🎨 **5. DDD 계층 준수 자동 검증**
```
기존: 수동으로 계층 간 의존성 확인
SDD: Constitutional rules로 DDD 원칙 위반 자동 탐지
```

---

## 🔧 실제 명령어 시퀀스

```powershell
# 1. 현재 위치에서 SDD 초기화
cd d:\projects\upbit-autotrader-vscode
uvx --from git+https://github.com/github/spec-kit.git specify init .

# 2. OverlapAnalyzer 명세 작성
# (위의 /specify 명령 실행)

# 3. 구현 계획 수립
# (위의 /plan 명령 실행)

# 4. 태스크 분해
# (위의 /tasks 명령 실행)

# 5. 단계별 구현 진행
# 각 태스크별로 승인/수정/중단 선택
```

---

## ✅ 예상 결과

### 📁 **생성될 폴더 구조**
```
specs/001-overlap-analyzer-v5/
├── feature-spec.md                    # 5가지 상태 분류 명세
├── implementation-plan.md             # Repository 확장 계획
├── implementation-details/
│   ├── 00-research.md                 # SQLite 최적화 연구
│   ├── 02-data-model.md              # OverlapRequest/Result 정의
│   ├── 03-api-contracts.md           # Repository 인터페이스 확장
│   ├── 06-contract-tests.md          # 5가지 상태 테스트 시나리오
│   └── 08-inter-library-tests.md    # Repository 통합 테스트
├── manual-testing.md                  # 수동 검증 절차
└── generated/                         # SDD 생성 코드
    ├── overlap_analyzer_v5.py
    ├── test_overlap_analyzer_v5.py
    └── repository_extensions.py
```

### 🎯 **핵심 이점**
1. **비침습적**: 기존 코드 1바이트도 건드리지 않음
2. **점진적**: 새 컴포넌트만 SDD로 실험
3. **비교 가능**: 기존 vs SDD 구현 성능/품질 비교
4. **롤백 용이**: `specs/` 폴더만 삭제하면 완전 제거

---

## 🧪 예상 SDD 생성 결과물

### 📊 **1. 정확한 5가지 상태 분류**
```python
class OverlapStatus(Enum):
    """SDD로 생성된 정확한 5개 상태 분류"""
    NO_OVERLAP = "no_overlap"
    COMPLETE_OVERLAP = "complete_overlap"
    PARTIAL_START = "partial_start"
    PARTIAL_MIDDLE_FRAGMENT = "partial_middle_fragment"
    PARTIAL_MIDDLE_CONTINUOUS = "partial_middle_continuous"
```

### 🔧 **2. Repository 확장 메서드**
```python
# SDD가 자동 생성할 Repository 확장
async def has_data_at_time(self, symbol: str, timeframe: str, target_time: datetime) -> bool:
    """특정 시점 데이터 존재 확인 (PRIMARY KEY 최적화)"""

async def find_data_start_in_range(self, symbol: str, timeframe: str,
                                  start_time: datetime, end_time: datetime) -> Optional[datetime]:
    """범위 내 데이터 시작점 찾기 (MAX 쿼리 + 업비트 내림차순 특성 반영)"""
```

### 🧪 **3. 5가지 상태별 테스트**
```python
# SDD가 자동 생성할 테스트 케이스
class TestOverlapAnalyzerV5:
    async def test_no_overlap(self):           # |------|
    async def test_complete_overlap(self):     # |111111|
    async def test_partial_start(self):        # |11----|
    async def test_partial_middle_fragment(self):   # |--1-11|
    async def test_partial_middle_continuous(self): # |--1111|
```

### ⚡ **4. 성능 최적화된 알고리즘**
```python
# SDD가 자동 생성할 단계별 조기 종료 로직
async def analyze_overlap(self, request: OverlapRequest) -> OverlapResult:
    # 1. LIMIT 1 쿼리로 겹침 없음 조기 판단
    # 2. COUNT 쿼리로 완전 겹침 조기 판단
    # 3. 시작점 확인 후 분기 처리
    # 4. 중간 겹침 세부 분류
```

---

## 🎯 성공 지표

### ✅ **기술적 성공 지표**
1. **5가지 상태 정확성**: 모든 DB 패턴을 올바르게 분류
2. **성능 향상**: 기존 대비 쿼리 실행 시간 단축
3. **테스트 커버리지**: 100% 상태 분류 테스트 통과
4. **DDD 준수**: Infrastructure 계층 완벽 격리

### 📊 **비즈니스 성공 지표**
1. **개발 속도**: 명세서 작성 → 구현 완료까지 시간 단축
2. **버그 감소**: 테스트 우선 개발로 상태 분류 오류 제거
3. **유지보수성**: 명세서-코드 동기화로 변경 관리 용이성
4. **확장성**: 새로운 겹침 패턴 추가 시 명세서만 수정

---

## 🔧 실제 시작 가이드

### 💾 **백업 먼저**
```powershell
# 1. 현재 프로젝트 백업 (안전장치)
git add -A
git commit -m "SDD 실험 전 OverlapAnalyzer 백업"
```

### 🚀 **SDD 실험 시작**
```powershell
# 2. SDD 초기화 및 OverlapAnalyzer 명세 작성
cd d:\projects\upbit-autotrader-vscode
uvx --from git+https://github.com/github/spec-kit.git specify init .
# 이후 /specify, /plan, /tasks 명령어 순차 실행
```

### 🔄 **결과 비교**
```powershell
# 3. 기존 vs SDD 구현 비교 테스트
python -m pytest tests/infrastructure/market_data/candle/test_overlap_analyzer.py  # 기존
python -m pytest specs/001-overlap-analyzer-v5/generated/test_overlap_analyzer_v5.py  # SDD
```

### 📊 **선택적 적용**
```powershell
# 4-A. 만족스러우면 교체
mv upbit_auto_trading/infrastructure/market_data/candle/overlap_analyzer.py overlap_analyzer_legacy.py
cp specs/001-overlap-analyzer-v5/generated/overlap_analyzer_v5.py overlap_analyzer.py

# 4-B. 불만족스러우면 롤백
git reset --hard HEAD  # 완전 롤백
Remove-Item -Recurse -Force specs/  # SDD 폴더 제거
```

---

## 📋 결론

**OverlapAnalyzer v5.0에 SDD를 적용**하면:

1. **리스크 제로**: 기존 구현 건드리지 않고 병렬 개발
2. **품질 향상**: 테스트 우선 + 명세서 기반 정확성 보장
3. **성능 최적화**: 체계적인 쿼리 최적화 전략 자동 적용
4. **학습 기회**: 새로운 개발 방법론 안전하게 실험

**첫 번째 SDD 실험 대상으로 OverlapAnalyzer가 최적**인 이유:
- 명확한 입출력 인터페이스 (OverlapRequest → OverlapResult)
- 구체적인 상태 분류 (5가지 케이스)
- 기존 상세 설계서 존재 (OVERLAP_ANALYZER_V5_SIMPLIFIED_DESIGN.md)
- 독립적인 컴포넌트로 실험 영향 최소화

지금 바로 시작해서 SDD의 효과를 직접 경험해보세요! 🚀

---

## 📚 관련 문서

- [OVERLAP_ANALYZER_V5_SIMPLIFIED_DESIGN.md](../../upbit_auto_trading/infrastructure/market_data/candle/OVERLAP_ANALYZER_V5_SIMPLIFIED_DESIGN.md) - 기존 상세 설계서
- [GITHUB_SPEC_KIT_ANALYSIS_GUIDE.md](./GITHUB_SPEC_KIT_ANALYSIS_GUIDE.md) - GitHub Spec Kit 전체 분석
- [GitHub Spec Kit 공식 리포지토리](https://github.com/github/spec-kit)
