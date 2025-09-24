# 📚 모델에서 서비스로: 언제, 무엇을 분리해야 하는가?

> **대상**: 비개발자 바이브 코딩 사용자
> **목적**: DDD 아키텍처에서 올바른 책임 분리 가이드
> **작성일**: 2025-09-25

---

## 🎯 핵심 원칙: "데이터 보관 vs 비즈니스 처리"

### 🏠 **모델(Model)의 역할**
```
모델 = 데이터를 담는 그릇 + 간단한 검증
```

**✅ 모델에서 해야 할 일**:
- 데이터 저장하기
- 기본적인 검증 (빈 값, 범위 체크)
- 상태 변경하기 (대기 → 처리중 → 완료)
- 간단한 계산 (필드 값만 사용하는 계산)

**❌ 모델에서 하면 안 되는 일**:
- 복잡한 계산 로직
- 외부 API 호출
- 데이터베이스 조회
- 비즈니스 규칙 처리

---

## 🚨 서비스 분리가 필요한 신호들

### 🔴 **즉시 분리 필요** (위험 신호)

#### 1. **복잡한 시간 계산**
```python
# ❌ 모델에서 하면 안 되는 예시
def calculate_effective_candle_count(self) -> int:
    # 겹침 상황별로 다른 계산 로직
    if status == OverlapStatus.PARTIAL_START:
        if self.db_start and self.api_response_end:
            return TimeUtils.calculate_expected_count(...)  # 복잡한 계산!
```

**왜 위험한가?**
- 여러 조건을 확인하는 복잡한 로직
- TimeUtils 같은 외부 도구 의존
- 비즈니스 규칙이 모델에 섞임

#### 2. **조건부 로직이 많은 경우**
```python
# ❌ 복잡한 조건 처리
def get_effective_end_time(self) -> Optional[datetime]:
    if status == OverlapStatus.COMPLETE_OVERLAP:
        return self.end or self.db_end or ...
    if status == OverlapStatus.PARTIAL_MIDDLE_CONTINUOUS:
        return self.db_end or self.final_candle_end or ...
    # ... 더 많은 조건들
```

**문제점**:
- 비즈니스 로직이 모델에 들어감
- 테스트하기 어려움
- 변경 시 모델 자체를 수정해야 함

### 🟡 **주의 깊게 살펴볼 것** (경고 신호)

#### 1. **여러 필드를 조합하는 계산**
```python
# 🟡 주의: 복잡해지면 서비스로 이동 고려
def has_complete_time_info(self) -> bool:
    return self.get_effective_end_time() is not None  # 간단하면 OK
```

#### 2. **외부 유틸리티 의존**
```python
# 🟡 현재는 허용, 미래에 분리 고려
self.to = TimeUtils.normalize_datetime_to_utc(new_to)  # 단순 정규화는 OK
```

---

## ✅ 올바른 분리 방법

### 🎯 **Before: 모델에서 복잡한 계산**
```python
# candle_business_models.py
class ChunkInfo:
    def calculate_effective_candle_count(self) -> int:
        # 복잡한 겹침 로직...
        if status == OverlapStatus.PARTIAL_START:
            if self.db_start and self.api_response_end:
                return TimeUtils.calculate_expected_count(...)
        # ... 더 많은 로직
```

### 🎯 **After: 서비스에서 계산, 모델에 저장**
```python
# chunk_calculation_service.py (새로 생성)
class ChunkCalculationService:
    @staticmethod
    def calculate_effective_candle_count(chunk_info: ChunkInfo) -> int:
        """겹침 상황을 반영한 실제 확보 캔들 수 계산"""
        if chunk_info.chunk_index == 0 and not chunk_info.has_overlap_info():
            return chunk_info.final_candle_count or 0

        status = chunk_info.overlap_status
        # ... 복잡한 비즈니스 로직

        return calculated_count

# candle_business_models.py (수정)
class ChunkInfo:
    effective_candle_count: Optional[int] = None  # 계산 결과 저장용

    def set_effective_candle_count(self, count: int) -> None:
        """계산된 캔들 수 저장"""
        self.effective_candle_count = count

    def get_effective_candle_count(self) -> int:
        """저장된 캔들 수 반환"""
        return self.effective_candle_count or 0
```

---

## 📋 실전 체크리스트

### 🔍 **이 기능이 서비스로 가야 하나?**

다음 질문들에 답해보세요:

#### ✅ **모델에 남겨도 되는 경우**
- [ ] 단순히 필드 값을 반환하나요?
- [ ] 기본적인 검증만 하나요? (빈 값, 범위 체크)
- [ ] 상태만 변경하나요? (대기 → 처리중)
- [ ] 단순한 데이터 변환인가요? (타임존 정규화)

#### ❌ **서비스로 분리해야 하는 경우**
- [ ] if-elif 조건이 3개 이상인가요?
- [ ] TimeUtils 같은 복잡한 유틸리티를 사용하나요?
- [ ] 여러 필드를 조합해서 계산하나요?
- [ ] 비즈니스 규칙이 들어가나요?
- [ ] 테스트하기 복잡한가요?

### 🎯 **분리 우선순위**

#### 🚨 **우선순위 1: 즉시 분리**
1. `calculate_effective_candle_count()` - 복잡한 겹침 계산
2. `get_effective_end_time()` - 복잡한 조건부 로직
3. 복잡한 시간 계산 로직들

#### ⚠️ **우선순위 2: 미래 분리 고려**
1. `get_time_source()` - 조건부 로직이지만 단순함
2. `has_complete_time_info()` - 현재는 단순하나 확장 가능성
3. TimeUtils 의존성들 - 단순한 정규화는 허용

#### ✅ **우선순위 3: 모델에 유지**
1. `mark_processing()`, `mark_completed()` - 단순 상태 변경
2. `is_pending()`, `is_completed()` - 단순 상태 확인
3. 기본 검증 로직들

---

## 🛠️ 실제 마이그레이션 예시

### 📝 **Step 1: 서비스 클래스 생성**
```python
# chunk_analysis_service.py
from typing import Optional
from datetime import datetime
from .models.candle_business_models import ChunkInfo, OverlapStatus
from .time_utils import TimeUtils

class ChunkAnalysisService:
    """청크 분석 및 계산 서비스"""

    @staticmethod
    def calculate_effective_candle_count(chunk: ChunkInfo) -> int:
        """겹침 상황을 반영한 실제 확보 캔들 수 계산"""
        # 기존 모델의 복잡한 로직을 여기로 이동
        pass

    @staticmethod
    def determine_effective_end_time(chunk: ChunkInfo) -> Optional[datetime]:
        """청크의 실제 종료 시각 결정"""
        # 기존 get_effective_end_time 로직을 여기로 이동
        pass
```

### 📝 **Step 2: 모델 단순화**
```python
# candle_business_models.py
class ChunkInfo:
    # 계산 결과 저장용 필드 추가
    effective_candle_count: Optional[int] = None
    effective_end_time: Optional[datetime] = None

    # 기존 복잡한 메서드 제거하고 단순한 getter/setter로 교체
    def set_effective_candle_count(self, count: int) -> None:
        self.effective_candle_count = count

    def get_effective_candle_count(self) -> int:
        return self.effective_candle_count or 0

    def set_effective_end_time(self, end_time: datetime) -> None:
        self.effective_end_time = end_time

    def get_effective_end_time(self) -> Optional[datetime]:
        return self.effective_end_time
```

### 📝 **Step 3: 사용하는 곳에서 서비스 호출**
```python
# chunk_processor.py
from .services.chunk_analysis_service import ChunkAnalysisService

class ChunkProcessor:
    def process_chunk(self, chunk: ChunkInfo) -> None:
        # 서비스에서 계산
        candle_count = ChunkAnalysisService.calculate_effective_candle_count(chunk)
        end_time = ChunkAnalysisService.determine_effective_end_time(chunk)

        # 모델에 결과 저장
        chunk.set_effective_candle_count(candle_count)
        chunk.set_effective_end_time(end_time)
```

---

## 🌟 장기적 이익

### 📈 **서비스 분리 후 얻는 것들**

#### 1. **테스트 용이성**
```python
# 서비스는 독립적으로 테스트 가능
def test_calculate_candle_count():
    chunk = create_test_chunk()
    result = ChunkAnalysisService.calculate_effective_candle_count(chunk)
    assert result == 150
```

#### 2. **재사용성**
```python
# 다른 곳에서도 같은 계산 로직 사용 가능
count1 = ChunkAnalysisService.calculate_effective_candle_count(chunk1)
count2 = ChunkAnalysisService.calculate_effective_candle_count(chunk2)
```

#### 3. **유지보수성**
- 비즈니스 로직 변경 시 서비스만 수정
- 모델은 안정적으로 유지
- 영향 범위가 명확함

#### 4. **확장성**
```python
# 새로운 계산 로직 추가가 쉬움
class ChunkAnalysisService:
    @staticmethod
    def calculate_effective_candle_count(chunk: ChunkInfo) -> int:
        # 기존 로직
        pass

    @staticmethod
    def calculate_performance_metrics(chunk: ChunkInfo) -> dict:
        # 새로운 기능 추가
        pass
```

---

## 🎓 학습 단계별 접근

### 🥉 **초급자**: 명확한 신호 확인
- if-elif가 3개 이상이면 서비스 고려
- TimeUtils 같은 복잡한 도구 사용 시 주의
- 단순한 getter/setter는 모델에 유지

### 🥈 **중급자**: 비즈니스 로직 식별
- 도메인 규칙인지 데이터 조작인지 구분
- 테스트 복잡도로 판단
- 재사용 가능성 고려

### 🥇 **고급자**: 아키텍처 일관성
- DDD 계층 간 의존성 방향 확인
- 단일 책임 원칙 적용
- 미래 확장성 고려한 설계

---

## 📞 도움이 필요할 때

### 🤔 **판단이 어려운 경우**
1. **GitHub Copilot에게 질문**: "이 기능이 서비스로 가야 하나요?"
2. **체크리스트 활용**: 위의 실전 체크리스트 사용
3. **작은 단위로 시작**: 가장 복잡한 것부터 분리

### 📚 **추가 학습 자료**
- `docs/DDD_아키텍처_패턴_가이드.md` - DDD 기본 개념
- `docs/DEVELOPMENT_GUIDE.md` - 전체 개발 가이드
- `.github/copilot-instructions.md` - Copilot 활용법

---

## ✨ 마무리

**기억하세요**:
- 모델 = 데이터 보관소 📦
- 서비스 = 비즈니스 처리소 🏭

복잡한 계산이나 비즈니스 로직은 서비스에서, 간단한 데이터 저장과 조회는 모델에서!

**시작은 작게, 점진적으로 개선하세요! 🚀**
