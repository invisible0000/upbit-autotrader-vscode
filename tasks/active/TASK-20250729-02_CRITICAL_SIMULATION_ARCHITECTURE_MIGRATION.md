# 🚨 CRITICAL TASK: 시뮬레이션 아키텍처 마이그레이션 - 상세 실행 계획

## ⚠️ 위험도: HIGH - 매우 신중하게 작업 필요

### 📍 현재 상황 분석 (2025-07-29)
- **폴더 구조 설계는 완료**되었으나 **실제 파일 이동/통합 작업은 미완료**
- **Junction 링크 제거** 작업 중 구조가 복잡해짐
- **GitHub 푸시 완료**된 상태이므로 롤백 시 주의 필요
- **매우 보수적이고 체계적인 접근** 필요

### 🎯 목표
Junction 링크 없이 GitHub Clone만으로 즉시 실행 가능한 구조 완성

### 🔬 디버깅 로그 시스템 v2.3 활용 전략 (NEW)
이 Critical Task에서는 **디버깅 로그 v2.3의 조건부 컴파일** 기능을 적극 활용합니다:

```powershell
# 🔧 마이그레이션 작업용 환경 설정 (PowerShell)
$env:UPBIT_ENV = "development"        # 모든 로그 표시
$env:UPBIT_DEBUG_MODE = "true"        # 상세 디버그 정보 활성화
$env:UPBIT_BUILD_TYPE = "debug"       # 최대 상세도 로깅
```

**로깅 전략**:
- ✅ **각 Phase 시작 시**: `logger.info("🚀 Phase 1 시작 - 현재 상태 파악")`
- ⚡ **성능 모니터링**: `logger.performance("📊 파일 복사 시간: 0.5초")`
- 🔍 **상세 디버깅**: `logger.debug("🔍 파일 존재 확인: {file_path}")`
- ⚠️ **위험 신호**: `logger.warning("⚠️ Junction 링크 발견: {link_path}")`
- ❌ **Critical 오류**: `logger.error("❌ 실제 데이터 가격대 검증 실패")`
- ✅ **성공 완료**: `logger.success("✅ Phase 완료 - 모든 테스트 통과")`

---

## 📋 Phase 1: 현재 상태 완전 파악 (30-45분)

> **🔬 디버깅 로그 활용**: 각 단계마다 상세한 로그를 남겨 문제 발생 시 즉시 추적 가능하도록 합니다.

### 🔍 Step 1.1: 환경 준비 및 백업 (5분)
```powershell
# PowerShell 환경에서 실행 (copilot-instructions.md 준수)
□ 1.1.0 디버깅 환경 설정
$env:UPBIT_ENV = "development"
$env:UPBIT_DEBUG_MODE = "true"
echo "🔬 디버깅 로그 v2.3 활성화 완료"

□ 1.1.1 현재 상태 백업
git add -A; git commit -m "🔒 Phase 1 시작 전 백업 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

□ 1.1.2 작업 브랜치 생성 (선택사항)
git checkout -b simulation-migration-phase1

□ 1.1.3 현재 커밋 해시 기록
git log -1 --oneline > migration_backup_commit.txt
```

### 🔍 Step 1.2: 필수 파일 존재 확인 (10분)
```powershell
# PowerShell 명령어 사용 (Windows 환경 최적화)
□ 1.2.1 테스트 스크립트 존재 확인
Get-ChildItem test_new_structure.py, verify_real_data.py, debug_sample_db.py -ErrorAction SilentlyContinue

예상 결과: 모든 파일이 존재해야 함
실패 시: 즉시 작업 중단, 이전 에이전트 세션 참고

□ 1.2.2 shared_simulation 폴더 구조 확인  
Get-ChildItem "upbit_auto_trading\ui\desktop\screens\strategy_management\shared_simulation" -Recurse

예상 결과:
shared_simulation/
├── engines/
│   ├── simulation_engines.py
│   ├── data/
│   │   └── sampled_market_data.sqlite3
│   └── __init__.py
├── data_sources/
│   ├── market_data_manager.py
│   └── __init__.py
└── charts/
    ├── simulation_panel.py
    └── __init__.py

□ 1.2.3 핵심 샘플 DB 파일 확인
Get-ChildItem "upbit_auto_trading\ui\desktop\screens\strategy_management\trigger_builder\engines\data\sampled_market_data.sqlite3" -ErrorAction SilentlyContinue

예상 결과: 파일 크기 > 1MB, 수정일 2025-07-23 이후
실패 시: 🚨 CRITICAL - 즉시 작업 중단
```

### 🔍 Step 1.3: 실제 데이터 무결성 검증 (10분)
```powershell
□ 1.3.1 실제 데이터 가격대 확인
python verify_real_data.py

예상 결과: "161백만원대" 또는 "161,xxx,xxx원" 포함
🚨 위험 신호: "5천만원대" 또는 "50,xxx,xxx원" 표시

□ 1.3.2 데이터 레코드 수 확인
python debug_sample_db.py | Select-String "레코드|records"

예상 결과: "2,862개" 또는 유사한 개수
🚨 위험 신호: 100개 미만 또는 에러 발생

□ 1.3.3 기본 시스템 구조 테스트
python test_new_structure.py

예상 결과: "✅" 표시가 대부분이어야 함
🚨 위험 신호: "❌" 표시가 3개 이상

💡 디버깅 팁: 각 테스트 실행 시 logs/upbit_auto_trading.log 파일에서 실시간 로그 확인 가능
```

### 🔍 Step 1.4: Junction 링크 및 중복 파일 현황 파악 (10분)
```powershell
□ 1.4.1 Junction 링크 찾기 (Windows PowerShell)
Get-ChildItem -Recurse | Where-Object {$_.LinkType -eq "Junction"}

□ 1.4.2 심볼릭 링크 찾기 (Windows PowerShell)
Get-ChildItem -Recurse | Where-Object {$_.LinkType -ne $null}

□ 1.4.3 중복 파일 검색
Get-ChildItem -Recurse -Name "simulation_engines.py"
Get-ChildItem -Recurse -Name "market_data_manager.py"

□ 1.4.4 중복 현황 기록
# 발견된 모든 중복 파일 경로를 duplicate_files.txt에 기록
Get-ChildItem -Recurse -Name "*simulation*" > duplicate_files.txt

💡 디버깅 팁: PowerShell 명령어로 Windows 환경에 최적화된 검색 수행
```

---

## 📋 Phase 2: 안전한 파일 통합 (60-90분)

> **🔬 디버깅 전략**: 각 파일 이동 후 즉시 테스트하여 문제 발생 시 이전 단계로 롤백

### 🔄 Step 2.1: 데이터 소스 파일 통합 (20분)

#### 🎯 Step 2.1.1: data_source_selector.py 이동
```powershell
□ 2.1.1.1 원본 파일 존재 확인
Get-ChildItem "upbit_auto_trading\ui\desktop\screens\strategy_management\trigger_builder\components\data_source_selector.py" -ErrorAction SilentlyContinue

□ 2.1.1.2 대상 디렉토리 확인
Get-ChildItem "upbit_auto_trading\ui\desktop\screens\strategy_management\shared_simulation\data_sources\" -ErrorAction SilentlyContinue

□ 2.1.1.3 파일 복사 실행
Copy-Item "upbit_auto_trading\ui\desktop\screens\strategy_management\trigger_builder\components\data_source_selector.py" "upbit_auto_trading\ui\desktop\screens\strategy_management\shared_simulation\data_sources\"

□ 2.1.1.4 복사 성공 확인
Get-ChildItem "upbit_auto_trading\ui\desktop\screens\strategy_management\shared_simulation\data_sources\data_source_selector.py"

□ 2.1.1.5 즉시 테스트 실행
python test_new_structure.py

예상 결과: 이전과 동일하거나 더 나은 결과
🚨 실패 시: 복사한 파일 삭제 후 다음 파일로 진행

💡 디버깅 팁: 각 단계에서 logs/upbit_auto_trading.log 모니터링으로 실시간 상태 확인
```

#### 🎯 Step 2.1.2: minichart_variable_service.py 이동
```powershell
□ 2.1.2.1 원본 파일 존재 확인
Get-ChildItem "upbit_auto_trading\ui\desktop\screens\strategy_management\trigger_builder\components\shared\minichart_variable_service.py"

□ 2.1.2.2 파일 복사 실행
Copy-Item "upbit_auto_trading\ui\desktop\screens\strategy_management\trigger_builder\components\shared\minichart_variable_service.py" "upbit_auto_trading\ui\desktop\screens\strategy_management\shared_simulation\data_sources\"

□ 2.1.2.3 복사 성공 확인 및 테스트
Get-ChildItem "upbit_auto_trading\ui\desktop\screens\strategy_management\shared_simulation\data_sources\minichart_variable_service.py"
python test_new_structure.py

□ 2.1.2.4 중간 백업
git add -A; git commit -m "✅ 데이터 소스 파일 이동 완료"

💡 성능 모니터링: 각 복사 작업의 소요 시간이 logs에 기록됩니다
```

### 🔄 Step 2.2: UI 컴포넌트 파일 통합 (20분)

#### 🎯 Step 2.2.1: simulation_control_widget.py 이동
```bash
□ 2.2.1.1 원본 파일 확인
ls -la "upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/components/core/simulation_control_widget.py"

□ 2.2.1.2 파일 복사
cp "upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/components/core/simulation_control_widget.py" "upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/charts/"

□ 2.2.1.3 복사 확인 및 테스트
ls -la "upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/charts/simulation_control_widget.py"
python test_new_structure.py
```

#### 🎯 Step 2.2.2: simulation_result_widget.py 이동
```bash
□ 2.2.2.1 원본 파일 확인
ls -la "upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/components/core/simulation_result_widget.py"

□ 2.2.2.2 파일 복사
cp "upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/components/core/simulation_result_widget.py" "upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/charts/"

□ 2.2.2.3 복사 확인 및 테스트
python test_new_structure.py
```

#### 🎯 Step 2.2.3: chart_visualizer.py 이동
```bash
□ 2.2.3.1 원본 파일 확인
ls -la "upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/components/shared/chart_visualizer.py"

□ 2.2.3.2 파일 복사
cp "upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/components/shared/chart_visualizer.py" "upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/charts/"

□ 2.2.3.3 복사 확인 및 테스트
python test_new_structure.py

□ 2.2.3.4 중간 백업
git add -A && git commit -m "✅ UI 컴포넌트 파일 이동 완료"
```

### 🔄 Step 2.3: MiniChartWidget 클래스 추출 (30분)

#### 🎯 Step 2.3.1: 기존 클래스 위치 확인
```bash
□ 2.3.1.1 MiniChartWidget 클래스 검색
grep -n "class MiniChartWidget" upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/trigger_builder_screen.py

예상 결과: 라인 번호와 함께 클래스 정의 위치 표시
실패 시: 다른 파일에서 검색 필요
```

#### 🎯 Step 2.3.2: 새로운 파일 생성
```bash
□ 2.3.2.1 mini_chart_widget.py 파일 생성
# 이 단계는 코드 편집이 필요하므로 별도 도구 사용

□ 2.3.2.2 생성 확인
ls -la "upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/charts/mini_chart_widget.py"

□ 2.3.2.3 테스트 실행
python test_new_structure.py
```

---

## 📋 Phase 3: Import 경로 수정 (45-60분)

### 🔧 Step 3.1: trigger_builder_screen.py 수정 (20분)
```bash
□ 3.1.1 기존 import 문 확인
grep -n "from.*engines.*import" upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/trigger_builder_screen.py

□ 3.1.2 수정할 import 문 목록:
OLD: from .engines.embedded_simulation_engine import EmbeddedSimulationEngine
NEW: from ..shared_simulation.engines.simulation_engines import get_embedded_engine

OLD: from .engines.real_data_simulation import RealDataSimulation  
NEW: from ..shared_simulation.engines.simulation_engines import get_realdata_engine

□ 3.1.3 수정 후 테스트
python test_new_structure.py
```

### 🔧 Step 3.2: 기타 파일들의 import 경로 수정 (25분)
```bash
□ 3.2.1 모든 simulation_engines 참조 검색
grep -r "simulation_engines" upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/

□ 3.2.2 각 파일별 수정 및 테스트
# 발견된 각 파일에 대해:
# 1. 파일 수정
# 2. python test_new_structure.py 실행
# 3. 성공 시 다음 파일로 진행
```

---

## 📋 Phase 4: 중복 파일 안전 제거 (30-45분)

### 🗑️ Step 4.1: 중복 파일 확인 및 제거 (30분)
```bash
□ 4.1.1 제거 대상 확인
ls -la "upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/components/shared/simulation_engines.py"

□ 4.1.2 백업 생성
cp "upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/components/shared/simulation_engines.py" "simulation_engines_backup.py"

□ 4.1.3 제거 실행
rm "upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/components/shared/simulation_engines.py"

□ 4.1.4 즉시 테스트
python test_new_structure.py

🚨 실패 시: 백업에서 복원
cp "simulation_engines_backup.py" "upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/components/shared/simulation_engines.py"
```

### 🗑️ Step 4.2: Junction 링크 제거 (15분)
```bash
□ 4.2.1 Junction 링크 목록 재확인
dir /al /s | findstr "<JUNCTION>"

□ 4.2.2 하나씩 제거 및 테스트
# 각 Junction 링크에 대해:
# 1. rmdir /s "junction_link_path"
# 2. python test_new_structure.py
# 3. 실패 시 복원 또는 건너뛰기
```

---

## 📋 Phase 5: 최종 검증 (30분)

### ✅ Step 5.1: 전체 시스템 테스트 (15분)
```bash
□ 5.1.1 구조 테스트
python test_new_structure.py

예상 결과: 모든 항목이 ✅ 표시

□ 5.1.2 실제 데이터 테스트
python verify_real_data.py

예상 결과: 161백만원대 가격 확인

□ 5.1.3 DB 연결 테스트
python debug_sample_db.py

예상 결과: 2,862개 레코드 확인

□ 5.1.4 GUI 실행 테스트
python run_desktop_ui.py

예상 결과: 에러 없이 GUI 실행
```

### ✅ Step 5.2: GitHub Clone 테스트 (15분)
```bash
□ 5.2.1 임시 디렉토리에서 테스트
cd C:\temp
git clone https://github.com/invisible0000/upbit-autotrader-vscode.git test-migration
cd test-migration

□ 5.2.2 의존성 설치
pip install -r requirements.txt

□ 5.2.3 즉시 실행 테스트
python test_new_structure.py
python verify_real_data.py

예상 결과: 모든 테스트 통과
```

---

## 🚨 위험 신호 및 롤백 절차

### ⚠️ 위험 신호
1. `python test_new_structure.py` 실행 실패
2. 실제 샘플 DB 데이터 로드 실패 (5천만원대 가격으로 돌아감)
3. Import 오류 3개 이상 발생
4. GUI 실행 불가
5. **🆕 로그 레벨별 위험 신호**:
   - `❌ ERROR` 로그가 연속 3개 이상 발생
   - `⚠️ WARNING` 로그에서 "Junction", "Import", "DB" 키워드 반복 출현
   - `🔍 DEBUG` 로그에서 파일 경로 불일치 감지

### 🔄 롤백 절차
```powershell
# 즉시 롤백 (PowerShell 구문)
git reset --hard HEAD~1

# 또는 특정 커밋으로 롤백
git reset --hard [백업_커밋_해시]

# 강제 정리
git clean -fd

# 디버깅 환경 초기화
$env:UPBIT_ENV = "development"
$env:UPBIT_DEBUG_MODE = "true"

# 안전 확인
python test_new_structure.py

💡 로그 분석: logs/upbit_auto_trading.log에서 롤백 이전 마지막 에러 원인 분석 가능
```

---

## 📊 성공 기준

### ✅ 필수 통과 기준
1. **python test_new_structure.py** → 모든 시나리오 ✅
2. **python verify_real_data.py** → 161백만원대 가격 확인
3. **GitHub Clone 후 즉시 실행** → 에러 없음
4. **Junction 링크 완전 제거** → dir /al 결과 없음
5. **GUI 정상 실행** → run_desktop_ui.py 성공

### 📈 부가 성공 기준
1. 코드 중복 최소화
2. Import 경로 일관성
3. 로그 에러 제거
4. 성능 저하 없음

---

## 📞 에이전트 인수인계 체크리스트

### ✅ 완료 시 확인사항
- [ ] 모든 Phase 완료
- [ ] 최종 테스트 통과
- [ ] Git 커밋 완료
- [ ] 문서 업데이트 완료
- [ ] **🆕 디버깅 로그 분석**: logs/upbit_auto_trading.log에서 에러 없음 확인

### 📝 다음 에이전트 전달사항
- **실제 데이터 상태**: 161백만원대 유지 여부
- **마지막 성공 커밋**: git log -1 --oneline
- **남은 작업**: strategy_maker 연동
- **발견된 이슈**: 상세 기록
- **🆕 로그 분석 결과**: 
  - 성공 로그 수: `✅ SUCCESS` 로그 개수
  - 경고 로그 수: `⚠️ WARNING` 로그 개수  
  - 에러 로그 수: `❌ ERROR` 로그 개수
  - 성능 데이터: `⚡ PERFORMANCE` 로그에서 병목 지점 파악

### 🔬 디버깅 로그 활용 성과 (작업 완료 후 기록)
```powershell
# 로그 통계 확인
Get-Content "logs\upbit_auto_trading.log" | Select-String "✅|❌|⚠️|⚡" | Measure-Object

# 주요 에러 패턴 분석
Get-Content "logs\upbit_auto_trading.log" | Select-String "❌|ERROR" | Select-Object -Last 10
```

---

**작성일**: 2025-07-29  
**버전**: v2.1 (디버깅 로그 v2.3 통합)  
**예상 소요시간**: 3-4시간  
**위험도**: HIGH → MEDIUM (체계적 접근 + 실시간 로그 모니터링으로 리스크 감소)
