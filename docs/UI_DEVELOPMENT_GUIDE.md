# UI 개발 가이드: 화면 구조 및 컴포넌트 설계

## 1. 기본 폴더 구조
```
upbit_auto_trading/
└── ui/
    └── desktop/
        ├── common/              # 공통 위젯, 스타일 등
        │   ├── widgets/        # 재사용 가능한 공통 위젯
        │   └── styles/         # 테마, 색상, 폰트 등 스타일 정의
        └── screens/            # 각 화면 모듈
            ├── dashboard/      # 대시보드 화면
            │   ├── components/ # 대시보드 전용 컴포넌트
            │   └── dashboard_screen.py
            ├── chart_view/     # 차트 뷰 화면
            │   ├── components/
            │   └── chart_view_screen.py
            └── ...
```

## 2. 화면 개발 구조

### 2.1 기본 구조
각 화면은 다음과 같은 구조로 개발합니다:

```
screens/화면명/
├── components/           # 화면 전용 컴포넌트
│   ├── component1.py    # 개별 컴포넌트
│   ├── component2.py
│   └── ...
└── 화면명_screen.py     # 메인 화면 클래스
```

### 2.2 파일 명명 규칙
- 메인 화면 파일: `스네이크_케이스_screen.py`
- 컴포넌트 파일: `스네이크_케이스.py`
- 클래스명: `파스칼케이스Screen` 또는 `파스칼케이스Widget`

## 3. 컴포넌트 기반 개발 방식

### 3.1 화면 분할 원칙
1. 화면을 논리적 단위로 분할
2. 각 단위를 독립적인 컴포넌트로 개발
3. 메인 화면에서 컴포넌트들을 조합

### 3.2 컴포넌트 설계 원칙
1. **단일 책임**: 각 컴포넌트는 하나의 명확한 역할만 수행
2. **독립성**: 다른 컴포넌트에 최소한의 의존성
3. **재사용성**: 필요시 다른 화면에서도 사용 가능하도록 설계
4. **통신**: 시그널/슬롯을 통한 명확한 인터페이스 정의

### 3.3 컴포넌트 구현 예시
```python
class SomeComponentWidget(QWidget):
    # 1. 시그널 정의
    value_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        # 2. 레이아웃 설정
        layout = QVBoxLayout(self)
        
        # 3. 자식 위젯 생성 및 설정
        self.setup_child_widgets()
        
        # 4. 이벤트 연결
        self.connect_events()
    
    def setup_child_widgets(self):
        """컴포넌트 내부 위젯 설정"""
        pass
    
    def connect_events(self):
        """이벤트 핸들러 연결"""
        pass
```

## 4. 화면-컴포넌트 간 통신

### 4.1 기본 통신 방식
1. 시그널/슬롯 메커니즘 사용
2. 컴포넌트는 상태 변경을 시그널로 알림
3. 부모 화면에서 시그널을 처리

### 4.2 구현 예시
```python
# 컴포넌트
class SetupWidget(QWidget):
    setup_changed = pyqtSignal(dict)  # 설정 변경 시그널

# 메인 화면
class MainScreen(QWidget):
    def __init__(self):
        self.setup = SetupWidget()
        self.setup.setup_changed.connect(self.on_setup_changed)
```

## 5. 장점

1. **구조화된 코드**
   - 명확한 폴더 구조
   - 컴포넌트별 책임 분리
   - 유지보수 용이

2. **재사용성**
   - 독립적인 컴포넌트
   - 다른 화면에서 재사용 가능

3. **확장성**
   - 새로운 컴포넌트 추가 용이
   - 기존 컴포넌트 수정 최소화

4. **테스트 용이성**
   - 컴포넌트 단위 테스트 가능
   - 독립적인 기능 검증 가능

## 6. 개발 순서

1. 화면 요구사항 분석
2. 컴포넌트 단위로 분할 설계
3. 개별 컴포넌트 구현
4. 메인 화면에서 컴포넌트 통합
5. 컴포넌트 간 통신 구현
6. 테스트 및 디버깅
