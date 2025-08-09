"""
로깅 관리 모듈

이 모듈은 업비트 자동매매 시스템의 로깅 기능을 관리하는 클래스를 제공합니다.
"""

import os
import logging
from datetime import datetime


class LoggingManager:
    """로깅 관리 클래스"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super(LoggingManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """초기화"""
        if self._initialized:
            return
        
        self._initialized = True
        self._loggers = {}
    
    def get_logger(self, name="upbit_auto_trading", log_level=logging.DEBUG):
        """
        로거 인스턴스 반환
        
        Args:
            name (str): 로거 이름
            log_level (int): 로그 레벨
            
        Returns:
            logging.Logger: 로거 인스턴스
        """
        if name in self._loggers:
            return self._loggers[name]
        
        # 로거 생성
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        
        # 이미 핸들러가 설정되어 있으면 추가하지 않음
        if logger.hasHandlers():
            self._loggers[name] = logger
            return logger
        
        # 로그 디렉토리 생성
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # 현재 날짜를 파일명에 포함
        current_date = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(logs_dir, f"{name}_{current_date}.log")
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        
        # 파일 핸들러
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        
        # 핸들러 추가
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        # 로거 캐싱
        self._loggers[name] = logger
        
        return logger