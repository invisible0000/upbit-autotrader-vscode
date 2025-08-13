# 🔧 로깅 관리 UI 위젯 리팩토링
**Priority**: HIGH
**Status**: ACTIVE
**Created**: 2025-08-12 14:10
**Assignee**: GitHub Copilot

## 📋 **태스크 개요**
기존 로깅 관리 시스템을 올바른 위젯 구조로 리팩토링하여 설정 파일 기반으로 전환

## 🎯 **목표**
- [x] 문제 분석 완료
- [ ] 위젯 구조 리팩토링 (3개 위젯)
- [ ] 설정 파일 통합
- [ ] 레거시 파일 정리
- [ ] 테스트 및 검증

## 📐 **UI 구조**
```
┌─────────────┬───────────────────────────┐
│             │      로그 뷰어              │
│  로깅 설정   │    (우측 상단)             │
│  (좌측)     │                           │
│             ├───────────────────────────┤
│             │     콘솔 뷰어              │
│             │    (우측 하단)             │
└─────────────┴───────────────────────────┘
   비율 1:2       우측 내부 비율 2:1
```

## 📂 **작업 항목**

### Phase 1: 위젯 분리 (✅ 완료)
- [x] **1.1** `logging_settings_widget.py` 생성 - **완료**
  - [x] 로그 레벨 설정
  - [x] 콘솔 출력 토글
  - [x] 로그 스코프 설정
  - [x] 파일 로깅 설정
  - [x] 컴포넌트 집중 설정

- [x] **1.2** `log_viewer_widget.py` 생성 - **완료**
  - [x] 로그 메시지 표시 영역
  - [x] 자동 스크롤 기능
  - [x] 로그 필터링
  - [x] 로그 저장 기능

- [x] **1.3** `console_viewer_widget.py` 생성 - **완료**
  - [x] 콘솔 출력 표시 영역
  - [x] 실시간 콘솔 캡처
  - [x] 콘솔 내용 지우기

### Phase 2: 메인 뷰 통합 (✅ 완료)
- [x] **2.1** `logging_management_view.py` 수정 - **완료**
  - [x] 기존 파일 백업 (logging_management_view_backup.py)
  - [x] 3개 위젯 레이아웃 구성
  - [x] 스플리터 비율 설정 (1:2, 2:1)
  - [x] 위젯 간 시그널 연결

- [x] **2.2** MVP 패턴 Presenter 백업 및 재작성 - **완료**
  - [x] 기존 Presenter 백업 (logging_management_presenter_backup.py)
  - [x] Config 파일 기반 로직 구현
  - [x] 실시간 설정 적용
  - [x] 이벤트 핸들링

### Phase 3: UI 테스트 및 검증 (✅ 완료)
- [x] **3.1** 통합 테스트 실행 - **✅ 완료**
  - [x] 메인 View 파일 재작성 (DDD/MVP 패턴 엄격 준수)
  - [x] 메인 Presenter 파일 재작성 (Config 파일 기반)
  - [x] 메인 UI 실행 (`python run_desktop_ui.py`) - **✅ 성공**
  - [x] 3-위젯 레이아웃 확인 - **✅ 정상 표시**
  - [x] 설정 변경 동작 확인 - **✅ Config 파일 기반 동작**
  - [x] UI 프리징 방지 확인 - **✅ 환경변수 의존성 제거 완료**

### Phase 4: UI 개선 및 최적화 (✅ 완료)
- [X] **4.1** Presenter 로직 단순화 - **✅ 완료**
  - [X] 불필요한 로그 저장 기능 제거 완료
  - [X] 실시간 로그 읽기만 유지 (Infrastructure 로깅 시스템 활용)
  - [X] LoggingConfigManager의 올바른 메서드 사용 (`get_current_config`, `update_logging_config`)
  - [X] 기존 파일 백업 (`logging_management_presenter_backup.py`)
  - [X] DDD/MVP 패턴 엄격 준수하며 단순화 완료
  - [X] 실시간 로그 모니터링 타이머 구현 (1초 간격)

- [X] **4.2** 로그 뷰어 UI 개선 - **✅ 완료**
  - [X] 로그 하이라이트 기능 추가 (`log_syntax_highlighter.py` 구현)
  - [X] 폰트 크기 조절 기능 추가 (6-20px 범위)
  - [X] 로그 레벨별 색상 구분 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - [X] 타임스탬프, 컴포넌트명, 특수 메시지 이모지 강조
  - [X] 테마 시스템 연동 (다크/라이트 테마 자동 전환)

- [X] **4.3** 환경 프로파일 지연 로딩 최적화 - **✅ 완료**
  - [X] EnvironmentProfilePresenter 지연 초기화 구현
  - [X] EnvironmentProfileView showEvent 기반 지연 로딩 구현
  - [X] 프로파일 탭 미사용시 config YAML 탐색 방지
  - [X] 로그 노이즈 대폭 감소 (ProfileMetadataService DEBUG 로그 최소화)

### Phase 5: 실시간 로그 연결 및 최종 테스트 (🔄 진행중)
- [x] **5.1** 실시간 로그 스트리밍 연결 - **✅ 완료**
  - [x] LoggingManagementPresenter와 LogViewerWidget 시그널 연결
  - [x] Infrastructure 로깅 시스템 실시간 로그 파일 모니터링
  - [x] 새 로그 라인 추가시 구문 강조 자동 적용
  - [x] 자동 스크롤 기능 완성

- [x] **5.2** 로그 뷰어 기본 설정 조정 - **✅ 완료**
  - [x] 폰트 크기 기본값 12px로 변경
  - [x] 초기 로드시 현재 세션 로그 표시
  - [x] 로그 내용 복사 기능 확인 (QTextEdit 표준 기능 Ctrl+C)
---
##### er_subTASK_00_**로깅설정 ui 및 기능 개선**

**Priority**: HIGH | **Status**: ACTIVE | **Created**: 2025-08-12 16:35

#### 🎯 **개선 목표**
현재 `logging_settings_widget.py`가 `logging_config.yaml`의 설정 항목을 완전히 반영하지 못하고 있는 문제를 해결하고, 레거시 기능을 정리하여 사용자 친화적인 로깅 설정 UI로 개선

#### 📋 **작업 분류**

### **Phase A: 기본 설정 UI 완성 (우선순위: 최고)**

- [x] **A.1** context 환경 콤보박스 추가 - **✅ 완료**
  - [x] `development`, `production`, `testing`, `staging`, `debug`, `demo` 옵션
  - [x] 현재 설정 파일의 `context` 필드와 연동
  - [x] 폼 레이아웃에 "실행 환경:" 라벨로 추가

- [x] **A.2** console_output 체크박스를 콤보박스로 변경 (통일성) - **✅ 완료**
  - [x] `true` (항상 출력), `false` (출력 안함), `auto` (오류시만) 옵션
  - [x] 기존 체크박스 제거 후 콤보박스로 교체
  - [x] 시그널 연결 `console_output_changed` 수정
  - [x] Boolean 호환성 유지 (기존 설정 파일과 호환)

- [x] **A.3** 파일 로깅 레벨 콤보박스 추가 - **✅ 완료**
  - [x] DEBUG, INFO, WARNING, ERROR, CRITICAL 옵션
  - [x] 현재 설정 파일의 `file_logging.level` 필드와 연동
  - [x] 파일 로깅 그룹 내부에 추가
  - [x] get/set 메서드 구현 및 시그널 연결

**📝 Phase A.2 참고사항:**
- `auto` 옵션은 UI에 추가했지만 Infrastructure Layer 미지원 (향후 확장 대비)
- 현재는 `true`/`false`만 실제 동작함

### **Phase B: 고급 설정 간소화 (우선순위: 중간)**

- [x] **B.1** component_focus 개선 - 다이얼로그 방식 ✅ **완료**
  - [x] 독립적인 다이얼로그 시스템 구축 (`dialogs/component_selector/`)
  - [x] 실제 컴포넌트 스캔 기능 구현 (`ComponentDataScanner`)
  - [x] 4계층 DDD 아키텍처 기반 컴포넌트 분류
  - [x] 검색 및 필터링 기능 포함
  - [x] 에러 격리로 기본 로깅 설정에 영향 없음
  - [x] 독립 테스트 환경 완성 (`test_component_selector_dialog.py`)
  - [x] 로깅 설정 위젯에 다이얼로그 통합 완료
  - [x] 이모티콘 중복 문제 해결 및 컴포넌트명 정제 완료

- [x] **B.2** advanced 섹션 기능 확인 및 정리 - **✅ 완료**
  - [x] `feature_development` 필드 용도 확인 (Infrastructure Layer 코드 분석)
  - [x] `performance_monitoring` 필드 용도 확인 (실제 사용 여부)
  - [x] `llm_briefing_enabled` 완전 제거 결정 (UI에서 숨김)
  - [x] 작업 세분화: B.2.1 (성능 모니터링 UI 추가), B.2.2 (LLM 관련 정리)

- [x] **B.2.1** performance_monitoring 체크박스 추가 - **✅ 완료**
  - [x] "고급 설정" 그룹에 성능 모니터링 체크박스 추가
  - [x] 시그널 연결 및 get/set 메서드 구현
  - [x] Infrastructure Layer의 PerformanceMonitor 연동
  - [x] advanced 섹션과 연동하여 설정 저장/로드

- [x] **B.2.2** LLM 관련 설정 UI에서 제거 - **✅ 완료**
  - [x] `llm_briefing_enabled` UI 처리 안함 (숨김) - 이미 UI에 없음
  - [x] `briefing_update_interval` UI 처리 안함 (숨김) - 이미 UI에 없음
  - [x] YAML 파일에는 유지하되 UI에서만 제거 - 현재 상태 유지

### **Phase C: 파일 로깅 시스템 개선 (우선순위: 중간)**

- [x] **C.1** 파일 로깅 설정 UI 개선 - **✅ 완료**
  - [x] 경로 설정을 "폴더 경로"로 변경 (현재는 파일 경로)
  - [x] 파일명 자동화 안내 텍스트 추가: "파일명은 자동으로 session_[날짜]_[시간]_PID[pid].log 형식으로 생성됩니다"
  - [x] 백업 시스템 안내 추가: "application.log로 자동 병합, 백업 관리"
  - [x] **C.1.1** 설명 텍스트를 '?' 헬프 버튼으로 교체 - **✅ 완료**
  - [x] 저장 경로 텍스트박스 우측에 헬프 버튼 추가
  - [x] 모든 헬프 버튼 스타일링: 패딩 제거, '?' 텍스트 표시, 우측 정렬

- [x] **C.1.1** UI 공간 최적화 - 헬프 버튼 시스템 구현 - **✅ 완료**
  - [x] 컴포넌트 집중 설명 텍스트 → '?' 버튼으로 교체
  - [x] 성능 모니터링 설명 텍스트 → '?' 버튼으로 교체
  - [x] 헬프 버튼 클릭 시 상세 설명 메시지박스 표시
  - [x] UI 레이아웃 정리 및 공간 확보
  - [x] 20x20 작은 크기의 '?' 버튼으로 공간 효율성 극대화

- [x] **C.2** Infrastructure Layer 파일 로깅 통합 확인 - **✅ 완료**
  - [x] 현재 이중 구현 상태 분석 (session 로깅 vs UI 위젯 로깅)
  - [x] 중복 로그 파일 생성 방지 방안 수립
  - [x] 기존 session 로깅 시스템과 UI 설정 연동
  - [x] RotatingFileHandler 백업 시스템 구현
  - [x] upbit_auto_trading.log → logs 폴더 경로로 변경
  - [x] application.log 자동 백업 및 순환 삭제 로직 구현
  - [x] YAML 중복 설정 문제 해결 (file_logging, advanced 중복 제거)
  - [x] UI 설정 로딩 로직 수정 (logging 섹션 구조 대응)
  - [x] 레거시 briefing/dashboard/configuration 폴더 제거
  - [x] 환경변수 시스템 완전 제거 및 YAML 기반 통합

### **Phase D: 레거시 완전 제거 + 단일 로깅 시스템 통합 (우선순위: 최고)** - **✅ 완료**

- [x] **D.1** LLM 브리핑 관련 코드 제거 - **✅ 완료**
  - [x] UI에서 LLM 브리핑 설정 완전 숨김
  - [x] `briefing_update_interval` 필드 UI에서 제거
  - [x] Infrastructure Layer의 LLM 관련 코드 비활성화
  - [x] `briefing/` 폴더 전체 제거
  - [x] `dashboard/` 폴더 제거 (LLM 시스템)
  - [x] `integration/` 폴더 제거 (환경변수 시스템)

- [x] **D.2** 사용하지 않는 고급 설정 정리 - **✅ 완료**
  - [x] `configuration/logging_config.py` 레거시 파일 제거
  - [x] `configuration/enhanced_config.py` LLM 전용 설정 제거
  - [x] 설정 파일에서 deprecated 필드 마킹
  - [x] 환경변수 기반 코드를 YAML 설정 파일 기반으로 완전 전환
  - [x] `run_desktop_ui.py`에서 레거시 Dashboard import 제거

### **Phase E: UX/UI 완전 개선 (우선순위: 최고)** - **✅ 완료**

- [x] **E.1** 변경사항 추적 및 안전장치 - **✅ 완료**
  - [x] 설정 변경사항 실시간 감지 및 표시
  - [x] "설정 적용" 버튼 스마트 활성화/비활성화
  - [x] 새로고침 시 변경사항 손실 경고
  - [x] 기본값 복원 확인 다이얼로그 추가

- [x] **E.2** 버튼 레이아웃 및 크기 최적화 - **✅ 완료**
  - [x] 균등한 버튼 크기 및 간격 설정
  - [x] 변경사항 라벨을 버튼 아래로 배치
  - [x] 윈도우 크기 변경에 반응하는 레이아웃
  - [x] 로깅 설정 위젯 크기 제한 해제 (최대 400px → 비례 확장)

- [x] **E.3** 로깅 시스템 백업 및 순환 삭제 - **✅ 완료**
  - [x] RotatingFileHandler 구현으로 자동 백업
  - [x] application.log.1, .2, .3, .4, .5 순환 관리
  - [x] 설정된 백업 개수 (5개) 초과 시 자동 삭제
  - [x] 최대 크기 (10MB) 도달 시 자동 로테이션

#### ⚠️ **주의사항**
- **복잡도 관리**: 각 Phase는 독립적으로 실행 가능하도록 설계
- **테스트 필수**: 각 Phase 완료 후 `python run_desktop_ui.py`로 검증
- **백업 보장**: 기존 파일 수정 전 반드시 백업 생성
- **설정 호환성**: 기존 `logging_config.yaml` 구조 유지

#### 🚀 **즉시 시작 권장 순서**
1. **Phase A.1** → **A.2** → **A.3** (기본 UI 완성)
2. **Phase B.1** (component_focus 개선)
3. **Phase C.1** (파일 로깅 UI 개선)
4. **Phase B.2**, **D.1** (레거시 정리)

---

- [x] **5.3** 콘솔 뷰어 실시간 연결 - **✅ 완료**
  - [x] 콘솔 출력 실시간 캡처 구현
  - [x] 콘솔 내용 필터링 기능 (전체/ERROR/WARNING/DEBUG/INFO)
  - [x] 콘솔 지우기 기능 연결
  - [x] 콘솔뷰어 최대 라인 수 1000라인으로 증가
  - [x] 한글 하이라이트 개선 (단일 문자 매칭 방지)
  - [x] 중복 로딩 메시지 방지

- [x] **5.4** 설정 적용 및 저장 테스트 - **✅ 완료**
  - [x] Infrastructure 로깅 시스템 즉시 반영 메커니즘 완전 구현
  - [x] LoggingManagementPresenter가 LoggingService의 config_manager 사용하도록 수정
  - [x] 콘솔 출력, 로그 레벨, 컴포넌트 집중 등 모든 설정 즉시 반영 확인
  - [x] Config 파일 기반 설정 저장/복원 검증
  - [x] 프로그램 재시작 후 설정 유지 확인

- [ ] **5.5** 통합 테스트 및 검증
  - [ ] 3-위젯 레이아웃 안정성 확인
  - [ ] 테마 변경시 정상 동작 확인
  - [ ] 전체 기능 통합 테스트
  - [ ] 성능 및 메모리 사용량 확인

- [ ] **4.3** 콘솔 뷰어 UI 개선
  - [ ] 실시간 콘솔 모니터링
  - [ ] 출력 포맷팅 개선

### Phase 6: 레거시 정리
- [ ] **3.1** 불필요 파일 제거
  - [ ] 환경변수 기반 코드 제거
  - [ ] LLM 관련 설정 제거
  - [ ] 사용하지 않는 위젯 정리

- [ ] **3.2** 코드 정리
  - [ ] Import 정리
  - [ ] 사용하지 않는 메서드 제거
  - [ ] 문서 업데이트

### Phase 4: 테스트 및 검증
- [ ] **4.1** 기능 테스트
  - [ ] 설정 변경 동작 확인
  - [ ] 파일 저장/로드 확인
  - [ ] UI 반응성 확인

- [ ] **4.2** 통합 테스트
  - [ ] 프로그램 재시작 후 설정 유지 확인
  - [ ] 프로파일 시스템과 연동 확인

## ⚠️ **위험 요소**
- 기존 로깅 시스템과의 호환성
- UI 프리징 방지
- 설정 파일 충돌 방지

## 📝 **작업 노트**
- 환경변수 → 설정 파일 기반으로 전환 중
- UI 프리징 문제 해결 필요
- 로그 파일 경로 하드코딩 문제 해결

## ✅ **완료 기준**
- [ ] 3개 위젯이 올바른 레이아웃으로 배치
- [ ] 설정 변경이 즉시 반영
- [ ] 프로그램 재시작 후 설정 유지
- [ ] UI 프리징 없음
- [ ] 레거시 코드 완전 제거
