"""
리소스 관리 모듈

이 모듈은 업비트 자동매매 시스템의 리소스(아이콘, 이미지 등)를 관리하는 클래스를 제공합니다.
"""

import os
from PyQt6.QtGui import QIcon, QPixmap


class ResourceManager:
    """리소스 관리 클래스"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super(ResourceManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """초기화"""
        if self._initialized:
            return
        
        self._initialized = True
        self._resources = {}
        
        # 리소스 디렉토리 경로
        self._base_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )))),
            "resources"
        )
        
        # 리소스 디렉토리가 없으면 생성
        if not os.path.exists(self._base_path):
            os.makedirs(self._base_path)
            os.makedirs(os.path.join(self._base_path, "icons"))
            os.makedirs(os.path.join(self._base_path, "images"))
    
    def get_icon(self, name):
        """
        아이콘 반환
        
        Args:
            name (str): 아이콘 이름 (확장자 제외)
            
        Returns:
            QIcon: 아이콘 인스턴스
        """
        resource_key = f"icon:{name}"
        
        if resource_key not in self._resources:
            icon_path = os.path.join(self._base_path, "icons", f"{name}.png")
            
            # 아이콘 파일이 존재하는지 확인
            if os.path.exists(icon_path):
                self._resources[resource_key] = QIcon(icon_path)
            else:
                # 기본 아이콘 반환
                self._resources[resource_key] = QIcon()
        
        return self._resources[resource_key]
    
    def get_image(self, name):
        """
        이미지 반환
        
        Args:
            name (str): 이미지 이름 (확장자 제외)
            
        Returns:
            QPixmap: 이미지 인스턴스
        """
        resource_key = f"image:{name}"
        
        if resource_key not in self._resources:
            image_path = os.path.join(self._base_path, "images", f"{name}.png")
            
            # 이미지 파일이 존재하는지 확인
            if os.path.exists(image_path):
                self._resources[resource_key] = QPixmap(image_path)
            else:
                # 빈 이미지 반환
                self._resources[resource_key] = QPixmap()
        
        return self._resources[resource_key]
    
    def clear_cache(self):
        """리소스 캐시 초기화"""
        self._resources.clear()