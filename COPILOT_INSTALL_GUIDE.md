# Upbit Autotrader 설치 및 환경 구성 가이드

## 1. 개발 환경 준비
- Python 3.8 이상 권장 (현재: 3.13.5)
- Windows, macOS, Linux 모두 지원
- 가상환경(.venv) 사용 권장

## 2. 의존성 패키지 설치
프로젝트 루트에서 아래 명령어 실행:
```cmd
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. 주요 패키지 설명
- pandas, numpy: 데이터 처리
- requests, python-dotenv, cryptography, pyjwt: API 통신 및 인증
- PyQt6, pyqtgraph, matplotlib: 데스크탑 GUI
- flask, dash, plotly: 웹 인터페이스(추가 설치 필요시)

## 4. 실행 방법
### 데스크탑 GUI
```cmd
python -m upbit_auto_trading.ui.desktop.main
```
또는
```cmd
upbit-autotrader-desktop
```

### 웹 인터페이스
```cmd
python -m upbit_auto_trading.ui.web.main
```
또는
```cmd
upbit-autotrader-web
```

### CLI
```cmd
python -m upbit_auto_trading.ui.cli.main
```
또는
```cmd
upbit-autotrader-cli
```

## 5. 문제 해결
- 패키지 설치 오류: pip 버전 확인, 관리자 권한으로 실행
- PyQt6 관련 오류: 최신 버전 설치, OS별 추가 라이브러리 필요시 공식 문서 참고
- 기타 문의: README.md, COPILOT_DEVELOPMENT_GUIDE.md 참고

---

## [중요] GUI 미구현/개선 필요 목록 및 추가 개발 시급 항목
- 종목 스크리닝 화면 미구현
- 매매전략 관리 화면 미구현
- 백테스팅 화면 미구현
- 실시간 거래 화면 미구현
- 포트폴리오 구성 화면 미구현
- 테마 전환(화이트/데이 모드)에서 글자 색이 배경과 같아 가독성 저하
- 로그인 기능 미구현
- 기타: 알림, 설정, 사용자 경험 등 전반적인 GUI 추가 개발 필요

> 위 항목들은 추후 개발 및 개선이 반드시 필요합니다. 실제 배포/운영 전 반드시 구현 및 테스트를 완료해 주세요.

---
최신 설치 가이드 및 환경 구성 문서 초안입니다. 추가 요청 시 상세 매뉴얼, FAQ, 트러블슈팅 문서화 가능합니다.
