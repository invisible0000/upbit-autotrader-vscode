#!/usr/bin/env python3
"""
🔄 Super DB Health Monitor
DB 상태 실시간 모니터링 및 성능 추적 도구

🤖 LLM 사용 가이드:
===================
이 도구는 3-Database 시스템의 건강도를 모니터링하고 성능을 추적합니다.

📋 주요 명령어 (tools 폴더에서 실행):
1. python super_db_health_monitor.py --mode realtime --interval 30
2. python super_db_health_monitor.py --mode tv-performance --period 7days
3. python super_db_health_monitor.py --mode migration-tools-check
4. python super_db_health_monitor.py --mode diagnose --all-dbs

🎯 언제 사용하면 좋은가:
- DB 성능 저하 징후 조기 발견
- 마이그레이션 도구들의 정상 작동 확인
- TV 변수 시스템 성능 모니터링
- 시스템 전반적인 건강도 체크

💡 출력 해석:
- 🟢 정상: 모든 지표가 임계값 내
- 🟡 주의: 일부 지표가 경고 수준
- 🔴 위험: 즉시 조치 필요한 문제 발견
- ⚡ 성능: 쿼리 실행 시간 및 최적화 제안

기능:
1. 3-Database 연결 상태 실시간 모니터링
2. TV 변수 시스템 성능 추적
3. 마이그레이션 도구들 상태 확인
4. 자동 경고 및 복구 제안

작성일: 2025-08-01
작성자: Upbit Auto Trading Team
"""
import sqlite3
import time
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
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
        logging.FileHandler('logs/super_db_health_monitor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class HealthMetrics:
    """건강도 지표 데이터 클래스"""
    timestamp: str
    db_name: str
    connection_time: float
    query_performance: Dict[str, float]
    table_record_counts: Dict[str, int]
    disk_usage_mb: float
    index_hit_ratio: float
    status: str  # 'healthy', 'warning', 'critical'
    issues: List[str]
    recommendations: List[str]


@dataclass
class MigrationToolStatus:
    """마이그레이션 도구 상태 데이터 클래스"""
    tool_name: str
    last_run: Optional[str]
    status: str  # 'active', 'idle', 'error'
    performance_score: float
    error_count: int
    success_count: int
    last_error: Optional[str]


class SuperDBHealthMonitor:
    """
    🔄 Super DB Health Monitor - 3-Database 시스템 건강도 모니터링
    
    🤖 LLM 사용 패턴:
    monitor = SuperDBHealthMonitor()
    monitor.run_realtime_monitoring(interval=30)
    monitor.generate_tv_performance_report("7days")
    monitor.check_migration_tools_status()
    
    💡 핵심 기능: 실시간 모니터링 + 성능 추적 + 문제 조기 발견
    """
    
    def __init__(self):
        """초기화 - 경로 및 설정 준비"""
        self.project_root = PROJECT_ROOT
        self.db_path = self.project_root / "upbit_auto_trading" / "data"
        self.data_info_path = (
            self.project_root / "upbit_auto_trading" / "utils" /
            "trading_variables" / "gui_variables_DB_migration_util" / "data_info"
        )
        
        # 로그 디렉토리 생성
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 모니터링 대상 DB 설정
        self.monitored_dbs = {
            'settings': self.db_path / 'settings.sqlite3',
            'strategies': self.db_path / 'strategies.sqlite3',
            'market_data': self.db_path / 'market_data.sqlite3'
        }
        
        # 성능 임계값 설정
        self.thresholds = {
            'connection_timeout': 5.0,      # 5초
            'query_timeout': 3.0,           # 3초
            'disk_usage_warning': 1000.0,   # 1GB
            'record_count_change': 0.1,     # 10% 변화
            'index_hit_ratio_min': 0.8      # 80%
        }
        
        # 모니터링 대상 TV 테이블들
        self.tv_tables = [
            'tv_trading_variables',
            'tv_variable_parameters',
            'tv_help_texts',
            'tv_indicator_categories'
        ]
        
        # 마이그레이션 도구 목록
        self.migration_tools = [
            'super_db_structure_generator.py',
            'super_db_extraction_db_to_yaml.py',
            'super_db_migration_yaml_to_db.py',
            'super_db_yaml_editor_workflow.py',
            'super_db_yaml_merger.py',
            'super_db_schema_extractor.py'
        ]
        
        logger.info("🔄 Super DB Health Monitor 초기화")
        logger.info(f"📂 DB Path: {self.db_path}")
        logger.info(f"🗄️ 모니터링 대상: {list(self.monitored_dbs.keys())}")
    
    def get_db_connection(self, db_name: str) -> Optional[sqlite3.Connection]:
        """안전한 DB 연결 생성"""
        db_file = self.monitored_dbs.get(db_name)
        
        if not db_file or not db_file.exists():
            logger.warning(f"⚠️ DB 파일 없음: {db_name} ({db_file})")
            return None
        
        try:
            start_time = time.time()
            conn = sqlite3.connect(db_file, timeout=self.thresholds['connection_timeout'])
            conn.row_factory = sqlite3.Row
            connection_time = time.time() - start_time
            
            if connection_time > self.thresholds['connection_timeout']:
                logger.warning(f"⚠️ 연결 지연: {db_name} ({connection_time:.2f}초)")
            
            return conn
            
        except sqlite3.Error as e:
            logger.error(f"❌ DB 연결 실패: {db_name} - {e}")
            return None
    
    def check_connection_status(self, db_name: str) -> Tuple[bool, float, List[str]]:
        """DB 연결 상태 확인"""
        issues = []
        start_time = time.time()
        
        conn = self.get_db_connection(db_name)
        if not conn:
            return False, 0.0, ["연결 실패"]
        
        try:
            # 기본 쿼리 테스트
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            connection_time = time.time() - start_time
            
            # 연결 시간 체크
            if connection_time > self.thresholds['connection_timeout']:
                issues.append(f"연결 지연 ({connection_time:.2f}초)")
            
            # 테이블 존재 체크
            if table_count == 0:
                issues.append("테이블 없음")
            
            conn.close()
            return True, connection_time, issues
            
        except sqlite3.Error as e:
            issues.append(f"쿼리 실패: {str(e)}")
            conn.close()
            return False, time.time() - start_time, issues
    
    def analyze_query_performance(self, db_name: str) -> Dict[str, float]:
        """쿼리 성능 분석"""
        performance_metrics = {}
        
        conn = self.get_db_connection(db_name)
        if not conn:
            return performance_metrics
        
        try:
            cursor = conn.cursor()
            
            # TV 테이블 성능 테스트 (settings DB인 경우)
            if db_name == 'settings':
                for table in self.tv_tables:
                    start_time = time.time()
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        cursor.fetchone()
                        query_time = time.time() - start_time
                        performance_metrics[f"{table}_count_query"] = query_time
                        
                        if query_time > self.thresholds['query_timeout']:
                            logger.warning(f"⚠️ 슬로우 쿼리: {table} ({query_time:.2f}초)")
                            
                    except sqlite3.Error as e:
                        logger.error(f"❌ {table} 쿼리 실패: {e}")
                        performance_metrics[f"{table}_count_query"] = -1
            
            # 일반적인 성능 테스트
            test_queries = [
                ("table_list", "SELECT name FROM sqlite_master WHERE type='table'"),
                ("pragma_info", "PRAGMA database_list"),
                ("index_list", "SELECT name FROM sqlite_master WHERE type='index'")
            ]
            
            for test_name, query in test_queries:
                start_time = time.time()
                try:
                    cursor.execute(query)
                    cursor.fetchall()
                    performance_metrics[test_name] = time.time() - start_time
                except sqlite3.Error as e:
                    logger.error(f"❌ {test_name} 쿼리 실패: {e}")
                    performance_metrics[test_name] = -1
            
            conn.close()
            return performance_metrics
            
        except Exception as e:
            logger.error(f"❌ 성능 분석 실패 ({db_name}): {e}")
            conn.close()
            return performance_metrics
    
    def get_table_record_counts(self, db_name: str) -> Dict[str, int]:
        """테이블별 레코드 수 조회"""
        record_counts = {}
        
        conn = self.get_db_connection(db_name)
        if not conn:
            return record_counts
        
        try:
            cursor = conn.cursor()
            
            # 모든 테이블 목록 조회
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # 각 테이블의 레코드 수 조회
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    record_counts[table] = count
                except sqlite3.Error as e:
                    logger.warning(f"⚠️ {table} 레코드 수 조회 실패: {e}")
                    record_counts[table] = -1
            
            conn.close()
            return record_counts
            
        except Exception as e:
            logger.error(f"❌ 레코드 수 조회 실패 ({db_name}): {e}")
            conn.close()
            return record_counts
    
    def calculate_disk_usage(self, db_name: str) -> float:
        """DB 파일 디스크 사용량 계산 (MB)"""
        db_file = self.monitored_dbs.get(db_name)
        if not db_file or not db_file.exists():
            return 0.0
        
        try:
            size_bytes = db_file.stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            return round(size_mb, 2)
        except Exception as e:
            logger.error(f"❌ 디스크 사용량 계산 실패 ({db_name}): {e}")
            return 0.0
    
    def calculate_index_hit_ratio(self, db_name: str) -> float:
        """인덱스 히트율 계산 (추정값)"""
        # SQLite에서는 정확한 히트율 계산이 어려우므로 간접 지표 사용
        conn = self.get_db_connection(db_name)
        if not conn:
            return 0.0
        
        try:
            cursor = conn.cursor()
            
            # 인덱스 수와 테이블 수 비율로 추정
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
            index_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            if table_count == 0:
                ratio = 0.0
            else:
                # 간단한 추정: 테이블당 인덱스 비율
                ratio = min(index_count / table_count, 1.0)
            
            conn.close()
            return round(ratio, 3)
            
        except Exception as e:
            logger.error(f"❌ 인덱스 히트율 계산 실패 ({db_name}): {e}")
            conn.close()
            return 0.0
    
    def generate_health_report(self, db_name: str) -> HealthMetrics:
        """종합 건강도 보고서 생성"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        issues = []
        recommendations = []
        
        # 연결 상태 확인
        is_connected, connection_time, connection_issues = self.check_connection_status(db_name)
        issues.extend(connection_issues)
        
        # 성능 분석
        query_performance = self.analyze_query_performance(db_name) if is_connected else {}
        
        # 테이블 레코드 수
        record_counts = self.get_table_record_counts(db_name) if is_connected else {}
        
        # 디스크 사용량
        disk_usage = self.calculate_disk_usage(db_name)
        
        # 인덱스 히트율
        index_hit_ratio = self.calculate_index_hit_ratio(db_name) if is_connected else 0.0
        
        # 상태 결정
        status = 'healthy'
        
        if not is_connected:
            status = 'critical'
            issues.append("DB 연결 불가")
            recommendations.append("DB 파일 권한 및 경로 확인")
        
        elif connection_time > self.thresholds['connection_timeout']:
            status = 'warning'
            recommendations.append("DB 연결 성능 최적화 필요")
        
        if disk_usage > self.thresholds['disk_usage_warning']:
            if status != 'critical':
                status = 'warning'
            issues.append(f"디스크 사용량 과다 ({disk_usage:.1f}MB)")
            recommendations.append("오래된 백업 파일 정리")
        
        if index_hit_ratio < self.thresholds['index_hit_ratio_min']:
            if status == 'healthy':
                status = 'warning'
            issues.append(f"인덱스 효율성 저하 ({index_hit_ratio:.1%})")
            recommendations.append("추가 인덱스 생성 검토")
        
        # TV 테이블 특별 검사 (settings DB)
        if db_name == 'settings' and is_connected:
            for table in self.tv_tables:
                if table in record_counts and record_counts[table] == 0:
                    if status == 'healthy':
                        status = 'warning'
                    issues.append(f"TV 테이블 비어있음: {table}")
                    recommendations.append(f"super_db_migration_yaml_to_db.py로 {table} 데이터 마이그레이션")
        
        return HealthMetrics(
            timestamp=timestamp,
            db_name=db_name,
            connection_time=connection_time,
            query_performance=query_performance,
            table_record_counts=record_counts,
            disk_usage_mb=disk_usage,
            index_hit_ratio=index_hit_ratio,
            status=status,
            issues=issues,
            recommendations=recommendations
        )
    
    def check_migration_tools_status(self) -> List[MigrationToolStatus]:
        """마이그레이션 도구들 상태 확인"""
        tools_status = []
        tools_dir = self.project_root / "tools"
        
        for tool_name in self.migration_tools:
            tool_path = tools_dir / tool_name
            
            if not tool_path.exists():
                status = MigrationToolStatus(
                    tool_name=tool_name,
                    last_run=None,
                    status='error',
                    performance_score=0.0,
                    error_count=1,
                    success_count=0,
                    last_error="파일 없음"
                )
                tools_status.append(status)
                continue
            
            # 파일 수정 시간으로 최근 사용 추정
            try:
                mtime = tool_path.stat().st_mtime
                last_run = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                
                # 간단한 상태 추정 (실제 사용시에는 로그 파일 분석 등으로 확장)
                status = MigrationToolStatus(
                    tool_name=tool_name,
                    last_run=last_run,
                    status='idle',  # 기본값
                    performance_score=0.85,  # 추정값
                    error_count=0,
                    success_count=1,
                    last_error=None
                )
                tools_status.append(status)
                
            except Exception as e:
                status = MigrationToolStatus(
                    tool_name=tool_name,
                    last_run=None,
                    status='error',
                    performance_score=0.0,
                    error_count=1,
                    success_count=0,
                    last_error=str(e)
                )
                tools_status.append(status)
        
        return tools_status
    
    def run_realtime_monitoring(self, interval: int = 30, duration: int = 0) -> None:
        """실시간 모니터링 실행"""
        print(f"🔄 실시간 DB 모니터링 시작 (간격: {interval}초)")
        print("Ctrl+C로 중지")
        print("=" * 80)
        
        start_time = time.time()
        iteration = 0
        
        try:
            while True:
                iteration += 1
                current_time = datetime.now().strftime("%H:%M:%S")
                
                print(f"\n📊 모니터링 #{iteration} - {current_time}")
                print("-" * 60)
                
                all_healthy = True
                
                for db_name in self.monitored_dbs.keys():
                    health = self.generate_health_report(db_name)
                    
                    # 상태 이모지
                    status_emoji = {
                        'healthy': '🟢',
                        'warning': '🟡', 
                        'critical': '🔴'
                    }.get(health.status, '⚪')
                    
                    print(f"{status_emoji} {db_name.upper()}: {health.status}")
                    print(f"   연결: {health.connection_time:.3f}초 | "
                          f"디스크: {health.disk_usage_mb:.1f}MB | "
                          f"인덱스: {health.index_hit_ratio:.1%}")
                    
                    if health.issues:
                        print(f"   ⚠️ 이슈: {', '.join(health.issues[:2])}")
                        all_healthy = False
                
                # 마이그레이션 도구 상태 (간소화)
                tools_status = self.check_migration_tools_status()
                error_tools = [t.tool_name for t in tools_status if t.status == 'error']
                
                if error_tools:
                    print(f"🔧 도구 오류: {len(error_tools)}개")
                    all_healthy = False
                else:
                    print(f"🔧 마이그레이션 도구: 정상 ({len(tools_status)}개)")
                
                if all_healthy:
                    print("✅ 전체 시스템 정상")
                else:
                    print("⚠️ 일부 문제 발견 - 상세 진단 권장")
                
                # 종료 조건 확인
                if duration > 0 and (time.time() - start_time) >= duration:
                    print(f"\n⏰ 모니터링 완료 ({duration}초)")
                    break
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n⏹️ 모니터링 중지됨")
        except Exception as e:
            print(f"\n❌ 모니터링 오류: {e}")
    
    def generate_tv_performance_report(self, period: str = "7days") -> str:
        """TV 시스템 성능 보고서 생성"""
        print(f"📊 TV 시스템 성능 보고서 ({period})")
        print("=" * 60)
        
        # settings DB 상세 분석
        health = self.generate_health_report('settings')
        
        print(f"🕐 생성 시간: {health.timestamp}")
        print(f"📍 상태: {health.status.upper()}")
        print(f"🔗 연결 시간: {health.connection_time:.3f}초")
        print(f"💾 디스크 사용량: {health.disk_usage_mb:.1f}MB")
        print(f"📈 인덱스 효율성: {health.index_hit_ratio:.1%}")
        
        print(f"\n📋 TV 테이블 현황:")
        for table in self.tv_tables:
            count = health.table_record_counts.get(table, 0)
            status_icon = "✅" if count > 0 else "❌"
            print(f"   {status_icon} {table}: {count:,}개 레코드")
        
        print(f"\n⚡ 쿼리 성능:")
        for query_name, time_taken in health.query_performance.items():
            if time_taken >= 0:
                performance_icon = "🟢" if time_taken < 1.0 else "🟡" if time_taken < 3.0 else "🔴"
                print(f"   {performance_icon} {query_name}: {time_taken:.3f}초")
            else:
                print(f"   ❌ {query_name}: 실패")
        
        if health.issues:
            print(f"\n⚠️ 발견된 이슈:")
            for issue in health.issues:
                print(f"   • {issue}")
        
        if health.recommendations:
            print(f"\n💡 권장사항:")
            for rec in health.recommendations:
                print(f"   • {rec}")
        
        # 추가 분석: YAML 파일 상태
        yaml_files = list(self.data_info_path.glob("*.yaml"))
        backup_files = list(self.data_info_path.glob("*backup*.yaml"))
        
        print(f"\n📄 YAML 파일 현황:")
        print(f"   📁 전체 YAML: {len(yaml_files)}개")
        print(f"   💾 백업 파일: {len(backup_files)}개")
        
        if self.data_info_path.exists():
            merged_dir = self.data_info_path / "_MERGED_"
            if merged_dir.exists():
                merged_files = list(merged_dir.glob("*.yaml"))
                print(f"   🔄 병합 파일: {len(merged_files)}개")
        
        return health.status
    
    def diagnose_all_systems(self) -> Dict[str, str]:
        """전체 시스템 종합 진단"""
        print("🔍 전체 시스템 종합 진단")
        print("=" * 80)
        
        results = {}
        
        # 각 DB 진단
        for db_name in self.monitored_dbs.keys():
            print(f"\n📊 {db_name.upper()} DB 진단:")
            print("-" * 40)
            
            health = self.generate_health_report(db_name)
            results[db_name] = health.status
            
            # 상태 출력
            status_emoji = {
                'healthy': '🟢',
                'warning': '🟡',
                'critical': '🔴'
            }.get(health.status, '⚪')
            
            print(f"{status_emoji} 전체 상태: {health.status.upper()}")
            print(f"🔗 연결: {health.connection_time:.3f}초")
            print(f"💾 디스크: {health.disk_usage_mb:.1f}MB")
            print(f"📊 테이블 수: {len(health.table_record_counts)}개")
            print(f"📈 인덱스: {health.index_hit_ratio:.1%}")
            
            if health.issues:
                print("⚠️ 이슈:")
                for issue in health.issues:
                    print(f"   • {issue}")
            
            if health.recommendations:
                print("💡 권장사항:")
                for rec in health.recommendations[:2]:  # 상위 2개만
                    print(f"   • {rec}")
        
        # 마이그레이션 도구 진단
        print(f"\n🔧 마이그레이션 도구 진단:")
        print("-" * 40)
        
        tools_status = self.check_migration_tools_status()
        
        for tool_status in tools_status:
            status_emoji = {
                'active': '🟢',
                'idle': '🟡',
                'error': '🔴'
            }.get(tool_status.status, '⚪')
            
            print(f"{status_emoji} {tool_status.tool_name}")
            if tool_status.last_run:
                print(f"   📅 최근 실행: {tool_status.last_run}")
            if tool_status.last_error:
                print(f"   ❌ 오류: {tool_status.last_error}")
        
        # 전체 요약
        print(f"\n📋 진단 요약:")
        print("-" * 40)
        
        healthy_count = len([s for s in results.values() if s == 'healthy'])
        warning_count = len([s for s in results.values() if s == 'warning'])
        critical_count = len([s for s in results.values() if s == 'critical'])
        
        total_dbs = len(results)
        
        print(f"🟢 정상: {healthy_count}/{total_dbs}개 DB")
        print(f"🟡 주의: {warning_count}/{total_dbs}개 DB")
        print(f"🔴 위험: {critical_count}/{total_dbs}개 DB")
        
        error_tools = len([t for t in tools_status if t.status == 'error'])
        total_tools = len(tools_status)
        
        print(f"🔧 도구: {total_tools - error_tools}/{total_tools}개 정상")
        
        # 전체 권장사항
        if critical_count > 0:
            print(f"\n🚨 즉시 조치 필요:")
            print(f"   • {critical_count}개 DB에 심각한 문제 발견")
            print(f"   • super_db_rollback_manager.py로 롤백 검토")
        elif warning_count > 0:
            print(f"\n⚠️ 주의 권장:")
            print(f"   • {warning_count}개 DB 성능 최적화 필요")
            print(f"   • 정기적인 모니터링 증가")
        else:
            print(f"\n✅ 시스템 양호:")
            print(f"   • 모든 DB 정상 작동 중")
            print(f"   • 현재 모니터링 유지")
        
        return results


def main():
    """
    🤖 LLM 사용 가이드: 메인 실행 함수
    
    명령행 인수에 따라 다른 모니터링 기능 실행:
    - --mode realtime: 실시간 모니터링
    - --mode tv-performance: TV 시스템 성능 보고서
    - --mode migration-tools-check: 마이그레이션 도구 상태 확인
    - --mode diagnose: 전체 시스템 종합 진단
    
    🎯 LLM이 자주 사용할 패턴:
    1. python super_db_health_monitor.py --mode diagnose --all-dbs
    2. python super_db_health_monitor.py --mode realtime --interval 30
    3. python super_db_health_monitor.py --mode tv-performance --period 7days
    """
    parser = argparse.ArgumentParser(
        description='🔄 Super DB Health Monitor - DB 상태 실시간 모니터링 도구',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 실시간 모니터링 (기본 30초 간격)
  python super_db_health_monitor.py --mode realtime --interval 30
  
  # TV 시스템 성능 보고서
  python super_db_health_monitor.py --mode tv-performance --period 7days
  
  # 마이그레이션 도구 상태 확인
  python super_db_health_monitor.py --mode migration-tools-check
  
  # 전체 시스템 진단
  python super_db_health_monitor.py --mode diagnose --all-dbs
        """
    )
    
    parser.add_argument('--mode', required=True,
                       choices=['realtime', 'tv-performance', 'migration-tools-check', 'diagnose'],
                       help='모니터링 모드')
    
    parser.add_argument('--interval', type=int, default=30,
                       help='실시간 모니터링 간격 (초, 기본값: 30)')
    
    parser.add_argument('--duration', type=int, default=0,
                       help='모니터링 지속 시간 (초, 0=무제한)')
    
    parser.add_argument('--period', default='7days',
                       choices=['1day', '7days', '30days'],
                       help='성능 보고서 기간')
    
    parser.add_argument('--all-dbs', action='store_true',
                       help='모든 DB 대상 (진단 모드용)')
    
    parser.add_argument('--db', 
                       choices=['settings', 'strategies', 'market_data'],
                       help='특정 DB만 대상')
    
    args = parser.parse_args()
    
    monitor = SuperDBHealthMonitor()
    
    try:
        if args.mode == 'realtime':
            monitor.run_realtime_monitoring(args.interval, args.duration)
            
        elif args.mode == 'tv-performance':
            status = monitor.generate_tv_performance_report(args.period)
            exit(0 if status == 'healthy' else 1)
            
        elif args.mode == 'migration-tools-check':
            tools_status = monitor.check_migration_tools_status()
            error_count = len([t for t in tools_status if t.status == 'error'])
            
            print("🔧 마이그레이션 도구 상태 확인")
            print("=" * 50)
            
            for tool_status in tools_status:
                status_emoji = {
                    'active': '🟢',
                    'idle': '🟡', 
                    'error': '🔴'
                }.get(tool_status.status, '⚪')
                
                print(f"{status_emoji} {tool_status.tool_name}: {tool_status.status}")
                if tool_status.last_error:
                    print(f"   ❌ {tool_status.last_error}")
            
            print(f"\n📊 요약: {len(tools_status) - error_count}/{len(tools_status)}개 도구 정상")
            exit(0 if error_count == 0 else 1)
            
        elif args.mode == 'diagnose':
            results = monitor.diagnose_all_systems()
            critical_count = len([s for s in results.values() if s == 'critical'])
            exit(0 if critical_count == 0 else 1)
            
    except Exception as e:
        logger.error(f"❌ 모니터링 실행 중 오류: {e}")
        exit(1)


if __name__ == "__main__":
    main()
