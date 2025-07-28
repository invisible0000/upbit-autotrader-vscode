# 아키텍처 가이드

## 🏗️ 컴포넌트 구조
```
upbit_auto_trading/
├── ui/desktop/screens/        # 화면별 UI
├── component_system/          # 핵심 컴포넌트
└── data_providers/           # 데이터 제공자
```

## 🎯 개발 원칙
- 컴포넌트 기반 모듈러 설계
- PyQt6 시그널/슬롯 활용
- 지연 로딩으로 성능 최적화

## 🔄 테스트 필수
모든 변경 후: `python run_desktop_ui.py`
