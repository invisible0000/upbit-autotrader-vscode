#!/usr/bin/env python3
"""
🎯 Trading Variables DB Migration GUI Tool
매매 변수 데이터베이스 마이그레이션을 위한 GUI 도구

주요 기능:
1. DB 파일 선택 및 기존 변수/파라미터 조회
2. 새로운 스키마 미리보기 및 변경사항 검토
3. 안전한 마이그레이션 실행 (세밀한 백업 기능)
4. 롤백 및 복원 기능

작성일: 2025-07-30
버전: 1.0.0
"""

import sys
import os
import tkinter as tk
from tkinter import ttk

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
sys.path.insert(0, project_root)

from components.db_selector import DatabaseSelectorFrame
from components.variables_viewer import VariablesViewerFrame
from components.migration_preview import MigrationPreviewFrame
from components.migration_executor import MigrationExecutorFrame
from components.backup_manager import BackupManagerFrame
from components.agent_info import AgentInfoFrame
from components.json_viewer import JsonViewerFrame
from components.sync_db_to_code import SyncDBToCodeFrame
from components.advanced_migration_tab import AdvancedMigrationTab


class TradingVariablesDBMigrationGUI:
    """Trading Variables DB Migration GUI 메인 클래스"""
    
    def __init__(self, root):
        """
        GUI 초기화
        
        Args:
            root: Tkinter 루트 윈도우
        """
        self.root = root
        self.root.title("🎯 Trading Variables DB Migration Tool v1.0")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # 현재 선택된 DB 경로
        self.current_db_path = None
        self.migration_data = None
        
        # GUI 컴포넌트 초기화
        self.setup_gui()
        
        # 기본 DB 경로 설정
        self.set_default_db_path()
    
    def setup_gui(self):
        """GUI 레이아웃 설정"""
        # 메인 타이틀
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill='x', padx=5, pady=5)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="🎯 Trading Variables Database Migration Tool",
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='#2c3e50'
        )
        title_label.pack(expand=True)
        
        # 메인 노트북 (탭 컨테이너)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 탭 1: DB 선택 및 현재 상태
        self.tab1 = tk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="📁 DB 선택 & 현재 상태")
        
        # 탭 2: 변수 및 파라미터 조회
        self.tab2 = tk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="📊 변수 & 파라미터 조회")
        
        # 탭 3: 마이그레이션 미리보기
        self.tab3 = tk.Frame(self.notebook)
        self.notebook.add(self.tab3, text="🔍 마이그레이션 미리보기")
        
        # 탭 4: 마이그레이션 실행
        self.tab4 = tk.Frame(self.notebook)
        self.notebook.add(self.tab4, text="🚀 마이그레이션 실행")
        
        # 탭 5: 백업 관리
        self.tab5 = tk.Frame(self.notebook)
        self.notebook.add(self.tab5, text="💾 백업 관리")
        
        # 탭 6: 에이전트 정보 요약
        self.tab6 = tk.Frame(self.notebook)
        self.notebook.add(self.tab6, text="🤖 AI 에이전트 정보")
        
        # 탭 7: JSON 데이터 뷰어
        self.tab7 = tk.Frame(self.notebook)
        self.notebook.add(self.tab7, text="📋 JSON 데이터 뷰어")
        
        # 탭 8: DB → Code 동기화
        self.tab8 = tk.Frame(self.notebook)
        self.notebook.add(self.tab8, text="🔄 DB → Code 동기화")
        
        # 탭 9: 고급 마이그레이션 (NEW!)
        self.tab9 = tk.Frame(self.notebook)
        self.notebook.add(self.tab9, text="🚀 고급 마이그레이션")
        
        # 각 탭의 컴포넌트 초기화
        self.init_tab_components()
        
        # 기본 탭을 DB 선택으로 설정
        self.notebook.select(0)
        
        # 상태바
        self.setup_status_bar()
    
    def init_tab_components(self):
        """각 탭의 컴포넌트 초기화"""
        # 탭 1: DB 선택기
        self.db_selector = DatabaseSelectorFrame(
            self.tab1, 
            on_db_selected=self.on_db_selected
        )
        self.db_selector.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 탭 2: 변수 뷰어
        self.variables_viewer = VariablesViewerFrame(self.tab2)
        self.variables_viewer.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 탭 3: 마이그레이션 미리보기
        self.migration_preview = MigrationPreviewFrame(self.tab3)
        self.migration_preview.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 탭 4: 마이그레이션 실행기
        self.migration_executor = MigrationExecutorFrame(
            self.tab4,
            on_migration_complete=self.on_migration_complete
        )
        self.migration_executor.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 탭 5: 백업 관리자
        self.backup_manager = BackupManagerFrame(self.tab5)
        self.backup_manager.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 탭 6: AI 에이전트 정보
        self.agent_info = AgentInfoFrame(self.tab6)
        self.agent_info.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 탭 7: JSON 데이터 뷰어
        self.json_viewer = JsonViewerFrame(self.tab7)
        self.json_viewer.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 탭 8: DB → Code 동기화
        self.sync_db_to_code = SyncDBToCodeFrame(self.tab8)
        self.sync_db_to_code.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 탭 9: 고급 마이그레이션 (NEW!)
        self.advanced_migration = AdvancedMigrationTab(self.notebook, self)
    
    def setup_status_bar(self):
        """상태바 설정"""
        self.status_frame = tk.Frame(self.root, relief='sunken', bd=1)
        self.status_frame.pack(side='bottom', fill='x')
        
        self.status_label = tk.Label(
            self.status_frame,
            text="준비 완료 - DB를 선택하세요",
            anchor='w'
        )
        self.status_label.pack(side='left', padx=5, pady=2)
        
        # 현재 DB 경로 표시
        self.db_path_label = tk.Label(
            self.status_frame,
            text="DB: 선택되지 않음",
            anchor='e',
            fg='blue'
        )
        self.db_path_label.pack(side='right', padx=5, pady=2)
    
    def set_default_db_path(self):
        """기본 DB 경로 설정"""
        default_db = os.path.join(
            project_root, 
            "upbit_auto_trading", 
            "data", 
            "settings.sqlite3"
        )
        
        if os.path.exists(default_db):
            self.current_db_path = default_db
            self.db_selector.set_db_path(default_db)
            self.update_status("기본 DB 경로 설정됨")
            self.update_db_path_display()
        else:
            self.update_status("기본 DB 파일을 찾을 수 없음 - 수동으로 선택하세요")
    
    def on_db_selected(self, db_path, auto_switch_tab=True):
        """
        DB가 선택되었을 때 호출되는 콜백
        
        Args:
            db_path: 선택된 DB 파일 경로
            auto_switch_tab: 자동으로 변수 뷰어 탭으로 전환할지 여부 (기본값: True)
        """
        self.current_db_path = db_path
        self.update_db_path_display()
        
        # 모든 컴포넌트에 DB 경로 전달
        self.variables_viewer.set_db_path(db_path)
        self.migration_preview.set_db_path(db_path)
        self.migration_executor.set_db_path(db_path)
        self.backup_manager.set_db_path(db_path)
        self.agent_info.set_db_path(db_path)
        self.json_viewer.set_db_path(db_path)
        self.sync_db_to_code.set_db_path(db_path)
        
        self.update_status(f"DB 선택됨: {os.path.basename(db_path)}")
        
        # 새로고침이 아닌 경우에만 변수 뷰어 탭으로 자동 전환
        if auto_switch_tab:
            self.notebook.select(1)
    
    def on_migration_complete(self, success, backup_path=None):
        """
        마이그레이션 완료 시 호출되는 콜백
        
        Args:
            success: 성공 여부
            backup_path: 백업 파일 경로 (성공 시)
        """
        if success:
            self.update_status("✅ 마이그레이션 완료!")
            if backup_path:
                self.backup_manager.refresh_backup_list()
        else:
            self.update_status("❌ 마이그레이션 실패")
    
    def update_status(self, message):
        """
        상태바 메시지 업데이트
        
        Args:
            message: 표시할 메시지
        """
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def update_db_path_display(self):
        """DB 경로 표시 업데이트"""
        if self.current_db_path:
            display_path = os.path.basename(self.current_db_path)
            self.db_path_label.config(text=f"DB: {display_path}")
        else:
            self.db_path_label.config(text="DB: 선택되지 않음")


def main():
    """메인 함수"""
    # Tkinter 루트 윈도우 생성
    root = tk.Tk()
    
    # 윈도우 아이콘 설정 (있다면)
    try:
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except:
        pass
    
    # GUI 애플리케이션 시작
    app = TradingVariablesDBMigrationGUI(root)
    
    # 메인 루프 시작
    root.mainloop()


if __name__ == "__main__":
    main()
