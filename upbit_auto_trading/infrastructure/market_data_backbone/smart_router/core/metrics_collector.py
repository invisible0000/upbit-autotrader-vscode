# d:\projects\upbit-autotrader-vscode\upbit_auto_trading\infrastructure\market_data_backbone\smart_router\core\metrics_collector.py

from collections import defaultdict
import time
from typing import Dict, Any, Tuple

class MetricsCollector:
    """
    시장 데이터 요청 빈도에 대한 메트릭을 수집하고 제공합니다.
    AdaptiveRoutingEngine이 정보에 입각한 결정을 내리는 데 사용됩니다.
    """
    def __init__(self, retention_period_seconds: int = 3600):
        # 각 요청 유형에 대한 (타임스탬프, 카운트)를 저장합니다.
        self._request_history: Dict[str, list[Tuple[float, int]]] = defaultdict(list)
        self.retention_period_seconds = retention_period_seconds

    def record_request(self, request_key: str, count: int = 1):
        """
        주어진 키에 대한 요청을 기록합니다.
        request_key는 요청되는 데이터 유형을 고유하게 식별해야 합니다.
        (예: "ticker/KRW-BTC", "candle/KRW-ETH/1m").
        """
        current_time = time.time()
        self._request_history[request_key].append((current_time, count))
        self._clean_old_metrics(request_key)

    def get_frequency(self, request_key: str) -> float:
        """
        보존 기간 내에서 주어진 키에 대한 평균 빈도(초당 요청 수)를 계산합니다.
        """
        self._clean_old_metrics(request_key)
        history = self._request_history[request_key]
        if not history:
            return 0.0

        total_requests = sum(count for _, count in history)

        # 보존 기간 내에서 가장 오래된 기록과 가장 최신 기록을 기반으로 시간 창을 계산합니다.
        min_time = float('inf')
        max_time = float('-inf')
        for t, _ in history:
            min_time = min(min_time, t)
            max_time = max(max_time, t)

        time_window = max_time - min_time
        if time_window <= 0: # 모든 요청이 동일한 타임스탬프에 있는 경우 처리
            return total_requests # 또는 다른 적절한 값, 예를 들어 요청이 하나뿐인 경우 0

        return total_requests / time_window

    def _clean_old_metrics(self, request_key: str):
        """
        특정 키에 대해 보존 기간을 벗어난 오래된 메트릭을 제거합니다.
        """
        current_time = time.time()
        self._request_history[request_key] = [
            (t, count) for t, count in self._request_history[request_key]
            if current_time - t <= self.retention_period_seconds
        ]

    def get_all_frequencies(self) -> Dict[str, float]:
        """
        추적되는 모든 요청 키에 대한 빈도를 반환합니다.
        """
        frequencies = {}
        for key in list(self._request_history.keys()): # 키의 복사본을 반복합니다.
            self._clean_old_metrics(key)
            if self._request_history[key]: # 데이터가 남아있는 경우에만 포함합니다.
                frequencies[key] = self.get_frequency(key)
        return frequencies
