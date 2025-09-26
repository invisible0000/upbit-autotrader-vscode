"""
QAsync Runtime Infrastructure
메인 런타임 컴포넌트들을 제공하는 패키지
"""

from .loop_guard import (
    LoopGuard,
    LoopViolation,
    get_loop_guard,
    ensure_main_loop,
    register_component,
    set_main_loop,
    loop_protected
)
from .app_kernel import (
    AppKernel,
    KernelConfig,
    TaskManager,
    get_kernel,
    create_task
)

__all__ = [
    'LoopGuard',
    'LoopViolation',
    'get_loop_guard',
    'ensure_main_loop',
    'register_component',
    'set_main_loop',
    'loop_protected',
    'AppKernel',
    'KernelConfig',
    'TaskManager',
    'get_kernel',
    'create_task'
]
