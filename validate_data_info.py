#!/usr/bin/env python3
"""
data_info 폴더 전체 검토 및 정리 스크립트
- SQL 스키마 검증
- YAML 파일 검증 및 중복 정리
- 백업 파일 정리
"""

import yaml
import sqlite3
import re
from pathlib import Path
from datetime import datetime
import shutil
import json

class DataInfoValidator:
    def __init__(self):
        self.data_info_path = Path("data_info")
        self.legacy_path = Path("legacy")
        self.report = {
            "sql_schemas": {},
            "yaml_files": {},
            "duplicates": [],
            "issues": [],
            "actions": []
        }

    def run_full_validation(self):
        """전체 검증 프로세스 실행"""
        print("=== DATA_INFO 폴더 전체 검토 시작 ===\n")

        # 1. SQL 스키마 파일 검증
        self.validate_sql_schemas()

        # 2. YAML 파일 검증
        self.validate_yaml_files()

        # 3. 중복 파일 식별
        self.identify_duplicates()

        # 4. 백업 파일 정리
        self.organize_backups()

        # 5. 리포트 생성
        self.generate_report()

        # 6. 정리 작업 실행
        self.execute_cleanup()

    def validate_sql_schemas(self):
        """SQL 스키마 파일들 검증"""
        print("1. SQL 스키마 파일 검증")

        sql_files = list(self.data_info_path.glob("*.sql"))
        expected_schemas = [
            "upbit_autotrading_schema_settings.sql",
            "upbit_autotrading_schema_strategies.sql",
            "upbit_autotrading_schema_market_data.sql"
        ]

        for schema_file in expected_schemas:
            file_path = self.data_info_path / schema_file
            print(f"  검증: {schema_file}")

            if not file_path.exists():
                issue = f"❌ 필수 스키마 파일 누락: {schema_file}"
                print(f"    {issue}")
                self.report["issues"].append(issue)
                continue

            # SQL 파일 내용 검증
            content = file_path.read_text(encoding='utf-8')
            schema_info = self.analyze_sql_schema(content, schema_file)
            self.report["sql_schemas"][schema_file] = schema_info

            print(f"    ✅ 테이블 수: {len(schema_info['tables'])}")
            for table in schema_info['tables']:
                print(f"      - {table}")

    def analyze_sql_schema(self, content, filename):
        """SQL 스키마 내용 분석"""
        # CREATE TABLE 문 찾기
        table_pattern = r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?([^\s(]+)'
        tables = re.findall(table_pattern, content, re.IGNORECASE)

        # 외래키 제약조건 찾기
        fk_pattern = r'FOREIGN KEY.*?REFERENCES\s+([^\s(]+)'
        foreign_keys = re.findall(fk_pattern, content, re.IGNORECASE)

        # 인덱스 찾기
        index_pattern = r'CREATE.*?INDEX.*?ON\s+([^\s(]+)'
        indexes = re.findall(index_pattern, content, re.IGNORECASE)

        return {
            "tables": tables,
            "foreign_keys": foreign_keys,
            "indexes": indexes,
            "line_count": len(content.split('\n')),
            "size_bytes": len(content.encode('utf-8'))
        }

    def validate_yaml_files(self):
        """YAML 파일들 검증"""
        print("\n2. YAML 파일 검증")

        yaml_files = list(self.data_info_path.glob("*.yaml"))

        for yaml_file in yaml_files:
            print(f"  검증: {yaml_file.name}")

            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                yaml_info = self.analyze_yaml_content(data, yaml_file.name)
                self.report["yaml_files"][yaml_file.name] = yaml_info

                print(f"    ✅ 유효한 YAML")
                if yaml_info.get("main_sections"):
                    print(f"    📊 주요 섹션: {len(yaml_info['main_sections'])}")
                    for section in yaml_info["main_sections"][:3]:  # 처음 3개만 표시
                        print(f"      - {section}")

            except yaml.YAMLError as e:
                issue = f"❌ YAML 파싱 오류: {yaml_file.name} - {e}"
                print(f"    {issue}")
                self.report["issues"].append(issue)
            except Exception as e:
                issue = f"❌ 파일 읽기 오류: {yaml_file.name} - {e}"
                print(f"    {issue}")
                self.report["issues"].append(issue)

    def analyze_yaml_content(self, data, filename):
        """YAML 내용 분석"""
        info = {
            "valid": True,
            "main_sections": [],
            "record_count": 0,
            "has_backups_header": False
        }

        if isinstance(data, dict):
            info["main_sections"] = list(data.keys())

            # 레코드 수 계산
            for key, value in data.items():
                if isinstance(value, dict):
                    info["record_count"] += len(value)

            # 백업 헤더 확인 (편집 세션 정보 등)
            content_str = str(data)
            if any(keyword in content_str for keyword in ["편집 세션", "백업", "EDIT_", "session_"]):
                info["has_backups_header"] = True

        return info

    def identify_duplicates(self):
        """중복 파일 식별"""
        print("\n3. 중복 파일 식별")

        # 파일명 패턴 분석
        base_files = {}
        backup_files = []

        for file_path in self.data_info_path.glob("*.yaml"):
            filename = file_path.name

            # 백업 파일 패턴 식별
            if any(pattern in filename for pattern in ["backup", "BACKUP", "EDIT_", "ORIGINAL_"]):
                backup_files.append(filename)
                continue

            # 베이스 파일명 추출
            base_name = filename
            if base_name not in base_files:
                base_files[base_name] = []
            base_files[base_name].append(filename)

        # 중복 찾기
        for base_name, files in base_files.items():
            if len(files) > 1:
                self.report["duplicates"].append({
                    "base_name": base_name,
                    "files": files
                })

        print(f"  📁 베이스 파일: {len(base_files)}")
        print(f"  📄 백업 파일: {len(backup_files)}")
        print(f"  🔄 중복 그룹: {len(self.report['duplicates'])}")

        for backup in backup_files:
            print(f"    백업: {backup}")

    def organize_backups(self):
        """백업 파일 정리"""
        print("\n4. 백업 파일 정리 계획")

        # legacy 폴더 생성
        if not self.legacy_path.exists():
            self.legacy_path.mkdir()
            self.report["actions"].append("legacy 폴더 생성")

        # 백업 파일들 이동 계획
        backup_patterns = ["backup", "BACKUP", "EDIT_", "ORIGINAL_"]

        for file_path in self.data_info_path.glob("*.yaml"):
            filename = file_path.name

            if any(pattern in filename for pattern in backup_patterns):
                target_path = self.legacy_path / filename
                self.report["actions"].append(f"이동: {filename} → legacy/{filename}")
                print(f"  📦 이동 예정: {filename}")

        # _BACKUPS_ 폴더도 legacy로 이동 계획
        backups_dir = self.data_info_path / "_BACKUPS_"
        if backups_dir.exists():
            target_dir = self.legacy_path / "data_info_BACKUPS"
            self.report["actions"].append(f"이동: _BACKUPS_ → legacy/data_info_BACKUPS")
            print(f"  📦 이동 예정: _BACKUPS_ 폴더")

    def generate_report(self):
        """검증 리포트 생성"""
        print("\n5. 검증 리포트 생성")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"data_info_validation_report_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)

        print(f"  📄 리포트 저장: {report_file}")

        # 요약 출력
        print("\n=== 검증 요약 ===")
        print(f"SQL 스키마 파일: {len(self.report['sql_schemas'])}")
        print(f"YAML 파일: {len(self.report['yaml_files'])}")
        print(f"발견된 문제: {len(self.report['issues'])}")
        print(f"정리 작업 항목: {len(self.report['actions'])}")

        if self.report['issues']:
            print("\n⚠️  발견된 문제들:")
            for issue in self.report['issues']:
                print(f"  - {issue}")

    def execute_cleanup(self):
        """정리 작업 실행"""
        print("\n6. 정리 작업 실행")

        response = input("정리 작업을 실행하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            print("정리 작업을 건너뜁니다.")
            return

        try:
            # 백업 파일들 이동
            backup_patterns = ["backup", "BACKUP", "EDIT_", "ORIGINAL_"]

            for file_path in self.data_info_path.glob("*.yaml"):
                filename = file_path.name

                if any(pattern in filename for pattern in backup_patterns):
                    target_path = self.legacy_path / filename
                    shutil.move(str(file_path), str(target_path))
                    print(f"  ✅ 이동 완료: {filename}")

            # _BACKUPS_ 폴더 이동
            backups_dir = self.data_info_path / "_BACKUPS_"
            if backups_dir.exists():
                target_dir = self.legacy_path / "data_info_BACKUPS"
                shutil.move(str(backups_dir), str(target_dir))
                print(f"  ✅ 폴더 이동 완료: _BACKUPS_")

            # _MERGED_ 폴더가 비어있으면 제거
            merged_dir = self.data_info_path / "_MERGED_"
            if merged_dir.exists() and not any(merged_dir.iterdir()):
                merged_dir.rmdir()
                print(f"  ✅ 빈 폴더 제거: _MERGED_")

            print("\n✅ 모든 정리 작업이 완료되었습니다!")

        except Exception as e:
            print(f"❌ 정리 작업 중 오류 발생: {e}")

if __name__ == "__main__":
    validator = DataInfoValidator()
    validator.run_full_validation()
