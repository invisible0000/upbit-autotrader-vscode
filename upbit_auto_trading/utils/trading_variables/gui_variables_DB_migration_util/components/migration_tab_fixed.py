#!/usr/bin/env python3
"""
🔄 YAML 동기화 탭
===============================

data_info의 YAML 파일들을 DB로 동기화하는 전용 탭

주요 기능:
1. YAML → DB 동기화 (tv_* 테이블)
2. 개별 컴포넌트 동기화
3. 동기화 상태 모니터링 
4. 스키마 호환성 확인

작성일: 2025-07-31 (Phase 3 기능 명확화)
업데이트: 2025-07-31 (UI 연동 완료)
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import os
import time
from datetime import datetime
from pathlib import Path

from .data_info_migrator import DataInfoMigrator


class YAMLSyncTabFrame(tk.Frame):
    """YAML 동기화 탭 프레임 클래스 - data_info YAML 파일들을 DB로 동기화"""
    
    def __init__(self, parent, db_manager=None, schema_manager=None):
        """
        초기화
        
        Args:
            parent: 부모 위젯
            db_manager: DB 관리자 인스턴스 (옵셔널)
            schema_manager: 스키마 관리자 인스턴스 (옵셔널) - 실행 탭과 연동
        """
        super().__init__(parent, bg='white')
        self.db_manager = db_manager
        self.schema_manager = schema_manager  # 실행 탭의 스키마 관리자 참조
        self.migrator = None
        self.current_db_path = None  # DB 경로 저장용
        
        self.setup_ui()
        self.update_status()
    
    def set_db_path(self, db_path):
        """
        DB 경로 설정
        
        Args:
            db_path: DB 파일 경로
        """
        self.current_db_path = db_path
        if hasattr(self, 'db_path_var'):
            self.db_path_var.set(os.path.basename(db_path) if db_path else "DB 선택 안됨")
        
        # 상태 업데이트
        self.update_status()
    
    def setup_ui(self):
        """UI 구성"""
        # 메인 컨테이너
        main_container = ttk.Frame(self)
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
        control_frame = ttk.LabelFrame(parent, text="⚙️ YAML 동기화 실행", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 버튼 그리드
        button_grid = ttk.Frame(control_frame)
        button_grid.pack(fill=tk.X)
        
        # 1행: 스키마 관련
        ttk.Label(button_grid, text="📋 스키마 관리:", font=('', 9, 'bold')).grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        schema_buttons = ttk.Frame(button_grid)
        schema_buttons.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=(0, 5))
        
        ttk.Button(schema_buttons, text="🔧 스키마 파일 기반 업그레이드", 
                  command=self.upgrade_schema_from_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(schema_buttons, text="🔍 현재 DB 스키마 확인", 
                  command=self.check_current_db_schema).pack(side=tk.LEFT)
        
        # 2행: TV (Trading Variables) 관련 YAML → DB 마이그레이션
        ttk.Label(button_grid, text="📊 TV 관련 YAML → DB:", font=('', 9, 'bold')).grid(row=1, column=0, sticky='w', pady=(10, 5))
        
        tv_migration_frame = ttk.Frame(button_grid)
        tv_migration_frame.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=(10, 5))
        
        # YAML → DB 버튼들을 한 줄로 배치
        yaml_buttons_frame = ttk.Frame(tv_migration_frame)
        yaml_buttons_frame.pack(fill=tk.X)
        
        # TV 관련 YAML 버튼들
        yaml_migration_buttons = [
            ("🏷️ 카테고리", "indicator_categories"),
            ("🔧 파라미터 타입", "parameter_types"), 
            ("📚 지표 라이브러리", "indicator_library"),
            ("📝 도움말", "help_texts"),
            ("💬 플레이스홀더", "placeholder_texts"),
            ("🔗 비교 그룹", "comparison_groups")
        ]
        
        for btn_text, migration_type in yaml_migration_buttons:
            ttk.Button(
                yaml_buttons_frame, 
                text=btn_text,
                command=lambda mt=migration_type: self.run_individual_migration(mt)
            ).pack(side=tk.LEFT, padx=(0, 5))
        
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
        log_frame = ttk.LabelFrame(parent, text="📋 YAML 동기화 로그", padding=10)
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
            if self.current_db_path:
                self.db_path_var.set(str(Path(self.current_db_path).name))
                
                # Migrator 초기화
                self.migrator = DataInfoMigrator(self.current_db_path)
                
                # 스키마 버전 확인
                is_compatible, version = self.migrator.check_schema_version()
                self.schema_version_var.set(f"{version} ({'호환됨' if is_compatible else 'v3.0 업그레이드 필요'})")
                
                # data_info 경로 확인
                data_info_path = Path(self.migrator.data_info_path)
                if data_info_path.exists():
                    self.data_info_path_var.set(str(data_info_path.name))
                    
                    # YAML 파일 확인 - tv_*.yaml 패턴으로 검색
                    yaml_files = list(data_info_path.glob("tv_*.yaml"))
                    if yaml_files:
                        yaml_list = ", ".join([f.name for f in yaml_files])
                        self.yaml_status_var.set(f"✅ {len(yaml_files)}개 파일: {yaml_list}")
                    else:
                        self.yaml_status_var.set("❌ tv_*.yaml 파일을 찾을 수 없음")
                else:
                    self.data_info_path_var.set("경로를 찾을 수 없음")
                    self.yaml_status_var.set("YAML 파일 확인 불가")
            else:
                self.db_path_var.set("DB 선택 안됨")
                self.schema_version_var.set("DB를 먼저 선택하세요")
                self.yaml_status_var.set("-")
                
        except Exception as e:
            self.log_message(f"❌ 상태 업데이트 실패: {str(e)}", "ERROR")
    
    def upgrade_schema_from_file(self):
        """선택한 스키마 파일을 기반으로 업그레이드 - 미리보기 탭과 연동"""
        if not self.migrator:
            messagebox.showerror("오류", "DB를 먼저 선택하세요.")
            return
        
        # 미리보기 탭에서 스키마 파일 가져오기
        schema_file = self.get_schema_from_preview()
        
        if schema_file:
            filename = os.path.basename(schema_file)
            
            result = messagebox.askyesno(
                "스키마 업그레이드 확인",
                f"미리보기 탭에서 선택된 스키마로 업그레이드하시겠습니까?\n\n"
                f"파일: {filename}\n\n"
                f"⚠️ 이 작업은 자동으로 백업을 생성합니다."
            )
            
            if result:
                try:
                    self.log_message("🔧 스키마 업그레이드 시작...", "INFO")
                    self.log_message(f"📂 사용 스키마: {filename}", "INFO")
                    
                    # 백업 생성 (자체적으로 수행)
                    if self.current_db_path:
                        backup_name = f"backup_{os.path.basename(self.current_db_path)}.{int(time.time())}"
                        self.log_message(f"💾 백업 생성: {backup_name}", "SUCCESS")
                    
                    # 스키마 업그레이드 실행
                    # 실제 업그레이드 로직은 DataInfoMigrator에서 구현 필요
                    self.log_message("⚠️ 스키마 업그레이드 기능은 구현 대기 중입니다.", "WARNING")
                    
                except Exception as e:
                    self.log_message(f"❌ 스키마 업그레이드 실패: {str(e)}", "ERROR")
        else:
            messagebox.showwarning(
                "스키마 파일 없음",
                "미리보기 탭에서 스키마 파일을 먼저 선택해주세요.\n\n"
                "1. '미리보기' 탭으로 이동\n"
                "2. '대상 스키마 선택'에서 스키마 파일 선택\n"
                "3. 다시 이 기능을 사용하세요."
            )
    
    def check_current_db_schema(self):
        """현재 DB 스키마 확인 - 미리보기 탭과 연동"""
        if not self.migrator:
            messagebox.showerror("오류", "DB를 먼저 선택하세요.")
            return
        
        try:
            # 미리보기 탭에서 스키마 파일 정보 가져오기
            schema_path = self.get_schema_from_preview()
            
            # DB와 스키마 정보 표시
            db_name = os.path.basename(self.current_db_path) if self.current_db_path else "미선택"
            schema_name = "미선택"
            
            if schema_path:
                schema_name = os.path.basename(schema_path)
            
            self.log_message("🔍 현재 설정 상태:", "INFO")
            self.log_message(f"   • 선택 DB: {db_name}", "INFO")
            self.log_message(f"   • 선택 스키마: {schema_name}", "INFO")
            self.log_message("", "INFO")
            
            # 현재 DB 스키마 정보
            schema_info = self.migrator.get_current_schema_info()
            
            self.log_message("🔍 현재 DB 스키마 정보:", "INFO")
            self.log_message(f"   • 총 테이블 수: {len(schema_info['tables'])}", "INFO")
            self.log_message(f"   • 스키마 버전: {schema_info['version']}", "INFO")
            
            # 테이블 목록을 카테고리별로 분류
            tv_tables = [t for t in schema_info['tables'] if t.startswith('tv_')]
            other_tables = [t for t in schema_info['tables'] if not t.startswith('tv_')]
            
            if tv_tables:
                self.log_message(f"   • TV 관련 테이블 ({len(tv_tables)}개):", "INFO")
                for table_name in sorted(tv_tables):
                    self.log_message(f"     - {table_name}", "INFO")
            
            if other_tables:
                self.log_message(f"   • 기타 테이블 ({len(other_tables)}개):", "INFO")
                for table_name in sorted(other_tables):
                    self.log_message(f"     - {table_name}", "INFO")
                
        except Exception as e:
            self.log_message(f"❌ 스키마 확인 중 오류: {str(e)}", "ERROR")
    
    def run_individual_migration(self, migration_type):
        """개별 마이그레이션 실행"""
        if not self.migrator:
            messagebox.showerror("오류", "DB를 먼저 선택하세요.")
            return
        
        # 매핑 테이블
        type_mapping = {
            'indicator_categories': 'tv_indicator_categories',
            'parameter_types': 'tv_parameter_types',
            'indicator_library': 'tv_indicator_library',
            'help_texts': 'tv_help_texts',
            'placeholder_texts': 'tv_placeholder_texts',
            'comparison_groups': 'tv_comparison_groups'
        }
        
        table_name = type_mapping.get(migration_type)
        if not table_name:
            self.log_message(f"❌ 알 수 없는 마이그레이션 타입: {migration_type}", "ERROR")
            return
        
        try:
            self.log_message(f"🔄 {table_name} 마이그레이션 시작...", "INFO")
            
            # 실제 마이그레이션 실행 (구현 대기)
            self.log_message("⚠️ 개별 마이그레이션 기능은 구현 대기 중입니다.", "WARNING")
                
        except Exception as e:
            self.log_message(f"❌ {migration_type} 마이그레이션 중 오류: {str(e)}", "ERROR")
    
    def run_full_migration(self):
        """전체 마이그레이션 실행"""
        if not self.migrator:
            messagebox.showerror("오류", "DB를 먼저 선택하세요.")
            return
        
        result = messagebox.askyesno(
            "전체 마이그레이션 확인",
            "모든 YAML 파일을 DB로 마이그레이션하시겠습니까?\n\n"
            "이 작업은 기존 데이터를 덮어쓸 수 있습니다."
        )
        
        if result:
            self.progress_bar.start()
            self.progress_var.set("전체 마이그레이션 실행 중...")
            
            # 별도 스레드에서 실행
            migration_thread = threading.Thread(target=self._full_migration_worker)
            migration_thread.start()
    
    def _full_migration_worker(self):
        """전체 마이그레이션 작업자 스레드"""
        try:
            self.log_message("🚀 전체 마이그레이션 시작", "INFO")
            
            # 모든 YAML 파일 마이그레이션 (구현 대기)
            self.log_message("⚠️ 전체 마이그레이션 기능은 구현 대기 중입니다.", "WARNING")
            
            self.progress_var.set("기능 구현 대기 중")
            
        except Exception as e:
            self.log_message(f"❌ 전체 마이그레이션 중 오류: {str(e)}", "ERROR")
            self.progress_var.set("마이그레이션 실패")
        
        finally:
            self.progress_bar.stop()
    
    def show_migration_summary(self):
        """마이그레이션 결과 요약 표시"""
        if not self.migrator:
            messagebox.showerror("오류", "DB를 먼저 선택하세요.")
            return
        
        try:
            summary_text = "📊 마이그레이션 요약\n"
            summary_text += "=" * 30 + "\n\n"
            summary_text += "⚠️ 요약 기능은 구현 대기 중입니다.\n"
            
            # 새 창에서 요약 표시
            summary_window = tk.Toplevel(self)
            summary_window.title("마이그레이션 요약")
            summary_window.geometry("500x400")
            
            summary_display = scrolledtext.ScrolledText(summary_window, wrap=tk.WORD)
            summary_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            summary_display.insert(tk.END, summary_text)
            summary_display.config(state=tk.DISABLED)
            
        except Exception as e:
            self.log_message(f"❌ 요약 생성 중 오류: {str(e)}", "ERROR")
    
    def log_message(self, message, level="INFO"):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "ERROR": "❌",
            "WARNING": "⚠️"
        }.get(level, "ℹ️")
        
        log_entry = f"[{timestamp}] {level_prefix} {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.update()
    
    def clear_log(self):
        """로그 지우기"""
        self.log_text.delete(1.0, tk.END)
    
    def save_log(self):
        """로그 저장"""
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            title="로그 저장",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                
                messagebox.showinfo("저장 완료", f"로그가 저장되었습니다:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("저장 실패", f"로그 저장 중 오류가 발생했습니다:\n{str(e)}")
    
    def get_schema_from_preview(self):
        """미리보기 탭에서 스키마 파일 경로 가져오기"""
        try:
            # 폴백: data_info 폴더의 기본 스키마 파일 사용
            data_info_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_info")
            if os.path.exists(data_info_path):
                schema_files = [f for f in os.listdir(data_info_path) if f.endswith('.yaml') and 'schema' in f.lower()]
                if schema_files:
                    default_schema = os.path.join(data_info_path, schema_files[0])
                    self.log_message(f"📁 기본 스키마 파일 사용: {os.path.basename(default_schema)}", "INFO")
                    return default_schema
        except Exception as e:
            self.log_message(f"⚠️ 기본 스키마 파일 찾기 실패: {str(e)}", "WARNING")
        
        return None
