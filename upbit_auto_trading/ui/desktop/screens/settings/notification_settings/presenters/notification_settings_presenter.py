"""
알림 설정 Presenter - MVP 패턴 구현

이 모듈은 알림 설정의 비즈니스 로직을 담당하는 Presenter입니다.
DDD 아키텍처에서 Application Layer 역할을 수행합니다.
"""

from typing import Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal

# Infrastructure Layer Enhanced Logging v4.0
# Application Layer - Infrastructure 의존성 격리 (Phase 2 수정)

class NotificationSettingsPresenter(QObject):
    """알림 설정 Presenter - MVP 패턴 Application Layer"""

    # View 업데이트 시그널
    settings_updated = pyqtSignal(dict)
    settings_changed = pyqtSignal()

    def __init__(self):
        """초기화"""
        super().__init__()
        if logging_service:
            self.logger = logging_service.get_component_logger("NotificationSettingsPresenter")
        else:
            raise ValueError("NotificationSettingsPresenter에 logging_service가 주입되지 않았습니다")
        self.logger.info("🎛️ NotificationSettingsPresenter 초기화")

        # 기본 설정 값 (Domain Model)
        self._settings = {
            'enable_price_alerts': True,
            'enable_trade_alerts': True,
            'enable_system_alerts': True,
            'notification_sound': True,
            'desktop_notifications': True,
            'email_notifications': False,
            'email_address': '',
            'notification_frequency': 'immediate',  # immediate, hourly, daily
            'quiet_hours_enabled': False,
            'quiet_hours_start': 22,  # 22:00
            'quiet_hours_end': 8,  # 08:00
        }

        self._report_to_infrastructure()

    def _report_to_infrastructure(self):
        """Infrastructure Layer 상태 보고 (레거시 briefing 시스템 제거됨)"""
        self.logger.debug("알림 설정 Presenter 상태 보고 완료")

    def get_current_settings(self) -> Dict[str, Any]:
        """현재 설정 값 반환"""
        return self._settings.copy()

    def update_setting(self, key: str, value: Any) -> None:
        """개별 설정 업데이트"""
        if key in self._settings:
            old_value = self._settings[key]
            self._settings[key] = value
            self.logger.debug(f"🔧 설정 업데이트: {key} = {old_value} → {value}")

            # View에 변경사항 알림
            self.settings_updated.emit(self._settings.copy())
            self.settings_changed.emit()
        else:
            self.logger.warning(f"❌ 알 수 없는 설정 키: {key}")

    def update_multiple_settings(self, settings: Dict[str, Any]) -> None:
        """여러 설정 일괄 업데이트"""
        updated_keys = []
        for key, value in settings.items():
            if key in self._settings:
                old_value = self._settings[key]
                self._settings[key] = value
                updated_keys.append(f"{key}={old_value}→{value}")

        if updated_keys:
            self.logger.info(f"🔧 일괄 설정 업데이트: {', '.join(updated_keys)}")
            self.settings_updated.emit(self._settings.copy())
            self.settings_changed.emit()

    def validate_settings(self) -> bool:
        """설정 유효성 검증"""
        try:
            # 방해 금지 시간 유효성 검증
            if self._settings['quiet_hours_enabled']:
                start = self._settings['quiet_hours_start']
                end = self._settings['quiet_hours_end']
                if not (0 <= start <= 23 and 0 <= end <= 23):
                    self.logger.error("❌ 방해 금지 시간이 유효하지 않음")
                    return False

            # 알림 빈도 유효성 검증
            valid_frequencies = ['immediate', 'hourly', 'daily']
            if self._settings['notification_frequency'] not in valid_frequencies:
                self.logger.error("❌ 알림 빈도가 유효하지 않음")
                return False

            self.logger.debug("✅ 설정 유효성 검증 통과")
            return True

        except Exception as e:
            self.logger.error(f"❌ 설정 유효성 검증 실패: {e}")
            return False

    def load_settings(self) -> bool:
        """설정 로드 (추후 DB/파일 연동 예정)"""
        try:
            # 현재는 기본값 사용, 추후 Infrastructure Layer와 연동
            self.logger.info("📥 알림 설정 로드 (기본값 사용)")
            self.settings_updated.emit(self._settings.copy())
            return True
        except Exception as e:
            self.logger.error(f"❌ 설정 로드 실패: {e}")
            return False

    def save_settings(self) -> bool:
        """설정 저장 (추후 DB/파일 연동 예정)"""
        try:
            if not self.validate_settings():
                return False

            # 현재는 메모리에만 저장, 추후 Infrastructure Layer와 연동
            self.logger.info("💾 알림 설정 저장 완료")
            return True
        except Exception as e:
            self.logger.error(f"❌ 설정 저장 실패: {e}")
            return False

    def reset_to_defaults(self) -> None:
        """기본값으로 재설정"""
        default_settings = {
            'enable_price_alerts': True,
            'enable_trade_alerts': True,
            'enable_system_alerts': True,
            'notification_sound': True,
            'desktop_notifications': True,
            'email_notifications': False,
            'email_address': '',
            'notification_frequency': 'immediate',
            'quiet_hours_enabled': False,
            'quiet_hours_start': 22,
            'quiet_hours_end': 8,
        }

        self._settings = default_settings
        self.logger.info("🔄 알림 설정을 기본값으로 재설정")
        self.settings_updated.emit(self._settings.copy())
        self.settings_changed.emit()

    def get_active_notification_types(self) -> list:
        """활성화된 알림 유형 목록 반환"""
        active_types = []
        if self._settings['enable_price_alerts']:
            active_types.append('price')
        if self._settings['enable_trade_alerts']:
            active_types.append('trade')
        if self._settings['enable_system_alerts']:
            active_types.append('system')
        return active_types

    def get_active_notification_methods(self) -> list:
        """활성화된 알림 방법 목록 반환"""
        active_methods = []
        if self._settings['notification_sound']:
            active_methods.append('sound')
        if self._settings['desktop_notifications']:
            active_methods.append('desktop')
        if self._settings['email_notifications']:
            active_methods.append('email')
        return active_methods

    def is_quiet_hours_active(self, current_hour: int) -> bool:
        """현재 시간이 방해 금지 시간인지 확인"""
        if not self._settings['quiet_hours_enabled']:
            return False

        start = self._settings['quiet_hours_start']
        end = self._settings['quiet_hours_end']

        # 자정을 넘지 않는 경우 (예: 22시-8시)
        if start < end:
            return start <= current_hour < end
        # 자정을 넘는 경우 (예: 22시-8시)
        else:
            return current_hour >= start or current_hour < end
