#!/usr/bin/env python3
"""
🔍 Super DB Inspector
DB 상태 관찰 전문 도구 - 실시간 DB 분석 및 모니터링

🤖 LLM 사용 가이드:
===================
이 도구는 DB 상태를 빠르고 정확하게 파악하기 위한 통합 분석 도구입니다.

📋 주요 명령어 (tools 폴더에서 실행):
1. python super_db_inspector.py --quick-status           # 3초 내 전체 DB 상태 요약 ⭐
2. python super_db_inspector.py --tv-variables           # TV 변수 시스템 전용 분석 ⭐
3. python super_db_inspector.py --data-flow              # YAML→DB→Code 데이터 흐름 추적
4. python super_db_inspector.py --export-current         # 현재 DB 상태를 YAML로 추출
5. python super_db_inspector.py --watch-changes          # 실시간 DB 변경 모니터링
6. python super_db_inspector.py --compare-schemas        # 스키마 버전 비교

🎯 사용 시나리오:
- ⚡ 빠른 상태 확인: --quick-status (개발 중 가장 많이 사용)
- 🔍 변수 시스템 분석: --tv-variables (TV 관련 작업 시)
- 📊 데이터 추적: --data-flow (마이그레이션 전후)
- 💾 현재 상태 백업: --export-current (안전한 작업 전)

💡 기존 도구 통합:
- super_db_table_viewer.py → 기본 테이블 조회 기능
- super_db_analyze_parameter_table.py → TV 변수 파라미터 분석
- super_db_extraction_db_to_yaml.py → DB→YAML 추출
- super_db_schema_extractor.py → 스키마 정보 추출

작성일: 2025-08-16
작성자: Upbit Auto Trading Team
"""

import sqlite3
import re
import yaml
import time
from pathlib import Path
from typing import Dict
from datetime import datetime
from dataclasses import dataclass
import argparse
import sys

# 프로젝트 루트를 파이썬 패스에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class DatabaseStatus:
    """데이터베이스 상태 정보"""
    name: str
    file_size_mb: float
    table_count: int
    total_records: int
    tv_tables: Dict[str, int]  # TV 관련 테이블과 레코드 수
    last_modified: str
    health_score: float


@dataclass
class TVVariableInfo:
    """TV 변수 정보"""
    variable_id: str
    name: str
    category: str
    has_parameters: bool
    parameter_count: int
    usage_frequency: int = 0


class SuperDBInspector:
    """
    🔍 DB 상태 관찰 전문 도구

    주요 기능:
    1. 빠른 상태 확인 (3초 내)
    2. TV 변수 시스템 전용 분석
    3. 데이터 흐름 추적
    4. 실시간 변경 모니터링
    5. 현재 상태 YAML 추출
    """

    def __init__(self):
        self.db_paths = {
            'settings': Path('data/settings.sqlite3'),
            'market_data': Path('data/market_data.sqlite3'),
            'strategies': Path('data/strategies.sqlite3')
        }
        self.data_info_path = Path('data_info')
        self.start_time = time.time()

    def quick_status(self) -> None:
        """⚡ 3초 내 전체 DB 상태 요약"""
        print("🔍 === Super DB Inspector - Quick Status ===\n")

        db_statuses = []
        total_tables = 0
        total_records = 0

        for db_name, db_path in self.db_paths.items():
            if not db_path.exists():
                print(f"❌ {db_name}: 파일 없음")
                continue

            status = self._get_database_status(db_name, db_path)
            db_statuses.append(status)
            total_tables += status.table_count
            total_records += status.total_records

            # 상태 출력
            health_emoji = "🟢" if status.health_score >= 90 else "🟡" if status.health_score >= 70 else "🔴"
            print(f"{health_emoji} {status.name.upper()}: {status.table_count}개 테이블, {status.total_records:,}개 레코드")
            print(f"   📁 크기: {status.file_size_mb:.1f}MB, 수정: {status.last_modified}")

            # TV 테이블 요약
            if status.tv_tables:
                tv_summary = ", ".join([f"{table}: {count}" for table, count in status.tv_tables.items()])
                print(f"   🎯 TV 테이블: {tv_summary}")
            print()

        # 전체 요약
        elapsed = time.time() - self.start_time
        print("📊 === 전체 요약 ===")
        print(f"📋 총 테이블: {total_tables}개")
        print(f"📈 총 레코드: {total_records:,}개")
        print(f"⏱️ 분석 시간: {elapsed:.2f}초")

    def tv_variables_analysis(self) -> None:
        """🎯 TV 변수 시스템 전용 분석"""
        print("🎯 === TV 변수 시스템 분석 ===\n")

        settings_db = self.db_paths['settings']
        if not settings_db.exists():
            print("❌ settings.sqlite3 파일이 없습니다.")
            return

        try:
            conn = sqlite3.connect(settings_db)
            cursor = conn.cursor()

            # TV 변수 목록 조회
            cursor.execute("""
                SELECT variable_id, display_name, purpose_category
                FROM tv_trading_variables
                ORDER BY purpose_category, display_name
            """)
            variables = cursor.fetchall()

            # 파라미터 정보 조회
            cursor.execute("""
                SELECT variable_id, COUNT(*) as param_count
                FROM tv_variable_parameters
                GROUP BY variable_id
            """)
            parameters = dict(cursor.fetchall())

            # 카테고리별 분석
            category_stats = {}
            tv_vars = []

            for var_id, name, category in variables:
                param_count = parameters.get(var_id, 0)
                tv_var = TVVariableInfo(
                    variable_id=var_id,
                    name=name,
                    category=category,
                    has_parameters=param_count > 0,
                    parameter_count=param_count
                )
                tv_vars.append(tv_var)

                if category not in category_stats:
                    category_stats[category] = {'count': 0, 'with_params': 0, 'total_params': 0}
                category_stats[category]['count'] += 1
                if param_count > 0:
                    category_stats[category]['with_params'] += 1
                    category_stats[category]['total_params'] += param_count

            # 결과 출력
            print(f"📋 총 TV 변수: {len(variables)}개")
            print(f"⚙️ 파라미터 있는 변수: {len(parameters)}개")
            print(f"📊 총 파라미터: {sum(parameters.values())}개\n")

            # 카테고리별 상세
            for category, stats in category_stats.items():
                print(f"🏷️ {category}:")
                print(f"   📋 변수 수: {stats['count']}개")
                print(f"   ⚙️ 파라미터 보유: {stats['with_params']}개")
                print(f"   📊 총 파라미터: {stats['total_params']}개")

                # 해당 카테고리 변수들 나열
                category_vars = [v for v in tv_vars if v.category == category]
                for var in category_vars[:5]:  # 상위 5개만 표시
                    param_info = f"({var.parameter_count}개 파라미터)" if var.has_parameters else "(파라미터 없음)"
                    print(f"     • {var.name} {param_info}")
                if len(category_vars) > 5:
                    print(f"     ... 외 {len(category_vars) - 5}개")
                print()

            conn.close()

        except Exception as e:
            print(f"❌ TV 변수 분석 중 오류: {e}")

    def data_flow_tracking(self) -> None:
        """📊 YAML→DB→Code 데이터 흐름 추적"""
        print("📊 === 데이터 흐름 추적 ===\n")

        # 1. YAML 파일 분석
        yaml_files = list(self.data_info_path.glob("**/*.yaml"))
        print(f"📁 data_info YAML 파일: {len(yaml_files)}개")

        yaml_stats = {}
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict):
                        yaml_stats[yaml_file.name] = len(data)
                    elif isinstance(data, list):
                        yaml_stats[yaml_file.name] = len(data)
                    else:
                        yaml_stats[yaml_file.name] = 1
            except:
                yaml_stats[yaml_file.name] = 0

        for filename, count in yaml_stats.items():
            print(f"   📄 {filename}: {count}개 항목")
        print()

        # 2. DB 테이블 상태
        settings_db = self.db_paths['settings']
        if settings_db.exists():
            conn = sqlite3.connect(settings_db)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'tv_%'")
            tv_tables = [row[0] for row in cursor.fetchall()]

            print(f"💾 DB TV 테이블: {len(tv_tables)}개")
            for table in tv_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   📊 {table}: {count}개 레코드")
            print()

            conn.close()

        # 3. 코드 참조 분석 (간단 버전)
        code_files = list(PROJECT_ROOT.glob("upbit_auto_trading/**/*.py"))
        tv_references = {}

        print("🔍 코드 참조 분석 (상위 10개):")
        for code_file in code_files[:50]:  # 성능을 위해 일부만 검사
            try:
                with open(code_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # TV 테이블 참조 찾기
                    for table in tv_tables:
                        if table in content:
                            if table not in tv_references:
                                tv_references[table] = 0
                            tv_references[table] += content.count(table)
            except:
                continue

        # 상위 참조 테이블
        sorted_refs = sorted(tv_references.items(), key=lambda x: x[1], reverse=True)
        for table, count in sorted_refs[:10]:
            print(f"   📝 {table}: {count}회 참조")

        print(f"\n⏱️ 분석 완료: {time.time() - self.start_time:.2f}초")

    def export_current_state(self, output_dir: str = "temp/db_exports") -> None:
        """💾 현재 DB 상태를 YAML로 추출"""
        print("💾 === 현재 DB 상태 추출 ===\n")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for db_name, db_path in self.db_paths.items():
            if not db_path.exists():
                continue

            print(f"📊 {db_name} DB 추출 중...")

            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # 테이블 목록 조회
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                db_export = {}
                for table in tables:
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()

                    # 컬럼 정보
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in cursor.fetchall()]

                    # 데이터 변환
                    table_data = []
                    for row in rows:
                        row_dict = dict(zip(columns, row))
                        table_data.append(row_dict)

                    db_export[table] = {
                        'schema': columns,
                        'data': table_data,
                        'record_count': len(table_data)
                    }

                # YAML 파일로 저장
                output_file = output_path / f"{db_name}_export_{timestamp}.yaml"
                with open(output_file, 'w', encoding='utf-8') as f:
                    yaml.dump(db_export, f, default_flow_style=False, allow_unicode=True)

                print(f"   ✅ 저장: {output_file}")
                print(f"   📊 {len(tables)}개 테이블, {sum(len(t['data']) for t in db_export.values())}개 레코드")

                conn.close()

            except Exception as e:
                print(f"   ❌ 오류: {e}")

        print(f"\n📁 출력 폴더: {output_path.absolute()}")

    def compare_schemas(self) -> None:
        """📋 스키마 버전 비교"""
        print("📋 === 스키마 버전 비교 ===\n")

        # data_info 스키마 파일들 찾기
        schema_files = list(self.data_info_path.glob("**/*.sql"))
        print(f"🔍 발견된 스키마 파일: {len(schema_files)}개")

        for schema_file in schema_files:
            print(f"📄 {schema_file.name}")

            # 실제 DB와 비교
            for db_name, db_path in self.db_paths.items():
                if db_path.exists():
                    similarity = self._compare_schema_with_db(schema_file, db_path)
                    if similarity > 0:
                        print(f"   📊 {db_name} DB와 유사도: {similarity:.1f}%")
        print()

    def watch_changes(self, interval: int = 5) -> None:
        """👁️ 실시간 DB 변경 모니터링"""
        print(f"👁️ === 실시간 DB 변경 모니터링 (간격: {interval}초) ===")
        print("Ctrl+C로 종료\n")

        # 초기 상태 저장
        initial_stats = {}
        for db_name, db_path in self.db_paths.items():
            if db_path.exists():
                initial_stats[db_name] = self._get_db_stats(db_path)

        try:
            while True:
                time.sleep(interval)

                # 현재 상태 확인
                changes_detected = False
                for db_name, db_path in self.db_paths.items():
                    if not db_path.exists():
                        continue

                    current_stats = self._get_db_stats(db_path)
                    initial = initial_stats.get(db_name, {})

                    # 변경 사항 확인
                    for table, count in current_stats.items():
                        if table not in initial or initial[table] != count:
                            print(f"🔄 {datetime.now().strftime('%H:%M:%S')} - {db_name}.{table}: {initial.get(table, 0)} → {count}")
                            changes_detected = True
                            initial_stats[db_name][table] = count

                if not changes_detected:
                    print(f"✅ {datetime.now().strftime('%H:%M:%S')} - 변경 사항 없음")

        except KeyboardInterrupt:
            print("\n👋 모니터링 종료")

    def _get_database_status(self, db_name: str, db_path: Path) -> DatabaseStatus:
        """데이터베이스 상태 정보 수집"""
        try:
            # 파일 정보
            stat = db_path.stat()
            file_size_mb = stat.st_size / (1024 * 1024)
            last_modified = datetime.fromtimestamp(stat.st_mtime).strftime('%m/%d %H:%M')

            # DB 정보
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 테이블 수
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]

            # 총 레코드 수
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            total_records = 0
            tv_tables = {}

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_records += count

                # TV 관련 테이블 식별
                if table.startswith('tv_') or 'variable' in table.lower():
                    tv_tables[table] = count

            conn.close()

            # 건강도 점수 계산 (간단한 휴리스틱)
            health_score = min(100, 80 + (table_count * 2) + (len(tv_tables) * 5))

            return DatabaseStatus(
                name=db_name,
                file_size_mb=file_size_mb,
                table_count=table_count,
                total_records=total_records,
                tv_tables=tv_tables,
                last_modified=last_modified,
                health_score=health_score
            )

        except Exception as e:
            return DatabaseStatus(
                name=db_name,
                file_size_mb=0,
                table_count=0,
                total_records=0,
                tv_tables={},
                last_modified="오류",
                health_score=0
            )

    def _get_db_stats(self, db_path: Path) -> Dict[str, int]:
        """DB 테이블별 레코드 수 조회"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            stats = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]

            conn.close()
            return stats

        except:
            return {}

    def _compare_schema_with_db(self, schema_file: Path, db_path: Path) -> float:
        """스키마 파일과 DB 비교"""
        try:
            # 스키마 파일에서 테이블 이름 추출
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_content = f.read()

            schema_tables = set(re.findall(r'CREATE TABLE (\w+)', schema_content, re.IGNORECASE))

            # DB 테이블 조회
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            db_tables = set(row[0] for row in cursor.fetchall())
            conn.close()

            if not schema_tables or not db_tables:
                return 0

            # 유사도 계산
            intersection = schema_tables & db_tables
            union = schema_tables | db_tables

            return (len(intersection) / len(union)) * 100

        except:
            return 0


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='Super DB Inspector - DB 상태 관찰 전문 도구')
    parser.add_argument('--quick-status', action='store_true', help='3초 내 전체 DB 상태 요약')
    parser.add_argument('--tv-variables', action='store_true', help='TV 변수 시스템 전용 분석')
    parser.add_argument('--data-flow', action='store_true', help='YAML→DB→Code 데이터 흐름 추적')
    parser.add_argument('--export-current', action='store_true', help='현재 DB 상태를 YAML로 추출')
    parser.add_argument('--compare-schemas', action='store_true', help='스키마 버전 비교')
    parser.add_argument('--watch-changes', action='store_true', help='실시간 DB 변경 모니터링')
    parser.add_argument('--output-dir', default='temp/db_exports', help='출력 디렉토리 (기본: temp/db_exports)')
    parser.add_argument('--interval', type=int, default=5, help='모니터링 간격 (초, 기본: 5)')

    args = parser.parse_args()

    inspector = SuperDBInspector()

    # 아무 옵션이 없으면 quick-status 실행
    if not any(vars(args).values()):
        inspector.quick_status()
        return

    if args.quick_status:
        inspector.quick_status()

    if args.tv_variables:
        inspector.tv_variables_analysis()

    if args.data_flow:
        inspector.data_flow_tracking()

    if args.export_current:
        inspector.export_current_state(args.output_dir)

    if args.compare_schemas:
        inspector.compare_schemas()

    if args.watch_changes:
        inspector.watch_changes(args.interval)


if __name__ == "__main__":
    main()
