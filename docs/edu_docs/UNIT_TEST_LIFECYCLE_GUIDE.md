# 🧪 유닛 테스트 생명주기 완전 가이드

> **대상**: 주니어 개발자, 신입 개발자  
> **목적**: 유닛 테스트의 전체 생명주기 이해와 실무 적용  
> **갱신**: 2025-08-03

## 📋 목차
- [1. 유닛 테스트란 무엇인가?](#1-유닛-테스트란-무엇인가)
- [2. 테스트 생명주기 개요](#2-테스트-생명주기-개요)
- [3. 개발 단계별 테스트 전략](#3-개발-단계별-테스트-전략)
- [4. 테스트 유지보수 전략](#4-테스트-유지보수-전략)
- [5. CI/CD 통합](#5-cicd-통합)
- [6. 실무 팁과 베스트 프랙티스](#6-실무-팁과-베스트-프랙티스)

---

## 1. 유닛 테스트란 무엇인가?

### 🎯 유닛 테스트의 정의
- **개별 함수나 클래스**를 독립적으로 테스트하는 자동화된 테스트
- **빠른 실행 속도** (1개당 1ms 이하)
- **외부 의존성 없음** (DB, 네트워크, 파일 시스템 제외)

### 💡 왜 유닛 테스트가 중요한가?

#### ✅ 개발 중 이점
```python
# 예시: 함수 작성 후 즉시 검증
def calculate_profit_rate(buy_price, sell_price):
    return (sell_price - buy_price) / buy_price * 100

def test_calculate_profit_rate():
    # 즉시 검증 가능
    assert calculate_profit_rate(100, 110) == 10.0
    assert calculate_profit_rate(100, 90) == -10.0
```

#### ✅ 장기적 이점
- **리팩토링 안전성**: 코드 변경 시 기존 기능 보장
- **문서화 효과**: 테스트가 코드 사용법 설명
- **버그 조기 발견**: 개발 중 문제 즉시 확인
- **협업 효율성**: 다른 개발자가 변경 시 영향 파악

---

## 2. 테스트 생명주기 개요

### 📊 전체 생명주기 흐름
```
개발 시작 → 개발 중 → 개발 완료 → 운영 → 유지보수 → 레거시
    ↓         ↓        ↓       ↓       ↓         ↓
   TDD      지속검증   완성도확인  회귀방지   리팩토링   아카이브
```

### 🔄 단계별 테스트 역할

| 단계 | 테스트 역할 | 주요 활동 | 예상 기간 |
|------|-------------|-----------|-----------|
| **개발 중** | 🚧 개발 가이드 | TDD, 즉시 피드백 | 2-4주 |
| **개발 완료** | ✅ 품질 보증 | 완성도 검증, 문서화 | 1-2주 |
| **운영** | 🛡️ 회귀 방지 | CI/CD 자동 검증 | 6개월-2년 |
| **유지보수** | 🔧 변경 지원 | 리팩토링 안전망 | 1-3년 |
| **레거시** | 📚 지식 보존 | 아카이브, 참조용 | 영구 보관 |

---

## 3. 개발 단계별 테스트 전략

### 🚧 Phase 1: 개발 중 (Development Phase)

#### TDD (Test-Driven Development) 적용
```python
# Step 1: 실패하는 테스트 작성
def test_rsi_calculation():
    # 아직 구현 안된 함수를 위한 테스트
    data = [100, 102, 101, 103, 105]
    result = calculate_rsi(data, period=4)
    assert 50 < result < 80  # RSI 예상 범위

# Step 2: 최소한의 구현
def calculate_rsi(data, period):
    # TODO: 실제 RSI 계산 로직 구현
    return 60  # 임시 반환

# Step 3: 테스트 통과 후 리팩토링
def calculate_rsi(data, period):
    # 실제 RSI 계산 로직
    gains = []
    losses = []
    # ... 구현 ...
    return rsi_value
```

#### 개발 중 테스트 관리 원칙
- **매일 실행**: `pytest` 또는 `python -m unittest`
- **빠른 피드백**: 전체 테스트 10초 이내 완료
- **커밋 전 검증**: Git hook으로 자동 실행

### ✅ Phase 2: 개발 완료 (Completion Phase)

#### 완성도 검증 체크리스트
```python
# 1. 경계값 테스트
def test_rsi_boundary_cases():
    # 최소 데이터
    assert calculate_rsi([100], 1) is not None
    # 모든 상승
    assert calculate_rsi([100, 101, 102, 103], 3) == 100
    # 모든 하락
    assert calculate_rsi([103, 102, 101, 100], 3) == 0

# 2. 예외 상황 테스트
def test_rsi_error_cases():
    with pytest.raises(ValueError):
        calculate_rsi([], 14)  # 빈 데이터
    with pytest.raises(ValueError):
        calculate_rsi([100, 101], -1)  # 음수 기간

# 3. 성능 테스트
def test_rsi_performance():
    large_data = list(range(10000))
    start_time = time.time()
    calculate_rsi(large_data, 14)
    execution_time = time.time() - start_time
    assert execution_time < 0.1  # 100ms 이내
```

#### 문서화로서의 테스트
```python
def test_rsi_usage_examples():
    """RSI 함수 사용법을 보여주는 테스트"""
    
    # 일반적인 사용 사례
    daily_prices = [100, 102, 101, 103, 105, 104, 106]
    rsi_14 = calculate_rsi(daily_prices, period=14)
    assert isinstance(rsi_14, float)
    
    # 과매수 구간 (70 이상)
    uptrend_prices = [100, 101, 102, 103, 104, 105, 106, 107]
    rsi_high = calculate_rsi(uptrend_prices, period=4)
    assert rsi_high > 70, "상승장에서는 RSI가 70 이상이어야 함"
    
    # 과매도 구간 (30 이하)
    downtrend_prices = [100, 99, 98, 97, 96, 95, 94, 93]
    rsi_low = calculate_rsi(downtrend_prices, period=4)
    assert rsi_low < 30, "하락장에서는 RSI가 30 이하여야 함"
```

### 🛡️ Phase 3: 운영 (Production Phase)

#### CI/CD 자동 실행
```yaml
# .github/workflows/test.yml
name: Unit Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run unit tests
      run: |
        pytest tests/ --cov=upbit_auto_trading
        coverage report --fail-under=80
```

#### 모니터링과 알림
```python
# pytest-html 리포트 생성
pytest tests/ --html=reports/test_report.html --self-contained-html

# Slack 알림 (실패 시)
if test_result.failed:
    send_slack_notification(
        "🚨 유닛 테스트 실패",
        f"실패한 테스트: {test_result.failed_count}개"
    )
```

### 🔧 Phase 4: 유지보수 (Maintenance Phase)

#### 리팩토링 시 테스트 활용
```python
# Before: 리팩토링 전 기존 구현
def old_calculate_profit(buy_price, sell_price, quantity):
    profit = (sell_price - buy_price) * quantity
    return profit

# 기존 동작을 보장하는 테스트
def test_profit_calculation_behavior():
    assert old_calculate_profit(100, 110, 10) == 100
    assert old_calculate_profit(100, 90, 10) == -100

# After: 리팩토링 후 새로운 구현
def new_calculate_profit(trade_info):
    """더 나은 구조로 리팩토링"""
    return (trade_info.sell_price - trade_info.buy_price) * trade_info.quantity

# 동일한 테스트로 검증
def test_profit_calculation_behavior():
    trade = TradeInfo(buy_price=100, sell_price=110, quantity=10)
    assert new_calculate_profit(trade) == 100
    
    trade = TradeInfo(buy_price=100, sell_price=90, quantity=10)
    assert new_calculate_profit(trade) == -100
```

---

## 4. 테스트 유지보수 전략

### 📊 테스트 건강도 관리

#### 정기적 테스트 리뷰 (월 1회)
```python
# 1. 느린 테스트 식별
pytest tests/ --durations=10

# 2. 불안정한 테스트 추적
# 5번 연속 실행하여 불안정성 확인
for i in range(5):
    pytest tests/test_flaky.py

# 3. 테스트 커버리지 확인
pytest --cov=upbit_auto_trading --cov-report=html
```

#### 테스트 리팩토링 신호
```python
# ❌ 리팩토링이 필요한 테스트
def test_complex_strategy_execution():
    # 100줄이 넘는 거대한 테스트
    # 많은 Mock 객체 설정
    # 여러 기능을 동시에 테스트
    pass

# ✅ 리팩토링 후
def test_strategy_entry_signal():
    # 진입 신호만 테스트
    pass
    
def test_strategy_exit_signal():
    # 청산 신호만 테스트
    pass

def test_strategy_risk_management():
    # 리스크 관리만 테스트
    pass
```

### 🔄 테스트 진화 전략

#### 테스트 삭제 기준
```python
# 삭제해도 되는 테스트들
def test_deprecated_function():
    """더 이상 사용하지 않는 함수의 테스트"""
    pass

def test_implementation_detail():
    """구현 세부사항만 테스트하는 경우"""
    # private 메서드 테스트 등
    pass

# 보존해야 하는 테스트들
def test_business_rule():
    """비즈니스 규칙을 검증하는 테스트 - 영구 보존"""
    pass

def test_api_contract():
    """외부 API 계약을 검증하는 테스트 - 영구 보존"""
    pass
```

---

## 5. CI/CD 통합

### 🚀 자동화 파이프라인

#### 단계별 테스트 실행
```yaml
# 빠른 피드백 (30초 이내)
stages:
  - fast_tests:
      - unit_tests      # 10초
      - lint_check      # 5초
      - type_check      # 10초
      
  # 완전한 검증 (5분 이내)
  - complete_tests:
      - integration_tests  # 2분
      - e2e_tests         # 3분
      
  # 배포 전 최종 검증
  - deployment_tests:
      - smoke_tests       # 1분
      - performance_tests # 10분
```

#### 테스트 결과 기반 배포 결정
```python
# 배포 게이트 조건
deployment_gate_rules = {
    "unit_test_pass_rate": 100,      # 유닛테스트 100% 통과
    "code_coverage": 80,             # 코드 커버리지 80% 이상
    "performance_regression": False,  # 성능 회귀 없음
    "security_scan_pass": True       # 보안 스캔 통과
}

def check_deployment_readiness():
    if not all(deployment_gate_rules.values()):
        raise DeploymentBlockedError("배포 조건 미충족")
    return True
```

### 📊 지속적 모니터링

#### 테스트 메트릭 추적
```python
# 일일 테스트 헬스 체크
test_metrics = {
    "execution_time": "< 30초",
    "success_rate": "> 99%",
    "coverage_trend": "상승 또는 유지",
    "flaky_test_count": "< 5%"
}

# 주간 리포트 생성
def generate_weekly_test_report():
    return {
        "total_tests": len(all_tests),
        "new_tests": len(tests_added_this_week),
        "removed_tests": len(tests_removed_this_week),
        "avg_execution_time": calculate_avg_time(),
        "top_failing_tests": get_most_failing_tests()
    }
```

---

## 6. 실무 팁과 베스트 프랙티스

### 💡 주니어 개발자를 위한 실무 팁

#### 1. 테스트 작성 순서
```python
# 추천 순서: AAA 패턴
def test_calculate_moving_average():
    # 1. Arrange (준비)
    prices = [100, 102, 104, 106, 108]
    period = 3
    
    # 2. Act (실행)
    result = calculate_moving_average(prices, period)
    
    # 3. Assert (검증)
    expected = (104 + 106 + 108) / 3  # 마지막 3개 평균
    assert result == expected
```

#### 2. 좋은 테스트 이름 짓기
```python
# ❌ 나쁜 테스트 이름
def test1():
def test_rsi():
def test_function():

# ✅ 좋은 테스트 이름
def test_rsi_returns_100_when_all_prices_increasing():
def test_rsi_returns_0_when_all_prices_decreasing():
def test_rsi_raises_error_when_empty_data():
```

#### 3. Mock 사용법
```python
# 외부 의존성 Mock 처리
from unittest.mock import Mock, patch

def test_strategy_with_mocked_api():
    # API 호출을 Mock으로 대체
    with patch('upbit_api.get_current_price') as mock_api:
        mock_api.return_value = 50000000  # 5천만원
        
        strategy = RSIStrategy()
        signal = strategy.generate_signal('KRW-BTC')
        
        assert signal in ['BUY', 'SELL', 'HOLD']
        mock_api.assert_called_once_with('KRW-BTC')
```

### 🎯 팀 차원의 테스트 문화

#### 코드 리뷰 시 테스트 체크포인트
- [ ] **테스트가 포함되어 있는가?**
- [ ] **테스트 이름이 의도를 명확히 표현하는가?**
- [ ] **경계값과 예외 상황을 다루는가?**
- [ ] **테스트가 독립적으로 실행 가능한가?**
- [ ] **실행 시간이 적절한가? (1초 이내)**

#### 테스트 작성 가이드라인
```python
# 팀 표준 테스트 템플릿
class TestCalculateRSI:
    """RSI 계산 함수 테스트 슈트"""
    
    def setup_method(self):
        """각 테스트 실행 전 준비"""
        self.sample_data = [100, 102, 101, 103, 105]
    
    def test_normal_case(self):
        """정상적인 케이스 테스트"""
        pass
        
    def test_boundary_cases(self):
        """경계값 테스트"""
        pass
        
    def test_error_cases(self):
        """예외 상황 테스트"""
        pass
        
    def teardown_method(self):
        """각 테스트 실행 후 정리"""
        pass
```

### 🔧 도구와 환경 설정

#### 개발 환경 설정
```bash
# 1. pytest 설정 파일 (pytest.ini)
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --cov=upbit_auto_trading
    --cov-report=term-missing

# 2. IDE 설정 (VS Code)
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "python.testing.autoTestDiscoverOnSaveEnabled": true
}

# 3. Git Hook 설정 (pre-commit)
#!/bin/sh
echo "Running tests before commit..."
pytest tests/ --tb=short
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

#### 성능 최적화
```python
# 느린 테스트 최적화
# Before: 느린 테스트
def test_slow_backtest():
    # 1년치 데이터로 백테스팅 (10초 소요)
    data = load_one_year_data()
    result = run_backtest(data)
    assert result.profit > 0

# After: 빠른 테스트
def test_fast_backtest():
    # 1주일치 샘플 데이터 (0.1초 소요)
    data = create_sample_data(days=7)
    result = run_backtest(data)
    assert result.profit > 0

# 실제 데이터는 통합 테스트에서 처리
def test_integration_full_backtest():
    """느린 테스트는 별도 마킹"""
    pytest.mark.slow
    data = load_one_year_data()
    result = run_backtest(data)
    assert result.profit > 0
```

---

## 📚 추가 학습 자료

### 📖 권장 도서
- **"Test Driven Development"** - Kent Beck
- **"Clean Code"** - Robert Martin
- **"The Art of Unit Testing"** - Roy Osherove

### 🔗 유용한 도구들
- **pytest**: Python 테스트 프레임워크
- **coverage.py**: 코드 커버리지 측정
- **pytest-mock**: Mock 객체 생성
- **pytest-html**: HTML 테스트 리포트
- **pytest-xdist**: 병렬 테스트 실행

### 💡 실무 예제 저장소
```bash
# 이 프로젝트의 테스트 예제들
tests/
├── unit/                   # 유닛 테스트
├── integration/            # 통합 테스트  
├── fixtures/              # 테스트 데이터
└── conftest.py            # pytest 설정
```

---

## 🎯 마무리: 핵심 기억할 점

### ✅ DO: 반드시 해야 할 것들
- **모든 새 기능에 테스트 작성**
- **커밋 전 테스트 실행 확인**
- **테스트 실패 시 즉시 수정**
- **정기적인 테스트 리뷰**

### ❌ DON'T: 피해야 할 것들
- **테스트 없이 코드 배포**
- **실패하는 테스트 방치**
- **너무 복잡한 테스트 작성**
- **외부 의존성에 의존하는 테스트**

### 🎪 테스트는 개발자의 안전망
> "테스트는 개발 완료 후 버리는 것이 아니라, 코드와 함께 살아가는 동반자입니다. 좋은 테스트는 코드의 품질을 높이고, 개발자의 자신감을 향상시키며, 팀의 생산성을 극대화합니다."

---

**💡 기억하세요**: 테스트는 비용이 아닌 투자입니다. 지금 작성한 테스트 코드가 미래의 당신과 팀을 구해줄 것입니다! 🚀
