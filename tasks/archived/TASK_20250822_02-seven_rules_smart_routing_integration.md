# 📋 TASK_20250822_02: 7규칙 전략 스마트 라우팅 적용 및 최종 검증

## 🎯 태스크 목표
- **주요 목표**: 완성된 스마트 라우팅 V2.0을 7규칙 전략 시스템에 적용하여 프로젝트 최종 목표 달성
- **완료 기준**:
  - ✅ `python run_desktop_ui.py` → 전략 관리 → 트리거 빌더에서 7규칙 구성 완벽 동작
  - ✅ 실시간 시장 데이터 기반 7규칙 전략 정상 실행
  - ✅ 스마트 라우팅을 통한 최적화된 데이터 수집 성능 달성
  - ✅ Dry-Run 모드에서 모든 7규칙 시나리오 검증 완료

## 📊 현재 상황 분석

### ✅ 완료된 기반 작업
1. **스마트 라우팅 V2.0 시스템 완성**
   - 위치: `upbit_auto_trading/infrastructure/market_data_backbone/smart_routing/`
   - 성능: 평균 응답시간 0.58ms, 15개 테스트 100% 통과
   - 기능: WebSocket/REST 자동 선택, 데이터 형식 통일, 캐시 시스템

2. **7규칙 전략 정의** (Golden Rules 문서 기준)
   - RSI 과매도 진입
   - 수익시 불타기
   - 계획된 익절
   - 트레일링 스탑
   - 하락시 물타기
   - 급락 감지
   - 급등 감지

### 🔍 분석 필요 사항
1. **7규칙 전략 현재 구현 상태**: 트리거 빌더에서 어느 정도 구성 가능한지 확인
2. **데이터 의존성**: 각 규칙이 필요로 하는 시장 데이터 타입 및 빈도 분석
3. **성능 요구사항**: 실시간 전략 실행을 위한 레이턴시 및 정확도 요구사항

### 사용 가능한 리소스
- **완성된 스마트 라우팅**: 최적화된 데이터 수집 시스템
- **기존 7규칙 구현**: `docs/BASIC_7_RULE_STRATEGY_GUIDE.md` 참조
- **트리거 빌더 UI**: `run_desktop_ui.py` → 전략 관리 시스템
- **DDD 아키텍처**: Domain/Application/Infrastructure 분리된 설계

## 🔄 체계적 작업 절차 (필수 준수)

### 8단계 작업 절차
1. **📋 작업 항목 확인**: 7규칙 전략과 스마트 라우팅 통합 요구사항 파악
2. **🔍 검토 후 세부 작업 항목 생성**: 규칙별 데이터 요구사항 및 통합 작업 분해
3. **⚡ 작업중 마킹**: 해당 작업 항목을 `[-]` 상태로 변경
4. **⚙️ 작업 항목 진행**: 실제 통합 및 검증 작업 수행
5. **✅ 작업 내용 확인**: 7규칙 동작 및 성능 검증
6. **📝 상세 작업 내용 업데이트**: 태스크 문서에 진행사항 기록
7. **[x] 작업 완료 마킹**: 해당 작업 항목을 완료 상태로 변경
8. **⏳ 작업 승인 대기**: 다음 단계 진행 전 검토 및 승인

## 🗺️ 작업 계획

### Phase 1: 7규칙 전략 현황 분석 (우선순위 1)
- [ ] 트리거 빌더에서 현재 구성 가능한 7규칙 상태 점검
- [ ] 각 규칙별 필요 데이터 타입 및 빈도 분석
  - [ ] RSI 과매도: 캔들 데이터 (1m, 5m, 15m), RSI 계산
  - [ ] 수익시 불타기: 실시간 티커, 포지션 정보
  - [ ] 계획된 익절: 실시간 티커, 목표가 설정
  - [ ] 트레일링 스탑: 실시간 티커, 고점 추적
  - [ ] 하락시 물타기: 실시간 티커, 평균단가 계산
  - [ ] 급락 감지: 실시간 티커, 변동률 모니터링
  - [ ] 급등 감지: 실시간 티커, 변동률 모니터링
- [ ] 스마트 라우팅 최적화 지점 식별

### Phase 2: 스마트 라우팅 전략 데이터 연동 (우선순위 1)
- [ ] 7규칙에 필요한 데이터 타입별 스마트 라우팅 채널 최적화
  - [ ] 실시간 티커: WebSocket 우선 설정
  - [ ] 캔들 데이터: REST API 고정 설정
  - [ ] 대량 히스토리: REST API 배치 처리
- [ ] 전략 실행 엔진에 스마트 라우터 통합
- [ ] 데이터 캐싱 전략으로 성능 최적화

### Phase 3: 7규칙 통합 검증 및 테스트 (우선순위 1)
- [ ] 각 규칙별 개별 테스트 (Dry-Run 모드)
  - [ ] RSI 과매도 진입 시나리오 테스트
  - [ ] 수익시 불타기 로직 테스트
  - [ ] 익절/손절 시나리오 테스트
  - [ ] 급락/급등 감지 테스트
- [ ] 7규칙 조합 시나리오 테스트
- [ ] 실시간 데이터 기반 End-to-End 테스트
- [ ] 성능 벤치마크 (레이턴시, 정확도, 안정성)

### Phase 4: UI 및 사용자 경험 개선 (우선순위 2)
- [ ] 트리거 빌더에 스마트 라우팅 상태 표시
- [ ] 7규칙 성능 모니터링 대시보드 추가
- [ ] 실시간 전략 상태 및 데이터 소스 표시
- [ ] 사용자 가이드 및 도움말 업데이트

## 🛠️ 개발할 도구 및 개선사항

### 신규 개발 필요
- `strategy_data_optimizer.py`: 7규칙 전략별 데이터 수집 최적화 도구
- `seven_rules_validator.py`: 7규칙 통합 검증 자동화 도구
- `performance_profiler.py`: 전략 실행 성능 프로파일링 도구

### 기존 시스템 개선
- **전략 실행 엔진**: 스마트 라우터 데이터 소스 통합
- **트리거 빌더**: 데이터 소스 상태 표시 기능
- **모니터링 시스템**: 실시간 성능 메트릭 추가

## 🎯 성공 기준

### 기능적 성공 기준 (프로젝트 최종 목표)
- ✅ **7규칙 완전 구현**: 모든 규칙이 트리거 빌더에서 구성 가능
- ✅ **실시간 전략 실행**: 스마트 라우팅 기반 실시간 데이터 처리
- ✅ **Dry-Run 검증**: 모든 시나리오에서 안전한 시뮬레이션 실행
- ✅ **UI 통합**: `python run_desktop_ui.py`에서 완전한 7규칙 워크플로우 지원

### 성능적 성공 기준
- ✅ **레이턴시**: 데이터 수집 → 전략 판단 → 신호 생성 < 500ms
- ✅ **정확도**: 시장 데이터 기반 전략 신호 정확도 > 95%
- ✅ **안정성**: 24시간 연속 운영 시 99.5% 가용성
- ✅ **효율성**: 스마트 라우팅으로 데이터 수집 효율성 30% 향상

### 사용자 경험 성공 기준
- ✅ **직관성**: 7규칙 설정이 5분 내 완료 가능
- ✅ **투명성**: 모든 전략 판단 근거 실시간 표시
- ✅ **안전성**: Dry-Run 기본 설정, 실거래 2단계 확인

## 💡 작업 시 주의사항

### 안전성 원칙 (Golden Rules 준수)
- **Dry-Run 우선**: 모든 주문은 기본 dry_run=True
- **2단계 확인**: 실거래 전환 시 사용자 명시적 확인 필수
- **백업 체계**: 기존 전략 시스템 백업 후 작업
- **단계별 검증**: 각 규칙별 개별 검증 후 통합 테스트

### DDD 아키텍처 준수
- **Domain 순수성**: 7규칙 비즈니스 로직은 외부 의존성 없이 구현
- **Infrastructure 격리**: 스마트 라우팅은 Infrastructure 레이어에서만 사용
- **Application 조합**: UseCase에서 Domain과 Infrastructure 조합

### 성능 최적화 고려사항
- **캐싱 전략**: 자주 사용되는 RSI, 이동평균 등 계산 결과 캐시
- **배치 처리**: 여러 심볼 동시 처리로 API 효율성 향상
- **메모리 관리**: 실시간 데이터 스트림의 메모리 사용량 모니터링

## 🚀 즉시 시작할 작업

### 1. 현재 7규칙 구현 상태 점검
```powershell
# UI 실행하여 트리거 빌더 현재 상태 확인
python run_desktop_ui.py

# 7규칙 관련 코드 위치 파악
Get-ChildItem upbit_auto_trading -Recurse -Include "*.py" | Select-String -Pattern "RSI|rule|strategy" -List
```

### 2. 데이터 요구사항 분석
```python
# 각 7규칙별 필요 데이터 타입 정의
SEVEN_RULES_DATA_REQUIREMENTS = {
    "rsi_oversold": {"ticker": "1m", "candles": "1m,5m,15m"},
    "profit_pyramiding": {"ticker": "realtime", "position": "current"},
    "planned_profit_taking": {"ticker": "realtime", "target": "user_defined"},
    "trailing_stop": {"ticker": "realtime", "high_tracking": "continuous"},
    "averaging_down": {"ticker": "realtime", "average_price": "calculated"},
    "crash_detection": {"ticker": "realtime", "volatility": "5m_window"},
    "surge_detection": {"ticker": "realtime", "volatility": "5m_window"}
}
```

### 3. 스마트 라우팅 연동 준비
```python
# 7규칙 전용 데이터 수집 최적화 클래스 설계 시작
class StrategyDataCollector:
    def __init__(self, smart_router):
        self.router = smart_router

    async def collect_for_seven_rules(self, symbol: str):
        # 7규칙에 최적화된 데이터 수집 로직
        pass
```

## 📋 관련 문서 및 리소스

### 핵심 참고 문서
- **7규칙 가이드**: `docs/BASIC_7_RULE_STRATEGY_GUIDE.md`
- **DDD 가이드**: `docs/DDD_아키텍처_패턴_가이드.md`
- **복잡 시스템 테스트**: `docs/COMPLEX_SYSTEM_TESTING_GUIDE.md`
- **Copilot 지침**: `.github/copilot-instructions.md`

### 기존 전략 시스템
- **전략 도메인**: `upbit_auto_trading/domain/strategy/`
- **전략 어플리케이션**: `upbit_auto_trading/application/strategy/`
- **UI 전략 관리**: `upbit_auto_trading/ui/desktop/`

### 데이터베이스 스키마
- **전략 DB**: `data/strategies.sqlite3`
- **설정 DB**: `data/settings.sqlite3`
- **마켓 데이터**: `data/market_data.sqlite3`

## 🔄 이전 태스크와의 연관성

### 선행 완료 작업
- **TASK_20250822_01**: 스마트 라우팅 V2.0 시스템 통합 (진행 중)
- **스마트 라우팅 V2.0**: 테스트 시스템 구축 완료

### 병행 가능한 작업
- **API 매니저 통합**: 실제 업비트 API 연동 작업
- **모니터링 개선**: 성능 메트릭 대시보드 고도화
- **문서 업데이트**: 사용자 가이드 및 개발 문서

---

**다음 에이전트 시작점**:
1. `python run_desktop_ui.py` 실행하여 현재 7규칙 구성 가능 상태 확인
2. 트리거 빌더에서 각 규칙별 설정 가능 범위 파악
3. 데이터 요구사항과 스마트 라우팅 최적화 지점 식별 후 통합 작업 시작

**현재 상태**: 스마트 라우팅 V2.0 완성, 7규칙 전략 시스템 통합 및 최종 목표 달성 단계
