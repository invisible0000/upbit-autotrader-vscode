# 📈 트레일링 스탑 구현 가이드

> **목적**: Clean Architecture에서 트레일링 스탑 기능 전체 구현 과정  
> **대상**: 개발자, 시스템 아키텍트  
> **예상 읽기 시간**: 18분

## 🎯 트레일링 스탑 요구사항

### 📋 비즈니스 요구사항
- **목적**: 수익 보호를 위한 동적 손절가 설정
- **동작**: 가격 상승 시 손절가를 일정 거리로 추적
- **활성화**: 설정된 수익률 달성 시 트레일링 시작
- **실행**: 손절가 터치 시 즉시 포지션 청산

### 🔧 기술적 요구사항
- **실시간 처리**: 1초 이내 가격 변동 감지
- **정확성**: 손절가 계산 정확도 99.9%
- **안정성**: 시스템 재시작 시 상태 복구
- **확장성**: 다중 포지션 동시 관리

## 💎 Domain Layer 구현

### 1. 도메인 객체 정의
```python
# domain/entities/trailing_stop.py
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class TrailingStopId:
    """트레일링 스탑 ID"""
    value: str

class TrailingStop:
    """트레일링 스탑 도메인 엔티티"""
    
    def __init__(
        self,
        id: TrailingStopId,
        position_id: str,
        activation_profit_rate: Decimal,
        trail_distance_rate: Decimal,
        current_price: Decimal,
        entry_price: Decimal
    ):
        self.id = id
        self.position_id = position_id
        self.activation_profit_rate = activation_profit_rate  # 활성화 수익률 (예: 0.05 = 5%)
        self.trail_distance_rate = trail_distance_rate        # 추적 거리 (예: 0.03 = 3%)
        self.entry_price = entry_price
        
        # 상태 변수
        self._is_active = False
        self._highest_price = current_price
        self._stop_price: Optional[Decimal] = None
        self._activated_at: Optional[datetime] = None
        self._last_updated = datetime.utcnow()
        
        # 초기 상태 설정
        self._check_activation(current_price)
    
    @property
    def is_active(self) -> bool:
        """트레일링 스탑 활성화 상태"""
        return self._is_active
    
    @property
    def stop_price(self) -> Optional[Decimal]:
        """현재 손절가"""
        return self._stop_price
    
    @property
    def highest_price(self) -> Decimal:
        """기록된 최고가"""
        return self._highest_price
    
    def update_price(self, new_price: Decimal) -> 'TrailingStopUpdateResult':
        """가격 업데이트 및 트레일링 스탑 로직 실행"""
        
        if new_price <= 0:
            raise ValueError("가격은 0보다 커야 합니다")
        
        previous_stop_price = self._stop_price
        previous_highest_price = self._highest_price
        
        # 활성화 상태 확인
        if not self._is_active:
            self._check_activation(new_price)
        
        # 활성화된 경우 추적 로직 실행
        if self._is_active:
            self._update_trailing_logic(new_price)
        
        self._last_updated = datetime.utcnow()
        
        # 결과 반환
        return TrailingStopUpdateResult(
            is_active=self._is_active,
            stop_price=self._stop_price,
            highest_price=self._highest_price,
            should_close_position=self._should_close_position(new_price),
            stop_price_changed=(previous_stop_price != self._stop_price),
            newly_activated=(not self._is_active and self._activated_at is not None)
        )
    
    def _check_activation(self, current_price: Decimal):
        """트레일링 스탑 활성화 검사"""
        profit_rate = (current_price - self.entry_price) / self.entry_price
        
        if profit_rate >= self.activation_profit_rate and not self._is_active:
            self._is_active = True
            self._highest_price = current_price
            self._stop_price = current_price * (1 - self.trail_distance_rate)
            self._activated_at = datetime.utcnow()
    
    def _update_trailing_logic(self, current_price: Decimal):
        """트레일링 로직 업데이트"""
        
        # 최고가 갱신 확인
        if current_price > self._highest_price:
            self._highest_price = current_price
            
            # 새로운 손절가 계산
            new_stop_price = current_price * (1 - self.trail_distance_rate)
            
            # 손절가는 상승만 가능 (하락하지 않음)
            if self._stop_price is None or new_stop_price > self._stop_price:
                self._stop_price = new_stop_price
    
    def _should_close_position(self, current_price: Decimal) -> bool:
        """포지션 청산 여부 판단"""
        if not self._is_active or self._stop_price is None:
            return False
        
        return current_price <= self._stop_price
    
    def to_snapshot(self) -> 'TrailingStopSnapshot':
        """현재 상태 스냅샷 생성"""
        return TrailingStopSnapshot(
            id=self.id.value,
            position_id=self.position_id,
            is_active=self._is_active,
            highest_price=self._highest_price,
            stop_price=self._stop_price,
            activated_at=self._activated_at,
            last_updated=self._last_updated
        )

@dataclass
class TrailingStopUpdateResult:
    """트레일링 스탑 업데이트 결과"""
    is_active: bool
    stop_price: Optional[Decimal]
    highest_price: Decimal
    should_close_position: bool
    stop_price_changed: bool
    newly_activated: bool

@dataclass
class TrailingStopSnapshot:
    """트레일링 스탑 상태 스냅샷"""
    id: str
    position_id: str
    is_active: bool
    highest_price: Decimal
    stop_price: Optional[Decimal]
    activated_at: Optional[datetime]
    last_updated: datetime
```

### 2. 도메인 서비스
```python
# domain/services/trailing_stop_service.py
class TrailingStopService:
    """트레일링 스탑 도메인 서비스"""
    
    def create_trailing_stop(
        self,
        position_id: str,
        current_price: Decimal,
        entry_price: Decimal,
        activation_profit_rate: Decimal = Decimal('0.05'),
        trail_distance_rate: Decimal = Decimal('0.03')
    ) -> TrailingStop:
        """트레일링 스탑 생성"""
        
        # 유효성 검증
        if activation_profit_rate <= 0 or activation_profit_rate >= 1:
            raise ValueError("활성화 수익률은 0과 1 사이여야 합니다")
        
        if trail_distance_rate <= 0 or trail_distance_rate >= 1:
            raise ValueError("추적 거리는 0과 1 사이여야 합니다")
        
        if current_price <= 0 or entry_price <= 0:
            raise ValueError("가격은 0보다 커야 합니다")
        
        # ID 생성
        trailing_stop_id = TrailingStopId(f"ts_{position_id}_{int(datetime.utcnow().timestamp())}")
        
        return TrailingStop(
            id=trailing_stop_id,
            position_id=position_id,
            activation_profit_rate=activation_profit_rate,
            trail_distance_rate=trail_distance_rate,
            current_price=current_price,
            entry_price=entry_price
        )
    
    def calculate_optimal_trail_distance(
        self,
        volatility: Decimal,
        timeframe: str = "1h"
    ) -> Decimal:
        """변동성 기반 최적 추적 거리 계산"""
        
        # 시간프레임별 기본 배수
        timeframe_multipliers = {
            "1m": Decimal('1.5'),
            "5m": Decimal('2.0'),
            "15m": Decimal('2.5'),
            "1h": Decimal('3.0'),
            "4h": Decimal('4.0'),
            "1d": Decimal('5.0')
        }
        
        multiplier = timeframe_multipliers.get(timeframe, Decimal('3.0'))
        
        # 변동성 * 배수 = 추적 거리
        # 최소 1%, 최대 10%로 제한
        optimal_distance = volatility * multiplier
        return max(Decimal('0.01'), min(optimal_distance, Decimal('0.10')))

# domain/events/trailing_stop_events.py
class TrailingStopActivatedEvent:
    """트레일링 스탑 활성화 이벤트"""
    
    def __init__(self, trailing_stop_id: str, position_id: str, activation_price: Decimal):
        self.trailing_stop_id = trailing_stop_id
        self.position_id = position_id
        self.activation_price = activation_price
        self.occurred_at = datetime.utcnow()

class TrailingStopTriggeredEvent:
    """트레일링 스탑 발동 이벤트"""
    
    def __init__(self, trailing_stop_id: str, position_id: str, trigger_price: Decimal, stop_price: Decimal):
        self.trailing_stop_id = trailing_stop_id
        self.position_id = position_id
        self.trigger_price = trigger_price
        self.stop_price = stop_price
        self.occurred_at = datetime.utcnow()

class TrailingStopUpdatedEvent:
    """트레일링 스탑 업데이트 이벤트"""
    
    def __init__(self, trailing_stop_id: str, old_stop_price: Decimal, new_stop_price: Decimal):
        self.trailing_stop_id = trailing_stop_id
        self.old_stop_price = old_stop_price
        self.new_stop_price = new_stop_price
        self.occurred_at = datetime.utcnow()
```

## ⚙️ Application Layer 구현

### 1. 유스케이스 구현
```python
# application/use_cases/create_trailing_stop_use_case.py
class CreateTrailingStopUseCase:
    """트레일링 스탑 생성 유스케이스"""
    
    def __init__(
        self,
        trailing_stop_repository,
        position_repository,
        market_data_service,
        event_publisher
    ):
        self.trailing_stop_repository = trailing_stop_repository
        self.position_repository = position_repository
        self.market_data_service = market_data_service
        self.event_publisher = event_publisher
    
    def execute(self, command: CreateTrailingStopCommand) -> CreateTrailingStopResult:
        """트레일링 스탑 생성 실행"""
        
        try:
            # 1. 포지션 존재 확인
            position = self.position_repository.find_by_id(command.position_id)
            if not position:
                return CreateTrailingStopResult.failure("포지션을 찾을 수 없습니다")
            
            # 2. 현재 시장 가격 조회
            current_price = self.market_data_service.get_current_price(position.symbol)
            if not current_price:
                return CreateTrailingStopResult.failure("현재 가격을 조회할 수 없습니다")
            
            # 3. 트레일링 스탑 생성
            trailing_stop_service = TrailingStopService()
            trailing_stop = trailing_stop_service.create_trailing_stop(
                position_id=command.position_id,
                current_price=current_price,
                entry_price=position.entry_price,
                activation_profit_rate=command.activation_profit_rate,
                trail_distance_rate=command.trail_distance_rate
            )
            
            # 4. 저장
            saved_trailing_stop = self.trailing_stop_repository.save(trailing_stop)
            
            # 5. 이벤트 발행
            if trailing_stop.is_active:
                event = TrailingStopActivatedEvent(
                    trailing_stop_id=trailing_stop.id.value,
                    position_id=trailing_stop.position_id,
                    activation_price=current_price
                )
                self.event_publisher.publish(event)
            
            return CreateTrailingStopResult.success(saved_trailing_stop.id.value)
            
        except Exception as e:
            logger.error(f"트레일링 스탑 생성 실패: {str(e)}")
            return CreateTrailingStopResult.failure(f"생성 실패: {str(e)}")

# application/use_cases/update_trailing_stop_use_case.py
class UpdateTrailingStopUseCase:
    """트레일링 스탑 업데이트 유스케이스"""
    
    def __init__(
        self,
        trailing_stop_repository,
        position_repository,
        event_publisher
    ):
        self.trailing_stop_repository = trailing_stop_repository
        self.position_repository = position_repository
        self.event_publisher = event_publisher
    
    def execute(self, command: UpdateTrailingStopCommand) -> UpdateTrailingStopResult:
        """트레일링 스탑 업데이트 실행"""
        
        try:
            # 1. 트레일링 스탑 조회
            trailing_stop = self.trailing_stop_repository.find_by_id(
                TrailingStopId(command.trailing_stop_id)
            )
            if not trailing_stop:
                return UpdateTrailingStopResult.failure("트레일링 스탑을 찾을 수 없습니다")
            
            # 2. 가격 업데이트
            old_stop_price = trailing_stop.stop_price
            update_result = trailing_stop.update_price(command.new_price)
            
            # 3. 변경사항 저장
            self.trailing_stop_repository.save(trailing_stop)
            
            # 4. 이벤트 발행
            await self._publish_events(trailing_stop, update_result, old_stop_price)
            
            # 5. 포지션 청산 처리
            if update_result.should_close_position:
                await self._close_position(trailing_stop.position_id, command.new_price)
            
            return UpdateTrailingStopResult.success(update_result)
            
        except Exception as e:
            logger.error(f"트레일링 스탑 업데이트 실패: {str(e)}")
            return UpdateTrailingStopResult.failure(f"업데이트 실패: {str(e)}")
    
    async def _publish_events(
        self,
        trailing_stop: TrailingStop,
        update_result: TrailingStopUpdateResult,
        old_stop_price: Optional[Decimal]
    ):
        """이벤트 발행"""
        
        # 새로 활성화된 경우
        if update_result.newly_activated:
            event = TrailingStopActivatedEvent(
                trailing_stop_id=trailing_stop.id.value,
                position_id=trailing_stop.position_id,
                activation_price=update_result.highest_price
            )
            await self.event_publisher.publish_async(event)
        
        # 손절가 업데이트된 경우
        if update_result.stop_price_changed and old_stop_price:
            event = TrailingStopUpdatedEvent(
                trailing_stop_id=trailing_stop.id.value,
                old_stop_price=old_stop_price,
                new_stop_price=update_result.stop_price
            )
            await self.event_publisher.publish_async(event)
        
        # 발동된 경우
        if update_result.should_close_position:
            event = TrailingStopTriggeredEvent(
                trailing_stop_id=trailing_stop.id.value,
                position_id=trailing_stop.position_id,
                trigger_price=update_result.highest_price,
                stop_price=update_result.stop_price
            )
            await self.event_publisher.publish_async(event)
    
    async def _close_position(self, position_id: str, close_price: Decimal):
        """포지션 청산 처리"""
        try:
            position = self.position_repository.find_by_id(position_id)
            if position:
                position.close(close_price, "TRAILING_STOP")
                self.position_repository.save(position)
        except Exception as e:
            logger.error(f"포지션 청산 실패: {str(e)}")

# application/services/trailing_stop_manager_service.py
class TrailingStopManagerService:
    """트레일링 스탑 관리 서비스"""
    
    def __init__(
        self,
        update_trailing_stop_use_case,
        trailing_stop_repository,
        market_data_service
    ):
        self.update_use_case = update_trailing_stop_use_case
        self.repository = trailing_stop_repository
        self.market_data_service = market_data_service
    
    async def process_market_data_update(self, symbol: str, new_price: Decimal):
        """시장 데이터 업데이트 처리"""
        
        # 해당 심볼의 활성 트레일링 스탑 조회
        active_trailing_stops = self.repository.find_active_by_symbol(symbol)
        
        if not active_trailing_stops:
            return
        
        # 병렬 처리로 성능 최적화
        tasks = []
        for trailing_stop in active_trailing_stops:
            command = UpdateTrailingStopCommand(
                trailing_stop_id=trailing_stop.id.value,
                new_price=new_price
            )
            task = self.update_use_case.execute(command)
            tasks.append(task)
        
        # 모든 업데이트 대기
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 로깅
        success_count = sum(1 for r in results if isinstance(r, UpdateTrailingStopResult) and r.success)
        error_count = len(results) - success_count
        
        logger.info(f"트레일링 스탑 업데이트 완료: 성공 {success_count}, 실패 {error_count}")
```

### 2. 명령 및 결과 객체
```python
# application/commands/trailing_stop_commands.py
@dataclass
class CreateTrailingStopCommand:
    """트레일링 스탑 생성 명령"""
    position_id: str
    activation_profit_rate: Decimal
    trail_distance_rate: Decimal

@dataclass
class UpdateTrailingStopCommand:
    """트레일링 스탑 업데이트 명령"""
    trailing_stop_id: str
    new_price: Decimal

# application/results/trailing_stop_results.py
class CreateTrailingStopResult:
    """트레일링 스탑 생성 결과"""
    
    def __init__(self, success: bool, trailing_stop_id: str = None, error_message: str = None):
        self.success = success
        self.trailing_stop_id = trailing_stop_id
        self.error_message = error_message
    
    @classmethod
    def success(cls, trailing_stop_id: str):
        return cls(success=True, trailing_stop_id=trailing_stop_id)
    
    @classmethod
    def failure(cls, error_message: str):
        return cls(success=False, error_message=error_message)

class UpdateTrailingStopResult:
    """트레일링 스탑 업데이트 결과"""
    
    def __init__(self, success: bool, update_result: TrailingStopUpdateResult = None, error_message: str = None):
        self.success = success
        self.update_result = update_result
        self.error_message = error_message
    
    @classmethod
    def success(cls, update_result: TrailingStopUpdateResult):
        return cls(success=True, update_result=update_result)
    
    @classmethod
    def failure(cls, error_message: str):
        return cls(success=False, error_message=error_message)
```

## 🔌 Infrastructure Layer 구현

### 1. Repository 구현
```python
# infrastructure/repositories/sqlite_trailing_stop_repository.py
class SQLiteTrailingStopRepository:
    """SQLite 트레일링 스탑 Repository"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def save(self, trailing_stop: TrailingStop) -> TrailingStop:
        """트레일링 스탑 저장"""
        
        snapshot = trailing_stop.to_snapshot()
        
        query = """
        INSERT OR REPLACE INTO trailing_stops 
        (id, position_id, is_active, highest_price, stop_price, 
         activation_profit_rate, trail_distance_rate, activated_at, 
         last_updated, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        with self.db.transaction():
            self.db.execute(query, (
                snapshot.id,
                snapshot.position_id,
                snapshot.is_active,
                float(snapshot.highest_price),
                float(snapshot.stop_price) if snapshot.stop_price else None,
                float(trailing_stop.activation_profit_rate),
                float(trailing_stop.trail_distance_rate),
                snapshot.activated_at.isoformat() if snapshot.activated_at else None,
                snapshot.last_updated.isoformat(),
                datetime.utcnow().isoformat()
            ))
        
        return trailing_stop
    
    def find_by_id(self, trailing_stop_id: TrailingStopId) -> Optional[TrailingStop]:
        """ID로 트레일링 스탑 조회"""
        
        query = """
        SELECT ts.*, p.symbol, p.entry_price
        FROM trailing_stops ts
        INNER JOIN positions p ON ts.position_id = p.id
        WHERE ts.id = ?
        """
        
        row = self.db.fetchone(query, (trailing_stop_id.value,))
        if row:
            return self._map_to_domain(row)
        return None
    
    def find_active_by_symbol(self, symbol: str) -> List[TrailingStop]:
        """심볼별 활성 트레일링 스탑 조회"""
        
        query = """
        SELECT ts.*, p.symbol, p.entry_price
        FROM trailing_stops ts
        INNER JOIN positions p ON ts.position_id = p.id
        WHERE p.symbol = ? AND ts.is_active = 1 AND p.status = 'OPEN'
        """
        
        rows = self.db.fetchall(query, (symbol,))
        return [self._map_to_domain(row) for row in rows]
    
    def _map_to_domain(self, row) -> TrailingStop:
        """DB 행을 도메인 객체로 변환"""
        
        trailing_stop = TrailingStop(
            id=TrailingStopId(row['id']),
            position_id=row['position_id'],
            activation_profit_rate=Decimal(str(row['activation_profit_rate'])),
            trail_distance_rate=Decimal(str(row['trail_distance_rate'])),
            current_price=Decimal(str(row['highest_price'])),
            entry_price=Decimal(str(row['entry_price']))
        )
        
        # 저장된 상태 복원
        if row['is_active']:
            trailing_stop._is_active = True
            trailing_stop._highest_price = Decimal(str(row['highest_price']))
            if row['stop_price']:
                trailing_stop._stop_price = Decimal(str(row['stop_price']))
            if row['activated_at']:
                trailing_stop._activated_at = datetime.fromisoformat(row['activated_at'])
        
        return trailing_stop

# infrastructure/database/trailing_stop_schema.sql
CREATE TABLE IF NOT EXISTS trailing_stops (
    id TEXT PRIMARY KEY,
    position_id TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 0,
    highest_price DECIMAL(20, 8) NOT NULL,
    stop_price DECIMAL(20, 8),
    activation_profit_rate DECIMAL(5, 4) NOT NULL,
    trail_distance_rate DECIMAL(5, 4) NOT NULL,
    activated_at TIMESTAMP,
    last_updated TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (position_id) REFERENCES positions(id),
    INDEX idx_trailing_stops_position (position_id),
    INDEX idx_trailing_stops_active (is_active, last_updated)
);
```

### 2. 실시간 가격 모니터링
```python
# infrastructure/services/real_time_price_monitor.py
class RealTimePriceMonitor:
    """실시간 가격 모니터링 서비스"""
    
    def __init__(self, market_data_client, trailing_stop_manager):
        self.market_data_client = market_data_client
        self.trailing_stop_manager = trailing_stop_manager
        self.subscriptions = set()
        self.running = False
    
    async def start_monitoring(self):
        """모니터링 시작"""
        self.running = True
        
        # WebSocket 연결
        await self.market_data_client.connect()
        
        # 가격 업데이트 구독
        self.market_data_client.on_price_update(self._handle_price_update)
        
        logger.info("실시간 가격 모니터링 시작")
    
    async def stop_monitoring(self):
        """모니터링 중지"""
        self.running = False
        await self.market_data_client.disconnect()
        logger.info("실시간 가격 모니터링 중지")
    
    async def subscribe_symbol(self, symbol: str):
        """심볼 구독"""
        if symbol not in self.subscriptions:
            await self.market_data_client.subscribe(symbol)
            self.subscriptions.add(symbol)
            logger.info(f"심볼 구독: {symbol}")
    
    async def unsubscribe_symbol(self, symbol: str):
        """심볼 구독 해제"""
        if symbol in self.subscriptions:
            await self.market_data_client.unsubscribe(symbol)
            self.subscriptions.remove(symbol)
            logger.info(f"심볼 구독 해제: {symbol}")
    
    async def _handle_price_update(self, symbol: str, price_data: dict):
        """가격 업데이트 처리"""
        try:
            new_price = Decimal(str(price_data['price']))
            
            # 트레일링 스탑 업데이트
            await self.trailing_stop_manager.process_market_data_update(symbol, new_price)
            
        except Exception as e:
            logger.error(f"가격 업데이트 처리 실패 - {symbol}: {str(e)}")
```

## 🎨 Presentation Layer 구현

### 1. Presenter 구현
```python
# presentation/presenters/trailing_stop_presenter.py
class TrailingStopPresenter:
    """트레일링 스탑 Presenter"""
    
    def __init__(
        self,
        create_trailing_stop_use_case,
        update_trailing_stop_use_case,
        view
    ):
        self.create_use_case = create_trailing_stop_use_case
        self.update_use_case = update_trailing_stop_use_case
        self.view = view
    
    def create_trailing_stop(
        self,
        position_id: str,
        activation_profit_rate: str,
        trail_distance_rate: str
    ):
        """트레일링 스탑 생성"""
        
        try:
            # 입력 검증
            activation_rate = Decimal(activation_profit_rate) / 100  # 퍼센트를 소수로 변환
            trail_rate = Decimal(trail_distance_rate) / 100
            
            if activation_rate <= 0 or activation_rate >= 1:
                self.view.show_validation_error("활성화 수익률은 0.1%에서 99.9% 사이여야 합니다")
                return
            
            if trail_rate <= 0 or trail_rate >= 1:
                self.view.show_validation_error("추적 거리는 0.1%에서 99.9% 사이여야 합니다")
                return
            
            # 유스케이스 실행
            command = CreateTrailingStopCommand(
                position_id=position_id,
                activation_profit_rate=activation_rate,
                trail_distance_rate=trail_rate
            )
            
            result = self.create_use_case.execute(command)
            
            if result.success:
                self.view.show_success_message("트레일링 스탑이 설정되었습니다")
                self.view.refresh_trailing_stop_list()
            else:
                self.view.show_error_message(result.error_message)
        
        except ValueError as e:
            self.view.show_validation_error("올바른 숫자를 입력해주세요")
        except Exception as e:
            logger.error(f"트레일링 스탑 생성 오류: {str(e)}")
            self.view.show_error_message("트레일링 스탑 설정 중 오류가 발생했습니다")

# presentation/views/trailing_stop_view.py
class TrailingStopView(QWidget):
    """트레일링 스탑 View"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_events()
    
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout()
        
        # 설정 패널
        self.settings_panel = self.create_settings_panel()
        layout.addWidget(self.settings_panel)
        
        # 트레일링 스탑 목록
        self.trailing_stop_list = self.create_trailing_stop_list()
        layout.addWidget(self.trailing_stop_list)
        
        self.setLayout(layout)
    
    def create_settings_panel(self) -> QWidget:
        """설정 패널 생성"""
        panel = QGroupBox("트레일링 스탑 설정")
        layout = QFormLayout()
        
        # 활성화 수익률 입력
        self.activation_rate_input = QDoubleSpinBox()
        self.activation_rate_input.setRange(0.1, 99.9)
        self.activation_rate_input.setValue(5.0)
        self.activation_rate_input.setSuffix(" %")
        layout.addRow("활성화 수익률:", self.activation_rate_input)
        
        # 추적 거리 입력
        self.trail_distance_input = QDoubleSpinBox()
        self.trail_distance_input.setRange(0.1, 99.9)
        self.trail_distance_input.setValue(3.0)
        self.trail_distance_input.setSuffix(" %")
        layout.addRow("추적 거리:", self.trail_distance_input)
        
        # 생성 버튼
        self.create_button = QPushButton("트레일링 스탑 설정")
        layout.addRow(self.create_button)
        
        panel.setLayout(layout)
        return panel
    
    def create_trailing_stop_list(self) -> QTableWidget:
        """트레일링 스탑 목록 테이블 생성"""
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "포지션", "상태", "활성화가", "현재 손절가", "최고가", "수익률"
        ])
        
        # 테이블 스타일 설정
        table.horizontalHeader().setStretchLastSection(True)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        return table
```

### 2. 실시간 UI 업데이트
```python
# presentation/widgets/trailing_stop_monitor_widget.py
class TrailingStopMonitorWidget(QWidget):
    """트레일링 스탑 실시간 모니터링 위젯"""
    
    def __init__(self):
        super().__init__()
        self.trailing_stops = {}  # 트레일링 스탑 상태 캐시
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout()
        
        # 상태 표시 라벨
        self.status_label = QLabel("트레일링 스탑 모니터링: 중지됨")
        layout.addWidget(self.status_label)
        
        # 트레일링 스탑 차트
        self.chart_widget = self.create_chart_widget()
        layout.addWidget(self.chart_widget)
        
        self.setLayout(layout)
    
    def setup_timer(self):
        """업데이트 타이머 설정"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # 1초마다 업데이트
    
    def update_trailing_stop_data(self, trailing_stop_data: dict):
        """트레일링 스탑 데이터 업데이트"""
        self.trailing_stops[trailing_stop_data['id']] = trailing_stop_data
        self.update_display()
    
    def update_display(self):
        """화면 업데이트"""
        if self.trailing_stops:
            self.status_label.setText(f"활성 트레일링 스탑: {len(self.trailing_stops)}개")
            self.update_chart()
        else:
            self.status_label.setText("활성 트레일링 스탑 없음")
    
    def create_chart_widget(self) -> QWidget:
        """차트 위젯 생성"""
        # 실시간 가격 차트와 트레일링 스탑 라인 표시
        # matplotlib 또는 pyqtgraph 사용
        pass
    
    def update_chart(self):
        """차트 업데이트"""
        # 현재 가격, 손절가, 최고가 라인 그리기
        pass
```

## 🔍 다음 단계

- **[백테스팅 확장](13_BACKTESTING_EXTENSION.md)**: 트레일링 스탑이 포함된 백테스팅
- **[성능 최적화](10_PERFORMANCE_OPTIMIZATION.md)**: 실시간 처리 최적화
- **[모니터링 전략](17_MONITORING_STRATEGY.md)**: 트레일링 스탑 성능 모니터링

---
**💡 핵심**: "Clean Architecture를 통해 복잡한 트레일링 스탑 로직을 계층별로 분리하여 테스트 가능하고 확장 가능한 구조로 구현합니다!"
