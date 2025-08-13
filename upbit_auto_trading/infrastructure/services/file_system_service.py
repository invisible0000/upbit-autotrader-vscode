"""
File System Service Adapter

데이터베이스 설정 변경에 필요한 파일 시스템 작업을 담당하는 외부 서비스 어댑터입니다.
Domain Layer의 Use Case들이 파일 시스템과 상호작용할 때 사용합니다.

Features:
- 데이터베이스 파일 이동/복사/백업
- 안전한 파일 작업 (원자적 연산)
- 파일 무결성 검증 (체크섬)
- 디스크 공간 확인
- 권한 검증

Design Principles:
- Adapter Pattern: Domain Service → Infrastructure Service 매핑
- Fail-Safe Operations: 모든 파일 작업은 원자적 수행
- Error Transparency: Domain 예외로 변환하여 전파
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.configuration import InfrastructurePaths

logger = create_component_logger("FileSystemService")


class FileSystemService:
    """파일 시스템 작업을 위한 Infrastructure Service"""

    def __init__(self):
        self._logger = logger
        self._paths = InfrastructurePaths()
        self._temp_dir = self._paths.DATA_DIR / ".tmp"
        self._temp_dir.mkdir(exist_ok=True)

    async def copy_database_file(self, source_path: Path, target_path: Path) -> bool:
        """
        데이터베이스 파일을 안전하게 복사

        Args:
            source_path: 원본 파일 경로
            target_path: 대상 파일 경로

        Returns:
            복사 성공 여부
        """
        try:
            self._logger.info(f"📁 데이터베이스 파일 복사 시작: {source_path} → {target_path}")

            # 1. 전제 조건 검증
            if not source_path.exists():
                raise FileNotFoundError(f"원본 파일이 존재하지 않습니다: {source_path}")

            if not self._check_disk_space(source_path, target_path.parent):
                raise OSError("디스크 공간이 부족합니다")

            # 2. 대상 디렉토리 생성
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # 3. 임시 파일로 복사 (원자적 연산)
            temp_target = self._temp_dir / f"{target_path.name}.tmp"
            shutil.copy2(source_path, temp_target)

            # 4. 무결성 검증
            if not self._verify_file_integrity(source_path, temp_target):
                temp_target.unlink(missing_ok=True)
                raise OSError("파일 복사 중 무결성 검증 실패")

            # 5. 원자적 이동 (최종 적용)
            shutil.move(temp_target, target_path)

            self._logger.info(f"✅ 데이터베이스 파일 복사 완료: {target_path}")
            return True

        except Exception as e:
            self._logger.error(f"❌ 데이터베이스 파일 복사 실패: {e}")
            # 임시 파일 정리
            temp_target = self._temp_dir / f"{target_path.name}.tmp"
            temp_target.unlink(missing_ok=True)
            raise

    async def move_database_file(self, source_path: Path, target_path: Path) -> bool:
        """
        데이터베이스 파일을 안전하게 이동

        Args:
            source_path: 원본 파일 경로
            target_path: 대상 파일 경로

        Returns:
            이동 성공 여부
        """
        try:
            self._logger.info(f"📁 데이터베이스 파일 이동 시작: {source_path} → {target_path}")

            # 1. 백업 생성 (안전을 위해)
            backup_path = self._create_backup_path(source_path)
            await self.copy_database_file(source_path, backup_path)

            # 2. 파일 이동
            success = await self.copy_database_file(source_path, target_path)

            if success:
                # 3. 원본 파일 삭제
                source_path.unlink()
                self._logger.info(f"✅ 데이터베이스 파일 이동 완료: {target_path}")

                # 4. 백업 파일 정리 (필요 시 보관)
                # backup_path.unlink()  # 임시 백업 삭제

                return True
            else:
                raise OSError("파일 복사 단계에서 실패")

        except Exception as e:
            self._logger.error(f"❌ 데이터베이스 파일 이동 실패: {e}")
            raise

    async def create_backup(self, source_path: Path, backup_dir: Path) -> Path:
        """
        데이터베이스 백업 생성

        Args:
            source_path: 백업할 파일 경로
            backup_dir: 백업 디렉토리

        Returns:
            생성된 백업 파일 경로
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{source_path.stem}_backup_{timestamp}{source_path.suffix}"
            backup_path = backup_dir / backup_filename

            self._logger.info(f"💾 백업 생성 시작: {source_path} → {backup_path}")

            await self.copy_database_file(source_path, backup_path)

            # 백업 메타데이터 생성
            metadata = {
                'source_file': str(source_path),
                'backup_created': datetime.now().isoformat(),
                'file_size': backup_path.stat().st_size,
                'checksum': self._calculate_checksum(backup_path)
            }

            metadata_path = backup_path.with_suffix('.meta.json')
            import json
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            self._logger.info(f"✅ 백업 생성 완료: {backup_path}")
            return backup_path

        except Exception as e:
            self._logger.error(f"❌ 백업 생성 실패: {e}")
            raise

    async def restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        """
        백업에서 데이터베이스 복원

        Args:
            backup_path: 백업 파일 경로
            target_path: 복원할 대상 경로

        Returns:
            복원 성공 여부
        """
        try:
            self._logger.info(f"🔄 백업 복원 시작: {backup_path} → {target_path}")

            # 1. 백업 파일 검증
            if not backup_path.exists():
                raise FileNotFoundError(f"백업 파일이 존재하지 않습니다: {backup_path}")

            # 2. 메타데이터 검증 (있는 경우)
            metadata_path = backup_path.with_suffix('.meta.json')
            if metadata_path.exists():
                if not self._verify_backup_metadata(backup_path, metadata_path):
                    raise OSError("백업 파일 무결성 검증 실패")

            # 3. 현재 파일 백업 (복원 전 안전장치)
            if target_path.exists():
                safety_backup = await self.create_backup(target_path, self._temp_dir)
                self._logger.info(f"🛡️ 복원 전 안전 백업 생성: {safety_backup}")

            # 4. 복원 실행
            success = await self.copy_database_file(backup_path, target_path)

            if success:
                self._logger.info(f"✅ 백업 복원 완료: {target_path}")
                return True
            else:
                raise OSError("백업 복원 실패")

        except Exception as e:
            self._logger.error(f"❌ 백업 복원 실패: {e}")
            raise

    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """
        파일 정보 조회

        Args:
            file_path: 조회할 파일 경로

        Returns:
            파일 정보 딕셔너리
        """
        try:
            if not file_path.exists():
                return {'exists': False}

            stat = file_path.stat()

            return {
                'exists': True,
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'checksum': self._calculate_checksum(file_path),
                'is_readable': os.access(file_path, os.R_OK),
                'is_writable': os.access(file_path, os.W_OK)
            }

        except Exception as e:
            self._logger.error(f"❌ 파일 정보 조회 실패: {e}")
            return {'exists': False, 'error': str(e)}

    def list_backups(self, backup_dir: Path, pattern: str = "*_backup_*") -> List[Dict[str, Any]]:
        """
        백업 파일 목록 조회

        Args:
            backup_dir: 백업 디렉토리
            pattern: 백업 파일 패턴

        Returns:
            백업 파일 정보 리스트
        """
        try:
            if not backup_dir.exists():
                return []

            backup_files = []
            for backup_path in backup_dir.glob(pattern):
                if backup_path.is_file() and not backup_path.name.endswith('.meta.json'):
                    info = self.get_file_info(backup_path)
                    info['path'] = str(backup_path)
                    info['name'] = backup_path.name
                    backup_files.append(info)

            # 수정 시간 기준 역순 정렬 (최신 순)
            backup_files.sort(key=lambda x: x.get('modified', ''), reverse=True)

            return backup_files

        except Exception as e:
            self._logger.error(f"❌ 백업 목록 조회 실패: {e}")
            return []

    def cleanup_old_backups(self, backup_dir: Path, keep_count: int = 10) -> int:
        """
        오래된 백업 파일 정리

        Args:
            backup_dir: 백업 디렉토리
            keep_count: 보관할 백업 개수

        Returns:
            삭제된 백업 개수
        """
        try:
            backups = self.list_backups(backup_dir)

            if len(backups) <= keep_count:
                return 0

            deleted_count = 0
            backups_to_delete = backups[keep_count:]

            for backup in backups_to_delete:
                backup_path = Path(backup['path'])
                metadata_path = backup_path.with_suffix('.meta.json')

                # 백업 파일 삭제
                if backup_path.exists():
                    backup_path.unlink()
                    deleted_count += 1

                # 메타데이터 파일 삭제
                if metadata_path.exists():
                    metadata_path.unlink()

            self._logger.info(f"🧹 오래된 백업 {deleted_count}개 정리 완료")
            return deleted_count

        except Exception as e:
            self._logger.error(f"❌ 백업 정리 실패: {e}")
            return 0

    # === Private Helper Methods ===

    def _check_disk_space(self, source_path: Path, target_dir: Path) -> bool:
        """디스크 공간 확인 (파일 크기의 2배 여유 공간 필요)"""
        try:
            file_size = source_path.stat().st_size
            required_space = file_size * 2  # 2배 여유

            free_space = shutil.disk_usage(target_dir).free

            return free_space >= required_space

        except Exception:
            return False

    def _calculate_checksum(self, file_path: Path) -> str:
        """파일 체크섬 계산 (SHA-256)"""
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    def _verify_file_integrity(self, source_path: Path, target_path: Path) -> bool:
        """파일 무결성 검증 (체크섬 비교)"""
        try:
            source_checksum = self._calculate_checksum(source_path)
            target_checksum = self._calculate_checksum(target_path)

            return source_checksum == target_checksum

        except Exception:
            return False

    def _create_backup_path(self, source_path: Path) -> Path:
        """임시 백업 경로 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{source_path.stem}_temp_backup_{timestamp}{source_path.suffix}"
        return self._temp_dir / backup_filename

    def _verify_backup_metadata(self, backup_path: Path, metadata_path: Path) -> bool:
        """백업 메타데이터 검증"""
        try:
            import json

            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # 파일 크기 검증
            if backup_path.stat().st_size != metadata.get('file_size'):
                return False

            # 체크섬 검증
            current_checksum = self._calculate_checksum(backup_path)
            if current_checksum != metadata.get('checksum'):
                return False

            return True

        except Exception:
            return False


# 전역 인스턴스 (Singleton 패턴)
file_system_service = FileSystemService()
