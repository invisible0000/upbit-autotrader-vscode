# 🚀 새 전략 추가 가이드

> **목적**: Clean Architecture에서 새로운 매매 전략을 체계적으로 추가  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-03

## 🎯 전략 추가 개요

### 구현 순서
1. **💎 Domain**: 전략 엔티티와 비즈니스 규칙 정의
2. **⚙️ Application**: UseCase와 서비스 구현  
3. **🔌 Infrastructure**: 데이터 저장소와 외부 연동
4. **🎨 Presentation**: UI 통합과 사용자 인터페이스
5. **🧪 Testing**: 단위 테스트와 백테스팅 검증

### 예시 전략: "볼린저 RSI 조합 전략"
```python
STRATEGY_SPEC = {
    "이름": "볼린저 RSI 조합 전략",
    "진입조건": "RSI < 30 AND Close < 볼린저밴드_하단",
    "익절조건": "RSI > 70 OR 수익률 > 12%", 
    "손절조건": "손실률 > 5%",
    "관리전략": "트레일링 스탑 (8% 수익 후 3% 추적)"
}
```

## 💎 Domain Layer 구현

### 전략 엔티티 정의
```python
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class StrategySignal(Enum):
    BUY = "buy"
    SELL = "sell" 
    HOLD = "hold"

@dataclass
class BollingerRSIStrategy:
    """볼린저 RSI 조합 전략 엔티티"""
    
    id: str
    name: str = "볼린저 RSI 조합 전략"
    
    # RSI 파라미터
    rsi_period: int = 14
    rsi_oversold: Decimal = Decimal('30')
    rsi_overbought: Decimal = Decimal('70')
    
    # 볼린저 밴드 파라미터
    bb_period: int = 20
    bb_std_dev: Decimal = Decimal('2.0')
    
    # 리스크 관리 파라미터
    take_profit_rate: Decimal = Decimal('0.12')  # 12% 익절
    stop_loss_rate: Decimal = Decimal('0.05')   # 5% 손절
    trailing_stop_activation: Decimal = Decimal('0.08')  # 8% 수익 후 활성화
    trailing_stop_distance: Decimal = Decimal('0.03')   # 3% 추적 거리
    
    is_active: bool = True
    created_at: datetime = datetime.now()
    
    def generate_signal(self, market_data: Dict[str, Any]) -> StrategySignal:
        """매매 신호 생성"""
        current_price = market_data['close']
        rsi = market_data.get('rsi')
        bb_lower = market_data.get('bb_lower')
        bb_upper = market_data.get('bb_upper')
        
        # 필수 지표 확인
        if not all([rsi, bb_lower, bb_upper]):
            return StrategySignal.HOLD
            
        # 진입 신호 (매수)
        if (rsi < self.rsi_oversold and 
            current_price < bb_lower):
            return StrategySignal.BUY
            
        # 청산 신호 (매도)
        if (rsi > self.rsi_overbought or
            current_price > bb_upper):
            return StrategySignal.SELL
            
        return StrategySignal.HOLD
        
    def calculate_position_size(self, available_balance: Decimal, 
                              current_price: Decimal) -> Decimal:
        """포지션 크기 계산"""
        # 리스크 기반 포지션 사이징
        risk_amount = available_balance * self.stop_loss_rate
        position_value = risk_amount / self.stop_loss_rate
        
        return min(position_value / current_price, available_balance / current_price)
        
    def should_apply_stop_loss(self, entry_price: Decimal, 
                             current_price: Decimal) -> bool:
        """손절 조건 확인"""
        loss_rate = (entry_price - current_price) / entry_price
        return loss_rate >= self.stop_loss_rate
        
    def should_take_profit(self, entry_price: Decimal, 
                          current_price: Decimal) -> bool:
        """익절 조건 확인"""
        profit_rate = (current_price - entry_price) / entry_price
        return profit_rate >= self.take_profit_rate
        
    def get_trailing_stop_params(self) -> Dict[str, Decimal]:
        """트레일링 스탑 파라미터 반환"""
        return {
            'activation_profit_rate': self.trailing_stop_activation,
            'trail_distance': self.trailing_stop_distance
        }

class BollingerRSIStrategyFactory:
    """볼린저 RSI 전략 팩토리"""
    
    @staticmethod
    def create_conservative() -> BollingerRSIStrategy:
        """보수적 설정의 전략 생성"""
        return BollingerRSIStrategy(
            id="bolrsi_conservative",
            rsi_oversold=Decimal('25'),
            rsi_overbought=Decimal('75'),
            take_profit_rate=Decimal('0.08'),
            stop_loss_rate=Decimal('0.03')
        )
        
    @staticmethod
    def create_aggressive() -> BollingerRSIStrategy:
        """공격적 설정의 전략 생성"""
        return BollingerRSIStrategy(
            id="bolrsi_aggressive", 
            rsi_oversold=Decimal('35'),
            rsi_overbought=Decimal('65'),
            take_profit_rate=Decimal('0.15'),
            stop_loss_rate=Decimal('0.07')
        )
        
    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> BollingerRSIStrategy:
        """설정으로부터 전략 생성"""
        return BollingerRSIStrategy(
            id=config.get('id', 'bolrsi_custom'),
            rsi_period=config.get('rsi_period', 14),
            rsi_oversold=Decimal(str(config.get('rsi_oversold', 30))),
            rsi_overbought=Decimal(str(config.get('rsi_overbought', 70))),
            bb_period=config.get('bb_period', 20),
            bb_std_dev=Decimal(str(config.get('bb_std_dev', 2.0))),
            take_profit_rate=Decimal(str(config.get('take_profit_rate', 0.12))),
            stop_loss_rate=Decimal(str(config.get('stop_loss_rate', 0.05)))
        )

class StrategyValidationService:
    """전략 유효성 검증 서비스"""
    
    def validate_strategy_parameters(self, strategy: BollingerRSIStrategy) -> List[str]:
        """전략 파라미터 유효성 검증"""
        errors = []
        
        # RSI 파라미터 검증
        if strategy.rsi_period < 2 or strategy.rsi_period > 100:
            errors.append("RSI 기간은 2-100 사이여야 합니다")
            
        if strategy.rsi_oversold >= strategy.rsi_overbought:
            errors.append("RSI 과매도 기준은 과매수 기준보다 작아야 합니다")
            
        # 볼린저 밴드 파라미터 검증  
        if strategy.bb_period < 5 or strategy.bb_period > 200:
            errors.append("볼린저 밴드 기간은 5-200 사이여야 합니다")
            
        if strategy.bb_std_dev <= 0 or strategy.bb_std_dev > 5:
            errors.append("볼린저 밴드 표준편차는 0-5 사이여야 합니다")
            
        # 리스크 관리 파라미터 검증
        if strategy.stop_loss_rate <= 0 or strategy.stop_loss_rate > Decimal('0.5'):
            errors.append("손절률은 0-50% 사이여야 합니다")
            
        if strategy.take_profit_rate <= strategy.stop_loss_rate:
            errors.append("익절률은 손절률보다 커야 합니다")
            
        if strategy.trailing_stop_distance >= strategy.trailing_stop_activation:
            errors.append("트레일링 스탑 거리는 활성화 기준보다 작아야 합니다")
            
        return errors
```

## ⚙️ Application Layer 구현

### UseCase 구현
```python
class CreateBollingerRSIStrategyCommand:
    """볼린저 RSI 전략 생성 명령"""
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config

class BollingerRSIStrategyUseCase:
    """볼린저 RSI 전략 UseCase"""
    
    def __init__(self, strategy_repo, indicator_service, backtesting_service):
        self.strategy_repo = strategy_repo
        self.indicator_service = indicator_service
        self.backtesting_service = backtesting_service
        self.validation_service = StrategyValidationService()
        
    async def create_strategy(self, command: CreateBollingerRSIStrategyCommand) -> Result[str]:
        """새 전략 생성"""
        try:
            # 1. 전략 생성
            strategy = BollingerRSIStrategyFactory.create_from_config(command.config)
            strategy.name = command.name
            
            # 2. 유효성 검증
            validation_errors = self.validation_service.validate_strategy_parameters(strategy)
            if validation_errors:
                return Result.failure(f"유효성 검증 실패: {', '.join(validation_errors)}")
                
            # 3. 중복 이름 체크
            existing = await self.strategy_repo.get_by_name(command.name)
            if existing:
                return Result.failure("동일한 이름의 전략이 이미 존재합니다")
                
            # 4. 저장
            await self.strategy_repo.save(strategy)
            
            return Result.success(strategy.id)
            
        except Exception as e:
            return Result.failure(f"전략 생성 실패: {e}")
            
    async def execute_strategy(self, strategy_id: str, market_data: Dict) -> Result[StrategySignal]:
        """전략 실행"""
        try:
            # 1. 전략 조회
            strategy = await self.strategy_repo.get_by_id(strategy_id)
            if not strategy:
                return Result.failure("전략을 찾을 수 없습니다")
                
            # 2. 필요한 지표 계산
            enriched_data = await self._enrich_market_data(strategy, market_data)
            
            # 3. 신호 생성
            signal = strategy.generate_signal(enriched_data)
            
            return Result.success(signal)
            
        except Exception as e:
            return Result.failure(f"전략 실행 실패: {e}")
            
    async def _enrich_market_data(self, strategy: BollingerRSIStrategy, 
                                market_data: Dict) -> Dict:
        """시장 데이터에 필요한 지표 추가"""
        enriched = market_data.copy()
        
        # RSI 계산
        rsi = await self.indicator_service.calculate_rsi(
            market_data['price_history'], 
            strategy.rsi_period
        )
        enriched['rsi'] = rsi
        
        # 볼린저 밴드 계산
        bb_upper, bb_middle, bb_lower = await self.indicator_service.calculate_bollinger_bands(
            market_data['price_history'],
            strategy.bb_period,
            strategy.bb_std_dev
        )
        enriched.update({
            'bb_upper': bb_upper,
            'bb_middle': bb_middle, 
            'bb_lower': bb_lower
        })
        
        return enriched
        
    async def backtest_strategy(self, strategy_id: str, 
                              start_date: datetime, end_date: datetime) -> Result[Dict]:
        """전략 백테스팅"""
        try:
            strategy = await self.strategy_repo.get_by_id(strategy_id)
            if not strategy:
                return Result.failure("전략을 찾을 수 없습니다")
                
            # 백테스팅 실행
            backtest_result = await self.backtesting_service.run_backtest(
                strategy, start_date, end_date
            )
            
            return Result.success(backtest_result)
            
        except Exception as e:
            return Result.failure(f"백테스팅 실패: {e}")
```

### 전략 관리 서비스
```python
class StrategyManagementService:
    """전략 관리 서비스"""
    
    def __init__(self, strategy_repo):
        self.strategy_repo = strategy_repo
        
    async def list_strategies(self, strategy_type: str = None) -> List[BollingerRSIStrategy]:
        """전략 목록 조회"""
        if strategy_type:
            return await self.strategy_repo.get_by_type(strategy_type)
        return await self.strategy_repo.get_all()
        
    async def clone_strategy(self, source_id: str, new_name: str) -> Result[str]:
        """전략 복제"""
        try:
            source = await self.strategy_repo.get_by_id(source_id)
            if not source:
                return Result.failure("원본 전략을 찾을 수 없습니다")
                
            # 새 전략 생성 (ID와 이름만 변경)
            cloned = BollingerRSIStrategy(
                id=f"clone_{uuid.uuid4().hex[:8]}",
                name=new_name,
                rsi_period=source.rsi_period,
                rsi_oversold=source.rsi_oversold,
                rsi_overbought=source.rsi_overbought,
                bb_period=source.bb_period,
                bb_std_dev=source.bb_std_dev,
                take_profit_rate=source.take_profit_rate,
                stop_loss_rate=source.stop_loss_rate
            )
            
            await self.strategy_repo.save(cloned)
            return Result.success(cloned.id)
            
        except Exception as e:
            return Result.failure(f"전략 복제 실패: {e}")
            
    async def update_strategy_parameters(self, strategy_id: str, 
                                       new_params: Dict[str, Any]) -> Result[bool]:
        """전략 파라미터 업데이트"""
        try:
            strategy = await self.strategy_repo.get_by_id(strategy_id)
            if not strategy:
                return Result.failure("전략을 찾을 수 없습니다")
                
            # 파라미터 업데이트
            for key, value in new_params.items():
                if hasattr(strategy, key):
                    setattr(strategy, key, value)
                    
            # 유효성 재검증
            validation_service = StrategyValidationService()
            errors = validation_service.validate_strategy_parameters(strategy)
            if errors:
                return Result.failure(f"유효성 검증 실패: {', '.join(errors)}")
                
            await self.strategy_repo.save(strategy)
            return Result.success(True)
            
        except Exception as e:
            return Result.failure(f"파라미터 업데이트 실패: {e}")
```

## 🔌 Infrastructure Layer 구현

### Repository 구현
```python
class SqliteBollingerRSIStrategyRepository:
    """SQLite 볼린저 RSI 전략 리포지토리"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._ensure_table_exists()
        
    def _ensure_table_exists(self):
        """테이블 생성"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS bollinger_rsi_strategies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                rsi_period INTEGER NOT NULL,
                rsi_oversold DECIMAL NOT NULL,
                rsi_overbought DECIMAL NOT NULL,
                bb_period INTEGER NOT NULL,
                bb_std_dev DECIMAL NOT NULL,
                take_profit_rate DECIMAL NOT NULL,
                stop_loss_rate DECIMAL NOT NULL,
                trailing_stop_activation DECIMAL NOT NULL,
                trailing_stop_distance DECIMAL NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
    async def save(self, strategy: BollingerRSIStrategy):
        """전략 저장"""
        query = """
            INSERT OR REPLACE INTO bollinger_rsi_strategies
            (id, name, rsi_period, rsi_oversold, rsi_overbought, bb_period, bb_std_dev,
             take_profit_rate, stop_loss_rate, trailing_stop_activation, trailing_stop_distance,
             is_active, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        
        await self.db.execute(query, (
            strategy.id, strategy.name, strategy.rsi_period,
            float(strategy.rsi_oversold), float(strategy.rsi_overbought),
            strategy.bb_period, float(strategy.bb_std_dev),
            float(strategy.take_profit_rate), float(strategy.stop_loss_rate),
            float(strategy.trailing_stop_activation), float(strategy.trailing_stop_distance),
            strategy.is_active
        ))
        
    async def get_by_id(self, strategy_id: str) -> Optional[BollingerRSIStrategy]:
        """ID로 전략 조회"""
        query = "SELECT * FROM bollinger_rsi_strategies WHERE id = ?"
        row = await self.db.fetch_one(query, (strategy_id,))
        
        return self._row_to_entity(row) if row else None
        
    def _row_to_entity(self, row) -> BollingerRSIStrategy:
        """DB 행을 엔티티로 변환"""
        return BollingerRSIStrategy(
            id=row['id'],
            name=row['name'],
            rsi_period=row['rsi_period'],
            rsi_oversold=Decimal(str(row['rsi_oversold'])),
            rsi_overbought=Decimal(str(row['rsi_overbought'])),
            bb_period=row['bb_period'],
            bb_std_dev=Decimal(str(row['bb_std_dev'])),
            take_profit_rate=Decimal(str(row['take_profit_rate'])),
            stop_loss_rate=Decimal(str(row['stop_loss_rate'])),
            trailing_stop_activation=Decimal(str(row['trailing_stop_activation'])),
            trailing_stop_distance=Decimal(str(row['trailing_stop_distance'])),
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at'])
        )
```

## 🎨 Presentation Layer 구현

### UI 통합
```python
class BollingerRSIStrategyPresenter:
    """볼린저 RSI 전략 프레젠터"""
    
    def __init__(self, view, usecase):
        self.view = view
        self.usecase = usecase
        
    async def on_create_strategy_requested(self, form_data: Dict):
        """전략 생성 요청 처리"""
        try:
            command = CreateBollingerRSIStrategyCommand(
                name=form_data['name'],
                config=form_data['parameters']
            )
            
            result = await self.usecase.create_strategy(command)
            
            if result.is_success():
                self.view.show_success_message("전략이 성공적으로 생성되었습니다")
                self.view.refresh_strategy_list()
            else:
                self.view.show_error_message(result.error)
                
        except Exception as e:
            self.view.show_error_message(f"전략 생성 중 오류: {e}")
            
    async def on_backtest_requested(self, strategy_id: str, date_range: tuple):
        """백테스팅 요청 처리"""
        start_date, end_date = date_range
        
        self.view.show_loading_indicator("백테스팅 실행 중...")
        
        try:
            result = await self.usecase.backtest_strategy(strategy_id, start_date, end_date)
            
            if result.is_success():
                self.view.display_backtest_results(result.value)
            else:
                self.view.show_error_message(result.error)
                
        finally:
            self.view.hide_loading_indicator()
```

## 🧪 테스트 구현

### 단위 테스트
```python
import pytest
from decimal import Decimal

class TestBollingerRSIStrategy:
    """볼린저 RSI 전략 단위 테스트"""
    
    def test_generate_buy_signal(self):
        """매수 신호 생성 테스트"""
        strategy = BollingerRSIStrategy(id="test")
        
        market_data = {
            'close': Decimal('50000'),
            'rsi': Decimal('25'),  # 과매도
            'bb_lower': Decimal('51000'),  # 현재가가 하단선 아래
            'bb_upper': Decimal('60000')
        }
        
        signal = strategy.generate_signal(market_data)
        assert signal == StrategySignal.BUY
        
    def test_generate_sell_signal(self):
        """매도 신호 생성 테스트"""
        strategy = BollingerRSIStrategy(id="test")
        
        market_data = {
            'close': Decimal('60000'),
            'rsi': Decimal('75'),  # 과매수
            'bb_lower': Decimal('50000'),
            'bb_upper': Decimal('59000')  # 현재가가 상단선 위
        }
        
        signal = strategy.generate_signal(market_data)
        assert signal == StrategySignal.SELL
        
    def test_parameter_validation(self):
        """파라미터 유효성 검증 테스트"""
        validation_service = StrategyValidationService()
        
        # 유효하지 않은 전략
        invalid_strategy = BollingerRSIStrategy(
            id="test",
            rsi_oversold=Decimal('80'),  # 과매수보다 큰 과매도
            rsi_overbought=Decimal('70')
        )
        
        errors = validation_service.validate_strategy_parameters(invalid_strategy)
        assert len(errors) > 0
        assert "과매도 기준은 과매수 기준보다 작아야 합니다" in errors
```

## 📚 관련 문서

- [시스템 개요](01_SYSTEM_OVERVIEW.md): Clean Architecture 구조
- [기능 개발](04_FEATURE_DEVELOPMENT.md): 새 기능 개발 프로세스
- [테스팅 전략](11_TESTING_STRATEGY.md): 테스트 방법론
- [백테스팅](15_BACKTESTING_EXTENSION.md): 전략 성능 검증

---
**💡 핵심**: "체계적인 계층별 구현으로 안정적이고 확장 가능한 전략을 개발하세요!"
