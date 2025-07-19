#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
업비트 API 키 테스트 스크립트
"""

import os
import sys
import logging
from dotenv import load_dotenv

# --- 한글 깨짐 방지 설정 (Windows 환경) ---
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except TypeError:
        # 일부 환경에서는 reconfigure가 지원되지 않을 수 있음
        pass
# -----------------------------------------

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# .env 파일에서 환경 변수 로드
load_dotenv()
logger.info(".env 파일 로드를 시도했습니다. (파일이 없으면 무시됩니다)")

# 프로젝트 루트 디렉토리를 Python 경로에 추가
# 이 스크립트를 프로젝트 루트에서 실행하는 것을 권장합니다.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
except ImportError as e:
    logger.error(f"모듈 임포트 오류: {e}")
    logger.error("upbit_auto_trading 패키지를 찾을 수 없습니다. 프로젝트 루트 디렉토리에서 'python test_api_key.py' 명령으로 실행하세요.")
    sys.exit(1)

def test_api_key():
    """API 키의 유효성을 검사하고 결과를 명확하게 출력합니다."""
    logger.info("="*50)
    logger.info("  업비트 API 키 유효성 검사를 시작합니다.")
    logger.info("="*50)

    # 환경 변수에서 API 키 확인
    access_key = os.getenv("UPBIT_ACCESS_KEY")
    secret_key = os.getenv("UPBIT_SECRET_KEY")

    if not access_key or not secret_key:
        logger.error("[실패] .env 파일에서 UPBIT_ACCESS_KEY 또는 UPBIT_SECRET_KEY를 찾을 수 없습니다.")
        logger.error("프로젝트 루트에 .env 파일이 있는지, 아래 형식으로 키가 저장되었는지 확인하세요.")
        logger.error("UPBIT_ACCESS_KEY=your_access_key")
        logger.error("UPBIT_SECRET_KEY=your_secret_key")
        return False

    logger.info("[성공] .env 파일에서 API 키를 로드했습니다.")
    logger.info(f"   - Access Key: ...{access_key[-4:]}") # 보안을 위해 끝 4자리만 표시
    logger.info(f"   - Secret Key: ...{secret_key[-4:]}")

    # API 클라이언트 생성
    api = UpbitAPI(access_key=access_key, secret_key=secret_key)

    try:
        # 1. 계좌 정보 조회 테스트 (인증 필요)
        logger.info("\n[테스트 1/2] 계좌 정보 조회를 시도합니다... (인증 필요)")
        accounts = api.get_account()

        # accounts가 None이거나 비어있는 리스트일 경우 처리
        if not accounts:
            logger.error("[실패] 계좌 정보를 조회하지 못했습니다.")
            logger.error("   - 원인 1: API 키가 잘못되었을 수 있습니다 (권한 확인).")
            logger.error("   - 원인 2: 네트워크 오류 또는 업비트 서버 문제일 수 있습니다.")
            logger.error(f"   - 받은 응답: {accounts}")
            return False
        
        logger.info("[성공] 성공적으로 계좌 정보를 조회했습니다.")
        logger.info(f"   - 조회된 통화 개수: {len(accounts)}개")
        logger.info(f"   - 첫 번째 계좌: {accounts[0]['currency']} (잔고: {accounts[0]['balance']})")

        # 2. 마켓 코드 조회 테스트 (인증 불필요)
        logger.info("\n[테스트 2/2] KRW 마켓 코드 조회를 시도합니다... (인증 불필요)")
        markets = api.get_markets()
        if markets.empty:
            logger.error("[실패] 마켓 코드를 조회하지 못했습니다.")
            return False
        
        logger.info(f"[성공] 성공적으로 KRW 마켓 정보를 조회했습니다.")
        logger.info(f"   - 조회된 KRW 마켓 수: {len(markets)}개")
        logger.info(f"   - 첫 번째 마켓: {markets['market'].iloc[0]}")

        logger.info("\n" + "="*50)
        logger.info("  [최종 결과] 모든 API 테스트를 성공적으로 완료했습니다!")
        logger.info("="*50)
        return True

    except Exception as e:
        logger.exception(f"\n[오류] API 테스트 중 예외가 발생했습니다: {e}")
        logger.error("   - API 키의 권한(계좌 조회)이 올바르게 설정되었는지 확인하세요.")
        logger.error("   - 업비트 웹사이트에서 IP 주소 등록이 필요한지 확인해보세요.")
        return False

if __name__ == "__main__":
    is_successful = test_api_key()
    sys.exit(0 if is_successful else 1)
