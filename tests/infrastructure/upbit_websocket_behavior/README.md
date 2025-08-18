# Upbit WebSocket Behavior Tests

## 📋 테스트 구조

### 완료된 테스트
- [ ] `test_quotation_websocket.py` - API키 불필요 시세 WebSocket
- [ ] `test_private_websocket.py` - API키 필요 Private WebSocket

### 테스트 요구사항
1. **기존 인프라 활용**: `ApiKeyService`를 통한 API 키 관리
2. **DDD 준수**: Infrastructure 계층 테스트
3. **실제 연결 테스트**: Dry-run 우선, 실제 API 연결 검증

## 🔧 준비 상태

### Private WebSocket 구현 상태
- **파일**: `upbit_websocket_private_client.py` (80% 완료)
- **주요 기능**: JWT 인증, myOrder/myAsset 구독
- **남은 작업**: 메시지 핸들러 통합, 에러 처리 완성

### 기존 인프라 연동 포인트
- `ApiKeyService`: API 키 안전 관리
- `UpbitAuthenticator`: JWT 토큰 생성
- `create_component_logger`: 표준 로깅

## 🎯 다음 세션 목표
1. Private WebSocket 완성
2. 통합 테스트 구조 정립
3. API 키 기반 실제 연결 검증
