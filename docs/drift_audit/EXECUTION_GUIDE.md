# 드리프트 감사 실행 가이드 (CI & 로컬)

이 문서는 문서-구현 드리프트 관련 3종 자동 감사 스크립트를 로컬/CI에서 일관되게 실행하기 위한 가이드입니다.

## 1. 감사 대상 스크립트

| 스크립트 | 목적 | 산출물 kind |
|----------|------|-------------|
| architecture_drift_audit.py | DDD 위반/print 사용 탐지 | architecture_drift_audit |
| db_schema_check.py | 선언 스키마 vs 실제 DB 구조 비교 | db_schema_audit |
| doc_freshness_scan.py | 문서 메타/신선도 점검 | doc_freshness_audit |

## 2. PowerShell 단일 실행 (권장)

`Invoke-DriftAudit.ps1` 스크립트를 이용해 세 가지 리포트를 한 번에 생성합니다.

```powershell
pwsh -File scripts/Invoke-DriftAudit.ps1
```

기본 출력 경로:

```text
docs/drift_audit/reports/
  latest_arch.json
  db_schema_latest.json
  doc_freshness_latest.json
```

## 3. 개별 실행 예시

```powershell
# 아키텍처
python docs/drift_audit/scripts/architecture_drift_audit.py --root . --output docs/drift_audit/reports/latest_arch.json

# DB 스키마
python docs/drift_audit/scripts/db_schema_check.py `
  --schema-dir data_info `
  --db data/settings.sqlite3 `
  --db data/strategies.sqlite3 `
  --db data/market_data.sqlite3 `
  --output docs/drift_audit/reports/db_schema_latest.json

# 문서 Freshness
python docs/drift_audit/scripts/doc_freshness_scan.py --root docs --output docs/drift_audit/reports/doc_freshness_latest.json
```

## 4. CI 통합 아이디어 (GitHub Actions 예시 YAML 스니펫)

```yaml
jobs:
  drift-audit:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Run drift audit
        shell: pwsh
        run: pwsh -File scripts/Invoke-DriftAudit.ps1
      - name: Upload reports artifact
        uses: actions/upload-artifact@v4
        with:
          name: drift-audit-reports
          path: docs/drift_audit/reports/*.json
```

## 5. 실패/경고 정책 제안

| 조건 | 처리 | 설명 |
|------|------|------|
| architecture_drift_audit High 이상 발견 | CI 실패 (exit 1) | 금지 import 도입 즉시 차단 |
| db_schema_audit drift/missing 발견 | PR 경고 코멘트 | 수동 확인 후 스키마 갱신 |
| doc_freshness_audit expired > 0 | 주간 리포트 경고 | 만료 문서 정비 우선순위화 |

## 6. 로컬 개발 흐름 권장

1. 기능 구현 → `Invoke-DriftAudit.ps1` 실행
2. 만약 domain에 print 추가되면 로거 전환
3. Authoritative 문서 수정 시 front-matter의 `last_reviewed` 갱신
4. DB 변경 시 `data_info/*.sql` 반영 후 감사 재실행

## 7. Authoritative 문서 체크리스트 (PR 템플릿에 추가 권장)

| 항목 | 상태 |
|------|------|
| last_reviewed 갱신 | [ ] |
| freshness_target_days 유지 | [ ] |
| owner 지정 | [ ] |
| 내용이 실제 코드 흐름과 일치 | [ ] |

## 8. 다음 확장 로드맵

- Dry-run 기본값 AST 검증 통합
- Drift Score 계산 및 history 누적
- Top-5 자동 요약 생성 스크립트
- pre-commit 훅: domain print 차단

## 9. Top-5 가중치 커스터마이징

`top5_drift_report.py`는 `--weights` 옵션을 통해 기본 점수를 재정의할 수 있습니다.

예시 파일: `docs/drift_audit/config/drift_weights.example.json`

```json
{
  "architecture": { "forbidden_import": 100, "print_usage": 15 },
  "db": { "missing_in_db": 70, "drift": 45, "extra_in_db": 10 },
  "docs": { "authoritative_expired": 55, "authoritative_missing_owner": 30, "missing_front_matter": 25 }
}
```

사용 예:

```powershell
python docs/drift_audit/scripts/top5_drift_report.py `
  --arch docs/drift_audit/reports/latest_arch.json `
  --db docs/drift_audit/reports/db_schema_latest.json `
  --docs docs/drift_audit/reports/doc_freshness_latest.json `
  --weights docs/drift_audit/config/drift_weights.example.json `
  --output-md docs/drift_audit/reports/top5_weighted.md
```

Invoke-DriftAudit.ps1는 동일 경로에 `drift_weights.json` 파일이 존재하면 자동 적용하도록 설정할 수 있습니다.

---
작성: v0.1 (초기 운영 가이드)
추가 개선 필요 시 drift_audit README 에서 링크 유지
