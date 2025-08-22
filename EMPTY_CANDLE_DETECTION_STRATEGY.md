# 🔍 빈 캔들 vs 미수집 캔들 구분 전략

## 📋 문제 정의

사용자 지적사항:
> "db에는 존재하는 캔들만 채운다고 해도 플롯을 그릴때 실제로 비어있는지 수집을 안한건지 확인을 해야되지 않나요?"

### 핵심 문제
- **미수집 캔들**: API에서 아직 가져오지 않은 데이터 → **재요청 필요**
- **빈 캔들**: 실제로 거래가 없어서 API에서 반환하지 않는 데이터 → **채움 처리 필요**

## 🔧 해결 전략

### 1. 수집 상태 메타데이터 테이블 설계

```sql
CREATE TABLE candle_collection_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    target_time TEXT NOT NULL,  -- 'YYYY-MM-DD HH:MM:SS'
    collection_status TEXT NOT NULL,  -- 'COLLECTED', 'EMPTY', 'PENDING', 'FAILED'
    last_attempt_at TEXT,
    attempt_count INTEGER DEFAULT 0,
    api_response_code INTEGER,  -- 200, 404, etc
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(symbol, timeframe, target_time)
);
```

### 2. 수집 상태 정의

| 상태 | 의미 | 처리 방법 |
|------|------|-----------|
| `PENDING` | 아직 수집 시도하지 않음 | API 요청 필요 |
| `COLLECTED` | 실제 데이터 수집 완료 | DB에서 조회 |
| `EMPTY` | 실제로 거래가 없음 (API 확인됨) | 차트용 채움 데이터 생성 |
| `FAILED` | 수집 실패 (네트워크/API 오류) | 재시도 필요 |

### 3. SmartCandleCollector 구현

```python
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class CollectionStatus(Enum):
    PENDING = "PENDING"
    COLLECTED = "COLLECTED"
    EMPTY = "EMPTY"
    FAILED = "FAILED"

@dataclass
class CandleCollectionRecord:
    symbol: str
    timeframe: str
    target_time: datetime
    status: CollectionStatus
    last_attempt_at: Optional[datetime] = None
    attempt_count: int = 0
    api_response_code: Optional[int] = None

class SmartCandleCollector:
    """빈 캔들과 미수집 캔들을 구분하는 지능형 수집기"""

    def __init__(self, upbit_client, db_manager):
        self.upbit_client = upbit_client
        self.db_manager = db_manager
        self.logger = create_component_logger("SmartCandleCollector")

    async def ensure_candle_range(self, symbol: str, timeframe: str,
                                start_time: datetime, end_time: datetime) -> List[Dict]:
        """지정된 시간 범위의 모든 캔들 확보 (빈 캔들 포함)"""

        # 1. 시간 범위 내 모든 예상 캔들 시간 생성
        expected_times = self._generate_expected_candle_times(
            start_time, end_time, timeframe
        )

        # 2. 각 시간의 수집 상태 확인
        collection_status = await self._check_collection_status(
            symbol, timeframe, expected_times
        )

        # 3. 미수집/실패 캔들 재수집
        await self._collect_missing_candles(symbol, timeframe, collection_status)

        # 4. 최종 캔들 데이터 구성 (실제 + 채움)
        final_candles = await self._build_final_candle_data(
            symbol, timeframe, expected_times
        )

        return final_candles

    def _generate_expected_candle_times(self, start_time: datetime,
                                      end_time: datetime, timeframe: str) -> List[datetime]:
        """예상되는 모든 캔들 시간 생성"""
        times = []
        current = start_time

        if timeframe == "1m":
            delta = timedelta(minutes=1)
        elif timeframe == "5m":
            delta = timedelta(minutes=5)
        elif timeframe == "15m":
            delta = timedelta(minutes=15)
        else:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

        while current <= end_time:
            times.append(current)
            current += delta

        return times

    async def _check_collection_status(self, symbol: str, timeframe: str,
                                     expected_times: List[datetime]) -> Dict[datetime, CollectionStatus]:
        """각 시간의 수집 상태 확인"""

        status_map = {}

        for target_time in expected_times:
            # DB에서 수집 상태 조회
            record = await self.db_manager.get_collection_status(
                symbol, timeframe, target_time
            )

            if record is None:
                # 처음 보는 시간 → PENDING
                status_map[target_time] = CollectionStatus.PENDING
                await self.db_manager.insert_collection_status(
                    symbol, timeframe, target_time, CollectionStatus.PENDING
                )
            else:
                status_map[target_time] = record.status

        return status_map

    async def _collect_missing_candles(self, symbol: str, timeframe: str,
                                     status_map: Dict[datetime, CollectionStatus]):
        """미수집 또는 실패한 캔들들 수집"""

        missing_times = [
            time for time, status in status_map.items()
            if status in [CollectionStatus.PENDING, CollectionStatus.FAILED]
        ]

        if not missing_times:
            return

        self.logger.info(f"미수집 캔들 {len(missing_times)}개 수집 시작: {symbol} {timeframe}")

        for target_time in missing_times:
            try:
                # 단일 캔들 시간에 대한 API 요청
                candle_data = await self._request_single_candle(
                    symbol, timeframe, target_time
                )

                if candle_data:
                    # 실제 데이터 있음 → COLLECTED
                    await self.db_manager.insert_candle_data(candle_data)
                    await self.db_manager.update_collection_status(
                        symbol, timeframe, target_time,
                        CollectionStatus.COLLECTED, api_response_code=200
                    )
                    self.logger.debug(f"캔들 수집 완료: {target_time}")
                else:
                    # 데이터 없음 → EMPTY (실제 빈 캔들)
                    await self.db_manager.update_collection_status(
                        symbol, timeframe, target_time,
                        CollectionStatus.EMPTY, api_response_code=404
                    )
                    self.logger.debug(f"빈 캔들 확인: {target_time}")

            except Exception as e:
                # 수집 실패 → FAILED
                await self.db_manager.update_collection_status(
                    symbol, timeframe, target_time,
                    CollectionStatus.FAILED, api_response_code=500
                )
                self.logger.error(f"캔들 수집 실패: {target_time}, {e}")

    async def _request_single_candle(self, symbol: str, timeframe: str,
                                   target_time: datetime) -> Optional[Dict]:
        """특정 시간의 단일 캔들 요청"""

        # 업비트 API는 범위 요청만 지원하므로,
        # target_time을 포함하는 최소 범위로 요청
        end_time = target_time + timedelta(minutes=1)  # 1분 범위

        try:
            candles = await self.upbit_client.get_candles_minutes(
                symbol=symbol,
                unit=timeframe,
                to=end_time.isoformat(),
                count=1
            )

            if candles:
                # 요청한 시간과 정확히 일치하는 캔들 찾기
                target_str = target_time.strftime("%Y-%m-%dT%H:%M:%S")
                for candle in candles:
                    if candle.get('candle_date_time_kst', '').startswith(target_str[:16]):
                        return candle

            return None  # 해당 시간의 캔들 없음

        except Exception as e:
            self.logger.error(f"API 요청 실패: {symbol} {timeframe} {target_time}, {e}")
            raise

    async def _build_final_candle_data(self, symbol: str, timeframe: str,
                                     expected_times: List[datetime]) -> List[Dict]:
        """최종 캔들 데이터 구성 (실제 + 채움)"""

        final_candles = []
        last_real_price = None

        for target_time in expected_times:
            # 수집 상태 확인
            status_record = await self.db_manager.get_collection_status(
                symbol, timeframe, target_time
            )

            if status_record.status == CollectionStatus.COLLECTED:
                # 실제 데이터 조회
                real_candle = await self.db_manager.get_candle_data(
                    symbol, timeframe, target_time
                )

                if real_candle:
                    final_candles.append({
                        **real_candle,
                        'is_real_trade': True,
                        'fill_method': None
                    })
                    last_real_price = real_candle['trade_price']

            elif status_record.status == CollectionStatus.EMPTY:
                # 빈 캔들 → 채움 데이터 생성
                if last_real_price is not None:
                    fill_candle = self._create_fill_candle(
                        symbol, timeframe, target_time, last_real_price
                    )
                    final_candles.append(fill_candle)
                else:
                    self.logger.warning(f"채움 불가 (이전 가격 없음): {target_time}")

            else:
                # PENDING 또는 FAILED → 경고 로그
                self.logger.warning(f"미처리 캔들: {target_time}, 상태: {status_record.status}")

        return final_candles

    def _create_fill_candle(self, symbol: str, timeframe: str,
                          target_time: datetime, last_price: float) -> Dict:
        """채움 캔들 데이터 생성"""

        return {
            'market': symbol,
            'candle_date_time_kst': target_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'opening_price': last_price,
            'high_price': last_price,
            'low_price': last_price,
            'trade_price': last_price,
            'timestamp': int(target_time.timestamp() * 1000),
            'candle_acc_trade_price': 0.0,
            'candle_acc_trade_volume': 0.0,
            'is_real_trade': False,
            'fill_method': 'last_price'
        }

# 데이터베이스 매니저 확장
class CandleCollectionStatusManager:
    """캔들 수집 상태 관리"""

    def __init__(self, db_connection):
        self.db = db_connection

    async def get_collection_status(self, symbol: str, timeframe: str,
                                  target_time: datetime) -> Optional[CandleCollectionRecord]:
        """수집 상태 조회"""

        query = """
        SELECT symbol, timeframe, target_time, collection_status,
               last_attempt_at, attempt_count, api_response_code
        FROM candle_collection_status
        WHERE symbol = ? AND timeframe = ? AND target_time = ?
        """

        result = await self.db.fetchone(query, (
            symbol, timeframe, target_time.strftime("%Y-%m-%d %H:%M:%S")
        ))

        if result:
            return CandleCollectionRecord(
                symbol=result[0],
                timeframe=result[1],
                target_time=datetime.fromisoformat(result[2]),
                status=CollectionStatus(result[3]),
                last_attempt_at=datetime.fromisoformat(result[4]) if result[4] else None,
                attempt_count=result[5],
                api_response_code=result[6]
            )

        return None

    async def insert_collection_status(self, symbol: str, timeframe: str,
                                     target_time: datetime, status: CollectionStatus):
        """새 수집 상태 등록"""

        query = """
        INSERT OR REPLACE INTO candle_collection_status
        (symbol, timeframe, target_time, collection_status, last_attempt_at, attempt_count)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
        """

        await self.db.execute(query, (
            symbol, timeframe,
            target_time.strftime("%Y-%m-%d %H:%M:%S"),
            status.value
        ))

    async def update_collection_status(self, symbol: str, timeframe: str,
                                     target_time: datetime, status: CollectionStatus,
                                     api_response_code: Optional[int] = None):
        """수집 상태 업데이트"""

        query = """
        UPDATE candle_collection_status
        SET collection_status = ?, last_attempt_at = CURRENT_TIMESTAMP,
            attempt_count = attempt_count + 1, api_response_code = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE symbol = ? AND timeframe = ? AND target_time = ?
        """

        await self.db.execute(query, (
            status.value, api_response_code,
            symbol, timeframe, target_time.strftime("%Y-%m-%d %H:%M:%S")
        ))
```

## 🎯 차트 렌더링 로직

### ChartDataProvider 구현

```python
class ChartDataProvider:
    """차트용 연속 데이터 제공자"""

    def __init__(self, smart_collector: SmartCandleCollector):
        self.smart_collector = smart_collector
        self.logger = create_component_logger("ChartDataProvider")

    async def get_continuous_candles(self, symbol: str, timeframe: str,
                                   start_time: datetime, end_time: datetime,
                                   include_empty: bool = True) -> List[Dict]:
        """차트용 연속 캔들 데이터 제공"""

        # 스마트 수집기로 완전한 데이터 확보
        all_candles = await self.smart_collector.ensure_candle_range(
            symbol, timeframe, start_time, end_time
        )

        if include_empty:
            return all_candles  # 빈 캔들 포함
        else:
            # 실제 거래 캔들만 반환 (매매 지표 계산용)
            return [candle for candle in all_candles if candle.get('is_real_trade', True)]

    def is_candle_empty(self, candle: Dict) -> bool:
        """빈 캔들 여부 확인"""
        return not candle.get('is_real_trade', True)

    def get_fill_method(self, candle: Dict) -> Optional[str]:
        """채움 방식 확인"""
        return candle.get('fill_method')
```

## 🔄 사용 예시

```python
# 1. 스마트 수집기 초기화
smart_collector = SmartCandleCollector(upbit_client, db_manager)
chart_provider = ChartDataProvider(smart_collector)

# 2. 차트용 연속 데이터 (빈 캔들 포함)
chart_candles = await chart_provider.get_continuous_candles(
    symbol="KRW-BTC",
    timeframe="1m",
    start_time=datetime(2025, 8, 22, 10, 0, 0),
    end_time=datetime(2025, 8, 22, 12, 0, 0),
    include_empty=True  # 차트용
)

# 3. 매매 지표 계산용 (실제 거래만)
trading_candles = await chart_provider.get_continuous_candles(
    symbol="KRW-BTC",
    timeframe="1m",
    start_time=datetime(2025, 8, 22, 10, 0, 0),
    end_time=datetime(2025, 8, 22, 12, 0, 0),
    include_empty=False  # 매매용
)

# 4. 상태별 분리
for candle in chart_candles:
    if chart_provider.is_candle_empty(candle):
        print(f"빈 캔들: {candle['candle_date_time_kst']}, 채움방식: {chart_provider.get_fill_method(candle)}")
    else:
        print(f"실제 거래: {candle['candle_date_time_kst']}, 거래량: {candle['candle_acc_trade_volume']}")
```

## 💡 핵심 장점

1. **명확한 구분**: 빈 캔들 vs 미수집 캔들을 메타데이터로 확실히 구분
2. **재요청 방지**: 이미 확인된 빈 캔들은 다시 API 요청하지 않음
3. **차트 연속성**: 빈 캔들을 채워서 차트 끊김 없음
4. **매매 정확성**: 실제 거래 데이터만으로 지표 계산
5. **효율적 캐싱**: 수집 상태를 DB에 저장하여 중복 요청 방지

## 🎨 finplot 통합

```python
import finplot as fplt

# 차트 데이터와 지표 데이터 분리
chart_data = await chart_provider.get_continuous_candles(symbol, tf, start, end, include_empty=True)
indicator_data = await chart_provider.get_continuous_candles(symbol, tf, start, end, include_empty=False)

# finplot 차트 생성 (연속성 보장)
df_chart = pd.DataFrame(chart_data)
fplt.candlestick_ochl(df_chart[['opening_price', 'trade_price', 'high_price', 'low_price']])

# 지표 계산 (정확성 보장)
df_indicator = pd.DataFrame(indicator_data)
sma = df_indicator['trade_price'].rolling(20).mean()
fplt.plot(sma, color='blue')

# 빈 캔들 시각적 구분
for i, candle in enumerate(chart_data):
    if chart_provider.is_candle_empty(candle):
        fplt.add_line((i, candle['low_price']), (i, candle['high_price']), color='gray', style='--')
```

이 전략으로 사용자가 지적한 핵심 문제를 완전히 해결할 수 있습니다! 🎯
