# Upbit Autotrader 데스크탑 UI 개발 주요 코드/클래스/함수 정리

## 1. 실행/엔트리 파일
- `run_desktop_ui.py` : 데스크탑 UI 실행 스크립트
- `upbit_auto_trading/ui/desktop/run.py` : 앱 실행 진입점
- `upbit_auto_trading/ui/desktop/app.py` : 앱 초기화 및 실행
- `upbit_auto_trading/ui/desktop/main.py` : run_app(), MainWindow

## 2. 메인 윈도우/화면 관리
- `upbit_auto_trading/ui/desktop/main_window.py`
  - 클래스: `MainWindow`
  - 주요 화면 인스턴스: `SettingsScreen`, `ApiKeyManager`

## 3. 화면별 주요 클래스/파일
- `upbit_auto_trading/ui/desktop/screens/settings/settings_screen.py`
  - 클래스: `SettingsScreen`, `ApiKeyManager`, `DatabaseSettings`, `NotificationSettings`
- `upbit_auto_trading/ui/desktop/screens/asset_screener/asset_screener_screen.py`
  - 클래스: `AssetScreenerScreen` (자산 스크리닝 화면)
  - 주요 UI 컨트롤: 필터 조건(한 줄 4개 배치), 결과 테이블(체크박스, 종목 등록/검색), 종목 선택/등록 기능
  - 메서드: `init_ui()`, 필터 적용, 결과 테이블 렌더링, 종목 등록/검색

## 4. 주요 함수/메서드
- `run_app()` : 앱 실행
- 각 화면별 `init_ui()` : UI 초기화
- AssetScreenerScreen: 필터 조건 배치, 결과 테이블 체크박스/종목 등록/검색 UI, 종목 선택/등록 기능, 백테스팅 연동 설계
- 기타 화면별 주요 메서드(예: 필터 적용, 결과 테이블 렌더링 등)

## 5. 인스턴스/연동 구조
- MainWindow에서 각 화면 인스턴스 관리 및 화면 스택 연결
- SettingsScreen, AssetScreenerScreen 등은 별도 파일/클래스로 분리
- AssetScreenerScreen은 메인 대시보드 탭에서 화면 연결, 네비게이션/인덱스 관리

---

> 본 문서는 데스크탑 UI 개발에 실제 사용되는 주요 코드, 클래스, 함수, 인스턴스 구조를 정리하여 관리합니다. 새로운 화면/기능 추가 및 asset_screener 등 주요 UI/기능 변경 시 본 문서에 반드시 업데이트 바랍니다.
