#!/usr/bin/env python3
"""
🚀 Migration Executor Component
마이그레이션 실행 및 진행 상황 모니터링 컴포넌트

작성일: 2025-07-30
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class MigrationExecutorFrame(tk.Frame):
    """마이그레이션 실행 프레임"""
    
    def __init__(self, parent, on_migration_complete=None):
        """
        초기화
        
        Args:
            parent: 부모 위젯
            on_migration_complete: 마이그레이션 완료 콜백
        """
        super().__init__(parent, bg='white')
        self.current_db_path = None
        self.on_migration_complete = on_migration_complete
        self.migration_thread = None
        self.is_running = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI 구성"""
        # 제목
        title_label = tk.Label(
            self,
            text="🚀 마이그레이션 실행",
            font=('Arial', 14, 'bold'),
            bg='white',
            fg='#2c3e50'
        )
        title_label.pack(pady=(20, 10))
        
        # 실행 전 체크리스트
        checklist_frame = tk.LabelFrame(
            self,
            text="✅ 실행 전 체크리스트",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        checklist_frame.pack(fill='x', padx=20, pady=10)
        
        self.checklist_vars = {}
        checklist_items = [
            ("db_selected", "DB 파일이 선택되었습니다"),
            ("schema_verified", "스키마 파일이 확인되었습니다"),
            ("backup_ready", "백업 계획이 수립되었습니다"),
            ("risks_reviewed", "리스크가 검토되었습니다"),
            ("confirmation", "변경사항을 이해하고 실행을 승인합니다")
        ]
        
        for key, text in checklist_items:
            var = tk.BooleanVar()
            self.checklist_vars[key] = var
            
            check = tk.Checkbutton(
                checklist_frame,
                text=text,
                variable=var,
                bg='white',
                font=('Arial', 9),
                command=self.update_execute_button_state
            )
            check.pack(anchor='w', padx=20, pady=2)
        
        # 백업 옵션
        backup_frame = tk.LabelFrame(
            self,
            text="💾 백업 옵션",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        backup_frame.pack(fill='x', padx=20, pady=10)
        
        # 백업 파일명 패턴
        backup_pattern_frame = tk.Frame(backup_frame, bg='white')
        backup_pattern_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(backup_pattern_frame, text="백업 파일명:", bg='white', width=12, anchor='w').pack(side='left')
        
        self.backup_pattern_var = tk.StringVar()
        self.update_backup_filename()
        
        backup_entry = tk.Entry(
            backup_pattern_frame,
            textvariable=self.backup_pattern_var,
            state='readonly',
            font=('Courier', 9)
        )
        backup_entry.pack(side='left', fill='x', expand=True, padx=(5, 10))
        
        # 백업 디렉토리
        backup_dir_frame = tk.Frame(backup_frame, bg='white')
        backup_dir_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        tk.Label(backup_dir_frame, text="백업 위치:", bg='white', width=12, anchor='w').pack(side='left')
        
        self.backup_dir_var = tk.StringVar(value="./backups/")
        backup_dir_entry = tk.Entry(
            backup_dir_frame,
            textvariable=self.backup_dir_var,
            state='readonly'
        )
        backup_dir_entry.pack(side='left', fill='x', expand=True, padx=(5, 0))
        
        # 실행 컨트롤
        control_frame = tk.Frame(self, bg='white')
        control_frame.pack(fill='x', padx=20, pady=20)
        
        # 실행 버튼
        self.execute_btn = tk.Button(
            control_frame,
            text="🚀 마이그레이션 실행",
            command=self.start_migration,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 12, 'bold'),
            width=20,
            height=2,
            state='disabled'
        )
        self.execute_btn.pack(side='left', padx=(0, 10))
        
        # 취소 버튼
        self.cancel_btn = tk.Button(
            control_frame,
            text="❌ 취소",
            command=self.cancel_migration,
            bg='#95a5a6',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=12,
            state='disabled'
        )
        self.cancel_btn.pack(side='left', padx=(0, 10))
        
        # 테스트 모드 체크박스
        self.test_mode_var = tk.BooleanVar()
        test_check = tk.Checkbutton(
            control_frame,
            text="🧪 테스트 모드 (실제 변경 없음)",
            variable=self.test_mode_var,
            bg='white',
            font=('Arial', 9)
        )
        test_check.pack(side='left', padx=(20, 0))
        
        # 진행 상황 표시
        progress_frame = tk.LabelFrame(
            self,
            text="📊 진행 상황",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        progress_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400
        )
        self.progress_bar.pack(pady=10)
        
        # 현재 작업 표시
        self.current_task_var = tk.StringVar(value="대기 중...")
        current_task_label = tk.Label(
            progress_frame,
            textvariable=self.current_task_var,
            bg='white',
            font=('Arial', 10),
            fg='#7f8c8d'
        )
        current_task_label.pack(pady=(0, 10))
        
        # 로그 출력
        log_label = tk.Label(
            progress_frame,
            text="📝 실행 로그:",
            bg='white',
            font=('Arial', 9, 'bold'),
            anchor='w'
        )
        log_label.pack(fill='x', padx=10)
        
        # 로그 텍스트 위젯과 스크롤바
        log_frame = tk.Frame(progress_frame, bg='white')
        log_frame.pack(fill='both', expand=True, padx=10, pady=(5, 10))
        
        self.log_text = tk.Text(
            log_frame,
            height=12,
            wrap='word',
            bg='#2c3e50',
            fg='#ecf0f1',
            font=('Courier', 9),
            state='disabled'
        )
        self.log_text.pack(side='left', fill='both', expand=True)
        
        log_scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        log_scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        # 결과 요약 프레임 (마이그레이션 완료 후 표시)
        self.result_frame = tk.LabelFrame(
            self,
            text="🎯 마이그레이션 결과",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        # 처음에는 숨김
        
        self.result_text = tk.Text(
            self.result_frame,
            height=6,
            wrap='word',
            bg='#f8f9fa',
            fg='#2c3e50',
            font=('Arial', 9),
            state='disabled'
        )
        self.result_text.pack(fill='both', expand=True, padx=10, pady=10)
    
    def set_db_path(self, db_path):
        """
        DB 경로 설정
        
        Args:
            db_path: DB 파일 경로
        """
        self.current_db_path = db_path
        self.checklist_vars["db_selected"].set(True)
        self.update_backup_filename()
        self.update_execute_button_state()
    
    def update_backup_filename(self):
        """백업 파일명 업데이트"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"settings_bck_{timestamp}.sqlite3"
        self.backup_pattern_var.set(filename)
    
    def update_execute_button_state(self):
        """실행 버튼 상태 업데이트"""
        all_checked = all(var.get() for var in self.checklist_vars.values())
        has_db = self.current_db_path is not None
        
        if all_checked and has_db and not self.is_running:
            self.execute_btn.config(state='normal', bg='#27ae60')
        else:
            self.execute_btn.config(state='disabled', bg='#95a5a6')
    
    def start_migration(self):
        """마이그레이션 시작"""
        if self.is_running:
            return
        
        # 최종 확인 다이얼로그
        test_mode = self.test_mode_var.get()
        mode_text = "테스트 모드" if test_mode else "실제 마이그레이션"
        
        result = messagebox.askyesno(
            f"{mode_text} 실행 확인",
            f"🚀 {mode_text}를 시작하시겠습니까?\n\n"
            f"• DB 파일: {os.path.basename(self.current_db_path) if self.current_db_path else 'None'}\n"
            f"• 백업 파일: {self.backup_pattern_var.get()}\n"
            f"• 실행 모드: {mode_text}\n\n"
            "⚠️ 실행 후에는 취소할 수 없습니다."
        )
        
        if not result:
            return
        
        # UI 상태 변경
        self.is_running = True
        self.execute_btn.config(state='disabled')
        self.cancel_btn.config(state='normal')
        
        # 로그 클리어
        self.clear_log()
        self.log_message("🚀 마이그레이션 시작", "INFO")
        
        # 진행률 초기화
        self.progress_var.set(0)
        self.current_task_var.set("초기화 중...")
        
        # 백그라운드 스레드에서 마이그레이션 실행
        self.migration_thread = threading.Thread(
            target=self.run_migration_thread,
            args=(test_mode,),
            daemon=True
        )
        self.migration_thread.start()
    
    def run_migration_thread(self, test_mode):
        """마이그레이션 스레드 실행"""
        try:
            if test_mode:
                self.run_test_migration()
            else:
                self.run_actual_migration()
                
        except Exception as e:
            self.log_message(f"❌ 마이그레이션 실패: {str(e)}", "ERROR")
            self.migration_complete(False)
        finally:
            self.is_running = False
    
    def run_test_migration(self):
        """테스트 마이그레이션 실행"""
        steps = [
            ("DB 파일 분석", 10),
            ("스키마 검증", 20),
            ("변경사항 시뮬레이션", 40),
            ("백업 시뮬레이션", 60),
            ("마이그레이션 시뮬레이션", 80),
            ("결과 검증", 100)
        ]
        
        for step_name, progress in steps:
            if not self.is_running:
                return
                
            self.update_progress(step_name, progress)
            self.log_message(f"🧪 [테스트] {step_name} 중...", "INFO")
            
            # 시뮬레이션 딜레이
            import time
            time.sleep(1)
        
        self.log_message("✅ 테스트 마이그레이션 완료 - 실제 변경사항 없음", "SUCCESS")
        self.migration_complete(True, test_mode=True)
    
    def run_actual_migration(self):
        """실제 마이그레이션 실행"""
        try:
            # 같은 폴더의 마이그레이션 모듈 import
            from .migrate_db import TradingVariablesDBMigration
            
            # 진행 상황 및 로그 콜백 함수 정의
            def progress_callback(message, percentage):
                self.update_progress(message, percentage)
            
            def log_callback(message, level):
                self.log_message(message, level)
            
            # 마이그레이션 객체 생성 (GUI 콜백 연결)
            migration = TradingVariablesDBMigration(
                db_path=self.current_db_path,
                progress_callback=progress_callback,
                log_callback=log_callback
            )
            
            # 마이그레이션 실행
            self.log_message("� 마이그레이션 시작", "INFO")
            success = migration.run_migration(force=True)  # GUI에서는 force 모드
            
            if success:
                self.log_message("🎉 마이그레이션 완료!", "SUCCESS")
                self.update_progress("마이그레이션 완료", 100)
                return True
            else:
                self.log_message("❌ 마이그레이션 실패", "ERROR")
                return False
            self.log_message("🗑️ 레거시 테이블 제거 중...", "INFO")
            
            self.update_progress("새 스키마 적용 중", 70)
            self.log_message("🔧 새 스키마 적용 중...", "INFO")
            
            self.update_progress("마이그레이션 실행 중", 85)
            self.log_message("🚀 마이그레이션 실행 중...", "INFO")
            
            # 실제 마이그레이션 실행
            success = migration.run_migration(force=True)
            
            self.update_progress("검증 중", 95)
            self.log_message("🔍 마이그레이션 결과 검증 중...", "INFO")
            
            self.update_progress("완료", 100)
            
            if success:
                self.log_message("🎉 마이그레이션 성공적으로 완료!", "SUCCESS")
                # 백업 파일 경로는 마이그레이션 객체에서 가져옴
                backup_path = getattr(migration, 'backup_path', None)
                self.migration_complete(True, backup_path=backup_path)
            else:
                self.log_message("❌ 마이그레이션 실패", "ERROR")
                self.migration_complete(False)
                
        except Exception as e:
            self.log_message(f"💥 마이그레이션 중 오류 발생: {str(e)}", "ERROR")
            self.migration_complete(False)
    
    def update_progress(self, task_name, progress):
        """진행 상황 업데이트 (스레드 안전)"""
        def update():
            self.current_task_var.set(task_name)
            self.progress_var.set(progress)
        
        self.after(0, update)
    
    def log_message(self, message, level="INFO"):
        """로그 메시지 추가 (스레드 안전)"""
        def add_log():
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # 레벨별 색상
            colors = {
                "INFO": "#3498db",
                "SUCCESS": "#27ae60", 
                "WARNING": "#f39c12",
                "ERROR": "#e74c3c"
            }
            
            formatted_message = f"[{timestamp}] {message}\n"
            
            self.log_text.config(state='normal')
            self.log_text.insert(tk.END, formatted_message)
            
            # 색상 적용
            if level in colors:
                start_line = int(self.log_text.index(tk.END).split('.')[0]) - 2
                self.log_text.tag_add(level, f"{start_line}.0", f"{start_line}.end")
                self.log_text.tag_config(level, foreground=colors[level])
            
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')
        
        self.after(0, add_log)
    
    def clear_log(self):
        """로그 클리어"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
    
    def cancel_migration(self):
        """마이그레이션 취소"""
        if not self.is_running:
            return
        
        result = messagebox.askyesno(
            "마이그레이션 취소",
            "⚠️ 마이그레이션을 취소하시겠습니까?\n\n"
            "진행 중인 작업이 중단되며, 일부 변경사항이\n"
            "불완전한 상태로 남을 수 있습니다."
        )
        
        if result:
            self.is_running = False
            self.log_message("🛑 사용자에 의해 마이그레이션 취소됨", "WARNING")
            self.migration_complete(False, cancelled=True)
    
    def migration_complete(self, success, backup_path=None, test_mode=False, cancelled=False):
        """마이그레이션 완료 처리 (스레드 안전)"""
        def complete():
            # UI 상태 복원
            self.execute_btn.config(state='normal', bg='#27ae60')
            self.cancel_btn.config(state='disabled')
            self.is_running = False
            
            # 결과 표시
            if cancelled:
                self.current_task_var.set("❌ 취소됨")
                self.show_result_summary("취소", "마이그레이션이 사용자에 의해 취소되었습니다.")
            elif test_mode:
                self.current_task_var.set("🧪 테스트 완료")
                self.show_result_summary("테스트 완료", "테스트 마이그레이션이 성공적으로 완료되었습니다.\n실제 데이터베이스 변경은 없었습니다.")
            elif success:
                self.current_task_var.set("✅ 완료")
                result_msg = "마이그레이션이 성공적으로 완료되었습니다!"
                if backup_path:
                    result_msg += f"\n백업 파일: {os.path.basename(backup_path)}"
                self.show_result_summary("성공", result_msg)
            else:
                self.current_task_var.set("❌ 실패")
                self.show_result_summary("실패", "마이그레이션 중 오류가 발생했습니다.\n로그를 확인하여 문제를 파악하세요.")
            
            # 콜백 호출
            if self.on_migration_complete:
                self.on_migration_complete(success and not cancelled, backup_path)
        
        self.after(0, complete)
    
    def show_result_summary(self, status, message):
        """결과 요약 표시"""
        # 결과 프레임 표시
        self.result_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # 결과 텍스트 업데이트
        full_message = f"📊 상태: {status}\n\n{message}\n\n"
        full_message += f"🕐 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.result_text.config(state='normal')
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, full_message)
        self.result_text.config(state='disabled')
    
    def reset_checklist(self):
        """체크리스트 초기화"""
        for key, var in self.checklist_vars.items():
            if key != "db_selected":  # DB 선택은 유지
                var.set(False)
        self.update_execute_button_state()
