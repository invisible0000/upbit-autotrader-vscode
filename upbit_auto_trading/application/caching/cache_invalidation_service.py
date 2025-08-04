"""
캐시 무효화 서비스
도메인 이벤트에 따른 캐시 무효화 규칙을 관리하고 실행합니다.
"""

from typing import Dict, List, Optional
import asyncio
from ...logging import get_integrated_logger


class CacheKey:
    """캐시 키 관리 클래스"""

    @staticmethod
    def strategy_list() -> str:
        """전략 목록 캐시 키"""
        return "strategy:list"

    @staticmethod
    def strategy_detail(strategy_id: str) -> str:
        """전략 상세 정보 캐시 키"""
        return f"strategy:detail:{strategy_id}"

    @staticmethod
    def strategy_triggers(strategy_id: str) -> str:
        """전략의 트리거 목록 캐시 키"""
        return f"strategy:triggers:{strategy_id}"

    @staticmethod
    def strategy_backtest_results(strategy_id: str) -> str:
        """전략의 백테스팅 결과 캐시 키"""
        return f"strategy:backtest_results:{strategy_id}"

    @staticmethod
    def dashboard_summary() -> str:
        """대시보드 요약 데이터 캐시 키"""
        return "dashboard:summary"

    @staticmethod
    def dashboard_performance() -> str:
        """대시보드 성과 데이터 캐시 키"""
        return "dashboard:performance"

    @staticmethod
    def user_statistics() -> str:
        """사용자 통계 데이터 캐시 키"""
        return "user:statistics"

    @staticmethod
    def market_indicators(symbol: str) -> str:
        """시장 지표 데이터 캐시 키"""
        return f"market:indicators:{symbol}"


class CacheInvalidationService:
    """캐시 무효화 관리 서비스"""

    def __init__(self):
        """서비스 초기화"""
        self._logger = get_integrated_logger("CacheInvalidationService")
        self._invalidation_rules: Dict[str, List[str]] = {}
        self._setup_invalidation_rules()

    def _setup_invalidation_rules(self) -> None:
        """캐시 무효화 규칙 설정"""
        # 전략 생성/수정 시 무효화할 글로벌 캐시들
        self._invalidation_rules["strategy_changed"] = [
            CacheKey.strategy_list(),
            CacheKey.dashboard_summary(),
            CacheKey.dashboard_performance(),
            CacheKey.user_statistics()
        ]

        # 트리거 변경 시 무효화할 글로벌 캐시들
        self._invalidation_rules["trigger_changed"] = [
            CacheKey.strategy_list(),
            CacheKey.dashboard_summary()
        ]

        # 백테스팅 완료 시 무효화할 글로벌 캐시들
        self._invalidation_rules["backtest_completed"] = [
            CacheKey.dashboard_summary(),
            CacheKey.dashboard_performance(),
            CacheKey.user_statistics()
        ]

        self._logger.info("캐시 무효화 규칙 설정 완료")

    async def invalidate_strategy_related_cache(self, strategy_id: str) -> None:
        """
        전략 관련 캐시 무효화

        Args:
            strategy_id: 전략 ID
        """
        # 특정 전략 관련 캐시들
        strategy_specific_keys = [
            CacheKey.strategy_detail(strategy_id),
            CacheKey.strategy_triggers(strategy_id),
            CacheKey.strategy_backtest_results(strategy_id)
        ]

        # 글로벌 캐시들
        global_keys = self._invalidation_rules.get("strategy_changed", [])

        # 모든 키 무효화
        all_keys = strategy_specific_keys + global_keys
        await self._invalidate_cache_keys(all_keys)

        self._logger.info(f"전략 관련 캐시 무효화 완료: strategy_id={strategy_id}, "
                          f"키 개수={len(all_keys)}")

    async def invalidate_trigger_related_cache(self, strategy_id: str, trigger_id: Optional[str] = None) -> None:
        """
        트리거 관련 캐시 무효화

        Args:
            strategy_id: 전략 ID
            trigger_id: 트리거 ID (선택)
        """
        # 전략의 트리거 목록과 상세 정보 캐시
        strategy_specific_keys = [
            CacheKey.strategy_detail(strategy_id),
            CacheKey.strategy_triggers(strategy_id)
        ]

        # 글로벌 캐시들
        global_keys = self._invalidation_rules.get("trigger_changed", [])

        # 모든 키 무효화
        all_keys = strategy_specific_keys + global_keys
        await self._invalidate_cache_keys(all_keys)

        trigger_info = f", trigger_id={trigger_id}" if trigger_id else ""
        self._logger.info(f"트리거 관련 캐시 무효화 완료: strategy_id={strategy_id}"
                          f"{trigger_info}, 키 개수={len(all_keys)}")

    async def invalidate_backtest_related_cache(self, strategy_id: str, backtest_id: Optional[str] = None) -> None:
        """
        백테스팅 관련 캐시 무효화

        Args:
            strategy_id: 전략 ID
            backtest_id: 백테스트 ID (선택)
        """
        # 백테스팅 결과 캐시
        strategy_specific_keys = [
            CacheKey.strategy_backtest_results(strategy_id),
            CacheKey.strategy_detail(strategy_id)  # 전략 상세에 최신 백테스팅 결과 포함
        ]

        # 글로벌 캐시들
        global_keys = self._invalidation_rules.get("backtest_completed", [])

        # 모든 키 무효화
        all_keys = strategy_specific_keys + global_keys
        await self._invalidate_cache_keys(all_keys)

        backtest_info = f", backtest_id={backtest_id}" if backtest_id else ""
        self._logger.info(f"백테스팅 관련 캐시 무효화 완료: strategy_id={strategy_id}"
                          f"{backtest_info}, 키 개수={len(all_keys)}")

    async def invalidate_market_data_cache(self, symbol: str) -> None:
        """
        시장 데이터 관련 캐시 무효화

        Args:
            symbol: 심볼 (예: KRW-BTC)
        """
        # 시장 데이터 캐시
        market_keys = [
            CacheKey.market_indicators(symbol)
        ]

        await self._invalidate_cache_keys(market_keys)

        self._logger.info(f"시장 데이터 캐시 무효화 완료: symbol={symbol}, "
                          f"키 개수={len(market_keys)}")

    async def invalidate_dashboard_cache(self) -> None:
        """대시보드 관련 캐시 전체 무효화"""
        dashboard_keys = [
            CacheKey.dashboard_summary(),
            CacheKey.dashboard_performance(),
            CacheKey.user_statistics()
        ]

        await self._invalidate_cache_keys(dashboard_keys)

        self._logger.info(f"대시보드 캐시 무효화 완료: 키 개수={len(dashboard_keys)}")

    async def invalidate_cache_by_pattern(self, pattern: str) -> None:
        """
        패턴 기반 캐시 무효화

        Args:
            pattern: 캐시 키 패턴 (예: "strategy:*", "dashboard:*")
        """
        # 실제 구현에서는 Redis의 KEYS 명령이나 메모리 캐시의 패턴 매칭 사용
        # 현재는 로깅으로 대체
        self._logger.info(f"패턴 기반 캐시 무효화: pattern={pattern}")

        # 비동기 처리 시뮬레이션
        await asyncio.sleep(0.001)

    async def _invalidate_cache_keys(self, keys: List[str]) -> None:
        """
        캐시 키들 무효화 실행

        Args:
            keys: 무효화할 캐시 키 목록
        """
        if not keys:
            return

        # 실제 구현에서는 여기서 Redis나 메모리 캐시에서 키들을 삭제
        # 현재는 로깅으로 동작 확인
        for key in keys:
            self._logger.debug(f"🗑️ 캐시 무효화: {key}")

        # 병렬 무효화 시뮬레이션
        await asyncio.sleep(0.01)

        self._logger.debug(f"캐시 키 {len(keys)}개 무효화 완료")

    async def get_invalidation_rules(self) -> Dict[str, List[str]]:
        """
        현재 설정된 무효화 규칙 반환

        Returns:
            무효화 규칙 딕셔너리
        """
        return self._invalidation_rules.copy()

    async def add_custom_invalidation_rule(self, rule_name: str, cache_keys: List[str]) -> None:
        """
        커스텀 무효화 규칙 추가

        Args:
            rule_name: 규칙 이름
            cache_keys: 무효화할 캐시 키 목록
        """
        self._invalidation_rules[rule_name] = cache_keys
        self._logger.info(f"커스텀 무효화 규칙 추가: {rule_name}, 키 개수={len(cache_keys)}")

    async def remove_invalidation_rule(self, rule_name: str) -> bool:
        """
        무효화 규칙 제거

        Args:
            rule_name: 제거할 규칙 이름

        Returns:
            제거 성공 여부
        """
        if rule_name in self._invalidation_rules:
            del self._invalidation_rules[rule_name]
            self._logger.info(f"무효화 규칙 제거: {rule_name}")
            return True
        else:
            self._logger.warning(f"존재하지 않는 무효화 규칙: {rule_name}")
            return False

    def get_cache_key_count(self) -> int:
        """
        관리 중인 캐시 키 총 개수 반환

        Returns:
            캐시 키 총 개수
        """
        total_keys = set()
        for keys in self._invalidation_rules.values():
            total_keys.update(keys)
        return len(total_keys)

    def get_rule_count(self) -> int:
        """
        무효화 규칙 개수 반환

        Returns:
            무효화 규칙 개수
        """
        return len(self._invalidation_rules)

    # 테스트 호환성을 위한 별칭 메서드들
    async def invalidate_for_strategy_change(self, strategy_id: str) -> None:
        """전략 변경을 위한 캐시 무효화 (별칭)"""
        await self.invalidate_strategy_related_cache(strategy_id)

    async def invalidate_for_backtest_completion(self, strategy_id: str, symbol: str) -> None:
        """백테스트 완료를 위한 캐시 무효화 (별칭)"""
        await self.invalidate_backtest_related_cache(strategy_id)
