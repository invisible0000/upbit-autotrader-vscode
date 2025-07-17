#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
웹 인터페이스 애플리케이션

웹 인터페이스를 통해 업비트 자동매매 시스템을 제어합니다.
"""

import logging
import os
from typing import Dict
from flask import Flask, render_template, jsonify, request, redirect, url_for

logger = logging.getLogger(__name__)

def create_app(config: Dict):
    """Flask 애플리케이션을 생성합니다.
    
    Args:
        config: 설정 정보
        
    Returns:
        Flask: Flask 애플리케이션 인스턴스
    """
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)
    
    # 라우트 설정
    @app.route('/')
    def index():
        """메인 페이지"""
        return render_template('index.html')
    
    @app.route('/api/status')
    def status():
        """시스템 상태 API"""
        return jsonify({
            'status': 'ok',
            'database': config['database']['type'],
            'logging_level': config['logging']['level']
        })
    
    @app.route('/api/screen')
    def screen():
        """종목 스크리닝 API"""
        return jsonify({
            'status': 'error',
            'message': '종목 스크리닝 기능은 아직 구현되지 않았습니다.'
        })
    
    @app.route('/api/strategies')
    def strategies():
        """전략 목록 API"""
        return jsonify({
            'status': 'error',
            'message': '전략 목록 조회 기능은 아직 구현되지 않았습니다.'
        })
    
    @app.route('/api/backtest')
    def backtest():
        """백테스팅 API"""
        return jsonify({
            'status': 'error',
            'message': '백테스팅 기능은 아직 구현되지 않았습니다.'
        })
    
    @app.route('/api/portfolios')
    def portfolios():
        """포트폴리오 목록 API"""
        return jsonify({
            'status': 'error',
            'message': '포트폴리오 목록 조회 기능은 아직 구현되지 않았습니다.'
        })
    
    @app.route('/api/trade/start')
    def trade_start():
        """실시간 거래 시작 API"""
        return jsonify({
            'status': 'error',
            'message': '실시간 거래 시작 기능은 아직 구현되지 않았습니다.'
        })
    
    @app.route('/api/trade/stop')
    def trade_stop():
        """실시간 거래 중지 API"""
        return jsonify({
            'status': 'error',
            'message': '실시간 거래 중지 기능은 아직 구현되지 않았습니다.'
        })
    
    @app.route('/api/trade/status')
    def trade_status():
        """거래 상태 API"""
        return jsonify({
            'status': 'error',
            'message': '거래 상태 확인 기능은 아직 구현되지 않았습니다.'
        })
    
    return app

def run_web(config: Dict):
    """웹 인터페이스를 실행합니다.
    
    Args:
        config: 설정 정보
    """
    logger.info("웹 인터페이스를 시작합니다.")
    
    try:
        # 템플릿 디렉토리 생성
        os.makedirs('upbit_auto_trading/ui/web/templates', exist_ok=True)
        
        # 기본 템플릿 파일 생성
        index_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>업비트 자동매매 시스템</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                }
                .header {
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    border-bottom: 1px solid #ddd;
                }
                .content {
                    padding: 20px;
                }
                .footer {
                    background-color: #f8f9fa;
                    padding: 10px;
                    text-align: center;
                    position: fixed;
                    bottom: 0;
                    width: 100%;
                    border-top: 1px solid #ddd;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>업비트 자동매매 시스템</h1>
                <p>웹 인터페이스에 오신 것을 환영합니다.</p>
            </div>
            
            <div class="content">
                <h2>시스템 상태</h2>
                <p>상태: <span id="status">확인 중...</span></p>
                
                <h2>기능</h2>
                <ul>
                    <li><a href="#" onclick="alert('종목 스크리닝 기능은 아직 구현되지 않았습니다.'); return false;">종목 스크리닝</a></li>
                    <li><a href="#" onclick="alert('전략 관리 기능은 아직 구현되지 않았습니다.'); return false;">전략 관리</a></li>
                    <li><a href="#" onclick="alert('백테스팅 기능은 아직 구현되지 않았습니다.'); return false;">백테스팅</a></li>
                    <li><a href="#" onclick="alert('포트폴리오 관리 기능은 아직 구현되지 않았습니다.'); return false;">포트폴리오 관리</a></li>
                    <li><a href="#" onclick="alert('실시간 거래 기능은 아직 구현되지 않았습니다.'); return false;">실시간 거래</a></li>
                </ul>
            </div>
            
            <div class="footer">
                <p>&copy; 2023 업비트 자동매매 시스템</p>
            </div>
            
            <script>
                // 시스템 상태 확인
                fetch('/api/status')
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'ok') {
                            document.getElementById('status').textContent = '정상 작동 중';
                        } else {
                            document.getElementById('status').textContent = '오류 발생';
                        }
                    })
                    .catch(error => {
                        document.getElementById('status').textContent = '연결 오류';
                        console.error('Error:', error);
                    });
            </script>
        </body>
        </html>
        """
        
        with open('upbit_auto_trading/ui/web/templates/index.html', 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        # Flask 애플리케이션 생성 및 실행
        app = create_app(config)
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except Exception as e:
        logger.exception(f"웹 인터페이스 실행 중 오류가 발생했습니다: {e}")
    finally:
        logger.info("웹 인터페이스를 종료합니다.")

if __name__ == "__main__":
    # 직접 실행 시 테스트용 설정
    test_config = {
        "database": {"type": "sqlite"},
        "logging": {"level": "INFO"}
    }
    run_web(test_config)