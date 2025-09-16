# 요청 실패 시 타임스탬프 롤백 설계안

## 방안 1: 지연된 커밋 (Delayed Commit) ⭐ 추천
```python
async def acquire_with_rollback(self, endpoint: str, method: str = 'GET'):
    # 1단계: Rate limit 체크 (타임스탬프 추가 없음)
    can_proceed, delay_time = await self._check_rate_limit_only(endpoint, method)

    if not can_proceed:
        await asyncio.sleep(delay_time)

    # 2단계: 실제 API 요청
    try:
        result = await self._make_api_request(endpoint, method)

        # 3단계: 성공 시에만 타임스탬프 커밋
        await self._commit_timestamp(endpoint, method)
        return result

    except Exception as e:
        # 4단계: 실패 시 롤백 (이미 추가 안했으므로 불필요)
        self.logger.warning(f"API 요청 실패, 타임스탬프 미커밋: {endpoint}")
        raise e
```

## 방안 2: 예약 시스템 (Reservation System)
```python
class TimestampReservation:
    def __init__(self, group, timestamp, limiter):
        self.group = group
        self.timestamp = timestamp
        self.limiter = limiter
        self.is_committed = False

    async def commit(self):
        if not self.is_committed:
            self.limiter._add_timestamp_to_window(self.group, self.timestamp)
            self.is_committed = True

    async def rollback(self):
        # 예약만 취소 (실제 윈도우엔 추가 안했으므로)
        self.is_committed = False

async def acquire_with_reservation(self, endpoint: str):
    # 1. 예약 생성
    reservation = await self._create_reservation(endpoint)

    try:
        # 2. API 요청
        result = await self._api_call(endpoint)

        # 3. 성공 시 커밋
        await reservation.commit()
        return result

    except Exception as e:
        # 4. 실패 시 롤백
        await reservation.rollback()
        raise e
```

## 구현 복잡도 평가:
- 방안 1 (지연된 커밋): 🟢 쉬움 - 기존 코드 약간 수정
- 방안 2 (예약 시스템): 🟡 중간 - 새로운 클래스 필요
- 완전한 롤백 시스템: 🔴 어려움 - 대규모 리팩터링 필요

## 결론:
**방안 1 (지연된 커밋)**이 가장 실용적입니다.
- 구현이 간단함
- 기존 코드와 호환성 좋음
- 충분한 안정성 제공
