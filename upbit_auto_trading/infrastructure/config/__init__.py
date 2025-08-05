"""
Configuration Management System
Infrastructure Layer - 설정 관리 시스템 공개 인터페이스

이 모듈은 애플리케이션 설정 관리를 위한 핵심 클래스들을 제공합니다:
- ApplicationConfig: 타입 안전한 애플리케이션 설정 모델
- Environment: 환경별 설정 분리 (development, testing, production)
- ConfigLoader: YAML 기반 계층적 설정 로딩
- EnvironmentConfigManager: 환경별 설정 캐싱 및 관리
"""

from .models.config_models import ApplicationConfig, Environment
from .loaders.config_loader import ConfigLoader, EnvironmentConfigManager

__all__ = [
    'ApplicationConfig',
    'Environment',
    'ConfigLoader',
    'EnvironmentConfigManager'
]

# 버전 정보
__version__ = '1.0.0'
__author__ = 'Upbit Auto Trading Team'
