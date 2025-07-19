# COPILOT_GUI_SCREEN_STRUCTURE.md

프로젝트의 GUI 화면 폴더 구조 및 설계 기준

---

## 1. 폴더 구조 기준

- 모든 주요 GUI 화면은 `upbit_auto_trading/ui/desktop/screens/` 하위에 폴더별로 분리하여 구현한다.
- 각 폴더는 `reference/ui_spec_*.md` 문서의 화면 정의를 기준으로 생성 및 관리한다.
- 예시:
    - dashboard
    - chart_view
    - coin_screener
    - strategy_management
    - backtesting
    - live_trading
    - portfolio_configuration
    - monitoring_and_alerts
    - settings
    - notification_center

## 2. 화면 정의와 코드 연동

- 각 폴더의 화면/위젯/컴포넌트는 해당 `ui_spec_*.md`의 요구사항과 디자인을 반드시 반영한다.
- 화면별 주요 클래스와 진입점은 폴더 내 `*_screen.py`로 통일한다.
- 화면별 위젯/컴포넌트는 `widgets/` 서브폴더에 분리한다.

## 3. 유지보수 및 명시

- 이 파일(`COPILOT_GUI_SCREEN_STRUCTURE.md`)은 폴더 구조와 설계 기준의 변경/추가/삭제 시 반드시 최신화한다.
- 모든 신규 화면/폴더/컴포넌트 추가 시 이 문서에 명시하고, reference/ui_spec_*.md와 동기화한다.

## 4. 예시

```
upbit_auto_trading/ui/desktop/screens/
├─dashboard/
├─chart_view/
├─coin_screener/
├─strategy_management/
├─backtesting/
├─live_trading/
├─portfolio_configuration/
├─monitoring_and_alerts/
├─settings/
├─notification_center/
```

---

> 이 구조와 기준은 프로젝트의 GUI 일관성, 유지보수성, 명확한 역할 분리를 위해 반드시 준수해야 한다.
> 모든 개발자는 이 문서를 참고하여 폴더/화면/컴포넌트 추가 및 변경 시 기준을 따를 것.
