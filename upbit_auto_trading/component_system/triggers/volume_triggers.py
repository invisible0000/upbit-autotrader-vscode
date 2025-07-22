"""
거래량 기반 트리거 컴포넌트들
Volume Based Trigger Components

거래량 급증, 거래량 감소, 상대적 거래량 등 거래량 기반 트리거들
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from ..base import TriggerComponent, ComponentResult, ExecutionContext


@dataclass
class VolumeSurgeConfig:
    """거래량 급증 트리거 설정"""
    multiplier: float = 2.0  # 평균 대비 배수
    lookback_periods: int = 20  # 평균 계산 기간
    min_volume: float = 100000000  # 최소 거래량 (원)


class VolumeSurgeTrigger(TriggerComponent):
    """
    거래량 급증 트리거 - 평균 대비 거래량이 급증했을 때
    """
    
    def __init__(self, config: VolumeSurgeConfig):
        super().__init__(
            component_id=f"volume_surge_{config.multiplier}x",
            name=f"거래량 급증 트리거 ({config.multiplier}배)",
            description=f"평균 대비 {config.multiplier}배 이상 거래량 급증"
        )
        self.config = config
        self.volume_history: List[float] = []
    
    def evaluate(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """거래량 급증 조건 확인"""
        try:
            current_volume = market_data.get('acc_trade_price_24h', 0)
            if current_volume < self.config.min_volume:
                return ComponentResult(False, f"최소 거래량 미달: {current_volume:,.0f}")
            
            # 거래량 히스토리 업데이트
            self.volume_history.append(current_volume)
            if len(self.volume_history) > self.config.lookback_periods:
                self.volume_history.pop(0)
            
            # 충분한 데이터가 없으면 대기
            if len(self.volume_history) < self.config.lookback_periods:
                return ComponentResult(False, f"데이터 수집 중: {len(self.volume_history)}/{self.config.lookback_periods}")
            
            # 평균 거래량 계산 (현재 제외)
            avg_volume = sum(self.volume_history[:-1]) / (len(self.volume_history) - 1)
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            if volume_ratio >= self.config.multiplier:
                return ComponentResult(
                    True,
                    f"거래량 급증 감지: {volume_ratio:.2f}배 (임계값: {self.config.multiplier}배)",
                    metadata={
                        'trigger_type': 'volume_surge',
                        'current_volume': current_volume,
                        'average_volume': avg_volume,
                        'volume_ratio': volume_ratio,
                        'multiplier': self.config.multiplier
                    }
                )
            
            return ComponentResult(False, f"거래량 비율: {volume_ratio:.2f}배 (임계값: {self.config.multiplier}배)")
            
        except Exception as e:
            return ComponentResult(False, f"거래량 급증 트리거 오류: {str(e)}")


@dataclass
class VolumeDropConfig:
    """거래량 감소 트리거 설정"""
    drop_threshold: float = 0.3  # 감소 임계값 (30% 감소)
    lookback_periods: int = 10  # 비교 기간
    min_volume: float = 50000000  # 최소 거래량 (원)


class VolumeDropTrigger(TriggerComponent):
    """
    거래량 감소 트리거 - 거래량이 급격히 감소했을 때
    """
    
    def __init__(self, config: VolumeDropConfig):
        super().__init__(
            component_id=f"volume_drop_{int(config.drop_threshold*100)}pct",
            name=f"거래량 감소 트리거 ({int(config.drop_threshold*100)}%)",
            description=f"거래량 {int(config.drop_threshold*100)}% 이상 감소"
        )
        self.config = config
        self.volume_history: List[float] = []
    
    def evaluate(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """거래량 감소 조건 확인"""
        try:
            current_volume = market_data.get('acc_trade_price_24h', 0)
            
            # 거래량 히스토리 업데이트
            self.volume_history.append(current_volume)
            if len(self.volume_history) > self.config.lookback_periods:
                self.volume_history.pop(0)
            
            # 충분한 데이터가 없으면 대기
            if len(self.volume_history) < self.config.lookback_periods:
                return ComponentResult(False, f"데이터 수집 중: {len(self.volume_history)}/{self.config.lookback_periods}")
            
            # 이전 평균과 현재 거래량 비교
            prev_avg_volume = sum(self.volume_history[:-3]) / (len(self.volume_history) - 3) if len(self.volume_history) > 3 else 0
            recent_avg_volume = sum(self.volume_history[-3:]) / 3
            
            if prev_avg_volume < self.config.min_volume:
                return ComponentResult(False, f"이전 평균 거래량 미달: {prev_avg_volume:,.0f}")
            
            volume_drop_ratio = (prev_avg_volume - recent_avg_volume) / prev_avg_volume if prev_avg_volume > 0 else 0
            
            if volume_drop_ratio >= self.config.drop_threshold:
                return ComponentResult(
                    True,
                    f"거래량 급감 감지: {volume_drop_ratio:.2%} 감소",
                    metadata={
                        'trigger_type': 'volume_drop',
                        'current_volume': current_volume,
                        'prev_avg_volume': prev_avg_volume,
                        'recent_avg_volume': recent_avg_volume,
                        'drop_ratio': volume_drop_ratio,
                        'threshold': self.config.drop_threshold
                    }
                )
            
            return ComponentResult(False, f"거래량 감소율: {volume_drop_ratio:.2%} (임계값: {self.config.drop_threshold:.2%})")
            
        except Exception as e:
            return ComponentResult(False, f"거래량 감소 트리거 오류: {str(e)}")


@dataclass
class RelativeVolumeConfig:
    """상대적 거래량 트리거 설정"""
    percentile_threshold: float = 80.0  # 백분위 임계값 (상위 20%)
    lookback_days: int = 30  # 과거 데이터 기간 (일)


class RelativeVolumeTrigger(TriggerComponent):
    """
    상대적 거래량 트리거 - 과거 대비 상대적으로 높은 거래량
    """
    
    def __init__(self, config: RelativeVolumeConfig):
        super().__init__(
            component_id=f"relative_volume_{int(config.percentile_threshold)}pct",
            name=f"상대적 거래량 트리거 (상위 {100-config.percentile_threshold:.0f}%)",
            description=f"과거 {config.lookback_days}일 대비 상위 {100-config.percentile_threshold:.0f}% 거래량"
        )
        self.config = config
        self.historical_volumes: List[float] = []
    
    def evaluate(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """상대적 거래량 조건 확인"""
        try:
            current_volume = market_data.get('acc_trade_price_24h', 0)
            
            # 과거 거래량 데이터 업데이트
            self.historical_volumes.append(current_volume)
            max_history = self.config.lookback_days * 24  # 시간별 데이터라고 가정
            if len(self.historical_volumes) > max_history:
                self.historical_volumes.pop(0)
            
            # 충분한 데이터가 없으면 대기
            min_required = max_history // 2  # 최소 절반 이상의 데이터
            if len(self.historical_volumes) < min_required:
                return ComponentResult(False, f"과거 데이터 수집 중: {len(self.historical_volumes)}/{min_required}")
            
            # 백분위 계산
            sorted_volumes = sorted(self.historical_volumes[:-1])  # 현재 제외
            percentile_index = int(len(sorted_volumes) * self.config.percentile_threshold / 100)
            percentile_volume = sorted_volumes[percentile_index] if percentile_index < len(sorted_volumes) else sorted_volumes[-1]
            
            if current_volume > percentile_volume:
                percentile_rank = (sum(1 for v in sorted_volumes if v < current_volume) / len(sorted_volumes)) * 100
                return ComponentResult(
                    True,
                    f"상대적 높은 거래량: {percentile_rank:.1f}백분위 (임계값: {self.config.percentile_threshold}백분위)",
                    metadata={
                        'trigger_type': 'relative_volume',
                        'current_volume': current_volume,
                        'percentile_volume': percentile_volume,
                        'percentile_rank': percentile_rank,
                        'threshold_percentile': self.config.percentile_threshold
                    }
                )
            
            percentile_rank = (sum(1 for v in sorted_volumes if v < current_volume) / len(sorted_volumes)) * 100
            return ComponentResult(False, f"상대적 거래량: {percentile_rank:.1f}백분위 (임계값: {self.config.percentile_threshold}백분위)")
            
        except Exception as e:
            return ComponentResult(False, f"상대적 거래량 트리거 오류: {str(e)}")


@dataclass
class VolumeBreakoutConfig:
    """거래량 돌파 트리거 설정"""
    volume_threshold: float = 500000000  # 절대적 거래량 임계값 (원)
    sustained_periods: int = 3  # 지속 기간 (연속으로 임계값 돌파)


class VolumeBreakoutTrigger(TriggerComponent):
    """
    거래량 돌파 트리거 - 특정 거래량 임계값을 돌파하고 지속
    """
    
    def __init__(self, config: VolumeBreakoutConfig):
        super().__init__(
            component_id=f"volume_breakout_{int(config.volume_threshold/1000000)}m",
            name=f"거래량 돌파 트리거 ({config.volume_threshold/1000000:.0f}M원)",
            description=f"{config.volume_threshold/1000000:.0f}M원 이상 거래량 {config.sustained_periods}회 연속 돌파"
        )
        self.config = config
        self.consecutive_breakouts: int = 0
    
    def evaluate(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """거래량 돌파 조건 확인"""
        try:
            current_volume = market_data.get('acc_trade_price_24h', 0)
            
            if current_volume >= self.config.volume_threshold:
                self.consecutive_breakouts += 1
                
                if self.consecutive_breakouts >= self.config.sustained_periods:
                    return ComponentResult(
                        True,
                        f"거래량 돌파 지속: {self.consecutive_breakouts}회 연속 (임계값: {self.config.volume_threshold/1000000:.0f}M원)",
                        metadata={
                            'trigger_type': 'volume_breakout',
                            'current_volume': current_volume,
                            'volume_threshold': self.config.volume_threshold,
                            'consecutive_breakouts': self.consecutive_breakouts,
                            'required_periods': self.config.sustained_periods
                        }
                    )
                else:
                    return ComponentResult(False, f"거래량 돌파 중: {self.consecutive_breakouts}/{self.config.sustained_periods}회")
            else:
                self.consecutive_breakouts = 0
                return ComponentResult(False, f"거래량 미달: {current_volume/1000000:.0f}M원 (임계값: {self.config.volume_threshold/1000000:.0f}M원)")
            
        except Exception as e:
            return ComponentResult(False, f"거래량 돌파 트리거 오류: {str(e)}")
