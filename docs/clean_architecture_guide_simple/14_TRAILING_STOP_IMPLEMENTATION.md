# 🎯 트레일링 스탑 구현 가이드

> **목적**: Clean Architecture에서 트레일링 스탑 기능 완전 구현  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-03

## 🎯 트레일링 스탑 개요

### 핵심 비즈니스 로직
```python
TRAILING_STOP_CONCEPT = {
    "목적": "수익 보호를 위한 동적 손절가 설정",
    "동작원리": "가격 상승 시 손절가를 일정 거리로 추적",
    "활성화조건": "설정된 수익률 달성 (예: 5% 이상)",
    "실행조건": "현재가가 손절가 이하로 하락",
    "실시간성": "1초 이내 가격 변동 감지 및 처리"
}
```

### Clean Architecture 구현 계층
1. **💎 Domain**: TrailingStop 엔티티, 비즈니스 규칙
2. **⚙️ Application**: UseCase, Command/Query
3. **🔌 Infrastructure**: 실시간 데이터, 주문 실행
4. **🎨 Presentation**: UI 설정, 상태 표시

## 💎 Domain Layer 구현

### 트레일링 스탑 엔티티
```python
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional
from enum import Enum

class TrailingStopStatus(Enum):
    INACTIVE = "inactive"      # 비활성화 상태
    WAITING = "waiting"        # 활성화 대기 (수익률 미달)
    ACTIVE = "active"          # 활성화 상태 (추적 중)
    TRIGGERED = "triggered"    # 손절 실행됨

@dataclass
class TrailingStop:
    """트레일링 스탑 도메인 엔티티"""
    
    id: str
    position_id: str
    activation_profit_rate: Decimal    # 활성화 수익률 (예: 0.05 = 5%)
    trail_distance: Decimal           # 추적 거리 (예: 0.03 = 3%)
    current_stop_price: Optional[Decimal] = None
    highest_price: Optional[Decimal] = None
    status: TrailingStopStatus = TrailingStopStatus.INACTIVE
    created_at: datetime = datetime.now()
    activated_at: Optional[datetime] = None
    triggered_at: Optional[datetime] = None
    
    def update_price(self, current_price: Decimal, entry_price: Decimal) -> bool:
        """가격 업데이트 및 손절 여부 반환"""
        profit_rate = (current_price - entry_price) / entry_price
        
        # 1. 활성화 체크
        if self.status == TrailingStopStatus.INACTIVE:
            if profit_rate >= self.activation_profit_rate:
                self._activate(current_price)
                
        elif self.status == TrailingStopStatus.WAITING:
            if profit_rate >= self.activation_profit_rate:
                self._activate(current_price)
                
        # 2. 추적 업데이트
        elif self.status == TrailingStopStatus.ACTIVE:
            # 최고가 갱신 시 손절가 상향 조정
            if current_price > self.highest_price:
                self.highest_price = current_price
                new_stop_price = current_price * (1 - self.trail_distance)
                self.current_stop_price = max(self.current_stop_price, new_stop_price)
                
            # 손절가 터치 체크
            if current_price <= self.current_stop_price:
                self._trigger()
                return True  # 손절 신호
                
        return False
        
    def _activate(self, current_price: Decimal):
        """트레일링 스탑 활성화"""
        self.status = TrailingStopStatus.ACTIVE
        self.highest_price = current_price
        self.current_stop_price = current_price * (1 - self.trail_distance)
        self.activated_at = datetime.now()
        
    def _trigger(self):
        """트레일링 스탑 실행"""
        self.status = TrailingStopStatus.TRIGGERED
        self.triggered_at = datetime.now()
        
    def get_profit_protection_rate(self) -> Optional[Decimal]:
        """현재 보호하고 있는 수익률 반환"""
        if self.status == TrailingStopStatus.ACTIVE and self.current_stop_price:
            return self.current_stop_price / self.entry_price - 1
        return None

class TrailingStopDomainService:
    """트레일링 스탑 도메인 서비스"""
    
    def calculate_optimal_trail_distance(self, 
                                       volatility: Decimal, 
                                       market_condition: str) -> Decimal:
        """시장 상황에 따른 최적 추적 거리 계산"""
        base_distance = Decimal('0.03')  # 기본 3%
        
        # 변동성에 따른 조정
        if volatility > Decimal('0.1'):  # 10% 이상 변동성
            volatility_multiplier = Decimal('1.5')
        elif volatility > Decimal('0.05'):  # 5-10% 변동성
            volatility_multiplier = Decimal('1.2')
        else:
            volatility_multiplier = Decimal('1.0')
            
        # 시장 상황에 따른 조정
        market_multiplier = {
            'bull': Decimal('0.8'),    # 상승장: 좁게
            'bear': Decimal('1.3'),    # 하락장: 넓게
            'sideways': Decimal('1.0') # 횡보: 기본
        }.get(market_condition, Decimal('1.0'))
        
        optimal_distance = base_distance * volatility_multiplier * market_multiplier
        return min(optimal_distance, Decimal('0.1'))  # 최대 10%
        
    def validate_trailing_stop_config(self, 
                                     activation_rate: Decimal,
                                     trail_distance: Decimal) -> bool:
        """트레일링 스탑 설정 유효성 검증"""
        if activation_rate <= 0:
            raise ValueError("활성화 수익률은 양수여야 합니다")
            
        if trail_distance <= 0 or trail_distance >= activation_rate:
            raise ValueError("추적 거리는 0보다 크고 활성화 수익률보다 작아야 합니다")
            
        if trail_distance > Decimal('0.2'):
            raise ValueError("추적 거리는 20%를 초과할 수 없습니다")
            
        return True
```

## ⚙️ Application Layer 구현

### UseCase 구현
```python
from abc import ABC, abstractmethod
from typing import Result

class CreateTrailingStopCommand:
    """트레일링 스탑 생성 명령"""
    def __init__(self, position_id: str, activation_profit_rate: Decimal, 
                 trail_distance: Decimal):
        self.position_id = position_id
        self.activation_profit_rate = activation_profit_rate
        self.trail_distance = trail_distance

class UpdateTrailingStopPriceCommand:
    """트레일링 스탑 가격 업데이트 명령"""
    def __init__(self, trailing_stop_id: str, current_price: Decimal):
        self.trailing_stop_id = trailing_stop_id
        self.current_price = current_price

class TrailingStopUseCase:
    """트레일링 스탑 UseCase"""
    
    def __init__(self, trailing_stop_repo, position_repo, order_service):
        self.trailing_stop_repo = trailing_stop_repo
        self.position_repo = position_repo
        self.order_service = order_service
        self.domain_service = TrailingStopDomainService()
        
    async def create_trailing_stop(self, command: CreateTrailingStopCommand) -> Result[str]:
        """트레일링 스탑 생성"""
        try:
            # 1. 입력 검증
            self.domain_service.validate_trailing_stop_config(
                command.activation_profit_rate, 
                command.trail_distance
            )
            
            # 2. 포지션 확인
            position = await self.position_repo.get_by_id(command.position_id)
            if not position:
                return Result.failure("포지션을 찾을 수 없습니다")
                
            # 3. 기존 트레일링 스탑 중복 체크
            existing = await self.trailing_stop_repo.get_by_position_id(command.position_id)
            if existing and existing.status in [TrailingStopStatus.ACTIVE, TrailingStopStatus.WAITING]:
                return Result.failure("이미 활성화된 트레일링 스탑이 있습니다")
                
            # 4. 트레일링 스탑 생성
            trailing_stop = TrailingStop(
                id=self._generate_id(),
                position_id=command.position_id,
                activation_profit_rate=command.activation_profit_rate,
                trail_distance=command.trail_distance,
                status=TrailingStopStatus.WAITING
            )
            
            # 5. 저장
            await self.trailing_stop_repo.save(trailing_stop)
            
            return Result.success(trailing_stop.id)
            
        except Exception as e:
            return Result.failure(f"트레일링 스탑 생성 실패: {e}")
            
    async def update_price(self, command: UpdateTrailingStopPriceCommand) -> Result[bool]:
        """가격 업데이트 및 손절 처리"""
        try:
            # 1. 트레일링 스탑 조회
            trailing_stop = await self.trailing_stop_repo.get_by_id(command.trailing_stop_id)
            if not trailing_stop:
                return Result.failure("트레일링 스탑을 찾을 수 없습니다")
                
            # 2. 포지션 조회
            position = await self.position_repo.get_by_id(trailing_stop.position_id)
            if not position:
                return Result.failure("포지션을 찾을 수 없습니다")
                
            # 3. 가격 업데이트
            should_close = trailing_stop.update_price(
                command.current_price, 
                position.entry_price
            )
            
            # 4. 상태 저장
            await self.trailing_stop_repo.save(trailing_stop)
            
            # 5. 손절 실행
            if should_close:
                close_result = await self.order_service.create_market_sell_order(
                    position.symbol,
                    position.quantity
                )
                
                if close_result.is_success():
                    # 포지션 상태 업데이트
                    position.close_position(command.current_price)
                    await self.position_repo.save(position)
                    
            return Result.success(should_close)
            
        except Exception as e:
            return Result.failure(f"가격 업데이트 실패: {e}")
            
    def _generate_id(self) -> str:
        """고유 ID 생성"""
        import uuid
        return f"ts_{uuid.uuid4().hex[:8]}"
```

### 실시간 모니터링 서비스
```python
class TrailingStopMonitoringService:
    """트레일링 스탑 실시간 모니터링"""
    
    def __init__(self, trailing_stop_usecase, market_data_service):
        self.usecase = trailing_stop_usecase
        self.market_data_service = market_data_service
        self.monitoring_positions = set()
        
    async def start_monitoring(self, trailing_stop_id: str):
        """모니터링 시작"""
        self.monitoring_positions.add(trailing_stop_id)
        print(f"📊 트레일링 스탑 모니터링 시작: {trailing_stop_id}")
        
    async def stop_monitoring(self, trailing_stop_id: str):
        """모니터링 중지"""
        self.monitoring_positions.discard(trailing_stop_id)
        print(f"⏹️ 트레일링 스탑 모니터링 중지: {trailing_stop_id}")
        
    async def process_price_update(self, symbol: str, price: Decimal):
        """가격 업데이트 처리"""
        # 해당 심볼의 모든 활성 트레일링 스탑 업데이트
        for trailing_stop_id in self.monitoring_positions.copy():
            try:
                command = UpdateTrailingStopPriceCommand(trailing_stop_id, price)
                result = await self.usecase.update_price(command)
                
                if result.is_success() and result.value:  # 손절 실행됨
                    await self.stop_monitoring(trailing_stop_id)
                    print(f"🎯 트레일링 스탑 손절 실행: {trailing_stop_id}")
                    
            except Exception as e:
                print(f"❌ 트레일링 스탑 업데이트 오류: {e}")
```

## 🔌 Infrastructure Layer 구현

### Repository 구현
```python
class SqliteTrailingStopRepository:
    """SQLite 트레일링 스탑 리포지토리"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        
    async def save(self, trailing_stop: TrailingStop):
        """트레일링 스탑 저장"""
        query = """
            INSERT OR REPLACE INTO trailing_stops 
            (id, position_id, activation_profit_rate, trail_distance, 
             current_stop_price, highest_price, status, created_at, 
             activated_at, triggered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        await self.db.execute(query, (
            trailing_stop.id,
            trailing_stop.position_id,
            float(trailing_stop.activation_profit_rate),
            float(trailing_stop.trail_distance),
            float(trailing_stop.current_stop_price) if trailing_stop.current_stop_price else None,
            float(trailing_stop.highest_price) if trailing_stop.highest_price else None,
            trailing_stop.status.value,
            trailing_stop.created_at.isoformat(),
            trailing_stop.activated_at.isoformat() if trailing_stop.activated_at else None,
            trailing_stop.triggered_at.isoformat() if trailing_stop.triggered_at else None
        ))
        
    async def get_by_id(self, trailing_stop_id: str) -> Optional[TrailingStop]:
        """ID로 트레일링 스탑 조회"""
        query = "SELECT * FROM trailing_stops WHERE id = ?"
        row = await self.db.fetch_one(query, (trailing_stop_id,))
        
        return self._row_to_entity(row) if row else None
        
    async def get_active_by_symbol(self, symbol: str) -> List[TrailingStop]:
        """심볼별 활성 트레일링 스탑 조회"""
        query = """
            SELECT ts.* FROM trailing_stops ts
            JOIN positions p ON ts.position_id = p.id
            WHERE p.symbol = ? AND ts.status IN ('waiting', 'active')
        """
        rows = await self.db.fetch_all(query, (symbol,))
        
        return [self._row_to_entity(row) for row in rows]
        
    def _row_to_entity(self, row) -> TrailingStop:
        """DB 행을 엔티티로 변환"""
        return TrailingStop(
            id=row['id'],
            position_id=row['position_id'],
            activation_profit_rate=Decimal(str(row['activation_profit_rate'])),
            trail_distance=Decimal(str(row['trail_distance'])),
            current_stop_price=Decimal(str(row['current_stop_price'])) if row['current_stop_price'] else None,
            highest_price=Decimal(str(row['highest_price'])) if row['highest_price'] else None,
            status=TrailingStopStatus(row['status']),
            created_at=datetime.fromisoformat(row['created_at']),
            activated_at=datetime.fromisoformat(row['activated_at']) if row['activated_at'] else None,
            triggered_at=datetime.fromisoformat(row['triggered_at']) if row['triggered_at'] else None
        )
```

### 실시간 가격 연동
```python
class RealTimePriceIntegration:
    """실시간 가격 데이터 연동"""
    
    def __init__(self, monitoring_service):
        self.monitoring_service = monitoring_service
        
    async def on_price_update(self, symbol: str, price_data: dict):
        """가격 업데이트 이벤트 처리"""
        current_price = Decimal(str(price_data['trade_price']))
        
        # 트레일링 스탑 업데이트
        await self.monitoring_service.process_price_update(symbol, current_price)
```

## 🎨 Presentation Layer 구현

### UI 컨트롤러
```python
class TrailingStopController:
    """트레일링 스탑 UI 컨트롤러"""
    
    def __init__(self, usecase, view):
        self.usecase = usecase
        self.view = view
        
    async def on_create_trailing_stop(self, position_id: str, 
                                    activation_rate: float, 
                                    trail_distance: float):
        """트레일링 스탑 생성 요청"""
        try:
            command = CreateTrailingStopCommand(
                position_id=position_id,
                activation_profit_rate=Decimal(str(activation_rate)),
                trail_distance=Decimal(str(trail_distance))
            )
            
            result = await self.usecase.create_trailing_stop(command)
            
            if result.is_success():
                self.view.show_success_message("트레일링 스탑이 설정되었습니다")
                self.view.refresh_trailing_stop_list()
            else:
                self.view.show_error_message(result.error)
                
        except Exception as e:
            self.view.show_error_message(f"트레일링 스탑 설정 실패: {e}")
            
    async def on_position_price_update(self, position_id: str, current_price: float):
        """포지션 가격 업데이트"""
        # UI에서 실시간 수익률 및 트레일링 스탑 상태 표시
        self.view.update_position_display(position_id, current_price)
```

## 📚 관련 문서

- [시스템 개요](01_SYSTEM_OVERVIEW.md): Clean Architecture 구조
- [레이어 책임](02_LAYER_RESPONSIBILITIES.md): 각 계층의 역할
- [데이터 흐름](03_DATA_FLOW.md): 데이터 처리 과정
- [기능 개발](04_FEATURE_DEVELOPMENT.md): 개발 프로세스

---
**💡 핵심**: "각 계층의 책임을 명확히 분리하여 트레일링 스탑을 안전하고 확장 가능하게 구현하세요!"
