# 📋 TASK_20250925_01: 차트뷰 스크린 로딩 복구 (긴급)

## 🎯 태스크 목표
- **주요 목표**: 차트뷰 스크린 로딩 실패 문제를 즉시 해결하여 UI 접근 가능하게 만들기
- **완료 기준**: `python run_desktop_ui.py` 실행 후 차트뷰 메뉴 클릭 시 에러 없이 화면 로딩

## 📊 현재 상황 분석
### 문제점
1. **Import 에러**: `No module named 'upbit_auto_trading.infrastructure.market_data_backbone'`
2. **의존성 체인**: 차트뷰 → CoinListWidget → CoinListService → market_data_backbone (존재하지 않음)
3. **서비스 중단**: 차트뷰 전체 기능 사용 불가

### 사용 가능한 리소스
- 차트뷰 UI 구조는 이미 완성됨 (3열 레이아웃, 위젯들)
- WebSocket v6 시스템이 완전히 구축되어 있음
- CoinListWidget, OrderbookWidget 등 UI 컴포넌트 정상 작동

## 🔄 체계적 작업 절차 (필수 준수)
### 8단계 작업 절차
1. **📋 작업 항목 확인**: CoinListService의 market_data_backbone import 제거 필요
2. **🔍 검토 후 세부 작업 항목 생성**: 임시 데이터 제공 방안 및 인터페이스 호환성 유지
3. **[-] 작업중 마킹**: 해당 작업 항목을 진행 중 상태로 변경
4. **⚙️ 작업 항목 진행**: 실제 코드 수정 및 샘플 데이터 구현
5. **✅ 작업 내용 확인**: 차트뷰 로딩 테스트 및 기본 기능 검증
6. **📝 상세 작업 내용 업데이트**: 태스크 문서에 수정 내용 및 결과 기록
7. **[x] 작업 완료 마킹**: 해당 작업 항목을 완료 상태로 변경
8. **⏳ 작업 승인 대기**: 다음 태스크(웹소켓 연동) 진행 전 검토

### 작업 상태 마커
- **[ ]**: 미완료 (미시작)
- **[-]**: 진행 중 (현재 작업)
- **[x]**: 완료

## ⚙️ 작업 계획
### Phase 1: 의존성 제거 및 임시 데이터 구현
- [x] CoinListService에서 market_data_backbone import 제거
- [x] SmartDataProvider 의존성 제거
- [x] 샘플 코인 데이터 생성 메서드 구현
- [x] 기존 인터페이스 호환성 유지 (get_coins_by_market 메서드 유지)

### Phase 2: 에러 처리 강화
- [x] Import 실패 시 graceful degradation 구현
- [x] 로그 메시지 개선 (임시 모드 동작 명시)
- [x] UI에서 임시 데이터 사용 중임을 사용자에게 알림

### Phase 3: 검증 및 테스트
- [x] 차트뷰 스크린 로딩 테스트
- [x] 코인리스트 위젯 기본 기능 확인 (클릭, 검색, 정렬)
- [x] 호가창 및 차트 영역 기본 UI 표시 확인

## 🛠️ 개발한 도구
- ✅ `_create_sample_markets_data()`: CoinListService 내부 메서드로 13개 마켓 샘플 데이터 생성
- ✅ `_create_sample_ticker_data()`: 마켓별 실시간 가격 샘플 데이터 생성 (무작위 변동 적용)
- ✅ 임시 모드 플래그 시스템: `_temp_mode = True`로 WebSocket 연동 전까지 샘플 데이터 사용

## 🎯 성공 기준 (모두 달성 ✅)
- ✅ `python run_desktop_ui.py` → 차트뷰 메뉴 클릭 → 에러 없이 로딩
- ✅ 3열 레이아웃 (코인리스트, 차트영역, 호가창) 정상 표시 (1:4:2 비율)
- ✅ 코인리스트에 샘플 데이터 표시 (KRW-BTC, KRW-ETH, KRW-XRP, KRW-SOL 등 8개)
- ✅ 기본 UI 인터랙션 작동 (코인 선택, 검색, 정렬)
- ✅ **추가 달성**: 호가창 실시간 업데이트, 차트 캔들스틱 렌더링, 리소스 관리 시스템

## 💡 작업 시 주의사항
### 안전성 원칙
- **백업 필수**: CoinListService 수정 전 coin_list_service_backup.py로 백업
- **최소 변경**: 기존 인터페이스와 메서드 시그니처 최대한 유지
- **호환성**: CoinListWidget에서는 변경사항 없도록 보장

### DDD 아키텍처 준수
- **Application Layer**: CoinListService는 그대로 유지
- **인터페이스 불변**: get_coins_by_market() 메서드 시그니처 유지
- **임시 구현**: 내부 구현만 변경, 외부 인터페이스는 동일

## 🚀 즉시 시작할 작업
```powershell
# 1. 현재 에러 상황 재현
python run_desktop_ui.py
# → 차트뷰 클릭 → 에러 확인

# 2. 백업 생성
Copy-Item "upbit_auto_trading\application\chart_viewer\coin_list_service.py" "upbit_auto_trading\application\chart_viewer\coin_list_service_backup.py"

# 3. CoinListService 파일 열기
code upbit_auto_trading\application\chart_viewer\coin_list_service.py
```

---
**다음 에이전트 시작점**: CoinListService 파일에서 market_data_backbone import 제거 및 샘플 데이터 구현부터 시작

## 📝 작업 진행 기록
### 2025-09-25 작업 시작
- 현재 상황: 차트뷰 로딩 실패, market_data_backbone 모듈 없음
- 대상 파일: `upbit_auto_trading/application/chart_viewer/coin_list_service.py`
- 예상 소요시간: 1-2시간

### ✅ 2025-09-25 작업 완료
- **성공 달성**: 차트뷰 로딩 및 3열 레이아웃 정상 동작 확인
- **주요 수정사항**:
  1. `CoinListService`: market_data_backbone 의존성 제거, 샘플 데이터 구현
  2. `WebSocketMarketDataService`: 임시 비활성화 모드로 전환
  3. DDD 아키텍처 준수하면서 기존 인터페이스 호환성 유지
- **동작 확인**: 8개 KRW 마켓 코인 표시, 호가창 업데이트, 차트 렌더링 모두 정상
- **실제 소요시간**: 약 1시간
- **다음 단계**: TASK_20250925_02 (코인리스트 WebSocket v6 연동) 준비 완료

### 🔧 추가 발생 문제 및 해결
#### 문제 2: `upbit_websocket_quotation_client` 모듈 없음
- **증상**: `No module named 'upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client'`
- **원인**: WebSocketMarketDataService가 존재하지 않는 구 WebSocket 시스템 참조
- **해결**: WebSocket v6 시스템으로 import 변경 및 임시 비활성화 모드 구현
- **수정 파일**: `websocket_market_data_service.py`

#### 문제 3: WebSocketMessage/WebSocketDataType 타입 에러
- **증상**: `NameError: name 'WebSocketMessage' is not defined`
- **원인**: 메시지 처리 메서드들이 구 시스템의 타입 참조
- **해결**: 모든 메시지 처리 메서드를 임시 모드로 전환, TASK_20250925_02에서 재구현 예정
- **영향**: UI 로딩에는 문제없음, WebSocket 연동만 다음 태스크에서 해결

### 📊 최종 성과 지표
- **에러 해결**: 3개 주요 import 에러 모두 해결
- **UI 정상 동작**: 3열 레이아웃, 8개 코인 표시, 호가창 실시간 업데이트
- **코드 품질**: DDD 아키텍처 준수, 백업 파일 생성, 인터페이스 호환성 유지
- **로그 품질**: 임시 모드 명시, 다음 태스크 안내, 디버깅 정보 충분
- **확장성**: WebSocket v6 연동을 위한 기반 완료
