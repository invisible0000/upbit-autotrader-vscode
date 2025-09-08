"""
캔들 데이터 DB 클리너
candles_KRW_BTC_1m 테이블을 완전히 초기화하여 깨끗한 테스트 환경 제공
"""

import sqlite3
import os
from typing import Optional


class CandleDBCleaner:
    """캔들 DB 클리너"""

    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        """
        Args:
            db_path: DB 파일 경로 (기본: data/market_data.sqlite3)
        """
        self.db_path = os.path.abspath(db_path)

    def clear_candle_table(self, table_name: str = "candles_KRW_BTC_1m") -> dict:
        """
        캔들 테이블 완전 초기화

        Args:
            table_name: 초기화할 테이블명 (기본: candles_KRW_BTC_1m)

        Returns:
            dict: 초기화 결과 통계
        """
        if not os.path.exists(self.db_path):
            return {
                'success': False,
                'error': f'DB 파일이 존재하지 않습니다: {self.db_path}',
                'records_before': 0,
                'records_after': 0
            }

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 초기화 전 레코드 수 확인
                records_before = self._get_record_count(cursor, table_name)

                # 테이블 완전 삭제 후 재생성 (더 확실한 초기화)
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

                # 테이블 재생성 (표준 스키마)
                self._create_candle_table(cursor, table_name)

                conn.commit()

                # 초기화 후 레코드 수 확인 (0이어야 함)
                records_after = self._get_record_count(cursor, table_name)

                return {
                    'success': True,
                    'table_name': table_name,
                    'records_before': records_before,
                    'records_after': records_after,
                    'db_path': self.db_path
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'records_before': 0,
                'records_after': 0
            }

    def _get_record_count(self, cursor: sqlite3.Cursor, table_name: str) -> int:
        """테이블의 레코드 수 조회"""
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cursor.fetchone()[0]
        except sqlite3.OperationalError:
            # 테이블이 존재하지 않는 경우
            return 0

    def _create_candle_table(self, cursor: sqlite3.Cursor, table_name: str) -> None:
        """캔들 테이블 생성 (표준 스키마)"""
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                candle_date_time_utc TEXT PRIMARY KEY,
                market TEXT NOT NULL,
                candle_date_time_kst TEXT,
                opening_price REAL,
                high_price REAL,
                low_price REAL,
                trade_price REAL,
                timestamp INTEGER,
                candle_acc_trade_price REAL,
                candle_acc_trade_volume REAL,
                created_at TEXT
            )
        """)

    def verify_clean_state(self, table_name: str = "candles_KRW_BTC_1m") -> dict:
        """
        테이블이 깨끗한 상태인지 검증

        Returns:
            dict: 검증 결과
        """
        if not os.path.exists(self.db_path):
            return {
                'is_clean': False,
                'error': f'DB 파일이 존재하지 않습니다: {self.db_path}'
            }

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                record_count = self._get_record_count(cursor, table_name)

                return {
                    'is_clean': record_count == 0,
                    'record_count': record_count,
                    'table_name': table_name,
                    'db_path': self.db_path
                }

        except Exception as e:
            return {
                'is_clean': False,
                'error': str(e)
            }


def main():
    """CLI 실행용 메인 함수"""
    print("🧹 === 캔들 DB 클리너 ===")

    cleaner = CandleDBCleaner()

    # 현재 상태 확인
    print("\n📊 초기화 전 상태 확인...")
    verify_result = cleaner.verify_clean_state()
    if 'error' not in verify_result:
        print(f"   현재 레코드 수: {verify_result['record_count']:,}개")
    else:
        print(f"   오류: {verify_result['error']}")

    # 테이블 초기화 실행
    print("\n🗑️ 테이블 초기화 실행...")
    clean_result = cleaner.clear_candle_table()

    if clean_result['success']:
        print(f"   ✅ 초기화 성공!")
        print(f"   📁 DB 경로: {clean_result['db_path']}")
        print(f"   📊 이전 레코드: {clean_result['records_before']:,}개")
        print(f"   📊 현재 레코드: {clean_result['records_after']:,}개")
    else:
        print(f"   ❌ 초기화 실패: {clean_result['error']}")

    # 최종 상태 확인
    print("\n🔍 최종 상태 확인...")
    final_verify = cleaner.verify_clean_state()
    if final_verify['is_clean']:
        print("   ✅ 깨끗한 상태 확인됨")
    else:
        print(f"   ⚠️ 문제 발견: {final_verify.get('error', '레코드가 남아있음')}")


if __name__ == "__main__":
    main()
