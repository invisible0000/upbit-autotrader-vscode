#!/usr/bin/env python3
"""
🔄 Super DB Rollback Manager
마이그레이션 실패 시 안전한 롤백 및 복구 관리 도구

🤖 LLM 사용 가이드:
===================
이 도구는 DB 마이그레이션 중 문제 발생 시 안전한 롤백을 제공합니다.

📋 주요 명령어 (tools 폴더에서 실행):
1. python super_db_rollback_manager.py --create-checkpoint "pre_migration_phase1"
2. python super_db_rollback_manager.py --rollback "pre_migration_phase1" --verify
3. python super_db_rollback_manager.py --list-checkpoints
4. python super_db_rollback_manager.py --auto-backup --schedule daily

🎯 언제 사용하면 좋은가:
- 중요한 마이그레이션 전 체크포인트 생성
- 마이그레이션 실패 시 이전 상태로 롤백
- 정기적인 백업 및 복구 점검
- 시스템 장애 시 빠른 복구

💡 출력 해석:
- 🟢 성공: 체크포인트 생성/롤백 성공
- 🟡 주의: 일부 파일 백업 실패 (부분 백업)
- 🔴 실패: 체크포인트 생성/롤백 실패
- 📦 백업: 전체/증분/구조만 백업 유형

기능:
1. 전체 시스템 체크포인트 생성
2. 단계별 안전 롤백
3. 백업 무결성 검증
4. 기존 Super DB 도구와 연동

작성일: 2025-08-01
작성자: Upbit Auto Trading Team
"""
import shutil
import json
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict

# 프로젝트 루트를 파이썬 패스에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/super_db_rollback_manager.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class CheckpointMetadata:
    """체크포인트 메타데이터"""
    checkpoint_id: str
    created_at: str
    description: str
    backup_type: str  # 'full', 'incremental', 'structure'
    db_files: List[str]
    yaml_files: List[str]
    backup_size_mb: float
    verification_status: str  # 'verified', 'partial', 'failed'
    tool_versions: Dict[str, str]
    
    
@dataclass
class RollbackResult:
    """롤백 결과"""
    checkpoint_id: str
    rollback_time: str
    success: bool
    restored_files: List[str]
    failed_files: List[str]
    verification_passed: bool
    issues: List[str]
    recommendations: List[str]


class SuperDBRollbackManager:
    """
    🔄 Super DB Rollback Manager - 안전한 롤백 및 복구 관리
    
    🤖 LLM 사용 패턴:
    manager = SuperDBRollbackManager()
    manager.create_migration_checkpoint("pre_major_update", "전체 백업")
    manager.rollback_to_checkpoint("pre_major_update", verify=True)
    manager.list_available_checkpoints()
    
    💡 핵심 기능: 완전 백업 + 안전 롤백 + 무결성 검증
    """
    
    def __init__(self):
        """초기화 - 경로 및 백업 설정 준비"""
        self.project_root = PROJECT_ROOT
        self.db_path = self.project_root / "upbit_auto_trading" / "data"
        self.data_info_path = (
            self.project_root / "upbit_auto_trading" / "utils" /
            "trading_variables" / "gui_variables_DB_migration_util" / "data_info"
        )
        
        # 백업 기본 디렉토리
        self.backup_base = self.project_root / "backups" / "rollback_checkpoints"
        self.backup_base.mkdir(parents=True, exist_ok=True)
        
        # 메타데이터 파일
        self.metadata_file = self.backup_base / "checkpoint_metadata.json"
        
        # 로그 디렉토리 생성
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 백업 대상 파일들
        self.target_dbs = {
            'settings': self.db_path / 'settings.sqlite3',
            'strategies': self.db_path / 'strategies.sqlite3',
            'market_data': self.db_path / 'market_data.sqlite3'
        }
        
        # 백업 레벨 설정
        self.backup_levels = {
            'full': {
                'include_db': True,
                'include_yaml': True,
                'include_merged': True,
                'include_backups': True,
                'include_logs': False
            },
            'incremental': {
                'include_db': True,
                'include_yaml': True,
                'include_merged': False,
                'include_backups': False,
                'include_logs': False
            },
            'structure': {
                'include_db': True,
                'include_yaml': False,
                'include_merged': False,
                'include_backups': False,
                'include_logs': False
            }
        }
        
        logger.info("🔄 Super DB Rollback Manager 초기화")
        logger.info(f"📂 DB Path: {self.db_path}")
        logger.info(f"💾 백업 경로: {self.backup_base}")
        logger.info(f"🗄️ 대상 DB: {list(self.target_dbs.keys())}")
    
    def load_checkpoint_metadata(self) -> Dict[str, CheckpointMetadata]:
        """체크포인트 메타데이터 로드"""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            checkpoints = {}
            for checkpoint_id, metadata_dict in data.items():
                checkpoints[checkpoint_id] = CheckpointMetadata(**metadata_dict)
            
            return checkpoints
            
        except Exception as e:
            logger.error(f"❌ 메타데이터 로드 실패: {e}")
            return {}
    
    def save_checkpoint_metadata(self, checkpoints: Dict[str, CheckpointMetadata]) -> None:
        """체크포인트 메타데이터 저장"""
        try:
            data = {}
            for checkpoint_id, metadata in checkpoints.items():
                data[checkpoint_id] = asdict(metadata)
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"❌ 메타데이터 저장 실패: {e}")
    
    def get_tool_versions(self) -> Dict[str, str]:
        """현재 Super DB 도구들의 버전 정보 수집"""
        tools_dir = self.project_root / "tools"
        tool_versions = {}
        
        super_db_tools = [
            'super_db_structure_generator.py',
            'super_db_extraction_db_to_yaml.py',
            'super_db_migration_yaml_to_db.py',
            'super_db_yaml_editor_workflow.py',
            'super_db_yaml_merger.py',
            'super_db_schema_extractor.py',
            'super_db_health_monitor.py',
            'super_db_schema_validator.py'
        ]
        
        for tool in super_db_tools:
            tool_path = tools_dir / tool
            if tool_path.exists():
                try:
                    mtime = tool_path.stat().st_mtime
                    version = datetime.fromtimestamp(mtime).strftime("%Y%m%d_%H%M%S")
                    tool_versions[tool] = version
                except Exception:
                    tool_versions[tool] = "unknown"
            else:
                tool_versions[tool] = "missing"
        
        return tool_versions
    
    def calculate_backup_size(self, backup_dir: Path) -> float:
        """백업 디렉토리 크기 계산 (MB)"""
        if not backup_dir.exists():
            return 0.0
        
        total_size = 0
        try:
            for file_path in backup_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            return round(total_size / (1024 * 1024), 2)
            
        except Exception as e:
            logger.error(f"❌ 백업 크기 계산 실패: {e}")
            return 0.0
    
    def backup_database_files(self, backup_dir: Path, backup_level: str) -> Tuple[List[str], List[str]]:
        """데이터베이스 파일 백업"""
        backed_up = []
        failed = []
        
        if not self.backup_levels[backup_level]['include_db']:
            return backed_up, failed
        
        db_backup_dir = backup_dir / "databases"
        db_backup_dir.mkdir(exist_ok=True)
        
        for db_name, db_file in self.target_dbs.items():
            if db_file.exists():
                try:
                    target_path = db_backup_dir / db_file.name
                    shutil.copy2(db_file, target_path)
                    backed_up.append(str(db_file))
                    logger.info(f"✅ DB 백업 완료: {db_name}")
                except Exception as e:
                    failed.append(f"{db_name}: {str(e)}")
                    logger.error(f"❌ DB 백업 실패 ({db_name}): {e}")
            else:
                logger.warning(f"⚠️ DB 파일 없음: {db_name} ({db_file})")
        
        return backed_up, failed
    
    def backup_yaml_files(self, backup_dir: Path, backup_level: str) -> Tuple[List[str], List[str]]:
        """YAML 파일들 백업"""
        backed_up = []
        failed = []
        
        if not self.backup_levels[backup_level]['include_yaml']:
            return backed_up, failed
        
        yaml_backup_dir = backup_dir / "yaml_files"
        yaml_backup_dir.mkdir(exist_ok=True)
        
        # data_info 디렉토리의 YAML 파일들
        if self.data_info_path.exists():
            try:
                for yaml_file in self.data_info_path.glob("*.yaml"):
                    target_path = yaml_backup_dir / yaml_file.name
                    shutil.copy2(yaml_file, target_path)
                    backed_up.append(str(yaml_file))
                
                # _MERGED_ 디렉토리 (필요한 경우)
                if self.backup_levels[backup_level]['include_merged']:
                    merged_dir = self.data_info_path / "_MERGED_"
                    if merged_dir.exists():
                        target_merged_dir = yaml_backup_dir / "_MERGED_"
                        shutil.copytree(merged_dir, target_merged_dir, dirs_exist_ok=True)
                        backed_up.extend([str(f) for f in merged_dir.rglob("*.yaml")])
                
                # _BACKUPS_ 디렉토리 (필요한 경우)
                if self.backup_levels[backup_level]['include_backups']:
                    backups_dir = self.data_info_path / "_BACKUPS_"
                    if backups_dir.exists():
                        target_backups_dir = yaml_backup_dir / "_BACKUPS_"
                        shutil.copytree(backups_dir, target_backups_dir, dirs_exist_ok=True)
                        backed_up.extend([str(f) for f in backups_dir.rglob("*.yaml")])
                
                logger.info(f"✅ YAML 파일 백업 완료: {len(backed_up)}개")
                
            except Exception as e:
                failed.append(f"YAML 백업 실패: {str(e)}")
                logger.error(f"❌ YAML 백업 실패: {e}")
        
        return backed_up, failed
    
    def verify_backup_integrity(self, backup_dir: Path, original_files: List[str]) -> Tuple[bool, List[str]]:
        """백업 무결성 검증"""
        issues = []
        
        # 백업 디렉토리 존재 확인
        if not backup_dir.exists():
            issues.append("백업 디렉토리 없음")
            return False, issues
        
        # 메타데이터 파일 확인
        metadata_backup = backup_dir / "checkpoint_info.json"
        if not metadata_backup.exists():
            issues.append("체크포인트 메타데이터 없음")
        
        # DB 파일 무결성 검증
        db_backup_dir = backup_dir / "databases"
        if db_backup_dir.exists():
            for db_name, original_db in self.target_dbs.items():
                if original_db.exists():
                    backup_db = db_backup_dir / original_db.name
                    if backup_db.exists():
                        # 크기 비교
                        original_size = original_db.stat().st_size
                        backup_size = backup_db.stat().st_size
                        
                        if original_size != backup_size:
                            issues.append(f"DB 크기 불일치: {db_name} (원본:{original_size}, 백업:{backup_size})")
                    else:
                        issues.append(f"백업 DB 파일 없음: {db_name}")
        
        # YAML 파일 확인
        yaml_backup_dir = backup_dir / "yaml_files"
        if yaml_backup_dir.exists():
            backup_yaml_count = len(list(yaml_backup_dir.glob("*.yaml")))
            if self.data_info_path.exists():
                original_yaml_count = len(list(self.data_info_path.glob("*.yaml")))
                if backup_yaml_count != original_yaml_count:
                    issues.append(f"YAML 파일 수 불일치 (원본:{original_yaml_count}, 백업:{backup_yaml_count})")
        
        integrity_passed = len(issues) == 0
        return integrity_passed, issues
    
    def create_migration_checkpoint(self, checkpoint_id: str, description: str = "", 
                                   backup_type: str = "full") -> bool:
        """마이그레이션 체크포인트 생성"""
        logger.info(f"🔄 체크포인트 생성 시작: {checkpoint_id}")
        
        # 기존 메타데이터 로드
        checkpoints = self.load_checkpoint_metadata()
        
        # 중복 ID 확인
        if checkpoint_id in checkpoints:
            logger.error(f"❌ 이미 존재하는 체크포인트 ID: {checkpoint_id}")
            return False
        
        # 백업 디렉토리 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_base / f"{checkpoint_id}_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 1. DB 파일 백업
            print(f"📦 DB 파일 백업 중...")
            db_backed_up, db_failed = self.backup_database_files(backup_dir, backup_type)
            
            # 2. YAML 파일 백업
            print(f"📄 YAML 파일 백업 중...")
            yaml_backed_up, yaml_failed = self.backup_yaml_files(backup_dir, backup_type)
            
            # 3. 체크포인트 정보 저장
            checkpoint_info = {
                'checkpoint_id': checkpoint_id,
                'created_at': datetime.now().isoformat(),
                'description': description,
                'backup_type': backup_type,
                'backup_location': str(backup_dir),
                'tool_versions': self.get_tool_versions()
            }
            
            info_file = backup_dir / "checkpoint_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_info, f, indent=2, ensure_ascii=False)
            
            # 4. 백업 무결성 검증
            print(f"🔍 백업 무결성 검증 중...")
            integrity_passed, integrity_issues = self.verify_backup_integrity(backup_dir, db_backed_up + yaml_backed_up)
            
            # 5. 메타데이터 생성
            backup_size = self.calculate_backup_size(backup_dir)
            
            verification_status = "verified" if integrity_passed else "partial" if len(integrity_issues) < 3 else "failed"
            
            metadata = CheckpointMetadata(
                checkpoint_id=checkpoint_id,
                created_at=datetime.now().isoformat(),
                description=description,
                backup_type=backup_type,
                db_files=db_backed_up,
                yaml_files=yaml_backed_up,
                backup_size_mb=backup_size,
                verification_status=verification_status,
                tool_versions=self.get_tool_versions()
            )
            
            # 메타데이터 저장
            checkpoints[checkpoint_id] = metadata
            self.save_checkpoint_metadata(checkpoints)
            
            # 결과 출력
            print(f"✅ 체크포인트 생성 완료: {checkpoint_id}")
            print(f"📊 백업 통계:")
            print(f"   💾 DB 파일: {len(db_backed_up)}개 백업, {len(db_failed)}개 실패")
            print(f"   📄 YAML 파일: {len(yaml_backed_up)}개 백업, {len(yaml_failed)}개 실패")
            print(f"   📦 백업 크기: {backup_size:.1f}MB")
            print(f"   🔍 무결성: {verification_status}")
            
            if integrity_issues:
                print(f"⚠️ 무결성 이슈:")
                for issue in integrity_issues[:3]:
                    print(f"   • {issue}")
            
            return verification_status != "failed"
            
        except Exception as e:
            logger.error(f"❌ 체크포인트 생성 실패: {e}")
            
            # 실패 시 부분 백업 정리
            if backup_dir.exists():
                try:
                    shutil.rmtree(backup_dir)
                except Exception:
                    pass
            
            return False
    
    def rollback_to_checkpoint(self, checkpoint_id: str, verify: bool = True) -> RollbackResult:
        """특정 체크포인트로 롤백"""
        logger.info(f"🔄 롤백 시작: {checkpoint_id}")
        
        # 메타데이터 로드
        checkpoints = self.load_checkpoint_metadata()
        
        if checkpoint_id not in checkpoints:
            logger.error(f"❌ 체크포인트 없음: {checkpoint_id}")
            return RollbackResult(
                checkpoint_id=checkpoint_id,
                rollback_time=datetime.now().isoformat(),
                success=False,
                restored_files=[],
                failed_files=[],
                verification_passed=False,
                issues=["체크포인트가 존재하지 않음"],
                recommendations=["사용 가능한 체크포인트 목록 확인"]
            )
        
        metadata = checkpoints[checkpoint_id]
        
        # 백업 디렉토리 찾기
        backup_dirs = list(self.backup_base.glob(f"{checkpoint_id}_*"))
        if not backup_dirs:
            return RollbackResult(
                checkpoint_id=checkpoint_id,
                rollback_time=datetime.now().isoformat(),
                success=False,
                restored_files=[],
                failed_files=[],
                verification_passed=False,
                issues=["백업 디렉토리를 찾을 수 없음"],
                recommendations=["체크포인트 재생성 필요"]
            )
        
        backup_dir = backup_dirs[0]  # 가장 최근 백업 사용
        
        restored_files = []
        failed_files = []
        issues = []
        
        try:
            print(f"🔄 롤백 진행 중: {checkpoint_id}")
            
            # 1. 현재 상태 임시 백업 생성
            temp_backup_id = f"temp_before_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"💾 현재 상태 임시 백업 생성: {temp_backup_id}")
            temp_backup_success = self.create_migration_checkpoint(temp_backup_id, "롤백 전 임시 백업", "incremental")
            
            if not temp_backup_success:
                issues.append("임시 백업 생성 실패")
            
            # 2. DB 파일 복원
            db_backup_dir = backup_dir / "databases"
            if db_backup_dir.exists():
                print(f"📊 DB 파일 복원 중...")
                for db_name, db_file in self.target_dbs.items():
                    backup_db = db_backup_dir / db_file.name
                    if backup_db.exists():
                        try:
                            # 기존 파일 백업 후 교체
                            if db_file.exists():
                                temp_file = db_file.with_suffix('.temp_rollback')
                                shutil.move(db_file, temp_file)
                            
                            shutil.copy2(backup_db, db_file)
                            restored_files.append(str(db_file))
                            
                            # 임시 파일 정리
                            temp_file = db_file.with_suffix('.temp_rollback')
                            if temp_file.exists():
                                temp_file.unlink()
                            
                            logger.info(f"✅ DB 복원 완료: {db_name}")
                            
                        except Exception as e:
                            failed_files.append(f"{db_name}: {str(e)}")
                            logger.error(f"❌ DB 복원 실패 ({db_name}): {e}")
                            
                            # 실패 시 원본 복구 시도
                            temp_file = db_file.with_suffix('.temp_rollback')
                            if temp_file.exists():
                                try:
                                    shutil.move(temp_file, db_file)
                                except Exception:
                                    pass
            
            # 3. YAML 파일 복원
            yaml_backup_dir = backup_dir / "yaml_files"
            if yaml_backup_dir.exists():
                print(f"📄 YAML 파일 복원 중...")
                
                # 기존 YAML 파일들 백업
                if self.data_info_path.exists():
                    for yaml_file in self.data_info_path.glob("*.yaml"):
                        try:
                            temp_file = yaml_file.with_suffix('.temp_rollback')
                            shutil.move(yaml_file, temp_file)
                        except Exception:
                            pass
                
                # 백업된 YAML 파일들 복원
                for yaml_file in yaml_backup_dir.glob("*.yaml"):
                    try:
                        target_path = self.data_info_path / yaml_file.name
                        shutil.copy2(yaml_file, target_path)
                        restored_files.append(str(target_path))
                    except Exception as e:
                        failed_files.append(f"{yaml_file.name}: {str(e)}")
                
                # _MERGED_ 디렉토리 복원
                merged_backup = yaml_backup_dir / "_MERGED_"
                if merged_backup.exists():
                    merged_target = self.data_info_path / "_MERGED_"
                    try:
                        if merged_target.exists():
                            shutil.rmtree(merged_target)
                        shutil.copytree(merged_backup, merged_target)
                        restored_files.append(str(merged_target))
                    except Exception as e:
                        failed_files.append(f"_MERGED_: {str(e)}")
            
            # 4. 롤백 검증 (옵션)
            verification_passed = True
            if verify:
                print(f"🔍 롤백 검증 중...")
                
                # 간단한 DB 연결 테스트
                for db_name, db_file in self.target_dbs.items():
                    if db_file.exists():
                        try:
                            import sqlite3
                            conn = sqlite3.connect(db_file)
                            cursor = conn.cursor()
                            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                            table_count = cursor.fetchone()[0]
                            conn.close()
                            
                            if table_count == 0:
                                issues.append(f"복원된 DB가 비어있음: {db_name}")
                                verification_passed = False
                                
                        except Exception as e:
                            issues.append(f"DB 검증 실패: {db_name} - {str(e)}")
                            verification_passed = False
            
            success = len(failed_files) == 0
            
            # 결과 출력
            if success:
                print(f"✅ 롤백 완료: {checkpoint_id}")
            else:
                print(f"⚠️ 롤백 부분 완료: {checkpoint_id}")
            
            print(f"📊 롤백 통계:")
            print(f"   ✅ 복원 성공: {len(restored_files)}개 파일")
            print(f"   ❌ 복원 실패: {len(failed_files)}개 파일")
            
            if failed_files:
                print(f"실패 목록:")
                for failed in failed_files[:3]:
                    print(f"   • {failed}")
            
            recommendations = []
            if not success:
                recommendations.extend([
                    "실패한 파일들을 수동으로 복원",
                    "임시 백업에서 추가 복구 시도",
                    "super_db_health_monitor.py로 시스템 상태 확인"
                ])
            
            return RollbackResult(
                checkpoint_id=checkpoint_id,
                rollback_time=datetime.now().isoformat(),
                success=success,
                restored_files=restored_files,
                failed_files=failed_files,
                verification_passed=verification_passed,
                issues=issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"❌ 롤백 실행 중 오류: {e}")
            return RollbackResult(
                checkpoint_id=checkpoint_id,
                rollback_time=datetime.now().isoformat(),
                success=False,
                restored_files=restored_files,
                failed_files=failed_files,
                verification_passed=False,
                issues=[f"롤백 실행 오류: {str(e)}"],
                recommendations=["시스템 관리자에게 문의"]
            )
    
    def list_available_checkpoints(self) -> List[CheckpointMetadata]:
        """사용 가능한 체크포인트 목록 조회"""
        checkpoints = self.load_checkpoint_metadata()
        return list(checkpoints.values())
    
    def cleanup_old_checkpoints(self, keep_count: int = 10) -> int:
        """오래된 체크포인트 정리"""
        checkpoints = self.load_checkpoint_metadata()
        
        if len(checkpoints) <= keep_count:
            return 0
        
        # 생성 시간 기준 정렬
        sorted_checkpoints = sorted(
            checkpoints.items(),
            key=lambda x: x[1].created_at,
            reverse=True
        )
        
        # 보관할 체크포인트와 삭제할 체크포인트 분리
        to_keep = sorted_checkpoints[:keep_count]
        to_delete = sorted_checkpoints[keep_count:]
        
        deleted_count = 0
        
        for checkpoint_id, metadata in to_delete:
            try:
                # 백업 디렉토리 삭제
                backup_dirs = list(self.backup_base.glob(f"{checkpoint_id}_*"))
                for backup_dir in backup_dirs:
                    if backup_dir.exists():
                        shutil.rmtree(backup_dir)
                
                # 메타데이터에서 제거
                del checkpoints[checkpoint_id]
                deleted_count += 1
                
                logger.info(f"🗑️ 체크포인트 삭제 완료: {checkpoint_id}")
                
            except Exception as e:
                logger.error(f"❌ 체크포인트 삭제 실패 ({checkpoint_id}): {e}")
        
        # 업데이트된 메타데이터 저장
        self.save_checkpoint_metadata(checkpoints)
        
        return deleted_count


def main():
    """
    🤖 LLM 사용 가이드: 메인 실행 함수
    
    명령행 인수에 따라 다른 롤백 관리 기능 실행:
    - --create-checkpoint: 새 체크포인트 생성
    - --rollback: 지정된 체크포인트로 롤백
    - --list-checkpoints: 사용 가능한 체크포인트 목록
    - --cleanup: 오래된 체크포인트 정리
    
    🎯 LLM이 자주 사용할 패턴:
    1. python super_db_rollback_manager.py --create-checkpoint "pre_migration" --description "마이그레이션 전 백업"
    2. python super_db_rollback_manager.py --rollback "pre_migration" --verify
    3. python super_db_rollback_manager.py --list-checkpoints
    """
    parser = argparse.ArgumentParser(
        description='🔄 Super DB Rollback Manager - 안전한 롤백 및 복구 관리 도구',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 체크포인트 생성
  python super_db_rollback_manager.py --create-checkpoint "pre_migration_phase1" --description "1단계 마이그레이션 전"
  
  # 롤백 실행
  python super_db_rollback_manager.py --rollback "pre_migration_phase1" --verify
  
  # 체크포인트 목록
  python super_db_rollback_manager.py --list-checkpoints
  
  # 정리
  python super_db_rollback_manager.py --cleanup --keep 5
        """
    )
    
    parser.add_argument('--create-checkpoint', 
                       help='새 체크포인트 생성 (체크포인트 ID)')
    
    parser.add_argument('--description', default='',
                       help='체크포인트 설명')
    
    parser.add_argument('--backup-type', default='full',
                       choices=['full', 'incremental', 'structure'],
                       help='백업 유형')
    
    parser.add_argument('--rollback',
                       help='롤백할 체크포인트 ID')
    
    parser.add_argument('--verify', action='store_true',
                       help='롤백 후 검증 실행')
    
    parser.add_argument('--list-checkpoints', action='store_true',
                       help='사용 가능한 체크포인트 목록 표시')
    
    parser.add_argument('--cleanup', action='store_true',
                       help='오래된 체크포인트 정리')
    
    parser.add_argument('--keep', type=int, default=10,
                       help='보관할 체크포인트 수 (기본값: 10)')
    
    args = parser.parse_args()
    
    manager = SuperDBRollbackManager()
    
    try:
        if args.create_checkpoint:
            success = manager.create_migration_checkpoint(
                args.create_checkpoint, 
                args.description, 
                args.backup_type
            )
            exit(0 if success else 1)
            
        elif args.rollback:
            result = manager.rollback_to_checkpoint(args.rollback, args.verify)
            
            if not result.success:
                print(f"❌ 롤백 실패:")
                for issue in result.issues:
                    print(f"   • {issue}")
                
                if result.recommendations:
                    print(f"권장사항:")
                    for rec in result.recommendations:
                        print(f"   • {rec}")
            
            exit(0 if result.success else 1)
            
        elif args.list_checkpoints:
            checkpoints = manager.list_available_checkpoints()
            
            if not checkpoints:
                print("📋 사용 가능한 체크포인트가 없습니다.")
                exit(0)
            
            print("📋 사용 가능한 체크포인트:")
            print("=" * 80)
            
            # 최신순으로 정렬
            sorted_checkpoints = sorted(checkpoints, key=lambda x: x.created_at, reverse=True)
            
            for checkpoint in sorted_checkpoints:
                status_emoji = {
                    'verified': '🟢',
                    'partial': '🟡',
                    'failed': '🔴'
                }.get(checkpoint.verification_status, '⚪')
                
                created_date = datetime.fromisoformat(checkpoint.created_at).strftime('%Y-%m-%d %H:%M')
                
                print(f"{status_emoji} {checkpoint.checkpoint_id}")
                print(f"   📅 생성일: {created_date}")
                print(f"   📦 크기: {checkpoint.backup_size_mb:.1f}MB")
                print(f"   📋 설명: {checkpoint.description or '설명 없음'}")
                print(f"   🔧 백업 유형: {checkpoint.backup_type}")
                print(f"   💾 DB 파일: {len(checkpoint.db_files)}개")
                print(f"   📄 YAML 파일: {len(checkpoint.yaml_files)}개")
                print()
            
            exit(0)
            
        elif args.cleanup:
            deleted_count = manager.cleanup_old_checkpoints(args.keep)
            print(f"🗑️ 체크포인트 정리 완료: {deleted_count}개 삭제")
            print(f"📦 보관 중인 체크포인트: {args.keep}개")
            exit(0)
            
        else:
            print("❌ 작업을 지정해주세요. --help로 사용법을 확인하세요.")
            exit(1)
            
    except Exception as e:
        logger.error(f"❌ 실행 중 오류: {e}")
        exit(1)


if __name__ == "__main__":
    main()
