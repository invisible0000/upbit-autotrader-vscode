# 🧪 컴포넌트 선택기 테스트 예제

## 📋 **테스트 목적**
로깅 설정의 `component_focus`를 위한 트리 구조 선택기 UI 방식 비교 테스트

## 🎯 **테스트 대상**
1. **Option A**: QComboBox + QTreeWidget (🔥 혁신적)
2. **Option B**: 별도 다이얼로그 + QTreeWidget (🛡️ 안전한 방법)

## 🚀 **실행 방법**
```powershell
# 메인 테스트 런처 (권장)
cd examples/component_selector_test
python main.py

# 개별 테스트
python option_a_tree_combo.py  # Option A만 테스트
python option_b_dialog.py      # Option B만 테스트
```

## 📂 **파일 구조**
- `main.py`: 🧪 메인 테스트 런처
- `option_a_tree_combo.py`: 🔥 QComboBox + QTreeWidget 방식
- `option_b_dialog.py`: 🛡️ 다이얼로그 기반 방식
- `component_data.py`: 📊 DDD 컴포넌트 테스트 데이터

## 🔥 **Option A 특징 (혁신적)**
- 일반 콤보박스처럼 보이지만 드롭다운이 트리 구조
- 공간 효율적, UI 통합도 높음
- `combo.setView(tree_widget)` 기법 활용
- 혁신적이고 사용자 친화적

## 🛡️ **Option B 특징 (안전한 방법)**
- 버튼 클릭시 전용 다이얼로그 팝업
- 검색 기능, 상세 정보 제공
- 더블클릭 선택, 카테고리/컴포넌트 구분
- 안전하고 기능이 풍부함

## ✅ **성공 기준**
- ✅ 클릭만으로 컴포넌트 선택 가능
- ✅ 계층 구조 표시 명확 (DDD 4계층)
- ✅ 선택된 컴포넌트 텍스트 정확히 표시
- ✅ 사용자 경험 직관적
- ✅ logging_config.yaml 설정값 표시

## 🎯 **적용 대상**
`upbit_auto_trading/ui/desktop/settings/logging_settings_widget.py`의 component_focus 콤보박스 개선
