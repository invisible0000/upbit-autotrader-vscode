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
3. python super_db_inspector.py --meta-variables         # 메타변수 상세 분석 (호환성 문제 해결) 🆕
4. python super_db_inspector.py --view-table 테이블명    # 특정 테이블 내용 조회 🆕
5. python super_db_inspector.py --list-tables            # 모든 테이블 목록 출력 🆕
6. python super_db_inspector.py --export-current         # 현재 DB 상태를 YAML로 추출
7. python super_db_inspector.py --data-flow              # YAML→DB→Code 데이터 흐름 추적
8. python super_db_inspector.py --watch-changes          # 실시간 DB 변경 모니터링

🎯 사용 시나리오:
- ⚡ 빠른 상태 확인: --quick-status (개발 중 가장 많이 사용)
- 🔍 변수 시스템 분석: --tv-variables (TV 관련 작업 시)
- 🔧 메타변수 문제 해결: --meta-variables (호환성 검증 문제 시)
- 📋 테이블 데이터 확인: --view-table tv_trading_variables
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

            # TV 변수 목록 조회 (올바른 컬럼명 사용)
            cursor.execute("""
                SELECT variable_id, display_name_ko, display_name_en, purpose_category, comparison_group
                FROM tv_trading_variables
                ORDER BY purpose_category, display_name_ko
            """)
            variables = cursor.fetchall()

            # 파라미터 정보 조회
            cursor.execute("""
                SELECT variable_id, COUNT(*) as param_count
                FROM tv_variable_parameters
                GROUP BY variable_id
            """)
            parameters = dict(cursor.fetchall())

            # 헬프 문서 정보 조회
            cursor.execute("""
                SELECT variable_id, COUNT(*) as help_count
                FROM tv_variable_help_documents
                GROUP BY variable_id
            """)
            help_docs = dict(cursor.fetchall())

            # 카테고리별 분석
            category_stats = {}
            tv_vars = []
            meta_vars = []

            for var_id, name_ko, name_en, category, comp_group in variables:
                param_count = parameters.get(var_id, 0)
                help_count = help_docs.get(var_id, 0)

                tv_var = TVVariableInfo(
                    variable_id=var_id,
                    name=name_ko or name_en or var_id,
                    category=category,
                    has_parameters=param_count > 0,
                    parameter_count=param_count
                )
                tv_vars.append(tv_var)

                # 메타변수 별도 수집
                if category == 'dynamic_management':
                    meta_vars.append((var_id, name_ko, comp_group, param_count, help_count))

                if category not in category_stats:
                    category_stats[category] = {'count': 0, 'with_params': 0, 'total_params': 0, 'with_help': 0}
                category_stats[category]['count'] += 1
                if param_count > 0:
                    category_stats[category]['with_params'] += 1
                    category_stats[category]['total_params'] += param_count
                if help_count > 0:
                    category_stats[category]['with_help'] += 1

            # 결과 출력
            print(f"📋 총 TV 변수: {len(variables)}개")
            print(f"⚙️ 파라미터 있는 변수: {len(parameters)}개")
            print(f"📊 총 파라미터: {sum(parameters.values())}개")
            print(f"📖 헬프 문서 있는 변수: {len(help_docs)}개\n")

            # 메타변수 특별 분석
            if meta_vars:
                print("🔧 === 메타변수 (dynamic_management) 분석 ===")
                for var_id, name_ko, comp_group, param_count, help_count in meta_vars:
                    help_status = "✅" if help_count > 0 else "❌"
                    param_status = f"({param_count}개)" if param_count > 0 else "(파라미터 없음)"
                    print(f"   • {name_ko} [{var_id}]")
                    print(f"     - 비교그룹: {comp_group}")
                    print(f"     - 파라미터: {param_status}")
                    print(f"     - 헬프문서: {help_status} ({help_count}개)")
                print()

            # 카테고리별 상세
            for category, stats in category_stats.items():
                print(f"🏷️ {category}:")
                print(f"   📋 변수 수: {stats['count']}개")
                print(f"   ⚙️ 파라미터 보유: {stats['with_params']}개")
                print(f"   📊 총 파라미터: {stats['total_params']}개")
                print(f"   📖 헬프 문서 보유: {stats['with_help']}개")

                # 해당 카테고리 변수들 나열
                category_vars = [v for v in tv_vars if v.category == category]
                for var in category_vars[:3]:  # 상위 3개만 표시
                    param_info = f"({var.parameter_count}개)" if var.has_parameters else "(없음)"
                    print(f"     • {var.name} {param_info}")
                if len(category_vars) > 3:
                    print(f"     ... 외 {len(category_vars) - 3}개")
                print()

            conn.close()

        except Exception as e:
            print(f"❌ TV 변수 분석 중 오류: {e}")
            import traceback
            traceback.print_exc()

    def view_table(self, table_name: str, limit: int = 20) -> None:
        """📋 특정 테이블 내용 조회"""
        print(f"📋 === 테이블 뷰어: {table_name} ===\n")

        # 테이블이 어느 DB에 있는지 찾기
        found_db = None
        for db_name, db_path in self.db_paths.items():
            if not db_path.exists():
                continue

            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if cursor.fetchone():
                    found_db = db_name
                    break
                conn.close()
            except:
                continue

        if not found_db:
            print(f"❌ 테이블 '{table_name}'을(를) 찾을 수 없습니다.")
            print("\n📋 사용 가능한 테이블 목록:")
            self._list_all_tables()
            return

        try:
            conn = sqlite3.connect(self.db_paths[found_db])
            cursor = conn.cursor()

            # 테이블 스키마 정보
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]

            print(f"🗄️ 데이터베이스: {found_db}")
            print(f"📊 컬럼 수: {len(columns)}개")
            print(f"📋 컬럼: {', '.join(columns)}")

            # 총 레코드 수
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_count = cursor.fetchone()[0]
            print(f"📈 총 레코드: {total_count:,}개")

            if total_count == 0:
                print("⚠️ 데이터가 없습니다.")
                conn.close()
                return

            # 데이터 조회
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            rows = cursor.fetchall()

            print(f"\n📄 데이터 (상위 {len(rows)}개):")
            print("=" * 80)

            for i, row in enumerate(rows):
                print(f"\n레코드 #{i+1}:")
                for col, value in zip(columns, row):
                    # 긴 텍스트는 잘라서 표시
                    if isinstance(value, str) and len(value) > 100:
                        display_value = value[:100] + "..."
                    else:
                        display_value = value
                    print(f"  {col}: {display_value}")

            if total_count > limit:
                print(f"\n💡 총 {total_count}개 중 {limit}개만 표시됨. --limit 옵션으로 개수 조정 가능")

            conn.close()

        except Exception as e:
            print(f"❌ 테이블 조회 중 오류: {e}")

    def _list_all_tables(self) -> None:
        """모든 데이터베이스의 테이블 목록 출력"""
        for db_name, db_path in self.db_paths.items():
            if not db_path.exists():
                continue

            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [row[0] for row in cursor.fetchall()]

                if tables:
                    print(f"\n🗄️ {db_name} DB:")
                    for table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        print(f"   • {table} ({count:,}개)")

                conn.close()
            except:
                continue

    def meta_variables_detail(self) -> None:
        """🔧 메타변수 상세 분석 (호환성 문제 해결용)"""
        print("🔧 === 메타변수 상세 분석 ===\n")

        settings_db = self.db_paths['settings']
        if not settings_db.exists():
            print("❌ settings.sqlite3 파일이 없습니다.")
            return

        try:
            conn = sqlite3.connect(settings_db)
            cursor = conn.cursor()

            # 메타변수 조회
            cursor.execute("""
                SELECT variable_id, display_name_ko, display_name_en,
                       comparison_group, purpose_category, description, is_active
                FROM tv_trading_variables
                WHERE purpose_category = 'dynamic_management'
                ORDER BY variable_id
            """)
            meta_vars = cursor.fetchall()

            print(f"🔧 발견된 메타변수: {len(meta_vars)}개\n")

            for var_id, name_ko, name_en, comp_group, category, desc, is_active in meta_vars:
                active_status = "✅ 활성" if is_active else "❌ 비활성"
                print(f"📌 {name_ko} [{var_id}]")
                print(f"   영문명: {name_en}")
                print(f"   상태: {active_status}")
                print(f"   비교그룹: {comp_group}")
                print(f"   설명: {desc}")

                # 파라미터 확인
                cursor.execute("""
                    SELECT parameter_name, default_value, parameter_type
                    FROM tv_variable_parameters
                    WHERE variable_id = ?
                """, (var_id,))
                params = cursor.fetchall()

                if params:
                    print(f"   파라미터 ({len(params)}개):")
                    for param_name, default_val, param_type in params:
                        print(f"     • {param_name}: {default_val} ({param_type})")
                else:
                    print(f"   파라미터: 없음")

                # 헬프 문서 확인
                cursor.execute("""
                    SELECT document_type, title_ko, content_ko
                    FROM tv_variable_help_documents
                    WHERE variable_id = ?
                """, (var_id,))
                help_docs = cursor.fetchall()

                if help_docs:
                    print(f"   헬프 문서 ({len(help_docs)}개):")
                    for doc_type, title, content in help_docs:
                        content_preview = content[:100] + "..." if content and len(content) > 100 else content
                        print(f"     • {doc_type}: {title}")
                        print(f"       내용: {content_preview}")
                else:
                    print(f"   헬프 문서: ❌ 없음")

                print()

            # 호환성 분석
            print("🔍 === 호환성 분석 ===")
            unique_comp_groups = set(var[2] for var in meta_vars)  # comparison_group
            print(f"메타변수 비교그룹: {', '.join(unique_comp_groups)}")

            # 일반 변수들의 비교그룹 확인
            cursor.execute("""
                SELECT DISTINCT comparison_group, COUNT(*) as count
                FROM tv_trading_variables
                WHERE purpose_category != 'dynamic_management'
                GROUP BY comparison_group
                ORDER BY count DESC
            """)
            regular_groups = cursor.fetchall()

            print("\n일반 변수 비교그룹:")
            for group, count in regular_groups:
                print(f"  • {group}: {count}개 변수")

            print("\n💡 호환성 권장사항:")
            print("   메타변수는 모든 변수와 호환되어야 하므로")
            print("   comparison_group을 'universal' 또는 별도 호환 로직이 필요합니다.")

            conn.close()

        except Exception as e:
            print(f"❌ 메타변수 분석 중 오류: {e}")
            import traceback
            traceback.print_exc()

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
    parser.add_argument('--meta-variables', action='store_true', help='메타변수 상세 분석 (호환성 문제 해결용)')
    parser.add_argument('--view-table', type=str, help='특정 테이블 내용 조회 (예: tv_trading_variables)')
    parser.add_argument('--list-tables', action='store_true', help='모든 테이블 목록 출력')
    parser.add_argument('--data-flow', action='store_true', help='YAML→DB→Code 데이터 흐름 추적')
    parser.add_argument('--export-current', action='store_true', help='현재 DB 상태를 YAML로 추출')
    parser.add_argument('--compare-schemas', action='store_true', help='스키마 버전 비교')
    parser.add_argument('--watch-changes', action='store_true', help='실시간 DB 변경 모니터링')
    parser.add_argument('--output-dir', default='temp/db_exports', help='출력 디렉토리 (기본: temp/db_exports)')
    parser.add_argument('--interval', type=int, default=5, help='모니터링 간격 (초, 기본: 5)')
    parser.add_argument('--limit', type=int, default=20, help='테이블 조회 시 레코드 수 제한 (기본: 20)')

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

    if args.meta_variables:
        inspector.meta_variables_detail()

    if args.view_table:
        inspector.view_table(args.view_table, args.limit)

    if args.list_tables:
        print("📋 === 전체 테이블 목록 ===")
        inspector._list_all_tables()

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
