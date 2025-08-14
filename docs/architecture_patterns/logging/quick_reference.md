# 🚀 로깅 시스템 빠른 참조 가이드

> **한 눈에 보는 최적화된 Domain Logger 시스템**

## 📍 핵심 포인트

### 🎯 24.2배 성능 향상 달성
- **Before**: 54.78ms (Domain Events)
- **After**: 2.26ms (의존성 주입)
- **결과**: NoOp 수준의 성능

### 🏗️ DDD 순수성 유지
- Domain Layer에서 Infrastructure 의존성 **0개**
- 추상 인터페이스만 사용
- 런타임 의존성 주입

---

## 📂 파일 위치 맵

```
📁 upbit_auto_trading/
├── 🎯 domain/logging.py                    # Domain Interface (핵심)
├── 🔧 infrastructure/logging/
│   └── domain_logger_impl.py              # Infrastructure 구현체
└── 🚀 run_desktop_ui.py                   # 의존성 주입 설정
```

---

## 🔧 코드 템플릿

### Domain Service에서 사용
```python
from upbit_auto_trading.domain.logging import create_domain_logger

class MyDomainService:
    def __init__(self):
        self.logger = create_domain_logger("MyDomainService")

    def do_business_logic(self):
        self.logger.info("업무 로직 시작", {"param": "value"})
```

### Infrastructure Service에서 사용
```python
from upbit_auto_trading.infrastructure.logging import create_component_logger

class MyInfraService:
    def __init__(self):
        self.logger = create_component_logger("MyInfraService")
```

---

## 🔍 아키텍처 흐름

```
Domain Service → create_domain_logger()
→ DomainLogger Interface → (의존성 주입)
→ InfrastructureDomainLogger → Infrastructure Logger
→ File/Console Output
```

---

## ⚡ 성능 특징

| 구분 | Legacy | New | 개선 |
|------|--------|-----|------|
| 로그 10k회 | 54.78ms | 2.26ms | **24.2배** |
| 오버헤드 | UUID+DateTime | 거의 없음 | **순수** |
| 메모리 | 이벤트 객체 생성 | 직접 위임 | **최적화** |

---

## 🛠️ 트러블슈팅

### ❌ 로그가 안 나올 때
```bash
# 의존성 주입 확인
grep "Domain Logger 성능 최적화 완료" logs/application.log
```

### 🔧 성능 테스트
```bash
python test_comprehensive_logging_performance.py
```

### 📊 DDD 의존성 체크
```powershell
Get-ChildItem upbit_auto_trading/domain -Recurse | Select-String "import.*infrastructure"
# 결과: 없어야 함 ✅
```

---

## 📋 체크리스트

- [ ] `domain/logging.py` - Domain Interface만 있는가?
- [ ] `infrastructure/logging/domain_logger_impl.py` - 구현체가 있는가?
- [ ] `run_desktop_ui.py` - 의존성 주입이 설정되었는가?
- [ ] 로그에서 "성능 최적화 완료" 메시지가 나오는가?
- [ ] Domain Services에서 로깅이 정상 동작하는가?

---

*🎯 핵심: DDD 순수성 + 24.2배 성능 향상 + 100% 호환성*
