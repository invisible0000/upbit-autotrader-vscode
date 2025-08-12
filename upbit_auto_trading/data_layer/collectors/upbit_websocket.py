#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
업비트 웹소켓 클라이언트

실시간 시세 데이터를 수신하는 웹소켓 클라이언트를 제공합니다.
"""

import json
import logging
import threading
import time
import uuid
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

try:
    import websocket
except ImportError:
    # websocket-client 패키지가 없는 경우 설치 안내
    logging.warning("websocket-client 패키지가 설치되지 않았습니다. 'pip install websocket-client' 명령으로 설치하세요.")
    websocket = None

logger = logging.getLogger(__name__)

class UpbitWebSocket:
    """업비트 웹소켓 클라이언트"""
    
    def __init__(self):
        self.ws = None
        self.is_connected = False
        self.is_running = False
        self.callbacks = {}
        self.subscriptions = []
        self.reconnect_interval = 5
        self.max_reconnect_attempts = 10
        self.reconnect_count = 0
        
        # 웹소켓 URL
        self.ws_url = "wss://api.upbit.com/websocket/v1"
        
        # 스레드 관리
        self.ws_thread = None
        self.reconnect_thread = None
        
    def connect(self):
        """웹소켓 연결"""
        if websocket is None:
            logger.error("websocket-client 패키지가 설치되지 않았습니다.")
            return False
            
        try:
            logger.info("업비트 웹소켓 연결 시도...")
            
            # 웹소켓 옵션 설정
            websocket.enableTrace(False)
            
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # 별도 스레드에서 웹소켓 실행
            self.is_running = True
            self.ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
            self.ws_thread.start()
            
            # 연결 완료까지 대기 (최대 10초)
            wait_count = 0
            while not self.is_connected and wait_count < 100:
                time.sleep(0.1)
                wait_count += 1
                
            if self.is_connected:
                logger.info("업비트 웹소켓 연결 성공")
                return True
            else:
                logger.error("업비트 웹소켓 연결 실패")
                return False
                
        except Exception as e:
            logger.error(f"웹소켓 연결 중 오류: {e}")
            return False
    
    def disconnect(self):
        """웹소켓 연결 해제"""
        try:
            logger.info("업비트 웹소켓 연결 해제...")
            self.is_running = False
            self.is_connected = False
            
            if self.ws:
                self.ws.close()
                
            # 스레드 종료 대기
            if self.ws_thread and self.ws_thread.is_alive():
                self.ws_thread.join(timeout=5)
                
            if self.reconnect_thread and self.reconnect_thread.is_alive():
                self.reconnect_thread.join(timeout=5)
                
            logger.info("웹소켓 연결 해제 완료")
            
        except Exception as e:
            logger.error(f"웹소켓 연결 해제 중 오류: {e}")
    
    def subscribe_ticker(self, symbols: List[str], callback: Callable[[Dict], None]):
        """현재가 구독
        
        Args:
            symbols: 구독할 심볼 리스트 (예: ["KRW-BTC", "KRW-ETH"])
            callback: 데이터 수신 시 호출될 콜백 함수
        """
        if not self.is_connected:
            logger.warning("웹소켓이 연결되지 않았습니다.")
            return False
            
        try:
            subscription = {
                "ticket": str(uuid.uuid4()),
                "type": "ticker",
                "codes": symbols,
                "isOnlySnapshot": False,
                "isOnlyRealtime": True
            }
            
            # 콜백 등록
            self.callbacks["ticker"] = callback
            
            # 구독 요청 전송
            message = json.dumps([subscription])
            self.ws.send(message)
            
            # 구독 정보 저장
            self.subscriptions.append({
                "type": "ticker",
                "symbols": symbols,
                "callback": callback
            })
            
            logger.info(f"현재가 구독 완료: {symbols}")
            return True
            
        except Exception as e:
            logger.error(f"현재가 구독 중 오류: {e}")
            return False
    
    def subscribe_orderbook(self, symbols: List[str], callback: Callable[[Dict], None]):
        """호가 구독
        
        Args:
            symbols: 구독할 심볼 리스트
            callback: 데이터 수신 시 호출될 콜백 함수
        """
        if not self.is_connected:
            logger.warning("웹소켓이 연결되지 않았습니다.")
            return False
            
        try:
            subscription = {
                "ticket": str(uuid.uuid4()),
                "type": "orderbook",
                "codes": symbols,
                "isOnlySnapshot": False,
                "isOnlyRealtime": True
            }
            
            # 콜백 등록
            self.callbacks["orderbook"] = callback
            
            # 구독 요청 전송
            message = json.dumps([subscription])
            self.ws.send(message)
            
            # 구독 정보 저장
            self.subscriptions.append({
                "type": "orderbook",
                "symbols": symbols,
                "callback": callback
            })
            
            logger.info(f"호가 구독 완료: {symbols}")
            return True
            
        except Exception as e:
            logger.error(f"호가 구독 중 오류: {e}")
            return False
    
    def subscribe_trade(self, symbols: List[str], callback: Callable[[Dict], None]):
        """체결 구독
        
        Args:
            symbols: 구독할 심볼 리스트
            callback: 데이터 수신 시 호출될 콜백 함수
        """
        if not self.is_connected:
            logger.warning("웹소켓이 연결되지 않았습니다.")
            return False
            
        try:
            # 업비트 웹소켓 구독 형식에 맞춰 수정
            subscription = [
                {"ticket": str(uuid.uuid4())},
                {
                    "type": "trade",
                    "codes": symbols,
                    "isOnlySnapshot": False,
                    "isOnlyRealtime": True
                }
            ]
            
            # 콜백 등록
            self.callbacks["trade"] = callback
            
            # 구독 요청 전송
            message = json.dumps(subscription)
            self.ws.send(message)
            
            # 구독 정보 저장
            self.subscriptions.append({
                "type": "trade",
                "symbols": symbols,
                "callback": callback
            })
            
            logger.info(f"체결 구독 완료: {symbols}")
            logger.debug(f"구독 메시지: {message}")
            return True
            
        except Exception as e:
            logger.error(f"체결 구독 중 오류: {e}")
            return False
    
    def _run_websocket(self):
        """웹소켓 실행 (별도 스레드)"""
        try:
            self.ws.run_forever()
        except Exception as e:
            logger.error(f"웹소켓 실행 중 오류: {e}")
            if self.is_running:
                self._schedule_reconnect()
    
    def _on_open(self, ws):
        """웹소켓 연결 성공"""
        logger.info("웹소켓 연결됨")
        self.is_connected = True
        self.reconnect_count = 0
    
    def _on_message(self, ws, message):
        """웹소켓 메시지 수신"""
        try:
            # 바이너리 데이터를 JSON으로 변환
            if isinstance(message, bytes):
                message = message.decode('utf-8')
                
            data = json.loads(message)
            
            # 업비트 API 응답 구조에 맞춰 처리
            message_type = data.get('type', data.get('ty', ''))
            
            # 체결 데이터 처리
            if message_type == 'trade' or 'trade_price' in data:
                if 'trade' in self.callbacks:
                    self.callbacks['trade'](data)
                    
            # 현재가 데이터 처리  
            elif message_type == 'ticker' or 'trade_price' in data:
                if 'ticker' in self.callbacks:
                    self.callbacks['ticker'](data)
                    
            # 호가 데이터 처리
            elif message_type == 'orderbook':
                if 'orderbook' in self.callbacks:
                    self.callbacks['orderbook'](data)
            
            # 디버그용 로그 추가
            logger.debug(f"웹소켓 메시지 수신: type={message_type}, keys={list(data.keys())}")
                
        except Exception as e:
            logger.error(f"메시지 처리 중 오류: {e}")
            logger.debug(f"원본 메시지: {message}")
    
    def _on_error(self, ws, error):
        """웹소켓 오류"""
        logger.error(f"웹소켓 오류: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """웹소켓 연결 종료"""
        logger.info(f"웹소켓 연결 종료: {close_status_code}, {close_msg}")
        self.is_connected = False
        
        if self.is_running and self.reconnect_count < self.max_reconnect_attempts:
            self._schedule_reconnect()
    
    def _schedule_reconnect(self):
        """재연결 스케줄링"""
        if not self.is_running:
            return
            
        self.reconnect_count += 1
        logger.info(f"웹소켓 재연결 시도 ({self.reconnect_count}/{self.max_reconnect_attempts})")
        
        def reconnect():
            if self.is_running:
                time.sleep(self.reconnect_interval)
                if self.is_running:  # 재연결 대기 중 종료되지 않았다면
                    self.connect()
        
        self.reconnect_thread = threading.Thread(target=reconnect, daemon=True)
        self.reconnect_thread.start()
    
    def get_status(self) -> Dict[str, Any]:
        """웹소켓 상태 정보 반환"""
        return {
            "is_connected": self.is_connected,
            "is_running": self.is_running,
            "reconnect_count": self.reconnect_count,
            "subscriptions_count": len(self.subscriptions),
            "callbacks_count": len(self.callbacks)
        }

class RealtimeChartUpdater:
    """실시간 차트 업데이터
    
    웹소켓 데이터를 받아서 차트를 실시간으로 업데이트하는 클래스
    """
    
    def __init__(self, chart_widget, symbol: str):
        self.chart_widget = chart_widget
        self.symbol = symbol
        self.websocket = UpbitWebSocket()
        self.current_candle = None
        self.last_trade_time = None
        
        # 캔들 집계를 위한 임시 데이터
        self.candle_buffer = {
            'open': None,
            'high': None,
            'low': None,
            'close': None,
            'volume': 0.0,
            'timestamp': None
        }
        
    def start(self) -> bool:
        """실시간 업데이트 시작"""
        try:
            # 웹소켓 연결
            if not self.websocket.connect():
                logger.error("웹소켓 연결 실패")
                return False
            
            # 체결 데이터 구독 (캔들 생성용)
            success = self.websocket.subscribe_trade(
                symbols=[self.symbol],
                callback=self._on_trade_data
            )
            
            if success:
                logger.info(f"실시간 차트 업데이트 시작: {self.symbol}")
                return True
            else:
                logger.error("체결 데이터 구독 실패")
                return False
                
        except Exception as e:
            logger.error(f"실시간 업데이트 시작 중 오류: {e}")
            return False
    
    def stop(self):
        """실시간 업데이트 중지"""
        try:
            self.websocket.disconnect()
            logger.info("실시간 차트 업데이트 중지")
        except Exception as e:
            logger.error(f"실시간 업데이트 중지 중 오류: {e}")
    
    def change_symbol(self, new_symbol: str):
        """구독 심볼 변경"""
        self.symbol = new_symbol
        self.current_candle = None
        self.last_trade_time = None
        self.candle_buffer = {
            'open': None, 'high': None, 'low': None, 
            'close': None, 'volume': 0.0, 'timestamp': None
        }
        
        # 기존 연결이 있다면 새로운 심볼로 재구독
        if self.websocket.is_connected:
            self.websocket.subscribe_trade(
                symbols=[new_symbol],
                callback=self._on_trade_data
            )
    
    def _on_trade_data(self, data: Dict):
        """체결 데이터 수신 처리"""
        try:
            # 업비트 체결 데이터 구조에 맞춰 파싱
            trade_price = float(data.get('trade_price', data.get('tp', 0)))
            trade_volume = float(data.get('trade_volume', data.get('tv', 0)))
            trade_timestamp = data.get('trade_timestamp', data.get('tdt', data.get('timestamp')))
            
            if not trade_price or not trade_timestamp:
                logger.debug(f"체결 데이터 불완전: price={trade_price}, timestamp={trade_timestamp}")
                return
            
            # 타임스탬프 처리 (밀리초 단위)
            if isinstance(trade_timestamp, str):
                # 문자열 형태의 타임스탬프 파싱
                trade_time = datetime.strptime(trade_timestamp[:19], "%Y-%m-%dT%H:%M:%S")
            else:
                # 숫자 형태의 타임스탬프 (밀리초)
                trade_time = datetime.fromtimestamp(trade_timestamp / 1000)
            
            logger.debug(f"체결 데이터 처리: 가격={trade_price:,.0f}, 수량={trade_volume:.8f}, 시간={trade_time}")
            
            # 현재 timeframe에 맞춰 캔들 시간 계산
            candle_time = self._get_candle_time(trade_time)
            
            # 새로운 캔들 시작인지 확인
            if (self.candle_buffer['timestamp'] is None or 
                candle_time > self.candle_buffer['timestamp']):
                
                # 이전 캔들이 있다면 차트에 업데이트
                if self.candle_buffer['timestamp'] is not None:
                    logger.info(f"캔들 완성: {self.candle_buffer}")
                    self._update_chart_with_candle()
                
                # 새로운 캔들 시작
                self.candle_buffer = {
                    'open': trade_price,
                    'high': trade_price,
                    'low': trade_price,
                    'close': trade_price,
                    'volume': trade_volume,
                    'timestamp': candle_time
                }
                logger.info(f"새 캔들 시작: {candle_time} - 가격: {trade_price:,.0f}")
                
            else:
                # 기존 캔들 업데이트
                old_close = self.candle_buffer['close']
                self.candle_buffer['high'] = max(self.candle_buffer['high'], trade_price)
                self.candle_buffer['low'] = min(self.candle_buffer['low'], trade_price)
                self.candle_buffer['close'] = trade_price
                self.candle_buffer['volume'] += trade_volume
                
                logger.debug(f"캔들 업데이트: {old_close:,.0f} -> {trade_price:,.0f}")
            
            # 차트에 현재 가격 실시간 표시 및 현재 캔들 업데이트
            if hasattr(self.chart_widget, 'update_current_price'):
                self.chart_widget.update_current_price(trade_price)
                
            # 현재 진행 중인 캔들 실시간 업데이트 (완성되지 않은 캔들)
            if hasattr(self.chart_widget, 'update_current_candle'):
                self.chart_widget.update_current_candle(trade_price, trade_volume)
                
        except Exception as e:
            logger.error(f"체결 데이터 처리 중 오류: {e}")
            logger.debug(f"원본 데이터: {data}")
    
    def _get_candle_time(self, trade_time: datetime) -> datetime:
        """거래 시간을 캔들 시간으로 변환"""
        # 1분 캔들로 고정 (나중에 동적으로 변경 가능)
        return trade_time.replace(second=0, microsecond=0)
    
    def _update_chart_with_candle(self):
        """완성된 캔들을 차트에 업데이트"""
        try:
            if not self.candle_buffer['timestamp']:
                return
                
            # 캔들 데이터를 pandas DataFrame 형태로 변환
            import pandas as pd
            
            candle_data = pd.DataFrame([{
                'timestamp': self.candle_buffer['timestamp'],
                'open': self.candle_buffer['open'],
                'high': self.candle_buffer['high'],
                'low': self.candle_buffer['low'],
                'close': self.candle_buffer['close'],
                'volume': self.candle_buffer['volume']
            }])
            
            candle_data.set_index('timestamp', inplace=True)
            
            # 차트 위젯의 실시간 업데이트 메서드 호출
            if hasattr(self.chart_widget, 'add_realtime_candle'):
                self.chart_widget.add_realtime_candle(candle_data)
            
            logger.debug(f"실시간 캔들 업데이트: {self.candle_buffer}")
            
        except Exception as e:
            logger.error(f"차트 캔들 업데이트 중 오류: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """업데이터 상태 정보"""
        ws_status = self.websocket.get_status()
        return {
            "symbol": self.symbol,
            "websocket_connected": ws_status["is_connected"],
            "current_candle": self.candle_buffer,
            "last_trade_time": self.last_trade_time
        }
