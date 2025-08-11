"""
Configuration Profile Service
YAML 프로파일 기반 환경 설정 관리 서비스
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger


logger = create_component_logger("ConfigProfileService")


@dataclass
class ProfileSwitchResult:
    """프로파일 스위칭 결과"""
    success: bool
    profile_name: str
    env_vars_applied: Dict[str, str]
    errors: List[str]


class ConfigProfileLoader:
    """YAML 설정 파일 로더"""

    def __init__(self, config_dir: str = "config"):
        """
        Args:
            config_dir: 설정 파일 디렉토리 경로
        """
        self.config_dir = Path(config_dir)
        self.base_config_path = self.config_dir / "config.yaml"
        logger.info(f"ConfigProfileLoader 초기화 - 설정 디렉토리: {self.config_dir}")

    def load_profile(self, profile_name: str) -> Dict[str, Any]:
        """지정된 프로파일 설정 로드

        Args:
            profile_name: 프로파일 이름 (development, production, testing)

        Returns:
            Dict[str, Any]: 로드된 설정 데이터

        Raises:
            FileNotFoundError: 프로파일 파일이 없는 경우
            yaml.YAMLError: YAML 파싱 오류
        """
        profile_path = self.config_dir / f"config.{profile_name}.yaml"

        if not profile_path.exists():
            error_msg = f"프로파일 파일이 존재하지 않습니다: {profile_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            logger.info(f"✅ 프로파일 로드 성공: {profile_name}")
            logger.debug(f"로드된 설정 키: {list(config_data.keys())}")
            return config_data
        except yaml.YAMLError as e:
            error_msg = f"YAML 파싱 오류 ({profile_name}): {e}"
            logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"프로파일 로드 실패 ({profile_name}): {e}"
            logger.error(error_msg)
            raise

    def get_available_profiles(self) -> List[str]:
        """사용 가능한 프로파일 목록 반환"""
        profiles = []

        for config_file in self.config_dir.glob("config.*.yaml"):
            # config.development.yaml → development
            profile_name = config_file.stem.replace("config.", "")
            profiles.append(profile_name)

        logger.debug(f"발견된 프로파일: {profiles}")
        return sorted(profiles)


class ProfileSwitcher:
    """프로파일 기반 환경 설정 스위처"""

    def __init__(self, config_loader: ConfigProfileLoader = None):
        """
        Args:
            config_loader: 설정 로더 (테스트용 주입 가능)
        """
        self.config_loader = config_loader or ConfigProfileLoader()
        self.current_profile: Optional[str] = None
        logger.info("ProfileSwitcher 초기화 완료")

    def switch_to_profile(self, profile_name: str) -> ProfileSwitchResult:
        """지정된 프로파일로 스위칭

        Args:
            profile_name: 전환할 프로파일 이름

        Returns:
            ProfileSwitchResult: 스위칭 결과
        """
        logger.info(f"🔄 프로파일 스위칭 시작: {profile_name}")
        errors = []
        env_vars_applied = {}

        try:
            # 1. 프로파일 설정 로드
            config_data = self.config_loader.load_profile(profile_name)

            # 2. 로깅 설정을 환경변수로 매핑
            if 'logging' in config_data:
                logging_env_vars = self._map_config_to_env_vars(config_data['logging'])

                # 3. 환경변수 일괄 적용
                self._apply_env_vars_bulk(logging_env_vars)
                env_vars_applied.update(logging_env_vars)

                logger.info(f"✅ 로깅 환경변수 {len(logging_env_vars)}개 적용 완료")

            # 4. 현재 프로파일 업데이트
            self.current_profile = profile_name

            logger.info(f"🎯 프로파일 스위칭 완료: {profile_name}")
            return ProfileSwitchResult(
                success=True,
                profile_name=profile_name,
                env_vars_applied=env_vars_applied,
                errors=errors
            )

        except Exception as e:
            error_msg = f"프로파일 스위칭 실패 ({profile_name}): {e}"
            logger.error(error_msg)
            errors.append(error_msg)

            return ProfileSwitchResult(
                success=False,
                profile_name=profile_name,
                env_vars_applied=env_vars_applied,
                errors=errors
            )

    def _map_config_to_env_vars(self, logging_config: Dict[str, Any]) -> Dict[str, str]:
        """로깅 설정을 환경변수로 매핑

        Args:
            logging_config: YAML 로깅 설정

        Returns:
            Dict[str, str]: 환경변수 매핑 결과
        """
        env_mapping = {
            'UPBIT_LOG_LEVEL': str(logging_config.get('level', 'INFO')).upper(),
            'UPBIT_LOG_CONTEXT': str(logging_config.get('context', 'development')).lower(),
            'UPBIT_LOG_SCOPE': str(logging_config.get('scope', 'normal')).lower(),
            'UPBIT_CONSOLE_OUTPUT': 'true' if logging_config.get('console_enabled', False) else 'false',
            'UPBIT_COMPONENT_FOCUS': str(logging_config.get('component_focus', '')),
            'UPBIT_LLM_BRIEFING_ENABLED': 'true' if logging_config.get('llm_briefing_enabled', False) else 'false',
            'UPBIT_FEATURE_DEVELOPMENT': str(logging_config.get('feature_development', '')),
            'UPBIT_PERFORMANCE_MONITORING': 'true' if logging_config.get('performance_monitoring', False) else 'false',
            'UPBIT_BRIEFING_UPDATE_INTERVAL': str(logging_config.get('briefing_update_interval', 30))
        }

        logger.debug(f"설정 → 환경변수 매핑 완료: {len(env_mapping)}개")
        return env_mapping

    def _apply_env_vars_bulk(self, env_vars: Dict[str, str]) -> None:
        """환경변수 일괄 적용

        Args:
            env_vars: 적용할 환경변수 딕셔너리
        """
        for key, value in env_vars.items():
            old_value = os.getenv(key)
            os.environ[key] = value

            if old_value != value:
                logger.debug(f"환경변수 변경: {key} = '{value}' (이전: '{old_value}')")

    # ============================================================================
    # Task 5.2 호환성 메서드들 - ProfileSwitcher에 추가
    # ============================================================================

    def get_current_environment(self) -> str:
        """현재 활성 환경 조회

        Returns:
            str: 현재 환경명 또는 기본값
        """
        if self.current_profile:
            return self.current_profile

        # 환경변수에서 현재 환경 추론
        log_context = os.getenv('UPBIT_LOG_CONTEXT', 'development')
        return log_context

    def switch_profile(self, profile_name: str) -> ProfileSwitchResult:
        """프로파일 전환 (Task 5.2 호환성 alias)

        Args:
            profile_name: 전환할 프로파일명

        Returns:
            ProfileSwitchResult: 전환 결과
        """
        return self.switch_to_profile(profile_name)

    def get_current_ui_state(self) -> Dict[str, Any]:
        """현재 환경변수 기반 UI 상태 반환

        Returns:
            Dict[str, Any]: UI 표시용 상태 정보
        """
        return {
            'log_level': os.getenv('UPBIT_LOG_LEVEL', 'INFO'),
            'log_context': os.getenv('UPBIT_LOG_CONTEXT', 'development'),
            'log_scope': os.getenv('UPBIT_LOG_SCOPE', 'normal'),
            'console_output': os.getenv('UPBIT_CONSOLE_OUTPUT', 'false').lower() == 'true',
            'component_focus': os.getenv('UPBIT_COMPONENT_FOCUS', ''),
            'current_profile': self.current_profile or 'none'
        }


class ConfigProfileService:
    """Configuration Profile Management Service

    환경&로깅 탭에서 사용할 프로파일 스위칭 통합 서비스
    - 기본 프로파일 (development, production, testing)
    - 사용자 커스텀 프로파일 저장/로드
    """

    def __init__(self):
        """서비스 초기화"""
        self.profile_switcher = ProfileSwitcher()
        self.custom_profiles_dir = Path("config/custom")
        self.custom_profiles_dir.mkdir(parents=True, exist_ok=True)
        logger.info("ConfigProfileService 초기화 완료")

    def get_available_profiles(self) -> List[str]:
        """사용 가능한 프로파일 목록 (기본 + 커스텀)"""
        # 기본 프로파일
        basic_profiles = self.profile_switcher.config_loader.get_available_profiles()

        # 커스텀 프로파일
        custom_profiles = []
        if self.custom_profiles_dir.exists():
            for custom_file in self.custom_profiles_dir.glob("*.yaml"):
                profile_name = f"custom_{custom_file.stem}"
                custom_profiles.append(profile_name)

        all_profiles = basic_profiles + custom_profiles
        logger.debug(f"사용 가능한 프로파일: 기본 {len(basic_profiles)}개, 커스텀 {len(custom_profiles)}개")
        return sorted(all_profiles)

    def switch_profile(self, profile_name: str) -> ProfileSwitchResult:
        """프로파일 스위칭 (기본 + 커스텀 지원)"""
        if profile_name.startswith("custom_"):
            return self._switch_custom_profile(profile_name)
        else:
            return self.profile_switcher.switch_to_profile(profile_name)

    def _switch_custom_profile(self, profile_name: str) -> ProfileSwitchResult:
        """커스텀 프로파일 스위칭"""
        logger.info(f"🔄 커스텀 프로파일 스위칭: {profile_name}")

        try:
            # custom_myprofile → myprofile
            actual_name = profile_name.replace("custom_", "")
            custom_path = self.custom_profiles_dir / f"{actual_name}.yaml"

            if not custom_path.exists():
                error_msg = f"커스텀 프로파일 파일이 없습니다: {custom_path}"
                logger.error(error_msg)
                return ProfileSwitchResult(
                    success=False,
                    profile_name=profile_name,
                    env_vars_applied={},
                    errors=[error_msg]
                )

            # YAML 로드
            with open(custom_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            # 환경변수 적용
            env_vars_applied = {}
            if 'logging' in config_data:
                logging_env_vars = self.profile_switcher._map_config_to_env_vars(config_data['logging'])
                self.profile_switcher._apply_env_vars_bulk(logging_env_vars)
                env_vars_applied.update(logging_env_vars)

            self.profile_switcher.current_profile = profile_name

            logger.info(f"✅ 커스텀 프로파일 스위칭 완료: {profile_name}")
            return ProfileSwitchResult(
                success=True,
                profile_name=profile_name,
                env_vars_applied=env_vars_applied,
                errors=[]
            )

        except Exception as e:
            error_msg = f"커스텀 프로파일 스위칭 실패 ({profile_name}): {e}"
            logger.error(error_msg)
            return ProfileSwitchResult(
                success=False,
                profile_name=profile_name,
                env_vars_applied={},
                errors=[error_msg]
            )

    def save_current_as_profile(self, profile_name: str, description: str = "") -> bool:
        """현재 환경변수 상태를 커스텀 프로파일로 저장

        Args:
            profile_name: 저장할 프로파일명 (영문, 숫자, _ 만 허용)
            description: 프로파일 설명

        Returns:
            bool: 저장 성공 여부
        """
        logger.info(f"💾 현재 상태를 커스텀 프로파일로 저장: {profile_name}")

        try:
            # 프로파일명 유효성 검사
            if not profile_name.replace('_', '').replace('-', '').isalnum():
                logger.error(f"❌ 유효하지 않은 프로파일명: {profile_name}")
                return False

            # 현재 환경변수 상태 수집
            current_env_state = {
                'UPBIT_LOG_LEVEL': os.getenv('UPBIT_LOG_LEVEL', 'INFO'),
                'UPBIT_LOG_CONTEXT': os.getenv('UPBIT_LOG_CONTEXT', 'development'),
                'UPBIT_LOG_SCOPE': os.getenv('UPBIT_LOG_SCOPE', 'normal'),
                'UPBIT_CONSOLE_OUTPUT': os.getenv('UPBIT_CONSOLE_OUTPUT', 'false'),
                'UPBIT_COMPONENT_FOCUS': os.getenv('UPBIT_COMPONENT_FOCUS', ''),
                'UPBIT_LLM_BRIEFING_ENABLED': os.getenv('UPBIT_LLM_BRIEFING_ENABLED', 'false'),
                'UPBIT_FEATURE_DEVELOPMENT': os.getenv('UPBIT_FEATURE_DEVELOPMENT', ''),
                'UPBIT_PERFORMANCE_MONITORING': os.getenv('UPBIT_PERFORMANCE_MONITORING', 'false'),
                'UPBIT_BRIEFING_UPDATE_INTERVAL': os.getenv('UPBIT_BRIEFING_UPDATE_INTERVAL', '30')
            }

            # 환경변수 → YAML 구조로 변환
            config_data = {
                'profile_info': {
                    'name': profile_name,
                    'description': description,
                    'created_at': datetime.now().isoformat(),
                    'created_from': 'environment_variables'
                },
                'logging': {
                    'level': current_env_state['UPBIT_LOG_LEVEL'],
                    'context': current_env_state['UPBIT_LOG_CONTEXT'],
                    'scope': current_env_state['UPBIT_LOG_SCOPE'],
                    'console_enabled': current_env_state['UPBIT_CONSOLE_OUTPUT'].lower() == 'true',
                    'component_focus': current_env_state['UPBIT_COMPONENT_FOCUS'],
                    'llm_briefing_enabled': current_env_state['UPBIT_LLM_BRIEFING_ENABLED'].lower() == 'true',
                    'feature_development': current_env_state['UPBIT_FEATURE_DEVELOPMENT'],
                    'performance_monitoring': current_env_state['UPBIT_PERFORMANCE_MONITORING'].lower() == 'true',
                    'briefing_update_interval': int(current_env_state['UPBIT_BRIEFING_UPDATE_INTERVAL'])
                }
            }

            # YAML 파일로 저장
            custom_path = self.custom_profiles_dir / f"{profile_name}.yaml"
            with open(custom_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config_data, f, default_flow_style=False, allow_unicode=True, indent=2)

            logger.info(f"✅ 커스텀 프로파일 저장 완료: {custom_path}")
            return True

        except Exception as e:
            logger.error(f"❌ 커스텀 프로파일 저장 실패 ({profile_name}): {e}")
            return False

    def delete_custom_profile(self, profile_name: str) -> bool:
        """커스텀 프로파일 삭제

        Args:
            profile_name: 삭제할 프로파일명 (custom_ 접두사 포함)

        Returns:
            bool: 삭제 성공 여부
        """
        logger.info(f"🗑️ 커스텀 프로파일 삭제: {profile_name}")

        try:
            if not profile_name.startswith("custom_"):
                logger.error(f"❌ 기본 프로파일은 삭제할 수 없습니다: {profile_name}")
                return False

            actual_name = profile_name.replace("custom_", "")
            custom_path = self.custom_profiles_dir / f"{actual_name}.yaml"

            if custom_path.exists():
                custom_path.unlink()
                logger.info(f"✅ 커스텀 프로파일 삭제 완료: {custom_path}")
                return True
            else:
                logger.warning(f"⚠️ 삭제할 프로파일 파일이 없습니다: {custom_path}")
                return False

        except Exception as e:
            logger.error(f"❌ 커스텀 프로파일 삭제 실패 ({profile_name}): {e}")
            return False

    def get_current_profile(self) -> Optional[str]:
        """현재 활성 프로파일"""
        return self.profile_switcher.current_profile

    def get_ui_state(self) -> Dict[str, Any]:
        """UI 표시용 현재 상태"""
        return self.profile_switcher.get_current_ui_state()

    def preview_profile_changes(self, profile_name: str) -> Dict[str, str]:
        """프로파일 변경 미리보기 (실제 적용 없이)

        Args:
            profile_name: 미리볼 프로파일명

        Returns:
            Dict[str, str]: 적용될 환경변수들
        """
        try:
            if profile_name.startswith("custom_"):
                actual_name = profile_name.replace("custom_", "")
                custom_path = self.custom_profiles_dir / f"{actual_name}.yaml"

                with open(custom_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
            else:
                config_data = self.profile_switcher.config_loader.load_profile(profile_name)

            if 'logging' in config_data:
                return self.profile_switcher._map_config_to_env_vars(config_data['logging'])
            return {}
        except Exception as e:
            logger.error(f"프로파일 미리보기 실패 ({profile_name}): {e}")
            return {}

    def get_profile_info(self, profile_name: str) -> Dict[str, Any]:
        """프로파일 상세 정보 조회

        Args:
            profile_name: 조회할 프로파일명

        Returns:
            Dict[str, Any]: 프로파일 정보 (이름, 설명, 생성일시 등)
        """
        try:
            if profile_name.startswith("custom_"):
                actual_name = profile_name.replace("custom_", "")
                custom_path = self.custom_profiles_dir / f"{actual_name}.yaml"

                if custom_path.exists():
                    with open(custom_path, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f)

                    profile_info = config_data.get('profile_info', {})
                    return {
                        'name': profile_info.get('name', actual_name),
                        'description': profile_info.get('description', ''),
                        'type': 'custom',
                        'created_at': profile_info.get('created_at', ''),
                        'file_path': str(custom_path)
                    }
            else:
                # 기본 프로파일 정보
                basic_profiles_info = {
                    'development': '개발 환경 - 디버깅 친화적 설정',
                    'production': '프로덕션 환경 - 실운영 최적화 설정',
                    'testing': '테스트 환경 - 격리된 테스트 환경'
                }

                return {
                    'name': profile_name,
                    'description': basic_profiles_info.get(profile_name, ''),
                    'type': 'built-in',
                    'created_at': '',
                    'file_path': str(self.profile_switcher.config_loader.config_dir / f"config.{profile_name}.yaml")
                }

        except Exception as e:
            logger.error(f"프로파일 정보 조회 실패 ({profile_name}): {e}")
            return {'name': profile_name, 'description': '정보 조회 실패', 'type': 'unknown'}

    # ============================================================================
    # Task 5.2 호환성 메서드들 - 기존 시스템과의 완전한 호환을 위해 추가
    # ============================================================================

    def get_current_environment(self) -> str:
        """현재 활성 환경 조회

        Returns:
            str: 현재 환경명 (development, production, testing)
        """
        try:
            return self.profile_switcher.get_current_environment()
        except Exception as e:
            logger.error(f"현재 환경 조회 실패: {e}")
            return "development"  # 기본값

    def switch_environment(self, environment_name: str) -> bool:
        """환경 전환 (Task 5.2 호환성)

        Args:
            environment_name: 전환할 환경명

        Returns:
            bool: 전환 성공 여부
        """
        try:
            result = self.profile_switcher.switch_profile(environment_name)
            return result.success
        except Exception as e:
            logger.error(f"환경 전환 실패 ({environment_name}): {e}")
            return False

    def get_available_environments(self) -> List[str]:
        """사용 가능한 환경 목록 조회

        Returns:
            List[str]: 환경명 리스트
        """
        try:
            # 기본 환경들
            basic_environments = ['development', 'production', 'testing']

            # 커스텀 프로파일들 추가
            custom_environments = []
            if self.custom_profiles_dir.exists():
                for yaml_file in self.custom_profiles_dir.glob("*.yaml"):
                    custom_name = f"custom_{yaml_file.stem}"
                    custom_environments.append(custom_name)

            all_environments = basic_environments + custom_environments
            logger.debug(f"사용 가능한 환경: {all_environments}")
            return all_environments

        except Exception as e:
            logger.error(f"환경 목록 조회 실패: {e}")
            return ['development', 'production', 'testing']  # 기본값

    def load_environment_config(self, environment_name: str) -> Dict[str, Any]:
        """환경 설정 로드 (Task 5.2 호환성)

        Args:
            environment_name: 환경명

        Returns:
            Dict[str, Any]: 환경 설정 데이터
        """
        try:
            if environment_name.startswith("custom_"):
                actual_name = environment_name.replace("custom_", "")
                custom_path = self.custom_profiles_dir / f"{actual_name}.yaml"

                if custom_path.exists():
                    with open(custom_path, 'r', encoding='utf-8') as f:
                        return yaml.safe_load(f)
                else:
                    logger.warning(f"커스텀 환경 파일 없음: {custom_path}")
                    return {}
            else:
                return self.profile_switcher.config_loader.load_profile(environment_name)

        except Exception as e:
            logger.error(f"환경 설정 로드 실패 ({environment_name}): {e}")
            return {}
