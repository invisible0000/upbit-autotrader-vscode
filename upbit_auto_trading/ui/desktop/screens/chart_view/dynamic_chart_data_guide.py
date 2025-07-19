"""
차트 뷰 최적화된 동적 데이터 로딩 구현 가이드

업비트 API 제한사항을 고려한 효율적인 차트 데이터 로딩 전략:
1. 점진적 로딩 (Lazy Loading): 필요한 만큼만 가져오기
2. 실시간 업데이트: 웹소켓 기반으로 API 요청 최소화
3. 과거 데이터 확장: 스크롤 시 동적으로 데이터 추가

API 제한사항:
- 한 번에 최대 200개 캔들 조회 가능
- 초당 10회, 분당 600회 요청 제한 (매우 넉넉함)
"""

from datetime import datetime, timedelta
import pandas as pd
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
import logging
import asyncio
import websockets
import json

logger = logging.getLogger(__name__)

class OptimizedChartDataLoader(QThread):
    """
    업비트 API 제한사항을 고려한 최적화된 차트 데이터 로더
    
    핵심 전략:
    1. 초기 로딩: 여러 번 API 호출로 충분한 데이터 확보 (600개 캔들)
    2. 점진적 로딩: 사용자 스크롤 시 과거 데이터 200개씩 추가
    3. 실시간 업데이트: 웹소켓으로 실시간 체결 데이터 수신
    """
    
    # 시그널 정의
    initial_data_loaded = pyqtSignal(pd.DataFrame)  # 초기 데이터 로딩 완료
    past_data_loaded = pyqtSignal(pd.DataFrame)     # 과거 데이터 추가 로딩 완료
    realtime_update = pyqtSignal(dict)              # 실시간 캔들 업데이트
    loading_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, symbol, timeframe, initial_candle_count=600):
        super().__init__()
        self.symbol = symbol
        self.timeframe = timeframe
        self.initial_candle_count = initial_candle_count
        self.api_client = None
        self.oldest_candle_time = None
        
    def set_api_client(self, api_client):
        """업비트 API 클라이언트 설정"""
        self.api_client = api_client
    
    def fetch_initial_candles(self):
        """
        초기 차트 로딩: 여러 번 API 호출로 충분한 데이터 확보
        
        전략:
        1. 최신 200개 캔들부터 시작
        2. 가장 오래된 캔들 시간을 'to' 파라미터로 사용
        3. 원하는 개수까지 반복 요청
        """
        try:
            if not self.api_client:
                from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
                self.api_client = UpbitAPI()
            
            all_candles = []
            request_count = (self.initial_candle_count + 199) // 200  # 필요한 요청 횟수
            last_candle_time = None
            
            logger.info(f"초기 캔들 로딩 시작: {self.symbol}, {self.timeframe}, {request_count}회 요청 예정")
            
            for i in range(request_count):
                # 업비트 API의 get_candles 메서드 활용 (기존 구현된 기능!)
                candles = self.api_client.get_candles(
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                    count=200,
                    to=last_candle_time
                )
                
                if not candles:
                    logger.warning(f"캔들 데이터 없음, 요청 {i+1}/{request_count} 중단")
                    break
                
                # 새 데이터를 앞에 추가 (과거 → 현재 순서 유지)
                all_candles = candles + all_candles
                last_candle_time = candles[0]['candle_date_time_utc']
                
                logger.info(f"캔들 로딩 진행: {i+1}/{request_count}, 현재 {len(all_candles)}개")
                
                # API 제한 고려한 약간의 지연 (초당 10회 제한 여유있게 준수)
                self.msleep(100)  # 0.1초 대기
            
            # 가장 오래된 캔들 시간 저장 (추후 과거 데이터 로딩용)
            if all_candles:
                self.oldest_candle_time = all_candles[0]['candle_date_time_utc']
            
            # DataFrame으로 변환
            df = pd.DataFrame(all_candles)
            
            logger.info(f"초기 캔들 로딩 완료: 총 {len(df)}개")
            return df
            
        except Exception as e:
            logger.error(f"초기 캔들 로딩 오류: {str(e)}")
            self.error_occurred.emit(f"초기 데이터 로딩 실패: {str(e)}")
            return pd.DataFrame()
    
    def fetch_past_candles(self, count=200):
        """
        과거 데이터 추가 로딩 (사용자가 차트를 왼쪽으로 스크롤할 때)
        
        Args:
            count: 가져올 캔들 개수 (기본 200개)
        """
        try:
            if not self.oldest_candle_time:
                logger.warning("과거 데이터 로딩 불가: oldest_candle_time 없음")
                return pd.DataFrame()
            
            logger.info(f"과거 캔들 로딩 시작: {count}개, to={self.oldest_candle_time}")
            
            candles = self.api_client.get_candles(
                symbol=self.symbol,
                timeframe=self.timeframe,
                count=count,
                to=self.oldest_candle_time
            )
            
            if candles:
                # 가장 오래된 시간 업데이트
                self.oldest_candle_time = candles[0]['candle_date_time_utc']
                df = pd.DataFrame(candles)
                
                logger.info(f"과거 캔들 로딩 완료: {len(df)}개")
                return df
            else:
                logger.warning("과거 캔들 데이터 없음")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"과거 캔들 로딩 오류: {str(e)}")
            self.error_occurred.emit(f"과거 데이터 로딩 실패: {str(e)}")
            return pd.DataFrame()
    
    def run(self):
        """백그라운드에서 초기 데이터 로드 실행"""
        df = self.fetch_initial_candles()
        if not df.empty:
            self.initial_data_loaded.emit(df)
        self.loading_finished.emit()


class RealtimeChartUpdater(QThread):
    """
    웹소켓 기반 실시간 차트 업데이트
    
    핵심 전략:
    1. 업비트 웹소켓으로 체결(trade) 데이터 실시간 수신
    2. 메모리에서 현재 캔들의 OHLCV 직접 계산
    3. 시간이 바뀌면 완성된 캔들을 차트에 추가
    4. API 요청 수를 전혀 사용하지 않음!
    """
    
    # 시그널 정의
    candle_updated = pyqtSignal(dict)      # 현재 캔들 업데이트
    new_candle_created = pyqtSignal(dict)  # 새 캔들 생성
    connection_status = pyqtSignal(bool)   # 연결 상태
    error_occurred = pyqtSignal(str)
    
    def __init__(self, symbol, timeframe="1m"):
        super().__init__()
        self.symbol = symbol
        self.timeframe = timeframe
        self.current_candle = None
        self.websocket = None
        self.running = False
        
    def start_realtime_update(self):
        """실시간 업데이트 시작"""
        self.running = True
        self.start()
        
    def stop_realtime_update(self):
        """실시간 업데이트 중지"""
        self.running = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())
    
    async def connect_websocket(self):
        """업비트 웹소켓 연결 및 체결 데이터 수신"""
        uri = "wss://api.upbit.com/websocket/v1"
        
        # 구독 메시지 (체결 데이터)
        subscribe_fmt = [
            {"ticket": "chart_realtime"},
            {"type": "trade", "codes": [self.symbol]}
        ]
        
        try:
            async with websockets.connect(uri) as websocket:
                self.websocket = websocket
                self.connection_status.emit(True)
                
                # 구독 요청 전송
                await websocket.send(json.dumps(subscribe_fmt))
                logger.info(f"웹소켓 연결 성공: {self.symbol}")
                
                # 실시간 데이터 수신
                async for message in websocket:
                    if not self.running:
                        break
                        
                    try:
                        data = json.loads(message)
                        if data.get('type') == 'trade':
                            self.process_trade_data(data)
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.error(f"웹소켓 연결 오류: {str(e)}")
            self.connection_status.emit(False)
            self.error_occurred.emit(f"실시간 연결 실패: {str(e)}")
    
    def process_trade_data(self, trade_data):
        """
        체결 데이터를 받아서 현재 캔들 업데이트
        
        Args:
            trade_data: 웹소켓으로 받은 체결 데이터
        """
        try:
            price = float(trade_data['trade_price'])
            volume = float(trade_data['trade_volume'])
            timestamp = trade_data['trade_date_utc'] + 'T' + trade_data['trade_time_utc']
            
            # 현재 시간으로 캔들 시간 계산 (1분 단위)
            candle_time = self.get_candle_time(timestamp)
            
            # 새로운 캔들 시작 여부 확인
            if not self.current_candle or self.current_candle['timestamp'] != candle_time:
                # 이전 캔들이 있다면 완료된 캔들로 전송
                if self.current_candle:
                    self.new_candle_created.emit(self.current_candle.copy())
                
                # 새 캔들 시작
                self.current_candle = {
                    'timestamp': candle_time,
                    'open': price,
                    'high': price,
                    'low': price,
                    'close': price,
                    'volume': volume
                }
            else:
                # 기존 캔들 업데이트
                self.current_candle['high'] = max(self.current_candle['high'], price)
                self.current_candle['low'] = min(self.current_candle['low'], price)
                self.current_candle['close'] = price
                self.current_candle['volume'] += volume
            
            # 현재 캔들 상태 전송
            self.candle_updated.emit(self.current_candle.copy())
            
        except Exception as e:
            logger.error(f"체결 데이터 처리 오류: {str(e)}")
    
    def get_candle_time(self, timestamp):
        """타임스탬프를 캔들 시간으로 변환 (1분 단위로 정규화)"""
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        # 초, 마이크로초를 0으로 설정하여 분 단위로 정규화
        return dt.replace(second=0, microsecond=0).isoformat()
    
    def run(self):
        """백그라운드에서 웹소켓 연결 실행"""
        try:
            asyncio.run(self.connect_websocket())
        except Exception as e:
            logger.error(f"웹소켓 스레드 오류: {str(e)}")
            self.error_occurred.emit(f"실시간 업데이트 오류: {str(e)}")


class AdvancedChartDataManager:
    """
    최적화된 차트 데이터 관리자
    
    기능:
    1. 초기 데이터 로딩 (여러 번 API 호출)
    2. 과거 데이터 확장 (스크롤 시)
    3. 실시간 업데이트 (웹소켓)
    4. 메모리 효율적인 데이터 관리
    """
    
    def __init__(self, chart_widget):
        self.chart_widget = chart_widget
        self.data_loader = None
        self.realtime_updater = None
        self.chart_data = pd.DataFrame()
        
    def initialize_chart(self, symbol, timeframe, initial_count=600):
        """
        차트 초기화 및 데이터 로딩 시작
        
        Args:
            symbol: 거래 심볼 (예: "KRW-BTC")
            timeframe: 시간프레임 (예: "1m", "5m", "1h")
            initial_count: 초기 로딩할 캔들 개수
        """
        logger.info(f"차트 초기화 시작: {symbol}, {timeframe}")
        
        # 1. 초기 데이터 로딩
        self.data_loader = OptimizedChartDataLoader(symbol, timeframe, initial_count)
        self.data_loader.initial_data_loaded.connect(self.on_initial_data_loaded)
        self.data_loader.error_occurred.connect(self.on_error)
        self.data_loader.start()
        
        # 2. 실시간 업데이트 시작
        self.realtime_updater = RealtimeChartUpdater(symbol, timeframe)
        self.realtime_updater.candle_updated.connect(self.on_candle_updated)
        self.realtime_updater.new_candle_created.connect(self.on_new_candle)
        self.realtime_updater.error_occurred.connect(self.on_error)
        self.realtime_updater.start_realtime_update()
    
    def load_past_data(self):
        """과거 데이터 추가 로딩 (사용자가 왼쪽으로 스크롤할 때)"""
        if self.data_loader:
            past_df = self.data_loader.fetch_past_candles()
            if not past_df.empty:
                # 기존 데이터 앞에 과거 데이터 추가
                self.chart_data = pd.concat([past_df, self.chart_data], ignore_index=True)
                self.update_chart_display()
    
    def on_initial_data_loaded(self, df):
        """초기 데이터 로딩 완료 시 처리"""
        self.chart_data = df
        self.update_chart_display()
        logger.info(f"차트 초기 데이터 로딩 완료: {len(df)}개 캔들")
    
    def on_candle_updated(self, candle_data):
        """현재 캔들 업데이트 시 처리"""
        if not self.chart_data.empty:
            # 마지막 캔들을 현재 실시간 캔들로 업데이트
            self.chart_data.iloc[-1] = pd.Series(candle_data)
            self.update_chart_display()
    
    def on_new_candle(self, candle_data):
        """새 캔들 생성 시 처리"""
        # 새 캔들을 데이터프레임에 추가
        new_row = pd.DataFrame([candle_data])
        self.chart_data = pd.concat([self.chart_data, new_row], ignore_index=True)
        self.update_chart_display()
        logger.info("새 캔들 추가됨")
    
    def update_chart_display(self):
        """차트 위젯에 최신 데이터 반영"""
        if hasattr(self.chart_widget, 'update_chart_data'):
            self.chart_widget.update_chart_data(self.chart_data)
    
    def on_error(self, error_message):
        """오류 처리"""
        logger.error(f"차트 데이터 관리 오류: {error_message}")
        # 사용자에게 오류 알림 (토스트, 상태바 등)
    
    def cleanup(self):
        """리소스 정리"""
        if self.data_loader and self.data_loader.isRunning():
            self.data_loader.quit()
            self.data_loader.wait()
        
        if self.realtime_updater and self.realtime_updater.isRunning():
            self.realtime_updater.stop_realtime_update()
            self.realtime_updater.quit()
            self.realtime_updater.wait()


# ============================================================================
# 기존 ChartDataLoader 클래스 (하위 호환성 유지)
# ============================================================================

class ChartDataLoader(QThread):
    """기존 차트 데이터 로더 (하위 호환성 유지)"""
    
    # 시그널 정의
    data_loaded = pyqtSignal(pd.DataFrame)
    loading_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, symbol, timeframe, period_days=200):
        super().__init__()
        self.symbol = symbol
        self.timeframe = timeframe
        self.period_days = period_days
        self.api_client = None
        
    def set_api_client(self, api_client):
        """업비트 API 클라이언트 설정"""
        self.api_client = api_client
    
    def run(self):
        """백그라운드에서 데이터 로드 실행"""
        try:
            if not self.api_client:
                from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
                self.api_client = UpbitAPI()
            
            # 시작 날짜 계산
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.period_days)
            
            # 과거 데이터 수집 (이미 구현된 메서드 활용!)
            df = self.api_client.get_historical_candles(
                symbol=self.symbol,
                timeframe=self.timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if not df.empty:
                self.data_loaded.emit(df)
                logger.info(f"차트 데이터 로드 완료: {self.symbol}, {self.timeframe}, {len(df)}개")
            else:
                self.error_occurred.emit("데이터를 가져올 수 없습니다.")
                
        except Exception as e:
            logger.exception(f"차트 데이터 로드 중 오류: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self.loading_finished.emit()


class DynamicChartDataManager:
    """동적 차트 데이터 관리자"""
    
    def __init__(self, chart_view_screen):
        self.chart_view = chart_view_screen
        self.data_loader = None
        self.api_client = None
        
        # 실시간 업데이트 타이머
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_latest_data)
        
    def initialize_api_client(self):
        """API 클라이언트 초기화"""
        try:
            from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
            self.api_client = UpbitAPI()
            logger.info("업비트 API 클라이언트 초기화 완료")
        except Exception as e:
            logger.exception(f"API 클라이언트 초기화 실패: {e}")
    
    def load_chart_data(self, symbol, timeframe, period_days=200):
        """차트 데이터 로드 시작"""
        # 기존 로더 정리
        if self.data_loader and self.data_loader.isRunning():
            self.data_loader.quit()
            self.data_loader.wait()
        
        # 새 데이터 로더 생성
        self.data_loader = ChartDataLoader(symbol, timeframe, period_days)
        self.data_loader.set_api_client(self.api_client)
        
        # 시그널 연결
        self.data_loader.data_loaded.connect(self.on_data_loaded)
        self.data_loader.loading_finished.connect(self.on_loading_finished)
        self.data_loader.error_occurred.connect(self.on_error_occurred)
        
        # 로딩 시작
        self.chart_view.show_loading_indicator()
        self.data_loader.start()
    
    def on_data_loaded(self, df):
        """데이터 로드 완료 처리"""
        # 차트뷰 데이터 업데이트
        self.chart_view.chart_data = df
        self.chart_view.update_chart()
        self.chart_view.chart_info_panel.set_data_count(len(df))
        
        # 실시간 업데이트 시작 (1분마다)
        self.update_timer.start(60000)  # 60초
    
    def on_loading_finished(self):
        """로딩 완료 처리"""
        self.chart_view.hide_loading_indicator()
    
    def on_error_occurred(self, error_message):
        """오류 발생 처리"""
        logger.error(f"차트 데이터 로드 오류: {error_message}")
        self.chart_view.show_error_message(error_message)
    
    def update_latest_data(self):
        """최신 데이터 업데이트 (실시간)"""
        try:
            if not self.api_client:
                return
            
            # 최신 1개 캔들 가져오기
            latest_df = self.api_client.get_candles(
                symbol=self.chart_view.current_symbol,
                timeframe=self.chart_view.current_timeframe,
                count=1
            )
            
            if not latest_df.empty and hasattr(self.chart_view, 'chart_data'):
                # 기존 데이터와 병합
                existing_data = self.chart_view.chart_data
                latest_timestamp = latest_df.iloc[0]['timestamp']
                
                # 중복 제거 후 추가
                if existing_data.empty or latest_timestamp > existing_data['timestamp'].max():
                    updated_data = pd.concat([existing_data, latest_df]).reset_index(drop=True)
                    self.chart_view.chart_data = updated_data
                    self.chart_view.update_chart()
                    
        except Exception as e:
            logger.exception(f"실시간 데이터 업데이트 오류: {e}")
    
    def stop_real_time_updates(self):
        """실시간 업데이트 중지"""
        self.update_timer.stop()


# 차트뷰 스크린에 추가할 메서드들
class ChartViewScreenExtensions:
    """차트뷰 스크린 확장 메서드들"""
    
    def setup_dynamic_data_loading(self):
        """동적 데이터 로딩 설정"""
        self.data_manager = DynamicChartDataManager(self)
        self.data_manager.initialize_api_client()
    
    def load_real_chart_data(self, symbol=None, timeframe=None):
        """실제 차트 데이터 로드"""
        symbol = symbol or self.current_symbol
        timeframe = timeframe or self.current_timeframe
        
        # 기간 계산 (시간대에 따라 조정)
        period_map = {
            "1m": 1,     # 1일치
            "5m": 5,     # 5일치
            "15m": 15,   # 15일치
            "1h": 30,    # 30일치
            "4h": 120,   # 120일치
            "1d": 365,   # 1년치
        }
        period_days = period_map.get(timeframe, 30)
        
        # 데이터 로드 시작
        self.data_manager.load_chart_data(symbol, timeframe, period_days)
    
    def show_loading_indicator(self):
        """로딩 인디케이터 표시"""
        # TODO: 로딩 스피너 또는 프로그레스 바 표시
        pass
    
    def hide_loading_indicator(self):
        """로딩 인디케이터 숨기기"""
        # TODO: 로딩 UI 숨기기
        pass
    
    def show_error_message(self, message):
        """오류 메시지 표시"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "데이터 로드 오류", message)


# 기존 chart_view_screen.py에 적용할 변경사항

def modify_chart_view_screen_data_loading():
    """
    기존 chart_view_screen.py 파일의 변경이 필요한 부분들:
    
    1. on_symbol_changed 메서드 수정:
       기존: self.chart_data = self.generate_sample_data()
       변경: self.load_real_chart_data(symbol)
    
    2. on_timeframe_changed 메서드 수정:
       기존: self.resample_data()
       변경: self.load_real_chart_data(timeframe=self.current_timeframe)
    
    3. __init__ 메서드에 추가:
       self.setup_dynamic_data_loading()
    
    4. generate_sample_data 메서드:
       백업용으로 유지 (API 오류 시 대체 데이터)
    """
    pass


if __name__ == "__main__":
    print("차트 뷰 동적 데이터 로딩 구현 가이드")
    print("="*50)
    print("✅ 업비트 API 클라이언트 이미 구현됨!")
    print("✅ get_historical_candles() 메서드 활용 가능")
    print("✅ API 제한 준수 로직 구현됨")
    print("🚀 즉시 실제 데이터 연동 가능!")
