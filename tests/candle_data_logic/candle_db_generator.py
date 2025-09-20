"""
캔들 DB 데이터 생성기
시작 시간과 개수를 입력받아 정확한 UTC와 timestamp로 테스트 데이터 생성
현실적인 가격 데이터도 포함
"""

import sqlite3
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import random


class CandleDBGenerator:
    """캔들 DB 데이터 생성기"""

    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        """
        Args:
            db_path: DB 파일 경로 (기본: data/market_data.sqlite3)
        """
        self.db_path = os.path.abspath(db_path)
        self.table_name = "candles_KRW_BTC_1m"

    def generate_candle_data(
        self,
        start_time: str,
        count: int,
        base_price: float = 155000000.0
    ) -> Dict[str, Any]:
        """
        캔들 데이터 생성 및 DB 저장

        Args:
            start_time: 시작 시간 (UTC) 예: '2025-09-08T00:00:00'
            count: 생성할 캔들 개수
            base_price: 기준 가격 (원) 기본: 1억 5500만원

        Returns:
            dict: 생성 결과
        """
        try:
            # 시작 시간 파싱 및 검증
            if 'T' not in start_time:
                return {
                    'success': False,
                    'error': f'시간 형식이 올바르지 않습니다. 예: 2025-09-08T00:00:00'
                }

            start_dt = datetime.fromisoformat(start_time).replace(tzinfo=timezone.utc)

            # 캔들 데이터 생성
            candle_data = self._create_candle_records(start_dt, count, base_price)

            # DB에 저장
            self._ensure_table_exists()
            saved_count = self._save_to_db(candle_data)

            # 종료 시간 계산 (과거 방향이므로 start_dt에서 빼기)
            end_dt = start_dt - timedelta(minutes=count - 1)

            return {
                'success': True,
                'start_time': start_time,
                'end_time': end_dt.strftime('%Y-%m-%dT%H:%M:%S'),
                'requested_count': count,
                'generated_count': len(candle_data),
                'saved_count': saved_count,
                'base_price': base_price,
                'db_path': self.db_path
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _create_candle_records(
        self,
        start_dt: datetime,
        count: int,
        base_price: float
    ) -> List[Dict[str, Any]]:
        """
        캔들 레코드들 생성

        주의: 업비트 API는 최신 → 과거 순서로 데이터 제공
        start_dt는 최신 시간이고, 과거 방향으로 생성
        """
        records = []
        current_price = base_price

        for i in range(count):
            # 과거 방향으로 계산 (최신부터 과거로)
            candle_time = start_dt - timedelta(minutes=i)

            # 현실적인 가격 변동 시뮬레이션
            price_change_percent = random.uniform(-0.002, 0.002)  # ±0.2% 변동
            current_price *= (1 + price_change_percent)

            # OHLC 데이터 생성
            opening_price = current_price
            high_price = opening_price * random.uniform(1.0, 1.001)  # 최대 0.1% 상승
            low_price = opening_price * random.uniform(0.999, 1.0)   # 최대 0.1% 하락

            # 종가는 고가와 저가 사이
            trade_price = random.uniform(low_price, high_price)
            current_price = trade_price  # 다음 캔들의 시작가

            # 거래량 시뮬레이션
            volume = random.uniform(5.0, 15.0)  # 5~15 BTC
            acc_trade_price = trade_price * volume

            # UTC 시간 문자열 (timezone 정보 없이)
            utc_str = candle_time.strftime('%Y-%m-%dT%H:%M:%S')

            # KST 시간 (UTC + 9시간)
            kst_time = candle_time + timedelta(hours=9)
            kst_str = kst_time.strftime('%Y-%m-%dT%H:%M:%S')

            # Unix timestamp (밀리초)
            timestamp = int(candle_time.timestamp() * 1000)

            record = {
                'candle_date_time_utc': utc_str,
                'market': 'KRW-BTC',
                'candle_date_time_kst': kst_str,
                'opening_price': round(opening_price, 0),
                'high_price': round(high_price, 0),
                'low_price': round(low_price, 0),
                'trade_price': round(trade_price, 0),
                'timestamp': timestamp,
                'candle_acc_trade_price': round(acc_trade_price, 0),
                'candle_acc_trade_volume': round(volume, 6),
                'empty_copy_from_utc': None,  # 빈 캔들 식별 필드
                'created_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            }

            records.append(record)

        return records

    def _ensure_table_exists(self) -> None:
        """테이블이 존재하는지 확인하고 없으면 생성 (sqlite_candle_repository.py와 동일한 스키마)"""
        # 디렉토리 생성
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # sqlite_candle_repository.py의 ensure_table_exists와 정확히 동일한 스키마
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    -- ✅ 단일 PRIMARY KEY (시간 정렬 + 중복 방지)
                    candle_date_time_utc TEXT NOT NULL PRIMARY KEY,

                    -- 업비트 API 공통 필드들
                    market TEXT NOT NULL,
                    candle_date_time_kst TEXT,  -- 빈 캔들에서는 NULL (용량 절약)
                    opening_price REAL,        -- 빈 캔들에서는 NULL (용량 절약)
                    high_price REAL,           -- 빈 캔들에서는 NULL (용량 절약)
                    low_price REAL,            -- 빈 캔들에서는 NULL (용량 절약)
                    trade_price REAL,         -- 빈 캔들에서는 NULL (용량 절약)
                    timestamp INTEGER NOT NULL,
                    candle_acc_trade_price REAL,  -- 빈 캔들에서는 NULL (용량 절약)
                    candle_acc_trade_volume REAL, -- 빈 캔들에서는 NULL (용량 절약)

                    -- 빈 캔들 처리 필드
                    empty_copy_from_utc TEXT,

                    -- 메타데이터
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 🚀 성능 최적화를 위한 timestamp 인덱스 생성
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_timestamp
                ON {self.table_name}(timestamp DESC)
            """)

            conn.commit()

    def _save_to_db(self, records: List[Dict[str, Any]]) -> int:
        """레코드들을 DB에 저장"""
        saved_count = 0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for record in records:
                try:
                    cursor.execute(f"""
                        INSERT OR REPLACE INTO {self.table_name}
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record['candle_date_time_utc'],
                        record['market'],
                        record['candle_date_time_kst'],
                        record['opening_price'],
                        record['high_price'],
                        record['low_price'],
                        record['trade_price'],
                        record['timestamp'],
                        record['candle_acc_trade_price'],
                        record['candle_acc_trade_volume'],
                        record['empty_copy_from_utc'],
                        record['created_at']
                    ))
                    saved_count += 1
                except sqlite3.Error as e:
                    print(f"⚠️ 레코드 저장 실패: {record['candle_date_time_utc']}, 오류: {e}")

            conn.commit()

        return saved_count

    def generate_sample_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """샘플 시나리오들 생성"""
        scenarios = {
            'basic_100': {
                'start_time': '2025-09-08T00:00:00',
                'count': 100,
                'description': '베이직 100개 (00:00부터 01:39까지)'
            },
            'basic_200': {
                'start_time': '2025-09-08T00:00:00',
                'count': 200,
                'description': '베이직 200개 (00:00부터 03:19까지)'
            },
            'basic_300': {
                'start_time': '2025-09-08T00:00:00',
                'count': 300,
                'description': '베이직 300개 (00:00부터 04:59까지)'
            },
            'basic_1000': {
                'start_time': '2025-09-08T00:00:00',
                'count': 1000,
                'description': '베이직 1000개 (00:00부터 16:39까지)'
            }
        }
        return scenarios


def main():
    """CLI 실행용 메인 함수"""
    print("🏭 === 캔들 DB 데이터 생성기 ===")

    generator = CandleDBGenerator()

    # 사용자 입력
    print("\n📝 데이터 생성 설정:")

    try:
        start_time = input("시작 시간 (예: 2025-09-08T00:00:00): ").strip()
        if not start_time:
            start_time = "2025-09-08T00:00:00"

        count_input = input("생성할 캔들 개수 (예: 100): ").strip()
        count = int(count_input) if count_input else 100

        print(f"\n🚀 데이터 생성 중...")
        print(f"   시작: {start_time}")
        print(f"   개수: {count:,}개")

        # 데이터 생성
        result = generator.generate_candle_data(start_time, count)

        if result['success']:
            print(f"\n✅ 생성 완료!")
            print(f"   📁 DB 경로: {result['db_path']}")
            print(f"   📅 시간 범위: {result['start_time']} ~ {result['end_time']}")
            print(f"   📊 생성: {result['generated_count']:,}개")
            print(f"   📊 저장: {result['saved_count']:,}개")
            print(f"   💰 기준 가격: {result['base_price']:,.0f}원")
        else:
            print(f"\n❌ 생성 실패: {result['error']}")

    except KeyboardInterrupt:
        print("\n\n⏹️ 사용자에 의해 중단됨")
    except ValueError as e:
        print(f"\n❌ 입력 오류: {e}")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")


if __name__ == "__main__":
    main()
