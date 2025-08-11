"""
Profile Metadata Service
========================

프로파일 메타데이터 관리를 위한 Application Service
DDD 아키텍처의 Application Layer에 위치하여 메타데이터 관련
비즈니스 로직을 캡슐화

Features:
- 메타데이터 YAML 구조 관리 (Task 4.2.1)
- 콤보박스 표시명 시스템 (Task 4.2.2)
- 메타데이터 편집 다이얼로그 연동 (Task 4.2.3)
- 프로파일 분류 및 태그 관리

Author: AI Assistant
Created: 2025-08-11
Refactored from: environment_profile_presenter.py (er-subTASK 01)
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import yaml

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.profile_storage.profile_metadata_repository import ProfileMetadataRepository
from upbit_auto_trading.infrastructure.yaml_processing.yaml_parser import YamlParser
from upbit_auto_trading.ui.desktop.screens.settings.environment_profile.dialogs.profile_metadata import ProfileMetadata


logger = create_component_logger("ProfileMetadataService")


class ProfileMetadataService:
    """
    프로파일 메타데이터 관리 Application Service

    DDD Application Layer의 서비스로써 메타데이터 관련
    모든 비즈니스 로직을 캡슐화하여 제공합니다.

    Infrastructure Services:
    - ProfileMetadataRepository: 메타데이터 영속성
    - YamlParser: YAML 파싱 및 검증
    """

    def __init__(self):
        """ProfileMetadataService 초기화"""
        logger.info("🏷️ ProfileMetadataService 초기화")

        # Infrastructure Services 주입
        self.metadata_repo = ProfileMetadataRepository()
        self.yaml_parser = YamlParser()

        # 설정 디렉토리 경로 설정
        self.config_dir = Path("config")

        # 커스텀 프로파일 디렉토리 설정 (필요시 생성)
        self.custom_profiles_dir = self.config_dir / "custom_profiles"
        self.custom_profiles_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir = Path("config")

        logger.debug("✅ Infrastructure 서비스 주입 완료")

    # ===============================================================================
    # === Task 4.2.1: 메타데이터 YAML 구조 관리 메서드 ===
    # ===============================================================================

    def list_all_profiles(self) -> List[str]:
        """모든 사용 가능한 프로파일 목록 반환

        Returns:
            List[str]: 프로파일명 리스트 (기본 환경 + 커스텀)
        """
        try:
            profiles = []

            # 기본 환경 프로파일들 (확장된 목록)
            basic_profiles = ['development', 'production', 'testing', 'staging', 'debug', 'demo']
            for profile in basic_profiles:
                config_path = self.config_dir / f"config.{profile}.yaml"
                if config_path.exists():
                    profiles.append(profile)

            # 커스텀 프로파일들 (Infrastructure Repository 활용)
            custom_metadata = self.metadata_repo.list_all_metadata()
            for metadata in custom_metadata:
                if metadata.profile_type == 'custom':
                    profiles.append(f"custom_{metadata.name}")

            logger.info(f"📋 프로파일 목록 조회 완료: {len(profiles)}개")
            return profiles

        except Exception as e:
            logger.error(f"❌ 프로파일 목록 조회 실패: {e}")
            return ['development', 'production', 'testing']  # 최소 기본값

    def get_available_profiles(self) -> List[str]:
        """사용 가능한 프로파일 목록 조회 (alias for list_all_profiles)"""
        return self.list_all_profiles()

    def format_profile_combo_item(self, profile_name: str) -> str:
        """콤보박스 표시용 프로파일 아이템 포맷팅

        Args:
            profile_name: 프로파일명

        Returns:
            str: 표시용 텍스트 (예: "Development Environment (기본)")
        """
        try:
            if profile_name in ['development', 'production', 'testing', 'staging', 'debug', 'demo']:
                # 기본 환경 프로파일 (확장된 목록)
                display_names = {
                    'development': 'Development Environment (개발)',
                    'production': 'Production Environment (운영)',
                    'testing': 'Testing Environment (테스트)',
                    'staging': 'Staging Environment (스테이징)',
                    'debug': 'Debug Environment (디버그)',
                    'demo': 'Demo Environment (데모)'
                }
                return display_names.get(profile_name, profile_name)

            elif profile_name.startswith('custom_'):
                # 커스텀 프로파일
                actual_name = profile_name.replace('custom_', '')
                metadata = self.metadata_repo.load_metadata(actual_name)
                if metadata and metadata.description:
                    return f"{metadata.description} (커스텀)"
                else:
                    return f"{actual_name} (커스텀)"

            else:
                return profile_name

        except Exception as e:
            logger.error(f"❌ 프로파일 아이템 포맷팅 실패: {e}")
            return profile_name

    def load_profile_metadata(self, profile_name: str) -> Optional[ProfileMetadata]:
        """프로파일의 메타데이터 로드"""
        try:
            # 메타데이터 파일 경로 결정
            config_file = self._get_profile_config_path(profile_name)
            logger.info(f"🔍 메타데이터 파일 경로 확인: {config_file}")

            if not config_file.exists():
                logger.debug(f"📄 메타데이터 파일 없음: {config_file}")
                return None

            # YAML 파일에서 메타데이터 추출
            with open(config_file, 'r', encoding='utf-8') as f:
                yaml_content = f.read()

            logger.debug(f"📄 YAML 내용 로드됨 (길이: {len(yaml_content)})")
            logger.debug(f"📄 YAML 내용 미리보기: {yaml_content[:200]}...")

            metadata = ProfileMetadata.from_yaml_content(yaml_content)
            logger.info(f"📖 메타데이터 로드 성공: {profile_name}")
            logger.debug(f"    → name='{metadata.name}', desc='{metadata.description}'")
            logger.debug(f"    → type='{metadata.profile_type}', tags={metadata.tags}")
            return metadata

        except Exception as e:
            logger.warning(f"⚠️ 메타데이터 로드 실패 ({profile_name}): {e}")
            return None

    def save_profile_metadata(self, profile_name: str, metadata: ProfileMetadata) -> bool:
        """프로파일의 메타데이터 저장"""
        try:
            # 기존 YAML 내용 로드
            config_file = self._get_profile_config_path(profile_name)
            existing_yaml = ""
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    existing_yaml = f.read()

            # 메타데이터 YAML 생성
            metadata_yaml = metadata.to_yaml_string()

            # 기존 YAML에 메타데이터가 있으면 교체, 없으면 맨 위에 추가
            if 'profile_info:' in existing_yaml:
                # 기존 메타데이터 교체
                import re
                pattern = r'profile_info:.*?(?=\n[a-zA-Z]|\Z)'
                new_yaml = re.sub(pattern, metadata_yaml.strip(), existing_yaml, flags=re.DOTALL)
            else:
                # 새 메타데이터 추가
                new_yaml = metadata_yaml + "\n" + existing_yaml

            # 파일에 저장
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(new_yaml)

            logger.info(f"💾 메타데이터 저장 완료: {profile_name}")
            return True

        except Exception as e:
            logger.error(f"❌ 메타데이터 저장 실패 ({profile_name}): {e}")
            return False

    def create_default_metadata(self, profile_name: str, created_from: str = "") -> ProfileMetadata:
        """기본 메타데이터 생성"""
        try:
            # 프로파일명 기반 기본 정보 생성
            name = self._generate_default_profile_name(profile_name)
            description = self._generate_default_description(profile_name, created_from)

            metadata = ProfileMetadata(
                name=name,
                description=description,
                created_from=created_from
            )

            # 기본 태그 추가
            if created_from:
                metadata.add_tag("custom")
            else:
                metadata.add_tag("system")

            logger.debug(f"🆕 기본 메타데이터 생성: {profile_name}")
            return metadata

        except Exception as e:
            logger.warning(f"⚠️ 기본 메타데이터 생성 실패: {e}")
            return ProfileMetadata()

    def update_profile_metadata(self, profile_name: str, metadata: ProfileMetadata) -> bool:
        """프로파일 메타데이터 업데이트"""
        try:
            # 메타데이터 유효성 검증
            is_valid, error_msg = metadata.validate()
            if not is_valid:
                logger.warning(f"⚠️ 메타데이터 유효성 검증 실패: {error_msg}")
                return False

            # 메타데이터 저장
            success = self.save_profile_metadata(profile_name, metadata)
            if success:
                logger.info(f"✅ 메타데이터 업데이트 완료: {profile_name}")

            return success

        except Exception as e:
            logger.error(f"❌ 메타데이터 업데이트 실패 ({profile_name}): {e}")
            return False

    def ensure_profile_has_metadata(self, profile_name: str) -> bool:
        """프로파일에 메타데이터가 있는지 확인하고 없으면 생성"""
        try:
            metadata = self.load_profile_metadata(profile_name)
            if metadata is None:
                # 메타데이터가 없으면 기본 메타데이터 생성
                default_metadata = self.create_default_metadata(profile_name)
                return self.save_profile_metadata(profile_name, default_metadata)
            return True

        except Exception as e:
            logger.warning(f"⚠️ 메타데이터 확인/생성 실패 ({profile_name}): {e}")
            return False

    # ===============================================================================
    # === Task 4.2.2: 콤보박스 표시명 시스템 메서드 ===
    # ===============================================================================

    def get_profile_display_name(self, profile_name: str) -> str:
        """프로파일의 표시명 조회 (Task 4.2.2용 메서드)"""
        try:
            metadata = self.load_profile_metadata(profile_name)
            if metadata:
                return metadata.generate_display_name(profile_name)
            else:
                return profile_name

        except Exception as e:
            logger.warning(f"⚠️ 표시명 조회 실패 ({profile_name}): {e}")
            return profile_name

    def format_profile_combo_item(self, profile_name: str, metadata: Optional[ProfileMetadata] = None) -> str:
        """프로파일 콤보박스 아이템 포맷팅"""
        try:
            if metadata is None:
                metadata = self.load_profile_metadata(profile_name)

            if metadata and metadata.name:
                # "Custom Dev Settings (커스텀)" 형식
                return f"{metadata.name} ({profile_name})"
            else:
                # 메타데이터가 없으면 기본 이름 사용
                return self._get_default_display_name(profile_name)

        except Exception as e:
            logger.warning(f"⚠️ 콤보박스 아이템 포맷팅 실패 ({profile_name}): {e}")
            return profile_name

    def update_profile_combo_display(self, combo_widget) -> None:
        """프로파일 콤보박스 표시명 업데이트"""
        try:
            if combo_widget is None:
                logger.warning("⚠️ 콤보박스 위젯이 None입니다")
                return

            # 현재 선택된 아이템 보존
            current_profile = None
            current_index = combo_widget.currentIndex()
            if current_index >= 0:
                current_data = combo_widget.itemData(current_index)
                if current_data:
                    current_profile = current_data

            # 콤보박스 클리어
            combo_widget.clear()

            # 사용 가능한 프로파일 목록 조회
            available_profiles = self.get_available_profiles()

            # 각 프로파일에 대해 표시명 설정
            for profile_name in available_profiles:
                try:
                    # 메타데이터 로드
                    metadata = self.load_profile_metadata(profile_name)

                    # 표시명 생성
                    display_name = self.format_profile_combo_item(profile_name, metadata)

                    # 콤보박스에 추가 (profile_name을 data로 저장)
                    combo_widget.addItem(display_name, profile_name)

                    logger.debug(f"📋 콤보박스 아이템 추가: {display_name}")

                except Exception as e:
                    logger.warning(f"⚠️ 프로파일 아이템 추가 실패 ({profile_name}): {e}")
                    # 실패 시 기본 이름으로 추가
                    combo_widget.addItem(profile_name, profile_name)

            # 이전 선택 복원
            if current_profile:
                self._restore_combo_selection(combo_widget, current_profile)

            logger.info(f"✅ 프로파일 콤보박스 표시명 업데이트 완료: {len(available_profiles)}개")

        except Exception as e:
            logger.error(f"❌ 프로파일 콤보박스 업데이트 실패: {e}")

    def get_available_profiles(self) -> list:
        """사용 가능한 프로파일 목록 조회"""
        try:
            config_dir = Path("config")
            if not config_dir.exists():
                logger.warning(f"⚠️ 설정 디렉토리 없음: {config_dir}")
                return []

            profiles = []
            for config_file in config_dir.glob("config.*.yaml"):
                try:
                    # config.development.yaml -> development
                    profile_name = config_file.stem.replace("config.", "")
                    if profile_name and profile_name != "config":
                        profiles.append(profile_name)
                except Exception as e:
                    logger.warning(f"⚠️ 프로파일명 추출 실패 ({config_file}): {e}")

            # 기본 정렬: 시스템 프로파일 먼저, 커스텀 프로파일 나중
            system_profiles = ['development', 'production', 'testing', 'staging']
            sorted_profiles = []

            # 시스템 프로파일 추가 (순서 유지)
            for sys_profile in system_profiles:
                if sys_profile in profiles:
                    sorted_profiles.append(sys_profile)
                    profiles.remove(sys_profile)

            # 나머지 커스텀 프로파일 추가 (알파벳 순)
            sorted_profiles.extend(sorted(profiles))

            logger.debug(f"📋 사용 가능한 프로파일: {sorted_profiles}")
            return sorted_profiles

        except Exception as e:
            logger.error(f"❌ 프로파일 목록 조회 실패: {e}")
            return []

    def is_custom_profile_by_name(self, profile_name: str) -> bool:
        """프로파일명으로 커스텀 프로파일 여부 확인"""
        try:
            # 시스템 기본 프로파일 목록
            system_profiles = ['development', 'production', 'testing', 'staging']
            return profile_name not in system_profiles

        except Exception as e:
            logger.warning(f"⚠️ 커스텀 프로파일 확인 실패: {e}")
            return False

    # ===============================================================================
    # === Task 4.2.3: 메타데이터 편집 다이얼로그 연동 메서드 ===
    # ===============================================================================

    def show_metadata_dialog(self, profile_name: str, parent_widget=None) -> bool:
        """메타데이터 편집 다이얼로그 표시"""
        try:
            from upbit_auto_trading.ui.desktop.screens.settings.environment_profile.dialogs.profile_metadata_dialog import (
                ProfileMetadataDialog
            )

            # 현재 메타데이터 로드
            current_metadata = self.load_profile_metadata(profile_name)

            # 다이얼로그 생성
            dialog = ProfileMetadataDialog(profile_name, current_metadata, parent_widget)

            # 메타데이터 적용 시그널 연결
            dialog.metadata_applied.connect(self._on_metadata_applied)

            # 다이얼로그 표시
            result = dialog.exec()

            logger.info(f"📝 메타데이터 다이얼로그 결과: {profile_name} - {'적용' if result == dialog.DialogCode.Accepted else '취소'}")
            return result == dialog.DialogCode.Accepted

        except Exception as e:
            logger.error(f"❌ 메타데이터 다이얼로그 표시 실패: {e}")
            return False

    def get_profile_metadata_summary(self, profile_name: str) -> dict:
        """프로파일 메타데이터 요약 정보 반환"""
        try:
            metadata = self.load_profile_metadata(profile_name)
            if metadata:
                return {
                    'display_name': metadata.name or profile_name,
                    'description': metadata.description,
                    'is_custom': metadata.is_custom_profile(),
                    'tag_count': len(metadata.tags),
                    'tags': metadata.tags,
                    'created_at': metadata.created_at,
                    'created_from': metadata.created_from
                }
            else:
                return {
                    'display_name': profile_name,
                    'description': '',
                    'is_custom': self.is_custom_profile_by_name(profile_name),
                    'tag_count': 0,
                    'tags': [],
                    'created_at': '',
                    'created_from': ''
                }

        except Exception as e:
            logger.error(f"❌ 메타데이터 요약 생성 실패: {e}")
            return {
                'display_name': profile_name,
                'description': 'Error loading metadata',
                'is_custom': False,
                'tag_count': 0,
                'tags': [],
                'created_at': '',
                'created_from': ''
            }

    # ===============================================================================
    # === 헬퍼 메서드 ===
    # ===============================================================================

    def _get_profile_config_path(self, profile_name: str) -> Path:
        """프로파일 설정 파일 경로 반환"""
        config_dir = Path("config")
        return config_dir / f"config.{profile_name}.yaml"

    def _generate_default_profile_name(self, profile_name: str) -> str:
        """프로파일명 기반 기본 표시명 생성"""
        name_mappings = {
            'development': '개발 환경',
            'production': '운영 환경',
            'testing': '테스트 환경',
            'staging': '스테이징 환경'
        }
        return name_mappings.get(profile_name, profile_name.title() + " 환경")

    def _generate_default_description(self, profile_name: str, created_from: str = "") -> str:
        """프로파일 기본 설명 생성"""
        if created_from:
            return f"{created_from} 환경을 기반으로 생성된 커스텀 설정"
        else:
            desc_mappings = {
                'development': '개발 및 디버깅용 설정',
                'production': '실제 운영용 최적화 설정',
                'testing': '테스트 및 검증용 설정',
                'staging': '배포 전 검증용 설정'
            }
            return desc_mappings.get(profile_name, f"{profile_name} 환경 설정")

    def _get_default_display_name(self, profile_name: str) -> str:
        """기본 표시명 반환"""
        display_mappings = {
            'development': '개발 환경 (development)',
            'production': '운영 환경 (production)',
            'testing': '테스트 환경 (testing)',
            'staging': '스테이징 환경 (staging)'
        }
        return display_mappings.get(profile_name, f"{profile_name.title()} ({profile_name})")

    def _restore_combo_selection(self, combo_widget, target_profile: str) -> None:
        """콤보박스 선택 복원"""
        try:
            for i in range(combo_widget.count()):
                item_data = combo_widget.itemData(i)
                if item_data == target_profile:
                    combo_widget.setCurrentIndex(i)
                    logger.debug(f"🔄 콤보박스 선택 복원: {target_profile}")
                    return

            logger.debug(f"📝 콤보박스 선택 복원 실패: {target_profile} 없음")

        except Exception as e:
            logger.warning(f"⚠️ 콤보박스 선택 복원 실패: {e}")

    def _on_metadata_applied(self, profile_name: str, metadata: ProfileMetadata):
        """메타데이터 적용 이벤트 핸들러"""
        try:
            # 메타데이터 저장
            success = self.save_profile_metadata(profile_name, metadata)

            if success:
                logger.info(f"✅ 메타데이터 적용 완료: {profile_name}")
                # 필요시 추가 처리 (예: 시그널 발생)
            else:
                logger.error(f"❌ 메타데이터 저장 실패: {profile_name}")

        except Exception as e:
            logger.error(f"❌ 메타데이터 적용 핸들러 실패: {e}")
