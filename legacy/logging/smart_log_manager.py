"""
스마트 로그 관리 시스템 v3.0
로그 범람 방지 + 개발 상황에 맞는 스마트 필터링
"""
import os
import threading
from enum import Enum
from typing import Set, Dict, Optional
from contextlib import contextmanager


class LogContext(Enum):
    """로그 컨텍스트 (상황별 분류)"""
    DEVELOPMENT = "development"      # 개발 중
    TESTING = "testing"             # 테스트 중
    DEBUGGING = "debugging"         # 디버깅 중
    PRODUCTION = "production"       # 프로덕션
    EMERGENCY = "emergency"         # 긴급 상황
    PERFORMANCE = "performance"     # 성능 측정


class LogScope(Enum):
    """로그 스코프 (출력 범위)"""
    SILENT = "silent"               # 최소한의 로그만
    MINIMAL = "minimal"             # 핵심 로그만
    NORMAL = "normal"               # 일반적인 로그
    VERBOSE = "verbose"             # 상세한 로그
    DEBUG_ALL = "debug_all"         # 모든 디버그 로그


class SmartLogManager:
    """스마트 로그 관리자 - 상황별 로그 제어"""
    
    def __init__(self):
        self._current_context = self._get_env_context()
        self._current_scope = self._get_env_scope()
        self._component_filters: Set[str] = self._get_env_component_filters()
        self._feature_mode: Optional[str] = os.getenv('UPBIT_FEATURE_FOCUS')
        self._thread_local = threading.local()
        
        # 성능 최적화를 위한 캐시
        self._filter_cache: Dict[str, bool] = {}
        
        # 초기화 로그
        self._log_initialization()
    
    def _get_env_context(self) -> LogContext:
        """환경변수에서 로그 컨텍스트 읽기"""
        context_str = os.getenv('UPBIT_LOG_CONTEXT', 'development').lower()
        try:
            return LogContext(context_str)
        except ValueError:
            return LogContext.DEVELOPMENT
    
    def _get_env_scope(self) -> LogScope:
        """환경변수에서 로그 스코프 읽기"""
        scope_str = os.getenv('UPBIT_LOG_SCOPE', 'normal').lower()
        try:
            return LogScope(scope_str)
        except ValueError:
            return LogScope.NORMAL
    
    def _get_env_component_filters(self) -> Set[str]:
        """환경변수에서 컴포넌트 필터 읽기"""
        filters_str = os.getenv('UPBIT_COMPONENT_FOCUS', '')
        if filters_str:
            return set(component.strip() for component in filters_str.split(',') if component.strip())
        return set()
    
    def _log_initialization(self):
        """초기화 상태 로그"""
        print(f"🔧 스마트 로그 관리자 v3.0 초기화")
        print(f"   📊 컨텍스트: {self._current_context.value}")
        print(f"   🎯 스코프: {self._current_scope.value}")
        if self._component_filters:
            print(f"   🔍 컴포넌트 필터: {', '.join(self._component_filters)}")
        if self._feature_mode:
            print(f"   🚀 기능 포커스: {self._feature_mode}")
    
    @contextmanager
    def feature_development(self, feature_name: str, scope: LogScope = LogScope.VERBOSE):
        """특정 기능 개발 중 로그 제어"""
        old_context = self._current_context
        old_scope = self._current_scope
        old_feature = self._feature_mode
        old_filters = self._component_filters.copy()
        
        try:
            self._current_context = LogContext.DEVELOPMENT
            self._current_scope = scope
            self._feature_mode = feature_name
            # 기능명 기반 컴포넌트 자동 추가
            self._component_filters.add(feature_name)
            self._clear_cache()
            
            print(f"🚀 기능 개발 모드 시작: {feature_name} (스코프: {scope.value})")
            yield
            
        finally:
            self._current_context = old_context
            self._current_scope = old_scope
            self._feature_mode = old_feature
            self._component_filters = old_filters
            self._clear_cache()
            print(f"✅ 기능 개발 모드 종료: {feature_name}")
    
    @contextmanager
    def testing_mode(self, test_name: str):
        """테스트 실행 중 로그 제어"""
        old_context = self._current_context
        old_scope = self._current_scope
        
        try:
            self._current_context = LogContext.TESTING
            self._current_scope = LogScope.MINIMAL
            self._clear_cache()
            
            print(f"🧪 테스트 모드 시작: {test_name}")
            yield
            
        finally:
            self._current_context = old_context
            self._current_scope = old_scope
            self._clear_cache()
            print(f"✅ 테스트 모드 종료: {test_name}")
    
    @contextmanager
    def debug_session(self, components: list):
        """특정 컴포넌트만 디버깅"""
        old_filters = self._component_filters.copy()
        old_context = self._current_context
        old_scope = self._current_scope
        
        try:
            self._current_context = LogContext.DEBUGGING
            self._current_scope = LogScope.DEBUG_ALL
            self._component_filters = set(components)
            self._clear_cache()
            
            print(f"🔍 디버그 세션 시작: {', '.join(components)}")
            yield
            
        finally:
            self._component_filters = old_filters
            self._current_context = old_context
            self._current_scope = old_scope
            self._clear_cache()
            print(f"✅ 디버그 세션 종료")
    
    @contextmanager
    def performance_mode(self):
        """성능 측정 모드 (로그 최소화)"""
        old_context = self._current_context
        old_scope = self._current_scope
        
        try:
            self._current_context = LogContext.PERFORMANCE
            self._current_scope = LogScope.SILENT
            self._clear_cache()
            
            print("⚡ 성능 측정 모드 시작 (로그 최소화)")
            yield
            
        finally:
            self._current_context = old_context
            self._current_scope = old_scope
            self._clear_cache()
            print("✅ 성능 측정 모드 종료")
    
    @contextmanager
    def emergency_mode(self):
        """긴급 상황 모드 (모든 로그 활성화)"""
        old_context = self._current_context
        old_scope = self._current_scope
        old_filters = self._component_filters.copy()
        
        try:
            self._current_context = LogContext.EMERGENCY
            self._current_scope = LogScope.DEBUG_ALL
            self._component_filters.clear()  # 모든 컴포넌트 허용
            self._clear_cache()
            
            print("🚨 긴급 모드 시작 (모든 로그 활성화)")
            yield
            
        finally:
            self._current_context = old_context
            self._current_scope = old_scope
            self._component_filters = old_filters
            self._clear_cache()
            print("✅ 긴급 모드 종료")
    
    def should_log(self, component: str, level: str, message: str) -> bool:
        """로그 출력 여부 결정 (캐시 적용)"""
        cache_key = f"{component}:{level}:{self._current_context.value}:{self._current_scope.value}"
        
        if cache_key in self._filter_cache:
            return self._filter_cache[cache_key]
        
        result = self._evaluate_should_log(component, level, message)
        self._filter_cache[cache_key] = result
        return result
    
    def _evaluate_should_log(self, component: str, level: str, message: str) -> bool:
        """실제 로그 출력 여부 평가"""
        # 긴급 상황에서는 모든 로그 출력
        if self._current_context == LogContext.EMERGENCY:
            return True
        
        # 컴포넌트 필터링 (설정된 경우)
        if self._component_filters:
            # 정확한 매치 또는 부분 매치 허용
            component_match = any(
                component == filter_comp or filter_comp in component or component in filter_comp
                for filter_comp in self._component_filters
            )
            if not component_match:
                return False
        
        # 기능 포커스 모드 (환경변수로 설정된 경우)
        if self._feature_mode and self._feature_mode not in component:
            return False
        
        # 스코프별 필터링
        return self._check_scope_filter(level, message)
    
    def _check_scope_filter(self, level: str, message: str) -> bool:
        """스코프에 따른 필터링"""
        if self._current_scope == LogScope.SILENT:
            return level in ["ERROR", "CRITICAL"]
        
        elif self._current_scope == LogScope.MINIMAL:
            # 핵심 키워드가 포함된 로그만 허용
            important_keywords = [
                "SUCCESS", "FAIL", "ERROR", "시작", "완료", "연결", "끊김", 
                "생성", "삭제", "초기화", "종료", "로딩", "저장"
            ]
            
            has_important_keyword = any(keyword in message for keyword in important_keywords)
            return level in ["INFO", "WARNING", "ERROR", "CRITICAL"] and has_important_keyword
        
        elif self._current_scope == LogScope.NORMAL:
            return level in ["INFO", "WARNING", "ERROR", "CRITICAL"]
        
        elif self._current_scope == LogScope.VERBOSE:
            return level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        elif self._current_scope == LogScope.DEBUG_ALL:
            return True
        
        return True
    
    def _clear_cache(self):
        """필터 캐시 초기화"""
        self._filter_cache.clear()
    
    def set_component_focus(self, components: list):
        """컴포넌트 포커스 설정"""
        self._component_filters = set(components)
        self._clear_cache()
        print(f"🎯 컴포넌트 포커스 설정: {', '.join(components)}")
    
    def clear_component_focus(self):
        """컴포넌트 포커스 해제"""
        self._component_filters.clear()
        self._clear_cache()
        print("🔄 컴포넌트 포커스 해제")
    
    def get_status(self) -> dict:
        """현재 로그 관리자 상태 반환"""
        return {
            "context": self._current_context.value,
            "scope": self._current_scope.value,
            "component_filters": list(self._component_filters),
            "feature_mode": self._feature_mode,
            "cache_size": len(self._filter_cache)
        }


# 전역 스마트 로그 매니저 인스턴스
smart_log_manager = SmartLogManager()
