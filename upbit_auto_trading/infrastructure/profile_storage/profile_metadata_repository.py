"""
Profile Metadata Repository
===========================

프로파일 메타데이터 저장소입니다.
메타데이터의 영속화와 조회를 담당합니다.

주요 기능:
- 메타데이터 CRUD 작업
- JSON 파일 기반 저장
- 메타데이터 검색 및 필터링
- 백업 및 복구
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from upbit_auto_trading.domain.profile_management.entities.profile_metadata import ProfileMetadata
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("ProfileMetadataRepository")

class ProfileMetadataRepository:
    """
    프로파일 메타데이터 저장소

    메타데이터를 JSON 파일로 영속화하고 관리합니다.
    """

    def __init__(self, metadata_dir: str = "config/metadata"):
        """
        Args:
            metadata_dir: 메타데이터 저장 디렉토리
        """
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.metadata_dir / "profile_metadata.json"

        # 메타데이터 캐시
        self._metadata_cache: Optional[Dict[str, Dict]] = None
        self._cache_last_modified: Optional[datetime] = None

        logger.info(f"ProfileMetadataRepository 초기화됨: {self.metadata_dir}")

    def save_metadata(self, metadata: ProfileMetadata) -> bool:
        """
        프로파일 메타데이터 저장

        Args:
            metadata: 저장할 메타데이터

        Returns:
            bool: 성공 여부
        """
        try:
            # 기존 메타데이터 로드
            all_metadata = self._load_all_metadata()

            # 새 메타데이터 추가/업데이트
            all_metadata[metadata.name] = metadata.to_dict()

            # 파일에 저장
            self._save_all_metadata(all_metadata)

            # 캐시 무효화
            self._invalidate_cache()

            logger.info(f"프로파일 메타데이터 저장됨: {metadata.name}")
            return True

        except Exception as e:
            logger.error(f"메타데이터 저장 실패 ({metadata.name}): {e}")
            return False

    def load_metadata(self, profile_name: str) -> Optional[ProfileMetadata]:
        """
        프로파일 메타데이터 로드

        Args:
            profile_name: 프로파일명

        Returns:
            Optional[ProfileMetadata]: 메타데이터 (없으면 None)
        """
        try:
            all_metadata = self._load_all_metadata()

            if profile_name in all_metadata:
                metadata_dict = all_metadata[profile_name]
                metadata = ProfileMetadata.from_dict(metadata_dict)
                logger.debug(f"메타데이터 로드됨: {profile_name}")
                return metadata
            else:
                logger.debug(f"메타데이터 없음: {profile_name}")
                return None

        except Exception as e:
            logger.error(f"메타데이터 로드 실패 ({profile_name}): {e}")
            return None

    def delete_metadata(self, profile_name: str) -> bool:
        """
        프로파일 메타데이터 삭제

        Args:
            profile_name: 프로파일명

        Returns:
            bool: 성공 여부
        """
        try:
            all_metadata = self._load_all_metadata()

            if profile_name in all_metadata:
                del all_metadata[profile_name]
                self._save_all_metadata(all_metadata)
                self._invalidate_cache()
                logger.info(f"메타데이터 삭제됨: {profile_name}")
                return True
            else:
                logger.warning(f"삭제할 메타데이터 없음: {profile_name}")
                return False

        except Exception as e:
            logger.error(f"메타데이터 삭제 실패 ({profile_name}): {e}")
            return False

    def list_all_metadata(self) -> List[ProfileMetadata]:
        """
        모든 프로파일 메타데이터 목록 반환

        Returns:
            List[ProfileMetadata]: 메타데이터 목록
        """
        try:
            all_metadata = self._load_all_metadata()

            metadata_list = []
            for profile_name, metadata_dict in all_metadata.items():
                try:
                    metadata = ProfileMetadata.from_dict(metadata_dict)
                    metadata_list.append(metadata)
                except Exception as e:
                    logger.warning(f"메타데이터 변환 실패 ({profile_name}): {e}")

            logger.debug(f"메타데이터 목록 조회됨: {len(metadata_list)}개")
            return metadata_list

        except Exception as e:
            logger.error(f"메타데이터 목록 조회 실패: {e}")
            return []

    def search_metadata(self, search_term: str = "",
                        profile_type: Optional[str] = None,
                        tags: Optional[List[str]] = None) -> List[ProfileMetadata]:
        """
        메타데이터 검색

        Args:
            search_term: 검색어 (이름, 설명에서 검색)
            profile_type: 프로파일 타입 필터
            tags: 태그 필터

        Returns:
            List[ProfileMetadata]: 검색 결과
        """
        try:
            all_metadata = self.list_all_metadata()

            filtered_metadata = []
            for metadata in all_metadata:
                # 검색어 필터
                if search_term and not metadata.matches_search(search_term):
                    continue

                # 타입 필터
                if profile_type and metadata.profile_type != profile_type:
                    continue

                # 태그 필터
                if tags:
                    has_all_tags = all(metadata.has_tag(tag) for tag in tags)
                    if not has_all_tags:
                        continue

                filtered_metadata.append(metadata)

            logger.debug(f"메타데이터 검색 완료: {len(filtered_metadata)}개 결과")
            return filtered_metadata

        except Exception as e:
            logger.error(f"메타데이터 검색 실패: {e}")
            return []

    def get_metadata_by_type(self, profile_type: str) -> List[ProfileMetadata]:
        """
        타입별 메타데이터 조회

        Args:
            profile_type: 프로파일 타입 ('built-in', 'custom')

        Returns:
            List[ProfileMetadata]: 해당 타입의 메타데이터 목록
        """
        return self.search_metadata(profile_type=profile_type)

    def get_recent_metadata(self, limit: int = 10) -> List[ProfileMetadata]:
        """
        최근 생성된 메타데이터 조회

        Args:
            limit: 조회할 개수

        Returns:
            List[ProfileMetadata]: 최근 메타데이터 목록
        """
        try:
            all_metadata = self.list_all_metadata()

            # 생성일자로 정렬 (최신순)
            sorted_metadata = sorted(
                all_metadata,
                key=lambda m: m.created_at,
                reverse=True
            )

            return sorted_metadata[:limit]

        except Exception as e:
            logger.error(f"최근 메타데이터 조회 실패: {e}")
            return []

    def create_backup(self) -> Optional[str]:
        """
        메타데이터 백업 생성

        Returns:
            Optional[str]: 백업 파일 경로 (실패 시 None)
        """
        try:
            if not self.metadata_file.exists():
                logger.warning("백업할 메타데이터 파일이 없습니다")
                return None

            # 백업 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"profile_metadata_backup_{timestamp}.json"
            backup_path = self.metadata_dir / backup_name

            # 백업 생성
            import shutil
            shutil.copy2(self.metadata_file, backup_path)

            logger.info(f"메타데이터 백업 생성됨: {backup_path}")
            return str(backup_path)

        except Exception as e:
            logger.error(f"메타데이터 백업 실패: {e}")
            return None

    def restore_from_backup(self, backup_path: str) -> bool:
        """
        백업에서 메타데이터 복원

        Args:
            backup_path: 백업 파일 경로

        Returns:
            bool: 성공 여부
        """
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                logger.error(f"백업 파일이 존재하지 않음: {backup_path}")
                return False

            # 백업 파일 검증
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            if not isinstance(backup_data, dict):
                logger.error("백업 파일 형식이 올바르지 않습니다")
                return False

            # 복원
            import shutil
            shutil.copy2(backup_file, self.metadata_file)
            self._invalidate_cache()

            logger.info(f"메타데이터 복원 완료: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"메타데이터 복원 실패: {e}")
            return False

    def get_statistics(self) -> Dict[str, int]:
        """
        메타데이터 통계 정보

        Returns:
            Dict[str, int]: 통계 정보
        """
        try:
            all_metadata = self.list_all_metadata()

            stats = {
                'total': len(all_metadata),
                'built_in': 0,
                'custom': 0,
                'with_description': 0,
                'with_tags': 0
            }

            for metadata in all_metadata:
                if metadata.is_built_in():
                    stats['built_in'] += 1
                elif metadata.is_custom():
                    stats['custom'] += 1

                if metadata.description.strip():
                    stats['with_description'] += 1

                if metadata.tags:
                    stats['with_tags'] += 1

            return stats

        except Exception as e:
            logger.error(f"통계 정보 생성 실패: {e}")
            return {}

    def _load_all_metadata(self) -> Dict[str, Dict]:
        """모든 메타데이터 로드 (캐시 지원)"""
        try:
            # 캐시 유효성 확인
            if (self._metadata_cache is not None and
                self._cache_last_modified is not None and
                self.metadata_file.exists()):

                file_mtime = datetime.fromtimestamp(self.metadata_file.stat().st_mtime)
                if file_mtime <= self._cache_last_modified:
                    logger.debug("메타데이터 캐시 사용")
                    return self._metadata_cache

            # 파일에서 로드
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if not isinstance(data, dict):
                    logger.warning("메타데이터 파일 형식 오류, 빈 딕셔너리로 초기화")
                    data = {}
            else:
                logger.debug("메타데이터 파일 없음, 빈 딕셔너리 생성")
                data = {}

            # 캐시 업데이트
            self._metadata_cache = data
            self._cache_last_modified = datetime.now()

            return data

        except Exception as e:
            logger.error(f"메타데이터 로드 실패: {e}")
            return {}

    def _save_all_metadata(self, metadata_dict: Dict[str, Dict]) -> None:
        """모든 메타데이터 저장"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, ensure_ascii=False, indent=2)

    def _invalidate_cache(self) -> None:
        """캐시 무효화"""
        self._metadata_cache = None
        self._cache_last_modified = None
