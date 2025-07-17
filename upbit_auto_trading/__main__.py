#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
업비트 자동매매 시스템 메인 실행 파일

이 파일은 업비트 자동매매 시스템의 진입점입니다.
"""

import os
import sys
import logging
import argparse
import yaml
from pathlib import Path

# 로깅 설정
def setup_logging(config_path=None):
    """로깅 설정을 초기화합니다."""
    try:
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logging.config.dictConfig(config)
        else:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(sys.stdout),
                    logging.FileHandler('logs/upbit_auto_trading.log', encoding='utf-8')
                ]
            )
    except Exception as e:
        # 기본 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        logging.error(f"로깅 설정 중 오류 발생: {e}")

def parse_arguments():
    """명령줄 인수를 파싱합니다."""
    parser = argparse.ArgumentParser(description='업비트 자동매매 시스템')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                        help='설정 파일 경로 (기본값: config/config.yaml)')
    parser.add_argument('--log-config', type=str, default='config/logging_config.yaml',
                        help='로깅 설정 파일 경로 (기본값: config/logging_config.yaml)')
    parser.add_argument('--mode', type=str, choices=['cli', 'web'], default='cli',
                        help='실행 모드 (cli: 명령줄 인터페이스, web: 웹 인터페이스) (기본값: cli)')
    parser.add_argument('--debug', action='store_true',
                        help='디버그 모드 활성화')
    return parser.parse_args()

def ensure_directories():
    """필요한 디렉토리가 존재하는지 확인하고, 없으면 생성합니다."""
    directories = ['logs', 'data']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)

def main():
    """메인 함수"""
    # 필요한 디렉토리 확인
    ensure_directories()
    
    # 명령줄 인수 파싱
    args = parse_arguments()
    
    # 로깅 설정
    setup_logging(args.log_config)
    
    # 로거 생성
    logger = logging.getLogger(__name__)
    logger.info("업비트 자동매매 시스템을 시작합니다.")
    
    try:
        # 설정 파일 로드
        if not os.path.exists(args.config):
            logger.error(f"설정 파일을 찾을 수 없습니다: {args.config}")
            sys.exit(1)
            
        with open(args.config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 디버그 모드 설정
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("디버그 모드가 활성화되었습니다.")
        
        # 실행 모드에 따라 다른 인터페이스 실행
        if args.mode == 'cli':
            logger.info("CLI 모드로 실행합니다.")
            from upbit_auto_trading.ui.cli.app import run_cli
            run_cli(config)
        else:  # web 모드
            logger.info("웹 인터페이스 모드로 실행합니다.")
            from upbit_auto_trading.ui.web.app import run_web
            run_web(config)
            
    except KeyboardInterrupt:
        logger.info("사용자에 의해 프로그램이 종료되었습니다.")
    except Exception as e:
        logger.exception(f"프로그램 실행 중 오류가 발생했습니다: {e}")
        sys.exit(1)
    finally:
        logger.info("업비트 자동매매 시스템을 종료합니다.")

if __name__ == "__main__":
    main()