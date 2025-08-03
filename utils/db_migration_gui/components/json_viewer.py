#!/usr/bin/env python3
"""
📋 JSON Data Viewer Component
DB 데이터를 JSON 형식으로 구조화하여 표시

작성일: 2025-07-30
"""

import os
import sqlite3
import tkinter as tk
from tkinter import ttk, scrolledtext
import json
from datetime import datetime


class JsonViewerFrame(tk.Frame):
    """JSON 데이터 뷰어 프레임"""
    
    def __init__(self, parent):
        super().__init__(parent, bg='white')
        self.current_db_path = None
        self.setup_ui()
    
    def setup_ui(self):
        """UI 설정"""
        # 상단 제어 패널
        control_frame = tk.Frame(self, bg='white')
        control_frame.pack(fill='x', padx=20, pady=10)
        
        # 제목
        title_label = tk.Label(
            control_frame,
            text="📋 JSON 데이터 뷰어",
            font=('Arial', 14, 'bold'),
            bg='white'
        )
        title_label.pack(side='left')
        
        # 버튼들
        button_frame = tk.Frame(control_frame, bg='white')
        button_frame.pack(side='right')
        
        # 새로고침 버튼
        refresh_btn = tk.Button(
            button_frame,
            text="🔄 새로고침",
            command=self.refresh_data,
            bg='#3498db',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        refresh_btn.pack(side='right')
        
        # 복사 버튼
        copy_btn = tk.Button(
            button_frame,
            text="📋 JSON 복사",
            command=self.copy_json,
            bg='#27ae60',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        copy_btn.pack(side='right', padx=(0, 10))
        
        # 내보내기 버튼
        export_btn = tk.Button(
            button_frame,
            text="💾 JSON 파일로 저장",
            command=self.export_json,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        export_btn.pack(side='right', padx=(0, 10))
        
        # 데이터 타입 선택
        type_frame = tk.Frame(self, bg='white')
        type_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        tk.Label(type_frame, text="데이터 타입:", bg='white', font=('Arial', 10, 'bold')).pack(side='left')
        
        self.data_type = tk.StringVar(value="full")
        
        data_types = [
            ("전체 데이터", "full"),
            ("변수만", "variables"),
            ("파라미터만", "parameters"),
            ("요약 정보", "summary")
        ]
        
        for text, value in data_types:
            rb = tk.Radiobutton(
                type_frame,
                text=text,
                variable=self.data_type,
                value=value,
                command=self.refresh_data,
                bg='white',
                font=('Arial', 9)
            )
            rb.pack(side='left', padx=(10, 0))
        
        # 메인 JSON 표시 영역
        self.json_text = scrolledtext.ScrolledText(
            self,
            wrap='none',
            font=('Courier', 10),
            bg='#f8f9fa',
            fg='#2c3e50'
        )
        self.json_text.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # 초기 메시지
        self.display_welcome_message()
    
    def set_db_path(self, db_path):
        """DB 경로 설정 및 데이터 업데이트"""
        self.current_db_path = db_path
        self.refresh_data()
    
    def refresh_data(self):
        """데이터 새로고침"""
        if not self.current_db_path:
            self.display_welcome_message()
            return
        
        try:
            data_type = self.data_type.get()
            json_data = self.generate_json_data(data_type)
            self.display_json(json_data)
        except Exception as e:
            self.display_error(f"JSON 생성 중 오류: {e}")
    
    def generate_json_data(self, data_type):
        """지정된 타입의 JSON 데이터 생성"""
        if not self.current_db_path or not os.path.exists(self.current_db_path):
            return {"error": "DB 파일이 선택되지 않았거나 존재하지 않습니다."}
        
        with sqlite3.connect(self.current_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if data_type == "full":
                return self._generate_full_data(cursor)
            elif data_type == "variables":
                return self._generate_variables_only(cursor)
            elif data_type == "parameters":
                return self._generate_parameters_only(cursor)
            elif data_type == "summary":
                return self._generate_summary_data(cursor)
    
    def _generate_full_data(self, cursor):
        """전체 데이터 JSON 생성"""
        data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "db_path": self.current_db_path,
                "schema_version": None
            },
            "variables": {},
            "parameters": {},
            "statistics": {}
        }
        
        # 스키마 버전 확인
        try:
            cursor.execute("SELECT version FROM tv_schema_version ORDER BY applied_at DESC LIMIT 1")
            version_row = cursor.fetchone()
            if version_row:
                data["metadata"]["schema_version"] = version_row[0]
        except:
            pass
        
        # 변수 데이터
        try:
            cursor.execute("SELECT * FROM tv_trading_variables ORDER BY variable_id")
            variables = cursor.fetchall()
            for var in variables:
                var_dict = dict(var)
                data["variables"][var["variable_id"]] = var_dict
        except Exception as e:
            data["variables"] = {"error": str(e)}
        
        # 파라미터 데이터
        try:
            cursor.execute("SELECT * FROM tv_variable_parameters ORDER BY variable_id, display_order")
            parameters = cursor.fetchall()
            for param in parameters:
                var_id = param["variable_id"]
                if var_id not in data["parameters"]:
                    data["parameters"][var_id] = []
                data["parameters"][var_id].append(dict(param))
        except Exception as e:
            data["parameters"] = {"error": str(e)}
        
        # 통계 정보
        data["statistics"] = self._generate_statistics(cursor)
        
        return data
    
    def _generate_variables_only(self, cursor):
        """변수만 JSON 생성"""
        data = {
            "variables": {},
            "generated_at": datetime.now().isoformat()
        }
        
        try:
            cursor.execute("SELECT * FROM tv_trading_variables ORDER BY variable_id")
            variables = cursor.fetchall()
            for var in variables:
                data["variables"][var["variable_id"]] = dict(var)
        except Exception as e:
            data["error"] = str(e)
        
        return data
    
    def _generate_parameters_only(self, cursor):
        """파라미터만 JSON 생성"""
        data = {
            "parameters": {},
            "generated_at": datetime.now().isoformat()
        }
        
        try:
            cursor.execute("SELECT * FROM tv_variable_parameters ORDER BY variable_id, display_order")
            parameters = cursor.fetchall()
            for param in parameters:
                var_id = param["variable_id"]
                if var_id not in data["parameters"]:
                    data["parameters"][var_id] = []
                data["parameters"][var_id].append(dict(param))
        except Exception as e:
            data["error"] = str(e)
        
        return data
    
    def _generate_summary_data(self, cursor):
        """요약 정보 JSON 생성"""
        data = {
            "summary": {
                "generated_at": datetime.now().isoformat(),
                "total_variables": 0,
                "total_parameters": 0,
                "variables_by_category": {},
                "variables_by_chart_type": {},
                "parameters_by_type": {},
                "top_variables_by_param_count": []
            }
        }
        
        try:
            # 전체 변수 수
            cursor.execute("SELECT COUNT(*) FROM tv_trading_variables")
            data["summary"]["total_variables"] = cursor.fetchone()[0]
            
            # 전체 파라미터 수
            cursor.execute("SELECT COUNT(*) FROM tv_variable_parameters")
            data["summary"]["total_parameters"] = cursor.fetchone()[0]
            
            # 카테고리별 변수 수
            cursor.execute("SELECT purpose_category, COUNT(*) FROM tv_trading_variables GROUP BY purpose_category")
            for row in cursor.fetchall():
                data["summary"]["variables_by_category"][row[0]] = row[1]
            
            # 차트 타입별 변수 수
            cursor.execute("SELECT chart_category, COUNT(*) FROM tv_trading_variables GROUP BY chart_category")
            for row in cursor.fetchall():
                data["summary"]["variables_by_chart_type"][row[0]] = row[1]
            
            # 파라미터 타입별 수
            cursor.execute("SELECT parameter_type, COUNT(*) FROM tv_variable_parameters GROUP BY parameter_type")
            for row in cursor.fetchall():
                data["summary"]["parameters_by_type"][row[0]] = row[1]
            
            # 파라미터가 많은 변수 TOP 10
            cursor.execute("""
                SELECT variable_id, COUNT(*) as param_count 
                FROM tv_variable_parameters 
                GROUP BY variable_id 
                ORDER BY param_count DESC 
                LIMIT 10
            """)
            for row in cursor.fetchall():
                data["summary"]["top_variables_by_param_count"].append({
                    "variable_id": row[0],
                    "parameter_count": row[1]
                })
        
        except Exception as e:
            data["error"] = str(e)
        
        return data
    
    def _generate_statistics(self, cursor):
        """통계 정보 생성"""
        stats = {}
        
        try:
            # 기본 통계
            cursor.execute("SELECT COUNT(*) FROM tv_trading_variables")
            stats["total_variables"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tv_variable_parameters")
            stats["total_parameters"] = cursor.fetchone()[0]
            
            # 카테고리별 통계
            cursor.execute("SELECT purpose_category, COUNT(*) FROM tv_trading_variables GROUP BY purpose_category")
            stats["by_category"] = dict(cursor.fetchall())
            
        except Exception as e:
            stats["error"] = str(e)
        
        return stats
    
    def display_welcome_message(self):
        """환영 메시지 표시"""
        welcome = {
            "message": "JSON 데이터 뷰어에 오신 것을 환영합니다!",
            "instructions": [
                "1. 먼저 DB를 선택하세요",
                "2. 원하는 데이터 타입을 선택하세요",
                "3. 새로고침 버튼을 클릭하세요",
                "4. JSON 데이터를 확인하고 복사/저장하세요"
            ],
            "data_types": {
                "full": "모든 변수와 파라미터 데이터",
                "variables": "변수 정보만",
                "parameters": "파라미터 정보만",
                "summary": "요약 통계"
            }
        }
        self.display_json(welcome)
    
    def display_json(self, data):
        """JSON 데이터 표시"""
        try:
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            self.json_text.delete(1.0, 'end')
            self.json_text.insert(1.0, json_str)
        except Exception as e:
            self.display_error(f"JSON 변환 오류: {e}")
    
    def display_error(self, error_msg):
        """오류 메시지 표시"""
        error_data = {
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        self.display_json(error_data)
    
    def copy_json(self):
        """JSON을 클립보드에 복사"""
        content = self.json_text.get(1.0, 'end-1c')
        self.clipboard_clear()
        self.clipboard_append(content)
        
        import tkinter.messagebox as msgbox
        msgbox.showinfo("복사 완료", "JSON 데이터가 클립보드에 복사되었습니다!")
    
    def export_json(self):
        """JSON을 파일로 저장"""
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            title="JSON 파일로 저장",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                content = self.json_text.get(1.0, 'end-1c')
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                import tkinter.messagebox as msgbox
                msgbox.showinfo("저장 완료", f"JSON 파일이 저장되었습니다:\n{file_path}")
            except Exception as e:
                import tkinter.messagebox as msgbox
                msgbox.showerror("저장 실패", f"파일 저장 중 오류가 발생했습니다:\n{e}")
