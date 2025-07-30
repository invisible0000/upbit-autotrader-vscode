#!/usr/bin/env python3
"""
📁 Database Selector Component
DB 파일 선택 및 기본 정보 표시 컴포넌트

작성일: 2025-07-30
"""

import os
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class DatabaseSelectorFrame(tk.Frame):
    """DB 파일 선택 프레임"""
    
    def __init__(self, parent, on_db_selected=None):
        """
        초기화
        
        Args:
            parent: 부모 위젯
            on_db_selected: DB 선택 시 호출될 콜백 함수
        """
        super().__init__(parent, bg='white')
        self.on_db_selected = on_db_selected
        self.current_db_path = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI 구성"""
        # 제목
        title_label = tk.Label(
            self,
            text="📁 데이터베이스 파일 선택",
            font=('Arial', 14, 'bold'),
            bg='white',
            fg='#2c3e50'
        )
        title_label.pack(pady=(20, 10))
        
        # DB 선택 섹션
        select_frame = tk.LabelFrame(
            self,
            text="DB 파일 선택",
            font=('Arial', 10, 'bold'),
            bg='white',
            pady=10
        )
        select_frame.pack(fill='x', padx=20, pady=10)
        
        # 현재 DB 경로 표시
        path_frame = tk.Frame(select_frame, bg='white')
        path_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(path_frame, text="현재 DB:", bg='white', width=10, anchor='w').pack(side='left')
        
        self.path_var = tk.StringVar(value="선택되지 않음")
        self.path_entry = tk.Entry(
            path_frame,
            textvariable=self.path_var,
            state='readonly',
            width=50
        )
        self.path_entry.pack(side='left', padx=(5, 10), fill='x', expand=True)
        
        # 버튼 프레임
        button_frame = tk.Frame(select_frame, bg='white')
        button_frame.pack(fill='x', padx=10, pady=5)
        
        # DB 파일 선택 버튼
        select_btn = tk.Button(
            button_frame,
            text="📂 DB 파일 선택",
            command=self.select_db_file,
            bg='#3498db',
            fg='white',
            font=('Arial', 9, 'bold'),
            width=15
        )
        select_btn.pack(side='left', padx=(0, 10))
        
        # 기본 경로 사용 버튼
        default_btn = tk.Button(
            button_frame,
            text="🏠 기본 경로 사용",
            command=self.use_default_path,
            bg='#27ae60',
            fg='white',
            font=('Arial', 9, 'bold'),
            width=15
        )
        default_btn.pack(side='left', padx=(0, 10))
        
        # 새 DB 생성 버튼
        create_btn = tk.Button(
            button_frame,
            text="➕ 새 DB 생성",
            command=self.create_new_db,
            bg='#e67e22',
            fg='white',
            font=('Arial', 9, 'bold'),
            width=15
        )
        create_btn.pack(side='left', padx=(0, 10))
        
        # 새로고침 버튼 추가
        refresh_btn = tk.Button(
            button_frame,
            text="🔄 새로고침",
            command=self.refresh_db_info,
            bg='#9b59b6',
            fg='white',
            font=('Arial', 9, 'bold'),
            width=15
        )
        refresh_btn.pack(side='left')
        
        # DB 정보 표시 섹션
        info_frame = tk.LabelFrame(
            self,
            text="DB 정보",
            font=('Arial', 10, 'bold'),
            bg='white',
            pady=10
        )
        info_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 정보 표시 텍스트 위젯
        self.info_text = tk.Text(
            info_frame,
            height=15,
            wrap='word',
            bg='#f8f9fa',
            fg='#2c3e50',
            font=('Courier', 9),
            state='disabled'
        )
        self.info_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 스크롤바 추가
        scrollbar = ttk.Scrollbar(info_frame, orient='vertical', command=self.info_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.info_text.config(yscrollcommand=scrollbar.set)
    
    def select_db_file(self):
        """DB 파일 선택 다이얼로그"""
        file_path = filedialog.askopenfilename(
            title="Trading Variables DB 파일 선택",
            filetypes=[
                ("SQLite files", "*.sqlite3"),
                ("SQLite files", "*.sqlite"),
                ("Database files", "*.db"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.set_db_path(file_path)
    
    def use_default_path(self):
        """기본 DB 경로 사용"""
        # 프로젝트 루트에서 기본 DB 경로 계산
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
        default_path = os.path.join(project_root, "upbit_auto_trading", "data", "settings.sqlite3")
        
        print(f"🔍 기본 경로 계산:")
        print(f"   현재 디렉토리: {current_dir}")
        print(f"   프로젝트 루트: {project_root}")
        print(f"   기본 DB 경로: {default_path}")
        print(f"   파일 존재 여부: {os.path.exists(default_path)}")
        
        if os.path.exists(default_path):
            self.set_db_path(default_path)
        else:
            # 다른 가능한 경로들 시도
            alternative_paths = [
                os.path.join(os.getcwd(), "upbit_auto_trading", "data", "settings.sqlite3"),
                "upbit_auto_trading/data/settings.sqlite3",
                "./upbit_auto_trading/data/settings.sqlite3"
            ]
            
            found_path = None
            for alt_path in alternative_paths:
                print(f"   대체 경로 확인: {alt_path} -> {os.path.exists(alt_path)}")
                if os.path.exists(alt_path):
                    found_path = alt_path
                    break
            
            if found_path:
                print(f"✅ 대체 경로에서 파일 발견: {found_path}")
                self.set_db_path(found_path)
            else:
                messagebox.showerror(
                    "파일 없음",
                    f"기본 DB 파일을 찾을 수 없습니다:\n{default_path}\n\n새로 생성하거나 다른 파일을 선택하세요."
                )
    
    def create_new_db(self):
        """새 DB 파일 생성"""
        file_path = filedialog.asksaveasfilename(
            title="새 DB 파일 생성",
            defaultextension=".sqlite3",
            filetypes=[
                ("SQLite files", "*.sqlite3"),
                ("SQLite files", "*.sqlite"),
                ("Database files", "*.db")
            ]
        )
        
        if file_path:
            try:
                # 빈 DB 파일 생성
                conn = sqlite3.connect(file_path)
                conn.close()
                
                messagebox.showinfo(
                    "DB 생성 완료",
                    f"새 DB 파일이 생성되었습니다:\n{file_path}"
                )
                
                self.set_db_path(file_path)
                
            except Exception as e:
                messagebox.showerror(
                    "DB 생성 실패",
                    f"DB 파일 생성 중 오류가 발생했습니다:\n{str(e)}"
                )
    
    def set_db_path(self, db_path):
        """
        DB 경로 설정 및 정보 업데이트
        
        Args:
            db_path: DB 파일 경로
        """
        self.current_db_path = db_path
        self.path_var.set(db_path)
        
        # DB 정보 분석 및 표시
        self.analyze_and_display_db_info()
        
        # 콜백 호출 (DB 선택 시에는 탭 이동하지 않음)
        if self.on_db_selected:
            self.on_db_selected(db_path, auto_switch_tab=False)
    
    def refresh_db_info(self):
        """DB 정보 새로고침"""
        if self.current_db_path:
            self.analyze_and_display_db_info()
            # 콜백 호출하여 다른 탭들도 새로고침 (현재 탭 유지)
            if self.on_db_selected:
                self.on_db_selected(self.current_db_path, auto_switch_tab=False)
        else:
            self.display_info("❌ 선택된 DB가 없습니다. DB를 먼저 선택해주세요.")
    
    def analyze_and_display_db_info(self):
        """DB 정보 분석 및 표시"""
        if not self.current_db_path or not os.path.exists(self.current_db_path):
            self.display_info("❌ DB 파일을 찾을 수 없습니다.")
            return
        
        try:
            with sqlite3.connect(self.current_db_path) as conn:
                cursor = conn.cursor()
                
                info_lines = []
                info_lines.append("🎯 Trading Variables Database 정보")
                info_lines.append("=" * 50)
                info_lines.append(f"📁 파일 경로: {self.current_db_path}")
                info_lines.append(f"📊 파일 크기: {self.get_file_size()}")
                info_lines.append("")
                
                # 테이블 목록 조회
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [row[0] for row in cursor.fetchall()]
                
                info_lines.append(f"📋 테이블 목록 ({len(tables)}개):")
                info_lines.append("-" * 30)
                
                for table in tables:
                    # 각 테이블의 레코드 수 조회
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        
                        # 테이블 유형 표시
                        table_type = self.get_table_type(table)
                        info_lines.append(f"  {table_type} {table}: {count}개 레코드")
                        
                    except sqlite3.Error as e:
                        info_lines.append(f"  ❓ {table}: 조회 실패 ({str(e)})")
                
                info_lines.append("")
                
                # Trading Variables 관련 정보
                if self.has_trading_variables_tables(tables):
                    info_lines.extend(self.get_trading_variables_summary(cursor))
                else:
                    info_lines.append("ℹ️ Trading Variables 관련 테이블이 없습니다.")
                    info_lines.append("   새 스키마를 적용하여 초기화할 수 있습니다.")
                
                self.display_info("\n".join(info_lines))
                
        except Exception as e:
            self.display_info(f"❌ DB 분석 중 오류 발생:\n{str(e)}")
    
    def get_file_size(self):
        """파일 크기 반환"""
        try:
            size = os.path.getsize(self.current_db_path)
            if size < 1024:
                return f"{size} bytes"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        except:
            return "알 수 없음"
    
    def get_table_type(self, table_name):
        """테이블 유형 아이콘 반환"""
        if 'trading_variables' in table_name.lower():
            return "📊"
        elif 'variable_parameters' in table_name.lower():
            return "⚙️"
        elif 'comparison_groups' in table_name.lower():
            return "🔗"
        elif 'schema_version' in table_name.lower():
            return "🏷️"
        elif table_name.startswith('tv_'):
            return "🆕"
        else:
            return "📄"
    
    def has_trading_variables_tables(self, tables):
        """Trading Variables 관련 테이블 존재 여부 확인"""
        tv_patterns = ['trading_variables', 'variable_parameters', 'tv_']
        return any(any(pattern in table.lower() for pattern in tv_patterns) for table in tables)
    
    def get_trading_variables_summary(self, cursor):
        """Trading Variables 요약 정보 생성"""
        summary = []
        summary.append("📊 Trading Variables 요약:")
        summary.append("-" * 30)
        
        try:
            # 새 스키마 테이블 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE name LIKE 'tv_%'")
            new_tables = [row[0] for row in cursor.fetchall()]
            
            if new_tables:
                summary.append("🆕 새 스키마 (tv_ 접두사) 테이블:")
                for table in new_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    summary.append(f"   • {table}: {count}개")
                summary.append("")
            
            # 레거시 테이블 확인
            legacy_patterns = ['trading_variables', 'variable_parameters', 'comparison_groups']
            legacy_tables = []
            
            for pattern in legacy_patterns:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE name = '{pattern}'")
                if cursor.fetchone():
                    legacy_tables.append(pattern)
            
            if legacy_tables:
                summary.append("🔄 레거시 테이블 (마이그레이션 대상):")
                for table in legacy_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    summary.append(f"   • {table}: {count}개")
            
        except sqlite3.Error as e:
            summary.append(f"❌ 요약 정보 조회 실패: {str(e)}")
        
        return summary
    
    def display_info(self, text):
        """정보 텍스트 표시"""
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, text)
        self.info_text.config(state='disabled')
