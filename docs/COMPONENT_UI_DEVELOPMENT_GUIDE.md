# 컴포넌트 기반 UI 개발 가이드

## 📋 최신 아키텍처: 컴포넌트 전략 시스템 (2025-07-22)

### 🎯 주요 아키텍처 변경
- **기존**: 고정 전략 클래스 → **신규**: 아토믹 컴포넌트 시스템
- **전략 메이커**: 드래그&드롭 기반 비주얼 에디터
- **모듈 분리**: 레거시/컴포넌트 시스템 공존
- **UI 통합**: 메인 앱 내 탭 시스템으로 전략 메이커 임베드

### 🔗 핵심 파일들
- **전략 메이커**: `strategy_maker_ui.py` (독립 실행형)
- **통합 관리 화면**: `upbit_auto_trading/ui/desktop/screens/strategy_management/strategy_management_screen.py`
- **컴포넌트 시스템**: `upbit_auto_trading/component_system/`

---

## 1. 새로운 폴더 구조

```
upbit_auto_trading/
├── component_system/           # 🆕 아토믹 컴포넌트 시스템
│   ├── base/                  # 기본 클래스 및 인터페이스
│   ├── triggers/              # 14개 트리거 컴포넌트
│   │   ├── price_triggers.py
│   │   ├── indicator_triggers.py  
│   │   ├── time_triggers.py
│   │   └── volume_triggers.py
│   ├── actions/               # 3개 액션 컴포넌트
│   │   └── trading_actions.py
│   ├── position_management.py # 태그 기반 포지션 관리
│   └── __init__.py           # 컴포넌트 메타데이터
├── business_logic/
│   └── component_strategy_manager.py  # 🆕 컴포넌트 전략 관리자
├── data_layer/
│   ├── models.py             # 기존 → LegacyStrategy로 변경
│   ├── component_models.py   # 🆕 컴포넌트 전략 모델
│   └── component_migration.py # 🆕 마이그레이션 스크립트
└── ui/
    └── desktop/
        └── screens/
            └── strategy_management/  # 🔄 전면 개편
                ├── strategy_management_screen.py      # 3탭 구조
                └── strategy_management_screen_old.py  # 레거시 백업
```

### 독립 실행형 UI
```
strategy_maker_ui.py    # 🆕 드래그&드롭 전략 빌더 (PyQt6)
```

---

## 2. 전략 메이커 UI 아키텍처

### 2.1 3-Panel 구조
```python
class StrategyMakerUI(QMainWindow):
    def __init__(self):
        # 좌측: 컴포넌트 팔레트
        self.component_palette = ComponentPaletteWidget()
        
        # 중앙: 전략 캔버스  
        self.strategy_canvas = StrategyCanvasWidget()
        
        # 우측: 설정 패널
        self.config_panel = ConfigurationPanelWidget()
```

### 2.2 컴포넌트 팔레트 구조
```python
# 카테고리별 그룹화
COMPONENT_CATEGORIES = {
    'price': ['price_change', 'price_breakout', 'price_crossover'],
    'indicator': ['rsi', 'macd', 'bollinger_bands', 'moving_average_cross'],
    'time': ['periodic', 'scheduled', 'delay'],
    'volume': ['volume_surge', 'volume_drop', 'relative_volume', 'volume_breakout']
}
```

### 2.3 드래그&드롭 메커니즘
```python
class DraggableComponentWidget(QWidget):
    def mousePressEvent(self, event):
        # 드래그 시작 시 컴포넌트 정보 저장
        
    def dragEnterEvent(self, event):
        # 드롭 가능 여부 검증
        
    def dropEvent(self, event):
        # 전략 캔버스에 컴포넌트 추가
```

---

## 3. 통합 관리 화면 구조

### 3.1 3탭 시스템
```python
class StrategyManagementScreen(QWidget):
    def init_ui(self):
        self.tab_widget = QTabWidget()
        
        # 탭 1: 전략 메이커 (메인)
        self.strategy_maker_tab = StrategyMakerUI()
        
        # 탭 2: 백테스팅 (TODO)
        self.backtest_tab = self.create_backtest_tab()
        
        # 탭 3: 전략 분석 (TODO)  
        self.analysis_tab = self.create_analysis_tab()
```

### 3.2 메인 UI 통합
```python
# main_window.py
def create_strategy_management_screen(self):
    if not hasattr(self, '_strategy_management_screen'):
        self._strategy_management_screen = StrategyManagementScreen(self)
    return self._strategy_management_screen
```

---

## 4. 컴포넌트 메타데이터 시스템

### 4.1 동적 UI 생성
```python
# triggers/__init__.py
TRIGGER_METADATA = {
    'price_change': {
        'display_name': '가격 변동 트리거',
        'category': 'price',
        'description': '가격이 지정된 비율만큼 변동했을 때 실행',
        'difficulty': 'beginner',
        'icon': '📈',
        'color': '#e74c3c'
    }
}
```

### 4.2 설정 폼 자동 생성
```python
def create_config_form(self, component_type: str):
    metadata = get_trigger_metadata(component_type)
    config_class = get_config_class(component_type)
    
    # 메타데이터 기반으로 동적 폼 생성
    form = self.generate_form_from_config_class(config_class)
    return form
```

---

## 5. 상태 관리 및 데이터 플로우

### 5.1 전략 데이터 구조
```python
strategy_data = {
    "id": "strategy-uuid",
    "name": "사용자 정의 이름",
    "triggers": [
        {
            "type": "rsi",
            "config": {"threshold": 30, "period": 14},
            "position": {"x": 100, "y": 50}  # UI 위치
        }
    ],
    "actions": [
        {
            "type": "market_buy",
            "config": {"amount_percent": 10},
            "position": {"x": 300, "y": 50}
        }
    ],
    "connections": [
        {"from": "trigger-0", "to": "action-0"}  # 연결 정보
    ]
}
```

### 5.2 저장/로드 플로우
```
UI 조작 → 내부 상태 업데이트 → ComponentStrategyManager → 데이터베이스
                                    ↓
데이터베이스 → ComponentStrategyManager → UI 상태 복원 → 화면 렌더링
```

---

## 6. 스타일링 및 테마

### 6.1 컴포넌트 색상 체계
```python
COMPONENT_COLORS = {
    'price': '#e74c3c',      # 빨강 (가격)
    'indicator': '#3498db',   # 파랑 (지표)  
    'time': '#f39c12',       # 주황 (시간)
    'volume': '#9b59b6',     # 보라 (거래량)
    'action': '#27ae60'      # 초록 (액션)
}
```

### 6.2 연결선 스타일
```python
class ConnectionLine(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(QColor('#95a5a6'), 2)  # 회색 연결선
        painter.setPen(pen)
        # 베지어 곡선으로 부드러운 연결선 그리기
```

---

## 7. 확장성 설계

### 7.1 플러그인 구조
```python
# 새 컴포넌트 추가 시
class NewCustomTrigger(BaseTrigger):
    def evaluate(self, market_data):
        # 사용자 정의 로직
        pass

# 자동 등록
TRIGGER_CLASSES['new_custom'] = NewCustomTrigger
```

### 7.2 템플릿 시스템
```python
# 사전 정의된 전략 템플릿
STRATEGY_TEMPLATES = {
    'rsi_reversal': {
        'name': 'RSI 반전 전략',
        'triggers': [{'type': 'rsi', 'config': {...}}],
        'actions': [{'type': 'market_buy', 'config': {...}}]
    }
}
```

---

## 8. 개발 가이드라인

### 8.1 컴포넌트 개발
1. **BaseTrigger/BaseAction 상속**
2. **evaluate() 메서드 구현**
3. **Config 클래스 정의** 
4. **메타데이터 등록**
5. **단위 테스트 작성**

### 8.2 UI 개발
1. **PyQt6 기반 구현**
2. **드래그&드롭 지원**
3. **실시간 설정 변경**
4. **시각적 피드백 제공**
5. **반응형 레이아웃**

### 8.3 테스트 전략
```python
# 컴포넌트 테스트
def test_rsi_trigger():
    trigger = RSITrigger(config={'threshold': 30})
    market_data = {'rsi': 25}
    assert trigger.evaluate(market_data) == True

# UI 테스트 (PyQt Test Framework)
def test_drag_drop():
    app = QApplication([])
    widget = StrategyMakerUI()
    # 드래그&드롭 시뮬레이션
```

---

## 9. 성능 최적화

### 9.1 렌더링 최적화
- **지연 로딩**: 보이는 컴포넌트만 렌더링
- **캐싱**: 반복 계산 결과 저장
- **배치 업데이트**: 여러 변경사항을 한 번에 처리

### 9.2 메모리 관리
- **약한 참조**: 순환 참조 방지
- **리소스 해제**: 컴포넌트 제거 시 정리
- **가비지 컬렉션**: 주기적 메모리 정리

---

## 📊 현재 구현 상태

### ✅ 완료
- [x] 아토믹 컴포넌트 시스템 (14 트리거 + 3 액션)
- [x] 전략 메이커 UI (드래그&드롭)
- [x] 태그 기반 포지션 관리
- [x] 컴포넌트 전략 매니저
- [x] 데이터베이스 모델 분리

### 🚧 진행 중
- [ ] 백테스팅 탭 구현
- [ ] 전략 분석 탭 구현  
- [ ] 템플릿 시스템 확장

### 📋 계획
- [ ] 조건 컴포넌트 추가
- [ ] 고급 트리거 확장
- [ ] 머신러닝 통합

---

**⚠️ 중요**: 이 가이드는 새로운 컴포넌트 기반 시스템을 위한 것입니다. 기존 고정 전략 시스템 관련 문서는 `docs/legacy_archive/`에서 확인하세요.
