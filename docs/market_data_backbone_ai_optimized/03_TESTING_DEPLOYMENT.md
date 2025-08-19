# MarketDataBackbone V2 - 테스트 & 배포 가이드 (AI 최적화 문서 3/3)

## ✅ **테스트 검증 체크리스트**

### **Phase 2.1 완료 검증 (81개 테스트)**
```yaml
Phase 1 기반 기능: 62/62 테스트 통과 ✅
Phase 2.1 통합 기능: 19/19 테스트 통과 ✅
전략적 최적화: 7개 시나리오 완료 ✅

총합: 81개 테스트 모두 통과 ✅
```

### **긴급 검증 명령어**
```powershell
# 전체 테스트 실행 (5분 소요)
pytest tests/market_data_backbone_v2/ -v --tb=short

# 핵심 기능만 빠른 확인 (1분 소요)
python demonstrate_phase_2_1_unified_api.py

# 파일 크기 위험도 확인
Get-ChildItem upbit_auto_trading/infrastructure/market_data/*.py |
ForEach-Object { "{0}: {1} lines" -f $_.Name, (Get-Content $_.FullName | Measure-Object -Line).Lines }
```

## 🧪 **테스트 시나리오 설명**

### **기본 기능 테스트 (SC01-SC06)**
```python
# SC01: 기본 API 응답
class BasicApiResponseTest:
    """REST API 기본 연결 및 응답 검증"""
    def test_basic_connection(self):
        # 업비트 API 연결 가능 여부
        # 기본 응답 형식 검증
        # 에러 처리 동작 확인

# SC02: 멀티 심볼 처리
class MultiSymbolTest:
    """여러 코인 동시 처리 검증"""
    def test_concurrent_requests(self):
        # BTC, ETH, XRP 동시 요청
        # 응답 시간 및 정확성 검증
        # 메모리 사용량 확인
```

### **고급 기능 테스트 (SC07-SC12)**
```python
# SC11: 전략적 데이터 수집
class StrategicDataCollectionTest:
    """ROI 기반 지능형 데이터 수집 검증"""
    def test_roi_optimization(self):
        # 포지션별 맞춤 데이터 제공
        # 캐시 활용률 최적화
        # 실시간 vs 히스토리 균형

# SC12: 실제 거래 패턴 시뮬레이션
class RealTradingPatternTest:
    """실제 자동매매 상황 재현"""
    def test_live_trading_simulation(self):
        # 진입/보유/청산 상태별 데이터 요구
        # 혼합 시나리오 처리
        # 성능 및 안정성 검증
```

## 🚀 **Phase 2.2 배포 시나리오**

### **배포 전 안전 점검**
```powershell
# 1. 코드 품질 검증
Get-ChildItem upbit_auto_trading/domain -Recurse -Include *.py |
Select-String -Pattern "import sqlite3|import requests|from PyQt6"
# 결과: 없어야 함 (DDD 위반 검출)

# 2. 로깅 규칙 준수 확인
Get-ChildItem upbit_auto_trading -Recurse -Include *.py |
Select-String -Pattern "print\("
# 결과: Infrastructure 외부에서 없어야 함

# 3. 테스트 커버리지 확인
pytest --cov=upbit_auto_trading/infrastructure/market_data tests/market_data_backbone_v2/
# 목표: 80% 이상
```

### **단계별 배포 계획**
```yaml
1단계 - 파일 분리 (1일):
  - unified_market_data_api.py → 3개 파일 분리
  - data_unifier.py → 3개 파일 분리
  - 테스트 마이그레이션 및 검증

2단계 - 실제 API 연동 (2일):
  - 업비트 REST API 클라이언트 연결
  - 업비트 WebSocket 클라이언트 연결
  - 실제 데이터 기반 통합 테스트

3단계 - 성능 최적화 (1일):
  - 실제 환경 성능 튜닝
  - 메모리 및 CPU 사용량 최적화
  - 최종 안정성 검증
```

## 📊 **성능 벤치마크 기준**

### **응답 시간 기준**
```yaml
캔들 데이터 200개 로딩: < 100ms
호가 데이터 실시간 업데이트: < 50ms
WebSocket 연결 설정: < 1000ms
캐시 히트 응답: < 10ms
API Rate Limit 준수: 90% 이하 사용률
```

### **메모리 사용량 기준**
```yaml
기본 메모리 사용: < 50MB
캐시 포함 최대 사용: < 200MB
24시간 연속 운영 후: < 250MB (메모리 누수 방지)
동시 심볼 10개 처리: < 300MB
```

### **안정성 기준**
```yaml
API 연결 실패 시: 자동 재연결 (3회 시도)
WebSocket 끊김 시: 자동 복구 (5초 이내)
잘못된 데이터 수신 시: 검증 후 폐기
네트워크 지연 시: Graceful degradation
```

## 🔧 **배포 환경 설정**

### **환경 변수 설정**
```powershell
# API 키 설정 (실거래용)
$env:UPBIT_ACCESS_KEY = "your_access_key_here"
$env:UPBIT_SECRET_KEY = "your_secret_key_here"

# 로깅 설정
$env:UPBIT_CONSOLE_OUTPUT = "true"
$env:UPBIT_LOG_SCOPE = "verbose"
$env:UPBIT_COMPONENT_FOCUS = "MarketDataBackbone"

# 성능 튜닝 설정
$env:MARKET_DATA_CACHE_TTL = "300"  # 5분
$env:MARKET_DATA_MAX_MEMORY = "200"  # 200MB
$env:WEBSOCKET_HEARTBEAT_INTERVAL = "30"  # 30초
```

### **데이터베이스 설정**
```powershell
# 3-DB 구조 확인
python tools/super_db_table_viewer.py settings
python tools/super_db_table_viewer.py strategies
python tools/super_db_table_viewer.py market_data

# 스키마 업데이트 (필요 시)
python tools/update_market_data_schema.py
```

## 🚨 **배포 후 모니터링**

### **실시간 모니터링 명령어**
```powershell
# 시스템 상태 모니터링
python tools/monitor_market_data_backbone.py --interval 60

# 성능 지표 확인
python tools/performance_report.py --period "last_24h"

# 에러 로그 확인
Get-Content logs/market_data_backbone.log -Tail 50 | Select-String "ERROR"
```

### **성능 알림 설정**
```python
# 성능 임계값 모니터링
class PerformanceMonitor:
    def check_performance_thresholds(self):
        metrics = self.get_current_metrics()

        if metrics.response_time > 100:  # 100ms 초과
            self.send_alert("응답 시간 임계값 초과")

        if metrics.memory_usage > 200_000_000:  # 200MB 초과
            self.send_alert("메모리 사용량 임계값 초과")

        if metrics.error_rate > 0.01:  # 1% 초과
            self.send_alert("에러율 임계값 초과")
```

## 🎯 **차트 뷰어 연동 준비**

### **차트 뷰어 개발을 위한 백본 준비 상태**
```python
# 차트 뷰어에서 사용할 수 있는 백본 인터페이스
class ChartViewerReadyInterface:
    """차트 뷰어 개발에 최적화된 백본 인터페이스"""

    async def get_chart_candles(self, symbol: str, timeframe: str,
                               count: int = 200) -> List[CandleData]:
        """차트용 캔들 데이터 (최적화된 응답 속도)"""

    async def subscribe_realtime_chart(self, symbol: str, timeframe: str,
                                     callback: Callable):
        """실시간 차트 업데이트 (50ms 이내 응답)"""

    async def get_orderbook_for_chart(self, symbol: str) -> OrderbookData:
        """호가창용 데이터 (깊이 20단계 보장)"""

    def get_cache_statistics(self) -> CacheStatistics:
        """캐시 성능 모니터링 (차트 최적화용)"""
```

### **차트 뷰어 개발 시 백본 활용 예시**
```python
# 차트 뷰어에서 백본 사용 패턴
async def setup_chart_data(self):
    """차트 초기 데이터 로딩"""
    # 히스토리 데이터 로딩 (빠른 응답)
    candles = await self.backbone.get_chart_candles("KRW-BTC", "1m", 200)

    # 실시간 업데이트 구독 (지연 최소화)
    await self.backbone.subscribe_realtime_chart(
        "KRW-BTC", "1m", self.on_candle_update
    )

async def on_candle_update(self, new_candle):
    """실시간 캔들 업데이트 처리"""
    # 차트 UI 즉시 업데이트 (50ms 이내)
    self.chart_widget.add_new_candle(new_candle)
```

## 🏁 **Phase 2.2 완료 기준**

### **완료 조건**
```yaml
✅ 파일 분리: 모든 파일 200라인 이하
✅ 실제 API: 업비트 API 완전 연동
✅ 성능 기준: 모든 벤치마크 통과
✅ 테스트: 85개 이상 테스트 통과
✅ 차트 준비: 차트 뷰어 개발 가능 상태
```

### **성공 검증 스크립트**
```powershell
# Phase 2.2 완료 검증
python verify_phase_2_2_completion.py

# 차트 뷰어 개발 준비 확인
python verify_chart_viewer_readiness.py

# 전체 시스템 통합 테스트
python run_integration_tests.py --full
```

---

**🎯 MarketDataBackbone V2 완성으로 차트 뷰어 개발 준비 완료!**

*AI 최적화 문서 3/3 완료 - 총 3개 문서로 모든 정보 통합*
