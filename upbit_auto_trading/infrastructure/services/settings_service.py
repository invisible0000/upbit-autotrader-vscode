"""
설정 서비스 구현

Configuration Management를 활용한 UI 및 매매 설정 관리
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from pathlib import Path
import json

from upbit_auto_trading.infrastructure.config.models.config_models import UIConfig, TradingConfig
from upbit_auto_trading.infrastructure.config.loaders.config_loader import ConfigLoader

class ISettingsService(ABC):
    """설정 서비스 인터페이스"""

    @abstractmethod
    def get_ui_config(self) -> UIConfig:
        """UI 설정 반환"""
        pass

    @abstractmethod
    def get_trading_config(self) -> TradingConfig:
        """매매 설정 반환"""
        pass

    @abstractmethod
    def update_ui_setting(self, key: str, value: Any) -> bool:
        """UI 설정 업데이트"""
        pass

    @abstractmethod
    def update_trading_setting(self, key: str, value: Any) -> bool:
        """매매 설정 업데이트"""
        pass

    @abstractmethod
    def save_window_state(self, x: int, y: int, width: int, height: int, maximized: bool) -> bool:
        """창 상태 저장"""
        pass

    @abstractmethod
    def load_window_state(self) -> Optional[Dict[str, Any]]:
        """창 상태 로드"""
        pass

    @abstractmethod
    def reset_to_defaults(self, section: str = "all") -> bool:
        """기본값으로 리셋"""
        pass

class SettingsService(ISettingsService):
    """설정 서비스 구현체 (Configuration Management 기반)"""

    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader
        self._user_settings_path = Path("config/user_settings.json")
        self._user_settings = self._load_user_settings()

    def _load_user_settings(self) -> Dict[str, Any]:
        """사용자 설정 파일 로드"""
        if self._user_settings_path.exists():
            try:
                with open(self._user_settings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 사용자 설정 로드 실패: {e}")

        return {
            "ui": {},
            "trading": {},
            "window_state": {}
        }

    def _save_user_settings(self) -> bool:
        """사용자 설정 파일 저장"""
        try:
            self._user_settings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._user_settings_path, 'w', encoding='utf-8') as f:
                json.dump(self._user_settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ 사용자 설정 저장 실패: {e}")
            return False

    def get_ui_config(self) -> UIConfig:
        """UI 설정 반환 (기본값 + 사용자 오버라이드)"""
        config = self.config_loader.load_config()
        base_ui_config = config.ui

        # 사용자 설정으로 오버라이드
        user_ui = self._user_settings.get("ui", {})

        # 기본 설정을 dict로 변환하고 사용자 설정으로 업데이트
        ui_dict = base_ui_config.__dict__.copy()
        ui_dict.update(user_ui)

        # UIConfig 객체로 재생성
        return UIConfig(**ui_dict)

    def get_trading_config(self) -> TradingConfig:
        """매매 설정 반환 (기본값 + 사용자 오버라이드)"""
        config = self.config_loader.load_config()
        base_trading_config = config.trading

        # 사용자 설정으로 오버라이드
        user_trading = self._user_settings.get("trading", {})

        # 기본 설정을 dict로 변환하고 사용자 설정으로 업데이트
        trading_dict = base_trading_config.__dict__.copy()
        trading_dict.update(user_trading)

        # TradingConfig 객체로 재생성
        return TradingConfig(**trading_dict)

    def update_ui_setting(self, key: str, value: Any) -> bool:
        """UI 설정 업데이트"""
        try:
            if "ui" not in self._user_settings:
                self._user_settings["ui"] = {}

            self._user_settings["ui"][key] = value
            return self._save_user_settings()
        except Exception as e:
            print(f"❌ UI 설정 업데이트 실패 ({key}={value}): {e}")
            return False

    def update_trading_setting(self, key: str, value: Any) -> bool:
        """매매 설정 업데이트"""
        try:
            if "trading" not in self._user_settings:
                self._user_settings["trading"] = {}

            self._user_settings["trading"][key] = value
            return self._save_user_settings()
        except Exception as e:
            print(f"❌ 매매 설정 업데이트 실패 ({key}={value}): {e}")
            return False

    def save_window_state(self, x: int, y: int, width: int, height: int, maximized: bool) -> bool:
        """창 상태 저장"""
        try:
            self._user_settings["window_state"] = {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "maximized": maximized
            }
            return self._save_user_settings()
        except Exception as e:
            print(f"❌ 창 상태 저장 실패: {e}")
            return False

    def load_window_state(self) -> Optional[Dict[str, Any]]:
        """창 상태 로드"""
        return self._user_settings.get("window_state")

    def reset_to_defaults(self, section: str = "all") -> bool:
        """기본값으로 리셋"""
        try:
            if section == "all":
                self._user_settings = {
                    "ui": {},
                    "trading": {},
                    "window_state": {}
                }
            elif section == "ui":
                self._user_settings["ui"] = {}
            elif section == "trading":
                self._user_settings["trading"] = {}
            elif section == "window_state":
                self._user_settings["window_state"] = {}
            else:
                return False

            return self._save_user_settings()
        except Exception as e:
            print(f"❌ 설정 리셋 실패 ({section}): {e}")
            return False

class MockSettingsService(ISettingsService):
    """Mock 설정 서비스 (테스트용)"""

    def __init__(self):
        self._ui_config = UIConfig()
        self._trading_config = TradingConfig()
        self._window_state = None

    def get_ui_config(self) -> UIConfig:
        return self._ui_config

    def get_trading_config(self) -> TradingConfig:
        return self._trading_config

    def update_ui_setting(self, key: str, value: Any) -> bool:
        setattr(self._ui_config, key, value)
        return True

    def update_trading_setting(self, key: str, value: Any) -> bool:
        setattr(self._trading_config, key, value)
        return True

    def save_window_state(self, x: int, y: int, width: int, height: int, maximized: bool) -> bool:
        self._window_state = {
            "x": x, "y": y, "width": width, "height": height, "maximized": maximized
        }
        return True

    def load_window_state(self) -> Optional[Dict[str, Any]]:
        return self._window_state

    def reset_to_defaults(self, section: str = "all") -> bool:
        if section in ["all", "ui"]:
            self._ui_config = UIConfig()
        if section in ["all", "trading"]:
            self._trading_config = TradingConfig()
        if section in ["all", "window_state"]:
            self._window_state = None
        return True
