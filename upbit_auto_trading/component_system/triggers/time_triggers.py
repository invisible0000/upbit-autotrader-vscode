"""
시간 기반 트리거 컴포넌트들
Time Based Trigger Components

특정 시간, 주기적 실행, 지연 실행 등 시간 기반 트리거들
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from ..base import TriggerComponent, ComponentResult, ExecutionContext


@dataclass
class PeriodicTriggerConfig:
    """주기적 트리거 설정"""
    interval_minutes: int = 60  # 실행 간격 (분)
    start_time: Optional[str] = None  # 시작 시간 "HH:MM"
    end_time: Optional[str] = None    # 종료 시간 "HH:MM"


class PeriodicTrigger(TriggerComponent):
    """
    주기적 트리거 - 지정된 간격으로 실행
    """
    
    def __init__(self, config: PeriodicTriggerConfig):
        super().__init__(
            component_id=f"periodic_{config.interval_minutes}min",
            name=f"주기적 트리거 ({config.interval_minutes}분)",
            description=f"{config.interval_minutes}분마다 실행"
        )
        self.config = config
        self.last_execution_time: Optional[datetime] = None
    
    def evaluate(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """주기적 실행 조건을 확인"""
        try:
            current_time = datetime.now()
            
            # 시간 범위 확인 (설정된 경우)
            if self.config.start_time and self.config.end_time:
                start_time = datetime.strptime(self.config.start_time, "%H:%M").time()
                end_time = datetime.strptime(self.config.end_time, "%H:%M").time()
                current_time_only = current_time.time()
                
                if not (start_time <= current_time_only <= end_time):
                    return ComponentResult(False, f"실행 시간 범위 외: {current_time_only}")
            
            # 첫 실행이거나 간격이 충족되었는지 확인
            if self.last_execution_time is None:
                self.last_execution_time = current_time
                return ComponentResult(True, "주기적 트리거 첫 실행")
            
            elapsed = current_time - self.last_execution_time
            elapsed_minutes = elapsed.total_seconds() / 60
            
            if elapsed_minutes >= self.config.interval_minutes:
                self.last_execution_time = current_time
                return ComponentResult(
                    True,
                    f"주기적 트리거 실행 (간격: {elapsed_minutes:.1f}분)",
                    metadata={
                        'trigger_type': 'periodic',
                        'interval_minutes': self.config.interval_minutes,
                        'elapsed_minutes': elapsed_minutes
                    }
                )
            
            return ComponentResult(False, f"대기 중 (경과: {elapsed_minutes:.1f}분/{self.config.interval_minutes}분)")
            
        except Exception as e:
            return ComponentResult(False, f"주기적 트리거 오류: {str(e)}")


@dataclass
class ScheduledTriggerConfig:
    """예약 트리거 설정"""
    trigger_times: list[str]  # 실행 시간 목록 ["09:00", "15:30"]
    weekdays_only: bool = True  # 평일만 실행


class ScheduledTrigger(TriggerComponent):
    """
    예약 트리거 - 특정 시간에 실행
    """
    
    def __init__(self, config: ScheduledTriggerConfig):
        super().__init__(
            component_id=f"scheduled_{'_'.join(config.trigger_times)}",
            name=f"예약 트리거 ({', '.join(config.trigger_times)})",
            description=f"{', '.join(config.trigger_times)} 시간에 실행"
        )
        self.config = config
        self.executed_today: set[str] = set()  # 오늘 실행한 시간들
        self.last_check_date: Optional[str] = None
    
    def evaluate(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """예약된 시간에 실행"""
        try:
            current_time = datetime.now()
            current_date = current_time.strftime("%Y-%m-%d")
            current_time_str = current_time.strftime("%H:%M")
            
            # 날짜가 바뀌면 실행 기록 초기화
            if self.last_check_date != current_date:
                self.executed_today.clear()
                self.last_check_date = current_date
            
            # 평일만 실행 옵션 확인
            if self.config.weekdays_only and current_time.weekday() >= 5:  # 토요일(5), 일요일(6)
                return ComponentResult(False, "주말에는 실행하지 않음")
            
            # 예약된 시간 중 실행할 시간이 있는지 확인
            for trigger_time in self.config.trigger_times:
                if current_time_str == trigger_time and trigger_time not in self.executed_today:
                    self.executed_today.add(trigger_time)
                    return ComponentResult(
                        True,
                        f"예약 시간 도달: {trigger_time}",
                        metadata={
                            'trigger_type': 'scheduled',
                            'trigger_time': trigger_time,
                            'current_time': current_time_str
                        }
                    )
            
            return ComponentResult(False, f"예약 시간 대기 중 (현재: {current_time_str})")
            
        except Exception as e:
            return ComponentResult(False, f"예약 트리거 오류: {str(e)}")


@dataclass
class DelayTriggerConfig:
    """지연 트리거 설정"""
    delay_minutes: int = 5  # 지연 시간 (분)
    trigger_once: bool = True  # 한 번만 실행


class DelayTrigger(TriggerComponent):
    """
    지연 트리거 - 지정된 시간 후 실행
    """
    
    def __init__(self, config: DelayTriggerConfig):
        super().__init__(
            component_id=f"delay_{config.delay_minutes}min",
            name=f"지연 트리거 ({config.delay_minutes}분)",
            description=f"{config.delay_minutes}분 후 실행"
        )
        self.config = config
        self.activation_time: Optional[datetime] = None
        self.executed: bool = False
    
    def activate(self):
        """트리거 활성화 (지연 시작)"""
        self.activation_time = datetime.now()
        self.executed = False
    
    def evaluate(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """지연 시간 경과 후 실행"""
        try:
            if self.activation_time is None:
                return ComponentResult(False, "지연 트리거가 아직 활성화되지 않음")
            
            if self.config.trigger_once and self.executed:
                return ComponentResult(False, "이미 실행됨 (한 번만 실행 설정)")
            
            current_time = datetime.now()
            elapsed = current_time - self.activation_time
            elapsed_minutes = elapsed.total_seconds() / 60
            
            if elapsed_minutes >= self.config.delay_minutes:
                if self.config.trigger_once:
                    self.executed = True
                
                return ComponentResult(
                    True,
                    f"지연 시간 경과: {elapsed_minutes:.1f}분",
                    metadata={
                        'trigger_type': 'delay',
                        'delay_minutes': self.config.delay_minutes,
                        'elapsed_minutes': elapsed_minutes
                    }
                )
            
            return ComponentResult(False, f"지연 대기 중: {elapsed_minutes:.1f}분/{self.config.delay_minutes}분")
            
        except Exception as e:
            return ComponentResult(False, f"지연 트리거 오류: {str(e)}")
