# UI 개발 가이드: 화면 구조 및 컴포넌트 설계

## 📋 최신 업데이트: 매매 전략 관리 V1.0.1 개선사항

### 🎯 주요 변경사항 (2025.01.21)
- **조합 전략 지원**: 이산 조합 및 웨이팅 조합 전략 추가 (최대 4개 전략 제한)
- **고급 전략 유형**: 물타기, 불타기, 트레일링 스탑, 평균가 에버리징, 그리드 매매, RSI 다이버전스 추가
- **탭 기반 UI**: 기본 전략과 조합 전략을 별도 탭으로 분리
- **UI 중복 제거**: 상단 툴바 정리로 공간 효율화
- **개발 방침 확정**: 디폴트 파라미터 제공, AI 친화적 구조 유지

### 🔗 관련 문서
- **개발 태스크**: `docs/STRATEGY_MANAGEMENT_V1.0.1_TASKS.md`
- **요구사항**: `.kiro/specs/upbit-auto-trading/requirements.md`

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
            ├── strategy_management/  # 매매 전략 관리 (V1.0.1 개선)
            │   ├── components/
            │   │   ├── strategy_list.py
            │   │   ├── strategy_editor.py
            │   │   ├── strategy_details.py
            │   │   ├── composite_strategy_tab.py     # 🆕 조합 전략 탭
            │   │   └── advanced_strategy_forms.py   # 🆕 고급 전략 폼
            │   └── strategy_management_screen.py
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

## 4. 한글 지원 및 폰트 설정

### 4.1 시스템 요구사항
- Windows 시스템에서 한글 폰트 지원
- matplotlib 3.5.0 이상 (차트 한글 표시용)
- 권장 한글 폰트: Malgun Gothic, Gulim, Dotum

### 4.2 matplotlib 한글 폰트 설정
```python
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 설정 (여러 옵션 시도)
korean_fonts = ['Malgun Gothic', 'Arial Unicode MS', 'Gulim', 'Dotum', 'Batang']
available_fonts = [f.name for f in fm.fontManager.ttflist]

for font in korean_fonts:
    if font in available_fonts:
        plt.rcParams['font.family'] = [font, 'DejaVu Sans']
        break
else:
    # 한글 폰트가 없으면 기본 설정
    plt.rcParams['font.family'] = ['DejaVu Sans']

plt.rcParams['axes.unicode_minus'] = False
```

### 4.3 PyQt6 한글 지원
- 기본적으로 시스템 기본 폰트 사용
- 필요시 명시적 폰트 설정 가능

## 5. 백테스팅 시스템 개발 현황

### 5.1 완료된 기능
- ✅ 기본 백테스팅 엔진
- ✅ DB 선택 UI 
- ✅ 차트 시각화 (한글 지원)
- ✅ 거래 기록 테이블
- ✅ 수익률 계산
- ✅ 거래 기록 ↔ 차트 링크 기능
- ✅ 자동 차트 리사이징 (tight_layout)

### 5.2 매매 전략 관리 V1.0.1 개발 계획

#### 현재 상태 분석
**기존 구조 (4개 기본 전략):**
- **이동평균 교차**: 단기/장기 이평선의 골든크로스/데드크로스 
- **RSI**: 과매수(70)/과매도(30) 기준의 역추세 매매
- **볼린저 밴드**: 상/하단 밴드 터치 시 반전 매매 또는 돌파 매매
- **변동성 돌파**: 래리 윌리엄스 방식의 변동성 기반 돌파 매매
- 3분할 UI: 전략목록(30%) - 에디터(40%) - 상세정보(30%)
- 상단 툴바 중복 버튼 문제

#### 개선 목표
1. **조합 전략 지원**: 여러 전략을 결합하여 새로운 신호 생성 (최대 4개 제한)
2. **고급 전략 추가**: 10개 전략 유형으로 확장 (디폴트 파라미터 제공)
3. **탭 기반 분리**: 기본 전략 vs 조합 전략 별도 관리
4. **UI 최적화**: 중복 제거 및 공간 효율화
5. **백테스팅 개선**: DB 선택 및 기간 설정 기능 추가

#### 새로운 전략 유형 상세 설계

**물타기 전략 (Dollar Cost Averaging Down):**
```python
parameters = {
    "initial_investment_ratio": 0.3,        # 초기 투자 비율 [디폴트]
    "additional_buy_count": 3,              # 추가 매수 횟수 [디폴트]
    "price_drop_threshold": [-5, -10, -15], # 하락률 기준점 (%) [디폴트]
    "additional_investment_ratios": [0.2, 0.25, 0.25], # 추가 투자 비율 [디폴트]
    "profit_target": 10.0,                  # 목표 수익률 (%) [사용자 조정 가능]
    "stop_loss": -30.0,                     # 절대 손절선 (%) [사용자 조정 가능]
    "max_holding_days": 30,                 # 최대 보유 기간 [사용자 조정 가능]
    "enable_partial_sell": True,            # 부분 매도 허용 [디폴트]
    "partial_sell_ratios": [0.3, 0.3, 0.4] # 부분 매도 비율 [디폴트]
}
```

**불타기 전략 (Pyramid Trading):**
```python
parameters = {
    "initial_investment_ratio": 0.4,        # 초기 투자 비율 [디폴트]
    "additional_buy_count": 2,              # 추가 매수 횟수 [디폴트]  
    "price_rise_threshold": [3, 7],         # 상승률 기준점 (%) [디폴트]
    "additional_investment_ratios": [0.3, 0.3], # 추가 투자 비율 [디폴트]
    "profit_target_levels": [15, 25, 35],   # 단계별 익절 목표 (%) [사용자 조정 가능]
    "partial_sell_ratios": [0.4, 0.3, 0.3], # 단계별 매도 비율 [디폴트]
    "trailing_stop_distance": 5.0,         # 트레일링 스탑 거리 (%) [사용자 조정 가능]
    "max_position_size": 1.0,               # 최대 포지션 크기 [디폴트]
    "enable_dynamic_targets": True          # 동적 목표가 조정 [디폴트]
}
```

#### 조합 전략 구조

**조합 전략 제약사항 (확정):**
- 최대 4개 전략까지만 조합 허용 (코드 안정성 우선)
- 기본 전략 유형(10개)만 조합 가능 (조합끼리 재조합 불가)
- UI에서 제약사항 명시적 표시 및 검증

**이산 조합 (Discrete Combination):**
- AND: 모든 전략이 같은 신호
- OR: 하나라도 강한 신호 발생
- MAJORITY: 과반수 이상 동의

**웨이팅 조합 (Weighted Combination):**
- 각 전략별 가중치 설정 (총합 1.0)
- 가중 평균으로 최종 신호 계산
- 임계값 기반 신호 발생

#### 개발 우선순위 (확정된 방침)
1. **Phase 1** (3-4일): UI 기본 정리 및 전략 유형 확장 (디폴트 파라미터 적용)
2. **Phase 2** (4-5일): 탭 기반 UI 구조 변경 (4개 제한 UI 반영)
3. **Phase 3** (5-6일): 조합 전략 백엔드 구현 (AI 친화적 구조)
4. **Phase 4** (2-3일): 백테스팅 통합 (DB/기간 선택 추가)

**개발 방침:**
- 파라미터 최적화: 디폴트 값 제공, 백테스팅으로 수동 조정
- 조합 전략: 최대 4개 제한으로 복잡도 관리
- 실시간 실행: LLM 모델 감당 가능한 코드 구조 유지

### 5.3 기술적 고려사항

#### 성능 최적화
- 조합 신호 계산 시 개별 전략 신호 캐싱
- 백테스트 병렬화로 처리 속도 향상 (4개 제한 활용)
- 대용량 시계열 데이터 메모리 효율 관리

#### 확장성 설계
- 플러그인 아키텍처로 새 전략 유형 쉽게 추가 (AI 친화적)
- JSON/YAML 기반 설정 외부화 (디폴트 파라미터 관리)
- 향후 웹 인터페이스 연동 고려

#### 사용자 경험
- 실시간 미리보기: 조합 설정 변경 시 즉시 결과 표시
- 드래그&드롭: 직관적인 전략 조합 인터페이스 (4개 제한 표시)
- 시각적 피드백: 조합 로직 그래프 표현
- 백테스팅 개선: DB 선택 및 기간 설정 기능
- 🔄 실제 DB 연동
- 🔄 매매전략 적용
- ⏳ 포트폴리오 백테스팅 (계획)

## 6. 컴포넌트 기반 개발 방식

### 6.1 화면 분할 원칙
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
