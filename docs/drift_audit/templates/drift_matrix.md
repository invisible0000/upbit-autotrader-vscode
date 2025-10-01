# 드리프트 매트릭스 템플릿 (Drift Matrix)

문서-구현 간 불일치를 표준화해 추적하기 위한 기록 형식.

## 사용 방법

1. 각 드리프트 사례마다 아래 섹션을 복사
2. `status`는 PASS / WARN / FAIL 중 하나
3. 해결 후 `resolution` 업데이트 및 `resolved_at` 기입
4. 위험도 상승 가능성 있으면 escalation_note 추가

---

## Drift Case: (짧은 식별자 기입)

- category: architecture | db | strategy | security | documentation | process
- severity: Critical | High | Medium | Low
- status: FAIL
- first_detected: 2025-10-01T12:00:00Z
- last_reviewed: 2025-10-01
- owner: (github-id or team)
- source_document: (상대경로 또는 N/A)
- authoritative: true | false | unknown

### Declared (문서 선언 내용)

```text
설명 또는 문서 인용
```

### Observed (코드/실행 관찰)

```text
실제 코드 스니펫/행동/로그 요약
```

### Gap 분석

- 차이 유형: omission | divergence | ambiguity | outdated
- 영향: (거래 실패 가능성 / 온보딩 혼선 등)
- 재현 단계: (선택)

### 측정/증거

| 항목 | 값 | 비고 |
|------|----|------|
| 관련 파일 수 | 0 | 예: grep 결과 |
| commit hash | (abc1234) | 최초 탐지 기준 |

### 권고 조치

- [ ] 수정 정의
- [ ] 리뷰어 할당
- [ ] 테스트 보강 필요 여부

### 해결 (채우기 전까지 비워둠)

- resolution: (적용된 변경 요약)
- resolved_at: (ISO8601)
- follow_up: (추가 태스크)
- drift_score_delta: -X

---
