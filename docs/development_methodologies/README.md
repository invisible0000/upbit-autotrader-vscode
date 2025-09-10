# 📚 Development Methodologies 문서 인덱스

> 업비트 자동매매 프로젝트의 개발 방법론 관련 문서 모음
>
> 경로: `docs/development_methodologies/`
> 최종 업데이트: 2025년 9월 10일

---

## 📋 문서 목록

### 🌱 **Specification-Driven Development (SDD)**

#### 1. [GitHub Spec Kit 분석 및 활용 가이드](./GITHUB_SPEC_KIT_ANALYSIS_GUIDE.md)
- **개요**: GitHub Spec Kit과 SDD 방법론 전체 분석
- **내용**:
  - SDD 핵심 개념과 권력의 역전 (Power Inversion)
  - 4단계 워크플로우 (설치 → 명세 → 계획 → 구현)
  - 업비트 프로젝트와의 호환성 분석
  - 단계별 도입 전략 (Phase 1~3)
- **대상**: 프로젝트 리더, 아키텍트, 개발 방법론에 관심 있는 개발자

#### 2. [OverlapAnalyzer SDD 적용 가이드](./OVERLAP_ANALYZER_SDD_APPLICATION_GUIDE.md)
- **개요**: 현재 개발 중인 OverlapAnalyzer v5.0에 SDD 적용 방안
- **내용**:
  - 특정 컴포넌트 단위 SDD 적용 전략
  - 기존 설계서와 SDD 명세서 연동 방법
  - 점진적 통합 전략 (병렬 개발 → 비교 → 선택적 교체)
  - 실제 명령어 시퀀스와 예상 결과물
- **대상**: OverlapAnalyzer 개발자, SDD 실험에 관심 있는 개발자

---

## 🎯 활용 시나리오

### 🚀 **SDD 도입을 고려 중인 경우**
1. **[GitHub Spec Kit 분석 가이드](./GITHUB_SPEC_KIT_ANALYSIS_GUIDE.md)** 먼저 읽기
2. SDD 개념과 이점 파악
3. 프로젝트 적합성 평가

### 🔧 **특정 컴포넌트에 SDD 적용하려는 경우**
1. **[OverlapAnalyzer SDD 적용 가이드](./OVERLAP_ANALYZER_SDD_APPLICATION_GUIDE.md)** 참조
2. 컴포넌트별 적용 전략 수립
3. 점진적 실험 및 비교

### 📊 **전체 프로젝트 SDD 전환을 계획하는 경우**
1. 두 문서 모두 검토
2. Phase별 도입 계획 수립
3. 위험 평가 및 롤백 전략 준비

---

## 🔗 관련 리소스

### 📖 **외부 문서**
- [GitHub Spec Kit 공식 리포지토리](https://github.com/github/spec-kit)
- [Specification-Driven Development 상세 가이드](https://github.com/github/spec-kit/blob/main/spec-driven.md)

### 🏗️ **프로젝트 내 관련 문서**
- [DDD 아키텍처 패턴 가이드](../DDD_아키텍처_패턴_가이드.md)
- [개발 방법론 완전 가이드](../개발%20방법론%20완전%20가이드.md)
- [OverlapAnalyzer v5.0 설계서](../../upbit_auto_trading/infrastructure/market_data/candle/OVERLAP_ANALYZER_V5_SIMPLIFIED_DESIGN.md)

### 🎨 **Copilot Instructions 연동**
- [.github/copilot-instructions.md](../../.github/copilot-instructions.md) - Ryan-Style 3-Step 프로세스와 SDD 통합 가능

---

## 📝 문서 작성 기준

### ✅ **작성 원칙**
- **실용성 우선**: 이론보다 실제 적용 방법에 집중
- **점진적 접근**: 급진적 변화보다 안전한 실험 우선
- **롤백 가능**: 모든 변경사항이 되돌릴 수 있도록 설계
- **비침습적**: 기존 시스템에 최소한의 영향

### 📊 **문서 구조**
- **개요**: 목적과 대상 명시
- **단계별 가이드**: 실행 가능한 단계별 지침
- **코드 예시**: 실제 명령어와 예상 결과
- **위험 관리**: 롤백 전략과 안전장치
- **관련 문서**: 추가 참조 자료 링크

---

## 🔄 업데이트 이력

| 날짜 | 문서 | 변경사항 |
|------|------|----------|
| 2025-09-10 | 전체 | 초기 문서 세트 생성 |
| 2025-09-10 | GitHub Spec Kit 분석 가이드 | SDD 방법론 전체 분석 완료 |
| 2025-09-10 | OverlapAnalyzer SDD 적용 가이드 | 특정 컴포넌트 적용 방안 완료 |

---

## 💬 피드백 및 기여

### 📋 **문서 개선 요청**
- 불명확한 설명이나 누락된 정보 발견 시 이슈 등록
- 실제 적용 과정에서의 경험과 결과 공유
- 추가 필요한 가이드나 시나리오 제안

### 🔧 **실험 결과 공유**
- SDD 적용 실험 결과 (성공/실패 사례)
- 성능 비교 데이터
- 개발 생산성 변화 측정 결과

SDD 도입으로 **더 나은 개발 경험과 품질 향상**을 함께 만들어가요! 🚀
