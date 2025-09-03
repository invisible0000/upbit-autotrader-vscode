# 업비트 WebSocket API 테스트 방법론 v6.0 (실제 API 기반)

## 🎯 **핵심 원칙**
- **전역 관리자 기반**: WebSocketManager 중심 테스트
- **API 키 선택적**: Public/Private 기능 분리 테스트
- **실제 API 우선**: Mock 없이 실제 업비트 API로 검증
- **간결한 5테스트 패턴**: 필수 기능만 검증
- **WebSocketClient 활용**: 상위 레벨 인터페이스 테스트

## 🚀 **v6.0 주요 개선사항**
- **실제 API 테스트**: Mock 제거, 실제 업비트 WebSocket API 연동
- **DDD 통합**: Application Service로 WebSocket v6 생명주기 관리
- **자동 인증 관리**: API 키 설정 자동화, 테스트 코드 단순화
- **리소스 자동 정리**: WeakRef 기반 자동 정리로 테스트 격리 보장

## 📁 **파일 구조 (v6.0 간소화)**
```
tests/infrastructure/test_external_apis/upbit/test_websocket_v6/
├── conftest.py                          # 공통 픽스처 (전역 관리자)
├── test_websocket_manager.py            # 전역 관리자 핵심 테스트
├── test_websocket_client.py             # 클라이언트 테스트
├── test_public_features.py              # Public 기능 통합 테스트
├── test_private_features.py             # Private 기능 통합 테스트 (API 키 필요)
└── test_integration_scenarios.py       # 실제 시나리오 통합 테스트
```

## 🧪 **표준 5테스트 패턴**

### **핵심 컴포넌트 테스트**

### **3. 기능 테스트 (검증)**

## 🚀 **실행 명령어 (v6.0 실제 API)**

### **기본 테스트 실행**

### **완전 검증 (API 키 필요)**

### **API 키 설정**

### **성능 및 안정성 테스트**

## 🔍 **핵심 검증 패턴**

### **실제 API 통합 테스트**

### **성능 검증 패턴**

### **연결 안정성 검증**

## 📈 **성능 기준 (v6.0 최적화)**

## 🎯 **테스트 전략 요약**

### **개발 단계별 테스트 적용**

1. **통합 단계**: Public 기능 실제 API 테스트
2. **배포 전**: Private 기능 포함 완전 검증
3. **운영 모니터링**: 지속적 성능 벤치마크

### **실패 처리 방침**
- **API 키 없음**: Private 테스트 자동 스킵
- **네트워크 오류**: 재시도 후 실패 시 건너뜀
- **Rate Limit**: 지수 백오프 자동 적용

---

## 🆕 **v6.0 테스트 방법론 특징**

### **1. WebSocketManager 중심**
- 하나의 WebSocketManager로 모든 기능 통합 테스트
- 중복 연결 방지 및 자원 효율성 극대화

### **2. 클라이언트 활용**
- WebSocketClient를 통한 고수준 API 테스트
- 개별 컴포넌트별 격리된 테스트 환경

### **3. 선택적 API 키 지원**
- Public 기능은 API 키 없이 완전 테스트
- Private 기능은 API 키 있을 때만 테스트

### **4. 자동화된 리소스 관리**
- WeakRef 기반 자동 정리로 테스트 간 격리 보장
- 메모리 누수 없는 안정적 테스트 환경

**v6.0: 전역 관리자 + 클라이언트 활용 + 자동 리소스 관리**
