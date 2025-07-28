# 🎨 디자인 시스템

> **참조**: `.vscode/project-specs.md`의 UI/UX 설계 원칙

## 🎯 디자인 철학

**핵심 원칙**: 직관적이고 일관된 사용자 경험  
**목표 사용자**: 초보자도 80% 기능을 무도움으로 사용  
**반응성**: 사용자 입력 0.5초 내 반응  
**접근성**: 최소 1280x720 해상도 지원

## 📏 윈도우 크기 및 레이아웃 시스템

### 트리거 빌더 화면 크기 설정

```python
class TriggerBuilderDimensions:
    """트리거 빌더 화면 크기 및 레이아웃 설정"""
    
    # 윈도우 크기 (유연한 크기 설정)
    WINDOW_WIDTH = 1600         # 권장 너비
    WINDOW_HEIGHT = 1000        # 권장 높이
    WINDOW_MIN_WIDTH = 1200     # 최소 너비 (느슨하게)
    WINDOW_MIN_HEIGHT = 800     # 최소 높이 (느슨하게)
    
    # 실제 테스트된 영역 크기 (2025-07-25 검증) - 참고용
    CONDITION_BUILDER_WIDTH = 512   # 조건 빌더 영역 (가변)
    CONDITION_BUILDER_HEIGHT = 920  # 높이는 자동 조절
    
    TRIGGER_LIST_WIDTH = 631        # 트리거 리스트 영역 (가변)
    TRIGGER_LIST_HEIGHT = 456       # 높이는 자동 조절
    
    SIMULATION_AREA_WIDTH = 421     # 시뮬레이션 영역 (가변)
    SIMULATION_AREA_HEIGHT = 456    # 높이는 자동 조절
    
    # 그리드 비율 (유연한 비율)
    GRID_RATIO_CONDITION = 2        # 조건 빌더 (적당히 넓게)
    GRID_RATIO_TRIGGER_LIST = 3     # 트리거 관리 (가장 넓게)
    GRID_RATIO_SIMULATION = 2       # 시뮬레이션 (적당히 넓게)
    
    # 마진 및 간격 (여유있게)
    MAIN_MARGIN = 8                 # 메인 레이아웃 마진
    GRID_SPACING = 10               # 그리드 간격
    WIDGET_MARGIN = 8               # 위젯 내부 마진
    WIDGET_SPACING = 5              # 위젯 내부 간격
```

### 화면 해상도별 대응

```python
class ResponsiveLayout:
    """반응형 레이아웃 설정 - 유연한 크기 조절"""
    
    # 1920x1080 (FHD) - 기본 권장
    FHD_SCALE = 1.0
    FHD_WINDOW_SIZE = (1600, 1000)     # 권장 크기
    
    # 1366x768 (HD) - 최소 지원 (여유있게)
    HD_SCALE = 0.8
    HD_WINDOW_SIZE = (1100, 700)       # 여유있는 최소 크기
    
    # 2560x1440 (QHD) - 고해상도 (넉넉하게)
    QHD_SCALE = 1.3
    QHD_WINDOW_SIZE = (2000, 1300)     # 넉넉한 크기
    
    # 자동 스케일링 기준 (여유있게)
    MIN_RESOLUTION = (1024, 768)       # 최소 지원 해상도
    OPTIMAL_RESOLUTION = (1600, 1000)  # 최적 해상도
    MAX_RESOLUTION = (3840, 2160)      # 최대 지원 해상도
    
    # 유연한 크기 조절 옵션
    ALLOW_RESIZE = True                # 크기 조절 허용
    MAINTAIN_ASPECT_RATIO = False      # 비율 강제 유지 안함
    AUTO_SCALE_CONTENT = True          # 내용 자동 스케일링
```

## 🎨 색상 시스템 (Color Palette)

### 기본 색상
```python
class ColorPalette:
    """프로젝트 색상 팔레트"""
    
    # 주요 색상
    PRIMARY = "#1E88E5"      # 파란색 - 주요 동작, 브랜드
    PRIMARY_DARK = "#1565C0" # 진한 파란색 - 호버 상태
    PRIMARY_LIGHT = "#64B5F6" # 연한 파란색 - 비활성 상태
    
    # 의미 색상
    SUCCESS = "#4CAF50"      # 녹색 - 성공, 이익, 매수
    WARNING = "#FF9800"      # 주황색 - 경고, 주의
    DANGER = "#F44336"       # 빨간색 - 위험, 손실, 매도
    INFO = "#2196F3"         # 하늘색 - 정보, 알림
    
    # 중성 색상
    BACKGROUND = "#FAFAFA"   # 연회색 - 메인 배경
    SURFACE = "#FFFFFF"      # 흰색 - 카드, 패널 배경
    BORDER = "#E0E0E0"       # 연회색 - 테두리
    DIVIDER = "#BDBDBD"      # 회색 - 구분선
    
    # 텍스트 색상
    TEXT_PRIMARY = "#212121"    # 진한 회색 - 주요 텍스트
    TEXT_SECONDARY = "#757575"  # 회색 - 보조 텍스트
    TEXT_DISABLED = "#BDBDBD"   # 연회색 - 비활성 텍스트
    TEXT_ON_PRIMARY = "#FFFFFF" # 흰색 - 주요 색상 위 텍스트
    
    # 차트 색상
    CHART_BULLISH = "#4CAF50"   # 녹색 - 상승 캔들
    CHART_BEARISH = "#F44336"   # 빨간색 - 하락 캔들
    CHART_GRID = "#E8E8E8"      # 연회색 - 차트 격자
    CHART_BACKGROUND = "#FFFFFF" # 흰색 - 차트 배경
```

### 다크 모드 색상
```python
class DarkColorPalette:
    """다크 모드 색상 팔레트"""
    
    PRIMARY = "#2196F3"         # 파란색 (더 밝게)
    PRIMARY_DARK = "#1976D2"
    PRIMARY_LIGHT = "#64B5F6"
    
    SUCCESS = "#66BB6A"         # 녹색 (더 밝게)  
    WARNING = "#FFA726"         # 주황색 (더 밝게)
    DANGER = "#EF5350"          # 빨간색 (더 밝게)
    INFO = "#42A5F5"            # 하늘색 (더 밝게)
    
    BACKGROUND = "#121212"       # 진한 회색 - 메인 배경
    SURFACE = "#1E1E1E"         # 진한 회색 - 카드 배경
    BORDER = "#333333"          # 회색 - 테두리
    DIVIDER = "#444444"         # 회색 - 구분선
    
    TEXT_PRIMARY = "#FFFFFF"     # 흰색 - 주요 텍스트
    TEXT_SECONDARY = "#CCCCCC"   # 연회색 - 보조 텍스트
    TEXT_DISABLED = "#666666"    # 회색 - 비활성 텍스트
    TEXT_ON_PRIMARY = "#000000"  # 검은색 - 주요 색상 위 텍스트
```

## 🎭 타이포그래피 (Typography)

### 폰트 시스템
```python
class FontSystem:
    """폰트 시스템 정의"""
    
    # 기본 폰트 패밀리
    FONT_FAMILY = ["맑은 고딕", "Malgun Gothic", "Segoe UI", "Arial", "sans-serif"]
    MONOSPACE_FAMILY = ["Consolas", "Monaco", "Courier New", "monospace"]
    
    # 폰트 크기 (px)
    SIZE_DISPLAY = 28      # 큰 제목
    SIZE_HEADLINE = 24     # 섹션 제목
    SIZE_TITLE = 20        # 하위 제목
    SIZE_SUBHEADING = 16   # 소제목
    SIZE_BODY = 14         # 본문
    SIZE_CAPTION = 12      # 캡션, 설명
    SIZE_SMALL = 10        # 작은 텍스트
    
    # 폰트 두께
    WEIGHT_LIGHT = 300     # 얇게
    WEIGHT_REGULAR = 400   # 보통
    WEIGHT_MEDIUM = 500    # 중간
    WEIGHT_BOLD = 700      # 굵게
```

### 텍스트 스타일 적용
```python
def apply_text_style(widget: QWidget, style_type: str):
    """텍스트 스타일 적용"""
    styles = {
        'display': f"""
            font-family: {', '.join(FontSystem.FONT_FAMILY)};
            font-size: {FontSystem.SIZE_DISPLAY}px;
            font-weight: {FontSystem.WEIGHT_BOLD};
            color: {ColorPalette.TEXT_PRIMARY};
        """,
        'headline': f"""
            font-family: {', '.join(FontSystem.FONT_FAMILY)};
            font-size: {FontSystem.SIZE_HEADLINE}px;
            font-weight: {FontSystem.WEIGHT_MEDIUM};
            color: {ColorPalette.TEXT_PRIMARY};
        """,
        'body': f"""
            font-family: {', '.join(FontSystem.FONT_FAMILY)};
            font-size: {FontSystem.SIZE_BODY}px;
            font-weight: {FontSystem.WEIGHT_REGULAR};
            color: {ColorPalette.TEXT_PRIMARY};
        """,
        'caption': f"""
            font-family: {', '.join(FontSystem.FONT_FAMILY)};
            font-size: {FontSystem.SIZE_CAPTION}px;
            font-weight: {FontSystem.WEIGHT_REGULAR};
            color: {ColorPalette.TEXT_SECONDARY};
        """
    }
    
    if style_type in styles:
        widget.setStyleSheet(styles[style_type])
```

## 🧩 간격 시스템 (Spacing)

### 표준 간격 값
```python
class Spacing:
    """표준 간격 시스템 (px)"""
    
    XS = 4      # 매우 작은 간격
    SM = 8      # 작은 간격  
    MD = 16     # 중간 간격 (기본)
    LG = 24     # 큰 간격
    XL = 32     # 매우 큰 간격
    XXL = 48    # 특별히 큰 간격
    
    # 컴포넌트별 특수 간격
    BUTTON_PADDING = 12     # 버튼 내부 여백
    CARD_PADDING = 16       # 카드 내부 여백
    SECTION_MARGIN = 24     # 섹션 간 여백
    FORM_SPACING = 16       # 폼 요소 간 간격
```

## 🔲 그림자 시스템 (Elevation)

### 깊이별 그림자
```python
class Elevation:
    """그림자 깊이 시스템"""
    
    LEVEL_1 = "0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)"  # 카드
    LEVEL_2 = "0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23)"  # 버튼
    LEVEL_3 = "0 10px 20px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23)" # 다이얼로그
    LEVEL_4 = "0 14px 28px rgba(0,0,0,0.25), 0 10px 10px rgba(0,0,0,0.22)" # 드롭다운
    LEVEL_5 = "0 19px 38px rgba(0,0,0,0.30), 0 15px 12px rgba(0,0,0,0.22)" # 모달
```

## 📐 레이아웃 그리드 시스템

### 그리드 기본 설정
```python
class GridSystem:
    """그리드 시스템 설정"""
    
    # 컨테이너 최대 너비
    CONTAINER_MAX_WIDTH = 1440
    
    # 컬럼 설정
    COLUMNS = 12           # 총 12컬럼
    GUTTER = 24           # 컬럼 간 간격
    MARGIN = 24           # 양쪽 여백
    
    # 브레이크포인트
    BREAKPOINT_SM = 768   # 태블릿
    BREAKPOINT_MD = 1024  # 데스크톱
    BREAKPOINT_LG = 1440  # 대형 데스크톱
    
    # 컴포넌트 비율 (3탭 전략 관리)
    STRATEGY_LIST_RATIO = 25    # 전략 목록 25%
    PARAMETER_RATIO = 50        # 파라미터 설정 50%  
    PREVIEW_RATIO = 25          # 미리보기 25%
```

## 🎛️ 컴포넌트 변형 (Component Variants)

### 버튼 변형
```python
class ButtonVariants:
    """버튼 스타일 변형"""
    
    @staticmethod
    def primary_style():
        return f"""
            QPushButton {{
                background-color: {ColorPalette.PRIMARY};
                color: {ColorPalette.TEXT_ON_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: {Spacing.BUTTON_PADDING}px {Spacing.MD}px;
                font-size: {FontSystem.SIZE_BODY}px;
                font-weight: {FontSystem.WEIGHT_MEDIUM};
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {ColorPalette.PRIMARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {ColorPalette.PRIMARY_LIGHT};
            }}
            QPushButton:disabled {{
                background-color: {ColorPalette.BORDER};
                color: {ColorPalette.TEXT_DISABLED};
            }}
        """
    
    @staticmethod
    def secondary_style():
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {ColorPalette.TEXT_PRIMARY};
                border: 2px solid {ColorPalette.BORDER};
                border-radius: 6px;
                padding: {Spacing.BUTTON_PADDING}px {Spacing.MD}px;
                font-size: {FontSystem.SIZE_BODY}px;
                font-weight: {FontSystem.WEIGHT_MEDIUM};
                min-height: 40px;
            }}
            QPushButton:hover {{
                border-color: {ColorPalette.PRIMARY};
                color: {ColorPalette.PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {ColorPalette.PRIMARY_LIGHT};
            }}
        """
    
    @staticmethod
    def danger_style():
        return f"""
            QPushButton {{
                background-color: {ColorPalette.DANGER};
                color: {ColorPalette.TEXT_ON_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: {Spacing.BUTTON_PADDING}px {Spacing.MD}px;
                font-size: {FontSystem.SIZE_BODY}px;
                font-weight: {FontSystem.WEIGHT_MEDIUM};
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: #D32F2F;
            }}
            QPushButton:pressed {{
                background-color: #FFCDD2;
            }}
        """
```

### 입력 필드 변형
```python
class InputVariants:
    """입력 필드 스타일 변형"""
    
    @staticmethod
    def line_edit_style():
        return f"""
            QLineEdit {{
                background-color: {ColorPalette.SURFACE};
                border: 2px solid {ColorPalette.BORDER};
                border-radius: 6px;
                padding: {Spacing.SM}px {Spacing.BUTTON_PADDING}px;
                font-size: {FontSystem.SIZE_BODY}px;
                color: {ColorPalette.TEXT_PRIMARY};
                min-height: 20px;
            }}
            QLineEdit:focus {{
                border-color: {ColorPalette.PRIMARY};
            }}
            QLineEdit:disabled {{
                background-color: {ColorPalette.BACKGROUND};
                color: {ColorPalette.TEXT_DISABLED};
            }}
        """
    
    @staticmethod
    def combo_box_style():
        return f"""
            QComboBox {{
                background-color: {ColorPalette.SURFACE};
                border: 2px solid {ColorPalette.BORDER};
                border-radius: 6px;
                padding: {Spacing.SM}px {Spacing.BUTTON_PADDING}px;
                font-size: {FontSystem.SIZE_BODY}px;
                color: {ColorPalette.TEXT_PRIMARY};
                min-height: 20px;
            }}
            QComboBox:focus {{
                border-color: {ColorPalette.PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }}
        """
```

## 📊 차트 스타일링

### 차트 색상 및 스타일
```python
class ChartStyles:
    """차트 스타일 정의"""
    
    @staticmethod
    def candlestick_style():
        return {
            'bullish_color': ColorPalette.CHART_BULLISH,
            'bearish_color': ColorPalette.CHART_BEARISH,
            'background_color': ColorPalette.CHART_BACKGROUND,
            'grid_color': ColorPalette.CHART_GRID,
            'text_color': ColorPalette.TEXT_PRIMARY,
            'border_width': 1,
            'candle_width': 0.8
        }
    
    @staticmethod
    def indicator_colors():
        return {
            'sma_20': '#2196F3',     # 파란색
            'sma_50': '#FF9800',     # 주황색
            'ema_12': '#9C27B0',     # 보라색
            'ema_26': '#795548',     # 갈색
            'bollinger_upper': '#F44336',  # 빨간색
            'bollinger_lower': '#4CAF50',  # 녹색
            'bollinger_middle': '#607D8B', # 회색
            'rsi': '#E91E63',        # 분홍색
            'macd_line': '#3F51B5',  # 남색
            'macd_signal': '#FF5722', # 주황빨강
            'volume': '#9E9E9E'      # 회색
        }
```

## 🏗️ 레이아웃 컴포넌트

### 카드 컴포넌트
```python
class StyledCard(QWidget):
    """스타일된 카드 컴포넌트"""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        """카드 UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.CARD_PADDING, Spacing.CARD_PADDING, 
                                 Spacing.CARD_PADDING, Spacing.CARD_PADDING)
        layout.setSpacing(Spacing.MD)
        
        if self.title:
            title_label = QLabel(self.title)
            apply_text_style(title_label, 'headline')
            layout.addWidget(title_label)
            
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)
        
    def apply_styles(self):
        """카드 스타일 적용"""
        self.setStyleSheet(f"""
            StyledCard {{
                background-color: {ColorPalette.SURFACE};
                border: 1px solid {ColorPalette.BORDER};
                border-radius: 8px;
                box-shadow: {Elevation.LEVEL_1};
            }}
        """)
        
    def add_content(self, widget: QWidget):
        """카드에 컨텐츠 추가"""
        self.content_layout.addWidget(widget)
```

### 섹션 구분자
```python
class SectionDivider(QWidget):
    """섹션 구분선 컴포넌트"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.text = text
        self.setup_ui()
        
    def setup_ui(self):
        """구분자 UI 구성"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, Spacing.LG, 0, Spacing.LG)
        
        if self.text:
            # 왼쪽 선
            left_line = QFrame()
            left_line.setFrameShape(QFrame.Shape.HLine)
            left_line.setStyleSheet(f"background-color: {ColorPalette.DIVIDER};")
            
            # 텍스트
            text_label = QLabel(self.text)
            apply_text_style(text_label, 'caption')
            text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # 오른쪽 선  
            right_line = QFrame()
            right_line.setFrameShape(QFrame.Shape.HLine)
            right_line.setStyleSheet(f"background-color: {ColorPalette.DIVIDER};")
            
            layout.addWidget(left_line, 1)
            layout.addWidget(text_label, 0)
            layout.addWidget(right_line, 1)
        else:
            # 텍스트 없는 구분선
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setStyleSheet(f"""
                background-color: {ColorPalette.DIVIDER};
                border: none;
                height: 1px;
            """)
            layout.addWidget(line)
```

## 🎭 애니메이션 및 전환 효과

### 기본 애니메이션
```python
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtWidgets import QGraphicsOpacityEffect

class AnimationHelper:
    """애니메이션 도우미 클래스"""
    
    @staticmethod
    def fade_in(widget: QWidget, duration: int = 300):
        """페이드 인 애니메이션"""
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()
        
        return animation
    
    @staticmethod
    def fade_out(widget: QWidget, duration: int = 300):
        """페이드 아웃 애니메이션"""
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1)
        animation.setEndValue(0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()
        
        return animation
    
    @staticmethod
    def slide_in_from_right(widget: QWidget, duration: int = 300):
        """오른쪽에서 슬라이드 인"""
        original_pos = widget.pos()
        start_pos = original_pos + QPoint(widget.width(), 0)
        widget.move(start_pos)
        
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(start_pos)
        animation.setEndValue(original_pos)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()
        
        return animation
```

## 📱 반응형 디자인

### 반응형 레이아웃 관리
```python
class ResponsiveLayout(QWidget):
    """반응형 레이아웃 관리"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_breakpoint = 'lg'
        self.setup_responsive_behavior()
        
    def setup_responsive_behavior(self):
        """반응형 동작 설정"""
        self.installEventFilter(self)
        
    def eventFilter(self, obj, event):
        """크기 변경 감지"""
        if event.type() == QEvent.Type.Resize:
            self.handle_resize(event.size())
        return super().eventFilter(obj, event)
        
    def handle_resize(self, size):
        """크기 변경 처리"""
        width = size.width()
        
        if width >= GridSystem.BREAKPOINT_LG:
            new_breakpoint = 'lg'
        elif width >= GridSystem.BREAKPOINT_MD:
            new_breakpoint = 'md'
        else:
            new_breakpoint = 'sm'
            
        if new_breakpoint != self.current_breakpoint:
            self.current_breakpoint = new_breakpoint
            self.apply_responsive_layout()
            
    def apply_responsive_layout(self):
        """반응형 레이아웃 적용"""
        if self.current_breakpoint == 'sm':
            # 작은 화면: 세로 배치
            self.apply_mobile_layout()
        elif self.current_breakpoint == 'md':
            # 중간 화면: 2열 배치
            self.apply_tablet_layout()
        else:
            # 큰 화면: 3열 배치
            self.apply_desktop_layout()
```

이 디자인 시스템은 일관된 사용자 경험과 확장 가능한 UI 컴포넌트 라이브러리를 제공하여 개발 효율성과 품질을 모두 향상시킵니다.
