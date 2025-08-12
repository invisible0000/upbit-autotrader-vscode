"""
Profile Editor Use Case
=======================

프로파일 편집을 위한 Use Case입니다.
Domain Layer와 Infrastruct    def save_edit_session(self, session: ProfileEditorSession,
                          content: str, target_file_path: str) -> bool:e Layer를 조율하여
안전한 프로파일 편집 워크플로우를 제공합니다.

주요 기능:
- 편집 세션 생성 및 관리
- 임시 파일 기반 안전 편집
- YAML 검증 및 적용
- 세션 상태 추적
"""

from datetime import datetime
from typing import Optional

from upbit_auto_trading.domain.profile_management.entities.profile_editor_session import ProfileEditorSession
from upbit_auto_trading.infrastructure.profile_storage.temp_file_manager import TempFileManager
from upbit_auto_trading.infrastructure.yaml_processing.yaml_parser import YamlParser, ValidationResult
from upbit_auto_trading.infrastructure.logging import create_component_logger
logger = create_component_logger("ProfileEditorUseCase")

class ProfileEditorUseCase:
    """
    프로파일 편집 Use Case

    프로파일 편집의 전체 워크플로우를 관리합니다:
    1. 편집 세션 시작
    2. 임시 파일 생성
    3. 내용 편집 및 검증
    4. 안전한 적용 또는 취소
    """

    def __init__(self,
                 temp_file_manager: TempFileManager,
                 yaml_parser: YamlParser):
        """
        Args:
            temp_file_manager: 임시 파일 관리자
            yaml_parser: YAML 파서
        """
        self.temp_file_manager = temp_file_manager
        self.yaml_parser = yaml_parser

        # 활성 세션 관리
        self._active_sessions: dict[str, ProfileEditorSession] = {}

        logger.info("ProfileEditorUseCase 초기화 완료")

    def start_edit_session(self, profile_name: str, is_new: bool,
                           original_content: str = "") -> ProfileEditorSession:
        """
        편집 세션 시작

        Args:
            profile_name: 편집할 프로파일명
            is_new: 신규 프로파일 생성 여부
            original_content: 원본 YAML 내용 (기존 프로파일인 경우)

        Returns:
            ProfileEditorSession: 생성된 편집 세션

        Raises:
            ValueError: 잘못된 매개변수
            RuntimeError: 세션 생성 실패
        """
        try:
            logger.info(f"편집 세션 시작: {profile_name} (신규: {is_new})")

            # 세션 검증
            if not profile_name.strip():
                raise ValueError("프로파일명은 필수입니다")

            # 기존 세션 종료 (동일 프로파일)
            existing_session = self._find_session_by_profile(profile_name)
            if existing_session:
                logger.warning(f"기존 세션 종료 후 새 세션 시작: {profile_name}")
                self.cancel_edit_session(existing_session)

            # 새 편집 세션 생성
            session = ProfileEditorSession(
                profile_name=profile_name,
                is_new_profile=is_new,
                original_content=original_content,
                current_content=original_content
            )

            # 임시 파일 생성
            temp_path = self.temp_file_manager.create_temp_file(
                profile_name=profile_name,
                content=original_content
            )
            session.set_temp_file_path(temp_path)

            # 활성 세션에 등록
            self._active_sessions[session.session_id] = session

            logger.info(f"편집 세션 생성 완료: {session.session_id[:8]}...")
            return session

        except Exception as e:
            error_msg = f"편집 세션 시작 실패 ({profile_name}): {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def save_edit_session(self, session: ProfileEditorSession,
                          content: str, target_file_path: str) -> bool:
        """
        편집 세션 저장 (임시 파일을 원본에 적용)

        Args:
            session: 편집 세션
            content: 최종 편집 내용
            target_file_path: 저장할 파일 경로

        Returns:
            bool: 성공 여부
        """
        try:
            logger.info(f"편집 세션 저장 시작: {session.session_id[:8]}...")

            # 세션 유효성 확인
            if session.session_id not in self._active_sessions:
                logger.error("유효하지 않은 편집 세션")
                return False

            # 내용 검증
            validation_result = self.validate_profile_content(content)
            if not validation_result.is_valid:
                logger.error(f"YAML 검증 실패: {validation_result.errors}")
                return False

            # 세션 내용 업데이트
            session.update_content(content)

            # 임시 파일에 최신 내용 저장
            if session.has_temp_file() and session.temp_file_path:
                with open(session.temp_file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            # 임시 파일을 원본에 적용
            if not session.temp_file_path:
                logger.error("임시 파일 경로가 없습니다")
                return False

            success = self.temp_file_manager.save_temp_to_original(
                temp_path=session.temp_file_path,
                original_path=target_file_path
            )

            if success:
                # 세션 완료 처리
                session.finalize_session()
                self._remove_session(session.session_id)

                logger.info(f"편집 세션 저장 완료: {target_file_path}")
                return True
            else:
                logger.error("임시 파일 적용 실패")
                return False

        except Exception as e:
            logger.error(f"편집 세션 저장 실패: {e}")
            return False

    def cancel_edit_session(self, session: ProfileEditorSession) -> bool:
        """
        편집 세션 취소

        Args:
            session: 취소할 편집 세션

        Returns:
            bool: 성공 여부
        """
        try:
            logger.info(f"편집 세션 취소: {session.session_id[:8]}...")

            # 임시 파일 정리
            if session.has_temp_file() and session.temp_file_path:
                self.temp_file_manager.cleanup_temp_file(session.temp_file_path)

            # 세션 제거
            self._remove_session(session.session_id)

            logger.info("편집 세션 취소 완료")
            return True

        except Exception as e:
            logger.error(f"편집 세션 취소 실패: {e}")
            return False

    def validate_profile_content(self, content: str) -> ValidationResult:
        """
        프로파일 내용 검증

        Args:
            content: 검증할 YAML 내용

        Returns:
            ValidationResult: 검증 결과
        """
        try:
            logger.debug("프로파일 내용 검증 시작")

            # YAML 구문 검증
            validation_result = self.yaml_parser.validate_yaml_syntax(content)

            # 추가 비즈니스 규칙 검증
            if validation_result.is_valid and validation_result.parsed_data:
                business_warnings = self._validate_business_rules(validation_result.parsed_data)
                validation_result.warnings.extend(business_warnings)

            logger.debug(f"검증 완료: {validation_result.get_summary()}")
            return validation_result

        except Exception as e:
            logger.error(f"내용 검증 실패: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"검증 중 오류 발생: {e}"],
                warnings=[]
            )

    def update_session_content(self, session: ProfileEditorSession,
                               new_content: str) -> bool:
        """
        세션 내용 업데이트 (임시 저장)

        Args:
            session: 편집 세션
            new_content: 새 내용

        Returns:
            bool: 성공 여부
        """
        try:
            # 세션 유효성 확인
            if session.session_id not in self._active_sessions:
                logger.error("유효하지 않은 편집 세션")
                return False

            # 내용 업데이트
            session.update_content(new_content)

            # 임시 파일에 저장
            if session.has_temp_file() and session.temp_file_path:
                with open(session.temp_file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                logger.debug(f"세션 내용 업데이트됨: {session.session_id[:8]}...")
                return True

            return False

        except Exception as e:
            logger.error(f"세션 내용 업데이트 실패: {e}")
            return False

    def get_active_sessions(self) -> list[ProfileEditorSession]:
        """활성 편집 세션 목록 반환"""
        return list(self._active_sessions.values())

    def get_session_by_profile(self, profile_name: str) -> Optional[ProfileEditorSession]:
        """프로파일명으로 세션 찾기"""
        return self._find_session_by_profile(profile_name)

    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """만료된 세션 정리"""
        try:
            expired_sessions = []
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)

            for session_id, session in self._active_sessions.items():
                if session.created_at.timestamp() < cutoff_time:
                    expired_sessions.append(session_id)

            # 만료된 세션 정리
            for session_id in expired_sessions:
                session = self._active_sessions[session_id]
                self.cancel_edit_session(session)

            if expired_sessions:
                logger.info(f"만료된 세션 {len(expired_sessions)}개 정리됨")

            return len(expired_sessions)

        except Exception as e:
            logger.error(f"세션 정리 실패: {e}")
            return 0

    def _find_session_by_profile(self, profile_name: str) -> Optional[ProfileEditorSession]:
        """프로파일명으로 세션 검색"""
        for session in self._active_sessions.values():
            if session.profile_name == profile_name:
                return session
        return None

    def _remove_session(self, session_id: str) -> None:
        """세션 제거"""
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]

    def _validate_business_rules(self, data: dict) -> list[str]:
        """비즈니스 규칙 검증"""
        warnings = []

        # 필수 섹션 확인
        required_sections = ['logging']
        for section in required_sections:
            if section not in data:
                warnings.append(f"권장 섹션 '{section}'이 없습니다")

        # 로깅 설정 검증
        if 'logging' in data:
            logging_config = data['logging']

            # 로그 레벨 검증
            if 'level' in logging_config:
                valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
                if logging_config['level'] not in valid_levels:
                    warnings.append(f"유효하지 않은 로그 레벨: {logging_config['level']}")

            # 컨텍스트 검증
            if 'context' in logging_config:
                valid_contexts = ['development', 'production', 'testing']
                if logging_config['context'] not in valid_contexts:
                    warnings.append(f"유효하지 않은 로그 컨텍스트: {logging_config['context']}")

        return warnings
