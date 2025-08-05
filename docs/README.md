# 📚 업비트 자동매매 시스템 문서 가이드

## 🎯 문서 체계 개요

이 폴더는 업비트 자동매매 시스템의 모든 개발 지침과 명세를 포함합니다.
**LLM 에이전트와 개발자 모두를 위한 효율적인 문서 구조**로 설계되었습니다.

### 📋 문서 읽기 순서 (권장)

1. **[프로젝트 명세](PROJECT_SPECIFICATIONS.md)** ← 모든 개발의 기준
2. **[개발 체크리스트](DEV_CHECKLIST.md)** ← 개발 검증 기준
3. **[아키텍처 개요](ARCHITECTURE_OVERVIEW.md)** ← 시스템 구조 이해
4. **해당 작업 영역의 전문 문서들**

## 📊 핵심 문서 (필수 숙지)

### 🎯 개발 지침
- **[PROJECT_SPECIFICATIONS.md](PROJECT_SPECIFICATIONS.md)**: 프로젝트 핵심 명세 (105줄)
- **[DEV_CHECKLIST.md](DEV_CHECKLIST.md)**: 개발 검증 체크리스트 (168줄)
- **[STYLE_GUIDE.md](STYLE_GUIDE.md)**: 코딩 스타일 가이드 (152줄)
- **[ERROR_HANDLING_POLICY.md](ERROR_HANDLING_POLICY.md)**: 오류 처리 정책 (118줄)
- **[LLM_DOCUMENTATION_GUIDELINES.md](LLM_DOCUMENTATION_GUIDELINES.md)**: LLM 최적화 문서 작성법 (NEW!)

### 🏗️ 시스템 아키텍처
- **[ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)**: 시스템 개요 (248줄)
- **[COMPONENT_ARCHITECTURE.md](COMPONENT_ARCHITECTURE.md)**: 컴포넌트 설계 (247줄)
- **[DB_SCHEMA.md](DB_SCHEMA.md)**: 데이터베이스 스키마 (241줄)

### ⚙️ 핵심 기능
- **[TRIGGER_BUILDER_GUIDE.md](TRIGGER_BUILDER_GUIDE.md)**: 트리거 빌더 (219줄)
- **[STRATEGY_SYSTEM.md](STRATEGY_SYSTEM.md)**: 매매 전략 시스템 (259줄)
- **[VARIABLE_COMPATIBILITY.md](VARIABLE_COMPATIBILITY.md)**: 변수 호환성 (156줄)

### 🎨 UI/UX
- **[UI_DESIGN_SYSTEM.md](UI_DESIGN_SYSTEM.md)**: UI 디자인 시스템 (202줄)

## 🎯 작업별 문서 가이드

### 📈 매매 전략 개발 시
```
1. STRATEGY_SYSTEM.md (전체 전략 시스템 이해)
2. BASIC_7_RULE_STRATEGY_GUIDE.md (검증 기준)
3. TRIGGER_BUILDER_GUIDE.md (조건 구성)
4. VARIABLE_COMPATIBILITY.md (변수 호환성)
```

### 🎨 UI 개발 시
```
1. UI_DESIGN_SYSTEM.md (디자인 원칙)
2. COMPONENT_ARCHITECTURE.md (컴포넌트 구조)
3. STYLE_GUIDE.md (코딩 스타일)
```

### 💾 데이터베이스 작업 시
```
1. DB_SCHEMA.md (스키마 정의)
2. ARCHITECTURE_OVERVIEW.md (3-DB 구조)
3. TRADING_VARIABLES_COMPACT.md (변수 정의)
```

### 🔧 백엔드 개발 시
```
1. COMPONENT_ARCHITECTURE.md (시스템 구조)
2. ERROR_HANDLING_POLICY.md (오류 처리)
3. STYLE_GUIDE.md (코딩 표준)
4. INFRASTRUCTURE_SMART_LOGGING_GUIDE.md (스마트 로깅 시스템)
```

### 🔍 Infrastructure Layer 개발 시
```
1. INFRASTRUCTURE_SMART_LOGGING_GUIDE.md (스마트 로깅 시스템 - 개발 첫 단계)
2. LLM_LOG_SEPARATION_GUIDE.md (LLM 로그 분리 시스템 - 사람/LLM 로그 구분)
3. COMPONENT_ARCHITECTURE.md (DDD 기반 아키텍처)
4. ERROR_HANDLING_POLICY.md (에러 처리 정책)
5. DEV_CHECKLIST.md (개발 검증)
```

## 📝 특별 문서들

### 기본 7규칙 전략 (검증 기준)
- **[BASIC_7_RULE_STRATEGY_GUIDE.md](BASIC_7_RULE_STRATEGY_GUIDE.md)**: 모든 개발의 검증 기준

### 참고/학습 문서
- **[TRADING_VARIABLES_COMPACT.md](TRADING_VARIABLES_COMPACT.md)**: 매매 변수 정의
- **[STRATEGY_SPECIFICATIONS.md](STRATEGY_SPECIFICATIONS.md)**: 전략 상세 명세
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: 기여 가이드

## 🔍 문서 특징

### ✅ LLM 최적화
- **간결성**: 평균 150줄, 최대 250줄
- **구조화**: 목차와 섹션 구분 명확
- **참조성**: 관련 문서 상호 링크
- **실용성**: 코드 예시와 실행 가능한 지침

### ✅ 개발자 친화적
- **검색성**: 명확한 제목과 키워드
- **완결성**: 각 문서가 독립적으로 완전한 정보 제공
- **실행성**: 바로 사용 가능한 코드와 명령어
- **검증성**: 체크리스트와 검증 기준 제공

## 🚀 빠른 시작 가이드

### 새로운 개발자라면
```markdown
1. PROJECT_SPECIFICATIONS.md 읽기 (20분)
2. ARCHITECTURE_OVERVIEW.md 스캔 (10분)
3. DEV_CHECKLIST.md 북마크 (5분)
4. 작업 영역별 전문 문서 참조
```

### LLM 에이전트라면
```markdown
1. PROJECT_SPECIFICATIONS.md로 프로젝트 컨텍스트 파악
2. 작업 유형에 따른 관련 문서 로드
3. DEV_CHECKLIST.md로 결과물 검증
4. STYLE_GUIDE.md로 코드 품질 확인
```

### 특정 기능 구현 시
```markdown
1. 해당 기능의 전문 문서 먼저 읽기
2. COMPONENT_ARCHITECTURE.md에서 구조 확인
3. 구현 후 DEV_CHECKLIST.md로 검증
4. 기본 7규칙 전략으로 동작 확인
```

### 리팩토링 계획 수립 시
```markdown
1. refactoring_plan/README.md로 전체 개요 파악
2. 현재 아키텍처 분석 문서로 현황 진단
3. 전문가 설계 문서로 목표 아키텍처 이해
4. 실행 계획 문서로 단계별 로드맵 수립
```

## 📚 레거시 문서 관리

### 통합 완료
- `.vscode/` 폴더 내용 → docs 폴더로 통합
- 중복 제거 및 내용 현행화 완료
- 47개 분산 문서 → 18개 핵심 문서로 압축

### 이전 위치 (참고만)
```
legacy_long_docs/        # 긴 문서들 (300줄+)
data_info/               # 데이터 정의 파일들 (.yaml, .sql)
docs/legacy/             # 이전 버전 문서들
```

## 💡 문서 활용 팁

### 🔍 빠른 검색
- **Ctrl+Shift+F**: 전체 docs 폴더에서 키워드 검색
- **파일명 패턴**: 대문자_언더스코어 형식으로 쉬운 식별
- **섹션 참조**: `[문서명](파일명.md)`로 빠른 이동

### 📋 체크리스트 활용
- 개발 전: 관련 문서 체크리스트 확인
- 개발 중: STYLE_GUIDE.md 수시 참조
- 개발 후: DEV_CHECKLIST.md로 품질 검증
- 배포 전: 기본 7규칙 전략으로 동작 검증

### 📝 문서 작성 시
- 새 문서 작성: LLM_DOCUMENTATION_GUIDELINES.md 참조
- LLM 최적화: 150-200줄 목표, 구조적 마커 활용
- 토큰 효율성: 핵심 키워드 상단 배치, 예시 코드 포함
- 일관성 유지: 용어 통일, 참조 체계 준수

### 🔄 문서 갱신 방식
- 주요 변경사항은 관련 문서에 즉시 반영
- 월 1회 전체 문서 정합성 검토
- 새로운 기능 추가 시 해당 문서 섹션 확장

---

**💡 핵심 원칙**: "모든 개발은 문서 기반으로, 모든 문서는 실행 가능하게!"

**🎯 기억할 것**: 의심스러우면 `PROJECT_SPECIFICATIONS.md`와 `DEV_CHECKLIST.md`로 돌아가기!

### 트리거 빌더
- **3중 카테고리**: purpose_category, chart_category, comparison_group
- **호환성 검증**: 실시간 변수 호환성 확인
- **드래그앤드롭**: 직관적인 조건 조합

## 🚀 빠른 시작

### 설치 및 실행
```powershell
# 1. 저장소 클론
git clone https://github.com/invisible0000/upbit-autotrader-vscode.git
cd upbit-autotrader-vscode

# 2. 가상환경 설정
python -m venv venv
venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 실행
python run_desktop_ui.py
```

## 📁 문서 구조

### 📋 핵심 명세서 (5개)
- **[기본 7규칙 전략](BASIC_7_RULE_STRATEGY_GUIDE.md)**: 필수 구현 목표 ⭐
- **[프로젝트 명세서](PROJECT_SPECIFICATIONS.md)**: 전체 시스템 개요
- **[아키텍처 개요](ARCHITECTURE_OVERVIEW.md)**: 시스템 구조와 설계 원칙
- **[전략 명세서](STRATEGY_SPECIFICATIONS.md)**: 진입/관리 전략 상세
- **[DB 스키마](DB_SCHEMA.md)**: 3-DB 아키텍처 구조

### 🛠️ 개발 가이드 (7개)
- **[개발 가이드](DEVELOPMENT_GUIDE_COMPACT.md)**: 빠른 시작과 핵심 패턴
- **[트리거 빌더 가이드](TRIGGER_BUILDER_GUIDE.md)**: 조건 생성 시스템 상세
- **[변수 호환성](VARIABLE_COMPATIBILITY.md)**: 호환성 검증 시스템
- **[트레이딩 변수](TRADING_VARIABLES_COMPACT.md)**: 변수 관리 시스템
- **[기여 가이드](CONTRIBUTING.md)**: 협업 규칙과 검증 기준
- **[스타일 가이드](STYLE_GUIDE.md)**: 코딩 표준
- **[개발 체크리스트](DEV_CHECKLIST.md)**: 필수 확인 사항

### 🔧 운영/설치 가이드 (5개)
- **[GitHub Clone 문제해결](GITHUB_CLONE_TROUBLESHOOTING.md)**: 설치 문제 해결
- **[DB 마이그레이션](DB_MIGRATION_USAGE_GUIDE.md)**: 데이터베이스 관리
- **[시작 가이드](README_FIRST.md)**: 처음 사용자용
- **[룰 빌더 실습](RULE_BUILDER_PRACTICE_GUIDE.md)**: UI 사용법

### �️ 리팩토링 계획 (4개)
- **[리팩토링 계획 가이드](refactoring_plan/README.md)**: 리팩토링 계획 수립 문서들
- **[현재 아키텍처 분석](refactoring_plan/01_CURRENT_ARCHITECTURE_ANALYSIS.md)**: 현재 상황 진단
- **[전문가 설계 종합](refactoring_plan/02_EXPERT_DESIGN_SYNTHESIS.md)**: 이상적 아키텍처
- **[리팩토링 실행 계획](refactoring_plan/03_EXPERT_REFACTORING_SYNTHESIS.md)**: 단계별 로드맵

### �📦 Legacy 문서
긴 문서들과 구버전 내용은 `legacy_long_docs/` 폴더에 보관

## 🎯 프로토타입 테스트 방법

```bash
# 프로토타입 실행 (각각 독립 실행 가능)
cd ui_prototypes
python drag_drop_vs_button_comparison.py
python enhanced_strategy_builder.py
python rule_based_strategy_maker.py
# ... 등등
```

## 🤔 선택 기준

각 프로토타입의 특징:

1. **간단함**: `rule_based_strategy_maker.py` - 7개 템플릿 선택
2. **유연성**: `enhanced_strategy_builder.py` - 세밀한 설정
3. **직관성**: `table_strategy_builder.py` - 스프레드시트 스타일
4. **통합성**: `unified_strategy_system_v2.py` - 모든 기능 통합

## 🚀 다음 단계

1. 각 프로토타입 실행해보기
2. UX 비교 분석
3. 최적 방식 선택
4. 실제 시스템에 적용
