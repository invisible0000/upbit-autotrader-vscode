# 📋 GitHub Spec Kit 분석 및 활용 가이드

> Specification-Driven Development (SDD) 방법론 도입을 위한 완전 가이드
>
> 작성일: 2025년 9월 10일
> 대상: 업비트 자동매매 프로젝트 개발팀

---

## 🌱 GitHub Spec Kit 개요

GitHub Spec Kit은 **Specification-Driven Development (SDD)**라는 혁신적인 개발 방법론을 구현한 도구입니다. 이는 기존의 코드 중심 개발을 뒤집어서 **명세서가 코드를 생성하는** 새로운 패러다임을 제시합니다.

### 🎯 핵심 개념: 권력의 역전 (Power Inversion)

**기존 방식**: 코드가 왕 → 명세서는 코드를 위한 가이드
**SDD 방식**: 명세서가 왕 → 코드는 명세서의 구현체

이는 단순한 개선이 아닌 **근본적인 패러다임 전환**입니다.

---

## 🔄 SDD 워크플로우 4단계

### 1. 설치 및 초기화
```bash
uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>
```

### 2. 명세서 작성 (`/specify` 명령)
```
/specify 사진을 날짜별 앨범으로 정리할 수 있는 애플리케이션을 만들어 주세요.
앨범은 드래그 앤 드롭으로 재정렬 가능하고, 각 앨범 내에서는 타일 형태로 사진을 미리볼 수 있습니다.
```
- **What과 Why에 집중**, How는 배제
- 비즈니스 요구사항을 자연어로 표현

### 3. 기술 구현 계획 (`/plan` 명령)
```
/plan Vite를 사용하고 최소한의 라이브러리로 구성합니다.
가능한 한 바닐라 HTML, CSS, JavaScript를 사용하고,
이미지는 업로드하지 않으며 메타데이터는 로컬 SQLite에 저장합니다.
```
- 기술 스택과 아키텍처 결정사항 명시
- 제약사항과 비기능적 요구사항 포함

### 4. 태스크 분해 및 구현 (`/tasks` 명령)
- 실행 가능한 태스크 리스트 생성
- AI가 단계별로 구현 진행

---

## 🏗️ 업비트 자동매매 프로젝트에서의 활용 방안

### 1. **기존 아키텍처와의 호환성**
현재 프로젝트의 DDD + MVP 아키텍처와 SDD가 완벽하게 조화됩니다:

- **Domain Layer**: 비즈니스 규칙을 명세서로 표현
- **Application Layer**: UseCase를 명세서에서 자동 생성
- **Infrastructure Layer**: 기술적 제약사항을 구현 계획에 반영

### 2. **7규칙 전략 개발에 적용**
```
/specify RSI 과매도 진입, 수익시 불타기, 계획된 익절, 트레일링 스탑,
하락시 물타기, 급락 감지, 급등 감지로 구성된 7규칙 자동매매 전략을 구현해 주세요.

/plan PyQt6 UI, 3-DB 분리 (settings/strategies/market_data),
Dry-Run 기본값, Infrastructure 로깅 시스템을 사용합니다.
```

### 3. **품질 보장 메커니즘**
SDD의 템플릿 기반 접근법이 프로젝트의 품질 기준을 자동으로 적용:

- **Constitutional Compliance**: 아키텍처 원칙 자동 검증
- **Test-First**: 테스트 우선 개발 강제
- **Clarity Markers**: `[NEEDS CLARIFICATION]` 마커로 모호함 명시

---

## 🎨 업비트 프로젝트 통합 전략

### Phase 1: 실험적 도입
1. **새로운 기능 개발**에만 SDD 적용
   - 예: 새로운 기술적 지표 추가
   - 예: UI 컴포넌트 확장

### Phase 2: 기존 기능 리팩터링
1. **복잡한 컴포넌트**를 SDD로 재구현
   - 예: 전략 엔진 최적화
   - 예: 실시간 데이터 처리 로직

### Phase 3: 전면 적용
1. **아키텍처 전체**를 SDD 기반으로 재설계
   - 명세서 기반 코드 생성
   - 지속적인 명세서-코드 동기화

---

## 💡 주요 이점

1. **명세서-코드 동기화**: 요구사항 변경 시 자동으로 코드 업데이트
2. **아키텍처 일관성**: Constitutional rules로 DDD 원칙 자동 준수
3. **품질 보장**: 테스트 우선, 명확성 마커 등으로 코드 품질 향상
4. **빠른 프로토타이핑**: 아이디어에서 작동하는 코드까지 몇 시간
5. **병렬 구현**: 동일 명세서에서 다양한 기술 스택으로 구현 탐색

---

## 🗑️ 제거 및 롤백 용이성

### **완전히 독립적인 도구**
Spec Kit은 기존 프로젝트를 수정하지 않고 별도로 작동합니다:
- 기존 코드베이스에 의존성 추가 없음
- 프로젝트 구조 변경 없음
- 설정 파일 수정 없음

### **간단한 제거 과정**

#### Option A: 완전 제거
```powershell
# 1. Spec Kit으로 생성된 프로젝트 폴더만 삭제
Remove-Item -Recurse -Force "생성된_프로젝트_폴더"

# 2. uv 캐시에서 제거 (선택사항)
uvx --help  # uv가 설치되어 있다면
```

#### Option B: 일시 중단
```powershell
# 생성된 specs/ 폴더만 임시로 이동
Move-Item "specs" "specs_backup"
```

### **기존 프로젝트에 미치는 영향: 0**

현재 업비트 자동매매 프로젝트는:
- ✅ 그대로 유지됨
- ✅ 기존 copilot-instructions.md 그대로
- ✅ 모든 설정과 코드 변경 없음
- ✅ DDD 아키텍처 그대로

---

## 🚀 시작 제안

지금 당장 시작할 수 있는 방법:

1. **Spec Kit 설치** 후 작은 기능 하나로 실험
2. **기존 copilot-instructions.md**와 SDD 원칙 통합
3. **Ryan-Style 3-Step 프로세스**에 SDD 명령어 추가
4. **점진적 확장**으로 전체 프로젝트에 적용

---

## 📋 결론

SDD는 당신의 업비트 자동매매 프로젝트를 **명세서 중심의 지속 가능한 시스템**으로 진화시킬 수 있는 강력한 도구입니다. 특히 복잡한 금융 로직과 안전성이 중요한 거래 시스템에서 명세서의 정확성과 추적 가능성은 매우 큰 가치를 제공할 것입니다.

**핵심**: 기존 프로젝트에 어떤 흔적도 남기지 않으므로 **부담 없이 실험**할 수 있습니다!

---

## 📚 관련 문서

- [GitHub Spec Kit 공식 리포지토리](https://github.com/github/spec-kit)
- [Specification-Driven Development 상세 가이드](https://github.com/github/spec-kit/blob/main/spec-driven.md)
- [OverlapAnalyzer SDD 적용 가이드](./OVERLAP_ANALYZER_SDD_APPLICATION_GUIDE.md)
