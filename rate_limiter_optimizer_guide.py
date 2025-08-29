#!/usr/bin/env python3
"""
Rate Limiter 파라미터 최적화 가이드

테스트 결과를 기반으로 각 전략의 파라미터 조정 가이드 제공
"""

import sys
from dataclasses import dataclass
from typing import Dict
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import RateLimitStrategy  # noqa: E402


@dataclass
class ParameterGuide:
    """파라미터 조정 가이드"""
    strategy: RateLimitStrategy
    current_issue: str
    recommended_changes: Dict[str, str]
    expected_improvement: str
    risk_level: str


class RateLimiterOptimizer:
    """Rate Limiter 파라미터 최적화 가이드"""

    def __init__(self):
        self.optimization_guides = {
            RateLimitStrategy.HYBRID_FAST: {
                "current_issue": "시작 시 간헐적 429 오류 발생",
                "recommended_changes": {
                    "SAFETY_BUFFER": "1 → 2 (안전 버퍼 증가)",
                    "LIGHT_WAIT_MULTIPLIER": "0.04 → 0.06 (대기시간 소폭 증가)",
                    "MAX_LIGHT_WAIT_MS": "60 → 80 (최대 대기시간 증가)"
                },
                "expected_improvement": "RPS 6.8-7.0 유지하면서 429 오류 완전 제거",
                "risk_level": "🟢 낮음 (안전한 조정)"
            },

            RateLimitStrategy.CLOUDFLARE_SLIDING_WINDOW: {
                "current_issue": "매우 안전하지만 50% 대역폭만 사용 (RPS 4.7)",
                "recommended_changes": {
                    "SAFETY_BUFFER": "1 → 0 (안전 버퍼 제거)",
                    "EXCESS_MULTIPLIER": "0.1 → 0.08 (대기시간 계수 감소)",
                    "MAX_WAIT_TIME_MS": "120 → 100 (최대 대기시간 감소)",
                    "CLEANUP_WINDOW_SECONDS": "2.0 → 1.5 (정리 주기 단축)"
                },
                "expected_improvement": "RPS 4.7 → 6.0-6.5 (30% 성능 향상)",
                "risk_level": "🟡 보통 (신중한 모니터링 필요)"
            },

            RateLimitStrategy.AIOLIMITER_OPTIMIZED: {
                "current_issue": "즉시 429 오류 폭탄 - 완전히 잘못된 제한 로직",
                "recommended_changes": {
                    "FAST_CHECK_THRESHOLD": "8 → 5 (임계값 대폭 감소)",
                    "MAX_WAIT_TIME_MS": "80 → 150 (대기시간 대폭 증가)",
                    "EXCESS_MULTIPLIER": "0.05 → 0.15 (대기시간 계수 3배 증가)",
                    "PRECISION_MODE": "True 유지 (정밀 모드 필수)"
                },
                "expected_improvement": "429 오류 방지 우선, 성능은 RPS 5-6 수준으로 제한",
                "risk_level": "🔴 높음 (여전히 위험, 사용 비권장)"
            }
        }

    def print_optimization_guide(self):
        """최적화 가이드 출력"""
        print("🎯" + "=" * 70 + "🎯")
        print("🔧 Rate Limiter 파라미터 최적화 가이드")
        print("🎯" + "=" * 70 + "🎯")

        print("\n📊 현재 테스트 결과 분석:")
        print("1. hybrid_fast: 전체적으로 안정 (RPS 7.0), 시작 시 가끔 429")
        print("2. cloudflare_sliding_window: 매우 안전 (RPS 4.7), 대역폭 50%만 사용")
        print("3. aiolimiter_optimized: 즉시 429 폭탄, 제한 로직 완전 실패")

        for strategy, guide in self.optimization_guides.items():
            self._print_strategy_guide(strategy, guide)

        self._print_implementation_guide()
        self._print_testing_guide()

    def _print_strategy_guide(self, strategy: RateLimitStrategy, guide: Dict):
        """개별 전략 가이드 출력"""
        print(f"\n🔧 {strategy.value} 최적화 가이드")
        print("-" * 60)
        print(f"📋 현재 문제: {guide['current_issue']}")
        print(f"🎯 기대 효과: {guide['expected_improvement']}")
        print(f"⚠️  위험도: {guide['risk_level']}")

        print("\n🛠️  권장 파라미터 변경:")
        for param, change in guide['recommended_changes'].items():
            print(f"   • {param}: {change}")

    def _print_implementation_guide(self):
        """구현 가이드 출력"""
        print("\n🛠️ " + "=" * 50 + "🛠️")
        print("📝 파라미터 변경 구현 방법")
        print("🛠️ " + "=" * 50 + "🛠️")

        print("\n1️⃣ 파일 위치:")
        print("   📁 upbit_auto_trading/infrastructure/external_apis/upbit/upbit_rate_limiter.py")

        print("\n2️⃣ 변경 방법:")
        print("   🔍 각 전략 함수 상단의 '조정 가능한 파라미터' 섹션 찾기")
        print("   ✏️  해당 상수값을 권장값으로 변경")
        print("   💾 저장 후 벤치마크 재실행")

        print("\n3️⃣ 예시 (hybrid_fast 전략):")
        print("```python")
        print("async def _enforce_global_limit_hybrid(self) -> None:")
        print("    # ==========================================")
        print("    # 🔧 HYBRID 전략 조정 가능한 파라미터들")
        print("    # ==========================================")
        print("    SAFETY_BUFFER = 2                    # 변경: 1 → 2")
        print("    LIGHT_WAIT_MULTIPLIER = 0.06         # 변경: 0.04 → 0.06")
        print("    MAX_LIGHT_WAIT_MS = 80               # 변경: 60 → 80")
        print("```")

    def _print_testing_guide(self):
        """테스트 가이드 출력"""
        print("\n🧪 " + "=" * 50 + "🧪")
        print("📋 파라미터 변경 후 테스트 방법")
        print("🧪 " + "=" * 50 + "🧪")

        print("\n1️⃣ 개별 전략 테스트:")
        print("   python rate_limiter_benchmark.py")
        print("   🔍 변경한 전략의 429 오류 발생 여부 확인")

        print("\n2️⃣ 성능 모니터링:")
        print("   📊 RPS (초당 요청 수)")
        print("   ⏱️  평균 Rate Limiter 시간")
        print("   🚨 429 오류 카운트 (0이어야 함)")

        print("\n3️⃣ 단계별 조정:")
        print("   🟢 1단계: 안전성 확보 (429 오류 완전 제거)")
        print("   🟡 2단계: 성능 최적화 (RPS 점진적 증가)")
        print("   🔴 3단계: 장기 안정성 테스트 (10분 이상)")

        print("\n4️⃣ 권장 순서:")
        print("   1. hybrid_fast 먼저 최적화 (가장 안전)")
        print("   2. cloudflare_sliding_window 성능 향상")
        print("   3. aiolimiter_optimized는 마지막 (또는 제외)")

    def print_current_parameters(self):
        """현재 파라미터 출력"""
        print("\n📊 " + "=" * 50 + "📊")
        print("🔍 현재 파라미터 값 확인")
        print("📊 " + "=" * 50 + "📊")

        print("\n각 전략별 현재 파라미터를 확인하려면:")
        print("📁 upbit_rate_limiter.py 파일에서 다음 함수들을 확인하세요:")
        print("   • _enforce_global_limit_hybrid() - HYBRID_FAST 전략")
        print("   • _enforce_global_limit_cloudflare() - CLOUDFLARE_SLIDING_WINDOW 전략")
        print("   • _enforce_global_limit_aiolimiter() - AIOLIMITER_OPTIMIZED 전략")

        print("\n🔧 각 함수 상단의 '조정 가능한 파라미터' 섹션에서 현재값을 확인할 수 있습니다.")

    def print_quick_429_fix(self):
        """429 오류 즉시 해결 가이드"""
        print("\n🚨 " + "=" * 50 + "🚨")
        print("🚑 429 오류 긴급 해결 가이드")
        print("🚨 " + "=" * 50 + "🚨")

        print("\n⚡ 즉시 적용할 안전한 설정:")

        print("\n🔧 hybrid_fast 전략 (즉시 수정):")
        print("   SAFETY_BUFFER = 2")
        print("   LIGHT_WAIT_MULTIPLIER = 0.06")
        print("   MAX_LIGHT_WAIT_MS = 80")

        print("\n🔧 cloudflare_sliding_window 전략 (현재 안전):")
        print("   - 현재 설정 유지 (429 오류 없음)")
        print("   - 필요시 성능 향상만 적용")

        print("\n🔧 aiolimiter_optimized 전략 (위험 - 사용 금지):")
        print("   ❌ 현재 사용 중단 권장")
        print("   ❌ 수정해도 안정성 보장 어려움")

        print("\n🎯 권장 프로덕션 설정:")
        print("   ✅ 1순위: hybrid_fast (수정 후)")
        print("   ✅ 2순위: cloudflare_sliding_window")
        print("   ❌ 사용금지: aiolimiter_optimized")


def main():
    """메인 실행 함수"""
    optimizer = RateLimiterOptimizer()

    print("🚀 Rate Limiter 파라미터 최적화 가이드")
    print("\n옵션을 선택하세요:")
    print("1. 📋 전체 최적화 가이드 보기")
    print("2. 🔍 현재 파라미터 확인 방법")
    print("3. 🚑 429 오류 긴급 해결")
    print("4. ❌ 종료")

    try:
        choice = input("\n선택 (1-4): ").strip()

        if choice == "1":
            optimizer.print_optimization_guide()
        elif choice == "2":
            optimizer.print_current_parameters()
        elif choice == "3":
            optimizer.print_quick_429_fix()
        elif choice == "4":
            print("👋 최적화 가이드를 종료합니다.")
        else:
            print("❌ 잘못된 선택입니다.")

    except KeyboardInterrupt:
        print("\n👋 사용자가 가이드를 종료했습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")


if __name__ == "__main__":
    main()
