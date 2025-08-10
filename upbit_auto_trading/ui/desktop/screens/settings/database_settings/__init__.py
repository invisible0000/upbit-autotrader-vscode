"""
Database Settings Module
========================

데이터베이스 설정 관리 모듈 (DDD + MVP 패턴)

Components:
- DatabaseSettingsView: 데이터베이스 설정 화면 (View)
- DatabaseSettingsPresenter: 비즈니스 로직 처리 (Presenter)
- Database Widgets: 전용 위젯들

Architecture:
- MVP Pattern with clear separation
- DDD Application Layer integration
- Infrastructure Layer repositories
"""

from .views.database_settings_view import DatabaseSettingsView
from .presenters.database_settings_presenter import DatabaseSettingsPresenter

# 호환성 alias (settings_screen.py에서 사용)
DatabaseSettings = DatabaseSettingsView

__all__ = [
    'DatabaseSettingsView',
    'DatabaseSettingsPresenter',
    'DatabaseSettings'
]
