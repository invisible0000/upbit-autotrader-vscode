"""
Business Logic 호환성 어댑터

기존 business_logic 계층과 새로운 Domain Service 간의 브릿지
기존 DataFrame 기반 시스템을 Domain 기반 시스템으로 점진적 마이그레이션
"""

from typing import List, Dict, Any, Optional, Callable
import pandas as pd
from datetime import datetime

from upbit_auto_trading.domain.services.trigger_evaluation_service import (
    TriggerEvaluationService, MarketData, EvaluationResult
)
from upbit_auto_trading.domain.entities.trigger import Trigger

class BusinessLogicAdapter:
    """
    기존 business_logic과 Domain Service 간 어댑터
    
    책임:
    - DataFrame을 MarketData로 변환
    - Domain Service 결과를 기존 형식으로 변환
    - 기존 StrategyInterface와 호환성 유지
    - 점진적 마이그레이션 지원
    """
    
    def __init__(self):
        self.trigger_evaluation_service = TriggerEvaluationService()
    
    def convert_dataframe_to_market_data(self, df: pd.DataFrame,
                                         symbol: str = "KRW-BTC",
                                         indicators: Optional[Dict[str, Any]] = None) -> MarketData:
        """
        pandas DataFrame을 MarketData Value Object로 변환
        
        기존 business_logic에서 사용하는 DataFrame 형식:
        - columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        - 추가 지표 컬럼들 (RSI, SMA, EMA 등)
        """
        if df.empty:
            raise ValueError("DataFrame이 비어있습니다")
        
        # 최신 데이터 행 사용 (기존 시스템은 마지막 행 기준 신호 생성)
        latest_row = df.iloc[-1]
        
        # 기본 OHLCV 데이터 추출
        market_data = MarketData(
            symbol=symbol,
            timestamp=self._extract_timestamp(latest_row, df),
            open_price=float(latest_row.get('open', latest_row.get('Open', 0))),
            high_price=float(latest_row.get('high', latest_row.get('High', 0))),
            low_price=float(latest_row.get('low', latest_row.get('Low', 0))),
            close_price=float(latest_row.get('close', latest_row.get('Close', 0))),
            volume=float(latest_row.get('volume', latest_row.get('Volume', 0))),
            indicators=self._extract_indicators(latest_row, indicators or {}),
            metadata={
                "source": "business_logic_adapter",
                "dataframe_length": len(df),
                "original_columns": list(df.columns)
            }
        )
        
        return market_data
    
    def evaluate_triggers_from_dataframe(self, triggers: List[Trigger],
                                         df: pd.DataFrame,
                                         symbol: str = "KRW-BTC",
                                         additional_indicators: Optional[Dict[str, Any]] = None) -> List[EvaluationResult]:
        """
        DataFrame 기반 트리거 평가 (기존 시스템 호환)
        
        기존 StrategyInterface.generate_signals() 대체 메서드
        """
        try:
            # DataFrame을 MarketData로 변환
            market_data = self.convert_dataframe_to_market_data(
                df, symbol, additional_indicators
            )
            
            # Domain Service로 평가 수행
            results = self.trigger_evaluation_service.evaluate_multiple_triggers(
                triggers, market_data
            )
            
            return results
            
        except Exception as e:
            # 기존 시스템과의 호환성을 위한 에러 처리
            error_result = EvaluationResult.create_error(
                trigger_id="adapter_error",
                error_message=f"DataFrame 평가 중 오류: {str(e)}",
                timestamp=datetime.now()
            )
            return [error_result]
    
    def convert_results_to_legacy_format(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """
        Domain Service 결과를 기존 business_logic 형식으로 변환
        
        기존 시스템에서 기대하는 반환 형식:
        {
            'signal': 'BUY' | 'SELL' | 'HOLD',
            'confidence': float,
            'details': {...}
        }
        """
        # 성공한 결과만 필터링
        successful_results = [r for r in results if r.status.value == "success"]
        
        if not successful_results:
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'details': {
                    'message': '평가 가능한 트리거가 없습니다',
                    'total_triggers': len(results),
                    'successful_evaluations': 0
                }
            }
        
        # 신호 통합 로직 (기존 시스템 방식)
        true_results = [r for r in successful_results if r.result]
        confidence = len(true_results) / len(successful_results) if successful_results else 0.0
        
        # 신호 결정 (기존 시스템 로직과 호환)
        if confidence >= 0.7:  # 70% 이상 조건 만족
            signal = 'BUY'
        elif confidence <= 0.3:  # 30% 이하 조건 만족
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        return {
            'signal': signal,
            'confidence': confidence,
            'details': {
                'total_triggers': len(results),
                'successful_evaluations': len(successful_results),
                'true_conditions': len(true_results),
                'timestamp': successful_results[0].timestamp.isoformat(),
                'trigger_results': [
                    {
                        'trigger_id': r.trigger_id,
                        'result': r.result,
                        'message': r.message,
                        'current_value': r.current_value,
                        'target_value': r.target_value
                    }
                    for r in successful_results
                ]
            }
        }
    
    def _extract_timestamp(self, row: pd.Series, df: pd.DataFrame) -> datetime:
        """DataFrame에서 타임스탬프 추출"""
        # 다양한 타임스탬프 컬럼명 시도
        timestamp_columns = ['timestamp', 'time', 'datetime', 'date']
        
        for col in timestamp_columns:
            if col in row.index:
                timestamp_value = row[col]
                if pd.isna(timestamp_value):
                    continue
                    
                if isinstance(timestamp_value, datetime):
                    return timestamp_value
                elif isinstance(timestamp_value, pd.Timestamp):
                    return timestamp_value.to_pydatetime()
                else:
                    try:
                        return pd.to_datetime(timestamp_value).to_pydatetime()
                    except:
                        continue
        
        # 인덱스가 타임스탬프인 경우
        if hasattr(df.index, 'to_pydatetime'):
            return df.index[-1].to_pydatetime()
        
        # 기본값: 현재 시간
        return datetime.now()
    
    def _extract_indicators(self, row: pd.Series,
                            additional_indicators: Dict[str, Any]) -> Dict[str, float]:
        """DataFrame 행에서 지표 데이터 추출"""
        indicators = {}
        
        # DataFrame 컬럼에서 지표 추출
        for column in row.index:
            value = row[column]
            
            # 숫자 데이터만 지표로 간주
            if pd.isna(value) or not isinstance(value, (int, float)):
                continue
            
            # 기본 OHLCV 제외
            if column.lower() in ['open', 'high', 'low', 'close', 'volume', 
                                'timestamp', 'time', 'datetime', 'date']:
                continue
            
            indicators[column] = float(value)
        
        # 추가 지표 병합
        for key, value in additional_indicators.items():
            if isinstance(value, (int, float)) and not pd.isna(value):
                indicators[key] = float(value)
        
        return indicators

class LegacyStrategyBridge:
    """
    기존 전략 클래스와 새로운 Domain Service 간 브릿지
    
    기존 코드 수정 최소화하면서 Domain Service 활용
    """
    
    def __init__(self, triggers: List[Trigger]):
        self.triggers = triggers
        self.adapter = BusinessLogicAdapter()
    
    def generate_signals(self, data: pd.DataFrame) -> str:
        """
        기존 StrategyInterface.generate_signals() 호환 메서드
        
        반환값: 'BUY' | 'SELL' | 'HOLD'
        """
        try:
            results = self.adapter.evaluate_triggers_from_dataframe(
                self.triggers, data
            )
            
            legacy_result = self.adapter.convert_results_to_legacy_format(results)
            return legacy_result['signal']
            
        except Exception as e:
            # 기존 시스템 안정성 보장
            print(f"⚠️ 신호 생성 중 오류: {e}")
            return 'HOLD'
    
    def get_detailed_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        상세 분석 결과 제공 (기존 시스템 확장)
        
        기존 코드에서 필요 시 호출 가능한 확장 메서드
        """
        results = self.adapter.evaluate_triggers_from_dataframe(
            self.triggers, data
        )
        
        return self.adapter.convert_results_to_legacy_format(results)

# 기존 코드와의 호환성을 위한 팩토리 함수
def create_legacy_strategy_from_triggers(triggers: List[Trigger]) -> LegacyStrategyBridge:
    """
    트리거 목록으로부터 기존 전략 호환 객체 생성
    
    기존 코드에서 사용 예시:
    ```python
    strategy = create_legacy_strategy_from_triggers(my_triggers)
    signal = strategy.generate_signals(market_dataframe)
    ```
    """
    return LegacyStrategyBridge(triggers)

def migrate_dataframe_strategy_to_domain(df_strategy_func: Callable,
                                        triggers: List[Trigger]) -> Callable:
    """
    기존 DataFrame 기반 전략 함수를 Domain Service 기반으로 마이그레이션
    
    데코레이터 패턴으로 기존 함수 래핑
    """
    def migrated_strategy(data: pd.DataFrame) -> str:
        bridge = LegacyStrategyBridge(triggers)
        
        # 새로운 Domain Service 시도
        try:
            return bridge.generate_signals(data)
        except Exception:
            # 실패 시 기존 함수로 폴백
            return df_strategy_func(data)
    
    return migrated_strategy
