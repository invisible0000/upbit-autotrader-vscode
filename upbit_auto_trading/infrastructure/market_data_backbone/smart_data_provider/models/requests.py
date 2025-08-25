"""
요청 모델 정의 - Dict 형식 통일 V3.0
Smart Data Provider의 요청 구조를 정의합니다.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from .priority import Priority


@dataclass
class DataRequest:
    """
    데이터 요청 - Dict 기반 통일

    external_apis와 smart_routing과 완전히 호환되는 Dict 기반 요청 형식
    모든 요청 파라미터는 Dict[str, Any] 형태로 통일하여 일관성 보장
    """
    request_type: str  # "candles", "ticker", "orderbook", "trades", "markets"
    symbols: Union[str, List[str]]  # 단일/다중 심볼 지원
    priority: Priority = Priority.NORMAL
    params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """요청 생성 후 초기화 및 유효성 검증"""
        # 심볼 정규화 (항상 리스트로 변환)
        if isinstance(self.symbols, str):
            self.symbols = [self.symbols]

        # 메타데이터 설정
        self.metadata.update({
            'created_at': datetime.now().isoformat(),
            'request_id': f"{self.request_type}_{hash(str(self.symbols))}_{int(datetime.now().timestamp())}"
        })

        # 요청 타입별 유효성 검증
        self._validate_request()

    def _validate_request(self):
        """요청 유효성 검증"""
        if self.request_type == "candles":
            if not self.params.get('timeframe'):
                raise ValueError("캔들 요청시 timeframe은 필수입니다")

        if self.request_type in ["tickers"] and not self.symbols:
            raise ValueError("다중 티커 요청시 symbols는 필수입니다")

    def get_single_symbol(self) -> str:
        """단일 심볼 반환 (첫 번째 심볼)"""
        return self.symbols[0] if self.symbols else ""

    def get_symbols(self) -> List[str]:
        """심볼 리스트 반환"""
        if isinstance(self.symbols, str):
            return [self.symbols]
        return self.symbols

    def is_multi_symbol(self) -> bool:
        """다중 심볼 요청 여부"""
        return len(self.symbols) > 1

    def get_param(self, key: str, default: Any = None) -> Any:
        """파라미터 값 조회"""
        return self.params.get(key, default)

    def set_param(self, key: str, value: Any) -> None:
        """파라미터 값 설정"""
        self.params[key] = value

    def get_timeframe(self) -> Optional[str]:
        """타임프레임 반환 (캔들 요청용)"""
        return self.params.get('timeframe')

    def get_count(self) -> Optional[int]:
        """개수 반환"""
        return self.params.get('count')

    def get_start_time(self) -> Optional[str]:
        """시작 시간 반환"""
        return self.params.get('start_time')

    def get_end_time(self) -> Optional[str]:
        """종료 시간 반환"""
        return self.params.get('end_time')

    def to_dict(self) -> Dict[str, Any]:
        """Dict 형태로 변환"""
        return {
            'request_type': self.request_type,
            'symbols': self.symbols,
            'priority': self.priority.value,
            'params': self.params,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataRequest':
        """Dict에서 요청 객체 생성"""
        priority = Priority(data.get('priority', Priority.NORMAL.value))
        return cls(
            request_type=data['request_type'],
            symbols=data['symbols'],
            priority=priority,
            params=data.get('params', {}),
            metadata=data.get('metadata', {})
        )

    @classmethod
    def create_candles_request(cls, symbol: str, timeframe: str,
                               count: Optional[int] = None,
                               start_time: Optional[str] = None,
                               end_time: Optional[str] = None,
                               priority: Priority = Priority.NORMAL) -> 'DataRequest':
        """캔들 요청 생성 헬퍼"""
        params: Dict[str, Any] = {'timeframe': timeframe}
        if count is not None:
            params['count'] = count
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time

        return cls(
            request_type="candles",
            symbols=symbol,
            priority=priority,
            params=params
        )

    @classmethod
    def create_ticker_request(cls, symbols: Union[str, List[str]],
                              priority: Priority = Priority.HIGH) -> 'DataRequest':
        """티커 요청 생성 헬퍼"""
        return cls(
            request_type="ticker",
            symbols=symbols,
            priority=priority
        )

    @classmethod
    def create_orderbook_request(cls, symbol: str,
                                 priority: Priority = Priority.HIGH) -> 'DataRequest':
        """호가 요청 생성 헬퍼"""
        return cls(
            request_type="orderbook",
            symbols=symbol,
            priority=priority
        )

    @classmethod
    def create_trades_request(cls, symbol: str, count: int = 100,
                              priority: Priority = Priority.NORMAL) -> 'DataRequest':
        """체결 요청 생성 헬퍼"""
        return cls(
            request_type="trades",
            symbols=symbol,
            priority=priority,
            params={'count': count}
        )

    @classmethod
    def create_markets_request(cls, is_details: bool = False,
                               priority: Priority = Priority.NORMAL) -> 'DataRequest':
        """마켓 목록 요청 생성 헬퍼"""
        return cls(
            request_type="markets",
            symbols=[],  # 마켓 목록은 심볼 불필요
            priority=priority,
            params={'is_details': is_details}
        )
