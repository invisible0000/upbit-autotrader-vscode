"""
실시간 로깅 관리 탭 (Logging Management Tab)
=========================================

DDD 아키텍처 기반 실시간 로깅 관리 UI
Infrastructure Layer 로깅 시스템 v4.0과 완전 통합

주요 기능:
- 실시간 로그 뷰어 (QPlainTextEdit 최적화)
- 환경변수 통합 제어 (UPBIT_LOG_LEVEL, UPBIT_CONSOLE_OUTPUT 등)
- MVP 패턴 적용 (Passive View + Presenter)
- 성능 최적화 (배치 업데이트, 탭 활성화 최적화)

Phase 1: MVP 기본 구현
Phase 2: Infrastructure 통합
Phase 3: 최적화 및 LLM 제거
"""

# Phase 1: 기본 MVP 구현 완료 후 import 활성화
try:
    from .logging_management_view import LoggingManagementView
    from .presenters.logging_management_presenter import LoggingManagementPresenter

    __all__ = [
        'LoggingManagementView',
        'LoggingManagementPresenter'
    ]
except ImportError:
    # 개발 중 임시 처리
    __all__ = []
