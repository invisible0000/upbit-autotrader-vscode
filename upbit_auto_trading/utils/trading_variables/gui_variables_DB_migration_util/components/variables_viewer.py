#!/usr/bin/env python3
"""
📊 Variables Viewer Component
기존 변수 및 파라미터 조회 컴포넌트

작성일: 2025-07-30
"""

import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox


class VariablesViewerFrame(tk.Frame):
    """변수 및 파라미터 조회 프레임"""
    
    def __init__(self, parent):
        """
        초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent, bg='white')
        self.current_db_path = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI 구성"""
        # 제목
        title_label = tk.Label(
            self,
            text="📊 현재 변수 및 파라미터 조회",
            font=('Arial', 14, 'bold'),
            bg='white',
            fg='#2c3e50'
        )
        title_label.pack(pady=(20, 10))
        
        # 컨트롤 프레임
        control_frame = tk.Frame(self, bg='white')
        control_frame.pack(fill='x', padx=20, pady=10)
        
        # 새로고침 버튼
        refresh_btn = tk.Button(
            control_frame,
            text="🔄 새로고침",
            command=self.refresh_data,
            bg='#3498db',
            fg='white',
            font=('Arial', 9, 'bold'),
            width=12
        )
        refresh_btn.pack(side='left')
        
        # 카테고리 필터
        tk.Label(control_frame, text="카테고리:", bg='white').pack(side='left', padx=(20, 5))
        
        self.category_var = tk.StringVar(value="전체")
        self.category_combo = ttk.Combobox(
            control_frame,
            textvariable=self.category_var,
            values=["전체", "trend", "momentum", "volatility", "volume", "price", "capital", "state"],
            state="readonly",
            width=15
        )
        self.category_combo.pack(side='left', padx=(0, 10))
        self.category_combo.bind('<<ComboboxSelected>>', self.on_category_changed)
        
        # 활성 상태 필터
        tk.Label(control_frame, text="상태:", bg='white').pack(side='left', padx=(20, 5))
        
        self.status_var = tk.StringVar(value="전체")
        self.status_combo = ttk.Combobox(
            control_frame,
            textvariable=self.status_var,
            values=["전체", "활성", "비활성"],
            state="readonly",
            width=10
        )
        self.status_combo.pack(side='left')
        self.status_combo.bind('<<ComboboxSelected>>', self.on_status_changed)
        
        # 메인 패널 (PanedWindow 사용)
        main_paned = tk.PanedWindow(self, orient='horizontal', bg='white')
        main_paned.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 왼쪽: 변수 목록
        left_frame = tk.LabelFrame(
            main_paned,
            text="Trading Variables",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        main_paned.add(left_frame, width=400)
        
        # 변수 트리뷰
        self.variables_tree = ttk.Treeview(
            left_frame,
            columns=('id', 'name', 'category', 'status'),
            show='tree headings',
            height=15
        )
        
        # 트리뷰 헤더 설정
        self.variables_tree.heading('#0', text='변수')
        self.variables_tree.heading('id', text='ID')
        self.variables_tree.heading('name', text='이름')
        self.variables_tree.heading('category', text='카테고리')
        self.variables_tree.heading('status', text='상태')
        
        # 트리뷰 컬럼 너비 설정
        self.variables_tree.column('#0', width=120)
        self.variables_tree.column('id', width=40)
        self.variables_tree.column('name', width=120)
        self.variables_tree.column('category', width=80)
        self.variables_tree.column('status', width=60)
        
        self.variables_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 변수 선택 이벤트 바인딩
        self.variables_tree.bind('<<TreeviewSelect>>', self.on_variable_selected)
        
        # 오른쪽: 파라미터 상세 정보
        right_frame = tk.LabelFrame(
            main_paned,
            text="Variable Parameters",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        main_paned.add(right_frame, width=500)
        
        # 파라미터 트리뷰
        self.parameters_tree = ttk.Treeview(
            right_frame,
            columns=('param_name', 'param_type', 'default_value', 'description'),
            show='tree headings',
            height=15
        )
        
        # 파라미터 트리뷰 헤더 설정
        self.parameters_tree.heading('#0', text='파라미터')
        self.parameters_tree.heading('param_name', text='이름')
        self.parameters_tree.heading('param_type', text='타입')
        self.parameters_tree.heading('default_value', text='기본값')
        self.parameters_tree.heading('description', text='설명')
        
        # 파라미터 트리뷰 컬럼 너비 설정
        self.parameters_tree.column('#0', width=0, stretch=False)  # 숨김
        self.parameters_tree.column('param_name', width=100)
        self.parameters_tree.column('param_type', width=70)
        self.parameters_tree.column('default_value', width=80)
        self.parameters_tree.column('description', width=200)
        
        self.parameters_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 하단: 통계 정보
        stats_frame = tk.LabelFrame(
            self,
            text="통계 정보",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        stats_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.stats_text = tk.Text(
            stats_frame,
            height=4,
            wrap='word',
            bg='#f8f9fa',
            fg='#2c3e50',
            font=('Arial', 9),
            state='disabled'
        )
        self.stats_text.pack(fill='x', padx=10, pady=10)
    
    def set_db_path(self, db_path):
        """
        DB 경로 설정 및 데이터 로드
        
        Args:
            db_path: DB 파일 경로
        """
        self.current_db_path = db_path
        self.refresh_data()
    
    def refresh_data(self):
        """데이터 새로고침"""
        if not self.current_db_path:
            self.clear_all_data()
            return
        
        try:
            with sqlite3.connect(self.current_db_path) as conn:
                # 변수 데이터 로드
                self.load_variables_data(conn)
                # 통계 정보 업데이트
                self.update_statistics(conn)
                
        except Exception as e:
            messagebox.showerror(
                "데이터 로드 실패",
                f"데이터를 불러오는 중 오류가 발생했습니다:\n{str(e)}"
            )
            self.clear_all_data()
    
    def load_variables_data(self, conn):
        """변수 데이터 로드"""
        cursor = conn.cursor()
        
        # 기존 데이터 클리어
        for item in self.variables_tree.get_children():
            self.variables_tree.delete(item)
        
        # 테이블 존재 확인
        table_name = self.get_variables_table_name(cursor)
        if not table_name:
            self.insert_no_data_message()
            return
        
        try:
            # 테이블 스키마 확인
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            available_columns = [col[1] for col in columns_info]  # 컬럼명 리스트
            
            # 필수 컬럼 확인 및 쿼리 구성
            select_columns = []
            
            # ID 컬럼 - tv_trading_variables는 variable_id가 PRIMARY KEY
            if "variable_id" in available_columns:
                select_columns.append("variable_id")
            elif "id" in available_columns:
                select_columns.append("id as variable_id")
            else:
                select_columns.append("rowid as variable_id")
            
            # 이름 컬럼 - 새 스키마는 display_name_ko 사용
            if "display_name_ko" in available_columns:
                select_columns.append("display_name_ko")
            elif "korean_name" in available_columns:
                select_columns.append("korean_name")
            elif "name" in available_columns:
                select_columns.append("name")
            elif "variable_name" in available_columns:
                select_columns.append("variable_name")
            else:
                select_columns.append("'Unknown' as display_name")
            
            # 영어 이름 컬럼 - 새 스키마는 display_name_en 사용
            if "display_name_en" in available_columns:
                select_columns.append("display_name_en")
            elif "english_name" in available_columns:
                select_columns.append("english_name")
            else:
                select_columns.append("'N/A' as display_name_en")
            
            # 카테고리 컬럼 (기존 스키마에는 type을 카테고리로 사용)
            if "purpose_category" in available_columns:
                select_columns.append("purpose_category")
            elif "category" in available_columns:
                select_columns.append("category as purpose_category")
            elif "type" in available_columns:
                select_columns.append("type as purpose_category")
            else:
                select_columns.append("'기타' as purpose_category")
            
            # 활성 상태 컬럼 (기존 스키마에는 없을 수 있음)
            if "is_active" in available_columns:
                select_columns.append("is_active")
            else:
                select_columns.append("1 as is_active")
            
            # 설명 컬럼
            if "description" in available_columns:
                select_columns.append("description")
            else:
                select_columns.append("'' as description")
            
            # 필터 조건 구성
            where_conditions = []
            params = []
            
            if self.category_var.get() != "전체":
                if "purpose_category" in available_columns:
                    where_conditions.append("purpose_category = ?")
                elif "category" in available_columns:
                    where_conditions.append("category = ?")
                elif "type" in available_columns:
                    where_conditions.append("type = ?")
                if where_conditions:  # 조건이 추가된 경우에만 파라미터 추가
                    params.append(self.category_var.get())
            
            if self.status_var.get() == "활성" and "is_active" in available_columns:
                where_conditions.append("is_active = 1")
            elif self.status_var.get() == "비활성" and "is_active" in available_columns:
                where_conditions.append("is_active = 0")
            
            where_clause = ""
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
            
            # 동적 쿼리 생성
            order_by = "purpose_category, variable_id"
            if "type" in available_columns and "purpose_category" not in available_columns:
                order_by = "type, variable_id"
            elif "id" in available_columns:
                order_by = order_by.replace("variable_id", "id")
            
            query = f"""
                SELECT {', '.join(select_columns)}
                FROM {table_name}
                {where_clause}
                ORDER BY {order_by}
            """
            
            cursor.execute(query, params)
            variables = cursor.fetchall()
            
            # 카테고리별로 그룹화하여 표시
            categories = {}
            for var in variables:
                var_id = var[0]
                display_name = var[1] if len(var) > 1 else f"Variable_{var_id}"
                english_name = var[2] if len(var) > 2 else "N/A"
                category = var[3] if len(var) > 3 else "기타"
                is_active = var[4] if len(var) > 4 else 1
                description = var[5] if len(var) > 5 else ""
                
                if category not in categories:
                    categories[category] = []
                
                categories[category].append({
                    'id': var_id,
                    'korean_name': display_name,      # 호환성을 위해 유지
                    'display_name_ko': display_name,  # 새 스키마 필드
                    'english_name': english_name,     # 호환성을 위해 유지  
                    'display_name_en': english_name,  # 새 스키마 필드
                    'is_active': is_active,
                    'description': description
                })
            
            # 트리뷰에 데이터 추가
            for category, vars_list in categories.items():
                # 카테고리 노드 생성
                category_node = self.variables_tree.insert(
                    '',
                    'end',
                    text=f"📁 {category.upper()}",
                    values=('', '', category, f"{len(vars_list)}개"),
                    open=True
                )
                
                # 각 변수를 카테고리 하위에 추가
                for var_info in vars_list:
                    status_text = "✅ 활성" if var_info['is_active'] else "❌ 비활성"
                    status_icon = "🟢" if var_info['is_active'] else "🔴"
                    
                    # 새 스키마(display_name_ko)와 기존 스키마(korean_name) 호환
                    korean_name = var_info.get('display_name_ko') or var_info.get('korean_name', 'Unknown')
                    english_name = var_info.get('display_name_en') or var_info.get('english_name', 'N/A')
                    
                    self.variables_tree.insert(
                        category_node,
                        'end',
                        text=f"{status_icon} {korean_name}",
                        values=(
                            var_info['id'],
                            english_name,
                            category,
                            status_text
                        ),
                        tags=(f"var_{var_info['id']}",)
                    )
            
        except sqlite3.Error as e:
            messagebox.showerror(
                "쿼리 실행 실패",
                f"변수 데이터 조회 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def get_variables_table_name(self, cursor):
        """사용 가능한 variables 테이블 이름 반환"""
        # 새 스키마 테이블 우선 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE name = 'tv_trading_variables'")
        if cursor.fetchone():
            return 'tv_trading_variables'
        
        # 레거시 테이블 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE name = 'trading_variables'")
        if cursor.fetchone():
            return 'trading_variables'
        
        return None
    
    def get_parameters_table_name(self, cursor):
        """사용 가능한 parameters 테이블 이름 반환"""
        # 새 스키마 테이블 우선 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE name = 'tv_variable_parameters'")
        if cursor.fetchone():
            return 'tv_variable_parameters'
        
        # 레거시 테이블 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE name = 'variable_parameters'")
        if cursor.fetchone():
            return 'variable_parameters'
        
        return None
    
    def insert_no_data_message(self):
        """데이터 없음 메시지 표시"""
        self.variables_tree.insert(
            '',
            'end',
            text="ℹ️ Trading Variables 테이블이 없습니다",
            values=('', '', '', '마이그레이션 필요'),
        )
    
    def on_variable_selected(self, event):
        """변수 선택 이벤트 처리"""
        selection = self.variables_tree.selection()
        if not selection:
            return
        
        item = self.variables_tree.item(selection[0])
        
        # 변수 ID 추출
        variable_id = item['values'][0] if item['values'] else None
        
        if variable_id:
            self.load_variable_parameters(variable_id)
        else:
            # 카테고리 선택된 경우 파라미터 클리어
            self.clear_parameters()
    
    def load_variable_parameters(self, variable_id):
        """특정 변수의 파라미터 로드"""
        if not self.current_db_path:
            return
        
        # 기존 파라미터 데이터 클리어
        for item in self.parameters_tree.get_children():
            self.parameters_tree.delete(item)
        
        try:
            with sqlite3.connect(self.current_db_path) as conn:
                cursor = conn.cursor()
                
                # 파라미터 테이블 확인
                params_table = self.get_parameters_table_name(cursor)
                
                if not params_table:
                    self.insert_no_parameters_message()
                    return
                
                # 파라미터 테이블 스키마 확인
                cursor.execute(f"PRAGMA table_info({params_table})")
                columns_info = cursor.fetchall()
                available_columns = [col[1] for col in columns_info]
                
                # 동적 쿼리 구성
                select_columns = []
                
                # 파라미터 이름 컬럼
                if "parameter_name" in available_columns:
                    select_columns.append("parameter_name")
                elif "param_name" in available_columns:
                    select_columns.append("param_name as parameter_name")
                elif "name" in available_columns:
                    select_columns.append("name as parameter_name")
                else:
                    select_columns.append("'Unknown' as parameter_name")
                
                # 파라미터 타입 컬럼
                if "parameter_type" in available_columns:
                    select_columns.append("parameter_type")
                elif "param_type" in available_columns:
                    select_columns.append("param_type as parameter_type")
                elif "type" in available_columns:
                    select_columns.append("type as parameter_type")
                else:
                    select_columns.append("'str' as parameter_type")
                
                # 기본값 컬럼
                if "default_value" in available_columns:
                    select_columns.append("default_value")
                elif "default_val" in available_columns:
                    select_columns.append("default_val as default_value")
                elif "value" in available_columns:
                    select_columns.append("value as default_value")
                else:
                    select_columns.append("NULL as default_value")
                
                # 설명 컬럼
                if "description" in available_columns:
                    select_columns.append("description")
                elif "desc" in available_columns:
                    select_columns.append("desc as description")
                else:
                    select_columns.append("'' as description")
                
                # 쿼리 실행 - variable_id를 문자열로 변환하여 매칭
                query = f"""
                    SELECT {', '.join(select_columns)}
                    FROM {params_table}
                    WHERE variable_id = ? OR variable_id = CAST(? AS TEXT)
                    ORDER BY parameter_name
                """
                
                cursor.execute(query, (variable_id, variable_id))
                parameters = cursor.fetchall()
                
                if not parameters:
                    self.insert_no_parameters_message()
                    return
                
                # 파라미터 트리뷰에 데이터 추가
                for param in parameters:
                    param_name = param[0] if len(param) > 0 else "Unknown"
                    param_type = param[1] if len(param) > 1 else "str"
                    default_value = param[2] if len(param) > 2 else None
                    description = param[3] if len(param) > 3 else ""
                    
                    # 타입별 아이콘
                    type_icon = self.get_type_icon(param_type)
                    
                    self.parameters_tree.insert(
                        '',
                        'end',
                        text=f"{type_icon} {param_name}",
                        values=(
                            param_name,
                            param_type,
                            default_value or 'None',
                            description or ''
                        )
                    )
                
        except Exception as e:
            messagebox.showerror(
                "파라미터 로드 실패",
                f"파라미터 데이터 로드 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def get_type_icon(self, param_type):
        """파라미터 타입별 아이콘 반환"""
        type_icons = {
            'int': '🔢',
            'float': '📊',
            'str': '📝',
            'bool': '☑️',
            'list': '📋',
            'dict': '📚'
        }
        return type_icons.get(param_type.lower(), '⚙️')
    
    def insert_no_parameters_message(self):
        """파라미터 없음 메시지 표시"""
        self.parameters_tree.insert(
            '',
            'end',
            text="ℹ️ 파라미터가 없습니다",
            values=('', '', '', '이 변수에는 설정 가능한 파라미터가 없습니다')
        )
    
    def clear_parameters(self):
        """파라미터 목록 클리어"""
        for item in self.parameters_tree.get_children():
            self.parameters_tree.delete(item)
    
    def update_statistics(self, conn):
        """통계 정보 업데이트"""
        cursor = conn.cursor()
        
        stats_lines = []
        
        # 변수 테이블 통계
        vars_table = self.get_variables_table_name(cursor)
        if vars_table:
            try:
                # 전체 변수 수
                cursor.execute(f"SELECT COUNT(*) FROM {vars_table}")
                total_vars = cursor.fetchone()[0]
                
                # 활성 변수 수
                cursor.execute(f"SELECT COUNT(*) FROM {vars_table} WHERE is_active = 1")
                active_vars = cursor.fetchone()[0]
                
                # 카테고리별 분포
                cursor.execute(f"SELECT purpose_category, COUNT(*) FROM {vars_table} GROUP BY purpose_category")
                category_stats = dict(cursor.fetchall())
                
                stats_lines.append(f"📊 변수 통계: 전체 {total_vars}개 (활성 {active_vars}개, 비활성 {total_vars - active_vars}개)")
                stats_lines.append(f"📁 카테고리 분포: {', '.join([f'{k}({v})' for k, v in category_stats.items()])}")
                
            except sqlite3.Error:
                stats_lines.append("❌ 변수 통계 조회 실패")
        
        # 파라미터 테이블 통계
        params_table = self.get_parameters_table_name(cursor)
        if params_table:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {params_table}")
                total_params = cursor.fetchone()[0]
                
                cursor.execute(f"SELECT COUNT(DISTINCT variable_id) FROM {params_table}")
                vars_with_params = cursor.fetchone()[0]
                
                stats_lines.append(f"⚙️ 파라미터 통계: 총 {total_params}개 파라미터 ({vars_with_params}개 변수에 분산)")
                
            except sqlite3.Error:
                stats_lines.append("❌ 파라미터 통계 조회 실패")
        
        if not stats_lines:
            stats_lines.append("ℹ️ 통계 정보를 조회할 수 없습니다. (테이블이 없거나 마이그레이션이 필요)")
        
        # 통계 텍스트 업데이트
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, '\n'.join(stats_lines))
        self.stats_text.config(state='disabled')
    
    def on_category_changed(self, event=None):
        """카테고리 필터 변경 이벤트"""
        self.refresh_data()
    
    def on_status_changed(self, event=None):
        """상태 필터 변경 이벤트"""
        self.refresh_data()
    
    def clear_all_data(self):
        """모든 데이터 클리어"""
        # 변수 트리뷰 클리어
        for item in self.variables_tree.get_children():
            self.variables_tree.delete(item)
        
        # 파라미터 트리뷰 클리어
        self.clear_parameters()
        
        # 통계 정보 클리어
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, "DB가 선택되지 않았습니다.")
        self.stats_text.config(state='disabled')
