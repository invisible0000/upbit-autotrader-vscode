"""
Settings and Live Trading Presenters - MVP 패턴

설정 관리와 실시간 거래 UI를 위한 Presenter들입니다.
"""

from typing import Dict, Any, List
import logging

from upbit_auto_trading.presentation.interfaces.view_interfaces import (
    ISettingsView, ILiveTradingView
)


class SettingsPresenter:
    """설정 관리 Presenter

    애플리케이션 설정 UI의 MVP 패턴 Presenter입니다.
    """

    def __init__(self, view: ISettingsView, settings_service):
        """Presenter 초기화

        Args:
            view: 설정 View 인터페이스
            settings_service: 설정 관리 Service
        """
        self._view = view
        self._settings_service = settings_service
        self._logger = logging.getLogger(__name__)

    def load_settings(self) -> None:
        """설정 로드"""
        try:
            # Application Service를 통해 설정 조회
            settings = self._settings_service.get_all_settings()

            # View에 표시
            self._view.display_settings(settings)

            self._logger.info("설정 로드 완료")

        except Exception as e:
            self._logger.error(f"설정 로드 실패: {e}", exc_info=True)

    def save_settings(self) -> None:
        """설정 저장"""
        try:
            # View에서 설정 데이터 수집
            settings_data = self._view.get_settings_data()

            # Application Service를 통해 저장
            self._settings_service.update_settings(settings_data)

            # 테마 변경 시 즉시 적용
            if 'theme' in settings_data:
                self._view.apply_theme_settings(settings_data['theme'])

            self._logger.info("설정 저장 완료")

        except Exception as e:
            self._logger.error(f"설정 저장 실패: {e}", exc_info=True)

    def reset_to_defaults(self) -> None:
        """설정 기본값으로 초기화"""
        try:
            # Application Service를 통해 기본값으로 리셋
            default_settings = self._settings_service.reset_to_defaults()

            # View에 기본값 표시
            self._view.display_settings(default_settings)

            self._logger.info("설정이 기본값으로 초기화됨")

        except Exception as e:
            self._logger.error(f"설정 초기화 실패: {e}", exc_info=True)


class LiveTradingPresenter:
    """실시간 거래 관리 Presenter

    실시간 거래 모니터링 및 제어 UI의 MVP 패턴 Presenter입니다.
    """

    def __init__(self, view: ILiveTradingView, trading_service, market_service):
        """Presenter 초기화

        Args:
            view: 실시간 거래 View 인터페이스
            trading_service: 거래 관리 Service
            market_service: 시장 데이터 Service
        """
        self._view = view
        self._trading_service = trading_service
        self._market_service = market_service
        self._logger = logging.getLogger(__name__)
        self._is_monitoring = False

    def start_monitoring(self) -> None:
        """실시간 모니터링 시작"""
        try:
            if not self._is_monitoring:
                self._is_monitoring = True

                # 활성 전략 로드
                self.refresh_active_strategies()

                # 시장 데이터 모니터링 시작
                self._market_service.start_real_time_monitoring(
                    callback=self._on_market_data_update
                )

                self._logger.info("실시간 모니터링 시작")

        except Exception as e:
            self._is_monitoring = False
            self._logger.error(f"실시간 모니터링 시작 실패: {e}", exc_info=True)

    def stop_monitoring(self) -> None:
        """실시간 모니터링 중지"""
        try:
            if self._is_monitoring:
                self._is_monitoring = False

                # 시장 데이터 모니터링 중지
                self._market_service.stop_real_time_monitoring()

                self._logger.info("실시간 모니터링 중지")

        except Exception as e:
            self._logger.error(f"실시간 모니터링 중지 실패: {e}", exc_info=True)

    def refresh_active_strategies(self) -> None:
        """활성 전략 목록 새로고침"""
        try:
            # Application Service를 통해 활성 전략 조회
            active_strategies = self._trading_service.get_active_strategies()

            # View에 표시
            strategies_data = [self._strategy_to_view_data(strategy) for strategy in active_strategies]
            self._view.display_active_strategies(strategies_data)

            self._logger.debug(f"활성 전략 새로고침: {len(active_strategies)}개")

        except Exception as e:
            self._logger.error(f"활성 전략 새로고침 실패: {e}", exc_info=True)

    def stop_strategy(self, strategy_id: str) -> None:
        """특정 전략 중지"""
        try:
            # Application Service를 통해 전략 중지
            self._trading_service.stop_strategy(strategy_id)

            # 전략 목록 새로고침
            self.refresh_active_strategies()

            self._logger.info(f"전략 중지: {strategy_id}")

        except Exception as e:
            self._logger.error(f"전략 중지 실패 ({strategy_id}): {e}", exc_info=True)

    def emergency_stop_all(self) -> None:
        """모든 전략 긴급 중지"""
        try:
            # View에서 사용자 확인
            if self._view.show_emergency_stop_confirmation():
                # Application Service를 통해 모든 전략 중지
                self._trading_service.emergency_stop_all_strategies()

                # 전략 목록 새로고침
                self.refresh_active_strategies()

                self._logger.warning("모든 전략 긴급 중지 실행")

        except Exception as e:
            self._logger.error(f"긴급 중지 실패: {e}", exc_info=True)

    def _on_market_data_update(self, market_data: Dict[str, Any]) -> None:
        """시장 데이터 업데이트 콜백"""
        try:
            # View에 시장 데이터 표시
            self._view.display_market_data(market_data)

            # 전략별 상태 업데이트가 필요한 경우
            if 'strategy_updates' in market_data:
                for update in market_data['strategy_updates']:
                    strategy_id = update['strategy_id']
                    status = update['status']
                    self._view.update_strategy_status(strategy_id, status)

        except Exception as e:
            self._logger.error(f"시장 데이터 업데이트 처리 실패: {e}", exc_info=True)

    def _strategy_to_view_data(self, strategy) -> Dict[str, Any]:
        """전략 객체를 View 데이터로 변환

        Args:
            strategy: 전략 객체

        Returns:
            Dict[str, Any]: View용 전략 데이터
        """
        return {
            'id': strategy.id,
            'name': strategy.name,
            'status': strategy.status,
            'position_size': getattr(strategy, 'position_size', 0),
            'current_profit': getattr(strategy, 'current_profit', 0),
            'total_trades': getattr(strategy, 'total_trades', 0),
            'win_rate': getattr(strategy, 'win_rate', 0),
            'last_trade_time': getattr(strategy, 'last_trade_time', None)
        }
