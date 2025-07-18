# UI 가이드

## 개요

업비트 자동매매 시스템은 PyQt6 기반의 데스크톱 애플리케이션으로, 사용자 친화적인 인터페이스를 제공합니다. 이 문서는 UI 컴포넌트의 구조와 사용 방법을 설명합니다.

## UI 구조

애플리케이션의 UI는 다음과 같은 주요 컴포넌트로 구성됩니다:

1. **메인 윈도우 (MainWindow)**: 애플리케이션의 기본 창
2. **네비게이션 바 (NavigationBar)**: 화면 간 이동을 위한 사이드바
3. **콘텐츠 영역 (StackedWidget)**: 현재 선택된 화면을 표시하는 영역
4. **상태 바 (StatusBar)**: 애플리케이션 상태 정보를 표시하는 하단 바
5. **메뉴 바**: 애플리케이션 메뉴를 제공하는 상단 바

## 화면 구성

애플리케이션은 다음과 같은 주요 화면으로 구성됩니다:

1. **대시보드**: 시스템 상태, 포트폴리오 요약, 활성 거래 등을 표시
2. **차트 뷰**: 코인 가격 차트 및 기술적 지표 표시
3. **종목 스크리닝**: 거래량, 변동성, 추세 등을 기반으로 코인 필터링
4. **매매 전략 관리**: 전략 생성, 수정, 저장, 관리
5. **백테스팅**: 과거 데이터를 사용하여 전략 성능 테스트
6. **실시간 거래**: 검증된 전략을 사용하여 실시간 자동 거래
7. **포트폴리오 구성**: 여러 코인과 전략 조합 관리
8. **모니터링 및 알림**: 시장 상황과 거래 활동 모니터링, 중요 이벤트 알림
9. **설정**: 애플리케이션 설정 관리

## 테마 지원

애플리케이션은 라이트 모드와 다크 모드를 지원합니다:

- **라이트 모드**: 밝은 배경과 어두운 텍스트
- **다크 모드**: 어두운 배경과 밝은 텍스트

테마는 다음과 같은 방법으로 전환할 수 있습니다:
1. 메뉴 바의 "보기" > "테마 전환" 선택
2. 코드에서 `StyleManager.toggle_theme()` 메서드 호출

## UI 컴포넌트 사용 방법

### 메인 윈도우 생성

```python
from upbit_auto_trading.ui.desktop.main_window import MainWindow
from PyQt6.QtWidgets import QApplication

# 애플리케이션 생성
app = QApplication([])

# 메인 윈도우 생성
main_window = MainWindow()

# 메인 윈도우 표시
main_window.show()

# 애플리케이션 실행
app.exec()
```

### 화면 전환

```python
# 메인 윈도우에서 화면 전환
main_window._change_screen("dashboard")  # 대시보드로 전환
main_window._change_screen("chart_view")  # 차트 뷰로 전환
main_window._change_screen("settings")  # 설정 화면으로 전환
```

### 상태 바 메시지 표시

```python
# 상태 바에 메시지 표시
main_window.status_bar.show_message("작업이 완료되었습니다.", timeout=3000)

# API 연결 상태 설정
main_window.status_bar.set_api_status(connected=True)

# 데이터베이스 연결 상태 설정
main_window.status_bar.set_db_status(connected=True)
```

### 테마 전환

```python
# 테마 전환
main_window._toggle_theme()
```

### 설정 저장 및 로드

애플리케이션은 사용자 설정을 자동으로 저장하고 로드합니다:

```python
# 설정 로드 (애플리케이션 시작 시 자동 실행)
main_window._load_settings()

# 설정 저장 (애플리케이션 종료 시 자동 실행)
main_window._save_settings()
```

현재 저장되는 설정:
- 윈도우 크기 및 위치
- 테마 설정 (라이트/다크 모드)

사용자 정의 설정을 추가하려면 `_load_settings()` 및 `_save_settings()` 메서드를 확장하면 됩니다:

```python
def _save_settings(self):
    """설정 저장"""
    settings = QSettings("UpbitAutoTrading", "MainWindow")
    
    # 윈도우 크기 및 위치 저장
    settings.setValue("size", self.size())
    settings.setValue("position", self.pos())
    
    # 사용자 정의 설정 저장
    settings.setValue("custom_setting", self.custom_setting)
```

## 레퍼런스 문서 활용

UI 구현 시 `reference` 폴더의 화면 명세서를 적극 활용해야 합니다. 화면 명세서에는 각 화면의 UI 요소, 기능, 백엔드 연결 정보, 사용자 경험 설계 등이 상세히 정의되어 있습니다. 레퍼런스 문서 활용에 대한 자세한 내용은 [레퍼런스 문서 활용 가이드](reference_guide.md)를 참조하세요.

### 화면 명세서 활용 방법

1. **요소 ID 활용**: 화면 명세서에 정의된 요소 ID를 그대로 사용합니다.
   ```python
   # 화면 명세서의 요소 ID 활용
   self.total_assets_widget = TotalAssetsWidget()
   self.total_assets_widget.setObjectName("widget-total-assets")
   ```

2. **백엔드 연결**: 화면 명세서의 '연결 기능(Backend/API)' 정보를 참조하여 UI와 백엔드 로직을 연결합니다.
   ```python
   # 화면 명세서의 연결 기능 정보 활용
   from data_layer.collectors.upbit_api import UpbitAPI
   
   api = UpbitAPI()
   ticker_data = api.get_tickers()
   ```

3. **사용자 경험 구현**: 화면 명세서의 '사용자 경험(UX)' 설계를 참조하여 UI 동작을 구현합니다.
   ```python
   # 화면 명세서의 사용자 경험 설계 활용
   def _update_price(self, price, change_percent):
       # 가격 상승/하락에 따른 색상 변경 (화면 명세서 UX 참조)
       if change_percent >= 0:
           self.price_label.setStyleSheet("color: green;")
       else:
           self.price_label.setStyleSheet("color: red;")
   ```

자세한 레퍼런스 문서 활용 지침은 `upbit_auto_trading/docs/reference_guide.md` 문서를 참조하세요.

## 새로운 화면 추가 방법

1. `reference` 폴더의 해당 화면 명세서를 검토합니다.
2. `upbit_auto_trading/ui/desktop/screens/` 디렉토리에 새 화면 모듈 생성합니다.
3. `QWidget`을 상속받는 화면 클래스를 구현하고, 화면 명세서의 요소 ID와 설계를 반영합니다.
4. `MainWindow` 클래스의 `_add_screens()` 메서드에 화면을 추가합니다.
5. `NavigationBar` 클래스에 해당 화면으로 이동하는 버튼을 추가합니다.
6. `MainWindow` 클래스의 `_change_screen()` 메서드에 화면 전환 로직을 추가합니다.

예시:
```python
# 화면 명세서를 참조하여 새 화면 클래스 구현
class DashboardScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 화면 명세서의 요소 ID 활용
        total_assets_widget = TotalAssetsWidget()
        total_assets_widget.setObjectName("widget-total-assets")
        
        portfolio_summary_widget = PortfolioSummaryWidget()
        portfolio_summary_widget.setObjectName("widget-portfolio-summary")
        
        layout.addWidget(total_assets_widget)
        layout.addWidget(portfolio_summary_widget)

# MainWindow._add_screens() 메서드에 화면 추가
def _add_screens(self):
    # 기존 화면들...
    
    # 새 화면 추가
    dashboard_screen = DashboardScreen()
    self.stack_widget.addWidget(dashboard_screen)

# MainWindow._change_screen() 메서드에 화면 전환 로직 추가
def _change_screen(self, screen_name):
    # 기존 로직...
    
    # 새 화면 전환 로직 추가
    elif screen_name == "dashboard":
        self.stack_widget.setCurrentIndex(0)  # 인덱스는 추가된 순서에 따라 조정
```

## 스타일 커스터마이징

애플리케이션의 스타일은 QSS(Qt Style Sheets)를 사용하여 커스터마이징할 수 있습니다:

1. `upbit_auto_trading/ui/desktop/common/styles/` 디렉토리의 QSS 파일 수정
2. `StyleManager` 클래스를 통해 스타일 적용

예시:
```python
from upbit_auto_trading.ui.desktop.common.styles.style_manager import StyleManager

# 스타일 관리자 생성
style_manager = StyleManager()

# 커스텀 스타일 적용
style_manager.apply_custom_style("path/to/custom_style.qss")
```