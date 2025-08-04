"""
Backtest Application Service - 백테스팅 관리 Application Service

백테스팅 관련 Use Case들을 구현합니다:
- 백테스팅 시작, 중단, 상태 조회
- 백테스팅 결과 관리
- 도메인 이벤트 발행
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from upbit_auto_trading.application.services.base_application_service import BaseApplicationService
from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
from upbit_auto_trading.domain.repositories.backtest_repository import BacktestRepository
from upbit_auto_trading.domain.repositories.market_data_repository import MarketDataRepository


class BacktestApplicationService(BaseApplicationService):
    """백테스팅 Application Service

    UI의 백테스팅 패널에서 수행되던 비즈니스 로직을 중앙 집중화합니다.
    """

    def __init__(self, strategy_repository: StrategyRepository,
                 backtest_repository: BacktestRepository,
                 market_data_repository: MarketDataRepository):
        super().__init__()
        self._strategy_repository = strategy_repository
        self._backtest_repository = backtest_repository
        self._market_data_repository = market_data_repository
        self._logger = logging.getLogger(__name__)

    def start_backtest(self, strategy_id: str, symbol: str,
                      start_date: datetime, end_date: datetime,
                      initial_capital: float, settings: Dict[str, Any]) -> str:
        """백테스팅 시작

        Args:
            strategy_id: 전략 ID
            symbol: 거래 심볼 (예: KRW-BTC)
            start_date: 백테스팅 시작일
            end_date: 백테스팅 종료일
            initial_capital: 초기 자본금
            settings: 백테스팅 설정

        Returns:
            str: 백테스트 ID

        Raises:
            ValueError: 검증 실패 시
        """
        # 1. 전략 존재 여부 확인
        strategy = self._strategy_repository.find_by_id(StrategyId(strategy_id))
        if not strategy:
            raise ValueError(f"존재하지 않는 전략입니다: {strategy_id}")

        # 2. 백테스트 ID 생성
        backtest_id = f"BT_{strategy_id}_{int(datetime.now().timestamp())}"

        # 3. 백테스트 시작 이벤트 발행
        try:
            from upbit_auto_trading.domain.events.backtest_events import BacktestStarted
            start_event = BacktestStarted(
                backtest_id=backtest_id,
                strategy_id=StrategyId(strategy_id),
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                settings=settings
            )
            self._event_publisher.publish(start_event)
        except ImportError:
            # BacktestStarted 이벤트가 없는 경우 로깅만
            self._logger.warning("BacktestStarted 이벤트 클래스를 찾을 수 없습니다. 이벤트 발행을 건너뜁니다.")

        # 4. 백테스트 메타데이터 저장
        backtest_metadata = {
            "backtest_id": backtest_id,
            "strategy_id": strategy_id,
            "symbol": symbol,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "initial_capital": initial_capital,
            "settings": settings,
            "status": "started",
            "created_at": datetime.now().isoformat()
        }

        self._backtest_repository.save_metadata(backtest_id, backtest_metadata)

        self._logger.info(f"백테스팅 시작: {backtest_id} (전략: {strategy.name})")
        return backtest_id

    def get_backtest_result(self, backtest_id: str) -> Dict[str, Any]:
        """백테스팅 결과 조회

        Args:
            backtest_id: 백테스트 ID

        Returns:
            Dict[str, Any]: 백테스팅 결과

        Raises:
            ValueError: 백테스트 없음
        """
        result = self._backtest_repository.find_by_id(backtest_id)
        if not result:
            raise ValueError(f"존재하지 않는 백테스트입니다: {backtest_id}")

        return result

    def get_backtest_progress(self, backtest_id: str) -> Dict[str, Any]:
        """백테스팅 진행률 조회

        Args:
            backtest_id: 백테스트 ID

        Returns:
            Dict[str, Any]: 진행률 정보
                - progress: float (0.0 ~ 1.0)
                - status: str
                - current_date: str (현재 처리 중인 날짜)
                - estimated_completion: str (완료 예상 시간)
        """
        progress = self._backtest_repository.get_progress(backtest_id)
        if not progress:
            return {"progress": 0.0, "status": "not_found"}

        return progress

    def stop_backtest(self, backtest_id: str, reason: str = "user_requested") -> bool:
        """백테스팅 중단

        Args:
            backtest_id: 백테스트 ID
            reason: 중단 이유

        Returns:
            bool: 중단 성공 여부

        Raises:
            ValueError: 백테스트 없음
        """
        # 1. 백테스트 존재 확인
        backtest = self._backtest_repository.find_by_id(backtest_id)
        if not backtest:
            raise ValueError(f"존재하지 않는 백테스트입니다: {backtest_id}")

        # 2. 중단 이벤트 발행
        try:
            from upbit_auto_trading.domain.events.backtest_events import BacktestStopped
            stop_event = BacktestStopped(
                backtest_id=backtest_id,
                reason=reason,
                stopped_at=datetime.now()
            )
            self._event_publisher.publish(stop_event)
        except ImportError:
            self._logger.warning("BacktestStopped 이벤트 클래스를 찾을 수 없습니다.")

        # 3. 상태 업데이트
        self._backtest_repository.update_status(backtest_id, "stopped", {"reason": reason})

        self._logger.info(f"백테스팅 중단: {backtest_id} (이유: {reason})")
        return True

    def get_backtest_list(self, strategy_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """백테스트 목록 조회

        Args:
            strategy_id: 특정 전략의 백테스트만 조회 (None이면 전체)

        Returns:
            List[Dict[str, Any]]: 백테스트 메타데이터 목록
        """
        if strategy_id:
            return self._backtest_repository.find_by_strategy_id(StrategyId(strategy_id))
        else:
            return self._backtest_repository.find_all()

    def delete_backtest(self, backtest_id: str) -> bool:
        """백테스트 결과 삭제

        Args:
            backtest_id: 백테스트 ID

        Returns:
            bool: 삭제 성공 여부

        Raises:
            ValueError: 백테스트 없음
        """
        backtest = self._backtest_repository.find_by_id(backtest_id)
        if not backtest:
            raise ValueError(f"존재하지 않는 백테스트입니다: {backtest_id}")

        self._backtest_repository.delete(backtest_id)
        self._logger.info(f"백테스트 삭제 완료: {backtest_id}")
        return True
