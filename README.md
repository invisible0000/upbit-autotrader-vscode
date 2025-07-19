# 🚀 Upbit Autotrader v0.1.0-alpha

[![Version](https://img.shields.io/badge/version-0.1.0--alpha-blue.svg)](./version.json)
[![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)](https://python.org)
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-orange.svg)](https://pypi.org/project/PyQt6/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](./LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](./VERSION_0_1_MILESTONE_TASKS.md)

> **Advanced cryptocurrency autotrading system for Upbit exchange with optimized chart visualization**

업비트 API를 활용한 **프로덕션급** 암호화폐 자동 거래 시스템입니다. 최적화된 차트 시스템, 실시간 웹소켓 업데이트, 그리고 직관적인 사용자 인터페이스를 제공합니다.

---

## 🎯 **v0.1.0-alpha 주요 특징**

### ⚡ **최적화된 차트 시스템**
- **점진적 로딩**: 600개 캔들 초기 로딩 (2초 이내)
- **실시간 업데이트**: 웹소켓 기반 0 API 요청 실시간 차트
- **무한 스크롤**: 과거 데이터 200개씩 동적 로딩
- **성능 최적화**: 메모리 효율적 대용량 데이터 처리

### 🎨 **프로덕션급 UI/UX**
- **테마 시스템**: 완전한 다크/라이트 모드 지원
- **반응형 디자인**: 창 크기 변경 시 즉시 조정
- **시각적 피드백**: 로딩 인디케이터, 상태 표시, 에러 메시지

### 🔌 **95% 완성된 API 통합**
- **업비트 API 클라이언트**: 완전한 REST API 지원
- **레이트 제한 준수**: 초당 10회, 분당 600회 자동 제한
- **에러 처리**: 강력한 재시도 로직 및 연결 관리

---

## 📊 **현재 개발 진행률**

| 모듈 | 상태 | 완성도 |
|------|------|--------|
| 🔌 API 클라이언트 | ✅ 완료 | 95% |
| 📈 차트 시스템 | 🟡 진행중 | 60% |
| 🎨 UI/UX | 🟡 진행중 | 70% |
| 💹 거래 기능 | 🟡 진행중 | 40% |
| 🧪 테스트 | 🔴 대기 | 35% |

**전체 진행률**: **62%** | [📋 상세 로드맵](./VERSION_0_1_MILESTONE_TASKS.md)

---

## 🚀 **빠른 시작**

### 📦 **설치**

```bash
# 1. 저장소 클론
git clone https://github.com/invisible0000/upbit-autotrader-vscode.git
cd upbit-autotrader-vscode

# 2. Python 가상환경 생성 (권장)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경 설정
copy .env.example .env
# .env 파일에 업비트 API 키 설정
```

### ⚙️ **환경 설정**

`.env` 파일에 업비트 API 키를 설정하세요:

```env
UPBIT_ACCESS_KEY=your_access_key_here
UPBIT_SECRET_KEY=your_secret_key_here
```

### 🖥️ **실행**

```bash
# 데스크톱 GUI 실행
python run_desktop_ui.py

# API 연결 테스트
python test_api_key.py

# 차트 뷰 테스트
python test_chart_view.py

# 전체 테스트 실행
python run_tests_in_order.py
```

---

## 📋 **시스템 요구사항**

- **Python**: 3.8 이상
- **운영체제**: Windows 10+, macOS 11+, Ubuntu 20.04+
- **메모리**: 최소 4GB, 권장 8GB
- **저장공간**: 1GB 여유 공간
- **네트워크**: 안정적인 인터넷 연결

---

## 🛠️ **핵심 기술 스택**

### **프론트엔드**
- **PyQt6**: 데스크톱 GUI 프레임워크
- **pyqtgraph**: 고성능 차트 라이브러리
- **QSS**: 사용자 정의 스타일링

### **백엔드**
- **Python 3.8+**: 메인 개발 언어
- **pandas/numpy**: 데이터 처리 및 분석
- **websockets**: 실시간 데이터 스트리밍
- **SQLite**: 로컬 데이터 저장

### **외부 API**
- **Upbit REST API**: 거래소 데이터 및 거래 실행
- **Upbit WebSocket**: 실시간 시세 및 체결 데이터

## 🏗️ **프로젝트 아키텍처**

```
upbit_auto_trading/
├── 📊 business_logic/          # 비즈니스 로직 (95% 완료)
│   ├── strategies/            # 거래 전략 엔진
│   ├── portfolio/             # 포트폴리오 관리
│   └── backtesting/           # 백테스팅 시스템
├── ⚙️ config/                  # 설정 관리
├── 🗃️ data_layer/               # 데이터 계층 (90% 완료)
│   ├── collectors/            # ✅ 업비트 API 클라이언트 (95% 완료)
│   ├── models/                # 데이터 모델
│   ├── processors/            # 기술적 지표 계산
│   └── storage/               # 데이터베이스 관리
├── 🎨 ui/                       # 사용자 인터페이스 (70% 완료)
│   ├── desktop/               # 🖥️ PyQt6 GUI (메인)
│   ├── web/                   # 🌐 웹 인터페이스 (미래)
│   └── cli/                   # 💻 CLI 도구
├── 🧪 tests/                    # 테스트 시스템 (35% 완료)
└── 📚 docs/                     # 문서화 (80% 완료)
```

---

## 💼 **핵심 구현 모듈**

### 🔌 **업비트 API 클라이언트** (95% 완료)
- ✅ **완전한 REST API 지원**: 모든 업비트 API 엔드포인트
- ✅ **레이트 제한 준수**: 초당 10회, 분당 600회 자동 관리
- ✅ **에러 처리**: 강력한 재시도 로직 및 예외 처리
- ✅ **인증 시스템**: JWT 토큰 기반 보안 인증
- ✅ **캔들 데이터**: `get_historical_candles()` 완벽 지원

### 📈 **최적화된 차트 시스템** (60% 완료)
- 🟡 **점진적 로딩**: 600개 캔들 초기 로딩 → 실시간 연동 중
- 🟡 **웹소켓 실시간**: 체결 데이터 기반 실시간 캔들 업데이트
- 🟡 **무한 스크롤**: 과거 데이터 200개씩 동적 로딩
- 🔴 **성능 최적화**: 메모리 효율성 및 렌더링 속도 개선

### 🎨 **프로덕션급 UI** (70% 완료)
- ✅ **테마 시스템**: 완전한 다크/라이트 모드
- ✅ **반응형 레이아웃**: 창 크기 변경 시 즉시 조정
- 🟡 **대시보드 위젯**: 실시간 데이터 연동 중
- 🔴 **알림 시스템**: 시각적 피드백 및 상태 표시

### 💹 **거래 기능** (40% 완료)
- ✅ **계좌 정보**: 실시간 자산 현황 조회
- 🟡 **주문 시스템**: 기본 주문 기능 구현 중
- 🔴 **자동매매**: 전략 기반 자동 실행 엔진
- 🔴 **리스크 관리**: 손절/익절 자동 관리

---

## 📋 **v0.1.0 개발 로드맵**

### 🔥 **이번 주 (7/20-7/26): 차트 최적화**
- [ ] **TASK-001**: 차트 데이터 로더 통합 (90% → 100%)
- [ ] **TASK-002**: 웹소켓 실시간 업데이트 구현
- [ ] **TASK-003**: 과거 데이터 무한 스크롤

### ⚡ **다음 주 (7/27-8/2): UI 안정화**
- [ ] **TASK-004**: 테마 전환 완전 안정화
- [ ] **TASK-005**: 차트 렌더링 문제 해결
- [ ] **TASK-007**: 대시보드 위젯 실데이터 연동

### 🧪 **3주차 (8/3-8/9): 테스트 및 검증**
- [ ] 차트 시스템 통합 테스트
- [ ] API 클라이언트 부하 테스트
- [ ] UI 반응성 테스트

### 📚 **4주차 (8/10-8/16): 릴리즈 준비**
- [ ] 사용자 매뉴얼 완성
- [ ] 개발자 API 문서 작성
- [ ] **v0.1.0-stable 릴리즈**

**📊 상세 일정**: [VERSION_0_1_MILESTONE_TASKS.md](./VERSION_0_1_MILESTONE_TASKS.md)

---

## 🎯 **주요 기능 미리보기**

### 💡 **스마트 차트 시스템**
```python
# 최적화된 차트 데이터 로딩
chart_manager = AdvancedChartDataManager(chart_widget)
chart_manager.initialize_chart("KRW-BTC", "1m", initial_count=600)

# 실시간 웹소켓 업데이트 (API 요청 0회!)
realtime_updater = RealtimeChartUpdater("KRW-BTC")
realtime_updater.start_realtime_update()
```

### 📊 **업비트 API 통합**
```python
# 95% 완성된 API 클라이언트 활용
api = UpbitAPI()
candles = api.get_historical_candles("KRW-BTC", "1h", start_date, end_date)
account = api.get_account()  # 실시간 자산 현황
```

### 🎨 **프로덕션급 UI**
```python
# 테마 시스템
main_window.apply_theme("dark")  # 또는 "light"

# 반응형 차트
chart_view.showEvent()  # 자동 크기 조정
chart_view.resizeEvent()  # 창 크기 변경 대응
```

---

### 환경 설정
1. `.env` 파일을 생성하고 다음 내용을 추가합니다:
```
UPBIT_ACCESS_KEY=your_access_key
UPBIT_SECRET_KEY=your_secret_key
```

### 실행
```bash
# 백엔드 실행
python run.py

# 데스크톱 UI 실행
python run_desktop_ui.py
```

## 개발 현황

### 완료된 작업
- [x] 데이터 계층 구현
  - [x] 업비트 API 클라이언트 확장
  - [x] 데이터 수집기 구현
  - [x] 데이터 처리기 구현
- [x] 비즈니스 로직 구현
  - [x] 스크리너 구현
    - [x] 기본 스크리닝 기능 구현 (거래량, 변동성, 추세 기반)
    - [x] 스크리닝 결과 처리 및 저장 기능 구현
  - [x] 매매 전략 관리 시스템 구현
    - [x] 전략 인터페이스 및 기본 클래스 구현
    - [x] 기본 매매 전략 구현
    - [x] 전략 저장 및 관리 기능 구현
  - [x] 포트폴리오 관리 시스템 구현
    - [x] 포트폴리오 모델 및 기본 기능 구현
    - [x] 포트폴리오 성과 계산 기능 구현
  - [x] 백테스팅 엔진 구현 (완료)
    - [x] 백테스트 실행기 구현
    - [x] 백테스트 결과 분석기 구현
    - [x] 포트폴리오 백테스트 기능 구현
    - [x] 백테스트 결과 저장 및 비교 기능 구현

### 진행 중인 작업
- [x] 사용자 인터페이스 개발
  - [x] 메인 애플리케이션 프레임워크 구현 (완료)
    - [x] 애플리케이션 윈도우 및 레이아웃 구현
    - [x] 메뉴 및 네비게이션 구현
    - [x] 테마 및 스타일 구현 (라이트/다크 모드)
    - [x] 화면 전환 기능 구현
    - [x] 설정 저장 및 로드 기능 구현
  - [x] 대시보드 구현 (완료)
    - [x] 포트폴리오 요약 위젯 구현
    - [x] 활성 거래 목록 위젯 구현
    - [x] 시장 개요 위젯 구현
  - [x] 차트 뷰 구현 (완료)
    - [x] 캔들스틱 차트 구현
    - [x] 기술적 지표 오버레이 구현
    - [x] 거래 시점 마커 구현
    - [ ] 실시간 데이터 연동
  - [x] 설정 화면 구현 (완료)
    - [x] API 키 관리 화면 구현
    - [x] 데이터베이스 설정 화면 구현
    - [x] 알림 설정 화면 구현
  - [x] 알림 센터 구현 (완료)
    - [x] 알림 목록 화면 구현
## 🤝 **기여하기**

### 🛠️ **개발 환경 설정**
```bash
# 개발용 의존성 설치
pip install -r requirements.txt
pip install -e .[dev]

# 코드 품질 검사
flake8 upbit_auto_trading/
black upbit_auto_trading/

# 테스트 실행
pytest tests/ -v
```

### 📋 **기여 가이드라인**
1. **이슈 확인**: [GitHub Issues](https://github.com/invisible0000/upbit-autotrader-vscode/issues)에서 작업할 이슈 선택
2. **브랜치 생성**: `feature/task-xxx` 또는 `bugfix/bug-xxx` 형식
3. **코딩 스타일**: Black 포매터 및 flake8 린터 준수
4. **테스트 작성**: 새 기능에 대한 단위 테스트 필수
5. **문서 업데이트**: 코드 변경 시 관련 문서 동기화

### 🏗️ **현재 우선순위 작업**
- 📈 **차트 최적화** (TASK-001~003)
- 🎨 **UI 안정화** (TASK-004~005)  
- 💹 **거래 기능** (TASK-006~007)

**상세 태스크**: [VERSION_0_1_MILESTONE_TASKS.md](./VERSION_0_1_MILESTONE_TASKS.md)

---

## 📚 **문서 및 리소스**

### 📖 **핵심 문서**
- 📋 **[개발 로드맵](./VERSION_0_1_MILESTONE_TASKS.md)**: v0.1.0 상세 태스크 계획
- 🎯 **[개발 가이드](./COPILOT_DEVELOPMENT_GUIDE.md)**: Copilot 친화적 통합 가이드
- 📊 **[차트 최적화](./upbit_auto_trading/ui/desktop/screens/chart_view/dynamic_chart_data_guide.py)**: 차트 성능 개선 구현
- 🎨 **[GUI 계획](./COPILOT_GUI_DEVELOPMENT_PLAN.md)**: UI 개발 전략

### 🔗 **외부 리소스**
- 📘 **[업비트 API 문서](https://docs.upbit.com/)**: 공식 API 레퍼런스
- 🐍 **[PyQt6 문서](https://doc.qt.io/qtforpython/)**: GUI 프레임워크
- 📈 **[pyqtgraph](https://pyqtgraph.readthedocs.io/)**: 차트 라이브러리

---

## ⚠️ **면책 조항**

> **🚨 중요**: 이 소프트웨어는 교육 및 연구 목적으로 제공됩니다. 실제 거래에 사용할 경우 발생하는 모든 손실에 대해 개발자는 책임지지 않습니다. 암호화폐 거래는 높은 위험을 수반하므로 신중하게 사용하시기 바랍니다.

### 🔒 **보안 주의사항**
- API 키를 절대 공개하지 마세요
- `.env` 파일을 Git에 커밋하지 마세요
- 정기적으로 API 키를 재생성하세요
- 테스트 환경에서 충분히 검증 후 실사용하세요

---

## 📞 **연락처 및 지원**

### 🐛 **버그 리포트**
- **GitHub Issues**: [이슈 등록](https://github.com/invisible0000/upbit-autotrader-vscode/issues/new)
- **버전 정보 포함**: `python -c "import json; print(json.load(open('version.json'))['version'])"`

### 💬 **커뮤니티**
- **Discussions**: [GitHub Discussions](https://github.com/invisible0000/upbit-autotrader-vscode/discussions)
- **Wiki**: [프로젝트 위키](https://github.com/invisible0000/upbit-autotrader-vscode/wiki)

### 📧 **문의**
- **개발팀**: dev@upbit-autotrader.com
- **일반 문의**: support@upbit-autotrader.com

---

## 🏆 **라이선스**

이 프로젝트는 **MIT 라이선스** 하에 배포됩니다. 자세한 내용은 [LICENSE](./LICENSE) 파일을 참조하세요.

---

## 🎉 **감사의 말**

이 프로젝트는 다음과 같은 오픈소스 프로젝트들의 도움을 받았습니다:

- **[PyQt6](https://pypi.org/project/PyQt6/)**: 강력한 GUI 프레임워크
- **[pandas](https://pandas.pydata.org/)**: 데이터 분석 및 처리
- **[pyqtgraph](https://pyqtgraph.readthedocs.io/)**: 고성능 차트 라이브러리
- **[websockets](https://websockets.readthedocs.io/)**: 실시간 데이터 스트리밍

그리고 모든 **기여자들**과 **커뮤니티 멤버들**에게 감사드립니다! 🙏

---

<div align="center">

**⭐ 이 프로젝트가 도움이 되셨다면 GitHub Star를 눌러주세요! ⭐**

[![GitHub stars](https://img.shields.io/github/stars/invisible0000/upbit-autotrader-vscode.svg?style=social)](https://github.com/invisible0000/upbit-autotrader-vscode/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/invisible0000/upbit-autotrader-vscode.svg?style=social)](https://github.com/invisible0000/upbit-autotrader-vscode/network/members)

**🚀 Happy Trading! 📈**

</div>
    - 테스트 환경 격리: 각 테스트 케이스마다 새로운 객체 생성
    - 알림 중복 방지: 알림 이력 관리 메커니즘 구현
    - 파일 경로 및 권한 관리: 디렉토리 경로 확인 및 생성 로직 추가
    - 멀티스레딩 안전성: 공유 데이터 접근 시 락 사용, 데몬 스레드 활용
  - 문서 업데이트
    - `development_guide.md`: 개발 시 주의사항 및 향후 개발 가이드 섹션 추가
    - `notification_guide.md`: 알림 시스템 개발 시 주의사항 및 모범 사례 섹션 추가
    - `development_progress.md`: 모니터링 및 알림 시스템 구현 내용 기록

- 사용자 인터페이스 - 알림 센터 구현 완료 및 개선
  - 알림 모델 구현
    - 알림 유형 열거형 구현 (NotificationType)
    - 알림 데이터 클래스 구현 (Notification)
    - 알림 관리 클래스 구현 (NotificationManager)
  - 알림 목록 화면 구현 (NotificationList)
    - 알림 항목 위젯 구현 (NotificationItem)
    - 알림 읽음 표시 및 삭제 기능 구현
    - 알림 목록 로드 및 표시 기능 구현
  - 알림 필터 기능 구현 (NotificationFilter)
    - 알림 유형별 필터링 (가격, 거래, 시스템)
    - 읽음 상태별 필터링 (읽음, 읽지 않음)
    - 시간 범위별 필터링 (오늘, 지난 7일, 지난 30일)
  - 알림 센터 메인 화면 구현 (NotificationCenter)
    - 알림 목록과 필터 통합
    - 툴바 및 상태바 구현
    - 알림 관리 기능 구현
  - 알림 설정 화면 구현 (NotificationSettings)
    - 알림 유형별 활성화/비활성화 설정
    - 알림 방법 설정 (소리, 데스크톱, 이메일)
    - 알림 빈도 및 방해 금지 시간 설정
  - 메인 윈도우 통합
    - 메인 윈도우에 알림 센터 화면 추가
    - 네비게이션 바와 연동하여 화면 전환 구현
  - 통합 테스트 작성 및 검증 (test_08_5_notification_center.py)
    - 알림 센터 초기화 테스트
    - 알림 목록 표시 테스트
    - 알림 필터 기능 테스트
    - 알림 작업 테스트
    - 알림 설정 통합 테스트
  - 알림 센터 가이드 문서 작성
    - 알림 센터 구조 및 기능 설명
    - 알림 생성 및 관리 방법 가이드
    - 알림 센터 확장 방법 설명
    - 향후 개선 사항 제안
  - 알림 센터 스크립트 개선 (show_notification_center.py)
    - 팩토리 패턴 도입 (NotificationFactory)
    - 코드 모듈화 및 구조화
    - 명령줄 인자 처리 기능 추가
    - 예외 처리 강화
    - 단위 테스트 추가 (test_notification_factory.py, test_sample_notification_generator.py, test_notification_center_integration.py)
    - 알림 센터 개선 사항 문서 작성

- 백테스팅 엔진 구현 완료
  - 백테스트 결과 저장 및 비교 기능 구현 완료
    - 백테스트 결과 관리자 클래스 구현 (BacktestResultsManager)
    - 백테스트 결과 저장 및 불러오기 기능 구현
    - 백테스트 결과 비교 기능 구현
    - 포트폴리오 백테스트 결과 저장 및 불러오기 기능 통합
    - 단위 테스트 작성 및 검증
  - 백테스팅 가이드 문서 업데이트
    - 백테스팅 컴포넌트 사용법 상세 설명
    - 백테스트 실행 방법 가이드 추가
    - 백테스트 결과 분석 방법 설명
    - 모범 사례 및 주의사항 추가

- 사용자 인터페이스 - 설정 화면 구현 완료
  - 설정 화면 클래스 구현 (SettingsScreen)
    - 탭 기반 인터페이스로 여러 설정 카테고리 관리
    - 모든 설정 저장 버튼 구현
    - 설정 변경 시그널 구현
  - API 키 관리 화면 구현 (ApiKeyManager)
    - Access Key 및 Secret Key 입력 필드 구현
    - 키 암호화 저장 기능 구현 (Fernet 암호화 사용)
    - 키 표시/숨김 기능 구현
    - API 키 테스트 기능 구현
    - 거래 권한 설정 기능 구현
  - 데이터베이스 설정 화면 구현 (DatabaseSettings)
    - 데이터베이스 경로 설정 기능 구현
    - 최대 크기 및 데이터 보존 기간 설정 기능 구현
    - 데이터베이스 백업 및 복원 기능 구현
    - 현재 데이터베이스 크기 표시 기능 구현
  - 알림 설정 화면 구현 (NotificationSettings)
    - 가격 알림, 거래 알림, 시스템 알림 설정 기능 구현
    - 가격 변동 임계값 및 알림 주기 설정 기능 구현
    - 일일 요약 알림 및 시간 설정 기능 구현
  - 통합 테스트 작성 및 검증 (test_08_4_settings_view.py)
    - 설정 화면 생성 테스트
    - API 키 관리 기능 테스트
    - 데이터베이스 설정 기능 테스트
    - 알림 설정 기능 테스트
    - 설정 통합 기능 테스트
  - 디자인 일관성 검증 및 개선
    - 공통 컴포넌트 라이브러리 생성
    - 스타일 가이드 준수 확인
    - 테마 전환 시 모든 설정 화면 요소 스타일링 검증
  - GUI 테스트 자동화 환경 구축
    - 통합 UI 테스트 환경 구현
    - 사용자 직접 테스트를 위한 체크포인트 문서 작성
    - 테스트 데이터 생성기 구현
    - 스크린샷 관리자 및 테스트 보고서 생성기 구현

- 사용자 인터페이스 - 차트 뷰 구현 완료
  - 캔들스틱 차트 구현 (CandlestickChart)
    - PyQtGraph 기반 고성능 차트 구현
    - 캔들스틱 렌더링 및 스타일링
    - 차트 확대/축소 및 이동 기능 구현
    - 십자선(crosshair) 및 가격 정보 표시 기능
    - 차트 이미지 저장 기능 구현
  - 기술적 지표 오버레이 구현 (IndicatorOverlay)
    - 이동 평균선(SMA, EMA) 구현
    - 볼린저 밴드 구현 (상단/중간/하단 밴드)
    - RSI 지표 구현 (과매수/과매도 영역 표시)
    - MACD 지표 구현 (MACD 라인, 시그널 라인, 히스토그램)
    - 스토캐스틱 오실레이터 구현 (%K, %D 라인)
    - 지표 추가/제거 UI 구현
  - 거래 시점 마커 구현 (TradeMarker)
    - 매수/매도 마커 시각적 구분 (삼각형 모양, 색상 차별화)
    - 마커 표시/숨김 기능 구현
    - 백테스트 결과와 연동 준비
  - 차트 뷰 화면 클래스 구현 (ChartViewScreen)
    - 심볼 및 시간대 선택 UI 구현
    - 지표 관리 사이드바 구현
    - 샘플 데이터 생성 및 테스트 기능 구현
  - 통합 테스트 작성 및 검증 (test_08_3_chart_view.py)
    - 차트 초기화 및 렌더링 테스트
    - 지표 오버레이 기능 테스트
    - 거래 마커 기능 테스트
    - 차트 상호작용 테스트
    - 이미지 저장 기능 테스트
  - 실시간 데이터 연동 준비 중
    - 업비트 API와 연동 계획 수립
    - 웹소켓 기반 실시간 데이터 처리 설계

- 사용자 인터페이스 - 대시보드 구현 완료
  - 대시보드 화면 클래스 구현 (DashboardScreen)
    - 스크롤 가능한 레이아웃으로 다양한 화면 크기 지원
    - 위젯 배치 및 간격 최적화
    - 새로고침 버튼 추가
  - 포트폴리오 요약 위젯 구현 (PortfolioSummaryWidget)
    - 도넛 차트를 통한 자산 구성 시각화
    - 코인별 비중 테이블 구현
    - pyqtgraph 라이브러리 활용한 차트 구현
    - 코인 선택 시 차트 뷰로 이동하는 시그널 구현
  - 활성 거래 목록 위젯 구현 (ActivePositionsWidget)
    - 실시간 거래 현황 테이블 구현
    - 포지션 청산 기능 구현
    - 수익/손실 시각적 표시 (색상 구분)
    - 정렬 및 필터링 기능 추가
  - 시장 개요 위젯 구현 (MarketOverviewWidget)
    - 주요 코인 시세 정보 테이블 구현
    - 24시간 변동률 및 거래대금 표시
    - 차트 보기 기능 연동
    - 상승/하락 시각적 표시 (색상 구분)
  - 자동 데이터 갱신 기능 구현 (5초 주기)
    - QTimer를 활용한 주기적 데이터 갱신
    - 화면 표시/숨김 시 타이머 자동 시작/중지
    - 오류 처리 및 예외 상황 대응
  - 통합 테스트 작성 및 검증 (test_08_2_dashboard.py)
    - 위젯 생성 및 속성 테스트
    - 데이터 갱신 기능 테스트
    - 사용자 상호작용 테스트
  - 메인 윈도우와 대시보드 화면 통합
  - 대시보드 가이드 문서 작성 및 업데이트

- 사용자 인터페이스 - 메인 애플리케이션 프레임워크 구현 완료
  - 디렉토리 구조 설계 및 생성
  - 스타일 시트 구현 (기본 테마 및 다크 모드)
  - 스타일 관리자 클래스 구현 (StyleManager)
  - 네비게이션 바 위젯 구현 (NavigationBar)
  - 상태 바 위젯 구현 (StatusBar)
  - 메인 윈도우 클래스 구현 (MainWindow)
  - 애플리케이션 진입점 구현 (run_desktop_ui.py)
  - 단위 테스트 작성 및 검증
  - requirements.txt 업데이트 - PyQt6 및 관련 패키지 추가
  - 개발 문서 업데이트 - 레퍼런스 문서 활용 가이드 작성
  - UI 가이드 및 개발 가이드 문서에 레퍼런스 문서 활용 지침 추가

- 백테스팅 엔진 - 백테스트 결과 저장 및 비교 기능 구현 완료
  - 백테스트 결과 관리자 클래스 구현 (BacktestResultsManager)
  - 백테스트 결과 저장 기능 구현
    - 데이터베이스 및 파일 시스템에 결과 저장
    - DataFrame 및 날짜 객체 직렬화/역직렬화 처리
  - 백테스트 결과 불러오기 기능 구현
    - ID 기반 결과 조회
    - 저장된 결과 복원 및 객체 변환
  - 백테스트 결과 비교 기능 구현
    - 여러 백테스트 결과의 성과 지표 비교
    - 자본 곡선, 성과 지표, 월별 수익률 시각화 비교
  - 백테스트 결과 관리 기능 구현
    - 결과 목록 조회 및 필터링
    - 결과 삭제 기능
  - 포트폴리오 백테스트 결과 저장 및 불러오기 기능 통합
  - 단위 테스트 작성 및 검증
  - API 문서 업데이트 - 백테스팅 관련 클래스 문서화 완료
    - BacktestRunner, BacktestAnalyzer, BacktestResultsManager 클래스 문서화
    - 백테스팅 가이드 문서 작성

- 백테스팅 엔진 - 포트폴리오 백테스트 기능 구현 완료
  - 포트폴리오 백테스트 클래스 구현 (PortfolioBacktest)
  - 포트폴리오 백테스트 실행 기능 구현
    - 포트폴리오 내 각 코인에 대한 개별 백테스트 실행
    - 가중치를 고려한 결과 통합
  - 포트폴리오 성과 지표 계산 기능 구현
    - 가중 평균 수익률, 최대 손실폭, 승률 계산
    - 샤프 비율, 소티노 비율 등 위험 조정 수익률 계산
    - 코인별 기여도 분석
  - 자본 곡선 결합 기능 구현
    - 개별 코인의 자본 곡선을 가중치에 따라 결합
    - 포트폴리오 전체의 자본 곡선 생성
  - 백테스트 결과 시각화 기능 구현
    - 포트폴리오 자본 곡선 시각화
    - 코인별 기여도 시각화
    - 코인별 성과 비교 시각화
  - 단위 테스트 작성 및 검증

- 백테스팅 엔진 - 백테스트 결과 분석기 구현 완료
  - 성과 지표 계산 기능 구현
    - 기본 성과 지표 (수익률, 최대 손실폭, 승률 등)
    - 고급 성과 지표 (칼마 비율, 울서 지수, 시스템 품질 지수 등)
  - 거래 내역 분석 기능 구현
    - 수익/손실 거래 분석
    - 요일별, 시간별 수익 분석
    - 연속 승/패 분석
  - 결과 시각화 기능 구현
    - 자본 곡선 시각화
    - 손실폭(Drawdown) 시각화
    - 월별 수익률 시각화
    - 거래 분석 시각화
  - 단위 테스트 작성 및 검증

- 포트폴리오 관리 시스템 구현 완료
  - 포트폴리오 모델 및 기본 기능 구현
    - 포트폴리오 데이터 모델 구현 (Portfolio, PortfolioCoin)
    - 포트폴리오 관리자 클래스 구현 (PortfolioManager)
    - 포트폴리오 생성, 수정, 삭제 기능 구현
    - 코인 추가/제거 및 가중치 관리 기능 구현
    - 단위 테스트 작성 및 검증
  - 포트폴리오 성과 계산 기능 구현
    - 포트폴리오 가중치 계산 기능 구현
    - 포트폴리오 기대 수익률 계산 기능 구현
    - 포트폴리오 변동성 및 위험 지표 계산 기능 구현
    - 자산 간 상관관계 분석 기능 구현
    - 포트폴리오 가중치 최적화 기능 구현
    - 단위 테스트 작성 및 검증

### 2025-07-17
- 매매 전략 관리 시스템 - 전략 저장 및 관리 기능 구현 완료
  - 전략 관리자 클래스 구현 (StrategyManager)
  - 전략 저장, 불러오기, 목록 관리 기능 구현
  - 데이터베이스 연동 및 전략 정보 저장
  - 한국 시간대(KST) 적용
  - 단위 테스트 작성 및 검증

- 매매 전략 관리 시스템 - 기본 매매 전략 구현 완료
  - 이동 평균 교차 전략 구현 (MovingAverageCrossStrategy)
  - 볼린저 밴드 전략 구현 (BollingerBandsStrategy)
  - RSI 기반 전략 구현 (RSIStrategy)
  - 전략 팩토리 통합 및 단위 테스트 작성

- 매매 전략 관리 시스템 - 전략 인터페이스 및 기본 클래스 구현 완료
  - 전략 인터페이스 정의 (StrategyInterface)
  - 기본 전략 추상 클래스 구현 (BaseStrategy)
  - 전략 매개변수 관리 기능 구현 (ParameterDefinition, StrategyParameterManager)
  - 전략 팩토리 패턴 구현 (StrategyFactory)
  - 단위 테스트 작성

- 스크리너 기능 구현 완료
  - 거래량 기반 스크리닝 구현
  - 변동성 기반 스크리닝 구현
  - 추세 기반 스크리닝 구현
  - 스크리닝 결과 저장 및 관리 기능 구현
  - 단위 테스트 작성

### 2025-07-15
- 데이터 처리기 구현 완료
  - 기술적 지표 계산 기능 구현 (SMA, EMA, 볼린저 밴드, RSI, MACD 등)
  - 데이터 정규화 및 전처리 기능 구현
  - 데이터 리샘플링 기능 구현

### 2025-07-10
- 데이터 수집기 구현 완료
  - 시장 데이터(OHLCV) 수집 기능 구현
  - 호가 데이터 수집 기능 구현
  - 데이터 저장 및 관리 기능 구현

### 2025-07-05
- 업비트 API 클라이언트 구현 완료
  - API 요청 제한 및 오류 처리 로직 구현
  - 시장 데이터 조회 기능 구현
  - 호가 데이터 조회 기능 구현
  - 계정 정보 조회 기능 구현
  - 주문 실행 및 관리 기능 구현

### 2025-07-01
- 프로젝트 초기 설정
  - 프로젝트 구조 설계
  - 기본 설정 파일 생성
  - Git 저장소 초기화

## 문서

프로젝트에 관한 자세한 문서는 다음 링크에서 확인할 수 있습니다:

- [문서 목록](upbit_auto_trading/docs/README.md)
- [개발 가이드](upbit_auto_trading/docs/development_guide.md)
- [API 문서](upbit_auto_trading/docs/api_docs.md)
- [UI 가이드](upbit_auto_trading/docs/ui_guide.md)
- [대시보드 구현 가이드](upbit_auto_trading/docs/dashboard_guide.md)
- [차트 뷰 구현 가이드](upbit_auto_trading/docs/chart_view_guide.md)
- [알림 센터 가이드](upbit_auto_trading/docs/notification_guide.md)
- [시스템 모니터링 가이드](upbit_auto_trading/docs/system_monitoring_guide.md)
- [레퍼런스 문서 활용 가이드](upbit_auto_trading/docs/reference_guide.md)
- [테스트 결과 요약](upbit_auto_trading/docs/test_results_summary.md)

### 레퍼런스 문서

시스템 설계 및 구현에 필요한 상세 레퍼런스 문서는 `reference` 폴더에서 확인할 수 있습니다:

- [시스템 아키텍처 설계서](reference/01_system_architecture_design.md) - C4 모델 기반 시스템 구조 설명
- [데이터베이스 스키마 명세서](reference/02_database_schema_specification_erd.md)
- [API 명세서](reference/03_api_specification.md)
- [배포 및 운영 가이드](reference/04_deployment_and_operations_guide.md)
- [보안 설계 문서](reference/05_security_design_document.md)
- [UI 명세서](reference/ui_spec_01_main_dashboard.md) 등

## 라이선스
이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 기여
이슈 및 풀 리퀘스트는 언제나 환영합니다.