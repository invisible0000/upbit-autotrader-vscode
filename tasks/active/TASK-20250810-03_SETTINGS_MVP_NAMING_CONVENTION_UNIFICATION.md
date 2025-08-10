# 🚨 **TASK-20250810-03: Settings 탭 MVP 명명 규칙 통일화 (긴급)**

**작성일**: 2025년 8월 10일
**우선순위**: 🔴 **긴급** (아키텍처 일관성 문제)
**상태**: 🔄 **진행중**

---

## 📋 **태스크 개요**

### **🎯 목표**
TASK-20250810-02 완료 후 발견된 MVP 명명 규칙 불일치를 긴급히 해결하여 완전한 아키텍처 일관성을 달성

### **🔍 발견된 문제**
```python
# 현재 불일치 상태
from .api_settings import ApiKeyManagerSecure as ApiKeyManager      # 호환성 우선 전략
from .database_settings import DatabaseSettings                    # 순수 MVP 전략
from .notification_settings import NotificationSettings            # 순수 MVP 전략
```

### **⚠️ 근본 원인**
- **Phase 1**: 순수 MVP 구조 → `DatabaseSettingsView`
- **Phase 2**: 호환성 우선 → `ApiKeyManagerSecure` (기존 클래스명 유지)
- **Phase 3,4**: 완전 리팩토링 → `*SettingsView`

---

## 🎯 **해결 방안: 순수 MVP 통일**

### **전략**: 모든 Phase를 순수 MVP View 클래스명으로 통일

#### **Phase 1: database_settings** ✅ (이미 완료)
- 현재: `DatabaseSettingsView`
- 목표: 유지

#### **Phase 2: api_settings** 🔄 (수정 필요)
- 현재: `ApiKeyManagerSecure` (호환성 어댑터)
- 목표: `ApiSettingsView` (순수 MVP)
- **작업**: 호환성 어댑터 → 순수 MVP View로 변경

#### **Phase 3: ui_settings** ✅ (이미 완료)
- 현재: `UISettingsView`
- 목표: 유지

#### **Phase 4: notification_settings** ✅ (이미 완료)
- 현재: `NotificationSettingsView`
- 목표: 유지

---

## 📋 **실행 계획**

### **🔧 Phase 2 리팩토링**

#### **1. api_settings 구조 분석**
- [ ] 현재 `ApiKeyManagerSecure` 클래스 분석
- [ ] 호환성 어댑터 vs 순수 MVP View 비교
- [ ] settings_screen.py 사용 패턴 확인

#### **2. 순수 MVP 구조로 변환**
- [ ] `ApiKeyManagerSecure` → `ApiSettingsView` 통합
- [ ] 호환성 어댑터 제거
- [ ] MVP 패턴 순수 구현

#### **3. Import 경로 통일**
```python
# 목표 상태
from .api_settings import ApiSettingsView as ApiSettings
from .database_settings import DatabaseSettingsView as DatabaseSettings
from .notification_settings import NotificationSettingsView as NotificationSettings
from .ui_settings import UISettingsView as UISettings
```

#### **4. settings_screen.py 업데이트**
- [ ] 모든 import 경로를 순수 MVP로 변경
- [ ] 호환성 코드 제거
- [ ] 일관된 인터페이스 사용

---

## ✅ **검증 기준**

### **아키텍처 일관성**
- [ ] 모든 설정 탭이 `*SettingsView` 클래스명 사용
- [ ] 호환성 어댑터 완전 제거
- [ ] DDD+MVP 패턴 순수 구현

### **기능 검증**
- [ ] `python run_desktop_ui.py` 정상 실행
- [ ] 모든 설정 탭 정상 동작
- [ ] 기존 기능 완전 호환

### **코드 품질**
- [ ] Import 경로 일관성 달성
- [ ] 명명 규칙 통일
- [ ] 기술부채 제거

---

## 🎯 **예상 결과**

### **통일된 Import 구조**
```python
# settings/__init__.py
from .settings_screen import SettingsScreen
from .api_settings import ApiSettingsView as ApiSettings
from .database_settings import DatabaseSettingsView as DatabaseSettings
from .ui_settings import UISettingsView as UISettings
from .notification_settings import NotificationSettingsView as NotificationSettings
```

### **완전한 MVP 일관성**
- 모든 Phase가 동일한 MVP 패턴 사용
- 호환성 어댑터 제거로 깨끗한 아키텍처
- DDD 원칙 100% 준수

---

## 📊 **진행 상황**

### **체크리스트**
- [ ] **Phase 2 분석**: api_settings 현재 구조 파악
- [ ] **MVP 변환**: ApiKeyManagerSecure → ApiSettingsView
- [ ] **Import 통일**: 모든 Phase 일관된 형식
- [ ] **검증**: 애플리케이션 정상 동작 확인
- [ ] **문서화**: 변경사항 기록

### **예상 소요시간**: 1-2시간
**리스크**: 낮음 (기존 기능은 이미 동작 중)

---

## 🚀 **다음 단계**

**즉시 시작 준비 완료** - Phase 2 api_settings 순수 MVP 변환 작업

이 태스크 완료 후 Settings 폴더는 **완벽한 DDD+MVP 아키텍처 일관성**을 달성하게 됩니다.

**시작하시겠습니까?** 🎯
