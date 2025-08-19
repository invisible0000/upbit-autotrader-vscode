# BTC/USDT 마켓 전환 Async 에러 해결

## 🚨 문제 상황
- **증상**: BTC/USDT 마켓 전환 시 "Event loop is closed" 에러 발생
- **발생 시점**: 2025-08-19
- **영향 범위**: 차트뷰 화면의 마켓 전환 기능

## 🔍 원인 분석
- **근본 원인**: aiohttp ClientSession이 다른 이벤트 루프에서 생성되어 재사용될 때 발생
- **기술적 세부사항**: PyQt6 UI 스레드와 async 작업 간 이벤트 루프 불일치

## 🛠️ 해결 방법

### 수정 파일
`upbit_auto_trading/infrastructure/external_apis/common/api_client_base.py`

### 핵심 수정 내용
```python
def _ensure_session(self):
    try:
        current_loop = asyncio.get_running_loop()
        session_invalid = (
            self._session is None or
            self._session.closed or
            getattr(self._session, '_loop', None) != current_loop
        )

        if session_invalid:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                connector=aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
            )
    except RuntimeError:
        # 이벤트 루프가 없는 경우
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(...)
```

## ✅ 검증 결과
- KRW → BTC → USDT → BTC 마켓 전환 모두 성공
- "Event loop is closed" 에러 완전 해결
- 242개(BTC), 118개(USDT) 코인 목록 정상 로드

## 📋 관련 이슈
- `coin_list_widget.py`: Threading 격리 개선
- 복합 시스템 테스팅 가이드 적용으로 근본 원인 발견

## 🔗 참고 문서
- `docs/COMPLEX_SYSTEM_TESTING_GUIDE.md`
- 격리 테스트 파일: `test_btc_usdt_issue.py`
