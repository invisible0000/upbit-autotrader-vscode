## 캔들 데이터 제공자 to 시간 문제

### 업비트 데이터 기초 정보
업비트가 제공하는 캔들 데이터의 시간 순서는 기본적으로 현재(미래)에서 과거 순서로 내림차순이야.
업비트 서버는 요청 시간의 다음 시점에 데이터부터 전달해줘. 예를 들면 `2025-09-09 00:50:30` 로 요청하면 `2025-09-09 00:49:00`부터 제공해. 조금 자세히 말하면 1m 타임프레임 일 때 `2025-09-09 00:50:59`~ `2025-09-09 00:50:00` 안에 데이터면 `2025-09-09 00:49:00` 부터 제공하는 거지. 업비트는 1초 단위까지 입력을 받는데 1초라도 존재하면 그 다음 시점의 데이터를 제공해. 염두해 둘것은 1s 타임프레임은 1초가 최소 단위 이므로 항상 다음부터 받을 수 있고, 1m 타임프레임 이상부터는 1초라도 포함 시키면 다음을 받을 수 있지. 그리고 제공하는 데이터의 utc, kst 열의 데이터는 시간이 타임프레임에 따라 깔끔하게 정렬되어 있어. timestamp 열은 실제로 캔들이 생성된 시점이라 정렬되어 있지 않아. 

### 상황 파악 및 문제점 검토
#### 테스트 설정
candle_test_04_micro_size.py 를 이용해서 캔들 데이터 제공자를 테스트 중이야. 수집된 db 레코드의 candle_date_time_utc열의 내용을 인식하기 쉽도록 매우 작은 사이즈로 테스트하고 있고 조건은 아래와 같아
```python
"symbol": "KRW-BTC",
"timeframe": "1m",
"table_name": "candles_KRW_BTC_1m",
"start_time": "2025-09-09 00:50:00",
"chunk_size": 5,
"test_scenarios": [{"name": "마이크로 테스트", "count": 13, "description": "utc 상세 분석"}]
```

#### 테스트 결과
현재 코드를 실행한 결과의 candle_date_time_utc 열은 아래와 같아. 내용을 보면 알겠지만 `2025-09-09T00:45:00`, `2025-09-09T00:39:00` 가 없는 상황이지. 추측하기로는 각 청크의 시작 시간이 하나씩 밀린거야. 그렇다면 어딘가에서 시작 시간이 하나씩 밀린거라고 생각해.

```candles_KRW_BTC_1m
candle_date_time_utc
2025-09-09T00:49:00
2025-09-09T00:48:00
2025-09-09T00:47:00
2025-09-09T00:46:00
2025-09-09T00:45:00
2025-09-09T00:43:00
2025-09-09T00:42:00
2025-09-09T00:41:00
2025-09-09T00:40:00
2025-09-09T00:39:00
2025-09-09T00:37:00
2025-09-09T00:36:00
2025-09-09T00:35:00
```

#### 원인 예측
캔들 데이터 제공자에서 시간을 제공 및 변환하는 기능이 포함된 코드는 기본적으로 아래 3가지야. 이 코드중에 어딘가에 문제가 있거나 지금 구조 및 로직에 문제가 있다고 봐야되는 상황이야.
```
upbit_auto_trading\infrastructure\market_data\candle\candle_data_provider.py
upbit_auto_trading\infrastructure\market_data\candle\overlap_analyzer.py
upbit_auto_trading\infrastructure\market_data\candle\time_utils.py
```

그간의 작업으로 추리를 해보면 지금은 오버랩 분석기(overlap_analyzer.py)의 영향으로 보여. 그런데 기본적으로 캔들 데이터 제공자 내부에서 시간을 다룰때는 db의 레코드 utc를 다루기 때문에 제공 하는 오버랩 분석기가 제공하는 데이터에 문제가 있다기 보다는 사용하는 방법의 문제로 봐야되.

#### 확인된 문제점
```candles_KRW_BTC_1m
candle_date_time_utc
오버랩 분석기 제공 시점: 2025-09-09T00:50:00 ~ 2025-09-09T00:46:00, count: 5
2025-09-09T00:49:00 <-- to: 2025-09-09T00:50:00 이기 때문
2025-09-09T00:48:00
2025-09-09T00:47:00
2025-09-09T00:46:00
2025-09-09T00:45:00 <- 수집은 to, count 파라미터 이용
오버랩 분석기 제공 시점: 2025-09-09T00:44:00 ~ 2025-09-09T00:40:00, count: 5
2025-09-09T00:43:00 <-- to: 2025-09-09T00:44:00 이기 때문
2025-09-09T00:42:00
2025-09-09T00:41:00
2025-09-09T00:40:00
2025-09-09T00:39:00 <- 수집은 to, count 파라미터 이용
오버랩 분석기 제공 시점: 2025-09-09T00:38:00 ~ 2025-09-09T00:36:00, count: 3
2025-09-09T00:37:00 <-- to: 2025-09-09T00:38:00 이기 때문
2025-09-09T00:36:00
2025-09-09T00:35:00
```

#### 바라는 동작 및 분석
- 핵심 메서드: `mark_chunk_completed`
1. 요청 시점과 카운트
	- to: 2025-09-09T00:50:00
	- count: 13
2. 종료 시점 계산
	- to: 2025-09-09T00:50:00 <-- 내부적으로는 db레코드의 utc로 가정, 시작점 포함 **처리할때 하나 빼자**
	- end: 2025-09-09T00:38:00
	- count: 12 <-- db 레코드의 시간으로 가정한 갯수, 계산 통일성
3. 청크 갯수 예상
	- chunk_size: 5 <-- 기본 200, 마이크로 테스트에서만 5로
	- chunk_cont: 3
4. first_chunk
	- chunk_start: 2025-09-09T00:50:00 <-- 시작부터 꼬임, 업비트는 정렬 시간 다음을 제공
	- chunk_end: 2025-09-09T00:46:00
	- count: 5
5. 겹침 분석
	- status: NO_OVERLAP
	- api_start: 2025-09-09T00:50:00
	- api_end: 2025-09-09T00:46:00
6. 청크 수집 <-- 기본적으로 to, count 파라미터로 수집
	- to: 2025-09-09T00:50:00
	- count: 5
	- last_time: 2025-09-09T00:46:00
	- total_collected: 5
7. next_chunk
	- chunk_start: 2025-09-09T00:45:00 <-- last_time - dt
	- chunk_end: 2025-09-09T00:41:00
	- count: 5
8. 겹침 분석
	- status: NO_OVERLAP
	- api_start: 2025-09-09T00:45:00
	- api_end: 2025-09-09T00:41:00
9. 청크 수집
	- to: 2025-09-09T00:45:00
	- count: 5
	- last_time: 2025-09-09T00:41:00 <-- 요청과 비교
	- total_collected: 10 <-- 요청과 비
10. next_chunk
	- chunk_start: 2025-09-09T00:40:00 <-- last_time - dt
	- chunk_end: 2025-09-09T00:38:00
	- count: 3
11. 겹침 분석
	- status: NO_OVERLAP
	- api_start: 2025-09-09T00:40:00
	- api_end: 2025-09-09T00:38:00
12. 청크 수집
    - to: 2025-09-09T00:40:00
	- count: 3
	- last_time: 2025-09-09T00:38:00 <-- 요청과 비교
	- total_collected: 13 <-- 요청과 비교

### 문제 해결 방안
- 내부 연산은 기존 방식대로 db레코드의 utc 시간을 다룬다는 가정으로 통일
- 요청에 to가 포함된 경우 업비트의 to exclusive 특성을 고려하여 처음 청크의 시작 시간을 한프레임 과거로 옮긴다음 로직을 시작한다.
- `_fetch_chunk_from_api` to파라미터가 있는 요청을 청크 처리 후 요청할 때 시간을 미래로 한프레임 옮긴다.
- **주의: count_only, end_only 는 to가 없으므로 처음은 바로 `_fetch_chunk_from_api` count 만 사용하고 다음 청크는 이어서 처리한다.

### **분석 중 발견한 `candle_data_provider.py`의 문제점**
- `_fetch_chunk_from_api` 수집 메서드가 포함된 메서드
	- `mark_chunk_completed` : 2개
	- `_collect_data_by_overlap_strategy` : 3개
- `_save_candles_to_repository` db 저장 메서드가 포함된 메서드
	- `mark_chunk_completed` : 1개
- 위 결과로 보면 현재 청크 수집은 `mark_chunk_completed` 가 담당 중이나 반복 로직이 없음
- `candle_data_provider.py` 에는 `get_candles` 같은 기능이 지금 존재 하지 않음
- **목표는 `get_candles(timeframe, symbol, count, to, end)`를 제공하거나 그에 준하는 클라이언트가 있어야함**

#### db 데이터 확인용 명령
```powershell
cd d:\projects\upbit-autotrader-vscode && python -c "  
import sqlite3  
conn = sqlite3.connect('data/market_data.sqlite3')  
cursor = conn.cursor()  
cursor.execute('SELECT candle_date_time_utc, candle_date_time_kst, timestamp FROM candles_KRW_BTC_1m ORDER BY candle_date_time_utc DESC')  
results = cursor.fetchall()  
print('=== KRW-BTC 1분 캔들 데이터 (UTC 시간 내림차순) ===')  
print('UTC 시간\t\tKST 시간\t\t타임스탬프')  
print('-' * 100)  
for row in results:print(f'{row[0]}\t{row[1]}\t{row[2]}')  
conn.close()  
"
```

