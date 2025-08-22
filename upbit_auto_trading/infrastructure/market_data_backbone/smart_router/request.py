# d:\projects\upbit-autotrader-vscode\upbit_auto_trading\infrastructure\market_data_backbone\smart_router\request.py

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class MarketDataRequest:
    """
    스마트 라우터의 입력으로 사용되는 시장 데이터 요청을 나타냅니다.
    """
    data_type: str  # 예: 'ticker', 'candle', 'orderbook', 'account_info'
    symbols: List[str] = field(default_factory=list) # 예: ['KRW-BTC', 'KRW-ETH']
    interval: Optional[str] = None # 캔들용, 예: '1m', '1h', '1d'
    count: Optional[int] = None # 검색할 데이터 포인트 수
    realtime: bool = False # 실시간 스트리밍 여부 (True: 실시간, False: 과거/스냅샷)
    options: Dict[str, Any] = field(default_factory=dict) # 추가적인 요청별 옵션

    def __post_init__(self):
        if not self.data_type:
            raise ValueError("data_type은 비워둘 수 없습니다.")
        if self.realtime and not self.symbols:
            # 실시간 요청은 일반적으로 특정 심볼을 필요로 합니다.
            # 이는 업비트의 실제 웹소켓 API에 따라 조정될 수 있습니다.
            pass # 필요한 경우 일반적인 실시간 스트림에 대해 빈 심볼을 허용합니다.

    def __hash__(self):
        # 캐싱 및 메트릭을 위한 해싱. 주어진 요청에 대해 고유해야 합니다.
        # 딕셔너리를 해싱을 위해 항목 튜플로 변환합니다.
        options_tuple = tuple(sorted(self.options.items()))
        return hash((self.data_type, tuple(sorted(self.symbols)), self.interval, self.count, self.realtime, options_tuple))

    def __eq__(self, other):
        if not isinstance(other, MarketDataRequest):
            return NotImplemented
        return (
            self.data_type == other.data_type and
            set(self.symbols) == set(other.symbols) and # 심볼의 순서는 동등성에 중요하지 않습니다.
            self.interval == other.interval and
            self.count == other.count and
            self.realtime == other.realtime and
            self.options == other.options
        )
