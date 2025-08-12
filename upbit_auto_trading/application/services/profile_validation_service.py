"""
Profile Validation Service
==========================

프로파일 검증 및 호환성 관리를 위한 Application Service
YAML 구문 검증, 환경 설정 호환성, 프로파일 무결성 검사 등을 담당

Features:
- YAML 구문 및 구조 검증
- 환경 설정 호환성 검사
- 프로파일 무결성 검증
- API 키 설정 검증
- 데이터베이스 연결 검증

Author: AI Assistant
Created: 2025-08-11
Refactored from: environment_profile_presenter.py (er-subTASK 01)
"""

from typing import Dict, List, Any
import yaml
import re
from pathlib import Path

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("ProfileValidationService")

class ValidationError(Exception):
    """프로파일 검증 에러"""
    def __init__(self, message: str, field_name: str = "", line_number: int = 0):
        super().__init__(message)
        self.field_name = field_name
        self.line_number = line_number

class ValidationResult:
    """검증 결과를 담는 데이터 클래스"""
    def __init__(self, is_valid: bool = True, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def add_error(self, error: str):
        """에러 추가"""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str):
        """경고 추가"""
        self.warnings.append(warning)

    def has_issues(self) -> bool:
        """에러나 경고가 있는지 확인"""
        return len(self.errors) > 0 or len(self.warnings) > 0

class ProfileValidationService:
    """
    프로파일 검증 및 호환성 관리 Application Service

    YAML 구문 검증, 환경 설정 호환성, 프로파일 무결성 등의
    검증 관련 모든 비즈니스 로직을 캡슐화합니다.
    """

    def __init__(self):
        """ProfileValidationService 초기화"""
        self._required_sections = [
            'upbit', 'logging', 'database', 'trading', 'indicators'
        ]
        self._api_key_pattern = re.compile(r'^[A-Za-z0-9]{32,64}$')
        logger.info("🔍 ProfileValidationService 초기화")

    # ===============================================================================
    # === YAML 구문 및 구조 검증 ===
    # ===============================================================================

    def validate_yaml_syntax(self, yaml_content: str) -> ValidationResult:
        """YAML 구문 검증"""
        logger.debug("📝 YAML 구문 검증 시작")
        result = ValidationResult()

        try:
            # 1단계: 기본 YAML 파싱 검증
            parsed_data = yaml.safe_load(yaml_content)

            if parsed_data is None:
                result.add_error("YAML 파일이 비어있거나 null입니다")
                return result

            if not isinstance(parsed_data, dict):
                result.add_error("YAML 루트는 딕셔너리여야 합니다")
                return result

            # 2단계: 기본 구조 검증
            self._validate_basic_structure(parsed_data, result)

            # 3단계: 필수 섹션 검증
            self._validate_required_sections(parsed_data, result)

            # 4단계: 섹션별 상세 검증
            self._validate_section_details(parsed_data, result)

            if result.is_valid:
                logger.info("✅ YAML 구문 검증 성공")
            else:
                logger.warning(f"⚠️ YAML 검증 실패: {len(result.errors)}개 에러")

            return result

        except yaml.YAMLError as e:
            error_msg = f"YAML 파싱 에러: {str(e)}"
            logger.error(f"❌ {error_msg}")
            result.add_error(error_msg)
            return result

        except Exception as e:
            error_msg = f"YAML 검증 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            result.add_error(error_msg)
            return result

    def validate_yaml_structure(self, parsed_data: Dict[str, Any]) -> ValidationResult:
        """파싱된 YAML 데이터 구조 검증"""
        logger.debug("🏗️ YAML 구조 검증 시작")
        result = ValidationResult()

        try:
            # 1단계: 필수 최상위 키 검증
            self._validate_required_sections(parsed_data, result)

            # 2단계: 각 섹션의 내부 구조 검증
            if 'upbit' in parsed_data:
                self._validate_upbit_section(parsed_data['upbit'], result)

            if 'logging' in parsed_data:
                self._validate_logging_section(parsed_data['logging'], result)

            if 'database' in parsed_data:
                self._validate_database_section(parsed_data['database'], result)

            if 'trading' in parsed_data:
                self._validate_trading_section(parsed_data['trading'], result)

            if 'indicators' in parsed_data:
                self._validate_indicators_section(parsed_data['indicators'], result)

            if result.is_valid:
                logger.info("✅ YAML 구조 검증 성공")
            else:
                logger.warning(f"⚠️ YAML 구조 검증 실패: {len(result.errors)}개 에러")

            return result

        except Exception as e:
            error_msg = f"YAML 구조 검증 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            result.add_error(error_msg)
            return result

    def extract_yaml_errors(self, yaml_content: str) -> List[Dict[str, Any]]:
        """YAML 에러를 라인 번호와 함께 추출"""
        logger.debug("🔍 YAML 에러 상세 분석")
        errors = []

        try:
            yaml.safe_load(yaml_content)
            return errors  # 에러 없음

        except yaml.scanner.ScannerError as e:
            errors.append({
                'type': 'ScannerError',
                'message': str(e.problem),
                'line': e.problem_mark.line + 1 if e.problem_mark else 0,
                'column': e.problem_mark.column + 1 if e.problem_mark else 0,
                'context': e.context or ''
            })

        except yaml.parser.ParserError as e:
            errors.append({
                'type': 'ParserError',
                'message': str(e.problem),
                'line': e.problem_mark.line + 1 if e.problem_mark else 0,
                'column': e.problem_mark.column + 1 if e.problem_mark else 0,
                'context': e.context or ''
            })

        except yaml.constructor.ConstructorError as e:
            errors.append({
                'type': 'ConstructorError',
                'message': str(e.problem),
                'line': e.problem_mark.line + 1 if e.problem_mark else 0,
                'column': e.problem_mark.column + 1 if e.problem_mark else 0,
                'context': e.context or ''
            })

        except Exception as e:
            errors.append({
                'type': 'UnknownError',
                'message': str(e),
                'line': 0,
                'column': 0,
                'context': ''
            })

        logger.debug(f"📊 YAML 에러 분석 완료: {len(errors)}개 발견")
        return errors

    # ===============================================================================
    # === 환경 설정 호환성 검증 ===
    # ===============================================================================

    def validate_profile_compatibility(self, profile_name: str, profile_data: Dict[str, Any]) -> ValidationResult:
        """프로파일 호환성 검증"""
        logger.info(f"🔄 프로파일 호환성 검증: {profile_name}")
        result = ValidationResult()

        try:
            # 1단계: 환경별 특수 검증
            if profile_name == 'production':
                self._validate_production_requirements(profile_data, result)
            elif profile_name == 'development':
                self._validate_development_requirements(profile_data, result)
            elif profile_name == 'testing':
                self._validate_testing_requirements(profile_data, result)
            else:
                self._validate_custom_requirements(profile_data, result)

            # 2단계: 공통 호환성 검증
            self._validate_common_compatibility(profile_data, result)

            # 3단계: API 키 설정 호환성
            self._validate_api_key_compatibility(profile_data, result)

            if result.is_valid:
                logger.info(f"✅ 프로파일 호환성 검증 성공: {profile_name}")
            else:
                logger.warning(f"⚠️ 프로파일 호환성 검증 실패: {profile_name}")

            return result

        except Exception as e:
            error_msg = f"프로파일 호환성 검증 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            result.add_error(error_msg)
            return result

    def validate_cross_profile_consistency(self, profiles: Dict[str, Dict[str, Any]]) -> ValidationResult:
        """여러 프로파일 간 일관성 검증"""
        logger.info("🔄 프로파일 간 일관성 검증")
        result = ValidationResult()

        try:
            # 1단계: 기본 구조 일관성 검증
            self._validate_structure_consistency(profiles, result)

            # 2단계: 설정값 일관성 검증
            self._validate_settings_consistency(profiles, result)

            # 3단계: 환경별 특수 요구사항 검증
            self._validate_environment_specific_consistency(profiles, result)

            if result.is_valid:
                logger.info("✅ 프로파일 간 일관성 검증 성공")
            else:
                logger.warning("⚠️ 프로파일 간 일관성 검증 실패")

            return result

        except Exception as e:
            error_msg = f"프로파일 간 일관성 검증 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            result.add_error(error_msg)
            return result

    # ===============================================================================
    # === 프로파일 무결성 검증 ===
    # ===============================================================================

    def validate_profile_integrity(self, profile_path: str) -> ValidationResult:
        """프로파일 파일 무결성 검증"""
        logger.info(f"🔒 프로파일 무결성 검증: {profile_path}")
        result = ValidationResult()

        try:
            # 1단계: 파일 존재 및 접근성 검증
            if not self._validate_file_accessibility(profile_path, result):
                return result

            # 2단계: 파일 내용 로드 및 파싱
            content = self._load_profile_content(profile_path)
            if not content:
                result.add_error(f"프로파일 파일을 읽을 수 없습니다: {profile_path}")
                return result

            # 3단계: YAML 구문 검증
            syntax_result = self.validate_yaml_syntax(content)
            if not syntax_result.is_valid:
                result.errors.extend(syntax_result.errors)
                result.warnings.extend(syntax_result.warnings)
                result.is_valid = False
                return result

            # 4단계: 프로파일 데이터 파싱
            try:
                profile_data = yaml.safe_load(content)
            except Exception as e:
                result.add_error(f"YAML 파싱 실패: {str(e)}")
                return result

            # 5단계: 구조 무결성 검증
            structure_result = self.validate_yaml_structure(profile_data)
            if not structure_result.is_valid:
                result.errors.extend(structure_result.errors)
                result.warnings.extend(structure_result.warnings)
                result.is_valid = False

            if result.is_valid:
                logger.info(f"✅ 프로파일 무결성 검증 성공: {profile_path}")
            else:
                logger.warning(f"⚠️ 프로파일 무결성 검증 실패: {profile_path}")

            return result

        except Exception as e:
            error_msg = f"프로파일 무결성 검증 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            result.add_error(error_msg)
            return result

    def validate_api_key_settings(self, profile_data: Dict[str, Any]) -> ValidationResult:
        """API 키 설정 검증"""
        logger.debug("🔑 API 키 설정 검증")
        result = ValidationResult()

        try:
            upbit_section = profile_data.get('upbit', {})

            # 1단계: API 키 파일 경로 검증
            api_key_file = upbit_section.get('api_key_file', '')
            secret_key_file = upbit_section.get('secret_key_file', '')

            if not api_key_file and not secret_key_file:
                result.add_warning("API 키 파일이 설정되지 않았습니다")
                return result

            # 2단계: 파일 존재성 검증
            if api_key_file and not Path(api_key_file).exists():
                result.add_error(f"API 키 파일을 찾을 수 없습니다: {api_key_file}")

            if secret_key_file and not Path(secret_key_file).exists():
                result.add_error(f"시크릿 키 파일을 찾을 수 없습니다: {secret_key_file}")

            # 3단계: 페이퍼 트레이딩 설정과의 일관성
            paper_trading = upbit_section.get('paper_trading', True)
            if not paper_trading and (not api_key_file or not secret_key_file):
                result.add_error("실제 거래 모드에서는 API 키와 시크릿 키가 모두 필요합니다")

            if result.is_valid:
                logger.debug("✅ API 키 설정 검증 성공")
            else:
                logger.warning("⚠️ API 키 설정 검증 실패")

            return result

        except Exception as e:
            error_msg = f"API 키 설정 검증 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            result.add_error(error_msg)
            return result

    def validate_database_connection_settings(self, profile_data: Dict[str, Any]) -> ValidationResult:
        """데이터베이스 연결 설정 검증"""
        logger.debug("🗄️ 데이터베이스 연결 설정 검증")
        result = ValidationResult()

        try:
            database_section = profile_data.get('database', {})

            # 1단계: 필수 설정 검증
            required_fields = ['connection_timeout', 'max_retry_attempts']
            for field in required_fields:
                if field not in database_section:
                    result.add_error(f"필수 데이터베이스 설정이 누락됨: {field}")

            # 2단계: 값 범위 검증
            connection_timeout = database_section.get('connection_timeout', 0)
            if not isinstance(connection_timeout, (int, float)) or connection_timeout <= 0:
                result.add_error("connection_timeout은 양수여야 합니다")

            max_retry_attempts = database_section.get('max_retry_attempts', 0)
            if not isinstance(max_retry_attempts, int) or max_retry_attempts < 0:
                result.add_error("max_retry_attempts는 0 이상의 정수여야 합니다")

            # 3단계: 백업 설정 검증 (선택사항)
            backup_interval = database_section.get('backup_interval', 0)
            if backup_interval and (not isinstance(backup_interval, (int, float)) or backup_interval <= 0):
                result.add_warning("backup_interval이 설정된 경우 양수여야 합니다")

            if result.is_valid:
                logger.debug("✅ 데이터베이스 연결 설정 검증 성공")
            else:
                logger.warning("⚠️ 데이터베이스 연결 설정 검증 실패")

            return result

        except Exception as e:
            error_msg = f"데이터베이스 연결 설정 검증 중 예외 발생: {str(e)}"
            logger.error(f"❌ {error_msg}")
            result.add_error(error_msg)
            return result

    # ===============================================================================
    # === 헬퍼 메서드 - 기본 구조 검증 ===
    # ===============================================================================

    def _validate_basic_structure(self, data: Dict[str, Any], result: ValidationResult):
        """기본 구조 검증"""
        if not isinstance(data, dict):
            result.add_error("루트 요소는 딕셔너리여야 합니다")
            return

        if len(data) == 0:
            result.add_error("설정이 비어있습니다")

    def _validate_required_sections(self, data: Dict[str, Any], result: ValidationResult):
        """필수 섹션 검증"""
        for section in self._required_sections:
            if section not in data:
                result.add_error(f"필수 섹션이 누락됨: {section}")

    def _validate_section_details(self, data: Dict[str, Any], result: ValidationResult):
        """섹션별 상세 검증"""
        try:
            for section_name, section_data in data.items():
                if section_name in self._required_sections:
                    if not isinstance(section_data, dict):
                        result.add_error(f"섹션 '{section_name}'은 딕셔너리여야 합니다")
                    elif len(section_data) == 0:
                        result.add_warning(f"섹션 '{section_name}'이 비어있습니다")
        except Exception as e:
            result.add_error(f"섹션 상세 검증 실패: {str(e)}")

    # ===============================================================================
    # === 헬퍼 메서드 - 섹션별 검증 ===
    # ===============================================================================

    def _validate_upbit_section(self, upbit_data: Dict[str, Any], result: ValidationResult):
        """Upbit 섹션 검증"""
        required_fields = ['paper_trading']
        for field in required_fields:
            if field not in upbit_data:
                result.add_error(f"Upbit 섹션에 필수 필드 누락: {field}")

        # paper_trading 필드 타입 검증
        if 'paper_trading' in upbit_data:
            if not isinstance(upbit_data['paper_trading'], bool):
                result.add_error("paper_trading은 boolean 값이어야 합니다")

    def _validate_logging_section(self, logging_data: Dict[str, Any], result: ValidationResult):
        """로깅 섹션 검증"""
        required_fields = ['level', 'console_output']
        for field in required_fields:
            if field not in logging_data:
                result.add_error(f"로깅 섹션에 필수 필드 누락: {field}")

        # 로그 레벨 검증
        if 'level' in logging_data:
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if logging_data['level'] not in valid_levels:
                result.add_error(f"잘못된 로그 레벨: {logging_data['level']}")

    def _validate_database_section(self, database_data: Dict[str, Any], result: ValidationResult):
        """데이터베이스 섹션 검증"""
        required_fields = ['connection_timeout', 'max_retry_attempts']
        for field in required_fields:
            if field not in database_data:
                result.add_error(f"데이터베이스 섹션에 필수 필드 누락: {field}")

    def _validate_trading_section(self, trading_data: Dict[str, Any], result: ValidationResult):
        """트레이딩 섹션 검증"""
        required_fields = ['paper_trading']
        for field in required_fields:
            if field not in trading_data:
                result.add_error(f"트레이딩 섹션에 필수 필드 누락: {field}")

    def _validate_indicators_section(self, indicators_data: Dict[str, Any], result: ValidationResult):
        """지표 섹션 검증"""
        # 지표 섹션은 선택적 필드들이므로 기본 구조만 검증
        if not isinstance(indicators_data, dict):
            result.add_error("지표 섹션은 딕셔너리여야 합니다")

    # ===============================================================================
    # === 헬퍼 메서드 - 환경별 요구사항 검증 ===
    # ===============================================================================

    def _validate_production_requirements(self, profile_data: Dict[str, Any], result: ValidationResult):
        """프로덕션 환경 요구사항 검증"""
        # 프로덕션에서는 페이퍼 트레이딩이 False여야 함
        upbit_section = profile_data.get('upbit', {})
        if upbit_section.get('paper_trading', True):
            result.add_warning("프로덕션 환경에서는 페이퍼 트레이딩을 비활성화하는 것이 권장됩니다")

        # API 키 설정 필수
        if not upbit_section.get('api_key_file') or not upbit_section.get('secret_key_file'):
            result.add_error("프로덕션 환경에서는 API 키 설정이 필수입니다")

    def _validate_development_requirements(self, profile_data: Dict[str, Any], result: ValidationResult):
        """개발 환경 요구사항 검증"""
        # 개발에서는 페이퍼 트레이딩이 True여야 함
        upbit_section = profile_data.get('upbit', {})
        if not upbit_section.get('paper_trading', True):
            result.add_warning("개발 환경에서는 페이퍼 트레이딩을 활성화하는 것이 권장됩니다")

    def _validate_testing_requirements(self, profile_data: Dict[str, Any], result: ValidationResult):
        """테스트 환경 요구사항 검증"""
        # 테스트에서는 페이퍼 트레이딩이 True여야 함
        upbit_section = profile_data.get('upbit', {})
        if not upbit_section.get('paper_trading', True):
            result.add_error("테스트 환경에서는 페이퍼 트레이딩이 활성화되어야 합니다")

    def _validate_custom_requirements(self, profile_data: Dict[str, Any], result: ValidationResult):
        """커스텀 환경 요구사항 검증"""
        # 커스텀 환경에 대한 일반적인 검증
        upbit_section = profile_data.get('upbit', {})
        if 'paper_trading' not in upbit_section:
            result.add_warning("커스텀 환경에서는 페이퍼 트레이딩 설정을 명시하는 것이 권장됩니다")

    def _validate_common_compatibility(self, profile_data: Dict[str, Any], result: ValidationResult):
        """공통 호환성 검증"""
        # 모든 환경에 공통으로 적용되는 호환성 검증
        pass

    def _validate_api_key_compatibility(self, profile_data: Dict[str, Any], result: ValidationResult):
        """API 키 설정 호환성 검증"""
        upbit_section = profile_data.get('upbit', {})
        paper_trading = upbit_section.get('paper_trading', True)
        api_key_file = upbit_section.get('api_key_file', '')
        secret_key_file = upbit_section.get('secret_key_file', '')

        if not paper_trading and (not api_key_file or not secret_key_file):
            result.add_error("실제 거래 모드에서는 API 키와 시크릿 키가 모두 필요합니다")

    # ===============================================================================
    # === 헬퍼 메서드 - 프로파일 간 일관성 검증 ===
    # ===============================================================================

    def _validate_structure_consistency(self, profiles: Dict[str, Dict[str, Any]], result: ValidationResult):
        """프로파일 간 구조 일관성 검증"""
        if len(profiles) < 2:
            return

        base_profile = next(iter(profiles.values()))
        base_sections = set(base_profile.keys())

        for profile_name, profile_data in profiles.items():
            current_sections = set(profile_data.keys())
            missing_sections = base_sections - current_sections
            extra_sections = current_sections - base_sections

            if missing_sections:
                result.add_warning(f"프로파일 '{profile_name}'에 누락된 섹션: {missing_sections}")

            if extra_sections:
                result.add_warning(f"프로파일 '{profile_name}'의 추가 섹션: {extra_sections}")

    def _validate_settings_consistency(self, profiles: Dict[str, Dict[str, Any]], result: ValidationResult):
        """프로파일 간 설정값 일관성 검증"""
        # 특정 설정값들이 프로파일 간에 일관성을 유지해야 하는 경우 검증
        pass

    def _validate_environment_specific_consistency(self, profiles: Dict[str, Dict[str, Any]], result: ValidationResult):
        """환경별 특수 요구사항 일관성 검증"""
        # 환경별로 다른 요구사항들의 일관성 검증
        pass

    # ===============================================================================
    # === 헬퍼 메서드 - 파일 및 데이터 처리 ===
    # ===============================================================================

    def _validate_file_accessibility(self, file_path: str, result: ValidationResult) -> bool:
        """파일 접근성 검증"""
        try:
            path = Path(file_path)

            if not path.exists():
                result.add_error(f"파일이 존재하지 않습니다: {file_path}")
                return False

            if not path.is_file():
                result.add_error(f"디렉터리입니다, 파일이 아닙니다: {file_path}")
                return False

            if not path.suffix.lower() in ['.yaml', '.yml']:
                result.add_warning(f"YAML 파일 확장자가 아닙니다: {file_path}")

            return True

        except Exception as e:
            result.add_error(f"파일 접근성 확인 실패: {str(e)}")
            return False

    def _load_profile_content(self, file_path: str) -> str:
        """프로파일 파일 내용 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"❌ 파일 로드 실패: {file_path} - {str(e)}")
            return ""
