"""
Presentation Layer Package - MVP 패턴 기반

Clean Architecture의 Presentation Layer를 구현합니다.
MVP(Model-View-Presenter) 패턴을 통해 UI와 비즈니스 로직을 완전히 분리합니다.

구조:
- interfaces/: View 인터페이스 정의
- presenters/: Presenter 구현체들
- views/: Passive View 구현체들
- view_models/: View에 필요한 데이터 모델들
- mvp_container.py: MVP 의존성 주입 컨테이너
"""

from .mvp_container import MVPContainer, initialize_mvp_system, get_mvp_container

__all__ = [
    'MVPContainer',
    'initialize_mvp_system',
    'get_mvp_container'
]
