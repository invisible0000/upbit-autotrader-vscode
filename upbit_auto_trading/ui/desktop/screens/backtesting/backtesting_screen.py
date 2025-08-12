"""
백테스팅 화면 메인 모듈
- 전략/포트폴리오 백테스트 실행
- 결과 분석 및 시각화
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal
from .components.backtest_setup import BacktestSetupWidget
from .components.backtest_results import BacktestResultsWidget
import logging
from typing import Dict, Any, List
import pandas as pd

logger = logging.getLogger(__name__)

class SimpleStrategyAdapter:
    """백테스트용 전략 어댑터 - StrategyInterface 요구사항 최소화"""
    
    def __init__(self, strategy_config):
        self.config = strategy_config
        self.parameters = getattr(strategy_config, 'parameters', {})
        self.name = getattr(strategy_config, 'name', 'Unknown Strategy')
        self.strategy_type = getattr(strategy_config, 'strategy_type', 'buy_and_hold')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """매매 신호 생성 - StrategyInterface 호환"""
        df = data.copy()
        df['signal'] = 0  # 기본값: 홀드
        
        if self.strategy_type == 'buy_and_hold':
            # Buy & Hold: 첫 번째 데이터에서만 매수
            if len(df) > 0:
                df.loc[df.index[0], 'signal'] = 1
        elif self.strategy_type == 'moving_average_cross':
            # 이동평균 교차 전략 구현
            short_period = self.parameters.get('short_period', 5)
            long_period = self.parameters.get('long_period', 20)
            
            df[f'MA_{short_period}'] = df['close'].rolling(window=short_period).mean()
            df[f'MA_{long_period}'] = df['close'].rolling(window=long_period).mean()
            
            # 골든크로스: 매수, 데드크로스: 매도
            for i in range(1, len(df)):
                idx = df.index[i]
                prev_idx = df.index[i-1]
                
                if (df.loc[prev_idx, f'MA_{short_period}'] <= df.loc[prev_idx, f'MA_{long_period}'] and
                    df.loc[idx, f'MA_{short_period}'] > df.loc[idx, f'MA_{long_period}']):
                    df.loc[idx, 'signal'] = 1  # 매수
                elif (df.loc[prev_idx, f'MA_{short_period}'] >= df.loc[prev_idx, f'MA_{long_period}'] and
                      df.loc[idx, f'MA_{short_period}'] < df.loc[idx, f'MA_{long_period}']):
                    df.loc[idx, 'signal'] = -1  # 매도
        
        return df
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """필요한 기술적 지표"""
        if self.strategy_type == 'moving_average_cross':
            short_period = self.parameters.get('short_period', 5)
            long_period = self.parameters.get('long_period', 20)
            return [
                {"name": "SMA", "params": {"window": short_period, "column": "close"}},
                {"name": "SMA", "params": {"window": long_period, "column": "close"}}
            ]
        return []
    
    # StrategyInterface 요구사항 최소 구현
    def get_parameters(self) -> Dict[str, Any]:
        return self.parameters
    
    def set_parameters(self, parameters: Dict[str, Any]) -> bool:
        self.parameters = parameters
        return True
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return True
    
    def get_strategy_info(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.strategy_type,
            'description': f'{self.name} 전략'
        }
    
    def get_default_parameters(self) -> Dict[str, Any]:
        if self.strategy_type == 'moving_average_cross':
            return {'short_period': 5, 'long_period': 20}
        return {}

class BacktestThread(QThread):
    """백테스트 실행 스레드"""
    
    backtest_completed = pyqtSignal(dict)  # 백테스트 결과
    backtest_failed = pyqtSignal(str)      # 오류 메시지
    
    def __init__(self, config):
        super().__init__()
        self.config = config
    
    def _create_strategy_from_id(self, strategy_id: str):
        """전략 ID로부터 전략 객체 생성"""
        from upbit_auto_trading.business_logic.strategy.trading_strategies import StrategyConfig
        from upbit_auto_trading.business_logic.strategy.basic_strategies import (
            MovingAverageCrossStrategy, BollingerBandsStrategy, RSIStrategy
        )
        
        if strategy_id == 'buy_and_hold':
            strategy_config = StrategyConfig(
                strategy_id="buy_and_hold",
                name="단순 매수 보유",
                strategy_type="buy_and_hold",
                parameters={}
            )
        elif strategy_id == 'ma_cross_5_20':
            strategy_config = StrategyConfig(
                strategy_id="ma_cross_5_20",
                name="이동평균 교차 (5, 20)",
                strategy_type="moving_average_cross",
                parameters={'short_period': 5, 'long_period': 20}
            )
        elif strategy_id == 'ma_cross_10_30':
            strategy_config = StrategyConfig(
                strategy_id="ma_cross_10_30",
                name="이동평균 교차 (10, 30)",
                strategy_type="moving_average_cross",
                parameters={'short_period': 10, 'long_period': 30}
            )
        elif strategy_id == 'ma_cross_20_50':
            strategy_config = StrategyConfig(
                strategy_id="ma_cross_20_50",
                name="이동평균 교차 (20, 50)",
                strategy_type="moving_average_cross",
                parameters={'short_period': 20, 'long_period': 50}
            )
        elif strategy_id == 'bollinger_bands':
            # 볼린저 밴드 전략 - 실제 전략 클래스 사용
            return BollingerBandsStrategy({
                'window': 20,
                'num_std': 2.0,
                'column': 'close'
            })
        elif strategy_id == 'rsi_strategy':
            # RSI 전략 - 실제 전략 클래스 사용
            return RSIStrategy({
                'window': 14,
                'oversold': 30,
                'overbought': 70,
                'column': 'close'
            })
        elif strategy_id == 'volatility_breakout':
            # 변동성 돌파 전략
            strategy_config = StrategyConfig(
                strategy_id="volatility_breakout",
                name="변동성 돌파 전략",
                strategy_type="volatility_breakout",
                parameters={'k': 0.5, 'period': 20}
            )
        else:
            # 기본값
            strategy_config = StrategyConfig(
                strategy_id="buy_and_hold",
                name="단순 매수 보유",
                strategy_type="buy_and_hold",
                parameters={}
            )
        
        return SimpleStrategyAdapter(strategy_config)
        self.config = config
    
    def run(self):
        """백테스트 실행"""
        try:
            import sys
            import os
            from datetime import datetime
            
            # 프로젝트 루트 경로 추가
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
            sys.path.insert(0, project_root)
            
            from upbit_auto_trading.business_logic.backtester.backtest_runner import BacktestRunner
            from upbit_auto_trading.business_logic.strategy.trading_strategies import StrategyManager
            from upbit_auto_trading.data_layer.storage.database_manager import DatabaseManager
            
            logger.info(f"백테스트 시작: {self.config}")
            
            # 데이터베이스 세션 생성
            db_manager = DatabaseManager()
            
            # 전략 처리 - strategy_id 기준으로 전략 선택
            strategy_id = self.config.get('strategy_id', 'buy_and_hold')
            
            # 실제 전략 객체 생성
            strategy = self._create_strategy_from_id(strategy_id)
            if not strategy:
                raise Exception(f"지원되지 않는 전략입니다: {strategy_id}")
            
            # 백테스트 설정 변환
            backtest_config = {
                "symbol": self.config['coin'],
                "timeframe": self.config['timeframes'][0] if self.config['timeframes'] else "1d",
                "start_date": datetime.strptime(self.config['start_date'], '%Y-%m-%d'),
                "end_date": datetime.strptime(self.config['end_date'], '%Y-%m-%d'),
                "initial_capital": self.config['initial_capital'],
                "fee_rate": self.config['trading_fee'] / 100.0,
                "slippage": self.config.get('slippage', 0.02) / 100.0  # 슬리피지 추가 (기본값 0.02%)
            }
            
            # 백테스트 실행
            backtest_runner = BacktestRunner(strategy, backtest_config)  # type: ignore
            result = backtest_runner.execute_backtest()
            
            logger.info("백테스트 완료")
            self.backtest_completed.emit(result)
            
        except Exception as e:
            logger.error(f"백테스트 실행 실패: {e}")
            import traceback
            traceback.print_exc()
            self.backtest_failed.emit(str(e))

class BacktestingScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("백테스팅")
        self.backtest_thread = None
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        # 전체를 감싸는 수평 레이아웃 (좌우 2분할)
        layout = QHBoxLayout(self)
        
        # 1. 왼쪽: 백테스트 설정 패널 (비율 조정)
        self.setup_panel = BacktestSetupWidget(self)
        layout.addWidget(self.setup_panel, stretch=2)  # 좌측 패널 비율 증가 (1 → 2)
        
        # 2. 오른쪽: 백테스트 결과 패널 (비율 유지)
        self.results_panel = BacktestResultsWidget(self)
        layout.addWidget(self.results_panel, stretch=3)  # 우측 패널 비율 유지
        
        # 시그널/슬롯 연결
        self.setup_panel.backtest_started.connect(self.start_backtest)
    
    def start_backtest(self, config):
        """백테스트 실행"""
        try:
            logger.info(f"백테스트 시작 요청: {config}")
            
            # 선택된 전략 ID 추가
            strategy_id = self.setup_panel.get_selected_strategy_id()
            config['strategy_id'] = strategy_id
            
            # 이전 결과 초기화
            self.results_panel.clear_results()
            self.results_panel.show_loading(True)
            
            # 백테스트 스레드 시작
            self.backtest_thread = BacktestThread(config)
            self.backtest_thread.backtest_completed.connect(self.on_backtest_completed)
            self.backtest_thread.backtest_failed.connect(self.on_backtest_failed)
            self.backtest_thread.start()
            
        except Exception as e:
            logger.error(f"백테스트 시작 실패: {e}")
            QMessageBox.critical(self, "오류", f"백테스트를 시작할 수 없습니다: {e}")
            self.results_panel.show_loading(False)
    
    def on_backtest_completed(self, result):
        """백테스트 완료 처리"""
        try:
            logger.info("백테스트 결과 수신")
            self.results_panel.show_loading(False)
            self.results_panel.update_results(result)
            
        except Exception as e:
            logger.error(f"백테스트 결과 처리 실패: {e}")
            QMessageBox.critical(self, "오류", f"백테스트 결과를 표시할 수 없습니다: {e}")
    
    def on_backtest_failed(self, error_message):
        """백테스트 실패 처리"""
        logger.error(f"백테스트 실패: {error_message}")
        self.results_panel.show_loading(False)
        QMessageBox.critical(self, "백테스트 실패", f"백테스트 실행 중 오류가 발생했습니다:\n\n{error_message}")
    
    def closeEvent(self, a0):
        """창 종료 시 스레드 정리"""
        if self.backtest_thread and self.backtest_thread.isRunning():
            self.backtest_thread.terminate()
            self.backtest_thread.wait()
        if a0:
            a0.accept()
