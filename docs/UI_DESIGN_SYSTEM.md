# 🎨 UI 디자인 시스템

## 🎯 디자인 철학

**핵심 목표**: 초보자도 80% 기능을 무도움으로 사용할 수 있는 직관적 인터페이스

### 기본 원칙
- **반응성**: 사용자 입력 0.5초 내 반응
- **접근성**: 최소 1280x720 해상도 지원
- **일관성**: 전체 애플리케이션 통일된 스타일
- **7규칙 중심**: 기본 7규칙 전략 워크플로 최적화

## 📐 레이아웃 시스템

### 메인 윈도우 크기
```python
# 권장 크기
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 1000

# 최소 지원 크기
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 800
```

### 트리거 빌더 레이아웃 (3분할)
```
┌─────────────────────────────────────────────────────┐
│                메인 윈도우 (1600x1000)                │
├─────────────┬─────────────────┬─────────────────────┤
│  조건 빌더   │  트리거 관리     │   시뮬레이션 영역    │
│   (2:5)     │    (3:5)        │      (2:5)         │
│             │                │                    │
│ 변수 선택   │ 생성된 조건 목록  │ 백테스팅 차트      │
│ 파라미터    │ 드래그앤드롭     │ 성능 지표          │
│ 호환성 검증  │ 조건 조합       │ 실시간 미리보기     │
└─────────────┴─────────────────┴─────────────────────┘
```

### UI 컴포넌트 구조
```
screens/
├── main_window.py                    # 메인 윈도우
├── market_analysis/                  # 📊 시장 분석 탭
├── strategy_management/              # ⚙️ 전략 관리 탭
│   ├── trigger_builder/              # 트리거 빌더
│   │   └── components/               # UI 컴포넌트들
│   ├── strategy_maker/               # 전략 메이커
│   │   └── components/
│   └── backtesting/                  # 백테스팅
│       └── components/
└── settings/                         # 🔧 설정 탭
    └── components/
```

## 🎨 색상 시스템

### 기본 색상 팔레트
```python
class ColorPalette:
    # 주요 색상
    PRIMARY = "#1E88E5"        # 파란색 - 주요 동작, 브랜드
    PRIMARY_DARK = "#1565C0"   # 진한 파란색 - 호버 상태
    PRIMARY_LIGHT = "#64B5F6"  # 연한 파란색 - 비활성 상태
    
    # 의미 색상
    SUCCESS = "#4CAF50"        # 녹색 - 성공, 매수, 이익
    WARNING = "#FF9800"        # 주황색 - 경고, 주의
    DANGER = "#F44336"         # 빨간색 - 위험, 매도, 손실
    INFO = "#2196F3"           # 하늘색 - 정보, 알림
    
    # 중성 색상
    BACKGROUND = "#FAFAFA"     # 연회색 - 메인 배경
    SURFACE = "#FFFFFF"        # 흰색 - 카드, 패널 배경
    BORDER = "#E0E0E0"         # 연회색 - 테두리
    TEXT_PRIMARY = "#212121"   # 진회색 - 주요 텍스트
    TEXT_SECONDARY = "#757575" # 회색 - 보조 텍스트
```

### 다크/라이트 테마 지원
```python
class ThemeManager:
    def apply_theme(self, theme_name):
        if theme_name == "dark":
            return {
                "background": "#121212",
                "surface": "#1E1E1E", 
                "text_primary": "#FFFFFF",
                "text_secondary": "#B0B0B0"
            }
        else:  # light theme
            return ColorPalette.__dict__
```

## 🖱️ 상호작용 패턴

### 드래그앤드롭 시스템
```python
# 트리거 빌더에서 조건 생성
1. 왼쪽 팔레트에서 변수 선택 (예: RSI)
2. 파라미터 설정 팝업 (기간: 14)
3. 중앙 캔버스로 드래그
4. 비교 연산자 설정 (>)
5. 대상값 설정 (30)
6. 호환성 실시간 검증
```

### 버튼 스타일
```css
/* 주요 동작 버튼 */
.primary-button {
    background-color: #1E88E5;
    color: white;
    border-radius: 4px;
    padding: 8px 16px;
}

/* 위험 동작 버튼 */
.danger-button {
    background-color: #F44336;
    color: white;
}

/* 비활성 버튼 */
.disabled-button {
    background-color: #E0E0E0;
    color: #757575;
}
```

## 📊 차트 및 그래프

### matplotlib 테마 적용
```python
def apply_chart_theme():
    plt.style.use('dark_background' if is_dark_theme() else 'default')
    
    # 차트 색상 설정
    colors = {
        'candle_up': '#4CAF50',    # 상승 캔들 (녹색)
        'candle_down': '#F44336',  # 하락 캔들 (빨간색)
        'volume': '#2196F3',       # 거래량 (파란색)
        'ma_short': '#FF9800',     # 단기 이평선 (주황색)
        'ma_long': '#9C27B0'       # 장기 이평선 (보라색)
    }
```

### 성능 지표 표시
```
┌─────────────────────────────────────┐
│         백테스팅 결과 카드           │
├─────────────────────────────────────┤
│ 📈 총 수익률: +15.3%                │
│ 📉 최대 손실: -8.2%                 │
│ 🎯 승률: 67.4%                      │
│ ⚡ 샤프 비율: 1.84                   │
│ 🔄 총 거래 수: 143                  │
└─────────────────────────────────────┘
```

## 🔧 컴포넌트 스타일링

### QSS 스타일시트 사용
```python
# 하드코딩 금지 - QSS 파일 사용
widget.setObjectName("condition-card")
widget.setStyleSheet("") # QSS 파일에서 로드

# QSS 파일 예시
"""
#condition-card {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    padding: 12px;
}

#condition-card:hover {
    border-color: #1E88E5;
    box-shadow: 0 2px 8px rgba(30, 136, 229, 0.2);
}
"""
```

### 반응형 크기 조절
```python
class ResponsiveWidget(QWidget):
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_layout_for_size(self.size())
    
    def adjust_layout_for_size(self, size):
        if size.width() < 1200:
            self.switch_to_compact_layout()
        else:
            self.switch_to_full_layout()
```

## 🎯 7규칙 전략 전용 UI

### 조건 카드 디자인
```
┌─────────────────────────────────────┐
│ 📈 RSI 과매도 진입                   │ ← 규칙 제목
├─────────────────────────────────────┤
│ RSI(14) < 30                        │ ← 조건 수식
│ 🎯 ENTRY                            │ ← 역할 태그
│                                     │
│ [편집] [삭제] [복사]                 │ ← 액션 버튼
└─────────────────────────────────────┘
```

### 파라미터 설정 팝업
```
┌─────────────────────────────────────┐
│          RSI 지표 설정              │
├─────────────────────────────────────┤
│ 기간 (period)                       │
│ ━━━━━━━●━━━━━━━━━━━━                  │ ← 슬라이더
│ 14 (범위: 2-100)                    │
│                                     │
│ 데이터 소스                          │
│ ┌─────────────────────────────────┐  │
│ │ Close Price               ▼    │  │ ← 드롭다운
│ └─────────────────────────────────┘  │
│                                     │
│ [취소]  [적용]                       │
└─────────────────────────────────────┘
```

## 🚀 성능 최적화

### UI 렌더링 최적화
- **지연 로딩**: 보이지 않는 탭은 필요 시에만 로드
- **가상화**: 긴 목록은 가상 스크롤 사용
- **캐싱**: 차트 데이터와 계산 결과 캐싱

### 메모리 관리
- **WeakRef 사용**: 순환 참조 방지
- **이벤트 해제**: 위젯 삭제 시 이벤트 연결 해제
- **정기 정리**: 사용하지 않는 차트 데이터 정리

## 📱 접근성 고려사항

### 키보드 네비게이션
- **Tab 순서**: 논리적 순서로 포커스 이동
- **단축키**: 주요 기능에 단축키 제공
- **Enter/Space**: 버튼 활성화 지원

### 시각적 접근성
- **고대비**: 텍스트와 배경 충분한 대비
- **색맹 고려**: 색상 외에 모양/패턴으로도 구분
- **확대**: 150%까지 확대 시에도 레이아웃 유지

## 📚 관련 문서

- [개발 체크리스트](DEV_CHECKLIST.md): UI 개발 검증 항목
- [스타일 가이드](STYLE_GUIDE.md): 코딩 표준
- [기본 7규칙 전략](BASIC_7_RULE_STRATEGY_GUIDE.md): UI 설계 기준

---
**💡 핵심**: "사용자가 7규칙 전략을 쉽게 구성할 수 있는 UI가 최고의 UI다!"
