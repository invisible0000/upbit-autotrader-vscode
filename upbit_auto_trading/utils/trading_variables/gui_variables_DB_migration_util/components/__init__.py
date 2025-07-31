#!/usr/bin/env python3
"""
🎯 Trading Variables DB Migration GUI Components
GUI 마이그레이션 도구의 컴포넌트 모듈

작성일: 2025-07-30
업데이트: 2025-07-31 (Phase 3 - 성능 최적화 및 모듈 정리)
버전: 1.1.0
"""

# 메인 GUI 컴포넌트들
from .db_selector import DatabaseSelectorFrame
from .variables_viewer import VariablesViewerFrame
from .migration_preview import MigrationPreviewFrame
from .migration_executor import MigrationExecutorFrame
from .backup_manager import BackupManagerFrame
from .agent_info import AgentInfoFrame
from .json_viewer import JsonViewerFrame
from .sync_db_to_code import SyncDBToCodeFrame
from .migration_tab import YAMLSyncTabFrame

# 유틸리티 모듈들
from .gui_utils import (
    StandardButton, StatusLabel, ProgressFrame, StandardFrame,
    GUIStyles, MessageUtils, LayoutUtils, AsyncOperationMixin,
    create_standard_button, create_status_label, create_progress_frame
)
from .performance_utils import (
    PerformanceOptimizedDBManager, DatabaseConnectionPool, QueryCache,
    get_db_manager, close_all_db_managers, monitor_performance
)

# 데이터 처리 모듈들
from .data_info_migrator import DataInfoMigrator
from .unified_code_generator import UnifiedVariableDefinitionsGenerator
from .code_generator import VariableDefinitionsGenerator

__all__ = [
    # 메인 GUI 컴포넌트
    'DatabaseSelectorFrame',
    'VariablesViewerFrame', 
    'MigrationPreviewFrame',
    'MigrationExecutorFrame',
    'BackupManagerFrame',
    'AgentInfoFrame',
    'JsonViewerFrame',
    'SyncDBToCodeFrame',
    'YAMLSyncTabFrame',
    
    # GUI 유틸리티
    'StandardButton',
    'StatusLabel', 
    'ProgressFrame',
    'StandardFrame',
    'GUIStyles',
    'MessageUtils',
    'LayoutUtils',
    'AsyncOperationMixin',
    'create_standard_button',
    'create_status_label',
    'create_progress_frame',
    
    # 성능 최적화
    'PerformanceOptimizedDBManager',
    'DatabaseConnectionPool',
    'QueryCache',
    'get_db_manager',
    'close_all_db_managers',
    'monitor_performance',
    
    # 데이터 처리
    'DataInfoMigrator',
    'UnifiedVariableDefinitionsGenerator',
    'VariableDefinitionsGenerator'
]

__version__ = "1.1.0"
__author__ = "Trading Variables DB Migration Team"
__description__ = "GUI components for Trading Variables database migration with performance optimization"
