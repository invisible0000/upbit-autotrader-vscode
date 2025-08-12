"""
로깅 관리 위젯 컴포넌트들

DDD+MVP 패턴에 따른 재사용 가능한 UI 위젯들입니다.
로깅 관리와 관련된 개별 컴포넌트들을 제공합니다.

구현된 위젯들:
- BatchedLogUpdater: 성능 최적화된 배치 로그 업데이터

향후 추가될 위젯들:
- OptimizedLogViewer: 성능 최적화된 로그 뷰어
- TabActivationOptimizer: 탭 활성화 최적화
- EnvironmentControlPanel: 환경변수 제어 패널
"""

from .batched_log_updater import BatchedLogUpdater

# Phase 1에서는 빈 파일로 시작
__all__ = ['BatchedLogUpdater']
