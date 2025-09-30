# 📋 TASK_FUTURE_01: 로깅 메시지 중복 제거

## 🎯 태스크 목표

**ApplicationLoggingService의 중복된 컴포넌트 식별 정보 제거**

- Logger Name과 Component Tag에서 동일한 컴포넌트 이름 중복 문제 해결
- 로깅 메시지 가독성 향상 및 정보 효율성 개선

## 📊 현재 문제점

### 중복 발생 패턴

```
DEBUG | upbit.QuietHoursWidget | [QuietHoursWidget] 🔇 QuietHoulsWidget 초기화
       ├─ Logger Name          ├─ Component Tag    ├─ Message Content
       └─ 중복 1               └─ 중복 2           └─ 중복 3
```

### 논리적 문제

- 동일한 정보(`QuietHoursWidget`)가 3번 반복
- 정보 중복으로 인한 가독성 저하
- 로깅 시스템 설계 원칙 위반

## 🛠️ 해결 방안

### Option A: Component Tag 제거 (권장)

```python
# ApplicationLoggingService 수정
class PresentationLoggerAdapter:
    def debug(self, message: str, *args, **kwargs):
        # [Component] 태그 제거
        self._logger.debug(message, *args, **kwargs)
```

### Option B: Logger Name 단순화

```python
# 컴포넌트별로 단순한 logger 이름 사용
logger = create_component_logger("QuietHours")  # 축약형
```

## 🎯 예상 결과

### 개선 후

```
DEBUG | upbit.QuietHoursWidget | 🔇 초기화 완료
```

## 📁 수정 파일 위치

- `upbit_auto_trading/application/services/logging_application_service.py`
- PresentationLoggerAdapter 클래스의 로깅 메서드들

## ⏰ 예상 소요 시간

- 30분 이내 (간단한 로직 수정)

## 🔗 발견 경위

- Widget DI 작업 중 로깅 메시지 검토 과정에서 발견
- 논리적 중복 패턴 인식 및 품질 개선 필요성 확인

---

**우선순위**: 낮음 (품질 개선)
**카테고리**: 로깅 시스템 개선
**발견일**: 2025-09-29
**등록자**: Factory 패턴 작업 중 발견
