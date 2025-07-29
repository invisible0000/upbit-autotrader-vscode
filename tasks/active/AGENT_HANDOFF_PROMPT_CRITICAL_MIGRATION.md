# 🚨 에이전트 인수인계 프롬프트: Critical 시뮬레이션 아키텍처 마이그레이션

## 🎯 미션 개요
**Junction 링크 없이 GitHub Clone만으로 즉시 실행 가능한 구조**를 완성하는 Critical Task를 수행하세요.

---

## 📋 필수 사전 준비사항

### 🔧 1단계: 환경 설정 (반드시 첫 번째로 실행)
```powershell
# 디버깅 로그 v2.3 활성화 (Critical Task 전용 설정)
$env:UPBIT_ENV = "development"
$env:UPBIT_DEBUG_MODE = "true"
$env:UPBIT_BUILD_TYPE = "debug"
echo "🔬 디버깅 로그 v2.3 활성화 완료"

# 콘솔 한글 인코딩 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
echo "🇰🇷 한글 인코딩 설정 완료"
```

### 📊 2단계: 현재 상태 체크 (필수 검증)
```powershell
# 핵심 테스트 스크립트 존재 확인
Get-ChildItem test_new_structure.py, verify_real_data.py, debug_sample_db.py -ErrorAction SilentlyContinue

# 실제 데이터 상태 확인 (가장 중요!)
python verify_real_data.py
# ✅ 예상: "161백만원대" 표시
# 🚨 위험: "5천만원대" 표시 시 즉시 작업 중단

# 전체 시스템 상태 확인
python test_new_structure.py
# ✅ 목표: ✅ 표시가 대부분
# 🚨 경고: ❌ 표시가 3개 이상 시 신중 접근
```

---

## 🛡️ 안전 운영 원칙

### ⚠️ 절대 규칙 (위반 시 즉시 중단)
1. **161백만원대 데이터 보호**: 어떤 상황에서도 실제 데이터가 5천만원대로 돌아가면 안 됨
2. **단계별 검증**: 각 파일 이동 후 반드시 `python test_new_structure.py` 실행
3. **즉시 백업**: 문제 발생 시 `git reset --hard HEAD~1`로 이전 상태 복구
4. **PowerShell 전용**: 모든 명령어는 PowerShell 구문 사용 (bash 금지)
5. **로그 모니터링**: `logs/upbit_auto_trading.log` 실시간 추적

### 🔄 작업 리듬 (반복 패턴)
```
1. 파일 복사/이동 → 2. 즉시 테스트 → 3. 로그 확인 → 4. 문제 시 롤백 → 5. 성공 시 다음 단계
```

---

## 📋 Phase별 실행 가이드

### 🔍 Phase 1: 현재 상태 완전 파악 (30분)
**목표**: 문제없이 작업할 수 있는 환경인지 확인

```powershell
# Step 1.1: 백업 생성
git add -A; git commit -m "🔒 Critical Task 시작 전 백업 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# Step 1.2: 핵심 파일 구조 확인
Get-ChildItem "upbit_auto_trading\ui\desktop\screens\strategy_management\shared_simulation" -Recurse

# Step 1.3: Junction 링크 현황 파악
Get-ChildItem -Recurse | Where-Object {$_.LinkType -ne $null}

# Step 1.4: 중복 파일 목록 생성
Get-ChildItem -Recurse -Name "*simulation*" > duplicate_files.txt
```

### 🔄 Phase 2: 안전한 파일 통합 (60분)
**목표**: 파일들을 shared_simulation으로 이동하되 안전 확보

```powershell
# 🎯 핵심 전략: 복사 → 테스트 → 성공 시 원본 제거

# Step 2.1: data_source_selector.py 이동
Copy-Item "upbit_auto_trading\ui\desktop\screens\strategy_management\trigger_builder\components\data_source_selector.py" "upbit_auto_trading\ui\desktop\screens\strategy_management\shared_simulation\data_sources\"
python test_new_structure.py
# ✅ 성공 시 다음 단계, ❌ 실패 시 복사 파일 삭제

# Step 2.2: minichart_variable_service.py 이동
Copy-Item "upbit_auto_trading\ui\desktop\screens\strategy_management\trigger_builder\components\shared\minichart_variable_service.py" "upbit_auto_trading\ui\desktop\screens\strategy_management\shared_simulation\data_sources\"
python test_new_structure.py

# 중간 백업
git add -A; git commit -m "✅ 데이터 소스 파일 이동 완료"
```

### 🔧 Phase 3: Import 경로 수정 (45분)
**목표**: 이동된 파일들에 맞게 import 경로 업데이트

```powershell
# PowerShell에서 grep 대신 Select-String 사용
Get-Content "upbit_auto_trading\ui\desktop\screens\strategy_management\trigger_builder\trigger_builder_screen.py" | Select-String "from.*engines.*import"

# 각 import 수정 후 즉시 테스트
python test_new_structure.py
```

### 🗑️ Phase 4: 중복 파일 제거 (30분)
**목표**: 안전하게 중복 파일들 정리

```powershell
# 백업 생성 후 제거
Copy-Item "원본파일경로" "백업파일명"
Remove-Item "원본파일경로"
python test_new_structure.py
# 실패 시 백업에서 즉시 복원
```

### ✅ Phase 5: 최종 검증 (30분)
**목표**: 모든 시스템이 정상 작동함을 확인

```powershell
# 전체 테스트 실행
python test_new_structure.py
python verify_real_data.py
python debug_sample_db.py
python run_desktop_ui.py

# GitHub Clone 테스트 (별도 디렉토리)
cd C:\temp
git clone https://github.com/invisible0000/upbit-autotrader-vscode.git test-migration
cd test-migration
python test_new_structure.py
```

---

## 🚨 긴급 상황 대응

### ❌ 위험 신호 감지 시
```powershell
# 즉시 롤백
git reset --hard HEAD~1
git clean -fd

# 환경 재설정
$env:UPBIT_ENV = "development"
$env:UPBIT_DEBUG_MODE = "true"

# 상태 재확인
python test_new_structure.py
python verify_real_data.py
```

### 🔍 로그 분석 (문제 발생 시)
```powershell
# 최근 에러 확인
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Get-Content "logs\upbit_auto_trading.log" -Encoding UTF8 | Select-String "ERROR|CRITICAL" | Select-Object -Last 10

# 특정 컴포넌트 문제 추적
Get-Content "logs\upbit_auto_trading.log" -Encoding UTF8 | Select-String "SimulationEngine|DatabaseManager" | Select-String "ERROR"
```

---

## 🎯 성공 기준

### ✅ 필수 통과 조건
1. `python test_new_structure.py` → 모든 항목 ✅
2. `python verify_real_data.py` → "161백만원대" 확인
3. `python run_desktop_ui.py` → 에러 없이 GUI 실행
4. Junction 링크 완전 제거
5. GitHub Clone 후 즉시 실행 가능

### 📊 품질 지표
- 로그에서 ERROR 0개
- WARNING 최소화
- 모든 import 경로 정상
- 성능 저하 없음

---

## 💡 중요한 팁

### 🔧 PowerShell 명령어 치트시트
```powershell
# 파일 복사: Copy-Item "source" "destination"
# 파일 삭제: Remove-Item "path"
# 디렉토리 확인: Get-ChildItem "path" -Recurse
# 텍스트 검색: Get-Content "file" | Select-String "pattern"
# 링크 찾기: Get-ChildItem -Recurse | Where-Object {$_.LinkType -ne $null}
```

### 🔍 디버깅 로그 v2.3 활용
- **실시간 모니터링**: `logs/upbit_auto_trading.log` 파일 지속 확인
- **성능 추적**: PERFORMANCE 키워드로 병목 지점 파악
- **에러 패턴**: ERROR, WARNING 키워드로 문제 조기 발견

### 🎯 작업 우선순위
1. **안전성**: 데이터 보호가 최우선
2. **검증**: 각 단계마다 테스트 실행
3. **로깅**: 모든 작업 과정 기록
4. **회복성**: 문제 시 즉시 롤백

---

## 📞 완료 보고 양식

작업 완료 시 다음 정보를 정리해주세요:

```
✅ 완료 상태:
- Phase 1~5 모두 완료: [ ]
- 161백만원대 데이터 유지: [ ]
- GUI 정상 실행: [ ]
- Junction 링크 제거: [ ]

📊 로그 분석 결과:
- SUCCESS 로그 수: ___개
- WARNING 로그 수: ___개  
- ERROR 로그 수: ___개
- 주요 성능 병목: _______

🔄 마지막 커밋: git log -1 --oneline
```

---

**🚀 이 프롬프트를 따라 차근차근 진행하면 안전하고 완벽한 Critical Task 완수가 가능합니다!**

**⚠️ 기억하세요**: 천천히 가는 것이 빠르게 가는 방법입니다. 각 단계마다 충분히 검증하고 넘어가세요!
