#!/usr/bin/env python3
"""
🤖 AI Agent Info Component
에이전트가 현재 상황을 이해할 수 있는 정보 요약 제공

작성일: 2025-07-30
"""

import os
import sqlite3
import tkinter as tk
from tkinter import ttk, scrolledtext
import json
from datetime import datetime


class AgentInfoFrame(tk.Frame):
    """AI 에이전트 정보 요약 프레임"""
    
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
            text="🤖 AI 에이전트 컨텍스트 정보",
            font=('Arial', 14, 'bold'),
            bg='white'
        )
        title_label.pack(side='left')
        
        # 새로고침 버튼
        refresh_btn = tk.Button(
            control_frame,
            text="🔄 새로고침",
            command=self.refresh_info,
            bg='#3498db',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        refresh_btn.pack(side='right')
        
        # 복사 버튼
        copy_btn = tk.Button(
            control_frame,
            text="📋 클립보드에 복사",
            command=self.copy_to_clipboard,
            bg='#27ae60',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        copy_btn.pack(side='right', padx=(0, 10))
        
        # 메인 정보 영역
        self.info_text = scrolledtext.ScrolledText(
            self,
            wrap='word',
            font=('Courier', 10),
            bg='#f8f9fa',
            fg='#2c3e50'
        )
        self.info_text.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # 초기 메시지
        self.display_welcome_message()
    
    def set_db_path(self, db_path):
        """DB 경로 설정 및 정보 업데이트"""
        self.current_db_path = db_path
        self.refresh_info()
    
    def refresh_info(self):
        """정보 새로고침"""
        if not self.current_db_path:
            self.display_welcome_message()
            return
        
        try:
            info = self.generate_agent_context()
            self.display_info(info)
        except Exception as e:
            self.display_error(f"정보 생성 중 오류: {e}")
    
    def generate_agent_context(self):
        """에이전트를 위한 컨텍스트 정보 생성"""
        if not self.current_db_path or not os.path.exists(self.current_db_path):
            return "❌ DB 파일이 선택되지 않았거나 존재하지 않습니다."
        
        context = []
        context.append("=" * 80)
        context.append("🤖 TRADING VARIABLES DB - AI AGENT CONTEXT")
        context.append("=" * 80)
        context.append(f"⏰ 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        context.append(f"📁 DB 파일: {self.current_db_path}")
        context.append("")
        
        try:
            with sqlite3.connect(self.current_db_path) as conn:
                cursor = conn.cursor()
                
                # 1. 전체 테이블 목록
                context.append("📋 전체 테이블 목록:")
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = cursor.fetchall()
                for table in tables:
                    context.append(f"  - {table[0]}")
                context.append(f"  총 {len(tables)}개 테이블")
                context.append("")
                
                # 2. Trading Variables 관련 테이블
                context.append("🎯 Trading Variables 관련 테이블:")
                tv_tables = [t[0] for t in tables if 'variable' in t[0].lower() or t[0].startswith('tv_')]
                for table in tv_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    context.append(f"  - {table}: {count}개 레코드")
                context.append("")
                
                # 3. tv_trading_variables 상세 정보
                if 'tv_trading_variables' in [t[0] for t in tables]:
                    context.append("📊 tv_trading_variables 상세:")
                    cursor.execute("SELECT purpose_category, COUNT(*) FROM tv_trading_variables GROUP BY purpose_category")
                    categories = cursor.fetchall()
                    for category, count in categories:
                        context.append(f"  - {category}: {count}개 변수")
                    
                    cursor.execute("SELECT chart_category, COUNT(*) FROM tv_trading_variables GROUP BY chart_category")
                    chart_types = cursor.fetchall()
                    context.append("  차트 위치별:")
                    for chart_type, count in chart_types:
                        context.append(f"    - {chart_type}: {count}개")
                    context.append("")
                
                # 4. tv_variable_parameters 상세 정보
                if 'tv_variable_parameters' in [t[0] for t in tables]:
                    context.append("⚙️ tv_variable_parameters 상세:")
                    cursor.execute("SELECT COUNT(*) FROM tv_variable_parameters")
                    total_params = cursor.fetchone()[0]
                    context.append(f"  - 총 파라미터: {total_params}개")
                    
                    cursor.execute("SELECT variable_id, COUNT(*) FROM tv_variable_parameters GROUP BY variable_id ORDER BY COUNT(*) DESC LIMIT 10")
                    top_vars = cursor.fetchall()
                    context.append("  파라미터가 많은 변수 TOP 10:")
                    for var_id, count in top_vars:
                        context.append(f"    - {var_id}: {count}개 파라미터")
                    context.append("")
                
                # 5. SMA 변수 상세 (예시)
                context.append("🔍 SMA 변수 예시 (상세):")
                cursor.execute("SELECT * FROM tv_trading_variables WHERE variable_id = 'SMA'")
                sma_var = cursor.fetchone()
                if sma_var:
                    cursor.execute("PRAGMA table_info(tv_trading_variables)")
                    columns = [col[1] for col in cursor.fetchall()]
                    for i, value in enumerate(sma_var):
                        context.append(f"  - {columns[i]}: {value}")
                    
                    cursor.execute("SELECT * FROM tv_variable_parameters WHERE variable_id = 'SMA' ORDER BY display_order")
                    sma_params = cursor.fetchall()
                    context.append(f"  SMA 파라미터 ({len(sma_params)}개):")
                    for param in sma_params:
                        context.append(f"    - {param[2]} ({param[3]}): {param[4]} [{param[9]}]")
                else:
                    context.append("  ❌ SMA 변수를 찾을 수 없음")
                context.append("")
                
                # 6. 스키마 정보
                context.append("🏗️ 스키마 정보:")
                cursor.execute("SELECT version, applied_at, description FROM tv_schema_version ORDER BY applied_at DESC LIMIT 1")
                schema_info = cursor.fetchone()
                if schema_info:
                    context.append(f"  - 현재 스키마 버전: {schema_info[0]}")
                    context.append(f"  - 적용 시간: {schema_info[1]}")
                    context.append(f"  - 설명: {schema_info[2]}")
                else:
                    context.append("  ❌ 스키마 버전 정보 없음")
                context.append("")
                
                # 7. 문제 진단
                context.append("🔧 자동 진단 결과:")
                issues = []
                
                # tv_variable_parameters 테이블 존재 확인
                if 'tv_variable_parameters' not in [t[0] for t in tables]:
                    issues.append("❌ tv_variable_parameters 테이블이 없음 - 마이그레이션 필요")
                else:
                    cursor.execute("SELECT COUNT(*) FROM tv_variable_parameters")
                    param_count = cursor.fetchone()[0]
                    if param_count == 0:
                        issues.append("⚠️ tv_variable_parameters 테이블이 비어있음")
                    else:
                        issues.append(f"✅ tv_variable_parameters 테이블 정상 ({param_count}개 파라미터)")
                
                # SMA 파라미터 확인
                if 'tv_variable_parameters' in [t[0] for t in tables]:
                    cursor.execute("SELECT COUNT(*) FROM tv_variable_parameters WHERE variable_id = 'SMA'")
                    sma_param_count = cursor.fetchone()[0]
                    if sma_param_count == 0:
                        issues.append("❌ SMA 파라미터가 없음")
                    else:
                        issues.append(f"✅ SMA 파라미터 정상 ({sma_param_count}개)")
                
                for issue in issues:
                    context.append(f"  {issue}")
                
        except Exception as e:
            context.append(f"❌ DB 분석 중 오류: {e}")
        
        context.append("")
        context.append("=" * 80)
        context.append("🎯 에이전트 액션 가이드:")
        context.append("1. 위 정보를 바탕으로 현재 DB 상태를 파악하세요")
        context.append("2. 문제가 있다면 마이그레이션 실행 탭에서 해결하세요")
        context.append("3. 변수 & 파라미터 조회 탭에서 실제 데이터를 확인하세요")
        context.append("4. 필요시 JSON 데이터 뷰어로 구조화된 데이터를 확인하세요")
        context.append("=" * 80)
        
        return "\n".join(context)
    
    def display_welcome_message(self):
        """환영 메시지 표시"""
        welcome = """
🤖 AI 에이전트 컨텍스트 정보

이 탭은 AI 에이전트가 현재 Trading Variables DB 상태를 빠르게 이해할 수 있도록 
핵심 정보를 요약하여 제공합니다.

사용법:
1. 먼저 'DB 선택 & 현재 상태' 탭에서 DB를 선택하세요
2. 이 탭에서 '새로고침' 버튼을 클릭하세요
3. 생성된 정보를 '클립보드에 복사' 버튼으로 복사하세요
4. AI 에이전트에게 복사한 정보를 전달하세요

💡 에이전트는 이 정보만으로 현재 상황을 정확히 파악할 수 있습니다!
        """
        self.display_info(welcome)
    
    def display_info(self, info):
        """정보 표시"""
        self.info_text.delete(1.0, 'end')
        self.info_text.insert(1.0, info)
    
    def display_error(self, error_msg):
        """오류 메시지 표시"""
        self.display_info(f"❌ 오류 발생:\n{error_msg}")
    
    def copy_to_clipboard(self):
        """클립보드에 복사"""
        content = self.info_text.get(1.0, 'end-1c')
        self.clipboard_clear()
        self.clipboard_append(content)
        
        # 피드백 메시지
        import tkinter.messagebox as msgbox
        msgbox.showinfo("복사 완료", "에이전트 컨텍스트 정보가 클립보드에 복사되었습니다!")
