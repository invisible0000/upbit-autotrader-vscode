# PyQt6 빈 위젯 Bool 평가 문제 - GUI 아키텍처 주의사항

## 🚨 핵심 문제

PyQt6에서 **빈 컨테이너 위젯들은 `bool()` 평가 시 `False`를 반환**합니다.

```python
# 위험한 코드 패턴
list_widget = QListWidget()  # 정상 생성됨
if not list_widget:          # ❌ False! (빈 위젯이므로)
    raise Error("위젯 생성 실패")  # 잘못된 에러 발생

# 안전한 코드 패턴
if list_widget is None:      # ✅ 올바른 None 체크
    raise Error("위젯 생성 실패")
```

## 📋 영향받는 위젯들

| 위젯 타입 | 빈 상태에서 bool() | 이유 |
|-----------|------------------|------|
| `QListWidget` | `False` | `__len__()` 구현, 빈 리스트 |
| `QComboBox` | `False` | `__len__()` 구현, 빈 콤보박스 |
| `QTableWidget` | `False` | `__len__()` 구현, 빈 테이블 |
| `QTreeWidget` | `False` | `__len__()` 구현, 빈 트리 |
| `QWidget` | `True` | `__len__()` 미구현 |
| `QPushButton` | `True` | `__len__()` 미구현 |

## ⚡ GUI 아키텍처에서 위험 요소

### 1. 이벤트 버스 시스템
```python
# 위험한 패턴
class EventBus:
    def register_widget(self, widget):
        if not widget:  # ❌ 빈 QListWidget은 False!
            return      # 정상 위젯이 등록되지 않음
```

### 2. 의존성 주입 (DI)
```python
# 위험한 패턴
class DIContainer:
    def inject_widget(self, widget):
        if not widget:  # ❌ 빈 위젯 주입 실패
            raise ValueError("Invalid widget")
```

### 3. 메모리 관리 시스템
```python
# 위험한 패턴
class WidgetManager:
    def track_widget(self, widget):
        if not widget:  # ❌ 정상 위젯을 추적하지 않음
            return None
        self.widgets.append(widget)
```

### 4. MVP/MVVM 패턴
```python
# 위험한 패턴
class Presenter:
    def bind_view(self, view_widget):
        if not view_widget:  # ❌ 빈 뷰 위젯 바인딩 실패
            self.logger.error("View binding failed")
            return
```

## ✅ 해결책

### 1. None 체크 사용
```python
# 올바른 패턴
if widget is None:           # ✅ None만 체크
if widget is not None:       # ✅ 존재 여부 체크
if hasattr(widget, 'count'): # ✅ 메서드 존재 체크
```

### 2. 타입 체크 활용
```python
from PyQt6.QtWidgets import QWidget

def is_valid_widget(widget) -> bool:
    return isinstance(widget, QWidget) and widget is not None
```

### 3. 팩토리 패턴 적용
```python
class SafeWidgetFactory:
    @staticmethod
    def create_list_widget() -> QListWidget:
        widget = QListWidget()
        if widget is None:  # ✅ 안전한 체크
            raise RuntimeError("위젯 생성 실패")
        return widget
```

## 🔧 코드 리뷰 체크리스트

- [ ] `if not widget:` 패턴 → `if widget is None:` 변경
- [ ] 이벤트 버스 등록 시 None 체크 사용
- [ ] DI 컨테이너에서 타입 기반 검증
- [ ] 메모리 관리자에서 isinstance() 활용
- [ ] MVP 바인딩에서 hasattr() 검증

## 🎯 결론

**PyQt6 GUI 아키텍처에서는 반드시 `is None` 체크를 사용하세요.**
`bool()` 평가는 빈 컨테이너 위젯에서 예상과 다르게 동작하여 복잡한 시스템에서 디버깅하기 어려운 버그를 유발합니다.

---
*본 문서는 upbit-autotrader-vscode 프로젝트의 QListWidget bool 평가 이슈 해결 과정에서 작성되었습니다.*
