# 🎨 UI 개발 및 테마 시스템 통합 가이드

> **목적**: PyQt6 기반 UI 개발, 테마 시스템, 사용자 경험 최적화 통합 안내
> **범위**: UI 디자인 시스템, 스타일 가이드, 트리거 빌더, 변수 호환성
> **갱신**: 2025-08-06

---

## 🎨 UI 디자인 시스템 (UI_DESIGN_SYSTEM)

### 핵심 디자인 철학
- **목표**: 초보자도 80% 기능을 무도움으로 사용할 수 있는 직관적 인터페이스
- **반응성**: 사용자 입력 0.5초 내 반응
- **접근성**: 최소 1280x720 해상도 지원
- **일관성**: 전체 애플리케이션 통일된 스타일
- **7규칙 중심**: 기본 7규칙 전략 워크플로 최적화

### 레이아웃 시스템
- **메인 윈도우**: 권장 1600x1000, 최소 1200x800
- **트리거 빌더**: 3분할 구조 (조건 빌더 2:5, 트리거 관리 3:5, 시뮬레이션 2:5)
- **DDD UI 구조**: presenters (MVP 패턴), views (Passive View), components (재사용)

### 색상 시스템
- **주요 색상**: PRIMARY #1E88E5 (파란색), SUCCESS #4CAF50 (녹색), DANGER #F44336 (빨간색)
- **의미 색상**: WARNING #FF9800 (주황색), INFO #2196F3 (하늘색)
- **중성 색상**: BACKGROUND #FAFAFA, SURFACE #FFFFFF, BORDER #E0E0E0
- **다크 테마**: 자동 변환 지원, ThemeManager로 동적 적용

### 상호작용 패턴
- **드래그앤드롭**: 왼쪽 팔레트 → 중앙 캔버스 → 조건 생성 → 호환성 검증
- **실시간 검증**: 변수 선택 시 즉시 호환성 확인, 비호환 시 경고 표시
- **파라미터 설정**: 팝업 다이얼로그, 슬라이더/드롭다운/입력 필드

### 차트 시스템
- **matplotlib 테마**: 다크/라이트 자동 적용, apply_chart_theme() 호출
- **차트 색상**: 상승 캔들 #4CAF50, 하락 캔들 #F44336, 거래량 #2196F3, 이평선 #FF9800/#9C27B0
- **성능 지표**: 카드 형태 표시 (총 수익률, 최대 손실, 승률, 샤프 비율)

### 7규칙 전략 전용 UI
- **조건 카드**: 📈 RSI 과매도 진입, RSI(14) < 30, 🎯 ENTRY 태그, [편집][삭제][복사] 버튼
- **파라미터 팝업**: 기간 슬라이더, 데이터 소스 드롭다운, [취소][적용] 버튼

### 성능 최적화
- **UI 렌더링**: 지연 로딩, 가상 스크롤, 차트 데이터 캐싱
- **메모리 관리**: WeakRef 사용, 이벤트 해제, 정기 정리

### 접근성 고려사항
- **키보드 네비게이션**: Tab 순서, 단축키, Enter/Space 버튼 활성화
- **시각적 접근성**: 고대비, 색맹 고려, 150% 확대 지원

---

## 🎨 스타일 가이드 (STYLE_GUIDE)

### UI/UX 테마 시스템 (필수 준수)

#### ✅ 반드시 지켜야 할 규칙
- **QSS 테마 시스템 활용**: widget.setObjectName("특정_위젯명") 설정 후 QSS 파일에서 스타일 정의
- **matplotlib 차트 테마**: apply_matplotlib_theme_simple() 차트 그리기 전 반드시 호출
- **테마 알림 시스템**: get_theme_notifier(), theme_changed.connect() 사용
- **동적 색상**: is_dark_theme()으로 분기, 테마별 line_color/bg_color 설정

#### ❌ 절대 하지 말아야 할 것들
- **하드코딩된 스타일**: setStyleSheet("background-color: white;") 금지
- **하드코딩된 차트 색상**: ax.plot(data, color='blue') 테마 무시 금지
- **지원하지 않는 CSS**: cursor: not-allowed 등 Qt 미지원 속성 금지

### PyQt6 스타일링 규칙
- **QSS 파일 위치**: upbit_auto_trading/ui/desktop/common/styles/
- **파일 구성**: default_style.qss (라이트), dark_style.qss (다크)
- **objectName 활용**: 특정 위젯 스타일링을 위한 선택자 기반

### 권장 objectName
- **차트 위젯**: chart_widget, chart_canvas
- **다이얼로그 라벨**: helpDialogLabel, infoDialogLabel
- **상태 라벨**: statusLabel, simulationStatus
- **제목 라벨**: titleLabel
- **구분선**: separator

### Matplotlib 차트 스타일링 (필수 패턴)
```python
# 1️⃣ 테마 적용 (필수)
from upbit_auto_trading.ui.desktop.common.theme_notifier import apply_matplotlib_theme_simple
apply_matplotlib_theme_simple()

# 2️⃣ 테마별 색상 설정
theme_notifier = get_theme_notifier()
is_dark = theme_notifier.is_dark_theme()

# 3️⃣ 동적 색상 정의
line_color = '#60a5fa' if is_dark else '#3498db'
bg_color = '#2c2c2c' if is_dark else 'white'

# 4️⃣ Figure/Canvas 배경 설정
self.figure.patch.set_facecolor(bg_color)
self.canvas.setStyleSheet(f"background-color: {bg_color};")
```

### 테마 변경 대응
```python
def _on_theme_changed(self, is_dark: bool):
    """테마 변경 시 차트 업데이트"""
    if hasattr(self, 'figure') and CHART_AVAILABLE:
        if self._last_data:
            self.update_chart(self._last_data)
        else:
            self.show_placeholder_chart()
```

### 코드 작성 규칙
- **테마 관련 import**: 표준 import 패턴 준수
- **에러 처리**: 테마 적용 실패 시 graceful fallback
- **로깅 메시지**: 일관된 형식 (🎨 다크 테마 적용, 🔍 StyleManager 테마)

### 체크리스트
- **새 UI 컴포넌트**: QSS 테마 시스템 활용, 하드코딩 색상 없음, objectName 설정
- **차트 개발**: apply_matplotlib_theme_simple() 호출, 동적 색상 사용, 테마 변경 이벤트 처리
- **코드 리뷰**: 테마 독립적 코드, Qt 지원 CSS 속성, 접근성 확인

---

## 🎯 트리거 빌더 시스템 (TRIGGER_BUILDER_GUIDE)

### 시스템 개요
- **목적**: 조건부 매매 신호 생성을 위한 핵심 시스템
- **방식**: 드래그앤드롭으로 조건 조합하여 매매 전략 구축
- **검증**: 3중 카테고리 호환성 시스템 기반 실시간 검증

### 컴포넌트 구조
- **condition_builder**: 조건 생성 엔진
- **condition_dialog**: 조건 생성 UI
- **condition_validator**: 조건 검증
- **parameter_widgets**: 파라미터 UI
- **compatibility_validator**: 호환성 검증

### UI 구조
- **📊 변수 팔레트** (좌측): 사용 가능한 변수들 (SMA, RSI, MACD 등)
- **🎯 조건 캔버스** (중앙): 조건 조합 영역
- **⚙️ 파라미터 패널** (우측): 세부 설정
- **🔍 미리보기 차트** (하단): 실시간 결과

### 3중 카테고리 호환성 시스템

#### 1. Purpose Category (목적별 분류)
- **trend**: 추세 지표 (SMA, EMA, MACD)
- **momentum**: 모멘텀 지표 (RSI, Stochastic)
- **volatility**: 변동성 지표 (Bollinger Bands, ATR)
- **volume**: 거래량 지표 (Volume, VWAP)
- **price**: 가격 지표 (Close, High, Low)

#### 2. Chart Category (차트 표시 방식)
- **overlay**: 가격 차트 위 오버레이 (이동평균, 볼린저밴드)
- **subplot**: 별도 서브플롯 (RSI, MACD, Stochastic)

#### 3. Comparison Group (비교 가능성)
- **price_comparable**: 가격과 직접 비교 가능 (이동평균, 볼린저밴드)
- **percentage_comparable**: 백분율 기준 비교 (RSI, Stochastic)
- **zero_centered**: 0 중심 지표 (MACD, Williams %R)

### 호환성 검증 규칙
- **기본 원칙**: 같은 comparison_group = 직접 비교 가능
- **경고 사항**: 다른 comparison_group = 비교 불가 (UI 경고)
- **예외 처리**: price vs percentage = 정규화 필요

### 사용자 워크플로
1. **변수 선택**: 변수 팔레트에서 지표 선택 (RSI, SMA 등)
2. **파라미터 설정**: 기간, 소스 등 세부 설정
3. **조건 생성**: 비교 연산자와 대상값 설정
4. **조건 조합**: AND/OR 논리로 조건 조합

### 실시간 검증
- **CompatibilityValidator**: 변수 선택 시 즉시 필터링
- **호환성 검사**: 실시간 변수 호환성 확인
- **경고 표시**: 비호환 조합 시 명확한 메시지

---

## 🔗 변수 호환성 검증 (VARIABLE_COMPATIBILITY)

### 핵심 호환성 규칙
- **같은 Comparison Group = 직접 비교 가능**
- **다른 Comparison Group = 비교 불가능**
- **Domain Service로 의미있는 변수 비교만 허용**

### 카테고리별 분류
```python
COMPARISON_GROUPS = {
    "price_comparable": {
        "variables": ["Close", "Open", "High", "Low", "SMA", "EMA", "BB_Upper", "BB_Lower"],
        "unit": "KRW",
        "range": "동적 (시장 가격에 따라 변동)"
    },
    "percentage_comparable": {
        "variables": ["RSI", "Stochastic_K", "Stochastic_D", "Williams_R"],
        "unit": "%",
        "range": "0-100 또는 -100~0"
    },
    "zero_centered": {
        "variables": ["MACD", "MACD_Signal", "MACD_Histogram", "ROC", "CCI"],
        "unit": "없음",
        "range": "0 중심으로 양수/음수 변동"
    },
    "volume_based": {
        "variables": ["Volume", "Volume_SMA", "VWAP"],
        "unit": "개수/KRW",
        "range": "거래량 기준"
    }
}
```

### 호환성 예시
```python
# ✅ 호환 가능한 조합
"SMA(20) > EMA(10)"           # 둘 다 price_comparable
"RSI > Stochastic_K"          # 둘 다 percentage_comparable
"MACD > Williams_R"           # 둘 다 zero_centered

# ⚠️ 경고 - 정규화 필요
"Close > RSI"                 # price vs percentage (자동 정규화)

# ❌ 비교 불가
"RSI > MACD"                  # percentage vs zero_centered
"Volume > RSI"                # 완전히 다른 단위
```

### Domain Service 기반 실시간 검증
```python
class VariableCompatibilityDomainService:
    def filter_compatible_variables(self, base_variable_id: VariableId) -> List[Variable]:
        """기본 변수와 호환 가능한 변수들만 반환"""
        base_variable = self.variable_repository.find_by_id(base_variable_id)
        compatible_variables = []

        for var in self.variable_repository.find_all_active():
            if var.check_compatibility_with(base_variable).is_valid():
                compatible_variables.append(var)

        return compatible_variables
```

### 자동 정규화 시스템
- **minmax 정규화**: 0-100 스케일로 변환
- **zscore 정규화**: Z-스코어 표준화
- **경고 메시지**: 정규화 적용 시 해석 주의 안내

### 호환성 매트릭스
```
            | Price | Percentage | Zero-Centered | Volume
------------|-------|------------|---------------|--------
Price       |   ✅   |     ⚠️     |       ❌      |   ❌
Percentage  |   ⚠️   |     ✅     |       ❌      |   ❌
Zero-Center |   ❌   |     ❌     |       ✅      |   ❌
Volume      |   ❌   |     ❌     |       ❌      |   ✅

✅ 직접 비교 가능
⚠️ 정규화 후 비교 가능 (경고 표시)
❌ 비교 불가능 (차단)
```

### 실시간 경고 시스템
```python
def on_external_variable_selected(self, variable_id):
    base_variable = self.get_current_base_variable()
    compatibility = self.check_compatibility(base_variable.id, variable_id)

    if compatibility == "incompatible":
        self.show_error_message(f"'{base_variable.name}'과 '{variable_id}'는 비교할 수 없습니다.")
        return False
    elif compatibility == "warning":
        self.show_warning_message("정규화를 통한 비교입니다. 결과 해석에 주의하세요.")

    return True
```

---

## 💡 실전 개발 가이드

### UI 개발 워크플로
1. **설계**: 7규칙 전략 워크플로 기준으로 UI 구조 설계
2. **구현**: QSS 테마 시스템 활용, objectName 설정
3. **검증**: 다크/라이트 테마 모두 테스트, 접근성 확인
4. **최적화**: 성능 측정, 메모리 관리, 반응성 확인

### 차트 개발 필수 단계
1. **테마 적용**: apply_matplotlib_theme_simple() 호출
2. **동적 색상**: is_dark_theme() 분기 처리
3. **배경 설정**: Figure, Canvas, Subplot 배경색 통일
4. **이벤트 처리**: theme_changed 신호 연결
5. **데이터 저장**: 테마 변경 시 재생성용 데이터 보관

### 트리거 빌더 구현 순서
1. **변수 시스템**: 3중 카테고리 분류 시스템
2. **호환성 검증**: Domain Service 기반 실시간 검증
3. **UI 인터페이스**: 드래그앤드롭, 파라미터 설정
4. **조건 생성**: 논리 조합, 실시간 미리보기
5. **통합 테스트**: 7규칙 전략 구성 가능 여부

### 성능 최적화 전략
- **UI 렌더링**: 지연 로딩, 가상화, 캐싱
- **차트 시스템**: 데이터 포인트 제한, 렌더링 최적화
- **메모리 관리**: 약한 참조, 정기 정리, 이벤트 해제
- **반응성**: 비동기 처리, 프로그레스 표시

### 접근성 구현
- **키보드**: Tab 순서, 단축키, Enter/Space 지원
- **시각**: 고대비 모드, 색상 외 구분 요소
- **확대**: 150%까지 레이아웃 유지
- **스크린리더**: 적절한 라벨과 설명

---

**🎯 UI 개발 성공 기준**: 사용자가 7규칙 전략을 쉽게 구성할 수 있는 UI
**💡 핵심**: 테마 시스템 준수, 실시간 호환성 검증, 직관적 사용자 경험!
