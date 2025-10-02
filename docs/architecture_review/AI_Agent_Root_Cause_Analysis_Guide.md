# 🎯 AI 에이전트 근본 원인 분석 가이드

> **목적**: AI 에이전트가 지엽적 수정 대신 근본 원인을 찾도록 하는 체계적 가이드
> **적용 시점**: 에러 발생 시, 방어적 코드 작성 전 필수 실행
> **원칙**: "증상 치료 < 근본 치료"

---

## 🚨 필수 실행 규칙

### Rule 1: **방어적 코드 금지령**

```python
# ❌ 절대 금지: 증상을 숨기는 방어적 코드
if hasattr(obj, 'method'):
    obj.method()
else:
    logger.warning("타입 불일치 - 임시 처리")

# ✅ 올바른 접근: 근본 원인부터 해결
# 1. 왜 obj가 잘못된 타입인가?
# 2. 의존성 주입 과정에서 무엇이 잘못되었나?
# 3. 설계 패턴에 문제가 있는가?
```

### Rule 2: **3-Why 분석 의무화**

모든 에러에 대해 3번의 "왜?"를 던져야 함:

1. **Why 1**: "왜 이 에러가 발생했는가?" → 직접적 원인
2. **Why 2**: "왜 그 상황이 만들어졌는가?" → 구조적 원인
3. **Why 3**: "왜 그런 구조가 되었는가?" → 설계적 원인

### Rule 3: **아키텍처 우선 원칙**

에러 해결 시 항상 다음 순서로 접근:

1. **Architecture Level** (최우선): 전체 시스템 설계 검토
2. **Pattern Level**: 사용된 디자인 패턴의 올바른 적용 여부
3. **Implementation Level**: 개별 코드 구현의 정확성
4. **Symptom Level** (최후): 증상에 대한 직접적 대응

---

## 📊 근본 원인 분석 매트릭스

### 🔍 **에러 분류 및 접근법**

| 에러 유형 | 증상적 접근 (❌) | 근본적 접근 (✅) | 분석 시간 |
|----------|-----------------|----------------|----------|
| **타입 에러** | hasattr() 체크 | DI 패턴 검증 | 30분 |
| **ImportError** | try/except 처리 | 의존성 구조 분석 | 20분 |
| **AttributeError** | 방어적 체크 | 객체 생성 과정 추적 | 25분 |
| **순환 참조** | 임시 회피 | 아키텍처 재설계 | 60분 |

### 🎯 **분석 깊이 결정 기준**

#### **Shallow Analysis (피해야 할 접근)**

- 에러 메시지만 보고 즉시 수정
- 해당 함수/메서드만 수정
- 조건문으로 예외 상황 처리
- 로그 추가로 문제 추적

#### **Deep Analysis (지향해야 할 접근)**

- 전체 시스템 컨텍스트에서 분석
- 유사한 패턴의 다른 구현 사례 비교
- 공식 문서와의 패턴 일치성 검증
- 아키텍처 원칙 준수 여부 확인

---

## 🔧 실제 적용 사례: DI Container 에러

### 📝 **Case Study: `.provider` 패턴 오류**

#### **❌ 증상적 접근 (실제로 했던 실수)**

```python
# 1단계: 에러 발생
# 'Factory' object has no attribute 'load_api_keys'

# 2단계: 방어적 코드 추가 (잘못된 접근)
if hasattr(self.api_key_service, 'load_api_keys'):
    api_keys = self.api_key_service.load_api_keys()
else:
    self.logger.warning(f"타입 불일치: {type(self.api_key_service)}")

# 3단계: 더 많은 방어 코드 추가
try:
    result = self.api_key_service.load_api_keys()
except AttributeError:
    self.logger.error("API Key Service 메서드 없음")
    return None
```

**문제점**: 증상만 숨기고 근본 원인은 그대로 둠

#### **✅ 근본적 접근 (올바른 방법)**

```python
# 1단계: 3-Why 분석
# Why 1: 왜 Factory 객체가 반환되었나?
# → PresentationContainer에서 .provider 패턴 사용

# Why 2: 왜 .provider 패턴을 사용했나?
# → dependency-injector 패턴을 잘못 이해함

# Why 3: 왜 표준 패턴 확인을 안 했나?
# → 공식 문서 검토 없이 추측으로 구현

# 2단계: 아키텍처 레벨 수정
# Before: external_container.provided.theme_service.provider
# After:  external_container.theme_service

# 3단계: 패턴 표준화
# 전체 프로젝트의 DI 패턴 일관성 확인 및 표준화
```

**결과**: 단일 패턴 수정으로 완전 해결

---

## 📋 AI 에이전트 행동 가이드라인

### 🎯 **에러 발생 시 필수 프로토콜**

#### **Phase 1: 전체 관점 확보 (15분)**

```bash
# 1. 아키텍처 맵핑
- 관련된 모든 컴포넌트 식별
- 의존성 체인 전체 추적
- 설계 패턴 및 아키텍처 원칙 확인

# 2. 패턴 일관성 검증
- 유사한 구현 사례 비교
- 공식 문서/베스트 프랙티스 확인
- 프로젝트 표준과의 일치성 검토
```

#### **Phase 2: 근본 원인 가설 (10분)**

```bash
# 3-Why 분석 수행
Why 1: 직접적 원인 (코드 레벨)
Why 2: 구조적 원인 (설계 레벨)
Why 3: 아키텍처적 원인 (시스템 레벨)

# 수정 범위 예측
- 단일 파일 vs 다중 컴포넌트
- 패턴 변경 vs 구현 수정
- 지역적 vs 전역적 영향
```

#### **Phase 3: 해결 방법 결정 (5분)**

```bash
# 해결 접근법 우선순위
1. 아키텍처/패턴 수정 (최우선)
2. 설계 원칙 준수
3. 표준 라이브러리 패턴 적용
4. 증상 대응 (최후 수단)
```

### 🚫 **금지 행동 목록**

1. **즉석 방어 코드**: `try/except`, `hasattr()`, `if isinstance()` 남용
2. **증상 숨기기**: 로그만 추가하고 근본 원인 방치
3. **부분적 수정**: 전체 맥락 고려 없는 지엽적 변경
4. **임시 해결**: "나중에 수정"을 전제로 한 임시방편
5. **패턴 파괴**: 기존 아키텍처 원칙을 위반하는 수정

### ✅ **권장 행동 목록**

1. **전체적 관점**: 시스템 전반의 일관성 고려
2. **표준 준수**: 공식 문서 및 베스트 프랙티스 확인
3. **패턴 일관성**: 프로젝트 내 동일한 패턴 적용
4. **아키텍처 준수**: 설계 원칙(DDD, MVP 등) 유지
5. **문서화**: 수정 이유와 근거 명확히 기록

---

## 🎯 구체적 적용 사례들

### **Case 1: Import Error**

```python
# ❌ 증상적 접근
try:
    from some_module import SomeClass
except ImportError:
    SomeClass = None

# ✅ 근본적 접근
# 1. 왜 import가 실패하는가?
# 2. 의존성 구조가 올바른가?
# 3. 패키지 구조 설계에 문제가 있는가?
# → 의존성 구조 재설계
```

### **Case 2: Configuration Error**

```python
# ❌ 증상적 접근
config_value = config.get('key', 'default_value')
if not config_value:
    config_value = 'fallback_value'

# ✅ 근본적 접근
# 1. 왜 config가 없는가?
# 2. Configuration 로딩 과정이 올바른가?
# 3. Config 아키텍처 설계가 적절한가?
# → Configuration 시스템 표준화
```

### **Case 3: Circular Dependency**

```python
# ❌ 증상적 접근
# 순환 참조 회피를 위한 지연 import
def get_service():
    from .service import SomeService
    return SomeService()

# ✅ 근본적 접근
# 1. 왜 순환 참조가 발생하는가?
# 2. 모듈 간 의존성 설계가 올바른가?
# 3. Dependency Injection 아키텍처가 적절한가?
# → DI Container 도입 또는 아키텍처 재설계
```

---

## 📊 성공 지표 및 측정

### 🎯 **근본 원인 분석 성공률**

**측정 기준:**

- **Time to Root Cause**: 근본 원인 발견까지 소요 시간
- **Fix Durability**: 수정 후 재발 방지 정도
- **Code Quality**: 방어적 코드 제거 정도
- **Architecture Compliance**: 설계 원칙 준수 정도

**목표 지표:**

- 방어적 코드 사용률: < 5%
- 근본 원인 발견 시간: < 30분
- 수정 후 재발률: < 1%
- 아키텍처 원칙 준수율: > 95%

### 📈 **개선 방안**

1. **체크리스트 자동화**: AI 에이전트가 자동으로 실행할 분석 체크리스트
2. **패턴 검증 도구**: 표준 패턴과의 일치성 자동 검증
3. **아키텍처 준수 검증**: DDD, MVP 등 원칙 위반 자동 탐지
4. **근본 원인 분석 템플릿**: 3-Why 분석 자동 실행 프레임워크

---

## 💡 결론 및 적용 방안

### 🎯 **AI 에이전트 개선을 위한 핵심 원칙**

1. **"Fix the Cause, Not the Symptom"**: 원인 치료 우선
2. **"Architecture First"**: 아키텍처 관점에서 접근
3. **"Pattern Consistency"**: 패턴 일관성 유지
4. **"Standard Compliance"**: 공식 표준 준수
5. **"Holistic View"**: 전체적 관점 유지

### 🔧 **실행 방안**

이 가이드를 AI 에이전트의 **필수 실행 프로토콜**로 적용:

1. **에러 발생 시**: 자동으로 3-Why 분석 실행
2. **방어적 코드 감지 시**: 근본 원인 분석 강제 실행
3. **패턴 불일치 발견 시**: 표준 패턴 적용 우선
4. **아키텍처 위반 감지 시**: 설계 원칙 준수 강제

**이러한 가이드라인을 통해 AI 에이전트가 지엽적 수정 대신 근본적 해결에 집중할 수 있습니다.**

---

**문서 버전**: v1.0
**작성일**: 2025년 10월 1일
**목적**: AI 에이전트의 근본 원인 분석 능력 향상
**적용 범위**: 모든 에러 및 문제 해결 상황
