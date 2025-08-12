"""
환경변수 실시간 관리 시스템
========================

Phase 2: Infrastructure Integration
Infrastructure 로깅 시스템의 환경변수를 실시간으로 관리하는 시스템입니다.

주요 기능:
- 환경변수 실시간 읽기/쓰기
- 로깅 시스템 재시작 없이 즉시 적용
- 변경 이력 추적
- 오류 복구 및 롤백 지원
"""

import os
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime


class EnvironmentVariableManager:
    """Infrastructure 로깅 시스템 환경변수 실시간 관리

    Phase 2 핵심 컴포넌트:
    - UPBIT_LOG_LEVEL, UPBIT_CONSOLE_OUTPUT 등 환경변수 관리
    - 실시간 변경 및 즉시 적용
    - 변경 이력 추적 및 롤백 지원
    """

    # Infrastructure 로깅 시스템 환경변수 정의
    SUPPORTED_VARIABLES = {
        'UPBIT_LOG_LEVEL': {
            'type': 'choice',
            'choices': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            'default': 'INFO',
            'description': '로그 레벨 설정'
        },
        'UPBIT_CONSOLE_OUTPUT': {
            'type': 'boolean',
            'default': 'false',
            'description': '콘솔 출력 활성화'
        },
        'UPBIT_LOG_SCOPE': {
            'type': 'choice',
            'choices': ['silent', 'minimal', 'normal', 'verbose', 'debug_all'],
            'default': 'normal',
            'description': '로그 스코프 설정'
        },
        'UPBIT_COMPONENT_FOCUS': {
            'type': 'string',
            'default': '',
            'description': '특정 컴포넌트 집중 로깅'
        },
        'UPBIT_LOG_CONTEXT': {
            'type': 'choice',
            'choices': ['development', 'testing', 'staging', 'production'],
            'default': 'development',
            'description': '로깅 컨텍스트'
        }
    }

    def __init__(self):
        """EnvironmentVariableManager 초기화"""
        self._lock = threading.RLock()
        self._change_handlers: List[Callable[[str, str, str], None]] = []
        self._change_history: List[Dict[str, Any]] = []
        self._original_values: Dict[str, str] = {}

        # 초기 상태 저장
        self._save_original_state()

    def _save_original_state(self) -> None:
        """초기 환경변수 상태 저장 (롤백용)"""
        for var_name in self.SUPPORTED_VARIABLES:
            self._original_values[var_name] = os.getenv(var_name, '')

    def get_variable(self, var_name: str) -> str:
        """환경변수 값 조회

        Args:
            var_name: 환경변수 이름

        Returns:
            str: 환경변수 값 (없으면 기본값)
        """
        if var_name not in self.SUPPORTED_VARIABLES:
            raise ValueError(f"지원하지 않는 환경변수: {var_name}")

        default_value = self.SUPPORTED_VARIABLES[var_name]['default']
        return os.getenv(var_name, default_value)

    def set_variable(self, var_name: str, value: str) -> bool:
        """환경변수 값 설정

        Args:
            var_name: 환경변수 이름
            value: 설정할 값

        Returns:
            bool: 설정 성공 여부
        """
        with self._lock:
            if var_name not in self.SUPPORTED_VARIABLES:
                raise ValueError(f"지원하지 않는 환경변수: {var_name}")

            try:
                # 값 검증
                if not self._validate_value(var_name, value):
                    return False

                # 이전 값 저장
                old_value = self.get_variable(var_name)

                # 환경변수 설정
                os.environ[var_name] = value

                # 변경 이력 기록
                self._record_change(var_name, old_value, value)

                # 변경 알림
                self._notify_change_handlers(var_name, old_value, value)

                return True

            except Exception as e:
                print(f"❌ 환경변수 설정 실패 ({var_name}={value}): {e}")
                return False

    def get_all_variables(self) -> Dict[str, str]:
        """모든 지원 환경변수 조회

        Returns:
            Dict[str, str]: 환경변수 이름-값 딕셔너리
        """
        result = {}
        for var_name in self.SUPPORTED_VARIABLES:
            result[var_name] = self.get_variable(var_name)
        return result

    def set_multiple_variables(self, variables: Dict[str, str]) -> Dict[str, bool]:
        """여러 환경변수 일괄 설정

        Args:
            variables: 설정할 환경변수 딕셔너리

        Returns:
            Dict[str, bool]: 각 변수별 설정 결과
        """
        results = {}
        for var_name, value in variables.items():
            results[var_name] = self.set_variable(var_name, value)
        return results

    def reset_variable(self, var_name: str) -> bool:
        """환경변수를 기본값으로 리셋

        Args:
            var_name: 환경변수 이름

        Returns:
            bool: 리셋 성공 여부
        """
        if var_name not in self.SUPPORTED_VARIABLES:
            raise ValueError(f"지원하지 않는 환경변수: {var_name}")

        default_value = self.SUPPORTED_VARIABLES[var_name]['default']
        return self.set_variable(var_name, default_value)

    def reset_all_variables(self) -> Dict[str, bool]:
        """모든 환경변수를 기본값으로 리셋

        Returns:
            Dict[str, bool]: 각 변수별 리셋 결과
        """
        results = {}
        for var_name in self.SUPPORTED_VARIABLES:
            results[var_name] = self.reset_variable(var_name)
        return results

    def rollback_to_original(self) -> Dict[str, bool]:
        """초기 상태로 롤백

        Returns:
            Dict[str, bool]: 각 변수별 롤백 결과
        """
        results = {}
        for var_name, original_value in self._original_values.items():
            if original_value:  # 원래 값이 있었던 경우만
                results[var_name] = self.set_variable(var_name, original_value)
            else:  # 원래 값이 없었던 경우 삭제
                try:
                    if var_name in os.environ:
                        del os.environ[var_name]
                    results[var_name] = True
                except Exception:
                    results[var_name] = False
        return results

    def add_change_handler(self, handler: Callable[[str, str, str], None]) -> None:
        """환경변수 변경 핸들러 추가

        Args:
            handler: 변경 알림 함수 (var_name, old_value, new_value)
        """
        with self._lock:
            if handler not in self._change_handlers:
                self._change_handlers.append(handler)

    def remove_change_handler(self, handler: Callable[[str, str, str], None]) -> None:
        """환경변수 변경 핸들러 제거

        Args:
            handler: 제거할 핸들러 함수
        """
        with self._lock:
            if handler in self._change_handlers:
                self._change_handlers.remove(handler)

    def get_change_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """환경변수 변경 이력 조회

        Args:
            limit: 반환할 최대 이력 수

        Returns:
            List[Dict[str, Any]]: 변경 이력 리스트
        """
        history = self._change_history.copy()
        if limit:
            history = history[-limit:]
        return history

    def get_variable_info(self, var_name: str) -> Dict[str, Any]:
        """환경변수 정보 조회

        Args:
            var_name: 환경변수 이름

        Returns:
            Dict[str, Any]: 환경변수 정보
        """
        if var_name not in self.SUPPORTED_VARIABLES:
            raise ValueError(f"지원하지 않는 환경변수: {var_name}")

        info = self.SUPPORTED_VARIABLES[var_name].copy()
        info['current_value'] = self.get_variable(var_name)
        info['original_value'] = self._original_values.get(var_name, '')
        return info

    def _validate_value(self, var_name: str, value: str) -> bool:
        """환경변수 값 검증

        Args:
            var_name: 환경변수 이름
            value: 검증할 값

        Returns:
            bool: 유효한 값인지 여부
        """
        var_info = self.SUPPORTED_VARIABLES[var_name]
        var_type = var_info['type']

        if var_type == 'choice':
            valid_choices = var_info['choices']
            if value not in valid_choices:
                print(f"❌ 잘못된 값: {var_name}={value}, 가능한 값: {valid_choices}")
                return False

        elif var_type == 'boolean':
            if value.lower() not in ['true', 'false']:
                print(f"❌ 잘못된 불린 값: {var_name}={value}, 가능한 값: true, false")
                return False

        # string 타입은 모든 값 허용
        return True

    def _record_change(self, var_name: str, old_value: str, new_value: str) -> None:
        """환경변수 변경 이력 기록

        Args:
            var_name: 환경변수 이름
            old_value: 이전 값
            new_value: 새 값
        """
        change_record = {
            'timestamp': datetime.now().isoformat(),
            'variable': var_name,
            'old_value': old_value,
            'new_value': new_value
        }

        self._change_history.append(change_record)

        # 이력 크기 제한 (최대 100개)
        if len(self._change_history) > 100:
            self._change_history = self._change_history[-100:]

    def _notify_change_handlers(self, var_name: str, old_value: str, new_value: str) -> None:
        """환경변수 변경 알림

        Args:
            var_name: 환경변수 이름
            old_value: 이전 값
            new_value: 새 값
        """
        handlers_copy = self._change_handlers.copy()

        for handler in handlers_copy:
            try:
                handler(var_name, old_value, new_value)
            except Exception as e:
                print(f"⚠️ 환경변수 변경 핸들러 오류: {e}")

    def get_status_summary(self) -> Dict[str, Any]:
        """환경변수 관리 상태 요약

        Returns:
            Dict[str, Any]: 상태 요약 정보
        """
        current_vars = self.get_all_variables()
        changes_count = len(self._change_history)
        handlers_count = len(self._change_handlers)

        return {
            'total_variables': len(self.SUPPORTED_VARIABLES),
            'current_values': current_vars,
            'changes_count': changes_count,
            'handlers_count': handlers_count,
            'last_change': self._change_history[-1] if self._change_history else None
        }
