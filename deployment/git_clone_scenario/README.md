# 🚀 Git Clone 시나리오 - 개발자용 빠른 시작

## 📋 이 폴더의 목적

이 폴더는 **개발자와 오픈소스 사용자**를 위한 Git Clone 후 빠른 실행 시나리오를 제공합니다.

## 🎯 사용 대상

- **개발자**: 소스코드를 직접 수정하고 싶은 사용자
- **파워 유저**: Python 환경이 있고 커스터마이징을 원하는 사용자  
- **기여자**: 프로젝트에 기여하고 싶은 개발자

## 📁 포함된 파일들

### `quick_start.py` - 자동 초기화 스크립트
**기능**:
- 의존성 패키지 자동 체크
- 프로젝트 환경 설정
- 필요한 디렉토리 생성
- Desktop UI 자동 실행

**사용법**:
```bash
cd upbit-autotrader-vscode
python deployment/git_clone_scenario/quick_start.py
```

### `.env.template` - 환경설정 템플릿
**기능**:
- API 키 설정 가이드
- 데이터베이스 경로 설정
- 로깅 설정
- 보안 설정 템플릿

**사용법**:
```bash
# 1. 템플릿을 실제 설정 파일로 복사
cp deployment/git_clone_scenario/.env.template .env

# 2. 실제 API 키로 수정
UPBIT_ACCESS_KEY=your_real_access_key
UPBIT_SECRET_KEY=your_real_secret_key
```

## 🚀 완전한 시작 가이드

### 1단계: 저장소 클론
```bash
git clone https://github.com/invisible0000/upbit-autotrader-vscode
cd upbit-autotrader-vscode
```

### 2단계: 가상환경 생성 (권장)
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

### 3단계: 의존성 설치
```bash
pip install -r requirements.txt
```

### 4단계: 환경설정
```bash
cp deployment/git_clone_scenario/.env.template .env
# .env 파일을 편집하여 실제 API 키 입력
```

### 5단계: 빠른 시작
```bash
python deployment/git_clone_scenario/quick_start.py
```

## ⚠️ 문제 해결

### 의존성 설치 실패
```bash
# Python 버전 확인 (3.8+ 필요)
python --version

# pip 업그레이드
python -m pip install --upgrade pip

# 개별 패키지 설치 시도
pip install PyQt6 pandas requests
```

### API 키 관련 오류
1. Upbit Open API에서 키 재발급
2. `.env` 파일의 키 형식 확인
3. 키에 특수문자나 공백 없는지 확인

### GUI 실행 오류
```bash
# 대체 실행 방법
python run_desktop_ui.py

# 콘솔 모드로 문제 확인
python deployment/future_cli_mode/run_console.py
```

## 🔄 개발 워크플로우

### 일반 개발
```bash
python run_desktop_ui.py  # GUI 모드 실행
```

### 테스트 실행
```bash
python -m pytest tests/
```

### 코드 스타일 체크
```bash
black upbit_auto_trading/
flake8 upbit_auto_trading/
```

---

## 📞 지원

- **이슈 리포트**: [GitHub Issues](https://github.com/invisible0000/upbit-autotrader-vscode/issues)
- **개발 가이드**: [docs/DEVELOPMENT_GUIDE.md](../../docs/DEVELOPMENT_GUIDE.md)
- **API 문서**: [Upbit Open API](https://docs.upbit.com/)

---

*이 시나리오는 개발자를 위한 것입니다. 일반 사용자용 설치형 버전은 추후 제공 예정입니다.*
