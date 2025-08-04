"""
백테스팅 결과 Repository 인터페이스

strategies.sqlite3의 시뮬레이션 및 실행 기록 데이터에 대한
도메인 중심의 추상화된 접근을 제공합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
from dataclasses import dataclass
from enum import Enum

from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId


class BacktestStatus(Enum):
    """백테스팅 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class BacktestMetric(Enum):
    """백테스팅 성능 지표"""
    TOTAL_RETURN = "total_return"
    ANNUAL_RETURN = "annual_return"
    MAX_DRAWDOWN = "max_drawdown"
    SHARPE_RATIO = "sharpe_ratio"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    TOTAL_TRADES = "total_trades"


@dataclass
class BacktestResult:
    """
    백테스팅 결과 도메인 모델
    
    Note: 임시 dataclass 구현
    추후 완전한 도메인 엔티티로 리팩토링 예정
    """
    backtest_id: str
    strategy_id: StrategyId
    session_name: str
    symbol: str
    start_date: date
    end_date: date
    initial_capital: float
    final_capital: Optional[float]
    total_return: Optional[float]
    annual_return: Optional[float]
    max_drawdown: Optional[float]
    sharpe_ratio: Optional[float]
    win_rate: Optional[float]
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_holding_time: Optional[float]
    profit_factor: Optional[float]
    status: BacktestStatus
    execution_type: str  # 'backtest', 'paper_trading', 'live_trading'
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class BacktestTrade:
    """백테스팅 개별 거래 기록"""
    trade_id: str
    backtest_id: str
    symbol: str
    action_type: str  # 'buy', 'sell'
    quantity: float
    price: float
    total_amount: float
    commission: float
    trade_date: datetime
    profit_loss: float
    portfolio_value: Optional[float]
    notes: Optional[str] = None


@dataclass
class BacktestStatistics:
    """백테스팅 통계 정보"""
    strategy_id: StrategyId
    total_backtests: int
    completed_backtests: int
    failed_backtests: int
    avg_total_return: float
    best_total_return: float
    worst_total_return: float
    avg_sharpe_ratio: float
    avg_win_rate: float
    last_backtest_date: Optional[datetime]


class BacktestRepository(ABC):
    """
    백테스팅 결과 데이터 접근을 위한 Repository 인터페이스
    
    strategies.sqlite3의 simulation_sessions, simulation_trades,
    strategy_execution 테이블과 매핑됩니다.
    """

    # =====================================
    # 기본 CRUD 작업
    # =====================================

    @abstractmethod
    def save_backtest_result(self, result: BacktestResult) -> str:
        """
        백테스팅 결과 저장
        
        Args:
            result: 저장할 백테스팅 결과
            
        Returns:
            str: 저장된 백테스팅 결과의 ID
            
        Raises:
            RepositoryError: 저장 실패 시
        """
        pass

    @abstractmethod
    def find_backtest_by_id(self, backtest_id: str) -> Optional[BacktestResult]:
        """
        ID로 백테스팅 결과 조회
        
        Args:
            backtest_id: 백테스팅 결과 ID
            
        Returns:
            Optional[BacktestResult]: 백테스팅 결과 또는 None
        """
        pass

    @abstractmethod
    def update_backtest_result(self, result: BacktestResult) -> bool:
        """
        백테스팅 결과 업데이트
        
        Args:
            result: 업데이트할 백테스팅 결과
            
        Returns:
            bool: 업데이트 성공 여부
        """
        pass

    @abstractmethod
    def delete_backtest_result(self, backtest_id: str) -> bool:
        """
        백테스팅 결과 삭제
        
        Args:
            backtest_id: 삭제할 백테스팅 결과 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        pass

    @abstractmethod
    def exists_backtest(self, backtest_id: str) -> bool:
        """
        백테스팅 결과 존재 여부 확인
        
        Args:
            backtest_id: 확인할 백테스팅 결과 ID
            
        Returns:
            bool: 존재 여부
        """
        pass

    # =====================================
    # 전략별 조회
    # =====================================

    @abstractmethod
    def find_backtests_by_strategy_id(self, strategy_id: StrategyId) -> List[BacktestResult]:
        """
        전략별 백테스팅 결과 조회
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            List[BacktestResult]: 해당 전략의 백테스팅 결과 목록
        """
        pass

    @abstractmethod
    def find_completed_backtests_by_strategy(self, strategy_id: StrategyId) -> List[BacktestResult]:
        """
        전략별 완료된 백테스팅 결과만 조회
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            List[BacktestResult]: 완료된 백테스팅 결과 목록
        """
        pass

    @abstractmethod
    def find_latest_backtest_by_strategy(self, strategy_id: StrategyId) -> Optional[BacktestResult]:
        """
        전략의 최신 백테스팅 결과 조회
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            Optional[BacktestResult]: 최신 백테스팅 결과 또는 None
        """
        pass

    # =====================================
    # 기간별 조회
    # =====================================

    @abstractmethod
    def find_backtests_in_period(self, start_date: date, end_date: date) -> List[BacktestResult]:
        """
        기간별 백테스팅 결과 조회
        
        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜
            
        Returns:
            List[BacktestResult]: 해당 기간의 백테스팅 결과 목록
        """
        pass

    @abstractmethod
    def find_recent_backtests(self, limit: int = 10) -> List[BacktestResult]:
        """
        최근 백테스팅 결과 조회
        
        Args:
            limit: 조회할 결과 수 (기본값: 10)
            
        Returns:
            List[BacktestResult]: 최근 백테스팅 결과 목록
        """
        pass

    # =====================================
    # 성능 기반 조회
    # =====================================

    @abstractmethod
    def find_best_performing_strategies(self,
                                      metric: BacktestMetric = BacktestMetric.TOTAL_RETURN,
                                      limit: int = 10,
                                      min_trades: int = 10) -> List[BacktestResult]:
        """
        성과별 최고 전략 조회
        
        Args:
            metric: 성능 지표 (기본값: 총 수익률)
            limit: 조회할 결과 수 (기본값: 10)
            min_trades: 최소 거래 수 필터 (기본값: 10)
            
        Returns:
            List[BacktestResult]: 성과 기준 상위 백테스팅 결과 목록
        """
        pass

    @abstractmethod
    def find_backtests_by_return_range(self,
                                     min_return: float,
                                     max_return: float) -> List[BacktestResult]:
        """
        수익률 범위별 백테스팅 결과 조회
        
        Args:
            min_return: 최소 수익률 (예: -0.1 = -10%)
            max_return: 최대 수익률 (예: 0.2 = 20%)
            
        Returns:
            List[BacktestResult]: 해당 수익률 범위의 백테스팅 결과 목록
        """
        pass

    @abstractmethod
    def find_backtests_by_drawdown_limit(self, max_drawdown: float) -> List[BacktestResult]:
        """
        최대 손실폭 기준 백테스팅 결과 조회
        
        Args:
            max_drawdown: 최대 허용 손실폭 (예: 0.1 = 10%)
            
        Returns:
            List[BacktestResult]: 기준 이하 손실폭의 백테스팅 결과 목록
        """
        pass

    # =====================================
    # 거래 기록 관리
    # =====================================

    @abstractmethod
    def save_backtest_trades(self, trades: List[BacktestTrade]) -> bool:
        """
        백테스팅 거래 기록 일괄 저장
        
        Args:
            trades: 저장할 거래 기록 목록
            
        Returns:
            bool: 저장 성공 여부
        """
        pass

    @abstractmethod
    def find_trades_by_backtest_id(self, backtest_id: str) -> List[BacktestTrade]:
        """
        백테스팅별 거래 기록 조회
        
        Args:
            backtest_id: 백테스팅 결과 ID
            
        Returns:
            List[BacktestTrade]: 해당 백테스팅의 거래 기록 목록
        """
        pass

    @abstractmethod
    def delete_trades_by_backtest_id(self, backtest_id: str) -> bool:
        """
        백테스팅별 거래 기록 삭제
        
        Args:
            backtest_id: 삭제할 백테스팅 결과 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        pass

    # =====================================
    # 통계 및 분석
    # =====================================

    @abstractmethod
    def get_backtest_statistics(self, strategy_id: StrategyId) -> BacktestStatistics:
        """
        전략별 백테스팅 통계 정보 조회
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            BacktestStatistics: 백테스팅 통계 정보
        """
        pass

    @abstractmethod
    def get_strategy_performance_comparison(self,
                                          strategy_ids: List[StrategyId]) -> Dict[str, Any]:
        """
        전략별 성능 비교 데이터 조회
        
        Args:
            strategy_ids: 비교할 전략 ID 목록
            
        Returns:
            Dict[str, Any]: 전략별 성능 비교 데이터
        """
        pass

    @abstractmethod
    def get_monthly_performance_summary(self, strategy_id: StrategyId) -> Dict[str, float]:
        """
        전략별 월별 성과 요약
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            Dict[str, float]: 월별 성과 데이터 (YYYY-MM 형식 키)
        """
        pass

    # =====================================
    # 중복 검사 및 검증
    # =====================================

    @abstractmethod
    def check_duplicate_backtest(self,
                                strategy_id: StrategyId,
                                start_date: date,
                                end_date: date,
                                symbol: str) -> Optional[str]:
        """
        중복 백테스팅 검사
        
        Args:
            strategy_id: 전략 ID
            start_date: 시작 날짜
            end_date: 종료 날짜
            symbol: 심볼
            
        Returns:
            Optional[str]: 중복된 백테스팅 ID (없으면 None)
        """
        pass

    @abstractmethod
    def validate_backtest_data_integrity(self, backtest_id: str) -> Tuple[bool, List[str]]:
        """
        백테스팅 데이터 무결성 검증
        
        Args:
            backtest_id: 검증할 백테스팅 ID
            
        Returns:
            Tuple[bool, List[str]]: (무결성 여부, 오류 메시지 목록)
        """
        pass

    # =====================================
    # 배치 작업
    # =====================================

    @abstractmethod
    def save_multiple_backtests(self, results: List[BacktestResult]) -> List[str]:
        """
        백테스팅 결과 일괄 저장
        
        Args:
            results: 저장할 백테스팅 결과 목록
            
        Returns:
            List[str]: 저장된 백테스팅 결과 ID 목록
        """
        pass

    @abstractmethod
    def delete_backtests_by_strategy(self, strategy_id: StrategyId) -> int:
        """
        전략별 모든 백테스팅 결과 삭제
        
        Args:
            strategy_id: 삭제할 전략 ID
            
        Returns:
            int: 삭제된 백테스팅 결과 수
        """
        pass

    @abstractmethod
    def cleanup_old_backtests(self, days_to_keep: int = 90) -> int:
        """
        오래된 백테스팅 결과 정리
        
        Args:
            days_to_keep: 보관할 일수 (기본값: 90일)
            
        Returns:
            int: 삭제된 백테스팅 결과 수
        """
        pass

    # =====================================
    # 상태 관리
    # =====================================

    @abstractmethod
    def update_backtest_status(self, backtest_id: str, status: BacktestStatus) -> bool:
        """
        백테스팅 상태 업데이트
        
        Args:
            backtest_id: 백테스팅 ID
            status: 새로운 상태
            
        Returns:
            bool: 업데이트 성공 여부
        """
        pass

    @abstractmethod
    def find_running_backtests(self) -> List[BacktestResult]:
        """
        실행 중인 백테스팅 조회
        
        Returns:
            List[BacktestResult]: 실행 중인 백테스팅 목록
        """
        pass

    @abstractmethod
    def mark_backtest_completed(self,
                               backtest_id: str,
                               final_capital: float,
                               total_return: float,
                               performance_metrics: Dict[str, float]) -> bool:
        """
        백테스팅 완료 처리
        
        Args:
            backtest_id: 백테스팅 ID
            final_capital: 최종 자본
            total_return: 총 수익률
            performance_metrics: 성능 지표 딕셔너리
            
        Returns:
            bool: 처리 성공 여부
        """
        pass

    # =====================================
    # 메타데이터 및 설정
    # =====================================

    @abstractmethod
    def get_backtest_count_by_strategy(self, strategy_id: StrategyId) -> int:
        """
        전략별 백테스팅 실행 횟수 조회
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            int: 백테스팅 실행 횟수
        """
        pass

    @abstractmethod
    def get_total_backtest_count(self) -> int:
        """
        전체 백테스팅 실행 횟수 조회
        
        Returns:
            int: 전체 백테스팅 실행 횟수
        """
        pass

    @abstractmethod
    def get_backtest_symbols(self) -> List[str]:
        """
        백테스팅에 사용된 모든 심볼 조회
        
        Returns:
            List[str]: 심볼 목록
        """
        pass

    @abstractmethod
    def get_backtest_execution_types(self) -> List[str]:
        """
        백테스팅 실행 타입 목록 조회
        
        Returns:
            List[str]: 실행 타입 목록 ('backtest', 'paper_trading', 'live_trading')
        """
        pass
