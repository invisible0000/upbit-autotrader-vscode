"""
Environment Profile Presenter (Refactored)
==========================================

DDD 기반으로 리팩토링된 깔끔한 MVP 패턴의 Presenter
Application Service들을 오케스트레이션하여 비즈니스 로직을 처리

Features:
- Service 기반 아키텍처로 단순화
- MVP 패턴의 순수한 Presenter 역할
- 비즈니스 로직을 Application Services로 위임
- View와 Domain Layer 간 중재

Author: AI Assistant
Created: 2025-08-11
Refactored from: environment_profile_presenter.py (er-subTASK 01 Step 05)
"""

from typing import Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger

# Application Services Import
from upbit_auto_trading.application.services.profile_metadata_service import ProfileMetadataService
from upbit_auto_trading.application.services.profile_edit_session_service import ProfileEditSessionService
from upbit_auto_trading.application.services.profile_validation_service import ProfileValidationService
from ..dialogs.profile_metadata import ProfileMetadata


logger = create_component_logger("EnvironmentProfilePresenter")


class EnvironmentProfilePresenter(QObject):
    """
    DDD 기반 환경 프로파일 관리 MVP Presenter

    Application Service들을 오케스트레이션하여 복잡한 비즈니스 로직을
    처리하고, View에 필요한 데이터와 상태를 제공합니다.
    """

    # ===============================================================================
    # === MVP Presenter 시그널 정의 ===
    # ===============================================================================

    # 프로파일 관리 시그널
    profile_data_loaded = pyqtSignal(dict)          # 프로파일 데이터 로드 완료
    yaml_content_loaded = pyqtSignal(str)           # YAML 내용 로드 완료
    profile_list_updated = pyqtSignal(dict)         # 프로파일 목록 업데이트 (딕셔너리)

    # 편집 상태 시그널
    edit_session_started = pyqtSignal(str)          # 편집 세션 시작 (임시파일 경로)
    unsaved_changes_detected = pyqtSignal(str)      # 저장되지 않은 변경사항 감지
    content_changed = pyqtSignal(str)               # 내용 변경됨

    # 검증 및 저장 시그널
    validation_result = pyqtSignal(bool, str)       # 검증 결과 (성공여부, 메시지)
    save_completed = pyqtSignal(str)                # 저장 완료 (파일경로)
    load_completed = pyqtSignal(str)                # 로드 완료 (프로파일명)

    # 환경 관리 시그널
    environment_switched = pyqtSignal(str)          # 환경 전환 완료
    environment_list_updated = pyqtSignal(list)     # 환경 목록 업데이트

    # 에러 및 상태 시그널
    error_occurred = pyqtSignal(str)                # 에러 발생
    warning_occurred = pyqtSignal(str)              # 경고 발생
    status_updated = pyqtSignal(str)                # 상태 메시지 업데이트

    def __init__(self, view=None):
        """EnvironmentProfilePresenter 초기화"""
        super().__init__()
        self._view = view
        self._current_profile = ""
        self._edit_mode = False
        self._has_unsaved_changes = False

        # Application Services 초기화
        self._metadata_service = ProfileMetadataService()
        self._edit_session_service = ProfileEditSessionService()
        self._validation_service = ProfileValidationService()

        logger.info("🎭 EnvironmentProfilePresenter 초기화 완료 (DDD 리팩토링 버전)")

        # 초기 데이터 로드
        self._initialize_data()

    def _initialize_data(self):
        """초기 데이터 로드 및 UI 초기화"""
        logger.debug("🔧 초기 데이터 로드 시작")

        try:
            # 프로파일 목록 새로고침
            self.refresh_profile_list()

            # 기본 환경 자동 선택 (development)
            self.load_profile('development')

            logger.info("✅ 초기 데이터 로드 완료")

        except Exception as e:
            logger.error(f"❌ 초기 데이터 로드 실패: {e}")

    # ===============================================================================
    # === 프로파일 선택 및 로드 (Task 3.1.1) ===
    # ===============================================================================

    def load_profile(self, profile_name: str) -> bool:
        """프로파일 로드 및 UI 업데이트 - 실제 YAML 파일 로드 기능 추가"""
        logger.info(f"📂 프로파일 로드 요청: {profile_name}")

        try:
            # 0단계: 빈 값 검증
            if not profile_name or profile_name.strip() == "":
                error_msg = "프로파일명이 비어있습니다"
                logger.error(f"❌ {error_msg}")
                self.error_occurred.emit(error_msg)
                return False

            # 1단계: 저장되지 않은 변경사항 확인 (기존 프로파일과 다른 경우만)
            if self._has_unsaved_changes and self._current_profile != profile_name:
                self.unsaved_changes_detected.emit(self._current_profile)
                logger.warning(f"⚠️ 저장되지 않은 변경사항 존재: {self._current_profile}")
                return False

            # 2단계: 메타데이터 서비스로 프로파일 로드
            profile_data = self._metadata_service.load_profile_metadata(profile_name)
            if not profile_data:
                logger.warning(f"⚠️ 메타데이터 로드 실패, 기본 데이터로 진행: {profile_name}")
                # 기본 프로파일의 경우 메타데이터가 없을 수 있으므로 계속 진행

            # 🔥 3단계: 실제 YAML 파일 내용 로드 (가장 중요)
            yaml_content = self._load_yaml_file_content(profile_name)
            if not yaml_content:
                error_msg = f"YAML 파일 로드 실패: {profile_name}"
                logger.error(f"❌ {error_msg}")
                self.error_occurred.emit(error_msg)
                return False

            # 4단계: 상태 업데이트
            self._current_profile = profile_name
            self._has_unsaved_changes = False
            self._edit_mode = False

            # 5단계: ProfileMetadata를 dict로 변환하여 시그널 발송
            if profile_data:
                if hasattr(profile_data, 'to_dict'):
                    profile_dict = profile_data.to_dict()
                elif hasattr(profile_data, '__dict__'):
                    profile_dict = profile_data.__dict__
                else:
                    # ProfileMetadata 객체의 속성들을 수동으로 dict 변환
                    profile_dict = {
                        'name': getattr(profile_data, 'name', profile_name),
                        'description': getattr(profile_data, 'description', ''),
                        'profile_type': getattr(profile_data, 'profile_type', 'unknown'),
                        'tags': getattr(profile_data, 'tags', []),
                        'created_at': getattr(profile_data, 'created_at', ''),
                        'created_from': getattr(profile_data, 'created_from', ''),
                        'metadata': profile_data if profile_data else {},
                        'content': yaml_content
                    }
            else:
                # 메타데이터가 없는 경우 기본 구조 생성
                built_in_profiles = ['development', 'production', 'testing', 'staging', 'debug', 'demo']
                profile_type = 'built-in' if profile_name in built_in_profiles else 'custom'

                profile_dict = {
                    'name': profile_name,
                    'description': f'{profile_name} 환경 설정',
                    'profile_type': profile_type,
                    'tags': [],
                    'created_at': '',
                    'created_from': '',
                    'metadata': {},
                    'content': yaml_content
                }

            # 🔥 6단계: 시그널 발송 순서 조정 및 강화
            logger.info(f"🚀 프로파일 데이터 시그널 발송: {profile_name}")
            self.profile_data_loaded.emit(profile_dict)

            logger.info(f"🚀 YAML 내용 시그널 발송: {len(yaml_content)} 문자")
            self.yaml_content_loaded.emit(yaml_content)

            logger.info(f"🚀 로드 완료 시그널 발송: {profile_name}")
            self.load_completed.emit(profile_name)

            logger.info(f"✅ 프로파일 로드 완료: {profile_name} (YAML: {len(yaml_content)} 문자)")
            return True

        except Exception as e:
            error_msg = f"프로파일 로드 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def _load_yaml_file_content(self, profile_name: str) -> str:
        """실제 YAML 파일 내용 로드"""
        try:
            from pathlib import Path

            # config.{profile_name}.yaml 파일 경로 생성
            config_file = f"config.{profile_name}.yaml"
            config_path = Path("config") / config_file

            logger.debug(f"📁 YAML 파일 로드 시도: {config_path}")

            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.debug(f"✅ YAML 파일 로드 성공: {len(content)} 문자")
                return content
            else:
                logger.warning(f"⚠️ YAML 파일 존재하지 않음: {config_path}")
                return f"# 프로파일 파일을 찾을 수 없습니다: {config_file}\n# 파일 경로: {config_path}"

        except Exception as e:
            logger.error(f"❌ YAML 파일 로드 실패: {e}")
            return f"# YAML 파일 로드 오류: {str(e)}"

    def refresh_profile_list(self):
        """프로파일 목록 새로고침"""
        logger.debug("🔄 프로파일 목록 새로고침")

        try:
            # 메타데이터 서비스로 프로파일 목록 조회
            profile_list = self._metadata_service.get_available_profiles()

            # View에서 사용할 수 있는 완전한 프로파일 데이터 생성
            profiles_data = {}
            for profile_name in profile_list:
                try:
                    # 각 프로파일의 메타데이터 로드
                    metadata = self._metadata_service.load_profile_metadata(profile_name)

                    # ProfileSelectorSection.load_profiles()가 요구하는 형태로 변환
                    profiles_data[profile_name] = {
                        'metadata': {
                            'name': getattr(metadata, 'name', profile_name),
                            'description': getattr(metadata, 'description', ''),
                            'profile_type': getattr(metadata, 'profile_type', 'unknown'),
                            'tags': getattr(metadata, 'tags', []),
                            'created_at': getattr(metadata, 'created_at', ''),
                            'created_from': getattr(metadata, 'created_from', '')
                        },
                        'content': ''  # YAML 내용은 필요시 로드
                    }
                except Exception as e:
                    logger.warning(f"⚠️ {profile_name} 메타데이터 로드 실패: {e}")
                    # 기본 데이터 구조 생성
                    built_in_profiles = ['development', 'production', 'testing']
                    profile_type = 'built-in' if profile_name in built_in_profiles else 'custom'

                    profiles_data[profile_name] = {
                        'metadata': {
                            'name': profile_name,
                            'description': f'{profile_name} 환경 설정',
                            'profile_type': profile_type,
                            'tags': [],
                            'created_at': '',
                            'created_from': ''
                        },
                        'content': ''
                    }

            # View 업데이트 시그널 발송 (딕셔너리 형태로 - ProfileSelectorSection.load_profiles() 호환)
            logger.info(f"🚀 profile_list_updated 시그널 발송: {len(profiles_data)}개 프로파일")
            logger.debug(f"📋 발송할 프로파일 데이터: {list(profiles_data.keys())}")
            self.profile_list_updated.emit(profiles_data)  # 딕셔너리 전체 발송

            logger.debug(f"✅ 프로파일 목록 새로고침 완료: {len(profile_list)}개")

        except Exception as e:
            error_msg = f"프로파일 목록 새로고침 실패: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)

    # ===============================================================================
    # === 편집 모드 관리 (Task 3.1.2) ===
    # ===============================================================================

    def start_edit_mode(self, profile_name: str = "") -> bool:
        """편집 모드 시작"""
        target_profile = profile_name or self._current_profile
        logger.info(f"✏️ 편집 모드 시작: {target_profile}")

        try:
            # 1단계: 기존 프로파일 편집 시작
            if target_profile and target_profile != "":
                temp_file_path = self._edit_session_service.start_edit_existing_profile(target_profile)
            else:
                # 새 프로파일 생성
                temp_file_path = self._edit_session_service.start_edit_new_profile()

            if not temp_file_path:
                error_msg = f"편집 세션 시작 실패: {target_profile}"
                logger.error(f"❌ {error_msg}")
                self.error_occurred.emit(error_msg)
                return False

            # 2단계: 편집 상태 업데이트
            self._edit_mode = True
            self._has_unsaved_changes = False

            # 3단계: View에 편집 세션 시작 알림
            self.edit_session_started.emit(temp_file_path)

            logger.info(f"✅ 편집 모드 시작 완료: {temp_file_path}")
            return True

        except Exception as e:
            error_msg = f"편집 모드 시작 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def exit_edit_mode(self, save_changes: bool = True) -> bool:
        """편집 모드 종료"""
        logger.info(f"🚪 편집 모드 종료 (저장: {save_changes})")

        try:
            if save_changes and self._has_unsaved_changes:
                # 변경사항 저장
                if not self.save_current_profile():
                    logger.warning("⚠️ 저장 실패로 편집 모드 유지")
                    return False

            # 편집 상태 초기화
            self._edit_mode = False
            self._has_unsaved_changes = False

            logger.info("✅ 편집 모드 종료 완료")
            return True

        except Exception as e:
            error_msg = f"편집 모드 종료 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def track_content_changes(self, new_content: str):
        """내용 변경 추적"""
        if self._edit_mode:
            self._has_unsaved_changes = True
            self.content_changed.emit(new_content)
            logger.debug("📝 내용 변경 감지됨")

    # ===============================================================================
    # === 환경 전환 처리 (Task 3.2) ===
    # ===============================================================================

    def switch_environment(self, new_profile_name: str) -> bool:
        """환경 전환 처리"""
        logger.info(f"🔄 환경 전환 요청: {self._current_profile} → {new_profile_name}")

        try:
            # 1단계: 현재 편집 중인지 확인
            if self._edit_mode and self._has_unsaved_changes:
                self.unsaved_changes_detected.emit(self._current_profile)
                logger.warning("⚠️ 편집 중인 내용이 있어 환경 전환 보류")
                return False

            # 2단계: 새 프로파일 로드
            if not self.load_profile(new_profile_name):
                return False

            # 3단계: 환경 전환 완료 시그널
            self.environment_switched.emit(new_profile_name)

            logger.info(f"✅ 환경 전환 완료: {new_profile_name}")
            return True

        except Exception as e:
            error_msg = f"환경 전환 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    # ===============================================================================
    # === 검증 및 저장 처리 ===
    # ===============================================================================

    def validate_current_content(self, yaml_content: str) -> bool:
        """현재 내용 검증"""
        logger.debug("🔍 내용 검증 시작")

        try:
            # 검증 서비스로 YAML 구문 검증
            validation_result = self._validation_service.validate_yaml_syntax(yaml_content)

            if validation_result.is_valid:
                self.validation_result.emit(True, "검증 성공")
                logger.debug("✅ 내용 검증 성공")
                return True
            else:
                error_msg = "; ".join(validation_result.errors)
                self.validation_result.emit(False, error_msg)
                logger.warning(f"⚠️ 내용 검증 실패: {error_msg}")
                return False

        except Exception as e:
            error_msg = f"내용 검증 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.validation_result.emit(False, error_msg)
            return False

    def save_current_profile(self) -> bool:
        """현재 프로파일 저장"""
        logger.info(f"💾 프로파일 저장: {self._current_profile}")

        try:
            if not self._current_profile:
                error_msg = "저장할 프로파일이 선택되지 않음"
                logger.error(f"❌ {error_msg}")
                self.error_occurred.emit(error_msg)
                return False

            # 편집 세션 서비스로 저장 처리
            success = self._edit_session_service.save_temp_to_original(self._current_profile)

            if success:
                self._has_unsaved_changes = False
                self.save_completed.emit(self._current_profile)
                logger.info(f"✅ 프로파일 저장 완료: {self._current_profile}")
                return True
            else:
                error_msg = f"프로파일 저장 실패: {self._current_profile}"
                logger.error(f"❌ {error_msg}")
                self.error_occurred.emit(error_msg)
                return False

        except Exception as e:
            error_msg = f"프로파일 저장 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    # ===============================================================================
    # === 메타데이터 관리 (Task 4.2) ===
    # ===============================================================================

    def show_metadata_dialog(self, profile_name: str) -> bool:
        """메타데이터 편집 다이얼로그 표시"""
        logger.info(f"📋 메타데이터 다이얼로그 표시: {profile_name}")

        try:
            # 메타데이터 서비스로 다이얼로그 처리 위임
            success = self._metadata_service.show_metadata_dialog(profile_name)

            if success:
                # 프로파일 목록 새로고침 (메타데이터 변경 반영)
                self.refresh_profile_list()
                logger.info(f"✅ 메타데이터 다이얼로그 처리 완료: {profile_name}")
                return True
            else:
                logger.warning(f"⚠️ 메타데이터 다이얼로그 취소됨: {profile_name}")
                return False

        except Exception as e:
            error_msg = f"메타데이터 다이얼로그 처리 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def update_profile_metadata(self, profile_name: str, metadata_dict: dict) -> bool:
        """프로파일 메타데이터 업데이트"""
        logger.info(f"📝 메타데이터 업데이트: {profile_name}")

        try:
            # 딕셔너리를 ProfileMetadata 객체로 변환
            metadata = ProfileMetadata.from_dict(metadata_dict)

            # 메타데이터 서비스로 업데이트 처리
            success = self._metadata_service.save_profile_metadata(profile_name, metadata)

            if success:
                # 콤보박스 표시 업데이트
                self._metadata_service.update_profile_combo_display(profile_name)
                self.refresh_profile_list()
                logger.info(f"✅ 메타데이터 업데이트 완료: {profile_name}")
                return True
            else:
                error_msg = f"메타데이터 업데이트 실패: {profile_name}"
                logger.error(f"❌ {error_msg}")
                self.error_occurred.emit(error_msg)
                return False

        except Exception as e:
            error_msg = f"메타데이터 업데이트 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    # ===============================================================================
    # === 유틸리티 및 상태 관리 ===
    # ===============================================================================

    def cleanup_temp_files(self):
        """임시 파일 정리"""
        logger.info("🧹 임시 파일 정리 시작")

        try:
            self._edit_session_service.cleanup_abandoned_temp_files()
            logger.info("✅ 임시 파일 정리 완료")

        except Exception as e:
            error_msg = f"임시 파일 정리 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.warning_occurred.emit(error_msg)

    def get_current_state(self) -> Dict[str, Any]:
        """현재 상태 정보 반환"""
        return {
            'current_profile': self._current_profile,
            'edit_mode': self._edit_mode,
            'has_unsaved_changes': self._has_unsaved_changes,
            'services_initialized': True
        }

    def is_edit_mode(self) -> bool:
        """편집 모드 상태 확인"""
        return self._edit_mode

    def has_unsaved_changes(self) -> bool:
        """저장되지 않은 변경사항 확인"""
        return self._has_unsaved_changes

    def get_current_profile(self) -> str:
        """현재 선택된 프로파일명 반환"""
        return self._current_profile

    # ===============================================================================
    # === Presenter 생명주기 관리 ===
    # ===============================================================================

    def initialize(self):
        """Presenter 초기화"""
        logger.info("🎬 Presenter 초기화")

        try:
            # 1단계: 프로파일 목록 로드
            self.refresh_profile_list()

            # 2단계: 임시 파일 정리
            self.cleanup_temp_files()

            # 3단계: 기본 프로파일 로드 (development)
            if not self._current_profile:
                self.load_profile("development")

            logger.info("✅ Presenter 초기화 완료")

        except Exception as e:
            error_msg = f"Presenter 초기화 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)

    def shutdown(self):
        """Presenter 종료 처리"""
        logger.info("🛑 Presenter 종료 처리")

        try:
            # 1단계: 편집 모드 정리
            if self._edit_mode:
                self.exit_edit_mode(save_changes=False)

            # 2단계: 임시 파일 정리
            self.cleanup_temp_files()

            # 3단계: 상태 초기화
            self._current_profile = ""
            self._edit_mode = False
            self._has_unsaved_changes = False

            logger.info("✅ Presenter 종료 처리 완료")

        except Exception as e:
            error_msg = f"Presenter 종료 처리 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")

    def __del__(self):
        """소멸자 - 정리 작업"""
        try:
            self.shutdown()
        except Exception:
            pass  # 소멸자에서는 예외 무시
