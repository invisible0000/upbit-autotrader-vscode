# 🚀 배포 시나리오 및 다중 UI 모드 계획

## 📋 개요

이 폴더는 Upbit Autotrader의 **미래 배포 전략**과 **다중 UI 모드** 개발 계획을 담고 있습니다.

## 🎯 배포 시나리오

### 1️⃣ **Git Clone 시나리오** (준비됨)

**폴더**: `git_clone_scenario/`
**대상**: 개발자, 오픈소스 사용자
**특징**: 
- 소스코드 직접 다운로드 후 실행
- 개발 환경 필요
- 커스터마이징 가능

**파일들**:
- `quick_start.py`: 의존성 체크 + 자동 실행
- `.env.template`: 환경설정 템플릿

```bash
# 사용법
git clone https://github.com/invisible0000/upbit-autotrader-vscode
cd upbit-autotrader-vscode
python deployment/git_clone_scenario/quick_start.py
```

### 2️⃣ **포터블 설치형 시나리오** (계획 단계)

**폴더**: `portable_installer/` (미구현)
**대상**: 일반 사용자
**특징**:
- 실행 파일 형태 (.exe)
- Python 환경 불필요
- 원클릭 설치/실행

**예상 구조**:
```
portable_installer/
├── build_executable.py     # PyInstaller 빌드 스크립트
├── installer_config.nsi    # NSIS 설치 스크립트
└── setup_wizard.py         # 초기 설정 마법사
```

---

## 🖥️ 다중 UI 모드 아키텍처 계획

### **현재 상태** (Phase 1)
```
upbit_auto_trading/
├── ui/
│   └── desktop/           # ✅ GUI 모드 (PyQt6) - 현재 개발 중
│       ├── main_window.py
│       └── screens/
└── business_logic/        # 🎯 비즈니스 로직 분리 진행 중
```

### **미래 계획** (Phase 2-3)
```
upbit_auto_trading/
├── ui/
│   ├── desktop/           # ✅ GUI 모드 (완성)
│   ├── cli/               # 🚧 CLI 모드 (계획)
│   └── web/               # 🚧 웹 모드 (계획)
├── business_logic/        # ✅ 공통 비즈니스 로직
└── core/                  # ✅ 핵심 유틸리티
```

---

## 🔮 미래 CLI 모드 계획

**폴더**: `future_cli_mode/`
**현재 상태**: 개념 증명용 파일 보관

### **파일들**:
- `run_console.py`: 현재 콘솔 실행기 (기본 기능만)

### **향후 개발 계획**:
```bash
# 예상되는 CLI 명령어들
upbit-trader start --strategy=rsi_strategy
upbit-trader backtest --from=2024-01-01 --to=2024-12-31
upbit-trader status
upbit-trader config --set-api-key
```

### **CLI 모드 장점**:
- 서버 환경에서 실행
- 자동화 스크립트 연동
- 헤드리스 환경 지원
- 배치 작업 최적화

---

## 🌐 미래 웹 모드 계획

### **웹 UI 장점**:
- 브라우저에서 접근
- 크로스 플랫폼 지원
- 원격 모니터링 가능
- 모바일 친화적

### **기술 스택 후보**:
- **Backend**: Flask/FastAPI + WebSocket
- **Frontend**: React/Vue.js + Chart.js
- **Real-time**: Socket.IO

---

## ⚠️ 현재 개발 우선순위

### **Phase 1** (현재): GUI 모드 완성도 집중
- ✅ 트리거 빌더 완성
- 🚧 전략 조합 시스템
- 🚧 백테스팅 시스템
- 🚧 실시간 매매 엔진

### **Phase 2** (미래): 비즈니스 로직 완전 분리
- CLI 모드 기반 설계
- API 계층 구축
- 공통 인터페이스 정의

### **Phase 3** (미래): 다중 UI 모드
- CLI 모드 구현
- 웹 모드 구현
- 배포 시나리오 완성

---

## 📚 관련 문서

- [프로젝트 아키텍처](../../docs/DEVELOPMENT_GUIDE.md)
- [비즈니스 로직 분리 계획](../../docs/STRATEGY_ARCHITECTURE_OVERVIEW.md)
- [UI 컴포넌트 설계](../../upbit_auto_trading/ui/desktop/README.md)

---

**⭐ 핵심 철학**: "GUI 완성 → 로직 분리 → 다중 UI 확장"

*마지막 업데이트: 2025-08-03*
