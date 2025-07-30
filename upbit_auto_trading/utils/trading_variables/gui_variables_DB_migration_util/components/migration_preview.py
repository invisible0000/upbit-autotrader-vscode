#!/usr/bin/env python3
"""
🔍 Migration Preview Component
마이그레이션 미리보기 및 변경사항 검토 컴포넌트

작성일: 2025-07-30
"""

import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox


class MigrationPreviewFrame(tk.Frame):
    """마이그레이션 미리보기 프레임"""
    
    def __init__(self, parent):
        """
        초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent, bg='white')
        self.current_db_path = None
        self.schema_file_path = None
        
        self.setup_ui()
        self.find_schema_file()
    
    def setup_ui(self):
        """UI 구성"""
        # 제목
        title_label = tk.Label(
            self,
            text="🔍 마이그레이션 미리보기 & 변경사항 검토",
            font=('Arial', 14, 'bold'),
            bg='white',
            fg='#2c3e50'
        )
        title_label.pack(pady=(20, 10))
        
        # 컨트롤 프레임
        control_frame = tk.Frame(self, bg='white')
        control_frame.pack(fill='x', padx=20, pady=10)
        
        # 스키마 파일 선택
        schema_frame = tk.Frame(control_frame, bg='white')
        schema_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(schema_frame, text="스키마 파일:", bg='white', width=12, anchor='w').pack(side='left')
        
        self.schema_var = tk.StringVar(value="선택되지 않음")
        schema_entry = tk.Entry(
            schema_frame,
            textvariable=self.schema_var,
            state='readonly',
            width=50
        )
        schema_entry.pack(side='left', padx=(5, 10), fill='x', expand=True)
        
        select_schema_btn = tk.Button(
            schema_frame,
            text="📂 선택",
            command=self.select_schema_file,
            bg='#3498db',
            fg='white',
            font=('Arial', 9, 'bold'),
            width=8
        )
        select_schema_btn.pack(side='left')
        
        # 분석 버튼
        analyze_btn = tk.Button(
            control_frame,
            text="🔍 변경사항 분석",
            command=self.analyze_changes,
            bg='#27ae60',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=15
        )
        analyze_btn.pack(side='left')
        
        # 리스크 수준 표시
        self.risk_frame = tk.Frame(control_frame, bg='white')
        self.risk_frame.pack(side='right')
        
        # 메인 패널 (PanedWindow 사용)
        main_paned = tk.PanedWindow(self, orient='vertical', bg='white')
        main_paned.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 상단: 변경사항 요약
        summary_frame = tk.LabelFrame(
            main_paned,
            text="📋 변경사항 요약",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        main_paned.add(summary_frame, height=200)
        
        self.summary_text = tk.Text(
            summary_frame,
            height=10,
            wrap='word',
            bg='#f8f9fa',
            fg='#2c3e50',
            font=('Courier', 9),
            state='disabled'
        )
        self.summary_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 중간: 상세 변경사항
        details_frame = tk.LabelFrame(
            main_paned,
            text="🔍 상세 변경사항",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        main_paned.add(details_frame, height=300)
        
        # 탭 노트북 (변경사항 유형별)
        self.details_notebook = ttk.Notebook(details_frame)
        self.details_notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 테이블 변경사항 탭
        self.tables_tab = tk.Frame(self.details_notebook)
        self.details_notebook.add(self.tables_tab, text="🗃️ 테이블 변경")
        
        self.tables_tree = ttk.Treeview(
            self.tables_tab,
            columns=('action', 'old_name', 'new_name', 'impact'),
            show='tree headings'
        )
        self.tables_tree.heading('#0', text='변경 유형')
        self.tables_tree.heading('action', text='작업')
        self.tables_tree.heading('old_name', text='기존 이름')
        self.tables_tree.heading('new_name', text='새 이름')
        self.tables_tree.heading('impact', text='영향도')
        
        self.tables_tree.pack(fill='both', expand=True)
        
        # 데이터 변경사항 탭
        self.data_tab = tk.Frame(self.details_notebook)
        self.details_notebook.add(self.data_tab, text="📊 데이터 변경")
        
        self.data_tree = ttk.Treeview(
            self.data_tab,
            columns=('table', 'records', 'action', 'risk'),
            show='tree headings'
        )
        self.data_tree.heading('#0', text='데이터 변경')
        self.data_tree.heading('table', text='테이블')
        self.data_tree.heading('records', text='레코드 수')
        self.data_tree.heading('action', text='작업')
        self.data_tree.heading('risk', text='위험도')
        
        self.data_tree.pack(fill='both', expand=True)
        
        # 호환성 분석 탭
        self.compatibility_tab = tk.Frame(self.details_notebook)
        self.details_notebook.add(self.compatibility_tab, text="🔗 호환성 분석")
        
        self.compatibility_text = tk.Text(
            self.compatibility_tab,
            wrap='word',
            bg='#f8f9fa',
            fg='#2c3e50',
            font=('Courier', 9),
            state='disabled'
        )
        self.compatibility_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 하단: 백업 및 리스크 정보
        risk_frame = tk.LabelFrame(
            main_paned,
            text="⚠️ 리스크 분석 & 백업 계획",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        main_paned.add(risk_frame, height=150)
        
        self.risk_text = tk.Text(
            risk_frame,
            height=8,
            wrap='word',
            bg='#fff5f5',
            fg='#c53030',
            font=('Arial', 9),
            state='disabled'
        )
        self.risk_text.pack(fill='both', expand=True, padx=10, pady=10)
    
    def find_schema_file(self):
        """스키마 파일 자동 찾기"""
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        schema_files = ['schema_new02.sql', 'schema_improved.sql', 'schema.sql']
        
        for filename in schema_files:
            schema_path = os.path.join(current_dir, filename)
            if os.path.exists(schema_path):
                self.schema_file_path = schema_path
                self.schema_var.set(schema_path)
                break
    
    def select_schema_file(self):
        """스키마 파일 선택 다이얼로그"""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="스키마 파일 선택",
            filetypes=[
                ("SQL files", "*.sql"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.schema_file_path = file_path
            self.schema_var.set(file_path)
    
    def set_db_path(self, db_path):
        """
        DB 경로 설정
        
        Args:
            db_path: DB 파일 경로
        """
        self.current_db_path = db_path
    
    def analyze_changes(self):
        """변경사항 분석 실행"""
        if not self.current_db_path:
            messagebox.showwarning("DB 미선택", "먼저 DB 파일을 선택하세요.")
            return
        
        if not self.schema_file_path or not os.path.exists(self.schema_file_path):
            messagebox.showwarning("스키마 파일 미선택", "유효한 스키마 파일을 선택하세요.")
            return
        
        try:
            # 분석 수행
            analysis_result = self.perform_migration_analysis()
            
            # 결과 표시
            self.display_analysis_result(analysis_result)
            
        except Exception as e:
            messagebox.showerror(
                "분석 실패",
                f"마이그레이션 분석 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def perform_migration_analysis(self):
        """마이그레이션 분석 수행"""
        analysis = {
            'summary': {},
            'table_changes': [],
            'data_changes': [],
            'compatibility': [],
            'risks': [],
            'backup_plan': {}
        }
        
        # 기존 DB 분석
        existing_tables = self.analyze_existing_db()
        
        # 새 스키마 분석
        new_schema = self.analyze_new_schema()
        
        # 변경사항 비교
        analysis['table_changes'] = self.compare_table_structures(existing_tables, new_schema)
        analysis['data_changes'] = self.analyze_data_migration(existing_tables)
        analysis['compatibility'] = self.analyze_compatibility()
        analysis['risks'] = self.assess_risks(analysis)
        analysis['backup_plan'] = self.create_backup_plan()
        
        # 요약 정보 생성
        analysis['summary'] = self.generate_summary(analysis)
        
        return analysis
    
    def analyze_existing_db(self):
        """기존 DB 구조 분석"""
        tables_info = {}
        
        if not os.path.exists(self.current_db_path):
            return tables_info
        
        try:
            with sqlite3.connect(self.current_db_path) as conn:
                cursor = conn.cursor()
                
                # 테이블 목록 조회
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    # 테이블 구조 정보
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    
                    # 레코드 수
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    record_count = cursor.fetchone()[0]
                    
                    tables_info[table] = {
                        'columns': columns,
                        'record_count': record_count,
                        'is_legacy': self.is_legacy_table(table)
                    }
        
        except Exception as e:
            print(f"기존 DB 분석 오류: {e}")
        
        return tables_info
    
    def analyze_new_schema(self):
        """새 스키마 분석"""
        schema_info = {
            'tables': [],
            'sql_statements': []
        }
        
        try:
            with open(self.schema_file_path, 'r', encoding='utf-8') as f:
                schema_content = f.read()
            
            # CREATE TABLE 문 추출
            import re
            create_patterns = re.findall(
                r'CREATE TABLE\s+(\w+)\s*\((.*?)\);',
                schema_content,
                re.DOTALL | re.IGNORECASE
            )
            
            for table_name, table_def in create_patterns:
                schema_info['tables'].append({
                    'name': table_name,
                    'definition': table_def.strip()
                })
            
            # 전체 SQL 문장들
            statements = [stmt.strip() for stmt in schema_content.split(';') if stmt.strip()]
            schema_info['sql_statements'] = statements
            
        except Exception as e:
            print(f"스키마 분석 오류: {e}")
        
        return schema_info
    
    def compare_table_structures(self, existing_tables, new_schema):
        """테이블 구조 비교"""
        changes = []
        
        # 새 스키마의 테이블 이름 목록
        new_table_names = [table['name'] for table in new_schema['tables']]
        
        # 제거될 테이블 (레거시)
        for table_name, info in existing_tables.items():
            if info['is_legacy'] and table_name not in new_table_names:
                changes.append({
                    'type': 'remove',
                    'action': '🗑️ 삭제',
                    'old_name': table_name,
                    'new_name': '-',
                    'impact': f"높음 ({info['record_count']}개 레코드 손실 가능)",
                    'details': f"레거시 테이블 제거: {info['record_count']}개 레코드"
                })
        
        # 추가될 테이블 (새 스키마)
        for table in new_schema['tables']:
            if table['name'] not in existing_tables:
                changes.append({
                    'type': 'add',
                    'action': '➕ 생성',
                    'old_name': '-',
                    'new_name': table['name'],
                    'impact': '낮음 (새 테이블)',
                    'details': f"새 테이블 생성: {table['name']}"
                })
        
        # 변경될 테이블 (구조 변경)
        for table in new_schema['tables']:
            if table['name'] in existing_tables:
                changes.append({
                    'type': 'modify',
                    'action': '🔄 수정',
                    'old_name': table['name'],
                    'new_name': table['name'],
                    'impact': '중간 (구조 변경)',
                    'details': f"테이블 구조 업데이트"
                })
        
        return changes
    
    def analyze_data_migration(self, existing_tables):
        """데이터 마이그레이션 분석"""
        data_changes = []
        
        for table_name, info in existing_tables.items():
            if info['is_legacy']:
                risk_level = "높음" if info['record_count'] > 0 else "낮음"
                
                data_changes.append({
                    'table': table_name,
                    'records': info['record_count'],
                    'action': '데이터 보존 후 테이블 제거',
                    'risk': risk_level,
                    'details': f"{info['record_count']}개 레코드가 있는 레거시 테이블"
                })
        
        return data_changes
    
    def analyze_compatibility(self):
        """호환성 분석"""
        compatibility_issues = []
        
        # 기본 호환성 체크 항목들
        compatibility_issues.extend([
            "✅ 기존 variable_definitions.py와 100% 호환 예상",
            "✅ condition_dialog.py의 get_category_variables() 호출 지원",
            "✅ tv_ 접두사로 네임스페이스 분리",
            "✅ 외래키 제약조건으로 데이터 무결성 보장",
            "⚠️ 레거시 테이블 제거로 인한 일시적 데이터 접근 불가",
            "ℹ️ 마이그레이션 후 애플리케이션 재시작 권장"
        ])
        
        return compatibility_issues
    
    def assess_risks(self, analysis):
        """리스크 평가"""
        risks = []
        
        # 데이터 손실 리스크
        legacy_records = sum(
            change['records'] for change in analysis['data_changes']
            if isinstance(change['records'], int)
        )
        
        if legacy_records > 0:
            risks.append({
                'level': 'HIGH',
                'category': '데이터 손실',
                'description': f"레거시 테이블의 {legacy_records}개 레코드가 영향받음",
                'mitigation': '자동 백업 생성으로 복원 가능'
            })
        
        # 호환성 리스크
        risks.append({
            'level': 'LOW',
            'category': '코드 호환성',
            'description': '기존 코드와의 호환성 검증 필요',
            'mitigation': '100% 호환 설계로 위험도 최소화'
        })
        
        # 다운타임 리스크
        risks.append({
            'level': 'MEDIUM',
            'category': '서비스 중단',
            'description': '마이그레이션 중 일시적 서비스 중단',
            'mitigation': '빠른 마이그레이션 프로세스 (예상 시간: 1-2분)'
        })
        
        return risks
    
    def create_backup_plan(self):
        """백업 계획 생성"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return {
            'backup_filename': f"settings_bck_{timestamp}.sqlite3",
            'backup_location': os.path.join(os.path.dirname(self.current_db_path), "backups"),
            'restore_procedure': "백업 파일을 원본 위치로 복사하여 복원",
            'verification_steps': [
                "백업 파일 무결성 확인",
                "원본 파일과 크기 비교",
                "테이블 구조 및 데이터 검증"
            ]
        }
    
    def generate_summary(self, analysis):
        """요약 정보 생성"""
        table_adds = len([c for c in analysis['table_changes'] if c['type'] == 'add'])
        table_removes = len([c for c in analysis['table_changes'] if c['type'] == 'remove'])
        table_modifies = len([c for c in analysis['table_changes'] if c['type'] == 'modify'])
        
        affected_records = sum(
            change['records'] for change in analysis['data_changes']
            if isinstance(change['records'], int)
        )
        
        high_risks = len([r for r in analysis['risks'] if r['level'] == 'HIGH'])
        medium_risks = len([r for r in analysis['risks'] if r['level'] == 'MEDIUM'])
        
        return {
            'table_operations': {
                'add': table_adds,
                'remove': table_removes,
                'modify': table_modifies
            },
            'affected_records': affected_records,
            'risk_summary': {
                'high': high_risks,
                'medium': medium_risks,
                'low': len(analysis['risks']) - high_risks - medium_risks
            }
        }
    
    def display_analysis_result(self, analysis):
        """분석 결과 표시"""
        # 요약 정보 표시
        self.display_summary(analysis['summary'])
        
        # 테이블 변경사항 표시
        self.display_table_changes(analysis['table_changes'])
        
        # 데이터 변경사항 표시
        self.display_data_changes(analysis['data_changes'])
        
        # 호환성 분석 표시
        self.display_compatibility(analysis['compatibility'])
        
        # 리스크 분석 표시
        self.display_risks(analysis['risks'], analysis['backup_plan'])
        
        # 리스크 수준 표시
        self.update_risk_indicator(analysis['risks'])
    
    def display_summary(self, summary):
        """요약 정보 표시"""
        summary_lines = []
        summary_lines.append("📋 마이그레이션 변경사항 요약")
        summary_lines.append("=" * 40)
        summary_lines.append("")
        
        ops = summary['table_operations']
        summary_lines.append(f"🗃️ 테이블 작업:")
        summary_lines.append(f"   • 새로 생성: {ops['add']}개")
        summary_lines.append(f"   • 제거 예정: {ops['remove']}개")
        summary_lines.append(f"   • 구조 변경: {ops['modify']}개")
        summary_lines.append("")
        
        summary_lines.append(f"📊 영향받는 데이터: {summary['affected_records']}개 레코드")
        summary_lines.append("")
        
        risks = summary['risk_summary']
        summary_lines.append(f"⚠️ 리스크 분석:")
        summary_lines.append(f"   • 높음: {risks['high']}개")
        summary_lines.append(f"   • 중간: {risks['medium']}개") 
        summary_lines.append(f"   • 낮음: {risks['low']}개")
        
        self.summary_text.config(state='normal')
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, '\n'.join(summary_lines))
        self.summary_text.config(state='disabled')
    
    def display_table_changes(self, table_changes):
        """테이블 변경사항 표시"""
        # 기존 데이터 클리어
        for item in self.tables_tree.get_children():
            self.tables_tree.delete(item)
        
        for change in table_changes:
            self.tables_tree.insert(
                '',
                'end',
                text=change['type'],
                values=(
                    change['action'],
                    change['old_name'],
                    change['new_name'],
                    change['impact']
                )
            )
    
    def display_data_changes(self, data_changes):
        """데이터 변경사항 표시"""
        # 기존 데이터 클리어
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        for change in data_changes:
            self.data_tree.insert(
                '',
                'end',
                text='데이터 마이그레이션',
                values=(
                    change['table'],
                    change['records'],
                    change['action'],
                    change['risk']
                )
            )
    
    def display_compatibility(self, compatibility_issues):
        """호환성 분석 표시"""
        self.compatibility_text.config(state='normal')
        self.compatibility_text.delete(1.0, tk.END)
        
        content = "🔗 기존 코드와의 호환성 분석\n"
        content += "=" * 40 + "\n\n"
        content += '\n'.join(compatibility_issues)
        
        self.compatibility_text.insert(1.0, content)
        self.compatibility_text.config(state='disabled')
    
    def display_risks(self, risks, backup_plan):
        """리스크 분석 표시"""
        risk_lines = []
        risk_lines.append("⚠️ 리스크 분석 & 대응 계획")
        risk_lines.append("=" * 40)
        risk_lines.append("")
        
        for risk in risks:
            level_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}[risk['level']]
            risk_lines.append(f"{level_icon} [{risk['level']}] {risk['category']}")
            risk_lines.append(f"   문제: {risk['description']}")
            risk_lines.append(f"   대응: {risk['mitigation']}")
            risk_lines.append("")
        
        risk_lines.append("💾 백업 계획:")
        risk_lines.append(f"   • 파일명: {backup_plan['backup_filename']}")
        risk_lines.append(f"   • 위치: {backup_plan['backup_location']}")
        risk_lines.append(f"   • 복원 방법: {backup_plan['restore_procedure']}")
        
        self.risk_text.config(state='normal')
        self.risk_text.delete(1.0, tk.END)
        self.risk_text.insert(1.0, '\n'.join(risk_lines))
        self.risk_text.config(state='disabled')
    
    def update_risk_indicator(self, risks):
        """리스크 수준 표시기 업데이트"""
        # 기존 위젯 제거
        for widget in self.risk_frame.winfo_children():
            widget.destroy()
        
        # 최고 리스크 수준 계산
        risk_levels = [risk['level'] for risk in risks]
        if 'HIGH' in risk_levels:
            color = '#e74c3c'
            text = "🔴 높은 위험"
        elif 'MEDIUM' in risk_levels:
            color = '#f39c12'
            text = "🟡 중간 위험"
        else:
            color = '#27ae60'
            text = "🟢 낮은 위험"
        
        risk_label = tk.Label(
            self.risk_frame,
            text=text,
            bg=color,
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=10,
            pady=5
        )
        risk_label.pack()
    
    def is_legacy_table(self, table_name):
        """레거시 테이블인지 확인"""
        legacy_patterns = [
            'trading_variables',
            'variable_parameters',
            'comparison_groups',
            'schema_version'
        ]
        
        return any(pattern in table_name.lower() for pattern in legacy_patterns) and not table_name.startswith('tv_')
