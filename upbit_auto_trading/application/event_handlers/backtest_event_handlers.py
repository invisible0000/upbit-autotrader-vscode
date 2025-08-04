"""
백테스팅 이벤트 핸들러 구현
Backtest 도메인 이벤트를 처리하여 알림, 로깅, 성과 통계 등의 부수 효과를 처리합니다.
"""

from typing import Type

from ..notifications.notification_service import NotificationService, Notification, NotificationType, NotificationChannel
from .base_event_handler import BaseEventHandler
from ...domain.events.backtest_events import (
    BacktestStarted, BacktestCompleted, BacktestFailed, BacktestProgressUpdated
)


class BacktestStartedHandler(BaseEventHandler[BacktestStarted]):
    """백테스팅 시작 이벤트 핸들러"""

    def __init__(self, notification_service: NotificationService):
        """
        핸들러 초기화

        Args:
            notification_service: 알림 서비스
        """
        super().__init__()
        self._notification_service = notification_service

    async def handle(self, event: BacktestStarted) -> None:
        """
        백테스팅 시작 이벤트 처리

        Args:
            event: 백테스팅 시작 이벤트
        """
        # 백테스팅 시작 알림
        notification = Notification(
            title="백테스트 시작",
            message=(f"{event.symbol} 백테스팅이 시작되었습니다. "
                     f"({event.start_date.strftime('%Y-%m-%d')} ~ {event.end_date.strftime('%Y-%m-%d')}, "
                     f"초기자본: {event.initial_capital:,.0f}원)"),
            notification_type=NotificationType.INFO,
            channels=[
                NotificationChannel.UI_TOAST,
                NotificationChannel.UI_STATUS_BAR,
                NotificationChannel.LOG_FILE
            ],
            metadata={
                "backtest_id": event.backtest_id,
                "strategy_id": event.strategy_id,
                "symbol": event.symbol,
                "initial_capital": event.initial_capital,
                "timeframe": event.timeframe,
                "started_by": event.started_by,
                "event_type": event.event_type
            }
        )

        await self._notification_service.send_notification(notification)

        # 백테스팅 시작 로깅
        self._logger.info(f"백테스팅 시작: backtest_id={event.backtest_id}, "
                          f"strategy_id={event.strategy_id}, symbol={event.symbol}")

    def get_event_type(self) -> Type[BacktestStarted]:
        """
        처리할 이벤트 타입 반환

        Returns:
            이벤트 타입 클래스
        """
        return BacktestStarted


class BacktestCompletedHandler(BaseEventHandler[BacktestCompleted]):
    """백테스팅 완료 이벤트 핸들러"""

    def __init__(self, notification_service: NotificationService):
        """
        핸들러 초기화

        Args:
            notification_service: 알림 서비스
        """
        super().__init__()
        self._notification_service = notification_service

    async def handle(self, event: BacktestCompleted) -> None:
        """
        백테스팅 완료 이벤트 처리

        Args:
            event: 백테스팅 완료 이벤트
        """
        # 결과에 따른 알림 타입 및 이모지 결정
        if event.total_return > 0:
            notification_type = NotificationType.SUCCESS
            result_emoji = "📈"
        elif event.total_return > -10:  # 경미한 손실
            notification_type = NotificationType.WARNING
            result_emoji = "📉"
        else:  # 큰 손실
            notification_type = NotificationType.ERROR
            result_emoji = "💥"

        # 성과 요약 메시지 생성
        message = (f"{result_emoji} {event.symbol} 백테스팅 완료!\n"
                   f"📊 총 수익률: {event.total_return:.2f}%\n"
                   f"📈 연간 수익률: {event.annual_return:.2f}%\n"
                   f"📉 최대 손실률: {event.max_drawdown:.2f}%\n"
                   f"🎯 승률: {event.win_rate:.1f}%\n"
                   f"🔄 총 거래: {event.total_trades}회")

        # 백테스팅 완료 알림
        notification = Notification(
            title="백테스트 완료",
            message=message,
            notification_type=notification_type,
            channels=[
                NotificationChannel.UI_TOAST,
                NotificationChannel.UI_STATUS_BAR,
                NotificationChannel.SYSTEM_NOTIFICATION,
                NotificationChannel.LOG_FILE
            ],
            metadata={
                "backtest_id": event.backtest_id,
                "strategy_id": event.strategy_id,
                "symbol": event.symbol,
                "total_return": event.total_return,
                "annual_return": event.annual_return,
                "max_drawdown": event.max_drawdown,
                "sharpe_ratio": event.sharpe_ratio,
                "total_trades": event.total_trades,
                "win_rate": event.win_rate,
                "profit_factor": event.profit_factor,
                "execution_duration_seconds": event.execution_duration_seconds,
                "event_type": event.event_type
            }
        )

        await self._notification_service.send_notification(notification)

        # 성과 통계 로깅
        self._logger.info(f"백테스팅 완료 통계: backtest_id={event.backtest_id}, "
                          f"수익률={event.total_return:.2f}%, MDD={event.max_drawdown:.2f}%, "
                          f"샤프비율={event.sharpe_ratio:.2f}, 거래수={event.total_trades}")

        # 백테스팅 결과 캐시 무효화 (향후 캐시 시스템과 연동)
        self._logger.info(f"백테스팅 결과 캐시 무효화 필요: strategy_id={event.strategy_id}")

    def get_event_type(self) -> Type[BacktestCompleted]:
        """
        처리할 이벤트 타입 반환

        Returns:
            이벤트 타입 클래스
        """
        return BacktestCompleted


class BacktestFailedHandler(BaseEventHandler[BacktestFailed]):
    """백테스팅 실패 이벤트 핸들러"""

    def __init__(self, notification_service: NotificationService):
        """
        핸들러 초기화

        Args:
            notification_service: 알림 서비스
        """
        super().__init__()
        self._notification_service = notification_service

    async def handle(self, event: BacktestFailed) -> None:
        """
        백테스팅 실패 이벤트 처리

        Args:
            event: 백테스팅 실패 이벤트
        """
        # 실패 단계별 상세 메시지 생성
        stage_messages = {
            "data_loading": "데이터 로딩 중 오류가 발생했습니다",
            "signal_generation": "매매 신호 생성 중 오류가 발생했습니다",
            "trade_execution": "거래 실행 중 오류가 발생했습니다",
            "metric_calculation": "성과 지표 계산 중 오류가 발생했습니다"
        }

        stage_message = stage_messages.get(event.failure_stage, "알 수 없는 단계에서 오류가 발생했습니다")

        # 백테스팅 실패 알림
        notification = Notification(
            title="백테스트 실패",
            message=(f"❌ {event.symbol} 백테스팅이 실패했습니다.\n"
                     f"🔍 실패 단계: {stage_message}\n"
                     f"💬 오류 내용: {event.error_message}"),
            notification_type=NotificationType.ERROR,
            channels=[
                NotificationChannel.UI_TOAST,
                NotificationChannel.UI_STATUS_BAR,
                NotificationChannel.LOG_FILE
            ],
            metadata={
                "backtest_id": event.backtest_id,
                "strategy_id": event.strategy_id,
                "symbol": event.symbol,
                "failure_stage": event.failure_stage,
                "error_message": event.error_message,
                "error_type": event.error_type,
                "error_code": event.error_type,  # 테스트에서 error_code 필드 기대
                "stack_trace": event.stack_trace,
                "partial_results": event.partial_results,
                "event_type": event.event_type
            }
        )

        await self._notification_service.send_notification(notification)

        # 에러 상세 로깅
        self._logger.error(f"백테스팅 실패: backtest_id={event.backtest_id}, "
                           f"실패단계={event.failure_stage}, 오류={event.error_message}")

        if event.stack_trace:
            self._logger.debug(f"백테스팅 실패 스택트레이스: {event.stack_trace}")

    def get_event_type(self) -> Type[BacktestFailed]:
        """
        처리할 이벤트 타입 반환

        Returns:
            이벤트 타입 클래스
        """
        return BacktestFailed


class BacktestProgressUpdatedHandler(BaseEventHandler[BacktestProgressUpdated]):
    """백테스팅 진행률 업데이트 이벤트 핸들러"""

    def __init__(self, notification_service: NotificationService):
        """
        핸들러 초기화

        Args:
            notification_service: 알림 서비스
        """
        super().__init__()
        self._notification_service = notification_service
        self._last_logged_progress = {}  # 백테스트별 마지막 로깅 진행률 저장

    async def handle(self, event: BacktestProgressUpdated) -> None:
        """
        백테스팅 진행률 업데이트 이벤트 처리

        Args:
            event: 백테스팅 진행률 업데이트 이벤트
        """
        backtest_id = event.backtest_id
        progress_percent = event.progress_percent

        # 로깅 스팸 방지: 10% 단위로만 로깅
        last_progress = self._last_logged_progress.get(backtest_id, 0)
        if progress_percent - last_progress >= 10 or progress_percent >= 100:

            # 성과 정보가 있으면 포함
            performance_text = ""
            if event.current_performance:
                current_return = event.current_performance.get("total_return", 0)
                performance_text = f", 현재수익률: {current_return:.1f}%"

            # 진행률 로깅
            self._logger.info(f"백테스팅 진행: backtest_id={backtest_id}, "
                              f"진행률={progress_percent:.1f}%, "
                              f"처리완료={event.processed_points}/{event.total_points}"
                              f"{performance_text}")

            # 마지막 로깅 진행률 업데이트
            self._last_logged_progress[backtest_id] = progress_percent

        # 진행률이 0% (시작), 주요 마일스톤 (25%, 75%), 또는 100% (완료)인 경우 알림 전송
        major_milestones = [25.0, 75.0]
        if progress_percent == 0 or progress_percent >= 100 or progress_percent in major_milestones:
            if progress_percent == 0:
                title = "백테스팅 시작"
                message = f"{event.symbol} 백테스팅 분석을 시작합니다"
            elif progress_percent >= 100:
                title = "백테스팅 진행률"
                message = f"{event.symbol} 백테스팅 분석 완료 (100%)"
            else:
                title = "백테스트 진행 상황"
                message = f"{event.symbol} 백테스팅 진행 중... ({progress_percent:.0f}%)"

            notification = Notification(
                title=title,
                message=message,
                notification_type=NotificationType.INFO,
                channels=[NotificationChannel.UI_STATUS_BAR],
                metadata={
                    "backtest_id": event.backtest_id,
                    "strategy_id": event.strategy_id,
                    "progress_percent": progress_percent,
                    "event_type": event.event_type
                }
            )

            await self._notification_service.send_notification(notification)

            # 완료된 백테스트는 진행률 추적에서 제거
            if backtest_id in self._last_logged_progress:
                del self._last_logged_progress[backtest_id]

    def get_event_type(self) -> Type[BacktestProgressUpdated]:
        """
        처리할 이벤트 타입 반환

        Returns:
            이벤트 타입 클래스
        """
        return BacktestProgressUpdated
