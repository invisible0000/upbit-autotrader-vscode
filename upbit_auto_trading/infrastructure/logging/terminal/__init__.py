"""
Terminal Integration Module
===========================

실시간 터미널 출력 캡쳐 및 LLM 동기화 시스템
"""

# 터미널 캡쳐 시스템
from .terminal_capturer import (
    TeeOutput,
    TerminalCapturer,
    get_terminal_capturer,
    start_terminal_capture,
    stop_terminal_capture,
    get_captured_output
)

# 출력 파싱 시스템
from .output_parser import (
    OutputType,
    ParsedOutput,
    TerminalOutputParser,
    create_terminal_output_parser
)

# 로그 동기화 시스템
from .log_synchronizer import (
    SyncState,
    SyncConfig,
    LogSynchronizer,
    get_log_synchronizer,
    create_log_synchronizer
)

__all__ = [
    # Terminal Capturer
    'TeeOutput',
    'TerminalCapturer',
    'get_terminal_capturer',
    'start_terminal_capture',
    'stop_terminal_capture',
    'get_captured_output',

    # Output Parser
    'OutputType',
    'ParsedOutput',
    'TerminalOutputParser',
    'create_terminal_output_parser',

    # Log Synchronizer
    'SyncState',
    'SyncConfig',
    'LogSynchronizer',
    'get_log_synchronizer',
    'create_log_synchronizer'
]
