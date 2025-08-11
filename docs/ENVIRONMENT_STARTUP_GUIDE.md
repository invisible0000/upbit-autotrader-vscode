# 🚀 프로그램 시작 시 환경 설정 가이드

## 📋 개요

Upbit Auto Trading 시스템은 프로그램 시작 시 **자동으로 적절한 환경 프로파일**을 감지하고 적용합니다.
더 이상 개발자 모드로 시작해서 수동으로 프로덕션 모드로 전환할 필요가 없습니다!

## 🔧 환경 지정 방법

### **방법 1: 환경변수 설정 (권장)**

PowerShell에서 환경변수를 설정하여 시작 환경을 지정:

```powershell
# 개발 환경으로 시작 (기본값)
$env:UPBIT_ENVIRONMENT = "development"
python run_desktop_ui.py

# 프로덕션 환경으로 시작 (실거래)
$env:UPBIT_ENVIRONMENT = "production"
python run_desktop_ui.py

# 테스트 환경으로 시작
$env:UPBIT_ENVIRONMENT = "testing"
python run_desktop_ui.py
```

### **방법 2: 영구 환경변수 설정**

시스템 환경변수로 영구 설정:

```powershell
# 시스템 환경변수 영구 설정 (관리자 권한 필요)
[Environment]::SetEnvironmentVariable("UPBIT_ENVIRONMENT", "production", "User")

# 설정 확인
$env:UPBIT_ENVIRONMENT
```

### **방법 3: 배치 파일 사용**

자주 사용하는 환경을 위한 배치 파일 생성:

**`start_development.ps1`**:
```powershell
$env:UPBIT_ENVIRONMENT = "development"
$env:UPBIT_CONSOLE_OUTPUT = "true"
$env:UPBIT_LOG_SCOPE = "verbose"
python run_desktop_ui.py
```

**`start_production.ps1`**:
```powershell
$env:UPBIT_ENVIRONMENT = "production"
$env:UPBIT_CONSOLE_OUTPUT = "false"
$env:UPBIT_LOG_SCOPE = "normal"
python run_desktop_ui.py
```

## 📊 환경별 자동 설정

### **Development 환경** (기본값)
- **목적**: 개발 및 디버깅
- **거래 모드**: 모의거래 (paper_trading: true)
- **로깅**: DEBUG 레벨, 콘솔 출력 활성화
- **포지션 크기**: 최대 10만원
- **안전**: 실거래 불가능

### **Production 환경** ⚠️
- **목적**: 실제 거래 운영
- **거래 모드**: 실거래 (paper_trading: false)
- **로깅**: INFO 레벨, 파일 로깅만
- **포지션 크기**: 최대 500만원
- **주의**: 실제 자금 거래

### **Testing 환경**
- **목적**: 전략 테스트 및 백테스팅
- **거래 모드**: 모의거래 (paper_trading: true)
- **로깅**: INFO 레벨, 균형잡힌 설정
- **포지션 크기**: 최대 50만원

## 🔍 환경 감지 과정

시스템은 다음 순서로 환경을 감지합니다:

1. **`UPBIT_ENVIRONMENT` 환경변수** (최우선)
2. **`UPBIT_LOG_CONTEXT` 환경변수** (Infrastructure Layer에서 설정한 경우)
3. **기본값: `development`** (환경변수가 없는 경우)

## ✅ 확인 방법

프로그램 시작 후 Environment&Logging 탭에서 현재 환경 확인:

- **프로파일 드롭다운**: 자동으로 해당 환경 프로파일 선택됨
- **현재 환경 표시**: 상단에 현재 환경 표시
- **로그 메시지**: "🔍 시스템 환경변수에서 환경 감지: production" 등

## 🚨 실거래 주의사항

**Production 환경 사용 시 반드시 확인:**

1. **API 키 설정**: 실제 Upbit API 키 등록
2. **자금 확인**: 거래 가능한 자금 존재
3. **전략 검증**: 충분한 백테스팅 완료
4. **모니터링 준비**: 실시간 거래 모니터링 체계

## 🔄 런타임 환경 전환

프로그램 실행 중에도 환경 전환 가능:

1. **Environment&Logging 탭** 이동
2. **프로파일 드롭다운**에서 원하는 환경 선택
3. **Switch Profile** 버튼 클릭
4. 즉시 새 환경 설정 적용

## 💡 실용적 워크플로우

### **개발자 워크플로우**
```powershell
# 1. 개발 시작
$env:UPBIT_ENVIRONMENT = "development"
python run_desktop_ui.py

# 2. 전략 테스트
$env:UPBIT_ENVIRONMENT = "testing"
python run_desktop_ui.py

# 3. 실거래 배포 (신중히!)
$env:UPBIT_ENVIRONMENT = "production"
python run_desktop_ui.py
```

### **일반 사용자 워크플로우**
```powershell
# 기본: 안전한 개발 모드로 시작
python run_desktop_ui.py

# 실거래: 환경변수 설정 후 시작
$env:UPBIT_ENVIRONMENT = "production"
python run_desktop_ui.py
```

## 🛡️ 안전장치

- **Development/Testing**: 실거래 완전 차단 (paper_trading: true)
- **Production**: 추가 검증 및 모니터링 활성화
- **환경 전환**: UI에서 명시적 확인 과정
- **로깅**: 모든 환경 전환 기록 보존

---

**🎯 핵심**: 이제 프로그램 시작 시 `UPBIT_ENVIRONMENT` 환경변수만 설정하면 자동으로 적절한 프로파일이 적용됩니다!
