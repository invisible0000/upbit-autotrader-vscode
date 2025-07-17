#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
기본 스크리너

거래량, 변동성, 추세 등을 기반으로 코인을 스크리닝하는 기능을 제공합니다.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta

from upbit_auto_trading.data_layer.collectors.data_collector import DataCollector
from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
from upbit_auto_trading.data_layer.processors.data_processor import DataProcessor

logger = logging.getLogger(__name__)

class BaseScreener:
    """기본 스크리닝 기능을 제공하는 클래스"""
    
    def __init__(self, api_key: str = None, secret_key: str = None):
        """BaseScreener 초기화
        
        Args:
            api_key: 업비트 API 키 (없으면 환경 변수에서 로드)
            secret_key: 업비트 API 시크릿 키 (없으면 환경 변수에서 로드)
        """
        self.api = UpbitAPI(access_key=api_key, secret_key=secret_key)
        self.data_collector = DataCollector(api_key=api_key, secret_key=secret_key)
        self.data_processor = DataProcessor()
    
    def screen_by_volume(self, min_volume: float, timeframe: str = '1d', days: int = 1) -> List[str]:
        """거래량 기준으로 코인을 스크리닝합니다.
        
        Args:
            min_volume: 최소 거래량 (KRW)
            timeframe: 시간대 (예: '1d', '1h', '15m')
            days: 조회할 일수
            
        Returns:
            List[str]: 스크리닝된 코인 심볼 목록
        """
        try:
            # 모든 KRW 마켓 코인 조회
            markets_df = self.api.get_markets()
            if markets_df.empty:
                logger.error("마켓 정보를 가져오는데 실패했습니다.")
                return []
            
            # KRW 마켓만 필터링
            krw_markets = markets_df[markets_df['market'].str.startswith('KRW-')]
            symbols = krw_markets['market'].tolist()
            
            # 티커 정보 조회
            tickers_df = self.api.get_tickers(symbols)
            if tickers_df.empty:
                logger.error("티커 정보를 가져오는데 실패했습니다.")
                return []
            
            # 거래량 기준 필터링
            if 'acc_trade_price_24h' in tickers_df.columns:
                filtered_df = tickers_df[tickers_df['acc_trade_price_24h'] >= min_volume]
                return filtered_df['market'].tolist()
            else:
                logger.error("24시간 거래대금 정보가 없습니다.")
                return []
            
        except Exception as e:
            logger.exception(f"거래량 기준 스크리닝 중 오류가 발생했습니다: {e}")
            return []
    
    def screen_by_volatility(self, min_volatility: float = 0.05, max_volatility: float = 0.5, 
                            timeframe: str = '1d', days: int = 7) -> List[str]:
        """변동성 기준으로 코인을 스크리닝합니다.
        
        Args:
            min_volatility: 최소 변동성 (0.05 = 5%)
            max_volatility: 최대 변동성 (0.5 = 50%)
            timeframe: 시간대 (예: '1d', '1h', '15m')
            days: 조회할 일수
            
        Returns:
            List[str]: 스크리닝된 코인 심볼 목록
        """
        try:
            # 모든 KRW 마켓 코인 조회
            markets_df = self.api.get_markets()
            if markets_df.empty:
                logger.error("마켓 정보를 가져오는데 실패했습니다.")
                return []
            
            # KRW 마켓만 필터링
            krw_markets = markets_df[markets_df['market'].str.startswith('KRW-')]
            symbols = krw_markets['market'].tolist()
            
            # 결과를 저장할 리스트
            filtered_symbols = []
            
            # 각 코인에 대해 변동성 계산
            for symbol in symbols:
                try:
                    # 캔들 데이터 조회
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=days)
                    
                    try:
                        # 먼저 로컬 데이터베이스에서 조회
                        df = self.data_collector.get_ohlcv_data(symbol, timeframe, start_date, end_date)
                        
                        # 데이터가 없으면 API에서 직접 조회
                        if df.empty:
                            df = self.data_collector.collect_historical_ohlcv(symbol, timeframe, start_date, end_date)
                    except Exception as e:
                        logger.warning(f"{symbol} 데이터 수집 중 오류 발생: {e}")
                        continue
                    
                    if df.empty or len(df) < 2:
                        continue
                    
                    # 일별 변동성 계산 (고가-저가)/저가
                    df['volatility'] = (df['high'] - df['low']) / df['low']
                    
                    # 평균 변동성 계산
                    avg_volatility = df['volatility'].mean()
                    
                    # 변동성 기준 필터링
                    if min_volatility <= avg_volatility <= max_volatility:
                        filtered_symbols.append(symbol)
                        logger.debug(f"{symbol}: 평균 변동성 {avg_volatility:.2%}")
                
                except Exception as e:
                    logger.warning(f"{symbol} 변동성 계산 중 오류 발생: {e}")
                    continue
            
            return filtered_symbols
            
        except Exception as e:
            logger.exception(f"변동성 기준 스크리닝 중 오류가 발생했습니다: {e}")
            return []
    
    def screen_by_trend(self, trend_type: str = 'bullish', timeframe: str = '1d', days: int = 14) -> List[str]:
        """추세 기준으로 코인을 스크리닝합니다.
        
        Args:
            trend_type: 추세 유형 ('bullish': 상승, 'bearish': 하락, 'sideways': 횡보)
            timeframe: 시간대 (예: '1d', '1h', '15m')
            days: 조회할 일수
            
        Returns:
            List[str]: 스크리닝된 코인 심볼 목록
        """
        try:
            # 모든 KRW 마켓 코인 조회
            markets_df = self.api.get_markets()
            if markets_df.empty:
                logger.error("마켓 정보를 가져오는데 실패했습니다.")
                return []
            
            # KRW 마켓만 필터링
            krw_markets = markets_df[markets_df['market'].str.startswith('KRW-')]
            symbols = krw_markets['market'].tolist()
            
            # 결과를 저장할 리스트
            filtered_symbols = []
            
            # 각 코인에 대해 추세 분석
            for symbol in symbols:
                try:
                    # 캔들 데이터 조회
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=days)
                    
                    try:
                        # 먼저 로컬 데이터베이스에서 조회
                        df = self.data_collector.get_ohlcv_data(symbol, timeframe, start_date, end_date)
                        
                        # 데이터가 없으면 API에서 직접 조회
                        if df.empty:
                            df = self.data_collector.collect_historical_ohlcv(symbol, timeframe, start_date, end_date)
                    except Exception as e:
                        logger.warning(f"{symbol} 데이터 수집 중 오류 발생: {e}")
                        continue
                    
                    if df.empty or len(df) < 5:  # 최소 5개 데이터 필요
                        continue
                    
                    # 이동평균 계산
                    df = self.data_processor.calculate_sma(df, window=5, column='close')
                    df = self.data_processor.calculate_sma(df, window=20, column='close')
                    
                    # 최근 데이터만 사용
                    recent_df = df.tail(5)
                    
                    # 추세 판단
                    is_bullish = False
                    is_bearish = False
                    is_sideways = False
                    
                    # 상승 추세: 5일 이동평균이 20일 이동평균보다 위에 있고, 5일 이동평균이 상승 중
                    if 'SMA_5' in recent_df.columns and 'SMA_20' in recent_df.columns:
                        if recent_df['SMA_5'].iloc[-1] > recent_df['SMA_20'].iloc[-1] and \
                           recent_df['SMA_5'].iloc[-1] > recent_df['SMA_5'].iloc[-2]:
                            is_bullish = True
                        
                        # 하락 추세: 5일 이동평균이 20일 이동평균보다 아래에 있고, 5일 이동평균이 하락 중
                        elif recent_df['SMA_5'].iloc[-1] < recent_df['SMA_20'].iloc[-1] and \
                             recent_df['SMA_5'].iloc[-1] < recent_df['SMA_5'].iloc[-2]:
                            is_bearish = True
                        
                        # 횡보 추세: 그 외의 경우
                        else:
                            is_sideways = True
                    
                    # 요청한 추세 유형에 맞는 코인 필터링
                    if (trend_type == 'bullish' and is_bullish) or \
                       (trend_type == 'bearish' and is_bearish) or \
                       (trend_type == 'sideways' and is_sideways):
                        filtered_symbols.append(symbol)
                        logger.debug(f"{symbol}: {trend_type} 추세 감지")
                
                except Exception as e:
                    logger.warning(f"{symbol} 추세 분석 중 오류 발생: {e}")
                    continue
            
            return filtered_symbols
            
        except Exception as e:
            logger.exception(f"추세 기준 스크리닝 중 오류가 발생했습니다: {e}")
            return []
    
    def combine_screening_results(self, results: List[List[str]], method: str = 'intersection') -> List[str]:
        """여러 스크리닝 결과를 조합합니다.
        
        Args:
            results: 스크리닝 결과 목록
            method: 조합 방법 ('intersection': 교집합, 'union': 합집합)
            
        Returns:
            List[str]: 조합된 코인 심볼 목록
        """
        if not results:
            return []
        
        if method == 'intersection':
            # 교집합: 모든 결과에 포함된 코인만 선택
            combined = set(results[0])
            for result in results[1:]:
                combined = combined.intersection(set(result))
            return list(combined)
        
        elif method == 'union':
            # 합집합: 어느 하나의 결과에라도 포함된 코인 선택
            combined = set()
            for result in results:
                combined = combined.union(set(result))
            return list(combined)
        
        else:
            logger.error(f"지원하지 않는 조합 방법입니다: {method}")
            return []
    
    def screen_coins(self, criteria: List[Dict]) -> List[Dict]:
        """설정된 기준으로 코인을 스크리닝합니다.
        
        Args:
            criteria: 스크리닝 기준 목록
            
        Returns:
            List[Dict]: 스크리닝된 코인 정보 목록
        """
        try:
            all_results = []
            
            for criterion in criteria:
                criterion_type = criterion.get('type')
                params = criterion.get('params', {})
                
                if criterion_type == 'volume':
                    min_volume = params.get('min_volume', 1000000000)  # 기본값: 10억원
                    timeframe = params.get('timeframe', '1d')
                    days = params.get('days', 1)
                    
                    result = self.screen_by_volume(min_volume, timeframe, days)
                    all_results.append((result, 'volume'))
                
                elif criterion_type == 'volatility':
                    min_volatility = params.get('min_volatility', 0.05)
                    max_volatility = params.get('max_volatility', 0.5)
                    timeframe = params.get('timeframe', '1d')
                    days = params.get('days', 7)
                    
                    result = self.screen_by_volatility(min_volatility, max_volatility, timeframe, days)
                    all_results.append((result, 'volatility'))
                
                elif criterion_type == 'trend':
                    trend_type = params.get('trend_type', 'bullish')
                    timeframe = params.get('timeframe', '1d')
                    days = params.get('days', 14)
                    
                    result = self.screen_by_trend(trend_type, timeframe, days)
                    all_results.append((result, 'trend'))
                
                else:
                    logger.warning(f"지원하지 않는 스크리닝 기준입니다: {criterion_type}")
            
            # 결과가 없으면 빈 리스트 반환
            if not all_results:
                return []
            
            # 조합 방법 결정
            combine_method = 'intersection'  # 기본값: 교집합
            for criterion in criteria:
                if criterion.get('type') == 'combine':
                    combine_method = criterion.get('params', {}).get('method', 'intersection')
            
            # 결과 조합
            symbols_only = [result[0] for result in all_results]
            combined_symbols = self.combine_screening_results(symbols_only, combine_method)
            
            # 결과 형식 구성
            result_list = []
            
            # 티커 정보 조회
            tickers_df = self.api.get_tickers(combined_symbols)
            
            for symbol in combined_symbols:
                # 해당 심볼이 어떤 기준을 만족했는지 확인
                matched_criteria = []
                for result, criterion_type in all_results:
                    if symbol in result:
                        matched_criteria.append(criterion_type)
                
                # 티커 정보에서 현재 가격과 거래량 추출
                ticker_info = tickers_df[tickers_df['market'] == symbol]
                
                if not ticker_info.empty:
                    current_price = ticker_info['trade_price'].iloc[0]
                    volume_24h = ticker_info['acc_trade_price_24h'].iloc[0] if 'acc_trade_price_24h' in ticker_info.columns else 0
                    
                    # 코인 한글명 조회
                    market_info = self.api.get_markets()
                    coin_name = market_info[market_info['market'] == symbol]['korean_name'].iloc[0] if not market_info.empty else ""
                    
                    result_list.append({
                        'symbol': symbol,
                        'name': coin_name,
                        'current_price': current_price,
                        'volume_24h': volume_24h,
                        'matched_criteria': matched_criteria
                    })
            
            return result_list
            
        except Exception as e:
            logger.exception(f"코인 스크리닝 중 오류가 발생했습니다: {e}")
            return []