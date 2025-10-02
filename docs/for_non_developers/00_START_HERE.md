# 🎯 비개발자를 위한 시작 가이드

## 당신이 여기에 온 이유

- 코파일럿과 협업하고 싶지만 "어디에 뭘 만들어야 할지" 모르겠다
- DDD, Infrastructure, Domain 같은 용어가 어렵다
- 기능을 상상하는데 이걸 코드로 요청하는 방법을 모르겠다

## 이 문서의 목적

**"3분 안에 다음 작업 위치를 결정하고 코파일럿에게 요청하기"**

---

## 📚 3단계 학습-가이드 체계

이 폴더는 **비개발자가 DDD 프로젝트에서 코파일럿과 효율적으로 협업**하기 위한 문서들입니다.

### 📂 폴더 구조

```
docs/for_non_developers/
├── 00_START_HERE.md          # 👈 지금 읽고 있는 파일
├── guides/                   # 🚀 실전용 가이드 (바로 써먹기)
│   ├── 01_어디에_무엇을_만들까.md
│   ├── 02_폴더_선택_가이드.md
│   ├── 03_파일_이름_짓기.md
│   ├── 04_코파일럿에게_요청하기.md
│   └── 05_검증_체크리스트.md
└── learning/                 # 📖 학습용 문서 (이해하기)
    ├── L01_DDD란_무엇인가.md
    ├── L02_왜_폴더가_4개인가.md
    ├── L03_Infrastructure_쉽게_이해하기.md
    ├── L04_Domain_쉽게_이해하기.md
    ├── L05_Application_쉽게_이해하기.md
    └── L06_Presentation_쉽게_이해하기.md
```

---

## 🎯 어떤 문서부터 읽을까?

### 상황 1: "급해요! 지금 당장 기능 구현해야 해요"

1. **guides/01_어디에_무엇을_만들까.md** (5분)
   - 빠른 의사결정 플로우차트
   - "이 기능은 어느 폴더에?" 즉시 판단
2. **guides/04_코파일럿에게_요청하기.md** (5분)
   - 명확한 요청 템플릿
   - 좋은 예시 vs 나쁜 예시

### 상황 2: "시간 있어요. 제대로 이해하고 싶어요"

1. **learning/L01_DDD란_무엇인가.md** (10분)
   - DDD를 레고 블록처럼 쉽게 설명
2. **learning/L02_왜_폴더가_4개인가.md** (10분)
   - Infrastructure/Domain/Application/Presentation 구분법
3. **guides/01_어디에_무엇을_만들까.md** (5분)
   - 실전 적용

### 상황 3: "특정 레이어만 집중하고 싶어요"

- Infrastructure 작업 → **learning/L03_Infrastructure_쉽게_이해하기.md**
- Domain 작업 → **learning/L04_Domain_쉽게_이해하기.md**
- Application 작업 → **learning/L05_Application_쉽게_이해하기.md**
- Presentation 작업 → **learning/L06_Presentation_쉽게_이해하기.md**

---

## 🚀 빠른 시작 (5분 속성 과정)

### 1단계: 4개 레이어 암기 (2분)

```
📦 upbit_auto_trading/
│
├── 🌐 infrastructure/    "외부 세계 연결"
│   ├── external_apis/   → 업비트 API 호출
│   ├── database/        → DB 저장/읽기
│   └── logging/         → 로그 기록
│
├── 💎 domain/           "핵심 비즈니스 규칙"
│   ├── entities/        → 전략, 주문, 포지션
│   ├── value_objects/   → 가격, 수량, 시간프레임
│   └── services/        → 계산 로직
│
├── 🎬 application/      "시나리오 조율"
│   ├── use_cases/       → "전략 생성하기", "주문 실행하기"
│   └── services/        → 여러 기능 조합
│
└── 🖥️ presentation/     "화면 로직"
    ├── presenters/      → UI 로직
    └── views/           → PyQt6 화면
```

### 2단계: 빠른 판단법 (1분)

```
질문: "이 기능 어디에 만들어야 하지?"

1. 화면에 보이는 거야?
   → YES: presentation/ 또는 ui/

2. 업비트 API나 DB 통신이야?
   → YES: infrastructure/

3. 비즈니스 규칙/계산이야?
   → YES: domain/

4. 여러 기능 조합이야?
   → YES: application/
```

### 3단계: 코파일럿에게 요청 (2분)

```
[기능명]을 구현하고 싶습니다.

📍 위치: upbit_auto_trading/[레이어]/[폴더]/[파일명].py
🎯 목적: [한 문장]
📋 요구사항:
1. [구체적 요구사항 1]
2. [구체적 요구사항 2]

✅ 제약사항:
- DDD 계층 준수
- Infrastructure 로깅 사용
- dry_run=True 기본값
```

---

## 💡 실전 예시

### 예시 1: "코인 목록을 화면에 표시하고 싶어요"

**판단 과정:**

1. 화면에 보이는 거? → YES
2. 하지만 데이터는 업비트에서 가져와야 함

**결론: 여러 레이어 협업 필요**

**요청 방법:**

```
코인 목록 조회 기능을 구현하고 싶습니다.

[1단계] infrastructure/external_apis/upbit/ 에
        get_market_list() 메서드 추가

[2단계] application/use_cases/ 에
        GetMarketListUseCase 구현

[3단계] presentation/presenters/ 에
        MarketListPresenter 구현

[4단계] ui/desktop/views/ 에
        MarketListView (테이블 UI) 구현
```

### 예시 2: "RSI 70 이상이면 과매수 판단하는 로직 필요해요"

**판단 과정:**

1. 화면? → NO
2. API/DB? → NO
3. 비즈니스 규칙? → YES ✅

**결론: domain/ 레이어**

**요청 방법:**

```
RSI 과매수 판단 규칙을 구현하고 싶습니다.

📍 위치: upbit_auto_trading/domain/services/indicator_validator.py
🎯 목적: RSI 값 기반 과매수/과매도 판단

📋 요구사항:
1. RSI > 70 → 과매수
2. RSI < 30 → 과매도
3. enum 타입 반환 (OVERBOUGHT/NEUTRAL/OVERSOLD)

✅ 제약사항:
- Domain 레이어이므로 외부 의존성 없음
- 순수 계산 로직만
```

---

## 📖 다음 단계

### 이제 어떻게 하나요?

1. **급하다면:**
   - `guides/01_어디에_무엇을_만들까.md` 읽기
   - 바로 기능 구현 시작

2. **천천히 배우고 싶다면:**
   - `learning/L01_DDD란_무엇인가.md`부터 순서대로 읽기
   - 각 레이어 이해 후 실전 적용

3. **특정 부분만 집중:**
   - 해당 레이어 learning 문서 읽기
   - guides 문서로 실전 연습

---

## 🆘 자주 묻는 질문

### Q1: "문서가 너무 많아요. 최소한 뭐만 읽으면 되나요?"

**A:** 이 3개만 읽으세요 (15분):

1. 이 파일 (00_START_HERE.md) - 5분
2. guides/01_어디에_무엇을_만들까.md - 5분
3. guides/04_코파일럿에게_요청하기.md - 5분

### Q2: "DDD가 너무 어려워요"

**A:** 처음엔 이것만 기억하세요:

- **Infrastructure** = 외부 연결 (API, DB, 파일)
- **Domain** = 핵심 규칙 (계산, 검증, 개념)
- **Application** = 시나리오 (여러 기능 조합)
- **Presentation** = 화면 (버튼, 테이블, 차트)

### Q3: "코파일럿이 엉뚱한 곳에 코드를 만들어요"

**A:** 요청할 때 **정확한 경로**를 명시하세요:

- ❌ "차트 만들어줘"
- ✅ "ui/desktop/views/chart_view.py에 matplotlib 차트 위젯 만들어줘"

### Q4: "한 번에 전체 기능을 만들어달라고 하면 안 되나요?"

**A:** 작은 단계로 쪼개세요:

- 복잡한 기능 = 여러 레이어 협업
- 한 번에 하나의 레이어/파일만 요청
- 검증 후 다음 단계 진행

---

## ✅ 체크리스트

시작하기 전에 확인:

- [ ] 4개 레이어의 역할을 이해했다
- [ ] 빠른 판단법을 숙지했다
- [ ] 명확한 요청 템플릿을 확인했다
- [ ] 실전 예시를 읽어봤다

**준비됐다면 `guides/01_어디에_무엇을_만들까.md`로 이동하세요!**

---

## 📝 문서 요청 가이드

이 폴더의 문서들은 필요할 때마다 생성됩니다.
다음과 같이 요청하세요:

```
"guides/01_어디에_무엇을_만들까.md 문서를 작성해주세요"
"learning/L03_Infrastructure_쉽게_이해하기.md 문서를 작성해주세요"
```

---

**문서 버전:** v1.0
**최종 수정:** 2025-10-02
**작성자:** GitHub Copilot (Claude Sonnet 4)
