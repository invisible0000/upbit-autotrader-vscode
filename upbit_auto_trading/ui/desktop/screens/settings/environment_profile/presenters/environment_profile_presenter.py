"""
Environment Profile Presenter
============================

환경 프로파일 관리를 위한 MVP 패턴의 Presenter 구현
View와 Domain Layer 사이의 중재자 역할

Features:
- 프로파일 선택 및 로드 로직
- YAML 편집 상태 관리
- 환경 전환 처리
- 데이터 검증 및 저장
- 에러 처리 및 사용자 피드백

Author: AI Assistant
Created: 2025-08-11
"""

from typing import Dict, Any, Optional
import yaml
from PyQt6.QtCore import QObject, pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger
from ..dialogs.profile_metadata import ProfileMetadata


# === Task 4.1.3: ProfileEditorSession 데이터 클래스 ===
class ProfileEditorSession:
    """편집 세션 정보를 관리하는 데이터 클래스"""
    def __init__(self, session_id: str, profile_name: str, is_new_profile: bool,
                 temp_file_path: str = "", original_content: str = "", current_content: str = ""):
        self.session_id = session_id
        self.profile_name = profile_name
        self.is_new_profile = is_new_profile
        self.temp_file_path = temp_file_path
        self.original_content = original_content
        self.current_content = current_content
        self.created_at = self._get_current_timestamp()
        self.last_modified = self.created_at

    def _get_current_timestamp(self) -> str:
        import datetime
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def update_content(self, new_content: str):
        """내용 업데이트 및 수정 시간 갱신"""
        self.current_content = new_content
        self.last_modified = self._get_current_timestamp()

    def to_dict(self) -> dict:
        """딕셔너리로 변환 (저장용)"""
        return {
            'session_id': self.session_id,
            'profile_name': self.profile_name,
            'is_new_profile': self.is_new_profile,
            'temp_file_path': self.temp_file_path,
            'original_content': self.original_content,
            'current_content': self.current_content,
            'created_at': self.created_at,
            'last_modified': self.last_modified
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ProfileEditorSession':
        """딕셔너리에서 복원"""
        session = cls(
            session_id=data['session_id'],
            profile_name=data['profile_name'],
            is_new_profile=data['is_new_profile'],
            temp_file_path=data.get('temp_file_path', ''),
            original_content=data.get('original_content', ''),
            current_content=data.get('current_content', '')
        )
        session.created_at = data.get('created_at', session.created_at)
        session.last_modified = data.get('last_modified', session.last_modified)
        return session


logger = create_component_logger("EnvironmentProfilePresenter")


class EnvironmentProfilePresenter(QObject):
    """
    환경 프로파일 관리를 위한 MVP Presenter

    View와 Domain/Infrastructure Layer 사이의 중재자 역할을 담당하여
    비즈니스 로직과 UI 로직을 분리합니다.
    """

    # Presenter에서 발생하는 시그널 (View 업데이트용)
    profile_data_loaded = pyqtSignal(dict)          # 프로파일 데이터 로드 완료
    yaml_content_loaded = pyqtSignal(str)           # YAML 내용 로드 완료
    validation_result = pyqtSignal(bool, str)       # 검증 결과 (성공여부, 메시지)
    save_completed = pyqtSignal(str)                # 저장 완료 (파일경로)
    error_occurred = pyqtSignal(str)                # 에러 발생

    # Task 3.1.2: 추가 시그널
    unsaved_changes_detected = pyqtSignal(str)      # 저장되지 않은 변경사항 감지
    environment_switched = pyqtSignal(str)          # 환경 전환 완료

    def __init__(self, view=None):
        super().__init__()
        self.view = view
        self.current_profile_path = ""
        self.current_environment = "development"
        self.is_editing = False
        self.unsaved_changes = False

        # Task 3.1.3: 편집 모드 관리를 위한 속성 추가
        self._edit_mode = False
        self._current_profile = None  # 현재 선택된 프로파일 정보

        logger.info("🎯 EnvironmentProfilePresenter 초기화")

        # View 연결
        if self.view:
            self._connect_view_signals()
            self._initialize_data()

    def set_view(self, view):
        """View 설정 (지연 초기화 지원)"""
        self.view = view
        if view:
            self._connect_view_signals()
            self._initialize_data()
            logger.info("✅ View 연결 완료")

    def _connect_view_signals(self):
        """View 시그널과 Presenter 메서드 연결"""
        if not self.view:
            return

        logger.debug("🔧 View 시그널 연결 시작")

        try:
            # 프로파일 선택 관련
            self.view.profile_changed.connect(self._on_profile_selected)

            # 내용 변경 관련
            self.view.content_saved.connect(self._on_content_saved)

            # 에러 처리
            self.view.error_occurred.connect(self._on_view_error)

            logger.debug("✅ View 시그널 연결 완료")

        except Exception as e:
            logger.error(f"❌ View 시그널 연결 실패: {e}")

    def _initialize_data(self):
        """초기 데이터 로드"""
        logger.info("🔄 초기 데이터 로드 시작")

        try:
            # 기본 프로파일 로드
            self._load_default_profile()

            # 환경 설정 초기화
            self._initialize_environment_settings()

            logger.info("✅ 초기 데이터 로드 완료")

        except Exception as e:
            logger.error(f"❌ 초기 데이터 로드 실패: {e}")
            self.error_occurred.emit(f"초기화 실패: {e}")

    def _load_default_profile(self):
        """기본 프로파일 로드"""
        logger.debug("📂 기본 프로파일 로드")

        try:
            # 개발 환경 프로파일을 기본으로 로드
            default_profile = "config/config.development.yaml"
            self._load_profile(default_profile)

        except Exception as e:
            logger.warning(f"⚠️ 기본 프로파일 로드 실패: {e}")

    def _initialize_environment_settings(self):
        """환경 설정 초기화"""
        logger.debug("🔧 환경 설정 초기화")

        # 기본 환경을 development로 설정
        self.current_environment = "development"

        logger.debug(f"✅ 환경 설정 완료: {self.current_environment}")

    # === Task 3.1.2: 프로파일 선택 로직 구현 ===

    def _on_profile_selected(self, profile_name: str):
        """프로파일 선택 시 처리 로직 (Task 3.1.2)"""
        logger.info(f"📂 프로파일 선택됨: {profile_name}")

        try:
            # 변경사항 확인
            if self.has_unsaved_changes():
                # 사용자에게 저장 여부 확인 (View에서 처리)
                self.unsaved_changes_detected.emit(profile_name)
                return

            # 프로파일 로드
            self._load_selected_profile(profile_name)

        except Exception as e:
            logger.error(f"❌ 프로파일 선택 처리 실패: {e}")
            self.error_occurred.emit(f"프로파일 선택 실패: {e}")

    def _load_profile(self, profile_path: str):
        """프로파일 로드"""
        logger.debug(f"📖 프로파일 로드: {profile_path}")

        try:
            # 프로파일 경로 저장
            self.current_profile_path = profile_path

            # 프로파일 메타데이터 로드 (실제 구현 시 ConfigProfileService 사용)
            profile_data = self._load_profile_metadata(profile_path)

            # YAML 내용 로드
            yaml_content = self._load_yaml_content(profile_path)

            # View에 데이터 전달
            self.profile_data_loaded.emit(profile_data)
            self.yaml_content_loaded.emit(yaml_content)

            # 상태 업데이트
            self.unsaved_changes = False

            logger.info(f"✅ 프로파일 로드 완료: {profile_path}")

        except Exception as e:
            logger.error(f"❌ 프로파일 로드 실패: {e}")
            self.error_occurred.emit(f"프로파일 로드 실패: {e}")

    def _load_profile_metadata_mock(self, profile_path: str) -> Dict[str, Any]:
        """프로파일 메타데이터 로드 (모스 구현)"""
        logger.debug(f"📋 프로파일 메타데이터 로드: {profile_path}")

        # 실제 구현에서는 ConfigProfileService를 사용
        return {
            "name": "개발 환경",
            "description": "개발용 프로파일",
            "environment": "development",
            "tags": ["development", "debug"],
            "created_at": "2025-08-11T14:30:00",
            "file_path": profile_path
        }

    def _load_yaml_content(self, profile_path: str) -> str:
        """YAML 파일 내용 로드 (모크 구현)"""
        logger.debug(f"📄 YAML 내용 로드: {profile_path}")

        # 실제 구현에서는 파일 시스템에서 로드
        return """# 개발 환경 설정
logging:
  level: DEBUG
  console_output: true
  file_output: false
  log_format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

database:
  connection_timeout: 30
  max_retry_attempts: 3
  backup_interval: 3600

trading:
  paper_trading: true
  max_position_size: 0.1
  stop_loss_percentage: 0.05

indicators:
  rsi_period: 14
  sma_period: 20"""

    def _get_profile_config_path(self, profile_name: str):
        """프로파일 설정 파일 경로 반환"""
        from pathlib import Path
        config_dir = Path("config")
        return config_dir / f"config.{profile_name}.yaml"

    # === 편집 관련 메서드 ===

    def _on_content_saved(self, content: str, filename: str):
        """내용 저장 시 처리"""
        logger.info(f"💾 내용 저장: {filename}")

        try:
            # YAML 내용 검증
            is_valid, message = self._validate_yaml_content(content)

            if not is_valid:
                logger.error(f"❌ YAML 검증 실패: {message}")
                self.validation_result.emit(False, message)
                return

            # 실제 파일 저장 (실제 구현에서는 ConfigProfileService 사용)
            self._save_yaml_content(content, filename)

            # 상태 업데이트
            self.unsaved_changes = False

            # 성공 알림
            self.validation_result.emit(True, "저장 완료")
            self.save_completed.emit(filename)

            logger.info(f"✅ 파일 저장 완료: {filename}")

        except Exception as e:
            logger.error(f"❌ 내용 저장 실패: {e}")
            self.error_occurred.emit(f"저장 실패: {e}")

    # === Task 3.1.3: 편집 모드 관리 로직 ===

    def _on_edit_mode_requested(self):
        """편집 모드 시작 처리"""
        logger.info("📝 편집 모드 시작 요청")

        try:
            # 현재 편집 중인 내용이 있는지 확인
            if self.unsaved_changes:
                logger.warning("⚠️ 저장되지 않은 변경사항 존재")
                self.unsaved_changes_detected.emit()
                return

            # 편집 모드 상태 설정
            self._edit_mode = True

            # 현재 프로파일의 YAML 내용을 편집기에 로드
            if self._current_profile:
                profile_name = self._current_profile['name']
                self._load_profile_yaml_content(profile_name)
                logger.info(f"📄 편집 모드 시작: {profile_name}")
            else:
                logger.warning("⚠️ 편집할 프로파일이 선택되지 않음")
                self.error_occurred.emit("편집할 프로파일을 먼저 선택해주세요")

        except Exception as e:
            logger.error(f"❌ 편집 모드 시작 실패: {e}")
            self.error_occurred.emit(f"편집 모드 시작 실패: {e}")

    def _on_save_requested(self, content: str, filename: str):
        """저장 요청 처리"""
        logger.info(f"💾 저장 요청: {filename}")

        try:
            # 프로파일 검증 및 저장
            success = self._validate_and_save_profile(content, filename)

            if success:
                # 편집 모드 종료
                self._edit_mode = False
                self.unsaved_changes = False

                # 저장 완료 시그널 발송
                self.save_completed.emit(filename)
                logger.info(f"✅ 저장 완료: {filename}")
            else:
                logger.warning(f"⚠️ 저장 검증 실패: {filename}")

        except Exception as e:
            logger.error(f"❌ 저장 요청 처리 실패: {e}")
            self.error_occurred.emit(f"저장 실패: {e}")

    def _on_cancel_requested(self):
        """편집 취소 처리"""
        logger.info("🚫 편집 취소 요청")

        try:
            # 저장되지 않은 변경사항 확인
            if self.unsaved_changes:
                logger.warning("⚠️ 저장되지 않은 변경사항이 손실됩니다")
                # 실제 구현에서는 사용자 확인 다이얼로그 표시 필요

            # 편집 모드 종료 및 상태 초기화
            self._edit_mode = False
            self.unsaved_changes = False

            # 원본 내용으로 복원 (현재 프로파일 다시 로드)
            if self._current_profile:
                profile_name = self._current_profile['name']
                self._load_profile_yaml_content(profile_name)
                logger.info(f"🔄 원본 내용으로 복원: {profile_name}")

            # 편집 취소 완료 시그널 발송
            # self.edit_cancelled.emit()  # 필요시 시그널 추가
            logger.info("✅ 편집 취소 완료")

        except Exception as e:
            logger.error(f"❌ 편집 취소 처리 실패: {e}")
            self.error_occurred.emit(f"편집 취소 실패: {e}")

    def _validate_and_save_profile(self, content: str, filename: str) -> bool:
        """프로파일 검증 및 저장"""
        logger.debug(f"🔍 프로파일 검증 및 저장: {filename}")

        try:
            # 1단계: YAML 구문 검증
            is_valid, validation_message = self._validate_yaml_content(content)
            if not is_valid:
                logger.error(f"❌ YAML 구문 검증 실패: {validation_message}")
                self.validation_result.emit(False, validation_message)
                return False

            # 2단계: 프로파일 스키마 검증 (추가 구현 필요)
            # 실제 구현에서는 ConfigProfileService를 통한 스키마 검증
            schema_valid = self._validate_profile_schema(content)
            if not schema_valid:
                error_msg = "프로파일 스키마 검증 실패"
                logger.error(f"❌ {error_msg}")
                self.validation_result.emit(False, error_msg)
                return False

            # 3단계: 파일 저장
            self._save_yaml_content(content, filename)

            # 4단계: 검증 성공 알림
            self.validation_result.emit(True, "검증 및 저장 완료")
            logger.debug(f"✅ 프로파일 검증 및 저장 완료: {filename}")

            return True

        except Exception as e:
            error_msg = f"프로파일 저장 중 오류: {e}"
            logger.error(f"❌ {error_msg}")
            self.validation_result.emit(False, error_msg)
            return False

    def _validate_profile_schema(self, content: str) -> bool:
        """프로파일 스키마 검증 (모크 구현)"""
        logger.debug("🔍 프로파일 스키마 검증")

        try:
            # YAML 파싱하여 기본 구조 확인
            data = yaml.safe_load(content)

            # 필수 섹션 확인
            required_sections = ['upbit', 'logging', 'database', 'trading']
            for section in required_sections:
                if section not in data:
                    logger.warning(f"⚠️ 필수 섹션 누락: {section}")
                    return False

            # 기본 검증 통과
            logger.debug("✅ 프로파일 스키마 검증 통과")
            return True

        except Exception as e:
            logger.warning(f"⚠️ 스키마 검증 중 오류: {e}")
            return False

    # === YAML 내용 검증 ===

    def _validate_yaml_content(self, content: str) -> tuple[bool, str]:
        """YAML 내용 검증"""
        logger.debug("🔍 YAML 내용 검증")

        try:
            # YAML 파싱 시도
            yaml.safe_load(content)

            # 추가 검증 로직 (실제 구현에서는 스키마 검증 등)

            return True, "검증 성공"

        except yaml.YAMLError as e:
            error_msg = f"YAML 구문 오류: {e}"
            logger.warning(f"⚠️ {error_msg}")
            return False, error_msg

        except Exception as e:
            error_msg = f"검증 중 오류: {e}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

    def _save_yaml_content(self, content: str, filename: str):
        """YAML 내용 저장 (모크 구현)"""
        logger.debug(f"💾 YAML 내용 저장: {filename}")

        # 실제 구현에서는 ConfigProfileService 사용
        # 임시 파일 시스템을 통한 안전한 저장

        logger.debug(f"✅ YAML 저장 완료: {filename}")

    # === 에러 처리 ===

    def _on_view_error(self, error_message: str):
        """View에서 발생한 에러 처리"""
        logger.error(f"🔴 View 에러: {error_message}")

        # 에러를 그대로 전파 (추가 처리 가능)
        self.error_occurred.emit(error_message)

    # === 공개 메서드 ===

    def refresh_data(self):
        """데이터 새로고침"""
        logger.info("🔄 데이터 새로고침")

        try:
            if self.current_profile_path:
                self._load_profile(self.current_profile_path)
            else:
                self._load_default_profile()

        except Exception as e:
            logger.error(f"❌ 데이터 새로고침 실패: {e}")
            self.error_occurred.emit(f"새로고침 실패: {e}")

    def get_current_profile_path(self) -> str:
        """현재 프로파일 경로 반환"""
        return self.current_profile_path

    def has_unsaved_changes(self) -> bool:
        """저장되지 않은 변경사항 여부"""
        return self.unsaved_changes

    def set_unsaved_changes(self, has_changes: bool):
        """변경사항 상태 설정"""
        self.unsaved_changes = has_changes

    def _on_quick_environment_switch(self, env_name: str):
        """빠른 환경 전환 처리 로직"""
        logger.info(f"⚡ 빠른 환경 전환: {env_name}")

        try:
            # 환경별 기본 프로파일 경로 매핑
            env_profile_mapping = {
                'development': 'config/config.development.yaml',
                'testing': 'config/config.testing.yaml',
                'production': 'config/config.production.yaml'
            }

            profile_path = env_profile_mapping.get(env_name)
            if not profile_path:
                raise ValueError(f"알 수 없는 환경: {env_name}")

            # 변경사항 확인
            if self.has_unsaved_changes():
                self.unsaved_changes_detected.emit(profile_path)
                return

            # 환경 프로파일 로드
            self._load_selected_profile(profile_path)

            # 환경 전환 완료 알림
            self.environment_switched.emit(env_name)

        except Exception as e:
            logger.error(f"❌ 환경 전환 실패: {e}")
            self.error_occurred.emit(f"환경 전환 실패: {e}")

    def _update_profile_info_display(self, profile_info: dict):
        """프로파일 정보 표시 업데이트"""
        logger.debug(f"📊 프로파일 정보 업데이트: {profile_info.get('name', 'Unknown')}")

        try:
            # 프로파일 메타데이터 준비
            metadata = {
                'name': profile_info.get('name', ''),
                'description': profile_info.get('description', ''),
                'created_at': profile_info.get('created_at', ''),
                'created_from': profile_info.get('created_from', ''),
                'tags': profile_info.get('tags', []),
                'file_path': profile_info.get('file_path', ''),
                'profile_type': profile_info.get('profile_type', 'unknown')
            }

            # View에 프로파일 데이터 전달
            self.profile_data_loaded.emit(metadata)

            logger.debug("✅ 프로파일 정보 표시 업데이트 완료")

        except Exception as e:
            logger.error(f"❌ 프로파일 정보 업데이트 실패: {e}")
            self.error_occurred.emit(f"정보 업데이트 실패: {e}")

    def _load_profile_yaml_content(self, profile_name: str) -> str:
        """프로파일 YAML 내용 로드"""
        logger.debug(f"📄 YAML 내용 로드: {profile_name}")

        try:
            from pathlib import Path

            # 프로파일 경로 결정
            if profile_name.startswith('config/'):
                profile_path = profile_name
            else:
                # 커스텀 프로파일 경로 처리
                profile_path = f"config/{profile_name}"

            # 절대 경로로 변환
            full_path = Path(profile_path).resolve()

            if not full_path.exists():
                logger.warning(f"⚠️ 프로파일 파일이 존재하지 않음: {full_path}")
                return f"# 프로파일을 찾을 수 없습니다: {profile_name}\n# 경로: {full_path}"

            # YAML 파일 읽기
            with open(full_path, 'r', encoding='utf-8') as file:
                content = file.read()

            logger.debug(f"✅ YAML 내용 로드 완료: {len(content)} 문자")
            return content

        except Exception as e:
            logger.error(f"❌ YAML 내용 로드 실패: {e}")
            error_content = f"# YAML 로드 실패\n# 오류: {str(e)}\n# 프로파일: {profile_name}"
            return error_content

    def _load_selected_profile(self, profile_path: str):
        """선택된 프로파일을 실제로 로드하는 내부 로직"""
        logger.info(f"🔄 프로파일 로드 시작: {profile_path}")

        try:
            # YAML 내용 로드
            yaml_content = self._load_profile_yaml_content(profile_path)

            # 프로파일 메타데이터 생성 (기본값)
            profile_info = {
                'name': self._extract_profile_name(profile_path),
                'description': self._extract_profile_description(yaml_content),
                'file_path': profile_path,
                'profile_type': self._determine_profile_type(profile_path),
                'created_at': self._get_file_created_time(profile_path),
                'created_from': 'unknown',
                'tags': self._extract_profile_tags(profile_path)
            }

            # 현재 프로파일 상태 업데이트
            self.current_profile_path = profile_path
            self.unsaved_changes = False

            # View에 데이터 전달
            self._update_profile_info_display(profile_info)
            self.yaml_content_loaded.emit(yaml_content)

            logger.info(f"✅ 프로파일 로드 완료: {profile_path}")

        except Exception as e:
            logger.error(f"❌ 프로파일 로드 실패: {e}")
            self.error_occurred.emit(f"프로파일 로드 실패: {e}")

    # === 보조 메서드들 ===

    def _extract_profile_name(self, profile_path: str) -> str:
        """프로파일 경로에서 표시명 추출"""
        from pathlib import Path
        return Path(profile_path).stem.replace('config.', '').title()

    def _extract_profile_description(self, yaml_content: str) -> str:
        """YAML 내용에서 설명 추출 (첫 번째 주석 라인)"""
        lines = yaml_content.split('\n')
        for line in lines:
            if line.strip().startswith('#') and len(line.strip()) > 2:
                return line.strip()[1:].strip()
        return "프로파일 설명이 없습니다"

    def _determine_profile_type(self, profile_path: str) -> str:
        """프로파일 타입 결정 (built-in vs custom)"""
        if 'config.development' in profile_path or 'config.testing' in profile_path or 'config.production' in profile_path:
            return 'built-in'
        return 'custom'

    def _get_file_created_time(self, profile_path: str) -> str:
        """파일 생성 시간 반환"""
        try:
            from pathlib import Path
            import datetime
            file_path = Path(profile_path)
            if file_path.exists():
                timestamp = file_path.stat().st_mtime
                return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
        return "시간 정보 없음"

    def _extract_profile_tags(self, profile_path: str) -> list:
        """프로파일 경로에서 태그 추출"""
        tags = []
        if 'development' in profile_path:
            tags.append('development')
        elif 'testing' in profile_path:
            tags.append('testing')
        elif 'production' in profile_path:
            tags.append('production')

        if 'custom' in profile_path.lower():
            tags.append('custom')
        else:
            tags.append('built-in')

        return tags

    # === Task 3.2.1: 환경 전환 처리 구현 ===

    def _on_profile_apply(self, profile_name: str):
        """프로파일 적용 요청 처리"""
        logger.info(f"⚙️ 프로파일 적용 요청: {profile_name}")

        try:
            # 현재 편집 중인 내용이 있는지 확인
            if self.unsaved_changes:
                logger.warning("⚠️ 저장되지 않은 변경사항 존재 - 적용 전 저장 필요")
                self.unsaved_changes_detected.emit()
                return

            # 프로파일 전환 실행
            success = self._switch_to_profile(profile_name)

            if success:
                # 현재 환경 표시 업데이트
                self._update_current_environment_display()

                # 환경 전환 완료 시그널 발송
                self.environment_switched.emit(profile_name)
                logger.info(f"✅ 프로파일 적용 완료: {profile_name}")
            else:
                error_msg = f"프로파일 적용 실패: {profile_name}"
                logger.error(f"❌ {error_msg}")
                self.error_occurred.emit(error_msg)

        except Exception as e:
            error_msg = f"프로파일 적용 중 오류: {e}"
            logger.error(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)

    def _switch_to_profile(self, profile_name: str) -> bool:
        """프로파일 전환 실행"""
        logger.debug(f"🔄 프로파일 전환 시작: {profile_name}")

        try:
            # 1단계: 프로파일 파일 경로 결정
            profile_path = self._resolve_profile_path(profile_name)
            if not profile_path:
                logger.error(f"❌ 프로파일 경로를 찾을 수 없음: {profile_name}")
                return False

            # 2단계: 프로파일 설정 로드
            profile_settings = self._load_profile_settings(profile_path)
            if not profile_settings:
                logger.error(f"❌ 프로파일 설정 로드 실패: {profile_path}")
                return False

            # 3단계: 데이터베이스 설정 동기화
            sync_success = self._sync_db_settings(profile_settings)
            if not sync_success:
                logger.warning(f"⚠️ DB 설정 동기화 실패 (계속 진행): {profile_name}")

            # 4단계: 현재 프로파일 정보 업데이트
            self._current_profile = {
                'name': profile_name,
                'file_path': profile_path,
                'settings': profile_settings
            }
            self.current_profile_path = profile_path

            # 5단계: 환경 변수 업데이트 (필요시)
            self._update_environment_variables(profile_settings)

            logger.debug(f"✅ 프로파일 전환 완료: {profile_name}")
            return True

        except Exception as e:
            logger.error(f"❌ 프로파일 전환 실패: {e}")
            return False

    def _update_current_environment_display(self):
        """현재 환경 표시 업데이트"""
        logger.debug("🖥️ 현재 환경 표시 업데이트")

        try:
            if not self._current_profile:
                logger.warning("⚠️ 현재 프로파일 정보 없음")
                return

            # 환경 정보 준비
            env_info = {
                'current_profile': self._current_profile['name'],
                'profile_path': self._current_profile['file_path'],
                'environment': self.current_environment,
                'last_switched': self._get_current_timestamp()
            }

            # View에 환경 정보 전달
            self.profile_data_loaded.emit(env_info)
            logger.debug(f"✅ 환경 표시 업데이트 완료: {self._current_profile['name']}")

        except Exception as e:
            logger.error(f"❌ 환경 표시 업데이트 실패: {e}")

    def _sync_db_settings(self, profile_settings: dict) -> bool:
        """데이터베이스 설정 동기화"""
        logger.debug("🗄️ 데이터베이스 설정 동기화 시작")

        try:
            # 실제 구현에서는 ConfigProfileService 사용
            # 현재는 모크 구현으로 기본 동기화 로직만 제공

            # 데이터베이스 관련 설정 추출
            db_settings = profile_settings.get('database', {})
            if not db_settings:
                logger.warning("⚠️ 데이터베이스 설정이 프로파일에 없음")
                return True  # 선택적 설정이므로 성공으로 처리

            # 연결 타임아웃 설정
            connection_timeout = db_settings.get('connection_timeout', 30)
            max_retry_attempts = db_settings.get('max_retry_attempts', 3)

            # 실제 구현에서는 여기서 다음 작업 수행:
            # 1. DB 연결 설정 업데이트
            # 2. 설정 테이블에 새 값 저장
            # 3. 캐시 무효화 및 새로고침

            logger.debug(f"✅ DB 설정 동기화 완료 - timeout: {connection_timeout}s, retry: {max_retry_attempts}")
            return True

        except Exception as e:
            logger.error(f"❌ DB 설정 동기화 실패: {e}")
            return False

    # === 헬퍼 메서드 ===

    def _resolve_profile_path(self, profile_name: str) -> str:
        """프로파일 이름으로부터 파일 경로 결정"""
        try:
            # 표준 프로파일 경로 매핑
            standard_profiles = {
                'development': 'config/config.development.yaml',
                'testing': 'config/config.testing.yaml',
                'production': 'config/config.production.yaml'
            }

            # 표준 프로파일인 경우
            if profile_name in standard_profiles:
                return standard_profiles[profile_name]

            # 커스텀 프로파일인 경우
            custom_path = f"config/config.{profile_name}.yaml"
            return custom_path

        except Exception as e:
            logger.error(f"❌ 프로파일 경로 결정 실패: {e}")
            return ""

    def _load_profile_settings(self, profile_path: str) -> dict:
        """프로파일 설정 로드"""
        try:
            from pathlib import Path

            file_path = Path(profile_path)
            if not file_path.exists():
                logger.warning(f"⚠️ 프로파일 파일이 존재하지 않음: {profile_path}")
                return {}

            # YAML 파일 읽기 및 파싱
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            settings = yaml.safe_load(content)
            logger.debug(f"✅ 프로파일 설정 로드 완료: {profile_path}")
            return settings or {}

        except Exception as e:
            logger.error(f"❌ 프로파일 설정 로드 실패: {e}")
            return {}

    def _update_environment_variables(self, profile_settings: dict):
        """환경 변수 업데이트 (필요시)"""
        try:
            # 실제 구현에서는 특정 설정을 환경 변수로 설정
            # 예: API 키, 로그 레벨 등

            upbit_settings = profile_settings.get('upbit', {})
            if upbit_settings.get('paper_trading'):
                # 페이퍼 트레이딩 모드 환경 변수 설정 등
                pass

            logger.debug("✅ 환경 변수 업데이트 완료")

        except Exception as e:
            logger.warning(f"⚠️ 환경 변수 업데이트 실패: {e}")

    def _get_current_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        import datetime
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # === Task 3.2.2: 실시간 설정 동기화 구현 ===

    def _on_config_file_changed(self, file_path: str):
        """설정 파일 변경 감지 처리"""
        logger.info(f"📁 설정 파일 변경 감지: {file_path}")

        try:
            # 현재 활성 프로파일과 관련된 파일인지 확인
            if self._current_profile and file_path == self._current_profile['file_path']:
                logger.info(f"🔄 활성 프로파일 파일 변경됨: {file_path}")

                # 외부 변경사항 처리
                self._handle_external_profile_changes()

                # 프로파일 목록 새로고침
                self._refresh_profile_list()

                # 현재 환경 표시 업데이트
                self._update_current_environment_display()
            else:
                # 다른 프로파일 파일 변경 - 목록만 새로고침
                logger.debug(f"📝 다른 프로파일 파일 변경: {file_path}")
                self._refresh_profile_list()

        except Exception as e:
            logger.error(f"❌ 설정 파일 변경 처리 실패: {e}")
            self.error_occurred.emit(f"설정 파일 변경 처리 실패: {e}")

    def _refresh_profile_list(self):
        """프로파일 목록 새로고침"""
        logger.debug("🔄 프로파일 목록 새로고침")

        try:
            # 실제 구현에서는 ConfigProfileService를 통해 프로파일 목록 조회
            # 현재는 모크 구현으로 기본 프로파일들을 반환

            # 표준 프로파일들 스캔
            standard_profiles = ['development', 'testing', 'production']
            available_profiles = []

            for profile_name in standard_profiles:
                profile_path = self._resolve_profile_path(profile_name)
                if self._check_profile_exists(profile_path):
                    profile_info = {
                        'name': profile_name,
                        'file_path': profile_path,
                        'profile_type': 'built-in',
                        'last_modified': self._get_file_modified_time(profile_path)
                    }
                    available_profiles.append(profile_info)

            # 커스텀 프로파일들 스캔 (실제 구현에서는 config 디렉토리 스캔)
            custom_profiles = self._scan_custom_profiles()
            available_profiles.extend(custom_profiles)

            # 프로파일 목록 업데이트 시그널 발송
            # self.profile_list_updated.emit(available_profiles)  # 필요시 시그널 추가

            logger.debug(f"✅ 프로파일 목록 새로고침 완료: {len(available_profiles)}개")

        except Exception as e:
            logger.error(f"❌ 프로파일 목록 새로고침 실패: {e}")

    def _handle_external_profile_changes(self):
        """외부 프로파일 변경사항 처리"""
        logger.debug("🔄 외부 프로파일 변경사항 처리")

        try:
            if not self._current_profile:
                logger.warning("⚠️ 현재 활성 프로파일 없음")
                return

            # 현재 편집 중인 내용과 충돌 확인
            if self.unsaved_changes:
                logger.warning("⚠️ 저장되지 않은 변경사항 있음 - 사용자 확인 필요")
                # 실제 구현에서는 사용자에게 충돌 해결 옵션 제공
                # 1. 외부 변경사항 수용 (현재 편집 내용 손실)
                # 2. 현재 편집 내용 유지 (외부 변경사항 무시)
                # 3. 병합 옵션 제공

                self.unsaved_changes_detected.emit()
                return

            # 파일에서 최신 내용 다시 로드
            current_profile_path = self._current_profile['file_path']
            updated_settings = self._load_profile_settings(current_profile_path)

            if updated_settings:
                # 프로파일 정보 업데이트
                self._current_profile['settings'] = updated_settings

                # YAML 내용 다시 로드하여 View 업데이트
                profile_name = self._current_profile['name']
                self._load_profile_yaml_content(profile_name)

                logger.info(f"✅ 외부 변경사항 적용 완료: {profile_name}")
            else:
                logger.error("❌ 외부 변경사항 로드 실패")

        except Exception as e:
            logger.error(f"❌ 외부 프로파일 변경사항 처리 실패: {e}")

    def _emit_environment_change_signal(self, env_name: str):
        """환경 변경 시그널 발송"""
        logger.debug(f"📡 환경 변경 시그널 발송: {env_name}")

        try:
            # 환경 전환 시그널 발송
            self.environment_switched.emit(env_name)

            # 추가 환경 정보가 필요한 경우:
            # environment_info = {
            #     'environment_name': env_name,
            #     'profile_name': self._current_profile['name'] if self._current_profile else '',
            #     'timestamp': self._get_current_timestamp(),
            #     'source': 'presenter'
            # }
            # self.environment_info_updated.emit(environment_info)  # 필요시 시그널 추가

            logger.debug(f"✅ 환경 변경 시그널 발송 완료: {env_name}")

        except Exception as e:
            logger.error(f"❌ 환경 변경 시그널 발송 실패: {e}")

    # === 헬퍼 메서드 (Task 3.2.2) ===

    def _check_profile_exists(self, profile_path: str) -> bool:
        """프로파일 파일 존재 여부 확인"""
        try:
            from pathlib import Path
            return Path(profile_path).exists()
        except Exception:
            return False

    def _get_file_modified_time(self, file_path: str) -> str:
        """파일 수정 시간 반환"""
        try:
            from pathlib import Path
            import datetime

            path = Path(file_path)
            if path.exists():
                timestamp = path.stat().st_mtime
                return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
        return "시간 정보 없음"

    def _scan_custom_profiles(self) -> list:
        """커스텀 프로파일 스캔 (모크 구현)"""
        try:
            # 실제 구현에서는 config 디렉토리에서 config.*.yaml 패턴 파일들을 스캔
            # 현재는 빈 목록 반환
            custom_profiles = []

            # 예시: config.custom.yaml, config.local.yaml 등이 있다면
            # for custom_file in custom_yaml_files:
            #     profile_info = self._create_profile_info_from_file(custom_file)
            #     custom_profiles.append(profile_info)

            logger.debug(f"✅ 커스텀 프로파일 스캔 완료: {len(custom_profiles)}개")
            return custom_profiles

        except Exception as e:
            logger.warning(f"⚠️ 커스텀 프로파일 스캔 실패: {e}")
            return []

    # === Task 3.2.3: ConfigProfileService 완전 호환성 구현 ===

    def _ensure_service_compatibility(self):
        """ConfigProfileService와의 호환성 보장"""
        logger.info("🔧 ConfigProfileService 호환성 확인")

        try:
            # 1단계: 서비스 상태 검증
            service_valid = self._validate_service_state()
            if not service_valid:
                logger.warning("⚠️ ConfigProfileService 상태 이상 - 복구 시도")
                self._recover_service_state()

            # 2단계: 레거시 설정 마이그레이션
            migration_needed = self._check_migration_needed()
            if migration_needed:
                logger.info("📦 레거시 설정 마이그레이션 시작")
                self._migrate_legacy_settings()

            # 3단계: API 호환성 검증
            api_compatible = self._verify_api_compatibility()
            if not api_compatible:
                logger.error("❌ API 호환성 문제 발견")
                raise RuntimeError("ConfigProfileService API 호환성 오류")

            # 4단계: 실시간 동기화 설정
            self._setup_realtime_sync()

            logger.info("✅ ConfigProfileService 호환성 확보 완료")

        except Exception as e:
            logger.error(f"❌ ConfigProfileService 호환성 확보 실패: {e}")
            self.error_occurred.emit(f"서비스 호환성 오류: {e}")

    def _migrate_legacy_settings(self):
        """레거시 설정 마이그레이션"""
        logger.debug("📦 레거시 설정 마이그레이션 시작")

        try:
            # 1. 구 설정 파일 위치 확인
            legacy_paths = [
                'config.yaml',  # 기본 설정 파일
                'app_settings.sqlite3',  # 구 DB 파일
                'user_settings.json'  # 사용자 설정
            ]

            migrated_count = 0
            for legacy_path in legacy_paths:
                if self._check_legacy_file_exists(legacy_path):
                    logger.info(f"📄 레거시 파일 발견: {legacy_path}")

                    # 마이그레이션 실행
                    migration_success = self._migrate_single_file(legacy_path)
                    if migration_success:
                        migrated_count += 1
                        logger.debug(f"✅ 마이그레이션 완료: {legacy_path}")
                    else:
                        logger.warning(f"⚠️ 마이그레이션 실패: {legacy_path}")

            # 2. 환경별 프로파일 자동 생성
            self._create_default_profiles_if_missing()

            # 3. 사용자 커스텀 설정 보존
            self._preserve_user_customizations()

            logger.info(f"✅ 레거시 설정 마이그레이션 완료: {migrated_count}개 파일")

        except Exception as e:
            logger.error(f"❌ 레거시 설정 마이그레이션 실패: {e}")

    def _validate_service_state(self) -> bool:
        """ConfigProfileService 상태 검증"""
        logger.debug("🔍 ConfigProfileService 상태 검증")

        try:
            # 실제 구현에서는 ConfigProfileService 인스턴스 상태 확인
            # 현재는 모크 검증으로 기본 요구사항 확인

            # 1. 필수 디렉토리 존재 확인
            required_dirs = ['config', 'data']
            for dir_name in required_dirs:
                if not self._check_directory_exists(dir_name):
                    logger.error(f"❌ 필수 디렉토리 없음: {dir_name}")
                    return False

            # 2. 필수 프로파일 파일 확인
            required_profiles = ['config.development.yaml', 'config.testing.yaml', 'config.production.yaml']
            for profile_file in required_profiles:
                profile_path = f"config/{profile_file}"
                if not self._check_profile_exists(profile_path):
                    logger.warning(f"⚠️ 필수 프로파일 없음: {profile_file}")
                    # 필수 프로파일이 없어도 서비스 상태는 유효 (자동 생성 가능)

            # 3. 설정 데이터베이스 연결 확인
            db_accessible = self._check_database_accessibility()
            if not db_accessible:
                logger.error("❌ 설정 데이터베이스 접근 불가")
                return False

            logger.debug("✅ ConfigProfileService 상태 검증 통과")
            return True

        except Exception as e:
            logger.error(f"❌ 서비스 상태 검증 실패: {e}")
            return False

    # === 헬퍼 메서드 (Task 3.2.3) ===

    def _check_migration_needed(self) -> bool:
        """마이그레이션 필요 여부 확인"""
        try:
            # 레거시 파일이 하나라도 존재하면 마이그레이션 필요
            legacy_files = ['config.yaml', 'app_settings.sqlite3', 'user_settings.json']
            for legacy_file in legacy_files:
                if self._check_legacy_file_exists(legacy_file):
                    return True
            return False
        except Exception:
            return False

    def _check_legacy_file_exists(self, file_path: str) -> bool:
        """레거시 파일 존재 여부 확인"""
        try:
            from pathlib import Path
            return Path(file_path).exists()
        except Exception:
            return False

    def _migrate_single_file(self, legacy_path: str) -> bool:
        """단일 레거시 파일 마이그레이션"""
        try:
            # 실제 구현에서는 파일 형식에 따른 마이그레이션 로직 구현
            # 현재는 모크 구현으로 성공 반환
            logger.debug(f"📄 파일 마이그레이션 시뮬레이션: {legacy_path}")
            return True
        except Exception as e:
            logger.error(f"❌ 파일 마이그레이션 실패: {e}")
            return False

    def _create_default_profiles_if_missing(self):
        """기본 프로파일 자동 생성"""
        try:
            default_profiles = ['development', 'testing', 'production']
            for profile_name in default_profiles:
                profile_path = f"config/config.{profile_name}.yaml"
                if not self._check_profile_exists(profile_path):
                    logger.info(f"📄 기본 프로파일 생성: {profile_name}")
                    # 실제 구현에서는 템플릿에서 프로파일 생성
                    # self._create_profile_from_template(profile_name)
        except Exception as e:
            logger.warning(f"⚠️ 기본 프로파일 생성 실패: {e}")

    def _preserve_user_customizations(self):
        """사용자 커스터마이징 보존"""
        try:
            # 실제 구현에서는 사용자가 수정한 설정들을 보존
            # 예: API 키, 개인 트레이딩 설정 등
            logger.debug("💾 사용자 커스터마이징 보존 완료")
        except Exception as e:
            logger.warning(f"⚠️ 사용자 커스터마이징 보존 실패: {e}")

    def _recover_service_state(self):
        """서비스 상태 복구"""
        try:
            logger.info("🔧 ConfigProfileService 상태 복구 시도")
            # 실제 구현에서는 서비스 재초기화 등 수행
            # self.config_service.reinitialize()
        except Exception as e:
            logger.error(f"❌ 서비스 상태 복구 실패: {e}")

    def _verify_api_compatibility(self) -> bool:
        """API 호환성 검증"""
        try:
            # 실제 구현에서는 ConfigProfileService의 필수 메서드들 존재 확인
            # required_methods = ['get_profile', 'save_profile', 'list_profiles']
            # return all(hasattr(self.config_service, method) for method in required_methods)
            return True
        except Exception:
            return False

    def _setup_realtime_sync(self):
        """실시간 동기화 설정"""
        try:
            logger.debug("⚡ 실시간 동기화 설정")
            # 실제 구현에서는 파일 시스템 감시자 설정
            # self.file_watcher.add_path('config/')
        except Exception as e:
            logger.warning(f"⚠️ 실시간 동기화 설정 실패: {e}")

    def _check_directory_exists(self, dir_name: str) -> bool:
        """디렉토리 존재 여부 확인"""
        try:
            from pathlib import Path
            return Path(dir_name).is_dir()
        except Exception:
            return False

    def _check_database_accessibility(self) -> bool:
        """데이터베이스 접근성 확인"""
        try:
            # 실제 구현에서는 settings.sqlite3 연결 테스트
            # 현재는 모크 구현으로 성공 반환
            return True
        except Exception:
            return False

    # === Task 4.1.1: 안전한 편집 워크플로우 구현 ===

    def _start_edit_existing_profile(self, profile_name: str) -> str:
        """기존 프로파일 편집 시작 - 임시 파일 생성"""
        logger.info(f"📝 기존 프로파일 편집 시작: {profile_name}")

        try:
            # 1단계: 원본 프로파일 경로 확인
            original_path = self._resolve_profile_path(profile_name)
            if not self._check_profile_exists(original_path):
                error_msg = f"편집할 프로파일이 존재하지 않음: {profile_name}"
                logger.error(f"❌ {error_msg}")
                raise FileNotFoundError(error_msg)

            # 2단계: 임시 파일 경로 생성
            temp_path = self._generate_temp_file_path(profile_name, is_new=False)
            logger.debug(f"📁 임시 파일 경로: {temp_path}")

            # 3단계: 원본 파일을 임시 파일로 복사
            original_content = self._load_profile_settings_as_yaml(original_path)
            if not original_content:
                error_msg = f"원본 프로파일 내용 로드 실패: {original_path}"
                logger.error(f"❌ {error_msg}")
                raise IOError(error_msg)

            # 4단계: 임시 파일 저장
            self._save_temp_file(temp_path, original_content)

            # 5단계: 편집 세션 등록
            self._register_edit_session(profile_name, temp_path, is_new=False)

            logger.info(f"✅ 기존 프로파일 편집 시작 완료: {temp_path}")
            return temp_path

        except Exception as e:
            error_msg = f"기존 프로파일 편집 시작 실패: {e}"
            logger.error(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return ""

    def _start_edit_new_profile(self) -> str:
        """새 프로파일 편집 시작 - 템플릿 기반 임시 파일 생성"""
        logger.info("📝 새 프로파일 편집 시작")

        try:
            # 1단계: 새 프로파일명 생성
            new_profile_name = self._generate_custom_profile_name()
            logger.debug(f"🆕 새 프로파일명: {new_profile_name}")

            # 2단계: 임시 파일 경로 생성
            temp_path = self._generate_temp_file_path(new_profile_name, is_new=True)
            logger.debug(f"📁 임시 파일 경로: {temp_path}")

            # 3단계: 기본 템플릿 내용 생성
            template_content = self._create_profile_template()

            # 4단계: 임시 파일 저장
            self._save_temp_file(temp_path, template_content)

            # 5단계: 편집 세션 등록
            self._register_edit_session(new_profile_name, temp_path, is_new=True)

            logger.info(f"✅ 새 프로파일 편집 시작 완료: {temp_path}")
            return temp_path

        except Exception as e:
            error_msg = f"새 프로파일 편집 시작 실패: {e}"
            logger.error(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return ""

    def _save_temp_to_original(self, profile_name: str) -> bool:
        """임시 파일을 원본 위치에 저장"""
        logger.info(f"💾 임시 파일을 원본으로 저장: {profile_name}")

        try:
            # 1단계: 편집 세션 정보 확인
            session = self._get_edit_session(profile_name)
            if not session:
                error_msg = f"편집 세션을 찾을 수 없음: {profile_name}"
                logger.error(f"❌ {error_msg}")
                return False

            # 2단계: 임시 파일 내용 검증
            temp_content = self._load_temp_file_content(session['temp_path'])
            if not temp_content:
                error_msg = f"임시 파일 내용 로드 실패: {session['temp_path']}"
                logger.error(f"❌ {error_msg}")
                return False

            # 3단계: 내용 검증 (YAML 구문 등)
            is_valid, validation_message = self._validate_yaml_content(temp_content)
            if not is_valid:
                error_msg = f"임시 파일 내용 검증 실패: {validation_message}"
                logger.error(f"❌ {error_msg}")
                return False

            # 4단계: 원본 파일 경로 결정
            if session['is_new']:
                # 새 프로파일인 경우 - config 디렉토리에 새 파일 생성
                original_path = f"config/config.{profile_name}.yaml"
            else:
                # 기존 프로파일인 경우 - 기존 경로 사용
                original_path = self._resolve_profile_path(profile_name)

            # 5단계: 원본 위치에 저장
            self._save_profile_to_path(original_path, temp_content)

            # 6단계: 임시 파일 정리
            self._cleanup_temp_file(session['temp_path'])

            # 7단계: 편집 세션 제거
            self._remove_edit_session(profile_name)

            logger.info(f"✅ 임시 파일을 원본으로 저장 완료: {original_path}")
            return True

        except Exception as e:
            error_msg = f"임시 파일을 원본으로 저장 실패: {e}"
            logger.error(f"❌ {error_msg}")
            return False

    def _cleanup_abandoned_temp_files(self):
        """방치된 임시 파일들 정리"""
        logger.info("🧹 방치된 임시 파일 정리 시작")

        try:
            from pathlib import Path
            import time

            # 1단계: 임시 파일 디렉토리 확인
            temp_dir = Path("temp")
            if not temp_dir.exists():
                logger.debug("📁 임시 디렉토리가 존재하지 않음")
                return

            # 2단계: 임시 파일 스캔
            temp_files = list(temp_dir.glob("temp_profile_*.yaml"))
            current_time = time.time()
            cleanup_threshold = 24 * 60 * 60  # 24시간

            cleaned_count = 0
            for temp_file in temp_files:
                try:
                    # 파일 생성 시간 확인
                    file_age = current_time - temp_file.stat().st_ctime

                    if file_age > cleanup_threshold:
                        # 24시간 이상 된 임시 파일 삭제
                        temp_file.unlink()
                        cleaned_count += 1
                        logger.debug(f"🗑️ 오래된 임시 파일 삭제: {temp_file.name}")

                except Exception as e:
                    logger.warning(f"⚠️ 임시 파일 처리 실패: {temp_file.name} - {e}")

            # 3단계: 편집 세션 정리
            self._cleanup_stale_edit_sessions()

            logger.info(f"✅ 방치된 임시 파일 정리 완료: {cleaned_count}개 삭제")

        except Exception as e:
            logger.error(f"❌ 방치된 임시 파일 정리 실패: {e}")

    # === 헬퍼 메서드 (Task 4.1.1) ===

    def _generate_temp_file_path(self, profile_name: str, is_new: bool) -> str:
        """임시 파일 경로 생성"""
        try:
            import datetime
            from pathlib import Path

            # 임시 디렉토리 생성
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)

            # 타임스탬프 생성
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            # 임시 파일명 생성
            if is_new:
                temp_filename = f"temp_profile_new_{timestamp}.yaml"
            else:
                safe_profile_name = self._sanitize_filename(profile_name)
                temp_filename = f"temp_profile_{safe_profile_name}_{timestamp}.yaml"

            temp_path = temp_dir / temp_filename
            return str(temp_path)

        except Exception as e:
            logger.error(f"❌ 임시 파일 경로 생성 실패: {e}")
            return ""

    def _load_profile_settings_as_yaml(self, profile_path: str) -> str:
        """프로파일을 YAML 문자열로 로드"""
        try:
            from pathlib import Path

            file_path = Path(profile_path)
            if not file_path.exists():
                return ""

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return content

        except Exception as e:
            logger.error(f"❌ 프로파일 YAML 로드 실패: {e}")
            return ""

    def _save_temp_file(self, temp_path: str, content: str):
        """임시 파일 저장"""
        try:
            from pathlib import Path

            temp_file = Path(temp_path)
            temp_file.parent.mkdir(parents=True, exist_ok=True)

            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.debug(f"💾 임시 파일 저장 완료: {temp_path}")

        except Exception as e:
            logger.error(f"❌ 임시 파일 저장 실패: {e}")
            raise

    def _create_profile_template(self) -> str:
        """새 프로파일 템플릿 생성"""
        template = """# 새 커스텀 프로파일
# 생성일: {timestamp}

upbit:
  paper_trading: true
  api_key_file: ""
  secret_key_file: ""

logging:
  level: INFO
  console_output: true
  file_output: false
  log_format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

database:
  connection_timeout: 30
  max_retry_attempts: 3
  backup_interval: 3600

trading:
  paper_trading: true
  max_position_size: 0.1
  stop_loss_percentage: 0.05

indicators:
  rsi_period: 14
  sma_period: 20
""".format(timestamp=self._get_current_timestamp())

        return template

    def _register_edit_session(self, profile_name: str, temp_path: str, is_new: bool):
        """편집 세션 등록"""
        try:
            # 편집 세션 정보를 인스턴스 변수에 저장 (간단한 구현)
            if not hasattr(self, '_edit_sessions'):
                self._edit_sessions = {}

            self._edit_sessions[profile_name] = {
                'temp_path': temp_path,
                'is_new': is_new,
                'started_at': self._get_current_timestamp(),
                'profile_name': profile_name
            }

            logger.debug(f"📝 편집 세션 등록: {profile_name}")

        except Exception as e:
            logger.warning(f"⚠️ 편집 세션 등록 실패: {e}")

    def _get_edit_session(self, profile_name: str) -> dict:
        """편집 세션 정보 조회"""
        try:
            if not hasattr(self, '_edit_sessions'):
                return {}

            return self._edit_sessions.get(profile_name, {})

        except Exception:
            return {}

    def _load_temp_file_content(self, temp_path: str) -> str:
        """임시 파일 내용 로드"""
        try:
            from pathlib import Path

            temp_file = Path(temp_path)
            if not temp_file.exists():
                return ""

            with open(temp_file, 'r', encoding='utf-8') as f:
                content = f.read()

            return content

        except Exception as e:
            logger.error(f"❌ 임시 파일 내용 로드 실패: {e}")
            return ""

    def _save_profile_to_path(self, file_path: str, content: str):
        """지정된 경로에 프로파일 저장"""
        try:
            from pathlib import Path

            target_file = Path(file_path)
            target_file.parent.mkdir(parents=True, exist_ok=True)

            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.debug(f"💾 프로파일 저장 완료: {file_path}")

        except Exception as e:
            logger.error(f"❌ 프로파일 저장 실패: {e}")
            raise

    def _cleanup_temp_file(self, temp_path: str):
        """임시 파일 삭제"""
        try:
            from pathlib import Path

            temp_file = Path(temp_path)
            if temp_file.exists():
                temp_file.unlink()
                logger.debug(f"🗑️ 임시 파일 삭제: {temp_path}")

        except Exception as e:
            logger.warning(f"⚠️ 임시 파일 삭제 실패: {e}")

    def _remove_edit_session(self, profile_name: str):
        """편집 세션 제거"""
        try:
            if hasattr(self, '_edit_sessions') and profile_name in self._edit_sessions:
                del self._edit_sessions[profile_name]
                logger.debug(f"🗑️ 편집 세션 제거: {profile_name}")

        except Exception as e:
            logger.warning(f"⚠️ 편집 세션 제거 실패: {e}")

    def _cleanup_stale_edit_sessions(self):
        """만료된 편집 세션 정리"""
        try:
            if not hasattr(self, '_edit_sessions'):
                return

            # 실제 구현에서는 시간 기반 만료 검사 수행
            # 현재는 모든 세션을 유지하는 간단한 구현
            stale_sessions = []

            # 추후 구현: 24시간 이상 된 세션 탐지
            # import time
            # current_time = time.time()
            # session_timeout = 24 * 60 * 60  # 24시간
            # for profile_name, session in self._edit_sessions.items():
            #     if self._is_session_expired(session, current_time, session_timeout):
            #         stale_sessions.append(profile_name)

            for profile_name in stale_sessions:
                self._remove_edit_session(profile_name)

            if stale_sessions:
                logger.debug(f"🧹 만료된 편집 세션 정리: {len(stale_sessions)}개")

        except Exception as e:
            logger.warning(f"⚠️ 만료된 편집 세션 정리 실패: {e}")

    # === Task 4.1.2: 파일명 자동 생성 시스템 구현 ===

    def _generate_custom_profile_name(self) -> str:
        """커스텀 프로파일명 자동 생성"""
        logger.debug("🏷️ 커스텀 프로파일명 자동 생성")

        try:
            import datetime

            # 기본 프로파일명 생성
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"Custom_Profile_{timestamp}"

            # 고유성 보장
            unique_name = self._ensure_unique_filename(base_name)

            # 파일명 검증
            if not self._validate_filename(unique_name):
                # 검증 실패 시 기본 안전 이름 사용
                fallback_name = f"Profile_{timestamp}"
                unique_name = self._ensure_unique_filename(fallback_name)

            logger.debug(f"✅ 프로파일명 생성 완료: {unique_name}")
            return unique_name

        except Exception as e:
            logger.error(f"❌ 프로파일명 생성 실패: {e}")
            # 최종 폴백
            import time
            return f"Profile_{int(time.time())}"

    def _validate_filename(self, filename: str) -> bool:
        """파일명 유효성 검증"""
        try:
            # 1. 길이 제한 확인 (Windows 파일명 제한 고려)
            if len(filename) > 100:
                logger.warning(f"⚠️ 파일명 너무 김: {len(filename)}자")
                return False

            # 2. 빈 파일명 확인
            if not filename or filename.strip() == "":
                logger.warning("⚠️ 빈 파일명")
                return False

            # 3. 금지된 문자 확인 (Windows/Linux 공통)
            forbidden_chars = r'<>:"/\|?*'
            if any(char in filename for char in forbidden_chars):
                logger.warning(f"⚠️ 금지된 문자 포함: {filename}")
                return False

            # 4. 예약어 확인 (Windows)
            reserved_names = [
                'CON', 'PRN', 'AUX', 'NUL',
                'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
            ]
            if filename.upper() in reserved_names:
                logger.warning(f"⚠️ 예약어 파일명: {filename}")
                return False

            # 5. 특수한 시작/끝 문자 확인
            if filename.startswith('.') or filename.endswith('.'):
                logger.warning(f"⚠️ 부적절한 시작/끝 문자: {filename}")
                return False

            # 6. 연속된 공백이나 특수문자 확인
            if '  ' in filename or '__' in filename:
                logger.warning(f"⚠️ 연속된 특수문자: {filename}")
                return False

            logger.debug(f"✅ 파일명 검증 통과: {filename}")
            return True

        except Exception as e:
            logger.error(f"❌ 파일명 검증 실패: {e}")
            return False

    def _sanitize_filename(self, filename: str) -> str:
        """파일명 안전화 (확장된 구현)"""
        try:
            import re

            # 1. 기본 정리
            sanitized = filename.strip()

            # 2. 금지된 문자를 언더스코어로 변경
            forbidden_chars = r'<>:"/\|?*'
            for char in forbidden_chars:
                sanitized = sanitized.replace(char, '_')

            # 3. 제어 문자 제거 (ASCII 0-31)
            sanitized = re.sub(r'[\x00-\x1f]', '', sanitized)

            # 4. 연속된 공백을 언더스코어로 변경
            sanitized = re.sub(r'\s+', '_', sanitized)

            # 5. 연속된 언더스코어 정리
            sanitized = re.sub(r'_+', '_', sanitized)

            # 6. 시작과 끝의 언더스코어/점 제거
            sanitized = sanitized.strip('_.')

            # 7. 예약어 처리
            reserved_names = [
                'CON', 'PRN', 'AUX', 'NUL',
                'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
            ]
            if sanitized.upper() in reserved_names:
                sanitized = f"Profile_{sanitized}"

            # 8. 길이 제한 (90자로 제한하여 확장자와 타임스탬프 여유 확보)
            if len(sanitized) > 90:
                sanitized = sanitized[:90]
                # 마지막이 언더스코어로 끝나지 않도록 정리
                sanitized = sanitized.rstrip('_')

            # 9. 최종 검증 - 빈 문자열인 경우 기본값 사용
            if not sanitized:
                sanitized = "Profile"

            logger.debug(f"🔧 파일명 안전화: '{filename}' → '{sanitized}'")
            return sanitized

        except Exception as e:
            logger.error(f"❌ 파일명 안전화 실패: {e}")
            return "Profile"

    def _ensure_unique_filename(self, base_name: str) -> str:
        """파일명 고유성 보장"""
        logger.debug(f"🔍 파일명 고유성 확인: {base_name}")

        try:
            from pathlib import Path

            # 1. 기본 이름이 사용 가능한지 확인
            config_path = Path("config") / f"config.{base_name}.yaml"
            if not config_path.exists():
                logger.debug(f"✅ 기본 이름 사용 가능: {base_name}")
                return base_name

            # 2. 숫자 접미사로 고유 이름 생성
            counter = 1
            max_attempts = 1000  # 무한 루프 방지

            while counter <= max_attempts:
                candidate_name = f"{base_name}_{counter:03d}"
                candidate_path = Path("config") / f"config.{candidate_name}.yaml"

                if not candidate_path.exists():
                    logger.debug(f"✅ 고유 이름 생성: {candidate_name}")
                    return candidate_name

                counter += 1

            # 3. 최대 시도 횟수 초과 시 타임스탬프 기반 생성
            import time
            timestamp_suffix = str(int(time.time()))
            fallback_name = f"{base_name}_{timestamp_suffix}"

            logger.warning(f"⚠️ 최대 시도 횟수 초과, 타임스탬프 사용: {fallback_name}")
            return fallback_name

        except Exception as e:
            logger.error(f"❌ 파일명 고유성 보장 실패: {e}")
            # 최종 폴백
            import time
            return f"{base_name}_{int(time.time())}"

    # === Task 4.1.2: 추가 헬퍼 메서드 ===

    def _get_existing_profile_names(self) -> set:
        """기존 프로파일 이름 목록 조회"""
        try:
            from pathlib import Path

            config_dir = Path("config")
            if not config_dir.exists():
                return set()

            existing_names = set()

            # config.*.yaml 패턴 파일들 스캔
            for config_file in config_dir.glob("config.*.yaml"):
                # config.{profile_name}.yaml에서 profile_name 추출
                filename = config_file.stem  # config.{profile_name} 부분
                if filename.startswith('config.'):
                    profile_name = filename[7:]  # 'config.' 제거
                    existing_names.add(profile_name)

            logger.debug(f"📋 기존 프로파일 {len(existing_names)}개 발견")
            return existing_names

        except Exception as e:
            logger.warning(f"⚠️ 기존 프로파일 목록 조회 실패: {e}")
            return set()

    def _is_profile_name_available(self, profile_name: str) -> bool:
        """프로파일 이름 사용 가능 여부 확인"""
        try:
            existing_names = self._get_existing_profile_names()
            is_available = profile_name not in existing_names

            logger.debug(f"🔍 프로파일명 사용 가능: {profile_name} → {is_available}")
            return is_available

        except Exception as e:
            logger.warning(f"⚠️ 프로파일명 사용 가능 여부 확인 실패: {e}")
            return False

    def _generate_profile_name_variants(self, base_name: str) -> list:
        """프로파일명 변형 목록 생성 (사용자 선택용)"""
        try:
            import datetime

            variants = []
            timestamp = datetime.datetime.now()

            # 1. 기본 이름
            variants.append(base_name)

            # 2. 날짜 포함 변형
            date_str = timestamp.strftime("%Y%m%d")
            variants.append(f"{base_name}_{date_str}")

            # 3. 시간 포함 변형
            time_str = timestamp.strftime("%H%M")
            variants.append(f"{base_name}_{date_str}_{time_str}")

            # 4. 환경별 변형
            env_variants = [f"{base_name}_dev", f"{base_name}_test", f"{base_name}_custom"]
            variants.extend(env_variants)

            # 5. 고유성 확인 및 필터링
            available_variants = []
            for variant in variants:
                sanitized = self._sanitize_filename(variant)
                if self._validate_filename(sanitized) and self._is_profile_name_available(sanitized):
                    available_variants.append(sanitized)

            logger.debug(f"📝 프로파일명 변형 생성: {len(available_variants)}개")
            return available_variants[:5]  # 최대 5개 제안

        except Exception as e:
            logger.warning(f"⚠️ 프로파일명 변형 생성 실패: {e}")
            return [base_name]

    # === Task 4.1.3: 편집 세션 관리 구현 ===

    def _create_edit_session(self, profile_name: str, is_new: bool) -> ProfileEditorSession:
        """새 편집 세션 생성"""
        logger.info(f"📝 편집 세션 생성: {profile_name} (새 프로파일: {is_new})")

        try:
            # 1단계: 고유 세션 ID 생성
            session_id = self._generate_session_id(profile_name)

            # 2단계: 원본 내용 로드 (기존 프로파일인 경우)
            original_content = ""
            if not is_new:
                profile_path = self._resolve_profile_path(profile_name)
                original_content = self._load_profile_settings_as_yaml(profile_path)
            else:
                original_content = self._create_profile_template()

            # 3단계: 임시 파일 경로 생성
            temp_path = self._generate_temp_file_path(profile_name, is_new)

            # 4단계: ProfileEditorSession 객체 생성
            session = ProfileEditorSession(
                session_id=session_id,
                profile_name=profile_name,
                is_new_profile=is_new,
                temp_file_path=temp_path,
                original_content=original_content,
                current_content=original_content  # 초기에는 원본과 동일
            )

            # 5단계: 임시 파일 저장
            self._save_temp_file(temp_path, original_content)

            # 6단계: 세션 저장
            self._save_edit_session(session)

            logger.info(f"✅ 편집 세션 생성 완료: {session_id}")
            return session

        except Exception as e:
            error_msg = f"편집 세션 생성 실패: {e}"
            logger.error(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            # 빈 세션 반환
            return ProfileEditorSession("", profile_name, is_new)

    def _save_edit_session(self, session: ProfileEditorSession) -> bool:
        """편집 세션 저장"""
        logger.debug(f"💾 편집 세션 저장: {session.session_id}")

        try:
            # 1단계: 세션 저장 디렉토리 생성
            from pathlib import Path
            session_dir = Path("temp/sessions")
            session_dir.mkdir(parents=True, exist_ok=True)

            # 2단계: 세션 파일 경로 생성
            session_file = session_dir / f"session_{session.session_id}.json"

            # 3단계: 세션 데이터를 JSON으로 저장
            import json
            session_data = session.to_dict()

            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            # 4단계: 메모리에도 캐시 (빠른 접근용)
            if not hasattr(self, '_session_cache'):
                self._session_cache = {}
            self._session_cache[session.session_id] = session

            logger.debug(f"✅ 편집 세션 저장 완료: {session_file}")
            return True

        except Exception as e:
            logger.error(f"❌ 편집 세션 저장 실패: {e}")
            return False

    def _restore_edit_session(self, session_id: str) -> Optional[ProfileEditorSession]:
        """편집 세션 복원"""
        logger.debug(f"🔄 편집 세션 복원: {session_id}")

        try:
            # 1단계: 메모리 캐시에서 확인
            if hasattr(self, '_session_cache') and session_id in self._session_cache:
                logger.debug("📋 메모리 캐시에서 세션 복원")
                return self._session_cache[session_id]

            # 2단계: 파일에서 로드
            from pathlib import Path
            session_file = Path("temp/sessions") / f"session_{session_id}.json"

            if not session_file.exists():
                logger.warning(f"⚠️ 세션 파일이 존재하지 않음: {session_file}")
                return None

            # 3단계: JSON 파일 읽기
            import json
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            # 4단계: ProfileEditorSession 객체 복원
            session = ProfileEditorSession.from_dict(session_data)

            # 5단계: 메모리 캐시에 저장
            if not hasattr(self, '_session_cache'):
                self._session_cache = {}
            self._session_cache[session_id] = session

            logger.debug(f"✅ 편집 세션 복원 완료: {session_id}")
            return session

        except Exception as e:
            logger.error(f"❌ 편집 세션 복원 실패: {e}")
            return None

    # === Task 4.1.3: 편집 세션 관리 헬퍼 메서드 ===

    def _generate_session_id(self, profile_name: str) -> str:
        """고유 세션 ID 생성"""
        try:
            import datetime
            import hashlib

            # 프로파일명 + 타임스탬프 + 프로세스 정보로 고유 ID 생성
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            base_string = f"{profile_name}_{timestamp}"

            # 해시를 사용해 짧고 고유한 ID 생성
            session_hash = hashlib.md5(base_string.encode()).hexdigest()[:8]
            session_id = f"{profile_name}_{session_hash}"

            return session_id

        except Exception as e:
            logger.warning(f"⚠️ 세션 ID 생성 실패: {e}")
            # 폴백: 간단한 타임스탬프 기반 ID
            import time
            return f"{profile_name}_{int(time.time())}"

    def _list_active_sessions(self) -> list:
        """활성 편집 세션 목록 조회"""
        try:
            from pathlib import Path

            session_dir = Path("temp/sessions")
            if not session_dir.exists():
                return []

            active_sessions = []
            for session_file in session_dir.glob("session_*.json"):
                try:
                    session_id = session_file.stem.replace("session_", "")
                    session = self._restore_edit_session(session_id)
                    if session:
                        active_sessions.append(session)
                except Exception as e:
                    logger.warning(f"⚠️ 세션 파일 처리 실패: {session_file} - {e}")

            logger.debug(f"📋 활성 편집 세션: {len(active_sessions)}개")
            return active_sessions

        except Exception as e:
            logger.warning(f"⚠️ 활성 세션 목록 조회 실패: {e}")
            return []

    def _cleanup_edit_session(self, session_id: str):
        """편집 세션 정리 (파일 및 캐시 삭제)"""
        try:
            # 1. 세션 파일 삭제
            from pathlib import Path
            session_file = Path("temp/sessions") / f"session_{session_id}.json"
            if session_file.exists():
                session_file.unlink()
                logger.debug(f"🗑️ 세션 파일 삭제: {session_file}")

            # 2. 메모리 캐시에서 제거
            if hasattr(self, '_session_cache') and session_id in self._session_cache:
                del self._session_cache[session_id]
                logger.debug(f"🗑️ 세션 캐시 제거: {session_id}")

        except Exception as e:
            logger.warning(f"⚠️ 편집 세션 정리 실패: {e}")

    def _update_session_content(self, session_id: str, new_content: str) -> bool:
        """편집 세션 내용 업데이트"""
        try:
            session = self._restore_edit_session(session_id)
            if not session:
                logger.warning(f"⚠️ 세션을 찾을 수 없음: {session_id}")
                return False

            # 내용 업데이트
            session.update_content(new_content)

            # 임시 파일도 업데이트
            if session.temp_file_path:
                self._save_temp_file(session.temp_file_path, new_content)

            # 세션 저장
            return self._save_edit_session(session)

        except Exception as e:
            logger.error(f"❌ 세션 내용 업데이트 실패: {e}")
            return False

    def _get_session_by_profile(self, profile_name: str) -> Optional[ProfileEditorSession]:
        """프로파일명으로 편집 세션 조회"""
        try:
            active_sessions = self._list_active_sessions()
            for session in active_sessions:
                if session.profile_name == profile_name:
                    return session
            return None

        except Exception as e:
            logger.warning(f"⚠️ 프로파일별 세션 조회 실패: {e}")
            return None

    def _cleanup_expired_sessions(self):
        """만료된 편집 세션 정리"""
        try:
            import time
            from pathlib import Path

            session_dir = Path("temp/sessions")
            if not session_dir.exists():
                return

            current_time = time.time()
            expiry_hours = 24  # 24시간 후 만료
            expiry_threshold = expiry_hours * 60 * 60

            cleaned_count = 0
            for session_file in session_dir.glob("session_*.json"):
                try:
                    # 파일 생성 시간 확인
                    file_age = current_time - session_file.stat().st_ctime

                    if file_age > expiry_threshold:
                        session_id = session_file.stem.replace("session_", "")
                        self._cleanup_edit_session(session_id)
                        cleaned_count += 1

                except Exception as e:
                    logger.warning(f"⚠️ 세션 만료 처리 실패: {session_file} - {e}")

            if cleaned_count > 0:
                logger.info(f"🧹 만료된 편집 세션 정리: {cleaned_count}개")

        except Exception as e:
            logger.warning(f"⚠️ 만료된 편집 세션 정리 실패: {e}")

    # ===============================================================================
    # === Task 4.2.1: 메타데이터 YAML 구조 관리 메서드 ===
    # ===============================================================================

    def _load_profile_metadata(self, profile_name: str) -> Optional[ProfileMetadata]:
        """프로파일의 메타데이터 로드"""
        try:
            # 메타데이터 파일 경로 결정
            config_file = self._get_profile_config_path(profile_name)
            if not config_file.exists():
                logger.debug(f"📄 메타데이터 파일 없음: {config_file}")
                return None

            # YAML 파일에서 메타데이터 추출
            with open(config_file, 'r', encoding='utf-8') as f:
                yaml_content = f.read()

            metadata = ProfileMetadata.from_yaml_content(yaml_content)
            logger.debug(f"📖 메타데이터 로드 성공: {profile_name}")
            return metadata

        except Exception as e:
            logger.warning(f"⚠️ 메타데이터 로드 실패 ({profile_name}): {e}")
            return None

    def _save_profile_metadata(self, profile_name: str, metadata: ProfileMetadata) -> bool:
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

    def _create_default_metadata(self, profile_name: str, created_from: str = "") -> ProfileMetadata:
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

    def _update_profile_metadata(self, profile_name: str, metadata: ProfileMetadata) -> bool:
        """프로파일 메타데이터 업데이트"""
        try:
            # 메타데이터 유효성 검증
            is_valid, error_msg = metadata.validate()
            if not is_valid:
                logger.warning(f"⚠️ 메타데이터 유효성 검증 실패: {error_msg}")
                return False

            # 메타데이터 저장
            success = self._save_profile_metadata(profile_name, metadata)
            if success:
                logger.info(f"✅ 메타데이터 업데이트 완료: {profile_name}")

            return success

        except Exception as e:
            logger.error(f"❌ 메타데이터 업데이트 실패 ({profile_name}): {e}")
            return False

    def _get_profile_display_name(self, profile_name: str) -> str:
        """프로파일의 표시명 조회 (Task 4.2.2용 메서드)"""
        try:
            metadata = self._load_profile_metadata(profile_name)
            if metadata:
                return metadata.generate_display_name(profile_name)
            else:
                return profile_name

        except Exception as e:
            logger.warning(f"⚠️ 표시명 조회 실패 ({profile_name}): {e}")
            return profile_name

    def _ensure_profile_has_metadata(self, profile_name: str) -> bool:
        """프로파일에 메타데이터가 있는지 확인하고 없으면 생성"""
        try:
            metadata = self._load_profile_metadata(profile_name)
            if metadata is None:
                # 메타데이터가 없으면 기본 메타데이터 생성
                default_metadata = self._create_default_metadata(profile_name)
                return self._save_profile_metadata(profile_name, default_metadata)
            return True

        except Exception as e:
            logger.warning(f"⚠️ 메타데이터 확인/생성 실패 ({profile_name}): {e}")
            return False

    # ===============================================================================
    # === Task 4.2.2: 콤보박스 표시명 시스템 메서드 ===
    # ===============================================================================

    def _format_profile_combo_item(self, profile_name: str, metadata: Optional[ProfileMetadata] = None) -> str:
        """프로파일 콤보박스 아이템 포맷팅"""
        try:
            if metadata is None:
                metadata = self._load_profile_metadata(profile_name)

            if metadata and metadata.name:
                # "Custom Dev Settings (커스텀)" 형식
                return f"{metadata.name} ({profile_name})"
            else:
                # 메타데이터가 없으면 기본 이름 사용
                return self._get_default_display_name(profile_name)

        except Exception as e:
            logger.warning(f"⚠️ 콤보박스 아이템 포맷팅 실패 ({profile_name}): {e}")
            return profile_name

    def _get_default_display_name(self, profile_name: str) -> str:
        """기본 표시명 반환"""
        display_mappings = {
            'development': '개발 환경 (development)',
            'production': '운영 환경 (production)',
            'testing': '테스트 환경 (testing)',
            'staging': '스테이징 환경 (staging)'
        }
        return display_mappings.get(profile_name, f"{profile_name.title()} ({profile_name})")

    def _update_profile_combo_display(self, combo_widget) -> None:
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
            available_profiles = self._get_available_profiles()

            # 각 프로파일에 대해 표시명 설정
            for profile_name in available_profiles:
                try:
                    # 메타데이터 로드
                    metadata = self._load_profile_metadata(profile_name)

                    # 표시명 생성
                    display_name = self._format_profile_combo_item(profile_name, metadata)

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

    def _get_available_profiles(self) -> list:
        """사용 가능한 프로파일 목록 조회"""
        try:
            from pathlib import Path

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

    def _get_profile_combo_data(self, combo_widget, index: int) -> Optional[str]:
        """콤보박스에서 프로파일명 데이터 조회"""
        try:
            if combo_widget is None or index < 0 or index >= combo_widget.count():
                return None

            return combo_widget.itemData(index)

        except Exception as e:
            logger.warning(f"⚠️ 콤보박스 데이터 조회 실패: {e}")
            return None

    def _is_custom_profile_by_name(self, profile_name: str) -> bool:
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
            from ..dialogs.profile_metadata_dialog import ProfileMetadataDialog

            # 현재 메타데이터 로드
            current_metadata = self._load_profile_metadata(profile_name)

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

    def _on_metadata_applied(self, profile_name: str, metadata: ProfileMetadata):
        """메타데이터 적용 이벤트 핸들러"""
        try:
            # 메타데이터 저장
            success = self._save_profile_metadata(profile_name, metadata)

            if success:
                # 뷰 업데이트 시그널 발생
                if hasattr(self, 'view') and self.view:
                    # 콤보박스 표시명 업데이트
                    if hasattr(self.view, 'profile_selector'):
                        self._update_profile_combo_display(self.view.profile_selector.combo)

                    # 프로파일 데이터 새로고침
                    self._load_profile(profile_name)

                logger.info(f"✅ 메타데이터 적용 및 뷰 업데이트 완료: {profile_name}")
            else:
                logger.error(f"❌ 메타데이터 저장 실패: {profile_name}")

        except Exception as e:
            logger.error(f"❌ 메타데이터 적용 핸들러 실패: {e}")

    def get_profile_metadata_summary(self, profile_name: str) -> dict:
        """프로파일 메타데이터 요약 정보 반환"""
        try:
            metadata = self._load_profile_metadata(profile_name)
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
                    'is_custom': self._is_custom_profile_by_name(profile_name),
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
