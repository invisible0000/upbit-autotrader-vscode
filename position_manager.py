#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
포지션 관리 시스템

실시간 포지션 생성, 수정, 청산을 관리하는 시스템:
- 포지션 ID 기반 추적
- 포트폴리오별 포지션 관리
- 리스크 관리 통합
- 실시간 손익 계산
- 포지션 이력 추적
"""

import os
import sys
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)


class PositionStatus(Enum):
    """포지션 상태"""
    OPEN = "open"
    PARTIAL_CLOSED = "partial_closed"
    CLOSED = "closed"
    STOPPED_OUT = "stopped_out"


class PositionAction(Enum):
    """포지션 액션"""
    OPEN = "OPEN"
    ADD = "ADD"
    REDUCE = "REDUCE"
    CLOSE = "CLOSE"
    UPDATE_STOP = "UPDATE_STOP"
    UPDATE_TARGET = "UPDATE_TARGET"


@dataclass
class Position:
    """포지션 정보"""
    position_id: str
    portfolio_id: str
    symbol: str
    direction: str  # 'BUY' | 'SELL'
    
    # 가격 정보
    entry_price: float
    current_price: float
    quantity: float
    remaining_quantity: float
    
    # 손익 정보
    unrealized_pnl_percent: float = 0.0
    unrealized_pnl_amount: float = 0.0
    realized_pnl_amount: float = 0.0
    
    # 리스크 관리
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    trailing_stop_price: Optional[float] = None
    max_position_value: Optional[float] = None
    
    # 전략 정보
    entry_strategy_id: Optional[str] = None
    entry_reason: Optional[str] = None
    management_actions: List[Dict[str, Any]] = field(default_factory=list)
    
    # 상태 관리
    status: PositionStatus = PositionStatus.OPEN
    opened_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None
    
    def calculate_pnl(self, current_price: Optional[float] = None) -> Tuple[float, float]:
        """손익 계산 (퍼센트, 금액)"""
        price = current_price or self.current_price
        
        if self.direction == 'BUY':
            pnl_percent = (price - self.entry_price) / self.entry_price
        else:  # SELL
            pnl_percent = (self.entry_price - price) / self.entry_price
        
        pnl_amount = pnl_percent * self.entry_price * self.remaining_quantity
        
        return pnl_percent, pnl_amount
    
    def get_position_value(self, current_price: Optional[float] = None) -> float:
        """포지션 가치 계산"""
        price = current_price or self.current_price
        return price * self.remaining_quantity
    
    def is_stop_triggered(self, current_price: float) -> bool:
        """손절 트리거 확인"""
        if not self.stop_loss_price:
            return False
        
        if self.direction == 'BUY':
            return current_price <= self.stop_loss_price
        else:  # SELL
            return current_price >= self.stop_loss_price
    
    def is_target_triggered(self, current_price: float) -> bool:
        """익절 트리거 확인"""
        if not self.take_profit_price:
            return False
        
        if self.direction == 'BUY':
            return current_price >= self.take_profit_price
        else:  # SELL
            return current_price <= self.take_profit_price


@dataclass
class PositionUpdate:
    """포지션 업데이트 정보"""
    action: PositionAction
    price: float
    quantity: float = 0.0
    strategy_name: Optional[str] = None
    reason: Optional[str] = None
    triggered_by: str = "manual"  # 'strategy', 'manual', 'risk_management'
    
    # 리스크 관리 업데이트
    new_stop_price: Optional[float] = None
    new_target_price: Optional[float] = None


class PositionManager:
    """포지션 관리자"""
    
    def __init__(self, db_path: str = "data/upbit_auto_trading.sqlite3"):
        self.db_path = db_path
        self._positions_cache: Dict[str, Position] = {}
    
    def get_connection(self) -> sqlite3.Connection:
        """데이터베이스 연결 반환"""
        return sqlite3.connect(self.db_path)
    
    def create_position(self, portfolio_id: str, symbol: str, direction: str,
                       entry_price: float, quantity: float,
                       entry_strategy_id: Optional[str] = None,
                       entry_reason: Optional[str] = None,
                       risk_settings: Optional[Dict[str, Any]] = None) -> Position:
        """새 포지션 생성"""
        
        # 포지션 ID 생성
        position_id = f"pos_{symbol}_{direction}_{uuid.uuid4().hex[:8]}"
        
        # 포지션 객체 생성
        position = Position(
            position_id=position_id,
            portfolio_id=portfolio_id,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            current_price=entry_price,
            quantity=quantity,
            remaining_quantity=quantity,
            entry_strategy_id=entry_strategy_id,
            entry_reason=entry_reason or "Manual entry"
        )
        
        # 리스크 설정 적용
        if risk_settings:
            self._apply_risk_settings(position, risk_settings)
        
        # 데이터베이스에 저장
        self._save_position_to_db(position)
        
        # 포지션 이력 기록
        self._add_position_history(position_id, PositionUpdate(
            action=PositionAction.OPEN,
            price=entry_price,
            quantity=quantity,
            strategy_name=entry_strategy_id,
            reason=entry_reason or "Position opened",
            triggered_by="strategy" if entry_strategy_id else "manual"
        ))
        
        # 캐시에 저장
        self._positions_cache[position_id] = position
        
        print(f"✅ 포지션 생성: {position_id}")
        print(f"   {symbol} {direction} {quantity} @ {entry_price:,.0f}")
        
        return position
    
    def update_position(self, position_id: str, update: PositionUpdate) -> Position:
        """포지션 업데이트"""
        position = self.get_position(position_id)
        if not position:
            raise ValueError(f"포지션을 찾을 수 없습니다: {position_id}")
        
        old_stop_price = position.stop_loss_price
        old_target_price = position.take_profit_price
        
        # 액션에 따른 업데이트 처리
        if update.action == PositionAction.ADD:
            # 추가 매수/매도
            total_cost = position.entry_price * position.quantity + update.price * update.quantity
            total_quantity = position.quantity + update.quantity
            position.entry_price = total_cost / total_quantity  # 평균 단가 재계산
            position.quantity = total_quantity
            position.remaining_quantity += update.quantity
            
        elif update.action == PositionAction.REDUCE:
            # 부분 청산
            if update.quantity > position.remaining_quantity:
                raise ValueError("청산 수량이 잔여 수량보다 큽니다")
            
            # 실현 손익 계산
            pnl_percent, _ = position.calculate_pnl(update.price)
            realized_pnl = pnl_percent * position.entry_price * update.quantity
            position.realized_pnl_amount += realized_pnl
            position.remaining_quantity -= update.quantity
            
            if position.remaining_quantity <= 0:
                position.status = PositionStatus.CLOSED
                position.closed_at = datetime.now()
            else:
                position.status = PositionStatus.PARTIAL_CLOSED
                
        elif update.action == PositionAction.CLOSE:
            # 전체 청산
            pnl_percent, _ = position.calculate_pnl(update.price)
            realized_pnl = pnl_percent * position.entry_price * position.remaining_quantity
            position.realized_pnl_amount += realized_pnl
            position.remaining_quantity = 0
            position.status = PositionStatus.CLOSED
            position.closed_at = datetime.now()
            
        elif update.action == PositionAction.UPDATE_STOP:
            # 손절가 업데이트
            position.stop_loss_price = update.new_stop_price
            
        elif update.action == PositionAction.UPDATE_TARGET:
            # 익절가 업데이트
            position.take_profit_price = update.new_target_price
        
        # 현재가 업데이트
        position.current_price = update.price
        position.updated_at = datetime.now()
        
        # 미실현 손익 재계산
        position.unrealized_pnl_percent, position.unrealized_pnl_amount = \
            position.calculate_pnl()
        
        # 관리 액션 기록
        action_record = {
            'timestamp': datetime.now().isoformat(),
            'action': update.action.value,
            'price': update.price,
            'quantity': update.quantity,
            'strategy_name': update.strategy_name,
            'reason': update.reason
        }
        position.management_actions.append(action_record)
        
        # 데이터베이스 업데이트
        self._update_position_in_db(position)
        
        # 포지션 이력 기록
        history_update = PositionUpdate(
            action=update.action,
            price=update.price,
            quantity=update.quantity,
            strategy_name=update.strategy_name,
            reason=update.reason,
            triggered_by=update.triggered_by
        )
        history_update.new_stop_price = update.new_stop_price
        history_update.new_target_price = update.new_target_price
        
        self._add_position_history(position_id, history_update, old_stop_price, old_target_price)
        
        # 캐시 업데이트
        self._positions_cache[position_id] = position
        
        print(f"✅ 포지션 업데이트: {position_id} - {update.action.value}")
        
        return position
    
    def get_position(self, position_id: str) -> Optional[Position]:
        """포지션 조회"""
        # 캐시에서 먼저 확인
        if position_id in self._positions_cache:
            return self._positions_cache[position_id]
        
        # 데이터베이스에서 조회
        position = self._load_position_from_db(position_id)
        if position:
            self._positions_cache[position_id] = position
        
        return position
    
    def get_portfolio_positions(self, portfolio_id: str, 
                              status_filter: Optional[List[PositionStatus]] = None) -> List[Position]:
        """포트폴리오의 포지션 목록 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = "SELECT position_id FROM positions WHERE portfolio_id = ?"
            params = [portfolio_id]
            
            if status_filter:
                status_list = [status.value for status in status_filter]
                placeholders = ','.join(['?' for _ in status_list])
                query += f" AND status IN ({placeholders})"
                params.extend(status_list)
            
            cursor.execute(query, params)
            position_ids = [row[0] for row in cursor.fetchall()]
            
            positions = []
            for position_id in position_ids:
                position = self.get_position(position_id)
                if position:
                    positions.append(position)
            
            return positions
            
        finally:
            conn.close()
    
    def get_symbol_positions(self, symbol: str,
                           status_filter: Optional[List[PositionStatus]] = None) -> List[Position]:
        """특정 심볼의 포지션 목록 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = "SELECT position_id FROM positions WHERE symbol = ?"
            params = [symbol]
            
            if status_filter:
                status_list = [status.value for status in status_filter]
                placeholders = ','.join(['?' for _ in status_list])
                query += f" AND status IN ({placeholders})"
                params.extend(status_list)
            
            cursor.execute(query, params)
            position_ids = [row[0] for row in cursor.fetchall()]
            
            positions = []
            for position_id in position_ids:
                position = self.get_position(position_id)
                if position:
                    positions.append(position)
            
            return positions
            
        finally:
            conn.close()
    
    def update_positions_price(self, symbol: str, current_price: float) -> List[Position]:
        """특정 심볼의 모든 열린 포지션 가격 업데이트"""
        positions = self.get_symbol_positions(symbol, [PositionStatus.OPEN, PositionStatus.PARTIAL_CLOSED])
        updated_positions = []
        
        for position in positions:
            # 가격 업데이트
            old_price = position.current_price
            position.current_price = current_price
            position.updated_at = datetime.now()
            
            # 손익 재계산
            position.unrealized_pnl_percent, position.unrealized_pnl_amount = \
                position.calculate_pnl()
            
            # 데이터베이스 업데이트
            self._update_position_price_in_db(position.position_id, current_price)
            
            # 캐시 업데이트
            self._positions_cache[position.position_id] = position
            
            updated_positions.append(position)
        
        if updated_positions:
            print(f"✅ {symbol} 포지션 가격 업데이트: {len(updated_positions)}개 @ {current_price:,.0f}")
        
        return updated_positions
    
    def check_risk_triggers(self, symbol: str, current_price: float) -> List[Tuple[Position, str]]:
        """리스크 관리 트리거 확인"""
        positions = self.get_symbol_positions(symbol, [PositionStatus.OPEN, PositionStatus.PARTIAL_CLOSED])
        triggered = []
        
        for position in positions:
            if position.is_stop_triggered(current_price):
                triggered.append((position, "STOP_LOSS"))
            elif position.is_target_triggered(current_price):
                triggered.append((position, "TAKE_PROFIT"))
        
        return triggered
    
    def _apply_risk_settings(self, position: Position, risk_settings: Dict[str, Any]) -> None:
        """리스크 설정 적용"""
        stop_loss_percent = risk_settings.get('stop_loss_percent')
        take_profit_percent = risk_settings.get('take_profit_percent')
        
        if stop_loss_percent:
            if position.direction == 'BUY':
                position.stop_loss_price = position.entry_price * (1 - stop_loss_percent)
            else:
                position.stop_loss_price = position.entry_price * (1 + stop_loss_percent)
        
        if take_profit_percent:
            if position.direction == 'BUY':
                position.take_profit_price = position.entry_price * (1 + take_profit_percent)
            else:
                position.take_profit_price = position.entry_price * (1 - take_profit_percent)
        
        position.max_position_value = risk_settings.get('max_position_value')
    
    def _save_position_to_db(self, position: Position) -> None:
        """포지션을 데이터베이스에 저장"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO positions (
                    position_id, portfolio_id, symbol, direction,
                    entry_price, current_price, quantity, remaining_quantity,
                    unrealized_pnl_percent, unrealized_pnl_amount, realized_pnl_amount,
                    stop_loss_price, take_profit_price, trailing_stop_price, max_position_value,
                    entry_strategy_id, entry_reason, management_actions,
                    status, opened_at, updated_at, closed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                position.position_id, position.portfolio_id, position.symbol, position.direction,
                position.entry_price, position.current_price, position.quantity, position.remaining_quantity,
                position.unrealized_pnl_percent, position.unrealized_pnl_amount, position.realized_pnl_amount,
                position.stop_loss_price, position.take_profit_price, position.trailing_stop_price, position.max_position_value,
                position.entry_strategy_id, position.entry_reason, json.dumps(position.management_actions),
                position.status.value, position.opened_at.isoformat(), position.updated_at.isoformat(),
                position.closed_at.isoformat() if position.closed_at else None
            ))
            conn.commit()
        finally:
            conn.close()
    
    def _update_position_in_db(self, position: Position) -> None:
        """데이터베이스의 포지션 정보 업데이트"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE positions SET
                    current_price = ?, quantity = ?, remaining_quantity = ?,
                    unrealized_pnl_percent = ?, unrealized_pnl_amount = ?, realized_pnl_amount = ?,
                    stop_loss_price = ?, take_profit_price = ?, trailing_stop_price = ?,
                    management_actions = ?, status = ?, updated_at = ?, closed_at = ?
                WHERE position_id = ?
            """, (
                position.current_price, position.quantity, position.remaining_quantity,
                position.unrealized_pnl_percent, position.unrealized_pnl_amount, position.realized_pnl_amount,
                position.stop_loss_price, position.take_profit_price, position.trailing_stop_price,
                json.dumps(position.management_actions), position.status.value,
                position.updated_at.isoformat(), 
                position.closed_at.isoformat() if position.closed_at else None,
                position.position_id
            ))
            conn.commit()
        finally:
            conn.close()
    
    def _update_position_price_in_db(self, position_id: str, current_price: float) -> None:
        """데이터베이스의 포지션 가격만 업데이트"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE positions SET current_price = ?, updated_at = ?
                WHERE position_id = ?
            """, (current_price, datetime.now().isoformat(), position_id))
            conn.commit()
        finally:
            conn.close()
    
    def _load_position_from_db(self, position_id: str) -> Optional[Position]:
        """데이터베이스에서 포지션 로드"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT portfolio_id, symbol, direction, entry_price, current_price,
                       quantity, remaining_quantity, unrealized_pnl_percent,
                       unrealized_pnl_amount, realized_pnl_amount,
                       stop_loss_price, take_profit_price, trailing_stop_price, max_position_value,
                       entry_strategy_id, entry_reason, management_actions,
                       status, opened_at, updated_at, closed_at
                FROM positions WHERE position_id = ?
            """, (position_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # 포지션 객체 생성
            position = Position(
                position_id=position_id,
                portfolio_id=row[0],
                symbol=row[1],
                direction=row[2],
                entry_price=row[3],
                current_price=row[4],
                quantity=row[5],
                remaining_quantity=row[6],
                unrealized_pnl_percent=row[7],
                unrealized_pnl_amount=row[8],
                realized_pnl_amount=row[9],
                stop_loss_price=row[10],
                take_profit_price=row[11],
                trailing_stop_price=row[12],
                max_position_value=row[13],
                entry_strategy_id=row[14],
                entry_reason=row[15],
                management_actions=json.loads(row[16]) if row[16] else [],
                status=PositionStatus(row[17]),
                opened_at=datetime.fromisoformat(row[18]),
                updated_at=datetime.fromisoformat(row[19]),
                closed_at=datetime.fromisoformat(row[20]) if row[20] else None
            )
            
            return position
            
        finally:
            conn.close()
    
    def _add_position_history(self, position_id: str, update: PositionUpdate,
                            old_stop_price: Optional[float] = None,
                            old_target_price: Optional[float] = None) -> None:
        """포지션 이력 추가"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO position_history (
                    position_id, timestamp, action, price, quantity_change, quantity_after,
                    strategy_name, reason, triggered_by,
                    stop_price_before, stop_price_after,
                    target_price_before, target_price_after
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                position_id,
                datetime.now().isoformat(),
                update.action.value,
                update.price,
                update.quantity,
                0,  # quantity_after는 포지션에서 계산
                update.strategy_name,
                update.reason,
                update.triggered_by,
                old_stop_price,
                update.new_stop_price,
                old_target_price,
                update.new_target_price
            ))
            conn.commit()
        finally:
            conn.close()


def main():
    """테스트 실행"""
    print("🧪 포지션 관리 시스템 테스트")
    
    manager = PositionManager()
    
    # 1. 새 포지션 생성
    position = manager.create_position(
        portfolio_id="backtest_portfolio_1",
        symbol="KRW-BTC",
        direction="BUY",
        entry_price=50000000,
        quantity=0.1,
        entry_strategy_id="rsi_config_1",
        entry_reason="RSI oversold signal",
        risk_settings={
            "stop_loss_percent": 0.05,
            "take_profit_percent": 0.10
        }
    )
    
    print(f"생성된 포지션: {position.position_id}")
    print(f"진입가: {position.entry_price:,.0f}")
    print(f"손절가: {position.stop_loss_price:,.0f}")
    print(f"익절가: {position.take_profit_price:,.0f}")
    
    # 2. 가격 업데이트
    new_price = 52000000
    updated_positions = manager.update_positions_price("KRW-BTC", new_price)
    print(f"가격 업데이트 후 손익: {position.unrealized_pnl_percent:.2%}")
    
    # 3. 포지션 부분 청산
    manager.update_position(position.position_id, PositionUpdate(
        action=PositionAction.REDUCE,
        price=52000000,
        quantity=0.05,
        reason="Partial profit taking",
        triggered_by="manual"
    ))
    
    # 4. 포트폴리오 포지션 조회
    portfolio_positions = manager.get_portfolio_positions("backtest_portfolio_1")
    print(f"포트폴리오 포지션 수: {len(portfolio_positions)}")
    
    print("✅ 포지션 관리 시스템 테스트 완료")


if __name__ == "__main__":
    main()
