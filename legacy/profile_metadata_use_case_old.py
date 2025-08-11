"""
프로파일 메타데이터 관리 Use Case
"""
from typing import List, Dict, Optional
from datetime import datetime

from upbit_auto_trading.domain.profile_management.entities.profile_metadata import ProfileMetadata
from upbit_auto_trading.infrastructure.profile_storage.profile_metadata_repository import ProfileMetadataRepository
from upbit_auto_trading.infrastructure.logging import LoggerManager

logger = LoggerManager.get_logger(__name__)


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

    def get_profile_metadata(self, profile_id: str) -> Optional[ProfileMetadata]:
        """
        특정 프로파일 메타데이터 조회

        Args:
            profile_id: 프로파일 ID

        Returns:
            프로파일 메타데이터 또는 None
        """
        try:
            profile = self.metadata_repository.load_metadata(profile_id)
            if profile:
                logger.debug(f"프로파일 메타데이터 조회 완료: {profile_id}")
            else:
                logger.warning(f"프로파일을 찾을 수 없습니다: {profile_id}")

            return profile

        except Exception as e:
            logger.error(f"프로파일 메타데이터 조회 실패 ({profile_id}): {e}")
            return None

    def create_profile_metadata(self, profile_id: str, display_name: str,
                                file_path: str, description: str = "") -> bool:
        """
        새 프로파일 메타데이터 생성

        Args:
            profile_id: 프로파일 ID (name 필드로 사용)
            display_name: 표시 이름 (사용하지 않음)
            file_path: 프로파일 파일 경로
            description: 설명

        Returns:
            생성 성공 여부
        """
        try:
            # 중복 검사
            existing = self.metadata_repository.load_metadata(profile_id)
            if existing:
                logger.warning(f"이미 존재하는 프로파일 ID: {profile_id}")
                return False

            # 메타데이터 생성
            metadata = ProfileMetadata(
                name=profile_id,
                description=description,
                file_path=file_path
            )

            # 저장
            success = self.metadata_repository.save_metadata(metadata)

            if success:
                logger.info(f"프로파일 메타데이터 생성 완료: {profile_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"프로파일 메타데이터 생성 실패 ({profile_id}): {e}")
            return False

    def update_profile_metadata(self, profile_id: str,
                                display_name: Optional[str] = None,
                                description: Optional[str] = None) -> bool:
        """
        프로파일 메타데이터 업데이트

        Args:
            profile_id: 프로파일 ID
            display_name: 새 표시 이름 (선택적)
            description: 새 설명 (선택적)

        Returns:
            업데이트 성공 여부
        """
        try:
            # 기존 메타데이터 조회
            existing = self.metadata_repository.load_profile(profile_id)
            if not existing:
                logger.warning(f"존재하지 않는 프로파일: {profile_id}")
                return False

            # 업데이트할 값들 결정
            new_display_name = existing.display_name
            new_description = existing.description

            if display_name is not None:
                try:
                    new_display_name = ProfileDisplayName(display_name)
                except ValueError as e:
                    logger.error(f"잘못된 표시 이름: {e}")
                    return False

            if description is not None:
                new_description = description

            # 새 메타데이터 생성
            updated_metadata = ProfileMetadata(
                profile_id=existing.profile_id,
                display_name=new_display_name,
                file_path=existing.file_path,
                description=new_description,
                created_at=existing.created_at,
                last_accessed=existing.last_accessed
            )

            # 저장
            success = self.metadata_repository.save_profile(updated_metadata)

            if success:
                logger.info(f"프로파일 메타데이터 업데이트 완료: {profile_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"프로파일 메타데이터 업데이트 실패 ({profile_id}): {e}")
            return False

    def delete_profile_metadata(self, profile_id: str) -> bool:
        """
        프로파일 메타데이터 삭제

        Args:
            profile_id: 프로파일 ID

        Returns:
            삭제 성공 여부
        """
        try:
            success = self.metadata_repository.delete_profile(profile_id)

            if success:
                logger.info(f"프로파일 메타데이터 삭제 완료: {profile_id}")
                return True
            else:
                logger.warning(f"프로파일 메타데이터 삭제 실패: {profile_id}")
                return False

        except Exception as e:
            logger.error(f"프로파일 메타데이터 삭제 실패 ({profile_id}): {e}")
            return False

    def update_last_accessed(self, profile_id: str) -> bool:
        """
        프로파일 마지막 액세스 시간 업데이트

        Args:
            profile_id: 프로파일 ID

        Returns:
            업데이트 성공 여부
        """
        try:
            # 기존 메타데이터 조회
            existing = self.metadata_repository.load_profile(profile_id)
            if not existing:
                logger.warning(f"존재하지 않는 프로파일: {profile_id}")
                return False

            # 액세스 시간 업데이트
            existing.update_last_accessed()

            # 저장
            success = self.metadata_repository.save_profile(existing)

            if success:
                logger.debug(f"마지막 액세스 시간 업데이트 완료: {profile_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"마지막 액세스 시간 업데이트 실패 ({profile_id}): {e}")
            return False

    def get_recent_profiles(self, limit: int = 5) -> List[ProfileMetadata]:
        """
        최근 액세스한 프로파일 목록 조회

        Args:
            limit: 조회할 최대 개수

        Returns:
            최근 프로파일 목록
        """
        try:
            all_profiles = self.metadata_repository.load_all_profiles()

            # 마지막 액세스 시간 기준으로 정렬
            recent_profiles = sorted(
                all_profiles,
                key=lambda p: p.last_accessed,
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
            all_profiles = self.metadata_repository.load_all_profiles()
            keyword_lower = keyword.lower()

            # 표시 이름, 설명, 프로파일 ID에서 검색
            matched_profiles = []
            for profile in all_profiles:
                if (keyword_lower in profile.display_name.value.lower() or
                    keyword_lower in profile.description.lower() or
                    keyword_lower in profile.profile_id.lower()):
                    matched_profiles.append(profile)

            logger.debug(f"프로파일 검색 완료: '{keyword}' -> {len(matched_profiles)}개")
            return matched_profiles

        except Exception as e:
            logger.error(f"프로파일 검색 실패: {e}")
            return []

    def get_profile_statistics(self) -> Dict[str, int]:
        """
        프로파일 통계 정보 조회

        Returns:
            통계 정보 딕셔너리
        """
        try:
            all_profiles = self.metadata_repository.load_all_profiles()

            # 기본 통계
            total_count = len(all_profiles)

            # 최근 30일 내 액세스한 프로파일 수
            thirty_days_ago = datetime.now().timestamp() - (30 * 24 * 60 * 60)
            recent_count = sum(
                1 for profile in all_profiles
                if profile.last_accessed > thirty_days_ago
            )

            # 설명이 있는 프로파일 수
            with_description = sum(
                1 for profile in all_profiles
                if profile.description.strip()
            )

            statistics = {
                'total_profiles': total_count,
                'recent_profiles': recent_count,
                'profiles_with_description': with_description,
                'profiles_without_description': total_count - with_description
            }

            logger.debug(f"프로파일 통계 조회 완료: {statistics}")
            return statistics

        except Exception as e:
            logger.error(f"프로파일 통계 조회 실패: {e}")
            return {
                'total_profiles': 0,
                'recent_profiles': 0,
                'profiles_with_description': 0,
                'profiles_without_description': 0
            }
