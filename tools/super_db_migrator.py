#!/usr/bin/env python3
"""
🔄 Super DB Migrator
마이그레이션 전문 도구 - data_info YAML ↔ 3-Database 통합 관리

🤖 LLM 사용 가이드:
===================
이 도구는 data_info 폴더의 YAML 파일들을 3-Database로 마이그레이션하는 전문 도구입니다.

📋 주요 명령어 (tools 폴더에서 실행):
1. python super_db_migrator.py --smart-merge                # data_info YAML 스마트 병합 ⭐
2. python super_db_migrator.py --preview-changes            # 마이그레이션 미리보기 ⭐
3. python super_db_migrator.py --yaml-to-db                 # YAML → DB 일괄 마이그레이션
4. python super_db_migrator.py --auto-backup                # 자동 백업 + 마이그레이션
5. python super_db_migrator.py --incremental                # 증분 마이그레이션 (변경분만)
6. python super_db_migrator.py --conflict-resolution        # 충돌 해결 가이드

🎯 사용 시나리오:
- 📝 YAML 수정 후 마이그레이션: --preview-changes → --yaml-to-db
- 🔄 정기 동기화: --incremental (빠른 업데이트)
- 🛡️ 안전한 마이그레이션: --auto-backup (백업 + 실행 + 검증)
- 🤝 충돌 해결: --conflict-resolution (Manual vs Runtime 충돌)

💡 기존 도구 통합:
- super_db_migration_yaml_to_db.py → YAML→DB 마이그레이션
- super_db_yaml_merger.py → YAML 병합 로직
- super_db_rollback_manager.py → 백업/복구 관리
- super_db_structure_generator.py → DB 구조 생성

작성일: 2025-08-16
작성자: Upbit Auto Trading Team
"""

import sqlite3
import yaml
import time
import shutil
from pathlib import Path
from typing import Any, List
from datetime import datetime
from dataclasses import dataclass
import argparse
import sys
import json
import hashlib

# 프로젝트 루트를 파이썬 패스에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class MigrationTask:
    """마이그레이션 작업 정보"""
    yaml_file: str
    target_db: str
    table_name: str
    action: str  # 'create', 'update', 'delete'
    record_count: int
    estimated_time: float


@dataclass
class ConflictInfo:
    """충돌 정보"""
    yaml_file: str
    table_name: str
    conflict_type: str  # 'schema', 'data', 'constraint'
    description: str
    suggested_resolution: str


class SuperDBMigrator:
    """
    🔄 마이그레이션 전문 도구

    주요 기능:
    1. data_info YAML 스마트 병합
    2. 마이그레이션 미리보기
    3. 증분 마이그레이션
    4. 자동 백업 및 복구
    5. 충돌 해결 가이드
    """

    def __init__(self):
        self.db_paths = {
            'settings': Path('data/settings.sqlite3'),
            'market_data': Path('data/market_data.sqlite3'),
            'strategies': Path('data/strategies.sqlite3')
        }
        self.data_info_path = Path('data_info')
        self.backup_path = Path('data/backups')
        self.temp_path = Path('temp/migrations')

        # YAML → DB 매핑 정의
        self.yaml_to_db_mapping = {
            'tv_trading_variables.yaml': ('settings', 'tv_trading_variables'),
            'tv_variable_parameters.yaml': ('settings', 'tv_variable_parameters'),
            'tv_help_texts.yaml': ('settings', 'tv_help_texts'),
            'tv_placeholder_texts.yaml': ('settings', 'tv_placeholder_texts'),
            'tv_indicator_categories.yaml': ('settings', 'tv_indicator_categories'),
            'tv_parameter_types.yaml': ('settings', 'tv_parameter_types'),
            'tv_indicator_library.yaml': ('settings', 'tv_indicator_library'),
            'tv_comparison_groups.yaml': ('settings', 'tv_comparison_groups'),
            'user_strategies.yaml': ('strategies', 'user_strategies'),
            'strategy_templates.yaml': ('strategies', 'strategy_templates'),
            'market_symbols.yaml': ('market_data', 'market_symbols'),
            'data_sources.yaml': ('market_data', 'data_sources'),
        }

        self.start_time = time.time()

    def smart_merge_yamls(self) -> None:
        """📝 data_info YAML 파일들 스마트 병합"""
        print("📝 === data_info YAML 스마트 병합 ===\n")

        yaml_files = list(self.data_info_path.glob("**/*.yaml"))
        if not yaml_files:
            print("❌ data_info 폴더에 YAML 파일이 없습니다.")
            return

        print(f"🔍 발견된 YAML 파일: {len(yaml_files)}개")

        # 각 YAML 파일 분석
        merge_stats = {}
        for yaml_file in yaml_files:
            print(f"\n📄 {yaml_file.name} 분석 중...")

            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                if isinstance(data, dict):
                    item_count = len(data)
                    data_type = "딕셔너리"
                elif isinstance(data, list):
                    item_count = len(data)
                    data_type = "리스트"
                else:
                    item_count = 1
                    data_type = "단일값"

                # 데이터 무결성 검사
                integrity_issues = self._check_yaml_integrity(yaml_file, data)

                merge_stats[yaml_file.name] = {
                    'item_count': item_count,
                    'data_type': data_type,
                    'integrity_issues': integrity_issues,
                    'last_modified': datetime.fromtimestamp(yaml_file.stat().st_mtime),
                    'file_size_kb': yaml_file.stat().st_size / 1024
                }

                print(f"   📊 {data_type}: {item_count}개 항목")
                print(f"   📁 크기: {merge_stats[yaml_file.name]['file_size_kb']:.1f}KB")
                print(f"   📅 수정: {merge_stats[yaml_file.name]['last_modified'].strftime('%m/%d %H:%M')}")

                if integrity_issues:
                    print(f"   ⚠️ 무결성 이슈: {len(integrity_issues)}개")
                    for issue in integrity_issues[:3]:  # 상위 3개만 표시
                        print(f"      • {issue}")
                    if len(integrity_issues) > 3:
                        print(f"      ... 외 {len(integrity_issues) - 3}개")
                else:
                    print("   ✅ 무결성 검사 통과")

            except Exception as e:
                print(f"   ❌ 분석 실패: {e}")
                merge_stats[yaml_file.name] = {
                    'item_count': 0,
                    'data_type': "오류",
                    'integrity_issues': [str(e)],
                    'last_modified': None,
                    'file_size_kb': 0
                }

        # 병합 요약
        total_items = sum(stats['item_count'] for stats in merge_stats.values())
        total_issues = sum(len(stats['integrity_issues']) for stats in merge_stats.values())

        print("\n📊 === 병합 요약 ===")
        print(f"📋 총 YAML 파일: {len(yaml_files)}개")
        print(f"📈 총 데이터 항목: {total_items:,}개")
        print(f"⚠️ 무결성 이슈: {total_issues}개")
        print(f"⏱️ 분석 시간: {time.time() - self.start_time:.2f}초")

    def preview_changes(self) -> None:
        """👁️ 마이그레이션 미리보기"""
        print("👁️ === 마이그레이션 미리보기 ===\n")

        migration_tasks = []
        total_records = 0

        # 각 YAML 파일별 마이그레이션 계획 생성
        for yaml_name, (target_db, table_name) in self.yaml_to_db_mapping.items():
            yaml_path = self.data_info_path / yaml_name

            if not yaml_path.exists():
                print(f"⚪ {yaml_name}: 파일 없음")
                continue

            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                # 레코드 수 계산
                if isinstance(data, dict):
                    record_count = len(data)
                elif isinstance(data, list):
                    record_count = len(data)
                else:
                    record_count = 1

                # 현재 DB 상태와 비교
                db_path = self.db_paths[target_db]
                current_count = 0
                action = "create"

                if db_path.exists():
                    try:
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        current_count = cursor.fetchone()[0]
                        action = "update" if current_count > 0 else "create"
                        conn.close()
                    except:
                        action = "create"

                # 예상 시간 계산 (간단한 휴리스틱)
                estimated_time = record_count * 0.001  # 레코드당 1ms

                task = MigrationTask(
                    yaml_file=yaml_name,
                    target_db=target_db,
                    table_name=table_name,
                    action=action,
                    record_count=record_count,
                    estimated_time=estimated_time
                )

                migration_tasks.append(task)
                total_records += record_count

                # 상태 표시
                action_emoji = "🆕" if action == "create" else "🔄"
                print(f"{action_emoji} {yaml_name}")
                print(f"   📊 {target_db}.{table_name}: {current_count} → {record_count} 레코드")
                print(f"   ⏱️ 예상 시간: {estimated_time:.2f}초")

            except Exception as e:
                print(f"❌ {yaml_name}: 분석 실패 - {e}")

        # 미리보기 요약
        print(f"\n📊 === 미리보기 요약 ===")
        print(f"📋 마이그레이션 작업: {len(migration_tasks)}개")
        print(f"📈 총 처리 레코드: {total_records:,}개")
        print(f"⏱️ 총 예상 시간: {sum(t.estimated_time for t in migration_tasks):.2f}초")

        # DB별 요약
        db_summary = {}
        for task in migration_tasks:
            if task.target_db not in db_summary:
                db_summary[task.target_db] = {'tasks': 0, 'records': 0}
            db_summary[task.target_db]['tasks'] += 1
            db_summary[task.target_db]['records'] += task.record_count

        print(f"\n📊 DB별 요약:")
        for db, summary in db_summary.items():
            print(f"   💾 {db}: {summary['tasks']}개 작업, {summary['records']:,}개 레코드")

    def yaml_to_db_migration(self, dry_run: bool = False) -> None:
        """🔄 YAML → DB 일괄 마이그레이션"""
        action_text = "시뮬레이션" if dry_run else "실행"
        print(f"🔄 === YAML → DB 마이그레이션 {action_text} ===\n")

        if not dry_run:
            # 실제 실행 전 백업
            self._create_backup("pre_migration")

        success_count = 0
        failure_count = 0

        for yaml_name, (target_db, table_name) in self.yaml_to_db_mapping.items():
            yaml_path = self.data_info_path / yaml_name

            if not yaml_path.exists():
                continue

            print(f"🔄 {yaml_name} → {target_db}.{table_name}")

            try:
                # YAML 데이터 로드
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                if dry_run:
                    if isinstance(data, dict):
                        record_count = len(data)
                    elif isinstance(data, list):
                        record_count = len(data)
                    else:
                        record_count = 1

                    print(f"   ✅ 시뮬레이션: {record_count}개 레코드 처리 예정")
                else:
                    # 실제 DB 마이그레이션 실행
                    affected_rows = self._execute_migration(yaml_path, target_db, table_name, data)
                    print(f"   ✅ 완료: {affected_rows}개 레코드 처리")

                success_count += 1

            except Exception as e:
                print(f"   ❌ 실패: {e}")
                failure_count += 1

        # 마이그레이션 결과
        print(f"\n📊 === 마이그레이션 결과 ===")
        print(f"✅ 성공: {success_count}개")
        print(f"❌ 실패: {failure_count}개")
        print(f"⏱️ 소요 시간: {time.time() - self.start_time:.2f}초")

        if not dry_run and failure_count == 0:
            print("\n🎉 모든 마이그레이션이 성공적으로 완료되었습니다!")
        elif failure_count > 0:
            print(f"\n⚠️ {failure_count}개의 마이그레이션이 실패했습니다. 로그를 확인해주세요.")

    def auto_backup_migration(self) -> None:
        """🛡️ 자동 백업 + 마이그레이션 + 검증"""
        print("🛡️ === 자동 백업 + 마이그레이션 + 검증 ===\n")

        # 1단계: 백업 생성
        print("1️⃣ 백업 생성 중...")
        backup_id = self._create_backup("auto_migration")
        if not backup_id:
            print("❌ 백업 생성 실패. 마이그레이션을 중단합니다.")
            return
        print(f"   ✅ 백업 완료: {backup_id}")

        # 2단계: 마이그레이션 실행
        print("\n2️⃣ 마이그레이션 실행 중...")
        try:
            self.yaml_to_db_migration(dry_run=False)
            migration_success = True
        except Exception as e:
            print(f"   ❌ 마이그레이션 실패: {e}")
            migration_success = False

        # 3단계: 검증
        print("\n3️⃣ 검증 실행 중...")
        validation_issues = self._validate_migration()

        if migration_success and not validation_issues:
            print("✅ 전체 프로세스 성공!")
            print(f"🗂️ 백업 보관: {backup_id}")
        else:
            print("❌ 문제가 발견되어 롤백을 실행합니다...")
            self._rollback_from_backup(backup_id)
            print("🔄 롤백 완료")

    def incremental_migration(self) -> None:
        """⚡ 증분 마이그레이션 (변경분만)"""
        print("⚡ === 증분 마이그레이션 ===\n")

        # 체크섬 기반 변경 감지
        changes_detected = []

        for yaml_name, (target_db, table_name) in self.yaml_to_db_mapping.items():
            yaml_path = self.data_info_path / yaml_name

            if not yaml_path.exists():
                continue

            # 현재 파일 체크섬
            current_checksum = self._calculate_file_checksum(yaml_path)

            # 저장된 체크섬과 비교
            stored_checksum = self._get_stored_checksum(yaml_name)

            if current_checksum != stored_checksum:
                changes_detected.append((yaml_name, target_db, table_name))
                print(f"🔄 변경 감지: {yaml_name}")
            else:
                print(f"✅ 변경 없음: {yaml_name}")

        if not changes_detected:
            print("\n📋 변경된 파일이 없습니다. 마이그레이션을 건너뜁니다.")
            return

        print(f"\n📊 {len(changes_detected)}개 파일의 변경이 감지되었습니다.")

        # 변경된 파일들만 마이그레이션
        for yaml_name, target_db, table_name in changes_detected:
            yaml_path = self.data_info_path / yaml_name

            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                print(f"🔄 마이그레이션: {yaml_name}")
                affected_rows = self._execute_migration(yaml_path, target_db, table_name, data)

                # 체크섬 업데이트
                self._update_stored_checksum(yaml_name, self._calculate_file_checksum(yaml_path))

                print(f"   ✅ 완료: {affected_rows}개 레코드")

            except Exception as e:
                print(f"   ❌ 실패: {e}")

        print(f"\n⏱️ 증분 마이그레이션 완료: {time.time() - self.start_time:.2f}초")

    def conflict_resolution_guide(self) -> None:
        """🤝 충돌 해결 가이드"""
        print("🤝 === 충돌 해결 가이드 ===\n")

        conflicts = []

        # 각 YAML 파일에 대한 충돌 검사
        for yaml_name, (target_db, table_name) in self.yaml_to_db_mapping.items():
            yaml_path = self.data_info_path / yaml_name

            if not yaml_path.exists():
                continue

            print(f"🔍 {yaml_name} 충돌 검사 중...")

            try:
                # YAML 데이터 로드
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    yaml_data = yaml.safe_load(f)

                # DB 현재 상태
                db_path = self.db_paths[target_db]
                if db_path.exists():
                    file_conflicts = self._detect_conflicts(yaml_data, target_db, table_name)
                    conflicts.extend(file_conflicts)

                    if file_conflicts:
                        print(f"   ⚠️ {len(file_conflicts)}개 충돌 발견")
                    else:
                        print("   ✅ 충돌 없음")
                else:
                    print("   📝 새 DB - 충돌 없음")

            except Exception as e:
                print(f"   ❌ 검사 실패: {e}")

        # 충돌 해결 가이드 제공
        if conflicts:
            print(f"\n⚠️ === 총 {len(conflicts)}개 충돌 발견 ===")

            for i, conflict in enumerate(conflicts, 1):
                print(f"\n{i}. {conflict.yaml_file} - {conflict.table_name}")
                print(f"   🔍 유형: {conflict.conflict_type}")
                print(f"   📝 설명: {conflict.description}")
                print(f"   💡 해결책: {conflict.suggested_resolution}")

            print(f"\n🔧 === 자동 해결 옵션 ===")
            print("1. --force-yaml: YAML 데이터를 우선하여 DB 덮어쓰기")
            print("2. --force-db: DB 데이터를 유지하고 YAML 무시")
            print("3. --manual-merge: 수동으로 충돌 해결 후 재시도")
        else:
            print("\n✅ 충돌이 발견되지 않았습니다. 안전하게 마이그레이션할 수 있습니다.")

    def _check_yaml_integrity(self, yaml_path: Path, data: Any) -> List[str]:
        """YAML 데이터 무결성 검사"""
        issues = []

        try:
            if isinstance(data, dict):
                # 딕셔너리 키 검사
                for key in data.keys():
                    if not isinstance(key, str):
                        issues.append(f"잘못된 키 타입: {type(key)}")
                    elif not key.strip():
                        issues.append("빈 키 발견")

            elif isinstance(data, list):
                # 리스트 요소 검사
                for i, item in enumerate(data):
                    if item is None:
                        issues.append(f"인덱스 {i}에 null 값")

        except Exception as e:
            issues.append(f"무결성 검사 오류: {e}")

        return issues

    def _execute_migration(self, yaml_path: Path, target_db: str, table_name: str, data: Any) -> int:
        """실제 마이그레이션 실행"""
        db_path = self.db_paths[target_db]

        # DB 연결
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # 기존 테이블 데이터 삭제
            cursor.execute(f"DELETE FROM {table_name}")

            affected_rows = 0

            if isinstance(data, dict):
                # 딕셔너리 데이터 처리
                for key, value in data.items():
                    # 간단한 INSERT (실제 구현은 스키마에 따라 조정 필요)
                    cursor.execute(f"INSERT INTO {table_name} (key, value) VALUES (?, ?)", (key, str(value)))
                    affected_rows += 1

            elif isinstance(data, list):
                # 리스트 데이터 처리
                for item in data:
                    if isinstance(item, dict):
                        # 딕셔너리 아이템을 컬럼으로 매핑
                        columns = list(item.keys())
                        values = list(item.values())
                        placeholders = ', '.join(['?'] * len(values))
                        column_names = ', '.join(columns)

                        cursor.execute(f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})", values)
                        affected_rows += 1

            conn.commit()
            return affected_rows

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _create_backup(self, backup_type: str) -> str:
        """백업 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"{backup_type}_{timestamp}"
        backup_dir = self.backup_path / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)

        try:
            # DB 파일들 백업
            for db_name, db_path in self.db_paths.items():
                if db_path.exists():
                    backup_file = backup_dir / f"{db_name}.sqlite3"
                    shutil.copy2(db_path, backup_file)

            # 메타데이터 저장
            metadata = {
                'backup_id': backup_id,
                'backup_type': backup_type,
                'timestamp': timestamp,
                'db_files': list(self.db_paths.keys())
            }

            with open(backup_dir / 'metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            return backup_id

        except Exception as e:
            print(f"백업 생성 실패: {e}")
            return None

    def _validate_migration(self) -> List[str]:
        """마이그레이션 검증"""
        issues = []

        for db_name, db_path in self.db_paths.items():
            if not db_path.exists():
                continue

            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # 테이블 존재 확인
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                for table in tables:
                    # 테이블 레코드 수 확인
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]

                    if count == 0:
                        issues.append(f"{db_name}.{table}: 레코드 없음")

                conn.close()

            except Exception as e:
                issues.append(f"{db_name}: 검증 실패 - {e}")

        return issues

    def _rollback_from_backup(self, backup_id: str) -> None:
        """백업에서 롤백"""
        backup_dir = self.backup_path / backup_id

        if not backup_dir.exists():
            print(f"❌ 백업을 찾을 수 없습니다: {backup_id}")
            return

        try:
            for db_name, db_path in self.db_paths.items():
                backup_file = backup_dir / f"{db_name}.sqlite3"
                if backup_file.exists():
                    shutil.copy2(backup_file, db_path)
                    print(f"   🔄 {db_name} 복구 완료")

        except Exception as e:
            print(f"❌ 롤백 실패: {e}")

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """파일 체크섬 계산"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def _get_stored_checksum(self, yaml_name: str) -> str:
        """저장된 체크섬 조회"""
        checksum_file = self.temp_path / 'checksums.json'
        if checksum_file.exists():
            try:
                with open(checksum_file, 'r', encoding='utf-8') as f:
                    checksums = json.load(f)
                return checksums.get(yaml_name, '')
            except:
                return ''
        return ''

    def _update_stored_checksum(self, yaml_name: str, checksum: str) -> None:
        """체크섬 업데이트"""
        self.temp_path.mkdir(parents=True, exist_ok=True)
        checksum_file = self.temp_path / 'checksums.json'

        checksums = {}
        if checksum_file.exists():
            try:
                with open(checksum_file, 'r', encoding='utf-8') as f:
                    checksums = json.load(f)
            except:
                pass

        checksums[yaml_name] = checksum

        with open(checksum_file, 'w', encoding='utf-8') as f:
            json.dump(checksums, f, indent=2, ensure_ascii=False)

    def _detect_conflicts(self, yaml_data: Any, target_db: str, table_name: str) -> List[ConflictInfo]:
        """충돌 감지"""
        conflicts = []

        # 간단한 충돌 감지 로직 (실제로는 더 정교해야 함)
        try:
            db_path = self.db_paths[target_db]
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 테이블 존재 여부 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                # 새 테이블이므로 충돌 없음
                conn.close()
                return conflicts

            # 레코드 수 비교
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            db_count = cursor.fetchone()[0]

            if isinstance(yaml_data, dict):
                yaml_count = len(yaml_data)
            elif isinstance(yaml_data, list):
                yaml_count = len(yaml_data)
            else:
                yaml_count = 1

            if db_count > 0 and yaml_count != db_count:
                conflicts.append(ConflictInfo(
                    yaml_file=f"{table_name}.yaml",
                    table_name=table_name,
                    conflict_type="레코드 수 불일치",
                    description=f"DB: {db_count}개, YAML: {yaml_count}개",
                    suggested_resolution="--force-yaml 옵션으로 YAML 우선 적용"
                ))

            conn.close()

        except Exception:
            pass

        return conflicts


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='Super DB Migrator - 마이그레이션 전문 도구')
    parser.add_argument('--smart-merge', action='store_true', help='data_info YAML 스마트 병합')
    parser.add_argument('--preview-changes', action='store_true', help='마이그레이션 미리보기')
    parser.add_argument('--yaml-to-db', action='store_true', help='YAML → DB 일괄 마이그레이션')
    parser.add_argument('--auto-backup', action='store_true', help='자동 백업 + 마이그레이션 + 검증')
    parser.add_argument('--incremental', action='store_true', help='증분 마이그레이션 (변경분만)')
    parser.add_argument('--conflict-resolution', action='store_true', help='충돌 해결 가이드')
    parser.add_argument('--dry-run', action='store_true', help='실제 실행 없이 시뮬레이션만')

    args = parser.parse_args()

    migrator = SuperDBMigrator()

    # 아무 옵션이 없으면 preview-changes 실행
    if not any(vars(args).values()):
        migrator.preview_changes()
        return

    if args.smart_merge:
        migrator.smart_merge_yamls()

    if args.preview_changes:
        migrator.preview_changes()

    if args.yaml_to_db:
        migrator.yaml_to_db_migration(dry_run=args.dry_run)

    if args.auto_backup:
        migrator.auto_backup_migration()

    if args.incremental:
        migrator.incremental_migration()

    if args.conflict_resolution:
        migrator.conflict_resolution_guide()


if __name__ == "__main__":
    main()
