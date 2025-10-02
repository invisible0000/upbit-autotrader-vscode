"""Documentation Freshness & Metadata Scanner (v0.1)

기능:
1. 지정 루트(docs/) 하위 Markdown 파일 탐색
2. Front-matter(YAML 유사) 블록 파싱 (선두의 --- ... ---)
3. 핵심 메타 필드 추출: type, authoritative, lifecycle, freshness_target_days, last_reviewed, owner
4. 누락/형식 오류/만료 여부 계산
5. JSON 결과 출력

만료 판단:
  authoritative=true 이고 last_reviewed 존재 시
    days_since_review > freshness_target_days => expired

향후 확장 (v0.2 계획):
 - drift_audit/document_inventory.md 와 매핑 후 차이 강조
 - auto front-matter 제안 패치 파일 생성 옵션
 - review_interval_days vs freshness_target_days 통합

사용 예 (PowerShell):
  python docs/drift_audit/scripts/doc_freshness_scan.py --root docs --output docs/drift_audit/reports/doc_freshness_latest.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
DATE_FMT_CANDIDATES = ["%Y-%m-%d", "%Y/%m/%d"]


@dataclass
class DocMeta:
    path: str
    type: Optional[str] = None
    authoritative: Optional[bool] = None
    lifecycle: Optional[str] = None
    freshness_target_days: Optional[int] = None
    last_reviewed: Optional[str] = None
    owner: Optional[str] = None
    parsed: bool = False
    expired: bool = False
    days_since_review: Optional[int] = None
    issues: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


def parse_front_matter(text: str) -> Dict[str, Any]:
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}
    block = m.group(1)
    meta: Dict[str, Any] = {}
    for line in block.splitlines():
        if not line.strip() or line.strip().startswith('#'):
            continue
        if ':' not in line:
            continue
        key, val = line.split(':', 1)
        key = key.strip()
        val = val.strip()
        # 단순 타입 변환
        if val.lower() in ("true", "false"):
            meta[key] = (val.lower() == "true")
        else:
            # 숫자
            if val.isdigit():
                try:
                    meta[key] = int(val)
                    continue
                except ValueError:
                    pass
            meta[key] = val
    return meta


def compute_expiry(meta: DocMeta) -> None:
    if not meta.authoritative:
        return
    if not meta.last_reviewed:
        meta.issues.append("missing_last_reviewed")
        return
    if not meta.freshness_target_days:
        meta.issues.append("missing_freshness_target_days")
        return
    # 날짜 파싱
    dt = None
    for fmt in DATE_FMT_CANDIDATES:
        try:
            dt = datetime.strptime(meta.last_reviewed, fmt)
            break
        except ValueError:
            continue
    if not dt:
        meta.issues.append("invalid_last_reviewed_format")
        return
    days = (datetime.now() - dt).days
    meta.days_since_review = days
    if days > meta.freshness_target_days:
        meta.expired = True


def scan_docs(root: str) -> List[DocMeta]:
    results: List[DocMeta] = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if not fn.lower().endswith('.md'):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, start=root)
            with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            meta_dict = parse_front_matter(text)
            dm = DocMeta(path=rel, issues=[])
            if meta_dict:
                dm.parsed = True
                dm.type = meta_dict.get('type')
                dm.authoritative = meta_dict.get('authoritative')
                dm.lifecycle = meta_dict.get('lifecycle')
                dm.freshness_target_days = meta_dict.get('freshness_target_days') or meta_dict.get('review_interval_days')
                dm.last_reviewed = meta_dict.get('last_reviewed')
                dm.owner = meta_dict.get('owner')
            else:
                dm.issues.append('missing_front_matter')
            compute_expiry(dm)
            # 추가 기초 검증
            if dm.authoritative and not dm.owner:
                dm.issues.append('missing_owner')
            if dm.authoritative and not dm.type:
                dm.issues.append('missing_type')
            results.append(dm)
    return results


def summarize(metas: List[DocMeta]) -> Dict[str, Any]:
    total = len(metas)
    expired = sum(1 for m in metas if m.expired)
    authoritative = sum(1 for m in metas if m.authoritative)
    missing_front = sum(1 for m in metas if 'missing_front_matter' in (m.issues or []))
    return {
        'total': total,
        'authoritative': authoritative,
        'expired': expired,
        'missing_front_matter': missing_front,
    }


def main():
    parser = argparse.ArgumentParser(description='Documentation Freshness Scanner')
    parser.add_argument('--root', default='docs', help='스캔할 문서 루트 (기본: docs)')
    parser.add_argument('--output', help='JSON 출력 경로')
    args = parser.parse_args()

    metas = scan_docs(args.root)
    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'root': args.root,
        'version': '0.1.0',
        'kind': 'doc_freshness_audit',
        'summary': summarize(metas),
        'documents': [m.to_dict() for m in metas],
    }
    js = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(js)
        print(args.output)
    else:
        print(js)


if __name__ == '__main__':  # pragma: no cover
    main()
