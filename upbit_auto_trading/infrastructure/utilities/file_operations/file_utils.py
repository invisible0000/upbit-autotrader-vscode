# 파일 연산 유틸리티 - Infrastructure Layer
import hashlib
import shutil
import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("FileOperationsUtils")


def calculate_file_checksum(file_path: Path) -> str:
    """파일 체크섬 계산 (SHA-256)"""
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def verify_file_integrity(source_path: Path, target_path: Path) -> bool:
    """파일 무결성 검증 (체크섬 비교)"""
    try:
        source_checksum = calculate_file_checksum(source_path)
        target_checksum = calculate_file_checksum(target_path)
        return source_checksum == target_checksum
    except Exception:
        return False


def check_disk_space(source_path: Path, target_dir: Path, multiplier: float = 2.0) -> bool:
    """디스크 공간 확인 (파일 크기의 배수만큼 여유 공간 필요)"""
    try:
        file_size = source_path.stat().st_size
        required_space = file_size * multiplier
        free_space = shutil.disk_usage(target_dir).free
        return free_space >= required_space
    except Exception:
        return False


def get_file_metadata(file_path: Path) -> Dict[str, Any]:
    """파일 메타데이터 추출"""
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
            'checksum': calculate_file_checksum(file_path),
            'is_readable': os.access(file_path, os.R_OK),
            'is_writable': os.access(file_path, os.W_OK)
        }
    except Exception as e:
        logger.error(f"파일 메타데이터 추출 실패 {file_path}: {e}")
        return {'exists': False, 'error': str(e)}


def create_backup_filename(source_path: Path, prefix: str = "backup") -> str:
    """백업 파일명 생성"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{source_path.stem}_{prefix}_{timestamp}{source_path.suffix}"


def safe_atomic_copy(source_path: Path, target_path: Path, verify_integrity: bool = True) -> bool:
    """안전한 원자적 파일 복사"""
    try:
        # 1. 임시 파일로 복사
        temp_target = target_path.with_suffix(f"{target_path.suffix}.tmp")
        shutil.copy2(source_path, temp_target)

        # 2. 무결성 검증 (옵션)
        if verify_integrity and not verify_file_integrity(source_path, temp_target):
            temp_target.unlink(missing_ok=True)
            raise OSError("파일 복사 중 무결성 검증 실패")

        # 3. 원자적 이동 (최종 적용)
        shutil.move(temp_target, target_path)
        return True

    except Exception as e:
        logger.error(f"원자적 파일 복사 실패 {source_path} -> {target_path}: {e}")
        return False


def ensure_directory_exists(directory_path: Path) -> bool:
    """디렉토리 존재 보장"""
    try:
        directory_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"디렉토리 생성 실패 {directory_path}: {e}")
        return False


def cleanup_temp_files(temp_dir: Path, pattern: str = "*.tmp", max_age_hours: int = 24) -> int:
    """임시 파일 정리"""
    try:
        cleaned_count = 0
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)

        for temp_file in temp_dir.glob(pattern):
            if temp_file.stat().st_mtime < cutoff_time:
                temp_file.unlink()
                cleaned_count += 1

        logger.info(f"임시 파일 정리 완료: {cleaned_count}개 파일 삭제")
        return cleaned_count

    except Exception as e:
        logger.error(f"임시 파일 정리 실패: {e}")
        return 0
