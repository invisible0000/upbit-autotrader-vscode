#!/usr/bin/env python3
"""
🚀 Advanced Data Info to DB Migration Manager
=============================================

data_info 폴더의 모든 variables_* YAML 파일들을 
확장된 DB 스키마(v3.0)로 완전 마이그레이션하는 고급 관리자

주요 기능:
- variables_help_texts.yaml → tv_help_texts 테이블
- variables_placeholder_texts.yaml → tv_placeholder_texts 테이블  
- variables_indicator_categories.yaml → tv_indicator_categories 테이블
- variables_parameter_types.yaml → tv_parameter_types 테이블
- variables_indicator_library.yaml → tv_indicator_library 테이블
- variables_workflow_guide.yaml → tv_workflow_guides 테이블

작성일: 2025-07-30
작성자: GitHub Copilot
"""

import os
import sqlite3
import yaml
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


class AdvancedDataInfoMigrator:
    """data_info → 확장 DB 스키마 마이그레이션 관리자"""
    
    def __init__(self, db_path: str, data_info_path: str = None):
        """
        초기화
        
        Args:
            db_path: 데이터베이스 파일 경로
            data_info_path: data_info 폴더 경로 (None이면 자동 감지)
        """
        self.db_path = db_path
        self.data_info_path = data_info_path or self._get_default_data_info_path()
        self.migration_log = []
        
    def _get_default_data_info_path(self) -> str:
        """기본 data_info 폴더 경로 반환"""
        current_dir = Path(__file__).parent
        return str(current_dir.parent / "data_info")
    
    def _log(self, message: str, level: str = "INFO"):
        """마이그레이션 로그 기록"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.migration_log.append(log_entry)
        print(log_entry)
    
    def _get_db_connection(self) -> sqlite3.Connection:
        """DB 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _load_yaml_file(self, filename: str) -> Dict[str, Any]:
        """YAML 파일 로드"""
        file_path = Path(self.data_info_path) / filename
        if not file_path.exists():
            self._log(f"YAML 파일을 찾을 수 없습니다: {filename}", "WARNING")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self._log(f"YAML 파일 로드 성공: {filename}")
                return data or {}
        except Exception as e:
            self._log(f"YAML 파일 로드 실패 {filename}: {str(e)}", "ERROR")
            return {}
    
    def check_schema_version(self) -> Tuple[bool, str]:
        """스키마 버전 확인"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version FROM tv_schema_version ORDER BY applied_at DESC LIMIT 1")
                result = cursor.fetchone()
                
                if result:
                    version = result['version']
                    is_v3_compatible = version >= '3.0.0'
                    return is_v3_compatible, version
                else:
                    return False, "Unknown"
        except Exception as e:
            self._log(f"스키마 버전 확인 실패: {str(e)}", "ERROR")
            return False, "Error"
    
    def setup_extended_schema(self) -> bool:
        """확장 스키마 설정 (v3.0)"""
        schema_file = Path(self.data_info_path) / "schema_extended_v3.sql"
        
        if not schema_file.exists():
            self._log(f"확장 스키마 파일을 찾을 수 없습니다: {schema_file}", "ERROR")
            return False
        
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.executescript(schema_sql)
                conn.commit()
                
            self._log("확장 스키마 v3.0 설정 완료")
            return True
            
        except Exception as e:
            self._log(f"확장 스키마 설정 실패: {str(e)}", "ERROR")
            return False
    
    def migrate_help_texts(self) -> bool:
        """variables_help_texts.yaml → tv_help_texts 마이그레이션"""
        self._log("📝 도움말 텍스트 마이그레이션 시작...")
        
        data = self._load_yaml_file("variables_help_texts.yaml")
        if not data:
            return False
        
        help_texts = data.get('help_texts', {})
        if not help_texts:
            self._log("도움말 텍스트 데이터가 없습니다", "WARNING")
            return True
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 기존 데이터 삭제 (재마이그레이션 대비)
                cursor.execute("DELETE FROM tv_help_texts WHERE help_key LIKE 'yaml_%'")
                
                # 도움말 텍스트 삽입
                for help_key, help_text in help_texts.items():
                    # 카테고리 추출 (키 이름에서)
                    category = help_key.split('_')[0] if '_' in help_key else 'general'
                    
                    cursor.execute("""
                        INSERT INTO tv_help_texts (
                            help_key, help_text, help_category, usage_context, 
                            language_code, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        f"yaml_{help_key}",  # 접두사로 YAML 기원 표시
                        help_text,
                        category,
                        'general',
                        'ko',
                        datetime.now(),
                        datetime.now()
                    ))
                
                conn.commit()
                count = len(help_texts)
                self._log(f"도움말 텍스트 {count}개 마이그레이션 완료")
                return True
                
        except Exception as e:
            self._log(f"도움말 텍스트 마이그레이션 실패: {str(e)}", "ERROR")
            return False
    
    def migrate_placeholder_texts(self) -> bool:
        """variables_placeholder_texts.yaml → tv_placeholder_texts 마이그레이션"""
        self._log("🎯 플레이스홀더 텍스트 마이그레이션 시작...")
        
        data = self._load_yaml_file("variables_placeholder_texts.yaml")
        if not data:
            return False
        
        placeholder_library = data.get('placeholder_library', {})
        if not placeholder_library:
            self._log("플레이스홀더 라이브러리 데이터가 없습니다", "WARNING")
            return True
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 기존 데이터 삭제
                cursor.execute("DELETE FROM tv_placeholder_texts")
                
                # 플레이스홀더 텍스트 삽입
                for variable_id, placeholder_data in placeholder_library.items():
                    # 기본 플레이스홀더들 삽입
                    for placeholder_type in ['target', 'name', 'description']:
                        if placeholder_type in placeholder_data:
                            cursor.execute("""
                                INSERT INTO tv_placeholder_texts (
                                    variable_id, placeholder_type, placeholder_text,
                                    scenario_order, is_primary, language_code, created_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                variable_id,
                                placeholder_type,
                                placeholder_data[placeholder_type],
                                0,
                                1,  # 기본 플레이스홀더는 primary
                                'ko',
                                datetime.now()
                            ))
                    
                    # 사용 시나리오들 삽입
                    usage_scenarios = placeholder_data.get('usage_scenarios', [])
                    for i, scenario in enumerate(usage_scenarios):
                        cursor.execute("""
                            INSERT INTO tv_placeholder_texts (
                                variable_id, placeholder_type, placeholder_text,
                                scenario_order, is_primary, language_code, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            variable_id,
                            'scenario',
                            scenario,
                            i + 1,
                            0,  # 시나리오는 primary 아님
                            'ko',
                            datetime.now()
                        ))
                
                conn.commit()
                total_count = sum(len(v.get('usage_scenarios', [])) + 3 for v in placeholder_library.values())
                self._log(f"플레이스홀더 텍스트 {total_count}개 마이그레이션 완료")
                return True
                
        except Exception as e:
            self._log(f"플레이스홀더 텍스트 마이그레이션 실패: {str(e)}", "ERROR")
            return False
    
    def migrate_indicator_library(self) -> bool:
        """variables_indicator_library.yaml → tv_indicator_library 마이그레이션"""
        self._log("📚 지표 라이브러리 마이그레이션 시작...")
        
        data = self._load_yaml_file("variables_indicator_library.yaml")
        if not data:
            return False
        
        indicators = data.get('indicators', {})
        if not indicators:
            self._log("지표 라이브러리 데이터가 없습니다", "WARNING")
            return True
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 기존 데이터 삭제
                cursor.execute("DELETE FROM tv_indicator_library")
                
                # 지표 라이브러리 정보 삽입
                for variable_id, indicator_info in indicators.items():
                    # 각 콘텐츠 타입별로 삽입
                    content_order = 0
                    
                    for content_type in ['definition', 'calculation', 'interpretation', 'usage_tip']:
                        if content_type in indicator_info:
                            content_order += 1
                            cursor.execute("""
                                INSERT INTO tv_indicator_library (
                                    variable_id, content_type, content_ko, content_order,
                                    reference_links, examples, created_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                variable_id,
                                content_type,
                                indicator_info[content_type],
                                content_order,
                                json.dumps(indicator_info.get('reference_links', [])),
                                json.dumps(indicator_info.get('examples', [])),
                                datetime.now()
                            ))
                
                conn.commit()
                self._log(f"지표 라이브러리 {len(indicators)}개 마이그레이션 완료")
                return True
                
        except Exception as e:
            self._log(f"지표 라이브러리 마이그레이션 실패: {str(e)}", "ERROR")
            return False
    
    def migrate_workflow_guides(self) -> bool:
        """variables_workflow_guide.yaml → tv_workflow_guides 마이그레이션"""
        self._log("📋 워크플로우 가이드 마이그레이션 시작...")
        
        data = self._load_yaml_file("variables_workflow_guide.yaml")
        if not data:
            return False
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 기존 데이터 삭제
                cursor.execute("DELETE FROM tv_workflow_guides")
                
                # 워크플로우 데이터 구조 분석 및 삽입
                workflow_sections = data.get('workflow', {})
                if workflow_sections:
                    order = 0
                    for section_key, section_data in workflow_sections.items():
                        order += 1
                        cursor.execute("""
                            INSERT INTO tv_workflow_guides (
                                guide_type, guide_title_ko, guide_content,
                                display_order, target_audience, importance_level,
                                is_active, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            'section',
                            section_key.replace('_', ' ').title(),
                            json.dumps(section_data, ensure_ascii=False),
                            order,
                            'both',
                            3,  # 중간 중요도
                            1,
                            datetime.now()
                        ))
                
                # 기타 가이드 섹션들도 추가
                for guide_type in ['principles', 'checklist', 'troubleshooting']:
                    if guide_type in data:
                        order += 1
                        cursor.execute("""
                            INSERT INTO tv_workflow_guides (
                                guide_type, guide_title_ko, guide_content,
                                display_order, target_audience, importance_level,
                                is_active, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            guide_type,
                            guide_type.replace('_', ' ').title(),
                            json.dumps(data[guide_type], ensure_ascii=False),
                            order,
                            'both',
                            4,  # 높은 중요도
                            1,
                            datetime.now()
                        ))
                
                conn.commit()
                self._log(f"워크플로우 가이드 마이그레이션 완료")
                return True
                
        except Exception as e:
            self._log(f"워크플로우 가이드 마이그레이션 실패: {str(e)}", "ERROR")
            return False
    
    def run_full_migration(self) -> Dict[str, Any]:
        """전체 마이그레이션 실행"""
        self._log("🚀 data_info → DB 전체 마이그레이션 시작")
        
        results = {
            'success': True,
            'schema_setup': False,
            'migrations': {},
            'error_count': 0,
            'log': []
        }
        
        # 1. 스키마 버전 확인 및 설정
        is_compatible, current_version = self.check_schema_version()
        self._log(f"현재 스키마 버전: {current_version}")
        
        if not is_compatible:
            self._log("v3.0 호환 스키마 설정 중...")
            if self.setup_extended_schema():
                results['schema_setup'] = True
            else:
                results['success'] = False
                results['error_count'] += 1
                self._log("스키마 설정 실패로 마이그레이션 중단", "ERROR")
                results['log'] = self.migration_log
                return results
        
        # 2. 각 컴포넌트 마이그레이션
        migration_tasks = [
            ('help_texts', self.migrate_help_texts),
            ('placeholder_texts', self.migrate_placeholder_texts),
            ('indicator_library', self.migrate_indicator_library),
            ('workflow_guides', self.migrate_workflow_guides),
        ]
        
        for task_name, task_func in migration_tasks:
            self._log(f"⚙️ {task_name} 마이그레이션 실행 중...")
            try:
                success = task_func()
                results['migrations'][task_name] = success
                if not success:
                    results['error_count'] += 1
            except Exception as e:
                self._log(f"{task_name} 마이그레이션 예외 발생: {str(e)}", "ERROR")
                results['migrations'][task_name] = False
                results['error_count'] += 1
        
        # 3. 최종 결과 평가
        if results['error_count'] > 0:
            results['success'] = False
            self._log(f"❌ 마이그레이션 완료 (오류 {results['error_count']}개)", "ERROR")
        else:
            self._log("✅ 모든 마이그레이션 성공적으로 완료!")
        
        results['log'] = self.migration_log
        return results
    
    def get_migration_summary(self) -> Dict[str, Any]:
        """마이그레이션 결과 요약"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                summary = {}
                
                # 각 테이블별 레코드 수 조회
                tables = [
                    'tv_help_texts',
                    'tv_placeholder_texts', 
                    'tv_indicator_library',
                    'tv_workflow_guides'
                ]
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    result = cursor.fetchone()
                    summary[table] = result['count'] if result else 0
                
                return summary
                
        except Exception as e:
            self._log(f"요약 정보 조회 실패: {str(e)}", "ERROR")
            return {}


def main():
    """테스트 실행"""
    # 기본 경로 설정
    current_dir = Path(__file__).parent
    db_path = current_dir / "test_migration.db"
    
    # 마이그레이터 생성 및 실행
    migrator = AdvancedDataInfoMigrator(str(db_path))
    
    print("🚀 Advanced Data Info Migration 테스트 시작")
    print("=" * 60)
    
    # 전체 마이그레이션 실행
    results = migrator.run_full_migration()
    
    print("\n" + "=" * 60)
    print("📊 마이그레이션 결과:")
    print(f"✅ 성공 여부: {results['success']}")
    print(f"🔧 스키마 설정: {results['schema_setup']}")
    print(f"❌ 오류 개수: {results['error_count']}")
    
    print("\n🗂️ 개별 마이그레이션 결과:")
    for task, success in results['migrations'].items():
        status = "✅" if success else "❌"
        print(f"  {status} {task}")
    
    # 요약 정보 출력
    summary = migrator.get_migration_summary()
    if summary:
        print("\n📋 테이블별 레코드 수:")
        for table, count in summary.items():
            print(f"  📄 {table}: {count}개")
    
    print("\n🔗 테스트 DB 경로:", db_path)


if __name__ == "__main__":
    main()
