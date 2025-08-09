# 🌍 TASK-20250809-01: 환경&로깅 통합 탭 구현

## 📋 **작업 개요**
**목표**: 설정 화면의 핵심 1순위 탭인 "환경&로깅" 탭 구현
**중요도**: ⭐⭐⭐⭐⭐ (최우선)
**예상 기간**: 3-4일
**담당자**: 개발팀

## 🎯 **작업 목표**
- 환경 프로파일 관리와 로깅 설정을 하나의 탭에 통합
- 좌우 6:4 분할 레이아웃으로 사용성 최적화
- 기존 EnvironmentProfileWidget과 로깅 기능 재활용
- 실시간 환경 전환 및 로깅 설정 적용

## 🏗️ **아키텍처 설계**

### **Presentation Layer (MVP)**
```
📁 upbit_auto_trading/ui/desktop/screens/settings/environment_logging/
├── presenters/
│   ├── environment_logging_presenter.py    # 통합 탭 프레젠터
│   ├── environment_profile_presenter.py    # 환경 프로파일 프레젠터
│   └── logging_configuration_presenter.py  # 로깅 설정 프레젠터
├── views/
│   ├── environment_logging_view.py         # 통합 탭 뷰 인터페이스
│   ├── environment_profile_view.py         # 환경 프로파일 뷰 인터페이스
│   └── logging_configuration_view.py       # 로깅 설정 뷰 인터페이스
└── widgets/
    ├── environment_logging_widget.py       # 통합 탭 메인 위젯
    ├── environment_profile_section.py      # 환경 프로파일 섹션
    └── logging_configuration_section.py    # 로깅 설정 섹션
```

### **Application Layer**
```
📁 upbit_auto_trading/application/environment_logging/
├── use_cases/
│   ├── switch_environment_use_case.py      # 환경 전환 Use Case
│   ├── apply_logging_config_use_case.py    # 로깅 설정 적용 Use Case
│   └── get_environment_status_use_case.py  # 환경 상태 조회 Use Case
└── dtos/
    ├── environment_switch_dto.py           # 환경 전환 DTO
    ├── logging_configuration_dto.py        # 로깅 설정 DTO
    └── environment_status_dto.py           # 환경 상태 DTO
```

## 📝 **작업 단계**

### **Sub-Task 1.1: 기반 구조 구축** (1일)
**목표**: 통합 탭의 기본 위젯 구조 생성

#### **Step 1.1.1**: EnvironmentLoggingWidget 생성
- [ ] 메인 통합 위젯 클래스 생성
- [ ] 좌우 6:4 분할 레이아웃 구현
- [ ] 기본 UI 구조 설정
- [ ] MVP 시그널 정의

#### **Step 1.1.2**: 기존 위젯 분석 및 재구성
- [ ] 기존 EnvironmentProfileWidget 분석
- [ ] 기존 EnvironmentVariablesWidget 로깅 부분 분석
- [ ] 재사용 가능 컴포넌트 식별
- [ ] 통합 전략 수립

#### **Step 1.1.3**: 레이아웃 구현
- [ ] QSplitter 기반 좌우 분할 구현
- [ ] 비율 조정 기능 (6:4 기본, 사용자 조정 가능)
- [ ] 최소 크기 제한 설정
- [ ] 반응형 레이아웃 적용

**예상 산출물**:
- `environment_logging_widget.py` (기본 구조)
- `environment_logging_section.py` (좌측 섹션)
- `logging_configuration_section.py` (우측 섹션)

---

### **Sub-Task 1.2: 환경 프로파일 섹션 구현** (1일)
**목표**: 좌측 환경 프로파일 관리 섹션 완성

#### **Step 1.2.1**: 환경 선택 UI 구현
- [ ] Development/Testing/Production 라디오 버튼
- [ ] 현재 환경 시각적 표시 (색상, 아이콘)
- [ ] 환경 설명 텍스트 추가
- [ ] 환경 전환 버튼 구현

#### **Step 1.2.2**: 현재 환경 정보 표시
- [ ] 활성 config 파일 경로 표시
- [ ] 연결된 데이터베이스 정보 표시
- [ ] API 키 설정 상태 표시
- [ ] 실시간 상태 업데이트 구현

#### **Step 1.2.3**: 환경 전환 로직 통합
- [ ] DatabaseProfileManagementUseCase 연동
- [ ] 환경 전환 확인 다이얼로그
- [ ] 전환 중 로딩 상태 표시
- [ ] 전환 완료 후 UI 새로고침

**예상 산출물**:
- `environment_profile_section.py` (완성)
- `environment_switch_dialog.py` (확인 다이얼로그)

---

### **Sub-Task 1.3: 로깅 설정 섹션 구현** (1일)
**목표**: 우측 로깅 설정 관리 섹션 완성

#### **Step 1.3.1**: 기본 로깅 설정 UI
- [ ] 로그 레벨 선택 (DEBUG/INFO/WARNING/ERROR)
- [ ] 콘솔 출력 활성화 체크박스
- [ ] 파일 저장 활성화 체크박스
- [ ] 컨텍스트 설정 (development/production/testing)
- [ ] 스코프 설정 (minimal/normal/verbose)

#### **Step 1.3.2**: 고급 로깅 설정 UI
- [ ] 컴포넌트 포커스 텍스트 입력 (예: TradingEngine)
- [ ] 기능 개발 모드 체크박스
- [ ] LLM 브리핑 활성화 체크박스
- [ ] 로그 파일 크기/로테이션 설정

#### **Step 1.3.3**: 환경변수 연동
- [ ] UPBIT_LOG_LEVEL 환경변수 연동
- [ ] UPBIT_LOG_CONTEXT 환경변수 연동
- [ ] UPBIT_LOG_SCOPE 환경변수 연동
- [ ] UPBIT_CONSOLE_OUTPUT 환경변수 연동
- [ ] UPBIT_COMPONENT_FOCUS 환경변수 연동
- [ ] 실시간 적용 기능 구현

**예상 산출물**:
- `logging_configuration_section.py` (완성)
- `logging_settings_form.py` (설정 폼 위젯)

---

### **Sub-Task 1.4: 통합 및 최적화** (0.5-1일)
**목표**: 전체 탭 통합 및 사용성 최적화

#### **Step 1.4.1**: MVP 패턴 통합
- [ ] EnvironmentLoggingPresenter 구현
- [ ] 뷰와 프레젠터 시그널 연결
- [ ] Use Case와의 통합
- [ ] 에러 처리 로직 구현

#### **Step 1.4.2**: 실시간 연동 구현
- [ ] 환경 전환 시 로깅 설정 자동 적용
- [ ] 로깅 설정 변경 시 즉시 반영
- [ ] 상태 동기화 로직 구현
- [ ] 충돌 방지 로직 구현

#### **Step 1.4.3**: 사용성 개선
- [ ] 툴팁 및 도움말 추가
- [ ] 설정 유효성 검증
- [ ] 사용자 피드백 메시지
- [ ] 키보드 단축키 지원

**예상 산출물**:
- `environment_logging_presenter.py` (완성)
- `environment_logging_use_cases.py` (Use Case 구현)

---

## 🧪 **테스트 계획**

### **Unit Tests**
- [ ] EnvironmentLoggingWidget 단위 테스트
- [ ] 환경 전환 로직 테스트
- [ ] 로깅 설정 적용 테스트
- [ ] MVP 시그널 연결 테스트

### **Integration Tests**
- [ ] DatabaseProfileManagementUseCase 통합 테스트
- [ ] 환경변수 시스템 통합 테스트
- [ ] UI 상호작용 테스트

### **User Acceptance Tests**
- [ ] 환경 전환 사용성 테스트
- [ ] 로깅 설정 변경 테스트
- [ ] 실시간 동기화 테스트

---

## 📊 **성공 기준**

### **기능적 요구사항**
- ✅ Development/Testing/Production 환경 전환 가능
- ✅ 로깅 설정 실시간 적용
- ✅ 환경별 독립적인 설정 관리
- ✅ 사용자 친화적인 UI/UX

### **기술적 요구사항**
- ✅ MVP 패턴 완전 적용
- ✅ DDD 아키텍처 준수
- ✅ Infrastructure Layer v4.0 로깅 시스템 연동
- ✅ 기존 코드와의 호환성 유지

### **성능 요구사항**
- ✅ 환경 전환 시간 < 3초
- ✅ 로깅 설정 적용 시간 < 1초
- ✅ UI 반응성 < 100ms

---

## 🔗 **의존성**

### **Prerequisites**
- DatabaseProfileManagementUseCase (기존 완성)
- Infrastructure Layer v4.0 로깅 시스템 (기존 완성)
- Config YAML 시스템 (기존 완성)

### **Parallel Tasks**
- TASK-20250809-02: 매매설정 탭 (독립적)
- TASK-20250809-03: UI설정 탭 정리 (독립적)

### **Blocking Tasks**
- 없음 (독립적으로 수행 가능)

---

## 🚀 **완료 후 기대효과**

1. **사용성 대폭 개선**: 환경 관리와 로깅이 한 화면에서 관리
2. **개발 효율성 증대**: 빠른 환경 전환으로 디버깅 효율 향상
3. **운영 안정성 강화**: 환경별 독립적인 설정 관리
4. **확장성 확보**: 향후 환경 설정 추가 용이

## 📝 **추가 고려사항**

- **국제화**: 다국어 지원 고려 (향후)
- **접근성**: 스크린 리더 지원 (향후)
- **모바일**: 터치 인터페이스 고려 (향후)
- **백업**: 설정 백업/복원 기능 (향후)
