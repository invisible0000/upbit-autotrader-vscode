#!/usr/bin/env python3
"""
집중적 시스템 정리 도구 - .venv 제외, 핵심 영역만

범위 제한:
- upbit_auto_trading/ (소스코드)
- data_info/ (정의 파일들)
- data/ (데이터베이스)
- config/ (설정 파일들)
- .venv, __pycache__, .git 등 제외
"""

import sqlite3
from pathlib import Path
import shutil
import json
from datetime import datetime


class FocusedSystemCleaner:
    """집중적 시스템 정리기 - 핵심 영역만"""

    def __init__(self):
        self.project_root = Path(".")

        # 분석 대상 폴더 (제한적)
        self.target_folders = [
            "upbit_auto_trading",
            "data_info",
            "data",
            "config",
            "tests",
            "tools"
        ]

        # 제외할 폴더들
        self.exclude_patterns = [
            ".venv",
            "__pycache__",
            ".git",
            "*.egg-info",
            "logs",
            "temp",
            "backups"
        ]

    def analyze_legacy_folders(self):
        """레거시 폴더 정확한 현황"""
        print("📁 레거시 폴더 현황 분석")

        legacy_targets = {
            "data_info/indicators": "SMA만 남은 구 지표 폴더",
            "data_info/tv_variable_help_guides": "구 도움말 가이드",
            "data_info/_archived": "이미 아카이브된 파일들",
            "legacy": "레거시 코드들"
        }

        results = {}
        for folder_path, description in legacy_targets.items():
            path = Path(folder_path)
            if path.exists():
                files = list(path.rglob("*"))
                file_count = len([f for f in files if f.is_file()])
                folder_count = len([f for f in files if f.is_dir()])

                results[folder_path] = {
                    "exists": True,
                    "description": description,
                    "file_count": file_count,
                    "folder_count": folder_count,
                    "total_size_kb": sum(f.stat().st_size for f in files if f.is_file()) // 1024
                }
                print(f"  📂 {folder_path}: {file_count}개 파일, {folder_count}개 폴더 ({results[folder_path]['total_size_kb']}KB)")
                print(f"     💡 {description}")
            else:
                results[folder_path] = {"exists": False, "description": description}
                print(f"  ❌ {folder_path}: 없음")

        return results

    def analyze_database_tables(self):
        """데이터베이스 테이블 정확한 분석"""
        print("\n💾 데이터베이스 테이블 분석")

        # 트리거 빌더 개발에 필수인 테이블들
        essential_tables = {
            "settings.sqlite3": [
                "tv_trading_variables",
                "tv_variable_parameters",
                "tv_variable_help_documents",
                "tv_help_texts",
                "tv_placeholder_texts",
                "api_keys",  # 암호화된 API 키
                "user_settings"  # 사용자 설정
            ]
        }

        db_analysis = {}

        for db_file in ["data/settings.sqlite3", "data/strategies.sqlite3", "data/market_data.sqlite3"]:
            db_path = Path(db_file)
            db_name = db_path.name

            if not db_path.exists():
                print(f"  ❌ {db_file}: 파일 없음")
                continue

            try:
                with sqlite3.connect(str(db_path)) as conn:
                    # 모든 테이블 목록
                    cursor = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                    all_tables = [row[0] for row in cursor.fetchall()]

                    # 각 테이블의 레코드 수
                    table_info = {}
                    for table in all_tables:
                        try:
                            count_cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                            record_count = count_cursor.fetchone()[0]
                            table_info[table] = record_count
                        except Exception as e:
                            table_info[table] = f"오류: {e}"

                    # 필수 vs 선택적 분류
                    essential_for_this_db = essential_tables.get(db_name, [])
                    essential_found = [t for t in all_tables if t in essential_for_this_db]
                    optional_tables = [t for t in all_tables if t not in essential_for_this_db]
                    missing_essential = [t for t in essential_for_this_db if t not in all_tables]

                    db_analysis[db_file] = {
                        "total_tables": len(all_tables),
                        "table_info": table_info,
                        "essential_found": essential_found,
                        "optional_tables": optional_tables,
                        "missing_essential": missing_essential
                    }

                    print(f"\n  📊 {db_file}:")
                    print(f"    📋 전체 테이블: {len(all_tables)}개")

                    if essential_found:
                        print(f"    ✅ 필수 테이블: {len(essential_found)}개")
                        for table in essential_found:
                            count = table_info.get(table, 0)
                            print(f"      - {table}: {count}개 레코드")

                    if optional_tables:
                        print(f"    🤔 선택적 테이블: {len(optional_tables)}개")
                        for table in optional_tables:
                            count = table_info.get(table, 0)
                            print(f"      - {table}: {count}개 레코드")

                    if missing_essential:
                        print(f"    ❌ 누락된 필수: {len(missing_essential)}개")
                        for table in missing_essential:
                            print(f"      - {table}")

            except Exception as e:
                print(f"  ❌ {db_file} 분석 오류: {e}")
                db_analysis[db_file] = {"error": str(e)}

        return db_analysis

    def check_import_dependencies(self):
        """import 의존성 체크 - 핵심 폴더만"""
        print("\n🔗 Import 의존성 분석 (핵심 폴더만)")

        old_patterns = [
            "from data_info.indicators",
            "import data_info.indicators",
            "from data_info.tv_variable_help_guides",
            "import data_info.tv_variable_help_guides"
        ]

        found_imports = {}

        for folder in self.target_folders:
            folder_path = Path(folder)
            if not folder_path.exists():
                continue

            for pattern in old_patterns:
                found_files = []

                # Python 파일에서 검색
                for py_file in folder_path.rglob("*.py"):
                    try:
                        with open(py_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if pattern in content:
                                found_files.append(str(py_file))
                    except Exception:
                        continue

                if found_files:
                    found_imports[pattern] = found_files

        if found_imports:
            print("  ⚠️  레거시 import 발견:")
            for pattern, files in found_imports.items():
                print(f"    🔍 '{pattern}': {len(files)}개 파일")
                for file_path in files[:3]:  # 처음 3개만 표시
                    print(f"      - {file_path}")
                if len(files) > 3:
                    print(f"      ... +{len(files)-3}개 더")
        else:
            print("  ✅ 레거시 import 없음")

        return found_imports

    def generate_cleanup_plan(self, folder_analysis, db_analysis, import_analysis):
        """정리 계획 생성"""
        print("\n📋 정리 계획 생성")

        plan = {
            "step1_fix_imports": {
                "description": "레거시 import 구문 수정",
                "files_to_fix": sum(len(files) for files in import_analysis.values()),
                "required": len(import_analysis) > 0
            },
            "step2_backup_legacy_folders": {
                "description": "레거시 폴더 백업",
                "folders": [name for name, info in folder_analysis.items() if info.get("exists")],
                "total_files": sum(info.get("file_count", 0) for info in folder_analysis.values() if info.get("exists"))
            },
            "step3_cleanup_database": {
                "description": "데이터베이스 선택적 테이블 정리",
                "databases": []
            },
            "step4_remove_legacy_folders": {
                "description": "백업 완료 후 레거시 폴더 삭제",
                "safe_to_remove": []
            }
        }

        # DB 정리 계획
        for db_path, info in db_analysis.items():
            if "optional_tables" in info and info["optional_tables"]:
                plan["step3_cleanup_database"]["databases"].append({
                    "db": db_path,
                    "optional_tables": info["optional_tables"],
                    "keep_essential": info.get("essential_found", [])
                })

        # 안전하게 제거 가능한 폴더
        safe_folders = [
            "data_info/indicators",  # trading_variables로 완전 이관됨
            "data_info/tv_variable_help_guides"  # 새 구조로 이관됨
        ]

        for folder in safe_folders:
            if folder in folder_analysis and folder_analysis[folder].get("exists"):
                plan["step4_remove_legacy_folders"]["safe_to_remove"].append(folder)

        print("  📝 계획 요약:")
        print(f"    1. Import 수정: {plan['step1_fix_imports']['files_to_fix']}개 파일")
        print(f"    2. 폴더 백업: {len(plan['step2_backup_legacy_folders']['folders'])}개 폴더")
        print(f"    3. DB 정리: {len(plan['step3_cleanup_database']['databases'])}개 데이터베이스")
        print(f"    4. 폴더 삭제: {len(plan['step4_remove_legacy_folders']['safe_to_remove'])}개 폴더")

        return plan

    def run_focused_analysis(self):
        """집중 분석 실행"""
        print("🎯 집중적 시스템 분석 시작")
        print("="*50)
        print("범위: 핵심 폴더만 (.venv 제외)")
        print("목표: 트리거 빌더 개발 환경 최적화")
        print("="*50)

        # 각 분석 단계
        folder_analysis = self.analyze_legacy_folders()
        db_analysis = self.analyze_database_tables()
        import_analysis = self.check_import_dependencies()
        cleanup_plan = self.generate_cleanup_plan(folder_analysis, db_analysis, import_analysis)

        # 결과 요약
        print("\n" + "="*50)
        print("📊 분석 결과 요약")
        print("="*50)

        total_legacy_files = sum(info.get("file_count", 0) for info in folder_analysis.values() if info.get("exists"))
        total_legacy_size = sum(info.get("total_size_kb", 0) for info in folder_analysis.values() if info.get("exists"))

        print(f"💾 레거시 파일: {total_legacy_files}개 ({total_legacy_size}KB)")
        print(f"🔗 수정 필요한 import: {len(import_analysis)}개 패턴")

        for db_path, info in db_analysis.items():
            if "optional_tables" in info:
                print(f"🗄️  {Path(db_path).name}: {len(info['optional_tables'])}개 선택적 테이블")

        print(f"\n✅ 안전 삭제 가능: {len(cleanup_plan['step4_remove_legacy_folders']['safe_to_remove'])}개 폴더")

        # 결과 저장
        result = {
            "timestamp": datetime.now().isoformat(),
            "scope": "focused_analysis_excluding_venv",
            "folder_analysis": folder_analysis,
            "db_analysis": db_analysis,
            "import_analysis": import_analysis,
            "cleanup_plan": cleanup_plan
        }

        with open("_focused_cleanup_result.json", 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n📁 상세 결과: _focused_cleanup_result.json")

        return result


def main():
    print("🔧 집중적 시스템 정리 도구")
    print("범위: 핵심 개발 폴더만 (.venv 제외)")

    cleaner = FocusedSystemCleaner()
    result = cleaner.run_focused_analysis()

    print("\n🎉 집중 분석 완료!")
    print("\n💡 다음 단계:")
    print("1. _focused_cleanup_result.json 검토")
    print("2. 필요시 import 구문 수정")
    print("3. 레거시 폴더 백업 후 삭제")
    print("4. 트리거 빌더 개발 진행!")


if __name__ == "__main__":
    main()
