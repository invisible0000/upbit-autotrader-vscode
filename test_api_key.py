#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
업비트 API 키 테스트 스크립트
"""

import os
import sys
import logging
# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# .env 파일에서 직접 API 키 읽기
try:
    with open('.env', 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    logger.info(".env 파일에서 환경 변수를 로드했습니다.")
except Exception as e:
    logger.error(f".env 파일 로드 중 오류 발생: {e}")

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append('.')

try:
    from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
except ImportError:
    logger.error("upbit_auto_trading 패키지를 찾을 수 없습니다. 프로젝트 루트 디렉토리에서 실행하세요.")
    sys.exit(1)

def test_api_key():
    """API 키 테스트"""
    logger.info("업비트 API 키 테스트를 시작합니다.")
    
    # 환경 변수에서 API 키 확인
    access_key = os.environ.get("UPBIT_ACCESS_KEY")
    secret_key = os.environ.get("UPBIT_SECRET_KEY")
    
    if not access_key or not secret_key:
        logger.error("API 키가 환경 변수에 설정되지 않았습니다.")
        return False
    
    logger.info(f"액세스 키: {access_key[:5]}...{access_key[-5:]}")
    logger.info(f"시크릿 키: {secret_key[:5]}...{secret_key[-5:]}")
    
    # API 클라이언트 생성
    api = UpbitAPI()
    
    try:
        # 1. 마켓 코드 조회 테스트 (인증 불필요)
        logger.info("마켓 코드 조회 테스트 중...")
        markets = api.get_markets()
        if markets.empty:
            logger.error("마켓 코드 조회 실패")
            return False
        logger.info(f"마켓 코드 조회 성공: {len(markets)}개 마켓")
        
        # 2. 계좌 정보 조회 테스트 (인증 필요)
        logger.info("계좌 정보 조회 테스트 중...")
        accounts = api.get_account()
        if not accounts:
            logger.error("계좌 정보 조회 실패")
            return False
        logger.info(f"계좌 정보 조회 성공: {len(accounts)}개 계좌")
        
        # 3. 주문 목록 조회 테스트 (인증 필요)
        logger.info("주문 목록 조회 테스트 중...")
        orders = api.get_orders()
        logger.info(f"주문 목록 조회 성공: {len(orders)}개 주문")
        
        logger.info("모든 테스트가 성공적으로 완료되었습니다.")
        return True
        
    except Exception as e:
        logger.exception(f"API 테스트 중 오류가 발생했습니다: {e}")
        return False

if __name__ == "__main__":
    success = test_api_key()
    sys.exit(0 if success else 1)