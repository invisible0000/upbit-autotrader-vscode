"""
Smart Router V2.0 연동 어댑터

Smart Data Provider와 Smart Router V2.0을 연결하는 어댑터입니다.
"""
from typing import List, Dict, Optional, Any, Union

from upbit_auto_trading.infrastructure.logging import create_component_logger
from ..models.priority import Priority

logger = create_component_logger("SmartRouterAdapter")


def _convert_priority_to_realtime(priority: Priority):
    """Priority를 RealtimePriority로 변환"""
    try:
        from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models import RealtimePriority
        # Priority enum 값을 RealtimePriority로 매핑
        priority_mapping = {
            Priority.HIGH: RealtimePriority.HIGH,
            Priority.NORMAL: RealtimePriority.MEDIUM,  # NORMAL을 MEDIUM으로 매핑
            Priority.LOW: RealtimePriority.LOW
        }
        result = priority_mapping.get(priority, RealtimePriority.MEDIUM)
        return result
    except ImportError:
        # RealtimePriority를 찾을 수 없는 경우 기본값 반환
        # 이 경우 호출자가 적절히 처리해야 함
        from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models import RealtimePriority
        return RealtimePriority.MEDIUM


class SmartRouterAdapter:
    """
    Smart Router V2.0 연동 어댑터

    Smart Data Provider의 요청을 Smart Router V2.0 형식으로 변환하고
    응답을 Smart Data Provider 형식으로 변환합니다.
    """

    def __init__(self):
        """어댑터 초기화"""
        try:
            from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.main_system_adapter import (
                get_market_data_adapter
            )
            self.smart_router_adapter = get_market_data_adapter()
            self._is_available = True
            logger.info("Smart Router 어댑터 초기화 완료")
        except Exception as e:
            logger.error(f"Smart Router 어댑터 초기화 실패: {e}")
            self.smart_router_adapter = None
            self._is_available = False

    async def get_candles(self,
                          symbols: Union[str, List[str]],
                          timeframe: str,
                          count: Optional[int] = None,
                          start_time: Optional[str] = None,
                          end_time: Optional[str] = None,
                          priority: Priority = Priority.NORMAL) -> Dict[str, Any]:
        """
        캔들 데이터 조회 (단일/일괄 통합)

        Args:
            symbols: 심볼 또는 심볼 리스트 (예: 'KRW-BTC' 또는 ['KRW-BTC', 'KRW-ETH'])
            timeframe: 타임프레임 (예: '1m', '5m', '1h', '1d')
            count: 조회할 캔들 개수
            start_time: 시작 시간 (ISO format)
            end_time: 종료 시간 (ISO format)
            priority: 요청 우선순위

        Returns:
            캔들 데이터 (단일 요청 시 dict, 일괄 요청 시 list)
        """
        if not self._is_available or self.smart_router_adapter is None:
            return {
                'success': False,
                'error': 'Smart Router 사용 불가',
                'source': 'smart_router_unavailable'
            }

        try:
            # 입력 정규화
            if isinstance(symbols, str):
                symbols_list = [symbols]
                is_single = True
            else:
                symbols_list = symbols
                is_single = False

            logger.debug(f"Smart Router 캔들 요청: {symbols_list} {timeframe} (단일: {is_single}), count={count}")

            # Smart Router를 통한 캔들 데이터 요청 (항상 batch 처리)
            result = await self.smart_router_adapter.get_candle_data(
                symbols=symbols_list,
                interval=timeframe,
                count=count or 200,
                use_cache=True
            )

            if result.get('success', False):
                candles_data = result.get('data', [])

                # 실제 캔들 수 계산 (data가 dict이면 _candles_list에서, list이면 직접)
                if isinstance(candles_data, dict):
                    actual_candles = candles_data.get('_candles_list', [])
                    candle_count = len(actual_candles)
                else:
                    candle_count = len(candles_data) if isinstance(candles_data, list) else 0

                logger.info(f"Smart Router 캔들 성공: {symbols_list} {timeframe}, {candle_count}개")

                # 단일 요청인 경우 첫 번째 데이터 반환, 일괄인 경우 전체 반환
                if is_single and isinstance(candles_data, list) and candles_data:
                    response_data = candles_data[0]
                else:
                    response_data = candles_data

                return {
                    'success': True,
                    'data': response_data,
                    'source': 'smart_router',
                    'channel': result.get('metadata', {}).get('channel', 'unknown')
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"Smart Router 캔들 실패: {symbols_list} {timeframe}, {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'source': 'smart_router'
                }

        except Exception as e:
            logger.error(f"Smart Router 캔들 요청 예외: {symbols} {timeframe}, {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'smart_router_error'
            }

    async def get_ticker(self,
                         symbols: Union[str, List[str]],
                         priority: Priority = Priority.HIGH) -> Dict[str, Any]:
        """
        실시간 티커 조회 (단일/일괄 통합)

        Args:
            symbols: 심볼 또는 심볼 리스트
            priority: 요청 우선순위

        Returns:
            티커 데이터 (단일 요청 시 dict, 일괄 요청 시 list)
        """
        if not self._is_available or self.smart_router_adapter is None:
            return {
                'success': False,
                'error': 'Smart Router 사용 불가',
                'source': 'smart_router_unavailable'
            }

        try:
            # 입력 정규화
            if isinstance(symbols, str):
                symbols_list = [symbols]
                is_single = True
            else:
                symbols_list = symbols
                is_single = False

            logger.debug(f"Smart Router 티커 요청: {symbols_list} (단일: {is_single})")

            # Smart Router를 통한 티커 요청 (항상 batch 처리)
            result = await self.smart_router_adapter.get_ticker_data(
                symbols=symbols_list,
                use_cache=True
            )

            if result.get('success', False):
                ticker_data = result.get('data')
                logger.debug(f"Smart Router 티커 성공: {symbols_list}")

                response_data = {
                    'success': True,
                    'data': ticker_data[0] if is_single and isinstance(ticker_data, list) and ticker_data else ticker_data,
                    'source': 'smart_router',
                    'channel': result.get('metadata', {}).get('channel', 'unknown')
                }
                return response_data
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"Smart Router 티커 실패: {symbols_list}, {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'source': 'smart_router'
                }

        except Exception as e:
            logger.error(f"Smart Router 티커 요청 예외: {symbols}, {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'smart_router_error'
            }

    async def get_markets(self,
                          is_details: bool = False,
                          priority: Priority = Priority.NORMAL) -> Dict[str, Any]:
        """
        마켓 목록 조회

        Args:
            is_details: 상세 정보 포함 여부
            priority: 요청 우선순위

        Returns:
            마켓 목록 데이터
        """
        # Smart Router는 현재 마켓 목록 조회를 지원하지 않으므로
        # 항상 폴백으로 처리
        return {
            'success': False,
            'error': 'Smart Router에서 마켓 목록 조회 미지원',
            'source': 'smart_router_not_supported'
        }

    async def get_orderbook(self,
                            symbols: Union[str, List[str]],
                            priority: Priority = Priority.HIGH) -> Dict[str, Any]:
        """
        호가창 조회 (단일/일괄 통합)

        Args:
            symbols: 심볼 또는 심볼 리스트
            priority: 요청 우선순위

        Returns:
            호가창 데이터 (단일 요청 시 dict, 일괄 요청 시 list)
        """
        if not self._is_available or self.smart_router_adapter is None:
            return {
                'success': False,
                'error': 'Smart Router 사용 불가',
                'source': 'smart_router_unavailable'
            }

        try:
            # 입력 정규화
            if isinstance(symbols, str):
                symbols_list = [symbols]
                is_single = True
            else:
                symbols_list = symbols
                is_single = False

            logger.debug(f"Smart Router 호가창 요청: {symbols_list} (단일: {is_single})")

            # Smart Router를 통한 호가창 요청 (항상 batch 처리)
            result = await self.smart_router_adapter.get_orderbook_data(
                symbols=symbols_list,
                use_cache=True
            )

            if result.get('success', False):
                orderbook_data = result.get('data')
                logger.debug(f"Smart Router 호가창 성공: {symbols_list}")

                # 단일 요청인 경우 첫 번째 데이터 반환, 일괄인 경우 전체 반환
                if is_single and isinstance(orderbook_data, list) and orderbook_data:
                    response_data = orderbook_data[0]
                else:
                    response_data = orderbook_data

                return {
                    'success': True,
                    'data': response_data,
                    'source': 'smart_router',
                    'channel': result.get('metadata', {}).get('channel', 'unknown')
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"Smart Router 호가창 실패: {symbols_list}, {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'source': 'smart_router'
                }

        except Exception as e:
            logger.error(f"Smart Router 호가창 요청 예외: {symbols}, {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'smart_router_error'
            }

    async def get_trades(self,
                         symbols: Union[str, List[str]],
                         count: int = 100,
                         priority: Priority = Priority.NORMAL) -> Dict[str, Any]:
        """
        체결 내역 조회 (단일/일괄 통합)

        Args:
            symbols: 심볼 또는 심볼 리스트
            count: 조회할 체결 개수
            priority: 요청 우선순위

        Returns:
            체결 데이터 (단일 요청 시 dict, 일괄 요청 시 list)
        """
        if not self._is_available or self.smart_router_adapter is None:
            return {
                'success': False,
                'error': 'Smart Router 사용 불가',
                'source': 'smart_router_unavailable'
            }

        try:
            # 입력 정규화
            if isinstance(symbols, str):
                symbols_list = [symbols]
                is_single = True
            else:
                symbols_list = symbols
                is_single = False

            logger.debug(f"Smart Router 체결 요청: {symbols_list} (단일: {is_single}), count={count}")

            # Smart Router를 통한 체결 데이터 요청 (항상 batch 처리)
            result = await self.smart_router_adapter.get_trades(
                symbols=symbols_list,
                count=min(count, 500),  # API 최대 제한 적용
                realtime_priority=_convert_priority_to_realtime(priority)
            )

            if result.get('success', False):
                trades_data = result.get('data', [])
                logger.info(f"Smart Router 체결 성공: {symbols_list}, {len(trades_data)}개")

                # 단일 요청인 경우 첫 번째 데이터 반환, 일괄인 경우 전체 반환
                if is_single and isinstance(trades_data, list) and trades_data:
                    response_data = trades_data[0]
                else:
                    response_data = trades_data

                return {
                    'success': True,
                    'data': response_data,
                    'source': 'smart_router',
                    'channel': result.get('metadata', {}).get('channel', 'unknown')
                }
            else:
                logger.error(f"Smart Router 체결 실패: {symbols_list}, {result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error', 'Smart Router 체결 요청 실패'),
                    'source': 'smart_router_error'
                }

        except Exception as e:
            logger.error(f"Smart Router 체결 요청 예외: {symbols}, {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'smart_router_error'
            }

    def get_performance_summary(self) -> Dict[str, Any]:
        """성능 요약 정보 조회"""
        if not self._is_available or self.smart_router_adapter is None:
            return {
                'smart_router_available': False,
                'total_requests': 0,
                'success_rate': 0.0,
                'error': 'Smart Router 사용 불가'
            }

        try:
            # Smart Router에서 성능 정보 조회 (메서드가 있다면)
            if hasattr(self.smart_router_adapter, 'get_performance_summary'):
                return self.smart_router_adapter.get_performance_summary()
            else:
                return {
                    'smart_router_available': True,
                    'total_requests': 0,
                    'success_rate': 0.0,
                    'status': 'performance_tracking_unavailable'
                }
        except Exception as e:
            logger.error(f"Smart Router 성능 요약 조회 실패: {e}")
            return {
                'smart_router_available': False,
                'error': str(e),
                'total_requests': 0,
                'success_rate': 0.0
            }
