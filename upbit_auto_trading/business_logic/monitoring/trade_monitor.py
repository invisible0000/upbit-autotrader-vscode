"""
거래 모니터링 모듈

이 모듈은 거래 모니터링 기능을 제공합니다.
- 주문 체결 알림
- 수익/손실 알림
- 포지션 변경 알림
"""

import os
import json
import threading
import time
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

from upbit_auto_trading.ui.desktop.models.notification import NotificationType
from .alert_manager import AlertManager


class TradeMonitor:
    """거래 모니터링 클래스"""
    
    def __init__(self, alert_manager: AlertManager):
        """초기화
        
        Args:
            alert_manager: 알림 관리자 객체
        """
        self.alert_manager = alert_manager
        self.monitored_orders: Dict[str, Dict[str, Any]] = {}  # uuid -> order_data
        self.monitored_positions: Dict[str, Dict[str, Any]] = {}  # symbol -> position_data
        self.notified_profits: Set[str] = set()  # 이미 수익 알림을 보낸 심볼 집합
        self.notified_losses: Set[str] = set()  # 이미 손실 알림을 보낸 심볼 집합
        
        # 알림 설정
        self.order_notification_enabled = True
        self.profit_loss_notification_enabled = True
        self.position_notification_enabled = True
        
        # 수익/손실 임계값 (%)
        self.profit_threshold = 5.0
        self.loss_threshold = 3.0
        
        # 모니터링 스레드
        self.monitoring_thread = None
        self.is_monitoring = False
        self.monitoring_interval = 10  # 초 단위
    
    def add_order_to_monitor(self, order_id: str, order_data: Dict[str, Any]):
        """모니터링할 주문 추가
        
        Args:
            order_id: 주문 ID
            order_data: 주문 데이터
        """
        self.monitored_orders[order_id] = order_data
    
    def remove_order_from_monitor(self, order_id: str) -> bool:
        """모니터링 중인 주문 제거
        
        Args:
            order_id: 주문 ID
            
        Returns:
            bool: 성공 여부
        """
        if order_id in self.monitored_orders:
            del self.monitored_orders[order_id]
            return True
        return False
    
    def update_order_status(self, order_id: str, order_data: Dict[str, Any]):
        """주문 상태 업데이트
        
        Args:
            order_id: 주문 ID
            order_data: 업데이트된 주문 데이터
        """
        if order_id not in self.monitored_orders:
            self.monitored_orders[order_id] = order_data
            return
        
        old_order = self.monitored_orders[order_id]
        
        # 주문 상태 변경 확인
        if old_order["state"] != "done" and order_data["state"] == "done":
            # 주문 체결 알림
            if self.order_notification_enabled:
                self._notify_order_executed(order_data)
        
        # 주문 데이터 업데이트
        self.monitored_orders[order_id] = order_data
    
    def add_position_to_monitor(self, symbol: str, position_data: Dict[str, Any]):
        """모니터링할 포지션 추가
        
        Args:
            symbol: 코인 심볼
            position_data: 포지션 데이터
        """
        self.monitored_positions[symbol] = position_data
    
    def remove_position_from_monitor(self, symbol: str) -> bool:
        """모니터링 중인 포지션 제거
        
        Args:
            symbol: 코인 심볼
            
        Returns:
            bool: 성공 여부
        """
        if symbol in self.monitored_positions:
            del self.monitored_positions[symbol]
            if symbol in self.notified_profits:
                self.notified_profits.remove(symbol)
            if symbol in self.notified_losses:
                self.notified_losses.remove(symbol)
            return True
        return False
    
    def update_position(self, symbol: str, position_data: Dict[str, Any]):
        """포지션 상태 업데이트
        
        Args:
            symbol: 코인 심볼
            position_data: 업데이트된 포지션 데이터
        """
        if symbol not in self.monitored_positions:
            self.monitored_positions[symbol] = position_data
            return
        
        old_position = self.monitored_positions[symbol]
        
        # 수익/손실 알림
        if self.profit_loss_notification_enabled:
            profit_loss_percentage = position_data.get("profit_loss_percentage", 0)
            
            # 수익 임계값 초과 시 알림
            if (profit_loss_percentage >= self.profit_threshold and 
                symbol not in self.notified_profits):
                self._notify_profit_threshold_reached(symbol, position_data)
                self.notified_profits.add(symbol)
            
            # 손실 임계값 초과 시 알림
            if (profit_loss_percentage <= -self.loss_threshold and 
                symbol not in self.notified_losses):
                self._notify_loss_threshold_reached(symbol, position_data)
                self.notified_losses.add(symbol)
        
        # 포지션 데이터 업데이트
        self.monitored_positions[symbol] = position_data
    
    def notify_position_opened(self, symbol: str, position_data: Dict[str, Any]):
        """포지션 생성 알림
        
        Args:
            symbol: 코인 심볼
            position_data: 포지션 데이터
        """
        if not self.position_notification_enabled:
            return
        
        # 포지션 추가
        self.add_position_to_monitor(symbol, position_data)
        
        # 포지션 생성 알림
        side = "매수" if position_data.get("side") == "long" else "매도"
        price = position_data.get("entry_price", 0)
        quantity = position_data.get("quantity", 0)
        
        message = (f"{symbol} {side} 포지션이 생성되었습니다. "
                  f"진입 가격: {price:,}원, 수량: {quantity} {symbol.split('-')[1]}")
        
        self.alert_manager.add_notification(
            notification_type=NotificationType.TRADE_ALERT,
            title="포지션 생성 알림",
            message=message,
            related_symbol=symbol
        )
    
    def notify_position_closed(self, symbol: str, position_data: Dict[str, Any]):
        """포지션 종료 알림
        
        Args:
            symbol: 코인 심볼
            position_data: 포지션 데이터
        """
        if not self.position_notification_enabled:
            return
        
        # 포지션 종료 알림
        side = "매수" if position_data.get("side") == "long" else "매도"
        entry_price = position_data.get("entry_price", 0)
        exit_price = position_data.get("current_price", 0)
        quantity = position_data.get("quantity", 0)
        profit_loss = position_data.get("profit_loss", 0)
        profit_loss_percentage = position_data.get("profit_loss_percentage", 0)
        
        message = (f"{symbol} {side} 포지션이 종료되었습니다. "
                  f"진입 가격: {entry_price:,}원, 종료 가격: {exit_price:,}원, "
                  f"수량: {quantity} {symbol.split('-')[1]}, "
                  f"손익: {profit_loss:,}원 ({profit_loss_percentage:.2f}%)")
        
        self.alert_manager.add_notification(
            notification_type=NotificationType.TRADE_ALERT,
            title="포지션 종료 알림",
            message=message,
            related_symbol=symbol
        )
        
        # 모니터링 목록에서 제거
        self.remove_position_from_monitor(symbol)
    
    def _notify_order_executed(self, order_data: Dict[str, Any]):
        """주문 체결 알림
        
        Args:
            order_data: 주문 데이터
        """
        market = order_data.get("market", "")
        side = "매수" if order_data.get("side") == "bid" else "매도"
        price = order_data.get("price", 0)
        volume = order_data.get("executed_volume", 0)
        
        message = (f"{market} {side} 주문이 체결되었습니다. "
                  f"체결 가격: {price:,}원, 수량: {volume} {market.split('-')[1]}")
        
        self.alert_manager.add_notification(
            notification_type=NotificationType.TRADE_ALERT,
            title="주문 체결 알림",
            message=message,
            related_symbol=market
        )
    
    def _notify_profit_threshold_reached(self, symbol: str, position_data: Dict[str, Any]):
        """수익 임계값 도달 알림
        
        Args:
            symbol: 코인 심볼
            position_data: 포지션 데이터
        """
        entry_price = position_data.get("entry_price", 0)
        current_price = position_data.get("current_price", 0)
        profit_loss_percentage = position_data.get("profit_loss_percentage", 0)
        
        message = (f"{symbol} 포지션이 수익 임계값에 도달했습니다. "
                  f"진입 가격: {entry_price:,}원, 현재 가격: {current_price:,}원, "
                  f"수익률: {profit_loss_percentage:.2f}%")
        
        self.alert_manager.add_notification(
            notification_type=NotificationType.TRADE_ALERT,
            title="수익 알림",
            message=message,
            related_symbol=symbol
        )
    
    def _notify_loss_threshold_reached(self, symbol: str, position_data: Dict[str, Any]):
        """손실 임계값 도달 알림
        
        Args:
            symbol: 코인 심볼
            position_data: 포지션 데이터
        """
        entry_price = position_data.get("entry_price", 0)
        current_price = position_data.get("current_price", 0)
        profit_loss_percentage = position_data.get("profit_loss_percentage", 0)
        
        message = (f"{symbol} 포지션이 손실 임계값에 도달했습니다. "
                  f"진입 가격: {entry_price:,}원, 현재 가격: {current_price:,}원, "
                  f"손실률: {abs(profit_loss_percentage):.2f}%")
        
        self.alert_manager.add_notification(
            notification_type=NotificationType.TRADE_ALERT,
            title="손실 알림",
            message=message,
            related_symbol=symbol
        )
    
    def start_monitoring(self, trade_data_provider):
        """모니터링 시작
        
        Args:
            trade_data_provider: 거래 데이터 제공 객체 (get_orders, get_positions 메서드 필요)
        """
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        
        def monitoring_task():
            while self.is_monitoring:
                try:
                    # 주문 데이터 가져오기
                    orders = trade_data_provider.get_orders()
                    for order_id, order_data in orders.items():
                        self.update_order_status(order_id, order_data)
                    
                    # 포지션 데이터 가져오기
                    positions = trade_data_provider.get_positions()
                    for symbol, position_data in positions.items():
                        self.update_position(symbol, position_data)
                    
                except Exception as e:
                    print(f"거래 모니터링 중 오류 발생: {e}")
                
                # 대기
                time.sleep(self.monitoring_interval)
        
        # 모니터링 스레드 시작
        self.monitoring_thread = threading.Thread(target=monitoring_task, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.is_monitoring = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=1.0)
    
    def set_monitoring_interval(self, interval: int):
        """모니터링 간격 설정
        
        Args:
            interval: 모니터링 간격 (초)
        """
        self.monitoring_interval = max(1, interval)  # 최소 1초
    
    def set_profit_threshold(self, threshold: float):
        """수익 임계값 설정
        
        Args:
            threshold: 수익 임계값 (%)
        """
        self.profit_threshold = max(0.1, threshold)
        # 임계값 변경 시 알림 상태 초기화
        self.notified_profits.clear()
    
    def set_loss_threshold(self, threshold: float):
        """손실 임계값 설정
        
        Args:
            threshold: 손실 임계값 (%)
        """
        self.loss_threshold = max(0.1, threshold)
        # 임계값 변경 시 알림 상태 초기화
        self.notified_losses.clear()
    
    def set_order_notification_enabled(self, enabled: bool):
        """주문 알림 활성화 여부 설정
        
        Args:
            enabled: 활성화 여부
        """
        self.order_notification_enabled = enabled
    
    def set_profit_loss_notification_enabled(self, enabled: bool):
        """수익/손실 알림 활성화 여부 설정
        
        Args:
            enabled: 활성화 여부
        """
        self.profit_loss_notification_enabled = enabled
        if enabled:
            # 활성화 시 알림 상태 초기화
            self.notified_profits.clear()
            self.notified_losses.clear()
    
    def set_position_notification_enabled(self, enabled: bool):
        """포지션 알림 활성화 여부 설정
        
        Args:
            enabled: 활성화 여부
        """
        self.position_notification_enabled = enabled
    
    def is_order_notification_enabled(self) -> bool:
        """주문 알림 활성화 여부 반환
        
        Returns:
            bool: 활성화 여부
        """
        return self.order_notification_enabled
    
    def is_profit_loss_notification_enabled(self) -> bool:
        """수익/손실 알림 활성화 여부 반환
        
        Returns:
            bool: 활성화 여부
        """
        return self.profit_loss_notification_enabled
    
    def is_position_notification_enabled(self) -> bool:
        """포지션 알림 활성화 여부 반환
        
        Returns:
            bool: 활성화 여부
        """
        return self.position_notification_enabled
    
    def save_settings(self, file_path: str) -> bool:
        """알림 설정 저장
        
        Args:
            file_path: 저장할 파일 경로
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 디렉토리 경로 확인
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # 설정 데이터
            settings = {
                "order_notification_enabled": self.order_notification_enabled,
                "profit_loss_notification_enabled": self.profit_loss_notification_enabled,
                "position_notification_enabled": self.position_notification_enabled,
                "profit_threshold": self.profit_threshold,
                "loss_threshold": self.loss_threshold,
                "monitoring_interval": self.monitoring_interval
            }
            
            # JSON 파일로 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"알림 설정 저장 중 오류 발생: {e}")
            return False
    
    def load_settings(self, file_path: str) -> bool:
        """알림 설정 로드
        
        Args:
            file_path: 로드할 파일 경로
            
        Returns:
            bool: 성공 여부
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            # JSON 파일에서 로드
            with open(file_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # 설정 적용
            self.order_notification_enabled = settings.get("order_notification_enabled", True)
            self.profit_loss_notification_enabled = settings.get("profit_loss_notification_enabled", True)
            self.position_notification_enabled = settings.get("position_notification_enabled", True)
            self.profit_threshold = settings.get("profit_threshold", 5.0)
            self.loss_threshold = settings.get("loss_threshold", 3.0)
            self.monitoring_interval = settings.get("monitoring_interval", 10)
            
            return True
        except Exception as e:
            print(f"알림 설정 로드 중 오류 발생: {e}")
            return False