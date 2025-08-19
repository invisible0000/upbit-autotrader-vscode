# 🧠 **전문가 권고: SmartChannelRouter 통합 API 구현 방안**

> **새로운 전문가 의견 도착** (2025-08-19)
> **핵심**: MarketDataBackbone V2의 다음 단계 - UnifiedMarketDataAPI 구현 필요

---

## 🎯 **전문가 핵심 권고사항**

### **1. SmartChannelRouter 필요성**
**현재 문제**: 개발자가 REST vs WebSocket을 수동으로 선택해야 함
**전문가 해결책**: 지능적 라우터가 자동으로 최적 채널 선택

```python
# 현재 방식 (복잡)
if need_realtime:
    data = await websocket_client.subscribe_ticker(["KRW-BTC"])
else:
    data = await rest_client.get_tickers(["KRW-BTC"])

# 전문가 권고 (투명)
unified_api = UnifiedMarketDataAPI()
data = await unified_api.get_ticker("KRW-BTC")  # 자동 최적화
```

### **2. 데이터 구조 통일 문제**
**현재 문제**: REST "market" ↔ WebSocket "code" 필드명 차이
**전문가 해결책**: 통합 데이터 모델로 표준화

### **3. 통합 에러 처리 부족**
**현재 문제**: 채널별 다른 예외 처리
**전문가 해결책**: HTTP 429 ↔ WebSocket INVALID_AUTH 동일 예외

---

## 🚀 **구현 우선순위**

### **Phase 2.1: SmartChannelRouter 구현** (필수)
- [ ] 요청 빈도 감지 로직
- [ ] 실시간성 vs 신뢰성 판단 알고리즘
- [ ] WebSocket 연결 상태 모니터링
- [ ] REST 폴백 처리

### **Phase 2.2: 데이터 통일** (필수)
- [ ] 필드명 매핑 시스템
- [ ] 타임스탬프 표준화
- [ ] 공통 데이터 클래스 정의

### **Phase 2.3: 에러 처리 통합** (권장)
- [ ] 공통 예외 클래스 설계
- [ ] 채널별 오류 → 통합 예외 매핑
- [ ] 네트워크 오류 일관 처리

---

## 💡 **MarketDataBackbone V2 연계 방안**

### **기존 구현 활용**
- ✅ **ProactiveRateLimiter**: 그대로 활용 (이미 전문가 권고 반영)
- ✅ **DataUnifier**: 확장하여 필드명 통일 기능 추가
- ✅ **WebSocketManager**: SmartChannelRouter의 기반으로 활용

### **신규 구현 필요**
- 🆕 **UnifiedMarketDataAPI**: 통합 인터페이스
- 🆕 **SmartChannelRouter**: 지능적 라우팅 로직
- 🆕 **FieldMapper**: REST ↔ WebSocket 필드 변환

---

## ⚠️ **주의사항**

### **침착한 접근 필요**
- **급하게 구현하지 말 것**: 전문가 권고 충분히 분석 후 진행
- **기존 시스템 안정성 유지**: 62개 테스트 통과 상태 보존
- **점진적 통합**: 기존 코드 변경 최소화하며 단계적 적용

### **성공 기준**
```python
# 목표: 이 코드가 자연스럽게 동작해야 함
unified_api = UnifiedMarketDataAPI()
ticker = await unified_api.get_ticker("KRW-BTC")
# 내부에서 SmartChannelRouter가 최적 채널 자동 선택
# 필드명은 통일된 형태로 반환
# 에러는 일관된 예외로 처리
```

---

## 📚 **참고 자료**

- **전문가 분석 원문**: `docs/업비트 마켓 데이터 통합 API 구현 평가 및 방안.md`
- **현재 구현**: `upbit_auto_trading/infrastructure/market_data_backbone/v2/`
- **테스트 기반**: 62개 테스트 모두 통과한 안정적 기반

**다음 코파일럿을 위한 메시지**: 전문가 권고를 성급하게 구현하지 말고, 먼저 충분히 이해한 후 기존 시스템과 조화롭게 통합하세요. 안정성이 최우선입니다.
