````prompt
# 🚀 태스크 실행 지시

#file:../../.github/copilot-instructions.md

첨부된 태스크를 숙지하고 즉시 실행에 들어가 주세요.

## 📋 실행 준비 절차

### 1단계: 태스크 분석 및 상황 파악
- [ ] **태스크 문서 완전 숙지**: 목표, 현재 상황, 작업 절차 이해
- [ ] **현재 프로젝트 상태 확인**: 관련 파일들 상태 점검
- [ ] **의존성 및 제약사항 파악**: 선행 조건, 안전장치 확인

### 2단계: 수행 계획 수립
- [ ] **Phase별 작업 순서 확정**: 태스크의 체계적 절차 따라 계획 수립
- [ ] **백업 및 안전장치 준비**: 롤백 계획, 테스트 방법 확정
- [ ] **예상 소요시간 검토**: 현실적 작업 계획 수립

### 3단계: 즉시 실행 개시
- [ ] **첫 번째 Phase 또는 지시한 Phase 시작**
- [ ] **Golden Rules 준수**: DDD, PowerShell, Infrastructure 로깅
- [ ] **단계별 진행**: 각 Phase 완료 시 **📊 태스크 문서 업데이트 + 보고 + ⏳ 승인 대기**

## 🎯 실행 원칙

### 워크플로우
```
태스크 분석 → 상황 파악 → 계획 수립 → Phase별 실행 → 태스크 문서 업데이트 → 보고 → 승인 → 다음 Phase
```

### 📝 **태스크 문서 체크리스트 마킹 규칙** (중요!)
각 작업 단계에서 반드시 태스크 문서의 체크리스트를 업데이트해야 합니다:

#### 작업 시작 전: `[ ]` → `[-]` 변경
- 작업에 들어가기 직전에 해당 항목을 `[-]` (진행 중)로 마킹
- 예: `- [ ] Phase 4.2: ApiSettingsComponentFactory 수정` → `- [-] Phase 4.2: ApiSettingsComponentFactory 수정`

#### 작업 완료 후: `[-]` → `[x]` 변경 + 실행 내용 기록
- 작업 완료 시 해당 항목을 `[x]` (완료)로 마킹
- 해당 항목 바로 아래에 실제 수행한 내용을 간략히 기록
- 예:
```markdown
- [x] Phase 4.2: ApiSettingsComponentFactory 수정
  - ✅ ApplicationServiceContainer 접근 패턴 확인 완료
  - ✅ MVP 패턴 조립 및 Presenter 연결 검증
  - ✅ UI 테스트 통과 (python run_desktop_ui.py)
```

#### 마킹 표준
- **`[ ]`**: 미완료 (미시작 상태)
- **`[-]`**: 진행 중 (현재 작업 중) - **작업 시작 시 즉시 마킹**
- **`[x]`**: 완료 (작업 완료) - **작업 완료 시 즉시 마킹 + 내용 기록**

### 필수 준수사항
- **DDD + MVP**: Presentation → Application → Domain ← Infrastructure
- **Golden Rules**: 에러 숨김 금지, Fail Fast 원칙
- **PowerShell 전용**: Unix 명령어 사용 금지
- **Infrastructure 로깅**: create_component_logger() 필수
- **3-DB 분리**: settings.sqlite3, strategies.sqlite3, market_data.sqlite3
- **Dry-Run false 기본**: 개발 중 실제 실패 케이스 확보 우선

### 진행 방식
각 Phase에서 **반드시** 다음 순서를 준수:

1. **📝 태스크 문서 마킹**: 작업 시작 전 `[ ]` → `[-]` 변경
2. **🔧 작업 실행**: 계획된 세부 작업들 순차 수행
3. **✅ 결과 확인**: 테스트, 검증을 통한 품질 확보
4. **📊 태스크 문서 업데이트**: `[-]` → `[x]` 변경 + 실행 내용 기록
5. **📋 간략 보고**: 완료된 작업, 발견된 이슈, 다음 단계 준비 상태
6. **⏳ 승인 대기**: 사용자 승인 후 다음 Phase 진행

### 🚨 **필수 실행 절차**
```
1. 태스크 문서에서 다음 작업 항목 식별
   ↓
2. `[ ]` → `[-]` 마킹 (작업 시작)
   ↓
3. 실제 작업 수행
   ↓
4. `[-]` → `[x]` 마킹 + 실행 내용 기록 (작업 완료)
   ↓
5. Phase 완료 보고서 작성
   ↓
6. 사용자 승인 대기
```

## 🛠️ 표준 도구 및 명령어

### 검증 명령어 (PowerShell)
```powershell
# UI 통합 검증
python run_desktop_ui.py

# 계층 위반 탐지
Get-ChildItem upbit_auto_trading/domain -Recurse -Include *.py | Select-String -Pattern "import sqlite3|import requests|from PyQt6"

# API 키 상태 확인
python -c "from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import UpbitAuthenticator; auth = UpbitAuthenticator(); print(f'🔐 API 키 인증 가능: {auth.is_authenticated()}')"
```

### 백업 명령어
```powershell
# 파일 백업
Copy-Item "원본파일.py" "원본파일_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').py"

# 롤백
Copy-Item "백업파일.py" "원본파일.py"
```

## 📊 보고 형식

### Phase 완료 보고 템플릿
```markdown
## 📊 Phase {번호} 완료 보고

### ✅ **완료된 작업**
- {구체적 작업 항목들}

### 🎯 **주요 성과**
- {달성한 목표들}

### ⚠️ **발견된 이슈**
- {해결된 문제들}
- {추가로 발견된 문제들}

### 🔍 **검증 결과**
- 테스트 실행: {결과}
- UI 동작: {결과}
- 아키텍처 준수: {확인 사항}

### ⏭️ **다음 단계 준비**
- {다음 Phase를 위한 준비 상태}
- {필요한 추가 정보나 결정사항}

**⏳ 다음 Phase 진행 승인을 요청드립니다.**
```

## 🚨 주의사항

### 안전성 최우선
- **백업 필수**: 모든 파일 수정 전 백업 생성
- **점진적 적용**: 한 번에 하나씩, 단계별 검증
- **롤백 준비**: 문제 발생 시 즉시 복원 가능
- **Golden Rules 엄수**: 에러 숨김/폴백 절대 금지

### 품질 확보
- **테스트 우선**: 각 변경 후 즉시 동작 확인
- **로그 활용**: Infrastructure 로깅으로 디버깅 지원
- **아키텍처 준수**: DDD 계층 위반 절대 금지
- **일관성 유지**: 표준 패턴과 네이밍 규칙 준수

## 🔥 **태스크 문서 업데이트 체크리스트** (실행 전 필독!)

### ✅ 작업 시작 시
- [ ] 태스크 문서에서 다음 작업 항목 찾기
- [ ] 해당 항목을 `[ ]` → `[-]` 마킹으로 변경
- [ ] `replace_string_in_file` 도구로 태스크 문서 업데이트

### ✅ 작업 완료 시
- [ ] 해당 항목을 `[-]` → `[x]` 마킹으로 변경
- [ ] 항목 아래에 실제 수행 내용 간략히 기록 (들여쓰기 사용)
- [ ] `replace_string_in_file` 도구로 태스크 문서 업데이트
- [ ] Phase 완료 보고서 작성

### 📝 기록 형식 예시
```markdown
- [x] Phase 4.2: ApiSettingsComponentFactory 수정
  - ✅ ApplicationServiceContainer 접근 패턴 확인 완료
  - ✅ MVP 패턴 조립 및 Presenter 연결 검증
  - ✅ UI 테스트 통과 (python run_desktop_ui.py)
  - ⚠️ 발견된 이슈: LoggingManagementPresenter 일부 오류 (기능적 영향 없음)
```

---

**태스크를 숙지하셨다면 즉시 실행에 들어가 주세요!** 🚀

⚠️ **중요**: 각 작업 시작/완료 시 반드시 태스크 문서 체크리스트를 업데이트하고, 각 단계별로 완료 보고와 승인 요청을 진행해 주시기 바랍니다.

````
