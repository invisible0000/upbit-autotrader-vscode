"""
UPBIT 자동매매 통합 로깅 시스템 v3.0
스마트 필터링 + 듀얼 파일 로깅 + 컨텍스트 인식
"""

# 핵심 로깅 시스템
try:
    from .debug_logger import debug_logger, get_logger, DebugLoggerNew
    from .smart_log_manager import (
        smart_log_manager, 
        LogContext, 
        LogScope, 
        SmartLogManager
    )
    
    LOGGING_SYSTEM_AVAILABLE = True
    print("✅ 통합 로깅 시스템 v3.0 로드 완료")
    
except ImportError as e:
    print(f"⚠️ 로깅 시스템 일부 로드 실패: {e}")
    # 기본 로거만 제공
    try:
        from .debug_logger import debug_logger, get_logger
        LOGGING_SYSTEM_AVAILABLE = False
    except ImportError:
        print("❌ 기본 로거도 로드 실패")
        debug_logger = None
        get_logger = None
        LOGGING_SYSTEM_AVAILABLE = False


# 통합 로거 팩토리
class LoggerFactory:
    """모든 로거를 관리하는 팩토리 클래스"""
    
    @staticmethod
    def get_debug_logger(component_name: str):
        """디버그 로거 (기존 방식)"""
        if get_logger:
            return get_logger(component_name)
        else:
            # 폴백: 기본 print 래퍼
            class PrintLogger:
                def __init__(self, name):
                    self.name = name
                
                def debug(self, msg): print(f"[DEBUG:{self.name}] {msg}")
                def info(self, msg): print(f"[INFO:{self.name}] {msg}")
                def warning(self, msg): print(f"[WARN:{self.name}] {msg}")
                def error(self, msg): print(f"[ERROR:{self.name}] {msg}")
                def critical(self, msg): print(f"[CRITICAL:{self.name}] {msg}")
                def success(self, msg): print(f"[SUCCESS:{self.name}] {msg}")
                def performance(self, msg): print(f"[PERF:{self.name}] {msg}")
            
            return PrintLogger(component_name)
    
    @staticmethod
    def get_smart_manager():
        """스마트 로그 매니저 반환"""
        if LOGGING_SYSTEM_AVAILABLE:
            return smart_log_manager
        else:
            print("⚠️ 스마트 로그 매니저를 사용할 수 없습니다")
            return None


# 편의 함수들
def get_integrated_logger(component_name: str):
    """통합 로거 반환 (스마트 필터링 적용)"""
    return LoggerFactory.get_debug_logger(component_name)


def get_smart_log_manager():
    """스마트 로그 매니저 반환"""
    return LoggerFactory.get_smart_manager()


# 데코레이터 함수들 (스마트 매니저가 있을 때만)
def log_scope(scope):
    """함수 실행 중 로그 스코프 변경"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_smart_log_manager()
            if manager:
                with manager.feature_development(func.__name__, scope):
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator


def debug_components(*components):
    """특정 컴포넌트만 디버깅"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_smart_log_manager()
            if manager:
                with manager.debug_session(list(components)):
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator


# 시스템 상태 확인
def get_logging_status():
    """로깅 시스템 상태 반환"""
    status = {
        "logging_system_available": LOGGING_SYSTEM_AVAILABLE,
        "debug_logger_available": debug_logger is not None,
        "smart_manager_available": False,
        "version": "3.0"
    }
    
    if LOGGING_SYSTEM_AVAILABLE:
        try:
            manager = get_smart_log_manager()
            if manager:
                status["smart_manager_available"] = True
                status["smart_manager_status"] = manager.get_status()
        except:
            pass
    
    return status


# 빠른 시작을 위한 기본 설정
def quick_setup(context: str = "development", scope: str = "normal", components: list = None):
    """빠른 로깅 설정"""
    manager = get_smart_log_manager()
    if manager and hasattr(manager, '_current_context'):
        try:
            # 환경변수 기반 설정 오버라이드
            import os
            os.environ['UPBIT_LOG_CONTEXT'] = context
            os.environ['UPBIT_LOG_SCOPE'] = scope
            
            if components:
                os.environ['UPBIT_COMPONENT_FOCUS'] = ','.join(components)
                print(f"🎯 컴포넌트 포커스 설정: {', '.join(components)}")
            
            print(f"⚙️ 로깅 설정 완료: {context}/{scope}")
            
        except Exception as e:
            print(f"⚠️ 빠른 설정 실패: {e}")
    else:
        print("⚠️ 스마트 로그 매니저가 없어 빠른 설정을 건너뜁니다")


# 하위 호환성을 위한 익스포트
__all__ = [
    # 기본 로거
    'debug_logger', 'get_logger',
    
    # 스마트 로깅
    'smart_log_manager', 'LogContext', 'LogScope',
    
    # 통합 인터페이스
    'LoggerFactory', 'get_integrated_logger', 'get_smart_log_manager',
    
    # 유틸리티
    'log_scope', 'debug_components', 'get_logging_status', 'quick_setup'
]


# 초기화 완료 메시지
if LOGGING_SYSTEM_AVAILABLE:
    print("🚀 통합 로깅 시스템 v3.0 준비 완료")
    print("   📖 사용법: from upbit_auto_trading.logging import get_integrated_logger")
    print("   🧠 스마트 필터링: from upbit_auto_trading.logging import get_smart_log_manager")
else:
    print("⚠️ 기본 로깅 시스템만 사용 가능")
