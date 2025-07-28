# Upbit Autotrader

**GitHub에서 클론하고 바로 실행 가능한 암호화폐 자동매매 시스템**

## 🚀 빠른 시작

### 1단계: 프로젝트 클론
```bash
git clone https://github.com/invisible0000/upbit-autotrader-vscode.git
cd upbit-autotrader-vscode
```

### 2단계: 의존성 설치
```bash
pip install -r requirements.txt
```

### 3단계: 애플리케이션 실행
```bash
# 방법 1: 빠른 시작 스크립트 (권장)
python quick_start.py

# 방법 2: Desktop UI 직접 실행
python run_desktop_ui.py

# 방법 3: 콘솔 모드
python run.py
```

## 📋 시스템 요구사항

- **Python**: 3.8 이상
- **운영체제**: Windows, macOS, Linux
- **메모리**: 최소 4GB RAM
- **디스크**: 최소 1GB 여유 공간

## 🔧 주요 기능

### 전략 관리 시스템
- **TriggerBuilder**: 조건부 매매 전략 구성
- **StrategyMaker**: 전략 생성 및 백테스트
- **미니 시뮬레이션**: 실시간 전략 검증

### 차트 및 분석
- **실시간 차트**: PyQt6 기반 고성능 차트
- **기술적 지표**: RSI, MACD, 볼린저 밴드 등
- **백테스트**: 과거 데이터 기반 전략 검증

### 자동매매 엔진
- **Upbit API 연동**: 실시간 매매 실행
- **리스크 관리**: 손절/익절 자동 실행
- **포트폴리오 관리**: 다중 코인 동시 관리

## 🏗️ 프로젝트 구조

```
upbit-autotrader-vscode/
├── quick_start.py                 # 빠른 시작 스크립트
├── requirements.txt               # 통합 의존성 패키지
├── run_desktop_ui.py             # Desktop UI 실행
├── run.py                        # 콘솔 모드 실행
├── config/                       # 설정 파일들
├── upbit_auto_trading/          # 메인 패키지
│   ├── ui/desktop/              # Desktop UI
│   ├── api/                     # Upbit API 연동
│   └── strategies/              # 매매 전략들
├── docs/                        # 문서
└── tests/                       # 테스트 코드
```

## 🎯 최신 기능 (2025년 7월)

### 미니 시뮬레이션 아키텍처 (v1.0)
- **공통 컴포넌트**: 크로스 탭 재사용 가능한 시뮬레이션 시스템
- **어댑터 패턴**: 각 탭별 특화 기능 지원
- **실시간 검증**: 전략 효과를 즉시 확인

### 컴포넌트 기반 UI
- **모듈화된 구조**: 독립적인 컴포넌트들
- **확장 가능**: 새로운 기능 쉽게 추가
- **재사용성**: 코드 중복 최소화

## ⚙️ 설정

### API 키 설정
1. Upbit에서 API 키 발급
2. `.env` 파일 생성:
```env
UPBIT_ACCESS_KEY=your_access_key
UPBIT_SECRET_KEY=your_secret_key
```

### 데이터베이스 초기화
```bash
python initialize_databases.py
```

## 🧪 테스트

```bash
# 전체 테스트 실행
python -m pytest tests/

# 특정 모듈 테스트
python -m pytest tests/test_strategy_management.py

# 커버리지 포함 테스트
python -m pytest tests/ --cov=upbit_auto_trading
```

## 📚 문서

- **개발 가이드**: `docs/DEVELOPMENT_GUIDE.md`
- **API 문서**: `docs/API_DOCUMENTATION.md`
- **아키텍처 가이드**: `docs/MINI_SIMULATION_ARCHITECTURE_GUIDE.md`
- **변경 로그**: `docs/CHANGELOG.md`

## 🐛 문제 해결

### 일반적인 문제들

**1. PyQt6 설치 오류**
```bash
# Linux
sudo apt-get install python3-pyqt6

# macOS
brew install pyqt6

# Windows
pip install PyQt6 --upgrade
```

**2. 의존성 충돌**
```bash
pip install --force-reinstall -r requirements.txt
```

**3. 데이터베이스 오류**
```bash
python initialize_databases.py --reset
```

## 🤝 기여하기

1. Fork 프로젝트
2. Feature 브랜치 생성: `git checkout -b feature/amazing-feature`
3. 변경사항 커밋: `git commit -m 'Add amazing feature'`
4. 브랜치에 Push: `git push origin feature/amazing-feature`
5. Pull Request 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 지원

- **이슈 리포트**: [GitHub Issues](https://github.com/invisible0000/upbit-autotrader-vscode/issues)
- **토론**: [GitHub Discussions](https://github.com/invisible0000/upbit-autotrader-vscode/discussions)
- **위키**: [GitHub Wiki](https://github.com/invisible0000/upbit-autotrader-vscode/wiki)

## 🎉 최근 업데이트

### v1.0.0-alpha (2025년 7월)
- ✅ 미니 시뮬레이션 아키텍처 리팩토링 완료
- ✅ 크로스 탭 재사용성 구현
- ✅ 어댑터 패턴 기반 확장성 확보
- ✅ 통합 환경 설정 및 GitHub 배포 준비

---

**⭐ 이 프로젝트가 도움이 되었다면 GitHub Star를 눌러주세요!**
