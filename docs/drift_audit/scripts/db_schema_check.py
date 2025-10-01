"""DB Schema Drift Checker (v0.1)

목표:
1. 선언 스키마(SQL 파일) vs 실제 SQLite 파일 구조(PRAGMA) 차이 탐지
2. 차이를 JSON 리포트로 출력 (추후 Drift Score 반영 예정)

지원 범위 (v0.1):
 - 테이블 존재 여부
 - 컬럼 목록/순서/타입/NOT NULL
 - 기본키(단순) 확인

미포함 (후속):
 - 외래키 제약 상세
 - 인덱스 비교
 - 트리거/뷰

사용 예 (PowerShell):
    python docs/drift_audit/scripts/db_schema_check.py \
        --schema-dir data_info \
        --db data/settings.sqlite3 \
        --db data/strategies.sqlite3 \
        --db data/market_data.sqlite3 \
        --output docs/drift_audit/reports/db_schema_latest.json

출력 JSON 구조(요약):
{
  "generated_at": "..",
  "schema_dir": "..",
  "databases": [
     {
        "path": "data/settings.sqlite3",
        "tables": { "table_name": { "status": "match|missing|extra|drift", "diff": {...}} }
     }
  ]
}
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Any


CREATE_TABLE_REGEX = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)", re.IGNORECASE)


@dataclass
class ColumnDef:
    name: str
    type: str
    notnull: int  # 0 or 1
    pk: int       # 0 or 1 (simple primary key flag)


@dataclass
class TableDecl:
    name: str
    columns: List[ColumnDef]


def parse_declared_tables(sql_text: str) -> Dict[str, TableDecl]:
    tables: Dict[str, TableDecl] = {}
    # 단순: CREATE TABLE 블록을 분리 -> 괄호 내 컬럼 라인 파싱
    for match in CREATE_TABLE_REGEX.finditer(sql_text):
        table_name = match.group(1)
        # 블록 추출 (매치 지점부터 첫 세미콜론까지)
        start = match.start()
        semicolon = sql_text.find(";", start)
        if semicolon == -1:
            continue
        block = sql_text[start:semicolon]
        paren_start = block.find("(")
        paren_end = block.rfind(")")
        if paren_start == -1 or paren_end == -1 or paren_end <= paren_start:
            continue
        inner = block[paren_start + 1:paren_end]
        # foreign key 라인은 v0.1에서 제외
        column_lines = []
        for raw_segment in inner.split(","):
            seg = raw_segment.strip()
            if not seg:
                continue
            if seg.upper().startswith("FOREIGN KEY"):
                continue
            column_lines.append(seg)
        cols: List[ColumnDef] = []
        for cl in column_lines:
            parts = cl.split()
            if len(parts) < 2:
                continue
            col_name = parts[0].strip('"`')
            col_type = parts[1].upper()
            has_not = any(p.upper() == "NOT" for p in parts)
            has_null = any(p.upper() == "NULL" for p in parts)
            notnull = 1 if (has_not and has_null) or ("NOT NULL" in cl.upper()) else 0
            pk = 1 if "PRIMARY KEY" in cl.upper() else 0
            cols.append(ColumnDef(col_name, col_type, notnull, pk))
        tables[table_name] = TableDecl(name=table_name, columns=cols)
    return tables


def load_declared_schema(schema_dir: str) -> Dict[str, TableDecl]:
    declared: Dict[str, TableDecl] = {}
    for fname in os.listdir(schema_dir):
        if not fname.endswith('.sql'):
            continue
        path = os.path.join(schema_dir, fname)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        partial = parse_declared_tables(text)
        # 파일별 중복 테이블 정의가 있다면 마지막이 덮어씀 (단순)
        declared.update(partial)
    return declared


def fetch_actual_tables(db_path: str) -> Dict[str, TableDecl]:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        actual: Dict[str, TableDecl] = {}
        for t in tables:
            cur.execute(f"PRAGMA table_info('{t}')")
            rows = cur.fetchall()  # cid, name, type, notnull, dflt_value, pk
            cols = [ColumnDef(name=r[1], type=(r[2] or '').upper(), notnull=r[3], pk=r[5]) for r in rows]
            actual[t] = TableDecl(name=t, columns=cols)
        return actual
    finally:
        conn.close()


def compare_table(decl: TableDecl, act: TableDecl) -> Dict[str, Any]:
    diff: Dict[str, Any] = {"column_drift": []}
    # 순서 및 개수 동시 비교
    decl_cols = decl.columns
    act_cols = act.columns
    max_len = max(len(decl_cols), len(act_cols))
    for i in range(max_len):
        d = decl_cols[i] if i < len(decl_cols) else None
        a = act_cols[i] if i < len(act_cols) else None
        if d and not a:
            diff["column_drift"].append({"index": i, "decl_only": d.name})
        elif a and not d:
            diff["column_drift"].append({"index": i, "actual_only": a.name})
        else:
            assert d and a
            issues = []
            if d.name != a.name:
                issues.append("name_mismatch")
            if d.type != a.type:
                issues.append("type_mismatch")
            if d.notnull != a.notnull:
                issues.append("notnull_mismatch")
            if d.pk != a.pk:
                issues.append("pk_mismatch")
            if issues:
                diff["column_drift"].append({
                    "index": i,
                    "decl": asdict(d),
                    "actual": asdict(a),
                    "issues": issues,
                })
    diff["status"] = "match" if not diff["column_drift"] else "drift"
    return diff


def audit_database(db_path: str, declared: Dict[str, TableDecl]) -> Dict[str, Any]:
    actual = fetch_actual_tables(db_path)
    result: Dict[str, Any] = {"path": db_path, "tables": {}}
    # 선언된 테이블 검사
    for tname, tdecl in declared.items():
        if tname not in actual:
            result["tables"][tname] = {"status": "missing_in_db"}
        else:
            result["tables"][tname] = compare_table(tdecl, actual[tname])
    # DB에만 있는 추가 테이블
    for tname in actual.keys():
        if tname not in declared:
            result["tables"][tname] = {"status": "extra_in_db"}
    return result


def run_audit(schema_dir: str, db_paths: List[str]) -> Dict[str, Any]:
    declared = load_declared_schema(schema_dir)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema_dir": schema_dir,
        "declared_table_count": len(declared),
        "databases": [],
        "version": "0.1.0",
        "kind": "db_schema_audit",
    }
    for db in db_paths:
        if not os.path.exists(db):
            report["databases"].append({"path": db, "error": "not_found"})
            continue
        report["databases"].append(audit_database(db, declared))
    return report


def main():
    parser = argparse.ArgumentParser(description="DB Schema Drift Checker")
    parser.add_argument("--schema-dir", default="data_info", help="선언 스키마 .sql 디렉터리")
    parser.add_argument("--db", action="append", dest="dbs", help="검사할 sqlite DB 경로 (여러 번 지정)")
    parser.add_argument("--output", help="JSON 출력 경로")
    args = parser.parse_args()

    if not args.dbs:
        parser.error("--db 최소 1개 필요")

    report = run_audit(args.schema_dir, args.dbs)
    output_json = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_json)
        print(args.output)
    else:
        print(output_json)


if __name__ == "__main__":  # pragma: no cover
    main()
