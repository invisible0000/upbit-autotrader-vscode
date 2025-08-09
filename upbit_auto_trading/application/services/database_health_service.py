"""
데이터베이스 건강 상태 서비스

최소한의 DB 상태 모니터링을 위한 간단한 서비스입니다.
클릭 기능 없이 순수 표시 전용으로 구현되었습니다.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from upbit_auto_trading.infrastructure.logging import create_component_logger


class DatabaseHealthService:
    """
    데이터베이스 건강 상태 서비스

    최소한의 DB 상태 확인 및 표시를 위한 서비스입니다.
    3가지 시점에서만 검증을 수행합니다:
    1. 프로그램 시작 시
    2. 데이터베이스 설정 변경 시
    3. 운영 불가능 상태 감지 시
    """

    def __init__(self):
        """초기화 - 최소 구현으로 의존성 제거"""
        self._logger = create_component_logger("DatabaseHealthService")
        self._current_status = True  # 기본값은 정상

        self._logger.info("📊 DB 건강 상태 서비스 초기화 완료 (최소 구현)")

    async def check_startup_health(self) -> bool:
        """
        프로그램 시작 시 DB 건강 상태 확인

        Returns:
            bool: DB가 정상이면 True, 고장이면 False
        """
        self._logger.info("🚀 프로그램 시작 시 DB 건강 검사 시작")

        try:
            # 간단한 DB 파일 존재 확인
            settings_path = Path("data/settings.sqlite3")

            if not settings_path.exists():
                self._logger.warning(f"⚠️ 설정 DB 파일이 존재하지 않음: {settings_path}")
                self._current_status = False
                return False

            # 간단한 연결 테스트 및 핵심 데이터 확인
            try:
                with sqlite3.connect(str(settings_path)) as conn:
                    cursor = conn.cursor()

                    # 테이블 존재 확인
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                    result = cursor.fetchone()

                    if not result:
                        self._logger.warning("⚠️ 설정 DB에 테이블이 없음 - 빈 DB로 판단")
                        self._current_status = False
                        return False

                    # 핵심 데이터 확인 - secure_keys 테이블과 데이터 존재 여부
                    try:
                        cursor.execute("SELECT COUNT(*) FROM secure_keys")
                        key_count = cursor.fetchone()[0]

                        if key_count == 0:
                            self._logger.warning("⚠️ 암호화 키가 없음 - 실질적으로 사용 불가능한 DB")
                            self._current_status = False
                            return False

                    except sqlite3.Error:
                        self._logger.warning("⚠️ secure_keys 테이블이 없음 - 불완전한 DB 스키마")
                        self._current_status = False
                        return False

                    self._logger.info("✅ 프로그램 시작 시 DB 건강 검사 통과 (핵심 데이터 포함)")
                    self._current_status = True
                    return True

            except sqlite3.Error as db_error:
                self._logger.warning(f"⚠️ 설정 DB 연결 실패: {db_error}")
                self._current_status = False
                return False

        except Exception as e:
            self._logger.error(f"❌ 프로그램 시작 시 DB 건강 검사 실패: {e}")
            self._current_status = False
            return False

    async def check_configuration_change_health(self, database_type: str, file_path: str) -> bool:
        """
        데이터베이스 설정 변경 시 건강 상태 확인

        Args:
            database_type: 데이터베이스 타입 (settings, strategies, market_data)
            file_path: 변경될 파일 경로

        Returns:
            bool: 새 DB가 정상이면 True, 고장이면 False
        """
        self._logger.info(f"🔧 DB 설정 변경 시 건강 검사: {database_type} -> {file_path}")

        try:
            # 파일 존재 확인
            if not Path(file_path).exists():
                self._logger.warning(f"⚠️ DB 파일이 존재하지 않음: {file_path}")
                return False

            # 간단한 연결 테스트
            try:
                with sqlite3.connect(file_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                    result = cursor.fetchone()

                    if result:
                        self._logger.info(f"✅ DB 설정 변경 건강 검사 통과: {database_type}")
                        return True
                    else:
                        self._logger.warning(f"⚠️ DB에 테이블이 없음: {database_type}")
                        return False

            except sqlite3.Error as db_error:
                self._logger.warning(f"⚠️ DB 연결 실패: {db_error}")
                return False

        except Exception as e:
            self._logger.error(f"❌ DB 설정 변경 건강 검사 실패: {e}")
            return False

    def mark_as_failed(self, reason: str) -> None:
        """
        운영 불가능 상태로 표시

        Args:
            reason: 실패 이유
        """
        self._logger.error(f"💀 DB 운영 불가능 상태 감지: {reason}")
        self._current_status = False

    def get_current_status(self) -> bool:
        """
        현재 DB 건강 상태 반환

        Returns:
            bool: 현재 상태 (True: 정상, False: 고장)
        """
        return self._current_status

    def get_detailed_status(self) -> Dict[str, Any]:
        """
        상세한 데이터베이스 상태 정보 반환

        Returns:
            Dict[str, Any]: 데이터베이스별 상세 상태 정보
        """
        try:
            status_data = {}

            # 3개 주요 데이터베이스 상태 확인
            databases = [
                ("settings", "data/settings.sqlite3"),
                ("strategies", "data/strategies.sqlite3"),
                ("market_data", "data/market_data.sqlite3")
            ]

            for db_type, db_path in databases:
                status_data[db_type] = self._check_single_database(db_type, db_path)

            return status_data

        except Exception as e:
            self._logger.error(f"❌ 상세 상태 조회 실패: {e}")
            return {}

    def _check_single_database(self, db_type: str, db_path: str) -> Dict[str, Any]:
        """단일 데이터베이스 상태 확인"""
        result = {
            'is_healthy': False,
            'response_time_ms': 0.0,
            'file_size_mb': 0.0,
            'table_count': 0,
            'has_secure_keys': False,
            'error_message': '',
            'last_check_time': datetime.now().strftime("%H:%M:%S")
        }

        try:
            # 파일 존재 및 크기 확인
            path = Path(db_path)
            if not path.exists():
                result['error_message'] = f"DB 파일이 존재하지 않음: {db_path}"
                return result

            result['file_size_mb'] = path.stat().st_size / (1024 * 1024)

            # DB 연결 테스트 (응답 시간 측정)
            start_time = datetime.now()

            with sqlite3.connect(str(path), timeout=5.0) as conn:
                cursor = conn.cursor()

                # 테이블 개수 확인
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                result['table_count'] = cursor.fetchone()[0]

                if result['table_count'] == 0:
                    result['error_message'] = "DB에 테이블이 없음 - 빈 파일"
                    return result

                # settings DB인 경우 secure_keys 확인
                if db_type == 'settings':
                    try:
                        # 전체 키 개수 확인
                        cursor.execute("SELECT COUNT(*) FROM secure_keys")
                        total_key_count = cursor.fetchone()[0]

                        # 실제 암호화 키(encryption 타입) 확인
                        cursor.execute("SELECT COUNT(*) FROM secure_keys WHERE key_type = 'encryption'")
                        encryption_key_count = cursor.fetchone()[0]

                        result['has_secure_keys'] = encryption_key_count > 0

                        # 디버그 정보 추가
                        self._logger.debug(
                            f"🔍 {db_type} DB 키 검사: 전체 {total_key_count}개, "
                            f"암호화키 {encryption_key_count}개"
                        )

                        # 암호화 키가 없어도 DB 자체는 정상으로 간주
                        if not result['has_secure_keys']:
                            self._logger.info(
                                f"ℹ️ {db_type} DB에 암호화 키가 없지만 DB는 정상 작동 "
                                f"(총 {total_key_count}개 키 존재)"
                            )

                    except sqlite3.Error as e:
                        self._logger.warning(f"⚠️ {db_type} DB secure_keys 테이블 접근 실패: {e}")
                        result['has_secure_keys'] = False

                # 응답 시간 계산
                end_time = datetime.now()
                result['response_time_ms'] = (end_time - start_time).total_seconds() * 1000

                result['is_healthy'] = True
                self._logger.debug(f"✅ {db_type} DB 상태 검사 완료: 정상")

        except sqlite3.Error as e:
            result['error_message'] = f"DB 연결 오류: {str(e)}"
            self._logger.warning(f"⚠️ {db_type} DB 연결 실패: {e}")
        except Exception as e:
            result['error_message'] = f"예상치 못한 오류: {str(e)}"
            self._logger.error(f"❌ {db_type} DB 검사 중 오류: {e}")

        return result
