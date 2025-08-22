"""
Smart Router V2.0 연동 어댑터

Smart Data Provider와 Smart Router V2.0을 연결하는 어댑터입니다.
"""
from typing import List, Dict, Optional, Any

from upbit_auto_trading.infrastructure.logging import create_component_logger
from ..models.priority import Priority

logger = create_component_logger("SmartRouterAdapter")


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
                          symbol: str,
                          timeframe: str,
                          count: Optional[int] = None,
                          start_time: Optional[str] = None,
                          end_time: Optional[str] = None,
                          priority: Priority = Priority.NORMAL) -> Dict[str, Any]:
        """
        캔들 데이터 조회

        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m', '1h', '1d')
            count: 조회할 캔들 개수
            start_time: 시작 시간 (ISO format)
            end_time: 종료 시간 (ISO format)
            priority: 요청 우선순위

        Returns:
            캔들 데이터 리스트
        """
        if not self._is_available or self.smart_router_adapter is None:
            return {
                'success': False,
                'error': 'Smart Router 사용 불가',
                'source': 'smart_router_unavailable'
            }

        try:
            logger.debug(f"Smart Router 캔들 요청: {symbol} {timeframe}, count={count}")

            # Smart Router를 통한 캔들 데이터 요청
            result = await self.smart_router_adapter.get_candle_data(
                symbols=symbol,
                interval=timeframe,
                count=count or 200,
                use_cache=True
            )

            if result.get('success', False):
                candles = result.get('data', [])

                # 실제 캔들 수 계산 (data가 dict이면 _candles_list에서, list이면 직접)
                if isinstance(candles, dict):
                    actual_candles = candles.get('_candles_list', [])
                    candle_count = len(actual_candles)
                else:
                    candle_count = len(candles) if isinstance(candles, list) else 0

                logger.info(f"Smart Router 캔들 성공: {symbol} {timeframe}, {candle_count}개")
                return {
                    'success': True,
                    'data': candles,
                    'source': 'smart_router',
                    'channel': result.get('metadata', {}).get('channel', 'unknown')
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"Smart Router 캔들 실패: {symbol} {timeframe}, {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'source': 'smart_router'
                }

        except Exception as e:
            logger.error(f"Smart Router 캔들 요청 예외: {symbol} {timeframe}, {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'smart_router_error'
            }

    async def get_ticker(self,
                         symbol: str,
                         priority: Priority = Priority.HIGH) -> Dict[str, Any]:
        """
        실시간 티커 조회

        Args:
            symbol: 심볼
            priority: 요청 우선순위

        Returns:
            티커 데이터
        """
        if not self._is_available or self.smart_router_adapter is None:
            return {
                'success': False,
                'error': 'Smart Router 사용 불가',
                'source': 'smart_router_unavailable'
            }

        try:
            logger.debug(f"Smart Router 티커 요청: {symbol}")

            # Smart Router를 통한 티커 요청
            result = await self.smart_router_adapter.get_ticker_data(
                symbols=symbol,
                use_cache=True
            )

            if result.get('success', False):
                ticker = result.get('data')
                logger.debug(f"Smart Router 티커 성공: {symbol}")
                return {
                    'success': True,
                    'data': ticker,
                    'source': 'smart_router',
                    'channel': result.get('metadata', {}).get('channel', 'unknown')
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"Smart Router 티커 실패: {symbol}, {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'source': 'smart_router'
                }

        except Exception as e:
            logger.error(f"Smart Router 티커 요청 예외: {symbol}, {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'smart_router_error'
            }

    async def get_tickers(self,
                          symbols: List[str],
                          priority: Priority = Priority.HIGH) -> Dict[str, Any]:
        """
        다중 심볼 티커 조회

        Args:
            symbols: 심볼 리스트
            priority: 요청 우선순위

        Returns:
            다중 티커 데이터
        """
        if not self._is_available or self.smart_router_adapter is None:
            return {
                'success': False,
                'error': 'Smart Router 사용 불가',
                'source': 'smart_router_unavailable'
            }

        try:
            logger.debug(f"Smart Router 다중 티커 요청: {len(symbols)}개 심볼")

            # Smart Router를 통한 다중 티커 요청
            result = await self.smart_router_adapter.get_ticker_data(
                symbols=symbols,
                use_cache=True
            )

            if result.get('success', False):
                tickers = result.get('data', [])
                logger.info(f"Smart Router 다중 티커 성공: {len(tickers)}개")
                return {
                    'success': True,
                    'data': tickers,
                    'source': 'smart_router',
                    'channel': result.get('metadata', {}).get('channel', 'unknown')
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"Smart Router 다중 티커 실패: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'source': 'smart_router'
                }

        except Exception as e:
            logger.error(f"Smart Router 다중 티커 요청 예외: {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'smart_router_error'
            }

    async def get_orderbook(self,
                            symbol: str,
                            priority: Priority = Priority.HIGH) -> Dict[str, Any]:
        """
        호가창 조회

        Args:
            symbol: 심볼
            priority: 요청 우선순위

        Returns:
            호가창 데이터
        """
        if not self._is_available or self.smart_router_adapter is None:
            return {
                'success': False,
                'error': 'Smart Router 사용 불가',
                'source': 'smart_router_unavailable'
            }

        try:
            logger.debug(f"Smart Router 호가창 요청: {symbol}")

            # Smart Router를 통한 호가창 요청
            result = await self.smart_router_adapter.get_orderbook_data(
                symbols=symbol,
                use_cache=True
            )

            if result.get('success', False):
                orderbook = result.get('data')
                logger.debug(f"Smart Router 호가창 성공: {symbol}")
                return {
                    'success': True,
                    'data': orderbook,
                    'source': 'smart_router',
                    'channel': result.get('metadata', {}).get('channel', 'unknown')
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"Smart Router 호가창 실패: {symbol}, {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'source': 'smart_router'
                }

        except Exception as e:
            logger.error(f"Smart Router 호가창 요청 예외: {symbol}, {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'smart_router_error'
            }

    async def get_trades(self,
                         symbol: str,
                         count: int = 100,
                         priority: Priority = Priority.NORMAL) -> Dict[str, Any]:
        """
        체결 내역 조회

        Args:
            symbol: 심볼
            count: 조회할 체결 개수
            priority: 요청 우선순위

        Returns:
            체결 데이터
        """
        if not self._is_available or self.smart_router_adapter is None:
            return {
                'success': False,
                'error': 'Smart Router 사용 불가',
                'source': 'smart_router_unavailable'
            }

        try:
            logger.debug(f"Smart Router 체결 요청: {symbol}, count={count}")

            # 체결 내역은 현재 Smart Router에서 미구현
            return {
                'success': False,
                'error': 'Smart Router에서 체결 내역 미구현',
                'source': 'smart_router_unsupported'
            }

        except Exception as e:
            logger.error(f"Smart Router 체결 요청 예외: {symbol}, {e}")
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
