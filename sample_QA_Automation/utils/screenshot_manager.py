"""
스크린샷 관리자 모듈

이 모듈은 업비트 자동매매 시스템의 GUI 자동화 테스트를 위한 스크린샷 관리 기능을 제공합니다.
"""

import os
from datetime import datetime
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtCore import QRect


class ScreenshotManager:
    """스크린샷 관리자 클래스"""
    
    def __init__(self, base_dir="screenshots"):
        """
        초기화
        
        Args:
            base_dir (str): 스크린샷 저장 기본 디렉토리
        """
        self.base_dir = os.path.join("sample_QA_Automation", base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
    
    def capture_widget(self, widget, name=None):
        """
        위젯 캡처
        
        Args:
            widget (QWidget): 캡처할 위젯
            name (str, optional): 스크린샷 이름. None인 경우 타임스탬프 사용.
        
        Returns:
            str: 저장된 스크린샷 경로
        """
        # 스크린샷 이름 생성
        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"screenshot_{timestamp}"
        
        # 위젯 클래스 이름 가져오기
        widget_class = widget.__class__.__name__
        
        # 저장 디렉토리 생성
        save_dir = os.path.join(self.base_dir, widget_class)
        os.makedirs(save_dir, exist_ok=True)
        
        # 파일 경로 생성
        file_path = os.path.join(save_dir, f"{name}.png")
        
        # 위젯 캡처
        pixmap = QPixmap(widget.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        widget.render(painter, QRect(0, 0, widget.width(), widget.height()))
        painter.end()
        
        # 스크린샷 저장
        pixmap.save(file_path)
        
        print(f"스크린샷이 저장되었습니다: {file_path}")
        return file_path
    
    def capture_widget_element(self, widget, element_name, rect=None):
        """
        위젯 요소 캡처
        
        Args:
            widget (QWidget): 캡처할 위젯
            element_name (str): 요소 이름
            rect (QRect, optional): 캡처할 영역. None인 경우 전체 위젯 캡처.
        
        Returns:
            str: 저장된 스크린샷 경로
        """
        # 스크린샷 이름 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{element_name}_{timestamp}"
        
        # 위젯 클래스 이름 가져오기
        widget_class = widget.__class__.__name__
        
        # 저장 디렉토리 생성
        save_dir = os.path.join(self.base_dir, widget_class, "elements")
        os.makedirs(save_dir, exist_ok=True)
        
        # 파일 경로 생성
        file_path = os.path.join(save_dir, f"{name}.png")
        
        # 위젯 캡처
        if rect is None:
            rect = QRect(0, 0, widget.width(), widget.height())
        
        pixmap = QPixmap(rect.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        widget.render(painter, QRect(0, 0, rect.width(), rect.height()), rect)
        painter.end()
        
        # 스크린샷 저장
        pixmap.save(file_path)
        
        print(f"요소 스크린샷이 저장되었습니다: {file_path}")
        return file_path
    
    def compare_screenshots(self, path1, path2):
        """
        스크린샷 비교
        
        Args:
            path1 (str): 첫 번째 스크린샷 경로
            path2 (str): 두 번째 스크린샷 경로
        
        Returns:
            float: 유사도 (0.0 ~ 1.0)
        """
        try:
            from PIL import Image
            import numpy as np
            
            # 이미지 로드
            img1 = Image.open(path1)
            img2 = Image.open(path2)
            
            # 크기가 다르면 리사이즈
            if img1.size != img2.size:
                img2 = img2.resize(img1.size)
            
            # 이미지를 NumPy 배열로 변환
            arr1 = np.array(img1)
            arr2 = np.array(img2)
            
            # 유사도 계산
            similarity = np.mean(arr1 == arr2)
            
            print(f"스크린샷 유사도: {similarity:.4f}")
            return similarity
        
        except ImportError:
            print("PIL 또는 NumPy 패키지가 설치되어 있지 않습니다.")
            return -1