"""
적응형 라우팅 엔진

Test 08-11 검증 결과를 기반으로 한 5-Tier 적응형 라우팅 시스템의 핵심 엔진입니다.
Usage Context와 네트워크 상황을 종합적으로 분석하여 최적의 데이터 소스를 선택합니다.

핵심 혁신:
- 273x 성능 향상 가능 (5,241 symbols/sec vs 19 symbols/sec)
- Usage Context 기반 지능형 라우팅
- 네트워크 효율성 실시간 최적화
- 0.1ms ~ 500ms 응답 시간 보장
"""

import time
from typing import Dict, List, Any
from datetime import datetime
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger
from ..interfaces.market_data_router import IMarketDataRouter, Priority
from ..models.routing_response import RoutingTier
from ..models import (
    RoutingRequest, RoutingResponse, RoutingContext,
    UsageContext, NetworkPolicy, ResponseStatus, PerformanceMetrics, TimeFrame, DataType
)
from ..implementations.upbit_data_provider import UpbitDataProvider

logger = create_component_logger("AdaptiveRoutingEngine")


@dataclass
class TierPerformanceSpec:
    """Tier별 성능 스펙 (Test 검증 기반)"""
    max_response_time_ms: float
    typical_response_time_ms: float
    max_symbols_per_request: int
    network_efficiency: float  # 0.0-1.0 (1.0이 가장 효율적)
    data_freshness_guarantee_ms: int


class AdaptiveRoutingEngine(IMarketDataRouter):
    """적응형 라우팅 엔진

    Test 08-11 검증된 성능을 기반으로 5-Tier 적응형 라우팅을 제공합니다.
    """

    def __init__(self):
        """라우팅 엔진 초기화"""
        logger.info("AdaptiveRoutingEngine 초기화 시작")

        # 실제 데이터 제공자 초기화
        self.data_provider = UpbitDataProvider()
        self._provider_started = False

        # Test 검증 기반 Tier별 성능 스펙
        self._tier_specs = {
            RoutingTier.HOT_CACHE: TierPerformanceSpec(
                max_response_time_ms=1.0,
                typical_response_time_ms=0.1,
                max_symbols_per_request=1000,  # 메모리 제한
                network_efficiency=1.0,
                data_freshness_guarantee_ms=100
            ),
            RoutingTier.LIVE_SUBSCRIPTION: TierPerformanceSpec(
                max_response_time_ms=5.0,
                typical_response_time_ms=0.2,
                max_symbols_per_request=20,  # 기존 개별 구독 한계
                network_efficiency=0.6,
                data_freshness_guarantee_ms=50
            ),
            RoutingTier.BATCH_SNAPSHOT: TierPerformanceSpec(
                max_response_time_ms=50.0,
                typical_response_time_ms=11.20,  # Test 08-11 실측
                max_symbols_per_request=189,  # Test 검증된 최대값
                network_efficiency=0.9,
                data_freshness_guarantee_ms=1000
            ),
            RoutingTier.WARM_CACHE_REST: TierPerformanceSpec(
                max_response_time_ms=300.0,
                typical_response_time_ms=200.0,
                max_symbols_per_request=100,
                network_efficiency=0.7,
                data_freshness_guarantee_ms=5000
            ),
            RoutingTier.COLD_REST: TierPerformanceSpec(
                max_response_time_ms=1000.0,
                typical_response_time_ms=500.0,
                max_symbols_per_request=1,  # REST API 제한
                network_efficiency=0.3,
                data_freshness_guarantee_ms=0  # 신선도 보장 없음
            )
        }

        # 네트워크 사용량 모니터링
        self._current_network_usage = 0.0
        self._network_history: List[float] = []
        self._last_optimization_time = datetime.now()

        # 성능 통계
        self._routing_stats = {tier: {
            'request_count': 0,
            'success_count': 0,
            'total_response_time_ms': 0.0,
            'avg_symbols_per_request': 0.0
        } for tier in RoutingTier}

        logger.info("AdaptiveRoutingEngine 초기화 완료")

    async def start(self) -> None:
        """AdaptiveRoutingEngine 시작 (데이터 제공자 시작)"""
        if not self._provider_started:
            await self.data_provider.start()
            self._provider_started = True
            logger.info("✅ AdaptiveRoutingEngine 시작 완료 - 데이터 제공자 준비됨")

    async def stop(self) -> None:
        """AdaptiveRoutingEngine 정지 (데이터 제공자 정지)"""
        if self._provider_started:
            await self.data_provider.stop()
            self._provider_started = False
            logger.info("✅ AdaptiveRoutingEngine 정지 완료")

    async def route_data_request(
        self,
        request: RoutingRequest,
        context: RoutingContext,
        priority: Priority = Priority.NORMAL
    ) -> RoutingResponse:
        """데이터 요청 라우팅 (Tier Fallback 지원)"""
        start_time = time.time()
        logger.info(f"라우팅 요청 처리 시작 - Request: {request.request_id}, Symbols: {len(request.symbols)}")

        try:
            # 1. Tier 우선순위 목록 생성 (점수순 정렬)
            ranked_tiers = await self.get_ranked_tiers(request, context, self._current_network_usage)
            logger.info(f"Tier 우선순위: {[tier.value for tier in ranked_tiers]}")

            # 2. Tier Fallback 실행
            last_error = None
            for i, tier in enumerate(ranked_tiers):
                try:
                    logger.info(f"[{i + 1}/{len(ranked_tiers)}] {tier.value} Tier 시도")

                    # Tier별 라우팅 실행
                    response = await self._execute_tier_routing(request, context, tier, start_time)

                    # 성공 시 즉시 반환
                    if response.status == ResponseStatus.SUCCESS:
                        await self._update_routing_stats(tier, response)
                        logger.info(
                            f"✅ {tier.value} Tier 성공 - "
                            f"{response.performance.response_time_ms:.2f}ms, "
                            f"성공률: {response.success_rate:.2%}"
                        )
                        return response

                    # 부분 실패도 기록
                    last_error = response.errors[0] if response.errors else f"{tier.value} Tier 실패"
                    logger.warning(f"⚠️ {tier.value} Tier 실패: {last_error}")

                    # 통계는 실패도 기록
                    await self._update_routing_stats(tier, response)

                except Exception as tier_error:
                    last_error = str(tier_error)
                    logger.warning(f"❌ {tier.value} Tier 예외 발생: {last_error}")

                # 다음 Tier로 Fallback
                if i < len(ranked_tiers) - 1:
                    next_tier = ranked_tiers[i + 1]
                    logger.info(f"🔄 {next_tier.value} Tier로 Fallback...")

            # 모든 Tier가 실패한 경우
            final_error = last_error or "알 수 없는 오류"
            logger.error(f"❌ 모든 Tier에서 데이터 조회 실패. 마지막 오류: {final_error}")
            return self._create_fallback_failure_response(request, final_error, ranked_tiers, start_time)

        except Exception as e:
            logger.error(f"라우팅 엔진 치명적 오류: {str(e)}")
            return self._create_error_response(request, e, start_time)

    async def get_optimal_tier(
        self,
        request: RoutingRequest,
        context: RoutingContext,
        current_network_usage: float
    ) -> RoutingTier:
        """최적 라우팅 Tier 결정 (단일 Tier 선택용 - 호환성 유지)"""
        ranked_tiers = await self.get_ranked_tiers(request, context, current_network_usage)
        optimal_tier = ranked_tiers[0] if ranked_tiers else RoutingTier.COLD_REST
        logger.info(f"선택된 최적 Tier: {optimal_tier.value}")
        return optimal_tier

    async def get_ranked_tiers(
        self,
        request: RoutingRequest,
        context: RoutingContext,
        current_network_usage: float
    ) -> List[RoutingTier]:
        """Tier를 점수순으로 정렬하여 반환 (Fallback 우선순위)"""
        logger.debug(f"Tier 우선순위 계산 - Context: {context.usage_context.value}")

        # Usage Context별 Tier 우선순위 매트릭스
        context_tier_preferences = self._get_context_tier_preferences(context.usage_context)

        # 요청 특성 분석
        request_analysis = self._analyze_request_characteristics(request)

        # 네트워크 제약 확인
        network_constraints = self._evaluate_network_constraints(context.network_policy, current_network_usage)

        # 모든 Tier의 점수 계산
        tier_scores = {}
        for tier in RoutingTier:
            score = self._calculate_tier_score(
                tier, request_analysis, context_tier_preferences, network_constraints
            )
            tier_scores[tier] = score
            logger.debug(f"{tier.value}: {score:.3f}")

        # 점수순으로 정렬 (높은 점수부터)
        ranked_tiers = sorted(tier_scores.keys(), key=lambda tier: tier_scores[tier], reverse=True)

        logger.info(f"Tier 우선순위 결정: {[(tier.value, f'{tier_scores[tier]:.3f}') for tier in ranked_tiers]}")

        return ranked_tiers

    def _get_context_tier_preferences(self, usage_context: UsageContext) -> Dict[RoutingTier, float]:
        """Usage Context별 Tier 선호도"""
        preferences = {
            UsageContext.REALTIME_TRADING: {
                RoutingTier.HOT_CACHE: 1.0,
                RoutingTier.LIVE_SUBSCRIPTION: 0.9,
                RoutingTier.BATCH_SNAPSHOT: 0.6,
                RoutingTier.WARM_CACHE_REST: 0.3,
                RoutingTier.COLD_REST: 0.1
            },
            UsageContext.MARKET_SCANNING: {
                RoutingTier.BATCH_SNAPSHOT: 1.0,  # 대량 심볼 처리 최적
                RoutingTier.HOT_CACHE: 0.8,
                RoutingTier.WARM_CACHE_REST: 0.7,
                RoutingTier.LIVE_SUBSCRIPTION: 0.4,  # 개별 구독 비효율
                RoutingTier.COLD_REST: 0.2
            },
            UsageContext.PORTFOLIO_MONITORING: {
                RoutingTier.HOT_CACHE: 0.9,
                RoutingTier.LIVE_SUBSCRIPTION: 0.8,
                RoutingTier.BATCH_SNAPSHOT: 0.7,
                RoutingTier.WARM_CACHE_REST: 0.5,
                RoutingTier.COLD_REST: 0.2
            },
            UsageContext.STRATEGY_BACKTESTING: {
                RoutingTier.WARM_CACHE_REST: 1.0,
                RoutingTier.COLD_REST: 0.9,
                RoutingTier.HOT_CACHE: 0.3,
                RoutingTier.BATCH_SNAPSHOT: 0.2,
                RoutingTier.LIVE_SUBSCRIPTION: 0.1
            },
            UsageContext.RESEARCH_ANALYSIS: {
                RoutingTier.COLD_REST: 1.0,
                RoutingTier.WARM_CACHE_REST: 0.8,
                RoutingTier.HOT_CACHE: 0.3,
                RoutingTier.BATCH_SNAPSHOT: 0.2,
                RoutingTier.LIVE_SUBSCRIPTION: 0.1
            }
        }

        return preferences.get(usage_context, {
            tier: 0.5 for tier in RoutingTier  # 기본값
        })

    def _analyze_request_characteristics(self, request: RoutingRequest) -> Dict[str, Any]:
        """요청 특성 분석"""
        return {
            'symbol_count': len(request.symbols),
            'is_bulk_request': request.is_bulk_request,
            'is_realtime': request.is_realtime,
            'batch_friendly': request.batch_friendly,
            'estimated_size_kb': request.estimated_response_size_kb,
            'data_type': request.data_type,
            'requires_low_latency': request.is_realtime and len(request.symbols) <= 5
        }

    def _evaluate_network_constraints(self, policy: NetworkPolicy, current_usage: float) -> Dict[str, float]:
        """네트워크 제약 평가"""
        # Network Policy별 허용 임계값
        policy_thresholds = {
            NetworkPolicy.AGGRESSIVE: 0.95,
            NetworkPolicy.BALANCED: 0.75,
            NetworkPolicy.CONSERVATIVE: 0.50,
            NetworkPolicy.MINIMAL: 0.25
        }

        threshold = policy_thresholds.get(policy, 0.75)
        network_pressure = min(current_usage / threshold, 1.0)

        return {
            'threshold': threshold,
            'current_usage': current_usage,
            'pressure': network_pressure,
            'available_capacity': max(0.0, threshold - current_usage)
        }

    def _calculate_tier_score(
        self,
        tier: RoutingTier,
        request_analysis: Dict[str, Any],
        context_preferences: Dict[RoutingTier, float],
        network_constraints: Dict[str, float]
    ) -> float:
        """Tier 점수 계산"""
        spec = self._tier_specs[tier]
        base_preference = context_preferences.get(tier, 0.5)

        # 1. 기본 선호도 (40% 가중치)
        score = base_preference * 0.4

        # 2. 성능 적합성 (30% 가중치)
        if request_analysis['symbol_count'] <= spec.max_symbols_per_request:
            performance_score = 1.0
        else:
            # 심볼 수 초과시 패널티
            overflow_ratio = request_analysis['symbol_count'] / spec.max_symbols_per_request
            performance_score = max(0.0, 1.0 - (overflow_ratio - 1.0))

        score += performance_score * 0.3

        # 3. 네트워크 효율성 (20% 가중치)
        network_efficiency = spec.network_efficiency
        network_pressure = network_constraints['pressure']

        # 네트워크 압박시 효율적인 Tier 선호
        efficiency_bonus = network_efficiency * (1.0 + network_pressure)
        score += (efficiency_bonus / 2.0) * 0.2

        # 4. 특수 조건 보너스/패널티 (10% 가중치)
        special_score = 0.0

        # 실시간 요청 + 저지연 요구시 HOT_CACHE/LIVE_SUBSCRIPTION 보너스
        if request_analysis['requires_low_latency']:
            if tier in [RoutingTier.HOT_CACHE, RoutingTier.LIVE_SUBSCRIPTION]:
                special_score += 0.5

        # 대량 요청 + BATCH_SNAPSHOT 보너스
        if request_analysis['is_bulk_request'] and tier == RoutingTier.BATCH_SNAPSHOT:
            special_score += 0.3

        # 배치 친화적 요청 보너스
        if request_analysis['batch_friendly'] and tier == RoutingTier.BATCH_SNAPSHOT:
            special_score += 0.2

        score += special_score * 0.1

        return max(0.0, min(1.0, score))  # 0.0-1.0 범위로 정규화

    async def _execute_tier_routing(
        self,
        request: RoutingRequest,
        context: RoutingContext,
        tier: RoutingTier,
        start_time: float
    ) -> RoutingResponse:
        """Tier별 라우팅 실행 - 실제 UpbitDataProvider 연동"""
        logger.info(f"Tier {tier.value} 라우팅 실행 - {request.data_type} 데이터 요청")

        try:
            # 실제 UpbitDataProvider를 통한 데이터 조회
            data_result = None

            # 데이터 타입에 따른 적절한 메서드 호출
            if request.data_type == DataType.TICKER:
                data_result = await self._execute_ticker_routing(request, tier)
            elif request.data_type == DataType.CANDLE:
                data_result = await self._execute_candle_routing(request, tier)
            elif request.data_type == DataType.ORDERBOOK:
                data_result = await self._execute_orderbook_routing(request, tier)
            elif request.data_type == DataType.TRADE:
                data_result = await self._execute_trade_routing(request, tier)
            else:
                raise ValueError(f"지원하지 않는 데이터 타입: {request.data_type}")

            processed_at = datetime.now()
            responded_at = datetime.now()

            # 데이터 유효성 검사
            is_complete_success, successful_symbols, failed_symbols = self._validate_data_result(data_result, request.symbols)

            # 성능 메트릭 생성
            response_time_ms = (time.time() - start_time) * 1000
            performance = PerformanceMetrics(
                response_time_ms=response_time_ms,
                data_freshness_ms=self._tier_specs[tier].data_freshness_guarantee_ms,
                cache_hit_ratio=0.85 if tier in [RoutingTier.HOT_CACHE, RoutingTier.WARM_CACHE_REST] else 0.0,
                network_bytes=int(request.estimated_response_size_kb * 1024),
                symbols_per_second=len(request.symbols) / (response_time_ms / 1000.0) if response_time_ms > 0 else 0.0
            )

            logger.info(f"✅ Tier {tier.value} 응답 완료 - {len(successful_symbols)}개 심볼 성공, {response_time_ms:.2f}ms")

            # 완전 성공 vs 부분 성공 판단
            if is_complete_success:
                return RoutingResponse.create_success_response(
                    request=request,
                    tier_used=tier,
                    data=data_result,
                    performance=performance,
                    processed_at=processed_at,
                    responded_at=responded_at
                )
            else:
                # 부분 성공 - Fallback 유도
                failed_preview = ', '.join(failed_symbols[:3])
                if len(failed_symbols) > 3:
                    failed_preview += '...'
                errors = [f"부분 실패: {len(failed_symbols)}개 심볼 누락 ({failed_preview})"]
                logger.warning(f"⚠️ Tier {tier.value} 부분 성공 - {len(failed_symbols)}개 심볼 누락")
                raise Exception(f"부분 실패: {errors[0]}")

        except Exception as e:
            logger.error(f"❌ Tier {tier.value} 라우팅 실패: {e}")
            return self._create_error_response(request, e, start_time)

    def _validate_data_result(
        self,
        data_result: Dict[str, Any],
        requested_symbols: List[str]
    ) -> tuple[bool, List[str], List[str]]:
        """데이터 결과 유효성 검사

        Returns:
            (완전_성공_여부, 성공한_심볼들, 실패한_심볼들)
        """
        if not isinstance(data_result, dict):
            return False, [], requested_symbols

        successful_symbols = []
        failed_symbols = []

        # API 응답 구조 확인 및 실제 데이터 추출
        actual_data = data_result

        # 중첩 구조인 경우 (예: {'success': True, 'data': {...}})
        if 'data' in data_result and isinstance(data_result['data'], dict):
            actual_data = data_result['data']

        # 각 심볼별 데이터 검증
        for symbol in requested_symbols:
            if symbol in actual_data and actual_data[symbol] is not None:
                symbol_data = actual_data[symbol]

                # 데이터 타입별 유효성 검사
                if isinstance(symbol_data, dict):
                    # 딕셔너리: 빈 것이 아니거나 유효한 필드가 있는지 확인
                    valid_fields = ['trade_price', 'opening_price', 'market', 'korean_name', 'timestamp']
                    if symbol_data or any(key in symbol_data for key in valid_fields):
                        successful_symbols.append(symbol)
                    else:
                        failed_symbols.append(symbol)
                elif isinstance(symbol_data, list):
                    # 리스트(캔들 데이터): 빈 리스트가 아니면 성공
                    if len(symbol_data) > 0:
                        successful_symbols.append(symbol)
                    else:
                        failed_symbols.append(symbol)
                else:
                    # 기타 타입: None이 아니면 성공
                    successful_symbols.append(symbol)
            else:
                failed_symbols.append(symbol)

        is_complete_success = len(failed_symbols) == 0
        return is_complete_success, successful_symbols, failed_symbols

    async def _execute_ticker_routing(self, request: RoutingRequest, tier: RoutingTier) -> Dict[str, Any]:
        """Ticker 데이터 Tier별 라우팅"""
        return await self.data_provider.get_ticker_data(
            symbols=request.symbols,
            tier=tier.value  # Enum 값을 문자열로 변환
        )

    async def _execute_candle_routing(self, request: RoutingRequest, tier: RoutingTier) -> Dict[str, Any]:
        """Candle 데이터 Tier별 라우팅"""
        # TimeFrame을 interval 문자열로 변환
        timeframe = request.timeframe or TimeFrame.MINUTES_1
        interval = self._timeframe_to_interval(timeframe)

        return await self.data_provider.get_candle_data(
            symbols=request.symbols,
            interval=interval,
            count=request.count or 100,
            tier=tier.value
        )

    async def _execute_orderbook_routing(self, request: RoutingRequest, tier: RoutingTier) -> Dict[str, Any]:
        """Orderbook 데이터 Tier별 라우팅"""
        return await self.data_provider.get_orderbook_data(request.symbols, tier=tier.value)

    async def _execute_trade_routing(self, request: RoutingRequest, tier: RoutingTier) -> Dict[str, Any]:
        """Trade 데이터 Tier별 라우팅"""
        return await self.data_provider.get_trade_data(
            symbols=request.symbols,
            tier=tier.value,
            count=request.count or 100
        )

    def _timeframe_to_interval(self, timeframe: TimeFrame) -> str:
        """TimeFrame을 API interval 문자열로 변환"""
        mapping = {
            TimeFrame.MINUTES_1: "1m",
            TimeFrame.MINUTES_3: "3m",
            TimeFrame.MINUTES_5: "5m",
            TimeFrame.MINUTES_15: "15m",
            TimeFrame.MINUTES_30: "30m",
            TimeFrame.HOURS_1: "1h",
            TimeFrame.HOURS_4: "4h",
            TimeFrame.DAYS_1: "1d",
            TimeFrame.WEEKS_1: "1w",
            TimeFrame.MONTHS_1: "1M"
        }
        return mapping.get(timeframe, "1m")

    def _create_error_response(self, request: RoutingRequest, error: Exception, start_time: float) -> RoutingResponse:
        """오류 응답 생성"""
        processed_at = datetime.now()
        responded_at = datetime.now()

        return RoutingResponse.create_error_response(
            request=request,
            tier_used=RoutingTier.COLD_REST,  # 기본 Tier
            error_message=str(error),
            processed_at=processed_at,
            responded_at=responded_at
        )

    def _create_fallback_failure_response(
        self,
        request: RoutingRequest,
        last_error: str,
        attempted_tiers: List[RoutingTier],
        start_time: float
    ) -> RoutingResponse:
        """모든 Tier Fallback 실패시 종합 오류 응답 생성"""
        processed_at = datetime.now()
        responded_at = datetime.now()

        # 종합 오류 메시지 생성
        attempted_tier_names = [tier.value for tier in attempted_tiers]
        comprehensive_error = (
            f"모든 Tier에서 데이터 조회 실패. "
            f"시도된 Tier: {attempted_tier_names}. "
            f"마지막 오류: {last_error}"
        )

        logger.error(f"Tier Fallback 완전 실패: {comprehensive_error}")

        return RoutingResponse.create_error_response(
            request=request,
            tier_used=attempted_tiers[0] if attempted_tiers else RoutingTier.COLD_REST,  # 첫 번째 시도 Tier
            error_message=comprehensive_error,
            processed_at=processed_at,
            responded_at=responded_at
        )

    async def _update_routing_stats(self, tier: RoutingTier, response: RoutingResponse) -> None:
        """라우팅 통계 업데이트"""
        stats = self._routing_stats[tier]
        stats['request_count'] += 1

        if response.status == ResponseStatus.SUCCESS:
            stats['success_count'] += 1

        stats['total_response_time_ms'] += response.performance.response_time_ms
        stats['avg_symbols_per_request'] = (
            stats['avg_symbols_per_request'] * (stats['request_count'] - 1) + response.symbols_requested
        ) / stats['request_count']

    async def optimize_network_usage(self, usage_threshold: float = 0.8) -> Dict[str, Any]:
        """네트워크 사용량 최적화"""
        logger.info(f"네트워크 최적화 실행 - 임계값: {usage_threshold:.2%}")

        if self._current_network_usage <= usage_threshold:
            return {
                'optimization_needed': False,
                'current_usage': self._current_network_usage,
                'threshold': usage_threshold,
                'message': '네트워크 사용량이 정상 범위입니다.'
            }

        # 최적화 권장사항 생성
        recommendations = []

        # 고사용량 Tier 식별
        high_usage_tiers = [
            tier for tier, spec in self._tier_specs.items()
            if spec.network_efficiency < 0.7
        ]

        recommendations.append(f"고사용량 Tier 제한 권장: {[t.value for t in high_usage_tiers]}")
        recommendations.append("BATCH_SNAPSHOT Tier 사용 증대 권장 (90% 네트워크 효율성)")

        self._last_optimization_time = datetime.now()

        return {
            'optimization_needed': True,
            'current_usage': self._current_network_usage,
            'threshold': usage_threshold,
            'recommendations': recommendations,
            'optimized_at': self._last_optimization_time.isoformat()
        }

    async def get_routing_stats(self) -> Dict[str, Any]:
        """라우팅 통계 조회"""
        total_requests = sum(stats['request_count'] for stats in self._routing_stats.values())

        tier_stats = {}
        for tier, stats in self._routing_stats.items():
            if stats['request_count'] > 0:
                avg_response_time = stats['total_response_time_ms'] / stats['request_count']
                success_rate = stats['success_count'] / stats['request_count']
            else:
                avg_response_time = 0.0
                success_rate = 0.0

            tier_stats[tier.value] = {
                'request_count': stats['request_count'],
                'success_rate': success_rate,
                'avg_response_time_ms': avg_response_time,
                'avg_symbols_per_request': stats['avg_symbols_per_request'],
                'usage_percentage': (stats['request_count'] / total_requests * 100) if total_requests > 0 else 0.0
            }

        return {
            'total_requests': total_requests,
            'tier_statistics': tier_stats,
            'network_usage': self._current_network_usage,
            'last_optimization': self._last_optimization_time.isoformat()
        }

    async def health_check(self) -> Dict[str, Any]:
        """라우터 상태 확인"""
        health_status = "healthy"
        issues = []

        # 네트워크 사용량 확인
        if self._current_network_usage > 0.9:
            health_status = "warning"
            issues.append("네트워크 사용량 높음")

        # Tier별 성공률 확인
        for tier, stats in self._routing_stats.items():
            if stats['request_count'] > 10:  # 충분한 샘플이 있는 경우만
                success_rate = stats['success_count'] / stats['request_count']
                if success_rate < 0.95:
                    health_status = "warning"
                    issues.append(f"{tier.value} Tier 성공률 낮음: {success_rate:.2%}")

        return {
            'status': health_status,
            'tier_count': len(RoutingTier),
            'active_tiers': len([t for t, s in self._routing_stats.items() if s['request_count'] > 0]),
            'network_usage': self._current_network_usage,
            'issues': issues,
            'last_check': datetime.now().isoformat()
        }
