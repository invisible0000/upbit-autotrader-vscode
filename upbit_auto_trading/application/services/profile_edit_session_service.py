"""
Profile Edit Session Service
============================

프로파일 편집 세션 관리를 위한 Application Service
임시 파일 생성, 편집 세션 추적, 안전한 저장 처리 등을 담당

Features:
- 안전한 편집 워크플로우 (Task 4.1.1)
- 파일명 자동 생성 시스템 (Task 4.1.2)
- 편집 세션 관리 (Task 4.1.3)
- 임시 파일 관리 및 정리

Author: AI Assistant
Created: 2025-08-11
Refactored from: environment_profile_presenter.py (er-subTASK 01)
"""

from typing import Optional
from pathlib import Path
import datetime
import time
import hashlib
import json

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("ProfileEditSessionService")

# === ProfileEditorSession 데이터 클래스 ===
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

class ProfileEditSessionService:
    """
    프로파일 편집 세션 관리 Application Service

    임시 파일 생성, 편집 세션 추적, 안전한 저장 등의
    편집 관련 모든 비즈니스 로직을 캡슐화합니다.
    """

    def __init__(self):
        """ProfileEditSessionService 초기화"""
        self._session_cache = {}
        logger.info("📝 ProfileEditSessionService 초기화")

    # ===============================================================================
    # === Task 4.1.1: 안전한 편집 워크플로우 구현 ===
    # ===============================================================================

    def start_edit_existing_profile(self, profile_name: str) -> str:
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
            return ""

    def start_edit_new_profile(self) -> str:
        """새 프로파일 편집 시작 - 템플릿 기반 임시 파일 생성"""
        logger.info("📝 새 프로파일 편집 시작")

        try:
            # 1단계: 새 프로파일명 생성
            new_profile_name = self.generate_custom_profile_name()
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
            return ""

    def save_temp_to_original(self, profile_name: str) -> bool:
        """임시 파일을 원본 위치에 저장"""
        logger.info(f"💾 임시 파일을 원본으로 저장: {profile_name}")

        try:
            # 1단계: 편집 세션 정보 확인
            session = self.get_edit_session(profile_name)
            if not session:
                error_msg = f"편집 세션을 찾을 수 없음: {profile_name}"
                logger.error(f"❌ {error_msg}")
                return False

            # 2단계: 임시 파일 내용 검증
            temp_content = self._load_temp_file_content(session.temp_file_path)
            if not temp_content:
                error_msg = f"임시 파일 내용 로드 실패: {session.temp_file_path}"
                logger.error(f"❌ {error_msg}")
                return False

            # 3단계: 원본 파일 경로 결정
            if session.is_new_profile:
                # 새 프로파일인 경우 - config 디렉토리에 새 파일 생성
                original_path = f"config/config.{profile_name}.yaml"
            else:
                # 기존 프로파일인 경우 - 기존 경로 사용
                original_path = self._resolve_profile_path(profile_name)

            # 4단계: 원본 위치에 저장
            self._save_profile_to_path(original_path, temp_content)

            # 5단계: 임시 파일 정리
            self._cleanup_temp_file(session.temp_file_path)

            # 6단계: 편집 세션 제거
            self._remove_edit_session(profile_name)

            logger.info(f"✅ 임시 파일을 원본으로 저장 완료: {original_path}")
            return True

        except Exception as e:
            error_msg = f"임시 파일을 원본으로 저장 실패: {e}"
            logger.error(f"❌ {error_msg}")
            return False

    def cleanup_abandoned_temp_files(self):
        """방치된 임시 파일들 정리"""
        logger.info("🧹 방치된 임시 파일 정리 시작")

        try:
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

    # ===============================================================================
    # === Task 4.1.2: 파일명 자동 생성 시스템 구현 ===
    # ===============================================================================

    def generate_custom_profile_name(self) -> str:
        """커스텀 프로파일명 자동 생성"""
        logger.debug("🏷️ 커스텀 프로파일명 자동 생성")

        try:
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
            return f"Profile_{int(time.time())}"

    def validate_filename(self, filename: str) -> bool:
        """파일명 유효성 검증"""
        return self._validate_filename(filename)

    def sanitize_filename(self, filename: str) -> str:
        """파일명 안전화"""
        return self._sanitize_filename(filename)

    # ===============================================================================
    # === Task 4.1.3: 편집 세션 관리 구현 ===
    # ===============================================================================

    def create_edit_session(self, profile_name: str, is_new: bool) -> ProfileEditorSession:
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
            # 빈 세션 반환
            return ProfileEditorSession("", profile_name, is_new)

    def get_edit_session(self, profile_name: str) -> Optional[ProfileEditorSession]:
        """편집 세션 조회"""
        try:
            # 메모리 캐시에서 먼저 확인
            for session in self._session_cache.values():
                if session.profile_name == profile_name:
                    return session

            # 파일에서 세션 복원 시도
            session_files = Path("temp/sessions").glob("session_*.json")
            for session_file in session_files:
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)

                    if session_data.get('profile_name') == profile_name:
                        session = ProfileEditorSession.from_dict(session_data)
                        self._session_cache[session.session_id] = session
                        return session
                except Exception:
                    continue

            return None

        except Exception as e:
            logger.warning(f"⚠️ 편집 세션 조회 실패: {e}")
            return None

    def save_edit_session(self, session: ProfileEditorSession) -> bool:
        """편집 세션 저장"""
        return self._save_edit_session(session)

    def restore_edit_session(self, session_id: str) -> Optional[ProfileEditorSession]:
        """편집 세션 복원"""
        return self._restore_edit_session(session_id)

    def list_active_sessions(self) -> list:
        """활성 편집 세션 목록 조회"""
        return self._list_active_sessions()

    # ===============================================================================
    # === 헬퍼 메서드 ===
    # ===============================================================================

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

    def _check_profile_exists(self, profile_path: str) -> bool:
        """프로파일 파일 존재 여부 확인"""
        try:
            return Path(profile_path).exists()
        except Exception:
            return False

    def _load_profile_settings_as_yaml(self, profile_path: str) -> str:
        """프로파일을 YAML 문자열로 로드"""
        try:
            file_path = Path(profile_path)
            if not file_path.exists():
                return ""

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return content

        except Exception as e:
            logger.error(f"❌ 프로파일 YAML 로드 실패: {e}")
            return ""

    def _generate_temp_file_path(self, profile_name: str, is_new: bool) -> str:
        """임시 파일 경로 생성"""
        try:
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

    def _save_temp_file(self, temp_path: str, content: str):
        """임시 파일 저장"""
        try:
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
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        template = f"""# 새 커스텀 프로파일
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
"""
        return template

    def _register_edit_session(self, profile_name: str, temp_path: str, is_new: bool):
        """편집 세션 등록"""
        try:
            session_id = self._generate_session_id(profile_name)
            self._session_cache[profile_name] = {
                'session_id': session_id,
                'temp_path': temp_path,
                'is_new': is_new,
                'started_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'profile_name': profile_name
            }

            logger.debug(f"📝 편집 세션 등록: {profile_name}")

        except Exception as e:
            logger.warning(f"⚠️ 편집 세션 등록 실패: {e}")

    def _validate_filename(self, filename: str) -> bool:
        """파일명 유효성 검증"""
        try:
            # 1. 길이 제한 확인
            if len(filename) > 100:
                logger.warning(f"⚠️ 파일명 너무 김: {len(filename)}자")
                return False

            # 2. 빈 파일명 확인
            if not filename or filename.strip() == "":
                logger.warning("⚠️ 빈 파일명")
                return False

            # 3. 금지된 문자 확인
            forbidden_chars = r'<>:"/\|?*'
            if any(char in filename for char in forbidden_chars):
                logger.warning(f"⚠️ 금지된 문자 포함: {filename}")
                return False

            # 4. 예약어 확인
            reserved_names = [
                'CON', 'PRN', 'AUX', 'NUL',
                'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
            ]
            if filename.upper() in reserved_names:
                logger.warning(f"⚠️ 예약어 파일명: {filename}")
                return False

            logger.debug(f"✅ 파일명 검증 통과: {filename}")
            return True

        except Exception as e:
            logger.error(f"❌ 파일명 검증 실패: {e}")
            return False

    def _sanitize_filename(self, filename: str) -> str:
        """파일명 안전화"""
        try:
            import re

            # 1. 기본 정리
            sanitized = filename.strip()

            # 2. 금지된 문자를 언더스코어로 변경
            forbidden_chars = r'<>:"/\|?*'
            for char in forbidden_chars:
                sanitized = sanitized.replace(char, '_')

            # 3. 제어 문자 제거
            sanitized = re.sub(r'[\x00-\x1f]', '', sanitized)

            # 4. 연속된 공백을 언더스코어로 변경
            sanitized = re.sub(r'\s+', '_', sanitized)

            # 5. 연속된 언더스코어 정리
            sanitized = re.sub(r'_+', '_', sanitized)

            # 6. 시작과 끝의 언더스코어/점 제거
            sanitized = sanitized.strip('_.')

            # 7. 길이 제한
            if len(sanitized) > 90:
                sanitized = sanitized[:90].rstrip('_')

            # 8. 빈 문자열인 경우 기본값 사용
            if not sanitized:
                sanitized = "Profile"

            logger.debug(f"🔧 파일명 안전화: '{filename}' → '{sanitized}'")
            return sanitized

        except Exception as e:
            logger.error(f"❌ 파일명 안전화 실패: {e}")
            return "Profile"

    def _ensure_unique_filename(self, base_name: str) -> str:
        """파일명 고유성 보장"""
        try:
            # 1. 기본 이름이 사용 가능한지 확인
            config_path = Path("config") / f"config.{base_name}.yaml"
            if not config_path.exists():
                return base_name

            # 2. 숫자 접미사로 고유 이름 생성
            counter = 1
            max_attempts = 1000

            while counter <= max_attempts:
                candidate_name = f"{base_name}_{counter:03d}"
                candidate_path = Path("config") / f"config.{candidate_name}.yaml"

                if not candidate_path.exists():
                    return candidate_name

                counter += 1

            # 3. 최대 시도 횟수 초과 시 타임스탬프 기반 생성
            timestamp_suffix = str(int(time.time()))
            fallback_name = f"{base_name}_{timestamp_suffix}"

            logger.warning(f"⚠️ 최대 시도 횟수 초과, 타임스탬프 사용: {fallback_name}")
            return fallback_name

        except Exception as e:
            logger.error(f"❌ 파일명 고유성 보장 실패: {e}")
            return f"{base_name}_{int(time.time())}"

    def _generate_session_id(self, profile_name: str) -> str:
        """고유 세션 ID 생성"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            base_string = f"{profile_name}_{timestamp}"
            session_hash = hashlib.md5(base_string.encode()).hexdigest()[:8]
            session_id = f"{profile_name}_{session_hash}"
            return session_id

        except Exception as e:
            logger.warning(f"⚠️ 세션 ID 생성 실패: {e}")
            return f"{profile_name}_{int(time.time())}"

    def _save_edit_session(self, session: ProfileEditorSession) -> bool:
        """편집 세션 저장"""
        try:
            # 세션 저장 디렉토리 생성
            session_dir = Path("temp/sessions")
            session_dir.mkdir(parents=True, exist_ok=True)

            # 세션 파일 경로 생성
            session_file = session_dir / f"session_{session.session_id}.json"

            # 세션 데이터를 JSON으로 저장
            session_data = session.to_dict()

            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            # 메모리에도 캐시
            self._session_cache[session.session_id] = session

            logger.debug(f"✅ 편집 세션 저장 완료: {session_file}")
            return True

        except Exception as e:
            logger.error(f"❌ 편집 세션 저장 실패: {e}")
            return False

    def _restore_edit_session(self, session_id: str) -> Optional[ProfileEditorSession]:
        """편집 세션 복원"""
        try:
            # 메모리 캐시에서 확인
            if session_id in self._session_cache:
                return self._session_cache[session_id]

            # 파일에서 로드
            session_file = Path("temp/sessions") / f"session_{session_id}.json"

            if not session_file.exists():
                return None

            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            session = ProfileEditorSession.from_dict(session_data)
            self._session_cache[session_id] = session

            logger.debug(f"✅ 편집 세션 복원 완료: {session_id}")
            return session

        except Exception as e:
            logger.error(f"❌ 편집 세션 복원 실패: {e}")
            return None

    def _list_active_sessions(self) -> list:
        """활성 편집 세션 목록 조회"""
        try:
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

            return active_sessions

        except Exception as e:
            logger.warning(f"⚠️ 활성 세션 목록 조회 실패: {e}")
            return []

    def _load_temp_file_content(self, temp_path: str) -> str:
        """임시 파일 내용 로드"""
        try:
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
            temp_file = Path(temp_path)
            if temp_file.exists():
                temp_file.unlink()
                logger.debug(f"🗑️ 임시 파일 삭제: {temp_path}")

        except Exception as e:
            logger.warning(f"⚠️ 임시 파일 삭제 실패: {e}")

    def _remove_edit_session(self, profile_name: str):
        """편집 세션 제거"""
        try:
            # 메모리 캐시에서 제거
            sessions_to_remove = []
            for session_id, session in self._session_cache.items():
                if hasattr(session, 'profile_name') and session.profile_name == profile_name:
                    sessions_to_remove.append(session_id)

            for session_id in sessions_to_remove:
                del self._session_cache[session_id]

                # 파일에서도 제거
                session_file = Path("temp/sessions") / f"session_{session_id}.json"
                if session_file.exists():
                    session_file.unlink()

            logger.debug(f"🗑️ 편집 세션 제거: {profile_name}")

        except Exception as e:
            logger.warning(f"⚠️ 편집 세션 제거 실패: {e}")

    def _cleanup_stale_edit_sessions(self):
        """만료된 편집 세션 정리"""
        try:
            current_time = time.time()
            session_timeout = 24 * 60 * 60  # 24시간

            cleaned_count = 0
            session_dir = Path("temp/sessions")

            if session_dir.exists():
                for session_file in session_dir.glob("session_*.json"):
                    try:
                        file_age = current_time - session_file.stat().st_mtime
                        if file_age > session_timeout:
                            session_file.unlink()
                            cleaned_count += 1
                    except Exception:
                        continue

            if cleaned_count > 0:
                logger.info(f"🧹 만료된 편집 세션 정리: {cleaned_count}개")

        except Exception as e:
            logger.warning(f"⚠️ 만료된 편집 세션 정리 실패: {e}")
