# 📋 CandleDataProvider 최소 구현 설계서
> 캔들 데이터 수집, 저장, 제공의 핵심 기능만 구현

## 🎯 구현 목표

### 핵심 기능 (최소 구현)
1. **캔들 데이터 수집**: 업비트 API에서 캔들 데이터 조회
2. **캔들 데이터 저장**: SQLite DB에 안전하게 저장
3. **캔들 데이터 제공**: 서브시스템에게 데이터 제공
4. **기본 캐시**: 중복 요청 방지를 위한 간단한 메모리 캐시

### 제외 기능 (향후 확장)
- 복잡한 청크 분할 로직
- 고급 겹침 분석
- 성능 최적화 기능
- 통계 수집
- 고급 캐시 정책

## 📋 최소 API 설계

### 1. 메인 진입점
```python
class CandleDataProvider:
    """캔들 데이터 Infrastructure Service - 최소 구현"""

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        count: int
    ) -> CandleDataResponse:
        """
        최신 캔들 데이터 조회 (가장 단순한 형태)

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '5m', '1h', '1d')
            count: 캔들 개수 (1~200, 업비트 API 제한 준수)

        Returns:
            CandleDataResponse: 성공/실패 + 캔들 데이터 리스트

        동작 순서:
            1. 파라미터 검증
            2. 캐시 확인 (있으면 반환)
            3. DB에서 조회 시도
            4. 부족하면 API 요청
            5. DB에 저장
            6. 캐시에 저장
            7. 결과 반환
        """
```

### 2. 지원 파라미터
```python
# 1단계: count만 지원 (가장 단순)
response = await provider.get_candles("KRW-BTC", "5m", 100)

# 향후 확장 (2단계):
# response = await provider.get_candles(
#     symbol="KRW-BTC",
#     timeframe="5m",
#     count=100,
#     start_time=datetime.now() - timedelta(hours=5)  # 선택적
# )
```

## 🏗️ 최소 아키텍처

### 컴포넌트 구성
```
CandleDataProvider (최소 구현)
├── 기본 의존성
│   ├── SqliteCandleRepository  ✅ (기존 활용)
│   ├── UpbitPublicClient      ✅ (기존 활용)
│   ├── CandleModels          ✅ (기존 활용)
│   └── DatabaseManager       ✅ (기존 활용)
│
├── 핵심 로직 (새로 구현)
│   ├── _validate_request()   # 파라미터 검증
│   ├── _check_cache()        # 간단한 캐시 확인
│   ├── _query_database()     # DB 조회
│   ├── _fetch_from_api()     # API 요청
│   └── _store_data()         # 저장
│
└── 유틸리티
    ├── 간단한 메모리 캐시 (dict 기반)
    └── 기본 에러 처리
```

### 데이터 플로우
```
1. get_candles() 요청
2. _validate_request() → 파라미터 검증
3. _check_cache() → 캐시 히트시 즉시 반환
4. _query_database() → DB에서 기존 데이터 조회
5. 데이터 부족시 → _fetch_from_api() → 업비트 API 호출
6. _store_data() → 새 데이터 DB 저장
7. 캐시 업데이트
8. CandleDataResponse 반환
```

## 🔧 구현 세부사항

### 1. 파라미터 검증 (_validate_request)
```python
async def _validate_request(self, symbol: str, timeframe: str, count: int) -> None:
    """기본 파라미터 검증"""
    # 1. symbol 형식 확인 ('KRW-BTC' 패턴)
    if not re.match(r'^[A-Z]{3}-[A-Z0-9]+$', symbol):
        raise ValueError(f"잘못된 심볼 형식: {symbol}")

    # 2. timeframe 지원 여부 확인
    if timeframe not in ['1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']:
        raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

    # 3. count 범위 확인 (업비트 API 제한: 1~200)
    if not 1 <= count <= 200:
        raise ValueError(f"캔들 개수는 1~200 사이여야 합니다: {count}")
```

### 2. 간단한 캐시 (_check_cache)
```python
class SimpleCache:
    """최소한의 메모리 캐시 (dict 기반)"""

    def __init__(self, ttl_seconds: int = 60):
        self._cache: Dict[str, Tuple[List[CandleData], datetime]] = {}
        self._ttl = ttl_seconds

    def get(self, symbol: str, timeframe: str, count: int) -> Optional[List[CandleData]]:
        """캐시에서 데이터 조회"""
        key = f"{symbol}_{timeframe}_{count}"

        if key in self._cache:
            data, stored_at = self._cache[key]

            # TTL 확인
            if datetime.now() - stored_at < timedelta(seconds=self._ttl):
                logger.debug(f"캐시 히트: {key}")
                return data
            else:
                # 만료된 데이터 제거
                del self._cache[key]

        return None

    def set(self, symbol: str, timeframe: str, count: int, data: List[CandleData]) -> None:
        """캐시에 데이터 저장"""
        key = f"{symbol}_{timeframe}_{count}"
        self._cache[key] = (data, datetime.now())
        logger.debug(f"캐시 저장: {key} ({len(data)}개)")
```

### 3. DB 조회 (_query_database)
```python
async def _query_database(self, symbol: str, timeframe: str, count: int) -> List[CandleData]:
    """DB에서 최신 캔들 데이터 조회"""
    try:
        # 테이블 존재 확인
        if not await self.repository.table_exists(symbol, timeframe):
            logger.debug(f"테이블 없음: {symbol}_{timeframe}")
            return []

        # 최신 데이터부터 count개 조회 (업비트 API와 동일한 순서)
        candles = await self.repository.get_latest_candles(symbol, timeframe, count)
        logger.debug(f"DB 조회 결과: {len(candles)}개")
        return candles

    except Exception as e:
        logger.error(f"DB 조회 실패: {e}")
        return []
```

### 4. API 요청 (_fetch_from_api)
```python
async def _fetch_from_api(self, symbol: str, timeframe: str, count: int) -> List[CandleData]:
    """업비트 API에서 캔들 데이터 조회"""
    try:
        # UpbitPublicClient 활용
        api_data = await self.upbit_client.get_candles(
            market=symbol,
            timeframe=timeframe,
            count=count
        )

        # CandleData 모델로 변환
        candles = []
        for item in api_data:
            candle = CandleData.from_upbit_api(item, timeframe)
            candles.append(candle)

        logger.info(f"API 조회 성공: {symbol} {timeframe} {len(candles)}개")
        return candles

    except Exception as e:
        logger.error(f"API 조회 실패: {e}")
        raise
```

### 5. 데이터 저장 (_store_data)
```python
async def _store_data(self, symbol: str, timeframe: str, candles: List[CandleData]) -> None:
    """캔들 데이터를 DB에 저장"""
    try:
        if not candles:
            return

        # 테이블 생성 (필요시)
        await self.repository.ensure_table_exists(symbol, timeframe)

        # 배치 저장
        saved_count = await self.repository.save_candle_chunk(symbol, timeframe, candles)
        logger.info(f"DB 저장 완료: {saved_count}개 (중복 제외)")

    except Exception as e:
        logger.error(f"DB 저장 실패: {e}")
        # 저장 실패해도 데이터는 반환 (서비스 연속성 우선)
```

## 📝 메인 구현 로직

### get_candles() 핵심 구현
```python
async def get_candles(self, symbol: str, timeframe: str, count: int) -> CandleDataResponse:
    """최신 캔들 데이터 조회 - 최소 구현"""
    start_time = time.time()

    try:
        # 1. 파라미터 검증
        await self._validate_request(symbol, timeframe, count)

        # 2. 캐시 확인
        cached_data = self._cache.get(symbol, timeframe, count)
        if cached_data:
            return create_success_response(
                candles=cached_data,
                data_source="cache",
                response_time_ms=(time.time() - start_time) * 1000
            )

        # 3. DB 조회
        db_candles = await self._query_database(symbol, timeframe, count)

        # 4. 데이터 부족시 API 요청
        if len(db_candles) < count:
            api_candles = await self._fetch_from_api(symbol, timeframe, count)

            # 5. 새 데이터 저장
            await self._store_data(symbol, timeframe, api_candles)

            # 6. 캐시 업데이트
            self._cache.set(symbol, timeframe, count, api_candles)

            return create_success_response(
                candles=api_candles,
                data_source="api",
                response_time_ms=(time.time() - start_time) * 1000
            )
        else:
            # 7. DB 데이터로 충분
            self._cache.set(symbol, timeframe, count, db_candles)

            return create_success_response(
                candles=db_candles,
                data_source="db",
                response_time_ms=(time.time() - start_time) * 1000
            )

    except Exception as e:
        logger.error(f"get_candles 실패: {e}")
        return create_error_response(
            error_message=str(e),
            response_time_ms=(time.time() - start_time) * 1000
        )
```

## 🧪 테스트 시나리오

### 1. 기본 동작 테스트
```python
# 1. 첫 요청 (API 호출)
response1 = await provider.get_candles("KRW-BTC", "5m", 10)
assert response1.success == True
assert response1.data_source == "api"
assert len(response1.candles) == 10

# 2. 동일 요청 (캐시 히트)
response2 = await provider.get_candles("KRW-BTC", "5m", 10)
assert response2.data_source == "cache"

# 3. 다른 요청 (DB 조회)
time.sleep(70)  # 캐시 만료 대기
response3 = await provider.get_candles("KRW-BTC", "5m", 10)
assert response3.data_source == "db"
```

### 2. 에러 처리 테스트
```python
# 잘못된 파라미터
response = await provider.get_candles("INVALID", "5m", 10)
assert response.success == False
assert "잘못된 심볼" in response.error_message

# 범위 초과
response = await provider.get_candles("KRW-BTC", "5m", 300)
assert response.success == False
assert "1~200 사이" in response.error_message
```

## 🚀 구현 순서

### Phase 1: 기본 골격
1. CandleDataProvider 클래스 생성
2. 생성자에서 의존성 주입
3. get_candles() 메서드 껍데기

### Phase 2: 핵심 로직
1. _validate_request() 구현
2. SimpleCache 클래스 구현
3. get_candles() 메인 로직 구현

### Phase 3: 세부 기능
1. _query_database() 구현
2. _fetch_from_api() 구현
3. _store_data() 구현

### Phase 4: 테스트 및 검증
1. 단위 테스트 작성
2. 통합 테스트 실행
3. `python run_desktop_ui.py` 연동 확인

## 📋 완성 기준

### 성공 기준
- [ ] `get_candles("KRW-BTC", "5m", 100)` 정상 동작
- [ ] 캐시 히트/미스 정상 동작
- [ ] DB 저장/조회 정상 동작
- [ ] 에러 상황 적절한 처리
- [ ] 메인 프로그램에서 호출 가능

### 성능 기준
- API 요청: 3초 이내
- 캐시 응답: 100ms 이내
- DB 응답: 500ms 이내

## 🔄 향후 확장 계획

### 2단계 확장 (선택적)
1. start_time 파라미터 지원
2. end_time 파라미터 지원
3. 청크 분할 (200개 초과 요청)

### 3단계 확장 (고급)
1. OverlapAnalyzer 통합
2. 성능 최적화
3. 통계 수집
4. 고급 캐시 정책

---

이 문서는 **최소 동작하는 버전**을 목표로 작성되었습니다.
복잡한 기능은 제외하고 핵심 기능만 구현하여 안정성을 확보한 후,
단계별로 기능을 확장하는 방식을 권장합니다.
