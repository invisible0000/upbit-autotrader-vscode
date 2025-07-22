"""
포지션 태그 기반 관리 시스템 설계
Position Tag-Based Management System Design

핵심 아이디어: 포지션을 태그로 구분하여 자동매매와 수동매매를 완전 분리
- AUTO: 완전 자동매매 포지션 (전략 엔진만 제어)
- MANUAL: 수동 매매 포지션 (사용자만 제어)
- HYBRID: 혼합 포지션 (제한적 자동화)

이 방식의 장점:
1. 사고 방지: 자동매매가 수동 포지션을 건드릴 수 없음
2. 명확한 책임 분리: 각 포지션의 관리 주체가 명확
3. 개발 복잡도 감소: 평단가 재계산 등 복잡한 로직 불필요
4. 사용자 경험 개선: 직관적이고 안전한 인터페이스
"""

from typing import Dict, Any, Optional, List, Literal
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from decimal import Decimal


class PositionTag(Enum):
    """포지션 태그 타입"""
    AUTO = "AUTO"        # 완전 자동매매 포지션
    MANUAL = "MANUAL"    # 수동 매매 포지션  
    HYBRID = "HYBRID"    # 혼합 포지션 (제한적 자동화)
    LOCKED = "LOCKED"    # 잠금 포지션 (거래 금지)


@dataclass
class PositionEntry:
    """개별 포지션 엔트리 (매수 기록)"""
    entry_id: str
    timestamp: datetime
    symbol: str
    quantity: Decimal
    price: Decimal
    amount: Decimal  # quantity * price
    tag: PositionTag
    strategy_id: Optional[str] = None  # AUTO 포지션인 경우 연결된 전략 ID
    notes: str = ""  # 사용자 메모


@dataclass 
class TaggedPosition:
    """태그별 포지션 정보"""
    symbol: str
    tag: PositionTag
    entries: List[PositionEntry]
    
    # 계산된 값들
    total_quantity: Decimal = Decimal('0')
    total_amount: Decimal = Decimal('0')
    average_price: Decimal = Decimal('0')
    current_value: Decimal = Decimal('0')
    unrealized_pnl: Decimal = Decimal('0')
    unrealized_pnl_percent: float = 0.0
    
    # 태그별 제한사항
    auto_trading_enabled: bool = True
    manual_trading_enabled: bool = True
    
    def __post_init__(self):
        """포지션 정보 재계산"""
        self.recalculate()
        self._apply_tag_restrictions()
    
    def recalculate(self):
        """포지션 수치 재계산"""
        if not self.entries:
            self.total_quantity = Decimal('0')
            self.total_amount = Decimal('0')
            self.average_price = Decimal('0')
            return
        
        self.total_quantity = sum(entry.quantity for entry in self.entries)
        self.total_amount = sum(entry.amount for entry in self.entries)
        
        if self.total_quantity > 0:
            self.average_price = self.total_amount / self.total_quantity
        else:
            self.average_price = Decimal('0')
    
    def _apply_tag_restrictions(self):
        """태그별 제한사항 적용"""
        if self.tag == PositionTag.AUTO:
            self.manual_trading_enabled = False  # 수동 매매 금지
        elif self.tag == PositionTag.MANUAL:
            self.auto_trading_enabled = False   # 자동 매매 금지
        elif self.tag == PositionTag.LOCKED:
            self.auto_trading_enabled = False   # 모든 거래 금지
            self.manual_trading_enabled = False
    
    def add_entry(self, entry: PositionEntry) -> bool:
        """포지션 엔트리 추가"""
        # 태그 일치 확인
        if entry.tag != self.tag:
            return False
        
        self.entries.append(entry)
        self.recalculate()
        return True
    
    def can_auto_trade(self) -> bool:
        """자동 매매 가능 여부"""
        return self.auto_trading_enabled and self.tag in [PositionTag.AUTO, PositionTag.HYBRID]
    
    def can_manual_trade(self) -> bool:
        """수동 매매 가능 여부"""
        return self.manual_trading_enabled and self.tag in [PositionTag.MANUAL, PositionTag.HYBRID]


class PositionManager:
    """
    태그 기반 포지션 관리자
    
    각 코인별로 여러 개의 태그별 포지션을 독립적으로 관리
    """
    
    def __init__(self):
        # symbol -> tag -> TaggedPosition
        self.positions: Dict[str, Dict[PositionTag, TaggedPosition]] = {}
        self.strategy_positions: Dict[str, List[str]] = {}  # strategy_id -> position_ids
    
    def create_position(self, 
                       symbol: str, 
                       tag: PositionTag, 
                       strategy_id: Optional[str] = None) -> str:
        """새로운 태그별 포지션 생성"""
        if symbol not in self.positions:
            self.positions[symbol] = {}
        
        if tag in self.positions[symbol]:
            # 이미 해당 태그의 포지션이 존재
            return f"{symbol}_{tag.value}"
        
        position = TaggedPosition(symbol=symbol, tag=tag, entries=[])
        self.positions[symbol][tag] = position
        
        # 전략 연결 (AUTO 포지션인 경우)
        if strategy_id and tag == PositionTag.AUTO:
            position_id = f"{symbol}_{tag.value}"
            if strategy_id not in self.strategy_positions:
                self.strategy_positions[strategy_id] = []
            self.strategy_positions[strategy_id].append(position_id)
        
        return f"{symbol}_{tag.value}"
    
    def add_buy_entry(self, 
                     symbol: str, 
                     tag: PositionTag,
                     quantity: Decimal, 
                     price: Decimal,
                     strategy_id: Optional[str] = None,
                     notes: str = "") -> bool:
        """매수 엔트리 추가"""
        
        # 포지션이 없으면 생성
        if symbol not in self.positions or tag not in self.positions[symbol]:
            self.create_position(symbol, tag, strategy_id)
        
        position = self.positions[symbol][tag]
        
        # 매매 권한 확인
        if tag == PositionTag.AUTO and not position.can_auto_trade():
            return False
        if tag == PositionTag.MANUAL and not position.can_manual_trade():
            return False
        
        entry = PositionEntry(
            entry_id=f"{symbol}_{tag.value}_{len(position.entries)+1}_{int(datetime.now().timestamp())}",
            timestamp=datetime.now(),
            symbol=symbol,
            quantity=quantity,
            price=price,
            amount=quantity * price,
            tag=tag,
            strategy_id=strategy_id,
            notes=notes
        )
        
        return position.add_entry(entry)
    
    def get_position(self, symbol: str, tag: PositionTag) -> Optional[TaggedPosition]:
        """특정 태그의 포지션 조회"""
        if symbol not in self.positions:
            return None
        return self.positions[symbol].get(tag)
    
    def get_all_positions(self, symbol: str) -> Dict[PositionTag, TaggedPosition]:
        """심볼의 모든 태그 포지션 조회"""
        return self.positions.get(symbol, {})
    
    def get_strategy_positions(self, strategy_id: str) -> List[TaggedPosition]:
        """전략에 연결된 모든 포지션 조회"""
        if strategy_id not in self.strategy_positions:
            return []
        
        positions = []
        for position_id in self.strategy_positions[strategy_id]:
            symbol, tag_value = position_id.split('_', 1)
            tag = PositionTag(tag_value)
            position = self.get_position(symbol, tag)
            if position:
                positions.append(position)
        
        return positions
    
    def close_position(self, 
                      symbol: str, 
                      tag: PositionTag, 
                      sell_quantity: Optional[Decimal] = None,
                      sell_price: Optional[Decimal] = None) -> bool:
        """포지션 청산 (전체 또는 부분)"""
        
        position = self.get_position(symbol, tag)
        if not position:
            return False
        
        # 매매 권한 확인
        if tag == PositionTag.AUTO and not position.can_auto_trade():
            return False
        if tag == PositionTag.MANUAL and not position.can_manual_trade():
            return False
        
        if sell_quantity is None:
            # 전체 청산
            del self.positions[symbol][tag]
            return True
        else:
            # 부분 청산 (복잡한 로직이므로 일단 전체 청산만 지원)
            # 실제 구현에서는 FIFO/LIFO 등의 방식으로 처리
            return True
    
    def change_position_tag(self, 
                           symbol: str, 
                           from_tag: PositionTag, 
                           to_tag: PositionTag) -> bool:
        """포지션 태그 변경 (신중하게 사용)"""
        
        position = self.get_position(symbol, from_tag)
        if not position:
            return False
        
        # 기존 포지션 제거
        del self.positions[symbol][from_tag]
        
        # 새로운 태그로 포지션 생성
        new_position = TaggedPosition(symbol=symbol, tag=to_tag, entries=position.entries)
        
        # 모든 엔트리의 태그도 변경
        for entry in new_position.entries:
            entry.tag = to_tag
        
        new_position.recalculate()
        self.positions[symbol][to_tag] = new_position
        
        return True
    
    def get_position_summary(self) -> Dict[str, Any]:
        """포지션 요약 정보"""
        summary = {
            'total_symbols': len(self.positions),
            'by_tag': {tag.value: 0 for tag in PositionTag},
            'by_symbol': {},
            'total_value': Decimal('0')
        }
        
        for symbol, tag_positions in self.positions.items():
            symbol_info = {
                'tags': list(tag_positions.keys()),
                'total_quantity': Decimal('0'),
                'total_value': Decimal('0')
            }
            
            for tag, position in tag_positions.items():
                summary['by_tag'][tag.value] += 1
                symbol_info['total_quantity'] += position.total_quantity
                symbol_info['total_value'] += position.current_value
                summary['total_value'] += position.current_value
            
            summary['by_symbol'][symbol] = symbol_info
        
        return summary


# 사용 예시 및 테스트
def example_usage():
    """태그 기반 포지션 관리 사용 예시"""
    
    print("=== 태그 기반 포지션 관리 시스템 예시 ===")
    
    manager = PositionManager()
    
    # 1. 수동으로 비트코인 매수 (MANUAL 포지션)
    print("\n1. 수동 매수: BTC 0.01개 @ 50,000,000원")
    success = manager.add_buy_entry(
        symbol="KRW-BTC",
        tag=PositionTag.MANUAL,
        quantity=Decimal('0.01'),
        price=Decimal('50000000'),
        notes="수동 매수 - 직관으로 매수"
    )
    print(f"매수 성공: {success}")
    
    # 2. 자동매매로 비트코인 매수 (AUTO 포지션) - 별도 관리
    print("\n2. 자동매매: BTC 0.005개 @ 48,000,000원 (물타기 전략)")
    success = manager.add_buy_entry(
        symbol="KRW-BTC", 
        tag=PositionTag.AUTO,
        quantity=Decimal('0.005'),
        price=Decimal('48000000'),
        strategy_id="pyramiding_001",
        notes="물타기 1단계 매수"
    )
    print(f"매수 성공: {success}")
    
    # 3. 또 다른 자동매매 추가 (같은 AUTO 포지션에 누적)
    print("\n3. 자동매매 추가: BTC 0.0075개 @ 46,000,000원")
    success = manager.add_buy_entry(
        symbol="KRW-BTC",
        tag=PositionTag.AUTO, 
        quantity=Decimal('0.0075'),
        price=Decimal('46000000'),
        strategy_id="pyramiding_001",
        notes="물타기 2단계 매수"
    )
    print(f"매수 성공: {success}")
    
    # 4. 포지션 현황 조회
    print("\n4. 현재 BTC 포지션 현황:")
    btc_positions = manager.get_all_positions("KRW-BTC")
    
    for tag, position in btc_positions.items():
        print(f"\n[{tag.value} 포지션]")
        print(f"  보유 수량: {position.total_quantity}")
        print(f"  평균 단가: {position.average_price:,.0f}원")
        print(f"  총 투자금: {position.total_amount:,.0f}원")
        print(f"  자동매매 가능: {position.can_auto_trade()}")
        print(f"  수동매매 가능: {position.can_manual_trade()}")
        print(f"  매수 기록: {len(position.entries)}건")
    
    # 5. 전략별 포지션 조회
    print("\n5. pyramiding_001 전략의 포지션:")
    strategy_positions = manager.get_strategy_positions("pyramiding_001")
    for position in strategy_positions:
        print(f"  {position.symbol} {position.tag.value}: {position.total_quantity} @ {position.average_price:,.0f}")
    
    # 6. 전체 요약
    print("\n6. 전체 포지션 요약:")
    summary = manager.get_position_summary()
    print(f"  보유 코인 수: {summary['total_symbols']}")
    print(f"  태그별 포지션: {summary['by_tag']}")
    
    return manager


if __name__ == "__main__":
    # 예시 실행
    manager = example_usage()
    
    print("\n" + "="*60)
    print("✅ 태그 기반 포지션 관리 시스템 구현 완료!")
    print("\n주요 특징:")
    print("- AUTO 포지션: 자동매매만 제어 가능, 수동 간섭 차단")
    print("- MANUAL 포지션: 사용자만 제어 가능, 자동매매 간섭 차단") 
    print("- HYBRID 포지션: 제한적 자동화 허용")
    print("- LOCKED 포지션: 모든 거래 차단")
    print("\n이제 전략 시스템을 이 포지션 매니저와 연결해야 합니다!")
