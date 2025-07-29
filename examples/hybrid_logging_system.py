"""
듀얼 로깅 시스템 v2.2 + 조건부 컴파일 통합 버전
최강의 디버깅 시스템 구현
"""
import os
import sys
from typing import TYPE_CHECKING

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from upbit_auto_trading.utils.debug_logger import get_logger
except ImportError:
    # 폴백: 간단한 로거
    class FallbackLogger:
        def __init__(self, name):
            self.name = name
        def info(self, msg): print(f"ℹ️ [{self.name}] {msg}")
        def debug(self, msg): print(f"🔍 [{self.name}] {msg}")
        def success(self, msg): print(f"✅ [{self.name}] {msg}")
        def error(self, msg): print(f"❌ [{self.name}] {msg}")
        def warning(self, msg): print(f"⚠️ [{self.name}] {msg}")
        def performance(self, msg): print(f"⏱️ [{self.name}] {msg}")
    
    def get_logger(name):
        return FallbackLogger(name)

# 🔧 빌드 타입 설정
DEBUG_BUILD = os.getenv('UPBIT_BUILD_TYPE', 'debug') == 'debug'
PRODUCTION_BUILD = not DEBUG_BUILD

if TYPE_CHECKING:
    from typing import Any, Dict, Optional

# 🎯 조건부 로거 설정
if DEBUG_BUILD:
    # 개발 모드: 풀 기능 듀얼 로깅 시스템
    logger = get_logger("TradingEngine")
else:
    # 프로덕션 모드: 최소한의 로깅만
    class ProductionLogger:
        """프로덕션용 최소 로거"""
        def info(self, msg): pass
        def error(self, msg): print(f"ERROR: {msg}")  # 에러만 출력
        def warning(self, msg): pass
        def debug(self, msg): pass  # 완전히 무시
        def success(self, msg): pass
        def performance(self, msg): pass
    
    logger = ProductionLogger()

print(f"🔧 로깅 시스템: {'FULL DEBUG' if DEBUG_BUILD else 'PRODUCTION MINIMAL'}")

class SmartTradingEngine:
    """조건부 컴파일 + 듀얼 로깅이 통합된 트레이딩 엔진"""
    
    def __init__(self):
        self.name = "스마트 트레이딩 엔진"
        
        # 조건부 컴파일: 디버그 빌드에서만 상세 초기화
        if DEBUG_BUILD:
            logger.success(f"🚀 {self.name} 초기화 시작")
            logger.debug(f"🔍 메모리 주소: {hex(id(self))}")
            logger.debug(f"🎯 빌드 모드: DEBUG")
            
            # 개발 모드에서만 존재하는 속성들
            self._debug_stats = {
                'initialized_at': os.times(),
                'memory_address': hex(id(self)),
                'debug_features_enabled': True
            }
            
            logger.performance(f"초기화 성능 추적 활성화됨")
        else:
            # 프로덕션: 최소한의 로깅
            logger.info("트레이딩 엔진 시작")
    
    def execute_order(self, symbol: str, amount: float, order_type: str):
        """주문 실행 - 조건부 로깅 적용"""
        
        # 핵심 로직 (항상 실행)
        result = self._process_order(symbol, amount, order_type)
        
        # 조건부 상세 로깅
        if DEBUG_BUILD:
            logger.info(f"📊 주문 실행 시작")
            logger.debug(f"  🎯 심볼: {symbol}")
            logger.debug(f"  💰 금액: {amount:,}")
            logger.debug(f"  📈 타입: {order_type}")
            
            # 개발 모드에서만 상세 검증
            self._validate_order_debug(symbol, amount, order_type)
            
            logger.success(f"✅ 주문 처리 완료: {result['order_id']}")
        else:
            # 프로덕션: 핵심 정보만
            logger.info(f"주문 완료: {symbol}")
        
        return result
    
    def _process_order(self, symbol: str, amount: float, order_type: str):
        """실제 주문 처리 로직"""
        # 실제 처리 로직 (시뮬레이션)
        order_id = f"ORD_{hash(f'{symbol}{amount}{order_type}') % 100000:05d}"
        
        if DEBUG_BUILD:
            logger.performance(f"주문 처리 시간 추적: {order_id}")
        
        return {
            'order_id': order_id,
            'symbol': symbol,
            'amount': amount,
            'type': order_type,
            'status': 'completed'
        }
    
    # 조건부 메서드 정의: 디버그 빌드에서만 존재
    if DEBUG_BUILD:
        def _validate_order_debug(self, symbol: str, amount: float, order_type: str):
            """디버그용 주문 검증 (개발 빌드에서만 존재)"""
            logger.debug("🔍 상세 주문 검증 시작")
            
            assert isinstance(symbol, str), "심볼은 문자열이어야 함"
            assert amount > 0, "주문 금액은 양수여야 함"
            assert order_type in ['buy', 'sell'], "주문 타입이 유효하지 않음"
            
            logger.debug("✅ 주문 검증 통과")
        
        def get_debug_stats(self):
            """디버그 통계 반환 (개발 빌드에서만 존재)"""
            logger.debug("📊 디버그 통계 조회")
            return getattr(self, '_debug_stats', {})
        
        def run_diagnostic(self):
            """시스템 진단 (개발 빌드에서만 존재)"""
            logger.info("🔍 시스템 진단 시작")
            
            stats = self.get_debug_stats()
            logger.debug(f"📈 초기화 시간: {stats.get('initialized_at')}")
            logger.debug(f"💾 메모리 주소: {stats.get('memory_address')}")
            
            logger.success("✅ 시스템 진단 완료")
            return True
    else:
        # 프로덕션에서는 더미 메서드나 아예 제거
        pass

# 조건부 헬퍼 함수들
if DEBUG_BUILD:
    def debug_log_with_context(component: str, action: str, data: dict = None):
        """컨텍스트가 포함된 디버그 로깅"""
        context_logger = get_logger(component)
        context_logger.debug(f"🎯 {action}")
        
        if data:
            for key, value in data.items():
                context_logger.debug(f"  📋 {key}: {value}")
    
    def performance_benchmark(func):
        """성능 벤치마크 데코레이터 (개발 빌드에서만)"""
        import time
        
        def wrapper(*args, **kwargs):
            perf_logger = get_logger("Performance")
            
            start_time = time.perf_counter()
            perf_logger.performance(f"⏱️ {func.__name__} 시작")
            
            try:
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                duration = end_time - start_time
                
                perf_logger.performance(f"✅ {func.__name__} 완료 - {duration:.4f}초")
                
                # 느린 함수 경고
                if duration > 1.0:
                    perf_logger.warning(f"⚠️ {func.__name__}이 느림: {duration:.4f}초")
                
                return result
                
            except Exception as e:
                end_time = time.perf_counter()
                duration = end_time - start_time
                
                perf_logger.error(f"❌ {func.__name__} 실패 - {duration:.4f}초 후 에러: {e}")
                raise
        
        return wrapper
else:
    # 프로덕션에서는 no-op 함수들
    def debug_log_with_context(component: str, action: str, data: dict = None):
        pass
    
    def performance_benchmark(func):
        return func  # 원본 함수 그대로 반환

# 사용 예시
@performance_benchmark
def complex_market_analysis(market_data: list):
    """복잡한 시장 분석 함수"""
    debug_log_with_context("MarketAnalysis", "분석 시작", {
        "데이터 크기": len(market_data),
        "분석 타입": "실시간"
    })
    
    # 실제 분석 로직 시뮬레이션
    result = sum(x * 1.1 for x in market_data)
    
    debug_log_with_context("MarketAnalysis", "분석 완료", {
        "결과": result,
        "처리된 데이터": len(market_data)
    })
    
    return result

def main():
    """메인 실행 함수"""
    print(f"\n🚀 통합 시스템 시작")
    print(f"📊 빌드 모드: {'DEBUG' if DEBUG_BUILD else 'PRODUCTION'}")
    print(f"🔧 로깅 레벨: {'FULL' if DEBUG_BUILD else 'MINIMAL'}\n")
    
    # 트레이딩 엔진 생성
    engine = SmartTradingEngine()
    
    # 주문 실행 테스트
    order_result = engine.execute_order("BTC-KRW", 1000000, "buy")
    print(f"💰 주문 결과: {order_result['order_id']}")
    
    # 시장 분석 테스트
    market_data = [100, 200, 300, 400, 500]
    analysis_result = complex_market_analysis(market_data)
    print(f"📈 분석 결과: {analysis_result}")
    
    # 조건부 진단 실행
    if DEBUG_BUILD:
        if hasattr(engine, 'run_diagnostic'):
            engine.run_diagnostic()
            
        if hasattr(engine, 'get_debug_stats'):
            stats = engine.get_debug_stats()
            print(f"📊 디버그 통계: {len(stats)} 항목")

if __name__ == "__main__":
    main()
