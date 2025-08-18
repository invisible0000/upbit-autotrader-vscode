# 🚀 Upbit Auto Trading System

**DDD 아키텍처 기반 프로덕션급 암호화폐 자동매매 시스템**

[![Python 3.13+](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.9.1-green.svg)](https://pypi.org/project/PyQt6/)
[![DDD Architecture](https://img.shields.io/badge/Architecture-DDD-orange.svg)](https://en.wikipedia.org/wiki/Domain-driven_design)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **🎉 DDD 리팩토링 90% 완료!** 견고한 아키텍처와 현대식 개발 환경으로 무장한 안정적인 자동매매 시스템

## ✨ 주요 특징

- **🏗️ DDD 4계층 아키텍처**: Domain 순수성 + Infrastructure 분리로 확장성 극대화
- **📊 7규칙 전략 시스템**: RSI, 불타기, 익절, 트레일링 스탑, 물타기, 급락/급등 감지
- **🎯 트리거 빌더**: 직관적인 GUI로 복잡한 매매 조건 구성
- **⚡ 실시간 연동**: Upbit API + WebSocket으로 밀리초 단위 반응
- **🔒 프로덕션 보안**: 암호화된 API 키 관리 + Dry-Run 기본 모드

## 🚀 빠른 시작

### 1️⃣ 프로젝트 클론 & 환경 설정
```powershell
# PowerShell (Windows 권장)
git clone https://github.com/invisible0000/upbit-autotrader-vscode.git
cd upbit-autotrader-vscode

# 현대식 가상환경 설정
python -m venv .venv
.venv\Scripts\Activate.ps1

# 의존성 설치 (실제 환경 검증됨)
pip install -r requirements.txt
```

### 2️⃣ 즉시 실행
```powershell
# GUI 실행 (추천) - 7규칙 전략 즉시 확인 가능
python run_desktop_ui.py
```

### 3️⃣ API 키 설정 (선택사항)
- GUI → 설정 → API 키 탭에서 안전하게 설정
- 또는 환경변수: `$env:UPBIT_ACCESS_KEY`, `$env:UPBIT_SECRET_KEY`

## 🏗️ DDD 아키텍처 구조

```
📁 upbit_auto_trading/
├── 🎨 ui/                     # Presentation Layer
│   ├── desktop/               # PyQt6 GUI
│   └── common/               # 공통 UI 컴포넌트
├── 🔧 application/           # Application Layer
│   ├── services/             # 비즈니스 서비스
│   └── use_cases/           # 유스케이스
├── 💎 domain/                # Domain Layer (순수)
│   ├── entities/             # 도메인 엔티티
│   ├── value_objects/        # 값 객체
│   └── services/            # 도메인 서비스
└── 🔌 infrastructure/        # Infrastructure Layer
    ├── repositories/         # 데이터 접근
    ├── services/            # 외부 서비스
    └── api/                 # API 연동

📁 config/                   # 설정 관리
📁 data/                     # 3-DB 분리 설계
├── settings.sqlite3         # 앱 설정
├── strategies.sqlite3       # 전략 데이터
└── market_data.sqlite3      # 시장 데이터
```

## 🎯 핵심 기능

### 📊 7규칙 자동매매 전략
| 규칙 | 설명 | 상태 |
|------|------|------|
| **RSI 과매도 진입** | RSI < 30 시 매수 진입 | ✅ |
| **수익시 불타기** | 수익률 5% 시 추가 매수 | ✅ |
| **계획된 익절** | 목표가 도달 시 자동 매도 | ✅ |
| **트레일링 스탑** | 최고가 대비 -3% 시 매도 | ✅ |
| **하락시 물타기** | -10% 하락 시 평단가 낮추기 | ✅ |
| **급락 감지** | 5분간 -15% 급락 시 손절 | ✅ |
| **급등 감지** | 5분간 +20% 급등 시 부분매도 | ✅ |

### 🎨 사용자 인터페이스
- **🖥️ Desktop GUI**: PyQt6 기반 네이티브 앱
- **📈 실시간 차트**: matplotlib + 한글 폰트 지원
- **⚙️ 설정 관리**: 직관적인 탭 기반 UI
- **📊 백테스팅**: 과거 데이터로 전략 검증

### 🔐 보안 & 안전성
- **🛡️ Dry-Run 기본**: 실거래 전 반드시 2단계 확인
- **🔑 암호화 저장**: API 키 SQLite 암호화 보관
- **⚠️ Rate Limit**: 업비트 API 호출 제한 준수
- **💰 자금 관리**: 총 자산 대비 최대 투자 비율 제한

## 🛠️ 시스템 요구사항

- **Python**: 3.13+ (현재 환경 검증됨)
- **OS**: Windows 10/11 (PowerShell 권장)
- **메모리**: 최소 8GB RAM
- **저장공간**: 2GB 여유 공간
- **네트워크**: 안정적인 인터넷 연결

## 📋 의존성 패키지

### 핵심 프레임워크
```
PyQt6==6.9.1              # GUI 프레임워크
matplotlib==3.10.5        # 차트 라이브러리
pandas==2.3.1             # 데이터 분석
numpy==2.3.2              # 수치 연산
```

### API & 데이터베이스
```
aiohttp==3.12.15          # 비동기 HTTP
requests==2.32.4          # HTTP 클라이언트
SQLAlchemy==2.0.42        # ORM
websocket-client==1.6.3   # WebSocket
```

### 보안 & 유틸리티
```
cryptography==45.0.5      # 암호화
PyJWT==2.10.1             # JWT 토큰
loguru==0.7.3             # 로깅
psutil==7.0.0             # 시스템 모니터링
```

## 🧪 테스트 & 개발

### 테스트 실행
```powershell
# 전체 테스트 (pytest 기반)
pytest -q

# 커버리지 포함
pytest --cov=upbit_auto_trading

# 특정 도메인 테스트
pytest tests/domain/ -v
```

### 개발 도구
```powershell
# 계층 위반 검사 (PowerShell)
Get-ChildItem upbit_auto_trading/domain -Recurse -Include *.py | Select-String -Pattern "import sqlite3|import requests|from PyQt6"

# 로깅 환경변수 설정
$env:UPBIT_CONSOLE_OUTPUT = "true"
$env:UPBIT_LOG_SCOPE = "verbose"

# DB 상태 확인
python tools/super_db_table_viewer.py settings
python tools/super_db_table_viewer.py strategies
python tools/super_db_table_viewer.py market_data
```

## 📚 문서 & 가이드

### 개발 가이드
- **[DDD 아키텍처 가이드](docs/DDD_아키텍처_패턴_가이드.md)**: 4계층 설계 원칙
- **[트리거 빌더 가이드](docs/TRIGGER_BUILDER_GUIDE.md)**: 7규칙 전략 구성법
- **[개발 방법론](docs/개발%20방법론%20완전%20가이드.md)**: TDD + DDD 실천법

### API 문서
- **[기본 7규칙 전략](docs/BASIC_7_RULE_STRATEGY_GUIDE.md)**: 전략별 상세 설명
- **[DB 스키마](docs/DB_SCHEMA.md)**: 3-DB 분리 설계
- **[UI 가이드](docs/UI_GUIDE.md)**: PyQt6 컴포넌트 사용법

## � 문제 해결

### 자주 발생하는 문제

**1. PyQt6 설치 오류**
```powershell
# Windows에서 PyQt6 재설치
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
pip install PyQt6==6.9.1 --no-cache-dir
```

**2. aiohttp 모듈 없음**
```powershell
# API 연결 필수 패키지
pip install aiohttp==3.12.15 requests==2.32.4
```

**3. 데이터베이스 초기화 필요**
```powershell
# 3-DB 자동 생성 (앱 실행시 자동)
python run_desktop_ui.py
```

**4. API 연결 실패**
- GUI → 설정 → API 키에서 연결 테스트
- Upbit API 권한: 자산조회, 주문조회, 주문하기 필요
- Rate Limit: 분당 100회 제한 준수

### 로그 확인
```powershell
# 실시간 로그 모니터링
Get-Content -Path "logs\application.log" -Wait

# 세션별 로그
Get-ChildItem logs\ -Name "session_*.log" | Sort-Object -Descending
```

## 🎯 로드맵

### ✅ 완료 (v1.0 - DDD 리팩토링 90%)
- DDD 4계층 아키텍처 완성
- 7규칙 전략 시스템 구현
- 현대식 .venv 환경 + VS Code 통합
- PyQt6 GUI + 실시간 차트
- 3-DB 분리 설계
- 암호화된 API 키 관리

### 🚧 진행중 (v1.1 - 나머지 10%)
- Domain Services 완성
- Repository 패턴 확장
- 백테스팅 엔진 고도화
- 실시간 알림 시스템

### 📅 계획 (v2.0)
- 멀티 거래소 지원 (바이낸스, 빗썸)
- 머신러닝 기반 예측 모델
- 모바일 앱 연동
- 클라우드 배포

## 🤝 기여하기

### 기여 방법
1. **Fork** 이 저장소
2. **Feature 브랜치** 생성: `git checkout -b feature/amazing-feature`
3. **DDD 원칙** 준수하여 개발
4. **테스트** 작성 및 통과 확인
5. **커밋**: `git commit -m "✨ 새로운 기능 추가"`
6. **Push**: `git push origin feature/amazing-feature`
7. **Pull Request** 생성

### 개발 가이드라인
- **Domain Layer**: 외부 의존성 금지
- **Infrastructure Layer**: 외부 서비스 연동만
- **Test First**: TDD 방식 개발
- **한글 커밋**: 명확한 변경사항 설명

## 📄 라이선스

```
MIT License

Copyright (c) 2025 invisible0000

이 소프트웨어는 MIT 라이선스 하에 배포됩니다.
자세한 내용은 LICENSE 파일을 참조하세요.
```

## 📞 지원 & 커뮤니티

- **🐛 버그 리포트**: [GitHub Issues](https://github.com/invisible0000/upbit-autotrader-vscode/issues)
- **💬 토론 & 질문**: [GitHub Discussions](https://github.com/invisible0000/upbit-autotrader-vscode/discussions)
- **📖 위키**: [GitHub Wiki](https://github.com/invisible0000/upbit-autotrader-vscode/wiki)
- **📧 직접 문의**: 이슈 생성 또는 토론 참여

## 🎉 최근 업데이트

### 🚀 v1.0-alpha (2025년 8월 17일)
```
🎯 DDD 아키텍처 리팩토링 90% 완료: 레거시 정리 및 현대식 환경 구축

✨ 주요 성과:
- 💀 레거시 코드 대정리: business_logic, core, data_layer 모두 legacy로 이동
- 🗑️ 백업 탭 제거: 매매전략 관리 UI 단순화
- 🏗️ 현대식 .venv 환경: VS Code 통합 완료
- 📦 requirements.txt 정리: 실제 환경 기반으로 카테고리별 재구성

🔧 기술적 개선:
- DDD 4계층 순수성 확보: Domain 외부 의존성 완전 제거
- Token 효율성 향상: 미사용 폴더들을 legacy로 격리
- API 연결 성공: 업비트 실계좌 연동 확인

✅ 검증 완료:
- GUI 시스템 정상 작동 (7규칙 전략 트리거 빌더 포함)
- 모든 화면 전환 및 설정 기능 정상
- DDD/MVP 패턴 무결성 유지
```

---

<div align="center">

**⭐ 이 프로젝트가 도움이 되었다면 GitHub Star를 눌러주세요! ⭐**

**🚀 안정적인 DDD 기반 자동매매 시스템으로 암호화폐 투자의 새로운 경험을 시작하세요! 🚀**

</div>
