"""Top-5 Drift Report Generator (v0.1)

세 개 감사 결과(architecture/db_schema/doc_freshness) JSON을 읽고 위험도 점수화하여 Top-5
요약 Markdown 리포트를 생성한다.

점수 규칙(초안):
 - architecture: forbidden_import -> 80, print_usage -> 20
 - db_schema: missing_in_db -> 60, drift -> 40, extra_in_db -> 15
 - doc_freshness: authoritative & expired -> 50, authoritative & missing_owner -> 25,
                  missing_front_matter -> 20

최종 score = base_score, 동일 점수는 최근성(파일명/카테고리 문자열 정렬)으로 결정.

출력: Markdown + JSON(선택) (기본은 Markdown stdout)
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


DEFAULT_ARCH_SCORES = {
    "forbidden_import": 80,
    "print_usage": 20,
}

DEFAULT_DB_SCORES = {
    "missing_in_db": 60,
    "drift": 40,
    "extra_in_db": 15,
}

DEFAULT_DOC_SCORES = {
    "authoritative_expired": 50,
    "authoritative_missing_owner": 25,
    "missing_front_matter": 20,
}


@dataclass
class DriftItem:
    category: str  # architecture | db | docs
    sub_type: str
    target: str
    detail: Dict[str, Any]
    score: int

    def to_row(self) -> str:
        return f"| {self.category} | {self.sub_type} | {self.score} | {self.target} |"


def load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_architecture(findings_json: Dict[str, Any], scores: Dict[str, int]) -> List[DriftItem]:
    items: List[DriftItem] = []
    for f in findings_json.get("findings", []):
        cat = f.get("category")
        score = scores.get(cat)
        if not score:
            continue
        items.append(
            DriftItem(
                category="architecture",
                sub_type=cat,
                target=f.get("file", "unknown"),
                detail=f,
                score=score,
            )
        )
    return items


def extract_db(db_json: Dict[str, Any], scores: Dict[str, int]) -> List[DriftItem]:
    items: List[DriftItem] = []
    for db in db_json.get("databases", []):
        tables = db.get("tables", {})
        for tname, tinfo in tables.items():
            status = tinfo.get("status")
            if status in scores:
                items.append(
                    DriftItem(
                        category="db",
                        sub_type=status,
                        target=f"{db.get('path')}::{tname}",
                        detail=tinfo,
                        score=scores[status],
                    )
                )
    return items


def extract_docs(doc_json: Dict[str, Any], scores: Dict[str, int]) -> List[DriftItem]:
    items: List[DriftItem] = []
    for doc in doc_json.get("documents", []):
        issues = doc.get("issues") or []
        authoritative = doc.get("authoritative")
        expired = doc.get("expired")
        path = doc.get("path")
        if authoritative and expired:
            items.append(
                DriftItem(
                    category="docs",
                    sub_type="authoritative_expired",
                    target=path,
                    detail=doc,
                    score=scores["authoritative_expired"],
                )
            )
        if authoritative and "missing_owner" in issues:
            items.append(
                DriftItem(
                    category="docs",
                    sub_type="authoritative_missing_owner",
                    target=path,
                    detail=doc,
                    score=scores["authoritative_missing_owner"],
                )
            )
        if "missing_front_matter" in issues:
            items.append(
                DriftItem(
                    category="docs",
                    sub_type="missing_front_matter",
                    target=path,
                    detail=doc,
                    score=scores["missing_front_matter"],
                )
            )
    return items


def generate_markdown(items: List[DriftItem], limit: int = 5) -> str:
    header = "# Top-5 Drift Report\n\n생성: " + datetime.now(timezone.utc).isoformat() + "\n\n"
    header += "| Category | Type | Score | Target |\n|----------|------|-------|--------|\n"
    body = "\n".join(i.to_row() for i in items[:limit])
    return header + body + "\n"


def load_weights(path: Optional[str]) -> tuple[Dict[str, int], Dict[str, int], Dict[str, int]]:
    if not path:
        return DEFAULT_ARCH_SCORES, DEFAULT_DB_SCORES, DEFAULT_DOC_SCORES
    if not os.path.exists(path):
        raise FileNotFoundError(f"weights file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    arch = {**DEFAULT_ARCH_SCORES, **data.get('architecture', {})}
    db = {**DEFAULT_DB_SCORES, **data.get('db', {})}
    docs = {**DEFAULT_DOC_SCORES, **data.get('docs', {})}
    return arch, db, docs


def main():
    parser = argparse.ArgumentParser(description="Top-5 Drift Report Generator")
    parser.add_argument("--arch", help="architecture audit JSON 경로")
    parser.add_argument("--db", help="db schema audit JSON 경로")
    parser.add_argument("--docs", help="doc freshness audit JSON 경로")
    parser.add_argument("--output-md", help="출력 Markdown 파일")
    parser.add_argument("--output-json", help="출력 JSON 파일 (선택)")
    parser.add_argument("--weights", help="가중치 JSON 파일 (architecture/db/docs 섹션 포함)")
    args = parser.parse_args()

    arch_scores, db_scores, doc_scores = load_weights(args.weights)

    items: List[DriftItem] = []
    if args.arch:
        items.extend(extract_architecture(load_json(args.arch), arch_scores))
    if args.db:
        items.extend(extract_db(load_json(args.db), db_scores))
    if args.docs:
        items.extend(extract_docs(load_json(args.docs), doc_scores))

    # 점수 내림차순, 그다음 target 정렬
    items.sort(key=lambda x: (-x.score, x.target))

    md = generate_markdown(items)
    if args.output_md:
        os.makedirs(os.path.dirname(args.output_md), exist_ok=True)
        with open(args.output_md, 'w', encoding='utf-8') as f:
            f.write(md)
        print(args.output_md)
    else:
        print(md)

    if args.output_json:
        data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "version": "0.1.0",
            "kind": "top5_drift_report",
            "items": [asdict(i) for i in items[:5]],
        }
        with open(args.output_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":  # pragma: no cover
    main()
