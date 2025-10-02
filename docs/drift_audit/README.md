# 문서-구현 드리프트 감시 (Documentation ↔ Implementation Drift Audit)

본 폴더는 프로젝트 내 문서와 실제 코드/구현 상태 사이의 불일치(드리프트)를 **지속적으로 탐지·분류·해결**하기 위한 시스템 자산을 보관합니다.

## 🎯 목적 (Charter)

문서에 선언된 아키텍처/규칙/프로세스가 실제 코드에 반영되어 있는지 주기적으로 검증
고위험(보안, 자금, 전략 로직) 드리프트를 조기 경보
유지보수 우선순위 선정을 위한 정량 지표(Drift Score) 생성
신규 기여자가 신뢰 가능한 "권위 문서(Authoritative Docs)" 세트를 빠르게 파악하도록 지원

## ✅ 범위

| 카테고리 | 포함 | 제외(초기 단계) |
|----------|------|-----------------|
| 아키텍처 계층 | DDD 레이어 경계, Domain 순수성 | 성능 마이크로 튜닝 |
| 데이터 스키마 | 3-DB (settings / strategies / market_data) 구조 | 외부 백업/보조 캐시 |
| 전략 로직 | 7 규칙 전략 선언 vs 실제 UseCase/Trigger 구성 | 실험적 / 비활성 전략 |
| 보안/안전 | Dry-Run 정책, API 키 처리, 로깅 금지 패턴 | 배포 파이프라인 세부 |
| 문서 메타 | last_reviewed, owner, authoritative 플래그 | 번역본 동기화 |

## ⚠️ 위험 정의

| 위험 수준 | 설명 | 예시 |
|-----------|------|------|
| Critical | 자금 손실 또는 개인정보/키 노출 가능 | Dry-run 기본 False, API 키 plaintext |
| High | 전략 오작동/잘못된 매매 의사결정 | RSI 규칙 문서와 파라미터 다름 |
| Medium | 혼선 유발, 신규 온보딩 지연 | 오래된 아키텍처 다이어그램 |
| Low | 사소한 용어 불일치 | Naming 스타일 편차 |

## 📊 Drift Score (초안)

`Score = Σ(weight(category) * severity_factor * freshness_penalty)`

- severity_factor: Critical=5, High=3, Medium=2, Low=1
- freshness_penalty: (days_since_last_review / review_interval_days) (0 이상 2 capped)
- weight(category) 기본 1.0 (Critical 영역은 1.2 제안)

향후 JSON 리포트 누적 → 이동평균 추세 그래프 지원 예정.

## 🔁 운영 주기

| 주기 | 작업 | 산출물 |
|------|------|--------|
| 매 커밋 (CI) | 베이직 정적 감사 | JSON (레이어/금지 import) |
| Daily | Drift Score 재계산 | score_history.json append |
| Weekly | Top-5 High+ 리포트 생성 | weekly_report.md |
| Monthly | 전수 검토 + 만료 문서 알람 | stale_docs.md |

## 🧪 감사 항목 매트릭스 (요약)

| Code Rule | 검사 방법 | 도구/스크립트 | 상태 |
|-----------|-----------|---------------|------|
| Domain 외부 의존 금지 | import 스캔 | audit 스크립트 | 계획 |
| print() 금지 | grep 패턴 | audit 스크립트 | 계획 |
| 3-DB 존재 | 파일 존재 + pragma | DB 검사 함수 | 계획 |
| Dry-run 기본 True | UseCase 파라미터 디폴트 분석 | AST/regex | 계획 |
| Authoritative 문서 신선도 | front-matter last_reviewed | 문서 메타 파서 | 계획 |

## 📁 구성 (예정)

```text
/README.md                # 본 개요
/charter.md               # 세부 챠터, 변경 이력
/templates/
  drift_matrix.md         # 단일 드리프트 기록 템플릿
  weekly_report.md        # 주간 리포트 템플릿
  stale_docs.md           # 만료 문서 목록 템플릿
/scripts/
  architecture_drift_audit.py  # 레이어/패턴 검사
  db_schema_check.py           # DB vs 선언 스키마
  doc_freshness_scan.py        # last_reviewed 수집
/reports/
  latest.json
  history/
    2025-10-01THHMMSS.json
```

## 🛠️ 초기 실행 우선순위 (Phase 1)

1. 스크립트: architecture_drift_audit.py (레이어/금지 import/print)
2. 템플릿: drift_matrix.md
3. 스크립트: doc_freshness_scan.py (front-matter 없으면 보강 제안)
4. 스크립트: db_schema_check.py (pragma + sql 파싱 단순 비교)
5. CI 연동: PowerShell 태스크 + README 사용법 추가

## 📌 Front-Matter 권장 예시

```markdown
---
authoritative: true
owner: architecture-team
last_reviewed: 2025-10-01
review_interval_days: 30
---
```

## 🚀 다음 단계 제안

- templates/ 및 scripts/ 디렉터리 생성
- drift_matrix 템플릿 초안 작성
- architecture_drift_audit.py 최소 기능 버전 구현

요청 주시면 곧바로 Phase 1 항목을 생성/구현 진행하겠습니다.
