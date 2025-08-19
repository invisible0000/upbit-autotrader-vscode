# 🎯 **MarketDataBackbone V2 코파일럿 마스터 프롬프트**

**프로젝트**: 업비트 자동매매 MarketDataBackbone V2 통합 백본 시스템
**현재 상태**: Phase 1.1 MVP 완료 (16/16 테스트 통과), Phase 1.2 WebSocket 구현 대기
**검증 명령어**: `python demonstrate_phase_1_1_success.py && pytest tests/infrastructure/market_data_backbone/v2/ -v`

## 📋 **즉시 실행 (30초)**

```powershell
cd "d:\projects\upbit-autotrader-vscode"
cat "docs\market_data_backbone_v2\README.md" | Select-Object -First 20
cat "docs\market_data_backbone_v2\development\CURRENT_STATUS.md" | Select-Object -First 20
cat "docs\market_data_backbone_v2\development\NEXT_ACTIONS.md" | Select-Object -First 20
python demonstrate_phase_1_1_success.py
```

## 🎯 **현재 임무**: Phase 1.2 WebSocket 실시간 스트림 구현

### **목표**: `backbone.stream_ticker(["KRW-BTC"])` 정상 동작
### **기간**: 2-3일
### **우선순위**:
1. **WebSocketManager 클래스 구현** (`upbit_auto_trading/infrastructure/market_data_backbone/v2/websocket_manager.py`)
2. **MarketDataBackbone에 스트림 API 추가** (stream_ticker, stream_orderbook)
3. **지능적 채널 선택 로직** (REST vs WebSocket 자동 최적화)
4. **테스트 작성** (`tests/infrastructure/market_data_backbone/v2/test_websocket_integration.py`)

## 📚 **문서 시스템**: `docs/market_data_backbone_v2/`

- **📖 README.md**: 문서 허브, 5분 온보딩 가이드
- **🧬 PROJECT_DNA.md**: 프로젝트 전체 컨텍스트
- **📊 development/CURRENT_STATUS.md**: 실시간 진행 상황
- **🚀 development/NEXT_ACTIONS.md**: 구체적 구현 가이드 (코드 예시 포함)
- **📈 phases/**: Phase별 상세 계획 및 완료 기록

## 🔧 **개발 원칙**

- **DDD 아키텍처**: Infrastructure 계층, Domain 순수성 유지
- **TDD 접근**: 테스트 우선, 점진적 구현
- **하이브리드 모델**: REST(안정성) + WebSocket(실시간성)
- **Infrastructure 로깅**: `create_component_logger()` 사용, print() 금지
- **Windows PowerShell**: Unix 명령어 금지

## ✅ **성공 검증**

```powershell
# 기존 기능 무결성
python demonstrate_phase_1_1_success.py
pytest tests/infrastructure/market_data_backbone/v2/ -v

# Phase 1.2 목표 (구현 후)
python -c "
import asyncio
from upbit_auto_trading.infrastructure.market_data_backbone.v2.market_data_backbone import MarketDataBackbone

async def test():
    backbone = MarketDataBackbone()
    async for ticker in backbone.stream_ticker(['KRW-BTC']):
        print(f'실시간: {ticker.symbol} = {ticker.current_price:,.0f}원')
        break

asyncio.run(test())
"
```

## 📝 **작업 완료 시**

1. **문서 업데이트**: `CURRENT_STATUS.md`, `NEXT_ACTIONS.md` 진행 상황 반영
2. **테스트 검증**: 모든 테스트 통과 확인
3. **시연 스크립트**: `demonstrate_phase_1_2_websocket.py` 생성
4. **Phase 1.3 계획**: 다음 단계 문서 준비

**🎯 완벽한 프로젝트 DNA 기반으로 Phase 1.2 WebSocket 통합을 완료하여 실시간 스트림 백본을 구현하세요!**
