# Upbit Auto Trading - Copilot 지침

## ⚡ 필수 원칙
- **DB**: `.sqlite3` 확장자, `data/` 폴더 저장
- **테스트**: 변경 후 `python run_desktop_ui.py` 실행
- **구조**: 컴포넌트 기반 PyQt6 UI

## 📚 상세 가이드 (개발 전 필독)
- 프로젝트 명세: `.vscode/specs/`
- 아키텍처: `.vscode/guides/architecture.md`
- DB 설계: `.vscode/guides/database.md`
- UI 규칙: `.vscode/guides/ui-standards.md`
- 코딩 스타일: `.vscode/guides/coding-style.md`
if position_state == "waiting_entry":
    # 진입 전략만 활성화
    entry_signal = entry_strategy.generate_signal()
    if entry_signal in ['BUY', 'SELL']:
        position_state = "position_management"
        
elif position_state == "position_management":
    # 관리 전략들만 활성화
    for mgmt_strategy in management_strategies:
        signal = mgmt_strategy.generate_signal()
        if signal == 'CLOSE_POSITION':
            position_state = "waiting_entry"
```

## 🎨 UI 개발 지침

### 필수 컴포넌트 사용
```python
# 항상 이 컴포넌트들을 사용
from upbit_auto_trading.ui.desktop.common.components import (
    PrimaryButton,      # 주요 동작 (파란색)
    SecondaryButton,    # 보조 동작 (회색)
    DangerButton,       # 위험 동작 (빨간색)
    StyledLineEdit,     # 입력 필드
    StyledComboBox,     # 드롭다운
    StyledDialog        # 다이얼로그
)
```

### 3탭 전략 관리 구조
1. **📈 진입 전략 탭**: 6개 진입 전략 관리 (이평교차, RSI, 볼밴드, 변동성돌파, MACD, 스토캐스틱)
2. **🛡️ 관리 전략 탭**: 6개 관리 전략 관리 (물타기, 불타기, 트레일링스탑, 고정익절손절, 부분청산, 시간청산)
3. **🔗 전략 조합 탭**: 진입+관리 전략 조합 생성

### 레이아웃 원칙
- QVBoxLayout, QHBoxLayout 기반 구조적 레이아웃
- 스트레치 팩터를 활용한 반응형 디자인
- 컴포넌트별 명확한 역할 분리
- 그룹박스(QGroupBox)를 활용한 논리적 영역 구분

## 🔧 기술 스택별 가이드

### PyQt6 패턴
```python
class MyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """UI 구성 요소 초기화"""
        layout = QVBoxLayout(self)
        
        # 그룹박스로 논리적 영역 구분
        group = QGroupBox("설정")
        group_layout = QVBoxLayout(group)
        
        # 스타일된 컴포넌트 사용
        self.input_field = StyledLineEdit(placeholder="힌트 텍스트")
        self.submit_btn = PrimaryButton("확인")
        
        group_layout.addWidget(self.input_field)
        group_layout.addWidget(self.submit_btn)
        layout.addWidget(group)
        
    def connect_signals(self):
        """시그널과 슬롯 연결"""
        self.submit_btn.clicked.connect(self.on_submit)
        
    def on_submit(self):
        """제출 버튼 클릭 처리"""
        try:
            value = self.input_field.text()
            # 비즈니스 로직 처리
        except Exception as e:
            logging.error(f"제출 처리 중 오류: {e}")
```

### 데이터 관리
- SQLite 기반 로컬 데이터베이스
- 업비트 API 연동시 rate limiting 고려
- 웹소켓을 통한 실시간 데이터 처리

### 🗄️ 데이터베이스 개발 원칙

#### **확장자 및 위치 표준**
```bash
# ✅ 올바른 DB 파일 구조 (필수 준수)
data/
├── app_settings.sqlite3      # 프로그램 설정 DB
└── market_data.sqlite3       # 백테스팅용 시장 데이터 DB

# ❌ 금지사항
- 루트 폴더의 .db 파일들
- 확장자 없는 DB 파일들
- 서로 다른 폴더의 DB 파일들
- .db 확장자 사용 (반드시 .sqlite3 사용)
```

#### **DB 연결 표준 패턴**
```python
# ✅ 모든 DB 클래스는 이 패턴을 따라야 함

# 프로그램 설정 관련 클래스들
class ConditionStorage:
    def __init__(self, db_path: str = "data/app_settings.sqlite3"):
        self.db_path = db_path

class StrategyStorage:
    def __init__(self, db_path: str = "data/app_settings.sqlite3"):
        self.db_path = db_path

# 시장 데이터 관련 클래스들
class MarketDataProvider:
    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        self.db_path = db_path

class BacktestEngine:
    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        self.db_path = db_path
```

#### **DB 파일 목적별 분리**
```python
# app_settings.sqlite3 (프로그램 설정)
TABLES = [
    "trading_conditions",    # 매매 조건
    "component_strategy",    # 전략 정보  
    "strategy_components",   # 전략 구성요소
    "strategy_execution",    # 전략 실행 기록
    "system_settings",       # 시스템 설정
    "user_preferences"       # 사용자 설정
]

# market_data.sqlite3 (백테스팅 데이터)
TABLES = [
    "candle_data",          # 캔들 데이터
    "ticker_data",          # 가격 정보
    "orderbook_data",       # 호가 데이터
    "trade_history"         # 거래 이력
]
```

### 아키텍처 패턴
- MVC/MVP 패턴 준수
- 컴포넌트 기반 모듈화
- 의존성 주입 원칙 적용
- 진입/관리 전략의 명확한 책임 분리

## 🚨 중요 고려사항

### 보안
- API 키 하드코딩 금지
- 환경변수 또는 설정 파일 활용
- 민감한 데이터 로깅 방지

### 성능
- UI 스레드 블로킹 방지
- 메모리 누수 주의
- 리소스 정리 (close, deleteLater) 필수
- 백테스팅: 1년치 분봉 5분 내 완료 목표

### 테스트
- 단위 테스트 작성 권장
- Mock 객체를 활용한 격리 테스트
- UI 테스트는 QTest 프레임워크 활용
- 전략 조합 상태 전환 테스트 필수

## 🎨 UI 디자인 패턴 상세

### 색상 시스템
- 주요 색상: #1E88E5 (파란색)
- 성공: #4CAF50 (녹색)  
- 경고: #FF9800 (주황색)
- 위험: #F44336 (빨간색)
- 배경: #FAFAFA (연회색)

### 다이얼로그 패턴
```python
from upbit_auto_trading.ui.desktop.common.components import StyledDialog

class StrategyConfigDialog(StyledDialog):
    def __init__(self, parent=None):
        super().__init__(parent, "전략 설정")
        self.setup_ui()
        
    def setup_ui(self):
        """전략별 파라미터 설정 UI"""
        # project-specs.md의 전략 파라미터 명세 참조
        pass
```

## 💡 전략 구현 패턴

### 진입 전략 기본 구조
```python
from abc import ABC, abstractmethod

class EntryStrategy(ABC):
    """모든 진입 전략의 기본 클래스"""
    
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> str:
        """진입 신호 생성: 'BUY', 'SELL', 'HOLD'"""
        pass
        
    @abstractmethod
    def get_parameters(self) -> Dict:
        """전략 파라미터 반환"""
        pass

class RSIEntryStrategy(EntryStrategy):
    def __init__(self, period=14, oversold=30, overbought=70):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        
    def generate_signal(self, data: pd.DataFrame) -> str:
        """RSI 기반 진입 신호"""
        # project-specs.md의 RSI 전략 명세 따름
        pass
```

### 관리 전략 기본 구조
```python
class ManagementStrategy(ABC):
    """모든 관리 전략의 기본 클래스"""
    
    @abstractmethod
    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> str:
        """관리 신호 생성: 'ADD_BUY', 'ADD_SELL', 'CLOSE_POSITION', 'UPDATE_STOP', 'HOLD'"""
        pass

class TrailingStopStrategy(ManagementStrategy):
    def __init__(self, trail_distance=0.05, activation_profit=0.02):
        self.trail_distance = trail_distance  # 5% 추적 거리
        self.activation_profit = activation_profit  # 2% 수익 시 활성화
        
    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> str:
        """트레일링 스탑 신호"""
        # project-specs.md의 트레일링 스탑 명세 따름
        pass
```

## 📊 데이터 바인딩 패턴

### 상태 기반 백테스팅
```python
class StatefulBacktester:
    def __init__(self):
        self.state = BacktestState.WAITING_ENTRY
        self.position = None
        self.entry_strategy = None
        self.management_strategies = []
        
    def run_backtest(self, data: pd.DataFrame):
        """상태 기반 백테스팅 실행"""
        for timestamp, row in data.iterrows():
            if self.state == BacktestState.WAITING_ENTRY:
                self._process_entry_signals(row)
            elif self.state == BacktestState.POSITION_MANAGEMENT:
                self._process_management_signals(row)
```

## 📝 코딩 컨벤션

### 네이밍
- 클래스: PascalCase (예: `StrategyMaker`)
- 함수/변수: snake_case (예: `create_ui_components`)
- 상수: UPPER_SNAKE_CASE (예: `MAX_RETRY_COUNT`)
- 프라이빗 멤버: 언더스코어 접두사 (예: `_internal_method`)

### 문서화
- 모든 퍼블릭 메서드에 독스트링 작성
- 복잡한 로직에는 인라인 주석 추가
- 전략 관련 코드는 project-specs.md 참조 명시

## 🔄 개발 워크플로

### 스펙 기반 개발 원칙
1. **요구사항 우선**: project-specs.md의 비즈니스 로직 확인
2. **일관성 유지**: 기존 컴포넌트 재사용 우선
3. **단계적 구현**: 진입 전략 → 관리 전략 → 조합 순서
4. **지속적 검증**: 각 단계마다 백테스팅으로 검증

### 개발 시 필수 체크리스트
- [ ] project-specs.md의 해당 섹션 확인
- [ ] 기존 공통 컴포넌트 재사용 여부
- [ ] 전략 역할(진입/관리) 명확히 구분
- [ ] 상태 전환 로직 정확성
- [ ] 한국어 주석 및 사용자 친화적 메시지
- [ ] 예외 처리 및 로깅 포함

## 💡 추가 권장사항
- 코드 작성 전 항상 project-specs.md의 관련 섹션 검토
- 새로운 기능 추가시 기존 아키텍처와의 일관성 고려
- 성능 최적화보다는 가독성과 유지보수성 우선
- 전략 시스템의 진입/관리 역할 분리 원칙 준수

---

**🎯 핵심 원칙**: 이 지침들을 따라 `.vscode/project-specs.md`에 정의된 명세를 기반으로 일관되고 고품질의 코드를 작성해 주세요! 🚀

## 🚨 중요 고려사항

### 보안
- API 키 하드코딩 금지
- 환경변수 또는 안전한 저장소 활용
- 민감한 정보 로깅 금지

### 성능
- UI 업데이트는 메인 스레드에서만
- 무거운 작업은 백그라운드 스레드 활용
- 메모리 누수 방지를 위한 적절한 리소스 해제

### 사용자 경험
- 사용자 친화적인 에러 메시지
- 진행 상황 표시 (프로그레스 바 등)
- 반응성 있는 UI (블로킹 방지)

## 📝 코딩 컨벤션

### 네이밍
- 클래스: PascalCase (예: `StrategyMaker`)
- 함수/변수: snake_case (예: `create_ui_components`)
- 상수: UPPER_SNAKE_CASE (예: `MAX_RETRY_COUNT`)
- 프라이빗 멤버: 언더스코어 접두사 (예: `_internal_method`)

### 문서화
- 모든 퍼블릭 메서드에 독스트링 작성
- 복잡한 로직에는 인라인 주석 추가
- README.md 파일 지속적 업데이트

## 🧪 테스트 지침
- 유닛 테스트 우선 작성
- GUI 테스트는 별도 테스트 파일로 분리
- Mock 객체를 활용한 외부 의존성 제거
- 테스트 커버리지 80% 이상 유지

## 🔄 안전한 개발 워크플로우

### 복잡한 기능 개발 시 격리 환경 구성
```bash
# 1. 현재 상태 Git 커밋/푸시 (복구 지점)
git add -A; git commit -m "feat: 복구 지점 - [기능명] 개발 시작 전"; git push

# 2. 개발용 격리 폴더 생성
mkdir -p dev_workspace/[기능명]_dev
cd dev_workspace/[기능명]_dev

# 3. 필요한 파일만 복사하여 독립 개발
cp ../../원본파일.py ./
```

### 개발 완료 후 통합 및 정리
```bash
# 1. 개발 완료된 코드를 원래 위치로 이동
cp 완성된파일.py ../../upbit_auto_trading/target_location/

# 2. 테스트/분석 스크립트 정리 
# - check_*.py, analyze_*.py, test_*.py 등을 scripts/ 폴더로 이동
# - 또는 완전 삭제 (Git 히스토리에 남아있음)

# 3. 최종 커밋
git add -A; git commit -m "feat: [기능명] 완성 및 코드 정리"; git push
```

### PowerShell 스크립트 실행 오류 방지
```python
# Python 스크립트 헤더에 항상 포함
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
스크립트 설명
"""
import sys
import os
sys.path.append('.')  # 프로젝트 루트 추가

if __name__ == "__main__":
    # 메인 로직
    pass
```

## 🧹 코드 정리 지침

### 정리 대상 파일 패턴
- `check_*.py` - 상태 확인 스크립트
- `analyze_*.py` - 분석 스크립트  
- `test_*.py` - 임시 테스트 스크립트
- `debug_*.py` - 디버깅 스크립트
- `simple_*.py` - 간단 테스트
- `migration_*.py` - 일회성 마이그레이션

### 정리 방법
1. **보관**: 유용한 스크립트는 `scripts/utility/` 폴더로 이동
2. **삭제**: 일회성/오류 스크립트는 완전 삭제
3. **통합**: 비슷한 기능은 하나로 통합

### 자동 정리 스크립트 실행
```bash
# 정리 스크립트 생성 후 실행
python scripts/cleanup_project.py
```

## 🔄 Git 워크플로우
- 기능별 브랜치 생성 권장
- 복잡한 기능 개발 전 반드시 복구 지점 커밋
- 개발용 격리 폴더 활용으로 기존 코드 보호
- 완성 후 즉시 코드 정리 및 통합
- 커밋 메시지는 영어 또는 한국어 일관성 유지

## 💡 추가 권장사항
- 코드 작성 전 항상 기존 컴포넌트 재사용 가능성 검토
- 새로운 기능 추가시 기존 아키텍처와의 일관성 고려
- 성능 최적화보다는 가독성과 유지보수성 우선
- 개발 완료 후 반드시 불필요한 파일 정리
- PowerShell 스크립트 실행 오류 방지를 위한 표준 헤더 사용

---

이 지침들을 따라 안전하고 깔끔한 개발을 진행해 주세요! 🚀
