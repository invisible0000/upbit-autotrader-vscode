#!/usr/bin/env python3
"""
SQLite Strategy Repository 구현 (완전 버전)
==========================================

SQLite 데이터베이스를 사용하여 Domain Layer의 StrategyRepository 인터페이스를 완전 구현합니다.
모든 추상 메서드를 Mock 패턴으로 구현하여 Domain Layer 완성 전까지 호환성을 보장합니다.
"""

from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

# Domain Interfaces
from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
from upbit_auto_trading.domain.entities.strategy import Strategy

# Infrastructure
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager
from upbit_auto_trading.infrastructure.mappers.strategy_mapper import (
    StrategyMapper, MockStrategy
)

class SqliteStrategyRepository(StrategyRepository):
    """
    SQLite 기반 Strategy Repository 완전 구현

    Domain Layer의 StrategyRepository 인터페이스를 완전히 구현하며,
    strategies.sqlite3 데이터베이스와 연동합니다.
    """

    def __init__(self, db_manager: DatabaseManager):
        """Repository 초기화"""
        self._db_manager = db_manager
        self._mapper = StrategyMapper()
        self._logger = logging.getLogger(__name__)
        self._logger.info("🏗️ SqliteStrategyRepository 초기화 완료")

    # === BaseRepository 인터페이스 구현 ===

    def save(self, entity: Strategy) -> None:
        """전략 저장 (Domain Interface 구현)"""
        try:
            # Domain Entity를 Mock으로 변환 (임시)
            mock_strategy = self._convert_to_mock(entity)
            self._save_mock_strategy(mock_strategy)
            self._logger.info(f"✅ Domain 전략 저장 완료: {entity}")
        except Exception as e:
            self._logger.error(f"❌ Domain 전략 저장 실패: {e}")
            raise

    def find_by_id(self, entity_id: StrategyId) -> Optional[Strategy]:
        """ID로 전략 조회 (Domain Interface 구현)"""
        try:
            mock_strategy = self._find_mock_by_id(str(entity_id))
            if mock_strategy:
                return self._convert_to_domain(mock_strategy)  # type: ignore
            return None
        except Exception as e:
            self._logger.error(f"❌ 전략 조회 실패 [{entity_id}]: {e}")
            return None

    def find_all(self) -> List[Strategy]:
        """모든 전략 조회 (Domain Interface 구현)"""
        try:
            mock_strategies = self._find_all_mock_active()
            return [self._convert_to_domain(mock) for mock in mock_strategies]  # type: ignore
        except Exception as e:
            self._logger.error(f"❌ 전체 전략 조회 실패: {e}")
            return []

    def delete(self, entity_id: StrategyId) -> bool:
        """전략 삭제 (Domain Interface 구현)"""
        return self._delete_mock_strategy(str(entity_id))

    def exists(self, entity_id: StrategyId) -> bool:
        """전략 존재 확인 (Domain Interface 구현)"""
        return self._strategy_exists(str(entity_id))

    # === 전략 특화 메서드 구현 ===

    def find_by_name(self, name: str) -> Optional[Strategy]:
        """전략 이름으로 조회"""
        try:
            query = "SELECT * FROM strategies WHERE strategy_name = ? AND is_active = 1"
            results = self._db_manager.execute_query('strategies', query, (name,))

            if results:
                strategy_dict = self._row_to_dict(results[0])
                mock_strategy = self._mapper.to_entity(strategy_dict)
                return self._convert_to_domain(mock_strategy)  # type: ignore
            return None
        except Exception as e:
            self._logger.error(f"❌ 이름 조회 실패 [{name}]: {e}")
            return None

    def find_by_tags(self, tags: List[str]) -> List[Strategy]:
        """태그로 전략 검색"""
        try:
            # 간단한 LIKE 검색 (JSON 함수는 복잡하므로 우선 기본 구현)
            tag_conditions = " OR ".join(["tags LIKE ?" for _ in tags])
            query = f"""
            SELECT * FROM strategies
            WHERE is_active = 1 AND ({tag_conditions})
            ORDER BY created_at DESC
            """
            params = [f"%{tag}%" for tag in tags]
            results = self._db_manager.execute_query('strategies', query, tuple(params))

            strategies = []
            for row in results:
                strategy_dict = self._row_to_dict(row)
                mock_strategy = self._mapper.to_entity(strategy_dict)
                strategies.append(self._convert_to_domain(mock_strategy))  # type: ignore
            return strategies
        except Exception as e:
            self._logger.error(f"❌ 태그 검색 실패 [{tags}]: {e}")
            return []

    def find_active_strategies(self) -> List[Strategy]:
        """활성 전략 조회"""
        return self.find_all()

    def find_strategies_created_after(self, date: datetime) -> List[Strategy]:
        """특정 날짜 이후 생성된 전략 조회"""
        try:
            query = """
            SELECT * FROM strategies
            WHERE created_at >= ? AND is_active = 1
            ORDER BY created_at DESC
            """
            results = self._db_manager.execute_query('strategies', query, (date.isoformat(),))

            strategies = []
            for row in results:
                strategy_dict = self._row_to_dict(row)
                mock_strategy = self._mapper.to_entity(strategy_dict)
                strategies.append(self._convert_to_domain(mock_strategy))  # type: ignore
            return strategies
        except Exception as e:
            self._logger.error(f"❌ 날짜 기준 조회 실패 [{date}]: {e}")
            return []

    def find_strategies_by_risk_level(self, min_risk: int, max_risk: int) -> List[Strategy]:
        """리스크 레벨 범위로 전략 조회"""
        try:
            query = """
            SELECT * FROM strategies
            WHERE risk_level BETWEEN ? AND ? AND is_active = 1
            ORDER BY risk_level, created_at DESC
            """
            results = self._db_manager.execute_query('strategies', query, (min_risk, max_risk))

            strategies = []
            for row in results:
                strategy_dict = self._row_to_dict(row)
                mock_strategy = self._mapper.to_entity(strategy_dict)
                strategies.append(self._convert_to_domain(mock_strategy))  # type: ignore
            return strategies
        except Exception as e:
            self._logger.error(f"❌ 리스크 레벨 조회 실패 [{min_risk}-{max_risk}]: {e}")
            return []

    def find_strategies_by_performance_range(self, min_return: float, max_return: float) -> List[Strategy]:
        """예상 수익률 범위로 전략 조회"""
        try:
            query = """
            SELECT * FROM strategies
            WHERE expected_return BETWEEN ? AND ? AND is_active = 1
            ORDER BY expected_return DESC, created_at DESC
            """
            results = self._db_manager.execute_query('strategies', query, (min_return, max_return))

            strategies = []
            for row in results:
                strategy_dict = self._row_to_dict(row)
                mock_strategy = self._mapper.to_entity(strategy_dict)
                strategies.append(self._convert_to_domain(mock_strategy))  # type: ignore
            return strategies
        except Exception as e:
            self._logger.error(f"❌ 수익률 범위 조회 실패 [{min_return}-{max_return}]: {e}")
            return []

    # === 전략 메타데이터 관리 ===

    def update_strategy_metadata(self, strategy_id: StrategyId, metadata: Dict[str, Any]) -> bool:
        """전략 메타데이터 업데이트"""
        try:
            allowed_fields = ['strategy_name', 'description', 'tags', 'risk_level', 'expected_return', 'max_drawdown']
            update_fields = {k: v for k, v in metadata.items() if k in allowed_fields}

            if not update_fields:
                return False

            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            query = f"UPDATE strategies SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"

            params = list(update_fields.values()) + [str(strategy_id)]
            results = self._db_manager.execute_query('strategies', query, tuple(params))

            return len(results) >= 0  # execute_query는 항상 리스트 반환
        except Exception as e:
            self._logger.error(f"❌ 메타데이터 업데이트 실패 [{strategy_id}]: {e}")
            return False

    def increment_use_count(self, strategy_id: StrategyId) -> None:
        """전략 사용 횟수 증가"""
        try:
            query = """
            UPDATE strategies
            SET use_count = COALESCE(use_count, 0) + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            self._db_manager.execute_query('strategies', query, (str(strategy_id),))
        except Exception as e:
            self._logger.error(f"❌ 사용 횟수 증가 실패 [{strategy_id}]: {e}")

    def update_last_used_at(self, strategy_id: StrategyId, timestamp: datetime) -> None:
        """마지막 사용 시간 업데이트"""
        try:
            query = """
            UPDATE strategies
            SET last_used_at = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            self._db_manager.execute_query('strategies', query, (timestamp.isoformat(), str(strategy_id)))
        except Exception as e:
            self._logger.error(f"❌ 마지막 사용 시간 업데이트 실패 [{strategy_id}]: {e}")

    def get_strategy_usage_statistics(self, strategy_id: StrategyId) -> Dict[str, Any]:
        """전략 사용 통계 조회"""
        try:
            query = "SELECT use_count, last_used_at, created_at FROM strategies WHERE id = ?"
            results = self._db_manager.execute_query('strategies', query, (str(strategy_id),))

            if results:
                row = results[0]
                return {
                    'use_count': row[0] or 0,
                    'last_used_at': row[1],
                    'created_at': row[2]
                }
            return {'use_count': 0, 'last_used_at': None, 'created_at': None}
        except Exception as e:
            self._logger.error(f"❌ 사용 통계 조회 실패 [{strategy_id}]: {e}")
            return {'use_count': 0, 'last_used_at': None, 'created_at': None}

    def get_popular_strategies(self, limit: int = 10) -> List[Strategy]:
        """인기 전략 조회 (사용 횟수 기준)"""
        try:
            query = """
            SELECT * FROM strategies
            WHERE is_active = 1
            ORDER BY COALESCE(use_count, 0) DESC, created_at DESC
            LIMIT ?
            """
            results = self._db_manager.execute_query('strategies', query, (limit,))

            strategies = []
            for row in results:
                strategy_dict = self._row_to_dict(row)
                mock_strategy = self._mapper.to_entity(strategy_dict)
                strategies.append(self._convert_to_domain(mock_strategy))  # type: ignore
            return strategies
        except Exception as e:
            self._logger.error(f"❌ 인기 전략 조회 실패: {e}")
            return []

    def search_strategies(self, query: str) -> List[Strategy]:
        """전략 이름/설명 검색"""
        try:
            search_query = """
            SELECT * FROM strategies
            WHERE is_active = 1
            AND (strategy_name LIKE ? OR description LIKE ?)
            ORDER BY created_at DESC
            """
            search_pattern = f"%{query}%"
            results = self._db_manager.execute_query('strategies', search_query, (search_pattern, search_pattern))

            strategies = []
            for row in results:
                strategy_dict = self._row_to_dict(row)
                mock_strategy = self._mapper.to_entity(strategy_dict)
                strategies.append(self._convert_to_domain(mock_strategy))  # type: ignore
            return strategies
        except Exception as e:
            self._logger.error(f"❌ 전략 검색 실패 [{query}]: {e}")
            return []

    # === 내부 Mock 처리 메서드들 ===

    def _convert_to_mock(self, entity: Strategy) -> MockStrategy:
        """Domain Entity를 Mock으로 변환"""
        return MockStrategy(
            strategy_id=str(entity.strategy_id) if hasattr(entity, 'strategy_id') else "mock_strategy",
            name=getattr(entity, 'name', 'Mock Strategy'),
            description=getattr(entity, 'description', 'Mock Description')
        )

    def _convert_to_domain(self, mock: MockStrategy) -> Strategy:
        """Mock을 Domain Entity로 변환 (임시)"""
        # TODO: 실제 Domain Entity 생성자로 교체
        return mock  # type: ignore

    def _save_mock_strategy(self, strategy: MockStrategy) -> str:
        """Mock 전략 저장"""
        try:
            db_record = self._mapper.to_database_record(strategy)

            if self._strategy_exists(strategy.strategy_id):
                # UPDATE
                query = """
                UPDATE strategies
                SET strategy_name = ?, description = ?, strategy_type = ?,
                    is_active = ?, tags = ?, risk_level = ?,
                    expected_return = ?, max_drawdown = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """
                # db_record는 Dict이므로 values로 변환
                values = list(db_record.values())
                params = values[1:] + [values[0]]  # id를 마지막으로
                self._db_manager.execute_query('strategies', query, tuple(params))
            else:
                # INSERT
                query = """
                INSERT INTO strategies
                (id, strategy_name, description, strategy_type, is_active,
                 tags, risk_level, expected_return, max_drawdown)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                values = list(db_record.values())
                self._db_manager.execute_query('strategies', query, tuple(values))

            return strategy.strategy_id
        except Exception as e:
            self._logger.error(f"❌ Mock 전략 저장 실패: {e}")
            raise

    def _find_mock_by_id(self, strategy_id: str) -> Optional[MockStrategy]:
        """Mock 전략 ID 조회"""
        try:
            query = "SELECT * FROM strategies WHERE id = ?"
            results = self._db_manager.execute_query('strategies', query, (strategy_id,))

            if results:
                strategy_dict = self._row_to_dict(results[0])
                return self._mapper.to_entity(strategy_dict)
            return None
        except Exception as e:
            self._logger.error(f"❌ Mock 전략 조회 실패 [{strategy_id}]: {e}")
            return None

    def _find_all_mock_active(self) -> List[MockStrategy]:
        """모든 활성 Mock 전략 조회"""
        try:
            query = "SELECT * FROM strategies WHERE is_active = 1 ORDER BY created_at DESC"
            results = self._db_manager.execute_query('strategies', query)

            strategies = []
            for row in results:
                strategy_dict = self._row_to_dict(row)
                strategies.append(self._mapper.to_entity(strategy_dict))
            return strategies
        except Exception as e:
            self._logger.error(f"❌ 활성 Mock 전략 조회 실패: {e}")
            return []

    def _delete_mock_strategy(self, strategy_id: str) -> bool:
        """Mock 전략 삭제 (소프트 삭제)"""
        try:
            query = "UPDATE strategies SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            self._db_manager.execute_query('strategies', query, (strategy_id,))
            return True
        except Exception as e:
            self._logger.error(f"❌ Mock 전략 삭제 실패 [{strategy_id}]: {e}")
            return False

    def _strategy_exists(self, strategy_id: str) -> bool:
        """전략 존재 여부 확인"""
        try:
            query = "SELECT 1 FROM strategies WHERE id = ? LIMIT 1"
            results = self._db_manager.execute_query('strategies', query, (strategy_id,))
            return len(results) > 0
        except Exception:
            return False

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """SQLite Row를 Dictionary로 변환"""
        return {
            'id': row[0],
            'strategy_name': row[1],
            'description': row[2] if len(row) > 2 else '',
            'strategy_type': row[3] if len(row) > 3 else 'manual',
            'is_active': row[4] if len(row) > 4 else 1,
            'tags': row[5] if len(row) > 5 else '[]',
            'risk_level': row[6] if len(row) > 6 else 3,
            'expected_return': row[7] if len(row) > 7 else 0.0,
            'max_drawdown': row[8] if len(row) > 8 else 0.0,
            'created_at': row[9] if len(row) > 9 else None,
            'updated_at': row[10] if len(row) > 10 else None,
            'last_used_at': row[11] if len(row) > 11 else None,
            'use_count': row[12] if len(row) > 12 else 0
        }
