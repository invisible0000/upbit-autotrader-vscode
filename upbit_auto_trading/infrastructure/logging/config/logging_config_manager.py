"""
로깅 설정 파일 관리자
==================

환경변수 대신 YAML 설정 파일을 기반으로 로깅 시스템을 관리합니다.

주요 기능:
- config/logging_config.yaml 기반 설정 관리
- 실행 중 안전한 설정 변경
- 환경 프로파일 연동
- 명령행 인수 오버라이드 지원
- 실시간 설정 파일 감시 및 리로드
"""

import os
import yaml
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import json


class LoggingConfigManager:
    """로깅 설정 파일 관리자

    환경변수 방식을 대체하는 안전하고 유연한 설정 시스템
    """

    def __init__(self, config_file: Optional[str] = None, profile: Optional[str] = None):
        """초기화

        Args:
            config_file: 설정 파일 경로 (기본: config/logging_config.yaml)
            profile: 환경 프로파일 (development, testing, production 등)
        """
        self._lock = threading.RLock()

        # 설정 파일 경로
        if config_file:
            self._config_file = Path(config_file)
        else:
            self._config_file = Path("config/logging_config.yaml")

        # 현재 프로파일
        self._current_profile = profile or self._detect_current_profile()

        # 변경 핸들러
        self._change_handlers: List[Callable[[Dict[str, Any]], None]] = []

        # 캐시된 설정
        self._cached_config: Optional[Dict[str, Any]] = None
        self._last_modified: Optional[float] = None

        # 초기 설정 로드
        self._load_config()

    def _detect_current_profile(self) -> str:
        """현재 환경 프로파일 감지

        Returns:
            str: 감지된 프로파일명
        """
        # 환경변수에서 프로파일 확인
        env_profile = os.getenv('UPBIT_ENVIRONMENT', '')
        if env_profile:
            return env_profile

        # 기본값
        return 'development'

    def _load_config(self) -> None:
        """설정 파일 로드"""
        with self._lock:
            try:
                if not self._config_file.exists():
                    print(f"⚠️ 로깅 설정 파일이 없습니다: {self._config_file}")
                    self._cached_config = self._get_default_config()
                    return

                # 파일 수정 시간 확인
                current_mtime = self._config_file.stat().st_mtime
                if self._last_modified and current_mtime <= self._last_modified:
                    return  # 변경되지 않음

                # YAML 파일 로드
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                if not config:
                    config = self._get_default_config()

                # 프로파일별 오버라이드 적용
                config = self._apply_profile_overrides(config)

                self._cached_config = config
                self._last_modified = current_mtime

                # 변경 알림
                self._notify_change_handlers(config)

            except Exception as e:
                print(f"❌ 로깅 설정 로드 실패: {e}")
                self._cached_config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """기본 설정 반환

        Returns:
            Dict[str, Any]: 기본 로깅 설정
        """
        return {
            'logging': {
                'level': 'INFO',
                'console_output': False,
                'scope': 'normal',
                'component_focus': '',
                'context': 'development',
                'file_logging': {
                    'enabled': True,
                    'path': 'logs',
                    'level': 'DEBUG',
                    'max_size_mb': 10,
                    'backup_count': 5
                },
                'advanced': {
                    'performance_monitoring': False
                }
            },
            'runtime': {
                'watch_config_file': True,
                'notify_on_change': True,
                'last_modified': datetime.now().isoformat()
            }
        }

    def _apply_profile_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """프로파일별 오버라이드 적용

        Args:
            config: 기본 설정

        Returns:
            Dict[str, Any]: 프로파일이 적용된 설정
        """
        if 'profile_overrides' not in config:
            return config

        profile_overrides = config['profile_overrides']
        if self._current_profile not in profile_overrides:
            return config

        # 딥 머지
        override_config = profile_overrides[self._current_profile]
        merged_config = self._deep_merge(config.copy(), override_config)

        return merged_config

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """딥 머지 수행

        Args:
            base: 기본 딕셔너리
            override: 오버라이드 딕셔너리

        Returns:
            Dict[str, Any]: 머지된 딕셔너리
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def get_logging_config(self) -> Dict[str, Any]:
        """로깅 설정 조회

        Returns:
            Dict[str, Any]: 현재 로깅 설정
        """
        self._load_config()  # 최신 설정 로드
        if self._cached_config is None:
            return self._get_default_config().get('logging', {})
        return self._cached_config.get('logging', {})

    def get_advanced_config(self) -> Dict[str, Any]:
        """고급 설정 조회

        Returns:
            Dict[str, Any]: 고급 로깅 설정
        """
        self._load_config()
        if self._cached_config is None:
            return self._get_default_config().get('advanced', {})
        return self._cached_config.get('advanced', {})

    def get_file_logging_config(self) -> Dict[str, Any]:
        """파일 로깅 설정 조회

        Returns:
            Dict[str, Any]: 파일 로깅 설정
        """
        self._load_config()
        if self._cached_config is None:
            return self._get_default_config().get('file_logging', {})
        return self._cached_config.get('file_logging', {})

    def get_all_config(self) -> Dict[str, Any]:
        """전체 설정 조회

        Returns:
            Dict[str, Any]: 전체 로깅 설정
        """
        self._load_config()
        if self._cached_config is None:
            return self._get_default_config()
        return self._cached_config.copy()

    def get_current_config(self) -> Dict[str, Any]:
        """현재 설정 조회 (get_all_config 별칭)

        Returns:
            Dict[str, Any]: 현재 로깅 설정
        """
        return self.get_all_config()

    def update_logging_config(self, updates: Dict[str, Any], save_to_file: bool = True) -> bool:
        """로깅 설정 업데이트

        Args:
            updates: 업데이트할 설정 (전체 구조 또는 부분 업데이트)
            save_to_file: 파일에 저장할지 여부

        Returns:
            bool: 업데이트 성공 여부
        """
        with self._lock:
            try:
                # 현재 설정 로드
                self._load_config()
                config = self._cached_config.copy() if self._cached_config else self._get_default_config()

                # 전체 설정 업데이트인지 부분 업데이트인지 판단
                if 'logging' in updates and isinstance(updates['logging'], dict):
                    # 전체 설정 업데이트 - 전체 구조 교체
                    config = self._deep_merge(config, updates)
                else:
                    # 부분 업데이트 - logging 섹션만 업데이트
                    if 'logging' not in config:
                        config['logging'] = {}
                    config['logging'].update(updates)

                # 중복 섹션 정리 - file_logging과 advanced가 최상위에 있으면 제거
                if 'file_logging' in config and 'logging' in config and 'file_logging' in config['logging']:
                    # logging 내부 file_logging을 우선으로 하고 최상위 제거
                    config.pop('file_logging', None)

                if 'advanced' in config and 'logging' in config and 'advanced' in config['logging']:
                    # logging 내부 advanced를 우선으로 하고 최상위 제거
                    config.pop('advanced', None)

                # runtime 섹션 보장
                if 'runtime' not in config:
                    config['runtime'] = {}
                config['runtime']['last_modified'] = datetime.now().isoformat()

                # 파일에 저장
                if save_to_file:
                    self._save_config_to_file(config)

                # 캐시 업데이트
                self._cached_config = config

                # 변경 알림
                self._notify_change_handlers(config)

                return True

            except Exception as e:
                print(f"❌ 로깅 설정 업데이트 실패: {e}")
                return False

    def _save_config_to_file(self, config: Dict[str, Any]) -> None:
        """설정을 파일에 저장

        Args:
            config: 저장할 설정
        """
        try:
            # 디렉토리 생성
            self._config_file.parent.mkdir(parents=True, exist_ok=True)

            # YAML 파일로 저장
            with open(self._config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            # 수정 시간 업데이트
            self._last_modified = self._config_file.stat().st_mtime

        except Exception as e:
            print(f"❌ 설정 파일 저장 실패: {e}")
            raise

    def set_profile(self, profile: str) -> bool:
        """환경 프로파일 변경

        Args:
            profile: 새 프로파일명

        Returns:
            bool: 변경 성공 여부
        """
        if profile != self._current_profile:
            self._current_profile = profile
            self._cached_config = None  # 캐시 무효화
            self._load_config()  # 새 프로파일로 리로드
            return True
        return False

    def get_current_profile(self) -> str:
        """현재 프로파일 조회

        Returns:
            str: 현재 프로파일명
        """
        return self._current_profile

    def reset_to_defaults(self, save_to_file: bool = True) -> bool:
        """기본값으로 리셋

        Args:
            save_to_file: 파일에 저장할지 여부

        Returns:
            bool: 리셋 성공 여부
        """
        try:
            config = self._get_default_config()

            if save_to_file:
                self._save_config_to_file(config)

            self._cached_config = config
            self._notify_change_handlers(config)

            return True

        except Exception as e:
            print(f"❌ 기본값 리셋 실패: {e}")
            return False

    def add_change_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """설정 변경 핸들러 추가

        Args:
            handler: 변경 알림 함수
        """
        with self._lock:
            if handler not in self._change_handlers:
                self._change_handlers.append(handler)

    def remove_change_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """설정 변경 핸들러 제거

        Args:
            handler: 제거할 핸들러
        """
        with self._lock:
            if handler in self._change_handlers:
                self._change_handlers.remove(handler)

    def _notify_change_handlers(self, config: Dict[str, Any]) -> None:
        """설정 변경 알림

        Args:
            config: 변경된 설정
        """
        handlers_copy = self._change_handlers.copy()

        for handler in handlers_copy:
            try:
                handler(config)
            except Exception as e:
                print(f"⚠️ 설정 변경 핸들러 오류: {e}")

    def get_status_summary(self) -> Dict[str, Any]:
        """상태 요약 조회

        Returns:
            Dict[str, Any]: 상태 요약
        """
        return {
            'config_file': str(self._config_file),
            'current_profile': self._current_profile,
            'file_exists': self._config_file.exists(),
            'last_modified': self._last_modified,
            'handlers_count': len(self._change_handlers),
            'cached_config_loaded': self._cached_config is not None
        }
