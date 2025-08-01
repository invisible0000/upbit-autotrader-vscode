#!/usr/bin/env python3
"""
🔄 Super DB Schema Validator
DB 스키마 정합성 검증 및 구조 무결성 확인 도구

🤖 LLM 사용 가이드:
===================
이 도구는 DB 스키마의 정합성을 검증하고 구조/인스턴스 분리 원칙 준수를 확인합니다.

📋 주요 명령어 (tools 폴더에서 실행):
1. python super_db_schema_validator.py --check naming --all-dbs
2. python super_db_schema_validator.py --check separation --settings settings.sqlite3 --strategies strategies.sqlite3
3. python super_db_schema_validator.py --db settings.sqlite3 --rules structure
4. python super_db_schema_validator.py --validate migration-completeness

🎯 언제 사용하면 좋은가:
- 마이그레이션 후 스키마 정합성 확인
- 구조/인스턴스 분리 원칙 준수 검증
- 네이밍 규칙 일관성 검사
- 관계 무결성 및 제약 조건 확인

💡 출력 해석:
- 🟢 통과: 모든 검증 규칙 만족
- 🟡 경고: 권장사항 위반 (기능상 문제없음)
- 🔴 실패: 필수 규칙 위반 (수정 필요)
- 📊 점수: 0-100점 스키마 품질 평가

기능:
1. 네이밍 규칙 준수 검증
2. 구조/인스턴스 분리 원칙 확인
3. 관계 무결성 검증
4. 마이그레이션 완성도 확인

작성일: 2025-08-01
작성자: Upbit Auto Trading Team
"""
import sqlite3
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

# 프로젝트 루트를 파이썬 패스에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/super_db_schema_validator.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """검증 결과 데이터 클래스"""
    category: str
    rule_name: str
    status: str  # 'pass', 'warning', 'fail'
    score: float  # 0-100점
    message: str
    details: List[str]
    recommendations: List[str]


@dataclass
class SchemaValidationReport:
    """스키마 검증 종합 보고서"""
    db_name: str
    validation_time: str
    overall_score: float
    results: List[ValidationResult]
    summary: Dict[str, int]
    critical_issues: List[str]
    recommendations: List[str]


class SuperDBSchemaValidator:
    """
    🔄 Super DB Schema Validator - 스키마 정합성 검증 도구
    
    🤖 LLM 사용 패턴:
    validator = SuperDBSchemaValidator()
    validator.validate_naming_conventions("settings")
    validator.check_structure_instance_separation("settings", "strategies")
    validator.generate_full_validation_report("settings")
    
    💡 핵심 기능: 구조 검증 + 무결성 확인 + 품질 평가
    """
    
    def __init__(self):
        """초기화 - 경로 및 검증 규칙 설정"""
        self.project_root = PROJECT_ROOT
        self.db_path = self.project_root / "upbit_auto_trading" / "data"
        
        # 로그 디렉토리 생성
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 검증 대상 DB 설정
        self.monitored_dbs = {
            'settings': self.db_path / 'settings.sqlite3',
            'strategies': self.db_path / 'strategies.sqlite3',
            'market_data': self.db_path / 'market_data.sqlite3'
        }
        
        # 네이밍 규칙 정의
        self.naming_rules = {
            'settings': {
                'required_prefixes': ['tv_', 'cfg_', 'sys_', 'app_'],
                'prohibited_prefixes': ['user_', 'execution_', 'temp_'],
                'allowed_suffixes': ['_structure', '_template', '_category', '_type', '_library'],
                'table_categories': {
                    'trading_variables': ['tv_trading_variables', 'tv_variable_parameters', 'tv_help_texts'],
                    'configuration': ['cfg_app_settings', 'cfg_system_settings'],
                    'system': ['sys_metadata', 'sys_version_info']
                }
            },
            'strategies': {
                'required_prefixes': ['user_', 'execution_', 'strategy_'],
                'prohibited_prefixes': ['tv_', 'cfg_', 'sys_'],
                'allowed_suffixes': ['_history', '_log', '_backup'],
                'table_categories': {
                    'user_data': ['user_triggers', 'user_strategies', 'user_portfolios'],
                    'execution': ['execution_history', 'execution_logs'],
                    'strategy': ['strategy_results', 'strategy_performance']
                }
            },
            'market_data': {
                'required_prefixes': ['market_', 'ticker_', 'candle_', 'order_'],
                'prohibited_prefixes': ['tv_', 'user_', 'cfg_'],
                'allowed_suffixes': ['_data', '_history', '_cache'],
                'table_categories': {
                    'market': ['market_tickers', 'market_status'],
                    'price_data': ['candle_1m', 'candle_5m', 'candle_1h'],
                    'order_data': ['order_book', 'order_history']
                }
            }
        }
        
        # 관계 무결성 규칙
        self.relationship_rules = {
            'foreign_keys': {
                'tv_variable_parameters.variable_id': 'tv_trading_variables.variable_id',
                'user_strategies.trigger_ids': 'user_triggers.id',
                'execution_history.strategy_id': 'user_strategies.id'
            },
            'required_indexes': {
                'settings': ['tv_trading_variables.variable_id', 'tv_variable_parameters.variable_id'],
                'strategies': ['user_triggers.id', 'user_strategies.id'],
                'market_data': ['market_tickers.symbol']
            }
        }
        
        logger.info("🔄 Super DB Schema Validator 초기화")
        logger.info(f"📂 DB Path: {self.db_path}")
        logger.info(f"🗄️ 검증 대상: {list(self.monitored_dbs.keys())}")
    
    def get_db_connection(self, db_name: str) -> Optional[sqlite3.Connection]:
        """안전한 DB 연결 생성"""
        db_file = self.monitored_dbs.get(db_name)
        
        if not db_file or not db_file.exists():
            logger.warning(f"⚠️ DB 파일 없음: {db_name} ({db_file})")
            return None
        
        try:
            conn = sqlite3.connect(db_file)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"❌ DB 연결 실패: {db_name} - {e}")
            return None
    
    def get_table_list(self, db_name: str) -> List[str]:
        """DB의 모든 테이블 목록 조회"""
        conn = self.get_db_connection(db_name)
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return tables
        except sqlite3.Error as e:
            logger.error(f"❌ 테이블 목록 조회 실패 ({db_name}): {e}")
            conn.close()
            return []
    
    def get_table_schema(self, db_name: str, table_name: str) -> Dict:
        """테이블 스키마 정보 조회"""
        conn = self.get_db_connection(db_name)
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # 테이블 구조 정보
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # 인덱스 정보
            cursor.execute(f"PRAGMA index_list({table_name})")
            indexes = cursor.fetchall()
            
            # Foreign Key 정보
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = cursor.fetchall()
            
            schema_info = {
                'columns': [dict(col) for col in columns],
                'indexes': [dict(idx) for idx in indexes],
                'foreign_keys': [dict(fk) for fk in foreign_keys],
                'column_count': len(columns),
                'index_count': len(indexes),
                'fk_count': len(foreign_keys)
            }
            
            conn.close()
            return schema_info
            
        except sqlite3.Error as e:
            logger.error(f"❌ 테이블 스키마 조회 실패 ({db_name}.{table_name}): {e}")
            conn.close()
            return {}
    
    def validate_naming_conventions(self, db_name: str) -> ValidationResult:
        """네이밍 규칙 준수 검증"""
        tables = self.get_table_list(db_name)
        rules = self.naming_rules.get(db_name, {})
        
        if not rules:
            return ValidationResult(
                category="naming",
                rule_name="naming_conventions",
                status="warning",
                score=50.0,
                message=f"DB '{db_name}'에 대한 네이밍 규칙이 정의되지 않음",
                details=[],
                recommendations=["네이밍 규칙 정의 필요"]
            )
        
        issues = []
        warnings = []
        compliant_tables = 0
        
        required_prefixes = rules.get('required_prefixes', [])
        prohibited_prefixes = rules.get('prohibited_prefixes', [])
        
        for table in tables:
            # 시스템 테이블 제외
            if table.startswith('sqlite_'):
                continue
            
            # 필수 접두사 확인
            has_required_prefix = any(table.startswith(prefix) for prefix in required_prefixes)
            if not has_required_prefix and required_prefixes:
                issues.append(f"테이블 '{table}': 필수 접두사 없음 ({', '.join(required_prefixes)})")
                continue
            
            # 금지된 접두사 확인
            has_prohibited_prefix = any(table.startswith(prefix) for prefix in prohibited_prefixes)
            if has_prohibited_prefix:
                issues.append(f"테이블 '{table}': 금지된 접두사 사용 ({', '.join(prohibited_prefixes)})")
                continue
            
            compliant_tables += 1
        
        # 점수 계산
        total_user_tables = len([t for t in tables if not t.startswith('sqlite_')])
        if total_user_tables == 0:
            score = 100.0
        else:
            score = (compliant_tables / total_user_tables) * 100
        
        # 상태 결정
        if score >= 90:
            status = "pass"
        elif score >= 70:
            status = "warning"
        else:
            status = "fail"
        
        recommendations = []
        if issues:
            recommendations.extend([
                "테이블명 변경 또는 마이그레이션 필요",
                f"권장 접두사: {', '.join(required_prefixes)}"
            ])
        
        return ValidationResult(
            category="naming",
            rule_name="naming_conventions",
            status=status,
            score=score,
            message=f"네이밍 규칙 준수율: {score:.1f}% ({compliant_tables}/{total_user_tables})",
            details=issues + warnings,
            recommendations=recommendations
        )
    
    def check_structure_instance_separation(self, settings_db: str, strategies_db: str) -> ValidationResult:
        """구조/인스턴스 분리 원칙 확인"""
        settings_tables = self.get_table_list(settings_db)
        strategies_tables = self.get_table_list(strategies_db)
        
        issues = []
        violations = 0
        
        # settings DB에 사용자 데이터 테이블이 있는지 확인
        user_data_prefixes = ['user_', 'execution_', 'strategy_instance_']
        for table in settings_tables:
            if any(table.startswith(prefix) for prefix in user_data_prefixes):
                issues.append(f"settings DB에 사용자 데이터 테이블: {table}")
                violations += 1
        
        # strategies DB에 구조 정의 테이블이 있는지 확인
        structure_prefixes = ['tv_', 'cfg_', 'sys_']
        for table in strategies_tables:
            if any(table.startswith(prefix) for prefix in structure_prefixes):
                issues.append(f"strategies DB에 구조 정의 테이블: {table}")
                violations += 1
        
        # 점수 계산
        total_checks = len(settings_tables) + len(strategies_tables)
        if total_checks == 0:
            score = 100.0
        else:
            score = max(0, (total_checks - violations) / total_checks * 100)
        
        # 상태 결정
        if violations == 0:
            status = "pass"
        elif violations <= 2:
            status = "warning"
        else:
            status = "fail"
        
        recommendations = []
        if violations > 0:
            recommendations.extend([
                "테이블을 적절한 DB로 이동",
                "super_db_structure_generator.py로 구조 재생성 검토"
            ])
        
        return ValidationResult(
            category="separation",
            rule_name="structure_instance_separation",
            status=status,
            score=score,
            message=f"분리 원칙 준수: {violations}개 위반 발견",
            details=issues,
            recommendations=recommendations
        )
    
    def verify_relationship_integrity(self, db_name: str) -> ValidationResult:
        """관계 무결성 검증"""
        tables = self.get_table_list(db_name)
        issues = []
        integrity_score = 100.0
        
        # 각 테이블의 Foreign Key 검증
        for table in tables:
            if table.startswith('sqlite_'):
                continue
            
            schema = self.get_table_schema(db_name, table)
            foreign_keys = schema.get('foreign_keys', [])
            
            for fk in foreign_keys:
                # FK 참조 무결성 확인 (실제 데이터 확인)
                try:
                    conn = self.get_db_connection(db_name)
                    if conn:
                        cursor = conn.cursor()
                        
                        # 참조 무결성 위반 검사
                        fk_table = fk['table']
                        fk_from = fk['from']
                        fk_to = fk['to']
                        
                        query = f"""
                        SELECT COUNT(*) FROM {table} 
                        WHERE {fk_from} IS NOT NULL 
                        AND {fk_from} NOT IN (SELECT {fk_to} FROM {fk_table})
                        """
                        
                        cursor.execute(query)
                        violation_count = cursor.fetchone()[0]
                        
                        if violation_count > 0:
                            issues.append(f"FK 무결성 위반: {table}.{fk_from} -> {fk_table}.{fk_to} ({violation_count}건)")
                            integrity_score -= 10
                        
                        conn.close()
                        
                except sqlite3.Error as e:
                    issues.append(f"FK 검증 실패: {table}.{fk_from} - {str(e)}")
                    integrity_score -= 5
        
        # 필수 인덱스 확인
        required_indexes = self.relationship_rules.get('required_indexes', {}).get(db_name, [])
        
        for required_index in required_indexes:
            table_name = required_index.split('.')[0]
            if table_name in tables:
                schema = self.get_table_schema(db_name, table_name)
                indexes = schema.get('indexes', [])
                
                # 인덱스 존재 여부 확인 (간단한 검사)
                has_index = len(indexes) > 0
                if not has_index:
                    issues.append(f"권장 인덱스 없음: {required_index}")
                    integrity_score -= 5
        
        integrity_score = max(0, integrity_score)
        
        # 상태 결정
        if integrity_score >= 95:
            status = "pass"
        elif integrity_score >= 80:
            status = "warning"
        else:
            status = "fail"
        
        recommendations = []
        if integrity_score < 100:
            recommendations.extend([
                "FK 제약 조건 수정 필요",
                "인덱스 추가 생성 검토",
                "데이터 정합성 확인"
            ])
        
        return ValidationResult(
            category="integrity",
            rule_name="relationship_integrity",
            status=status,
            score=integrity_score,
            message=f"관계 무결성: {integrity_score:.1f}점",
            details=issues,
            recommendations=recommendations
        )
    
    def validate_migration_completeness(self, db_name: str) -> ValidationResult:
        """마이그레이션 완성도 검증"""
        tables = self.get_table_list(db_name)
        issues = []
        completeness_score = 100.0
        
        if db_name == 'settings':
            # TV 시스템 필수 테이블 확인
            required_tv_tables = [
                'tv_trading_variables',
                'tv_variable_parameters',
                'tv_help_texts',
                'tv_indicator_categories'
            ]
            
            missing_tables = [table for table in required_tv_tables if table not in tables]
            for missing in missing_tables:
                issues.append(f"필수 TV 테이블 없음: {missing}")
                completeness_score -= 20
            
            # TV 테이블 데이터 존재 확인
            for table in required_tv_tables:
                if table in tables:
                    try:
                        conn = self.get_db_connection(db_name)
                        if conn:
                            cursor = conn.cursor()
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cursor.fetchone()[0]
                            
                            if count == 0:
                                issues.append(f"TV 테이블이 비어있음: {table}")
                                completeness_score -= 10
                            
                            conn.close()
                    except sqlite3.Error as e:
                        issues.append(f"TV 테이블 데이터 확인 실패: {table} - {str(e)}")
                        completeness_score -= 5
        
        elif db_name == 'strategies':
            # 사용자 데이터 테이블 구조 확인
            expected_user_tables = ['user_triggers', 'user_strategies']
            
            for table in expected_user_tables:
                if table not in tables:
                    issues.append(f"예상 사용자 테이블 없음: {table}")
                    completeness_score -= 15
        
        completeness_score = max(0, completeness_score)
        
        # 상태 결정
        if completeness_score >= 90:
            status = "pass"
        elif completeness_score >= 70:
            status = "warning"
        else:
            status = "fail"
        
        recommendations = []
        if completeness_score < 100:
            recommendations.extend([
                "super_db_migration_yaml_to_db.py로 누락 데이터 마이그레이션",
                "super_db_structure_generator.py로 누락 테이블 생성",
                "데이터 소스 확인"
            ])
        
        return ValidationResult(
            category="completeness",
            rule_name="migration_completeness",
            status=status,
            score=completeness_score,
            message=f"마이그레이션 완성도: {completeness_score:.1f}점",
            details=issues,
            recommendations=recommendations
        )
    
    def generate_full_validation_report(self, db_name: str) -> SchemaValidationReport:
        """종합 검증 보고서 생성"""
        validation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        results = []
        
        # 각 검증 실행
        naming_result = self.validate_naming_conventions(db_name)
        results.append(naming_result)
        
        integrity_result = self.verify_relationship_integrity(db_name)
        results.append(integrity_result)
        
        completeness_result = self.validate_migration_completeness(db_name)
        results.append(completeness_result)
        
        # 전체 점수 계산
        total_score = sum(result.score for result in results) / len(results)
        
        # 상태별 요약
        summary = {
            'pass': len([r for r in results if r.status == 'pass']),
            'warning': len([r for r in results if r.status == 'warning']),
            'fail': len([r for r in results if r.status == 'fail'])
        }
        
        # 중요 이슈 추출
        critical_issues = []
        recommendations = set()
        
        for result in results:
            if result.status == 'fail':
                critical_issues.extend(result.details[:2])  # 상위 2개만
            recommendations.update(result.recommendations)
        
        return SchemaValidationReport(
            db_name=db_name,
            validation_time=validation_time,
            overall_score=total_score,
            results=results,
            summary=summary,
            critical_issues=critical_issues,
            recommendations=list(recommendations)[:5]  # 상위 5개만
        )
    
    def print_validation_report(self, report: SchemaValidationReport) -> None:
        """검증 보고서 출력"""
        print(f"🔍 DB 스키마 검증 보고서: {report.db_name.upper()}")
        print("=" * 70)
        
        print(f"🕐 검증 시간: {report.validation_time}")
        print(f"📊 전체 점수: {report.overall_score:.1f}점")
        
        # 상태 표시
        if report.overall_score >= 90:
            status_emoji = "🟢"
            status_text = "우수"
        elif report.overall_score >= 70:
            status_emoji = "🟡"
            status_text = "양호"
        else:
            status_emoji = "🔴"
            status_text = "개선필요"
        
        print(f"{status_emoji} 전체 상태: {status_text}")
        
        # 요약 통계
        print(f"\n📋 검증 요약:")
        print(f"   🟢 통과: {report.summary['pass']}개")
        print(f"   🟡 경고: {report.summary['warning']}개")
        print(f"   🔴 실패: {report.summary['fail']}개")
        
        # 상세 결과
        print(f"\n📊 상세 검증 결과:")
        for result in report.results:
            status_emoji = {"pass": "🟢", "warning": "🟡", "fail": "🔴"}.get(result.status, "⚪")
            print(f"   {status_emoji} {result.rule_name}: {result.score:.1f}점")
            print(f"      {result.message}")
            
            if result.details:
                print(f"      세부사항: {', '.join(result.details[:2])}")
        
        # 중요 이슈
        if report.critical_issues:
            print(f"\n🚨 중요 이슈:")
            for issue in report.critical_issues:
                print(f"   • {issue}")
        
        # 권장사항
        if report.recommendations:
            print(f"\n💡 권장사항:")
            for rec in report.recommendations:
                print(f"   • {rec}")
    
    def validate_all_databases(self) -> Dict[str, SchemaValidationReport]:
        """모든 DB 검증 실행"""
        reports = {}
        
        for db_name in self.monitored_dbs.keys():
            if self.monitored_dbs[db_name].exists():
                reports[db_name] = self.generate_full_validation_report(db_name)
            else:
                logger.warning(f"⚠️ DB 파일 없음, 검증 건너뜀: {db_name}")
        
        return reports


def main():
    """
    🤖 LLM 사용 가이드: 메인 실행 함수
    
    명령행 인수에 따라 다른 검증 기능 실행:
    - --check naming: 네이밍 규칙 검증
    - --check separation: 구조/인스턴스 분리 검증
    - --check integrity: 관계 무결성 검증
    - --validate migration-completeness: 마이그레이션 완성도 검증
    
    🎯 LLM이 자주 사용할 패턴:
    1. python super_db_schema_validator.py --db settings.sqlite3 --rules all
    2. python super_db_schema_validator.py --check naming --all-dbs
    3. python super_db_schema_validator.py --validate migration-completeness
    """
    parser = argparse.ArgumentParser(
        description='🔄 Super DB Schema Validator - 스키마 정합성 검증 도구',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 특정 DB 전체 검증
  python super_db_schema_validator.py --db settings.sqlite3 --rules all
  
  # 네이밍 규칙 검증 (모든 DB)
  python super_db_schema_validator.py --check naming --all-dbs
  
  # 구조/인스턴스 분리 검증
  python super_db_schema_validator.py --check separation --settings settings.sqlite3 --strategies strategies.sqlite3
  
  # 마이그레이션 완성도 검증
  python super_db_schema_validator.py --validate migration-completeness
        """
    )
    
    parser.add_argument('--db', 
                       choices=['settings', 'strategies', 'market_data'],
                       help='검증할 특정 DB')
    
    parser.add_argument('--rules',
                       choices=['all', 'naming', 'integrity', 'completeness'],
                       help='적용할 검증 규칙')
    
    parser.add_argument('--check',
                       choices=['naming', 'separation', 'integrity'],
                       help='특정 검증 유형')
    
    parser.add_argument('--validate',
                       choices=['migration-completeness'],
                       help='특정 검증 실행')
    
    parser.add_argument('--all-dbs', action='store_true',
                       help='모든 DB 대상')
    
    parser.add_argument('--settings', help='Settings DB 파일 경로')
    parser.add_argument('--strategies', help='Strategies DB 파일 경로')
    
    args = parser.parse_args()
    
    validator = SuperDBSchemaValidator()
    
    try:
        if args.db and args.rules:
            # 특정 DB 검증
            if args.rules == 'all':
                report = validator.generate_full_validation_report(args.db)
                validator.print_validation_report(report)
                exit(0 if report.overall_score >= 70 else 1)
            else:
                # 개별 규칙 검증
                if args.rules == 'naming':
                    result = validator.validate_naming_conventions(args.db)
                elif args.rules == 'integrity':
                    result = validator.verify_relationship_integrity(args.db)
                elif args.rules == 'completeness':
                    result = validator.validate_migration_completeness(args.db)
                
                print(f"🔍 {result.rule_name} 검증 결과:")
                print(f"📊 점수: {result.score:.1f}점")
                print(f"📍 상태: {result.status}")
                print(f"📝 메시지: {result.message}")
                
                if result.details:
                    print(f"세부사항:")
                    for detail in result.details:
                        print(f"  • {detail}")
                
                exit(0 if result.status != 'fail' else 1)
        
        elif args.check == 'naming' and args.all_dbs:
            # 모든 DB 네이밍 검증
            print("🔍 전체 DB 네이밍 규칙 검증")
            print("=" * 50)
            
            all_passed = True
            for db_name in validator.monitored_dbs.keys():
                if validator.monitored_dbs[db_name].exists():
                    result = validator.validate_naming_conventions(db_name)
                    status_emoji = {"pass": "🟢", "warning": "🟡", "fail": "🔴"}.get(result.status, "⚪")
                    print(f"{status_emoji} {db_name.upper()}: {result.score:.1f}점 - {result.message}")
                    
                    if result.status == 'fail':
                        all_passed = False
                else:
                    print(f"⚪ {db_name.upper()}: 파일 없음")
            
            exit(0 if all_passed else 1)
        
        elif args.check == 'separation' and args.settings and args.strategies:
            # 구조/인스턴스 분리 검증
            result = validator.check_structure_instance_separation('settings', 'strategies')
            
            print("🔍 구조/인스턴스 분리 원칙 검증")
            print("=" * 40)
            print(f"📊 점수: {result.score:.1f}점")
            print(f"📍 상태: {result.status}")
            print(f"📝 메시지: {result.message}")
            
            if result.details:
                print(f"위반사항:")
                for detail in result.details:
                    print(f"  • {detail}")
            
            exit(0 if result.status != 'fail' else 1)
        
        elif args.validate == 'migration-completeness':
            # 마이그레이션 완성도 검증
            print("🔍 마이그레이션 완성도 검증")
            print("=" * 40)
            
            all_complete = True
            for db_name in ['settings', 'strategies']:
                if validator.monitored_dbs[db_name].exists():
                    result = validator.validate_migration_completeness(db_name)
                    status_emoji = {"pass": "🟢", "warning": "🟡", "fail": "🔴"}.get(result.status, "⚪")
                    print(f"{status_emoji} {db_name.upper()}: {result.score:.1f}점")
                    print(f"   {result.message}")
                    
                    if result.details:
                        for detail in result.details[:2]:
                            print(f"   • {detail}")
                    
                    if result.status == 'fail':
                        all_complete = False
                else:
                    print(f"⚪ {db_name.upper()}: 파일 없음")
                    all_complete = False
            
            exit(0 if all_complete else 1)
        
        else:
            # 기본: 모든 DB 전체 검증
            reports = validator.validate_all_databases()
            
            if not reports:
                print("❌ 검증할 DB 파일이 없습니다.")
                exit(1)
            
            overall_pass = True
            
            for db_name, report in reports.items():
                validator.print_validation_report(report)
                print()
                
                if report.overall_score < 70:
                    overall_pass = False
            
            # 전체 요약
            print("📋 전체 검증 요약:")
            total_score = sum(r.overall_score for r in reports.values()) / len(reports)
            print(f"   📊 평균 점수: {total_score:.1f}점")
            print(f"   🗄️ 검증 DB 수: {len(reports)}개")
            
            if overall_pass:
                print("   ✅ 전체 시스템 양호")
            else:
                print("   ⚠️ 일부 개선 필요")
            
            exit(0 if overall_pass else 1)
            
    except Exception as e:
        logger.error(f"❌ 검증 실행 중 오류: {e}")
        exit(1)


if __name__ == "__main__":
    main()
