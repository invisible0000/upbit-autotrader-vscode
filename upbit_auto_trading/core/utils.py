#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
유틸리티 함수 모음

프로젝트 전반에서 사용되는 유틸리티 함수를 제공합니다.
"""

import os
import re
import uuid
import json
import yaml
import logging
import hashlib
import base64
from pathlib import Path
from typing import Dict, List, Any, Union, Optional
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

def generate_id(prefix: str = "") -> str:
    """고유 ID를 생성합니다.
    
    Args:
        prefix: ID 접두사 (선택적)
        
    Returns:
        str: 생성된 고유 ID
    """
    unique_id = str(uuid.uuid4())
    if prefix:
        return f"{prefix}-{unique_id}"
    return unique_id

def encrypt_api_key(api_key: str, password: str) -> str:
    """API 키를 암호화합니다.
    
    Args:
        api_key: 암호화할 API 키
        password: 암호화에 사용할 비밀번호
        
    Returns:
        str: 암호화된 API 키 (Base64 인코딩)
    """
    try:
        # 비밀번호에서 키 유도
        salt = b'upbit_auto_trading_salt'  # 실제 구현에서는 안전한 솔트 사용 필요
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Fernet 암호화
        f = Fernet(key)
        encrypted_data = f.encrypt(api_key.encode())
        
        return base64.urlsafe_b64encode(encrypted_data).decode()
    except Exception as e:
        logger.exception(f"API 키 암호화 중 오류가 발생했습니다: {e}")
        raise

def decrypt_api_key(encrypted_api_key: str, password: str) -> str:
    """암호화된 API 키를 복호화합니다.
    
    Args:
        encrypted_api_key: 암호화된 API 키 (Base64 인코딩)
        password: 암호화에 사용한 비밀번호
        
    Returns:
        str: 복호화된 API 키
    """
    try:
        # 비밀번호에서 키 유도
        salt = b'upbit_auto_trading_salt'  # 암호화에 사용한 것과 동일한 솔트
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Fernet 복호화
        f = Fernet(key)
        decrypted_data = f.decrypt(base64.urlsafe_b64decode(encrypted_api_key))
        
        return decrypted_data.decode()
    except Exception as e:
        logger.exception(f"API 키 복호화 중 오류가 발생했습니다: {e}")
        raise

def load_config(config_path: str) -> Dict:
    """설정 파일을 로드합니다.
    
    Args:
        config_path: 설정 파일 경로
        
    Returns:
        Dict: 설정 정보
    """
    try:
        if not os.path.exists(config_path):
            logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
            return {}
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                config = yaml.safe_load(f)
            elif config_path.endswith('.json'):
                config = json.load(f)
            else:
                logger.error(f"지원하지 않는 설정 파일 형식입니다: {config_path}")
                return {}
        
        return config
    except Exception as e:
        logger.exception(f"설정 파일 로드 중 오류가 발생했습니다: {e}")
        return {}

def save_config(config: Dict, config_path: str) -> bool:
    """설정 정보를 파일로 저장합니다.
    
    Args:
        config: 저장할 설정 정보
        config_path: 설정 파일 경로
        
    Returns:
        bool: 저장 성공 여부
    """
    try:
        # 디렉토리 생성
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            elif config_path.endswith('.json'):
                json.dump(config, f, ensure_ascii=False, indent=2)
            else:
                logger.error(f"지원하지 않는 설정 파일 형식입니다: {config_path}")
                return False
        
        return True
    except Exception as e:
        logger.exception(f"설정 파일 저장 중 오류가 발생했습니다: {e}")
        return False

def format_number(value: float, decimal_places: int = 2) -> str:
    """숫자를 포맷팅합니다.
    
    Args:
        value: 포맷팅할 숫자
        decimal_places: 소수점 자릿수
        
    Returns:
        str: 포맷팅된 숫자 문자열
    """
    try:
        format_str = f"{{:,.{decimal_places}f}}"
        return format_str.format(value)
    except Exception as e:
        logger.exception(f"숫자 포맷팅 중 오류가 발생했습니다: {e}")
        return str(value)

def format_timestamp(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """타임스탬프를 포맷팅합니다.
    
    Args:
        timestamp: 포맷팅할 타임스탬프
        format_str: 포맷 문자열
        
    Returns:
        str: 포맷팅된 타임스탬프 문자열
    """
    try:
        return timestamp.strftime(format_str)
    except Exception as e:
        logger.exception(f"타임스탬프 포맷팅 중 오류가 발생했습니다: {e}")
        return str(timestamp)

def parse_timeframe(timeframe: str) -> timedelta:
    """시간대 문자열을 timedelta로 변환합니다.
    
    Args:
        timeframe: 시간대 문자열 (예: "1m", "5m", "15m", "1h", "4h", "1d")
        
    Returns:
        timedelta: 변환된 timedelta
        
    Raises:
        ValueError: 지원하지 않는 시간대인 경우
    """
    try:
        # 정규식으로 숫자와 단위 분리
        match = re.match(r'(\d+)([mhdwM])', timeframe)
        if not match:
            raise ValueError(f"지원하지 않는 시간대 형식입니다: {timeframe}")
        
        value, unit = int(match.group(1)), match.group(2)
        
        if unit == 'm':
            return timedelta(minutes=value)
        elif unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
        elif unit == 'w':
            return timedelta(weeks=value)
        elif unit == 'M':
            return timedelta(days=value * 30)  # 근사값
        else:
            raise ValueError(f"지원하지 않는 시간대 단위입니다: {unit}")
    except Exception as e:
        logger.exception(f"시간대 변환 중 오류가 발생했습니다: {e}")
        raise

def ensure_directory(directory: str) -> bool:
    """디렉토리가 존재하는지 확인하고, 없으면 생성합니다.
    
    Args:
        directory: 디렉토리 경로
        
    Returns:
        bool: 디렉토리 존재 여부
    """
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.exception(f"디렉토리 생성 중 오류가 발생했습니다: {e}")
        return False