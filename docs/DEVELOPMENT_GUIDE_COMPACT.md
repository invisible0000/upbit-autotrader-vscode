# 🛠️ 개발 가이드 (간결판)

## 📋 개요

업비트 자동매매 시스템 개발을 위한 **핵심 가이드라인**입니다. 빠른 시작과 일관된 개발을 위해 필수 사항만 정리했습니다.

## 🚀 빠른 시작

### 환경 설정
```powershell
# 1. 저장소 클론
git clone https://github.com/invisible0000/upbit-autotrader-vscode.git
cd upbit-autotrader-vscode

# 2. 파이썬 가상환경 (Windows)
python -m venv venv
venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 실행 테스트
python run_desktop_ui.py
```

### 프로젝트 구조
```
upbit_auto_trading/
├── 📁 core/              # 핵심 유틸리티
├── 📁 ui/desktop/        # PyQt6 GUI
├── 📁 business_logic/    # 비즈니스 로직
├── 📁 data_layer/        # 데이터베이스
└── 📁 logging/           # 로깅 시스템

data/                     # DB 파일 위치
├── settings.sqlite3      # 구조 정의
├── strategies.sqlite3    # 전략 인스턴스
└── market_data.sqlite3   # 시장 데이터

data_info/               # DB 스키마 관리
├── *.sql               # 테이블 스키마
└── *.yaml              # 변수 정의
```

## 🎯 개발 원칙

### 코딩 표준
- **PEP 8 준수**: 79자 제한, 타입 힌트 필수
- **함수 크기**: 20줄 이하, 단일 책임
- **네이밍**: 축약어 금지, 명확한 의미
- **테스트**: 신규 기능은 단위테스트 필수

### 아키텍처 원칙
- **컴포넌트 기반**: 재사용 가능한 모듈 설계
- **계층 분리**: UI → 비즈니스 → 데이터
- **의존성 주입**: 테스트 가능한 구조
- **에러 투명성**: 폴백 코드로 문제 숨기지 않음

## 🗄️ 데이터베이스 개발

### 3-DB 아키텍처
```python
# 1. settings.sqlite3 - 구조 정의
{
    "tv_trading_variables": "변수 정의",
    "tv_variable_parameters": "파라미터 스키마", 
    "tv_indicator_categories": "카테고리 분류",
    "cfg_app_settings": "앱 설정"
}

# 2. strategies.sqlite3 - 전략 인스턴스
{
    "strategies": "사용자 전략",
    "strategy_conditions": "조건 조합",
    "backtest_results": "백테스팅 결과"
}

# 3. market_data.sqlite3 - 시장 데이터
{
    "price_data": "가격 데이터",
    "indicator_cache": "지표 캐시",
    "market_info": "시장 정보"
}
```

### DB 관리 방식
- **스키마 정의**: `data_info/*.sql` 파일
- **변수 정의**: `data_info/*.yaml` 파일
- **실제 DB**: `data/*.sqlite3` 파일

### DB 연결 예시
```python
from upbit_auto_trading.data_layer.database_manager import DatabaseManager

# 표준 DB 연결
db = DatabaseManager()
db.get_connection("settings")    # settings.sqlite3
db.get_connection("strategies")  # strategies.sqlite3
db.get_connection("market_data") # market_data.sqlite3
```

## 🎨 UI 개발 (PyQt6)

### 메인 화면 구조
```python
# 탭 구성
tabs = {
    "market_analysis": "📊 시장 분석",
    "strategy_management": "⚙️ 전략 관리", 
    "settings": "🔧 설정"
}

# 전략 관리 하위 탭
strategy_tabs = {
    "trigger_builder": "트리거 빌더",
    "strategy_maker": "전략 메이커",
    "backtesting": "백테스팅"
}
```

### 컴포넌트 패턴
```python
# 시그널/슬롯 통신
class MyWidget(QWidget):
    data_changed = pyqtSignal(dict)  # 시그널 정의
    
    def __init__(self):
        super().__init__()
        self.data_changed.connect(self.on_data_changed)  # 슬롯 연결
    
    def on_data_changed(self, data):
        # 데이터 변경 처리
        pass
```

## 📈 전략 개발

### 진입 전략 개발
```python
from upbit_auto_trading.strategies.base import EntryStrategy

class MyEntryStrategy(EntryStrategy):
    def __init__(self, **params):
        super().__init__()
        self.params = params
    
    def generate_signal(self, data):
        # 진입 신호 로직
        if self.condition_met(data):
            return "BUY"  # or "SELL", "HOLD"
        return "HOLD"
    
    def validate_params(self):
        # 파라미터 검증
        required = ["period", "threshold"]
        return all(param in self.params for param in required)
```

### 관리 전략 개발
```python
from upbit_auto_trading.strategies.base import ManagementStrategy

class MyManagementStrategy(ManagementStrategy):
    def manage_position(self, position, market_data):
        current_profit = position.calculate_profit(market_data.current_price)
        
        if current_profit >= self.params["take_profit"]:
            return "CLOSE_POSITION"
        elif current_profit <= -self.params["stop_loss"]:
            return "CLOSE_POSITION"
        
        return "HOLD"
```

## 🧪 테스트 개발

### 단위 테스트 패턴
```python
import pytest
from unittest.mock import Mock, patch

class TestMyStrategy:
    def test_generate_signal_buy(self):
        strategy = MyEntryStrategy(period=14, threshold=0.7)
        mock_data = Mock()
        mock_data.rsi = 25  # 과매도 상태
        
        signal = strategy.generate_signal(mock_data)
        assert signal == "BUY"
    
    def test_parameter_validation(self):
        strategy = MyEntryStrategy(period=14)  # threshold 누락
        assert not strategy.validate_params()
```

### 백테스팅 테스트
```python
def test_strategy_backtest():
    strategy = create_test_strategy()
    data = load_test_data("KRW-BTC", "2023-01-01", "2023-12-31")
    
    results = run_backtest(strategy, data)
    
    assert results.total_return > 0
    assert results.max_drawdown < 0.2  # 20% 이하
    assert results.sharpe_ratio > 1.0
```

## 🔧 로깅 시스템

### 환경변수 설정
```powershell
# 로그 컨텍스트 (컴포넌트별 필터링)
$env:UPBIT_LOG_CONTEXT = "strategy_maker,trigger_builder"

# 로그 스코프 (레벨별 필터링)  
$env:UPBIT_LOG_SCOPE = "debug,performance,error"
```

### 로깅 사용법
```python
from upbit_auto_trading.logging import get_logger

logger = get_logger("MyComponent")

# 다양한 로그 레벨
logger.debug("🔍 디버그 정보")
logger.info("ℹ️ 일반 정보") 
logger.warning("⚠️ 경고 메시지")
logger.error("❌ 오류 발생")
logger.performance("⚡ 성능 측정: 0.5초")
```

## 🚀 배포 및 실행

### 개발 모드 실행
```powershell
# GUI 모드
python run_desktop_ui.py

# 디버그 모드
$env:UPBIT_DEBUG = "true"
python run_desktop_ui.py
```

### 테스트 실행
```powershell
# 전체 테스트
pytest

# 특정 테스트
pytest tests/test_strategies.py -v

# 커버리지 포함
pytest --cov=upbit_auto_trading
```

## 🔒 보안 가이드

### API 키 관리
```python
import os
from upbit_auto_trading.core.config import get_api_keys

# ✅ 올바른 방식 - 환경변수 사용
api_keys = get_api_keys()
access_key = api_keys.get("access_key")

# ❌ 잘못된 방식 - 하드코딩 절대 금지
# access_key = "your_access_key_here"  # 절대 이렇게 하지 마세요!
```

### 민감 정보 로깅 방지
```python
# 자동 마스킹 기능
logger.info(f"API 호출: access_key={access_key}")  
# 출력: "API 호출: access_key=****ed3f"
```

## 📚 추가 리소스

### 핵심 문서
- [프로젝트 명세서](PROJECT_SPECIFICATIONS.md)
- [아키텍처 개요](ARCHITECTURE_OVERVIEW.md)
- [전략 명세서](STRATEGY_SPECIFICATIONS.md)
- [DB 스키마](DB_SCHEMA.md)

### 문제 해결
- [GitHub Clone 문제해결](GITHUB_CLONE_TROUBLESHOOTING.md)
- [기여 가이드](CONTRIBUTING.md)

---
**💡 팁**: 개발 중 문제가 발생하면 먼저 로그를 확인하고, 관련 테스트를 실행해보세요!
