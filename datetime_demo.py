"""
datetime_demo.py
루트에 배치: 파이썬 datetime 연산 특성 파악용 데모 스크립트
- datetime 끼리 연산(차이) 예제
- 날짜 간 총 일수 계산법
- datetime에 포함된 주요 메서드/속성 예제
- 엣지 케이스와 활용 팁

실행: Windows PowerShell에서 `python datetime_demo.py`
"""
from datetime import datetime, date, time, timedelta, timezone
import calendar


def print_header(title):
    print('\n' + '='*10 + ' ' + title + ' ' + '='*10)


print_header('1. datetime 끼리 연산')
# 예제 1: 2000-01-01 00:00:00 - 1900-01-01 00:00:00
dt1 = datetime(2000,1,1,0,0,0)
dt2 = datetime(1900,1,1,0,0,0)
diff1 = dt1 - dt2
print('2000-01-01 00:00:00 - 1900-01-01 00:00:00 =>', diff1, '(', diff1.days, 'days,', diff1.seconds, 'seconds )')

# 예제 2: 2024-12-31 - 2023-12-31 (date 객체 사용 가능)
d1 = date(2024,12,31)
d2 = date(2023,12,31)
days_between = d1 - d2
print('2024-12-31 - 2023-12-31 =>', days_between, '(', days_between.days, 'days )')

# 예제 3: 2025-09-11 01:00:00 - 2025-09-10 23:00:00
# 시간대가 없을 때는 naive datetime끼리 직접 연산 가능
dt_a = datetime(2025,9,11,1,0,0)
dt_b = datetime(2025,9,10,23,0,0)
diff3 = dt_a - dt_b
print('2025-09-11 01:00:00 - 2025-09-10 23:00:00 =>', diff3, '(', diff3.total_seconds(), 'seconds )')

print_header('요약')
print('-> datetime / date 객체끼리 뺄셈이 가능하며 결과는 timedelta')
print('-> timezone-aware(아래 예)와 naive datetime은 섞어 연산 불가')

print_header('2. 어떤 datetime 이 총 몇일인지 계산하는 법')
# 방법 A: 두 datetime/date 차이를 timedelta로 구해서 .days 사용
start = datetime(2024,1,1)
end = datetime(2025,1,1)
print('기간', start, '부터', end, '까지 =>', (end - start).days, 'days')

# 방법 B: 날짜 단위로 포함되는 개수 계산 (예: 월단위, 윤년 고려)
# 예: 2020-02-01 부터 2020-03-01 까지
s = date(2020,2,1)
e = date(2020,3,1)
print('2020-02-01 ~ 2020-03-01 =>', (e - s).days, 'days (윤년 포함 확인)')

# 시간대가 포함된 경우: UTC로 통일하거나 tz-aware끼리 연산
print_header('시간대 예시 (tz-aware vs naive)')
utc = timezone.utc
aware1 = datetime(2025,9,11,0,0,0, tzinfo=utc)
aware2 = datetime(2025,9,10,23,0,0, tzinfo=timezone(timedelta(hours=-1)))
print('aware1:', aware1)
print('aware2:', aware2)
try:
    print('aware1 - aware2 =>', aware1 - aware2)
except Exception as e:
    print('에러 발생:', e)

print_header('3. datetime에 포함된 주요 함수/속성 설명과 예제')
now = datetime.now()
print('now()', now)
print('now().isoformat() =>', now.isoformat())
print('now().timestamp() =>', now.timestamp())
print('replace 예제: set hour=0 =>', now.replace(hour=0, minute=0, second=0, microsecond=0))
print('combine 예제: date + time =>', datetime.combine(date(2025,9,11), time(12,34,56)))

print_header('4. 기타 활용법 및 엣지 케이스')
print('- 윤년: 2020년 2월은 29일까지 있음 (check via calendar.isleap)')
print('  2020 is leap?', calendar.isleap(2020))

print('- DST 및 로컬 타임: 표준 라이브러리만으로는 복잡. pytz 또는 zoneinfo 권장 (Python 3.9+는 zoneinfo 사용)')
try:
    from zoneinfo import ZoneInfo
    kst = ZoneInfo('Asia/Seoul')
    kst_dt = datetime(2025,3,30,2,30, tzinfo=kst)
    print('zoneinfo 사용 예 (Asia/Seoul):', kst_dt)
except Exception:
    print('zoneinfo 모듈 사용 불가 또는 지역 데이터 없음')

print('- naive datetime과 tz-aware datetime을 섞어 연산하면 TypeError 발생')
print('- 큰 값 차이: datetime 연산 결과의 days, seconds, microseconds 범위를 확인')

print_header('간단한 assert-style 확인 (자동 검증)')
assert diff1.days > 0
assert days_between.days == 366  # 2024이 윤년인지 확인 (2024은 윤년)
assert diff3.total_seconds() == 7200  # 2시간 차이
print('모든 간단 체크 통과')
