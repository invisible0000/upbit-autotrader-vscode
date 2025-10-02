# 문서 자산 분류 & 초기 인벤토리 (v0.1)

본 문서는 `docs/` 내 문서들을 유형/권위/신선도 관리 대상으로 체계화하기 위한 분류 기준과 1차 샘플 인벤토리를 제공합니다.

## 1. 분류 체계 개요

| 속성 | 설명 | 값 정의 |
|------|------|----------|
| type | 문서 1차 목적 | architecture / strategy / operations / process / guide / reference / spec / security / glossary |
| authoritative | 시스템 규칙의 "단일 진실" 여부 | true / false |
| lifecycle | 유지 전략 | active / legacy / deprecated / experimental |
| freshness_target_days | 재검토 주기 기준 | 정수 (기본 30) |
| last_reviewed | 마지막 검토 일자 | ISO8601 (없으면 NULL) |
| owner | 책임자 또는 팀 | ex) architecture-team |

### 1.1 Authoritative 판정 기준

아래 중 2개 이상 해당 시 authoritative=true 권장:

- 실행/코드가 의존하는 공식 규칙 정의 (예: DDD 계층 규칙)
- 보안/자금/거래 안전 관련 필수 정책
- 전략 실행 파라미터 표준화 근거 제공
- CI 또는 스크립트에서 참조 가능 구조

### 1.2 Legacy / Deprecated 구분

- legacy: 과거 참조용, 개념은 유효하나 최신 반영 아님
- deprecated: 사용 금지 안내 필요, 대체 문서 명시

## 2. 메타데이터 권장 Front-Matter 예시

```markdown
---
type: architecture
authoritative: true
lifecycle: active
freshness_target_days: 30
last_reviewed: 2025-10-01
owner: architecture-team
---
```

## 3. 초기 스캔 샘플 (부분) — 상세 자동화는 `doc_freshness_scan.py`에서 추출 예정

| 경로 | 추정 type | authoritative | lifecycle | last_reviewed | owner | 비고 |
|------|-----------|--------------|-----------|---------------|-------|------|
| docs/ARCHITECTURE_GUIDE.md | architecture | true (후보) | active | (missing) | (missing) | 핵심 아키텍처 설명 |
| docs/MVP_ARCHITECTURE.md | architecture | false | legacy | (missing) | (missing) | 통합가이드 중복 가능성 |
| docs/DDD_Ubiquitous_Language_Dictionary.md | glossary | true (후보) | active | (missing) | (missing) | 용어 표준 |
| docs/STRATEGY_GUIDE.md | strategy | true (후보) | active | (missing) | (missing) | 전략 구성 원칙 |
| docs/BASIC_7_RULE_STRATEGY_GUIDE.md | strategy | true (후보) | active | (missing) | (missing) | 7규칙 핵심 |
| docs/COMPLEX_SYSTEM_TESTING_GUIDE.md | process | false | active | (missing) | qa-team? | 복잡 시스템 테스트 |
| docs/DEPENDENCY_INJECTION_ARCHITECTURE.md | architecture | true (후보) | active | (missing) | (missing) | DI 구조 |
| docs/UNIFIED_CONFIGURATION_MANAGEMENT_GUIDE.md | operations | true (후보) | active | (missing) | (missing) | 설정 통합 |
| docs/UI_GUIDE.md | guide | false | active | (missing) | (missing) | UI 사용 패턴 |
| docs/TRIGGER_BUILDER_GUIDE.md | guide | false | active | (missing) | (missing) | 빌더 사용법 |

초기 표는 우선순위 선별을 위한 seed이며, authoritative 후보 문서는 front-matter 추가 우선 대상.

## 4. 1차 액션 추천 (우선순위)

| 우선순위 | 액션 | 근거 |
|----------|------|------|
| P1 | ARCHITECTURE_GUIDE.md front-matter 추가 | 아키텍처 규칙 단일 출처 명확화 |
| P1 | STRATEGY_GUIDE.md + BASIC_7_RULE_STRATEGY_GUIDE.md 메타 추가 | 전략 규칙 근거 확립 |
| P2 | DDD_Ubiquitous_Language_Dictionary.md 메타 추가 | 용어 표준화 추적 |
| P2 | DEPENDENCY_INJECTION_ARCHITECTURE.md 메타 추가 | 레이어/DI 설계 기준 |
| P3 | legacy/중복 문서 정리 계획 수립 | 탐색 비용 감소 |

## 5. 다음 단계 연계

1. `doc_freshness_scan.py` 구현 → missing 메타 자동 감지
2. drift_matrix 작성 시작 (권위 문서 중 실코드 괴리 의심 항목)
3. PR 템플릿에 "Authoritative 문서 변경 시 last_reviewed 갱신" 체크박스 추가 제안

---
작성: 자동화 준비 단계 v0.1 (수동 seed)
향후: 스크립트 생성 output으로 재생성 예정
