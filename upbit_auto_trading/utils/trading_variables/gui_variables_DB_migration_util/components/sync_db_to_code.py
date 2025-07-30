#!/usr/bin/env python3
"""
DB → variable_definitions.py 동기화 GUI 컴포넌트 (간소화)
======================================================

분해된 모듈들을 활용한 간소화된 GUI 컴포넌트:
- db_data_manager: DB 데이터 관리
- code_generator: 코드 생성  
- data_info_loader: YAML 파일 처리

주요 기능:
- DB 중심 워크플로우 GUI 제공
- 분해된 모듈들의 통합 인터페이스
- 안전한 파일 생성 및 보고서 기능

작성일: 2025-07-30
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from datetime import datetime
from typing import Dict, Any
import threading

# 분해된 모듈들 import
from .db_data_manager import DBDataManager
from .code_generator import VariableDefinitionsGenerator, create_safe_filename
from .data_info_loader import DataInfoLoader
from .enhanced_code_generator import EnhancedVariableDefinitionsGenerator


class SyncDBToCodeFrame(tk.Frame):
    """DB → variable_definitions.py 동기화 프레임 (간소화된 GUI 전용)"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.db_path = None
        self.output_directory = None
        self.last_generated_file = None
        
        # 분해된 모듈들 초기화
        self.db_manager = None
        self.data_info_loader = DataInfoLoader()
        
        self.setup_gui()
        self._load_data_info()
    
    def setup_gui(self):
        """GUI 레이아웃 설정"""
        # 상단 제목
        title_frame = tk.Frame(self, bg='#34495e', height=50)
        title_frame.pack(fill='x', pady=(0, 10))
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="🔄 DB → variable_definitions.py 동기화 (DB 중심)",
            font=('Arial', 14, 'bold'),
            fg='white',
            bg='#34495e'
        )
        title_label.pack(expand=True)
        
        # 메인 컨테이너
        main_frame = tk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 설정 섹션
        self.setup_config_section(main_frame)
        
        # 진행 상황 섹션
        self.setup_progress_section(main_frame)
        
        # 결과 섹션
        self.setup_result_section(main_frame)
    
    def setup_config_section(self, parent):
        """설정 섹션 구성"""
        config_frame = tk.LabelFrame(parent, text="📋 동기화 설정 (DB 중심)", font=('Arial', 10, 'bold'))
        config_frame.pack(fill='x', pady=(0, 10))
        
        # DB 상태 표시
        db_info_frame = tk.Frame(config_frame)
        db_info_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(db_info_frame, text="💾 DB 파일:", font=('Arial', 9, 'bold')).pack(side='left')
        self.db_path_label = tk.Label(
            db_info_frame,
            text="선택되지 않음",
            fg='red',
            font=('Arial', 9)
        )
        self.db_path_label.pack(side='left', padx=(10, 0))
        
        # data_info 상태 표시
        data_info_frame = tk.Frame(config_frame)
        data_info_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(data_info_frame, text="📁 data_info:", font=('Arial', 9, 'bold')).pack(side='left')
        self.data_info_status_label = tk.Label(
            data_info_frame,
            text="로딩 중...",
            fg='orange',
            font=('Arial', 9)
        )
        self.data_info_status_label.pack(side='left', padx=(10, 0))
        
        # 출력 경로 설정
        output_frame = tk.Frame(config_frame)
        output_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(output_frame, text="📂 출력 폴더:", font=('Arial', 9, 'bold')).pack(side='left')
        
        self.output_path_var = tk.StringVar()
        self.output_path_entry = tk.Entry(
            output_frame,
            textvariable=self.output_path_var,
            font=('Arial', 9),
            state='readonly'
        )
        self.output_path_entry.pack(side='left', fill='x', expand=True, padx=(10, 5))
        
        browse_btn = tk.Button(
            output_frame,
            text="찾아보기",
            command=self.browse_output_directory,
            bg='#3498db',
            fg='white',
            font=('Arial', 8)
        )
        browse_btn.pack(side='right')
        
        # 파일명 미리보기
        filename_frame = tk.Frame(config_frame)
        filename_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(filename_frame, text="📝 생성될 파일:", font=('Arial', 9, 'bold')).pack(side='left')
        self.filename_preview_label = tk.Label(
            filename_frame,
            text="variable_definitions_new.py",
            fg='blue',
            font=('Arial', 9)
        )
        self.filename_preview_label.pack(side='left', padx=(10, 0))
        
        # 동기화 버튼
        button_frame = tk.Frame(config_frame)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        self.sync_button = tk.Button(
            button_frame,
            text="🔄 DB 동기화 실행",
            command=self.start_sync,
            bg='#27ae60',
            fg='white',
            font=('Arial', 10, 'bold'),
            state='disabled'
        )
        self.sync_button.pack(side='left')
        
        self.open_file_button = tk.Button(
            button_frame,
            text="📂 파일 열기",
            command=self.open_generated_file,
            bg='#f39c12',
            fg='white',
            font=('Arial', 10),
            state='disabled'
        )
        self.open_file_button.pack(side='left', padx=(10, 0))
        
        self.open_folder_button = tk.Button(
            button_frame,
            text="📁 폴더 열기",
            command=self.open_output_folder,
            bg='#9b59b6',
            fg='white',
            font=('Arial', 10),
            state='disabled'
        )
        self.open_folder_button.pack(side='left', padx=(10, 0))
    
    def setup_progress_section(self, parent):
        """진행 상황 섹션 구성"""
        progress_frame = tk.LabelFrame(parent, text="⏳ 진행 상황", font=('Arial', 10, 'bold'))
        progress_frame.pack(fill='x', pady=(0, 10))
        
        # 진행률 바
        self.progress_var = tk.StringVar(value="대기 중...")
        progress_label = tk.Label(progress_frame, textvariable=self.progress_var, font=('Arial', 9))
        progress_label.pack(pady=5)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='indeterminate',
            length=400
        )
        self.progress_bar.pack(pady=5)
        
        # 로그 출력
        log_frame = tk.Frame(progress_frame)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        tk.Label(log_frame, text="📋 상세 로그:", font=('Arial', 9, 'bold')).pack(anchor='w')
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            font=('Consolas', 9),
            bg='#2c3e50',
            fg='#ecf0f1'
        )
        self.log_text.pack(fill='both', expand=True, pady=(5, 0))
    
    def setup_result_section(self, parent):
        """결과 섹션 구성"""
        result_frame = tk.LabelFrame(parent, text="📊 동기화 결과", font=('Arial', 10, 'bold'))
        result_frame.pack(fill='both', expand=True)
        
        # 결과 요약
        summary_frame = tk.Frame(result_frame)
        summary_frame.pack(fill='x', padx=10, pady=5)
        
        self.result_summary_label = tk.Label(
            summary_frame,
            text="DB 동기화를 실행하면 결과가 여기에 표시됩니다.",
            font=('Arial', 9),
            fg='gray'
        )
        self.result_summary_label.pack()
        
        # 상세 보고서
        report_frame = tk.Frame(result_frame)
        report_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        tk.Label(report_frame, text="📋 상세 보고서:", font=('Arial', 9, 'bold')).pack(anchor='w')
        
        self.report_text = scrolledtext.ScrolledText(
            report_frame,
            height=10,
            font=('Consolas', 9),
            bg='#ecf0f1',
            fg='#2c3e50'
        )
        self.report_text.pack(fill='both', expand=True, pady=(5, 0))
    
    def _load_data_info(self):
        """data_info 파일들 로드"""
        try:
            self.data_info_loader.load_all_files()
            summary = self.data_info_loader.get_summary()
            
            if summary['path_exists']:
                status_text = f"✅ 로드됨 ({summary['data_counts']['indicators']}개 지표)"
                self.data_info_status_label.config(text=status_text, fg='green')
            else:
                self.data_info_status_label.config(text="❌ 경로 없음", fg='red')
                
            print(f"✅ data_info 상태: {summary}")
            
        except Exception as e:
            self.data_info_status_label.config(text=f"❌ 로드 실패", fg='red')
            print(f"⚠️ data_info 로드 실패: {str(e)}")
    
    def set_db_path(self, db_path):
        """DB 경로 설정"""
        self.db_path = db_path
        if db_path:
            try:
                self.db_manager = DBDataManager(db_path)
                self.db_path_label.config(text=os.path.basename(db_path), fg='green')
                
                # 기본 출력 경로 설정
                default_output = os.path.dirname(os.path.dirname(__file__))
                self.output_path_var.set(default_output)
                self.output_directory = default_output
                
                self.update_filename_preview()
                self.sync_button.config(state='normal')
                
                self._log(f"✅ DB 연결 성공: {os.path.basename(db_path)}")
                
            except Exception as e:
                self.db_path_label.config(text=f"DB 오류", fg='red')
                self.sync_button.config(state='disabled')
                self._log(f"❌ DB 연결 실패: {str(e)}")
        else:
            self.db_path_label.config(text="선택되지 않음", fg='red')
            self.sync_button.config(state='disabled')
    
    def browse_output_directory(self):
        """출력 폴더 선택"""
        directory = filedialog.askdirectory(
            title="출력 폴더 선택",
            initialdir=self.output_directory or os.getcwd()
        )
        
        if directory:
            self.output_directory = directory
            self.output_path_var.set(directory)
            self.update_filename_preview()
    
    def update_filename_preview(self):
        """생성될 파일명 미리보기 업데이트"""
        if self.output_directory:
            filename = create_safe_filename(self.output_directory)
            preview = os.path.basename(filename)
            self.filename_preview_label.config(text=preview)
    
    def start_sync(self):
        """동기화 시작 (별도 스레드)"""
        if not self.db_path or not os.path.exists(self.db_path):
            messagebox.showerror("오류", "유효한 DB 파일을 선택해주세요.")
            return
        
        if not self.output_directory:
            messagebox.showerror("오류", "출력 폴더를 선택해주세요.")
            return
        
        # UI 상태 변경
        self.sync_button.config(state='disabled')
        self.progress_bar.start()
        self.progress_var.set("DB 동기화 진행 중...")
        self.log_text.delete(1.0, tk.END)
        self.report_text.delete(1.0, tk.END)
        
        # 별도 스레드에서 동기화 실행
        thread = threading.Thread(target=self._sync_worker)
        thread.daemon = True
        thread.start()
    
    def _sync_worker(self):
        """동기화 작업 실행 (간소화된 워커 스레드)"""
        try:
            self._log("🔄 DB 중심 동기화 시작...")
            self._log(f"📁 출력 폴더: {self.output_directory}")
            self._log(f"💾 DB 경로: {self.db_path}")
            
            # 1. DB 데이터 로드
            self._log("📊 DB에서 모든 데이터 로딩 중...")
            db_data = self.db_manager.get_variable_definitions_data()
            indicator_count = db_data['stats']['active_indicators']
            self._log(f"✅ {indicator_count}개 지표 및 관련 데이터 로드 완료")
            
            # 2. data_info 데이터 로드
            self._log("📋 data_info 보조 데이터 로딩 중...")
            data_info = self.data_info_loader.load_all_files()
            validation = self.data_info_loader.validate_data_integrity()
            
            if validation['is_valid']:
                self._log("✅ data_info 데이터 검증 통과")
            else:
                self._log(f"⚠️ data_info 검증 경고: {len(validation['warnings'])}개")
            
            # 3. 코드 생성
            self._log("📝 variable_definitions.py 파일 생성 중...")
            output_file = create_safe_filename(self.output_directory)
            
            generator = VariableDefinitionsGenerator(db_data, data_info)
            success = generator.save_to_file(output_file)
            
            if success:
                self.last_generated_file = output_file
                self._log(f"✅ 파일 생성 완료: {os.path.basename(output_file)}")
                
                # 4. 보고서 생성
                self._log("📋 동기화 보고서 생성 중...")
                report = self._generate_sync_report(db_data, data_info, validation)
                
                # UI 업데이트
                self.after(0, self._sync_completed, True, output_file, report)
            else:
                raise Exception("파일 생성 실패")
                
        except Exception as e:
            error_msg = f"❌ 동기화 실패: {str(e)}"
            self._log(error_msg)
            self.after(0, self._sync_completed, False, None, str(e))
    
    def _sync_completed(self, success, output_file, report_or_error):
        """동기화 완료 (메인 스레드)"""
        # UI 상태 복원
        self.progress_bar.stop()
        self.sync_button.config(state='normal')
        
        if success:
            self.progress_var.set("✅ DB 동기화 완료!")
            self.result_summary_label.config(
                text=f"✅ 성공! 파일: {os.path.basename(output_file)}",
                fg='green'
            )
            
            # 보고서 표시
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END, report_or_error)
            
            # 버튼 활성화
            self.open_file_button.config(state='normal')
            self.open_folder_button.config(state='normal')
            
            # 파일명 미리보기 업데이트
            self.update_filename_preview()
            
        else:
            self.progress_var.set("❌ 동기화 실패")
            self.result_summary_label.config(
                text=f"❌ 실패: {report_or_error}",
                fg='red'
            )
    
    def _generate_sync_report(self, db_data: Dict[str, Any], data_info: Dict[str, Any], validation: Dict[str, Any]) -> str:
        """동기화 보고서 생성"""
        stats = db_data.get("stats", {})
        indicators = db_data.get("indicators", {})
        
        report_lines = [
            "🔄 DB 중심 동기화 보고서",
            "=" * 50,
            f"📊 총 지표 수: {len(indicators)}개",
            f"🔧 활성 지표: {stats.get('active_indicators', 0)}개",
            f"📋 총 파라미터: {stats.get('total_parameters', 0)}개",
            f"📅 동기화 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "📊 카테고리별 분포:",
        ]
        
        for category, count in stats.get("category_distribution", {}).items():
            report_lines.append(f"  - {category}: {count}개")
        
        report_lines.extend([
            "",
            "🎨 차트 위치별 분포:",
        ])
        
        for position, count in stats.get("chart_distribution", {}).items():
            report_lines.append(f"  - {position}: {count}개")
        
        # data_info 상태 정보
        if data_info:
            data_info_summary = self.data_info_loader.get_summary()
            report_lines.extend([
                "",
                "📁 data_info 보조 데이터:",
                f"  - 경로: {data_info_summary['data_info_path']}",
                f"  - 지표 라이브러리: {data_info_summary['data_counts']['indicators']}개",
                f"  - 도움말: {data_info_summary['data_counts']['help_texts']}개",
                f"  - 플레이스홀더: {data_info_summary['data_counts']['placeholders']}개",
            ])
            
            if validation:
                if validation['is_valid']:
                    report_lines.append("  - 검증 상태: ✅ 통과")
                else:
                    report_lines.append(f"  - 검증 상태: ⚠️ 경고 {len(validation['warnings'])}개")
                    for warning in validation['warnings'][:3]:  # 처음 3개만
                        report_lines.append(f"    • {warning}")
        
        report_lines.extend([
            "",
            "✅ DB 중심 동기화 성공!",
            "📁 생성된 파일을 확인하고 필요시 기존 파일과 교체하세요.",
            "",
            "🚀 향후 계획:",
            "  - data_info → DB 마이그레이션으로 완전한 DB 중심화",
            "  - 모든 정보가 DB에 통합되면 data_info 폴더는 제거 예정",
            "  - LLM 에이전트와 사용자는 DB만 수정하면 됨"
        ])
        
        return "\n".join(report_lines)
    
    def _log(self, message):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # 메인 스레드에서 실행되는지 확인
        if threading.current_thread() == threading.main_thread():
            self.log_text.insert(tk.END, log_message)
            self.log_text.see(tk.END)
            self.update_idletasks()
        else:
            # 워커 스레드에서는 after 사용
            self.after(0, lambda: self._log_safe(log_message))
    
    def _log_safe(self, log_message):
        """스레드 안전한 로그 메시지 추가"""
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.update_idletasks()
    
    def open_generated_file(self):
        """생성된 파일 열기"""
        if self.last_generated_file and os.path.exists(self.last_generated_file):
            try:
                if sys.platform == "win32":
                    os.startfile(self.last_generated_file)
                else:
                    import subprocess
                    subprocess.call(["open", self.last_generated_file])
            except Exception as e:
                messagebox.showerror("오류", f"파일을 열 수 없습니다: {str(e)}")
        else:
            messagebox.showwarning("경고", "생성된 파일이 없습니다.")
    
    def open_output_folder(self):
        """출력 폴더 열기"""
        if self.output_directory and os.path.exists(self.output_directory):
            try:
                if sys.platform == "win32":
                    os.startfile(self.output_directory)
                else:
                    import subprocess
                    subprocess.call(["open", self.output_directory])
            except Exception as e:
                messagebox.showerror("오류", f"폴더를 열 수 없습니다: {str(e)}")
        else:
            messagebox.showwarning("경고", "출력 폴더가 설정되지 않았습니다.")
