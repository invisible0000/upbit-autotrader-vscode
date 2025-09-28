#!/usr/bin/env python3
"""
SQLite 기반 보안 키 Repository 구현
================================

settings.sqlite3 데이터베이스의 secure_keys 테이블을 위한 Repository 구현입니다.
API 키 암호화에 사용되는 키와 기타 보안 관련 데이터의 영속화를 담당합니다.

Features:
- 암호화 키 CRUD 연산 (sqlite3 기반)
- 키 타입별 UNIQUE 제약조건 지원
- 안전한 키 교체 (INSERT OR REPLACE)
- 메타데이터 조회 (생성/수정 시간)
- DDD Repository 패턴 준수

Security:
- BLOB 타입으로 키 데이터 안전 저장
- 트랜잭션 기반 원자적 연산
- SQL 인젝션 방지 (파라미터화 쿼리)
- 에러 처리 및 로깅

Database Schema:
- Table: secure_keys
- Columns: id, key_type(UNIQUE), key_value(BLOB), created_at, updated_at
- Indexes: idx_secure_keys_type (key_type)
"""

import logging
from typing import Optional, List, Dict, Any

from upbit_auto_trading.domain.repositories.secure_keys_repository import SecureKeysRepository
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager


class SqliteSecureKeysRepository(SecureKeysRepository):
    """SQLite 기반 보안 키 Repository 구현"""

    def __init__(self, db_manager: DatabaseManager):
        """
        Repository 초기화

        Args:
            db_manager (DatabaseManager): 데이터베이스 연결 관리자
        """
        self._db = db_manager
        self._logger = logging.getLogger(__name__)

    def save_key(self, key_type: str, key_data: bytes) -> bool:
        """
        보안 키 저장 (기존 키 교체)

        INSERT OR REPLACE를 사용하여 기존 키가 있으면 교체하고,
        없으면 새로 생성합니다.

        Args:
            key_type (str): 키 타입 (예: "encryption")
            key_data (bytes): 키 데이터

        Returns:
            bool: 저장 성공 여부

        Raises:
            ValueError: 잘못된 입력 데이터
        """
        if not key_type or not isinstance(key_type, str):
            raise ValueError("키 타입이 올바르지 않습니다")

        if not key_data or not isinstance(key_data, bytes):
            raise ValueError("키 데이터가 올바르지 않습니다")

        try:
            with self._db.get_connection('settings') as conn:
                cursor = conn.cursor()

                # INSERT OR REPLACE로 안전한 키 저장/교체
                cursor.execute("""
                    INSERT OR REPLACE INTO secure_keys (key_type, key_value)
                    VALUES (?, ?)
                """, (key_type, key_data))

                self._logger.info(f"✅ 보안 키 저장 완료: {key_type}")
                return True

        except Exception as e:
            self._logger.error(f"❌ 보안 키 저장 실패 ({key_type}): {e}")
            return False

    def load_key(self, key_type: str) -> Optional[bytes]:
        """
        키 타입으로 보안 키 조회

        Args:
            key_type (str): 키 타입

        Returns:
            Optional[bytes]: 키 데이터 (없으면 None)
        """
        if not key_type or not isinstance(key_type, str):
            raise ValueError("키 타입이 올바르지 않습니다")

        try:
            with self._db.get_connection('settings') as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT key_value FROM secure_keys
                    WHERE key_type = ?
                """, (key_type,))

                result = cursor.fetchone()

                if result:
                    self._logger.debug(f"✅ 보안 키 로드 완료: {key_type}")
                    return result[0]  # BLOB 데이터 반환
                else:
                    self._logger.debug(f"🔑 보안 키 없음: {key_type}")
                    return None

        except Exception as e:
            self._logger.error(f"❌ 보안 키 로드 실패 ({key_type}): {e}")
            raise

    def delete_key(self, key_type: str) -> bool:
        """
        키 타입으로 보안 키 삭제

        Args:
            key_type (str): 삭제할 키 타입

        Returns:
            bool: 삭제 성공 여부 (없어도 True)
        """
        if not key_type or not isinstance(key_type, str):
            raise ValueError("키 타입이 올바르지 않습니다")

        try:
            with self._db.get_connection('settings') as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    DELETE FROM secure_keys WHERE key_type = ?
                """, (key_type,))

                deleted_count = cursor.rowcount

                if deleted_count > 0:
                    self._logger.info(f"✅ 보안 키 삭제 완료: {key_type} ({deleted_count}개)")
                else:
                    self._logger.debug(f"🔑 삭제할 키 없음: {key_type}")

                return True

        except Exception as e:
            self._logger.error(f"❌ 보안 키 삭제 실패 ({key_type}): {e}")
            return False

    def key_exists(self, key_type: str) -> bool:
        """
        키 존재 여부 확인

        Args:
            key_type (str): 확인할 키 타입

        Returns:
            bool: 키 존재 여부
        """
        try:
            key_data = self.load_key(key_type)
            return key_data is not None
        except Exception:
            return False

    def list_key_types(self) -> List[str]:
        """
        저장된 모든 키 타입 목록 조회

        Returns:
            List[str]: 키 타입 목록
        """
        try:
            with self._db.get_connection('settings') as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT key_type FROM secure_keys
                    ORDER BY key_type
                """)

                rows = cursor.fetchall()
                key_types = [row[0] for row in rows]

                self._logger.debug(f"✅ 키 타입 목록 조회: {key_types}")
                return key_types

        except Exception as e:
            self._logger.error(f"❌ 키 타입 목록 조회 실패: {e}")
            return []

    def get_key_metadata(self, key_type: str) -> Optional[Dict[str, Any]]:
        """
        키 메타데이터 조회 (생성/수정 시간 등)

        Args:
            key_type (str): 키 타입

        Returns:
            Optional[Dict[str, Any]]: 메타데이터 (없으면 None)
        """
        if not key_type or not isinstance(key_type, str):
            raise ValueError("키 타입이 올바르지 않습니다")

        try:
            with self._db.get_connection('settings') as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        id,
                        key_type,
                        LENGTH(key_value) as key_size,
                        created_at,
                        updated_at
                    FROM secure_keys
                    WHERE key_type = ?
                """, (key_type,))

                result = cursor.fetchone()

                if result:
                    metadata = {
                        'id': result[0],
                        'key_type': result[1],
                        'key_size': result[2],
                        'created_at': result[3],
                        'updated_at': result[4]
                    }

                    self._logger.debug(f"✅ 키 메타데이터 조회 완료: {key_type}")
                    return metadata
                else:
                    self._logger.debug(f"🔑 키 메타데이터 없음: {key_type}")
                    return None

        except Exception as e:
            self._logger.error(f"❌ 키 메타데이터 조회 실패 ({key_type}): {e}")
            raise

    def replace_key(self, key_type: str, old_key: bytes, new_key: bytes) -> bool:
        """
        안전한 키 교체 (old_key 검증 후 교체)

        Args:
            key_type (str): 키 타입
            old_key (bytes): 기존 키 (검증용)
            new_key (bytes): 새로운 키

        Returns:
            bool: 교체 성공 여부

        Raises:
            ValueError: 기존 키 불일치
        """
        if not all([key_type, old_key, new_key]):
            raise ValueError("모든 파라미터가 필요합니다")

        try:
            # 1. 기존 키 검증
            current_key = self.load_key(key_type)
            if current_key != old_key:
                raise ValueError("기존 키가 일치하지 않습니다")

            # 2. 새 키로 교체
            success = self.save_key(key_type, new_key)

            if success:
                self._logger.info(f"✅ 키 교체 완료: {key_type}")

            return success

        except ValueError:
            raise  # ValueError는 그대로 전파
        except Exception as e:
            self._logger.error(f"❌ 키 교체 실패 ({key_type}): {e}")
            return False

    def delete_all_keys(self) -> int:
        """
        모든 보안 키 삭제 (초기화)

        Returns:
            int: 삭제된 키 개수

        Warning:
            매우 위험한 연산입니다. 신중하게 사용하세요.
        """
        try:
            with self._db.get_connection('settings') as conn:
                cursor = conn.cursor()

                cursor.execute("DELETE FROM secure_keys")
                deleted_count = cursor.rowcount

                self._logger.warning(f"⚠️ 모든 보안 키 삭제 완료: {deleted_count}개")
                return deleted_count

        except Exception as e:
            self._logger.error(f"❌ 모든 키 삭제 실패: {e}")
            raise
