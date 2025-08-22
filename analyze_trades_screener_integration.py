"""
체결 데이터의 스크리너 활용 가능성 분석 보고서

Smart Data Provider에 체결 데이터 기능 구현 시
Asset Screener에서 활용할 수 있는 핵심 지표들을 분석합니다.
"""
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


@dataclass
class TradeData:
    """체결 데이터 구조"""
    trade_date_utc: str        # 체결 시각 (UTC)
    trade_time_utc: str        # 체결 시각 (UTC)
    timestamp: int             # 체결 타임스탬프
    trade_price: float         # 체결 가격
    trade_volume: float        # 체결 양
    prev_closing_price: float  # 전일 종가
    change_price: float        # 변화액
    ask_bid: str              # 매수/매도 구분 (ASK: 매도, BID: 매수)
    sequential_id: int         # 체결 번호


class TradeAnalyzer:
    """체결 데이터 분석기 - 스크리너용 지표 계산"""

    def __init__(self):
        self.analysis_window = timedelta(minutes=5)  # 5분 분석 윈도우

    def analyze_trade_momentum(self, trades: List[TradeData]) -> Dict[str, Any]:
        """
        체결 모멘텀 분석 - 스크리너 핵심 지표

        Returns:
            거래량 급증, 대량 거래, 가격 모멘텀 등 스크리너용 지표
        """
        if not trades:
            return self._empty_analysis()

        recent_trades = self._filter_recent_trades(trades)

        return {
            # 1. 거래량 분석
            "volume_metrics": self._analyze_volume_patterns(recent_trades),

            # 2. 가격 모멘텀 분석
            "price_momentum": self._analyze_price_momentum(recent_trades),

            # 3. 매수/매도 세력 분석
            "order_flow": self._analyze_order_flow(recent_trades),

            # 4. 대량 거래 감지
            "whale_activities": self._detect_whale_trades(recent_trades),

            # 5. 시장 참여도
            "market_participation": self._analyze_market_participation(recent_trades)
        }

    def _filter_recent_trades(self, trades: List[TradeData]) -> List[TradeData]:
        """최근 5분 내 체결 데이터만 필터링"""
        cutoff_time = time.time() - self.analysis_window.total_seconds()
        return [trade for trade in trades if trade.timestamp >= cutoff_time]

    def _analyze_volume_patterns(self, trades: List[TradeData]) -> Dict[str, Any]:
        """거래량 패턴 분석 - 스크리너 핵심 활용"""
        if not trades:
            return {"surge_detected": False, "volume_score": 0}

        total_volume = sum(trade.trade_volume for trade in trades)
        avg_trade_size = total_volume / len(trades) if trades else 0

        # 거래량 급증 감지 (임계값 기반)
        volume_surge = total_volume > 1000000  # 예: 100만 코인 이상

        # 거래 빈도 분석
        trade_frequency = len(trades) / 5  # 분당 거래 횟수

        return {
            "surge_detected": volume_surge,
            "total_volume_5m": total_volume,
            "trade_frequency_per_min": trade_frequency,
            "avg_trade_size": avg_trade_size,
            "volume_score": min(100, total_volume / 10000),  # 0-100 점수

            # 🎯 스크리너 활용도: ⭐⭐⭐⭐⭐ (매우 높음)
            # - 거래량 급증 코인 실시간 감지
            # - 활발한 거래 코인 선별
            # - 유동성 높은 코인 필터링
        }

    def _analyze_price_momentum(self, trades: List[TradeData]) -> Dict[str, Any]:
        """가격 모멘텀 분석 - 추세 감지용"""
        if len(trades) < 2:
            return {"momentum_direction": "neutral", "momentum_strength": 0}

        # 가격 변화 추이
        prices = [trade.trade_price for trade in trades[-10:]]  # 최근 10건

        if len(prices) >= 2:
            price_change = (prices[-1] - prices[0]) / prices[0] * 100
            momentum_direction = "bullish" if price_change > 0.1 else "bearish" if price_change < -0.1 else "neutral"
        else:
            price_change = 0
            momentum_direction = "neutral"

        return {
            "momentum_direction": momentum_direction,
            "price_change_5m": price_change,
            "momentum_strength": abs(price_change) * 10,  # 0-100 점수

            # 🎯 스크리너 활용도: ⭐⭐⭐⭐ (높음)
            # - 급등/급락 코인 즉시 감지
            # - 모멘텀 거래 기회 포착
            # - 브레이크아웃 초기 신호 감지
        }

    def _analyze_order_flow(self, trades: List[TradeData]) -> Dict[str, Any]:
        """매수/매도 세력 분석"""
        if not trades:
            return {"buy_dominance": 0.5, "flow_direction": "neutral"}

        buy_volume = sum(trade.trade_volume for trade in trades if trade.ask_bid == "BID")
        sell_volume = sum(trade.trade_volume for trade in trades if trade.ask_bid == "ASK")
        total_volume = buy_volume + sell_volume

        buy_dominance = buy_volume / total_volume if total_volume > 0 else 0.5

        if buy_dominance > 0.6:
            flow_direction = "buying_pressure"
        elif buy_dominance < 0.4:
            flow_direction = "selling_pressure"
        else:
            flow_direction = "balanced"

        return {
            "buy_dominance": buy_dominance,
            "flow_direction": flow_direction,
            "buy_volume_5m": buy_volume,
            "sell_volume_5m": sell_volume,

            # 🎯 스크리너 활용도: ⭐⭐⭐⭐ (높음)
            # - 매수/매도 세력 균형 분석
            # - 강한 매수세 코인 선별
            # - 기관/고래 매매 패턴 감지
        }

    def _detect_whale_trades(self, trades: List[TradeData]) -> Dict[str, Any]:
        """대량 거래(고래) 감지"""
        if not trades:
            return {"whale_detected": False, "large_trades_count": 0}

        # 대량 거래 기준 (거래량 기준 상위 10%)
        volumes = [trade.trade_volume for trade in trades]
        if len(volumes) >= 10:
            whale_threshold = sorted(volumes, reverse=True)[min(len(volumes)//10, 9)]
        else:
            whale_threshold = max(volumes) * 0.8 if volumes else 0

        whale_trades = [trade for trade in trades if trade.trade_volume >= whale_threshold]

        return {
            "whale_detected": len(whale_trades) > 0,
            "large_trades_count": len(whale_trades),
            "whale_volume_ratio": len(whale_trades) / len(trades) if trades else 0,

            # 🎯 스크리너 활용도: ⭐⭐⭐⭐⭐ (매우 높음)
            # - 기관/고래 매매 코인 즉시 감지
            # - 큰 손 움직임 추적
            # - 시장 주도 세력 분석
        }

    def _analyze_market_participation(self, trades: List[TradeData]) -> Dict[str, Any]:
        """시장 참여도 분석"""
        if not trades:
            return {"participation_score": 0, "liquidity_level": "low"}

        # 참여도 지표
        unique_prices = len(set(trade.trade_price for trade in trades))
        price_spread = max(trade.trade_price for trade in trades) - min(trade.trade_price for trade in trades)
        participation_score = min(100, len(trades) * unique_prices / 10)

        if participation_score > 70:
            liquidity_level = "high"
        elif participation_score > 30:
            liquidity_level = "medium"
        else:
            liquidity_level = "low"

        return {
            "participation_score": participation_score,
            "liquidity_level": liquidity_level,
            "price_spread_5m": price_spread,
            "unique_price_levels": unique_prices,

            # 🎯 스크리너 활용도: ⭐⭐⭐ (중간)
            # - 유동성 높은 코인 선별
            # - 거래 활성도 측정
            # - 시장 깊이 분석
        }

    def _empty_analysis(self) -> Dict[str, Any]:
        """빈 데이터에 대한 기본 분석 결과"""
        return {
            "volume_metrics": {"surge_detected": False, "volume_score": 0},
            "price_momentum": {"momentum_direction": "neutral", "momentum_strength": 0},
            "order_flow": {"buy_dominance": 0.5, "flow_direction": "neutral"},
            "whale_activities": {"whale_detected": False, "large_trades_count": 0},
            "market_participation": {"participation_score": 0, "liquidity_level": "low"}
        }


class ScreenerIntegration:
    """스크리너와 체결 데이터 통합 분석"""

    def __init__(self):
        self.trade_analyzer = TradeAnalyzer()

    def create_screener_criteria(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        체결 데이터 분석 결과를 스크리너 필터 조건으로 변환

        Returns:
            스크리너에서 사용할 수 있는 필터 조건 리스트
        """
        criteria = []

        # 1. 거래량 급증 필터
        volume_metrics = analysis_result.get("volume_metrics", {})
        if volume_metrics.get("surge_detected"):
            criteria.append({
                "type": "volume_surge",
                "params": {
                    "min_volume_score": volume_metrics.get("volume_score", 0),
                    "timeframe": "5m"
                },
                "description": "거래량 급증 감지",
                "priority": "high"
            })

        # 2. 가격 모멘텀 필터
        momentum = analysis_result.get("price_momentum", {})
        if momentum.get("momentum_strength", 0) > 50:
            criteria.append({
                "type": "price_momentum",
                "params": {
                    "direction": momentum.get("momentum_direction"),
                    "min_strength": momentum.get("momentum_strength"),
                    "timeframe": "5m"
                },
                "description": f"{momentum.get('momentum_direction')} 모멘텀 감지",
                "priority": "high"
            })

        # 3. 고래 거래 필터
        whale_data = analysis_result.get("whale_activities", {})
        if whale_data.get("whale_detected"):
            criteria.append({
                "type": "whale_activity",
                "params": {
                    "min_large_trades": whale_data.get("large_trades_count"),
                    "timeframe": "5m"
                },
                "description": "대량 거래 감지",
                "priority": "critical"
            })

        # 4. 매수세 우위 필터
        order_flow = analysis_result.get("order_flow", {})
        if order_flow.get("flow_direction") == "buying_pressure":
            criteria.append({
                "type": "buying_pressure",
                "params": {
                    "min_buy_dominance": order_flow.get("buy_dominance"),
                    "timeframe": "5m"
                },
                "description": "강한 매수세",
                "priority": "medium"
            })

        return criteria


def analyze_screener_integration_potential():
    """체결 데이터와 스크리너 통합 잠재력 분석"""

    print("🔍 체결 데이터의 스크리너 활용 가능성 분석")
    print("=" * 60)

    # 1. 핵심 활용 시나리오
    scenarios = [
        {
            "name": "거래량 급증 감지",
            "use_case": "갑작스러운 거래량 증가로 관심 집중된 코인 실시간 포착",
            "implementation": "5분 윈도우 내 거래량이 평균 대비 300% 이상 증가 시 알림",
            "value": "⭐⭐⭐⭐⭐ 매우 높음 - 시장 변화 초기 신호",
            "difficulty": "🟢 낮음 - 단순 집계"
        },
        {
            "name": "고래 거래 추적",
            "use_case": "기관/고래의 대량 매매 시점 감지하여 추종 매매 기회 제공",
            "implementation": "단일 거래가 평균 거래량의 10배 이상일 때 고래 거래로 분류",
            "value": "⭐⭐⭐⭐⭐ 매우 높음 - 시장 주도 세력 추적",
            "difficulty": "🟡 중간 - 임계값 튜닝 필요"
        },
        {
            "name": "매수/매도 세력 분석",
            "use_case": "매수세와 매도세 균형 분석으로 방향성 예측",
            "implementation": "5분간 BID/ASK 거래량 비율로 매수/매도 우위 판단",
            "value": "⭐⭐⭐⭐ 높음 - 단기 방향성 예측",
            "difficulty": "🟢 낮음 - 비율 계산"
        },
        {
            "name": "모멘텀 브레이크아웃",
            "use_case": "가격이 급격히 상승/하락하는 초기 시점 포착",
            "implementation": "연속 체결가격의 방향성과 가속도 분석",
            "value": "⭐⭐⭐⭐ 높음 - 추세 초기 진입",
            "difficulty": "🟡 중간 - 노이즈 필터링 필요"
        },
        {
            "name": "유동성 분석",
            "use_case": "거래가 활발하고 슬리피지가 낮은 코인 선별",
            "implementation": "체결 빈도와 가격 분산도로 유동성 수준 측정",
            "value": "⭐⭐⭐ 중간 - 안전한 거래 환경",
            "difficulty": "🟢 낮음 - 통계 계산"
        }
    ]

    print("\n📊 주요 활용 시나리오")
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   💡 활용: {scenario['use_case']}")
        print(f"   🔧 구현: {scenario['implementation']}")
        print(f"   💎 가치: {scenario['value']}")
        print(f"   ⚙️ 난이도: {scenario['difficulty']}")

    # 2. 기술적 구현 복잡도
    print("\n\n🛠️ 기술적 구현 복잡도 분석")
    print("-" * 40)

    implementation_aspects = {
        "데이터 수집": {
            "현재 상태": "Smart Router에서 체결 API 미지원",
            "필요 작업": "Smart Router 확장 또는 직접 업비트 API 연동",
            "예상 시간": "2-3일",
            "복잡도": "🟡 중간"
        },
        "실시간 분석": {
            "현재 상태": "메모리 캐시 시스템 존재",
            "필요 작업": "5분 슬라이딩 윈도우 분석기 구현",
            "예상 시간": "1-2일",
            "복잡도": "🟢 낮음"
        },
        "스크리너 통합": {
            "현재 상태": "스크리너 DDD 재개발 중",
            "필요 작업": "체결 기반 필터 조건 추가",
            "예상 시간": "1일",
            "복잡도": "🟢 낮음"
        },
        "UI 표시": {
            "현재 상태": "Asset Screener 화면 폴백 상태",
            "필요 작업": "체결 지표 컬럼 및 실시간 업데이트",
            "예상 시간": "1-2일",
            "복잡도": "🟢 낮음"
        }
    }

    for aspect, details in implementation_aspects.items():
        print(f"\n• {aspect}")
        print(f"  현재: {details['현재 상태']}")
        print(f"  작업: {details['필요 작업']}")
        print(f"  기간: {details['예상 시간']}")
        print(f"  복잡도: {details['복잡도']}")

    # 3. 투자 대비 효과 분석
    print("\n\n💰 투자 대비 효과 (ROI) 분석")
    print("-" * 40)

    roi_analysis = {
        "개발 투자": {
            "예상 시간": "5-8일",
            "개발 리소스": "Smart Data Provider 확장 + 스크리너 재개발",
            "기술 복잡도": "중간 (외부 API 의존성)"
        },
        "기대 효과": {
            "트레이딩 가치": "⭐⭐⭐⭐⭐ 시장 타이밍 크게 개선",
            "사용자 경험": "⭐⭐⭐⭐ 실시간 시장 인사이트 제공",
            "차별화": "⭐⭐⭐⭐⭐ 일반적인 차트 분석 대비 독특함"
        },
        "위험 요소": {
            "외부 의존성": "Smart Router 또는 업비트 API 안정성",
            "데이터 품질": "체결 데이터 지연 및 누락 가능성",
            "복잡성 증가": "추가 모니터링 및 유지보수 필요"
        }
    }

    for category, details in roi_analysis.items():
        print(f"\n📈 {category}")
        for key, value in details.items():
            print(f"  • {key}: {value}")

    # 4. 최종 권장사항
    print("\n\n🎯 최종 권장사항")
    print("=" * 30)

    recommendations = [
        "✅ 높은 가치: 거래량 급증과 고래 거래 감지는 매우 높은 트레이딩 가치 제공",
        "⚠️ 외부 의존성: Smart Router 체결 API 지원이 선결 조건",
        "🚀 단계적 접근: 먼저 간단한 거래량 분석부터 시작, 점진적 확장",
        "💡 차별화 포인트: 일반적인 기술적 분석과 차별되는 실시간 시장 분석",
        "⏰ 적절한 타이밍: 스크리너 DDD 재개발과 함께 진행하면 시너지"
    ]

    for rec in recommendations:
        print(f"  {rec}")

    print(f"\n🏆 종합 평가: 스크리너에서 체결 데이터 활용은 **높은 가치**를 제공하지만")
    print(f"   **Smart Router 체결 API 지원**이 선결 조건이므로 단계적 접근 권장")


if __name__ == "__main__":
    analyze_screener_integration_potential()
