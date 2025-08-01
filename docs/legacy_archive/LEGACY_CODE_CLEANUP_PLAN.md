# 레거시 코드 정리 및 제거 작업 리스트

## 🎯 목표
현재 시스템에서 사용하지 않는 레거시 코드들을 식별하고 제거하여 코드베이스를 깔끔하게 정리합니다.

---

## 🔍 제거 대상 파일 목록

### 📁 **중복 파일들**

#### **1. 백업/임시 파일들**
```bash
# 제거 대상
upbit_auto_trading/ui/desktop/strategy_management_screen_bck.py  # 백업 파일
upbit_auto_trading/ui/desktop/strategy_management_screen.py      # 루트 레벨 중복 파일
```

**제거 이유**: 
- `screens/strategy_management/strategy_management_screen.py`가 정식 버전
- 백업 파일과 중복 파일은 혼란만 가중

#### **2. 테스트 파일들 (과도한 중복)**
```bash
# 검토 후 정리 필요
test_*.py (138개 파일 중 실제 사용되는 것만 유지)
test_api_key.py
test_backtest_result_display.py
test_chart_view_new.py
test_chart_view.py
test_combinations.json
test_comprehensive_backtest.py
test_data_collection.py
test_full_integration.py
test_indicator_fix_v2.py
test_indicator_fix.py
test_indicator_integration.py
test_infinite_scroll_improved.py
test_infinite_scroll.py
test_real_data_collection.py
test_simple_api.py
test_simple_chart.py
test_step_by_step.py
test_strategy_backtest.py
test_strategy_management.py
test_strategy_ui.py
test_ui_fixes.py
test_updated_strategy_ui.py
test_websocket_chart.py
```

**정리 기준**:
- 현재 개발 중인 기능과 무관한 테스트
- 중복되거나 오래된 테스트 코드
- 단발성 실험 코드

### 📁 **사용하지 않는 기능 모듈들**

#### **3. 차트 관련 테스트 코드**
```bash
# 제거 대상 (차트 기능 미사용)
test_chart_view_new.py
test_chart_view.py  
test_simple_chart.py
test_websocket_chart.py
websocket_chart_test.log
```

#### **4. 무한 스크롤 관련 코드**
```bash
# 제거 대상 (GUI에서 미사용)
test_infinite_scroll_improved.py
test_infinite_scroll.py
infinite_scroll_test.log
```

#### **5. 지표 수정 관련 임시 코드**
```bash
# 제거 대상 (임시 실험 코드)
test_indicator_fix_v2.py
test_indicator_fix.py
test_indicator_integration.py
```

---

## 🗂️ 정리 작업 계획

### 🚀 **Phase 1: 즉시 제거 (안전한 파일들)**

#### **Step 1-1: 백업 파일 제거**
```bash
# 제거할 파일들
rm upbit_auto_trading/ui/desktop/strategy_management_screen_bck.py
rm upbit_auto_trading/ui/desktop/strategy_management_screen.py  # 루트 레벨
```

#### **Step 1-2: 테스트 로그 파일 제거**
```bash
# 로그 파일들 제거
rm infinite_scroll_test.log
rm websocket_chart_test.log
rm test_results_summary.md  # 오래된 결과 파일
```

#### **Step 1-3: 차트 관련 테스트 제거**
```bash
# 차트 기능 미사용으로 제거
rm test_chart_view_new.py
rm test_chart_view.py
rm test_simple_chart.py
rm test_websocket_chart.py
```

### 🔍 **Phase 2: 검토 후 제거 (신중한 검토 필요)**

#### **Step 2-1: 지표 관련 테스트 코드 검토**
- [ ] `test_indicator_fix_v2.py` - 내용 확인 후 필요 시 통합
- [ ] `test_indicator_fix.py` - 내용 확인 후 필요 시 통합  
- [ ] `test_indicator_integration.py` - 현재 지표 시스템과 비교

#### **Step 2-2: 백테스트 관련 테스트 정리**
```bash
# 검토 대상 (중복 가능성)
test_backtest_result_display.py    # 현재 백테스트 시스템과 비교
test_comprehensive_backtest.py     # 통합 백테스트와 중복 여부 확인
test_strategy_backtest.py          # 전략 백테스트와 중복 여부 확인
```

#### **Step 2-3: UI 관련 테스트 정리**
```bash
# 검토 대상
test_strategy_management.py        # 현재 전략 관리 화면과 비교
test_strategy_ui.py                # 현재 UI 구현과 비교
test_ui_fixes.py                   # 수정 사항이 현재 코드에 반영되었는지 확인
test_updated_strategy_ui.py        # 최신 UI와 중복 여부 확인
```

### 🧪 **Phase 3: 테스트 시스템 재구성**

#### **Step 3-1: 핵심 테스트만 유지**
**유지할 테스트 카테고리**:
- 단위 테스트 (Unit Tests): `upbit_auto_trading/tests/unit/`
- 통합 테스트 (Integration Tests): 핵심 기능만
- 전략 테스트: 개별 전략 검증용

**제거할 테스트 카테고리**:
- 실험성 테스트
- 중복 테스트
- 더 이상 관련 없는 기능 테스트

#### **Step 3-2: 새로운 테스트 구조 구축**
```
tests/
├── unit/                    # 단위 테스트 (유지)
│   ├── strategies/         # 전략 단위 테스트
│   ├── database/          # DB 관련 테스트
│   └── api/               # API 관련 테스트
├── integration/           # 통합 테스트 (재구성)
│   ├── strategy_combination/  # 전략 조합 테스트
│   └── backtest/         # 백테스트 통합 테스트
└── e2e/                   # E2E 테스트 (새로 구성)
    └── gui/               # GUI 통합 테스트
```

---

## 📋 제거 전 백업 체크리스트

### ✅ **안전성 확인**
- [ ] Git 커밋 상태 확인 (모든 중요 변경사항 커밋됨)
- [ ] 현재 브랜치에서 백업 브랜치 생성
- [ ] 중요 설정/데이터 파일 별도 백업

### ✅ **의존성 확인**  
- [ ] 제거할 파일이 다른 모듈에서 import되지 않는지 확인
- [ ] 테스트 실행에 필수적인 파일인지 확인
- [ ] CI/CD 파이프라인에 영향 없는지 확인

---

## 🔧 실행 스크립트

### **즉시 제거 스크립트**
```bash
#!/bin/bash
# cleanup_phase1.sh - 안전한 파일들 즉시 제거

echo "=== Phase 1: 안전한 파일 제거 시작 ==="

# 백업 파일 제거
echo "백업 파일 제거 중..."
rm -f upbit_auto_trading/ui/desktop/strategy_management_screen_bck.py
rm -f upbit_auto_trading/ui/desktop/strategy_management_screen.py

# 로그 파일 제거  
echo "로그 파일 제거 중..."
rm -f infinite_scroll_test.log
rm -f websocket_chart_test.log

# 차트 관련 테스트 제거
echo "차트 관련 테스트 제거 중..."
rm -f test_chart_view_new.py
rm -f test_chart_view.py
rm -f test_simple_chart.py
rm -f test_websocket_chart.py

# 무한 스크롤 관련 제거
echo "무한 스크롤 관련 파일 제거 중..."
rm -f test_infinite_scroll_improved.py
rm -f test_infinite_scroll.py

echo "=== Phase 1 완료 ==="
echo "제거된 파일들:"
echo "- 백업 파일 2개"
echo "- 로그 파일 2개" 
echo "- 차트 테스트 4개"
echo "- 무한 스크롤 테스트 2개"
echo "총 10개 파일 제거됨"
```

### **검토용 스크립트**
```bash
#!/bin/bash
# analyze_test_files.sh - 테스트 파일 의존성 분석

echo "=== 테스트 파일 의존성 분석 ==="

# import 관계 확인
echo "1. Import 관계 분석 중..."
grep -r "import.*test_" upbit_auto_trading/ || echo "테스트 파일 import 없음"

# 실행 중인 테스트 확인  
echo "2. pytest 설정 확인 중..."
if [ -f pytest.ini ]; then
    echo "pytest.ini 발견:"
    cat pytest.ini
fi

# 파일 크기 및 수정 날짜 확인
echo "3. 테스트 파일 정보:"
ls -la test_*.py | head -10

echo "=== 분석 완료 ==="
```

---

## 📊 정리 효과 예상

### **Before (현재)**
```
전체 파일 수: ~200개
테스트 파일: 138개  
중복/레거시: ~30개
코드 복잡도: 높음
```

### **After (정리 후)**
```
전체 파일 수: ~170개 (-30개)
테스트 파일: ~50개 (-88개)
중복/레거시: 0개 (-30개)  
코드 복잡도: 중간
```

### **예상 이익**
- 🚀 **빌드 시간 단축**: 30% 감소
- 🧹 **코드 탐색 용이성**: 불필요한 파일 제거
- 🎯 **집중도 향상**: 현재 사용 중인 코드만 유지
- 🔧 **유지보수성**: 관리할 파일 수 감소

---

> **⚠️ 주의사항**: 파일 제거 전 반드시 Git 커밋을 통해 현재 상태를 백업하고, 중요한 로직이 포함된 파일은 내용을 검토 후 제거하세요.
