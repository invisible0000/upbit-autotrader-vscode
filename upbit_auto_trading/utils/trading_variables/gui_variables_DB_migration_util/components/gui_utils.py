#!/usr/bin/env python3
"""
🎨 GUI 공통 유틸리티 모듈
========================

Trading Variables DB Migration Tool을 위한 공통 GUI 컴포넌트 및 유틸리티

주요 기능:
1. 표준화된 위젯 스타일
2. 공통 레이아웃 패턴
3. 에러 처리 및 메시지 표시
4. 성능 최적화 헬퍼

작성일: 2025-07-31
버전: 1.0.0 (Phase 3 - GUI 프레임워크 표준화)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, Dict, Any
import threading
import functools


class GUIStyles:
    """GUI 스타일 상수 클래스"""
    
    # 색상 팔레트
    PRIMARY_COLOR = '#3498db'      # 파란색 (주요 버튼)
    SUCCESS_COLOR = '#27ae60'      # 초록색 (성공/확인)
    WARNING_COLOR = '#f39c12'      # 주황색 (경고)
    DANGER_COLOR = '#e74c3c'       # 빨간색 (위험/삭제)
    SECONDARY_COLOR = '#95a5a6'    # 회색 (보조 버튼)
    
    BACKGROUND_COLOR = '#f8f9fa'   # 배경색
    SURFACE_COLOR = '#ffffff'      # 카드/패널 배경
    TEXT_COLOR = '#2c3e50'         # 주요 텍스트
    MUTED_COLOR = '#7f8c8d'        # 보조 텍스트
    
    # 폰트
    TITLE_FONT = ('Arial', 14, 'bold')
    HEADING_FONT = ('Arial', 12, 'bold')
    BODY_FONT = ('Arial', 10)
    SMALL_FONT = ('Arial', 9)
    
    # 패딩 및 마진
    LARGE_PADDING = 20
    MEDIUM_PADDING = 10
    SMALL_PADDING = 5


class StandardButton(tk.Button):
    """표준화된 버튼 컴포넌트"""
    
    def __init__(self, parent, text: str, command: Callable = None, 
                 style: str = 'primary', width: int = 15, **kwargs):
        """
        표준 버튼 초기화
        
        Args:
            parent: 부모 위젯
            text: 버튼 텍스트
            command: 클릭 시 실행할 함수
            style: 버튼 스타일 ('primary', 'success', 'warning', 'danger', 'secondary')
            width: 버튼 너비
            **kwargs: 추가 버튼 옵션
        """
        # 스타일별 색상 설정
        style_colors = {
            'primary': (GUIStyles.PRIMARY_COLOR, 'white'),
            'success': (GUIStyles.SUCCESS_COLOR, 'white'),
            'warning': (GUIStyles.WARNING_COLOR, 'white'),
            'danger': (GUIStyles.DANGER_COLOR, 'white'),
            'secondary': (GUIStyles.SECONDARY_COLOR, 'white')
        }
        
        bg_color, fg_color = style_colors.get(style, style_colors['primary'])
        
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg=fg_color,
            font=GUIStyles.BODY_FONT,
            width=width,
            relief='flat',
            bd=0,
            padx=10,
            pady=5,
            cursor='hand2',
            **kwargs
        )
        
        # 호버 효과
        self._setup_hover_effects(bg_color)
    
    def _setup_hover_effects(self, normal_color: str):
        """호버 효과 설정"""
        def on_enter(event):
            self.configure(bg=self._darken_color(normal_color))
        
        def on_leave(event):
            self.configure(bg=normal_color)
        
        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)
    
    @staticmethod
    def _darken_color(hex_color: str, factor: float = 0.8) -> str:
        """색상을 어둡게 만드는 유틸리티"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * factor) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"


class StatusLabel(tk.Label):
    """상태 표시용 라벨"""
    
    def __init__(self, parent, initial_text: str = "준비", **kwargs):
        """
        상태 라벨 초기화
        
        Args:
            parent: 부모 위젯
            initial_text: 초기 텍스트
            **kwargs: 추가 라벨 옵션
        """
        super().__init__(
            parent,
            text=initial_text,
            font=GUIStyles.BODY_FONT,
            bg=GUIStyles.SURFACE_COLOR,
            fg=GUIStyles.TEXT_COLOR,
            **kwargs
        )
    
    def set_status(self, message: str, status_type: str = 'info'):
        """
        상태 업데이트
        
        Args:
            message: 표시할 메시지
            status_type: 상태 유형 ('info', 'success', 'warning', 'error')
        """
        colors = {
            'info': GUIStyles.TEXT_COLOR,
            'success': GUIStyles.SUCCESS_COLOR,
            'warning': GUIStyles.WARNING_COLOR,
            'error': GUIStyles.DANGER_COLOR
        }
        
        self.configure(text=message, fg=colors.get(status_type, colors['info']))


class ProgressFrame(tk.Frame):
    """진행 상황 표시 프레임"""
    
    def __init__(self, parent, **kwargs):
        """진행 상황 프레임 초기화"""
        super().__init__(parent, bg=GUIStyles.SURFACE_COLOR, **kwargs)
        
        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progressbar = ttk.Progressbar(
            self,
            mode='determinate',
            variable=self.progress_var,
            length=300
        )
        self.progressbar.pack(pady=GUIStyles.SMALL_PADDING)
        
        # 상태 라벨
        self.status_label = StatusLabel(self, "대기 중...")
        self.status_label.pack()
    
    def update_progress(self, value: float, message: str = None):
        """
        진행률 업데이트
        
        Args:
            value: 진행률 (0.0 ~ 100.0)
            message: 상태 메시지
        """
        self.progress_var.set(value)
        if message:
            self.status_label.set_status(message)
        
        # UI 업데이트 강제 실행
        self.update_idletasks()
    
    def reset(self):
        """진행률 리셋"""
        self.progress_var.set(0)
        self.status_label.set_status("대기 중...")


class AsyncOperationMixin:
    """비동기 작업을 위한 믹스인 클래스"""
    
    def run_async(self, operation: Callable, callback: Optional[Callable] = None,
                  error_handler: Optional[Callable] = None):
        """
        비동기로 작업 실행
        
        Args:
            operation: 실행할 작업 함수
            callback: 작업 완료 시 호출할 콜백
            error_handler: 에러 발생 시 호출할 핸들러
        """
        def worker():
            try:
                result = operation()
                if callback:
                    # UI 스레드에서 콜백 실행
                    self.after(0, lambda: callback(result))
            except Exception as e:
                if error_handler:
                    self.after(0, lambda: error_handler(e))
                else:
                    self.after(0, lambda: self._default_error_handler(e))
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    def _default_error_handler(self, error: Exception):
        """기본 에러 핸들러"""
        messagebox.showerror("오류", f"작업 중 오류가 발생했습니다:\n{str(error)}")


class StandardFrame(tk.Frame, AsyncOperationMixin):
    """표준화된 프레임 베이스 클래스"""
    
    def __init__(self, parent, title: str = None, **kwargs):
        """
        표준 프레임 초기화
        
        Args:
            parent: 부모 위젯
            title: 프레임 제목
            **kwargs: 추가 프레임 옵션
        """
        super().__init__(
            parent,
            bg=GUIStyles.SURFACE_COLOR,
            **kwargs
        )
        
        self.title = title
        if title:
            self._setup_title()
    
    def _setup_title(self):
        """제목 섹션 설정"""
        title_frame = tk.Frame(self, bg=GUIStyles.SURFACE_COLOR)
        title_frame.pack(fill='x', pady=(0, GUIStyles.MEDIUM_PADDING))
        
        title_label = tk.Label(
            title_frame,
            text=self.title,
            font=GUIStyles.HEADING_FONT,
            bg=GUIStyles.SURFACE_COLOR,
            fg=GUIStyles.TEXT_COLOR
        )
        title_label.pack(side='left')
        
        # 구분선
        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill='x', pady=(0, GUIStyles.MEDIUM_PADDING))


class MessageUtils:
    """메시지 표시 유틸리티"""
    
    @staticmethod
    def show_success(title: str, message: str):
        """성공 메시지 표시"""
        messagebox.showinfo(title, message)
    
    @staticmethod
    def show_warning(title: str, message: str) -> bool:
        """경고 메시지 표시 (확인/취소)"""
        return messagebox.askokcancel(title, message, icon='warning')
    
    @staticmethod
    def show_error(title: str, message: str):
        """에러 메시지 표시"""
        messagebox.showerror(title, message)
    
    @staticmethod
    def ask_confirmation(title: str, message: str) -> bool:
        """확인 메시지 표시"""
        return messagebox.askyesno(title, message)


class LayoutUtils:
    """레이아웃 유틸리티"""
    
    @staticmethod
    def create_button_row(parent, buttons_config: list, **pack_options) -> tk.Frame:
        """
        버튼 행 생성
        
        Args:
            parent: 부모 위젯
            buttons_config: 버튼 설정 리스트 [{'text': '버튼명', 'command': 함수, 'style': '스타일'}, ...]
            **pack_options: pack 옵션
        
        Returns:
            버튼들이 포함된 프레임
        """
        button_frame = tk.Frame(parent, bg=GUIStyles.SURFACE_COLOR)
        button_frame.pack(**pack_options)
        
        for config in buttons_config:
            btn = StandardButton(
                button_frame,
                text=config.get('text', '버튼'),
                command=config.get('command'),
                style=config.get('style', 'primary'),
                width=config.get('width', 15)
            )
            btn.pack(side='left', padx=(0, GUIStyles.SMALL_PADDING))
        
        return button_frame
    
    @staticmethod
    def create_info_grid(parent, info_data: Dict[str, str], **pack_options) -> tk.Frame:
        """
        정보 표시 그리드 생성
        
        Args:
            parent: 부모 위젯
            info_data: 정보 딕셔너리 {'라벨': '값', ...}
            **pack_options: pack 옵션
        
        Returns:
            정보가 표시된 프레임
        """
        info_frame = tk.Frame(parent, bg=GUIStyles.SURFACE_COLOR)
        info_frame.pack(**pack_options)
        
        for row, (label, value) in enumerate(info_data.items()):
            # 라벨
            tk.Label(
                info_frame,
                text=f"{label}:",
                font=GUIStyles.BODY_FONT + ('bold',),
                bg=GUIStyles.SURFACE_COLOR,
                fg=GUIStyles.TEXT_COLOR
            ).grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
            
            # 값
            tk.Label(
                info_frame,
                text=str(value),
                font=GUIStyles.BODY_FONT,
                bg=GUIStyles.SURFACE_COLOR,
                fg=GUIStyles.MUTED_COLOR
            ).grid(row=row, column=1, sticky='w', pady=2)
        
        return info_frame


def debounce(delay: float):
    """
    디바운스 데코레이터 - 연속 호출 방지
    
    Args:
        delay: 지연 시간 (초)
    """
    def decorator(func):
        timer = None
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal timer
            if timer:
                timer.cancel()
            timer = threading.Timer(delay, func, args, kwargs)
            timer.start()
        
        return wrapper
    return decorator


def safe_call(func: Callable, *args, **kwargs) -> Any:
    """
    안전한 함수 호출 - 예외 처리 포함
    
    Args:
        func: 호출할 함수
        *args: 함수 인자
        **kwargs: 함수 키워드 인자
    
    Returns:
        함수 실행 결과 또는 None (에러 시)
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"함수 실행 중 오류 발생: {func.__name__} - {str(e)}")
        return None


# 모듈 레벨 편의 함수들
def create_standard_button(parent, text: str, command: Callable = None, 
                          style: str = 'primary', **kwargs) -> StandardButton:
    """표준 버튼 생성 편의 함수"""
    return StandardButton(parent, text, command, style, **kwargs)


def create_status_label(parent, initial_text: str = "준비", **kwargs) -> StatusLabel:
    """상태 라벨 생성 편의 함수"""
    return StatusLabel(parent, initial_text, **kwargs)


def create_progress_frame(parent, **kwargs) -> ProgressFrame:
    """진행률 프레임 생성 편의 함수"""
    return ProgressFrame(parent, **kwargs)
