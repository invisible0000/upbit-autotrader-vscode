"""
패턴 분석기 - 요청 간격 분석 및 패턴 추적

기능:
1. 요청 간격 추세 분석 (가속/감속/안정)
2. 빈도 예측 (고빈도/중빈도/저빈도)
3. 심볼별 요청 패턴 추적
4. 비활성 심볼 자동 정리
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

from upbit_auto_trading.infrastructure.logging import create_component_logger


class IntervalAnalyzer:
    """요청 간격 분석기 (패턴 학습)"""

    def __init__(self, max_history: int = 20):
        self.max_history = max_history

    def analyze_trend(self, intervals: List[float]) -> str:
        """간격 추세 분석 (가속/감속/안정)"""
        if len(intervals) < 6:
            return "insufficient_data"

        # 최근 3개와 이전 3개 비교
        recent_avg = sum(intervals[-3:]) / 3
        previous_avg = sum(intervals[-6:-3]) / 3

        if recent_avg < previous_avg * 0.7:
            return "accelerating"  # 고빈도화 (간격 줄어듦)
        elif recent_avg > previous_avg * 1.3:
            return "decelerating"  # 저빈도화 (간격 늘어남)
        else:
            return "stable"

    def predict_frequency(self, intervals: List[float]) -> str:
        """다음 요청 빈도 예측"""
        if not intervals:
            return "unknown"

        current_freq = 1.0 / intervals[-1] if intervals[-1] > 0 else 0
        trend = self.analyze_trend(intervals)

        # 예측 로직
        if trend == "accelerating" or current_freq > 0.5:  # 2초 이하 간격
            return "high"
        elif trend == "decelerating" or current_freq < 0.1:  # 10초 이상 간격
            return "low"
        else:
            return "medium"


class RequestPatternTracker:
    """요청 패턴 추적기 (심볼별 히스토리)"""

    def __init__(self):
        self.symbol_patterns = defaultdict(lambda: {
            "intervals": [],
            "last_request": None,
            "request_count": 0,
            "url_history": []
        })
        self.analyzer = IntervalAnalyzer()
        self._logger = create_component_logger("RequestPatternTracker")

    def record_request(self, symbol: str, url: str) -> None:
        """요청 기록 및 패턴 업데이트"""
        pattern = self.symbol_patterns[symbol]
        now = datetime.now()

        # 간격 계산
        if pattern["last_request"]:
            interval = (now - pattern["last_request"]).total_seconds()
            pattern["intervals"].append(interval)

            # 최대 20개만 유지
            if len(pattern["intervals"]) > 20:
                pattern["intervals"].pop(0)

        pattern["last_request"] = now
        pattern["request_count"] += 1
        pattern["url_history"].append(url)

        # URL 히스토리도 20개만 유지
        if len(pattern["url_history"]) > 20:
            pattern["url_history"].pop(0)

    def get_frequency_prediction(self, symbol: str) -> str:
        """빈도 예측"""
        pattern = self.symbol_patterns.get(symbol)
        if not pattern or not pattern["intervals"]:
            return "unknown"

        return self.analyzer.predict_frequency(pattern["intervals"])

    def get_pattern_stats(self, symbol: str) -> Dict[str, Any]:
        """패턴 통계 정보"""
        pattern = self.symbol_patterns.get(symbol, {})

        # 데이터 유효성 검증
        intervals_data = pattern.get("intervals", [])
        if not pattern or not intervals_data or not isinstance(intervals_data, list):
            return {
                "status": "no_data",
                "request_count": pattern.get("request_count", 0),
                "frequency_category": "알 수 없음"
            }

        # 타입 안전성을 위한 명시적 캐스팅
        intervals: List[float] = intervals_data
        if not intervals:
            return {
                "status": "no_data",
                "request_count": pattern.get("request_count", 0),
                "frequency_category": "알 수 없음"
            }

        avg_interval = sum(intervals) / len(intervals)

        return {
            "request_count": pattern.get("request_count", 0),
            "avg_interval": avg_interval,
            "frequency_category": "고빈도" if avg_interval < 2.0 else "중빈도" if avg_interval < 10.0 else "저빈도",
            "trend": self.analyzer.analyze_trend(intervals),
            "prediction": self.get_frequency_prediction(symbol),
            "last_intervals": intervals[-5:] if len(intervals) >= 5 else intervals
        }

    def cleanup_inactive(self, inactive_hours: int = 1) -> int:
        """비활성 심볼 정리"""
        cutoff = datetime.now() - timedelta(hours=inactive_hours)

        inactive_symbols = []
        for symbol, pattern in self.symbol_patterns.items():
            last_request = pattern.get("last_request")
            if last_request and isinstance(last_request, datetime) and last_request < cutoff:
                inactive_symbols.append(symbol)

        for symbol in inactive_symbols:
            del self.symbol_patterns[symbol]

        if inactive_symbols:
            self._logger.info(f"비활성 심볼 {len(inactive_symbols)}개 정리: {inactive_symbols}")

        return len(inactive_symbols)

    def get_all_patterns(self) -> Dict[str, Dict[str, Any]]:
        """모든 패턴 정보 반환"""
        return {
            symbol: self.get_pattern_stats(symbol)
            for symbol in self.symbol_patterns.keys()
        }
