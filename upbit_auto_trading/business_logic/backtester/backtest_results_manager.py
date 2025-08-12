#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
백테스트 결과 관리 모듈

이 모듈은 백테스트 결과를 저장, 불러오기, 비교하는 기능을 제공합니다.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid

# matplotlib 및 seaborn 임포트 시도
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import seaborn as sns
    from matplotlib.figure import Figure
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    # 시각화 라이브러리가 없을 때 사용할 Figure 대체 클래스
    class DummyFigure:
        """시각화 라이브러리가 없을 때 사용하는 더미 Figure 클래스"""
        pass
    Figure = DummyFigure

from sqlalchemy.orm import Session
from upbit_auto_trading.data_layer.models import Backtest

class BacktestResultsManager:
    """백테스트 결과 관리 클래스"""

    def __init__(self, session: Session, results_dir: Optional[str] = None):
        """
        백테스트 결과 관리자 초기화
        
        Args:
            session: SQLAlchemy 세션
            results_dir: 결과 파일 저장 디렉토리 (기본값: './data/backtest_results')
        """
        self.logger = logging.getLogger(__name__)
        self.session = session
        
        # 결과 저장 디렉토리 설정
        if results_dir is None:
            self.results_dir = os.path.join("data", "backtest_results")
        else:
            self.results_dir = results_dir
        
        # 결과 저장 디렉토리 생성
        os.makedirs(self.results_dir, exist_ok=True)
        
        self.logger.info(f"백테스트 결과 관리자 초기화 완료. 결과 저장 디렉토리: {self.results_dir}")

    def save_backtest_result(self, result: Dict[str, Any]) -> str:
        """
        백테스트 결과 저장
        
        Args:
            result: 백테스트 결과 딕셔너리
            
        Returns:
            저장된 결과 ID
        """
        self.logger.info("백테스트 결과 저장 중")
        
        # 결과 ID 확인 또는 생성
        result_id = result.get("id")
        if result_id is None:
            result_id = str(uuid.uuid4())
            result["id"] = result_id
        
        # 데이터베이스에 저장
        try:
            # 자본 곡선 및 기타 DataFrame 객체 처리
            performance_metrics = result.get("performance_metrics", {})
            
            # Backtest 모델 생성
            backtest = Backtest(
                id=result_id,
                strategy_id=result.get("strategy_id"),
                symbol=result.get("symbol"),
                portfolio_id=result.get("portfolio_id"),
                timeframe=result.get("timeframe"),
                start_date=result.get("start_date"),
                end_date=result.get("end_date"),
                initial_capital=result.get("initial_capital"),
                performance_metrics=json.dumps(performance_metrics),
                created_at=datetime.utcnow()
            )
            
            # 데이터베이스에 저장
            self.session.add(backtest)
            self.session.commit()
            
            self.logger.info(f"백테스트 결과를 데이터베이스에 저장했습니다. ID: {result_id}")
        except Exception as e:
            self.logger.error(f"백테스트 결과 데이터베이스 저장 실패: {e}")
            self.session.rollback()
        
        # 파일로 저장
        try:
            # 결과 파일 경로
            result_file_path = os.path.join(self.results_dir, f"{result_id}.json")
            
            # 저장할 결과 복사본 생성
            result_to_save = result.copy()
            
            # DataFrame 객체 처리
            if "equity_curve" in result_to_save and isinstance(result_to_save["equity_curve"], pd.DataFrame):
                # DataFrame을 JSON 직렬화 가능한 형태로 변환
                equity_curve_dict = {
                    "index": [str(idx) for idx in result_to_save["equity_curve"].index],
                    "data": result_to_save["equity_curve"].to_dict(orient="list")
                }
                result_to_save["equity_curve"] = equity_curve_dict
            
            # 날짜 객체 처리
            result_to_save["start_date"] = str(result_to_save.get("start_date", ""))
            result_to_save["end_date"] = str(result_to_save.get("end_date", ""))
            
            # 거래 내역의 날짜 처리
            if "trades" in result_to_save:
                for trade in result_to_save["trades"]:
                    if "entry_time" in trade:
                        trade["entry_time"] = str(trade["entry_time"])
                    if "exit_time" in trade:
                        trade["exit_time"] = str(trade["exit_time"])
            
            # JSON 파일로 저장
            with open(result_file_path, "w", encoding="utf-8") as f:
                json.dump(result_to_save, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"백테스트 결과를 파일로 저장했습니다. 경로: {result_file_path}")
        except Exception as e:
            self.logger.error(f"백테스트 결과 파일 저장 실패: {e}")
        
        return result_id

    def load_backtest_result(self, result_id: str) -> Dict[str, Any]:
        """
        백테스트 결과 불러오기
        
        Args:
            result_id: 결과 ID
            
        Returns:
            백테스트 결과 딕셔너리
        """
        self.logger.info(f"백테스트 결과 불러오기 중. ID: {result_id}")
        
        # 결과 파일 경로
        result_file_path = os.path.join(self.results_dir, f"{result_id}.json")
        
        # 파일이 존재하는지 확인
        if not os.path.exists(result_file_path):
            self.logger.warning(f"백테스트 결과 파일이 존재하지 않습니다. 경로: {result_file_path}")
            
            # 데이터베이스에서 기본 정보만 불러오기
            backtest = self.session.query(Backtest).filter(Backtest.id == result_id).first()
            
            if backtest is None:
                self.logger.error(f"백테스트 결과를 찾을 수 없습니다. ID: {result_id}")
                return {}
            
            # 기본 정보만 포함된 결과 반환
            return {
                "id": backtest.id,
                "strategy_id": backtest.strategy_id,
                "symbol": backtest.symbol,
                "portfolio_id": backtest.portfolio_id,
                "timeframe": backtest.timeframe,
                "start_date": backtest.start_date,
                "end_date": backtest.end_date,
                "initial_capital": backtest.initial_capital,
                "performance_metrics": json.loads(backtest.performance_metrics) if backtest.performance_metrics else {},
                "created_at": backtest.created_at
            }
        
        # 파일에서 결과 불러오기
        try:
            with open(result_file_path, "r", encoding="utf-8") as f:
                result = json.load(f)
            
            # DataFrame 객체 복원
            if "equity_curve" in result and isinstance(result["equity_curve"], dict):
                equity_curve_dict = result["equity_curve"]
                
                # 인덱스를 datetime으로 변환
                try:
                    index = pd.to_datetime(equity_curve_dict["index"])
                    data = equity_curve_dict["data"]
                    result["equity_curve"] = pd.DataFrame(data, index=index)
                except Exception as e:
                    self.logger.error(f"자본 곡선 DataFrame 복원 실패: {e}")
                    result["equity_curve"] = pd.DataFrame()
            
            # 날짜 객체 복원
            try:
                if "start_date" in result and isinstance(result["start_date"], str):
                    result["start_date"] = pd.to_datetime(result["start_date"])
                if "end_date" in result and isinstance(result["end_date"], str):
                    result["end_date"] = pd.to_datetime(result["end_date"])
                
                # 거래 내역의 날짜 복원
                if "trades" in result:
                    for trade in result["trades"]:
                        if "entry_time" in trade and isinstance(trade["entry_time"], str):
                            trade["entry_time"] = pd.to_datetime(trade["entry_time"])
                        if "exit_time" in trade and isinstance(trade["exit_time"], str):
                            trade["exit_time"] = pd.to_datetime(trade["exit_time"])
            except Exception as e:
                self.logger.error(f"날짜 객체 복원 실패: {e}")
            
            self.logger.info(f"백테스트 결과를 성공적으로 불러왔습니다. ID: {result_id}")
            return result
        except Exception as e:
            self.logger.error(f"백테스트 결과 불러오기 실패: {e}")
            return {}

    def save_portfolio_backtest_result(self, result: Dict[str, Any]) -> str:
        """
        포트폴리오 백테스트 결과 저장
        
        Args:
            result: 포트폴리오 백테스트 결과 딕셔너리
            
        Returns:
            저장된 결과 ID
        """
        self.logger.info("포트폴리오 백테스트 결과 저장 중")
        
        # 결과 ID 확인 또는 생성
        result_id = result.get("id")
        if result_id is None:
            result_id = str(uuid.uuid4())
            result["id"] = result_id
        
        # 데이터베이스에 저장
        try:
            # 포트폴리오 성과 지표
            portfolio_performance = result.get("portfolio_performance", {})
            
            # Backtest 모델 생성 (포트폴리오 백테스트용)
            backtest = Backtest(
                id=result_id,
                portfolio_id=result.get("portfolio_id"),
                timeframe=result.get("timeframe"),
                start_date=result.get("start_date"),
                end_date=result.get("end_date"),
                initial_capital=result.get("initial_capital"),
                performance_metrics=json.dumps(portfolio_performance),
                created_at=datetime.utcnow()
            )
            
            # 데이터베이스에 저장
            self.session.add(backtest)
            self.session.commit()
            
            self.logger.info(f"포트폴리오 백테스트 결과를 데이터베이스에 저장했습니다. ID: {result_id}")
        except Exception as e:
            self.logger.error(f"포트폴리오 백테스트 결과 데이터베이스 저장 실패: {e}")
            self.session.rollback()
        
        # 파일로 저장
        try:
            # 결과 파일 경로
            result_file_path = os.path.join(self.results_dir, f"{result_id}.json")
            
            # 저장할 결과 복사본 생성
            result_to_save = result.copy()
            
            # DataFrame 객체 처리
            if "combined_equity_curve" in result_to_save and isinstance(result_to_save["combined_equity_curve"], pd.DataFrame):
                # DataFrame을 JSON 직렬화 가능한 형태로 변환
                equity_curve_dict = {
                    "index": [str(idx) for idx in result_to_save["combined_equity_curve"].index],
                    "data": result_to_save["combined_equity_curve"].to_dict(orient="list")
                }
                result_to_save["combined_equity_curve"] = equity_curve_dict
            
            # 개별 백테스트 결과의 DataFrame 객체 처리
            if "backtest_results" in result_to_save:
                for backtest_result in result_to_save["backtest_results"]:
                    if "result" in backtest_result and "equity_curve" in backtest_result["result"] and isinstance(backtest_result["result"]["equity_curve"], pd.DataFrame):
                        equity_curve = backtest_result["result"]["equity_curve"]
                        equity_curve_dict = {
                            "index": [str(idx) for idx in equity_curve.index],
                            "data": equity_curve.to_dict(orient="list")
                        }
                        backtest_result["result"]["equity_curve"] = equity_curve_dict
            
            # 날짜 객체 처리
            result_to_save["start_date"] = str(result_to_save.get("start_date", ""))
            result_to_save["end_date"] = str(result_to_save.get("end_date", ""))
            
            # 개별 백테스트 결과의 날짜 객체 처리
            if "backtest_results" in result_to_save:
                for backtest_result in result_to_save["backtest_results"]:
                    if "result" in backtest_result:
                        result_item = backtest_result["result"]
                        if "start_date" in result_item:
                            result_item["start_date"] = str(result_item["start_date"])
                        if "end_date" in result_item:
                            result_item["end_date"] = str(result_item["end_date"])
                        
                        # 거래 내역의 날짜 처리
                        if "trades" in result_item:
                            for trade in result_item["trades"]:
                                if "entry_time" in trade:
                                    trade["entry_time"] = str(trade["entry_time"])
                                if "exit_time" in trade:
                                    trade["exit_time"] = str(trade["exit_time"])
            
            # JSON 파일로 저장
            with open(result_file_path, "w", encoding="utf-8") as f:
                json.dump(result_to_save, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"포트폴리오 백테스트 결과를 파일로 저장했습니다. 경로: {result_file_path}")
        except Exception as e:
            self.logger.error(f"포트폴리오 백테스트 결과 파일 저장 실패: {e}")
        
        return result_id

    def load_portfolio_backtest_result(self, result_id: str) -> Dict[str, Any]:
        """
        포트폴리오 백테스트 결과 불러오기
        
        Args:
            result_id: 결과 ID
            
        Returns:
            포트폴리오 백테스트 결과 딕셔너리
        """
        self.logger.info(f"포트폴리오 백테스트 결과 불러오기 중. ID: {result_id}")
        
        # 결과 파일 경로
        result_file_path = os.path.join(self.results_dir, f"{result_id}.json")
        
        # 파일이 존재하는지 확인
        if not os.path.exists(result_file_path):
            self.logger.warning(f"포트폴리오 백테스트 결과 파일이 존재하지 않습니다. 경로: {result_file_path}")
            
            # 데이터베이스에서 기본 정보만 불러오기
            backtest = self.session.query(Backtest).filter(Backtest.id == result_id).first()
            
            if backtest is None:
                self.logger.error(f"포트폴리오 백테스트 결과를 찾을 수 없습니다. ID: {result_id}")
                return {}
            
            # 기본 정보만 포함된 결과 반환
            return {
                "id": backtest.id,
                "portfolio_id": backtest.portfolio_id,
                "timeframe": backtest.timeframe,
                "start_date": backtest.start_date,
                "end_date": backtest.end_date,
                "initial_capital": backtest.initial_capital,
                "portfolio_performance": json.loads(backtest.performance_metrics) if backtest.performance_metrics else {},
                "created_at": backtest.created_at
            }
        
        # 파일에서 결과 불러오기
        try:
            with open(result_file_path, "r", encoding="utf-8") as f:
                result = json.load(f)
            
            # DataFrame 객체 복원
            if "combined_equity_curve" in result and isinstance(result["combined_equity_curve"], dict):
                equity_curve_dict = result["combined_equity_curve"]
                
                # 인덱스를 datetime으로 변환
                try:
                    index = pd.to_datetime(equity_curve_dict["index"])
                    data = equity_curve_dict["data"]
                    result["combined_equity_curve"] = pd.DataFrame(data, index=index)
                except Exception as e:
                    self.logger.error(f"자본 곡선 DataFrame 복원 실패: {e}")
                    result["combined_equity_curve"] = pd.DataFrame()
            
            # 개별 백테스트 결과의 DataFrame 객체 복원
            if "backtest_results" in result:
                for backtest_result in result["backtest_results"]:
                    if "result" in backtest_result and "equity_curve" in backtest_result["result"] and isinstance(backtest_result["result"]["equity_curve"], dict):
                        equity_curve_dict = backtest_result["result"]["equity_curve"]
                        
                        try:
                            index = pd.to_datetime(equity_curve_dict["index"])
                            data = equity_curve_dict["data"]
                            backtest_result["result"]["equity_curve"] = pd.DataFrame(data, index=index)
                        except Exception as e:
                            self.logger.error(f"개별 백테스트 자본 곡선 DataFrame 복원 실패: {e}")
                            backtest_result["result"]["equity_curve"] = pd.DataFrame()
            
            # 날짜 객체 복원
            try:
                if "start_date" in result and isinstance(result["start_date"], str):
                    result["start_date"] = pd.to_datetime(result["start_date"])
                if "end_date" in result and isinstance(result["end_date"], str):
                    result["end_date"] = pd.to_datetime(result["end_date"])
                
                # 개별 백테스트 결과의 날짜 객체 복원
                if "backtest_results" in result:
                    for backtest_result in result["backtest_results"]:
                        if "result" in backtest_result:
                            result_item = backtest_result["result"]
                            if "start_date" in result_item and isinstance(result_item["start_date"], str):
                                result_item["start_date"] = pd.to_datetime(result_item["start_date"])
                            if "end_date" in result_item and isinstance(result_item["end_date"], str):
                                result_item["end_date"] = pd.to_datetime(result_item["end_date"])
                            
                            # 거래 내역의 날짜 복원
                            if "trades" in result_item:
                                for trade in result_item["trades"]:
                                    if "entry_time" in trade and isinstance(trade["entry_time"], str):
                                        trade["entry_time"] = pd.to_datetime(trade["entry_time"])
                                    if "exit_time" in trade and isinstance(trade["exit_time"], str):
                                        trade["exit_time"] = pd.to_datetime(trade["exit_time"])
            except Exception as e:
                self.logger.error(f"날짜 객체 복원 실패: {e}")
            
            self.logger.info(f"포트폴리오 백테스트 결과를 성공적으로 불러왔습니다. ID: {result_id}")
            return result
        except Exception as e:
            self.logger.error(f"포트폴리오 백테스트 결과 불러오기 실패: {e}")
            return {}

    def list_backtest_results(self, filter_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        백테스트 결과 목록 조회
        
        Args:
            filter_params: 필터링 매개변수 (예: {"symbol": "KRW-BTC", "timeframe": "1h"})
            
        Returns:
            백테스트 결과 요약 목록
        """
        self.logger.info("백테스트 결과 목록 조회 중")
        
        # 필터링 매개변수가 없으면 빈 딕셔너리로 초기화
        if filter_params is None:
            filter_params = {}
        
        try:
            # 데이터베이스에서 백테스트 결과 조회
            query = self.session.query(Backtest)
            
            # 필터링 적용
            if "symbol" in filter_params:
                query = query.filter(Backtest.symbol == filter_params["symbol"])
            if "strategy_id" in filter_params:
                query = query.filter(Backtest.strategy_id == filter_params["strategy_id"])
            if "portfolio_id" in filter_params:
                query = query.filter(Backtest.portfolio_id == filter_params["portfolio_id"])
            if "timeframe" in filter_params:
                query = query.filter(Backtest.timeframe == filter_params["timeframe"])
            if "start_date" in filter_params:
                query = query.filter(Backtest.start_date >= filter_params["start_date"])
            if "end_date" in filter_params:
                query = query.filter(Backtest.end_date <= filter_params["end_date"])
            
            # 결과 조회
            backtest_records = query.all()
            
            # 결과 요약 목록 생성
            results = []
            for record in backtest_records:
                # 성과 지표 파싱
                performance_metrics = {}
                if record.performance_metrics:
                    try:
                        performance_metrics = json.loads(record.performance_metrics)
                    except Exception as e:
                        self.logger.error(f"성과 지표 파싱 실패: {e}")
                
                # 결과 요약 생성
                result_summary = {
                    "id": record.id,
                    "strategy_id": record.strategy_id,
                    "symbol": record.symbol,
                    "portfolio_id": record.portfolio_id,
                    "timeframe": record.timeframe,
                    "start_date": record.start_date,
                    "end_date": record.end_date,
                    "initial_capital": record.initial_capital,
                    "total_return_percent": performance_metrics.get("total_return_percent", 0.0),
                    "max_drawdown": performance_metrics.get("max_drawdown", 0.0),
                    "win_rate": performance_metrics.get("win_rate", 0.0),
                    "sharpe_ratio": performance_metrics.get("sharpe_ratio", 0.0),
                    "created_at": record.created_at
                }
                
                results.append(result_summary)
            
            self.logger.info(f"백테스트 결과 목록 조회 완료. {len(results)}개 결과 조회됨")
            return results
        except Exception as e:
            self.logger.error(f"백테스트 결과 목록 조회 실패: {e}")
            return []

    def compare_backtest_results(self, result_ids: List[str]) -> Dict[str, Any]:
        """
        백테스트 결과 비교
        
        Args:
            result_ids: 비교할 백테스트 결과 ID 목록
            
        Returns:
            비교 결과 딕셔너리
        """
        self.logger.info(f"백테스트 결과 비교 중. 결과 ID: {result_ids}")
        
        # 결과 불러오기
        results = []
        for result_id in result_ids:
            result = self.load_backtest_result(result_id)
            if result:
                results.append(result)
        
        # 결과가 없으면 빈 비교 결과 반환
        if not results:
            self.logger.warning("비교할 백테스트 결과가 없습니다.")
            return {
                "results": [],
                "comparison_metrics": {},
                "visualization": {}
            }
        
        # 비교 지표 계산
        comparison_metrics = self._calculate_comparison_metrics(results)
        
        # 시각화
        visualization = self._visualize_comparison(results)
        
        # 비교 결과 반환
        comparison_result = {
            "results": results,
            "comparison_metrics": comparison_metrics,
            "visualization": visualization
        }
        
        self.logger.info(f"백테스트 결과 비교 완료. {len(results)}개 결과 비교됨")
        return comparison_result

    def _calculate_comparison_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        백테스트 결과 비교 지표 계산
        
        Args:
            results: 백테스트 결과 목록
            
        Returns:
            비교 지표 딕셔너리
        """
        # 비교 지표 초기화
        comparison_metrics = {
            "total_return_percent": [],
            "max_drawdown": [],
            "win_rate": [],
            "sharpe_ratio": [],
            "sortino_ratio": [],
            "profit_factor": [],
            "trades_count": []
        }
        
        # 각 결과의 성과 지표 추출
        for result in results:
            metrics = result.get("performance_metrics", {})
            
            comparison_metrics["total_return_percent"].append({
                "id": result.get("id"),
                "symbol": result.get("symbol"),
                "value": metrics.get("total_return_percent", 0.0)
            })
            
            comparison_metrics["max_drawdown"].append({
                "id": result.get("id"),
                "symbol": result.get("symbol"),
                "value": metrics.get("max_drawdown", 0.0)
            })
            
            comparison_metrics["win_rate"].append({
                "id": result.get("id"),
                "symbol": result.get("symbol"),
                "value": metrics.get("win_rate", 0.0)
            })
            
            comparison_metrics["sharpe_ratio"].append({
                "id": result.get("id"),
                "symbol": result.get("symbol"),
                "value": metrics.get("sharpe_ratio", 0.0)
            })
            
            comparison_metrics["sortino_ratio"].append({
                "id": result.get("id"),
                "symbol": result.get("symbol"),
                "value": metrics.get("sortino_ratio", 0.0)
            })
            
            comparison_metrics["profit_factor"].append({
                "id": result.get("id"),
                "symbol": result.get("symbol"),
                "value": metrics.get("profit_factor", 0.0)
            })
            
            comparison_metrics["trades_count"].append({
                "id": result.get("id"),
                "symbol": result.get("symbol"),
                "value": metrics.get("trades_count", 0)
            })
        
        # 각 지표별로 정렬
        for metric_name in comparison_metrics:
            if metric_name in ["total_return_percent", "win_rate", "sharpe_ratio", "sortino_ratio", "profit_factor"]:
                # 높을수록 좋은 지표는 내림차순 정렬
                comparison_metrics[metric_name] = sorted(
                    comparison_metrics[metric_name],
                    key=lambda x: x["value"],
                    reverse=True
                )
            elif metric_name in ["max_drawdown"]:
                # 낮을수록 좋은 지표는 오름차순 정렬
                comparison_metrics[metric_name] = sorted(
                    comparison_metrics[metric_name],
                    key=lambda x: x["value"]
                )
            else:
                # 기타 지표는 내림차순 정렬
                comparison_metrics[metric_name] = sorted(
                    comparison_metrics[metric_name],
                    key=lambda x: x["value"],
                    reverse=True
                )
        
        return comparison_metrics

    def _visualize_comparison(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        백테스트 결과 비교 시각화
        
        Args:
            results: 백테스트 결과 목록
            
        Returns:
            시각화 결과 딕셔너리
        """
        # 시각화 라이브러리가 없는 경우
        if not VISUALIZATION_AVAILABLE:
            self.logger.warning("시각화 라이브러리가 설치되어 있지 않아 시각화를 수행할 수 없습니다.")
            return {}
        
        visualization = {}
        
        # 1. 자본 곡선 비교
        visualization["equity_curves"] = self._plot_equity_curves_comparison(results)
        
        # 2. 성과 지표 비교
        visualization["performance_metrics"] = self._plot_performance_metrics_comparison(results)
        
        # 3. 월별 수익률 비교
        visualization["monthly_returns"] = self._plot_monthly_returns_comparison(results)
        
        return visualization

    def _plot_equity_curves_comparison(self, results: List[Dict[str, Any]]) -> Figure:
        """
        자본 곡선 비교 시각화
        
        Args:
            results: 백테스트 결과 목록
            
        Returns:
            matplotlib Figure 객체
        """
        # 결과가 없는 경우
        if not results:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "비교할 결과가 없습니다.", ha='center', va='center')
            return fig
        
        # 그림 생성
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 각 결과의 자본 곡선 그리기
        for result in results:
            equity_curve = result.get("equity_curve")
            if equity_curve is not None and isinstance(equity_curve, pd.DataFrame) and "equity" in equity_curve.columns:
                # 초기 자본으로 정규화
                initial_equity = equity_curve["equity"].iloc[0]
                normalized_equity = equity_curve["equity"] / initial_equity * 100
                
                # 자본 곡선 그리기
                label = f"{result.get('symbol')} ({result.get('id')})"
                ax.plot(equity_curve.index, normalized_equity, label=label, linewidth=2)
        
        # 그래프 스타일 설정
        ax.set_title('백테스트 결과 자본 곡선 비교', fontsize=16)
        ax.set_xlabel('날짜', fontsize=12)
        ax.set_ylabel('정규화된 자본 (%)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')
        
        # x축 날짜 포맷 설정
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()
        
        plt.tight_layout()
        return fig

    def _plot_performance_metrics_comparison(self, results: List[Dict[str, Any]]) -> Figure:
        """
        성과 지표 비교 시각화
        
        Args:
            results: 백테스트 결과 목록
            
        Returns:
            matplotlib Figure 객체
        """
        # 결과가 없는 경우
        if not results:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "비교할 결과가 없습니다.", ha='center', va='center')
            return fig
        
        # 비교할 지표 선택
        metrics = ["total_return_percent", "max_drawdown", "win_rate", "sharpe_ratio"]
        
        # 그림 생성 (2x2 서브플롯)
        fig, axs = plt.subplots(2, 2, figsize=(15, 12))
        axs = axs.flatten()
        
        # 각 지표별로 막대 그래프 그리기
        for i, metric in enumerate(metrics):
            ax = axs[i]
            
            # 데이터 준비
            labels = [result.get("symbol", f"Result {j+1}") for j, result in enumerate(results)]
            values = [result.get("performance_metrics", {}).get(metric, 0.0) for result in results]
            
            # 막대 그래프 그리기
            bars = ax.bar(labels, values)
            
            # 막대 색상 설정 (수익률은 양수/음수에 따라 색상 변경)
            if metric == "total_return_percent":
                for j, bar in enumerate(bars):
                    if values[j] >= 0:
                        bar.set_color('green')
                    else:
                        bar.set_color('red')
            
            # 그래프 스타일 설정
            metric_names = {
                "total_return_percent": "총 수익률 (%)",
                "max_drawdown": "최대 손실폭 (%)",
                "win_rate": "승률 (%)",
                "sharpe_ratio": "샤프 비율"
            }
            
            ax.set_title(metric_names.get(metric, metric), fontsize=14)
            ax.set_ylabel("값", fontsize=12)
            ax.grid(True, alpha=0.3, axis='y')
            
            # 막대 위에 값 표시
            for j, v in enumerate(values):
                ax.text(j, v + (0.01 * max(values) if max(values) > 0 else 0.1), 
                        f'{v:.2f}', ha='center')
        
        plt.tight_layout()
        return fig

    def _plot_monthly_returns_comparison(self, results: List[Dict[str, Any]]) -> Figure:
        """
        월별 수익률 비교 시각화
        
        Args:
            results: 백테스트 결과 목록
            
        Returns:
            matplotlib Figure 객체
        """
        # 결과가 없는 경우
        if not results:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "비교할 결과가 없습니다.", ha='center', va='center')
            return fig
        
        # 그림 생성
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # 월별 수익률 계산 및 시각화
        for result in results:
            equity_curve = result.get("equity_curve")
            if equity_curve is not None and isinstance(equity_curve, pd.DataFrame) and "equity" in equity_curve.columns:
                # 월별 수익률 계산
                monthly_equity = equity_curve["equity"].resample('M').last()
                monthly_returns = monthly_equity.pct_change() * 100
                monthly_returns = monthly_returns.dropna()
                
                # 월별 수익률 그리기
                label = f"{result.get('symbol')} ({result.get('id')})"
                ax.plot(monthly_returns.index, monthly_returns, marker='o', linestyle='-', label=label)
        
        # 그래프 스타일 설정
        ax.set_title('월별 수익률 비교', fontsize=16)
        ax.set_xlabel('날짜', fontsize=12)
        ax.set_ylabel('월별 수익률 (%)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')
        
        # x축 날짜 포맷 설정
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        fig.autofmt_xdate()
        
        # 0% 라인 추가
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        plt.tight_layout()
        return fig

    def delete_backtest_result(self, result_id: str) -> bool:
        """
        백테스트 결과 삭제
        
        Args:
            result_id: 결과 ID
            
        Returns:
            삭제 성공 여부
        """
        self.logger.info(f"백테스트 결과 삭제 중. ID: {result_id}")
        
        success = True
        
        # 데이터베이스에서 삭제
        try:
            backtest = self.session.query(Backtest).filter(Backtest.id == result_id).first()
            
            if backtest is None:
                self.logger.warning(f"삭제할 백테스트 결과를 찾을 수 없습니다. ID: {result_id}")
                success = False
            else:
                self.session.delete(backtest)
                self.session.commit()
                self.logger.info(f"백테스트 결과를 데이터베이스에서 삭제했습니다. ID: {result_id}")
        except Exception as e:
            self.logger.error(f"백테스트 결과 데이터베이스 삭제 실패: {e}")
            self.session.rollback()
            success = False
        
        # 파일 삭제
        try:
            result_file_path = os.path.join(self.results_dir, f"{result_id}.json")
            
            if os.path.exists(result_file_path):
                os.remove(result_file_path)
                self.logger.info(f"백테스트 결과 파일을 삭제했습니다. 경로: {result_file_path}")
            else:
                self.logger.warning(f"삭제할 백테스트 결과 파일이 존재하지 않습니다. 경로: {result_file_path}")
        except Exception as e:
            self.logger.error(f"백테스트 결과 파일 삭제 실패: {e}")
            success = False
        
        return success