#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
스크리너 결과 처리

스크리닝 결과를 처리하고 저장하는 기능을 제공합니다.
"""

import os
import logging
import pandas as pd
import json
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from upbit_auto_trading.data_layer.storage.database_manager import get_database_manager

logger = logging.getLogger(__name__)

class ScreenerResult:
    """스크리닝 결과 처리 및 저장을 담당하는 클래스"""
    
    def __init__(self):
        """ScreenerResult 초기화"""
        self.db_manager = get_database_manager()
        self._ensure_tables()
    
    def _ensure_tables(self):
        """필요한 테이블이 존재하는지 확인하고, 없으면 생성합니다."""
        engine = self.db_manager.get_engine()
        
        # 스크리닝 결과 테이블 생성
        screening_result_query = """
        CREATE TABLE IF NOT EXISTS screening_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            criteria JSON NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 스크리닝 결과 상세 테이블 생성
        screening_detail_query = """
        CREATE TABLE IF NOT EXISTS screening_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_id INTEGER NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            name VARCHAR(100),
            current_price FLOAT NOT NULL,
            volume_24h FLOAT,
            matched_criteria JSON NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (result_id) REFERENCES screening_results(id) ON DELETE CASCADE
        )
        """
        
        # 인덱스 생성
        screening_detail_index_query = """
        CREATE INDEX IF NOT EXISTS idx_screening_details_result_id ON screening_details(result_id)
        """
        
        try:
            with engine.connect() as conn:
                conn.execute(text(screening_result_query))
                conn.execute(text(screening_detail_query))
                conn.execute(text(screening_detail_index_query))
                conn.commit()
            logger.info("스크리너 결과 테이블이 생성되었습니다.")
        except Exception as e:
            logger.exception(f"테이블 생성 중 오류가 발생했습니다: {e}")
            raise
    
    def save_screening_result(self, name: str, description: str, criteria: List[Dict], results: List[Dict]) -> int:
        """스크리닝 결과를 저장합니다.
        
        Args:
            name: 스크리닝 결과 이름
            description: 스크리닝 결과 설명
            criteria: 스크리닝 기준 목록
            results: 스크리닝 결과 목록
            
        Returns:
            int: 저장된 결과 ID
        """
        try:
            engine = self.db_manager.get_engine()
            
            # 스크리닝 결과 저장
            insert_result_query = """
            INSERT INTO screening_results (name, description, criteria, created_at)
            VALUES (:name, :description, :criteria, :created_at)
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(insert_result_query), {
                    'name': name,
                    'description': description,
                    'criteria': json.dumps(criteria),
                    'created_at': datetime.now()
                })
                conn.commit()
                
                result_id = result.lastrowid
            
            # 스크리닝 결과 상세 저장
            if results and result_id:
                self._save_screening_details(result_id, results)
            
            logger.info(f"스크리닝 결과가 저장되었습니다. ID: {result_id}")
            return result_id
        
        except SQLAlchemyError as e:
            logger.exception(f"스크리닝 결과 저장 중 오류가 발생했습니다: {e}")
            return 0
    
    def _save_screening_details(self, result_id: int, results: List[Dict]) -> bool:
        """스크리닝 결과 상세 정보를 저장합니다.
        
        Args:
            result_id: 스크리닝 결과 ID
            results: 스크리닝 결과 목록
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            engine = self.db_manager.get_engine()
            
            # 스크리닝 결과 상세 저장
            insert_detail_query = """
            INSERT INTO screening_details 
            (result_id, symbol, name, current_price, volume_24h, matched_criteria, created_at)
            VALUES (:result_id, :symbol, :name, :current_price, :volume_24h, :matched_criteria, :created_at)
            """
            
            details = []
            for result in results:
                details.append({
                    'result_id': result_id,
                    'symbol': result.get('symbol', ''),
                    'name': result.get('name', ''),
                    'current_price': result.get('current_price', 0),
                    'volume_24h': result.get('volume_24h', 0),
                    'matched_criteria': json.dumps(result.get('matched_criteria', [])),
                    'created_at': datetime.now()
                })
            
            with engine.connect() as conn:
                conn.execute(text(insert_detail_query), details)
                conn.commit()
            
            logger.info(f"스크리닝 결과 상세 정보가 저장되었습니다. 결과 ID: {result_id}, 항목 수: {len(details)}")
            return True
        
        except SQLAlchemyError as e:
            logger.exception(f"스크리닝 결과 상세 정보 저장 중 오류가 발생했습니다: {e}")
            return False
    
    def get_screening_results(self, limit: int = 10, offset: int = 0) -> List[Dict]:
        """저장된 스크리닝 결과 목록을 조회합니다.
        
        Args:
            limit: 조회할 결과 수
            offset: 조회 시작 위치
            
        Returns:
            List[Dict]: 스크리닝 결과 목록
        """
        try:
            engine = self.db_manager.get_engine()
            
            # 스크리닝 결과 조회
            query = """
            SELECT id, name, description, criteria, created_at,
                   (SELECT COUNT(*) FROM screening_details WHERE result_id = screening_results.id) as coin_count
            FROM screening_results
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(query), {'limit': limit, 'offset': offset})
                rows = result.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'criteria': json.loads(row[3]),
                    'created_at': row[4],
                    'coin_count': row[5]
                })
            
            return results
        
        except SQLAlchemyError as e:
            logger.exception(f"스크리닝 결과 조회 중 오류가 발생했습니다: {e}")
            return []
    
    def get_screening_result(self, result_id: int) -> Dict:
        """특정 스크리닝 결과를 조회합니다.
        
        Args:
            result_id: 스크리닝 결과 ID
            
        Returns:
            Dict: 스크리닝 결과 정보
        """
        try:
            engine = self.db_manager.get_engine()
            
            # 스크리닝 결과 조회
            query = """
            SELECT id, name, description, criteria, created_at
            FROM screening_results
            WHERE id = :result_id
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(query), {'result_id': result_id})
                row = result.fetchone()
            
            if not row:
                logger.warning(f"스크리닝 결과를 찾을 수 없습니다. ID: {result_id}")
                return {}
            
            # 스크리닝 결과 상세 조회
            details_query = """
            SELECT symbol, name, current_price, volume_24h, matched_criteria
            FROM screening_details
            WHERE result_id = :result_id
            """
            
            with engine.connect() as conn:
                details_result = conn.execute(text(details_query), {'result_id': result_id})
                details_rows = details_result.fetchall()
            
            details = []
            for detail_row in details_rows:
                details.append({
                    'symbol': detail_row[0],
                    'name': detail_row[1],
                    'current_price': detail_row[2],
                    'volume_24h': detail_row[3],
                    'matched_criteria': json.loads(detail_row[4])
                })
            
            return {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'criteria': json.loads(row[3]),
                'created_at': row[4],
                'details': details
            }
        
        except SQLAlchemyError as e:
            logger.exception(f"스크리닝 결과 조회 중 오류가 발생했습니다: {e}")
            return {}
    
    def delete_screening_result(self, result_id: int) -> bool:
        """스크리닝 결과를 삭제합니다.
        
        Args:
            result_id: 스크리닝 결과 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            engine = self.db_manager.get_engine()
            
            # 스크리닝 결과 삭제 (외래 키 제약으로 인해 상세 정보도 함께 삭제됨)
            query = """
            DELETE FROM screening_results
            WHERE id = :result_id
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(query), {'result_id': result_id})
                conn.commit()
                
                if result.rowcount > 0:
                    logger.info(f"스크리닝 결과가 삭제되었습니다. ID: {result_id}")
                    return True
                else:
                    logger.warning(f"삭제할 스크리닝 결과를 찾을 수 없습니다. ID: {result_id}")
                    return False
        
        except SQLAlchemyError as e:
            logger.exception(f"스크리닝 결과 삭제 중 오류가 발생했습니다: {e}")
            return False
    
    def filter_screening_results(self, criteria: Dict) -> List[Dict]:
        """스크리닝 결과를 필터링합니다.
        
        Args:
            criteria: 필터링 기준
            
        Returns:
            List[Dict]: 필터링된 스크리닝 결과 목록
        """
        try:
            engine = self.db_manager.get_engine()
            
            # 기본 쿼리
            query = """
            SELECT sr.id, sr.name, sr.description, sr.criteria, sr.created_at,
                   COUNT(sd.id) as coin_count
            FROM screening_results sr
            JOIN screening_details sd ON sr.id = sd.result_id
            WHERE 1=1
            """
            
            params = {}
            
            # 이름 필터
            if 'name' in criteria:
                query += " AND sr.name LIKE :name"
                params['name'] = f"%{criteria['name']}%"
            
            # 날짜 범위 필터
            if 'start_date' in criteria:
                query += " AND sr.created_at >= :start_date"
                params['start_date'] = criteria['start_date']
            
            if 'end_date' in criteria:
                query += " AND sr.created_at <= :end_date"
                params['end_date'] = criteria['end_date']
            
            # 코인 심볼 필터
            if 'symbol' in criteria:
                query += " AND sd.symbol = :symbol"
                params['symbol'] = criteria['symbol']
            
            # 그룹화 및 정렬
            query += " GROUP BY sr.id ORDER BY sr.created_at DESC"
            
            # 페이지네이션
            if 'limit' in criteria:
                query += " LIMIT :limit"
                params['limit'] = criteria['limit']
                
                if 'offset' in criteria:
                    query += " OFFSET :offset"
                    params['offset'] = criteria['offset']
            
            with engine.connect() as conn:
                result = conn.execute(text(query), params)
                rows = result.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'criteria': json.loads(row[3]),
                    'created_at': row[4],
                    'coin_count': row[5]
                })
            
            return results
        
        except SQLAlchemyError as e:
            logger.exception(f"스크리닝 결과 필터링 중 오류가 발생했습니다: {e}")
            return []
    
    def sort_screening_details(self, result_id: int, sort_by: str = 'current_price', order: str = 'desc') -> List[Dict]:
        """스크리닝 결과 상세 정보를 정렬합니다.
        
        Args:
            result_id: 스크리닝 결과 ID
            sort_by: 정렬 기준 ('current_price', 'volume_24h', 'symbol')
            order: 정렬 순서 ('asc', 'desc')
            
        Returns:
            List[Dict]: 정렬된 스크리닝 결과 상세 정보 목록
        """
        try:
            engine = self.db_manager.get_engine()
            
            # 정렬 기준 검증
            valid_sort_columns = ['current_price', 'volume_24h', 'symbol', 'name']
            if sort_by not in valid_sort_columns:
                sort_by = 'current_price'
            
            # 정렬 순서 검증
            order = order.lower()
            if order not in ['asc', 'desc']:
                order = 'desc'
            
            # 스크리닝 결과 상세 조회 및 정렬
            query = f"""
            SELECT symbol, name, current_price, volume_24h, matched_criteria
            FROM screening_details
            WHERE result_id = :result_id
            ORDER BY {sort_by} {order}
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(query), {'result_id': result_id})
                rows = result.fetchall()
            
            details = []
            for row in rows:
                details.append({
                    'symbol': row[0],
                    'name': row[1],
                    'current_price': row[2],
                    'volume_24h': row[3],
                    'matched_criteria': json.loads(row[4])
                })
            
            return details
        
        except SQLAlchemyError as e:
            logger.exception(f"스크리닝 결과 상세 정보 정렬 중 오류가 발생했습니다: {e}")
            return []
    
    def export_to_csv(self, result_id: int, file_path: str = None) -> str:
        """스크리닝 결과를 CSV 파일로 내보냅니다.
        
        Args:
            result_id: 스크리닝 결과 ID
            file_path: 저장할 파일 경로 (None인 경우 자동 생성)
            
        Returns:
            str: 저장된 파일 경로
        """
        try:
            # 스크리닝 결과 조회
            result = self.get_screening_result(result_id)
            
            if not result or 'details' not in result or not result['details']:
                logger.warning(f"내보낼 스크리닝 결과가 없습니다. ID: {result_id}")
                return ""
            
            # 데이터프레임 생성
            df = pd.DataFrame(result['details'])
            
            # matched_criteria 컬럼 처리
            df['matched_criteria'] = df['matched_criteria'].apply(lambda x: ', '.join(x))
            
            # 파일 경로 생성
            if not file_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"screening_result_{result_id}_{timestamp}.csv"
                
                # 데이터 디렉토리 확인 및 생성
                data_dir = os.path.join(os.getcwd(), 'data', 'exports')
                os.makedirs(data_dir, exist_ok=True)
                
                file_path = os.path.join(data_dir, file_name)
            
            # CSV 파일로 저장
            df.to_csv(file_path, index=False, encoding='utf-8-sig')  # UTF-8 with BOM for Excel
            
            logger.info(f"스크리닝 결과가 CSV 파일로 내보내졌습니다: {file_path}")
            return file_path
        
        except Exception as e:
            logger.exception(f"스크리닝 결과 내보내기 중 오류가 발생했습니다: {e}")
            return ""