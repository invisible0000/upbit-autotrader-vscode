# 복잡한 백본 시스템 테스트 가이드
> DDD + MVP + Infrastructure 기반 시스템의 효과적인 테스트 방법론

---

## 🎯 테스트 전략 개요

복잡한 백본 시스템에서는 **점진적 검증 + 실시간 로깅 분석**이 핵심입니다.

### 기본 원칙
- **Live Testing First**: `python run_desktop_ui.py`로 실제 동작 확인 우선
- **로그 기반 디버깅**: Infrastructure 로깅으로 문제점 추적
- **계층별 격리 테스트**: UI → Application → Domain → Infrastructure 순서
- **점진적 개선**: 작은 단위로 수정 → 즉시 검증 → 누적 개선

---

## 🔍 테스트 수행 절차

### 1. 초기 상태 확인
```powershell
# 기본 실행으로 전체 시스템 상태 파악
python run_desktop_ui.py
```
**목적**: 전체 시스템이 정상 구동되는지, 어느 부분에서 문제가 발생하는지 파악

### 2. 로그 분석 패턴
```
✅ 정상: INFO | upbit.ComponentName | ✅ 작업 완료
❌ 에러: ERROR | upbit.ComponentName | ❌ 작업 실패: 상세 메시지
⚠️  경고: WARNING | upbit.ComponentName | ⚠️ 주의사항
🔍 디버그: DEBUG | upbit.ComponentName | 상세 디버그 정보
```

### 3. 문제 발견 시 접근법
1. **에러 로그 추적**: 스택트레이스와 Component 식별
2. **계층별 분석**: 문제가 발생한 계층(UI/App/Domain/Infra) 확인
3. **점진적 수정**: 최소한의 변경으로 문제 해결
4. **즉시 검증**: 수정 후 바로 `python run_desktop_ui.py`로 확인

---

## 📊 실제 테스트 사례 (코인 리스트 위젯)

### 발견된 문제들과 해결 과정

#### 문제 1: UI 표시 이슈
```
DEBUG | upbit.CoinListWidget | 🔍 필터링 시작 - 전체 코인: 188개
INFO | upbit.CoinListWidget | ✅ UI 업데이트 완료: 188개 아이템
```
**결과**: 188개 로드되지만 UI에 모두 표시되지 않음
**해결**: 정렬/필터링 로직 개선

#### 문제 2: 다른 마켓 에러
```
ERROR | upbit.CoinListService | ❌ 현재가 데이터 조회 실패: Timeout context manager should be used inside a task
ERROR | upbit.CoinListService | ❌ BTC 마켓 코인 목록 조회 실패
```
**결과**: KRW는 정상, BTC/USDT 마켓에서 async 컨텍스트 문제
**해결**: ThreadPoolExecutor + 새로운 이벤트 루프 생성으로 격리

#### 문제 3: UI 요구사항 개선
- 초기화 버튼 텍스트: "초기화" → "X"
- 레이아웃: 검색을 마켓 콤보박스와 같은 줄로 이동
- 정렬: 라디오 버튼으로 이름순/변화율순/거래량순
- 스타일: 코인명 볼드, 변화율 색상

**검증 패턴**:
```
DEBUG | upbit.CoinListWidget | 정렬 모드: 변화율순
DEBUG | upbit.CoinListWidget | 🔍 최종 결과: 즐겨찾기 2개 + 일반 186개 = 총 188개 (정렬: change)
INFO | upbit.CoinListWidget | ✅ UI 업데이트 완료: 188개 아이템
```

---

## 🛠️ 핵심 테스트 도구

### 1. Live Testing Commands
```powershell
# 기본 실행
python run_desktop_ui.py

# 로깅 환경변수 설정
$env:UPBIT_CONSOLE_OUTPUT = "true"
$env:UPBIT_LOG_SCOPE = "verbose"
$env:UPBIT_COMPONENT_FOCUS = "CoinListWidget"
```

### 2. 계층 위반 검증
```powershell
# Domain Layer 순수성 검증
Get-ChildItem upbit_auto_trading/domain -Recurse -Include *.py | Select-String -Pattern "import sqlite3|import requests|from PyQt6"

# print() 사용 금지 검증
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String -Pattern "print\("
```

### 3. 빠른 DB 상태 확인
```powershell
python tools/super_db_table_viewer.py settings
python tools/super_db_table_viewer.py strategies
python tools/super_db_table_viewer.py market_data
```

---

## 🎯 테스트 체크리스트

### 기능 검증
- [ ] 전체 시스템 정상 구동 (`python run_desktop_ui.py`)
- [ ] 각 계층별 로그 정상 출력
- [ ] 에러 로그 없이 주요 기능 동작
- [ ] UI 응답성 및 사용자 경험 확인

### 아키텍처 검증
- [ ] DDD 계층 규칙 준수 (Domain 순수성)
- [ ] Infrastructure 로깅 사용 (print() 금지)
- [ ] 3-DB 분리 구조 유지
- [ ] Dry-run 기본값 확인

### 성능 검증
- [ ] 메모리 사용량 적정성
- [ ] API 호출 최적화
- [ ] UI 렌더링 속도
- [ ] 데이터 로딩 시간

---

## 🚀 효과적인 개발 워크플로우

### 1. 개발 사이클
```
수정 → Live Test → 로그 분석 → 문제 식별 → 점진적 개선 → 재검증
```

### 2. 실시간 피드백 활용
- **Component Logger**: 각 컴포넌트별 상세 로그
- **Debug 모드**: 개발 중 상세한 디버그 정보
- **Live UI Testing**: 코드 변경 즉시 실제 동작 확인

### 3. 문제 해결 우선순위
1. **Critical**: 시스템 크래시, 데이터 손실
2. **High**: 주요 기능 동작 불가
3. **Medium**: UI/UX 개선, 성능 최적화
4. **Low**: 스타일, 편의성 개선

---

## 📚 참고 자료

- **Architecture Guide**: `docs/ARCHITECTURE_GUIDE.md`
- **DDD Patterns**: `docs/DDD_아키텍처_패턴_가이드.md`
- **Logging Guide**: Infrastructure 로깅 시스템 활용법
- **Golden Rules**: `.github/copilot-instructions.md`

---

**핵심 교훈**: 복잡한 시스템일수록 **실제 동작 중심의 테스트**와 **체계적인 로깅 분석**이 개발 효율성을 극대화합니다.
