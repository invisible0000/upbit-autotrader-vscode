#!/usr/bin/env python3
"""
💾 Backup Manager Component
백업 파일 관리 및 복원 기능 컴포넌트

작성일: 2025-07-30
"""

import os
import shutil
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime


class BackupManagerFrame(tk.Frame):
    """백업 관리 프레임"""
    
    def __init__(self, parent):
        """
        초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent, bg='white')
        self.current_db_path = None
        self.backup_directory = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI 구성"""
        # 제목
        title_label = tk.Label(
            self,
            text="💾 백업 파일 관리 & 복원",
            font=('Arial', 14, 'bold'),
            bg='white',
            fg='#2c3e50'
        )
        title_label.pack(pady=(20, 10))
        
        # 백업 디렉토리 선택
        dir_frame = tk.LabelFrame(
            self,
            text="📁 백업 디렉토리",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        dir_frame.pack(fill='x', padx=20, pady=10)
        
        dir_control_frame = tk.Frame(dir_frame, bg='white')
        dir_control_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(dir_control_frame, text="디렉토리:", bg='white', width=10, anchor='w').pack(side='left')
        
        self.backup_dir_var = tk.StringVar(value="백업 디렉토리를 선택하세요")
        dir_entry = tk.Entry(
            dir_control_frame,
            textvariable=self.backup_dir_var,
            state='readonly'
        )
        dir_entry.pack(side='left', fill='x', expand=True, padx=(5, 10))
        
        select_dir_btn = tk.Button(
            dir_control_frame,
            text="📂 선택",
            command=self.select_backup_directory,
            bg='#3498db',
            fg='white',
            font=('Arial', 9, 'bold'),
            width=8
        )
        select_dir_btn.pack(side='left', padx=(0, 10))
        
        refresh_btn = tk.Button(
            dir_control_frame,
            text="🔄 새로고침",
            command=self.refresh_backup_list,
            bg='#27ae60',
            fg='white',
            font=('Arial', 9, 'bold'),
            width=10
        )
        refresh_btn.pack(side='left')
        
        # 백업 파일 목록
        list_frame = tk.LabelFrame(
            self,
            text="📋 백업 파일 목록",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 백업 파일 트리뷰
        self.backup_tree = ttk.Treeview(
            list_frame,
            columns=('filename', 'date', 'size', 'type', 'status'),
            show='tree headings',
            height=12
        )
        
        # 트리뷰 헤더 설정
        self.backup_tree.heading('#0', text='백업 파일')
        self.backup_tree.heading('filename', text='파일명')
        self.backup_tree.heading('date', text='생성일시')
        self.backup_tree.heading('size', text='크기')
        self.backup_tree.heading('type', text='유형')
        self.backup_tree.heading('status', text='상태')
        
        # 트리뷰 컬럼 너비 설정
        self.backup_tree.column('#0', width=40)
        self.backup_tree.column('filename', width=180)
        self.backup_tree.column('date', width=130)
        self.backup_tree.column('size', width=80)
        self.backup_tree.column('type', width=80)
        self.backup_tree.column('status', width=100)
        
        # 스크롤바 추가
        tree_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.backup_tree.yview)
        tree_scrollbar.pack(side='right', fill='y')
        self.backup_tree.config(yscrollcommand=tree_scrollbar.set)
        
        self.backup_tree.pack(fill='both', expand=True, padx=(10, 0), pady=10)
        
        # 백업 파일 선택 이벤트
        self.backup_tree.bind('<<TreeviewSelect>>', self.on_backup_selected)
        self.backup_tree.bind('<Double-1>', self.on_backup_double_click)
        
        # 컨트롤 버튼들
        control_frame = tk.Frame(self, bg='white')
        control_frame.pack(fill='x', padx=20, pady=10)
        
        # 수동 백업 생성
        create_backup_btn = tk.Button(
            control_frame,
            text="💾 수동 백업 생성",
            command=self.create_manual_backup,
            bg='#3498db',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=15
        )
        create_backup_btn.pack(side='left', padx=(0, 10))
        
        # 백업 복원
        self.restore_btn = tk.Button(
            control_frame,
            text="🔄 백업 복원",
            command=self.restore_from_backup,
            bg='#e67e22',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=12,
            state='disabled'
        )
        self.restore_btn.pack(side='left', padx=(0, 10))
        
        # 백업 파일 삭제
        self.delete_btn = tk.Button(
            control_frame,
            text="🗑️ 삭제",
            command=self.delete_backup,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=8,
            state='disabled'
        )
        self.delete_btn.pack(side='left', padx=(0, 10))
        
        # 백업 파일 검증
        self.verify_btn = tk.Button(
            control_frame,
            text="🔍 검증",
            command=self.verify_backup,
            bg='#9b59b6',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=8,
            state='disabled'
        )
        self.verify_btn.pack(side='left', padx=(0, 10))
        
        # 백업 내보내기
        self.export_btn = tk.Button(
            control_frame,
            text="📤 내보내기",
            command=self.export_backup,
            bg='#1abc9c',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=10,
            state='disabled'
        )
        self.export_btn.pack(side='left')
        
        # 선택된 백업 정보 표시
        info_frame = tk.LabelFrame(
            self,
            text="ℹ️ 선택된 백업 정보",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        info_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.info_text = tk.Text(
            info_frame,
            height=5,
            wrap='word',
            bg='#f8f9fa',
            fg='#2c3e50',
            font=('Arial', 9),
            state='disabled'
        )
        self.info_text.pack(fill='x', padx=10, pady=10)
    
    def set_db_path(self, db_path):
        """
        DB 경로 설정
        
        Args:
            db_path: DB 파일 경로
        """
        self.current_db_path = db_path
        
        # 기본 백업 디렉토리 설정
        if db_path:
            default_backup_dir = os.path.join(os.path.dirname(db_path), "backups")
            if os.path.exists(default_backup_dir):
                self.backup_directory = default_backup_dir
                self.backup_dir_var.set(default_backup_dir)
                self.refresh_backup_list()
            else:
                # 백업 디렉토리가 없으면 생성
                try:
                    os.makedirs(default_backup_dir, exist_ok=True)
                    self.backup_directory = default_backup_dir
                    self.backup_dir_var.set(default_backup_dir)
                except Exception as e:
                    print(f"백업 디렉토리 생성 실패: {e}")
    
    def select_backup_directory(self):
        """백업 디렉토리 선택"""
        directory = filedialog.askdirectory(
            title="백업 디렉토리 선택",
            initialdir=self.backup_directory if self.backup_directory else os.getcwd()
        )
        
        if directory:
            self.backup_directory = directory
            self.backup_dir_var.set(directory)
            self.refresh_backup_list()
    
    def refresh_backup_list(self):
        """백업 파일 목록 새로고침"""
        # 기존 데이터 클리어
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        if not self.backup_directory or not os.path.exists(self.backup_directory):
            self.insert_no_backups_message()
            return
        
        try:
            # 백업 파일 검색
            backup_files = []
            for filename in os.listdir(self.backup_directory):
                if filename.endswith('.sqlite3') and ('backup' in filename.lower() or 'bck' in filename.lower()):
                    file_path = os.path.join(self.backup_directory, filename)
                    backup_files.append((filename, file_path))
            
            if not backup_files:
                self.insert_no_backups_message()
                return
            
            # 파일 정보 수집 및 정렬
            backup_info = []
            for filename, file_path in backup_files:
                try:
                    stat = os.stat(file_path)
                    
                    # 파일 생성 시간
                    create_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    # 파일 크기
                    size = self.format_file_size(stat.st_size)
                    
                    # 백업 유형 추정
                    backup_type = self.determine_backup_type(filename)
                    
                    # 파일 상태 확인
                    status = self.check_backup_status(file_path)
                    
                    backup_info.append({
                        'filename': filename,
                        'path': file_path,
                        'date': create_time,
                        'size': size,
                        'type': backup_type,
                        'status': status,
                        'timestamp': stat.st_mtime
                    })
                    
                except Exception as e:
                    print(f"파일 정보 수집 오류 ({filename}): {e}")
            
            # 생성 시간 기준 내림차순 정렬 (최신 파일이 위로)
            backup_info.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # 트리뷰에 추가
            for info in backup_info:
                # 아이콘 선택
                if info['status'] == '정상':
                    icon = '✅'
                elif info['status'] == '손상':
                    icon = '❌'
                else:
                    icon = '❓'
                
                self.backup_tree.insert(
                    '',
                    'end',
                    text=icon,
                    values=(
                        info['filename'],
                        info['date'].strftime('%Y-%m-%d %H:%M:%S'),
                        info['size'],
                        info['type'],
                        info['status']
                    ),
                    tags=(info['path'],)
                )
            
        except Exception as e:
            messagebox.showerror(
                "목록 새로고침 실패",
                f"백업 파일 목록을 불러오는 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def insert_no_backups_message(self):
        """백업 파일 없음 메시지 표시"""
        self.backup_tree.insert(
            '',
            'end',
            text='ℹ️',
            values=('백업 파일이 없습니다', '', '', '', '수동으로 백업을 생성하세요')
        )
    
    def format_file_size(self, size_bytes):
        """파일 크기 포맷팅"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def determine_backup_type(self, filename):
        """백업 유형 결정"""
        filename_lower = filename.lower()
        
        if 'bck_' in filename_lower:
            return '정밀백업'
        elif 'backup_' in filename_lower:
            return '일반백업'
        elif 'auto' in filename_lower:
            return '자동백업'
        elif 'manual' in filename_lower:
            return '수동백업'
        else:
            return '기타'
    
    def check_backup_status(self, file_path):
        """백업 파일 상태 확인"""
        try:
            # SQLite 파일 무결성 간단 체크
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            cursor.fetchone()
            conn.close()
            return '정상'
        except Exception:
            return '손상'
    
    def on_backup_selected(self, event):
        """백업 파일 선택 이벤트"""
        selection = self.backup_tree.selection()
        if not selection:
            self.clear_backup_info()
            self.disable_backup_buttons()
            return
        
        item = self.backup_tree.item(selection[0])
        
        # 백업 파일 경로 추출
        tags = item.get('tags', [])
        if not tags:
            self.clear_backup_info()
            self.disable_backup_buttons()
            return
        
        backup_path = tags[0]
        
        # 백업 정보 표시
        self.display_backup_info(backup_path)
        
        # 버튼 활성화
        self.enable_backup_buttons()
    
    def on_backup_double_click(self, event):
        """백업 파일 더블클릭 이벤트 (복원)"""
        selection = self.backup_tree.selection()
        if selection:
            self.restore_from_backup()
    
    def display_backup_info(self, backup_path):
        """백업 파일 상세 정보 표시"""
        try:
            # 파일 기본 정보
            stat = os.stat(backup_path)
            create_time = datetime.fromtimestamp(stat.st_mtime)
            size = self.format_file_size(stat.st_size)
            
            info_lines = []
            info_lines.append(f"📁 파일 경로: {backup_path}")
            info_lines.append(f"📅 생성 시간: {create_time.strftime('%Y년 %m월 %d일 %H시 %M분 %S초')}")
            info_lines.append(f"📊 파일 크기: {size}")
            info_lines.append("")
            
            # DB 내용 간단 분석
            try:
                with sqlite3.connect(backup_path) as conn:
                    cursor = conn.cursor()
                    
                    # 테이블 목록
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    info_lines.append(f"🗃️ 테이블 수: {len(tables)}개")
                    
                    # Trading Variables 관련 테이블 확인
                    tv_tables = [t for t in tables if 'trading_variables' in t.lower() or 'variable_parameters' in t.lower()]
                    if tv_tables:
                        info_lines.append(f"📊 Trading Variables 테이블: {len(tv_tables)}개")
                        
                        for table in tv_tables:
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cursor.fetchone()[0]
                            info_lines.append(f"   • {table}: {count}개 레코드")
                    
            except Exception as e:
                info_lines.append(f"⚠️ DB 분석 실패: {str(e)}")
            
            # 정보 텍스트 업데이트
            self.info_text.config(state='normal')
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, '\n'.join(info_lines))
            self.info_text.config(state='disabled')
            
        except Exception as e:
            error_msg = f"❌ 백업 파일 정보를 불러올 수 없습니다:\n{str(e)}"
            self.info_text.config(state='normal')
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, error_msg)
            self.info_text.config(state='disabled')
    
    def clear_backup_info(self):
        """백업 정보 클리어"""
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, "백업 파일을 선택하세요.")
        self.info_text.config(state='disabled')
    
    def enable_backup_buttons(self):
        """백업 관련 버튼 활성화"""
        self.restore_btn.config(state='normal')
        self.delete_btn.config(state='normal')
        self.verify_btn.config(state='normal')
        self.export_btn.config(state='normal')
    
    def disable_backup_buttons(self):
        """백업 관련 버튼 비활성화"""
        self.restore_btn.config(state='disabled')
        self.delete_btn.config(state='disabled')
        self.verify_btn.config(state='disabled')
        self.export_btn.config(state='disabled')
    
    def create_manual_backup(self):
        """수동 백업 생성"""
        if not self.current_db_path:
            messagebox.showwarning("DB 미선택", "먼저 DB 파일을 선택하세요.")
            return
        
        if not os.path.exists(self.current_db_path):
            messagebox.showerror("DB 파일 없음", f"DB 파일을 찾을 수 없습니다:\n{self.current_db_path}")
            return
        
        try:
            # 백업 파일명 생성 (정밀한 타임스탬프)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"settings_manual_bck_{timestamp}.sqlite3"
            backup_path = os.path.join(self.backup_directory, backup_filename)
            
            # 백업 디렉토리 생성
            os.makedirs(self.backup_directory, exist_ok=True)
            
            # 파일 복사
            shutil.copy2(self.current_db_path, backup_path)
            
            messagebox.showinfo(
                "백업 완료",
                f"수동 백업이 완료되었습니다!\n\n"
                f"파일명: {backup_filename}\n"
                f"위치: {self.backup_directory}"
            )
            
            # 목록 새로고침
            self.refresh_backup_list()
            
        except Exception as e:
            messagebox.showerror(
                "백업 실패",
                f"백업 생성 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def restore_from_backup(self):
        """백업에서 복원"""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("백업 미선택", "복원할 백업 파일을 선택하세요.")
            return
        
        item = self.backup_tree.item(selection[0])
        tags = item.get('tags', [])
        if not tags:
            return
        
        backup_path = tags[0]
        backup_filename = item['values'][0]
        
        # 확인 다이얼로그
        result = messagebox.askyesno(
            "백업 복원 확인",
            f"⚠️ 다음 백업으로 복원하시겠습니까?\n\n"
            f"백업 파일: {backup_filename}\n"
            f"현재 DB: {os.path.basename(self.current_db_path) if self.current_db_path else 'None'}\n\n"
            "⚠️ 현재 DB의 모든 데이터가 백업 내용으로 덮어씌워집니다!\n"
            "이 작업은 되돌릴 수 없습니다."
        )
        
        if not result:
            return
        
        try:
            # 현재 DB 백업 (복원 전 안전장치)
            if self.current_db_path and os.path.exists(self.current_db_path):
                safety_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safety_backup = os.path.join(
                    self.backup_directory,
                    f"settings_safety_bck_{safety_timestamp}.sqlite3"
                )
                shutil.copy2(self.current_db_path, safety_backup)
            
            # 백업에서 복원
            shutil.copy2(backup_path, self.current_db_path)
            
            messagebox.showinfo(
                "복원 완료",
                f"✅ 백업 복원이 완료되었습니다!\n\n"
                f"복원된 백업: {backup_filename}\n"
                f"안전 백업: {os.path.basename(safety_backup) if 'safety_backup' in locals() else 'None'}\n\n"
                "애플리케이션을 재시작하여 변경사항을 적용하세요."
            )
            
        except Exception as e:
            messagebox.showerror(
                "복원 실패",
                f"백업 복원 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def delete_backup(self):
        """백업 파일 삭제"""
        selection = self.backup_tree.selection()
        if not selection:
            return
        
        item = self.backup_tree.item(selection[0])
        tags = item.get('tags', [])
        if not tags:
            return
        
        backup_path = tags[0]
        backup_filename = item['values'][0]
        
        # 확인 다이얼로그
        result = messagebox.askyesno(
            "백업 삭제 확인",
            f"🗑️ 다음 백업 파일을 삭제하시겠습니까?\n\n"
            f"파일: {backup_filename}\n\n"
            "⚠️ 삭제된 백업은 복구할 수 없습니다!"
        )
        
        if not result:
            return
        
        try:
            os.remove(backup_path)
            messagebox.showinfo("삭제 완료", f"백업 파일이 삭제되었습니다:\n{backup_filename}")
            self.refresh_backup_list()
            self.clear_backup_info()
            
        except Exception as e:
            messagebox.showerror(
                "삭제 실패",
                f"백업 파일 삭제 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def verify_backup(self):
        """백업 파일 검증"""
        selection = self.backup_tree.selection()
        if not selection:
            return
        
        item = self.backup_tree.item(selection[0])
        tags = item.get('tags', [])
        if not tags:
            return
        
        backup_path = tags[0]
        backup_filename = item['values'][0]
        
        try:
            verification_results = []
            
            # 1. 파일 존재 및 크기 확인
            if os.path.exists(backup_path):
                size = os.path.getsize(backup_path)
                verification_results.append(f"✅ 파일 존재: 예 ({self.format_file_size(size)})")
            else:
                verification_results.append("❌ 파일 존재: 아니오")
                raise FileNotFoundError("백업 파일을 찾을 수 없습니다")
            
            # 2. SQLite 파일 무결성 확인
            try:
                conn = sqlite3.connect(backup_path)
                cursor = conn.cursor()
                
                # PRAGMA integrity_check
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                
                if integrity_result == "ok":
                    verification_results.append("✅ DB 무결성: 정상")
                else:
                    verification_results.append(f"❌ DB 무결성: {integrity_result}")
                
                # 3. 테이블 구조 확인
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                verification_results.append(f"📋 테이블 수: {len(tables)}개")
                
                # 4. Trading Variables 테이블 확인
                tv_tables = [t for t in tables if 'trading_variables' in t.lower() or 'variable_parameters' in t.lower()]
                if tv_tables:
                    verification_results.append(f"📊 Trading Variables 테이블: {len(tv_tables)}개")
                    
                    for table in tv_tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        verification_results.append(f"   • {table}: {count}개 레코드")
                
                conn.close()
                
            except Exception as e:
                verification_results.append(f"❌ DB 검증 실패: {str(e)}")
            
            # 결과 표시
            messagebox.showinfo(
                f"백업 검증 결과 - {backup_filename}",
                '\n'.join(verification_results)
            )
            
        except Exception as e:
            messagebox.showerror(
                "검증 실패",
                f"백업 파일 검증 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def export_backup(self):
        """백업 파일 내보내기"""
        selection = self.backup_tree.selection()
        if not selection:
            return
        
        item = self.backup_tree.item(selection[0])
        tags = item.get('tags', [])
        if not tags:
            return
        
        backup_path = tags[0]
        backup_filename = item['values'][0]
        
        # 내보낼 위치 선택
        export_path = filedialog.asksaveasfilename(
            title="백업 파일 내보내기",
            initialfilename=backup_filename,
            defaultextension=".sqlite3",
            filetypes=[
                ("SQLite files", "*.sqlite3"),
                ("Database files", "*.db"),
                ("All files", "*.*")
            ]
        )
        
        if not export_path:
            return
        
        try:
            shutil.copy2(backup_path, export_path)
            messagebox.showinfo(
                "내보내기 완료",
                f"백업 파일이 성공적으로 내보내졌습니다:\n{export_path}"
            )
            
        except Exception as e:
            messagebox.showerror(
                "내보내기 실패",
                f"백업 파일 내보내기 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def get_selected_backup_path(self):
        """선택된 백업 파일 경로 반환"""
        selection = self.backup_tree.selection()
        if not selection:
            return None
        
        item = self.backup_tree.item(selection[0])
        tags = item.get('tags', [])
        return tags[0] if tags else None
