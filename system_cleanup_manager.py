#!/usr/bin/env python3
"""
시스템 정리 실행 스크립트

1. 레거시 폴더 안전 삭제
2. 코드에서 실제 사용하는 테이블 식별
3. 미사용 테이블 정리 권장사항 제공
4. 트리거 빌더 개발을 위한 최적화된 DB 구조 제안
"""

import sqlite3
from pathlib import Path
import shutil
import json
from datetime import datetime


class SystemCleaner:
    """시스템 정리 실행기"""

    def __init__(self):
        self.project_root = Path(".")
        self.backup_dir = Path("_cleanup_backup")

    def step1_check_legacy_folders(self):
        """1단계: 레거시 폴더 현황 확인"""
        print("🔍 1단계: 레거시 폴더 현황 확인")

        folders_to_check = [
            "data_info/indicators",
            "data_info/tv_variable_help_guides"
        ]

        results = {}
        for folder_path in folders_to_check:
            path = Path(folder_path)
            if path.exists():
                files = list(path.rglob("*"))
                file_count = len([f for f in files if f.is_file()])
                results[folder_path] = {
                    "exists": True,
                    "file_count": file_count,
                    "files": [str(f) for f in files if f.is_file()]
                }
                print(f"  📂 {folder_path}: {file_count}개 파일 발견")
            else:
                results[folder_path] = {"exists": False}
                print(f"  ❌ {folder_path}: 존재하지 않음")

        return results

    def step2_analyze_database_usage(self):
        """2단계: 실제 사용되는 테이블 식별"""
        print("\n💾 2단계: 데이터베이스 테이블 사용 현황 분석")

        # 트리거 빌더 개발 관점에서 필요한 핵심 테이블들
        essential_tables = {
            "settings.sqlite3": [
                "tv_trading_variables",      # 거래 변수 정의
                "tv_variable_parameters",    # 변수 파라미터
                "tv_variable_help_documents", # 도움말 문서
                "tv_help_texts",             # 간단 도움말
                "tv_placeholder_texts",      # 플레이스홀더
                "api_keys",                  # API 키 (암호화된)
                "user_settings"              # 사용자 설정
            ],
            "strategies.sqlite3": [
                # 트리거 빌더 개발 단계에서는 비어있는 것이 좋음
                "strategy_definitions",      # 전략 정의 (향후 사용)
                "strategy_triggers",         # 트리거 설정 (향후 사용)
            ],
            "market_data.sqlite3": [
                # 트리거 빌더 개발 단계에서는 비어있는 것이 좋음
                "price_data",               # 가격 데이터 (향후 사용)
                "indicators_cache",         # 지표 캐시 (향후 사용)
            ]
        }

        # 실제 DB 현황 확인
        actual_tables = {}
        for db_name in ["data/settings.sqlite3", "data/strategies.sqlite3", "data/market_data.sqlite3"]:
            db_path = Path(db_name)
            if db_path.exists():
                try:
                    with sqlite3.connect(str(db_path)) as conn:
                        cursor = conn.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                        )
                        tables = [row[0] for row in cursor.fetchall()]
                        actual_tables[db_name] = tables
                        print(f"  📊 {db_name}: {len(tables)}개 테이블")
                        for table in tables:
                            print(f"    - {table}")
                except Exception as e:
                    print(f"  ❌ {db_name} 분석 오류: {e}")
                    actual_tables[db_name] = []
            else:
                print(f"  ❌ {db_name}: 파일 없음")
                actual_tables[db_name] = []

        return {"essential": essential_tables, "actual": actual_tables}

    def step3_safe_cleanup_legacy_folders(self, folder_analysis):
        """3단계: 레거시 폴더 안전 삭제"""
        print("\n🗑️  3단계: 레거시 폴더 안전 삭제")

        # 백업 디렉토리 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"legacy_backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)

        deleted_folders = []

        for folder_path, info in folder_analysis.items():
            if info.get("exists") and info.get("file_count", 0) > 0:
                source = Path(folder_path)
                backup_dest = backup_path / folder_path

                print(f"  📦 백업 중: {folder_path} → {backup_dest}")

                try:
                    # 백업 생성
                    backup_dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(source, backup_dest)

                    # 원본 삭제
                    shutil.rmtree(source)
                    deleted_folders.append(folder_path)
                    print(f"  ✅ 삭제 완료: {folder_path}")

                except Exception as e:
                    print(f"  ❌ 삭제 실패: {folder_path} - {e}")

        print(f"\n  📁 백업 위치: {backup_path}")
        print(f"  🗑️  삭제된 폴더: {len(deleted_folders)}개")

        return {"backup_path": str(backup_path), "deleted": deleted_folders}

    def step4_generate_db_cleanup_recommendations(self, db_analysis):
        """4단계: DB 정리 권장사항 생성"""
        print("\n📋 4단계: 데이터베이스 정리 권장사항")

        essential = db_analysis["essential"]
        actual = db_analysis["actual"]

        recommendations = {
            "settings.sqlite3": {
                "keep": [],
                "consider_removing": [],
                "missing_essential": []
            },
            "strategies.sqlite3": {
                "action": "개발 단계에서는 테이블을 비우거나 최소화 권장",
                "reason": "트리거 빌더 개발에 집중하기 위해"
            },
            "market_data.sqlite3": {
                "action": "개발 단계에서는 테이블을 비우거나 최소화 권장",
                "reason": "실시간 데이터 없이도 UI 개발 가능"
            }
        }

        # settings.sqlite3 상세 분석
        settings_essential = essential.get("settings.sqlite3", [])
        settings_actual = actual.get("data/settings.sqlite3", [])

        for table in settings_actual:
            if table in settings_essential:
                recommendations["settings.sqlite3"]["keep"].append(table)
            else:
                recommendations["settings.sqlite3"]["consider_removing"].append(table)

        for table in settings_essential:
            if table not in settings_actual:
                recommendations["settings.sqlite3"]["missing_essential"].append(table)

        print("  📊 settings.sqlite3:")
        print(f"    ✅ 유지 권장: {len(recommendations['settings.sqlite3']['keep'])}개")
        for table in recommendations["settings.sqlite3"]["keep"]:
            print(f"      - {table}")

        print(f"    🤔 제거 검토: {len(recommendations['settings.sqlite3']['consider_removing'])}개")
        for table in recommendations["settings.sqlite3"]["consider_removing"]:
            print(f"      - {table}")

        if recommendations["settings.sqlite3"]["missing_essential"]:
            print(f"    ❌ 누락된 필수: {len(recommendations['settings.sqlite3']['missing_essential'])}개")
            for table in recommendations["settings.sqlite3"]["missing_essential"]:
                print(f"      - {table}")

        print("\n  📊 strategies.sqlite3:")
        print(f"    💡 {recommendations['strategies.sqlite3']['action']}")
        print(f"    📝 이유: {recommendations['strategies.sqlite3']['reason']}")

        print("\n  📊 market_data.sqlite3:")
        print(f"    💡 {recommendations['market_data.sqlite3']['action']}")
        print(f"    📝 이유: {recommendations['market_data.sqlite3']['reason']}")

        return recommendations

    def step5_generate_cleanup_script(self, recommendations):
        """5단계: 실제 정리를 위한 SQL 스크립트 생성"""
        print("\n📜 5단계: 정리 실행 스크립트 생성")

        cleanup_sql = {
            "settings_cleanup.sql": [],
            "strategies_cleanup.sql": [],
            "market_data_cleanup.sql": []
        }

        # settings.sqlite3 정리 스크립트
        tables_to_remove = recommendations["settings.sqlite3"]["consider_removing"]
        if tables_to_remove:
            cleanup_sql["settings_cleanup.sql"].append("-- Settings DB 불필요 테이블 제거")
            cleanup_sql["settings_cleanup.sql"].append("-- 실행 전 반드시 백업 수행!")
            cleanup_sql["settings_cleanup.sql"].append("")

            for table in tables_to_remove:
                cleanup_sql["settings_cleanup.sql"].append(f"-- DROP TABLE IF EXISTS {table};")

            cleanup_sql["settings_cleanup.sql"].append("")
            cleanup_sql["settings_cleanup.sql"].append("-- VACUUM으로 DB 크기 최적화")
            cleanup_sql["settings_cleanup.sql"].append("VACUUM;")

        # strategies.sqlite3 정리 스크립트
        cleanup_sql["strategies_cleanup.sql"].extend([
            "-- Strategies DB 개발용 정리",
            "-- 트리거 빌더 개발 단계에서는 데이터 없이 스키마만 유지",
            "",
            "-- 모든 테이블의 데이터 삭제 (스키마는 유지)",
            "-- DELETE FROM strategy_definitions;",
            "-- DELETE FROM strategy_triggers;",
            "",
            "-- 또는 테이블 자체 제거 후 나중에 재생성",
            "-- DROP TABLE IF EXISTS strategy_definitions;",
            "-- DROP TABLE IF EXISTS strategy_triggers;",
            "",
            "VACUUM;"
        ])

        # market_data.sqlite3 정리 스크립트
        cleanup_sql["market_data_cleanup.sql"].extend([
            "-- Market Data DB 개발용 정리",
            "-- 개발 단계에서는 실시간 데이터 불필요",
            "",
            "-- 모든 테이블의 데이터 삭제 (스키마는 유지)",
            "-- DELETE FROM price_data;",
            "-- DELETE FROM indicators_cache;",
            "",
            "-- 또는 테이블 자체 제거 후 나중에 재생성",
            "-- DROP TABLE IF EXISTS price_data;",
            "-- DROP TABLE IF EXISTS indicators_cache;",
            "",
            "VACUUM;"
        ])

        # 스크립트 파일 생성
        for filename, content in cleanup_sql.items():
            if content:
                script_path = Path(f"_cleanup_scripts/{filename}")
                script_path.parent.mkdir(exist_ok=True)

                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(content))

                print(f"  📜 생성됨: {script_path}")

        return cleanup_sql

    def run_complete_analysis(self):
        """전체 정리 분석 실행"""
        print("🧹 시스템 종합 정리 분석 시작\n")
        print("="*60)

        # 각 단계 실행
        folder_analysis = self.step1_check_legacy_folders()
        db_analysis = self.step2_analyze_database_usage()

        # 실제 정리 실행 여부 확인
        print("\n" + "="*60)
        print("🎯 정리 실행 계획")
        print("="*60)

        print("\n💡 권장 실행 순서:")
        print("1. 레거시 폴더 백업 및 삭제")
        print("2. 데이터베이스 테이블 정리")
        print("3. 트리거 빌더 개발 환경 최적화")

        # 결과 요약
        result_summary = {
            "timestamp": datetime.now().isoformat(),
            "folder_analysis": folder_analysis,
            "db_analysis": db_analysis,
            "recommendations": self.step4_generate_db_cleanup_recommendations(db_analysis)
        }

        # 결과 저장
        with open("_cleanup_analysis_result.json", 'w', encoding='utf-8') as f:
            json.dump(result_summary, f, ensure_ascii=False, indent=2)

        print(f"\n📊 분석 결과 저장됨: _cleanup_analysis_result.json")

        return result_summary

    def execute_safe_cleanup(self):
        """안전한 정리 실행"""
        print("🚀 안전한 시스템 정리 실행\n")

        # 분석 먼저 실행
        analysis = self.run_complete_analysis()

        print("\n" + "="*60)
        print("🗑️  실제 정리 실행")
        print("="*60)

        # 레거시 폴더 정리
        cleanup_result = self.step3_safe_cleanup_legacy_folders(
            analysis["folder_analysis"]
        )

        # 정리 스크립트 생성
        self.step5_generate_cleanup_script(analysis["recommendations"])

        print("\n✅ 정리 완료!")
        print("\n📋 다음 단계:")
        print("1. _cleanup_scripts/ 폴더의 SQL 스크립트들을 검토")
        print("2. 필요한 경우 데이터베이스 백업 후 스크립트 실행")
        print("3. 트리거 빌더 개발에 집중!")

        return cleanup_result


def main():
    print("🔧 업비트 자동매매 시스템 정리 도구")
    print("="*50)

    cleaner = SystemCleaner()

    # 분석만 실행 (안전한 옵션)
    print("\n옵션을 선택하세요:")
    print("1. 분석만 실행 (추천)")
    print("2. 분석 + 실제 정리 실행")

    # 일단 분석만 실행
    print("\n🔍 분석만 실행합니다...")
    result = cleaner.run_complete_analysis()

    print(f"\n🎉 분석 완료! 결과를 확인하고 다음 단계를 진행하세요.")


if __name__ == "__main__":
    main()
