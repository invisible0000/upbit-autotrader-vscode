"""
테스트 공용 픽스처 및 유틸리티

Given-When-Then 패턴과 DDD 아키텍처를 위한 공용 설정
"""
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock
import pytest
from typing import Generator, Tuple, Dict, Any

# 테스트용 환경변수 설정
os.environ['UPBIT_CONSOLE_OUTPUT'] = 'false'  # 테스트 중 로그 출력 제한
os.environ['UPBIT_LOG_SCOPE'] = 'minimal'


@pytest.fixture
def temp_directory() -> Generator[Path, None, None]:
    """임시 디렉토리 생성 픽스처"""
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)

    yield temp_path

    # 정리
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_api_key_service() -> Mock:
    """Mock API 키 서비스 픽스처"""
    mock_service = Mock()

    # 기본 Mock 설정
    mock_service.save_api_keys.return_value = True
    mock_service.load_api_keys.return_value = (None, None, False)
    mock_service.delete_api_keys.return_value = True
    mock_service.has_valid_keys.return_value = False
    mock_service.test_api_connection.return_value = (True, "연결 성공", {"KRW": {"total": 10000.0}})
    mock_service.get_secret_key_mask_length.return_value = 72

    # 새로운 메서드들 Mock 설정
    mock_service.save_api_keys_clean.return_value = (True, "저장 완료")
    mock_service.delete_api_keys_smart.return_value = "삭제 완료"
    mock_service.get_cache_status.return_value = {
        'cached': False,
        'valid': False,
        'age_seconds': None,
        'ttl_seconds': 300,
        'keys_hash': None
    }

    return mock_service


@pytest.fixture
def sample_api_credentials() -> Dict[str, Any]:
    """테스트용 API 자격증명 데이터"""
    return {
        'access_key': 'test_access_key_123456789',
        'secret_key': 'test_secret_key_abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNO',
        'trade_permission': True
    }


@pytest.fixture
def sample_invalid_credentials() -> Dict[str, Any]:
    """테스트용 잘못된 API 자격증명 데이터"""
    return {
        'access_key': '',
        'secret_key': '',
        'trade_permission': False
    }


@pytest.fixture
def sample_masked_credentials() -> Dict[str, Any]:
    """테스트용 마스킹된 API 자격증명 데이터"""
    return {
        'access_key': 'test_access_key_123456789',
        'secret_key': '●' * 72,  # 마스킹된 Secret Key
        'trade_permission': True
    }


class MockQWidget:
    """Qt 위젯 Mock 클래스"""
    def __init__(self):
        self.enabled = True
        self._text = ""
        self.checked = False
        self.tooltip = ""

    def setEnabled(self, enabled: bool):
        self.enabled = enabled

    def isEnabled(self) -> bool:
        return self.enabled

    def setText(self, text: str):
        self._text = text

    def text(self) -> str:
        return self._text

    def setChecked(self, checked: bool):
        self.checked = checked

    def isChecked(self) -> bool:
        return self.checked

    def setToolTip(self, tooltip: str):
        self.tooltip = tooltip

    def toolTip(self) -> str:
        return self.tooltip


class MockMessageBox:
    """Qt QMessageBox Mock 클래스"""

    class StandardButton:
        Yes = 'Yes'
        No = 'No'

    @staticmethod
    def question(parent, title: str, text: str, buttons, default_button=None):
        """Mock question dialog - 기본적으로 Yes 반환"""
        return MockMessageBox.StandardButton.Yes

    @staticmethod
    def information(parent, title: str, text: str):
        """Mock information dialog"""
        pass

    @staticmethod
    def warning(parent, title: str, text: str):
        """Mock warning dialog"""
        pass


def create_test_api_response_success() -> Tuple[bool, str, Dict[str, Any]]:
    """성공적인 API 응답 생성"""
    return (
        True,
        "API 연결 성공 (총 2개 계좌, KRW: 50,000원)",
        {
            'KRW': {'balance': 45000.0, 'locked': 5000.0, 'total': 50000.0},
            'BTC': {'balance': 0.001, 'locked': 0.0, 'total': 0.001}
        }
    )


def create_test_api_response_failure() -> Tuple[bool, str, Dict[str, Any]]:
    """실패한 API 응답 생성"""
    return (
        False,
        "API 키가 올바르지 않습니다",
        {}
    )


def create_test_api_response_network_error() -> Tuple[bool, str, Dict[str, Any]]:
    """네트워크 에러 API 응답 생성"""
    return (
        False,
        "네트워크 연결 오류: 업비트 서버에 연결할 수 없습니다",
        {}
    )


@pytest.fixture
def mock_secure_keys_repository() -> Mock:
    """Mock SecureKeysRepository 픽스처"""
    mock_repo = Mock()
    mock_repo.save_key.return_value = True
    mock_repo.load_key.return_value = None
    mock_repo.delete_key.return_value = True
    mock_repo.key_exists.return_value = False
    return mock_repo


# 테스트 데이터 상수
TEST_ACCESS_KEY = "test_access_key_1234567890abcdef"
TEST_SECRET_KEY = "test_secret_key_abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNO"
TEST_INVALID_ACCESS_KEY = ""
TEST_INVALID_SECRET_KEY = ""
TEST_MASKED_SECRET_KEY = "●" * 72
