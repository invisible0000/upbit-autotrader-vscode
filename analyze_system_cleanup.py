#!/usr/bin/env python3
"""
데이터베이스 및 파일 시스템 정리를 위한 사용 현황 분석 스크립트

1. 코드에서 실제 사용되는 테이블 분석
2. 불필요한 파일/폴더 식별
3. 정리 권장사항 제공
"""

import sqlite3
import re
from pathlib import Path
from typing import Dict, List, Set


class SystemCleanupAnalyzer:
    """시스템 정리를 위한 분석기"""

    def __init__(self):
        self.project_root = Path(".")
        self.databases = {
            "settings": "data/settings.sqlite3",
            "strategies": "data/strategies.sqlite3",
            "market_data": "data/market_data.sqlite3"
        }

    def analyze_code_database_usage(self) -> Dict[str, Set[str]]:
        """코드에서 실제 사용되는 테이블들 분석"""
        print("🔍 코드에서 데이터베이스 사용 현황 분석...")

        # Python 파일들에서 테이블명 검색
        python_files = list(self.project_root.rglob("*.py"))

        # 테이블명 패턴들
        table_patterns = [
            r"FROM\s+(\w+)",
            r"INSERT\s+INTO\s+(\w+)",
            r"UPDATE\s+(\w+)",
            r"DELETE\s+FROM\s+(\w+)",
            r"CREATE\s+TABLE\s+(\w+)",
            r"DROP\s+TABLE\s+(\w+)",
            r"SELECT.*FROM\s+(\w+)",
            r"\"(\w+)\"\s*\)",  # 테이블명이 따옴표로 감싸진 경우
            r"'(\w+)'\s*\)",   # 테이블명이 따옴표로 감싸진 경우
        ]

        used_tables = set()
        file_table_usage = {}

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                file_tables = set()
                for pattern in table_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            table_name = match[0]
                        else:
                            table_name = match

                        # 일반적인 테이블명 필터링
                        if (len(table_name) > 2 and
                                table_name.lower() not in ['select', 'from', 'where', 'and', 'or', 'table', 'create', 'drop'] and
                                not table_name.isdigit()):
                            used_tables.add(table_name)
                            file_tables.add(table_name)

                if file_tables:
                    file_table_usage[str(py_file)] = file_tables

            except Exception as e:
                print(f"  ⚠️  파일 읽기 오류: {py_file} - {e}")

        print(f"  📊 발견된 테이블 사용: {len(used_tables)}개")
        print(f"  📁 분석된 Python 파일: {len(python_files)}개")

        return {"used_tables": used_tables, "file_usage": file_table_usage}

    def analyze_actual_database_tables(self) -> Dict[str, List[str]]:
        """실제 데이터베이스에 존재하는 테이블들 분석"""
        print("\n💾 실제 데이터베이스 테이블 현황 분석...")

        db_tables = {}

        for db_name, db_path in self.databases.items():
            if not Path(db_path).exists():
                print(f"  ❌ {db_name} 데이터베이스 없음: {db_path}")
                db_tables[db_name] = []
                continue

            try:
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                    tables = [row[0] for row in cursor.fetchall()]
                    db_tables[db_name] = tables
                    print(f"  📊 {db_name}: {len(tables)}개 테이블")

            except Exception as e:
                print(f"  ❌ {db_name} 분석 오류: {e}")
                db_tables[db_name] = []

        return db_tables

    def analyze_legacy_folders(self) -> Dict[str, Dict]:
        """레거시 폴더들 분석"""
        print("\n📁 레거시 폴더 분석...")

        legacy_candidates = [
            "data_info/indicators",
            "data_info/tv_variable_help_guides",
            "data_info/_archived",
            "temp",
            "legacy"
        ]

        folder_analysis = {}

        for folder_path in legacy_candidates:
            path = Path(folder_path)
            if path.exists():
                # 폴더 크기 및 파일 수 계산
                total_size = 0
                file_count = 0

                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        try:
                            total_size += file_path.stat().st_size
                            file_count += 1
                        except:
                            pass

                folder_analysis[folder_path] = {
                    "exists": True,
                    "file_count": file_count,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "last_modified": path.stat().st_mtime if path.exists() else None
                }
                print(f"  📂 {folder_path}: {file_count}개 파일, {folder_analysis[folder_path]['total_size_mb']}MB")
            else:
                folder_analysis[folder_path] = {"exists": False}
                print(f"  ❌ {folder_path}: 존재하지 않음")

        return folder_analysis

    def check_import_dependencies(self) -> Dict[str, List[str]]:
        """import 구문에서 레거시 경로 사용 체크"""
        print("\n🔗 import 의존성 분석...")

        python_files = list(self.project_root.rglob("*.py"))
        legacy_imports = {}

        legacy_patterns = [
            r"from\s+.*indicators.*import",
            r"import\s+.*indicators",
            r"from\s+.*tv_variable_help_guides.*import",
            r"import\s+.*tv_variable_help_guides"
        ]

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                file_legacy_imports = []
                for pattern in legacy_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        file_legacy_imports.extend(matches)

                if file_legacy_imports:
                    legacy_imports[str(py_file)] = file_legacy_imports

            except Exception as e:
                continue

        print(f"  📊 레거시 import 발견: {len(legacy_imports)}개 파일")
        return legacy_imports

    def generate_cleanup_recommendations(self, analysis_results: Dict) -> List[str]:
        """정리 권장사항 생성"""
        recommendations = []

        # 1. 레거시 폴더 정리
        folder_analysis = analysis_results.get("folders", {})
        for folder_path, info in folder_analysis.items():
            if info.get("exists") and info.get("file_count", 0) > 0:
                if "indicators" in folder_path or "help_guides" in folder_path:
                    recommendations.append(f"🗑️  삭제 가능: {folder_path} ({info['file_count']}개 파일)")

        # 2. 데이터베이스 정리
        used_tables = analysis_results.get("used_tables", set())
        db_tables = analysis_results.get("db_tables", {})

        for db_name, tables in db_tables.items():
            unused_tables = [t for t in tables if t not in used_tables]
            if unused_tables:
                recommendations.append(f"🗑️  {db_name} DB 미사용 테이블: {len(unused_tables)}개")

        # 3. Import 정리
        legacy_imports = analysis_results.get("legacy_imports", {})
        if legacy_imports:
            recommendations.append(f"🔧 레거시 import 수정 필요: {len(legacy_imports)}개 파일")

        return recommendations

    def run_full_analysis(self):
        """전체 분석 실행"""
        print("🧹 시스템 정리를 위한 종합 분석 시작...\n")

        # 각종 분석 실행
        code_usage = self.analyze_code_database_usage()
        db_tables = self.analyze_actual_database_tables()
        folders = self.analyze_legacy_folders()
        imports = self.check_import_dependencies()

        # 결과 통합
        analysis_results = {
            "used_tables": code_usage["used_tables"],
            "file_usage": code_usage["file_usage"],
            "db_tables": db_tables,
            "folders": folders,
            "legacy_imports": imports
        }

        # 권장사항 생성
        recommendations = self.generate_cleanup_recommendations(analysis_results)

        # 결과 출력
        print("\n" + "="*60)
        print("📋 분석 결과 요약")
        print("="*60)

        print(f"\n🔍 코드에서 사용 중인 테이블: {len(analysis_results['used_tables'])}개")
        for table in sorted(analysis_results['used_tables']):
            print(f"  - {table}")

        print(f"\n💾 데이터베이스별 테이블 현황:")
        for db_name, tables in analysis_results['db_tables'].items():
            unused = [t for t in tables if t not in analysis_results['used_tables']]
            print(f"  - {db_name}: 전체 {len(tables)}개, 미사용 {len(unused)}개")

        print(f"\n📁 레거시 폴더 현황:")
        for folder_path, info in analysis_results['folders'].items():
            if info.get("exists"):
                print(f"  - {folder_path}: {info.get('file_count', 0)}개 파일")

        print(f"\n🔧 정리 권장사항:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

        if not recommendations:
            print("  ✅ 현재 시스템이 깔끔하게 정리되어 있습니다!")

        return analysis_results


def main():
    analyzer = SystemCleanupAnalyzer()
    results = analyzer.run_full_analysis()

    print(f"\n💡 다음 단계 제안:")
    print(f"  1. 먼저 레거시 import 구문들을 새로운 trading_variables 경로로 수정")
    print(f"  2. 미사용 테이블들을 백업 후 삭제")
    print(f"  3. 레거시 폴더들을 _archived로 이동 후 삭제")
    print(f"  4. settings.sqlite3에서 필수 테이블만 유지")


if __name__ == "__main__":
    main()
