# 🚨 CRITICAL TASK: 시뮬레이션 아키텍처 마이그레이션 완료

## ⚠️ 위험도: HIGH - 매우 신중하게 작업 필요

### 📍 현재 상황 (2025-07-29)
- **폴더 구조 설계는 완료**되었으나 **실제 파일 이동/통합 작업은 미완료**
- **Junction 링크 제거** 작업 중 구조가 복잡해짐
- **GitHub 푸시 완료**된 상태이므로 롤백 시 주의 필요
- **다음 에이전트는 매우 보수적으로 접근** 필요

### 🎯 목표
Junction 링크 없이 GitHub Clone만으로 즉시 실행 가능한 구조 완성

### 📊 현재 아키텍처 상태

#### ✅ 완료된 작업
1. **shared_simulation/ 폴더 구조 생성 완료**
   - `upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/`
   - 하위 디렉토리: `engines/`, `data_sources/`, `charts/`

2. **핵심 파일들 생성 완료**
   - `simulation_engines.py` - 통합 시뮬레이션 엔진 (실제 샘플 DB 연동 완료)
   - `market_data_manager.py` - 데이터 로더
   - `simulation_panel.py` - UI 컴포넌트

3. **샘플 DB 연동 완료**
   - 실제 2,862개 비트코인 데이터 사용 확인
   - 가격대: 161백만원 (실제 데이터)

#### ❌ 미완료 작업 (위험 요소)
1. **기존 Junction 링크 파일들이 여전히 존재**
2. **중복된 코드 정리 필요**
3. **import 경로 통합 미완료**
4. **전체 시스템 검증 필요**

### 🔍 상황 파악 참고 문서

#### 필수 읽기 문서
1. `docs/CLEAR_PROJECT_STRUCTURE_GUIDE.md` - 새로운 구조 설명
2. `docs/DB_MIGRATION_USAGE_GUIDE.md` - DB 관련 정보
3. `docs/STRATEGY_ARCHITECTURE_OVERVIEW.md` - 전체 아키텍처
4. `logs/agent_log_2025-07.md` - 현재까지 작업 로그

#### 핵심 참고 파일
1. `test_new_structure.py` - 시스템 검증 스크립트
2. `verify_real_data.py` - 실제 데이터 사용 확인
3. `debug_sample_db.py` - DB 연결 확인

### 📋 다음 에이전트 작업 지침

#### 🛡️ 안전 수칙 (필수)
1. **백업 먼저**: 작업 전 반드시 `git commit` 으로 현재 상태 백업
2. **점진적 접근**: 한 번에 하나씩만 변경
3. **검증 우선**: 매 단계마다 `python test_new_structure.py` 실행
4. **롤백 준비**: 문제 발생 시 즉시 이전 커밋으로 복구

#### 📝 권장 작업 순서

##### Phase 1: 현재 상태 파악 (1시간)
```bash
# 1. 현재 상태 확인
python test_new_structure.py
python verify_real_data.py

# 2. Junction 링크 현황 파악
find . -type l  # Linux/WSL에서
dir /al        # Windows PowerShell에서

# 3. 중복 파일 확인
find . -name "simulation_engines.py" -type f
find . -name "market_data_manager.py" -type f
```

##### Phase 2: 안전한 정리 작업 (2-3시간)
1. **중복 파일 제거**
   - 기존 Junction 링크 파일들을 하나씩 확인 후 제거
   - 각 제거 후 테스트 실행

2. **import 경로 수정**
   - shared_simulation을 사용하도록 import 문 업데이트
   - 한 파일씩 수정 후 테스트

3. **데이터 검증**
   - 실제 샘플 DB 연동 유지 확인
   - 161백만원대 가격 데이터 로드 확인

##### Phase 3: 최종 검증 (1시간)
```bash
# 전체 시스템 테스트
python test_new_structure.py
python verify_real_data.py

# 새로운 환경에서 테스트
cd /tmp
git clone https://github.com/invisible0000/upbit-autotrader-vscode.git
cd upbit-autotrader-vscode
pip install -r requirements.txt
python quick_start.py
```

### 🚨 위험 신호 감지 시 조치
다음 증상 발견 시 **즉시 작업 중단**하고 이전 커밋으로 롤백:

1. `python test_new_structure.py` 실행 실패
2. 실제 샘플 DB 데이터 로드 실패 (5천만원대 가격으로 돌아감)
3. Import 오류 대량 발생
4. 기존 기능 동작 불가

### 📞 에이전트 간 인수인계 정보

#### 현재 DB 연동 상태
- ✅ 샘플 DB 경로: `upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/engines/data/sampled_market_data.sqlite3`
- ✅ 데이터 개수: 2,862개 레코드
- ✅ 가격대: 161백만원 (실제 비트코인 데이터)
- ✅ 최신 데이터: 2025-07-23

#### 핵심 아키텍처 파일
```
shared_simulation/
├── engines/
│   └── simulation_engines.py  ✅ 완성 (실제 DB 연동)
├── data_sources/
│   └── market_data_manager.py  ✅ 완성
└── charts/
    └── simulation_panel.py     ✅ 완성
```

#### Git 상태
- 마지막 커밋: "✅ 시뮬레이션 시스템 완성: 실제 샘플 DB 데이터 통합"
- 브랜치: master
- 푸시 완료: origin/master

### 🎯 성공 기준
1. `python test_new_structure.py` → 모든 시나리오 ✅
2. `python verify_real_data.py` → 161백만원대 가격 확인
3. GitHub Clone → requirements 설치 → 즉시 실행 가능
4. Junction 링크 완전 제거
5. 코드 중복 최소화

### � 세션 인수인계 - 모든 메모리 전달

#### � 실제 파일 이동 매핑 (핵심!)
```
📂 현재 Junction 링크 구조 → 새로운 shared_simulation/ 실제 파일 구조

1. 시뮬레이션 엔진 파일들:
   FROM: upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/engines/
   TO:   upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/engines/
   
   파일 목록:
   ✅ embedded_simulation_engine.py → simulation_engines.py (통합됨)
   ✅ real_data_simulation.py → simulation_engines.py (통합됨) 
   ✅ robust_simulation_engine.py → simulation_engines.py (통합됨)
   ✅ data/ 폴더 전체 → engines/data/ (샘플 DB 포함)

2. 데이터 소스 관리:
   FROM: trigger_builder/components/data_source_manager.py
   TO:   shared_simulation/data_sources/market_data_manager.py (이미 완료)
   
   FROM: trigger_builder/components/data_source_selector.py  
   TO:   shared_simulation/data_sources/data_source_selector.py

3. UI 컴포넌트들:
   FROM: trigger_builder/components/core/simulation_control_widget.py
   TO:   shared_simulation/charts/simulation_control_widget.py
   
   FROM: trigger_builder/components/core/simulation_result_widget.py
   TO:   shared_simulation/charts/simulation_result_widget.py
   
   FROM: trigger_builder_screen.py의 MiniChartWidget 클래스
   TO:   shared_simulation/charts/mini_chart_widget.py

4. 서비스 레이어:
   FROM: trigger_builder/components/shared/minichart_variable_service.py
   TO:   shared_simulation/data_sources/minichart_variable_service.py
   
   FROM: trigger_builder/components/shared/chart_visualizer.py
   TO:   shared_simulation/charts/chart_visualizer.py
```

#### 🚨 중복 파일 제거 목록 (매우 중요!)
```
❌ 제거할 중복 파일들:
1. trigger_builder/components/shared/simulation_engines.py 
   → shared_simulation/engines/simulation_engines.py 이미 존재
   
2. trigger_builder/engines/ 폴더 전체
   → shared_simulation/engines/로 이동 후 삭제

3. 기존 Junction 링크들:
   - 모든 심볼릭 링크 제거
   - 실제 파일만 유지
```

#### 📋 단계별 안전한 파일 이동 절차
```bash
# Phase 1: 백업 및 준비
git add -A && git commit -m "🔒 마이그레이션 전 백업"

# Phase 2: 실제 파일 복사 (하나씩!)
# 1. 시뮬레이션 엔진 통합 (이미 완료)
# shared_simulation/engines/simulation_engines.py 이미 존재 ✅

# 2. 데이터 소스 복사
cp "trigger_builder/components/data_source_selector.py" "shared_simulation/data_sources/"

# 3. UI 컴포넌트 복사  
cp "trigger_builder/components/core/simulation_control_widget.py" "shared_simulation/charts/"
cp "trigger_builder/components/core/simulation_result_widget.py" "shared_simulation/charts/"

# 4. 서비스 파일 이동
cp "trigger_builder/components/shared/minichart_variable_service.py" "shared_simulation/data_sources/"
cp "trigger_builder/components/shared/chart_visualizer.py" "shared_simulation/charts/"

# Phase 3: MiniChartWidget 클래스 추출
# trigger_builder_screen.py에서 MiniChartWidget 클래스를 
# shared_simulation/charts/mini_chart_widget.py로 추출

# Phase 4: 각 복사 후 테스트
python test_new_structure.py  # 매번 실행

# Phase 5: 성공 시 원본 삭제
rm "trigger_builder/components/shared/simulation_engines.py"
rm -rf "trigger_builder/engines/"
```

#### 🔧 Import 경로 수정 매핑표
```python
# 파일별 import 수정 필요 목록:

1. trigger_builder_screen.py:
   OLD: from .engines.embedded_simulation_engine import EmbeddedSimulationEngine
   NEW: from ..shared_simulation.engines.simulation_engines import get_embedded_engine

   OLD: from .engines.real_data_simulation import RealDataSimulation  
   NEW: from ..shared_simulation.engines.simulation_engines import get_realdata_engine

2. trigger_builder/components/core/ 파일들:
   OLD: from ..shared.simulation_engines import RobustSimulationEngine
   NEW: from ...shared_simulation.engines.simulation_engines import get_robust_engine

3. strategy_maker/ 파일들 (재사용 시):
   NEW: from ..shared_simulation.engines.simulation_engines import get_simulation_engine
   NEW: from ..shared_simulation.charts.simulation_panel import StrategySimulationPanel

4. 모든 data_source_manager 참조:
   OLD: from .data_source_manager import DataSourceManager
   NEW: from ..shared_simulation.data_sources.market_data_manager import MarketDataLoader
```

#### 📁 최종 목표 폴더 구조
```
shared_simulation/
├── engines/
│   ├── simulation_engines.py           ✅ 완료 (통합 엔진)
│   ├── data/
│   │   └── sampled_market_data.sqlite3 ✅ 완료 (실제 DB)
│   └── __init__.py
├── data_sources/
│   ├── market_data_manager.py          ✅ 완료 (데이터 로더)
│   ├── data_source_selector.py         🔄 이동 필요
│   ├── minichart_variable_service.py   🔄 이동 필요
│   └── __init__.py
├── charts/
│   ├── simulation_panel.py             ✅ 완료 (UI 컴포넌트)
│   ├── mini_chart_widget.py            🔄 추출 필요
│   ├── simulation_control_widget.py    🔄 이동 필요
│   ├── simulation_result_widget.py     🔄 이동 필요
│   ├── chart_visualizer.py             🔄 이동 필요
│   └── __init__.py
└── __init__.py
```

#### 🎯 Junction 링크 우회 전략
```
핵심 아이디어: 실제 파일 복사로 Junction 링크 완전 우회!

1. 기존 Junction 링크 → 실제 파일 복사
2. 모든 import 경로를 shared_simulation 기준으로 수정  
3. 중복 파일 제거
4. 원본 Junction 링크 폴더 삭제

결과: GitHub Clone 시 실제 파일들만 다운로드 → 즉시 실행 가능!
```

#### 🔥 세션 인수인계 - 모든 메모리 전달

#### �📂 실제 파일 이동 매핑 (핵심!)
```
현재 Junction 링크 파일들 → 새로운 shared_simulation/ 위치

1. 시뮬레이션 엔진 통합:
   기존: upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/engines/
   신규: upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/engines/
   
2. 데이터 소스 통합:
   기존: 여러 곳에 분산된 market_data_loader들
   신규: shared_simulation/data_sources/market_data_manager.py
   
3. 차트 컴포넌트 통합:
   기존: strategy_maker의 개별 차트들
   신규: shared_simulation/charts/simulation_panel.py
```

#### 🔍 Junction 링크 현황 파악 방법
```powershell
# Windows에서 Junction 링크 찾기
dir /al /s | findstr "<JUNCTION>"

# 심볼릭 링크도 확인
Get-ChildItem -Recurse | Where-Object {$_.LinkType -ne $null}

# 중복 파일 찾기
Get-ChildItem -Recurse -Name "simulation_engines.py"
Get-ChildItem -Recurse -Name "market_data_manager.py"
```

#### 🖥️ UI 동작 확인 절차
1. **StrategyMaker 실행**: `python run_desktop_ui.py`
2. **시뮬레이션 패널 확인**: strategy_management 화면에서 시뮬레이션 탭
3. **미니차트 표시 확인**: 실제 161백만원대 데이터가 차트에 표시되는지
4. **에러 로그 모니터링**: `logs/upbit_auto_trading.log` 실시간 확인

#### 📊 디버깅 로그 확인 방법
```bash
# 실시간 로그 모니터링
tail -f logs/upbit_auto_trading.log

# 에러만 필터링
grep "ERROR\|❌" logs/upbit_auto_trading.log

# 시뮬레이션 관련만 필터링
grep "simulation\|engine\|market_data" logs/upbit_auto_trading.log

# GUI 에러 로그
cat logs/gui_error.log
```

#### 🧪 필수 테스트 시퀀스
```bash
# 1. 기본 동작 확인
python test_new_structure.py

# 2. 실제 데이터 확인 (161백만원대여야 함)
python verify_real_data.py

# 3. DB 연결 확인
python debug_sample_db.py

# 4. GUI 실행 테스트
python run_desktop_ui.py
```

#### 🚨 위험 파일들 (절대 건드리지 말 것)
1. `upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/engines/data/sampled_market_data.sqlite3`
   - 실제 2,862개 비트코인 데이터 (161백만원대)
   - 이 파일 손상 시 모든 실제 데이터 손실

2. `run_desktop_ui.py`
   - 메인 GUI 엔트리포인트
   - 이 파일 수정 시 전체 UI 다운

#### 🔧 안전한 파일 이동 절차
```bash
# 1. 백업
git add -A && git commit -m "백업: 파일 이동 전"

# 2. 하나씩 이동 (예시)
cp source_file.py shared_simulation/target_location/
# 테스트 실행
python test_new_structure.py
# 성공 시에만 원본 삭제
rm source_file.py

# 3. import 경로 수정
# 예: from ..trigger_builder.engines import simulation_engines
# 을: from ..shared_simulation.engines import simulation_engines
```

#### 📝 Import 경로 매핑표
```python
# 기존 → 신규
from ..trigger_builder.engines.simulation_engines import *
→ from ..shared_simulation.engines.simulation_engines import *

from .components.mini_chart import MiniChartWidget  
→ from ..shared_simulation.charts.simulation_panel import StrategySimulationPanel

from ..data_sources.market_data_loader import MarketDataLoader
→ from ..shared_simulation.data_sources.market_data_manager import MarketDataLoader
```

#### 🎯 중요한 실제 동작 확인점
1. **StrategyMaker 시뮬레이션 탭**에서 차트가 161백만원대 데이터로 표시
2. **TriggerBuilder**에서 미니차트가 정상 동작
3. **백테스트 실행** 시 실제 샘플 데이터 사용
4. **에러 로그에 "No module named" 오류 없음**

#### 💾 현재 세션에서 확인된 핵심 정보
- **실제 샘플 DB 경로**: `trigger_builder/engines/data/sampled_market_data.sqlite3`
- **실제 데이터 확인**: 2025-07-23 최신 데이터, 161,127,000원 종가
- **성공적인 엔진**: RobustSimulationEngine이 실제 DB 데이터 로드 성공
- **테스트 스크립트**: `test_new_structure.py` → 모든 시나리오 ✅ 확인됨

#### 🚫 절대 하지 말 것
1. **일괄 삭제**: rm -rf로 폴더 통째로 삭제 금지
2. **DB 파일 이동**: 샘플 DB 위치 변경 시 경로 업데이트 필수
3. **메인 UI 파일 수정**: run_desktop_ui.py, strategy_maker 핵심 파일들
4. **Git Reset Hard**: 데이터 손실 위험

### �💡 중요 참고사항
- **사용자는 "폴더만 짜놓고 아무것도 옮기지 않았다"고 명시**
- **구조가 두 번 꼬였다고 경고**
- **매우 보수적이고 안정적으로 접근 필요**
- **실제 작업은 파일 이동/통합이 핵심**
- **161백만원대 실제 데이터 유지가 성공 기준**

---
**작성일**: 2025-07-29  
**작성자**: AI Agent Session (전체 메모리 전달)  
**우선순위**: CRITICAL  
**예상 소요시간**: 4-6시간  
**위험도**: HIGH
