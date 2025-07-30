#!/usr/bin/env python3
"""
🚀 고급 Data Info 마이그레이션 탭
===============================

variables_* YAML 파일들을 확장된 DB 스키마로 완전 마이그레이션하는 GUI 탭

주요 기능:
1. data_info → DB 전체 마이그레이션
2. 개별 컴포넌트 마이그레이션
3. 마이그레이션 상태 모니터링
4. DB 스키마 업그레이드

작성일: 2025-07-30
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from datetime import datetime
from pathlib import Path

from .advanced_data_info_migrator import AdvancedDataInfoMigrator


class AdvancedMigrationTab:
    """고급 마이그레이션 탭 클래스"""
    
    def __init__(self, parent_notebook, db_manager):
        """
        초기화
        
        Args:
            parent_notebook: 부모 노트북 위젯
            db_manager: DB 관리자 인스턴스
        """
        self.parent_notebook = parent_notebook
        self.db_manager = db_manager
        self.migrator = None
        
        # 탭 생성
        self.tab_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.tab_frame, text="🚀 고급 마이그레이션")
        
        self.setup_ui()
        self.update_status()
    
    def setup_ui(self):
        """UI 구성"""
        # 메인 컨테이너
        main_container = ttk.Frame(self.tab_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === 상단: 상태 정보 ===
        self.setup_status_section(main_container)
        
        # === 중간: 마이그레이션 컨트롤 ===
        self.setup_migration_controls(main_container)
        
        # === 하단: 로그 및 결과 ===
        self.setup_log_section(main_container)
    
    def setup_status_section(self, parent):
        """상태 정보 섹션 구성"""
        status_frame = ttk.LabelFrame(parent, text="📊 현재 상태", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 상태 표시 Grid
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill=tk.X)
        
        # DB 경로 정보
        ttk.Label(status_grid, text="🗄️ 데이터베이스:", font=('', 9, 'bold')).grid(row=0, column=0, sticky='w', padx=(0, 5))
        self.db_path_var = tk.StringVar(value="DB 선택 안됨")
        ttk.Label(status_grid, textvariable=self.db_path_var, foreground='blue').grid(row=0, column=1, sticky='w')
        
        # 스키마 버전
        ttk.Label(status_grid, text="📋 스키마 버전:", font=('', 9, 'bold')).grid(row=1, column=0, sticky='w', padx=(0, 5), pady=(5, 0))
        self.schema_version_var = tk.StringVar(value="확인 중...")
        ttk.Label(status_grid, textvariable=self.schema_version_var).grid(row=1, column=1, sticky='w', pady=(5, 0))
        
        # data_info 경로
        ttk.Label(status_grid, text="📁 data_info 경로:", font=('', 9, 'bold')).grid(row=2, column=0, sticky='w', padx=(0, 5), pady=(5, 0))
        self.data_info_path_var = tk.StringVar(value="자동 감지됨")
        ttk.Label(status_grid, textvariable=self.data_info_path_var, foreground='green').grid(row=2, column=1, sticky='w', pady=(5, 0))
        
        # YAML 파일 상태
        ttk.Label(status_grid, text="📄 YAML 파일:", font=('', 9, 'bold')).grid(row=3, column=0, sticky='w', padx=(0, 5), pady=(5, 0))
        self.yaml_status_var = tk.StringVar(value="확인 중...")
        ttk.Label(status_grid, textvariable=self.yaml_status_var).grid(row=3, column=1, sticky='w', pady=(5, 0))
        
        # 새로고침 버튼
        ttk.Button(status_frame, text="🔄 상태 새로고침", command=self.update_status).pack(anchor='e', pady=(10, 0))
    
    def setup_migration_controls(self, parent):
        """마이그레이션 컨트롤 섹션 구성"""
        control_frame = ttk.LabelFrame(parent, text="⚙️ 마이그레이션 실행", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 버튼 그리드
        button_grid = ttk.Frame(control_frame)
        button_grid.pack(fill=tk.X)
        
        # 1행: 스키마 관련
        ttk.Label(button_grid, text="📋 스키마 관리:", font=('', 9, 'bold')).grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        schema_buttons = ttk.Frame(button_grid)
        schema_buttons.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=(0, 5))
        
        ttk.Button(schema_buttons, text="🔧 스키마 v3.0 업그레이드", 
                  command=self.upgrade_schema).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(schema_buttons, text="🔍 스키마 확인", 
                  command=self.check_schema).pack(side=tk.LEFT)
        
        # 2행: 개별 마이그레이션
        ttk.Label(button_grid, text="🎯 개별 마이그레이션:", font=('', 9, 'bold')).grid(row=1, column=0, sticky='w', pady=(10, 5))
        
        individual_buttons = ttk.Frame(button_grid)
        individual_buttons.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=(10, 5))
        
        ttk.Button(individual_buttons, text="📝 도움말", 
                  command=lambda: self.run_individual_migration('help_texts')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(individual_buttons, text="🎯 플레이스홀더", 
                  command=lambda: self.run_individual_migration('placeholder_texts')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(individual_buttons, text="📚 라이브러리", 
                  command=lambda: self.run_individual_migration('indicator_library')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(individual_buttons, text="📋 워크플로우", 
                  command=lambda: self.run_individual_migration('workflow_guides')).pack(side=tk.LEFT)
        
        # 3행: 전체 마이그레이션
        ttk.Label(button_grid, text="🚀 전체 마이그레이션:", font=('', 9, 'bold')).grid(row=2, column=0, sticky='w', pady=(10, 5))
        
        full_buttons = ttk.Frame(button_grid)
        full_buttons.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=(10, 5))
        
        self.full_migration_btn = ttk.Button(full_buttons, text="🚀 전체 마이그레이션 실행", 
                                           command=self.run_full_migration)
        self.full_migration_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(full_buttons, text="📊 결과 요약", 
                  command=self.show_migration_summary).pack(side=tk.LEFT)
        
        # 진행률 표시
        self.progress_var = tk.StringVar(value="대기 중...")
        ttk.Label(control_frame, textvariable=self.progress_var, font=('', 9)).pack(pady=(10, 0))
        
        self.progress_bar = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
    
    def setup_log_section(self, parent):
        """로그 섹션 구성"""
        log_frame = ttk.LabelFrame(parent, text="📋 마이그레이션 로그", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 로그 텍스트 위젯
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 로그 버튼들
        log_buttons = ttk.Frame(log_frame)
        log_buttons.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(log_buttons, text="🗑️ 로그 지우기", command=self.clear_log).pack(side=tk.LEFT)
        ttk.Button(log_buttons, text="💾 로그 저장", command=self.save_log).pack(side=tk.LEFT, padx=(5, 0))
    
    def update_status(self):
        """상태 정보 업데이트"""
        try:
            # DB 경로 업데이트
            if hasattr(self.db_manager, 'current_db_path') and self.db_manager.current_db_path:
                self.db_path_var.set(str(Path(self.db_manager.current_db_path).name))
                
                # Migrator 초기화
                self.migrator = AdvancedDataInfoMigrator(self.db_manager.current_db_path)
                
                # 스키마 버전 확인
                is_compatible, version = self.migrator.check_schema_version()
                status_color = 'green' if is_compatible else 'orange'
                self.schema_version_var.set(f"{version} ({'호환됨' if is_compatible else 'v3.0 업그레이드 필요'})")
                
                # data_info 경로 확인
                data_info_path = Path(self.migrator.data_info_path)
                if data_info_path.exists():
                    self.data_info_path_var.set(str(data_info_path.name))
                    
                    # YAML 파일 확인
                    yaml_files = list(data_info_path.glob("variables_*.yaml"))
                    self.yaml_status_var.set(f"{len(yaml_files)}개 파일 발견")
                else:
                    self.data_info_path_var.set("경로를 찾을 수 없음")
                    self.yaml_status_var.set("YAML 파일 확인 불가")
            else:
                self.db_path_var.set("DB 선택 안됨")
                self.schema_version_var.set("DB를 먼저 선택하세요")
                self.yaml_status_var.set("-")
                
        except Exception as e:
            self.log_message(f"❌ 상태 업데이트 실패: {str(e)}", "ERROR")
    
    def upgrade_schema(self):
        """스키마 v3.0 업그레이드"""
        if not self.migrator:
            messagebox.showerror("오류", "DB를 먼저 선택하세요.")
            return
        
        if messagebox.askyesno("스키마 업그레이드", 
                              "스키마를 v3.0으로 업그레이드하시겠습니까?\n\n"
                              "⚠️ 이 작업은 되돌릴 수 없습니다.\n"
                              "DB 백업을 권장합니다."):
            
            def upgrade_task():
                self.start_progress("스키마 업그레이드 중...")
                try:
                    success = self.migrator.setup_extended_schema()
                    if success:
                        self.log_message("✅ 스키마 v3.0 업그레이드 완료")
                        self.update_status()
                    else:
                        self.log_message("❌ 스키마 업그레이드 실패", "ERROR")
                finally:
                    self.stop_progress()
            
            threading.Thread(target=upgrade_task, daemon=True).start()
    
    def check_schema(self):
        """스키마 확인"""
        if not self.migrator:
            messagebox.showerror("오류", "DB를 먼저 선택하세요.")
            return
        
        is_compatible, version = self.migrator.check_schema_version()
        
        info_text = f"현재 스키마 버전: {version}\n"
        info_text += f"v3.0 호환성: {'✅ 호환됨' if is_compatible else '❌ 업그레이드 필요'}\n\n"
        
        if is_compatible:
            info_text += "🎉 모든 고급 마이그레이션 기능을 사용할 수 있습니다!"
        else:
            info_text += "⚠️ 고급 마이그레이션을 위해 스키마 업그레이드가 필요합니다."
        
        messagebox.showinfo("스키마 정보", info_text)
    
    def run_individual_migration(self, migration_type):
        """개별 마이그레이션 실행"""
        if not self.migrator:
            messagebox.showerror("오류", "DB를 먼저 선택하세요.")
            return
        
        # 스키마 호환성 확인
        is_compatible, _ = self.migrator.check_schema_version()
        if not is_compatible:
            if messagebox.askyesno("스키마 업그레이드 필요", 
                                  "v3.0 호환 스키마가 필요합니다.\n지금 업그레이드하시겠습니까?"):
                self.upgrade_schema()
                return
            else:
                return
        
        def migration_task():
            self.start_progress(f"{migration_type} 마이그레이션 중...")
            try:
                if migration_type == 'help_texts':
                    success = self.migrator.migrate_help_texts()
                elif migration_type == 'placeholder_texts':
                    success = self.migrator.migrate_placeholder_texts()
                elif migration_type == 'indicator_library':
                    success = self.migrator.migrate_indicator_library()
                elif migration_type == 'workflow_guides':
                    success = self.migrator.migrate_workflow_guides()
                else:
                    success = False
                
                if success:
                    self.log_message(f"✅ {migration_type} 마이그레이션 완료")
                else:
                    self.log_message(f"❌ {migration_type} 마이그레이션 실패", "ERROR")
                    
                # 로그 표시
                for log_entry in self.migrator.migration_log:
                    self.log_message(log_entry)
                
            finally:
                self.stop_progress()
        
        threading.Thread(target=migration_task, daemon=True).start()
    
    def run_full_migration(self):
        """전체 마이그레이션 실행"""
        if not self.migrator:
            messagebox.showerror("오류", "DB를 먼저 선택하세요.")
            return
        
        if messagebox.askyesno("전체 마이그레이션", 
                              "모든 data_info 내용을 DB로 마이그레이션하시겠습니까?\n\n"
                              "📄 포함 내용:\n"
                              "- 도움말 텍스트\n"
                              "- 플레이스홀더 텍스트\n"
                              "- 지표 라이브러리\n"
                              "- 워크플로우 가이드\n\n"
                              "⚠️ 기존 데이터는 덮어쓰여집니다."):
            
            def full_migration_task():
                self.start_progress("전체 마이그레이션 실행 중...")
                self.full_migration_btn.config(state='disabled')
                
                try:
                    results = self.migrator.run_full_migration()
                    
                    # 로그 표시
                    for log_entry in results['log']:
                        self.log_message(log_entry)
                    
                    # 결과 메시지
                    if results['success']:
                        self.log_message("🎉 전체 마이그레이션 성공적으로 완료!")
                        messagebox.showinfo("성공", "전체 마이그레이션이 성공적으로 완료되었습니다!")
                    else:
                        self.log_message(f"❌ 마이그레이션 완료 (오류 {results['error_count']}개)", "ERROR")
                        messagebox.showwarning("부분 성공", 
                                             f"마이그레이션이 완료되었지만 {results['error_count']}개의 오류가 발생했습니다.\n"
                                             "로그를 확인하세요.")
                    
                finally:
                    self.stop_progress()
                    self.full_migration_btn.config(state='normal')
            
            threading.Thread(target=full_migration_task, daemon=True).start()
    
    def show_migration_summary(self):
        """마이그레이션 결과 요약 표시"""
        if not self.migrator:
            messagebox.showerror("오류", "DB를 먼저 선택하세요.")
            return
        
        summary = self.migrator.get_migration_summary()
        if not summary:
            messagebox.showinfo("요약", "요약 정보를 가져올 수 없습니다.")
            return
        
        summary_text = "📊 마이그레이션 결과 요약\n"
        summary_text += "=" * 40 + "\n\n"
        
        table_names = {
            'tv_help_texts': '📝 도움말 텍스트',
            'tv_placeholder_texts': '🎯 플레이스홀더 텍스트',
            'tv_indicator_library': '📚 지표 라이브러리',
            'tv_workflow_guides': '📋 워크플로우 가이드'
        }
        
        for table, count in summary.items():
            display_name = table_names.get(table, table)
            summary_text += f"{display_name}: {count}개\n"
        
        summary_text += f"\n📅 조회 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        messagebox.showinfo("마이그레이션 요약", summary_text)
    
    def start_progress(self, message):
        """진행률 표시 시작"""
        self.progress_var.set(message)
        self.progress_bar.start(10)
    
    def stop_progress(self):
        """진행률 표시 중지"""
        self.progress_var.set("대기 중...")
        self.progress_bar.stop()
    
    def log_message(self, message, level="INFO"):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 레벨별 색상 및 아이콘
        if level == "ERROR":
            icon = "❌"
            color = "red"
        elif level == "WARNING":
            icon = "⚠️"
            color = "orange"
        elif "성공" in message or "완료" in message:
            icon = "✅"
            color = "green"
        else:
            icon = "ℹ️"
            color = "black"
        
        log_entry = f"[{timestamp}] {icon} {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """로그 지우기"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("로그가 지워졌습니다.")
    
    def save_log(self):
        """로그 저장"""
        from tkinter import filedialog
        
        log_content = self.log_text.get(1.0, tk.END)
        if not log_content.strip():
            messagebox.showinfo("알림", "저장할 로그가 없습니다.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("로그 파일", "*.log"), ("텍스트 파일", "*.txt"), ("모든 파일", "*.*")],
            initialname=f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                self.log_message(f"로그 저장 완료: {Path(filename).name}")
                messagebox.showinfo("성공", f"로그가 저장되었습니다:\n{filename}")
            except Exception as e:
                self.log_message(f"로그 저장 실패: {str(e)}", "ERROR")
                messagebox.showerror("오류", f"로그 저장 중 오류 발생:\n{str(e)}")
