# DDD란 무엇인가? - 레고 블록처럼 쉬운 설명

## 🎯 이 문서의 목적

**"DDD(Domain-Driven Design)"를 전문 용어 없이 완벽히 이해하기**

---

## 🤔 DDD가 뭐죠?

### 한 문장 정의

**"프로그램을 역할별로 깔끔하게 나누는 설계 방법"**

### 왜 배워야 하나요?

프로그램이 복잡해지면:

- ❌ 어디에 뭘 만들어야 할지 모르겠음
- ❌ 한 곳을 고치면 다른 곳이 망가짐
- ❌ 코드를 찾기가 너무 어려움
- ❌ 새 기능 추가가 두려움

DDD를 사용하면:

- ✅ 위치를 명확히 알 수 있음
- ✅ 한 부분을 고쳐도 다른 곳은 안전함
- ✅ 코드를 쉽게 찾을 수 있음
- ✅ 새 기능을 자신 있게 추가 가능

---

## 🏗️ 레고 블록 비유로 이해하기

### 레고로 집 짓기

당신이 레고로 큰 집을 짓는다고 상상해보세요.

#### ❌ 나쁜 방법: 모든 블록을 한 곳에

```
[거실 블록 + 주방 블록 + 화장실 블록 + 지붕 블록 + 창문 블록 + ...]
→ 전부 섞여 있음
→ 어디가 거실인지 모르겠음
→ 창문 하나 고치려면 전체를 뜯어야 함
```

**문제점:**

- 뭐가 뭔지 모르겠음
- 고치기 무서움
- 확장 불가능

#### ✅ 좋은 방법: 방별로 모듈 분리

```
[거실 모듈]
  - 거실용 블록만 포함
  - 독립적으로 조립 가능
  - 다른 모듈과 연결 가능

[주방 모듈]
  - 주방용 블록만 포함
  - 독립적으로 조립 가능
  - 거실과 연결 가능

[화장실 모듈]
  - 화장실용 블록만 포함
  - 독립적으로 조립 가능
```

**장점:**

- 각 방의 역할이 명확
- 한 방을 고쳐도 다른 방은 안전
- 새 방 추가 쉬움
- 방을 통째로 교체 가능

### 🎯 이것이 바로 DDD입니다

**DDD = 프로그램을 "모듈(레이어)"로 나누는 방법**

---

## 📦 DDD의 4개 레이어 (4개의 방)

우리 프로젝트는 **4개의 레이어**로 나뉩니다.

```
📦 upbit_auto_trading/ (집 전체)
│
├── 🌐 infrastructure/    "외부 세계와 연결하는 방"
│   역할: 업비트 API, DB, 파일, 로그
│   비유: 집의 수도관, 전기선, 인터넷 케이블
│
├── 💎 domain/           "핵심 규칙을 보관하는 방"
│   역할: 거래 규칙, 계산식, 검증
│   비유: 집의 설계도, 건축 규칙
│
├── 🎬 application/      "일 순서를 정하는 방"
│   역할: 시나리오, 여러 기능 조합
│   비유: 집의 일정표 (아침: 씻기 → 식사 → 출근)
│
└── 🖥️ presentation/     "사람과 대화하는 방"
    역할: 화면, 버튼, 테이블
    비유: 집의 거실 (손님을 맞이하는 곳)
```

---

## 🌐 레이어 1: Infrastructure (외부 연결)

### 일상 생활 비유

**집의 수도관, 전기선, 인터넷 케이블**

- 물이 필요하면 수도관 사용
- 전기가 필요하면 콘센트 사용
- 인터넷이 필요하면 와이파이 사용

**집 내부 사람들은 "수도관이 어떻게 생겼는지" 몰라도 됨**
→ 그냥 "물 주세요" 하면 됨

### 프로그램에서

**외부 세계와 연결하는 통로**

```
프로그램: "BTC 현재가 알려줘"
Infrastructure: → 업비트 API 호출
                → 응답 받음
                → 프로그램에 전달
```

**프로그램 내부는 "업비트 API가 어떻게 생겼는지" 몰라도 됨**
→ 그냥 "현재가 주세요" 하면 됨

### 실제 예시

```python
# infrastructure/external_apis/upbit/upbit_public_client.py
class UpbitPublicClient:
    """업비트와 통신하는 통로"""

    def get_current_price(self, symbol: str) -> Decimal:
        # 1. HTTP 요청 보내기
        response = requests.get(f"https://api.upbit.com/v1/ticker?markets={symbol}")

        # 2. 응답 받기
        data = response.json()

        # 3. 필요한 부분만 추출
        price = data[0]["trade_price"]

        # 4. 프로그램이 이해하는 형태로 변환
        return Decimal(str(price))
```

**핵심:** Infrastructure는 **"외부와 대화하는 법"**을 담당

---

## 💎 레이어 2: Domain (핵심 규칙)

### 일상 생활 비유

**집의 설계도와 건축 규칙**

- "방의 최소 면적은 5평 이상" (규칙)
- "천장 높이 = 바닥 면적 ÷ 10" (계산식)
- "화장실은 반드시 환기구 필요" (검증)

**이 규칙들은 집이 어디에 있든 동일함**
→ 서울이든 부산이든 건축 규칙은 같음

### 프로그램에서

**핵심 비즈니스 규칙과 계산**

```
거래 규칙: "RSI 30 이하면 과매도"
계산식: "수익률 = (현재가 - 진입가) ÷ 진입가 × 100"
검증: "주문 금액은 5,000원 이상"
```

**이 규칙들은 어떤 거래소든 동일함**
→ 업비트든 바이낸스든 매매 규칙은 같음

### 실제 예시

```python
# domain/services/profit_calculator.py
class ProfitCalculator:
    """수익률 계산 규칙"""

    def calculate_profit_rate(
        self,
        entry_price: Decimal,
        current_price: Decimal
    ) -> Decimal:
        """
        비즈니스 규칙:
        수익률 = (현재가 - 진입가) ÷ 진입가 × 100
        """
        return (current_price - entry_price) / entry_price * 100

    def is_profit_target_reached(
        self,
        profit_rate: Decimal,
        target_rate: Decimal
    ) -> bool:
        """
        비즈니스 규칙:
        목표 수익률 도달 판단
        """
        return profit_rate >= target_rate
```

**핵심:** Domain은 **"프로그램의 핵심 지식"**을 담당

**중요 규칙:** Domain은 외부를 몰라야 함

- ❌ Domain에서 업비트 API 호출 금지
- ❌ Domain에서 DB 저장 금지
- ❌ Domain에서 화면 표시 금지
- ✅ Domain은 순수한 규칙과 계산만

---

## 🎬 레이어 3: Application (시나리오 조율)

### 일상 생활 비유

**집의 일정표와 순서**

```
아침 루틴:
1. 알람 듣기 (외부 입력)
2. 화장실 가기 (Domain 규칙: "아침엔 씻어야 함")
3. 옷장에서 옷 가져오기 (Infrastructure: 저장소 접근)
4. 식탁에 앉기 (Presentation: 위치 이동)
```

**Application은 "무엇을 어떤 순서로 할지" 결정**

### 프로그램에서

**사용자 시나리오 구현**

```
"전략 생성하기" 시나리오:
1. 사용자 입력 받기 (Presentation)
2. 전략 검증하기 (Domain)
3. DB에 저장하기 (Infrastructure)
4. 성공 메시지 표시 (Presentation)
```

**Application은 "일의 순서"를 담당**

### 실제 예시

```python
# application/use_cases/create_strategy.py
class CreateStrategyUseCase:
    """전략 생성 시나리오"""

    def __init__(
        self,
        strategy_validator,    # Domain
        strategy_repository    # Infrastructure
    ):
        self.validator = strategy_validator
        self.repository = strategy_repository

    def execute(self, strategy_data: StrategyDTO) -> str:
        """
        시나리오:
        1. 검증 → 2. 저장 → 3. 결과 반환
        """
        # 1단계: Domain에게 검증 요청
        if not self.validator.is_valid(strategy_data):
            raise ValidationError("전략 설정이 올바르지 않습니다")

        # 2단계: Infrastructure에게 저장 요청
        strategy_id = self.repository.save(strategy_data)

        # 3단계: 결과 반환
        return f"전략 생성 완료: {strategy_id}"
```

**핵심:** Application은 **"누구에게 무엇을 시킬지"**를 담당

---

## 🖥️ 레이어 4: Presentation (화면)

### 일상 생활 비유

**집의 거실 (손님 맞이)**

- 손님이 문을 두드림 → 문 열기
- 손님이 "물 주세요" → 주방에 요청 → 물 가져다주기
- 손님이 떠남 → 인사하기

**거실은 손님과 대화만 함, 직접 요리하지 않음**

### 프로그램에서

**사용자와 대화하는 화면**

```
사용자: 버튼 클릭
Presentation: "전략 생성 요청이 왔어요" → Application에 전달
Application: 처리 완료 → "성공했어요"
Presentation: 화면에 "성공!" 메시지 표시
```

**Presentation은 "메신저" 역할**

### 실제 예시

```python
# presentation/presenters/strategy_form_presenter.py
class StrategyFormPresenter:
    """전략 폼 화면 로직"""

    def __init__(
        self,
        view,                      # UI
        create_strategy_use_case   # Application
    ):
        self.view = view
        self.use_case = create_strategy_use_case

    def on_save_button_clicked(self):
        """저장 버튼 클릭 시"""
        # 1. View에서 데이터 가져오기
        strategy_data = self.view.get_form_data()

        try:
            # 2. Application에게 처리 요청
            result = self.use_case.execute(strategy_data)

            # 3. View에 성공 메시지 표시
            self.view.show_success_message(result)

        except ValidationError as e:
            # 4. View에 에러 메시지 표시
            self.view.show_error_message(str(e))
```

**핵심:** Presentation은 **"사용자 ↔ 프로그램 통역사"** 역할

---

## 🎯 4개 레이어가 함께 일하는 모습

### 실전 시나리오: "BTC를 매수하고 싶어요"

```
[사용자]
  ↓ "BTC 매수" 버튼 클릭

[Presentation] 🖥️
  ↓ "매수 요청이 왔어요"
  ↓ Application에 전달

[Application] 🎬
  ↓ "매수 시나리오 시작"
  ↓ 1. Domain에 "이 주문 유효해?" 물어봄

[Domain] 💎
  ↓ "잔액 충분? 최소 금액 이상? → OK!"
  ↓ Application에 "유효함" 응답

[Application] 🎬
  ↓ 2. Infrastructure에 "업비트에 주문 넣어줘" 요청

[Infrastructure] 🌐
  ↓ 업비트 API 호출
  ↓ 주문 성공
  ↓ Application에 "완료" 응답

[Application] 🎬
  ↓ 3. Presentation에 "성공!" 전달

[Presentation] 🖥️
  ↓ 화면에 "매수 완료!" 메시지 표시

[사용자]
  ✅ "오! 매수됐네"
```

---

## 🚫 레이어 규칙: 절대 넘지 말아야 할 선

### 규칙 1: Domain은 외부를 몰라야 함

**❌ 잘못된 예:**

```python
# domain/services/trading_service.py
class TradingService:
    def should_buy(self, symbol: str) -> bool:
        # ❌ Domain에서 API 호출 금지!
        price = requests.get(f"https://api.upbit.com/v1/ticker?markets={symbol}")
        return price < 50000000
```

**✅ 올바른 예:**

```python
# domain/services/trading_service.py
class TradingService:
    def should_buy(self, current_price: Decimal, threshold: Decimal) -> bool:
        # ✅ 순수 규칙만
        return current_price < threshold
```

### 규칙 2: Presentation은 비즈니스 로직 없음

**❌ 잘못된 예:**

```python
# presentation/presenters/chart_presenter.py
class ChartPresenter:
    def on_buy_button_clicked(self):
        # ❌ Presenter에서 계산 금지!
        profit_rate = (current_price - entry_price) / entry_price * 100
        if profit_rate > 5:
            self.execute_sell()
```

**✅ 올바른 예:**

```python
# presentation/presenters/chart_presenter.py
class ChartPresenter:
    def on_buy_button_clicked(self):
        # ✅ UseCase에 위임
        result = self.execute_order_use_case.execute(order_data)
        self.view.show_result(result)
```

### 규칙 3: Infrastructure는 규칙 결정 안 함

**❌ 잘못된 예:**

```python
# infrastructure/repositories/strategy_repository.py
class StrategyRepository:
    def save(self, strategy):
        # ❌ Infrastructure에서 검증 금지!
        if strategy.entry_price < 0:
            raise ValidationError("가격은 양수여야 함")
        self.db.insert(strategy)
```

**✅ 올바른 예:**

```python
# infrastructure/repositories/strategy_repository.py
class StrategyRepository:
    def save(self, strategy):
        # ✅ 검증은 Domain이 함, 여기선 저장만
        self.db.insert(strategy)
```

---

## 🎓 DDD의 핵심 철학

### 1. **관심사의 분리** (Separation of Concerns)

각 레이어는 자기 일만 함:

- Infrastructure → 외부 연결만
- Domain → 규칙만
- Application → 조율만
- Presentation → 화면만

### 2. **의존성 역전** (Dependency Inversion)

```
잘못된 방향:
Domain → Infrastructure (X)
  ↑
 Domain이 Infrastructure를 알게 됨

올바른 방향:
Domain ← Infrastructure (O)
  ↑
 Infrastructure가 Domain을 알게 됨
```

**왜?**

- Domain(핵심 규칙)은 변하면 안 됨
- Infrastructure(기술)는 자주 변함
- 안정적인 것을 중심으로!

### 3. **테스트 가능성**

각 레이어를 독립적으로 테스트 가능:

```python
# Domain 테스트 - 외부 없이 가능
def test_profit_calculator():
    calculator = ProfitCalculator()
    profit = calculator.calculate_profit_rate(
        entry_price=Decimal("100"),
        current_price=Decimal("110")
    )
    assert profit == Decimal("10")  # 10% 수익

# Infrastructure 테스트 - 실제 API 없이 가능 (Mock 사용)
def test_upbit_client(mock_requests):
    client = UpbitPublicClient()
    price = client.get_current_price("KRW-BTC")
    assert price > 0
```

---

## 💡 DDD를 사용하는 이유 - 종합 정리

### 문제 상황 (DDD 없이)

```
📄 my_program.py (5000줄)
  - 화면 코드
  - 업비트 API 코드
  - 계산 로직
  - DB 저장 코드
  - 전부 섞여 있음 😱

문제:
❌ 수익률 계산 로직을 찾으려면 5000줄 검색
❌ 화면 수정했는데 계산이 망가짐
❌ 테스트 불가능
❌ 새 기능 추가 두려움
```

### 해결 방법 (DDD 적용)

```
📦 upbit_auto_trading/
├── infrastructure/
│   └── upbit_client.py (200줄)
│
├── domain/
│   └── profit_calculator.py (50줄)
│
├── application/
│   └── create_strategy.py (100줄)
│
└── presentation/
    └── strategy_presenter.py (150줄)

해결:
✅ 수익률 계산은 domain/profit_calculator.py
✅ 화면 수정해도 계산은 안전
✅ 각 부분 독립 테스트 가능
✅ 새 기능은 적절한 레이어에 추가
```

---

## 🎯 실전 적용 가이드

### 새 기능을 만들 때

1. **먼저 물어보기:**
   - "이것은 외부 연결인가?" → Infrastructure
   - "이것은 핵심 규칙인가?" → Domain
   - "이것은 시나리오인가?" → Application
   - "이것은 화면인가?" → Presentation

2. **레이어 경계 지키기:**
   - Domain에서 API 호출 금지
   - Presentation에서 계산 금지
   - Infrastructure에서 규칙 결정 금지

3. **작은 단위로 만들기:**
   - 한 번에 한 레이어만
   - 테스트하면서 진행
   - 검증 후 다음 레이어

---

## ✅ 졸업 테스트

### 다음 중 올바른 것은?

1. **Domain에서 업비트 API를 직접 호출한다**
   - [ ] 맞음
   - [x] 틀림 (Domain은 외부 의존성 없음)

2. **Presentation은 비즈니스 계산을 직접 한다**
   - [ ] 맞음
   - [x] 틀림 (계산은 Domain에 위임)

3. **Infrastructure는 DB와 통신한다**
   - [x] 맞음
   - [ ] 틀림

4. **Application은 여러 레이어를 조율한다**
   - [x] 맞음
   - [ ] 틀림

5. **Domain은 프로그램의 핵심 규칙을 담는다**
   - [x] 맞음
   - [ ] 틀림

### 다음 코드는 어느 레이어?

```python
class ProfitCalculator:
    def calculate_profit_rate(self, entry, current):
        return (current - entry) / entry * 100
```

<details>
<summary>정답 보기</summary>

**Domain**

이유:

- 계산 로직 (비즈니스 규칙)
- 외부 의존성 없음
- 순수 함수

</details>

```python
class UpbitClient:
    def get_current_price(self, symbol):
        response = requests.get(f"https://api.upbit.com/...")
        return response.json()
```

<details>
<summary>정답 보기</summary>

**Infrastructure**

이유:

- 외부 API 통신
- requests 라이브러리 사용
- 외부 세계와 연결

</details>

```python
class StrategyPresenter:
    def on_save_button_clicked(self):
        data = self.view.get_form_data()
        self.use_case.execute(data)
        self.view.show_success()
```

<details>
<summary>정답 보기</summary>

**Presentation**

이유:

- 화면 이벤트 처리
- View와 UseCase 연결
- 사용자 시나리오 시작점

</details>

---

## 📖 다음 학습

DDD를 이해했다면:

1. **learning/L02_왜_폴더가_4개인가.md** - 레이어 심화 이해
2. **learning/L03~L06** - 각 레이어 상세 가이드
3. **guides/01_어디에_무엇을_만들까.md** - 실전 판단 연습

---

**문서 버전:** v1.0
**최종 수정:** 2025-10-02
**작성자:** GitHub Copilot (Claude Sonnet 4)
