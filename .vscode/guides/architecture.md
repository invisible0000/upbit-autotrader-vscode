# 아키텍처 가이드

## 🏗️ 컴포넌트 구조
```
upbit_auto_trading/
├── ui/desktop/screens/        # 화면별 UI
├── component_system/          # 핵심 컴포넌트
├── data_providers/           # 데이터 제공자
└── utils/debug_logger.py     # 통합 디버깅 시스템 v2.3
```

## 🎯 개발 원칙
- 컴포넌트 기반 모듈러 설계
- PyQt6 시그널/슬롯 활용
- 지연 로딩으로 성능 최적화
- 조건부 컴파일로 배포 최적화 (NEW)
- **폴백 제거**: 에러를 숨기지 않고 명확히 드러내기 (`.vscode/guides/fallback-removal-policy.md`)

## 🚨 에러 처리 철학
**"동작이 안되면 화면이 비고 에러가 표시되는게 훨씬 개발에 도움이 됩니다"**
- 폴백 코드로 문제를 숨기지 않음
- ModuleNotFoundError 등이 발생하면 정확한 경로 문제를 즉시 파악
- "종기의 고름을 빼는" 방식으로 근본 원인 해결

## 🔬 통합 디버깅 시스템 v2.3
```python
# 컴포넌트별 로거 생성
logger = get_logger("ComponentName")

# 환경별 자동 최적화
if logger.should_log_debug():  # 프로덕션에서 자동 스킵
    logger.debug("🔍 상세 디버그 정보")

# 성능 모니터링
logger.performance("⚡ DB 쿼리 완료: 0.5초")
```

## 🔄 테스트 필수
모든 변경 후: `python run_desktop_ui.py`
