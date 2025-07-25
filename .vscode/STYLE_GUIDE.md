# 🎨 Upbit 자동거래 시스템 스타일 가이드

> **중요**: 모든 개발자는 이 스타일 가이드를 준수하여 일관성 있는 코드를 작성해야 합니다.

## 📋 목차
- [1. UI/UX 테마 시스템 가이드](#1-uiux-테마-시스템-가이드)
- [2. PyQt6 스타일링 규칙](#2-pyqt6-스타일링-규칙)
- [3. Matplotlib 차트 스타일링](#3-matplotlib-차트-스타일링)
- [4. 코드 작성 규칙](#4-코드-작성-규칙)
- [5. 파일 구조 및 네이밍](#5-파일-구조-및-네이밍)

---

## 1. UI/UX 테마 시스템 가이드

### ✅ DO: 반드시 지켜야 할 규칙

#### 테마 시스템 활용
```python
# ✅ 올바른 방법: QSS 테마 시스템 활용
widget.setObjectName("특정_위젯명")  # QSS 선택자용
# QSS 파일에서 스타일 정의

# ✅ 차트에서 테마 알림 시스템 사용
from upbit_auto_trading.ui.desktop.common.theme_notifier import get_theme_notifier
theme_notifier = get_theme_notifier()
theme_notifier.theme_changed.connect(self._on_theme_changed)
```

#### matplotlib 차트 테마 적용
```python
# ✅ 반드시 사용해야 하는 테마 적용
from upbit_auto_trading.ui.desktop.common.theme_notifier import apply_matplotlib_theme_simple
apply_matplotlib_theme_simple()  # 차트 그리기 전에 호출

# ✅ 테마별 동적 색상 사용
theme_notifier = get_theme_notifier()
is_dark = theme_notifier.is_dark_theme()
line_color = '#60a5fa' if is_dark else '#3498db'
bg_color = '#2c2c2c' if is_dark else 'white'
```

### ❌ DON'T: 절대 하지 말아야 할 것들

#### 하드코딩된 스타일
```python
# ❌ 금지: 하드코딩된 배경색
widget.setStyleSheet("background-color: white;")
widget.setStyleSheet("background-color: #2c2c2c;")

# ❌ 금지: 하드코딩된 차트 색상
ax.plot(data, color='blue')  # 테마 무시
ax.set_facecolor('white')    # 고정 배경색

# ❌ 금지: 지원하지 않는 CSS 속성
setStyleSheet("cursor: not-allowed;")  # Qt에서 지원 안함
```

---

## 2. PyQt6 스타일링 규칙

### QSS 파일 활용
- **위치**: `upbit_auto_trading/ui/desktop/common/styles/`
- **파일**: `default_style.qss` (라이트), `dark_style.qss` (다크)

### objectName 기반 스타일링
```python
# ✅ 특정 위젯 스타일링
self.chart_widget = QWidget()
self.chart_widget.setObjectName("chart_widget")
# QSS에서 QWidget#chart_widget { ... } 로 스타일 정의

# ✅ 다이얼로그 라벨 스타일링
info_label = QLabel("정보")
info_label.setObjectName("infoDialogLabel")
```

### 위젯별 권장 objectName
- 차트 위젯: `chart_widget`, `chart_canvas`
- 다이얼로그 라벨: `helpDialogLabel`, `infoDialogLabel`
- 상태 라벨: `statusLabel`, `simulationStatus`
- 제목 라벨: `titleLabel`
- 구분선: `separator`

---

## 3. Matplotlib 차트 스타일링

### 필수 패턴
```python
def create_chart(self):
    # 1️⃣ 테마 적용 (필수)
    from upbit_auto_trading.ui.desktop.common.theme_notifier import (
        apply_matplotlib_theme_simple, get_theme_notifier
    )
    apply_matplotlib_theme_simple()
    
    # 2️⃣ 테마별 색상 설정
    theme_notifier = get_theme_notifier()
    is_dark = theme_notifier.is_dark_theme()
    
    # 3️⃣ 동적 색상 정의
    line_color = '#60a5fa' if is_dark else '#3498db'
    trigger_color = '#f87171' if is_dark else '#ef4444'
    bg_color = '#2c2c2c' if is_dark else 'white'
    
    # 4️⃣ Figure/Canvas 배경 설정
    self.figure.patch.set_facecolor(bg_color)
    if hasattr(self, 'canvas'):
        self.canvas.setStyleSheet(f"background-color: {bg_color};")
    
    # 5️⃣ Subplot 배경 설정
    ax.set_facecolor(bg_color)
```

### 테마 변경 대응
```python
def _on_theme_changed(self, is_dark: bool):
    """테마 변경 시 차트 업데이트"""
    if hasattr(self, 'figure') and CHART_AVAILABLE:
        # 마지막 데이터로 차트 재생성
        if self._last_data:
            self.update_chart(self._last_data)
        else:
            self.show_placeholder_chart()
```

---

## 4. 코드 작성 규칙

### 테마 관련 import
```python
# ✅ 표준 import 패턴
from upbit_auto_trading.ui.desktop.common.theme_notifier import (
    get_theme_notifier, 
    apply_matplotlib_theme_simple
)
```

### 에러 처리
```python
# ✅ 테마 적용 실패 시 graceful fallback
try:
    apply_matplotlib_theme_simple()
except Exception as e:
    print(f"⚠️ 테마 적용 실패: {e}")
    # 기본 스타일로 fallback
```

### 로깅 메시지
```python
# ✅ 일관된 로깅 형식
print("🎨 다크 테마 적용: matplotlib 'dark_background' 스타일")
print("🎨 라이트 테마 적용: matplotlib 기본 스타일")
print("🔍 StyleManager 테마: dark -> 다크")
```

---

## 5. 파일 구조 및 네이밍

### 테마 관련 파일 위치
```
upbit_auto_trading/ui/desktop/common/
├── theme_notifier.py          # 전역 테마 알림 시스템
├── styles/
│   ├── style_manager.py       # 테마 관리자
│   ├── default_style.qss      # 라이트 테마 스타일
│   └── dark_style.qss         # 다크 테마 스타일
```

### 위젯 파일 네이밍
- `*_widget.py`: 재사용 가능한 위젯
- `*_dialog.py`: 다이얼로그 창
- `*_manager.py`: 관리 클래스

---

## 🚨 중요 체크리스트

### 새 UI 컴포넌트 개발 시
- [ ] QSS 테마 시스템 활용
- [ ] 하드코딩된 색상 없음
- [ ] objectName 설정 (필요시)
- [ ] 테마 변경 신호 연결 (차트 포함 시)

### 차트 개발 시
- [ ] `apply_matplotlib_theme_simple()` 호출
- [ ] 동적 색상 시스템 사용
- [ ] Figure/Canvas/Subplot 배경색 설정
- [ ] 테마 변경 이벤트 처리
- [ ] 마지막 데이터 저장으로 재생성 지원

### 코드 리뷰 시
- [ ] 테마 독립적인 코드인지 확인
- [ ] Qt 지원 CSS 속성만 사용했는지 확인
- [ ] 접근성 (다크/라이트 모드 가독성) 확인

---

## 📞 문의사항

테마 시스템 관련 문의사항이 있으면:
1. 기존 코드 참조: `simulation_result_widget.py`
2. 테마 시스템 문서: `theme_notifier.py` 주석 참조
3. QSS 스타일 예시: `default_style.qss`, `dark_style.qss`

---

**⚡ 기억하세요**: 일관된 테마 시스템으로 사용자에게 최고의 경험을 제공합시다! 🎨✨
