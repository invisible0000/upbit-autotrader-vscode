# 🎯 DB 마이그레이션 테이블 보존/삭제 결정 작업 지시서

## 📋 **작업 개요**
Super DB Table Reference Code Analyzer v5.0을 활용하여 DB 마이그레이션 시 삭제 예정 테이블 중에서 실제로는 보존해야 할 테이블들을 정확히 식별하고 분류하는 작업입니다.

## 🎯 **핵심 목표**
1. **삭제 대상 테이블의 코드 참조 분석**: 실제 비즈니스 로직에서 사용되는지 확인
2. **보존/삭제 결정 기준 수립**: 참조 유형과 중요도에 따른 분류
3. **안전한 마이그레이션 계획 수립**: 위험도 기반 단계적 접근

## 🛠️ **사용 가능한 도구**
- **Super DB Table Reference Code Analyzer v5.0** (`tools/super_db_table_reference_code_analyzer.py`)
  - 위치: `d:\projects\upbit-autotrader-vscode\tools\super_db_table_reference_code_analyzer.py`
  - 기능: 정확한 DB 테이블 참조 분석 (False Positive 제거)
  - 출력: 사람용 상세 보고서 + 머신용 JSON 데이터

## 📊 **분석 대상 정보**
- **데이터베이스**: `upbit_auto_trading/data/settings.sqlite3` (28개 테이블)
- **분석 범위**: Python 파일 273개 (tools, tests, __pycache__ 등 제외)
- **이전 세션 결과**: backup_info(10개 참조), execution_history(7개 참조) - 매우 낮은 위험도

## 🚀 **단계별 작업 계획**

### **Phase 1: 삭제 대상 테이블 식별 및 분석**
```powershell
# 1-1. 전체 테이블 분석으로 현황 파악
python tools\super_db_table_reference_code_analyzer.py --output-suffix "full_analysis"

# 1-2. 결과 검토하여 삭제 후보 테이블들 식별
# → db_table_reference_codes_full_analysis.log 파일 분석
```

### **Phase 2: 위험도별 테이블 분류**
```powershell
# 2-1. 참조 수가 적은 테이블들 (삭제 후보) 정밀 분석
python tools\super_db_table_reference_code_analyzer.py \
  --tables [삭제_후보_테이블들] \
  --output-suffix "deletion_candidates"

# 2-2. 참조 수가 많은 테이블들 (보존 필수) 분석
python tools\super_db_table_reference_code_analyzer.py \
  --tables [중요_테이블들] \
  --output-suffix "critical_tables"
```

### **Phase 3: 참조 유형별 보존/삭제 결정**

**🟢 안전한 삭제 조건**:
- 참조 수 < 5개
- 참조 유형이 주로 "문자열"(설정 파일)
- "함수/클래스" 참조가 없음
- "SQL컨텍스트" 참조가 없음

**🟡 주의 깊은 검토 필요**:
- 참조 수 5-20개
- "함수/클래스" 참조 1-2개
- 백업/로그 관련 테이블

**🔴 보존 필수**:
- 참조 수 > 20개
- "SQL컨텍스트" 참조 다수
- 핵심 비즈니스 로직에서 사용

### **Phase 4: 마이그레이션 계획 수립**

**단계적 삭제 계획**:
1. **1차**: 참조 없는 테이블 (100% 안전)
2. **2차**: 설정 파일에서만 참조되는 테이블
3. **3차**: 백업/로그 테이블 (기능 확인 후)
4. **최종**: 보존 결정된 테이블들은 스키마만 업데이트

## 💻 **실행 명령어 템플릿**

### **기본 분석**
```powershell
cd "d:\projects\upbit-autotrader-vscode"

# 전체 현황 파악
python tools\super_db_table_reference_code_analyzer.py --output-suffix "migration_analysis"

# 의심 테이블들 정밀 분석 (예시)
python tools\super_db_table_reference_code_analyzer.py \
  --tables backup_info execution_history chart_variables \
  --output-suffix "suspect_tables"

# 핵심 테이블 확인 (예시)
python tools\super_db_table_reference_code_analyzer.py \
  --tables strategies system_settings app_settings \
  --output-suffix "critical_check"
```

### **결과 해석 가이드**
- **참조 파일 분석**: `📄 경로 (참조수) - 유형 | 라인번호`
- **위험도 판단**: SQL컨텍스트 > 함수/클래스 > 문자열 순
- **비즈니스 로직**: `upbit_auto_trading/` 경로의 핵심 모듈들 우선 확인

## 📈 **예상 결과 및 활용**

**분류 예시**:
- **즉시 삭제 가능**: 참조 0개 또는 도구 파일에서만 참조
- **조건부 삭제**: 백업/로그 기능 확인 후 삭제
- **보존 필수**: 핵심 비즈니스 로직에서 활발히 사용

**활용 방안**:
1. **안전한 마이그레이션 순서 결정**
2. **테스트 우선순위 설정** (보존 테이블 집중)
3. **백업 전략 수립** (중요도별 차등 백업)

## ⚠️ **주의사항**
- 모든 분석 전에 데이터베이스 백업 필수
- False Positive가 제거되었지만 수동 검증 권장
- 테이블 삭제는 단계적으로 진행 (롤백 가능한 방식)

## 🎯 **성공 기준**
1. 삭제 대상 테이블의 정확한 위험도 분류 완료
2. 각 테이블별 보존/삭제 결정 근거 문서화
3. 단계적 마이그레이션 계획 수립 완료
4. 중요 테이블 보존으로 시스템 안정성 확보

---

**💡 팁**: 첫 번째로 전체 분석을 실행한 후, 참조 수가 적은 테이블들부터 상세 분석을 시작하세요. 이 도구의 정확성이 입증되었으므로 결과를 신뢰하고 활용할 수 있습니다.
