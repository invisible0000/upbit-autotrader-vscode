# 🔍 Domain Event 기본값 추적 시스템

## 📋 개요

현재 dataclass 상속 제약으로 인해 임시 기본값을 사용 중입니다. 
나중에 구조 개선 시 쉽게 찾아서 수정할 수 있도록 마커 기반 시스템을 구축했습니다.

## 🏷️ 마커 시스템

### 주석 마커로 필드 분류

```python
# TODO_REQUIRED_FIELD: 나중에 필수 필드로 변경 예정
strategy_id: Optional[str] = None  # TEMP_DEFAULT: 필수값이지만 dataclass 제약으로 임시 None

# VALID_DEFAULT: 의미있는 기본값
strategy_type: str = "entry"

# OPTIONAL_FIELD: 진짜 선택적 필드
creator_id: Optional[str] = None
```

### 검증 로직 마커

```python
def __post_init__(self):
    """이벤트 생성 후 필수 필드 검증"""
    super().__post_init__()
    
    # TODO_VALIDATION: 나중에 구조 개선 시 제거할 임시 검증 로직
    if not self.strategy_id:
        raise ValueError("strategy_id는 필수 필드입니다 (현재 임시 None 기본값)")
```

## 🔍 검색으로 빠른 수정

### 1. 필수 필드 찾기
```bash
# VSCode에서 Ctrl+Shift+F로 검색
TODO_REQUIRED_FIELD
TEMP_DEFAULT
```

### 2. 임시 검증 로직 찾기
```bash
TODO_VALIDATION
```

### 3. 의미있는 기본값 확인
```bash
VALID_DEFAULT
```

### 4. 선택적 필드 확인
```bash
OPTIONAL_FIELD
```

## 🚀 향후 리팩토링 계획

### Phase 1: 구조 개선
1. `TODO_REQUIRED_FIELD` 검색으로 모든 필수 필드 식별
2. dataclass 상속 구조 재설계 또는 팩토리 패턴 도입
3. 필수 필드에서 `Optional[str] = None` 제거

### Phase 2: 검증 로직 정리
1. `TODO_VALIDATION` 검색으로 모든 임시 검증 로직 식별
2. 구조적 해결로 __post_init__ 검증 제거
3. 타입 시스템에서 필수성 보장

### Phase 3: 검증
1. 모든 TODO 마커 제거 확인
2. 의미있는 기본값만 유지
3. 타입 안정성 확보

## 📝 현재 적용된 파일들

### Domain Events
- `upbit_auto_trading/domain/events/strategy_events.py` ✅ 적용 완료
- `upbit_auto_trading/domain/events/trigger_events.py` (향후 적용)
- `upbit_auto_trading/domain/events/trading_events.py` (향후 적용)
- `upbit_auto_trading/domain/events/backtest_events.py` (향후 적용)

### 적용 상태 확인 명령어
```bash
# 모든 TODO 마커 검색
grep -r "TODO_REQUIRED_FIELD\|TODO_VALIDATION\|TEMP_DEFAULT" upbit_auto_trading/domain/events/

# 각 파일의 마커 개수 확인
grep -c "TODO_" upbit_auto_trading/domain/events/*.py
```

## 💡 장점

1. **추적 가능성**: 검색으로 모든 임시 해결책 즉시 식별
2. **의도 명확화**: 각 기본값의 의미와 목적 명시
3. **점진적 개선**: 나중에 안전하게 단계별 리팩토링 가능
4. **코드 품질**: 임시 해결책과 정상 설계 구분
5. **협업 효율성**: 다른 개발자도 쉽게 이해 가능

이 방식으로 현재는 안정적으로 동작하면서, 나중에 완벽하게 리팩토링할 수 있는 기반을 마련했습니다.
