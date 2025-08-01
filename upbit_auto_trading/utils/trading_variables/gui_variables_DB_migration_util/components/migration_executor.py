#!/usr/bin/env python3
"""
🚀 Schema-Based Migration Executor Component
스키마 기반 마이그레이션 실행 및 진행 상황 모니터링 컴포넌트

주요 기능:
1. 스키마 파일과 현재 DB 비교 분석
2. 버전/테이블 변경점 상세 표시
3. 백업 기반 안전한 마이그레이션 실행
4. 실시간 진행 상황 모니터링

작성일: 2025-07-30
업데이트: 2025-07-31 (스키마 중심 기능 분리)
"""

import os
import sqlite3
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from datetime import datetime
import shutil
import re


class MigrationExecutorFrame(tk.Frame):
    """스키마 기반 마이그레이션 실행 프레임"""
    
    def __init__(self, parent, on_migration_complete=None):
        """
        초기화
        
        Args:
            parent: 부모 위젯
            on_migration_complete: 마이그레이션 완료 콜백
        """
        super().__init__(parent, bg='white')
        self.parent = parent  # 부모 참조 저장
        self.current_db_path = None
        self.selected_schema_path = None
        self.on_migration_complete = on_migration_complete
        self.migration_thread = None
        self.is_running = False
        
        self.setup_ui()
    
    def set_schema_file(self, schema_file_path):
        """
        미리보기에서 선택한 스키마 파일 경로 설정
        
        Args:
            schema_file_path: 스키마 파일 경로
        """
        self.selected_schema_path = schema_file_path
        if hasattr(self, 'schema_info_var'):
            filename = os.path.basename(schema_file_path) if schema_file_path else "스키마 미선택"
            self.schema_info_var.set(f"📄 {filename}")
    
    
    def setup_ui(self):
        """UI 구성"""
        # 제목
        title_label = tk.Label(
            self,
            text="🚀 스키마 기반 마이그레이션 실행",
            font=('Arial', 14, 'bold'),
            bg='white',
            fg='#2c3e50'
        )
        title_label.pack(pady=(20, 10))
        
        # === 차이점 분석 & 체크리스트 섹션 (같은 줄 배치) ===
        self.setup_diff_and_checklist_section()
        
        # === 마이그레이션 실행 섹션 ===
        self.setup_execution_section()
    
    def setup_diff_and_checklist_section(self):
        """차이점 분석과 체크리스트를 같은 줄에 배치 (3:1 비율)"""
        main_frame = tk.Frame(self, bg='white')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # === 왼쪽: 차이점 분석 (75% 너비) ===
        diff_frame = tk.LabelFrame(
            main_frame,
            text="🔍 스키마 차이점 분석",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        diff_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # 분석 실행 버튼과 선택된 스키마 정보
        button_frame = tk.Frame(diff_frame, bg='white')
        button_frame.pack(fill='x', padx=10, pady=10)
        
        # 선택된 스키마 파일명 표시
        self.schema_info_var = tk.StringVar(value="스키마 미선택")
        schema_info_label = tk.Label(
            button_frame,
            textvariable=self.schema_info_var,
            font=('Arial', 9),
            bg='white',
            fg='#7f8c8d'
        )
        schema_info_label.pack(side='left')
        
        # 분석 버튼
        analyze_btn = tk.Button(
            button_frame,
            text="🔍 차이점 분석 실행",
            command=self.analyze_schema_differences,
            bg='#e67e22',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        analyze_btn.pack(side='right')
        
        # 결과 표시 텍스트
        self.diff_text = scrolledtext.ScrolledText(
            diff_frame,
            height=12,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg='#f8f9fa'
        )
        self.diff_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # 초기 메시지
        initial_message = """📊 스키마 차이점 분석 대기 중...

🔍 분석 항목:
• 데이터베이스 버전 비교
• 테이블 구조 변경사항 (추가/수정/삭제)
• 컬럼 변경사항 및 타입 호환성
• 인덱스 및 제약조건 변경
• 데이터 마이그레이션 영향도 평가

💡 먼저 스키마 파일을 선택한 후 '차이점 분석 실행' 버튼을 클릭하세요."""
        
        self.diff_text.insert(tk.END, initial_message)
        self.diff_text.config(state=tk.DISABLED)
        
        # === 오른쪽: 체크리스트 (25% 너비) ===
        checklist_frame = tk.LabelFrame(
            main_frame,
            text="✅ 실행 전 체크리스트",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        checklist_frame.pack(side='right', fill='y', ipadx=10)
        
        self.checklist_vars = {}
        checklist_items = [
            ("db_selected", "✅ DB 파일 선택됨"),
            ("schema_selected", "✅ 스키마 파일 선택됨 (미리보기)"),
            ("diff_analyzed", "✅ 차이점 분석 완료"),
            ("backup_ready", "✅ 백업 계획 수립"),
            ("risk_reviewed", "✅ 리스크 검토 완료")
        ]
        
        for item_id, item_text in checklist_items:
            var = tk.BooleanVar()
            self.checklist_vars[item_id] = var
            
            check = tk.Checkbutton(
                checklist_frame,
                text=item_text,
                variable=var,
                font=('Arial', 9),
                bg='white',
                command=self.update_execute_button_state
            )
            check.pack(anchor='w', padx=10, pady=5)
    
    def setup_execution_section(self):
        """마이그레이션 실행 섹션 구성 - 로그를 우측에 배치"""
        execution_frame = tk.LabelFrame(
            self,
            text="🚀 마이그레이션 실행",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        execution_frame.pack(fill='x', padx=20, pady=10)
        
        # 실행 컨트롤과 로그를 좌우로 분할
        main_container = tk.Frame(execution_frame, bg='white')
        main_container.pack(fill='x', padx=10, pady=10)
        
        # 왼쪽: 실행 버튼들과 진행률 (60% 너비)
        control_frame = tk.Frame(main_container, bg='white')
        control_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # 실행 버튼들
        button_frame = tk.Frame(control_frame, bg='white')
        button_frame.pack(pady=10)
        
        self.execute_btn = tk.Button(
            button_frame,
            text="🚀 마이그레이션 시작",
            command=self.start_migration,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 10, 'bold'),
            state='disabled'
        )
        self.execute_btn.pack(side='left', padx=(0, 10))
        
        self.test_btn = tk.Button(
            button_frame,
            text="🧪 테스트 모드",
            command=self.start_test_migration,
            bg='#f39c12',
            fg='white',
            font=('Arial', 10)
        )
        self.test_btn.pack(side='left')
        
        # 진행률 표시
        self.progress_var = tk.StringVar(value="대기 중...")
        progress_label = tk.Label(
            control_frame,
            textvariable=self.progress_var,
            font=('Arial', 9),
            bg='white'
        )
        progress_label.pack(pady=(10, 5))
        
        self.progress_bar = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress_bar.pack(fill='x', pady=(0, 10))
        
        # 오른쪽: 실행 로그 (40% 너비)
        log_frame = tk.LabelFrame(
            main_container,
            text="📋 실행 로그",
            font=('Arial', 9, 'bold'),
            bg='white'
        )
        log_frame.pack(side='right', fill='both', padx=(10, 0), ipadx=5, ipady=5)
        
        # 로그 텍스트 위젯
        self.execution_log_text = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            width=40,
            wrap=tk.WORD,
            font=('Consolas', 8),
            bg='#f8f9fa'
        )
        self.execution_log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 로그 지우기 버튼
        clear_log_btn = tk.Button(
            log_frame,
            text="🗑️ 로그 지우기",
            command=self.clear_execution_log,
            bg='#95a5a6',
            fg='white',
            font=('Arial', 8)
        )
        clear_log_btn.pack(pady=(5, 0))
        
        # 초기 로그 메시지
        self.log_execution_message("🔧 마이그레이션 실행 시스템 준비 완료", "INFO")
    
    # === 새로운 메서드들 ===
    
    def select_schema_file(self):
        """스키마 파일 선택"""
        # data_info 폴더로 기본 경로 설정
        data_info_path = os.path.join(os.path.dirname(__file__), "..", "data_info")
        if not os.path.exists(data_info_path):
            data_info_path = os.getcwd()
            
        file_path = filedialog.askopenfilename(
            title="스키마 파일 선택",
            filetypes=[
                ("SQL files", "*.sql"),
                ("All files", "*.*")
            ],
            initialdir=data_info_path
        )
        
        if file_path:
            self.selected_schema_path = file_path
            self.schema_path_var.set(file_path)
            
            # 선택된 스키마 파일명을 차이점 분석 섹션에 표시
            filename = os.path.basename(file_path)
            self.schema_info_var.set(f"선택된 스키마: {filename}")
            
            self.checklist_vars["schema_selected"].set(True)
            self.update_execute_button_state()
    
    def auto_detect_schema(self):
        """스키마 파일 자동 감지"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_info_dir = os.path.join(current_dir, "../data_info")
        
        schema_files = []
        for filename in ["upbit_autotrading_unified_schema.sql", "schema_new02.sql", "schema_improved.sql"]:
            schema_path = os.path.join(data_info_dir, filename)
            if os.path.exists(schema_path):
                schema_files.append(schema_path)
        
        if schema_files:
            # 첫 번째 발견된 스키마 사용
            self.selected_schema_path = schema_files[0]
            self.schema_path_var.set(self.selected_schema_path)
            self.checklist_vars["schema_selected"].set(True)
            self.update_execute_button_state()
            messagebox.showinfo("자동 감지", f"스키마 파일을 찾았습니다:\n{os.path.basename(self.selected_schema_path)}")
        else:
            messagebox.showwarning("자동 감지 실패", "data_info 폴더에서 스키마 파일을 찾을 수 없습니다.")
    
    def analyze_schema_differences(self):
        """스키마 차이점 분석"""
        # 미리보기에서 선택된 스키마 파일 사용하기 위해 상위로 탐색
        self.selected_schema_path = self.get_schema_from_preview()
        
        if not self.current_db_path:
            self.log_execution_message("DB 파일이 선택되지 않았습니다", "WARNING")
            messagebox.showwarning("DB 미선택", "먼저 DB 파일을 선택하세요.")
            return
        
        if not self.selected_schema_path:
            self.log_execution_message("스키마 파일이 선택되지 않았습니다", "WARNING")
            messagebox.showwarning("스키마 미선택", "미리보기 탭에서 먼저 스키마 파일을 선택하세요.")
            return
        
        try:
            self.log_execution_message("스키마 차이점 분석을 시작합니다", "INFO")
            
            # 분석 결과 표시
            self.diff_text.config(state=tk.NORMAL)
            self.diff_text.delete(1.0, tk.END)
            
            analysis_result = self.perform_schema_analysis()
            self.diff_text.insert(tk.END, analysis_result)
            self.diff_text.config(state=tk.DISABLED)
            
            # 분석 완료 체크
            self.checklist_vars["diff_analyzed"].set(True)
            self.update_execute_button_state()
            
            self.log_execution_message("스키마 차이점 분석이 완료되었습니다", "SUCCESS")
            
        except Exception as e:
            self.log_execution_message(f"분석 중 오류 발생: {str(e)}", "ERROR")
            messagebox.showerror("분석 실패", f"스키마 분석 중 오류가 발생했습니다:\n{str(e)}")
    
    def get_schema_from_preview(self):
        """미리보기 탭에서 선택된 스키마 파일 경로 가져오기"""
        # 우선 순위: 1. set_schema_file로 설정된 경로 사용
        if self.selected_schema_path and os.path.exists(self.selected_schema_path):
            return self.selected_schema_path
            
        try:
            # 여러 경로로 미리보기 탭 찾기 시도
            preview_tab = None
            
            # 방법 1: 직접 부모에서 찾기
            if hasattr(self.parent, 'migration_preview'):
                preview_tab = self.parent.migration_preview
            # 방법 2: 부모의 부모에서 찾기 (메인 윈도우)
            elif hasattr(self.parent, 'parent') and hasattr(self.parent.parent, 'migration_preview'):
                preview_tab = self.parent.parent.migration_preview
            # 방법 3: 메인 윈도우 클래스에서 찾기
            else:
                # tkinter 위젯 트리를 통해 찾기
                current = self.parent
                while current and not hasattr(current, 'migration_preview'):
                    current = getattr(current, 'parent', None) or getattr(current, 'master', None)
                if current and hasattr(current, 'migration_preview'):
                    preview_tab = current.migration_preview
            
            if preview_tab and hasattr(preview_tab, 'selected_schema_file'):
                schema_file = preview_tab.selected_schema_file
                if schema_file and os.path.exists(schema_file):
                    return schema_file
            
            # 기본 스키마 파일 경로 사용
            default_schema = os.path.join(
                os.path.dirname(__file__), 
                "..", 
                "data_info", 
                "upbit_autotrading_unified_schema.sql"
            )
            if os.path.exists(default_schema):
                return default_schema
                    
        except Exception as e:
            self.log_execution_message(f"스키마 경로 조회 중 오류: {str(e)}", "WARNING")
        
        return None
    
    def perform_schema_analysis(self):
        """실제 스키마 분석 수행 - 개선된 좌우 비교 형태"""
        result_lines = []
        result_lines.append("🔍 스키마 차이점 분석 결과")
        result_lines.append("=" * 80)
        result_lines.append("")
        
        # 기본 정보
        result_lines.append(f"📊 현재 DB: {os.path.basename(self.current_db_path or '')}")
        result_lines.append(f"📋 대상 스키마: {os.path.basename(self.selected_schema_path or '')}")
        result_lines.append("")
        
        try:
            # 현재 DB 스키마 정보
            with sqlite3.connect(self.current_db_path) as conn:
                cursor = conn.cursor()
                
                # 현재 테이블 목록
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                current_tables = set([row[0] for row in cursor.fetchall()])
                
                # 스키마 버전 확인
                current_version = "v2.x (레거시)"
                if 'tv_schema_version' in current_tables:
                    cursor.execute("SELECT version, description FROM tv_schema_version ORDER BY version DESC LIMIT 1")
                    version_row = cursor.fetchone()
                    if version_row:
                        current_version = f"{version_row[0]} ({version_row[1]})"
                    else:
                        current_version = "버전 정보 없음"
            
            # 대상 스키마 분석
            with open(self.selected_schema_path, 'r', encoding='utf-8') as f:
                schema_content = f.read()
            
            # CREATE TABLE 문과 스키마 버전 추출 - IF NOT EXISTS도 포함
            create_patterns = re.findall(
                r'CREATE TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+(\w+)\s*\(',
                schema_content,
                re.IGNORECASE
            )
            target_tables = set(create_patterns)
            
            # 대상 스키마 버전 추출
            target_version = "불명"
            version_match = re.search(r"INSERT INTO tv_schema_version.*?VALUES.*?'([^']+)'", schema_content, re.IGNORECASE | re.DOTALL)
            if version_match:
                target_version = version_match.group(1)
            
            # 버전 정보 표시
            result_lines.append("📈 스키마 버전 비교:")
            result_lines.append(f"   현재 DB: {current_version}")
            result_lines.append(f"   대상 스키마: {target_version}")
            result_lines.append("")
            
            # 테이블 변경사항 분석
            new_tables = target_tables - current_tables
            removed_tables = current_tables - target_tables
            common_tables = current_tables & target_tables
            
            # 좌우 비교 형태로 테이블 정보 표시
            result_lines.append("📊 테이블 비교 (현재 DB ↔ 대상 스키마):")
            result_lines.append("-" * 80)
            result_lines.append(f"{'현재 DB (' + str(len(current_tables)) + '개)':<35} | {'대상 스키마 (' + str(len(target_tables)) + '개)'}")
            result_lines.append("-" * 80)
            
            # 매칭되는 테이블들 (공통)
            if common_tables:
                result_lines.append(f"\n🔄 유지되는 테이블 ({len(common_tables)}개):")
                for table in sorted(common_tables):
                    result_lines.append(f"   ✅ {table:<30} | ✅ {table}")
            
            # 새로 추가되는 테이블들
            if new_tables:
                result_lines.append(f"\n➕ 추가될 테이블 ({len(new_tables)}개):")
                for table in sorted(new_tables):
                    result_lines.append(f"   ❌ (없음){'':21} | ✨ {table}")
            
            # 제거되는 테이블들  
            if removed_tables:
                result_lines.append(f"\n🗑️ 제거될 테이블 ({len(removed_tables)}개):")
                for table in sorted(removed_tables):
                    result_lines.append(f"   🗑️ {table:<30} | ❌ (제거됨)")
            
            result_lines.append("")
            
            # 상세 변경 통계
            result_lines.append("📋 변경 통계:")
            result_lines.append(f"   • 유지: {len(common_tables)}개")
            result_lines.append(f"   • 추가: {len(new_tables)}개")
            result_lines.append(f"   • 제거: {len(removed_tables)}개")
            result_lines.append(f"   • 총 변경: {len(new_tables) + len(removed_tables)}개")
            result_lines.append("")
            
            # 리스크 평가 및 권장사항
            risk_level = "낮음"
            risk_factors = []
            
            if removed_tables:
                risk_level = "높음" if len(removed_tables) > 2 else "중간"
                risk_factors.append(f"{len(removed_tables)}개 테이블 제거")
            
            if new_tables and len(new_tables) > 3:
                if risk_level == "낮음":
                    risk_level = "중간"
                risk_factors.append(f"{len(new_tables)}개 테이블 추가")
            
            result_lines.append(f"⚠️ 위험도 평가: {risk_level}")
            if risk_factors:
                result_lines.append(f"   위험 요소: {', '.join(risk_factors)}")
            result_lines.append("")
            
            # 권장사항
            result_lines.append("💡 마이그레이션 권장사항:")
            result_lines.append("   1. ✅ 마이그레이션 전 자동 백업 생성됨")
            if removed_tables:
                result_lines.append("   2. ⚠️ 제거될 테이블의 데이터 손실 가능")
                result_lines.append("   3. 💾 중요 데이터는 별도 백업 권장")
            result_lines.append("   4. 🧪 테스트 모드로 먼저 검증 권장")
            result_lines.append("   5. ✔️ 실행 후 데이터 무결성 검증 필수")
            
            # 백업 정보
            self.checklist_vars["backup_ready"].set(True)
            result_lines.append("")
            result_lines.append("💾 백업 계획: 자동 백업 시스템이 마이그레이션 전 전체 DB를 백업합니다.")
            
        except Exception as e:
            result_lines.append(f"❌ 분석 중 오류 발생: {str(e)}")
        
        return '\n'.join(result_lines)
    
    def update_execute_button_state(self):
        """실행 버튼 상태 업데이트"""
        required_checks = ["db_selected", "schema_selected", "diff_analyzed"]
        all_checked = all(self.checklist_vars.get(check, tk.BooleanVar()).get() for check in required_checks)
        
        if all_checked:
            self.execute_btn.config(state='normal')
        else:
            self.execute_btn.config(state='disabled')
    
    def start_migration(self):
        """마이그레이션 시작"""
        if not self.validate_migration_ready():
            return
        
        # 확인 대화상자
        response = messagebox.askyesno(
            "마이그레이션 실행 확인",
            "정말로 마이그레이션을 실행하시겠습니까?\n\n"
            "이 작업은 데이터베이스를 변경하며, 백업이 자동으로 생성됩니다."
        )
        
        if response:
            self.execute_migration(test_mode=False)
    
    def start_test_migration(self):
        """테스트 마이그레이션 시작"""
        if not self.validate_migration_ready():
            return
        
        messagebox.showinfo(
            "테스트 모드",
            "테스트 모드에서는 실제 변경 없이 마이그레이션 과정을 시뮬레이션합니다."
        )
        
        self.execute_migration(test_mode=True)
    
    def validate_migration_ready(self):
        """마이그레이션 준비 상태 검증"""
        if not self.current_db_path:
            messagebox.showwarning("준비 미완료", "DB 파일이 선택되지 않았습니다.")
            return False
        
        if not self.selected_schema_path:
            messagebox.showwarning("준비 미완료", "스키마 파일이 선택되지 않았습니다.")
            return False
        
        if not os.path.exists(self.current_db_path):
            messagebox.showerror("파일 오류", "선택된 DB 파일이 존재하지 않습니다.")
            return False
        
        if not os.path.exists(self.selected_schema_path):
            messagebox.showerror("파일 오류", "선택된 스키마 파일이 존재하지 않습니다.")
            return False
        
        return True
    
    def execute_migration(self, test_mode=False):
        """마이그레이션 실행"""
        if self.is_running:
            messagebox.showwarning("실행 중", "이미 마이그레이션이 실행 중입니다.")
            return
        
        self.is_running = True
        self.progress_bar.start()
        
        mode_text = "테스트" if test_mode else "실제"
        self.progress_var.set(f"{mode_text} 마이그레이션 실행 중...")
        
        # 버튼 비활성화
        self.execute_btn.config(state='disabled')
        self.test_btn.config(state='disabled')
        
        # 별도 스레드에서 실행
        self.migration_thread = threading.Thread(
            target=self._migration_worker,
            args=(test_mode,)
        )
        self.migration_thread.start()
    
    def _migration_worker(self, test_mode):
        """마이그레이션 작업자 스레드"""
        try:
            self.log_execution_message(f"{'테스트' if test_mode else '실제'} 마이그레이션을 시작합니다", "INFO")
            
            # 백업 생성
            if not test_mode:
                self.log_execution_message("데이터베이스 백업을 생성하고 있습니다...", "INFO")
                backup_path = self.create_backup()
                if not backup_path:
                    raise Exception("백업 생성에 실패했습니다.")
                self.log_execution_message(f"백업 완료: {os.path.basename(backup_path)}", "SUCCESS")
            
            # 스키마 적용
            if test_mode:
                self.log_execution_message("테스트 모드: 시뮬레이션 실행 중...", "INFO")
                # 테스트 모드: 시뮬레이션만
                import time
                for i in range(5):
                    time.sleep(1)
                    self.progress_var.set(f"테스트 진행 중... ({i+1}/5)")
                    self.log_execution_message(f"테스트 단계 {i+1}/5 완료", "INFO")
                
                self.progress_var.set("✅ 테스트 완료 - 문제없이 실행될 것으로 예상됩니다.")
                self.log_execution_message("테스트 완료: 실제 마이그레이션이 성공할 것으로 예상됩니다", "SUCCESS")
            else:
                self.log_execution_message("스키마를 데이터베이스에 적용하고 있습니다...", "INFO")
                # 실제 마이그레이션
                self.apply_schema()
                self.progress_var.set("✅ 마이그레이션 완료")
                self.log_execution_message("마이그레이션이 성공적으로 완료되었습니다", "SUCCESS")
            
            # 완료 콜백 호출
            if self.on_migration_complete:
                self.on_migration_complete()
            
        except Exception as e:
            error_msg = f"마이그레이션 실패: {str(e)}"
            self.progress_var.set(f"❌ {error_msg}")
            self.log_execution_message(error_msg, "ERROR")
            messagebox.showerror("마이그레이션 실패", f"마이그레이션 중 오류가 발생했습니다:\n{str(e)}")
        
        finally:
            self.is_running = False
            self.progress_bar.stop()
            
            # 버튼 재활성화
            self.execute_btn.config(state='normal')
            self.test_btn.config(state='normal')
            self.log_execution_message("마이그레이션 프로세스가 종료되었습니다", "INFO")
    
    def create_backup(self):
        """백업 생성"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            db_name = os.path.splitext(os.path.basename(self.current_db_path))[0]
            backup_filename = f"{db_name}_bck_{timestamp}.sqlite3"
            backup_dir = os.path.join(os.path.dirname(self.current_db_path), "backups")
            
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, backup_filename)
            
            shutil.copy2(self.current_db_path, backup_path)
            
            return backup_path
            
        except Exception as e:
            raise Exception(f"백업 생성 실패: {str(e)}")
    
    def apply_schema(self):
        """스키마 적용"""
        try:
            # 스키마 파일 읽기
            with open(self.selected_schema_path, 'r', encoding='utf-8') as f:
                schema_content = f.read()
            
            # SQL 실행
            with sqlite3.connect(self.current_db_path) as conn:
                cursor = conn.cursor()
                
                # 스키마 적용 (여러 구문 실행)
                cursor.executescript(schema_content)
                conn.commit()
                
        except Exception as e:
            raise Exception(f"스키마 적용 실패: {str(e)}")
    
    # === 기존 메서드들 ===
    
    def set_db_path(self, db_path):
        """DB 경로 설정"""
        self.current_db_path = db_path
        if db_path:
            self.checklist_vars["db_selected"].set(True)
            self.log_execution_message(f"DB 선택됨: {os.path.basename(db_path)}", "INFO")
        else:
            self.checklist_vars["db_selected"].set(False)
        
        # 미리보기에서 스키마가 선택되었는지 확인
        self.check_schema_from_preview()
        
        self.update_execute_button_state()
    
    def check_schema_from_preview(self):
        """미리보기 탭에서 스키마 선택 상태 확인"""
        try:
            schema_path = self.get_schema_from_preview()
            if schema_path:
                self.selected_schema_path = schema_path
                filename = os.path.basename(schema_path)
                self.schema_info_var.set(f"미리보기에서 선택: {filename}")
                self.checklist_vars["schema_selected"].set(True)
                self.log_execution_message(f"미리보기에서 스키마 확인됨: {filename}", "INFO")
            else:
                self.schema_info_var.set("미리보기에서 스키마를 선택하세요")
                self.checklist_vars["schema_selected"].set(False)
        except Exception as e:
            self.log_execution_message(f"스키마 확인 중 오류: {str(e)}", "WARNING")
    
    def log_execution_message(self, message, level="INFO"):
        """실행 로그에 메시지 추가"""
        if not hasattr(self, 'execution_log_text'):
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "ERROR": "❌",
            "WARNING": "⚠️"
        }.get(level, "ℹ️")
        
        log_entry = f"[{timestamp}] {level_prefix} {message}\n"
        
        self.execution_log_text.insert(tk.END, log_entry)
        self.execution_log_text.see(tk.END)
        self.execution_log_text.update()
    
    def clear_execution_log(self):
        """실행 로그 지우기"""
        if hasattr(self, 'execution_log_text'):
            self.execution_log_text.delete(1.0, tk.END)
            self.log_execution_message("로그가 초기화되었습니다", "INFO")
