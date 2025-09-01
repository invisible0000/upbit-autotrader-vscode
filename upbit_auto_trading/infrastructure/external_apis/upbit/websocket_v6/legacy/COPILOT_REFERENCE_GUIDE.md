# 📚 WebSocket v6 개발을 위한 참조 문서 목록

## 🎯 코파일럿에게 제공해야 할 핵심 문서들

### 1. 기획 및 명세 문서 (필수)
- `docs/upbit_API_reference/websocket_v6/WEBSOCKET_V6_FINAL_SPECIFICATION.md`
- `docs/upbit_API_reference/websocket_v6/WEBSOCKET_V6_COMPREHENSIVE_PLAN.md`
- `upbit_auto_trading/infrastructure/external_apis/upbit/websocket_v6/README.md`

### 2. 기존 v5 시스템 참조 (필수)
```python
# 물리적 연결 재사용을 위한 v5 클라이언트
upbit_auto_trading/infrastructure/external_apis/upbit/websocket_v5/
├── upbit_websocket_public_client.py    # 핵심: Public WebSocket 구현
├── upbit_websocket_private_client.py   # 핵심: Private WebSocket 구현
├── models.py                           # 데이터 모델 참조
├── exceptions.py                       # 예외 체계 참조
├── config.py                          # 설정 구조 참조
└── subscription_manager.py            # 구독 로직 참조 (v6에서 재구현)
```

### 3. 전역 Rate Limiter 시스템 (핵심)
```python
# v6에서 반드시 통합해야 할 Rate Limiter
upbit_auto_trading/infrastructure/external_apis/upbit/
├── upbit_rate_limiter.py              # GCRA 기반 전역 Rate Limiter
├── dynamic_rate_limiter_wrapper.py    # 429 에러 자동 조정
└── upbit_auth.py                      # JWT 인증 시스템
```

### 4. 로깅 시스템 (필수)
```python
# Infrastructure 로깅 사용 필수
upbit_auto_trading/infrastructure/logging/
└── __init__.py                        # create_component_logger 함수
```

### 5. 업비트 API 공식 문서 (참조)
- [업비트 WebSocket API 공식 문서](https://docs.upbit.com/docs/websocket-api)
- 구독 덮어쓰기 정책, 티켓 시스템, Rate Limit 정책

### 6. DDD 아키텍처 가이드 (필수)
```
프로젝트 루트의 .github/copilot-instructions.md
- DDD 4계층 구조 (Domain은 외부 의존 없음)
- Infrastructure 계층 규칙
- 로깅 정책 (print() 금지)
- PowerShell 전용 명령어
```

## 🚀 개발 시작 시 권장 순서

### Phase 1: 환경 이해
1. 기존 v5 클라이언트 분석 (`upbit_websocket_public_client.py`)
2. Rate Limiter 동작 방식 이해 (`upbit_rate_limiter.py`)
3. 인증 시스템 파악 (`upbit_auth.py`)

### Phase 2: 핵심 구조 구현
1. `types.py` - 기본 이벤트 타입 정의
2. `global_websocket_manager.py` - 싱글톤 관리자
3. `subscription_state_manager.py` - 구독 상태 통합

### Phase 3: 프록시 인터페이스
1. `websocket_client_proxy.py` - 컴포넌트 인터페이스
2. `component_lifecycle_manager.py` - 자동 정리

## ⚠️ 주의사항

### 절대 금지
- v5 호환성 레이어 구현 금지 (v6 완성 시 v5 완전 폐기)
- Domain 계층에 외부 의존성 추가 금지
- print() 사용 금지 (Infrastructure 로깅만)
- Unix 명령어 사용 금지 (PowerShell만)

### 필수 준수
- 전역 Rate Limiter 통합 (모든 업비트 요청)
- WeakRef 기반 자동 정리
- asyncio 기반 비동기 처리
- @dataclass 타입 안전성
- Infrastructure 로깅: `create_component_logger()`

## 🎯 성공 기준
- 업비트 구독 덮어쓰기 문제 100% 해결
- 전역 Rate Limiter 완전 통합
- 메모리 누수 0건
- v5 완전 대체

---

*이 문서는 다음 코파일럿이 효율적으로 개발할 수 있도록 하는 가이드입니다.*
