"""
프로파일 메타데이터 관리 Use Case
"""
from typing import List, Dict, Optional

from upbit_auto_trading.domain.profile_management.entities.profile_metadata import ProfileMetadata
from upbit_auto_trading.infrastructure.profile_storage.profile_metadata_repository import ProfileMetadataRepository
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("ProfileMetadataUseCase")

class ProfileMetadataUseCase:
    """프로파일 메타데이터 관리 Use Case"""

    def __init__(self, metadata_repository: ProfileMetadataRepository):
        self.metadata_repository = metadata_repository

    def get_profile_list(self) -> List[ProfileMetadata]:
        """
        프로파일 목록 조회

        Returns:
            프로파일 메타데이터 목록
        """
        try:
            profiles = self.metadata_repository.list_all_metadata()
            logger.debug(f"프로파일 목록 조회 완료: {len(profiles)}개")
            return profiles

        except Exception as e:
            logger.error(f"프로파일 목록 조회 실패: {e}")
            return []

    def get_profile_metadata(self, profile_name: str) -> Optional[ProfileMetadata]:
        """
        특정 프로파일 메타데이터 조회

        Args:
            profile_name: 프로파일명

        Returns:
            프로파일 메타데이터 또는 None
        """
        try:
            profile = self.metadata_repository.load_metadata(profile_name)
            if profile:
                logger.debug(f"프로파일 메타데이터 조회 완료: {profile_name}")
            else:
                logger.warning(f"프로파일을 찾을 수 없습니다: {profile_name}")

            return profile

        except Exception as e:
            logger.error(f"프로파일 메타데이터 조회 실패 ({profile_name}): {e}")
            return None

    def create_profile_metadata(self, profile_name: str, file_path: str,
                                description: str = "") -> bool:
        """
        새 프로파일 메타데이터 생성

        Args:
            profile_name: 프로파일명
            file_path: 프로파일 파일 경로
            description: 설명

        Returns:
            생성 성공 여부
        """
        try:
            # 중복 검사
            existing = self.metadata_repository.load_metadata(profile_name)
            if existing:
                logger.warning(f"이미 존재하는 프로파일명: {profile_name}")
                return False

            # 메타데이터 생성
            metadata = ProfileMetadata(
                name=profile_name,
                description=description,
                file_path=file_path
            )

            # 저장
            success = self.metadata_repository.save_metadata(metadata)

            if success:
                logger.info(f"프로파일 메타데이터 생성 완료: {profile_name}")
                return True

            return False

        except Exception as e:
            logger.error(f"프로파일 메타데이터 생성 실패 ({profile_name}): {e}")
            return False

    def update_profile_metadata(self, profile_name: str,
                                description: Optional[str] = None,
                                file_path: Optional[str] = None) -> bool:
        """
        프로파일 메타데이터 업데이트

        Args:
            profile_name: 프로파일명
            description: 새 설명 (선택적)
            file_path: 새 파일 경로 (선택적)

        Returns:
            업데이트 성공 여부
        """
        try:
            # 기존 메타데이터 조회
            existing = self.metadata_repository.load_metadata(profile_name)
            if not existing:
                logger.warning(f"존재하지 않는 프로파일: {profile_name}")
                return False

            # 업데이트할 값들 결정
            new_description = description if description is not None else existing.description
            new_file_path = file_path if file_path is not None else existing.file_path

            # 새 메타데이터 생성 (기존 생성 시간 유지)
            updated_metadata = ProfileMetadata(
                name=existing.name,
                description=new_description,
                file_path=new_file_path,
                created_at=existing.created_at,
                created_from=existing.created_from,
                tags=existing.tags,
                profile_type=existing.profile_type
            )

            # 저장
            success = self.metadata_repository.save_metadata(updated_metadata)

            if success:
                logger.info(f"프로파일 메타데이터 업데이트 완료: {profile_name}")
                return True

            return False

        except Exception as e:
            logger.error(f"프로파일 메타데이터 업데이트 실패 ({profile_name}): {e}")
            return False

    def delete_profile_metadata(self, profile_name: str) -> bool:
        """
        프로파일 메타데이터 삭제

        Args:
            profile_name: 프로파일명

        Returns:
            삭제 성공 여부
        """
        try:
            success = self.metadata_repository.delete_metadata(profile_name)

            if success:
                logger.info(f"프로파일 메타데이터 삭제 완료: {profile_name}")
                return True
            else:
                logger.warning(f"프로파일 메타데이터 삭제 실패: {profile_name}")
                return False

        except Exception as e:
            logger.error(f"프로파일 메타데이터 삭제 실패 ({profile_name}): {e}")
            return False

    def get_recent_profiles(self, limit: int = 5) -> List[ProfileMetadata]:
        """
        최근 생성된 프로파일 목록 조회

        Args:
            limit: 조회할 최대 개수

        Returns:
            최근 프로파일 목록
        """
        try:
            all_profiles = self.metadata_repository.list_all_metadata()

            # 생성 시간 기준으로 정렬
            recent_profiles = sorted(
                all_profiles,
                key=lambda p: p.created_at,
                reverse=True
            )

            # 제한된 개수만 반환
            result = recent_profiles[:limit]

            logger.debug(f"최근 프로파일 {len(result)}개 조회 완료")
            return result

        except Exception as e:
            logger.error(f"최근 프로파일 조회 실패: {e}")
            return []

    def search_profiles(self, keyword: str) -> List[ProfileMetadata]:
        """
        프로파일 검색

        Args:
            keyword: 검색 키워드

        Returns:
            검색된 프로파일 목록
        """
        try:
            all_profiles = self.metadata_repository.list_all_metadata()
            keyword_lower = keyword.lower()

            # 프로파일명, 설명에서 검색
            matched_profiles = []
            for profile in all_profiles:
                if (keyword_lower in profile.name.lower()
                        or keyword_lower in profile.description.lower()):
                    matched_profiles.append(profile)

            logger.debug(f"프로파일 검색 완료: '{keyword}' -> {len(matched_profiles)}개")
            return matched_profiles

        except Exception as e:
            logger.error(f"프로파일 검색 실패: {e}")
            return []

    def get_profiles_by_type(self, profile_type: str) -> List[ProfileMetadata]:
        """
        타입별 프로파일 조회

        Args:
            profile_type: 프로파일 타입 ('built-in', 'custom')

        Returns:
            해당 타입의 프로파일 목록
        """
        try:
            profiles = self.metadata_repository.get_metadata_by_type(profile_type)
            logger.debug(f"타입별 프로파일 조회 완료 ({profile_type}): {len(profiles)}개")
            return profiles

        except Exception as e:
            logger.error(f"타입별 프로파일 조회 실패 ({profile_type}): {e}")
            return []

    def get_profile_statistics(self) -> Dict[str, int]:
        """
        프로파일 통계 정보 조회

        Returns:
            통계 정보 딕셔너리
        """
        try:
            statistics = self.metadata_repository.get_statistics()
            logger.debug(f"프로파일 통계 조회 완료: {statistics}")
            return statistics

        except Exception as e:
            logger.error(f"프로파일 통계 조회 실패: {e}")
            return {
                'total_profiles': 0,
                'built_in_profiles': 0,
                'custom_profiles': 0,
                'profiles_with_description': 0
            }

    def add_tag_to_profile(self, profile_name: str, tag: str) -> bool:
        """
        프로파일에 태그 추가

        Args:
            profile_name: 프로파일명
            tag: 추가할 태그

        Returns:
            추가 성공 여부
        """
        try:
            # 기존 메타데이터 조회
            existing = self.metadata_repository.load_metadata(profile_name)
            if not existing:
                logger.warning(f"존재하지 않는 프로파일: {profile_name}")
                return False

            # 태그 추가 (중복 방지)
            if tag.strip().lower() not in [t.lower() for t in existing.tags]:
                existing.tags.append(tag.strip())

                # 저장
                success = self.metadata_repository.save_metadata(existing)

                if success:
                    logger.info(f"태그 추가 완료: {profile_name} -> {tag}")
                    return True
            else:
                logger.debug(f"이미 존재하는 태그: {profile_name} -> {tag}")
                return True

            return False

        except Exception as e:
            logger.error(f"태그 추가 실패 ({profile_name}, {tag}): {e}")
            return False

    def remove_tag_from_profile(self, profile_name: str, tag: str) -> bool:
        """
        프로파일에서 태그 제거

        Args:
            profile_name: 프로파일명
            tag: 제거할 태그

        Returns:
            제거 성공 여부
        """
        try:
            # 기존 메타데이터 조회
            existing = self.metadata_repository.load_metadata(profile_name)
            if not existing:
                logger.warning(f"존재하지 않는 프로파일: {profile_name}")
                return False

            # 태그 제거
            tag_lower = tag.strip().lower()
            original_count = len(existing.tags)
            existing.tags = [t for t in existing.tags if t.lower() != tag_lower]

            if len(existing.tags) < original_count:
                # 저장
                success = self.metadata_repository.save_metadata(existing)

                if success:
                    logger.info(f"태그 제거 완료: {profile_name} -> {tag}")
                    return True
            else:
                logger.debug(f"존재하지 않는 태그: {profile_name} -> {tag}")
                return True

            return False

        except Exception as e:
            logger.error(f"태그 제거 실패 ({profile_name}, {tag}): {e}")
            return False
