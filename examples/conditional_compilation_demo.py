"""
컴파일 타임 조건부 컴파일 구현 및 IDE 지원 데모
Python에서 타입 체킹 기반 조건부 컴파일 구현
"""
from typing import TYPE_CHECKING
import os

# 빌드 타입 설정
DEBUG_BUILD = os.getenv('UPBIT_BUILD_TYPE', 'debug') == 'debug'
PRODUCTION_BUILD = not DEBUG_BUILD

# mypy나 IDE의 타입 체킹 시에만 실행되는 코드
if TYPE_CHECKING:
    from typing import Optional, Protocol
    
    # 개발 시에만 보이는 타입 정의
    class DebugProtocol(Protocol):
        def debug_info(self) -> str: ...

print(f"🔧 현재 빌드 모드: {'DEBUG' if DEBUG_BUILD else 'PRODUCTION'}")

class TradingStrategy:
    def __init__(self):
        self.name = "전략"
        
        # 컴파일 타임 조건부 - 빌드 시점에 결정됨
        if DEBUG_BUILD:
            # 개발 빌드에서만 포함되는 코드
            self._debug_enabled = True
            self._debug_info = f"Debug: {self.name} at {id(self)}"
            print(f"🔍 디버그 빌드: {self._debug_info}")
        else:
            # 프로덕션 빌드에서는 이 코드가 완전히 제거됨
            self._debug_enabled = False
    
    def execute_trade(self, symbol: str, amount: float):
        """거래 실행"""
        result = amount * 0.999
        
        # 조건부 컴파일: DEBUG_BUILD가 False면 이 블록 자체가 제거됨
        if DEBUG_BUILD:
            print(f"🚀 디버그 정보: {symbol} 거래 실행")
            print(f"  입력 금액: {amount:,}")
            print(f"  처리 결과: {result:,}")
            
            # 개발 시에만 사용하는 상세 검증
            assert amount > 0, "거래 금액은 양수여야 합니다"
            assert isinstance(symbol, str), "심볼은 문자열이어야 합니다"
        
        return result
    
    # 조건부 메서드 정의
    if DEBUG_BUILD:
        def get_debug_info(self) -> str:
            """디버그 정보 반환 (개발 빌드에서만 존재)"""
            return getattr(self, '_debug_info', 'No debug info')
        
        def validate_state(self) -> bool:
            """상태 검증 (개발 빌드에서만 존재)"""
            print(f"🔍 상태 검증: {self.name}")
            return hasattr(self, '_debug_enabled')
    else:
        # 프로덕션에서는 더미 메서드나 아예 없음
        pass

# 조건부 헬퍼 함수들
if DEBUG_BUILD:
    def debug_print(message: str) -> None:
        """디버그 출력 함수 (개발 빌드에서만 존재)"""
        print(f"🔍 DEBUG: {message}")
    
    def performance_monitor(func):
        """성능 모니터링 데코레이터 (개발 빌드에서만)"""
        import time
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            print(f"⏱️ {func.__name__} 실행시간: {end-start:.4f}초")
            return result
        return wrapper
else:
    # 프로덕션에서는 no-op 함수들
    def debug_print(message: str) -> None:
        """프로덕션에서는 아무것도 하지 않음"""
        pass
    
    def performance_monitor(func):
        """프로덕션에서는 원본 함수 그대로 반환"""
        return func

# 사용 예시
@performance_monitor
def complex_calculation(data: list) -> float:
    """복잡한 계산 함수"""
    debug_print(f"계산 시작: {len(data)} 개 데이터")
    result = sum(x * 2 for x in data)
    debug_print(f"계산 완료: {result}")
    return result

# 조건부 테스트 코드
if DEBUG_BUILD:
    def run_debug_tests():
        """디버그 테스트 (개발 빌드에서만 실행)"""
        print("\n🧪 디버그 테스트 시작...")
        
        strategy = TradingStrategy()
        
        # 디버그 메서드 호출 (타입 체커가 존재 여부 확인)
        if hasattr(strategy, 'get_debug_info'):
            debug_info = strategy.get_debug_info()
            print(f"📊 디버그 정보: {debug_info}")
        
        if hasattr(strategy, 'validate_state'):
            is_valid = strategy.validate_state()
            print(f"✅ 상태 검증: {is_valid}")
        
        # 성능 모니터링 테스트
        test_data = [1, 2, 3, 4, 5]
        result = complex_calculation(test_data)
        print(f"📈 계산 결과: {result}")
        
        print("🎉 디버그 테스트 완료!")

def main():
    """메인 함수"""
    print(f"🚀 애플리케이션 시작 (빌드: {'DEBUG' if DEBUG_BUILD else 'PRODUCTION'})")
    
    strategy = TradingStrategy()
    result = strategy.execute_trade("BTC-KRW", 1000000)
    print(f"💰 거래 결과: {result:,}")
    
    # 조건부 실행
    if DEBUG_BUILD:
        run_debug_tests()

if __name__ == "__main__":
    main()
