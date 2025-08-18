# 차트뷰 Upbit API 타임프레임 조사 결과
> 1개월(1M) 타임프레임 지원 여부 및 대안 방안

## 📊 Upbit API 타임프레임 지원 현황

### 1. REST API 지원 타임프레임
**Quotation API - 캔들 조회 엔드포인트:**
- `GET /v1/candles/minutes/{unit}` - 분봉 (1, 3, 5, 15, 30, 60, 240분)
- `GET /v1/candles/days` - 일봉
- `GET /v1/candles/weeks` - 주봉
- `GET /v1/candles/months` - **월봉** ✅

### 2. WebSocket 지원 타임프레임
**실시간 스트리밍:**
- ticker (현재가)
- trade (체결)
- orderbook (호가)
- **캔들 데이터는 WebSocket 미지원** ⚠️

## 🔄 1개월 타임프레임 구현 방안

### 방안 1: 하이브리드 모드 (추천)
```python
class TimeframeManager:
    """타임프레임별 데이터 수집 전략"""

    WEBSOCKET_SUPPORTED = [
        "1m", "3m", "5m", "15m", "30m", "1h", "4h"  # 분/시간봉
    ]

    API_ONLY = [
        "1d", "1w", "1M"  # 일/주/월봉
    ]

    def getDataSource(self, timeframe: str) -> str:
        """타임프레임별 데이터 소스 결정"""
        if timeframe in self.WEBSOCKET_SUPPORTED:
            return "websocket+api"  # 실시간 + 백업
        elif timeframe in self.API_ONLY:
            return "api_only"       # API 폴링만
        else:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

    def getPollingInterval(self, timeframe: str) -> int:
        """타임프레임별 적절한 폴링 주기 (ms)"""
        intervals = {
            "1m": 10000,    # 10초 (WebSocket 백업용)
            "3m": 30000,    # 30초
            "5m": 60000,    # 1분
            "15m": 180000,  # 3분
            "30m": 300000,  # 5분
            "1h": 600000,   # 10분
            "4h": 1800000,  # 30분
            "1d": 3600000,  # 1시간
            "1w": 7200000,  # 2시간
            "1M": 21600000, # 6시간 (월봉)
        }
        return intervals.get(timeframe, 60000)
```

### 방안 2: 데이터 변환 로직
```python
class TimeframeConverter:
    """저차원 데이터를 고차원으로 변환"""

    def convertToMonthly(self, daily_data: List[dict]) -> List[dict]:
        """일봉 데이터를 월봉으로 변환"""
        monthly_candles = []
        current_month_data = []
        current_month = None

        for candle in daily_data:
            candle_date = datetime.fromisoformat(candle['candle_date_time_kst'])
            month_key = candle_date.strftime('%Y-%m')

            if current_month != month_key:
                # 이전 달 데이터 처리
                if current_month_data:
                    monthly_candle = self.aggregateToMonthly(current_month_data)
                    monthly_candles.append(monthly_candle)

                # 새 달 시작
                current_month = month_key
                current_month_data = [candle]
            else:
                current_month_data.append(candle)

        # 마지막 달 처리
        if current_month_data:
            monthly_candle = self.aggregateToMonthly(current_month_data)
            monthly_candles.append(monthly_candle)

        return monthly_candles

    def aggregateToMonthly(self, daily_candles: List[dict]) -> dict:
        """일봉들을 월봉으로 집계"""
        if not daily_candles:
            return None

        # 시가: 첫째 날의 시가
        opening_price = daily_candles[0]['opening_price']

        # 종가: 마지막 날의 종가
        closing_price = daily_candles[-1]['trade_price']

        # 고가: 기간 중 최고가
        high_price = max([c['high_price'] for c in daily_candles])

        # 저가: 기간 중 최저가
        low_price = min([c['low_price'] for c in daily_candles])

        # 거래량: 기간 총 거래량
        acc_trade_volume = sum([c['candle_acc_trade_volume'] for c in daily_candles])

        # 거래대금: 기간 총 거래대금
        acc_trade_price = sum([c['candle_acc_trade_price'] for c in daily_candles])

        return {
            'market': daily_candles[0]['market'],
            'candle_date_time_kst': daily_candles[0]['candle_date_time_kst'],
            'opening_price': opening_price,
            'high_price': high_price,
            'low_price': low_price,
            'trade_price': closing_price,
            'candle_acc_trade_volume': acc_trade_volume,
            'candle_acc_trade_price': acc_trade_price,
            'prev_closing_price': daily_candles[0]['prev_closing_price'],
            'change_price': closing_price - daily_candles[0]['prev_closing_price'],
            'change_rate': ((closing_price - daily_candles[0]['prev_closing_price']) / daily_candles[0]['prev_closing_price']) * 100
        }
```

### 방안 3: 백본 시스템 통합
```python
class MonthlyDataManager:
    """월봉 전용 데이터 관리자"""

    def __init__(self, api_client, cache_manager):
        self.api_client = api_client
        self.cache = cache_manager
        self.update_timer = QTimer()

    def startMonthlyDataCollection(self, symbol: str):
        """월봉 데이터 수집 시작"""
        # 초기 데이터 로딩 (최근 24개월)
        self.loadInitialMonthlyData(symbol)

        # 6시간마다 업데이트 (API 부하 최소화)
        self.update_timer.timeout.connect(lambda: self.updateMonthlyData(symbol))
        self.update_timer.start(21600000)  # 6시간

    async def loadInitialMonthlyData(self, symbol: str):
        """초기 월봉 데이터 로딩"""
        try:
            url = "https://api.upbit.com/v1/candles/months"
            params = {
                "market": symbol,
                "count": 24  # 최근 24개월
            }

            response = await self.api_client.get(url, params=params)
            if response.status == 200:
                monthly_data = await response.json()

                # 캐시에 저장
                self.cache.put(symbol, "1M", monthly_data)

                logger.info(f"월봉 데이터 로딩 완료: {symbol}, {len(monthly_data)}개")

        except Exception as e:
            logger.error(f"월봉 데이터 로딩 실패: {symbol} - {e}")

    async def updateMonthlyData(self, symbol: str):
        """월봉 데이터 업데이트"""
        try:
            # 최근 1개월 데이터만 요청
            url = "https://api.upbit.com/v1/candles/months"
            params = {
                "market": symbol,
                "count": 1
            }

            response = await self.api_client.get(url, params=params)
            if response.status == 200:
                latest_data = await response.json()

                if latest_data:
                    # 기존 캐시 업데이트
                    cached_data = self.cache.get(symbol, "1M")
                    if cached_data is not None:
                        # 최신 데이터로 첫 번째 요소 교체
                        cached_data[0] = latest_data[0]
                        self.cache.put(symbol, "1M", cached_data)

                        logger.debug(f"월봉 데이터 업데이트: {symbol}")

        except Exception as e:
            logger.error(f"월봉 데이터 업데이트 실패: {symbol} - {e}")
```

## 🎯 구현 권장사항

### 1. UI 표시 방식
```python
class TimeframeSelector(QComboBox):
    """타임프레임 선택 콤보박스"""

    def setupTimeframes(self):
        timeframes = [
            ("1분", "1m", True),    # (표시명, 값, WebSocket지원)
            ("3분", "3m", True),
            ("5분", "5m", True),
            ("15분", "15m", True),
            ("30분", "30m", True),
            ("1시간", "1h", True),
            ("4시간", "4h", True),
            ("1일", "1d", False),
            ("1주", "1w", False),
            ("1개월", "1M", False), # API만 지원
        ]

        for display_name, value, ws_supported in timeframes:
            self.addItem(display_name, value)

            # WebSocket 미지원 항목은 색상으로 구분
            if not ws_supported:
                index = self.count() - 1
                self.setItemData(index, QColor(255, 200, 100), Qt.ForegroundRole)
```

### 2. 사용자 피드백
```python
class TimeframeStatusIndicator(QLabel):
    """타임프레임별 상태 표시"""

    def updateStatus(self, timeframe: str, data_source: str):
        if data_source == "websocket+api":
            self.setText("🟢 실시간")
            self.setStyleSheet("color: green;")
        elif data_source == "api_only":
            self.setText("🟡 API 폴링")
            self.setStyleSheet("color: orange;")

        self.setToolTip(f"{timeframe} - {data_source}")
```

## 📝 결론

1. **1개월 타임프레임 지원**: Upbit API의 월봉 엔드포인트 사용 ✅
2. **WebSocket 한계**: 캔들 데이터는 WebSocket 미지원 ⚠️
3. **하이브리드 전략**: 분/시간봉은 WebSocket+API, 일/주/월봉은 API 전용
4. **폴링 주기**: 월봉은 6시간마다 업데이트로 충분
5. **사용자 경험**: 데이터 소스별 상태 표시로 투명성 제공

이 방식으로 모든 타임프레임을 지원하면서도 효율적인 리소스 사용이 가능합니다.

---
*Upbit API 한계를 고려한 최적화된 타임프레임 지원 방안*
